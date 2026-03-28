# OpenClaw 本地 Dashboard 路线图

## 项目目标
建立一个本地统一任务作战面板，统一展示 Mission Card、任务状态、Agent/节点执行流、证据、风险阻塞、OpenViking 记忆验证，并通过单入口与 Gateway 1979 集成。

## 核心原则
1. 控制面与执行面分离：Dashboard 独立服务，Gateway 保持核心控制职责。
2. 单入口：通过反向代理挂到 Gateway 1979 的统一入口，而不是深度耦合到 Gateway 核心。
3. 先只读后控制：先做可视化与审计，再逐步开放触发/停止/重跑等动作。
4. 强制立项三问：复杂任务执行前必须先形成 Mission Card。
5. 证据优先：没有证据的完成不算完成。

## 里程碑

### M1：治理层落地
- 固化《CEO 立项三问协议》
- 固化 Mission Card 模板
- 固化任务验收与证据标准
- 将方法论写入 OpenViking 并可被 recall 验证

### M2：Dashboard MVP
- 任务总览页
- Mission Card 详情页
- Agent/节点执行流视图
- 证据面板
- 风险/阻塞面板
- Memory 写入与验证面板
- SQLite 最小状态层

### M3：系统集成
- 从 sessions/process/cron/nodes/memory 聚合状态
- 接入 Fiona Polymarket 监控与扫描流水线
- 接入 Gateway 1979 单入口反代
- 默认只读访问

### M4：轻控制能力
- 手动重跑任务
- 停止 agent / 标记阻塞
- 升级告警
- 任务状态流转操作

### M5：运营中枢
- 成本/ROI 视图
- 节点健康热力图
- 实时事件流（SSE/WebSocket）
- 历史审计与版本演进

## 当前执行顺序
1. 产出 Dashboard 系统设计草案
2. 产出 Mission Card 标准模板
3. 验证/补写 OpenViking 记忆
4. 视需要启动 ACP 实施开发
