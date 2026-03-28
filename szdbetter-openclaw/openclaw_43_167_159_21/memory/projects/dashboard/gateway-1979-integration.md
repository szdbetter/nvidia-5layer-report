# Gateway 1979 集成方案

## 目标
在不深度污染 Gateway 核心的前提下，为 Dashboard 提供单入口访问能力。

## 推荐方案
采用“独立 Dashboard 服务 + Gateway 1979 单入口反向代理”。

## 拓扑
- Gateway 核心服务：继续负责消息、session、tool orchestration、配置管理。
- Dashboard 服务：负责任务面板、状态聚合、证据展示、记忆验证。
- 反向代理层：对外只暴露一个入口，例如 1979。

示例路径：
- /gateway -> Gateway 原生接口
- /dashboard -> Dashboard UI/API
- /events -> Dashboard 事件流（后续）

## 为什么不直接写进 Gateway
1. Dashboard 需求高频变化
2. UI 与控制面耦合风险高
3. 升级与回滚复杂度增加
4. 审计边界不清晰

## 权限建议
- 默认绑定 127.0.0.1
- 若需远程访问，增加 token/session auth
- 默认只读
- 写操作需二次确认
- 所有动作进入 audit log

## MVP 集成方式
1. 本地启动 Dashboard 服务
2. Dashboard 定时拉取 sessions/process/cron/nodes/memory 数据
3. 通过反向代理挂到 1979 的 /dashboard
4. 人类通过统一入口访问

## 后续演进
- SSE/WebSocket 实时推送
- 更细粒度 RBAC
- 任务触发、停止、重跑等轻控制能力
- 与 cron / Fiona 扫描流水线联动

## 验收点
若集成方案不能同时满足以下条件，则不通过：
- 单入口访问
- Dashboard 与 Gateway 解耦
- 默认最小权限
- 有审计设计
- 后续可平滑扩展控制能力
