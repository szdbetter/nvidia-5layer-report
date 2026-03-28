import json
from pathlib import Path

from elon_research.config import Settings
from elon_research.data_sources.storage import RawSnapshotWriter


def test_raw_snapshot_writer_creates_payload_and_metadata(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)
    writer = RawSnapshotWriter(settings)

    payload_path = writer.write_json(
        source_name="tweets_archive",
        dataset_name="elon_posts",
        payload={"items": [{"id": "1", "text": "hello"}]},
        coverage_start="2024-01-01T00:00:00Z",
        coverage_end="2024-01-07T00:00:00Z",
        fetched_at="2026-03-27T12:00:00Z",
    )

    assert payload_path == tmp_path / "datasets" / "raw" / "tweets_archive" / "elon_posts.json"
    assert json.loads(payload_path.read_text(encoding="utf-8")) == {
        "items": [{"id": "1", "text": "hello"}]
    }

    meta = json.loads(payload_path.with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert payload_path.exists()
    assert meta["source_name"] == "tweets_archive"
    assert meta["dataset_name"] == "elon_posts"
    assert meta["coverage_start"] == "2024-01-01T00:00:00Z"
    assert meta["coverage_end"] == "2024-01-07T00:00:00Z"
    assert meta["fetched_at"] == "2026-03-27T12:00:00Z"
