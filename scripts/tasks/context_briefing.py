#!/usr/bin/env python3
"""
context_briefing.py — CEO上下文简报生成器
每6小时扫描一次，生成 BRIEFING.md 供 Reese 在 session 启动时读取
无 LLM 调用，纯文件扫描+规则提取
"""

import os
import glob
import json
from datetime import datetime, timezone, timedelta

WORKSPACE    = "/root/.openclaw/workspace"
TODO_FILE    = "/root/.openclaw/obsidian-vault/Projects/TODO.md"
MEMORY_DIR   = os.path.join(WORKSPACE, "memory")
BRIEFING_OUT = os.path.join(WORKSPACE, "BRIEFING.md")
STATUS_DB    = os.path.join(WORKSPACE, "scripts/dashboard/status.json")
TZ_BJ        = timezone(timedelta(hours=8))


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


def read_recent_memory(days=1):
    """读最近N天的memory文件，提取关键行"""
    snippets = []
    today = now_bj().date()
    for d in range(days):
        date_str = (today - timedelta(days=d)).strftime("%Y-%m-%d")
        pattern = os.path.join(MEMORY_DIR, f"{date_str}*.md")
        for fpath in sorted(glob.glob(pattern)):
            fname = os.path.basename(fpath)
            # 跳过配置类文件
            if any(x in fname for x in ["skills-policy", "session-startup", "skills-store"]):
                continue
            with open(fpath) as f:
                content = f.read()
            # 只取前200字
            snippets.append(f"**{fname}**\n{content[:200]}...")
    return snippets


def read_task_status():
    if not os.path.exists(STATUS_DB):
        return []
    with open(STATUS_DB) as f:
        status = json.load(f)
    lines = []
    for tid, s in status.items():
        badge = "🟢" if s.get("last_status") == "ok" else "🔴"
        lines.append(f"{badge} {tid}: 上次运行 {s.get('last_run','—')}")
    return lines


def main():
    now = now_bj()
    todos = read_todos()
    snippets = read_recent_memory(days=1)
    task_status = read_task_status()

    lines = [
        f"# CEO 上下文简报",
        f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M')} 北京时间",
        f"> 读此文件可快速恢复上下文，无需翻历史对话",
        "",
        "## 📋 当前待办（TODO.md）",
    ]

    if todos:
        for t in todos:
            lines.append(f"- [ ] {t}")
    else:
        lines.append("_暂无待办，或 TODO.md 不存在_")

    lines += ["", "## 🔧 系统任务状态"]
    if task_status:
        lines += task_status
    else:
        lines.append("_状态文件不存在_")

    lines += ["", "## 📝 近24小时 Memory 摘要"]
    if snippets:
        for s in snippets[:5]:  # 最多5条
            lines.append(s)
            lines.append("")
    else:
        lines.append("_近24小时无新 memory 文件_")

    with open(BRIEFING_OUT, "w") as f:
        f.write("\n".join(lines))

    print(f"简报已生成: {BRIEFING_OUT} | TODO:{len(todos)}条 | Memory片段:{len(snippets)}个")


if __name__ == "__main__":
    main()
