#!/usr/bin/env python3
"""
DEV/TEST ONLY.

Parses the local markdown sample (raw_data.md) into data/tools.json so the
site builder can be developed and previewed without network access.

In production, data/tools.json is produced instead by scripts/scrape_source.py,
which scrapes the live osint4all.github.io mirror directly (see that script
and the GitHub Actions workflow for the real pipeline).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "raw_data.md"
OUT = ROOT / "data" / "tools.json"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def main():
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()

    categories = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            name = line[3:].strip()
            current = {
                "name": name,
                "slug": slugify(name),
                "tools": [],
            }
            categories.append(current)
            continue
        if line.startswith("# "):
            continue
        m = LINK_RE.search(line)
        if m and current is not None:
            name, url = m.group(1).strip(), m.group(2).strip()
            current["tools"].append({
                "name": name,
                "url": url,
                "status": None,          # filled in by check_links.py
                "status_code": None,
                "checked_at": None,
            })

    categories = [c for c in categories if c["tools"]]
    total = sum(len(c["tools"]) for c in categories)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "https://start.me/p/L1rEYQ/osint4all",
        "categories": categories,
    }, indent=2), encoding="utf-8")

    print(f"Parsed {len(categories)} categories, {total} tools -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
