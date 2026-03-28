import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from elon_research.config import Settings
from elon_research.data_sources.storage import RawSnapshotWriter

XTRACKER_API_BASE = "https://xtracker.polymarket.com/api"
DEFAULT_TRACKING_ID = "d861bacb-6108-45d6-9a14-47b9e58ea095"


def ingest_tweet_snapshot(
    settings: Settings,
    tracking_id: str = DEFAULT_TRACKING_ID,
    historical_file: Path | None = None,
) -> str:
    """抓取当前 tracking 摘要，并桥接本地历史周数据作为辅助输入。"""
    writer = RawSnapshotWriter(settings)
    fetched_at = _utc_now_iso()
    tracking_payload = _fetch_json(
        f"{XTRACKER_API_BASE}/trackings/{tracking_id}",
        params={"includeStats": "true"},
    )
    data = tracking_payload.get("data", {})
    history_payload = _load_optional_history(historical_file)
    payload_path = writer.write_json(
        source_name="tweets",
        dataset_name=f"tracking_{tracking_id}",
        payload={
            "tracking": tracking_payload,
            "historical_reference": history_payload,
            "provenance": {
                "tracking_source": "xtracker",
                "historical_file": str(historical_file) if historical_file else None,
                "historical_is_reference_only": True,
            },
        },
        coverage_start=data.get("startDate", "UNKNOWN"),
        coverage_end=data.get("endDate", "UNKNOWN"),
        fetched_at=fetched_at,
    )
    return str(payload_path)


def _load_optional_history(historical_file: Path | None) -> dict[str, Any]:
    if historical_file is None or not historical_file.exists():
        return {"items": [], "note": "未提供本地历史周数据文件。"}
    return {
        "items": json.loads(historical_file.read_text(encoding="utf-8")),
        "note": "本地历史周数据仅作为辅助参考，不可冒充逐条历史推文时间线。",
    }


def _fetch_json(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
