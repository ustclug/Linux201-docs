---
icon: material/package
---

# 包管理系统

!!! warning "本文初稿编写中"

<!-- 简介 -->

APT(Advanced Package Tool) 是 Debian 发行版最常用的包管理工具。其可以执行安装，卸载，更新，系统更新，校验与修复这些常见功能。

## APT 系列工具

Debian 是一个基于二进制（而非源码）的发行版，其软件包格式为 .deb，这代表这是一个二进制包。

Debian 的初等包管理器是 dpkg，其负责管理包的安装，删除，查询，替换，校验。

dpkg 一般不会被直接使用。而是作为 apt 以及其他一些高等包管理器的后端使用。

Debian 自带的高等包管理器是 APT，负责进行依赖解析与安装包下载，并且以最优的顺序调用 dpkg，其没有直接安装 .deb 包的能力。

Debian 下还有很多包管理软件，如 Synaptics、Aptitude，这里不一一详细展开。

### 常用操作

#### 安装软件包
   如果我们需要安装一个名称为 name 的包
   
   在手动下载 .deb 包后，使用 dpkg 直接安装 .deb 包：
   
   `dpkg -i <name_version.deb>`
   
   使用 apt 安装软件包：
   
   `apt install <name>`
   
   如果 name 有未在系统上安装的依赖的话，那么第一个命令会失败（除非使用 `--force` 选项），第二个命令会下载对应的安装包及其依赖，并且进行安装。
   
#### 卸载软件包

   使用 dpkg 直接卸载：
   
   `dpkg -r <name>`
   
   使用 apt 卸载：

   `apt remove name`

   那么现在产生了一个问题：要是我安装了一个有很多依赖的包，那么我们卸载它时依赖不会同时被卸载。这样依赖会一直占据我们电脑里面的空间。而手动卸载依赖并不直观，还可能破坏其他包的依赖。

   因此，在使用 APT 安装一个包时，我们将其标记为 manual，在安装依赖时，我们将其标记为 automatic，
   那么我们知道**所有没有被 manual 直接或者间接依赖的 automatic 包**都是不必要的。

   这样，我们可以使用`apt autoremove`来卸载不必要的包以释放存储空间。

#### 推荐与建议

   安装软件包时，APT 在默认配置下会安装推荐（Recommended）的包。还会提示你可以安装建议（Suggested）的包以拓展原包的功能。

   比如：apt 包的推荐有 ca-certificates，建议包有 aptitude、synaptic、gnupg、powermgmt-base 和 dpkg-dev

   那么安装这个包时，会默认安装 ca-certificates，结束后会给出后面的包的提示。

   为了精简安装的软件包，可以使用 `--no-install-recommends` 的选项，以跳过推荐的软件包。

   还可以在配置文件中添加 `Apt::Install-Recommends "false"` 以使默认配置不会安装推荐的包。

   当这类包被安装的时候，它们的类型为 automatic，也就是说在默认情况下，
   如果没有软件**推荐或者建议它们**，它们会被 `apt autoremove` 卸载。

   使用 `apt-mark (automatic|manual) <name>` 修改包的状态。

#### 查找包中文件与文件所属的包，替换 command not found

   APT 家族中存在一个用于查找文件所属包的工具 `apt-file`

   使用 `apt-file update` 进行数据库的初始化及更新。

   使用 `apt-file search <file>` 进行搜索。

   可以使用 `dpkg -S <file>` 搜索所有**已安装**包中的文件。

   反过来，想要查看一个包包含什么文件，可以使用 `apt-file list <name>`。

   使用 `dpkg-deb -c <name_version.deb>` 查看 .deb 中内容。

   也可以使用 `dpkg-query -L <name>` ，但是这只对已经安装的包生效。

   在使用了一个未安装的命令时，可以选择使用 `command-not-found`。

   其安装方式十分简单，只需 `apt install command-not-found` 即可。

#### 查找包

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

#### 固定包

   有时我们希望固定一个包，使得这个包不会被改变或升级。

   这时可以使用 `apt-mark hold <name>` ，这个包将会被固定，其不会被升级。
   
#### 自动更新

   一般而言，使用 apt 的系统默认安装了`unattended-upgrades`包，如果系统上没有，可以使用
   
   ```sh
   apt install unattended-upgrades
   ```
   
   进行安装
   
   可以使用
   
   ```sh
   sudo unattended-upgrades --dry-run --debug
   ```
   
   检验系统自动更新是否可用
   
   unattended-upgrades 以 systemd 服务形式存在，通过以下命令启动自动更新
   
   ```sh
   sudo systemctl enable unattended-upgrades
   sudo systemctl start unattended-upgrades
   ```

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

```
Package: <name>
Pin: <clause>
Pin-Priority: <priority>
```

例如：

```
Package: sudo
Pin: version 1.9.13p3*
Pin-Priority: 1001
```

那么在安装 sudo 包时会最优先安装任何 1.9.13p3 版本。在这之后会安装最新版本。

可以选择调整不同源的优先级，例如：

```
Package: *
Pin: origin "mirrors.ustc.edu.cn"
Pin-Priority: 999
```

如果 origin 后使用空字符串，那么代表本地。

**对于优先级大于等于 1000 的来源，安装时可以允许降级。**

对于优先级介于 990 与 999 之间的来源，就算发行目标不一致也会进行安装，除非本地的优先级更高。因此可以优先安装一些包，例如：

```
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
