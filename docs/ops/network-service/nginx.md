---
icon: simple/nginx
---

# Nginx 网页服务器

!!! note "主要作者"

    [@Cherrling][Cherrling]

> WebServer 不能失去 Nginx，就如同西方不能失去耶路撒冷
>
> —— [@Cherrling][Cherrling]

Nginx 是一个高性能的 HTTP 和反向代理服务器，它可以作为一个独立的 Web 服务器，也可以作为其他 Web 服务器的反向代理服务器。

如果你只是需要简单快速的拉起一个网站，或许也可以试试 [Caddy](../../advanced/caddy.md)，它是一个更加简单的 Web 服务器。

## 安装

Nginx 可以直接从 Debian 官方源安装。如果有特殊的需求，也有其他的选择：

- [Nginx.org 官方源](https://nginx.org/en/linux_packages.html#Debian) 提供了最新主线和稳定版本的 Nginx。
- [n.wtf](https://n.wtf/) 提供了最新的 Nginx，并内置了 Brotli、QUIC（HTTP/3）等支持。
- [OpenResty](https://openresty.org/en/linux-packages.html) 提供了基于 Nginx 的高性能 Web 平台，内置了 LuaJIT 支持。用户可以编写 Lua 脚本来扩展 Nginx 的功能。

常用命令：

```bash
sudo nginx -t # 检查配置文件是否正确
sudo nginx -s reload # 不停机重新加载配置文件
sudo systemctl reload nginx # 不停机重新加载配置文件
sudo nginx -s stop # 停止 Nginx
sudo nginx -s quit # 安全停止 Nginx（完成当前请求后停止）
```

## 配置

### 配置文件结构简介

对于 Debian & Ubuntu 来说，nginx.conf 的内容一般包含：

```nginx
http {
    # ...
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

配置 Nginx 主要涉及到三个目录，分别是 `/etc/nginx/nginx.conf`、`/etc/nginx/sites-available` 和 `/etc/nginx/sites-enabled`。

- `nginx.conf` 是 Nginx 的主配置文件，它包含了 Nginx 的全局配置。
- `sites-available` 目录下存放的是所有的站点配置文件。
- `sites-enabled` 目录下存放的是启用的站点配置文件的符号链接。

一般情况下，我们不在 `nginx.conf` 文件中直接编写站点信息（`http` 块），而是在 `sites-available` 目录下创建一个新的配置文件，然后在 `sites-enabled` 目录下创建一个符号链接。如果要暂时下线某个站点，只需要删除 `sites-enabled` 目录下的符号链接即可，而不需要删除配置文件。

从 Nginx 的角度来看，唯一的区别在于来自 `conf.d` 的文件能够更早被处理，因此，如果你有相互冲突的配置，那么来自 `conf.d` 的配置会优先于 `sites-enabled` 中的配置。

!!! note "其他发行版和 Nginx 官方的配置"

    对于其他发行版和官方源来说，配置中则不包含 `sites-available` 和 `sites-enabled`，而是只会 `include` `conf.d` 目录：

    ```nginx
    http {
        # ...
        include /etc/nginx/conf.d/*.conf;
    }
    ```

    此时，你需要将你编写的配置文件放置于 `/etc/nginx/conf.d` 目录下，但当你需要禁用某些内容时，必须将其移出文件夹、删除或进行更改。当然，你也可以自己创建 `sites-available` 和 `sites-enabled` 目录，然后在 `nginx.conf` 中引入。

    关于两者的区别，你可以查看[这篇文章](https://serverfault.com/questions/527630/difference-in-sites-available-vs-sites-enabled-vs-conf-d-directories-nginx)。

### 编辑站点配置

默认的站点配置文件在 `/etc/nginx/sites-available/default`，你可以直接编辑它——以下为去除了所有注释的默认版本：

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

这个配置文件中定义了一个完整的 `server` 块。一个 `server` 块定义了一个站点（虚拟主机），Nginx 会根据请求的域名和端口号来匹配对应的 `server` 块。`server` 块中的指令如下：

- `listen`：该默认站点在所有的 IPv4 和 IPv6 上监听 80 端口。
- `root`：根目录是 `/var/www/html`。
- `index`：在处理 URL 结尾为 `/` 的请求时，使用的默认的首页文件是 `index.html`、`index.htm` 和 `index.nginx-debian.html`；Nginx 会按顺序查找这些文件，找到第一个存在的文件后返回给客户端。
- `server_name`：默认的服务器名称是 `_`，表示匹配所有未被其他 server 块匹配的请求。
- `location /`：处理所有以 `/` 开头的请求。
    - `try_files $uri $uri/ =404;`：尝试按顺序查找请求的文件 `$uri`（请求的路径），如果找不到则尝试查找目录 `$uri/`，如果仍然找不到则返回 404 错误。

这时你可以在 `/var/www/html` 目录下放置你自己的 HTML、CSS、JS 等文件，然后访问 `http://localhost` 就可以看到你的网站了。

反向代理是代表服务器接收客户端请求、转发到后端、再返回结果的一层中间代理。一种常见的需求是让 Nginx 作为其他后端服务的反向代理。可以参考下面的配置：

```nginx
server {
    listen 80 default_server; # 监听 80 端口
    listen [::]:80 default_server;

    location / {
        proxy_pass http://backend_server:port;  # 替换为后端服务器的地址和端口
        proxy_set_header Host $host;  # 设置主机头
        proxy_set_header X-Real-IP $remote_addr;  # 设置真实客户端 IP
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # 设置转发的 IP
        proxy_set_header X-Forwarded-Proto $scheme;  # 设置转发的协议
    }
}
```

!!! note "约定俗成的 HTTP 请求头"

    以上配置中除了 `Host` 是 HTTP/1.1 标准的请求头以外，其他以 `X-` 开头的请求头都是约定俗成的非标准请求头，用于让反向代理（Nginx）传递请求用户的真实 IP 地址和请求协议等信息，否则后端服务只能看到反代本身的 IP 信息。需要注意的是，如果后端服务器没有经过反向代理，或者反向代理配置不正确，那么用户可能会伪造这些请求头，如果此时后端服务错误地信任了这些请求头，就会导致安全问题。

这时访问 `http://localhost` 就会被转发到 `http://backend_server:port`。对外部网络来说，Nginx 就是一个反向代理站点。

### 重新加载配置

修改配置文件后，别忘了重新加载 Nginx 配置，否则修改不会生效。

你可以先检查配置文件是否正确：

```bash
sudo nginx -t
```

如果没有问题，就重新加载配置文件：

```bash
sudo nginx -s reload
```

或者使用：

```bash
sudo systemctl reload nginx
```

需要注意的是，如果没有检查配置，并且配置中存在错误，`nginx -s reload` 会让 nginx 停止，而 `systemctl reload nginx` 不会，并且不会采用新的配置文件。

## 进阶教程

### Nginx 名词扫盲

在向你展示如何进阶配置 Nginx 之前，有一些你必须要了解的概念。

#### server 块

Nginx 的配置文件中可以有多个 server 块，每个 server 块定义了一个站点（虚拟主机），Nginx 会根据请求的域名和端口号来匹配对应的 server 块。
Nginx 正是通过 server 块来实现多站点配置的。
一个典型的 server 块：

```nginx
server {
    listen 80;  # 监听的端口
    server_name example.com;  # 服务器名称

    location / {
        # 处理请求的指令
    }
}
```

#### location 块

location 块嵌套于 server 块中，用于定义如何处理特定 URI 的请求。一个 server 块中可以有多个 location 块。

Nginx 的 location 块用于定义如何处理特定 URI 的请求。它是 Nginx 配置中的一个重要部分，允许您根据请求的路径、参数或其他条件来执行不同的操作。

一个 location 块的基本结构如下：

```nginx
location [modifier] /path/ {
    # 处理请求的指令
}
```

#### 反向代理与负载均衡

反向代理是指代理服务器接收客户端的请求，然后将请求转发给后端服务器，最后将后端服务器的响应返回给客户端。反代有不同协议的区分，如 HTTP 反代、TCP 反代、UDP 反代等。

负载均衡是指将请求分发给多个后端服务器，以达到均衡负载的目的。Nginx 支持多种负载均衡算法，如轮询、加权轮询、IP 哈希、最少连接等。

一个十分巧妙的负载均衡算法是一致性哈希算法，它可以保证在服务器数量变化时，尽可能少地改变已有的映射关系。推荐阅读：[一致性哈希算法](https://zh.wikipedia.org/wiki/%E4%B8%80%E8%87%B4%E5%93%88%E5%B8%8C)。

#### TLS

TLS 是一种加密通信协议，用于保护客户端和服务器之间的通信安全。Nginx 支持 TLS 协议，可以用来配置 HTTPS 站点。

一般的 http 监听端口是 80，https 监听端口是 443。

#### WebSocket

WebSocket 是一种全双工通信协议，用于在客户端和服务器之间建立持久连接，实现实时通信。Nginx 支持 WebSocket 协议，可以用来配置 WebSocket 服务器。

### 示例讲解

Nginx 主要用途可以分为固定站点和反代两类，可以通过几个例子来学习一下。

#### 多站点配置

Nginx 的一个十分炫酷的功能就是可以实现一台主机上运行多个网站，对不同的域名提供不同的服务。这就是所谓的虚拟主机配置。

那么如何实现呢？答案就是 server 块中的 server_name 指令。server_name 指令用于定义服务器的名称，可以是域名、IP 地址、通配符等。我们来看一个典型的示例：

- 对于请求 `example.com` 和 `www.example.com`，Nginx 会使用第一个 server 块来处理请求，对应的网站根目录是 `/var/www/example.com`。
- 对于请求 `example.org` 和 `www.example.org`，Nginx 会使用第二个 server 块来处理请求。对应的网站根目录是 `/var/www/example.org`。
- 对于其他请求，Nginx 会返回 404 错误。

```nginx
server {
    listen 80;  # 监听的端口
    server_name example.com www.example.com;  # 指定的域名
    root /var/www/example.com;  # 网站根目录
    location / {
        try_files $uri $uri/ =404;
    }
}
server {
    listen 80;  # 监听的端口
    server_name example.org www.example.org;  # 指定的域名
    root /var/www/example.org;  # 网站根目录
    location / {
        try_files $uri $uri/ =404;
    }
server {
    listen 80 default_server;  # 默认站点
    server_name _;  # 默认域名
    root /var/www/default;  # 默认网站根目录
    location / {
        try_files $uri $uri/ =404;
    }
}
```

注意到除了指定的域名外，还有一个 `_`，它表示默认域名。如果请求的域名不在 server_name 中，Nginx 会使用 `_` 对应的 server 块来处理请求。
那 `default_server` 又是什么意思呢？它表示默认站点，当请求的域名不在 server_name 中时，Nginx 会使用 `default_server` 对应的 server 块来处理请求。
一般建议为 Nginx 配置一个默认站点，用于处理未知域名的请求。

但是要注意的是，如果你只写了 `listen 80 default_server;`，比如：

```nginx
server {
    listen 80 default_server;
    # 缺少 server_name 指令
    root /var/www/default;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

只写了 `listen 80 default_server;` 而没有 `server_name` 指令，Nginx 仍然会将该 server 块标记为默认服务器，但由于没有指定 `server_name`，它将会匹配所有请求的 Host 头。
在这种情况下，任何发送到 80 端口的请求（无论 Host 头是什么）都会被这个 server 块处理，因为它是默认服务器。

如果只写了 `server_name _;`，比如：

```nginx
server {
    # 缺少 listen 指令
    server_name _;
    root /var/www/default;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

只写了 `server_name _;` 而没有 listen 指令，Nginx 将不会知道在哪个端口上监听这个 server 块，所以 Nginx 不会启动这个 server 块，不会处理任何请求。

#### Location 块详解

一个典型的 location 块如下：

```nginx
location [modifier] /path/ {
    # 处理请求的指令
}
```

首先来看 `modifier`，它是一个可选的修饰符，用于修改 location 块的匹配规则。常用的修饰符有：

- 前缀匹配

前缀匹配是 location 块的默认匹配规则，只要请求的路径以 location 块的路径开头，就会匹配成功。例如：

```nginx
location /example {
    # 处理请求 /example 和 /example/xxx
    return 200 "This is a prefix match.";
}
```

- `=`

精确匹配，只有请求的路径与 location 块的路径完全相同时才匹配。

```nginx
location = /example {
    # 处理请求 /example
    # 不处理 /example/xxx
    return 200 "This is an exact match.";
}
```

- `~`

区分大小写的正则匹配。

- `~*`

不区分大小写的正则匹配。

正则匹配的例子是：

```nginx
location ~ /example[0-9] {
    # 处理请求 /example1, /example2, ...
    return 200 "This is a case-sensitive regex match.";
}
location ~ \.php$ {
    # 处理以 .php 结尾的请求
    include fastcgi_params;
    fastcgi_pass 127.0.0.1:9000;
}

location ~* \.(jpg|jpeg|png)$ {
    # 处理 jpg、jpeg 和 png 文件，不区分大小写
    root /var/www/html/images;
}
```

- `^~`

通配符匹配，如果请求的 URI 以指定的路径开头，且该路径是最长的前缀匹配，则使用该 location 块。它优先于正则匹配。

```nginx
location ^~ /static/ {
    # 处理以 /static/ 开头的请求
    root /var/www/html/static;
}

location ~ \.css$ {
    # 处理以 .css 结尾的请求
    root /var/www/html/styles;
}
```

在这个例子中，如果请求的 URI 是 `/static/style.css`，则会匹配到第一个 location 块，因为它是以 `/static/` 开头的前缀匹配。即使 `/static/style.css` 也符合第二个正则匹配的条件，但由于第一个 location 块使用了 `^~`，Nginx 不会继续检查正则匹配。

Nginx 在处理请求时会按照以下顺序匹配 location 块：

1. 精确匹配 (=)。
2. 前缀匹配（最长匹配）。
3. 通配符匹配 (^~)。
4. 正则匹配（~ 和 ~\*，按出现顺序匹配）。

而在 Location 块中，我们可以使用一些指令来处理请求，如：

- `proxy_pass http://backend_server;`：反向代理。
- `root /var/www/html;`：指定网站根目录。
- `try_files $uri $uri/ =404;`：尝试查找文件，如果找不到返回 404 错误。
- `return 200 "Hello, World!";`：返回指定的状态码和内容。
- `include fastcgi_params;`：引入 FastCGI 参数。

#### SSL/TLS 配置

作为 WebServer，必不可少的功能就是支持 HTTPS。你可以在 [https://cherr.cc/ssl.html](https://cherr.cc/ssl.html) 找到 SSL/TLS 的原理解释。

首先，你需要为你的域名申请一个 SSL 证书。你可以使用免费的 Let's Encrypt 证书，也可以购买商业证书。
假设你的证书保存在 `/etc/ssl/certs/example.com.pem` 和 `/etc/ssl/private/example.com.pem`。

然后，你需要在 Nginx 配置文件中添加 SSL 配置：

```nginx
server {
    listen 443 ssl;  # 监听的端口
    server_name example.com;  # 指定的域名
    root /var/www/example.com;  # 网站根目录

    ssl_certificate /etc/ssl/certs/example.com.pem;  # SSL 证书路径
    ssl_certificate_key /etc/ssl/private/example.com.pem;  # SSL 证书密钥路径

    # （可选）中间证书
    ssl_trusted_certificate /etc/ssl/certs/ca_bundle.crt;  # 中间证书文件

    # （可选）SSL 设置
    ssl_protocols TLSv1.2 TLSv1.3;  # 启用的 SSL/TLS 协议
    ssl_ciphers 'HIGH:!aNULL:!MD5';  # 使用的加密套件
    ssl_prefer_server_ciphers on;  # 优先使用服务器的加密套件
    ssl_session_cache shared:SSL:10m;  # SSL 会话缓存大小
    ssl_session_timeout 10m;  # SSL 会话超时时间

    # （可选）HSTS（HTTP Strict Transport Security）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

注意到和前文的配置不同，这里的监听端口是 443，而且增加了 ssl 选项。
`ssl_certificate` 和 `ssl_certificate_key` 分别指定了 SSL 证书和密钥的路径。

在配置文件中，我们还提到了一些可选的配置，如中间证书、SSL 设置、HSTS 等。一般建议设置 `ssl_protocols TLSv1.2 TLSv1.3;` ，因为 TLSv1.0 和 TLSv1.1 已经不安全且被弃用。

HSTS 是一种安全机制，用于强制客户端（浏览器）使用 HTTPS 访问网站。
当用户首次访问支持 HSTS 的网站时，浏览器会通过 HTTP 或 HTTPS 发送请求。
如果网站支持 HSTS，服务器会在响应中包含 Strict-Transport-Security 头部，指示浏览器该网站应仅通过 HTTPS 访问。
`add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;` 表示启用 HSTS，浏览器会在 1 年内强制使用 HTTPS 访问网站，并且包括子域名。

#### 反向代理配置

反向代理是 Nginx 的一个重要功能，可以用于隐藏后端服务器的真实 IP 地址，提高安全性。也可以将开在不同端口的服务统一到一个端口上。

假如你开设了一个多媒体服务器，在运行的服务器软件中，alist 默认端口是 5244，komga 默认端口是 25600，jellyfin 默认端口是 8096，grafana 的默认端口是 3000，你可以通过反向代理将它们统一到 80 或 443 端口上。使用如下的域名区分不同的服务：

- alist.cherr.cc -> 5244
- komga.cherr.cc -> 25600
- jellyfin.cherr.cc -> 8096
- grafana.cherr.cc -> 3000

比如上面的例子，就可以通过下面的配置实现反向代理：

```nginx
server {
    listen 80;  # 监听的端口
    server_name alist.cherr.cc;  # 指定的域名

    location / {
        proxy_pass http://localhost:5244;  # 反向代理的地址
        proxy_set_header Host $host;  # 设置主机头
        proxy_set_header X-Real-IP $remote_addr;  # 设置真实客户端 IP
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # 设置转发的 IP
        proxy_set_header X-Forwarded-Proto $scheme;  # 设置转发的协议
    }
}

server {
    listen 80;  # 监听的端口
    server_name komga.cherr.cc;  # 指定的域名

    location / {
        proxy_pass http://localhost:25600;  # 反向代理的地址
        proxy_set_header Host $host;  # 设置主机头
        proxy_set_header X-Real-IP $remote_addr;  # 设置真实客户端 IP
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # 设置转发的 IP
        proxy_set_header X-Forwarded-Proto $scheme;  # 设置转发的协议
    }
}

...
...
```

但是这只是最简单的反向代理配置，实际情况下往往还需要根据不同的服务做一些特殊的配置，可以通过两个狠狠坑过我的例子来学习。

- alist 反向代理非标准端口或启用 https 后丢失 https 或端口号/无法播放视频

    参考：<https://alist.nn.ci/zh/guide/install/reverse-proxy.html>

    问题就在于反代时需要正确的 Host 头，添加设置 `proxy_set_header Host $host;`，否则会导致反代失败。

    这里要说明一下 `$host` 和 `$http_host` 的区别：

    `$host` 是 Nginx 的一个内置变量，用于获取请求的主机名（Host）。它的值是根据以下优先级确定的：

    1. 请求行中的主机名（HTTP/1.0）
    2. Host 请求头字段
    3. 与请求匹配的 `server_name`

    `$host` 变量的可靠性高。如果 Host 头缺失，会使用 `server_name` 作为后备值，保证有值。同时即使请求中有端口号，`$host` 也只会返回主机名部分，不包含端口号。

    `$http_` 是 Nginx 的一个变量前缀，用于获取任意 HTTP 请求头的值。`$http_host` 就是专门用于获取 Host 请求头的变量。它纯粹是客户端发送过来的 Host 头的副本。

    如果客户端请求是 GET / HTTP/1.1，并且带了 `Host: www.example.com:8080`，那么 `$http_host` 的值就是 "www.example.com:8080"。

    如果客户端请求是 GET / HTTP/1.0（HTTP/1.0 没有 Host 头），那么 `$http_host` 的值就是 空。

    因为它可能为空，如果你在配置中直接使用它（例如 `proxy_set_header Host $http_host;`），当其为空时，转发给后端的请求的 Host 头也会是空的，这可能导致后端服务器无法正确处理请求（无法识别要访问哪个虚拟主机）。

    ```nginx
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Range $http_range;
        proxy_set_header If-Range $http_if_range;
        proxy_redirect off;
        proxy_pass http://127.0.0.1:5244;
        # the max size of file to upload
        client_max_body_size 20000m;
    }
    ```

- Grafana 需要 websocket 反代支持

    参考：<https://grafana.com/tutorials/run-grafana-behind-a-proxy/>

    关键在于 Grafana 加载数据时使用了 websocket，需要指示 Nginx 支持 websocket 反代。

    ```nginx
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
    # Proxy Grafana Live WebSocket connections.
    location /api/live/ {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_pass http://grafana;
    }
    ```

#### 负载均衡配置

负载均衡是 Nginx 的另一个重要功能，可以用于分发请求到多个后端服务器，提高性能和可靠性。

一个典型的负载均衡配置如下：

```nginx
http {
    upstream backend {
        server backend1.example.com;
        server backend2.example.com;
        server backend3.example.com;
    }

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://backend;  # 将请求转发到 upstream 定义的后端服务器
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

    server {
        listen 80;
        server_name another-example.com;

        location / {
            proxy_pass http://backend;  # 也可以使用相同的 upstream
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

- 负载均衡算法

Nginx 支持多种负载均衡算法，默认是轮询（round-robin）。你可以通过在 upstream 块中指定不同的算法来更改负载均衡策略，例如：

最少连接：

```nginx
upstream backend {
    least_conn;  # 使用最少连接算法
    server backend1.example.com;
    server backend2.example.com;
}
```

IP 哈希：

```nginx
upstream backend {
    ip_hash;  # 使用 IP 哈希算法
    server backend1.example.com;
    server backend2.example.com;
}
```
