#!/usr/bin/env python3
"""
scheduler.py — 统一任务调度器
运行方式：crontab 每分钟触发一次
  * * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/scheduler.py >> /tmp/scheduler.log 2>&1

逻辑：读 dashboard/registry.json → 判断哪些任务到期 → 执行 → 写回状态
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
REGISTRY  = os.path.join(WORKSPACE, "scripts/dashboard/registry.json")
STATUS    = os.path.join(WORKSPACE, "scripts/dashboard/status.json")
TZ_BJ     = timezone(timedelta(hours=8))


def now_bj():
    return datetime.now(TZ_BJ)


def load_registry():
    with open(REGISTRY, "r") as f:
        return json.load(f)


def load_status():
    if os.path.exists(STATUS):
        with open(STATUS, "r") as f:
            return json.load(f)
    return {}


def save_status(status):
    with open(STATUS, "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)


def is_due(task, status):
    tid = task["id"]
    now = now_bj()

    # 指定时间运行（如晨报 08:00）
    if "run_at_time" in task:
        target_time = task["run_at_time"]  # "HH:MM"
        th, tm = map(int, target_time.split(":"))
        target_today = now.replace(hour=th, minute=tm, second=0, microsecond=0)

        last_run_str = status.get(tid, {}).get("last_run")
        if last_run_str:
            last_run = datetime.fromisoformat(last_run_str)
            # 今天已跑过就跳过
            if last_run.date() == now.date():
                return False
        # 到时间了
        return now >= target_today

    # 间隔运行
    interval_min = task.get("interval_minutes", 60)
    last_run_str = status.get(tid, {}).get("last_run")
    if not last_run_str:
        return True  # 从未运行过，立刻运行

    last_run = datetime.fromisoformat(last_run_str)
    elapsed = (now - last_run).total_seconds() / 60
    return elapsed >= interval_min


def run_task(task):
    script = os.path.join(WORKSPACE, task["script"])
    if not os.path.exists(script):
        return False, f"脚本不存在: {script}"

    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=300,
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            return True, result.stdout.strip()[-500:] if result.stdout else "ok"
        else:
            return False, (result.stderr or result.stdout or "exit非0").strip()[-500:]
    except subprocess.TimeoutExpired:
        return False, "超时(300s)"
    except Exception as e:
        return False, str(e)


def main():
    reg = load_registry()
    status = load_status()
    now_str = now_bj().isoformat()

    ran = []
    for task in reg["tasks"]:
        if not task.get("enabled", True):
            continue
        if not is_due(task, status):
            continue

        tid = task["id"]
        print(f"[{now_bj().strftime('%H:%M')}] 运行任务: {task['name']}")
        ok, msg = run_task(task)

        status[tid] = {
            "last_run": now_str,
            "last_status": "ok" if ok else "error",
            "last_output": msg
        }
        ran.append(f"{'✅' if ok else '❌'} {task['name']}: {msg[:100]}")

    save_status(status)

    if ran:
        print("\n".join(ran))
    else:
        print(f"[{now_bj().strftime('%H:%M')}] 无到期任务")


if __name__ == "__main__":
    main()
