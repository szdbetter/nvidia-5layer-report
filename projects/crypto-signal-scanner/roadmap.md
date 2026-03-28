# 🎯 Crypto Signal Scanner - Roadmap

## 项目定义
**产品名**：Crypto Signal Scanner (CSS)
**目标**：零API成本，用币安免费公开API实现信号扫描，通过Discord实时通知老板交易机会
**核心度量**：每周产出≥3个有效信号（事后验证涨幅>10%的算有效）

---

## 架构设计

```
[币安公开API] ──免费──→ [VPS Python脚本] ──cron──→ [信号判定引擎] ──→ [Discord通知]
                              │
                              ├── 模块1: 新币上线狙击
                              ├── 模块2: 异常波动扫描  
                              ├── 模块3: 恐慌抄底信号
                              └── 模块4: 资金费率套利（Phase 2）
```

**数据源（全部免费，无需Key）**：
- `api.binance.com/api/v3/ticker/24hr` — 全市场24h行情
- `api.binance.com/api/v3/klines` — K线数据
- `api.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query` — 官方公告
- `api.binance.com/api/v3/ticker/price` — 实时价格
- `fapi.binance.com/fapi/v1/premiumIndex` — 资金费率（合约）

---

## 里程碑

### Phase 1: MVP（3天）— 新币狙击 + 异常波动
- **M1.1**: 新币上线公告监控脚本 → cron每60秒轮询
- **M1.2**: 全市场异常波动扫描脚本 → cron每5分钟
- **M1.3**: Discord通知集成（统一通知到指定频道）
- **M1.4**: 信号日志记录（SQLite写入ops.db）
- **交付物**: 2个cron任务运行 + Discord频道收到信号

### Phase 2: 恐慌指标 + 资金费率（Phase 1验证有效后）
- **M2.1**: MEME板块恐慌指数计算（板块均跌>8%触发）
- **M2.2**: 合约资金费率异常扫描（费率>0.1%或<-0.05%）
- **M2.3**: 信号回测验证框架（自动追踪信号后24h/72h表现）
- **交付物**: 恐慌/费率信号 + 自动验证报告

### Phase 3: 接入币安Skills（Phase 2验证有效后）
- **M3.1**: trading-signal（Smart Money链上信号）
- **M3.2**: crypto-market-rank（热度排名）
- **M3.3**: meme-rush（MEME新币监控）
- **M3.4**: query-token-audit（安全审计过滤）
- **交付物**: 多源信号融合 + 安全过滤

---

## 成本预算

| 项目 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| API费用 | $0 | $0 | 待评估 |
| LLM Token | ~$0.5（开发调试） | ~$0.3 | ~$1 |
| VPS资源 | 已有 | 已有 | 已有 |
| 人力 | Reese + subagent | Reese | Reese |

---

## 分工

| 角色 | 职责 |
|---|---|
| **Reese (CEO)** | 架构设计、信号判定逻辑、cron调度、Discord通知、Phase 2/3规划 |
| **Subagent (廉价模型)** | 编写Python脚本（公告解析、行情扫描、数据入库） |
| **Fiona (MacBook)** | 不参与本项目（原因：需24/7运行，MacBook不适合） |
| **老板** | 验证信号质量、决定是否进Phase 2、提供交易反馈 |

---

## 风险与约束
1. 币安API有IP限速（1200次/分钟）→ 合理控制轮询频率
2. 公告解析可能延迟几秒 → 不做高频交易，做信号通知足够
3. 信号≠交易建议 → 所有通知附带免责声明
