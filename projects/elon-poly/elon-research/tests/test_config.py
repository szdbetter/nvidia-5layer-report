from pathlib import Path

from elon_research.config import Settings


def test_settings_use_project_relative_directories(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)

    assert settings.project_root == tmp_path
    assert settings.raw_dir == tmp_path / "datasets" / "raw"
    assert settings.normalized_dir == tmp_path / "datasets" / "normalized"
    assert settings.features_dir == tmp_path / "datasets" / "features"
    assert settings.reports_dir == tmp_path / "datasets" / "reports"
