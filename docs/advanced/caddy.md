---
icon: simple/caddy
---

# Caddy

!!! note "主要作者"

    [@tiankaima][tiankaima]

!!! success "本文已完成"

Caddy 是一个用 Go 编写的现代的 HTTP Web 服务器，具有自动 HTTPS 功能。它的设计目标是简单、易于使用。

与 Nginx 相比，Caddy 确实更像是个玩具，但是更像是那种自带电池的玩具，更利于人类使用，可以快速搭建 Prototype 而不用花费太多时间在配置上。

## 安装 {#installation}

以 Debian 为例：

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

通过以上方法安装的 Caddy 会默认配置 systemd 服务，可以通过 `systemctl` 来管理：

```bash
sudo systemctl start caddy
sudo systemctl stop caddy
sudo systemctl restart caddy
```

默认的 `Caddyfile` 的目录在 `/etc/caddy/Caddyfile`，可以通过修改 `Caddyfile` 来配置 Caddy 的行为。修改 Caddyfile 之后，可以使用 `sudo systemctl reload caddy` 让 Caddy 重新加载配置，而无须重启服务。

!!! note "Caddyfile 验证与格式化"

    在修改配置文件后，可以通过如下命令检查 Caddyfile 格式（类似 `nginx -t`）：

    ```bash
    caddy validate --config /etc/caddy/Caddyfile
    ```

    同时 Caddy 也支持格式化 Caddyfile：

    ```bash
    caddy fmt --overwrite --config /etc/caddy/Caddyfile
    ```

!!! note "Caddyfile 与 Caddy 配置"

    在 Caddy v1 时，Caddyfile 是唯一配置 Caddy 的方法。但是目前的 Caddy v2 相比于 v1 发生了非常大的变化，其中尽管 Caddyfile 仍然是标准的配置方式（一部分语法有变化，参考[升级指南](https://caddyserver.com/docs/v2-upgrade)），但是 Caddy 实际识别的是 [JSON 格式](https://caddyserver.com/docs/json)的配置，对 Caddyfile（以及其他类型的配置）的支持则由 [config adapter](https://caddyserver.com/docs/config-adapters) 实现。

    考虑目前的使用情况，以下配置均只考虑 Caddy v2。

    同时，Caddy v2 默认还会在本地监听 2019 端口用来实时接收管理配置修改，详情可参考 [API](https://caddyserver.com/docs/api)。

## 常用配置 {#common-configuration}

以下是一些常用的 Caddyfile 配置示例：

### 静态文件服务器 {#static-file-server}

```caddy
example.com {
    root /var/www
    file_server
    encode zstd gzip
    log {
		output file /var/log/access.log
	}
}
```

### 反向代理 {#reverse-proxy}

```caddy
example.com {
    reverse_proxy localhost:8080
}
```

!!! note "Simple LB"

    使用如下配置可做简单的 Load Balance：

    ```caddy
    example.com {
        reverse_proxy localhost:8080 localhost:8081 {
            lb_policy round_robin
        }
    }
    ```

### 阻止 Caddy 对未配置的域名进行 HTTPS 跳转 {#abort-unconfigured-domains}

Caddy 默认情况下会对所有的域名进行 HTTPS 跳转（HTTP 308），即使对应的域名在 Caddyfile 中不存在。一些特定地区或环境的监管要求 HTTP 服务器对未备案登记的域名的请求拒绝响应，这时可以使用这种配置。

可以在配置中添加以下内容：

```caddy
http:// {
    abort
}
```

使得 Caddy 拒绝在 80 端口对所有未配置的域名提供服务。
