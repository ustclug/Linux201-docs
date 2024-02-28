# 隧道组网

!!! warning "本文仍在编辑中"

在网络中，隧道是一种将数据包从一个网络节点封装并传输到另一个网络节点的技术。它可以用于在两个不同的网络之间建立虚拟连接，也可以用于绕过防火墙或其他网络限制。

在隧道中，数据包会被封装在一个新的数据包中，并使用隧道协议进行传输。

在虚拟专用网络（VPN）中，隧道用于将用户设备与 VPN 服务器之间的通信加密并封装。这使得用户设备可以安全地连接到 VPN 服务器，并通过 VPN 服务器访问受限的网络资源，通常是内网环境（IntraNet）下的各种服务。

如今略显陈旧的 PPTP、SSTP、L2TP 协议下面不再提及。一些高校和企业使用的深信服 EasyConnect 由于服务端并未放出，且其仍在使用过时的 Java applet 实现 SSL VPN，因此略过。

## IPsec

标准化程度高，支持广泛

### GRE over IPsec

### IKEv2

IKEv2 是一种安全性高、易于配置的 VPN 协议，由 IPsec 负责数据的传输安全，基于 UDP 协议。大部分系统都内建了对 IKEv2 协议的支持。

#### 安装 strongSwan

在 Linux 上的开源 IKEv2/IPsec 实现有 strongSwan、Libreswan，和已经停止更新的 Openswan。本文使用 strongSwan。

大多数现代 Linux 发行版都可以直接从官方仓库中安装 strongSwan。例如，在基于 Debian 的系统（如 Ubuntu）上，你可以使用以下命令安装：

```shell
sudo apt update
sudo apt install strongswan
```

strongSwan 当前提供多种 daemon：

- `strongswan-starter.service` 来自 `strongswan-starter`
- `strongswan.service` 来自 `charon-systemd`

## AnyConnect

是思科的专有软件，但是 [openconnect/ocserv](https://gitlab.com/openconnect/ocserv) 兼容了其协议

易于使用，安全性高，支持多种平台

## OpenVPN

开源，免费，可定制，但是速度相对较慢

## WireGuard

WireGuard 是一种现代的 VPN 协议，速度快、配置简单、安全性良好，基于 UDP 协议。

### 安装 WireGuard

大多数现代 Linux 发行版都可以直接从官方仓库中安装 WireGuard。例如，在基于 Debian 的系统（如 Ubuntu）上，你可以使用以下命令安装：

```shell
sudo apt update
sudo apt install wireguard
```

在 Red Hat 或 Fedora 系列的系统上，你可以使用 `dnf`：

```shell
sudo dnf install wireguard-tools
```

### 生成密钥对

每个 WireGuard 接口都需要一个私钥和公钥。`wg genkey` 生成一个私钥，`wg pubkey` 根据输入的私钥输出公钥。

使用下面的命令生成密钥对：

```shell
wg genkey | tee privatekey | wg pubkey > publickey
```

这将在当前目录下生成两个文件：`privatekey` 和 `publickey`。

### 创建配置文件

这里以一个简单的场景为例，两台机器 A 和 B 进行组网。其中 A 有公网 IP，对应域名 `example.com`。

A 的配置如下：

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <A 的私钥>

[Peer]
PublicKey = <B 的公钥>
AllowedIPs = 10.0.0.4/32
```

B 的配置如下：

```ini
[Interface]
Address = 10.0.0.4/24
PrivateKey = <B 的私钥>

[Peer]
PublicKey = <A 的公钥>
Endpoint = example.com:51820
AllowedIPs = 10.0.11.0/24
PersistentKeepalive = 25
```

上述配置文件中，密钥的替换成密钥的**内容**，而不是密钥文件的路径。

设备 A 的 VPN 内部 IP 地址设置为 `10.0.0.1`，设备 B 的 VPN 内部 IP 地址设置为 `10.0.0.4`，子网掩码为 24 位。

`PersistentKeepalive = 25` 代表每 25 秒发送一个无实质数据的心跳包，用于在 NAT 或防火墙环境中保持连接活跃。

`AllowedIPs` 指定了可以通过 VPN 发送到哪些 IP 地址的数据。例如 `10.0.0.1/32` 表示只有目标为 `10.0.0.1` 的数据包可以通过 VPN 发送给对方。

配置文件需要写在 `/etc/wireguard/<配置名>.conf` 中。例如：`/etc/wireguard/wg0.conf`。

### 启动 WireGuard 接口

使用 `wg-quick` 工具启动 WireGuard 接口：

```shell
sudo wg-quick up wg0
```

其中 `wg0` 是配置文件的名称，不包括 `.conf` 后缀。

### 检查接口状态

可以使用 `wg` 命令查看当前的 WireGuard 状态：

```shell
sudo wg
```

### 停止 WireGuard 接口

当不再需要时，可以使用以下命令停止接口：

```shell
sudo wg-quick down wg0
```
