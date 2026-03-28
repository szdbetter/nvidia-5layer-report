import json
from pathlib import Path

from elon_research.evaluation.weak_validation import run_weak_validation


def test_run_weak_validation_writes_report_and_json(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    reports_dir = tmp_path / "reports"
    normalized_dir.mkdir(parents=True, exist_ok=True)

    (normalized_dir / "event_278377_markets.json").write_text(
        json.dumps(
            [
                {
                    "market_slug": "event-260-279",
                    "outcome": "Yes",
                    "token_id": "yes-1",
                    "bracket_low": 260,
                    "bracket_high": 279,
                }
            ]
        ),
        encoding="utf-8",
    )
    (normalized_dir / "event_278377_trades.json").write_text(
        json.dumps(
            [
                {"bracket_low": 260, "bracket_high": 279},
                {"bracket_low": 260, "bracket_high": 279},
            ]
        ),
        encoding="utf-8",
    )
    (normalized_dir / "event_278377_prices.json").write_text(
        json.dumps(
            [
                {
                    "timestamp": 1774625897,
                    "price": 0.10,
                    "market_slug": "event-260-279",
                    "outcome": "Yes",
                    "token_id": "yes-1",
                    "bracket_low": 260,
                    "bracket_high": 279,
                },
                {
                    "timestamp": 1774626997,
                    "price": 0.20,
                    "market_slug": "event-260-279",
                    "outcome": "Yes",
                    "token_id": "yes-1",
                    "bracket_low": 260,
                    "bracket_high": 279,
                },
                {
                    "timestamp": 1774627997,
                    "price": 0.90,
                    "market_slug": "event-260-279",
                    "outcome": "Yes",
                    "token_id": "yes-1",
                    "bracket_low": 260,
                    "bracket_high": 279,
                },
            ]
        ),
        encoding="utf-8",
    )
    (normalized_dir / "tracking_d861bacb-6108-45d6-9a14-47b9e58ea095_summary.json").write_text(
        json.dumps(
            {
                "total": 269,
                "end_date": "2026-03-20T22:00:00Z",
                "daily": {"2026-03-20": 269},
            }
        ),
        encoding="utf-8",
    )

    report_path = run_weak_validation(
        normalized_dir=normalized_dir,
        reports_dir=reports_dir,
        event_id=278377,
        tracking_id="d861bacb-6108-45d6-9a14-47b9e58ea095",
        top_brackets=1,
    )

    details_path = reports_dir / "2026-03-27-event-278377-weak-validation.json"
    assert report_path.exists()
    assert details_path.exists()
    assert "弱验证回放结果" in report_path.read_text(encoding="utf-8")
    assert "参数敏感性" in report_path.read_text(encoding="utf-8")
    details = json.loads(details_path.read_text(encoding="utf-8"))
    assert details["event_id"] == 278377
    assert details["summary"]["trade_count"] >= 0
    assert len(details["sensitivity"]) == 3
    assert "window_results" in details["brackets"][0]
    assert "last_1h" in details["brackets"][0]["window_results"]
    assert details["feature_mode"] == "proxy_tweet_windows"
    assert details["brackets"][0]["feature_rows"][0]["tweet_delta_1h"] >= 0
