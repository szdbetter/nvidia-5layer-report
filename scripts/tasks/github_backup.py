#!/usr/bin/env python3
"""
github_backup.py — workspace 增量备份到 GitHub
替代原有 cron 备份任务，统一由 scheduler.py 调度
"""

import subprocess
import sys
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
TZ_BJ = timezone(timedelta(hours=8))


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=WORKSPACE, **kw)


def main():
    now_str = datetime.now(TZ_BJ).strftime("%Y-%m-%d %H:%M UTC+8")

    # 检查是否有变更
    r = run("git status --porcelain")
    if not r.stdout.strip():
        print("无变更，跳过备份")
        return

    run("git add -A")
    r = run(f'git commit -m "auto-backup: {now_str}"')
    if r.returncode != 0:
        print(f"commit失败: {r.stderr}")
        sys.exit(1)

    r = run("git push origin master")
    if r.returncode != 0:
        print(f"push失败: {r.stderr}")
        sys.exit(1)

    # 统计
    r2 = run("git show --stat HEAD")
    lines = [l for l in r2.stdout.split("\n") if "changed" in l]
    print(f"备份完成: {now_str} | {lines[0] if lines else 'done'}")


if __name__ == "__main__":
    main()
