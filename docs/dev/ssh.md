# SSH 使用技巧

!!! warning "本文仍在编辑中"

尽管 SSH 是一种开放协议，它的主流实现 OpenSSH 具有最丰富的功能，因此本教程只介绍 OpenSSH 的使用。

## 客户端配置 {#ssh-config}

SSH 客户端会按顺序处理以下配置，先出现的配置优先级更高：

- 命令行参数
- `~/.ssh/config`
- `/etc/ssh/ssh_config`

OpenSSH 的所有配置项都可以在 [ssh_config(5)][ssh_config.5] 中找到，这里介绍一些常用的配置。

对于经常登录的主机，可以在 `~/.ssh/config` 中配置主机别名、用户名、端口等信息，以简化登录命令。

```shell
Host example
  Hostname example.com
  User sshuser
  Port 22
```

注意 SSH config 没有提供密码配置，因为这是不安全的，请使用密钥登录。

### 公钥认证 {#public-key-authentication}

默认情况下，SSH 会寻找 `~/.ssh/id_*` 作为私钥，其中 `*` 部分可以是 `rsa`、`dsa`、`ecdsa`、`ed25519` 等，也可以通过 `-i` 参数指定私钥文件。私钥的文件名加上 `.pub` 后缀就是公钥文件，暂时没有方法指定公钥文件的路径。如果要在配置文件中指定一个或多个私钥，可以使用 `IdentityFile` 选项，例如：

```shell
Host example
  IdentityFile ~/.ssh/id_rsa
  #CertificateFile ~/.ssh/id_rsa-cert.pub
```

一般来说，除非为了兼容一些非常古老（如 10 年前的）或非常简单的（如嵌入式）系统而不得不使用较短的 RSA 密钥对的时候，我们推荐使用 Ed25519 密钥对，或者 ECDSA 密钥对。这两种基于椭圆曲线的密码学算法比 RSA 更安全，而且性能也更好。如果不得不使用 RSA 的话，请尽可能使用 3072 位或更长的密钥长度。密钥长度可以在使用 `ssh-keygen` 生成密钥对时指定（`-b`），其中不同算法支持与推荐的长度也是不同的：

|       算法        |    支持长度     |    推荐长度     | 说明                                                                               |
| :---------------: | :-------------: | :-------------: | ---------------------------------------------------------------------------------- |
|        RSA        |    1024-4096    |   3072 或以上   | 曾经的推荐长度是 2048 位，但 2020 年以后认为这个长度已不够安全                     |
| DSA<br>（不推荐） |      1024       |      1024       | 由于安全性问题，OpenSSH 7.0 以后不再默认支持 DSA 密钥                              |
|       ECDSA       | 256 / 384 / 521 | 256 / 384 / 521 | 由于椭圆曲线参数选择的特殊性，只有这三种长度可选。注意最后一个选项是 521，不是 512 |
|      Ed25519      |        -        |        -        | Ed25519 是基于 Edwards 曲线的算法，没有“长度”这种参数                              |

### 端口转发 {#port-forwarding}

SSH 支持三种端口转发：

- 本地端口转发（**L**ocal port forwarding）：在本地上监听一个端口，将收到的数据转发到远程主机的指定端口。例如：

    ```shell
    ssh -L 8080:localhost:80 example
    ```

    本地端口转发默认监听在 localhost。如果要监听其他地址，可以指定需要监听的地址，例如：

    ```shell
    ssh -L 0.0.0.0:8080:localhost:80 example
    ```

    虽然 SSH 客户端也有一个 `GatewayPorts` 选项，但它只影响没有指定监听地址的语法模式（即三段式 `localport:remotehost:remoteport`）。指定四段式语法后，`GatewayPorts` 选项不再起作用。

- 远程端口转发（**R**emote port forwarding）：在远程主机上监听一个端口，将收到的数据转发到本地的指定端口。例如：

    ```shell
    ssh -R 8080:localhost:80 example
    ```

    上面命令表示在远程主机 example 上监听 8080 端口，将收到的数据转发到本地的 80 端口。

    注意远程端口转发默认只能监听 localhost。如果要监听其他地址，需要在远程主机的 `sshd_config` 中设置 `GatewayPorts yes`。与另外两种端口转发不同，客户端无法覆盖服务端的 `GatewayPorts` 设定。

- 动态端口转发（**D**ynamic port forwarding）：在本地监听一个端口用作 SOCKS5 代理，将收到的数据转发到远程主机。例如：

    ```shell
    ssh -D 1080 example
    ```

    由于 SOCKS 代理是一个通用的代理协议，因此可以用于任何 TCP 连接，不仅仅是 HTTP。

    与 LocalForward 类似，DynamicForward 也可以指定监听地址：

    ```shell
    ssh -D 0.0.0.0:1080 example
    ```

    同样地，`GatewayPorts` 只影响没有指定监听地址的语法模式（即只给出了一个端口）。指定监听地址后，`GatewayPorts` 选项不再起作用。

以上三种端口转发都可以在配置文件中指定，例如：

```shell
Host example
  LocalForward 8080 localhost:80
  LocalForward 8081 localhost:8081
  RemoteForward 8080 localhost:80
  RemoteForward 8081 localhost:8081
  DynamicForward 1080
  DynamicForward 1081
```

`-L`、`-R`、`-D` 和配置文件中对应的选项都可以多次出现，指定多条转发规则，它们互相独立、不会覆盖，因此如果重复指定了同一个端口，就会出现冲突。

### 跳板 {#jump-host}

SSH 支持通过跳板机连接目标主机，即先 SSH 登录 jump-host，再从 jump-host 登录目标主机。一些受限的网络环境常常采用这种方案，例如一个集群内只有跳板机暴露在公网上，而其他主机都在被隔离的内网中，只能通过跳板机访问。

`ssh` 命令的 `-J` 选项可以指定跳板机，例如：

```shell
ssh -J user@jumphost.example.com user@realhost.example.com
```

对应的配置文件语句是 `ProxyJump user@jumphost.example.com`。

如果要给跳板机设置更多参数，如端口等，则必须使用配置文件：

```shell
Host jumphost
  HostName jumphost.example.com
  User jumphostuser
  Port 2333

Host realhost
  HostName realhost.example.com
  User realhostuser
  ProxyJump jumphost
```

### 高级功能：连接复用 {#connection-reuse}

SSH 协议允许在一条连接内运行多个 channel，其中每个 channel 可以是一个 shell session、端口转发、scp 命令等。OpenSSH 支持连接复用，即一个 SSH 进程在后台保持连接，其他客户端在连接同一个主机时可以复用这个连接，而不需要重新握手认证等，可以显著减少连接时间。这在频繁连接同一个主机时非常有用，尤其是当主机的延迟较大、常用操作所需的 RTT 较多时（例如从 GitHub 拉取仓库，或者前文所述的跳板机使用方式）。

启用连接复用需要在配置文件中同时指定 `ControlMaster`、`ControlPath` 和 `ControlPersist` 三个选项（它们的默认值都是禁用或者很不友好的值）：

```shell
Host *
  ControlMaster auto
  ControlPath /tmp/sshcontrol-%C
  ControlPersist yes
```

其中 `%C` 是 `%l%h%p%r` 的 hash，因此连接不同主机的 control socket 不会冲突。**但是**，如果你尝试用相同的用户名和不同的公钥连接同一个目标（例如 `git@github.com`），由于没有新建连接的过程，你指定的公钥并不会生效，解决方法是再单独指定另一个 `ControlPath`。

## 服务端配置 {#sshd-config}

服务端的配置与客户端有一些不同点：

- sshd 服务端程序只有很少量的命令行参数，各种配置都在配置文件中完成。特别注意，如果配置文件不存在，sshd 会拒绝启动。
- sshd 仅有一个配置文件 `/etc/ssh/sshd_config`，它的配置项可以在 [sshd_config(5)][sshd_config.5] 中找到。

sshd 接受 SIGHUP 信号作为重新载入配置文件的方式。`sshd -t` 命令可以检查配置文件的语法是否正确，这也是大多数发行版提供的 `ssh.service` 中指定的 `ExecStartPre=` 命令和第一条 `ExecReload=` 命令，即在尝试启动和重新加载服务前先检查配置文件的语法。

## 拆分配置文件 {#include}

从 OpenSSH 7.3p1 开始，ssh_config 和 sshd_config 都支持 `Include` 选项，可以在主配置文件中 include 其他文件。与 C 的 `#include` 或 Nginx 的 `include` 不同，SSH config 里的 `Include` **不**等价于文本插入替换，并且 `Include` 可以出现在 `Host` 和 `Match` 块中。因此一个（不太常见的）坑是：

??? failure "错误写法"

    ```shell
    Host example
      HostName example.com
      User user

    Include ~/.ssh/global.conf
    ```

因为 SSH 读取配置文件时是不会看缩进的，因此上面示例中的 Include 仅对 `Host example` 生效。正确的写法是将其放在一个 `Match all` 块（或者 `Host *`）中：

??? success "正确写法"

    ```shell
    Host example
      HostName example.com
      User user

    Match all
      Include ~/.ssh/global.conf
    ```

更加推荐的写法是将 `Include` 放在配置文件开头：

!!! success "推荐写法"

    ```shell
    Include ~/.ssh/global.conf

    Host example
      HostName example.com
      User user
    ```

## 一些坑点 {#traps}

在 OpenSSH 内部，同一个“代号”可能指代多种（有关联但）不同的细节。例如 `ssh-rsa` 至少有以下三种不同的含义：

- RSA 密钥对或 RSA 公钥算法（`id_rsa` 和 `id_rsa.pub` 文件）
- 基于 RSA / SHA-1 的 SSH 证书的签名算法（`CASignatureAlgorithms`）

    这种算法已经在 OpenSSH 8.2 中被淘汰，而 OpenSSH 7.2 起就已经支持替代算法 `rsa-sha2-256` 和 `rsa-sha2-512`（采用 SHA-256 和 SHA-512 哈希算法），虽然直到 OpenSSH 8.2，使用 RSA CA 私钥签出来的证书才**默认**采用 `rsa-sha2-512` 算法。

    如果你正在使用一个 RSA CA，那么你需要将已有的证书使用 OpenSSH 8.2 以上的版本重新签名。

    如果需要临时兼容 &le; 7.1 版本的 OpenSSH，可以在 `~/.ssh/config` 或 `sshd_config` 中指定 `CASignatureAlgorithms +ssh-rsa`，这样就可以使用旧版本的证书签名算法了。

- 基于 RSA / SHA-1 的公钥签名算法套件（`ssh-rsa`）。与前面的证书不同，这种签名算法是用于用户登录时的公钥验证，不会保存在文件里，而是在 SSH 协议内部使用。

    与前一个采用 SHA-1 作为哈希算法的算法套件类似，OpenSSH 8.8 起也不再默认启用，且替代算法也分别叫做 `rsa-sha2-256` 和 `rsa-sha2-512`。好消息是，你不需要重新签发任何证书，只要确保客户端和服务端的 OpenSSH 版本都不低于 7.2 就可以了。

    如果需要临时兼容 &le; 7.1 版本的 OpenSSH，可以通过配置选项 `HostkeyAlgorithms` 和 `PubkeyAcceptedAlgorithms` 启用。这两个选项分别控制服务端和客户端的公钥签名算法套件，并且在两端都可以指定。
