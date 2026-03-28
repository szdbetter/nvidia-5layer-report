# Polymarket 自动化交易系统 — 完整技术规格书

**版本**: v1.0  
**日期**: 2026-03-27  
**负责人**: Reese (AI CEO)  
**交接对象**: Claude Code 重写团队

---

## 一、项目全景

本项目包含三个相互独立的 Polymarket 交易系统：

| 系统 | 目标市场 | 策略类型 | 现状 |
|------|---------|---------|------|
| **Elon Poly** | Elon本周推文数 bracket prediction | 方向性预测（低胜率高盈亏比） | ❌ 实盘亏损-$5.43，已停 |
| **Iran Ceasefire** | US×Iran停火概率 | 地缘政治事件驱动 | ⚠️ 持有NO仓，浮亏 |
| **LP Farming** | 所有negRisk CLOB市场 | 被动做市商赚取流动性奖励 | 🔴 研究阶段，未启动 |

---

## 二、Elon Polymarket 交易系统（已亏损终止）

### 2.1 背景与目标

**市场结构**：
- Polymarket 上每周有一个 "Elon Musk 本周推文数" 市场
- 把推文总数分成30个条件bracket（280-299, 300-319, ..., 600+）
- 每个bracket可买 YES（赌最终落在这个区间）或 NO
- YES 结算为 $1（落在区间）或 $0（未中）
- 市场运作在 Polygon 网络，使用 negRisk CTF 代币

**目标**：用算法预测 Elon 最终推文数落在哪个 bracket，在市场错误定价时买入 YES 获取概率套利。

**事件信息**：
- Event ID: 278377（March 20–27, 2026）
- 结算时间: 2026-03-27 15:59 UTC
- 追踪: xtracker `d861bacb-6108-45d6-9a14-47b9e58ea095`
- 链接: https://polymarket.com/event/elon-musk-of-tweets-march-20-march-27

### 2.2 策略模型

**三因子混合模型**（`backtest_v2.py`）：
1. **条件概率分布**：基于历史70周数据，建立 Day5累计 → Day7最终 的线性回归
   ```
   Day7_final = 1.2503 × Day5_cumulative + 84.18
   标准差 = 45.8 条
   ```
2. **动量矩阵**：当周已有日均速率 → 判断 HIGH/LOW 活跃状态
3. **制度分类（Regime）**：HIGH（选举/DOGE期300-500条/周）vs LOW（退场期150-250条/周）

**最优参数**（回测结果）：
- 入场日: Day6（最优）、Day5（次优）
- min_edge: 6%（宽松）→ 10%（严格）
- 多档×2分散：同时持有相邻两个bracket

**盘口Edge计算**：
```
edge = P_model(bracket) - best_ask
入场条件: edge > 阈值
```

### 2.3 原始回测结果（无效数据）

⚠️ **致命问题**：回测 Sharpe 2.41 使用的是**模拟市场价格**，不是真实 Polymarket orderbook 数据。

- 70周价格快照（2024.5–2025.9）与42周推文历史（2025.11–2026.3）**时间不重叠**
- 无法在真实价格上验证策略
- 历史bracket分档范围每周不同，不可跨周比较

### 2.4 实盘执行过程

**资金**：
- EOA `0xcD1862c43F7F276026AA1579eC2b8b9c02c10552`：$7.31 USDC.e
- Safe AA `0x13e1E54C0dB451a990646913355B56255484Bfa4`：$5.16 USDC.e

**执行记录**：
- 2026-03-24：买入 280-299 YES × 23.1股 @ $0.13（验证链路）
- 2026-03-24：买入 300-319 YES × 17.6股 @ $0.17（验证链路）
- 2026-03-25：预测跌至233，触发止损，全仓平
- 2026-03-26：320-339 意外以7.9% edge（低于8%阈值）入场，仓位从$4跌至$0.24

### 2.5 亏损分析（复盘）

**最终结果**：起始$8.61 → 剩余$3.18，亏损 **-$5.43 (-63%)**

**根因**：
1. **持仓追踪断裂**：positions.json 为空{}，daemon不知道有持仓，止损永不触发
2. **过度交易**：220-239 在5小时内进出5次，摩擦成本$3+
3. **策略cron有写权限**：可修改代码+重启daemon，引入不一致状态
4. **监控≠干预**：每小时汇报但从不执行止损
5. **风控参数过松**：止损-60%才出，实际-87.5%已触发归零

**硬止损规则**（修复后）：
- 单笔止损: -30%（不是-60%）
- 单日熔断: -30%总资金
- 触发后全部平仓+停daemon+告警

### 2.6 技术架构

**文件清单**：
```
projects/elon-poly/
├── backtest_v2.py     # 主回测引擎（517行）
├── backtest_engine.py  # 底层回测v1（469行）
├── algo_v3.py          # 制度感知算法（318行）
├── trader.py           # 主交易循环（391行）
├── iterate.py          # 参数优化（227行）
├── dashboard_api.py    # Flask API（81行）
├── price_monitor.py    # 价格监控（58行）
├── fetch_history.py    # 数据抓取（94行）
├── daemon.py           # systemd守护进程
├── strategy_engine_v2.py # 三因子策略引擎
├── decision_log.jsonl  # 决策日志（96+条）
├── orderbook_snapshots.jsonl # 订单快照（99条）
├── positions.json      # 持仓追踪（现已废弃）
├── weekly_history.json       # 42周推文数据
├── day5_price_snapshots.json # 70周Day5盘口
├── historical_brackets.json  # 70周结算结果
└── current_week_price_history.json # 本周每小时价格
```

**系统架构（修复后）**：
- Daemon Layer: systemd `elon-poly.service`，5分钟循环，纯Python硬编码逻辑
- Strategy Layer: 60分钟cron，MiniMax-M2.7分析（已禁用）
- 状态文件: `/tmp/elon_strategy.json`
- 持仓: **从链上CTF合约读取**，不再依赖本地positions.json

### 2.7 API集成细节

**数据源**：
- xtracker.polymarket.com：实时推文数
- gamma-api.polymarket.com：实时盘口价格（免费，无Key）
- clob.polymarket.com：订单簿（需签名认证）

**negRisk下单关键参数**：
```python
from py_clob_client.clob_types import PartialCreateOrderOptions
options = PartialCreateOrderOptions(neg_risk=True)  # 必须传！
# 之前一直没传这个参数，导致所有balance错误
```

**钱包凭证**（`.env`）：
```
POLYMARKET_API_KEY=...
POLYMARKET_SECRET=...
POLYMARKET_PASSPHRASE=...
POLYMARKET_MNEMONIC=<24词助记词>
```

**CTF合约地址**（Polygon）：
- NegRisk CTF Exchange: `0xC5d563A36AE78145C45a50134d48A1215220f80a`
- USDC.e: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`

---

## 三、Iran Ceasefire 宏观监控系统

### 3.1 背景

**目标**：监控霍尔木兹海峡局势，通过三个数据源交叉验证美伊停火概率：
1. JMIC海峡通行量（真实AIS数据）
2. 劳合社战争险费率
3. Polymarket停火盘口

**核心逻辑**：
- 通行量环比下滑≥10% OR 战争险涨幅≥50% → 冲突升级，**持有NO仓**
- 通行量环比回升≥30% OR 战争险跌幅≥40% → 封锁缓解，**NO仓止盈**

### 3.2 系统架构

**部署路径**: `/root/.openclaw/workspace/polymarket-runtime/`

**文件**：
- `poly_macro_engine.py`：宏观引擎核心逻辑
- `com.clawlabs.poly_macro.plist`：macOS launchd 配置

**当前状态**：
- Daemon已停（Fiona上的launchd任务已 unload）
- 脚本已完成并回测通过
- 未完成物理部署（因Fiona节点状态）

### 3.3 真实局势（2026-03-16记录）

- 自2月28日起海峡接近关闭
- 正常通行量约60艘/天，当时接近零
- 150余艘船滞留
- 吞吐量<正常水平的2%
- 战争险价格上涨16倍
- 布伦特原油价格暴涨

**当时盘口**：
- 3月31日停火 YES 11.5% / NO 88.5%，成交量$9.46M
- 4月30日停火 YES 35.5% / NO 64.5%，成交量$2.5M

---

## 四、Polymarket LP流动性挖矿

### 4.1 机制概述

**两种独立激励**：
1. **Liquidity Rewards**：挂限价单在orderbook里即可得，不需要成交，每分钟采样，每天UTC午夜结算
2. **Maker Rebates**：挂单被吃掉才赚钱，按taker fee比例返

### 4.2 评分公式

```
S(v,s) = ((v-s)/v)² × b

v = 最大激励spread（市场参数，API可查）
s = 距离midpoint多少
b = 挂单量
```

**关键特性**：
- 二次方曲线：离midpoint 1分 vs 3分，得分差9倍
- 单边挂单：得分÷3（惩罚）
- midpoint在0.10-0.90外：必须双边，否则零分

### 4.3 风险

1. **逆向选择**：挂单越靠近midpoint越容易被知情交易者吃掉
2. **临近结算gap**：最后48小时概率加速收敛
3. **资金效率**：双边挂单=资金利用率50%

### 4.4 年化收益

| 资金规模 | 市场选择 | 预估日收益 | 年化 |
|---------|---------|-----------|-----|
| $1K | 低竞争+激励市场 | $2-5 | 73-182% |
| $10K | 中等竞争 | $20-50 | 73-182% |
| $100K | 高竞争主流 | $150-300 | 55-110% |

### 4.5 适合市场条件

✅ 适合：
- 长期市场（3个月+到期）
- midpoint在0.30-0.70
- 激励池大但参与者少
- 低新闻敏感度

❌ 避开：
- 24-48小时内到期
- 有已知催化剂（选举日、数据发布）
- midpoint<0.10或>0.90

---

## 五、数据架构

### 5.1 数据库

**Fiona本地**：`/Users/ai/.openclaw/workspace/data/ops.db`
- `market_prices` 表：存所有市场价格数据
- 每2分钟增量更新

**VPS同步**：`/root/.openclaw/workspace/data/ops.db`
- 每5分钟从Fiona同步
- 通过 `nodes.run` + SQL dump/import

**同步机制**：
```python
# 从Fiona导出
ssh ... 'sqlite3 ops.db "SELECT * FROM market_prices WHERE ts > $LAST_TS"'

# 导入VPS
sqlite3 ops.db ".import ... market_prices"
```

### 5.2 数据可获取性

**已有**：
- 70周 Day5 盘口快照（2024.5–2025.9）
- 42周推文历史（2025.11–2026.3）
- 本周每小时30个bracket价格（175个数据点/bracket）

**不可获取**：
- 历史周 orderbook depth（结算后清除）
- 历史周 tick-by-tick 交易数据
- 链上结算前价格历史

**待探索**：
- poly-data-xyz/poly-data-docs
- Dune Analytics 链上数据
- The Graph Polymarket Subgraph

---

## 六、监控与告警

### 6.1 Fiona节点监控架构

**节点**：fiona-mbp2015（MacBook Pro 2015，macOS）
- OpenClaw版本：2026.3.13
- 状态：✅ 在线（2026-03-27）
- 远程IP：100.108.26.48

**两个独立监控链路**：

1. **主链路（主动告警）**：Fiona本机 `poly_monitor_daemon.py`
   - launchd管理：`com.openclaw.polymonitor`
   - 条件：TP/SL触发、连续错误、daemon退出
   - 30分钟冷却防刷屏
   - 状态：❌ 已停

2. **兜底链路（4小时审计）**：VPS `poly-fiona-readonly-monitor`
   - Cron Job ID: `493c8b30-7523-4ff6-be7b-44dcbf05182d`
   - 检查：`/tmp/poly_latest_result.json` 新鲜度 + `ops.db` 行数
   - 状态：❌ 已禁用

### 6.2 告警发送目标

- 主要：Discord频道 `1480446033531240469`（#polymarket）
- 方式：`POLY_DISCORD_WEBHOOK_URL` → `DISCORD_BOT_TOKEN` → `openclaw message`

### 6.3 告警条件

| 条件 | 消息 |
|------|------|
| 心跳>3分钟 | `[POLY] 🚨 FIONA DOWN | poly daemon unresponsive >3min` |
| ok=false | `[POLY] 🔴 FIONA ERROR | ok=false` |
| alert非空 | `[POLY] ⚠️ ` + alert内容 |
| DB同步延迟 | `[POLY] 🚨 FIONA SYNC STALE | last data older than 10min` |

---

## 七、历史错误与教训

### 7.1 Elon交易系统致命错误

1. **持仓文件 vs 链上真相**：用本地positions.json而非从CTF合约读balanceOf
2. **止损嵌入策略**：止损逻辑被策略cron覆盖，永远不触发
3. **cron有写权限**：可改代码+重启daemon，导致状态不一致
4. **最小持仓时间缺失**：220-239在5小时内交易5次，摩擦成本$3+
5. **风控阈值过松**：止损-60%，实际-87.5%已归零
6. **dry-run验证缺失**：没有完整测试周期就直接上实盘

### 7.2 铁律（必须遵守）

1. 持仓状态**必须从链上**读取
2. 止损是**独立watchdog进程**，不是策略的一部分
3. 单日熔断**-30%**（不是-60%）
4. 分析cron**只读**，不给写代码权限
5. **没有完整dry-run验证周期，不上实盘**
6. BUY NO = 做空YES（negRisk CLOB不支持裸SELL YES）

---

## 八、当前状态（2026-03-27）

### 8.1 系统状态

| 系统 | 状态 |
|------|------|
| Elon Poly Daemon | ❌ stopped |
| Iran Macro Daemon | ❌ stopped（launchd已unload） |
| 所有Elon Poly Crons | ❌ disabled |
| LP Farming | 🔴 研究阶段 |
| Polymarket Alpha | 🔴 策略扫描，未执行 |

### 8.2 钱包状态

| 地址 | 类型 | 余额 |
|------|------|------|
| `0xcD1862c43F7F276026AA1579eC2b8b9c02c10552` | EOA | ~$3.18 USDC.e |
| `0x13e1E54C0dB451a990646913355B56255484Bfa4` | Safe AA | ~$0 |

### 8.3 Dashboard

- URL: http://clawlabs.top/elon2（HTTP，port 1980）
- 显示：实时推文数、Day进度、预测
- 问题：SSR数据注入曾有问题，后改用客户端fetch

---

## 九、待开发项目优先级

### P0 - LP Farming Bot（最高优先级）
- 需要：$1000+启动资金、Python自动化bot、PyClobClient
- 核心：选对市场 + 紧贴midpoint双边挂单 + 及时补单

### P1 - Iran停火套利监控
- 已完成：引擎逻辑、回测、数据源
- 待完成：Fiona节点恢复 → 重新部署daemon

### P2 - Elon Poly系统重建
- 需要：完整重写，遵守铁律，真实价格验证
- 当前：所有crons已禁，daemon已停

### P3 - Polymarket Alpha扫描
- 目标：扫描所有市场找套利机会（规则模糊性）
- 现状：6大案例，4个可复用模式，覆盖$476M流动性

---

## 十、技术债务与约束

1. **数据不重叠**：70周价格与42周推文历史时间不重叠，无法做真实价格回测
2. **无历史orderbook**：Polymarket不保存历史depth数据
3. **$12本金不足**：最小有效仓位$20/次，$12连一笔都吃力
4. **Fiona节点不稳定**：曾多次离线，需定期检查
5. **CLOB API需要签名**：钱包私钥必须在VPS或Fiona上，存在安全权衡

---

## 十一、环境信息

**VPS**：` clawlabs.top`，端口1980（Dashboard）、443（Xray VLESS）
**Fiona**：MacBook Pro 2015，macOS，OpenClaw 2026.3.13
**数据库同步**：每5分钟Fiona→VPS，ops.db
**Discord频道**：1480446033531240469（#polymarket，核心告警）
**Gamma API**：api.minimax.chat（MiniMax验证OK）

---

*本文件由Reese于2026-03-27生成，供Claude Code团队完整重写系统使用。*
