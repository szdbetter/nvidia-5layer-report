#!/usr/bin/env python3
"""
Lightweight HTTP receiver for Polymarket price data.
Fiona daemon POSTs price ticks here; this writes to VPS ops.db.
Runs on port 8002.
"""
import json
import sqlite3
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.expanduser("~/.openclaw/workspace/data/ops.db")
BJT = timezone(timedelta(hours=8))
AUTH_TOKEN = "poly_sync_2026"  # simple shared secret

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    return c

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/price":
            self._handle_price()
        elif self.path == "/api/alert":
            self._handle_alert()
        elif self.path == "/api/bulk":
            self._handle_bulk()
        else:
            self._respond(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/health":
            c = _conn()
            count = c.execute("SELECT COUNT(*) FROM market_prices").fetchone()[0]
            latest = c.execute("SELECT ts FROM market_prices ORDER BY id DESC LIMIT 1").fetchone()
            c.close()
            self._respond(200, {"ok": True, "rows": count, "latest": latest[0] if latest else None})
        else:
            self._respond(404, {"error": "not found"})

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        return json.loads(body)

    def _check_auth(self):
        token = self.headers.get("X-Auth-Token", "")
        return token == AUTH_TOKEN

    def _handle_price(self):
        if not self._check_auth():
            return self._respond(401, {"error": "unauthorized"})
        data = self._read_json()
        c = _conn()
        c.execute(
            "INSERT INTO market_prices(market_id,market_name,outcome,price,spread,volume,source,ts) VALUES(?,?,?,?,?,?,?,?)",
            (data["market_id"], data.get("market_name"), data["outcome"],
             data["price"], data.get("spread"), data.get("volume"),
             data.get("source", "polymarket"), data["ts"])
        )
        c.commit()
        c.close()
        self._respond(200, {"ok": True})

    def _handle_alert(self):
        if not self._check_auth():
            return self._respond(401, {"error": "unauthorized"})
        data = self._read_json()
        c = _conn()
        c.execute(
            "INSERT INTO alerts(level,source,message,ts) VALUES(?,?,?,?)",
            (data.get("level", "info"), data.get("source"), data["message"], data["ts"])
        )
        c.commit()
        c.close()
        self._respond(200, {"ok": True})

    def _handle_bulk(self):
        if not self._check_auth():
            return self._respond(401, {"error": "unauthorized"})
        data = self._read_json()
        rows = data.get("rows", [])
        c = _conn()
        inserted = 0
        for r in rows:
            c.execute(
                "INSERT INTO market_prices(market_id,market_name,outcome,price,spread,volume,source,ts) VALUES(?,?,?,?,?,?,?,?)",
                (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7])
            )
            inserted += 1
        c.commit()
        c.close()
        self._respond(200, {"ok": True, "inserted": inserted})

    def _respond(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, format, *args):
        pass  # silence logs

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8002), Handler)
    print(f"Price receiver listening on :8002")
    server.serve_forever()
