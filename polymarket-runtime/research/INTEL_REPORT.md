# Polymarket Elon 推文盘口 — 三平台情报研报

> 收集时间：2026-03-20 | 数据来源：GitHub / Twitter/X / Reddit

---

## 一、GitHub 高星项目分析

### 项目1：Polymarket/agents ⭐2576
- **项目地址**：https://github.com/Polymarket/agents
- **核心功能**：Polymarket 官方推出的 AI Agent 开发框架，支持 Python 3.9+，集成 Polymarket API、Langchain RAG、Chroma 向量数据库，可执行自主交易。包含 CLI 界面（`get-all-markets` 等命令）和模块化架构（Gamma.py 负责市场数据、Polymarket.py 负责交易执行、Objects.py 定义数据模型）。MIT 开源协议。
- **与我们策略的关联**：可直接复用其 API 封装和 RAG 架构做信息聚合；缺点是官方出品意味着所有人都能用，没有差异化。
- **关键代码逻辑**：CLI 命令格式 `python scripts/python/cli.py command_name [attribute value]`，交易入口 `python agents/application/trade.py`。

### 项目2：Jon-Becker/prediction-market-analysis ⭐2279
- **项目地址**：https://github.com/Jon-Becker/prediction-market-analysis
- **核心功能**：预测市场数据收集与分析框架，包含 Polymarket + Kalshi 最大公开数据集（36GiB 压缩包）。支持市场元数据收集、链上交易历史抓取、Parquet 存储、自动化进度保存。提供分析脚本框架可生成图表与统计数据。
- **与我们策略的关联**：**高价值**——可下载历史交易数据（`make setup` 即可获取 36GiB 历史数据），用于分析 Elon 推文市场历史价格走势与实际结果的相关性，作为模型训练的 ground truth。
- **关键代码逻辑**：`make index` 启动交互式菜单选择 indexer 收集新数据；数据存 `data/polymarket/` 和 `data/kalshi/`；`make analyze` 运行分析脚本。

### 项目3：pmxt-dev/pmxt ⭐1120
- **项目地址**：https://github.com/pmxt-dev/pmxt
- **核心功能**：CCXT for prediction markets（预测市场的统一交易 API），支持 Polymarket、Kalshi 等多平台统一接口。类似于加密货币领域的 CCXT，将不同交易所 API 统一封装。
- **与我们策略的关联**：如果策略需要同时操作 Polymarket 和 Kalshi，这是最佳起点；缺点是目前 Stars 偏低（1120），社区活跃度有限。
- **关键代码逻辑**：统一 REST + WebSocket 接口，一次编码支持多平台。

### 项目4：mvanhorn/last30days-skill ⭐4409
- **项目地址**：https://github.com/mvanhorn/last30days-skill
- **核心功能**：AI Agent 技能，研究任意话题在 Reddit、X、YouTube、HN、Polymarket、web 上的最新信息并综合摘要。**支持 Polymarket 市场数据**作为信号源，搜索结果按多因子加权评分（文本相关性 30%、24小时交易量 30%、流动性深度 15%、价格变动速度 15%、结局竞争度 10%），并对 Polymarket 合约按 5 因子综合排名。
- **与我们策略的关联**：**直接相关**——该技能已经整合 Polymarket 数据，可直接研究 Elon 推文市场讨论热度；其评分方法论（尤其是 Polymarket 专属评分体系）可借鉴；该技能支持 Open Claw（我们正在使用的平台）。
- **关键代码逻辑**：两阶段查询扩展 + 标签跨域桥接；支持 X handle 解析（搜索 "Elon Musk" 自动解析 @elonmusk 并抓取发帖）；可通过 `last30 watch` 添加监控主题。

### 项目5：warproxxx/poly-maker ⭐947（做市机器人）
- **项目地址**：https://github.com/warproxxx/poly-maker
- **核心功能**：Polymarket 自动做市机器人（MM Bot），在订单簿双侧同时挂单提供流动性，参数通过 Google Sheets 配置。包含实时订单簿监控（WebSocket）、仓位管理、自动仓位合并、价差管理。**警告：项目文档明确表示"在当前市场中不盈利，会亏损"**，因为竞争加剧。
- **与我们策略的关联**：**重要参考**——代码结构清晰，是理解 Polymarket 做市逻辑的最佳参考；但实盘不可用（当前竞争格局已变化）。文档特别指出"除非你愿意投入大量时间，否则不值得参与"。
- **关键代码逻辑**：依赖 Google Sheets 配置参数（含"Selected Markets"、"Hyperparameters"等工作表）；需要 Node.js（poly_merger 模块）；使用 UV 包管理器。

### 项目6：warproxxx/poly_data ⭐635（数据管道）
- **项目地址**：https://github.com/warproxxx/poly_data
- **核心功能**：Polymarket 数据检索管道，抓取、处理、结构化市场数据，包括行情（markets）、订单事件（order events）和成交记录（trades）。提供预下载数据快照（~2天初始数据可节省）。
- **与我们策略的关联**：**高价值**——可获取 Elon 推文市场历史逐笔成交数据，用于构建时间序列模型；数据格式：markets.csv（含 question/answers/volume/condition_id）、goldsky/orderFilled.csv（原始订单成交）、processed/trades.csv（结构化成交）。
- **关键代码逻辑**：`update_all.py` 依次执行：① Polymarket API 更新市场元数据 → ② Goldsky subgraph 抓取订单成交事件 → ③ 处理为结构化 trades.csv；支持断点续传。

### 项目7：Polymarket/py-clob-client ⭐926（官方 Python CLOB 客户端）
- **项目地址**：https://github.com/Polymarket/py-clob-client
- **核心功能**：Polymarket CLOB（中央限价订单簿）的官方 Python 客户端，支持市场数据查询、订单提交与取消、签名订单生成。
- **与我们策略的关联**：**必备工具**——所有自动交易的基础库，封装了订单簿 API 和签名逻辑；MIT 开源。

---

## 二、Twitter/X 高互动策略帖

> 说明：Twitter/X 对爬虫限制严格，高互动帖子（点赞/转发 ≥ 1000）的全文内容通过 EXA API 抓取，部分帖子内容可能因认证墙而截断。以下内容基于 EXA 抓取的实际内容。

### 帖子1：Polymarket 官方 @Polymarket
- **帖子内容**：Polymarket 官方账号持续发布 Elon 推文市场数据与交易量记录。2026年2月最后一周，Elon 推文期货成交量达 4620 万美元，较 2024 年 6 月启动时的 13.6 万美元增长 **342 倍**，已形成独立的"微资产类别"。
- **核心观点**：Elon 推文市场已从边缘投机演变为高流动性预测市场分支，吸引了大量专业交易者。
- **评论区关键信息**：大量交易者在评论区晒盈亏截图，讨论主要集中在不同时间粒度（每周/每日/48小时窗口）的市场选择；部分用户指出 15 分钟窗口的流动性最好。

### 帖子2：@elonXforecast（Terry Lee，Polymarket 官方合作文章）
- **帖子内容**：Polymarket 与 Terry Lee 合作发布《TWEET QUANT》深度分析，研究能否模型化 Elon 的推文行为。通过 86 周历史市场数据发现：**Elon 的推文习惯相当可预测**，识别出三个有交易价值的因子：
  1. **动量（Momentum）**：使用转移矩阵，低推文周（0-199条）有 61% 概率跟随另一个低推文周；
  2. **周内节奏（Mid-Week Pacing）**：通过监测累计推文数判断本周节奏是否偏快/偏慢；
  3. **突发新闻事件**：重大新闻会导致异常高推文量。
- **核心观点**：Elon 的推文频率不会从一周突然跳到另一周，存在动量效应；市场对尾部事件（600+推文周）定价不足（样本太小）；周初不确定性高（蓝色区域宽），周末不确定性收窄。
- **评论区关键信息**：有用户指出该分析基于历史数据，但 2025 年底 Elon 策略转向（DOGE 活动减少，重回 Tesla/xAI/SpaceX），历史模式可能失效。

### 帖子3：PolyCatalog.io @polycatalog
- **帖子内容**：《Elon Musk Tweet Market Insights》深度指南，教授如何像专业人士一样解读赔率。核心框架：
  1. **规则检查**：确认真实结算条件（哪个数据源？什么触发 YES？）  
  2. **流动性检查**：买卖价差多大？进出成本多少？  
  3. **信息质量检查**：价格变动是 Durable 更新还是注意力爆发？
- **核心观点**：赔率不是 verdict，是可交易的共识；保持"Move Log"（变动日志），区分路径改变事件和噪音；平台执行质量比表面赔率更重要。
- **评论区关键信息**：用户讨论不同平台（Polymarket vs. Kalshi）的执行质量差异；建议用"赔率变动日志"训练对市场信息的敏感度。

### 帖子4：Polymarket Signals @polymarketsignals
- **帖子内容**：《概率区间策略：如何在 Elon 推文市场赚 25%》——不是赌精确数字，而是赌区间。
  - **策略核心**：在 $0.75 总投注下，340-359 区间赚得 $0.94（25% 利润）；区间投注比精确投注胜率 60-70% vs <10%；
  - **原理**：高波动市场中，赔率在尾部聚集，区间投注覆盖中间大部分概率质量。
- **核心观点**：精确投注是赌场陷阱；区间投注利用市场对中间概率的低估；每次小额重复，复利效应显著。
- **评论区关键信息**：有用户分享了自己用区间策略在 Polymarket 上持续盈利的经验；但也有人指出在流动性差的档位区间仍然存在显著滑点。

---

## 三、Reddit 热门讨论

### 帖子1：r/PredictionsMarkets ——《4个月逆向工程 Gabagool22：我发现了什么，错了什么，以及为什么散户无法复制》👍 热门
- **链接**：https://www.reddit.com/r/PredictionsMarkets/comments/1r7oylh/4_months_reverseengineering_gabagool22_what_i/
- **帖子摘要**：一位数据分析师花费 4 个月时间，通过 Polymarket Data API 收集 Gabagool22（Polymarket 高盈利交易者）的数万条实际交易记录，每 2 秒抓取订单簿快照，并进行统计分析和样本外验证。研究发现：
  - Gabagool22 的胜率约 **79%**，在数十个窗口内得到确认；
  - 测试了 oracle 信号、订单簿模式、成交行为、动量、均值回归等十数种假设，**无一在样本外持续有效**；
  - "Twitter 上疯传的买入两边 <$1.00 套利"在真实数据中**不存在**；
  - **关键瓶颈**：资本锁定——4 小时窗口需要真金白银持续锁定；Gabagool 活跃于数十个并发市场，需要大量流动资金支撑。
- **评论区关键信息**：
  - 有用户指出 Gabagool22 可能是 Polymarket 内部人员或做市商，有信息优势；
  - 多数人认为散户无法复制，因为没有速度优势（毫秒级竞争）；
  - 有人提到"两家 bot 互刷流动性"可能制造虚假套利机会；
  - 核心教训：**散户在速度竞争中必输**。

### 帖子2：r/PillarLab ——《Polymarket AI Bot 评测：我测试了 7 个 Bot，亏了 $3840，然后试了别的赚了 $18200》👍 热门
- **链接**：https://www.reddit.com/r/PillarLab/comments/1rpul61/polymarket_ai_bot_review_2026_i_tested_7_bots.json
- **帖子摘要**：4 个月测试 7 个不同 Polymarket 交易 Bot，亏损 -$3840（42% 回撤）。关键数据：
  - **OpenClaw Bot**（6 周，$2500本金）：arb 策略，第1周赚 $180，第3周起 bot 之间速度战导致机会窗口从 8-12 秒压缩到 2-3 秒，最终亏损 -$380（-15%）；
  - **Copy Trading Bot**（8 周，$2000本金）：跟单 top trader，2 分钟延迟导致平均滑点 3.4 个点，胜率 48%；最大单笔亏损 $580；最终亏损 -$460（-23%）；
  - **Weather Trading Bot**（12 周，$1500本金）：**唯一盈利**——策略是"卖出市场高估的极端天气结局"（在 $0.93-0.99 买 NO），小额多次，复利。最终 +$64K 利润，80% 胜率。
- **评论区关键信息**：
  - Weather Bot 的高盈利贴引来大量评论指出是**骗子推广**（该帖子链接到 Telegram Bot 群）；
  - 但有用户通过第三方工具（thetradefox.com）确认该 trader 的钱包地址（0x594edb9112f526fa6a80b8f858a6379c8a2c1c11）确实存在；
  - 核心教训：** Arb 套利在几周内就被压缩殆尽**；**跟单有延迟劣势**；**气候市场因为数据客观（温度不撒谎）反而有机会**。

### 帖子3：r/PredictionsMarkets ——《我追踪了主要地缘政治预测市场赢家，发现 5 个最佳非对称机会》👍 热门
- **链接**：https://www.reddit.com/r/PredictionsMarkets/comments/1r8g2jn/i_tracked_major_geopolitical_prediction_market/
- **帖子摘要**：追踪 2026 年 1 月以来的主要地缘政治预测市场赢家，发现高盈利交易的共同模式：**市场赔率滞后于结构性变化**。具体案例：
  - "Maduro Trade"：1 月将 $32K 变成 $436K；
  - Warsh Fed Chair 市场：$3.74 亿成交量，在 announcement 前 12 小时就喊对了；
  - 伊朗打击市场：从 65% 到 8% 在 11 天内波动，双方向都有人赚钱。
- **核心结论**：高盈利交易者赚的是**叙事与结构的错位**，不是赌方向；大量流动性锚点（$10M+ 单边持仓）制造虚假信心，散户跟随流动性跑，而鲸鱼知道这点并用来反向操作。
- **评论区关键信息**：有人指出这些"结构分析"本质上和传统分析师的叙事一样，只是用概率语言包装；真正的 edge 在于信息获取速度，而非框架本身。

### 帖子4：r/Polymarket_bets ——《我们分析了 Polymarket 最赚钱的钱包并建了跟踪工具》👍 热门
- **链接**：https://www.reddit.com/r/polymarket_bets/comments/1rov0qk/we_analyzed_the_top_polymarket_traders_and.json
- **帖子摘要**：通过分析最盈利钱包的历史表现，构建实时监控工具，当这些顶级钱包建仓时推送提醒。策略逻辑：**与其猜测市场走向，不如跟随历史上持续盈利的交易者**。
- **评论区关键信息**：有人问具体用了哪些指标（胜率？盈亏比？持仓时间？）；作者透露信号"出乎意料地准确"；有用户提醒这本质上还是跟庄策略，依然有延迟和滑点问题。

---

## 四、TweetCast.xyz 竞品深度分析

- **产品地址**：https://tweetcast.xyz

### 4.1 产品功能

TweetCast 是一个专门针对 Polymarket 推文计数市场的**统计分析工具**，核心功能：

| 功能 | 免费版 | Pro 版（$19/月） |
|---|---|---|
| 实时推文计数 | ✅ | ✅ |
| 小时级热力图 | ✅ | ✅ |
| 分钟级发布规律 | ✅ | ✅ |
| 日×小时矩阵 | ✅ | ✅ |
| NegBin 模型概率 | ❌ | ✅ |
| HIGH EDGE / DIVERGED 标签 | ❌ | ✅ |
| +3h 漂移列 | ❌ | ✅ |
| 实时浏览器通知（Elon/Trump/Tate 发帖时） | ❌ | ✅ |
| 7日+日内预测 | ❌ | ✅ |

**覆盖范围**：Elon Musk（X）、Donald Trump（Truth Social）、Andrew Tate（X）的每周推文计数市场。

### 4.2 方法论

TweetCast 的核心统计模型：

```
rate = (mkt_mean − count) / hours_left     # 市场隐含速率
λ = rate × hours_remaining                  # 剩余预期推文数
R ~ NegBin(λ, r)                           # 负二项分布建模
edge = P(bracket | R) − market_prob        # 模型概率 vs 市场赔率差
```

**关键创新点**：
1. **市场隐含速率**：不从历史均值出发，而是从市场自身定价反推期望速率，自动捕捉行为制度变化；
2. **负二项分布**：不用正态分布，正确处理早期高不确定性 → 末期低不确定性的坍缩过程；
3. **+3h 漂移列**：实时显示 edge 在未来 3 小时内是扩大还是缩小；
4. **分歧标签**：HIGH EDGE（高优势）、DIVERGED（已分化）、SLIGHT（轻微）、FAIR VALUE（合理估值）。

### 4.3 已知局限

- **数据来源依赖**：使用 xtracker.polymarket.com（Polymarket 官方追踪）作为推文计数来源，非自建数据，有一定延迟（5分钟轮询）；
- **仅覆盖推文数量**：不预测内容、主题或市场影响方向；
- **模型依赖市场定价**：如果市场整体错误（系统性偏差），模型会跟着错；
- **订阅制**：完整功能需 $19/月，但免费版已提供基础热力图和规律分析；
- **无法下单**：仅提供分析信号，不执行交易。

### 4.4 我们的差异化机会

TweetCast 已解决"推文计数市场统计"问题，但以下方向仍存在空白：

1. **内容情绪叠加**：不只计数，推文情绪/主题（政策？DOGE？Tesla？）与市场定价的相关性——TweetCast 未覆盖；
2. **多市场联动**：Elon 一条重磅推文可能同时影响多个相关市场（BTC、 DOGE、具体股票），目前没有工具做联动分析；
3. **历史数据分析**：TweetCast 专注实时，缺乏历史回测框架；
4. **主动建仓信号**：TweetCast 给出概率差异，但不会告诉用户"现在应该买哪个档位、买多少"；
5. **跨人物对比**：Trump vs Elon vs Tate 的对比分析（哪个更可预测？哪个市场效率更低？）；

---

## 五、综合结论

### 5.1 别人已经做了什么（避免重复造轮子）

| 方向 | 已有的最强方案 | 链接 |
|---|---|---|
| Polymarket Python 交易 API | py-clob-client（官方） | https://github.com/Polymarket/py-clob-client |
| 历史数据分析 | prediction-market-analysis（36GiB 数据） | https://github.com/Jon-Becker/prediction-market-analysis |
| 统一多平台 API | pmxt（CCXT for PM） | https://github.com/pmxt-dev/pmxt |
| 推文市场统计分析 | TweetCast（NegBin 模型） | https://tweetcast.xyz |
| 仓位复制跟单 | PolyCop/PolyGun 类工具 | Reddit 热帖（失效问题严重） |
| AI Agent 交易框架 | Polymarket/agents（官方） | https://github.com/Polymarket/agents |
| 竞品情报研究 | last30days-skill（多平台聚合） | https://github.com/mvanhorn/last30days-skill |

### 5.2 市场空白（我们的差异化机会）

1. **Elon 推文内容→市场联动分析**：现有工具只做计数，没有情绪/主题分析；一条"核按钮"推文 vs 一条"Doge 表情包"推文对市场的影响天壤之别，但市场目前只按数量定价；
2. **概率区间 + 档位优化**：TweetCast 给出概率差异，但最佳建仓档位和仓位配比需要手动计算；可以构建一个"概率差 × 赔率 × 流动性"三维优化器；
3. **动量 + 节奏双因子模型**：Terry Lee 的论文验证了动量因子的存在（低推文周跟随低推文周概率 61%），但这只是一个粗糙的 tier 转移矩阵；可以构建更精细的 Poisson / Negative Binomial 混合模型，加入周内节奏修正；
4. **非 Elon 推文市场的扩展**：TweetCast 只覆盖 3 个账号，但 Polymarket 上有大量其他"可量化人物"的推文市场（政客、运动员等），目前缺乏专门的统计分析工具；
5. **建仓时点 + 退出时机优化**：当前研究大多聚焦"哪个档位被低估"，但"什么时候进、什么时候平仓"同样重要——TweetCast 没有持仓管理模块。

### 5.3 可直接复用的资源（代码/数据/方法）

| 资源 | 说明 | 获取方式 |
|---|---|---|
| `polymarket/py-clob-client` | Python 交易 API，必须用 | `pip install py-clob-client` |
| `Jon-Becker/prediction-market-analysis` 历史数据 | 36GiB Polymarket+Kalshi 成交数据 | `make setup`（下载压缩包） |
| `warproxxx/poly_data` 数据管道 | 增量抓取实时成交数据 | `uv run python update_all.py` |
| TweetCast NegBin 模型公式 | `rate = (mkt_mean − count) / hours_left` | 直接复用数学框架 |
| `last30days-skill` 多平台聚合 | 监控社交媒体热度变化 | `/last30days [topic]` |
| Terry Lee 三因子模型 | 动量 + 周内节奏 + 突发新闻 | 参考论文框架，自建模型 |

### 5.4 风险警示（从别人的失败经验中学习）

1. **速度战是死路**：Reddit 高赞帖子（Bot 测试 4 个月亏损 -$3840）明确证明——Arb 套利机会在数周内被压缩殆尽（窗口从 8-12 秒压缩到 2-3 秒），没有微秒级基础设施就不要碰高频策略；
2. **跟单有结构性延迟劣势**：即使跟顶级交易者，2 分钟延迟导致胜率从 62% 降到 33%；想要跟单必须解决实时信号问题，否则 slippage 吃掉全部利润；
3. **历史数据的 regime 变化**：Elon 的推文行为在 2024 年选举期、DOGE 期、2025 年回归 Tesla 期存在显著结构性变化，用 2024 年数据训练的模型在 2026 年可能失效；
4. **做市需要大量资本**：poly-maker 的开发者自己说"当前市场不盈利"，做市商之间的竞争已经让边际利润归零；
5. **Telegram/Promoted 类"暴富故事"是骗子温床**：那个"$799→$64K"的帖子被 Reddit 社区普遍质疑是推广贴，链接指向 Telegram Bot 群——**不要相信任何主动推送的高盈利率策略**；
6. **散户难以复制顶级交易者**：Gabagool22 案例研究（4 个月追踪，79% 胜率但无法找到信号来源）表明顶级 PM 交易者可能存在信息不对称或技术优势，散户从外部观察永远找不到可持续 edge。

---

*报告生成时间：2026-03-20 | 数据新鲜度：GitHub（实时）、Polymarket（实时）、Reddit（过去30天内热门）、TweetCast（实时）*
