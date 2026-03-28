# OpenClaw Dashboard MVP

## 当前架构
- 独立 Dashboard 服务
- Node.js + Express + better-sqlite3
- 任务数据源：SQLite seed + `~/.openclaw/projects` 自动发现
- 兼容回退：若 `~/.openclaw/projects` 为空，则回退到 workspace 内 `memory/projects`

## 功能
- 任务列表（搜索 / 排序 / 进度 / 完工勾选）
- Mission 详情
- SOP / 工作分工摘要
- Runtime 面板（含 Fiona Polymarket 监控与 Polymarket Alpha 扫描真实任务占位）
- Task / Issue / 复盘 / SOP 原始文件查看
- 图片预览
- OpenViking Memory 验证面板

## 启动
```bash
cd dashboard-mvp
node server.js
```
默认地址：`http://127.0.0.1:1980`

## 项目目录
默认使用：
- `~/.openclaw/projects`

建议项目目录结构：
- `roadmap.md`
- `task.md`
- `issue.md`
- `learning.md`
- `decision.md`
- `cowork.md`
- `sop.md` 或 `sop-evolution.md`
- 图片文件（可选）

## 文件查看
前端支持点击查看：
- 文件名
- 原始路径
- 文本内容 / 图片预览

## 真实任务说明
当前版本已在 Runtime 面板显式展示：
- Fiona Polymarket 监控
- Polymarket 全网 Alpha 扫描策略

它们目前作为真实任务卡片接入；后续继续与 sessions/process/cron/nodes/memory 打通。

## 自测
```bash
npm test
node server.js
curl http://127.0.0.1:1980/api/summary
curl http://127.0.0.1:1980/api/missions/polymarket
```
