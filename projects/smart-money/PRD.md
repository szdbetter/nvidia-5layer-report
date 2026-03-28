# Smart Money 地址库 — PRD v0.2

> 作者：Opus + Reese (ClawLabs)  
> 日期：2026-03-19  
> 状态：**老板已确认核心方向，进入 Phase 1 开发**

---

## ✅ 老板决策确认（2026-03-19）

| 问题 | 决策 |
|------|------|
| 最终目标 | 监控自用 → 跟单 → 付费群（远期） |
| 跟单方式 | 手动决策，信号分钟级延迟 |
| 资金规模 | 10-100U 试仓 |
| SM 入库标准 | 跨3+币盈利 + 非bot，持续优化 |
| 链上实时监控 | 暂不做 |
| 采集频率 | 热门币 1h + 持仓 1h（全部 1h） |
| 技术约束 | **禁用 Chrome GUI**，必须用脚本（Playwright headed 算脚本） |
| 执行架构 | VPS 写脚本 → Fiona 执行，后续加 Windows 节点 |
| 前端 | 需要 Dashboard，端口 127.0.0.1:1980 |
| 架构原则 | 先搜现成轮子，不重复造 |

---

## 🔧 现成轮子调研

### GitHub: ykky0/Smart_Money_Tracker ⭐4
- **功能**：Solana 链上 SM 钱包实时交易监控（Raydium + Pump）
- **技术栈**：TypeScript + gRPC + Solana RPC
- **适用**：Phase 2（链上交易监听），不适用于 Phase 1（GMGN 数据采集）
- **结论**：Phase 2 可参考其 gRPC 订阅架构，Phase 1 需自建

### 其他参考
- `MessengerPigeonn/solana-smart-tracker`：含 PrintScan 微市值发现
- `JussCubs/solana-whale-tracker`：鲸鱼交易追踪 + copy-trade 告警
- `agds-alt/solana-alpha-scanner`：混合 Token 扫描 + SM 追踪

**Phase 1 结论**：GMGN 数据采集部分无现成轮子（因为 GMGN 无官方 API），必须自建。但链上监听部分有参考。

---

## 📋 产品需求

### 核心价值
在 Meme 币赌场里，不跟运气，跟赢家。

### 用户故事

| 角色 | 场景 | 期望 |
|------|------|------|
| 交易者 | 想知道哪些钱包持续盈利 | SM 排行榜 + 历史战绩 |
| 交易者 | SM 买入新币时通知 | Discord 推送（币名 + 买入量 + SM 胜率） |
| 交易者 | 过滤 MEV bot | 自动标记排除 bot 地址 |
| 交易者 | 评估 SM 是否值得跟 | 综合评分（胜率、收益、活跃度） |

### 功能模块

#### M1: 数据采集层
- Fiona Playwright 定时采集 GMGN
- 热门代币 Top 100（每 1h）
- 代币持有者 Top 50 + 盈亏（每 1h）
- 随机延迟 2-5s 防封

#### M2: SM 评分引擎
| 维度 | 权重 |
|------|------|
| 跨币盈利数 | 30% |
| 累计已实现盈利 | 25% |
| 胜率 | 20% |
| 活跃度 | 15% |
| 标签信誉 | 10% |

入库门槛：跨3+币盈利 或 单币盈利>$50K，非 bot 标签

#### M3: 信号推送
- Discord Channel 推送
- 格式：SM 地址（脱敏）+ Score + 代币 + 金额 + 历史胜率

#### M4: Dashboard（127.0.0.1:1980）
- SM 排行榜
- 单 SM 历史交易记录
- 热门代币 SM 共识度
- 信号历史

---

## 🗃️ 数据模型

```sql
-- 代币表
CREATE TABLE tokens (
    address TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    chain TEXT DEFAULT 'sol',
    discovered_at TIMESTAMP,
    swap_count_1h INTEGER,
    volume REAL,
    market_cap REAL,
    last_seen TIMESTAMP
);

-- 钱包表
CREATE TABLE wallets (
    address TEXT PRIMARY KEY,
    smart_score REAL DEFAULT 0,
    total_realized_profit REAL DEFAULT 0,
    tokens_profitable INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0,
    labels TEXT, -- JSON array
    is_bot BOOLEAN DEFAULT FALSE,
    name TEXT,
    twitter TEXT,
    first_seen TIMESTAMP,
    last_active TIMESTAMP,
    status TEXT DEFAULT 'candidate' -- candidate/confirmed/blacklisted
);

-- 钱包-代币盈亏
CREATE TABLE wallet_token_profits (
    wallet_address TEXT,
    token_address TEXT,
    realized_profit REAL,
    unrealized_profit REAL,
    cost_basis REAL,
    profit_change REAL,
    snapshot_at TIMESTAMP,
    PRIMARY KEY (wallet_address, token_address)
);

-- 交易信号
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address TEXT,
    token_address TEXT,
    token_symbol TEXT,
    action TEXT, -- buy/sell
    amount_usd REAL,
    smart_score REAL,
    detected_at TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE
);
```

---

## 🏗️ 技术架构

```
[GMGN.ai] ←(Playwright Script)← [Fiona Mac]
                                      │
                                 (SSH/API sync)
                                      │
                                      ▼
                            [VPS - 核心服务]
                            ├── SQLite DB (smart_money.db)
                            ├── 评分引擎 (Python)
                            ├── Dashboard (port 1980)
                            └── Discord 推送
```

### 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 采集 | Playwright headed + Python on Fiona | 已验证可行 |
| 存储 | SQLite (smart_money.db) | 独立于 ops.db |
| 后端 | Python + FastAPI | 轻量，datasette 风格 |
| Dashboard | HTML + Tailwind + Alpine.js | 无构建，单文件 |
| 调度 | launchd (Fiona) + cron (VPS) | 各司其职 |
| 推送 | Discord Webhook | 已有基础设施 |

### 采集频率

| 任务 | 频率 | 请求/天 |
|------|------|---------|
| 热门代币 Top 100 | 1h | 24 |
| 持有者盈亏（Top 100 代币 × 50 holder） | 1h | 2,400 |
| **总计** | | **~2,424** |

> ⚠️ 每日 2400+ 请求量较大。配合随机延迟(2-5s)，单次采集耗时 ~8-12min，可接受。

---

## 🗺️ Roadmap

### Phase 1: 数据基建（本周）
- [ ] Fiona 定时采集脚本（热门币 + 持有者盈亏）
- [ ] Fiona → VPS 数据同步（JSON over SSH）
- [ ] VPS SQLite 存储 + 去重聚合
- [ ] SM 评分引擎 v1
- [ ] Dashboard v1（排行榜 + 信号历史）on :1980
- [ ] Discord 推送：每日 SM 排行 Top 10
- **交付物**：自动更新的 SM 地址库 + Dashboard + Discord 日报

### Phase 2: 信号监控（下周）
- [ ] SM 地址新买入检测（GMGN 轮询对比）
- [ ] Discord 实时信号推送
- [ ] 信号回测胜率统计
- [ ] 参考 ykky0/Smart_Money_Tracker 的 gRPC 链上监听架构
- **交付物**：实时 SM 交易信号

### Phase 3: 跟单辅助（远期）
- [ ] 半自动跟单（信号 + Jupiter swap 链接）
- [ ] 仓位管理 + 风控
- [ ] 多节点支持（Windows 新机）
- **交付物**：跟单工具

---

## 📊 首批数据洞察

| 指标 | 数值 |
|------|------|
| 扫描代币 | 69 |
| 唯一盈利钱包 | 1,851 |
| 跨 2+ 币 | 129 (7.0%) |
| 跨 3+ 币 | 23 (1.2%) |
| Top SM 盈利 | $93K / 6 币 |
| Bot 污染率 | ~5% |

---

*PRD v0.2 — 老板已确认方向，准备进入 Phase 1 开发。*
