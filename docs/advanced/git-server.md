---
icon: fontawesome/brands/git
---

# Git 服务

!!! note "主要作者"

    [@taoky][taoky]

!!! warning "本文编写中"

本文讨论在镜像站场景下，为不特定用户提供基于 HTTP(S) 协议的 Git 拉取服务（Git over HTTP(S)）相关的知识与优化技巧。本文**不**涉及以下主题：

- 交互式的 Git 服务，例如 [GitWeb](https://git-scm.com/book/en/v2/Git-on-the-Server-GitWeb)、[GitLab](https://gitlab.com/opensource/gitlab-ce)、[Forgojo](https://forgejo.org/)
- 通过 Git 协议（TCP 9418）或 SSH 协议拉取数据
- Git 与用户认证
- 需要用户向服务器推送（push）变更的场景

建议在阅读[网络服务实践的 Nginx 服务器](../ops/network-service/nginx.md)与[版本管理与合作](../dev/git.md)后再阅读本部分。

!!! note "其他实现：JGit"

    以下介绍的是基于 Git 官方的 C 实现的内容，不过这不是唯一的选择。Google 的 [Gerrit](https://www.gerritcodereview.com/) 平台使用的就是基于 Java 的 [JGit](https://github.com/eclipse-jgit/jgit)，其实现了完整的与 Git 服务有关的功能。

## 搭建服务 {#setup-service}

Git over HTTP(S) 有两种传输协议：Dumb protocol 和 Smart protocol，前者不需要运行专门的服务，而后者需要。Smart protocol 处理用户请求的组件是 [git-http-backend][git-http-backend.1]，这是一个 CGI 程序。

!!! note "CGI"

    CGI（Common Gateway Interface）是一种传统的 Web 服务器与用户程序交互的接口：对需要给程序处理的每个 HTTP 连接，Web 服务器读取用户请求的头之后，启动用户程序，将请求头信息（例如请求方法 `REQUEST_METHOD`、请求路径 `PATH_INFO`）放在环境变量中，请求的 body 通过标准输入提供给用户程序，而程序的标准输出则会在 Web 服务器处理后作为返回给用户的响应。可参考 [RFC 3875](https://www.rfc-editor.org/rfc/rfc3875) 了解相关标准。

    由于 CGI 程序每个请求都有创建与销毁进程的开销，因此如今大部分网络应用都会直接处理 HTTP 请求，Web 服务器通过反代（`proxy_pass`）的方式将请求转发给对应的网络应用。

Nginx 支持使用 [FastCGI](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html) 或 [SCGI](https://nginx.org/en/docs/http/ngx_http_scgi_module.html) 模块，它们在 CGI 的基础上自定义了优化的协议。为了运行我们的 CGI 程序，这里安装 `fcgiwrap` 包。[fcgiwrap](https://github.com/gnosek/fcgiwrap) 可以将 CGI 程序包装为 FastCGI 接口，以此对接 Nginx 的 `ngx_http_fastcgi_module` 模块。
