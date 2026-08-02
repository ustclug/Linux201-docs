---
icon: simple/clickhouse
---

# ClickHouse

!!! note "主要作者"

    [@iBug][iBug]

!!! warning "本文编写中"

[ClickHouse](https://clickhouse.com/)（也称作 CH、CK、<s>:material-cursor-default-click::material-home:点击房子</s>）是一个开源的列式数据库，主要用于 OLAP 查询，支持大规模数据集和实时分析。

## 安装

### Docker 部署

Docker Hub 上有两个 ClickHouse 仓库：

- [`clickhouse`](https://hub.docker.com/_/clickhouse)（a.k.a. `library/clickhouse`）：由 Docker 维护的 Docker 官方镜像
- [`clickhouse/clickhouse-server`](https://hub.docker.com/r/clickhouse/clickhouse-server)：由 ClickHouse 维护的镜像

两份镜像在功能和管理方式上没有区别，但 ClickHouse 维护的镜像能够更快地跟进新的 ClickHoue 软件版本，也是更加热门的选项。
本文后续将默认采用 `clickhouse/clickhouse-server` 仓库。
截至本文编写时，ClickHouse 最新的 LTS 版本为 `26.3`，使用 Docker Compose 部署 ClickHouse 的示例配置如下：

```yaml title="docker-compose.yaml"
name: clickhouse

services:
  clickhouse:
    image: clickhouse/clickhouse-server:26.3
    container_name: clickhouse
    restart: unless-stopped
    ports:
      - "8123:8123"  # HTTP 端口
      - "9000:9000"  # TCP 端口
      # "9009:9009"  # 集群内的 TCP 通信端口
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    environment:
      CLICKHOUSE_DB: ${CLICKHOUSE_DB}
      CLICKHOUSE_USER: ${CLICKHOUSE_USER}
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
    volumes:
      - /srv/clickhouse/data:/var/lib/clickhouse
      - /srv/clickhouse/logs:/var/log/clickhouse-server
      # ./init:/docker-entrypoint-initdb.d:ro
      # ./config/users.xml:/etc/clickhouse-server/users.d/users.xml:ro
```

如果 `/srv/clicikhouse/data` 目录为空的话，ClickHouse 会在首次启动时根据提供的环境变量自动创建默认数据库和用户，该用户具有读写数据库的权限，但没有管理权限（创建其他数据库、创建用户等）。如果需要创建其他数据库或用户，可以在 `docker-compose.yaml` 中挂载初始化 SQL 脚本，或者在容器中使用 `clickhouse-client` 命令行工具执行 SQL 语句。

### 初始化

```sql title="01-mirrors.sql"
CREATE TABLE mirrors.access_log (
    `timestamp` Float64,
    `event_time` DateTime64(3, 'UTC') MATERIALIZED fromUnixTimestamp64Milli(toInt64(timestamp * 1000)),
    `clientip` String,
    `serverip` LowCardinality(String),
    `method` LowCardinality(String),
    `scheme` LowCardinality(String),
    `url` String,
    `status` UInt16,
    `size` UInt64,
    `resp_time` Float32,
    `http_host` LowCardinality(String),
    `referer` String,
    `user_agent` String,
    `request_id` String DEFAULT hex(cityHash64(tuple(event_time, ip))),
    `proto` LowCardinality(String),
    `proxied` LowCardinality(String),
    `alpn` LowCardinality(String),
    -- `ip` IPv6 MATERIALIZED if(isIPv4String(clientip), IPv4ToIPv6(toIPv4OrDefault(clientip)), toIPv6OrDefault(clientip)),
    `source` LowCardinality(String) DEFAULT '',
    -- `repo` LowCardinality(String) MATERIALIZED extract_repo("url")
)
ENGINE = ReplacingMergeTree
PARTITION BY toDate(event_time)
PRIMARY KEY (event_time)
ORDER BY (event_time, request_id)
SETTINGS index_granularity = 8192;
```

## 数据采集

### Vector

USTC Mirrors 使用的 Vector 配置参考：

```yaml title="vector.yaml"
sources:
  mirror_logs:
    type: file
    include:
      - /var/log/nginx/mirrors/access_json.log
      - /var/log/nginx/403/access_json.log
      - /var/log/nginx/cacheproxy/*_json.log
    read_from: end
    fingerprint:
      strategy: device_and_inode

transforms:
  parsed_logs:
    type: remap
    inputs:
      - mirror_logs
    source: |
      filename = .file
      . = parse_json!(string!(.message))
      .source = ""
      if contains!(filename, "/mirrors/") {
        .source = "mirrors"
      } else if contains!(filename, "/403/") {
        .source = "403"
      } else if contains!(filename, "/cacheproxy/") {
        .source = "cacheproxy"
      }

sinks:
  mirrorlog:
    type: clickhouse
    inputs:
      - parsed_logs
    endpoint: http://localhost:8123/
    auth:
      strategy: basic
      user: xi
      password: "Xaleid<>scopiX"
    database: mirrors
    table: access_log
    format: json_each_row
    buffer:
      type: disk
      max_size: 1073741824
```
