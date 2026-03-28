#!/usr/bin/env python3
"""
极简 OpenClaw Gateway 守护程序
- 实时监控 gateway 状态
- 检测僵死/死锁（状态命令超时或连续失败）
- 自动重启并发送 Discord 报警

安全默认：
- DRY_RUN=1 时仅打印重启动作，不执行真实重启
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Config:
    check_interval_sec: int = int(os.getenv("CHECK_INTERVAL_SEC", "5"))
    status_timeout_sec: int = int(os.getenv("STATUS_TIMEOUT_SEC", "4"))
    fail_threshold: int = int(os.getenv("FAIL_THRESHOLD", "3"))
    restart_cooldown_sec: int = int(os.getenv("RESTART_COOLDOWN_SEC", "20"))
    dry_run: bool = os.getenv("DRY_RUN", "0") == "1"

    # 默认使用 OpenClaw 官方子命令
    status_cmd: str = os.getenv("GATEWAY_STATUS_CMD", "openclaw gateway status")
    restart_cmd: str = os.getenv("GATEWAY_RESTART_CMD", "openclaw gateway restart")

    # Discord 入站 Webhook URL
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_cmd(cmd: str, timeout_sec: int) -> tuple[int, str, str, bool]:
    """返回: (returncode, stdout, stderr, timeout_flag)"""
    try:
        cp = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return cp.returncode, (cp.stdout or "").strip(), (cp.stderr or "").strip(), False
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout>{timeout_sec}s", True


def send_discord(webhook_url: str, content: str) -> None:
    if not webhook_url:
        print(f"[{now_iso()}] [discord-skip] {content}")
        return

    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            _ = resp.read()
    except urllib.error.URLError as e:
        print(f"[{now_iso()}] [discord-error] {e}", file=sys.stderr)


class GatewayWatchdog:
    def __init__(self, config: Config):
        self.cfg = config
        self.running = True
        self.consecutive_failures = 0
        self.last_restart_ts = 0.0
        self.awaiting_recovery = False

    def stop(self, *_args):
        self.running = False

    def is_healthy(self) -> tuple[bool, str]:
        rc, out, err, timeout_flag = run_cmd(self.cfg.status_cmd, self.cfg.status_timeout_sec)
        if timeout_flag:
            return False, "状态检测超时（疑似僵死）"

        blob = f"{out}\n{err}".lower()
        healthy_keywords = ["running", "active", "up", "healthy"]
        unhealthy_keywords = ["stopped", "inactive", "dead", "failed", "error"]

        if rc == 0 and any(k in blob for k in healthy_keywords):
            return True, f"status ok: {out or 'running'}"
        if any(k in blob for k in unhealthy_keywords):
            return False, f"status bad(rc={rc}): {out or err or 'unhealthy'}"

        # 保守策略：非 0 直接判失败；0 但未命中关键词也判可疑
        if rc != 0:
            return False, f"status cmd failed(rc={rc}): {out or err}"
        return False, f"status ambiguous: {out or err or 'empty'}"

    def restart_gateway(self, reason: str) -> None:
        now = time.time()
        if now - self.last_restart_ts < self.cfg.restart_cooldown_sec:
            print(f"[{now_iso()}] [cooldown] skip restart, reason={reason}")
            return

        self.last_restart_ts = now
        msg = f"⚠️【异常重启】Gateway 检测异常，触发重启。原因：{reason}"
        print(f"[{now_iso()}] {msg}")
        send_discord(self.cfg.discord_webhook_url, msg)

        if self.cfg.dry_run:
            print(f"[{now_iso()}] [dry-run] would run: {self.cfg.restart_cmd}")
        else:
            rc, out, err, timeout_flag = run_cmd(self.cfg.restart_cmd, timeout_sec=30)
            print(
                f"[{now_iso()}] restart rc={rc} timeout={timeout_flag} out={out!r} err={err!r}"
            )

        self.awaiting_recovery = True

    def loop(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        online_msg = "✅【监控上线】OpenClaw Gateway Watchdog 已启动"
        print(f"[{now_iso()}] {online_msg}")
        send_discord(self.cfg.discord_webhook_url, online_msg)

        while self.running:
            healthy, detail = self.is_healthy()
            if healthy:
                if self.awaiting_recovery:
                    recover_msg = f"🟢【系统恢复】Gateway 已恢复正常。详情：{detail}"
                    print(f"[{now_iso()}] {recover_msg}")
                    send_discord(self.cfg.discord_webhook_url, recover_msg)
                    self.awaiting_recovery = False
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                print(
                    f"[{now_iso()}] health-fail#{self.consecutive_failures}/{self.cfg.fail_threshold}: {detail}"
                )
                if self.consecutive_failures >= self.cfg.fail_threshold:
                    self.restart_gateway(detail)
                    self.consecutive_failures = 0

            time.sleep(self.cfg.check_interval_sec)


def main():
    cfg = Config()
    wd = GatewayWatchdog(cfg)
    wd.loop()


if __name__ == "__main__":
    main()
