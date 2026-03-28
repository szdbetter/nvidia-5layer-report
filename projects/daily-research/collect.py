#!/usr/bin/env python3
"""
Daily AI+Crypto Research Collector
三平台采集：小红书 + X(Twitter via Fiona) + Reddit
MiniMax M2.7 做分析汇总
"""
import json, urllib.request, os, subprocess, concurrent.futures, sys
from datetime import datetime, timezone, timedelta

# 加载 .env
_env_path = "/root/.openclaw/.env"
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ── 配置 ──────────────────────────────────────────────
XHS_MCP = "http://localhost:18060/mcp"
MINIMAX_URL = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
FIONA_NODE = "7b53806ae001dccd8ad5643c4eb63c788cc35efaf32c1b0181f8ea599023ae94"
OUTPUT_DIR = "/root/.openclaw/workspace/dashboard-mvp/data/research"
SETTINGS_FILE = "/root/.openclaw/workspace/dashboard-mvp/data/settings.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

_S = load_settings()
LIMITS    = _S.get("collect_limits", {"xhs": 20, "reddit": 20, "twitter": 15})
MIN_SCORE = _S.get("min_score",      {"xhs": 0,  "reddit": 0,  "twitter": 30})

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ── 工具函数 ──────────────────────────────────────────
def http_post(url, data, headers, timeout=45):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.headers.get("mcp-session-id"), json.loads(r.read())

def xhs_mcp(method, params=None, sid=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json,text/event-stream"}
    if sid: headers["mcp-session-id"] = sid
    _, body = http_post(XHS_MCP, {"jsonrpc":"2.0","id":1,"method":method,"params":params or {}}, headers)
    return body

# ── 1. 小红书 ─────────────────────────────────────────
def fetch_xhs():
    log("小红书采集开始...")
    init = xhs_mcp("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"collector","version":"1.0"}})
    sid = None
    # 从response header拿sid，这里重新调用
    headers = {"Content-Type": "application/json", "Accept": "application/json,text/event-stream"}
    req = urllib.request.Request(XHS_MCP, data=json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"c","version":"1"}}}).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        sid = r.headers.get("mcp-session-id")

    results = []
    for kw, label in [("AI大模型 Claude","AI"), ("比特币 加密货币","Crypto")]:
        headers2 = {"Content-Type":"application/json","Accept":"application/json,text/event-stream","mcp-session-id":sid}
        req2 = urllib.request.Request(XHS_MCP,
            data=json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
                "name":"search_feeds","arguments":{"keyword":kw,"filters":{"sort_by":"最多点赞","publish_time":"一周内"}}
            }}).encode(), headers=headers2)
        with urllib.request.urlopen(req2, timeout=45) as r:
            body = json.loads(r.read())
        feeds = json.loads(body["result"]["content"][0]["text"]).get("feeds", [])
        for f in feeds:
            nc = f.get("noteCard", {})
            ii = nc.get("interactInfo", {})
            def n(s):
                s = str(s or "0").replace("+","").strip()
                if "w" in s: return int(float(s.replace("w",""))*10000)
                return int(s) if s.isdigit() else 0
            liked, collected, comments = n(ii.get("likedCount")), n(ii.get("collectedCount")), n(ii.get("commentCount"))
            results.append({
                "platform": "小红书", "category": label,
                "title": nc.get("displayTitle","")[:120],
                "score": liked + collected*2 + comments*2,
                "likes": liked, "collects": collected, "comments": comments,
                "url": f"https://www.xiaohongshu.com/explore/{f.get('id','')}"
            })
    # 去重排序
    seen, deduped = set(), []
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        k = r["title"][:40]
        if k not in seen: seen.add(k); deduped.append(r)
    min_s = MIN_SCORE.get("xhs", 0)
    deduped = [r for r in deduped if r["score"] >= min_s]
    limit = LIMITS.get("xhs", 20)
    log(f"小红书: {len(deduped)} 条（min_score≥{min_s}，取前{limit}）")
    return deduped[:limit]

# ── 2. Reddit ─────────────────────────────────────────
def fetch_reddit():
    log("Reddit采集开始...")
    results = []
    env = os.environ
    for sub, label in [("artificial","AI"), ("CryptoCurrency","Crypto")]:
        req = urllib.request.Request(
            f"https://www.reddit.com/r/{sub}/hot.json?limit=30",
            headers={"Cookie": f"reddit_session={env.get('REDDIT_SESSION','')}; token_v2={env.get('REDDIT_TOKEN_V2','')}",
                     "User-Agent": "Mozilla/5.0 AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        for p in d.get("data",{}).get("children",[]):
            pd = p["data"]
            score = pd.get("ups",0) + pd.get("num_comments",0)*2
            results.append({"platform":"Reddit","category":label,
                "title": pd.get("title","")[:120], "score": score,
                "likes": pd.get("ups",0), "comments": pd.get("num_comments",0),
                "url": "https://reddit.com"+pd.get("permalink","")})
    results.sort(key=lambda x: x["score"], reverse=True)
    min_s = MIN_SCORE.get("reddit", 0)
    results = [r for r in results if r["score"] >= min_s]
    limit = LIMITS.get("reddit", 20)
    log(f"Reddit: {len(results)} 条（min_score≥{min_s}，取前{limit}）")
    return results[:limit]

# ── 3. X via VPS本地xreach (cookie from .env) ─────────
def fetch_twitter_once(auth_token, ct0, timeout=45):
    """单次抓取，返回原始列表或抛出异常"""
    results = []
    for q, label in [("AI LLM agent Claude 2026","AI"), ("bitcoin crypto ethereum 2026","Crypto")]:
        result = subprocess.run(
            ["xreach","search",q,"-n","20","--json",
             "--auth-token",auth_token,"--ct0",ct0],
            capture_output=True, text=True, timeout=timeout
        )
        d = json.loads(result.stdout)
        tweets = d.get("items", d.get("tweets", d.get("data", [])))
        for t in tweets:
            if t.get("isRetweet"): continue
            likes = t.get("likeCount",0); rt = t.get("retweetCount",0)
            bk = t.get("bookmarkCount",0); views = t.get("viewCount",0)
            score = likes + rt*3 + bk*2
            if score < MIN_SCORE.get("twitter", 30): continue
            results.append({"platform":"X","category":label,
                "title": t.get("text","")[:120],
                "score": score, "likes": likes, "retweets": rt, "bookmarks": bk, "views": views,
                "url": f"https://twitter.com/i/web/status/{t.get('id','')}"})
    return results

def fetch_twitter(max_retries=3, retry_delay=8):
    log("X(Twitter)采集开始 via VPS xreach...")
    import time
    auth_token = os.environ.get("TWITTER_AUTH_TOKEN","")
    ct0 = os.environ.get("TWITTER_CT0","")
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            results = fetch_twitter_once(auth_token, ct0, timeout=45)
            if results:
                results.sort(key=lambda x: x["score"], reverse=True)
                for i, r in enumerate(results): r["rank"] = i + 1
                limit = LIMITS.get("twitter", 15)
                log(f"X: {len(results)} 条 (第{attempt}次成功，取前{limit})")
                return results[:limit]
            else:
                log(f"X: 第{attempt}次返回0条，{'重试中' if attempt < max_retries else '放弃'}")
        except Exception as e:
            last_err = e
            log(f"X: 第{attempt}次失败: {e}，{'重试中' if attempt < max_retries else '放弃'}")
        if attempt < max_retries:
            time.sleep(retry_delay)
    log(f"X: 全部{max_retries}次尝试失败，last_err={last_err}")
    return []

# ── 4. MiniMax分析 ────────────────────────────────────
DOUBAO_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

DEEP_ANALYSIS_PROMPT_TPL = """你是一位深度研究AI+加密货币的首席分析师，同时具备内容创作嗅觉。以下是今日{total}条多平台热点数据，请完成如下深度分析（输出可直接拿来使用，无需润色）：

---

## 一、跨平台共振雷达（必须≥3条）

逐条输出跨平台共振信号，格式：
**信号名** | 涉及平台 | 热度合计
> 一句话说明共振背后的深层逻辑（是叙事升级？资金流入？技术突破？监管变化？）
> 研判：短期炒作 / 中期趋势 / 长期结构变化？

---

## 二、今日爆款选题库（Top 5，可直接用于创作）

每条格式：
**[平台] 标题** | 热度分：XX
- 爆款逻辑：为什么这条内容能火？（情绪共鸣/认知差/信息差/稀缺性？）
- 衍生角度：你可以写的3个相关选题（具体到标题级别）
- 适合平台：小红书 / X / 公众号 / 短视频

---

## 三、今日最高确定性机会（1个，精确到可执行动作）

格式：
**机会标题**
背景：（2-3句，讲清楚为什么是现在）
信号链：数据1 → 数据2 → 数据3（逻辑推导链条）
执行方案：
| 动作 | 标的/平台 | 入场条件 | 止损/退出 |
|------|----------|---------|---------|
催化剂时间表：接下来7天内可能触发的关键事件
风险提示：1-2条最大风险

---

## 四、沉默信号（反向机会）

哪条数据表面热度高、实质泡沫大？为什么要反向操作或回避？

---

【原始数据】

### 小红书（热度=点赞+收藏×2+评论×2）
{xhs_data}

### X/Twitter（热度=点赞+转发×3+书签×2）
{twitter_data}

### Reddit（热度=点赞+评论×2）
{reddit_data}

---
请直接输出分析正文，不要加开场白或结尾废话。"""


def build_analysis_prompt(xhs, reddit, twitter):
    def fmt(items, n=10):
        lines = []
        for r in items[:n]:
            lines.append(f"- [{r.get('platform','?')}] {r['title']} [热度{r['score']}]")
        return "\n".join(lines) if lines else "（无数据）"
    total = len(xhs) + len(reddit) + len(twitter)
    return DEEP_ANALYSIS_PROMPT_TPL.format(
        total=total,
        xhs_data=fmt(xhs, 10),
        twitter_data=fmt(twitter, 8) if twitter else "（Fiona节点离线，暂无数据）",
        reddit_data=fmt(reddit, 8)
    )


def call_minimax(prompt):
    """主力：MiniMax M2.7"""
    env = os.environ
    key = env.get("MINIMAX_API_KEY", "")
    if not key:
        raise ValueError("MINIMAX_API_KEY not set")
    req = urllib.request.Request(MINIMAX_URL,
        data=json.dumps({"model":"MiniMax-M2.7","messages":[{"role":"user","content":prompt}],"max_tokens":3500}).encode(),
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]


def call_doubao_fallback(prompt):
    """Fallback：火山引擎 doubao-seed-2.0-pro"""
    env = os.environ
    key = env.get("VOLCENGINE_API_KEY", "")
    if not key:
        raise ValueError("VOLCENGINE_API_KEY not set")
    req = urllib.request.Request(DOUBAO_URL,
        data=json.dumps({"model":"doubao-seed-2.0-pro-250615","messages":[{"role":"user","content":prompt}],"max_tokens":2500}).encode(),
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]


def analyze_with_minimax(xhs, reddit, twitter):
    log("深度分析中（MiniMax主力 / Doubao备用）...")
    prompt = build_analysis_prompt(xhs, reddit, twitter)
    try:
        result = call_minimax(prompt)
        log(f"MiniMax分析完成，{len(result)}字")
        return result
    except Exception as e:
        log(f"MiniMax失败({e})，切换Doubao fallback...")
        try:
            result = call_doubao_fallback(prompt)
            log(f"Doubao分析完成，{len(result)}字")
            return "[Fallback: Doubao]\n" + result
        except Exception as e2:
            log(f"Doubao也失败: {e2}")
            return ""

# ── 主流程 ────────────────────────────────────────────
def main():
    now_bj = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    log(f"=== Daily Research 开始 {now_bj} ===")

    # 并发采集XHS + Reddit，X串行（依赖Fiona）
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_xhs = ex.submit(fetch_xhs)
        f_reddit = ex.submit(fetch_reddit)
        xhs = f_xhs.result(timeout=90) if True else []
        reddit = f_reddit.result(timeout=30) if True else []

    try: xhs = f_xhs.result(timeout=90)
    except Exception as e: log(f"XHS失败: {e}"); xhs = []
    try: reddit = f_reddit.result(timeout=30)
    except Exception as e: log(f"Reddit失败: {e}"); reddit = []

    twitter = []
    try: twitter = fetch_twitter()
    except Exception as e: log(f"X失败: {e}")

    # 保存原始数据
    # 提取 BJ time 部分
    time_bj = now_bj.split(" ")[1] + " BJT" if " " in now_bj else now_bj
    raw = {
        "date": now_bj.split(" ")[0],
        "time": time_bj,
        "twitterOnline": len(twitter) > 0,
        "stats": {
            "total": len(xhs) + len(reddit) + len(twitter),
            "xhs": len(xhs),
            "reddit": len(reddit),
            "twitter": len(twitter)
        },
        "xhs": xhs, "reddit": reddit, "twitter": twitter
    }

    # MiniMax分析（先分析再保存，结果写入raw）
    analysis = ""
    try: analysis = analyze_with_minimax(xhs, reddit, twitter)
    except Exception as e: log(f"MiniMax失败: {e}")

    raw["analysis"] = analysis
    with open(f"{OUTPUT_DIR}/raw_{datetime.now().strftime('%Y%m%d_%H%M')}.json","w") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    # 输出报告
    report = f"""# 🔍 AI+Crypto 每日热点情报
**{now_bj} BJ | 小红书·X·Reddit 三平台**

---

## 📊 MiniMax 分析

{analysis}

---

## 📋 原始数据 Top10

### 🔴 小红书
{chr(10).join([f"{i+1}. [{r['title']}]({r['url']}) 热度{r['score']}" for i,r in enumerate(xhs[:10])])}

### 🐦 X (Twitter)
{chr(10).join([f"{i+1}. {r['title'][:80]}... ❤️{r['likes']} 🔁{r.get('retweets',0)} 👁{r.get('views',0)}" for i,r in enumerate(twitter[:5])]) if twitter else "（节点离线）"}

### 🟠 Reddit
{chr(10).join([f"{i+1}. [{r['title']}]({r['url']}) 热度{r['score']}" for i,r in enumerate(reddit[:10])])}
"""

    report_path = f"{OUTPUT_DIR}/report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(report_path, "w") as f:
        f.write(report)

    print(report)
    log(f"=== 完成，报告已存 {report_path} ===")

if __name__ == "__main__":
    # 加载.env
    env_path = "/root/.openclaw/.env"
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    main()
