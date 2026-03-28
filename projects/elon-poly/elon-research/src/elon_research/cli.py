from pathlib import Path

import typer

from elon_research.config import Settings
from elon_research.data_sources.polymarket import DEFAULT_EVENT_ID, ingest_polymarket_snapshot
from elon_research.data_sources.polymarket_subgraph import ingest_subgraph_event_batch, ingest_subgraph_market_snapshot
from elon_research.data_sources.tweets import DEFAULT_TRACKING_ID, ingest_tweet_snapshot
from elon_research.evaluation.reporting import build_summary_report
from elon_research.evaluation.weak_validation import run_weak_validation
from elon_research.normalization.pipeline import normalize_snapshots

app = typer.Typer(help="Elon 推文 Polymarket 研究系统命令行")
NORMALIZED_MARKER_NAME = "_placeholder_normalized.txt"


@app.callback()
def main() -> None:
    """注册命令组入口。"""


@app.command()
def doctor() -> None:
    """输出命令行健康检查结果。"""
    typer.echo("elon-research CLI 已就绪")


@app.command()
def ingest(
    project_root: Path = typer.Option(Path("."), "--project-root", help="项目根目录"),
    event_id: int = typer.Option(DEFAULT_EVENT_ID, "--event-id", help="Polymarket 事件 ID"),
    tracking_id: str = typer.Option(DEFAULT_TRACKING_ID, "--tracking-id", help="xtracker tracking ID"),
    historical_weekly_file: Path = typer.Option(
        Path("../weekly_history.json"),
        "--historical-weekly-file",
        help="本地历史周数据文件，仅作辅助参考",
    ),
) -> None:
    """执行真实原始数据采集。"""
    settings = Settings.from_project_root(project_root.resolve())
    history_path = historical_weekly_file.resolve() if not historical_weekly_file.is_absolute() else historical_weekly_file
    market_path = ingest_polymarket_snapshot(settings, event_id=event_id)
    tweet_path = ingest_tweet_snapshot(settings, tracking_id=tracking_id, historical_file=history_path)
    typer.echo(f"已写入 Polymarket 原始快照：{market_path}")
    typer.echo(f"已写入推文侧原始快照：{tweet_path}")


@app.command("ingest-subgraph-market")
def ingest_subgraph_market(
    project_root: Path = typer.Option(Path("."), "--project-root", help="项目根目录"),
    event_id: int = typer.Option(DEFAULT_EVENT_ID, "--event-id", help="Polymarket 事件 ID"),
    bracket_label: str = typer.Option(..., "--bracket-label", help="bracket 标签，例如 260-279"),
    window_days: int = typer.Option(7, "--window-days", help="向前抓取的天数"),
    first_per_window: int = typer.Option(200, "--first-per-window", help="每个时间窗口的事件上限"),
) -> None:
    """抓取单个 bracket 的 Goldsky subgraph 原始快照。"""
    settings = Settings.from_project_root(project_root.resolve())
    snapshot_path = ingest_subgraph_market_snapshot(
        settings=settings,
        event_id=event_id,
        bracket_label=bracket_label,
        window_days=window_days,
        first_per_window=first_per_window,
    )
    typer.echo(f"已写入 Subgraph 原始快照：{snapshot_path}")


@app.command("ingest-subgraph-event")
def ingest_subgraph_event(
    project_root: Path = typer.Option(Path("."), "--project-root", help="项目根目录"),
    event_id: int = typer.Option(DEFAULT_EVENT_ID, "--event-id", help="Polymarket 事件 ID"),
    top_brackets: int = typer.Option(3, "--top-brackets", help="抓取成交最活跃的前 N 个 bracket"),
    window_days: int = typer.Option(7, "--window-days", help="向前抓取的天数"),
    first_per_window: int = typer.Option(200, "--first-per-window", help="每个时间窗口的事件上限"),
) -> None:
    """按事件批量抓取高流动 bracket 的 Goldsky subgraph 原始快照。"""
    settings = Settings.from_project_root(project_root.resolve())
    snapshot_paths = ingest_subgraph_event_batch(
        settings=settings,
        event_id=event_id,
        top_brackets=top_brackets,
        window_days=window_days,
        first_per_window=first_per_window,
    )
    typer.echo(f"已写入 {len(snapshot_paths)} 个 Subgraph 原始快照")
    for path in snapshot_paths:
        typer.echo(path)


@app.command()
def normalize(project_root: Path = typer.Option(Path("."), "--project-root", help="项目根目录")) -> None:
    """执行真实快照标准化。"""
    settings = Settings.from_project_root(project_root.resolve())
    required_raw_files = [
        settings.raw_dir / "polymarket" / f"event_{DEFAULT_EVENT_ID}.json",
        settings.raw_dir / "tweets" / f"tracking_{DEFAULT_TRACKING_ID}.json",
    ]
    missing_raw_files = [str(path) for path in required_raw_files if not path.exists()]
    if missing_raw_files:
        typer.echo(f"缺少原始快照输入：{', '.join(missing_raw_files)}")
        raise typer.Exit(code=1)
    outputs = normalize_snapshots(settings, event_id=DEFAULT_EVENT_ID, tracking_id=DEFAULT_TRACKING_ID)
    marker_path = settings.normalized_dir / NORMALIZED_MARKER_NAME
    marker_path.write_text("标准化已完成。\n", encoding="utf-8")
    typer.echo(f"标准化目录已就绪：{settings.normalized_dir}")
    for name, path in outputs.items():
        typer.echo(f"已写入标准化{name}：{path}")


@app.command()
def backtest(project_root: Path = typer.Option(Path("."), "--project-root", help="项目根目录")) -> None:
    """执行首轮弱验证回放。"""
    settings = Settings.from_project_root(project_root.resolve())
    marker_path = settings.normalized_dir / NORMALIZED_MARKER_NAME
    if not marker_path.exists():
        typer.echo(f"缺少标准化输入：{marker_path}")
        raise typer.Exit(code=1)
    report_path = run_weak_validation(
        normalized_dir=settings.normalized_dir,
        reports_dir=settings.reports_dir,
        event_id=DEFAULT_EVENT_ID,
        tracking_id=DEFAULT_TRACKING_ID,
    )
    typer.echo(f"报告目录已就绪：{settings.reports_dir}")
    typer.echo(f"弱验证回放报告已生成：{report_path}")


@app.command("report-demo")
def report_demo() -> None:
    """输出中文报告摘要演示。"""

    demo_result = {
        "trades": [
            {
                "entry_timestamp": "2026-03-20T03:00:00Z",
                "entry_price": 0.40,
                "size": 100.0,
                "exit_timestamp": "2026-03-20T04:00:00Z",
                "exit_price": 0.55,
            }
        ],
        "summary": {"trade_count": 1},
    }
    typer.echo(build_summary_report(demo_result))


if __name__ == "__main__":
    app()
