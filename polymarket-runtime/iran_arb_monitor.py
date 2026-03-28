#!/usr/bin/env python3
"""
美伊战争盘口套利监控 v1.0
- 每15分钟轮询 Polymarket Gamma API
- 检测：单调性违反、逻辑约束、价格异动
- 触发条件时 Discord 告警（附套利逻辑说明）
- 静默OK原则：无异动不发消息
"""
import json, urllib.request, os, time, logging, sys
from datetime import datetime, timezone
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────────────────
DISCORD_CHANNEL = "1480446033531240469"
CHECK_INTERVAL_SEC = 900  # 15分钟
CACHE_FILE = "/tmp/iran_arb_cache.json"
LOG_FILE   = "/tmp/iran_arb_monitor.log"

# 关键盘口监控列表（截止日期升序组）
MONITOR_SERIES = {
    "ceasefire": [
        {"slug": "us-x-iran-ceasefire-by-march-31",   "label": "停战3月31", "deadline": "2026-03-31"},
        {"slug": "us-x-iran-ceasefire-by-april-15-182", "label": "停战4月15", "deadline": "2026-04-15"},
        {"slug": "us-x-iran-ceasefire-by-april-30-194", "label": "停战4月30", "deadline": "2026-04-30"},
        {"slug": "us-x-iran-ceasefire-by-may-31-313",  "label": "停战5月31",  "deadline": "2026-05-31"},
        {"slug": "us-x-iran-ceasefire-by-june-30-752", "label": "停战6月30",  "deadline": "2026-06-30"},
        {"slug": "us-x-iran-ceasefire-by-december-31", "label": "停战12月31", "deadline": "2026-12-31"},
    ],
    "conflict_ends": [
        {"slug": "iran-x-israelus-conflict-ends-by-march-31",    "label": "冲突结束3月", "deadline": "2026-03-31"},
        {"slug": "iran-x-israelus-conflict-ends-by-april-15-618","label": "冲突结束4月15","deadline": "2026-04-15"},
        {"slug": "iran-x-israelus-conflict-ends-by-april-30-766-662","label": "冲突结束4月30","deadline": "2026-04-30"},
        {"slug": "iran-x-israelus-conflict-ends-by-june-30-813-454","label": "冲突结束6月","deadline": "2026-06-30"},
    ],
    "leadership_change": [
        {"slug": "iran-leadership-change-by-march-31", "label": "领导层更迭3月", "deadline": "2026-03-31"},
        {"slug": "iran-leadership-change-by-april-30", "label": "领导层更迭4月", "deadline": "2026-04-30"},
        {"slug": "iran-leadership-change-by-december-31","label": "领导层更迭12月","deadline": "2026-12-31"},
    ],
    "regime_fall": [
        {"slug": "will-the-iranian-regime-fall-by-march-31", "label": "政权倒台3月", "deadline": "2026-03-31"},
        {"slug": "will-the-iranian-regime-fall-by-april-30", "label": "政权倒台4月", "deadline": "2026-04-30"},
        {"slug": "will-the-iranian-regime-fall-by-june-30",  "label": "政权倒台6月",  "deadline": "2026-06-30"},
    ],
    "end_ops_trump": [
        {"slug": "trump-announces-end-of-military-operations-against-iran-by-march-31st","label": "结束军事行动3月","deadline":"2026-03-31"},
        {"slug": "trump-announces-end-of-military-operations-against-iran-by-april-30th","label": "结束军事行动4月","deadline":"2026-04-30"},
        {"slug": "trump-announces-end-of-military-operations-against-iran-by-june-30th", "label": "结束军事行动6月","deadline":"2026-06-30"},
    ],
}

# 逻辑约束（应满足 A.yes <= B.yes）
LOGIC_CONSTRAINTS = [
    {
        "id": "ceasefire_vs_conflict",
        "a": "us-x-iran-ceasefire-by-april-30-194",
        "b": "iran-x-israelus-conflict-ends-by-april-30-766-662",
        "desc": "停战4月(A) 应 ≤ 冲突结束4月(B)，停战需双方宣布，门槛更高",
        "relation": "A<=B",
    },
    {
        "id": "end_ops_vs_ceasefire",
        "a": "trump-announces-end-of-military-operations-against-iran-by-march-31st",
        "b": "us-x-iran-ceasefire-by-march-31",
        "desc": "结束行动3月(A) 应 ≥ 停战3月(B)，结束行动只需Trump单方面宣布",
        "relation": "A>=B",
    },
    {
        "id": "regime_fall_vs_leadership",
        "a": "will-the-iranian-regime-fall-by-april-30",
        "b": "iran-leadership-change-by-april-30",
        "desc": "政权倒台4月(A) 应 ≤ 领导层更迭4月(B)，倒台是更迭子集",
        "relation": "A<=B",
    },
]

# 价格异动阈值（与上次相比变化超过此值触发告警）
PRICE_MOVE_THRESHOLD = 0.05  # 5%

# ── 日志 ──────────────────────────────────────────────────────────────────────
def setup_logging():
    lg = logging.getLogger("iran_arb")
    lg.setLevel(logging.INFO)
    lg.propagate = False
    if not lg.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        for h in [logging.StreamHandler(), logging.FileHandler(LOG_FILE)]:
            h.setFormatter(fmt)
            lg.addHandler(h)
    return lg

# ── Discord 告警 ──────────────────────────────────────────────────────────────
def load_env_var(key):
    for envfile in ["/root/.openclaw/.env", "/Users/ai/.openclaw/.env"]:
        try:
            for line in Path(envfile).read_text().splitlines():
                if line.strip().startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return os.environ.get(key)

def send_discord(msg, lg):
    import subprocess, os as _os
    # 1. Webhook
    wh = load_env_var("POLY_DISCORD_WEBHOOK_URL") or load_env_var("DISCORD_WEBHOOK_URL")
    if wh:
        try:
            payload = json.dumps({"content": msg[:1990]}).encode()
            req = urllib.request.Request(wh, data=payload,
                  headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
            lg.info("Discord webhook 发送成功")
            return True
        except Exception as e:
            lg.warning(f"Webhook 失败: {e}")
    # 2. Bot Token 直接调用 Discord API
    bot_token = load_env_var("DISCORD_BOT_TOKEN")
    if bot_token:
        try:
            payload = json.dumps({"content": msg[:1990]}).encode()
            url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL}/messages"
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bot {bot_token}"
            })
            urllib.request.urlopen(req, timeout=10)
            lg.info("Discord Bot Token 发送成功")
            return True
        except Exception as e:
            lg.warning(f"Bot Token 失败: {e}")
    # 3. openclaw CLI fallback
    for cli in ["/usr/local/bin/openclaw",
                "/Users/ai/.nvm/versions/node/v22.22.0/bin/openclaw",
                "/Users/ai/.local/bin/openclaw"]:
        if not _os.path.exists(cli):
            continue
        try:
            r = subprocess.run(
                [cli, "message", "send", "--channel", "discord",
                 "--target", DISCORD_CHANNEL, "-m", msg[:1990]],
                capture_output=True, text=True, timeout=15,
                env={**_os.environ, "PATH": "/usr/local/bin:/usr/bin:/bin"})
            if r.returncode == 0:
                lg.info(f"openclaw CLI ({cli}) 发送成功")
                return True
            lg.error(f"CLI 失败: {r.stderr[:200]}")
        except Exception as e:
            lg.error(f"CLI 异常: {e}")
    return False

# ── Polymarket 数据拉取 ───────────────────────────────────────────────────────
def fetch_market(slug, lg):
    url = f"https://gamma-api.polymarket.com/markets?slug={slug}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if data:
            m = data[0]
            prices = json.loads(m.get("outcomePrices", "[]"))
            yes = round(float(prices[0]), 4) if prices else None
            return {
                "yes": yes,
                "volume": float(m.get("volume", 0)),
                "liquidity": float(m.get("liquidity", 0)),
                "active": m.get("active", True),
                "closed": m.get("closed", False),
            }
    except Exception as e:
        lg.debug(f"fetch {slug}: {e}")
    return None

def fetch_all_prices(lg):
    prices = {}
    all_slugs = set()
    for series in MONITOR_SERIES.values():
        for m in series:
            all_slugs.add(m["slug"])
    for c in LOGIC_CONSTRAINTS:
        all_slugs.add(c["a"])
        all_slugs.add(c["b"])

    for slug in all_slugs:
        d = fetch_market(slug, lg)
        if d and not d["closed"] and d["yes"] is not None and d["yes"] < 0.99:
            prices[slug] = d
        time.sleep(0.2)  # rate limit friendly
    return prices

# ── 套利检测 ──────────────────────────────────────────────────────────────────
def check_monotonicity(prices, lg):
    alerts = []
    for name, series in MONITOR_SERIES.items():
        priced = [(m, prices[m["slug"]]) for m in series if m["slug"] in prices]
        for i in range(len(priced) - 1):
            m1, d1 = priced[i]
            m2, d2 = priced[i+1]
            gap = d2["yes"] - d1["yes"]
            if gap < -0.04:  # 后期日期概率 < 前期 超过4%
                alerts.append({
                    "type": "monotonicity",
                    "series": name,
                    "a_label": m1["label"], "a_yes": d1["yes"], "a_slug": m1["slug"],
                    "b_label": m2["label"], "b_yes": d2["yes"], "b_slug": m2["slug"],
                    "edge": abs(gap),
                    "msg": f"单调性违反: {m1['label']}({d1['yes']*100:.1f}%) > {m2['label']}({d2['yes']*100:.1f}%) 价差{abs(gap)*100:.1f}%"
                })
    return alerts

def check_logic_constraints(prices, lg):
    alerts = []
    for c in LOGIC_CONSTRAINTS:
        da = prices.get(c["a"])
        db = prices.get(c["b"])
        if not da or not db:
            continue
        pa, pb = da["yes"], db["yes"]
        violated = False
        gap = 0
        if c["relation"] == "A<=B" and pa - pb > 0.03:
            violated = True; gap = pa - pb
        elif c["relation"] == "A>=B" and pb - pa > 0.03:
            violated = True; gap = pb - pa
        if violated:
            alerts.append({
                "type": "logic_constraint",
                "id": c["id"],
                "edge": gap,
                "msg": f"逻辑约束违反: {c['desc']} | A={pa*100:.1f}% B={pb*100:.1f}% 价差{gap*100:.1f}%"
            })
    return alerts

def check_price_moves(prices, prev_prices, lg):
    alerts = []
    for slug, d in prices.items():
        prev = prev_prices.get(slug)
        if not prev or prev.get("yes") is None:
            continue
        move = d["yes"] - prev["yes"]
        if abs(move) >= PRICE_MOVE_THRESHOLD:
            # 找label
            label = slug
            for series in MONITOR_SERIES.values():
                for m in series:
                    if m["slug"] == slug:
                        label = m["label"]
            alerts.append({
                "type": "price_move",
                "slug": slug,
                "label": label,
                "prev": prev["yes"],
                "curr": d["yes"],
                "move": move,
                "msg": f"价格异动: {label} {prev['yes']*100:.1f}%→{d['yes']*100:.1f}% ({'+' if move>0 else ''}{move*100:.1f}%)"
            })
    return alerts

# ── 格式化告警消息 ─────────────────────────────────────────────────────────────
def format_alert_message(alerts, prices):
    now = datetime.now(timezone.utc).strftime("%m-%d %H:%M UTC")
    lines = [f"🚨 **[美伊套利告警]** {now}\n"]

    price_moves = [a for a in alerts if a["type"] == "price_move"]
    mono_alerts = [a for a in alerts if a["type"] == "monotonicity"]
    logic_alerts = [a for a in alerts if a["type"] == "logic_constraint"]

    if price_moves:
        lines.append("**📈 价格异动**")
        for a in price_moves[:5]:
            arrow = "📈" if a["move"] > 0 else "📉"
            lines.append(f"{arrow} {a['label']}: {a['prev']*100:.1f}% → **{a['curr']*100:.1f}%** ({'+' if a['move']>0 else ''}{a['move']*100:.1f}%)")
            lines.append(f"   [Polymarket](https://polymarket.com/event/{a['slug']})")

    if mono_alerts:
        lines.append("\n**⚠️ 单调性套利**")
        for a in sorted(mono_alerts, key=lambda x: -x["edge"])[:3]:
            lines.append(f"• {a['a_label']}({a['a_yes']*100:.1f}%) > {a['b_label']}({a['b_yes']*100:.1f}%) | 价差**{a['edge']*100:.1f}%**")
            lines.append(f"  → 买入 {a['b_label']} YES @ {a['b_yes']*100:.1f}¢")

    if logic_alerts:
        lines.append("\n**🔴 逻辑约束违反**")
        for a in logic_alerts:
            lines.append(f"• {a['msg']}")

    # 当前关键价格快照
    key_slugs = [
        ("us-x-iran-ceasefire-by-march-31", "停战3月"),
        ("us-x-iran-ceasefire-by-april-30-194", "停战4月"),
        ("will-the-iranian-regime-fall-by-april-30", "政权倒台4月"),
        ("iran-leadership-change-by-april-30", "领导层更迭4月"),
    ]
    lines.append("\n**📊 关键盘口快照**")
    for slug, label in key_slugs:
        d = prices.get(slug)
        if d:
            lines.append(f"• {label}: **{d['yes']*100:.1f}%** Liq${d['liquidity']/1000:.0f}K")

    return "\n".join(lines)

# ── 主循环 ────────────────────────────────────────────────────────────────────
def main():
    lg = setup_logging()
    lg.info("🚀 美伊套利监控启动")
    send_discord("✅ **[美伊套利监控]** 守护进程已启动，每15分钟检查一次，有异动告警", lg)

    prev_prices = {}
    # 加载缓存
    if Path(CACHE_FILE).exists():
        try:
            prev_prices = json.loads(Path(CACHE_FILE).read_text())
            lg.info(f"加载缓存 {len(prev_prices)} 个盘口")
        except Exception:
            pass

    while True:
        try:
            lg.info("开始轮询...")
            prices = fetch_all_prices(lg)
            lg.info(f"获取到 {len(prices)} 个活跃盘口")

            alerts = []
            alerts += check_monotonicity(prices, lg)
            alerts += check_logic_constraints(prices, lg)
            alerts += check_price_moves(prices, prev_prices, lg)

            if alerts:
                msg = format_alert_message(alerts, prices)
                lg.info(f"触发 {len(alerts)} 个告警，发送Discord")
                send_discord(msg, lg)
            else:
                lg.info("无异动，静默")

            # 保存缓存
            Path(CACHE_FILE).write_text(json.dumps(prices))
            prev_prices = prices

        except KeyboardInterrupt:
            lg.info("手动停止")
            break
        except Exception as e:
            lg.error(f"轮询异常: {e}", exc_info=True)

        lg.info(f"等待 {CHECK_INTERVAL_SEC//60} 分钟...")
        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
