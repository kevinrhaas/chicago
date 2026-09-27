#!/usr/bin/env python3
"""The freight shed's cargo openings: one set-out, read by three callers (T-1662).

WHY THIS EXISTS. Family F1 in the archetype crosswalk is the freight or storage
shed, `outbuilding` draws it, and its required variant is `freight_shed_low` —
*"wide doors; low openings"*. Until T-1662 the widest door this archetype had was
`wagon`, and a wagon door failed the family in two measurable ways:

  * `tools/family_bands.eave_floor` asks this archetype's own door table how much
    wall a door needs, so a 3.00 m wagon door clamped F1's eave FLOOR at 3.08 m —
    32 mm ABOVE the bottom of the 10-13 ft band the crosswalk authors for the same
    family. No F1 shed could be dealt the low end of its own band.
  * there was one of it, centred, on an eleven-metre shed.

WHAT THE RHYTHM COSTS IF IT DRIFTS, which is the reason for a test rather than a
reading. Three callers now have to agree about where the openings are: the builder
that draws the frames and leaves, `openings()` which cuts the holes in the boarding
and tells `tools/generate_business_signboards.py` where a board may not hang, and
the validator that refuses a count the wall cannot carry. They agree by all reading
`door_spans_m`. If any of them ever computes its own, the frames land in one place
and the holes in another, and nothing else in the gate would notice — a boarded
wall with a door frame on solid board beside a rectangular hole is a perfectly
valid mesh.

    python3 tools/test_outbuilding_cargo.py
    python3 tools/test_outbuilding_cargo.py --self-test   # the assertions must fire
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "generators"))

from archetypes import outbuilding_params as OB  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import family_bands as FB  # noqa: E402

FAILED: list = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"   — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


# F1's own authored band, from data/reconstruction/1835_family_archetype_crosswalk.json:
# footprint 18x32-28x50 ft, eave 10-13 ft. Retyped here as FEET and converted, so the
# test says which numbers it is holding the archetype to and where they come from.
FT = 0.3048
F1_EAVE_LO_M = round(10 * FT, 4)
F1_FRONT_LO_M = round(18 * FT, 4)
F1_FRONT_HI_M = round(28 * FT, 4)


def shed(width: float, depth: float, wall: float, bays: int = 2,
         door: str = "cargo") -> OB.OutbuildingParams:
    return OB.OutbuildingParams(width_m=width, depth_m=depth, wall_height_m=wall,
                                roof_type="gable", roof_pitch_deg=32.0,
                                construction="plank", door=door, door_bays=bays)


def main(break_it: bool = False) -> int:
    print("F1's cargo openings\n")

    # 1. THE OPENING IS LOW ENOUGH FOR THE FAMILY'S OWN EAVE BAND. This is the
    #    finding the ticket was filed on, and it is asked of the same function the
    #    parcel generators ask before they sample an eave.
    floor = FB.eave_floor("F1", "cargo")
    check("a cargo door lets F1 reach the bottom of its own 10-13 ft eave band",
          floor <= F1_EAVE_LO_M,
          f"eave_floor {floor} m vs the band's {F1_EAVE_LO_M} m")
    check("…which the wagon door it replaces did not",
          FB.eave_floor("F1", "wagon") > F1_EAVE_LO_M,
          f"wagon floor {FB.eave_floor('F1', 'wagon')} m")

    # 2. IT IS WIDE, in the family's word: wider than a horse led through in hand,
    #    and narrower than a team, because no team goes through it.
    cw, ch = OB.DOOR_SIZE_M["cargo"]
    check("a cargo opening is wider than a stable door and narrower than a wagon's",
          OB.DOOR_SIZE_M["stable"][0] < cw < OB.DOOR_SIZE_M["wagon"][0],
          f"{cw} m clear")
    check("…and lower than both the wagon door and the wall it stands in",
          ch < OB.DOOR_SIZE_M["wagon"][1], f"{ch} m clear")

    # 3. THE SET-OUT IS THE ONE THE VALIDATOR AND THE HOLE-CUTTER READ. `openings()`
    #    is what cuts the boarding and what the signboard generator reads; the spans
    #    are what the builder frames. A drift here is invisible to every other gate.
    p = shed(8.121, 11.336, 3.193)
    p.validate()
    spans = p.door_spans_m
    holes = [(u0, u1) for u0, u1, _z0, _z1 in OB.boarding_holes(p)[p.door_side]]
    if break_it:
        spans = [(u0 + 0.4, u1 + 0.4) for u0, u1 in spans]
    check("the frames and the holes in the boarding are the same rectangles",
          [tuple(round(v, 4) for v in s) for s in spans]
          == [tuple(round(v, 4) for v in h) for h in holes],
          f"frames {spans} vs holes {holes}")
    check("a two-bay shed has two openings and not one", len(spans) == 2,
          f"{len(spans)} span(s)")

    # 4. THE RHYTHM IS EVEN AND INSIDE THE WALL. An even set-out is the only one
    #    this project can defend: anything else claims a plan no source gives.
    left = spans[0][0] - OB.DOOR_JAMB_M
    right = p.side_run_m(p.door_side) - spans[-1][1] - OB.DOOR_JAMB_M
    between = spans[1][0] - OB.DOOR_JAMB_M - (spans[0][1] + OB.DOOR_JAMB_M)
    check("the piers at the corners and between the bays are equal",
          abs(left - right) < 1e-6 and abs(left - between) < 1e-6,
          f"{left:.4f} / {between:.4f} / {right:.4f} m")
    check("no opening runs off the end of its elevation",
          spans[0][0] > 0 and spans[-1][1] < p.side_run_m(p.door_side))

    # 5. ONE DOORWAY IS STILL CENTRED, BYTE FOR BYTE. 133 of the town's 134
    #    outbuildings carry a single door and this change may not move any of them.
    one = shed(8.121, 11.336, 3.193, bays=1, door="man")
    one.validate()
    (u0, u1), = one.door_spans_m
    dw, _dh = one.door_size_m
    check("a single door still stands in the middle of its wall",
          abs((u0 + u1) / 2.0 - one.side_run_m(one.door_side) / 2.0) < 1e-9
          and abs((u1 - u0) - dw) < 1e-9, f"({u0}, {u1})")

    # 6. AND THE ARCHETYPE REFUSES RATHER THAN THINS. Both refusals are what stop a
    #    rhythm being bought by shaving the wall between the doors.
    def refuses(label: str, **kw) -> None:
        try:
            shed(**kw).validate()
        except OB.ParamError:
            check(label, True)
            return
        check(label, False, "it built instead")

    refuses("three cargo bays on F1's narrowest front are refused",
            width=F1_FRONT_LO_M, depth=9.754, wall=3.2, bays=3)
    refuses("two wagon doors are refused on a front two cargo doors fit",
            width=7.315, depth=13.411, wall=3.721, bays=2, door="wagon")
    refuses("half a doorway is refused", width=8.121, depth=11.336, wall=3.2, bays=0)

    # 7. TWO BAYS FIT EVERY FRONT F1'S OWN FOOTPRINT BAND ALLOWS ABOVE THE MEDIAN,
    #    and that is the bound the 2.20 m width was chosen against.
    median = round((F1_FRONT_LO_M + F1_FRONT_HI_M) / 2.0, 4)
    ok = True
    for i in range(41):
        w = median + (F1_FRONT_HI_M - median) * i / 40.0
        try:
            shed(w, 9.754, 3.2).validate()
        except OB.ParamError:
            ok = False
            break
    check("two cargo bays build on every F1 front from the band's median up",
          ok, f"median front {median} m, top {F1_FRONT_HI_M} m")

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"F1's cargo openings OK — {cw} x {ch} m clear, eave floor {floor} m")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("SELF-TEST: the frames are shifted off the holes; the set-out check must fire.")
        rc = main(break_it=True)
        if rc == 0:
            print("SELF-TEST FAILED: the assertions passed on a drifted set-out.")
            sys.exit(1)
        print("self-test OK — the assertions fire when the set-out drifts.")
        sys.exit(0)
    sys.exit(main())
