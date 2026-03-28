# 2026-03-27 会话记忆策略

## 目标

在无法依赖模型长期会话记忆的情况下，通过文件化机制维持“可恢复历史记忆”。

## 原则

1. 文件优先，不依赖聊天窗口历史。
2. 每次关键动作后立即写中间文档。
3. 所有结论必须有可追溯文件位置。

## 必须持续维护的文件

1. `datasets/reports/2026-03-27-phase-progress-log.md`
2. `datasets/reports/2026-03-27-artifacts-index.md`
3. `experiments/2026-03-27-next-handoff.md`
4. 本文件 `datasets/reports/2026-03-27-memory-policy.md`

## 每轮开发结束时的最小动作

1. 更新 `phase-progress-log.md`：
   - 已完成内容
   - 当前阻塞
   - 下一步优先级
2. 更新 `artifacts-index.md`：
   - 新增数据文件
   - 新增报告
   - 新增代码入口
3. 若有方向变化，更新 `next-handoff.md`。

## 新会话如何“继续历史记忆”

新会话中不要说“参考上文”。要明确要求读取固定文件，并把这些文件视为历史记忆来源：

- `specs/...design.md`
- `plans/...implementation-plan.md`
- `datasets/reports/...phase-progress-log.md`
- `datasets/reports/...artifacts-index.md`
- `experiments/...next-handoff.md`

只有把历史信息写进文件并在新会话显式加载，才能稳定延续上下文。
