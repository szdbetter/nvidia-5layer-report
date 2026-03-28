import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from elon_research.backtesting.replay import replay_strategy
from elon_research.features.build import build_feature_rows


def run_weak_validation(
    normalized_dir: Path,
    reports_dir: Path,
    event_id: int,
    tracking_id: str,
    top_brackets: int = 3,
) -> Path:
    """基于标准化市场数据执行首轮弱验证并输出中文报告。"""
    markets = _read_json(normalized_dir / f"event_{event_id}_markets.json")
    trades = _read_json(normalized_dir / f"event_{event_id}_trades.json")
    prices = _read_json(normalized_dir / f"event_{event_id}_prices.json")
    tweet_summary = _read_json(normalized_dir / f"tracking_{tracking_id}_summary.json")

    total_tweets = int(tweet_summary.get("total") or 0)
    proxy_tweet_rows = _expand_daily_summary_to_proxy_tweets(tweet_summary.get("daily", {}))
    top = _top_liquid_brackets(trades, top_n=top_brackets)
    backtest_rows: list[dict[str, Any]] = []
    bracket_results: list[dict[str, Any]] = []
    aggregated_features: list[dict[str, Any]] = []
    end_ts = _parse_iso_to_ts(tweet_summary.get("end_date"))

    for bracket in top:
        yes_prices = [
            row
            for row in prices
            if row.get("outcome") == "Yes"
            and row.get("bracket_low") == bracket[0]
            and row.get("bracket_high") == bracket[1]
        ]
        yes_prices.sort(key=lambda row: row.get("timestamp", 0))
        if not yes_prices:
            continue
        feature_rows = _build_proxy_feature_rows(
            tweet_rows=proxy_tweet_rows,
            yes_price_rows=yes_prices,
            bracket_low=bracket[0],
            bracket_high=bracket[1],
            end_date=tweet_summary.get("end_date"),
            fallback_total_tweets=total_tweets,
        )
        replay_result = replay_strategy(
            feature_rows=feature_rows,
            edge_threshold=0.05,
            slippage_bps=100,
            max_position_size=10.0,
        )
        aggregated_features.extend(feature_rows)
        window_results = _run_window_replays(
            feature_rows=feature_rows,
            end_ts=end_ts,
            edge_threshold=0.05,
            slippage_bps=100,
            max_position_size=10.0,
        )
        bracket_results.append(
            {
                "bracket_low": bracket[0],
                "bracket_high": bracket[1],
                "fair_value": feature_rows[0]["fair_value"] if feature_rows else None,
                "price_points": len(feature_rows),
                "trade_count": replay_result["summary"]["trade_count"],
                "window_results": window_results,
                "feature_rows": feature_rows[:5],
                "trades": replay_result["trades"],
            }
        )
        backtest_rows.extend(replay_result["trades"])

    summary = _summarize_trades(backtest_rows)
    sensitivity = _run_sensitivity_grid(aggregated_features)
    report_lines = [
        "# 首轮弱验证回放结果",
        "",
        f"- 事件 ID：`{event_id}`",
        f"- tracking ID：`{tracking_id}`",
        f"- 使用总推文数（弱标签）：`{total_tweets}`",
        f"- 选取高流动 bracket 数：`{len(bracket_results)}`",
        f"- 总交易次数：`{summary['trade_count']}`",
        f"- 总收益（名义）：`{summary['total_pnl']:.4f}`",
        f"- 最大回撤（名义）：`{summary['max_drawdown']:.4f}`",
        "",
        "## 重要说明",
        "- 本结果使用了 tracking 总推文作为弱标签公允值，不是逐推文事件强验证。",
        "- 当前版本已接入 5m/15m/1h/6h proxy tweet windows，但 proxy tweet 仍由 daily 摘要展开，不等同逐条历史时间线。",
        "- 本结果仅用于检验市场侧数据链路与高流动区间回放框架是否可运行。",
        "",
        "## 参数敏感性（聚合高流动 bracket）",
    ]
    for row in sensitivity:
        report_lines.append(
            f"- edge={row['edge_threshold']:.2f}, slippage_bps={row['slippage_bps']}: 交易 {row['trade_count']}，总收益 {row['total_pnl']:.4f}"
        )

    report_lines.extend(
        [
            "",
        "## 分 bracket 结果",
        ]
    )
    for result in bracket_results:
        report_lines.append(
            f"- `{result['bracket_low']}-{result['bracket_high']}`: 价格点 {result['price_points']}，回放交易 {result['trade_count']}，弱标签公允值 {result['fair_value']:.3f}"
        )
        windows = result["window_results"]
        report_lines.append(
            f"  窗口分层：全窗口({windows['all']['trade_count']}) / 末2h({windows['last_2h']['trade_count']}) / 末1h({windows['last_1h']['trade_count']})"
        )

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"2026-03-27-event-{event_id}-weak-validation.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    details_path = reports_dir / f"2026-03-27-event-{event_id}-weak-validation.json"
    details_path.write_text(
        json.dumps(
            {
                "event_id": event_id,
                "tracking_id": tracking_id,
                "feature_mode": "proxy_tweet_windows",
                "total_tweets": total_tweets,
                "summary": summary,
                "sensitivity": sensitivity,
                "brackets": bracket_results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report_path


def _run_sensitivity_grid(feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not feature_rows:
        return []
    grid = [
        (0.03, 50),
        (0.05, 100),
        (0.08, 150),
    ]
    results: list[dict[str, Any]] = []
    for edge_threshold, slippage_bps in grid:
        replay_result = replay_strategy(
            feature_rows=feature_rows,
            edge_threshold=edge_threshold,
            slippage_bps=slippage_bps,
            max_position_size=10.0,
        )
        summary = _summarize_trades(replay_result["trades"])
        results.append(
            {
                "edge_threshold": edge_threshold,
                "slippage_bps": slippage_bps,
                "trade_count": summary["trade_count"],
                "total_pnl": summary["total_pnl"],
                "max_drawdown": summary["max_drawdown"],
            }
        )
    return results


def _run_window_replays(
    feature_rows: list[dict[str, Any]],
    end_ts: float,
    edge_threshold: float,
    slippage_bps: int,
    max_position_size: float,
) -> dict[str, dict[str, Any]]:
    all_result = replay_strategy(
        feature_rows=feature_rows,
        edge_threshold=edge_threshold,
        slippage_bps=slippage_bps,
        max_position_size=max_position_size,
    )
    last_2h_rows = [row for row in feature_rows if _parse_iso_to_ts(row["timestamp"]) >= end_ts - 7200]
    last_1h_rows = [row for row in feature_rows if _parse_iso_to_ts(row["timestamp"]) >= end_ts - 3600]
    last_2h_result = replay_strategy(
        feature_rows=last_2h_rows,
        edge_threshold=edge_threshold,
        slippage_bps=slippage_bps,
        max_position_size=max_position_size,
    )
    last_1h_result = replay_strategy(
        feature_rows=last_1h_rows,
        edge_threshold=edge_threshold,
        slippage_bps=slippage_bps,
        max_position_size=max_position_size,
    )
    return {
        "all": _summarize_trades(all_result["trades"]),
        "last_2h": _summarize_trades(last_2h_result["trades"]),
        "last_1h": _summarize_trades(last_1h_result["trades"]),
    }


def _top_liquid_brackets(trades: list[dict[str, Any]], top_n: int) -> list[tuple[int, int | None]]:
    counter: Counter[tuple[int, int | None]] = Counter()
    for trade in trades:
        low = trade.get("bracket_low")
        high = trade.get("bracket_high")
        if low is None:
            continue
        counter[(int(low), int(high) if high is not None else None)] += 1
    return [item[0] for item in counter.most_common(top_n)]


def _weak_fair_value(bracket_low: int, bracket_high: int | None, total_tweets: int) -> float:
    if bracket_high is None:
        return 0.02
    if bracket_low <= total_tweets <= bracket_high:
        return 0.98
    distance = min(abs(total_tweets - bracket_low), abs(total_tweets - bracket_high))
    if distance <= 20:
        return 0.25
    if distance <= 40:
        return 0.10
    return 0.02


def _build_proxy_feature_rows(
    tweet_rows: list[dict[str, Any]],
    yes_price_rows: list[dict[str, Any]],
    bracket_low: int,
    bracket_high: int | None,
    end_date: str | None,
    fallback_total_tweets: int,
) -> list[dict[str, Any]]:
    if not yes_price_rows:
        return []
    market_close_at = end_date or _to_iso(yes_price_rows[-1]["timestamp"])
    price_inputs = [
        {
            "observed_at": _to_iso(row["timestamp"]),
            "market_close_at": market_close_at,
            "price_yes": float(row["price"]),
            "price_no": 1.0 - float(row["price"]),
        }
        for row in yes_price_rows
    ]
    features = build_feature_rows(tweet_rows=tweet_rows, price_rows=price_inputs)
    feature_rows: list[dict[str, Any]] = []
    for feature in features:
        proxy_total = _project_proxy_total(feature, fallback_total_tweets=fallback_total_tweets)
        feature_rows.append(
            {
                "timestamp": feature["observed_at"],
                "market_mid": feature["market_mid"],
                "fair_value": _weak_fair_value(
                    bracket_low=bracket_low,
                    bracket_high=bracket_high,
                    total_tweets=proxy_total,
                ),
                "tweets_total": feature["tweets_total"],
                "tweet_delta_5m": feature["tweet_delta_5m"],
                "tweet_delta_15m": feature["tweet_delta_15m"],
                "tweet_delta_1h": feature["tweet_delta_1h"],
                "tweet_delta_6h": feature["tweet_delta_6h"],
                "proxy_total_tweets": proxy_total,
            }
        )
    return feature_rows


def _project_proxy_total(feature_row: dict[str, Any], fallback_total_tweets: int) -> int:
    observed_total = int(feature_row.get("tweets_total") or 0)
    burst_component = max(
        int(feature_row.get("tweet_delta_15m") or 0) * 4,
        int(feature_row.get("tweet_delta_1h") or 0),
    )
    projected = max(observed_total + burst_component, fallback_total_tweets)
    return projected


def _expand_daily_summary_to_proxy_tweets(daily_counts: Any) -> list[dict[str, str]]:
    proxy_rows: list[dict[str, str]] = []
    if isinstance(daily_counts, dict):
        iterable = [(date_str, count_value, 86400) for date_str, count_value in sorted(daily_counts.items())]
    elif isinstance(daily_counts, list):
        iterable = [
            (str(item.get("date")), item.get("count"), 3600)
            for item in daily_counts
            if isinstance(item, dict) and item.get("date") is not None
        ]
    else:
        iterable = []

    for date_str, count_value, bucket_span_seconds in iterable:
        try:
            count = int(count_value)
            base_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if base_dt.tzinfo is None:
            base_dt = base_dt.replace(tzinfo=UTC)
        if count <= 0:
            continue
        for index in range(count):
            second_offset = int(index * bucket_span_seconds / count)
            posted_at = base_dt.timestamp() + second_offset
            proxy_rows.append(
                {
                    "tweet_id": f"{date_str}-{index}",
                    "posted_at": _to_iso(posted_at),
                }
            )
    return proxy_rows


def _summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in trades:
        pnl = (trade["exit_price"] - trade["entry_price"]) * trade["size"]
        total += pnl
        peak = max(peak, total)
        max_drawdown = max(max_drawdown, peak - total)
    return {"trade_count": len(trades), "total_pnl": total, "max_drawdown": max_drawdown}


def _to_iso(ts: int | float) -> str:
    return datetime.fromtimestamp(float(ts), tz=UTC).isoformat().replace("+00:00", "Z")


def _parse_iso_to_ts(value: str | None) -> float:
    if not value:
        return 0.0
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
