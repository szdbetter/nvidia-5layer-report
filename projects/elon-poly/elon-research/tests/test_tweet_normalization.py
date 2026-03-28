from elon_research.normalization.tweets import normalize_tweet_rows


def test_normalize_tweet_rows_builds_running_count() -> None:
    rows = [
        {"tweet_id": "t2", "posted_at": "2026-03-20T02:00:00Z"},
        {"tweet_id": "t1", "posted_at": "2026-03-20T01:00:00Z"},
    ]

    normalized = normalize_tweet_rows(rows)

    assert normalized[0]["tweet_id"] == "t1"
    assert normalized[0]["running_count"] == 1
    assert normalized[1]["tweet_id"] == "t2"
    assert normalized[1]["running_count"] == 2


def test_normalize_tweet_rows_orders_by_actual_timestamp_with_offset() -> None:
    rows = [
        {"tweet_id": "t_offset", "posted_at": "2026-03-20T01:30:00-05:00"},
        {"tweet_id": "t_utc", "posted_at": "2026-03-20T03:00:00Z"},
    ]

    normalized = normalize_tweet_rows(rows)

    assert normalized[0]["tweet_id"] == "t_utc"
    assert normalized[0]["running_count"] == 1
    assert normalized[1]["tweet_id"] == "t_offset"
    assert normalized[1]["running_count"] == 2
