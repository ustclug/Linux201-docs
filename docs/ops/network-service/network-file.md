# 网络文件共享

!!! warning "仍在编辑中，目前只有基于 ssh 的传输方式"

网络文件共享是日常工作提高生产力的重要一环。Linux 环境下有多种文件传输工具，这里提供实践指南。

## SCP

SCP 是基于 SSH (Secure Shell) 协议的文件传输工具，它允许用户在本地和远程主机之间安全地复制文件。SCP 使用 SSH 进行数据传输，提供同 SSH 相同级别的安全性，包括数据加密和用户认证。

SCP 命令的基本语法如下：

```shell
scp [选项] [源文件] [目标文件]
```

其中，源文件或目标文件的格式可以是本地路径，或者远程路径，如 `用户名@主机名:文件路径`。

### 使用示例

#### 文件复制

从本地复制到远程服务器

```shell
scp /path/to/local/file username@remotehost:/path/to/remote/directory
```

或从远程服务器复制到本地

```shell
scp username@remotehost:/path/to/remote/file /path/to/local/directory
```

这个命令会提示您输入远程主机上用户的密码，除非您已经设置了 SSH 密钥认证。

!!! tip

    你可以一次性传输多个文件或目录，将它们作为源路径的参数。
    例如：`scp file1.txt file2.txt username@remotehost:/path/to/remote/directory`

#### 复制目录

如果需要复制整个目录，需要使用 `-r` 选项，这表示递归复制：

```shell
scp -r /path/to/local/directory username@remotehost:/path/to/remote/directory
```

#### 使用非标准端口

如果远程主机的 SSH 服务不是运行在标准端口（22），则可以使用 `-P` 选项指定端口：

```shell
scp -P 2222 /path/to/local/file username@remotehost:/path/to/remote/directory
```

#### 限制带宽

使用 `-l` 选项可以限制 SCP 使用的带宽，单位是 `Kbit/s`：

```shell
scp -l 1024 /path/to/local/file username@remotehost:/path/to/remote/directory
```

#### 保留文件属性

使用 `-p` 选项可以保留原文件的修改时间和访问权限：

```shell
scp -p /path/to/local/file username@remotehost:/path/to/remote/directory
```

#### 开启压缩

使用 `-C` 选项开启压缩，可以减少传输数据量并提升传输速度，特别对于文本文件效果显著。

```shell
scp -C /path/to/local/file username@remotehost:/path/to/remote/directory
```

## SFTP

SFTP 是一种安全的文件传输协议，它在 SSH 的基础上提供了一个扩展的功能集合，用于文件访问、文件传输和文件管理。与 SCP 相比，SFTP 提供了更丰富的操作文件和目录的功能，例如列出目录内容、删除文件、创建和删除目录等。由于 SFTP 在传输过程中使用 SSH 提供的加密通道，因此它能够保证数据的安全性和隐私性。

### 使用指南

#### 启动 SFTP 会话

要连接到远程服务器，可以使用以下命令：

```shell
sftp username@remotehost
```

如果远程服务器的 SSH 服务使用的不是默认端口（22），可以使用 `-P` 选项指定端口：

```shell
sftp -P 2233 username@remotehost
```

#### 文件和目录操作

- `ls`：列出远程目录的内容。
- `get remote-file [local-file]`：下载文件。
- `put local-file [remote-file]`：上传文件。
- `mkdir directory-name`：创建远程目录。
- `rmdir directory-name`：删除远程目录。
- `rm file-name`：删除远程文件。
- `chmod mode file-name`：改变远程文件的权限。
- `pwd`：显示当前远程目录。
- `lpwd`：显示当前本地目录。
- `cd directory-name`：改变远程工作目录。
- `lcd directory-name`：改变本地工作目录。

#### 退出 SFTP 会话

输入 `exit` 或 `bye` 来终止 SFTP 会话。

!!! 使用脚本进行自动化操作

    通过创建一个包含SFTP命令的批处理文件，你可以让SFTP会话自动执行这些命令。例如，你可以创建一个文件 `upload.txt`，其中包含以下内容：

    ```shell
    put file1.txt
    put file2.jpg
    put file3.pdf
    quit
    ```
    然后使用命令 `sftp -b upload.txt username@remotehost` 来自动上传文件。
