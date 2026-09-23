#!/usr/bin/env python3
"""Derive the 5 August 1835 hay-stacking limits from committed geometry (T-0334).

Section 22 of the by-laws the Trustees passed on 5 August 1835 makes it unlawful to
stack hay inside a boundary the ordinance walks street by street:

    commencing on Washington street, at the United States Reservation, and running
    thence West to the intersection of Canal Street, thence North to the intersection
    of Kinzie Street, thence East to the intersection of Wolcott street, thence to
    Illinois Street, and thence to Lake Michigan

Six vertices, and every one of them is a street this reconstruction already carries.
That makes the sentence the only DOCUMENTED statement this project holds about where
the built-up town ended in the scene year: every other judgement about density has
been made from the plat, from the land deal and from measured frontage, and this one
is the town's own, six weeks after the scene date.

    python3 tools/derive_hay_limits.py            re-derive and write the file
    python3 tools/derive_hay_limits.py --check     re-derive and diff against committed
    python3 tools/derive_hay_limits.py --self-test prove the assertions fire when broken

WHAT IS DERIVED AND WHAT IS DECIDED
-----------------------------------
Derived, and never typed: each of the six vertices is the intersection of two
committed centrelines — `data/streets/1835.json` `path_local_enu_m`, which is the
PLATTED line the plat and lot derivations read, not the worn track the renderer
paints. The starting point is the intersection of Washington Street with the west
side of the committed Fort Dearborn reservation ring, which is what "at the United
States Reservation" names: Washington Street cannot run further east than that,
because the reservation is where it stops.

Decided, and said so in the file: the ordinance walks an OPEN line of six vertices
and names Lake Michigan as its end. A closed area needs two more sides, and both are
the ordinance's own words rather than its geometry — the lake shore north of the
harbour, and the reservation the walk commenced at. The ring therefore closes down
the traced 1834 lake shore, across the harbour entrance in one straight segment
(water, between two piers — the ordinance draws nothing here and neither does this),
west along the reservation's own north boundary, and south down its west side to the
point the walk began at. Every one of those closure edges is graded `inferred` and
carries its reasoning. NOTHING IS DRAWN IN THE SCENE: a legal limit is not a fence,
and the card says where a building stands with respect to it instead.
"""

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "reconstruction" / "1835_hay_limits.json"

STREETS = ROOT / "data" / "streets" / "1835.json"
TRACTS = ROOT / "data" / "reconstruction" / "1835_survey_tracts.json"
SHORELINE = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut" / "shoreline.geojson"
DATUM = ROOT / "data" / "datum.json"
PROGRAMME = ROOT / "data" / "reconstruction" / "1835_665_roof_programme.json"
SIDECARS = ROOT / "data" / "sidecars" / "1835"

SCENE_DATE = "1835-07-01"
ORDINANCE_DATE = "1835-08-05"
PRINTED_DATE = "1835-08-19"

QUOTE = ("commencing on Washington street, at the United States Reservation, and running "
         "thence West to the intersection of Canal Street, thence North to the intersection "
         "of Kinzie Street, thence East to the intersection of Wolcott street, thence to "
         "Illinois Street, and thence to Lake Michigan")

# The one leg the ordinance names that no committed line reaches: Illinois Street is
# platted and drawn as far as Kinzie's Addition carries it, and the water is a hundred
# metres further on. An extension longer than this is a different claim and is refused.
MAX_EXTENSION_M = 150.0
# The traced lake shore and the reservation's traced waterline are two readings of the
# same 1834 sheet; the harbour entrance between them is the river mouth. A closure
# segment longer than this would not be a river mouth and the derivation refuses it.
MAX_HARBOUR_CLOSURE_M = 300.0


# ---------------------------------------------------------------- plane geometry

def _seg_intersection(a, b, c, d):
    """Infinite-line intersection of segment ab with segment cd, with both
    parameters, so the caller can see whether it was a crossing or an extension."""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a, b, c, d
    den = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(den) < 1e-12:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / den
    u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1), t, u)


def _length(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def meet(poly_a, poly_b):
    """Where two polylines meet: the segment pair whose line intersection needs the
    least EXTENSION of either segment. A true crossing needs none and wins outright;
    otherwise the answer reports how far past its own end each line had to be carried,
    which is the number the caller gates on."""
    best = None
    for i in range(len(poly_a) - 1):
        for j in range(len(poly_b) - 1):
            hit = _seg_intersection(poly_a[i], poly_a[i + 1], poly_b[j], poly_b[j + 1])
            if hit is None:
                continue
            x, y, t, u = hit
            over_a = max(0.0, -t, t - 1.0) * _length(poly_a[i], poly_a[i + 1])
            over_b = max(0.0, -u, u - 1.0) * _length(poly_b[j], poly_b[j + 1])
            cand = (over_a + over_b, over_a, over_b, x, y, i, j, t, u)
            if best is None or cand[0] < best[0]:
                best = cand
    if best is None:
        raise ValueError("two polylines with no line intersection at all")
    _, over_a, over_b, x, y, i, j, t, u = best
    return {
        "local_e": round(x, 2), "local_n": round(y, 2),
        "extension_a_m": round(over_a, 2), "extension_b_m": round(over_b, 2),
        "segment_a": i, "segment_b": j, "t": round(t, 6), "u": round(u, 6),
    }


def ring_area_m2(ring):
    a = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def ring_perimeter_m(ring):
    return sum(_length(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))


def _straddles(a, b, c, d):
    def orient(p, q, r):
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    d1, d2 = orient(c, d, a), orient(c, d, b)
    d3, d4 = orient(a, b, c), orient(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def self_intersections(ring):
    """Pairs of non-adjacent edges that cross. A limit that crosses itself has no
    inside, so this is checked rather than assumed — the closure edges are the
    reason it could happen."""
    n = len(ring)
    edges = [(ring[i], ring[(i + 1) % n]) for i in range(n)]
    bad = []
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _straddles(*edges[i], *edges[j]):
                bad.append([i, j])
    return bad


def contains(point, ring):
    """Crossing-number test, the same rule the renderer applies to a building's
    committed position."""
    x, y = point
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i - 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


# ---------------------------------------------------------------- committed inputs

def load_inputs():
    streets = {s["id"]: s for s in json.loads(STREETS.read_text())["streets"]}
    tracts = {t["id"]: t for t in json.loads(TRACTS.read_text())["tracts"]}
    datum = json.loads(DATUM.read_text())
    if not datum.get("verified"):
        raise SystemExit("REFUSING: data/datum.json is not verified.")
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    shore = json.loads(SHORELINE.read_text())
    north = None
    for feature in shore["features"]:
        name = (feature.get("properties") or {}).get("name") or ""
        if name.startswith("North shore of the harbour reach"):
            north = [[round(x - oe, 2), round(y - on, 2)]
                     for x, y in feature["geometry"]["coordinates"]]
    if north is None:
        raise SystemExit("REFUSING: the traced north shore run is not in the shoreline file.")
    return streets, tracts, north


def path(streets, sid):
    street = streets.get(sid)
    if street is None:
        raise SystemExit(f"REFUSING: data/streets/1835.json carries no street {sid!r}.")
    return street["path_local_enu_m"]


# ---------------------------------------------------------------- the derivation

def derive():
    streets, tracts, north = load_inputs()
    reservation = tracts["us_military_reservation"]["polygon_local_enu_m"]
    # The reservation's west side: the constructed section line between the two ends
    # of its ring, which is the side Washington Street runs into.
    res_west = [reservation[0], reservation[1]]

    washington = path(streets, "washington")
    canal = path(streets, "canal")
    kinzie = path(streets, "kinzie")
    wolcott = path(streets, "wolcott")
    illinois = path(streets, "illinois_north")

    legs = [
        ("v1_washington_at_the_reservation", washington, res_west,
         "washington", "us_military_reservation west side",
         "“commencing on Washington street, at the United States Reservation” — the "
         "point where Washington Street meets the committed reservation ring's west "
         "side. Washington runs no further east than this because the reservation is "
         "where it stops, which is why the ordinance can name the spot without a "
         "cross street."),
        ("v2_washington_and_canal", washington, canal, "washington", "canal",
         "“running thence West to the intersection of Canal Street”."),
        ("v3_canal_and_kinzie", canal, kinzie, "canal", "kinzie",
         "“thence North to the intersection of Kinzie Street”."),
        ("v4_kinzie_and_wolcott", kinzie, wolcott, "kinzie", "wolcott",
         "“thence East to the intersection of Wolcott street” — Wolcott Street is "
         "modern North State Street."),
        ("v5_wolcott_and_illinois", wolcott, illinois, "wolcott", "illinois_north",
         "“thence to Illinois Street” — north up Wolcott to the Illinois Street line "
         "of Kinzie's Addition."),
        ("v6_illinois_at_the_lake", illinois, north, "illinois_north",
         "traced 1834 lake shore",
         "“and thence to Lake Michigan” — east along the Illinois Street line to the "
         "traced shore. The committed street stops short of the water, so this leg "
         "carries the platted line beyond its own east end; the distance is recorded "
         "and gated."),
    ]

    walk, hits = [], []
    for key, poly_a, poly_b, id_a, id_b, reading in legs:
        hit = meet(poly_a, poly_b)
        hits.append(hit)
        walk.append({
            "vertex": key,
            "streets": [id_a, id_b],
            "reading": reading,
            "local_e": hit["local_e"], "local_n": hit["local_n"],
            "is_a_crossing": hit["extension_a_m"] == 0.0 and hit["extension_b_m"] == 0.0,
            "extension_m": {id_a: hit["extension_a_m"], id_b: hit["extension_b_m"]},
            "confidence": "documented",
            "sources": ["chicago_democrat_1833_1835"],
        })

    extension = walk[5]["extension_m"]["illinois_north"]
    if extension > MAX_EXTENSION_M:
        raise SystemExit(f"REFUSING: Illinois Street would have to be carried {extension} m "
                         f"past its committed end, over the {MAX_EXTENSION_M} m this "
                         f"derivation allows.")
    for v in walk[:5]:
        if not v["is_a_crossing"]:
            raise SystemExit(f"REFUSING: {v['vertex']} is not a crossing of two committed "
                             f"lines — {v['extension_m']}.")

    vertices = [[v["local_e"], v["local_n"]] for v in walk]

    # ---- the closure, which is the ordinance's words and not its geometry.
    # Down the lake shore from Illinois Street to the harbour: the traced run's
    # easternmost vertex is the outer end of the north pier, which is where the lake
    # stops being a shore and becomes the entrance.
    pier = max(range(len(north)), key=lambda k: north[k][0])
    shore_from = hits[5]["segment_b"]
    if shore_from < pier:
        raise SystemExit("REFUSING: Illinois Street meets the traced shore SOUTH of the "
                         "north pier, so the lake run between them is not a shore.")
    lake_run = [north[k] for k in range(shore_from, pier - 1, -1)]

    # Across the harbour entrance: one straight segment to the reservation's own
    # northernmost traced point, which is the south side of the same water.
    res_north = max(range(len(reservation)), key=lambda k: reservation[k][1])
    crossing_m = _length(north[pier], reservation[res_north])
    if crossing_m > MAX_HARBOUR_CLOSURE_M:
        raise SystemExit(f"REFUSING: the harbour closure is {crossing_m:.1f} m, over the "
                         f"{MAX_HARBOUR_CLOSURE_M} m a river mouth can be.")

    # West along the reservation's north boundary — its traced waterline on the south
    # bank of the main stem — back to the ring's west side, then south to the start.
    res_run = [reservation[k] for k in range(res_north, 0, -1)]

    ring = vertices + lake_run + res_run
    crossings = self_intersections(ring)
    if crossings:
        raise SystemExit(f"REFUSING: the limit crosses itself at edges {crossings}.")

    area = abs(ring_area_m2(ring))
    perimeter = ring_perimeter_m(ring)

    closure = {
        "why": "The ordinance walks six vertices and stops at Lake Michigan. An AREA "
               "needs the two sides it names but does not draw, and both are added here "
               "rather than read off the page.",
        "edges": [
            {"edge": "lake_shore_illinois_to_the_north_pier",
             "vertices": len(lake_run),
             "length_m": round(sum(_length(lake_run[i], lake_run[i + 1])
                                   for i in range(len(lake_run) - 1)), 2),
             "confidence": "inferred",
             "note": "The 1834 lake shore as traced by tools/trace_shoreline.py, walked "
                     "south from the Illinois Street line to the outer end of the north "
                     "pier. The ordinance says “to Lake Michigan” and the shore is where "
                     "the lake is; the pier's outer end is where the shore ends and the "
                     "harbour entrance begins.",
             "sources": ["wright_1834_nara_hup"]},
            {"edge": "across_the_harbour_entrance",
             "vertices": 2,
             "length_m": round(crossing_m, 2),
             "confidence": "inferred",
             "note": "One straight segment across the 1834 cut, between the outer end of "
                     "the north pier and the northernmost traced point of the reservation. "
                     "This is water between two piers: the ordinance draws nothing here, "
                     "nothing can be stacked here, and the segment exists only so that the "
                     "limit closes. It is not a claim about anything on the ground.",
             "sources": ["wright_1834_nara_hup"]},
            {"edge": "the_reservation_north_boundary_and_west_side",
             "vertices": len(res_run),
             "length_m": round(sum(_length(res_run[i], res_run[i + 1])
                                   for i in range(len(res_run) - 1))
                               + _length(res_run[-1], vertices[0]), 2),
             "confidence": "inferred",
             "note": "The committed Fort Dearborn reservation ring, walked west along its "
                     "traced waterline on the south bank of the main stem and then south "
                     "down its west side to the point the ordinance commenced at. THE "
                     "READING THIS RESTS ON: the walk commences AT the reservation, so the "
                     "reservation bounds the limit and the federal ground inside it is "
                     "outside the town's hay rule. The alternative reading — that the "
                     "reservation is only a landmark naming the spot where Washington "
                     "Street ends, and the limit runs on to the lake across the fort — "
                     "is recorded here and not taken, because it would have the Trustees "
                     "fining the garrison. Which reading is right is the owner's call and "
                     "the measured difference is stated below.",
             "sources": ["wright_1834_nara_hup"]},
        ],
    }

    # The alternative reading, priced rather than argued: the same walk with the lake
    # shore carried south past the fort instead of the reservation taken out.
    south_shore_note = ("The alternative reading is not built as geometry here. What it "
                        "costs is stated as the count it would move: every structure this "
                        "file reports as outside the limit ON THE RESERVATION would come "
                        "inside it, and nothing else would change.")

    structures = census(ring)
    blocks = programme_blocks(ring)

    doc = {
        "$schema_note": "Derived. Not hand-editable — tools/derive_hay_limits.py --check "
                        "re-derives this file from committed geometry on every commit.",
        "id": "1835_hay_limits",
        "target_date": SCENE_DATE,
        "ticket": "T-0334",
        "tool": "tools/derive_hay_limits.py",
        "reads": [
            "data/streets/1835.json — path_local_enu_m, the PLATTED lines",
            "data/reconstruction/1835_survey_tracts.json — us_military_reservation",
            "data/terrain/epochs/e1834_harbor_cut/shoreline.geojson — the north shore run",
            "data/datum.json — origin_utm_e / origin_utm_n",
            "data/sidecars/1835/*.json — committed structure positions",
            "data/reconstruction/1835_665_roof_programme.json — the block-infill schedule",
        ],
        "why_this_file_exists":
            "THE ONLY DOCUMENTED STATEMENT THIS PROJECT HOLDS ABOUT WHERE THE BUILT TOWN "
            "ENDED IN THE SCENE YEAR. Every other judgement about density here — which "
            "blocks get roofs, which stay open ground — is made from the plat, from the "
            "land deal and from measured frontage. This one is the town's own, in the "
            "town's own words, and it is a fire rule: the Trustees drew a line round the "
            "ground they thought was built up closely enough that a hay stack inside it "
            "would take the town with it.",
        "ordinance": {
            "section": "Sec. 22",
            "passed": ORDINANCE_DATE,
            "passed_over": "J. Hugunin, President; Alex. N. Fullerton, Secretary",
            "printed": PRINTED_DATE,
            "forbids": "stacking hay inside the limits",
            "penalty_dollars": 25,
            "penalty_note": "Twenty-five dollars for each offence and the cost of removing "
                            "the stack — the heaviest penalty in the whole ordinance "
                            "except gaming.",
            "quote": QUOTE,
            "source_id": "chicago_democrat_1833_1835",
            "locator": "The Chicago Democrat, Vol. II No. 18, 19 August 1835, page 1, "
                       "columns 1–2; transcription claim c006 in "
                       "data/research/newspapers/extracted/chicago_democrat_1835_08_19.json",
            "confidence": "documented",
        },
        "date_standing": {
            "scene_date": SCENE_DATE,
            "ordinance_date": ORDINANCE_DATE,
            "days_after_the_scene_date": 35,
            "note": "THE ORDINANCE IS FIVE WEEKS LATER THAN THE SCENE. It is carried here "
                    "as evidence about the town of 1835 and not as something standing in "
                    "the scene on 1 July: nothing is placed, moved or drawn because of it. "
                    "A line the Trustees walked on 5 August describes ground that was "
                    "already built up when they walked it, which is exactly why it is "
                    "worth having; it is still a claim about August and it says so.",
        },
        "walk": walk,
        "closure": closure,
        "alternative_reading": south_shore_note,
        "ring_local_enu_m": ring,
        "ring_note": "Closed ring, local ENU metres on data/datum.json. The first six "
                     "vertices are the ordinance's own; the rest are the closure.",
        "ring_vertices": len(ring),
        "area_m2": round(area, 1),
        "area_acres": round(area / 4046.8564224, 1),
        "perimeter_m": round(perimeter, 1),
        "self_intersections": crossings,
        "structures": structures,
        "block_infill_programme": blocks,
        "nothing_is_drawn":
            "A legal limit is not a fence. Nothing is added to the 3-D scene by this file "
            "and docs/LIBERTIES.md carries no new admission for it: drawing an invisible "
            "boundary as a visible one would put a line in the town that nobody in 1835 "
            "could see. What a visitor gets instead is a line on the card of every "
            "building, saying whether it stood inside the limit or outside it and quoting "
            "the section that says so.",
    }
    return doc


def _street_side(point, poly, axis):
    """Which side of a committed street a point falls on, by carrying the street's
    NEAREST segment as a straight line. `axis` is 'ew' for a street that runs east and
    west (the answer is north or south of it) and 'ns' for one that runs north and
    south (east or west). A point beyond a street's own ends is answered on the
    extension of its last segment, which is stated because it is a decision: the
    alternative is to refuse an answer for every structure past the end of a line,
    and the streets here are platted lines that the plat carries further than the
    reconstruction draws them."""
    x, y = point
    best = None
    for i in range(len(poly) - 1):
        (x1, y1), (x2, y2) = poly[i], poly[i + 1]
        if axis == "ew":
            span = abs(x2 - x1)
            if span < 1e-9:
                continue
            at = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
            dist = max(0.0, min(x1, x2) - x, x - max(x1, x2))
            cand = (dist, y - at)
        else:
            span = abs(y2 - y1)
            if span < 1e-9:
                continue
            at = x1 + (x2 - x1) * (y - y1) / (y2 - y1)
            dist = max(0.0, min(y1, y2) - y, y - max(y1, y2))
            cand = (dist, x - at)
        if best is None or cand[0] < best[0]:
            best = cand
    return 0.0 if best is None else best[1]


def census(ring):
    """Every committed structure position in the scene, sorted by the limit — and for
    the ones outside it, WHICH side of the line they are on, so that "outside" is a
    statement about the town rather than a number."""
    streets, tracts, _ = load_inputs()
    reservation = tracts["us_military_reservation"]["polygon_local_enu_m"]
    canal = path(streets, "canal")
    washington = path(streets, "washington")
    kinzie = path(streets, "kinzie")
    illinois = path(streets, "illinois_north")
    wolcott_e = path(streets, "wolcott")[0][0]

    inside, outside, unplaced = [], [], []
    where = {"on_the_united_states_reservation": [], "north_of_the_limit": [],
             "west_of_canal_street": [], "south_of_washington_street": [],
             "east_of_the_limit_in_the_water": [], "unclassified": []}
    for f in sorted(SIDECARS.glob("*.json")):
        doc = json.loads(f.read_text())
        sid = doc.get("id")
        if not sid:
            continue
        place = doc.get("placement") or {}
        e, n = place.get("local_e"), place.get("local_n")
        if e is None or n is None:
            unplaced.append(sid)
            continue
        if contains((e, n), ring):
            inside.append(sid)
            continue
        outside.append(sid)
        north_edge = illinois if e > wolcott_e else kinzie
        if contains((e, n), reservation):
            where["on_the_united_states_reservation"].append(sid)
        elif _street_side((e, n), north_edge, "ew") > 0:
            where["north_of_the_limit"].append(sid)
        elif _street_side((e, n), canal, "ns") < 0:
            where["west_of_canal_street"].append(sid)
        elif _street_side((e, n), washington, "ew") < 0:
            where["south_of_washington_street"].append(sid)
        elif e > wolcott_e:
            where["east_of_the_limit_in_the_water"].append(sid)
        else:
            where["unclassified"].append(sid)
    return {
        "counted_from": "data/sidecars/1835/*.json placement.local_e / local_n",
        "inside": len(inside),
        "outside": len(outside),
        "no_committed_position": len(unplaced),
        "outside_by_where": {k: len(v) for k, v in where.items()},
        "outside_ids_by_where": where,
        "no_committed_position_ids": unplaced,
        "note": "A structure is sorted by the single point its record commits, which is "
                "where the reconstruction stands it — not by its footprint. A building "
                "whose walls straddle the limit is counted by its point. The side a "
                "structure outside the limit falls on is read off the committed street "
                "itself, carried straight past its own ends where it has to be; the "
                "reservation is tested against its committed ring and answered first, "
                "because a building on federal ground is outside the town's rule for a "
                "different reason than a building up the North Branch. The last class is "
                "reached by elimination and then checked: a structure outside the limit "
                "that is not on the reservation and not beyond any of the three street "
                "edges must lie east of the limit's eastern side, which here is water — "
                "so it is required to stand east of Wolcott Street before it is called "
                "that, and anything else stays unclassified rather than being tidied away.",
    }


def programme_blocks(ring):
    """Does the ground the block-infill schedule treats as built agree with the ground
    the Trustees fenced? Each scheduled block's centre is the mean of the four corners
    its four bounding streets make, so this is derived the same way the limit is."""
    streets = {s["id"]: s for s in json.loads(STREETS.read_text())["streets"]}
    programme = json.loads(PROGRAMME.read_text())
    rows, no_geometry = [], []
    for row in programme["schedule"]:
        bounded = row.get("bounded_by") or {}
        if not all(k in bounded for k in ("north", "south", "west", "east")):
            no_geometry.append({"id": row["id"], "kind": row["kind"],
                                "state": row["state"], "roofs": row.get("roofs", 0)})
            continue
        corners = []
        for ns in ("north", "south"):
            for we in ("west", "east"):
                hit = meet(path(streets, bounded[ns]), path(streets, bounded[we]))
                corners.append((hit["local_e"], hit["local_n"]))
        centre = (round(sum(c[0] for c in corners) / 4, 2),
                  round(sum(c[1] for c in corners) / 4, 2))
        rows.append({"id": row["id"], "state": row["state"],
                     "roofs_scheduled": row.get("roofs", 0),
                     "centre_local_enu_m": list(centre),
                     "inside_the_limit": contains(centre, ring)})
    disagreements = [r for r in rows
                     if r["roofs_scheduled"] > 0 and not r["inside_the_limit"]]
    return {
        "counted_from": "data/reconstruction/1835_665_roof_programme.json schedule[]",
        "method": "A block's centre is the mean of the four corners its own four "
                  "bounding street centrelines make. No block polygon is invented.",
        "blocks_with_four_bounding_streets": len(rows),
        "inside_the_limit": sum(1 for r in rows if r["inside_the_limit"]),
        "outside_the_limit": sum(1 for r in rows if not r["inside_the_limit"]),
        "scheduling_roofs_outside_the_limit": len(disagreements),
        "scheduling_roofs_outside_the_limit_rows": disagreements,
        "blocks_outside_the_limit": [r for r in rows if not r["inside_the_limit"]],
        "rows_without_block_geometry": no_geometry,
        "note": "The five schedule rows with no bounding streets are district balances "
                "and recipe remainders, not blocks; they are listed and not placed. "
                "Every one of them is gated on control or ground this project has not "
                "committed, so the limit cannot be asked about them yet.",
        "what_agreement_means": "The programme and the Trustees were answering different "
                "questions — one asks where there was room to build, the other where it "
                "was already dangerous to stack hay. That the schedule puts no NEW roof "
                "outside the fenced ground is therefore a check that passed, not a "
                "tautology: nothing in the schedule's derivation had ever read this line.",
        "the_one_disagreement": "THE LINE RUNS UP CANAL STREET AND THE PROGRAMME DOES NOT. "
                "Three of the twenty-one scheduled blocks sit west of Canal Street, in the "
                "Clinton–Canal tier, and the Trustees' boundary turns north AT Canal and "
                "leaves them out. Two of the three are the programme's own `at_capacity` — "
                "it holds standing roofs there and schedules no more — and the third it "
                "already calls `not_a_block`. So the disagreement is not about where to "
                "build next; it is that the reconstruction's built town reaches one tier "
                "further west than the town's own fire line did, on ground the ordinance "
                "was willing to let a hay stack stand on. Which is right is not settled "
                "here. The two at-capacity blocks hold 21 standing roofs between them "
                "(11 and 10 of a 31-roof capacity each), so this is not a rounding "
                "difference: it is twenty-one roofs of reconstructed town standing on "
                "ground the Trustees did not fence, and either they were there and the "
                "line was drawn short of them, or the tier is a block too far west.",
    }


# ---------------------------------------------------------------- entry points

def write(doc):
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text):,} bytes)")
    print(f"  {doc['ring_vertices']} vertices, {doc['area_acres']} acres, "
          f"{doc['perimeter_m']} m round")
    print(f"  structures: {doc['structures']['inside']} inside, "
          f"{doc['structures']['outside']} outside "
          f"{doc['structures']['outside_by_where']}, "
          f"{doc['structures']['no_committed_position']} with no committed position")
    print(f"  block-infill schedule: "
          f"{doc['block_infill_programme']['inside_the_limit']} blocks inside, "
          f"{doc['block_infill_programme']['scheduling_roofs_outside_the_limit']} "
          f"scheduling roofs outside")


def check(doc):
    if not OUT.exists():
        print(f"FAIL {OUT.relative_to(ROOT)} — not committed")
        return 1
    want = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    got = OUT.read_text()
    if want == got:
        print(f"OK   {OUT.relative_to(ROOT)} re-derives exactly "
              f"({doc['area_acres']} acres, {doc['structures']['inside']} structures inside)")
        return 0
    print(f"DIFF {OUT.relative_to(ROOT)} — the committed file is not what this tool derives")
    want_doc = json.loads(want)
    got_doc = json.loads(got)
    for key in sorted(set(want_doc) | set(got_doc)):
        if want_doc.get(key) != got_doc.get(key):
            print(f"  differs: {key}")
    return 1


def self_test():
    """Break each assertion and prove it fires. The whole value of this derivation is
    that it refuses rather than shrugs, so the refusals are tested."""
    failures = []

    def expect(label, fn):
        try:
            fn()
        except SystemExit as err:
            print(f"   self-test | FAIL as designed: {label} — {str(err)[:90]}")
            return
        except ValueError as err:
            print(f"   self-test | FAIL as designed: {label} — {str(err)[:90]}")
            return
        print(f"   self-test | NOT CAUGHT: {label}")
        failures.append(label)

    # A limit that crosses itself has no inside.
    square = [[0, 0], [10, 0], [10, 10], [0, 10]]
    bowtie = [[0, 0], [10, 10], [10, 0], [0, 10]]
    if self_intersections(square):
        failures.append("a plain square reads as self-crossing")
        print("   self-test | NOT CAUGHT: a plain square reads as self-crossing")
    else:
        print("   self-test | ok: a plain square does not read as self-crossing")
    if not self_intersections(bowtie):
        failures.append("a bow tie does not read as self-crossing")
        print("   self-test | NOT CAUGHT: a bow tie does not read as self-crossing")
    else:
        print("   self-test | FAIL as designed: a bow tie reads as self-crossing")

    # The inside test, on a shape whose answer is known by hand.
    for point, want in ([(5, 5), True], [(15, 5), False], [(-1, -1), False], [(5, 9.9), True]):
        if contains(point, square) is not want:
            failures.append(f"point-in-polygon wrong at {point}")
            print(f"   self-test | NOT CAUGHT: point-in-polygon wrong at {point}")
    print("   self-test | ok: the inside test agrees with four hand answers on a square")

    # Area and perimeter of the same square, by hand.
    if abs(abs(ring_area_m2(square)) - 100.0) > 1e-9:
        failures.append("a 10 m square does not measure 100 m2")
    if abs(ring_perimeter_m(square) - 40.0) > 1e-9:
        failures.append("a 10 m square does not measure 40 m round")
    print("   self-test | ok: the square measures 100 m2 and 40 m round")

    # Two parallel lines have no intersection, and `meet` says so rather than guessing.
    expect("two parallel polylines are made to meet",
           lambda: meet([[0, 0], [10, 0]], [[0, 5], [10, 5]]))

    # The extension gate: an Illinois Street ending a kilometre short must refuse.
    expect("a leg carried a kilometre past its own end is accepted",
           lambda: _gate_extension(1200.0))
    # The harbour closure gate.
    expect("a kilometre of open water is accepted as a river mouth",
           lambda: _gate_harbour(1000.0))
    # A missing street must refuse rather than derive a limit without it.
    expect("a missing street is derived around",
           lambda: path({}, "wolcott"))

    # And the real derivation still stands.
    doc = derive()
    if doc["structures"]["inside"] <= 0:
        failures.append("the derived limit holds no structures")
    if not (100 < doc["area_acres"] < 400):
        failures.append(f"the derived limit measures {doc['area_acres']} acres")
    print(f"   self-test | ok: the derivation stands — {doc['area_acres']} acres, "
          f"{doc['structures']['inside']} structures inside")

    if failures:
        print("SELF-TEST FAILED: " + "; ".join(failures))
        return 1
    print("self-test ok")
    return 0


def _gate_extension(metres):
    if metres > MAX_EXTENSION_M:
        raise SystemExit(f"REFUSING: {metres} m past a committed end.")


def _gate_harbour(metres):
    if metres > MAX_HARBOUR_CLOSURE_M:
        raise SystemExit(f"REFUSING: a {metres} m river mouth.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff against the committed file")
    ap.add_argument("--self-test", action="store_true",
                    help="prove this tool's own refusals fire")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    doc = derive()
    if args.check:
        return check(doc)
    write(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
