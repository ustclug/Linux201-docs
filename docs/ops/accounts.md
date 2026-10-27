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

!!! question "`useradd` 呢？" {#no-useradd}

    尽管在其他的发行版中更加常见，但 Debian 认为 [`useradd(8)`][useradd.8] 是一个低层次的命令，因此不建议管理员直接使用，并且 `adduser.conf` 文件中的配置也不会对 `useradd` 命令生效。

    类似地，Debian 也不推荐直接使用 [`userdel(8)`][userdel.8] 命令来删除用户，并提供了 [`deluser(8)`][deluser.8] 命令。

### PAM

(TODO)

## LDAP

LDAP 即轻量级目录访问协议（Lightweight Directory Access Protocol），是一种用于访问和维护分布式目录信息服务的开放标准协议。

在 Linux 中，LDAP 通常用于集中管理用户和组信息，分为服务端和客户端两部分。服务端负责存储用户和组信息，客户端则按需查询这些信息，其中的数据交换格式为 LDIF（LDAP Data Interchange Format）。LDAP 一般用于多名用户以统一的身份访问多台服务器或服务。

常用的 LDAP 服务器有 OpenLDAP 和 [389 Directory Server](https://www.port389.org/) 等。在 Debian 中，OpenLDAP 的软件名为 `slapd`。由于 LDAP 的复杂性，可以使用成熟的客户端查看 LDAP 的信息，以便理解与修改数据，例如 [Apache Directory Studio](https://directory.apache.org/studio/)。

!!! comment "@taoky: LDAP 的都市传说" {#ldap-urban-legends}

    根据来自 [TUNA](https://tuna.moe/) 的都市传说：折腾过 LDAP 的人，都会在某种意义上延毕。因此这一部分是由已经毕业的同学编写的（大概吧）。

### 基础概念 {#ldap-basic}

LDAP 的数据组成一颗树，被称为 Directory Information Tree（DIT）。树中每个项（Entry）都有一个**唯一**表示它的名字，被称为 Distinguished Name（识别名，**dn**）。例如一个用户项的 DN 可能为如下：

```txt
cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org
```

其中 **cn** 为 Common Name（通用名称），**ou** 为 Organization Unit（组织单元），**dc** 为 Domain Component（域组件）。其对应的相对识别名（Relative Distinguished Name，RDN）则是 `dn` 最左边的 `cn=Takamatsu Tomori`。RDN 不一定必须是 `cn`，只要在下面所说的属性里面即可，所以这个用户项的 DN 也可以设置为：

```txt
uid=tomori,ou=people,dc=bangdream,dc=example,dc=org
```

此外，树中的项也被称为 DSE（Directory Service Entry）。RootDSE 存储了 LDAP 服务器本身的信息。一个 LDAP 服务器可以有多个 `namingContexts`，每个 `namingContexts` 对应一颗目录树。每颗目录树的树根也被称为 Base DN。

一般来讲，域组件习惯上按照 DNS 域名的顺序来写。而上述用户项所在的目录树可能长这样：

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

!!! note "字符转义" {#ldap-escape}

    可以看到上述 LDAP 树的 `ou=groups` 里面有一些项的 `cn` 有特殊的字符。`cn` 里面确实可以存储任意 UTF-8 字符串，但是根据 [RFC 4514](https://datatracker.ietf.org/doc/html/rfc4514#section-2.4) 的要求，有一些字符需要转义，例如 `Hello, Happy World!` 中的 `,` 就需要在前面添加 `\`，避免在写成 `dn` 的时候产生混淆：

    ```txt
    cn=Hello\, Happy World!,ou=groups,dc=bangdream,dc=example,dc=org
    ```

    因此尽管可以，但是不建议在 `cn` 中使用需要转义的字符，避免麻烦。

!!! note "为什么不每个 group 一个 ou？" {#group-ou}

    对于上面这个例子，以下的目录树似乎会更符合直觉一些：

    ```txt
    dc=bangdream,dc=example,dc=org
        ou=Poppin'Party
            cn=Toyama Kasumi
            cn=Ichigaya Arisa
            ...
        ...
    ```

    但是在更多的例子中，一个用户可能会属于多个组（例如同时隶属于可以登录 A 机器的 group，和可以登录 B 机器的 group），这种 ou 的模型就无法表示这种情况。并且要把用户从一个组搬到另一个组也会麻烦很多——用户的 DN 会发生变化（相当于变化了关系型数据库中的主键），即使 LDAP 实现能够在内部处理好，外部程序记录的 DN 也要随之更改。

项是属性（Attribute）的集合。属性是一对 key（被称为 Attribute Type）和 value。例如上面 `cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org` 的属性以 LDIF 格式表示可能是这样：

```ldif
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

!!! note "`objectClass` 的继承" {#objectclass-inheritance}

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

    此外，`objectClass` 分为三大类：STRUCTURAL（结构类）、AUXILIARY（辅助类）和 ABSTRACT（抽象类）。结构类确定一个 entry 的基本类型，辅助类给已有的 entry 添加新的功能，抽象类则给其他类提供基础属性（比如说 `top`）。对结构类来说，两个结构类要在同一条继承链条上面，才能够组合在一起。

!!! note "RFC 2307" {#rfc2307}

    另外还可以注意到样例中的一些属性和类 Unix 系统中用户的信息是对应的，比如说 `uid`、`homeDirectory`、`loginShell` 等等。这些是 `posixAccount` 这个 `objectClass` 定义的（用户组对应的则是 `posixGroup`）。其对应的标准是 [RFC 2307](https://datatracker.ietf.org/doc/html/rfc2307)，用来让 LDAP 替代早期（1985）由 Sun 公司开发的 NIS 来存储 Unix 上的用户信息。

    在一些场合下还可以看到 [RFC 2307bis](https://datatracker.ietf.org/doc/html/draft-howard-rfc2307bis-01) 草稿标准，尽管不是正式 RFC 标准，2307bis 也仍然被广泛应用。相比 RFC 2307，其最大的区别是对用户组的处理。RFC 2307 的用户组可能长这样：

    ```ldif
    dn: cn=CRYCHIC,ou=groups,dc=bangdream,dc=example,dc=org
    objectClass: top
    objectClass: posixGroup
    cn: CRYCHIC
    gidNumber: 2101
    memberUid: sakiko
    memberUid: tomori
    memberUid: soyo
    memberUid: mutsumi
    memberUid: taki
    ```

    而 2307bis 的用户组：

    ```ldif
    dn: cn=CRYCHIC,ou=groups,dc=bangdream,dc=example,dc=org
    objectClass: top
    objectClass: groupOfNames
    objectClass: posixGroup
    cn: CRYCHIC
    gidNumber: 2101
    member: cn=Togawa Sakiko,ou=people,dc=bangdream,dc=example,dc=org
    member: cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org
    member: cn=Nagasaki Soyo,ou=people,dc=bangdream,dc=example,dc=org
    member: cn=Wakaba Mutsumi,ou=people,dc=bangdream,dc=example,dc=org
    member: cn=Shina Taki,ou=people,dc=bangdream,dc=example,dc=org
    ```

    这里，`posixGroup` 因为从 RFC 2307 的结构类变成了辅助类，因此可以和 `groupOfNames` 组合起来，由 `groupOfNames` 提供 `member` 属性，包含对应成员完整的 DN。这样做有一些好处，比如说如果用户的 `uid` 需要变化时，组的信息不需要修改（因为使用了 DN 来引用），以及删除、重命名用户 entry 的时候，根据服务器的配置，LDAP 服务器实现可能能够帮助自动维护好相关的配置。

此外有一些特殊的属性，不能被用户设置，只能由服务器生成，例如 `createTimestamp` 和 `modifyTimestamp`。这些被称为操作属性（Operational Attribute）。

LDIF 格式不仅可以表示一个项，也可以表示数据的修改，例如删除或者修改一些项：

```ldif
dn: cn=CRYCHIC,ou=groups,dc=bangdream,dc=example,dc=org
changetype: delete

# 对不同对象的操作之间用空行隔开
dn: cn=Viola,ou=people,dc=bangdream,dc=example,dc=org
changetype: delete
```

```ldif
dn: cn=Togawa Sakiko,ou=people,dc=bangdream,dc=example,dc=org
add: displayName
displayName: Oblivionis
-
# 对同一对象的修改操作用 - 隔开
replace: postalAddress
postalAddress: 114-0001
```

用户如果要访问 LDAP 数据的话需要登录，这个过程被称为 Bind。最常见的 Simple Bind 需要用户提供自己的 DN 和密码，类似这样：

```sh
ldapwhoami -x -H ldap://bangdream.example.org:389 \
  -D "cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org" \
  -w "<redacted>"
```

注意在 OpenLDAP 提供的 CLI 工具中，Simple Bind 需要使用 `-x` 参数，否则会变成使用 SASL Bind。SASL 是一种能够应用于某些网络协议（例如 LDAP、SMTP、IMAP 等）的认证框架：服务端需要在对应网络协议的标准内提供自己支持的 SASL 框架下的认证机制，客户端选择一种机制，提供对应的认证数据，由服务器再验证。以下不涉及相关的高级鉴权方式。

有一些反直觉的地方是，如果你的 DN 像上面这样，那么不能使用（看起来更合理的）uid 来登录，因为 `uid=tomori,...` 不是你的 DN。因此应用常用的一种形式是：如果 LDAP 服务不允许匿名搜索，那么就需要先用提前配置好的专门用于搜索的账号 bind，根据用户的条件（例如 `uid`）找到实际的 DN，再拿这个 DN 加上用户输入的密码再来 bind。

LDAP 的搜索也有自己一套独特的 filter 语法，格式是 `(属性名 运算符 属性值)`，而组合条件（`&`、`|`、`!`）使用前缀的形式，例如：

- 所有 `inetOrgPerson` 用户：`(objectClass=inetOrgPerson)`
- 寻找 UID 为 tomori 的人员：`(uid=tomori)`
- 寻找多个用户（或）：`(|(uid=anon)(uid=soyo))`
- 寻找设置了 `mail` 的项：`(mail=*)`
- 寻找 cn 开头（姓）是 Hikawa 的项：`(cn=Hikawa *)`，或者更加贴切的 `(sn=Hikawa)`
- 寻找 UID 数字大于等于 1000，小于等于 9999 的项：`(&(uidNumber>=1000)(uidNumber<=9999))`

使用 `ldapsearch` 可以进行查询：

```sh
ldapsearch -x -H ldap://bangdream.example.org:389 \
  -D "cn=Takamatsu Tomori,ou=people,dc=bangdream,dc=example,dc=org" \
  -w "<redacted>" \
  -b "dc=bangdream,dc=example,dc=org" \
  "(uid=tomori)"
```

### 服务端配置 {#ldap-server}

#### 基本环境 {#slapd-basic-env}

以下以 OpenLDAP 为例讲解相关配置。在安装 `slapd` 包的过程中会要求设置管理员密码。配置完成后，LDAP 数据库存储在 `/var/lib/ldap`。

!!! note "mdb 格式" {#mdb-format}

    OpenLDAP 会保存两个 mdb 文件：`data.mdb` 和 `lock.mdb`，分别存储实际的数据，以及锁管理相关的数据。这个格式对应的是 [LMDB](https://www.symas.com/mdb)，是为 OpenLDAP 的需求量身定制的嵌入式键值数据库。

    尽管 `lmdb-utils` 包提供了 `mdb_stat`、`mdb_dump` 等工具可以读取、导出 mdb 数据库的内容，但是以此阅读 OpenLDAP 实际存储的内容仍然是难以理解的。如果需要导出 mdb 到可读的 LDIF 格式，需要使用 `slapcat` 工具：

    ```sh title="读取配置（如果 LDAP 配置存储在 cn=config 中）"
    slapcat -n 0
    ```

    ```sh title="读取第一个数据库"
    slapcat -n 1
    ```

安装 `slapd` 后对应的服务为 `slapd.service`，默认配置下监听未加密的 LDAP 协议端口 TCP 389。如果后续配置了 LDAPS，则默认是 TCP 636 端口。

默认情况下，`slapd` 安装时会尝试根据 `hostname -d` 的输出配置 base DN，如果输出为空，那么就会变成 `dc=nodomain`。在几乎所有的情况下，都不是我们想要的，可以用下面的命令从 rootDSE 获取 `namingContexts` 验证：

```console
$ ldapsearch -x -H ldapi:/// -b "" -s base namingContexts
# extended LDIF
#
# LDAPv3
# base <> with scope baseObject
# filter: (objectclass=*)
# requesting: namingContexts
#

#
dn:
namingContexts: dc=nodomain

# search result
search: 2
result: 0 Success

# numResponses: 2
# numEntries: 1
```

这里表明当前环境的 base DN 就是 `dc=nodomain`。如果不满意，使用 `dpkg-reconfigure slapd` 配置即可。后文的 `ldapsearch` 输出会省略一部分注释以方便阅读。

!!! note "ldapi?" {#ldapi}

    可以注意到，我们这里连接本地的 OpenLDAP 服务器时，使用的是 `ldapi:///`（LDAP over IPC）。对 OpenLDAP，其实际访问的是 `/var/run/slapd/ldapi`。对 Simple Bind，如果没有提供任何凭据，那么相当于匿名访问（即使操作者是 root 也是这样）：

    ```console
    $ ldapwhoami -x -H ldapi:///
    anonymous
    $ sudo ldapwhoami -x -H ldapi:///
    anonymous
    ```

    如果使用 SASL 的话，在选择 `EXTERNAL` 认证机制（复用已经完成的身份认证，这里即 Unix socket 自动提供的对端凭据）的情况下，OpenLDAP 会根据访问者的本地用户信息构造出一个身份：

    ```console
    $ ldapwhoami -H ldapi:/// -Y EXTERNAL  # -Y EXTERNAL 可以省略
    SASL/EXTERNAL authentication started
    SASL username: gidNumber=1000+uidNumber=1000,cn=peercred,cn=external,cn=auth
    SASL SSF: 0
    dn:gidNumber=1000+uidNumber=1000,cn=peercred,cn=external,cn=auth
    $ sudo ldapwhoami -H ldapi:/// -Y EXTERNAL
    SASL/EXTERNAL authentication started
    SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
    SASL SSF: 0
    dn:gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
    ```

    在默认配置下，root 用户有全部权限。

#### 查看配置 {#slapd-cn-config}

OpenLDAP 有两种配置方式：使用 `/etc/ldap/slapd.conf` 配置文件，以及 `cn=config` 配置数据库。基于 `slapd.conf` 配置文件的方式目前**已经弃用**（下文也不会再做介绍），对比较新的 LDAP 服务器来说，使用的都是 `cn=config` 的方式，在 LDAP 数据库中动态存储配置。相比配置文件，这样做在修改配置时，不需要重启 OpenLDAP 服务器。`cn=config` 与实际存储用户信息的目录树（Base DN）是两套由同一个 slapd 管理的不同的数据库。

可以使用 `ldapsearch` 查看（大部分输出省略）：

```console
$ sudo ldapsearch -H ldapi:/// -Y EXTERNAL -b cn=config
# config
dn: cn=config
...
# module{0}, config
dn: cn=module{0},cn=config
...
# schema, config
dn: cn=schema,cn=config
...
# {-1}frontend, config
dn: olcDatabase={-1}frontend,cn=config
...
# {0}config, config
dn: olcDatabase={0}config,cn=config
...
# {1}mdb, config
dn: olcDatabase={1}mdb,cn=config
...
# search result
search: 2
result: 0 Success
```

根据对应的完整输出，`cn=config` 的结构如下。本文不会详尽介绍所有配置项的细节。

```txt
cn=config
    cn=module{0},cn=config
    cn=schema,cn=config
        cn={0}core,cn=schema,cn=config
        cn={1}cosine,cn=schema,cn=config
        cn={2}nis,cn=schema,cn=config
        cn={3}inetorgperson,cn=schema,cn=config
    olcDatabase={-1}frontend,cn=config
    olcDatabase={0}config,cn=config
    olcDatabase={1}mdb,cn=config
```

!!! note "`{-1}frontend` 是什么数据库？" {#frontend-database}

    可以发现，除了存储用户数据的数据库（`{1}mdb`）和 `cn=config` 配置数据库（`{0}config`）以外，还有一个 `{-1}frontend` 数据库。这个「数据库」并非实际存在，对应的配置只用来配置对其他所有数据库的默认行为。例如：

    ```console
    $ sudo ldapsearch -H ldapi:/// -Y EXTERNAL -b 'olcDatabase={-1}frontend,cn=config'
    （省略）
    # {-1}frontend, config
    dn: olcDatabase={-1}frontend,cn=config
    objectClass: olcDatabaseConfig
    objectClass: olcFrontendConfig
    olcDatabase: {-1}frontend
    olcAccess: {0}to * by dn.exact=gidNumber=0+uidNumber=0,cn=peercred,cn=external
     ,cn=auth manage by * break
    olcAccess: {1}to dn.exact="" by * read
    olcAccess: {2}to dn.base="cn=Subschema" by * read
    olcSizeLimit: 500
    （省略）
    ```

    这里通过 `olcAccess` 指定的 ACL 配置，就允许了通过 `ldapi:///` 连接的 root 用户管理数据库，并允许所有用户（包括匿名用户）读取 rootDSE 和 schema。

!!! tip "OpenLDAP 工具的自动折行" {#openldap-ldif-line-folding}

    上面的例子中，可以发现 `ldapsearch` 在输出时，过长的行会折行处理：

    ```ldif
    olcAccess: {0}to * by dn.exact=gidNumber=0+uidNumber=0,cn=peercred,cn=external
     ,cn=auth manage by * break
    ```

    LDIF 允许折行：对太长的一行，可以拆成多行，后面接续的行开头需要是一个空格。解析的时候会把这个开头的空格去掉，再接到上面的内容。对 OpenLDAP 的 CLI 工具，可以添加 `-o ldif-wrap=no` 关闭其默认的折行行为。

#### 用户操作 {#slapd-user-op}

在起始状态下，base DN 里面是没有内容的：

```console
$ sudo ldapsearch -H ldapi:/// -Y EXTERNAL -b dc=bangdream,dc=example,dc=org
# bangdream.example.org
dn: dc=bangdream,dc=example,dc=org
objectClass: top
objectClass: dcObject
objectClass: organization
o: bangdream
dc: bangdream

# search result
search: 2
result: 0 Success
```

我们至少需要先添加 `ou=people` 和 `ou=groups`（也可以用自己喜欢的名字表示用户和组的 ou）。就像对关系型数据库需要写 SQL 来创建数据库一样，我们也需要写 LDIF 来创建 ou：

```ldif
dn: ou=people,dc=bangdream,dc=example,dc=org
objectClass: top
objectClass: organizationalUnit
ou: people

dn: ou=groups,dc=bangdream,dc=example,dc=org
objectClass: top
objectClass: organizationalUnit
ou: groups
```

!!! note "我可以写 `ou=用户`，`ou=组` 吗？" {#ou-utf8}

    (TODO)

(TODO)

## 参考资料 {#references}

- [使用 OpenLDAP 在 Linux 上进行中心化用户管理](https://harrychen.xyz/2021/01/17/openldap-linux-auth/)
