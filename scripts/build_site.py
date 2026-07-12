#!/usr/bin/env python3
"""
Builds the static site into site/ from data/tools.json.

No templating engine dependency — base.html uses simple {{ placeholder }}
tokens replaced via str.replace, which is all this needs.

Usage:
    python3 scripts/build_site.py
"""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tools.json"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
SITE = ROOT / "site"

SITE_URL = "https://aaravborad1.github.io/osint-tools-index/"
SITE_NAME = "OSINT Index"


def render(template_name, **ctx):
    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")
    for key, val in ctx.items():
        tpl = tpl.replace("{{ " + key + " }}", str(val))
    return tpl


def stamp(status):
    if status == "alive":
        return '<span class="stamp alive mono">LIVE</span>'
    if status == "dead":
        return '<span class="stamp dead mono">DEAD</span>'
    return '<span class="stamp unknown mono">UNCHECKED</span>'


def build_index(data, tool_count, last_checked):
    cats = data["categories"]
    cards = []
    for cat in sorted(cats, key=lambda c: c["name"]):
        alive = sum(1 for t in cat["tools"] if t["status"] == "alive")
        n = len(cat["tools"])
        pct = f"{round(100 * alive / n)}%" if n and any(t["status"] for t in cat["tools"]) else "unchecked"
        cards.append(f'''
        <a class="cat-card" href="category/{cat["slug"]}.html">
          <span class="name">{html.escape(cat["name"])}</span>
          <span class="count">{n} tools &middot; {pct} live</span>
        </a>''')

    stats = data.get("link_stats", {})
    stats_html = ""
    if stats:
        stats_html = f'''
        <div class="stats">
          <span><b>{stats.get("total", 0)}</b> tools tracked</span>
          <span><b>{stats.get("alive", 0)}</b> live</span>
          <span><b>{stats.get("dead", 0)}</b> dead / unreachable</span>
          <span><b>{len(cats)}</b> categories</span>
        </div>'''

    content = f'''
    <p class="eyebrow">Field Index &mdash; OSINT Tools</p>
    <h1>A checked, categorized mirror of OSINT4ALL</h1>
    <p class="lede">Every tool from the <a href="https://start.me/p/L1rEYQ/osint4all" target="_blank" rel="noopener">OSINT4ALL</a> start.me collection, organized by category, with automated weekly checks for whether each link still resolves.</p>
    {stats_html}
    <div class="search-box">
      <input id="search-input" type="text" placeholder="Search all {tool_count} tools by name or domain&hellip;" autocomplete="off">
      <div id="search-count"></div>
      <div id="search-results"></div>
    </div>
    <h2>Browse by category</h2>
    <div class="cat-grid">
      {"".join(cards)}
    </div>
    <script src="static/js/app.js"></script>
    '''

    return render(
        "base.html",
        title=f"{SITE_NAME} — categorized, link-checked OSINT tool directory",
        description=f"A categorized, automatically link-checked mirror of the OSINT4ALL tool collection — {tool_count} tools across {len(cats)} categories.",
        path="index.html",
        rel="",
        site_url=SITE_URL,
        tool_count=tool_count,
        content=content,
        last_checked=last_checked,
    )


def build_category(cat, tool_count, last_checked):
    rows = []
    for t in cat["tools"]:
        rows.append(f'''
        <li class="tool-row">
          <span>
            <a class="tool-link" href="{html.escape(t["url"])}" target="_blank" rel="noopener">{html.escape(t["name"])}</a>
            <span class="url mono">{html.escape(t["url"])}</span>
          </span>
          {stamp(t["status"])}
        </li>''')

    content = f'''
    <p class="eyebrow"><a href="../index.html">&larr; All categories</a></p>
    <h1>{html.escape(cat["name"])}</h1>
    <p class="lede">{len(cat["tools"])} tools in this category, checked automatically for link health.</p>
    <ul class="tool-list">
      {"".join(rows)}
    </ul>
    '''

    return render(
        "base.html",
        title=f"{html.escape(cat['name'])} — {SITE_NAME}",
        description=f"{len(cat['tools'])} OSINT tools for {cat['name'].lower()}, link-checked automatically.",
        path=f"category/{cat['slug']}.html",
        rel="../",
        site_url=SITE_URL,
        tool_count=tool_count,
        content=content,
        last_checked=last_checked,
    )


def build_sitemap(cats):
    urls = [f"{SITE_URL}index.html"]
    urls += [f"{SITE_URL}category/{c['slug']}.html" for c in cats]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
'''


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cats = data["categories"]
    tool_count = sum(len(c["tools"]) for c in cats)
    last_checked = data.get("last_checked", "not yet checked")

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / "category").mkdir()
    shutil.copytree(STATIC, SITE / "static")
    (SITE / "data").mkdir()
    shutil.copy(DATA, SITE / "data" / "tools.json")

    (SITE / "index.html").write_text(build_index(data, tool_count, last_checked), encoding="utf-8")

    for cat in cats:
        (SITE / "category" / f"{cat['slug']}.html").write_text(
            build_category(cat, tool_count, last_checked), encoding="utf-8"
        )

    (SITE / "sitemap.xml").write_text(build_sitemap(cats), encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8"
    )
    (SITE / ".nojekyll").write_text("", encoding="utf-8")  # so GitHub Pages serves static/ as-is

    print(f"Built site: {len(cats)} category pages + index -> {SITE}")


if __name__ == "__main__":
    sys.exit(main())
