#!/usr/bin/env python3
"""Fetch one rights-cleared image into the Prairie 1904 image collection.

    python3 tools/fetch_image.py <record-id> <direct-image-url> [--max 1600]

Writes research/images/files/<id>.jpg (long side <= --max, JPEG q80) and
<id>-thumb.jpg (long side <= 480) and prints a JSON `local` block to paste into
the record. Only use it for items whose rights are public domain or "no known
restrictions" — everything else stays link-only (rights rule, AGENTS.md rule 6).
The original is never kept: its URL is the record of where it lives.
"""
import hashlib, io, json, re, sys, time, urllib.request
from pathlib import Path
from PIL import Image
Image.MAX_IMAGE_PIXELS = 400_000_000
P = Path(__file__).resolve().parents[1]
OUT = P / 'research/images/files'
UA = 'ChicagoBuildingAtlas/1.0 (https://chicago.polecat.live; research) Python-urllib'

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    rid, url = a[0], a[1]
    mx = int(a[a.index('--max') + 1]) if '--max' in a else 1600
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,90}', rid): sys.exit('id must be lowercase a-z0-9 and hyphens')
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
    for name, size, q in ((f'{rid}.jpg', mx, 80), (f'{rid}-thumb.jpg', 480, 78)):
        c = im.copy(); c.thumbnail((size, size), Image.LANCZOS)
        p = OUT / name; c.save(p, 'JPEG', quality=q, optimize=True, progressive=True)
        out['display' if not name.endswith('-thumb.jpg') else 'thumb'] = str(p.relative_to(P))
        out[('display' if not name.endswith('-thumb.jpg') else 'thumb') + '_bytes'] = p.stat().st_size
    out.update(original_px=[w, h], original_sha256=src_sha, original_bytes=len(raw), fetched_from=url,
               fetched=time.strftime('%Y-%m-%d'))
    print(json.dumps(out, indent=1))

if __name__ == '__main__': main()
