import re
import json
import math
from pathlib import Path

import sys

BASE_DIR = Path(__file__).resolve().parents[2]

def main():
    if len(sys.argv) > 1:
        base = sys.argv[1]
    else:
        base = "mor_10_06_2026"
    filepath = BASE_DIR / "reports" / base / "source" / f"{base}_full.md"
    if not filepath.exists():
        print(f"Error: File {filepath} does not exist.")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by section
    sections = re.split(r'(?=\n## )', content)
    articles_list = []

    for section in sections:
        sec_match = re.match(r'\n## (.*?)\n', section)
        if not sec_match:
            continue
        sec_title = sec_match.group(1).strip()
        
        # Split section into articles
        articles = re.split(r'(?=\n### )', section)
        # Skip the first split since it's the section header itself
        articles = articles[1:]
        
        for article in articles:
            # Title
            title_match = re.match(r'\n### (.*?)\n', article)
            title = title_match.group(1).strip() if title_match else ""
            
            # Source & Category line
            src_match = re.search(r'\*\*Source:\*\*\s*(.*?)\s*\*\*Category:\*\*', article)
            source = src_match.group(1).strip() if src_match else ""
            if not source:
                 src_match = re.search(r'\*\*Source:\*\*\s*(.*?)(?:\*\*Category:\*\*|$)', article)
                 source = src_match.group(1).strip() if src_match else ""

            # URL line
            url_match = re.search(r'\*\*URL:\*\*\s*<(.*?)>', article)
            url = url_match.group(1).strip() if url_match else ""
            
            # Published date line
            pub_match = re.search(r'\*\*Published:\*\*\s*(.*?)\n', article)
            published = pub_match.group(1).strip() if pub_match else ""
            
            # Content
            content_split = article.split("**Full Content:**")
            body = content_split[1].strip() if len(content_split) > 1 else ""
            
            # Strip trailing hyphens or lines
            body = re.sub(r'\n\s*---\s*$', '', body).strip()
            
            articles_list.append({
                'section': sec_title,
                'title': title,
                'source': source,
                'url': url,
                'published': published,
                'body': body
            })

    print(f"Total articles parsed: {len(articles_list)}")

    out_dir = BASE_DIR / "reports" / base / "source"
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "articles_parsed.json", "w", encoding="utf-8") as out:
        json.dump(articles_list, out, ensure_ascii=False, indent=2)
    print(f"Saved parsed articles to {out_dir / 'articles_parsed.json'}")

    # Split into 4 chunks
    num_chunks = 4
    chunk_size = math.ceil(len(articles_list) / num_chunks)

    prefix = "mor_chunk" if base.startswith("mor") else "after_chunk"
    for i in range(num_chunks):
        chunk = articles_list[i * chunk_size : (i + 1) * chunk_size]
        chunk_path = out_dir / f"{prefix}_{i}.json"
        with open(chunk_path, "w", encoding="utf-8") as out:
            json.dump(chunk, out, ensure_ascii=False, indent=2)
        print(f"Created {chunk_path} with {len(chunk)} articles.")

if __name__ == "__main__":
    main()
