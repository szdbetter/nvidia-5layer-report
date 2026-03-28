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
