from elon_research.features.build import build_feature_rows


def test_build_feature_rows_generates_research_features() -> None:
    tweet_rows = [
        {"tweet_id": "t1", "posted_at": "2026-03-20T19:30:00Z"},
        {"tweet_id": "t2", "posted_at": "2026-03-20T20:15:00Z"},
        {"tweet_id": "t3", "posted_at": "2026-03-20T21:00:00Z"},
    ]
    price_rows = [
        {
            "observed_at": "2026-03-20T20:30:00Z",
            "market_close_at": "2026-03-20T22:00:00Z",
            "price_yes": 0.62,
            "price_no": 0.38,
        },
        {
            "observed_at": "2026-03-20T21:30:00Z",
            "market_close_at": "2026-03-20T22:00:00Z",
            "price_yes": 0.55,
            "price_no": 0.45,
        },
    ]

    feature_rows = build_feature_rows(tweet_rows=tweet_rows, price_rows=price_rows)

    assert feature_rows == [
        {
            "observed_at": "2026-03-20T20:30:00Z",
            "tweets_total": 2,
            "tweet_delta_5m": 0,
            "tweet_delta_15m": 1,
            "tweet_delta_1h": 2,
            "tweet_delta_6h": 2,
            "minutes_to_close": 90,
            "market_mid": 0.5,
        },
        {
            "observed_at": "2026-03-20T21:30:00Z",
            "tweets_total": 3,
            "tweet_delta_5m": 0,
            "tweet_delta_15m": 0,
            "tweet_delta_1h": 1,
            "tweet_delta_6h": 3,
            "minutes_to_close": 30,
            "market_mid": 0.5,
        },
    ]


def test_build_feature_rows_parses_iso8601_offsets() -> None:
    tweet_rows = [
        {"tweet_id": "t1", "posted_at": "2026-03-20T15:40:00-05:00"},
        {"tweet_id": "t2", "posted_at": "2026-03-20T16:10:00-05:00"},
    ]
    price_rows = [
        {
            "observed_at": "2026-03-20T21:30:00Z",
            "market_close_at": "2026-03-20T22:00:00Z",
            "price_yes": 0.7,
            "price_no": 0.3,
        }
    ]

    feature_rows = build_feature_rows(tweet_rows=tweet_rows, price_rows=price_rows)

    assert feature_rows == [
        {
            "observed_at": "2026-03-20T21:30:00Z",
            "tweets_total": 2,
            "tweet_delta_5m": 0,
            "tweet_delta_15m": 0,
            "tweet_delta_1h": 2,
            "tweet_delta_6h": 2,
            "minutes_to_close": 30,
            "market_mid": 0.5,
        }
    ]


def test_build_feature_rows_normalizes_naive_and_aware_timestamps() -> None:
    tweet_rows = [
        {"tweet_id": "t1", "posted_at": "2026-03-20T20:45:00"},
        {"tweet_id": "t2", "posted_at": "2026-03-20T21:15:00Z"},
    ]
    price_rows = [
        {
            "observed_at": "2026-03-20T21:30:00+00:00",
            "market_close_at": "2026-03-20T22:00:00",
            "price_yes": 0.6,
            "price_no": 0.4,
        }
    ]

    feature_rows = build_feature_rows(tweet_rows=tweet_rows, price_rows=price_rows)

    assert feature_rows == [
        {
            "observed_at": "2026-03-20T21:30:00+00:00",
            "tweets_total": 2,
            "tweet_delta_5m": 0,
            "tweet_delta_15m": 1,
            "tweet_delta_1h": 2,
            "tweet_delta_6h": 2,
            "minutes_to_close": 30,
            "market_mid": 0.5,
        }
    ]
