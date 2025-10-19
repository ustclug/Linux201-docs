---
icon: simple/nginx
---

# Nginx 服务器

!!! note "主要作者"

    [@Cherrling][Cherrling]、[@iBug][iBug]、[@taoky][taoky]

> Web server 不能失去 Nginx，就如同西方不能失去耶路撒冷
>
> —— [@Cherrling][Cherrling]

Nginx 是一个高性能的开源 Web 服务器和反向代理服务器，以稳定性高、性能优异、并发能力强等优势被广泛使用。

如果你只是需要简单快速的拉起一个网站，或许也可以试试 [Caddy](../../advanced/caddy.md)，它是一个更加简单的 Web 服务器。

## 安装 {#install}

Nginx 可以直接从 Debian APT 源安装。

```bash
sudo apt update
sudo apt install nginx
# 如果需要更多模块，可以安装 nginx-full 与 nginx-extras 包
sudo apt install nginx-full nginx-extras
```

如果有特殊的需求，也有其他的选择：

- [Nginx.org 源](https://nginx.org/en/linux_packages.html#Debian) 提供了最新主线和稳定版本的 Nginx。
- [n.wtf](https://n.wtf/) 提供了最新的 Nginx，并内置了 Brotli、QUIC（HTTP/3）等支持。
- [OpenResty](https://openresty.org/en/linux-packages.html) 提供了基于 Nginx 的高性能 Web 平台，内置了 LuaJIT 支持。用户可以编写 Lua 脚本来扩展 Nginx 的功能。

管理 Nginx 的常用命令：

```bash
sudo nginx -t # 检查配置文件是否正确
sudo nginx -s reload # 不停机重新加载配置文件
sudo nginx -s stop # 停止 Nginx
sudo nginx -s quit # 安全停止 Nginx（完成当前请求后停止）
```

对于使用 systemd 管理 Nginx 服务的系统，可以使用：

```bash
sudo systemctl reload nginx # 重新加载配置文件
sudo systemctl stop nginx # 安全停止 Nginx
```

## 配置 {#configuration}

### 配置文件结构简介 {#config-file-structure}

对于 Debian & Ubuntu 来说，`nginx.conf` 的内容一般包含：

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

一般情况下，我们不在 `nginx.conf` 文件的 `http` 块中直接编写站点信息，而是在 `sites-available` 目录下创建一个新的配置文件，然后在 `sites-enabled` 目录下创建一个符号链接。如果要暂时下线某个站点，只需要删除 `sites-enabled` 目录下的符号链接即可，而不需要删除配置文件。

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

### 指令、变量与模块 {#directives-variables-modules}

Nginx 的配置由一系列的指令（directive）组成。directive 有两种：简单 directive 和块 directive。在上面的例子中，`http` 块就是一个块 directive，而 `include` 则是简单 directive。

Nginx 的配置还支持变量。在之后的例子中，`$host`、`$remote_addr`、`$uri` 等都是变量，Nginx 会在处理请求的时候将它们替换为实际的值。用户也可以用 `set` 指令来定义自己的变量：

```nginx
set $my_variable "Hello, World!";
```

Nginx 是模块化的服务器，其中 [`ngx_http_core_module`](https://nginx.org/en/docs/http/ngx_http_core_module.html) 提供了基础的让 Nginx 提供 HTTP 服务的功能（包括 `http` 块）。Nginx 也不仅限于 HTTP 服务——可以转发 TCP 和 UDP 流量，甚至是当邮件服务器，或者 RTMP 直播服务器等。这些功能都是通过不同的模块来实现的。用户也可以自己编译安装第三方模块来扩展 Nginx 的功能。如果使用了 Debian 提供的 Nginx 包，那么可以使用 Debian 编写的一些第三方模块，这些模块以 `libnginx-mod-` 前缀开头；如果要自行编译模块，需要安装 `nginx-dev` 包。

[Nginx 文档](https://nginx.org/en/docs/) 是非常重要的参考资料，其包含了：

- [按字母序排序的 directive 列表文档](https://nginx.org/en/docs/dirindex.html)
- [按字母序排序的变量列表文档](https://nginx.org/en/docs/varindex.html)
- 官方模块的列表文档

其中每个 directive 和变量都包含了详细的说明。

### `server` 块与 `location` 块 {#server-location-blocks}

Nginx 配置的 [`http` 块](https://nginx.org/en/docs/http/ngx_http_core_module.html#http)中可以有多个 [`server` 块](https://nginx.org/en/docs/http/ngx_http_core_module.html#server)，每个 `server` 块定义了一个站点（虚拟主机），Nginx 会根据请求的域名和端口号来匹配对应的 `server` 块。Nginx 正是通过 `server` 块来实现多站点配置的。

一个典型的 `server` 块如下：

```nginx
server {
    listen 80;  # 监听的端口
    server_name example.com;  # 服务器名称

    location / {
        # 处理请求的指令
    }
}
```

[`location` 块](https://nginx.org/en/docs/http/ngx_http_core_module.html#location)嵌套于 `server` 块中，用于定义如何处理特定 URI 的请求。一个 `server` 块中可以有多个 `location` 块。

??? tip "URI? URL?"

    URI（Uniform Resource Identifier，统一资源标识符）包含 URL（Uniform Resource Locator，统一资源定位符）和 URN（Uniform Resource Name，统一资源名称）。其中 URL 大家都非常熟悉，而 URN 则比较少见。URN 的格式类似于 [`urn:isbn:0262510871`](https://web.mit.edu/6.001/6.037/sicp.pdf)，用于标识资源（这里是一本书）的名称。因为 URN 很少见，在绝大部分场景下，URI 和 URL 可以视为同义词。

Nginx 的 `location` 块用于定义如何处理特定 URI 的请求。它是 Nginx 配置中的一个重要部分，允许让 Nginx 根据请求的路径、参数或其他条件来执行不同的操作。

一个 `location` 块的基本结构如下：

```nginx
location [modifier] /path/ {
    # 处理请求的指令
}
```

其中可选的 `modifier` 用于指定匹配方式（例如精确匹配、正则匹配等），默认不填写的话则为前缀匹配，详细介绍见下面的 [Location 匹配](#location-matching)部分。

### 站点配置简介 {#site-config-intro}

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

这个配置文件中定义了一个完整的 `server` 块。`server` 块中的指令如下：

- [`listen`](https://nginx.org/en/docs/http/ngx_http_core_module.html#listen)：该默认站点在所有的 IPv4 和 IPv6 上监听 80 端口。
- [`root`](https://nginx.org/en/docs/http/ngx_http_core_module.html#root)：根目录是 `/var/www/html`。
- [`index`](https://nginx.org/en/docs/http/ngx_http_index_module.html#index)：在处理 URL 结尾为 `/` 的请求时，使用的默认的首页文件是 `index.html`、`index.htm` 和 `index.nginx-debian.html`；Nginx 会按顺序查找这些文件，找到第一个存在的文件后返回给客户端。
- [`server_name`](https://nginx.org/en/docs/http/ngx_http_core_module.html#server_name)：一个约定俗成的“默认服务器”名称 `_`。
- `location /`：处理所有以 `/` 开头的请求。
    - [`try_files $uri $uri/ =404;`](https://nginx.org/en/docs/http/ngx_http_core_module.html#try_files)：尝试按顺序查找请求的文件 `$uri`（请求的路径），如果找不到则尝试查找目录 `$uri/`，如果仍然找不到则返回 404 错误。

这时你可以在 `/var/www/html` 目录下放置你自己的 HTML、CSS、JS 等文件，然后访问 `http://localhost` 就可以看到你的网站了。

反向代理是代表服务器接收客户端请求、转发到后端、再返回结果的一层中间代理。也可以认为这里的「后端」是反向代理的「上游」。一种常见的需求是让 Nginx 作为其他后端服务的反向代理。可以参考下面的配置：

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

其中对绝大部分后端服务来说，`Host` 头是必须设置的。

!!! note "约定俗成的 HTTP 请求头"

    以上配置中除了 `Host` 是 HTTP/1.1 标准的请求头以外，其他以 `X-` 开头的请求头都是约定俗成的非标准请求头，用于让反向代理（Nginx）传递请求用户的真实 IP 地址和请求协议等信息，否则后端服务只能看到反代本身的 IP 信息。需要注意的是，如果后端服务器没有经过反向代理，或者反向代理配置不正确，那么用户可能会伪造这些请求头，如果此时后端服务错误地信任了这些请求头，就会导致安全问题。

这时访问 `http://localhost` 就会被转发到 `http://backend_server:port`。对外部网络来说，Nginx 就是一个反向代理站点。

### 重新加载配置 {#reload}

修改配置文件后，别忘了重新加载 Nginx 配置，否则修改不会生效。

你可以先检查配置文件是否正确：

```bash
sudo nginx -t
```

如果没有问题，就重新加载配置文件：

```bash
sudo systemctl reload nginx  # 推荐使用
# 或者
sudo nginx -s reload
```

需要注意的是，如果配置文件中存在错误，重新加载的时候会报出这些错误，然后 Nginx 会以旧的配置文件继续运行。

??? note "Nginx 的主进程与工作进程的设计"

    Nginx 采用了主进程（master process）和工作进程（worker process）的设计。主进程负责读取配置、打开端口、管理工作进程，而工作进程则负责处理实际的请求。当你向主进程发送 SIGHUP 信号时（重新加载配置文件），主进程先验证新的配置，成功后会启动新的工作进程来应用新的配置，并且让旧的工作进程停止接受新连接，处理完成已有的连接之后再退出，因此正在处理的请求不会被突然中断。

### 多站点配置 {#multiple-servers}

Nginx 的一个十分炫酷的功能就是可以实现一台主机上运行多个网站，对不同的域名提供不同的服务。这就是所谓的虚拟主机配置。

那么如何实现呢？答案就是 `server` 块中的 `server_name` 指令。`server_name` 指令用于定义服务器的名称，可以是域名、IP 地址、通配符等。我们来看一个典型的示例：

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

那 `default_server` 又是什么意思呢？它表示默认站点，当请求的域名不在 `server_name` 中时，Nginx 会使用 `default_server` 对应的 `server` 块来处理请求。该站点的 server_name 指定为 `_`，是一种约定俗成的默认域名，本身没有特殊含义。对于配置了 `default_server` 的 `server` 块，你也可以完全不写 `server_name` 指令。一般建议为 Nginx 配置一个默认站点，用于处理未知域名的请求。

!!! example "拒绝未知域名请求"

    你也可以通过配置一个默认站点来拒绝未知域名的请求，例如：

    ```nginx
    server {
        listen 80 default_server;  # 默认站点
        listen [::]:80 default_server;
        listen 443 default_server ssl;  # 默认站点（HTTPS）
        listen [::]:443 default_server ssl;
        ssl_reject_handshake on;  # 拒绝 SSL 握手
        return 444;  # 直接关闭连接
    }
    ```

    这样，当请求的域名不符合任何一个已经配置的 `server_name` 时，Nginx 对于 HTTP 请求会直接关闭连接，同时拒绝 HTTPS 请求的 SSL 握手。

    一些特定地区或环境的监管要求 HTTP 服务器对未备案登记的域名的请求拒绝响应，这时可以使用这种配置。

我们建议将不同的站点配置放置于不同的文件中：

```nginx title="/etc/nginx/sites-available/example.com"
server {
    listen 80;
    server_name example.com www.example.com;
    # ...
}
```

```nginx title="/etc/nginx/sites-available/example.org"
server {
    listen 80;
    server_name example.org www.example.org;
    # ...
}
```

```nginx title="/etc/nginx/sites-available/default"
server {
    listen 80 default_server;
    server_name _;
    # ...
}
```

然后在 `/etc/nginx/sites-enabled` 目录下创建符号链接：

```bash
sudo ln -sf /etc/nginx/sites-available/example.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/example.org /etc/nginx/sites-enabled/
# 默认情况下 default 站点已经启用
# sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/
```

### 处理复杂的 location 匹配 {#complex-location-matching}

在 location 块里，我们可以使用一些指令来处理请求，如：

- [`proxy_pass http://backend_server;`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)：反向代理。
- `root /var/www/html;`：指定网站根目录。
- `try_files $uri $uri/ =404;`：尝试查找文件，如果找不到返回 404 错误。
- [`return 200 "Hello, World!";`](https://nginx.org/en/docs/http/ngx_http_rewrite_module.html#return)：返回指定的状态码和内容。
- [`include fastcgi_params;`](https://nginx.org/en/docs/ngx_core_module.html#include)：导入 `fastcgi_params` 文件的内容，引入 FastCGI 参数。

同时在一个 `server` 块中，我们也可以定义多个 `location` 块来处理不同的请求路径。以下介绍几种常见的 `location` 匹配方式。

#### Location 匹配 {#location-matching}

Nginx 需要决定由哪个 `location` 块来处理请求时，会根据请求的 URI path 来匹配 `location` 块。

Nginx 支持多种匹配方式，主要通过 `location` 指令后面的可选修饰符来区分。常用的修饰符有：

前缀匹配（无修饰符）

:   前缀匹配是最基本的匹配方式，只要请求的路径以 `location` 块的路径开头，就会匹配成功。例如：

    ```nginx
    location /example {
        # 处理请求 /example 和 /example/xxx
        return 200 "This is a prefix match.";
    }
    ```

    多个前缀匹配时，Nginx 会选择匹配前缀最长的 `location` 块。例如：

    ```nginx
    location /example { ...; }
    location /example/sub { ...; }
    ```

    在此例中，请求 `/example`、`/example123` 和 `/example/test` 会匹配第一个 `location`；请求 `/example/sub/page` 会匹配到第二个 `location`，因为它的前缀更长。

前缀匹配（`^~`）

:   这是另一种形式的前缀匹配，匹配规则与无修饰符相同，但会阻止后续的正则匹配检查。

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

    在这个例子中，如果请求的 URI 是 `/static/style.css`，则会匹配到第一个 `location` 块，因为它是以 `/static/` 开头的前缀匹配，且使用了 `^~`，Nginx 不会继续检查正则匹配。

精确匹配（`=`）

:   精确匹配，只有请求的路径与 `location` 块的路径完全相同时才匹配，优先级最高。

    ```nginx
    location = /example {
        # 处理请求 /example
        # 不处理 /example/xxx
        return 200 "This is an exact match.";
    }
    ```

正则匹配（`~` 和 `~*`）

:   正则匹配的 modifier 有两种，区分大小写的 `~` 与不区分大小写的 `~*`。两种 modifier 的优先级都是最低的，例如：

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

#### Location 块的匹配顺序 {#location-matching-order}

Nginx 在处理请求时会按照以下顺序匹配 `location` 块：

1. 精确匹配 (`=`)。
2. 前缀匹配（无修饰符和 `^~`，按最长前缀匹配）。

    在此步骤中，所有无修饰符和 `^~` 的 `location` 块会一起参与匹配，Nginx 会选择匹配前缀最长的 location。
    在确定了最长前缀匹配后，如果该 `location` 块使用了 `^~` 修饰符，Nginx 会停止匹配过程，直接使用该 `location` 块处理请求；否则，Nginx 会继续进行正则匹配检查。

3. 正则匹配（`~` 和 `~*`，按在配置文件中的出现顺序匹配）。

    如果有匹配到的正则表达式，Nginx 会使用该 `location` 块处理请求。
    如果没有匹配到的正则表达式，Nginx 会使用第二步中匹配到的前缀 `location` 块处理请求。

### TLS {#tls}

TLS 是一种加密通信协议，用于保护客户端和服务器之间的通信安全。HTTPS 就使用了 TLS。你可以在 <https://cherr.cc/ssl.html> 找到 SSL/TLS 的原理解释。

!!! note "SSL?"

    在早期，HTTPS 使用 SSL 来加密通信，但是人们后续发现 SSL 存在一些安全漏洞，因此逐渐被 TLS 取代。尽管如此，SSL 这个术语仍然被广泛使用，尤其是在非正式场合下。因此，SSL 和 TLS 在很多情况下可以视为同义词。

一般的 HTTP 监听端口是 80，HTTPS 监听端口是 443，这是 IANA（互联网号码分配局）为这两种协议分配的标准端口号。Nginx 支持 TLS 协议，可以用来配置 HTTPS 站点。

#### 申请证书 {#getting-certificates}

首先，你需要为你的域名申请一个 TLS 证书。一般有以下几种方式：

- 使用基于 ACME 协议的免费证书，例如 Let's Encrypt、ZeroSSL 等。可以使用 [Certbot](https://certbot.eff.org/)、[acme.sh](https://github.com/acmesh-official/acme.sh) 等工具来申请和自动续期证书。
- 购买商业证书。
- 自签名证书（仅用于测试环境，不建议在生产环境中使用）。

!!! tip "ngx_http_acme_module"

    Nginx 的 [`ngx_http_acme_module`](https://nginx.org/en/docs/http/ngx_http_acme_module.html) 也实现了 ACME 协议，可以类似 Caddy 那样避免多余的证书管理工具，直接让 Nginx 自行申请和续期证书。该模块可能需要自行编译安装。

!!! comment "@taoky: 商业证书一定比免费证书更好吗？"

    不一定。经常有的一种论调是：商业证书因为付了钱，所以比 Let's Encrypt 等免费证书更可靠、更安全，例如像[下面这样](https://www.bilibili.com/opus/1119462279183597571)：

    > 北大用的商业证书，这种证书能证明这个网站确实属于北京大学，你可以看证书颁发对象的组织栏。清华用的是免费证书（注：Let's Encrypt），没有组织信息，不能证明这个网站属于清华大学。商业证书大概每年万把块？我不清楚具体行情，但世一大不应该差这点钱[吃瓜]

    这里存在的几个常见的误解是：

    1. 「商业证书」不代表一定有组织信息。证书分为三种：DV（Domain Validation，域名验证）、OV（Organization Validation，组织验证）和 EV（Extended Validation，扩展验证）。其中 DV 证书只验证域名所有权。以上提供免费证书的服务只签署 DV 证书，而付费 CA 除了 OV 和 EV 证书以外，也大量销售 DV 证书。
    2. 证书的核心功能是：证明你连接的是域名对应的服务器，并且加密传输的数据。不管是 DV、OV 还是 EV 证书，都能同等安全地实现这个功能。
    3. 在很久以前，浏览器会给 EV 证书在地址栏显示组织信息，但是现代浏览器早已经不再这么做了。因为：

        - 大部分人不怎么看地址栏，更别说注意到组织信息了。
        - 用户大多只关注是不是 HTTPS（在很久以前，如果网站是 HTTPS 的话，地址栏左侧对应区域会是绿的），而不会刻意去区分证书类型。
        - 恶意攻击者可以合法注册一个名称相似的组织，然后申请 EV 证书用于诈骗，这样的 EV 证书可能反而会强化用户的错误信任。例如 [2017 年曾有安全研究员注册了名叫「Identity Verified」（身份已验证）的公司，并申请到了 EV 证书](https://www.bleepingcomputer.com/news/security/extended-validation-ev-certificates-abused-to-create-insanely-believable-phishing-sites/)， [同年另一名安全研究员用不到 200 美元成功注册了一个名为「Stripe, Inc.」的组织，并给自己的域名申请到了对应的 EV 证书，用于展示 EV 证书的设计缺陷](https://arstechnica.com/information-technology/2017/12/nope-this-isnt-the-https-validated-stripe-website-you-think-it-is/)。

        因此，即使申请 EV 证书，这种付费 CA 的「背书」意义也非常有限。至少除非你不怕麻烦，而且钱多得没地方花，否则我个人并不建议为了 EV 证书而花钱。
    4. 免费证书使用的 ACME 协议决定了，能为域名申请到有效证书的前提是申请方对域名有控制权。并且，现在所有证书签署都有证书透明度（Certificate Transparency，CT）机制，任何人都可以[查询](https://crt.sh/)到某个域名对应的证书签署记录。因此想要骗签证书难度很大，并且很容易被发现。
    5. 安全性不取决于花了多少钱，而是取决于具体实践。ACME 协议支持自动化签署、续期证书，可以大大降低人为操作失误（包括泄漏私钥、忘记续期）的风险。而**如果花了钱买了 EV 证书，但是最后部署的时候却是通过微信（我听说过不止一例类似的情况）给对应服务的运维传递证书私钥，那安全性反而大大降低了，远不如自动化的免费证书**。

!!! tip "Debian 的 snakeoil 自签名证书"

    Debian 系统的 `ssl-cert` 包自带了一个自签名的测试证书。对应的证书在 `/etc/ssl/certs/ssl-cert-snakeoil.pem`，私钥在 `/etc/ssl/private/ssl-cert-snakeoil.key`。可以用它本地测试 HTTPS 配置，但不建议在生产环境中使用。

    如果需要重新生成，可以执行：

    ```bash
    make-ssl-cert generate-default-snakeoil -f
    ```

以下假设你的证书保存在 `/etc/nginx/ssl/example.com.crt` 和 `/etc/nginx/ssl/example.com.key`。

!!! tip "证书格式"

    PEM 格式是最常见的证书格式。其内容为纯文本，包含 base64 编码的相关数据。对于证书（一般为 `pem`、`crt` 或者 `cer` 后缀）：

    ```pem
    -----BEGIN CERTIFICATE-----
    （base64 编码的数据）
    -----END CERTIFICATE-----
    ```

    对于私钥（一般为 `pem` 或 `key` 后缀）：

    ```pem
    -----BEGIN PRIVATE KEY-----
    （base64 编码的数据）
    -----END PRIVATE KEY-----
    ```

    可以使用 OpenSSL 工具查看信息：

    ```bash
    openssl x509 -in example.crt -text -noout  # 查看证书信息
    openssl pkey -in example.key -text -noout  # 检查私钥
    ```

!!! tip "fullchain.pem"

    一些 ACME 客户端会生成 `fullchain.pem` 文件，它包含了服务器证书和中间证书的完整链。如果存在这个文件，请**优先使用**它，否则浏览器以外的其他客户端可能会因为缺少中间证书而无法验证证书链。

#### TLS 配置 {#tls-configuration}

然后，你需要在 Nginx 配置文件中添加 TLS 配置：

```nginx
server {
    listen 443 ssl;  # 监听的端口
    server_name example.com;  # 指定的域名
    root /var/www/example.com;  # 网站根目录

    ssl_certificate /etc/nginx/ssl/example.com.crt;  # TLS 证书路径
    ssl_certificate_key /etc/nginx/ssl/example.com.key;  # TLS 证书密钥路径

    # （可选）SSL 设置
    ssl_protocols TLSv1.2 TLSv1.3;  # 启用的 TLS 协议（默认值）
    ssl_ciphers 'HIGH:!aNULL:!MD5';  # 使用的加密套件（默认值）
    ssl_prefer_server_ciphers on;  # 优先使用服务器的加密套件（默认为 off）
    ssl_session_cache shared:SSL:10m;  # TLS 会话缓存大小（默认没有缓存）
    ssl_session_timeout 10m;  # TLS 会话超时时间（默认为 5m）

    # （可选）HSTS（HTTP Strict Transport Security）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

注意到和前文的配置不同，这里的监听端口是 443，而且增加了 `ssl` 选项。`ssl_certificate` 和 `ssl_certificate_key` 分别指定了 TLS 证书和密钥的路径。

!!! note "既然 TLS 是加密的，那么 Nginx 是怎么在握手阶段知道要用哪个 `server` 块，以及里面对应的证书呢？"

    在 TLS 握手阶段，绝大多数客户端都会发送 SNI（Server Name Indication，服务器名称指示）信息，告诉服务器它想要连接的域名。**SNI 是明文的**，因此服务器可以根据 SNI 信息来选择对应的 `server` 块和证书。

在配置文件中，我们还提到了一些可选的配置，如中间证书、TLS 设置、HSTS 等。一般建议设置 `ssl_protocols TLSv1.2 TLSv1.3;`，因为 SSLv3、TLSv1.0 和 TLSv1.1 等旧的加密协议已经不再被认为是安全的了。

HSTS 是一种安全机制，用于强制客户端（浏览器）使用 HTTPS 访问网站。当用户首次访问支持 HSTS 的网站时，浏览器会通过 HTTP 或 HTTPS 发送请求。如果网站支持 HSTS，服务器会在响应中包含 `Strict-Transport-Security` 头部，指示浏览器该网站应仅通过 HTTPS 访问。`add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;` 表示启用 HSTS，浏览器会在 1 年内强制使用 HTTPS 访问网站，并且包括子域名。

!!! tip "购买域名之前注意一下 HSTS 预加载列表哦！"

    [HSTS 预加载列表（HSTS Preload List）](https://hstspreload.org)是一个由浏览器维护的列表，在这个列表里面的网站浏览器在访问时必须使用 HTTPS。如果买了一个在 HSTS 预加载列表上面的域名，但是不想用 HTTPS 的话，事情就会非常麻烦。

    此外，一些 TLD（顶级域）也被加入到了 HSTS 预加载列表中，例如 `.dev` 等。

!!! lab "访问 HTTP 自动跳转到 HTTPS 的配置"

    假设希望让用户访问 `http://example.com` 时自动跳转到 `https://example.com`，对应的 `server` 块要怎么写呢？（提示：`return` 指令；HTTP 301 是永久重定向）

### 反向代理与负载均衡 {#reverse-proxy-load-balancing}

在[站点配置简介](#site-config-intro)部分，我们给出了一个简单的反向代理配置示例。实际上，Nginx 的反向代理功能非常强大，可以实现负载均衡、缓存、请求修改等功能。

#### 反向代理杂项配置 {#reverse-proxy-misc}

以下介绍一些常用的反向代理配置选项：

```nginx
location / {
    proxy_pass http://backend_server;  # 反向代理的地址
    # 设置 header 部分略过
    proxy_buffering on;  # 启用 buffering（默认启用）
    proxy_ssl_server_name on;  # 向后端服务器发送 SNI（默认关闭）
    proxy_connect_timeout 10s;  # 连接后端服务器的超时时间（默认 60s）
    proxy_max_temp_file_size 128m;  # 临时文件的最大大小（默认 1024m）
}
```

这里比较重要的配置是 [buffering](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering) 的启用与否。在启用 buffering 的时候，Nginx 在收到后端数据后，不会立刻给客户端，而是先将数据缓存在内存或者临时文件中，然后再发送，以此提高吞吐量。但是对于延迟敏感的应用，或者在磁盘空间有限的情况下，可能需要关闭 buffering。

此外，在配置一些应用的时候，可能需要额外添加 WebSocket 支持。

!!! note "WebSocket 是什么？"

    在现代网站开发时，经常存在的一种需求是：服务端需要主动向客户端推送数据，而不是仅仅被动地响应客户端（浏览器）请求。如果让浏览器定期轮询服务器，既浪费资源，又增加延迟。WebSocket 协议正是为了解决这个问题而设计的。它允许在客户端和服务器之间建立一个持久的双向通信通道，从而实现实时数据传输。

    WebSocket 协议在协商时会先发送一个 HTTP/1.1 请求，包含 `Upgrade: websocket` 与 `Connection: Upgrade` 头，表示请求升级到 WebSocket 协议。

以下给出一个示例：

```nginx
http {
    # ...
    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    server {
        # ...

        location / {
            # 其他反向代理配置略过
            proxy_http_version 1.1;  # 使用 HTTP/1.1 协议
            proxy_set_header Upgrade $http_upgrade;  # 支持 WebSocket 升级
            proxy_set_header Connection $connection_upgrade;  # 支持 WebSocket 连接
        }
    }
}
```

这里 [`map`](https://nginx.org/en/docs/http/ngx_http_map_module.html#map) 指令必须在 `http` 块中，定义了一个从 HTTP 请求的 `Upgrade` 头到 `$connection_upgrade` 变量的映射关系。

!!! note "为什么不能 `proxy_set_header Connection $http_connection`？"

    在 HTTP 标准中，[`Connection`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Connection) 头是 hop-by-hop 的，这意味着这个头[不应该按照原样转发](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers#hop-by-hop_headers)。直接转发会存在非预期的副作用。

#### 反代缓存 {#reverse-proxy-caching}

Nginx 可以作为反向代理缓存服务器，缓存后端的响应内容，从而减少后端的负载，提升性能。常用于缓存局域网外部的静态资源（将外部的网站作为反向代理的「后端」），提供给局域网内的用户访问。

首先需要在 `http` 块中设置缓存路径，类似如下：

```nginx
http {
    # ...
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=exampleCache:128m inactive=1d max_size=4G;
}
```

这里，[`proxy_cache_path`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_path) 指令定义了缓存存储路径等参数。这里的参数含义如下：

- `levels=1:2`：定义缓存目录的层级结构，`1:2` 表示第一层目录使用 1 个字符，第二层目录使用 2 个字符，最终路径就类似于 `/var/cache/nginx/a/bc/...bca` 这样的形式。这是为了避免单个目录下文件过多在一些文件系统中会导致的性能问题。
- `keys_zone=exampleCache:128m`：定义缓存键值区域的名称和大小，这里是 `exampleCache`，大小为 128MB。注意 128MB 不是缓存的总大小，而只是用于存储缓存键值的内存大小。1MB 大约可以存储 8000 个键。
- `inactive=1d`：定义缓存项在多长时间内没有被访问就会被删除，这里是 1 天。默认是 10 分钟。
- `max_size=4G`：定义缓存的最大大小，这里是 4GB。

之后在需要缓存的块中加入 [`proxy_cache`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache) 指令。以下是一个比较激进的缓存配置：

```nginx
location / {
    proxy_pass http://backend_server;
    proxy_cache exampleCache;  # 启用 exampleCache 对应的缓存
    proxy_cache_valid 200 12h;  # 定义 200 响应的缓存时间为 12 小时
    proxy_cache_valid 301 302 6h;  # 定义 301 和 302 响应的缓存时间为 6 小时
    proxy_cache_valid 400 500 502 504 1m;  # 定义 4xx 和 5xx 响应的缓存时间为 1 分钟
    proxy_cache_valid any 5m;  # 定义其他响应的缓存时间为 5 分钟
    proxy_cache_revalidate on;  # 对过期的缓存使用条件请求
    proxy_cache_use_stale error timeout invalid_header updating http_500 http_502 http_503 http_504;  # 在后端错误时使用过期缓存
    add_header X-Cache-Status $upstream_cache_status;  # 添加响应头显示缓存状态
}
```

这里加入的一些额外选项：

- [`proxy_cache_valid`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_valid) 指令用于定义不同响应状态码的缓存时间。
- [`proxy_cache_revalidate`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_revalidate) 则会在缓存过期后使用条件请求（If-Modified-Since 或 If-None-Match）来验证缓存的有效性，如果后端资源没有变化，则继续使用缓存。
- [`proxy_cache_use_stale`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_use_stale) 指令允许在后端服务器出现错误时使用过期的缓存响应，从而提高可用性。
- 最后的 `add_header` 用于在响应头中添加一个 `X-Cache-Status` 字段，显示缓存状态（`HIT`、`MISS`、`BYPASS` 等）。

#### 负载均衡配置 {#load-balancing-configuration}

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

Nginx 支持多种负载均衡算法，如轮询、加权轮询、IP 哈希、最少连接等。

Nginx 支持多种负载均衡算法，默认是轮询（round-robin）。可以通过在 upstream 块中指定不同的算法来更改负载均衡策略，例如：

加权轮询：

```nginx
upstream backend {
    server backend1.example.com weight=3;  # 权重为 3
    server backend2.example.com weight=1;  # 权重为 1
}
```

最少连接：

```nginx
upstream backend {
    least_conn;  # 使用最少连接算法
    server backend1.example.com;
    server backend2.example.com;
}
```

IP 哈希，使得同 IP 的用户始终可以访问到同一个节点：

```nginx
upstream backend {
    ip_hash;  # 使用 IP 哈希算法
    server backend1.example.com;
    server backend2.example.com;
}
```

根据 `key` 指定的变量进行哈希：

```nginx
upstream backend {
    hash $request_uri consistent;  # 使用请求 URI 进行哈希
    server backend1.example.com;
    server backend2.example.com;
}
```

!!! tip "一致性哈希算法"

    在上面的配置中，我们添加了 `consistent` 选项，这表示使用[一致性哈希算法](https://en.wikipedia.org/wiki/Consistent_hashing)，而不是传统的 `hash(key) % N` 的方法。它可以保证在节点数量变化时，尽可能少地改变已有的映射关系。

`server` 块后还可以添加诸如 `max_fails`（最大失败次数）、`fail_timeout`（失败超时时间）等参数来控制节点的故障转移行为。

<!-- ## 示例讲解

以下给出一些实践中会使用的 Nginx 配置示例。

### 反向代理配置

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
```

但是这只是最简单的反向代理配置，实际情况下往往还需要根据不同的服务做一些特殊的配置，可以通过两个狠狠坑过我的例子来学习。

!!! bug "alist 反向代理非标准端口或启用 https 后丢失 https 或端口号/无法播放视频"

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

!!! bug "Grafana 需要 websocket 反代支持"

    WebSocket 是一种全双工通信协议，用于在客户端和服务器之间建立持久连接，实现实时通信。Nginx 支持 WebSocket 协议，可以用来配置 WebSocket 服务器。

    参考：<https://grafana.com/tutorials/run-grafana-behind-a-proxy/>

    关键在于 Grafana 加载数据时使用了 WebSocket，需要指示 Nginx 支持 WebSocket 反代。

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
    ``` -->
