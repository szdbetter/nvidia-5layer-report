import json
from pathlib import Path

from typer.testing import CliRunner

from elon_research import cli


def test_cli_help_lists_research_workflow_commands() -> None:
    runner = CliRunner()

    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "ingest" in result.stdout
    assert "normalize" in result.stdout
    assert "backtest" in result.stdout


def test_ingest_writes_real_snapshot_paths(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

    def fake_ingest_polymarket_snapshot(settings, event_id):
        target = settings.raw_dir / "polymarket" / f"event_{event_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        target.with_suffix(".meta.json").write_text(
            json.dumps({"coverage_start": "2026-03-20T16:00:00Z", "fetched_at": "2026-03-27T16:00:00Z"}),
            encoding="utf-8",
        )
        return str(target)

    def fake_ingest_tweet_snapshot(settings, tracking_id, historical_file):
        target = settings.raw_dir / "tweets" / f"tracking_{tracking_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        target.with_suffix(".meta.json").write_text(
            json.dumps({"coverage_start": "2026-03-20T16:00:00Z", "fetched_at": "2026-03-27T16:00:00Z"}),
            encoding="utf-8",
        )
        return str(target)

    monkeypatch.setattr(cli, "ingest_polymarket_snapshot", fake_ingest_polymarket_snapshot)
    monkeypatch.setattr(cli, "ingest_tweet_snapshot", fake_ingest_tweet_snapshot)

    result = runner.invoke(cli.app, ["ingest", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "已写入 Polymarket 原始快照" in result.stdout
    assert "已写入推文侧原始快照" in result.stdout
    assert (tmp_path / "datasets" / "raw" / "polymarket" / "event_278377.json").exists()
    assert (
        tmp_path
        / "datasets"
        / "raw"
        / "tweets"
        / "tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json"
    ).exists()


def test_normalize_requires_ingested_raw_inputs(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(cli.app, ["normalize", "--project-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "缺少原始快照输入" in result.stdout


def test_normalize_succeeds_after_real_raw_snapshots_exist(tmp_path: Path) -> None:
    raw_polymarket = tmp_path / "datasets" / "raw" / "polymarket"
    raw_tweets = tmp_path / "datasets" / "raw" / "tweets"
    raw_polymarket.mkdir(parents=True, exist_ok=True)
    raw_tweets.mkdir(parents=True, exist_ok=True)
    (raw_polymarket / "event_278377.json").write_text("{}", encoding="utf-8")
    (raw_tweets / "tracking_d861bacb-6108-45d6-9a14-47b9e58ea095.json").write_text("{}", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli.app, ["normalize", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "标准化目录已就绪" in result.stdout


def test_backtest_requires_normalized_inputs(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(cli.app, ["backtest", "--project-root", str(tmp_path)])

    assert result.exit_code != 0
    assert "缺少标准化输入" in result.stdout


def test_ingest_subgraph_market_writes_snapshot_path(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

    def fake_ingest_subgraph_market_snapshot(settings, event_id, bracket_label, window_days, first_per_window):
        target = settings.raw_dir / "polymarket_subgraph" / f"event_{event_id}_market_{bracket_label}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        target.with_suffix(".meta.json").write_text("{}", encoding="utf-8")
        return str(target)

    monkeypatch.setattr(cli, "ingest_subgraph_market_snapshot", fake_ingest_subgraph_market_snapshot)

    result = runner.invoke(
        cli.app,
        [
            "ingest-subgraph-market",
            "--project-root",
            str(tmp_path),
            "--event-id",
            "278377",
            "--bracket-label",
            "260-279",
        ],
    )

    assert result.exit_code == 0
    assert "已写入 Subgraph 原始快照" in result.stdout
    assert (tmp_path / "datasets" / "raw" / "polymarket_subgraph" / "event_278377_market_260-279.json").exists()


def test_ingest_subgraph_event_batch_writes_snapshot_paths(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

    def fake_ingest_subgraph_event_batch(settings, event_id, top_brackets, window_days, first_per_window):
        base = settings.raw_dir / "polymarket_subgraph"
        base.mkdir(parents=True, exist_ok=True)
        targets = []
        for label in ["260-279", "280-299"]:
            path = base / f"event_{event_id}_market_{label}.json"
            path.write_text("{}", encoding="utf-8")
            path.with_suffix(".meta.json").write_text("{}", encoding="utf-8")
            targets.append(str(path))
        return targets

    monkeypatch.setattr(cli, "ingest_subgraph_event_batch", fake_ingest_subgraph_event_batch)

    result = runner.invoke(
        cli.app,
        [
            "ingest-subgraph-event",
            "--project-root",
            str(tmp_path),
            "--event-id",
            "278377",
            "--top-brackets",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "已写入 2 个 Subgraph 原始快照" in result.stdout
    assert (tmp_path / "datasets" / "raw" / "polymarket_subgraph" / "event_278377_market_260-279.json").exists()
    assert (tmp_path / "datasets" / "raw" / "polymarket_subgraph" / "event_278377_market_280-299.json").exists()
