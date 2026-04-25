---
icon: material/room-service
---

# 服务与日志管理 {#top}

!!! note "主要作者"

    [@iBug][iBug]

!!! warning "本文编写中"

现代的 Linux 发行版都使用 systemd 来管理系统服务，因此本文主要介绍 systemd 环境下的服务与日志管理，<s>Gentoo 用户请绕道</s>。

早期（2014 年以前）还有 SysVinit 和 Upstart 等，但现在已经很少见了。SysVinit 还有一个现代化的替代品，叫做 OpenRC。

## Systemd 与服务 {#systemd-and-service}

Systemd 是一大坨软件，包括服务管理（PID 1）、日志管理（systemd-journald）、网络管理（systemd-networkd）、本地 DNS 缓存（systemd-resolved）、时间同步（systemd-timesyncd）等，本文主要关心服务管理和日志管理。

### Unit

在 systemd 中，运行一个完整系统所需的每个部件都作为“单元”（unit）管理。一个 unit 可以是服务（`.service`）、挂载点（`.mount`）、设备（`.device`）、定时器（`.timer`）以至于目标（`.target`）等，完整的列表可以在 [`systemd.unit(5)`][systemd.unit.5] 中找到。

```mermaid
graph TD
U(unit) --> A(service)
U --> B(mount)
U --> C(device)
U --> D(target)
U --> E(slice)
U --> F(scope)
```

Systemd unit 的配置文件**主要**从以下目录按顺序载入，其中同名的文件只取找到的第一个：

- `/etc/systemd/system`：本地配置文件，优先级最高，这也是唯一一个管理员可以手动修改文件的地方。
- `/run/systemd/system`：运行时目录，存放由 systemd 或其他程序动态创建的 unit。注意 `/run` 目录重启后会被清空。
- `/usr/lib/systemd/system`：系统配置文件，优先级最低，一般由发行版（软件包管理器）提供。

实际会搜索的目录比这多得多（又到了看 [man][systemd.unit.5] 的时候了），但是一般只需要关心上面这三个。

很多通过 `systemctl` 命令改变的配置都会被保存到 `/etc/systemd/system` 目录下，例如：

- `systemctl enable [some-unit]` 可以“启用”一个 unit，即激活该 unit 在 `[Install]` 部分声明的自动启动条件，如 `WantedBy=` 和 `RequiredBy=` 等，以及 `Alias=`。该命令的本质是在 `/etc/systemd/system` 目录下创建软链接。

    !!! tip

        `systemctl enable --now [some-unit]` 可以在 enable 一个 unit 的同时立即启动它。

- `systemctl disable [some-unit]` 可以“禁用”一个 unit，即取消它的自动启动条件。类似地，该命令的本质是删除了上面创建的软链接。

    !!! tip

        - 同理，`systemctl disable --now [some-unit]` 可以在 disable 一个 unit 的同时立即停止它。

    !!! note "`systemctl mask`"

        有些时候，`systemctl disable` 无法满足需求，例如：

        - 对应的 unit 没有 `[Install]` 部分，因此无法被 enable/disable。
        - Unit 会被其他 unit Wants/Requires，但是又不想 disable 依赖它的 unit。

        此时可以使用 `systemctl mask`，它做的事情就是在 `/etc/systemd/system` 下，将对应的 unit 文件替换为一个指向 `/dev/null` 的软链接，从而彻底禁止该 unit 被启动。例如，在配置了自动挂载 /tmp 为 tmpfs 的系统上（`/usr/lib/systemd/system/tmp.mount`），如果不希望 /tmp 被挂载为 tmpfs，可以运行下面的命令来禁用：

        ```console
        systemctl mask tmp.mount
        ```

        由于 `tmp.mount` 没有 `[Install]` 部分，因此 `systemctl disable tmp.mount` 是无效的。

- `systemctl edit [some-unit]` 会提供一个临时文件，并在编辑完之后将其保存到 `/etc/systemd/system/[some-unit].d/override.conf` 文件中，实现对 unit 的修改。

    相比于手工修改文件，使用 `systemctl edit` 更加安全，它会检查配置文件的语法，而且不需要再额外运行 `systemctl daemon-reload`。

    !!! tip "修改可以指定多次的字段"

        Systemd unit 中有一些字段是可以指定多次的，例如下文介绍的服务的 `ExecStart=`。如果你想在 `systemctl edit` 中覆盖这些字段，那么需要先指定空值，再设置，类似下面这样：

        ```ini
        ExecStart=
        ExecStart=/your/new/command arg1 arg2
        ```

Unit 的配置文件是一个 INI 格式的文件，通常包括一个 `[Unit]` section，然后根据 unit 的类型不同有不同的 section。例如一个服务的配置文件会有 `[Service]` section，并通常会包含一个 `[Install]` section。以 cron 服务的配置文件为例：

``` { .ini title="/lib/systemd/system/cron.service" #cron.service }
[Unit]
Description=Regular background program processing daemon
Documentation=man:cron(8)
After=remote-fs.target nss-user-lookup.target

[Service]
EnvironmentFile=-/etc/default/cron
ExecStart=/usr/sbin/cron -f -P $EXTRA_OPTS
IgnoreSIGPIPE=false
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

!!! tip "查询手册"

    Unit 配置中不同的字段分布在 systemd 不同的手册页中。其中 `[Unit]` 和 `[Install]` 部分的字段可以在 [`systemd.unit(5)`][systemd.unit.5] 中找到。

    对于服务，`[Service]` 中的字段大部分在 [`systemd.service(5)`][systemd.service.5] 中，但其中与运行环境有关的会在 [`systemd.exec(5)`][systemd.exec.5] 中，与程序资源限制相关的会在 [`systemd.resource-control(5)`][systemd.resource-control.5] 中，与退出/杀死服务相关的会在 [`systemd.kill(5)`][systemd.kill.5] 中。

    对于定时器，`[Timer]` 部分的字段可以在 [`systemd.timer(5)`][systemd.timer.5] 中找到。

!!! note "Generator"

    或许你会注意到，有一些 unit 文件存储在 `/run/systemd/generator/` 下：

    ```console
    $ systemctl status home.mount
    ● home.mount - /home
        Loaded: loaded (/etc/fstab; generated)
        Active: active (mounted) since Mon 2026-04-06 09:27:46 UTC; 1 day 8h ago
    Invocation: 513aed29e7f049babe06455dbbc90087
        Where: /home
        What: /dev/vda1
        Docs: man:fstab(5)
                man:systemd-fstab-generator(8)
        Tasks: 0 (limit: 2318)
        Memory: 84K (peak: 1.7M)
            CPU: 4ms
        CGroup: /system.slice/home.mount
    $ ls /run/systemd/generator/home.mount
    /run/systemd/generator/home.mount
    ```

    这些临时生成出来的 unit 是由 [systemd.generator.5][systemd.generator.5] 生成的。Generator 程序（大部分都在 `/usr/lib/systemd/system-generators/`）会在系统启动最开始，以及重新加载配置的时候执行，生成对应的 unit。

#### 顺序与依赖 {#unit-dependency}

相比于 SysVinit（完全顺序启动）和 upstart（基于 event 触发的方式有限的并行），systemd 的每个 unit 都明确指定了依赖关系，分析依赖关系后 systemd 就可以最大化并行启动服务，这样可以大大缩短启动时间。

Systemd 中的 unit 有很多状态，大致可以归为以下几类：

- inactive：未启动
- activating：正在启动
- active：已启动（成功）
- deactivating：正在停止
- failed：启动失败

大部分系统 unit 都会使用以下几个字段：

`Wants=` 和 `Requires=`

:   指定 unit 之间的依赖关系，例如网络服务通常会依赖 `network.target`，即当网络开始配置时才会运行。
    两者都在 `[Unit]` section 中指定，区别在于 `Requires=` 是强依赖，即如果被依赖的 unit 没有启动或启动失败，那么当前 unit 也会被标记为失败，同时如果被依赖的 unit 停止，则当前 unit 也会停止；
    而 `Wants=` 是弱依赖，即尝试启动被依赖的 unit，但如果失败了也不会影响当前 unit 的启动。

`WantedBy=` 和 `RequiredBy=`

:   与上面两个相反，指定了其他 unit 依赖当前 unit。
    这两个字段在 `[Install]` section 中指定，并且仅当对应的 unit 被启用（`systemctl enable`）时才会生效。

`Before=` 和 `After=`

:   指定启动顺序，即相关的 unit 需要在前者启动完成，进入 active 状态后才会尝试启动。这两个字段在 `[Unit]` section 中指定。
    与 Wants/Requires 不同，Before/After 只是指定启动顺序，不影响依赖关系。

需要注意的是，依赖关系和启动顺序是互相独立的。如果只写 `Requires=` 或 `Wants=`，没有写 `Before=` 或 `After=`，那么 systemd 会启动依赖与被依赖的单元，但是不保证它们的启动顺序；反过来，如果只写 `Before=` 或 `After=`，那么 systemd 不保证这些服务会被启动。

!!! tip "获取某个 unit 的顺序与依赖关系"

    使用 `systemctl show [unit]` 可以查看某个 unit 的所有属性，包括上面提到的依赖关系和启动顺序。例如：

    ```console
    $ systemctl show gdm.service
    Id=gdm.service
    Names=gdm.service display-manager.service
    Requires=system.slice sysinit.target dbus.socket
    WantedBy=graphical.target
    Conflicts=getty@tty1.service shutdown.target plymouth-quit.service
    Before=graphical.target shutdown.target
    After=fwupd.service rc-local.service systemd-journald.socket sysinit.target basic.target system.slice plymouth-quit.service systemd-user-sessions.service plymouth-start.service dbus.socket getty@tty1.service
    （以下省略）
    ```

    此外使用 `systemctl list-dependencies [unit]` 可以以树状结构显示某个 unit 的依赖关系：

    ```console
    $ systemctl list-dependencies gdm.service
    gdm.service
    ● ├─dbus.socket
    ● ├─system.slice
    ● └─sysinit.target
    ●   ├─dev-hugepages.mount
    ●   ├─dev-mqueue.mount
    ●   ├─kmod-static-nodes.service
    ●   ├─ldconfig.service
    ●   ├─proc-sys-fs-binfmt_misc.automount
    ●   ├─sys-fs-fuse-connections.mount
    ●   ├─sys-kernel-config.mount
    ●   ├─sys-kernel-debug.mount
    ●   ├─sys-kernel-tracing.mount
    ●   ├─systemd-ask-password-console.path
    ●   ├─systemd-binfmt.service
    （以下省略）
    ```

!!! tip "分析系统启动时间"

    相比传统的 init，systemd 的一大卖点就是通过分析顺序与依赖，并行启动服务，从而缩短系统启动时间。可以使用 `systemd-analyze` 来绘制启动时间线：

    ```console
    systemd-analyze plot > boot.svg
    ```

    每个服务的启动时间可以使用 `blame` 子命令查看：

    ```console
    systemd-analyze blame
    ```

    不过，`systemd-analyze blame` 显示的最耗时的服务可能并不会实际影响启动。如果需要快速查看对启动时间影响最大的服务，可以查看关键路径：

    ```console
    systemd-analyze critical-chain
    ```

#### 模板 {#unit-template}

Systemd 的 unit 支持模板特性：一个 unit 文件可以实例化为多个 unit。模板 unit 的文件名（不含扩展名）结尾是 `@`，例如 `foo@.service`。用户使用时需要提供一个参数，例如 `systemctl enable --now foo@arg.service`。

在 unit 文件内部，可以使用 `%i` 和 `%I` 来引用这个参数（其中 `%I` 是没有经过转义的），例如：

```ini
[Unit]
Description=Hello for %I

[Service]
# ...
ExecStart=/usr/bin/echo Hello, %i
```

### Target

Target 是一组服务（其他 unit）的集合，通过 target 这样一层抽象可以更方便地管理服务的启动顺序，类似 SysVinit 中的 runlevel，可以理解为“系统启动目标”。
例如网络服务应该 `Requires=network-online.target` 并且 `After=network-online.target`，这样就可以保证网络服务在网络连通后再启动。

Systemd 在开机时会尝试启动 default.target，这个 target 一般是指向 graphical.target 的软链接，即启动图形界面相关的服务，另一个常见的 multi-user.target 则是命令行模式。

|  systemd target   | SysVinit runlevel | 说明                                                 |
| :---------------: | :---------------: | ---------------------------------------------------- |
|  poweroff.target  |         0         | 关机                                                 |
|   rescue.target   |         1         | 单用户模式                                           |
|      （无）       |         2         | （systemd 不使用这个 runlevel）                      |
| multi-user.target |         3         | 多用户模式，但只有命令行                             |
|      （无）       |         4         | （systemd 不使用这个 runlevel）                      |
| graphical.target  |         5         | 图形界面                                             |
|   reboot.target   |         6         | 重启                                                 |
| emergency.target  |         S         | 紧急模式                                             |
|    halt.target    |      （无）       | 系统已经停止，但是既不断电也不重启，可以看到关机日志 |

默认的 target 可以通过 `systemctl set-default` 命令修改，或者在 GRUB 中为 kernel cmdline 指定 `systemd.unit=`。
与其他 `systemctl` 命令一样，前者的本质是创建一个软链接 `/etc/systemd/system/default.target`。

### Service

Service 也就是我们最常见的服务，它的配置文件中有一个 `[Service]` section，包括了服务的启动命令和一系列其他配置。以[上面的 cron 服务](#cron.service)为例：

- `[Unit]` 部分指定的 `After=remote-fs.target nss-user-lookup.target` 表示 cron 会在系统达到这两个 target 之后才启动，即远程文件系统挂载完成和用户信息服务（`getent passwd` 等命令可用）都已经启动。
- `EnvironmentFile=-/etc/default/cron` 表示会读取 `/etc/default/cron` 文件中的环境变量。开头的 `-` 表示如果这个文件不存在，则直接忽略。
- `ExecStart=/usr/sbin/cron -f -P $EXTRA_OPTS` 指定了服务的启动命令，其中 `$EXTRA_OPTS` 是从上面的文件中读取的环境变量。

    !!! tip

        通常情况下我们建议对命令使用绝对路径，因为 systemd 启动服务时并不会使用系统配置的 `$PATH` 环境变量，而是使用一个硬编码的列表。

- `Restart=on-failure` 表示服务在失败时会自动重启。`Restart=` 的取值和含义可以在 [systemd.service][systemd.service.5#Restart=] 文档中找到。
- 最后的 `[Install]` 部分指定了服务的启动级别，即 `WantedBy=multi-user.target` 表示在多用户模式下启动。

其他常用的配置还有：

`ExecStartPre=`、`ExecStartPost=`、`ExecStopPost=`

:   在服务启动前、启动后、停止后执行的命令。可用于检查服务的配置文件是否正确、创建临时文件、清理临时文件等。例如 ssh.service 就会使用 `ExecStartPre=/usr/sbin/sshd -t` 来检查配置文件是否正确。

`ExecReload=`

:   指定重载服务的命令，一个常见的做法是 `ExecReload=/bin/kill -HUP $MAINPID`。
    配置了 `ExecReload=` 之后即可使用 `systemctl reload [service]` 命令来向服务的主进程发送 SIGHUP 信号。一些服务还有自己的 reload 命令，例如 nginx 的 `ExecReload=/usr/sbin/nginx -s reload`。

`Type=`

:   指定服务的类型。大部分服务都由一个在后台运行的进程组成，此时可以省略 Type 使用默认值 `simple`，或者更推荐的做法是 `Type=exec`。其他的服务类型参见下面的 [Service Type](#service-type) 一节。

`User=`、`Group=` 和 `SupplementaryGroups=`

:   指定运行服务的用户和组，以及额外的附加组。默认情况下服务会以 `root` 用户运行，如果有安全和权限管理的需求，那么你应该配置这几项设置。

    !!! tip

        如果你有额外的安全需求，可以参考 [Sandboxing][systemd.exec.5#Sandboxing] 一节使用 systemd 提供的高级隔离功能。可以使用 `systemd-analyze security` 命令检查整个系统的服务安全性配置情况，与单个服务的具体配置是否安全。该命令会根据服务配置计算 "exposure level" 分数，并且提供相关配置以及解释，类似如下：

        ```console
        $ systemd-analyze security --no-pager caddy.service
          NAME                                         DESCRIPTION                                  EXPOSURE
        ✗ RemoveIPC=                                   Service user may leave SysV IPC objects aro…      0.1
        ✗ RootDirectory=/RootImage=                    Service runs within the host's root directo…      0.1
        ✓ User=/DynamicUser=                           Service runs under a static non-root user i…
        ✗ CapabilityBoundingSet=~CAP_SYS_TIME          Service processes may change the system clo…      0.2
        （以下省略）
        ```

#### Service Type {#service-type}

simple 和 exec

:   是最常见的服务类型，服务主体是一个长期运行的进程。
    两者的区别在于 `simple` 类型“启动即成功”，即 `systemctl start` 会立刻成功退出；
    而 `exec` 类型会确保 `ExecStart=` 命令可以正常运行，包括 `User=` 和 `Group=` 存在、所指定的命令存在且可执行等。
    因此现代的服务应该尽量使用 `Type=exec`。

forking

:   一些传统的服务会使用这种方式，启动命令会 fork 出一个子进程然后退出，实际服务由这个子进程提供。
    这种服务需要配置 `PIDFile=`，以便 systemd 能够正确追踪服务的主进程。当 `PIDFile=` 指定的文件存在且包含一个有效的 PID 时，systemd 认为服务已经启动成功。

oneshot

:   一次性服务，即启动后运行一次 `ExecStart=` 命令，然后退出。
    这个 Type 有两种使用场景：

    1. 一次性的初始化或者清理工作、或者改变系统状态的命令等（如一些 `ip` 命令）。

        在这个场景下，你很可能也想同时设置 `RemainAfterExit=yes`，这样配置的命令执行完成后会一直保持 active 状态。

    2. 和 timer 配合使用，即定时任务。

notify 和 dbus

:   类似 `simple` 和 `exec`，但是服务会在启动完成后主动通知 systemd。
    与前面的类型不同的是，这类服务需要程序主动支持 `sd_notify` 或者 D-Bus 接口。

    ??? tip "sd_notify"

        [sd_notify(3)][sd_notify.3] 是一个非常简单的协议。Systemd 对于标注自己支持 `notify` 的服务，会通过环境变量 `NOTIFY_SOCKET` 给应用提供一个 UNIX socket 地址。应用向这个 socket 发送指定的字符串来通知 systemd 自身的状态。例如，服务完整启动之后，应用可以发送 `READY=1` 来通知 systemd 服务已经成功启动。

        通知的逻辑很简单，即使不使用 systemd 的 C 库，也可以自己手写实现，帮助文档也提供了 C 和 Python 的样例代码。值得一提的是，2024 年轰动一时的 [xz 后门事件][xz-backdoor]之所以能够影响 sshd 的逻辑，就是因为部分发行版在编译 OpenSSH 时链接了 libsystemd 来使用 `sd_notify()`，而 libsystemd 又依赖于（被植入后门的）liblzma。

  [xz-backdoor]: https://zh.wikipedia.org/wiki/XZ%E5%AE%9E%E7%94%A8%E7%A8%8B%E5%BA%8F%E5%90%8E%E9%97%A8 "维基百科：XZ 实用程序后门"

#### Socket activation {#systemd-socket}

如果你安装比较新的 Debian 或者 Ubuntu，可能会发现 ssh 服务默认启用的是 `ssh.socket`，而不是 `ssh.service`。此时 SSH 开放的 socket 由 systemd 接管，在有连接的时候才会启动同名的 `ssh.service`（如果没有启动），并且将对应 socket 的文件描述符转交给 sshd。这被称为 socket activation。

传统的 inetd（和 xinetd）做的事情和 systemd 的 socket activation 有一些相似：监听指定的端口，如果有连接进入，就启动对应的程序，并把 socket 丢给它。不过 systemd 的功能相比其强大得多。例如，相比较于 inetd 每个连接都要 fork 进程处理的方式，systemd 支持仅在第一个连接到来的时候按需启动程序，后续新连接仍然由传输的 socket 处理，而不用每次都启动新的进程（`Accept=no`）。Systemd 在服务启动后，仍然持有 socket，会定时 poll 对应的 socket，在服务退出或崩溃后重新开启服务。

Socket activation 帮助实现了服务的惰性加载，可以在不必要的情况下减小资源占用，并且提升系统启动速度。例如对 Docker，`docker.service` 如果 enable，它可能会在系统启动的关键路径上面占用几秒的时间，而如果不 enable `docker.service`，改为 enable `docker.socket`，那么就能够减小启动时间，让对应服务延迟到首次使用时开启。同时，socket activation 机制允许 systemd 预先绑定低权限用户无法绑定的低端口（小于 1024），然后在有用户访问时把 socket 交给低权限的服务进程。

当然，对 SSH，如果你想继续使用 `ssh.socket` 并且修改端口的话，就需要 `systemctl edit ssh.socket`，而不是编辑 sshd 配置了。

!!! note "应用是如何获取到自己的 socket 的？"

    Systemd 提供了两种方法：应用可以用 libsystemd 的 [sd_listen_fds(3)][sd_listen_fds.3] 函数获取到 socket 对应的文件描述符，然后直接 `accept` 或者 `recv`（根据 `Accept` 选项的不同）。

    而旧的 inetd 应用会直接从 stdin 读取 socket，向 stdout 写入 socket，此时需要在配置 `Accept=yes` 的同时，配置 `StandardInput=socket` 等参数。

??? example "使用 systemd socket 将 rsync 服务监听在 Unix domain socket 上"

    分别创建 systemd 需要的 socket unit 和模板化 service unit：

    ```ini title="/etc/systemd/system/rsync.socket"
    [Unit]
    Description=systemd socket activation for rsync

    [Socket]
    ListenStream=/run/rsyncd.sock
    Accept=yes

    [Install]
    WantedBy=sockets.target
    ```

    ```ini title="/etc/systemd/system/rsync@.service"
    [Unit]
    Description=Rsync Service
    CollectMode=inactive-or-failed

    [Service]
    Type=exec
    ExecStart=/usr/bin/rsync --daemon --no-detach --config=/etc/rsyncd.conf
    StandardInput=socket
    ```

    启用并启动其中的 socket unit：

    ```console
    systemctl enable --now rsync.socket
    ```

    此时 rsync 服务就会监听在 `/run/rsyncd.sock` 上了。

    由于 rsync 本身并没有 UDS 的支持，如果你需要进行测试的话，可以使用 socat 转发一下：

    ```shell
    socat TCP-LISTEN:873,fork UNIX-CONNECT:/run/rsyncd.sock &
    rsync rsync://localhost:873/
    ```

    将 rsync 服务监听在 UDS 的好处是可以通过文件权限来控制访问，且本地访问时不会经过防火墙等网络协议栈组件，性能会更好一些。
    例如，USTC 镜像站的 [rsync-proxy](https://github.com/ustclug/rsync-proxy) 就支持通过 UDS 和后端 rsync 服务通信。

!!! note "`Accept=yes` 与拒绝服务攻击"

    配置 `Accept=yes` 时，systemd 接受的并发连接数由 `MaxConnections=` 选项控制（默认为 64）。
    如果服务暴露在互联网等不可信环境的话，默认的连接数限制可能会导致正常用户无法使用服务。

    早期的 `ssh.socket` 对应配置为 `Accept=yes`，就导致用户无法正常连接到 SSH 的问题（可参考 [Arch Linux FS#62248](https://bugs.archlinux.org/task/62248)、[Arch Linux 移除 ssh.socket 的 commit](https://gitlab.archlinux.org/archlinux/packaging/packages/openssh/-/commit/b5ee8a935e7f3869efb16c11d2dc6356870c91da)、[Debian 切换到 `Accept=no` 的 commit](https://salsa.debian.org/ssh-team/openssh/-/commit/0dc73888bbfc17fae04b891ac0c80f35f9c44f48)）。

    如果无法切换到 `Accept=no`，那么可能需要增大最大连接数，或者利用 [fail2ban](security.md#public-service-and-login) 与[防火墙](network/firewall.md)等方式来阻止恶意的扫描影响正常服务。

!!! note "systemd-ssh-generator"

    可能出乎人意料的是，systemd 默认除了对外的 TCP 22 端口以外，还会额外 bind：

    - `/run/ssh-unix-local/socket`
    - 如果是容器里面的 systemd，且 `/run/host/unix-export/` 可以写入，那么会 bind `/run/host/unix-export/ssh`，用来让 host 能 ssh 进入容器。
    - 如果是虚拟机，会在 `AF_VSOCK` 的 22 端口也 bind 一份。`AF_VSOCK` 是一种 VM 与 host 交互的特殊 socket，相比传统的 `IP:port`，vsock 使用 `CID:port`，其中 CID 是虚拟机管理器设置的上下文 ID，对虚拟机一般从 3 开始。

    这些操作是 [systemd-ssh-generator.8][systemd-ssh-generator.8] 完成的。相关的引入原因可以参考 [Lennart Poettering 的 mastodon](https://mastodon.social/@pid_eins/112411218075942131)。

    需要特别注意的是，**[命名空间机制](./virtualization/container.md#namespace)在 Linux 的 7.0 内核之前，无法隔离 `AF_VSOCK`**。这也就意味着，如果没有设置其他的保护措施，所有虚拟机里开启的容器都可以访问到虚拟机的 SSH，同时因为有虚拟机的主机上也有 vsock 的另一端，因此主机里的容器也可以访问虚拟机的 SSH。如果虚拟机上的用户采用了弱密码，并且 SSH 允许密码登录（或者其他脆弱的场景下），恶意程序就可能会从虚拟机或者主机里的容器逃逸到虚拟机中。不过好消息是，不少容器运行时都使用 seccomp 阻止了容器内部对 vsock 的访问（例如 [moby](https://github.com/moby/moby/pull/44562)）。

    可以使用以下命令检查机器上有没有在 vsock 上监听的服务：

    ```console
    $ ss --vsock --all
    Netid      State       Recv-Q       Send-Q             Local Address:Port             Peer Address:Port      
    v_str      LISTEN      0            0                              *:22                          *:*
    ```

    不过从另一方面来说，这也给管理虚拟机带来了方便。Systemd 提供了 [systemd-ssh-proxy.1][systemd-ssh-proxy.1] 工具，用来作为 [`ProxyCommand`](../dev/ssh.md#proxy) 方便连接由 Unix socket 和 `AF_VSOCK` 暴露的 SSH 服务。Debian 的 `systemd` 包会写入 `/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf`，允许直接使用 `.host` 或 `machine/.host` 连接到本机的 SSH，使用 `unix/*`、`vsock/*`、`machine/*` 连接到 Unix socket、`AF_VSOCK` 和使用 systemd-machined（systemd 的虚拟机和容器管理器）管理的虚拟机。于是可以这样连接到启用了 vsock 功能的虚拟机上：

    ```shell
    # 可以 open /dev/vsock 后使用 ioctl IOCTL_VM_SOCKETS_GET_LOCAL_CID 获取虚拟机自己的 CID
    # 详情可阅读手册 vsock.7
    ssh user@vsock/3
    ```

    当然也可以用 `socat` 来做：

    ```shell
    ssh -o ProxyCommand="socat - VSOCK-CONNECT:3:22" user@anythingyoulike
    ```

### 定时任务 {#timers}

Systemd 提供了 timer 类型的 unit，用于定时执行任务。一个 timer unit 通常会对应一个 service unit，即在指定的时间点或者时间间隔触发 service 的启动。

相比于更常见的定时任务方案 CRON，systemd timers 具有以下优点：

- 更丰富的时间表达式，除了等价于 crontab 的 `OnCalendar=` 时间之外，也可以使用 `OnUnitActiveSec=`（服务启动后）、`OnBootSec=`（系统启动后）等指定其他时间计算方式。

    - 例如，`systemd-tmpfiles-clean.timer` 就是在系统启动后 15 分钟触发一次 `systemd-tmpfiles-clean.service`，然后每天触发一次，用于清理临时文件。

        ```ini title="/lib/systemd/system/systemd-tmpfiles-clean.timer"
        [Timer]
        OnBootSec=15min
        OnUnitActiveSec=1d
        ```

    - 如果不使用 `OnCalendar=` 的话，一般常用的模式是：使用 `OnActiveSec=`（timer 被激活后）、`OnBootSec=` 或 `OnStartupSec=`（systemd 启动后）来**首次触发**，然后使用 `OnUnitActiveSec=` 来保证**后续定时触发**。因为 `OnActiveSec=`、`OnBootSec=` 和 `OnStartupSec=` 只会触发一次服务启动，为了实现定时启动，那么就需要额外设置以服务启动后为基准的定时器，即 `OnUnitActiveSec=`。而如果没有前者的话，那么就必须要手动启动对应的服务之后，timer 才会有效。因此这一类 timer 会同时包含两个定时规则。

- 更加精确的时间控制，通过 `AccuracySec=` 可以支持秒级甚至更细的时间精度。
    一般不推荐小于 1 分钟的时间精度，否则系统计时器需要频繁唤醒，可能会影响系统性能。这一点考虑与 cron 是相同的。
- `RandomizedDelaySec=` 可以配置每次触发时随机延迟的时间，避免大量服务在同一时间点启动。
    这在使用同一份系统镜像部署大量虚拟机或类似场景下非常有用，可以避免大量计划任务同时触发，导致系统负载过高。
- `Persistent=` 可以确保如果因关机、重启等原因错过了设定时间，定时任务会在下次系统启动后会立即执行。
- 可以通过 `systemctl enable` 和 `systemctl disable` 启用和禁用定时任务，而无需修改配置文件。
    也可以使用 `systemctl status` 查看 timer 和 service 的状态，以及 `journalctl` 查看日志。
- 基于 service 而不是简单运行命令的优点：
    - 享受 service 的全部好处，如依赖管理、环境变量、自动重启等，也包括安全与隔离等高级功能。
    - 利用 service 单实例的特性，避免一个任务同时运行多份实例，即当任务已经在运行而没有结束时，不会继续启动新的进程。在 cron 中，这通常需要借助额外的工具实现，如 `flock(1)`。

Timers 的主要缺点是：

- 配置文件繁琐，一个定时任务至少需要创建两个文件，一个是 timer unit，一个是对应的 service unit。相比于在 crontab 中添加一行配置，动辄数十行的配置文件实在不够方便。
- 没有 cron 的邮件通知功能。但是 service 的输出可以记录到日志中，可以通过 `journalctl` 查看；也可以为 service 指定 `StandardOutput=` 和 `StandardError=` 手动重定向输出。

另外，第三方开发的 [systemd-cron][systemd-cron] 项目提供了一个 cron 的替代方案，它使用 systemd 的 generator 接口将 crontab 翻译成 systemd timer 和 service，然后由 systemd 负责这些 timer 和 service 的触发和运行。

  [systemd-cron]: https://github.com/systemd-cron/systemd-cron

#### 创建一个定时任务 {#create-timer}

如上所述，一个定时任务包含两个文件，一个是 timer unit，一个是对应的 service unit。下面以 certbot 的配置文件为例，说明如何创建一个定时任务。

首先创建一个 service，需要注意的是 `Type=oneshot`，并且**不能**使用 `RemainAfterExit=yes`（一般将其忽略即可，它的默认值是 no）。

```ini title="/lib/systemd/system/certbot.service"
[Unit]
Description=Certbot
Documentation=file:///usr/share/doc/python-certbot-doc/html/index.html
Documentation=https://certbot.eff.org/docs

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot -q renew
PrivateTmp=true
```

接下来创建一个 timer，指定触发时间，并按需启用 `Persistent=`。

```ini title="/lib/systemd/system/certbot.timer"
[Unit]
Description=Run certbot twice daily

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=43200
Persistent=true

[Install]
WantedBy=timers.target
```

此时 `certbot.timer` 会自动触发同名的 service，也就是 `certbot.service`。

在编辑完两个文件之后，需要运行 `systemctl daemon-reload` 使 systemd 重新加载配置文件，然后可以使用 `systemctl start certbot.timer` 启动定时器，或者使用 `systemctl enable certbot.timer` 让其开机启动。

### 临时服务 {#transient-service}

systemd 提供了临时服务的支持，可以在需要时动态创建和启动服务，而不需要事先编写 `.service` 文件，这对于一些临时任务或一次性操作非常有用。

`systemd-run` 命令可以创建临时服务。例如，以下命令会创建一个临时服务并立即启动：

```shell
systemd-run --unit=my-sleep sleep 600
```

此后，你就可以通过 `systemctl status my-sleep` 查看临时服务的状态，或者使用诸如 `systemctl stop` / `systemctl restart` 等命令管理其状态了。同时，你也可以使用 `journalctl` 命令查看进程的输出（[见下](#log)）。

默认情况下，如果临时服务的命令正常退出了，那么对应的服务会被回收，即 `systemctl status my-sleep` 将会显示 service not found。此时你仍然可以使用 `journalctl` 命令查看日志，回收服务并不会清除其运行日志。`systemd-run` 有两个参数可以改变此默认行为：

- `-r` 可以使 systemd 在进程正常退出后仍然保留服务；
- `-G` 可以使 systemd 在进程退出后立刻回收服务，即使不是正常退出（如非零的 exit code 或被信号杀死）。

同时，`systemd-run` 还有更多的参数可以用于指定服务进程的运行环境，例如工作目录和输入输出文件描述符等，具体可参考 [`systemd-run(1)`][systemd-run.1]。

基于这些讨论，本文认为 `systemd-run` 是 `nohup` 命令的全面替代品，也鼓励读者尽量使用 `systemd-run` 来运行各种一次性的后台命令，而不是使用 `nohup` 和 `&`。

作为一个常见的使用场景，普通用户需要使用 `systemd-run --user` 以运行临时的用户服务，而非系统服务。

## 日志管理 {#log}

### Systemd-journald

Journald 是 systemd 套件中负责管理日志的部分。与传统的 `/var/log/*.log` 文件不同，journald 能够处理结构化数据（例如 KV），并且将日志以二进制形式保存。因此 systemd-journald 的日志不能简单通过文本查看器（`less`、`vim` 等）查看，需要通过 `journalctl` 管理。

!!! note "为什么 journald 选择使用二进制格式？"

    传统上，Unix 系统的日志都以文本格式存储，并定时压缩、删除过期的日志。但作为中心化的日志管理服务，journald 选择了二进制格式存储日志，打破 Unix 传统，主要基于下面几点考虑：

    - 更好支持结构化日志，避免解析文本的麻烦（可以添加 `-o verbose` 参数查看结构化信息）
    - 二进制中可以添加索引，快速搜索指定时间、指定服务的日志，而不需要从头到尾遍历一遍文本
    - 允许更方便存储非文本（二进制）日志数据
    - 二进制中可以添加哈希校验，甚至签名，防止日志被恶意篡改

    当然代价是用户无法再直接使用文本编辑器，或者 `grep` 等工具直接操作分析 journald 的日志文件，需要使用 `journalctl` 工具处理。有关其设计考虑的更多细节，可以参考其[最初的设计文档](https://docs.google.com/document/u/0/d/1IC9yOXj7j6cdLLxWEBAGRL6wl97tFxgjLUEHIX3MSTs/pub)。

一些常用的选项和参数：

|    选项     | 说明                                         |
| :---------: | -------------------------------------------- |
| `-u [unit]` | 只显示指定 unit 的日志                       |
|    `-e`     | 显示最新的日志（自动将 less 跳转到末尾）     |
|    `-f`     | 实时查看日志（类似 `tail -f`）               |
|    `-x`     | 为事件显示额外的解释内容，如服务启动、停止等 |

默认情况下，journald 会将日志存储在 `/var/log/journal` 目录下，如果这个目录不存在的话，则会使用 `/run/log/journal`。由于 `/run` 目录使用 tmpfs，若配置不当可能会导致内存占用过高，且重启后日志丢失。

Journald 的配置文件位于 `/etc/systemd/journald.conf`，可以通过 [`journald.conf(5)`][journald.conf.5] 查看所有的配置项，Debian 也会在这个文件内以注释的形式提供所有配置的默认值。一些常见的配置项有：

|               配置项               | 说明                                                                   |
| :--------------------------------: | ---------------------------------------------------------------------- |
|              Storage=              | 指定日志存储方式，可以是 `auto`、`volatile`、`persistent` 和 `none`    |
|  SystemMaxUse=<br>SystemKeepFree=  | 指定系统日志（`/var/log/journal`）的最大占用空间或保证磁盘的空余空间   |
| RuntimeMaxUse=<br>RuntimeKeepFree= | 指定运行时日志（`/run/log/journal`）的最大占用空间或保证磁盘的空余空间 |
|  MaxRetentionSec=<br>MaxFileSec=   | 指定日志内容和日志文件的最大保存时间                                   |

!!! tip "避免覆盖由包管理器管理的文件"

    自 systemd v249 起（Ubuntu 22.04，Debian 12 Bookworm），所有 `/etc/systemd/*.conf` 文件均支持 `*.conf.d` 目录，即可以创建 `/etc/systemd/journald.conf.d/` 目录，并在其中创建文件来覆盖默认配置，而无需修改 `*.conf` 文件本身，使用这个方法可以避免在软件包更新或系统升级时处理配置文件的修改冲突。

    例如，要限制磁盘占用（`/var/log/journal`）为 1G，可以创建如下文件，然后重启 `systemd-journald` 服务：

    ```ini title="/etc/systemd/journald.conf.d/override.conf"
    [Journal]
    SystemMaxUse=1G
    ```

如果你需要手动清理日志，释放磁盘空间的话，可以使用 `journalctl --vacuum-size=100M` 来清理日志，journald 会删除日志，直到磁盘占用小于 100M。另外有两个类似的参数 `--vacuum-time=` 和 `--vacuum-files=10` 也可参考。

!!! note "用户程序视角：如何记录日志？"

    C 库提供了传统的 [`syslog()`][syslog.3] 函数，用来连接到 `/dev/log` 这个 Unix socket 并发送日志信息。在使用 journald 的系统上，这个 socket 由 journald 提供：

    ```console
    $ ls -l /dev/log
    lrwxrwxrwx 1 root root 28 Mar 30 22:55 /dev/log -> /run/systemd/journal/dev-log=
    ```

    而在容器场景中，容器运行时一般不会对 `/dev/log` 作特殊处理，因此如果容器内执行的程序使用了 `syslog()` 记录日志，那么就需要将 `/dev/log` 和指向的 socket 都 bind mount 进入容器，或者在容器中跑 rsyslog 或 syslog-ng。

    对脚本程序，可以使用 `logger` 记录日志：

    ```shell
    logger "hello, world!"
    ```

    libsystemd 也提供了 `sd_journal` 系列函数，允许记录结构化日志等操作。

### logrotate

按照 Unix 的“一个程序只做一件事”的设计思想，一般的程序只管将日志输出到指定地方，因此有了 logrotate 这个工具来负责非 journald 日志的“滚动”（rotate），即重命名、压缩、删除等操作。

logrotate 的全局配置文件位于 `/etc/logrotate.conf`，而每个服务的配置文件则位于 `/etc/logrotate.d/` 目录下。以 Telegraf 为例，其配置文件如下：

```shell title="/etc/logrotate.d/telegraf"
/var/log/telegraf/telegraf.log
{
    rotate 6
    daily
    missingok
    dateext
    copytruncate
    notifempty
    compress
}
```

配置文件的开头可以指定一个或多个文件（每行一个，可以使用 shell 的通配符），然后是一系列的配置项。常见的配置项有：

rotate &lt;n&gt;

:   保留的**额外**日志文件数量。例如 `rotate 6` 会保留 `example.log`、`example.log.1` 直到 `example.log.6`，而 `example.log.7` 则会直接删除。

daily / weekly / monthly / yearly

:   rotate 的频率，也许你并不需要使用后两者。

missingok / notifempty

:   特殊情况的处理方式（见这两个选项的字面含义）。

dateext / dateformat

:   使用日期作为后缀，而不是使用 `.1`、`.2` 等。另有 `dateyesterday` 选项，即使用昨天的日期来命名，保证文件名中的日期和文件内容尽可能一致。

copytruncate

:   将文件内容复制到新文件，然后清空原文件。程序需要以 `O_APPEND` 的方式打开日志文件，否则可能会造成错乱。

    适用于不支持通过 `SIGHUP` 等方式重新打开日志文件的程序。对于支持“重载日志文件”的程序，**不推荐**使用这个选项。

create &lt;mode&gt; &lt;owner&gt; &lt;group&gt;

:   创建新的日志文件时的权限和所有者。如果程序可以自己创建日志文件，那么可以忽略。

compress<br>compresscmd<br>uncompresscmd<br>compressext<br>compressoptions

:   压缩旧的日志文件，以及压缩参数（默认使用 `gzip` / `gunzip` / `.gz` / `-9`）。其中 `compress` 是开关，默认行为是 `nocompress`。

    例如，如果使用 Zstd 压缩，可以使用以下配置：

    ```shell
    compresscmd /usr/bin/zstd
    uncompresscmd /usr/bin/unzstd
    compressext .zst
    compressoptions -13 -T0
    ```

delaycompress

:   不压缩刚 rotate 出来的日志文件，即保留 `example.log` 和 `example.log.1`，压缩 `.2` 开始的日志文件<br>如果没有这个选项，那么 `example.log.1` 会被压缩

prerotate / postrotate

:   在 rotate 之前/之后执行的命令，命令块需要以 `endscript` 结束。与 Makefile / Dockerfile 等语法类似，每行为单独的一个命令，因此如果要将 `if` 等 shell 语法写成多行，需要在除了最后一行以外的每一行末尾使用反斜杠，避免被解释成多条命令。

    例如，Nginx 软件包提供的配置就会在 rotate 之后重载 Nginx：

    ```shell title="/etc/logrotate.d/nginx"
    postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1
    endscript
    ```

修改了 logrotate 的配置文件之后，可以使用 `logrotate -d /etc/logrotate.conf` 来测试配置文件的正确性，而不会真正执行任何操作。

同时由于 logrotate 不存在守护进程，而是通过 systemd timer 来定期执行的，因此修改配置文件之后不需要重启任何服务。

### rsyslog

rsyslog 和 syslog-ng 是传统的日志管理方案，尽管 journald 已经取代了它们不少功能，但是在一些场景下仍然有着重要的作用。以下介绍 rsyslog 的相关内容。

#### 与 journald 协作 {#rsyslog-with-journald}

在 Debian 12 之前，rsyslog 默认预装，用于将文本格式的日志输出到 `/var/log` 下。在 Debian 12 之后，由于 systemd-journald 会将日志存储为二进制格式（`/var/log/journal/` 下），因此 rsyslog 不再预装，避免同时写两份内容一样的东西到磁盘上。不过，Debian 12 之后的 journald 配置仍然会将日志转发到 `/run/systemd/journal/syslog`：

```ini title="/usr/lib/systemd/journald.conf.d/syslog.conf"
# Undo upstream commit 46b131574fdd7d77 for now. For details see
#  http://lists.freedesktop.org/archives/systemd-devel/2014-November/025550.html

[Journal]
ForwardToSyslog=yes
```

`/run/systemd/journal/syslog` 由 `syslog.socket` 控制，被激活时会启动 `syslog.service`。安装 rsyslog 后，`/etc/systemd/system/syslog.service` 会变成指向 `rsyslog.service` 的软链接。在激活后，rsyslog 的 [imuxsock 插件](https://docs.rsyslog.com/doc/configuration/modules/imuxsock.html#coexistence-with-systemd) 会从 systemd 获取到对应的 socket 的描述符。

在配置后，如果不希望 journald 继续记录日志（只做转发日志到 rsyslog 的中间人），直接删除 `/var/log/journal` 目录即可。这项设置由 `journald.conf` 的 `Storage=auto` 控制，在目录不存在时不会执行存储日志到磁盘的操作。

此外，rsyslog 也提供了 [`imjournal` 插件](https://docs.rsyslog.com/doc/configuration/modules/imjournal.html)，用来直接从 journald 文件获取日志，但是性能相比前述方案较差，除非需要让 rsyslog 也存储结构化日志，否则不建议使用。

#### 转发日志到其他服务器 {#rsyslog-forward-log}

虽然 journald 提供了转发到 socket 的功能（`ForwardToSocket` 配置），但是 journald 自带的转发是同步的——这意味着应用在输出日志时，需要等待 journald 转发完成，才能继续操作。如果网络环境不是非常好，对应用性能会有比较大的影响。

!!! note "systemd-journal-{upload,remote,gatewayd}"

    事实上，systemd-journal 也提供了远程通过网络传输日志的独立服务（由 `systemd-journal-remote` 包提供），其中 systemd-journal-gatewayd 提供了访问日志的 HTTP API 服务，systemd-journal-remote 运行在日志接收端，systemd-journal-upload 运行在发送端。

    但是在 Debian 下存在一个严重的问题：由于 systemd 与 TLS 相关的代码从 GnuTLS 迁移到了 OpenSSL，并且 Debian 不希望同时使用多个 TLS 库构建 systemd，因此在构建时关闭了 GnuTLS 的支持。但是 systemd-journal-remote 依赖于 [libmicrohttpd](https://www.gnu.org/software/libmicrohttpd/)，其依赖于 GnuTLS。这导致了 Debian 构建的 systemd-journal-remote 不支持 HTTPS 加密传输日志，带来了安全风险。

    详情可参考 [Debian bug #1100729](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1100729)。

以下介绍使用 rsyslog TLS 加密传输日志的相关设置，下面给出的例子中服务端有证书，客户端没有（客户端会校验服务端，但是服务端不会校验客户端），在需要高安全性的场合下，建议为客户端也生成证书。生成 CA 证书与服务端（接收端）证书的部分可参考 [nginx 一章中我们的相关介绍](./network-service/nginx.md#getting-certificates)。

TLS 传输日志一般使用 TCP 6514 端口（传统非加密的 syslog 传输使用 TCP 或 UDP 的 514 端口）。两端都需要运行 rsyslog。这里使用 GnuTLS 模块（需要安装 `rsyslog-gnutls` 包）。

服务端：

```conf title="/etc/rsyslog.d/server.conf"
global(
    DefaultNetstreamDriver="gtls"
    DefaultNetstreamDriverCAFile="/path/to/ca.crt"
    DefaultNetstreamDriverCertFile="/path/to/server.crt"
    DefaultNetstreamDriverKeyFile="/path/to/server.key"
)

module(
    load="imtcp"
    StreamDriver.Name="gtls"
    StreamDriver.Mode="1"
    # anon -- 不校验客户端
    StreamDriver.Authmode="anon"
)

input(
    type="imtcp"
    port="6514"
)

# 设置按照主机名分开的模板
template(name="PerHost" type="string"
    string="/var/log/remote/%hostname%.log"
)

if ($inputname == "imtcp") then {
    action(
        type="omfile"
        dynaFile="PerHost"
    )
    # 防止远程日志再被写入本地默认的日志文件
    stop
}
```

客户端：

```conf title="/etc/rsyslog.d/client.conf"
global(DefaultNetstreamDriverCAFile="/path/to/ca.crt")

action(
    type="omfwd"
    protocol="tcp"
    target="logserver.example.com"  # 或者 IP 地址
    port="6514"
    StreamDriver="gtls"
    StreamDriverMode="1"
    # 验证远程证书的名称
    StreamDriverAuthMode="x509/name"
    StreamDriverPermittedPeers="logserver.example.com"
)
```

## 登录管理器 {#logind}

systemd-logind 是 systemd 的登录管理器，其负责的功能包括用户 session、电源管理（例如按下电源键、笔记本电脑盒盖时的行为）等，具体可参考 [systemd-logind(8)][systemd-logind.8]。本部分主要关注在日常运维中可能会用到的一部分特性。

在登录系统时，PAM 的 `pam_systemd.so` 模块会在用户登录时创建一个 session。因此在使用 systemd 的发行版中，不管是 SSH 登录、通过 TTY 控制台登录，还是在图形界面登录，在配置正确的情况下都会创建一个 session。

`loginctl list-sessions` 可以显示当前的所有用户 session：

```console
$ loginctl list-sessions
SESSION  UID USER  SEAT  TTY
      2 1000 user  seat0

1 sessions listed.
```

`loginctl` 支持锁定（`lock-session`）、解锁（`unlock-session`）、注销（`terminate-session`）等操作。一种使用场景是：在线下的计算机类比赛中，需要限制选手只能在比赛开始后才能登录系统，在比赛结束后不能够再使用系统，此时就可以使用 `loginctl` 的功能来实现。

systemd 中每个 session 都会启动一个用户级别的 systemd 进程，用于管理用户的服务、timer 等，在 `systemctl`、`journalctl` 操作时添加 `--user` 参数即可查看当前用户的服务和日志等。

!!! note "DBus"

    `systemctl`、`journalctl` 等命令依赖于 DBus 总线与 systemd 通信。对于用户 session 来说，则依赖于 session 的 DBus 服务正常工作（一般路径为 `/run/user/<用户 PID>/bus`）。

    在命令行下需要切换用户的场合中，如果需要使用用户级别的 systemd，推荐的做法是使用以下命令：

    - `machinectl shell username@`
    - `run0`（需要很新的发行版，如 Debian 13）

    相关设计原因可阅读 [systemd/systemd#7451](https://github.com/systemd/systemd/issues/7451#issuecomment-346787237)。注意，以上方法对非 root 用户使用 polkit 鉴权，与 sudo 配置无关。

    如果需要使用 `sudo` 或 `su` 切换用户，或者在某些非常特殊的环境下，可能需要自行配置 `XDG_RUNTIME_DIR=/run/user/<用户 PID>` 与 `DBUS_SESSION_BUS_ADDRESS=/run/user/<用户 PID>/bus` 环境变量，以便 `systemctl` 等命令能够正常工作。

有些场景下，我们希望在机器启动时，用户 session 也能够创建，并且即使用户注销也不销毁。此时需要使用 lingering 的功能。使用 `loginctl enable-linger <user>` 命令即可启用。

!!! lab "限制用户的资源使用"

    用户 session 启动时，systemd 会创建 `user-<uid>.slice`。Slice 是 systemd 中用于限制资源的 unit，将多个 service 等 unit 组织在一起进行统一的资源限制。为用户限制资源使用是一个常见的需求，特别是在实验室服务器上。在用的人够多的情况下，每过几天就会有人把服务器的 CPU、内存或者 IO 全部吃满，无法操作，只能重启。

    （最常见的情况是，有人在编译软件时，跑了不限制并发的 `make -j`）

    请尝试限制让**每个**用户 CPU 最多只使用 30%，内存最多只使用 8G（可阅读 [user@.service(5)][user@.service.5]）。
