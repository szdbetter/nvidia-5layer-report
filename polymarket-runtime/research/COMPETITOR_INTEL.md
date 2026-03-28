# Polymarket Elon 推文盘口竞争者情报报告
**收集时间**: 2026-03-20 UTC  
**研究范围**: GitHub / Reddit / Twitter / Polymarket 生态

---

## 1. 开源项目汇总

### 🔴 顶级威胁（已具备完整策略逻辑）

#### TweetCast.xyz — 最强竞争对手
- **URL**: https://tweetcast.xyz/
- **核心策略**: 使用市场隐含收益率 (market-implied rate) 作为先验，结合负二项分布 (Negative Binomial) 建模推文数量不确定性
- **模型公式**:
  - `rate = (mkt_mean − count) / hours_left` （市场隐含率）
  - `λ = rate × hours_remaining` （剩余推文期望值）
  - `R ~ NegBin(λ, r)` （负二项分布建模）
  - `edge = P(bracket | R) − market_prob`
- **覆盖范围**: Elon Musk (X), Donald Trump (Truth Social), Andrew Tate (X)，各自独立校准
- **当前实时数据**（March 20窗口）:
  - Model μ: 98 | Market Mean: 98 | Implied Rate: 32.7/day | σ: ±23
  - 65–89 bracket: 市场39.5% vs 模型28.1% → **−11.4% edge** (HIGH EDGE 卖)
  - 90–114 bracket: 市场31.5% vs 模型39.9% → **+8.4% edge** (HIGH EDGE 买)
  - 115–139 bracket: 市场12.5% vs 模型19.6% → **+7.1% edge** (DIVERGED)
  - 140–164 bracket: 市场6.0% vs 模型2.8% → **−3.2% edge** (FAIR VALUE)
- **数据源**: XTracker (每5分钟刷新)，免费无需认证
- **评级**: ⚠️ **最高威胁** — 统计严谨，实时更新，已产品化

---

#### PolyX (Ibere22) — AI量化交易系统
- **URL**: https://github.com/Ibere22/Automatic-Trading-System-on-Polymarket
- **Stars**: ~2 (小众项目)
- **核心策略**:
  1. 🐦 爬取 Elon 最新推文/转推/自回复
  2. 🧠 Neural Prophet 时序预测模型预测未来推文数
  3. 📊 对比 AI 预测 vs Polymarket 赔率
  4. 🎯 寻找最大边缘机会
  5. 🤖 自动执行交易（有风险管理模块）
- **技术栈**: Python, Neural Prophet, Polymarket API
- **评级**: 中高威胁 — AI预测框架完整，但Neural Prophet对高方差事件（如Elon发推）的预测效果存疑

---

#### Polymarket-Edge-Tracker (Jaisev-Sachdev) — 实时信号面板
- **URL**: https://github.com/Jaisev-Sachdev/polymarket-edge-tracker
- **核心策略**:
  - 从 XTracker 实时获取推文计数
  - 基于当前速率投影最终计数
  - 计算统计概率 vs 市场赔率，输出 BUY/SELL/HOLD 信号
  - 置信度: HIGH (>15% edge), MEDIUM (8-15% edge)
- **技术栈**: Next.js 14, TypeScript, Tailwind CSS, 免费API（XTracker/CoinGecko/Gamma）
- **特点**: 仅是信号面板（非自动交易），展示 Elon's run rate → projected count → 每档概率
- **评级**: 中威胁 — 免费开源，实时性强，但无交易执行

---

### 🟡 中等威胁

#### Tweet Quant — 专业分析报告 (Terry Lee)
- **URL**: https://news.polymarket.com/p/tweet-quant
- **核心发现**:
  - 分析了86周历史市场数据（2024年6月 ~ 2026年2月）
  - 发现了3个可交易边缘因素: **momentum（动量）、weekly pacing（周内节奏）、outlier news events（突发新闻）**
  - 建立了 elonXforecast.com 工具
  - 关键洞察: "Elon的发推习惯相当可预测"（与随机游走假说相反）
  - 交易量从 $136k 增长到 **$46.5m/周**（342倍增长）
- **评级**: 中威胁 — 理念领先但未公开代码，已产品化为付费内容

---

#### Polymarket-Arbitrage-Bot 系列
- **主要项目**:
  - `qntrade/polymarket-5min-15min-arbitrage-bot` — 5分钟/15分钟窗口套利
  - `Gabagool221/polymarket-trading-bot-python` — Python执行
  - `Datagoverment/polymarket-arbitrage-bot`
- **注意**: 这些大多是做二元市场套利（YES/NO价差），并非专门针对推文计数市场
- **评级**: 低威胁（针对Elon推文市场无效）

---

### 🟢 边缘项目（低威胁或已停更）

| 项目 | URL | 说明 |
|------|-----|------|
| vslaykovsky/elonbot | GitHub | 监控Elon发推买卖加密货币（非Polymarket） |
| waleedrizwan/elon_tweet_analyzer | GitHub | 简单推文分析，无交易逻辑 |
| xmurcia/elon-asymetric-tweet-bets | GitHub | 非对称押注概念实验，0 stars |
| parlpott-gif/polymarket_musk_monitor | GitHub | 简单监控，0 stars |
| polymarketsignal.com | 网站 | SEO内容农场，非实时策略 |
| polycatalog.io | 网站 | 赔率解读指南，无交易逻辑 |
| xtracker.me | 网站 | Elon发推活动追踪，非交易 |

---

## 2. Reddit 讨论摘要

- Reddit搜索 `polymarket+elon+tweets` 结果极少，多数指向外部工具/博客
- 核心讨论模式:
  1. **"Is there an edge?"** — Terry Lee的Tweet Quant文章是唯一认真回答此问题的公开分析
  2. **"How does XTracker count work?"** — 规则澄清（主推文/引用推文/转推送算，回复不计入，但带媒体的主页回复计入）
  3. **"Which bracket is best value?"** — 讨论分散，无系统性答案
  4. **获利经验分享**: **极少公开**。成功交易者倾向于保密策略而非分享
- 结论: Reddit上无公开的、经过验证的获利策略分享。TweetCast.xyz是唯一已产品化的边缘发现工具。

---

## 3. 已知竞争者情况

### 量化团队 / 专业参与者
| 参与者 | 类型 | 策略特征 | 估算规模 |
|--------|------|---------|---------|
| TweetCast.xyz | 产品化SaaS | 负二项分布+市场隐含率，每日更新边缘信号 | 中型（已获社区广泛使用） |
| Terry Lee / elonXforecast | 个人量化 | Momentum+过渡矩阵，86周历史数据回测 | 小型 |
| PolyX (Ibere22) | 自动交易机器人 | Neural Prophet + 自动执行 | 极小型（代码未广泛传播） |
| Polymarket专业做市商 | 做市商 | 提供流动性，倾向于中性套利而非方向性押注 | 大型（有报道称单账号交易量达数百万美元） |

### 市场结构
- **规模**: 从 $136k → $46.5m/周（342倍增长），已形成微型资产类别
- **庄家**: Polymarket平台提供基础流动性；专业量化团队提供深度
- **当前窗口 (March 20-27)**: 共识区间 300-340 推文（~32.7/day），顶部档位各 ~11.5% 隐含概率
- **热点档位**: 280-299 (10.5%), 300-319 (11.5%), 320-339 (11.5%)

---

## 4. 市场当前价格数据

### 当前活跃市场 (March 20, 2026)
来源: Polymarket.com / XTracker / TweetCast 实时数据

| 档位 | 市场隐含概率 | 模型概率 | Edge | 信号 |
|------|------------|---------|------|------|
| 65-89 | 39.5% | 28.1% | −11.4% | HIGH EDGE 卖 |
| 90-114 | 31.5% | 39.9% | **+8.4%** | HIGH EDGE 买 |
| 115-139 | 12.5% | 19.6% | **+7.1%** | DIVERGED 买 |
| 140-164 | 6.0% | 2.8% | −3.2% | 公平 |
| 165+ | 低 | 低 | - | - |

**关键观察**:
- 当前市场共识: ~98推文（7天窗口），约 **32.7/天**
- 90-114 和 115-139 档位存在显著正边缘（市场低估）
- 65-89 档位被过度定价（市场高估）
- Elon历史上周均水平约 54-57推文/天（高频活动模式）

### 历史数据 (Feb 24 - Mar 3, 2026 窗口)
- PolymarketSignal.com 分析: 380-399 档位领跑 (10.5% 概率)，400-419 档位 4.95%
- 共识转向7天窗口约380-399推文区间（约54-57/天）
- XTracker累计计数: ~23,451 tweets (as of March 6 resolve)

---

## 5. 竞争强度综合评分

### 评分: **7.5 / 10**

| 维度 | 评分 | 说明 |
|------|------|------|
| 工具成熟度 | 8/10 | TweetCast已产品化，统计严谨 |
| 量化参与者密度 | 7/10 | 已有专业做市商+多个量化机器人 |
| 信息透明度 | 6/10 | 代码开源极少，策略高度保密 |
| 边缘可获取性 | 5/10 | 90-114/115-139仍有~7-8%边缘，但窗口期短 |
| 市场规模 | 9/10 | $46.5m/周，足够大值得专业参与 |
| 监管/限制 | 2/10 | 基本无监管，进入壁垒低 |

### 关键结论

1. **TweetCast 是最大威胁** — 它已解决了"市场隐含率"这个核心问题，且免费提供给所有用户。它的负二项分布模型是统计上最严谨的方法，构成了当前市场效率的主要推动力。

2. **边缘仍然存在，但窗口期极短** — 90-114 和 115-139 档位有 ~7-8% 边缘。这相当于年化 ~250%+ 的预期收益（在Kelly criterion下）。但 TweetCast 用户也会看到同样的信号，边缘会在小时内被套平。

3. **动量因素是独特边缘来源** — Terry Lee 发现的 momentum/weekly pacing 因素在统计上可预测，但难以被简单的均值回归模型捕获。如果 Elon 本周发推高于均值，下周大概率也高于均值——这个因素目前未被 TweetCast 完全定价。

4. **策略建议**:
   - 不要在 TweetCast 已标注 "DIVERGED" 的档位追高
   - 重点关注 **90-114** 档位（+8.4% edge，当前最高）
   - 利用 **momentum 因素**: 当 Elon 本周发推超预期时，在下一周市场开市前提前买入
   - 新闻事件（非预期）是最大机会——模型无法预测突发新闻导致的发推飙升
   - 低流动性档位（140+）存在彩票效应机会，但期望值为负

5. **竞争壁垒**: 唯一可持续的竞争优势是:
   - 更快的执行速度（毫秒级而非分钟级）
   - 更好的新闻事件预测（不可行）
   - 更好的 momentum 量化模型（目前 TweetCast 未使用）
   - 跨市场联合押注（如结合 Trump Truth Social 市场和 Elon 市场对冲尾部风险）

---

*数据来源: EXA搜索, GitHub API, Reddit JSON API, Polymarket CLOB API, XTracker API, TweetCast.xyz, Polymarket.com, news.polymarket.com*
