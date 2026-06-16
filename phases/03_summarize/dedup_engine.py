"""
Semantic deduplication engine for news summaries.
Uses sentence-transformers (multilingual) + local NPZ index.

Usage:
  python dedup_engine.py <json_dir> [--threshold 0.75]
  python dedup_engine.py <json_dir> --add-to-index  (after HITL confirmation)
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_THRESHOLD = 0.75
ROLLING_DAYS = 30
INDEX_PATH = Path(__file__).resolve().parent / "dedup_index.npz"


def _load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def _item_title(item: dict) -> str:
    return item.get("title_en") or item.get("title_vn") or item.get("title", "")


def _item_text(item: dict) -> str:
    parts = [
        _item_title(item),
        item.get("summary_vn", ""),
        item.get("summary_en", ""),
    ]
    return " ".join(p for p in parts if p)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return vectors / norms


def _load_index(index_path: Path) -> dict:
    if not index_path.exists():
        return {"embeddings": np.empty((0, 384)), "titles": [], "dates": [], "report_ids": []}
    data = np.load(index_path, allow_pickle=True)
    return {
        "embeddings": data["embeddings"],
        "titles": list(data["titles"]),
        "dates": list(data["dates"]),
        "report_ids": list(data["report_ids"]),
    }


def _prune_old(index: dict, days: int = ROLLING_DAYS) -> dict:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    keep = [i for i, d in enumerate(index["dates"]) if str(d) >= cutoff]
    if not keep:
        return {"embeddings": np.empty((0, 384)), "titles": [], "dates": [], "report_ids": []}
    return {
        "embeddings": index["embeddings"][keep],
        "titles": [index["titles"][i] for i in keep],
        "dates": [index["dates"][i] for i in keep],
        "report_ids": [index["report_ids"][i] for i in keep],
    }


def check_duplicates(
    items: list[dict],
    index_path: Path = INDEX_PATH,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict]:
    """
    Returns items list with duplicate metadata added to flagged items:
      item["dup_score"], item["dup_match_title"], item["dup_match_date"]
    Non-flagged items are returned unchanged.
    """
    index = _prune_old(_load_index(index_path))
    if index["embeddings"].shape[0] == 0:
        return items

    model = _load_model()
    texts = [_item_text(item) for item in items]
    new_embeddings = _normalize(model.encode(texts, show_progress_bar=False))
    index_embeddings = _normalize(index["embeddings"])

    similarity_matrix = new_embeddings @ index_embeddings.T

    annotated = []
    for i, item in enumerate(items):
        sims = similarity_matrix[i]
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])
        if best_score >= threshold:
            item = dict(item)
            item["dup_score"] = round(best_score, 3)
            item["dup_match_title"] = index["titles"][best_idx]
            item["dup_match_date"] = index["dates"][best_idx]
        annotated.append(item)

    return annotated


def add_to_index(
    items: list[dict],
    index_path: Path = INDEX_PATH,
    report_id: str = "",
) -> None:
    """Appends confirmed (kept) items to the NPZ index."""
    model = _load_model()
    texts = [_item_text(item) for item in items]
    new_embeddings = model.encode(texts, show_progress_bar=False)

    today = datetime.now().strftime("%Y-%m-%d")
    new_titles = [_item_title(item) for item in items]
    new_dates = [today] * len(items)
    new_ids = [report_id] * len(items)

    existing = _load_index(index_path)
    merged_embeddings = (
        np.vstack([existing["embeddings"], new_embeddings])
        if existing["embeddings"].shape[0] > 0
        else new_embeddings
    )
    merged_titles = existing["titles"] + new_titles
    merged_dates = existing["dates"] + new_dates
    merged_ids = existing["report_ids"] + new_ids

    np.savez(
        index_path,
        embeddings=merged_embeddings,
        titles=np.array(merged_titles, dtype=object),
        dates=np.array(merged_dates, dtype=object),
        report_ids=np.array(merged_ids, dtype=object),
    )
    print(f"Index updated: {len(merged_titles)} total entries in {index_path.name}")


def _extract_items_from(data) -> list[dict]:
    """Flatten any JSON structure into a list of item dicts."""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    if "sectors" in data:
        return [item for s in data["sectors"] for item in s.get("items", [])]
    if "subtypes" in data:
        return [item for s in data["subtypes"] for item in s.get("items", [])]
    if "items" in data:
        return data["items"]
    return [data]


def _load_json_dir(json_dir: Path) -> list[dict]:
    items = []
    for f in sorted(json_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        items.extend(_extract_items_from(data))
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_dir", help="Directory containing JSON files for current session")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--add-to-index", action="store_true",
                        help="Add items to index instead of checking duplicates")
    parser.add_argument("--report-id", default="", help="Report ID for index metadata")
    parser.add_argument("--index", default=str(INDEX_PATH), help="Path to NPZ index file")
    args = parser.parse_args()

    json_dir = Path(args.json_dir)
    index_path = Path(args.index)

    if not json_dir.is_dir():
        print(f"Not a directory: {json_dir}")
        sys.exit(1)

    items = _load_json_dir(json_dir)
    if not items:
        print("No items found in JSON files.")
        sys.exit(0)

    if args.add_to_index:
        add_to_index(items, index_path, args.report_id)
        return

    print(f"\nChecking {len(items)} items against index (threshold={args.threshold})...\n")
    annotated = check_duplicates(items, index_path, args.threshold)

    flagged = [item for item in annotated if "dup_score" in item]
    clean = [item for item in annotated if "dup_score" not in item]

    print(f"  {len(clean)} clean  |  {len(flagged)} flagged\n")
    for item in flagged:
        title = _item_title(item) or "?"
        print(f"  FLAG [{item['dup_score']:.0%}] {title[:60]}")
        print(f"      Past: \"{item['dup_match_title'][:60]}\" ({item['dup_match_date']})")


if __name__ == "__main__":
    main()
