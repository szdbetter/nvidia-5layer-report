# 利基市场实验：美股财报预期差分析 (Alpha)
## 实验目标
利用 Opus 的 1M 上下文能力，对标的进行「地毯式」研报及推文审查，寻找市场共识之外的「预期差」。

## 当前标的：RDW (Redwire Corp)
- **核心数据回顾**：Q4 2025 营收超预期，但 FCF 承压。
- **监控点**：SpaceX 发射频率对 RDW 积压订单交付速度的影响。

## 待办
- [ ] 编写 `rdw_deep_scan.js`：调用 QVeris 获取实时 SEC 申报及分析师评价。
- [ ] 配置 Opus 任务流：将 RDW 最近 3 个季度的 Transcript 喂给 opus-agent 寻找管理层指引的矛盾点。
