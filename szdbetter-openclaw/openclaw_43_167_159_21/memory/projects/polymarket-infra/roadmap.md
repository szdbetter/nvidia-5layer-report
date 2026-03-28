# Polymarket Infra Roadmap

## Phase 1: 数据基建 (2026-03-10)
- [x] SQLite + WAL mode
- [x] 5-table schema (prices, signals, tasks, orders, alerts)
- [x] Python DAL 统一写入层
- [x] Datasette Dashboard
- [ ] 监控脚本接入 DAL
- [ ] 子Agent 审计回写
- [ ] Datasette systemd 持久化

## Phase 2: 自动化 & 可视化 (TBD)
- [ ] Cron 定时监控 → DAL 落盘
- [ ] OSINT 信号自动入库
- [ ] Dashboard 定制视图
