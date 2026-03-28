#!/usr/bin/env python3
# Hormuz Macro Engine v3 - 真实数据模式
# 数据源：hormuzstraitmonitor.com（爬虫）+ Polymarket Gamma API
# 无任何 Mock/随机数代码
import os, sys, json, re, subprocess, logging
from datetime import datetime, timezone

RESULT_FILE     = "/tmp/poly_macro_result.json"
LOG_FILE        = "/tmp/poly_macro_engine.log"
DISCORD_CHANNEL = "1480446033531240469"

# Polymarket 市场 slug
SLUG_MARCH31 = "us-x-iran-ceasefire-by-march-31"
SLUG_APRIL30 = "us-x-iran-ceasefire-by-april-30-194"

def setup_logging():
    lg = logging.getLogger("poly_macro")
    lg.setLevel(logging.INFO)
    lg.propagate = False
    if not lg.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        for h in [logging.StreamHandler(), logging.FileHandler(LOG_FILE)]:
            h.setFormatter(fmt)
            lg.addHandler(h)
    return lg


def send_alert(msg, lg):
    """发送 Discord 告警，优先 Webhook，降级 openclaw CLI"""
    wh = os.environ.get("POLY_DISCORD_WEBHOOK_URL") or os.environ.get("DISCORD_WEBHOOK_URL")
    if wh:
        try:
            import urllib.request
            payload = json.dumps({"content": msg}).encode()
            req = urllib.request.Request(wh, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
            lg.info("discord webhook 发送成功")
            return True
        except Exception as e:
            lg.warning(f"webhook 失败: {e}")
    try:
        r = subprocess.run(
            ["/usr/local/bin/openclaw", "message", "send",
             "--channel", "discord", "--target", DISCORD_CHANNEL, "-m", msg],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            lg.info("openclaw CLI 发送成功")
            return True
        lg.error(f"CLI 失败: {r.stderr}")
    except Exception as e:
        lg.error(f"CLI 异常: {e}")
    return False


def fetch_strait_data(lg):
    """
    通过 scrapling 爬取 hormuzstraitmonitor.com，解析通行量数据。
    失败时返回 fallback 默认值并标记 data_source = "fallback"
    """
    lg.info("正在爬取 hormuzstraitmonitor.com ...")
    try:
        result = subprocess.run(
            ['python3', '/root/.openclaw/workspace/tools/scrapling_fetch.py',
             'https://hormuzstraitmonitor.com/', '30000'],
            capture_output=True, text=True, timeout=60
        )
        text = result.stdout
        if result.returncode != 0 or not text.strip():
            raise RuntimeError(f"scrapling 返回码={result.returncode} stderr={result.stderr[:200]}")
        lg.info(f"爬取成功，文本长度={len(text)}")
    except Exception as e:
        lg.warning(f"爬取失败，使用 fallback: {e}")
        return {
            "transit_count": None,
            "transit_status": "UNKNOWN",
            "stranded_vessels": None,
            "throughput_pct": 50,   # 保守中间值
            "normal_daily": 60,
            "data_source": "fallback"
        }

    # 解析通行量（Ships transiting）
    transit_count = None
    transit_status = "UNKNOWN"
    m = re.search(r'Ships transiting[:\s]*(Near zero|[\d,]+)', text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        if val.lower() == "near zero":
            transit_count = 0
            transit_status = "CLOSED"
        else:
            transit_count = int(val.replace(",", ""))
            transit_status = "OPEN"

    # 解析滞留船只（Stranded vessels）
    stranded = None
    m = re.search(r'Stranded vessels[:\s]*([\d,]+)\+?', text, re.IGNORECASE)
    if m:
        stranded = int(m.group(1).replace(",", ""))

    # 解析吞吐率（Throughput）
    throughput_pct = None
    m = re.search(r'Throughput[:\s]*Under\s*([\d]+)%', text, re.IGNORECASE)
    if m:
        throughput_pct = int(m.group(1))
    else:
        m = re.search(r'Throughput[:\s]*([\d.]+)%', text, re.IGNORECASE)
        if m:
            throughput_pct = float(m.group(1))

    # 解析正常日流量（normal: ~60/day）
    normal_daily = 60  # 默认值
    m = re.search(r'normal[:\s]*~?([\d]+)/day', text, re.IGNORECASE)
    if m:
        normal_daily = int(m.group(1))

    # 如果吞吐率未解析到，根据状态估算
    if throughput_pct is None:
        if transit_status == "CLOSED":
            throughput_pct = 2
        elif transit_count is not None and normal_daily > 0:
            throughput_pct = round(transit_count / normal_daily * 100, 1)
        else:
            throughput_pct = 50  # 保守中间值

    lg.info(f"解析结果: transit={transit_count} status={transit_status} stranded={stranded} throughput={throughput_pct}% normal_daily={normal_daily}")

    return {
        "transit_count": transit_count,
        "transit_status": transit_status,
        "stranded_vessels": stranded,
        "throughput_pct": throughput_pct,
        "normal_daily": normal_daily,
        "data_source": "hormuzstraitmonitor.com"
    }


def get_polymarket(slug, lg):
    """
    从 Polymarket Gamma API 获取市场 YES 概率和交易量。
    只用标准库，不依赖 requests。
    """
    import urllib.request
    url = f'https://gamma-api.polymarket.com/markets?slug={slug}'
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        if data:
            prices = json.loads(data[0].get('outcomePrices', '[]'))
            yes = float(prices[0]) if prices else None
            no  = float(prices[1]) if len(prices) > 1 else (1 - yes if yes is not None else None)
            volume = data[0].get('volume', None)
            volume = float(volume) if volume else None
            lg.info(f"Polymarket [{slug}] YES={yes} NO={no} volume={volume}")
            return yes, no, volume
    except Exception as e:
        lg.warning(f"Polymarket API 失败 [{slug}]: {e}")
    return None, None, None


HISTORY_FILE = "/tmp/poly_macro_history.json"

def load_history():
    """读取历史通行量记录（最近14天）"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history, current_pct):
    """追加当前值，保留最近14天"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # 去重同一天
    history = [h for h in history if h.get("date") != now]
    history.append({"date": now, "pct": current_pct})
    history = history[-14:]  # 最多保留14条
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except Exception:
        pass
    return history

def compute_change(history, current_pct):
    """计算环比变化：对比昨天和7日均值"""
    result = {"day1_delta": None, "day7_avg": None, "day7_delta": None}
    if len(history) >= 2:
        yesterday = history[-2]["pct"]
        result["day1_delta"] = round(current_pct - yesterday, 1)
    if len(history) >= 7:
        avg7 = sum(h["pct"] for h in history[-7:]) / 7
        result["day7_avg"] = round(avg7, 1)
        result["day7_delta"] = round(current_pct - avg7, 1)
    return result

def determine_signal(throughput_pct, change):
    """根据吞吐率 + 环比变化判断信号"""
    d1 = change.get("day1_delta")
    d7 = change.get("day7_delta")

    # 趋势描述
    if d1 is not None:
        trend = f"较昨日{'↓' if d1 < 0 else '↑'}{abs(d1):.1f}%"
        if d7 is not None:
            trend += f"，较7日均值{'↓' if d7 < 0 else '↑'}{abs(d7):.1f}%"
    elif d7 is not None:
        trend = f"较7日均值{'↓' if d7 < 0 else '↑'}{abs(d7):.1f}%"
    else:
        trend = "首次记录，暂无历史对比"

    if throughput_pct < 10:
        return "STRAIT_CLOSED", f"🚫 海峡已关闭（{trend}）", "海峡已关闭，停战概率极低，NO仓坚定持有"
    elif throughput_pct < 50:
        return "SEVERE_DISRUPTION", f"⚠️ 严重中断（{trend}）", "严重中断，停战前不可能恢复，继续持有NO"
    elif throughput_pct < 80:
        return "PARTIAL_DISRUPTION", f"🔶 部分中断（{trend}）", "部分中断，关注和谈进展"
    else:
        return "NORMAL", f"✅ 通行正常（{trend}）", "通行正常，可能停战，考虑平仓"


def main():
    lg = setup_logging()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ── 1. 爬取海峡数据 ──────────────────────────────────────
    strait_data = fetch_strait_data(lg)
    throughput_pct = strait_data["throughput_pct"]

    # ── 2. 获取 Polymarket 盘口 ──────────────────────────────
    m31_yes, m31_no, m31_vol = get_polymarket(SLUG_MARCH31, lg)
    a30_yes, a30_no, a30_vol = get_polymarket(SLUG_APRIL30, lg)

    # ── 3. 历史记录 + 环比计算 ───────────────────────────────
    history = load_history()
    change = compute_change(history, throughput_pct)
    history = save_history(history, throughput_pct)
    lg.info(f"环比: day1_delta={change['day1_delta']} day7_avg={change['day7_avg']} day7_delta={change['day7_delta']}")

    # ── 4. 信号判断 ──────────────────────────────────────────
    signal, signal_cn, recommendation = determine_signal(throughput_pct, change)

    # ── 5. 套利告警 ──────────────────────────────────────────
    mispricing = None
    alert_msg  = None
    if signal == "STRAIT_CLOSED" and m31_yes is not None and m31_yes > 0.15:
        mispricing = f"⚠️ 盘口可能高估停战概率，海峡仍关闭但 YES 价格偏高（march31 YES={m31_yes:.1%}）"
        alert_msg  = f"[宏观引擎] {mispricing}"

    # ── 6. 构建结果 JSON ─────────────────────────────────────
    res = {
        "ts": now,
        "ok": True,
        "mock": False,
        "signal": signal,
        "signal_cn": signal_cn,
        "recommendation": recommendation,
        "change": change,
        "data": strait_data,
        "polymarket": {
            "march31": {
                "yes": m31_yes,
                "no": m31_no,
                "volume": int(m31_vol) if m31_vol else None,
                "url": f"https://polymarket.com/event/{SLUG_MARCH31}"
            },
            "april30": {
                "yes": a30_yes,
                "no": a30_no,
                "volume": int(a30_vol) if a30_vol else None,
                "url": f"https://polymarket.com/event/{SLUG_APRIL30}"
            }
        },
        "mispricing": mispricing,
        "alert": alert_msg
    }

    # ── 6. 写入结果文件 ──────────────────────────────────────
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    lg.info(f"结果已写入 {RESULT_FILE}")

    # ── 7. 发送告警 ──────────────────────────────────────────
    if alert_msg:
        send_alert(alert_msg, lg)
        lg.warning(f"告警已发送: {alert_msg}")

    lg.info(f"完成 signal={signal} throughput={throughput_pct}% march31_yes={m31_yes} april30_yes={a30_yes}")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
