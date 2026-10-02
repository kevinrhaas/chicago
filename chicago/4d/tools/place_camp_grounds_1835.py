#!/usr/bin/env python3
"""Place the camps of the two conjectural grounds: the land-sale crowd on the lake shore
south of the fort, and an emigrant wagon party at the west approach (T-1804, the second
piece of T-1214).

WHAT THIS PLACES, AND ON WHAT FOOTING. `data/reconstruction/1835_camp_grounds.json`
offers five grounds and grades one `documented` — the landing place, which
tools/place_landing_camps_1835.py (T-1803) already stands. The two placed here are
graded `conjectural` in that file, which says so of each in its own words: no committed
source puts anybody on the lake shore south of the fort or at the prairie edge west of
the town. They are built because the owner asked for them by name (T-1214: "the
land-sale crowd south of the fort, the immigrants' wagons at the west approach") and
AGENTS.md § RECONSTRUCTED IS A TIER is the rule for a thing the scene needs and nothing
states: build it at the reconstructed tier, bound it, and say so on every attribute.

AND A THIRD, FOR THE EMIGRANTS MOVED OFF THE WHARVES (T-1979, the owner's report of
2026-10-02). The American's "Some build tents upon the spot they were landed from the
boats" is read now as SOME: four tent households stay at the landing, and the other
eleven of the class are dealt by tools/reconstruct_transients_1835.py to the lake shore
south of the fort. Their camp stands here, a pocket of canvas further down the shore than
the land-sale camp, at the same conjectural tier and labelled so (L356). Unlike the two
camps below it SEATS people: the households whose own cards name the shore.

WHO SLEEPS THERE (the land-sale camp and the wagon camp): NOBODY THIS LAYER COUNTS.
1835_transient_persons.json seats none of the land-sale crowd and no overland party. The land-sale
crowd is its first refusal — 77 visitors the Public Domain register NAMES at the sale of
26-27 June 1835, reserved and left unminted because a drawn person may never stand in
for a named one. So the shore camp seats nobody and moves no count; its tents stand for
that crowd's ground, not for any of those 77 men. The wagon party is not a row of the
transient model at all (it counts the lake arrivals the papers describe), and its camp
seats nobody either. Both records say this in `occupants`.

WHAT IS NOT PLACED HERE. The Native and Métis camps T-1804 also names are not built:
T-1177's own reading (1835_native_and_metis.json § the_counted_but_unnamed) REFUSED a
bracket for the unnamed Native and Métis people at Chicago on 1 July 1835 because the
corpus holds no count, and a camp sized with no count would be the population that
refusal declined to invent, on the one subject AGENTS.md says is not a gap to fill by
inference. That is put to the owner as a question on its own ticket.

THE STREET LINE. This tool reads `data/streets/1835.json`'s DRAWN centrelines and keeps
each camp clear of the corridor each draws, because the question is whether canvas would
stand in a road a visitor sees (AGENTS.md rule 10). It does not call `corridors`,
`control_offsets`, `intrusion` or `block_edges`.

    python3 tools/place_camp_grounds_1835.py           # write the two records
    python3 tools/place_camp_grounds_1835.py --check   # re-derive; fail on drift
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

from heightfield import Heightfield  # noqa: E402
import measure_no_build_ground as nobuild  # noqa: E402
from place_landing_camps_1835 import rect_clear_of  # noqa: E402

DATA = ROOT / "data"
DATUM = DATA / "datum.json"
STREETS = DATA / "streets" / "1835.json"
ENCLOSURES = DATA / "enclosures"
SIDECARS = DATA / "sidecars" / "1835"
TRANSIENTS = DATA / "residents" / "transients"
STRUCTURES = DATA / "structures"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"

# The least a camp's edge may stand from a drawn roadway's edge, a fence run or a
# committed footprint; the most its ground may fall across its outline (well inside the
# walker's 0.35 m ground-contact tolerance, so the camp reads as pitched on the level);
# the least height above the water plane any sampled point may have.
CLEARANCE_M = 3.0
LEVEL_M = 0.25
DRY_M = 0.50
# The Fort Cemetery's own record keeps a 30 m skirt clear of every committed record
# (1835_no_build_ground.json, fort_cemetery); a camp keeps it too.
CEMETERY_SKIRT_M = 30.0
# Streets the layer carries without a width are drawn at the platted 80 ft.
DEFAULT_CORRIDOR_M = 24.384

CAMPS = (
    {
        "id": "land_sale_camp_shore",
        "name": "The land-sale camp on the lake shore south of the fort",
        "aka": ["the tents on the reservation shore"],
        "ground": "the_lake_shore_south_of_the_fort",
        "on_reservation": True,
        # E and N of the camp's ground, local ENU metres. The origin is the south-west
        # corner and the camp opens north, towards the fort (rotation 0).
        "e": (1130.0, 1180.0), "n": (-40.0, 0.0),
        "tents": 12, "tent_kind": "mixed", "wagons": 3, "brush_shelters": 1,
        "fire_rings": 6, "woodpiles": 3, "baggage_heaps": 4,
        "arrangement": "scatter", "canvas_condition": "weathered",
        "function": "land_sale_camp",
        "range": ("1835-06-15", "1835-07-31"),
        "range_sources": ["isa_public_domain_land_tract_sales"],
        "range_note": "THE SALE, NOT THE CAMP. The Public Domain register enters 232 "
                      "purchases at Chicago on 26-27 June 1835; the range opens a "
                      "fortnight before the sale, when the crowd it drew was arriving, "
                      "and closes a month after it, by when the buyers had gone to see "
                      "their land. No source dates any tent here, or says there was "
                      "one. What the range says is that on 1 July 1835, four days after "
                      "the sale, canvas stood here. T-1804.",
    },
    {
        "id": "emigrant_camp_shore",
        "name": "The emigrants' tents on the lake shore",
        "aka": ["the tents further down the shore"],
        "ground": "the_lake_shore_south_of_the_fort",
        "on_reservation": True,
        "seats": True,
        # A pocket south and east of the land-sale camp, the cemetery's skirt between
        # them and the town: the nearest open ground off the wharf frontage.
        "e": (1170.0, 1212.0), "n": (-140.0, -108.0),
        "tents": 11, "tent_kind": "mixed", "wagons": 2, "brush_shelters": 1,
        "fire_rings": 6, "woodpiles": 3, "baggage_heaps": 0,
        "arrangement": "scatter", "canvas_condition": "weathered",
        "function": "emigrant_camp",
        "range": ("1835-06-01", "1835-09-30"),
        "range_sources": ["chicago_american_1835"],
        "range_note": "THE SEASON, NOT THE CAMP. The American of 13 June 1835 has the "
                      "emigrants' tents already standing at the landing; the range runs "
                      "the navigation summer they came in on. No source dates a tent on "
                      "this shore or says there was one. What the range says is that on "
                      "1 July 1835 canvas stood here. T-1979.",
    },
    {
        "id": "west_approach_wagon_camp",
        "name": "The emigrants' wagon camp at the west approach",
        "aka": ["the wagons beyond the Des Plaines Street line"],
        "ground": "the_prairie_edge_west_of_the_canal_street_approach",
        "on_reservation": False,
        "e": (-700.0, -666.0), "n": (-236.0, -202.0),
        "tents": 2, "tent_kind": "wedge", "wagons": 4, "brush_shelters": 0,
        "fire_rings": 2, "woodpiles": 1, "baggage_heaps": 2,
        "arrangement": "ring", "canvas_condition": "patched",
        "function": "emigrant_camp",
        "range": ("1835-06-01", "1835-09-30"),
        "range_sources": ["chicago_american_1835"],
        "range_note": "THE SEASON, NOT THE CAMP. The American of 13 June 1835 has the "
                      "summer's emigrants already arriving; the range runs the "
                      "emigrating summer. No source dates a wagon camp at the west "
                      "approach or says there was one, and a party stopping a night or "
                      "two before going on west was gone before anybody could write it "
                      "down. What the range says is that on 1 July 1835 a party stood "
                      "here. T-1804.",
    },
)


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def seated(ground: str) -> list:
    """(slot, household id, name, persons) for the tent households whose own cards name
    `ground` (tools/reconstruct_transients_1835.py deals them)."""
    out = []
    for f in sorted(TRANSIENTS.glob("*.json")):
        d = load(f)
        t = d.get("transient") or {}
        if t.get("household_kind") != "camp":
            continue
        if ground not in {r.get("place_id") for r in d.get("lodged_at") or []}:
            continue
        out.append((t["slot"], d["id"], d["name"], len(d.get("persons") or [])))
    return sorted(out)


def grounds() -> dict:
    g = load(DATA / "reconstruction" / "1835_camp_grounds.json")
    return {c["id"]: c for c in g["candidates"]}


def roadways() -> list:
    """(id, centreline, half width) for every drawn street."""
    out = []
    for st in load(STREETS)["streets"]:
        path = st.get("path_local_enu_m") or []
        if len(path) >= 2:
            w = st.get("corridor_width_m") or DEFAULT_CORRIDOR_M
            out.append((st["id"], [tuple(p) for p in path], float(w) / 2.0))
    return out


def fences() -> list:
    out = []
    for f in sorted(ENCLOSURES.glob("*.json")):
        if f.name == "index.json":
            continue
        for run in load(f).get("runs") or []:
            path = run.get("path_local_enu_m") or []
            if len(path) >= 2:
                out.append([tuple(p) for p in path])
    return out


def footprints() -> list:
    out = []
    for f in sorted(SIDECARS.glob("*.json")):
        sc = load(f)
        if sc.get("archetype") == "camp" or sc.get("id", f.stem) in {c["id"] for c in CAMPS}:
            continue
        pl, fp = sc.get("placement") or {}, (sc.get("footprint") or {}).get("polygon")
        if not fp or pl.get("local_e") is None:
            continue
        th = math.radians(float(pl.get("rotation_deg") or 0.0))
        c, s = math.cos(th), math.sin(th)
        e0, n0 = float(pl["local_e"]), float(pl["local_n"])
        ring = [(e0 + u * c + v * s, n0 - u * s + v * c) for u, v in fp]
        out.append(ring + ring[:1])
    return out


def rect_inside_ring(rect, ring) -> bool:
    (e0, e1), (n0, n1) = rect
    return all(nobuild.inside(p, ring) for p in
               ((e0, n0), (e1, n0), (e1, n1), (e0, n1)))


def measure(camp: dict, field: Heightfield, streets: list, walls: list, prints: list,
            rings: dict) -> dict:
    """The tests a camp's ground must pass, each as the reading the record states."""
    (e0, e1), (n0, n1) = camp["e"], camp["n"]
    rect = ((e0, e1), (n0, n1))
    cid = camp["id"]
    samples = [field.height(e0 + (e1 - e0) * i / 4, n0 + (n1 - n0) * j / 4)
               for i in range(5) for j in range(5)]
    if any(h is None for h in samples):
        raise SystemExit(f"{cid}: part of the camp stands off the modelled terrain")
    lo, hi = min(samples), max(samples)
    if lo < DRY_M:
        raise SystemExit(f"{cid}: a point stands {lo:.2f} m above the water, under the "
                         f"{DRY_M} m dry margin")
    if hi - lo > LEVEL_M:
        raise SystemExit(f"{cid}: the ground falls {hi - lo:.2f} m across the camp, more "
                         f"than {LEVEL_M} m")
    road, road_id = math.inf, None
    for sid, path, half in streets:
        d = rect_clear_of(rect, [path]) - half
        if d < road:
            road, road_id = d, sid
    if road < CLEARANCE_M:
        raise SystemExit(f"{cid}: {road:.2f} m from the drawn edge of {road_id}")
    fence = rect_clear_of(rect, walls) if walls else math.inf
    if fence < CLEARANCE_M:
        raise SystemExit(f"{cid}: {fence:.2f} m from a fence run")
    built = rect_clear_of(rect, prints) if prints else math.inf
    if built < CLEARANCE_M:
        raise SystemExit(f"{cid}: {built:.2f} m from a committed footprint")
    cem = rings["fort_cemetery"]
    grave = rect_clear_of(rect, [cem + cem[:1]])
    if grave < CEMETERY_SKIRT_M:
        raise SystemExit(f"{cid}: {grave:.2f} m from the Fort Cemetery, inside its "
                         f"{CEMETERY_SKIRT_M:.0f} m skirt")
    res = rect_inside_ring(rect, rings["fort_dearborn_reservation"])
    if res != camp["on_reservation"]:
        raise SystemExit(f"{cid}: on the reservation is {res}, and the camp says "
                         f"{camp['on_reservation']}")
    if not camp["on_reservation"] and any(
            rect_clear_of(rect, [r + r[:1]]) == 0.0 for r in rings.values()):
        raise SystemExit(f"{cid}: touches refused ground it does not claim")
    return {"lo": lo, "hi": hi, "road": road, "road_id": road_id, "fence": fence,
            "built": built, "cemetery": grave}


def record(camp: dict, m: dict, datum: dict, ground: dict, hh: list) -> dict:
    rec = _record(camp, m, datum, ground)
    if not camp.get("seats"):
        return rec
    # The emigrants' shore camp (T-1979): the land-sale camp's ground tests and tent
    # forms, with what it is FOR said in its own words.
    ph = rec["phases"][0]
    form = ph["form"]
    persons = sum(r[3] for r in hh)
    form["tents"]["note"] = (
        f"ONE TENT A HOUSEHOLD, for the {len(hh)} households "
        "1835_transient_persons.json deals to 'a tent at the landing place' and then to "
        "this shore: the American says SOME built tents at the landing, so four stand "
        "there and the rest of the class is drawn here, off the working wharf frontage "
        "(T-1979). One family to one tent is the reading that invents no sharing. L356.")
    form["wagons"]["note"] = (
        "NOT ATTESTED. A family that came by lake and shipped its wagon on the schooner "
        "drove it off the wharf to wherever it camped; two to eleven tents is the "
        "restrained reading, and the owner has asked that wagons not be rationed "
        "(AGENTS.md, 2026-08-18). Invented. L356.")
    form["baggage_heaps"]["note"] = (
        "None: every household here has a tent and its baggage is in it. L356.")
    form["arrangement"]["note"] = (
        "A scatter, because families that came off different vessels over a fortnight "
        "pitched where there was room, not in a row.")
    ph["position"]["note"] = ph["position"]["note"].replace(
        "the nearest open ground to the landing", "the nearest open ground to the "
        "landing, off the working wharf frontage,").replace("L355.", "L356.")
    ph["position"]["symbolic_location"] = ph["position"]["symbolic_location"].replace(
        "north-east of the Fort Cemetery, south-east of the garrison garden, south-west "
        "of the factor's house, and short of the lake beach.",
        "east of the Fort Cemetery, south of the land-sale camp, and short of the lake "
        "beach.")
    ph["footprint"]["note"] = ph["footprint"]["note"].replace("L355.", "L356.")
    ph["change_note"] = ("Emigrants' tents on the reservation shore, moved off the South "
                         "Water wharves. T-1979.")
    rec["function"]["note"] = rec["function"]["note"].replace(
        "on the owner's ask (T-1214) and labelled so; L355.",
        "on the owner's report of 2026-10-02 that a camp belongs off the town's working "
        "frontage (T-1979), and labelled so; L356.")
    names = "; ".join(f"{r[2].split(' — ')[0]} ({r[1]})" for r in hh)
    rec["occupants"] = {
        "value": f"{len(hh)} households of the summer's crowd, {persons} persons, in "
                 f"tents: {names}.",
        "confidence": "reconstructed",
        "note": "Every one of these households is RECONSTRUCTED by "
                "tools/reconstruct_transients_1835.py (T-1353): a name off the 1835 "
                "surname pool given to a slot the cohort model counts, and not a person "
                "any source names. Their own records name the lake shore south of the "
                "fort as the candidate ground, conjectural; this camp is where T-1214 "
                "stands it. No figure is drawn for any of them (L1).",
    }
    rec["research_note"] = (
        "T-1979, on the owner's report of 2026-10-02: the emigrants' tents the American "
        "puts at the landing, all but four of them moved to the nearest open ground off "
        "the wharf frontage. WHAT WOULD REPLACE THIS: a letter, a diary or a view of the "
        "summer of 1835 saying where the emigrants who could not get a room pitched.")
    return rec


def _record(camp: dict, m: dict, datum: dict, ground: dict) -> dict:
    (e0, e1), (n0, n1) = camp["e"], camp["n"]
    length, depth = round(e1 - e0, 2), round(n1 - n0, 2)
    shore = camp["on_reservation"]
    where = (f"On the United States Reservation south of Fort Dearborn, between local "
             f"E +{e0:.0f} and E +{e1:.0f} and N {n0:+.0f} to {n1:+.0f}: north-east of "
             f"the Fort Cemetery, south-east of the garrison garden, south-west of the "
             f"factor's house, and short of the lake beach."
             if shore else
             f"On the prairie west of the Des Plaines Street line, between local "
             f"E {e0:.0f} and E {e1:.0f} and N {n0:.0f} to {n1:.0f}: beyond the last "
             f"drawn street of the West Division, just north of the line Randolph would "
             f"carry west, where the road out to the Des Plaines crossing left the town.")
    tests = (f"every sampled point of its ground between {m['lo']:.2f} and "
             f"{m['hi']:.2f} m above the water plane on the committed heightfield; "
             f"{m['road']:.1f} m clear of the drawn edge of the nearest roadway "
             f"({m['road_id']}); {m['built']:.1f} m clear of the nearest committed "
             f"footprint; {m['fence']:.1f} m clear of the nearest fence run")
    if shore:
        tests += (f"; {m['cemetery']:.1f} m clear of the Fort Cemetery's ring, outside "
                  f"its {CEMETERY_SKIRT_M:.0f} m skirt")
    if shore:
        why_here = ("THE GROUND IS A CONJECTURE AND THE SPOT IS OURS. "
                    "1835_camp_grounds.json offers the lake shore south of the fort "
                    "as the nearest open ground to the landing that carried no lot "
                    "line in July 1835 — unplatted, unsold, with no street across it — "
                    "and grades the candidacy conjectural: no source says anybody "
                    "camped there. This camp stands on the stretch of it a visitor "
                    "at the fort's south-west corner looks across: ")
        refused = ("It stands on ground 1835_no_build_ground.json refuses to a "
                   "builder, and that file permits it by name: the camp-grounds file "
                   "rules that a crowd sleeping rough on the shore for a fortnight is "
                   "not a dwelling and asked nobody's leave. ")
    else:
        why_here = ("THE GROUND IS A CONJECTURE AND THE SPOT IS OURS. "
                    "1835_camp_grounds.json offers the prairie edge beyond the "
                    "westernmost platted corridor as where a wagon party stops "
                    "without entering the town, and grades the candidacy conjectural: "
                    "it rests on the direction of the traffic and nothing else. The "
                    "camp stands at the western edge of the modelled ground, off the "
                    "end of Randolph's drawn line: ")
        refused = ""
    form = {
        "tents": {
            "value": camp["tents"],
            "confidence": "reconstructed",
            "note": (f"{camp['tents']} TENTS, AND NOT A COUNT OF ANYBODY. The register's "
                     "77 unseated visitors at the sale would fill this many wall tents "
                     "about one and a half times over at four men to a tent; most of "
                     "them slept where the transient model already sleeps the crowd, "
                     "in rooms and on floors, and twelve is the share drawn as having "
                     "come with canvas. Invented. L355."
                     if shore else
                     f"{camp['tents']} WEDGE TENTS for a party of four wagons: the "
                     "wagon beds carried the bedding and the tents took who did not fit. "
                     "Invented. L355."),
        },
        "tent_kind": {
            "value": camp["tent_kind"],
            "confidence": "reconstructed",
            "note": ("NO SOURCE DESCRIBES THE TENTS. Wall and wedge tents alternately, "
                     "the two forms an outfitter of the 1830s sold. L355."
                     if camp["tent_kind"] == "mixed" else
                     "NO SOURCE DESCRIBES THE TENTS. The wedge tent is the smaller and "
                     "cheaper of the two forms the archetype carries, and the one a "
                     "family going on by wagon would carry. L355."),
        },
        "wagons": {
            "value": camp["wagons"],
            "confidence": "reconstructed",
            "note": ("THE COUNTRY CAME TO THE SALE BY ROAD. A buyer from the "
                     "settlements west of the town drove in, and the "
                     "owner has asked that wagons not be rationed (AGENTS.md, "
                     "2026-08-18); the number is invented. L355."
                     if shore else
                     "A PARTY OF FOUR WAGONS, invented: families came overland to "
                     "Chicago from Indiana and Ohio in 1835 as well as by lake, and "
                     "a party travelled together. L355."),
        },
        "brush_shelters": {
            "value": camp["brush_shelters"],
            "confidence": "reconstructed",
            "note": "A lean-to of poles and cut brush, the cheapest roof there is. "
                    "Invented. L355.",
        },
        "fire_rings": {
            "value": camp["fire_rings"],
            "confidence": "reconstructed",
            "note": ("One cooking fire to two tents. The fires are drawn out: no flame, "
                     "no smoke, nobody at them (L1). L355."
                     if shore else
                     "Two cooking fires inside the ring of wagons. Drawn out: no flame, "
                     "no smoke, nobody at them (L1). L355."),
        },
        "woodpiles": {
            "value": camp["woodpiles"],
            "confidence": "reconstructed",
            "note": "Cordwood for the fires. Invented. L355.",
        },
        "baggage_heaps": {
            "value": camp["baggage_heaps"],
            "confidence": "reconstructed",
            "note": ("Chests and a barrel set down where a buyer had no tent of his "
                     "own. Invented. L355."
                     if shore else
                     "What came off the wagons for the night. Invented. L355."),
        },
        "arrangement": {
            "value": camp["arrangement"],
            "confidence": "reconstructed",
            "note": ("A scatter, because a crowd that arrived party by party over a "
                     "fortnight pitched where there was room, not in a row."
                     if shore else
                     "A ring about the fires, because one party camps round its own "
                     "fires with its wagons drawn up close."),
        },
        "canvas_condition": {
            "value": camp["canvas_condition"],
            "confidence": "reconstructed",
            "note": ("Weathered: canvas a fortnight in the sun on the lake shore."
                     if shore else
                     "Patched: wagon covers and tents that had come hundreds of miles "
                     "overland."),
        },
    }
    occupants = (
        "Nobody this layer counts. The land-sale crowd is the transient model's first "
        "refusal (1835_transient_persons.json § refusals): 77 visitors the Public "
        "Domain register names at the sale of 26-27 June 1835 whom no resident card "
        "places, reserved and left unminted because a drawn person may never stand in "
        "for a named one. So this camp seats none of them and moves no count; its tents "
        "stand for that crowd's ground. No figure is drawn (L1)."
        if shore else
        "Nobody this layer counts. The transient model (T-1352/T-1353) counts the lake "
        "arrivals the papers describe and deals its camp households to the landing "
        "place and the lake shore; no overland party is a row of it. So this camp seats nobody and "
        "moves no count. No figure is drawn (L1).")
    return {
        "id": camp["id"],
        "name": camp["name"],
        "aka": camp["aka"],
        "archetype": "camp",
        "phases": [{
            "id": "camp_1835",
            "documented_range": {
                "from": camp["range"][0],
                "to": camp["range"][1],
                "confidence": "reconstructed",
                "sources": camp["range_sources"],
                "note": camp["range_note"],
            },
            "position": {
                "utm_e": round(datum["origin_utm_e"] + e0, 2),
                "utm_n": round(datum["origin_utm_n"] + n0, 2),
                "rotation_deg": 0.0,
                "symbolic_location": where,
                "confidence": "reconstructed",
                "note": why_here + tests + ". " + refused +
                        "The point recorded is the camp's south-west corner, the "
                        "footprint's origin at rotation 0, so the camp opens north. "
                        "Placed by tools/place_camp_grounds_1835.py; L355.",
                "derivation": {
                    "method": "not_derivable",
                    "reason": "Placed against the drawn street lines, the heightfield, "
                              "the fences, the refused regions and every footprint by "
                              "tools/place_camp_grounds_1835.py, which re-derives it "
                              "with --check; it is not a street line or a traced "
                              "waterline validate.py can re-derive a coordinate from.",
                },
            },
            "footprint": {
                "polygon": [[0, 0], [length, 0], [length, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"The camp's ground, {length} x {depth} m. INVENTED in its "
                        "extent: room for the pitches the form asks at the archetype's "
                        "spacing, inside the ground the placer measured clear. L355.",
            },
            "form": form,
            "change_note": ("Canvas on the reservation shore in the week of the land "
                            "sale. T-1804." if shore else
                            "A wagon party's camp at the west edge of town. T-1804."),
        }],
        "function": {
            "value": camp["function"],
            "confidence": "reconstructed",
            "sources": [],
            "note": "THE GROUND IS A CONJECTURE AND SO IS THE USE. "
                    + ground["why"] + " Built at the reconstructed tier on the owner's "
                    "ask (T-1214) and labelled so; L355.",
        },
        "occupants": {
            "value": occupants,
            "confidence": "reconstructed",
            "note": "Seats nobody: see the value. T-1804.",
        },
        "research_note": "T-1804, the second piece of T-1214: the camps of the two "
                         "conjectural grounds the owner named. The Native and Métis "
                         "camps are NOT built here — T-1177 refused a count for them and "
                         "the question is the owner's. WHAT WOULD REPLACE THIS: "
                         + ("an account of the June 1835 land sale saying where the "
                            "crowd that came for it slept"
                            if shore else
                            "a letter or diary of an overland party reaching Chicago in "
                            "1835 saying where it stopped") + ".",
        "review_required": False,
    }


def derive() -> list:
    datum = load(DATUM)
    field = Heightfield.load(EPOCH)
    if field is None:
        raise SystemExit("the committed heightfield is missing")
    streets, walls, prints = roadways(), fences(), footprints()
    rings = {r["id"]: nobuild.region_ring(r)
             for r in nobuild.load(nobuild.NO_BUILD_PATH)["regions"]}
    g = grounds()
    out = []
    for camp in CAMPS:
        ground = g.get(camp["ground"])
        if ground is None:
            raise SystemExit(f"{camp['id']}: 1835_camp_grounds.json has no ground "
                             f"'{camp['ground']}'")
        m = measure(camp, field, streets, walls, prints, rings)
        hh = seated(camp["ground"]) if camp.get("seats") else []
        if camp.get("seats") and len(hh) != camp["tents"]:
            raise SystemExit(f"{camp['id']}: the transient model deals {len(hh)} tent "
                             f"households to {camp['ground']}; the camp pitches "
                             f"{camp['tents']}. One tent a household: re-count CAMPS.")
        out.append(record(camp, m, datum, ground, hh))
    return out


# Fields another tool writes onto these records, which this one must carry rather than
# drop: tools/resolve_land_tracts.py --build stamps `land_owner` on any structure that
# stands inside a land-sale tract, and the shore camp stands on the reservation's.
FOREIGN = ("land_owner",)


def keep_foreign(rec: dict, path: Path) -> dict:
    """The derived record with any FOREIGN field the committed file carries, in the
    committed file's key order so neither tool's rewrite moves a line."""
    if not path.exists():
        return rec
    old = load(path)
    out = {}
    for k in old:
        if k in rec:
            out[k] = rec[k]
        elif k in FOREIGN:
            out[k] = old[k]
    for k in rec:
        out.setdefault(k, rec[k])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = 0
    for rec in derive():
        p = STRUCTURES / f"{rec['id']}.json"
        rec = keep_foreign(rec, p)
        text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        if a.check:
            if not p.exists() or p.read_text() != text:
                print(f"FAIL {p.relative_to(ROOT)} is not what the placement derives; "
                      f"run tools/place_camp_grounds_1835.py")
                bad += 1
            else:
                print(f"ok   {rec['id']}")
        else:
            p.write_text(text)
            print(f"wrote {p.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
