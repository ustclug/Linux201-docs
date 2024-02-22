# RAID

本文介绍常见的 RAID 方案的使用与维护。
直接使用 LVM 创建 RAID 的方法请参考 [LVM](./lvm.md)；
使用 ZFS 创建 RAID (raidz) 的方法请参考 [ZFS](./zfs.md)。

本部分不涉及 FakeRAID（例如 Intel Rapid Storage Technology）。
建议阅读以下内容前，先阅读 [LVM](./lvm.md) 中与 RAID 相关的部分。

## mdadm

mdadm 是 Linux 上最常用的软件 RAID 方案。
在下面的步骤中，与 LVM 一章类似，我们使用本地回环创建三个块设备。
同样地，在实际使用中，强烈建议先分区再创建 RAID。

```console
$ truncate -s 1G md0.img md1.img md2.img
$ sudo losetup -f --show md0.img
/dev/loop0
$ sudo losetup -f --show md1.img
/dev/loop1
$ sudo losetup -f --show md2.img
/dev/loop2
```

### 创建 RAID

我们先以 RAID 0 为例，创建一个跨 3 块盘的 RAID 0。

```console
$ sudo mdadm --create /dev/md0 --level=0 --raid-devices=3 /dev/loop0 /dev/loop1 /dev/loop2
mdadm: Defaulting to version 1.2 metadata
mdadm: array /dev/md0 started.
```

得到的 `/dev/md0` 就是创建完成的 RAID 块设备，它的大小是约 3G，可以使用 `mdadm --detail` 查看详细信息。

```console
$ sudo mdadm --detail /dev/md0
/dev/md0:
           Version : 1.2
     Creation Time : Wed Feb 21 00:54:02 2024
        Raid Level : raid0
        Array Size : 3139584 (2.99 GiB 3.21 GB)
      Raid Devices : 3
     Total Devices : 3
       Persistence : Superblock is persistent

       Update Time : Wed Feb 21 00:54:02 2024
             State : clean 
    Active Devices : 3
   Working Devices : 3
    Failed Devices : 0
     Spare Devices : 0

            Layout : -unknown-
        Chunk Size : 512K

Consistency Policy : none

              Name : hostname:0  (local to host hostname)
              UUID : 119661ca:ff0a76b7:28909e39:18af76dc
            Events : 0

    Number   Major   Minor   RaidDevice State
       0       7        0        0      active sync   /dev/loop0
       1       7        1        1      active sync   /dev/loop1
       2       7        2        2      active sync   /dev/loop2
```

对应的状态也可以通过 `/proc/mdstat` 查看：

```console
$ cat /proc/mdstat
Personalities : [raid6] [raid5] [raid4] [raid1] [raid0] 
md0 : active raid0 loop2[2] loop1[1] loop0[0]
      3139584 blocks super 1.2 512k chunks
      
unused devices: <none>
```

使用 `--stop` 选项停止 RAID：

```console
$ sudo mdadm --stop /dev/md0
mdadm: stopped /dev/md0
$ ls -lha /dev/md0
ls: cannot access '/dev/md0': No such file or directory
```

在 stop 之后，如果需要再恢复，可以使用 `--assemble` 选项：

```console
$ sudo mdadm --assemble /dev/md0 /dev/loop0 /dev/loop1 /dev/loop2
mdadm: /dev/md0 has been started with 3 drives.
$ # 或者使用 --scan 参数：
$ sudo mdadm --assemble --scan
mdadm: /dev/md/0 has been started with 3 drives.
```

将这个 RAID 0 拆掉，然后试试组建 RAID 1、RAID 5：

```console
$ # RAID 1
$ sudo mdadm --stop /dev/md0
mdadm: stopped /dev/md0
$ sudo mdadm --misc --zero-superblock /dev/loop0 /dev/loop1 /dev/loop2
$ sudo mdadm --create /dev/md0 --level=1 --raid-devices=3 /dev/loop0 /dev/loop1 /dev/loop2
mdadm: Note: this array has metadata at the start and
    may not be suitable as a boot device.  If you plan to
    store '/boot' on this device please ensure that
    your boot-loader understands md/v1.x metadata, or use
    --metadata=0.90
Continue creating array? y
mdadm: Defaulting to version 1.2 metadata
mdadm: array /dev/md0 started.
$ # RAID 5
$ sudo mdadm --stop /dev/md0
mdadm: stopped /dev/md0
$ sudo mdadm --misc --zero-superblock /dev/loop0 /dev/loop1 /dev/loop2
$ sudo mdadm --create /dev/md0 --level=5 --raid-devices=3 /dev/loop0 /dev/loop1 /dev/loop2
mdadm: Defaulting to version 1.2 metadata
mdadm: array /dev/md0 started.
```

如果在重新创建 mdadm 阵列之前不清空 superblock，会输出类似以下的警告信息：

```console
mdadm: /dev/loop0 appears to be part of a raid array:
       level=raid0 devices=3 ctime=Wed Feb 21 00:54:02 2024
mdadm: /dev/loop1 appears to be part of a raid array:
       level=raid0 devices=3 ctime=Wed Feb 21 00:54:02 2024
mdadm: /dev/loop2 appears to be part of a raid array:
       level=raid0 devices=3 ctime=Wed Feb 21 00:54:02 2024
```

此外，尽管这里不展示 RAID10 的创建过程，但是 mdadm 的 RAID10 涉及到 near, far 和 offset 三种布局的选择。
详细的介绍可参考 [md(4)][md.4] 的 "About the RAID10 Layout Examples" 部分。

### 重建操作

与 LVM 一章类似，这里展示在一块盘丢失（损坏）情况下的操作：

```console
$ sudo mdadm --stop /dev/md0
mdadm: stopped /dev/md0
$ sudo losetup -D
$ sudo losetup -f --show md0.img
/dev/loop0
$ sudo losetup -f --show md1.img
/dev/loop1
$ # 此时 /dev/md0 已经自动构建，并且处于丢失一块盘的状态
$ sudo mdadm --detail /dev/md0
/dev/md0:
           Version : 1.2
     Creation Time : Thu Feb 22 13:05:14 2024
        Raid Level : raid5
        Array Size : 2093056 (2044.00 MiB 2143.29 MB)
     Used Dev Size : 1046528 (1022.00 MiB 1071.64 MB)
      Raid Devices : 3
     Total Devices : 2
       Persistence : Superblock is persistent

       Update Time : Thu Feb 22 13:05:19 2024
             State : clean, degraded 
    Active Devices : 2
   Working Devices : 2
    Failed Devices : 0
     Spare Devices : 0

            Layout : left-symmetric
        Chunk Size : 512K

Consistency Policy : resync

              Name : hostname:0  (local to host hostname)
              UUID : 3e4455f5:65e4251c:b21c1c81:13b44a8b
            Events : 18

    Number   Major   Minor   RaidDevice State
       0       7        0        0      active sync   /dev/loop0
       1       7        1        1      active sync   /dev/loop1
       -       0        0        2      removed
$ # 添加新的盘
$ truncate -s 1G md3.img
$ sudo losetup /dev/loop3 md3.img
$ sudo mdadm --add /dev/md0 /dev/loop3
$ sudo mdadm --detail /dev/md0
/dev/md0:
           Version : 1.2
     Creation Time : Thu Feb 22 13:05:14 2024
        Raid Level : raid5
        Array Size : 2093056 (2044.00 MiB 2143.29 MB)
     Used Dev Size : 1046528 (1022.00 MiB 1071.64 MB)
      Raid Devices : 3
     Total Devices : 3
       Persistence : Superblock is persistent

       Update Time : Thu Feb 22 13:52:32 2024
             State : clean, degraded, recovering 
    Active Devices : 2
   Working Devices : 3
    Failed Devices : 0
     Spare Devices : 1

            Layout : left-symmetric
        Chunk Size : 512K

Consistency Policy : resync

    Rebuild Status : 35% complete

              Name : hostname:0  (local to host hostname)
              UUID : 3e4455f5:65e4251c:b21c1c81:13b44a8b
            Events : 26

    Number   Major   Minor   RaidDevice State
       0       7        0        0      active sync   /dev/loop0
       1       7        1        1      active sync   /dev/loop1
       3       7        3        2      spare rebuilding   /dev/loop3
```

添加新盘后，可以看到重建操作会自动开始。

### 完整性检查

这里展示三盘 RAID 1 下进行检查与修复的场景：

```console
$ sudo mdadm --stop /dev/md0
mdadm: stopped /dev/md0
$ sudo mdadm --misc --zero-superblock /dev/loop0 /dev/loop1 /dev/loop3
$ sudo mdadm --create /dev/md0 --level=1 --raid-devices=3 /dev/loop0 /dev/loop1 /dev/loop3
mdadm: Note: this array has metadata at the start and
    may not be suitable as a boot device.  If you plan to
    store '/boot' on this device please ensure that
    your boot-loader understands md/v1.x metadata, or use
    --metadata=0.90
Continue creating array? y
mdadm: Defaulting to version 1.2 metadata
mdadm: array /dev/md0 started.
$ # 向其中一块盘写入垃圾数据
$ sudo dd if=/dev/urandom of=/dev/loop0 bs=1M count=1 oseek=100
1+0 records in
1+0 records out
1048576 bytes (1.0 MB, 1.0 MiB) copied, 0.00406889 s, 258 MB/s
$ sudo bash -c 'echo check > /sys/block/md0/md/sync_action'
$ # 在 /proc/mdstat 中可以看到检查的进度
$ cat /proc/mdstat
Personalities : [raid6] [raid5] [raid4] [raid1] [raid0] 
md0 : active raid1 loop3[2] loop1[1] loop0[0]
      1046528 blocks super 1.2 [3/3] [UUU]
      [===================>.]  check = 95.3% (998016/1046528) finish=0.0min speed=249504K/sec
      
unused devices: <none>
$ # 由于我们这里盘很小，所以检查很快就结束了
$ cat /sys/block/md0/md/mismatch_cnt  # 获取不一致的块数
4096
$ # 由于我们有足够多的副本，可以尝试修复
$ sudo bash -c 'echo repair > /sys/block/md0/md/sync_action'
$ # 在 /proc/mdstat 中也可以看到修复的进度
$ cat /proc/mdstat
Personalities : [raid6] [raid5] [raid4] [raid1] [raid0] 
md0 : active raid1 loop3[2] loop1[1] loop0[0]
      1046528 blocks super 1.2 [3/3] [UUU]
      [===========>.........]  resync = 57.4% (601984/1046528) finish=0.0min speed=300992K/sec
      
unused devices: <none>
$ # 修复完成后，mismatch_cnt 中仍然记录的是不一致的数量
$ # 再执行一次 check 后 mismatch_cnt 值会变为 0
```

## 硬件 RAID 方案

不同的服务器可能提供了不同的硬件 RAID 方案，目前最常见的是 MegaRAID 方案。
在服务器启动时，按下指定的按键，可以进入 RAID 卡的设置界面进行操作。

??? example "图片：可能会看到的界面"

    <figure markdown="span">
      ![MegaRAID Utility](https://docs.oracle.com/cd/E41059_01/html/E48312/figures/adapter_selection.jpg)
      <figcaption>MegaRAID 在开机时可以选择进入的设置页面</figcaption>
    </figure>

同时，硬件 RAID 厂商一般会提供私有的工具进行管理，例如 MegaRAID 可以使用 `megacli` 或 `storcli`，
HPE 的 Smart Array 可以使用 `ssacli` 等。
这些软件 Linux 发行版不自带，需要自行下载安装。

以下介绍 MegaRAID 相关的一些操作。

### 获取管理软件

### 基础概念

### 维护操作

## RAID 与文件系统

## 监控
