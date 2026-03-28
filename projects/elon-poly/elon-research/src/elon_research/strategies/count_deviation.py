def generate_count_deviation_signal(feature_row: dict, edge_threshold: float) -> bool:
    """根据公平价值与市场中价偏离生成信号。"""

    return (feature_row["fair_value"] - feature_row["market_mid"]) >= edge_threshold
