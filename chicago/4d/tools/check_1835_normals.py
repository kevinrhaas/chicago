#!/usr/bin/env python3
"""T-2299 — the 1835 PBR library's normal maps are handed the way they are named.

    python3 tools/check_1835_normals.py --check       exit 1 on a map handed wrong
    python3 tools/check_1835_normals.py --self-test   break each rule, in memory

The library (assets/textures/chicago_1835_pbr/) ships every material twice: an OpenGL
`normal_gl` (+Y up the image) and a DirectX `normal_dx` (-Y). Its generator wrote green
as -dh/drow, the DirectX sign, into the OpenGL file, and wrote the OpenGL map under the
DirectX name — the same slip T-2296 found in the 1904 street library. Every reader in
the renderer binds `normal_gl` through a flipY'd texture (frontage.js, wall-relief.js,
roof-relief.js; signage.js turns it a quarter as an OpenGL map), so the relief of every
board, log, shingle and signboard in 1835 was lit upside down along +V.

THE RULES, for each of the 27 materials, read against the material's own `height16`:
  1. `normal_gl.png` is OpenGL-handed: red tracks -dh/dx and green +dh/drow.
  2. `normal_dx.png` is DirectX-handed: red the same, green -dh/drow.
  3. Every `normal_gl.webp` the renderer binds is OpenGL-handed (web_textures.py holds
     it pixel-identical to its master; this holds the sign it carries).

Measured as correlation (check_street_surfaces.handedness), so it reads the sign and
not the strength: dev's maps read green -0.80..-1.00 under the OpenGL name before
T-2299. It re-reads rasters, so with no numpy or Pillow it says so and stands aside
(tools/check_gate_readers.py makes that red in CI). It reads; it writes nothing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_street_surfaces import HANDED_MIN, handed_faults, handedness  # noqa: E402

LIBRARY = HERE.parent / "assets" / "textures" / "chicago_1835_pbr"


def dx_faults(where: str, c: dict) -> list:
    bad = []
    if not c["red"] <= -HANDED_MIN:
        bad.append(f"{where}: red reads {c['red']:+.3f} against dh/dx; DirectX wants <= -{HANDED_MIN}")
    if not c["green"] <= -HANDED_MIN:
        bad.append(f"{where}: green reads {c['green']:+.3f} against dh/drow; DirectX wants <= "
                   f"-{HANDED_MIN} — a positive one is an OpenGL map")
    return bad


def materials(library: Path = LIBRARY) -> list:
    return sorted(d for d in library.glob("*/*") if (d / "material.json").exists())


def check(library: Path = LIBRARY):
    """(faults, lines, count), or None if the readers are missing."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    rgb = lambda p: np.asarray(Image.open(p).convert("RGB"), dtype=np.float64) / 255.0  # noqa: E731
    bad, lines, mats = [], [], materials(library)
    for d in mats:
        h = np.asarray(Image.open(d / f"{d.name}_height16.png"), dtype=np.float64) / 65535.0
        rel = f"{d.parent.name}/{d.name}"
        for name, rule in ((f"{d.name}_normal_gl.png", handed_faults),
                           (f"{d.name}_normal_dx.png", dx_faults),
                           (f"{d.name}_normal_gl.webp", handed_faults)):
            if not (d / name).exists():
                if name.endswith(".png"):
                    bad.append(f"{rel}: {name} is missing")
                continue
            c = handedness(h, rgb(d / name))
            lines.append(f"{rel + '/' + name.split(d.name + '_')[1]:58s} red {c['red']:+.3f}  green {c['green']:+.3f}")
            bad += rule(f"{rel}: {name}", c)
    if not mats:
        bad.append(f"no material.json under {library}")
    return bad, lines, len(mats)


def self_test() -> int:
    try:
        import numpy as np
    except ImportError:
        print("   skip: numpy is not installed (check_gate_readers.py names this)")
        return 0
    rows, cols = np.mgrid[0:64, 0:64] / 64.0
    h = 0.3 * rows + 0.2 * cols + 0.05 * np.sin(rows * 37) * np.cos(cols * 23)
    gx = np.roll(h, -1, 1) - np.roll(h, 1, 1)
    gy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    n = np.stack((-gx, gy, np.full_like(h, 0.02)), axis=-1)
    gl = n / np.linalg.norm(n, axis=-1, keepdims=True) * 0.5 + 0.5
    dx = gl.copy()
    dx[..., 1] = 1 - dx[..., 1]
    red = gl.copy()
    red[..., 0] = 1 - red[..., 0]
    got = check()
    cases = [
        ("an OpenGL map passes as normal_gl", not handed_faults("gl", handedness(h, gl))),
        ("a DirectX map passes as normal_dx", not dx_faults("dx", handedness(h, dx))),
        ("a DirectX map filed as normal_gl is refused (T-2299)",
         any("DirectX" in b for b in handed_faults("gl", handedness(h, dx)))),
        ("an OpenGL map filed as normal_dx is refused (T-2299)",
         any("OpenGL" in b for b in dx_faults("dx", handedness(h, gl)))),
        ("a map with red mirrored is refused under either name",
         bool(handed_faults("gl", handedness(h, red))) and bool(dx_faults("dx", handedness(h, red)))),
        ("an empty library is refused, not passed",
         got is None or bool(check(LIBRARY / "no-such-group")[0])),
        ("the committed library is handed as named, all 27 materials",
         got is not None and not got[0] and got[2] == 27),
    ]
    for label, ok in cases:
        print(("   ok   " if ok else "   FAIL ") + label)
    return 0 if all(ok for _, ok in cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    got = check()
    if got is None:
        print("SKIP the 1835 normals' handedness: numpy or Pillow is not installed — a banked "
              "reading, not a pass (tools/check_gate_readers.py)")
        return 0
    bad, lines, count = got
    for line in lines:
        print("  ", line)
    for b in bad:
        print("FAIL", b)
    print(f"{count} material(s), {len(lines)} normal map(s): "
          + ("handed as named" if not bad else f"{len(bad)} fault(s)"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
