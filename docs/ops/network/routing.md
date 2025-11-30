---
icon: material/router-network
---

# 路由

!!! note "主要作者"

    [@iBug][iBug]

!!! warning "本文已完成，等待校对"

## 路由表 {#routing-tables}

**路由**是网络系统用来决定数据包去向的过程，主要由**路由表**来实现。
在 Linux 中，路由表存储在内核中，可以通过 `ip route` 命令查看当前的路由表：

```console
$ ip route
default via 192.0.2.1 dev eth0 src 192.0.2.100
192.0.2.0/24 dev eth0 src 192.0.2.100
```

在以上示例中，第二行表示目标为 192.0.2.0/24 的地址发送到 eth0 设备的本地网络中，以源地址 192.0.2.100 进行通信（即本机地址）；而其他所有流量（`default`）都将发送给网关 192.0.2.1，由该网关决定进一步的去向。

Linux 的路由表数据结构为 [Trie][trie]（前缀树），可以高效地进行**最长前缀匹配**，这也是 Linux 的基本路由规则[^windows]。
在此基础上，`default` 是 `0.0.0.0/0`（或 IPv6 `::/0`）的简写或别名，表示前缀长度为零的默认路由。

  [trie]: https://zh.wikipedia.org/wiki/Trie
  [^windows]: Windows 系统的路由表使用线性表结构，匹配时会按优先级顺序遍历所有规则，效率较低，且不符合最长前缀匹配原则。

### `ip route` 命令 {#ip-route}

`ip route` 命令是管理路由表的主要工具，其默认操作是显示当前的路由表，等价于 `ip route show table main`。

#### 增、删、改 {#ip-route-manip}

如果要**增加或替换**一条路由规则，可以使用 `ip route add` 或 `ip route replace` 命令，例如：

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

如果要**删除**一条路由规则，可以使用 `ip route delete` 命令。
与增加和修改的命令不同，由于每条路由由其 CIDR 唯一确定，因此只需要指定该 CIDR 即可删除路由。

```shell
ip route delete 192.0.2.0/24
```

#### 查 {#ip-route-show}

前文提到，`ip route` 命令等价于 `ip route show table main`，用于显示主路由表的内容。
如果要查看其他路由表的内容，可以使用 `table` 选项指定路由表，例如：

```shell
ip route show table local
```

如果要测试某个数据包会匹配到哪条路由规则，可以使用 `ip route get` 命令，例如：

```console
$ ip route get 8.8.8.8
8.8.8.8 via 192.0.2.1 dev eth0 src 192.0.2.100
```

对于策略路由，`ip route get` 命令也允许指定额外的数据包信息（如源地址、TOS 等），以便测试路由规则的匹配情况，例如：

```shell
ip route get 8.8.8.8 from 192.0.2.100 mark 1
```

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

### 自定义路由表 {#custom-routing-tables}

内核中有多张路由表，以编号区别，默认的路由表有三张：

| 路由表  | 编号  |
| :-----: | :---: |
|  local  |  255  |
|  main   |  254  |
| default |  253  |

路由表的编号仅用于区分，不影响路由表的功能和优先级（优先级由路由规则决定）。
其中 local 表和 main 表会由内核自动维护一些规则（如上一段所述），如本地路由等。其余的路由表则需要用户手动管理。

在下文的「策略路由」部分，由于单一的路由表功能非常有限，自定义更多的路由表是实现复杂路由策略的基础。

`ip` 命令允许使用任意编号（1～MAX_INT）的路由表，但为了便于管理，建议为自定义路由表指定一个名称，并在 `/etc/iproute2/rt_tables` 文件中添加对应的映射关系，例如：

```shell title="/etc/iproute2/rt_tables"
#
# reserved values
#
255     local
254     main
253     default
0       unspec
#
# local
#
100     eth0
101     eth1
```

你也可以在 `/etc/iproute2/rt_tables.d/` 目录中创建单独的文件来定义路由表名称映射，以避免与软件包管理的文件冲突。

!!! warning

    `/etc/iproute2/rt_tables` 为 iproute2 工具（即 `ip` 命令）的配置文件，修改该文件不会影响内核的实际路由表编号，也不会影响其他路由工具（如 `route` 命令）的行为。

    例如，若要在 systemd-networkd 的配置文件中使用自定义路由表名，则需要在 `/etc/systemd/networkd.conf` 中添加 `RouteTable=` 配置项。该配置项需要 systemd 版本 ≥ 252。

    ```ini title="/etc/systemd/networkd.conf.d/custom.conf"
    [Network]
    RouteTable=eth0:100
    RouteTable=eth1:101
    ```

    systemd-networkd 内置了 `local`、`main` 和 `default` 三个路由表名称映射，无需在 `networkd.conf` 中重复定义。

## 策略路由 {#policy-based-routing}

单一的路由表只能根据数据包的目的地址来决定去向，无法满足更复杂的路由需求。
一个典型的场景是，同时接入多个网络的服务器在处理网络连接时，需要「[源进源出](#source-based-routing)」的路由方式才能确保与客户端正常通信。
**策略路由**（Policy-Based Routing，PBR）通过引入多个路由表和（不仅仅根据目的地址的）路由规则，实现了更灵活的路由控制。

### 路由规则 {#routing-rules}

在 Linux 中，路由决策的过程分为两个阶段：

1. **路由规则匹配**：根据数据包的特征（如源地址、目的地址、TOS 等）在路由规则列表（Routing Policy DataBase，RPDB）中查找匹配的规则，确定使用哪个路由表。

    注意路由规则是一个线性表，内核会按顺序逐条考察规则，因此过多的路由规则会影响路由决策的效率。相比之下，路由表的前缀树结构可以高效地进行前缀匹配。

2. **路由表查找**：在选定的路由表中查找匹配的路由规则，决定数据包的去向。

    特别地，如果路由规则的类型为 `throw`，则跳出当前路由表，继续考察后续的路由规则。

路由规则存储在内核中，可以通过 `ip rule` 命令查看。
每条路由规则都有一个优先级（preference / priority），数值越小则优先级越高。
在启动时，内核会自动创建三条默认的 IPv4 路由规则和两条默认的 IPv6 路由规则：

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

1. IPv6 的默认路由规则不包括 `default` 路由表，尽管你可以手动添加该规则。

### `ip rule` 命令 {#ip-rule}

`ip rule` 命令用于管理路由规则，其默认操作是显示当前的路由规则列表（等价于 `ip rule list`）。

如果要增减路由规则，可以使用 `ip rule add` 和 `ip rule delete` 命令，例如：

```shell
ip rule add from 192.0.2.0/24 table 100 pref 1000
```

在以上命令中，`from 192.0.2.0/24` 指定了匹配条件，`table 100` 指定“动作”为进入路由表 100，`pref 1000` 指定该规则的优先级。

由于内核不保证相同优先级的规则之间的顺序，因此我们建议仅为逻辑上完全互斥的规则使用相同的优先级，避免出现非预期的行为。

此时你可以在路由规则列表中看到新添加的规则：

```console
$ ip rule
[...]
1000:   from 192.0.2.0/24 lookup eth0
[...]
```

如果你在[前文](#custom-routing-tables)中为路由表 100 定义了名称映射（如 `eth0`），`ip rule` 命令就会显示该名称，便于识别。

### 路由策略匹配规则 {#routing-policy-matching}

路由规则的匹配条件可以包含多个字段，常用的匹配条件包括：

| 条件                                | 说明                                       |
| ----------------------------------- | ------------------------------------------ |
| from CIDR                           | 源地址（CIDR）                             |
| to CIDR                             | 目的地址（CIDR）                           |
| fwmark mark<br>fwmark mark/mask     | 防火墙标记（firewall mark），可以附带掩码  |
| iif IFACE                           | 数据包的输入接口                           |
| oif IFACE                           | 数据包的输出接口                           |
| uidrange MIN-MAX                    | 进程的用户 ID 范围                         |
| tos TOS                             | IP 数据包的服务类型（Type of Service）字段 |
| ipproto PROTOCOL                    | IP 层内协议（如 `tcp`、`udp`、`icmp` 等）  |
| sport port<br>sport portmin-portmax | 源端口号或范围                             |
| dport port<br>dport portmin-portmax | 目的端口号或范围                           |

其中：

- from 条件既适用于本机发出的数据包（需要 socket 已经 `bind()` 到一个 IP 地址上），也适用于经过本机转发的数据包（此时数据包的源地址是已知的）。

    如果要匹配没有 `bind()` 的数据包，可以使用 `from 0.0.0.0` 或 `from ::`（即零地址，注意不是前缀为零的 CIDR）。

- fwmark 条件匹配防火墙的数据包标记，通常与 Netfilter 的 `MARK` 目标结合使用，实现更复杂的路由策略。
- iif 条件匹配数据包的输入接口，其中由本机发出的数据包可以用 `iif lo` 匹配。
- oif 条件匹配数据包的输出接口，只适用于本机发出的包，对应的 socket 已经绑定到该接口（`setsockopt(SO_BINDTODEVICE)`）[^oif-why]。
- uidrange 条件匹配发包进程的 UID，但只适用于本机发出的数据包。

    特别地，许多 Android VPN 软件使用该条件实现应用级别的访问控制，利用了 Android 系统中的每个应用都有一个独立的 UID 这一特性。

- sport 和 dport 条件只能用于 TCP 和 UDP 协议[^port-protocol]的数据包。

  [^oif-why]: 否则，你觉得在路由决策阶段，内核怎么可能知道数据包将要从哪个接口发出呢？
  [^port-protocol]: 其实还有 DCCP 和 SCTP 协议也支持端口号，但这两种协议较少使用，因此本文在此不做赘述。

## 路由案例 {#routing-examples}

### 源进源出 {#source-based-routing}

一种常见的做法是，新增一条优先级非常高的规则指向 main 表，然后为每个接口指定一张专属路由表，实现本机流量的「源进源出」：

```shell title="ip rule"
0:      from all lookup local
1:      from all lookup main suppress_prefixlength 0 # (1)!
3:      from 192.0.2.2 lookup eth0
3:      from 198.51.100.2 lookup eth1
32766:  from all lookup main
32767:  from all lookup default
```

1. `suppress_prefixlength 0` 表示屏蔽所有前缀长度不大于 0 的路由规则（即 `default` 路由），避免 main 表中 `default` 路由过早生效。

此时在 `eth0` 和 `eth1` 两个路由表中指定各自的 `default` 路由，就能确保流量从对应的接口发出：

```console
$ ip route show table eth0
default via 192.0.2.1 dev eth0
$ ip route show table eth1
default via 198.51.100.1 dev eth1
```

这对于具有多张网卡或接入了多个网络的服务器尤为重要，否则可能会导致客户端无法与服务器建立连接。

该方法的一个局限性是，它只能为本机运行的服务（进程）提供「源进源出」的能力，无法满足通过本机转发的流量（如经过 NAT 的转发）的需求。
这种需求需要结合使用数据包的防火墙标记（mark）、[连接跟踪器（conntrack）](firewall.md#conntrack)的 [connmark 标记](firewall.md#conntrack-mark)和路由规则的 `fwmark` 匹配条件综合实现。

### 源进源出 + 转发 {#source-based-routing-with-forwarding}

本需求的一个典型场景是，路由器具有多个上游（WAN 接口）或接入了多个运营商，同时对 LAN 侧的主机提供 NAT 转发上网功能。

本节内容需要结合防火墙规则和 conntrack 的知识，建议先对[防火墙](firewall.md)章节中的相关内容有初步了解。

使用基于源地址的路由规则只能为本机发出的数据包实现「源进源出」，而无法满足通过本机转发的流量的需求。
这是因为前文的方式依赖于这项假设：建立连接的数据包的目的地址必然是对应接口上的地址，那么对于回包来说，源地址自然也是对应接口上的地址，那么基于源地址决定从哪个接口发出就能保证「源进源出」。
但对于转发的数据包来说，回包的源地址不再对应到接口上了，因此源地址匹配的方式就不顶用了。

此时，我们可以结合使用防火墙标记（fwmark）和 conntrack 标记（connmark）来实现「源进源出」的需求。
具体做法分为几个部分：

- 在初次确定上游接口的时候，为数据包打上对应的防火墙标记（mark），并将该标记保存到 CT 中（connmark）。
- 若一个待转发的数据包（PREROUTING）匹配某条连接，那么就从 CT 中将对应的 connmark 还原到数据包上作为 fwmark。
- 在路由规则中使用 `fwmark` 条件匹配对应的防火墙标记，进入对应的路由表，从而实现「源进源出」。

作为例子，本文假设路由器有两个 WAN 接口 `eth0` 和 `eth1`，分别指定防火墙标记为 100 和 101，那么路由规则可以这样写：

```shell title="ip rule"
0:      from all lookup local
1:      from all lookup main suppress_prefixlength 0
3:      from all fwmark 100 lookup eth0
3:      from all fwmark 101 lookup eth1
32766:  from all lookup main
32767:  from all lookup default
```

然后在防火墙规则中配置打标和还原标记的规则：

```shell title="iptables"
*mangle
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
# 若数据包属于已建立的连接，从 connmark 恢复到 fwmark
-A PREROUTING -j CONNMARK --restore-mark
-A PREROUTING -m mark ! --mark 0 -j RETURN

# 初次确定上游接口，打标并保存到 connmark
-A PREROUTING -i eth0 -j MARK --set-mark 100
-A PREROUTING -i eth1 -j MARK --set-mark 101
-A PREROUTING -j CONNMARK --save-mark
COMMIT
```

前两条规则会尝试从 CT 中恢复 connmark 到 fwmark，如果恢复成功，那么数据包的标记就不再为零，可以直接 RETURN，避免重复打标。
若标记仍为零，则表示这是一个新连接的数据包，需要根据输入接口打上对应的标记，并保存到 CT 中以备后续使用。

注意到，尽管打标的规则仅使用了 `-i`（输入接口）条件，对于从 LAN 侧向 WAN 侧发起的连接来说，在收到第一个回包时，输入接口自然就是对应的 WAN 接口，此时根据 `-i` 条件能够正确打标。

对于入向（WAN → LAN）的连接，由于 `main` 表的优先级很高（1 &lt; 3），因此会优先匹配到 `main` 表中的路由规则，从而不受标记影响，正常发送到 LAN 侧。

显然，本节所述的方法不区分 IPv4 和 IPv6，因此只需要将相同的配置在 `ip -6 rule` 和 `ip6tables` 中重复一遍即可。

!!! question

    相信你也注意到了，如果 LAN 侧还需要进一步的类似「源进源出」式路由的话，就需要更复杂的打标和路由规则设计了。
    本文将这个问题留给读者作为练习。

    作为提示，[上文](#routing-policy-matching)提到 `fwmark` 路由规则有两种格式。

### 「网络通」青春版 {#wlt-lite}

「网络通」是中国科学技术大学校园网的一项服务，只需每月 20 元，用户即可通过网络通的网页平台，在四个运营商出口之间自由切换，实现「单线多拨」的效果。
此过程中，用户设备在校园网中的 IP 地址保持不变，由网络通根据此 IP 地址及用户的选择进行分流。

原版的网络通服务在校园网出口处部署了魔改过的 Linux 内核，添加了额外的路由匹配规则，作为分流路由器。
但在多宽带接入的家庭网络等小规模场景中，[ipset 的 skbinfo 功能](firewall.md#ipset-skbinfo)使得我们能够在未修改的 Linux 上实现类似的功能。

!!! question

    本文到此已经把实现「网络通青春版」所需的知识都介绍完了，那么系统设计和实现就留给读者作为练习吧。  

    同样作为提示，该系统需要结合本文介绍的技术实现，至少具有以下几个组件：

    - 基于 fwmark 的策略路由规则
    - 结合 ipset 进行打标（`--map-mark`）的防火墙规则
    - 一个 Web 平台，供用户选择运营商出口，并保存到 ipset 中
