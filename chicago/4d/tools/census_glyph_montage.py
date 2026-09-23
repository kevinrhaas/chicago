#!/usr/bin/env python3
"""census_glyph_montage.py — the glyph boxes of one column of an 1840 continuation
sheet, tiled and slant-corrected so a human can read the figures.

## Why this exists

`read_census_continuation.py` measures where the numbers are and refuses to say
what they are, for a stated reason: a tool that guessed at a `4` that is two
strokes reading as `11` would launder a guess into a measurement. The boxes are
the measurement and a human reads the digit in the box.

Reading them one crop at a time is what made that expensive. This tool does the
mechanical half: it takes the group boxes that module already produced, crops
each one out of the deposited leaf with a little context, and tiles them into a
single labelled image, in the column's own order.

It also rotates. On `33S7-9YYJ-K2` the enumerator's body figures lean about fifty
degrees off upright — the footer row does not — and at that slant a `6` and a `5`
are hard to tell apart in a crop that a rotation makes obvious. So each figure is
shown TWICE: as it lies on the leaf, and rotated. Both are shown because the
rotation is an interpretation of the hand's slant and the reader has to be able to
see what it did.

    tools/census_glyph_montage.py 33S7-9YYJ-K2 /tmp/k2.json total /tmp/k2_1.png 1 8
    tools/census_glyph_montage.py 33S7-9YYJ-K2 /tmp/k2.json total /tmp/k2_2.png 9 16 --angle 50

where the JSON is the `--json` output of `read_census_continuation.py`. The
montage is scratch: nothing it writes is ever committed, and no image, crop or
render of the deposit is either (data/research/census_1840/README.md).

It reads no digits, for the same reason the module it borrows from does not.

Needs Pillow. Not in the per-commit gate's install list and not in the gate: it is
a research instrument, run by hand, whose OUTPUT is a human's reading.
"""
import argparse
import json
import os
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # chicago/4d
REPO = os.path.dirname(os.path.dirname(APP))                        # the repo root
DEPOSIT = os.path.join(REPO, "chicago", "reference", "census1840")

# 50 degrees is what uprights 33S7-9YYJ-K2's body hand. It is a default, not a
# constant of the deposit: every leaf's slant is its own and the reader who
# changes it should say so beside the reading.
DEFAULT_ANGLE = 50.0
TILE_HEIGHT = 170
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size):
    from PIL import ImageFont
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def montage(fsid, boxes, out, start=1, angle=DEFAULT_ANGLE, pad=24):
    from PIL import Image, ImageDraw
    im = Image.open(os.path.join(DEPOSIT, fsid + ".jpg")).convert("L")
    w, h = im.size
    rows = []
    for b in boxes:
        crop = im.crop((max(0, b[0] - pad), max(0, b[1] - pad),
                        min(w, b[2] + pad), min(h, b[3] + pad)))
        turned = crop.rotate(angle, expand=True, fillcolor=225,
                             resample=Image.BICUBIC)

        def fit(x):
            s = TILE_HEIGHT / x.height
            return x.resize((max(1, int(x.width * s)), TILE_HEIGHT), Image.LANCZOS)

        rows.append((fit(crop), fit(turned)))
    if not rows:
        raise SystemExit("no boxes in that range")
    w0 = max(a.width for a, _ in rows) + 24
    w1 = max(b.width for _, b in rows) + 24
    canvas = Image.new("L", (120 + w0 + w1 + 20, (TILE_HEIGHT + 14) * len(rows) + 20), 255)
    draw = ImageDraw.Draw(canvas)
    font = _font(38)
    for i, (flat, turned) in enumerate(rows):
        y = 10 + i * (TILE_HEIGHT + 14)
        draw.text((12, y + TILE_HEIGHT // 2 - 22), str(start + i), fill=0, font=font)
        canvas.paste(flat, (120, y))
        canvas.paste(turned, (120 + w0, y))
        draw.line((110, y + TILE_HEIGHT + 7, canvas.width - 10, y + TILE_HEIGHT + 7), fill=170)
    canvas.save(out)
    return canvas.size, len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("fsid", help="FamilySearch id of the leaf, e.g. 33S7-9YYJ-K2")
    ap.add_argument("measurements", help="the --json output of read_census_continuation.py")
    ap.add_argument("column", help="which column's group_boxes to tile, e.g. total")
    ap.add_argument("out", help="PNG to write (scratch — never committed)")
    ap.add_argument("first", type=int, help="first group, 1-based")
    ap.add_argument("last", type=int, help="last group, inclusive")
    ap.add_argument("--angle", type=float, default=DEFAULT_ANGLE,
                    help="degrees to rotate the second view (default %(default)s)")
    ap.add_argument("--pad", type=int, default=24, help="context pixels around each box")
    a = ap.parse_args()
    boxes = json.load(open(a.measurements))["columns"][a.column]["group_boxes"]
    size, n = montage(a.fsid, boxes[a.first - 1:a.last], a.out, start=a.first,
                      angle=a.angle, pad=a.pad)
    print(f"{a.out}  {size[0]}x{size[1]}  {n} figures, groups {a.first}-{a.first + n - 1}")


if __name__ == "__main__":
    main()
