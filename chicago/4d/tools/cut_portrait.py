#!/usr/bin/env python3
"""Cut the picture a person's card shows beside their fitted face (T-3413, T-3478).

    python3 tools/cut_portrait.py PERSON SCAN

PERSON names data/humans/variation/portraits/<PERSON>.json; SCAN is a local copy of the picture
the record cites (its `scan` field says where the copy is kept: the source's own URL, or the
evidence repo). The record's `card.portrait_from_scan_px` box (left, top, right, bottom) is cut
and scaled to `card.size_px`, and written to `card.portrait`.

A record with `stand_in` (T-3478: no photograph of the person is known, so the face is fitted to
someone else's) gets the stand-in's own label burned along the picture's foot, `stand_in.label`
(for example "STAND-IN, NOT KATE RYAN"), so the picture says what it is wherever it is copied to.
The card's caption says the same.
"""
import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]


def font(px):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if pathlib.Path(f).exists():
            return ImageFont.truetype(f, px)
    return ImageFont.load_default()


def main(person, scan):
    rec = json.loads((ROOT / 'data/humans/variation/portraits' / f'{person}.json').read_text())
    card = rec['card']
    w, h = card['size_px']
    im = Image.open(scan).convert('RGB').crop(tuple(card['portrait_from_scan_px'])).resize((w, h), Image.LANCZOS)
    label = (rec.get('stand_in') or {}).get('label')
    if label:
        d = ImageDraw.Draw(im, 'RGBA')
        f = font(max(11, h // 30))
        box = d.textbbox((0, 0), label, font=f)
        band = box[3] - box[1] + 12
        d.rectangle([0, h - band, w, h], fill=(16, 16, 14, 205))
        d.text(((w - (box[2] - box[0])) / 2, h - band + 6 - box[1]), label, font=f, fill=(242, 236, 222, 255))
    out = ROOT / card['portrait']
    im.save(out, quality=88)
    print(f'wrote {card["portrait"]} ({w}x{h}){" with its stand-in label" if label else ""}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
