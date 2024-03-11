# 包管理器

在 Linux 系统中往往有一些系统负责软件的安装，升级，卸载。这个系统被称作包管理器（Package Manager）。

包管理器的范畴较广：管理系统的，比如 apt，zypper；管理环境的，比如 conda；管理语言包的，比如 pip，gem；有一些包管理器甚至是语言的“附属”，如 cargo

本文将着重讲解 Debian 的包管理器。

Debian 的包管理器是 APT（**A**dvanced **p**ackage **t**ool）& dpkg 其中，dpkg 负责中低层操作，包括.deb 包的安装，卸载，以及信息查询，dpkg 还可以检查依赖的安装情况。

APT 主要功能是解析包的依赖信息，从线上（或线下）的软件仓库（repository）下载（离线下载）.deb 软件包，然后按照合理的顺序调用`dpkg`，在必要时使用`--force`。

## 安装一个包（.deb）的过程

在这一段中，可以自己手操（其实建议不要）安装若干包，这里以`apt-utils`为例进行演示，这个包的依赖在 debian 环境中应当已经被配置完成。

1. 准备工作：获得`apt-utils`的下载地址，并且在系统中下载。创建/tmp/install-temp 文件夹。

    ```bash
    cd /tmp
    mkdir install-temp
    cd install-temp
    wget http://ftp.cn.debian.org/debian/pool/main/a/apt/apt-utils_2.7.12_amd64.deb

    # 可以观察包的内容
    # dpkg -c apt-utils_2.7.12_amd64.deb
    # apt-file list apt-utils # 这个命令位于apt-file包中
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

    这个包的结构十分简单，仅作参考用，大多数的包包含 preinst，postinst，conffiles，prerm，postrm 等附加属性，安装过程步骤比该例复杂很多，因此请慎重（不要）使用以上步骤！尽可能使用 gpkg 等工具进行包的操作。

## 配置文件与辅助文件

`dpkg`的配置文件位于`/etc/dpkg/`，辅助文件位于`/var/lib/dpkg/`

APT 的配置文件位于`/etc/apt`，辅助文件位于`/var/lib/apt`

可以观察`/var/lib/apt/lists`中的文件作为参考

TODO

## 重要而不常见的功能

TODO
