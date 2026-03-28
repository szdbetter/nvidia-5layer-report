---
name: stock-research
description: 执行美股标的从初筛到深度研报的全流程投研任务，
allowed-tools: ["exec", "read", "write", "message", "web_search"]
metadata: {"openclaw": {"requires": {"bins": ["ov"]}, "user-invocable": true, "emoji": "📈"}}
---

## 核心文件

- `phase1-prompt.md` — 美股默认一阶段候选筛选（Ajinomoto Filter + 4 步流程 + ≤12 次调用）
- `phase1-hk-agent-prompt.md` — 港股 AI Agent / 机器人 / 模型基础设施一阶段筛选（按港股场景切换，不覆盖美股）
- `phase2-prompt.md` — 二阶段深度研报（14 维度评分卡 + 物理门控 + 交互网页）
- `EXECUTE.md` — 执行指南（可选）


## 输出位置

- 一阶段研报：`~/.openclaw/workspace/reports/phase1/[日期]_[赛道].md`
- 二阶段研报：`~/.openclaw/workspace/reports/phase2/[日期]_[TICKER].md`
-

## 配额限制

| 项目 | 限制 |
|------|------|
| 一阶段工具调用 | ≤20 次/标的 |
| 单工具失败重试 | 3 次后淘汰 |


## SOP 位置

`～/.openclaw/workspace/skills/stock-research/stock-research-sop.mdd`

## 版本

v1.0 (2026-02-24)
