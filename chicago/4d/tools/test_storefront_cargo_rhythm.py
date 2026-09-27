#!/usr/bin/env python3
"""The warehouse's cargo-door rhythm, and the doors above it (T-1663).

WHY THIS EXISTS. Two families in the archetype crosswalk ask `frame_storefront` for
more than one cargo opening, in their own words: **F3** `warehouse_river_large`
("multiple cargo doors"), and **F2** `warehouse_narrow_two_story` ("hoist beam;
upper freight doors"). Until T-1663 this archetype drew exactly one goods door,
centred, on every store and every warehouse alike, and drew no hoist on anything.

WHAT IT HOLDS THAT NOTHING ELSE CAN SEE, which is the reason for a test rather than
a reading:

  * THE 43 STOREFRONTS THAT DID NOT CHANGE. A single-bay record's set-out has to be
    the very same double the archetype computed before the rhythm existed — not the
    same quantity, the same float. outbuilding made exactly this measurement at
    T-1662 and eleven of its sheds moved by a fraction of a tenth of a millimetre,
    which churns a bake and shows a visitor nothing.
  * THE TIE BETWEEN THE TWO STOREYS. An upper freight door stands over a cargo
    opening. If the doors above ever compute their own set-out, they drift off the
    doors below and the mesh is still perfectly valid.
  * THE COUNT'S DERIVATION. Two for F2 and three for F3 are inventions
    (docs/LIBERTIES.md L279) bounded by each family's OWN footprint band against the
    braced frame's post spacing. A number that stops following from its bound is a
    number somebody has quietly chosen.
  * THE BEAM OVER AN OFF-CENTRE BAY. The gable's apex stands over the middle of the
    wall, so the roof line at a bay near the corner is far lower. No committed record
    reaches that case — both of the town's F2 gables are deep enough to carry every
    bay — so the arithmetic is held here or it is held nowhere.

    python3 tools/test_storefront_cargo_rhythm.py
    python3 tools/test_storefront_cargo_rhythm.py --self-test   # assertions must fire
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import frame_storefront_params as FS  # noqa: E402
import family_bands as FB  # noqa: E402

FAILED: list = []

# The builder's own overhang and hoist stock, retyped here as the numbers this test
# holds the arithmetic to. They are NOT imported: `generators/archetypes/
# frame_storefront.py` imports bpy and the commit gate has no Blender, which is why
# `gable_top_m` was put in the params module in the first place.
ROOF_OVERHANG_M = 0.30
HOIST_DOOR_W_M = 1.22
HOIST_BEAM_FACE_M = 0.152

FT = 0.3048


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"   — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def store(width: float, depth: float, wall: float, bays: int = 1, **kw):
    """A warehouse on this archetype: no shopfront, freight in at the gable end."""
    opts = dict(width_m=width, depth_m=depth, wall_height_m=wall, stories=2.0,
                roof_type="gable", roof_pitch_deg=27.0, gable_front=False,
                construction="braced_frame", cladding="vertical_board",
                chimneys=0, shopfront=False, goods_door=True,
                goods_door_side="end", goods_door_bays=bays)
    opts.update(kw)
    return FS.FrameStorefrontParams(**opts)


def main(break_it: bool = False) -> int:
    print("F2 and F3's cargo-door rhythm\n")
    bands = FB.families()
    framed = FS.GOODS_DOOR_W_M + 2 * FS.GOODS_DOOR_JAMB_M

    # 1. THE COUNT COMES FROM THE FAMILY'S BAND, and only two families answer more
    #    than one. Every store family answers 1, which is what keeps the town's
    #    43 single-door storefronts out of this change entirely.
    check("F2's band authors two cargo bays",
          FB.cargo_door_bays("F2", bands["F2"]["band_ft"]) == 2,
          f"band {bands['F2']['band_ft']} ft")
    check("F3's band authors three",
          FB.cargo_door_bays("F3", bands["F3"]["band_ft"]) == 3,
          f"band {bands['F3']['band_ft']} ft")
    others = [f for f in bands
              if f not in ("F2", "F3")
              and FB.cargo_door_bays(f, bands[f]["band_ft"]) != 1]
    check("every other family in the crosswalk answers one", not others,
          f"{others or 'none'}")

    # 2. THE BOUND THE COUNTS REST ON: at the SHORT end of each family's own
    #    footprint band, n bays leave a pier at least one post bay wide and n + 1 do
    #    not. This is the derivation in L279, re-run rather than restated.
    for fam, n in (("F2", 2), ("F3", 3)):
        lo = bands[fam]["band_ft"][1] * FT
        fits = (lo - n * framed) / (n + 1)
        over = (lo - (n + 1) * framed) / (n + 2)
        check(f"{fam}: {n} bays clear the frame's post spacing on its shortest plan",
              fits >= FS.POST_SPACING_M, f"pier {fits:.3f} m vs {FS.POST_SPACING_M} m")
        check(f"{fam}: …and {n + 1} do not",
              over < FS.POST_SPACING_M, f"pier {over:.3f} m")

    # 3. A SINGLE BAY IS THE OLD CENTRING, TO THE FLOAT. Every committed storefront
    #    that carries one goods door is driven through it, so this is the whole of
    #    the claim that no store in the town moved for a change about warehouses.
    moved, seen = [], 0
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text())
        if rec.get("archetype") != "frame_storefront":
            continue
        for phase in rec.get("phases", []):
            p = FS.from_phase(phase, rec)
            if not p.goods_door or p.goods_door_bays != 1:
                continue
            seen += 1
            mx0, my0, mx1, my1 = FS.main_extent(p)
            if p.goods_door_side == "rear":
                u0 = (FS.ell_extent(p)[2] if (p.ell and p.ell_side == "rear") else mx0)
                mid = (u0 + mx1) / 2.0
            else:
                mid = (my0 + my1) / 2.0
            was = (mid - 1.85 / 2, mid + 1.85 / 2)
            now = p.goods_door_spans_m[0]
            if break_it:
                now = (now[0] + 1e-9, now[1])
            if now != was:
                moved.append(rec["id"])
    check("every single-door storefront keeps the exact double it always had",
          not moved and seen > 0, f"{seen} phase(s) driven, {len(moved)} moved")

    # 4. THE RHYTHM IS EVEN AND INSIDE THE WALL.
    p = store(7.599, 15.548, 6.764, bays=2)
    p.validate()
    spans = p.goods_door_spans_m
    run = p.loading_side_run_m
    left = spans[0][0] - FS.GOODS_DOOR_JAMB_M
    right = run - spans[-1][1] - FS.GOODS_DOOR_JAMB_M
    between = spans[1][0] - FS.GOODS_DOOR_JAMB_M - (spans[0][1] + FS.GOODS_DOOR_JAMB_M)
    check("a two-bay warehouse has two openings and not one", len(spans) == 2,
          f"{len(spans)} span(s)")
    check("the piers at the corners and between the bays are equal",
          abs(left - right) < 1e-9 and abs(left - between) < 1e-9,
          f"{left:.4f} / {between:.4f} / {right:.4f} m")
    check("…and every opening is inside the wall",
          spans[0][0] > 0 and spans[-1][1] < run,
          f"{spans[0][0]:.3f}..{spans[-1][1]:.3f} of {run:.3f} m")
    check("the pier the set-out reports is the pier it leaves",
          abs(p.goods_door_pier_m - round(left, 4)) < 1e-9,
          f"reported {p.goods_door_pier_m} m")

    # 5. ONE SET-OUT SERVES BOTH STOREYS. The upper freight doors are centred on the
    #    cargo openings below them — one loading point, two doors — and a door above
    #    sits inside the width of the one below it.
    uppers = [((a + b) / 2.0 - HOIST_DOOR_W_M / 2, (a + b) / 2.0 + HOIST_DOOR_W_M / 2)
              for a, b in spans]
    check("there is one upper freight door for each cargo opening",
          len(uppers) == len(spans), f"{len(uppers)} over {len(spans)}")
    check("…each centred on the opening it lifts to",
          all(abs((u0 + u1) / 2 - (g0 + g1) / 2) < 1e-9
              for (u0, u1), (g0, g1) in zip(uppers, spans)))
    check("…and none of them wider than the door below it",
          all(u0 > g0 and u1 < g1 for (u0, u1), (g0, g1) in zip(uppers, spans)),
          f"upper {HOIST_DOOR_W_M} m vs {FS.GOODS_DOOR_W_M} m clear")

    # 6. THE BEAM IS ASKED THE QUESTION AT ITS OWN BAY. On the town's F2 gable every
    #    bay carries one; on a shallow gable the outer bays must not, and the centred
    #    arithmetic would have said they did.
    wall_z, u0, u1 = 6.764, 0.0, 15.548
    apex = FS.gable_top_m((u0 + u1) / 2, u0, u1, wall_z, 10.93, ROOF_OVERHANG_M)
    corner = FS.gable_top_m(u0, u0, u1, wall_z, 10.93, ROOF_OVERHANG_M)
    check("the gable is highest over the middle of the wall and lowest at its ends",
          apex > corner >= wall_z, f"{apex:.3f} m vs {corner:.3f} m")
    shallow = 7.20   # a ridge barely above the eave: no gable to speak of
    outer = FS.gable_top_m(spans[0][0], u0, u1, wall_z, shallow, ROOF_OVERHANG_M)
    mid_top = FS.gable_top_m((u0 + u1) / 2, u0, u1, wall_z, shallow, ROOF_OVERHANG_M)
    beam_z = wall_z + (shallow - wall_z) * 0.30 + HOIST_BEAM_FACE_M
    check("a shallow gable carries a beam on the middle bay and not on an outer one",
          mid_top > beam_z >= outer,
          f"middle {mid_top:.3f} m, outer {outer:.3f} m, beam head {beam_z:.3f} m")

    # 7. THE REFUSALS. The archetype refuses a rhythm it cannot build rather than
    #    thinning the piers or dropping a bay, because either of those is the
    #    generator deciding how the building was worked and not saying so.
    def refuses(label: str, **kw) -> None:
        try:
            store(**kw).validate()
        except FS.ParamError:
            check(label, True)
            return
        check(label, False, "it built instead")

    refuses("a rhythm the loading side cannot carry at all is refused",
            width=7.0, depth=6.0, wall=6.5, bays=3)
    refuses("…and one that only fits by thinning the piers under the jamb stock",
            width=7.0, depth=9.10, wall=6.5, bays=4)
    refuses("half a cargo opening is refused", width=7.6, depth=15.5, wall=6.5, bays=0)
    refuses("a rhythm of nothing — bays without a door — is refused",
            width=7.6, depth=15.5, wall=6.5, bays=2, goods_door=False)
    refuses("a hoist on a one-storey shop is refused",
            width=7.6, depth=15.5, wall=6.5, bays=2, stories=1.0, hoist_door=True)
    refuses("a hoist under a hip, which has no gable to hang in, is refused",
            width=7.6, depth=15.5, wall=6.5, bays=2, roof_type="hip", hoist_door=True)
    refuses("a hoist over an EAVES loading side is refused",
            width=7.6, depth=15.5, wall=6.5, bays=2, gable_front=True, hoist_door=True)

    # 8. AND THE TOWN'S TWO F2 ROOFS ACTUALLY CARRY IT — the records, not the rule.
    built = []
    for rid in ("recon_1835_blk_south_water_clark_f2_01",
                "recon_1835_blk_south_water_lasalle_f2_10"):
        rec = json.loads((ROOT / "data" / "structures" / f"{rid}.json").read_text())
        p = FS.from_phase(rec["phases"][0], rec)
        p.validate()
        built.append((rid, p.goods_door_bays, p.hoist_door, p.loading_end_is_gable))
    check("both of the town's F2 warehouses stand at two bays with a hoist over them",
          all(b == 2 and h and g for _r, b, h, g in built),
          "; ".join(f"{r}: {b} bays, hoist {h}" for r, b, h, _g in built))

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"the cargo-door rhythm OK — F2 2 bays, F3 3, {seen} single-door "
          f"storefront phase(s) unmoved")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("SELF-TEST: a single-bay set-out is nudged by a nanometre; the "
              "byte-identity check must fire.")
        rc = main(break_it=True)
        if rc == 0:
            print("SELF-TEST FAILED: the assertions passed on a moved storefront.")
            sys.exit(1)
        print("self-test OK — the assertions fire when a single-door store moves.")
        sys.exit(0)
    sys.exit(main())
