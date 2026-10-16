#!/usr/bin/env python3
"""The home-screen icons for the installed year (T-2561).

    python3 tools/make_app_icons.py          # writes renderers/web/icons/*.png

The page's own favicon, drawn larger: the dark plate (#16150f, corner radius 6/32)
and the brass river forks (#d8a24a) — `M30 16H17 M17 16L7 6 M17 16L7 26` on a 32
grid, stroke 3, round caps — from the inline SVG in renderers/web/index.html. The
maskable icon draws the same forks at 70 % on a full-bleed plate, inside the safe
zone a launcher may crop to a circle. Deterministic: rerunning reproduces the bytes.
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "renderers" / "web" / "icons"
PLATE, BRASS = (0x16, 0x15, 0x0F, 255), (0xD8, 0xA2, 0x4A, 255)
FORKS = [((30, 16), (17, 16)), ((17, 16), (7, 6)), ((17, 16), (7, 26))]


def icon(size, maskable=False):
    s = 4  # supersample, then reduce: smooth edges with no antialiasing flags
    big = size * s
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if maskable:
        d.rectangle([0, 0, big, big], fill=PLATE)
        scale, off = big * 0.70 / 32, big * 0.15
    else:
        d.rounded_rectangle([0, 0, big - 1, big - 1], radius=big * 6 / 32, fill=PLATE)
        scale, off = big / 32, 0
    w = 3 * scale
    pt = lambda p: (off + p[0] * scale, off + p[1] * scale)
    for a, b in FORKS:
        d.line([pt(a), pt(b)], fill=BRASS, width=round(w))
        for p in (a, b):
            x, y = pt(p)
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=BRASS)
    return im.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size, mask in [("icon-192.png", 192, False), ("icon-512.png", 512, False),
                             ("icon-maskable-512.png", 512, True), ("apple-touch-icon.png", 180, True)]:
        icon(size, mask).save(OUT / name, optimize=True)
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
