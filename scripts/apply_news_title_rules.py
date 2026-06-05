#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from news_title_rules import apply_titles_to_data
from report_paths import find_data_file, find_latest_base


CATEGORIES = ("macro", "trading", "economy_political_others")


def apply_for_base(base: str) -> list[Path]:
    changed: list[Path] = []
    for category in CATEGORIES:
        path = find_data_file(base, category)
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        data = json.loads(original)
        apply_titles_to_data(data, category)
        updated = json.dumps(data, ensure_ascii=False, indent=2)
        if updated != original.strip():
            path.write_text(updated + "\n", encoding="utf-8")
            changed.append(path)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply standardized news title rules to report data JSONs")
    parser.add_argument("base", nargs="?", default=None, help="Report base, e.g. mor_05_06_2026")
    args = parser.parse_args()

    base = args.base or find_latest_base()
    changed = apply_for_base(base)
    if changed:
        print(f"Applied title rules for {base}:")
        for path in changed:
            print(f"  {path}")
    else:
        print(f"No title changes needed for {base}.")


if __name__ == "__main__":
    main()
