# 版本管理与合作

!!! warning "本文仍在编辑中"

## Git 使用技巧

### 本地配置 {#git-config}

Git 的配置文件一般存放于 `~/.gitconfig` 或 `~/.config/git/config` 中。

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

#### 配置文件 {#git-config-file}

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
```

### Git Hook {#git-hooks}

TBC

### Git Submodule {#git-submodule}

TBC

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

即便不严格遵循上述规范，设置一个 commit message 模板也是非常有用的，例如，可以将 [这里的例子](https://gist.github.com/lisawolderiksen/a7b99d94c92c6671181611be1641c733#template-file) 添加到 `~/.gitmessage`：

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
