---
icon: material/web-clock
---

# 网络时间同步

!!! note "主要作者"

    [@JiaminL][JiaminL]、[@iBug][iBug]

在现代计算环境中，准确的系统时间对服务器的稳定运行至关重要。无论是分布式日志的对齐、安全证书的验证，还是任务调度与数据记录，所有这些功能的正常运行都依赖于系统时钟的准确性。因此，所有计算机都需要某种“时间同步”机制，以防止系统时间因硬件时钟漂移而逐渐偏离。

## NTP 协议简介 {#ntp}

标准的时间同步协议是 **NTP（Network Time Protocol）**，它允许计算机通过网络与时间服务器通信，定期校准本地时钟。NTP 使用一种分层结构组织时间源，每层称为一个 **Stratum**。Stratum 值越小，表示距离原始时间参考源越近，理论上同步的精度也越高。这种设计还能有效防止时间源之间形成循环依赖。

* **Stratum 0**：非网络设备，而是高精度的物理时间源（如 GPS 接收器、原子时钟等）。
* **Stratum 1**：直接连接到 Stratum 0 的计算机，作为一级时间源。
* **Stratum 2**：通过网络从一个或多个 Stratum 1 服务器获取时间的服务器。
* **Stratum n**：以此类推，通过网络从 Stratum (n-1) 获取时间，最大为 Stratum 15；若系统处于 Stratum 16 的状态，表示尚未成功同步到任何可靠的时间源。

在实际应用中，普通服务器或终端设备从 Stratum 2 或 Stratum 3 的时间服务器同步时间，已能满足绝大多数需求。若条件允许，选择网络路径更短、延迟更低的时间源，会获得更好的同步效果。

## Linux 中的时间同步工具 {#ntp-tools}

Linux 中支持 NTP 的软件有多种，其中较为常见的有 [chrony](https://chrony-project.org/) 、 [systemd-timesyncd](https://wiki.archlinux.org/title/Systemd-timesyncd) 和 [ntpdate](https://www.ntp.org/documentation/4.2.8-series/ntpdate/)。

### chrony

chrony 是一个功能丰富 NTP 软件，它支持多种时间源和网络协议，能够在不稳定的网络环境中保持较高的同步精度，甚至使用与计算机相连的 GPS 设备作为时钟信号源。chrony 还具有自动检测网络延迟和时钟漂移的能力，适合在虚拟机、笔记本电脑等经常变更网络环境的设备上使用。

chrony 曾经是 Debian 发行版的默认 NTP 客户端。对于 Debian 和 Ubuntu 发行版，你也可以使用 `apt install chrony` 手动安装它。

使用以下命令可以查看当前同步状态，包括系统时钟偏移量和误差修正速率等信息：

```shell
chronyc tracking
```

查看各时间源的状态（Stratum 一列展示了各时间源的层级）：

```shell
chronyc sources
chronyc sources -v  # 显示详细界面说明
```

### systemd-timesyncd

systemd 项目也提供了一个轻量级的时间同步客户端，即 systemd-timesyncd。该服务可以在系统联网后通过 NTP 协议定期向网络上的时间服务器请求当前时间，并自动校准系统时钟。如果你只需要“能同步时间”，尤其是当校园网或企业内网中存在 NTP 服务器的时候，systemd-timesyncd 是一个更加简单省心的选项。

Debian 自 12（Bookworm）版本起选择 systemd-timesyncd 作为默认的 NTP 客户端，因此通常情况下你不再需要手动安装它（即 `apt install systemd-timesyncd`）。

你可以在 `/etc/systemd/timesyncd.conf` 文件中查看发行版提供的默认时间服务器配置。如果你想要自己指定同步的时间服务器，可在 `/etc/systemd/timesyncd.conf.d/` 目录下新建一个配置文件（例如 `custom.conf`）。我们推荐尽可能使用位于校园网或企业内网的时间源，以减少网络延迟并提升同步稳定性。例如，科大校园网提供了一个 Stratum 2 的时间服务器 `time.ustc.edu.cn`，你可以在 `/etc/systemd/timesyncd.conf.d/custom.conf` 中添加以下内容让 systemd-timesyncd 使用它：

```ini
[Time]
NTP=time.ustc.edu.cn
```

可以使用以下命令查看 `systemd-timesyncd` 的同步状态：

```shell
timedatectl show-timesync
```

### ntpdate

ntpdate 是一个一次性的时间同步工具。它适用于临时性地校准系统时钟，通常用于在系统启动时或在没有持续运行的 NTP 服务的情况下进行时间同步。

你可以在 Debian/Ubuntu 系统中使用以下命令安装 ntpdate：

```shell
apt install ntpdate
```

可以使用以下命令查询某个特定的时间服务器的 Stratum 层级、与本地时钟的偏差以及网络延迟等信息：

```shell
ntpdate -q time.ustc.edu.cn
```

如果需要手动同步时间，可以使用以下命令：

```shell
ntpdate -u time.ustc.edu.cn  
```

需要注意的是，ntpdate 并不是一个持续运行的服务，只会在每次执行时进行一次时间同步，因此如果你需要持续的时间同步功能，还需要结合其他工具（如 cron）来定期执行 ntpdate 命令。相比之下，我们推荐直接使用 systemd-timesyncd 或 chrony 来实现持续的时间同步。

## 设置时区 {#timezone}

完成时间同步后，为确保本地时间显示正确，还需要设置系统时区，例如设置为中国标准时间（东八区）：

```shell
timedatectl set-timezone Asia/Shanghai --adjust-system-clock
```

设置完时间同步服务和时区后，可使用以下命令检查系统时间、时区、以及 NTP 服务是否已启用：

```shell
timedatectl status
```
