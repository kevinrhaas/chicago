#!/usr/bin/env python3
"""The crosswalk's store-family variants, held to the entries that author them.
(T-1659)

WHY THIS EXISTS. `data/reconstruction/1835_family_archetype_crosswalk.json` authors a
`required_variant` and a `variants` line for every family, and for the store families
three of those lines named forms `frame_storefront` could not draw. Two of the three
were not visible as refusals — they were visible as nothing at all:

* **C2, the store-residence**, authors `levels: "1.5"` and asks in writing for "a true
  knee-wall/attic-room silhouette". `from_phase` resolved the record's storeys with
  `int()`, so the EIGHT committed records that state 1.5 were built as one-storey shops.
  Nothing failed: `validate()` was satisfied, the attic simply had no light, and
  `shopfront_head_z` put the head of the shop opening ABOVE the floor of the room over
  it on all eight — a shopfront cut through a joist.
* **C4, the wide store or mixed block**, authors `roof: "side gable or hip"`. The
  archetype refused a hip outright, and `tools/roof_form.roof_kind` returned a front
  gable for every family whose id begins with C — so the one C4 record stood with its
  gable to South Water, which is neither of the two forms its own entry offers.
* **C3 and F2** author an "optional hoist door" and a "hoist beam; upper freight doors",
  and the archetype had no such form. It has one now, and the two families' correct
  states are DIFFERENT — which is why this check is per family and not a single sweep:
    - **C3, and every store family**, still carries no hoist. C3's own assumption note
      is explicit that upper lodging and hoist equipment "cannot be inferred from
      height alone", so a two-storey shop does not get one for being two storeys.
      This remains a capability nothing exercises, which is the thing a gate is for.
    - **F2 carries one on both of its roofs** since T-1663. The same entry's EVIDENCE
      note names "warehouse framing/hoist support" as what this archetype must add
      before the family is satisfied, and a two-storey warehouse whose only opening is
      a ground door cannot load the floor it exists to have. Its assumption note's
      "Hoist beam presence varies" is therefore over-claimed here on purpose, recorded
      as a liberty (docs/LIBERTIES.md L280) rather than inferred quietly. The rhythm
      the doors stand on is held by `tools/test_storefront_cargo_rhythm.py`.

    python3 tools/test_store_variants.py
    python3 tools/test_store_variants.py --self-test   # the assertions must fire
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from archetypes import frame_storefront_params as P   # noqa: E402
import roof_form                                       # noqa: E402

STRUCTURES = ROOT / "data" / "structures"
FAILED = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  ok   {label}")
    else:
        FAILED.append(label)
        print(f"  FAIL {label}{(' — ' + detail) if detail else ''}")


def refuses(label: str, **kw) -> None:
    """The archetype must refuse these parameters, with an argument."""
    base = dict(width_m=9.0, depth_m=13.0, stories=2.0, wall_height_m=6.2)
    base.update(kw)
    try:
        P.FrameStorefrontParams(**base).validate()
    except P.ParamError:
        print(f"  ok   refused: {label}")
        return
    FAILED.append(f"refused: {label}")
    print(f"  FAIL refused: {label} — it was accepted")


def builds(label: str, **kw) -> None:
    base = dict(width_m=9.0, depth_m=13.0, stories=2.0, wall_height_m=6.2)
    base.update(kw)
    try:
        P.FrameStorefrontParams(**base).validate()
    except P.ParamError as e:
        FAILED.append(f"builds: {label}")
        print(f"  FAIL builds: {label} — {e}")
        return
    print(f"  ok   builds: {label}")


def committed(family: str) -> list[tuple[str, P.FrameStorefrontParams, dict]]:
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        rec = json.loads(path.read_text())
        if rec.get("archetype") != "frame_storefront":
            continue
        if (rec.get("reconstruction") or {}).get("family") != family:
            continue
        for phase in rec.get("phases", []):
            out.append((rec["id"], P.from_phase(phase, rec), phase))
    return out


def main(break_it: bool = False) -> int:
    # ---- 1. C2: the storey count reaches the mesh -------------------------
    # `break_it` reinstates the truncation, which is the regression this file is for.
    def resolve(phase, rec):
        p = P.from_phase(phase, rec)
        if break_it:
            p.stories = int(float(p.stories))
        return p

    c2 = [(sid, resolve(ph, json.loads((STRUCTURES / f"{sid}.json").read_text())), ph)
          for sid, _, ph in committed("C2")]
    stated_half = [(sid, p) for sid, p, ph in c2
                   if float((ph["form"].get("stories") or {}).get("value", 0)) == 1.5]
    # ELEVEN SINCE T-1681 (2026-09-27), ten since T-1682 the same day, eight before the
    # pair. This number is a CENSUS of the committed tree and it moves every time the
    # programme raises or re-families a store-residence: T-1682 re-familied the Lake
    # frontage roofs of blk_lake_franklin and blk_lake_market from D5 to C2, and T-1681
    # re-familied the middle unit of blk_lake_clark's Lake party-line run the same way,
    # so three more records state the half storey than did on 2026-09-26. It is written
    # as a literal rather than derived on purpose — the count is what makes the check
    # below a statement about the whole town and not about whatever the sample happens to
    # hold — so a run that adds a C2 moves it here and says why.
    check("eleven committed C2 records state a story-and-a-half",
          len(stated_half) == 11, f"got {len(stated_half)}")
    check("...and every one of them RESOLVES at 1.5, not at 1",
          all(p.half_story for _, p in stated_half),
          ", ".join(f"{s}={p.stories}" for s, p in stated_half if not p.half_story))
    # The defect, stated as the measurement that finds it: the head of the shop opening
    # must land under the floor of the attic room over it. At one storey the archetype
    # measured the head against the whole wall, so it did not.
    over = [(s, round(p.shopfront_head_z, 3), round(p.wall_height_m - p.knee_wall_m, 3))
            for s, p in stated_half
            if p.shopfront and p.shopfront_head_z > p.wall_height_m - P.KNEE_WALL_DEFAULT_M]
    check("...and none of them cuts its shopfront through the attic floor",
          not over, f"{over}")

    # ---- 2. C2's eave band is the one a SHOPFRONT can stand in ------------
    # The band is what `tools/family_bands.eave_limits` hands a sampler, so it has to
    # be the band the archetype can carry — not merely the band a storey needs.
    lo, hi = P.wall_height_band_m(1.5)
    worst = P.FrameStorefrontParams(width_m=6.2, depth_m=10.8, stories=1.5,
                                    wall_height_m=lo)
    check("the 1.5-storey eave floor still carries a shop opening",
          worst.shopfront_head_z >= P.SHOP_HEAD_MIN_Z_M,
          f"floor {lo} gives head {worst.shopfront_head_z:.3f}")
    just_under = P.FrameStorefrontParams(width_m=6.2, depth_m=10.8, stories=1.5,
                                         wall_height_m=round(lo - 0.01, 3))
    check("...and one centimetre under it does not",
          just_under.shopfront_head_z < P.SHOP_HEAD_MIN_Z_M,
          "the published floor is not the binding one")
    check("a record with no shopfront is not held to the shopfront's floor",
          P.wall_height_band_m(1.5, shopfront=False)[0] < lo)

    # ---- 3. C4: the family's own roof line decides the gable --------------
    check("C1, C2 and C3 front their gables, as their entries say",
          all(roof_form.fronts_gable(f) for f in ("C1", "C2", "C3")))
    check("C4 does NOT — its entry offers a side gable or a hip",
          roof_form.fronts_gable("C4") is False,
          f"got {roof_form.fronts_gable('C4')}")
    check("the question is not asked of a family it is not about",
          roof_form.fronts_gable("D3") is None and roof_form.fronts_gable("F2") is None)
    c4 = committed("C4")
    check("the committed C4 record no longer fronts its gable",
          c4 and not any(p.gable_front for _, p, _ in c4),
          ", ".join(s for s, p, _ in c4 if p.gable_front))

    # ---- 4. the hip, buildable exactly where C4's entry reaches -----------
    builds("a hip over a two-storey store (C4's own levels)", roof_type="hip")
    refuses("a hip over one storey", roof_type="hip", stories=1.0, wall_height_m=3.4)
    refuses("a hip over a store-residence", roof_type="hip", stories=1.5,
            wall_height_m=3.6)

    # ---- 5. the hoist door, off by default and refused where it is a prop --
    check("no STORE record carries a hoist door — C3's note forbids inferring one "
          "from height",
          not any(p.hoist_door for f in ("C1", "C2", "C3", "C4")
                  for _, p, _ in committed(f)))
    builds("a hoist door on a two-storey gable with a goods door", hoist_door=True)
    refuses("a hoist door over one storey", hoist_door=True, stories=1.0,
            wall_height_m=3.4)
    refuses("a hoist door with no goods door", hoist_door=True, goods_door=False)
    refuses("a hoist door under a hip, which has no gable to hang it in",
            hoist_door=True, roof_type="hip")
    refuses("a hoist door whose loading side is an eaves wall — the beam has no gable",
            hoist_door=True, gable_front=True)
    builds("...and the same record with the goods door moved to the gable it has",
           hoist_door=True, gable_front=True, goods_door_side="rear")
    # F2, the narrow two-storey warehouse, is the family whose entry actually says
    # "hoist beam; upper freight doors" — and its committed records are the ones whose
    # geometry can carry one, which is the check that the capability is reachable where
    # the crosswalk puts it rather than only in the abstract.
    f2 = committed("F2")
    check("every committed F2 record could carry the hoist its entry offers",
          f2 and all(p.loading_end_is_gable for _, p, _ in f2),
          ", ".join(s for s, p, _ in f2 if not p.loading_end_is_gable))
    # …AND SINCE T-1663 EVERY ONE OF THEM DOES. This is the assertion that says the
    # family's line is satisfied by the town and not merely by the archetype: F2 was
    # the one family whose entry asks for hoist support in its evidence note, and a
    # capability reachable but never reached leaves that line only half built.
    check("…and every one of them does carry it, which is what L280 records",
          f2 and all(p.hoist_door for _, p, _ in f2),
          ", ".join(s for s, p, _ in f2 if not p.hoist_door) or "all of them")

    # ---- 6. the CONSUMED contract ----------------------------------------
    # An attribute a vertex depends on that the set does not name is a record stating
    # something the mesh does not contain — the rule frame_tavern_params sets out.
    check("knee_wall_m and hoist_door are declared consumed",
          {"knee_wall_m", "hoist_door"} <= set(P.CONSUMED))

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"store variants OK — {len(stated_half)} C2 records at 1.5 storeys, "
          f"{len(c4)} C4 record off its front gable, hip buildable and unbuilt, "
          f"hoist unbuilt on every store and built on both F2 warehouses")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("SELF-TEST: the storey count is truncated again; the C2 checks must fire.")
        rc = main(break_it=True)
        if rc == 0:
            print("SELF-TEST FAILED: the assertions passed on a truncated storey count.")
            sys.exit(1)
        print("self-test OK — the assertions fire when 1.5 storeys is read as 1.")
        sys.exit(0)
    sys.exit(main())
