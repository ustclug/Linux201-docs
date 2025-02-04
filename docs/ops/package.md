---
icon: material/package
---

# 包管理系统

!!! note "主要作者"

    [@2403772980ygy][2403772980ygy]、[@taoky][taoky]

!!! warning "本文编写中"

<!-- 简介 -->

包管理系统是现代 Linux 发行版的重要组成部分。以下介绍与 Debian 的包管理系统相关工具，例如 APT（Advanced Package Tool）。其他发行版的包管理系统会有所不同，可参考 [Arch Linux Wiki 的 pacman/Rosetta 页面](https://wiki.archlinux.org/title/Pacman/Rosetta)。

本文假设读者了解最基础的 `apt` 使用方法，如 `apt install`, `apt remove`, `apt update`, `apt upgrade`。

## APT

Debian 有多个与软件包管理相关的工具。

其中的底层工具为 dpkg。dpkg 不负责管理软件依赖关系，只管理具体某一个包的安装、卸载等操作。因此**除非需要排查疑难问题，否则不应该直接使用 dpkg**。

!!! warning "避免在安装 deb 文件时使用 dpkg"

    网络上许多教程，甚至是一些官方文档，都会建议使用 `dpkg -i` 安装 deb 文件。当 deb 存在依赖，并且系统未安装满足要求的依赖时，直接使用 `dpkg` 会导致系统依赖管理出现问题，需要额外花费精力修复。

    建议始终使用 `apt install ./path/to/package.deb` 的方式安装 deb 文件。

从用户视角来看，最常使用的工具是 apt（以及其他以 `apt-` 开头的命令）。

### 常用操作 {#common-operations}

#### 标记软件包为自动/手动安装 {#auto-manual}

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

#### 推荐与建议 {#recommends-suggests}

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

#### 搜索包 {#search}

Debian 与 Ubuntu 均提供了网页端搜索软件包的服务：[Debian 软件包](https://packages.debian.org/)、[Ubuntu Packages Search](https://packages.ubuntu.com/)。不过，使用 apt 工具搜索来快得多。

##### 名称与描述搜索：`apt search` {#apt-search}

`apt search <name>` 可以进行包的查找。

也可以通过使用一种特殊的语法（apt-patterns）来进行更具体的查找。

比如你想寻找已经安装，并且名称包含 gcc 的软件，可以使用 `~i ~ngcc`，
如果要求名称完全匹配，可以使用 `~i ?exact-name(gcc)`

以下是一些常见的 apt-patterns 单位

- `?and()` 也可以使用空格分隔若干个 apt-patterns 简写。
- `?or()` 也可以使用 `|` 分隔若干个 apt-patterns 简写。
- `?not()` 可以使用 `!` 进行简写。
- `~g` 为需要被 autoremove 的已安装包。在进行 autoremove 之前建议进行一次检查。
- `~i` 为已经安装的包。
- `~U` 可以升级的包。
- `~nREGEX` 包名称满足正则表达式的包。

##### 文件搜索：`apt-file` {#apt-file}

APT 家族中存在一个用于查找文件所属包的工具 `apt-file`

使用 `apt-file update` 进行数据库的初始化及更新。

使用 `apt-file search <file>` 进行搜索。

可以使用 `dpkg -S <file>` 搜索所有**已安装**包中的文件。

反过来，想要查看一个包包含什么文件，可以使用 `apt-file list <name>`。

使用 `dpkg-deb -c <name_version.deb>` 查看 .deb 中内容。

也可以使用 `dpkg-query -L <name>` ，但是这只对已经安装的包生效。

在使用了一个未安装的命令时，可以选择使用 `command-not-found`。

其安装方式十分简单，只需 `apt install command-not-found` 即可。

#### 固定包

有时我们希望固定一个包，使得这个包不会被改变或升级。

这时可以使用 `apt-mark hold <name>` ，这个包将会被固定，其不会被升级。

#### 自动更新

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

查看并确认系统自动更新时的行为。

此外，systemd 服务 `unattended-upgrades.service` 会确保系统在关机或重启前正确进行软件包升级的收尾工作。因此也需要确认该服务已启动并会开机自启。

#### 使用 aptitude 作为替代前端

aptitude 是 dpkg 的一个 tui 前端，拥有更加简洁的操作以及更加完善的依赖解析机制。

在终端里直接运行 `aptitude` 命令即可

可以使用 `?` 键查看说明，使用 `q` 退出

#### 进行完整性校验

dpkg 可以对已经安装的包进行完整性校验。

通过

```sh
dpkg -V <name>
```

对已经安装的包的完整性进行检查

可以省略 `<name>` 选项，以对于所有包进行检查。

注意，该操作并不能可靠地用于防范病毒入侵，其主要用途是防范意外的数据丢失或修改。

<!-- automatic 和 manual 安装的区别，autoremove 的功能 -->
<!-- "Recommends", "Suggests" 等是什么；在需要精简的场合使用 --no-install-recommends 避免安装不必要的软件包 -->
<!-- 查找某个文件可以由什么包提供，查找某个包提供了什么文件 -->
<!-- APT pattern（例如查找系统中状态为 local 的软件包） -->
<!-- 如何固定一个软件包的版本（避免被升级） -->
<!-- 配置自动升级 (unattended-upgrade) -->
<!-- aptitude 简介 -->
<!-- 检查已安装软件包完整性 -->

### 理解 apt 基本目录结构

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

apt 在遇到相同软件包时，会选择优先级最高的安装包进行安装。在拥有相同优先级的情况下，会选择最高版本安装。

### 软件包优先级

如果你同时使用多个不同的源，而这两个源包含相同的包，那么在安装时会产生歧义。

我们通过 `apt-cache policy <name>` 查看包的安装状态与优先级信息。

例子：

在安装 sudo 前：

```sh
root@c8338bbdbf69:/var/lib/apt# apt-cache policy sudo
sudo:
  Installed: (none)
  Candidate: 1.9.13p3-1+deb12u1
  Version table:
     1.9.13p3-1+deb12u1 500
        500 http://mirrors.ustc.edu.cn/debian bookworm/main amd64 Packages
```

在安装 sudo 后

```sh
root@c8338bbdbf69:/var/lib/apt# apt-cache policy sudo 
sudo:
  Installed: 1.9.13p3-1+deb12u1
  Candidate: 1.9.13p3-1+deb12u1
  Version table:
 *** 1.9.13p3-1+deb12u1 500
        500 http://mirrors.ustc.edu.cn/debian bookworm/main amd64 Packages
        100 /var/lib/dpkg/status
```

在添加另一软件源后：

```sh
sudo:
  Installed: 1.9.13p3-1+deb12u1
  Candidate: 1.9.13p3-1+deb12u1
  Version table:
 *** 1.9.13p3-1+deb12u1 500
        500 http://mirrors.ustc.edu.cn/debian bookworm/main amd64 Packages
        500 http://mirrors.nju.edu.cn/debian bookworm/main amd64 Packages
        100 /var/lib/dpkg/status
```

在声明默认安装目标时（注意`-t stable`选项）：

```sh
root@c8338bbdbf69:/etc/apt/preferences.d# apt-cache policy -t stable sudo
sudo:
  Installed: 1.9.13p3-1+deb12u1
  Candidate: 1.9.13p3-1+deb12u1
  Version table:
 *** 1.9.13p3-1+deb12u1 990
        990 http://mirrors.ustc.edu.cn/debian bookworm/main amd64 Packages
        990 http://mirrors.nju.edu.cn/debian bookworm/main amd64 Packages
        100 /var/lib/dpkg/status
```

如果有两个源同时拥有最高的优先级并且在同优先级下有最新的版本，但是其 metadata 有差异，那么安装**被卸载的**包。

#### 编写优先级配置

优先级配置条目的一般格式如下：

```yaml
Package: <name>
Pin: <clause>
Pin-Priority: <priority>
```

例如：

```yaml
Package: sudo
Pin: version 1.9.13p3*
Pin-Priority: 1001
```

那么在安装 sudo 包时会最优先安装任何 1.9.13p3 版本。在这之后会安装最新版本。

可以选择调整不同源的优先级，例如：

```yaml
Package: *
Pin: origin "mirrors.ustc.edu.cn"
Pin-Priority: 999
```

如果 origin 后使用空字符串，那么代表本地。

**对于优先级大于等于 1000 的来源，安装时可以允许降级。**

对于优先级介于 990 与 999 之间的来源，就算发行目标不一致也会进行安装，除非本地的优先级更高。因此可以优先安装一些包，例如：

```yaml
Package: vim
Pin: release a=experimental
Pin-Priority: 991
```

这会使得 vim 优先安装来自 experimental 的版本。

对于优先级介于 500 与 989 之间的来源，其会优先于一般来源安装。

对于优先级介于 100 与 499 之间的来源，会落后于其他来源安装。

对于优先级介于 1 与 99 之间的来源，只有系统没有安装的时候会进行安装。

**对于优先级小于 0 的来源，不会安装该来源的包，可以用来屏蔽一些可能出问题的包。**

**优先级为 0 是未定义的，不要使用。**

对于一个具体包（例如 sudo），第一个出现的**针对**该包的条目决定其优先级。否则，

这些配置有很多不同选项，详细请参考官方文档。

关于 apt 优先级，可以通过 `man apt_preferences` 查看更具体的信息。

<!-- 介绍 apt-cache policy 工具的使用 -->
<!-- 如何编写 /etc/apt/preferences.d/ 配置，举一些例子 -->

## 使用源码重编译包

有时，默认的编译设置并不满足实际的需求，有时，我们需要一些软件包的更新版本，但是这些版本的依赖难以满足，这时，我们可能可以尝试自己编译一个包。

### 使用 apt 获得源码

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

以编译源代码并生成安装包。

## 软件源

### 目录结构

### 构建一个自己的 DEB 软件源

<!-- 可参考 https://github.com/USTC-vlab/deb -->

## 软件包构建

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
