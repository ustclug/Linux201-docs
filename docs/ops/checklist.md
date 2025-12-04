---
icon: octicons/checklist-16
---

# 运维检查单

!!! note "主要作者"

    [@iBug][iBug]、[@libreliu][libreliu]

!!! warning "本文编写中"

本节主要提供如单/多台 Linux 服务器供多用户分享的情况下的运维配置和检查清单。

如果遵循本节提供的内容进行设置和排查操作，则可以部署基本可用的服务器环境，并且防范常见的网络安全问题。

## 系统安装

- 使用 PXE 方式或 U 盘安装较稳定且确保适当长度的维护时间的 Linux 发行版
- 安装时对有 root 或有 sudo 权限的用户设置强密码
- 尽量在 SSD 上部署系统 rootfs，并且确认分区方案合理

## 软件安装

- 对于部署在中国大陆地区的服务器，使用镜像站替换软件包管理系统提供的源
- 除非确有需要，不使用除软件包管理系统之外的方法安装软件到 `/home` 外的位置；对使用软件包管理系统之外的方法安装到 `/home` 外位置的软件，系统管理员应建立台账
- 对于实验室场合，在系统目录内设置恰当版本的编译和开发环境，并对有额外需求的用户的提供在家目录设置单独工具链的适当指引

    > TODO: explain

- 必要但容易忽略的维护系统稳定、帮助调试的工具
    - `earlyoom` 或 `systemd-oomd`：用户态监测内存使用，在内存不足时自动杀死占用内存过多的进程
    - `systemd-coredump`：收集崩溃进程的 coredump 文件
    - `chrony` 或 `systemd-timesyncd`：[自动时钟同步](network-service/ntp.md#ntp-tools)
    - `bcc-tools`：一系列基于 BPF 的调试工具
    - `bpftrace`：快速编写跟踪内核或用户态程序的 BPF 的脚本
    - `rasdaemon`：收集系统硬件（CPU、内存等）的错误信息
    - 性能监测工具，包括 `htop`、`iotop`、`iftop`、`bmon` 等
    - `ncdu`：快速检查谁吃了大量磁盘空间

## 远程管理

- 对于带有 IPMI 等带外管理功能的服务器，将其启用，并配置固定 IP 地址和安全的密码后接入网络

    > 正确配置的 IPMI 功能将为服务器崩溃等无法正常登录进入服务器的情况下的重启操作提供方便，可提升如假期等情况下的服务器可靠性。
  
- 正确[设置 SSH 服务](../dev/ssh.md#sshd-config)，并作为远程管理的主要手段

    > TODO: add ref to ssh & explain

## 系统安全

- 为所有用户（或者至少 root 及有 sudo 权限的用户）都设置强密码
- 禁用 SSH 的密码登录（`PasswordAuthentication no`）
    - 如果有任何原因需要启用密码登录，至少禁用 root 用户的密码登录（`PermitRootLogin prohibit-password`）
    - 或者，仅对有需要的用户启用密码登录（`Match user <username>`、`PasswordAuthentication yes`）

## 网络安全

- MySQL、PostgreSQL、Redis 等数据库服务只监听本地地址（localhost、`127.0.0.1` 或 Unix socket）
    - 或者，配置外部防火墙阻断相关端口的入站连接（例如 MySQL: 3306，PostgreSQL: 5432，Redis: 6379）
