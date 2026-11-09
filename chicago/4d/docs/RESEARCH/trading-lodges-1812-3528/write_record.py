#!/usr/bin/env python3
"""Write T-3528's ground: the Potawatomi lodges that stand by the river all 1812, not only
in the August gathering.

    python3 docs/RESEARCH/trading-lodges-1812-3528/write_record.py           write the record
    python3 docs/RESEARCH/trading-lodges-1812-3528/write_record.py --check   say if it is current

WHY. The owner, 2026-11-09, chose "Camps follow the date" for the 1812 camps (T-3527): the
gathering's lodges stand only 12-16 August, and "the rest of the year that ground is open
prairie with two or three trading lodges at the river mouth". Currey writes of the years
before the war that the Potawatomi "continued to come and go on their nomadic excursions
according to their habit, and while in this vicinity they lived in their wigwams near the
river, their favorite camping place being at a point on the south bank near the present State
Street bridge", and that the traders were "anxious to sell them supplies in exchange for the
furs brought in by them" (1912 ch. II). So families came and went all year to trade; which
lodges stood on a given day no source says. This ground stands for that coming and going: a
small camp of one or two families, drawn every day of 1812.

THE PLACE, chosen by this project: the creek's mouth itself is the August landing group's
(potawatomi_camp_1812_mouth), so this ground stands on the same south bank a little west of
it, between the river and the gathering's north-flat group. It is the nearest 26 x 18 m (the least in which the archetype lays every piece)
rectangle to the mouth group that is level on the e1830_natural heightfield (spread at most
0.2 m), at least 0.6 m with every point 6 m out of it above 0.6 m (off the creek's and river's
cut), 10 m from the camp grounds, 15 m from every other 1812 footprint, 6 m from every worn
trail (the August camp paths too, so the two never cross) and 4 m from the 1835 inferred
households: docs/RESEARCH/trading-lodges-1812-3528/sites.py. L-1812-trading-lodges-3528.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

ORIGIN_E, ORIGIN_N = 447072.7, 4637395.8   # data/datum.json origin_utm_e / _n
TEMPLATE = DATA / "structures" / "potawatomi_camp_1812_mouth.json"
RID = "potawatomi_trading_lodges_1812"
LIB = "L-1812-trading-lodges-3528"
SW = (698, -34)
SIZE = (26, 18)
COUNTS = dict(mat_lodges=2, bark_houses=1, hearths=2, drying_racks=1, scaffolds=1,
              hide_frames=1, woodpiles=1, mortars=1, canoes=2)
COUNT_KEYS = ("mat_lodges", "long_lodges", "bark_roofed_lodges", "bark_houses", "arbors",
              "hearths", "drying_racks", "scaffolds", "hide_frames", "woodpiles", "mortars",
              "canoes", "horse_pickets", "pack_saddles")
CURREY_LOC = "ch. II, Gutenberg #52346 plain text lines 1360-1369"
CURREY = ("'The Indians continued to come and go on their nomadic excursions according to their "
          "habit, and while in this vicinity they lived in their wigwams near the river, their "
          "favorite camping place being at a point on the south bank near the present State "
          "Street bridge. A swale or gully opened into the river there, reaching back as far as "
          "the present line of Randolph Street. The movements of the Indians were regarded with "
          "great interest by the traders located in the neighborhood, who were anxious to sell "
          "them supplies in exchange for the furs brought in by them'")


def spread(e0, n0, L, D):
    from heightfield import Heightfield
    hf = Heightfield.load(DATA / "terrain" / "epochs" / "e1830_natural")
    hs = [hf.height(e0 + u, n0 + v) for u in range(0, L + 1, 2) for v in range(0, D + 1, 2)]
    h0 = hf.height(e0, n0)
    return round(min(hs) - h0, 2), round(max(hs) - h0, 2), round(h0, 2)


NOTES = {
    "mat_lodges": "Two mat lodges: the winter house of Forsyth's account, and what a travelling family carried.",
    "bark_houses": "One elm-bark house: the summer house of Forsyth's account, for a family that came back each year to the same ground.",
    "hearths": "Two fires, one a household.",
    "canoes": "Two canoes drawn up on the river side: the families came and went by water with their furs.",
}


def form() -> dict:
    out = {}
    for k in COUNT_KEYS:
        v = COUNTS.get(k, 0)
        lead = NOTES.get(k) or ((f"{v} in this group." if v else "None in this group."))
        out[k] = {"value": v, "confidence": "reconstructed", "note": f"{lead} {LIB}."}
    out["canoe_edge"] = {"value": "north", "confidence": "reconstructed",
                         "note": f"The side the canoes are drawn up on, towards the river. {LIB}."}
    out["mat_condition"] = {"value": "weathered", "confidence": "reconstructed",
                            "note": f"Mats greyed by seasons of carrying and rain: these families' lodges were their own all year. {LIB}."}
    return out


def build() -> dict:
    t = json.loads(TEMPLATE.read_text())
    (e0, n0), (L, D) = SW, SIZE
    lo, hi, h0 = spread(e0, n0, L, D)
    r = copy.deepcopy(t)
    r["id"] = RID
    r["name"] = "The Potawatomi lodges by the river, 1812"
    r["aka"] = ["the trading lodges", "the Indian wigwams near the river (Currey)"]
    r["function"] = {
        "value": "trading_camp", "confidence": "inferred",
        "sources": ["currey_1912_old_fort_dearborn"],
        "note": (f"Currey 1912 {CURREY_LOC}: {CURREY}. That families came and went to trade all "
                 "year, and camped by the river near the creek's mouth while here, is Currey's; "
                 "that some lodges stood there on any day is inferred from it."),
    }
    r["occupants"] = {
        "value": ("A family or two of the Potawatomi come in to trade, whom no source names or "
                  "counts; no household is minted for them yet."),
        "confidence": "reconstructed",
        "note": f"Currey says families came and went; who, and how many, no source read says. {LIB}.",
    }
    ph = r["phases"][0]
    ph["id"] = "camp_1812"
    ph["documented_range"] = {
        "from": "1812-01-01", "to": "1812-12-31", "confidence": "inferred",
        "sources": ["currey_1912_old_fort_dearborn"],
        "note": (f"THE RANGE IS THE SCENE'S YEAR, NOT A DATE FOR THESE LODGES. Currey ({CURREY_LOC}) "
                 "describes the Potawatomi coming and going to camp by the river in the years "
                 "before the war, with no date for any lodge; the record stands for that habit, "
                 "so it is drawn every day of 1812, whatever date the Season or a jaunt sets, beside "
                 "the gathering's camps in August. Its bounds are this project's. Nothing of 1835 "
                 f"can draw it. {LIB}."),
    }
    loc = f"local E +{e0}..+{e0 + L}, N {n0}..{n0 + D}"
    ph["position"] = {
        "utm_e": round(ORIGIN_E + e0, 1), "utm_n": round(ORIGIN_N + n0, 1), "rotation_deg": 0.0,
        "symbolic_location": f"On the river's south bank a little west of the creek's mouth: {loc}.",
        "confidence": "reconstructed",
        "sources": ["currey_1912_old_fort_dearborn"],
        "note": (
            "THE PLACE IS CURREY'S, THIS GROUND IS OURS (T-3528). Currey puts the Potawatomi's "
            "favourite camping place 'on the south bank near the present State Street bridge', "
            f"where the creek opened into the river ({CURREY_LOC}). The creek's mouth itself is "
            "the August gathering's landing group (potawatomi_camp_1812_mouth), so this ground "
            f"stands on the same bank a little west of it, between the river and the north-flat group: {loc}. "
            "Chosen by a search on the committed e1830_natural heightfield "
            "(docs/RESEARCH/trading-lodges-1812-3528/sites.py): its outline lies between "
            f"{lo:+.2f} and {hi:+.2f} m of the origin's {h0:.2f} m, every point 6 m outside it "
            "stands above 0.6 m (off the cut of the river and the creek), and it keeps 10 m from "
            "the camp grounds, 15 m from every other 1812 footprint, 6 m from every worn trail and "
            "4 m from the 1835 inferred households' footprints. The point recorded is the "
            f"ground's south-west corner, the footprint's origin at rotation 0. {LIB}. "
            "THE PLATTED STREET IS REFUSED IN WRITING (T-3528): the ground laps the corridor of "
            "Dearborn Street, which Thompson's plat of 4 August 1830 (thompson_plat_1830) laid out "
            "eighteen years after this camp's one phase, so the camp and the street never stand in "
            "one scene; tools/corridor_intrusion_baseline.json carries the refusal, as it does "
            "T-3499's north-flat ground and T-3342's horse ground."),
        "derivation": {
            "method": "not_derivable",
            "reason": ("A ground chosen by a search over the e1830_natural heightfield and the "
                       "committed 1812 footprints and trails, not a street line or a traced "
                       "waterline validate.py can re-derive a coordinate from; the search is "
                       "docs/RESEARCH/trading-lodges-1812-3528/sites.py."),
        },
    }
    ph["footprint"] = {"polygon": [[0, 0], [float(L), 0], [float(L), float(D)], [0, float(D)]],
                       "confidence": "reconstructed",
                       "note": (f"The ground, {L:.1f} x {D:.1f} m, inside which the archetype lays "
                                f"its lodges, yard and gear out. INVENTED in its extent. {LIB}.")}
    ph["form"] = form()
    ph["change_note"] = ("A small camp of Potawatomi families come in to trade, on the river's "
                         "south bank by the creek's mouth, standing all 1812. Added by T-3528; "
                         "flagged for review.")
    r["research_note"] = (
        "THIS RECORD IS FLAGGED review_required, AND touches_removal, because it draws a camp of "
        "the Potawatomi at Chicago in 1812, the people whose land this was and who were removed "
        "from it in 1835, from a settler historian's account. The owner's rulings of 2026-10-16 "
        "(AGENTS.md § Standing constraint) trust this project to draw Native depictions on fair "
        "and reasonable judgement; the flags stay, and say why here. WHAT IS DRAWN: a small camp "
        "in T-3342's lodge_camp archetype: two mat lodges and an elm-bark house, two fires, a "
        "drying rack, a scaffold, a hide frame, firewood, a mortar and two canoes drawn up on the "
        f"river side. WHY IT IS HERE: Currey ({CURREY_LOC}): {CURREY}. The owner chose on "
        "2026-11-09 that the August gathering's camps stand only on its days (T-3527), with a few "
        "lodges by the river the rest of the year. NOTHING IS STAGED: no ceremony or trade is "
        "drawn, and no lodge is given to a family, band or person by any source. WHAT WOULD "
        "REPLACE THIS: a source that dates, counts or places the lodges by the river in a given "
        f"season. {LIB}.")
    r["review_required"] = True
    r["touches_removal"] = True
    return r


def dump(r: dict) -> str:
    return json.dumps(r, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    p = DATA / "structures" / f"{RID}.json"
    s = dump(build())
    if args.check:
        if not p.exists() or p.read_text() != s:
            print(f"stale: {p.relative_to(ROOT)}")
            return 1
        print(f"current: {p.relative_to(ROOT)}")
        return 0
    p.write_text(s)
    print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
