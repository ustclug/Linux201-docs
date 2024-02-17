# CUDA 环境简介

!!! warning "本文仍在编辑中"

CUDA（Compute Unified Device Architecture）是由 NVIDIA 公司推出的开发套件，它允许软件开发人员使用 NVIDIA 的 GPU（图形处理单元）进行通用计算。

包含的组件有：

- CUDA Runtime API：CUDA 编程的高级 API，为开发者提供了管理 GPU 设备、内存分配、数据传输和执行计算任务等功能的接口。

- CUDA Driver API：CUDA 的低级 API，提供了更细粒度的控制，允许开发者直接与 CUDA 驱动程序交互。对于需要更精细管理资源和执行模型的高级用户来说，这是一个有用的工具。

- CUDA Toolkit：一系列编译工具、库和技术文档。包括 `nvcc`（NVIDIA 的 CUDA 编译器）、CUDA 库、CUDA 调试器、性能分析工具（如 `nvprof`）以及其他开发工具。

- CUDA Libraries：一组为加速不同类型的计算任务而优化的库

    - cuBLAS：基本线性代数子程序（`BLAS`）的 GPU 加速版本。

    - cuFFT：在 GPU 上进行快速傅里叶变换的库。

    - cuRAND：在 GPU 上生成随机数的库。

    - cuDNN：用于深度神经网络的 GPU 加速的原语和函数库。

    - NCCL：多 GPU 和多节点上的集合通信的库。

    - Thrust：类似于 C++ 标准模板库（`STL`）的并行算法库。

- CUDA Samples：示例代码，涵盖了基本的`Hello World`程序到更复杂的应用程序。

- NVIDIA Nsight Tools：集成开发环境和调试工具，用于帮助开发者优化 CUDA 应用程序的性能和可靠性。包括 `Nsight Eclipse Edition`、`Nsight Visual Studio Edition`、`Nsight Compute` 和 `Nsight Systems`。

- CUDA Documentation：包括 API 参考、编程指南、最佳实践指南和其他技术资源等

## 配置 CUDA 环境

### 硬件准备

在开始之前，你需要确认显卡是否支持支持 CUDA。在这里可以查看支持的列表：<https://developer.nvidia.com/CUDA-gpus>

表中的`Compute Capability`代表计算能力，同时也表明了 GPU 支持的 CUDA 特性和指令集版本。

### 安装 CUDA

虽然在不同的操作系统下，CUDA 的多种不同的安装方式，但总的来说，在 Linux 下，CUDA 的安装方式大致分为：

- 使用官方 runfile 一键安装

- 从官网下载本地仓库的安装包，并用包管理系统进行安装

- 直接使用操作系统本身的仓库和包管理系统进行安装

对于前两种方式，可以在官网下载页面<https://developer.nvidia.com/CUDA-downloads>选择合适的操作系统，网页将给出对应操作系统的安装指令。

如果你的主机处于内网环境，例如某些企业中，或和 Nvidia 服务器的连接较慢，可以直接使用操作系统自带的软件仓库进行安装。这里以常用的 Ubuntu 为例：

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

## CUDA 编程模型
