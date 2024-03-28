# 容器

!!! warning "本文初稿编写中"

容器是近十几年来兴起的一种轻量级的虚拟化技术，在 Linux 内核支持的基础上实现了共享内核的虚拟化，让应用的部署与管理变得更加简单。

本部分假设读者了解基本的 Docker 使用。

## 容器技术的内核支持 {#kernel-support}

### 命名空间 {#namespace}

Linux 内核的命名空间功能是容器技术的重要基础。命名空间可以控制进程所能看到的系统资源，包括其他进程、网络、文件系统、用户等。可以阅读 [namespaces(7)][namespaces.7] 了解相关的信息。

可以在 procfs 看到某个进程所处的命名空间：

```console
$ ls -lh /proc/self/ns/
total 0
lrwxrwxrwx 1 username username 0 Mar 24 21:04 cgroup -> 'cgroup:[4026531835]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 ipc -> 'ipc:[4026531839]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 mnt -> 'mnt:[4026531841]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 net -> 'net:[4026531840]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 pid -> 'pid:[4026531836]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 pid_for_children -> 'pid:[4026531836]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 time -> 'time:[4026531834]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 time_for_children -> 'time:[4026531834]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 user -> 'user:[4026531837]'
lrwxrwxrwx 1 username username 0 Mar 24 21:04 uts -> 'uts:[4026531838]'
```

使用 `nsenter` 命令可以进入某个命名空间：

```console
$ sudo docker run -it --rm --name test ustclug/ubuntu:22.04
root@9213a075a2f4:/#
...
$ # 开启另一个终端
$ sudo docker top test
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                117426              117406              0                   21:09               pts/0               00:00:00            bash
$ sudo nsenter --target 117426 --uts bash # 进入 UTS 命名空间
[root@9213a075a2f4 example]# # 可以看到 hostname 已经改变
```

那么 PID 命名空间也是同理吗？

```console
$ sudo nsenter --target 117426 --pid bash
# ps aux
fatal library error, lookup self
# echo $$
417
# ls -lh /proc/$$/
ls: cannot access '/proc/417/': No such file or directory
# # 如果使用 htop，仍然可以看到完整的进程列表
```

这是因为这里挂载的 procfs 是对应整个系统的，因此即使进入了新的 PID 命名空间，
在 mount 命名空间不变的情况下，`/proc` 目录下的内容仍然是宿主机的。
因此需要同时进入 mount 命名空间：

```console
$ sudo nsenter --target 117426 --pid --mount bash
# ps aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0   4624  3712 pts/0    Ss+  13:09   0:00 bash
root         434  0.0  0.0   4624  3712 ?        S    13:32   0:00 bash
root         437  0.0  0.0   7060  2944 ?        R+   13:32   0:00 ps aux
```

因此一般来讲，我们会希望同时进入进程所属所有的命名空间，以避免可能的不一致性问题。可以通过 `-a` 参数实现。

另一个与命名空间有关的实用命令是 `unshare`，取自同名的系统调用，可以创建新的命名空间。对于上面展示 PID 命名空间的例子，可以使用 `unshare` 命令创建一个新的 PID 命名空间（与 mount 命名空间），并且挂载新的 `/proc`：

```console
$ sudo unshare --pid --fork --mount-proc bash
# ps aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0  10876  4568 pts/17   S    21:42   0:00 bash
root           2  0.0  0.0  14020  4464 pts/17   R+   21:42   0:00 ps aux
```

另外，有一种**用户命名空间**，允许非 root 用户创建新的用户命名空间（这也是 rootless 容器的基础），让我们简单试一试：

```console
$ unshare --user --pid --fork --mount-proc bash
$ ps aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
nobody         1  0.0  0.0  10876  4312 pts/16   S    21:44   0:00 bash
nobody         2  0.0  0.0  14020  4276 pts/16   R+   21:44   0:00 ps aux
$ exit
$ # 甚至可以修改映射，实现「假的」root
$ unshare --user --pid --fork --map-root-user --mount-proc bash
# ps aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0  10876  4468 pts/16   S    21:46   0:00 bash
root           2  0.0  0.0  14020  4416 pts/16   R+   21:46   0:00 ps aux
```

!!! note "命名空间的魔法"

    在了解命名空间的基础上，我们可以绕过容器运行时的一些限制，直接操作命名空间。
    
    作为其中一个「花式操作」的例子，可以阅读这篇 USENIX ATC 2018 的论文：[Cntr: Lightweight OS Containers](https://www.usenix.org/conference/atc18/presentation/thalheim)（以及目前仍然在维护的[代码仓库](https://github.com/Mic92/cntr)）。这篇工作实现了在不包含调试工具的容器中使用包含调试工具的镜像（或者 host 的调试工具）进行调试的功能。

### Cgroups

Cgroups（[cgroups(7)][cgroups.7]）是 Linux 内核提供的限制与统计进程资源使用的机制。
Cgroups 以文件系统的形式暴露给用户态，一般挂载在 `/sys/fs/cgroup/`。
相比于传统的 `setrlimit` 等系统调用，cgroups 能够有效地管理一组进程（以及它们新建的子进程）的资源使用。

在使用 systemd 的系统中，cgroups 由 systemd 负责管理。
仔细观察 `systemctl status` 的输出，可以发现其就展示了一颗 cgroup 树（注意看 `init.scope` 上一行）：

```console
$ systemctl status
● example
    State: running
    Units: 271 loaded (incl. loaded aliases)
     Jobs: 0 queued
   Failed: 0 units
    Since: Sun 2023-06-11 15:42:13 CST; 9 months 14 days ago
  systemd: 252.19-1~deb12u1
   CGroup: /
           ├─init.scope
           │ └─1 /lib/systemd/systemd --system --deserialize=34
           ├─system.slice
           │ ├─caddy.service
           │ │ └─2398446 /usr/bin/caddy run --environ --config /etc/caddy/Caddyfile
           │ ├─containerd.service
           │ │ └─3923123 /usr/bin/containerd
           │ ├─cron.service
           │ │ └─649 /usr/sbin/cron -f
           │ ├─dbus.service
           │ │ └─650 /usr/bin/dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
           │ ├─docker.service
           │ │ └─3926029 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
（省略）
```

也可以使用 `systemd-cgtop` 实时查看 cgroup 的使用情况。

Cgroups 有 v1 与 v2 两个版本。
较新的发行版默认仅支持 cgroups v2，稍老一些的会使用 systemd 的 "unified_cgroup_hierarchy" 特性，将 cgroups v1 与 v2 合并暴露给用户。目前大部分软件都已经支持 cgroups v2，因此下文讨论 cgroups 时，默认为 v2。

可以手工通过读写文件控制 cgroups：

```console
$ sleep 1d &
[1] 1910225
$ sudo -i
# cd /sys/fs/cgroup
# mkdir test
# cd test
# echo 1910225 > cgroup.procs
# cat cgroup.procs
1910225
```

这样，我们就将刚刚创建的 `sleep 1d` 的进程**移动**到了 `test` cgroup 中。
（注意 cgroup 树包含了系统的所有进程，因此写入到 `cgroup.procs` 的实际语义是移动进程所属的 cgroup）。

由于 `test` 创建在根下面，因此其包含了所有的「控制器」（Controller）。
不同的控制器对应不同的系统资源，例如内存、CPU、IO 等。
可以通过 `ls` 确认：

```console
# ls
cgroup.controllers	cpu.max.burst			 cpu.weight.nice	   hugetlb.2MB.rsvd.max  memory.low	      memory.zswap.current
cgroup.events		cpu.pressure			 hugetlb.1GB.current	   io.bfq.weight	 memory.max	      memory.zswap.max
cgroup.freeze		cpuset.cpus			 hugetlb.1GB.events	   io.latency		 memory.min	      misc.current
cgroup.kill		cpuset.cpus.effective		 hugetlb.1GB.events.local  io.low		 memory.numa_stat     misc.events
cgroup.max.depth	cpuset.cpus.exclusive		 hugetlb.1GB.max	   io.max		 memory.oom.group     misc.max
cgroup.max.descendants	cpuset.cpus.exclusive.effective  hugetlb.1GB.numa_stat	   io.pressure		 memory.peak	      pids.current
cgroup.pressure		cpuset.cpus.partition		 hugetlb.1GB.rsvd.current  io.prio.class	 memory.pressure      pids.events
cgroup.procs		cpuset.mems			 hugetlb.1GB.rsvd.max	   io.stat		 memory.reclaim       pids.max
cgroup.stat		cpuset.mems.effective		 hugetlb.2MB.current	   io.weight		 memory.stat	      pids.peak
cgroup.subtree_control	cpu.stat			 hugetlb.2MB.events	   irq.pressure		 memory.swap.current  rdma.current
cgroup.threads		cpu.stat.local			 hugetlb.2MB.events.local  memory.current	 memory.swap.events   rdma.max
cgroup.type		cpu.uclamp.max			 hugetlb.2MB.max	   memory.events	 memory.swap.high
cpu.idle		cpu.uclamp.min			 hugetlb.2MB.numa_stat	   memory.events.local	 memory.swap.max
cpu.max			cpu.weight			 hugetlb.2MB.rsvd.current  memory.high		 memory.swap.peak
```

控制器可以通过 `cgroup.subtree_control` 控制是否启用。
需要注意的是，根据 cgroup v2 的 "no internal processes" 规则，
除根节点以外，其他的 cgroup 不能同时本身既包含进程，又设置了 `subtree_control`。

!!! lab "尝试操作 `subtree_control`"

    请根据 cgroups 手册以及上文的说明，在 `test` cgroup 下创建一个新的 cgroup，并且使其仅包含内存控制器。
    想一想：上面的 `sleep` 进程应该怎么操作？

实验完成后，杀掉 `sleep` 进程，并且使用 `rmdir` 删除 `test` cgroup：

```console
# cd /sys/fs/cgroup
# kill 1910225
# rmdir /sys/fs/cgroup/test
```

!!! question "为什么不使用 `rm -r`"

    思考这个问题：
    `/sys/fs/cgroup/test` 并非我们传统意义上的「空目录」，为什么这里要用 `rmdir`，而不是用 `rm -r` 递归删除？

Cgroups 有命令行工具可以帮助管理，安装 `cgroup-tools` 后，可以使用 `cgcreate`、`cgexec` 等命令：

```console
$ sudo cgcreate -g memory:test  # 创建一个名为 test 的 cgroup
$ sudo cgset -r memory.max=16777216 test  # 限制使用 16 MiB 内存
$ sudo cgexec -g memory:test python3  # 在 test 下运行 python3
Python 3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> a = [0] * 4000000  # 尝试占用至少 32 MB 内存
Killed
$ sudo cgdelete memory:test  # 清理现场
```

!!! lab "观察这些命令的行为"

    请使用系统调用分析工具 `strace` 观察 `cgcreate`、`cgset`、`cgexec`、`cgdelete` 的文件系统操作。

具体的控制器使用方法这里不再赘述。

### Seccomp

Seccomp 是 Linux 内核提供的限制进程系统调用的机制。
如果没有 seccomp，即使使用上面提到的命名空间、cgroups，容器内的进程仍然可以执行任意的系统调用：
root 权限的进程可以随意进行诸如关机、操作内核模块等危险操作，这通常是非预期的；
即使通过用户机制限制了权限，暴露所有的系统调用仍然大幅度增加了攻击面。

从程序员的角度，可以使用 libseccomp 库简化 seccomp 的使用。

!!! lab "执行 Python 3 解释器最少需要多少系统调用？"

    使用 libseccomp 编写程序，设置系统调用白名单限制。
    尝试找出最小的系统调用集合，并且了解其中的每个系统调用的作用。

### Overlay 文件系统 {#overlayfs}

[Overlay 文件系统](https://docs.kernel.org/filesystems/overlayfs.html)（OverlayFS）不是容器所必需的——比如说，一些容器运行时支持像 chroot 一样，直接从一个 rootfs 目录启动容器（例如 systemd-nspawn）。
但是对于 Docker 这样的容器运行时，其 image 的分层结构使得 OverlayFS 成为了一个非常重要的技术。
尽管对于 Docker 来说，其也支持其他的写时复制的存储驱动，例如 Btrfs 和 ZFS，但是 OverlayFS 仍然是最常见的选择——因为它不需要特殊的文件系统支持。

挂载 OverlayFS 需要三个目录：

- lowerdir: 只读的底层目录（支持多个）
- upperdir: 可读写的上层目录
- workdir: 需要为与上层目录处于同一文件系统的目录，用于处理文件系统的原子操作

最终合成的文件系统会将 lowerdir 与 upperdir 合并，对于相同的文件，upperdir 优先。
让我们试一试：

```console
$ mkdir lower upper work merged
$ echo "lower" > lower/lower
$ echo "upper" > upper/upper
$ mkdir lower/dir upper/dir
$ echo "lower1" > lower/dir/file1
$ echo "upper1" > upper/dir/file1
$ echo "lower2" > lower/dir/file2
$ echo "upper2" > upper/dir/file2
$ echo "lower4" > lower/dir/file4
$ echo "upper3" > upper/dir/file3
$ sudo mount -t overlay overlay -o lowerdir=lower,upperdir=upper,workdir=work merged
$ tree merged
merged/
├── dir
│   ├── file1
│   ├── file2
│   ├── file3
│   └── file4
├── lower
└── upper

2 directories, 6 files
```

可以看到 merged 目录下的文件是合并后的结果，同时存在 lower 和 upper 目录的文件。

```console
$ cat merged/lower
lower
$ cat merged/dir/file1
upper1
$ cat merged/dir/file2
upper2
$ cat merged/dir/file3
upper3
$ cat merged/dir/file4
lower4
```

上面只有 upper 不存在的 dir/file4 是 lower 的内容，因此可以印证 upper 优先。

```console
$ echo "merged" > merged/merged
$ echo "modified-lower" > merged/lower
$ cat upper/merged
merged
$ cat upper/lower
modified-lower
$ cat lower/merged
cat: lower/merged: No such file or directory
$ cat lower/lower
lower
```

可以显然发现写入操作会被应用到 upperdir 中。

传统上，OverlayFS 最常见的用途是在 LiveCD/LiveUSB 上使用：在只读的底层文件系统上，挂载一个可写的上层文件系统，用于保存用户的数据。
而在容器（特别是 Docker）上，由于容器镜像的分层设计，OverlayFS 就成为了一个非常好的选择。
假设某个容器镜像有三层，每一层都做了一些修改。由于 OverlayFS 支持多个 lowerdir，
所以最后合成出来的 image 就是第一层基底 + 第二层的变化作为 lowerdir，第三层作为 upperdir，
这也可以从 `docker image inspect` 的结果印证：

```console
$ sudo docker image inspect 201test
（省略）
        "GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/9d15ee29579c96414c51ea2e693d2fe764da2e704a005e2d398025bf8c2b85b6/diff:/var/lib/docker/overlay2/38eb305239012877d40fc4f06620d0293d7632f188b986a0ff7f30a57b6feb32/diff",
                "MergedDir": "/var/lib/docker/overlay2/a66d2956c278d83a86454659dba3b2f75b99b41ddb39c5227b02afde898efe55/merged",
                "UpperDir": "/var/lib/docker/overlay2/a66d2956c278d83a86454659dba3b2f75b99b41ddb39c5227b02afde898efe55/diff",
                "WorkDir": "/var/lib/docker/overlay2/a66d2956c278d83a86454659dba3b2f75b99b41ddb39c5227b02afde898efe55/work"
            },
            "Name": "overlay2"
        },
（省略）
```

（当然，这里容器镜像不会，也没有必要挂载，因此如果尝试访问 merged 目录，会发现不存在）

使用容器镜像启动的容器则将镜像作为 lowerdir，在容器里面的写入操作则会被保存在 upperdir 中。

```console
$ sudo docker run -it --rm --name test 201test
root@1522be2f7d29:/# echo 'test' > /test
root@1522be2f7d29:/# # 切换到另一个终端
$ sudo docker inspect test
（省略）
"GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/34e8198226f478c89021fd9a00a31570cdda57d4fcea66a0bb8506cf7b81dff5-init/diff:/var/lib/docker/overlay2/a66d2956c278d83a86454659dba3b2f75b99b41ddb39c5227b02afde898efe55/diff:/var/lib/docker/overlay2/9d15ee29579c96414c51ea2e693d2fe764da2e704a005e2d398025bf8c2b85b6/diff:/var/lib/docker/overlay2/38eb305239012877d40fc4f06620d0293d7632f188b986a0ff7f30a57b6feb32/diff",
                "MergedDir": "/var/lib/docker/overlay2/34e8198226f478c89021fd9a00a31570cdda57d4fcea66a0bb8506cf7b81dff5/merged",
                "UpperDir": "/var/lib/docker/overlay2/34e8198226f478c89021fd9a00a31570cdda57d4fcea66a0bb8506cf7b81dff5/diff",
                "WorkDir": "/var/lib/docker/overlay2/34e8198226f478c89021fd9a00a31570cdda57d4fcea66a0bb8506cf7b81dff5/work"
            },
            "Name": "overlay2"
        },
（省略）
$ sudo ls /var/lib/docker/overlay2/34e8198226f478c89021fd9a00a31570cdda57d4fcea66a0bb8506cf7b81dff5/diff/
test
```
