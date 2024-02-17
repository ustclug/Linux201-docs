# LVM 与 RAID

!!! warning "本文仍在编辑中"

本文将介绍 LVM，以及常见的 RAID 方案的使用与维护。

## LVM

LVM（Logical Volume Manager）是 Linux 下的逻辑卷管理器，基于内核的 device mapper（dm）功能。
相比于直接在创建分区表后使用分区，LVM 提供了更加灵活的存储管理方式：

- LVM 可以管理多个硬盘（物理卷）上的存储空间
- LVM 中的逻辑卷可以跨越多个物理卷，文件系统不需要关心物理卷的位置
- LVM 的逻辑卷可以动态调整大小，而不需要移动分区的位置——移动分区的起始位置是一个危险且耗时的操作

一些 Linux 发行版的安装程序默认使用 LVM 来管理磁盘，例如 Fedora、CentOS 等。如果需要实际使用 LVM，也推荐阅读来自[红帽 RHEL 的 LVM 管理指南](https://access.redhat.com/documentation/zh-cn/red_hat_enterprise_linux/9/html-single/configuring_and_managing_logical_volumes/index#doc-wrapper)[^rhel-version]。

!!! warning "本部分无法涵盖全部内容"

    LVM 包含了很多功能，在本份文档中不可能面面俱到，因此我们仅介绍在 LUG 与 Vlab 项目中使用过的功能。

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

!!! warning "不建议使用 LVM 构建 RAID"

    相比于 mdadm，LVM 与 RAID 相关的概念与提供的工具更加复杂，并且这种复杂性在很多场景下没有收益。
    更加常见的模式是，使用 mdadm 构建 RAID，然后使用 LVM 管理构建好的 RAID 上的逻辑卷。

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
$ # RAID 1。--mirrors 参数指定了副本数量（不含本体），所以是盘数量减一
$ sudo lvcreate -n lvraid1 -L 0.5G --type raid1 --mirrors 2 vg201-test
  Logical volume "lvraid1" created.
$ # 因为只有 3 块盘，这里展示 RAID 5。--stripes 参数不包含额外的验证盘。
$ sudo lvcreate -n lvraid5 -L 0.2G --type raid5 --stripes 2 vg201-test
  Using default stripesize 64.00 KiB.
  Rounding up size to full physical extent 208.00 MiB
  Logical volume "lvraid5" created.
$ sudo lvs
  LV      VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvraid0 vg201-test -wi-a----- 516.00m                                                    
  lvraid1 vg201-test rwi-a-r--- 512.00m                                    100.00          
  lvraid5 vg201-test rwi-a-r--- 208.00m                                    100.00
```

!!! warning "不要使用 `--type mirror`"

    `mirror` 和 `raid1` 是两个**不同**的 type。除非有特殊需要，否则应该使用 `--type raid1` 创建 RAID 1 阵列。
    可以使用 `lvconvert` 将 mirror 转换为 raid1。
    
    相关讨论可查看 [In what case(s) will `--type mirror` continue to be a good choice / is not deprecated?](https://unix.stackexchange.com/questions/697364/in-what-cases-will-type-mirror-continue-to-be-a-good-choice-is-not-depre)。

    在后文的缺盘测试中，`mirror` 的行为也与预期不同——LVM 默认会拒绝挂载，如果强行挂载，会直接将缺失的盘丢掉。

!!! note "Extent 是多大"

    有时在输入错误的参数之后，会出现 extent 不足的提示，类似于这样：

    ```console
    $ # --mirrors 参数多了一，空间不够
    $ sudo lvcreate -n lvraid1 -L 0.5G --type raid1 --mirrors 3 vg201-test
      Insufficient suitable allocatable extents for logical volume lvraid1: 516 more required
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

    可以看到 PE 是 4M，因此缺少 516 个 extent 指缺少 516 * 4M ~= 2G 空间。
    这里是因为 PV 数量不足，所以无法找到能够存储第四份副本的磁盘。

`lvs` 支持指定参数查看 LV 的其他信息，这里我们查看逻辑卷实际使用的物理卷：

```console
$ sudo lvs -a -o +devices vg201-test
  LV                 VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert Devices                                                    
  lvraid0            vg201-test -wi-a----- 516.00m                                                     /dev/loop0(0),/dev/loop1(0),/dev/loop2(0)                  
  lvraid1            vg201-test rwi-a-r--- 512.00m                                    100.00           lvraid1_rimage_0(0),lvraid1_rimage_1(0),lvraid1_rimage_2(0)
  [lvraid1_rimage_0] vg201-test iwi-aor--- 512.00m                                                     /dev/loop0(44)                                             
  [lvraid1_rimage_1] vg201-test iwi-aor--- 512.00m                                                     /dev/loop1(44)                                             
  [lvraid1_rimage_2] vg201-test iwi-aor--- 512.00m                                                     /dev/loop2(44)                                             
  [lvraid1_rmeta_0]  vg201-test ewi-aor---   4.00m                                                     /dev/loop0(43)                                             
  [lvraid1_rmeta_1]  vg201-test ewi-aor---   4.00m                                                     /dev/loop1(43)                                             
  [lvraid1_rmeta_2]  vg201-test ewi-aor---   4.00m                                                     /dev/loop2(43)                                             
  lvraid5            vg201-test rwi-a-r--- 208.00m                                    100.00           lvraid5_rimage_0(0),lvraid5_rimage_1(0),lvraid5_rimage_2(0)
  [lvraid5_rimage_0] vg201-test iwi-aor--- 104.00m                                                     /dev/loop0(173)                                            
  [lvraid5_rimage_1] vg201-test iwi-aor--- 104.00m                                                     /dev/loop1(173)                                            
  [lvraid5_rimage_2] vg201-test iwi-aor--- 104.00m                                                     /dev/loop2(173)                                            
  [lvraid5_rmeta_0]  vg201-test ewi-aor---   4.00m                                                     /dev/loop0(172)                                            
  [lvraid5_rmeta_1]  vg201-test ewi-aor---   4.00m                                                     /dev/loop1(172)                                            
  [lvraid5_rmeta_2]  vg201-test ewi-aor---   4.00m                                                     /dev/loop2(172)
```

??? note "rimage, rmeta（与 mimage, mlog）"

    可以观察到，列表中出现了一些默认隐藏的逻辑卷，它们是创建 RAID 1/5/6 的产物：

    - rimage: "RAID image"，代表了实际存储数据（以及校验信息）的逻辑卷
    - rmeta: 存储了 RAID 的元数据信息

    如果在创建 RAID 1 时选择了 `--type mirror`，那么对应创建的是 mimage 和 mlog：

    - mimage: "mirrored image"，数据写入时，会向每个关联的 mimage 写入数据
    - mlog: 存储了 RAID 1 的盘之间的同步状态信息

### RAID 维护

#### RAID 状态与重建

正常情况下，`lvs` 返回的 RAID 1/5/6 设备的 "Cpy%Sync" 应该是 100.00，表示数据已经同步到所有盘上。
并且 `health_status` 属性应该为空。这里模拟强制删除一块盘的情况：

```console
$ sudo vgchange -an vg201-test
  0 logical volume(s) in volume group "vg201-test" now active
$ sudo losetup -D
$ # 接下来只挂载两块盘
$ sudo losetup -f --show pv1.img
/dev/loop0
$ sudo losetup -f --show pv2.img
/dev/loop1
$ sudo pvs
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to /dev/loop2).
  PV         VG         Fmt  Attr PSize    PFree  
  /dev/loop0 vg201-test lvm2 a--  1020.00m 228.00m
  /dev/loop1 vg201-test lvm2 a--  1020.00m 228.00m
  [unknown]  vg201-test lvm2 a-m  1020.00m 224.00m
$ sudo vgchange -ay vg201-test
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to /dev/loop2).
  Refusing activation of partial LV vg201-test/lvraid0.  Use '--activationmode partial' to override.
  2 logical volume(s) in volume group "vg201-test" now active
$ sudo lvs -a -o name,copy_percent,health_status,devices vg201-test
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to /dev/loop2).
  LV                 Cpy%Sync Health          Devices                                                    
  lvraid0                     partial         /dev/loop0(0),/dev/loop1(0),[unknown](0)                   
  lvraid1            100.00   partial         lvraid1_rimage_0(0),lvraid1_rimage_1(0),lvraid1_rimage_2(0)
  [lvraid1_rimage_0]                          /dev/loop0(44)                                             
  [lvraid1_rimage_1]                          /dev/loop1(44)                                             
  [lvraid1_rimage_2]          partial         [unknown](44)                                              
  [lvraid1_rmeta_0]                           /dev/loop0(43)                                             
  [lvraid1_rmeta_1]                           /dev/loop1(43)                                             
  [lvraid1_rmeta_2]           partial         [unknown](43)                                              
  lvraid5            100.00   partial         lvraid5_rimage_0(0),lvraid5_rimage_1(0),lvraid5_rimage_2(0)
  [lvraid5_rimage_0]                          /dev/loop0(173)                                            
  [lvraid5_rimage_1]                          /dev/loop1(173)                                            
  [lvraid5_rimage_2]          partial         [unknown](173)                                             
  [lvraid5_rmeta_0]                           /dev/loop0(172)                                            
  [lvraid5_rmeta_1]                           /dev/loop1(172)                                            
  [lvraid5_rmeta_2]           partial         [unknown](172)
```

可以发现：

- RAID 0 由于缺少一块盘，LVM 会拒绝激活
- RAID 1/5 可以激活，但是 health_status 为 partial，表示对应阵列处于不完整的状态

假设我们添加一块新盘，并删除旧盘，进行 RAID 1/5 的重建：

```console
$ truncate -s 1G pv4.img
$ sudo losetup /dev/loop3 pv4.img
$ sudo pvcreate /dev/loop3
  Physical volume "/dev/loop3" successfully created.
$ sudo vgextend vg201-test /dev/loop3
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to /dev/loop2).
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  Volume group "vg201-test" successfully extended
$ sudo lvconvert --repair vg201-test/lvraid1
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to [unknown]).
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
Attempt to replace failed RAID images (requires full device resync)? [y/n]: y
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  Faulty devices in vg201-test/lvraid1 successfully replaced.
$ sudo lvconvert --repair vg201-test/lvraid5
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to [unknown]).
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
Attempt to replace failed RAID images (requires full device resync)? [y/n]: y
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  Faulty devices in vg201-test/lvraid5 successfully replaced.
$ sudo lvs -a -o name,copy_percent,health_status,devices vg201-test
  WARNING: Couldn't find device with uuid AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test is missing PV AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ (last written to [unknown]).
  LV                 Cpy%Sync Health          Devices                                                    
  lvraid0                     partial         /dev/loop0(0),/dev/loop1(0),[unknown](0)                   
  lvraid1            100.00                   lvraid1_rimage_0(0),lvraid1_rimage_1(0),lvraid1_rimage_2(0)
  [lvraid1_rimage_0]                          /dev/loop0(44)                                             
  [lvraid1_rimage_1]                          /dev/loop1(44)                                             
  [lvraid1_rimage_2]                          /dev/loop3(1)                                              
  [lvraid1_rmeta_0]                           /dev/loop0(43)                                             
  [lvraid1_rmeta_1]                           /dev/loop1(43)                                             
  [lvraid1_rmeta_2]                           /dev/loop3(0)                                              
  lvraid5            100.00                   lvraid5_rimage_0(0),lvraid5_rimage_1(0),lvraid5_rimage_2(0)
  [lvraid5_rimage_0]                          /dev/loop0(173)                                            
  [lvraid5_rimage_1]                          /dev/loop1(173)                                            
  [lvraid5_rimage_2]                          /dev/loop3(130)                                            
  [lvraid5_rmeta_0]                           /dev/loop0(172)                                            
  [lvraid5_rmeta_1]                           /dev/loop1(172)                                            
  [lvraid5_rmeta_2]                           /dev/loop3(129)
```

下面展示将原始的 `/dev/loop2` 恢复回 vg201-test 的过程，以「恢复」最后的 RAID 0。
通过使用 `vgextend` 的 `--restoremissing` 参数，我们不需要重新初始化 `/dev/loop2`，而是直接将其加入到卷组中。
**只在确定原始的 PV 没有被修改的情况下才能如此操作**。

```console
$ sudo losetup /dev/loop2 pv3.img
$ sudo pvs
  WARNING: ignoring metadata seqno 37 on /dev/loop2 for seqno 43 on /dev/loop0 for VG vg201-test.
  WARNING: Inconsistent metadata found for VG vg201-test.
  See vgck --updatemetadata to correct inconsistency.
  WARNING: VG vg201-test was previously updated while PV /dev/loop2 was missing.
  WARNING: VG vg201-test was missing PV /dev/loop2 AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  PV         VG         Fmt  Attr PSize    PFree  
  /dev/loop0 vg201-test lvm2 a--  1020.00m 224.00m
  /dev/loop1 vg201-test lvm2 a--  1020.00m 224.00m
  /dev/loop2 vg201-test lvm2 a-m  1020.00m 848.00m
  /dev/loop3 vg201-test lvm2 a--  1020.00m 396.00m
$ sudo vgextend vg201-test /dev/loop2 --restoremissing
  WARNING: ignoring metadata seqno 37 on /dev/loop2 for seqno 43 on /dev/loop0 for VG vg201-test.
  WARNING: Inconsistent metadata found for VG vg201-test.
  See vgck --updatemetadata to correct inconsistency.
  WARNING: VG vg201-test was previously updated while PV /dev/loop2 was missing.
  WARNING: VG vg201-test was missing PV /dev/loop2 AQj8ej-EKps-ud3h-0KkP-wDxo-ZagG-ZJIdnZ.
  WARNING: VG vg201-test was previously updated while PV /dev/loop2 was missing.
  WARNING: updating old metadata to 44 on /dev/loop2 for VG vg201-test.
  Volume group "vg201-test" successfully extended
$ sudo lvs -a -o name,copy_percent,health_status,devices vg201-test
  LV                 Cpy%Sync Health          Devices                                                    
  lvraid0                                     /dev/loop0(0),/dev/loop1(0),/dev/loop2(0)                  
  lvraid1            100.00                   lvraid1_rimage_0(0),lvraid1_rimage_1(0),lvraid1_rimage_2(0)
  [lvraid1_rimage_0]                          /dev/loop0(44)                                             
  [lvraid1_rimage_1]                          /dev/loop1(44)                                             
  [lvraid1_rimage_2]                          /dev/loop3(1)                                              
  [lvraid1_rmeta_0]                           /dev/loop0(43)                                             
  [lvraid1_rmeta_1]                           /dev/loop1(43)                                             
  [lvraid1_rmeta_2]                           /dev/loop3(0)                                              
  lvraid5            100.00                   lvraid5_rimage_0(0),lvraid5_rimage_1(0),lvraid5_rimage_2(0)
  [lvraid5_rimage_0]                          /dev/loop0(173)                                            
  [lvraid5_rimage_1]                          /dev/loop1(173)                                            
  [lvraid5_rimage_2]                          /dev/loop3(130)                                            
  [lvraid5_rmeta_0]                           /dev/loop0(172)                                            
  [lvraid5_rmeta_1]                           /dev/loop1(172)                                            
  [lvraid5_rmeta_2]                           /dev/loop3(129)
```

#### 完整性检查

即使正常运行，RAID 也无法防止阵列中的某块硬盘因为某种原因数据不一致的情况（例如比特翻转），
因此**定期进行完整性检查（Scrub）是非常重要的**。以下展示一个没有定期 scrub 的反例：

> 有一个三块盘的 RAID1，因为某些神奇的误操作，其中一块盘的状态一直是 2018 年的，另两块是正确的 RAID1，然后这组盘被挪到了新机器，被重新加成了一个三盘的 RAID1，软 RAID 软件 somehow 没有做检查就跑了起来，于是读文件时有 1/3 概率读取到旧盘，也就是 ls 一下可能看到旧文件也可能看到新文件，可能这样用了很长一段时间一直没发现，昨天重启之后突然发现 glibc 回到了 2018 年

另一个没有 scrub 数据，最终导致文件丢失的例子是 Linus Tech Tips（[YouTube](https://www.youtube.com/watch?v=Npu7jkJk5nM)/[Bilibili](https://www.bilibili.com/video/BV1844y1W74r), 05:15）。

下面我们向 `pv4.img` 中间写入 1M 的随机数据，并展示 LVM 的检查与修复功能。

```console
$ sudo dd if=/dev/urandom of=/dev/loop3 bs=1M count=1 oseek=100
1+0 records in
1+0 records out
1048576 bytes (1.0 MB, 1.0 MiB) copied, 0.00402655 s, 260 MB/s
$ sudo lvs -o devices vg201-test
  LV      VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvraid0 vg201-test -wi------- 516.00m                                                    
  lvraid1 vg201-test rwi-a-r--- 512.00m                                    100.00          
  lvraid5 vg201-test rwi-a-r--- 208.00m                                    100.00
$ sudo lvchange --syncaction check vg201-test/lvraid1
$ sudo dmesg
（省略）
[1655658.162616] md: mdX: data-check done.
[1655663.533169] md: data-check of RAID array mdX
$ sudo lvs -o +raid_sync_action,raid_mismatch_count
  LV      VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert SyncAction Mismatches
  lvraid0 vg201-test -wi------- 516.00m                                                                          
  lvraid1 vg201-test rwi-a-r-m- 512.00m                                    100.00           idle             2048
  lvraid5 vg201-test rwi-a-r--- 208.00m                                    100.00           idle                0
$ # 因为我们的 RAID 1 有三块盘，所以这里的「不一致」还可以修复。
$ sudo lvchange --syncaction repair vg201-test/lvraid1
$ sudo dmesg
（省略）
[1655787.490037] md: requested-resync of RAID array mdX
[1655789.691174] md: mdX: requested-resync done.
$ sudo lvs -o +raid_sync_action,raid_mismatch_count
  LV      VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert SyncAction Mismatches
  lvraid0 vg201-test -wi------- 516.00m                                                                          
  lvraid1 vg201-test rwi-a-r--- 512.00m                                    100.00           idle                0
  lvraid5 vg201-test rwi-a-r--- 208.00m                                    100.00           idle                0
```

!!! note "dm-integrity"

    LVM 支持在设置 RAID 时添加 integrity 功能（`--raidintegrity`），这项功能为数据添加了校验和，
    LVM 在发现数据不一致时会在内核日志中报告，并在可以修复的情况下自动修复。

    这项功能不是 scrub 的替代品。

### SSD 缓存

LVM 支持将 SSD 作为 HDD 的缓存，以提高性能。以下介绍基于 dm-cache 的读写缓存。

!!! note "dm-writecache"

    本部分不介绍以优化写入为目的的 dm-writecache——我们没有相关的使用场景。

!!! note "缓存方案"

    目前内核自带这些缓存方案：

    - [bcache](https://wiki.archlinux.org/title/Bcache)：需要将 SSD 和 HDD 对应的块设备分区使用 `make-bcache` 初始化后，
    在 bcache 暴露的 `/dev/bcache0` 上进行操作。
    - [lvmcache](https://wiki.archlinux.org/title/LVM#Cache)：需要在 LVM 的基础上进行操作。基于内核的 dm-cache。

    此外，在 Linux 6.7（2024 年 1 月）之后，内核合并了 bcachefs 支持，它同样也包含了 SSD 缓存的功能。
    但是 bcachefs 的稳定性仍然需要至少数年的时间来验证。ZFS 同样也包含缓存功能（ARC 与 L2ARC），将在 [ZFS](./zfs.md) 中介绍。

    不过，随着 SSD 单位空间成本逐渐降低，SSD 缓存的意义也在逐渐减小。
    甚至也[有预测表明](https://thecuberesearch.com/flash-native-drives-real-time-business-process/)，到 2026 年后 SSD 的成本甚至会低于 HDD。内核中 `dm-cache` 的开发也不活跃。

    在考虑缓存方案的选择时，需要考虑各种因素，下文会做一些简单的介绍。

首先删除上面创建的 LV 与 PV，然后创建一个大的 image 和一个小的 image 作为 HDD 与 SSD：

```console
$ sudo lvremove vg201-test/lvraid0 vg201-test/lvraid1 vg201-test/lvraid5
  Logical volume "lvraid0" successfully removed.
Do you really want to remove active logical volume vg201-test/lvraid1? [y/n]: y
  Logical volume "lvraid1" successfully removed.
Do you really want to remove active logical volume vg201-test/lvraid5? [y/n]: y
  Logical volume "lvraid5" successfully removed.
$ sudo vgremove vg201-test
  Volume group "vg201-test" successfully removed
$ sudo losetup -D
$ rm pv*.img
$ truncate -s 100G hdd.img
$ truncate -s 10G ssd.img
$ sudo losetup -f --show hdd.img
/dev/loop0
$ sudo losetup -f --show ssd.img
/dev/loop1
$ sudo pvcreate /dev/loop0 /dev/loop1
  Physical volume "/dev/loop0" successfully created.
  Physical volume "/dev/loop1" successfully created.
$ sudo vgcreate vg201-test /dev/loop0 /dev/loop1
  Volume group "vg201-test" successfully created
```

<!-- TODO: 如何模拟限制访问 hdd.img 的速度？ -->

接下来我们创建存储（后备）数据的 LV，这个 LV 只应该在 HDD 上：

```console
$ sudo lvcreate -n lvdata -l 100%FREE vg201-test /dev/loop0
  Logical volume "lvdata" created.
$ sudo lvs -o +devices vg201-test
  LV     VG         Attr       LSize    Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert Devices      
  lvdata vg201-test -wi-a----- <100.00g                                                     /dev/loop0(0)
```

!!! comment "@taoky: 另一种做法"

    在配置 mirrors4 服务器的缓存时，[我们的文档](https://docs.ustclug.org/services/mirrors/4/volumes/#ssd)中的做法是把 SSD 和 HDD 分别开 VG，在后面创建好之后再 `vgmerge`。
    
    这么做其实是没有必要的，只要 `lvcreate` 的时候清醒一些就行。
    况且缓存盘和后备设备必须在同一个 VG 里头。

之后我们需要创建缓存相关的 LV。LVM 支持两种方式：`cachevol` 和 `cachepool`：

- `cachevol` 在一个 LV 中包含了缓存的数据和元数据
- `cachepool` 将缓存的数据和元数据分开存储（因此可以将数据和元数据放到不同的设备上）

许多教程中都使用 `cachepool`，但是很多时候是没有必要的。

下面先展示 `cachevol` 的操作（只需两步：创建缓存盘，然后 `lvconvert` 配置缓存即可）：

```console
$ sudo lvcreate -n lvdata_cache -l 100%FREE vg201-test /dev/loop1
  Logical volume "lvdata_cache" created.
$ sudo lvconvert --type cache --cachevol lvdata_cache vg201-test/lvdata
Erase all existing data on vg201-test/lvdata_cache? [y/n]: y
  Logical volume vg201-test/lvdata is now cached.
$ sudo lvs -a -o +devices vg201-test
  LV                  VG         Attr       LSize    Pool                Origin         Data%  Meta%  Move Log Cpy%Sync Convert Devices        
  lvdata              vg201-test Cwi-a-C--- <100.00g [lvdata_cache_cvol] [lvdata_corig] 0.01   11.07           0.00             lvdata_corig(0)
  [lvdata_cache_cvol] vg201-test Cwi-aoC---  <10.00g                                                                            /dev/loop1(0)  
  [lvdata_corig]      vg201-test owi-aoC--- <100.00g                                                                            /dev/loop0(0)
```

`lvs` 也可以输出一些缓存相关的配置和统计信息：

```console
$ sudo lvs -o devices,cache_policy,cachemode,cache_settings,cache_total_blocks,cache_used_blocks,cache_dirty_blocks,cache_read_hits,cache_read_misses,cache_write_hits,cache_write_misses
  Devices         CachePolicy CacheMode    CacheSettings CacheTotalBlocks CacheUsedBlocks  CacheDirtyBlocks CacheReadHits    CacheReadMisses  CacheWriteHits   CacheWriteMisses
  lvdata_corig(0) smq         writethrough                         163584               15                0                5               51                0                0
```

可以看到缓存的模式是 writethrough，策略是 smq，以及缓存的读写命中率与脏块数量。

!!! note "lvmcache 的缓存模式、策略与部分术语"

    lvmcache 支持三种缓存模式：

    - passthrough: 缓存无效。此时**所有读写**都到后备设备。同时写命中会触发对应的块缓存失效。
    - writethrough: 写入操作在缓存和后备设备上都进行。
    - writeback: 写入操作只在缓存上进行，对应的块标记为脏块（Dirty Block）。
    **除非被缓存的数据完全无关紧要，或者有多块 SSD 进行缓存，否则不要使用 writeback。文件系统核心元数据的损坏可能直接导致整个文件系统无法读取。**

    在策略一栏，我们可以看到 "smq"。事实上，lvmcache 唯一支持的有效的现代策略就是 [smq（Stochastic Multi-Queue）](https://elixir.bootlin.com/linux/v6.7/source/drivers/md/dm-cache-policy-smq.c)。
    另一种 cleaner 策略用于将所有脏块写回后备设备。

    此外，在阅读相关资料时，可能会看到下面三个术语：

    - Migration：将一块数据从一个设备复制到另一个设备
    - Promotion：将一块数据从后备设备复制到缓存设备
    - Demotion：将一块数据从缓存设备复制到后备设备

!!! comment "@taoky: 关于缓存模式"

    分享一个笑话，最开始 @iBug 配的缓存模式选了 passthrough，理由是：

    > 这里的缓存模式采用 passthrough，即写入动作绕过缓存直接写回原设备（当然啦，写入都是由从上游同步产生的），另外两种 writeback 和 writethrough 都会写入缓存，不是我们想要的。

    （当然，这是错的）

    另外可以注意到，`lvmcache` 做了这么一个假设：写入的内容很快就会被读取。但是这个假设真的总是成立吗？
    writearound 的做法是写入的内容会绕过缓存，当然 lvmcache 没有实现这个模式。

??? note "`dm-cache-policy-smq.c` 中实现的 SMQ 策略算法"

    核心的结构体是 `smq_policy`，其中包含了三个 SMQ 队列：热点（hotspot）队列、clean 队列和 dirty 队列。
    每个 SMQ 队列中包含 64 个 LRU 队列。这 64 个队列构成不同的等级，存储由热到冷的内容。

    <!-- TODO: 更详细的介绍 -->

使用 `cachepool` 就麻烦很多。先把上面的 uncache 掉：

```console
$ sudo lvconvert --uncache vg201-test/lvdata
  Logical volume "lvdata_cache" successfully removed.
  Logical volume vg201-test/lvdata is not cached and vg201-test/lvdata_cache is removed.
```

[^rhel-version]: 推荐查看最新版本的 RHEL 手册进行阅读，因为新版本可能包含一些新特性，并且 Debian 的版本更新比 RHEL 更快。本链接指向目前最新的 RHEL 9 的 LVM 手册。
