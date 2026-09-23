#!/usr/bin/env python3
"""Did the ambient occlusion that was baked actually reach the file? Read the bytes.

T-0158, and it is the SECOND fault of this exact shape here. `generators/build.py --ao`
baked occlusion correctly and shipped a texture that was **uniformly black**: in memory,
straight after `bpy.ops.object.bake(type="AO")`, min 0.000 / max 1.000; in the exported
GLB, min 0 and max 0, every one of 262,144 texels. The run exited 0, the texture was
wired into all six materials, the GLB grew 4 KB and `assets/manifest.json` recorded
`baked_ao: true`. Under glTF an occlusion value of 0 means FULLY occluded, so the asset
would have rendered with its ambient light extinguished while the manifest asserted good
AO. The comment above the wiring block in `build.py` records the FIRST time the exporter
dropped AO — *"the bake silently produces nothing, which is exactly what happened before
this was added"* — which is why the fix ships a check rather than only a working export.

**The mechanism, measured 2026-08-27** (`sauganash_hotel`, 512x512, 48 samples, Blender
4.5.3, one asset, four bakes):

| when the image is tagged `Non-Color` | in memory after the bake | in the exported GLB |
|---|---|---|
| AFTER the bake — as shipped | mean 0.2158 | **mean 0.0000, min 0, max 0** |
| BEFORE the bake — the fix | mean 0.1665 | mean 0.1665, min 0.0000, max 1.0000 |

Setting `colorspace_settings.name` on a GENERATED image that has no file behind it and
is not packed frees its buffer, and the buffer regenerates from `generated_color`, which
is black. It also clears `is_dirty` — and `is_dirty` is the flag Blender's own exporter
tests in `make_temp_image_copy()` before it bothers to carry unsaved pixels across. So
one line destroyed the data AND switched off the exporter's only rescue path. The two
in-memory means differ because `Image.pixels` on an 8-bit buffer is RAW — measured, both
directions, no colour management either way — so under `sRGB` the bake stores the
sRGB-ENCODED occlusion (0.2158) and under `Non-Color` it stores the linear occlusion
(0.1665). glTF requires occlusion to be non-colour data, sampled as `byte / 255`, so
0.1665 is the number that belongs in the file and the old 0.2158 was already 30 % too
bright before it went black.

    generators/ao_export.py             census of every committed GLB
    generators/ao_export.py --gate      exit 1 on a disagreement
    generators/ao_export.py --self-test break each assertion, in memory

NO BLENDER, NO NUMPY, NO NETWORK, NO PILLOW. CI installs `jsonschema` and `pyproj` and
nothing else, and a guard that only runs where Blender runs is a guard that runs nightly
at best. This file is deliberately NOT hashed into any asset's `inputs_sha256`: it reads
exported bytes and makes no geometry, which is the same ground `generators/mesh_inputs.py`
excludes itself on. `generators/build.py` IS hashed, so the bake-order fix over there
restaled and rebuilt the whole town.

## The assertions

1.  **A GLB that carries an occlusion texture carries occlusion.** `max > min` over the
    R channel. A uniform texture is refused whichever value it is uniform ON — black is
    what this bug produced, but a uniformly white map is just as much a bake that did
    not arrive, and a guard that only knows the one failure it has seen is the guard
    that lets the next one through.
2.  **The manifest and the file agree.** `baked_ao: true` with no occlusion texture, or
    an occlusion texture under `baked_ao: false`, is the manifest lying about the asset
    in one direction or the other. The black texture shipped with `baked_ao: true`.
3.  **The bake survived the export** (`assert_ao_survived_export`, called by `build.py`
    the moment the GLB is written). The mean the exported bytes carry must agree with
    the mean measured in Blender's own buffer to within 2 %. Measured drift on the fix:
    0.0 %. This is the assertion the shipped bug would have failed at 100 %.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# 8-bit, non-interlaced, no palette. Blender's glTF exporter writes exactly this for a
# baked byte image; anything else here means the pipeline changed and the reader should
# say so rather than quietly report a number it did not really read.
PNG_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}

# The bake and the file may differ by 8-bit quantisation and the exporter's own float
# round-trip. They may not differ by a gamma curve (30 %) or by an extinguished texture
# (100 %). Measured drift on the fixed path is 0.0 %.
MEAN_TOLERANCE = 0.02


class AoExportError(Exception):
    """The occlusion in the exported file is not the occlusion that was baked."""


# --------------------------------------------------------------------------- PNG


def decode_png(data: bytes) -> tuple[int, int, int, bytearray]:
    """(width, height, channels, pixels) from an 8-bit non-interlaced PNG."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AoExportError("not a PNG")
    pos, idat = 8, bytearray()
    w = h = ctype = None
    while pos + 8 <= len(data):
        (ln,) = struct.unpack_from(">I", data, pos)
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _cm, _fm, interlace = struct.unpack(">IIBBBBB", body[:13])
            if depth != 8:
                raise AoExportError(f"{depth}-bit PNG; this reader handles 8-bit only")
            if interlace:
                raise AoExportError("interlaced PNG")
            if ctype not in PNG_CHANNELS:
                raise AoExportError(f"PNG colour type {ctype} (palette or unknown)")
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if w is None:
        raise AoExportError("PNG has no IHDR")
    nch = PNG_CHANNELS[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = w * nch
    if len(raw) != h * (stride + 1):
        raise AoExportError(f"PNG data is {len(raw)} bytes, expected {h * (stride + 1)}")
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = o = 0
    for _y in range(h):
        f = raw[p]
        p += 1
        row = bytearray(raw[p:p + stride])
        p += stride
        if f == 0:
            pass
        elif f == 1:
            for x in range(nch, stride):
                row[x] = (row[x] + row[x - nch]) & 0xFF
        elif f == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 0xFF
        elif f == 3:
            for x in range(stride):
                a = row[x - nch] if x >= nch else 0
                row[x] = (row[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(stride):
                a = row[x - nch] if x >= nch else 0
                c = prev[x - nch] if x >= nch else 0
                b = prev[x]
                est = a + b - c
                pa, pb, pc = abs(est - a), abs(est - b), abs(est - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[x] = (row[x] + pred) & 0xFF
        else:
            raise AoExportError(f"PNG filter type {f}")
        out[o:o + stride] = row
        o += stride
        prev = row
    return w, h, nch, out


def encode_png(w: int, h: int, nch: int, pixels: bytes, filter_type: int = 0) -> bytes:
    """The inverse, for the self-test. Every filter type, so the reader is exercised."""
    ctype = {1: 0, 2: 4, 3: 2, 4: 6}[nch]
    stride = w * nch
    raw = bytearray()
    prev = bytearray(stride)
    for y in range(h):
        row = bytearray(pixels[y * stride:(y + 1) * stride])
        enc = bytearray(stride)
        for x in range(stride):
            a = row[x - nch] if x >= nch else 0
            b = prev[x]
            c = prev[x - nch] if x >= nch else 0
            if filter_type == 0:
                enc[x] = row[x]
            elif filter_type == 1:
                enc[x] = (row[x] - a) & 0xFF
            elif filter_type == 2:
                enc[x] = (row[x] - b) & 0xFF
            elif filter_type == 3:
                enc[x] = (row[x] - ((a + b) >> 1)) & 0xFF
            elif filter_type == 4:
                est = a + b - c
                pa, pb, pc = abs(est - a), abs(est - b), abs(est - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                enc[x] = (row[x] - pred) & 0xFF
            else:
                raise AoExportError(f"filter {filter_type}")
        raw.append(filter_type)
        raw += enc
        prev = row

    def chunk(typ: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


# --------------------------------------------------------------------------- GLB


def read_glb(data: bytes) -> tuple[dict, bytes]:
    if data[:4] != b"glTF":
        raise AoExportError("not a GLB")
    _magic, _version, length = struct.unpack_from("<III", data, 0)
    off, js, binary = 12, None, b""
    while off + 8 <= min(length, len(data)):
        clen, ctype = struct.unpack_from("<II", data, off)
        body = data[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(body)
        elif ctype == 0x004E4942:
            binary = body
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    if js is None:
        raise AoExportError("GLB has no JSON chunk")
    return js, binary


def occlusion_stats(data: bytes) -> dict | None:
    """The R channel of every image an `occlusionTexture` points at.

    None when no material declares occlusion at all — which is the correct, honest
    state of all 348 committed assets today, because `--ao` is opt-in and nothing
    passes it (T-0015). It is a fault only against a manifest that claims otherwise.
    """
    js, binary = read_glb(data)
    materials = js.get("materials", [])
    sources: list[int] = []
    with_occ = 0
    for mat in materials:
        occ = mat.get("occlusionTexture")
        if occ is None:
            continue
        with_occ += 1
        tex = js.get("textures", [])[occ["index"]]
        src = tex.get("source")
        if src is not None and src not in sources:
            sources.append(src)
    if with_occ == 0:
        return None
    if not sources:
        raise AoExportError("an occlusionTexture points at a texture with no image source")

    hist = [0] * 256
    texels = 0
    for src in sources:
        img = js["images"][src]
        if "bufferView" not in img:
            raise AoExportError(f"image {src} is not embedded (uri {img.get('uri')!r}) — "
                                f"a master GLB must carry its own texture")
        bv = js["bufferViews"][img["bufferView"]]
        start = bv.get("byteOffset", 0)
        payload = binary[start:start + bv["byteLength"]]
        if img.get("mimeType") not in (None, "image/png"):
            raise AoExportError(f"occlusion image is {img.get('mimeType')}, not PNG")
        w, h, nch, pixels = decode_png(payload)
        red = bytes(pixels[0::nch])
        for value in range(256):
            hist[value] += red.count(value)
        texels += w * h

    lo = next(v for v in range(256) if hist[v])
    hi = next(v for v in range(255, -1, -1) if hist[v])
    total = sum(v * n for v, n in enumerate(hist))
    return {
        "materials_with_occlusion": with_occ,
        "materials": len(materials),
        "images": len(sources),
        "texels": texels,
        "min": lo / 255.0,
        "max": hi / 255.0,
        "mean": total / 255.0 / texels,
        "uniform": lo == hi,
    }


# --------------------------------------------------------------- the build-time guard


def assert_ao_survived_export(glb_path, baked_mean: float,
                              tolerance: float = MEAN_TOLERANCE) -> dict:
    """Refuse a GLB whose occlusion texture is not the occlusion that was baked.

    Called by `generators/build.py` the moment the file is written, on the EXPORTED
    BYTES rather than on the in-memory image, because memory is not where this breaks.
    """
    path = pathlib.Path(glb_path)
    label = path.name
    stats = occlusion_stats(path.read_bytes())
    if stats is None:
        raise AoExportError(
            f"{label}: ambient occlusion was baked (mean {baked_mean:.4f}) but the exported "
            f"file declares NO occlusionTexture on any of its materials — the exporter "
            f"dropped it. The wiring the exporter recognises is a node group literally named "
            f"'glTF Material Output' with an 'Occlusion' input; that is the only supported path")
    if stats["uniform"]:
        meaning = ("FULLY OCCLUDED under glTF — every asset built this way renders with its "
                   "ambient light extinguished" if stats["max"] == 0.0 else "unoccluded")
        raise AoExportError(
            f"{label}: the exported occlusion texture is UNIFORMLY {stats['max']:.4f} over "
            f"{stats['texels']:,} texels ({meaning}), while the bake read mean "
            f"{baked_mean:.4f}. The bake is fine and the export lost it. Check that nothing "
            f"touches the image between the bake and the export: setting "
            f"colorspace_settings.name on a GENERATED image frees its buffer, which then "
            f"regenerates BLACK, and clears is_dirty so the exporter will not copy the "
            f"pixels either. Tag the image Non-Color BEFORE the bake (T-0158)")
    drift = abs(stats["mean"] - baked_mean) / max(baked_mean, 1e-9)
    if drift > tolerance:
        raise AoExportError(
            f"{label}: the exported occlusion mean is {stats['mean']:.4f} but the bake read "
            f"{baked_mean:.4f} — {drift * 100:.1f} % apart, over a {tolerance * 100:.0f} % "
            f"tolerance. Occlusion is non-colour data in glTF, sampled as byte/255; a "
            f"~30 % gap is the sRGB transfer curve applied to it (T-0158)")
    return stats


# --------------------------------------------------------------------------- the gate


def check_asset(name: str, claims_ao: bool, data: bytes) -> tuple[dict | None, list[str]]:
    """One committed asset against what the manifest says about it.

    The whole of assertions 1 and 2, in one place, so `--gate` and `--self-test` are
    running the same code rather than two descriptions of it.
    """
    findings: list[str] = []
    try:
        stats = occlusion_stats(data)
    except AoExportError as e:
        return None, [f"{name}: {e}"]
    if stats is None:
        if claims_ao:
            findings.append(f"{name}: assets/manifest.json records baked_ao: true, but the GLB "
                            f"declares no occlusionTexture on any material — the manifest is "
                            f"asserting AO the file does not carry (T-0158)")
        return None, findings
    if not claims_ao:
        findings.append(f"{name}: the GLB carries an occlusionTexture on "
                        f"{stats['materials_with_occlusion']} of {stats['materials']} materials, "
                        f"but assets/manifest.json records baked_ao: false — the manifest cannot "
                        f"tell a reader whether the shipped occlusion is trustworthy")
    if stats["uniform"]:
        findings.append(f"{name}: the shipped occlusion texture is UNIFORMLY "
                        f"{stats['max']:.4f} over {stats['texels']:,} texels. Under glTF a value "
                        f"of 0 means fully occluded, so this asset renders with its ambient "
                        f"light extinguished. This is exactly T-0158")
    return stats, findings


def census(rep: list, quiet: bool = False) -> int:
    manifest_path = ROOT / "assets" / "manifest.json"
    gltf = ROOT / "assets" / "gltf"
    if not manifest_path.exists() or not gltf.exists():
        if not quiet:
            print("  note  no baked assets yet, so nothing to read")
        return 0
    assets = json.loads(manifest_path.read_text()).get("assets", {})
    checked = with_ao = 0
    for name in sorted(assets):
        path = gltf / name
        if not path.exists():
            continue                     # validate.py --stale already reports this
        checked += 1
        stats, findings = check_asset(name, bool(assets[name].get("baked_ao")),
                                      path.read_bytes())
        rep.extend(findings)
        if stats is None:
            continue
        with_ao += 1
        if not findings and not quiet:
            print(f"  ok    {name}  occlusion min {stats['min']:.4f} max {stats['max']:.4f} "
                  f"mean {stats['mean']:.4f} over {stats['texels']:,} texels")
    if not quiet:
        print(f"  note  {checked} committed GLB(s) read; {with_ao} carry an occlusion texture")
    return checked


# ----------------------------------------------------------------------- self-test

def _solid_glb(value: int, w: int = 8, h: int = 8, occlusion: bool = True) -> bytes:
    return _glb(bytes([value]) * (w * h * 3), w, h, occlusion=occlusion)


def _glb(pixels: bytes, w: int, h: int, occlusion: bool = True, filter_type: int = 0) -> bytes:
    png = encode_png(w, h, 3, pixels, filter_type)
    pad = (-len(png)) % 4
    binary = png + b"\x00" * pad
    material = {"pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1]}}
    js = {"asset": {"version": "2.0"},
          "buffers": [{"byteLength": len(binary)}],
          "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(png)}],
          "images": [{"bufferView": 0, "mimeType": "image/png"}],
          "textures": [{"source": 0}],
          "materials": [material]}
    if occlusion:
        material["occlusionTexture"] = {"index": 0}
    jsb = json.dumps(js, separators=(",", ":")).encode()
    jsb += b" " * ((-len(jsb)) % 4)
    total = 12 + 8 + len(jsb) + 8 + len(binary)
    return (b"glTF" + struct.pack("<II", 2, total)
            + struct.pack("<I", len(jsb)) + b"JSON" + jsb
            + struct.pack("<I", len(binary)) + b"BIN\x00" + binary)


def _ramp(w: int, h: int) -> bytes:
    """A gradient with a known mean: byte value = x, so mean = (w-1)/2 / 255."""
    return bytes(bytearray([x for _y in range(h) for x in range(w) for _c in range(3)]))


def self_test() -> int:
    fails = []

    def arm(label, fn, *, must_raise=True):
        try:
            fn()
        except AoExportError as e:
            if must_raise:
                print(f"  ok    {label}\n          {str(e)[:150]}")
                return
            fails.append(f"{label}: refused a good file — {e}")
            return
        if must_raise:
            fails.append(f"{label}: NOT caught")
        else:
            print(f"  ok    {label}")

    print("\n  -- the reader itself")
    src = _ramp(16, 6)
    for ft in range(5):
        w, h, nch, back = decode_png(encode_png(16, 6, 3, src, ft))
        if (w, h, nch) != (16, 6, 3) or bytes(back) != src:
            fails.append(f"PNG filter {ft} does not round-trip")
        else:
            print(f"  ok    PNG filter type {ft} round-trips exactly")

    ramp = _glb(_ramp(16, 6), 16, 6)
    ramp_mean = (sum(range(16)) / 16) / 255.0
    got = occlusion_stats(ramp)
    if got is None or abs(got["mean"] - ramp_mean) > 1e-9 or got["texels"] != 96:
        fails.append(f"the reader mis-measures a known gradient: {got}")
    else:
        print(f"  ok    a known gradient reads back exactly — mean {got['mean']:.6f} "
              f"over {got['texels']} texels")

    print("\n  -- the build-time guard (assert_ao_survived_export), each arm broken")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def write(name, data):
            p = tmp / name
            p.write_bytes(data)
            return p

        black = write("black.glb", _solid_glb(0))
        white = write("white.glb", _solid_glb(255))
        none_ = write("none.glb", _solid_glb(128, occlusion=False))
        good = write("good.glb", ramp)

        arm("the shipped bug: a uniformly BLACK occlusion texture",
            lambda: assert_ao_survived_export(black, 0.2158))
        arm("a uniformly WHITE one — a bake that did not arrive either",
            lambda: assert_ao_survived_export(white, 0.2158))
        arm("AO baked but the exporter declared no occlusionTexture",
            lambda: assert_ao_survived_export(none_, 0.2158))
        arm("real variation, but 30 % off the bake — the sRGB-curve failure",
            lambda: assert_ao_survived_export(good, ramp_mean * 1.30))
        arm("real variation agreeing with the bake — must PASS",
            lambda: assert_ao_survived_export(good, ramp_mean * 1.005),
            must_raise=False)

    print("\n  -- the manifest cross-check (--gate), each arm broken")
    no_tex = _solid_glb(128, occlusion=False)
    cases = [
        ("manifest says baked_ao: true, the file carries none", True, no_tex, True),
        ("manifest says baked_ao: false, the file carries one", False, ramp, True),
        ("a black occlusion texture, consistently recorded as true", True, _solid_glb(0), True),
        ("a white occlusion texture, consistently recorded as true", True, _solid_glb(255), True),
        ("manifest says true and the file carries real occlusion", True, ramp, False),
        ("manifest says false and the file carries none — today's town", False, no_tex, False),
    ]
    for label, claims, data, want_refused in cases:
        _stats, findings = check_asset("probe.glb", claims, data)
        if bool(findings) != want_refused:
            fails.append(f"{label}: expected {'a refusal' if want_refused else 'a clean read'}, "
                         f"got {findings or 'clean'}")
        else:
            print(f"  ok    {label} -> {'refused' if findings else 'clean'}")

    print()
    for f in fails:
        print(f"  FAIL  {f}")
    print("AO EXPORT SELF-TEST " + ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true", help="exit 1 on a disagreement")
    ap.add_argument("--self-test", action="store_true",
                    help="break each assertion in memory and prove it fires")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    rep: list[str] = []
    census(rep, quiet=args.quiet)
    for line in rep:
        print(f"  FAIL  {line}")
    if rep and args.gate:
        return 1
    print("AO EXPORT PASS" if not rep else "AO EXPORT FINDINGS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
