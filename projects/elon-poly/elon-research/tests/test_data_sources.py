import json
from pathlib import Path

from elon_research.config import Settings
from elon_research.data_sources import polymarket, tweets
from elon_research.data_sources import polymarket_subgraph


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class FakeHttpErrorResponse(FakeResponse):
    status_code = 400


class FakeHttpError(Exception):
    def __init__(self, response):
        super().__init__("http error")
        self.response = response


def test_ingest_polymarket_snapshot_writes_real_event_payload(monkeypatch, tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)

    def fake_get(url, params=None, timeout=30):
        if url.endswith("/events/278377"):
            return FakeResponse(
                {
                    "id": "278377",
                    "startDate": "2026-03-20T16:00:00Z",
                    "endDate": "2026-03-27T16:00:00Z",
                    "markets": [
                        {
                            "slug": "elon-280-299",
                            "outcomes": ["Yes", "No"],
                            "clobTokenIds": ["yes-token", "no-token"],
                        }
                    ],
                }
            )
        if url.endswith("/trades"):
            offset = params.get("offset", 0)
            if offset == 0:
                return FakeResponse(
                    [
                        {
                            "slug": "elon-280-299",
                            "price": 0.12,
                            "timestamp": 1774625897,
                        }
                    ]
                )
            return FakeResponse([])
        if url.endswith("/prices-history"):
            return FakeResponse({"history": [{"t": 1773723647, "p": 0.105}]})
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(polymarket.requests, "get", fake_get)
    monkeypatch.setattr(polymarket, "_utc_now_iso", lambda: "2026-03-27T16:00:00Z")

    path = polymarket.ingest_polymarket_snapshot(settings, event_id=278377)

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = json.loads(Path(path).with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert payload["event"]["id"] == "278377"
    assert len(payload["trades"]) == 1
    assert payload["price_history"]["elon-280-299:Yes"][0]["p"] == 0.105
    assert meta["coverage_start"] == "2026-03-20T16:00:00Z"
    assert meta["fetched_at"] == "2026-03-27T16:00:00Z"


def test_ingest_tweet_snapshot_writes_tracking_and_reference_history(monkeypatch, tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)
    historical_file = tmp_path / "weekly_history.json"
    historical_file.write_text(json.dumps([{"week": "2025-11-14", "total": 165}]), encoding="utf-8")

    def fake_get(url, params=None, timeout=30):
        return FakeResponse(
            {
                "data": {
                    "id": "tracking-id",
                    "startDate": "2026-03-20T16:00:00.000Z",
                    "endDate": "2026-03-27T15:59:59.000Z",
                }
            }
        )

    monkeypatch.setattr(tweets.requests, "get", fake_get)
    monkeypatch.setattr(tweets, "_utc_now_iso", lambda: "2026-03-27T16:00:00Z")

    path = tweets.ingest_tweet_snapshot(settings, tracking_id="tracking-id", historical_file=historical_file)

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = json.loads(Path(path).with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert payload["tracking"]["data"]["id"] == "tracking-id"
    assert payload["historical_reference"]["items"][0]["total"] == 165
    assert payload["provenance"]["historical_is_reference_only"] is True
    assert meta["coverage_start"] == "2026-03-20T16:00:00.000Z"
    assert meta["fetched_at"] == "2026-03-27T16:00:00Z"


def test_fetch_event_trades_stops_cleanly_on_tail_400(monkeypatch) -> None:
    monkeypatch.setattr(polymarket, "TRADES_PAGE_SIZE", 1)

    def fake_fetch_json(url, params=None):
        offset = params["offset"]
        if offset == 0:
            return [{"price": 0.1}]
        if offset == polymarket.TRADES_PAGE_SIZE:
            return [{"price": 0.2}]
        raise FakeHttpError(FakeHttpErrorResponse({}))

    monkeypatch.setattr(polymarket, "_fetch_json", fake_fetch_json)
    monkeypatch.setattr(polymarket.requests, "HTTPError", FakeHttpError)

    trades = polymarket._fetch_event_trades(event_id=278377)

    assert trades == [{"price": 0.1}, {"price": 0.2}]


def test_fetch_order_filled_events_by_asset_window(monkeypatch) -> None:
    captured = {}

    def fake_post(url, json=None, timeout=30):
        captured["url"] = url
        captured["query"] = json["query"]
        return FakeResponse(
            {
                "data": {
                    "orderFilledEvents": [
                        {
                            "id": "evt-1",
                            "timestamp": "1774560015",
                            "makerAssetId": "token-a",
                            "takerAssetId": "0",
                            "transactionHash": "0xabc",
                        }
                    ]
                }
            }
        )

    monkeypatch.setattr(polymarket_subgraph.requests, "post", fake_post)

    events = polymarket_subgraph.fetch_order_filled_events_by_asset_window(
        asset_id="token-a",
        start_ts=1774560000,
        end_ts=1774646400,
        side="maker",
        first=5,
    )

    assert len(events) == 1
    assert events[0]["transactionHash"] == "0xabc"
    assert "makerAssetId: \"token-a\"" in captured["query"]
    assert "timestamp_gte: 1774560000" in captured["query"]


def test_fetch_order_filled_events_over_windows_combines_results(monkeypatch) -> None:
    calls = []

    def fake_fetch(asset_id, start_ts, end_ts, side="maker", first=100):
        calls.append((asset_id, start_ts, end_ts, side, first))
        return [{"transactionHash": f"{start_ts}", "timestamp": str(start_ts)}]

    monkeypatch.setattr(
        polymarket_subgraph,
        "fetch_order_filled_events_by_asset_window",
        fake_fetch,
    )

    events = polymarket_subgraph.fetch_order_filled_events_over_windows(
        asset_id="token-a",
        windows=[(100, 200), (200, 300)],
        side="taker",
        first=50,
    )

    assert len(events) == 2
    assert calls == [
        ("token-a", 100, 200, "taker", 50),
        ("token-a", 200, 300, "taker", 50),
    ]


def test_fetch_unique_order_filled_events_for_asset_combines_sides(monkeypatch) -> None:
    def fake_fetch(asset_id, windows, side="maker", first=100):
        if side == "maker":
            return [
                {"transactionHash": "0x1", "timestamp": "100"},
                {"transactionHash": "0x2", "timestamp": "110"},
            ]
        return [
            {"transactionHash": "0x2", "timestamp": "110"},
            {"transactionHash": "0x3", "timestamp": "120"},
        ]

    monkeypatch.setattr(
        polymarket_subgraph,
        "fetch_order_filled_events_over_windows",
        fake_fetch,
    )

    events = polymarket_subgraph.fetch_unique_order_filled_events_for_asset(
        asset_id="token-a",
        windows=[(100, 200)],
        first=50,
    )

    assert [event["transactionHash"] for event in events] == ["0x1", "0x2", "0x3"]


def test_fetch_unique_order_filled_events_for_market_combines_tokens(monkeypatch) -> None:
    calls = []

    def fake_fetch(asset_id, windows, first=100):
        calls.append((asset_id, windows, first))
        return [{"transactionHash": f"tx-{asset_id}"}]

    monkeypatch.setattr(
        polymarket_subgraph,
        "fetch_unique_order_filled_events_for_asset",
        fake_fetch,
    )

    events = polymarket_subgraph.fetch_unique_order_filled_events_for_market(
        market={"clobTokenIds": '["yes-token","no-token"]'},
        windows=[(100, 200)],
        first=50,
    )

    assert calls == [
        ("yes-token", [(100, 200)], 50),
        ("no-token", [(100, 200)], 50),
    ]
    assert [event["transactionHash"] for event in events] == ["tx-no-token", "tx-yes-token"]
