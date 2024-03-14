# 基础知识简介

!!! warning "本文初稿已完成，但可能仍需大幅度修改"

服务器需要使用的存储方案与个人计算机的差异较大，例如：

- 服务器提供了大量的盘位，不同服务器的盘位使用的接口、磁盘的尺寸可能不同。
- 服务器一般提供 RAID 卡，可以在硬件层面实现 RAID 功能，大部分 RAID 卡也允许管理员设置直通到操作系统中，由操作系统实现 RAID 功能。
- 根据工作负载的不同，可能需要考虑不同文件系统的差异，并且选择合适的文件系统。
- 由于磁盘数量多，磁盘故障的概率也会增加，因此需要能够及时发现故障，并采取相应的措施。
- …………

本部分会对运维需要了解的基础知识进行介绍。

## 磁盘 {#disks}

### 磁盘类型简介 {#disk-type}

在服务器上最常见的为机械硬盘（HDD）和固态硬盘（SSD）。机械硬盘使用磁盘片和机械臂进行数据读写，固态硬盘使用闪存芯片进行数据读写。
除此以外，还可能有一些特殊的存储设备，例如磁带、Intel Optane 等，这里不做详细介绍。

一般来讲，单块机械硬盘的性能取决于 RPM（转速）。在估算时可以认为顺序读写带宽在 100 MB/s 左右，4K 随机读写带宽在 1 MB/s 左右，IOPS[^1] 在 100 左右。
而单块固态硬盘的顺序读写带宽在 500 MB/s (SATA) 或 1500 MB/s (NVMe) 以上，4K 随机读写带宽在 50 MB/s 左右，IOPS 在 10000 左右。
对于企业级硬盘，这些性能指标可能会更高。

硬盘的使用寿命的一项重要参数是 MTBF（Mean Time Between Failures，平均故障间隔时间）。
由于机械硬盘包含运动的部件，机械硬盘的 MTBF 一般会比固态硬盘低，大致在 10 万小时到 100 万小时。
尽管看起来很长，但是由于实际使用中的振动、温度、读写次数等因素，硬盘的实际寿命可能会远远低于 MTBF。
而对于 SSD 来说，一项更加重要的参数是 TBW（Total Bytes Written，总写入字节数），它表示了闪存芯片可以承受的总写入量，一般在几十到数千 TB；
读取操作对 SSD 的损耗可以忽略不计。

另一项与可靠性有关的重要参数是 Non-recoverable Read Error Rate（不可恢复读错误率），它表示了硬盘在读取数据时出现错误的**概率**。
对于机械硬盘来讲，这个值一般为 10^14 到 10^15，即**平均**每读取 10^14（12.5 TB）到 10^15（125 TB）位的数据中会有一位出现错误
（这不代表读取了 12.5/125 TB 之后就一定会遇到一次错误）。
而对于固态硬盘，一般为 10^16 到 10^17。
如果在重建 RAID 时遇到不可恢复错误（也被称为 URE）并且没有额外的 parity，那么重建操作会失败——即使在最好的情况下，也会丢失部分数据。

对具体的硬盘型号，建议阅读厂商的文档（例如 datasheet 等），以获取准确的信息。

!!! tip "Zoned storage，与叠瓦（SMR）盘"

    [Zoned storage](https://zonedstorage.io/) 是一种新型的硬盘存储技术，它将硬盘分为多个区域，每个区域的写入方式不同，
    通过暴露更多的信息给 OS 使得针对性的优化得以进行，以提升硬盘的容量和性能。
    我们常说的「叠瓦盘」就是一种 zoned storage。叠瓦盘通过重叠磁道的方式（类似于屋顶上瓦片排列一般）来增加存储密度。
    其写入和固态硬盘的闪存有一些相似：需要先读取临近磁道的数据，然后擦除整个区块，再重写，会很大程度影响写入性能。
    因此叠瓦盘内部通常划分为多个写入区域，以减小写入性能的影响。

    但是你在市面上可以买到的叠瓦盘几乎都没有暴露 zoned storage 的接口给操作系统（这些盘也被称为 Device-Managed SMR），
    因此在系统写入时仍会将其视为普通硬盘。
    这导致了叠瓦盘的性能远不及传统的非重叠磁道的硬盘。**硬盘厂商可能不会标注相关信息，因此在购买硬盘时需要特别注意。**

### 磁盘规格与尺寸 {#disk-size}

关于磁盘规格，在服务器安装时我们主要关心以下几点：

- 磁盘的尺寸（2.5 英寸、3.5 英寸）
    - 部分手册会将 2.5 英寸的磁盘称为 SFF（Small Form Factor），3.5 英寸的磁盘称为 LFF（Large Form Factor）。
- 磁盘的接口与协议（SAS、SATA、NVMe、M.2、U.2）
- 是否与服务器配置兼容：
    - 部分服务器会有硬盘白名单，只有白名单中的硬盘才能识别。
    - 使用的硬件 RAID 方案可能会对硬盘接口有要求，例如 SATA 和 SAS 接口的硬盘不能混用。

!!! warning "仔细阅读并确认厂商文档"

    一个现实中发生过的例子是：将错误的硬盘托架安装至服务器盘位，导致托架卡住无法取出，最后费了近半个小时，甚至用上了螺丝刀作为杠杆，才将其松动，取出硬盘。

磁盘需要带上托架才能安装到服务器中。托架的主要作用是固定住磁盘，并且方便安装和取出。托架的尺寸与磁盘的尺寸有关，3.5 英寸磁盘的托架一般需要安装转接板才能安装 2.5 英寸的磁盘，但也有一些托架预留了 2.5 英寸磁盘的螺丝孔位。同时，托架也一般有 LED 灯，在磁盘故障时会亮黄灯或红灯，也一般能够使用服务器的管理工具控制灯闪烁来定位磁盘。

<!-- TODO: 一张托架的照片 -->

### 磁盘接口与协议 {#disk-interface}

机械硬盘使用 SATA（Serial ATA）或 SAS（Serial Attached SCSI）接口连接，一些固态硬盘也会使用 SATA 接口。SATA 是个人计算机上最常见的硬盘连接方式，而 SAS 的接口带宽更高（虽然机械硬盘实际的传输速度通常无法跑满 SATA 的带宽），支持更多功能，并且向下兼容 SATA，因此在服务器上更常见。

SATA 与 SAS 的详细对比可参考[英文 Wikipedia 中 SAS 的 "Comparison with SATA" 一节](https://en.wikipedia.org/wiki/Serial_Attached_SCSI#Comparison_with_SATA)。

随着固态硬盘的普及，PCIe 接口的固态硬盘也越来越多见。PCIe 接口的固态硬盘通常使用 NVMe 协议，因此也被称为 NVMe SSD。NVMe SSD 常见的接口形态有 U.2、M.2 和 AIC（PCIe Add-in Card，即扩展卡）。

- M.2 接口的尺寸最小，在个人计算机上也更常见，甚至可以放入硬盘盒中作为小巧轻便的移动硬盘使用。

    - 常见的 M.2 接口有 B-key 和 M-key 两种，主流的 NVMe SSD 通常使用 M-key 接口，而 SATA SSD 通常使用 B-key 或 B+M（两个缺口）。一个 M.2 接口是否支持 NVMe 或 SATA 协议取决于主板或控制器，因此具体情况需要参考产品的说明书。
        - 作为参考，2023 年以来市面上已经见不到只支持 SATA 而不支持 NVme 的 M.2 接口了，尽管 M.2 SATA 的 SSD 仍然有卖。
    - 除了接口的形状，M.2 接口的长宽也有一系列选项，例如 2230、2242、2280、22110 等，即宽度为 22 mm，长度分别为 30、42、80、110 mm 等。个人电脑一般采用 2280 的尺寸，而服务器（和一些高端台式机主板）上可能会使用 22110 的尺寸。这些尺寸不影响接口的电气特性，只是为了适应不同的空间和散热需求。
  
- U.2 接口形状与 SAS 类似，但是**不兼容 SAS**（毕竟底层协议都不一样），且 2.5 英寸和 15 mm 以上厚度的外形相比 M.2 也具有更好的散热能力，是服务器上的常见形态。
- AIC 就是一块 PCIe 扩展卡，可以插入 PCIe 插槽中使用。

??? example "图片：M.2 SSD"

    <figure markdown="span">
      ![M.2 2280 SSD](https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Intel_512G_M2_Solid_State_Drive.jpg/500px-Intel_512G_M2_Solid_State_Drive.jpg)
      <figcaption>M.2 2280 SSD</figcaption>
    </figure>

??? example "图片：U.2 SSD"

    <figure markdown="span">
      ![U.2 SSD](https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/OCZ_Z6300_NVMe_flash_SSD%2C_U.2_%28SFF-8639%29_form-factor.jpg/620px-OCZ_Z6300_NVMe_flash_SSD%2C_U.2_%28SFF-8639%29_form-factor.jpg)
      <figcaption>U.2 SSD</figcaption>
    </figure>

??? example "图片：AIC SSD"

    <figure markdown="span">
      ![PCIe AIC SSD](https://m.media-amazon.com/images/I/61jyO1d8v1L.jpg)
      <figcaption>PCIe 插卡式 SSD</figcaption>
    </figure>

### S.M.A.R.T. {#smart}

磁盘的 S.M.A.R.T.（Self-Monitoring, Analysis and Reporting Technology，以下简称为 SMART）功能可以记录磁盘的运行状态，并且在磁盘出现故障前提供预警。SMART 可以记录磁盘的温度、读写错误率、磁盘旋转速度、磁盘的寿命等信息。

Linux 系统上可以安装 `smartmontools` 包来查看磁盘的 SMART 信息。使用以下命令查看可用的磁盘与其 SMART 状态：

```console
$ sudo smartctl --scan
/dev/nvme0 -d nvme # /dev/nvme0, NVMe device
$ sudo smartctl -a /dev/nvme0
（内容省略）
```

<!-- TODO: 可能放 RAID 里面还是不太合适，在这里完整讲 SMART 会比较好 -->
有关 SMART 指标解释与监控的内容将会在 [RAID](./raid.md#smart) 中介绍。

### Trim (Discard/Unmap) {#trim}

SSD 的闪存存储的特点是：不支持任意的随机写，修改数据只能通过清空区块之后重新写入来实现。并且区块能够经受的写入次数是有限的。
SSD 中的固件会进行区块管理，以将写入带来的磨损分散到所有区块中。但是，固件并不清楚文件系统的情况，因此在文件系统中删除某个文件之后，
SSD 固件会仍然认为对应的区块存储了数据，不能释放。Trim 操作由操作系统发出，告诉固件哪些区块可以释放，以提升性能，延长 SSD 使用寿命。一些特殊的存储设备也会支持 trim 操作，例如虚拟机磁盘（`virtio-scsi`）、部分企业级的 SAN 等。

??? note "关注存储的可用空间比例"

    不建议将存储的可用空间全部或接近全部耗尽，这是因为：

    - 机械硬盘：可用空间不足时，文件系统为了存储数据，会不得不产生大量磁盘碎片，而机械硬盘的随机读写性能很差；
    - 固态硬盘：可用空间不足会导致没有足够的空区块改写内容，因此可能不得不大量重复擦写已有的区块，加速磨损。

一般来说，确保 `fstrim.timer` 处于启用状态即可。一些文件系统也支持调整 trim/discard 参数（立即 discard 或周期性 discard，
一般推荐后者）。

## RAID

RAID（Redundant Array of Inexpensive Disks）是一种将多个磁盘组合在一起实现数据冗余和性能提升的技术。不同的磁盘组合方式称为“RAID 级别（RAID Level）”，常见的有 RAID 0、RAID 1、RAID 5、RAID 6、RAID 10 等。

RAID 0

:   也称作条带化（Striped），将数据分块存储在多个磁盘上，可以充分利用所有容量，获得叠加的顺序读写性能（但随机读写性能一般），但没有冗余，任何一块磁盘损坏都会导致整个阵列的数据丢失，适合需要高性能读写但不需要数据安全性的场景。

RAID 1

:   也称作镜像（Mirrored），将数据完全复制到多个磁盘上，提供了绝对冗余，整个阵列中只需要有一块盘存活，数据就不会丢失。代价是整个阵列的容量等单块磁盘的容量，空间利用率低下，适合需要高可靠性<s>而且不缺钱</s>的场景。同时由于每块盘上的数据完全一致，RAID 1 的读取性能可以叠加（甚至包括随机读取），但写入性能不会提升。

RAID 5

:   将数据和**一份**校验信息分块存储在多个磁盘上，可以允许阵列中任何一块磁盘损坏，兼顾冗余性和容量利用率。重建期间的性能会严重下降，并且一旦在重建完成前又坏了一块盘，那么你就寄了。

    !!! danger "不要为大容量机械硬盘阵列组 RAID 5"

        否则坏了一块盘后重建的时候就等死吧。
        
        下面的思考题也会涉及到这个问题。

RAID 6

:   将数据和**两份**校验信息分块存储在多个磁盘上，比 RAID 5 多了一份校验信息，可以容纳两块磁盘损坏，适合大容量或者磁盘较多的阵列。尽管允许两块盘损坏，但我们仍然建议在第一块盘损坏后立即更换并重建，不要等到更危险的时候。

RAID 10, 50, 60

:   将不同级别的 RAID 组合在一起，兼顾性能和冗余，各取所长，对于 10 块盘以上的阵列是更加常见的选择。例如 RAID 10 = RAID 1 + RAID 0，通常将每两块盘组成 RAID 1，再将这些 RAID 1 的组合拼成一个大 RAID 0。

!!! danger "磁盘阵列不是备份"

    RAID 不是备份，它可以实现在某块磁盘故障时保证系统继续运行，但是不能在数据误删除、自然灾害、人为破坏等情况下保护数据。

    [![磁盘阵列不是备份](../../images/raid-is-not-backup.png)](https://mirrors.tuna.tsinghua.edu.cn/tuna/tunight/2023-03-26-disk-array/slides.pdf)

    *图片来自[金枪鱼之夜：实验物理垃圾佬之乐——PB 级磁盘阵列演进](https://tuna.moe/event/2023/disk-array/)*

### RAID 等级比较 {#raid-compare}

| 等级    | 容量         | 冗余                           | 读写性能                                         | 适用场景                     |
| ------- | ------------ | ------------------------------ | ------------------------------------------------ | ---------------------------- |
| RAID 0  | 全部叠加     | 无，挂一块盘就寄了             | 顺序读写性能高，随机读写性能一般（略好于单块盘） | 临时数据、缓存               |
| RAID 1  | 单块盘       | 最高，只要有一块盘存活就行     | 叠加的读性能，但是只有单块盘的写性能             | 重要数据                     |
| RAID 5  | N-1 块盘     | 可以坏一块盘                   | 顺序读写性能高，随机读写性能差；重建期间**很差** | 兼顾容量和安全性             |
| RAID 6  | N-2 块盘     | 可以坏两块盘                   | 顺序读写性能高，随机读写性能差；重建期间**更差** | 比 RAID 5 更稳一点           |
| RAID 10 | 每组 RAID 1 容量叠加    | 每组 RAID 1 内只需要存活一块盘 | 顺序和随机性能都不错，并且重建期间还凑合         | 兼顾性能和安全性             |
| RAID 60 | （自行计算） | 每组 RAID 6 内可以坏两块盘     | 顺序读写性能不错，并且重建期间<s>更凑合了</s>    | 盘很多，并且兼顾容量和安全性 |

RAID 4 和 RAID 50 在这里不作讨论，因为它们没人用。

!!! question "思考题"

    1. 为什么 RAID 5 和 RAID 6 的重建期间性能会很差？
    2. 为什么将大量的磁盘组合成单个 RAID 6 不是一个好主意？
    3. 为什么说 RAID 5/6 有很高的写惩罚（Write Penalty）？
    4. 在[该帖子](https://v2ex.com/t/1018680)中，发帖人说自己组了 **14TB * 12** 的 **RAID 5**。
    假设这 12 块盘是机械硬盘，不可恢复读错误率为 10^14，如果仅考虑 URE，那么当损坏了一块盘重建时，重建成功的概率是多少？
    如果不可恢复读错误率为 10^15 呢？
        
        提示：假设为二项分布，前者结果接近于 0（几乎不可能成功），后者结果接近于 0.25（凶多吉少）。

### RAID 实现方式 {#raid-implementation}

RAID 可以在硬件层面实现，也可以在操作系统层面通过软件实现。

硬件：

- LSI MegaRAID 系列是最常见的硬件 RAID 卡
- HPE Smart Array 系列
- 一些专用的存储服务器，如 HPE MSA、Dell EMC PowerVault 等存储网络（SAN）设备
- Intel RST 和 Intel VMD，是个人计算机上常见的硬件 RAID 方案<s>（但是非常难用）</s>

Windows：

- 较早的“动态磁盘”功能支持 RAID 0、1、5 等级别，并且是在分区层面实现的，因此同一个硬盘组上可以同时存在多个采用不同 RAID 级别的卷（文件系统）
- 较新的 Windows 开始支持 Storage Spaces，可以实现更多 RAID 级别，以及“镜像加速”、“自动热迁移”等功能，但是比动态磁盘更加难用，重建也更复杂

Linux：

- mdadm 是 Linux 上最常见的软件 RAID 实现方式之一
- Linux 常用的逻辑卷管理工具 LVM 也支持 RAID 功能
- 一部分文件系统，如 ZFS 和 Btrfs，也支持 RAID 功能

服务器一般都配备了硬件 RAID 卡，如果需要使用软件 RAID，需要设置 RAID 卡或对应磁盘到 HBA 模式（也叫 JBOD/Non-RAID/直通 模式）。
一部分低端 RAID 卡不提供相关功能的支持，尽管可以通过为每块磁盘创建单独的 RAID 0 阵列实现类似的功能，但是并不推荐。

## 性能测试 {#benchmark}

我们可以使用 [`fio`](https://fio.readthedocs.io/en/latest/) 测试磁盘的性能，其支持在文件系统或者块设备上使用不同的 I/O 访问模式进行测试。

!!! info "使用 dd 测速的不足"

    以下是使用 dd 命令测试一块希捷4TB机械硬盘的例子：

    ```console
    # 测试写
    $ dd if=/dev/zero of=test.img bs=1M count=1000 oflag=direct
    1000+0 records in
    1000+0 records out
    1048576000 bytes (1.0 GB, 1000 MiB) copied, 11.3336 s, 92.5 MB/s
    # 测试读
    $ dd if=/dev/sda1 of=/dev/null bs=1M count=1000 iflag=direct
    1000+0 records in
    1000+0 records out
    1048576000 bytes (1.0 GB, 1000 MiB) copied, 6.68942 s, 157 MB/s
    ```

    虽然可以使用 dd 命令简易地测速，但是 dd 命令有一些缺点：
    
    - dd 只能测试顺序读写的情况，无法测试随机读写。
    - dd 使用非常低的 I/O 队列深度，无法充分测试设备的并发性能，这对于固态硬盘尤为明显。
    - dd 命令中使用的特殊设备 `/dev/urandom`、`/dev/random` 本身性能有限，可能会成为测试的瓶颈。（比如测试 `dd if=/dev/random of=/dev/null bs=1M count=1000` 可能只有 500MB/s 的速度）

    因此要对磁盘进行更加全面的性能测试，我们需要使用 fio 这款更加专业的工具。

使用 fio 进行测试需要确定以下基础参数，这些参数描述了 I/O 负载是什么样的：

- `--rw`：I/O 访问的模式，例如 `read`, `write`（顺序读写）, `randread`, `randwrite`（随机读写）, `randrw`（随机混合读写）等。
- `--bs`：每次 I/O 操作的块大小，默认为 4KB。bs 对性能影响很大，电商平台硬盘标称的速度通常都是 1MB 大块顺序读写的速度（代表了拷贝大文件时的速度），而更加影响实际使用体验的 4k 的随机读写性能则要弱得多。
- `--size`：测试文件的大小。支持 k/m/g/t/p 后缀（字节 B 可以省略），不区分大小写。使用 1024 倍率，要使用 1000 倍率，可以使用 `kib`, `mib` 等。

    !!! note "SI 与 IEC 单位"

        SI 单位是国际单位制中的单位，采用 10 进制（即 1 KB = 1000 B）；IEC 单位是国际电工委员会的单位，采用二进制和带有 i 的单位（即 1 KiB = 1024 B）。

        fio 出于对旧脚本的兼容性，默认情况下交换了 SI 和 IEC 单位的含义，即不带 i 的使用 1024 倍率，而带 i 的采用 1000 倍率。这在 fio 文档中有说明（参数 `kb_base`）。

- `--ioengine`：使用的 I/O 引擎。默认为 `psync`（使用 pread/pwrite 系统调用）。在 Linux 上推荐选择 `libaio` 来使用系统的异步 I/O 接口，此时建议添加 `--direct=1` 参数使用非缓冲 I/O，因为 Linux 上缓冲 I/O 不是异步的。
- `--iodepth`: 并发（处于未完成状态的）I/O 操作的数量，通常和异步 I/O 引擎结合使用。增加 `iodepth` 可以显著提高吞吐量。
- `--numjobs`：fork 若干进程执行相同的 I/O 任务，用于进行并发测试。此时建议添加 `--group_reporting` 参数，这样所有进程的数据会被累加到一起。

还有一些其他的参数影响 fio 如何运行：

- `--filename`：测试的文件名或者块设备名。fio 默认为每个任务生成单独测试文件，使用该选项使所有任务使用相同文件。使用相对路径时，可以使用`--directory`指定测试文件的目录（默认为当前目录）。
- `--name`：任务的名称。fio 可以同时运行多个测试任务，每个任务都有一个名称。命令行参数中每遇到一个 `--name` 会定义一个新任务，后面跟随该任务的参数。
- `--stonewall`：等待前一个任务完成才开始这一个任务，fio 默认所有任务是同时执行的。
- `--runtime`：测试的最大时间长度（无单位则为秒）。可以添加 `--time_based` 参数防止任务完成而提前结束
- `--readonly`：检查当前任务是否为只读任务，防止误操作导致数据丢失。
- `--loops`: 多次测试取平均值。

以下是一些例子，一部分在编写其他内容时使用到了：

!!! warning "对正在运行的块设备操作时需要小心"

    对已经有数据的块设备进行写入操作会导致数据丢失，在测试时请加上 `--readonly` 参数。

??? example "使用 fio 测试块设备（`/dev/mapper/vg201--test-lvdata`）随机读延迟的例子"

    本部分编写时参考了 [Oracle 的文档](https://docs.oracle.com/en-us/iaas/Content/Block/References/samplefiocommandslinux.htm)。

    一个只读情况下测试 10s `/dev/mapper/vg201--test-lvdata` 的 4K 随机读的例子如下：

    ```console
    $ sudo fio --filename=/dev/mapper/vg201--test-lvdata \
        --direct=1 --rw=randread --bs=4k \
        --ioengine=libaio --iodepth=1 --numjobs=1 \
        --time_based --group_reporting --name=readlatency-test-job \
        --runtime=10 --eta-newline=1 --readonly
    readlatency-test-job: (g=0): rw=randread, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=libaio, iodepth=1
    fio-3.36
    Starting 1 process
    fio: file /dev/mapper/vg201--test-lvdata exceeds 32-bit tausworthe random generator.
    fio: Switching to tausworthe64. Use the random_generator= option to get rid of this warning.
    Jobs: 1 (f=1): [r(1)][30.0%][r=233MiB/s][r=59.6k IOPS][eta 00m:07s]
    Jobs: 1 (f=1): [r(1)][50.0%][r=218MiB/s][r=55.9k IOPS][eta 00m:05s] 
    Jobs: 1 (f=1): [r(1)][70.0%][r=226MiB/s][r=57.8k IOPS][eta 00m:03s] 
    Jobs: 1 (f=1): [r(1)][90.0%][r=219MiB/s][r=56.1k IOPS][eta 00m:01s] 
    Jobs: 1 (f=1): [r(1)][100.0%][r=220MiB/s][r=56.2k IOPS][eta 00m:00s]
    readlatency-test-job: (groupid=0, jobs=1): err= 0: pid=1334208: Sat Feb 17 23:46:54 2024
    read: IOPS=56.0k, BW=219MiB/s (229MB/s)(2186MiB/10001msec)
        slat (nsec): min=1143, max=870047, avg=2109.53, stdev=1843.07
        clat (nsec): min=211, max=26562k, avg=14946.90, stdev=60736.24
        lat (usec): min=10, max=26564, avg=17.06, stdev=60.82
        clat percentiles (usec):
        |  1.00th=[   10],  5.00th=[   12], 10.00th=[   12], 20.00th=[   13],
        | 30.00th=[   13], 40.00th=[   13], 50.00th=[   13], 60.00th=[   13],
        | 70.00th=[   14], 80.00th=[   15], 90.00th=[   22], 95.00th=[   23],
        | 99.00th=[   52], 99.50th=[   76], 99.90th=[  174], 99.95th=[  243],
        | 99.99th=[  465]
    bw (  KiB/s): min=185288, max=249304, per=100.00%, avg=223874.11, stdev=13053.14, samples=19
    iops        : min=46322, max=62326, avg=55968.53, stdev=3263.28, samples=19
    lat (nsec)   : 250=0.01%, 500=0.01%, 750=0.01%, 1000=0.01%
    lat (usec)   : 2=0.01%, 4=0.01%, 10=1.43%, 20=87.06%, 50=10.48%
    lat (usec)   : 100=0.75%, 250=0.24%, 500=0.03%, 750=0.01%, 1000=0.01%
    lat (msec)   : 2=0.01%, 4=0.01%, 10=0.01%, 20=0.01%, 50=0.01%
    cpu          : usr=7.91%, sys=18.76%, ctx=560581, majf=0, minf=23
    IO depths    : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0%
        submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
        complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
        issued rwts: total=559688,0,0,0 short=0,0,0,0 dropped=0,0,0,0
        latency   : target=0, window=0, percentile=100.00%, depth=1

    Run status group 0 (all jobs):
    READ: bw=219MiB/s (229MB/s), 219MiB/s-219MiB/s (229MB/s-229MB/s), io=2186MiB (2292MB), run=10001-10001msec
    ```

??? example "向 `./test` 随机读写，模拟 I/O 压力"

    ```shell
    sudo fio --filename=./test \
      --filesize=2G --direct=1 --rw=randrw \
      --bs=4k --ioengine=libaio --iodepth=256 \
      --runtime=120 --numjobs=4 --time_based \
      --group_reporting --name=job_name --eta-newline=1
    ```

??? example "模拟 Crystal DiskMark 测试磁盘性能"

    本部分来自 [Raspberry Pi 4 B Review and Benchmark - What’s improved over Pi 3 B+](https://ibug.io/blog/2019/09/raspberry-pi-4-review-benchmark/#3-fio-microsd-card-speed-test)。

    ```shell
    sudo fio --loops=5 --size=500m --filename=fiotest.tmp --stonewall --ioengine=libaio --direct=1 \
        --name=SeqRead --bs=1m --rw=read \
        --name=SeqWrite --bs=1m --rw=write \
        --name=512Kread --bs=512k --rw=randread \
        --name=512Kwrite --bs=512k --rw=randwrite \
        --name=4KQD32read --bs=4k --iodepth=32 --rw=randread \
        --name=4KQD32write --bs=4k --iodepth=32 --rw=randwrite \
        --name=4Kread --bs=4k --rw=randread \
        --name=4Kwrite --bs=4k --rw=randwrite
    ```

由于性能测试的参数通常会很长，fio 还支持将参数放置在配置文件中，便于修改和重复使用。

fio 的配置文件被称为 job 文件，定义了一组需要模拟的 I/O 负载。fio 支持输入多个 job 文件，每个 job 文件会依次运行。而 job 文件内的任务默认是并行运行的，可以使用`stonewall`参数来保证串行。

Job 文件使用 ini 格式，通常包括一个 global 节定义共享参数和若干个 job 节定义每个 I/O 任务的参数（可以覆盖 global 节的参数）。

??? example "模拟 Crystal DiskMark 测试磁盘性能 job 文件"

    ```ini
    [global]
    ioengine=libaio
    direct=1
    size=4g
    runtime=60
    loops=3

    [Read SEQ1M Q8T1]
    bs=1m
    iodepth=8
    rw=read

    [Read SEQ1M Q1T1]
    stonewall
    bs=1m
    rw=read

    [Read RND4K Q32T1]
    stonewall
    bs=4k
    iodepth=32
    rw=randread

    [Read RND4K Q1T1]
    stonewall
    bs=4k
    iodepth=1
    rw=randread

    [Write SEQ1M Q8T1]
    bs=1m
    iodepth=8
    rw=write

    [Write SEQ1M Q1T1]
    stonewall
    bs=1m
    rw=write

    [Write RND4K Q32T1]
    stonewall
    bs=4k
    iodepth=32
    rw=randwrite

    [Write RND4K Q1T1]
    stonewall
    bs=4k
    iodepth=1
    rw=randwrite
    ```
    保存为`fio_CrystalDiskMark.ini`，然后运行
    ```console
    fio --filename=xxx fio_CrystalDiskMark.ini
    ```

fio 输出内容比较丰富，除了带宽 BW 外，还可以关注 IOPS、提交延迟 (slat)、完成延迟 (clat)、以及 iodepth 分布等。输出内容具体含义可以参考 man 手册 OUTPUT 节。

## 文件系统 {#filesystem}

在 Linux 上，ext4 是最常见的文件系统。但是对于某些需求，ext4 可能无法满足，例如：

- 需要支持存储大量文件，数量甚至可能超过 ext4 的限制
- 需要支持快照、透明压缩、数据校验等高级功能

在[「分区与文件系统」部分](filesystem.md)会对文件系统的选择进行介绍。
本部分主要介绍与文件系统、挂载等有关的通用内容。

### `/etc/fstab` {#fstab}

`/etc/fstab` 是 Linux 系统中用于配置文件系统挂载的文件。
在启动时，系统会根据 `/etc/fstab` 中的配置自动挂载文件系统。
如果配置不当，那么开机时就可能会出现挂载失败，从而进入紧急模式的情况。

下面给出一个在 QEMU 虚拟机中的 Linux 系统的 `/etc/fstab` 的例子：

```fstab
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
UUID=6cf8f654-9a14-4703-be4e-c5a059c9f7f8 /               ext4    errors=remount-ro 0       1
/dev/sr0        /media/cdrom0   udf,iso9660 user,noauto     0       0
sharing	/mnt/sharing	virtiofs	defaults,nofail	0	0
```

可以看到第一部分定位了文件系统的位置。对于物理磁盘来说，使用 UUID 是比较好的选择，详情可参考[分区与文件系统](./filesystem.md)中对 `/dev/disk` 的介绍。`/dev/sda1` 这样的设备名虽然也可以使用，但是可能会出现意料之外的问题。
对特殊的文件系统，这里的内容由对应的实现决定，例如 `tmpfs` 的话，这里可能就是 `none` 或者 `tmpfs`；
例子中的 `virtiofs` 是 QEMU 的虚拟文件系统，用于与宿主机共享文件，
由于设置中的 `target` 是 `sharing`，因此这里的设备名是 `sharing`。

后面则是挂载点、文件系统与挂载选项。挂载选项中大部分会提供给文件系统（例如这里的 `errors=remount-ro`），但是有一些是通用的设置。
例如 `noauto` 选项表示启动时不挂载，`nofail` 表示即使挂载失败也不影响启动。
一个在 [fstab(5)][fstab.5] 中没有提及的重要选项是 `_netdev`，它表示这个挂载点需要网络连接，
systemd 会配置启动时在网络配置好之后才挂载。
这个选项在挂载基于网络的存储时非常有用。

"dump" 可以忽略（0 即可），而 "pass" 标记了文件系统检查（fsck）的顺序：0 不检查，根分区应该为 1，其他分区为 2。

在修改配置后，如果系统使用了 systemd，应当使用 `systemctl daemon-reload` 来让 systemd 重新加载所有的 mount 单元。
否则 `mount -a` 之后，systemd 可能会「好心」地帮你改回来。

## 补充阅读 {#supplement}

[对 Linux 虚拟机上的永久性磁盘性能进行基准测试](https://cloud.google.com/compute/docs/disks/benchmarking-pd-performance?hl=zh-cn)：GCE 关于使用 fio 进行磁盘性能测试的文档。

[^1]: IOPS 为每秒的 I/O 操作数，可以简单认为是命令操作延迟的倒数。
