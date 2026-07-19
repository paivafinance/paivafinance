"""Convert a prepped image into a self-typing ASCII-art SVG.

Each pixel's brightness picks a glyph from a density ramp (bright -> sparse,
dark -> dense). Rows are wrapped in horizontal clips that wipe left-to-right
(SMIL) with a block cursor riding the wipe edge, staggered top to bottom.
Prints once, then freezes -- no looping.

Mostly monochrome by design: one light-gray fill, with a single exception --
pixels that are clearly the Integranos brand green keep their green.
Set STATIC=1 for a frozen frame. Swap in a photo by running prep_photo.py
first and passing --source.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears the bg
CHAR_ASPECT = 0.5       # monospace glyphs are ~2x taller than wide
FONT_SIZE, CW, LH = 12, 7.2, 12
PAD = 18

BG, BORDER, FG = "#0d1117", "#30363d", "#c9d1d9"
GREEN = "#5CB033"
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Consolas,Menlo,monospace"

T0, STAGGER, DUR = 0.3, 0.09, 0.55


def to_grid(source: Path, cols: int, invert: bool,
            crop: tuple[int, int, int, int] | None,
            gamma: float, floor: int) -> list[list[tuple[str, str]]]:
    img = Image.open(source).convert("RGBA")
    if crop:
        img = img.crop(crop)
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white, img).convert("RGB")
    rows_n = max(1, round(cols * img.height / img.width * CHAR_ASPECT))
    small = flat.resize((cols, rows_n), Image.LANCZOS)
    gray = small.convert("L")

    grid = []
    for j in range(rows_n):
        row = []
        for i in range(cols):
            g = gray.getpixel((i, j))
            if invert:
                # light-on-dark source: bright -> dense, below the floor (dark bg + JPEG
                # noise) -> blank; gamma < 1 pulls mid-tones into denser glyphs
                if g < floor:
                    ch = " "
                else:
                    idx = round(((g - floor) / (255 - floor)) ** gamma * (len(RAMP) - 1))
                    ch = RAMP[min(len(RAMP) - 1, idx)]
            else:
                ch = RAMP[(255 - g) * len(RAMP) // 256]
            r, gr, b = small.getpixel((i, j))
            color = GREEN if ch != " " and gr > r + 24 and gr > b + 24 else FG
            row.append((ch, color))
        grid.append(row)
    return grid


def row_tspans(row: list[tuple[str, str]]) -> tuple[str, int]:
    while row and row[-1][0] == " ":
        row = row[:-1]
    if not row:
        return "", 0
    runs, buf, cur = [], [], row[0][1]
    for ch, color in row:
        if color != cur:
            runs.append((cur, "".join(buf)))
            buf, cur = [], color
        buf.append(ch)
    runs.append((cur, "".join(buf)))
    tspans = "".join(
        f'<tspan fill="{color}">{text.replace("&", "&amp;").replace("<", "&lt;")}</tspan>'
        for color, text in runs
    )
    return tspans, len(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "assets" / "logo-source.png")
    parser.add_argument("--out", type=Path, default=ROOT / "ascii-logo.svg")
    parser.add_argument("--cols", type=int, default=100)
    parser.add_argument("--invert", action="store_true",
                        help="bright pixels -> dense glyphs (for light-on-dark sources like the logo)")
    parser.add_argument("--crop", type=str, default=None, metavar="L,T,R,B",
                        help="crop the source before converting (e.g. isolate the monogram)")
    parser.add_argument("--gamma", type=float, default=0.5,
                        help="invert-mode tone curve: 0.5 for flat logos, ~0.85 for photos")
    parser.add_argument("--floor", type=int, default=48,
                        help="invert-mode: gray levels below this become blank background")
    args = parser.parse_args()
    static = os.environ.get("STATIC") == "1"
    crop = tuple(int(v) for v in args.crop.split(",")) if args.crop else None

    grid = to_grid(args.source, args.cols, args.invert, crop, args.gamma, args.floor)
    width = round(PAD * 2 + args.cols * CW)
    height = PAD * 2 + len(grid) * LH

    defs, texts, cursors = [], [], []
    for j, row in enumerate(grid):
        tspans, length = row_tspans(row)
        if not tspans:
            continue
        row_w = round(length * CW, 1)
        y_top = PAD + j * LH
        baseline = y_top + FONT_SIZE - 2
        begin = T0 + j * STAGGER
        clip = "" if static else f' clip-path="url(#r{j})"'
        texts.append(
            f'<text x="{PAD}" y="{baseline}" font-size="{FONT_SIZE}"{clip} xml:space="preserve" '
            f'textLength="{row_w}" lengthAdjust="spacingAndGlyphs">{tspans}</text>'
        )
        if static:
            continue
        defs.append(
            f'<clipPath id="r{j}"><rect x="{PAD}" y="{y_top - 2}" width="0" height="{LH + 4}">'
            f'<animate attributeName="width" from="0" to="{row_w}" dur="{DUR}s" '
            f'begin="{begin:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        cursors.append(
            f'<rect x="{PAD}" y="{y_top}" width="{CW}" height="{LH - 1}" fill="{FG}" opacity="0">'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + row_w}" dur="{DUR}s" '
            f'begin="{begin:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + DUR:.2f}s"/></rect>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Integranos logo rendered as ASCII art">
<style>text{{font-family:{FONT};text-rendering:optimizeSpeed}}</style>
<defs>{"".join(defs)}</defs>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
{chr(10).join(texts)}
{chr(10).join(cursors)}
</svg>
"""
    args.out.write_text(svg, encoding="utf-8")
    print(
        f"{args.cols}x{len(grid)} chars -> {args.out.name} "
        f"({width}x{height}){' [static]' if static else ''}"
    )


if __name__ == "__main__":
    main()
