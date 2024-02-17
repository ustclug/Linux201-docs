# 分区与文件系统

!!! warning "本文初稿已完成，但可能仍需大幅度修改"

## 相关概念

块设备

:   常见的磁盘设备的读写均以块（而不是字节）为单位，因此在 Linux 中，设备文件分为块设备和字符设备两种。

    可以使用 `lsblk` 命令查看系统中的块设备。一个桌面系统的例子如下：

    ```text
    NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
    nvme0n1     259:0    0  1.9T  0 disk 
    ├─nvme0n1p1 259:1    0  260M  0 part 
    ├─nvme0n1p2 259:2    0   56G  0 part [SWAP]
    └─nvme0n1p3 259:3    0  1.8T  0 part /var/lib/docker/btrfs
                                         /var
                                         /tmp
                                         /opt
                                         /home
                                         /
    ```

分区表

:   一个块设备上可以有一个或多个分区，而分区表则记录了分区的信息，常见的分区表有 MBR 和 GPT 两种格式。

    可以使用 `fdisk` 查看块设备的分区表，例如：

    ```console
    $ sudo fdisk -l /dev/nvme0n1
    Disk /dev/nvme0n1: 1.86 TiB, 2048408248320 bytes, 4000797360 sectors
    Disk model: INTEL SSDPEKNU020TZ                     
    Units: sectors of 1 * 512 = 512 bytes
    Sector size (logical/physical): 512 bytes / 512 bytes
    I/O size (minimum/optimal): 512 bytes / 512 bytes
    Disklabel type: gpt
    Disk identifier: BAF03C52-854E-41AD-9C42-6DD5C0E9F156
    
    Device             Start        End    Sectors  Size Type
    /dev/nvme0n1p1      2048     534527     532480  260M EFI System
    /dev/nvme0n1p2    534528  117975039  117440512   56G Linux swap
    /dev/nvme0n1p3 117975040 4000796671 3882821632  1.8T Linux filesystem
    ```

    可以看到，该块设备使用了 GPT 分区表，有三个分区。

文件系统

:   每个分区需要被格式化成某种文件系统后，才能存储文件。

## 本地回环

Linux 支持「本地回环设备」，支持挂载一个文件作为块设备使用，类似于「虚拟光驱」类软件。
因此，可以通过本地回环的方式，在不购买新硬件的情况下进行一些磁盘相关的实验。

!!! note "本地回环与容器"

    Linux 目前不支持设备命名空间（隔离），因此如果需要在容器环境内对本地回环进行挂载等操作，需要特权容器，并且为 root 权限。
    Linux 内核开发中曾有过允许非特权用户挂载本地回环的讨论（[loopfs LWN](https://lwn.net/Articles/819625/)），
    但是由于安全性问题（内核文件系统开发时假设挂载的内容不会被恶意构造，而提供相关支持会破坏这样的假设），未进入主线。

    这也是 Vlab 不支持本地回环的原因。

可以使用 `mount` 命令挂载文件到本地回环。最常见的用途是挂载一个 ISO 文件：

```console
$ sudo mount -o loop ./debian-12.4.0-amd64-DVD-1.iso /media/iso
$ cd /media/iso
$ ls
boot/  debian@  doc/  firmware/  install.amd/  md5sum.txt  pool/        README.mirrors.html  README.source
css/   dists/   EFI/  install/   isolinux/     pics/       README.html  README.mirrors.txt   README.txt
$ cd
$ sudo umount /media/iso
```

但是有的时候，我们需要挂载测试磁盘镜像中的某个分区，此时使用 `mount` 就会麻烦很多——需要计算对应的偏移量。
此时可以使用 `kpartx` 命令，它会自动识别磁盘镜像中的分区，并创建对应的回环设备：

```console
$ fdisk -l ./root.img
Disk ./root.img: 5 GiB, 5368709120 bytes, 10485760 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: 9E89351F-1674-4BA6-9FA3-D063E7C028E0

Device       Start      End Sectors  Size Type
./root.img1   2048   499711  497664  243M EFI System
./root.img2 499712 10483711 9984000  4.8G Linux filesystem
$ sudo kpartx -av ./root.img
add map loop0p1 (254:0): 0 497664 linear 7:0 2048
add map loop0p2 (254:1): 0 9984000 linear 7:0 499712
$ ls -l /dev/mapper/loop0p*
lrwxrwxrwx 1 root root 7 Feb 10 17:22 /dev/mapper/loop0p1 -> ../dm-0
lrwxrwxrwx 1 root root 7 Feb 10 17:22 /dev/mapper/loop0p2 -> ../dm-1
$ sudo mount /dev/mapper/loop0p2 /media/root
$ ls /media/root
...
$ sudo umount /media/root
$ sudo kpartx -dv ./root.img
del devmap : loop0p1
del devmap : loop0p2
loop deleted : /dev/loop0
```

系统的本地回环信息可以使用 `losetup` 命令查看。该命令也可以管理本地回环设备：

```console
$ sudo kpartx -av ./root.img
...
$ sudo losetup -a
/dev/loop0: [0028]:18723300 (/home/username/tmp/root.img)
$ sudo losetup -D
$ sudo losetup -a  # 正在使用的设备不会被立刻删除
/dev/loop0: [0028]:18723300 (/home/username/tmp/root.img)
$ sudo losetup --partscan --find ./root2.img  # partscan 用于自动识别分区，find 用于自动分配本地回环设备
$ # 也可以自己指定本地回环设备路径
$ sudo losetup -a
/dev/loop1: [0028]:18789360 (/home/username/tmp/root2.img)
/dev/loop0: [0028]:18723300 (/home/username/tmp/root.img)
$ ls -lha /dev/loop1*  # 该镜像中包含的两个分区自动识别为了 loop1p1 和 loop1p2
brw-rw---- 1 root disk   7, 1 Feb 10 17:30 /dev/loop1
brw-rw---- 1 root disk 259, 4 Feb 10 17:30 /dev/loop1p1
brw-rw---- 1 root disk 259, 5 Feb 10 17:30 /dev/loop1p2
$ sudo losetup -d /dev/loop1
$ sudo losetup -a
/dev/loop0: [0028]:18723300 (/home/username/tmp/root.img)
$ sudo kpax -dv ./root.img  # 清理现场
$ sudo losetup -a
```

## 分区表

以下介绍 MBR 与 GPT 分区表。

MBR（Master Boot Record）分区表是早期的分区表格式，在存储分区信息的同时，还负责系统的启动。
MBR 信息存储在磁盘的第一个扇区[^sector]（512 字节[^sector-size]），其中用于引导的代码位于最开头，占据 440 字节（BIOS 在启动会加载代码，并且跳转）；
提供给分区信息的空间只有 64 个字节。由于每个分区需要 16 字节的信息，因此 MBR 分区表最多支持 4 个主分区。
为了让磁盘支持更多分区，出现了扩展分区的概念。
扩展分区是一个特殊的主分区，可以划分为多个逻辑分区。受到设计限制，MBR 仅支持最大 2 TiB 的磁盘。

而 GPT（GUID Partition Table）分区表是新一代的分区表格式，不再存储引导信息，并且支持更多的分区、更大的磁盘。
目前除非极其老旧的系统，都使用 GPT 分区表。GPT 分区表在最开头存储了一份「保护性 MBR」（Protective MBR），用于防止不认识 GPT 的旧系统和软件对磁盘误操作，
同时分区表信息在磁盘最后有一份备份，以减小损坏风险。

!!! note "那 GPT 的磁盘怎么开机呢？"

    对于使用传统 BIOS 的机器，GPT 开头的保护性 MBR 仍然可以存储引导代码。不过，目前的主流是使用 UEFI，不再需要在扇区里存储引导代码，
    而是有一个专门的 EFI 系统分区（必须格式化为 FAT32），用来存储引导程序与其他信息。

    以下展示一个 EFI 系统分区的例子：

    ```console
    $ sudo mount /dev/disk/by-uuid/0E62-46C6 /efi
    $ mount | grep efi
    ...
    /dev/nvme0n1p1 on /efi type vfat (rw,relatime,fmask=0077,dmask=0077,codepage=437,iocharset=ascii,shortname=mixed,utf8,errors=remount-ro)
    $ sudo tree /efi
    /efi/
    ├── $RECYCLE.BIN
    │   └── desktop.ini
    ├── BOOT
    │   └── BOOT.SDI
    ├── EFI
    │   ├── arch
    │   │   ├── fw
    │   │   └── fwupdx64.efi
    │   ├── Boot
    │   │   ├── bootx64.efi
    │   │   ├── LenovoBT.EFI
    │   │   ├── License.txt
    │   │   └── ReadMe.txt
    │   ├── GRUB
    │   │   └── grubx64.efi
    │   └── Linux
    └── System Volume Information
        ├── IndexerVolumeGuid
        └── WPSettings.dat

    10 directories, 10 files
    ```

    这里 `efi` 后缀的文件就是 UEFI 会选择的启动引导程序，一般可以在启动时按下 F12 或者其他快捷键选择启动的设备或 EFI 文件。

### 实验操作展示

我们可以使用诸如 `fdisk`, `parted` 等工具对分区表进行操作。对于图形界面用户，`gparted` 是一个不错的选择。

首先创建一个空文件：

```shell
truncate -s 8G test.img
```

!!! info "稀疏文件"

    这里我们创建了「稀疏文件」（Sparse file）。尽管文件大小是 8G，但是实际上只占用了很少的磁盘空间。可以以此验证：

    ```console
    $ du -h test.img
    0	test.img
    $ du -h --apparent-size test.img
    8G	test.img
    ```

之后我们就可以直接操作这个文件，而不用担心破坏真实的磁盘。

```shell
fdisk test.img
# 或者
parted test.img
```

以下的例子会创建一个 256M 的 EFI 分区，一个 1G 的 swap 分区，剩下的空间作为根文件系统的分区。

??? info "fdisk 操作示例"

    fdisk 默认使用 MBR 分区表，如果需要使用 GPT 分区表，需要使用 `g` 命令。
    在创建分区时，按回车使用默认参数。设置分区末尾位置时，可以使用 `+` 表示相对于当前位置的偏移量（即分区大小），或者使用 `-` 表示相对于磁盘末尾的偏移量（即在尾部留出多少空间）。

    最后使用 `w` 命令写入分区表。如果不想实际写入到磁盘，可以使用 `q` 退出而不保存。
    更多信息可以使用 `m` 命令查看帮助。

    ```console
    $ fdisk test.img
    Welcome to fdisk (util-linux 2.39.3).
    Changes will remain in memory only, until you decide to write them.
    Be careful before using the write command.

    Device does not contain a recognized partition table.
    Created a new DOS (MBR) disklabel with disk identifier 0xb7358160.

    Command (m for help): g
    Created a new GPT disklabel (GUID: E19C12C2-CAB9-4A9A-88D5-2F389F7B4452).

    Command (m for help): n
    Partition number (1-128, default 1): 
    First sector (2048-16777182, default 2048): 
    Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-16777182, default 16775167): +256M

    Created a new partition 1 of type 'Linux filesystem' and of size 256 MiB.

    Command (m for help): n
    Partition number (2-128, default 2): 
    First sector (526336-16777182, default 526336): 
    Last sector, +/-sectors or +/-size{K,M,G,T,P} (526336-16777182, default 16775167): +1G

    Created a new partition 2 of type 'Linux filesystem' and of size 1 GiB.

    Command (m for help): n
    Partition number (3-128, default 3): 
    First sector (2623488-16777182, default 2623488): 
    Last sector, +/-sectors or +/-size{K,M,G,T,P} (2623488-16777182, default 16775167): 

    Created a new partition 3 of type 'Linux filesystem' and of size 6.7 GiB.

    Command (m for help): t
    Partition number (1-3, default 3): 1
    Partition type or alias (type L to list all): L
    （省略）
    Partition type or alias (type L to list all): 1

    Changed type of partition 'Linux filesystem' to 'EFI System'.

    Command (m for help): t
    Partition number (1-3, default 3): 2
    Partition type or alias (type L to list all): 19

    Changed type of partition 'Linux filesystem' to 'Linux swap'.

    Command (m for help): p
    Disk test.img: 8 GiB, 8589934592 bytes, 16777216 sectors
    Units: sectors of 1 * 512 = 512 bytes
    Sector size (logical/physical): 512 bytes / 512 bytes
    I/O size (minimum/optimal): 512 bytes / 512 bytes
    Disklabel type: gpt
    Disk identifier: E19C12C2-CAB9-4A9A-88D5-2F389F7B4452

    Device       Start      End  Sectors  Size Type
    test.img1     2048   526335   524288  256M EFI System
    test.img2   526336  2623487  2097152    1G Linux swap
    test.img3  2623488 16775167 14151680  6.7G Linux filesystem

    Command (m for help): w
    The partition table has been altered.
    Syncing disks.
    ```

??? info "parted 操作示例"

    这里不推荐交互式使用 `parted`，因为其交互不如 `fdisk` 直观，并且**所有操作均为立刻写入**。但是 `parted` 在脚本中使用更加方便。
    parted 脚本的例子可以参考 [101strap 脚本](https://github.com/ustclug/101strap/blob/4d27f3dc86d9201f139e605e6fdaa595c25fb1ea/101strap_img#L46)。

    ```console
    $ parted -a optimal test.img  # 使用 optimal 参数，在创建新分区时使用最佳对齐
    WARNING: You are not superuser.  Watch out for permissions.
    GNU Parted 3.6
    Using /home/taoky/tmp/201/test.img
    Welcome to GNU Parted! Type 'help' to view a list of commands.
    (parted) mklabel gpt
    (parted) mkpart efi 0% 256M
    (parted) mkpart swap 256M 1289M
    (parted) mkpart rootfs 1289M 100%
    (parted) set 1 esp
    New state?  [on]/off?
    (parted) set 2 swap
    New state?  [on]/off?
    (parted) print
    Model:  (file)
    Disk /home/taoky/tmp/201/test.img: 8590MB
    Sector size (logical/physical): 512B/512B
    Partition Table: gpt
    Disk Flags: 

    Number  Start   End     Size    File system  Name    Flags
    1      1049kB  256MB   255MB                efi     boot, esp
    2      256MB   1289MB  1033MB               swap    swap
    3      1289MB  8589MB  7300MB               rootfs

    (parted) quit
    ```

在创建后，我们可以使用 `file` 和 `fdisk` 工具验证分区表的类型：

```console
$ file test.img  # MBR 只有一个分区，并且分区 ID 为 0xee，代表该磁盘镜像使用 GPT
test.img: DOS/MBR boot sector; partition 1 : ID=0xee, start-CHS (0x0,0,2), end-CHS (0x3ff,255,63), startsector 1, 16777215 sectors, extended partition table (last)
$ fdisk -l test.img
Disk test.img: 8 GiB, 8589934592 bytes, 16777216 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: E19C12C2-CAB9-4A9A-88D5-2F389F7B4452

Device       Start      End  Sectors  Size Type
test.img1     2048   526335   524288  256M EFI System
test.img2   526336  2623487  2097152    1G Linux swap
test.img3  2623488 16775167 14151680  6.7G Linux filesystem
```

如果对 GPT 的细节感兴趣，可以使用十六进制编辑器查看镜像内容，并与 GPT 标准对照。

??? info "分区对齐"

    观察 fdisk 的输出可以发现一些有趣的地方：查找资料可以知道，GPT 分区表本身只需要 34 个扇区，但是上文中首个分区却从第 2048 个扇区开始。
    这是基于将分区与物理设备的扇区/访问边界「对齐」的考虑。
    
    在实践中我们一般采取 4K（8 个扇区）对齐，因此起始位置需要为 4K（8 个扇区）的整数倍。
    2048 个扇区即 1M，是现代版本 fdisk 的默认对齐粒度，可以应对未来的对齐需求，因此是一个合理且被普遍使用的选择。

## 文件系统

下表给出了常见的文件系统。在某些操作系统上，一部分文件系统可以通过安装第三方软件的方式实现支持，但是可能存在额外的性能或可靠性问题。

| 文件系统                                        | Linux                                                  | macOS                                    | Windows                                  | 特点与备注                                                                                                            |
| ----------------------------------------------- | ------------------------------------------------------ | ---------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| FAT32 (VFAT)                                    | :fontawesome-solid-check:{: .limegreen }               | :fontawesome-solid-check:{: .limegreen } | :fontawesome-solid-check:{: .limegreen } | 仅适用于 EFI 分区和部分情况下的 `/boot`，或不同操作系统交换文件的场合。不支持大于 4 GiB 的文件。                      |
| exFAT                                           | :fontawesome-solid-check:{: .limegreen }               | :fontawesome-solid-check:{: .limegreen } | :fontawesome-solid-check:{: .limegreen } | 应仅用于不同操作系统交换文件。不支持日志。                                                                            |
| [ext4](https://wiki.archlinux.org/title/Ext4)   | :fontawesome-solid-check:{: .limegreen }               | :fontawesome-solid-xmark:{: .orangered } | :fontawesome-solid-xmark:{: .orangered } | Linux 上最常见的文件系统。                                                                                            |
| [XFS](https://wiki.archlinux.org/title/XFS)     | :fontawesome-solid-check:{: .limegreen }               | :fontawesome-solid-xmark:{: .orangered } | :fontawesome-solid-xmark:{: .orangered } | 适用于大文件、大容量的场合。无法随意缩小[^xfs_growfs]。                                                                        |
| ReiserFS                                        | :fontawesome-solid-check:{: .orangered } (deprecated)  | :fontawesome-solid-xmark:{: .orangered } | :fontawesome-solid-xmark:{: .orangered } | 适用于存储大量小文件的场合。由于内核主线已经考虑移除支持，如有存储大量小文件需求，可能需要使用其他方案替代。          |
| [Btrfs](https://wiki.archlinux.org/title/Btrfs) | :fontawesome-solid-check:{: .limegreen }               | :fontawesome-solid-xmark:{: .orangered } | :fontawesome-solid-xmark:{: .orangered } | 内置于 Linux 内核的新一代的 CoW 文件系统，支持快照、透明压缩等高级功能。RAID 5/6 支持不稳定，也有对整体稳定性的争议。 |
| [ZFS](https://wiki.archlinux.org/title/ZFS)     | :fontawesome-solid-check:{: .limegreen }（需要 kernel module）              | :fontawesome-solid-xmark:{: .orangered } | :fontawesome-solid-xmark:{: .orangered } | 起源于 Solaris 的 CoW 文件系统，适用于存储大量文件、需要高级功能的场合。需要额外的内存和 CPU 资源。                   |
| NTFS                                            | :fontawesome-solid-check:{: .limegreen } (Linux 5.15+) | 只读                                     | :fontawesome-solid-check:{: .limegreen } | Windows 上最常见的文件系统。                                                                                          |
| HFS+                                            | 只读                                                   | :fontawesome-solid-check:{: .limegreen } | 只读，Bootcamp                           | macOS 较早期版本最常见的文件系统。                                                                                    |
| APFS                                            | :fontawesome-solid-xmark:{: .orangered }               | :fontawesome-solid-check:{: .limegreen } | :fontawesome-solid-xmark:{: .orangered } | macOS 较新版本的 CoW 文件系统。                                                                                       |

以下将关注在 Linux 服务器端常见的场景。表格中指向 ArchWiki 的链接也可能有所帮助。

### ext4

ext4 是包括 Debian 和 Ubuntu 在内的众多发行版为系统分区（根文件系统）默认采用的文件系统格式。
如果没有特殊的需求，ext4 是一个不错的选择；即使有其他需求，也建议对系统分区使用 ext4。
ext4 最常见的问题之一是 inode 的数量限制。

!!! info "inode"

    inode 是 Unix 文件系统中的一个重要概念，其包含了文件（文件系统对象）的元数据（如权限、大小、时间等），每个文件对应一个 inode，有一个在文件系统上唯一的 inode 号码。
    可以使用 `stat` 或 `ls -i` 查看文件的 inode 信息。

    ```console
    $ stat test
      File: test
      Size: 0         	Blocks: 0          IO Block: 4096   regular empty file
    Device: 0,28	Inode: 54475724    Links: 1
    Access: (0644/-rw-r--r--)  Uid: ( 1000/   username)   Gid: ( 1000/   username)
    Access: 2024-02-11 00:23:27.743633975 +0800
    Modify: 2024-02-11 00:23:27.743633975 +0800
    Change: 2024-02-11 00:23:27.743633975 +0800
     Birth: 2024-02-11 00:23:27.743633975 +0800
    ```

    这里 test 文件的 inode 号码则为 54475724。

在创建 ext4 文件系统时，会固定名为 "bytes-per-inode" 的参数，用于控制总的 inode 数量。默认情况下，硬盘上每有 16KB 的空间，就会保留一个 inode。
该参数无法在文件系统创建后更改。
因此，如果创建了大量小文件，可能会发现磁盘空间并没有用完，但是已经无法再创建新文件了。
此时如果扩充了文件系统的容量，那么 inode 的数量也会按比例增加。

除此之外，ext4 默认的 5% 保留空间也是常会遇到的问题。这一部分保留空间仅允许 root 用户使用，以在磁盘空间不足时仍保证 root 权限的进程能够正常运行。
但是对于现代的大容量磁盘来说，这一部分空间可能会浪费很多。可以使用 `tune2fs` 命令调整这一参数：

```shell
sudo tune2fs -m 1 /dev/sda1  # 将保留空间调整为 1%
```

### Btrfs

尽管在我们的实践中，我们不太建议使用 Btrfs——高级特性用不上，而许多年前在镜像站上的测试表明 Btrfs 在长时间运行后存在严重的性能问题。
但是在许多年的开发后，Btrfs 的稳定性有了很大的提升，并且一部分特性在某些场合下很有用，因此这里提供一些相关的介绍。

#### Subvolume

Subvolume 是 Btrfs 的一个重要概念，可以看作是 Btrfs 的「子文件系统」。与目录不同，Subvolume 是独立的，可以有自己的挂载点。
同时 subvolume 共享同一个 Btrfs 文件系统的空间，不需要手动分配空间。

我们可以来试一试：

```console
$ truncate -s 8G btrfs.img
$ mkfs.btrfs btrfs.img
（输出省略）
$ sudo mount btrfs.img /media/btrfs
$ sudo btrfs filesystem show /media/btrfs  # 可以使用 btrfs 工具管理 Btrfs 文件系统
Label: none  uuid: 5cdcf4bb-8020-45f9-8dfd-95e04a2a2bc1
	Total devices 1 FS bytes used 144.00KiB
	devid    1 size 8.00GiB used 536.00MiB path /dev/loop0

$ # btrfs 工具也可以管理离线的 btrfs 块设备
$ # 接下来创建一些 subvolume
$ sudo btrfs subvolume create /media/btrfs/subvol1
Create subvolume '/media/btrfs/subvol1'
$ sudo btrfs subvolume create /media/btrfs/subvol2
Create subvolume '/media/btrfs/subvol2'
$ sudo btrfs subvolume create /media/btrfs/subvol3
Create subvolume '/media/btrfs/subvol3'
$ sudo btrfs subvolume list /media/btrfs
ID 256 gen 8 top level 5 path subvol1
ID 257 gen 8 top level 5 path subvol2
ID 258 gen 8 top level 5 path subvol3
$ ls -lh /media/btrfs  # 看起来和普通目录没什么区别
total 0
drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol1/
drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol2/
drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol3/
$ sudo umount /media/btrfs
$ sudo mount -o subvol=subvol1 btrfs.img /media/btrfs1  # 挂载 subvol1
$ sudo mount -o subvol=subvol2 btrfs.img /media/btrfs2  # 挂载 subvol2
$ mount | grep btrfs.img
/path/to/btrfs.img on /media/btrfs1 type btrfs (rw,relatime,ssd,discard=async,space_cache=v2,subvolid=256,subvol=/subvol1)
/path/to/btrfs.img on /media/btrfs2 type btrfs (rw,relatime,ssd,discard=async,space_cache=v2,subvolid=257,subvol=/subvol2)
$ sudo umount /media/btrfs1
$ sudo umount /media/btrfs2
```

!!! warning "Subvolume 的挂载参数"

    [大部分 Btrfs 的挂载参数（例如透明压缩）只适用于整个文件系统](https://btrfs.readthedocs.io/en/latest/Subvolumes.html#mount-options)，在首个 subvolume 上挂载时，这些参数会被应用到整个文件系统。
    后续挂载使用的参数会被忽略。

#### 快照

在 subvolume 的基础上，Btrfs 支持了快照功能。这里的快照可能与我们熟悉的「快照」（例如虚拟机软件的快照功能）有所不同，它本质上就是和其他 subvolume 共享数据的 subvolume。让我们试一试吧：

```console
$ sudo mount btrfs.img /media/btrfs  # 挂载整个文件系统
$ echo "test1" > /media/btrfs/subvol1/test  # 可能需要 root 权限
$ sudo btrfs subvolume snapshot /media/btrfs/subvol1 /media/btrfs/snap1  # 创建快照
Create a snapshot of '/media/btrfs/subvol1/' in '/media/btrfs/snap1'
$ # 此时 snap1 和 subvol1 共享数据——存储的是目前 subvol1 的内容
$ cat /media/btrfs/snap1/test
test1
$ echo "test2" > /media/btrfs/subvol1/test  # 修改 subvol1
$ cat /media/btrfs/snap1/test  # snap1 不受影响
test1
$ echo "test3" > /media/btrfs/snap1/test  # 修改 snap1
$ cat /media/btrfs/subvol1/test  # subvol1 不受影响
test2
$ sudo btrfs subvolume delete /media/btrfs/snap1  # 删除快照
Delete subvolume 259 (no-commit): '/media/btrfs/snap1'
$ sudo umount /media/btrfs
```

这里我们可以修改「快照」的内容，在 CoW 文件系统中，修改共享的内容会被复制，而未修改的内容会被共享。
不过很多时候我们不希望快照可写，在创建快照时可以加上 `-r` 参数。

#### 透明压缩

Btrfs 支持透明压缩，文件系统会自动压缩文件，而上层的应用程序不需要关心这一过程。
这也是许多 Btrfs 用户会开启的挂载选项。
Zstd 压缩算法兼顾了性能与压缩效率，是许多用户的选择。

以下是一个启用了 Btrfs 透明压缩（`compress=zstd:3`）的桌面用户，在 `/home` 这个 subvolume 下的例子：

```console
$ sudo compsize /home
Processed 4429337 files, 5827189 regular extents (6428918 refs), 2327200 inline.
Type       Perc     Disk Usage   Uncompressed Referenced  
TOTAL       78%     1017G         1.2T         1.3T       
none       100%      911G         911G         918G       
zstd        27%      105G         384G         413G       
prealloc   100%      643M         643M         1.0G
```

可以看到，透明压缩特性为该用户节省了 200G 的磁盘空间。

#### 常见问题

Balance

:   一个常见的问题是：明明还有剩余空间，但是已经无法写入数据了。简单来说，这是因为 Btrfs 内部存储分为数据（Data）和元数据（Metadata）等部分，当两者任一已满，并且没有未分配（Unallocated）的空间，那么就无法再写入数据了。这可以通过执行 `btrfs filesystem usage` 判断：

    ```console
    $ sudo btrfs filesystem usage /
    Overall:
        Device size:		   1.81TiB
        Device allocated:		   1.66TiB
        Device unallocated:		 156.45GiB
        Device missing:		     0.00B
        Device slack:		     0.00B
        Used:			   1.39TiB
        Free (estimated):		 414.79GiB	(min: 336.57GiB)
        Free (statfs, df):		 414.79GiB
        Data ratio:			      1.00
        Metadata ratio:		      2.00
        Global reserve:		 512.00MiB	(used: 0.00B)
        Multiple profiles:		        no

    Data,single: Size:1.62TiB, Used:1.37TiB (84.43%)
    /dev/nvme0n1p3	   1.62TiB

    Metadata,DUP: Size:18.00GiB, Used:11.54GiB (64.13%)
    /dev/nvme0n1p3	  36.00GiB

    System,DUP: Size:8.00MiB, Used:208.00KiB (2.54%)
    /dev/nvme0n1p3	  16.00MiB

    Unallocated:
    /dev/nvme0n1p3	 156.45GiB
    ```

    除了直接删除文件以外，使用 `truncate` 将大文件的大小截断为 0 可以在不添加 metadata 信息的情况下释放空间。
    如果 metadata 已满，但是 data 仍有空间，可以使用 balance 功能重新分配空间：

    ```console
    $ sudo btrfs balance start /mountpoint -dusage=0
    ```

    `-dusage=0` 代表将 data 中没有使用（使用率为 0%）的空间释放。视情况，有可能需要增大 `-dusage` 参数的值。

Check

:   Btrfs 的文件系统检查工具 `btrfs-check` **不是传统文件系统 fsck 的平替**。
    对出现问题的 Btrfs 分区使用 `btrfs-check` 的 `--repair` 选项很可能导致数据丢失。

    一般来讲，建议设置定时 scrub 任务，以检查 checksum 与实际内容是否一致。Scrub 可以在运行时执行，但是不检查结构是否正确。

关闭 CoW

:   对于部分应用场景（例如数据库、虚拟机镜像），Btrfs 的 CoW 特性可能会带来性能问题。可以对文件使用 `chattr +C` 命令关闭 CoW 特性。

### ZFS

参见 [ZFS](./zfs.md)。

[^sector]: 当然了，「扇区」的概念在现代磁盘，特别是固态硬盘上已经不再准确，但是这里仍然使用这个习惯性的术语。
[^sector-size]: 扇区的大小（特别是现代磁盘在实际物理上）不一定是 512 字节，但在实际创建分区时，一般都是以 512 字节为单位。
[^xfs_growfs]: [xfs_growfs(8)][xfs_growfs.8]: A filesystem with only 1 AG cannot be shrunk further, and a filesystem cannot be shrunk to the point where it would only have 1 AG.
