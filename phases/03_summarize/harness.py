"""
LLM output validator for news summary JSON files.
Usage: python harness.py <json_file>
Returns per-item pass/fail with specific error messages for LLM retry feedback.

Handles both nested structures:
  corporate.json:                 top-level "sectors" -> each has "items"
  economy_political_others.json:  top-level "subtypes" -> each has "items"
  macro.json / trading.json:      top-level "items" list
"""
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORD_MAX = 60
LANG_MIN_WORDS = 20
FLEXIBLE_MIN = 10
NUMBER_COVERAGE_MIN = 0.80

# Verbatim Google Sheets content — skip word count entirely
WORD_COUNT_EXEMPT_CATEGORIES = {"macro"}
WORD_COUNT_EXEMPT_SOURCES = {"vin_bank"}
# Concise facts/figures — enforce only a loose floor, no ceiling
WORD_COUNT_FLEXIBLE_CATEGORIES = {"trading"}


def _word_count(text: str) -> int:
    return len(text.split())


def _extract_numbers(text: str) -> set:
    return set(re.findall(r"\d+(?:[.,]\d+)*%?", text))


def validate_item(item: dict, category: str = "", source_text: str = "") -> dict:
    errors = []

    vn = item.get("summary_vn", "")
    en = item.get("summary_en", "")
    src = item.get("source", "")
    title_vn = item.get("title_vn", "")
    title_en = item.get("title_en", "")

    # 1. Schema check
    if not (title_vn or title_en):
        errors.append("missing both title_vn and title_en")
    if not vn:
        errors.append("missing or empty field: 'summary_vn'")
    if not en:
        errors.append("missing or empty field: 'summary_en'")
    if not src:
        errors.append("missing or empty field: 'source'")

    if errors:
        return {"valid": False, "errors": errors}

    vn_words = _word_count(vn)
    en_words = _word_count(en)

    # Determine word count mode based on category and source
    skip_word_count = (
        category in WORD_COUNT_EXEMPT_CATEGORIES
        or src in WORD_COUNT_EXEMPT_SOURCES
    )
    flexible = not skip_word_count and category in WORD_COUNT_FLEXIBLE_CATEGORIES

    # 2. Word count
    if skip_word_count:
        pass  # verbatim Google Sheets content — no word count enforced
    elif flexible:
        if vn_words < FLEXIBLE_MIN:
            errors.append(f"summary_vn too short ({vn_words} words), minimum {FLEXIBLE_MIN}")
        if en_words < FLEXIBLE_MIN:
            errors.append(f"summary_en too short ({en_words} words), minimum {FLEXIBLE_MIN}")
    else:
        if vn_words > WORD_MAX:
            errors.append(f"summary_vn word count is {vn_words}, must be ≤{WORD_MAX}")
        if en_words > WORD_MAX:
            errors.append(f"summary_en word count is {en_words}, must be ≤{WORD_MAX}")

    # 3. Both languages present and distinct
    if not skip_word_count and not flexible:
        if vn_words < LANG_MIN_WORDS:
            errors.append(f"summary_vn too short ({vn_words} words), minimum {LANG_MIN_WORDS}")
        if en_words < LANG_MIN_WORDS:
            errors.append(f"summary_en too short ({en_words} words), minimum {LANG_MIN_WORDS}")
    if vn.strip() == en.strip():
        errors.append("summary_vn and summary_en are identical - both languages required")

    # 4. Numbers preserved (only if source text provided)
    if source_text:
        source_nums = _extract_numbers(source_text)
        if source_nums:
            combined = vn + " " + en
            summary_nums = _extract_numbers(combined)
            missing = source_nums - summary_nums
            coverage = 1.0 - len(missing) / len(source_nums)
            if coverage < NUMBER_COVERAGE_MIN:
                errors.append(
                    f"numbers not preserved: {sorted(missing)} from source missing in summary "
                    f"(coverage {coverage:.0%}, minimum {NUMBER_COVERAGE_MIN:.0%})"
                )

    # 5. KIS Writing Style Check (only for LLM-generated items, i.e., non-exempt)
    if not skip_word_count:
        is_llm_summary = (category != "trading")
        
        # Check English style
        if en:
            if re.search(r"\b(?:VND|USD)\s+\d", en):
                errors.append("summary_en style error: space found between currency symbol and amount (e.g., use 'VND100bn', not 'VND 100bn')")
            if re.search(r"\d+\s*(?:billion|million|trillion|bln|mln|trn)\b", en, re.IGNORECASE):
                errors.append("summary_en style error: use 'bn', 'mn', 'tn' instead of full words or non-standard abbreviations (e.g., use 'VND100bn', not 'VND100 billion' or 'VND100 bln')")
            if re.search(r"\b(?:YoY|QoQ|YOY|QOQ|Yoy|Qoq)\b", en):
                errors.append("summary_en style error: use lowercase 'yoy', 'qoq' (not 'YoY', 'QoQ')")
            # if is_llm_summary and not re.match(r"^On \d+ [A-Za-z]+,", en.strip()):
            #     errors.append("summary_en style error: must start with date prefix matching format 'On D Month,' (e.g. 'On 16 June,')")
        
        # Check Vietnamese style
        if vn:
            if re.search(r"\b(?:yoy|qoq|YoY|QoQ|YOY|QOQ|N/N|Q/Q)\b", vn):
                errors.append("summary_vn style error: use lowercase 'n/n', 'q/q' instead of 'yoy', 'qoq' or uppercase 'N/N', 'Q/Q'")
            # if is_llm_summary and not re.match(r"^Ngày \d+/\d+,", vn.strip()):
            #     errors.append("summary_vn style error: must start with date prefix matching format 'Ngày D/M,' (e.g. 'Ngày 16/6,')")

    return {"valid": len(errors) == 0, "errors": errors}


def _extract_items(data: dict) -> tuple[list[dict], str]:
    """Returns (flat list of items, category string) from any JSON structure."""
    category = data.get("category", "") if isinstance(data, dict) else ""
    items = []

    if isinstance(data, dict):
        if "sectors" in data:
            for sector in data["sectors"]:
                items.extend(sector.get("items", []))
        elif "subtypes" in data:
            for subtype in data["subtypes"]:
                items.extend(subtype.get("items", []))
        elif "items" in data:
            items = data["items"]
    elif isinstance(data, list):
        items = data

    return items, category


def validate_file(json_path: Path) -> list[dict]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    items, category = _extract_items(data)
    results = []
    for i, item in enumerate(items):
        result = validate_item(item, category)
        result["index"] = i
        result["title"] = item.get("title_vn") or item.get("title_en") or item.get("title", f"item[{i}]")
        results.append(result)
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python harness.py <json_file>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    results = validate_file(path)
    passed = sum(1 for r in results if r["valid"])
    total = len(results)

    if total == 0:
        print(f"\nHarness validation: 0 items found in {path.name}")
        print("  ERROR: No items extracted — check JSON structure (expected sectors/subtypes/items)")
        sys.exit(1)

    print(f"\nHarness validation: {passed}/{total} passed\n")
    for r in results:
        status = "PASS" if r["valid"] else "FAIL"
        title_display = r["title"]
        if isinstance(title_display, str):
            title_display = title_display[:60]
        print(f"  {status} [{r['index']}] {title_display}")
        for err in r["errors"]:
            print(f"      ERROR: {err}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
