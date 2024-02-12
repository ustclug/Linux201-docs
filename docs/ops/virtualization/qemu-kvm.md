# QEMU/KVM

!!! warning "本文仍在编辑中"

QEMU/KVM 是 Linux 服务器上常用的虚拟化方案。其分为运行在用户空间的 QEMU 和运行在内核空间的 KVM 两部分。QEMU 负责模拟硬件，KVM 则负责虚拟机的运行。

本部分将对 QEMU 和 KVM 基础知识和基本操作进行介绍。

## 组件介绍

### QEMU

QEMU（Quick Emulator）是一个开源的虚拟化软件，它通过动态二进制翻译来模拟 CPU，并提供一系列的硬件模型，可以模拟多种外设硬件。QEMU 可以在没有硬件加速的情况下独立运行，但这样其中的 CPU 部分是模拟指令的执行，性能低下。

此外 QEMU 也可以仅用于 CPU 指令和系统调用的翻译，不模拟硬件模型，这种模式称为 User Mode。主要用于运行不同于宿主系统 CPU 指令集的用户态二进制程序。

### KVM

KVM（Kernel-based Virtual Machine）是一种基于Linux内核的开源虚拟化解决方案。KVM将Linux转变成一个虚拟机监视器（Hypervisor）。它利用了现代处理器中的硬件虚拟化支持（例如Intel VT或AMD-V），以实现高性能的虚拟化。它专注于以最小的开销在Linux上提供安全和隔离的虚拟环境，同时维持接近原生的性能。它向用户空间提供了虚拟 CPU 和内存子系统的配置和执行控制相关接口，但 KVM 不包含硬件模型，不能独立构成虚拟机。

### QEMU/KVM

QEMU 与 KVM 的关系是互补的。当二者结合使用时，QEMU 负责提供软件模拟和用户界面，而 KVM 则在内核级别提供硬件加速支持。这种配合使得虚拟机能够以较低的性能开销运行，同时用户还可以享受到 QEMU 在设备模拟方面提供的灵活性。实际上，QEMU 通常作为用户空间的工具与 KVM 的内核虚拟化功能配合，一起形成了现代 Linux 环境中强大的虚拟化解决方案。

## 安装配置

现在大多数发行版提供的内核都包含 KVM 相关模块，也提供了 QEMU 的二进制包。因此在大多数情况下，KVM 无需进行任何配置，只需要安装 QEMU 的二进制包即可。

如果需要手动进行配置，以下内容可以作为参考。

??? info "KVM"

    以 x86 为例。

    1. 确保内核配置中包含了 KVM 相关模块。需要的配置项包括：
        - `CONFIG_KVM`
        - `CONFIG_KVM_INTEL` 或 `CONFIG_KVM_AMD`
        - EPT 支持等模块
    2. 加载 KVM 模块：`modprobe kvm_intel` 或 `modprobe kvm_amd`。
    3. 正确配置 `/dev/kvm` 字符设备的权限，使需要运行虚拟机的用户可以访问该设备。

??? info "QEMU"

    只需安装 QEMU 的二进制包。

    如果发行版不提供相关包，也可以从 [QEMU 官网](https://www.qemu.org/download/) 下载源码编译安装。

### 第一台虚拟机

以下实例命令用于启动一个使用 KVM, 带有双核 CPU，1GB 内存，使用一个名为 `example.img` 的磁盘镜像文件和用户态网络的虚拟机。

```bash
qemu-system-x86_64 \
    -enable-kvm \
    -m 1024 \
    -cpu host \
    -smp cores=2 \
    -drive file=example.img,format=raw,if=virtio \
    -nic user,model=virtio
```

这个命令的各个参数意义如下：

- `qemu-system-x86_64`: QEMU 的二进制文件名，这里表示运行 x86_64 架构的系统级模拟器。
- `-enable-kvm`: 启用 KVM。
- `-m 1024`: 分配 1024MB 内存。
- `-cpu host`: 使用宿主机 CPU 模型。
- `-smp cores=2`: 使用 2 个 CPU 核心。
- `-drive file=example.img,format=raw,if=virtio`: 使用 `example.img` 作为磁盘镜像，格式为 `raw`，使用 `virtio` 设备模型。
- `-nic user,model=virtio`: 使用用户态网络设备，使用 `virtio` 设备模型。

这只是创建虚拟机的一个基本示例，QEMU 提供了很多其他选项，可以让您定制网络、图形输出、设备等。

## 详细配置

### 块存储

#### 存储格式

QEMU 支持多种存储格式，每种格式都有其特定的优点和用途。以下是一些最常见的 QEMU 磁盘镜像格式：

1. raw: 这是最简单的磁盘镜像格式。它是未经过任何处理的磁盘镜像，没有任何元数据或附加特性。因为其简单性，它通常有最好的性能，并且可以直接被许多其他工具读取，比如 dd。如果主机文件系统支持稀疏文件，那么 raw 格式的磁盘镜像文件可以非常小，因为它只会在需要时才增长到所需大小。如果主机文件系统支持 hole-punching 操作，那么 raw 格式的磁盘镜像文件可以直接释放未使用的空间。
2. qcow2 (QEMU Copy-On-Write version 2): 这是QEMU最常用的磁盘镜像格式。它支持许多高级特性，如写时复制 (copy-on-write)，快照，压缩，加密和增量备份。

此外 QEMU 还支持许多其他磁盘格式，如 vmdk, vdi, vhdx 等。由于这些格式不是很常见，这里不再详细介绍。

#### 配置参数

QEMU 中存储分为存储后端和存储设备两个部分，分别使用 `-blockdev` 和 `-device` 参数进行配置。

`-blockdev` 参数用于配置存储后端，常用的配置语法如下：

```bash
-blockdev driver=<file|raw|qcow2>,node-name=<name>,file=<path>,<other opts>
```

其中 `raw` 和 `qcow2` driver 通常层叠在 `file` 后端上使用。`node-name` 参数用于指定该后端的名称，以便于后面引用。

`-device` 参数用于配置设备，常用的配置语法如下：

```bash
-device virtio-blk-pci,drive=<blockdev node name>,<other opts>
```

其中 `virtio-blk-pci` 是设备模型，`drive` 参数用于指定该设备的后端。除了 `virtio-blk-pci`，QEMU 还支持其他设备模型，如 `ide`，`scsi` 等。

此外，QEMU 还支持 `-drive` 参数用于同时配置存储后端和设备，其实例如下：

```bash
-drive file=example.img,format=raw,if=virtio
```

这种方式更加简洁，但不如 `-blockdev` 和 `-device` 参数灵活。当 `if` 选项值为 `none` 时，`-drive` 选项仅创建后端，不创建设备。

### 网络

QEMU 支持多种网络后端，包括 `user`，`tap`，`bridge` 等。其中 `user` 是最简单的网络后端，它使用宿主机的 NAT 网络进行网络连接。`tap` 则是最常用的网络后端，它使用主机上的 TAP 设备进行网络连接。`bridge` 与 `tap` 没有本质区别，它只是自动将创建的 tap 接口接到网桥上。

`-nic` 参数同时配置网络后端和设备，常用的配置语法如下：

```bash
-nic [tap|bridge|user|l2tpv3|vde|netmap|af-xdp|vhost-user|socket][,...][,mac=macaddr][,model=mn]
```

QEMU 支持多种网络设备模型，包括 `virtio`，`e1000`，`rtl8139` 等。其中 `virtio` 是性能最好的设备模型，且现在几乎所有 Linux 发行版均包含了对应驱动，因此大多数情况下直接使用该模型即可。

### 内存

!!! warning "本节内容待补充"

### CPU

!!! warning "本节内容待补充"

## 实用工具

### qemu-img

`qemu-img` 是 QEMU 提供的一个用于创建、转换和操作磁盘镜像的工具。它支持多种磁盘格式，可以方便地进行磁盘镜像的创建、转换、扩容等操作。

`qemu-img` 的详细用法和选项可以通过 `man qemu-img` 或 `qemu-img --help` 查看。

#### 创建

`qemu-img create` 命令用于创建磁盘镜像，基本用法如下：

```bash
qemu-img create -f <FORMAT:raw|qcow2|...> -o <OPTIONS> <IMAGE> <SIZE>
```

其中 `-f` 选项用于指定磁盘镜像格式，`-o` 选项用于指定格式相关的选项，`<IMAGE>` 为磁盘镜像文件名，`<SIZE>` 为磁盘镜像大小。

!!! tip

    创建 `qcow2` 格式的磁盘镜像时，可以使用 `-o preallocation=metadata` 选项指定预分配元数据，以提高性能。

#### 转换

`qemu-img convert` 命令用于转换磁盘镜像格式，基本用法如下：

```bash
qemu-img convert -f <SRC_FORMAT:raw|qcow2|...> -O <DST_FORMAT:raw|qcow2|...> -o <OPTIONS> <SRC_IMAGE> <DST_IMAGE>
```

其中 `-f` 选项用于指定源磁盘镜像格式，`-O` 选项用于指定目标磁盘镜像格式，`-o` 选项用于指定格式相关的选项，`<SRC_IMAGE>` 为源磁盘镜像文件名，`<DST_IMAGE>` 为目标磁盘镜像文件名。

#### 扩缩容

`qemu-img resize` 命令用于扩缩容磁盘镜像，基本用法如下：

```bash
qemu-img resize -f <FORMAT> [--shrink] <IMAGE> [+|-]<SIZE>
```

其中 `-f` 选项用于指定磁盘镜像格式，`--shrink` 选项用于指定是否收缩磁盘镜像，`<IMAGE>` 为磁盘镜像文件名，`<SIZE>` 为磁盘镜像大小。

需要注意的是，缩小镜像时，超过指定大小的数据将被截断丢弃，因此需要在镜像内部先进行文件系统容量调整和分区表调整操作，并需要小心计算各分区偏移量和目标镜像大小。

!!! tip
    缩容时，可以先将内部文件系统调整至最小大小，然后调整分区大小至目标大小，接着调整镜像大小，最后再将文件系统扩容至最大。在此过程中也需要小心计算涉及到的各种大小和偏移量。

### qemu-nbd

`qemu-nbd` 是 QEMU 提供的一个用于挂载磁盘镜像的工具。它可以将磁盘镜像文件映射为一个块设备，然后可以使用 `mount` 命令将其挂载到文件系统中，或者对该块设备进行其他操作。

使用前需要先加载 `nbd` 内核模块：

```bash
modprobe nbd
```

!!! warning "坑"
    `nbd` 默认创建很多 nbd 设备，占据大量设备号，如果主机上本来就已经有很多设备，在加载 `nbd` 模块的过程中可能因设备号分配失败而出错，在内核日志中留下一个 oops。这种情况下可以通过 `nbds_max` 参数限制 `nbd` 设备的数量。

    ```bash
    modprobe nbd nbds_max=2
    ```

然后可以使用 `qemu-nbd` 命令挂载磁盘镜像，常用命令如下：

```bash
qemu-nbd -c /dev/nbdX -f <FORMAT:raw|qcow2|...> --discard=<unmap|ignore> <IMAGE>
```

其中 `-c` 选项用于指定 nbd 设备号，`-f` 选项用于指定磁盘镜像格式，`--discard` 选项用于指定磁盘镜像支持的 TRIM/DISCARD 操作，`<IMAGE>` 为磁盘镜像文件。如果需要只读挂载，可以指定 `-r` 选项。`qemu-nbd` 的其他用法和选项可以通过 `man qemu-nbd` 或 `qemu-nbd --help` 查看。

## 管理工具

!!! warning "本节内容待补充"

QEMU 直接运行参数众多，配置复杂，因此一般不直接运行 QEMU 命令，而是使用一些管理工具来创建和管理虚拟机，如 [libvirt](https://libvirt.org/)，[virt-manager](https://virt-manager.org/), [Proxmox VE](https://www.proxmox.com/en/proxmox-virtual-environment/overview) 等。
