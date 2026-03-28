# 2026-03-27 标准化结果摘要

## 输入快照

- 市场侧：`datasets/raw/polymarket/event_278377.json`
- 推文侧：`datasets/raw/tweets/tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json`

## 输出文件

- 市场表：`datasets/normalized/event_278377_markets.json`
- 成交表：`datasets/normalized/event_278377_trades.json`
- 价格表：`datasets/normalized/event_278377_prices.json`
- 推文摘要表：`datasets/normalized/tracking_d861bacb-6108-45d6-9a14-47b9e58ea095_summary.json`

## 行数统计

- `markets`：`60` 行（30 个 bracket × Yes/No 两个 outcome）
- `trades`：`3500` 行
- `prices`：`12494` 行
- `tweets summary`：`1` 份摘要对象（含 daily 字典）

## 结构说明

### 市场表

关键字段：
- `event_slug`
- `market_slug`
- `condition_id`
- `outcome`
- `token_id`
- `bracket_low` / `bracket_high`
- `active` / `closed`

说明：
- 真实标签中存在 `<20` 区间，标准化后映射为 `0-19`。

### 成交表

关键字段：
- `timestamp`
- `market_slug`
- `token_id`
- `outcome`
- `side`
- `price`
- `size`
- `transaction_hash`
- `bracket_low` / `bracket_high`

说明：
- 通过 `token_id` 回连市场表，补齐 bracket 区间字段。

### 价格表

关键字段：
- `timestamp`
- `market_slug`
- `outcome`
- `token_id`
- `price`
- `bracket_low` / `bracket_high`

说明：
- 输入键为 `<market_slug>:<outcome>`，标准化时拆分并做 token 映射。

### 推文摘要表

关键字段：
- `tracking_id`
- `start_date` / `end_date`
- `total`
- `days_elapsed`
- `daily`
- `provenance`

说明：
- 当前是 tracking 级摘要，不是逐条历史推文事件表。

## 数据质量观察

1. 标准化后市场、成交、价格三表可以通过 `market_slug + outcome` 或 `token_id` 关联。
2. 推文侧仍是摘要层级，适合弱验证，不适合逐事件强验证。
3. 本次标准化已达到“可做首轮事件研究和弱验证回测”的最低结构要求。
