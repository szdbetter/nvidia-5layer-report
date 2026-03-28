# Goldsky orderFilledEvents 替代成交来源 PoC

## 样本
- 事件：`278377`
- bracket：`260-279`
- 窗口：`2026-03-20` 到 `2026-03-27`

## 结果
- maker token `257058814796...`：返回 10 条样本
- taker token `257058814796...`：返回 10 条样本
- maker token `329281667972...`：返回 10 条样本
- taker token `329281667972...`：返回 10 条样本

## 结论
- Goldsky orderbook subgraph 已验证可访问。
- `asset + timestamp window` 组合查询可返回目标 token 的 fill 事件。
- 这条路径具备成为替代成交来源的潜力，下一步应做分页与全窗口拉取实现。