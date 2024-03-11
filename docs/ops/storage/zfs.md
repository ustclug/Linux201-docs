# ZFS

ZFS（Zettabyte File System）虽然名叫“FS”，但是集成了一系列存储管理功能，包括文件系统、卷管理、快照、数据完整性检查和修复等，常被称作“单机最强存储方案”。

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

## 基础概念

与 LVM 和其他卷管理工具类似，ZFS 也将存储设备组织成多级结构：

- vdev（Virtual Device）是 ZFS 对“硬盘组”的抽象。一个 vdev 可以是单块硬盘、mirror（类似 RAID 1 硬盘组）或 RAID-Z、RAID-Z2、RAID-Z3（类似 RAID 5、6、7 硬盘组）等。
- pool 是 ZFS 的存储池，由一个或多个 vdev 组成，类似 LVM 的 VG（Volume Group）概念。
- ZFS 的文件系统和 Zvol（ZFS Volume）都是在 pool 上创建的，类似 LVM 的 LV（Logical Volume）概念。

    与 LVM 略有区别的地方是，ZFS 的文件系统是直接创建在 pool 上的，而无需像 LVM 一样先创建 LV，再将其格式化为某种文件系统。ZFS 的文件系统就是 ZFS。

## 创建 pool

同样与 LVM 不同的是，ZFS 推荐使用整块硬盘或尽可能整块的硬盘来创建 pool，以保证稳定的性能。作为一项适配操作，如果将整块硬盘用于创建 zpool，ZFS 会自动对其进行分区，以便在硬盘故障时能够更好地识别和处理。

以下假设 disk\[1-3\].img 是三块大小相同的硬盘。

```console
$ truncate -s 1G disk1.img disk2.img disk3.img
$ sudo losetup -f --show disk1.img
/dev/loop0
$ sudo losetup -f --show disk2.img
/dev/loop1
$ sudo losetup -f --show disk3.img
/dev/loop2
$ sudo zpool create tank /dev/loop0 /dev/loop1 /dev/loop2
$
```

!!! warning "关于 zpool"

    `ashift` 参数是 ZFS 对“磁盘扇区大小”的理解，且在创建 pool 后**无法更改**。
    为了确保最佳的性能，`ashift` 参数应当与硬盘的真实扇区大小相匹配，既不宜过大也不宜过小。
    默认情况下，在创建 zpool 的时候，ZFS 会自动检测硬盘的扇区大小（`ioctl(BLKPBSZGET)`）并设置合适的 `ashift` 参数。
    对于固态硬盘，建议查阅硬盘的规格，然后手动指定 `zpool create -o ashift=...`。

    在生产环境中，请**不要**将 ZFS 用于任何虚拟硬盘或软件/硬件 RAID 阵列上。
    只有当 ZFS 直接管理每块硬盘时，才能获得最佳的性能和 ZFS 提供的数据完整性保证。
    如果你的阵列卡不支持直通，可以考虑为每块盘建立一个单盘阵列。

在实际应用中，如果你使用 `sda`、`nvme0n1` 等设备名来创建 pool，ZFS 会自动对其进行分区，然后使用 `sda1`、`nvme0n1p1` 等分区名来创建 pool，并在每个盘的末尾创建一个 8 MB 的分区（`sda9`、`nvme0n1p9`）。分区的目的可能出于某些历史原因，目前无从考证，且这个编号为 9 的分区是没有任何用途的。

在创建好 pool 之后，可以使用 `zpool status` 和 `zpool list` 查看 pool 的状态和使用情况。

```console
$ zpool status
  pool: tank
 state: ONLINE
config:

        NAME        STATE     READ WRITE CKSUM
        tank        ONLINE       0     0     0
          loop0     ONLINE       0     0     0
          loop1     ONLINE       0     0     0
          loop2     ONLINE       0     0     0

errors: No known data errors
$ zpool list
NAME    SIZE  ALLOC   FREE  CKPOINT  EXPANDSZ   FRAG    CAP  DEDUP    HEALTH  ALTROOT
tank   2.81G   112K  2.81G        -         -     0%     0%  1.00x    ONLINE  -
```

!!! tip

    在 ZFS 中，绝大多数诸如查询状态等只读的命令都不需要 `sudo`。

在创建好 zpool `tank` 后，ZFS 也自动创建了一个文件系统 `tank` 并挂载在了 `/tank` 目录，可以直接使用。

!!! tip "参数调节"

    对于新建的 ZFS pool，我们推荐调整一些参数以获得最佳的性能。具体参见下面的[参数调节](#tuning)。

## 参数调节 {#tuning}

### Zpool {#tuning-zpool}

Zpool 层面的参数可以通过 `zpool set` 命令进行调整，以下是一些推荐修改的参数：

- `autotrim=on`：如果你使用硬盘是 SSD，启用此选项后 ZFS 会自动为已删除的数据块向硬盘发送 TRIM 指令。例如：

    ```shell
    zpool set autotrim=on tank
    ```

### ZFS 文件系统 {#tuning-zfs}

ZFS（文件系统）层面的参数可以通过 `zfs set` 命令进行调整，语法与 `zpool set` 类似。以下是一些推荐修改的参数：

- `xattr=sa`：将文件的扩展属性（如 POSIX ACL 和 SELinux 标签等）存储在 dnode 中（类似其他文件系统的 inode），而不是独立的“文件”中。对于经常使用扩展属性的应用场景（如 Samba），使用 `xattr=sa` 可以减少磁盘 I/O，提高性能。

    如果你的使用场景不需要扩展属性（如镜像站），可以使用 `xattr=off` 关闭扩展属性功能，进一步减少磁盘 I/O。

    该选项的默认值为 `xattr=on`，即扩展属性存储在额外的数据块中。这是为了保持与 FreeBSD / Solaris 等系统中的 ZFS 实现的兼容性。除非你预计需要将 ZFS pool 搬到这些系统上使用，否则我们推荐使用 `xattr=sa` 或 `xattr=off`。

- `compression=on` 或 `compression=zstd`：启用 ZFS 的透明压缩功能。对于大多数数据，压缩后的数据量会显著减小，从而减少磁盘 I/O。

    一般建议启用透明压缩功能，除非你的 CPU 性能较差（例如 10 年前的服务器）或者预期的数据量不会因压缩而减小（例如归档存储已经压缩过的数据）。

    !!! note "压缩算法"

        截至 2024 年，ZFS 默认使用 LZ4 算法进行压缩，这是一种速度较快的单线程算法。如果你的 CPU 不是上古级别的，可以考虑使用 Zstd，这是一种更加现代化的压缩算法，支持多线程和更高的压缩比。

### ZFS 内核模块参数 {#tuning-zfs-ko}

ZFS 的内核模块具有**非常**多的可调节参数，其中大部分参数可以通过读写 `/sys/module/zfs/parameters` 目录下的文件进行调节。ZFS 的内核模块参数从生效时间上可以分为三类：

- **仅加载时生效**：这类参数在加载模块时就已经确定，无法在运行时修改。如果需要使用非默认值的话，需要在加载模块的时候就指定。一般通过在 `/etc/modprobe.d` 中创建 `.conf` 文件来指定。
- **import 时生效**：这类参数可以在运行时通过读写 sysfs 进行调节，但新的值只有在下次导入 pool 时才会生效。如果需要对使用中的 pool 修改这些参数，需要先 `zpool export` 再 `zpool import`。
- **立即生效**：这类参数可以在运行时通过读写 sysfs 进行调节，且立即生效。

最常调节的 ZFS 模块参数其实只有一个，那就是 `zfs_arc_max`，即 ZFS 使用系统内存作为一级缓存的最大值。默认情况下，ZFS 会使用系统内存的一半作为 ARC，但是如果你的服务器是专用于存储和文件服务的，可以考虑将这个值调大一些。例如：

```shell
echo 4294967296 > /sys/module/zfs/parameters/zfs_arc_max
```

### 关于 ARC

ZFS ARC 的全称是 Adaptive Replacement Cache，是 ZFS 用于缓存磁盘数据的一级缓存。ZFS 的缓存算法非常智能，会将可用的缓存容量分为 MFU（Most Frequently Used）和 MRU（Most Recently Used）两部分，并根据负载情况自动调整两部分的大小。

在 Linux 下，受限于 kernel 的设计，ARC 占用的内存会在 htop / free 等程序中显示为 used 而不是 cached，但是其行为和 cached 是一致的，即在系统内存压力升高时会自动释放，以供其他程序使用。

!!! note ""

    在 FreeBSD 中，ZFS ARC 占用的内存会正确地显示为 cached。
