---
icon: material/account
---

# 用户账户系统 {#accounts}

## Unix 用户 {#unix-users}

Linux 采用 Unix 用户系统，即通过一个数字 ID 来标识用户，称为 UID。
UID 0 通常称为 root 用户，具有操作系统的最高管理权限，而非零 UID 的用户不具有特殊的权限。

类似地，用户组也通过数字 ID 来标识，称为 GID。
用户组的 GID 0 通常称为 root 组，但一般没有特殊的权限。

在 Debian 及其衍生发行版中，UID 和 GID 的范围 0-999 是系统用户和组，范围 1000-59999 是普通用户和组，范围 60000-65533 是动态分配的用户和组，65534 为 `nobody` 用户和 `nogroup` 组。
其中 UID/GID 范围 0-100 由 Debian 保留分配，确保在所有 Debian 系统中都保持一致，例如 `sudo`, `www-data` 和 `users` 组的 GID 分别固定为 27, 33 和 100。

### 添加与删除用户 {#adduser}

Debian 提供了用户友好的 `adduser` 和 `deluser` 命令来添加和删除用户，由软件包 `adduser` 提供，即：

```shell
apt install adduser
```

`adduser` 命令会创建一个新的用户，为其创建一个主目录，并指导管理员（运行 `adduser` 命令的人）为新用户设置密码和备注信息。

adduser 的一些默认行为可以通过 `/etc/adduser.conf` 文件进行配置，例如指定系统用户和普通用户的 UID 范围，以及默认 shell（`DSHELL`）等。

!!! question "`useradd` 呢？"

    尽管在其他的发行版中更加常见，但 Debian 认为 [`useradd(8)`][useradd.8] 是一个低层次的命令，因此不建议管理员直接使用，并且 `adduser.conf` 文件中的配置也不会对 `useradd` 命令生效。

    类似地，Debian 也不推荐直接使用 [`userdel(8)`][userdel.8] 命令来删除用户，并提供了 [`deluser(8)`][deluser.8] 命令。

### PAM

## LDAP
