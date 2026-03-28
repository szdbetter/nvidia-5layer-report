from datetime import UTC, datetime


def _parse_iso8601(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def build_feature_rows(tweet_rows: list[dict], price_rows: list[dict]) -> list[dict]:
    ordered_tweets = sorted(tweet_rows, key=lambda row: _parse_iso8601(row["posted_at"]))
    tweet_times = [_parse_iso8601(row["posted_at"]) for row in ordered_tweets]
    feature_rows = []

    for price_row in sorted(price_rows, key=lambda row: _parse_iso8601(row["observed_at"])):
        observed_at = _parse_iso8601(price_row["observed_at"])
        market_close_at = _parse_iso8601(price_row["market_close_at"])
        observed_ts = observed_at.timestamp()
        tweets_total = sum(1 for tweet_time in tweet_times if tweet_time <= observed_at)
        window_start_5m = observed_ts - 300
        window_start_15m = observed_ts - 900
        window_start_1h = observed_ts - 3600
        window_start_6h = observed_ts - 21600
        tweet_delta_5m = sum(
            1 for tweet_time in tweet_times if window_start_5m <= tweet_time.timestamp() <= observed_ts
        )
        tweet_delta_15m = sum(
            1 for tweet_time in tweet_times if window_start_15m <= tweet_time.timestamp() <= observed_ts
        )
        tweet_delta_1h = sum(
            1 for tweet_time in tweet_times if window_start_1h <= tweet_time.timestamp() <= observed_ts
        )
        tweet_delta_6h = sum(
            1 for tweet_time in tweet_times if window_start_6h <= tweet_time.timestamp() <= observed_ts
        )
        minutes_to_close = int((market_close_at - observed_at).total_seconds() // 60)
        market_mid = (price_row["price_yes"] + price_row["price_no"]) / 2

        feature_rows.append(
            {
                "observed_at": price_row["observed_at"],
                "tweets_total": tweets_total,
                "tweet_delta_5m": tweet_delta_5m,
                "tweet_delta_15m": tweet_delta_15m,
                "tweet_delta_1h": tweet_delta_1h,
                "tweet_delta_6h": tweet_delta_6h,
                "minutes_to_close": minutes_to_close,
                "market_mid": market_mid,
            }
        )

    return feature_rows
