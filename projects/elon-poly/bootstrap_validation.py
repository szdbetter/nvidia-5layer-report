#!/usr/bin/env python3
"""
P7: Bootstrap 置信区间验证
用蒙特卡洛重采样（N=10000）检验策略结果的统计显著性
"""

import json, math, random, statistics, sys
sys.path.insert(0, "/root/.openclaw/workspace/projects/elon-poly")
from backtest_v2 import run_backtest, DEFAULT_PARAMS

N_BOOTSTRAP = 10000
random.seed(42)

def sharpe_from_pnl(pnl_list):
    if len(pnl_list) < 2:
        return 0.0
    avg = statistics.mean(pnl_list)
    std = statistics.stdev(pnl_list)
    return (avg / std) * math.sqrt(52) if std > 0 else 0.0

def bootstrap_run(params, n_bootstrap=N_BOOTSTRAP):
    """
    1. 获取基准回测的每笔 PnL 序列
    2. 有放回重采样 N 次（每次 len 相同）
    3. 计算 Sharpe, P&L 分布
    4. 与零假设（随机押注）对比
    """
    result = run_backtest(params, verbose=False)
    pnl_list = [d["pnl"] for d in result["bet_details"]]
    n = len(pnl_list)
    
    if n < 5:
        return {"error": "样本不足"}
    
    # ── Bootstrap Sharpe & P&L 分布 ──
    bs_sharpes = []
    bs_pnls = []
    for _ in range(n_bootstrap):
        sample = random.choices(pnl_list, k=n)
        bs_sharpes.append(sharpe_from_pnl(sample))
        bs_pnls.append(sum(sample))
    
    bs_sharpes.sort()
    bs_pnls.sort()
    
    ci_sharpe_95 = (bs_sharpes[int(0.025 * n_bootstrap)], bs_sharpes[int(0.975 * n_bootstrap)])
    ci_pnl_95 = (bs_pnls[int(0.025 * n_bootstrap)], bs_pnls[int(0.975 * n_bootstrap)])
    
    # ── 零假设检验：随机押注同一组档位（随机 PnL±） ──
    # 构造零分布：随机打乱 PnL（保留幅度分布，破坏时序）
    null_sharpes = []
    for _ in range(n_bootstrap):
        shuffled = pnl_list[:]
        random.shuffle(shuffled)
        null_sharpes.append(sharpe_from_pnl(shuffled))
    
    # 置换检验 p-value: 零分布中 Sharpe ≥ 实际 Sharpe 的比例
    actual_sharpe = result["sharpe_annualized"]
    p_value = sum(1 for s in null_sharpes if s >= actual_sharpe) / n_bootstrap
    
    # ── 随机入场对照 ──
    # 用随机档位（非模型推荐），相同注额，计算期望
    random_pnls = []
    for _ in range(n_bootstrap):
        rp = random.choice([-1, 8.0]) * random.uniform(100, 200)
        random_pnls.append(rp)
    
    return {
        "actual_sharpe": actual_sharpe,
        "actual_pnl": result["total_pnl"],
        "actual_trades": n,
        "actual_hit_rate": result["hit_rate"],
        "ci_sharpe_95": ci_sharpe_95,
        "ci_pnl_95": ci_pnl_95,
        "ci_sharpe_lo_positive": ci_sharpe_95[0] > 0,
        "ci_pnl_lo_positive": ci_pnl_95[0] > 0,
        "p_value_sharpe": p_value,
        "statistically_significant": p_value < 0.05,
        "n_bootstrap": n_bootstrap,
    }


def main():
    print("="*60)
    print("P7: Bootstrap 置信区间验证 (N=10,000 重采样)")
    print("="*60)
    
    configs = [
        {"label": "Day6/8%/单档 (基准)", "entry_day": 6, "min_edge": 0.08, "multi_bracket": False},
        {"label": "Day6/6%/多档x2 (最优)", "entry_day": 6, "min_edge": 0.06, "multi_bracket": True, "max_brackets": 2},
        {"label": "Day5/6%/单档", "entry_day": 5, "min_edge": 0.06, "multi_bracket": False},
    ]
    
    all_results = []
    for cfg in configs:
        params = DEFAULT_PARAMS.copy()
        params["entry_day"] = cfg["entry_day"]
        params["min_edge"] = cfg["min_edge"]
        params["multi_bracket"] = cfg.get("multi_bracket", False)
        params["max_brackets"] = cfg.get("max_brackets", 3)
        
        print(f"\n▶ {cfg['label']}")
        r = bootstrap_run(params)
        
        print(f"  实际 Sharpe: {r['actual_sharpe']:.2f}")
        print(f"  95% CI Sharpe: [{r['ci_sharpe_95'][0]:.2f}, {r['ci_sharpe_95'][1]:.2f}]")
        print(f"  实际 P&L: ${r['actual_pnl']:,.0f}")
        print(f"  95% CI P&L: [${r['ci_pnl_95'][0]:,.0f}, ${r['ci_pnl_95'][1]:,.0f}]")
        print(f"  p-value (vs 随机): {r['p_value_sharpe']:.4f}")
        sig = "✅ 统计显著" if r['statistically_significant'] else "❌ 不显著"
        ci_ok = "✅ CI下界>0" if r['ci_sharpe_lo_positive'] else "⚠️  CI含负值"
        print(f"  统计显著性: {sig}  |  Sharpe CI: {ci_ok}")
        all_results.append({"config": cfg["label"], **r})
    
    # 写入结果
    out_path = "/root/.openclaw/workspace/projects/elon-poly/bootstrap_result.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 写入: {out_path}")
    
    return all_results

if __name__ == "__main__":
    main()
