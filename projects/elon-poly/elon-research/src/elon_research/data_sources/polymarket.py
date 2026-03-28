from datetime import UTC, datetime
from typing import Any

import requests

from elon_research.config import Settings
from elon_research.data_sources.storage import RawSnapshotWriter

GAMMA_API_BASE = "https://gamma-api.polymarket.com"
DATA_API_BASE = "https://data-api.polymarket.com"
CLOB_API_BASE = "https://clob.polymarket.com"
DEFAULT_EVENT_ID = 278377
DEFAULT_PRICE_FIDELITY = 60
TRADES_PAGE_SIZE = 500


def ingest_polymarket_snapshot(settings: Settings, event_id: int = DEFAULT_EVENT_ID) -> str:
    """抓取单个 Elon 事件的真实市场、成交与价格历史快照。"""
    writer = RawSnapshotWriter(settings)
    fetched_at = _utc_now_iso()
    event_payload = _fetch_json(f"{GAMMA_API_BASE}/events/{event_id}")
    markets = event_payload.get("markets", [])
    trades = _fetch_event_trades(event_id=event_id)
    price_history = _fetch_event_price_history(markets)
    payload_path = writer.write_json(
        source_name="polymarket",
        dataset_name=f"event_{event_id}",
        payload={
            "event": event_payload,
            "markets": markets,
            "trades": trades,
            "price_history": price_history,
        },
        coverage_start=event_payload.get("startDate", "UNKNOWN"),
        coverage_end=event_payload.get("endDate", "UNKNOWN"),
        fetched_at=fetched_at,
    )
    return str(payload_path)


def _fetch_event_trades(event_id: int) -> list[dict[str, Any]]:
    return _fetch_trades_pages({"eventId": event_id})


def _fetch_trades_pages(query_params: dict[str, Any]) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    offset = 0
    while True:
        try:
            page = _fetch_json(
                f"{DATA_API_BASE}/trades",
                params={**query_params, "limit": TRADES_PAGE_SIZE, "offset": offset},
            )
        except requests.HTTPError as exc:
            response = exc.response
            if response is not None and response.status_code == 400 and offset > 0:
                break
            raise
        if not page:
            break
        trades.extend(page)
        if len(page) < TRADES_PAGE_SIZE:
            break
        offset += len(page)
    return trades


def _fetch_event_price_history(markets: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    history_by_asset: dict[str, list[dict[str, Any]]] = {}
    for market in markets:
        slug = market.get("slug", "")
        outcome_labels = market.get("outcomes")
        token_ids = market.get("clobTokenIds")
        if isinstance(outcome_labels, str):
            outcome_labels = _parse_json_array_string(outcome_labels)
        if isinstance(token_ids, str):
            token_ids = _parse_json_array_string(token_ids)
        if not isinstance(outcome_labels, list) or not isinstance(token_ids, list):
            continue
        for outcome_label, token_id in zip(outcome_labels, token_ids):
            response = _fetch_json(
                f"{CLOB_API_BASE}/prices-history",
                params={"market": token_id, "interval": "max", "fidelity": DEFAULT_PRICE_FIDELITY},
            )
            history_by_asset[f"{slug}:{outcome_label}"] = response.get("history", [])
    return history_by_asset


def _parse_json_array_string(value: str) -> list[str]:
    cleaned = value.strip()
    if not cleaned:
        return []
    if cleaned.startswith("[") and cleaned.endswith("]"):
        import json

        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _fetch_json(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
