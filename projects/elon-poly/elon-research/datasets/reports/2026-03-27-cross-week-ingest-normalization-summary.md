# 跨周样本扩展与标准化摘要

## 样本选择规则
- 来源：`weekly_history.json` 日期窗口反查 Polymarket `event slug`。
- 条件：`end <= 2026-03-27`，且事件成交量 `volume > 0`。
- 结果：选取最近且流动性更高的 8 个事件。

## 样本清单
- `208544` `2026-02-17~2026-02-24`: markets=60, trades=3710, prices=0, volume=17177918.00
- `212454` `2026-02-20~2026-02-27`: markets=60, trades=4210, prices=104, volume=14239946.53
- `220474` `2026-02-24~2026-03-03`: markets=60, trades=5000, prices=4212, volume=46476194.32
- `226986` `2026-02-27~2026-03-06`: markets=60, trades=4000, prices=8638, volume=29155527.27
- `236151` `2026-03-03~2026-03-10`: markets=60, trades=5000, prices=12480, volume=3631219.37
- `251243` `2026-03-10~2026-03-17`: markets=60, trades=5000, prices=12388, volume=1305032.98
- `257217` `2026-03-13~2026-03-20`: markets=60, trades=4000, prices=12807, volume=3850093.12
- `278377` `2026-03-20~2026-03-27`: markets=60, trades=5000, prices=12528, volume=11018614.46

## 产物
- `datasets/reports/2026-03-27-cross-week-selected-events.json`
- `datasets/raw/polymarket/event_<event_id>.json`（新增 7 个事件快照）
- `datasets/normalized/event_<event_id>_{markets,trades,prices}.json`（8 周全量标准化）

## 已识别限制与当前状态
- 已确认：`eventId` 维度查询存在历史 offset 上限，直接按事件抓取会截断在每周 `3500` 条成交。
- 已确认：公开 `data-api /trades` 中，`slug / market / conditionId / asset` 过滤不可依赖，不能作为可辩护的 market 级拆分修复方案。
- 当前基线：跨周样本已恢复为“事件级有效但截断”的干净基线。
