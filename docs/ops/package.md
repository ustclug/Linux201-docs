---
icon: material/package
---

# 包管理系统

!!! note "主要作者"

    [@2403772980ygy][2403772980ygy]、[@taoky][taoky]

!!! warning "本文编写中"

包管理系统是现代 Linux 发行版的重要组成部分。以下介绍与 Debian 的包管理系统相关工具，例如 APT（Advanced Package Tool）。其他发行版的包管理系统会有所不同，可参考 [Arch Linux Wiki 的 pacman/Rosetta 页面](https://wiki.archlinux.org/title/Pacman/Rosetta)。

本文假设读者了解最基础的 `apt` 使用方法，如 `apt install`, `apt remove`, `apt update`, `apt upgrade`。

## APT 常用操作 {#apt-common-operations}

Debian 有多个与软件包管理相关的工具。

其中的底层工具为 dpkg。dpkg 不负责管理软件依赖关系，只管理具体某一个包的安装、卸载等操作。因此**除非需要排查疑难问题，否则不应该直接使用 dpkg 修改系统状态**。

!!! warning "避免在安装 deb 文件时使用 dpkg"

    网络上许多教程，甚至是一些官方文档，都会建议使用 `dpkg -i` 安装 deb 文件。当 deb 存在依赖，并且系统未安装满足要求的依赖时，直接使用 `dpkg` 会导致系统依赖管理出现问题，需要额外花费精力修复。

    建议始终使用 `apt install ./path/to/package.deb` 的方式安装 deb 文件。

从用户视角来看，最常使用的工具是 apt（以及其他以 `apt-` 开头的命令）。

### 标记软件包为自动/手动安装 {#auto-manual}

绝大多数软件包都不是孤立的：它们也有自己的依赖。那么，如果安装了一个带有其他依赖的软件，然后再删除这个软件，其引入的依赖不会被自动删除，不过：

```console
# apt install x11-apps
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  bsdextrautils bsdutils fontconfig-config fonts-dejavu-core groff-base libblkid1 libbrotli1 libbsd0 libexpat1 libfontconfig1 libfreetype6 libgdbm6 libice6 libmount1
  libpipeline1 libpng16-16 libsm6 libsmartcols1 libuchardet0 libuuid1 libx11-6 libx11-data libx11-xcb1 libxau6 libxaw7 libxcb-damage0 libxcb-present0 libxcb-xfixes0 libxcb1
  libxcursor1 libxdmcp6 libxext6 libxfixes3 libxft2 libxi6 libxkbfile1 libxmu6 libxmuu1 libxpm4 libxrender1 libxt6 man-db mount util-linux util-linux-extra x11-common
  xbitmaps
Suggested packages:
  groff gdbm-l10n cryptsetup-bin apparmor less www-browser nfs-common dosfstools kbd util-linux-locales mesa-utils
Recommended packages:
  uuid-runtime sensible-utils
The following NEW packages will be installed:
  bsdextrautils fontconfig-config fonts-dejavu-core groff-base libbrotli1 libbsd0 libexpat1 libfontconfig1 libfreetype6 libgdbm6 libice6 libpipeline1 libpng16-16 libsm6
  libuchardet0 libx11-6 libx11-data libx11-xcb1 libxau6 libxaw7 libxcb-damage0 libxcb-present0 libxcb-xfixes0 libxcb1 libxcursor1 libxdmcp6 libxext6 libxfixes3 libxft2
  libxi6 libxkbfile1 libxmu6 libxmuu1 libxpm4 libxrender1 libxt6 man-db x11-apps x11-common xbitmaps
The following packages will be upgraded:
  bsdutils libblkid1 libmount1 libsmartcols1 libuuid1 mount util-linux util-linux-extra
8 upgraded, 40 newly installed, 0 to remove and 4 not upgraded.
（以下省略）
# apt remove x11-apps
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following packages were automatically installed and are no longer required:
  fontconfig-config fonts-dejavu-core groff-base libbrotli1 libbsd0 libexpat1 libfontconfig1 libfreetype6 libgdbm6 libice6 libpipeline1 libpng16-16 libsm6 libuchardet0
  libx11-6 libx11-data libx11-xcb1 libxau6 libxaw7 libxcb-damage0 libxcb-present0 libxcb-xfixes0 libxcb1 libxcursor1 libxdmcp6 libxext6 libxfixes3 libxft2 libxi6
  libxkbfile1 libxmu6 libxmuu1 libxpm4 libxrender1 libxt6 man-db x11-common xbitmaps
Use 'apt autoremove' to remove them.
The following packages will be REMOVED:
  x11-apps
0 upgraded, 0 newly installed, 1 to remove and 4 not upgraded.
```

可以发现，虽然 `x11-apps` 在该环境中引入的依赖没有被自动删除，但是 APT 知道哪些依赖是不再被需要的了。这有赖于 APT 的软件包标记功能：用户直接安装的包会被标记为手动安装（manual），而被这样引入的依赖会被标记为自动安装（automatic）。于是，没有被任何手动安装的包直接以及间接依赖的自动安装的包就可以被 `apt autoremove` 移除。

`apt-mark` 命令可以显示、修改标记：

- `apt-mark showauto` 与 `apt-mark showmanual` 可以显示系统中被标记为自动安装与手动安装的包。
- `apt-mark auto <package>` 与 `apt-mark manual <package>` 可以修改包的标记。

### 推荐与建议 {#recommends-suggests}

安装软件包时，APT 在默认配置下会安装推荐（Recommended）的包。建议（Suggested）的包会显示在安装界面，但是不会自动被安装。例如在 Debian 12 中，[docker.io 包](https://packages.debian.org/bookworm/docker.io)的推荐有 apparmor、ca-certificates 等，建议包有 btrfs-progs、debootstrap 等。那么在安装 `docker.io` 时，包括 apparmor、ca-certificates 等包就会默认被安装，并且用户也可以看到这些包建议，并且可以在当前包安装完成后自行安装。

大部分情况下，被设置为「推荐」的包是有意义的，如果不安装，可能程序仍然可以运行，但是会缺失一些重要的功能。不过在某些环境下，例如容器场景，我们需要安装的包尽可能得少。为了精简安装的软件包，可以使用 `--no-install-recommends` 的选项，以跳过推荐的软件包。还可以在 [`apt.conf`][apt.conf.5] 配置中添加 `Apt::Install-Recommends "false"` 以使默认配置不会安装推荐的包。

!!! tip "使用 `.conf.d` 目录形式，避免直接修改 `.conf` 配置文件"

    对于绝大多数 Debian 包来说，软件包对应的配置文件（以下称为 `.conf` 文件）是直接由软件包安装（管理）的。尽管直接修改配置也可以达到目的，但是在软件包升级，特别是系统大版本更新时，`apt` 会要求用户手工介入配置冲突问题（保留原配置，或者安装新配置），会带来一些困扰。

    目前大部分软件包的配置文件都支持 `.conf.d` 目录形式，允许用户以不同文件的形式添加自己的配置片段，对应的程序会「导入」这些配置。这种方式不仅可以避免直接修改软件包的配置文件，还可以更好地管理配置文件（例如，用户可以将不同目的的配置以不同的文件名存储，提升配置的可维护性）。

    以上文的 `apt.conf` 为例，这里推荐的做法是在 `/etc/apt/apt.conf.d/` 目录下创建一个新的 `.conf` 文件，在其中写入需要的配置，例如不安装推荐包：

    ```shell
    echo 'APT::Install-Recommends "false";' | sudo tee /etc/apt/apt.conf.d/99no-install-recommends
    ```

    某些软件会根据文件名的字典序来决定配置的优先级，因此这里使用 `99` 作为前缀，确保这个配置文件在其他配置文件之后被读取。

### 搜索包 {#search}

Debian 与 Ubuntu 均提供了网页端搜索软件包的服务：[Debian 软件包](https://packages.debian.org/)、[Ubuntu Packages Search](https://packages.ubuntu.com/)。不过，使用 apt 工具搜索来快得多。

#### `apt search` 与 apt 搜索模式 {#apt-search-pattern}

`apt search <name>` 会根据包名与描述进行包的查找，支持正则表达式：

```console
$ apt search wayland
Sorting... Done
Full Text Search... Done
bemenu/noble 0.6.15+dfsg-1build2 amd64
  Dynamic menu inspired by dmenu

cage/noble 0.1.5+20240127-2build1 amd64
  Kiosk compositor for Wayland
（以下省略）
$ apt search ^docker
Sorting... Done
Full Text Search... Done
debocker/noble 0.2.5 all
  docker-powered package builder for Debian

docker-buildx/noble-updates 0.14.1-0ubuntu1~24.04.1 amd64
  Docker CLI plugin for extended build capabilities with BuildKit
（以下省略）
```

不过，有些时候这种搜索也不太符合需求，例如有些时候我们只想搜索包名等，此时可以使用 apt 搜索模式（search pattern）来进行更具体的查找。完整文档可以参考 [apt-patterns(7)][apt-patterns.7]。搜索模式不适用于 `apt search`，但适用于其他各类 apt 命令，例如 `apt list`、`apt show`、`apt remove` 等。

以下是一些常见的 apt 搜索模式，句尾括号为更加繁琐的完整表示：

- `~nREGEX` 包名称满足正则表达式的包（`?name(REGEX)`）。
- `~c` 已经删除，但是仍然有配置残留的包，可以使用 `apt purge` 彻底删除（`?config-files`）。
- `~i` 为已经安装的包（`?installed`）。
- `~U` 可以升级的包（`?upgradable`）。
- `~o` 远程已经不再存在的包，一般是在系统大版本更新后残留的旧包，或者是本地手动安装的包（`?obsolete`）。

!!! question "搜索模式练习"

    请尝试写出以下查询的搜索模式，并且在自己的环境中试一试：

    - 输出（提示：`apt list`）所有未完全删除以及远程仓库不再提供的包（虽然 `apt purge` 也支持搜索模式，小心执行，因为所有配置都会被删除！）
    - 输出本地安装的名字里有 `top` 的所有包
        - 提示：可以像这样要求同时满足多个 pattern: `apt list 'P1 P2 P3'`

#### 文件搜索：`apt-file` {#apt-file}

如果使用过默认安装的 Ubuntu 的话，可能会发现，在输入命令时，如果命令不存在，会有类似下面的提示：

```console
$ htop
Command 'htop' not found, but can be installed with:
sudo apt install htop
```

这是由 `command-not-found` 包支持的，不过可以注意到，这一项功能会拖慢与 shell 交互时的速度，因此这里更加推荐删除这个包，只在需要的时候用 `apt-file` 命令搜索。

在操作前，需要执行 `apt-file update` 命令更新本地文件与包关系的数据库的初始化及更新。之后使用 `apt-file search <file>` 就可以搜索包含某个文件的包：

```console
$ apt-file search execsnoop
bpfcc-tools: /usr/sbin/execsnoop-bpfcc
bpfcc-tools: /usr/share/doc/bpfcc-tools/examples/doc/execsnoop_example.txt
bpfcc-tools: /usr/share/man/man8/execsnoop-bpfcc.8.gz
bpftrace: /usr/sbin/execsnoop.bt
bpftrace: /usr/share/doc/bpftrace/examples/execsnoop_example.txt
bpftrace: /usr/share/man/man8/execsnoop.bt.8.gz
golang-github-iovisor-gobpf-dev: /usr/share/gocode/src/github.com/iovisor/gobpf/examples/bcc/execsnoop/execsnoop.go
golang-github-iovisor-gobpf-dev: /usr/share/gocode/src/github.com/iovisor/gobpf/examples/bcc/execsnoop/output.go
libbpf-tools: /usr/sbin/execsnoop
pcp: /usr/lib/pcp/pmdas/bcc/modules/execsnoop.bpf
pcp: /usr/lib/pcp/pmdas/bcc/modules/execsnoop.python
pcp: /usr/lib/pcp/pmdas/bpf/modules/execsnoop.so
pcp: /usr/share/pcp/htop/screens/execsnoop
pcp: /var/lib/pcp/pmdas/bcc/modules/execsnoop.bpf
pcp: /var/lib/pcp/pmdas/bcc/modules/execsnoop.python
pcp: /var/lib/pcp/pmdas/bpf/modules/execsnoop.so
perf-tools-unstable: /usr/sbin/execsnoop-perf
perf-tools-unstable: /usr/share/doc/perf-tools-unstable/examples/execsnoop_example.txt
perf-tools-unstable: /usr/share/man/man8/execsnoop-perf.8.gz
systemtap-doc: /usr/share/systemtap/examples/lwtools/execsnoop-nd.8
systemtap-doc: /usr/share/systemtap/examples/lwtools/execsnoop-nd.meta
systemtap-doc: /usr/share/systemtap/examples/lwtools/execsnoop-nd.stp
systemtap-doc: /usr/share/systemtap/examples/lwtools/execsnoop-nd_example.txt
```

此外，`apt-file list <package>` 可以查看某个包中包含的文件：

```console
$ apt-file list htop
htop: /usr/bin/htop
htop: /usr/share/applications/htop.desktop
htop: /usr/share/doc/htop/AUTHORS
htop: /usr/share/doc/htop/README.gz
htop: /usr/share/doc/htop/changelog.Debian.gz
htop: /usr/share/doc/htop/copyright
htop: /usr/share/icons/hicolor/scalable/apps/htop.svg
htop: /usr/share/man/man1/htop.1.gz
htop: /usr/share/pixmaps/htop.png
```

!!! tip "使用 dpkg 类命令在**已安装的包**内查找文件"

    `apt-file` 依赖于对完整仓库的索引，并且搜索也是一个略微耗时的过程。如果只需要确认本地已经安装的包，以及已有的 deb 包文件中的文件情况，有更快的方法：

    - `dpkg -S <file>` 可以查找所有已安装包中的文件。
    - `dpkg-deb -c <name_version.deb>` 可以查看 `.deb` 文件中的内容。
    - `dpkg-query -L <name>` 查看给定的安装了的包提供了哪些文件。

### 固定包 {#hold}

有时我们希望固定一个包，使得这个包不会被改变或升级：一个例子是，我们自行打包了某个有 bug 的包的修复版本，同时不希望系统自动升级到官方的版本。这时可以使用 `apt-mark hold <name>` 来标记这个包为固定的。

`apt-mark unhold` 可以取消固定，而 `apt-mark showhold` 可以查看所有被固定的包。

### 自动更新 {#unattended-upgrade}

一般而言，使用 apt 的系统默认安装了 `unattended-upgrades` 包，如果系统上没有，安装该包即可。一些 Debian 系统镜像在预配置阶段会关闭自动更新，这可以通过以下命令确认：

```sh
debconf-get-selections | grep unattended-upgrades/enable_auto_updates
```

如果输出的内容类似下面：

```console
unattended-upgrades	unattended-upgrades/enable_auto_updates	boolean	false
```

则代表自动更新被关闭，反之则启用。可以执行 `dpkg-reconfigure unattended-upgrades` 修改配置。当自动更新启用时，`/etc/apt/apt.conf.d/20auto-upgrades` 文件应当存在。

可以使用以下命令：

```sh
sudo unattended-upgrades --dry-run --debug
```

查看并确认系统自动更新时的行为。默认情况下，自动更新只会操作 Debian 官方上游的包，用户自己设置的源不会被自动更新，这一点可以在 `/etc/apt/apt.conf.d/50unattended-upgrades` 文件中验证：

```apt.conf
// Automatically upgrade packages from these (origin:archive) pairs
//
// Note that in Ubuntu security updates may pull in new dependencies
// from non-security sources (e.g. chromium). By allowing the release
// pocket these get automatically pulled in.
Unattended-Upgrade::Allowed-Origins {
	"${distro_id}:${distro_codename}";
	"${distro_id}:${distro_codename}-security";
	// Extended Security Maintenance; doesn't necessarily exist for
	// every release and this system may not have it installed, but if
	// available, the policy for updates is such that unattended-upgrades
	// should also install from here by default.
	"${distro_id}ESMApps:${distro_codename}-apps-security";
	"${distro_id}ESM:${distro_codename}-infra-security";
//	"${distro_id}:${distro_codename}-updates";
//	"${distro_id}:${distro_codename}-proposed";
//	"${distro_id}:${distro_codename}-backports";
};
```

此外，systemd 服务 `unattended-upgrades.service` 会确保系统在关机或重启前正确进行软件包升级的收尾工作。因此也需要确认该服务已启动并会开机自启。

### APT 前端 {#apt-frontend}

APT 面向用户使用的前端除了 `apt` 以外，还有 `apt-get`、`aptitude` 和 `synaptic` 等。其中 `apt-get` 是早期的 Debian 的包管理工具，基础功能与 `apt` 类似（如 `apt-get update`、`apt-get install` 等），但是用户体验不如 `apt` 友好，由于其交互界面不再变化，因此仅适用于需要使用脚本交互的场景；`synaptic` 是图形界面的包管理工具（中文名为「新立得软件包管理器」）。

![Synaptic](../images/synaptic.png)

Ubuntu 24.04 下的新立得软件包管理器截图
{: .caption }

`aptitude` 提供了 TUI 界面的包管理功能，不过对于运维的场景下，其更加重要的是相比于 `apt` 更灵活的依赖解析功能。在系统出现损坏包的情况下，`apt` 可能无法提供有效的解决方案，而 `aptitude` 会计算出多种解法，并且提供给用户选择。

### 完整性校验 {#verify}

dpkg 可以对已经安装的包进行完整性校验。`dpkg --verify <name>` 可以校验已经安装的包的完整性，可以省略 `<name>` 选项，以对于所有包进行检查。如果怀疑软件包文件因意外被破坏（例如在升级时断电，或误删除等），可以使用该命令确认哪些软件包需要重新安装。

!!! example "检查某系统强制重启后无法开机的问题"

    一个现实发生的例子是，某系统强制重启后无法正常开机，提示：

    ```console
    [    4.634427] systemd[1]: Assertion 'close_nointr(fd) != -EBADF' failed at src/basic/fd-util.c:77, function safe_close(). Aborting.
    [    4.635043] systemd[1]: Caught <ABRT> from our own process.
    [    4.635624] systemd[1]: Caught <ABRT>, core dump failed (child 225, code=killed, status=6/ABRT).
    [    4.635750] systemd[1]: Freezing execution.
    ```

    使用 ISO 引导后 `chroot` 到系统，执行 `dpkg --verify`，发现：

    ```console
    # dpkg --verify
    （省略）
    ??5??????   /usr/lib/x86_64-linux-gnu/systemd/libsystemd-core-252.so
    ```

    重新安装 `libsystemd-shared` 包后，问题解决。

`dpkg --verify` 默认输出为 `rpm -V` 风格，类似如下：

```rpm
??5??????   /some/file
??5?????? c /some/config_file
missing     /some/missing_file
```

`dpkg` 目前只会检查文件的 MD5（即上面的 `5`），因此其他列均标记为 `?`（未检查）。`c` 代表是配置文件，`missing` 代表文件不存在。

!!! warning "`dpkg --verify` 不是为安全性用途设计的"

    如果怀疑攻击者已经有对应机器的 root 权限，那么 `dpkg --verify` 的结果是不可信的，因为攻击者可以修改 `dpkg` 本身，或者修改本地的包数据库。

### 软件优先级 {#priority}

有时候，我们会设置多个不同的源，而这些源会提供相同名称的软件包，例如：

- 正常安装的系统中，security 源提供了一些主源已有的软件包的，包含安全修复的更新版本。
- 在 stable 版本的 Debian 中添加 [backports](https://backports.debian.org/) 源，以获取一些来自 testing 的，在 stable 下重新编译的新版本的软件包。
- Ubuntu 源中的 `firefox` 为 Snap 包，而来自 Mozilla 的 APT 仓库的 `firefox` 为原生的 deb 包（[Mozilla 的帮助信息](https://support.mozilla.org/en-US/kb/install-firefox-linux#w_install-firefox-deb-package-for-debian-based-distributions-recommended)）。

APT 选择包的逻辑并非单纯的「版本越新越好」（比如，用户添加 backports 源**不代表**用户希望所有 backports 有的软件都安装最新版本），而是根据优先级来选择。默认的优先级为 500，如果优先级一致，才会根据版本号来选择。

Backports 源的优先级为 100，因为其 `Release` 文件中 `NotAutomatic` 和 `ButAutomaticUpgrades` 字段都为 `yes`，[因此 APT 会授予 backports 100 的优先级](https://wiki.debian.org/DebianRepository/Format#NotAutomatic_and_ButAutomaticUpgrades)。如果只有 `NotAutomatic` 为 `yes`，则优先级为 1。

我们通过 `apt-cache policy <name>` 查看包的安装状态与优先级信息，以某配置了 backports、[deb-multimedia](https://deb-multimedia.org/)，并且有一段时间未升级的系统为例：

```console
$ apt-cache policy yt-dlp
yt-dlp:
  Installed: 1:2024.10.07-dmo1
  Candidate: 1:2025.01.26-dmo1
  Version table:
     1:2025.01.26-dmo1 500
        500 http://mirrors.ustc.edu.cn/deb-multimedia bookworm/main amd64 Packages
 *** 1:2024.10.07-dmo1 100
        100 /var/lib/dpkg/status
     2025.01.26-1~bpo12+1 100
        100 http://mirrors.ustc.edu.cn/debian bookworm-backports/main amd64 Packages
     2023.03.04-1 500
        500 http://mirrors.ustc.edu.cn/debian bookworm/main amd64 Packages
```

可以看到，APT 已知四个不同的 `yt-dlp` 版本，分别是 deb-multimedia 的 `1:2025.01.26-dmo1`、本地安装的 `1:2024.10.07-dmo1`、backports 的 `2025.01.26-1~bpo12+1` 以及官方源的 `2023.03.04-1`。特别地，本地的版本的优先级为 100。因此当执行更新命令时，APT 会首先选择优先级最高的（`deb-multimedia` 或者官方源），然后选择版本最高的（`1:2025.01.26-dmo1`）。

如果需要指定从某个特定的源安装软件包，可以使用 `-t` 选项，例如：

```sh
apt install -t bookworm-backports yt-dlp
```

这样就会安装 backports 源中的 `yt-dlp`。其实际上是把 `bookworm-backports` 源的优先级临时拉高到了 990：

```console
$ apt-cache policy -t bookworm-backports yt-dlp
yt-dlp:
  Installed: 1:2024.10.07-dmo1
  Candidate: 1:2025.01.26-dmo1
  Version table:
     1:2025.01.26-dmo1 500
        500 http://mirrors.ustc.edu.cn/deb-multimedia bookworm/main amd64 Packages
 *** 1:2024.10.07-dmo1 100
        100 /var/lib/dpkg/status
     2025.01.26-1~bpo12+1 990
        990 http://mirrors.ustc.edu.cn/debian bookworm-backports/main amd64 Packages
     2023.03.04-1 500
        500 http://mirrors.ustc.edu.cn/debian bookworm/main amd64 Packages
```

用户也可以手动配置软件的优先级，相关配置位于 `/etc/apt/preferences` 和 `/etc/apt/preferences.d/` 中。优先级配置条目的一般格式如下：

```yaml
Package: <name>
Pin: <clause>
Pin-Priority: <priority>
```

例如：

```yaml
Package: *
Pin: origin packages.mozilla.org
Pin-Priority: 1000
```

那么在安装所有 packages.mozilla.org 的包的时候，都会被优先选择。优先级系统也可以用来固定包，例如将 `mtr-tiny` 包固定在 0.87 版本：

```yaml
Package: mtr-tiny
Pin: version 0.87*
Pin-Priority: 1000
```

详细文档请参考 [apt_preferences(5)][apt_preferences.5]。

## DEB 软件包 {#deb-package}

### 软件包结构 {#deb-structure}

Deb 包是一个 ar 格式的包，包含三个文件（可以使用 `ar t` 查看，`ar x` 解压）：

- `debian-binary`：包含版本号的文本文件，目前版本为 `2.0`。
- `control.tar.xz`（或 `control.tar.zst` 等）：包含软件包的元数据，例如软件包的依赖、描述、安装脚本等。
- `data.tar.xz`（或 `data.tar.zst` 等）：包含软件包的实际文件。

!!! note "ar 与 tar"

    ar 格式（1971）与 tar（1979）类似，都是归档格式。由于 ar 不支持目录，因此目前 ar 仅用于生成静态链接库（`.a` 文件）与 deb 包。

`control.tar.xz` 中的 `control` 文件是包的元数据，包含版本、依赖、描述、维护者等等信息，类似如下：

```control
Package: sudo
Version: 1.9.9-1ubuntu2.3
Architecture: amd64
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Installed-Size: 2504
Depends: libaudit1 (>= 1:2.2.1), libc6 (>= 2.34), libpam0g (>= 0.99.7.1), libselinux1 (>= 3.1~), zlib1g (>= 1:1.2.0.2), libpam-modules, lsb-base
Conflicts: sudo-ldap
Replaces: sudo-ldap
Section: admin
Priority: optional
Homepage: https://www.sudo.ws/
Description: Provide limited super user privileges to specific users
 Sudo is a program designed to allow a sysadmin to give limited root
 privileges to users and log root activity.  The basic philosophy is to give
 as few privileges as possible but still allow people to get their work done.
 .
 This version is built with minimal shared library dependencies, use the
 sudo-ldap package instead if you need LDAP support for sudoers.
Original-Maintainer: Sudo Maintainers <sudo@packages.debian.org>
```

此外，`control.tar.xz` 可以包含一些 hook 脚本，在安装与删除前后进行操作，包括 `preinst`, `prerm`, `postinst`, `postrm`。还可以包含以下文件：

- `md5sums`，用于校验包文件的完整性。
- `conffiles`，标志包安装的哪些文件是配置文件。
- `shlibs`，如果软件包包含了动态库（`.so`），那么这个文件就需要包含库的版本信息，以帮助其他软件包解决相关的依赖问题。
- `triggers`，定义了软件包感兴趣（interest）的触发器，以及软件包状态变化时会触发（activate）的触发器。

### 获取软件包源码 {#apt-source}

Debian 目前大多数的包的源代码都可以在 Debian Salsa GitLab 上找到，可以在 [Debian Package Tracker](https://tracker.debian.org/) 上找到相关信息。

除了直接使用 git clone 之外，还可以使用 `apt source <package>` 来下载源码。需要注意的是，该功能需要安装 `dpkg-dev`，且需要在 `/etc/apt/sources.list` 或 `/etc/apt/sources.list.d/debian.sources` 中添加 `deb-src`，类似于这样：

```debsources
deb-src http://deb.debian.org/debian/ bookworm main
```

或者这样（DEB822）：

```yaml
Types: deb deb-src
URIs: http://deb.debian.org/debian/
Suites: bookworm
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
```

!!! tip "DEB822"

    DEB822 是 Debian 新的仓库配置格式，用于取代旧的 `sources.list` 格式（又被称为 One-Line-Style 格式）。详情可阅读 <https://repolib.readthedocs.io/en/latest/deb822-format.html>。

`apt source` 会下载必要的文件、解压并应用 Debian 的补丁：

```shell
$ apt source sudo
Reading package lists... Done
NOTICE: 'sudo' packaging is maintained in the 'Git' version control system at:
https://salsa.debian.org/sudo-team/sudo.git
Please use:
git clone https://salsa.debian.org/sudo-team/sudo.git
to retrieve the latest (possibly unreleased) updates to the package.
Skipping already downloaded file 'sudo_1.9.13p3-1+deb12u1.dsc'
Skipping already downloaded file 'sudo_1.9.13p3.orig.tar.gz'
Skipping already downloaded file 'sudo_1.9.13p3.orig.tar.gz.asc'
Skipping already downloaded file 'sudo_1.9.13p3-1+deb12u1.debian.tar.xz'
Need to get 0 B of source archives.
dpkg-source: info: extracting sudo in sudo-1.9.13p3
dpkg-source: info: unpacking sudo_1.9.13p3.orig.tar.gz
dpkg-source: info: unpacking sudo_1.9.13p3-1+deb12u1.debian.tar.xz
dpkg-source: info: using patch list from debian/patches/series
dpkg-source: info: applying debian-bug-1039557
dpkg-source: info: applying paths-in-samples.diff
dpkg-source: info: applying Whitelist-DPKG_COLORS-environment-variable.diff
dpkg-source: info: applying sudo-ldap-docs
```

<!-- 有时，默认的编译设置并不满足实际的需求，有时，我们需要一些软件包的更新版本，但是这些版本的依赖难以满足，这时，我们可能可以尝试自己编译一个包。

一般而言，使用 apt 可以获得一些软件包的源码。

首先，添加源码源，添加方法参考[Debian - USTC Mirror help](https://mirrors.ustc.edu.cn/help/debian.html#__tabbed_1_2)

通过 `apt source <package>` 获得源码。

源码将被在当前文件夹下载并解压。

### 修改源码

对源码进行简单的修改，你可以修改编译选项以开启额外功能。

如果额外功能需要更多依赖，需要修改下载的 `.dsc` 文件与 `source/debian/control`，添加对应的依赖。

在源码目录下使用

```sh
dch --local +<changed_proc>
```

来自动生成版本号并且修改 changelogs

### 编译修改后的源代码

运行

```sh
dpkg-buildpackage -us -uc
```

以编译源代码并生成安装包。 -->

## 软件源 {#repo}

### 目录结构

### 构建一个自己的 DEB 软件源

<!-- 可参考 https://github.com/USTC-vlab/deb -->

<!-- DEB 软件包的结构 -->
<!-- 如何从已有的 DEB 源码包打自己的 patch 并重新打包 -->
<!-- 如何为第三方软件打包 -->

<!-- ------ -->
<!-- 在 Linux 系统中往往有一些系统负责软件的安装，升级，卸载。这个系统被称作包管理器（Package Manager）。

包管理器的范畴较广：管理系统的，比如 apt，zypper；管理环境的，比如 conda；管理语言包的，比如 pip，gem；有一些包管理器甚至是语言的“附属”，如 cargo

本文将着重讲解 Debian 的包管理器。

Debian 的包管理器是 APT（**A**dvanced **p**ackage **t**ool）& dpkg 其中，dpkg 负责中低层操作，包括.deb 包的安装，卸载，以及信息查询，dpkg 还可以检查依赖的安装情况。

APT 主要功能是解析包的依赖信息，从线上（或线下）的软件仓库（repository）下载（离线下载）.deb 软件包，然后按照合理的顺序调用 `dpkg`，在必要时使用 `--force`。

## dpkg 安装一个包（.deb）的过程

!!! warning "请勿手动安装包"
    在生产环境中，请使用 apt 安装 deb 包。本部分仅用于展示 dpkg 实际完成的工作。

在这一段中，可以自己手操（其实建议不要）安装若干包，这里以 `apt-utils` 为例进行演示，这个包的依赖在 debian 环境中应当已经被配置完成。

1. 准备工作：获得 `apt-utils` 的下载地址，并且在系统中下载。创建 /tmp/install-temp 文件夹。

    ```bash
    cd /tmp
    mkdir install-temp
    cd install-temp
    wget http://ftp.cn.debian.org/debian/pool/main/a/apt/apt-utils_2.7.12_amd64.deb

    # 可以观察包的内容
    # dpkg -c apt-utils_2.7.12_amd64.deb
    # apt-file list apt-utils # 这个命令位于 apt-file 包中
    ```

2. 解包

    ```bash
    ar -x apt-utils_2.7.12_amd64.deb

    # 可以使用以下命令代替

    dpkg-deb -R apt-utils_2.7.12_amd64.deb .

    # 注意两者结果不同，可以尝试并且观察区别
    ```

3. 移动文件

    将文件移动至其安装位置，该包结构十分简单，可以直接操作。

    这个过程其实包含在解包中。

    ```bash
    sudo tar xpvf data.tar.xf --directory=/

    # 或者......

    sudo rsync -av usr /
    ```

4. 在 dpkg 的辅助文件中修改为已安装

    复制 control.tar.xz 中的 control，并添加到/var/lib/dpkg/status 中的合适位置，添加 Status 行目

    将 control.tar.xz 中的 md5sum 移动到/var/lib/dpkg/list/包名.md5sum

    ```bash
    tar tf /tmp/install-temp/data.tar.xz | sed -e 's/^.//' -e 's/^\/$/\/\./' > /var/lib/dpkg/list/包名.list
    ```

    这个包的结构十分简单，仅作参考用，大多数的包包含 preinst，postinst，conffiles，prerm，postrm 等附加属性，安装过程步骤比该例复杂很多，因此请慎重（不要）使用以上步骤！尽可能使用 dpkg 等工具进行包的操作。

## 配置文件与辅助文件

`dpkg` 的配置文件位于 `/etc/dpkg/`，辅助文件位于 `/var/lib/dpkg/`。

APT 的配置文件位于 `/etc/apt`，辅助文件位于 `/var/lib/apt`。

可以观察 `/var/lib/apt/lists` 中的文件作为参考

TODO

## 重要而不常见的功能

TODO -->

<!-- ### 理解 apt 基本目录结构

apt 的工作依赖于一些文件，理解这些文件（与目录）的作用有助于更好的理解其工作原理。

#### `/etc/apt/sources.list` 与 `/etc/apt/sources.list.d/`

这些文件声明 apt 的软件源，在进行 `apt update` 这类操作时，会从这些软件源下载 metadata 并且进行缓存。

这些 metadata 包括软件源里所有包的基本信息，例如包名称，每个包的依赖，推荐与建议包，开发者与维护者等等。

#### `/etc/apt/apt.conf` 与 `/etc/apt/apt.conf.d/`

这些文件是 apt（以及其拓展）使用的配置文件。

对于 apt.conf.d 里面的文件，其优先级由字典序决定。一般在文件前添加数字代表优先级，数字更大者读取越靠后，因而优先级更高。
apt.conf 最后被读取，拥有最高的优先级。

#### `/var/lib/apt/lists`

我们之前提到的 metadata 的储存位置。

需要注意的是，metadata 不止和软件源包含什么有关。

使用 apt-cache 工具查询相关信息。

例子：

使用 apt-cache 查看软件包相关 metadata

```sh
apt-cache show <name>
```

使用 apt-cache 查看软件包的依赖和反向依赖

```sh
apt-cache depends <name>
apt-cache rdepends <name>
```

检查未被满足的依赖，用来修复一些依赖地狱问题

```sh
apt-cache unmet
```

#### `/var/lib/dpkg/available`

dpkg 的数据库，结构与 apt 相似，在现在随着 dpkg 本身的使用逐渐减少，已经基本停止使用。

#### `/var/lib/dpkg/status`

dpkg 的状态列表，相较于纯粹的 metadata，其添加了优先级和状态，去除了校验值。

一般这里包含安装结束的包与部分安装的包。

#### `/var/lib/dpkg/info`

所有包的管理相关信息，例如包内文件的 md5sum 值，库包的符号列表，安装和卸载时需要的额外操作等等。

#### `/var/lib/apt/extended_states`

记录已经安装的包的类型：自动安装或者手动安装的。

一般而言列表中的包都是自动安装的。

在进行 `apt autoremove` 时用于判定是否要卸载，如果一个包没有被其他手动安装的包（直接或间接）依赖并且是自动安装的，那么其会被移除。

通过 `apt-mark auto <name>` 和 `apt-mark manual <name>` 进行修改。

#### `/etc/apt/preferences` 与 `/etc/apt/preferences.d/`

apt 优先级的配置文件

apt 在遇到相同软件包时，会选择优先级最高的安装包进行安装。在拥有相同优先级的情况下，会选择最高版本安装。 -->
