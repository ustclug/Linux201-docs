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

例如，Proxmox VE 是一个专为虚拟化场景打造的 Linux 发行版。它不仅提供直观的 Web UI 管理界面，还支持通过 Web Console、SSH 等方式连接到 Shell，以命令行方式进行高级配置。

![Web UI in PVE](https://pve.proxmox.com/pve-docs/images/screenshot/gui-qemu-summary.png)

![Web Console in PVE](https://www.vinchin.com/images/proxmox/proxmox-vm-backup-using-shell-command-1.png)

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

!!! warning "本节内容待补充"

<!-- 硬件设备的模拟？ -->

<!-- 设备运行方式（I/O 架构）：虚拟中断、虚拟寄存器访问、虚拟 DMA。 -->

<!-- 纯软件实现的完全虚拟化：效率低，可用于简单的设备模拟，如 QEMU 中的总线。 -->

<!-- 半虚拟化（PV）：重新定义 I/O 架构（Xen、KVM、Virtualbox） -->

<!-- 设备直通（Passthrough）：I/O 操作发往物理设备、捕获中断、DMA（通过 IOMMU，如 Intel VT-d）、SRIOV（将物理设备分割为多个虚拟设备）、virtio 驱动 -->

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

## Linux 下的虚拟化方案

### 底层：QEMU/KVM

关于 QEMU/KVM 的详细介绍，可以阅读本文档的 [QEMU/KVM](./qemu-kvm.md) 部分。

### 高层：Proxmox VE

Proxmox Virtual Environment（简称 Proxmox VE、PVE）是一个开源的服务器虚拟化环境 Linux 发行版。其使用基于 Ubuntu 的定制内核，包含安装程序、网页控制台和命令行工具，并且提供了 REST API 进行控制。

Proxmox VE 支持两类虚拟化技术：基于容器的 LXC 和硬件抽象层全虚拟化的 KVM。

## 参考资料

- [VMware White Paper - Understanding Full Virtualization, Paravirtualization, and Hardware Assist](#_7)
- [阿里云课程 - 虚拟化技术入门](https://edu.aliyun.com/course/313115/)
- [Intel® 64 and IA-32 Architectures Software Developer’s Manual Volume 3C: System Programming Guide, Part 3](https://cdrdv2.intel.com/v1/dl/getContent/671506)
- Edouard Bugnion, Scott Devine, Mendel Rosenblum, Jeremy Sugerman, and Edward Y. Wang. 2012. Bringing Virtualization to the x86 Architecture with the Original VMware Workstation. ACM Trans. Comput. Syst. 30, 4, Article 12 (November 2012), 51 pages. <https://doi.org/10.1145/2382553.2382554>
- Paul Barham, Boris Dragovic, Keir Fraser, Steven Hand, Tim Harris, Alex Ho, Rolf Neugebauer, Ian Pratt, and Andrew Warfield. 2003. Xen and the art of virtualization. SIGOPS Oper. Syst. Rev. 37, 5 (December 2003), 164–177. <https://doi.org/10.1145/1165389.945462>
