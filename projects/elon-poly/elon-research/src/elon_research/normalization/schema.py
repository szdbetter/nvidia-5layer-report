from dataclasses import dataclass


@dataclass(frozen=True)
class BracketDefinition:
    bracket_low: int
    bracket_high: int | None
