---
icon: simple/caddy
---

# Caddy

!!! note "主要作者"

    [@tiankaima][tiankaima]

!!! warning "本文已完成，等待校对"

Caddy 是一个用 Go 编写的 HTTP/2 web 服务器，具有自动 HTTPS 功能。它的设计目标是简单、易于使用。

与 Nginx 相比，Caddy 确实更像是个玩具，但是更像是那种自带电池的玩具，更利于人类使用，可以快速搭建 Prototype 而不用花费太多时间在配置上。

## 安装

以 Debian 为例：

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
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

!!! note "Validate"

    在修改配置文件后，可以通过如下命令检查 Caddyfile 格式（类似 `nginx -t`）：

    ```bash
    caddy validate --config /etc/caddy/Caddyfile
    ```

## 常用配置

以下是一些常用的 Caddyfile 配置示例：

### 静态文件服务器

```caddy
example.com {
    root /var/www
    gzip
    log /var/log/access.log
    errors /var/log/error.log
}
```

### 反向代理

```caddy
example.com {
    proxy / localhost:8080
}
```

!!! note "Simple LB"

    使用如下配置可做简单的 Load Balance：

    ```caddy
    example.com {
        proxy / localhost:8080 localhost:8081 {
            policy round_robin
        }
    }
    ```
