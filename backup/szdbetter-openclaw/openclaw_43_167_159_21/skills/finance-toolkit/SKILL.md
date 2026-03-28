# Finance Toolkit Skill

## 🎯 核心定位
由 Reese 管理的金融 Alpha 挖掘工具集，集成自动化研报、实时行情与量化交易能力。

## 🛠️ 集成工具
1. **Alpaca Trading** (`apcacli`):
   - 状态：待安装 (需要 Rust 环境)
   - 用途：股票/期权/加密货币自动化交易。
   - 配置：需要 `APCA_API_KEY_ID` 和 `APCA_API_SECRET_KEY`。

2. **Twitter KOL Analysis**:
   - 状态：已集成 (`skills/twitter-crawler/deep_crawl.js`)
   - 用途：抓取 KOL 观点，提取 Alpha。

3. **Stock Market Pro** (Stock Charting):
   - 状态：待集成 (通过 `agent-reach` 监控)
   - 用途：生成含 RSI/MACD 等指标的高清技术分析图表。

## 📈 进化目标
- [ ] 实装 `apcacli` 并完成模拟盘 (Paper Trading) 测试。
- [ ] 编写 `report_generator.py`：自动聚合 KOL 观点与实时股价，生成 Alpha 简报。
- [ ] 接入 Polymarket 预测市场数据，监控宏观事件概率。

---
*Created by Reese via agent-reach discovery.*
