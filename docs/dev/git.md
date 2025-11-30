---
icon: simple/git
---

# 版本管理与合作

!!! note "主要作者"

    [@tiankaima][tiankaima]、[@taoky][taoky]

!!! success "本文已完成"

本部分面向已经了解 git 最基本的操作的用户。如果你从未使用过 git，请参考网络上的其他教程，例如 USTC Vlab 项目的 [Git 简明教程](https://vlab.ustc.edu.cn/docs/tutorial/git/)。

## Git 使用技巧

### 基本概念 {#basic-concepts}

#### Object {#git-object}

对象（Object）是 git 存储数据的基本单元，存储在 `.git/objects` 目录下，以内容的 SHA-1 值区分。可以使用以下命令获取当前 git 仓库所有的 object 信息：

```shell
$ git cat-file --batch-check --batch-all-objects
000b2be4f2369ae78f788a92ee3fc00bb3cd64c7 tree 38
000b50049d29b61c300e4ec2e5cdcce52685861e blob 49457
000c536877dfda433b574fb37c6dc50048461505 blob 58088
001fe807cffb8bdb3d9fcd8d98282e596345aee9 tree 183
002e8efc4f94115882caec99b7b36e6a8f42e616 blob 331
00344f3b943fa09dde4694487e818f19d84d63f1 blob 67539
00392bcd6cec7e034d9996e5e17e506b8b7a7644 blob 243
0040fffeb2037807b75c5b3e69572e6e0e93c309 blob 43519
0046ec26cf4e99119ec2759d0580b894c1a7f344 tree 258
004d2057d06042847ca109edd9ca12be7cc255cb tree 409
（以下省略）
```

!!! tip "git 的文档"

    可以使用诸如 `man git-xxx` 的方式查看 `git xxx` 命令的文档，例如上面的 `git cat-file` 对应的是 `man git-cat-file`。

其中，`blob` 对象代表单个文件的内容，`tree` 对象代表目录结构，`commit` 对象代表提交，`tag` 对象代表标签。可以使用 `git cat-file -p <SHA-1>` 查看对象的内容。例如对于本仓库 hash 为 `74b5f6330f76d1e464deeff4d29935bba8d48c55` 的提交：

!!! tip "Commit ID 就是 Commit Object 的 SHA-1 值"

```shell
$ git cat-file -p 74b5f6330f76d1e464deeff4d29935bba8d48c55
tree 367ba031c357a771f2444048db71d109ec7e76d3
parent 87d45ab1963b039931f426a1402403996bba0300
author taoky <me@taoky.moe> 1736422437 +0800
committer taoky <me@taoky.moe> 1736422437 +0800

ops/storage: Take reciprocal for URE
```

可以看到，这个提交中除了 commit 内容以外，还包含了：

- 这个提交对应的目录信息（`tree`）
- 这个提交的父提交（`parent`）——这也是一个 commit 对象。
    - 第一个提交没有父提交。
    - Merge commit 有多个父提交，代表来自不同分支的合并。
- 提交的作者（`author`）与提交者（`committer`）

!!! tip "作者与提交者"

    没错，commit 的作者和提交者可以是两个不同的人。一般来讲，作者是编写原始代码的人，提交者是实际执行 commit 操作的人。

    默认情况下，作者和提交者都会采用 `git config` 中的配置。使用 `git commit --author="Name <email>"` 可以手动指定作者，设置环境变量 `GIT_COMMITTER_NAME` 和 `GIT_COMMITTER_EMAIL` 可以手动指定提交者。

!!! tip "其他角色"

    除了作者与提交者以外，完成工作的可能还有其他角色，例如合作者、审阅者等。Git 本身并没有提供这些角色的概念，但是可以通过 commit message 来记录这些信息。对合作者角色，最常见、收到广泛支持的方式是使用 `Co-Authored-By` 标记信息，例如下面这个示例 commit message：

    ```text
    modules: Add a new module

    This module provides a new feature that allows users to do something useful.

    Co-Authored-By: Alice <alice@example.com>
    Co-Authored-By: Bob <bob@example.com>
    ```

    在显示这个 commit 时，常见的 Git 平台（GitHub、GitLab 等）会自动识别 `Co-Authored-By` 并显示出来。

    诸如 Linux 内核等大型项目可能会使用类似的方式标记更多的信息，例如 `Reported-by`、`Tested-by`、`Reviewed-by` 等。

而 tree 对象的内容如下：

```shell
$ git cat-file -p 367ba031c357a771f2444048db71d109ec7e76d3
040000 tree 9ffaaee6a500ec6fe9a8becced39bfcadca6320a	.github
100644 blob 9331f5dd8db34e1cdc48fe663d662be8c976074c	.gitignore
100644 blob 6ddd90df33d0b98e704b71f33910ae91152bb005	.markdownlint.jsonc
100644 blob 7cdbe0b482f604a06a0988dad8877ae8d9257f7d	LICENSE
100644 blob ab9868d501db1eba893afcff8cb428d9a0cdf534	Makefile
100644 blob edc9f746d77a497fb08ba2dfac6bdf194b230c12	README.md
040000 tree e4de763b60a9a9a2ddd5cbf56591e3d187da7d0a	docs
040000 tree 4afa16d4c6461b534a002b432bdc5218e8826229	includes
100644 blob 982322412bf8c459de35408c255358ca64705e36	mkdocs.yml
100644 blob 81ed11cbdb707e57b178605d5aff73fdfa8b0dc4	requirements.txt
040000 tree a0a863b399b5255c497d35837c2371e3b7f0ed36	scripts
```

可以看到，tree 对象就是其对应目录的文件列表。

#### Ref {#git-ref}

引用（Ref）是一个指向对象（commit）的指针，存储在 `.git/refs` 目录下。一般有以下几种引用：

- 本地分支（`refs/heads`）
- 远程分支（`refs/remotes`）
- Tag（`refs/tags`）

可以直接通过 `cat` 的方式查看引用对应的对象 SHA-1 值，例如查看本地 `master` 分支对应的 commit：

```shell
$ cat .git/refs/heads/master
d959e182468be92957bd175d189472de91f614c8
```

除此之外，有一些特殊的（间接的）引用，对应的文件位于 `.git/` 下：

- `HEAD`：指向当前所在（你正在操作的）分支的引用。
- `ORIG_HEAD`：指向上一次操作前的 HEAD。
- `FETCH_HEAD`：指向上一次 `git fetch` 操作的结果。
- `MERGE_HEAD`：指向正在合并的分支。

其中最重要的是 `HEAD`。例如，`git checkout some-branch` 就会将 `HEAD` 指向 `refs/heads/some-branch`；而 `git reset --hard HEAD~1` 就会将 `HEAD` 指向 `HEAD~1`（同时更新工作目录下面的文件）。

!!! tip "HEAD~n"

    `HEAD~n` 表示 `HEAD` 的第 n 个父提交（前 n 个提交）。

!!! question "比较差异"

    如果需要比较当前 commit 相比上一个 commit 修改了哪些东西，应该输入的命令是？

!!! tip "refspec"

    你可能会在 `.git/config` 或者其他人写的 `git fetch` 等命令中看到以 `:` 分割的类似下面的东西：

    ```text
    +refs/heads/*:refs/remotes/origin/*
    ```

    这被称为 "refspec"，基本格式为 `<source>:<destination>`，表示从 `<source>` 获取对象并存储到 `<destination>`。如果 `<source>` 以 `+` 开头，则表示强制覆盖。上面的例子表示将远程仓库中 `refs/heads` 下的所有分支获取到本地的 `refs/remotes/origin` 下，即 `git fetch` 的默认行为。

    `git push` 同样也可以接受 refspec，默认的 `push.default` 配置项的值为 `simple`，表示将当前分支推送到与其同名的远程分支，相当于 `refs/heads/<some-branch>:refs/heads/<some-branch>`（把 `<source>` 的对象推送到远程的 `<destination>` 上）。

    更多信息可阅读 [Git Book 的 10.5 节](https://git-scm.com/book/en/v2/Git-Internals-The-Refspec) 与 [git-fetch(1)][git-fetch.1]。

!!! tip "`git reflog`"

    Reflogs（Reference logs）记录了 git 操作中 ref 的更新历史，在需要从误操作恢复，或确认之前操作给 ref 带来的变化时非常有用。例子参考 [Hackergame 2023 的 "Git? Git!" 一题](https://github.com/USTC-Hackergame/hackergame2023-writeups/tree/master/official/Git%20Git!)。

#### Remote {#git-remote}

绝大部分时候我们都有本地与远程仓库交互的需求，因此这里也介绍与 remote 相关的内容。

默认情况下，remote 的名字是 `origin`，可以通过 `git remote` 查看当前的 remote 信息：

```shell
$ git remote
origin
```

比较常用的相关命令：

- `git remote add <name> <url>`：添加一个新的 remote
- `git remote get-url <name>`：获取 remote 的 URL
- `git remote set-url <name> <url>`：设置 remote 的 URL

可以使用 `git fetch <remote>` 从远程仓库拉取最新的 commit——注意这个命令**只会更新远程分支相关对象以及 ref**。之后可以使用 `git merge` 将远程分支合并到本地分支（并更新本地分支的 ref）。因此，`git pull origin master` 等价于 `git fetch origin master && git merge origin/master`。

!!! question "让本地分支与远程一致"

    有的时候，我们的本地分支做了一些操作，与远程不一致，此时需要让本地分支与远程一致，那么怎么做呢？

    提示：如果希望让远程和本地一致，那么可以 `git push -f`，但是 `git pull -f` 是**不正确的**。你可能需要 `git fetch` 与 `git reset`。

#### Staging Area {#git-staging}

在运行 `git status` 的时候，会看到类似如下的输出：

```shell
$ git status
On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   docs/dev/git.md

no changes added to commit (use "git add" and/or "git commit -a")
```

这里的 "Changes not staged for commit" 指的是工作目录下的修改还没有被添加到 staging area（暂存区，也叫 index）中。常用的诸如 `git add`、`git rm --cached` 等命令就是用来在 staging area 中添加、删除文件的。

### 本地配置 {#git-config-file}

!!! note "配置文件"

    Git 的配置文件一般存放于 `~/.gitconfig` 或 `~/.config/git/config` 中, 可以使用 `git config --global --edit` 快速打开配置文件, 你可以直接拷贝下面的内容。

    下文中会讲解部分配置的作用及注意事项。

!!! warning "缩进问题"

    下面的文档中，`.gitconfig` 的配置文件均使用 4 个空格而不是 Tab 进行缩进。

#### 常用别名 {#git-alias}

```ini
[alias]
    aliases = !git config --get-regexp alias | sed -re 's/alias\\.(\\S*)\\s(.*)$/\\1 = \\2/g'
    ci = commit
    co = checkout
    st = status
    lg = log --graph --date=relative --pretty=tformat:'%Cred%h%Creset -%C(auto)%d%Creset %s %Cgreen(%an %ad)%Creset'
    oops = commit --amend --no-edit
    reword = commit --amend
    push-with-lease = push --force-with-lease
    uncommit = reset --soft HEAD~1
```

!!! tip "部分别名介绍"

    `git commit --amend` 用来修改上一个 commit 的内容（包括 commit 消息）：你可以将新的修改 stage 后使用该命令修改上一个 commit。如果添加了 `--no-edit`，就会跳过消息编辑。

    `git push --force-with-lease` 在 force push 之前先检查 remote 的状态，如果 remote 有本地不存在的新提交，该命令就会阻止此次 force push 操作。

#### 常用配置 {#git-config}

```ini
[color]
    ui = auto
[color "branch"]
    upstream = green
    remote = red
[core]
    editor = nvim
    excludesfile = ~/.gitignore_global
[commit]
    template = ~/.gitmessage
[pull]
    ff = only
[push]
    default = upstream
    followTags = true
[tag]
    sort = version:refname
```

我们也将上述的 `.gitconfig` 正确使用 Tab 缩进的版本放在 [这里](../assets/gitconfig_sample). 使用如下命令可以快速将我们提供的模板放入你的配置文件中：

```bash
curl -sS https://201.ustclug.org/assets/gitconfig_sample >> ~/.gitconfig
```

### gitignore {#git-gitignore}

GitHub 在 [这里](https://github.com/github/gitignore) 提供了一些常见的 `.gitignore` 文件，对于较为复杂的项目，也可以使用[gitignore.io](https://www.gitignore.io/) 生成。

!!! note "仅本地的 gitignore"

    本地的 `.git/info/exclude` 起到与 `.gitignore` 相同的作用，但是不会被提交到版本库中，适用于以下的情况：

    - 项目不允许修改 `.gitignore`
    - 目录名称本身包含敏感信息
    - 不希望 `.gitignore` 参与到版本控制中

    详细的文档可以参考[这里](https://git-scm.com/docs/gitignore#_description)。

#### Global gitignore {#git-global-gitignore}

对于一些常见的文件类型，可以在全局配置文件中指定：

```ini
[core]
    excludesfile = ~/.gitignore_global
```

```txt
# ~/.gitignore_global
*~
.DS_Store # for macOS
.idea
*.cache
.vscode
```

### Git Hook {#git-hooks}

对于一些重复性的工作（例如格式化代码、检查代码风格等），可以使用 Git Hook 来自动化。

一个叫较为成熟的框架是 [pre-commit](https://pre-commit.com/)，它支持多种语言和工具，例如 `black`、`flake8`、`eslint` 等，[这里](https://github.com/pre-commit/pre-commit-hooks) 提供了一些常用的 hook.

!!! note "如果只需要在 commit 后运行一段脚本"

    可以按照如下方法进行配置：
    ```bash
    # 在项目根目录下创建 .git/hooks/post-commit
    touch .git/hooks/__hook_name__
    chmod +x .git/hooks/__hook_name__
    ```

    ```bash
    # .git/hooks/post-commit
    #!/bin/bash

    # 在这里写入你的脚本
    for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
        black $file
    done
    ```

### 部分 clone {#partial-clone}

Git 支持三种部分 clone 的方式：

- blobless，不 clone HEAD 未涉及的 blob：`git clone --filter=blob:none <url>`
- treeless，不 clone HEAD 未涉及的 blob 和 tree：`git clone --filter=tree:0 <url>`
- shallow，不 clone HEAD 未涉及的 blob、tree 和 commit（**不推荐**）：`git clone --depth=1 --single-branch <url>`

在网络上常见的部分 clone 方式为 `--depth=1`，但是请注意：**`--depth=1` 在后续更新时，会给服务器和网络带宽带来非常大的负担，因此建议仅在用完即删的场景下使用**。因为 shallow clone 没有存储历史信息，在某些情况下，服务器需要索引全部历史信息，并且这一过程难以优化。一个知名的例子是：[由于 shallow clone 给服务器带来的压力过大，GitHub 勒令要求 Homebrew 不允许 shallow clone](https://github.com/Homebrew/brew/pull/9383)。

有关更多内容，可阅读 [Get up to speed with partial clone and shallow clone](https://github.blog/open-source/git/get-up-to-speed-with-partial-clone-and-shallow-clone/)。

### Git Submodule {#git-submodule}

Submodule 可以用来添加外部项目，例如向一个 C++ 项目中添加 Eigen：

```bash
git submodule add https://gitlab.com/libeigen/eigen.git src/eigen
```

如果已经 clone 到了子目录 `src/eigen` 下，可以通过如下方法添加：

```bash
git rm --cached -f src/eigen # if you've already added it to the index
git submodule add <url_of_eigen> src/eigen
```

初始化、更新 submodule 等操作则使用 `git submodule update` 命令：

```bash
git submodule update --init --recursive # clone 后初始化并拉取 submodule
git submodule update --remote --recursive # 更新 submodule 到远程最新版本
```

### Stash {#git-stash}

有的时候，我们在工作目录中进行了一些修改，还没有 commit（例如还没有完全完成），但是需要切换到其他分支进行一些操作。这时可以使用 `git stash` 将当前的修改放在 stash 中，操作完成后，可以使用 `git stash pop` 将修改恢复到工作目录中。

### 交互式 stage {#git-add-patch}

你是否有时一时兴起，写了或者改了很多很多代码，但是又不想把所有修改一股脑塞进一个 commit 里面？虽然 `git add` 可以选择文件，每次只 commit 指定的文件，但很多时候在一个文件里面会有多个修改，怎么把这些修改「拆开来」呢？

此时可以使用 `git add -p` 来选择指定的修改，该命令会将文件中的修改分成多个块（hunk），并询问你是否将该块添加到 staging area 中，如以下所示：

```diff
diff --git a/docs/dev/git.md b/docs/dev/git.md
index 80c4501..4085b25 100644
--- a/docs/dev/git.md
+++ b/docs/dev/git.md
@@ -114,6 +114,10 @@ d959e182468be92957bd175d189472de91f614c8

     `HEAD~n` 表示 `HEAD` 的第 n 个父提交（前 n 个提交）。

+!!! question "比较差异"
+
+    如果需要比较当前 commit 相比上一个 commit 修改了哪些东西，应该输入的命令是？
+
 #### Remote {#git-remote}

 绝大部分时候我们都有本地与远程仓库交互的需求，因此这里也介绍与 remote 相关的内容。
(1/4) Stage this hunk [y,n,q,a,d,j,J,g,/,e,p,?]?
```

如果有多个修改在一个 hunk 中，可以输入 `s` 将该 hunk 拆分成多个 hunk。如果这样都无法拆分，也可以输入 `e` 手动选择需要 stage 的内容。

### Rebase 与 Merge {#git-rebase-merge}

一般来说，我们希望保持项目有线性的提交历史（即不包含有多个 parent 的 merge commit），这样可以更容易地追溯问题，因此推荐使用 `rebase` 来合并分支。

```bash
git checkout -b feature
git commit -a --allow-empty -m "feat: aaaaaa"
git checkout master
git commit -a --allow-empty -m "feat: bbbbbb"
git checkout feature
git rebase master
```

如果你或者你的团队对线性历史有需求，通过如下设置，可以使得 `rebase` 成为 `git pull` 时候的默认行为。这样可以防止与其他人在同一分支合作时，出现大量的 merge commit：

```ini
[pull]
    rebase = true
```

或者也可以限制 `git pull` 只能进行 fast-forward，在出现分叉时用户可以手动 `git pull --rebase`，或者使用其他解决的方式：

```ini
[pull]
    ff = only
```

!!! question "更新一个有修改的本地仓库"

    以下是一个现实的例子：某个代码 git 仓库（存储在 GitHub 上）的 `master` 分支部署在一台服务器上，并且在该服务器上不仅做了一些额外的 commit 用来记录一些服务器相关的配置，还有一些没有被 stage 的文件。现在该代码仓库在 GitHub 上的 `master` 分支有一些新的更新 commit（例如更新了依赖，修复了 bug 等），那么如何将这些 commit 部署在该服务器上呢？

    提示：你可能会需要 `git fetch`、`git stash` 与 `git rebase`。

!!! tip "交互式 rebase"

    `git rebase` 另一个重要的功能是修改 commit 历史记录。使用 `git rebase -i HEAD~n` 来修改历史以来的 n 个 commit。在输入命令后，git 会打开编辑器，将 commit 从旧到新排序，显示类似如下的内容：

    ```txt
    pick b9c96cc Install XDG Desktop Portal
    pick d20fcf1 Set 2048m mem when running qemu
    pick 74fd856 Add gnome-software; clean comments

    # Rebase ebb0dcf..74fd856 onto ebb0dcf (3 commands)
    #
    # Commands:
    # p, pick <commit> = use commit
    # r, reword <commit> = use commit, but edit the commit message
    # e, edit <commit> = use commit, but stop for amending
    # s, squash <commit> = use commit, but meld into previous commit
    # f, fixup [-C | -c] <commit> = like "squash" but keep only the previous
    #                    commit's log message, unless -C is used, in which case
    #                    keep only this commit's message; -c is same as -C but
    #                    opens the editor
    # x, exec <command> = run command (the rest of the line) using shell
    # b, break = stop here (continue rebase later with 'git rebase --continue')
    # d, drop <commit> = remove commit
    # l, label <label> = label current HEAD with a name
    # t, reset <label> = reset HEAD to a label
    # m, merge [-C <commit> | -c <commit>] <label> [# <oneline>]
    #         create a merge commit using the original merge commit's
    #         message (or the oneline, if no original merge commit was
    #         specified); use -c <commit> to reword the commit message
    # u, update-ref <ref> = track a placeholder for the <ref> to be updated
    #                       to this position in the new commits. The <ref> is
    #                       updated at the end of the rebase
    #
    # These lines can be re-ordered; they are executed from top to bottom.
    #
    # If you remove a line here THAT COMMIT WILL BE LOST.
    #
    # However, if you remove everything, the rebase will be aborted.
    #
    ```

    比如说，你想合并最近 3 个 commit 到 1 个，那么在编辑器中将上面的内容修改为如下，保存并退出即可：

    ```text
    pick b9c96cc Install XDG Desktop Portal
    squash d20fcf1 Set 2048m mem when running qemu
    squash 74fd856 Add gnome-software; clean comments
    ```

    交互式 rebase 的其他用法请参考相关文档。

!!! tip "解决冲突"

    在合并其他人的分支时，如果你和其他人的分支用不同的方式修改了相同的部分，那么就会出现冲突。当出现 git 无法处理的冲突时，合并会停在出现冲突的 commit 上，并且提示你解决冲突。出现冲突的文件类似如下：

    ```text
    <<<<<<< HEAD
    This is your own changes.
    ========
    This is the changes from the other branch.
    >>>>>>> other-branch
    ```

    可以看到，这里同时给出了双方的修改，解决冲突需要：
    
    - 手动修改文件到预期的内容（记得把 `<<<<<<<`、`=======` 和 `>>>>>>>` 删除掉！）
    - 然后 `git add` 该文件
    - 最后根据是 merge 还是 rebase 操作，使用 `git merge --continue` 或 `git rebase --continue` 继续合并（可以使用 `git status` 查看当前的状态）
    - 如果不想解决了，可以使用 `git merge --abort` 或 `git rebase --abort` 取消合并操作

    可以使用 pre-commit 的 [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks?tab=readme-ov-file#check-merge-conflict) 来避免不小心把未解决的冲突 commit 到仓库里。

!!! tip "`git commit --fixup`"

    git 提供了 fixup 功能，可以直接向指定的 commit 添加修改，并且在 rebase 时自动合并。一个常见的场景是：在编写 PR 时需要保证每个 commit 有意义、功能完整，同时需要向 PR 里之前的 commit 添加修复，此时使用 fixup 功能会很方便。方法如下：

    ```bash
    # 先 stage 修改，然后：
    git commit --fixup <commit>
    ```

    此时会生成一个以 `fixup! <original commit message>` 命名的 commit。之后可以使用如下命令进行 rebase：

    ```bash
    # 需要包含 fixup 的目标 commit
    git rebase -i --autosquash <base>
    ```

### Bisect {#git-bisect}

在调试问题时，有时会出现这样的情况：某个 bug 在旧版本没有出现，但是在新版本出现了，或者某个问题在旧版本存在，新版本不存在，同时需要搞清楚具体是哪一个 commit 导致/修复了对应的问题。一个一个 commit 编译测试显然工作量实在太大，此时 `git bisect` 就可以起到很大的帮助。在使用 bisect 时，需要提供一个 "good"（旧版本）commit 和一个 "bad"（新版本）commit：

```console
git bisect start
git bisect good <old-commit>
git bisect bad <new-commit>
```

之后 `git bisect` 就会帮助你做二分搜索，跳转到两者中间的 commit 以供测试，之后提供 `git bisect good` 或者 `git bisect bad` 引导 git 搜索，最终找到对应的 commit。

!!! question "good or bad?"

    有时候我们会需要确认哪个 commit **修复**（而不是导致）了问题，但是 `git bisect` 默认 good 需要早于 bad，直接 `git bisect start` 的话很容易误操作。请阅读 [git-bisect(1)][git-bisect.1] 了解应该如何处理此类情况。

### Commit Message Convention {#git-commit-message}

对于多人协作的项目，良好的 commit message 是非常重要的。胡乱使用诸如 `update`、`fix`、`change` 等无意义的 Commit Message，会使得项目的历史记录变得难以理解，也会给后续的维护带来困难。

!!! note "Conventional Commits"

    一种常见的 Commit Message 格式是 [Conventional Commits](https://www.conventionalcommits.org/)，它的格式是：

    ```txt
    <type>[optional scope]: <description>

    [optional body]

    [optional footer(s)]
    ```

    其中：

    - `type` 是 commit 的类型，可以是 `feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore` 等。
    - `scope` 是 commit 的作用域
    - `description` 是 commit 的简要描述
    - `body` 是 commit 的详细描述，通常会引用 issue、解释修改的原因等
    - `footer` 通常用于引用 issue、关闭 issue 等，例如 `Closes #123`，也可以用于指定 breaking change 等

    值得注意的是，以上规范仅仅只是推荐，实际使用时可以根据项目的实际情况进行调整，例如本文档所存放的[仓库](https://github.com/ustclug/Linux201-docs)是一个文档类的项目，一般情况下可以直接省略掉 `type`, 可用文档相对目录来替代，例如修改本文的 Commit Message 一般就写成 `dev/git: fix typo`.

!!! note "Commit Message 模板"

    即便不严格遵循上述规范，设置一个 commit message 模板也是非常有用的，例如，可以将 [这里的例子](https://gist.github.com/lisawolderiksen/a7b99d94c92c6671181611be1641c733#template-file) 添加到 `~/.gitmessage`：

    ```ini
    # ~/.gitconfig
    [commit]
        template = ~/.gitmessage
    ```

    添加后不要忘记在首行添加空行，这样 `git commit` 时无需新建一行。

## GitHub 使用技巧

### [GitHub CLI](https://cli.github.com/)

GitHub CLI 是 GitHub 官方提供的命令行工具，可以用于管理 GitHub 仓库、Issue、Pull Request 等。

例如，给 `ustclug/Linux201-docs` 修 bug 的流程可以简化为：

```bash
gh repo clone ustclug/Linux201-docs
git commit -a -m "fix: some bug"
gh pr create
```

其他常用的 GitHub CLI 命令包括：

- `gh repo view --web`：在浏览器中打开当前仓库
- `gh issue list`：列出当前仓库的 Issue
- `gh run watch`：查看当前仓库的 GitHub Actions 运行状态

??? note "`gh run watch`"

    默认情况下 `gh run watch` 需要手动选择关注的 GitHub workflow, 如果只想关注最新的 workflow 可以将如下函数添加到 `~/.bashrc` 或 `~/.zshrc`:

    ```bash
    watch_latest_run() {
      # Fetch the latest run ID using gh and jq
      local latest_run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')

      if [ -z "$latest_run_id" ]; then
        echo "No runs found."
        return 1
      fi

      # Pass the latest run ID to gh run watch
      gh run watch "$latest_run_id"
    }
    ```

    之后可以直接使用 `watch_latest_run` 命令即可。

### GPG 与 SSH 密钥签名 {#github-sign}

在默认配置下，SSH Key 只用来验证你是否有权限修改指定的仓库，但有些时候我们需要证明某个 commit 就是由你（而不是其他人）提交的，以验证 commit 的真实性，此时就需要对 commit **签名**。GPG Key 和 SSH Key 都可以用来签名。

在按照以下内容配置完成后，使用以下命令即可为 commit 和 tag 签名：

```shell
git commit -S ...
git tag -s ...
```

如果需要自动为所有 commit 和 tag 签名（不管是使用 GPG 还是 SSH 签名），则：

```shell
git config --global commit.gpgSign true
git config --global tag.gpgSign true
```

#### GPG 签名 {#github-gpg}

GitHub 对 GPG Key 的文档描述很详细，我们将其列在这里：

- [生成 GPG Key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key)
- [修改 GPG Key 信息](https://docs.github.com/en/authentication/managing-commit-signature-verification/associating-an-email-with-your-gpg-key)
- [设置 Git 使用 GPG Sign](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key)
- [在 GitHub 上关联 GPG Key](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account)

请注意备份 GPG Key, 并额外向其他 Key Server 发布 GPG Key, 以防止 GPG Key 丢失：

```bash
gpg --list-secret-keys --keyid-format LONG
gpg --armor --export <GPG Key ID> | tee gpg.key
gpg --keyserver keyserver.ubuntu.com --send-keys <GPG Key ID>
gpg --keyserver pgp.mit.edu --send-keys <GPG Key ID>
```

!!! warning "过期的 GPG Key"

    过期的 GPG Key 是可以更新的, 参考 [这个 StackOverflow 回答](https://superuser.com/a/1141251).
    在 GitHub 上 rotate 只需要删除旧的 GPG Key, 然后重新添加新的 GPG Key 即可.
    值得注意的是过期的 GPG Key 签名的 commit 依然会显示成 Verified, 因此**不要轻易删除过期的 GPG Key**.

#### SSH 签名 {#github-ssh}

在已经为账户添加了 SSH Key 的基础上，SSH 签名的配置就简单得多：

```shell
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/yourkey.pub
```

### Deploy Keys {#github-deploy-keys}

GitHub 的 deploy keys 功能允许用户对特定仓库添加只用于该仓库的 SSH key，在需要将仓库 clone 到其它机器，但又不希望该机器有用户的全部权限时很有用。但是，GitHub 不允许同一个 SSH key 用在多个仓库上，对于需要在同一机器上 clone 多仓库的场景带来了不便。

官方文档 [Managing deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys#using-multiple-repositories-on-one-server) 提供了一种方案。以下提供另一种不需要修改 `~/.ssh/config` 为每个仓库设置别名的方案。

1. 进入仓库的 `.git` 目录，在该目录下创建密钥对。

    ```shell
    cd .git
    # RSA key pair
    ssh-keygen -f ./id_rsa -t rsa -b 4096 -N ""
    # or ED25519 key pair
    ssh-keygen -f ./id_ed25519 -t ed25519 -N ""
    ```

2. 修改 `.git/config` 内容，在 `[core]` 这个 section 下添加：

    ```ini
    [core]
    	# ...
    	# RSA key pair
    	sshCommand = ssh -i .git/id_rsa
    	# or ED25519 key pair
    	sshCommand = ssh -i .git/id_ed25519
    ```

3. 将公钥（**以 `.pub` 结尾，别将私钥发给其他任何人！**）添加到仓库设置的 deploy keys 中。

之后就可以像普通的仓库一样，正常进行 `git` 操作了。

### Issue {#github-issue}

下面关于 Markdown 的特性并不限于 Issue，也适用于 Pull Request 等。

#### GitHub 链接 {#github-link}

我们以 [ustclug/mirrorrequest#213](https://github.com/ustclug/mirrorrequest/issues/213) 为例：

- 在 Issue 中，可以使用 `#` 来引用其他 Issue / PR，例如 `#133`
- 可以通过 `user/repo#issue_number` 的方式引用其他仓库的 Issue / PR，例如 `tuna/issues#341`
    - 当一个 PR 包含如下关键字，并且按照上述方法连接到一个 Issue 时，合并这个 PR 会关闭对应的 issue：

        ```txt
        close(s,d) #123
        fix(es, ed) #123
        resolve(s, d) #123
        ```

- 可以通过 GitHub Web 上 Copy permalink 的方式获取代码的链接，例如打开 [ustclug/mirrorrequest/README.md](https://github.com/ustclug/mirrorrequest/blob/master/README.md?plain=1) 后，可以选择某一行，点击左侧的菜单，选择 Copy permalink, 即可获得诸如 <https://github.com/ustclug/mirrorrequest/blob/f23dd1f1cbe81f01e4f878ac11ee064b6c7d70ec/README.md?plain=1#L1> 这样的链接。
    - 这样的链接可以在 Issue 中直接粘贴，会被以代码框的形式渲染到 Issue 中，方便其他人迅速了解问题。
    - 点击后也可以直接复制地址栏中的 URL，这样的链接总是指向某个 branch 或者 tag 的，而不是特定 commit，但这样的作法可能会导致链接失效。

#### GitHub Flavor Markdown {#github-gfm}

正如其他编辑器对 Markdown 的支持一样，GitHub 支持一个 Markdown 方言（超集）的写法，称为 [GitHub Flavor Markdown](https://github.github.com/gfm/)。

我们在这里介绍一些你可能感兴趣的 feature：

- [Mermaid 关系图](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)

    Mermaid 是一种简单且强大的关系图/流程图语法，例如可以通过如下方式创建一个简单的关系图：

    ````txt
    ```mermaid
    graph LR;
        A-->B;
        A-->C;
        B-->D;
        C-->D;
    ```
    ````

    ```mermaid
    graph LR;
        A-->B;
        A-->C;
        B-->D;
        C-->D;
    ```

- [MathJax 支持](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions)

    GitHub 通过 MathJax 支持 LaTeX 公式，可以通过 `$ \frac 12 $` 的形式创建行内公式， `$$ \frac 12 $$` 的形式创建块级公式。

- [进度跟踪](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-task-lists)

    在 Issue 正文中创建一个任务列表，例如：

    ```markdown
    - [x] Task 1 #123
    - [ ] Task 2
    ```

    - [x] Task 1 #123
    - [ ] Task 2

    此时可以将这个 Issue 转化为一个任务列表，方便追踪任务的进度，同时 `#123` 会被标记为 `Tracked by #xxx`。

#### Issue 模板 {#github-issue-template}

对于大型项目，使用 Issue template 可以使得 Issue 更加规范化，例如，可以在 `.github/ISSUE_TEMPLATE/bug_report.yml` 中添加如下内容：

```yaml
name: Bug Report
about: Create a report to help us improve
labels:
  - bug
body:
  - type: textarea
    id: bug-description
    attributes:
      label: Describe the bug
      description: A clear and concise description of what the bug is.
      placeholder: I'm always frustrated when...
    validations:
      required: true
```

可以参考 [ustclug/mirrorrequest/.../01-mirror-request.yml](https://github.com/ustclug/mirrorrequest/blob/master/.github/ISSUE_TEMPLATE/01-mirror-request.yml?plain=1), [GitHub 文档](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository).

### Pull Request {#github-pr}

对于维护者（Maintainer）来说，Pull Request 更像是 Merge Request, 他们会检查代码、测试代码、review 代码，然后将代码合并到主分支中。

GitHub 在 [这里](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request) 介绍了合并 PR 的方式，简单来说跟本地 merge / rebase 没有太大区别。

- PR 中仅有一个 commit 时，推荐使用 Rebase 合并 PR
- 当 PR 中包含多次 commit，但实际上应当合并为一个时（例如经过 Review 后），推荐使用 Squash 合并 PR
- 多次 commit 来提交新 feature 时，推荐使用 Merge 合并 PR

维护者有时会需要将 PR checkout 到本地以测试：

- 可以使用 GitHub CLI 的 `gh pr checkout` 命令快速完成

- 也可以采用手工方式：

    - 使用 `git fetch origin pull/1234/head:pr-1234` 的形式将编号为 1234 的 PR 对应的 HEAD 同步到本地的 `pr-1234` 分支
    - 之后 `git checkout pr-1234` 即可

!!! warning "只读分支"

    需要注意的是，远程的 `pull/<id>/head` 是只读的分支，如果需要写入其他人的 PR 分支，需要自行 `git remote add` 添加对方的仓库，并将其 PR 对应的分支添加到本地。

维护者可以在这个新分支中同步贡献者的新修改，如果 PR 设置为 "Allow edits from maintainers"，那么维护者也可以直接写入贡献者的 PR。

!!! note "在 Pull Request 之前：早期的邮件协作"

    在基于网页端的 Pull Request 出现之前，早期的 Git 使用邮件列表作为协作的主要方式。贡献者通过 `git send-email` 将补丁发送到邮件列表，维护者通过 `git am` 将补丁应用到代码库中。目前诸如 Linux Kernel 等项目仍然使用邮件列表作为主要的协作方式。

    本文不介绍相关使用方法。有兴趣的读者可以参考阅读由 [sourcehut](https://sourcehut.org/) 编写的 [git-send-email.io](https://git-send-email.io/) 与 [git-am.io](https://git-am.io/) 教程。一句题外话：sourcehut 与 GitHub、GitLab 等平台不同，它基于传统的邮件工作流，但是提供了简洁美观的网页界面。

!!! note "GitLab"

    GitLab 的 Merge Request 整体上与 GitHub 的 Pull Request 类似，不过 checkout 到本地的操作有所不同。可以使用 GitLab 提供的命令行工具 [glab](https://docs.gitlab.com/editor_extensions/gitlab_cli/)，也可以使用 `git fetch origin merge-requests/1234/head:mr-1234` 的方式将编号为 1234 的 MR 对应的 HEAD 同步到本地的 `mr-1234` 分支。

    以上内容也适用于自托管的 GitLab 实例。

!!! tip "便于同步 PR/MR 的参考 alias"

    ```ini title="~/.gitconfig"
    [alias]
        pr = !sh -c 'git fetch -u $1 +pull/$2/head:pr-$1-$2 && git checkout pr-$1-$2 && git reset --hard HEAD' -
        mr = !sh -c 'git fetch -u $1 +merge-requests/$2/head:mr-$1-$2 && git checkout mr-$1-$2 && git reset --hard HEAD' -
    ```

    使用例子：`git pr origin 1234`（GitHub）、`git mr origin 1234`（GitLab）。重复执行可从 PR/MR 中获取最新的修改。

    !!! question "`git pull`?"

        为什么这样得到的分支无法执行 `git pull`？如何修复这个问题？

    以上修改自 [Check out locally by adding a Git alias](https://docs.gitlab.com/user/project/merge_requests/merge_request_troubleshooting/#check-out-locally-by-adding-a-git-alias)。

    !!! question "参数说明"

        原始的 alias 如下：

        ```ini title="~/.gitconfig"
        [alias]
            pr = !sh -c 'git fetch $1 pull/$2/head:pr-$1-$2 && git checkout pr-$1-$2' -
            mr = !sh -c 'git fetch $1 merge-requests/$2/head:mr-$1-$2 && git checkout mr-$1-$2' -
        ```

        相比原始的 alias，这里的有什么变化？添加这些变化的目的是什么？是否有更好的解决方案？

### GitHub Actions {#github-actions}

GitHub Actions 是 GitHub 提供的 CI/CD 服务，可以用于自动化构建、测试、部署等。

!!! note "GitHub Actions Pricing"

    对于 Public 仓库，GitHub 提供了免费的服务，对于 Private 仓库，GitHub 提供了 2000 分钟的免费服务。

    关于计费问题，可以参考[这里](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions#included-storage-and-minutes)。

对于 GitHub Actions 的写法，只需要关心如下几件事情：

- 何时应当触发 Action：例如 `on: push, pull_request`
- 如何在 GitHub Actions 上搭建环境（例如安装依赖、配置环境变量等）
- 产物的存放位置：例如 `artifacts`、`release`

如果涉及到 Secret Key，还应当注意安全问题（限制触发条件、产物等）。

GitHub 在 [这里](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions) 提供了详细的文档。

!!! tip "本地运行 GitHub Actions"

    测试 CI 很多时候是件头疼的事情：要一遍又一遍 commit、push、观察是否运行正确，几乎是一种无尽的折磨——如果能在本地运行指定的 workflow 就好了！对于 GitHub Actions，可以使用 [act](https://github.com/nektos/act) 工具，其会调用 Docker 运行模拟 Actions 的环境，可以在本地快速测试。

#### Other CI/CD systems {#ci-cd}

以下是一些其他常用的 CI/CD 提供商，它们提供了类似的服务：

- [Travis CI](https://docs.travis-ci.com/)
- [Circle CI](https://circleci.com/docs/)
- [GitLab CI](https://docs.gitlab.com/ee/ci/)
- [Jenkins](https://www.jenkins.io/doc/)
- [Azure Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/)

考虑到 GitHub Actions 的免费额度，以及与 GitHub 的无缝集成等，已经足够满足大多数项目的需求，因此我们在这里不再详细介绍其他 CI/CD 系统。
