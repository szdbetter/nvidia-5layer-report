# 历史逐条推文时间线来源调研（provenance v2）

## 目标

继续寻找可公开复现、可落盘、能提供逐条时间戳的 Elon 历史推文来源，并明确每类来源的证据等级与风险。

## 来源分级结论

1. A 级（官方强来源）：X API v2（用户时间线 + Full-archive Search）
2. B 级（官方衍生工具）：twarc（依赖 X API 权限，当前可用性受限）
3. C 级（历史归档/抓取）：Archive Team Twitter Stream、snscrape 等
4. D 级（当前项目已有）：xtracker + weekly_history（仅周级摘要，不能替代逐条时间线）

## 逐项核验

### 1) X API v2 用户时间线与搜索（A 级）

- 证据：官方文档提供 `GET /2/users/{id}/tweets` 时间线接口，支持 `since_id`、`until_id`、`max_results`、`pagination_token` 与 `created_at` 字段。
- 证据：官方搜索文档明确 recent search 仅最近 7 天，`/2/tweets/search/all` 属于付费/企业全量历史搜索。
- 判断：若要做“逐条历史推文强验证”，这是当前最可辩护的主路径，但需要可用的 X API 权限与预算。

### 2) twarc（B 级）

- 证据：`DocNow/twarc` README 明确它是通过 Twitter/X API 采集 JSON；同时声明在 API 配额变化后项目已不再积极维护。
- 判断：twarc 可作为执行器，但不是独立数据源。其可信度继承自 X API 权限与返回数据。

### 3) Archive Team Twitter Stream（C 级）

- 证据：Internet Archive metadata 显示该集合为 `Spritzer` 流，且“no longer updated / static dataset”，并标注访问限制。
- 判断：可作为历史研究辅助线索，不适合作为当前周级市场强验证主数据源（覆盖与可得性都不足）。

### 4) snscrape（C 级）

- 证据：项目 README 显示支持 Twitter 用户时间线抓取与 JSONL 导出。
- 风险：抓取链路非官方 API，稳定性、完整性与可复现性受平台策略影响较大。
- 判断：可做候选补充来源，但默认仅作辅助，不直接进入“主回测证据链”。

### 5) xtracker + weekly_history（D 级）

- 当前状态：已接入并可复现，能提供周级 total/daily 参考。
- 限制：不具备“逐条 tweet_id + created_at 全时序”能力。
- 判断：继续保留为弱验证标签，不冒充强验证来源。

## 建议执行路径

1. 优先推进 A 级路径：申请/确认可用的 X API 历史权限（至少可覆盖目标研究窗口）。
2. 若 A 级受限：用 C 级来源做“候选时间线”，并为每条记录附 `source_url + fetched_at + hash`，只用于辅助分析。
3. 在获得可验证逐条时间线前，研究结论继续标注为“弱验证”。

## 参考链接

- X API Get Posts: https://docs.x.com/x-api/users/get-posts
- X API Search Introduction: https://docs.x.com/x-api/posts/search/introduction
- twarc README: https://github.com/DocNow/twarc
- Archive Team Twitter Stream metadata: https://archive.org/metadata/twitterstream
- snscrape README: https://github.com/JustAnotherArchivist/snscrape
