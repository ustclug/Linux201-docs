# LVM

!!! note "主要作者"

    [@taoky][taoky]

!!! success "本文已完成"

本文将介绍常见 LVM 特性的使用与维护。

LVM（Logical Volume Manager）是 Linux 下的逻辑卷管理器，基于内核的 device mapper（dm）功能。
相比于直接在创建分区表后使用分区，LVM 提供了更加灵活的存储管理方式：

- LVM 可以管理多个硬盘（物理卷）上的存储空间
- LVM 中的逻辑卷可以跨越多个物理卷，文件系统不需要关心物理卷的位置
- LVM 的逻辑卷可以动态调整大小，而不需要移动分区的位置——移动分区的起始位置是一个危险且耗时的操作

一些 Linux 发行版的安装程序默认使用 LVM 来管理磁盘，例如 Fedora、CentOS 等。如果需要实际使用 LVM，也推荐阅读来自[红帽 RHEL 的 LVM 管理指南](https://access.redhat.com/documentation/zh-cn/red_hat_enterprise_linux/9/html-single/configuring_and_managing_logical_volumes/index#doc-wrapper)[^rhel-version]。

!!! warning "本部分无法涵盖全部内容"

    LVM 包含了很多功能，在本份文档中不可能面面俱到，因此我们仅介绍在 LUG 与 Vlab 项目中使用过的功能。

## 基础概念 {#basic}

LVM 中有三个基本概念：

- 物理卷（Physical Volume，PV）：通常是一块硬盘（分区）
- 卷组（Volume Group，VG）：由一个或多个物理卷组成
- 逻辑卷（Logical Volume，LV）：在卷组里分配的逻辑存储空间。称之为「逻辑」，是因为它可以跨越多个物理卷，也不一定是连续的

这里我们创建三个 1GB 的文件作为物理卷，并且加入到一个卷组中：

!!! warning "避免在物理磁盘上创建无分区表的文件系统/物理卷"

    在实践中，尽管技术上可行，但是不创建分区表、直接将整个磁盘格式化为某个文件系统，或者加入 LVM 中是不建议的。
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
$ # 对应的设备文件也可以在 /dev/vg201-test/ 里面找到
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

## 创建 RAID {#raid}

!!! warning "不建议使用 LVM 构建 RAID"

    相比于 mdadm，LVM 与 RAID 相关的概念与提供的工具更加复杂，并且这种复杂性在很多场景下没有收益。
    更加常见的模式是，使用 mdadm 构建 RAID，然后使用 LVM 管理构建好的 RAID 上的逻辑卷。

    LVM 与 mdadm 使用的都是内核的 md 模块。即使最终使用 LVM 构建 RAID，也建议简单阅读后一节关于 mdadm 的内容。

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
    
    相关讨论可查看 [In what case(s) will `--type mirror` continue to be a good choice / is not deprecated?](https://unix.stackexchange.com/q/697364)。

    在后文的缺盘测试中，`mirror` 的行为也与预期不同——LVM 默认会拒绝挂载，如果强行挂载，会直接将缺失的盘丢掉。

!!! note "Extent 是多大"

    有时在输入错误的参数之后，会出现 extent 不足的提示，类似于这样：

    ```console
    $ # --mirrors 参数多了一，空间不够
    $ sudo lvcreate -n lvraid1 -L 0.5G --type raid1 --mirrors 3 vg201-test
      Insufficient suitable allocatable extents for logical volume lvraid1: 516 more required
    ```

    但是 "extent" 是多大呢？
    此时可以使用 `pvdisplay` 或 `vgdisplay` 查看物理卷的 PE（Physical Extent）大小：

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

    可以看到 PE 是 4M，因此缺少 516 个 extent 指缺少 516 * 4M ≈ 2G 空间。
    这里报错实际的原因是 PV 数量不足，所以无法找到能够存储第四份副本的磁盘（即缺少满足条件的 extent，而非单纯的 VG 中空闲 extent）。

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

## RAID 维护 {#raid-maintain}

### RAID 状态与重建 {#raid-rebuild}

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

### 完整性检查 {#raid-scrub}

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

## 扩容/缩小操作 {#resize}

LVM 支持在线扩容/缩小逻辑卷，有三个相关命令：`lvextend`（扩大）、`lvreduce`（缩小）、`lvresize`（通用）。
让我们先在 lvraid0 上创建一个 ext4 文件系统并挂载，模拟在线场景：

```console
$ sudo mkfs.ext4 /dev/vg201-test/lvraid0
mke2fs 1.47.0 (5-Feb-2023)
Discarding device blocks: done                            
Creating filesystem with 132096 4k blocks and 33040 inodes
Filesystem UUID: 49e73c33-1ea2-43fa-8609-586389a11b98
Superblock backups stored on blocks: 
	32768, 98304

Allocating group tables: done                            
Writing inode tables: done                            
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information: done
$ sudo mount /dev/vg201-test/lvraid0 /somewhere/you/like
$ df -h /somewhere/you/like
Filesystem                       Size  Used Avail Use% Mounted on
/dev/mapper/vg201--test-lvraid0  492M  152K  455M   1% /somewhere/you/like
```

下面展示 `lvextend` 和 `lvreduce`。`lvresize` 的操作可以自行查阅。

```console
$ sudo lvextend --size +100M /dev/vg201-test/lvraid0
  Using stripesize of last segment 64.00 KiB
  Rounding size (154 extents) up to stripe boundary size for segment (156 extents).
  Size of logical volume vg201-test/lvraid0 changed from 516.00 MiB (129 extents) to 624.00 MiB (156 extents).
  Logical volume vg201-test/lvraid0 successfully resized.
```

此时 `lvraid0` 这个 LV 已经增大了 100M，但是文件系统并没有感知到这个变化：

```console
$ df -h /somewhere/you/like
Filesystem                       Size  Used Avail Use% Mounted on
/dev/mapper/vg201--test-lvraid0  492M  152K  455M   1% /somewhere/you/like
```

因此我们需要用文件系统提供的工具扩容。ext4 支持使用 `resize2fs` 在线扩容/缩小：

```console
$ sudo resize2fs /dev/vg201-test/lvraid0
resize2fs 1.47.0 (5-Feb-2023)
Filesystem at /dev/vg201-test/lvraid0 is mounted on /somewhere/you/like; on-line resizing required
old_desc_blocks = 1, new_desc_blocks = 1
The filesystem on /dev/vg201-test/lvraid0 is now 159744 (4k) blocks long.

$ df -h /somewhere/you/like
Filesystem                       Size  Used Avail Use% Mounted on
/dev/mapper/vg201--test-lvraid0  600M  152K  563M   1% /somewhere/you/like
```

缩小操作的顺序刚好相反：**需要先缩小文件系统，再缩小 LV**。
否则文件系统被缩小的部分会丢失，导致文件系统损坏。
由于 ext4 文件系统不支持在线缩小，因此操作前必须卸载文件系统。
这里我们把文件系统缩到最小，然后缩小 LV，最后再扩大文件系统：

```console
$ sudo umount /somewhere/you/like
$ sudo resize2fs -M /dev/vg201-test/lvraid0
resize2fs 1.47.0 (5-Feb-2023)
Please run 'e2fsck -f /dev/vg201-test/lvraid0' first.

$ # 在缩小前，保险起见，需要先检查文件系统的完整性
$ sudo e2fsck -f /dev/vg201-test/lvraid0
e2fsck 1.47.0 (5-Feb-2023)
Pass 1: Checking inodes, blocks, and sizes
Pass 2: Checking directory structure
Pass 3: Checking directory connectivity
Pass 4: Checking reference counts
Pass 5: Checking group summary information
/dev/vg201-test/lvraid0: 12/33040 files (0.0% non-contiguous), 6407/159744 blocks
$ sudo resize2fs -M /dev/vg201-test/lvraid0
resize2fs 1.47.0 (5-Feb-2023)
Resizing the filesystem on /dev/vg201-test/lvraid0 to 6420 (4k) blocks.
The filesystem on /dev/vg201-test/lvraid0 is now 6420 (4k) blocks long.

$ # 现在缩小 LV
$ sudo lvreduce --size -100M /dev/vg201-test/lvraid0
  Rounding size (131 extents) up to stripe boundary size for segment (132 extents).
  File system ext4 found on vg201-test/lvraid0.
  File system size (<25.08 MiB) is smaller than the requested size (528.00 MiB).
  File system reduce is not needed, skipping.
  Size of logical volume vg201-test/lvraid0 changed from 624.00 MiB (156 extents) to 528.00 MiB (132 extents).
  Logical volume vg201-test/lvraid0 successfully resized.
$ sudo resize2fs /dev/vg201-test/lvraid0
resize2fs 1.47.0 (5-Feb-2023)
Resizing the filesystem on /dev/vg201-test/lvraid0 to 135168 (4k) blocks.
The filesystem on /dev/vg201-test/lvraid0 is now 135168 (4k) blocks long.

$ sudo mount /dev/vg201-test/lvraid0 /somewhere/you/like
$ df -h /somewhere/you/like
Filesystem                       Size  Used Avail Use% Mounted on
/dev/mapper/vg201--test-lvraid0  504M  152K  471M   1% /somewhere/you/like
```

对于支持的文件系统，`lvreduce` 会检查文件系统的大小，避免数据损坏。但在操作时仍然需要谨慎。

## SSD 缓存 {#lvmcache}

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

    科大镜像站于 2024 年 7 月将缓存方案由 lvmcache（基于 SSD）迁移至了 ZFS ARC（基于内存），以减小下文中提到的相关问题导致的运维压力。

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

!!! warning "resize"

    直到[相对新（>= 2.03.12，发布于 2021/05/08）的 LVM 工具](https://github.com/lvmteam/lvm2/issues/30#issuecomment-1412248104)之前，被缓存的 LV 不能被 resize。因此 resize 之前必须先撤下缓存，resize 结束后再安回去。

    因此 [Debian Bookworm 的 LVM 工具](https://packages.debian.org/bookworm/lvm2)支持这种情况下的 resize，而 Bullseye 不支持。

!!! warning "`cachevol` 无法修复"

    目前 `lvconvert --repair` 不支持修复 cachevol，尝试这么做会看到以下输出：

    ```console
    $ sudo lvconvert --repair vg201-test/lvdata_cache_cvol
      WARNING: Command on LV vg201-test/lvdata_cache_cvol does not accept LV type linear.
      Command not permitted on LV vg201-test/lvdata_cache_cvol.
    ```

!!! note "lvmcache 的缓存模式、策略与部分术语"

    lvmcache 支持三种缓存模式：

    - passthrough: 缓存无效。此时**所有读写**都到后备设备。同时写命中会触发对应的块缓存失效。
    - writethrough: 写入操作在缓存和后备设备上都进行，在两者均写入完成后才视作写入生效。
    - writeback: 写入操作先在缓存上进行，对应的块标记为脏块（Dirty Block），推迟在后备设备上的写入。
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

如果不关心数据卷和元数据卷的细节，创建 `cachepool` 的体验也类似。先把上面的 uncache 掉：

```console
$ sudo lvconvert --uncache vg201-test/lvdata
  Logical volume "lvdata_cache" successfully removed.
  Logical volume vg201-test/lvdata is not cached and vg201-test/lvdata_cache is removed.
```

然后创建 **cache-pool 类型**的 LV，并且附加到后备设备上：

```console
$ sudo lvcreate --type cache-pool -n lvdata_cache -l 100%FREE vg201-test /dev/loop1
  Logical volume "lvdata_cache" created.
$ sudo lvs -a
  LV                   VG         Attr       LSize    Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvdata               vg201-test -wi-a----- <100.00g                                                    
  lvdata_cache         vg201-test Cwi---C---    9.97g                                                    
  [lvdata_cache_cdata] vg201-test Cwi-------    9.97g                                                    
  [lvdata_cache_cmeta] vg201-test ewi-------   12.00m                                                    
  [lvol0_pmspare]      vg201-test ewi-------   12.00m
$ sudo lvconvert --type cache --cachepool lvdata_cache vg201-test/lvdata
Do you want wipe existing metadata of cache pool vg201-test/lvdata_cache? [y/n]: y
  Logical volume vg201-test/lvdata is now cached.
$ sudo lvs -a
  LV                         VG         Attr       LSize    Pool                 Origin         Data%  Meta%  Move Log Cpy%Sync Convert
  lvdata                     vg201-test Cwi-a-C--- <100.00g [lvdata_cache_cpool] [lvdata_corig] 0.01   11.07           0.00            
  [lvdata_cache_cpool]       vg201-test Cwi---C---    9.97g                                     0.01   11.07           0.00            
  [lvdata_cache_cpool_cdata] vg201-test Cwi-ao----    9.97g                                                                            
  [lvdata_cache_cpool_cmeta] vg201-test ewi-ao----   12.00m                                                                            
  [lvdata_corig]             vg201-test owi-aoC--- <100.00g                                                                            
  [lvol0_pmspare]            vg201-test ewi-------   12.00m
```

可以发现，在 `lvcreate --type cache-pool` 的时候，LVM 会自动创建两个 LV：`lvdata_cache_cdata` 和 `lvdata_cache_cmeta`。
但是更老一些的教程中会介绍分别手工创建缓存和元数据 LV 的内容。让我们先把这个再拆掉（uncache），然后手工做这个过程。

根据 [RHEL 6 的文档](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/logical_volume_manager_administration/lvm_cache_volume_creation)，数据和元数据的推荐大小比例是 1000:1（例如如果有 2G 的缓存，那么就需要 12M 的元数据）。
这里我们的 "SSD" 有 10G，因此大约需要 60M 的元数据，可以先创建元数据 LV，然后剩下的——全部给数据？

```console
$ sudo lvcreate -L 60M -n lvdata_cache_meta vg201-test /dev/loop1
  Logical volume "lvdata_cache_meta" created.
$ sudo lvcreate -l 100%FREE -n lvdata_cache_data vg201-test /dev/loop1
  Logical volume "lvdata_cache_data" created.
$ sudo lvconvert --type cache-pool --poolmetadata lvdata_cache_meta --cachemode writethrough vg201-test/lvdata_cache_data
  WARNING: Converting vg201-test/lvdata_cache_data and vg201-test/lvdata_cache_meta to cache pool's data and metadata volumes with metadata wiping.
  THIS WILL DESTROY CONTENT OF LOGICAL VOLUME (filesystem etc.)
Do you really want to convert vg201-test/lvdata_cache_data and vg201-test/lvdata_cache_meta? [y/n]: y
  Volume group "vg201-test" has insufficient free space (0 extents): 15 required.
  Failed to set up spare metadata LV for pool.
```

可以看到还需要一些空间（15 个 extent），因此使用 `lvreduce` 留点出来：

```console
$ sudo lvreduce -l -15 vg201-test/lvdata_cache_data
  No file system found on /dev/vg201-test/lvdata_cache_data.
  Size of logical volume vg201-test/lvdata_cache_data changed from <9.94 GiB (2544 extents) to <9.88 GiB (2529 extents).
  Logical volume vg201-test/lvdata_cache_data successfully resized.
$ sudo lvconvert --type cache-pool --poolmetadata lvdata_cache_meta --cachemode writethrough vg201-test/lvdata_cache_data
  WARNING: Converting vg201-test/lvdata_cache_data and vg201-test/lvdata_cache_meta to cache pool's data and metadata volumes with metadata wiping.
  THIS WILL DESTROY CONTENT OF LOGICAL VOLUME (filesystem etc.)
Do you really want to convert vg201-test/lvdata_cache_data and vg201-test/lvdata_cache_meta? [y/n]: y
  Converted vg201-test/lvdata_cache_data and vg201-test/lvdata_cache_meta to cache pool.
```

之后就和上面一致了：

```console
$ sudo lvs -a
  LV                        VG         Attr       LSize    Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvdata                    vg201-test -wi-a----- <100.00g                                                    
  lvdata_cache_data         vg201-test Cwi---C---   <9.88g                                                    
  [lvdata_cache_data_cdata] vg201-test Cwi-------   <9.88g                                                    
  [lvdata_cache_data_cmeta] vg201-test ewi-------   60.00m                                                    
  [lvol0_pmspare]           vg201-test ewi-------   60.00m
$ sudo lvconvert --type cache --cachepool lvdata_cache_data vg201-test/lvdata
Do you want wipe existing metadata of cache pool vg201-test/lvdata_cache_data? [y/n]: y
  Logical volume vg201-test/lvdata is now cached.
```

### Does lvmcache scale? {#lvmcache-scalability}

现实中我们肯定不可能只用 10G 的 SSD 来做缓存，而在非家用的场景下，需要缓存的后备存储也不可能只有 100G 这么大。
下面考虑一个类似于目前 mirrors 的场景：1.5T 的 SSD 空间对 65T 的 HDD 空间进行缓存（比例大约 1:45）。

把已有的拆掉之后重新创建 1.5T（1536G）和 65T 的稀疏文件作为 SSD 和 HDD，加入 LVM，然后让我们试试 cachevol……

```console
$ sudo lvconvert --type cache --cachevol lvdata_cache vg201-test/lvdata
Erase all existing data on vg201-test/lvdata_cache? [y/n]: y
  Cache data blocks 3219046400 and chunk size 128 exceed max chunks 1000000.
  Use smaller cache, larger --chunksize or increase max chunks setting.
```

（这里显示的单位是扇区，即 512 字节）

这里 cache 需要记录缓存数据的访问情况，记录的单位就是 chunk（需要是 32K 的倍数）。默认情况下，chunk 大小设置为 64KB。
并且 LVM 推荐 chunk 不超过一百万个（这也是 allocation/cache_pool_max_chunks 设置的默认值）。
换句话讲，如果保持默认设置，那么后备数据最大只能有 64KB * 1,000,000 ~= 64GB << 1.5T，这显然是不够的。

直觉来讲，既然 chunk 推荐不超过一百万个，那就拉高 chunk size？但是需要考虑这两个问题：

1. 如果访问的模式不那么连续，那么更大的 chunk size 就势必导致更多的数据在缓存和后备设备之间来回传输。（命中率降低）
2. SSD 的写入量是有限制的。上面一点中提到的命中率降低的问题会导致更多的写入，最终导致 SSD 的寿命缩短。

因此更好的选择是以（相对更能接受的）一些额外的 overhead 为代价，增加 chunk 数量。具体的「代价」在后续创建后，可以在内核日志里面看到：

```log
[2030783.641796] device-mapper: cache: You have created a cache device with a lot of individual cache blocks (12578624)
                 All these mappings can consume a lot of kernel memory, and take some time to read/write.
                 Please consider increasing the cache block size to reduce the overall cache block count.
```

考虑到在服务器场合，内存一般都是足够（甚至过量）的，因此唯一可能需要考虑的就是额外的延迟了。

!!! comment "@taoky: 真实事件的教训"

    最开始的时候，mirrors 的 chunk size 设置为了 1M，结果过了两年多就发现 SSD 快挂了。
    查看统计发现 SSD 每小时读取 0.1T，但是写 1T 数据……

    因为经历过 SSD 被 lvmcache 磨没的事件，所以我个人的看法是，
    在 201 中，提及这一点（以及后面会介绍 lvmcache 还有其他的坑）是很重要的——有些方案放大规模之后，就会出现意想不到的问题。

```console
$ sudo lvconvert --type cache --cachevol lvdata_cache --config allocation/cache_pool_max_chunks=25148800 vg201-test/lvdata
Erase all existing data on vg201-test/lvdata_cache? [y/n]: y
  WARNING: Configured cache_pool_max_chunks value 25148800 is higher then recommended 1000000.
  Logical volume vg201-test/lvdata is now cached.
```

64K 也是目前 mirrors 机器使用的 chunk size。

当然也可以把 chunk size 略微调大到 128K，这样的话 chunk 就少一些：

```console
$ sudo lvconvert --type cache --cachevol lvdata_cache --chunksize 128K --config allocation/cache_pool_max_chunks=12578624 vg201-test/lvdata
Erase all existing data on vg201-test/lvdata_cache? [y/n]: y
  WARNING: Configured cache_pool_max_chunks value 12578624 is higher then recommended 1000000.
  Logical volume vg201-test/lvdata is now cached.
```

可能需要进行一些性能测试来权衡 chunk size 带来的影响——考虑到本地测试时稀疏文件等因素，实际的性能测试可能需要在真实的环境中进行。

<!-- TODO: 很明显，缺真实的延迟数据 -->

此外，在 `lvconvert` 创建缓存时，如果 SSD 设备不支持 TRIM（常见的场景是在 RAID 卡后面），那么其会清零对应的块，这个过程可能会花费超过半个小时的时间。

### Too dirty to use {#lvmcache-dirty-issue}

lvmcache 方案的一个无法忽视的弊端是：**即使模式设置为 writethrough，如果没有干净地卸载，那么在下次加载后，缓存中所有的块都会被标记为脏块**。
更加致命的是，在生产负载下，可能会出现脏块写回在默认情况下极其缓慢的问题（即使设置 policy 为 cleaner），以至于可能过了几个小时都没有迁移任何一个块。

??? tip "如何实验复现「所有块被标记」的行为？"

    由于没有能够强制卸载本地回环的方法，因此这里可以考虑的思路是：
    在虚拟机中使用本地回环设备创建 lvmcache，写入并读取一些数据（单纯的写入一次可能不会使用缓存块空间），然后使用 `reboot -f` 强制重启。

    如果使用的块够多，并且操作及时，可能就能看到 dirty block > 0 的情况：

    ```console
    $ sudo losetup -f --show hdd.img
    /dev/loop0
    $ sudo losetup -f --show ssd.img
    /dev/loop1
    $ sudo lvs -a -o devices,cache_policy,cachemode,cache_settings,cache_total_blocks,cache_used_blocks,cache_dirty_blocks,cache_read_hits,cache_read_misses,cache_write_hits,cache_write_misses
      Devices         CachePolicy CacheMode    CacheSettings CacheTotalBlocks CacheUsedBlocks  CacheDirtyBlocks CacheReadHits    CacheReadMisses  CacheWriteHits   CacheWriteMisses
      lvdata_corig(0) smq         writethrough                         163584            62544             4918              120                0                0                0
      /dev/loop1(0)                                                                                                                                                                
      /dev/loop0(0)
    ```

    另外在本地测试时发现，如果创建 cache 之后过短暂的时间后重启，LVM 调用的旧版本的 [cache 检查工具](https://github.com/jthornber/thin-provisioning-tools)可能会认为 cache LV 的结构不正确，
    此时 LVM 无法挂载[^t-p-t-bug] cache，只能用一些 trick 来 uncache 掉这个坏掉的 LV
    （cachevol 可能会麻烦一些，需要先使用 `dmsetup remove` 移除多余的卷；cachepool 可以直接 uncache）。
    或者将 thin-provisioning-tools 升级至 1.0.12 以上。

    来自 linux-lvm 邮件列表的可能相关的故障报告参见
    <https://lore.kernel.org/all/b9e10482-e508-63fa-5518-94cccc007e81@redhat.com/T/>。

!!! note "最新的内核可能部分修复了后一个问题"

    参见 <https://github.com/torvalds/linux/commit/1e4ab7b4c881cf26c1c72b3f56519e03475486fb>。
    根据该 commit 的描述，**在 cleaner 状态下**即使 IO idle 为 false，也会进行脏块迁移。

!!! note "lvmcache 的设计"

    从前面的统计数据可以注意到，脏块的数量是一个指标。在 lvmcache 的设计中，存在出现模式为 writethrough 并且存在脏块的可能，所以目前程序上没有实现看到 writethrough 之后
    就忽略脏块的问题。

??? note "模拟在 IO 压力下迁移缓慢的情况"

    格式化我们刚才创建的有 cache 的 LV，使用 `fio` 上点压力：

    ```console
    $ sudo fio --filename=./test --filesize=2G --direct=1 --rw=randrw --bs=4k --ioengine=libaio --iodepth=256 --runtime=120 --numjobs=4 --time_based --group_reporting --name=job_name --eta-newline=1
    ```

    同时做切换 cachemode 的操作：

    ```console
    $ sudo lvchange --cachemode writeback vg201-test/lvdata
      WARNING: repairing a damaged cachevol is not yet possible.
      WARNING: cache mode writethrough is suggested for safe operation.
    Continue using writeback without repair?y
      Logical volume vg201-test/lvdata changed.
    $ sudo lvchange --cachemode writethrough vg201-test/lvdata
      Flushing 16401 blocks for cache vg201-test/lvdata.
      Flushing 16405 blocks for cache vg201-test/lvdata.
      Flushing 12309 blocks for cache vg201-test/lvdata.
      Flushing 8213 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 6481 blocks for cache vg201-test/lvdata.
      Flushing 2411 blocks for cache vg201-test/lvdata.
      Logical volume vg201-test/lvdata changed.
    ```

    可以注意到卡在了 `Flushing 6481 blocks` 比较长的时间。测试环境为笔记本电脑的 NVMe SSD，如果是实际的 HDD + 较大负载的话，问题会严重得多。

!!! comment "@taoky: 其他信息"

    这可能是对于较大缓存、较重的负载下 lvmcache 最大的问题了。
    关于下面处理不方便的问题，我在 lvm2 仓库提交了 issue: <https://github.com/lvmteam/lvm2/issues/141>，
    希望能够在 lvm 工具中实现绕过 flush dirty block 的操作。

    不过最佳的解决方法可能还是给 kernel 交个 patch，如果目前状态是 writethrough 并且 dirty = 0 那么给某个 struct 设一个特殊的 bit。但是感觉不知道如何下手，只能以后再说了。

根据文档，`migration_threshold` 参数控制每次迁移脏块的扇区数量。相关的 bug report 建议将这个值设置为 chunk size 的至少 8 倍（默认为 2048，对应 1M）。
在调试问题时发现，修改这个值可以实现强制迁移（但是迁移时所有相关的 IO 操作都会暂停），脚本类似这样：

```sh
# dirty hack
sudo lvchange --cachepolicy cleaner lug/repo
for i in `seq 1 1500`; do sudo lvchange --cachesettings migration_threshold=2113536 lug/repo && sudo lvchange --cachesettings migration_threshold=16384 lug/repo && echo $i && sleep 15; done;
# 需要确认没有脏块。如果还有的话继续执行（次数调小一些）
# 如果是从 writeback 切换，需要先把模式切到 writethrough
# 然后再修改 cachepolicy 到 smq
sudo lvchange --cachepolicy smq lug/repo
```

在我们的配置下，写全部脏块操作（包括中间的 `sleep` 操作在内）需要大约 10 个小时。

!!! danger "GRUB 可能无法处理自定义的 migration_threshold 等属性"

    参考 patch: <https://github.com/taoky/grub/commit/484b718831ab3ca034bb5ea3624a85efeb5bf2ba>。

    相关的备注信息：<https://blog.taoky.moe/attachments/2021-04-17-tunight/show.html#21>。

    虽然这个 patch 也有问题，并且 GRUB 的开发非常不活跃，所以可能一直都要自己编译 GRUB 了。

我们目前的建议是在计划重启（维护窗口）前手动卸载缓存，在重启后再挂载（之前维护时观察到，即使正常关机，也可能出现脏块的问题）。
另一种方式是：（在确认没有事实上的脏块的前提下）手动修改 LVM 元数据，把缓存扔掉。

!!! danger "小心操作"

    对每次 LVM 操作，lvm 的工具都会在 `/etc/lvm/archive` 备份操作前的元数据信息，同时在 `/etc/lvm/backup` 存储当前的元数据，但是还是尽量小心，以免酿成悲剧。

??? note "有 cache 的 VG 元数据例子"

    ```lvm
    # Generated by LVM2 version 2.03.23(2) (2023-11-21): Sun Feb 18 00:25:36 2024

    contents = "Text Format Volume Group"
    version = 1

    description = "Created *after* executing 'lvconvert --type cache --cachevol lvdata_cache --config allocation/cache_pool_max_chunks=25148800 vg201-test/lvdata'"

    creation_host = "shimarin.taoky.moe"	# Linux shimarin.taoky.moe 6.6.10-arch1-1 #1 SMP PREEMPT_DYNAMIC Fri, 05 Jan 2024 16:20:41 +0000 x86_64
    creation_time = 1708187136	# Sun Feb 18 00:25:36 2024

    vg201-test {
        id = "kDKbJ2-kebs-HaIJ-4Vfj-E4OB-aCce-yEcdAy"
        seqno = 34
        format = "lvm2"			# informational
        status = ["RESIZEABLE", "READ", "WRITE"]
        flags = []
        extent_size = 8192		# 4 Megabytes
        max_lv = 0
        max_pv = 0
        metadata_copies = 0

        physical_volumes {

            pv0 {
                id = "VfZ83M-BPwe-bIQ1-JJRO-ZBSf-ks8d-fMln8E"
                device = "/dev/loop0"	# Hint only

                status = ["ALLOCATABLE"]
                flags = []
                dev_size = 139586437120	# 65 Terabytes
                pe_start = 2048
                pe_count = 17039359	# 65 Terabytes
            }

            pv1 {
                id = "8hZXeS-gZJX-OfrY-vfUm-tG1R-pw3V-6c3CBI"
                device = "/dev/loop1"	# Hint only

                status = ["ALLOCATABLE"]
                flags = []
                dev_size = 3221225472	# 1.5 Terabytes
                pe_start = 2048
                pe_count = 393215	# 1.5 Terabytes
            }
        }

        logical_volumes {

            lvdata {
                id = "6BsYbX-T21Z-BgiW-pZET-a3Lf-wcSh-E5hSm2"
                status = ["READ", "WRITE", "VISIBLE"]
                flags = []
                creation_time = 1708181300	# 2024-02-17 22:48:20 +0800
                creation_host = "shimarin.taoky.moe"
                segment_count = 1

                segment1 {
                    start_extent = 0
                    extent_count = 17039359	# 65 Terabytes

                    type = "cache+CACHE_USES_CACHEVOL"
                    cache_pool = "lvdata_cache_cvol"
                    origin = "lvdata_corig"
                    metadata_format = 2
                    chunk_size = 128
                    cache_mode = "writethrough"
                    policy = "smq"
                    metadata_start = 0
                    metadata_len = 2170880
                    data_start = 2170880
                    data_len = 3219046400
                }
            }

            lvdata_cache_cvol {
                id = "RuL2He-0xlL-J4fd-T0eD-2YTr-QASe-gsWtBV"
                status = ["READ", "WRITE"]
                flags = ["CACHE_VOL"]
                creation_time = 1708187133	# 2024-02-18 00:25:33 +0800
                creation_host = "shimarin.taoky.moe"
                segment_count = 1

                segment1 {
                    start_extent = 0
                    extent_count = 393215	# 1.5 Terabytes

                    type = "striped"
                    stripe_count = 1	# linear

                    stripes = [
                        "pv1", 0
                    ]
                }
            }

            lvdata_corig {
                id = "xIprwR-KD4I-f6E8-tdgp-lcjN-iUdk-rS63YR"
                status = ["READ", "WRITE"]
                flags = []
                creation_time = 1708187136	# 2024-02-18 00:25:36 +0800
                creation_host = "shimarin.taoky.moe"
                segment_count = 1

                segment1 {
                    start_extent = 0
                    extent_count = 17039359	# 65 Terabytes

                    type = "striped"
                    stripe_count = 1	# linear

                    stripes = [
                        "pv0", 0
                    ]
                }
            }
        }

    }
    ```

??? note "没有 cache 的 VG 元数据例子"

    以下仅展示 `logical_volumes` 部分：

    ```lvm
    # （省略）

    vg201-test {
        # （省略）

        logical_volumes {

            lvdata {
                id = "6BsYbX-T21Z-BgiW-pZET-a3Lf-wcSh-E5hSm2"
                status = ["READ", "WRITE", "VISIBLE"]
                flags = []
                creation_time = 1708181300	# 2024-02-17 22:48:20 +0800
                creation_host = "shimarin.taoky.moe"
                segment_count = 1

                segment1 {
                    start_extent = 0
                    extent_count = 17039359	# 65 Terabytes

                    type = "striped"
                    stripe_count = 1	# linear

                    stripes = [
                        "pv0", 0
                    ]
                }
            }

            lvdata_cache {
                id = "RuL2He-0xlL-J4fd-T0eD-2YTr-QASe-gsWtBV"
                status = ["READ", "WRITE", "VISIBLE"]
                flags = []
                creation_time = 1708187133	# 2024-02-18 00:25:33 +0800
                creation_host = "shimarin.taoky.moe"
                segment_count = 1

                segment1 {
                    start_extent = 0
                    extent_count = 393215	# 1.5 Terabytes

                    type = "striped"
                    stripe_count = 1	# linear

                    stripes = [
                        "pv1", 0
                    ]
                }
            }
        }

    }
    ```

首先对比 archive 和 backup 中的元数据，确认无误之后使用 `vgcfgrestore` 恢复元数据。
某些情况下，可能需要编辑元数据文件以符合实际情况（例如在创建缓存之后又做了其他操作）。

```console
$ sudo vgcfgrestore -f /etc/lvm/archive/vg201-test_00084-792872325.vg vg201-test
  Volume group vg201-test has active volume: lvdata.
  Volume group vg201-test has active volume: lvdata_cache_cvol.
  Volume group vg201-test has active volume: lvdata_cache_cvol.
  Volume group vg201-test has active volume: lvdata_cache_cvol.
  Volume group vg201-test has active volume: lvdata_corig.
  WARNING: Found 5 active volume(s) in volume group "vg201-test".
  Restoring VG with active LVs, may cause mismatch with its metadata.
Do you really want to proceed with restore of volume group "vg201-test", while 5 volume(s) are active? [y/n]: y
  Restored volume group vg201-test.
$ sudo lvs -a
  WARNING: Detected cache segment type does not match expected type striped for vg201-test/lvdata.
  LV           VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvdata       vg201-test -wi-XX--X- <65.00t                                                    
  lvdata_cache vg201-test -wi-a-----  <1.50t
```

在重新 activate 之后，状态即恢复正常：

```console
$ sudo vgchange -an vg201-test
  0 logical volume(s) in volume group "vg201-test" now active
$ sudo vgchange -ay vg201-test
  2 logical volume(s) in volume group "vg201-test" now active
$ sudo lvs -a
  LV           VG         Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvdata       vg201-test -wi-a----- <65.00t                                                    
  lvdata_cache vg201-test -wi-a-----  <1.50t
```

### 缓存方案比较 {#ssdcache-comparison}

作为 SSD 缓存部分的最后一小节，本部分以表格形式介绍已有的 SSD 缓存方案（包括已经不再维护的）。
我们建议无论选择何种方案，都需要先测试其是否易于使用，是否会给运维操作带来额外的负担。

| 方案 | 缓存模式 | 缓存算法 | 简介 | 上次维护时间[^time] |
| --- | --- | --- | --- | --- |
| lvmcache | writethrough, writeback | smq | 与 LVM 集成的缓存方案，基于内核的 dm-cache | [7 个月前](https://github.com/torvalds/linux/commit/1e4ab7b4c881cf26c1c72b3f56519e03475486fb) |
| bcache | writethrough, writeback, writearound | lru, fifo, random | 已在内核中的稳定 cache 方案 | [2 个月前](https://github.com/torvalds/linux/commit/105c1a5f6ccef7f52f9e76664407ef96218272eb) |
| ZFS ARC + L2ARC | 类似 writearound | ARC | ZFS 自带的缓存。ARC 以内存为缓存；L2ARC 作为第二级缓存，使用 SSD，用于在高负载情况下支撑 IOPS，命中率较低 | [随 ZFS 开发](https://github.com/openzfs/zfs/) |
| EnhanceIO | readonly (writearound), writethrough, writeback | lru, fifo, random | 早期的 SSD 缓存方案 | ☠️ [9 年前](https://github.com/stec-inc/EnhanceIO/commit/104d4287f32da28f51efc5a451e62e4071322480) |
| Flashcache | writethrough, writeback, writearound | fifo, lru | Facebook 开发的早期 SSD 缓存方案 | ☠️ [7 年前](https://github.com/facebookarchive/flashcache/commit/437afbfe233e94589948b76743c6489080cdd100) |
| [OpenCAS](https://open-cas.github.io/index.html) | writethrough, writeback, writearound, write-invalidate, write-only | lru (?) | SPDK 的一部分 | [3 个月前](https://github.com/Open-CAS/open-cas-linux/commit/fd39e912cc4ec4f02741269df81cd6bcc88b18b8)  |
| bcachefs | writethrough, writeback, writearound | lru[^bcachefs-principles] | 由 bcache 作者开发的新 CoW 文件系统，内置 SSD 缓存支持 | [活跃开发](https://evilpiepirate.org/git/bcachefs.git) |

## 集群存储 {#lvm-cluster}

LVM 支持多机共享存储。在这种场景下，集群中的服务器通过 iSCSI 等方式连接到同一台共享的存储，并且通过锁等机制实现集群内部的同步。
LVM 自带的 locking 机制为 `lvmlockd`，支持 `dlm`（需要配置 dlm 与 corosync 构建集群）和 `sanlock` 两种后端。

不过很可惜的是，我们唯一使用到集群存储的地方是 Proxmox VE 虚拟机，而 PVE 使用的是另一套方案：
PVE 自带的集群管理功能使用了 `corosync` 维护了一个集群内部的全局锁，所有使用 PVE 工具修改存储的操作都会先获取这个全局锁。
并且 PVE 不存在多台机器访问同一个 LV 的情况，因此这一套方案不依赖于 `lvmlockd`。

<!-- TODO: 关于 corosync 和分布式系统相关的内容放在哪里呢？ -->

!!! warning "确保所有访问 LVM 的机器在同一个 PVE 集群中"

    否则在集群外的虚拟机创建等操作不会正确获取锁，导致**覆盖**已有的虚拟机磁盘。
    相关故障案例见 <https://vlab.ibugone.com/servers/ct100/#%E6%95%85%E9%9A%9C>。

!!! warning "LVM 集群不支持精简置备 LV"

    在虚拟化场景下，一个常见的节省空间的做法是使用精简置备（thin-provisioned）的存储，
    这么做可以在创建 LV 时只分配少量的空间，然后在需要的时候再分配更多的空间。
    但是 LVM 集群不支持这种操作（因此每个虚拟机都要实打实地占用对应的空间）。
    如果需要节约空间，可能需要考虑其他方案（例如部分企业级 SAN 支持类似于「虚拟地址」的功能，可以在需要的时候再分配空间）。

[^rhel-version]: 推荐查看最新版本的 RHEL 手册进行阅读，因为新版本可能包含一些新特性，并且 Debian 的版本更新比 RHEL 更快。本链接指向目前最新的 RHEL 9 的 LVM 手册。
[^time]: Retrieved on 2024-02-18.
[^bcachefs-principles]: "Buckets containing only cached data are discarded as needed by the allocator in LRU order" ([bcachefs: Principles of Operation](https://bcachefs.org/bcachefs-principles-of-operation.pdf) 2.2.4)
<!-- markdownlint-disable -->
[^t-p-t-bug]: Cache 的完整性检查工具 `cache_check` 位于 [thin-provisioning-tools](https://github.com/jthornber/thin-provisioning-tools) 中。其 1.0 版本使用 Rust 重写后[存在一个 bug](https://github.com/jthornber/thin-provisioning-tools/issues/294)，会导致即使检查失败，LVM 也会继续尝试挂载。该问题在 1.0.12 被修复。
