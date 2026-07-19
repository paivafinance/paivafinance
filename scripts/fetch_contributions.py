"""Fetch the public GitHub contribution calendar and derive stats.

No token needed: GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions -- the same fragment the
profile page itself renders. Output goes to data/contributions.json with the
raw days plus derived stats (streaks, best day, monthly totals).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "paivafinance"
URL = f"https://github.com/users/{USERNAME}/contributions"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def fetch_days() -> list[dict]:
    resp = requests.get(
        URL,
        headers={"User-Agent": f"Mozilla/5.0 (profile-art; +https://github.com/{USERNAME})"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        sys.exit("No contribution cells found -- GitHub may have changed the markup.")

    # Counts live in <tool-tip for="..."> elements ("3 contributions on July 4th.")
    tooltips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tooltips[target] = tip.get_text(strip=True)

    days = []
    for cell in cells:
        tip = tooltips.get(cell.get("id", ""), "")
        m = re.match(r"([\d,]+)\s+contribution", tip)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append(
            {
                "date": cell["data-date"],
                "count": count,
                "level": int(cell.get("data-level", 0)),
            }
        )
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)

    # Today may still be 0 because the day isn't over -- don't break the streak on it.
    tail = list(days)
    if tail and tail[-1]["count"] == 0:
        tail.pop()
    current = 0
    for day in reversed(tail):
        if day["count"] == 0:
            break
        current += 1
    return current, longest


def main() -> None:
    days = fetch_days()
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])

    monthly: dict[str, int] = {}
    for day in days:
        monthly[day["date"][:7]] = monthly.get(day["date"][:7], 0) + day["count"]

    total = sum(d["count"] for d in days)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "username": USERNAME,
                "fetched_on": days[-1]["date"],
                "total": total,
                "best_day": best,
                "current_streak": current,
                "longest_streak": longest,
                "monthly": monthly,
                "days": days,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{len(days)} days, {total} contributions -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
