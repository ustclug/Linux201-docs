# SSH 登录

尽管 SSH 是一种开放协议，它的主流实现 OpenSSH 具有最丰富的功能，因此本教程只介绍 OpenSSH 的使用。

## 配置文件 {#config}

SSH 客户端会按顺序处理以下配置，先出现的配置优先级更高：

- 命令行参数
- `~/.ssh/config`
- `/etc/ssh/ssh_config`

OpenSSH 的所有配置项都可以在 `man ssh_config` 中找到，这里介绍一些常用的配置。

对于经常登录的主机，可以在 `~/.ssh/config` 中配置主机别名、用户名、端口等信息，以简化登录命令。

```shell
Host example
  Hostname example.com
  User sshuser
  Port 22
```

注意 SSH config 没有提供密码配置，因为这是不安全的，请使用密钥登录。

默认情况下，SSH 会寻找 `~/.ssh/id_*` 作为私钥，其中 `*` 部分可以是 `rsa`、`dsa`、`ecdsa`、`ed25519` 等，也可以通过 `-i` 参数指定私钥文件。私钥的文件名加上 `.pub` 后缀就是公钥文件，暂时没有方法指定公钥文件的路径。如果要在配置文件中指定一个或多个私钥，可以使用 `IdentityFile` 选项，例如：

```shell
Host example
  IdentityFile ~/.ssh/id_rsa
```

### 端口转发 {#port-forwarding}

SSH 支持三种端口转发：

- 本地端口转发（**L**ocal port forwarding）：在本地上监听一个端口，将收到的数据转发到远程主机的指定端口。

    ```shell
    ssh -L 8080:localhost:80 example
    ```
    
    上面命令表示监听本地的 8080 端口，将收到的数据转发到远程主机 example 的 80 端口。

    本地端口转发默认监听在 localhost。如果要监听其他地址，可以指定需要监听的地址，例如：

    ```shell
    ssh -L 0.0.0.0:8080:localhost:80 example
    ```

    此时，本地主机监听的 8080 端口可以接受来自其他主机的连接。

    虽然 SSH 客户端也有一个 `GatewayPorts` 选项，但它只影响没有指定监听地址的语法模式（即三段式 `localport:remotehost:remoteport`）。指定四段式语法后，`GatewayPorts` 选项不再起作用。

- 远程端口转发（**R**emote port forwarding）：在远程主机上监听一个端口，将收到的数据转发到本地的指定端口。

    ```shell
    ssh -R 8080:localhost:80 example
    ```
    
    上面命令表示在远程主机 example 上监听 8080 端口，将收到的数据转发到本地的 80 端口。

    注意远程端口转发默认只能监听 localhost。如果要监听其他地址，需要在远程主机的 `sshd_config` 中设置 `GatewayPorts yes`。与另外两种端口转发不同，客户端无法覆盖服务端的 `GatewayPorts` 设定。

- 动态端口转发（**D**ynamic port forwarding）：在本地监听一个端口用作 SOCKS5 代理，将收到的数据转发到远程主机。
  
    ```shell
    ssh -D 1080 example
    ```
    
    上面命令表示在本地 8080 端口开启 SOCKS5 代理服务器，将收到的数据通过远程主机 example 转发。

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
  RemoteForward 8080 localhost:80
  DynamicForward 1080
```