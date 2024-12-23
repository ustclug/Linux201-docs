---
icon: simple/nvidia
---

# CUDA 环境简介

!!! note "主要作者"

    [@sscssc][sscssc]、[@taoky][taoky]

!!! warning "本文初稿（也许）已完成，但可能仍需大幅度修改"

CUDA（Compute Unified Device Architecture）是由 NVIDIA 公司推出的开发套件，它允许软件开发人员使用 NVIDIA 的 GPU（图形处理单元）进行通用计算，利用 GPU 强大的并行处理能力来加速计算密集型任务，常用于科学计算、工程模拟、机器学习等领域。

包含的组件包括：

- CUDA 驱动和运行时：CUDA 驱动与内核层驱动共同工作，与 GPU 交互；运行时提供了更高级别的 API，使开发者能够更方便地使用 GPU。

- CUDA 编译器（nvcc）：将 CUDA 代码转换成可以在 NVIDIA GPU 上运行的二进制代码的编译器。

- CUDA 库：优化过的数学与科学计算库，比如线性代数运算（cuBLAS）、傅里叶变换（cuFFT）等。

- CUDA 工具：比如性能分析器（NVIDIA Nsight 和 Visual Profiler）和调试工具，它们帮助开发者优化和调试 CUDA 应用程序。

## 配置 CUDA 环境

### 版本准备

在开始之前，你需要确认显卡是否支持所需的 CUDA 版本。在这里可以查看支持的列表：<https://developer.nvidia.com/CUDA-gpus>。

表中的 `Compute Capability` 代表计算能力，同时也表明了 GPU 支持的 CUDA 特性和指令集版本。架构越新的显卡，对应的计算能力数字越高。使用的 CUDA 版本需要能够支持对应的计算能力，可以查看此表：<https://docs.nvidia.com/datacenter/tesla/drivers/index.html#cuda-arch-matrix>。同时，CUDA 也对系统编译器版本有要求，可以查看此表：<https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#system-requirements>。

### 安装 NVIDIA 驱动

当我们说到「安装 CUDA」的时候，实际上指的是**两件事情**：

1. 安装 NVIDIA 的**内核态**驱动以及部分用户态组件（驱动），使得操作系统能够正确识别显卡并与之通信。
2. 安装 CUDA 运行时和开发工具（**用户态**），使得我们能够在程序中使用 CUDA API。

!!! note "NVIDIA 内核驱动"

     默认情况下，Linux 内核自带开源的 Nouveau 驱动。Nouveau 驱动大部分时候能够点亮屏幕，进行基础的图形渲染，对于没有计算和重度渲染需求（例如大型游戏）的用户来讲是可以尝试的选择[^nouveau-performance]。但是很遗憾，Nouveau 不支持运行包括 CUDA 在内的计算任务[^nouveau-matrix]。

     很长一段时间内，特别是对桌面用户来说，NVIDIA 的驱动安装一直是一个头疼（甚至让人想[骂人](https://www.youtube.com/watch?v=UeU1WUb1q10)）的问题。尽管 NVIDIA 提供了闭源驱动，但是恰当地安装与配置也不是很容易的事情。不过近年来，NVIDIA 推出的新显卡上添加了 GSP 芯片，能够承载 NVIDIA 不愿意公开的功能实现，因此 NVIDIA 也提供了自己的[「开源驱动」](https://github.com/NVIDIA/open-gpu-kernel-modules)。尽管这个驱动实现有可能永远都不会出现在 Linux 内核的主线代码里，但是可以期望其至少能够减少不少麻烦，并且为 NVIDIA GPU 运行在诸如 RISC-V 等新架构的机器上提供支持。当然，NVIDIA 的用户态驱动仍然是不开源的。

     [^nouveau-performance]: 根据 2024 年 1 月[该视频](https://www.youtube.com/watch?v=E-1vukqRKf4)的数据，对于视频中的 benchmark，基于 Nouveau + NVK + Zink 的性能评分达到了 NVIDIA 官方驱动的 66% 左右。

     [^nouveau-matrix]: <https://nouveau.freedesktop.org/FeatureMatrix.html> 中 "Compute" 一行均为 WIP（Work In Progress）状态，即尚未支持。

总的来说，在 Linux 下，NVIDIA 驱动与 CUDA 的安装方式大致分为：

1. 使用操作系统本身的仓库和包管理系统进行安装（推荐），例如：

     - [Debian Wiki](https://wiki.debian.org/NvidiaGraphicsDrivers)
     - [Ubuntu Server Guide](https://ubuntu.com/server/docs/nvidia-drivers-installation)
     - [Arch Wiki](https://wiki.archlinux.org/title/NVIDIA)

     对于部分不被 NVIDIA 官方支持的发行版（例如 Arch Linux），使用发行版自行打包的版本是唯一推荐的方法。

2. 使用 [NVIDIA 提供的软件源](https://developer.nvidia.com/CUDA-downloads)，并用包管理系统进行安装。

3. 使用官方 runfile 一键安装（不推荐使用此方法安装驱动）

     - 使用官方 runfile 一键安装的方式较为方便，但是在安装过程中会覆盖系统中的某些文件，**可能会破坏系统**。另外 runfile 安装管理麻烦，不能像包管理器在安装软件时会自动处理依赖关系，需要用户手动处理依赖问题。

对于后两种方式，可以在官网下载页面 <https://developer.nvidia.com/CUDA-downloads> 选择合适的操作系统，网页将给出对应操作系统的安装指令。其中 "Install Type" 中 local 代表安装包包含了完整的 CUDA 运行时和相关驱动，包管理器在需要时从本地获取；而 network 单纯只包含了源配置，由包管理器在需要时联网获取。"runfile (local)" 则是上面所说的第三种不推荐的安装方式。另外，旧的 CUDA 版本需要在 [CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive) 中查找。

在安装时，可能会需要选择 NVIDIA 驱动的版本。如果没有特殊需求，选择最新的版本即可，因为旧的驱动可能不支持新版本的 CUDA 与显卡。

!!! tip "Linux 头文件，与 DKMS"

     NVIDIA 驱动尽管是闭源的，但是其仍然包含一部分开源的代码，用于在内核和闭源驱动之间交互（这一部分代码也被戏称为 "GPL condom"）。由于不同版本的内核的 ABI 不兼容，因此更换内核后就需要重新编译驱动。DKMS（Dynamic Kernel Module Support）会帮助在内核更新后自动重新编译驱动，不过编译驱动还需要内核头文件，否则 DKMS 会跳过编译。

     对 Ubuntu 来说，默认安装的内核为 "generic"，对应的内核包为 `linux-image-generic`，头文件则为 `linux-headers-generic`。如果你使用的是其他内核（例如在虚拟化环境中，可能会使用 `linux-image-virtual`），则需要安装对应的头文件包。而默认的 Debian 则分别是 `linux-image-amd64` 和 `linux-headers-amd64`。某些时候头文件不会被自动安装，因此需要注意。

对于第一种安装方式，Ubuntu 和 Debian 都提供了 NVIDIA 驱动的元包（metapackage），包含了所有需要的内容。

Ubuntu 用户可以使用 `apt list` 查找当前仓库中提供的驱动版本：

```console
$ apt list 'nvidia-driver-*'
Listing... Done
nvidia-driver-460-server/noble 470.239.06-0ubuntu2 amd64
nvidia-driver-460/noble 470.239.06-0ubuntu2 amd64
nvidia-driver-465/noble 470.239.06-0ubuntu2 amd64
nvidia-driver-470-server/noble 470.239.06-0ubuntu2 amd64
nvidia-driver-470/noble 470.239.06-0ubuntu2 amd64
nvidia-driver-510/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-515-open/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-515-server/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-515/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-520-open/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-520/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-525-open/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-525-server/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-525/noble 525.147.05-0ubuntu2 amd64
nvidia-driver-530-open/noble 535.171.04-0ubuntu2 amd64
nvidia-driver-530/noble 535.171.04-0ubuntu2 amd64
nvidia-driver-535-open/noble 535.171.04-0ubuntu2 amd64
nvidia-driver-535-server-open/noble 535.161.08-0ubuntu2 amd64
nvidia-driver-535-server/noble 535.161.08-0ubuntu2 amd64
nvidia-driver-535/noble 535.171.04-0ubuntu2 amd64
nvidia-driver-550-open/noble 550.67-0ubuntu3 amd64
nvidia-driver-550-server-open/noble 550.54.15-0ubuntu2 amd64
nvidia-driver-550-server/noble 550.54.15-0ubuntu2 amd64
nvidia-driver-550/noble 550.67-0ubuntu3 amd64
```

Debian 则只包含了 `nvidia-driver` 包，对应发行版发布时最新的驱动版本，同时对于 stable 发行版，还可以从 backports 仓库中获取更新的驱动版本，详情请参考上文提供的 Debian Wiki。

### 查看显卡状态

```shell
nvidia-smi
```

这个命令可以列举并查看显卡的资源使用率，温度，功率等信息。

如果能够查看到你的显卡，那么恭喜你，显卡已经可以使用了。

!!! tip

    `nvidia-smi` 界面右上角显示的 CUDA 版本是指当前系统上安装的 NVIDIA 驱动支持的最高 CUDA 版本，并不是已安装的 CUDA 版本——比显示版本低的 CUDA 也是能够正常使用的。

### 安装 CUDA

可以从包管理器安装 CUDA。如果使用第一种方式，那么在 Ubuntu 与 Debian 中则对应 `nvidia-cuda-dev nvidia-cuda-toolkit nvidia-visual-profiler` 这几个包，不过发行版一般不会提供多个版本的 CUDA。当前使用的 NVIDIA 源中也可能没有需要的版本（可以检查名字以 `cuda` 开头的包），此时一种解决方式是安装旧版本 CUDA 对应的软件源包后，使用软件包管理器安装；或者使用 runfile，并在运行时添加选项只安装 toolkit。

<!-- 问题：Anaconda 是如何解决 CUDA 依赖的？ -->

### 环境变量设置

如果你想要方便地在 Shell 中使用 CUDA 指令，需要将可执行文件目录加到 `PATH` 环境变量中，以便执行 nvcc 等程序。假设 CUDA 安装在 `/usr/local/cuda` 目录下：

```shell
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
```

如果编译项目时找不到 CUDA 库，则需要更新动态链接库路径，对应需要设置 `LD_LIBRARY_PATH` 环境变量：

```shell
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
```
