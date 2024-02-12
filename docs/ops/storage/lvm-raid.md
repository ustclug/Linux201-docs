# LVM 与 RAID

!!! warning "本文仍在编辑中"

本文将介绍 LVM，以及常见的 RAID 方案的使用与维护。

## LVM

LVM（Logical Volume Manager）是 Linux 下的逻辑卷管理器，相比于直接在创建分区表后使用分区，LVM 提供了更加灵活的存储管理方式：

- LVM 可以管理多个硬盘（物理卷）上的存储空间
- LVM 中的逻辑卷可以跨越多个物理卷，文件系统不需要关心物理卷的位置
- LVM 的逻辑卷可以动态调整大小，而不需要移动分区的位置——移动分区的起始位置是一个危险且耗时的操作

一些 Linux 发行版的安装程序默认使用 LVM 来管理磁盘，例如 Fedora、CentOS 等。

### 基础概念

LVM 中有三个基本概念：

- 物理卷（Physical Volume，PV）：通常是一块硬盘（分区）
- 卷组（Volume Group，VG）：由一个或多个物理卷组成
- 逻辑卷（Logical Volume，LV）：在卷组里分配的逻辑存储空间。称之为「逻辑」，是因为它可以跨越多个物理卷，也不一定是连续的

这里我们创建三个 1GB 的文件作为物理卷，并且加入到一个卷组中：

!!! warning "避免在物理磁盘上创建无分区表的文件系统/物理卷"

    在实践中，尽管没有什么阻止这么做，但是不创建分区表、直接将整个磁盘格式化为某个文件系统，或者加入 LVM 中是不建议的。
    这会给其他人带来困惑，并且如果未来有在对应磁盘上启动系统等需要多分区的需求，会带来很多麻烦（可能只能备份数据后从头再来）。

    直接对物理磁盘设备格式化为文件系统也是操作时常见的输入错误：

    ```console
    $ mkfs.ext4 /dev/sdz  # 错误 ❌
    $ mkfs.ext4 /dev/sdz1 # 正确 ✅
    ```

    在下面的例子中，为了简化操作，我们假设 pv[1-3].img 相当于每块硬盘上使用全部空间的分区。

```console
$ truncate -s 1G pv1.img pv2.img pv3.img
$ sudo losetup -f --show pv1.img
/dev/loop0
$ sudo losetup -f --show pv2.img
/dev/loop1
$ sudo losetup -f --show pv3.img
/dev/loop2
$ sudo pvcreate /dev/loop0 /dev/loop1 /dev/loop2  # 创建物理卷
  Physical volume "/dev/loop0" successfully created.
  Physical volume "/dev/loop1" successfully created.
  Physical volume "/dev/loop2" successfully created.
$ sudo vgcreate vg201-test /dev/loop0 /dev/loop1 /dev/loop2  # 创建卷组
  Volume group "vg201-test" successfully created
$ sudo pvs  # 查看物理卷信息
  PV         VG         Fmt  Attr PSize    PFree   
  /dev/loop0 vg201-test lvm2 a--  1020.00m 1020.00m
  /dev/loop1 vg201-test lvm2 a--  1020.00m 1020.00m
  /dev/loop2 vg201-test lvm2 a--  1020.00m 1020.00m
$ sudo vgs  # 查看卷组信息
  VG         #PV #LV #SN Attr   VSize  VFree 
  vg201-test   3   0   0 wz--n- <2.99g <2.99g
$ sudo lvcreate -n lvol0 -L 2.5G vg201-test  # 创建一个 2.5G 的逻辑卷
  Logical volume "lvol0" created.
$ sudo lvs  # 查看逻辑卷信息
  LV    VG         Attr       LSize Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvol0 vg201-test -wi-a----- 2.50g
$ ls -lh /dev/mapper/
total 0
crw------- 1 root root 10, 236 Feb 11 13:30 control
lrwxrwxrwx 1 root root       7 Feb 12 00:09 vg201--test-lvol0 -> ../dm-0
$ # /dev/mapper/vg201--test-lvol0 就是我们创建的逻辑卷（块设备），可以在上面创建文件系统。
$ sudo lvchange -an vg201-test/lvol0  # 取消激活 (disactivate) 刚才创建的逻辑卷
$ sudo lvs
  LV    VG         Attr       LSize Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvol0 vg201-test -wi------- 2.50g 
$ sudo losetup -D  # 卸载本地回环
```

之后再次挂载：

```console
$ sudo losetup -f --show pv1.img
/dev/loop0
$ sudo losetup -f --show pv2.img
/dev/loop1
$ sudo losetup -f --show pv3.img
/dev/loop2
$ sudo pvs  # 可以看到物理卷被自动识别了
  PV         VG         Fmt  Attr PSize    PFree  
  /dev/loop0 vg201-test lvm2 a--  1020.00m      0 
  /dev/loop1 vg201-test lvm2 a--  1020.00m      0 
  /dev/loop2 vg201-test lvm2 a--  1020.00m 500.00m
$ sudo lvchange -ay vg201-test/lvol0  # 激活 LV
$ sudo lvs
  LV    VG         Attr       LSize Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvol0 vg201-test -wi-a----- 2.50g
```

!!! note "等等，怎么每块盘少了几 MB 空间？"

    其实大概可以猜到，这些空间留给了 LVM 的元数据。LVM 的元数据为**纯文本**格式，可以存储相对复杂的信息，但是也带来了下述两个问题：

    - LVM 的元数据格式没有书面的标准，因此其他软件在解析 LVM 元数据时可能会出现问题。[科大镜像站的机器就遇到过 GRUB 解析 LVM 元数据代码的问题](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=985974)，导致无法正确配置启动器。
    这个问题直到现在都没有被 GRUB 修复，因此只能自行编译手动修复后的版本，并且固定 GRUB 版本。
    - LVM 的纯文本格式导致元数据本身较大，如果预分配的元数据空间不足，并且卷组中有大量逻辑卷（默认值 + 上千个 LV 就会出现问题），那么最后会导致无法再创建/扩容逻辑卷，并且只能通过添加新的物理卷，然后由该卷存储元数据来解决问题。[Vlab 项目曾遇到过这样的问题](https://vlab.ibugone.com/records/2022-06-16/)。

!!! note "这里创建的逻辑卷横跨了三块盘，所以 LVM 默认是 RAID 0？"

    这是不正确的。这里逻辑卷的数据布局与 RAID 0 不同。RAID 0 考虑的是性能，因此数据类似于这么存储：

    | Disk 1 | Disk 2 | Disk 3 |
    | ------ | ------ | ------ |
    | 0      | 1      | 2      |
    | 3      | 4      | 5      |
    | 6      | 7      | 8      |
    | ...    | ...    | ...    |

    这样的话，应用程序顺序读写时，就可以利用多块盘的并行读写能力。但是 LVM 类似于这样：

    | Disk 1 | Disk 2 | Disk 3 |
    | ------ | ------ | ------ |
    | 0      | 100000 | 200000 |
    | 1      | 100001 | 200001 |
    | 2      | 100002 | 200002 |
    | ...    | ...    | ...    |

    每块盘是顺序填充的。这样做可以更加灵活地管理空间，但是性能不如 RAID 0。

    LVM 也提供了创建 RAID 0 逻辑卷的功能，被称为「条带化」（Striped）卷，上面默认生成的被称为「线性」（Linear）卷。

### 创建 RAID

当然了，对于多盘场景，上面的例子显然是不满足需求的：创建出的逻辑卷仍然是有一块盘坏掉就会故障的状态。
以下展示了 RAID0, 1, 5 的创建方式：

```console
$ sudo lvremove vg201-test/lvol0  # 删除刚才的 LV，腾出一些空间
Do you really want to remove active logical volume vg201-test/lvol0? [y/n]: y
  Logical volume "lvol0" successfully removed.
$ # RAID 0 (striped)。--stripes 参数指定了条带的数量，正常情况下和盘数量一致
$ sudo lvcreate -n lvraid0 -L 0.5G --type striped --stripes 3 vg201-test
  Using default stripesize 64.00 KiB.
  Logical volume "lvraid0" created.
$ # RAID 1 (mirror)。--mirrors 参数指定了副本数量（不含本体），所以是盘数量减一
$ sudo lvcreate -n lvraid1 -L 0.5G --type mirror --mirrors 2 vg201-test
  Logical volume "lvraid1" created.
$ # 因为只有 3 块盘，这里展示 RAID 5。--stripes 参数不包含额外的验证盘。
$ sudo lvcreate -n lvraid5 -L 0.2G --type raid5 --stripes 2 vg201-test
  Using default stripesize 64.00 KiB.
  Rounding up size to full physical extent 208.00 MiB
  Logical volume "lvraid5" created.
$ sudo lvs
  LV      VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log            Cpy%Sync Convert
  lvraid0 vg201-test -wi-a----- 516.00m                                                               
  lvraid1 vg201-test mwi-a-m--- 512.00m                                [lvraid1_mlog] 100.00          
  lvraid5 vg201-test rwi-a-r--- 208.00m                                               100.00
```

!!! note "Extent 是多大"

    有时在输入错误的参数之后，会出现 extent 不足的提示，类似于这样：

    ```console
    $ # --mirrors 参数多了一，空间不够
    $ sudo lvcreate -n lvraid1 -L 0.5G --type mirror --mirrors 3 vg201-test
      Insufficient suitable allocatable extents for logical volume lvraid1: 512 more required
    ```

    但是 "extent" 是多大呢？在 LVM 中，有两种 extent: PE（Physical Extent）和 LE（Logical Extent），
    对应物理卷和逻辑卷的大小参数。这里指的是 PE，可以使用 `pvdisplay` 或 `vgdisplay` 查看。

    ```console
    $ sudo vgdisplay
      --- Volume group ---
      VG Name               vg201-test
      System ID             
      Format                lvm2
      Metadata Areas        3
      Metadata Sequence No  11
      VG Access             read/write
      VG Status             resizable
      MAX LV                0
      Cur LV                2
      Open LV               0
      Max PV                0
      Cur PV                3
      Act PV                3
      VG Size               <2.99 GiB
      PE Size               4.00 MiB
      Total PE              765
      Alloc PE / Size       514 / <2.01 GiB
      Free  PE / Size       251 / 1004.00 MiB
      VG UUID               Ybsskf-2giI-Q5PU-LCof-Irr9-EDud-nlB0Ms
    $ sudo pvdisplay
      --- Physical volume ---
      PV Name               /dev/loop0
      VG Name               vg201-test
      PV Size               1.00 GiB / not usable 4.00 MiB
      Allocatable           yes 
      PE Size               4.00 MiB
      Total PE              255
      Free PE               84
      Allocated PE          171
      PV UUID               DBn9ke-9UfO-tZJA-ymSh-GQtP-jMq8-tSm62B
      
      --- Physical volume ---
      PV Name               /dev/loop1
      VG Name               vg201-test
      PV Size               1.00 GiB / not usable 4.00 MiB
      Allocatable           yes 
      PE Size               4.00 MiB
      Total PE              255
      Free PE               84
      Allocated PE          171
      PV UUID               aut3hf-J6Tl-O5Gq-0TIw-bneD-mfzr-8wMJJx
      
      --- Physical volume ---
      PV Name               /dev/loop2
      VG Name               vg201-test
      PV Size               1.00 GiB / not usable 4.00 MiB
      Allocatable           yes 
      PE Size               4.00 MiB
      Total PE              255
      Free PE               83
      Allocated PE          172
      PV UUID               AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ
    ```

    可以看到 PE 是 4M，因此缺少 512 个 extent 指缺少 512 * 4M = 2048M = 2G 空间。
    这里是因为 PV 数量不足，所以无法找到能够存储第四份副本的磁盘。

`lvs` 支持指定参数查看 LV 的其他信息，这里我们查看逻辑卷实际使用的物理卷：

```console
$ sudo lvs -a -o +devices vg201-test
  LV                 VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log            Cpy%Sync Convert Devices                                                    
  lvraid0            vg201-test -wi-a----- 516.00m                                                                /dev/loop0(0),/dev/loop1(0),/dev/loop2(0)                  
  lvraid1            vg201-test mwi-a-m--- 512.00m                                [lvraid1_mlog] 100.00           lvraid1_mimage_0(0),lvraid1_mimage_1(0),lvraid1_mimage_2(0)
  [lvraid1_mimage_0] vg201-test iwi-aom--- 512.00m                                                                /dev/loop0(43)                                             
  [lvraid1_mimage_1] vg201-test iwi-aom--- 512.00m                                                                /dev/loop1(43)                                             
  [lvraid1_mimage_2] vg201-test iwi-aom--- 512.00m                                                                /dev/loop2(43)                                             
  [lvraid1_mlog]     vg201-test lwi-aom---   4.00m                                                                /dev/loop2(171)                                            
  lvraid5            vg201-test rwi-a-r--- 208.00m                                               100.00           lvraid5_rimage_0(0),lvraid5_rimage_1(0),lvraid5_rimage_2(0)
  [lvraid5_rimage_0] vg201-test iwi-aor--- 104.00m                                                                /dev/loop0(172)                                            
  [lvraid5_rimage_1] vg201-test iwi-aor--- 104.00m                                                                /dev/loop1(172)                                            
  [lvraid5_rimage_2] vg201-test iwi-aor--- 104.00m                                                                /dev/loop2(173)                                            
  [lvraid5_rmeta_0]  vg201-test ewi-aor---   4.00m                                                                /dev/loop0(171)                                            
  [lvraid5_rmeta_1]  vg201-test ewi-aor---   4.00m                                                                /dev/loop1(171)                                            
  [lvraid5_rmeta_2]  vg201-test ewi-aor---   4.00m                                                                /dev/loop2(172)
```

??? note "mimage, mlog, rimage, rmeta"

    可以观察到，列表中出现了一些默认隐藏的逻辑卷，它们是创建 RAID 1 (mirror) 或 RAID 5/6 的产物：

    - mimage: "mirrored image"，数据写入时，会向每个关联的 mimage 写入数据
    - mlog: 存储了 RAID 1 的盘之间的同步状态信息
    - rimage: "RAID image"，代表了实际存储数据（以及校验信息）的逻辑卷
    - rmeta: 存储了 RAID 的元数据信息
