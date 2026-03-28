# Subgraph 事件覆盖摘要

## 样本
- 事件：`278377`
- 来源：`ingest-subgraph-event --top-brackets 3` 后的标准化结果

## 结果
- 标准化 subgraph trade 行数：`6084`
- `300-319`: 2133 行
- `280-299`: 1999 行
- `260-279`: 1952 行

## 结论
- 替代成交来源已经从单个 bracket 扩展到事件内多个高流动 bracket。
- 下一步可以用 subgraph trades 单独做一版事件内研究比较。