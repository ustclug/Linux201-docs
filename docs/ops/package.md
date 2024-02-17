# 包管理器

Debian / Ubuntu 使用的包管理系统是由 Debian 开发的 Debian 软件包管理系统（dpkg）和由 Ubuntu 开发的高级包装工具（Advanced Packing Tool，APT）。`dpkg` 和 `apt` 都是命令行工具，但是另有 aptitude 和 synaptic 等图形界面工具可以使用。

APT 和 dpkg 的分工大致如下：

- dpkg 负责直接操作软件包，如安装、卸载、运行配置脚本等，同时一定程度上处理软件包的依赖关系。
- APT 负责管理软件包，如更新和维护仓库（即软件包的源）、下载软件包、解决依赖关系、提供搜索和查询功能等。APT 在分析软件包依赖并下载软件包后，会调用 dpkg 完成剩下的工作。
