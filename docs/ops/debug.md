---
icon: material/bug
---

# 问题调试

!!! warning "本文初稿编写中"

本部分介绍调试问题时的一般思路和方法。
请注意本部分无法面面俱到，因此只能够提供一些在运维上常用的方法，具体问题需要具体分析。

## 服务状态与日志 {#status-and-logs}

当出现异常，登录系统后，第一件事情可能是检查当前系统的服务状态。
`systemctl --failed` 可以列出当前失败的服务。
如果显示大量服务失败，那么说明可能遇到了比较严重的问题，例如磁盘已满等。
可以先尝试将失败的服务恢复。`systemctl status` 可以列出当前系统中的 cgroup 情况（约等于所有正在运行的服务以及进程的树）。

检查日志内容也是检查、排除问题的重要步骤。
现代基于 systemd 的 Linux 系统的日志通常由 systemd-journald 负责管理。
以下是常用的命令：

- `journalctl -b`: 查看本次开机的日志。在 `-b` 后加上 `-1`/`-2` 等可以查看上次/上上次等的开机日志。
- `journalctl --since "1 hour ago"`: 查看最近一小时的日志。
- `journalctl -u xxx.service`: 查看某个服务的日志。
- `journalctl -f`: 实时查看日志。
- `journalctl -b -k`: 查看本次启动的内核态日志。
  `dmesg` 的命令虽然也可以查看，但是因为内核内存有限，所以可能看不到较早的内核态日志信息。
  journald 会帮我们持久化内核态日志信息。

journalctl 默认会使用 pager（换句话说，`less`）显示日志，当然也可以后面接个 `| grep ...` 来过滤日志。
此外，如果使用了用户服务（user service），那么检查用户服务的状态或者日志时，需要加上 `--user` 参数。

!!! comment "@taoky: journald 的一点吐槽"

    首先……journald 看日志太慢了，日志很多的话实在是慢。
    而且 `systemctl status xxx.service` 因为要显示最近几条日志，
    也跟着慢——在 mirrors 服务器上甚至要一分多钟才能显示出服务状态。
    关于这个问题，可以阅读以下讨论:

    - <https://github.com/systemd/systemd/issues/2460>
    - <https://github.com/systemd/systemd/pull/29261>
    - <https://github.com/systemd/systemd/pull/30209>

    然后，journald 设置按照时间的 retention 也不太方便。
    比如说，如果想保留 180 天的日志的话，怎么设置 journald 呢？
    `MaxRetentionSec` 似乎不够……

    最后一点是，如果要实时看内核态日志，我更推荐用 `dmesg -w`，因为颜色更好看一些。

大部分的 Debian 系统会预装 rsyslog，它会将 journald 的日志转发到 `/var/log/syslog`，可以直接使用常规的命令行文本处理工具分析。
其他一些软件可能也不会使用 journald，而是直接将日志写入到 `/var/log/` 目录下的文件中，例如 nginx。

logrotate 会定期（一般是每天，或者文件足够大的时候，请参考 `/etc/logrotate*` 对应的配置）「轮转」（rotate）日志文件：
这是一个将旧日志压缩，更旧的日志删除的过程。为了分析被压缩过的历史日志，可以使用对应压缩软件提供的工具，例如 `gz` 格式对应 `zcat`/`zgrep`，`xz` 格式对应 `xzcat`/`xzgrep`，`zst` 格式对应 `zstdcat`/`zstdgrep` 等等。

## procfs 与 strace {#procfs-and-strace}

`/proc`（procfs）是内核以文件系统形式向用户空间提供的查看、管理进程状态的接口。
其中 `/proc/self` 指向了访问文件的当前进程的信息，`/proc/<pid>` 则指向了 PID 对应进程的信息。
常关注的信息（不会直接从 `htop` 等获得的信息）有：

- `cwd` 与 `exe`：程序的当前工作目录与可执行文件路径
- `fd` 目录包含了所有程序打开的文件描述符
- `stack`：程序在内核态的栈信息，这一项信息在程序一直处于 D 状态（不可中断睡眠）时特别有用

在分析进程行为时，另一个相当有用的工具是 `strace`。它可以输出程序使用的所有系统调用信息，在调试许多问题的时候都可以提供很大的帮助。

## 调试符号与 gdb

## 内核态调试

## 信息收集与寻求帮助
