#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_paths import find_data_file
from summary_rules import CATEGORIES, total_item_count, validate_summary_payload


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def validate_base(base: str, expected_total: int | None = None, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    payloads: list[dict] = []

    for category in CATEGORIES:
        path = find_data_file(base, category)
        if not path.exists():
            errors.append(f"{category}: missing file {path}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{category}: invalid JSON: {exc}")
            continue
        payloads.append(payload)
        errors.extend(validate_summary_payload(payload, category, strict=strict))

    if expected_total is not None:
        actual_total = total_item_count(payloads)
        if actual_total != expected_total:
            errors.append(f"total item_count is {actual_total}, expected {expected_total}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate report summary JSON files.")
    parser.add_argument("base", help="Report base, e.g. mor_05_06_2026")
    parser.add_argument("--expected-total", type=int, default=None, help="Expected total article count across all categories")
    parser.add_argument("--strict", action="store_true", help="Also require canonical section title fields and values")
    args = parser.parse_args()

    errors = validate_base(args.base, args.expected_total, strict=args.strict)
    if errors:
        print("Summary data validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print(f"Summary data validation passed for {args.base}.")


if __name__ == "__main__":
    main()
