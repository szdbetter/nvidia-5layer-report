
## Cron 使用原则（2026-03-24 CEO决策）
- Cron 是稀缺资源，极度克制，只用于：固定时间触发的事件驱动任务（日报、告警心跳、定时备份）
- 轮询类任务（数据刷新/健康检查/状态查询）：纳入 Dashboard 脚本统一管理，不开 Cron
- MiniMax Token Plan 额度 → dashboard 按需读取，不开 Cron
- 新增 Cron 前必须自问：能放进 dashboard 脚本吗？能则不开 Cron
