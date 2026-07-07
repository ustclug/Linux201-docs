---
icon: material/account-supervisor
---

# 用户账户系统 {#accounts}

!!! note "主要作者"

    [@iBug][iBug]、[@taoky][taoky]

!!! warning "本文编写中"

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

adduser 的一些默认行为可以通过 [`/etc/adduser.conf`][adduser.conf.5] 文件进行配置，例如指定系统用户和普通用户的 UID 范围，以及默认 shell（`DSHELL`）等。
使用 adduser 命令的一个例子如下：

```console
# adduser test
info: Adding user `test' ...
info: Selecting UID/GID from range 1000 to 59999 ...
info: Adding new group `test' (1145) ...
info: Adding new user `test' (1145) with group `test (1145)' ...
info: Creating home directory `/home/test' ...
info: Copying files from `/etc/skel' ...
New password:
Retype new password:
passwd: password updated successfully
Changing the user information for test
Enter the new value, or press ENTER for the default
        Full Name []: test
        Room Number []:
        Work Phone []:
        Home Phone []:
        Other []:
Is the information correct? [Y/n]
info: Adding new user `test' to supplemental / extra groups `users' ...
info: Adding user `test' to group `users' ...
```

从输出中可以看到，adduser 命令完成了以下几项工作：

- 创建了一个新的用户 `test`，并为其分配了一个 UID 和 GID（1145）。

    注意 Unix 用户和组是通过数字 ID 来标识的，因此“创建”用户的全部内容就是在 `/etc/passwd` 文件中添加一行信息，将用户名和 UID 关联起来，并附带家目录和登录 shell 等额外信息。
    即使一个“用户”不存在于 `/etc/passwd` 文件中，对应的 UID 仍然是有效的。

- 创建了一个新的组 `test`，并为其分配了一个数值相同的 GID。

    这个默认行为可以通过在 `adduser.conf` 文件中设置 `USERGROUPS=no` 来禁用，此后添加的用户将不再创建同名的组，而是默认属于 `users` 组。

- 为 `test` 用户创建了家目录 `/home/test`，并从 `/etc/skel` 目录初始化这个新的家目录。

    `/etc/skel`（名称取自 **skel**eton）目录包含了一些默认的配置文件，例如 `.bashrc` 和 `.profile` 等。
    管理员也可以按需添加其他文件，注意 `/etc/skel` 只会在创建新用户时复制一次，不会影响现有用户的家目录。

- 提示管理员设置用户的密码和备注信息（gecos）。
- 将 `test` 用户添加到 `users` 组中。

    注意这不是 adduser 的默认行为，而是本实例的实验环境在 `adduser.conf` 中已经设置了 `ADD_EXTRA_GROUPS=1`（或者添加 `--add-extra-groups` 参数）。

!!! question "`useradd` 呢？"

    尽管在其他的发行版中更加常见，但 Debian 认为 [`useradd(8)`][useradd.8] 是一个低层次的命令，因此不建议管理员直接使用，并且 `adduser.conf` 文件中的配置也不会对 `useradd` 命令生效。

    类似地，Debian 也不推荐直接使用 [`userdel(8)`][userdel.8] 命令来删除用户，并提供了 [`deluser(8)`][deluser.8] 命令。

### PAM

## LDAP

LDAP 即轻量级目录访问协议（Lightweight Directory Access Protocol），是一种用于访问和维护分布式目录信息服务的开放标准协议。

在 Linux 中，LDAP 通常用于集中管理用户和组信息，分为服务端和客户端两部分。服务端负责存储用户和组信息，客户端则按需查询这些信息，其中的数据交换格式为 LDIF（LDAP Data Interchange Format）。LDAP 一般用于多名用户以统一的身份访问多台服务器或服务。

常用的 LDAP 服务器有 OpenLDAP 和 [389 Directory Server](https://www.port389.org/) 等。在 Debian 中，OpenLDAP 的软件名为 `slapd`。由于 LDAP 的复杂性，可以使用成熟的客户端查看 LDAP 的信息，以便理解与修改数据，例如 [Apache Directory Studio](https://directory.apache.org/studio/)。

!!! comment "@taoky: LDAP 的都市传说"

    根据来自 [TUNA](https://tuna.moe/) 的都市传说：折腾过 LDAP 的人，都会在某种意义上延毕。因此这一部分是由已经毕业的同学编写的（大概吧）。

### 基础概念 {#ldap-basic}

LDAP 的数据组成一颗树，被称为 Directory Information Tree（DIT）。树中每个项（Entry）都有一个唯一表示它的名字，被称为 Distinguished Name（识别名，**dn**）。例如一个用户项的 `dn` 可能为如下：

```txt
cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org
```

其中 **cn** 为 Common Name（通用名称），**ou** 为 Organization Unit（组织单元），**dc** 为 Domain Component（域组件）。其对应的相对识别名（Relative Distinguished Name，RDN）则是 `dn` 最左边的 `cn=Takamatsu Tomori`。

一般来讲，域组件习惯上按照 DNS 域名的顺序来写。而上述用户项所在的 LDAP 树可能长这样：

```txt
dc=bangdream,dc=example,dc=org
    ou=people
        cn=Toyama Kasumi
        cn=Ichigaya Arisa
        ...
        cn=Takamatsu Tomori
        ...
    ou=groups
        cn=Poppin'Party
        cn=Roselia
        cn=Hello\, Happy World!
        ...
        cn=MyGO!!!!!
        ...
    ou=sudoers
        cn=SPACE
        cn=CiRCLE
        cn=RiNG
        ...
```

!!! note "字符转义"

    可以看到上述 LDAP 树的 `ou=groups` 里面有一些项的 `cn` 有特殊的字符。`cn` 里面确实可以存储任意 UTF-8 字符串，但是根据 [RFC 4514](https://datatracker.ietf.org/doc/html/rfc4514#section-2.4) 的要求，有一些字符需要转义，例如 `cn=Hello\, Happy World!` 中的 `,` 就需要在前面添加 `\`，避免在写成 `dn` 的时候产生混淆：

    ```txt
    cn=Hello\, Happy World!,ou=groups,dc=bangdream,dc=example,dc=org
    ```

    因此尽管可以，但是不建议在 `cn` 中使用需要转义的字符，避免麻烦。

项是属性（Attribute）的集合。属性是一对 key（被称为 Attribute Type）和 value。例如上面 `cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org` 的属性可能是这样：

```txt
dn: cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: posixAccount
objectClass: shadowAccount
objectClass: top
cn: Takamatsu Tomori
gidNumber: 2008
homeDirectory: /home/tomori
sn: Takamatsu
uid: tomori
uidNumber: 2036
gecos: Takamatsu Tomori
givenName: Tomori
loginShell: /bin/fish
shadowLastChange: 12345
userPassword: {SSHA}(redacted)
createTimestamp: 20220429000000Z
modifyTimestamp: 20260112000000Z
```

属性不是想怎么填就可以怎么填的，可以使用的属性和 `objectClass` 的定义受到 LDAP schema 的限制。`objectClass` 规定了当前项中必选或可选哪些属性，例如 `inetOrgPerson` 要求当前项必须有 `cn` 或 `commonName`、`objectClass` 属性和 `sn` 或 `surname` 属性，可选诸如 `carLicense`、`photo`、`manager` 等属性。属性的语法以及匹配规则也由 schema 限制。

!!! note "`objectClass` 的继承"

    可以注意到上面有一个特殊的 `objectClass`：`top`。这个类是所有其他 `objectClass` 的根。`cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org` 的例子里出现的 `objectClass` 的继承关系如下：

    ```txt
    top
        person
            organizationalPerson
                inetOrgPerson
        posixAccount
        shadowAccount
    ```

    尽管只要写 `inetOrgPerson`，就包含了 `organizationalPerson`、`person` 和 `top` 的约束关系，但是在实践中在这个继承链条上的 `objectClass` 很多时候仍然是完整写出的。

此外有一些特殊的属性，不能被用户设置，只能由服务器生成，例如 `createTimestamp` 和 `modifyTimestamp`。这些被称为操作属性（Operational Attribute）。

### 服务端配置 {#ldap-server}

以下以 OpenLDAP 为例讲解相关配置。(TODO)
