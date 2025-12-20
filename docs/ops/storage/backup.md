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
- 使用 [Btrfs](./filesystem.md#btrfs-snapshot)、[ZFS](./zfs.md#snapshot) 或 LVM 提供的快照功能。Btrfs 与 ZFS 提供了 send/receive 功能以便网络传输。
- 使用 `rclone` 同步到云存储（例如 OneDrive、S3 对象存储等）。
- 使用诸如 [Duplicity](https://duplicity.gitlab.io/)、[BorgBackup](https://www.borgbackup.org/)、[restic](https://restic.net/) 等备份工具。
- 特定平台可能有专用的备份工具，例如虚拟化平台 Proxmox VE 的 [Proxmox Backup Server](https://proxmox.com/en/products/proxmox-backup-server/overview)。

!!! warning "单纯的快照与 RAID 都不是备份"

    快照是文件系统的特性，如果文件系统损坏，那么快照就都无法正常读取。而 RAID 只能在硬盘故障数量小于对应等级限制时才能保证数据完整性，无法防止在诸如误删除、自然灾害等情况下数据的丢失与损坏。

以下首先介绍设计备份时需要注意的问题，之后从上述方法列表引申开来，介绍一部分工具的使用方法与技巧。

## 备份的注意事项 {#backup-considerations}

除了简介中提到的 3-2-1 原则以外，备份的设计还需要关注**版本管理**与**数据一致性**。

版本管理的问题很容易理解：如果备份的版本只有一份的话，那么一旦数据被误删除，并且触发了备份，那么被删除的数据就没法用正常方法找回了。不过如果数据很大的话，存储每份版本就会需要大量的磁盘空间，因此在选型时需要考虑使用支持增量备份或去重的方案。

而数据一致性的问题在不少时候会被忽视。

!!! note "崩溃一致性"

    很多时候，我们希望即使程序崩溃、系统断电，程序维护的数据内部状态仍然是一致的。这被称为崩溃一致性（crash consistency）。一般来讲，数据库都实现了崩溃一致性。

即使应用实现了崩溃一致性，如果备份工具直接复制对应的文件，那么得到的文件也有可能是不一致的——这个文件可能前半部分在 A 状态，后半部分在 B 状态。因此，备份数据库一般都使用数据库软件提供的 dump 工具导出 SQL，而不是直接用 rsync 等工具简单复制数据库对应的存储文件。

如果需要备份的文件有一致性的要求，并且不方便使用专用的工具，那么也可以使用文件系统的快照功能避免上述提到的问题。

最后，在有条件的情况下，需要验证备份的有效性，避免出现备份损坏或不完整的情况。

!!! example "反面例子"

    2017 年，GitLab 由于操作失误，在错误的数据库主机上执行了命令导致数据丢失。尽管设置了各种备份，他们没能够第一时间有效恢复：

    - LVM 备份每天执行一次，上一次执行还是手动在 6 小时之前做的；备份的数据会加载到 staging 环境里面，但是 webhook 数据会被删除。
    - 常规备份每天执行一次，但是没人知道备份到了哪里；等到找到的时候发现备份结果只有几个字节。
    - PostgreSQL 的备份因为版本不兼容，实际上一直运行失败，啥都没备份。
    - Azure 的磁盘快照没有给数据库服务器开启。
    - S3 的备份也是空的。

    于是最后，五重备份只留下了一个 6 小时前、没有 webhook 数据的备份。

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
rsync -avP /etc /tmp/example1/
# 此时 /etc/passwd 对应 /tmp/example1/etc/passwd
rsync -avP /etc/ /tmp/example2/
# 此时 /etc/passwd 对应 /tmp/example2/passwd
```

!!! warning "是否要在目标路径后添加 `/`？"

    在以上的例子中，我们给目标路径（`/tmp/example1/` 和 `/tmp/example2/`）结尾都添加了 `/`。这是因为如果不在目标结尾添加 `/`，如果原始路径是文件或者**空目录**，并且目标路径不存在的话，rsync 的行为会变成复制并重命名为目标路径。对以下的例子，结果会出现区别：

    ```shell
    mkdir /tmp/example3
    rsync -avP /tmp/example3 /tmp/example4
    # rsync 将 /tmp/example3 复制并重命名为 /tmp/example4
    rsync -avP /tmp/example3 /tmp/example5/
    # rsync 将 /tmp/example3 复制到 /tmp/example5 目录下，即 /tmp/example5/example3
    ```

    在编写脚本的时候，这可能会出现问题，因为如果在测试时没有考虑到原始路径是空目录的情况，那么脚本在运行时就可能会出现意外的行为（例如后续的脚本假设 rsync 会将文件夹复制到目标目录下，但是实际上 rsync 却将其重命名了）。因此，**建议在目标目录路径结尾都添加 `/`**，以避免这种情况的发生。

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

## 备份配置示例 {#backup-examples}

以下是一些实际使用的备份配置示例（其中一些严格意义来说，不是完整的备份方案），以供读者参考。

### 使用 restic 备份到 Backblaze B2 {#restic-backblaze}

restic 是一款现代的备份工具，支持使用包括本地、SFTP、S3 等多种后端存储备份数据，同时支持加密、多主机备份、版本管理等功能。Backblaze B2 云对象存储则以实惠的价格（截至写作时，每月存储开销 6 美元/TB；下载量超过存储 3 倍后流量收费 0.01 美元/GB）与对自动化程序友好的 API 成为了个人用户的热门选择。

首先在 Backblaze 处创建桶和 Application Key，记录下 Bucket 名称和 Application Key 的 ID 和 Key。

!!! note "为每台主机设置单独的 Application Key"

    为了安全起见，建议为每台需要备份的主机创建单独的 Application Key，以便单独吊销。

之后设置环境变量并初始化仓库：

```shell
export B2_ACCOUNT_ID="your_account_id"
export B2_ACCOUNT_KEY="your_account_key"
export RESTIC_REPOSITORY="b2:your_bucket_name:/"
export RESTIC_PASSWORD="your_strong_password"  # restic 使用这个密码加密备份数据
export RESTIC_HOST="your_hostname"  # 用于区分不同主机的备份

restic init
```

!!! tip "也可使用 S3 兼容模式连接 Backblaze B2"

    事实上，由于使用的第三方库的错误处理问题，[restic 官方文档目前更建议使用 S3 兼容模式连接 Backblaze B2](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#backblaze-b2)：

    ```shell
    export AWS_ACCESS_KEY_ID="your_account_id"
    export AWS_SECRET_ACCESS_KEY="your_account_key"
    # 以下 endpoint 需要根据桶所在的实际区域修改
    export RESTIC_REPOSITORY="s3:https://s3.us-east-005.backblazeb2.com/your_bucket_name"
    # ...
    ```

    有关 S3 兼容模式的注意事项，请参阅上述文档。

之后就可以备份了，不过先让我们排除一些不需要备份的目录：

```shell title="excludes"
.local/share/Trash/
.cache/
.local/share/Steam/steamapps/
target/
node_modules/
.cargo/registry/
.cargo/git/
```

以上的排除项是针对备份个人电脑的家目录设置的，排除了回收站、缓存、Steam 游戏库、Rust 与 Node.js 的依赖与构建产物等目录。可以根据自己的实际情况调整。

之后就可以执行备份了：

```shell
restic backup \
  --one-file-system \
  --exclude-file=/path/to/excludes \
  /home/username
```

备份完成后，可以使用以下命令查看备份状态：

```shell
# 查看所有的备份
restic snapshots
# 查看某个备份下的所有文件
restic ls <snapshot_id>
# 使用 FUSE 挂载备份
restic mount /path/to/mountpoint
```

备份积累到一定程度后，可以参考[以下命令](https://restic.readthedocs.io/en/latest/060_forget.html#removing-snapshots-according-to-a-policy)清理旧的备份：

```shell
# 每个主机保留最近 100 个备份
restic forget --group-by=host --keep-last 100
```

建议定时进行备份，以下是一个参考的 systemd timer 配置。其中 `/etc/restic/env` 存储环境变量信息（记得限制权限！），`/usr/local/bin/restic-backup.sh` 则是调用上述备份命令的脚本。

```ini title="restic-backup.service"
[Unit]
Description=Backup to B2 by restic

[Service]
Type=oneshot
EnvironmentFile=/etc/restic/env
ExecStart=/usr/local/bin/restic-backup.sh
```

```ini title="restic-backup.timer"
[Unit]
Description=Run restic backup daily with random delay

[Timer]
OnCalendar=daily
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
```
