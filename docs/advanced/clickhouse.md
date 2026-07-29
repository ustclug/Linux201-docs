---
icon: simple/clickhouse
---

# ClickHouse

!!! warning "本文编写中"

## 安装

### Docker 安装

Docker Hub 上有两个 ClickHouse 仓库：

- [`clickhouse`](https://hub.docker.com/_/clickhouse)（a.k.a. `library/clickhouse`）：由 Docker 维护的 Docker 官方镜像
- [`clickhouse/clickhouse-server`](https://hub.docker.com/r/clickhouse/clickhouse-server)：由 ClickHouse 维护的镜像

两份镜像在功能和管理方式上没有区别，但 ClickHouse 维护的镜像能够更快地跟进新的 ClickHoue 软件版本，也是更加热门的选项。
本文后续将以 `clickhouse/clickhouse-server` 为示例编写。
