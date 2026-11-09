#!/usr/bin/env python3
"""Write the T-3499 camp grounds: lodges for the whole August 1812 gathering, and a camp for
Wells's Miami escort.

    python3 docs/RESEARCH/gathering-camp-1812-3499/write_records.py           write the records
    python3 docs/RESEARCH/gathering-camp-1812-3499/write_records.py --check   say if they are current

WHY. The owner, 2026-11-08 (thread "Reconstruct 1812 Chicago's full population"), after the
population spike: card every missing person of the gathering, draw about one in five, and
"the remainder would be in buildings and I can ask them to come out and meet them". Helm's
narrative (Quaife 1913, Appendix VI) counts the gathering on 12 August 1812: "the tribes there
assembled to amount of 500 warriors 179 women & children", and has Wells arrive "with 27
Miamis". T-3342's six grounds on the State Street creek hold 27 dwellings, and the Miamis
had no camp at all. So people need roofs.

THE OCCUPANCY RULE, stated once and reconstructed (L-1812-gathering-lodges-3499): a mat lodge or
a bark-roofed lodge sleeps 8, a long lodge 20, a bark house 14. The six T-3342 grounds sleep
270 by it; these seven sleep 440 more, 710 in all, room for Helm's 679. The Miami camp sleeps
36, room for Wells's 27.

THE SPLIT, reconstructed. Helm counts 179 women and children against 500 warriors: about 45
families at a man, a woman or two and their children, so most of the men came without
families, as the bands of a war-time gathering would. Three of the new grounds are drawn as
family grounds (the gear of a camp of families: racks, hide frames, mortars), four as men's
grounds (lodges, hearths, firewood and horse pickets, and little of the rest).

THE PLACES, chosen by this project on the committed ground and not by any source: each
rectangle is level on the e1830_natural heightfield (its spread stated in the record), stands
on ground at least 0.6 m with every point 6 m out of it also above 0.6 m (so off the creek's
cut), 10 m from the other camp grounds, 15 m from every other 1812 footprint, 6 m from every
worn trail, and the Miami camp 4 m clear of the T-3497 wagon roads. The search that found
them is docs/RESEARCH/gathering-camp-1812-3499/sites.py (run from chicago/4d).
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

ORIGIN_E, ORIGIN_N = 447072.7, 4637395.8   # data/datum.json origin_utm_e / _n
TEMPLATE = DATA / "structures" / "potawatomi_camp_1812_middle.json"
LIB = "L-1812-gathering-lodges-3499"
OCCUPANCY = {"mat_lodges": 8, "bark_roofed_lodges": 8, "long_lodges": 20, "bark_houses": 14}
HELM = ("Helm's narrative (Quaife 1913, Appendix VI): 'Capt. William Wells arrived from Fort "
        "Wayne on the 12th August with 27 Miamis and after a council being held by him with "
        "the tribes there assembled to amount of 500 warriors 179 women & children'")

COUNT_KEYS = ("mat_lodges", "long_lodges", "bark_roofed_lodges", "bark_houses", "arbors",
              "hearths", "drying_racks", "scaffolds", "hide_frames", "woodpiles", "mortars",
              "canoes", "horse_pickets", "pack_saddles")

#   id suffix, kind, (E, N) south-west corner, (length, depth), label, where, counts,
#   mat condition
GROUNDS = [
    ("south_west", "family", (676, -288), (36, 28), "the family lodges south of the reach",
     "On the level prairie south of the south-reach group, west of the south prairie group",
     dict(mat_lodges=4, bark_roofed_lodges=1, long_lodges=1, bark_houses=1, arbors=1,
          hearths=2, drying_racks=2, scaffolds=1, hide_frames=1, woodpiles=1, mortars=1),
     "mixed"),
    ("north_flat", "men", (696, -100), (36, 28), "the men's lodges on the flat above the mouth",
     "On the flat between the mouth group and the horse ground",
     dict(mat_lodges=5, long_lodges=1, hearths=3, woodpiles=2, scaffolds=1,
          horse_pickets=6, pack_saddles=3),
     "weathered"),
    ("south_bend", "family", (736, -232), (36, 28), "the family lodges below the bend",
     "On the level ground south of the middle group, east of the south reach",
     dict(mat_lodges=4, bark_roofed_lodges=1, long_lodges=1, arbors=1, hearths=2,
          drying_racks=2, scaffolds=1, hide_frames=1, woodpiles=1, mortars=1),
     "new"),
    ("head_west", "men", (616, -172), (36, 28), "the men's lodges by the creek's head",
     "West of the creek's upper reach, north of the upper group",
     dict(mat_lodges=5, long_lodges=1, hearths=3, woodpiles=2, scaffolds=1,
          horse_pickets=4, pack_saddles=2),
     "weathered"),
    ("prairie_west", "men", (568, -172), (36, 28), "the men's lodges on the west prairie",
     "On the prairie west of the creek's head, west of the head group",
     dict(mat_lodges=5, long_lodges=1, hearths=3, woodpiles=2, scaffolds=1,
          horse_pickets=6, pack_saddles=3),
     "mixed"),
    ("far_west", "men", (576, -132), (36, 28), "the men's lodges furthest west",
     "The westernmost ground, on the prairie's edge west of the creek",
     dict(mat_lodges=4, bark_roofed_lodges=1, long_lodges=1, hearths=3, woodpiles=2,
          scaffolds=1, horse_pickets=4, pack_saddles=2),
     "weathered"),
    ("south_prairie", "family", (736, -272), (36, 28), "the family lodges on the south prairie",
     "The southernmost ground, south of the bend group",
     dict(mat_lodges=4, bark_houses=1, long_lodges=1, arbors=1, hearths=2, drying_racks=2,
          scaffolds=1, hide_frames=1, woodpiles=1, mortars=1),
     "mixed"),
]

MIAMI = ("miami_escort_camp_1812", (1060, 56), (30, 24),
         dict(mat_lodges=2, long_lodges=1, hearths=2, woodpiles=1, scaffolds=1,
              horse_pickets=10, pack_saddles=4),
         "weathered")


# The grounds that lap a street of the 1830 plat (tools/measure_corridor_intrusion.py), and the
# street: each is refused in writing, here and in tools/corridor_intrusion_baseline.json.
LAPS = {"north_flat": "Dearborn", "prairie_west": "Clark", "far_west": "Lake",
        "south_prairie": "Randolph", "south_west": "Dearborn"}


def refusal(suffix: str) -> str:
    street = LAPS.get(suffix)
    if not street:
        return ""
    return (f" THE PLATTED STREET IS REFUSED IN WRITING (T-3499): the ground laps the corridor of "
            f"{street} Street, which Thompson's plat of 4 August 1830 (thompson_plat_1830) laid out "
            "eighteen years after this camp's one phase, so the camp and the street never stand in "
            "one scene; tools/corridor_intrusion_baseline.json carries the refusal, as it does "
            "T-3342's horse ground and the first fort's cornfield and wharf.")


def sleeps(c: dict) -> int:
    return sum(OCCUPANCY[k] * c.get(k, 0) for k in OCCUPANCY)


def spread(e0, n0, L, D):
    from heightfield import Heightfield
    hf = Heightfield.load(DATA / "terrain" / "epochs" / "e1830_natural")
    hs = [hf.height(e0 + u, n0 + v) for u in range(0, L + 1, 2) for v in range(0, D + 1, 2)]
    h0 = hf.height(e0, n0)
    return round(min(hs) - h0, 2), round(max(hs) - h0, 2), round(h0, 2)


def form(counts: dict, cond: str, kind_note: str) -> dict:
    out = {}
    for k in COUNT_KEYS:
        v = counts.get(k, 0)
        note = (f"{v} in this group" if v else "None in this group") + f". {kind_note} {LIB}."
        if k in OCCUPANCY and v:
            note = f"{v} in this group, sleeping {OCCUPANCY[k]} each by this project's rule. {kind_note} {LIB}."
        out[k] = {"value": v, "confidence": "reconstructed", "note": note}
    out["canoe_edge"] = {"value": "none", "confidence": "reconstructed",
                         "note": f"No canoes in this group. {LIB}."}
    out["mat_condition"] = {"value": cond, "confidence": "reconstructed",
                            "note": f"The mats' condition; which group has which is this project's. {LIB}."}
    return out


def build_potawatomi(t: dict, g) -> dict:
    suffix, kind, (e0, n0), (L, D), label, where, counts, cond = g
    rid = f"potawatomi_camp_1812_{suffix}"
    lo, hi, h0 = spread(e0, n0, L, D)
    r = copy.deepcopy(t)
    r["id"] = rid
    r["name"] = f"The Potawatomi camp of August 1812: {label}"
    kind_note = ("A family ground: the gear of a camp of families." if kind == "family" else
                 "A men's ground: most of Helm's 500 warriors came without families.")
    r["occupants"] = {
        "value": (f"Sleeps {sleeps(counts)} by this project's occupancy rule (a mat or bark-roofed "
                  "lodge 8, a long lodge 20, a bark house 14). Who sleeps here is the gathering's "
                  "households' to say (T-3500); no lodge is given to a named family or band by "
                  "any source."),
        "confidence": "reconstructed",
        "note": f"Helm counts the gathering, not its lodges: {HELM}. {LIB}.",
    }
    ph = r["phases"][0]
    loc = f"local E +{e0}..+{e0 + L}, N {n0}..{n0 + D}"
    ph["position"]["utm_e"] = round(ORIGIN_E + e0, 1)
    ph["position"]["utm_n"] = round(ORIGIN_N + n0, 1)
    ph["position"]["symbolic_location"] = f"{where}: {loc}."
    ph["position"]["confidence"] = "reconstructed"
    ph["position"]["note"] = (
        "THE CAMP'S PLACE IS THE SOURCES', THIS GROUND IS OURS (T-3499). Currey puts the "
        "gathering's lodges 'clustered along the creek' at the later State Street on 14 August "
        "(1912 ch. III) and Wau-Bun the encampment on the river's south bank with a stream beside "
        "it (ch. XIX); T-3342's six grounds stand there. Helm's count of 679 people needs more "
        f"roofs than those six give, so this ground is added to the cluster. {where}: {loc}. "
        "Chosen by a search on the committed e1830_natural heightfield "
        "(docs/RESEARCH/gathering-camp-1812-3499/sites.py): its outline lies "
        f"between {lo:+.2f} and {hi:+.2f} m of the origin's {h0:.2f} m, every point 6 m outside it "
        "stands above 0.6 m (off the creek's cut), and it keeps 10 m from the other camp grounds, "
        "15 m from every other 1812 footprint, 6 m from every worn trail and 4 m from the 1835 inferred households' footprints. The point recorded "
        f"is the ground's south-west corner, the footprint's origin at rotation 0. {LIB}."
        + refusal(suffix))
    ph["footprint"] = {"polygon": [[0, 0], [float(L), 0], [float(L), float(D)], [0, float(D)]],
                       "confidence": "reconstructed",
                       "note": (f"The group's ground, {L:.1f} x {D:.1f} m, inside which the archetype "
                                f"lays its lodges, yards and gear out. INVENTED in its extent. {LIB}.")}
    ph["form"] = form(counts, cond, kind_note)
    ph["change_note"] = (f"A ground of the Potawatomi camp of the August 1812 gathering on the "
                         f"State Street creek: {label}. Added by T-3499 so the camp roofs Helm's "
                         "count of the gathering; flagged for review.")
    r["research_note"] = (
        t["research_note"].split(" WHAT IS DRAWN")[0]
        + " WHAT IS DRAWN (T-3499, beside T-3342's six grounds and in the same archetype): "
        + ("a family ground of mat lodges, a long lodge and their yards, racks, hide frame and mortar. "
           if kind == "family" else
           "a men's ground of mat lodges and a long lodge, hearths, firewood and horse pickets, "
           "with little of a family camp's women's work, since most of the warriors Helm counts "
           "came without families. ")
        + f"WHY IT IS HERE: {HELM}. The six T-3342 grounds sleep 270 at this project's occupancy "
        "rule and the gathering was 679, so seven grounds are added, sleeping 440. NOTHING IS "
        "STAGED, as in the six: no ceremony, council, dialogue or sacred lodge, and no lodge is "
        "given to a family, band or person by any source. WHAT WOULD REPLACE THIS: a source that "
        "counts or maps the lodges of August 1812, or places the camp more exactly. " + LIB + ".")
    return r


def build_miami(t: dict) -> dict:
    rid, (e0, n0), (L, D), counts, cond = MIAMI
    lo, hi, h0 = spread(e0, n0, L, D)
    r = copy.deepcopy(t)
    r["id"] = rid
    r["name"] = "The Miami escort's camp, August 1812"
    r["aka"] = ["Wells's Miamis", "the Miami escort"]
    r["function"] = {
        "value": "gathering_camp", "confidence": "inferred", "sources": ["quaife_1913", "currey_1912_old_fort_dearborn"],
        "note": (f"{HELM}. Wells came from Fort Wayne to bring the garrison out, and his Miamis "
                 "marched with the column on the 15th, part in the lead and the rest behind "
                 "(Quaife 1913 ch. X). Where they camped for the two or three nights before is "
                 "in no source read; that they stood somewhere near the fort is inferred."),
    }
    r["occupants"] = {
        "value": (f"Sleeps {sleeps(counts)} by this project's occupancy rule; Helm's 27 Miamis "
                  "(the escort's households are T-3500's)."),
        "confidence": "reconstructed", "note": f"{HELM}. {LIB}.",
    }
    ph = r["phases"][0]
    ph["documented_range"] = {
        "from": "1812-08-12", "to": "1812-08-15", "confidence": "inferred",
        "sources": ["quaife_1913"],
        "note": ("Wells arrived on the 12th (Helm), the 13th (Heald) or the 14th (Wau-Bun); the "
                 "camp opens on Helm's date, the earliest, and closes on the 15th, when the "
                 "Miamis marched out with the column (Quaife 1913 ch. X). L-1812-gathering-lodges-3499."),
    }
    loc = f"local E +{e0}..+{e0 + L}, N +{n0}..+{n0 + D}"
    ph["position"]["utm_e"] = round(ORIGIN_E + e0, 1)
    ph["position"]["utm_n"] = round(ORIGIN_N + n0, 1)
    ph["position"]["symbolic_location"] = f"On the prairie about 175 m south-west of the fort: {loc}."
    ph["position"]["confidence"] = "reconstructed"
    ph["position"]["sources"] = ["quaife_1913"]
    ph["position"]["note"] = (
        "NO SOURCE PLACES THE MIAMIS' CAMP; THIS GROUND IS OURS (T-3499). Heald, Helm and Currey say "
        "only that Wells came from Fort Wayne with about thirty Miamis 'mounted on ponies' (Currey "
        "1912) and that they marched out on the 15th, part before the column and part behind it "
        "(Heald's report, Quaife 1913 Appendix IV). Mounted men come to march the garrison out "
        "would camp by the fort, by its stables and the road south they would take, and apart "
        "from the Potawatomi gathering on the creek; so the ground stands on the level prairie "
        "about 40 m south of the fort's three stables and 175 m south-west of the outer pickets "
        f"(the owner, 2026-11-08: build the camps 'where they would most logically have been'): {loc}. Its outline lies between {lo:+.2f} and {hi:+.2f} m of the "
        f"origin's {h0:.2f} m on the e1830_natural heightfield; it keeps 15 m from every 1812 "
        "footprint, 6 m from every worn trail and 4 m from the wagon roads of T-3497 (the fort's "
        "south loop and the shore road). The point recorded is the ground's south-west corner. "
        f"{LIB}.")
    ph["footprint"] = {"polygon": [[0, 0], [float(L), 0], [float(L), float(D)], [0, float(D)]],
                       "confidence": "reconstructed",
                       "note": f"The escort's ground, {L:.1f} x {D:.1f} m. INVENTED in its extent. {LIB}."}
    ph["form"] = form(counts, cond, "A travelling camp of mounted men: lodges of carried mats, "
                                    "hearths and the horse lines.")
    ph["change_note"] = ("The camp of the Miami escort Wells brought from Fort Wayne, 12-15 August "
                         "1812. Added by T-3499; flagged for review.")
    r["research_note"] = (
        "THIS RECORD IS FLAGGED review_required, AND touches_removal, because it draws the camp of "
        "Native men at Chicago on the eve of 15 August 1812 from accounts written by the garrison's "
        "side; the Miamis, like the Potawatomi, were later removed from their lands. The owner's "
        "rulings of 2026-10-16 (AGENTS.md § Standing constraint) trust this project to draw Native "
        "depictions on fair and reasonable judgement; the flags stay, and say why here. WHAT IS "
        "DRAWN: a small travelling camp in the lodge_camp archetype: two mat lodges and a long lodge "
        "of carried mats, two hearths, firewood, a scaffold for saddles and loads, and ten tether "
        "stakes for the horses (the Miamis were mounted: Currey 1912, of the battle, 'the mounted Miamis'). "
        "The Miamis' own lodge forms are not described at Chicago; the Potawatomi camp's are used "
        "as the nearest. NOTHING IS STAGED. WHAT WOULD REPLACE THIS: a source that places or "
        f"describes the escort's camp. {LIB}.")
    return r


def records() -> dict:
    t = json.loads(TEMPLATE.read_text())
    out = {}
    for g in GROUNDS:
        r = build_potawatomi(t, g)
        out[r["id"]] = r
    r = build_miami(t)
    out[r["id"]] = r
    return out


def dump(r: dict) -> str:
    return json.dumps(r, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    total = 0
    for rid, r in records().items():
        p = DATA / "structures" / f"{rid}.json"
        s = dump(r)
        total += sleeps({k: v["value"] for k, v in r["phases"][0]["form"].items()
                         if k in OCCUPANCY})
        if args.check:
            if not p.exists() or p.read_text() != s:
                print(f"stale: {p.relative_to(ROOT)}")
                bad += 1
        else:
            p.write_text(s)
            print(f"wrote {p.relative_to(ROOT)}")
    print(f"the new grounds sleep {total} (Miami camp included)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
