import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from elon_research.config import Settings


@dataclass
class RawSnapshotWriter:
    settings: Settings

    def write_json(
        self,
        source_name: str,
        dataset_name: str,
        payload: dict[str, Any],
        coverage_start: str,
        coverage_end: str,
        fetched_at: str,
    ) -> Path:
        source_dir = self.settings.raw_dir / source_name
        source_dir.mkdir(parents=True, exist_ok=True)

        payload_path = source_dir / f"{dataset_name}.json"
        payload_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        payload_path.with_suffix(".meta.json").write_text(
            json.dumps(
                {
                    "source_name": source_name,
                    "dataset_name": dataset_name,
                    "coverage_start": coverage_start,
                    "coverage_end": coverage_end,
                    "fetched_at": fetched_at,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return payload_path
