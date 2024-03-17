# RAID

!!! warning "本文初稿已完成，但可能仍需大幅度修改"

本文介绍常见的 RAID 方案的使用与维护。
直接使用 LVM 创建 RAID 的方法请参考 [LVM](./lvm.md)；
使用 ZFS 创建 RAID 的方法请参考 [ZFS](./zfs.md)。

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

!!! comment "@taoky: 硬件 RAID，md/LVM，还是 ZFS？"

    选择何种方案，需要在系统部署前确定好，否则后续切换的代价极高。
    在约十年前，硬件 RAID 是很合理的方案，因为能够节省 CPU 计算资源，性能足够好，配置简单，而且服务器一般都会带个卡。
    但在今天，硬件 RAID 方案（以及块设备级别的软件 RAID 方案）可能不总是最佳选择了：

    - CPU 性能提升，使得软件 RAID 的计算开销不再是瓶颈
    - 软件 RAID 方案的监控与运维操作更方便
        - 考虑到厂商混乱的文档管理，我敢肯定大多数配置硬件 RAID 的运维都不太清楚如何使用 MegaCLI/StorCLI 来监控硬盘的状态
        - 如果没有人去机房（或者去机房的人 don't care），那么结果就是：RAID 6（或者 RAID 10）坏了一块盘 => 没人知道 => 又坏了一盘 => 还是没人知道（可能会发现服务器变慢了） => 又坏盘了 => 服务挂了，Boom，只能氪金（去数据恢复）了！
        - 而查看软件 RAID 的状态就方便得多
    - 不受制于闭源、无法调试的固件
        - 我们曾经遇到过在某台旧服务器上，硬件 RAID 卡固件多次崩溃的问题，此时整个阵列（包括系统盘）都会掉线
        - 并且没有人知道为什么——开放的软件 RAID 方案至少还有调试的机会
        - 商业 SAN 方案也有类似的问题——我们也遇到过 SAN 的管理口启动一会之后就直接坏掉的情况，而且无法处理（同样，没有人知道为什么）
    - 文件系统比块设备（和阵列卡）更懂数据
        - ZFS/Btrfs 的重建操作只会涉及到实际的数据块，而不会涉及到整个设备，减少重建时间与风险
        - ZFS/Btrfs 的 checksum 会在读取时检查数据的完整性，帮助处理 bit rot 问题（LVM 的 dm-integrity 也有类似的功能）
    
    所以目前的结论是：如果需要存储大量的数据，那么 ZFS 绝对值得一试（至于 Btrfs，可能需要至少等它的 RAID 5/6 实现稳定下来再说了）。

    当然了，如果你在使用 Windows Server，那么硬件 RAID……大概仍然还是一个挺不错的选择？
    如果愿意吃螃蟹的话，也可以试试 ReFS……

### 获取管理软件

MegaCLI 是早期的 MegaRAID 管理工具，之后被 StorCLI 取代，但是某些型号的旧阵列仅支持 MegaCLI。
由于博通的文档管理混乱，找到需要的管理软件并不是一件容易的事情。
这里提供了一些链接：

!!! warning "尽可能从官方来源获取这些工具"

    即使会麻烦一些，在下载前确认来源站点（在这里是博通）是非常重要的。
    从不明网站下载工具存在很大的供应链攻击的风险。

- 用户手册：<https://docs.broadcom.com/docs/12353236>
- MegaCLI 下载：<https://docs.broadcom.com/docs-and-downloads/raid-controllers/raid-controllers-common-files/8-07-14_MegaCLI.zip>（SHA256 `d9b152ae3dab76a334b9251702dba3311ceed91b58aaf52d916eb4ba1c2ab6e9`）
- StorCLI 下载：<https://docs.broadcom.com/docs/1232743397>

压缩包中包含的是 rpm 包，在非 rpm 系的发行版上可以使用 `rpm2cpio` 解压后手动「安装」：

```console
$ rpm2cpio MegaCli-8.07.14-1.noarch.rpm | cpio -div
./opt/MegaRAID/MegaCli/MegaCli
./opt/MegaRAID/MegaCli/MegaCli64
./opt/MegaRAID/MegaCli/libstorelibir-2.so.14.07-0
11194 blocks
```

将解压出的文件（一般都在 `opt` 里面）放到合适的位置。
如果在运行时缺少库（例如 `libncurses.so.5`），安装对应的包即可。

MegaCLI 与 StorCLI 的操作有许多不同，下面主要展示 StorCLI 的操作。
MegaCLI 的相似命令会折叠给出（以下的例子中，两者展示的是不同的阵列）。

!!! tip "使用时加上 `-NoLog` (MegaCLI) / `nolog` (StorCLI) 参数"

    MegaRAID 的这两个工具默认每次执行都会在当前工作目录创建日志文件，可以使用 `-NoLog` 或 `nolog` 参数禁用。

!!! tip "StorCLI 的 JSON 支持"

    StorCLI 支持输出 JSON 格式的信息，这对程序化解析 RAID 阵列状态很有帮助。
    在命令的最后添加 ` J` 即可，如：

    ```console
    $ sudo ./storcli64 /c0 show all nolog J
    {
    "Controllers":[
    {
      "Command Status" : {
    （以下省略）
    ```

### 基础概念

MegaRAID 支持管理多个 RAID 控制器（Adapter/Controller），每个控制器可以连接一个或多个机柜（Enclosure），
机柜中有物理磁盘（Physical Drive, PD），这些磁盘可以组成虚拟磁盘（Virtual Drive, VD 或 Logical Drive, LD）。

因此我们可以查看控制器，以及其控制的机柜、物理/虚拟磁盘的相关信息：

```console
$ sudo ./storcli64 /c0 show all nolog  # /c0 表示控制器 0，也可以使用 /call 表示所有控制器
Generating detailed summary of the adapter, it may take a while to complete.

CLI Version = 007.1513.0000.0000 Apr 01, 2021
Operating system = Linux 5.10.0-21-amd64
Controller = 0
Status = Success
Description = None
（以下省略；上面的部分每次 storcli 正确执行时都会输出，所以下面也会省略）
$ sudo ./storcli64 /c0 /eall show all nolog  # 也可以使用 /e252 表示机柜 252
...
Enclosure /c0/e252  :
===================
（以下省略）
$ sudo ./storcli64 /c0 /e252 /sall show all nolog
...
Drive /c0/e252/s0 :
=================

--------------------------------------------------------------------------------
EID:Slt DID State DG     Size Intf Med SED PI SeSz Model                Sp Type 
--------------------------------------------------------------------------------
252:0     8 Onln   0 9.094 TB SATA HDD N   N  512B HGST HUH721010ALE600 U  -    
--------------------------------------------------------------------------------
（以下省略）
$ sudo ./storcli64 /c0 /vall show all nolog
...
/c0/v0 :
======

--------------------------------------------------------------
DG/VD TYPE  State Access Consist Cache Cac sCC      Size Name 
--------------------------------------------------------------
0/0   RAID6 Optl  RW     Yes     NRWTC -   ON  36.380 TB      
--------------------------------------------------------------
（以下省略）
```

??? note "MegaCLI alternative"

    ```console
    $ sudo ./MegaCli64 -AdpallInfo -a0 -NoLog  # 使用 -aALL 表示所有控制器
                                            
    Adapter #0

    ==============================================================================
                        Versions
                    ================
    Product Name    : PERC 6/i Integrated
    Serial No       : 1122334455667788
    FW Package Build: 6.3.3.0002
    （以下省略）
    $ sudo ./MegaCli64 -EncInfo -a0 -NoLog
                                         
    Number of enclosures on adapter 0 -- 1

    Enclosure 0:
    Device ID                     : 32
    （以下省略）
    $ sudo ./MegaCli64 -PDList -a0 -NoLog
                                            
    Adapter #0

    Enclosure Device ID: 32
    Slot Number: 2
    Drive's position: DiskGroup: 1, Span: 0, Arm: 0
    Enclosure position: N/A
    Device Id: 2
    WWN: 
    Sequence Number: 2
    Media Error Count: 0
    Other Error Count: 50107
    Predictive Failure Count: 0
    Last Predictive Failure Event Seq Number: 0
    PD Type: SATA
    （以下省略）
    $ sudo ./MegaCli64 -LDInfo -Lall -a0 -NoLog
                                            

    Adapter 0 -- Virtual Drive Information:
    Virtual Drive: 0 (Target Id: 0)
    Name                :sys
    RAID Level          : Primary-1, Secondary-0, RAID Level Qualifier-0
    Size                : 931.0 GB
    Sector Size         : 512
    Mirror Data         : 931.0 GB
    State               : Degraded
    Strip Size          : 64 KB
    Number Of Drives    : 2
    Span Depth          : 1
    Default Cache Policy: WriteBack, ReadAheadNone, Direct, No Write Cache if Bad BBU
    Current Cache Policy: WriteBack, ReadAheadNone, Direct, No Write Cache if Bad BBU
    Default Access Policy: Read/Write
    Current Access Policy: Read/Write
    Disk Cache Policy   : Disk's Default
    Encryption Type     : None
    Is VD Cached: No
    （以下省略）
    ```

### 维护操作

#### 电池状态

MegaRAID 控制器一般会有一个电池（Battery Backup Unit, BBU）用于保护缓存中的数据。
当意外断电的情况发生时，电池会支撑控制器将缓存中的数据写入磁盘，以避免数据丢失。
在默认配置下，如果电池损坏，那么控制器不会使用缓存（WriteBack）模式，而是使用直写（WriteThrough）模式，造成写入性能下降。
在某些控制器上，这项功能是由称之为 CacheVault 的技术实现的。

```console
$ sudo ./storcli64 /c0 /bbu show all
...
Detailed Status :
===============

--------------------------------------
Ctrl Status Property ErrMsg     ErrCd 
--------------------------------------
   0 Failed -        use /cx/cv   255 
--------------------------------------
$ # 这里提示使用 /cx/cv 查看 CacheVault 的状态
$ sudo ./storcli64 /c0 /cv show all
...
Cachevault_Info :
===============

--------------------
Property    Value   
--------------------
Type        CVPM02  
Temperature 20 C    
State       Optimal 
--------------------
（以下省略）
```

??? note "MegaCLI alternative"

    ```console
    $ sudo ./MegaCli64 -AdpBbuCmd -a0 -NoLog
                                            
    BBU status for Adapter: 0

    BatteryType: BBU
    Voltage: 3991 mV
    Current: 0 mA
    Temperature: 22 C
    Battery State: Optimal
    （以下省略）
    ```

    MegaCLI 可能不支持 CacheVault。

!!! note "RAID 5/6 write hole 问题"

    在讨论 RAID 5/6 的可靠性，以及为什么 btrfs 一直没有稳定的 RAID 5/6 支持时，经常会提到 write hole 问题。
    在 RAID 5/6 阵列中，在每块盘写入的数据都需要保持一致性（包括 parity），但是阵列的写入操作不是「原子」的。
    这意味着每次写入时，阵列在事实上有一小段时间是不一致的。
    如果突然断电，就可能产生不一致。如果这种不一致出现在 parity 中，这样的错误不可能被文件系统检测到，
    那么就可能在未来重建时恢复出错误的数据。

    对于硬件 RAID，设置电池一般即可解决这个问题。但是对于软件 RAID 来说就麻烦一些了。Linux 的 md 支持两种方法：
    设置一个额外的设备用来做 dirty stripe journal，或者对于 RAID 5，在 RAID 元数据中存储 partial parity log。

    ZFS 的 raidz1/2/3 不受 write hole 影响。

#### 完整性检查

!!! note "下面的部分内容没有命令输出展示"

    由于没有测试条件，因此下面的部分需要对磁盘状态作修改的内容仅作示例。

MegaRAID 阵列卡默认定期进行完整性检查（Consistency Check）与 Patrol Read；
前者检查阵列中的数据是否一致，后者检查物理磁盘是否有坏道等问题。
可以查看阵列的完整性检查与 Patrol Read 状态：

```console
$ sudo ./storcli64 /c0 show cc nolog
...
Controller Properties :
=====================

-----------------------------------------------
Ctrl_Prop                 Value                
-----------------------------------------------
CC Operation Mode         Concurrent           
CC Execution Delay        168 hours            
CC Next Starttime         02/17/2024, 03:00:00 
CC Current State          Active               
CC Number of iterations   110                  
CC Number of VD completed 0                    
CC Excluded VDs           None                 
-----------------------------------------------
$ sudo ./storcli64 /c0 show patrolRead nolog
...
Controller Properties :
=====================

---------------------------------------------
Ctrl_Prop               Value                
---------------------------------------------
PR Mode                 Auto                 
PR Execution Delay      168 hours            
PR iterations completed 18                   
PR Next Start time      09/17/2022, 03:00:00 
PR on SSD               Disabled             
PR Current State        Active 0             
PR Excluded VDs         None                 
PR MaxConcurrentPd      255                  
---------------------------------------------
```

!!! tip "检查阵列卡的时间"

    阵列卡的时间可能与系统时间不一致，可以使用 `/cx show time` (StorCLI) / `-AdpGetTime -ax` (MegaCLI) 查看。

??? note "MegaCLI alternative"

    ```console
    $ sudo ./MegaCli64 -AdpCcSched -Info -a0 -NoLog
    
    Adapter #0

    Operation Mode: Disabled
    Execution Delay: 168
    Next start time: 09/02/2023, 03:00:00
    Current State: Stopped
    Number of iterations: 0
    Number of VD completed: 0
    Excluded VDs          : None
    Exit Code: 0x00
    $ sudo ./MegaCli64 -AdpPR -Info -a0 -NoLog

    Adapter 0: Patrol Read Information:

    Patrol Read Mode: Auto
    Patrol Read Execution Delay: 168 hours
    Number of iterations completed: 591 
    Next start time: 02/26/2024, 21:00:00
    Current State: Stopped
    Patrol Read on SSD Devices: Disabled

    Exit Code: 0x00
    ```

#### 重建操作

在替换坏盘后，阵列卡会自动开始重建操作。
如果在有盘损坏时有热备盘（Spare），那么阵列卡会自动将热备盘加入阵列并开始重建。

默认情况下，阵列卡会在重建时限制 IO 性能，这个指标可以通过 `rebuildrate` 参数调整（默认为 30%）：

```console
$ sudo ./storcli64 /c0 show rebuildrate nolog
...
Controller Properties :
=====================

------------------
Ctrl_Prop   Value 
------------------
Rebuildrate 30%   
------------------
$ sudo ./storcli64 /c0 set rebuildrate=60 nolog
...
Controller Properties :
=====================

------------------
Ctrl_Prop   Value 
------------------
Rebuildrate 60%   
------------------
```

??? note "MegaCLI alternative"

    ```console
    $ sudo ./MegaCli64 -AdpGetProp RebuildRate -a0 -NoLog

    Adapter 0: Rebuild Rate = 30%

    Exit Code: 0x00
    $ sudo ./MegaCli64 -AdpSetProp RebuildRate -60 -a0 -NoLog

    Adapter 0: Set rebuild rate to 60% success.

    Exit Code: 0x00
    ```

在重建时，也可以查看重建的进度：

```console
sudo ./storcli64 /c0 /sx show rebuild nolog
```

??? note "MegaCLI alternative"

    ```console
    $ sudo ./MegaCli64 -PDRbld -ShowProg -PhysDrv [252:7] -a0 -NoLog

    Rebuild Progress on Device at Enclosure 252, Slot 7 Completed 8% in 39 Minutes.

    Exit Code: 0x00
    ```

#### 磁盘识别

在磁盘损坏的时候，托架上的 LED 灯一般会亮红或黄灯，便于搜索。
但是有的时候我们有找到某块硬盘的需求（即使它还没有被阵列卡识别为损坏）。
MegaRAID 的工具可以控制硬盘的 LED 灯，便于找到对应的硬盘。

```console
# 开始闪烁对应硬盘的 LED 灯
sudo ./storcli64 /c0 /e252 /s0 locate start nolog
# 停止闪烁
sudo ./storcli64 /c0 /e252 /s0 locate stop nolog
```

??? note "MegaCLI alternative"

    ```console
    # 开始闪烁
    sudo ./MegaCli64 -PdLocate -start -physdrv[252:0] -a0 -NoLog
    # 停止闪烁
    sudo ./MegaCli64 -PdLocate -stop -physdrv[252:0] -a0 -NoLog
    ```

!!! tip "还可以让阵列卡发出声音……"

    可以配置阵列卡在阵列出现异常情况时发出声音，这可以帮助在机房的系统管理员发现异常情况。
    可以使用 `show alarm` (StorCLI) / `-AdpGetProp AlarmDsply` (MegaCLI) 显示当前的配置情况。

    ```console
    $ sudo ./storcli64 /c0 show alarm nolog
    ...
    Controller Properties :
    =====================

    ----------------
    Ctrl_Prop Value 
    ----------------
    Alarm     ON    
    ----------------
    ```

## RAID 与文件系统

在 RAID 阵列中，"chunk" 指每块盘上的数据块大小，例如以下 RAID 0 的布局表：

| Disk 0 | Disk 1 |
| ------ | ------ |
| 0      | 1      |
| 2      | 3      |
| ...    | ...    |

其中的 0, 1, 2, 3 等每一项都是一个 chunk。Chunk 通常比扇区（512B 或 4KB）大得多，例如 64KB 或 128KB。
每行的 chunk 就组成条带（stripe）。
文件系统在格式化时，也可以提供 RAID 相关的信息，帮助合理布局数据。

对于 ext4 文件系统，`mkfs.ext4 -E` 中的 `stride` 与 `stripe_width` 参数可以用来提供 RAID 阵列的信息：

- `stride` 是 chunk 除以 block size（一般为 4k）的结果，即在移动到下一块盘之前会处理的 block 的数量
- `stripe_width` 是 stripe 的块数（stride * 实际数据盘数，不包含 parity 盘）

而对于 XFS 文件系统，其能够自动识别软件 RAID 的信息。在使用硬件 RAID 的情况下，则需要在 `mkfs.xfs -d` 的时候
考虑 `sunit` 与 `swidth` 参数：

- `sunit` 是 chunk 除以扇区（512B）的结果
- `swidth` 则是 `sunit` 乘以实际数据盘数

## 监控

### SMART 信息 {#smart}

阅读 SMART 信息可以帮助了解硬盘的健康状态。在服务器上，如果使用硬件 RAID，使用 `smartctl` 需要添加额外的参数来从 RAID 控制器获取真实的磁盘信息，例如下面的例子：

```console
$ sudo smartctl --scan
/dev/sda -d scsi # /dev/sda, SCSI device
/dev/sdb -d scsi # /dev/sdb, SCSI device
/dev/sdc -d scsi # /dev/sdc, SCSI device
/dev/sdd -d scsi # /dev/sdd, SCSI device
/dev/bus/4 -d megaraid,8 # /dev/bus/4 [megaraid_disk_08], SCSI device
/dev/bus/4 -d megaraid,9 # /dev/bus/4 [megaraid_disk_09], SCSI device
/dev/bus/4 -d megaraid,10 # /dev/bus/4 [megaraid_disk_10], SCSI device
/dev/bus/4 -d megaraid,11 # /dev/bus/4 [megaraid_disk_11], SCSI device
/dev/bus/4 -d megaraid,12 # /dev/bus/4 [megaraid_disk_12], SCSI device
/dev/bus/4 -d megaraid,13 # /dev/bus/4 [megaraid_disk_13], SCSI device
/dev/bus/4 -d megaraid,14 # /dev/bus/4 [megaraid_disk_14], SCSI device
/dev/bus/4 -d megaraid,15 # /dev/bus/4 [megaraid_disk_15], SCSI device
/dev/bus/0 -d megaraid,8 # /dev/bus/0 [megaraid_disk_08], SCSI device
/dev/bus/0 -d megaraid,9 # /dev/bus/0 [megaraid_disk_09], SCSI device
/dev/bus/0 -d megaraid,10 # /dev/bus/0 [megaraid_disk_10], SCSI device
/dev/bus/0 -d megaraid,11 # /dev/bus/0 [megaraid_disk_11], SCSI device
/dev/bus/0 -d megaraid,12 # /dev/bus/0 [megaraid_disk_12], SCSI device
/dev/bus/0 -d megaraid,13 # /dev/bus/0 [megaraid_disk_13], SCSI device
$ sudo smartctl -a /dev/sdd  # 直接查询只能看到没有意义的控制器信息
smartctl 7.2 2020-12-30 r5155 [x86_64-linux-5.10.0-21-amd64] (local build)
Copyright (C) 2002-20, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF INFORMATION SECTION ===
Vendor:               AVAGO
Product:              MR9361-8i
Revision:             4.68
Compliance:           SPC-3
User Capacity:        1,919,816,826,880 bytes [1.91 TB]
Logical block size:   512 bytes
Physical block size:  4096 bytes
Logical Unit id:      0x600605b00f17786026223e2d33c1767b
Serial number:        007b76c1332d3e22266078170fb00506
Device type:          disk
Local Time is:        Sun Feb 11 18:40:45 2024 CST
SMART support is:     Unavailable - device lacks SMART capability.

=== START OF READ SMART DATA SECTION ===
Current Drive Temperature:     0 C
Drive Trip Temperature:        0 C

Error Counter logging not supported

Device does not support Self Test logging
$ sudo smartctl -a /dev/bus/4 -d megaraid,8  # 添加参数可以看到真实的磁盘信息
（内容省略）
```

`smartctl -a` 的输出主要分为两个部分：information section 和 smart data section。

Information section 展示硬盘的基本信息，包括型号、序列号、容量、固件版本等。

??? example "一块 NVMe SSD 的信息示例"

    ```smartctl
    === START OF INFORMATION SECTION ===
    Model Number:                       INTEL SSDPEKNU020TZ
    Serial Number:                      PHKA119600MK2P0D
    Firmware Version:                   002C
    PCI Vendor/Subsystem ID:            0x8086
    IEEE OUI Identifier:                0x5cd2e4
    Controller ID:                      1
    NVMe Version:                       1.4
    Number of Namespaces:               1
    Namespace 1 Size/Capacity:          2,048,408,248,320 [2.04 TB]
    Namespace 1 Formatted LBA Size:     512
    Local Time is:                      Mon Feb 26 21:59:27 2024 CST
    Firmware Updates (0x14):            2 Slots, no Reset required
    Optional Admin Commands (0x0017):   Security Format Frmw_DL Self_Test
    Optional NVM Commands (0x005f):     Comp Wr_Unc DS_Mngmt Wr_Zero Sav/Sel_Feat Timestmp
    Log Page Attributes (0x0f):         S/H_per_NS Cmd_Eff_Lg Ext_Get_Lg Telmtry_Lg
    Maximum Data Transfer Size:         64 Pages
    Warning  Comp. Temp. Threshold:     77 Celsius
    Critical Comp. Temp. Threshold:     80 Celsius

    Supported Power States
    St Op     Max   Active     Idle   RL RT WL WT  Ent_Lat  Ex_Lat
    0 +     5.50W       -        -    0  0  0  0        0       0
    1 +     3.60W       -        -    1  1  1  1        0       0
    2 +     2.60W       -        -    2  2  2  2        0       0
    3 -   0.0250W       -        -    3  3  3  3     5000    5000
    4 -   0.0040W       -        -    4  4  4  4     3000   11999

    Supported LBA Sizes (NSID 0x1)
    Id Fmt  Data  Metadt  Rel_Perf
    0 +     512       0         0
    ```

??? example "一块 SATA SSD 的信息示例"

    ```smartctl
    === START OF INFORMATION SECTION ===
    Model Family:     Intel S4510/S4610/S4500/S4600 Series SSDs
    Device Model:     INTEL SSDSC2KB019T8
    Serial Number:    PHYF8314006P1P9DGM
    LU WWN Device Id: 5 5cd2e4 14fa8880b
    Firmware Version: XCV10165
    User Capacity:    1,920,383,410,176 bytes [1.92 TB]
    Sector Sizes:     512 bytes logical, 4096 bytes physical
    Rotation Rate:    Solid State Device
    Form Factor:      2.5 inches
    TRIM Command:     Available, deterministic, zeroed
    Device is:        In smartctl database [for details use: -P show]
    ATA Version is:   ACS-3 T13/2161-D revision 5
    SATA Version is:  SATA 3.2, 6.0 Gb/s (current: 6.0 Gb/s)
    Local Time is:    Mon Feb 26 22:13:57 2024 CST
    SMART support is: Available - device has SMART capability.
    SMART support is: Enabled
    ```

??? example "一块 SATA HDD 的信息示例"

    ```smartctl
    === START OF INFORMATION SECTION ===
    Model Family:     Hitachi Ultrastar A7K2000
    Device Model:     Hitachi HUA722020ALA330
    Serial Number:    JK11A4B8KKLUDX
    LU WWN Device Id: 5 000cca 222f24777
    Firmware Version: JKAOA3EA
    User Capacity:    2,000,398,934,016 bytes [2.00 TB]
    Sector Size:      512 bytes logical/physical
    Rotation Rate:    7200 rpm
    Form Factor:      3.5 inches
    Device is:        In smartctl database [for details use: -P show]
    ATA Version is:   ATA8-ACS T13/1699-D revision 4
    SATA Version is:  SATA 2.6, 3.0 Gb/s
    Local Time is:    Mon Feb 26 22:15:41 2024 CST
    SMART support is: Available - device has SMART capability.
    SMART support is: Enabled
    ```

??? example "一块 SAS HDD 的信息示例"

    ```smartctl
    === START OF INFORMATION SECTION ===
    Vendor:               WDC
    Product:              WUH721818AL5206
    Revision:             C240
    Compliance:           SPC-5
    User Capacity:        18,000,207,937,536 bytes [18.0 TB]
    Logical block size:   512 bytes
    Physical block size:  4096 bytes
    LU is fully provisioned
    Rotation Rate:        7200 rpm
    Form Factor:          3.5 inches
    Logical Unit id:      0x5000cca2a909e560
    Serial number:        3JG5ER6G
    Device type:          disk
    Transport protocol:   SAS (SPL-4)
    Local Time is:        Mon Feb 26 22:21:06 2024 CST
    SMART support is:     Available - device has SMART capability.
    SMART support is:     Enabled
    Temperature Warning:  Enabled
    ```

!!! warning "检查硬盘的固件版本"

    数据中心盘的 SSD 近年来有多起因为固件问题导致使用时间过长（几万小时）后盘坏掉的新闻：

    - [Time to Patch: HPE SSDs Will Fail After 32,768 Hours](https://www.pcmag.com/news/time-to-patch-hpe-ssds-will-fail-after-32768-hours)
    - [SSD drives' 40,000-hour "death bug" continues to catch enterprises unawares](https://www.thestack.technology/ssd-death-bug-40000-hours-sandisk/)

    对于服务器场景，这类事件一旦发生，后果极其严重，因为配置新服务器时，很多时候使用的盘型号是一样的，导致开机时间也是一样的，
    因此出现问题之后，所有盘都会在短时间内坏掉，RAID 的冗余再高也无力回天。

    即使是面向个人用户的产品，也出现过固件问题导致 SSD 在短时间内损坏的情况。
    因此检查固件版本（以及关注相关信息）是非常重要的。`smartctl` 提供的信息中包含了固件版本，可以用作搜索、自查的参考。

    一部分厂商提供了 fwupd 支持，可以直接进行固件版本的检查与升级；而另一些就需要自己去搜索相关工具进行升级。
    [我们的文档](https://docs.ustclug.org/faq/ssd/)记录了在两块盘遇到固件导致的损坏后升级 Intel SSD 固件（XCV10100 -> XCV10110）的惨痛经历，可以作为参考。

Smart data section 则展示了硬盘的 SMART 信息。其中**自检信息**与**错误记录**均会显示，其他的部分视硬盘类型而定。

??? example "一块 NVMe SSD 的 SMART 数据示例"

    ```smartctl
    === START OF SMART DATA SECTION ===
    SMART overall-health self-assessment test result: PASSED

    SMART/Health Information (NVMe Log 0x02)
    Critical Warning:                   0x00
    Temperature:                        38 Celsius
    Available Spare:                    100%
    Available Spare Threshold:          10%
    Percentage Used:                    2%
    Data Units Read:                    84,073,721 [43.0 TB]
    Data Units Written:                 61,243,095 [31.3 TB]
    Host Read Commands:                 447,275,235
    Host Write Commands:                1,184,078,579
    Controller Busy Time:               9,203
    Power Cycles:                       77
    Power On Hours:                     14,101
    Unsafe Shutdowns:                   25
    Media and Data Integrity Errors:    0
    Error Information Log Entries:      0
    Warning  Comp. Temperature Time:    0
    Critical Comp. Temperature Time:    0

    Error Information (NVMe Log 0x01, 16 of 256 entries)
    No Errors Logged

    Read Self-test Log failed: Invalid Field in Command (0x002)
    ```

    对于 NVMe SSD 来说，关注的重点是：

    - 写入量与寿命：Available Spare、Percentage Used、Data Units Written
    - 出现错误的次数：Media and Data Integrity Errors

??? example "一块 SATA SSD 的 SMART 数据示例"

    ```smartctl
    === START OF READ SMART DATA SECTION ===
    SMART overall-health self-assessment test result: PASSED

    General SMART Values:
    Offline data collection status:  (0x00)	Offline data collection activity
                        was never started.
                        Auto Offline Data Collection: Disabled.
    Self-test execution status:      (   0)	The previous self-test routine completed
                        without error or no self-test has ever 
                        been run.
    Total time to complete Offline 
    data collection: 		(    0) seconds.
    Offline data collection
    capabilities: 			 (0x79) SMART execute Offline immediate.
                        No Auto Offline data collection support.
                        Suspend Offline collection upon new
                        command.
                        Offline surface scan supported.
                        Self-test supported.
                        Conveyance Self-test supported.
                        Selective Self-test supported.
    SMART capabilities:            (0x0003)	Saves SMART data before entering
                        power-saving mode.
                        Supports SMART auto save timer.
    Error logging capability:        (0x01)	Error logging supported.
                        General Purpose Logging supported.
    Short self-test routine 
    recommended polling time: 	 (   1) minutes.
    Extended self-test routine
    recommended polling time: 	 (   2) minutes.
    Conveyance self-test routine
    recommended polling time: 	 (   2) minutes.
    SCT capabilities: 	       (0x003d)	SCT Status supported.
                        SCT Error Recovery Control supported.
                        SCT Feature Control supported.
                        SCT Data Table supported.

    SMART Attributes Data Structure revision number: 1
    Vendor Specific SMART Attributes with Thresholds:
    ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
    5 Reallocated_Sector_Ct   0x0032   100   100   000    Old_age   Always       -       0
    9 Power_On_Hours          0x0032   100   100   000    Old_age   Always       -       41492
    12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       22
    170 Available_Reservd_Space 0x0033   100   100   010    Pre-fail  Always       -       0
    171 Program_Fail_Count      0x0032   100   100   000    Old_age   Always       -       0
    172 Erase_Fail_Count        0x0032   100   100   000    Old_age   Always       -       0
    174 Unsafe_Shutdown_Count   0x0032   100   100   000    Old_age   Always       -       18
    175 Power_Loss_Cap_Test     0x0033   100   100   010    Pre-fail  Always       -       2561 (22 65535)
    183 SATA_Downshift_Count    0x0032   100   100   000    Old_age   Always       -       0
    184 End-to-End_Error_Count  0x0033   100   100   090    Pre-fail  Always       -       0
    187 Uncorrectable_Error_Cnt 0x0032   100   100   000    Old_age   Always       -       0
    190 Drive_Temperature       0x0022   079   073   000    Old_age   Always       -       21 (Min/Max 19/27)
    192 Unsafe_Shutdown_Count   0x0032   100   100   000    Old_age   Always       -       18
    194 Temperature_Celsius     0x0022   100   100   000    Old_age   Always       -       21
    197 Pending_Sector_Count    0x0012   100   100   000    Old_age   Always       -       0
    199 CRC_Error_Count         0x003e   100   100   000    Old_age   Always       -       0
    225 Host_Writes_32MiB       0x0032   100   100   000    Old_age   Always       -       1627966
    226 Workld_Media_Wear_Indic 0x0032   100   100   000    Old_age   Always       -       1177
    227 Workld_Host_Reads_Perc  0x0032   100   100   000    Old_age   Always       -       20
    228 Workload_Minutes        0x0032   100   100   000    Old_age   Always       -       2489558
    232 Available_Reservd_Space 0x0033   100   100   010    Pre-fail  Always       -       0
    233 Media_Wearout_Indicator 0x0032   099   099   000    Old_age   Always       -       0
    234 Thermal_Throttle_Status 0x0032   100   100   000    Old_age   Always       -       0/0
    235 Power_Loss_Cap_Test     0x0033   100   100   010    Pre-fail  Always       -       2561 (22 65535)
    241 Host_Writes_32MiB       0x0032   100   100   000    Old_age   Always       -       1627966
    242 Host_Reads_32MiB        0x0032   100   100   000    Old_age   Always       -       407022
    243 NAND_Writes_32MiB       0x0032   100   100   000    Old_age   Always       -       8173747

    SMART Error Log Version: 1
    No Errors Logged

    SMART Self-test log structure revision number 1
    No self-tests have been logged.  [To run self-tests, use: smartctl -t]

    SMART Selective self-test log data structure revision number 1
    SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
        1        0        0  Not_testing
        2        0        0  Not_testing
        3        0        0  Not_testing
        4        0        0  Not_testing
        5        0        0  Not_testing
    Selective self-test flags (0x0):
    After scanning selected spans, do NOT read-scan remainder of disk.
    If Selective self-test is pending on power-up, resume after 0 minute delay.
    ```

    这里主要关注 attributes 表中的值。Attributes 分为两类，"Pre-fail" 代表其异常预示着硬盘会在不久的将来出现问题，"Old_age" 则表示硬盘随时间老化的指标。
    Value 为 100（有些硬盘的起始值会更高）通常表示最佳指标，随着使用逐渐降低。Worst 则记录历史最差（最低）值，如果值低于阈值（Threshold），则代表硬盘出现了问题。

    对于 SSD 来说，除了 Pre-fail 以外，需要额外关注与 wearout（磨损）有关的指标。

??? example "一块 SATA HDD 的 SMART 数据示例"

    ```smartctl
    === START OF READ SMART DATA SECTION ===
    SMART Status not supported: ATA return descriptor not supported by controller firmware
    SMART overall-health self-assessment test result: PASSED
    Warning: This result is based on an Attribute check.

    General SMART Values:
    Offline data collection status:  (0x82)	Offline data collection activity
                        was completed without error.
                        Auto Offline Data Collection: Enabled.
    Self-test execution status:      (   0)	The previous self-test routine completed
                        without error or no self-test has ever 
                        been run.
    Total time to complete Offline 
    data collection: 		(21007) seconds.
    Offline data collection
    capabilities: 			 (0x5b) SMART execute Offline immediate.
                        Auto Offline data collection on/off support.
                        Suspend Offline collection upon new
                        command.
                        Offline surface scan supported.
                        Self-test supported.
                        No Conveyance Self-test supported.
                        Selective Self-test supported.
    SMART capabilities:            (0x0003)	Saves SMART data before entering
                        power-saving mode.
                        Supports SMART auto save timer.
    Error logging capability:        (0x01)	Error logging supported.
                        General Purpose Logging supported.
    Short self-test routine 
    recommended polling time: 	 (   1) minutes.
    Extended self-test routine
    recommended polling time: 	 ( 350) minutes.
    SCT capabilities: 	       (0x003d)	SCT Status supported.
                        SCT Error Recovery Control supported.
                        SCT Feature Control supported.
                        SCT Data Table supported.

    SMART Attributes Data Structure revision number: 16
    Vendor Specific SMART Attributes with Thresholds:
    ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
    1 Raw_Read_Error_Rate     0x000b   100   100   016    Pre-fail  Always       -       0
    2 Throughput_Performance  0x0005   133   133   054    Pre-fail  Offline      -       102
    3 Spin_Up_Time            0x0007   119   119   024    Pre-fail  Always       -       604 (Average 610)
    4 Start_Stop_Count        0x0012   100   100   000    Old_age   Always       -       104
    5 Reallocated_Sector_Ct   0x0033   100   100   005    Pre-fail  Always       -       0
    7 Seek_Error_Rate         0x000b   100   100   067    Pre-fail  Always       -       0
    8 Seek_Time_Performance   0x0005   121   121   020    Pre-fail  Offline      -       35
    9 Power_On_Hours          0x0012   084   084   000    Old_age   Always       -       113016
    10 Spin_Retry_Count        0x0013   100   100   060    Pre-fail  Always       -       0
    12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       104
    192 Power-Off_Retract_Count 0x0032   100   100   000    Old_age   Always       -       129
    193 Load_Cycle_Count        0x0012   100   100   000    Old_age   Always       -       129
    194 Temperature_Celsius     0x0002   181   181   000    Old_age   Always       -       33 (Min/Max 17/56)
    196 Reallocated_Event_Count 0x0032   100   100   000    Old_age   Always       -       0
    197 Current_Pending_Sector  0x0022   100   100   000    Old_age   Always       -       0
    198 Offline_Uncorrectable   0x0008   100   100   000    Old_age   Offline      -       0
    199 UDMA_CRC_Error_Count    0x000a   200   200   000    Old_age   Always       -       1

    SMART Error Log Version: 0
    No Errors Logged

    SMART Self-test log structure revision number 1
    No self-tests have been logged.  [To run self-tests, use: smartctl -t]

    SMART Selective self-test log data structure revision number 1
    SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS
        1        0        0  Not_testing
        2        0        0  Not_testing
        3        0        0  Not_testing
        4        0        0  Not_testing
        5        0        0  Not_testing
    Selective self-test flags (0x0):
    After scanning selected spans, do NOT read-scan remainder of disk.
    If Selective self-test is pending on power-up, resume after 0 minute delay.
    ```

    阅读 attributes 的方法参见上面的 SATA SSD 的示例。

??? example "一块 SAS HDD 的 SMART 数据示例"

    ```smartctl
    === START OF READ SMART DATA SECTION ===
    SMART Health Status: OK

    Grown defects during certification <not available>
    Total blocks reassigned during format <not available>
    Total new blocks reassigned <not available>
    Power on minutes since format <not available>
    Current Drive Temperature:     26 C
    Drive Trip Temperature:        85 C

    Accumulated power on time, hours:minutes 3632:21
    Manufactured in week 44 of year 2021
    Specified cycle count over device lifetime:  50000
    Accumulated start-stop cycles:  6
    Specified load-unload count over device lifetime:  600000
    Accumulated load-unload cycles:  155
    Elements in grown defect list: 0

    Error counter log:
            Errors Corrected by           Total   Correction     Gigabytes    Total
                ECC          rereads/    errors   algorithm      processed    uncorrected
            fast | delayed   rewrites  corrected  invocations   [10^9 bytes]  errors
    read:          0        0         0         0          3       1235.896           0
    write:         0        0         0         0         30        595.461           0
    verify:        0        0         0         0         28          0.000           0

    Non-medium error count:        0

    No Self-tests have been logged
    ```

安装 smartmontools 之后，可以启用 smartd 服务（smartd.service 或 smartmontools.service）。
该服务会每隔一段时间检查硬盘的 SMART 信息，并在发现问题时发送邮件通知管理员（在正确配置的情况下）。
默认 Debian 提供的 `/etc/smartd.conf` 的有效内容如下：

<!-- TODO: 201 需要有配置邮件传输代理 (MTA) 的内容 -->

```conf
DEVICESCAN -d removable -n standby -m root -M exec /usr/share/smartmontools/smartd-runner
```

`/usr/share/smartmontools/smartd-runner` 会调用 `/etc/smartmontools/run.d/` 下的文件，
其中默认提供的 `10mail` 会使用系统的 `mail` 命令发送邮件。

??? example "邮件样例"

    ```
    This message was generated by the smartd daemon running on:

       host name:  example
       DNS domain: vm.example.org

    The following warning/error was logged by the smartd daemon:

    Device: /dev/sdh [SAT], FAILED SMART self-check. BACK UP DATA NOW!

    Device info:
    INTEL SSDSC2KB019T8, S/N:PHYF830400R01P9DGM, WWN:5-5cd2e4-14fa2d6ae, FW:XCV10165, 1.92 TB

    For details see host's SYSLOG.

    You can also use the smartctl utility for further investigation.
    The original message about this issue was sent at Fri Jan 12 02:51:00 2024 CST
    Another message will be sent in 24 hours if the problem persists.
    ```

在配置中添加 `-M test` 可以在启动时发送测试邮件。更多配置详情请参考 [`smartd.conf(5)`][smartd.conf.5]。

### RAID 信息

Linux 系统下的软件 RAID 方案一般都会提供使用邮件通知管理员异常情况的功能。
mdadm 与 ZFS 方案均支持邮件通知。而 LVM 不包含这样的功能，需要系统管理员额外设置定时任务来检查。

<!-- TODO: 内容需要扩充、测试 -->

除了在异常情况下发送邮件通知，还可以使用相关的指标监控工具来监控 RAID 以及硬盘 SMART 等信息。
以 telegraf 为例，自带的与健康度相关的插件包括 mdstat (mdadm) 与 smart。
编写自己的监控插件也很方便。

<!-- TODO: 一个到「指标监控与告警」的 link -->

!!! note "USTCLUG 目前的方案"

    我们的 RAID 目前主要有 ZFS (zpool) 与硬件 RAID 两种。前者我们使用的方案是 <https://github.com/iwvelando/telegraf-exec-zpool-status>，
    而后者是 @taoky 编写的 [raid-telegraf](https://github.com/ustclug/raid-telegraf)。

    可用于导入的 [Grafana.com Dashboard 分享页面](https://grafana.com/grafana/dashboards/20645-raid-and-ssd/)，[Grafana Dashboard JSON](../../assets/RAID%20and%20SSD-1709828565742.json)，以及[参考效果](https://monitor.ustclug.org/d/SonKmbWnk/raid-and-ssd?orgId=1)。

## 紧急救援

!!! danger "数据无价，谨慎操作！"

    如果不满足以下任一条件，请咨询专业的数据恢复公司，不要轻易尝试自行操作：

    - 数据的价值不高，可以承受丢失的风险
    - 有足够的时间、精力，以及购置临时存储的硬盘的预算
    - 有足够的盘能被识别，并能够读取大部分的内容

!!! tip "也可阅读 Hackergame 2021 题目「阵列恢复大师」的官方题解"

    相关内容基于真实的事件改编。该题目要求选手从完整未损坏但配置未知的 RAID 盘组中恢复数据。
    题目描述与题解参见 <https://github.com/USTC-Hackergame/hackergame2021-writeups/tree/master/official/%E9%98%B5%E5%88%97%E6%81%A2%E5%A4%8D%E5%A4%A7%E5%B8%88>。

尽管没有人会想经历这样的事情，但是这种事情确实有可能会发生，特别是在缺少经验，或监控设施不完善的情况下。
不过一条可能不算那么糟糕的经验是：在阵列因为硬盘问题下线的时候，最后一块报告损坏的硬盘很多时候仍然可以读取大部分内容，
不过在此之前的坏盘可能就没那么好运了——插在电脑上如果发出了怪声音，那么多半是真的坏了。

那么首先我们需要获取所有还能读取的硬盘，dump 出对应的块设备全部的内容。这个过程会很漫长，而且需要大量的存储空间。
大部分人可能会首先考虑使用 `dd` 来做这个事情，但是在这种场合下，`dd` 不是非常可靠——如果遇到了 I/O 错误，那么 `dd` 默认的行为是
直接退出，即使添加了 `conv=noerror` 选项，[其填充的行为也是不可控的](https://superuser.com/questions/622541/what-does-dd-conv-sync-noerror-do/1075837#1075837)。因此，这里推荐使用 [ddrescue](https://www.gnu.org/software/ddrescue/manual/ddrescue_manual.html) 进行应急的读取全部块设备内容的工作（[参考操作](https://askubuntu.com/questions/146524/recover-files-from-ntfs-drive-with-bad-sectors)）。

在操作完成后，得到的文件建议设置只读或额外备份，避免后续操作出现意外。

如果使用的是软件 RAID，那么元数据一般位于硬盘/分区的开头，如果幸运的话，使用本地回环挂载为块设备后就可以直接使用对应的 RAID 工具挂载了；
但如果是硬件 RAID 的话，就没有这么幸运了——硬件 RAID 的元数据一般位于硬盘末尾，使用的格式为 [DDF（Disk Data Format）](https://www.snia.org/tech_activities/standards/curr_standards/ddf)。并且，没有通用的工具可以解析 DDF 格式的元数据[^mdadm-ddf]，因此需要自行判断 RAID 的配置，以及每块盘在其中的位置，可能需要在之后的挂载中多次试错后才能找到正确的配置。

对于 RAID 0 类型的配置（包括 RAID 10/01），`mdadm` 工具支持拼接多个（没有 mdadm superblock 的）块设备的内容组成 RAID，参考命令如下：

```console
sudo mdadm --build --assume-clean -c 128 --level=0 --raid-devices=8 --size=195364584 /dev/md0 /dev/mapper/disk1 /dev/mapper/disk2 /dev/mapper/disk3 /dev/mapper/disk4 /dev/mapper/disk5 /dev/mapper/disk6 /dev/mapper/disk7 /dev/mapper/disk8
```

如果是 RAID 5/6，`mdadm` 不支持直接拼接，需要使用 assemble 操作，但是对应的操作会覆盖掉每块盘开头的一部分[^dmsetup-cow]。
另一种方法是编写使用 fuse 的脚本挂载，更加灵活但是性能较差，脚本内容可参照「阵列恢复大师」的官方题解的后半部分。

在此次实际的事件中，最终成功挂载了文件系统。对文件检查后发现有部分文件损坏，但是这些文件都不重要，最终成功恢复了所有重要数据。

## 补充阅读 {#supplement}

- [MegaCli wrapper for LSI MegaRAID for Debian/Ubuntu/RHEL/CentOS](https://gist.github.com/demofly/53b26d7a3f12b3008716)：一个服务器运维的 MegaCLI 脚本，其中包含了一些可供参考的操作与推荐设置
- [Linux Raid Wiki](https://raid.wiki.kernel.org/)：Linux-raid 邮件列表的社区成员维护的 wiki，包含了大量有用的信息

[^mdadm-ddf]: mdadm 工具可能支持 DDF，但是在我们自行数据恢复的过程中没有成功操作，可能是硬件厂商的 DDF 格式与 mdadm 实现不符。
[^dmsetup-cow]: 通过使用 dmsetup 可以实现类似于 CoW 的操作：在只读的 image 上添加一层 CoW 的 overlay，相关脚本可以参考 <https://gist.github.com/coderjo/c8de3ecc31f1d6450254b5e97ea2c595>。
<!-- TODO: dmsetup 高级操作（扔高级内容里） -->