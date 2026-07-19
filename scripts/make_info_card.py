"""Hand-author the neofetch-style info card SVG (info-card.svg).

A terminal window with colored key/value rows that fade and slide in on a
short stagger, plus the classic neofetch color-palette bar. Set STATIC=1 to
emit a frozen frame for local previews.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

BG, BORDER, FG, MUTED = "#0d1117", "#30363d", "#c9d1d9", "#8b949e"
GREEN = "#5CB033"
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Consolas,Menlo,monospace"

ROWS = [
    ("Role", "Co-founder & Dev @ Integranos"),
    ("Also", "CTO @ ArchLab · AI for architecture"),
    ("Stack", "Python · FastAPI · Next.js · TypeScript"),
    ("Data", "Supabase · PostgreSQL"),
    ("AI", "Gemini · Claude · gen-media pipelines"),
    ("Infra", "Hetzner VPS · Docker · Easypanel · Cloudflare"),
    ("Focus", "B2B process automation & custom software"),
    ("Web", "integranos.com.br"),
    ("Where", "Brazil · UTC-3"),
]

# GitHub-dark takes on the 8 normal + 8 bright ANSI terminal colors
ANSI_NORMAL = ["#21262d", "#f85149", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"]
ANSI_BRIGHT = ["#30363d", "#ff7b72", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#f0f6fc"]

W = 640
TITLE_H = 34
LINE_H = 22
PAD_X = 28
KEY_X, VAL_X = PAD_X, PAD_X + 92


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    body: list[str] = []
    delay = 0.0

    def line(el: str) -> None:
        nonlocal delay
        style = "" if static else f' style="animation-delay:{delay:.2f}s"'
        body.append(f'<g class="l"{style}>{el}</g>')
        delay += 0.12

    y = TITLE_H + 34
    line(
        f'<text x="{PAD_X}" y="{y}" font-size="13">'
        f'<tspan fill="{GREEN}" font-weight="bold">thiago</tspan><tspan fill="{MUTED}">@</tspan>'
        f'<tspan fill="{GREEN}" font-weight="bold">integranos</tspan></text>'
    )
    y += LINE_H
    line(f'<text x="{PAD_X}" y="{y}" font-size="13" fill="{MUTED}">{"-" * 17}</text>')

    for key, value in ROWS:
        y += LINE_H
        value = value.replace("&", "&amp;").replace("<", "&lt;")
        line(
            f'<text x="{KEY_X}" y="{y}" font-size="13" fill="{GREEN}" font-weight="bold">{key}</text>'
            f'<text x="{VAL_X}" y="{y}" font-size="13" fill="{FG}">{value}</text>'
        )

    y += 14
    for row_colors in (ANSI_NORMAL, ANSI_BRIGHT):
        y += 16
        swatches = "".join(
            f'<rect x="{PAD_X + i * 24}" y="{y}" width="22" height="13" rx="2" fill="{c}"/>'
            for i, c in enumerate(row_colors)
        )
        line(swatches)

    height = y + 34

    anim_css = "" if static else (
        f".l{{opacity:0;animation:slide .5s ease-out forwards}}\n"
        f"@keyframes slide{{from{{opacity:0;transform:translateX(-10px)}}"
        f"to{{opacity:1;transform:translateX(0)}}}}\n"
        f"@media (prefers-reduced-motion:reduce){{.l{{animation:none;opacity:1}}}}\n"
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="Profile card: Thiago Paiva, co-founder and dev at Integranos">
<style>
text{{font-family:{FONT}}}
{anim_css}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<path d="M0.5 {TITLE_H} h{W - 1}" stroke="{BORDER}"/>
<circle cx="24" cy="{TITLE_H // 2}" r="6" fill="#ff5f56"/>
<circle cx="44" cy="{TITLE_H // 2}" r="6" fill="#ffbd2e"/>
<circle cx="64" cy="{TITLE_H // 2}" r="6" fill="#27c93f"/>
<text x="{W // 2}" y="{TITLE_H // 2 + 4}" font-size="12" fill="{MUTED}" text-anchor="middle">thiago@integranos: ~</text>
{chr(10).join(body)}
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"{len(ROWS)} rows -> {OUT.name} ({W}x{height}){' [static]' if static else ''}")


if __name__ == "__main__":
    main()
