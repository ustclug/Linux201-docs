# 章节编写指导

本部分参考自 [Linux 101 章节编写指导](https://101.lug.ustc.edu.cn/Spec/writing/)，有较大幅度的调整。以下将从两个方面：格式和内容，介绍如何编写章节。

## 格式要求 {#format}

### 环境配置 {#env-setup}

Linux 201 使用 mkdocs + mkdocs-material 作为文档框架与主题，并且使用 [autocorrect](https://github.com/huacnlee/autocorrect/) 进行中文格式检查，与 [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) 做 Markdown 格式检查。请阅读[仓库下的 README.md](https://github.com/ustclug/Linux201-docs/blob/master/README.md) 了解基本环境的配置。

提示：Autocorrect 无法捉住所有的中文格式问题，特别是在 [Admonition](#admonition) 里面的内容。请注意**避免**以下常见的情况：

- 中文与拉丁字母、阿拉伯数字之间缺失空格
- 中文段落中使用半角而非全角标点符号
- 在标点符号前后添加多余的空格
- 中文段落结尾不加标点符号

### 主要作者 {#authors}

如果你编写了某个章节的一部分或全部内容，或为某个章节的写作思路提供了重要的帮助，请在 `includes/authors.md` 中添加你的 ID，类似于这样（假设你叫 `example`）：

```markdown
[example]: https://github.com/example
```

然后章节开头的主要作者提示框格式类似如下：

```markdown
!!! note "主要作者"

    [@example][example]、[@test][test]
```

不同名字之间使用**中文全角顿号**（即「、」）分隔。

### 章节编写状态 {#status}

对于未定稿的内容，根据状态不同，请在 h1 标题下方添加如下内容：

```markdown
!!! warning "本文编写中"
```

或

```markdown
!!! success "本文已完成"
```

### 使用提示框（Admonition） {#admonition}

提示框是 mkdocs-material 的特色功能。格式类似于如下：

```markdown
!!! warning "警告标题"

    这是提示框的内容。

??? note "提示标题"

    这是提示框的内容，`???` 表示默认折叠。
```

效果如下：

!!! warning "警告标题"

    这是提示框的内容。

??? note "提示标题"

    这是提示框的内容，`???` 表示默认折叠, 使用 `???+` 可以折叠, 但是默认展开。

我们使用的 mkdocs-material 提供的标准提示框有以下几种：

- note: 提示，表示重要的信息
- warning: 警告，表示需要特别注意的信息
- danger: 危险，表示如果忽视，可能导致严重后果的信息
- tip: 小技巧
- example: 示例
- question: 需要读者思考的问题

此外，我们自定义了一些提示框类型：

- comment: 表示编者对内容的评论（类似于某些游戏的「Developer Commentary」），使用时请在标题处写上你的昵称，类似于这样：

    ```markdown
    !!! comment "@taoky: 吐槽"

        比如说……
    ```

    效果：

    !!! comment "@taoky: 吐槽"

        比如说……

- lab: 教程不会详细说明，需要读者自己尝试的实验。

### 为标题和小标题添加 ID {#heading-ids}

由于文章篇目较长，使用时会经常遇到需要链接到文章某一段的情况。受限于 MkDocs 自动生成 Anchor ID 的功能（只支持英文字符），纯中文的标题会导致生成 `_1`, `_2` 这样的 ID。一方面这样的 ID 看起来不直观，另一方面每当标题发生增减时这些 ID 都会变，因此请为每个**除了 h1 以外的标题**手动添加一个有意义的 ID，方法如下：

```markdown
### 为标题和小标题添加 ID {#heading-ids}

注意 `{` 前面要有一个空格哦！
```

建议 ID 只包含小写字母、数字和横线 `-`，必要时使用句点（不使用大写字母和其他标点符号）。

### 图片规格 {#image-specs}

如果你使用 [draw.io](https://draw.io) 绘制图片，请在「文件→属性」中设置缩放比为 200%，并导出为 SVG 格式。如果使用其他绘图工具，请确保导出的图片清晰可见，且文字大小适中。

### 为图片添加配字 {#image-caption}

使用 [Python Markdown Extension](https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/caption/) 的语法，在图片后面添加配字，格式如下：

```markdown
![image](url)

/// caption
图 1. 这张图片的配字
///
```

### 图片与附件文件 {#images-attachments}

图片放置在 `docs/images` 目录，小的附件文件放置在 `docs/assets/` 目录，编写 Markdown 时可以使用**相对路径**引用。

### man 手册引用 {#man}

`includes/man.md` 中包含了一些手册的在线阅读链接，类似如下：

```markdown
[fstab.5]: https://man7.org/linux/man-pages/man5/fstab.5.html
```

按照指定格式添加后，使用如下方式引用：

```markdown
[fstab(5)][fstab.5] 提供了……
```

### 定义列表 {#definition-list}

在写作时，我们可能会需要列出多个术语，同时给出它们的定义或者介绍，如果使用普通的有序或无序列表的话，给读者的观感可能过于紧凑。此时可以考虑使用定义列表格式，类似如下：

```markdown
定义一

:   本项经常出现在科大西区和中区的交界处：肥西路上。在晚上九点之后，有概率可以在路边发现本项。

    需要注意的是，离开校门时请带好手机。

定义二

:   我编不下去了。
```

显示效果如下：

定义一

:   本项经常出现在科大西区和中区的交界处：肥西路上。在晚上九点之后，有概率可以在路边发现本项。

    需要注意的是，离开校门时请带好手机。

定义二

:   我编不下去了。

## 内容要求 {#content}

### 编写原则 {#principle}

请阅读[首页](../index.md)，了解我们的四条编写原则。

### 可读性建议 {#readability-suggestions}

以下给出一些在实际写作时发现的可以提升文本可读性的参考建议，例子为实际写作时出现的情况。由于 Linux 201 仍然在编写中，因此以下的反例有可能仍然存在于现有的内容中。

#### 省略极其简单的内容 {#skip-naive-contents}

Linux 201 的读者应当有基础的 Linux 操作的能力，因此有一些非常简单的操作是没有必要写出来的。这样做可以让读者的注意力尽可能在更关键的地方。其中最典型的例子是安装软件包。

❌ 反例：

:   在使用了一个未安装的命令时，可以选择使用 `command-not-found`。其安装方式十分简单，只需 `apt install command-not-found` 即可。

✅ 正例：

:   如果使用过默认安装的 Ubuntu 的话，可能会发现，在输入命令时，如果命令不存在，会有类似下面的提示：

    ```console
    $ htop
    Command 'htop' not found, but can be installed with:
    sudo apt install htop
    ```

    这是由 `command-not-found` 包支持的，（后略）。

#### 避免极长的 `console` 代码块 {#no-extremely-long-console-code-block}

极长的 `console` 代码块会让读者迷失在命令与输出中，无法抓住重点需要了解的命令。

❌ 反例：

:   我们可以来试一试：

    ```console
    $ truncate -s 8G btrfs.img
    $ mkfs.btrfs btrfs.img
    （输出省略）
    $ sudo mount btrfs.img /media/btrfs
    $ sudo btrfs filesystem show /media/btrfs  # 可以使用 btrfs 工具管理 Btrfs 文件系统
    Label: none  uuid: 5cdcf4bb-8020-45f9-8dfd-95e04a2a2bc1
        Total devices 1 FS bytes used 144.00KiB
        devid    1 size 8.00GiB used 536.00MiB path /dev/loop0
    $ # 接下来创建一些 subvolume
    $ sudo btrfs subvolume create /media/btrfs/subvol1
    Create subvolume '/media/btrfs/subvol1'
    $ sudo btrfs subvolume create /media/btrfs/subvol2
    Create subvolume '/media/btrfs/subvol2'
    $ sudo btrfs subvolume create /media/btrfs/subvol3
    Create subvolume '/media/btrfs/subvol3'
    $ sudo btrfs subvolume list /media/btrfs
    ID 256 gen 8 top level 5 path subvol1
    ID 257 gen 8 top level 5 path subvol2
    ID 258 gen 8 top level 5 path subvol3
    $ ls -lh /media/btrfs  # 看起来和普通目录没什么区别
    total 0
    drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol1/
    drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol2/
    drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol3/
    ```

✅ 正例：

:   我们可以来试一试。首先创建一个 Btrfs 的文件系统：

    ```console
    $ truncate -s 8G btrfs.img
    $ mkfs.btrfs btrfs.img
    （输出省略）
    $ sudo mount btrfs.img /media/btrfs
    $ sudo btrfs filesystem show /media/btrfs  # 可以使用 btrfs 工具管理 Btrfs 文件系统
    Label: none  uuid: 5cdcf4bb-8020-45f9-8dfd-95e04a2a2bc1
        Total devices 1 FS bytes used 144.00KiB
        devid    1 size 8.00GiB used 536.00MiB path /dev/loop0
    ```

    此时 `/media/btrfs` 挂载的就是 top-level subvolume。之后创建一些 subvolume：

    ```console
    $ sudo btrfs subvolume create /media/btrfs/subvol1
    Create subvolume '/media/btrfs/subvol1'
    $ sudo btrfs subvolume create /media/btrfs/subvol2
    Create subvolume '/media/btrfs/subvol2'
    $ sudo btrfs subvolume create /media/btrfs/subvol3
    Create subvolume '/media/btrfs/subvol3'
    $ sudo btrfs subvolume list /media/btrfs
    ID 256 gen 8 top level 5 path subvol1
    ID 257 gen 8 top level 5 path subvol2
    ID 258 gen 8 top level 5 path subvol3
    $ ls -lh /media/btrfs  # 看起来和普通目录没什么区别
    total 0
    drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol1/
    drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol2/
    drwxr-xr-x 1 root root 0 Feb 11 14:50 subvol3/
    ```

#### 避免单纯列出手册内容 {#avoid-repeat-manual}

对于程序不常用的参数，宁可不介绍，也不要花大篇幅一个一个讲参数。

❌ 反例：

:   Nmap 支持的输出格式包括：

    - 标准输出到控制台。
    - -oN 输出到普通文件。
    - -oX 输出为 XML 格式。
    - -oG 输出为 grep 友好格式。
    - -oA 输出所有上述格式。

    例如想要输出到文件，可以这样做：

    ```shell
    nmap -oN output.txt [target]
    ```

✅ 正例：

:   （重写的时候这个介绍直接删除了）

### 版权与 AI 工具使用约定 {#copyright-and-ai}

Linux 201 的 license 为 [CC BY-NC-SA 4.0 协议](https://creativecommons.org/licenses/by-nc-sa/4.0/)。简单来说，这要求：

- 转载、修改自 Linux 201 的内容需要署名。一般来说，你至少需要提及 "Linux 201"，并提供原内容的链接。
- Linux 201 的内容不可用于商业用途（包括但不限于售卖、添加网页广告等）。
- 转载、修改自 Linux 201 的内容也需要使用 CC BY-NC-SA 4.0 协议授权。

为 Linux 201 贡献内容意味着你同意将你写作的内容以 CC BY-NC-SA 4.0 协议授权给 Linux 201 项目。你仍然有你写作内容的所有权。

#### 为图片添加引用来源 {#image-ref}

如果添加到 Linux 201 的图片不是你自己创作或截图的，你需要：

- 以外链形式引用图片内容
- 如果需要将图片存储到 Linux 201 仓库，需要在文本中明确给出原始图片的来源（例如以 caption 的形式）

现有的内容中可能存在少量的图片不符合这里的要求，如果发现可帮助我们修改。

#### 请勿抄袭 {#no-plagiarism}

请勿抄袭他人的文章。如果有参考其他人写作的内容，请在文中明确写明。

#### AI 工具使用注意事项 {#ai-tools}

以下 AI 工具特指基于大语言模型（LLM）进行文本、图片生成的工具，包括但不限于 LLM 供应商的 Web 平台、对接 LLM 的即时聊天工具的机器人、直接调用 API、诸如 GitHub Copilot、Claude Code、Codex、OpenCode 等编程工具、诸如 OpenClaw 等 agent 工具。

**Linux 201 是由人类写作，并提供给人类阅读的文档。写作本身也是一种训练与学习的过程**。基于这一原则，我们希望在 Linux 201 的写作中规范相关工具的使用。

以下情况下，你不需要披露 LLM 的使用情况：

- 从 LLM 的输出中获得写作灵感
- 写作时参考并人工核对了由 LLM 提供的资料
- 使用 LLM 工具检查写作完成的文本，并人工核对、应用建议
- 写作时正常使用**代码补全**模型（利用代码补全模型大量生成文档文本的不在此列）

以下情况下，你需要在 PR 或 commit message 中披露 LLM 的使用情况：

- 写作内容的部分或全部初稿由 LLM 生成，并人工进行了足够的改写
- 使用 LLM 工具进行了写作以外的修改（例如修改 CI、文档生成配置等）

我们不接受以下的贡献：

- 由 LLM 工具（例如 Claude Code）提交的极其简单（trivial）的 PR（例如修改错别字）。这样的 PR 会被直接关闭。
- 完全使用 LLM 工具进行思考与写作产生的贡献
- PR 或 commit 中存在大量疑似 LLM 生成的废话的贡献
- 使用 LLM 工具提交与 Linux 201 无关的 PR
    - 如果这么做，你的 GitHub 账号会被 GitHub ustclug 组织无限期拉黑。请参考这个反例：<https://github.com/ustclug/Linux201-docs/pull/61>
