# 章节编写指导

本部分参考自 [Linux 101 章节编写指导](https://101.lug.ustc.edu.cn/Spec/writing/)，有较大幅度的调整。以下将从两个方面：格式和内容，介绍如何编写章节。

## 格式要求 {#format}

### 环境配置 {#env-setup}

Linux 201 使用 mkdocs + mkdocs-material 作为文档框架与主题，并且使用 [autocorrect](https://github.com/huacnlee/autocorrect/) 进行中文格式检查，与 [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) 做 Markdown 格式检查。请阅读[仓库下的 README.md](https://github.com/ustclug/Linux201-docs/blob/master/README.md) 了解基本环境的配置。

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
!!! warning "本文已完成，等待校对"
```

或

```markdown
!!! success "本文已完成并校对"
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

### 请勿抄袭 {#no-plagiarism}

请勿抄袭他人的文章。如果有参考，请在文中明确写明。

特别地，也不要使用 GPT 大段大段生成内容，然后直接提交。这样的内容即使正确性无误，也包含大量的废话，并且存在潜在的版权风险。
