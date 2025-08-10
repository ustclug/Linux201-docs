---
icon: simple/gnubash
---

# Shell 脚本

!!! note "主要作者"

    [@tiankaima][tiankaima]

!!! warning "本文编写中"

!!! comment "适用范围"

    Shell 也许是与 Linux 打交道 (日常维护、安装等) 最直接的方式。
    在此基础上逐渐发展出了需要使用变量、控制流的 Shell Script。

    <!-- TODO: require revision -->

    Shell Script 的适用范围：**自动化、不涉及核心业务的流程** (例如周期性执行的任务、编译、安装脚本) 等，通过 Shell 可以很方便的调用其他命令、批量处理文件/目录等，但是不适合编写大型程序。

!!! note "特点"

    -   作为脚本语言，Shell Script 只提供基本的变量、控制流、函数等，几乎没有面向对象的特性。
    -   Shell Script 适合处理文本、调用系统命令等，但是不适合处理复杂的数据结构。
    -   真正意义上的开箱即用，无需额外安装，因此常用在安装、编译等场景。

参考资料：

- [Linux 101/Ch06](https://101.lug.ustc.edu.cn/Ch06/)
- [The Missing Semester of Your CS Education/shell-tools](https://missing-semester-cn.github.io/2020/shell-tools/)

作为补充，可以查阅：

- [jq](https://jqlang.github.io/jq/): 用于处理 JSON 数据
- [yq](https://github.com/mikefarah/yq): 用于处理 YAML 数据

??? comment "Shell tools"

    一个常见的提升日常效率的办法是: 使用 oh-my-zsh、fzf、tmux 等工具。
