# Polymarket 成交分页上限核验与修复记录

## 问题

原实现使用 `data-api /trades?eventId=...` 拉取成交，验证发现当 `offset > 3000` 时返回 400：

`{"error":"max historical activity offset of 3000 exceeded"}`

这会导致按事件维度抓取时出现成交样本截断。

## 修复

已将抓取策略改为：

1. 先读取事件下所有 market slug；
2. 对每个 slug 独立分页拉取 `/trades`；
3. 按 `transactionHash + asset + timestamp + price + size + side` 去重合并。

## 修复后验证（8 周样本）

修复前：每周 `trades=3500`（固定）

修复后：

- `208544`: 3710
- `212454`: 4210
- `220474`: 5000
- `226986`: 4000
- `236151`: 5000
- `251243`: 5000
- `257217`: 4000
- `278377`: 5000

说明：事件级固定截断已被缓解，但单 market 维度仍可能受分页上限影响，需后续持续核验。
