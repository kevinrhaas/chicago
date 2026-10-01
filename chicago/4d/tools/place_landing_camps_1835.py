#!/usr/bin/env python3
"""Place the camps of the landing place: the tents and baggage of the summer crowd on
the South Water bank (T-1803, the first piece of T-1214).

WHAT THIS PLACES. `data/reconstruction/1835_camp_grounds.json` offers five grounds and
grades one `documented`: the landing place, where the Chicago American of 13 June 1835
puts the emigrants "under the open sky upon the wharves" and says "Some build tents
upon the spot they were landed from the boats". `1835_transient_persons.json` (T-1353)
deals 28 camp households to that ground and to no other — 15 in "a tent at the landing
place" and 13 under "the open sky upon the wharves". This tool gives those 28 ground.

WHERE, AND WHAT BOUNDS IT. The candidate's own rule: the bank the landings layer stands
its decks on, taken landward of the deck line. Measured, that is the strip between
South Water Street's roadway and the traced 1834 south bank, and it is only wide enough
for a row of tents from about E +262 to E +342 — between J. H. Kinzie's landing and
Jones's, the stretch where the dry bank runs 9 to 16 m. West of it the bank closes on
the street; east of it the river walk takes the strip. Two camps stand there, a row
each, opening south onto the street they came up from the boats by.

THE STREET LINE. This tool reads `data/streets/1835.json`'s DRAWN centreline for South
Water and keeps every camp clear of the corridor that line draws. That is the line the
rendered roadway and the block grid stand on (AGENTS.md rule 10): the question here is
whether canvas would stand in the road a visitor sees. It does not call `corridors`,
`control_offsets`, `intrusion` or `block_edges`. On the CONTROL line the platted street
ran to the water and the whole strip is street — a camp on it is a camp in the plat's
roadway, which is what an emigrant who could not get a room did, and is said so on
every record.

    python3 tools/place_landing_camps_1835.py           # write the two records
    python3 tools/place_landing_camps_1835.py --check   # re-derive; fail on drift
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

DATA = ROOT / "data"
DATUM = DATA / "datum.json"
STREETS = DATA / "streets" / "1835.json"
LANDINGS = DATA / "wharves" / "river_landings.json"
RIVER_WALKS = DATA / "frontage" / "river_walk_frontage.json"
BOATS = DATA / "boats" / "era_boats.json"
TRANSIENTS = DATA / "residents" / "transients"
SIDECARS = DATA / "sidecars" / "1835"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
STRUCTURES = DATA / "structures"

TENT_CLASS = "a_tent_at_the_landing_place"
SKY_CLASS = "the_open_sky_upon_the_wharves"
GROUND = "the_landing_place"

# The least a camp's edge may stand from the drawn roadway, a deck, a walk, a beached
# boat or a committed footprint, and the least height above the water plane any
# corner of it may have. 0.20 m is the wet margin: below it the heightfield is the
# shelving bank, where canvas would stand in the river's edge.
CLEARANCE_M = 1.0
DRY_M = 0.20

# The two camps: (id, the camp's west and east ends along the bank, its south and
# north edges, its arrangement, its share of the 28). The ends are the measured strip
# (module doc); the split between the two is at the narrowing by E +299, where the
# beached rowboats lie and the bank comes in.
CAMPS = (
    {"id": "landing_camp_west", "name": "The emigrants' camp at the landing, west",
     "e": (264.0, 297.0), "n": (20.0, 26.4), "tents": 7, "sky": 6,
     "wagons": 1, "brush_shelters": 0},
    {"id": "landing_camp_east", "name": "The emigrants' camp at the landing, east",
     "e": (300.5, 342.5), "n": (20.5, 27.5), "tents": 8, "sky": 7,
     "wagons": 1, "brush_shelters": 1},
)


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def households() -> tuple[list, list]:
    tent, sky = [], []
    for f in sorted(TRANSIENTS.glob("*.json")):
        d = load(f)
        t = d.get("transient") or {}
        if t.get("household_kind") != "camp":
            continue
        places = {r.get("place_id") for r in d.get("lodged_at") or []}
        if GROUND not in places:
            continue
        row = (t["slot"], d["id"], d["name"], int(d.get("persons") and len(d["persons"])
                                                  or 0))
        (tent if t["sleeping_class"] == TENT_CLASS else sky).append(row)
    return sorted(tent), sorted(sky)


def drawn_edge_n(path: list, half: float, e: float) -> float:
    """North edge of the drawn South Water corridor at easting `e`."""
    for (e0, n0), (e1, n1) in zip(path, path[1:]):
        if e0 <= e <= e1:
            return n0 + (n1 - n0) * (e - e0) / (e1 - e0) + half
    raise ValueError(f"E {e} is off South Water's drawn line")


def _seg_dist(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy)
                                              / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def rect_clear_of(rect, pts_or_polys) -> float:
    """Least distance from the camp rectangle to any of the given polylines/points."""
    (e0, e1), (n0, n1) = rect
    best = math.inf
    for shape in pts_or_polys:
        if len(shape) == 1:
            x, y = shape[0]
            dx = max(e0 - x, 0.0, x - e1)
            dy = max(n0 - y, 0.0, y - n1)
            best = min(best, math.hypot(dx, dy))
            continue
        segs = list(zip(shape, shape[1:]))
        corners = [(e0, n0), (e1, n0), (e1, n1), (e0, n1)]
        for a, b in segs:
            for c in corners:
                best = min(best, _seg_dist(c, a, b))
            for x, y in (a, b):
                if e0 <= x <= e1 and n0 <= y <= n1:
                    return 0.0
    return best


def obstacles(origin) -> dict:
    out = {"wharf decks": [], "river walks": [], "beached boats": [], "footprints": []}
    for w in load(LANDINGS)["wharves"]:
        q = w["deck_quad_local_enu_m"]
        out["wharf decks"].append([tuple(p) for p in q + q[:1]])
    for w in load(RIVER_WALKS)["walks"]:
        out["river walks"].append([tuple(p) for p in w["centreline_local_enu_m"]])
    for b in load(BOATS)["boats"]:
        p = b.get("position_local_enu_m")
        if p:
            out["beached boats"].append([tuple(p)])
    for f in sorted(SIDECARS.glob("*.json")):
        sc = load(f)
        if sc.get("archetype") == "camp":
            continue
        pl, fp = sc.get("placement") or {}, (sc.get("footprint") or {}).get("polygon")
        if not fp or pl.get("local_e") is None:
            continue
        th = math.radians(float(pl.get("rotation_deg") or 0.0))
        c, s = math.cos(th), math.sin(th)
        e0, n0 = float(pl["local_e"]), float(pl["local_n"])
        ring = [(e0 + u * c + v * s, n0 - u * s + v * c) for u, v in fp]
        out["footprints"].append(ring + ring[:1])
    return out


def record(camp: dict, tent: list, sky: list, datum: dict, edge_n: float,
           clear: dict, lo_h: float) -> dict:
    (e0, e1), (n0, n1) = camp["e"], camp["n"]
    length, depth = round(e1 - e0, 2), round(n1 - n0, 2)
    persons = sum(r[3] for r in tent + sky)
    names = "; ".join(f"{r[2].split(' — ')[0]} ({r[1]})" for r in tent)
    sky_names = "; ".join(f"{r[2].split(' — ')[0]} ({r[1]})" for r in sky)
    fires = math.ceil(len(tent) / 2)
    clear_txt = ", ".join(f"{k} {v:.1f} m" for k, v in clear.items())
    return {
        "id": camp["id"],
        "name": camp["name"],
        "aka": ["the tents at the landing"],
        "archetype": "camp",
        "phases": [{
            "id": "camp_1835",
            "documented_range": {
                "from": "1835-06-01",
                "to": "1835-09-30",
                "confidence": "reconstructed",
                "sources": ["chicago_american_1835"],
                "note": "THE SEASON, NOT THE CAMP. The American of 13 June 1835 has the "
                        "tents already standing; the range opens at the start of that "
                        "June and closes at the end of the navigation summer the crowd "
                        "came in on. No source dates any one tent, and a camp of people "
                        "awaiting lots was struck and repitched as its families moved "
                        "on. What the range says is that on 1 July 1835 canvas stood "
                        "here. T-1803.",
            },
            "position": {
                "utm_e": round(datum["origin_utm_e"] + e1, 2),
                "utm_n": round(datum["origin_utm_n"] + n1, 2),
                "rotation_deg": 180.0,
                "symbolic_location": "The South Water Street bank of the main stem "
                                     f"between local E +{e0:.0f} and E +{e1:.0f}: "
                                     "landward of the landings, between the street's "
                                     "roadway and the traced 1834 bank.",
                "confidence": "reconstructed",
                "note": "THE GROUND IS DOCUMENTED AND THE SPOT IS OURS. The American "
                        "puts tents 'upon the spot they were landed from the boats', "
                        "and 1835_camp_grounds.json resolves that to the bank the "
                        "landings stand their decks on, taken landward of the deck "
                        "line. This camp stands on the stretch of that bank where the "
                        f"dry strip is widest: its south edge {n0 - edge_n:.1f} m clear "
                        "of South Water's DRAWN roadway (the line the scene's road "
                        "stands on), every corner at least "
                        f"{lo_h:.2f} m above the water plane on the committed "
                        f"heightfield, and clear of: {clear_txt}. On the street's "
                        "CONTROL line (AGENTS.md rule 10) the platted street ran to "
                        "the water and this ground is roadway; a camp of people "
                        "nobody had a room for is the ordinary reading of a crowd "
                        "on the riverfront, and it is drawn there. That lap is REFUSED "
                        "IN WRITING (T-1803, tools/corridor_intrusion_baseline.json): "
                        "the whole dry strip lies inside the control corridor, so the "
                        "only escape runs north across the camp's own front and off the "
                        "bank into the river, and a camp moved anywhere else would no "
                        "longer stand on the ground the American names. The point recorded "
                        "is the camp's north-east corner, the footprint's origin at "
                        "rotation 180. Placed by tools/place_landing_camps_1835.py; "
                        "L321.",
                "derivation": {
                    "method": "not_derivable",
                    "reason": "Placed against the drawn street line, the traced bank "
                              "and the heightfield by tools/place_landing_camps_1835.py,"
                              " which re-derives it with --check; it is not a street "
                              "line or a traced waterline validate.py can re-derive a "
                              "coordinate from.",
                },
            },
            "footprint": {
                "polygon": [[0, 0], [length, 0], [length, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"The camp's ground, {length} x {depth} m: the length of bank "
                        "this camp's share of the row needs at the archetype's pitch "
                        "(camp_params.row_length), inside the measured strip. "
                        "INVENTED in its extent; bounded by the roadway, the bank and "
                        "the landings either side. L321.",
            },
            "form": {
                "tents": {
                    "value": len(tent),
                    "confidence": "reconstructed",
                    "note": f"ONE TENT A HOUSEHOLD, for the {len(tent)} households "
                            "1835_transient_persons.json deals to 'a tent at the "
                            "landing place' and this record seats. The American "
                            "says some built tents; how many people a tent held is "
                            "not stated, and one family to one tent is the reading "
                            "that invents no sharing. L321.",
                },
                "tent_kind": {
                    "value": "mixed",
                    "confidence": "reconstructed",
                    "note": "NO SOURCE DESCRIBES THE TENTS. Wall tents and wedge "
                            "tents, alternately, are the two forms an outfitter or "
                            "a quartermaster of the 1830s sold; an emigrant family "
                            "landing at Chicago carried what it had bought in the "
                            "East or sewn. L321.",
                },
                "wagons": {
                    "value": camp["wagons"],
                    "confidence": "reconstructed",
                    "note": "NOT ATTESTED AT THE LANDING. An emigrant family that "
                            "came by lake shipped its wagon on the schooner and "
                            "drove it west from here; one wagon to a camp is the "
                            "restrained reading, and the owner has asked that "
                            "wagons not be rationed (AGENTS.md, 2026-08-18). L321.",
                },
                "brush_shelters": {
                    "value": camp["brush_shelters"],
                    "confidence": "reconstructed",
                    "note": "A lean-to of poles and cut brush, the cheapest roof "
                            "there is. Invented. L321.",
                },
                "fire_rings": {
                    "value": fires,
                    "confidence": "reconstructed",
                    "note": "One cooking fire to two tents, rounded up. The fires are "
                            "drawn out: no flame, no smoke, nobody at them (L1). L321.",
                },
                "woodpiles": {
                    "value": max(1, fires // 2),
                    "confidence": "reconstructed",
                    "note": "Cordwood for the fires, one pile to two of them. L321.",
                },
                "baggage_heaps": {
                    "value": len(sky),
                    "confidence": "reconstructed",
                    "note": f"ONE HEAP A HOUSEHOLD, for the {len(sky)} households "
                            "dealt to 'the open sky upon the wharves'. They had no "
                            "tent, so what stands for them is what they had landed "
                            "with — chests, a barrel, a blanket roll — set down beside "
                            "the tents rather than on the decks, which are working "
                            "landings. L321.",
                },
                "arrangement": {
                    "value": "row",
                    "confidence": "reconstructed",
                    "note": "One row along the bank, because the dry strip between "
                            "the roadway and the water is a row wide.",
                },
                "canvas_condition": {
                    "value": "weathered",
                    "confidence": "reconstructed",
                    "note": "Canvas carried from the East, then a lake passage and a "
                            "fortnight of sun and wood smoke: greyed duck, not new "
                            "cream. L321.",
                },
            },
            "change_note": "Canvas on the South Water bank where the emigrants landed. "
                           "T-1803.",
        }],
        "function": {
            "value": "emigrant_camp",
            "confidence": "inferred",
            "sources": ["chicago_american_1835"],
            "note": "THE USE IS DOCUMENTED, THE CAMP IS DRAWN. The American of 13 June "
                    "1835: 'our wharves are covered with [men], women and children "
                    "just landed from the vessels ... who [had else] remained under "
                    "the open [sk]y upon the wharves. Some build tents upon the spot "
                    "[t]hey [we]re landed from the b[oa]ts.' Inferred, not attested, "
                    "because the paper does not say where on the riverfront, and this "
                    "is one stretch of it.",
        },
        "occupants": {
            "value": f"{len(tent) + len(sky)} households of the summer's crowd, "
                     f"{persons} persons: in tents, {names}; in the open beside "
                     f"them, {sky_names}.",
            "confidence": "reconstructed",
            "note": "Every one of these households is RECONSTRUCTED by "
                    "tools/reconstruct_transients_1835.py (T-1353): a name off the "
                    "1835 surname pool given to a slot the cohort model counts, and "
                    "not a person any source names. Their own records name 'the "
                    "landing place' as the candidate ground; this camp is where "
                    "T-1214 stands that ground. No figure is drawn for any of them "
                    "(L1).",
        },
        "research_note": "T-1803, the first piece of T-1214: the camps of the one "
                         "documented ground. The shore south of the fort, the west "
                         "approach and the Native and Metis camps are T-1804's. WHAT "
                         "WOULD REPLACE THIS: a view or a letter of the summer of 1835 "
                         "placing the tents on the riverfront, or describing them.",
        "review_required": False,
    }


def derive() -> list:
    datum = load(DATUM)
    st = next(s for s in load(STREETS)["streets"] if s["id"] == "south_water")
    path, half = st["path_local_enu_m"], st["corridor_width_m"] / 2.0
    field = Heightfield.load(EPOCH)
    obs = obstacles(None)
    tent, sky = households()
    if len(tent) != sum(c["tents"] for c in CAMPS) or len(sky) != sum(c["sky"] for c in CAMPS):
        raise SystemExit(f"the transient model deals {len(tent)} tent and {len(sky)} "
                         f"open-sky households to the landing place; CAMPS seats "
                         f"{sum(c['tents'] for c in CAMPS)} and "
                         f"{sum(c['sky'] for c in CAMPS)}. Re-split CAMPS.")
    out, ti, si = [], 0, 0
    for camp in CAMPS:
        (e0, e1), (n0, n1) = camp["e"], camp["n"]
        edge = max(drawn_edge_n(path, half, e) for e in (e0, (e0 + e1) / 2, e1))
        if n0 - edge < CLEARANCE_M:
            raise SystemExit(f"{camp['id']}: {n0 - edge:.2f} m from the drawn roadway")
        hs = [field.height(e, n) for e in (e0, (e0 + e1) / 2, e1) for n in (n0, n1)]
        if min(hs) < DRY_M:
            raise SystemExit(f"{camp['id']}: a corner stands {min(hs):.2f} m above the "
                             f"water, under the {DRY_M} m dry margin")
        clear = {}
        for k, shapes in obs.items():
            d = rect_clear_of(((e0, e1), (n0, n1)), shapes) if shapes else math.inf
            if d < CLEARANCE_M:
                raise SystemExit(f"{camp['id']}: {d:.2f} m from the {k}")
            clear[k] = d
        mine_t, mine_s = tent[ti:ti + camp["tents"]], sky[si:si + camp["sky"]]
        ti, si = ti + camp["tents"], si + camp["sky"]
        out.append(record(camp, mine_t, mine_s, datum, edge, clear, min(hs)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = 0
    for rec in derive():
        p = STRUCTURES / f"{rec['id']}.json"
        text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        if a.check:
            if not p.exists() or p.read_text() != text:
                print(f"FAIL {p.relative_to(ROOT)} is not what the placement derives; "
                      f"run tools/place_landing_camps_1835.py")
                bad += 1
            else:
                print(f"ok   {rec['id']}")
        else:
            p.write_text(text)
            print(f"wrote {p.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
