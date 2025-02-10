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

以下介绍一部分相关的工具。

## Rsync
