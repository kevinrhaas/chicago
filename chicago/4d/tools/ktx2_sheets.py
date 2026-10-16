#!/usr/bin/env python3
"""
Write the runtime library sheets as KTX2 (Basis Universal), next to their sources.

    python3 tools/ktx2_sheets.py            # convert every sheet below
    python3 tools/ktx2_sheets.py --check    # the gate: every sheet's .ktx2 present, a KTX2,
                                            # its web map's size, a full mip chain; no orphans
    python3 tools/ktx2_sheets.py --list     # what it would write
    python3 tools/ktx2_sheets.py --only walls/   # only the sheets under one directory

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

THE DROP-IN SHEETS (roof-relief, street-grid, ground-strip; T-2582) are their master
re-encoded. THE DERIVED SHEETS are maps the renderer used to compute from decoded pixels,
which a compressed texture cannot feed, so the KTX2 is the derived map itself, computed
here from the masters by the same recipe as the page's packer. T-2583 owns them, in
pieces: the wall relief's `orl` and its normal are T-2588 (`wall_sheets` below); the
frontage timber (T-2589) is still canvas-packed; the signboard grain (T-2590) is a derived
WebP tile written by `tools/web_textures.py`, since signage paints it into an atlas canvas
and never uploads it.

ROWS (T-2588). three uploads a KTX2 with its first row at v = 0, and it cannot flip a
compressed texture; an image texture goes up `flipY`, its top row at v = 1. So a KTX2
written straight from a PNG is the image mirrored along v — measured in Chromium on a
two-band test sheet, the band at the top of the PNG came back at the bottom. The derived
wall sheets are therefore written BOTTOM ROW FIRST (`rows='bottom'`), which puts every
texel where the flipY'd WebP beside it puts it, as `relief-pack.js` does for the
DataTexture it replaces. The drop-ins are still written top first, as T-2582 shipped them;
that is the mirror T-2591 is filed to correct.

A DERIVED SHEET CARRIES A STATEMENT (`<id>_orl.json`): the mean roughness the shader
divides by, which the page used to sum from the pixels it no longer reads, and the sha256
of each master it was packed from, so `--check` refuses a sheet whose master moved.

WHAT A RENDERER READ FROM PIXELS IS DERIVED HERE (T-2590). The ground strip's sand used
to stay an image because `ground-strip.js` drew it into a canvas for one number, its mean
linear Rec. 709 luminance, which normalises the sand's grain in the shader. That number
is now written beside the sheet as `<id>_basecolor.luma.json` (LUMA below), from the
lossless master, and the sheet ships as KTX2 like the muck. `--check` recomputes it and
refuses a sidecar that has drifted from its master, so the two cannot disagree silently.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
# The wall's packed `orl` is the one data map on ETC1S, at its top quality (T-2588). It
# carries no vector — AO, a roughness and a luminance ratio, each read as a scalar — so
# the shared endpoints that smear a normal cost it only amplitude. Measured against the
# packed master, per channel R/G/B: clapboard 37.6/40.6/37.9 dB, hewn log 36.8/36.7/35.5
# dB, about 1.5 % of full scale RMS, against 47/52/46 and 45/52/44 on UASTC. UASTC would
# ship 1.193 MB for the pair where ETC1S ships 0.253 MB, and every 1835 visit fetches them
# (docs/SITE-BUDGET.md § 4c): on UASTC the walls cost the boot +0.556 MB over the six
# WebPs they replace, against 0.142 MB of room; on ETC1S they save it 0.385 MB.
ETC1S_DATA = ['--encode', 'basis-lz', '--clevel', '4', '--qlevel', '255']


# wall-relief.js SUBSTRATES (T-2588): the normal as it stands, and the packed `orl`.
WALL_SUBSTRATES = ('walls/clapboard_board_face', 'walls/hewn_log_face')


def wall_sheets():
    """(directory, id, map, web file, rows) for the wall relief's two maps a substrate.

    `web` is the `.webp` the canvas path loads in its place, which fixes the size."""
    out = []
    for d in WALL_SUBSTRATES:
        sid = d.split('/')[-1]
        here = ASSETS / 'chicago_1835_pbr' / d
        out.append((here, sid, 'normal_gl', f'{sid}_normal_gl.webp', 'bottom'))
        out.append((here, sid, 'orl', f'{sid}_orm.webp', 'bottom'))
    return out


def sheets():
    """(directory, id, map, web file, rows) for every sheet the renderer loads by URL."""
    return [(*t, 'top') for t in drop_in_sheets()] + wall_sheets()


def drop_in_sheets():
    """(directory, id, map, web file) for every drop-in sheet the renderer loads by URL."""
    out = []
    # roof-relief.js COVERINGS: normal_gl + orm, each beside a `.webp`.
    for d in ('roofs/wood_shingles_weathered', 'roofs/roof_boards_weathered'):
        sid = d.split('/')[-1]
        for m in ('normal_gl', 'orm'):
            out.append((ASSETS / 'chicago_1835_pbr' / d, sid, m, f'{sid}_{m}.webp'))
    # ground-strip.js SUBSTRATES: basecolour only. The sand's mean luma, which the strip
    # once read from its pixels, comes from its LUMA sidecar (T-2590).
    for sid in ('wet_prairie_muck', 'lake_michigan_dune_sand'):
        out.append((ASSETS / 'chicago_1835_pbr' / 'ground' / sid, sid, 'basecolor', f'{sid}_basecolor.png'))
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


# The sheets whose mean linear luma a renderer needs and can no longer read from a
# compressed texture: ground-strip.js's sand (`uSandLuma`, T-2590).
LUMA = (ASSETS / 'chicago_1835_pbr' / 'ground' / 'lake_michigan_dune_sand', 'lake_michigan_dune_sand')


def srgb_to_linear(u8: int) -> float:
    v = u8 / 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def mean_linear_luma(png: Path) -> float:
    """Mean linear Rec. 709 luminance over every texel of the master, exactly: the mean is
    linear in each channel, so it is read from the channel histograms, with no sampling."""
    im = Image.open(png).convert('RGB')
    n = im.size[0] * im.size[1]
    lut = [srgb_to_linear(v) for v in range(256)]
    hist = im.histogram()
    return sum(w * sum(c * lut[v] for v, c in enumerate(hist[256 * k:256 * (k + 1)]))
               for k, w in enumerate((0.2126, 0.7152, 0.0722))) / n


def luma_sidecar(d: Path, sid: str):
    return d / f'{sid}_basecolor.luma.json'


def luma_record(d: Path, sid: str) -> dict:
    src = d / f'{sid}_basecolor.png'
    return {'mean_linear_luma': round(mean_linear_luma(src), 6),
            'from': src.name,
            'method': 'mean linear Rec. 709 luminance over every texel of the lossless master '
                      '(tools/ktx2_sheets.py, T-2590); ground-strip.js divides the sand\'s sampled '
                      'luma by it to normalise the grain'}


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


def sized(d: Path, sid: str, m: str, web: str) -> Image.Image:
    """The lossless master at the web derivative's size, as 8-bit RGB."""
    web_im = Image.open(d / web)
    src = d / f'{sid}_{m}.png'
    im = Image.open(src if src.exists() else d / web).convert('RGB')
    if im.size != web_im.size:
        im = im.resize(web_im.size, Image.LANCZOS)
    return im


# sRGB code value -> linear, the table relief-pack.js builds.
SRGB_LINEAR = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
               for c in (i / 255 for i in range(256))]


def pack_orl(d: Path, sid: str, web: str):
    """relief-pack.js `packOrl`, from the masters: R = AO, G = roughness (the orm's own),
    B = 0.5 * L / mean(L), L the basecolor's linear luminance. Returns the image (canvas
    order, top row first) and the mean roughness over 0..1, as `packOrl` returns it."""
    orm = sized(d, sid, 'orm', web)
    col = sized(d, sid, 'basecolor', web)
    lin = SRGB_LINEAR
    px = col.tobytes()
    lum = [0.2126 * lin[px[i]] + 0.7152 * lin[px[i + 1]] + 0.0722 * lin[px[i + 2]]
           for i in range(0, len(px), 3)]
    mean = max(sum(lum) / len(lum), 1e-6)
    ratio = Image.new('L', col.size)
    ratio.putdata([max(0, min(255, round(255 * min(1.0, 0.5 * v / mean)))) for v in lum])
    r, g, _ = orm.split()
    rough = sum(g.tobytes()) / (g.size[0] * g.size[1]) / 255
    return Image.merge('RGB', (r, g, ratio)), max(rough, 1e-3)


def masters_of(d: Path, sid: str, m: str):
    """The master PNGs a sheet is made from, for its statement's hashes."""
    names = ('orm', 'basecolor') if m == 'orl' else (m,)
    return [d / f'{sid}_{n}.png' for n in names]


def statement(d: Path, sid: str, m: str, mean_rough: float, size) -> dict:
    return {
        'sheet': f'{sid}_{m}.ktx2',
        'what': 'the wall relief\'s packed map: R = AO, G = roughness, B = 0.5 * L / mean(L) '
                '(relief-pack.js packOrl), written bottom row first (tools/ktx2_sheets.py)',
        'px': list(size),
        'mean_roughness': round(mean_rough, 6),
        'masters': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in masters_of(d, sid, m)},
    }


def master(d: Path, sid: str, m: str, web: str, rows: str, tmp: Path) -> Path:
    """The image to encode, as an 8-bit RGB PNG, in the row order the sheet ships."""
    if m == 'orl':
        im, mean_rough = pack_orl(d, sid, web)
        (d / f'{sid}_orl.json').write_text(
            json.dumps(statement(d, sid, m, mean_rough, im.size), indent=2) + '\n')
    else:
        im = sized(d, sid, m, web)
    if rows == 'bottom':
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    p = tmp / f'{sid}_{m}.png'
    im.save(p)
    return p


def convert(exe, env, d, sid, m, web, rows, tmp):
    out = d / f'{sid}_{m}.ktx2'
    colour = m == 'basecolor'
    args = [exe, 'create',
            '--format', 'R8G8B8_SRGB' if colour else 'R8G8B8_UNORM',
            '--assign-oetf', 'srgb' if colour else 'linear',
            '--generate-mipmap', '--mipmap-wrap', 'wrap',
            *(ETC1S if colour else ETC1S_DATA if m == 'orl' else UASTC),
            str(master(d, sid, m, web, rows, tmp)), str(out)]
    subprocess.run(args, check=True, env=env)
    return out


KTX2_MAGIC = bytes([0xAB, 0x4B, 0x54, 0x58, 0x20, 0x32, 0x30, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A])


def check(todo):
    """What the renderer relies on, read from each file's header — no `ktx` needed."""
    bad = []
    want = {d / f'{sid}_{m}.ktx2': d / web for d, sid, m, web, _ in todo}
    # A derived sheet's statement: present, and naming the masters as they stand now.
    for d, sid, m, web, _ in todo:
        if m != 'orl':
            continue
        st = d / f'{sid}_orl.json'
        if not st.exists():
            bad.append(f'{st.relative_to(ROOT)}: missing — run python3 tools/ktx2_sheets.py')
            continue
        got = json.loads(st.read_text())
        now = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in masters_of(d, sid, m)}
        if got.get('masters') != now:
            bad.append(f'{st.relative_to(ROOT)}: packed from masters that have since changed — '
                       'run python3 tools/ktx2_sheets.py')
        if not (0 < float(got.get('mean_roughness') or 0) <= 1):
            bad.append(f'{st.relative_to(ROOT)}: no mean_roughness in 0..1')
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
    # The derived luma, recomputed from its master: a sidecar that drifted would mis-scale
    # the sand's grain with nothing to show for it.
    d, sid = LUMA
    side = luma_sidecar(d, sid)
    if not side.exists():
        bad.append(f'{side.relative_to(ROOT)}: missing — run python3 tools/ktx2_sheets.py')
    else:
        got, want_v = json.loads(side.read_text()).get('mean_linear_luma'), luma_record(d, sid)['mean_linear_luma']
        if got != want_v:
            bad.append(f'{side.relative_to(ROOT)}: mean_linear_luma {got}, but its master reads {want_v}')
    # An orphan ships a file nothing loads.
    for f in sorted(ASSETS.rglob('*.ktx2')):
        if f not in want:
            bad.append(f'{f.relative_to(ROOT)}: no sheet in tools/ktx2_sheets.py names it')
    for b in bad:
        print(f'BAD: {b}')
    if bad:
        sys.exit(1)
    print(f'ok   {len(want)} KTX2 sheet(s): present, their web map\'s size, full mip chains, no orphans;'
          f' {sid} luma sidecar matches its master')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--only', help='convert only the sheets whose directory contains this')
    a = ap.parse_args()
    todo = sheets()
    if a.check:
        return check(todo)
    if a.list:
        for d, sid, m, web, rows in todo:
            print(f'{(d / f"{sid}_{m}.ktx2").relative_to(ROOT)}  <-  {web}  ({rows} row first)')
        print(f'{luma_sidecar(*LUMA).relative_to(ROOT)}  <-  {LUMA[1]}_basecolor.png (mean linear luma)')
        return
    exe, env = ktx_binary()
    with tempfile.TemporaryDirectory() as t:
        for d, sid, m, web, rows in todo:
            if a.only and a.only not in str(d):
                continue
            out = convert(exe, env, d, sid, m, web, rows, Path(t))
            w = (d / web).stat().st_size
            print(f'{str(out.relative_to(ROOT)):88s} {out.stat().st_size:>8,d} B  (web {w:,d} B)')
    side = luma_sidecar(*LUMA)
    rec = luma_record(*LUMA)
    side.write_text(json.dumps(rec, indent=2) + '\n')
    print(f'{str(side.relative_to(ROOT)):88s} mean linear luma {rec["mean_linear_luma"]}')


if __name__ == '__main__':
    main()
