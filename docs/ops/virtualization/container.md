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

### OverlayFS

<!-- TODO: not fin -->
