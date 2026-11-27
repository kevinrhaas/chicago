#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""photo_face_thumbs.py: the face library's picture sheet for the You tab (T-3553).

    python3 tools/photo_face_thumbs.py           write thumbs.jpg beside the adult photo library
    python3 tools/photo_face_thumbs.py --check   exit 1 if thumbs.jpg is not what the sources give

Kevin, 2026-11-27: "Defining your person no longer works with the photo faces ... maybe if
easier to present as a category library of faces organized by type so a person can choose from
the library in addition to any of the other customizations". The You tab (person-settings.js)
shows each face of the photo library as its own picture: the head of its source portrait
(`<id>_source.jpg`, already published beside the library), cut square about the face and laid on
one sheet in the library's own order (`index`), so the tab fetches one small file when it opens
and nothing on the way into a year. Derived only from the library's own source previews
(assets/LICENSES.md, T-3746/T-3761): no new picture of anyone.
"""
import io
import json
import pathlib
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / 'assets/humans/web/photo_faces/pilot'
OUT = LIB / 'thumbs.jpg'
TILE = 64          # px a face on the sheet; the tab draws it at 48 CSS px
COLS = 16
# The source previews are 314 px portraits, head centred, shoulders at the foot. The square
# kept runs from the hairline's top to the chin, so a face fills its button.
CROP = (0.14, 0.06, 0.86, 0.78)   # left, top, right, bottom as fractions of the source
QUALITY = 78


def build():
    runtime = json.loads((LIB / 'runtime.json').read_text())
    faces = sorted(runtime['faces'], key=lambda f: f['index'])
    rows = (len(faces) + COLS - 1) // COLS
    sheet = Image.new('RGB', (COLS * TILE, rows * TILE), (128, 128, 128))
    for f in faces:
        src = Image.open(LIB / f"{f['id']}_source.jpg").convert('RGB')
        w, h = src.size
        box = tuple(round(v * s) for v, s in zip(CROP, (w, h, w, h)))
        tile = src.crop(box).resize((TILE, TILE), Image.LANCZOS)
        i = f['index']
        sheet.paste(tile, ((i % COLS) * TILE, (i // COLS) * TILE))
    buf = io.BytesIO()
    sheet.save(buf, 'JPEG', quality=QUALITY, optimize=True, progressive=False, subsampling=2)
    return buf.getvalue(), {'file': OUT.name, 'cols': COLS, 'tile_px': TILE, 'size_px': [COLS * TILE, rows * TILE]}


def main(argv):
    data, layout = build()
    if '--check' in argv:
        if not OUT.exists():
            print(f'photo_face_thumbs: {OUT.relative_to(ROOT)} missing; run python3 tools/photo_face_thumbs.py')
            return 1
        # Decoded pixels, not bytes: a JPEG encoder's last bits may differ between Pillow builds.
        have = Image.open(OUT).convert('RGB')
        want = Image.open(io.BytesIO(data)).convert('RGB')
        if have.size != want.size:
            print(f'photo_face_thumbs: {OUT.name} is {have.size}, the library gives {want.size}')
            return 1
        diff = int(np.abs(np.asarray(have, np.int16) - np.asarray(want, np.int16)).max())
        if diff > 24:
            print(f'photo_face_thumbs: {OUT.name} differs from its sources by {diff} levels; rebuild it')
            return 1
        print(f'photo_face_thumbs: ok ({layout["size_px"][0]}x{layout["size_px"][1]}, {len(data) // 1024} KiB)')
        return 0
    OUT.write_bytes(data)
    print(f'photo_face_thumbs: wrote {OUT.relative_to(ROOT)} {layout} {len(data) // 1024} KiB')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
