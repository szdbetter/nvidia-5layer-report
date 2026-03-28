#!/usr/bin/env python3
"""
Smart Money Dashboard
端口: 127.0.0.1:1980
"""
import sqlite3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.expanduser("~/smart_money/smart_money.db")
PORT = int(os.getenv('SM_DASHBOARD_PORT', '1980'))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Smart Money Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
<style>.mono{font-family:monospace}</style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen" x-data="app()" x-init="init()">
<div class="max-w-7xl mx-auto p-4">

  <!-- Header -->
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-yellow-400">🧠 Smart Money Dashboard</h1>
    <span class="text-gray-400 text-sm" x-text="stats.last_crawl ? '最后更新: '+stats.last_crawl : '加载中...'"></span>
  </div>

  <!-- Stats Cards -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-gray-800 rounded-lg p-4">
      <div class="text-gray-400 text-sm">✅ 确认SM</div>
      <div class="text-3xl font-bold text-green-400" x-text="stats.confirmed_sm || 0"></div>
    </div>
    <div class="bg-gray-800 rounded-lg p-4">
      <div class="text-gray-400 text-sm">🔍 候选</div>
      <div class="text-3xl font-bold text-yellow-400" x-text="stats.candidates || 0"></div>
    </div>
    <div class="bg-gray-800 rounded-lg p-4">
      <div class="text-gray-400 text-sm">🪙 追踪代币</div>
      <div class="text-3xl font-bold text-blue-400" x-text="stats.tokens_tracked || 0"></div>
    </div>
    <div class="bg-gray-800 rounded-lg p-4">
      <div class="text-gray-400 text-sm">🤖 Bot过滤</div>
      <div class="text-3xl font-bold text-red-400" x-text="stats.bots_filtered || 0"></div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="flex gap-4 mb-4 border-b border-gray-700">
    <button @click="tab='leaderboard'" :class="tab=='leaderboard'?'border-b-2 border-yellow-400 text-yellow-400':'text-gray-400'" class="pb-2 px-2">🏆 排行榜</button>
    <button @click="tab='signals'" :class="tab=='signals'?'border-b-2 border-yellow-400 text-yellow-400':'text-gray-400'" class="pb-2 px-2">⚡ 信号</button>
  </div>

  <!-- Leaderboard -->
  <div x-show="tab=='leaderboard'" class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="text-gray-400 border-b border-gray-700">
          <th class="pb-2 text-left">#</th>
          <th class="pb-2 text-left">地址</th>
          <th class="pb-2 text-right">Score</th>
          <th class="pb-2 text-right">跨币</th>
          <th class="pb-2 text-right">利润</th>
          <th class="pb-2 text-right">胜率</th>
          <th class="pb-2 text-left">标签</th>
        </tr>
      </thead>
      <tbody>
        <template x-for="(w,i) in wallets" :key="w.address">
          <tr class="border-b border-gray-800 hover:bg-gray-800 cursor-pointer" @click="selectWallet(w)">
            <td class="py-2 text-gray-500" x-text="i+1"></td>
            <td class="py-2 mono text-yellow-300" x-text="(w.name || w.address.slice(0,8)+'...')"></td>
            <td class="py-2 text-right">
              <span :class="w.smart_score>=70?'text-green-400':w.smart_score>=50?'text-yellow-400':'text-gray-400'"
                    x-text="w.smart_score.toFixed(1)"></span>
            </td>
            <td class="py-2 text-right text-blue-400" x-text="w.tokens_profitable"></td>
            <td class="py-2 text-right text-green-400" x-text="'$'+(w.total_profit||0).toLocaleString('en',{maximumFractionDigits:0})"></td>
            <td class="py-2 text-right" x-text="((w.win_rate||0)*100).toFixed(0)+'%'"></td>
            <td class="py-2 text-xs text-gray-400" x-text="(JSON.parse(w.labels||'[]')).slice(0,2).join(',')"></td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>

  <!-- Signals -->
  <div x-show="tab=='signals'">
    <template x-if="signals.length==0">
      <div class="text-gray-500 text-center py-8">暂无信号</div>
    </template>
    <template x-for="s in signals" :key="s.id">
      <div class="bg-gray-800 rounded-lg p-4 mb-3">
        <div class="flex justify-between">
          <span :class="s.action=='buy'?'text-green-400':'text-red-400'" class="font-bold"
                x-text="s.action=='buy'?'🟢 买入':'🔴 卖出'"></span>
          <span class="text-gray-400 text-sm" x-text="s.detected_at"></span>
        </div>
        <div class="mono text-yellow-300 text-sm mt-1" x-text="s.wallet_address"></div>
        <div class="flex gap-4 mt-2 text-sm">
          <span class="text-blue-400" x-text="'$'+s.token_symbol"></span>
          <span class="text-gray-400" x-text="'金额: $'+(s.amount_usd||0).toLocaleString()"></span>
          <span class="text-yellow-400" x-text="'Score: '+s.smart_score?.toFixed(1)"></span>
        </div>
      </div>
    </template>
  </div>

</div>

<script>
function app() {
  return {
    tab: 'leaderboard',
    wallets: [],
    signals: [],
    stats: {},
    async init() {
      await this.loadAll();
      setInterval(() => this.loadAll(), 60000);
    },
    async loadAll() {
      const [s, w, sig] = await Promise.all([
        fetch('/api/stats').then(r=>r.json()),
        fetch('/api/wallets').then(r=>r.json()),
        fetch('/api/signals').then(r=>r.json()),
      ]);
      this.stats = s;
      this.wallets = w;
      this.signals = sig;
    },
    selectWallet(w) {
      window.open('https://gmgn.ai/sol/address/'+w.address, '_blank');
    }
  }
}
</script>
</body>
</html>"""


def get_db():
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默日志
    
    def send_json(self, data, code=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            body = HTML_TEMPLATE.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
            return
        
        conn = get_db()
        if not conn:
            self.send_json({'error': 'DB not found'}, 503)
            return
        
        c = conn.cursor()
        
        if path == '/api/stats':
            c.execute("SELECT COUNT(*) FROM wallets WHERE status='confirmed'")
            confirmed = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM wallets WHERE status='candidate'")
            candidate = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM wallets WHERE is_bot=1")
            bots = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM tokens")
            tokens = c.fetchone()[0]
            c.execute("SELECT MAX(finished_at) FROM crawl_logs WHERE status='success'")
            last_crawl = c.fetchone()[0]
            self.send_json({
                'confirmed_sm': confirmed, 'candidates': candidate,
                'bots_filtered': bots, 'tokens_tracked': tokens, 'last_crawl': last_crawl
            })
        
        elif path == '/api/wallets':
            qs = parse_qs(parsed.query)
            limit = int(qs.get('limit', ['100'])[0])
            c.execute("""
                SELECT address, smart_score, tokens_profitable, total_realized_profit,
                       win_rate, labels, name, last_active, status
                FROM wallets WHERE is_bot=FALSE
                ORDER BY smart_score DESC LIMIT ?
            """, (limit,))
            cols = ['address','smart_score','tokens_profitable','total_profit','win_rate','labels','name','last_active','status']
            self.send_json([dict(zip(cols, r)) for r in c.fetchall()])
        
        elif path == '/api/signals':
            c.execute("""
                SELECT id, wallet_address, token_address, token_symbol, action,
                       amount_usd, smart_score, detected_at, notified
                FROM signals ORDER BY detected_at DESC LIMIT 50
            """)
            cols = ['id','wallet_address','token_address','token_symbol','action','amount_usd','smart_score','detected_at','notified']
            self.send_json([dict(zip(cols, r)) for r in c.fetchall()])
        
        else:
            self.send_json({'error': 'not found'}, 404)
        
        conn.close()


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f"🚀 Dashboard: http://127.0.0.1:{PORT}")
    server.serve_forever()
