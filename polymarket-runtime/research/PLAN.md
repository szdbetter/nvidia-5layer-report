# Polymarket 全量盘口扫描 + 赛道筛选调研规划

> 生成时间: 2026-03-20 UTC | 状态: 待执行

---

## 1. 全量活跃盘口拉取脚本框架

```python
"""
polymarket_scanner.py — 全量盘口扫描器
输出: data/events_all.json, data/markets_all.json, data/clob_all.json
"""
import requests, json, time

GAMMA_EVENTS = "https://gamma-api.polymarket.com/events"
GAMMA_MARKETS = "https://gamma-api.polymarket.com/markets"
CLOB_MARKETS = "https://clob.polymarket.com/markets"

def fetch_all_events():
    """拉取全量活跃事件（按流动性降序）"""
    all_events = []
    offset = 0
    while True:
        r = requests.get(GAMMA_EVENTS, params={
            "active": "true", "limit": 100,
            "order": "liquidity", "ascending": "false",
            "offset": offset
        })
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_events.extend(batch)
        offset += 100
        time.sleep(0.3)  # 防限流
    return all_events

def fetch_all_markets():
    """拉取全量活跃盘口（Gamma API，含 volume/spread）"""
    all_markets = []
    offset = 0
    while True:
        r = requests.get(GAMMA_MARKETS, params={
            "active": "true", "limit": 100, "offset": offset
        })
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        all_markets.extend(batch)
        offset += 100
        time.sleep(0.3)
    return all_markets

def fetch_all_clob():
    """拉取全量 CLOB 盘口（含 tags/fee 结构）"""
    all_clob = []
    cursor = "MA=="
    while cursor:
        r = requests.get(CLOB_MARKETS, params={"next_cursor": cursor})
        r.raise_for_status()
        data = r.json()
        all_clob.extend(data.get("data", []))
        cursor = data.get("next_cursor")
        if cursor == "LTE=":  # 终止标记
            break
        time.sleep(0.3)
    return all_clob

def merge_and_classify(events, markets, clob):
    """
    合并三个数据源，按 tag/关键词 分类到赛道
    输出: { track_name: [market_list] }
    """
    # 用 CLOB tags 做主分类
    tag_map = {}
    for m in clob:
        for tag in (m.get("tags") or []):
            tag_map.setdefault(tag, []).append(m)

    # 关键词二次分类（覆盖无 tag 的盘口）
    KEYWORD_TRACKS = {
        "经济数据": ["CPI", "NFP", "nonfarm", "unemployment", "fed", "FOMC", "interest rate", "GDP", "PCE", "PPI"],
        "原油/能源": ["EIA", "crude", "oil", "inventory", "gasoline", "petroleum", "OPEC"],
        "气候/温度": ["temperature", "GISTEMP", "climate", "hottest", "warmest", "ERA5"],
        "体育": ["NBA", "NFL", "MLB", "UEFA", "FIFA", "Premier League", "champion", "winner", "playoff"],
        "社交行为": ["tweet", "post", "Elon", "X post", "follower", "Truth Social"],
        "加密货币": ["Bitcoin", "BTC", "ETH", "crypto", "Ethereum", "Solana"],
        "地缘政治": ["war", "ceasefire", "invasion", "sanction", "NATO", "Iran", "Russia", "Ukraine", "Taiwan"],
        "选举/政治": ["election", "president", "governor", "senate", "poll", "approval rating"],
        "AI/科技": ["AI", "GPT", "OpenAI", "Google", "Apple", "launch", "release"],
    }

    # 为每个 market 匹配赛道
    track_results = {k: [] for k in KEYWORD_TRACKS}
    track_results["其他"] = []

    gamma_map = {m.get("conditionId") or m.get("id"): m for m in markets}

    for m in markets:
        question = (m.get("question") or "").lower() + " " + (m.get("description") or "").lower()
        matched = False
        for track, keywords in KEYWORD_TRACKS.items():
            if any(kw.lower() in question for kw in keywords):
                track_results[track].append(m)
                matched = True
                break
        if not matched:
            track_results["其他"].append(m)

    return track_results

def compute_track_stats(track_results):
    """每个赛道的汇总统计"""
    stats = {}
    for track, markets in track_results.items():
        volumes_24h = [float(m.get("volume24hr") or 0) for m in markets]
        spreads = [float(m.get("spread") or 0) for m in markets if m.get("spread")]
        stats[track] = {
            "count": len(markets),
            "total_volume_24h": sum(volumes_24h),
            "avg_volume_24h": sum(volumes_24h) / max(len(volumes_24h), 1),
            "avg_spread": sum(spreads) / max(len(spreads), 1),
            "top3_by_volume": sorted(markets, key=lambda x: float(x.get("volume24hr") or 0), reverse=True)[:3],
        }
    return stats

if __name__ == "__main__":
    print("=== Phase 1: 拉取全量数据 ===")
    events = fetch_all_events()
    markets = fetch_all_markets()
    clob = fetch_all_clob()
    print(f"Events: {len(events)}, Markets: {len(markets)}, CLOB: {len(clob)}")

    # 持久化原始数据
    for name, data in [("events", events), ("markets", markets), ("clob", clob)]:
        with open(f"data/{name}_all.json", "w") as f:
            json.dump(data, f, indent=2)

    print("=== Phase 2: 分类 ===")
    track_results = merge_and_classify(events, markets, clob)
    stats = compute_track_stats(track_results)

    for track, s in sorted(stats.items(), key=lambda x: -x[1]["total_volume_24h"]):
        print(f"  {track}: {s['count']}个盘口 | 24h总量=${s['total_volume_24h']:,.0f} | 平均spread={s['avg_spread']:.4f}")

    with open("data/track_stats.json", "w") as f:
        json.dump(stats, f, indent=2, default=str)
```

---

## 2. 赛道筛选维度

### 评分标准（每项 1-5 分）

| 维度 | 定义 |
|------|------|
| **数据可获取性** | 数据源是否免费、API是否稳定、延迟多少 |
| **时效性优势** | 我们能比市场早多少获取/处理信息 |
| **盘口流动性** | 能否以合理 spread 进出 $500+ 仓位 |
| **竞争密度** | Bot/做市商饱和程度 |
| **可自动化程度** | 能否全自动决策+下单，无需人工判断 |
| **Fee 友好度** | Maker/Taker 费率是否允许薄利策略 |

### 各赛道评估

#### 2.1 经济数据盘口（CPI / NFP / Fed 决议）
| 维度 | 评分 | 说明 |
|------|------|------|
| 数据可获取性 | ⭐5 | BLS/Fed 官网免费，发布时间精确到分钟 |
| 时效性优势 | ⭐4 | Cleveland Fed Nowcast CPI 提前2周可预测，精度±0.1%；CME FedWatch 可实时抓取 |
| 盘口流动性 | ⭐4 | CPI/Fed 类盘口通常 $50K-$500K 流动性 |
| 竞争密度 | ⭐3 | 有量化玩家但不如天气市场泛滥，门槛较高 |
| 可自动化程度 | ⭐5 | 数据发布时间固定，可全自动预测+下单 |
| Fee 友好度 | ⭐4 | 月度/季度盘口通常 maker 0%, taker 1-2% |
| **总分** | **25/30** | |

**数据源清单**：
- Cleveland Fed Inflation Nowcast: `https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting`
- BLS CPI Release: `https://www.bls.gov/schedule/news_release/cpi.htm`
- CME FedWatch: `https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html`
- Atlanta Fed GDPNow: `https://www.atlantafed.org/cqer/research/gdpnow`
- ADP Employment (NFP 前瞻): 每月 NFP 前2天发布

**信息优势来源**：组合多个 Nowcast 模型的预测 → 加权集成 → 比单一盘口定价更精准

#### 2.2 EIA 原油/能源库存周报
| 维度 | 评分 | 说明 |
|------|------|------|
| 数据可获取性 | ⭐5 | EIA 官网免费 API，每周三 10:30 ET 固定发布 |
| 时效性优势 | ⭐5 | API Inventory Report 每周二晚发布（比 EIA 早1天），可提前定位 |
| 盘口流动性 | ⭐3 | 需验证—能源类盘口可能偏小 |
| 竞争密度 | ⭐4 | Polymarket 能源盘口较冷门，Bot 少 |
| 可自动化程度 | ⭐5 | 纯数值比较，全自动 |
| Fee 友好度 | ⭐4 | 周度盘口，费率通常合理 |
| **总分** | **26/30** | |

**数据源清单**：
- EIA Weekly Petroleum Status: `https://www.eia.gov/petroleum/supply/weekly/`
- API (American Petroleum Institute) 周报: 每周二 16:30 ET（比 EIA 早1天）
- Bloomberg/Reuters 市场预期调查值

**信息优势来源**：API 报告 → 预测 EIA 偏差方向 → 在 EIA 发布前 Polymarket 盘口未充分反映

#### 2.3 全球温度异常月度盘口
| 维度 | 评分 | 说明 |
|------|------|------|
| 数据可获取性 | ⭐5 | ERA5 near-realtime（延迟5天）、NCEP GFS 预报免费 |
| 时效性优势 | ⭐5 | ERA5 数据可在 NASA GISTEMP 发布前2-3周预测月均温度异常 |
| 盘口流动性 | ⭐2 | 需验证—月度温度盘口可能流动性不足 |
| 竞争密度 | ⭐3 | 普通天气 Bot 泛滥，但全球月度异常需专业气候建模，门槛高 |
| 可自动化程度 | ⭐4 | ERA5 下载+计算可自动化，但数据处理链较长 |
| Fee 友好度 | ⭐4 | 月度盘口费率通常低 |
| **总分** | **23/30** | |

**数据源清单**：
- Copernicus ERA5: `https://cds.climate.copernicus.eu/`（Near-realtime, 延迟5天）
- NASA GISTEMP: `https://data.giss.nasa.gov/gistemp/`
- NOAA NCEP GFS: 全球预报，6小时更新

**信息优势来源**：ERA5 月内累计数据 → 线性外推月度异常值 → 在 GISTEMP 发布前2周建仓

#### 2.4 体育赛事
| 维度 | 评分 | 说明 |
|------|------|------|
| 数据可获取性 | ⭐4 | ESPN/Sportradar API 可获取伤病、阵容、实时比分 |
| 时效性优势 | ⭐3 | 伤病消息通常 Twitter 先出，但抓取速度竞争激烈 |
| 盘口流动性 | ⭐5 | 体育是 Polymarket 最大赛道之一 |
| 竞争密度 | ⭐1 | 极度红海—专业体育量化团队+做市商密集 |
| 可自动化程度 | ⭐3 | 需要复杂赛事模型，维护成本高 |
| Fee 友好度 | ⭐3 | 高流动性盘口 fee 尚可，但 spread 被做市商压缩 |
| **总分** | **19/30** | |

**结论**：除非有独特数据优势（如低级别联赛），否则不建议作为首选。

#### 2.5 社交行为盘口（Tweet 数量等）
| 维度 | 评分 | 说明 |
|------|------|------|
| 数据可获取性 | ⭐3 | X API 付费（$100/月 Basic），爬虫不稳定 |
| 时效性优势 | ⭐4 | 实时计数 vs 盘口更新延迟，有窗口 |
| 盘口流动性 | ⭐2 | 社交行为盘口通常流动性低 |
| 竞争密度 | ⭐3 | 中等—有人做但不算饱和 |
| 可自动化程度 | ⭐5 | 纯计数逻辑，全自动 |
| Fee 友好度 | ⭐3 | 需验证 |
| **总分** | **20/30** | |

#### 2.6 加密货币（非快市）
| 维度 | 评分 | 说明 |
|------|------|------|
| 数据可获取性 | ⭐5 | CEX API 免费实时 |
| 时效性优势 | ⭐2 | 价格信息几乎零延迟，无信息差 |
| 盘口流动性 | ⭐5 | BTC 类盘口流动性最高 |
| 竞争密度 | ⭐1 | 极度饱和 |
| 可自动化程度 | ⭐5 | 全自动 |
| Fee 友好度 | ⭐2 | 快市 taker 10%，非快市需验证 |
| **总分** | **20/30** | |

---

## 3. 优先级排序

| 优先级 | 赛道 | 总分 | 理由 |
|--------|------|------|------|
| **P0** | EIA 原油库存周报 | 26 | API报告提前1天、发布时间固定、盘口冷门Bot少、全自动化、每周稳定出手机会 |
| **P1** | 经济数据 (CPI/NFP/Fed) | 25 | Nowcast模型成熟可用、盘口流动性好、时间确定性极强、组合多源预测有优势 |
| **P2** | 全球温度异常月度 | 23 | ERA5信息差大（2-3周）、但需验证盘口是否存在且流动性是否够 |
| **P3** | 社交行为盘口 | 20 | 逻辑简单但流动性存疑 |
| **P4** | 体育 / 加密非快市 | 19-20 | 红海，暂不投入 |

**核心逻辑**：P0 和 P1 共享一个模式——**政府/机构定时发布硬数据，发布前存在可量化的预测窗口**。这是我们的最佳甜蜜点。

---

## 4. 下一步执行任务清单

### Task 1: 全量扫描（立即执行）
- [ ] 运行 `polymarket_scanner.py`，拉取全量活跃盘口
- [ ] 输出 `data/track_stats.json`，确认各赛道的实际盘口数量和流动性
- [ ] 重点标记含以下关键词的盘口：`EIA`, `crude`, `oil`, `inventory`, `CPI`, `inflation`, `NFP`, `jobs`, `Fed`, `FOMC`, `temperature`, `warmest`, `hottest`
- [ ] 输出 `data/target_markets.json`，列出所有目标盘口的 conditionId / question / volume / spread / fee

### Task 2: EIA 原油库存深度验证（P0，Task 1 完成后）
- [ ] 确认 Polymarket 上是否存在 EIA 周报相关盘口（搜索 "EIA", "crude inventory", "oil"）
- [ ] 如存在：记录盘口结构（阈值设定、到期时间、流动性、fee）
- [ ] 抓取最近 4 周 API 周报 vs EIA 实际值，计算偏差分布
- [ ] 评估：API 发布后 → Polymarket 盘口价格是否滞后？滞后多久？
- [ ] 输出 `research/EIA_DEEP_DIVE.md`

### Task 3: 经济数据盘口深度验证（P1，可与 Task 2 并行）
- [ ] 搜索 Polymarket 上所有 CPI/NFP/Fed 相关活跃盘口
- [ ] 抓取 Cleveland Fed Nowcast 最近 6 个月历史预测 vs 实际 CPI，计算预测精度
- [ ] 对比 Nowcast 预测值 vs Polymarket 盘口隐含概率，寻找系统性偏差
- [ ] 评估下一个 CPI 发布日（查 BLS 日历）的盘口机会
- [ ] 输出 `research/ECON_DATA_DEEP_DIVE.md`

### Task 4: 温度异常盘口存在性验证（P2）
- [ ] 搜索 Polymarket 上所有温度/气候相关盘口
- [ ] 如存在：评估 ERA5 预测窗口是否足够（≥1周）
- [ ] 如不存在：标记为"暂无盘口"，归档

### Task 5: Fee 结构全景（贯穿所有任务）
- [ ] 从 CLOB 数据中提取所有目标盘口的 maker_base_fee / taker_base_fee
- [ ] 计算各赛道的平均 fee，评估薄利策略可行性
- [ ] 输出 `research/FEE_ANALYSIS.md`

---

## 附录：目录结构

```
polymarket-runtime/
├── research/
│   ├── PLAN.md                  ← 本文件
│   ├── EIA_DEEP_DIVE.md         ← Task 2 产出
│   ├── ECON_DATA_DEEP_DIVE.md   ← Task 3 产出
│   └── FEE_ANALYSIS.md          ← Task 5 产出
├── data/
│   ├── events_all.json          ← 全量事件原始数据
│   ├── markets_all.json         ← 全量盘口原始数据
│   ├── clob_all.json            ← 全量 CLOB 数据
│   ├── track_stats.json         ← 赛道统计
│   └── target_markets.json      ← 目标盘口清单
└── scripts/
    └── polymarket_scanner.py    ← 扫描脚本
```
