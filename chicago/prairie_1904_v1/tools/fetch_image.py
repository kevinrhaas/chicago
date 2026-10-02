#!/usr/bin/env python3
"""Fetch one rights-cleared image into the Prairie 1904 image collection.

    python3 tools/fetch_image.py <record-id> <direct-image-url> [--max 1400] [--thumb-only]

Writes research/images/files/<id>.jpg (long side <= --max, default 1400, JPEG q74) and
<id>-thumb.jpg (long side <= 400) — sized for the collection's 300 MB budget (validate.py) and prints a JSON `local` block to paste into
the record. Only use it for items whose rights are public domain or "no known
restrictions" — everything else stays link-only (rights rule, AGENTS.md rule 6).
The original is never kept: its URL is the record of where it lives.

--thumb-only writes just the 480 px thumbnail: for public-domain items whose holder serves
no small size (chicagology's ~3,800 px Robinson 1886 crops), so the grid does not pull the
full file, while the detail view still shows the holder's own image (owner, 2026-10-01).
"""
import hashlib, io, json, re, sys, time, urllib.request
from pathlib import Path
from PIL import Image
Image.MAX_IMAGE_PIXELS = 400_000_000
P = Path(__file__).resolve().parents[1]
# THE BYTES LIVE IN kevinrhaas/chicago-images (owner, 2026-10-02), under prairie-1904/files/,
# served by that repository's own Pages site — this repository's Pages budget could not hold
# the collection the owner wants. Records keep the LOGICAL path research/images/files/<id>.jpg;
# the viewer maps that prefix onto the image host (data/images.json `image_store`).
# A clone of chicago-images beside this repository is the default store; override with
# PRAIRIE_IMAGE_STORE=<dir>. research/images/files/ here is the retired first store: no new files.
import os
_REPO = P.parents[1]
STORE = Path(os.environ.get('PRAIRIE_IMAGE_STORE') or (_REPO.parent / 'chicago-images' / 'prairie-1904' / 'files'))
OUT = STORE
UA = 'ChicagoBuildingAtlas/1.0 (https://chicago.polecat.live; research) Python-urllib'

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    rid, url = a[0], a[1]
    mx = int(a[a.index('--max') + 1]) if '--max' in a else 1400
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,90}', rid): sys.exit('id must be lowercase a-z0-9 and hyphens')
    if not OUT.parent.parent.joinpath('.git').exists() and 'PRAIRIE_IMAGE_STORE' not in os.environ:
        sys.exit(f'image store not found: clone kevinrhaas/chicago-images beside this repository ({OUT.parent.parent}) or set PRAIRIE_IMAGE_STORE')
    OUT.mkdir(parents=True, exist_ok=True)
    raw = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            raw = urllib.request.urlopen(req, timeout=120).read(); break
        except Exception as e:
            err = e; time.sleep(2 * 2 ** attempt)
    if raw is None: sys.exit(f'fetch failed: {err}')
    src_sha = hashlib.sha256(raw).hexdigest()
    im = Image.open(io.BytesIO(raw))
    im.seek(0)
    if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
    w, h = im.size
    out = {}
    sizes = [(f'{rid}-thumb.jpg', 400, 74)] if '--thumb-only' in a else [(f'{rid}.jpg', mx, 74), (f'{rid}-thumb.jpg', 400, 74)]
    for name, size, q in sizes:
        c = im.copy(); c.thumbnail((size, size), Image.LANCZOS)
        p = OUT / name; c.save(p, 'JPEG', quality=q, optimize=True, progressive=True)
        out['display' if not name.endswith('-thumb.jpg') else 'thumb'] = 'research/images/files/' + name
        out[('display' if not name.endswith('-thumb.jpg') else 'thumb') + '_bytes'] = p.stat().st_size
    out.update(original_px=[w, h], original_sha256=src_sha, original_bytes=len(raw), fetched_from=url,
               fetched=time.strftime('%Y-%m-%d'))
    print(json.dumps(out, indent=1))

if __name__ == '__main__': main()
