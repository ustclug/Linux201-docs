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

!!! note "ustclug Docker image"

    本页的容器示例使用了 [ustclug/mirrorimage](https://github.com/ustclug/mirrorimage/) 生成的容器镜像，默认配置了科大镜像站，帮助减少 `apt` 等操作之前还要跑 `sed` 的麻烦。

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

!!! question "解释 Dockerfile 编写中的实践"

    从 OverlayFS 的角度，解释以下 Dockerfile 存在的问题：

    ```Dockerfile
    # 以上部分省略
    RUN wget -O /tmp/example.tar.gz https://example.com/example.tar.gz
    RUN tar -zxvf /tmp/example.tar.gz -C /tmp
    RUN make && make install
    RUN rm -rf /tmp/*
    ```

## Docker

### 基础概念复习 {#docker-basic}

Docker 是众多容器运行时中的一种（也是最流行的一种）。用户可以从 **registry** 获取 **image**，
获得的 image 可以直接创建 **container** 运行，也可以使用 Dockerfile 来定制 image。
除此之外，Docker 也提供了与存储（**volume**）、网络（**network**）等相关的功能。
Docker 的设计主要考虑了开发与部署的便利性。

Docker 采取 C-S 架构，server daemon（dockerd）暴露一个 UNIX socket（`/run/docker.sock`），
用户通过 `docker` 这个 CLI 工具，或者自行编写程序与其通信。
这个 daemon 的容器操作则是与 containerd 进行交互。

!!! info "Podman"

    对比 Docker 的 C-S 架构，红帽主推的 [Podman](https://podman.io/) 则不再依赖于 daemon 进行容器管理。

最简单的创建容器的方法是：

```console
sudo docker run -it --rm --name test ubuntu:22.04
```

!!! danger "加入 docker 用户组等价于提供 root 权限"

    在默认安装下，Docker socket 只有位于 docker 用户组的用户才能访问，对应的 server daemon 程序以 root 权限运行。
    将用户加入 docker 用户组即授权了对应的用户与 Docker 的 UNIX socket，或者说与 dockerd 服务端，任意通信的权限。
    用户可以通过创建特权容器、任意挂载宿主机目录等操作来实际做和 root 一模一样的事情。

    2023 年的 Hackergame 有一道相关的题目：[Docker for Everyone](https://github.com/USTC-Hackergame/hackergame2023-writeups/tree/master/official/Docker%20for%20Everyone)。

    基于相同的理由，如果需要跨机器操作 Docker，也**不**应该用 `-H tcp://` 的方式开启远程访问。
    请阅读 <https://docs.docker.com/engine/security/protect-access/> 了解安全配置远程访问 Docker 的方法。

    以下所有块代码示例中均会使用 `sudo`。

!!! warning "保持环境整洁：给容器起名，并且为临时使用的容器加上 `--rm`"

    一个非常常见的问题是，很多人启动容器的时候直接这么做：

    ```console
    sudo docker run -it ubuntu:22.04
    ```

    然后做了一些操作之后就直接退出了。这么做的后果，就是**在 `docker ps -a` 的时候，发现一大堆已经处于退出状态的容器**。

    加上 `--name` 参数命名，可以帮助之后判断容器的用途；加上 `--rm` 参数则会在容器退出后自动删除容器。

另外创建容器时非常常见的需求：

- `-e KEY=VALUE`/`--env KEY=VALUE`：设置环境变量
- `-v HOST_PATH:CONTAINER_PATH`：挂载宿主机目录
    - 相对路径需要自行加上 `$(pwd)`，像这样：`-v $(pwd)/data:/data`
- `-p HOST_PORT:CONTAINER_PORT`：映射端口
- `--restart=always`/`--restart=unless-stopped`：设置容器启动、重启策略（可以使用 `docker update` 修改）
- `--memory=512m --memory-swap=512m`：限制容器内存使用

!!! danger "映射端口的安全性"

    默认情况下，Docker 会自行维护 iptables 规则，并且这样的规则不受 ufw 等工具的管理。
    这会导致暴露的端口绕过了系统的防火墙。

    **如果不需要其他机器访问，使用 `-p 127.0.0.1:xxxx:xxxx`，而非 `-p xxxx:xxxx`**。
    作为一个真实的案例，某服务器这样启动了一个 MongoDB 数据库容器：

    ```console
    sudo docker run -p 27017:27017 -tid --name mongo mongo:3.6
    ```

    过了几个月，发现程序功能不正常，再一看才发现数据被加密勒索了——万幸的是里面没有重要的内容。

以及常见的容器管理命令：

- `docker ps`：查看容器
- `docker exec -it CONTAINER COMMAND`：在容器内执行命令
- `docker inspect CONTAINER`：查看容器详细信息

与查看、清理 Docker 磁盘占用等操作：

- `docker system df`：查看镜像、容器、volume 与构建缓存的磁盘占用
- `docker system prune --volumes --all`：清理不再使用的镜像、容器、volume、network 与全部构建缓存

### 导入与导出 {#docker-import-export}

Docker 支持导出容器与镜像，并以镜像的形式导入，格式均为 tar。可以通过管道的方式实现压缩：

```console
$ # 镜像导入/导出
$ sudo docker image save hello-world:latest | zstd -o hello-world.tar.zst
/*stdin*\            : 15.11%   (  26.0 KiB =>   3.93 KiB, hello-world.tar.zst)
$ sudo docker image rm hello-world:latest
$ zstd -d -c hello-world.tar.zst | sudo docker image load
e07ee1baac5f: Loading layer [==================================================>]  14.85kB/14.85kB
Loaded image: hello-world:latest
$ # 容器导出，并以镜像形式导入
$ sudo docker run -it --name test ustclug/debian:12 touch /test
$ sudo docker container export test | zstd -o test.tar.zst
/*stdin*\            : 33.93%   (   116 MiB =>   39.2 MiB, test.tar.zst)
$ sudo docker rm test
$ zstd -d -c test.tar.zst | sudo docker import - test
sha256:21a35d8f910941f4913ada5f3600c04234d13860fe498ac5cb301ba1801aa82c
$ sudo docker run -it --rm test ls /test
/test
```

其中镜像导出（save）后仍然有层级结构，但是容器导出（export）后则是一个完整的文件系统。

也有一些工具，例如 [dive](https://github.com/wagoodman/dive)，可以方便地查看镜像每一层的内容。

### 多阶段构建 {#docker-multi-stage}

在制作容器镜像的时候，一个常见的场景是：编译软件和实际运行的环境是不同的。
如果将两者写在不同的 Dockerfile 中，实际操作会很麻烦（需要先构建编译容器、运行容器、再构建运行环境容器）；
如果写在同一个 Dockerfile 里面，并且需要清理掉实际运行时不需要的文件，也会非常非常麻烦：

```dockerfile
# 那么可能只能这么写，否则编译环境仍然会残留在镜像中
RUN apt install -y some-dev-package another-dev-package ... && \
    wget https://example.com/some-source.tar.gz && \
    tar -zxvf some-source.tar.gz && \
    ./configure --some-option && make && make install && \
    rm -rf /some-source.tar.gz /some-source && \
    apt remove -y some-dev-package another-dev-package ... && \
```

Dockerfile 对多阶段（multi-stage）的支持很好地解决了这个问题，一个简单的例子如下：

```dockerfile
FROM alpine:3.15 AS builder
RUN apk add --no-cache build-base
WORKDIR /tmp
ADD example.c .
RUN gcc -o example example.c

FROM alpine:3.15
COPY --from=builder /tmp/example /usr/local/bin/example
```

可以发现，这个 Dockerfile 有多个 `FROM` 代表了多个阶段。
第一阶段的 `FROM` 后面加上了 `AS builder`，这样就可以在第二阶段使用 `COPY --from=builder` 从第一阶段拷贝文件。

### 运行图形应用 {#docker-gui}

<!-- TODO: 链接到高级内容中的显示与窗口系统部分 -->

在容器中运行图形程序也是相当常见的需求。
以下简单介绍在 Docker 中运行 X11 图形应用（即 X 客户端）的方法，假设主机环境已经配置好了 X 服务器。

!!! tip "X 客户端与服务器"

    X 服务器负责显示图形界面，而具体的图形界面程序，即 X 客户端，则需要连接到 X 服务器才能绘制出自己的窗口。

    如果你正在使用 Linux 作为桌面环境，那么要么整个桌面环境就由 X 服务器渲染，要么在 Wayland 下 Xwayland 会作为 X 服务器提供兼容。如果正在使用 Windows 或 macOS，则需要各自安装 X 服务器实现。

    对于 SSH 连接到远程服务器的场景，可以使用 `ssh -X`（或 `ssh -Y` (1)）为远程的服务器上的 X 客户端暴露自己的 X 服务器。下面的例子假设了 X 服务器 socket 是一个本地的 UNIX socket 文件，但是这对 SSH X forwarding 的场景来说并不适用（SSH 会使用 TCP 转发 X 端口）。对应的，如果正在使用 SSH 测试下面的内容，那么在传递环境变量与 `$HOME/.Xauthority` 文件的同时，还需要设置容器与主机使用相同的网络（`--network host`）。
    {: .annotate }

    1. 当使用 `-X` 时，服务端会假设客户端是不可信任的，因此会限制一些操作；`-Y` 选项则会放宽这些限制。详见 [ssh_config(5)][ssh_config.5] 对 `ForwardX11Trusted` 的介绍。

X 客户端连接到服务器，首先需要知道 X 服务器的地址。这是由 `DISPLAY` 环境变量指定的，一般是 `:0`，代表连接到 `/tmp/.X11-unix/X0` 这个 UNIX socket。
此外，由于 X 的协议设计是「网络透明」的，因此 X 服务器理论上也可以以 TCP 的方式暴露出来（但是不建议这么做），客户端通过类似于 `DISPLAY=host:port` 的方式连接。

因此，首先需要传递 `DISPLAY` 环境变量，并且将 `/tmp/.X11-unix` 挂载到容器中：

```console
sudo docker run -it --rm -e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix ustclug/debian:12
```

为了测试，可以在容器里安装 `x11-apps`，然后运行 `xeyes`。如果配置正确，可以看到一双眼睛在跟随鼠标。
但是上面的配置是不够的：

```console
root@6f640b929f0e:/# xeyes
Authorization required, but no authorization protocol specified

Error: Can't open display: :0
```

这是因为 X 服务器需要认证信息才能够连接，对应的认证信息就在名为 "Xauthority" 的文件中，对应 `XAUTHORITY` 环境变量：

```console
$ echo $XAUTHORITY  # 一个例子，实际值会根据环境不同而不同
/run/user/1000/.mutter-Xwaylandauth.5S15L2
```

如果这个环境变量不存在，那么就会使用默认值：当前用户的家目录下的 `.Xauthority` 文件。

!!! warning "避免直接关闭认证的做法"

    如果阅读网络上的一些教程，它们可能会建议直接关闭 X 服务器的认证，就像这样：

    ```console
    xhost +
    ```

    这在安全性上是**非常糟糕**的做法，因为这样的话就会允许所有能访问到 X 服务器的人/程序连接。

所以也需要将这一对环境变量和文件塞进来：

```console
sudo docker run -it --rm -e "DISPLAY=$DISPLAY" -e "XAUTHORITY=$XAUTHORITY" -v /tmp/.X11-unix:/tmp/.X11-unix -v $XAUTHORITY:$XAUTHORITY ustclug/debian:12
```

这样就可以在容器中运行基本的图形应用了。
不过，如果实际需求是在类似沙盒的环境中运行图形应用，有一些更合适的选择，例如 [bubblewrap](https://github.com/containers/bubblewrap) 以及基于此的 [Flatpak](https://flatpak.org/) 等。

??? note "GPU"

    **（以下内容不完全适用于使用 NVIDIA 专有驱动的 NVIDIA GPU）**

    在 Linux 下，GPU 设备文件位于 `/dev/dri` 目录下。每张显卡会暴露两个设备文件，其中 `cardX` 代表了完整的 GPU 设备（有写入权限相当于有控制 GPU 的完整权限），而 `renderDXXX` 代表了 GPU 的渲染设备。对于需要 GPU 加速渲染的场景，为其挂载 `/dev/dri/renderDXXX` 设备即可。

    与此同时，容器内还需要安装对应的 GPU **用户态**驱动。对于开源驱动来说，安装 Mesa 即可。

### Registry

Registry 是存储与分发容器镜像的服务。在大部分时候，我们使用的 registry 是 [Docker Hub](https://hub.docker.com/)。

!!! warning "区分 Docker 和 Docker Hub"

    Docker 是容器运行时，而 Docker Hub 是一个 registry 服务。除了 Docker Hub 以外，还有很多其他的 registry 服务，
    这些服务提供的容器镜像也可以正常在 Docker 中使用。

镜像名称的格式是 `registry.example.com:username/image:tag`，其中在 Docker 中，如果没有指定 registry，默认会使用 Docker Hub；而如果没有指定 username，则默认会指定为 `library`，其代表 Docker Hub 中的「官方」镜像。

Registry 服务大多允许用户上传自己的容器镜像。在对应的服务注册帐号，使用 `docker login` 登录之后，需要先使用 `docker tag` 为自己的镜像打上对应的标签：

```console
sudo docker tag example:latest registry.example.com:username/example:latest
```

然后再 `docker push`：

```console
sudo docker push registry.example.com:username/example:latest
```

除了 Docker Hub 以外，另一个比较常见的 registry 服务是 [GitHub Container Registry (ghcr)](https://ghcr.io)。它与 GitHub 的其他功能，如 Actions 有更好的集成（例如可以直接使用 `${{ secrets.GITHUB_TOKEN }}` 来登录到 ghcr）。[谷歌](https://gcr.io)和[红帽](https://quay.io)也提供了自己的 registry 服务。

### Volume

Volume 是 Docker 提供的一种持久化存储的方式，可以用于保存数据、配置等。
上面介绍了使用 `-v HOST_PATH:CONTAINER_PATH` 的方式挂载宿主机的目录（这种方式也被称为 bind mount），不过如果将参数写成 `-v VOLUME_NAME:CONTAINER_PATH` 的形式，那么 Docker 就会自动创建一个以此命名的 volume，并且将其挂载到容器中。

```console
$ sudo docker run -it --rm -v myvolume:/myvolume ustclug/debian:12
root@c273ee70fe7a:/# touch /myvolume/a
root@c273ee70fe7a:/# ls /myvolume/
a
```

Volume 在这里不会因为容器销毁被删除：

```console
root@c273ee70fe7a:/#
$ # 原来的容器没了，挂载相同的 volume 开个新的
$ sudo docker run -it --rm -v myvolume:/myvolume ustclug/debian:12
root@38e2da3a59f7:/# ls /myvolume/
a
```

可以查看 Docker 管理的所有 volume，它们在文件系统中的实际位置：

```console
$ sudo docker volume ls
DRIVER    VOLUME NAME
local     2aa17ad1c2ee9bf3b2933d241a5196bdaff5e144abcfbf4c1d161198f0f35912
（省略）
local     myvolume
（省略）
$ sudo docker inspect myvolume
[
    {
        "CreatedAt": "2024-04-14T22:54:12+08:00",
        "Driver": "local",
        "Labels": null,
        "Mountpoint": "/var/lib/docker/volumes/myvolume/_data",
        "Name": "myvolume",
        "Options": null,
        "Scope": "local"
    }
]
```

此外，在上面列出的 volume 里面，有一些没有名字，显示为哈希值的 volume。这些被称为「匿名 volume」。
例如，如果在创建容器的时候不指定 volume 名字，那么 Docker 就会自动创建一个匿名 volume：

```console
$ sudo docker run -it --rm --name test -v /myvolume ustclug/debian:12
root@ec434eb92714:/# # 打开另一个终端
$ sudo docker inspect test
（省略）
        "Mounts": [
            {
                "Type": "volume",
                "Name": "e97304e5a0d8a981b4f0c62b776f6fcaed8d8a6a7263d8e8b7b2f1ea60018976",
                "Source": "/var/lib/docker/volumes/e97304e5a0d8a981b4f0c62b776f6fcaed8d8a6a7263d8e8b7b2f1ea60018976/_data",
                "Destination": "/myvolume",
                "Driver": "local",
                "Mode": "",
                "RW": true,
                "Propagation": ""
            }
        ],
```

如果在 `docker run` 时添加了 `--rm` 参数，那么匿名 volume 会在容器销毁时被删除。
反之，手动 `docker rm` 一个容器时，它对应的匿名 volume 不会被删除。

同时，Dockerfile 中也可以使用 `VOLUME` 指令声明 volume。如果用户在运行容器的时候没有指定 volume，那么 Docker 就会自动创建一个匿名 volume。
一个例子是 [`mariadb` 容器镜像](https://hub.docker.com/layers/library/mariadb/lts/images/sha256-e0a092f10ea8a4c33e88b790606b68dab3d00e6b1ef417f6f5d8e825574e1fa6?context=explore)：

```dockerfile
VOLUME [/var/lib/mysql]  # Layer 18
```

### 网络 {#docker-network}

Docker 的网络隔离基于 Linux 的网络命名空间等特性。
默认情况下，Docker 会创建三种网络：

```console
$ sudo docker network ls
NETWORK ID     NAME                   DRIVER    SCOPE
47bf1753e571   bridge                 bridge    local
a490cc0dc175   host                   host      local
4ad7868e3a47   none                   null      local
```

其中 `bridge` 为容器默认使用的网络，`host` 为容器与宿主机共享网络，`none` 则是不使用网络（只保留本地回环）。
可以使用 `--network` 参数指定容器使用的网络。

#### Bridge 介绍 {#docker-bridge}

在计算机网络中，网桥（bridge）负责连接两个网络，提供在网络之间过滤与转发数据包等功能。
而在 Docker 中，bridge 网络也可以看作是连接容器网络和主机网络之间的桥。
连接到相同 bridge 的容器之间可以互相通信。

!!! note "bridge 在 Linux 上的实现"

    首先，Docker 会创建一个虚拟的 `docker0` 网络设备作为网桥，这个设备默认对应了 IP 段 `172.17.0.1/16`，
    创建的容器会被分配到这个网段中的一个 IP 地址。路由表也会将对这个网段的请求转发到 `docker0` 设备上：

    ```console
    $ ip a show docker0
    20: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
        link/ether 02:42:e0:cb:d8:81 brd ff:ff:ff:ff:ff:ff
        inet 172.17.0.1/16 brd 172.17.0.255 scope global docker0
            valid_lft forever preferred_lft forever
        inet6 fe80::42:e0ff:fecb:d881/64 scope link proto kernel_ll 
            valid_lft forever preferred_lft forever
    $ ip route get 172.17.0.2
    172.17.0.2 dev docker0 src 172.17.0.1 uid 1000 
        cache
    ```

    在默认网络配置下，如果创建了容器，可以发现增加了对应数量的 `veth`（虚拟以太网）设备：

    ```console
    $ # 开启了两个容器的情况下
    $ ip a
    （省略）
    7: veth5669cd1@if6: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master docker0 state UP group default 
        link/ether 96:2b:10:03:cc:36 brd ff:ff:ff:ff:ff:ff link-netnsid 1
        inet6 fe80::942b:10ff:fe03:cc36/64 scope link 
            valid_lft forever preferred_lft forever
    9: veth9219d7b@if8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master docker0 state UP group default 
        link/ether d2:b8:23:74:49:2a brd ff:ff:ff:ff:ff:ff link-netnsid 2
        inet6 fe80::d0b8:23ff:fe74:492a/64 scope link 
            valid_lft forever preferred_lft forever
    ```

    `veth` 设备可以看作是一根虚拟的网线，一端连接到容器内部（容器内部安装 `iproute2` 之后可以 `ip a` 看到 eth0 这个设备），另一端连接到 `docker0` 网桥。
    但是仅仅有设备是不够的，Docker 还需要配置主机的 iptables 规则，否则尽管容器与主机之间能够正常通信，容器无法通过主机访问外部网络。
    换句话讲，我们需要主机为容器扮演「路由器」的角色进行 NAT。

    查看 iptables 的 `nat` 表：

    ```console
    $ sudo iptables -t nat -S
    -P PREROUTING ACCEPT
    -P INPUT ACCEPT
    -P OUTPUT ACCEPT
    -P POSTROUTING ACCEPT
    -N DOCKER
    -A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
    -A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
    -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
    -A DOCKER -i docker0 -j RETURN
    ```

    对于容器访问外部网络的数据包，会经过 `POSTROUTING` 链的 `MASQUERADE` 规则，将源地址替换为主机的地址。
    同时，Docker 也会控制 iptables 处理端口映射等规则，例如如果启动这样一个容器：

    ```console
    sudo docker run -it --rm -p 8080:80 nginx
    ```

    那么 `DOCKER` 和 `POSTROUTING` 链就会变成这样：

    ```console
    $ sudo iptables -t nat -S
    -P PREROUTING ACCEPT
    -P INPUT ACCEPT
    -P OUTPUT ACCEPT
    -P POSTROUTING ACCEPT
    -N DOCKER
    -A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
    -A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
    -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
    -A POSTROUTING -s 172.17.0.4/32 -d 172.17.0.4/32 -p tcp -m tcp --dport 80 -j MASQUERADE
    -A DOCKER -i docker0 -j RETURN
    -A DOCKER ! -i docker0 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 172.17.0.4:80
    ```

    对于外部到本机的访问，`PREROUTING` 链在跳转到 `DOCKER` 链之后，对于未进入 `docker0` 的 TCP 数据包，会根据 `DNAT` 规则将端口 `8080` 的数据包的目的地址修改为到该容器内部的 `80` 端口。

    <!-- TODO: 到网络部分的链接 -->

    特别地，到本地回环 8080 端口的连接，会由用户态的 `docker-proxy` 程序负责「转发」到容器对应的端口上。
    对该用户态程序的讨论，可以阅读 <https://github.com/moby/moby/issues/11185>。

可以通过 `docker network create` 创建自己的网络。对于新的 bridge 类型的网络，在主机上也会创建新的以 `br-` 开头的网桥设备。如果使用 docker compose 管理容器服务，那么其也会为对应的服务自动创建 bridge 类型的网络。有关用户创建的 bridge 网络相比于默认网络的优势（例如同网络容器间自动的 DNS 解析支持），可参考官方文档：[Bridge network driver](https://docs.docker.com/network/drivers/bridge/#differences-between-user-defined-bridges-and-the-default-bridge)。

默认情况下，Docker 创建的网络会[分配很大的 IP 段](https://github.com/moby/moby/blob/b7c059886c0898436db90b4615a27cfb4d93ce34/libnetwork/ipamutils/utils.go#L18-L26)。
在创建了很多网络之后，可能会发现内网 IP 地址都被 Docker 占用了。我们建议修改 `/etc/docker/daemon.json`，将 `default-address-pools` 设置为一个较小的 IP 段：

```json
{
	"default-address-pools": [
		{
			"base": "172.17.1.0/24",
			"size": 28
		},
		{
			"base": "172.17.2.0/23",
			"size": 28
		}
	],
}
```

此外，默认 `docker0` 的地址段也可以修改，对应 `bip` 选项：

```json
{
    "bip": "172.17.0.1/24"
}
```

#### 防火墙配置 {#docker-firewall}

在 Linux 上，防火墙功能一般的实现方式是在 iptables 的 filter 表中添加规则。
而由于 Docker 自身支持为容器配置不同的网络，因此也需要操作 filter 表来保证容器之间的网络隔离。
Docker 会在 filter 表的 `FORWARD` 链中添加这样的规则：

```iptables
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
```

这些规则在 `FORWARD` 链最前面——即使自行添加了规则，Docker 服务重启之后它也会在最前面重新添加。

其中 `DOCKER-USER` 链允许用户自定义规则，其他以 `DOCKER` 开头的链则由 Docker 自行管理。
在有端口映射的情况下，`DOCKER` 链会直接允许对应的数据包，不经过之后的规则：

```iptables
-A DOCKER -d 172.17.0.4/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 80 -j ACCEPT
```

而例如在 Ubuntu/Debian 上比较常见的 ufw 工具，它的规则会在 Docker 的规则后面。
一个例子如下：

```iptables
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
-A FORWARD -o br-3e32bdc5bc2a -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o br-3e32bdc5bc2a -j DOCKER
-A FORWARD -i br-3e32bdc5bc2a ! -o br-3e32bdc5bc2a -j ACCEPT
-A FORWARD -i br-3e32bdc5bc2a -o br-3e32bdc5bc2a -j ACCEPT
-A FORWARD -j ufw-before-logging-forward
-A FORWARD -j ufw-before-forward
-A FORWARD -j ufw-after-forward
-A FORWARD -j ufw-after-logging-forward
-A FORWARD -j ufw-reject-forward
-A FORWARD -j ufw-track-forward
```

于是这就导致了配置的「防火墙」对 Docker 形同虚设的问题。
如果不希望自行管理 `DOCKER-USER` 链，建议将端口映射设置为只向 `127.0.0.1` 开放，然后使用其他的程序（例如 Nginx）来对外提供服务（如果希望设置为默认选项，可以参考文档中 [Setting the default bind address for containers](https://docs.docker.com/network/packet-filtering-firewalls/#setting-the-default-bind-address-for-containers) 一节。）；或者配置让容器直接使用 host 网络。

#### IPv6

Docker 默认未开启 IPv6，并且在比较老的版本中，配置 IPv6 会比较麻烦。
一个重要的原因是：Docker 对 IPv4 的策略是配置 NAT 网络，但在 IPv6 的设计中，NAT 不是很「原教旨主义」（毕竟 IPv6 的地址多得用不完，为什么还要有状态的 NAT 呢？）。这就导致了在之前，Docker 中配置可用的 IPv6 就需要：

- 要么每个容器一个公网 IPv6 地址（否则容器无法连接外部的 IPv6 网络）。要这么做的前提是得知道自己能控制的 IPv6 段，并且容器打开的所有端口都会暴露在公网上。
- 使用[第三方的方案](https://github.com/robbertkl/docker-ipv6nat)帮忙做 IPv6 NAT，同时给容器分配 IPv6 的 ULA（Unique Local Address）地址段（目前可以分配 fd00::/8 内的地址段）。

不过好消息是，目前 Docker 添加了对 IPv6 NAT 的实验性支持，尽管默认的 bridge 网络的 IPv6 支持仍然不是默认打开的。
参考[对应的文档](https://docs.docker.com/config/daemon/ipv6/)[^ipv6-docaddr]，一个配置 daemon.json 的例子如下：

```json
{
    "ipv6": true,
    "fixed-cidr-v6": "fd00::/80",
    "experimental": true,
    "ip6tables": true
}
```

这样新建的容器就能得到一个在 fd00::/80 内的 IPv6 地址，并且顺利访问外部的 IPv6 网络了：

```console
root@14354a8c5349:/# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
52: eth0@if53: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:ac:11:00:03 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.3/24 brd 172.17.0.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fd00::242:ac11:3/80 scope global nodad 
       valid_lft forever preferred_lft forever
    inet6 fe80::42:acff:fe11:3/64 scope link 
       valid_lft forever preferred_lft forever
root@14354a8c5349:/# ping6 mirrors.ustc.edu.cn
PING mirrors.ustc.edu.cn(2001:da8:d800:95::110 (2001:da8:d800:95::110)) 56 data bytes
64 bytes from 2001:da8:d800:95::110 (2001:da8:d800:95::110): icmp_seq=1 ttl=62 time=2.42 ms
```

#### VLAN

VLAN（虚拟局域网）用于将一个物理局域网划分为多个逻辑上的局域网，以实现网络隔离。Docker 支持 `macvlan` 和 `ipvlan` 两种 VLAN 驱动，前者允许每个容器拥有自己的 MAC 地址，后者则允许每个容器拥有自己的 IP 地址（MAC 地址共享）。这个功能适用于需要将多个容器直接在某个特定网络内提供服务的场景——一种场景是，内网使用 tinc 互联，希望能够使用内网的 IP 地址连接内部服务，而这些服务又在 Docker 容器中。此时可以使用 Docker 的 VLAN 功能，并且为容器分配不同的内网 IP 地址，实现内网通过对应的 IP 即可直接访问到容器服务的需求。

!!! note "Bridge 与 macvlan"

    如果你曾经有过使用类似于 VMware 虚拟机软件的经验，可能会发现：软件中的 NAT 更像是 Docker 里面的 bridge，而「桥接」则更像是这里介绍的 macvlan。
    
    Linux 下的 bridge 实际上是一个虚拟的交换机：在创建 bridge 之后，可以为这个 bridge 添加其他的设备作为 "slave"（设置其他设备的 "master" 为这个 bridge），然后 bridge 就像交换机一样转发数据包。同时，bridge 也支持设置一个 IP 地址，相当于在主机一端有一个自己的 "slave"。Docker 默认的 bridge 网络模式则是利用了这一点：bridge 的 IP 为容器的网关，主机一端的 veth 设备的 master 是 Docker 创建的 bridge 设备。这个 bridge 不对应到具体的物理设备（Docker 未提供相关的配置方式）。

    而虚拟机软件的桥接则需要指定一个物理设备，这个设备会加入虚拟的交换机里面，虚拟机也会连接到这个交换机上。从外部来看，这种模式和 macvlan 的效果是一样的：有多个不同的 MAC 地址的设备连接到同一个物理网络上，但是具体实现是不同的。

    Macvlan 与 IPvlan 功能也支持对接基于 IEEE 802.1Q 的 VLAN 配置，但是这里不做详细介绍。

##### Macvlan

由于每个容器都有不同于对应网络设备的 MAC 地址，因此 macvlan 模式要求网络设备支持混杂模式（promiscuous mode），即处理所有经过的数据包，即使数据包的 MAC 地址不是自己的。

以下以一台 Linux 虚拟机为例，对应的「物理」网络设备为 `enp1s0`：

```console
$ ip a show enp1s0
2: enp1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:d3:7d:6f brd ff:ff:ff:ff:ff:ff
    inet 192.168.122.247/24 brd 192.168.122.255 scope global dynamic noprefixroute enp1s0
       valid_lft 3577sec preferred_lft 3577sec
    inet6 fe80::5054:ff:fed3:7d6f/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever
```

我们创建一个 macvlan 网络，并且启动多个容器：

```console
$ sudo docker network create -d macvlan --subnet=192.168.122.0/25 --gateway=192.168.122.1 -o parent=enp1s0 macvlan_test
047c9f91cb1a6962d45a916f60c612b0174be5425dcf75d55da1b964037d518f
$ sudo docker run -it --network macvlan_test --name ct1 -d --ip 192.168.122.10 ustclug/debian:12
83570467e991dea9fe9f221d7e4e6256f37d193a000b23777a4d37429cdd5e47
$ sudo docker run -it --network macvlan_test --name ct2 -d --ip 192.168.122.11 ustclug/debian:12
ea0ef56a73d940dad0b860099e2d8fe26ddcba1d424824e3f45bf4f492dd54f1
```

由于 macvlan 的实现原因，这两个 IP 在主机上无法 ping 通，但是容器之间，以及与虚拟机处在同一个子网的其他设备之间可以通信。

```console
$ # 该虚拟机
$ ping 192.168.122.10
PING 192.168.122.10 (192.168.122.10) 56(84) bytes of data.
From 192.168.122.247 icmp_seq=1 Destination Host Unreachable
...
$ # ct1 内部——需要先安装 iputils-ping
$ sudo docker exec -it ct1 ping 192.168.122.11
PING 192.168.122.11 (192.168.122.11) 56(84) bytes of data.
64 bytes from 192.168.122.11: icmp_seq=1 ttl=64 time=0.095 ms
...
$ # 同子网其他设备（例如宿主机）
$ ping 192.168.122.10
PING 192.168.122.10 (192.168.122.10) 56(84) bytes of data.
64 bytes from 192.168.122.10: icmp_seq=1 ttl=64 time=0.284 ms
...
```

同时，也可以验证它们的 MAC 地址不同：

```console
$ sudo arping 192.168.122.10
ARPING 192.168.122.10 from 192.168.122.1 virbr0
Unicast reply from 192.168.122.10 [02:42:C0:A8:7A:0A]  1.091ms
...
$ sudo arping 192.168.122.11
ARPING 192.168.122.11 from 192.168.122.1 virbr0
Unicast reply from 192.168.122.11 [02:42:C0:A8:7A:0B]  0.979ms
...
```

解决这个问题的一种方法是在主机上添加一个（和容器的 macvlan 一样的）新的 macvlan 接口，这样就可以互相通信了：

```console
$ sudo ip link add macvlan-enp1s0 link enp1s0 type macvlan mode bridge
$ sudo ip addr add 192.168.122.9/25 dev macvlan-enp1s0
$ sudo ip link set macvlan-enp1s0 up
$ ping 192.168.122.10
PING 192.168.122.10 (192.168.122.10) 56(84) bytes of data.
64 bytes from 192.168.122.10: icmp_seq=1 ttl=64 time=0.172 ms
```

##### IPvlan

这里主要关注 IPvlan 的 L2 模式（也是 IPvlan 的默认模式），L3 模式与上文的场景不同，更加关注网络的隔离，和 bridge 网络类似（主机外部网络无法访问到其中的容器）。
同时由于不需要额外的 MAC 地址，IPvlan 可以避免混杂模式的开启。

和 macvlan 非常相似，仍然是创建网络与容器：

```console
$ # 在执行命令之前，需要先清除上文的 macvlan 网络，否则网段会冲突，无法创建
$ # 清理之后就可以：
$ sudo docker network create -d ipvlan --subnet=192.168.122.0/25 --gateway=192.168.122.1 -o parent=enp1s0 ipvlan_test
1d7118ac1a4520b08d4420260700550bb1bcf2ff2badf6f2aeae830b7119502c
$ # 下面的内容和 macvlan 是几乎一致的，省略
```

主机无法连通容器 IP 的问题仍然存在，解决方法也几乎一致：

```console
$ sudo ip link add ipvlan-enp1s0 link enp1s0 type ipvlan mode l2
$ # 后面省略……
$ ping 192.168.122.10
PING 192.168.122.10 (192.168.122.10) 56(84) bytes of data.
64 bytes from 192.168.122.10: icmp_seq=1 ttl=64 time=0.154 ms
```

同时，容器与主机共享相同的 MAC 地址：

```console
$ sudo arping 192.168.122.10
ARPING 192.168.122.10 from 192.168.122.1 virbr0
Unicast reply from 192.168.122.10 [52:54:00:D3:7D:6F]  0.687ms
...
$ sudo arping 192.168.122.11
ARPING 192.168.122.11 from 192.168.122.1 virbr0
Unicast reply from 192.168.122.11 [52:54:00:D3:7D:6F]  0.721ms
...
$ sudo arping 192.168.122.247  # 虚拟机主机
ARPING 192.168.122.247 from 192.168.122.1 virbr0
Unicast reply from 192.168.122.247 [52:54:00:D3:7D:6F]  0.852ms
...
```

### Docker Compose

Docker compose 是 Docker 官方提供的运行多个容器组成的服务的工具：用户编写 YAML 描述如何启动容器，然后使用 `docker-compose` 命令启动、停止、删除服务。

作为一个直观的例子，对于类似于下面这样需要大量设置环境变量与挂载点的的单容器启动命令：

```console
docker run -it --rm -e "DISPLAY=$DISPLAY" \
                    -e "XAUTHORITY=$XAUTHORITY" \
                    -v /tmp/.X11-unix:/tmp/.X11-unix \
                    -v "$XAUTHORITY:$XAUTHORITY" \
                    -v /dev/dri/renderD128:/dev/dri/renderD128 \
                    -v /run/user/1000/pipewire-0:/run/pipewire/pipewire-0 \
                    -v /run/user/1000/pulse:/run/pulse/native \
                    local/example-desktop-1
```

可以发现这样写不直观，并且容易出错（对于这里的例子，把 `-e` 和 `-v` 写反了 Docker 启动容器不会报错）。而使用 Docker compose，就可以将这些参数写入一个 `docker-compose.yml` 文件：

```yaml
version: "2"
services:
  desktop:
    image: local/example-desktop-1
    environment:
      - DISPLAY=$DISPLAY
      - XAUTHORITY=$XAUTHORITY
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
      - $XAUTHORITY:$XAUTHORITY
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /run/user/1000/pipewire-0:/run/pipewire/pipewire-0
      - /run/user/1000/pulse:/run/pulse/native
```

然后跑一下 `docker compose up`，容器就可以启动。相比于上述的命令来讲直观得多了。

#### 版本 {#compose-version}

Docker compose 有 v1 和 v2 两个版本，而其配置文件（Compose file）则有 version 1（不再使用）、version 2、version 3，以及最新的 [Compose Specification](https://docs.docker.com/compose/compose-file/) 四种版本，容易造成混乱。

Docker compose 的 v1 版本（基于 Python）已经于 2021 年 5 月停止维护。如果你是从 Debian 的官方源安装的 `docker-compose` 包，那么就是 v1 版本的 compose：

```console
$ docker-compose --version
docker-compose version 1.29.2, build unknown
docker-py version: 5.0.3
CPython version: 3.11.2
OpenSSL version: OpenSSL 3.0.11 19 Sep 2023
```

从 Docker 源（docker-ce）安装的 `docker-compose-plugin` 则是 v2 版本的（基于 Go 语言）。v2 版本的 compose 此时作为 Docker 的插件，推荐的运行方式是 `docker compose`（不含横线）：

```console
$ docker compose version
Docker Compose version v2.24.5
```

从 v1 迁移到 v2 的细节问题参见 [Migrate to Compose V2](https://docs.docker.com/compose/migrate/)（主要是容器名称与环境变量处理上存在差异）。

特别地，Ubuntu 在官方源中打包了 `docker-compose-v2` 这个包。

对于 compose 文件，早期 version 2 与 version 3 的共存导致了一些混乱，因为后者是为了与 Docker Swarm（集群管理）兼容而设计的，丢弃了一些有意义的功能。

!!! warning "避免在非 swarm 集群场合使用 version 3 compose 文件格式"

    Version 3 格式令人诟病一点的是其[抛弃了对资源限制的支持](https://docs.docker.com/compose/compose-file/compose-versioning/#version-2x-to-3x)。最为糟糕的是，如果配置了资源限制，docker-compose 不会输出警告，而是直接忽略：

    > `cpu_shares`, `cpu_quota`, `cpuset`, `mem_limit`, `memswap_limit`: These have been replaced by the [resources](https://docs.docker.com/compose/compose-file/compose-file-v3/#resources) key under `deploy`. `deploy` configuration only takes effect when using `docker stack deploy`, and is ignored by `docker-compose`.

    ??? note "测试用 `docker-compose.yml` 文件"

        ```yaml
        version: '3.8'
        services:
          python-app:
            image: python:3.10-slim
            command: python -c "print('Init'); a = [0] * 4000000; print('Array created')"
            mem_limit: 16m
            memswap_limit: 16m
            environment:
              - PYTHONUNBUFFERED=1
        ```

        如果运行的 compose 环境支持 Compose Specification，那么这个容器不会输出 Array created（在分配内存时即被杀死）。

    如果不知道这一点，那么就只会在容器把机器资源耗尽之后才能发现问题。就目前的情况而言，如果仍然有使用旧版 docker-compose（不支持 Compose Specification 格式，即 1.27.0 以下的版本）的需求，建议使用 version 2 格式。相关讨论可以参考：<https://github.com/docker/compose/issues/4513>。

考虑到 Docker compose v1 已经不再维护，并且 Compose Specification 保持了对旧版 compose 文件的兼容性，因此下文仅考虑最新的 compose v2 与 Compose Specification 文件格式。

#### 配置文件与基本使用 {#compose-format-and-usage}

Compose Specification 规定了以下这些 "top-level" 元素：

- Version 和 name
- Services
- Network
- Volumes
- Configs
- Secrets

其中前四项是最常见的。同时 Compose Specification 已经不再需要写版本号（已有的会被忽略），而项目名称也是可选的（默认为当前目录名），所以一个最简单的 compose 文件可以只有 `services` 一项：

```yaml
services:
  hello-world:
    image: hello-world
```

假设当前目录名为 `helloworld`，运行 `docker compose up` 之后，可以看到 compose 会创建一个名为 `helloworld-hello-world-1` 的容器，并且为容器创建 `helloworld-hello-world-1` 的 bridge 网络——由于 `hello-world` 的唯一功能是输出一段文字，所以容器会立即退出。

在测试完成后，使用 `docker compose down` 销毁环境（否则容器和网络会一直存在）。接下来的部分会分析一些使用 Docker compose 的例子。

#### 案例 1：Hackergame 的 nc 类题目 Docker 容器环境 {#compose-hackergame-nc}

[Hackergame nc 类题目的 Docker 容器资源限制、动态 flag、网页终端](https://github.com/USTC-Hackergame/hackergame-challenge-docker) 提供了两个服务。其中 `dynamic_flag` 由 xinetd 暴露一个 TCP 端口，在客户端（nc）连接时，xinetd 会执行 `front.py` 脚本处理请求。脚本会要求用户输入 token，检查 token 有效性与连接频率，然后根据预先设置的规则生成 flag，创建并启动容器，由对应的题目容器与用户交互。题目容器内不需要做诸如验证 token、限制资源、处理网络连接等工作，只需要与用户使用标准输入输出交互即可。而 `web_netcat` 服务则是一个网页终端，用户可以通过浏览器连接到这个服务，然后在网页上输入命令与 `dynamic_flag` 交互。

[`dynamic_flag` 的 `docker-compose.yml`](https://github.com/USTC-Hackergame/hackergame-challenge-docker/blob/4311cbfb6b3159192ff882d609fed5bbc7936f88/dynamic_flag/docker-compose.yml) 文件类似如下：

```yaml
version: '2.4'
services:
  front:
    build: .
    ports:
      - ${port}:2333
    restart: always
    read_only: true
    ipc: shareable
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    environment:
      - hackergame_conn_interval=${conn_interval}
      - hackergame_token_timeout=${token_timeout}
      - hackergame_challenge_timeout=${challenge_timeout}
      - hackergame_pids_limit=${pids_limit}
      - hackergame_mem_limit=${mem_limit}
      - hackergame_flag_path=${flag_path}
      - hackergame_flag_rule=${flag_rule}
      - hackergame_challenge_docker_name=${challenge_docker_name}
      - hackergame_read_only=${read_only}
      - hackergame_flag_suid=${flag_suid}
      - hackergame_challenge_network=${challenge_network}
      - hackergame_shm_exec=${shm_exec}
      - TZ=Asia/Shanghai
```

其中 `build: .` 表示使用当前目录下的 Dockerfile 构建镜像，其他的配置项都可以找到 `docker run` 的对应参数。配置中形如 `${port}` 的部分被称为 [Interpolation](https://docs.docker.com/compose/compose-file/12-interpolation/)，在运行时会被替换——这里替换这些变量的值位于同一目录的 `.env`，目前最新版本使用的格式定义可参考[文档说明](https://docs.docker.com/compose/compose-file/05-services/#env_file-format)。

[`web_netcat` 的 `docker-compose.yml`](https://github.com/USTC-Hackergame/hackergame-challenge-docker/blob/4311cbfb6b3159192ff882d609fed5bbc7936f88/web_netcat/docker-compose.yml) 也类似：

```yaml
version: '2.4'
services:
  web:
    build: .
    ports:
      - ${web_port}:3000
    environment:
      - nc_host=${nc_host}
      - nc_port=${nc_port}
      - nc_raw=${nc_raw}
    restart: always
    init: true
```

其中 [`init: true`](https://docs.docker.com/reference/cli/docker/container/run/#init) 表示 Docker 会在容器启动时使用基于 [tini](https://github.com/krallin/tini) 的 `docker-init` 管理容器内进程。

用户需要运行的题目的示例则在 `example` 目录下，可以看一下[这里的 `docker-compose.yml`](https://github.com/USTC-Hackergame/hackergame-challenge-docker/blob/4311cbfb6b3159192ff882d609fed5bbc7936f88/example/docker-compose.yml) 文件：

```yaml
version: '2.4'
services:
  challenge:
    build: .
    entrypoint: ["/bin/true"]
  front:
    extends:
      file: ../dynamic_flag/docker-compose.yml
      service: front
    depends_on:
      - challenge
  web:
    extends:
      file: ../web_netcat/docker-compose.yml
      service: web
```

其中 `challenge` 服务代表题目本身，这里修改 `entrypoint`，让运行时行为变成直接退出，只是为了能让 compose 创建出对应的容器镜像（选手在连接时由拥有 Docker socket 的 `front` 操作为每个选手创建、运行容器）。`front` 与 `web` 使用了 [`extends` 指令](https://docs.docker.com/compose/compose-file/05-services/#extends)来继承对应的 compose 配置。另外，`depends_on` 指令表示 `front` 服务依赖于 `challenge` 服务，即 `challenge` 服务启动后 `front` 服务才会启动。

在 `extends` 之后 interpolation 会优先使用当前目录的 `.env` 文件，因此 [`example/.env`](https://github.com/USTC-Hackergame/hackergame-challenge-docker/blob/4311cbfb6b3159192ff882d609fed5bbc7936f88/example/.env) 文件中可以覆盖掉上述两个目录下 `.env` 的配置。

最终生成的配置可以使用 `docker compose config` 查看。

??? note "Example 最后的实际配置"

    ```console
    $ docker compose config
    WARN[0000] /example/hackergame-challenge-docker/example/docker-compose.yml: `version` is obsolete
    name: example
    services:
      challenge:
        build:
          context: /example/hackergame-challenge-docker/example
          dockerfile: Dockerfile
        entrypoint:
          - /bin/true
        networks:
          default: null
      front:
        build:
          context: /example/hackergame-challenge-docker/dynamic_flag
          dockerfile: Dockerfile
        depends_on:
          challenge:
            condition: service_started
            required: true
        environment:
          TZ: Asia/Shanghai
          hackergame_challenge_docker_name: example_challenge
          hackergame_challenge_network: ""
          hackergame_challenge_timeout: "300"
          hackergame_conn_interval: "10"
          hackergame_flag_path: /flag1,/flag2
          hackergame_flag_rule: f"flag{{this_is_an_example_{sha256('example1'+token)[:10]}}}",f"flag{{this_is_the_second_flag_{sha256('example2'+token)[:10]}}}"
          hackergame_flag_suid: ""
          hackergame_mem_limit: 256m
          hackergame_pids_limit: "16"
          hackergame_read_only: "1"
          hackergame_shm_exec: "0"
          hackergame_token_timeout: "30"
        ipc: shareable
        networks:
          default: null
        ports:
          - mode: ingress
            target: 2333
            published: "10000"
            protocol: tcp
        read_only: true
        restart: always
        ulimits:
          nofile:
            soft: 65536
            hard: 65536
        volumes:
          - type: bind
            source: /var/run/docker.sock
            target: /var/run/docker.sock
            bind:
              create_host_path: true
      web:
        build:
          context: /example/hackergame-challenge-docker/web_netcat
          dockerfile: Dockerfile
        environment:
          nc_host: front
          nc_port: "2333"
          nc_raw: "0"
        init: true
        networks:
          default: null
        ports:
          - mode: ingress
            target: 3000
            published: "10001"
            protocol: tcp
        restart: always
    networks:
      default:
        name: example_default
    ```

#### 案例 2：Hackergame 比赛平台的 Docker compose 测试方案 {#compose-hackergame-platform}

（以下内容基于 <https://github.com/ustclug/hackergame/pull/175/files>）

Hackergame 比赛平台可以算是一个比较复杂的 Web 应用了：

- 平台使用 Django 框架，在生产环境中，需要使用 uWSGI 作为 WSGI 服务器。
- 平台需要使用 PostgreSQL 作为数据库。
    - 由于 uWSGI 使用了 gevent，因此 Django 自带的数据库连接池无法正常工作，需要使用 pgBouncer 在 Django 与 PostgreSQL 之间建立连接池。
- 平台使用 Memcached 作为内存缓存数据库。
- 在 uWSGI 外是 Nginx 作为反向代理，为用户暴露服务。

对于这里的 [`docker-compose.yml`](https://github.com/ustclug/hackergame/blob/3d0d2dcc08cb5a75b724fe4601e4f5e7043c4c6a/docker-compose.yml)，首先看 `services` 内部与数据库有关的三个服务：

```yaml
memcached:
  container_name: hackergame-memcached
  image: memcached
  restart: always
postgresql:
  container_name: hackergame-postgresql
  image: postgres:15
  restart: always
  environment:
    - POSTGRES_USER=hackergame
    - POSTGRES_PASSWORD=${DB_PASSWORD}
    - POSTGRES_DB=hackergame
  volumes:
    - hackergame-postgresql:/var/lib/postgresql/data/
pgbouncer:
  container_name: hackergame-pgbouncer
  image: edoburu/pgbouncer:latest
  restart: always
  environment:
    - DB_USER=hackergame
    - DB_PASSWORD=${DB_PASSWORD}
    - DB_HOST=postgresql
    - POOL_MODE=transaction
    # 坑: pg14+ 默认使用 scram-sha-256, 而 pgbouncer 默认是 md5
    - AUTH_TYPE=scram-sha-256
  depends_on:
    - postgresql
```

除去案例 1 中已经介绍的配置，这里设置了容器名称与 volume。对于数据库而言，添加 volume 进行持久化是有必要的，否则容器重启后数据就会丢失。如果定义了 volume，还需要在最外层的 `volumes` 中定义这个 volume。该 compose 文件定义了三个使用的 volume：

```yaml
volumes:
  hackergame-static:
  nginx-log:
  hackergame-postgresql:
```

!!! note "`docker compose down` 与 volume"

    默认情况下，`docker compose down` 不会删除 volume。如果需要删除 volume，可以使用 `docker compose down -v`。

而这里额外设置 `container_name`（容器名）的目的是，在这些容器组成的内网中，Docker 提供的 DNS 就允许使用更短的主机名（服务名）做服务（容器）之间的互相通信，而用户管理容器时因为容器名都以 `hackergame-` 开头，可以方便地区分平台容器与其他的容器。

??? note "`resolv.conf` 配置，与 `ping` 主机名与容器名的输出"

    ```console
    root@hackergame:/# cat /etc/resolv.conf
    # Generated by Docker Engine.
    # This file can be edited; Docker Engine will not make further changes once it
    # has been modified.

    nameserver 127.0.0.11
    search example.com
    options ndots:0

    # Based on host file: '/etc/resolv.conf' (internal resolver)
    # ExtServers: [192.168.0.1]
    # Overrides: []
    # Option ndots from: internal
    root@hackergame:/# ping nginx
    PING nginx (172.17.1.118) 56(84) bytes of data.
    64 bytes from hackergame-nginx.hackergame_default (172.17.1.118): icmp_seq=1 ttl=64 time=0.184 ms
    ^C
    root@hackergame:/# ping hackergame-nginx
    PING hackergame-nginx (172.17.1.118) 56(84) bytes of data.
    64 bytes from hackergame-nginx.hackergame_default (172.17.1.118): icmp_seq=1 ttl=64 time=0.233 ms
    ^C
    ```

!!! danger "映射端口的安全性（Compose）"

    如果阅读网络上某些 Docker compose 的配置，可能会发现他们会像这样将数据库的端口进行映射：

    ```yaml
    postgresql:
      image: postgres:15
      ports:
        - "5432:5432"
    ```

    除非有确切的需求需要数据库从该 compose 文件管理的容器之外的地方访问，否则**不应该这么设置**，理由和[基础概念部分](#docker-basic)中提到的一样。

    由于 compose 会为其管理的服务创建专门的 bridge 网络，而 bridge 网络内部的容器可以互相直接使用主机名通信，因此不需要像这么暴露端口也可以正常工作。

Django 部分的配置如下：

```yaml
hackergame:
  container_name: &name hackergame
  hostname: *name
  build: .
  restart: always
  environment:
    - DJANGO_SETTINGS_MODULE=conf.settings.docker
    - DB_PASSWORD=${DB_PASSWORD}
    # 调试用
    - DEBUG=True
  volumes:
    - .:/opt/hackergame/:ro
    # 存储静态网页与题目文件
    - hackergame-static:/var/opt/hackergame/
    # 很不幸，你可能还需要 bind 完整的题目目录进来（不然不方便导入）
  depends_on:
    - memcached
    - pgbouncer
```

这里的 `&name` 和 `*name` 利用了 YAML 的 [Anchor 与 Alias](https://yaml.org/spec/1.2/spec.html#id2765878) 功能。这里 `&name hackergame` 定义了一个名为 `name`，值为 `hackergame` 的 Anchor，而 `*name` 则表示使用 `name` 这个 Anchor 的值。

在这个例子中，使用这个特性或许有些小题大做，但是在一些复杂的配置中，可以使用 Anchor 定义一系列映射，类似这样：

```yaml
environment: &env
  - EXAMPLE=1
  - PYTHON_UNBUFFERED=1
  - TZ=Asia/Shanghai
  # ...
```

然后在其他地方使用 `*env` 引用这个映射：

```yaml
environment: *env

# 或者，如果需要再添加其他的值
environment:
  <<: *env
  - OTHER_ENV=2
```

Nginx 的 compose 配置没有新的特性，因此不再赘述。不过，另一点需要特别提及的是，在不使用 Docker compose 部署时，服务之间的通信使用了 UNIX socket，例如 [uwsgi 暴露的 socket 配置](https://github.com/ustclug/hackergame/blob/99bfb728670393757247f45679f9216cd64ae5ad/conf/uwsgi-apps/hackergame.ini#L2C1-L2C47)如下：

```ini
[uwsgi]
socket=unix:///run/uwsgi/app/hackergame/socket
# ...
```

而 [compose 实现替换为了 TCP socket](https://github.com/ustclug/hackergame/blob/f1754f0c93d90458cd29dbe288634f8bf01aae5c/conf/uwsgi-apps/hackergame-docker.ini#L2)：

```ini
[uwsgi]
socket=:2018
# ...
```

一个重要的原因是，UNIX socket 是有用户所有者和权限的，但是在多个容器的场合下，保证所有容器的 `/etc/passwd` 映射的用户一致是比较困难的。而 TCP socket 则解决了这个问题。但是其**安全性**需要考虑，例如 uWSGI 的 TCP socket 默认是没有额外的鉴权的，而能够连接到这个 socket 的进程就可以[执行任意命令](https://github.com/wofeiwo/webcgi-exploits/blob/master/python/uwsgi-rce-zh.md)，[在某些不正确的设置下，即使在配置中将 uWSGI 降权运行，也可以以此获取到更高的权限](https://github.com/PKU-GeekGame/geekgame-1st/tree/master/writeups/xmcp#%E6%97%A9%E6%9C%9F%E4%BA%BA%E7%B1%BB%E7%9A%84%E8%81%8A%E5%A4%A9%E5%AE%A4-uwsgi)。即使 uWSGI 的端口没有暴露到容器内网外部，如果有其他容器被攻破，那么攻击者也可以轻松横向移动到 uWSGI 所在容器。

!!! lab "Health check"

    在上面的例子中，我们限制了一些容器在其他容器启动之后再启动。但是在某些场景下，「容器启动」并不意味着「容器已经准备好接受请求」，在「启动」和「准备好」这个时间间隔中，启动需要对应服务的容器可能会失败。

    Docker 提供了 [Health check](https://docs.docker.com/reference/dockerfile/#healthcheck) 功能，可以定义健康检查的命令，在容器启动后，Docker 会定期执行这个命令，根据返回值判断容器是否「健康」。

    尝试编写一个 compose 文件，其中一个容器启动一个数据库（你可能需要自行定义 health check 命令），另一个容器需要在数据库准备好之后才能启动。

[^ipv6-docaddr]: 需要注意的是，文档中的 2001:db8:1::/64 这个地址隶属于 2001:db8::/32 这个专门用于文档和样例代码的地址段（类似于 example.com 的功能），不能用于实际的网络配置。
