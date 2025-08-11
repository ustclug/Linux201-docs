# 备份与文件传输工具

!!! note "主要作者"

    [@taoky][taoky]

!!! warning "本文编写中"

## 简介 {#intro}

备份是保障数据安全的重要手段。在理想情况下，备份应做到 3-2-1 原则：三份文件的副本，其中两份存储在不同的设备上，另一份远程存储。

一般来讲，管理员需要设置定时任务（使用 crontab 或者 [systemd timer](../service.md#timers)），在任务中调用备份数据的命令来实现备份。常见的方法包括：

- 使用 `tar` 归档数据目录。
- 使用 `rsync` 同步数据目录。
- 使用数据库的 dump 工具（例如 `mysqldump`）备份数据库。
- 使用 [Btrfs](./filesystem.md#btrfs-snapshot) 或 [ZFS](./zfs.md#snapshot) 的快照与 send/receive 功能。
- 使用 `rclone` 同步到云存储（例如 OneDrive、S3 对象存储等）。
- 使用诸如 [Duplicity](https://duplicity.gitlab.io/)、[BorgBackup](https://www.borgbackup.org/) 等备份工具。
- 特定平台可能有专用的备份工具，例如虚拟化平台 Proxmox VE 的 [Proxmox Backup Server](https://proxmox.com/en/products/proxmox-backup-server/overview)。

!!! warning "单纯的快照与 RAID 都不是备份"

    快照是文件系统的特性，如果文件系统损坏，那么快照就都无法正常读取。而 RAID 只能在硬盘故障数量小于对应等级限制时才能保证数据完整性，无法防止在诸如误删除、自然灾害等情况下数据的丢失与损坏。

以下从上述方法列表引申开来，介绍一部分工具的使用方法与技巧。

## Rsync

Rsync 是最常用的文件同步工具之一，支持本地复制和远程复制。相比于 `cp`（本地）和 `scp`（SSH 远程），`rsync` 可以做到增量复制，只复制文件中发生变化的部分，并且能够保留文件完整的元数据信息。Rsync 也是从镜像站点同步完整镜像的事实标准。

### 文件传输 {#rsync-transfer}

最常用的命令：

```shell
rsync -avP --delete /path/to/source /path/to/destination
```

参数含义如下：

|    参数    |              说明              |
| :--------: | :----------------------------: |
|    `-a`    |  归档模式，等同于 `-rlptgoD`   |
|    `-r`    |          递归复制目录          |
|    `-l`    |          保留符号链接          |
|    `-p`    |          保留文件权限          |
|    `-t`    |     保留修改时间（mtime）      |
|    `-g`    |        保留 group 信息         |
|    `-o`    |        保留 owner 信息         |
|    `-D`    |     保留设备文件与特殊文件     |
|    `-v`    |            详细输出            |
|    `-P`    | 保留传输一部分的文件且显示进度 |
| `--delete` | 删除目标目录中源目录没有的文件 |

以下提供一些参考示例。

将 `/A` 文件复制到 `/tmp/A`：

```shell
rsync -avP /A /tmp/A
# 或者
rsync -avP /A /tmp/
```

将 `/etc` 文件夹复制为/复制到 `/tmp/example`。区别在 source 的结尾是否有 `/`，如果没有的话，源文件夹就会**作为一个整体**复制到目标文件夹内；否则如果有 `/`，源文件夹内的**内容**会被复制到目标文件夹内。

```shell
rsync -avP /etc /tmp/example1
# 此时 /etc/passwd 对应 /tmp/example1/etc/passwd
rsync -avP /etc/ /tmp/example2
# 此时 /etc/passwd 对应 /tmp/example2/passwd
```

作为 `scp` 的高效替代，`rsync` 也支持基于 SSH 的远程复制（远程服务器也需要安装 rsync）。可以使用 `-z` 开启压缩，以 CPU 为代价减小传输量。`rsync` 对增量复制的支持允许了「断点续传」的功能，在网络情况欠佳的时候尤其有用。

```shell
rsync -avPz user@remote:/path/to/source /path/to/destination
rsync -avPz /path/to/source user@remote:/path/to/destination
```

如果远程服务器需要特殊的 `ssh` 参数（例如端口），并且不想修改 `~/.ssh/config`，可以使用 `-e` 参数：

```shell
rsync -avPz -e "ssh -p 2222" user@remote:/path/to/source /path/to/destination
```

### 镜像同步 {#rsync-mirror}

Rsync 同时也可以作为服务端（daemon 模式）对外提供 rsync 服务，默认端口为 TCP 873。

!!! tip "Rsync over TLS"

    Rsync 默认为明文协议，不过其支持通过其他反向代理工具（例如 Nginx 的 stream 模块）实现 TLS 加密，默认端口为 874，需要使用 `rsync-ssl` 命令连接。

以下介绍与镜像同步（mirrors）相关的服务端与客户端配置。其他用途可视情况自行调整。

#### Rsync 服务端配置 {#rsync-server}

Debian 默认的 rsync 的 systemd 服务依赖于 `/etc/rsyncd.conf` 文件，同时 `/usr/share/doc/rsync/examples/rsyncd.conf` 提供了一个参考范例。

一份用于镜像站点的 `rsyncd.conf` 可能如下所示：

```ini
motd file = /etc/rsyncd/rsyncd.motd
pid file = /var/run/rsyncd.pid
log file = /var/log/rsyncd.log
max verbosity = yes
transfer logging = yes
ignore nonreadable = yes
# 需要 adduser --system rsyncd
uid = rsyncd
gid = nogroup
use chroot = yes
dont compress = *
max connections = 50
refuse options = checksum
read only = true
timeout = 240
reverse lookup = no
```

其中比较重要的参数有：

- 安全性相关：rsync daemon 会以 root 身份运行，在收到请求后会 fork 出子进程实际处理请求。`uid` 与 `gid` 用于子进程降权，`use chroot` 用于限制访问范围，避免非预期的漏洞泄漏系统中的其他文件。由于镜像站点肯定不允许用户修改文件，因此 `read only` 应当设置为 `true`。
- 性能相关：`max connections` 用于限制总连接数，`timeout` 用于限制连接超时时间，防止被未响应的客户端长时间占用资源。`dont compress` 与 `refuse options` 用于禁用压缩（如果需要传输的文件大多已经是压缩过的）与检验和（会大量占用服务器 CPU）。`reverse lookup` 用于关闭反向 DNS 查询，避免 DNS 问题导致的连接延迟。

之后就是定义暴露的模块（module）：

```ini
[repo1]
path = /path/to/repo1

[repo2]
path = /path/to/repo2
```

模块是 rsync URL 的第一层，例如 `rsync://server/repo1/somedir/` 中，`repo1` 就是模块名。配置完成之后，可以使用 `rsync://server/` 列出全部模块，`rsync rsync://server/repo1` 来确认，并且采用类似的命令同步某个模块的全部文件。

!!! tip "同时启用多个 rsync 服务"

    如果有需要多个 daemon 的需求（例如需要多个 rsync 服务端 bind 到不同的 IP 地址上），可以使用 systemd 的[模板单元格式](../service.md#unit-template)手动编写 `rsync@.service` 文件。

    同时 `rsyncd.conf` 格式支持导入其他的配置文件，因此不同服务的共通部分可以提取出来。其中 `&include` 用于导入模块的定义，`&merge` 用于导入配置，类似如下：

    ```ini
    # common.inc 包含配置
    &merge /etc/rsyncd/common.inc
    # common.conf 包含模块定义
    &include /etc/rsyncd/common.conf
    ```

!!! tip "使用 systemd 安全加固 rsync 服务"

    [Systemd 服务的安全加固参数](../service.md#service)可以帮助避免未知的安全问题影响 rsync 服务，特别是在 [rsync 于 2025 年 1 月暴露了多个 CVE 的情况下](https://kb.cert.org/vuls/id/952657)（其中两个是服务端的漏洞），这样的加固就显得更加重要。

    一份参考 `rsync@.service` 如下，其中包含安全加固以及降低 IO 与 CPU 优先级的设置（这同样也是[科大镜像站目前使用的配置](https://docs.ustclug.org/services/mirrors/rsync/)）：

    ```ini
    [Unit]
    Description=fast remote file copy program daemon
    ConditionPathExists=/etc/rsyncd/rsyncd-%i.conf
    After=network.target network-online.target

    [Service]
    Type=exec
    PIDFile=rsyncd-%i.pid
    ExecStart=/usr/bin/rsync --daemon --no-detach --config=/etc/rsyncd/rsyncd-%i.conf

    Nice=19
    IOSchedulingClass=best-effort
    IOSchedulingPriority=7
    IOAccounting=true

    ProtectSystem=strict
    ProtectHome=true
    ProtectProc=invisible
    ProtectControlGroups=true
    ProtectKernelModules=true
    ProtectKernelTunables=true
    PrivateTmp=true
    PrivateDevices=true
    NoNewPrivileges=true
    MemoryDenyWriteExecute=true

    ReadWritePaths=/var/log/rsyncd

    [Install]
    WantedBy=multi-user.target
    Alias=rsyncd@.service
    ```

    也可以考虑将 `uid` 与 `gid` 修改为在 systemd 服务中配置（而不是让 daemon 自己降权），并且提供 `chroot` 等必要的 capability。

!!! tip "Rsync 反向代理"

    [ustclug/rsync-proxy](https://github.com/ustclug/rsync-proxy) 项目支持基于模块名的 rsync 反向代理，可以将不同的模块放在不同的服务器上，由 rsync-proxy 代理到不同的后端服务器上。

#### Rsync 客户端参数 {#rsync-client}

一份参考的完整参数如下（修改自 [ustcmirror-images 的 rsync 同步脚本](https://github.com/ustclug/ustcmirror-images/blob/2915ed8c403090f54f4295d8ceef63a12bbaf471/rsync/sync.sh)）：

```shell
rsync -pPrltvH --partial-dir=.rsync-partial --timeout 14400 --safe-links --delete-excluded --delete-delay --delay-updates --sparse --max-delete 4000 rsync://server/repo1/ /path/to/destination
```

其中部分参数含义如下：

|        参数         |                                    说明                                    |
| :-----------------: | :------------------------------------------------------------------------: |
|        `-H`         |                                 保留硬链接                                 |
|   `--partial-dir`   |                       保证部分传输的文件均在该目录中                       |
|     `--timeout`     |                                  超时时间                                  |
|   `--safe-links`    | 忽略指向对应仓库外部的符号链接，避免有问题的符号链接导致其他文件非预期暴露 |
| `--delete-excluded` |                           删除被排除（exclude）的文件                            |
|  `--delete-delay`   |       在同步完成后再删除文件，避免在同步过程中删除文件导致仓库不可用       |
|  `--delay-updates`  |       在同步完成后再更新文件，避免在同步过程中更新文件导致仓库不可用       |
|     `--sparse`      |                            保留稀疏文件的稀疏性                            |
|   `--max-delete`    |              限制删除文件的数量，避免误操作导致大量文件被删除              |

### 包含与排除 {#rsync-include-exclude}

Rsync 支持 `--include` 与 `--exclude` 参数。简单来讲，rsync 的处理规则如下：

1. 每个文件/文件夹会按照用户在命令行中提供的顺序匹配，如果命中，则会被处理，后续的规则对该文件不再生效。具体匹配的规则可参考 [rsync.1][rsync.1] 手册的 "PATTERN MATCHING RULES" 部分。
2. 如果没有命中任何规则，那么会被包含。
3. 命中 `--exclude` 代表其子文件和文件夹也会被排除，因此如果要包含 `a/b/c/d`，那么 `a/`, `a/b/`, `a/b/c/` 都需要被包含。

!!! question "匹配练习"

    请尝试分别写出符合以下条件的 rsync 参数，假设需要从 src 同步到 dst：

    1. 排除 src 下的 `manjaro` 目录（不要排除其他名称包含 `manjaro` 的文件或目录）。
    2. 排除所有名称为 `s390x` 的目录。
    3. 排除 src 下的 `cloud` 目录，但是需要保留 `cloud` 目录下的所有 `repodata.json` 文件。

### SSH 限制 rsync 访问 {#rsync-ssh}

rsync 支持利用 [rrsync 脚本][rrsync.1]限制使用 SSH 连接的用户只能够使用 rsync 读写指定的目录，确保用户不会通过 SSH 执行其他命令，或者访问到指定目录以外的文件。

详情可以参考[本教程关于 SSH 的章节](../../dev/ssh.md#authorized-keys)。

### 文件备份 {#rsync-backup}

Rsync 本身不是完整的备份工具，其没有版本管理功能，因此如果某个文件被误删除/修改，那么 rsync 会将这个变化同步到备份中。不过基于 rsync 高效复制文件的能力，有工具实现了基于 rsync 和文件系统硬链接功能的备份，例如 Linux Mint 的 [Timeshift](https://github.com/linuxmint/timeshift) 项目就通过硬链接实现不同时间点备份的去重操作，而 rsync 负责文件的复制。
