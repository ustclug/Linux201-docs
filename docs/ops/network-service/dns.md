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

!!! note "`res_query`"

    尽管 `getaddrinfo()` 可以解决不少问题，并且跨平台兼容性也不错，但是如果我们需要更底层的 DNS 查询功能（例如查询 A/AAAA 以外的记录）的时候，上面的 API 就不太够用了。而 libresolv（包含在 glibc 中）则提供了更底层的 [`res_nquery()`/`res_query()`][resolver.3] 等接口，便于需要直接构造 DNS 报文进行查询的程序使用。

    musl 不支持 `res_nquery()`，但是支持 `res_query()`。

    libresolv 在其他平台上可能有不同的行为，可参考：[getaddrinfo sucks. everything else is much worse](https://valentin.gosu.se/blog/2025/02/getaddrinfo-sucks-everything-else-is-much-worse)。

!!! tip "获取 C 库解析 API 的延迟"

    bcc 提供的基于 eBPF 的 [gethostlatency](https://github.com/iovisor/bcc/blob/master/tools/gethostlatency.py) 工具可以用来获取使用 C 运行时库的 DNS 解析延迟：

    ```console
    $ sudo gethostlatency
    TIME     PID     COMM             LATms      HOST
    02:59:28 10680   ThreadPoolForeg  166.831    main.vscode-cdn.net
    ```

    有关 eBPF 的介绍，可参考[问题调试部分](../debug.md#ebpf)。

不同的 C 运行时库对 DNS 会采取不同的解析方式。以下介绍 Linux 下最流行的两种 C 运行时库：glibc 和 musl。

#### glibc

glibc 会使用一套复杂的逻辑来决定如何解析用户提供的域名。其 [`getaddrinfo()`](https://elixir.bootlin.com/glibc/glibc-2.42.9000/source/nss/getaddrinfo.c#L2286) 的内部实现调用了 [`gaih_inet()`](https://elixir.bootlin.com/glibc/glibc-2.42.9000/source/nss/getaddrinfo.c#L1134) 函数执行实际的解析工作。简单来讲，这个函数会：

1. 尝试从 nscd 缓存中获取结果（如果编译期启用了相关支持）
2. 如果 nscd 缓存没有结果，那么就根据 [`/etc/nsswitch.conf`][nsswitch.conf.5] 文件中的配置，依次使用不同的 NSS（Name Service Switch）模块来解析域名

在 `gaih_inet()` 完成后，`getaddrinfo()` 会根据 [RFC 3484](https://datatracker.ietf.org/doc/html/rfc3484)（以及其继任者 [RFC 6724](https://datatracker.ietf.org/doc/html/rfc6724)）的规则，对返回的结果进行排序，然后返回给用户。

##### nscd

[nscd][nscd.8]（Name Service Cache Daemon）是 glibc 提供的用于缓存 DNS、用户信息等结果的服务。如果你在 Debian 下尝试对使用 glibc DNS 查询的程序 `strace` 的话，你会发现 glibc 会尝试连接 `/var/run/nscd/socket`：

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

如果需要清理 nscd 的缓存，可以使用 `nscd -i` 命令。

##### NSS

NSS 模块是 glibc 提供的一套插件机制，用于从不同的数据源获取名称解析结果。相关模块的配置在 `/etc/nsswitch.conf` 文件中。glibc 会根据这个配置加载 NSS 模块（`/lib/libnss_xxx.so`，`xxx` 为模块名，如 `files`），然后调用模块中的接口来获取名称解析结果。

以下是 Debian 13 容器的默认配置：

```text title="/etc/nsswitch.conf"
passwd:         files
group:          files
shadow:         files
gshadow:        files

hosts:          files dns
networks:       files

protocols:      db files
services:       db files
ethers:         db files
rpc:            db files

netgroup:       nis
```

这里与 DNS 相关的配置是 `hosts` 一行，以上配置表示：

1. `files` 模块会解析 `/etc/hosts` 文件的内容，查看是否能够解析。
2. 如果 `files` 模块没有解析出结果，那么就使用 `dns` 模块进行 DNS 查询（使用 `/etc/resolv.conf` 作为配置）。

另一种非常常见的配置是安装了 `systemd-resolved` 的场景。那么 `hosts` 可能会变成这样：

```text
hosts:          files myhostname resolve [!UNAVAIL=return] dns
```

其中 [myhostname][nss-myhostname.8] 负责解析本机的主机名，[resolve][nss-resolve.8] 模块则会通过 `systemd-resolved` 的 Unix socket（`/run/systemd/resolve/io.systemd.Resolve`）来进行解析。

`[!UNAVAIL=return]` 表示，除非（`!`）`resolve` 模块不可用（例如 `systemd-resolved` 没有运行），否则就直接返回，不再继续使用后面的 `dns` 模块。这样设置下，如果 `systemd-resolved` 出现故障，那么系统仍然可以回退到直接使用 DNS 服务器进行解析。而如果只是域名不存在，那么就不会继续使用 `dns` 模块，避免了不必要的 DNS 查询。

可以使用 `getent` 测试 NSS 的解析结果，例如 `getent hosts example.com`、`getent passwd` 等。同时可以使用 `-s` 参数来指定使用的 NSS 模块，用于调试，例如：

```shell
getent -s files hosts example.com
```

就（一般来说）会返回空，因为其只会用 `files` 模块来解析 `example.com`，如果 `/etc/hosts` 中没有相关的记录，那么就不会有结果。

!!! note "NSS 的返回状态"

    NSS 模块可能会返回以下几种状态：

    - `SUCCESS`：解析成功。
    - `NOTFOUND`：没有找到对应的记录。
    - `UNAVAIL`：模块（永久）不可用。
    - `TRYAGAIN`：模块（暂时）不可用，可以重试。

    默认配置相当于 `[SUCCESS=return !SUCCESS=continue]`。除了 `return` 和 `continue` 之外，还有 `merge`：

    ```text
    group:          files [SUCCESS=merge] sss
    ```

    这样的话，如果某用户在本地（`files`）属于组 A，在 sssd（`sss`）中属于组 B，那么最终该用户就会同时属于组 A 和组 B。

!!! note "为什么解析本机还需要 `myhostname` 模块？"

    一个约定俗成的做法是，将主机名放在 `/etc/hostname` 文件，而在 `/etc/hosts` 中添加相关的映射：

    ```text
    127.0.0.1 myhost
    ```

    不过，如果 `/etc/hosts` 里面忘写了/忘改了对应的条目，那么就可能会出现非预期的行为。例如，如果忘记添加 `localhost`，那么有些程序就可能会因为无法解析 `localhost` 而出现问题。
    
    systemd-hostnamed 服务则负责管理系统的主机名——静态的主机名（static hostname）仍然在 `/etc/hostname` 中，用户可读的主机名（pretty hostname，比如说 "Xiao Ming's Computer" 或者 "我的电脑" 这种有空格、特殊字符，甚至汉字的名字）等存储在 `/etc/machine-info` 中，同时其也会记录从网络（例如 DHCP）获取的主机名（transient hostname）。而 `myhostname` 模块就是 systemd-hostnamed 提供的 NSS 模块，确保系统主机名总是可以被正确解析，请看下面的例子：

    ```console
    $ getent -s myhostname hosts localhost
    ::1             localhost
    $ # hostnamed 能获取网络接口的地址
    $ getent -s myhostname hosts myhost
    fd36:cccc:bbbb:aaaa:aaaa:aaaa:aaaa:aaaa myhost
    2001:da8:d800:aaaa:aaaa:aaaa:aaaa:aaaa myhost
    fe80::aaaa:aaaa:aaaa:aaaa:aaaa myhost
    fe80::bbbb:bbbb:bbbb:bbbb:bbbb myhost
    $ getent -s myhostname hosts 127.0.0.1
    127.0.0.1       localhost
    $ # hostnamed 中，127.0.0.2 对应主机名，127.0.0.1 对应 localhost
    $ getent -s myhostname hosts 127.0.0.2
    127.0.0.2       myhost
    ```

!!! note "glibc、NSS 与静态链接"

    如果有尝试对访问网络（使用了 NSS 的）C 程序进行静态链接（`-static`）的话，那么你可能会看到：

    ```
    /usr/bin/ld: /tmp/cchbUcHT.o: in function `main':
    example.c:(.text+0x2a): warning: Using 'gethostbyname' in statically linked applications requires at runtime the shared libraries from the glibc version used for linking
    ```

    这是因为 NSS 是动态加载（`dlopen`）的，如果静态链接之后扔到别的机器上，那么对应的 NSS 模块可能就不存在或者不兼容，从而导致程序无法运行。

##### 地址排序与 gai.conf {#addr-sort-and-gai-conf}

glibc 的 `getaddrinfo()` 默认根据 RFC 3484 的规则对返回的结果进行排序，不过用户也可以在 [`/etc/gai.conf`][gai.conf.5] 文件中自定义排序规则。

RFC 3484 的排序包含两者：源地址选择（source address selection）和目的地址选择（destination address selection）。这里只涉及目的地址选择。目的地址选择具体的规则可以阅读 RFC 的[第 6 节](https://www.rfc-editor.org/rfc/rfc3484#section-6)。其中需要了解的是 [Policy Table（第 2.1 节）](https://www.rfc-editor.org/rfc/rfc3484#section-2.1)，它是一个最长匹配的前缀表，对每个在表中的前缀定义了优先级（Precedence）和标签（Label），这些值会影响排序结果。`gai.conf` 配置的其实就是这个表。

最常见需要修改 `gai.conf` 的情况是希望优先使用 IPv4 地址。在进行目的地址选择时，IPv4 地址会映射到 `::ffff:0:0/96` 前缀（例如 `1.1.1.1` 会映射到 `::ffff:101:101`），而默认情况它的优先级是 10，比其他的 IPv6 地址都要低。因此如果希望优先使用 IPv4 地址，可以添加如下配置：

```text title="/etc/gai.conf"
precedence ::ffff:0:0/96  100
```

##### resolv.conf {#resolv-conf-glibc}

glibc 在实际发 DNS 请求前会读取 [`/etc/resolv.conf`][resolv.conf.5]。其最多支持 [MAXNS](https://elixir.bootlin.com/glibc/glibc-2.42.9000/source/resolv/bits/types/res_state.h#L8)（默认为 3）个 `nameserver` 配置。如果配置了多个 `nameserver`，那么 glibc 会依次尝试这些服务器。

此外，一些可能有帮助的配置包括：

- 对查询非完整域名（例如主机名）的场景，glibc 会依次将 `search` 列表中的域名附加到查询的域名后面进行查询。例如，假设配置了 `search example.com`，那么查询 `myhost` 的时候，会优先搜索 `myhost.example.com`。

    !!! tip "没有点（dot）的公开域名"

        其实反直觉的是，有非常少量（有解析）的域名是没有点的，比如说 `bd`（孟加拉国的顶级域）：

        ```console
        $ dig bd A +short
        203.112.194.232
        ```

    这个行为也可以被 `options ndots:n` 配置项控制，默认值是 1，表示只有查询的域名中没有点的时候，才会使用 `search` 列表进行搜索。

- 默认情况下，glibc 会对每个 `nameserver` 等待 5 秒（`options timeout:n`），尝试 2 次（`options attempts:n`）。所以如果你发现有什么东西刚好会卡住 5 秒或者 5 秒的倍数，那么检查一下 DNS 可能会有帮助，特别是在写了多个 `nameserver`，而第一个 `nameserver` 有问题的情况下。

#### musl

musl 追求简洁、可移植（一大好处是：静态链接变得极其方便），其和 glibc 在 DNS 解析方面有非常大的区别：

- musl 不使用 nscd、NSS，也不会读取 `/etc/gai.conf`。其固定使用 `/etc/hosts` 和 `/etc/resolv.conf` 作为解析的配置来源。
- 对于 `/etc/resolv.conf` 中有多个 `nameserver` 的情况，musl 会并发请求（最多 3 个 `nameserver`），并取首个返回的结果。这会导致网络压力增大，因此建议在这种情况下配置好本地的 DNS 缓存服务以缓解网络压力，减小 DNS 解析出错的可能。
- 在 musl 1.2.4（2023/5/1）之前，musl 不支持 TCP DNS 查询——这对 DNS 响应会超过 512 字节的场景是致命的。

其他技术区别的整理可参考：[Functional differences from glibc](https://wiki.musl-libc.org/functional-differences-from-glibc.html#Name_Resolver/DNS)。

### resolvconf

### DNS 缓存服务 {#dns-cache}

可以注意到，glibc 设置了非常复杂的 DNS 解析逻辑，但是问题也是很明显的：

- `nsswitch.conf` 和 `gai.conf` 配置文件对容器场景难以适用
- nscd 缓存服务不稳定且也不适合容器化
- 如果程序不使用 glibc 的 API 做 DNS 解析，那么这些配置就完全无效了（最典型的例子是使用 Go 语言在关闭了 cgo 的情况下编译的程序）

因此目前来讲，更推荐的做法是：在本地运行一个 DNS 缓存服务器，并且修改 `/etc/resolv.conf` 等配置将所有的 DNS 请求都发给这个缓存服务器，以统一整个系统的 DNS 解析行为。

#### systemd-resolved

#### dnsmasq

## 服务端 {#server}
