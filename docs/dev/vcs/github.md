---
icon: simple/github
---

# GitHub 使用技巧

!!! note "主要作者"

    [@tiankaima][tiankaima]、[@taoky][taoky]

!!! success "本文已完成"

## [GitHub CLI](https://cli.github.com/)

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

## GPG 与 SSH 密钥签名 {#github-sign}

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

### GPG 签名 {#github-gpg}

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

### SSH 签名 {#github-ssh}

在已经为账户添加了 SSH Key 的基础上，SSH 签名的配置就简单得多：

```shell
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/yourkey.pub
```

## Deploy Keys {#github-deploy-keys}

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

!!! tip

    Git 会在当前项目的「根目录」中执行 `ssh` 命令，这也是 `sshCommand` 中 `-i` 参数的相对路径的参照路径。

    本地 Git 仓库的「根目录」是指包含 `.git` 目录的目录，可以用以下命令查看：

    ```shell
    git rev-parse --show-toplevel
    ```

## Issue {#github-issue}

下面关于 Markdown 的特性并不限于 Issue，也适用于 Pull Request 等。

### GitHub 链接 {#github-link}

我们以 [ustclug/mirrorrequest#213](https://github.com/ustclug/mirrorrequest/issues/213) 为例：

- 在 Issue 中，可以使用 `#` 来引用其他 Issue / PR，例如 `#133`
- 可以通过 `user/repo#issue_number` 的方式引用其他仓库的 Issue / PR，例如 `tuna/issues#341`
    - 当一个 PR 包含如下关键字，并且按照上述方法连接到一个 Issue 时，合并这个 PR 会关闭对应的 issue：

        ```text
        close[s,d] #123
        fix[es, ed] #123
        resolve[s, d] #123
        ```

- 可以通过 GitHub Web 上 Copy permalink 的方式获取代码的链接，例如打开 [ustclug/mirrorrequest/README.md](https://github.com/ustclug/mirrorrequest/blob/master/README.md?plain=1) 后，可以选择某一行，点击左侧的菜单，选择 Copy permalink, 即可获得形如 <https://github.com/ustclug/mirrorrequest/blob/f23dd1f1cbe81f01e4f878ac11ee064b6c7d70ec/README.md?plain=1#L1> 这样的链接。
    - 这样的链接可以在 Issue 中直接粘贴，会被以代码框的形式渲染到 Issue 中，方便其他人迅速了解问题。
    - 点击后也可以直接复制地址栏中的 URL，这样的链接总是指向某个 branch 或者 tag 的，而不是特定 commit，但这样的作法可能会导致链接失效。

### GitHub Flavored Markdown {#github-gfm}

正如其他编辑器对 Markdown 的支持一样，GitHub 支持一个 Markdown 方言（超集）的写法，称为 [GitHub Flavored Markdown](https://github.github.com/gfm/)。

我们在这里介绍一些你可能感兴趣的 feature：

- [Mermaid 关系图](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)

    Mermaid 是一种简单且强大的关系图/流程图语法，例如可以通过如下方式创建一个简单的关系图：

    ````markdown
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

### Issue 模板 {#github-issue-template}

对于大型项目，使用 Issue template 可以使得 Issue 更加规范化。例如，你可以在仓库的 `.github/ISSUE_TEMPLATE/bug_report.yml` 文件中添加如下内容：

```yaml title=".github/ISSUE_TEMPLATE/bug_report.yml"
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

## Pull Request {#github-pr}

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

## GitHub Actions {#github-actions}

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

### Other CI/CD systems {#ci-cd}

以下是一些其他常用的 CI/CD 提供商，它们提供了类似的服务：

- [Travis CI](https://docs.travis-ci.com/)
- [Circle CI](https://circleci.com/docs/)
- [GitLab CI](https://docs.gitlab.com/ee/ci/)
- [Jenkins](https://www.jenkins.io/doc/)
- [Azure Pipelines](https://docs.microsoft.com/en-us/azure/devops/pipelines/)

考虑到 GitHub Actions 的免费额度，以及与 GitHub 的无缝集成等，已经足够满足大多数项目的需求，因此我们在这里不再详细介绍其他 CI/CD 系统。
