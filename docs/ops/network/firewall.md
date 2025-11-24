---
icon: material/wall-fire
---

# 防火墙

!!! note "主要作者"

    [@iBug][iBug]

!!! warning "本文编写中"

Linux 内核网络栈中的防火墙模块称为 Netfilter，负责对进出主机的数据包进行过滤和修改。Netfilter 提供了一套强大的工具，用于实现各种防火墙功能，如包过滤、网络地址转换（NAT）和连接跟踪等。

## Netfilter {#netfilter}

### Netfilter 阶段 {#netfilter-chains}

Netfilter 将数据包的处理过程划分为 5 个阶段，并在每个阶段提供 hook 点，允许用户定义规则来控制数据包的流动。这些阶段包括：

PREROUTING / `NF_INET_PRE_ROUTING`

:   数据包由网络接口（网卡）接收后，首先进入 PREROUTING 阶段。这个阶段通常用于更改目的地址（DNAT）。

INPUT / `NF_INET_LOCAL_IN`

:   数据包在经过路由决策后，如果目标是本地主机，则进入 INPUT 阶段。这个阶段通常用于过滤，管控对本地服务的访问，以及（如有必要）更改源地址（SNAT）。

FORWARD / `NF_INET_FORWARD`

:   如果由外部网络进入的数据包的目标不是本地主机，而是需要由本机转发到其他主机，则进入 FORWARD 阶段。这个阶段通常用于过滤。

OUTPUT / `NF_INET_LOCAL_OUT`

:   由本地主机发出的数据包首先进入 OUTPUT 阶段。这个阶段通常用于过滤，管控本地应用程序对外的网络访问，以及（如有必要）更改目的地址（DNAT）。

POSTROUTING / `NF_INET_POST_ROUTING`

:   数据包在离开主机由网卡发出之前，进入 POSTROUTING 阶段。这个阶段通常用于更改源地址（SNAT）。

这些阶段对应 iptables 的内置链（chains）或 nftables 的 hook 点。

从主机的视角来看，数据包经过 Netfilter 的各个阶段的路径如下图所示：

![Netfilter 阶段](../../images/netfilter-host-view.svg)

/// caption
从主机视角看 Netfilter 的各个阶段
///

在上图中，ROUTE 指[路由决策](routing.md)。

特别地，由本机发往本机（回环接口，即 `lo`）的数据包会依次经过 OUTPUT 和 POSTROUTING 阶段，由 lo 接口发出的同时也由 lo 接口收到，并再次经过 PREROUTING 和 INPUT 阶段后到达接收端 socket。
该路径的典型场景是使用 `localhost`、`127.0.0.1` 或 `::1` 等地址访问本机服务，但不包括 Unix socket[^unix-socket]。

  [^unix-socket]: 事实上 Unix socket 是一种 IPC 方式，与网络栈几乎无关，没有「路由」和「防火墙」等组件。

!!! question "路由决策与 Reroute check 是什么关系？"

    可能有部分读者见过 Wikipedia 的这张著名的 [Netfilter packet flow](https://commons.wikimedia.org/wiki/File:Netfilter-packet-flow.svg)：

    ![Netfilter flow chart](https://upload.wikimedia.org/wikipedia/commons/3/37/Netfilter-packet-flow.svg)
    {#wikipedia-netfilter-packet-flow}

    它与本文的图示有一处微妙的区别：路由决策位于 OUTPUT 阶段之前，而 OUTPUT 阶段后另有一个 Reroute check[^iptable_mangle_hook]。
    事实上此图是更加准确的，但在大多数情况下，将路由决策视作位于 OUTPUT 之后更容易理解，可以从以下两点看出：

    1. 保持 OUTPUT 阶段与 PREROUTING 阶段的相似性：两个阶段均发生在路由决策之前，且 NAT 模式为仅可更改目的地址（DNAT）。
    2. 路由结果的准确性：数据包最终的路由结果基于经过 OUTPUT 或 PREROUTING 阶段修改后的元信息，如目的地址和防火墙标记等。

    本文在介绍 iptables 的表时绘制了 [Netfilter 视角的阶段图](#netfilter-kernel-view-tables)，能够更直观地反映出此「相似性」。

  [^iptable_mangle_hook]: 此图的 2021 年的版本仍然有一处错误：Reroute check 发生在 OUTPUT 阶段内部，而 FORWARD 阶段后不经过 reroute check。细节可见 [`iptable_mangle_hook`](https://elixir.bootlin.com/linux/v6.17.8/source/net/ipv4/netfilter/iptable_mangle.c#L78) 函数。

??? info "Reroute check 的细节"

    首先需要重复的一点是：数据包最终的路由结果是基于经过 OUTPUT 阶段后、进入 POSTROUTING（或 INPUT）阶段前的状态决定的。
    那么既然数据包在 OUTPUT 阶段可能发生 MARK 或 DNAT 等修改，为什么不像外部传入的数据包一样，直接在 OUTPUT 阶段后进行路由决策呢？
    作者认为有以下两种可能的原因：

    1. 只是一个历史遗留问题：早期的内核可能并没有考虑到 OUTPUT 阶段修改信息会导致路由变化，因此在数据包由本机进程发出后，直接进行路由决策。
    2. 「由本机往网卡发出」的数据包只会经过 OUTPUT 和 POSTROUTING 两个阶段，而仅有 OUTPUT 阶段[具有](#iptables-tables-validity) filter 表。在这种情况下，若要限制本机进程允许发出数据包的网络接口，则 OUTPUT 阶段必须支持 `-o` 参数，即需要在 OUTPUT 阶段前进行一次（初步的）路由决策。

    为了兼顾「在 OUTPUT 链中可以使用 `-o`」和最终路由决策的正确性，内核采用了 Reroute 机制[^ip_route_me_harder]，即针对 OUTPUT 阶段：

    - 数据包由本机进程 `send()` 到 Netfilter 之后，首先进行一次路由决策，确定初步的输出接口。
    - 在 mangle 表中，若数据包的源地址、目的地址、防火墙标记或 TOS 字段这 4 个元信息发生了变化[^ip6t_mangle_out]，则重新进行一次路由决策[^ip_route_me_harder.mangle]。
    - 在 nat 表中，若数据包的目的地址发生了变化，则还会重新进行一次路由决策[^ip_route_me_harder.nat]。

    需要注意的是，尽管数据包可能在 mangle 表和 nat 表中已经经过了至多两次额外路由决策，但其在 filter 表中时，`-o` 参数所匹配的输出接口始终是最初的路由决策结果。
    这是因为最终生效的路由决策存储在数据包的 `skb->_skb_refdst` 字段中[^skb._skb_refdst]，而 Netfilter 在进行匹配时使用的是 `nf_hook_state->out` 字段[^ipt_do_table]，该字段在数据包进入 OUTPUT 阶段之前就已经确定，并不会随着后续的 reroute check 而改变。

    在搞清楚这些细节后，我们就能理解为什么以下两种理解方式都是正确的：

    1. 路由决策位于 OUTPUT 之后：因为数据包最终的路由结果是基于经过 OUTPUT 阶段修改后的状态决定的。
    2. 路由决策位于 OUTPUT 之前，且 OUTPUT 后另有重新路由：因为 OUTPUT 阶段需要支持 `-o` 匹配方式，该信息依赖于初步的路由决策结果。

  [^ip_route_me_harder]: [`ip_route_me_harder`](https://elixir.bootlin.com/linux/v6.17.8/source/net/ipv4/netfilter.c#L21) 或 [`ip6_route_me_harder`](https://elixir.bootlin.com/linux/v6.17.8/source/net/ipv6/netfilter.c#L23) 函数
  [^ip6t_mangle_out]: IPv6 采用的判断条件有所不同，此处不再赘述。详情请见 [`ip6t_mangle_out`](https://elixir.bootlin.com/linux/v6.17.8/source/net/ipv6/netfilter/ip6table_mangle.c#L52) 函数。
  [^ip_route_me_harder.mangle]: [`ipt_mangle_out`](https://elixir.bootlin.com/linux/v6.17.8/source/net/ipv4/netfilter/iptable_mangle.c#L63) 函数
  [^ip_route_me_harder.nat]: [`nf_nat_ipv4_local_fn`](https://elixir.bootlin.com/linux/v6.17.8/source/net/netfilter/nf_nat_proto.c#L767) 函数
  [^skb._skb_refdst]: [`skb_dst_set`](https://elixir.bootlin.com/linux/v6.17.8/source/include/linux/skbuff.h#L1173) 函数
  [^ipt_do_table]: [`ipt_do_table`](https://elixir.bootlin.com/linux/v6.17.8/source/net/ipv4/netfilter/ip_tables.c#L245) 函数

### Hook 的优先级 {#netfilter-hook-priorities}

Netfilter 为 hook 定义了一系列优先级，优先级越高的 hook 越早执行。特别地，iptables 的各个表是注册在对应的优先级上的，因此不同表的处理顺序也由 hook 的优先级决定。

在同一个阶段中，不同 hook 的处理顺序为 raw → (conntrack) → mangle → nat (DNAT) → filter → security → nat (SNAT)。
该顺序定义在 [`enum nf_ip_hook_priorities`](https://elixir.bootlin.com/linux/v6.17.8/source/include/uapi/linux/netfilter_ipv4.h#L30) 中，数值越小则优先级越高。

### conntrack {#conntrack}

连接跟踪器（**Conn**ection **Track**er，conntrack，也经常简称为 CT）是 Netfilter 的一个核心组件，用于跟踪网络连接的状态。

#### 连接跟踪 {#connection-tracking}

Conntrack 表的一个重要作用是支持有状态防火墙，允许 Netfilter 组件获取连接状态，并据此做出过滤决策。
一个典型的例子是，允许已建立连接的数据包通过防火墙，而仅过滤新连接请求。
由于 iptables 和 nftables 的规则链都是按顺序线性执行的，若在规则链开头插入「允许 conntrack 状态为已建立（ESTABLISHED）」的规则，就能减少大量数据包的匹配开销。例如：

=== "iptables / ip6tables"

    ```shell
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    ```

=== "nftables"

    ```shell
    nft add rule ip filter input ct state established,related accept
    ```

#### 连接标记 {#conntrack-mark}

Conntrack 除了记录连接的五元组（四层协议、源地址、目的地址、源端口、目的端口）外，还可以为连接记录一个「标记」（conntrack mark，`CONNMARK`）。
该标记可以在 iptables 或 nftables 规则中从数据包保存或恢复到数据包上，实现「数据包标记」与「连接标记」的双向互动，例如：

=== "iptables / ip6tables"

    ```shell
    iptables -t mangle -A PREROUTING -j CONNMARK --restore-mark
    iptables -t mangle -A POSTROUTING -j CONNMARK --save-mark
    ```

=== "nftables"

    ```shell
    nft add rule ip mangle prerouting meta mark set ct mark
    nft add rule ip mangle postrouting ct mark set mark
    ```

#### NAT 支持 {#conntrack-nat}

在 Netfilter 中，用户定义的 NAT 规则只会对**新连接**生效，而已建立的连接的后续数据包则由 conntrack 负责处理 NAT，确保同一连接内的所有数据包都能被正确处理。

例如，在一个典型的家用路由器上，当内网主机向外网发起连接时，路由器上的 NAT 规则会将数据包的源地址改写为路由器的 WAN 口地址，整个流程如下：

- 内网主机对外建立一个新的连接，发送第一个数据包到路由器
- 第一个数据包经过 POSTROUTING 阶段，被 MASQUERADE 改写源地址
    - 此时 conntrack 记录该连接**双向**的五元组（共 9 个字段，其中协议号只需记录一次），包括正向（original）的四元组和反向（reply）的四元组
- 后续的数据包（不论方向）经过该路由器时，在 conntrack 阶段（`NF_IP_PRI_CONNTRACK`）匹配到某一方向的四元组，由 conntrack 改写为另一方向的四元组的反向地址[^nf_nat_manip_pkt]，使对端主机能够正确接收数据包。

  [^nf_nat_manip_pkt]: [`nf_nat_manip_pkt`](https://elixir.bootlin.com/linux/v6.17.8/source/net/netfilter/nf_nat_proto.c#L383)

对于经过 NAT 的连接，Linux 要求属于该连接的所有数据包都由相同的网卡发出（区分正反方向），否则会停止记录连接信息并丢掉即将发往不同网卡的数据包[^nf_nat_oif_changed]。

  [^nf_nat_oif_changed]: [`nf_nat_inet_fn`](https://elixir.bootlin.com/linux/v6.17.8/source/net/netfilter/nf_nat_core.c#L978)

#### conntrack 命令 {#conntrack-command}

[`conntrack(8)`][conntrack.8] 可以查看和管理内核中的 conntrack 表，其记录了所有经过主机的数据包的连接状态信息。

最常用的命令是列出当前的连接跟踪条目：

```shell
conntrack -L
```

??? example "conntrack 输出示例"

    ```text
    udp      17 91 src=192.0.2.2 dst=8.8.8.8 sport=39043 dport=53 src=8.8.8.8 dst=198.51.100.1 sport=53 dport=39043 [ASSURED] mark=1 use=1
    ```

    - 协议：`udp`（协议号 17）
    - 剩余超时时间：91 秒
    - 正向四元组 src, dst, sport, dport
    - 反向四元组 src, dst, sport, dport

        本例中，当前主机为负责进行 NAT 的出口路由器，所以反向的 dst 地址为路由器的 WAN 口地址。

    - 连接状态标记，如 `[ASSURED]`
    - 连接标记 `mark`
    - 引用计数器 `use`

`conntrack` 命令支持一些与 iptables 语法相同的匹配条件，可以用来过滤输出的连接条目，例如：

```shell
conntrack -L -p udp --dport 53
```

`conntrack` 命令也可以对 conntrack 表进行修改操作，但相比于查询类操作较为不常用，因此具体用法可以参考 [conntrack(8)][conntrack.8]。

另外，`conntrack -E` 命令可以实时监控 conntrack 表的变化，适合用于调试和分析网络连接的动向。`-E` 操作同样支持匹配条件，可以过滤出特定的连接事件，方便查找和分析。

## iptables {#iptables}

iptables 是 Netfilter 的用户空间工具，用于管理防火墙规则。
iptables 将规则组织成不同的表（table），每个表包含多个链（chain），每个链对应一个 Netfilter 阶段。

操作 IPv4 防火墙规则时使用 `iptables` 命令，操作 IPv6 防火墙规则时使用 `ip6tables` 命令。除此之外，两者的用法完全相同。

### iptables 命令 {#iptables-cmdline}

iptables 使用 GNU `getopt_long` 风格的命令行参数，即以短横线 `-` 开头的单字符选项和以双短横线 `--` 开头的长选项。

每一条 iptables 命令及其所有参数构成一条规则，规则的基本结构如下：

```shell
iptables [全局选项] [-t 表名] 链操作 规则匹配条件 目标
```

其中 `-t` 也是全局选项之一，用于指定要操作的表。若省略 `-t`，则默认该命令操作 filter 表。

#### 链操作 {#iptables-commands}

对 iptables 链的操作类似增删改查，常用的操作有以下几种：

```shell
iptables -A 链名 ... # 追加规则到链尾
iptables -I 链名 [位置] ... # 插入规则到指定位置（默认位置为链头）
iptables -D 链名 序号 # 删除指定规则
iptables -R 链名 序号 ... # 替换指定规则
iptables -L [链名] # 列出指定链的所有规则
iptables -S [链名] # 以命令行格式列出指定链的所有规则

iptables -P 链名 目标 # 设置链的默认策略
iptables -F [链名] # 清空指定链的所有规则
iptables -Z [链名] # 将指定链的所有规则的计数器归零

iptables -N 链名 # 新增一条用户自定义链
iptables -X [链名] # 删除一条用户自定义链
```

例如，要将 iptables 的 filter 表恢复到初始状态，可以执行以下命令：

```shell
iptables -F
iptables -X
iptables -Z
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
```

注意到 `-L`, `-S`, `-F`, `-X`, `-Z` 这些操作都可以省略链名参数，表示对所有链进行操作。

完整的 iptables 规则语法和选项可以参考 [iptables(8)][iptables.8] 和 [iptables-extensions(8)][iptables-extensions.8] 手册页。

#### 规则匹配条件 {#iptables-match}

在「规则匹配条件」部分，可以使用多种匹配模块来指定数据包的特征，如源地址、目的地址、协议类型、端口号等。
匹配的顺序是按命令行参数的顺序依次进行的，只有当数据包满足所有匹配条件时，才会应用该规则的目标。

常用的匹配规则包括：

`-s` / `--source` / `-d` / `--destination`

:   指定源地址或目的地址，可以是单个 IP 地址、CIDR 块或域名。一个 `-s` 或 `-d` 参数可以指定最多 15 个 IP 地址或 CIDR 块，多个地址之间用逗号分隔。

`-p` / `--protocol`

:   指定 IP 数据包内层的协议，如 `tcp`、`udp`、`icmp` 等。

`--sport` / `--dport`

:   指定源端口号或目的端口号，可以是单个端口号或端口范围（格式为 `起始端口-结束端口`）。该选项只能与 `-p tcp` 或 `-p udp` 一起使用。

    该参数事实上由 `-m tcp` 或 `-m udp` 模块提供，而 iptables 会根据 `-p` 参数自动加载相应的模块，因此不需要显式指定 `-m tcp` 或 `-m udp`。
    出于同样的原因，你也无法在一条规则内同时匹配 TCP 和 UDP 协议的端口号，需要分别使用两条规则来实现。

    此参数只能匹配一个端口号或一个端口范围（包含起止端口号），如果需要匹配多个不连续的端口号，可以使用 `-m multiport --sports` / `--dports` 模块。

`-i` / `--in-interface` / `-o` / `--out-interface`

:   指定数据包的输入接口或输出接口，可以是接口名称（如 `eth0`）或前缀通配符（如 `eth+`）。

    由于 Netfilter 的结构和设计考虑，`-i`（输入接口）和 `-o`（输出接口）这两个匹配选项在不同阶段的可用性有所不同：

    |    阶段     |              可以使用 `-i`               |                     可以使用 `-o`                     |
    | :---------: | :--------------------------------------: | :---------------------------------------------------: |
    | PREROUTING  | :fontawesome-solid-check:{: .limegreen } |       :fontawesome-solid-xmark:{: .orangered }        |
    |    INPUT    | :fontawesome-solid-check:{: .limegreen } |       :fontawesome-solid-xmark:{: .orangered }        |
    |   FORWARD   | :fontawesome-solid-check:{: .limegreen } |       :fontawesome-solid-check:{: .limegreen }        |
    |   OUTPUT    | :fontawesome-solid-xmark:{: .orangered } | :fontawesome-solid-check:{: .limegreen }[^output-oif] |
    | POSTROUTING | :fontawesome-solid-xmark:{: .orangered } |       :fontawesome-solid-check:{: .limegreen }        |

  [^output-oif]: 还记得[上文](#wikipedia-netfilter-packet-flow)为什么说 Wikipedia 的图更准确吗？

#### 动作 {#iptables-jump}

若一个数据包满足某条规则的所有匹配条件，就会进执行该规则的目标（`-j` / `-g` 参数）。目标可以是内置目标（如 ACCEPT、DROP、REJECT 等），也可以是用户自定义链的名称（跳转至自定义链继续处理）。

`-j` / `--jump` 与 `-g` / `--goto` 的区别是，当跳转到自定义链后，`-j` 会在自定义链处理完毕后返回到原链继续处理，而 `-g` 则不会返回原链，视作原链已完成处理。可以类比在 shell 中执行命令时的 `source`（对应 `-j`）和 `exec`（对应 `-g`）的区别。

其中，内置目标包括：

- ACCEPT：接受数据包，允许其继续传输。
- DROP：丢弃数据包，不发送任何响应。
- REJECT：拒绝数据包，并发送响应给对端（默认响应为 ICMP port unreachable）。

其他常用的、由扩展模块提供的目标包括：

- DNAT (REDIRECT) / SNAT (MASQUERADE)：用于网络地址转换（NAT），分别用于更改数据包的目的地址和源地址。

    其中 REDIRECT 和 MASQUERADE 分别是 DNAT 和 SNAT 的特殊形式，用于将数据包的目的地址和源地址改写为对应网卡上的地址。

- LOG：记录数据包信息到系统日志，通常与其他目标结合使用。
- MARK：为数据包打上防火墙标记（firewall mark），通常与路由策略结合使用。
- CONNMARK：为数据包对应的 conntrack 连接打上标记，或从连接中恢复标记。

每条内置链都有一个**默认策略**（`-P` / `--policy`），当数据包经过该链但未匹配到任何规则时，会由该默认策略处理。默认策略只能是 ACCEPT 或 DROP。

!!! example "例：科大镜像站上限制 80 / 443 端口并发连接数"

    ```shell
    iptables -A LIMIT \
      -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN \
      -m multiport --dports 80,443 \
      -m connlimit --connlimit-above 12 --connlimit-mask 29 --connlimit-saddr \
      -j REJECT --reject-with tcp-reset
    ```

    这条命令的理解方式如下：

    - `iptables -A LIMIT`：将规则追加（`-A`）到名为 LIMIT 的链中，该规则只会对 IPv4 数据包生效。IPv6 防火墙规则需要使用 `ip6tables`。

        LIMIT 是我们自定义的一条链，在 INPUT 阶段调用，负责执行类似的限流规则。

    - `-p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN`：匹配 TCP 协议的数据包，且匹配仅有 SYN 标志位被设置的数据包（即新连接请求）。
        - 等价的写法是 `-p tcp --syn`
        - 另一个（几乎）等价的写法是 `-m conntrack --ctstate NEW`，该写法事实上调用了连接跟踪模块，匹配将要建立新连接的数据包。
    - `-m multiport --dports 80,443`：调用 `multiport` 模块，匹配目的端口为 80 或 443 的数据包。
    - `-m connlimit --connlimit-above 12 --connlimit-mask 29 --connlimit-saddr`：调用 `connlimit` 模块，匹配来自同一子网（掩码长度 29，即每 8 个 IP 地址为一个子网）且当前已建立连接数超过 12 的数据包。
    - `-j REJECT --reject-with tcp-reset`：目标为 REJECT，即主动拒绝匹配的数据包，并发送 TCP RST 响应给对端。

### iptables 表 {#iptables-tables}

iptables 的主要表类型有以下几种：

filter

:   默认表，用于包过滤，其中 DROP 和 REJECT 目标通常只用在此表中。

nat

:   用于网络地址转换（NAT），如源地址转换（SNAT）和目的地址转换（DNAT）。其中「伪装」（MASQUERADE）是一种特殊的 SNAT 方式，让内核根据出接口网卡上配置的地址自动决定替换后的源地址，通常用于动态 IP 地址的场景。

    需要注意的是，nat 表的 PREROUTING 和 OUTPUT 链只能使用 DNAT 目标，而 INPUT 和 POSTROUTING 链只能使用 SNAT（或 MASQUERADE）目标。
    这是因为 iptables 将 Netfilter 的两种 hook 优先级（`NAT_DST` 和 `NAT_SRC`）都放进了 nat 表，因此尽管四个链都在 nat 表中，它们实际上是分属于两种不同的 Netfilter hook。

    特别的是，仅有建立新连接的数据包会经过 nat 表，而已经建立连接的数据包不会经过 nat 表，而是由 [conntrack 模块](#conntrack)处理。
    对于用户而言，可以理解为「nat 表自带 `--ctstate NEW` 约束[^nf_nat_inet_fn]，之后的数据包都使用已经转换后的地址进行通信」。

  [^nf_nat_inet_fn]: 该约束事实上是「NEW 或 RELATED」，具体可参考 [`nf_nat_inet_fn`](https://elixir.bootlin.com/linux/v6.17.8/source/net/netfilter/nf_nat_core.c#L936) 函数。

mangle

:   用于修改原始数据包，如更改 TOS（服务类型）或 TTL（生存时间），也包括打上防火墙标记（`-j MARK`）。这个表通常用于高级的包处理。

raw

:   用于处理原始数据包，将包标记为不经过连接跟踪（如 `-j CT --notrack`），或引入其他连接跟踪帮助模块（如 `-j CT --helper`）。

另有 security 表用于 SELinux 等安全模块的集成，但在大多数系统中不常用。Security 表与 filter 表适用于相同的阶段（Netfilter hook 点），且运行在 filter 表之后，即能够进入 security 表中的数据包都已由 filter 表标记为接受（ACCEPT）了。

iptables 的每个表都会注册到对应的 Netfilter hook 优先级上，因此同一个阶段（例如 PREROUTING）中，不同表的处理顺序与 [hook 的优先级](#netfilter-hook-priorities)相同。

各个表在各个阶段的可用性如下表所示：
{: #iptables-tables-validity }

|    阶段     |            filter / security             |    nat    |                  mangle                  |                   raw                    |
| :---------: | :--------------------------------------: | :-------: | :--------------------------------------: | :--------------------------------------: |
| PREROUTING  |                                          | DNAT only | :fontawesome-solid-check:{: .limegreen } | :fontawesome-solid-check:{: .limegreen } |
|    INPUT    | :fontawesome-solid-check:{: .limegreen } | SNAT only | :fontawesome-solid-check:{: .limegreen } |                                          |
|   FORWARD   | :fontawesome-solid-check:{: .limegreen } |           | :fontawesome-solid-check:{: .limegreen } |                                          |
|   OUTPUT    | :fontawesome-solid-check:{: .limegreen } | DNAT only | :fontawesome-solid-check:{: .limegreen } | :fontawesome-solid-check:{: .limegreen } |
| POSTROUTING |                                          | SNAT only | :fontawesome-solid-check:{: .limegreen } |                                          |

若从 Netfilter 自己的视角，将网卡和本地进程（数据包的来源和接收者）都看作外部元素的话，各个阶段及其可用的表和处理顺序如下图所示：

![Netfilter 阶段](../../images/netfilter-kernel-view-tables.svg)
{#netfilter-kernel-view-tables}

/// caption
从 Netfilter 自己的视角看各个阶段，以及每个阶段可用的表
///

### iptables-save {#iptables-save}

## nftables {#nftables}
