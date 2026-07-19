"""Render data/contributions.json as an animated 53-week heatmap SVG.

Pure stdlib. Cells reveal once with a diagonal line-after-line slide-down
(CSS keyframes that play on load, then freeze -- no looping), followed by a
fading-in stats footer and Less->More legend. Output: contrib-heatmap.svg.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, BORDER, FG, MUTED = "#0d1117", "#30363d", "#c9d1d9", "#8b949e"
CELL, PITCH = 11, 13
PADX, PADY = 26, 40
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Consolas,Menlo,monospace"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days = data["days"]
    best_count = max((d["count"] for d in days), default=0)

    first = date.fromisoformat(days[0]["date"])
    start_sunday = first - timedelta(days=(first.weekday() + 1) % 7)

    cells = []
    n_weeks = 0
    for d in days:
        day = date.fromisoformat(d["date"])
        week = (day - start_sunday).days // 7
        weekday = (day.weekday() + 1) % 7  # Sunday = 0, GitHub's convention
        n_weeks = max(n_weeks, week + 1)
        x = PADX + week * PITCH
        y = PADY + weekday * PITCH
        # level 5 is the neon top end, reserved for the best day of the year
        idx = 5 if d["count"] and d["count"] == best_count else min(d["level"], 4)
        delay = (week + weekday) * 0.02
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[idx]}" style="animation-delay:{delay:.2f}s"/>'
        )

    width = PADX * 2 + n_weeks * PITCH - (PITCH - CELL)
    grid_bottom = PADY + 7 * PITCH - (PITCH - CELL)
    footer_y = grid_bottom + 30
    height = footer_y + 20

    month_labels = []
    prev_month = None
    for w in range(n_weeks):
        sunday = start_sunday + timedelta(weeks=w)
        if sunday.month != prev_month:
            prev_month = sunday.month
            # skip partial first months and labels glued to the right edge
            if sunday.day <= 7 and w <= n_weeks - 3:
                month_labels.append(
                    f'<text class="f" x="{PADX + w * PITCH}" y="{PADY - 12}" '
                    f'font-size="11" fill="{MUTED}">{sunday.strftime("%b")}</text>'
                )

    noun = "contribution" if data["total"] == 1 else "contributions"
    stats = (
        f'{data["total"]:,} {noun} in the last year'
        f'  ·  streak {data["current_streak"]}d'
        f'  ·  longest {data["longest_streak"]}d'
    )

    more_x = width - PADX
    swatch_end = more_x - 42
    legend = [
        f'<text class="f" x="{more_x}" y="{footer_y}" font-size="11" fill="{MUTED}" '
        f'text-anchor="end">More</text>'
    ]
    for i, color in enumerate(PALETTE):
        legend.append(
            f'<rect class="f" x="{swatch_end - (len(PALETTE) - i) * PITCH}" y="{footer_y - 9}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>'
        )
    legend.append(
        f'<text class="f" x="{swatch_end - len(PALETTE) * PITCH - 8}" y="{footer_y}" '
        f'font-size="11" fill="{MUTED}" text-anchor="end">Less</text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="GitHub contribution heatmap for {data["username"]}">
<style>
text{{font-family:{FONT}}}
.c{{opacity:0;animation:drop .4s cubic-bezier(.2,.7,.3,1) forwards}}
.f{{opacity:0;animation:fade .6s ease-out 1.4s forwards}}
@keyframes drop{{from{{opacity:0;transform:translateY(-8px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fade{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.c,.f{{animation:none;opacity:1}}}}
</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
{chr(10).join(month_labels)}
{chr(10).join(cells)}
<text class="f" x="{PADX}" y="{footer_y}" font-size="11" fill="{MUTED}">{stats}</text>
{chr(10).join(legend)}
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"{n_weeks} weeks, {len(days)} cells -> {OUT.name} ({width}x{height})")


if __name__ == "__main__":
    main()
