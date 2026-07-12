#!/usr/bin/env python3
"""
Checks every URL in data/tools.json concurrently and records whether it's
alive. Updates the same file in place with status/status_code/checked_at.

Usage:
    python3 scripts/check_links.py

Tuning via env vars:
    CONCURRENCY   max simultaneous requests (default 40)
    TIMEOUT       per-request timeout in seconds (default 12)
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiohttp

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tools.json"

CONCURRENCY = int(os.environ.get("CONCURRENCY", "40"))
TIMEOUT = float(os.environ.get("TIMEOUT", "12"))
USER_AGENT = "Mozilla/5.0 (compatible; osint4all-index-bot/1.0; +link-checker)"


async def check_one(session, tool, sem):
    async with sem:
        url = tool["url"]
        status = "dead"
        code = None
        try:
            # Try HEAD first (cheaper); fall back to GET since many sites
            # reject HEAD or handle it inconsistently.
            async with session.head(url, allow_redirects=True) as resp:
                code = resp.status
                if code < 400:
                    status = "alive"
                else:
                    raise aiohttp.ClientResponseError(
                        resp.request_info, resp.history, status=code)
        except Exception:
            try:
                async with session.get(url, allow_redirects=True) as resp:
                    code = resp.status
                    status = "alive" if code < 400 else "dead"
            except Exception:
                status = "dead"
                code = None

        tool["status"] = status
        tool["status_code"] = code
        tool["checked_at"] = datetime.now(timezone.utc).isoformat()


async def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    all_tools = [t for cat in data["categories"] for t in cat["tools"]]

    sem = asyncio.Semaphore(CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)

    async with aiohttp.ClientSession(
        timeout=timeout, connector=connector,
        headers={"User-Agent": USER_AGENT}
    ) as session:
        tasks = [check_one(session, t, sem) for t in all_tools]
        done = 0
        for coro in asyncio.as_completed(tasks):
            await coro
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"checked {done}/{len(tasks)}", file=sys.stderr)

    alive = sum(1 for t in all_tools if t["status"] == "alive")
    dead = sum(1 for t in all_tools if t["status"] == "dead")

    data["last_checked"] = datetime.now(timezone.utc).isoformat()
    data["link_stats"] = {"alive": alive, "dead": dead, "total": len(all_tools)}

    DATA.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Done: {alive} alive, {dead} dead, {len(all_tools)} total")


if __name__ == "__main__":
    asyncio.run(main())
