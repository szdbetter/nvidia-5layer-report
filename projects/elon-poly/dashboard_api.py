#!/usr/bin/env python3
"""
Elon Poly - Dashboard API
Flask API on port 8899, serves state and history for web dashboard.
"""

import os
import json
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)
STATE_FILE = "/tmp/elon_trader_state.json"
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
PRICES_FILE = os.path.join(PROJ_DIR, "live_prices.jsonl")
OFFLINE_THRESHOLD = 600  # 10 minutes


def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.after_request
def after_request(response):
    return add_cors(response)


@app.route("/api/elon", methods=["GET", "OPTIONS"])
def get_state():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        stat = os.stat(STATE_FILE)
        age = time.time() - stat.st_mtime
        if age > OFFLINE_THRESHOLD:
            return jsonify({"ok": False, "alert": "trader offline", "age_seconds": int(age)}), 200
        with open(STATE_FILE) as f:
            data = json.load(f)
        data["_age_seconds"] = int(age)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"ok": False, "alert": "trader offline", "detail": "state file not found"}), 200
    except Exception as e:
        return jsonify({"ok": False, "alert": str(e)}), 500


@app.route("/api/elon/history", methods=["GET", "OPTIONS"])
def get_history():
    if request.method == "OPTIONS":
        return jsonify([]), 200
    try:
        if not os.path.exists(PRICES_FILE):
            return jsonify([])
        with open(PRICES_FILE) as f:
            lines = f.readlines()
        last50 = lines[-50:]
        records = []
        for line in last50:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        return jsonify(records)
    except Exception as e:
        return jsonify({"ok": False, "alert": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"ok": True, "ts": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    print("[API] Starting dashboard API on 0.0.0.0:8899")
    app.run(host="0.0.0.0", port=8899, debug=False)
