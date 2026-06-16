from __future__ import annotations

from typing import Any


CATEGORIES = ("macro", "trading", "corporate", "economy_political_others")
FEED_CATEGORIES = ("corporate", "economy_political_others")

SECTION_TITLES = {
    "macro": {"vn": "KINH TẾ VĨ MÔ", "en": "Macro indicators"},
    "trading": {"vn": "GIAO DỊCH", "en": "Trading"},
    "corporate": {"vn": "DOANH NGHIỆP", "en": "Corporate"},
    "economy_political_others": {
        "vn": "KINH TẾ - CHÍNH TRỊ - KHÁC",
        "en": "Economy - Politics - Others",
    },
}

SECTOR_TITLES = {
    "banking": {"vn": "NGÂN HÀNG", "en": "Banking"},
    "financials": {"vn": "TÀI CHÍNH", "en": "Financials"},
    "consumers": {"vn": "TIÊU DÙNG", "en": "Consumers"},
    "industrials": {"vn": "CÔNG NGHIỆP", "en": "Industrials"},
    "materials": {"vn": "NGUYÊN VẬT LIỆU", "en": "Materials"},
    "real_estate": {"vn": "BẤT ĐỘNG SẢN", "en": "Real Estate"},
    "technologies": {"vn": "CÔNG NGHỆ", "en": "Technologies"},
    "pharma": {"vn": "DƯỢC PHẨM", "en": "Pharma"},
    "utilities": {"vn": "TIỆN ÍCH", "en": "Utilities"},
    "oil_gas": {"vn": "DẦU KHÍ", "en": "Oil & Gas"},
}

SUBTYPE_TITLES = {
    "economies_investments": {"vn": "KINH TẾ & ĐẦU TƯ", "en": "Economy & Investments"},
    "political": {"vn": "CHÍNH TRỊ", "en": "Political"},
    "policies": {"vn": "CHÍNH SÁCH", "en": "Policies"},
    "social": {"vn": "XÃ HỘI", "en": "Social"},
    "commodities": {"vn": "HÀNG HÓA", "en": "Commodities"},
    "international_relation": {"vn": "QUAN HỆ QUỐC TẾ", "en": "International Relations"},
    "others": {"vn": "KHÁC", "en": "Others"},
}

COMMON_ITEM_FIELDS = {
    "order",
    "title_vn",
    "title_en",
    "summary_vn",
    "summary_en",
    "source",
    "url",
    "published",
}
CORPORATE_ITEM_FIELDS = COMMON_ITEM_FIELDS | {"ticker", "exchange", "company_vn", "company_en"}
TOP_LEVEL_FIELDS = {
    "report",
    "session",
    "category",
    "generated_at",
    "item_count",
}
STRICT_TOP_LEVEL_FIELDS = TOP_LEVEL_FIELDS | {"section_title_vn", "section_title_en"}


def validate_summary_payload(data: dict[str, Any], category: str, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    missing_top = sorted((STRICT_TOP_LEVEL_FIELDS if strict else TOP_LEVEL_FIELDS) - data.keys())
    if missing_top:
        errors.append(f"{category}: missing top-level fields: {', '.join(missing_top)}")

    if data.get("category") != category:
        errors.append(f"{category}: category field must be {category!r}")

    expected_title = SECTION_TITLES.get(category)
    if strict and expected_title:
        _check_title_fields(errors, data, category, expected_title)

    item_count = _validate_items(errors, data, category, strict=strict)
    if data.get("item_count") != item_count:
        errors.append(f"{category}: item_count is {data.get('item_count')}, expected {item_count}")
    return errors


def total_item_count(payloads: list[dict[str, Any]]) -> int:
    return sum(int(payload.get("item_count") or 0) for payload in payloads)


def _validate_items(errors: list[str], data: dict[str, Any], category: str, *, strict: bool) -> int:
    if category in ("macro", "trading"):
        return _check_items(errors, data.get("items", []), category, COMMON_ITEM_FIELDS)
    if category == "corporate":
        return _check_grouped_items(errors, data.get("sectors", []), category, ("sector_key",), SECTOR_TITLES, CORPORATE_ITEM_FIELDS, strict)
    if category == "economy_political_others":
        return _check_grouped_items(errors, data.get("subtypes", []), category, ("subtype", "subtype_key"), SUBTYPE_TITLES, COMMON_ITEM_FIELDS, strict)
    errors.append(f"{category}: unsupported category")
    return 0


def _check_grouped_items(
    errors: list[str],
    groups: Any,
    category: str,
    key_fields: tuple[str, ...],
    title_map: dict[str, dict[str, str]],
    required_fields: set[str],
    strict: bool,
) -> int:
    if not isinstance(groups, list):
        errors.append(f"{category}: grouped collection must be a list")
        return 0

    count = 0
    for group_index, group in enumerate(groups, 1):
        key = next((group.get(field) for field in key_fields if group.get(field)), None)
        label = f"{category}.{key or group_index}"
        if key not in title_map:
            errors.append(f"{label}: invalid {'/'.join(key_fields)}")
        elif strict and isinstance(group, dict):
            _check_title_fields(errors, group, label, title_map[key])
        count += _check_items(errors, group.get("items", []), label, required_fields)
    return count


def _check_items(errors: list[str], items: Any, label: str, required_fields: set[str]) -> int:
    if not isinstance(items, list):
        errors.append(f"{label}: items must be a list")
        return 0

    for index, item in enumerate(items, 1):
        missing = sorted(required_fields - item.keys())
        if missing:
            errors.append(f"{label}.items[{index}]: missing fields: {', '.join(missing)}")
    return len(items)


def _check_title_fields(errors: list[str], obj: dict[str, Any], label: str, titles: dict[str, str]) -> None:
    if _fold_title(obj.get("section_title_vn")) != _fold_title(titles["vn"]):
        errors.append(f"{label}: section_title_vn should be {titles['vn']!r}")
    if _fold_title(obj.get("section_title_en")) != _fold_title(titles["en"]):
        errors.append(f"{label}: section_title_en should be {titles['en']!r}")


def _fold_title(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())
