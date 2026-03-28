# 2026-03-27 阶段进度日志

## 目的

这份文档用于在模型额度不足、会话中断或更换模型后，提供最低成本的恢复点。

## 当前阶段

阶段名称：跨周样本扩展完成，进入统一参数横向对比与强验证来源收敛

## 已完成

1. 新研究项目 `elon-research/` 已创建并通过测试。
2. 原始快照存储、标准化、特征、回放、中文报告、CLI 最小流程已实现。
3. 官方 Polymarket 真实数据已接入并落盘：
   - 事件详情
   - 30 个 bracket 市场
   - 3500 笔真实成交
   - 60 条 outcome 价格历史
4. 推文侧已接入：
   - 当前 xtracker tracking 摘要
   - 本地 `weekly_history.json` 作为辅助历史参考
5. 当前全量测试状态：
   - `27 passed`
6. 真实标准化流程已落地：
   - `event_278377_markets.json`
   - `event_278377_trades.json`
   - `event_278377_prices.json`
   - `tracking_d861bacb-6108-45d6-9a14-47b9e58ea095_summary.json`
7. 首轮中间研究文档已产出：
   - `2026-03-27-normalization-summary.md`
   - `2026-03-27-first-event-study-and-weak-validation.md`
8. 首轮弱验证回放已产出：
   - `2026-03-27-event-278377-weak-validation.md`
   - `2026-03-27-event-278377-weak-validation.json`
9. 中间产物索引已产出：
   - `2026-03-27-artifacts-index.md`
10. 弱验证 V2（参数敏感性 + 窗口分层）已产出：
   - `2026-03-27-weak-validation-v2-summary.md`
11. 跨会话恢复与记忆策略文档已产出：
   - `experiments/2026-03-27-session-bootstrap.md`
   - `datasets/reports/2026-03-27-memory-policy.md`
12. 启动流程验证已完成：
   - `pytest -q` 通过（`27 passed`）
   - `PYTHONPATH=src python3 -m elon_research.cli normalize --project-root .` 可执行
   - `PYTHONPATH=src python3 -m elon_research.cli backtest --project-root .` 可执行
13. 跨周样本已扩展到 8 个真实事件并完成标准化：
   - 事件：`208544, 212454, 220474, 226986, 236151, 251243, 257217, 278377`
   - 清单：`2026-03-27-cross-week-selected-events.json`
14. 跨周统一参数弱验证对比报告已产出：
   - `2026-03-27-cross-week-weak-validation-unified-params.md`
   - `2026-03-27-cross-week-weak-validation-unified-params.json`
15. 历史逐条推文时间线来源调研（provenance v2）已产出：
   - `2026-03-27-historical-tweet-timeline-provenance-scout-v2.md`
16. Polymarket 成交分页上限核验已完成：
   - `data-api /trades` 在 `offset > 3000` 返回 400
   - 记录：`2026-03-27-polymarket-trades-pagination-cap-note.md`
17. 曾尝试 market 级拆分抓取作为修复路径，但已确认公开接口过滤器不可依赖：
   - `slug / market / conditionId / asset` 不能作为可辩护的成交分段条件
   - 该错误路径已回滚，不再作为有效修复
18. 8 周样本已恢复到干净事件级基线并重标准化：
   - 每周成交样本重新回到 `3500`
   - 跨周报告已按干净基线重算
19. 跨周稳健性检验已完成（非重叠窗口 + regime 分层）：
   - `2026-03-28-cross-week-robustness-check.md`
   - `2026-03-28-cross-week-robustness-check.json`
20. 事件窗口特征工程已扩展到目标窗口：
   - 新增特征：`tweet_delta_5m`、`tweet_delta_15m`、`tweet_delta_1h`、`tweet_delta_6h`
   - 实现：`src/elon_research/features/build.py`
   - 测试：`tests/test_feature_build.py`（通过）
21. 窗口特征已接入弱验证主链路：
   - 单事件回放已使用 `feature_mode=proxy_tweet_windows`
   - 跨周报告：`2026-03-28-cross-week-proxy-window-validation.{md,json}`
   - 当前聚合结果：`0` 交易，未观察到可执行弱信号
22. 高流动 bracket 的单 market 分页完整性抽样已完成：
   - 报告：`2026-03-28-market-slug-pagination-audit.{md,json}`
   - 结果：`8/8` 抽样 market 触发 `offset > 3000` 上限
   - 含义：当前市场微结构基线仍存在单 market 截断风险，结论需保守解释
23. 阶段性结论检查点已产出：
   - `2026-03-28-phase-checkpoint-conclusion.md`
   - 当前判断：尚未观察到可辩护的可交易 edge，主阻塞仍是逐条推文时间线与单 market 成交完整性
24. 已确认 `data-api /trades` 的真实过滤行为：
   - `eventId` 有效
   - `slug / market / conditionId / asset` 在公开接口上不可依赖
   - 之前尝试的 market 级拆分抓取已回滚，不再作为有效修复
25. 干净基线已恢复并重算：
   - 8 周事件级样本重新回到每周 `3500` 条成交
   - `2026-03-28-cross-week-proxy-window-validation.{md,json}` 已按干净基线重算
   - 结果仍为 `0` 交易
26. 阶段继续 / 暂停 条件报告已产出：
   - `2026-03-28-go-no-go-checkpoint.md`
   - 当前建议：不进入交易设计；只有在更强推文或成交来源到位后才进入下一轮研究
27. 替代成交来源 PoC 已落地：
   - 新模块：`src/elon_research/data_sources/polymarket_subgraph.py`
   - 新测试：`test_fetch_order_filled_events_by_asset_window`
   - PoC 报告：`2026-03-28-subgraph-orderfilled-poc.{md,json}`
   - 当前判断：Goldsky orderbook subgraph 具备成为替代成交来源的潜力
28. 替代成交来源原型已扩展到窗口拼接：
   - 新函数：`fetch_order_filled_events_over_windows`
   - 新测试：`test_fetch_order_filled_events_over_windows_combines_results`
   - 当前全量测试：`29 passed`
29. 替代成交来源原型已扩展到 maker/taker 双侧去重：
   - 新函数：`fetch_unique_order_filled_events_for_asset`
   - 新测试：`test_fetch_unique_order_filled_events_for_asset_combines_sides`
   - 当前全量测试：`30 passed`
30. Goldsky 替代成交来源真实样本已验证：
   - `2026-03-28-subgraph-windowed-sample.{md,json}`
   - `2026-03-28-subgraph-deduped-asset-sample.{md,json}`
   - `278377 / 260-279` 的两个 token 在分窗 + 双侧去重后分别得到 `245` 与 `268` 条唯一交易哈希
   - 当前判断：Goldsky 路线已具备继续工程化的价值
31. Goldsky market 级样本已拿到：
   - `2026-03-28-subgraph-market-sample.{md,json}`
   - `278377 / 260-279` 在两侧 token 合并去重后得到 `365` 条 fill 事件
   - 当前判断：可以进入 raw snapshot 落盘与标准化接入阶段
32. Goldsky market 级真实样本已接入数据链路：
   - raw：`datasets/raw/polymarket_subgraph/event_278377_market_260-279.json`
   - normalized：`datasets/normalized/event_278377_subgraph_trades.json`
   - 当前样本行数：`365`
   - 当前判断：替代成交来源已从原型进入研究数据接入阶段
33. 替代成交来源与 data-api 对比摘要已产出：
   - `2026-03-28-subgraph-vs-data-api-comparison.{md,json}`
   - 当前判断：subgraph 已成为项目内第二条可独立落盘与标准化的成交来源
34. Subgraph 抓取已接入 CLI：
   - 新命令：`ingest-subgraph-market`
   - 真实验证：`278377 / 260-279` 已通过命令链路成功落盘
   - 当前全量测试：`33 passed`
35. Subgraph event 批量抓取已接入 CLI：
   - 新命令：`ingest-subgraph-event`
   - `278377` 前 3 个高流动 bracket 已成功落盘并标准化
   - `event_278377_subgraph_trades.json` 当前共 `6084` 行
   - bracket 分布：`260-279 / 280-299 / 300-319`

## 已知结论

1. 市场侧真实历史数据可支持第一轮事件研究和弱验证回测，但当前公开接口下仍只有事件级、且每周最多 `3500` 条的截断样本。
2. 推文侧仍缺少可信、可公开复现的逐条历史时间线下载入口。
3. 因此当前可以做：
   - 市场微结构研究
   - 成交与价格时间序列研究
   - 基于周级/日级推文计数的弱验证
4. 当前还不能做：
   - 严格意义上的逐推文事件强验证

## 正在进行

1. 推进 A 级来源（X API 历史权限）以进入逐条推文强验证。
2. 寻找替代成交来源，因公开 `data-api /trades` 现有过滤器不足以绕过单 market `offset > 3000` 限制。
3. 输出更正式的阶段终止/继续条件报告，明确当前证据为何仍不足以支持交易设计。

## 下一步优先级

1. 推进 A 级推文来源（X API 历史权限或等价来源）
2. 把 Goldsky orderbook subgraph PoC 扩成可分页、可落盘的替代成交抓取链路
3. 在替代成交来源到位后，重跑跨周 proxy window 验证
4. 事件窗口特征工程（5m/15m/1h/6h）进入实现与回归
5. 若上下文不足，按 `session-bootstrap.md` 启动新会话并继续

## 关键文件

- 设计规格：`docs/superpowers/specs/2026-03-27-elon-research-system-design.md`
- 实施计划：`docs/superpowers/plans/2026-03-27-elon-research-system-implementation-plan.md`
- 原始接入摘要：`datasets/reports/2026-03-27-raw-ingest-summary.md`
- 原始市场快照：`datasets/raw/polymarket/event_278377.json`
- 原始推文快照：`datasets/raw/tweets/tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json`
- 标准化摘要：`datasets/reports/2026-03-27-normalization-summary.md`
- 首轮研究结论：`datasets/reports/2026-03-27-first-event-study-and-weak-validation.md`
- 弱验证回放：`datasets/reports/2026-03-27-event-278377-weak-validation.md`
- 弱验证 V2：`datasets/reports/2026-03-27-weak-validation-v2-summary.md`
- 跨周样本摘要：`datasets/reports/2026-03-27-cross-week-ingest-normalization-summary.md`
- 跨周统一参数弱验证：`datasets/reports/2026-03-27-cross-week-weak-validation-unified-params.md`
- 跨周稳健性检验：`datasets/reports/2026-03-28-cross-week-robustness-check.md`
- 历史推文来源调研：`datasets/reports/2026-03-27-historical-tweet-timeline-provenance-scout-v2.md`
- 成交分页上限核验：`datasets/reports/2026-03-27-polymarket-trades-pagination-cap-note.md`
- 产物索引：`datasets/reports/2026-03-27-artifacts-index.md`
- 会话记忆策略：`datasets/reports/2026-03-27-memory-policy.md`
- 新会话启动模板：`experiments/2026-03-27-session-bootstrap.md`

## 恢复提示

如果后续会话需要恢复，请先读：

1. 本文件
2. `datasets/reports/2026-03-27-raw-ingest-summary.md`
3. `docs/superpowers/specs/2026-03-27-elon-research-system-design.md`

然后从“事件窗口特征构建”继续，而不是重新搭框架。
