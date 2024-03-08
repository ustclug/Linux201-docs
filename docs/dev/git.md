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
    oops = commit --amend --no-edit # 修改上一次提交，(忘记添加文件)
    reword = commit --amend
    push-with-lease = push --force-with-lease # “安全”地 force push，（不会覆盖别人的提交）
    uncommit = reset --soft HEAD~1
```

#### 配置文件 {#git-config-file}

```ini
[color]
    ui = auto
[color "branch"]
    upstream = green
    remote = red
[push]
    default = upstream
    followTags = true
[tag]
    sort = version:refname
```

### Git Hook {#git-hooks}

TBC

### Git Submodule {#git-submodule}

TBC

### Rebase 与 Merge {#git-rebase-merge}

TBC

### Commit Message Convention {#git-commit-message}

TBC

### Global Gitignore {#git-global-gitignore}

TBC

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
