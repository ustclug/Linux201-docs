# 网络存储系统

!!! warning "本文初稿编写中"

本文介绍在服务器上常见的网络存储方案，包括 NFS 与 iSCSI。
<!-- TODO: well, 我们没有使用过 ceph；如果有人有经验想写的话，可能需要放在高级内容里面 -->

## NFS

NFS 是非常常用的文件系统级别的网络存储协议，允许服务器暴露文件系统给多个客户端。
目前 NFS 有两个主要的版本：NFSv3 和 NFSv4。简单来讲：

- NFSv3（1995 年）是无状态协议，支持 TCP 与 UDP（2049，111 以及其他动态端口）
- NFSv4（2000 年）是有状态协议，只支持 TCP（2049 端口），性能更好

NFS 默认没有基于密码等的鉴权机制，仅依靠客户端 IP 地址来鉴权。并且默认没有加密，因此主要用于内部网络共享存储。
以下不涉及有关高级鉴权方法（如 Kerberos）与 TLS 加密的内容。

NFS 在 Linux 上的服务端和客户端实现均有内核态与用户态的选择，如果没有特殊考虑，建议使用内核态实现。

### 服务端配置

服务端需要安装 `nfs-kernel-server` 包。除此之外，NFSv3 支持还需要安装 `rpcbind` 包（对应 NFSv3 协议的 111 端口），该包在目前的 Debian 中以 `rpcbind.socket` 的形式对外提供服务。

<!-- TODO: a link to systemd socket -->

NFS 的导出配置位于 `/etc/exports` 文件中。例如以下的配置：

```exports
/srv/abcde        localhost(ro,no_root_squash,async,insecure,no_subtree_check)
```

将 `/srv/abcde` 目录「导出」给了本机（localhost），并且设置了诸如只读等选项。
在修改配置后，运行 `systemctl reload nfs-server.service`（等价于 `exportfs -r`）重新加载配置。

!!! lab "尝试配置并挂载"

    NFS 在各种主流桌面/服务器操作系统上都有不错的支持。请尝试在你的系统（虚拟机或 Linux 主机）上配置 NFS 服务端，
    并在主机上挂载。如果需要在 Linux 上挂载，可先阅读下面的客户端配置。
    
    需要注意的是，Windows 需要启用 NFS 对应的可选特性，并且不支持 NFSv4。

接下来主要介绍 `exports` 文件的常见配置。以上例子中对应目录被导出到了 `localhost`，但是同样也接受其他格式，例如：

```exports
/var/lib/example 10.0.0.0/25(rw,sync,no_subtree_check,no_root_squash)
/share        *(ro,no_root_squash,async,insecure,no_subtree_check)
/media 192.168.93.2(rw,no_subtree_check) 192.168.93.3(rw,no_subtree_check)
```

分别代表目录导出给了一个 CIDR 网段、所有 IP，以及两个特定的 IP。

!!! warning "使用 `exportfs -a` 检查配置问题"

    `exports` 文件如果编辑不当，可能会导致客户端无法正确挂载，或者带来非预期的安全风险。
    这是在 [RHEL 9 手册](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html-single/configuring_and_using_network_file_services/index#the-etc-exports-configuration-file_exporting-nfs-shares)中举的一个例子：

    ```exports
    /home bob.example.com(rw)
    /home bob.example.com (rw)
    ```

    第一行是正确的配置，而**第二行是错误的配置，实际行为是：bob.example.com 获得只读权限，而其他所有人获得读写权限。**
    这显然是非预期的。我们在本地模仿类似的问题：

    ```exports
    /srv/abcde        localhost (rw,no_root_squash,async,insecure,no_subtree_check)
    ```

    之后执行 `exportfs -a`，可以看到输出了一些警告，提示我们目前的配置存在潜在的问题（一些配置没有显式给出）：

    ```console
    $ sudo exportfs -a
    exportfs: No options for /srv/abcde localhost: suggest localhost(sync) to avoid warning
    exportfs: /etc/exports [2]: Neither 'subtree_check' or 'no_subtree_check' specified for export "localhost:/srv/abcde".
    Assuming default behaviour ('no_subtree_check').
    NOTE: this default has changed since nfs-utils version 1.0.x

    exportfs: No host name given with /srv/abcde (rw,no_root_squash,async,insecure,no_subtree_check), suggest *(rw,no_root_squash,async,insecure,no_subtree_check) to avoid warning
    ```

    可以发现 `localhost` 没有得到正确的配置，而 `*` 对应的配置却是应该给 `localhost` 的。
    在修复（去掉空格）后，再次执行 `exportfs -a`，就不会有警告了：

    ```console
    $ sudo exportfs -a
    $
    ```

在参数部分有一些常见的选项：

- `rw`/`ro`：读写/只读
- `sync`/`async`：同步/异步，后者允许服务器在完成写入操作前就返回，在提升性能的同时可能会导致数据在崩溃/断电时丢失
- `no_subtree_check`：「取消子树检查」——如果确认 NFS 不会暴露在不可信的环境下，或者导出的目录是文件系统的根目录，可以设置这个选项以提升性能
- `no_root_squash`：默认情况下，客户端的 root 会被映射到特定用户（`nobody`），设置 `no_root_squash` 会让客户端的 root 拥有和服务器 root 一样的文件权限；该选项不影响非 root 用户
- `all_squash`：将所有客户端的用户映射到一个特定的用户（`nobody`）
- `secure`/`insecure`：默认情况下，NFS 服务端只接受客户端使用 1024 以下的端口访问，设置 `insecure` 会放宽这个限制

!!! tip "1024 端口，与 root"

    在传统上，类 Unix 操作系统中只有 root 用户才能使用 1024 以下的端口。因此在很久以前，程序可以假设来自 1024 以下的端口的请求/服务是 root 用户发出/授权的。
    在 NFS 的情况下，这意味着只有 root 才能访问 NFS 服务，没有 root 权限的用户不能够假冒自己为 NFS 客户端，从而以假的用户权限读写数据。
    这在很久以前的内部网络中的服务器场景是有意义的。

    目前 Linux 仍然保留了这个机制，但是程序不应该仅仅依赖于这个机制来保证安全性。

??? note "关于「子树检查」的解释"

    NFS 服务器与客户端之间使用「文件句柄」（file handle）来标识文件。
    文件句柄的内容含义由服务器决定。
    在 Linux 内核态 NFS 的实现中，文件句柄的结构体为 [`knfsd_fh`](https://elixir.bootlin.com/linux/v6.8/source/fs/nfsd/nfsfh.h#L47)，如下所示：

    ```c
    struct knfsd_fh {
        unsigned int    fh_size;    /*
                                     * Points to the current size while
                                     * building a new file handle.
                                     */
        union {
            char        fh_raw[NFS4_FHSIZE];
            struct {
                u8      fh_version;     /* == 1 */
                u8      fh_auth_type;   /* deprecated */
                u8      fh_fsid_type;
                u8      fh_fileid_type;
                u32     fh_fsid[]; /* flexible-array member */
            };
        };
    };
    ```

    例如抓包得到一个由内核态 NFSv4 服务器返回的文件句柄（十六进制）是这样的：

    ```
    01 00 07 01
    b0 18 06 00 00 00 00 00 6c f8 f6 54 9a 14 47 03
    be 4e c5 a0 59 c9 f7 f8 16 2e 06 00 a5 70 74 83
    ```

    与 union 中的结构体对应。根据 fsid 和 fileid type 可以推断 `fh_fsid[]` 的前 24 个字节存储文件系统信息，后 8 个字节存储文件信息。
    inode 编号后是 generation number，用于检测文件是否被修改。
    
    该文件 inode 编号为 405014，即 0x62e16，可以发现以小端序的形式存储在最后 8 个字节。
    同时，被导出目录的 inode 编号为 399536，即 0x618b0；所处的文件系统的 UUID 为 6cf8f654-9a14-4703-be4e-c5a059c9f7f8，
    这些信息存储在前 24 个字节中。

    于是如果 NFS 共享（导出）的目录不是文件系统的根目录，那么内核态服务器就需要判断客户端请求的文件句柄是否真的在共享的目录下。
    这一项检查需要从文件的 inode 信息不停向上查找来确认文件确实在共享的目录中。
    而 `no_subtree_check` 会跳过这样的检查。

    部分可能对决策有帮助的信息——在例如有大量文件重命名的场合，可能不得不关闭子树检查：

    - [Making Filesystems Exportable -- The Linux Kernel  documentation](https://docs.kernel.org/filesystems/nfs/exporting.html?highlight=export_op_nosubtreechk)
    - [Network File System (NFS) | Ubuntu](https://ubuntu.com/server/docs/service-nfs)
    - [Linux NFS faq](https://nfs.sourceforge.net/#faq_c7)

    以及相关的 CVE 与修复的 commit message：

    [CVE-2021-3178](https://lists.debian.org/debian-lts-announce/2021/03/msg00010.html):

    ```
    吴异 reported an information leak in the NFSv3 server.  When only
    a subdirectory of a filesystem volume is exported, an NFS client
    listing the exported directory would obtain a file handle to the
    parent directory, allowing it to access files that were not meant
    to be exported.

    Even after this update, it is still possible for NFSv3 clients to
    guess valid file handles and access files outside an exported
    subdirectory, unless the "subtree_check" export option is enabled.
    It is recommended that you do not use that option but only export
    whole filesystem volumes.
    ```

    [nfsd4: readdirplus shouldn't return parent of export](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=51b2ee7d006a736a9126e8111d1f24e4fd0afaa6):

    ```
    nfsd4: readdirplus shouldn't return parent of export

    If you export a subdirectory of a filesystem, a READDIRPLUS on the root
    of that export will return the filehandle of the parent with the ".."
    entry.

    The filehandle is optional, so let's just not return the filehandle for
    ".." if we're at the root of an export.

    Note that once the client learns one filehandle outside of the export,
    they can trivially access the rest of the export using further lookups.

    However, it is also not very difficult to guess filehandles outside of
    the export.  So exporting a subdirectory of a filesystem should
    considered equivalent to providing access to the entire filesystem.  To
    avoid confusion, we recommend only exporting entire filesystems.

    Reported-by: Youjipeng <wangzhibei1999@gmail.com>
    Signed-off-by: J. Bruce Fields <bfields@redhat.com>
    Cc: stable@vger.kernel.org
    Signed-off-by: Chuck Lever <chuck.lever@oracle.com>
    ```

??? note "RDMA 支持（服务端）"

    NFS 支持 RDMA 协议，在配置了专用 RDMA 卡的情况下，可以在数据中心内部网络的场景下减小网络延迟，提升性能。
    （如果希望本地测试，可以安装 `rdma-core` 包，其包含了 Soft-RoCE 实现，即软件模拟的 RDMA；
    `rdmacm-utils` 包包含了 `rping` 工具用于测试 RDMA 连接。
    如何使用 `rdma link` 命令创建软件模拟的 RDMA 设备请自行搜索）

    在系统能够识别到 RDMA 设备的情况下：

    ```console
    $ rdma link
    link rxe0/1 state ACTIVE physical_state LINK_UP netdev enp1s0
    ```

    编辑 `/etc/nfs/nfs.conf` 文件，在 `[nfsd]` 一段进行 RDMA 的配置：

    ```ini
    [nfsd]
    # ...
    rdma=y
    rdma-port=20049
    ```

    之后重启 `nfs-server` 服务即可。可以在 `/proc/fs/nfsd/portlist` 确认 NFS 服务器监听的端口情况：

    ```console
    $ cat /proc/fs/nfsd/portlist
    rdma 20049
    rdma 20049
    tcp 2049
    tcp 2049
    ```

### 客户端配置

挂载 NFS（表面上）是一件很简单的事情：

```console
$ sudo mount -t nfs localhost:/srv/abcde /mnt/nfs
$ mount | grep nfs
nfsd on /proc/fs/nfsd type nfsd (rw,relatime)
localhost:/srv/abcde on /mnt/nfs type nfs4 (rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,namlen=255,hard,proto=tcp6,timeo=600,retrans=2,sec=sys,clientaddr=::1,local_lock=none,addr=::1)
```

有的时候需要添加参数，例如下面这个使用 NFS over RDMA 的例子中，需要指定协议与端口号：

```console
$ sudo mount -t nfs -o proto=rdma,port=20049 192.168.122.47:/srv/abcde /mnt/nfs
$ mount | grep nfs
192.168.122.47:/srv/abcde on /mnt/nfs type nfs4 (rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,namlen=255,hard,proto=rdma,port=20049,timeo=600,retrans=2,sec=sys,clientaddr=192.168.122.47,local_lock=none,addr=192.168.122.47)
```

但是最常见的问题，还是 `hard` 与 `soft`（或者 Linux 5.6 之后新增的 `softerr`）的选择。
NFS 客户端在每次重试之前会等待 `timeo` / 10（默认 600 / 10 = 60）秒。
在 `hard` 模式下，如果服务器没有响应，那么客户端会永远重试下去，直到服务器恢复；
而在 `soft` 模式下，在经过 `retrans`（默认为 2）次重试后，客户端会放弃，并向应用程序返回错误。
（但是应用能不能正确处理错误，就是另外一回事了）

默认情况下，出于保护数据完整性的考虑，`mount` 会选择 `hard` 模式。
但是如果网络或者 NFS 服务器的稳定性不够的话，结果可能会比较棘手。
让我们**在虚拟机里试一试（请先保存全部数据！）**：

```console
$ sudo mount -t nfs localhost:/srv/abcde /mnt/nfs
$ sudo systemctl stop nfs-server
$ echo "test" > /mnt/nfs/testfile
^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C^C
```

可以发现 `echo` 被阻塞住了，并且发送 SIGINT 无法正常终止。此时的 bash 进程处于 D 状态，栈如下：

```console
$ sudo cat /proc/4971/stack
[<0>] rpc_wait_bit_killable+0xd/0x60 [sunrpc]
[<0>] nfs4_run_open_task+0x152/0x1e0 [nfsv4]
[<0>] nfs4_do_open+0x25b/0xc20 [nfsv4]
[<0>] nfs4_atomic_open+0xf4/0x100 [nfsv4]
[<0>] nfs_atomic_open+0x215/0x6a0 [nfs]
[<0>] path_openat+0x6d7/0x1260
[<0>] do_filp_open+0xaf/0x160
[<0>] do_sys_openat2+0xaf/0x170
[<0>] __x64_sys_openat+0x6a/0xa0
[<0>] do_syscall_64+0x58/0xc0
[<0>] entry_SYSCALL_64_after_hwframe+0x64/0xce
```

因为栈顶是 killable 的，发送 SIGKILL 仍可正常终止进程：

```console
$ kill -9 4971
$ sudo cat /proc/4971/stack
cat: /proc/4971/stack: No such file or directory
```

如果没有进程在使用的话，也能……正常（？）umount：

```console
$ sudo umount /mnt/nfs
^C
$ mount | grep nfs
nfsd on /proc/fs/nfsd type nfsd (rw,relatime)
```

但是如果有的话，umount 会拒绝，即使加上 `-f` 也不会操作：

```console
$ sudo umount /mnt/nfs
umount.nfs4: /mnt/nfs: target is busy
$ sudo umount -f /mnt/nfs
umount.nfs4: /mnt/nfs: target is busy
```

即使看似有办法能从 hard 中全身而退（杀掉全部访问进程再 umount），但是仍然需要小心：
一个例子是 `home` 目录在 NFS 上，而用户登录时又需要读取 `~/.bashrc` 等文件。
如果此时 NFS 服务器不可用，那么所有用户登录都会卡住，如果不能登录 root 的话，就只有强制重启一种选择了。

如果能够登录，但是发现没有办法杀光所有访问 NFS 的进程（可能在不停出现新的），一种妥协的方法是 lazy unmount：

```console
$ sudo umount -l /mnt/nfs
$
```

此时 `/mnt/nfs` 不会暴露为挂载点，但是已有的进程如果持有挂载点内的文件描述符，仍然可以继续访问。
此时的问题挂载点事实上还是没有被卸载，只是之后新的访问不会再涉及 NFS 了。
在用这种方式「解决」问题之后，建议尽快重启服务器。

此外，`intr` 参数在现在能碰到的内核（2.6.25+）中，没有任何意义，因此没有必要设置。

## iSCSI
