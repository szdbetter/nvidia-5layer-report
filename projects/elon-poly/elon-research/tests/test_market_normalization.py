from elon_research.normalization.markets import normalize_market_rows


def test_normalize_market_rows_extracts_bracket_bounds() -> None:
    rows = [
        {"market_slug": "elon-week-1", "groupItemTitle": "280-299", "token_id": "abc"},
        {"market_slug": "elon-week-1", "groupItemTitle": "600+", "token_id": "xyz"},
    ]

    normalized = normalize_market_rows(rows)

    assert normalized[0]["bracket_low"] == 280
    assert normalized[0]["bracket_high"] == 299
    assert normalized[1]["bracket_low"] == 600
    assert normalized[1]["bracket_high"] is None


def test_normalize_market_rows_handles_less_than_bracket() -> None:
    rows = [{"market_slug": "elon-week-1", "groupItemTitle": "<20", "token_id": "t0"}]

    normalized = normalize_market_rows(rows)

    assert normalized[0]["bracket_low"] == 0
    assert normalized[0]["bracket_high"] == 19
