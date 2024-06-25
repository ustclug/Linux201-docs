# Linux 201 进阶教程

## 如何构建？

1. `python3 -m venv venv`
2. `. venv/bin/activate`
3. `pip install -r requirements.txt`
4. `mkdocs serve`

## 格式检查

### Autocorrect

从 <https://github.com/huacnlee/autocorrect/> 安装后，运行 `autocorrect --lint` 即可。`autocorrect --fix` 可以自动修复问题。

### Markdownlint-cli2

对应仓库为 <https://github.com/DavidAnson/markdownlint-cli2>。运行 `markdownlint-cli2 docs/**/*.md README.md` 即可。添加 `--fix` 可以自动修复问题。

## 许可

本文档以 Creative Commons BY-NC-SA 4.0 协议发布。详情请见 [LICENSE](LICENSE)。
