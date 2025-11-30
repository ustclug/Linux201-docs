---
icon: material/skull-scan
---

# Nmap

!!! note "主要作者"

    [@taoky][taoky]、[@sscscc][sscscc]

!!! success "本文已完成"

Nmap（Network Mapper）是开源的网络探测和安全检查工具。其主要功能包括主机发现、端口扫描、服务版本探测、操作系统检测、脚本扫描等。不管是在红方（攻击方）还是蓝方（防御方）的工作中，Nmap 都是一个非常有用的工具。

以下介绍 Nmap 的常用功能。

!!! danger "请勿进行未经授权的扫描操作"

    再次重复：**扫描器本身是中性的工具，既可以帮助系统管理员检查已有的系统的问题，也可以帮助攻击者快速发现已有的安全漏洞。请仅在得到授权的前提下使用这类工具，否则可能会有严重的法律风险。**

!!! tip "GUI 版本"

    如果你不喜欢命令行，可以使用 Zenmap，它提供了相对用户友好的界面来运行 Nmap。

## 基本扫描 {#basic-scanning}

对系统管理员，Nmap 的一个重要用途是搞清楚自己管理的网络中的资产情况。Nmap 可以扫描指定网段中存活（在线）的主机与开放的端口。

以下假设网络段为 192.168.1.0/24。

!!! tip "扫描到哪里了？"

    在扫描中按下任意键可以显示进度。

### 存活检测 {#alive-detection}

Nmap 的 `-sn` 选项会关闭端口扫描，只进行存活检测。`-sn` 选项会发送 ICMP Echo（ping）、TCP SYN 到 443（HTTPS）端口和 TCP ACK 到 80（HTTP）端口，以及发送 ICMP Timestamp 请求来检测主机是否在线。

!!! note "为什么 TCP SYN 到 443，但是 TCP ACK 到 80？"

    很多防火墙会配置直接丢弃对非公开服务端口的 TCP SYN 请求包，但是不是所有防火墙都会丢弃 TCP ACK 请求包，特别是对应防火墙没有记录 TCP 连接状态的情况下。因此采取不同的 TCP 包探测方式可以提高存活检测的成功率。

!!! note "ICMP Timestamp"

    ICMP Timestamp 请求是一个较少使用的 ICMP 类型，用来获取目标主机的时间信息。部分现代操作系统默认不响应此请求。

    可以使用 Nmap 提供的 `nping` 工具测试：

    ```shell
    sudo nping --icmp --icmp-type timestamp 192.168.1.2
    ```

!!! tip "使用 root 执行"

    由于发送 ICMP 包需要特权（创建 raw socket），如果希望 Nmap 把所有的扫描方法都用上，建议采用 `sudo` 执行 Nmap。此外，只发送 TCP SYN、TCP ACK 也需要特权，如果以普通用户运行，Nmap 会使用 `connect()` 系统调用来检测存活主机，因此只发送 TCP ACK 在这种条件下无法实现。

    如果扫描的是本地网络并且是 root，Nmap 还会尝试使用 ARP 请求来检测存活主机。

!!! tip "关闭 DNS 解析"

    Nmap 默认会尝试从 IP 地址使用 DNS 解析主机名，这很多时候是没有必要的，而且会占用大量时间。可以使用 `-n` 选项关闭 DNS 解析。

!!! tip "减小等待时间"

    Nmap 的 `-T` 参数会控制操作的时间间隔，默认是 `-T3`。如果网络情况好，可以使用 `-T4` 或 `-T5` 来加快扫描速度。

可以使用 `-P` 系列参数限制存活检测的方式（默认行为相当于 `-PE -PS443 -PA80 -PP`），例如只允许进行 ICMP Echo 请求（在权限不足的情况下，Nmap 会自动降级到使用 TCP）：

```shell
nmap -n -sn -PE 192.168.1.0/24
```

或者只允许 TCP SYN 到 443 端口：

```shell
nmap -n -sn -PS443 192.168.1.0/24
```

!!! tip "跳过某些主机"

    如果你想扫描整个网络，但需要跳过某些主机，可以使用 `--exclude` 选项。

!!! question "第一天的工作"

    假设你刚刚加入了一个新的团队，上一任的系统管理员没有留下任何文档。为了搞清楚有哪些机器，你需要做什么来获取你需要扫描的网段？

### 端口扫描 {#port-scanning}

获取存活主机后，下一步是获取这些主机上开放的端口。最常用的扫描方式有三种：

- TCP SYN 扫描 `-sS`（需要特权）
- TCP connect 扫描 `-sT`
- UDP 扫描 `-sU`

此外，Nmap 默认只会扫描最常用的 1000 种端口。`-p` 选项可以指定要扫描的端口（例如 `-p 12345`），或者端口范围（例如 `-p 1-1024`）。如果希望让 Nmap 扫描所有端口，可以使用 `-p-`。

!!! question "扫描网段内的指定端口"

    你想扫描整个网段内有哪些主机开放了 22 端口（SSH），应该怎么写参数？

!!! tip "rustscan 和 masscan"

    在端口扫描领域，除了 Nmap 以外还有一些其他的工具。其中常用的包括：
    
    - [rustscan](https://github.com/bee-san/RustScan)，其默认配置就能够非常快速扫描全部端口。
    - [masscan](https://github.com/robertdavidgraham/masscan)，用于超大规模扫描的工具，其宣称可以在 5 分钟内扫描整个互联网。

## 进一步检测 {#further-detection}

### 服务和版本检测 {#service-and-version-detection}

`-sV` 选项可以让 Nmap 尝试检测开放端口上运行的服务和版本信息，因为很多网络服务的实现都会以某种方式透露自己的信息，例如 SSH 服务会在连接时发送版本信息：

```console
$ nc example.com 22
SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u6
```

服务和版本检测耗费时间较长，特别是在不限制端口的情况下。一个检测例子如下：

```console
$ nmap -sV 192.168.1.247
Starting Nmap 7.97 ( https://nmap.org ) at 2025-08-03 21:43 +0800
Nmap scan report for bogon (192.168.1.247)
Host is up (0.000069s latency).
Not shown: 992 closed tcp ports (conn-refused)
PORT      STATE SERVICE           VERSION
22/tcp    open  ssh               OpenSSH 9.2p1 Debian 2+deb12u6 (protocol 2.0)
80/tcp    open  http              OpenResty web app server 1.27.1.2
111/tcp   open  rpcbind           2-4 (RPC #100000)
1145/tcp  open  http              Caddy httpd
2049/tcp  open  nfs_acl           3 (RPC #100227)
3260/tcp  open  iscsi?
10000/tcp open  snet-sensor-mgmt?
10001/tcp open  http              Node.js Express framework
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
（省略）
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 172.50 seconds
```

### 操作系统检测 {#os-detection}

`-O` 选项可以让 Nmap 尝试检测目标主机的操作系统。Nmap 会根据 TCP/IP 协议栈的特征来猜测操作系统类型和版本。该操作需要特权。

```console
$ sudo nmap -O 192.168.1.253
（省略）
Device type: general purpose|router
Running: Linux 4.X|5.X, MikroTik RouterOS 7.X
OS CPE: cpe:/o:linux:linux_kernel:4 cpe:/o:linux:linux_kernel:5 cpe:/o:mikrotik:routeros:7 cpe:/o:linux:linux_kernel:5.6.3
OS details: Linux 4.15 - 5.19, OpenWrt 21.02 (Linux 5.4), MikroTik RouterOS 7.2 - 7.5 (Linux 5.6.3)
Network Distance: 1 hop
（省略）
```

## 脚本简介 {#scripts}

Nmap 的 Nmap Scripting Engine（NSE）功能允许用户编写 Lua 脚本扩展 Nmap 的功能，执行自动化任务。目前，Nmap 自带了[六百多种 NSE 脚本](https://nmap.org/nsedoc/scripts/)，分为不同的几类（详见 [Usage and Examples](https://nmap.org/book/nse-usage.html)）。使用 `-sC` 或 `--script=default` 选项可以让 Nmap 使用默认（default）这一分类的脚本对指定主机执行，能够做一些基本的信息收集任务。

如果要执行具体某个脚本，使用 `--script` 选项指定脚本名称。例如获取 banner（服务版本信息）：

```console
$ nmap --script=banner 192.168.1.253
Starting Nmap 7.97 ( https://nmap.org ) at 2025-08-04 01:45 +0800
Nmap scan report for bogon (192.168.1.253)
Host is up (0.0034s latency).
Not shown: 999 closed tcp ports (conn-refused)
PORT   STATE SERVICE
22/tcp open  ssh
|_banner: SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u7

Nmap done: 1 IP address (1 host up) scanned in 10.23 seconds
```

!!! tip "部分 NSE 脚本示例"

    正如最开始所说的那样，Nmap 是一个中性的工具，其自带脚本集也是如此：一些脚本可以用于调试用途，另一些脚本则非常有攻击性。例如 [`broadcast-dhcp-discover`](https://nmap.org/nsedoc/scripts/broadcast-dhcp-discover.html) 脚本会广播发送 `DHCPDISCOVER`，输出得到的 `DHCPOFFER`，可以帮助系统管理员检查 DHCP 服务器是否存在问题；而 [`ssh-brute`](https://nmap.org/nsedoc/scripts/ssh-brute.html) 则会尝试暴力破解 SSH 密码。

    可以补充阅读 [Red Hat Blog 的文章 *5 scripts for getting started with the Nmap Scripting Engine*](https://www.redhat.com/en/blog/nmap-scripting-engine) 作为参考。
