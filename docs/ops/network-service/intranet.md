# 隧道组网

!!! note "主要作者"

    [@yuanyiwei][yuanyiwei]、[@sscscc][sscscc]、[@tiankaima][tiankaima]

!!! warning "本文初稿编写中"

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

TODO

也可以使用如 [yangzhaofengsteven/strongswan](https://hub.docker.com/r/yangzhaofengsteven/strongswan) 等 docker 镜像。

#### 配置证书和路由

## AnyConnect

AnyConnect 是由思科开发的专用 VPN 协议，由 TLS 负责数据的传输安全。其客户端易于使用、并且跨平台，该协议较为流行。

然而 AnyConnect 作为 Cisco 专有协议，我们一般使用兼容 AnyConnect 协议的服务端 [openconnect/ocserv](https://gitlab.com/openconnect/ocserv)。

### 安装 ocserv

[yangzhaofengsteven/ocserv](https://hub.docker.com/r/yangzhaofengsteven/ocserv) docker 镜像

## OpenVPN

OpenVPN 是一款开源的 VPN 协议，使用 TLS 进行认证。相比其他协议，其服务端性能开销较大。

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

## Headscale

在部分场景下，单纯 Wireguard 不能很好满足需求，例如需要 peer-to-peer 之间的互联（不经过中心节点），或者在更复杂的网络环境下。[Tailscale](https://tailscale.com/kb/1151/what-is-tailscale) 便是一个解决方案，我们这里介绍 Headscale，一个开源的 Tailscale 服务端实现。

> Headscale 仅是 Tailscale 的一个开源、可自行部署的实现，客户端仍需要使用 Tailscale。

### 安装 Headscale

截止编辑时，Headscale 尚不提供 apt repo，需要在 [GitHub Release](https://github.com/juanfont/headscale/releases) 选择 `.deb` 安装：

```shell
wget --output-document=headscale.deb <URL>
sudo apt install ./headscale.deb
```

### 配置 Headscale

配置文件位于 `/etc/headscale/config.yaml`，默认配置文件：<https://github.com/juanfont/headscale/blob/main/config-example.yaml>

### 启动 Headscale

```shell
sudo systemctl enable --now headscale
sudo systemctl status headscale
```

### 安装 Headscale-ui

与 Tailscale 不同，Headscale 目前没有集成的 Admin Console，可以部署 [headscale-ui](https://github.com/gurucomputing/headscale-ui) 替代部分功能。这是一个纯静态的 Web 界面，可以在 [GitHub Release](https://github.com/gurucomputing/headscale-ui/releases) 下载 `headscale-ui.zip`。

```shell
wget --output-document=headscale-ui.zip <URL>
unzip headscale-ui.zip -d /var/www/headscale-ui
```

### 配置反向代理

以 Caddy 为例，我们演示如何配置 Headscale & Headscale-ui：

```txt title="/etc/caddy/Caddyfile"
headscale.****.**** {
        handle_path /web* {
                root * /var/www/headscale-ui
                file_server
        }

        reverse_proxy * 127.0.0.1:8080
}
```

Nginx 配置文件可以参考：<https://headscale.net/ref/integration/reverse-proxy/#nginx>

### 设置 API Key

```shell
sudo headscale apikeys create --expiration 9999d
```

通过浏览器访问 `/web`，在 Settings 界面中填写 API Key。

### 添加用户

```shell
sudo headscale users create <NAME>
```

### 客户端设置

与一般连接 Tailscale 方法不同，需要指定 `--login-server` 和 `--auth-key`：

```shell
tailscale up --login-server <URL> --authkey <KEY>
```

其中 `authkey` 可以在管理面板（headscale-ui）中获取，也可以使用下面的命令：

```shell
sudo headscale preauthkeys create --user <NAME>
```

### 列出其他节点

```shell
tailscale status
```
