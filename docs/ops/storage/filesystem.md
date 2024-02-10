# 分区与文件系统

## 相关概念

- 块设备：常见的磁盘设备的读写均以块（而不是字节）为单位，因此在 Linux 中，设备文件分为块设备和字符设备两种。

    可以使用 `lsblk` 命令查看系统中的块设备。一个桌面系统的例子如下：

    ```console
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

- 分区表：一个块设备上可以有一个或多个分区，而分区表则记录了分区的信息，常见的分区表有 MBR 和 GPT 两种。

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

- 文件系统：每个分区需要被格式化成某种文件系统后，才能存储文件。

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
