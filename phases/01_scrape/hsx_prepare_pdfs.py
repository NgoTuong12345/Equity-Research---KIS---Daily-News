"""
HSX Insider Trading — PDF Downloader & Image Renderer

Downloads PDFs from the latest hsx_insider_trading_*.json and renders each
page to a PNG image that can be read by the AI agent for extraction.

This replaces the NLM-based extraction pipeline with a simpler approach:
  1. Download PDFs (same as before)
  2. Render each PDF page to a PNG image
  3. Save a manifest JSON that tells the agent what to process

Usage:
    python hsx_prepare_pdfs.py                  # auto-finds latest JSON
    python hsx_prepare_pdfs.py --input PATH     # explicit JSON path
    python hsx_prepare_pdfs.py --dry-run        # skip downloads, test plumbing
"""
from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

PDF_DIR = Path(__file__).resolve().parent / "pdfs"
IMAGES_DIR = Path(__file__).resolve().parent / "pdf_images"
OUTDIR = Path(__file__).resolve().parent


def download_pdf(url: str, dest: Path) -> bool:
    """Download PDF from staticfile.hsx.vn and verify signature."""
    try:
        import urllib.parse
        parsed = urllib.parse.urlsplit(url)
        encoded_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, urllib.parse.quote(parsed.path), parsed.query, parsed.fragment))
        resp = requests.get(encoded_url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            log.error(f"HTTP {resp.status_code} downloading {encoded_url}")
            return False
        if b"%PDF" not in resp.content[:1024]:
            log.error(f"Not a valid PDF: {url}")
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return True
    except Exception as e:
        log.error(f"Download failed for {url}: {e}")
        return False


def render_pdf_to_images(pdf_path: Path, output_dir: Path, scale: float = 2.0) -> list[Path]:
    """Render each page of a PDF to a PNG image. Returns list of image paths."""
    import pypdfium2

    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []

    try:
        pdf = pypdfium2.PdfDocument(str(pdf_path))
        for page_idx in range(len(pdf)):
            page = pdf[page_idx]
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()
            img_name = f"{pdf_path.stem}_p{page_idx + 1}.png"
            img_path = output_dir / img_name
            img.save(str(img_path), "PNG")
            image_paths.append(img_path)
        pdf.close()
        log.info(f"Rendered {len(image_paths)} page(s) from {pdf_path.name}")
    except Exception as e:
        log.error(f"Failed to render {pdf_path.name}: {e}")

    return image_paths


def extract_text_if_available(pdf_path: Path) -> str:
    """Try to extract text from PDF using pdfplumber and fitz fallback."""
    text_plumber = ""
    try:
        import pdfplumber
        pdf = pdfplumber.open(str(pdf_path))
        texts = [p.extract_text() for p in pdf.pages if p.extract_text()]
        pdf.close()
        text_plumber = "\n\n".join(texts).strip()
    except Exception:
        pass

    text_fitz = ""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        texts = [p.get_text() for p in doc if p.get_text()]
        text_fitz = "\n\n".join(texts).strip()
    except Exception:
        pass

    return text_plumber if len(text_plumber) >= len(text_fitz) else text_fitz


import re


def find_latest_json() -> Optional[Path]:
    """Find the latest hsx_insider_trading_*.json matching YYYYMMDD_HHMM.json exactly."""
    pattern = re.compile(r"^hsx_insider_trading_\d{8}_\d{4}\.json$")
    matches = []
    for p in OUTDIR.glob("hsx_insider_trading_*.json"):
        if pattern.match(p.name):
            matches.append(p)
    matches.sort(key=lambda x: x.name)
    return matches[-1] if matches else None


def run(json_path: Optional[Path] = None, dry_run: bool = False, scale: float = 2.0):
    if not json_path:
        json_path = find_latest_json()
    if not json_path or not json_path.exists():
        log.error("No hsx_insider_trading_*.json found. Run hsx_insider_scraper.py first.")
        sys.exit(1)

    log.info(f"Reading {json_path}")
    records = json.loads(json_path.read_text(encoding="utf-8"))

    # Build work queue: download PDFs and render to images
    manifest = []
    for rec in records:
        article_id = rec.get("article_id")
        pdf_urls = rec.get("pdf_urls") or []
        ticker = rec.get("ticker", "")
        title = rec.get("title", "")

        if not article_id or not pdf_urls:
            manifest.append({
                "article_id": article_id,
                "ticker": ticker,
                "title": title,
                "pdf_count": 0,
                "pdfs": [],
            })
            continue

        pdf_entries = []
        for idx, pdf_url in enumerate(pdf_urls):
            filename = f"{article_id}_{idx}.pdf"
            pdf_path = PDF_DIR / filename

            # Download if not cached
            if not pdf_path.exists():
                if dry_run:
                    log.info(f"[DRY-RUN] Would download {pdf_url}")
                    continue
                log.info(f"Downloading PDF for article {article_id} (part {idx})...")
                if not download_pdf(pdf_url, pdf_path):
                    continue
            else:
                log.info(f"PDF already cached: {pdf_path.name}")

            if dry_run:
                pdf_entries.append({
                    "pdf_path": str(pdf_path),
                    "image_paths": [],
                    "text": "",
                })
                continue

            # Render PDF pages to images
            article_img_dir = IMAGES_DIR / str(article_id)
            image_paths = render_pdf_to_images(pdf_path, article_img_dir, scale=scale)

            # Try text extraction too (for text-based PDFs)
            text = extract_text_if_available(pdf_path)

            pdf_entries.append({
                "pdf_path": str(pdf_path),
                "image_paths": [str(p) for p in image_paths],
                "text": text,
                "has_text_layer": bool(text),
            })

        manifest.append({
            "article_id": article_id,
            "ticker": ticker,
            "title": title,
            "url": rec.get("url", ""),
            "date": rec.get("date", ""),
            "pdf_count": len(pdf_entries),
            "pdfs": pdf_entries,
        })

    # Save manifest
    manifest_path = json_path.with_name(json_path.stem + "_manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_pdfs = sum(m["pdf_count"] for m in manifest)
    total_images = sum(
        len(p["image_paths"])
        for m in manifest
        for p in m["pdfs"]
    )

    log.info(f"Manifest saved: {manifest_path}")
    log.info(f"  Articles: {len(manifest)} | PDFs: {total_pdfs} | Images: {total_images}")
    log.info(f"  Source JSON: {json_path}")

    return manifest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HSX PDF downloader & image renderer")
    parser.add_argument("--input", type=Path, default=None, help="Path to hsx_insider_trading_*.json")
    parser.add_argument("--dry-run", action="store_true", help="Skip downloads, test plumbing")
    parser.add_argument("--scale", type=float, default=2.0, help="Image render scale (default 2.0)")
    args = parser.parse_args()
    run(json_path=args.input, dry_run=args.dry_run, scale=args.scale)
