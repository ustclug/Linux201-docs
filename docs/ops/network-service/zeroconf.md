---
icon: material/help-network
---

# Zeroconf

!!! note "主要作者"

    [@taoky][taoky]

!!! warning "本文编写中"

Zeroconf 是一套在局域网中进行自动网络配置的方案，分为三个部分：

- Link-local 地址分配：在没有 DHCP 服务器的情况下，设备可以为自己分配一个 link-local 地址。
    - 但是正常情况下，不会有人依赖于这个特性组网。
- 名称解析：设备可以通过 mDNS 协议解析局域网内部其他设备的名称。
- 服务发现：设备可以通过 DNS-SD 协议发现其他设备提供的服务。

以下主要介绍上面三个部分的需求对应的各类协议，包括但不限于 mDNS 与 DNS-SD。

## Link-local 地址分配 {#link-local}

<!-- How IPv4 & IPv6 handle this -->
<!-- Why nobody uses them -->

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
