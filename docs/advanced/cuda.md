# CUDA 环境简介

!!! warning "本文初稿（也许）已完成，但可能仍需大幅度修改"

CUDA（Compute Unified Device Architecture）是由 NVIDIA 公司推出的开发套件，它允许软件开发人员使用 NVIDIA 的 GPU（图形处理单元）进行通用计算，利用 GPU 强大的并行处理能力来加速计算密集型任务，常用于科学计算、工程模拟、机器学习等领域。

包含的组件包括：

- CUDA 驱动和运行时：这是连接你的软件和 GPU 硬件的基础层，它允许你的程序在 GPU 上执行。

- CUDA 编译器（nvcc）：这是一个将 CUDA 代码转换成 GPU 可以理解的形式的编译器。

- CUDA 库：这些库包括一系列预制的、高效的函数，比如线性代数运算（cuBLAS）、傅里叶变换（cuFFT）等。

- CUDA 工具：比如性能分析器（NVIDIA Nsight 和 Visual Profiler）和调试工具，它们帮助开发者优化和调试 CUDA 应用程序。

## 配置 CUDA 环境

### 硬件准备

在开始之前，你需要确认显卡是否支持支持 CUDA。在这里可以查看支持的列表：<https://developer.nvidia.com/CUDA-gpus>

表中的`Compute Capability`代表计算能力，同时也表明了 GPU 支持的 CUDA 特性和指令集版本。

### 安装 CUDA

虽然在不同的操作系统下，CUDA 的多种不同的安装方式，但总的来说，在 Linux 下，CUDA 的安装方式大致分为：

1. 使用操作系统本身的仓库和包管理系统进行安装（推荐）

     - 部分 linux 发行版不支持使用这种方式安装 cuda

2. 从官网下载安装包，并用包管理系统进行安装

3. 使用官方 runfile 一键安装

     - 使用官方 runfile 一键安装的方式较为方便，但是在安装过程中会覆盖系统中的某些文件，**可能会破坏系统**。另外 runfile 安装管理麻烦，不能像包管理器在安装软件时会自动处理依赖关系，需要用户手动处理依赖问题。

对于后两种方式，可以在官网下载页面<https://developer.nvidia.com/CUDA-downloads>选择合适的操作系统，网页将给出对应操作系统的安装指令。

对于第一种安装方式，这里以常用的 Ubuntu 为例：

#### 安装预编译的内核模块

```shell
sudo apt install linux-modules-nvidia-${DRIVER_BRANCH}${SERVER}-${LINUX_FLAVOUR}
```

`${DRIVER_BRANCH}`是 Nvidia 驱动的版本号，例如`525`,`535`等

`${SERVER}`可以是`-server`或为空，代表是否选择为服务器优化的版本。

`${LINUX_FLAVOUR}`可以是`generic`，`lowlatency`等。通常情况下，选择前者，除非希望系统尽可能的实时，同时又不希望降低太多的性能。

例如：

```shell
sudo apt install linux-modules-nvidia-525-generic
```

#### 安装用户空间的驱动和库

```shell
sudo apt install nvidia-driver-${DRIVER_BRANCH}${SERVER}
```

参数意义同上

例如：

```shell
sudo apt install nvidia-driver-525
```

### 查看显卡状态

```shell
nvidia-smi
```

这个命令可以列举并查看显卡的资源使用率，温度，功率等信息。

如果能够查看到你的显卡，那么恭喜你，显卡已经可以使用了。

!!! tip

    `nvidia-smi`界面右上角显示的 CUDA 版本是指当前系统上安装的 NVIDIA 驱动支持的最高 CUDA 版本，并不是已安装的 CUDA 版本

### 添加环境变量（可选）

如果你想要方便地在 Shell 中使用 CUDA 指令，需要将可执行文件目录加到`PATH`环境变量中

在`~/.bashrc`等文件中添加这一行

```shell
export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}
```

以便执行 nvcc 等程序。

如果编译项目时找不到 CUDA 库，则需要更新动态链接库路径。

在`~/.bashrc`等文件中添加这一行

```shell
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
```
