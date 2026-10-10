#!/usr/bin/env python3
"""No trim board lies flat on its own wall. (T-2104)

WHY THIS EXISTS. `MeshBuilder.add_box` names its faces by axis: "front" is the y0
face and "back" the y1 face. On a +y street facade a board runs from the wall at y
out to y + t, so "front" is the face nailed to the wall and "back" is the face the
street sees. The storefront archetype built its fascia, pilasters, mullion boards
and counter sills skipping "back": every shopfront in the town had a header board
with no street face and a face lying exactly ON the wall behind it. The renderer
draws buildings double-sided, so that face and the wall fought for the same depth
and the header flickered as a visitor turned in front of it (owner, 2026-10-04,
Rockwell's cabinet warehouse on South Water). The house stoops had the same skip.

Nothing failed. The meshes were valid, the GLB contract held, and the board still
read as a board from most angles because its ends and top were built.

So this builds every frame storefront, frame dwelling and frame tavern in the town,
without Blender, and refuses a TRIM face that lies on another material's face —
same upright axis-aligned plane, overlapping by more than a square centimetre — unless the
trim face is the hidden side of a board, i.e. the same rectangle stands again a
board's thickness away. That is exactly the shape of the fault: a board whose only
face along the wall is the one on the wall.

    python3 tools/test_facade_board_faces.py
    python3 tools/test_facade_board_faces.py --self-test   # the assertions must fire
"""

from __future__ import annotations

import collections
import itertools
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

# The generators import bpy for Blender's mesh calls; this reads the face lists the
# builders accumulate before any of that, so a stub is enough.
sys.modules.setdefault("bpy", types.ModuleType("bpy"))

from common import mesh as M  # noqa: E402
from archetypes import frame_dwelling, frame_storefront, frame_tavern  # noqa: E402
from archetypes.frame_dwelling_params import from_phase as dwelling_params  # noqa: E402
from archetypes.frame_storefront_params import from_phase as storefront_params  # noqa: E402
from archetypes.frame_tavern_params import from_phase as tavern_params  # noqa: E402



def _emit(self, mats=None):
    """The real `to_object`'s bookkeeping without Blender: the openings kit's named
    materials (T-2278) are appended after the archetype's list and their indices
    remapped, so `mats[i]` names every face's material."""
    mats = list(mats or [])
    base = len(mats)
    for name, _spec in sorted(self.named.items(), key=lambda kv: kv[1][0]):
        mats.append(name)
    self.mat_index = [base + (mi - self.NAMED_BASE) if mi >= self.NAMED_BASE else mi
                      for mi in self.mat_index]
    return self, mats


M.MeshBuilder.to_object = _emit
for _mod in (frame_dwelling, frame_storefront, frame_tavern):
    _mod.simple_material = lambda name, *a, **k: name

ARCHETYPES = {
    "frame_storefront": (storefront_params, frame_storefront.build),
    "frame_dwelling": (dwelling_params, frame_dwelling.build),
    "frame_tavern": (tavern_params, frame_tavern.build),
}

MIN_OVERLAP_M2 = 1e-4     # a square centimetre
BOARD_MAX_M = 0.25        # the thickest board a "hidden side" twin may stand off


def _plane_faces(b):
    """Every axis-aligned face as (axis, plane, lo, hi, material index)."""
    out = []
    for fi, f in enumerate(b.faces):
        pts = [b.verts[i] for i in f]
        for ax in range(3):
            vals = [p[ax] for p in pts]
            if max(vals) - min(vals) < 1e-6:
                o = [k for k in range(3) if k != ax]
                lo = tuple(round(min(p[k] for p in pts), 4) for k in o)
                hi = tuple(round(max(p[k] for p in pts), 4) for k in o)
                out.append((ax, round(vals[0], 4), lo, hi, b.mat_index[fi]))
                break
    return out


def exposed_trim_on_wall(b, mats) -> list[str]:
    faces = _plane_faces(b)
    rects = collections.defaultdict(list)
    for ax, c, lo, hi, m in faces:
        rects[(ax, m, lo, hi)].append(c)

    def board_side(f):
        ax, c, lo, hi, m = f
        return any(1e-4 < abs(o - c) < BOARD_MAX_M for o in rects[(ax, m, lo, hi)])

    by_plane = collections.defaultdict(list)
    for f in faces:
        by_plane[(f[0], f[1])].append(f)
    found = []
    for (ax, c), group in by_plane.items():
        if ax == 2:
            continue      # walls and the boards nailed to them stand upright
        for f, g in itertools.combinations(group, 2):
            if f[4] == g[4]:
                continue
            trim = [x for x in (f, g) if mats[x[4]] == "trim"]
            if not trim or any(board_side(x) for x in (f, g)):
                continue
            w = min(f[3][0], g[3][0]) - max(f[2][0], g[2][0])
            h = min(f[3][1], g[3][1]) - max(f[2][1], g[2][1])
            if w > 0 and h > 0 and w * h > MIN_OVERLAP_M2:
                other = g if trim[0] is f else f
                found.append(f"{'xyz'[ax]}={c} trim {trim[0][2]}..{trim[0][3]} on "
                             f"{mats[other[4]]} ({w * h:.3f} m²)")
    return found


def main() -> int:
    built = 0
    failures: dict[str, list[str]] = {}
    per_arch = collections.Counter()
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        arch = ARCHETYPES.get(rec.get("archetype"))
        if arch is None:
            continue
        for phase in rec.get("phases", []):
            b, mats = arch[1](arch[0](phase, rec), rec["id"])
            built += 1
            per_arch[rec["archetype"]] += 1
            bad = exposed_trim_on_wall(b, mats)
            if bad:
                failures[f"{rec['id']}/{phase.get('id')}"] = bad
    print(f"  built {built} phases: "
          + ", ".join(f"{k} {v}" for k, v in sorted(per_arch.items())))
    ok = built > 0 and not failures
    if built == 0:
        print("  FAIL: built nothing — the structure records moved or the archetype key did")
    for sid, bad in list(failures.items())[:12]:
        print(f"  FAIL: {sid}: {len(bad)} trim face(s) lie on a wall with no street face — "
              f"{bad[0]}")
    if len(failures) > 12:
        print(f"  … and {len(failures) - 12} more")
    if ok:
        print("  OK  : no trim board in the frame town lies flat on its own wall")
    return 0 if ok else 1


def self_test() -> int:
    """Re-introduce the fault — every board on a +y face skipping its street side
    instead of its wall side — and require the gate to name it."""
    real = M.MeshBuilder.add_box

    def inverted(self, x0, y0, z0, x1, y1, z1, confidence, mat=0, skip=()):
        skip = tuple("back" if s == "front" else s for s in skip)
        return real(self, x0, y0, z0, x1, y1, z1, confidence, mat, skip=skip)

    M.MeshBuilder.add_box = inverted
    try:
        rc = main()
    finally:
        M.MeshBuilder.add_box = real
    if rc == 0:
        print("self-test FAIL — the gate passed a town whose boards lie on their walls")
        return 1
    print("self-test OK — the assertions fire when a board's street face goes missing.")
    return 0


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else main())
