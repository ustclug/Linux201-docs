# ZFS

ZFS（Zettabyte File System）虽然名叫 "FS"，但是集成了一系列存储管理功能，包括文件系统、卷管理、快照、数据完整性检查和修复等，常被称作“单机最强存储方案”。

虽然 ZFS 没有特殊的系统要求，但是我们推荐在具有较好配置的服务器上使用 ZFS，以获得更好的性能和稳定性。

- 固态硬盘，或者多块规格相同的大容量机械硬盘（推荐 4 块或更多），尽量避免用单块机械硬盘。
- 如果预期需要承载较重的读写负载，推荐使用大容量内存用于缓存（ZFS 官方推荐每 1 TB 存储容量配置 1 GB 内存）。
    - 如果打算启用 ZFS 的去重（deduplication）功能，推荐为每 TB 存储容量配备至少 5 GB 内存（但是官方推荐的比例是 30 GB）。
- 如果预期的热数据量超出了内存容量，推荐使用 SSD 作为 L2ARC 缓存，但用于缓存的 SSD 容量不宜超过内存的 10 倍。
- 多核心 CPU，以便处理 ZFS 的数据完整性检查和透明压缩等任务。

如果只是为了将 ZFS 的高级功能用于个人存储，如 NAS 等，那么你大可忽略以上所有推荐，在 Intel J3455 和 4 GB 内存的小主机上就可以轻松运行 ZFS，例如 QNAP 的个人 NAS 设备就已经默认采用 ZFS 了。

## 内核模块 {#kernel-module}

尽管 OpenZFS 也是一个开源项目，但是由于开源协议不兼容（OpenZFS 采用 CDDL，Linux 内核采用 GPL），因此 OpenZFS 无法直接集成到 Linux 内核中。

- Debian 将 ZFS 的代码以 DKMS 模块的形式打包（包名 `zfs-dkms`），以便在更新内核之后自动编译和安装。

    !!! note "Debian backports"

        受限于 Debian 的稳定性政策，stable 的软件源中的 ZFS 版本可能较老。如果需要使用较新的 ZFS 版本，可以考虑使用 Debian 的 backports 仓库（`apt install -t bookworm-backports zfs-dkms`）。

- Ubuntu 自 20.04 LTS 起提供预编译好的 `zfs.ko`（软件包 `linux-modules-$(uname -r)`），因此无需再安装 `zfs-dkms`。Ubuntu 18.04 LTS 及之前的版本仍然需要安装 `zfs-dkms`。

不论是 Debian 还是 Ubuntu，都需要安装 `zfsutils-linux` 软件包，以便使用 ZFS 的命令行工具。

## Pool
