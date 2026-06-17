#!/usr/bin/env python3
"""
Intra-session semantic dedup harness for TAKE articles.

Detects pairs of articles within the same session that are semantically
similar (likely covering the same story from different sources).

Runs AFTER prepare_chunks.py produces articles_parsed.json and BEFORE
subagent summarization begins.

Usage:
    # Check for duplicates (console output + writes dedup_review.json for agent)
    python dedup_source.py <base> [--threshold 0.80]

    # Auto-drop shorter duplicates without agent review
    python dedup_source.py <base> --threshold 0.80 --auto-drop

    # Apply agent decisions from dedup_review.json (after agent marks drop indices)
    python dedup_source.py <base> --apply-decisions

Output:
    - Console report of flagged duplicate pairs
    - reports/{base}/source/dedup_review.json  — structured review for LLM agent
    - Exit code 0 if no duplicates, 1 if duplicates found
    - With --auto-drop: writes cleaned articles_parsed.json and re-chunks
    - With --apply-decisions: reads dedup_review.json, drops marked articles, re-chunks

Threshold guidance:
    >= 0.92  Almost certainly the same article republished
    0.85-0.92  Very likely same story, different source
    0.75-0.85  Similar topic, may be distinct angles
    < 0.75  Different stories
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_THRESHOLD = 0.30
BODY_EXCERPT_LEN = 500  # chars of body to include in the review file

BASE_DIR = Path(__file__).resolve().parents[2]

STOPWORDS = {
    # Vietnamese common stop words / grammatical particles
    "và", "của", "các", "để", "là", "trong", "cho", "đã", "đang", "sẽ", "có", "một", "với", "như", "được", "bị", "từ", "ra", "vào",
    # English common stop words
    "the", "and", "of", "to", "in", "is", "for", "on", "with", "at", "by", "an", "be", "this", "that", "it", "from", "as", "are", "was"
}


def _tokenize(text: str) -> set[str]:
    """Lowercase, remove punctuation, and extract set of words."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = cleaned.split()
    return {w for w in words if len(w) >= 2 and w not in STOPWORDS}


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))


def _article_text(article: dict) -> str:
    """Combine title + body into a single text for embedding."""
    parts = [
        article.get("title", ""),
        article.get("body", "")[:1000],
    ]
    return " ".join(p for p in parts if p)


def find_intra_session_duplicates(
    articles: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict]:
    """
    Compare all articles against each other within the same session using Jaccard similarity.
    Returns a list of duplicate pairs with metadata.
    """
    if len(articles) < 2:
        return []

    tokenized = [_tokenize(_article_text(a)) for a in articles]

    pairs = []
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            score = _jaccard_similarity(tokenized[i], tokenized[j])
            if score >= threshold:
                pairs.append({
                    "i": i,
                    "j": j,
                    "score": round(score, 3),
                    "title_i": articles[i].get("title", "")[:100],
                    "title_j": articles[j].get("title", "")[:100],
                    "source_i": articles[i].get("source", ""),
                    "source_j": articles[j].get("source", ""),
                })

    pairs.sort(key=lambda p: -p["score"])
    return pairs


def build_review_file(
    articles: list[dict], pairs: list[dict], base: str, threshold: float
) -> dict:
    """
    Build a structured JSON review object that an LLM agent can read to
    decide whether each flagged pair is a true duplicate or a false positive.

    Each pair includes excerpts from both articles so the agent can compare
    content without needing to read the full source files.
    """
    review_pairs = []
    for pair_idx, p in enumerate(pairs):
        i, j = p["i"], p["j"]
        a_i, a_j = articles[i], articles[j]
        body_i = a_i.get("body", "")
        body_j = a_j.get("body", "")

        review_pairs.append({
            "pair_id": pair_idx,
            "similarity": p["score"],
            "article_a": {
                "index": i,
                "title": a_i.get("title", ""),
                "source": a_i.get("source", ""),
                "url": a_i.get("url", ""),
                "body_length": len(body_i),
                "body_excerpt": body_i[:BODY_EXCERPT_LEN],
            },
            "article_b": {
                "index": j,
                "title": a_j.get("title", ""),
                "source": a_j.get("source", ""),
                "url": a_j.get("url", ""),
                "body_length": len(body_j),
                "body_excerpt": body_j[:BODY_EXCERPT_LEN],
            },
            # Agent fills this in:
            "decision": None,       # "keep_both" | "drop_a" | "drop_b"
            "reason": None,         # Agent's explanation
        })

    return {
        "report": base,
        "threshold": threshold,
        "total_articles": len(articles),
        "flagged_pairs": len(review_pairs),
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
        "instructions": (
            "For each flagged pair, set 'decision' to one of: "
            "'keep_both' (different stories), 'drop_a' (drop article_a, keep article_b), "
            "or 'drop_b' (drop article_b, keep article_a). "
            "Set 'reason' to a brief explanation. "
            "Then run: dedup_source.py <base> --apply-decisions"
        ),
        "pairs": review_pairs,
    }


def _rechunk(articles: list[dict], source_dir: Path, base: str) -> None:
    """Rewrite chunk files from the filtered article list."""
    num_chunks = 4
    chunk_size = math.ceil(len(articles) / num_chunks) if articles else 1
    prefix = "mor_chunk" if base.startswith("mor") else "after_chunk"
    for i in range(num_chunks):
        chunk = articles[i * chunk_size: (i + 1) * chunk_size]
        chunk_path = source_dir / f"{prefix}_{i}.json"
        with open(chunk_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        print(f"  Re-chunked: {chunk_path.name} ({len(chunk)} articles)")


def apply_decisions(base: str) -> None:
    """Read dedup_review.json, apply agent decisions, rewrite articles + chunks."""
    source_dir = BASE_DIR / "reports" / base / "source"
    review_path = source_dir / "dedup_review.json"
    parsed_path = source_dir / "articles_parsed.json"

    if not review_path.exists():
        print(f"Error: {review_path} does not exist. Run dedup check first.")
        sys.exit(1)
    if not parsed_path.exists():
        print(f"Error: {parsed_path} does not exist.")
        sys.exit(1)

    with open(review_path, encoding="utf-8") as f:
        review = json.load(f)
    with open(parsed_path, encoding="utf-8") as f:
        articles = json.load(f)

    drop_indices = set()
    for pair in review.get("pairs", []):
        decision = pair.get("decision")
        if decision == "drop_a":
            drop_indices.add(pair["article_a"]["index"])
        elif decision == "drop_b":
            drop_indices.add(pair["article_b"]["index"])
        elif decision == "keep_both":
            pass
        elif decision is None:
            print(f"  WARNING: pair {pair['pair_id']} has no decision, skipping")
        else:
            print(f"  WARNING: pair {pair['pair_id']} has unknown decision '{decision}', skipping")

    if not drop_indices:
        print("  No articles to drop. All pairs marked as keep_both.")
        sys.exit(0)

    kept = [a for idx, a in enumerate(articles) if idx not in drop_indices]
    print(f"  Dropping {len(drop_indices)} article(s): indices {sorted(drop_indices)}")
    print(f"  Remaining: {len(kept)} articles")

    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)
    print(f"  Updated: {parsed_path}")

    _rechunk(kept, source_dir, base)
    print()


def auto_drop_duplicates(articles: list[dict], pairs: list[dict]) -> tuple[list[dict], set[int]]:
    """
    For each duplicate pair, keep the article with the longer body text
    and drop the shorter one.
    """
    drop_indices = set()
    for pair in pairs:
        i, j = pair["i"], pair["j"]
        if i in drop_indices or j in drop_indices:
            continue
        body_i = len(articles[i].get("body", ""))
        body_j = len(articles[j].get("body", ""))
        if body_i >= body_j:
            drop_indices.add(j)
        else:
            drop_indices.add(i)

    kept = [a for idx, a in enumerate(articles) if idx not in drop_indices]
    return kept, drop_indices


def main():
    parser = argparse.ArgumentParser(
        description="Detect semantically duplicate TAKE articles within the same session."
    )
    parser.add_argument("base", help="Report base, e.g. after_16_06_2026")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Cosine similarity threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--auto-drop", action="store_true",
                        help="Automatically drop the shorter duplicate and rewrite articles_parsed.json")
    parser.add_argument("--apply-decisions", action="store_true",
                        help="Apply agent decisions from dedup_review.json")
    args = parser.parse_args()

    # --- Apply decisions mode ---
    if args.apply_decisions:
        print(f"\nApplying dedup decisions for {args.base}...\n")
        apply_decisions(args.base)
        return

    # --- Detection mode ---
    source_dir = BASE_DIR / "reports" / args.base / "source"
    parsed_path = source_dir / "articles_parsed.json"

    if not parsed_path.exists():
        print(f"Error: {parsed_path} does not exist.")
        print("Run prepare_chunks.py first to generate articles_parsed.json.")
        sys.exit(1)

    with open(parsed_path, encoding="utf-8") as f:
        articles = json.load(f)

    # Convert ST threshold to Jaccard threshold if it looks like ST range
    if args.threshold >= 0.60:
        jaccard_threshold = 0.30 + (args.threshold - 0.80) * 1.5
        jaccard_threshold = max(0.10, min(0.95, jaccard_threshold))
        print(f"  Note: Cosine threshold {args.threshold} mapped to Jaccard threshold {jaccard_threshold:.2f}")
    else:
        jaccard_threshold = args.threshold

    print(f"\nIntra-session Jaccard dedup check: {len(articles)} articles (threshold={jaccard_threshold:.2f})\n")

    pairs = find_intra_session_duplicates(articles, jaccard_threshold)

    if not pairs:
        print("  ✓ No intra-session duplicates found.\n")
        sys.exit(0)

    print(f"  ⚠ Found {len(pairs)} potential duplicate pair(s):\n")
    for p in pairs:
        print(f"  [{p['score']:.0%}] PAIR:")
        print(f"    [{p['i']}] ({p['source_i']}) {p['title_i']}")
        print(f"    [{p['j']}] ({p['source_j']}) {p['title_j']}")
        print()

    # Always write the review file for agent consumption
    review = build_review_file(articles, pairs, args.base, jaccard_threshold)
    review_path = source_dir / "dedup_review.json"
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)
    print(f"  Review file written: {review_path}")
    print(f"  → Agent: read this file, set 'decision' for each pair, then run:")
    print(f"    dedup_source.py {args.base} --apply-decisions\n")

    if args.auto_drop:
        kept, dropped = auto_drop_duplicates(articles, pairs)
        print(f"  Auto-dropped {len(dropped)} article(s): indices {sorted(dropped)}")
        print(f"  Remaining: {len(kept)} articles")

        with open(parsed_path, "w", encoding="utf-8") as f:
            json.dump(kept, f, ensure_ascii=False, indent=2)
        print(f"  Updated: {parsed_path}")

        _rechunk(kept, source_dir, args.base)
        print()

    sys.exit(1)  # Non-zero = duplicates found (for pipeline gating)


if __name__ == "__main__":
    main()
