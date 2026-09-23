#!/usr/bin/env python3
"""derive_timber_belt.py — where the South Water Street timber belt stood.

TICKET T-0031 (ROADMAP R-BUG5(b)). R-BUG5 measured `FAR_TIMBER.main_stem_belt_east`
standing in the main stem — 39 of 39 samples over water, 3.347 m under its
surface — and the renderer has refused to draw it since. Repairing it means
choosing where the belt's near edge ran, and Andreas does not say. The owner
ruled on 2026-08-17: **route 1, derive it from the committed `south_water`
street centreline**, the same move `south_branch_belt` already makes off the
river's modern course, and record the side of the street as a liberty.

THE RULE, and every number in it comes from `data/streets/1835.json`
--------------------------------------------------------------------
    the belt line = the committed `south_water` centreline
                  · offset half a platted corridor (12.192 m) to the SOUTH
                  · clipped east at the mean easting of the committed `wells`
                    centreline (E +329.3)

Three parts, and only one of them is an assertion:

1. **The line** is South Water Street's own committed path. Andreas puts the
   South Side timber "along the river", and this street is the committed line
   that follows that bank; nothing else in the dataset traces it.
2. **The east end** is Wells Street, which Andreas states outright — the belt
   "extend[ed] east as far as Wells Street". It is read as the mean of the
   street's point eastings, which is EXACTLY what `timberEastLimits()` in
   `renderers/web/js/trees.js` gives the near-field planter for the same limit.
   One street record, one number, so the far body and the near wood cannot
   disagree about where the belt ends.
3. **The side of the street is asserted** — `docs/LIBERTIES.md` L182. Andreas
   does not say which side the standing timber was on. South is chosen because
   the dossier's own reading of the same sentence puts the survivors in the
   riverside BLOCKS (`docs/research/02-flora.md`: relict native trees "8-25 /ha
   in the north/riverside blocks (South Water-Lake, west of Wells)"), and
   because by 1 July 1835 the strip between the street and the water is the
   town's working waterfront — 11.5 to 36.0 m of dry ground carrying the
   wharves. Half a corridor is where the platted lot line runs: the timber
   begins at the back of the street, not in it.

WHY THIS IS A TOOL AND NOT A COMMITTED COORDINATE
-------------------------------------------------
`main_stem_belt_east` was authored on a Wells Street 66.7 m east of where the
committed centreline puts it, and that error is half of why it ended up in the
river. K45(b2) found the same error in `z05_riverbank_timber`'s note (440 m out)
and fixed it the same way: read the street, do not restate it. So the path stays
a literal in `trees.js` — the census in `measure_far_timber.py` reads the
renderer's own table and must keep being able to — and `--check` re-derives it
from the street record on every commit. Move South Water Street and this fails
until the belt is moved with it.

    tools/derive_timber_belt.py           print the derivation and the drift
    tools/derive_timber_belt.py --check   fail on drift (tools/check.sh)
    tools/derive_timber_belt.py --write   rewrite the path literal in trees.js
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from measure_far_timber import Fault, read_far_timber  # noqa: E402

STREETS = ROOT / "data" / "streets" / "1835.json"
TREES_JS = ROOT / "renderers" / "web" / "js" / "trees.js"

BODY_ID = "main_stem_belt_east"
LINE_STREET = "south_water"
EAST_LIMIT_STREET = "wells"
#: Metres. Rounded at authoring so the literal in trees.js and the derivation
#: are the same number rather than the same number to a tolerance.
PLACES = 2


def street(records: list[dict], ident: str) -> dict:
    for rec in records:
        if rec.get("id") == ident:
            return rec
    raise Fault(f"data/streets/1835.json carries no street `{ident}` — the belt is "
                "derived from it and cannot be derived without it")


def east_limit(records: list[dict]) -> float:
    """Wells Street's easting, the way `timberEastLimits()` reads it.

    The mean of the centreline's point eastings. A street is not exactly
    north-south — Wells runs E +328.1 at N -400 to E +330.5 at N +7 — and a mean
    cannot be wrong in the way picking one end can. Restated here rather than
    imported because the renderer's copy is JavaScript; the two are asserted
    equal by `--check` reading the same file the renderer loads.
    """
    pts = street(records, EAST_LIMIT_STREET)["path_local_enu_m"]
    return sum(p[0] for p in pts) / len(pts)


def clip_east(path: list[list[float]], limit: float) -> list[list[float]]:
    """The centreline west of `limit`, ending exactly ON it.

    The last point is interpolated rather than dropped: a belt that ended at the
    last vertex WEST of Wells would stop 109 m short of the street its own
    source names, which is the error this whole parcel is repairing in reverse.
    """
    out: list[list[float]] = []
    for i, (e, n) in enumerate(path):
        if e <= limit:
            out.append([float(e), float(n)])
            continue
        if i == 0:
            raise Fault(f"{LINE_STREET} begins east of {EAST_LIMIT_STREET} — the belt "
                        "has no reach to derive")
        ae, an = path[i - 1]
        f = (limit - ae) / (e - ae)
        out.append([limit, an + (n - an) * f])
        break
    if len(out) < 2:
        raise Fault(f"{LINE_STREET} clipped at {EAST_LIMIT_STREET} leaves fewer than "
                    "two points")
    return out


def offset_south(path: list[list[float]], distance: float) -> list[list[float]]:
    """The polyline moved `distance` metres to its south side.

    A mitred offset: each vertex moves along the bisector of its two adjacent
    segment normals, scaled so the result is exactly `distance` from BOTH
    segments. Offsetting each vertex along one segment's normal instead pulls
    the line in at every bend, and South Water's west approach bends through
    50 degrees in 170 m.
    """
    def unit_right_normal(a: list[float], b: list[float]) -> tuple[float, float]:
        de, dn = b[0] - a[0], b[1] - a[1]
        length = math.hypot(de, dn)
        if length == 0:
            raise Fault("a street centreline repeats a point; the belt cannot be offset")
        # Walking east, the right hand points south: direction (1, 0) -> (0, -1).
        return (dn / length, -de / length)

    normals = [unit_right_normal(path[i], path[i + 1]) for i in range(len(path) - 1)]
    out = []
    for i, (e, n) in enumerate(path):
        n1 = normals[max(0, i - 1)] if i else normals[0]
        n2 = normals[min(i, len(normals) - 1)]
        me, mn = n1[0] + n2[0], n1[1] + n2[1]
        length = math.hypot(me, mn)
        if length < 1e-9:                       # a 180-degree reversal; not a street
            me, mn, length = n2[0], n2[1], 1.0
        me, mn = me / length, mn / length
        scale = distance / (me * n1[0] + mn * n1[1])
        out.append([round(e + me * scale, PLACES), round(n + mn * scale, PLACES)])
    return out


def derive() -> tuple[list[list[float]], dict]:
    doc = json.loads(STREETS.read_text(encoding="utf-8"))
    records = doc["streets"]
    line = street(records, LINE_STREET)
    corridor = line.get("corridor_width_m", doc["corridor_width_m"])
    limit = east_limit(records)
    clipped = clip_east(line["path_local_enu_m"], limit)
    belt = offset_south(clipped, corridor / 2)
    length = sum(math.hypot(belt[i + 1][0] - belt[i][0], belt[i + 1][1] - belt[i][1])
                 for i in range(len(belt) - 1))
    return belt, {
        "street": LINE_STREET,
        "corridor_width_m": corridor,
        "offset_m": corridor / 2,
        "east_limit_street": EAST_LIMIT_STREET,
        "east_limit_e": round(limit, 4),
        "points": len(belt),
        "length_m": round(length, 1),
    }


def committed() -> list[list[float]]:
    bodies = {b["id"]: b["path"] for b in read_far_timber(
        TREES_JS.read_text(encoding="utf-8"))}
    if BODY_ID not in bodies:
        raise Fault(f"FAR_TIMBER no longer carries `{BODY_ID}` — the belt this tool "
                    "derives is not in the renderer's table")
    return bodies[BODY_ID]


def as_literal(belt: list[list[float]]) -> str:
    """The path as trees.js writes one: `[[e, n], [e, n], …]`, wrapped at 78."""
    pieces = [f"[{e:g}, {n:g}]" for e, n in belt]
    lines, cur = [], "    path: ["
    for i, piece in enumerate(pieces):
        tail = "," if i < len(pieces) - 1 else "],"
        if len(cur) + len(piece) + len(tail) > 78 and cur.strip() != "path: [":
            lines.append(cur.rstrip())
            cur = "      "
        cur += piece + tail + (" " if tail == "," else "")
    lines.append(cur.rstrip())
    return "\n".join(lines)


def write(belt: list[list[float]]) -> None:
    src = TREES_JS.read_text(encoding="utf-8")
    block = re.search(r"(\{\s*\n\s*id: '" + BODY_ID + r"',.*?\n  \},)", src, re.S)
    if not block:
        raise Fault(f"cannot find the `{BODY_ID}` entry in trees.js to rewrite")
    old = block.group(1)
    new = re.sub(r"    path: \[.*?\],\n", as_literal(belt) + "\n", old, flags=re.S)
    if new == old:
        raise Fault(f"the `{BODY_ID}` entry has no `path: [ … ],` line to rewrite")
    TREES_JS.write_text(src.replace(old, new), encoding="utf-8")
    print(f"  rewrote FAR_TIMBER.{BODY_ID} in {TREES_JS.relative_to(ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if the belt has drifted")
    ap.add_argument("--write", action="store_true", help="rewrite the path in trees.js")
    args = ap.parse_args()

    belt, how = derive()
    if args.write:
        write(belt)
        return 0

    have = committed()
    drifted = len(have) != len(belt) or any(
        abs(a[0] - b[0]) > 1e-9 or abs(a[1] - b[1]) > 1e-9 for a, b in zip(have, belt))
    print(f"  the South Water belt, derived from `{how['street']}` offset "
          f"{how['offset_m']:.3f} m south and clipped at `{how['east_limit_street']}` "
          f"(E +{how['east_limit_e']:.1f})")
    print(f"  {how['points']} points, {how['length_m']:.1f} m of belt")
    if not drifted:
        print("  PASS — FAR_TIMBER.main_stem_belt_east is the derived line")
        return 0
    print("  FAIL — the committed belt is not the line the street derives (T-0031)")
    print(f"    committed {json.dumps(have)}")
    print(f"    derived   {json.dumps(belt)}")
    print("    re-derive with tools/derive_timber_belt.py --write")
    return 1 if args.check else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fault as exc:
        print(f"  FAIL — {exc}")
        sys.exit(1)
