---
icon: material/cable-data
---

# InfiniBand 网络

!!! note "主要作者"

    [@Harry-Chen][Harry-Chen]

!!! warning "本文已完成，等待校对"

InfiniBand (IB) 是高性能计算中常用的高带宽、低延迟的网络互联技术。得益于其简单的部署方式和优秀的扩展能力，IB 网络被广泛应用于各种规模的计算集群中。在多年的发展中，IB 战胜了 Intel OmniPath 等技术，成为了 HPC 领域的事实标准。

!!! note "概念辨析：RDMA"

    在讨论 InfiniBand 网络和技术时，不可避免会提到 RDMA 技术。RDMA 是远程直接内存访问（Remote Direct Memory Access）的简称，指允许计算节点（通过网络）直接访问远程节点的内存，绕过操作系统内核的网络协议栈，从而实现低延迟和高吞吐量的数据传输。IB 网络是实现 RDMA 的一种常见技术，此外还有 RoCE（RDMA over Converged Ethernet）、iWARP 等技术也能实现 RDMA。

## IB 硬件 {#ib-hardware}

目前主流（也是几乎唯一）的 IB 硬件制造商为 Mellanox（在 2020 年被 NVIDIA 收购）。IB 网络通常由四类设备组成：

* 主机通道适配器（HCA, Host Channel Adapter）
* 目标通道适配器（TCA, Target Channel Adapter）
* 交换机：在子网（subnet）中连接多台 HCA 和 TCA 设备
* 路由器：连接不同子网的交换机，实现跨子网通信

考虑到 IB TCA 和路由器非常稀有，目前市面上几乎无法见到，本文中将只讨论 HCA（通常称为“IB 卡”）和交换机两类设备。

IB 网络有明确的代际划分，每两代之间最主要的差异就是带宽的提升。目前市面上还见到的 IB 设备主要有以下几代：

| 代号 | 带宽（每通道）| 通道数量 | 物理接口 | PCIe 链路 | Mellanox 型号 |
|------|---------------|----------|----------|-----------|--------|
| FDR | 14 Gbps | 4 | QSFP+ | PCIe 3.0 x8 | CX3, CX4 |
| EDR | 25 Gbps | 4 | QSFP28 | PCIe 3.0 x16 | CX4, CX5 |
| HDR | 50 Gbps | 4 | QSFP56 | PCIe 4.0 x16 | CX6 |
| NDR | 100 Gbps | 4 | OSFP / 2 &times; QSFP112 | PCIe 5.0 x16 | CX7 |

表格中的 "CX" 是 Mellanox 的品牌，全名为 ConnectX。除了 CX4 系列有覆盖两个 IB 代际的产品外，其他的系列都对应了一代 IB 标准。IB 标准都是向下兼容的，较新的网卡和交换机都能降级为较老的标准运行。

为了提升了网络的部署密度，从 HDR 开始，Mellanox 推出了“一拆二”的标准，如 HDR100 是只有两个通道启用的 HDR，速率为 100 Gbps；而 NDR200 则是只有两个通道的 NDR，速率为 200 Gbps。进一步地，从 NDR 开始，交换机侧“二合一”，改为使用八通道 OSFP 接口，每个端口通过线缆可拆分为两个四通道的 OSFP / QSFP112 接口，总共提供 800 Gbps 的速率。也就是说，一台 1U 的 36 口 OSFP NDR 交换机实际可以提供 72 个 800 Gbps OSFP / QSFP112 NDR 接口；再进一步拆分，等价于 144 个 400 Gbps QSFP112 NDR200 接口，背板速率达到了 57.6 Tbps。

!!! question "真的有这么快吗？"

    网卡的最高通信速率受到各个环节中最短板的制约，如交换机速率、（网络）通道数量、PCIe 版本和通道数量等。在采购设备和规划网络时，务必确认各个环节的速率均满足需求。

    常见的降速场景包括：

    * PCIe 版本降级或通道数量不足（如单口 HDR 卡插入了 PCIe 3.0 x16 的插槽，物理速率最大只有 128 Gbps）：可通过 `lspci -vv` 检查，或者观察 `dmseg` 中 `mlx5` 驱动程序的日志输出；
    * PCIe 总线带宽小于端口速率（如双口 HDR 卡在 PCIe 4.0 x16 的插槽上，对外传输速率不可能超过 256 Gbps）：可简单计算得出；
    * 网络通道速率降级或数量不足（如使用 EDR 交换机连接 HDR100 网口，则网卡降级为只有两通道的 EDR，速率为 50 Gbps；用一拆四的拆分线连接 NDR 交换机的 OSFP 端口和 NDR 网卡的 QSFP112 端口，则单卡速率类似也降级为 200 Gbps）：可通过端口速率确认；
    * 配置不正确：较新的 IB 卡依赖 PCIe Relaxed Ordering 等高级特性，若控制器不支持或 BIOS 无法启用，也会导致性能无法达到预期。

熟悉网络设备的读者可能会注意到，IB 标准中的各个速率、物理接口与以太网非常类似。
这并非巧合，而是因为二者确实共享同样的物理层，包括收发器、电气接口、线缆等，都使用相同的标准。如对此部分感兴趣，可参阅[《杰哥的知识库——以太网》](https://jia.je/kb/networking/ethernet.html)。

正因如此，绝大部分 IB 网卡都支持 VPI（Virtual Protocol Interconnect），仅需更改固件设置并重启，就能在同等速率的 IB 和以太网模式间自由切换（注：当然需要配合支持对应协议的交换机）。尽管如此，IB 和以太网仍然是两种截然不同的网络技术，在物理层以上，二者的协议栈、寻址方式、传输机制等均不相同，不能直接互联通信。

!!! warning "谨慎采购备件"

    虽说遵守的各类标准相同，但在采购如光模块、线缆等备件时，也不能随意地将以太网标准的产品用于 IB 设备上。
    这是因为 Mellanox 对此有比较严格的兼容性要求（或许是商业考虑？），未明确标明可用于 IB 网络的产品，很可能无法在相应设备上正常工作。

## IB 软件栈 {#ib-software}

### 前置知识 {#prerequisite}

在 RDMA 的抽象中，底层的网络设备和具体协议被称为 fabrics，而上层的通信接口则被称为 verbs。用户（程序员）可使用统一的 RDMA verbs 接口进行通信（如 `WRITE`, `READ`, `SEND` 等），而无须关心底层使用的是哪种 RDMA 技术。Verbs 还可以被封装为更高级的 API，成为 [Unified Communication X (UCX)](https://github.com/openucx/ucx) 等通信库；它们进一步地被 MPI、NVIDIA NCCL 等高层编程框架所使用，最终为高性能分布式计算提供支持。

### 驱动程序 {#drivers}

虽然 Linux 内核包含 [`mlx5` 驱动程序](https://www.kernel.org/doc/html/v6.17/networking/device_drivers/ethernet/mellanox/mlx5/index.html)，几乎可以做到开箱即用；Debian 等发行版也打包了相应的用户态工具（如 `rdma-core`, `libibverbs` 等），但为了获得更好的性能和稳定性，建议安装 Mellanox 官方提供的 [DOCA-OFED](https://developer.nvidia.com/doca-downloads?deployment_platform=Host-Server&deployment_package=DOCA-Host&target_os=Linux&Architecture=x86_64&Profile=doca-ofed) 驱动包（曾经称为 MLNX_OFED）。官方的安装十分好用，根据情况自行点击选择，并使用 `apt-get install doca-ofed` 即可完成安装。

??? tip "谨防捆绑销售"

    [DOCA](https://developer.nvidia.com/networking/doca) 软件栈包含了 NVIDIA 所有网络设备（包括 IB 卡、以太网卡、智能网卡等）的驱动、运行时、SDK、文档等，内容十分庞杂。我们仅需其中的 OFED 部分即可，不必安装多余的软件包。

OFED 的全称是 Open Fabrics Enterprise Distribution，这个名称表明其并非 NVIDIA 独有——话虽如此，目前也[没有其他厂商](https://stackoverflow.com/questions/58622347/what-is-the-difference-between-ofed-mlnx-ofed-and-the-inbox-driver)提供类似的软件包。

在 DOCA-OFED 安装的大量软件包中，比较重要、耦合比较紧密的包括：

* `{mlnx-ofed-kernel,srp,knem,iser,isert}-dkms`：通过 DKMS 编译的各类内核模块，提供网卡驱动和 RDMA 协议栈，以及各类扩展功能（如 SRP、iSER 等）；
* `lib{ibverbs,rdmacm,ibumad}`：用户态 RDMA 库和管理工具

这些组件必须从统一来源安装，即必须都来自于发行版（或内核自带），或者都来自于 DOCA-OFED，否则可能会出现微妙而难以解决的兼容性问题。更高层的库或者应用（如 `rdma-core`, `ucx`, `openmpi` 等）可以使用 OFED 自带的版本，也可以遵循 HPC 集群上的惯例，从源码编译安装，以便多版本共存。需要注意，编译时必须遵循从底层到高层的顺序，并打开相应的选项（如 UCX 的 `--with-rc`，OpenMPI 的 `--with-ucx`），才能真正利用硬件。

??? example "检查设备情况"

    在成功安装驱动程序后，可以通过多种方式查看 IB 设备的状态：
    
    ```text
    harry@foo:~$ ls /dev/infiniband/
    by-ibdev  by-path  issm0  issm1  rdma_cm  umad0  umad1  uverbs0  uverbs1
    
    harry@foo:~$ sudo ibstat
    CA 'mlx5_0'
            CA type: MT4129
            Number of ports: 1
            Firmware version: 28.40.1000
            Hardware version: 0
            Node GUID: 0xc470bd0300cf4964
            System image GUID: 0xc470bd0300cf4964
            Port 1:
                    State: Active
                    Physical state: LinkUp
                    Rate: 200
                    Base lid: 48
                    LMC: 0
                    SM lid: 48
                    Capability mask: 0xa751e84a
                    Port GUID: 0xc470bd0300cf4964
                    Link layer: InfiniBand
    
    harry@foo:~$ sudo ibstatus
    Infiniband device 'mlx5_0' port 1 status:
            default gid:     fe80:0000:0000:0000:c470:bd03:00cf:4964
            base lid:        0x30
            sm lid:          0x30
            state:           4: ACTIVE
            phys state:      5: LinkUp
            rate:            200 Gb/sec (4X HDR)
            link_layer:      InfiniBand
    
    harry@foo:~$ ibv_devinfo
    hca_id: mlx5_0
            transport:                      InfiniBand (0)
            fw_ver:                         28.40.1000
            node_guid:                      c470:bd03:00cf:4964
            sys_image_guid:                 c470:bd03:00cf:4964
            vendor_id:                      0x02c9
            vendor_part_id:                 4129
            hw_ver:                         0x0
            board_id:                       MT_0000000834
            phys_port_cnt:                  1
                    port:   1
                            state:                  PORT_ACTIVE (4)
                            max_mtu:                4096 (5)
                            active_mtu:             4096 (5)
                            sm_lid:                 48
                            port_lid:               48
                            port_lmc:               0x00
                            link_layer:             InfiniBand
    ```

    如果设备状态不正常，如长时间显示 `Intializing` 等状态，则说明 IB 子网状态不正常，请参考下一节配置子网管理器。

## IB 网络管理 {#network-management}

IB 网络贯彻了软件定义网络（Software Defined Networking, SDN）的理念，网络中的所有设备均由专门的子网管理器（Subnet Manager, SM）进行集中管理和配置。SM 负责为各个 HCA 和 TCA 分配 LID 地址、维护路由表、监控网络状态等工作。每个 IB 子网中必须至少运行一个 SM，且通常只有一个 SM 处于活动状态（Active），以避免冲突。

带管理的 IB 交换机（如 QM8700、QM9700 或者更高级型号）通常内置 SM 功能，可以直接配置为 SM 角色。如果整个网络中都只有不带管理的交换机（如 QM8790、QM9790 等），则需要在集群中的某台节点上运行有 SM 能力的软件。安装 OFED 驱动包时，通常会一并安装 `opensm` 软件，只要用 `systemctl enable --now opensmd` 启用即可。

!!! tip "启动不了？"

    如果 OpenSM 出现各种奇怪的问题（比如 segfault），首先要检查是否混用了来自发行版与 OFED 的软件包，其次不妨试一试升级你的 OFED，或许有奇效。

### 网络管理工具 {#network-management-tools}

`infiniband-diags` 软件包中带有大量 `ib` 开头的可执行文件，可用于诊断和检查 IB 网络的状态。这些工具通常需要管理员权限，并依赖与 `libibumad` 库。如：

* `ibnetdiscover`：发现并打印 IB 子网中的所有设备和连接关系（可能很长）
* `ibnodes`, `ibswitches`, `ibhosts`, `sminfo`：打印子网中的交换机、主机和 SM 信息
* `ibportstate`, `iblinkinfo`：打印端口状态和链路信息

`perftest` 软件包中则带有通常无需权限的 `ib_*` 系列的性能测试工具，可用于测试 IB 网络的带宽和延迟。如：

* `ib_read_lat`, `ib_write_lat`：测试 RDMA 操作的延迟；
* `ib_read_bw`, `ib_write_bw`, `ib_send_bw`, `ib_send_bw`：测试 RDMA 操作的带宽，通常测试值应该接近网卡的端口速率。

此外，也可通过上层应用测试 IB 网络的性能，如 UCX 自带的 `ucx_perftest` 套件，经典的 [OSU MPI Benchmark](https://mvapich.cse.ohio-state.edu/benchmarks/)、[nccl-tests](https://github.com/NVIDIA/nccl-tests) 等。

### GPUDirect RDMA

NVIDIA 的数据中心系列 GPU 均有 [GPUDirect RDMA](https://docs.nvidia.com/cuda/gpudirect-rdma/) 支持，允许第三方设备（如 IB 卡）直接读写 GPU 显存，从而大幅降低延迟、提升带宽。

如果要启用此功能，则需要保证：

1. IB 卡与 GPU 在同一个 PCIe 根复合体（Root Complex）下，如直连于同一个 CPU 的 PCIe 插槽，或者在同一个 PCIe 交换芯片下（可通过 `nvidia-smi topo -m` 或者 `lstopo` 等方式检查）；
2. 在安装 OFED 后再编译 NVIDIA GPU 驱动，以保证 `nvidia-peermem` 模块是使用 OFED 提供的内核头文件编译的；
3. 在加载 GPU 驱动后，加载 `nvidia-peermem` 模块。

GPUDirect RDMA 的支持没有直接检测的手段，部分通信库（如 [NCCL](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html#nccl-ib-cuda-support)）可通过环境变量来控制此功能的启用与否。

### IP over IB {#ipoib}

虽然 IB 网络不是以太网，但通过 IP over IB（IPoIB）协议，可以让 IB 支持 IP 协议栈，从而兼容现有的大量应用程序和工具。IPoIB 协议由内核模块 `ib_ipoib` 提供，安装 OFED 驱动包时会一并安装。启用 IPoIB 后，系统中会多出 `ib` 开头的虚拟网络接口，每个 IB 子网对应为一个 IPoIB 的广播域。此接口可通过标准的网络配置工具（如 `ip`, `ifconfig`, `netplan` 等）进行配置和管理，也可以运行任何 TCP/IP 负载。

??? question "高级网络功能"

    IPoIB 网络不提供传统意义上的 VLAN 支持，但可以通过配置 IB 子接口的方式实现；也不能通过链路聚合（bonding）进行负载均衡，而只能提供一定的冗余（failover）能力。具体配置方式请查阅文档。

虽然 IPoIB 提供了极大的便利性，但由于其额外的协议开销，性能通常低于直接使用 RDMA verbs 接口。因此在可能的情况下，应尽量使用原生 RDMA 协议进行通信，如将 iSCSI 替换为 [iSER](https://docs.nvidia.com/doca/sdk/iSER+-+iSCSI+Extensions+for+RDMA/index.html)，将 NFS 替换为 NFS over RDMA，将基于 TCP 的 MPI 替换为基于 UCX 的 MPI 等。此外，IPoIB 的默认 MTU 较低（通常为 2044 字节），也会影响性能，建议酌情调整（如 4092 或 65520 字节）。

### 设备管理工具 {#device-management-tools}

在安装 OFED 时，还会一并安装 `mft` 软件包，其中包含了 Mellanox Fabric Tools (MFT) 工具集。MFT 提供了大量管理和配置 IB 设备的工具，常用的包括：

* `mlxconfig`：用于查看和修改设备的配置参数，如启用/禁用 VPI 模式、强制设置链路速率等；
* `mlxfwmanager`, `flint`：用于升级和管理 Mellanox 设备的固件，后者更为底层；
* `mlxlink`, `mlxcables`：用于查看和配置链路和线缆信息；

这些工具通过私有协议与主机和网络上的 Mellanox 设备通信，能对设备进行复杂的配置，通常需要管理员权限才能运行。

??? example "工具使用示例"

    下面是使用 mlxcables 查询线缆信息的示例：
    
    ```text
    root@foo:~# mst start
    Starting MST (Mellanox Software Tools) driver set
    Loading MST PCI module - Success
    Loading MST PCI configuration module - Success
    Create devices
    Unloading MST PCI module (unused) - Success
    root@foo:~# mst cable add
    Added 1 mellanox cable devices.
    root@ja1:~# mlxcables
    Querying Cables ....
    
    Cable #1:
    ---------
    Cable name    : mt4123_pciconf0_cable_0
    >> No FW data to show
    -------- Cable EEPROM --------
    Identifier                     : QSFP28 (11h)
    Technology                     : Copper cable unequalized (a0h)
    Compliance                     : 50GBASE-CR, 100GBASE-CR2, or 200GBASE-CR4, HDR,EDR,FDR,    QDR,DDR,SDR
    Attenuation: 2.5GHz            : 3dB
                 5.0GHz            : 5dB
                 7.0GHz            : 6dB
                 12.9GHz           : 10dB
                 25.78GHz          : 0dB
    OUI                            : 0x0002c9
    Vendor                         : Mellanox
    Serial number                  : MT2115VS01418
    Part number                    : MCP1650-H002E26
    Revision                       : A4
    Temperature [c]                : N/A
    Digital Diagnostic Monitoring  : NO
    Length [m]                     : 2 m
    ```
    
    可以看到这是一根原装 HDR DAC（同时也支持 200G 以太网），长度是 2 米，型号是 MCP1650-H002E26。

!!! tip "注意更新固件"

    如果发现 IB 网卡有明显的性能或者稳定性问题，或者在升级系统 / OFED 后发生设备丢失等情况（即 PCIe 设备还存在，但无法识别为 IB 设备），则很可能是固件版本过旧导致的，更新固件或许可以解决这些问题。

    安装新的 OFED 软件包时，通常会一并为支持的型号安装最新的固件版本。但太老的卡或者 OEM 型号都不在自动升级的范围内，需要手工下载安装。可以参考[《杰哥的{运维，编程，调板子}小笔记——升级 Mellanox 网卡固件》](https://jia.je/hardware/2022/11/23/upgrade-mlnx-firmware/)获得一些经验。
