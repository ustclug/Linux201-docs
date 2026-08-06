---
icon: simple/clickhouse
---

# ClickHouse

!!! note "主要作者"

    [@iBug][iBug]

!!! warning "本文编写中"

[ClickHouse](https://clickhouse.com/)（也称作 CH、CK、<s>:material-cursor-default-click::material-home:点击房子</s>）是一个开源的列式数据库，主要用于 OLAP 查询，支持大规模数据集和实时分析。

## 安装 {#install}

### Docker 部署 {#install-docker}

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
      nofile: # (1)
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

1. ClickHouse 在运行过程中会打开大量文件，默认的 `nofile` 限制通常是不够的，因此需要在 Docker Compose 配置中增加 `ulimits` 配置。

在同级目录下创建 `.env` 文件，根据 Docker Compose 配置指定合适的环境变量，运行 `docker compose up -d` 即可启动 ClickHouse 服务，并进行初始化（见下）。

### 初始化 {#initialization}

如果 `/srv/clickhouse/data` 目录为空的话，ClickHouse 会在首次启动时根据提供的环境变量和挂载的文件自动创建默认数据库和用户。其中：

- `CLICKHOUSE_DB` 用于在初始化时创建对应名称的数据库。
- `CLICKHOUSE_USER` 和 `CLICKHOUSE_PASSWORD` 这两个环境变量用于合成 ClickHouse 的 XML 配置文件中的 `<users>` 部分。
    - 这意味着如果你在数据库正常运行后修改了这两个环境变量并重建 ClickHouse 容器，ClickHouse 会使用新的值覆盖原有的用户配置。
    - 通过环境变量创建的用户具有读写数据库的权限，但没有管理权限（创建数据库和用户等）。
- 执行 `/docker-entrypoint-initdb.d` 目录下挂载的所有 `.sql` 文件。你可以通过 `docker-compose.yaml` 在此目录中挂载 SQL 脚本进行额外的初始化操作，例如创建其他数据库、表或用户。

在初始化完成后，你也可以在容器中使用 `clickhouse-client` 命令行工具执行 SQL 语句。

## 创建表 {#create-table}


USTC Mirrors 的 Nginx 访问日志格式为自定义的单行 JSON 格式（命名为 `ngx_json`），配置方式可以在 [Nginx](../ops/network-service/nginx.md#logging) 一页中找到，示例如下（经过格式化）：

??? example "访问日志示例"

    ```json
    {
        "timestamp": 1777114514.777,
        "clientip": "1.14.5.14",
        "serverip": "202.38.95.110",
        "method": "GET",
        "scheme": "https",
        "url": "/debian/dists/stable/InRelease",
        "status": 200,
        "size": 114514,
        "resp_time": 0.001,
        "http_host": "mirrors.ustc.edu.cn",
        "referer": "",
        "user_agent": "Debian APT-HTTP/1.3 (2.6.1)",
        "request_id": "0123456789abcdef0123456789abcdef",
        "proto": "HTTP/1.1",
        "proxied": "0"
    }
    ```

根据我们的 JSON 格式创建用于结构化存储日志的 ClickHouse 表的 SQL 语句如下：

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
    `source` LowCardinality(String) DEFAULT '',
    `ip` IPv6 MATERIALIZED toIPv6OrDefault(clientip),
    `repo` LowCardinality(String) MATERIALIZED extract_repo("url")
)
ENGINE = ReplacingMergeTree
PARTITION BY toDate(event_time)
PRIMARY KEY (event_time)
ORDER BY (event_time, request_id)
SETTINGS index_granularity = 8192;
```

这个表定义有以下几个特点：

- 根据 ClickHouse 的 convention，存储时间序列数据时，将主要的时间戳列命名为 `event_time`，并使用 `DateTime64(3)` 类型存储毫秒级时间戳（或者如果只需要秒级精度时，可以使用 `DateTime`）。原始的浮点数时间戳列 `timestamp` 仍然保留，方便通过 JSON 方式导入数据。
- 对于 `serverip` 等取值有限的列，使用 `LowCardinality(String)` 类型节省存储空间和提高查询性能。`LowCardinality` 类型会在内部创建一个哈希字典，从而减少重复存储的字符串数据。
    - 由于哈希字典本身存在一定的开销，因此一般不用于字符串以外的类型，或者取值范围非常大（数千到一万以上）的列。例如，尽管 `status` 列只有十几个可能的取值（HTTP 状态码），由于 UInt16 已经是非常紧凑的存储类型，且具有良好的查询性能，因此不使用 `LowCardinality`。
- 较旧的日志没有记录 `request_id`，因此该列使用 `DEFAULT` 生成一个哈希作为替代。
- 使用 ReplacingMergeTree 引擎，允许在导入重复日志时进行去重。
    - 重复行的判断依据是 `ORDER BY` 语句指定的列组合（即 `event_time`+`request_id`），因此在 ClickHouse 中，**「主键」通常指 `ORDER BY` 的定义**，而非望文生义的 `PRIMARY KEY`。
    - `PRIMARY KEY` 指定主键的一个前缀序列，作为 ClickHouse 在内存中维护稀疏索引（sparse index）的依据，通过排除不常用或不必要的列来减少内存占用。
- `PARTITION BY` 指定分区键，ClickHouse 会根据该列的值将数据划分为不同的分区，从而提高查询性能和管理效率。对于时间序列数据，通常根据数据量和查询模式选择合适的时间粒度进行分区。本文示例中使用 `toDate(event_time)` 按天分区。

### 自定义函数 {#user-defined-functions}

ClickHouse 支持自定义函数（User Defined Functions，简称 UDF），可以将常用的表达式封装成函数，减少编写 SQL 时的重复工作。

例如，为了方便从 URL 中提取镜像仓库名称，USTC Mirrors 定义了一个 `extract_repo` 函数：

```sql
-- 提取 URL path 中的第一段目录
CREATE FUNCTION extract_repo_dir AS (path) ->
if(
  match(path, '^/*[^/?]+/'),
  extract(path, '^/*([^/?]+)/'),
  '/'
);

CREATE FUNCTION extract_repo AS (path) ->
multiIf(
  has([
    'adoptium', 'alpine', 'anaconda', -- 一大串仓库名
    'zerotier',
    '/'
  ], extract_repo_dir(path)), extract_repo_dir(path),
  has(['assets', 'static', 'status', '.well-known'], extract_repo_dir(path)), '/',
  has(['misc'], extract_repo_dir(path)), 'ustclug',
  '<invalid>'
);
```

结合下面介绍的 MATERIALIZED 列，`extract_repo` 函数可以在数据插入时自动计算出 `repo` 列的值，方便后续按仓库归类查询和统计。

### 物化列 {#materialized-columns}

ClickHouse 的物化列（`MATERIALIZED` columns）是指在表中定义的列，其值由其他列的表达式计算得出，并在数据插入时自动计算和存储，是一种以空间换时间的思想。

在以上示例中，开头的 `event_time` 和最后两列 `ip` 和 `repo` 都是 MATERIALIZED 列：

- `event_time` 列通过将原始的浮点数时间戳 `timestamp` 转换为毫秒级时间戳并使用 `fromUnixTimestamp64Milli` 函数生成 `DateTime64(3)` 类型的时间列。
- `ip` 列将 `clientip` 列存储的字符串转换为 IPv6 地址，其中合法的 IPv4 地址也会被转换成 IPv4-mapped IPv6 地址（例如 `::ffff:127.0.0.1`）。
- `repo` 列使用一个自定义函数从 `url` 中提取镜像仓库名称。

默认情况下，MATERIALIZED 列不允许被插入数据，如果尝试插入的数据包含了 MATERIALIZED 的列，ClickHouse 会返回错误。
开启设置 `insert_allow_materialized_columns` 可以让 ClickHouse 忽略尝试插入到 MATERIALIZED 列的数据（采用计算结果），继续插入其他列的数据。

## 数据采集 {#data-collection}

将访问日志导入 ClickHouse 的方式有很多种，本节简单介绍主流的 [Vector.dev](https://vector.dev/) 采集器。

根据使用场景，Fluent Bit 和 Filebeat 也可以作为日志采集器。

### Vector

Vector 是 Datadog 开源的日志采集器，以 Rust 语言编写（因此非常轻量），支持多种数据源（sources）、转换（transforms）和输出（sinks），可以将日志数据从源头采集、转换后发送到 ClickHouse。Vector 可以[通过多种方式安装](https://vector.dev/docs/setup/installation/)，且支持通过 SIGHUP 信号重新加载配置文件。

Vector 的 [`file` 数据源](https://vector.dev/docs/reference/configuration/sources/file/)能够以类似 `tail -F` 的方式读取文件内容，并将每一行作为一个事件传递给下游处理器。File 数据源读取的每一行日志都包含一个 `message` 字段，存储了原始的文本内容，因此我们需要使用 `remap` 将其解析为 JSON 对象，并根据文件路径注入 `source` 字段，标记日志来源。

```yaml title="USTC Mirrors 使用的 Vector 配置参考"
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

为 sink 配置磁盘缓冲区可以在 ClickHouse 服务暂时不可用时缓存日志数据，并在 ClickHouse 恢复可用后继续发送。缓冲区的大小决定了 Vector 在开始丢失日志前能够容忍的 ClickHouse 最大停机时间。

## 数据查询 {#query}

[ClickHouse 的查询语言](https://clickhouse.com/docs/reference/statements/select)是 SQL 的一个方言，较为接近 PostgreSQL，但有许多 QoL（Quality of Life）特性和高级扩展功能。
ClickHouse 的 SQL 方言，例如：

- 双引号和反引号都可以用作标识符的引用符号，单引号用于字符串字面量。
- `WHERE`、`GROUP BY` 和 `HAVING` 子句中可以使用 SELECT 列表中的别名。
- 大量的辅助函数。

例如，要实现与 [ayano](https://github.com/taoky/ayano) 类似的输出，可以使用以下 SQL 查询：

```sql
SELECT
  ip_prefix("ip", 24, 48) AS "IP",
  COUNT(DISTINCT "ip") AS "Unique IPs",
  count() AS "Request Count",
  sum("size") AS "Bytes Sent",
  argMax("url", "event_time") AS "Last URL",
  max("event_time") AS "Last Seen",
  count(DISTINCT "user_agent") AS "Unique UAs"
FROM "mirrors"."access_log"
WHERE $__timeFilter("event_time")
  AND "source" = 'mirrors'
GROUP BY "IP"
ORDER BY "Bytes Sent" DESC, "IP" ASC
LIMIT 50;
```

在 Grafana 中使用 ClickHouse 数据源时，Grafana ClickHouse Plugin 会[提供一些额外的函数](https://grafana.com/docs/plugins/grafana-clickhouse-datasource/latest/template-variables/)，例如 `$__timeFilter("event_time")` 会被替换为与 Grafana 界面上的时间选择器匹配的、采用 `event_time` 列的时间范围过滤条件。Grafana 以表格展示的查询结果类似这样：

![Grafana ClickHouse 查询结果示例](../images/grafana-ayano-example.png)

??? example "Grafana ClickHouse SQL 示例"

    恰当地配置 [Grafana 的模板变量](https://grafana.com/docs/grafana/latest/visualizations/dashboards/variables/)，可以让用户（或者你自己）更方便地选择过滤条件，例如：

    ```sql
    SELECT
      ip_prefix(ip, ${ipv4_prefix}, ${ipv6_prefix}) AS IP,
      COUNT(DISTINCT ip) AS "Unique IPs",
      count() AS "Request Count",
      sum(size) AS "Bytes Sent",
      argMax(url, event_time) AS "Last URL",
      max(event_time) + INTERVAL 1 DAY AS "Last Seen",
      count(DISTINCT user_agent) AS "Unique UAs"
    FROM $database_table
    WHERE $__timeFilter(event_time)
      AND $__conditionalAll("source" IN (${source:singlequote}), $source)
      AND $__conditionalAll("repo" IN (${repo:singlequote}), $repo)
      AND $__conditionalAll(intDivOrZero("status", 100) = ${status}, $status)
    GROUP BY IP
    ORDER BY "${order_by}" DESC, "IP" ASC
    LIMIT ${limit};
    ```

    上面的示例图使用的即是此 SQL 查询语句。

### `WITH` 语句 {#with-clause}
