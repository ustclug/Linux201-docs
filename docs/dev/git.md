---
icon: simple/git
---

# 版本管理与合作

!!! warning "Pending Review"

## Git 使用技巧

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
curl -sS  https://201.ustclug.org/assets/gitconfig_sample >> ~/.gitconfig
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

一般来说，我们希望保持项目有线性的提交历史，这样可以更容易地追溯问题，因此推荐使用 `rebase` 来合并分支。

```bash
git checkout -b feature
git commit -a --alow-empty -m "feat: aaaaaa"
git checkout master
git commit -a --alow-empty -m "feat: bbbbbb"
git checkout feature
git rebase master
```

通过如下设置，可以使得 `rebase` 成为默认行为：

```ini
[pull]
    rebase = true
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

    值得注意的是，以上规范仅仅只是推荐，实际使用时可以根据项目的实际情况进行调整，例如本文档所存放的[仓库](https://github.com/ustclug/Linux201-docs)是一个文档类的项目，一般情况下可以直接省略掉`type`, 可用文档相对目录来替代，例如修改本文的 Commit Message 一般就写成 `dev/git: fix typo`.

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

### GPG 签名 {#github-gpg}

SSH Key 只用来验证 push 环节的身份，而 GPG Key 则用来验证 Commit 的真实性。

GitHub 对 GPG Key 的文档描述很详细，我们将其列在这里：

- [生成 GPG Key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key)
- [修改 GPG Key 信息](https://docs.github.com/en/authentication/managing-commit-signature-verification/associating-an-email-with-your-gpg-key)
- [设置 Git 使用 GPG Sign](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key)
- [在 GitHub 上关联 GPG Key](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-gpg-key-to-your-github-account)

请注意备份 GPG Key, 并额外向其他 Key Server 发布 GPG Key, 以防止 GPG Key 丢失:

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

对于 Maintainer 来说，Pull Request 更像是 Merge Request, 他们会检查代码、测试代码、review 代码，然后将代码合并到主分支中。

GitHub 在 [这里](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request) 介绍了合并 PR 的方式，简单来说跟本地 merge / rebase 没有太大区别。

- PR 中仅有一个 commit 时，推荐使用 Rebase 合并 PR
- 当 PR 中包含多次 commit，但实际上应当合并为一个时（例如经过 Review 后），推荐使用 Squash 合并 PR
- 多次 commit 来提交新 feature 时，推荐使用 Merge 合并 PR

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

#### Other CI/CD systems {#ci-cd}

以下是一些其他常用的 CI/CD 提供商，它们提供了类似的服务：

- [Travis CI](https://docs.travis-ci.com/)
- [Circle CI](https://circleci.com/docs/)
- [GitLab CI](https://docs.gitlab.com/ee/ci/)
- [Jenkins](https://www.jenkins.io/doc/)
- [Azure Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/)

考虑到 GitHub Actions 的免费额度，以及与 GitHub 的无缝集成等，已经足够满足大多数项目的需求，因此我们在这里不再详细介绍其他 CI/CD 系统。
