#!/usr/bin/env python3
"""The street edge's face enumeration, driven over the cross streets it does not
yet carry.

WHY THIS EXISTS. `tools/generate_frontage_works.py` lays the town's plank walks
on the block faces that front a covered street, and until T-0192 it enumerated
two faces of four: an east-west street bounds a block on its NORTH or SOUTH
face, a cross street on its EAST or WEST, and only the first pair was ever
looked at. Naming Clark Street in the covered tuple would therefore have laid
nothing at all — silently, with no refusal on the record — whatever the frame
budget said.

T-0192 enumerated all four and made every ordering in that generator axis-aware:
a face's position along Lake Street is its easting and along Clark Street its
northing, and the corner crossings, the across-the-road pairing and the face
sort all read the street's own axis now. **And then the seven cross streets were
measured and left out**: all three scene-detail tiers go over their ceilings with
them in, by 145,639 / 122,299 / 15,372 triangles at T-0135's worst stand, on a
`dev` that stands half of one per cent inside two of those ceilings before a
board is laid. The numbers are on the record, in that generator's own `refused`.

So `EDGE_CROSS_STREETS` is empty and the whole east/west path would be DEAD CODE
— written, measured once, and then never executed by any gate, free to rot until
the day the budget is won back and somebody trusts it. This test is what keeps it
alive: it drives the generator's own rule over all seven cross streets on every
commit and asserts the answers the plat gives, in about a hundredth of a second
and without building a single board.

    python3 tools/test_frontage_faces.py
    python3 tools/test_frontage_faces.py --self-test   # the assertions must fire
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_frontage_works as G   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOTS = ROOT / "data" / "traces" / "vectors" / "thompson_lots.json"

FAILED = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  ok   {label}")
    else:
        FAILED.append(label)
        print(f"  FAIL {label}{(' — ' + detail) if detail else ''}")


def faces_with(cross: tuple, lots: dict) -> list:
    """`_edge_faces` run with a given covered cross-street tuple. The generator
    reads `EDGE_CROSS_STREETS` at call time for exactly this reason."""
    was = G.EDGE_CROSS_STREETS
    try:
        G.EDGE_CROSS_STREETS = cross
        return G._edge_faces(lots)
    finally:
        G.EDGE_CROSS_STREETS = was


def main(break_it: bool = False) -> int:
    lots = json.loads(LOTS.read_text())
    seven = G.EDGE_CROSS_STREETS_ALL
    if break_it:
        # The self-test's fault: enumerate the east-west faces only, which is
        # what this generator did before T-0192 — the exact regression this file
        # exists to catch. The checks that COUNT cross-street faces must go red;
        # the ones that walk them go vacuous, which is what a silent enumeration
        # failure looks like and is the reason a bare count is asserted first.
        seven = ()

    shipped = faces_with(G.EDGE_CROSS_STREETS, lots)
    check("the shipped tuple lays only east-west faces",
          {f["face"] for f in shipped} <= {"north", "south"} if G.EDGE_CROSS_STREETS == ()
          else True)

    got = faces_with(seven, lots)
    cross = [f for f in got if f["axis"] == 1]
    along = [f for f in got if f["axis"] == 0]

    # 1. THE PLAT'S OWN COUNT. Seventeen blocks of the South Division are bounded
    #    east and west by a cross street; `blk_lake_clinton` is skipped as the
    #    West Division block, and Canal and Clinton Streets bound only it.
    check("the seven cross streets have 34 platted faces", len(cross) == 34,
          f"got {len(cross)}")
    check("naming the cross streets does not disturb the east-west faces",
          len(along) == len(faces_with((), lots)),
          f"{len(along)} vs {len(faces_with((), lots))}")
    check("no skipped block is enumerated",
          not any(f["block"]["id"] in G.EDGE_SKIP_BLOCKS for f in got))
    check("Canal and Clinton are not covered",
          not any(f["street"] in ("canal", "clinton") for f in got))

    # 2. THE SIDE IS THE OTHER WAY ABOUT FROM THE FACE, which is the clause that
    #    pairs a face with the one opposite it across the road. A block bounded
    #    on its EAST face lies WEST of that street.
    check("an east face stands on its street's west side",
          all(f["side"] == "west" for f in cross if f["face"] == "east"))
    check("a west face stands on its street's east side",
          all(f["side"] == "east" for f in cross if f["face"] == "west"))
    check("both sides of every covered cross street are found",
          all({f["side"] for f in cross if f["street"] == s} == {"east", "west"}
              for s in ("franklin", "wells", "lasalle", "clark", "dearborn")),
          "Market and State are the town's outer edges and front on one side only")

    # 3. THE AXIS, and it is the whole of the change. A face is ordered along the
    #    street it fronts, so a cross street's faces must come out sorted by
    #    NORTHING; sorting them by easting is the ninety-degree error this
    #    enumeration was written to make impossible.
    for street in G.EDGE_CROSS_STREETS_ALL if not break_it else ("clark",):
        for side in ("east", "west"):
            run = [f for f in cross if f["street"] == street and f["side"] == side]
            ns = [f["frame"]["origin"][1] for f in run]
            check(f"{street} {side} side is ordered by northing", ns == sorted(ns),
                  f"{ns}")

    # 4. THE FRAME IS THE PLAT'S, not this test's: a cross street runs north-south,
    #    so its faces' outward normals must point east or west, and their along
    #    axes north or south. A face_frame that came back rotated would pass every
    #    count above and lay every board across the street.
    for f in cross:
        e, n = f["frame"]["outward"]
        check(f"{f['block']['id']} {f['face']} face looks across its street",
              abs(e) > abs(n), f"outward {f['frame']['outward']}")

    # 5. A CROSS-STREET FACE IS THE END OF A LOT ROW. Every lot in the Thompson
    #    plat fronts an east-west street, which is why the fence and hitching-post
    #    rules — both per-lot — have nothing to stand on there, and why the
    #    generator writes that refusal instead of leaving a silence.
    tiers = {lot.get("tier") for f in got for lot in f["block"].get("lots", [])}
    check("no platted lot fronts a cross street", tiers <= {"north", "south"},
          f"tiers {sorted(t for t in tiers if t)}")

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"frontage face enumeration OK — {len(along)} east-west faces, "
          f"{len(cross)} cross-street faces over "
          f"{len(G.EDGE_CROSS_STREETS_ALL)} cross streets")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("SELF-TEST: the cross-street faces are withheld; the counts must fire.")
        rc = main(break_it=True)
        if rc == 0:
            print("SELF-TEST FAILED: the assertions passed on a broken enumeration.")
            sys.exit(1)
        print("self-test OK — the assertions fire when the enumeration is wrong.")
        sys.exit(0)
    sys.exit(main())
