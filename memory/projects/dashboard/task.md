# Dashboard 项目任务拆解

- [Done] T1: 输出《CEO 立项三问协议》 | Proof: memory/projects/dashboard/ceo-intake-protocol.md
- [Done] T2: 输出《Mission Card 标准模板》 | Proof: memory/projects/dashboard/mission-card-template.md
- [Done] T3: 输出《OpenClaw 本地 Dashboard PRD / 系统设计草案》 | Proof: memory/projects/dashboard/dashboard-system-design.md
- [Done] T4: 输出《最小数据模型（SQLite）》 | Proof: memory/projects/dashboard/sqlite-minimal-data-model.md
- [Done] T5: 输出《与 Gateway 1979 集成方案》 | Proof: memory/projects/dashboard/gateway-1979-integration.md
- [Done] T6: 将以上方法论写入 OpenViking 长期记忆 | Proof: memory_store sessions 65691687-ae1b-489a-b989-27dedd9dd05c / 305342b1-d43c-4c79-81d5-34ded7767695 / bf8ed25b-a15e-4fad-9c7f-046edcfa25d1
- [Done] T7: 用 recall 验证记忆是否可检索 | Proof: memory_recall 命中“CEO立项三问/Mission Card/Dashboard/Gateway 1979”相关记忆
- [Done] T8: 若确认开发，实施 Dashboard MVP | Proof: dashboard-mvp/ 目录已交付可运行 Node+SQLite MVP；`npm test` 通过；README 已提供启动与自测说明
- [Done] T9: 接入真实项目文档数据源（memory/projects/* 自动发现） | Proof: dashboard-mvp/adapters.js + server.js 已支持 project-docs adapter；PORT=4320 验证 summary 返回 6 个 missions / 5 个 projectDocs
- [Done] T10: 沉淀 SOP 演进机制与 think 模式强度策略 | Proof: memory/projects/dashboard/sop-evolution.md + think-mode-policy.md；并已写入 OpenViking

## 验收标准
- 文档完整、可执行、字段固定
- 长期记忆可被稳定召回
- 明确推荐架构：独立 Dashboard + Gateway 单入口反代
- 明确 Fiona 在扫描流水线中的职责边界
