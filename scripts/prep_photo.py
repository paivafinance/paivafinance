"""Prep a portrait photo for ASCII conversion.

A flatly-lit face converts to a dark, unreadable blob. Three steps fix that:
1. Remove the background (rembg) so the subject is isolated.
2. Boost local contrast with CLAHE (opencv) for real highlights and shadows.
3. Composite onto pure white so the background maps to the blank end of the
   ASCII ramp (white -> spaces).

rembg and opencv are optional heavy deps; without them this falls back to the
image's own alpha channel and Pillow's autocontrast. Output lands next to the
input as <name>-prepped.png. Run once per photo, then:

    python scripts/make_ascii_svg.py --source <name>-prepped.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

try:
    from rembg import remove as rembg_remove
except ImportError:
    rembg_remove = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("photo", type=Path)
    parser.add_argument("--keep-bg", action="store_true", help="skip background removal")
    args = parser.parse_args()

    img = Image.open(args.photo).convert("RGBA")

    if not args.keep_bg:
        if rembg_remove is None:
            print("rembg not installed (pip install rembg) -- keeping original background",
                  file=sys.stderr)
        else:
            img = rembg_remove(img)

    gray = img.convert("L")
    if cv2 is not None:
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        gray = Image.fromarray(clahe.apply(np.array(gray)))
    else:
        gray = ImageOps.autocontrast(gray, cutoff=1)

    white = Image.new("L", gray.size, 255)
    white.paste(gray, mask=img.getchannel("A"))

    out = args.photo.with_name(args.photo.stem + "-prepped.png")
    white.save(out)
    print(f"{args.photo.name} -> {out.name} ({white.width}x{white.height})")


if __name__ == "__main__":
    main()
