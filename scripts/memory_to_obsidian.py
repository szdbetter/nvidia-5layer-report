#!/usr/bin/env python3
"""
memory_to_obsidian.py
将 workspace/memory/YYYY-MM-DD*.md 归档追加到 Obsidian Daily 笔记。
无 LLM 调用，纯文件操作，省 token。

用法：
  python3 scripts/memory_to_obsidian.py           # 归档今天
  python3 scripts/memory_to_obsidian.py 2026-03-18  # 归档指定日期

服务器 crontab（每晚 23:50 北京时间 = 15:50 UTC）：
  50 15 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/memory_to_obsidian.py >> /tmp/memory_to_obsidian.log 2>&1
"""

import os
import sys
import glob
from datetime import datetime, timezone, timedelta

# ── 路径配置 ──────────────────────────────────────────────
WORKSPACE   = "/root/.openclaw/workspace"
MEMORY_DIR  = os.path.join(WORKSPACE, "memory")
OBSIDIAN_DAILY = "/root/.openclaw/obsidian-vault/Daily"

# ── 跳过的文件（这些是固定知识库文件，不是当天记录）──────
SKIP_PATTERNS = [
    "skills-policy", "skills-store-policy", "session-startup",
    "llm-routing", "wechat-draft", "polymarket-tp1"
]

def beijing_today() -> str:
    """返回北京时间今日日期字符串 YYYY-MM-DD"""
    tz_bj = timezone(timedelta(hours=8))
    return datetime.now(tz_bj).strftime("%Y-%m-%d")

def should_skip(filename: str) -> bool:
    name = os.path.basename(filename).lower()
    for p in SKIP_PATTERNS:
        if p in name:
            return True
    return False

def collect_memory_files(date_str: str) -> list:
    """收集指定日期的所有 memory 文件，按文件名排序"""
    pattern = os.path.join(MEMORY_DIR, f"{date_str}*.md")
    files = sorted(glob.glob(pattern))
    return [f for f in files if not should_skip(f)]

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def build_obsidian_entry(date_str: str, memory_files: list) -> str:
    """将多个 memory 文件组合成 Obsidian 日记追加块"""
    lines = []
    lines.append(f"\n\n---\n## 📥 自动归档 — {date_str}\n")
    lines.append(f"> 由 `memory_to_obsidian.py` 自动合并，共 {len(memory_files)} 个记录文件\n")

    for fpath in memory_files:
        fname = os.path.basename(fpath)
        content = read_file(fpath)
        lines.append(f"\n### 📄 {fname}\n")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)

def ensure_obsidian_daily(date_str: str) -> str:
    """确保 Obsidian Daily 文件存在，返回路径"""
    os.makedirs(OBSIDIAN_DAILY, exist_ok=True)
    daily_path = os.path.join(OBSIDIAN_DAILY, f"{date_str}.md")

    if not os.path.exists(daily_path):
        # 创建基础日记文件
        with open(daily_path, "w", encoding="utf-8") as f:
            f.write(f"---\ndate: {date_str}\ntags: [日记]\n---\n\n# {date_str} 日记\n")
        print(f"[创建] {daily_path}")

    return daily_path

def already_archived(daily_path: str, date_str: str) -> bool:
    """检查是否已经归档过，避免重复追加"""
    content = read_file(daily_path)
    return f"自动归档 — {date_str}" in content

def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else beijing_today()

    print(f"[开始] 归档日期: {date_str}")

    # 1. 收集 memory 文件
    memory_files = collect_memory_files(date_str)
    if not memory_files:
        print(f"[跳过] {date_str} 没有找到 memory 文件")
        return

    print(f"[找到] {len(memory_files)} 个文件: {[os.path.basename(f) for f in memory_files]}")

    # 2. 确保 Obsidian Daily 存在
    daily_path = ensure_obsidian_daily(date_str)

    # 3. 检查是否已归档
    if already_archived(daily_path, date_str):
        print(f"[跳过] {daily_path} 已包含今日归档，不重复写入")
        return

    # 4. 生成追加内容
    entry = build_obsidian_entry(date_str, memory_files)

    # 5. 追加写入
    with open(daily_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"[完成] 已追加到 {daily_path}")
    print(f"[字数] 新增约 {len(entry)} 字符")

if __name__ == "__main__":
    main()
