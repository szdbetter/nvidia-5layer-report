#!/usr/bin/env python3
"""
Elon Poly 交易守护进程
纯脚本，每30分钟轮询一次，零LLM成本
告警通过 Discord Webhook 发送
"""
import time, json, os, sys, signal, traceback

INTERVAL = 300  # 5分钟
PROJ = os.path.dirname(os.path.abspath(__file__))
PID_FILE = "/tmp/elon_poly_daemon.pid"
LOG_FILE = os.path.join(PROJ, "daemon.log")

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def cleanup(signum=None, frame=None):
    log("Daemon shutting down")
    try: os.unlink(PID_FILE)
    except: pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

def main():
    # 写 PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    log(f"Daemon started (pid={os.getpid()}, interval={INTERVAL}s)")

    while True:
        try:
            # 导入策略引擎（每次重新导入以支持热更新）
            import importlib
            spec = importlib.util.spec_from_file_location("engine", os.path.join(PROJ, "strategy_engine.py"))
            engine = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(engine)

            # 运行策略引擎
            engine.main()

            # 读取决策结果
            with open("/tmp/elon_strategy.json") as f:
                state = json.load(f)

            # v2: decisions是list; v1: decision是dict
            decs = state.get("decisions", [])
            d = decs[0] if decs else state.get("decision", {})
            action = d.get("action", "?")
            urgency = d.get("urgency", "?")
            pos_count = state.get("position_count", "?")
            usdc = state.get("usdc_balance", "?")
            executed = state.get("executed", [])
            exec_str = f" | EXEC: {', '.join(executed)}" if executed else ""
            log(f"Day{state['day']} | 🐦{state['tweets']} | 预测{state['prediction']['mean']}±{state['prediction']['std']} | {action} [{urgency}] | 持仓{pos_count} | USDC ${usdc}{exec_str}")

        except Exception as e:
            log(f"ERROR: {e}")
            traceback.print_exc()

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
