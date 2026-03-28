import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from elon_research.config import Settings
from elon_research.data_sources.storage import RawSnapshotWriter

ORDERBOOK_SUBGRAPH_URL = (
    "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn"
)


def fetch_order_filled_events_by_asset_window(
    asset_id: str,
    start_ts: int,
    end_ts: int,
    side: str = "maker",
    first: int = 100,
) -> list[dict[str, Any]]:
    field_name = "makerAssetId" if side == "maker" else "takerAssetId"
    query = f"""
query {{
  orderFilledEvents(
    first: {first},
    where: {{
      {field_name}: "{asset_id}",
      timestamp_gte: {start_ts},
      timestamp_lt: {end_ts}
    }},
    orderBy: timestamp,
    orderDirection: asc
  ) {{
    id
    timestamp
    makerAssetId
    takerAssetId
    transactionHash
  }}
}}
""".strip()
    response = requests.post(
        ORDERBOOK_SUBGRAPH_URL,
        json={"query": query},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(str(payload["errors"]))
    return payload.get("data", {}).get("orderFilledEvents", [])


def fetch_order_filled_events_over_windows(
    asset_id: str,
    windows: list[tuple[int, int]],
    side: str = "maker",
    first: int = 100,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for start_ts, end_ts in windows:
        events.extend(
            fetch_order_filled_events_by_asset_window(
                asset_id=asset_id,
                start_ts=start_ts,
                end_ts=end_ts,
                side=side,
                first=first,
            )
        )
    return events


def fetch_unique_order_filled_events_for_asset(
    asset_id: str,
    windows: list[tuple[int, int]],
    first: int = 100,
) -> list[dict[str, Any]]:
    combined = fetch_order_filled_events_over_windows(
        asset_id=asset_id,
        windows=windows,
        side="maker",
        first=first,
    )
    combined.extend(
        fetch_order_filled_events_over_windows(
            asset_id=asset_id,
            windows=windows,
            side="taker",
            first=first,
        )
    )
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in sorted(combined, key=lambda row: (row.get("timestamp", ""), row.get("transactionHash", ""))):
        tx = str(event.get("transactionHash"))
        if tx in seen:
            continue
        seen.add(tx)
        deduped.append(event)
    return deduped


def fetch_unique_order_filled_events_for_market(
    market: dict[str, Any],
    windows: list[tuple[int, int]],
    first: int = 100,
) -> list[dict[str, Any]]:
    token_ids = market.get("clobTokenIds", [])
    if isinstance(token_ids, str):
        token_ids = json.loads(token_ids)
    combined: list[dict[str, Any]] = []
    for token_id in token_ids:
        combined.extend(
            fetch_unique_order_filled_events_for_asset(
                asset_id=str(token_id),
                windows=windows,
                first=first,
            )
        )
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in sorted(combined, key=lambda row: (row.get("timestamp", ""), row.get("transactionHash", ""))):
        tx = str(event.get("transactionHash"))
        if tx in seen:
            continue
        seen.add(tx)
        deduped.append(event)
    return deduped


def ingest_subgraph_market_snapshot(
    settings: Settings,
    event_id: int,
    bracket_label: str,
    window_days: int = 7,
    first_per_window: int = 200,
) -> str:
    raw_event_path = settings.raw_dir / "polymarket" / f"event_{event_id}.json"
    event_payload = json.loads(raw_event_path.read_text(encoding="utf-8"))
    market = next(m for m in event_payload["markets"] if m.get("groupItemTitle") == bracket_label)
    end_dt = datetime.fromisoformat(market["endDate"].replace("Z", "+00:00"))
    start_dt = end_dt.timestamp() - window_days * 86400
    windows = [
        (int(start_dt) + i * 86400, int(start_dt) + (i + 1) * 86400)
        for i in range(window_days)
    ]
    events = fetch_unique_order_filled_events_for_market(market=market, windows=windows, first=first_per_window)
    writer = RawSnapshotWriter(settings)
    payload_path = writer.write_json(
        source_name="polymarket_subgraph",
        dataset_name=f"event_{event_id}_market_{bracket_label}",
        payload={
            "event_id": event_id,
            "market_slug": market["slug"],
            "bracket_label": bracket_label,
            "events": events,
        },
        coverage_start=datetime.fromtimestamp(int(start_dt), tz=UTC).isoformat().replace("+00:00", "Z"),
        coverage_end=market["endDate"],
        fetched_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    return str(payload_path)


def ingest_subgraph_event_batch(
    settings: Settings,
    event_id: int,
    top_brackets: int = 3,
    window_days: int = 7,
    first_per_window: int = 200,
) -> list[str]:
    raw_event_path = settings.raw_dir / "polymarket" / f"event_{event_id}.json"
    event_payload = json.loads(raw_event_path.read_text(encoding="utf-8"))
    trades = event_payload.get("trades", [])
    counts: dict[str, int] = {}
    for trade in trades:
        slug = str(trade.get("slug") or "")
        if not slug:
            continue
        counts[slug] = counts.get(slug, 0) + 1
    selected_markets = []
    seen_labels: set[str] = set()
    for market in sorted(
        event_payload.get("markets", []),
        key=lambda market: counts.get(str(market.get("slug") or ""), 0),
        reverse=True,
    ):
        label = str(market.get("groupItemTitle") or "")
        if not label or label in seen_labels:
            continue
        selected_markets.append(label)
        seen_labels.add(label)
        if len(selected_markets) >= top_brackets:
            break
    return [
        ingest_subgraph_market_snapshot(
            settings=settings,
            event_id=event_id,
            bracket_label=label,
            window_days=window_days,
            first_per_window=first_per_window,
        )
        for label in selected_markets
    ]
