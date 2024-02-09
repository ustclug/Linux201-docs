# 存储系统

!!! warning "本文仍在编辑中"

服务器需要使用的存储方案与个人计算机的差异较大，例如：

- 服务器提供了大量的盘位，不同服务器的盘位使用的接口、磁盘的尺寸可能不同。
- 服务器一般提供 RAID 卡，可以在硬件层面实现 RAID 功能，大部分 RAID 卡也允许管理员设置直通到操作系统中，由操作系统实现 RAID 功能。
- 根据工作负载的不同，可能需要考虑不同文件系统的差异，并且选择合适的文件系统。
- 由于磁盘数量多，磁盘故障的概率也会增加，因此需要能够及时发现故障，并采取相应的措施。
- …………

本部分会对运维需要了解的基础知识进行介绍。

## 磁盘规格

关于磁盘规格，在服务器安装时我们主要关心以下几点：

- 磁盘的尺寸（2.5 英寸、3.5 英寸）
    - 部分手册会将 2.5 英寸的磁盘称为 SFF（Small Form Factor），3.5 英寸的磁盘称为 LFF（Large Form Factor）。
- 磁盘的接口与协议（SAS、SATA、NVMe、M.2、U.2）
- 是否与服务器配置兼容：
    - 部分服务器会有硬盘白名单，只有白名单中的硬盘才能识别。
    - 使用的硬件 RAID 方案可能会对硬盘接口有要求，例如 SATA 和 SAS 接口的硬盘不能混用。

!!! warning "仔细阅读并确认厂商文档"

    一个现实中发生过的例子是：将错误的硬盘托架安装至服务器盘位，导致托架卡住无法取出，最后费了近半个小时，甚至用上了螺丝刀作为杠杆，才将其松动，取出硬盘。

### 磁盘尺寸

磁盘需要带上托架才能安装到服务器中。托架的主要作用是固定住磁盘，并且方便安装和取出。托架的尺寸与磁盘的尺寸有关，3.5 英寸磁盘的托架一般需要安装转接板才能安装 2.5 英寸的磁盘，但也有一些托架预留了 2.5 英寸磁盘的螺丝孔位。

### 磁盘接口与协议

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

    <figure markdown>
      ![M.2 2280 SSD](https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Intel_512G_M2_Solid_State_Drive.jpg/500px-Intel_512G_M2_Solid_State_Drive.jpg)
      <figcaption>M.2 2280 SSD</figcaption>
    </figure>

??? example "图片：U.2 SSD"

    <figure markdown>
      ![U.2 SSD](https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/OCZ_Z6300_NVMe_flash_SSD%2C_U.2_%28SFF-8639%29_form-factor.jpg/620px-OCZ_Z6300_NVMe_flash_SSD%2C_U.2_%28SFF-8639%29_form-factor.jpg)
      <figcaption>U.2 SSD</figcaption>
    </figure>

??? example "图片：AIC SSD"

    <figure markdown>
      ![PCIe AIC SSD](https://m.media-amazon.com/images/I/61jyO1d8v1L.jpg)
      <figcaption>PCIe 插卡式 SSD</figcaption>
    </figure>
