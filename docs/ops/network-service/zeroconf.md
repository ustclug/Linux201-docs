---
icon: material/help-network
---

# Zeroconf

!!! note "主要作者"

    [@taoky][taoky]

!!! warning "本文编写中"

Zeroconf 是一套在局域网中进行自动网络配置的方案，分为三个部分：

- Link-local 地址分配：在没有 DHCP 服务器的情况下，设备可以为自己分配一个 link-local 地址。
    - 但是正常情况下，不会有人依赖于这个特性组网。这个特性主要用于点对点连接（例如两台电脑通过网线直接连接），或者小型的、不需要访问外部网络的局域网中。
- 名称解析：设备可以通过 mDNS 协议解析局域网内部其他设备的名称。
- 服务发现：设备可以通过 DNS-SD 协议发现其他设备提供的服务。

以下主要介绍上面三个部分的需求对应的各类协议，包括但不限于 mDNS 与 DNS-SD。

## Link-local 地址分配 {#link-local}

Link-local 在 IPv4 和 IPv6 中有着不同的表现。IPv4 下，如果网络中没有 DHCP 服务器，并且用户也没有手动配置 IP 地址，那么设备会自动为自己分配一个 Link-local 地址。这个地址在 169.254.0.0/16（除了 169.254.0.0/24 和 169.254.255.0/24 以外）中。在 IPv4 下的 Link-local 地址分配使用的是 APIPA（Automatic Private IP Addressing）协议，这个协议很简单：

1. 随机在上面的地址段中选择一个地址。
2. 发送 ARP 请求，检查这个地址是否已经被使用。
3. 如果有人回应了 ARP 请求，说明地址已经被使用，回到步骤 1。

而在 IPv6 下，Link-local 的地址段是 `fe80::/10`，无论如何，设备都会为自己分配一个 Link-local 地址（有些设备上会基于接口的 MAC 地址来分配），所以在支持 IPv6 的场合下，你会发现设备会有多个 IPv6 地址，其中就包括一个 Link-local 地址。和 IPv4 类似，在选择地址之后，也需要避免和其他人的地址冲突。IPv6 不再使用 ARP，而是使用基于 ICMPv6 的 NDP（Neighbor Discovery Protocol）完成地址冲突检测（DAD，Duplicate Address Detection）。

!!! note "为什么 IPv6 没有 ARP？"

    IPv6 并非「更大地址空间的 IPv4」。IPv6 的设计者在设计时，就希望将 IPv4 中能用，但是设计得不好的东西改进掉。ARP 是一个横跨二层（数据链路层，最常见的是以太网）和三层（网络层，这里是 IP）的特殊协议，在解析 IP 到 MAC 地址的过程中需要在二层广播（在以太网中，是将目标 MAC 地址设置为 ff:ff:ff:ff:ff:ff），在大型网络中这样做开销很大。而 ARP 也无法基于 ICMP 实现，因为 ICMP 协议依赖于 IP 层，而 ARP 要解决的问题就是在 IP 层还没有准备好的时候，获取 IP 到 MAC 的映射关系。

    而在 IPv6 中，所有接口都必须有 Link-local 地址，因此 NDP 就可以在 ICMPv6 的基础上实现。在检测地址冲突时，NDP 会构造 [solicited-node multicast address](https://datatracker.ietf.org/doc/html/rfc4291#section-2.7.1) 多播地址，只有可能使用该地址的节点会收到这个多播包，从而避免了广播带来的开销。

!!! note "Link-local 地址 = 网坏了？"

    有一定网络经验的读者可能对 169.254.0.0/16 和 fe80::/10 这两个地址段比较熟悉，因为如果自己的设备只分配到了这个地址段的地址，通常意味着网络出现了问题。

    对 IPv4 来说，这是因为 DHCP 服务器做的事情除了分配 IP 地址以外，还会将网关、DNS 服务器等信息一并发送给客户端，而如果没有网关信息的话，设备就无法和局域网外的设备通信了（无法连接到互联网），对很多场景来讲，这就是网络出现了故障的表现。

    那么，假如我们回到过去，修改 IPv4 下关于 Link-local 的约定，让设备在 APIPA 的时候自动将默认网关和默认 DNS 设置为 169.254.0.1 的话，那么就可以不需要 DHCP 服务器，也能够组建小型的局域网络，并且让这个网络有访问外部网络的能力了（假设网关支持 NAT）——这个模型就比较接近 IPv6 有关 Link-local 的设计思路了。

    在 IPv6 下，路由器需要通过 RA（Router Advertisement）消息告诉设备包括网关、网络前缀、DNS 等信息，在 Link-local 地址收到 RA 之后，设备会使用 SLAAC（Stateless Address Autoconfiguration）为自己分配一个全局单播地址（这个地址是全局唯一的——可以在其他的网络里面访问），从而实现和外部网络的通信。在 IPv6 下，Link-local 地址是「IPv6 控制面」接口，不承载其他的功能。

## 名称解析 {#name-resolution}

<!-- mDNS and LLMNR -->

## 服务发现 {#service-discovery}

<!-- Introduce NetBIOS -->
<!-- Introduce WSD and DNS-SD -->

如果你使用过较早期版本的 Windows，那么你肯定会熟悉「网上邻居」这个功能。在「网上邻居」里，你可以看到局域网内其他计算机，以及它们共享的文件夹、打印机等资源。早期这个功能依赖于 NetBIOS 来实现。

!!! note "NetBIOS"

    NetBIOS（以下均指代 NetBIOS over TCP/IP）需要三种端口：

    - 命名与解析（TCP 137 和 UDP 137）：NetBIOS 会广播主机名，并确定是否存在冲突。其他计算机可以使用主机名连接。由于等待冲突检测会花掉比较长的时间，因此之后添加了 WINS（Windows Internet Name Service）来集中管理主机名，Windows 在查找到 WINS 服务器后会优先使用 WINS。尽管不是以 DNS 的形式存在，但是 Windows 机器可以以此解析主机名对应的 IP 地址。
    - UDP 138：用于无 session 的消息传递。
    - TCP 139：用于有 session 的消息传递。

    NetBIOS 上面可以运行应用，例如 Browser 服务与 SMB 服务。

    Browser 服务维护了局域网中的网络资源列表（就是以前「网上邻居」里面你可以看到的内容），局域网的 Windows 机器会根据 Windows 版本号、类型（是桌面还是服务器系统）等信息来「选举」出一个 master browser，由 master browser 维护这个列表。

    SMB 服务最早也依赖于 NetBIOS——不过，从 Windows 2000 开始，SMB 已经可以直接在 TCP 445 端口上运行，而不再需要 NetBIOS。

    此外，「臭名昭著」的 Windows Messenger service 也是基于 NetBIOS 的。这个服务允许你用 `net send` 命令向网络上其他计算机发送消息，比如说：

    ```cmd
    net send somehost "你的电脑被黑了！"
    ```

    然后 somehost 上面就会弹出这么一个对话框。可能相比于正经用途来说，Messenger 服务被拿来整人和干坏事的频率更高一些，因此在 Windows XP SP2 后默认被禁用，且之后被彻底移除了。

    出于安全等考虑，目前除非需要兼容老设备，否则**不建议使用 NetBIOS**。Windows 10 之后的版本也已经不再默认启用 NetBIOS。

目前最常见的服务自动发现协议是 DNS-SD：它依赖 mDNS 负责局域网内的主机名解析，而 DNS-SD 则在 mDNS 基础上负责服务发现，但是 Windows 目前对此的支持不佳。Windows 则会使用 WS‑Discovery（Web Services Dynamic Discovery）来发现局域网中的服务。
