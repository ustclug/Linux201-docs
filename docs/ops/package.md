---
icon: material/package
---

# 包管理系统

!!! warning "本文初稿编写中"

<!-- 简介 -->

APT(Advanced Package Tool) 是 Debian 发行版最常用的包管理工具。其可以执行安装，卸载，更新，系统更新，校验与修复这些常见功能。

## APT 系列工具

Debian 是一个基于二进制（而非源码）的发行版，其软件包格式为 .deb ，这代表这是一个二进制包。

Debian 的初等包管理器是 dpkg ，其负责管理包的安装，删除，查询，替换，校验。

dpkg 一般不会被直接使用。而是作为 apt 以及其他一些高等包管理器的后端使用。

Debian 自带的高等包管理器是 APT ，负责进行依赖解析与安装包下载，并且以最优的顺序调用 dpkg ，其没有直接安装 .deb 包的能力。

Debian 下还有很多包管理软件，如 Synaptics 、 Aptitude ，这里不一一详细展开。

### 常用操作

0. 安装软件包

   如果我们需要安装一个名称为 name 的包
   
   在手动下载 .deb 包后，使用 dpkg 直接安装 .deb 包：
   
   `dpkg -i <name_version.deb>`
   
   使用 apt 安装软件包：
   
   `apt install <name>`
   
   如果 name 有未在系统上安装的依赖的话，那么第一个命令会失败（除非使用 `--force** 选项），第二个命令会下载对应的安装包及其依赖，并且进行安装。
   
0. 卸载软件包

   使用 dpkg 直接卸载：
   
   `dpkg -r <name>**
   
   使用 apt 卸载：
   
   `apt remove name**
   
   那么现在产生了一个问题：要是我安装了一个有很多依赖的包，那么我们卸载它时依赖不会同时被卸载。这样依赖会一直占据我们电脑里面的空间。而手动卸载依赖并不直观，还可能破坏其他包的依赖。
   
   因此，在使用 APT 安装一个包时，我们将其标记为 manual ，在安装依赖时，我们将其标记为 automatic ，那么我们知道**所有没有被 manual 直接或者间接依赖的 automatic 包**都是不必要的。
   
   这样，我们可以使用`apt autoremove`来卸载不必要的包以释放存储空间。

0. 推荐与建议

   安装软件包时， APT 在默认配置下会安装推荐（ Recommended ）的包。 还会提示你可以安装建议（ Suggested ）的包以拓展原包的功能。
   
   比如： apt包的推荐有 ca-certificates ，建议包有 aptitude 、 synaptic 、 gnupg 、 powermgmt-base 和 dpkg-dev
   
   那么安装这个包时，会默认安装 ca-certificates ， 结束后会给出后面的包的提示。
   
   为了精简安装的软件包，可以使用 `--no-install-recommends` 的选项，以跳过推荐的软件包。
   
   还可以在配置文件中添加 `Apt::Install-Recommends "false"` 以使默认配置不会安装推荐的包。
   
   当这类包被安装的时候，它们的类型为 automatic ，也就是说在默认情况下，如果没有软件**推荐或者建议它们**，它们会被 `apt autoremove` 卸载。
    
   使用 `apt-mark (automatic|manual) <name>` 修改包的状态。
   
0. 查找包中文件与文件所属的包，替换 command not found
   
   APT 家族中存在一个用于查找文件所属包的工具 `apt-file`
   
   使用 `apt-file update` 进行数据库的初始化及更新。
   
   使用 `apt-file search <file>` 进行搜索。
   
   可以使用 `dpkg -S <file>` 搜索所有**已安装**包中的文件。
   
   反过来，想要查看一个包包含什么文件，可以使用 `apt-file list <name>`。
   
   使用 `dpkg-deb -c <name_version.deb>` 查看 .deb 中内容。
   
   也可以使用 `dpkg-query -L <name>` ，但是这只对已经安装的包生效。
   
   在使用了一个未安装的命令时，可以选择使用 `command-not-found`。
   
   其安装方式十分简单，只需 `apt install command-not-found` 即可。
   
0. 查找包

   `apt search <name>` 可以进行包的查找。
   
   也可以通过使用一种特殊的语法（ apt-patterns ）来进行更具体的查找。
   
   比如你想寻找已经安装，并且名称包含gcc的软件，可以使用 `~i ~ngcc` ，如果要求名称完全匹配， 可以使用 `~i ?exact-name(gcc)`
   
   以下是一些常见的 apt-patterns 单位
   
   - `?and()` 也可以使用空格分隔若干个 apt-patterns 简写。
   - `?or()` 也可以使用 `|` 分隔若干个 apt-patterns 简写。
   - `?not()` 可以使用 `!` 进行简写。
   - `~g` 为需要被 autoremove 的已安装包。在进行 autoremove 之前建议进行一次检查。
   - `~i` 为已经安装的包。
   - `~U` 可以升级的包。
   - `~nREGEX` 包名称满足正则表达式的包。
   
0. 固定包

   有时我们希望固定一个包，使得这个包不会被改变或升级。
   
   这时可以使用 `apt-mark hold <name>` ，这个包将会被固定，其不会被升级。
 
<!-- automatic 和 manual 安装的区别，autoremove 的功能 -->
<!-- "Recommends", "Suggests" 等是什么；在需要精简的场合使用 --no-install-recommends 避免安装不必要的软件包 -->
<!-- 查找某个文件可以由什么包提供，查找某个包提供了什么文件 -->
<!-- APT pattern（例如查找系统中状态为 local 的软件包） -->
<!-- 如何固定一个软件包的版本（避免被升级） -->
<!-- 配置自动升级 (unattended-upgrade) -->
<!-- aptitude 简介 -->
<!-- 检查已安装软件包完整性 -->

### 软件包优先级

<!-- 介绍 apt-cache policy 工具的使用 -->
<!-- 如何编写 /etc/apt/preferences.d/ 配置，举一些例子 -->

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
