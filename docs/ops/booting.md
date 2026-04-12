---
icon: material/power
---

# 启动程序

!!! warning "本文编写中"

## 一般启动过程 {#general-booting-process}

常见的 x86 平台下 Linux 系统的启动过程一般可以划分为以下几个阶段：

- Firmware（固件）：计算机上电后最先执行的程序，负责硬件自检和初始化，并将控制权移交给 Bootloader。
- Bootloader（引导加载程序）：负责加载操作系统内核到内存，并将控制权移交给 Kernel。
- Kernel（内核）：负责内核空间（Kernel Space）的初始化，比如初始化中断例程、加载驱动、挂载根文件系统等，并最终启动 `init` 进程。
- Init（初始程序）：负责用户空间（User Space）的初始化，启动各种系统服务，比如 getty（tty 终端服务）、sshd（SSH 服务）等。

其中，Kernel 和 Init 阶段都属于 OS（操作系统）的启动过程，而 Firmware 和 Bootloader 阶段则独立于 OS 之外，属于计算机平台的启动过程。

其他平台（如 ARM、RISC-V）或其他系统（如 BSD、Windows）虽然在细节上有所不同，但整体的启动流程大体类似。

## Firmware {#firmware}

固件（Firmware）是计算机上电后最先执行的程序，存储在主板上的只读存储器（ROM/Flash/EEPROM 等）中，负责硬件自检和硬件初始化，并最终将控制权移交给 Bootloader。常见的 PC 和服务器上的固件主要有两种实现：传统的 BIOS 和现代的 UEFI。

### BIOS {#bios}

BIOS（Basic Input/Output System，基本输入/输出系统）最初是 IBM PC 的专有固件，但是由一些公司（如 Compag、Phoenix、AMI 等）进行逆向工程，创建了兼容 BIOS 的 IBM PC 兼容机。此后，BIOS 接口成为 PC 兼容机的事实标准，被广泛采用并沿用至今。

!!! tip "BIOS is not BIOS"

    需要注意的是，我们日常口头上说的 BIOS 其实大部分情况下指的是广义上的 BIOS，不仅包括传统的 IBM PC 兼容机上的 BIOS 实现，还包括基于 UEFI 规范实现的 UEFI BIOS 。真正意义上的传统 BIOS 已经逐渐被淘汰，现代计算机上更多使用的是基于 UEFI 规范的 BIOS 实现。

    本文中所指的 BIOS 均指传统的 IBM PC 兼容机上的 BIOS 实现。

### UEFI {#uefi}

UEFI（Unified Extensible Firmware Interface，统一可扩展固件接口）严格来说并不是一个固件实现，而是一套**固件接口规范**，由 UEFI Forum 负责维护（前身是 Intel 于 1998 年发布的 EFI 规范）。

UEFI 规范定义了固件与上层程序（Bootloader、OS 等）之间的标准接口，使得 Bootloader 和操作系统无需关心底层的具体硬件架构，从而实现跨平台的可移植性。

## Bootloader {#bootloader}

Bootloader（引导加载程序）通常存储在可引导设备（如硬盘、U 盘、光盘等）的特定位置（如 MBR、GPT 分区表中的 EFI System Partition 等）中，负责加载操作系统内核到内存，并将控制权移交给 Kernel。

通常，对于 Linux 系统来说，Bootloader 还需要将 initrd/initramfs（初始内存盘）加载到内存，并将相关信息（如内核命令行参数、initramfs 的位置等）传递给 Kernel，里面包含了内核启动所需的各种驱动和工具，帮助内核完成系统的初始化过程。

!!! question "为什么需要 Bootloader？"

    一个很自然的问题是，为什么需要 Bootloader？为什么不直接让 Firmware 加载 Kernel 呢？

    这是因为，Firmware 的设计目标只是去初始化硬件并提供一个基本的运行环境，它需要尽可能不去关心上层运行的程序是什么样的，不论是一个 Linux 系统，还是一个 Windows 系统，又或者只是一个运行在裸机上的打印 Hello World 到屏幕上的简单程序。

    而 Bootloader 的设计目标则是去负责初始化操作系统所需要的**初始状态**，比如对于 Linux 系统来说，Kernel 和 initramfs 需要被加载进内存，需要在指定位置填写好内核参数从而指定某些内核功能的启用等等。这些都需要一个单独的程序来完成，靠 Firmware 是无法胜任的。

### GRUB

### systemd-boot

## initramfs

### UKI

## init 进程

`init` 进程是 Linux 启动时运行的第一个进程，负责启动系统的各种服务并最终启动 shell。传统的 init 程序位于 `/sbin/init`，而现代发行版中它一般是指向 `/lib/systemd/systemd` 的软链接，即由 systemd 作为 PID 1 运行。

PID 1 在 Linux 中有一些特殊的地位：

- 不受 `SIGKILL` 或 `SIGSTOP` 信号影响，不能被杀死或暂停。类似地，即使收到了其他未注册的信号，默认行为也是忽略，而不是结束进程或挂起。
- 当其他进程退出时，这些进程的子进程会由 PID 1 接管，因此 PID 1 需要负责回收（`wait(2)`）这些僵尸进程。

### systemd

### 其他 init 系统
