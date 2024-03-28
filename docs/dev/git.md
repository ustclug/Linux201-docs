# 版本管理与合作

!!! warning "本文仍在编辑中"

## Git 使用技巧

### 本地配置 {#git-config-file}

!!! note "配置文件"

    Git 的配置文件一般存放于 `~/.gitconfig` 或 `~/.config/git/config` 中, 你可以直接将下面的内容拷贝到你的配置文件中（如果没有，新建一个）。

    下文中会讲解部分配置的作用及注意事项。

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
[push]
    default = upstream
    followTags = true
[tag]
    sort = version:refname
```

### gitignore {#git-gitignore}

GitHub 在[这里](https://github.com/github/gitignore) 提供了一些常见的 `.gitignore` 文件，对于较为复杂的项目，也可以使用[gitignore.io](https://www.gitignore.io/) 生成。

!!! warning "`.env` 文件与 `.gitignore`"

    有些项目在开发的途中，可能引入`.env`用于存放测试环境的配置，这类文件通常包含敏感信息，因此应该被加入到`.gitignore`中。

    请注意，回退时 `.env` 会被忽略，如果此时 `.gitignore` 不含 `.env`， `.env` 会被视作 untracked files。

    ```mermaid
    classDiagram
    direction LR
    CommitA --|> CommitB : "Add .env to .gitignore"
    CommitB --|> CommitA_revert : reset --hard
    CommitA: .gitignore (without .env)
    CommitB: .gitignore (including .env)
    CommitB: .env
    CommitA_revert: .env (untracked)
    CommitA_revert: .gitignore (without .env)
    ```

    此时需手动将`.env` 移除版本控制，例如 `mv ./.env ../.env.bk` 以防止`.env`被提交。

!!! note 仅本地的 gitignore

    本地的 `.git/info/exclude` 起到与 `.gitignore` 相同的作用，但是不会被提交到版本库中，适用于以下的情况：

    - 项目不允许修改 `.gitignore`
    - 你的工作流程中有一些特殊的文件不希望被提交

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

如果只需要在 commit 后运行一段脚本，可以按照如下方法进行配置：

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

### Rebase 与 Merge {#git-rebase-merge}

TBC

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

    值得注意的是，以上规范仅仅只是推荐，实际使用时可以根据项目的实际情况进行调整，例如本文档所存放的[仓库](https://github.com/ustclug/Linux201-docs)是一个文档类的项目，一般情况下可以直接省略掉`type`.

!!! note "Commit Message 模板"

    即便不严格遵循上述规范，设置一个 commit message 模板也是非常有用的，例如，可以将 [这里的例子](https://gist.github.com/lisawolderiksen/a7b99d94c92c6671181611be1641c733#template-file) 添加到 `~/.gitmessage`：

    添加后不要忘记在首行添加空行，这样 `git commit` 时无需新建一行。

    ```ini
    # ~/.gitconfig
    [commit]
        template = ~/.gitmessage
    ```

## GitHub 使用技巧

### GPG 签名 {#github-gpg}

TBC

### Issue {#github-issue}

#### Issue 模板 {#github-issue-template}

TBC

### Pull Request {#github-pr}

TBC

### GitHub Actions {#github-actions}

TBC

#### Other CI/CD systems {#ci-cd}
