def generate_event_shock_signal(feature_row: dict, min_burst: int, edge_threshold: float) -> bool:
    """仅在事件突发与价格偏离同时满足时生成信号。"""

    return feature_row.get("tweet_delta_1h", 0) >= min_burst and (
        feature_row["fair_value"] - feature_row["market_mid"]
    ) >= edge_threshold
