# Elon 推文 Polymarket 交易系统 — 项目状态报告
> 更新时间: 2026-03-24 17:30 UTC+8

## 一、当前策略（算法说明）

### 核心模型：条件概率线性回归
```
Day7_final = 1.2503 × Day5_cumulative + 84.18
标准差 = 45.8 条
```
- 输入：Day5（第5天）累计推文数
- 输出：Day7（最终）推文总数的高斯概率分布
- 对每个 bracket 计算 P(落在该区间) = Φ((hi-mean)/std) - Φ((lo-mean)/std)
- Edge = P_model - Market_ask_price
- 入场条件：edge > 8%

### 三因子混合（trader.py 中实现）
1. **历史基率**：该 bracket 在70周历史中的命中频率
2. **速率动量**：当前推文速率外推到 Day7 的高斯概率
3. **时间权重**：越接近结束越信任实时数据（regime_weight = 0.3 + elapsed × 0.6）

### 当前实时信号 (2026-03-24)
- 累计 161 条，Day 3.7/7
- 速率趋势：Day2=64 → Day3=51 → Day4=31（递减）
- 预测终点：267条（三模型均值）
- 最优 bracket：240-259 (ask=0.061, edge=+0.74)

## 二、回测真实结果

### ⚠️ Sharpe 2.41 是无效数据
- 用的是**模拟市场价格**，不是真实盘口
- 回测代码在 `backtest_v2.py`，517行

### 真实数据回测状态
- 70周 Day5 盘口快照（`day5_price_snapshots.json`）：时间范围 2024.5-2025.9
- 42周推文历史（`weekly_history.json`）：时间范围 2025.11-2026.3
- **两个数据集时间不重叠，无法做完整回测**
- 历史周 bracket 分档范围每周不同，不可跨周比较

### 可做的回测
- 用 Day5 快照中的"隐含概率分布"对比实际结算结果 → 计算市场定价误差
- 但没有 Day5 累计推文数，无法运行条件概率模型

## 三、历史数据可获取性

### 已有
| 数据 | 文件 | 范围 | 说明 |
|------|------|------|------|
| 推文周总量 | weekly_history.json | 42周 (2025.11-2026.3) | 含每日明细 |
| Day5盘口快照 | day5_price_snapshots.json | 70周 (2024.5-2025.9) | 含结算结果 |
| 历史bracket结算 | historical_brackets.json | 70周 | bracket+结算价 |
| 当前周每小时价格 | current_week_price_history.json | 本周 | 30个bracket, 175点/bracket |
| 全量时序数据 | full_timeseries.json | 近期 | 推文时序 |

### 不可获取（Polymarket 限制）
- ❌ 历史周的 orderbook depth（结算后被清除）
- ❌ 历史周的 tick-by-tick 交易数据

### 外部数据源（待探索）
- [poly-data-xyz/poly-data-docs](https://github.com/poly-data-xyz/poly-data-docs) — Polymarket 历史数据 API 文档项目
- Polymarket 官方 `prices-history` API — 仅当前活跃市场可用
- Dune Analytics — 可能有链上交易数据
- The Graph Subgraph — Polymarket 链上事件

## 四、执行链路状态

| 组件 | 状态 | 说明 |
|------|------|------|
| 推文数据 API | ✅ 通 | xtracker.polymarket.com |
| 盘口价格 API | ✅ 通 | gamma-api + clob.polymarket.com |
| API Key 认证 | ✅ 通 | derive_api_creds 成功 |
| 非negRisk下单 | ✅ 通 | Iran YES/NO 成功下单+取消 |
| **negRisk下单** | ❌ 失败 | 需要传 `negRisk: true` 选项（刚发现） |
| USDC.e 余额 | $6.11 | EOA 链上 |
| Native USDC | $5.15 | 需 swap 为 USDC.e |
| NegRisk Allowance | ✅ MaxUint256 | 已授权 |

### negRisk 下单修复方案
根据 [Polymarket 官方文档](https://docs.polymarket.com/advanced/neg-risk.md)：
```python
# Python SDK 需要这样传：
from py_clob_client.clob_types import PartialCreateOrderOptions
options = PartialCreateOrderOptions(neg_risk=True)
resp = client.create_and_post_order(order_args, options)
```
**之前一直没传 `neg_risk=True`，这就是所有 "not enough balance" 错误的根因。**

## 五、Dashboard 状态

- URL: http://clawlabs.top/elon2 (简化版)
- 显示：累计推文、进度、Day7预测、每日柱状图
- 缺失：策略信号、盘口价格、模型概率对比、回测结果
- 原版 /elon 有 SSR 渲染问题（已修复基本数据）

## 六、关键问题 & 下一步

### P0: 立刻修复 negRisk 下单
加 `neg_risk=True` 参数，重试下单

### P1: 数据采集自动化
- 每小时抓取30个bracket价格 + 推文数存入SQLite
- 从本周开始积累真实 orderbook 数据

### P2: 外部历史数据
- 调研 poly-data-xyz 是否有历史价格数据
- 查 Dune Analytics 链上交易记录
- 搜索 Twitter/GitHub 社区是否有人分享过数据集

### P3: Dashboard 重做
- 展示实时策略信号 + 模型概率 vs 市场价格
- 展示历史预测准确度

## 七、文件清单

```
/root/.openclaw/workspace/projects/elon-poly/
├── STATUS.md          ← 本文件
├── HANDOFF.md         ← 交接文档
├── trader.py          ← 主交易循环 (391行)
├── backtest_v2.py     ← 回测引擎 v2 (517行)
├── algo_v3.py         ← 优化算法 (318行)
├── backtest_engine.py ← 回测引擎 v1 (469行)
├── iterate.py         ← 参数优化 (227行)
├── dashboard_api.py   ← Flask API (81行)
├── price_monitor.py   ← 价格监控 (58行)
├── fetch_history.py   ← 数据抓取 (94行)
├── weekly_history.json       ← 42周推文数据
├── day5_price_snapshots.json ← 70周Day5盘口
├── historical_brackets.json  ← 70周结算结果
├── current_week_price_history.json ← 本周每小时价格
├── full_timeseries.json      ← 推文时序
├── iterate_log.jsonl         ← 优化日志
└── issue.md                  ← 问题追踪
```

## 八、当前持仓 & 监控

### 持仓
| 区间 | 股数 | 买入价 | 成本 | 状态 |
|------|------|--------|------|------|
| 280-299 | 23.1 | $0.13 | $3.00 | matched |
| 300-319 | 17.6 | $0.17 | $2.99 | matched |

### 买入理由（诚实版）
- 主要目的：**验证 negRisk 执行链路**，不是策略驱动的高确信交易
- 区间选择：模型预测终点 267-330（三模型分歧大），280-319 覆盖中间区域
- ⚠️ 这不是经过回测验证的策略入场，是工程验证单

### 监控
- cron: `elon-poly-monitor` (每30分钟)
- 告警条件: 推文突变>20条/30min, P&L变动>30%, 预测偏离持仓区间
- 状态文件: `/tmp/elon_poly_monitor.json`
- 脚本: `monitor.py`

### 结算条件
- 如果最终推文落在 280-319: 赢约 $37 (23.1+17.6股 × $1 - $6成本)
- 如果落在区间外: 亏 $6

## 九、资金分布

| 地址 | 类型 | 余额 |
|------|------|------|
| 0xcD1862...10552 | EOA | $6.11 USDC.e + $5.15 USDC |
| 0x13e1E5...4Bfa4 | Safe AA | $0 (已转出) |
| CLOB 内部 | Polymarket | $6.11 |
