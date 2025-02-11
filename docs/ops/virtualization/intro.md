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

### 实现

对于 x86 平台，目前有多种技术来实现硬件虚拟化，包括：

- 全虚拟化（Full Virtualization）
- 半虚拟化（Paravirtualization）
- 硬件辅助虚拟化（Hardware Assisted Virtualization）

全虚拟化技术采用二进制翻译与直接指令执行相结合的方式来实现 CPU 虚拟化，能够保证不经过修改的裸机程序（如操作系统内核）能够直接运行在虚拟机上。

半虚拟化有时又被称为操作系统辅助虚拟化（OS Assisted Virtualization），它依赖于操作系统内核的修改来减少虚拟化带来的性能开销。使用半虚拟化技术的典型代表是 Xen，这是一个开源的 Hypervisor，官网：[Xen Project](https://xenproject.org/)。

<!-- TODO: 需要一些性能损耗的具体数据，我没有具体测试的数据 -->

到了 2006 年前后，Intel VT-x 和 AMD-V 扩展被加入。它们属于硬件辅助虚拟化技术，在 Ring 0 之下引入一个新的 CPU 执行模式，Hypervisor 特权指令和敏感指令的执行都会使 CPU 进入该模式，免去了二进制翻译和直接指令执行的需求。这两种技术出现之后，常常结合全虚拟化和半虚拟化使用，以减少性能损耗。

!!! note "I/O 设备直通（Passthrough）"

    在通常情况下，Guest OS 的 I/O 请求会发送给 Hypervisor 模拟出来的虚拟硬件，并交由 Hypervisor 处理与调度。然而，目前许多 Hypervisor 都已经支持 I/O 设备直通，这允许 Guest OS 直接使用物理设备。
    
    虚拟化 I/O 设备与直通设备各有优劣之处。一个显然的点是，直通降低了虚拟化带来的开销，但也使得虚拟机的可移植性和灵活性变差。
    
    选择将 I/O 设备进行虚拟化和直通是一项取舍，需要管理员根据实际情况进行选择。

## 操作系统层虚拟化

<!-- TODO: 这里应该是一个技术 Overview 和术语介绍的区域，其中的知识或许不应该局限于某一特定 OS（尤其是 Linux 下的容器技术） -->

在操作系统级虚拟化（OS-level virtualization）中，虚拟化的对象是操作系统内核及其调度的系统资源，而不像硬件虚拟化那样直接对硬件资源进行虚拟化。在这种模式下，每个虚拟化实例都认为自己独占操作系统内核及其所调度的资源，但实际上会受到真正操作系统内核的调度与限制。

目前最流行的操作系统层虚拟化技术被称为容器技术（Containers），它依赖于操作系统内核提供的资源隔离与限制等功能。

以 Linux 为例，其提供的隔离与限制机制包括：

- chroot
- namespaces
- cgroups
- apparmor

与硬件虚拟化相比，操作系统级虚拟化的开销较小，也不依赖于硬件支持，但其不能实现跨操作系统，目前一般用于应用隔离与部署、环境复现等场景。

关于 Linux 下容器技术的详细介绍，可以阅读本文档的 [容器](./container.md) 部分。

!!! note "API 兼容层"

    API 兼容层技术实现的是 API 级别的虚拟化，这种技术的典型代表是 Linux 平台下的 Wine 和 Windows 平台下的 Windows Subsystem for Linux 1（WSL1）。
    
    而 WSL2 中的 Linux 实例本质上是运行在 Hyper-V 虚拟化技术上的轻量级虚拟机，与 WSL1 的架构完全不同。
    
    请读者查阅资料，了解相关技术之间的差异。

## Linux 下的虚拟化方案

### 底层：QEMU/KVM

关于 QEMU/KVM 的详细介绍，可以阅读本文档的 [QEMU/KVM](./qemu-kvm.md) 部分。

### 高层：Proxmox VE

Proxmox Virtual Environment（简称 Proxmox VE、PVE）是一个开源的服务器虚拟化环境 Linux 发行版。其使用基于 Ubuntu 的定制内核，包含安装程序、网页控制台和命令行工具，并且提供了 REST API 进行控制。

Proxmox VE 支持两类虚拟化技术：基于容器的 LXC 和硬件抽象层全虚拟化的 KVM。

## 参考资料

- [VMware White Paper - Understanding Full Virtualization, Paravirtualization, and Hardware Assist](#_7)
