from typer.testing import CliRunner

from elon_research.cli import app
from elon_research.evaluation.reporting import build_summary_report


def test_build_summary_report_outputs_chinese_summary() -> None:
    result = {
        "trades": [
            {
                "entry_timestamp": "2026-03-20T03:00:00Z",
                "entry_price": 0.40,
                "size": 100.0,
                "exit_timestamp": "2026-03-20T04:00:00Z",
                "exit_price": 0.55,
            },
            {
                "entry_timestamp": "2026-03-20T05:00:00Z",
                "entry_price": 0.60,
                "size": 50.0,
                "exit_timestamp": "2026-03-20T06:00:00Z",
                "exit_price": 0.50,
            },
        ],
        "summary": {"trade_count": 2},
    }

    report = build_summary_report(result)

    assert "总交易次数：2" in report
    assert "总收益：10.00" in report
    assert "最大回撤：5.00" in report
    assert "建议：" in report


def test_build_summary_report_recommends_wait_when_no_trades() -> None:
    report = build_summary_report({"trades": [], "summary": {"trade_count": 0}})

    assert "总交易次数：0" in report
    assert "总收益：0.00" in report
    assert "建议：当前暂无成交，建议继续观察样本。" in report


def test_build_summary_report_uses_trade_length_when_summary_count_mismatches() -> None:
    report = build_summary_report(
        {
            "trades": [
                {
                    "entry_timestamp": "2026-03-20T05:00:00Z",
                    "entry_price": 0.60,
                    "size": 50.0,
                    "exit_timestamp": "2026-03-20T06:00:00Z",
                    "exit_price": 0.50,
                }
            ],
            "summary": {"trade_count": 0},
        }
    )

    assert "总交易次数：1" in report
    assert "总收益：-5.00" in report


def test_build_summary_report_recommends_review_when_losing_money() -> None:
    report = build_summary_report(
        {
            "trades": [
                {
                    "entry_timestamp": "2026-03-20T05:00:00Z",
                    "entry_price": 0.60,
                    "size": 50.0,
                    "exit_timestamp": "2026-03-20T06:00:00Z",
                    "exit_price": 0.50,
                }
            ],
            "summary": {"trade_count": 1},
        }
    )

    assert "建议：策略暂未体现稳定优势，建议暂停实盘假设并复查信号。" in report


def test_report_demo_command_prints_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["report-demo"])

    assert result.exit_code == 0
    assert "总交易次数：" in result.stdout
    assert "建议：" in result.stdout
