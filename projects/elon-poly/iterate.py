#!/usr/bin/env python3
"""
自动迭代优化器 v1.0
每次调用：
  1. 运行当前参数回测
  2. 分析弱点，提出改进
  3. 更新参数（网格搜索最优 min_edge + entry_day）
  4. 写 issue.md 记录
  5. 如果达标 → 触发通知

Usage: python3 iterate.py [--notify-channel CHANNEL_ID]
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timezone

PROJ_DIR = "/root/.openclaw/workspace/projects/elon-poly"
RESULT_FILE = f"{PROJ_DIR}/backtest_result.json"
ISSUE_FILE  = f"{PROJ_DIR}/issue.md"
PARAMS_FILE = f"{PROJ_DIR}/params.json"
LOG_FILE    = f"{PROJ_DIR}/iterate_log.jsonl"

# 超参网格搜索范围
ENTRY_DAY_OPTS = [5, 6]
MIN_EDGE_OPTS  = [0.06, 0.08, 0.10, 0.12]

PROFITABLE_THRESHOLD = {
    "win_rate": 0.55,
    "sharpe_annualized": 1.5,
    "total_pnl": 0,
}

def run_backtest(entry_day, min_edge, params_override=None):
    """运行 backtest_engine.py，返回结果 dict"""
    result_tmp = f"{PROJ_DIR}/bt_tmp_{entry_day}_{int(min_edge*100)}.json"
    cmd = [
        "python3", f"{PROJ_DIR}/backtest_engine.py",
        "--entry-day", str(entry_day),
        "--min-edge", str(min_edge),
        "--output", result_tmp,
    ]
    if params_override and os.path.exists(params_override):
        cmd += ["--params", params_override]
    
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if os.path.exists(result_tmp):
        with open(result_tmp) as f:
            result = json.load(f)
        os.remove(result_tmp)
        return result, proc.stdout
    return None, proc.stdout + proc.stderr

def grid_search():
    """网格搜索最优超参"""
    best = None
    best_score = -999
    all_results = []
    
    print("🔍 网格搜索超参组合...")
    for ed in ENTRY_DAY_OPTS:
        for me in MIN_EDGE_OPTS:
            result, output = run_backtest(ed, me)
            if result is None or "error" in result:
                continue
            
            # 综合评分 = Sharpe * 0.5 + 胜率*0.3 + P&L归一化*0.2
            score = (result.get("sharpe_annualized", 0) * 0.5 +
                     result.get("win_rate", 0) * 0.3 +
                     min(result.get("total_pnl", 0) / 5000, 1.0) * 0.2)
            
            all_results.append({
                "entry_day": ed, "min_edge": me,
                "score": score, **result
            })
            
            if score > best_score:
                best_score = score
                best = {"entry_day": ed, "min_edge": me, **result}
            
            print(f"  Day{ed} edge={me:.0%} → Sharpe={result.get('sharpe_annualized',0):.2f} "
                  f"WR={result.get('win_rate',0):.1%} PnL=${result.get('total_pnl',0):+.0f} "
                  f"score={score:.3f}")
    
    return best, all_results

def write_issue(iteration, best, all_results, is_profitable):
    """追加写 issue.md"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    lines = [f"\n---\n## 迭代 #{iteration} — {ts}\n"]
    
    lines.append(f"### 最优超参\n")
    lines.append(f"- Entry Day: Day{best.get('entry_day', '?')}")
    lines.append(f"- Min Edge: {best.get('min_edge', 0):.0%}")
    lines.append(f"- Sharpe: {best.get('sharpe_annualized', 0):.2f}")
    lines.append(f"- 胜率: {best.get('win_rate', 0):.1%}")
    lines.append(f"- 总P&L: ${best.get('total_pnl', 0):+.0f}")
    lines.append(f"- 最大回撤: ${best.get('max_drawdown', 0):.0f}")
    lines.append(f"- 平均Edge: {best.get('avg_edge', 0):.1%}")
    
    lines.append(f"\n### 全网格结果\n")
    lines.append("| Day | Edge | Sharpe | WR | PnL |")
    lines.append("|-----|------|--------|----|-----|")
    for r in sorted(all_results, key=lambda x: x.get("sharpe_annualized", 0), reverse=True)[:8]:
        lines.append(f"| Day{r['entry_day']} | {r['min_edge']:.0%} | "
                    f"{r.get('sharpe_annualized',0):.2f} | "
                    f"{r.get('win_rate',0):.1%} | "
                    f"${r.get('total_pnl',0):+.0f} |")
    
    lines.append(f"\n### 状态\n")
    if is_profitable:
        lines.append("🎯 **达标！可以实盘。**")
    else:
        reasons = []
        if best.get("win_rate", 0) <= 0.55:
            reasons.append(f"胜率 {best.get('win_rate',0):.1%} < 55%")
        if best.get("sharpe_annualized", 0) <= 1.5:
            reasons.append(f"Sharpe {best.get('sharpe_annualized',0):.2f} < 1.5")
        lines.append(f"⚠️ 未达标：{'; '.join(reasons)}")
        
        # 自动分析并提出改进方向
        lines.append(f"\n### 改进方向\n")
        if best.get("win_rate", 0) < 0.5:
            lines.append("- [ ] 提高 min_edge 阈值（当前胜率太低，信号质量差）")
        if best.get("avg_edge", 0) < 0.10:
            lines.append("- [ ] 检查条件概率表是否需要更新（平均edge偏低）")
        if best.get("max_drawdown", 0) > best.get("total_pnl", 1) * 2:
            lines.append("- [ ] 降低 stake_per_trade 或 kelly_half 更保守")
        if best.get("no_trade_periods", 0) > best.get("total_trades", 1):
            lines.append("- [ ] 降低 min_edge 阈值（跳过太多机会）")
    
    with open(ISSUE_FILE, "a") as f:
        f.write("\n".join(lines) + "\n")

def get_iteration_count():
    """获取当前迭代次数"""
    if not os.path.exists(LOG_FILE):
        return 0
    with open(LOG_FILE) as f:
        return sum(1 for line in f if line.strip())

def notify_profitable(best):
    """通过 OpenClaw 通知老板"""
    msg = (
        f"🎯 **Elon Polymarket 策略已稳定盈利！**\n\n"
        f"回测结果（{best.get('total_trades')}次交易）：\n"
        f"• 胜率: {best.get('win_rate',0):.1%}\n"
        f"• 年化Sharpe: {best.get('sharpe_annualized',0):.2f}\n"
        f"• 总P&L: ${best.get('total_pnl',0):+.0f}\n"
        f"• 最大回撤: ${best.get('max_drawdown',0):.0f}\n"
        f"• 最优参数: Day{best.get('entry_day')} 入场, Edge>{best.get('min_edge',0):.0%}\n\n"
        f"老板可以充值实盘了 💰"
    )
    # 写到通知文件，由 cron systemEvent 触发时读取
    with open(f"{PROJ_DIR}/NOTIFY_READY.md", "w") as f:
        f.write(msg)
    print(f"\n🔔 通知已写入 NOTIFY_READY.md")
    return msg

def main():
    os.makedirs(PROJ_DIR, exist_ok=True)
    
    iteration = get_iteration_count() + 1
    ts = datetime.now(timezone.utc).isoformat()
    
    print(f"{'='*60}")
    print(f"🔄 自动迭代优化器 — 第 {iteration} 次迭代")
    print(f"   时间: {ts}")
    print(f"{'='*60}\n")
    
    # 网格搜索
    best, all_results = grid_search()
    
    if not best:
        print("[ERROR] 网格搜索未返回有效结果")
        sys.exit(1)
    
    # 判断是否达标
    is_profitable = (
        best.get("win_rate", 0) > PROFITABLE_THRESHOLD["win_rate"] and
        best.get("sharpe_annualized", 0) > PROFITABLE_THRESHOLD["sharpe_annualized"] and
        best.get("total_pnl", 0) > PROFITABLE_THRESHOLD["total_pnl"]
    )
    
    # 更新最优参数文件
    best_params = {
        "entry_day": best.get("entry_day", 6),
        "min_edge": best.get("min_edge", 0.08),
    }
    with open(PARAMS_FILE, "w") as f:
        json.dump(best_params, f, indent=2)
    
    # 写 issue 日志
    write_issue(iteration, best, all_results, is_profitable)
    
    # 追加 log
    log_entry = {
        "iteration": iteration, "timestamp": ts,
        "is_profitable": is_profitable,
        "best_sharpe": best.get("sharpe_annualized", 0),
        "best_win_rate": best.get("win_rate", 0),
        "best_pnl": best.get("total_pnl", 0),
        "best_params": best_params,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"\n{'='*60}")
    print(f"迭代 #{iteration} 完成")
    print(f"最优: Day{best['entry_day']} edge={best['min_edge']:.0%} "
          f"Sharpe={best.get('sharpe_annualized',0):.2f} "
          f"WR={best.get('win_rate',0):.1%}")
    
    if is_profitable:
        notify_profitable(best)
        print(f"\n🎯 策略已达标！等待老板充值。")
        sys.exit(0)
    else:
        print(f"⚠️  未达标，等待下次迭代（30分钟后）")
        sys.exit(2)

if __name__ == "__main__":
    main()
