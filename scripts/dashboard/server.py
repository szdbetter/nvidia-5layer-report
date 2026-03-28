#!/usr/bin/env python3
"""
dashboard/server.py — 任务状态看板（本地HTTP）
运行：python3 scripts/dashboard/server.py
访问：http://localhost:7788

展示：任务列表、最近运行状态、日志片段
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
REGISTRY  = os.path.join(WORKSPACE, "scripts/dashboard/registry.json")
STATUS    = os.path.join(WORKSPACE, "scripts/dashboard/status.json")
TZ_BJ     = timezone(timedelta(hours=8))
PORT      = 7788


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def render_html():
    reg = load_json(REGISTRY)
    status = load_json(STATUS)
    now = datetime.now(TZ_BJ).strftime("%Y-%m-%d %H:%M:%S")

    rows = ""
    for task in reg.get("tasks", []):
        tid = task["id"]
        s = status.get(tid, {})
        last_run = s.get("last_run", "—")
        last_status = s.get("last_status", "—")
        last_output = s.get("last_output", "")[:120].replace("<", "&lt;").replace(">", "&gt;")
        enabled = "✅" if task.get("enabled") else "⏸️"
        interval = task.get("run_at_time", f"{task.get('interval_minutes','?')}min")
        status_badge = {"ok": "🟢", "error": "🔴"}.get(last_status, "⚪")

        rows += f"""
        <tr>
          <td>{enabled} {task['name']}</td>
          <td>{interval}</td>
          <td>{status_badge} {last_status}</td>
          <td>{last_run}</td>
          <td style="font-size:11px;color:#666">{last_output}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Reese Task Dashboard</title>
<meta http-equiv="refresh" content="30">
<style>
  body {{ font-family: -apple-system, sans-serif; padding: 20px; background: #0d1117; color: #c9d1d9; }}
  h1 {{ color: #58a6ff; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ padding: 10px 14px; border-bottom: 1px solid #21262d; text-align: left; }}
  th {{ background: #161b22; color: #8b949e; font-size: 12px; text-transform: uppercase; }}
  tr:hover {{ background: #161b22; }}
  .ts {{ color: #8b949e; font-size: 12px; }}
</style>
</head><body>
<h1>🤖 Reese Task Dashboard</h1>
<p class="ts">更新时间：{now}（北京时间）· 每30秒自动刷新</p>
<table>
  <tr><th>任务</th><th>频率</th><th>状态</th><th>上次运行</th><th>输出</th></tr>
  {rows}
</table>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        html = render_html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format, *args):
        pass  # 静默


if __name__ == "__main__":
    print(f"Dashboard 运行中: http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
