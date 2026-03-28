# Polymarket 专项策略专属记忆 (Project Memory)

## 项目约定
- 每次交互前必须读取此文件获取历史信息。
- 每次有新进展或决策后，必须将最新进度写入此文件。
- 项目全部完结后标记为 `[CLOSED]`。
- **当前状态**: `[OPEN]`

## 资金与基建盘点 (截止 2026-03-09)
- **EOA 钱包地址**: `0xcD1862c43F7F276026AA1579eC2b8b9c02c10552`
- **真实链上余额**: 约 0.93 MATIC，1.14 USDC.e，0.01 Native USDC (已核实，此前 1245 USDC 为测试环境 Mock 数据)
- **AA Wallet 地址**: 暂缺/未部署 (需充值后激活或重新查询)
- **基建脚本**: `scripts/polymarket_monitor.py` (持仓/盈亏自动化巡检)
- **自动化监控**: 已配置 Cron 任务 (Reese Polymarket Monitor, 原设每2小时)

## 核心策略与历史持仓
- **标的**: US x Iran ceasefire (March 31) 
- **方向**: **NO**
- **建仓成本**: 约 $0.56
- **风控策略 (基于靖安科技 OSINT 框架)**:
  - 止损: $0.40 或物理信号(加油机撤回、GPS干扰消失)反转。
  - 止盈: 达到 $0.85 时减仓 50%，达到 $0.92 全清。

## 后台策略进程管理规范 (Task Management Protocol)
- **禁止使用 `nohup` 启动无主幽灵进程**，防止内存泄漏引发 OOM 影响 OpenClaw 网关稳定性。
- **分级调度架构**:
  1. **低频任务 (分钟/小时级)**: 弃用 `while True` 常驻脚本，强制改用 OpenClaw 内置 `cron` 触发 `exec`，执行完即销毁。
  2. **高频/流任务 (Websocket/高频 API)**: 统一使用 `pm2` 纳管 Python 策略，强制添加内存熔断上限 (例如 `pm2 start monitor.py --max-memory-restart 100M`)。
  3. **事件驱动 (Webhook)**: 优先采用 Push 模式替代 Polling 轮询。
- **2026-03-10 拓扑更新**: Polymarket 相关策略默认部署到 Fiona 节点执行；Reese 负责策略脑、开发组织、调度与异常处置。巡检默认提升为分钟级。

## 视觉资产生成规范 (Visual Style Constraints)
- **固定风格**: 仿手写白板思维导图 (Hand-drawn whiteboard style mind map, marker sketch style)。
- **核心特征**: 针对复杂策略与逻辑梳理，统一采用“极简手绘白板图”风格（带线框、箭头指示、高对比度标记），禁止生成花哨的 3D/写实图片。

---
## 进度日志 (Progress Log)
- **2026-03-09**: 
  - 岁月老板建立 Discord #polymarket 专项频道，确立此专属记忆文件。
  - 修正了错误的资金余额（改为 0 持仓）。
  - 梳理并汇报了“美伊战争”策略的靖安科技框架（ADS-B/GPS监控），反省了目前脚本仅监控价格而未真正接入外部物理信号源的问题。
  - 更新了 `TOOLS.md` 中的模型能力清单。
