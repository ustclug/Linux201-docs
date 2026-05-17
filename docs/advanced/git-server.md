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

Git over HTTP(S) 的核心组件是 [git-http-backend][git-http-backend.1]，这是一个 CGI 程序，可以与 FastCGI 等实现对接。

!!! note "CGI"

    (TODO)
