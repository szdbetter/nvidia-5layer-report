# Elon Polymarket 策略 — 完整交接文档

**生成时间**: 2026-03-23 22:20 CST  
**接手人**: Claude（新对话）  
**项目路径**: `/root/.openclaw/workspace/projects/elon-poly/`  
**联系人**: 岁月（老板），Discord @cndbetter

---

## 一、项目背景

每周 Polymarket 上有一个「Elon Musk 本周推文数」市场，把推文总数切成30个档位（如 320-339、340-359 等），每档独立交易 YES/NO。

目标：用算法预测 Elon 最终落在哪个档位，在盘口低估时买入 YES，获取概率套利收益。

---

## 二、当前市场状态

| 项目 | 内容 |
|------|------|
| **当前周** | March 20–27, 2026 |
| **Gamma event_id** | 278377 |
| **xtracker tracking_id** | `d861bacb-6108-45d6-9a14-47b9e58ea095` |
| **市场链接** | https://polymarket.com/event/elon-musk-of-tweets-march-20-march-27 |
| **截止时间** | 2026-03-27 15:59 UTC |
| **当前日** | Day4（2026-03-23） |
| **累计推文** | 145条 |
| **每日明细** | 3/20: 7条，3/21: 64条，3/22: 51条，3/23: 23条 |

### 当前盘口（2026-03-23 21:49 CST）

| 档位 | Ask | Last |
|------|-----|------|
| 320-339 | 0.14 | 0.14 |
| 340-359 | 0.14 | 0.13 |
| 360-379 | 0.13 | 0.12 |
| 380-399 | 0.111 | 0.11 |
| 300-319 | 0.10 | 0.10 |
| 400-419 | 0.087 | 0.087 |

---

## 三、策略核心逻辑

### 三因子模型（algo_v3.py）

1. **条件概率分布表**：基于历史70周最终结果，估算各档位基础概率
2. **动量矩阵**：当周已有日均速率 → 判断 HIGH/LOW 活跃状态
3. **制度分类（Regime）**：
   - HIGH：2024年选举期 / DOGE任命期（推文量300-500+/周）
   - LOW：2025年后 DOGE 退场期（推文量150-250/周）

### 关键参数（已优化）

```
lookback = 20 周
regime_weight = 2
rate_threshold = 1.15
min_edge = 0.15（最严格模式）/ 0.06（宽松模式）
entry_day = Day6（最优）
```

### 盘口 Edge 计算

```
edge = P_model(bracket) - P_market(bracket)
P_market = bestAsk（买入价）
只在 edge > 阈值 时入场
```

---

## 四、回测结果（真实历史数据）

### 数据来源

- **历史价格**：70周 Day5 盘口快照（`day5_price_snapshots.json`，128KB）
- **历史结果**：70周实际推文总数（`weekly_history.json`）
- **历史档位**：每周全部档位价格（`historical_brackets.json`，75KB）
- **实时数据**：`live_prices.jsonl`（每30分钟追加，当前仅1条快照）

### 最新回测（iteration 21，2026-03-23 14:07 UTC）

| 指标 | 单档模式 | 多档×2 模式 |
|------|---------|-----------|
| 交易次数 | 34 | 34 |
| 胜率 | 23.5% | 23.5% |
| P&L | +$9,353 | +$8,436 |
| **Sharpe** | **2.41** ✅ | **5.37** ✅ |
| 最大回撤 | $1,367 | $586 |
| Avg Edge | 15.2% | 15.2% |
| EV | 1.674 | 1.473 |

> ⚠️ **重要警告**：回测基于历史Day5盘口价格（非真实入场价），存在一定乐观偏差。真实滑点/流动性待验证。Sharpe 2.41 来自模拟数据，需实盘验证。

### 历史数据覆盖

- 2024-05 ~ 2025-09：70周完整价格数据 ✅
- 推文日量数据：**只有 Nov 2025 以后才有**（xtracker 只存近期）
- 2026-03-20 起：实时推文+价格双源数据开始积累 ✅

---

## 五、钱包与资金

| 钱包 | 地址 | 余额 | 用途 |
|------|------|------|------|
| EOA（CLOB API直签） | `0xcD1862c43F7F276026AA1579eC2b8b9c02c10552` | ~$7.31 USDC.e | 实盘API交易 |
| Safe AA（UI） | `0x13e1E54C0dB451a990646913355B56255484Bfa4` | ~$5.16 USDC.e | 备用 |

**⚠️ 行动项**：Day5入场前需向 EOA 充值 $50–200 USDC（Polygon 网络）

### API 凭证

位置：`/root/.openclaw/.env`  
字段：`POLYMARKET_API_KEY`、`POLYMARKET_SECRET`、`POLYMARKET_PASSPHRASE`、`POLYMARKET_MNEMONIC`

API 连接状态：✅ py-clob-client 已验证可连（4条历史交易记录）

---

## 六、运行中的自动化任务

| Cron Job | ID | 频率 | 功能 |
|----------|-----|------|------|
| elon-live-price-monitor | `c369b96c-cef4-45aa-8d83-437205532160` | 每30分钟 | 抓实时推文+盘口写入 live_prices.jsonl |
| poly-iteration（已暂停） | `1aa92165-d4f6-4d9b-99ec-7cec2512d7c6` | 已停 | 原回测迭代循环 |

---

## 七、文件清单

| 文件 | 说明 |
|------|------|
| `algo_v3.py` | 当前最优算法（制度分类+三因子模型） |
| `algo_v3_result.json` | 制度感知回测结果（Sharpe 0.30，13笔交易） |
| `backtest_v2.py` | 主回测引擎（35周历史，Sharpe 2.41） |
| `day5_price_snapshots.json` | 70周Day5盘口快照（31KB） |
| `historical_brackets.json` | 历史全档位价格（75KB） |
| `weekly_history.json` | 历史每周最终推文总数（19KB） |
| `full_timeseries.json` | 完整时序数据（131KB） |
| `live_prices.jsonl` | 实时价格日志（追加） |
| `iterate_log.jsonl` | 迭代回测日志（21次迭代） |
| `issue.md` | 问题追踪与改进记录 |
| `price_monitor.py` | 实时监控脚本 |
| `backtest_engine.py` | 底层回测引擎 |

---

## 八、决策时间线

| 时间 | 事件 | 行动 |
|------|------|------|
| **Day4（今天 3/23）** | 145条推文，当前状态 | 等待，继续监控 |
| **Day5（3/26 周三）** | 方差收窄 ±25条 | 🔴 **入场决策窗口** - 运行模型，评估盘口 edge |
| **Day6（3/27 周四）** | 最优入场日（回测参数） | 备选入场 |
| **3/27 15:59 UTC** | 市场结算 | 结果揭晓 |

### Day5 决策流程

```python
# 伪代码
current_total = fetch_xtracker(TRACKING_ID)  # 实时推文数
prices = fetch_gamma(EVENT_ID)               # 当前盘口
signal = algo_v3.predict(current_total, prices, regime='LOW')  # LOW = 2026年

# 入场条件
if signal.edge > 0.08 and signal.bracket:
    # 计算下单金额（Kelly）
    amount = kelly_fraction * capital
    # 下单（需 USDC 余额 > $20）
    place_order(signal.bracket, amount)
```

---

## 九、当前挑战与待解问题

1. **制度判断模糊**：2026年3月 Elon 活跃度不明（DOGE 已基本退出），需根据当周数据实时判断是 HIGH 还是 LOW
2. **回测乐观风险**：Sharpe 2.41 基于历史Day5快照，真实入场价可能更差
3. **资金不足**：当前 $12 远不够，最小有效仓位 $20/次，建议充到 $200
4. **algo_v3 Sharpe 仅 0.30**：制度感知版本（只13笔交易），数据不足。主力回测（backtest_v2）Sharpe 2.41 但未考虑制度
5. **尚未做真实订单测试**：API 连通但从未实际下单，需先用 $1 测试流程

---

## 十、推荐下一步行动

**优先级排序：**

1. **P0 - 充值**：向 EOA 转 $100 USDC（Polygon），3/26前完成
2. **P1 - Day5模型运行**：3/26 早上拉实时数据，跑 algo_v3 或 backtest_v2，看 edge 是否 > 8%
3. **P2 - 小额测试**：用 $5 先走一遍完整下单流程（验证 API 路径）
4. **P3 - 制度判断**：当周145条已过Day4，按当前速度推算日均≈48条，全周预测约336条 → 与盘口中心 330 接近，edge 可能偏小

**Day5 入场评估命令（当时运行）：**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
python3 - << 'EOF'
import requests, json

TRACKING_ID = "d861bacb-6108-45d6-9a14-47b9e58ea095"
EVENT_ID = 278377

r1 = requests.get(f"https://xtracker.polymarket.com/api/trackings/{TRACKING_ID}?includeStats=true")
total = r1.json()['data']['stats'].get('total', 0)

r2 = requests.get(f"https://gamma-api.polymarket.com/events/{EVENT_ID}")
markets = r2.json().get('markets', [])

print(f"当前推文: {total}")
print("盘口 Top 10:")
liquid = [(m.get('groupItemTitle'), float(m.get('lastTradePrice') or 0)) for m in markets]
liquid = [(t, p) for t, p in liquid if p > 0.01]
liquid.sort(key=lambda x: -x[1])
for t, p in liquid[:10]:
    print(f"  {t}: {p:.3f}")
EOF
```

---

## 十一、模型核心代码位置

- **主回测**：`backtest_v2.py` → `run_backtest()` 函数
- **制度感知算法**：`algo_v3.py` → `RegimeAwareModel` 类
- **API 下单**：未封装，参考 py-clob-client 文档
- **凭证加载**：`from dotenv import load_dotenv; load_dotenv('/root/.openclaw/.env')`

---

*文档由 Reese (OpenClaw) 自动生成，2026-03-23*
