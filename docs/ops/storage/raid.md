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

使用 `--stop` 选项停止 RAID：

```console
$ sudo mdadm --stop /dev/md0
mdadm: stopped /dev/md0
$ ls -lha /dev/md0
ls: cannot access '/dev/md0': No such file or directory
```
