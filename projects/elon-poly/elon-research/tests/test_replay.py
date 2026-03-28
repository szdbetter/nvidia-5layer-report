from elon_research.backtesting.replay import replay_strategy
from elon_research.strategies.count_deviation import generate_count_deviation_signal
from elon_research.strategies.event_shock import generate_event_shock_signal


def test_generate_count_deviation_signal_requires_minimum_edge() -> None:
    feature_row = {"market_mid": 0.10, "fair_value": 0.16}

    assert generate_count_deviation_signal(feature_row, edge_threshold=0.05) is True
    assert generate_count_deviation_signal(feature_row, edge_threshold=0.07) is False


def test_generate_event_shock_signal_requires_burst_and_edge() -> None:
    feature_row = {"market_mid": 0.20, "fair_value": 0.28, "tweet_delta_1h": 4}

    assert generate_event_shock_signal(feature_row, min_burst=3, edge_threshold=0.05) is True
    assert generate_event_shock_signal(feature_row, min_burst=5, edge_threshold=0.05) is False


def test_replay_strategy_applies_slippage_and_position_limit() -> None:
    feature_rows = [
        {"timestamp": "2026-03-20T03:00:00Z", "market_mid": 0.10, "fair_value": 0.20, "minutes_to_close": 1000},
        {"timestamp": "2026-03-20T04:00:00Z", "market_mid": 0.14, "fair_value": 0.13, "minutes_to_close": 940},
    ]

    result = replay_strategy(
        feature_rows=feature_rows,
        edge_threshold=0.05,
        slippage_bps=100,
        max_position_size=100.0,
    )

    assert result["trades"] == [
        {
            "entry_timestamp": "2026-03-20T03:00:00Z",
            "entry_price": 0.101,
            "size": 100.0,
            "exit_timestamp": "2026-03-20T04:00:00Z",
            "exit_price": 0.139,
        }
    ]
    assert result["summary"] == {"trade_count": 1}
