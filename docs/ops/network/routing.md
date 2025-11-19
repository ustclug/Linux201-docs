---
icon: material/router-network
---

# 路由

!!! note "主要作者"

    [@iBug][iBug]

!!! warning "本文编写中"

## 路由表 {#routing-tables}

**路由**是网络系统用来决定数据包去向的过程，主要由**路由表**来实现。
在 Linux 中，路由表存储在内核中，可以通过 `ip route` 命令查看当前的路由表：

```console
$ ip route
default via 192.0.2.1 dev eth0 src 192.0.2.100
192.0.2.0/24 dev eth0 src 192.0.2.100
```

在以上示例中，第二行表示目标为 192.0.2.0/24 的地址发送到 eth0 设备的本地网络中，以源地址 192.0.2.100 进行通信（即本机地址）；而其他所有流量（`default`）都将发送给网关 192.0.2.1，由该网关决定进一步的去向。

Linux 的路由表数据结构为 Trie（前缀树），可以高效地进行**最长前缀匹配**，这也是 Linux 的基本路由规则[^windows]。
在此基础上，`default` 是 `0.0.0.0/0`（或 IPv6 `::/0`）的简写或别名，表示前缀长度为零的默认路由。

  [^windows]: Windows 系统的路由表使用线性表结构，匹配时会按优先级顺序遍历所有规则，效率较低，且不符合最长前缀匹配原则。

### `ip route` 命令 {#ip-route}

`ip route` 命令是管理路由表的主要工具，其默认操作是显示当前的路由表，等价于 `ip route show table main`。
如果要增加或替换一条路由规则，可以使用 `ip route add` 或 `ip route replace` 命令，例如：

```shell
ip route add 198.51.100.0/24 via 192.0.2.2 dev eth0
```

此后，Linux 就会将目标地址为 198.51.100.0/24 的数据包发送给网关 192.0.2.2。
`add` 与 `replace` 的区别如同字面含义，当完全相同的 CIDR 已经存在时，`add` 会报错，而 `replace` 会覆盖原有规则。

对于本地网络的路由规则，可以省略 `via` 部分[^via-zero]，例如：

```shell
ip route add 192.0.2.0/24 dev eth0
```

此后，Linux 就会将目标地址为 192.0.2.0/24 的数据包发送到 eth0 接口的本地网络中，不经过网关。

  [^via-zero]: 事实上，若省略了 `via` 部分，`ip` 命令向内核传递路由规则时会将其设置为 `0.0.0.0`（IPv4）或 `::`（IPv6），这是系统接口的实现细节。如果你明确指定 `via 0.0.0.0`，会得到相同的效果。

对于没有链路层的接口（如 WireGuard 接口、其他三层隧道接口和 TUN 设备等），`via` 部分没有意义，即使指定了也不会产生任何影响。

### 路由类型 {#route-types}

每条路由规则都有一个类型（type），常见的路由类型包括：

unicast（默认）

:   单播路由，表示数据包发送到单一目的地址。

local

:   本地路由，表示数据包由本机接收，通常用于本机的 IP 地址。

broadcast / multicast

:   广播或多播路由，表示数据包发送到广播或多播地址。该类型需要链路层支持多播，所以在三层隧道接口上通常不起作用。

throw

:   特殊的规则，表示跳出当前路由表，继续在后续的路由规则中查找匹配的规则（见下文「策略路由」部分）。

    如果一个路由表中不包含 `default` 路由，则隐含一个 `throw default` 规则。

blackhole / unreachable / prohibit

:   拒绝路由，处理方式分别为静默丢弃、返回 ICMP unreachable 和 ICMP prohibited 响应。

如果你尝试查看 `local` 表中的路由，就能发现 Linux 已经自动维护了许多 local 和 broadcast 类型的路由：

```console
$ ip route show table local
local 127.0.0.0/8 dev lo proto kernel scope host src 127.0.0.1
local 127.0.0.1 dev lo proto kernel scope host src 127.0.0.1
broadcast 127.255.255.255 dev lo proto kernel scope link src 127.0.0.1
local 192.0.2.1 dev eth0 proto kernel scope host src 192.0.2.1
broadcast 192.0.2.255 dev eth0 proto kernel scope link src 192.0.2.1
```

## 策略路由 {#policy-based-routing}

单一的路由表只能根据数据包的目的地址来决定去向，无法满足更复杂的路由需求。
一个典型的场景是，同时接入多个网络的服务器在处理网络连接时，需要「源进源出」的路由方式才能确保与客户端正常通信。
**策略路由**（Policy-Based Routing，PBR）通过引入多个路由表和（不仅仅根据目的地址的）路由规则，实现了更灵活的路由控制。

### 路由规则 {#routing-rules}

在 Linux 中，路由决策的过程分为两个阶段：

1. **路由规则匹配**：根据数据包的特征（如源地址、目的地址、TOS 等）在路由规则列表（Routing Policy DataBase，RPDB）中查找匹配的规则，确定使用哪个路由表；
2. **路由表查找**：在选定的路由表中查找匹配的路由规则，决定数据包的去向。

    特别地，如果路由规则的类型为 `throw`，则跳出当前路由表，继续考察后续的路由规则。

路由规则存储在内核中的 RPDB，可以通过 `ip rule` 命令查看当前的路由规则列表。
每条路由规则都有一个优先级（priority），数值越小优先级越高，默认情况下，内核会维护三条基本的路由规则（IPv6 为两条）：

```shell title="IPv4 默认路由规则"
$ ip rule
0:      from all lookup local
32766:  from all lookup main
32767:  from all lookup default
```

<!-- `shell` language is required for rendering annotation: https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#fn:1 -->
```shell title="IPv6 默认路由规则"
$ ip -6 rule
0:      from all lookup local
32766:  from all lookup main # (1)!
```

1. 注意到，IPv6 默认没有指向 `default` 路由表的规则

在内核中，每个路由表都有一个编号，默认的路由表编号如下：

| 路由表  | 编号  |
| :-----: | :---: |
|  local  |  255  |
|  main   |  254  |
| default |  253  |

路由表的编号仅用于区分，不影响路由表的功能和优先级（优先级由路由规则决定）。

### `ip rule` 命令 {#ip-rule}
