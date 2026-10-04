#!/usr/bin/env python3
"""Generate the town's lot-line fences — the enclosure layer's fourth, fifth and sixth records.

WHAT THIS IS. The owner, 2026-08-18, verbatim: *"i think there should be more fences."*
Image 12 of `data/sources/assets/owner_brief_2026_08_18/README.md` — Chicago circa 1833,
looking east — is why: **split-rail and board fences line the roads and enclose every
property in view**. An enclosure is the NORM of an 1830s town lot, not the exception, and
until this record the whole town held four of them: a wagon yard, a pound, a hotel's rear
yard and fifteen garden plots (T-0050/51/52).

WHAT IT BUILDS. The **whole lot** of every improved platted lot with room for a yard: a
fence up one side lot line from the street corner, along the rear lot line at the alley,
and down the other side lot line to the street. The street side is left open where a
building on the lot fronts it (stands in the lot's front half), so the house or the store
is seen from the road — which is what the Sauganash's yard record already says of its own
missing side, *"the two buildings that stand on this lot close the fourth side
themselves"*; a lot whose buildings all stand at the back is fenced on its street line too,
with a street gateway. UNTIL T-2102 the side fences ran only along the rear 40 ft (the
"head of the yard" below), which left a quarter of each side line fenced and the rest of
the lot open to both neighbours and the street. The owner, 2026-10-04: *"the half built
fence seems odd if there is no facing of a building on that street"* — and the town's
1833 code let ringed hogs run at large, so a fence open on three sides kept nothing out
(docs/LIBERTIES.md L378). The CONTINUOUS STREET-LINING runs at the road edge
are deliberately NOT here: they are T-0069's half of the owner's sentence, and a fence
built twice on one line is worse than a fence built once.

THE RULE, and every clause of it is doing work. A platted lot gets a yard fence iff

  1. it is a lot in `data/traces/vectors/thompson_lots.json` — so the line the fence
     stands on is the committed plat grid and not a shape invented here. A fence follows
     a LOT LINE; this project has lot lines and does not have to guess at them;
  2. it is IMPROVED — at least one committed building centre stands in it. An empty lot
     in 1835 Chicago was prairie somebody held on paper, and fencing it would be a claim
     about improvement nobody made;
  3. there is room behind those buildings for a yard `MIN_DEPTH_M` deep and `MIN_WIDTH_M`
     wide, between the rearmost building's back face and the lot's own rear line;
  4. and the line is not already fenced. A segment running within `CLEAR_OF_EXISTING_M` of
     any run already on the enclosure layer is dropped, because two fences a metre apart is
     not a town, it is a bug you can see from the street.

EVERY CLAUSE ABOVE IS AN ARGUMENT ABOUT 1835 AND NONE OF THEM IS A BUDGET. An earlier cut of
this record held four blocks at the plat's western margin back for the renderer's draw-call
ceiling; the owner ruled on 2026-08-21 that the ceiling is the thing to move, not the town, so
the ceiling moved (`renderers/web/js/main.js` `BUDGET`) and the blocks came back.

THE TYPE FOLLOWS THE TRAFFIC, which is the other half of what image 12 shows: board and
picket in the built core, split rail toward the edges and along the outlying lanes. The
project already grades its streets — `data/streets/1835.json` classes every one of them
`principal`, `ordinary` or `light` — so the classification is READ rather than drawn on a
map by hand:

  * a block **all four of whose bounding streets are `principal` or `ordinary`** is in the
    built core. On it, a lot carrying a trade or business building takes a **board** fence
    (the yard behind a store is private working ground, which is exactly what the town's
    one attested board fence encloses — the Sauganash's), and a lot carrying only dwellings
    takes a **picket** (the Kinzie-view plate's treatment, the same one the dooryard
    gardens are drawn with);
  * a block that touches a street the record classes `light` — Washington, State, Clinton —
    is on the town's edge or up one of its outlying lanes, and every lot on it takes
    **post-and-rail**, the split-rail fence image 12 shows running out of the town.

Where two lots of different classes share a side line, ONE fence stands on it and the
heavier wins: board over picket over rail. A party fence is built to the higher requirement,
because the man who wants his yard private is the one who pays for it.

Every metre of every run below is DERIVED from the committed lot polygons and the committed
footprints. Nothing here is hand-placed, which is what makes several hundred fence runs
auditable rather than several hundred numbers somebody typed; `--check` re-derives all three
records byte for byte in `tools/check.sh`.

WHAT IS INVENTED is the whole scheme: that these lots were fenced at all, which fence each
one got, how deep the yard is, the rhythm of the posts and the stock they carry, and the
gateway on the alley. All of it is graded `reconstructed` and claimed in `docs/LIBERTIES.md`
L161, on the precedent of L129.

WHAT IS NOT DECLARED, deliberately: a ground treatment. `renderers/web/js/yards.js` will
draw the inside of any enclosure whose record states one, and these records state none —
a lot's yard held a woodpile, a privy, a stable, a patch of trodden mud and a patch of
grass, and this project does not know which was where on any lot in this town. The garden
plots say what they are and get their green; a yard fence whose interior is unstated leaves
the sward exactly as the flora layer plants it, which is the honest answer rather than a
default one.

    python3 tools/generate_lot_line_fences.py            write the records
    python3 tools/generate_lot_line_fences.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from generate_dooryard_pickets import footprint_world, poly_contains
import enclosure_owners
import generate_entrances

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
STREETS_PATH = DATA / "streets" / "1835.json"
SIDECARS = DATA / "sidecars" / "1835"
STRUCTURES = DATA / "structures"
ENCLOSURES = DATA / "enclosures"
STREET_EDGE = DATA / "frontage" / "town_street_edge.json"

# The records this writes, in the order the manifest lists them.
OUT = {
    "board": ENCLOSURES / "town_lot_line_boards.json",
    "picket": ENCLOSURES / "town_lot_line_pickets.json",
    "post_and_rail": ENCLOSURES / "town_lot_line_rails.json",
}
# The enclosure records this reads to keep out of their way. Everything already on the
# layer, whether hand-authored or generated.
STANDING = ["western_hotel_wagon_yard.json", "estray_pen.json",
            "town_dooryard_pickets.json", "sauganash_yard.json"]

# THE YARD, in feet and recorded converted, per data/datum.json's units rule.
REAR_CLEAR_M = 3.048       # 10 ft of open ground between a back wall and the yard fence
MAX_DEPTH_M = 12.192      # 40 ft — the yard the room test and the outbuildings read; no longer where fences stop (T-2102)
MIN_DEPTH_M = 4.572        # 15 ft — under this it is a gap between buildings, not a yard
MIN_WIDTH_M = 6.096        # 20 ft
GATE_WIDTH_M = 3.048       # 10 ft on the alley: a cart's way in, not a person's
CLEAR_OF_EXISTING_M = 2.0  # how close a new run may come to one already standing
PARALLEL_DEG = 20.0        # a standing fence within this of a line's bearing runs along it
BUILDING_CLEAR_M = 0.30    # a fence stops this far off a wall that stands on its line
MIN_PIECE_M = 2.5          # a piece shorter than this is not a fence, it is a stub

# The heavier fence wins a shared line; higher is heavier.
WEIGHT = {"post_and_rail": 0, "picket": 1, "board": 2}


# A lot carrying one of these is a lot with a trade on it, read off the structure record's
# own `function`. The words are the vocabulary `data/structures/` already uses.
BUSINESS_WORDS = (
    "store", "shop", "tavern", "hotel", "warehouse", "cooperage", "smith", "printing",
    "auction", "drug", "boarding", "packing", "slaughter", "brickyard", "soap",
    "manufactory", "office", "commission", "harbour", "court", "council", "church",
    "school", "agency", "livery", "bakery", "market",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def key(p) -> tuple:
    """A coordinate rounded to the centimetre, so two lots that share a line agree."""
    return (round(p[0], 2), round(p[1], 2))


def seg_len(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def point_seg_dist(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    if l2 <= 1e-12:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2
    t = min(max(t, 0.0), 1.0)
    return math.hypot(a[0] + dx * t - p[0], a[1] + dy * t - p[1])


def lot_edges(block, lot):
    """(front, rear, sides) as index pairs into the lot polygon.

    A lot is a quadrilateral with two END edges — the street frontage and the rear line —
    and two SIDE edges. The ends are the two SHORTEST edges: a lot in this grid is 80 ft on
    the street and deeper than it is wide everywhere. The street end is the one farther
    from the block's own centroid, because a lot's rear is the inside of its block. This is
    the same frame `tools/generate_dooryard_pickets.py` reads, taken here off the polygon's
    own corners rather than off an idealised rectangle, so two lots sharing a side line
    share it to the centimetre and the fence between them is built once.
    """
    poly = lot["polygon"]
    bnd = block["boundary_local_enu_m"]
    bx = sum(p[0] for p in bnd) / len(bnd)
    by = sum(p[1] for p in bnd) / len(bnd)
    idx = []
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        idx.append((seg_len(poly[i], poly[j]), i, j))
    ends = sorted(idx, key=lambda e: e[0])[:2]
    sides = [(i, j) for _, i, j in sorted(idx, key=lambda e: e[0])[2:]]

    def mid(e):
        return ((poly[e[1]][0] + poly[e[2]][0]) / 2, (poly[e[1]][1] + poly[e[2]][1]) / 2)

    front, rear = sorted(ends, key=lambda e: -math.hypot(mid(e)[0] - bx, mid(e)[1] - by))
    return (front[1], front[2]), (rear[1], rear[2]), sides


def bbox(pts):
    return (min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts))


def bbox_apart(u, v, clear: float) -> bool:
    """Two bounding boxes that cannot come within `clear` of each other. A cheap gate in
    front of the sampled tests below, which are otherwise every footprint against every
    lot line in the town."""
    return (u[0] - clear > v[2] or v[0] - clear > u[2]
            or u[1] - clear > v[3] or v[1] - clear > u[3])


def seg_polygon_gaps(a, b, poly, clear: float) -> list[tuple[float, float]]:
    """The parameter intervals of segment a→b that lie inside `poly` grown by `clear`.

    A wall standing on a lot line is not a hole in the fence, it IS the fence there, so the
    timber stops at it. Sampled rather than solved: the footprints are convex quadrilaterals
    a few metres across and the sample step is finer than any of them, which is what this
    has to be right about.
    """
    n = max(2, int(math.ceil(seg_len(a, b) / 0.25)))
    hits = []
    for i in range(n + 1):
        t = i / n
        p = lerp(a, b, t)
        inside = poly_contains(p, poly)
        if not inside and clear > 0:
            # Grown by `clear`: the nearest edge of the footprint is within reach.
            for k in range(len(poly)):
                if point_seg_dist(p, poly[k], poly[(k + 1) % len(poly)]) <= clear:
                    inside = True
                    break
        hits.append(inside)
    spans = []
    i = 0
    while i <= n:
        if hits[i]:
            j = i
            while j + 1 <= n and hits[j + 1]:
                j += 1
            spans.append((i / n, j / n))
            i = j + 1
        else:
            i += 1
    return spans


def subtract(spans: list[tuple[float, float]],
             cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = list(spans)
    for lo, hi in cuts:
        nxt = []
        for a, b in out:
            if hi <= a or lo >= b:
                nxt.append((a, b))
                continue
            if lo > a:
                nxt.append((a, lo))
            if hi < b:
                nxt.append((hi, b))
        out = nxt
    return out


def block_class(block, streets) -> str:
    """`core` or `edge`, read off the traffic class of the block's own bounding streets."""
    for sid in block["bounded_by"].values():
        if (streets.get(sid, {}).get("traffic") or "light") == "light":
            return "edge"
    return "core"


def function_of(sid: str) -> str:
    path = STRUCTURES / f"{sid}.json"
    if not path.exists():
        return ""
    fn = load(path).get("function")
    fn = fn.get("value") if isinstance(fn, dict) else fn
    return (fn or "").strip().lower()


def standing_runs() -> list[list[tuple[float, float]]]:
    out = []
    for name in STANDING:
        path = ENCLOSURES / name
        if not path.exists():
            continue
        for run in load(path).get("runs", []):
            pts = run.get("path_local_enu_m") or []
            if len(pts) >= 2:
                out.append([(p[0], p[1]) for p in pts])
    # T-2102 — AND THE STREET'S OWN FENCES. T-0069's street-lining fences stand on the
    # same lot lines this record now closes at the street, so a lot whose street line
    # that layer already fences takes nothing more there.
    if STREET_EDGE.exists():
        for run in load(STREET_EDGE).get("fences", []):
            pts = run.get("path_local_enu_m") or []
            if len(pts) >= 2:
                out.append([(p[0], p[1]) for p in pts])
    return out


def shadowed_spans(a, b, runs, clear: float) -> list[tuple[float, float]]:
    """The parameter intervals of a→b that run within `clear` of, and ALONG, a fence that
    already stands — two fences a metre apart on one line. A standing segment more than
    `PARALLEL_DEG` off a→b's bearing crosses or meets it and shadows nothing. Sampled at
    a quarter metre, the same step as `seg_polygon_gaps`."""
    L = seg_len(a, b)
    if L <= 1e-9:
        return []
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    cos_min = math.cos(math.radians(PARALLEL_DEG))
    segs = []
    for path in runs:
        for k in range(len(path) - 1):
            p, q = path[k], path[k + 1]
            m = seg_len(p, q)
            if m > 1e-9 and abs((q[0] - p[0]) * ux + (q[1] - p[1]) * uy) / m >= cos_min:
                segs.append((p, q))
    if not segs:
        return []
    n = max(2, int(math.ceil(L / 0.25)))
    hits = [any(point_seg_dist(lerp(a, b, i / n), p, q) <= clear for p, q in segs)
            for i in range(n + 1)]
    spans = []
    i = 0
    while i <= n:
        if hits[i]:
            j = i
            while j + 1 <= n and hits[j + 1]:
                j += 1
            spans.append((i / n, j / n))
            i = j + 1
        else:
            i += 1
    return spans


def survey():
    """Every improved platted lot, with its buildings, its class and its yard depth."""
    lots = load(LOTS_PATH)
    streets = {s["id"]: s for s in load(STREETS_PATH)["streets"]}
    sidecars = {}
    for path in sorted(SIDECARS.glob("*.json")):
        sc = load(path)
        pl = sc.get("placement") or {}
        if pl.get("local_e") is None:
            continue
        sidecars[path.stem] = sc

    occupancy: dict[tuple[str, int], list[str]] = {}
    for sid, sc in sidecars.items():
        pl = sc["placement"]
        for block in lots["blocks"]:
            for i, lot in enumerate(block["lots"]):
                if poly_contains((pl["local_e"], pl["local_n"]), lot["polygon"]):
                    occupancy.setdefault((block["id"], i), []).append(sid)

    out = []
    for block in lots["blocks"]:
        klass = block_class(block, streets)
        for i, lot in enumerate(block["lots"]):
            here = sorted(occupancy.get((block["id"], i), []))
            if not here:
                continue
            if klass == "edge":
                kind = "post_and_rail"
            elif any(any(w in function_of(s) for w in BUSINESS_WORDS) for s in here):
                kind = "board"
            else:
                kind = "picket"
            out.append({"block": block, "index": i, "lot": lot, "buildings": here,
                        "class": klass, "kind": kind,
                        "footprints": [footprint_world(sidecars[s]) for s in here]})
    return out, sidecars


def yard_for(entry):
    """The lot's yard as parameter ranges on its own side edges, or (None, why)."""
    lot = entry["lot"]
    poly = lot["polygon"]
    (fa, fb), (ra, rb), sides = lot_edges(entry["block"], lot)
    front_mid = ((poly[fa][0] + poly[fb][0]) / 2, (poly[fa][1] + poly[fb][1]) / 2)
    rear_mid = ((poly[ra][0] + poly[rb][0]) / 2, (poly[ra][1] + poly[rb][1]) / 2)
    depth = seg_len(front_mid, rear_mid)
    vx, vy = (rear_mid[0] - front_mid[0]) / depth, (rear_mid[1] - front_mid[1]) / depth

    def v_of(p):
        return (p[0] - front_mid[0]) * vx + (p[1] - front_mid[1]) * vy

    # THE YARD BEGINS BEHIND THE STREET BUILDING, not behind the last shed. A town lot's
    # outbuildings — the privy, the woodshed, the stable — stand IN the yard, which is what
    # the yard is for; measuring from the deepest of them would refuse a fence to exactly
    # the lots that most obviously had one. So the head of the yard is the back face of the
    # building nearest the street, and anything deeper stands inside the enclosure.
    front_building = None
    for fp in entry["footprints"]:
        if len(fp) < 3:
            continue
        near = min(v_of(p) for p in fp)
        if front_building is None or near < front_building[0]:
            front_building = (near, max(v_of(p) for p in fp))
    back = front_building[1] if front_building else 0.0
    v_start = max(back + REAR_CLEAR_M, depth - MAX_DEPTH_M)
    v_end = depth
    if v_end - v_start < MIN_DEPTH_M:
        over = back - depth
        why = (f"the committed buildings reach {over:.2f} m past the lot's own rear line"
               if over > 0 else
               f"only {max(v_end - v_start, 0):.2f} m of lot is left behind them")
        return None, why
    width = seg_len(poly[ra], poly[rb])
    if width < MIN_WIDTH_M:
        return None, f"the lot is only {width:.2f} m wide between its side lines"
    # T-2102 — DOES A BUILDING FRONT THE STREET? One that stands in the front half of the
    # lot faces the street it is platted on, and its street face is left open so the house
    # or the store is seen from the road. A lot whose buildings all stand in its back half
    # turns only a privy or a shed to the street, and its street line is fenced like the
    # other three.
    fronts = front_building is not None and front_building[0] < depth / 2
    return {"sides": sides, "rear": (ra, rb), "front": (fa, fb), "fronts_street": fronts,
            "v_start": v_start, "depth": depth, "v_of": v_of, "poly": poly,
            "width": width}, None


def build(entries, sidecars):
    all_footprints = [footprint_world(sc) for sc in sidecars.values()]
    all_footprints = [(fp, bbox(fp)) for fp in all_footprints if len(fp) >= 3]
    # T-1984 — NO FENCE ACROSS A DOOR. A stable's or a house's door that faces a lot
    # line had the line's fence run straight across its doorway, a step out from the
    # sill. The doorway (`generate_entrances.doorway_zones`: the door's width and a hand
    # either side, two paces out) is cut out of a line exactly as a footprint standing
    # on it is, so the fence stops either side of the way out.
    doorways = [(ring, bbox(ring)) for _eid, ring in generate_entrances.doorway_zones()]
    standing = [(path, bbox(path)) for path in standing_runs()]

    # A side line proposed by two neighbours is ONE fence: keyed on the pair of committed
    # corners, so the two proposals meet to the centimetre or they are different lines.
    # THE GROUND, indexed by lot id: the polygon and the committed buildings standing
    # in it, which is everything tools/enclosure_owners.py needs to say whose fence
    # this is.
    ground: dict[str, tuple[list, list[str]]] = {}
    sides: dict[tuple, dict] = {}
    rears: list[dict] = []
    fronts: list[dict] = []
    refused: list[str] = []
    fenced: dict[str, list[str]] = {"board": [], "picket": [], "post_and_rail": []}

    for entry in sorted(entries, key=lambda e: (e["block"]["id"], e["index"])):
        yard, why = yard_for(entry)
        lot_id = f"{entry['block']['id']}_lot{entry['index']}"
        ground[lot_id] = (entry["lot"]["polygon"], entry["buildings"])
        if yard is None:
            refused.append(f"{lot_id} ({', '.join(entry['buildings'])}): {why}")
            continue
        poly = yard["poly"]
        # The side lines, street corner to rear corner. The segment is
        # keyed and ORIENTED on its own committed corners, so the two neighbours that claim
        # it compute the same interval on the same line and the fence is built once.
        for (i, j) in yard["sides"]:
            k = tuple(sorted([key(poly[i]), key(poly[j])]))
            a, b = k
            length = seg_len(a, b)
            # T-2102 — THE WHOLE SIDE LINE, street corner to rear corner. Until then the
            # fence ran only along the rear 40 ft of the lot (the head of the yard), which
            # left the ground between the house and the yard open to both neighbours and
            # to the street: a fence on three sides of a quarter of a lot, which keeps
            # nothing out in a town whose ordinance let ringed hogs run at large. A wall
            # standing on the line still stops it (`pieces` below), so a house built to
            # its side line is the fence there.
            lo, hi = 0.0, 1.0
            rec = sides.setdefault(k, {"a": a, "b": b, "lo": 1.0, "hi": 0.0,
                                       "kind": "post_and_rail", "lots": []})
            rec["lo"] = min(rec["lo"], lo)
            rec["hi"] = max(rec["hi"], hi)
            if WEIGHT[entry["kind"]] > WEIGHT[rec["kind"]]:
                rec["kind"] = entry["kind"]
            rec["lots"].append(lot_id)
        # The rear line, the whole width of the lot, with one gateway on the alley.
        ra, rb = yard["rear"]
        rears.append({"a": poly[ra], "b": poly[rb], "kind": entry["kind"],
                      "lot": lot_id, "block": entry["block"]["id"], "index": entry["index"],
                      "buildings": entry["buildings"], "depth": yard["depth"],
                      "yard": round(yard["depth"] - yard["v_start"], 2),
                      "width": round(yard["width"], 2), "class": entry["class"]})
        fenced[entry["kind"]].append(lot_id)
        # The street line, only where no building on the lot fronts that street.
        if not yard["fronts_street"]:
            fa, fb = yard["front"]
            fronts.append({"a": poly[fa], "b": poly[fb], "kind": entry["kind"],
                           "lot": lot_id, "buildings": entry["buildings"],
                           "width": round(seg_len(poly[fa], poly[fb]), 2)})

    def pieces(a, b, spans):
        """Turn parameter spans into world segments, trimmed of the buildings that stand
        on the line and of any fence that already stands beside it."""
        line = bbox([a, b])
        cuts = []
        for fp, box in all_footprints:
            if bbox_apart(line, box, BUILDING_CLEAR_M):
                continue
            cuts += seg_polygon_gaps(a, b, fp, BUILDING_CLEAR_M)
        for ring, box in doorways:
            if bbox_apart(line, box, 0.30):
                continue
            cuts += seg_polygon_gaps(a, b, ring, 0.30)
        # T-2102 — A FENCE ALREADY STANDING BESIDE THE LINE TAKES ONLY THE SPAN IT
        # SHADOWS. It used to take the whole piece, which was harmless while yard fences
        # stood only at the alley; on a side line that runs the lot's whole depth it
        # would hand a whole party fence to a garden plot that shadows two metres of it,
        # and put the half fence straight back. Only a fence running ALONG the line
        # shadows it: one meeting it square is a junction, not a second fence.
        near = [path for path, box in standing
                if not bbox_apart(line, box, CLEAR_OF_EXISTING_M)]
        if near:
            cuts += shadowed_spans(a, b, near, CLEAR_OF_EXISTING_M)
        out = []
        for lo, hi in subtract(spans, cuts):
            p, q = lerp(a, b, lo), lerp(a, b, hi)
            if seg_len(p, q) < MIN_PIECE_M:
                continue
            out.append((p, q))
        return out

    runs = {"board": [], "picket": [], "post_and_rail": []}
    openings = {"board": [], "picket": [], "post_and_rail": []}
    links = enclosure_owners.household_links()

    def belongs(lot_ids, path):
        return enclosure_owners.owners_for(
            [(lid, ground[lid][0], ground[lid][1]) for lid in sorted(set(lot_ids))],
            path, links)

    def side_of(lot_ids, a, b) -> str:
        """WHICH SIDE of the first-named lot this line is on — `e`, `w`, `n` or `s`.

        A run id has to name the thing it identifies, and `side_<lot>` named the LOT: a
        lot has two side lines, so the two of them came out with one id between them
        (T-0828). The discriminator is the geometry that already distinguishes them —
        the side line's midpoint lies to one side of the lot's centre, and the two sides
        of a lot lie on opposite sides of it, so the token always tells them apart.

        The lot it is measured from is the FIRST one named in the id, which is the id's
        own sorted order, so a party line between two lots reads as the side of the
        earlier-named one. That is a statement about a real line and not a tie-break:
        the east side of lot 1 IS the west side of lot 2, and the id names both lots.
        """
        poly = ground[sorted(set(lot_ids))[0]][0]
        cx = sum(v[0] for v in poly) / len(poly)
        cy = sum(v[1] for v in poly) / len(poly)
        dx, dy = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
        if abs(dx) >= abs(dy):
            return "e" if dx >= 0 else "w"
        return "n" if dy >= 0 else "s"

    for k in sorted(sides.keys()):
        rec = sides[k]
        # The side token comes off the WHOLE line, not the piece, so trimming a run around
        # a building that stands on it cannot rename the side the run is on.
        side = side_of(rec["lots"], rec["a"], rec["b"])
        for n, (p, q) in enumerate(pieces(rec["a"], rec["b"], [(rec["lo"], rec["hi"])])):
            runs[rec["kind"]].append({
                "id": f"side_{'_'.join(sorted(set(rec['lots'])))}_{side}"
                      + (f"_{n}" if n else ""),
                "path_local_enu_m": [[round(p[0], 2), round(p[1], 2)],
                                     [round(q[0], 2), round(q[1], 2)]],
                "belongs_to": belongs(rec["lots"], [p, q]),
                "note": (
                    f"A SIDE LOT LINE — the "
                    f"{ {'e': 'east', 'w': 'west', 'n': 'north', 's': 'south'}[side] } "
                    f"side of {sorted(set(rec['lots']))[0]} — and the fence on it is "
                    f"built ONCE: {' and '.join(sorted(set(rec['lots'])))} "
                    f"{'both claim' if len(set(rec['lots'])) > 1 else 'claims'} this line "
                    f"and a party fence between two yards is one fence. THE LINE IS THE "
                    f"COMMITTED PLAT'S, corner to corner out of "
                    f"data/traces/vectors/thompson_lots.json; what is derived is only "
                    f"WHERE ALONG IT the timber runs — the whole line, street corner to rear "
                    f"corner, since T-2102 closed the lot (L378) — and it stops "
                    f"{BUILDING_CLEAR_M:.2f} m short of any committed footprint standing "
                    f"on the line, because a wall on a lot line is not a hole in the fence, "
                    f"it IS the fence there."
                ),
            })

    for rec in rears:
        a, b = rec["a"], rec["b"]
        got = pieces(a, b, [(0.0, 1.0)])
        for n, (p, q) in enumerate(got):
            runs[rec["kind"]].append({
                "id": f"rear_{rec['lot']}" + (f"_{n}" if n else ""),
                "path_local_enu_m": [[round(p[0], 2), round(p[1], 2)],
                                     [round(q[0], 2), round(q[1], 2)]],
                "belongs_to": belongs([rec["lot"]], [p, q]),
                "note": (
                    f"THE REAR LOT LINE of {rec['lot']}, which in this grid is the ALLEY "
                    f"line: the plat drives a service alley through the middle of every "
                    f"block and the back of a lot opens onto it. The lot is improved — it "
                    f"holds {', '.join(rec['buildings'])} — and the yard behind those "
                    f"buildings is {rec['yard']:.2f} m deep by {rec['width']:.2f} m wide, "
                    f"which is the room the committed footprints leave inside the "
                    f"committed lot. EVERY COORDINATE IS THE PLAT'S; the invention is that "
                    f"the line carries a fence at all, and which one."
                ),
            })
        if got:
            mid = lerp(a, b, 0.5)
            # The gateway is centred in the rear line unless the middle of it is one of
            # the pieces a building took out, in which case it goes in the middle of the
            # longest piece that survived. A yard with no way in from the alley is a yard
            # nothing was ever carried into.
            best = max(got, key=lambda s: seg_len(*s))
            if not any(point_seg_dist(mid, p, q) < 0.05 for p, q in got):
                mid = lerp(best[0], best[1], 0.5)
            if seg_len(*best) > GATE_WIDTH_M + 2 * MIN_PIECE_M:
                openings[rec["kind"]].append({
                    "id": f"rear_{rec['lot']}_gate",
                    "on": "alley",
                    "at_local_enu_m": [round(mid[0], 2), round(mid[1], 2)],
                    "width_m": GATE_WIDTH_M,
                    "confidence": "reconstructed",
                    "note": (
                        "INVENTED, like every gateway on this layer. A yard a cart could "
                        "not enter is not a yard, and the alley is the only side of this "
                        "lot a cart could come at, so the gap is centred in the alley line; "
                        "10 ft is a team and a wagon, not a person with a basket. NO GATE "
                        "LEAF IS DRAWN — the fence simply stops, the way it does at the "
                        "wagon yard, the pound and the garden plots, because a hung gate "
                        "would be an invention on top of an invention."
                    ),
                })

    for rec in fronts:
        a, b = rec["a"], rec["b"]
        got = pieces(a, b, [(0.0, 1.0)])
        for n, (p, q) in enumerate(got):
            runs[rec["kind"]].append({
                "id": f"front_{rec['lot']}" + (f"_{n}" if n else ""),
                "path_local_enu_m": [[round(p[0], 2), round(p[1], 2)],
                                     [round(q[0], 2), round(q[1], 2)]],
                "belongs_to": belongs([rec["lot"]], [p, q]),
                "note": (
                    f"THE STREET LOT LINE of {rec['lot']} (T-2102), closing the lot. Its "
                    f"buildings — {', '.join(rec['buildings'])} — all stand in the back "
                    f"half of the lot, so none of them fronts the street and the street "
                    f"line is fenced like the other three; a lot with a house or a store "
                    f"in its front half leaves this line open so the building is seen "
                    f"from the road. EVERY COORDINATE IS THE PLAT'S; the invention is that "
                    f"the line carries a fence at all, and which one."
                ),
            })
        if got:
            mid = lerp(a, b, 0.5)
            best = max(got, key=lambda s: seg_len(*s))
            if not any(point_seg_dist(mid, p, q) < 0.05 for p, q in got):
                mid = lerp(best[0], best[1], 0.5)
            if seg_len(*best) > GATE_WIDTH_M + 2 * MIN_PIECE_M:
                openings[rec["kind"]].append({
                    "id": f"front_{rec['lot']}_gate",
                    "on": "street",
                    "at_local_enu_m": [round(mid[0], 2), round(mid[1], 2)],
                    "width_m": GATE_WIDTH_M,
                    "confidence": "reconstructed",
                    "note": (
                        "INVENTED, like every gateway on this layer. A lot closed on its "
                        "street line still has to be got into from the street, so the gap "
                        "is centred in that line, 10 ft for a cart. NO GATE LEAF IS DRAWN."
                    ),
                })

    # RUNS ARE LISTED IN SPATIAL ORDER — north to south in bands, west to east inside them
    # — so the file reads the way the town is laid out and a diff on it is legible block by
    # block. It is NOT what the renderer relies on: `renderers/web/js/enclosures.js` packs
    # neighbouring runs into one culling-sized mesh and re-sorts the whole LAYER to do it,
    # because these three records interleave lot by lot down every block and no one of them
    # can put itself in order with respect to the other two.
    def cell(run):
        p = run["path_local_enu_m"]
        e = sum(q[0] for q in p) / len(p)
        n = sum(q[1] for q in p) / len(p)
        return (math.floor(-n / 30.0), math.floor(e / 30.0), -n, e, run["id"])

    for kind in runs:
        runs[kind].sort(key=cell)
    return runs, openings, refused, fenced


# ---------------------------------------------------------------------------
# the records
# ---------------------------------------------------------------------------

FORM_NOTES = {
    "board": {
        "why": (
            "INVENTED. A BOARD FENCE IS A WALL, and that is the claim: the yard behind a "
            "store, a warehouse or a tavern was working ground with stock in it, and the "
            "one board fence this town attests encloses exactly that — the Sauganash's "
            "rear yard, which three retrospective views agree on "
            "(data/enclosures/sauganash_yard.json). Image 12 of the 2026-08-18 owner brief "
            "shows board fencing in the built-up part of its view and rails at the edges. "
            "Nothing states that any of THESE lots was fenced, in board or in anything else."
        ),
        "height": 1.68,
        "height_why": (
            "INVENTED. 1.68 m is 5 ft 6 in, recorded converted, and it is read between the "
            "two board fences already in this dataset rather than chosen: the Sauganash's "
            "yard fence is 1.83 m — 6 ft, a fence nobody sees over — and the Western "
            "Hotel's rail yard is 1.37 m. A trade yard on a town lot wants to be private "
            "from the alley without being the hotel's stockade. Nothing attests a height."
        ),
        "courses": 3,
        "spacing": 2.44,
        "post": 0.12,
        "stock_w": 0.254,
        "stock_gap": 0.006,
    },
    "picket": {
        "why": (
            "INVENTED, and it is the one fence type on this record with a picture behind "
            "it. The Kinzie-view plate shows PICKETS — close-set vertical pales — around "
            "the garden plots of a house on the north bank, and "
            "data/enclosures/town_dooryard_pickets.json already draws the town's gardens "
            "with that treatment. A house lot's yard takes the same fence for the same "
            "reason a garden does: it keeps poultry and a rooting hog off ground somebody "
            "is keeping. The plate is tier 5, retrospective, and of a house this scene "
            "excludes, so it bounds a treatment and attests nothing about these lots."
        ),
        "height": 1.22,
        "height_why": (
            "INVENTED. 1.22 m is 4 ft, the same as the garden pickets and for the same "
            "reason: four feet is the least that turns poultry and a hog off kept ground, "
            "and a house lot's yard fence has no heavier work than that. Nothing attests a "
            "height, and a Chicago or Cook County lawful-fence ordinance of the 1830s would "
            "replace this number outright."
        ),
        "courses": 2,
        "spacing": 2.44,
        "post": 0.10,
        "stock_w": 0.089,
        "stock_gap": 0.089,
    },
    "post_and_rail": {
        "why": (
            "INVENTED. A SPLIT-RAIL FENCE IS THE CHEAP ONE and it is what image 12 of the "
            "2026-08-18 owner brief shows running out of the town — open horizontal rails "
            "between posts, turning stock and hiding nothing. On the edge blocks and the "
            "outlying lanes that is the right fence twice over: the timber was riven rather "
            "than sawn, and there was nothing behind it a man needed screened. The town's "
            "other two rail fences — the Western Hotel's wagon yard and the estray pen — "
            "are the same construction. Nothing states that any of these lots was fenced."
        ),
        "height": 1.37,
        "height_why": (
            "INVENTED. 1.37 m is 4 ft 6 in, the Western Hotel's yard fence exactly, because "
            "it is the same fence doing the same job: turning a beast off ground somebody "
            "is holding. Nothing attests a height."
        ),
        "courses": 3,
        "spacing": 3.048,
        "post": 0.14,
        "stock_w": None,
        "stock_gap": None,
    },
}

TITLE = {
    "board": ("town_lot_line_boards", "The built core's board yard fences",
              ["the board fences", "the trade yards"]),
    "picket": ("town_lot_line_pickets", "The built core's picketed house yards",
               ["the house-lot pickets", "the yard pales"]),
    "post_and_rail": ("town_lot_line_rails", "The edge blocks' split-rail lot fences",
                      ["the rail fences", "the split-rail lot lines"]),
}


def form_block(kind: str) -> dict:
    f = FORM_NOTES[kind]
    out = {
        "fence_type": {"value": kind, "confidence": "reconstructed", "note": f["why"]},
        "height_m": {"value": f["height"], "confidence": "reconstructed",
                     "note": f["height_why"]},
        "rail_courses": {
            "value": f["courses"], "confidence": "reconstructed",
            "note": (
                "INVENTED. On a rail fence the courses ARE the fence and three is what "
                "turns stock at this height; on a paled or boarded fence they are stringers "
                "behind the stock and only hold it in line. Nothing attests a count."
            ),
        },
        "post_spacing_m": {
            "value": f["spacing"], "confidence": "reconstructed",
            "note": (
                f"INVENTED. {f['spacing']:.3f} m is " + (
                    "10 ft, the span a riven rail of the period is cut to carry"
                    if f["spacing"] > 2.5 else
                    "8 ft, the same bay as the pound and the garden plots, which is the "
                    "span a sawn rail of the period is cut to carry"
                ) + ". Nothing attests a bay."
            ),
        },
        "post_size_m": {
            "value": f["post"], "confidence": "reconstructed",
            "note": (
                f"INVENTED. A {f['post']:.2f} m post is a "
                f"{round(f['post'] / 0.0254)}-inch stick, sized to what it carries: this "
                f"layer runs from the garden pickets' 4-inch post to the wagon yard's "
                f"5½-inch one, and nothing attests any of them."
            ),
        },
    }
    if f["stock_w"] is not None:
        w = "board" if kind == "board" else "picket"
        out[f"{w}_width_m"] = {
            "value": f["stock_w"], "confidence": "reconstructed",
            "note": (
                f"INVENTED. {f['stock_w']:.3f} m is " + (
                    "a 10-inch board off the same pile of stuff the town is sided from"
                    if kind == "board" else
                    "3½ in — a riven or sawn pale, the width the garden plots already "
                    "use"
                ) + ". Nothing attests the stock, its width, or that these fences were "
                "sawn timber at all."
            ),
        }
        out[f"{w}_gap_m"] = {
            "value": f["stock_gap"], "confidence": "reconstructed",
            "note": (
                "INVENTED, and it is the number that decides whether a visitor is looking "
                "at a fence or at a wall. " + (
                    "6 mm is boards butted to their neighbours with nothing but the "
                    "shrinkage gap between them, which is what makes a board fence a wall"
                    if kind == "board" else
                    "A pale-wide gap is the rhythm the Kinzie-view plate reads as at the "
                    "scale it is drawn, and it is what lets a visitor see the yard through "
                    "the fence"
                ) + ". Nothing attests it."
            ),
        }
    return out


def record(kind: str, runs, openings, refused, fenced, counts, owners, prose) -> dict:
    rid, name, aka = TITLE[kind]
    where = ("the built core — every block all four of whose bounding streets the project "
             "classes `principal` or `ordinary`"
             if kind != "post_and_rail" else
             "the edge blocks and the outlying lanes — every block that touches a street "
             "the project classes `light`")
    return {
        "id": rid,
        "name": name,
        "aka": aka,
        "kind": "lot_yard",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_lot_line_fences.py",
        "generated_from": [
            "data/traces/vectors/thompson_lots.json",
            "data/streets/1835.json",
            "data/sidecars/1835/*.json",
            "data/structures/*.json",
            "data/enclosures/*.json",
            "data/frontage/town_street_edge.json",
        ],
        "belongs_to": [],
        "belongs_to_rule": enclosure_owners.rule_block(owners, prose),
        "documented_range": {
            "from": "1835-01-01",
            "to": "1835-12-31",
            "confidence": "reconstructed",
            "sources": [],
            "note": (
                "THE RANGE IS THE SCENE YEAR AND NOTHING MORE. No source dates a lot fence "
                "in this town, because no source names one. The range is a housekeeping "
                "bound so that this record answers the same date gate every other record "
                "answers, and it should not be read as evidence that these fences went up "
                "in 1835 or came down in 1836."
            ),
        },
        "existence": {
            "value": True,
            "confidence": "reconstructed",
            "sources": [],
            "note": (
                "NOTHING ATTESTS A FENCE ON ANY OF THESE LOTS, and this record does not "
                "claim one. What is attested is a NORM, and it arrives as a picture: image "
                "12 of data/sources/assets/owner_brief_2026_08_18/README.md — Chicago circa "
                "1833, looking east — shows split-rail and board fences lining the roads and "
                "enclosing every property in the view, and the Kinzie-view plate shows "
                "picket-fenced plots on the north bank. Both are tier-5 pictorial and "
                "retrospective: they may drive treatment, materials and setting and they may "
                "never drive a coordinate, which is exactly how they are used here. The "
                "plates say what an 1830s town lot's fence looked like and that a town lot "
                "generally had one; the RULE in tools/generate_lot_line_fences.py says which "
                "lots get which, and every metre of every line below is the committed plat's. "
                "SOURCES IS DELIBERATELY EMPTY AND THAT IS THE FINDING: this project holds "
                "no source record for either plate — the owner brief reaches the repository "
                "as an owner-supplied reference set with a README, and holding those plates "
                "as sources is filed as its own ticket (T-0075)."
            ),
        },
        "runs": runs,
        "openings": openings,
        "form": form_block(kind),
        "ground": {
            "value": "not stated",
            "confidence": "reconstructed",
            "geometry": "absent",
            "note": (
                "NOT DRAWN, AND SAYING SO IS THE POINT — which is the opposite of the call "
                "T-0067 made for the garden plots, and deliberately so. "
                "renderers/web/js/yards.js draws the inside of any enclosure whose record "
                "states a `treatment`, and this record states none. A town lot's yard held a "
                "woodpile, a privy, a stable, a patch of trodden mud and a patch of grass, "
                "in an arrangement that changed with the season and the household, and this "
                "project does not know which was where on any lot in this town. The garden "
                "plots can say what they are because a garden is one thing; a yard is not, "
                "so the sward stays exactly as the flora layer plants it and the fence "
                "claims only the line it stands on. What would change it: any tax, "
                "insurance or sale description of a Chicago town lot naming what stood in "
                "its yard."
            ),
        },
        "coverage": {
            "where": where,
            "lots_fenced": len(fenced[kind]),
            "lots": sorted(fenced[kind]),
            "runs": len(runs),
            "note": (
                f"{counts['fenced']} of the {counts['improved']} improved platted lots in "
                f"this town carry a yard fence after this record and its two companions — "
                f"every one the rule reaches, on every block of the plat. The other "
                f"{counts['refused']} are refused for want of room behind their buildings "
                f"and each is named in `refused` below with the measurement that refused it. "
                f"THE REMAINDER OF THE OWNER'S ASK IS NOT HERE AND IS NOT PRETENDED TO BE: "
                f"the continuous street-lining fences at the road edge are T-0069's half of "
                f"it, and ground outside the {counts['blocks_with_lots']} platted blocks "
                f"that carry lot lines — the reservation, Kinzie's Addition, the West "
                f"Division blocks whose own sheet prints no dimension to divide them by, "
                f"the country places outside the plat — has no committed lot geometry to "
                f"derive a line from at all."
            ),
        },
        "refused": refused,
        "research_note": (
            "THE EVIDENCE HERE IS A NORM AND NOT A LOCATION, which is why this record is "
            "generated from a rule instead of authored lot by lot. Read the rule in "
            "tools/generate_lot_line_fences.py — it is the answer to 'why this lot and why "
            "this fence', and it is enforced on every commit, because tools/check.sh "
            "re-derives this file byte for byte. In short: a platted lot, improved by at "
            "least one committed building, with room behind those buildings for a yard, on "
            "a line no fence already stands on; and the TYPE follows the traffic class the "
            "project already grades its own streets with — board and picket where the "
            "town's made streets meet, split rail where a light-worn lane runs. WHAT WOULD "
            "CHANGE IT: a Chicago or Cook County fence ordinance of the 1830s, which would "
            "settle the heights and probably the rhythms; any tax, insurance or sale "
            "description of a town lot naming a fence; and the North Division street "
            "control docs/ROADMAP.md S9 still records as owed, which is what keeps two "
            "thirds of the plat off this grid."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    args = ap.parse_args()
    entries, sidecars = survey()
    runs, openings, refused, fenced = build(entries, sidecars)
    # Counted rather than written down, since T-1455: the note below used to say "the 19
    # platted blocks" and the number was a literal, so the day the grid grew a block the
    # prose went quietly wrong. It is the blocks with lot LINES in them that a per-lot
    # rule can reach, which is not the same as the blocks on the grid.
    counts = {
        "improved": len(entries),
        "refused": len(refused),
        "fenced": sum(len(v) for v in fenced.values()),
        "blocks_with_lots": sum(1 for b in json.loads(
            LOTS_PATH.read_text(encoding="utf-8"))["blocks"] if b.get("lots")),
    }
    failed = 0
    total_runs = 0
    # The ownership counts are stated the same on all three records, because a visitor
    # reading one of them is asking about the town's fences and not about this file's
    # third of them.
    owners = enclosure_owners.tally([{"runs": runs[k]} for k in sorted(runs)])
    prose = enclosure_owners.prose_report(
        sid for k in sorted(runs) for run in runs[k]
        for entry in run["belongs_to"] for sid in entry["structures"])
    for kind, path in OUT.items():
        text = json.dumps(record(kind, runs[kind], openings[kind], refused, fenced, counts,
                                 owners, prose),
                          indent=2, ensure_ascii=False) + "\n"
        total_runs += len(runs[kind])
        if args.check:
            if not path.exists():
                print(f"LOT-LINE FENCE DRIFT\n  - {path.relative_to(ROOT)} is missing")
                failed = 1
            elif path.read_text(encoding="utf-8") != text:
                print(f"LOT-LINE FENCE DRIFT\n  - {path.relative_to(ROOT)} has drifted from "
                      f"the rule in tools/generate_lot_line_fences.py")
                failed = 1
        else:
            path.write_text(text, encoding="utf-8")
    verb = "verified" if args.check else "wrote"
    if failed:
        return 1
    print(f"{verb} {counts['fenced']} fenced lot(s) of {counts['improved']} improved "
          f"({len(fenced['board'])} board, {len(fenced['picket'])} picket, "
          f"{len(fenced['post_and_rail'])} split rail) in {total_runs} run(s); "
          f"{counts['refused']} lot(s) refused for want of room")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
