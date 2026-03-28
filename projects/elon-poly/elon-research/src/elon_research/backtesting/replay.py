def replay_strategy(
    feature_rows: list[dict],
    edge_threshold: float,
    slippage_bps: int,
    max_position_size: float,
) -> dict:
    """按时间顺序执行最小严格回放，支持滑点与仓位上限。"""

    trades: list[dict] = []
    open_trade: dict | None = None
    slippage = slippage_bps / 10000

    for row in feature_rows:
        edge = row["fair_value"] - row["market_mid"]
        if open_trade is None and edge >= edge_threshold:
            open_trade = {
                "entry_timestamp": row["timestamp"],
                "entry_price": round(row["market_mid"] * (1 + slippage), 3),
                "size": max_position_size,
            }
            continue

        if open_trade is not None and edge < 0:
            open_trade["exit_timestamp"] = row["timestamp"]
            open_trade["exit_price"] = round(row["market_mid"] * (1 - slippage), 3)
            trades.append(open_trade)
            open_trade = None

    return {"trades": trades, "summary": {"trade_count": len(trades)}}
