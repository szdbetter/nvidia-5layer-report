#!/usr/bin/env python3
"""
用 qwen3:8b (Ollama) 为 research JSON 补全缺失字段：
  - signals: 三大共振信号
  - daily_review: 信号评分
  - top_opportunity: 今日机会

用法:
  python3 enrich-research.py                      # 处理最新的 raw JSON
  python3 enrich-research.py raw_20260325.json    # 处理指定文件
"""
import json, sys, os, glob, httpx
from datetime import datetime

DATA_DIR = "/root/.openclaw/workspace/dashboard-mvp/data/research"
SETTINGS_FILE = "/root/.openclaw/workspace/dashboard-mvp/data/settings.json"
OLLAMA_URL = "http://100.84.3.25:11434/api/chat"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8055188738:AAEUcRH1KbuUSSKH4yxfS0x9gv4GbOuU6e4")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5001695999")


def read_settings() -> dict:
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"telegram_notify": True}

# 高热度阈值
HEAT_THRESHOLDS = {"xhs": 5000, "reddit": 500, "twitter": 5000}
MODEL = "qwen3:8b"


def call_ollama(prompt: str, json_mode: bool = True) -> str | None:
    """调用 Ollama qwen3:8b"""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": 4096},
    }
    if json_mode:
        payload["format"] = "json"
    try:
        r = httpx.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")
    except Exception as e:
        print(f"[enrich] Ollama error: {e}")
        return None


def find_latest_raw() -> str:
    """找到最新的 raw JSON 文件"""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "raw_*.json")),
                   key=os.path.getmtime, reverse=True)
    return files[0] if files else ""


def build_summary(data: dict, top_n: int = 8, include_url: bool = False) -> str:
    """构建数据摘要给 LLM"""
    lines = []
    for platform in ["xhs", "reddit", "twitter"]:
        items = data.get(platform, [])
        for item in items[:top_n]:
            extra = ""
            if platform == "xhs":
                extra = f" 点赞:{item.get('likes',0)} 收藏:{item.get('collects',0)}"
            elif platform == "twitter":
                extra = f" 点赞:{item.get('likes',0)} 转发:{item.get('retweets',0)} 浏览:{item.get('views',0)}"
            url_part = f" URL:{item.get('url','')}" if include_url and item.get('url') else ""
            lines.append(f"[{platform}] {item.get('title','')} (热度:{item.get('score',0)}{extra}){url_part}")
    return "\n".join(lines)


def enrich_signals(data: dict) -> list:
    """生成三大共振信号"""
    summary = build_summary(data)
    prompt = f"""分析以下 AI+Crypto 热点数据，提取 3 个跨平台共振信号。

数据：
{summary}

返回 JSON 格式（严格按此结构）：
{{
  "signals": [
    {{
      "icon": "emoji图标",
      "tag": "信号标签（如：AI工具化浪潮）",
      "color": "#颜色代码（红#ff4d4f/蓝#1890ff/绿#52c41a）",
      "title": "一句话标题",
      "desc": "2-3句话描述，解释为什么这个信号重要"
    }}
  ]
}}

只返回 JSON，不要其他文字。"""

    raw = call_ollama(prompt)
    if not raw:
        return []
    try:
        result = json.loads(raw)
        return result.get("signals", [])[:3]
    except json.JSONDecodeError:
        print(f"[enrich] signals JSON parse error: {raw[:200]}")
        return []


def enrich_review(data: dict) -> list:
    """生成信号评分"""
    summary = build_summary(data)
    prompt = f"""基于以下 AI+Crypto 热点数据，评估 3 个关键信号的强度。

数据：
{summary}

返回 JSON 格式：
{{
  "daily_review": [
    {{
      "signal": "信号名称",
      "score": 1到3的整数评分,
      "comment": "一句话评语"
    }}
  ]
}}

只返回 JSON，不要其他文字。"""

    raw = call_ollama(prompt)
    if not raw:
        return []
    try:
        result = json.loads(raw)
        return result.get("daily_review", [])[:3]
    except json.JSONDecodeError:
        print(f"[enrich] review JSON parse error: {raw[:200]}")
        return []


def enrich_opportunity(data: dict) -> dict | None:
    """生成今日机会"""
    summary = build_summary(data)
    prompt = f"""基于以下 AI+Crypto 热点数据，找出今日最值得关注的一个投资/行动机会。

数据：
{summary}

返回 JSON 格式：
{{
  "top_opportunity": {{
    "title": "机会标题",
    "urgency": "紧急度（🔴急/🟡中/🟢低）",
    "subtitle": "一句话说明",
    "actions": ["行动建议1", "行动建议2", "行动建议3"]
  }}
}}

只返回 JSON，不要其他文字。"""

    raw = call_ollama(prompt)
    if not raw:
        return None
    try:
        result = json.loads(raw)
        return result.get("top_opportunity")
    except json.JSONDecodeError:
        print(f"[enrich] opportunity JSON parse error: {raw[:200]}")
        return None


def enrich_topics(data: dict) -> list:
    """生成爆款选题建议 — 核心功能"""
    summary = build_summary(data, top_n=10, include_url=True)
    prompt = f"""你是一个爆款内容策划专家。你的读者是对 AI 和 Crypto 感兴趣的小白（非技术人员）。

基于以下今日热点数据，挑出 3-5 个最有爆款潜力的选题。

判断标准：
- 跨平台出现（小红书+Reddit+Twitter 同时在聊的话题）
- 热度高且还在上升
- 有争议性或颠覆认知（"你以为的 vs 实际上"）
- 能用简单语言解释给小白听

今日数据（每条包含来源平台、标题、热度和原始URL）：
{summary}

对每个选题，严格按以下 JSON 格式返回：
{{
  "topics": [
    {{
      "title": "选题标题（像小红书爆款标题，20字以内，吸引眼球）",
      "hook": "开头第一句话怎么写（让人想继续看）",
      "what": "这个话题是什么？用一句大白话解释",
      "why": "为什么现在火？背后的逻辑是什么（2-3句）",
      "angle": "切入角度（你要站在什么立场写？举例：反常识、亲身体验、科普、对比测评）",
      "outline": ["大纲要点1", "大纲要点2", "大纲要点3"],
      "platform": "建议发布平台（小红书/公众号/Twitter）",
      "heat_score": 该选题相关内容的热度总和（数字）,
      "confidence": "爆款概率（高/中/低）",
      "source_platform": "来源平台（xhs/reddit/twitter）",
      "source_urls": ["最相关的1-2条原始帖子URL，必须是数据中出现过的真实URL"]
    }}
  ]
}}

要求：
1. 标题要像真正的小红书爆款标题
2. 角度要新颖，不要写成百科科普
3. 大纲要具体到"写什么"，不是"分析什么"
4. 面向小白：不用术语，用类比和例子
5. source_urls 必须从上面数据的 URL 字段中挑选，不能编造

只返回 JSON。"""

    raw = call_ollama(prompt, json_mode=True)
    if not raw:
        return []
    try:
        result = json.loads(raw)
        topics = result.get("topics", [])
        # 按 heat_score 降序
        topics.sort(key=lambda t: t.get("heat_score", 0), reverse=True)
        return topics[:5]
    except json.JSONDecodeError:
        print(f"[enrich] topics JSON parse error: {raw[:200]}")
        return []


def send_telegram(text: str):
    """发送 Telegram 通知"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = httpx.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        if r.status_code == 200:
            print("[enrich] Telegram sent OK")
        else:
            print(f"[enrich] Telegram error: {r.status_code}")
    except Exception as e:
        print(f"[enrich] Telegram error: {e}")


def notify_hot_items(data: dict):
    """推送高热度帖子到 Telegram"""
    hot_items = []
    for platform in ["xhs", "reddit", "twitter"]:
        threshold = HEAT_THRESHOLDS.get(platform, 5000)
        for item in data.get(platform, []):
            if item.get("score", 0) >= threshold:
                hot_items.append((platform, item))

    if not hot_items:
        print("[enrich] No hot items above threshold")
        return

    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    lines = [f"🔥 *ClawLabs 高热度预警* ({date})", ""]
    platform_emoji = {"xhs": "📕", "reddit": "🌐", "twitter": "𝕏"}
    for plat, item in hot_items[:10]:
        emoji = platform_emoji.get(plat, "📊")
        score = item.get("score", 0)
        title = item.get("title", "")[:60]
        lines.append(f"{emoji} *{score:,}* | {title}")

    lines.append(f"\n📊 共 {len(hot_items)} 条高热度 | [查看详情](http://clawlabs.top/research)")
    send_telegram("\n".join(lines))


def main():
    # 确定要处理的文件
    if len(sys.argv) > 1:
        target = os.path.join(DATA_DIR, sys.argv[1])
    else:
        target = find_latest_raw()

    if not target or not os.path.exists(target):
        print(f"[enrich] File not found: {target}")
        sys.exit(1)

    print(f"[enrich] Processing: {os.path.basename(target)}")

    with open(target) as f:
        data = json.load(f)

    changed = False

    # 补全 signals
    if not data.get("signals"):
        print("[enrich] Generating signals...")
        signals = enrich_signals(data)
        if signals:
            data["signals"] = signals
            changed = True
            print(f"[enrich] Generated {len(signals)} signals")

    # 补全 daily_review
    if not data.get("daily_review"):
        print("[enrich] Generating daily_review...")
        review = enrich_review(data)
        if review:
            data["daily_review"] = review
            changed = True
            print(f"[enrich] Generated {len(review)} reviews")

    # 生成爆款选题（每次都重新生成）
    if not data.get("topics"):
        print("[enrich] Generating topic suggestions...")
        topics = enrich_topics(data)
        if topics:
            data["topics"] = topics
            changed = True
            print(f"[enrich] Generated {len(topics)} topic suggestions")

    # 补全 top_opportunity
    if not data.get("top_opportunity"):
        print("[enrich] Generating top_opportunity...")
        opp = enrich_opportunity(data)
        if opp:
            data["top_opportunity"] = opp
            changed = True
            print("[enrich] Generated opportunity")

    # 推送高热度通知（每个文件只推一次，且需设置中启用）
    if not data.get("notified"):
        settings = read_settings()
        if settings.get("telegram_notify", True):
            notify_hot_items(data)
        else:
            print("[enrich] Telegram notify disabled in settings, skipping")
        data["notified"] = True
        changed = True

    if changed:
        with open(target, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[enrich] Saved to {os.path.basename(target)}")
    else:
        print("[enrich] No changes needed")


if __name__ == "__main__":
    main()
