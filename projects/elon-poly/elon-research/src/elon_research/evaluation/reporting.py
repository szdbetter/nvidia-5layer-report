def build_summary_report(backtest_result: dict) -> str:
    """根据回测结果生成中文摘要。"""

    trades = backtest_result.get("trades", [])
    trade_count = len(trades)

    total_profit = 0.0
    peak_profit = 0.0
    max_drawdown = 0.0

    for trade in trades:
        trade_profit = (trade["exit_price"] - trade["entry_price"]) * trade["size"]
        total_profit += trade_profit
        peak_profit = max(peak_profit, total_profit)
        max_drawdown = max(max_drawdown, peak_profit - total_profit)

    if trade_count == 0:
        advice = "当前暂无成交，建议继续观察样本。"
    elif total_profit > 0:
        advice = "策略阶段性为正收益，建议结合更多样本继续验证。"
    else:
        advice = "策略暂未体现稳定优势，建议暂停实盘假设并复查信号。"

    return "\n".join(
        [
            "回测摘要",
            f"总交易次数：{trade_count}",
            f"总收益：{total_profit:.2f}",
            f"最大回撤：{max_drawdown:.2f}",
            f"建议：{advice}",
        ]
    )
