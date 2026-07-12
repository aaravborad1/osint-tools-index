#!/usr/bin/env python3
"""
Scrapes the live OSINT4ALL GitHub Pages mirror and writes data/tools.json.

This is the PRODUCTION data source. It replaces scripts/parse_markdown_sample.py
once you're running this in CI (GitHub Actions runners have normal internet
access; this repo's sandboxed dev environment may not).

Usage:
    python3 scripts/scrape_source.py

Env vars:
    SOURCE_URL   override the page to scrape (default: osint4all.github.io)
"""
import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "tools.json"

SOURCE_URL = os.environ.get("SOURCE_URL", "https://osint4all.github.io/")
ORIGINAL_URL = "https://start.me/p/L1rEYQ/osint4all"

SKIP_LINK_TEXT = {"github pages", "published with"}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def main():
    resp = requests.get(SOURCE_URL, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (compatible; osint4all-index-bot/1.0)"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the main content container; fall back to <body> if no article/main tag.
    content = soup.find("article") or soup.find("main") or soup.body

    categories = []
    current = None
    seen_in_current = set()

    for el in content.descendants:
        if getattr(el, "name", None) == "h2":
            name = el.get_text(strip=True)
            if not name:
                continue
            current = {"name": name, "slug": slugify(name), "tools": []}
            seen_in_current = set()
            categories.append(current)
        elif getattr(el, "name", None) == "a" and current is not None:
            href = el.get("href", "").strip()
            label = el.get_text(strip=True)
            if not href or not label:
                continue
            if href.startswith("#") or "github.com/pages" in href:
                continue
            if label.lower() in SKIP_LINK_TEXT:
                continue
            key = (label, href)
            if key in seen_in_current:
                continue
            seen_in_current.add(key)
            current["tools"].append({
                "name": label,
                "url": href,
                "status": None,
                "status_code": None,
                "checked_at": None,
            })

    categories = [c for c in categories if c["tools"]]
    total = sum(len(c["tools"]) for c in categories)

    if total < 100:
        # Sanity check: the real page has ~900+ links. If parsing broke
        # (site structure changed), fail loudly instead of overwriting
        # good data with a near-empty file.
        print(f"ERROR: only found {total} tools across {len(categories)} "
              f"categories — the page structure may have changed. Aborting.",
              file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": ORIGINAL_URL,
        "scraped_from": SOURCE_URL,
        "categories": categories,
    }, indent=2), encoding="utf-8")

    print(f"Scraped {len(categories)} categories, {total} tools -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
