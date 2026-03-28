from datetime import datetime


def _parse_posted_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_tweet_rows(rows: list[dict]) -> list[dict]:
    ordered_rows = sorted(rows, key=lambda row: _parse_posted_at(row["posted_at"]))
    normalized = []

    for running_count, row in enumerate(ordered_rows, start=1):
        normalized.append(
            {
                "tweet_id": row["tweet_id"],
                "posted_at": row["posted_at"],
                "running_count": running_count,
            }
        )

    return normalized
