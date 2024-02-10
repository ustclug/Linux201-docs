# 隧道组网

!!! warning "本文仍在编辑中"

在网络中，隧道是一种将数据包从一个网络节点封装并传输到另一个网络节点的技术。它可以用于在两个不同的网络之间建立虚拟连接，也可以用于绕过防火墙或其他网络限制。

在隧道中，数据包会被封装在一个新的数据包中，并使用隧道协议进行传输。

在虚拟专用网络（VPN）中，隧道用于将用户设备与 VPN 服务器之间的通信加密并封装。这使得用户设备可以安全地连接到 VPN 服务器，并通过 VPN 服务器访问受限的网络资源，通常是内网环境（IntraNet）下的各种服务。

如今略显陈旧的 PPTP、SSTP、L2TP 协议下面不再提及。一些高校和企业使用的深信服 EasyConnect 由于服务端并未放出且仍在使用 Java applet 实现 SSL VPN，因此同样略过。

## IPsec

标准化程度高，支持广泛

### GRE over IPsec

## AnyConnect

是思科的专有软件，但是 [openconnect/ocserv](https://gitlab.com/openconnect/ocserv) 兼容了其协议

易于使用，安全性高，支持多种平台

## OpenVPN

开源，免费，可定制，但是速度相对较慢

## IKEv2

安全性高，易于配置，但是基于 udp

## WireGuard

WireGuard 是一种现代的 VPN 协议，速度快，配置简单，安全性高，但是基于 udp
