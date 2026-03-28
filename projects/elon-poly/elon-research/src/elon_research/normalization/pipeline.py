import json
from pathlib import Path
from typing import Any

from elon_research.config import Settings
from elon_research.normalization.markets import _parse_bracket


def normalize_snapshots(settings: Settings, event_id: int, tracking_id: str) -> dict[str, Path]:
    """将真实 raw snapshot 标准化为研究用中间表。"""
    raw_polymarket_path = settings.raw_dir / "polymarket" / f"event_{event_id}.json"
    raw_tweets_path = settings.raw_dir / "tweets" / f"tracking_{tracking_id}.json"
    polymarket_payload = _read_json(raw_polymarket_path)
    tweets_payload = _read_json(raw_tweets_path)

    markets_rows = _build_markets_rows(polymarket_payload.get("markets", []))
    market_lookup = {(row["market_slug"], row["outcome"]): row for row in markets_rows}
    token_lookup = {row["token_id"]: row for row in markets_rows if row["token_id"]}
    trades_rows = _build_trades_rows(polymarket_payload.get("trades", []), token_lookup)
    subgraph_trade_rows = _build_subgraph_trade_rows(
        raw_subgraph_dir=settings.raw_dir / "polymarket_subgraph",
        event_id=event_id,
        token_lookup=token_lookup,
    )
    prices_rows = _build_prices_rows(polymarket_payload.get("price_history", {}), market_lookup)
    tweet_rows = _build_tweet_rows(tweets_payload)

    settings.normalized_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "markets": settings.normalized_dir / f"event_{event_id}_markets.json",
        "trades": settings.normalized_dir / f"event_{event_id}_trades.json",
        "subgraph_trades": settings.normalized_dir / f"event_{event_id}_subgraph_trades.json",
        "prices": settings.normalized_dir / f"event_{event_id}_prices.json",
        "tweets": settings.normalized_dir / f"tracking_{tracking_id}_summary.json",
    }
    _write_json(outputs["markets"], markets_rows)
    _write_json(outputs["trades"], trades_rows)
    _write_json(outputs["subgraph_trades"], subgraph_trade_rows)
    _write_json(outputs["prices"], prices_rows)
    _write_json(outputs["tweets"], tweet_rows)
    return outputs


def _build_markets_rows(markets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for market in markets:
        bracket = _parse_bracket(market.get("groupItemTitle", "0-0"))
        outcomes = _as_list(market.get("outcomes"))
        token_ids = _as_list(market.get("clobTokenIds"))
        for index, outcome in enumerate(outcomes):
            token_id = token_ids[index] if index < len(token_ids) else None
            rows.append(
                {
                    "event_slug": _event_slug_from_market_slug(market.get("slug", "")),
                    "market_slug": market.get("slug"),
                    "condition_id": market.get("conditionId"),
                    "outcome": outcome,
                    "token_id": token_id,
                    "bracket_label": market.get("groupItemTitle"),
                    "bracket_low": bracket.bracket_low,
                    "bracket_high": bracket.bracket_high,
                    "start_date": market.get("startDate"),
                    "end_date": market.get("endDate"),
                    "active": market.get("active"),
                    "closed": market.get("closed"),
                }
            )
    return rows


def _build_trades_rows(trades: list[dict[str, Any]], token_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trade in trades:
        token_id = trade.get("asset")
        matched = token_lookup.get(token_id, {})
        rows.append(
            {
                "timestamp": trade.get("timestamp"),
                "market_slug": trade.get("slug"),
                "event_slug": trade.get("eventSlug"),
                "token_id": token_id,
                "outcome": trade.get("outcome"),
                "side": trade.get("side"),
                "price": trade.get("price"),
                "size": trade.get("size"),
                "transaction_hash": trade.get("transactionHash"),
                "condition_id": trade.get("conditionId"),
                "bracket_low": matched.get("bracket_low"),
                "bracket_high": matched.get("bracket_high"),
            }
        )
    return rows


def _build_prices_rows(
    price_history: dict[str, list[dict[str, Any]]], market_lookup: dict[tuple[str, str], dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, history in price_history.items():
        if ":" not in key:
            continue
        market_slug, outcome = key.rsplit(":", 1)
        matched = market_lookup.get((market_slug, outcome), {})
        for point in history:
            rows.append(
                {
                    "timestamp": point.get("t"),
                    "price": point.get("p"),
                    "market_slug": market_slug,
                    "outcome": outcome,
                    "token_id": matched.get("token_id"),
                    "bracket_low": matched.get("bracket_low"),
                    "bracket_high": matched.get("bracket_high"),
                }
            )
    return rows


def _build_subgraph_trade_rows(
    raw_subgraph_dir: Path,
    event_id: int,
    token_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(raw_subgraph_dir.glob(f"event_{event_id}_market_*.json")):
        payload = _read_json(path)
        market_slug = payload.get("market_slug")
        for event in payload.get("events", []):
            maker_token = str(event.get("makerAssetId") or "")
            taker_token = str(event.get("takerAssetId") or "")
            matched = token_lookup.get(maker_token) or token_lookup.get(taker_token) or {}
            rows.append(
                {
                    "timestamp": int(event.get("timestamp")),
                    "market_slug": market_slug,
                    "token_id": matched.get("token_id"),
                    "transaction_hash": event.get("transactionHash"),
                    "maker_asset_id": maker_token,
                    "taker_asset_id": taker_token,
                    "bracket_low": matched.get("bracket_low"),
                    "bracket_high": matched.get("bracket_high"),
                }
            )
    return rows


def _build_tweet_rows(payload: dict[str, Any]) -> dict[str, Any]:
    tracking = payload.get("tracking", {}).get("data", {})
    stats = tracking.get("stats", {})
    return {
        "tracking_id": tracking.get("id"),
        "start_date": tracking.get("startDate"),
        "end_date": tracking.get("endDate"),
        "total": stats.get("total"),
        "days_elapsed": stats.get("daysElapsed"),
        "daily": stats.get("daily", {}),
        "pace": stats.get("pace"),
        "provenance": payload.get("provenance", {}),
    }


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError:
                parsed = []
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        return [segment.strip() for segment in cleaned.split(",") if segment.strip()]
    return []


def _event_slug_from_market_slug(slug: str) -> str:
    parts = slug.split("-")
    if len(parts) < 3:
        return slug
    return "-".join(parts[:-2])


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
