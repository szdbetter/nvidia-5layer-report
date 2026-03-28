#!/usr/bin/env python3
"""
morning_briefing.py — 每日晨报推送到 Discord #思过崖
读 BRIEFING.md + TODO.md，格式化后推送
通过 OpenClaw webhook 发送（复用 .env 中的配置）
"""

import os
import glob
import subprocess
import json
from datetime import datetime, timezone, timedelta

WORKSPACE  = "/root/.openclaw/workspace"
TODO_FILE  = "/root/.openclaw/obsidian-vault/Projects/TODO.md"
BRIEFING   = os.path.join(WORKSPACE, "BRIEFING.md")
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TZ_BJ      = timezone(timedelta(hours=8))

# Discord channel ID for #思过崖
DISCORD_CHANNEL = "1483250878369497218"


def now_bj():
    return datetime.now(TZ_BJ)


def read_todos():
    if not os.path.exists(TODO_FILE):
        return []
    todos = []
    with open(TODO_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("- [ ]"):
                todos.append(line[5:].strip())
    return todos


def get_yesterday_summary():
    """从昨天的 memory 文件提取摘要"""
    yesterday = (now_bj().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    pattern = os.path.join(MEMORY_DIR, f"{yesterday}.md")
    files = glob.glob(pattern)
    if not files:
        return None
    with open(files[0]) as f:
        content = f.read()
    # 取前300字
    return content[:300].replace("\n", " ").strip()


def send_via_openclaw(message: str):
    """通过 openclaw CLI 发送消息"""
    cmd = [
        "openclaw", "send",
        "--channel", "discord",
        "--to", DISCORD_CHANNEL,
        "--message", message
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # fallback: 写入文件，等 Reese 手动读
        fallback = os.path.join(WORKSPACE, "scripts/dashboard/morning_briefing_pending.md")
        with open(fallback, "w") as f:
            f.write(message)
        print(f"发送失败，已写入 fallback: {fallback}\n{r.stderr}")
        return False
    return True


def build_message():
    now = now_bj()
    todos = read_todos()
    yesterday_summary = get_yesterday_summary()

    lines = [
        f"## 🌅 {now.strftime('%m月%d日')} 晨报",
        f"_北京时间 {now.strftime('%H:%M')}_",
        "",
    ]

    if todos:
        lines.append(f"**📋 待办清单（{len(todos)}项）**")
        for t in todos[:8]:  # 最多显示8条
            lines.append(f"- [ ] {t}")
        if len(todos) > 8:
            lines.append(f"_... 还有 {len(todos)-8} 项，查看 Projects/TODO.md_")
    else:
        lines.append("**📋 待办清单**：暂无，在 Obsidian `Projects/TODO.md` 中添加")

    if yesterday_summary:
        lines += ["", f"**📝 昨日摘要**", f"> {yesterday_summary[:200]}"]

    lines += ["", "_输入 @Reese 开始今日工作_"]
    return "\n".join(lines)


def main():
    msg = build_message()
    ok = send_via_openclaw(msg)
    if ok:
        print(f"晨报发送成功: {now_bj().strftime('%H:%M')}")
    else:
        print("晨报发送失败，已写入 fallback 文件")


if __name__ == "__main__":
    main()
