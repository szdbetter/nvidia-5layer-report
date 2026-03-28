# Elon 推文 Polymarket 研究系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一套仅面向研究与验证的 Elon 推文 Polymarket 系统，能够采集历史数据、统一标准化、运行事件研究、执行严格回放回测，并输出是否具有可交易 edge 的结论。

**Architecture:** 在现有 `elon-poly` 目录内新增一个独立的 `elon-research/` 子项目，采用“原始采集 -> 标准化 -> 特征 -> 回放回测 -> 评估”的单向流水线。所有研究代码只读取标准化后的数据集，不直接依赖旧项目脚本；旧目录仅作为参考数据和文档来源。

**Tech Stack:** Python 3.11、pytest、SQLite、Parquet、pandas、requests、Typer、matplotlib

---

## 文件结构

### 新建目录

- `elon-research/pyproject.toml`
- `elon-research/README.md`
- `elon-research/src/elon_research/__init__.py`
- `elon-research/src/elon_research/config.py`
- `elon-research/src/elon_research/cli.py`
- `elon-research/src/elon_research/data_sources/__init__.py`
- `elon-research/src/elon_research/data_sources/polymarket.py`
- `elon-research/src/elon_research/data_sources/tweets.py`
- `elon-research/src/elon_research/data_sources/storage.py`
- `elon-research/src/elon_research/normalization/__init__.py`
- `elon-research/src/elon_research/normalization/schema.py`
- `elon-research/src/elon_research/normalization/markets.py`
- `elon-research/src/elon_research/normalization/tweets.py`
- `elon-research/src/elon_research/features/__init__.py`
- `elon-research/src/elon_research/features/build.py`
- `elon-research/src/elon_research/strategies/__init__.py`
- `elon-research/src/elon_research/strategies/count_deviation.py`
- `elon-research/src/elon_research/strategies/event_shock.py`
- `elon-research/src/elon_research/backtesting/__init__.py`
- `elon-research/src/elon_research/backtesting/replay.py`
- `elon-research/src/elon_research/evaluation/__init__.py`
- `elon-research/src/elon_research/evaluation/reporting.py`
- `elon-research/tests/test_config.py`
- `elon-research/tests/test_storage.py`
- `elon-research/tests/test_market_normalization.py`
- `elon-research/tests/test_tweet_normalization.py`
- `elon-research/tests/test_feature_build.py`
- `elon-research/tests/test_replay.py`
- `elon-research/tests/test_reporting.py`
- `elon-research/datasets/raw/.gitkeep`
- `elon-research/datasets/normalized/.gitkeep`
- `elon-research/datasets/features/.gitkeep`
- `elon-research/datasets/reports/.gitkeep`
- `elon-research/experiments/.gitkeep`

### 文件职责

- `config.py`：研究项目路径、数据目录、运行参数与数据版本配置
- `cli.py`：统一命令入口，支持 `ingest`、`normalize`、`features`、`backtest`、`report`
- `data_sources/polymarket.py`：市场元数据、价格时间序列、成交拉取
- `data_sources/tweets.py`：Elon 推文时间线导入、来源元信息与可信度标注
- `data_sources/storage.py`：原始快照保存、来源登记、版本化目录管理
- `normalization/schema.py`：标准化数据模型
- `normalization/markets.py`：Polymarket 市场、bracket、交易、价格序列标准化
- `normalization/tweets.py`：推文事件标准化与累计计数重建
- `features/build.py`：生成研究特征数据集
- `strategies/*.py`：候选策略信号函数
- `backtesting/replay.py`：严格回放回测与执行假设
- `evaluation/reporting.py`：统计指标、图表与中文结论输出

## 实施原则

- 每个任务都必须产出可运行、可测试、可提交的最小增量
- 先搭数据与验证基础，再做策略与回测
- 不复用旧项目的 `daemon.py`、`trader.py`、`monitor.py` 或 `positions.json` 工作流
- 所有文档、注释、报告输出使用中文
- 优先 TDD；研究脚本也必须有核心单元测试

### 任务 1：初始化独立研究项目骨架

**Files:**
- Create: `elon-research/pyproject.toml`
- Create: `elon-research/README.md`
- Create: `elon-research/src/elon_research/__init__.py`
- Create: `elon-research/src/elon_research/config.py`
- Create: `elon-research/src/elon_research/cli.py`
- Create: `elon-research/tests/test_config.py`

- [ ] **Step 1: 写失败测试，约束默认配置路径和数据目录**

```python
from pathlib import Path

from elon_research.config import Settings


def test_settings_use_project_relative_directories(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)

    assert settings.project_root == tmp_path
    assert settings.raw_dir == tmp_path / "datasets" / "raw"
    assert settings.normalized_dir == tmp_path / "datasets" / "normalized"
    assert settings.features_dir == tmp_path / "datasets" / "features"
    assert settings.reports_dir == tmp_path / "datasets" / "reports"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError` or `cannot import name 'Settings'`

- [ ] **Step 3: 写最小实现与项目配置**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "elon-research"
version = "0.1.0"
description = "Elon 推文 Polymarket 研究系统"
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.2.0",
  "pyarrow>=16.0.0",
  "requests>=2.32.0",
  "typer>=0.12.0",
  "matplotlib>=3.9.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.2.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    raw_dir: Path
    normalized_dir: Path
    features_dir: Path
    reports_dir: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "Settings":
        return cls(
            project_root=project_root,
            raw_dir=project_root / "datasets" / "raw",
            normalized_dir=project_root / "datasets" / "normalized",
            features_dir=project_root / "datasets" / "features",
            reports_dir=project_root / "datasets" / "reports",
        )
```

```python
import typer

app = typer.Typer(help="Elon 推文 Polymarket 研究系统命令行")


@app.command()
def doctor() -> None:
    typer.echo("elon-research CLI 已就绪")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/pyproject.toml elon-research/README.md elon-research/src/elon_research/__init__.py elon-research/src/elon_research/config.py elon-research/src/elon_research/cli.py elon-research/tests/test_config.py
git commit -m "feat: 初始化 Elon 研究项目骨架"
```

### 任务 2：实现原始采集存储与来源登记

**Files:**
- Create: `elon-research/src/elon_research/data_sources/storage.py`
- Create: `elon-research/tests/test_storage.py`
- Modify: `elon-research/src/elon_research/config.py`

- [ ] **Step 1: 写失败测试，约束原始快照与来源元数据写入**

```python
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

    meta = json.loads(payload_path.with_suffix(".meta.json").read_text())
    assert payload_path.exists()
    assert meta["source_name"] == "tweets_archive"
    assert meta["dataset_name"] == "elon_posts"
    assert meta["coverage_start"] == "2024-01-01T00:00:00Z"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_storage.py -v`
Expected: FAIL with `ModuleNotFoundError` or `RawSnapshotWriter` missing

- [ ] **Step 3: 写最小实现**

```python
import json
from dataclasses import dataclass
from pathlib import Path

from elon_research.config import Settings


@dataclass
class RawSnapshotWriter:
    settings: Settings

    def write_json(
        self,
        source_name: str,
        dataset_name: str,
        payload: dict,
        coverage_start: str,
        coverage_end: str,
        fetched_at: str,
    ) -> Path:
        source_dir = self.settings.raw_dir / source_name
        source_dir.mkdir(parents=True, exist_ok=True)
        payload_path = source_dir / f"{dataset_name}.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
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
            )
        )
        return payload_path
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_storage.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/src/elon_research/config.py elon-research/src/elon_research/data_sources/storage.py elon-research/tests/test_storage.py
git commit -m "feat: 增加原始采集快照与来源登记"
```

### 任务 3：实现市场与推文标准化

**Files:**
- Create: `elon-research/src/elon_research/normalization/schema.py`
- Create: `elon-research/src/elon_research/normalization/markets.py`
- Create: `elon-research/src/elon_research/normalization/tweets.py`
- Create: `elon-research/tests/test_market_normalization.py`
- Create: `elon-research/tests/test_tweet_normalization.py`

- [ ] **Step 1: 写失败测试，约束 bracket 标准化**

```python
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
```

- [ ] **Step 2: 写失败测试，约束推文事件标准化与累计计数**

```python
from elon_research.normalization.tweets import normalize_tweet_rows


def test_normalize_tweet_rows_builds_running_count() -> None:
    rows = [
        {"tweet_id": "t1", "posted_at": "2026-03-20T01:00:00Z"},
        {"tweet_id": "t2", "posted_at": "2026-03-20T02:00:00Z"},
    ]

    normalized = normalize_tweet_rows(rows)

    assert normalized[0]["running_count"] == 1
    assert normalized[1]["running_count"] == 2
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_market_normalization.py tests/test_tweet_normalization.py -v`
Expected: FAIL with missing modules or functions

- [ ] **Step 4: 写最小实现**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class BracketDefinition:
    bracket_low: int
    bracket_high: int | None
```

```python
def _parse_bracket(label: str) -> tuple[int, int | None]:
    if label.endswith("+"):
        return int(label[:-1]), None
    low, high = label.split("-", 1)
    return int(low), int(high)


def normalize_market_rows(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        low, high = _parse_bracket(row["groupItemTitle"])
        normalized.append(
            {
                "market_slug": row["market_slug"],
                "token_id": row["token_id"],
                "bracket_low": low,
                "bracket_high": high,
            }
        )
    return normalized
```

```python
def normalize_tweet_rows(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda row: row["posted_at"])
    normalized = []
    for index, row in enumerate(ordered, start=1):
        normalized.append(
            {
                "tweet_id": row["tweet_id"],
                "posted_at": row["posted_at"],
                "running_count": index,
            }
        )
    return normalized
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_market_normalization.py tests/test_tweet_normalization.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/src/elon_research/normalization/schema.py elon-research/src/elon_research/normalization/markets.py elon-research/src/elon_research/normalization/tweets.py elon-research/tests/test_market_normalization.py elon-research/tests/test_tweet_normalization.py
git commit -m "feat: 增加市场与推文标准化逻辑"
```

### 任务 4：实现特征生成

**Files:**
- Create: `elon-research/src/elon_research/features/build.py`
- Create: `elon-research/tests/test_feature_build.py`

- [ ] **Step 1: 写失败测试，约束窗口增量和剩余时间计算**

```python
from elon_research.features.build import build_feature_rows


def test_build_feature_rows_computes_deltas_and_time_remaining() -> None:
    tweet_rows = [
        {"posted_at": "2026-03-20T01:00:00Z", "running_count": 1},
        {"posted_at": "2026-03-20T02:00:00Z", "running_count": 2},
        {"posted_at": "2026-03-20T03:00:00Z", "running_count": 5},
    ]
    price_rows = [
        {"timestamp": "2026-03-20T03:00:00Z", "market_mid": 0.18},
    ]

    features = build_feature_rows(
        tweet_rows=tweet_rows,
        price_rows=price_rows,
        market_end="2026-03-27T16:00:00Z",
    )

    assert features[0]["tweet_delta_1h"] == 3
    assert features[0]["tweets_total"] == 5
    assert features[0]["minutes_to_close"] > 0
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_feature_build.py -v`
Expected: FAIL with missing module or function

- [ ] **Step 3: 写最小实现**

```python
from datetime import datetime


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def build_feature_rows(tweet_rows: list[dict], price_rows: list[dict], market_end: str) -> list[dict]:
    market_end_dt = _parse_iso(market_end)
    tweet_map = {row["posted_at"]: row["running_count"] for row in tweet_rows}
    features = []
    for price in price_rows:
        ts = _parse_iso(price["timestamp"])
        current_total = max(
            row["running_count"]
            for row in tweet_rows
            if _parse_iso(row["posted_at"]) <= ts
        )
        one_hour_ago = max(
            (
                row["running_count"]
                for row in tweet_rows
                if _parse_iso(row["posted_at"]) <= ts.replace(hour=ts.hour - 1)
            ),
            default=0,
        )
        features.append(
            {
                "timestamp": price["timestamp"],
                "tweets_total": current_total,
                "tweet_delta_1h": current_total - one_hour_ago,
                "minutes_to_close": int((market_end_dt - ts).total_seconds() // 60),
                "market_mid": price["market_mid"],
            }
        )
    return features
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_feature_build.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/src/elon_research/features/build.py elon-research/tests/test_feature_build.py
git commit -m "feat: 增加研究特征生成逻辑"
```

### 任务 5：实现候选策略与严格回放回测

**Files:**
- Create: `elon-research/src/elon_research/strategies/count_deviation.py`
- Create: `elon-research/src/elon_research/strategies/event_shock.py`
- Create: `elon-research/src/elon_research/backtesting/replay.py`
- Create: `elon-research/tests/test_replay.py`

- [ ] **Step 1: 写失败测试，约束信号生成与保守执行**

```python
from elon_research.backtesting.replay import replay_strategy


def test_replay_strategy_applies_slippage_and_position_limit() -> None:
    feature_rows = [
        {"timestamp": "2026-03-20T03:00:00Z", "market_mid": 0.10, "fair_value": 0.20, "minutes_to_close": 1000},
        {"timestamp": "2026-03-20T04:00:00Z", "market_mid": 0.14, "fair_value": 0.13, "minutes_to_close": 940},
    ]

    result = replay_strategy(
        feature_rows=feature_rows,
        edge_threshold=0.05,
        slippage_bps=100,
        max_position_size=100.0,
    )

    assert result["trades"][0]["entry_price"] == 0.101
    assert result["summary"]["trade_count"] == 1
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_replay.py -v`
Expected: FAIL with missing module or function

- [ ] **Step 3: 写最小实现**

```python
def generate_count_deviation_signal(feature_row: dict, edge_threshold: float) -> bool:
    return (feature_row["fair_value"] - feature_row["market_mid"]) >= edge_threshold
```

```python
def generate_event_shock_signal(feature_row: dict, min_burst: int, edge_threshold: float) -> bool:
    return feature_row.get("tweet_delta_1h", 0) >= min_burst and (
        feature_row["fair_value"] - feature_row["market_mid"]
    ) >= edge_threshold
```

```python
def replay_strategy(
    feature_rows: list[dict],
    edge_threshold: float,
    slippage_bps: int,
    max_position_size: float,
) -> dict:
    trades = []
    open_trade = None
    slippage = slippage_bps / 10000
    for row in feature_rows:
        edge = row["fair_value"] - row["market_mid"]
        if open_trade is None and edge >= edge_threshold:
            open_trade = {
                "entry_timestamp": row["timestamp"],
                "entry_price": round(row["market_mid"] * (1 + slippage), 3),
                "size": max_position_size,
            }
        elif open_trade is not None and edge < 0:
            open_trade["exit_timestamp"] = row["timestamp"]
            open_trade["exit_price"] = round(row["market_mid"] * (1 - slippage), 3)
            trades.append(open_trade)
            open_trade = None
    return {"trades": trades, "summary": {"trade_count": len(trades)}}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_replay.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/src/elon_research/strategies/count_deviation.py elon-research/src/elon_research/strategies/event_shock.py elon-research/src/elon_research/backtesting/replay.py elon-research/tests/test_replay.py
git commit -m "feat: 增加候选策略与严格回放回测"
```

### 任务 6：实现评估输出与中文研究报告

**Files:**
- Create: `elon-research/src/elon_research/evaluation/reporting.py`
- Create: `elon-research/tests/test_reporting.py`
- Modify: `elon-research/src/elon_research/cli.py`

- [ ] **Step 1: 写失败测试，约束中文结论与核心指标输出**

```python
from elon_research.evaluation.reporting import build_summary_report


def test_build_summary_report_returns_chinese_summary() -> None:
    report = build_summary_report(
        summary={"trade_count": 3, "total_pnl": 12.5, "max_drawdown": -4.0},
        recommendation="继续进入半自动交易设计",
    )

    assert "总交易次数：3" in report
    assert "总收益：12.5" in report
    assert "建议：继续进入半自动交易设计" in report
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_reporting.py -v`
Expected: FAIL with missing module or function

- [ ] **Step 3: 写最小实现**

```python
def build_summary_report(summary: dict, recommendation: str) -> str:
    return "\n".join(
        [
            "# 研究结论摘要",
            f"总交易次数：{summary['trade_count']}",
            f"总收益：{summary['total_pnl']}",
            f"最大回撤：{summary['max_drawdown']}",
            f"建议：{recommendation}",
        ]
    )
```

```python
import typer

from elon_research.evaluation.reporting import build_summary_report

app = typer.Typer(help="Elon 推文 Polymarket 研究系统命令行")


@app.command()
def doctor() -> None:
    typer.echo("elon-research CLI 已就绪")


@app.command()
def demo_report() -> None:
    typer.echo(
        build_summary_report(
            summary={"trade_count": 1, "total_pnl": 0.0, "max_drawdown": 0.0},
            recommendation="等待真实研究结果",
        )
    )
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_reporting.py -v`
Expected: PASS

- [ ] **Step 5: 运行全量测试**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest -v`
Expected: PASS for all test files

- [ ] **Step 6: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/src/elon_research/evaluation/reporting.py elon-research/src/elon_research/cli.py elon-research/tests/test_reporting.py
git commit -m "feat: 增加中文评估输出与报告摘要"
```

### 任务 7：接入真实数据采集命令并完成首轮实验

**Files:**
- Modify: `elon-research/src/elon_research/cli.py`
- Modify: `elon-research/src/elon_research/data_sources/polymarket.py`
- Modify: `elon-research/src/elon_research/data_sources/tweets.py`
- Create: `elon-research/experiments/README.md`
- Create: `elon-research/datasets/reports/README.md`

- [ ] **Step 1: 写失败测试，约束 CLI 子命令存在**

```python
from typer.testing import CliRunner

from elon_research.cli import app


def test_cli_lists_ingest_and_backtest_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "ingest" in result.stdout
    assert "backtest" in result.stdout
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_reporting.py -v`
Expected: FAIL because commands are not yet registered

- [ ] **Step 3: 写最小实现并记录首轮实验步骤**

```python
@app.command()
def ingest() -> None:
    typer.echo("执行原始数据采集")


@app.command()
def normalize() -> None:
    typer.echo("执行标准化")


@app.command()
def backtest() -> None:
    typer.echo("执行严格回放回测")
```

```markdown
# 实验目录说明

本目录存放冻结实验版本、参数说明、训练集/验证集/测试集切分记录，以及最终中文结论。

首轮实验要求：
1. 冻结数据集版本。
2. 记录 Polymarket 数据来源与推文数据来源。
3. 明确训练集、验证集、测试集的时间切分。
4. 运行事件研究。
5. 运行 S1 与 S2 的保守级回测。
6. 输出中文报告，不得修改结论文本以迎合结果。
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && pytest tests/test_reporting.py -v`
Expected: PASS

- [ ] **Step 5: 手动验证 CLI**

Run: `cd /root/.openclaw/workspace/projects/elon-poly/elon-research && python -m elon_research.cli --help`
Expected: help output contains `ingest`, `normalize`, `backtest`, `demo-report` or equivalent Chinese descriptions

- [ ] **Step 6: 提交**

```bash
cd /root/.openclaw/workspace/projects/elon-poly
git add elon-research/src/elon_research/cli.py elon-research/src/elon_research/data_sources/polymarket.py elon-research/src/elon_research/data_sources/tweets.py elon-research/experiments/README.md elon-research/datasets/reports/README.md
git commit -m "feat: 增加研究流程命令与首轮实验约束"
```

## Spec 覆盖检查

- 原始采集层：任务 2、任务 7
- 标准化层：任务 3
- 特征层：任务 4
- 候选策略：任务 5
- 严格回放回测：任务 5
- 中文评估输出：任务 6、任务 7
- 防止泄漏与伪验证：任务 7 中的实验冻结与记录要求，后续实现时必须落到真实实验元数据文件
- 新开干净研究项目：任务 1

## 自检结论

- 未保留 `TODO`、`TBD` 一类占位符
- 任务顺序满足先骨架、后数据、再特征、再策略、再评估
- 计划只覆盖研究系统，不包含自动交易或实时运营型 dashboard
