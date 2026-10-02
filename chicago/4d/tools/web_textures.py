#!/usr/bin/env python3
"""The texture maps a visitor downloads, as lossless WebP beside their PNG masters.

T-1973. Dev's boot payload measured 14.27 MB against the 12 MB budget
(docs/SITE-BUDGET.md § 4), and the largest single class in it was 3.95 MB of PNG:
the relief maps the walls, roofs, street edge and signboards bind at boot (T-1488,
T-1815, T-1836, T-1963). PNG barely compresses under the origin's gzip — the maps
are procedural noise, already deflated — so those bytes reach the wire whole.

Lossless WebP carries the SAME PIXELS in about a quarter fewer bytes. Not
"visually the same": the same. Every one of these maps is data (a normal vector, a
packed occlusion/roughness/metal triple, a luminance ratio read for grain), and a
lossy codec would bend a normal and blur a roughness for a saving nobody could
then account for. This file is what makes the swap answerable:

    python3 tools/web_textures.py --write       write every derivative (deliberate act)
    python3 tools/web_textures.py --check       exit 1 unless every derivative decodes,
                                                pixel for pixel, to its PNG master
    python3 tools/web_textures.py --self-test   break each assertion, in memory

The PNG stays the master, in the library, where the generator writes it
(assets/textures/chicago_1835_pbr/tools/generate_1835_pbr_library.py). The WebP is
a derivative of it, the same relationship assets/web/ has to assets/gltf/, and it
is held the same way: by reading the bytes back, not by trusting the encoder.

THE ASSERTIONS
  1. Every map in SHIPPED has a .webp beside its .png.
  2. Each .webp decodes to exactly the master's size and to exactly its pixels
     (both read as RGB; the masters carry no alpha and no colour profile).
  3. No .webp in the library lacks a master or sits outside SHIPPED — an orphan
     is a file the site may serve that no master answers for.
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parent / "assets" / "textures" / "chicago_1835_pbr"

# The maps the renderer binds and tools/publish.sh ships, by library sheet. Each
# row names its reader; a map is here because a module asks for its .webp.
SHIPPED: dict[str, tuple[str, ...]] = {
    # renderers/web/js/roof-relief.js (T-1488)
    "roofs/wood_shingles_weathered": ("normal_gl", "orm"),
    "roofs/roof_boards_weathered": ("normal_gl", "orm"),
    # renderers/web/js/frontage.js (T-1815) and wall-relief.js (T-1963)
    "walls/clapboard_board_face": ("normal_gl", "orm", "basecolor"),
    # renderers/web/js/wall-relief.js (T-1963)
    "walls/hewn_log_face": ("normal_gl", "orm", "basecolor"),
    # renderers/web/js/signage.js (T-1836)
    "props/signboard_weathered": ("basecolor", "normal_gl"),
    "timber/heavy_timber_weathered": ("basecolor", "normal_gl"),
}


def _pil():
    try:
        from PIL import Image  # noqa: WPS433
    except ImportError:
        print("web_textures: Pillow is not installed — `pip install Pillow`; a GATE may not "
              "count a skip as a pass", file=sys.stderr)
        sys.exit(2)
    return Image


def pairs(library: Path = LIBRARY):
    for sheet, maps in SHIPPED.items():
        sid = sheet.split("/")[-1]
        for m in maps:
            yield library / sheet / f"{sid}_{m}.png", library / sheet / f"{sid}_{m}.webp"


def encode(png: Path) -> bytes:
    Image = _pil()
    im = Image.open(png).convert("RGB")
    out = io.BytesIO()
    # method 6 is the slowest, smallest lossless search; exact keeps every value.
    im.save(out, "WEBP", lossless=True, quality=100, method=6, exact=True)
    return out.getvalue()


def problems(library: Path = LIBRARY, read=lambda p: p.read_bytes()) -> list[str]:
    Image = _pil()
    found: list[str] = []
    expected = set()
    for png, webp in pairs(library):
        expected.add(webp)
        rel = webp.relative_to(library)
        if not png.exists():
            found.append(f"{rel}: its master {png.name} is not in the library")
            continue
        try:
            data = read(webp)
        except FileNotFoundError:
            found.append(f"{rel}: missing — run python3 tools/web_textures.py --write")
            continue
        master = Image.open(png).convert("RGB")
        try:
            shipped = Image.open(io.BytesIO(data))
            shipped.load()
        except Exception as err:  # noqa: BLE001 — any decode failure is the finding
            found.append(f"{rel}: does not decode ({err})")
            continue
        if shipped.format != "WEBP":
            found.append(f"{rel}: is {shipped.format}, not WebP")
            continue
        shipped = shipped.convert("RGB")
        if shipped.size != master.size:
            found.append(f"{rel}: {shipped.size} against its master's {master.size}")
            continue
        if shipped.tobytes() != master.tobytes():
            found.append(f"{rel}: its pixels differ from {png.name} — a lossy or stale "
                         f"derivative; re-run --write")
    for webp in library.rglob("*.webp"):
        if webp not in expected:
            found.append(f"{webp.relative_to(library)}: an orphan — no SHIPPED row answers for it")
    return found


def write(library: Path = LIBRARY) -> None:
    total_png = total_webp = 0
    for png, webp in pairs(library):
        data = encode(png)
        webp.write_bytes(data)
        total_png += png.stat().st_size
        total_webp += len(data)
        print(f"  {webp.relative_to(library)}  {png.stat().st_size:>8} -> {len(data):>8}")
    print(f"wrote {sum(len(v) for v in SHIPPED.values())} derivative(s): "
          f"{total_png / 1048576:.3f} MB of PNG -> {total_webp / 1048576:.3f} MB of WebP")


def self_test() -> int:
    """Each assertion must fire on the fault it names, against an in-memory library."""
    import shutil
    import tempfile
    Image = _pil()
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        lib = Path(tmp)
        for png, _ in pairs(LIBRARY):
            dst = lib / png.relative_to(LIBRARY)
            dst.parent.mkdir(parents=True, exist_ok=True)
            # A small crop keeps the self-test to a second; the assertions are size-blind.
            Image.open(png).convert("RGB").crop((0, 0, 32, 32)).save(dst)
        for png, webp in pairs(lib):
            webp.write_bytes(encode(png))
        if problems(lib):
            failures.append(f"a faithful library reads as broken: {problems(lib)[:2]}")
        first_png, first_webp = next(pairs(lib))
        cases = []
        # 1. missing
        cases.append(("a missing derivative", lambda: first_webp.unlink(), "missing"))
        # 2. lossy pixels
        def lossy():
            out = io.BytesIO()
            Image.open(first_png).convert("RGB").save(out, "WEBP", quality=60)
            first_webp.write_bytes(out.getvalue())
        cases.append(("a lossy derivative", lossy, "pixels differ"))
        # 2. wrong size
        def resized():
            out = io.BytesIO()
            Image.open(first_png).convert("RGB").resize((16, 16)).save(out, "WEBP", lossless=True)
            first_webp.write_bytes(out.getvalue())
        cases.append(("a resized derivative", resized, "against its master"))
        # 2. not WebP at all
        cases.append(("a PNG renamed .webp", lambda: shutil.copy(first_png, first_webp), "not WebP"))
        # 3. orphan
        orphan = lib / "walls" / "stray_orphan.webp"
        cases.append(("an orphan", lambda: orphan.write_bytes(encode(first_png)), "orphan"))
        for name, breakit, needle in cases:
            for png, webp in pairs(lib):
                webp.write_bytes(encode(png))
            orphan.unlink(missing_ok=True)
            breakit()
            got = problems(lib)
            if not any(needle in p for p in got):
                failures.append(f"{name} was not caught (got {got[:2]})")
            else:
                print(f"  ok  {name} fails the gate")
    for f in failures:
        print(f"SELF-TEST FAILED: {f}", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.write:
        write()
        return 0
    if a.self_test:
        return self_test()
    found = problems()
    for p in found:
        print(f"FAIL {p}", file=sys.stderr)
    if not found:
        n = sum(len(v) for v in SHIPPED.values())
        print(f"{n} WebP derivative(s) decode pixel-identical to their PNG masters")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
