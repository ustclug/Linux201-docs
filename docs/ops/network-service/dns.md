---
icon: material/dns
---

# DNS

!!! note "主要作者"

    [@taoky][taoky]

!!! warning "本文编写中"

DNS 是网络最重要的组件之一。如果 DNS 出现问题，那么可能会以非预期的方式把其他的东西一起弄坏，甚至在不少「高可用」的场景下，DNS 故障也可能会让整个集群出现问题。以至于有人写[俳句](https://dnshaiku.com/)如下：

> It’s not DNS
>
> There’s no way it’s DNS
>
> It was DNS.

以下分别介绍在 Linux 客户端和服务端，DNS 相关的配置和使用方法。

## 客户端 {#client}

说到 DNS，你可能首先想到的是 `/etc/resolv.conf` 文件，可以像这样配置使用的 DNS 服务器：

```text
nameserver 8.8.8.8
```

事实上，上面的知识对解决一部分 DNS 问题已经足够了。但是很多时候事情没有那么简单：

- nsswitch.conf 是什么东西？
- 为什么我的 resolv.conf 写的是 127.0.0.53？
- 为什么 Alpine 容器的 DNS 行为好像不太一样？

为了解决这些疑难杂症，我们就需要完整了解 Linux 下 DNS 解析的相关组件。

### C 库提供的 DNS 解析接口 {#libc-dns}

在最早期的时候，C 运行时库提供 [`gethostbyname()`][gethostbyname.3] 和 [`gethostbyaddr()`][gethostbyname.3] 函数来进行 DNS 解析：

```c
// 获取 example.com 解析的 IP
struct hostent host_1 = gethostbyname("example.com");
// 地址在 he->h_addr_list 列表中

// 获取 1.1.1.1 对应的域名
const char *ip_str = "1.1.1.1";
struct in_addr ip;
inet_aton(ip_str, &ip);
struct hostent host_2 = gethostbyaddr(&ip, sizeof(ip), AF_INET);
// 域名在 he->h_name 中
```

!!! tip "从 IP 反查域名"

    很多人对 DNS 的理解仅限于「从域名查 IP」（A 记录和 AAAA 记录），但 DNS 也支持「从 IP 查域名」（PTR 记录）。例如对上面 1.1.1.1 的域名的查询，可以先构造出 `1.1.1.1.in-addr.arpa` 这个域名，然后查询这个域名的 PTR 记录。

    PTR 记录由 IP 的所有者（ISP/云服务商等）负责维护。

但是 `gethostbyname` 和 `gethostbyaddr` 这两个函数已经过时了——`gethostbyname` 不支持 IPv6（AAAA），而且这两个函数都不是线程安全的。因此现代 POSIX 标准引入了 [`getaddrinfo()`][getaddrinfo.3]（有时候也简称为 gai）和 [`getnameinfo()`][getnameinfo.3] 函数来替代它们：

```c
// 获取 example.com 解析的 IP
struct addrinfo hints, *res;
memset(&hints, 0, sizeof(hints));
hints.ai_family = AF_UNSPEC; // IPv4 + IPv6
hints.ai_socktype = SOCK_STREAM;
int ret_1 = getaddrinfo("example.com", NULL, &hints, &res);
// 地址在 res 链表中

// 获取 1.1.1.1 对应的域名
struct sockaddr_in sa;
char hostname[NI_MAXHOST];
memset(&sa, 0, sizeof(sa));
sa.sin_family = AF_INET;
sa.sin_port = htons(53);
inet_pton(AF_INET, "1.1.1.1", &sa.sin_addr);
int ret_2 = getnameinfo((struct sockaddr *)&sa, sizeof(sa),
                        hostname, sizeof(hostname), NULL, 0, 0);
// 域名在 hostname 中
```

不同的 C 运行时库对 DNS 会采取不同的解析方式。以下介绍 Linux 下最流行的两种 C 运行时库：glibc 和 musl。

#### glibc

glibc 会使用一套复杂的逻辑来决定如何解析用户提供的域名。其 [`getaddrinfo()`](https://elixir.bootlin.com/glibc/glibc-2.42.9000/source/nss/getaddrinfo.c#L2286) 的内部实现调用了 [`gaih_inet()`](https://elixir.bootlin.com/glibc/glibc-2.42.9000/source/nss/getaddrinfo.c#L1134) 函数执行实际的解析工作。简单来讲，这个函数会：

1. 尝试从 nscd 缓存中获取结果（如果编译期启用了相关支持）
2. 如果 nscd 缓存没有结果，那么就根据 `/etc/nsswitch.conf` 文件中的配置，依次使用不同的 NSS（Name Service Switch）模块来解析域名

在 `gaih_inet()` 完成后，`getaddrinfo()` 会根据 [RFC 3484](https://datatracker.ietf.org/doc/html/rfc3484) 的规则，对返回的结果进行排序，然后返回给用户。

##### nscd

[nscd][nscd.8]（Name Service Cache Daemon）是 glibc 提供的用于缓存 DNS 等结果的服务。如果你在 Debian 下尝试对使用 glibc DNS 查询的程序 `strace` 的话，你会发现 glibc 会尝试连接 `/var/run/nscd/socket`：

```text
socket(AF_UNIX, SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK, 0) = 3
connect(3, {sa_family=AF_UNIX, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT (No such file or directory)
close(3)                                = 0
socket(AF_UNIX, SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK, 0) = 3
connect(3, {sa_family=AF_UNIX, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT (No such file or directory)
close(3)                                = 0
```

尽管 Debian 的 glibc 仍然还有 nscd 的支持，但是其他一些发行版，例如 [Fedora](https://fedoraproject.org/wiki/Changes/RemoveNSCD)、[Arch Linux](https://gitlab.archlinux.org/archlinux/packaging/packages/glibc/-/blob/bb99fc244e3d1404c3d5fdd2d205bfe4bb6080bd/PKGBUILD#L57) 等都移除了 nscd 的支持，因为：

- nscd [bug 较多](https://fedoraproject.org/wiki/Changes/DeprecateNSCD#Benefit_to_Fedora)，[不太稳定](https://jameshfisher.com/2018/02/05/dont-use-nscd/)。
- nscd 除了缓存 DNS 以外的部分（缓存用户信息等）已经被 sssd（System Security Services Daemon）代替了。
- nscd 强绑定了 glibc，并且不适用于容器化场景（你需要把 `/var/run/nscd/socket` 给 bind mount 进容器，有些太疯狂了）。
- 本地运行的 DNS 缓存服务（例如 systemd-resolved、dnsmasq 等）已经可以很好地完成 DNS 缓存的功能。

因此这里也不推荐使用 nscd。

##### NSS



#### musl

## 服务端 {#server}
