#!/usr/bin/env python3
"""
Write the runtime library sheets as KTX2 (Basis Universal), next to their sources.

    python3 tools/ktx2_sheets.py            # convert every sheet below
    python3 tools/ktx2_sheets.py --check    # the gate: every sheet's .ktx2 present, a KTX2,
                                            # its web map's size, a full mip chain; no orphans
    python3 tools/ktx2_sheets.py --list     # what it would write

WHY (T-2551, split to T-2582): a WebP/PNG/JPEG sheet is decoded on the CPU and uploaded as
uncompressed RGBA8, four bytes a texel plus a third for mips. A Basis Universal KTX2 is
transcoded in a worker to the GPU's own block format (ASTC/ETC2 on phones, BC7/BC1 on
desktop), half a byte to a byte a texel, uploaded with no decode and kept compressed in GPU
memory. The renderer half is `renderers/web/js/ktx2.js`.

THE CODECS (the ticket's rule): basecolour is colour, and ETC1S (BasisLZ) is small and
good enough for it; normal and ORM maps are data, where ETC1S's shared endpoints smear the
vectors, so they are UASTC with RDO and Zstandard supercompression. Every sheet carries a
full mip chain generated with WRAP sampling, because every one of these tiles.

THE SOURCE is the lossless master PNG the library generator wrote, resampled to the web
derivative's size where the two differ, so the KTX2 is never a re-encode of a lossy JPEG.

THE TOOL is KTX-Software 4.3.2, the same release `.github/workflows/chicago-4d-bake.yml`
installs (approved by the owner 2026-08-14, docs/RENDERING.md §8 decision 5). It is fetched
from the Khronos release, verified against the sha256 below, and unpacked with `dpkg -x`
into a cache — no sudo, nothing installed system-wide. A `ktx` already on PATH reporting
v4.3.2 is used as it stands.

THIS PIECE converts the drop-in sheets only (roof-relief, street-grid, ground-strip). The
CPU-packed sheets (frontage, wall-relief, signage) are T-2583: they derive maps from
decoded pixels, which a compressed texture cannot feed, so their KTX2 must be the DERIVED
map, written by that ticket.

THE FRONTAGE TIMBER (T-2589, a piece of T-2583) is the first of those. `frontage.js` binds
the board face's `normal_gl` and `orm` and a GRAIN map: each texel's linear luminance over
the basecolor's mean, pulled toward 1 by GRAIN_STRENGTH and stored under GRAIN_HEADROOM,
grey in RGB. It used to be packed on the CPU at every boot (relief-pack.js `packGrain`);
`grain_master` writes the same map here from the lossless basecolor, reading both
constants out of frontage.js so the two can never drift. Its three sheets are written
BOTTOM ROW FIRST (`FLIP_V`): a compressed texture uploads with flipY false, so a KTX2
written top-first lands mirrored along v against the flipY'd image it replaces, and a
`normal_gl` mirrored without its green negated is lit upside down across the board. Flipped
here, the KTX2 path samples the very texel the image path did. The grain and the ORM are
ETC1S (`ETC1S_DATA`): measured on these maps, the grey grain reads 45.5 dB against its
master and the ORM 37.7/39.3 dB (AO/roughness), at 89 KB and 56 KB where UASTC wrote 388 KB
and 374 KB; the normal stays UASTC (52/46 dB), where ETC1S read 38/37. So the three cost
the 1835 boot what the three WebPs did (436 KB against 433 KB), which is all the room the
boot budget has (docs/SITE-BUDGET.md section 4c).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = ROOT / 'assets' / 'textures'

KTX_VERSION = '4.3.2'
KTX_DEB = f'KTX-Software-{KTX_VERSION}-Linux-x86_64.deb'
KTX_URL = f'https://github.com/KhronosGroup/KTX-Software/releases/download/v{KTX_VERSION}/{KTX_DEB}'
KTX_SHA256 = 'fa0670f157b77bc67e2da00fb4825a2df69a1a0ed12058626c9852dd23b90f07'
CACHE = Path(os.environ.get('KTX_CACHE') or Path.home() / '.cache' / 'chicago-4d' / f'ktx-{KTX_VERSION}')

# Colour: ETC1S. Data: UASTC level 2, RDO over a 32 KB dictionary, Zstandard 18.
# Measured on the shingle ORM (T-2582): ETC1S reads 28-32 dB per channel against the
# master, UASTC 41 dB and up; the 32 KB dictionary is 3 % smaller than the default 4 KB
# and no worse, and raising the RDO lambda past 1 saved under 1 % for 2-3 dB lost.
ETC1S = ['--encode', 'basis-lz', '--clevel', '2', '--qlevel', '160']
UASTC = ['--encode', 'uastc', '--uastc-quality', '2', '--uastc-rdo', '--uastc-rdo-d', '32768', '--zstd', '18']

# T-2589: the frontage timber's board face. Its maps are written bottom row first, and its
# grain and ORM are ETC1S; see the module docstring for both measurements.
FRONTAGE_FACE = 'clapboard_board_face'
FLIP_V = {(FRONTAGE_FACE, m) for m in ('normal_gl', 'orm', 'grain')}
ETC1S_DATA = {(FRONTAGE_FACE, 'orm'), (FRONTAGE_FACE, 'grain')}
FRONTAGE_JS = ROOT / 'renderers' / 'web' / 'js' / 'frontage.js'


def sheets():
    """(directory, id, map, web file) for every drop-in sheet the renderer loads by URL."""
    out = []
    # roof-relief.js COVERINGS: normal_gl + orm, each beside a `.webp`.
    for d in ('roofs/wood_shingles_weathered', 'roofs/roof_boards_weathered'):
        sid = d.split('/')[-1]
        for m in ('normal_gl', 'orm'):
            out.append((ASSETS / 'chicago_1835_pbr' / d, sid, m, f'{sid}_{m}.webp'))
    # ground-strip.js SUBSTRATES: basecolour only, and the muck only — the sand's pixels
    # are read on the CPU for its mean luma, so it is T-2583's.
    for sid in ('wet_prairie_muck',):
        out.append((ASSETS / 'chicago_1835_pbr' / 'ground' / sid, sid, 'basecolor', f'{sid}_basecolor.png'))
    # frontage.js (T-2589): the board face's relief pair, and the grain derived from its
    # basecolor, which is sized against the basecolor's WebP.
    d = ASSETS / 'chicago_1835_pbr' / 'walls' / FRONTAGE_FACE
    for m in ('normal_gl', 'orm'):
        out.append((d, FRONTAGE_FACE, m, f'{FRONTAGE_FACE}_{m}.webp'))
    out.append((d, FRONTAGE_FACE, 'grain', f'{FRONTAGE_FACE}_basecolor.webp'))
    # street-grid.js: every material any street_surfaces file names, its `web` maps.
    seen = set()
    for f in sorted((ROOT / 'data' / 'street_surfaces').glob('*.json')):
        for m in (json.loads(f.read_text()).get('materials') or {}).values():
            if m['texture'] in seen:
                continue
            seen.add(m['texture'])
            d = ASSETS / 'prairie_1904_pbr' / m['texture']
            sheet = json.loads((d / 'material.json').read_text())
            for k in ('basecolor', 'normal_gl', 'orm'):
                out.append((d, sheet['id'], k, sheet['web'][k]))
    return out


def ktx_binary():
    """A runnable `ktx` 4.3.2 and the environment to run it in."""
    on_path = shutil.which('ktx')
    if on_path:
        r = subprocess.run([on_path, '--version'], capture_output=True, text=True)
        if f'v{KTX_VERSION}' in (r.stdout + r.stderr):
            return on_path, dict(os.environ)
    exe = CACHE / 'usr' / 'bin' / 'ktx'
    if not exe.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        deb = CACHE / KTX_DEB
        if not deb.exists():
            print(f'fetching {KTX_URL}', file=sys.stderr)
            with urllib.request.urlopen(KTX_URL) as r, open(deb, 'wb') as w:
                shutil.copyfileobj(r, w)
        got = hashlib.sha256(deb.read_bytes()).hexdigest()
        if got != KTX_SHA256:
            deb.unlink()
            sys.exit(f'{KTX_DEB}: sha256 {got} is not the pinned {KTX_SHA256}')
        subprocess.run(['dpkg', '-x', str(deb), str(CACHE)], check=True)
    env = dict(os.environ)
    env['LD_LIBRARY_PATH'] = f"{CACHE / 'usr' / 'lib'}:{env.get('LD_LIBRARY_PATH', '')}"
    return str(exe), env


def frontage_constant(name: str) -> float:
    """GRAIN_STRENGTH or GRAIN_HEADROOM, read from frontage.js, the one place it is set."""
    hit = re.search(rf'^const {name} = ([0-9.]+);', FRONTAGE_JS.read_text(), re.M)
    if not hit:
        sys.exit(f'{FRONTAGE_JS.relative_to(ROOT)}: no `const {name} = <number>;` to read')
    return float(hit.group(1))


def grain_master(base: Image.Image) -> Image.Image:
    """relief-pack.js `packGrain`, texel for texel, in image row order (T-2589)."""
    strength, headroom = frontage_constant('GRAIN_STRENGTH'), frontage_constant('GRAIN_HEADROOM')
    lut = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in (i / 255 for i in range(256))]
    px = list(base.convert('RGB').getdata())
    lum = [0.2126 * lut[r] + 0.7152 * lut[g] + 0.0722 * lut[b] for r, g, b in px]
    mean = sum(lum) / len(lum)
    # JS Math.round, which rounds a half up where Python's round() goes to even.
    grey = [max(0, min(255, int((255 * (1 + strength * (v / mean - 1))) / headroom + 0.5))) for v in lum]
    im = Image.new('L', base.size)
    im.putdata(grey)
    return im.convert('RGB')


def master(d: Path, sid: str, m: str, web: str, tmp: Path) -> Path:
    """The lossless master at the web derivative's size, as an 8-bit RGB PNG."""
    web_im = Image.open(d / web)
    src = d / f'{sid}_{"basecolor" if m == "grain" else m}.png'
    im = Image.open(src if src.exists() else d / web).convert('RGB')
    if im.size != web_im.size:
        im = im.resize(web_im.size, Image.LANCZOS)
    if m == 'grain':
        im = grain_master(im)
    if (sid, m) in FLIP_V:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    p = tmp / f'{sid}_{m}.png'
    im.save(p)
    return p


def convert(exe, env, d, sid, m, web, tmp):
    out = d / f'{sid}_{m}.ktx2'
    colour = m == 'basecolor'
    args = [exe, 'create',
            '--format', 'R8G8B8_SRGB' if colour else 'R8G8B8_UNORM',
            '--assign-oetf', 'srgb' if colour else 'linear',
            '--generate-mipmap', '--mipmap-wrap', 'wrap',
            *(ETC1S if colour or (sid, m) in ETC1S_DATA else UASTC),
            str(master(d, sid, m, web, tmp)), str(out)]
    subprocess.run(args, check=True, env=env)
    return out


KTX2_MAGIC = bytes([0xAB, 0x4B, 0x54, 0x58, 0x20, 0x32, 0x30, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A])


def check(todo):
    """What the renderer relies on, read from each file's header — no `ktx` needed."""
    bad = []
    want = {d / f'{sid}_{m}.ktx2': d / web for d, sid, m, web in todo}
    for out, web in want.items():
        rel = out.relative_to(ROOT)
        if not out.exists():
            bad.append(f'{rel}: missing — run python3 tools/ktx2_sheets.py')
            continue
        head = out.read_bytes()[:48]
        if head[:12] != KTX2_MAGIC:
            bad.append(f'{rel}: not a KTX2 file')
            continue
        w, h = int.from_bytes(head[20:24], 'little'), int.from_bytes(head[24:28], 'little')
        levels = int.from_bytes(head[40:44], 'little')
        if (w, h) != Image.open(web).size:
            bad.append(f'{rel}: {w}x{h}, but {web.name} is {Image.open(web).size[0]}x{Image.open(web).size[1]}')
        # ktx2.js drops the top level on the light tier, which needs one beneath it.
        if levels != max(w, h).bit_length():
            bad.append(f'{rel}: {levels} mip level(s), wanted the full chain of {max(w, h).bit_length()}')
    # An orphan ships a file nothing loads (the sand basecolor, whose pixels are read on
    # the CPU, must not grow one until T-2583 derives what is read from it).
    for f in sorted(ASSETS.rglob('*.ktx2')):
        if f not in want:
            bad.append(f'{f.relative_to(ROOT)}: no sheet in tools/ktx2_sheets.py names it')
    for b in bad:
        print(f'BAD: {b}')
    if bad:
        sys.exit(1)
    print(f'ok   {len(want)} KTX2 sheet(s): present, their web map\'s size, full mip chains, no orphans')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    todo = sheets()
    if a.check:
        return check(todo)
    if a.list:
        for d, sid, m, web in todo:
            print(f'{(d / f"{sid}_{m}.ktx2").relative_to(ROOT)}  <-  {web}')
        return
    exe, env = ktx_binary()
    with tempfile.TemporaryDirectory() as t:
        for d, sid, m, web in todo:
            out = convert(exe, env, d, sid, m, web, Path(t))
            w = (d / web).stat().st_size
            print(f'{str(out.relative_to(ROOT)):88s} {out.stat().st_size:>8,d} B  (web {w:,d} B)')


if __name__ == '__main__':
    main()
