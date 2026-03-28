# 2026-03-27 中间产物索引

## 目标

统一索引本阶段已生成的中间数据、报告和接手文档，降低会话中断后的恢复成本。

## 代码入口

- CLI：`src/elon_research/cli.py`
- 数据采集：`src/elon_research/data_sources/`
- 成交抓取修复：`src/elon_research/data_sources/polymarket.py`
- Subgraph 成交 PoC：`src/elon_research/data_sources/polymarket_subgraph.py`
- 标准化流水线：`src/elon_research/normalization/pipeline.py`
- 窗口特征工程：`src/elon_research/features/build.py`
- 弱验证执行：`src/elon_research/evaluation/weak_validation.py`

## 原始数据

- `datasets/raw/polymarket/event_278377.json`
- `datasets/raw/polymarket/event_278377.meta.json`
- `datasets/raw/polymarket/event_208544.json`
- `datasets/raw/polymarket/event_212454.json`
- `datasets/raw/polymarket/event_220474.json`
- `datasets/raw/polymarket/event_226986.json`
- `datasets/raw/polymarket/event_236151.json`
- `datasets/raw/polymarket/event_251243.json`
- `datasets/raw/polymarket/event_257217.json`
- `datasets/raw/polymarket_subgraph/event_278377_market_260-279.json`
- `datasets/raw/tweets/tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json`
- `datasets/raw/tweets/tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.meta.json`

## 标准化数据

- `datasets/normalized/event_278377_markets.json`
- `datasets/normalized/event_278377_trades.json`
- `datasets/normalized/event_278377_prices.json`
- `datasets/normalized/event_278377_subgraph_trades.json`
- `datasets/normalized/event_208544_{markets,trades,prices}.json`
- `datasets/normalized/event_212454_{markets,trades,prices}.json`
- `datasets/normalized/event_220474_{markets,trades,prices}.json`
- `datasets/normalized/event_226986_{markets,trades,prices}.json`
- `datasets/normalized/event_236151_{markets,trades,prices}.json`
- `datasets/normalized/event_251243_{markets,trades,prices}.json`
- `datasets/normalized/event_257217_{markets,trades,prices}.json`
- `datasets/normalized/tracking_d861bacb-6108-45d6-9a14-47b9e58ea095_summary.json`

## 报告文档

- `datasets/reports/2026-03-27-raw-ingest-summary.md`
- `datasets/reports/2026-03-27-normalization-summary.md`
- `datasets/reports/2026-03-27-first-event-study-and-weak-validation.md`
- `datasets/reports/2026-03-27-event-278377-weak-validation.md`
- `datasets/reports/2026-03-27-event-278377-weak-validation.json`
- `datasets/reports/2026-03-27-weak-validation-v2-summary.md`
- `datasets/reports/2026-03-27-cross-week-selected-events.json`
- `datasets/reports/2026-03-27-cross-week-ingest-normalization-summary.md`
- `datasets/reports/2026-03-27-cross-week-weak-validation-unified-params.md`
- `datasets/reports/2026-03-27-cross-week-weak-validation-unified-params.json`
- `datasets/reports/2026-03-28-cross-week-robustness-check.md`
- `datasets/reports/2026-03-28-cross-week-robustness-check.json`
- `datasets/reports/2026-03-28-cross-week-proxy-window-validation.md`
- `datasets/reports/2026-03-28-cross-week-proxy-window-validation.json`
- `datasets/reports/2026-03-28-market-slug-pagination-audit.md`
- `datasets/reports/2026-03-28-market-slug-pagination-audit.json`
- `datasets/reports/2026-03-28-phase-checkpoint-conclusion.md`
- `datasets/reports/2026-03-28-go-no-go-checkpoint.md`
- `datasets/reports/2026-03-28-subgraph-orderfilled-poc.md`
- `datasets/reports/2026-03-28-subgraph-orderfilled-poc.json`
- `datasets/reports/2026-03-28-subgraph-windowed-sample.md`
- `datasets/reports/2026-03-28-subgraph-windowed-sample.json`
- `datasets/reports/2026-03-28-subgraph-deduped-asset-sample.md`
- `datasets/reports/2026-03-28-subgraph-deduped-asset-sample.json`
- `datasets/reports/2026-03-28-subgraph-market-sample.md`
- `datasets/reports/2026-03-28-subgraph-market-sample.json`
- `datasets/reports/2026-03-28-subgraph-vs-data-api-comparison.md`
- `datasets/reports/2026-03-28-subgraph-vs-data-api-comparison.json`
- `datasets/reports/2026-03-28-subgraph-event-coverage-summary.md`
- `datasets/reports/2026-03-28-subgraph-event-coverage-summary.json`
- `datasets/reports/2026-03-27-historical-tweet-timeline-provenance-scout-v2.md`
- `datasets/reports/2026-03-27-polymarket-trades-pagination-cap-note.md`
- `datasets/reports/2026-03-27-phase-progress-log.md`
- `datasets/reports/2026-03-27-memory-policy.md`

## 接手文档

- `experiments/2026-03-27-next-handoff.md`
- `experiments/2026-03-27-session-bootstrap.md`

## 当前状态

- 启动流程验证：通过（`pytest -q` + `normalize` + `backtest`）
- 样本状态：8 周市场真实快照已标准化，可做跨周弱验证
- 数据限制：当前只有 `eventId` 过滤可依赖；事件级样本每周最多 `3500` 条，market 级过滤不可依赖
- 当前能做：跨周市场侧事件研究 + 统一参数弱验证回放 + 替代成交来源 PoC
- 当前不能做：逐条历史推文事件强验证（待 A 级来源权限）
