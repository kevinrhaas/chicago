#!/usr/bin/env python3
"""Re-encode every PNG/JPEG inside a GLB as KTX2 (KHR_texture_basisu) — T-2595.

    python3 tools/ktx2_glb.py IN.glb OUT.glb [--cap 2048]

`tools/web_derivatives.sh` runs this between `gltf-transform optimize` and `meshopt` on
every textured master (the Glessner v4 set excepted until T-2596). A JPEG in a GLB goes up
to the GPU as RGBA8, four bytes a texel and a third again for mips; a Basis Universal KTX2
is transcoded to the GPU's own block format and stays a quarter to an eighth of that.

THE RECIPE is `tools/ktx2_sheets.py`'s, so a house's sheets and the library sheets are
one encoding with one tool:
  * a texture any material reads as COLOUR (baseColor, emissive) -> ETC1S (basis-lz,
    clevel 2, qlevel 160), sRGB;
  * everything else — normal, occlusion, metallic-roughness — is DATA -> UASTC level 2
    with RDO and zstd 18, linear. ETC1S's shared endpoint palette smears a normal map's
    gradients; UASTC does not.
  * sizes go to the nearest power of two and at most `--cap` on a side (three's
    KTX2Loader refuses a Basis texture whose size is not a multiple of four).

THE TOOL is the KTX-Software 4.3.2 `ktx` that ktx2_sheets.py pins and fetches (sha256
checked, no sudo). Not gltf-transform's own `uastc`/`etc1s`: measured on the 20 Prairie
houses, the CLI never applies RDO to a normal map, and the normals came out 6.8x their
JPEG bytes — the published payload went from 28.8 MB to 67.9 MB. And gltf-transform 4.5.0
needs `ktx` 4.4+, so against the pinned 4.3.2 every texture failed inside `ktx create`
while the CLI exited 0 and wrote the JPEGs back. This tool checks its own output.

Rows: `ktx create` writes the image's top row first, and a GLB wants exactly that — the
GLTFLoader uploads every texture with flipY false, glTF's v = 0 being the image's top.
(The library SHEETS are the opposite case, loaded outside a GLB: T-2593.)

The GLB surgery: each new KTX2 is appended to the binary chunk as its own buffer view and
the image is pointed at it; the old views are left unreferenced, and the `meshopt` pass
after this rewrites the file from what is referenced, so they do not ship.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ktx2_sheets import ETC1S, UASTC, KTX_VERSION, ktx_binary  # noqa: E402

# The houses share their material sheets (the same clapboard normal ships in a dozen
# GLBs), and a UASTC encode with RDO takes about forty seconds a 1024² sheet. Both
# encodes are deterministic — measured, the same input gives the same bytes twice — so
# the result is kept under the hash of everything that decides it and reused.
CACHE = Path(os.environ.get('KTX2_GLB_CACHE') or Path.home() / '.cache' / 'chicago-4d' / 'ktx2-glb')

RASTER = ('image/png', 'image/jpeg')
COLOUR_SLOTS = ('baseColorTexture', 'emissiveTexture')


def read_glb(path: Path):
    b = path.read_bytes()
    if b[:4] != b'glTF':
        raise SystemExit(f'{path}: not a GLB')
    jl = struct.unpack('<I', b[12:16])[0]
    doc = json.loads(b[20:20 + jl])
    off = 20 + jl
    bin_ = b''
    if off < len(b):
        bl, kind = struct.unpack('<II', b[off:off + 8])
        if kind == 0x004E4942:
            bin_ = b[off + 8:off + 8 + bl]
    return doc, bytearray(bin_)


def write_glb(path: Path, doc: dict, bin_: bytes):
    j = json.dumps(doc, separators=(',', ':')).encode()
    j += b' ' * (-len(j) % 4)
    bin_ = bytes(bin_) + b'\0' * (-len(bin_) % 4)
    total = 12 + 8 + len(j) + (8 + len(bin_) if bin_ else 0)
    out = struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(j), 0x4E4F534A) + j
    if bin_:
        out += struct.pack('<II', len(bin_), 0x004E4942) + bin_
    path.write_bytes(out)


def colour_images(doc: dict) -> set[int]:
    """Images some material samples as colour. A texture is found by every slot, including
    the ones inside material extensions, by walking for {"index": n} under a *Texture key."""
    tex_source = {i: t.get('source') for i, t in enumerate(doc.get('textures', []))}
    colour = set()

    def walk(node, key=''):
        if isinstance(node, dict):
            if key.endswith('Texture') and 'index' in node:
                if key in COLOUR_SLOTS or key.endswith(('ColorTexture', 'colorTexture')):
                    colour.add(tex_source.get(node['index']))
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, key)
    for m in doc.get('materials', []):
        walk(m)
    return colour


def pot(n: int, cap: int) -> int:
    lo = 1 << max(0, n.bit_length() - 1)
    hi = lo * 2
    return min(cap, lo if n - lo <= hi - n else hi)


def encode(exe, env, data: bytes, colour: bool, cap: int, tmp: Path, i: int) -> bytes:
    key = hashlib.sha256(json.dumps([KTX_VERSION, colour, cap, ETC1S, UASTC]).encode()
                         + hashlib.sha256(data).digest()).hexdigest()
    hit = CACHE / f'{key}.ktx2'
    if hit.exists():
        return hit.read_bytes()
    blob = _encode(exe, env, data, colour, cap, tmp, i)
    CACHE.mkdir(parents=True, exist_ok=True)
    part = hit.with_suffix(f'.{os.getpid()}.part')
    part.write_bytes(blob)
    part.replace(hit)
    return blob


def _encode(exe, env, data: bytes, colour: bool, cap: int, tmp: Path, i: int) -> bytes:
    im = Image.open(io.BytesIO(data))
    alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    im = im.convert('RGBA' if alpha else 'RGB')
    size = (pot(im.width, cap), pot(im.height, cap))
    if size != im.size:
        im = im.resize(size, Image.LANCZOS)
    src, out = tmp / f'{i}.png', tmp / f'{i}.ktx2'
    im.save(src)
    fmt = ('R8G8B8A8' if alpha else 'R8G8B8') + ('_SRGB' if colour else '_UNORM')
    args = [exe, 'create', '--format', fmt, '--assign-oetf', 'srgb' if colour else 'linear',
            '--generate-mipmap', '--mipmap-wrap', 'wrap', *(ETC1S if colour else UASTC),
            str(src), str(out)]
    subprocess.run(args, check=True, env=env, stdout=subprocess.DEVNULL)
    blob = out.read_bytes()
    if blob[:12] != b'\xabKTX 20\xbb\r\n\x1a\n':
        raise SystemExit(f'image {i}: ktx create wrote something that is not a KTX2')
    return blob


def convert(src: Path, dst: Path, cap: int) -> tuple[int, int]:
    doc, bin_ = read_glb(src)
    images = doc.get('images', [])
    todo = [i for i, im in enumerate(images) if im.get('mimeType') in RASTER and 'bufferView' in im]
    if any(im.get('uri') for im in images):
        raise SystemExit(f'{src}: an image is an external URI; a GLB derivative embeds them')
    if not todo:
        write_glb(dst, doc, bin_)
        return 0, 0
    exe, env = ktx_binary()
    colour = colour_images(doc)
    views = doc['bufferViews']
    def job(i):
        v = views[images[i]['bufferView']]
        o = v.get('byteOffset', 0)
        return encode(exe, env, bytes(bin_[o:o + v['byteLength']]), i in colour, cap, tmp, i)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) // 2)) as pool:
            blobs = list(pool.map(job, todo))
        for i, blob in zip(todo, blobs):
            bin_ += b'\0' * (-len(bin_) % 8)
            views.append({'buffer': 0, 'byteOffset': len(bin_), 'byteLength': len(blob)})
            bin_ += blob
            images[i]['bufferView'] = len(views) - 1
            images[i]['mimeType'] = 'image/ktx2'
    for t in doc.get('textures', []):
        if t.get('source') in todo:
            t.setdefault('extensions', {})['KHR_texture_basisu'] = {'source': t.pop('source')}
    for key in ('extensionsUsed', 'extensionsRequired'):
        doc[key] = sorted(set(doc.get(key, [])) | {'KHR_texture_basisu'})
    doc['buffers'][0]['byteLength'] = len(bin_) + (-len(bin_) % 4)
    write_glb(dst, doc, bin_)
    return len(todo), sum(1 for i in todo if i in colour)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('src', type=Path)
    ap.add_argument('dst', type=Path)
    ap.add_argument('--cap', type=int, default=2048, help='largest side, after power of two')
    a = ap.parse_args()
    n, c = convert(a.src, a.dst, a.cap)
    doc, _ = read_glb(a.dst)
    left = sum(1 for im in doc.get('images', []) if im.get('mimeType') in RASTER)
    if left:
        print(f'{a.dst}: {left} PNG/JPEG image(s) remain after the encode', file=sys.stderr)
        return 1
    print(f'   ktx2: {n} image(s) — {c} colour as ETC1S, {n - c} data as UASTC')
    return 0


if __name__ == '__main__':
    sys.exit(main())
