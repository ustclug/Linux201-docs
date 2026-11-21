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

### PAM 认证 {#pam}

!!! tip "认证（Authentication）和授权（Authorization）的区别" {#authentication-authorization}

    这两个对应的英文单词由于长得比较相似，容易被混淆。简单来说，认证负责**确认你是谁**，而授权负责**确认你能不能做你要做的事情**。

    在 Unix 的架构下，PAM 就负责认证用户（在外部组件的帮助下，可以实现包括但不限于让用户输入密码、按指纹、按硬件密钥、输入 TOTP、刷脸验证等等），而我们熟悉的 `sudo`，以及其平替 `doas`，和细粒度的 Polkit 做的就是授权（检查用户能否提权到 root 或者其他用户，用户自己能不能执行某种特权操作，例如修改系统名等）。

(TODO)

### 授权工具 {#authorization-tools}

以下介绍包括 sudo 和 Polkit 在内的授权相关的工具。

#### sudo

sudo 应该是本文几乎所有读者都经常使用的工具。如果需要添加自己的配置，推荐在 `/etc/sudoers.d/` 下使用 `visudo` 添加。

sudo 规则的基本结构为 `谁 在哪台机器上=(可以以谁的身份) 运行哪些命令`，其中括号内可以是 `(用户:组)` 的结构。例如：

- `root ALL=(ALL:ALL) ALL`：允许 root 切换到任意用户运行任意命令，否则即使你是 root，`sudo` 也会拒绝。
- `%sudo ALL=(ALL:ALL) ALL`：允许 `sudo` 用户组的用户切换到任意用户运行任意命令。
- `certupdate ALL=(root) NOPASSWD: /usr/bin/systemctl reload nginx`：允许 `certupdate` 用户无密码让 Nginx 重新加载配置。
- `telegraf ALL=(root) NOEXEC: NOPASSWD: /usr/sbin/nfacct list`：允许 `telegraf` 用户提取到 root 无密码运行 `nfacct list` 命令，但是不可以让 `nfacct` 再启动其他的程序。

其中指定的可以运行的命令必须使用完整路径。用户可以用 `sudo -l` 查看自己的配置。

!!! note "sudo 规则的主机限制真的有意义吗？" {#sudoers-hostname}

    sudoers 配置设计初衷是希望同一个文件可以部署到很多台机器上（例如通过 NFS 等），添加主机限制可以帮助系统管理员写出「允许用户 A 在 X 服务器上提权跑应用 1，在 Y 服务器上提权跑应用 2」这样的配置，而不需要给每台机器放不一样的配置文件。这里可以添加主机名（hostname）、IP 地址等。

!!! warning "细粒度限制的安全性建议" {#sudoers-process-limitation}

    虽然 sudo 提供了方便的按用户和程序名称配置能否提权的功能，但是在编写配置时，需要额外注意安全，否则可能实质上给用户授权了没有限制的 root 权限：

    - 限制提权的目标用户，如果只需要提权到某个特定用户，不要写 `(ALL:ALL)`。
    - 在可行的情况下，添加 `NOEXEC`：避免程序以非预期的方式启动其他程序。
    - 如果可以授权运行的命令没有任何参数，结尾需要添加 `""`（例如 `/usr/local/bin/backup.sh ""`），**否则会被 sudo 解释为允许任意参数**。
    - 额外限制环境变量。对需要保留的环境变量，sudo 默认为白名单制，可以以 root 身份用 `sudo -V` 查看。
        - 某些情况下需要额外添加环境变量，例如**添加 `LESSSECURE=1` 来禁用 `less` 分页器的命令执行功能**。
    - 从命令字符串角度限制有时候完全无法避免用户做预期以外的事情，例如 [Hackergame 2024 的 "Docker for Everyone Plus" 题目](https://github.com/USTC-Hackergame/hackergame2024-writeups/blob/master/official/Docker%20for%20Everyone%20Plus/README.md) 展示的失败的用 `sudo` 限制普通用户使用 `docker` 命令的例子。这种情况下建议放弃 sudo，使用其他方式解决问题。

此外其他的一些设置：

- `Defaults secure_path="/usr/sbin:/usr/bin:/sbin:/bin"`：重写 PATH 环境变量，避免提权运行的程序未使用绝对路径调用其他程序时，被用户自己的 PATH 欺骗。
- `Defaults:%wheel !targetpw`：允许 `wheel` 用户组的用户使用 sudo 时不使用提权目标用户的密码（而是自己的密码）验证。一般来讲，`!targetpw` 是默认配置，但在某些环境下，可能会设置 `Defaults targetpw`（默认要求输入目标密码）。

!!! tip "sudo 录屏审计" {#sudo-record}

    sudo 有一个鲜为人知的功能：它可以录制 sudo 提权之后的 PTY 操作，在对安全性要求较高的环境下可以帮助系统管理员检查是否有内鬼使用 sudo 提权之后搞破坏：

    ```sudoers title="/etc/sudoers.d/record-pty"
    # 录制终端输出
    Defaults log_output
    # 录制终端输入，可能会把用户后续输入的密码录制进去，所以不建议启用
    # Defaults log_input
    # 不让 sudoreplay（播放录制）的输出记录进去
    Defaults!/usr/bin/sudoreplay !log_output
    # 不让重启的输出记录进去，REBOOT 在 /etc/sudoers 有定义
    Defaults!REBOOT !log_output
    # 限制最多记录 1000 条数据
    Defaults maxseq = 1000
    ```

    之后可以用 `sudoreplay` 播放：

    ```console
    # sudoreplay -l
    Nov 21 10:34:42 2026 : root : HOST=localhost ; TTY=pts/0 ; CWD=/etc ; USER=root ; TSID=000001 ; COMMAND=/bin/bash
    # sudoreplay 000001
    Replaying sudo session: /bin/bash
    （后续省略）
    ```

    录屏存储在 `/var/log/sudo-io` 里。由于提权后用户可能会把这个目录直接删了，因此在需要高安全性的场合下，可以配置让 sudo 把录屏发送到运行 `sudo_logsrvd` 的日志服务器上面。

!!! note "sudo 认证缓存" {#sudo-auth-cache}

    没有人喜欢一遍一遍又一遍输密码，因此 sudo 默认会缓存认证状态，这样在一定时间内，sudo 就不会再问你要密码。sudo 会存储对应操作的 TTY 设备号，session 的 leader 进程的创建时间到 `/run/sudo/ts/<UID>` 或者 `/run/sudo/ts/<username>`（较老版本）里。在相同的 TTY 里，一段时间内再操作的话，sudo 就不会再进行认证，而是直接进行授权判断。

!!! note "doas、sudo-rs 和 run0" {#doas-sudo-rs-run0}

    sudo 是系统非常重要的组件：它本身有 SUID 权限，以 root 身份运行，一旦有安全漏洞，攻击者就能轻松成为 root，接管系统。但是 sudo 的功能比较多（包括历史遗留的兼容性考虑），攻击面也相对较大。因此有一些改进的新方案：

    - doas 由 OpenBSD 开发，在 Linux 上的实现为 [OpenDoas](https://github.com/Duncaen/OpenDoas)。相比 sudo（十几万行），它的代码量很小（几千行），因此审计也更为简单。它只实现了最常见的功能，并且配置与 sudo 不兼容。
    - [sudo-rs](https://github.com/trifectatechfoundation/sudo-rs) 是 Rust 重写的 sudo，旨在利用 Rust 去除与内存安全相关的问题，并在保持与 sudo 配置兼容性的情况下移除了一部分罕见、复杂的功能。Ubuntu 从 25.10 开始使用 sudo-rs 替代 sudo。
    - run0 是 systemd 的方案，利用下文介绍的 Polkit 授权。和其他方案相比，其最大的不同是不再依赖于 SUID 权限，而是由 systemd 创建一个隔离的提权后的进程。

    此外，`pkexec` 尽管使用 Polkit，但是其也是一个 SUID 权限程序。其曾经出现过非常严重的安全漏洞（[CVE-2021-4034](https://www.qualys.com/2022/01/25/cve-2021-4034/pwnkit.txt)），并且对 `pkexec` 的代码审计可能远不如上述方案，因此不建议使用。

#### Polkit

即使你不是 Linux 桌面用户，可能也见过 Polkit 的鉴权提示：

```console
$ systemctl enable ssh
==== AUTHENTICATING FOR org.freedesktop.systemd1.manage-unit-files ====
Authentication is required to manage system service or unit files.
Authenticating as: ,,, (username)
Password: 
```

为什么已经有 sudo 了，还要再来一个授权工具呢？在服务器场景下，Polkit 看起来用途不大，但是在桌面环境下，Polkit 很有必要，因为桌面用户经常需要高频做一些传统意义上需要 root 的事情，包括连接/断开网络、调整时间、关机/重启、挂载 U 盘等等。如果每次都要敲密码，那实在有点太折磨了。但是光靠 sudo 规则无法完全解决问题：

- sudo 依靠的是字符串匹配来决定是否放行，对复杂的需求很容易误判导致安全问题。
- sudo 不知道（不关心）操作的用户是物理意义上可以和设备接触，还是在用 SSH 访问。

Polkit 相比于 sudo，提供了更加细粒度的规则设置。Polkit 的核心是动作（Action）和规则（Rule），其中动作在 `/usr/share/polkit-1/actions/` 中，由软件包安装，指定需要权限的动作以及默认的策略，例如上面的 `org.freedesktop.systemd1.manage-unit-files` 就是一种动作，对应的 XML 节选如下：

```xml
<action id="org.freedesktop.systemd1.manage-unit-files">
        <description gettext-domain="systemd">Manage system service or unit files</description>
        <message gettext-domain="systemd">Authentication is required to manage system service or unit files.</message>
        <defaults>
                <allow_any>auth_admin</allow_any>
                <allow_inactive>auth_admin</allow_inactive>
                <allow_active>auth_admin_keep</allow_active>
        </defaults>
        <annotate key="org.freedesktop.policykit.imply">org.freedesktop.systemd1.reload-daemon org.freedesktop.systemd1.manage-units</annotate>
</action>
```

其中如果用户是当前正在物理操作电脑的话，那么就对应 `allow_active`，如果物理操作，但是切换到了后台（例如切走了 TTY），那么对应 `allow_inactive`，其他情况（例如远程登录）对应 `allow_any`。在使用 systemd-logind 的系统上，Polkit 会使用 systemd 后端获取对应的信息。

当前所有的 Polkit 动作可以用 `pkaction` 查看。

而 Polkit 的规则使用的是 JavaScript 语言。系统默认规则在 `/usr/share/polkit-1/rules.d/`，用户自定义的规则在 `/etc/polkit-1/rules.d/`。例如默认定义 `sudo` 用户组为管理员组：

```js title="/usr/share/polkit-1/rules.d/50-default.rules"
polkit.addAdminRule(function(action, subject) {
    return ["unix-group:sudo"];
});
```

允许 `empower` 用户组提权（动作总是允许执行）：

```js title="/usr/share/polkit-1/rules.d/empower.rules"
polkit.addRule(function(action, subject) {
    if (subject.isInGroup("empower")) {
        return polkit.Result.YES;
    }
});
```

允许 `systemd-network` 用户设置 hostname，获取 UUID，设置时区：

```js title="/usr/share/polkit-1/rules.d/systemd-networkd.rules"
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.hostname1.set-hostname" ||
         action.id == "org.freedesktop.hostname1.get-product-uuid" ||
         action.id == "org.freedesktop.timedate1.set-timezone") &&
        subject.user == "systemd-network") {
        return polkit.Result.YES;
    }
});
```

!!! note "Polkit 引入 JavaScript 的争议" {#polkit-js-controversy}

    早期的 Polkit 使用的是类似 INI 的 `.pkla` 文件。例如在 Debian 11 中，`systemd` 包安装的配置类似如下：

    ```ini title="/var/lib/polkit-1/localauthority/10-vendor.d/systemd-networkd.pkla"
    [Allow systemd-networkd to set timezone and transient hostname]
    Identity=unix-user:systemd-network
    Action=org.freedesktop.hostname1.set-hostname;org.freedesktop.hostname1.get-product-uuid;org.freedesktop.timedate1.set-timezone;
    ResultAny=yes
    ```

    但是[出于灵活性等考虑](https://davidz25.blogspot.com/2012/06/authorization-rules-in-polkit.html)，Polkit 在 0.106（2012 年）迁移到了 JavaScript 作为配置，使用 Firefox 的 JS 引擎 SpiderMonkey 来执行 JavaScript 配置脚本。这一点颇具争议，尽管 JS 引擎分离出来，不以 root 权限运行，但是这样导致了可能的攻击面增加，并且 SpiderMonkey 本身也比较庞大。因此很长时间内，Debian 都没有采用新的 JS 配置。一直到轻量的 [Duktape](https://duktape.org/) 引入到 Polkit 作为 SpiderMonkey 的替代之后，相关的部分问题才得到了缓解。

!!! tip "让 run0 免密码执行" {#run0-nopasswd}

    如果版本足够新（需要至少 systemd 259 版本，Debian 14+），systemd 会安装 `/usr/share/polkit-1/rules.d/empower.rules`，允许 empower 组内所有用户使用所有动作，因此把自己加到这个组里（如果没有需要创建一个）即可。`run0 --empower` 会同时给创建出来的 service 里面的用户所有 capabilities，并临时加入到 empower 这个组里面，因此相当于启动了一个有所有特权的当前用户的 shell。

    如果没有的话，也可以自己创建类似的规则，例如让 `sudo` 用户组无密码：

    ```js title="/etc/polkit-1/rules.d/sudo-group-nopasswd.rules"
    polkit.addRule(function(action, subject) {
        if (action.id == "org.freedesktop.systemd1.manage-units" && subject.isInGroup("sudo")) {
            return polkit.Result.YES;
        }
    });
    ```

!!! tip "让用户只能用 run0 跑某个指定的命令" {#run0-service}

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
changetype: modify
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
# 或者用 -W 交互式输入密码，以下同。
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

这里表明当前环境的 base DN 就是 `dc=nodomain`。如果不满意，使用 `dpkg-reconfigure slapd` 配置即可（这一步也会设置 LDAP 的管理员密码）。后文的 `ldapsearch` 输出会省略一部分注释以方便阅读。

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

    在默认配置下，root 用户有很多权限，具体配置会在后文介绍 ACL 时提到。

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

!!! tip "查看初始配置" {#slapd-init-config}

    `slapd` 包的初始配置在 `/usr/share/slapd/slapd.init.ldif`，包含每项设置的注释，可以参考阅读。

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

    这里通过 `olcAccess` 指定的 ACL 配置会在其他数据库的 `olcAccess` 之后插入，在数据库前面的 `olcAccess` 没有终止匹配的情况下，允许通过 `ldapi:///` 连接的 root 用户管理数据库，并允许所有用户（包括匿名用户）读取 rootDSE 和 schema。

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

```ldif title="ou.ldif"
dn: ou=people,dc=bangdream,dc=example,dc=org
objectClass: top
objectClass: organizationalUnit
ou: people

dn: ou=groups,dc=bangdream,dc=example,dc=org
objectClass: top
objectClass: organizationalUnit
ou: groups
```

之后使用 `ldapadd` 执行 LDIF：

```sh
ldapadd -x -H ldapi:/// -D "cn=admin,dc=bangdream,dc=example,dc=org" -W -f ou.ldif
```

如果没有 `-f ou.ldif` 的话，`ldapadd` 就会直接从 stdin 读 LDIF。

!!! note "查找数据库管理员的 DN" {#get-admin-from-olcrootdn}

    用户数据库的管理员由数据库的 `olcRootDN` 属性指定：

    ```console
    $ sudo ldapsearch -H ldapi:/// -Y EXTERNAL -b 'olcDatabase={1}mdb,cn=config'
    # {1}mdb, config
    dn: olcDatabase={1}mdb,cn=config
    （省略）
    olcRootDN: cn=admin,dc=bangdream,dc=example,dc=org
    （省略）
    ```

!!! note "我可以写 `ou=用户`，`ou=组` 吗？" {#ou-utf8}

    `ou` 可以是非 ASCII 字符，`ldapadd` 也能正常处理：

    ```ldif title="test.ldif"
    dn: ou=测试,dc=bangdream,dc=example,dc=org
    objectClass: top
    objectClass: organizationalUnit
    ou: 测试
    ```

    但是 `ldapsearch` 在输出查询结果时，根据 [RFC 2849](https://datatracker.ietf.org/doc/html/rfc2849)，会对非 ASCII 等特殊的字符做 base64 处理。这一类的属性名称和值之间是两个冒号（`:: `）。

    ```console
    $ ldapsearch -H ldapi:/// -Y EXTERNAL -b 'dc=bangdream,dc=example,dc=org'
    # \E6\B5\8B\E8\AF\95, bangdream.example.org
    dn:: b3U95rWL6K+VLGRjPWJhbmdkcmVhbSxkYz1leGFtcGxlLGRjPW9yZw==
    objectClass: top
    objectClass: organizationalUnit
    ou:: 5rWL6K+V
    $ echo 'b3U95rWL6K+VLGRjPWJhbmdkcmVhbSxkYz1leGFtcGxlLGRjPW9yZw==' | base64 -d; echo
    ou=测试,dc=bangdream,dc=example,dc=org
    $ echo '5rWL6K+V' | base64 -d; echo
    测试
    ```

    所以为了阅读方便，不建议这么做。

!!! note "为什么不能用 root 添加 LDIF？" {#mdb-acl}

    如果查看用户数据库的 `olcAccess`：

    ```console
    $ sudo ldapsearch -H ldapi:/// -Y EXTERNAL -b 'olcDatabase={1}mdb,cn=config'
    # {1}mdb, config
    dn: olcDatabase={1}mdb,cn=config
    （省略）
    olcAccess: {0}to attrs=userPassword by self write by anonymous auth by * none
    olcAccess: {1}to attrs=shadowLastChange by self write by * read
    olcAccess: {2}to * by * read
    （省略）
    ```

    在默认情况下，如果一条 `olcAccess` 被匹配到了，那么就不会再继续匹配。这里 root 会匹配到 `{2}to * by * read`，从而只能获取到只读权限，不会再去匹配 `{-1}frontend` 的配置。

!!! tip "忘了/要修改 `cn=admin,...` 的密码怎么办？" {#reset-mdb-password}

    这种情况下，千万不要使用 `dpkg-reconfigure slapd` 来重新设置，除非你想完全扔掉当前的所有数据。

    首先使用 `slappasswd` 生成自己想要设置的密码对应的哈希：

    ```console
    $ /sbin/slappasswd
    New password: 
    Re-enter new password: 
    {SSHA}(redacted)
    ```

    然后写一个 LDIF 文件：

    ```ldif title="reset-admin-passwd.ldif"
    dn: olcDatabase={1}mdb,cn=config
    changetype: modify
    replace: olcRootPW
    olcRootPW: {SSHA}(redacted)
    ```

    最后以 root 的身份应用：

    ```sh
    sudo ldapmodify -H ldapi:/// -Y EXTERNAL -f reset-admin-passwd.ldif
    ```

    注意这里不能够使用接下来会介绍的 `ldappasswd`。因为数据库管理员的密码，即使同 DN 的条目存在，也不在对应 entry 的 `userPassword` 里，而是在数据库的 `olcRootPW` 中。

`ldapadd` 其实是 `ldapmodify` 的软链接，相当于 `ldapmodify -a`（`-a` 即创建新的 entry）。

之后创建第一个用户和第一个组，以 RFC 2307 的组的格式为标准。

```ldif title="first-user-group.ldif"
dn: cn=Toyama Kasumi,ou=people,dc=bangdream,dc=example,dc=org
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: posixAccount
objectClass: shadowAccount
objectClass: top
cn: Toyama Kasumi
sn: Toyama
uid: kasumi
uidNumber: 2001
gidNumber: 2001
homeDirectory: /home/kasumi

dn: cn=Poppin'Party,ou=groups,dc=bangdream,dc=example,dc=org
objectClass: top
objectClass: posixGroup
cn: Poppin'Party
gidNumber: 2001
memberUid: kasumi
```

如法炮制：

```sh
ldapadd -x -H ldapi:/// -D "cn=admin,dc=bangdream,dc=example,dc=org" -W -f first-user-group.ldif
```

向已有的组添加用户时，因为组已经存在，所以一种常见的方式是分开操作：使用 `ldapadd` 添加用户，使用 `ldapmodify` 来做组的修改操作。

```ldif title="arisa.ldif"
dn: cn=Ichigaya Arisa,ou=people,dc=bangdream,dc=example,dc=org
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: posixAccount
objectClass: shadowAccount
objectClass: top
cn: Ichigaya Arisa
sn: Ichigaya
uid: arisa
uidNumber: 2002
gidNumber: 2001
homeDirectory: /home/arisa
```

```ldif title="add-arisa-to-group.ldif"
dn: cn=Poppin'Party,ou=groups,dc=bangdream,dc=example,dc=org
changetype: modify
add: memberUid
memberUid: arisa
```

```sh
ldapadd -x -H ldapi:/// -D "cn=admin,dc=bangdream,dc=example,dc=org" -W -f arisa.ldif
ldapmodify -x -H ldapi:/// -D "cn=admin,dc=bangdream,dc=example,dc=org" -W -f add-arisa-to-group.ldif
```

!!! tip "当然也可以放一起操作" {#ldapmodify-changetype-add}

    `changetype` 可以是 `add`，所以其实可以这样：

    ```ldif title="tae.ldif"
    dn: cn=Hanazono Tae,ou=people,dc=bangdream,dc=example,dc=org
    changetype: add
    objectClass: inetOrgPerson
    objectClass: organizationalPerson
    objectClass: person
    objectClass: posixAccount
    objectClass: shadowAccount
    objectClass: top
    cn: Hanazono Tae
    sn: Hanazono
    uid: tae
    uidNumber: 2003
    gidNumber: 2001
    homeDirectory: /home/tae

    dn: cn=Poppin'Party,ou=groups,dc=bangdream,dc=example,dc=org
    changetype: modify
    add: memberUid
    memberUid: tae
    ```

    ```sh
    ldapmodify -x -H ldapi:/// -D "cn=admin,dc=bangdream,dc=example,dc=org" -W -f tae.ldif
    ```

当然，别忘了给用户设置密码！虽然可以像重置管理员用户的密码一样用 `slappasswd` + `ldapmodify` 的方式来修改用户 entry 的 `userPassword` 属性，但是一般来说，使用的是 `ldappasswd` 工具：

```sh
# -S => 交互式输入新密码
ldappasswd -x -H ldapi:/// -D "cn=admin,dc=bangdream,dc=example,dc=org" \
  -W -S "cn=Toyama Kasumi,ou=people,dc=bangdream,dc=example,dc=org"
# 默认情况下，如果知道自己的密码，用户也可以修改自己的密码
ldappasswd -x -H ldapi:/// -D "cn=Toyama Kasumi,ou=people,dc=bangdream,dc=example,dc=org" \
  -W -S "cn=Toyama Kasumi,ou=people,dc=bangdream,dc=example,dc=org"
```

(TODO)

## 参考资料 {#references}

- [使用 OpenLDAP 在 Linux 上进行中心化用户管理](https://harrychen.xyz/2021/01/17/openldap-linux-auth/)
