---
icon: material/web-clock
---

# 网络时间同步

在现代计算环境中，准确的系统时间对服务器的稳定运行至关重要。无论是分布式日志的对齐、安全证书的验证，还是任务调度与数据记录，所有这些功能的正常运行都依赖于系统时钟的精确性。因此，Linux 系统通常需要某种“时间同步”机制，以防止系统时间因硬件时钟漂移而逐渐偏离。

目前主流的时间同步协议是 **NTP（Network Time Protocol）**，它允许计算机通过网络与时间服务器通信，定期校准本地时钟。NTP 使用一种分层结构组织时间源，每层称为一个 **Stratum**。Stratum 值越小，表示距离原始时间参考源越近，理论上同步的精度也越高。这种设计还能有效防止时间源之间形成循环依赖。

* **Stratum 0**：非网络设备，而是高精度的物理时间源（如 GPS 接收器、原子时钟等）。
* **Stratum 1**：直接连接到 Stratum 0 的计算机，作为一级时间源。
* **Stratum 2**：通过网络从一个或多个 Stratum 1 服务器获取时间的服务器。
* **Stratum n**：以此类推，通过网络从 Stratum n -1 获取时间，最大为 Stratum 15；若系统处于 Stratum 16，表示尚未成功同步到任何可靠的时间源。

在实际应用中，普通服务器或终端设备从 Stratum 2 或 Stratum 3 的时间服务器同步时间，已能满足绝大多数需求。若条件允许，选择网络路径更短、延迟更低的时间源，会获得更好的同步效果。

Linux 中支持 NTP 的工具有多种，其中较为常见的有 `systemd-timesyncd` 和 `chrony`。

1. **systemd-timesyncd**

    在使用 `systemd` 的 Linux 系统中，通常默认启用了一个轻量级时间同步服务 —— `systemd-timesyncd`。该服务在系统联网后，会通过 NTP 协议定期向公共时间服务器请求当前时间，并自动校准系统时钟。**如果你只希望“能同步时间”，并不关心精度细节，使用 `systemd-timesyncd` 即可，简单省心。**

    如需自定义同步的时间服务器，可在 `/etc/systemd/timesyncd.conf.d/` 目录下新建一个配置文件（例如 `custom.conf`）。对于位于校园网或企业内网的服务器，建议使用内网可访问的时间源，以减少网络延迟并提升同步稳定性。例如：

    ```ini
    [Time]
    NTP=time.ustc.edu.cn
    ```

    查看 `systemd-timesyncd` 的同步状态，可使用：

    ```bash
    timedatectl show-timesync
    ```

2. **chrony**

    对于需要长时间稳定运行、并对时间精度要求更高的服务器，更推荐使用功能更强大的 `chrony`。它适用于网络条件较差的环境、虚拟机，甚至可在断网情况下估算和修正时间误差。**如果你是服务器运维人员，或对时钟同步的精度和可靠性有较高要求，建议选择 `chrony`。**

    在 Debian/Ubuntu 系统上启用 `chrony` 的方法如下：

    ```bash
    apt -y install chrony          # 安装 chrony
    systemctl enable --now chronyd # 启动服务并设置开机自启
    ```

    使用以下命令可以查看当前同步状态，包括系统时钟偏移量和误差修正速率等信息：

    ```bash
    chronyc tracking
    ```

    查看各时间源的状态（Stratum 一列展示了各时间源的层级）：

    ```bash
    chronyc sources
    chronyc sources -v  # 显示详细界面说明
    ```

完成时间同步后，为确保本地时间显示正确，还需要设置系统时区。例如，设置为中国标准时间（东八区）：

```bash
timedatectl set-timezone Asia/Shanghai --adjust-system-clock
```

设置完时间同步服务和时区后，可使用以下命令检查系统时间、时区、以及 NTP 服务是否已启用：

```bash
timedatectl status
```
