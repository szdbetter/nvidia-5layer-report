from elon_research.normalization.schema import BracketDefinition


def _parse_bracket(label: str) -> BracketDefinition:
    cleaned = label.strip()
    if cleaned.startswith("<"):
        upper = int(cleaned[1:])
        return BracketDefinition(bracket_low=0, bracket_high=upper - 1)
    if cleaned.endswith("+"):
        return BracketDefinition(bracket_low=int(cleaned[:-1]), bracket_high=None)

    low, high = cleaned.split("-", 1)
    return BracketDefinition(bracket_low=int(low), bracket_high=int(high))


def normalize_market_rows(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        bracket = _parse_bracket(row["groupItemTitle"])
        normalized.append(
            {
                "market_slug": row["market_slug"],
                "token_id": row["token_id"],
                "bracket_low": bracket.bracket_low,
                "bracket_high": bracket.bracket_high,
            }
        )
    return normalized
