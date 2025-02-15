# 基础知识简介

!!! note "主要作者"

    [@Crabtux][Crabtux]

!!! warning "本文仍在编辑中"

在服务器运维的过程中，虚拟化技术的使用十分常见。运维人员可能会将服务器划分为若干虚拟机进行使用，或使用容器技术将应用进行包装与隔离；在需要管理大量服务器的场景下，虚拟化技术能够为集群管理提供底层支持，极大地提高了管理效率。

本部分介绍与虚拟化技术有关的常用术语和基础理论知识。

## 虚拟化技术简介

虚拟化技术是一种资源管理技术，它在下层计算资源与上层软件之间添加了一层抽象层，称为虚拟化层。虚拟化层负责分割、隔离并管理计算资源，并将资源划分为多个抽象的资源实例，提供给上层软件使用。上层软件拥有对抽象资源的完全控制权，然而，其对物理资源的使用会由虚拟化层进行调度和限制。

使用虚拟化技术可以带来许多好处：

- 资源隔离：在虚拟化层未被攻击成功的前提下，即使一个虚拟化实例被攻击，也不会影响其他虚拟化实例，从而提高安全性。
- 资源共享：一台物理主机可以运行多个虚拟化实例，每个虚拟化实例能够使用的资源都可以弹性分配，从而提高资源利用率。
- 环境迁移：虚拟化实例是软件定义的，抽象于具体硬件，因此虚拟化实例可以方便地移植到不同机器上运行。

根据虚拟化层所在的层级不同，虚拟化技术可以分出以下两种常见类型：

- 硬件虚拟化（Hardware virtualization）
- 操作系统级虚拟化（OS-level virtualization）

以下将具体介绍这两类虚拟化技术。

## 硬件虚拟化

### 概述

在硬件虚拟化技术中，物理主机被分割为一台或多台虚拟机（Virtual Machine）。每台虚拟机都可以看作一台独立的“计算机”，拥有自己的虚拟硬件（CPU、内存、硬盘、网络接口等），运行自己的操作系统和应用程序，通过虚拟化技术共享物理主机的硬件资源。

硬件虚拟化使得一台物理主机能够同时运行多个不同的操作系统，此时，被虚拟化的下层资源即为 CPU、内存、I/O 设备等硬件资源。用于创建、管理和执行虚拟机的虚拟化层被称为 Hypervisor，有时也被称为 Virtual Machine Monitor（VMM）。被虚拟化的物理主机称为宿主机（Host），而分割出的虚拟机称为客户机（Guest）。

在 1973 年的论文《Architectural Principles for Virtual Computer Systems》中，Robert P. Goldberg 将 Hypervisor 分成以下两类：

- Type-1/Native/Bare-metal Hypervisor

    - Hypervisor 直接运行在硬件上，可以直接调度硬件资源
    - 性能损耗低，适合在服务器环境下使用
    - 例：VMware ESXi、Xen、Microsoft Hyper-V

- Type-2/Hosted Hypervisor

    - Hypervisor 作为宿主机操作系统上的应用程序运行
    - 需要通过操作系统实现资源调度，因此性能损耗较高
    - 例：VMware Workstation、Oracle VM VirtualBox

Linux KVM 的情形较为特殊。作为内核模块，KVM 将 Linux 内核转变为一个 Type-1 Hypervisor，同时保留了内核的全部功能。因此，由 KVM 创建和调度的虚拟机会与内核下运行的常规进程共享硬件资源。

完整的硬件虚拟化解决方案除了提供 Hypervisor 这样的虚拟化基础设施之外，一般还会附带图形化管理界面和命令行接口，帮助管理员完成虚拟机配置。

### x86 虚拟化实现

对于 x86 平台，目前有多种技术路线来实现硬件虚拟化，包括：

- 完全虚拟化（Full Virtualization）
- 半虚拟化（Paravirtualization）
- 硬件辅助虚拟化（Hardware Assisted Virtualization）

以下将从 CPU、内存、I/O 虚拟化三个部分来简要介绍硬件虚拟化的实现。

!!! info "VMware Tools"

    待补充

#### CPU 虚拟化

由于 x86 架构在最初设计时未能考虑到虚拟化的需求，缺乏虚拟化的硬件支持，因此，在 x86 虚拟化技术发展的早期，一种实现 CPU 完全虚拟化的技术路线是，采用直接指令执行与二进制翻译相结合的方式，通过在运行时动态分析 Guest OS 执行的指令，用二进制翻译模块来替换掉其中难以虚拟化的指令，保证未经过修改的裸机程序（如操作系统内核）能够直接运行在虚拟机上。然而，动态二进制翻译实现起来相对复杂，且可能会带来较大的运行时开销。

实现 CPU 虚拟化的另一种技术路线是半虚拟化，有时又被称为操作系统辅助虚拟化（OS Assisted Virtualization），通过修改操作系统内核（如 Linux 这样的开源操作系统），或向操作系统中添加驱动（如 Windows 这样的闭源操作系统），使操作系统能与 Hypervisor 通过预先约定好的接口协作运行。这种虚拟化方式性能较为优越，且实现简单，但由于需要对每一类需要虚拟化的操作系统内核都进行单独修改或编写驱动，在灵活性上可能稍逊一筹。

到了 2006 年前后，Intel 与 AMD 先后发布了 VT-x 和 AMD-V 指令集扩展，从硬件层面提供了对虚拟化的支持。以 VT-x 为例，其引入了两个新的 CPU 运行模式（VMX root/non-root operation），分别交由 Hypervisor 和 Guest OS 使用，并从硬件层面实现权限控制。这种做法不仅能简化 Hypervisor 的实现，还大大减少了虚拟化带来的开销。目前，x86 平台上几乎所有 Hypervisor 的高效运行都依赖于这类方式。

<!-- TODO: 上述这些应该都是比较古代的做法，不知道是否需要补充更现代的做法 -->

#### 内存虚拟化

!!! warning "本节内容待补充"

#### I/O 虚拟化

在非虚拟化的环境下，操作系统内核通过驱动与 I/O 设备进行交互。从 CPU 的角度看，与设备的交互方式一般分为以下三种：

- 中断：当设备发生特定 I/O 事件时，通过中断信号通知 CPU，促使操作系统及时响应处理
- 寄存器访问：CPU 通过读写设备寄存器来控制设备状态或获取设备数据
- DMA：设备直接与内存进行数据交换，无需 CPU 介入控制

而在虚拟化架构中，Guest OS 与物理 I/O 设备之间多出了一个虚拟化层，它们之间的交互必须由虚拟化层妥善处理。为此，I/O 虚拟化需要：

- 向 Guest OS 提供设备接口
- 截获并处理 Guest OS 向设备发起的访问操作

以下将讨论几类主流的 I/O 虚拟化的实现方式。

##### 设备仿真

对于一些实现简单，且性能要求不高的 I/O 设备（如键盘、鼠标、简单网卡等），可以采用纯软件方式来完全模拟已有物理硬件的行为，并向 Guest OS 提供模拟的目标设备的接口。

这种虚拟化实现对于 Guest OS 是无感的，具有较好的兼容性，因为 Guest OS 可以直接使用现有的、为物理硬件实现的驱动来操作设备，不需要对 OS 做出任何修改或编写新的驱动；但对于 I/O 吞吐量较大的设备来说，纯软件实现可能带来无法忽略的性能开销。

##### 半虚拟化

在这种架构中，Guest OS 通过在 I/O 子系统上加以修改，能够感知到自己运行在虚拟化环境中，并与 Hypervisor 协同工作。

以 Xen 和 virtio 使用的「分离驱动」架构为例。在这种架构中，驱动被分为两个部分：运行在 Guest OS 上的前端驱动（front-end driver）和运行在 Hypervisor 上的后端驱动（back-end driver）。前端驱动向 Guest OS 提供标准的设备接口，而后端驱动则负责对实际物理硬件进行操作，前后端驱动之间通过预先约定的协议进行通信。

这种实现避免了设备仿真中硬件模拟复杂、Trap 开销大等问题，通过采用专门优化的通信接口与 Hypervisor 协同工作，在 I/O 性能上优于完全的软件仿真；并且，如果在虚拟化实现上定义了规范的标准接口，也具有一定的可移植性。

!!! info "virtio"

    待补充

##### 设备直通

在设备直通技术中，Hypervisor 将物理 I/O 设备直接分配给特定的虚拟机，使得该虚拟机能够直接与硬件进行交互，而无需经过中间的软件仿真或分离驱动层。这种方式可能依赖于硬件支持（例如 Intel VT-d 或 AMD IOMMU）来实现 DMA 重映射和中断隔离等功能。

设备直通的性能是最好的，几乎能够获得原生的 I/O 性能，但独占设备使得其灵活性稍差，在配置上可能会略微复杂，并且可能会存在兼容性问题。

!!! info "SR-IOV"

    待补充

## 操作系统层虚拟化

在操作系统级虚拟化（OS-level virtualization）中，虚拟化的对象是操作系统内核及其调度的系统资源，而不像硬件虚拟化那样直接对硬件资源进行虚拟化。每个虚拟化实例都认为自己独占操作系统内核及其所调度的资源，但实际上，这些虚拟化实例是共享内核资源的，并且仍受到操作系统内核的调度与限制。

这一类虚拟化技术一般依赖于操作系统内核提供的隔离与资源限制功能。例如，FreeBSD 内核提供的主要机制被称为 jail，以系统调用的形式提供使用接口，用于创建多个隔离的用户环境，提供更高的安全性；而 Linux 内核提供的机制比较多样化，例如：

- namespaces：将全局系统资源（PID、网络、挂载点等）隔离到不同的命名空间中，使得每个进程组拥有独立的资源视图
- cgroups：对进程组的使用的硬件资源（CPU、内存、磁盘 I/O 等）进行限制、监控和管理
- seccomp：限制进程所能够使用的系统调用

目前流行的、生态较好的虚拟化技术被称为容器（Containers），我们常用的 Docker 就属于一种容器实现。与 FreeBSD jail 相比，容器技术注重软件的可分发性，在 DevOps 领域中得到了广泛使用；当然，只要配置得当，容器同样也能实现较为可靠的安全隔离作用。关于容器技术的详细介绍，请参考本文档的 [容器](./container.md) 部分。

与硬件虚拟化相比，操作系统级虚拟化的开销较小，也不依赖于硬件支持，但受到实现原理的限制，无法运行不同内核的操作系统。

<!-- !!! note "API 兼容层"

    API 兼容层技术实现的是 API 级别的虚拟化，这种技术的典型代表是 Linux 平台下的 Wine 和 Windows 平台下的 Windows Subsystem for Linux 1（WSL1）。
    
    而 WSL2 中的 Linux 实例本质上是运行在 Hyper-V 虚拟化技术上的轻量级虚拟机，与 WSL1 的架构完全不同。
    
    请读者查阅资料，了解相关技术之间的差异。 -->

## 常见服务器虚拟化方案

### Proxmox VE (PVE)

Proxmox Virtual Environment（简称 Proxmox VE、PVE）是一个开源的服务器虚拟化环境 Linux 发行版。其使用基于 Ubuntu 的定制内核，包含安装程序、网页控制台和命令行工具，并且提供了 REST API 进行控制。

Proxmox VE 支持两类虚拟化技术：基于容器的 LXC 和硬件抽象层全虚拟化的 KVM。

![Web UI in PVE](https://pve.proxmox.com/pve-docs/images/screenshot/gui-qemu-summary.png)

![Web Console in PVE](https://www.vinchin.com/images/proxmox/proxmox-vm-backup-using-shell-command-1.png)

### VMware ESXi

VMware ESXi（简称 ESXi）是由 VMware 公司开发的一款企业级 Type-1 虚拟化平台，其提供了图形化管理工具（Web UI）、命令行接口（ESXi Shell 及配套工具）以及 API 接口，便于用户进行虚拟机管理和自动化运维。

ESXi 可以通过与 VMware vSphere 套件集成，实现如热迁移（vMotion）、高可用性（HA）等高级功能。

需要注意的是，ESXi 及 vSphere 是闭源的付费软件，并且从 2024 年开始不再提供免费版本。

![Web UI in ESXi](https://blogs.vmware.com/wp-content/uploads/sites/72/2016/04/ESXi-EHC.png)

![ESXi Shell](https://be-virtual.net/wp-content/uploads/2019/10/VMware-ESXi-01-SSH-Login.png)

### Microsoft Hyper-V

!!! warning "本节内容待补充"

### Xen

!!! warning "本节内容待补充"

## 参考资料

- [阿里云课程 - 虚拟化技术入门](https://edu.aliyun.com/course/313115/)
- [CTF Wiki - 虚拟化基础知识](https://ctf-wiki.org/pwn/virtualization/basic-knowledge/basic-knowledge/)
- [VMware White Paper - Understanding Full Virtualization, Paravirtualization, and Hardware Assist](#_11)
- [Intel® 64 and IA-32 Architectures Software Developer’s Manual Volume 3C: System Programming Guide, Part 3](https://cdrdv2.intel.com/v1/dl/getContent/671506)
- [Virtio: An I/O virtualization framework for Linux](https://developer.ibm.com/articles/l-virtio/)
- [Intel® Virtualization Technology for Directed I/O](https://cdrdv2-public.intel.com/774206/vt-directed-io-spec%20.pdf)
- Edouard Bugnion, Scott Devine, Mendel Rosenblum, Jeremy Sugerman, and Edward Y. Wang. 2012. Bringing Virtualization to the x86 Architecture with the Original VMware Workstation. ACM Trans. Comput. Syst. 30, 4, Article 12 (November 2012), 51 pages. <https://doi.org/10.1145/2382553.2382554>
- Paul Barham, Boris Dragovic, Keir Fraser, Steven Hand, Tim Harris, Alex Ho, Rolf Neugebauer, Ian Pratt, and Andrew Warfield. 2003. Xen and the art of virtualization. SIGOPS Oper. Syst. Rev. 37, 5 (December 2003), 164–177. <https://doi.org/10.1145/1165389.945462>
