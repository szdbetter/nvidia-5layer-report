import json
from pathlib import Path

from elon_research.config import Settings
from elon_research.normalization.pipeline import normalize_snapshots


def test_normalize_snapshots_outputs_research_tables(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)
    raw_polymarket = settings.raw_dir / "polymarket"
    raw_tweets = settings.raw_dir / "tweets"
    raw_polymarket.mkdir(parents=True, exist_ok=True)
    raw_tweets.mkdir(parents=True, exist_ok=True)

    (raw_polymarket / "event_278377.json").write_text(
        json.dumps(
            {
                "markets": [
                    {
                        "slug": "elon-musk-of-tweets-march-20-march-27-280-299",
                        "groupItemTitle": "280-299",
                        "conditionId": "cond-1",
                        "outcomes": ["Yes", "No"],
                        "clobTokenIds": ["yes-token", "no-token"],
                        "startDate": "2026-03-20T16:00:00Z",
                        "endDate": "2026-03-27T16:00:00Z",
                        "active": False,
                        "closed": True,
                    }
                ],
                "trades": [
                    {
                        "timestamp": 1774625897,
                        "slug": "elon-musk-of-tweets-march-20-march-27-280-299",
                        "eventSlug": "elon-musk-of-tweets-march-20-march-27",
                        "asset": "yes-token",
                        "outcome": "Yes",
                        "side": "BUY",
                        "price": 0.12,
                        "size": 10,
                        "transactionHash": "0xabc",
                        "conditionId": "cond-1",
                    }
                ],
                "price_history": {
                    "elon-musk-of-tweets-march-20-march-27-280-299:Yes": [{"t": 1773723647, "p": 0.105}],
                    "elon-musk-of-tweets-march-20-march-27-280-299:No": [{"t": 1773723647, "p": 0.895}],
                },
            }
        ),
        encoding="utf-8",
    )
    (raw_tweets / "tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json").write_text(
        json.dumps(
            {
                "tracking": {
                    "data": {
                        "id": "tracking-id",
                        "startDate": "2026-03-20T16:00:00.000Z",
                        "endDate": "2026-03-27T15:59:59.000Z",
                        "stats": {
                            "total": 269,
                            "daysElapsed": 7,
                            "daily": {"2026-03-20": 7},
                            "pace": 269,
                        },
                    }
                },
                "provenance": {"historical_is_reference_only": True},
            }
        ),
        encoding="utf-8",
    )

    outputs = normalize_snapshots(settings, event_id=278377, tracking_id="d861bacb-6108-45d6-9a14-47b9e58ea095")

    markets = json.loads(outputs["markets"].read_text(encoding="utf-8"))
    trades = json.loads(outputs["trades"].read_text(encoding="utf-8"))
    prices = json.loads(outputs["prices"].read_text(encoding="utf-8"))
    tweets = json.loads(outputs["tweets"].read_text(encoding="utf-8"))

    assert len(markets) == 2
    assert markets[0]["bracket_low"] == 280
    assert markets[0]["token_id"] == "yes-token"
    assert trades[0]["bracket_low"] == 280
    assert prices[0]["token_id"] == "yes-token"
    assert tweets["total"] == 269


def test_normalize_snapshots_outputs_optional_subgraph_trades(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)
    raw_polymarket = settings.raw_dir / "polymarket"
    raw_tweets = settings.raw_dir / "tweets"
    raw_subgraph = settings.raw_dir / "polymarket_subgraph"
    raw_polymarket.mkdir(parents=True, exist_ok=True)
    raw_tweets.mkdir(parents=True, exist_ok=True)
    raw_subgraph.mkdir(parents=True, exist_ok=True)

    (raw_polymarket / "event_278377.json").write_text(
        json.dumps(
            {
                "markets": [
                    {
                        "slug": "elon-musk-of-tweets-march-20-march-27-280-299",
                        "groupItemTitle": "280-299",
                        "conditionId": "cond-1",
                        "outcomes": ["Yes", "No"],
                        "clobTokenIds": ["yes-token", "no-token"],
                        "startDate": "2026-03-20T16:00:00Z",
                        "endDate": "2026-03-27T16:00:00Z",
                        "active": False,
                        "closed": True,
                    }
                ],
                "trades": [],
                "price_history": {},
            }
        ),
        encoding="utf-8",
    )
    (raw_tweets / "tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json").write_text(
        json.dumps({"tracking": {"data": {"stats": {}}}, "provenance": {}}),
        encoding="utf-8",
    )
    (raw_subgraph / "event_278377_market_280-299.json").write_text(
        json.dumps(
            {
                "market_slug": "elon-musk-of-tweets-march-20-march-27-280-299",
                "events": [
                    {
                        "timestamp": "1774560015",
                        "transactionHash": "0xsubgraph",
                        "makerAssetId": "yes-token",
                        "takerAssetId": "0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    outputs = normalize_snapshots(settings, event_id=278377, tracking_id="d861bacb-6108-45d6-9a14-47b9e58ea095")

    subgraph_trades = json.loads(outputs["subgraph_trades"].read_text(encoding="utf-8"))
    assert subgraph_trades[0]["market_slug"] == "elon-musk-of-tweets-march-20-march-27-280-299"
    assert subgraph_trades[0]["bracket_low"] == 280
    assert subgraph_trades[0]["transaction_hash"] == "0xsubgraph"
