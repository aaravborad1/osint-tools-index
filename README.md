# OSINT Index

A categorized, automatically link-checked mirror of the [OSINT4ALL](https://start.me/p/L1rEYQ/osint4all)
tool collection — more then 900+ OSINT tools, organized by category, rebuilt weekly with fresh
"is this link still alive" status.

## How it works

1. **`scripts/scrape_source.py`** — pulls the live tool list from the
   [osint4all.github.io](https://osint4all.github.io/) mirror (categories = `<h2>`,
   tools = the links under each) into `data/tools.json`.
2. **`scripts/check_links.py`** — concurrently pings every URL (HEAD, falling back to GET)
   and records `alive` / `dead` + status code + timestamp.
3. **`scripts/build_site.py`** — renders `data/tools.json` into a static site in `site/`:
   one page per category, a searchable index, `sitemap.xml`, and `robots.txt` for
   Google indexing.
4. **GitHub Actions** (`.github/workflows/build-and-deploy.yml`) runs all three every
   Monday, commits the refreshed data, and deploys `site/` to GitHub Pages.

## Setting this up yourself

1. Push this folder to a new GitHub repo.
2. In **Settings → Pages**, set the source to **GitHub Actions**.
3. In **Settings → Actions → General**, under "Workflow permissions," select
   **"Read and write permissions"** (needed so the workflow can commit the
   refreshed `data/tools.json`).
4. Push to `main` (or run the workflow manually from the **Actions** tab) — the
   first run scrapes, checks all links, builds, and deploys.
5. Your site will be live at `https://<your-username>.github.io/<repo-name>/`.
   Update `SITE_URL` at the top of `scripts/build_site.py` to match that URL so
   the sitemap and canonical tags are correct, then re-run.
6. Submit the sitemap (`/sitemap.xml`) in
   [Google Search Console](https://search.google.com/search-console) to get it
   indexed faster.

## Running locally (dev/preview only)

This sandbox couldn't reach arbitrary external sites, so it was built and
tested against `raw_data.md`, a manually captured sample of the source page —
NOT the full live list. To develop/preview locally with that sample:

```bash
pip install -r requirements.txt
python3 scripts/parse_markdown_sample.py   # sample data only, dev/test
python3 scripts/build_site.py
python3 -m http.server -d site 8000
```

For the real, complete dataset (all ~900+ tools) and live link-checking, let
GitHub Actions run it — that environment has normal internet access:

```bash
python3 scripts/scrape_source.py   # full live scrape
python3 scripts/check_links.py     # full live check
python3 scripts/build_site.py
```

## Project layout

```
data/tools.json          generated data (scrape + check results)
scripts/
  scrape_source.py       production scraper (run in CI)
  check_links.py         async link checker (run in CI)
  build_site.py          static site generator
  parse_markdown_sample.py  dev-only parser for the local sample
templates/base.html      shared page shell
static/css/style.css     styling
static/js/app.js         client-side search
site/                    build output (gitignored except via CI artifact)
```
