# 备份方案

!!! warning "本文编写中"

## 简介 {#intro}

备份是保障数据安全的重要手段。在理想情况下，备份应做到 3-2-1 原则：三份文件的副本，其中两份存储在不同的设备上，另一份远程存储。

一般来讲，管理员需要设置定时任务（使用 crontab 或者 [systemd timer](../service.md#timers)），在任务中调用备份数据的命令来实现备份。常见的方法包括：

- 使用 `tar` 归档数据目录。
- 使用 `rsync` 同步数据目录。
- 使用数据库的 dump 工具（例如 `mysqldump`）备份数据库。
- 使用 [Btrfs](./filesystem.md#btrfs-snapshot) 或 ZFS 的快照与 send/receive 功能。
- 使用 `rclone` 同步到云存储（例如 OneDrive、S3 对象存储等）。
- 使用诸如 [Duplicity](https://duplicity.gitlab.io/)、[BorgBackup](https://www.borgbackup.org/) 等备份工具。
- 特定平台可能有专用的备份工具，例如虚拟化平台 Proxmox VE 的 [Proxmox Backup Server](https://proxmox.com/en/products/proxmox-backup-server/overview)。

!!! warning "单纯的快照与 RAID 都不是备份"

    快照是文件系统的特性，如果文件系统损坏，那么快照就都无法正常读取。而 RAID 只能在硬盘故障数量小于对应等级限制时才能保证数据完整性，无法防止在诸如误删除、自然灾害等情况下数据的丢失与损坏。

以下介绍一部分相关的工具。

## Rsync

Rsync 是最常用的文件同步工具之一，支持本地复制和远程复制。相比于 `cp`（本地）和 `scp`（SSH 远程），`rsync` 可以做到增量复制，只复制文件中发生变化的部分，并且能够保留文件完整的元数据信息。Rsync 也是从镜像站点同步完整镜像的事实标准。

### 文件传输 {#rsync-transfer}

最常用的命令：

```shell
rsync -avP --delete /path/to/source /path/to/destination
```

其中 `-a` 代表归档模式，即 `-rlptgoD` 这几个参数的集合，分别代表：

- `r`: 递归复制目录
- `l`: 保留符号链接
- `p`: 保留文件权限
- `t`: 保留修改时间（mtime）
- `g`: 保留 group 信息
- `o`: 保留 owner 信息
- `D`: 保留设备文件与特殊文件

`-v` 代表详细输出，`-P` 代表保留传输一部分的文件且显示进度，`--delete` 代表删除目标目录中源目录没有的文件。以下提供一些参考示例。

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

Rsync 同时也可以作为服务端对外提供 rsync 服务，默认端口为 TCP 873。
