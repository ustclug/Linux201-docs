---
icon: material/apple-safari
---

# 网络服务实践

本部分介绍在 Linux 服务器上进行的一些网络服务实践。

其中网络存储系统的实践请参考 [存储系统/网络存储系统](../storage/network.md)。

## 网络时间同步机制

在现代计算环境中，准确的系统时间对服务器至关重要。无论是分布式日志的对齐、安全证书的验证，还是任务调度与数据记录，所有这些功能的正常运行都依赖于系统时钟的精确性。因此，Linux 系统通常需要某种“时间同步”机制，以防止系统时间因硬件时钟漂移而逐渐偏离。

目前主流的时间同步协议是 NTP（Network Time Protocol），它允许计算机通过网络与时间服务器通信，定期校准本地时钟。Linux 中支持 NTP 的工具有多种，其中较为常见的有 `systemd-timesyncd` 和 `chronyd`。

1. **systemd-timesyncd**

    在使用 `systemd` 的 Linux 系统中，通常默认启用了一个轻量级时间同步服务 —— `systemd-timesyncd`。该服务在系统联网时，会通过 NTP 协议定期向公共时间服务器请求当前时间，并自动对齐本地时钟。


    如需自定义同步的时间服务器，可在 `/etc/systemd/timesyncd.conf.d/` 目录下新建一个配置文件（例如 `custom.conf`），内容如下。对于位于校园内网、无法访问外网的服务器，推荐配置为校内 NTP 源：

    ```ini
    [Time]
    NTP=time.ustc.edu.cn
    ```

    查看 `systemd-timesyncd` 的同步状态可使用：

    ```bash
    timedatectl show-timesync
    ```

2. **chrony**

    对于需要长时间稳定运行、并对时间精度要求更高的服务器，更推荐使用功能更强大的 `chrony`。它适用于网络不稳定、虚拟机环境，甚至可以在离线时进行时间误差的估算与校正。

    在 Debian/Ubuntu 系统上启用 `chrony` 的方法如下：

    ```bash
    apt -y install chrony          # 安装 chrony
    systemctl enable --now chronyd # 启动服务并设置开机自启
    ```

    使用以下命令可以查看当前同步状态，包括系统时钟偏移量和误差修正速率等信息：

    ```bash
    chronyc tracking
    ```

完成时间同步后，为确保本地时间显示正确，还需要设置系统时区。例如，设置为中国标准时间（东八区）：

```bash
timedatectl set-timezone Asia/Shanghai --adjust-system-clock
```

设置完时间同步服务和时区后，可使用以下命令检查系统时间、时区、以及 NTP 服务是否处于激活状态：

```bash
timedatectl status
```



