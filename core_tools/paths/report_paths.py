from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_root import PROJECT_ROOT

BASE_DIR = PROJECT_ROOT
REPORTS_DIR = BASE_DIR / "reports"


def report_dir(base: str) -> Path:
    return REPORTS_DIR / base


def report_subdir(base: str, name: str) -> Path:
    path = report_dir(base) / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir(base: str) -> Path:
    return report_subdir(base, "data")


def summaries_dir(base: str) -> Path:
    return report_subdir(base, "summaries")


def source_dir(base: str) -> Path:
    return report_subdir(base, "source")


def export_dir(base: str, kind: str) -> Path:
    return report_subdir(base, "exports") / kind


def testing_dir(base: str, kind: str) -> Path:
    return report_subdir(base, "testing") / kind


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def data_file(base: str, suffix: str) -> Path:
    return data_dir(base) / f"{base}_{suffix}.json"


def summary_file(base: str, lang: str) -> Path:
    return summaries_dir(base) / f"{base}_summary_{lang}.md"


def source_file(base: str, suffix: str = "") -> Path:
    stem = f"{base}_{suffix}" if suffix else base
    return source_dir(base) / f"{stem}.md"


def export_file(base: str, kind: str, filename: str) -> Path:
    out = export_dir(base, kind) / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def find_existing(base: str, *candidates: Path) -> Path:
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def find_data_file(base: str, suffix: str) -> Path:
    return find_existing(base, data_dir(base) / f"{base}_{suffix}.json", REPORTS_DIR / f"{base}_{suffix}.json")


def find_html_file(base: str, lang: str) -> Path:
    filename = f"{base}_report_{lang}.html"
    return find_existing(base, export_dir(base, "html") / filename, REPORTS_DIR / filename)


def find_latest_base() -> str:
    nested = sorted(p.name for p in REPORTS_DIR.iterdir() if p.is_dir() and (p / "data").exists())
    if nested:
        return nested[-1]
    flat = sorted({p.stem[: -len("_macro")] for p in REPORTS_DIR.glob("*_macro.json")})
    if flat:
        return flat[-1]
    raise SystemExit("No report data found in reports/.")
