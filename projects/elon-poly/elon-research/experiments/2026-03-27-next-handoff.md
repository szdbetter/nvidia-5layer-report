# 2026-03-27 下一阶段接手说明

## 接手目标

不要再做项目骨架工作。当前阶段已经进入“数据限制核验后重新收敛结论”，下一阶段的重点是：

1. 推进逐条历史推文时间线来源（优先 A 级来源）
2. 寻找单 market 成交完整性的替代路径
3. 在更强数据条件下再做下一轮策略验证

## 当前状态

- 代码骨架已完成
- CLI 已完成
- 真实 `ingest` 已完成
- `ingest -> normalize -> backtest` 已打通
- 跨周样本已扩展到 8 周
- 事件级成交抓取当前只能稳定拿到每周 `3500` 条
- 单 market 维度仍存在 `offset > 3000` 上限
- 推文侧已接入 hourly/daily tracking 摘要，但仍不够做逐事件强验证

## 数据现实

### 已真实可用

- `event_278377.json`
  - 30 个 bracket 市场
  - 事件级成交可抓取，但存在 `3500` 条截断
  - outcome 价格序列可用

### 仅可作辅助参考

- `tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json`
  - 当前 tracking 摘要可信
  - 小时桶/日桶可用于 proxy windows
  - 本地历史周数据只可作辅助参考
  - 不可冒充逐条历史推文时间线

## 推荐执行顺序

1. 先读以下文档：
   - `datasets/reports/2026-03-28-phase-checkpoint-conclusion.md`
   - `datasets/reports/2026-03-28-market-slug-pagination-audit.md`
   - `datasets/reports/2026-03-28-cross-week-proxy-window-validation.md`
2. 如果继续攻市场侧：
   - 先解决单 market 成交完整性，而不是继续调参数
3. 如果继续攻推文侧：
   - 优先推进 X API 历史权限或等价 A 级来源
4. 没有更强数据前：
   - 不要宣称已发现可交易 edge

## 不要做的事

- 不要重新设计项目结构
- 不要再做 dashboard
- 不要加入自动交易
- 不要把辅助推文数据包装成强验证证据

## 成功标准

下一阶段至少需要新增以下之一：

1. 可公开复现的逐条历史推文时间线落盘结果
2. 可证明优于当前 `data-api /trades` 的成交完整性方案
3. 基于更强数据重新得到仍然成立的策略证据
