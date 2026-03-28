#!/usr/bin/env python3
"""
Mock 测试：不影响真实 gateway。
通过伪造状态机，验证 watchdog 的三类通知：
1) 监控上线
2) 异常重启
3) 系统恢复
"""

from __future__ import annotations

import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


STATE_FILE = Path("/tmp/mock_gateway_state.txt")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        state = STATE_FILE.read_text().strip() if STATE_FILE.exists() else "running"
        if state == "running":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"running")
            return

        if state == "hung":
            # 模拟僵死：故意 sleep 超过 watchdog timeout
            time.sleep(10)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"hung")
            return

        self.send_response(500)
        self.end_headers()
        self.wfile.write(state.encode())

    def log_message(self, *_args):
        return


def start_mock_server(port: int = 18080):
    srv = HTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


def main():
    print("[mock] 启动 mock gateway: http://127.0.0.1:18080")
    STATE_FILE.write_text("running")
    srv = start_mock_server()

    print("[mock] 初始状态 running，5 秒后切换到 hung（模拟僵死）")
    time.sleep(5)
    STATE_FILE.write_text("hung")

    print("[mock] 15 秒后切回 running（模拟恢复）")
    time.sleep(15)
    STATE_FILE.write_text("running")

    print("[mock] 继续运行 20 秒，观察 watchdog 恢复消息")
    time.sleep(20)

    srv.shutdown()
    print("[mock] 测试完成")


if __name__ == "__main__":
    os.makedirs("/tmp", exist_ok=True)
    main()
