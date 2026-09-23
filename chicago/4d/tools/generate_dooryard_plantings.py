#!/usr/bin/env python3
"""Generate the town's dooryard plantings — kept trees and bushes around the houses.

WHAT THIS IS. Ticket T-0074, from the owner's 2026-08-18 brief: *"there should be...
more trees and greenery around the houses like people would have put or kept some
trees and bushes around their houses."* The reference is image 12 of
`data/sources/assets/owner_brief_2026_08_18/README.md` — the circa-1833 view looking
east, where trees and bushes stand close around the houses, kept deliberately —
and the committed Kinzie plate agrees (its poplar row was planted, not wild). Today
the woody layer is prairie-driven: distribution follows the land, so houses stand on
bare grass. This tool gives the town's houses their dooryard stems, the way
T-0052 gave its house lots their garden pickets: by a RULE, not a list, so the
record can say of every stem on what basis that particular house got it.

THE RULE. A committed structure gets dooryard stems iff

  1. its archetype is a dwelling's (`frame_dwelling` / `log_dwelling`) and its
     function reads as a dwelling — the same two clauses T-0052 uses, for the same
     reason: a tavern yard or a store frontage is a different ground with different
     uses, and the one tavern yard with evidence behind it (the Sauganash's,
     T-0091) is already carried by its own hand-authored record;
  2. a deterministic deal seeded on the structure id gives it 0-2 kept trees and
     0-2 currant bushes — dealt, because no source counts any house's trees, and
     seeded, because a re-run must re-derive the same town (`--check` diffs it);
  3. every stem stands where the renderer's own refusals allow: clear of every
     committed footprint by more than trees.js's CLEAR_MARGIN, off every street's
     travelled track by more than streets.js's shoulder, above the dry floor,
     outside every committed fence line, and clear of its neighbours.

WHAT THE SPECIES ARE, and why nothing here is new ecology. Every stem names a
species `data/flora/zones/z10_settled_town.json` already records: the settled
town's relict survivors (American elm, eastern cottonwood — "Survivor elm in a
part-cleared block") for the trees, and its dooryard currants (`ribes_spp`, whose
own record note says currants inside the town box are inferred from the Fort
Dearborn garden and Dr. Harmon's nursery) for the bushes. WHETHER A GIVEN TREE WAS
KEPT OR PLANTED IS NOT CLAIMED, because it is not knowable: the ticket's own brief
has settlers doing both, the timber belt's documented east end (Wells Street in
the South Division, the sandy hills exception in the North) means most house lots
stood on ground with nothing to keep, and a transplanted elm or cottonwood — the
period's two quick dooryard shades — is the same species either way. Tree heights
sit in the LOW third of each species' recorded band: T-0091's cut-back argument
for a kept tree, and a young transplant for a planted one, land in the same third.

WHAT IS INVENTED is every coordinate, every count and every height — graded
`reconstructed` and claimed in `docs/LIBERTIES.md` L151. The Lombardy poplars the
ticket also names are NOT dealt: no committed flora zone record describes the
species, and a planting record may not invent a tree the zone records do not
carry (trees.js refuses the stem). Holding the poplar as a species is its own
ticket.

    python3 tools/generate_dooryard_plantings.py            write the record
    python3 tools/generate_dooryard_plantings.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heightfield import Heightfield  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SIDECARS = DATA / "sidecars" / "1835"
STRUCTURES = DATA / "structures"
STREETS = DATA / "streets" / "1835.json"
ENCLOSURES = DATA / "enclosures"
FRONTAGE = DATA / "frontage"
ZONE = DATA / "flora" / "zones" / "z10_settled_town.json"
EXISTING = DATA / "flora" / "plantings" / "sauganash_yard.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
OUT = DATA / "flora" / "plantings" / "town_dooryard_plantings.json"

DWELLING_ARCHETYPES = {"frame_dwelling", "log_dwelling"}

# The renderer's own refusals, with a working margin on top of each so a stem this
# tool deals can never sit on the wrong side of a boundary the renderer then
# refuses it over (a refused stem is a `problems` line, and the smoke fails on it).
CLEAR_MARGIN_M = 4.5      # trees.js CLEAR_MARGIN — nothing grows nearer a wall
FOOTPRINT_MARGIN_M = 5.0  # this tool's stricter bound over CLEAR_MARGIN_M
TRACK_SHOULDER_M = 0.65   # streets.js blocksGrowth's shoulder off the track
TRACK_MARGIN_M = 2.0      # this tool's stricter bound over the shoulder
FENCE_MARGIN_M = 1.2      # no bole in a committed fence line
# A PLANK WALK IS A FLOOR, AND NOTHING GROWS UP THROUGH ONE (T-0240). `main.js`
# hands the planters `frontage.keepOut` inside the same `planting` array as the
# building footprints, so `trees.js` refuses a stem standing on a walk exactly as
# it refuses one standing in a wall — and this tool did not know it, because when
# it was written the street edge reached no block a dooryard stands on. T-0240
# laid Randolph Street and two dealt bushes came out underneath it
# (`blk_randolph_clinton_d4_02_bush_1`, `blk_randolph_dearborn_d1_12_bush_2`):
# still in the record, refused at load, visible only in the smoke's problem list.
# Read here from `data/frontage/`, the same records `frontage.js` builds its
# rectangles from, so the two agree by construction rather than by luck.
# The margin is `trees.js` CLEAR_MARGIN plus this tool's usual half metre, the
# same pair as FOOTPRINT_MARGIN_M above and for the same reason: `blocked()`
# refuses a stem within CLEAR_MARGIN of ANY polygon edge in the `planting`
# array, and a keep-out rectangle is in that array beside the footprints. The
# two refused bushes stood 0.99 m and 2.63 m off a walk edge — clear of the
# boards and well inside the 4.5 m.
WALK_MARGIN_M = 5.0       # outside the walk's own half-width
DRY_FLOOR_M = 0.9         # trees.js asks +0.20 over water; this tool asks more
STEM_SPACING_M = 3.0      # stems keep clear of each other
EDGE_INSET_M = 6.0        # and off the heightfield's own edge

# THE STREET A HOUSE'S YARD IS MEASURED FROM (T-0255). `candidates()` seats a
# house's stems AWAY FROM THE NEAREST STREET, because the yard is behind the
# house — and until this ticket "the nearest street" meant the nearest record in
# data/streets/1835.json, every one of them, at any distance, on either bank.
# Nobody chose that. T-0099 laid `fort_bank_track`, a 23.91 m track on the SOUTH
# bank below the fort's north gate, and it became the nearest street to a
# dwelling on the NORTH bank with no crossing between the two for hundreds of
# metres, turning that house's cottonwoods about 6 m. Worse than the 6 m: any
# street laid anywhere could re-seat stems at a house it has nothing to do with,
# and the only signal was a --check drift with no rule to decide it against.
#
# TWO BOUNDS NOW SAY WHAT THE PHRASE IS ALLOWED TO MEAN, and both are measured
# off committed data rather than picked.
#
#   THE BANK. A street is a house's street only where it stands on the same dry
#   ground. The committed heightfield's land cells fall into FOUR four-connected
#   pieces — the West, South and North Divisions the river separates, and the
#   9.5 ha of lake shore east of the 1834 harbour cut — and that partition IS
#   the river, drawn by the same field the renderer walks the visitor over. Each
#   street's path is cut into the runs that lie in each piece, and a house
#   measures only the runs in its own. Kinzie Street runs out of the West
#   Division, across the North Branch at Wolf Point and into the North: a North
#   Division house now measures it along its North Division reach, and not across
#   the water. Nothing here is a tolerance — a bank is a connected component, and
#   the fix is exactly as sharp as the committed waterline is.
#
#   THE REACH. 68.72 m, and the figure is the plat's own rather than a round
#   number: the deepest committed lot in data/traces/vectors/thompson_lots.json
#   is 56.53 m deep (144 lots, 43.83-56.53 m), and the centreline of the street it
#   fronts stands half of the plat's 80 ft module — 12.192 m — beyond its
#   frontage. So no ground inside the platted town lies further than 68.72 m from
#   the centreline of the street it fronts, and ground past that reach is no
#   further "away from the street" than ground at it. THE BOUND IS A CLAMP ON THE
#   SCORE, NOT A CLIFF, and that is load-bearing: a cliff would score a house's
#   far candidates above its near ones wherever the bound fell inside its own ring
#   of candidate ground, and seat its trees outside its lot to escape a street.
#
# WHAT IS DELIBERATELY NOT BOUNDED is the REFUSAL in `clear()`: no stem may stand
# in any street's travelled track, whichever bank that street is on and whoever
# fronts it. That refusal is about the two metres around the point, not about
# whose yard it is, and bounding it would let a stem grow up through a road.
YARD_STREET_REACH_M = 68.72

SEED = "t74-dooryard-plantings-v1"

# The deal. Numbers of stems per house, and the species weights among the kept
# trees. All invented; the RECORD-LEVEL bound is the zone's own density bands,
# checked and printed by build().
TREE_DEAL = [(0.15, 0), (0.75, 1), (1.0, 2)]
BUSH_DEAL = [(0.20, 0), (0.70, 1), (1.0, 2)]
TREE_SPECIES = [(0.55, "ulmus_americana"), (1.0, "populus_deltoides")]
BUSH_SPECIES = "ribes_spp"
# Kept-tree heights: the LOW third of each species' recorded band (T-0091's
# cut-back argument). Bushes take their full recorded band.
KEPT_FRACTION = 1 / 3


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rnd(sid: str, what: str) -> float:
    """Deterministic uniform [0,1) from the structure id and a purpose tag."""
    digest = hashlib.sha256(f"{SEED}:{sid}:{what}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def deal(u: float, table):
    for ceiling, value in table:
        if u < ceiling:
            return value
    return table[-1][1]


def footprint_world(sidecar):
    """The footprint in local ENU, placed and rotated the way the RENDERER does it
    (walker.js footprintsFrom: compass bearing, clockwise from north)."""
    fp = (sidecar.get("footprint") or {}).get("polygon") or []
    pl = sidecar.get("placement") or {}
    e0, n0 = pl.get("local_e"), pl.get("local_n")
    th = math.radians(pl.get("rotation_deg") or 0.0)
    c, s = math.cos(th), math.sin(th)
    return [(e0 + u * c + v * s, n0 - u * s + v * c) for u, v in fp]


def poly_contains(pt, poly) -> bool:
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def seg_dist(p, a, b) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def poly_edge_dist(p, poly) -> float:
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)])
               for i in range(len(poly)))


def path_dist(p, path) -> float:
    return min(seg_dist(p, path[i], path[i + 1]) for i in range(len(path) - 1))


def dry_banks(hf):
    """Every heightfield cell labelled with the piece of dry ground it belongs to.

    A four-connected flood fill over the cells at or above the committed water
    surface; water and everything off the field label -1. This is the whole notion
    of "which bank" this tool has, and it is the renderer's own ground rather than
    a second opinion about it: the same samples terrain.js draws, cut at the same
    water surface. On the committed field it finds FOUR pieces, which is the town:
    the West Division (20.4 ha), the South (55.2 ha), the North (35.9 ha), and the
    9.5 ha of lake shore east of the 1834 harbour cut.
    """
    water = float(hf.meta.get("water_surface_m", 0.0))
    cols, rows = hf.cols, hf.rows
    dry = [raw * hf.scale + hf.offset >= water for raw in hf.samples]
    labels = [-1] * (cols * rows)
    count = 0
    for seed in range(cols * rows):
        if not dry[seed] or labels[seed] >= 0:
            continue
        labels[seed] = count
        stack = [seed]
        while stack:
            k = stack.pop()
            j, i = divmod(k, cols)
            for kk in ((k - cols if j else -1), (k + cols if j + 1 < rows else -1),
                       (k - 1 if i else -1), (k + 1 if i + 1 < cols else -1)):
                if kk >= 0 and dry[kk] and labels[kk] < 0:
                    labels[kk] = count
                    stack.append(kk)
        count += 1
    return labels, count


def bank_at(hf, labels, e, n) -> int:
    """The piece of dry ground a point stands on, or -1 for water and off-field."""
    i = int(round((e - hf.origin_e) / hf.cell_m))
    j = int(round((n - hf.origin_n) / hf.cell_m))
    if 0 <= i < hf.cols and 0 <= j < hf.rows:
        return labels[j * hf.cols + i]
    return -1


def split_by_bank(path, hf, labels):
    """One street's path cut into short segments, filed under the bank each stands
    on. Sampled at the heightfield's own cell so every segment endpoint lies ON the
    original line: a distance measured to these segments is a distance to the
    street, not to an approximation of it. A street that crosses water files
    segments under both banks and none for the crossing itself."""
    banks = {}
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        span = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(1, int(math.ceil(span / hf.cell_m)))
        prev = None
        for s in range(steps + 1):
            t = s / steps
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if prev is not None:
                k = bank_at(hf, labels, (prev[0] + p[0]) / 2, (prev[1] + p[1]) / 2)
                if k >= 0:
                    banks.setdefault(k, []).append((prev, p))
            prev = p
    return banks


def is_dwelling_function(value: str) -> bool:
    """T-0052's clause, verbatim — the same houses get trees that get gardens."""
    v = (value or "").strip().lower()
    if v in {"dwelling", "residence"}:
        return True
    return any(word in v for word in ("dwelling", "cottage", "house", "shanty",
                                      "cabin")) and \
        not any(word in v for word in ("boarding", "school", "meeting", "warehouse",
                                       "tavern", "hotel", "store", "shop", "wash",
                                       "court", "guard", "packing", "slaughter"))


class World:
    """Everything a stem must stand clear of, and the ground it stands on."""

    def __init__(self, sidecars, obstructions, streets, fences, walks, hf,
                 labels, bank_count, taken):
        self.sidecars = sidecars
        self.obstructions = obstructions
        self.streets = streets
        self.fences = fences
        self.walks = walks
        self.hf = hf
        self.labels = labels
        self.bank_count = bank_count
        self.taken = taken


def world():
    """Everything a stem must stand clear of, read once."""
    sidecars = {}
    for path in sorted(SIDECARS.glob("*.json")):
        sc = load(path)
        pl = sc.get("placement") or {}
        if pl.get("local_e") is None:
            continue
        sidecars[path.stem] = sc
    # The obstruction set mirrors walker.js footprintsFrom(): a water-anchored
    # footprint is a deck, and a record drawn by another layer is a fence line,
    # not a wall — both are excluded there and both are excluded here.
    obstructions = []
    for sid, sc in sidecars.items():
        pl = sc.get("placement") or {}
        if pl.get("vertical_anchor") == "water":
            continue
        if sc.get("drawn_by"):
            continue
        fp = footprint_world(sc)
        if len(fp) >= 3:
            obstructions.append(fp)
    hf = Heightfield.load(EPOCH)
    if hf is None:
        raise SystemExit("no heightfield at " + str(EPOCH))
    # The banks, before the streets, because a street is now read bank by bank.
    labels, bank_count = dry_banks(hf)
    streets = []
    for st in load(STREETS)["streets"]:
        pts = st.get("path_local_enu_m") or []
        if len(pts) >= 2:
            streets.append((pts, float(st.get("track_width_m") or 0.0),
                            split_by_bank(pts, hf, labels)))
    fences = []
    for path in sorted(ENCLOSURES.glob("*.json")):
        if path.name == "index.json":
            continue
        rec = load(path)
        for run in rec.get("runs") or []:
            pts = run.get("path_local_enu_m") or []
            if len(pts) >= 2:
                fences.append(pts)
    # The plank walks and board crossings, segment by segment with their own
    # half-width — the same rectangles `frontage.js` hands the planters as
    # `keepOut`, derived here from the same records the way
    # `tools/generate_yard_goods.py` derives them.
    walks = []
    for path in sorted(FRONTAGE.glob("*.json")):
        if path.name == "index.json":
            continue
        rec = load(path)
        for walk in rec.get("walks") or []:
            line = walk.get("centreline_local_enu_m") or []
            half = float(walk.get("width_m") or 1.83) / 2.0
            for i in range(len(line) - 1):
                walks.append((tuple(line[i]), tuple(line[i + 1]), half))
    taken = [tuple(stem["at_local_enu_m"]) for stem in load(EXISTING)["stems"]]
    return World(sidecars, obstructions, streets, fences, walks, hf, labels,
                 bank_count, taken)


def clear(p, w) -> bool:
    e, n = p
    obstructions, streets, fences, walks, hf, taken = (
        w.obstructions, w.streets, w.fences, w.walks, w.hf, w.taken)
    if not (hf.origin_e + EDGE_INSET_M <= e
            <= hf.origin_e + (hf.cols - 1) * hf.cell_m - EDGE_INSET_M
            and hf.origin_n + EDGE_INSET_M <= n
            <= hf.origin_n + (hf.rows - 1) * hf.cell_m - EDGE_INSET_M):
        return False
    if hf.height(e, n) < float(hf.meta.get("water_surface_m", 0.0)) + DRY_FLOOR_M:
        return False
    for fp in obstructions:
        cx = sum(q[0] for q in fp) / len(fp)
        cy = sum(q[1] for q in fp) / len(fp)
        if abs(e - cx) > 60 or abs(n - cy) > 60:
            continue
        if poly_contains(p, fp) or poly_edge_dist(p, fp) < FOOTPRINT_MARGIN_M:
            return False
    # THE REFUSAL IS UNBOUNDED ON PURPOSE (T-0255): every street, either bank.
    for pts, track_w, _banks in streets:
        if path_dist(p, pts) < track_w / 2 + TRACK_SHOULDER_M + TRACK_MARGIN_M:
            return False
    for pts in fences:
        if path_dist(p, pts) < FENCE_MARGIN_M:
            return False
    for a, b, half in walks:
        if seg_dist(p, a, b) < half + WALK_MARGIN_M:
            return False
    return all(math.hypot(e - te, n - tn) >= STEM_SPACING_M for te, tn in taken)


def facing_street_segments(cx, cy, ring, w):
    """The street ground this house's yard is measured from: the segments of every
    street that stand on THIS HOUSE'S BANK and near enough to matter.

    "Near enough" is the reach bound plus the radius of the candidate ring, so a
    segment is kept whenever any candidate point could fall inside the bound of
    it; the bound itself is applied per point in `candidates()`. Segments are one
    heightfield cell long, so testing their endpoints against a box is exact to
    within that cell and the slack below covers it.
    """
    bank = bank_at(w.hf, w.labels, cx, cy)
    if bank < 0:
        return []
    box = YARD_STREET_REACH_M + ring + w.hf.cell_m
    out = []
    for _pts, _track_w, banks in w.streets:
        for a, b in banks.get(bank, ()):
            if (abs(a[0] - cx) <= box and abs(a[1] - cy) <= box) or \
               (abs(b[0] - cx) <= box and abs(b[1] - cy) <= box):
                out.append((a, b))
    return out


def candidates(sc, w):
    """Allowed points around one house, each scored for yard-ness.

    A ring scan around the footprint centroid: 24 compass bearings by radii from
    just past the clearance out to 12 m beyond the house. `yard` prefers ground
    away from the nearest street (the yard is behind the house) and close to the
    walls; `door` prefers the closest allowed ground whatever its quarter, which
    is where a bush by the house reads from the road.

    THE NEAREST STREET IS THE NEAREST STREET ON THIS HOUSE'S OWN BANK, MEASURED NO
    FURTHER THAN THE PLAT'S OWN DEEPEST REACH — the two bounds stated at
    YARD_STREET_REACH_M above. A house with no street inside that reach on its own
    bank scores every candidate at the bound, which leaves `yard` deciding on
    closeness to the walls alone: that is the honest answer for a house whose
    street this project does not hold, and it is stable under any street laid
    anywhere else in the town.
    """
    fp = footprint_world(sc)
    cx = sum(q[0] for q in fp) / len(fp)
    cy = sum(q[1] for q in fp) / len(fp)
    reach = max(math.hypot(q[0] - cx, q[1] - cy) for q in fp)
    facing = facing_street_segments(cx, cy, reach + 12.0, w)
    out = []
    r = reach + 2.0
    while r <= reach + 12.0:
        for k in range(24):
            b = math.radians(k * 15.0)
            p = (round(cx + math.sin(b) * r, 2), round(cy + math.cos(b) * r, 2))
            if not clear(p, w):
                continue
            street = YARD_STREET_REACH_M
            for a, c in facing:
                d = seg_dist(p, a, c)
                if d < street:
                    street = d
            near = poly_edge_dist(p, fp)
            out.append({"p": p, "yard": street - 0.6 * near, "door": -near})
        r += 1.0
    return out


def build():
    w = world()
    sidecars, taken = w.sidecars, w.taken
    z10 = {sp["id"]: sp for sp in load(ZONE)["species"]}
    stems, refused = [], []
    houses = kept = 0
    for sid in sorted(sidecars):
        sc = sidecars[sid]
        if sc.get("archetype") not in DWELLING_ARCHETYPES:
            continue
        st_path = STRUCTURES / f"{sid}.json"
        st = load(st_path) if st_path.exists() else sc
        fn = (st.get("attributes") or {}).get("function") if "attributes" in st \
            else st.get("function")
        if fn is None:
            fn = (sc.get("attributes") or {}).get("function")
        fn = fn.get("value") if isinstance(fn, dict) else fn
        if not is_dwelling_function(fn):
            continue
        houses += 1
        n_trees = deal(rnd(sid, "trees"), TREE_DEAL)
        n_bushes = deal(rnd(sid, "bushes"), BUSH_DEAL)
        if not n_trees and not n_bushes:
            continue
        pool = candidates(sc, w)
        placed_here = 0
        for i in range(n_trees):
            pool = [c for c in pool
                    if all(math.hypot(c["p"][0] - te, c["p"][1] - tn)
                           >= STEM_SPACING_M for te, tn in taken)]
            if not pool:
                refused.append(f"{sid}: no allowed ground for tree {i + 1}")
                break
            best = max(pool, key=lambda c: c["yard"])
            species = deal(rnd(sid, f"species{i}"), TREE_SPECIES)
            band = z10[species]["height_m"]
            lo, hi = band[0], band[0] + (band[1] - band[0]) * KEPT_FRACTION
            h = round(lo + (hi - lo) * rnd(sid, f"treeh{i}"), 1)
            stems.append({
                "id": f"{sid}_tree_{i + 1}",
                "species": species,
                "at_local_enu_m": list(best["p"]),
                "height_m": h,
                "confidence": "reconstructed",
                "note": (f"DEALT BY RULE for {sid}: the best-scored allowed ground "
                         f"in this house's yard quarter. {h} m sits in the low "
                         f"third of the species' recorded {band[0]}-{band[1]} m "
                         f"band — a kept tree is cut back and a planted one is "
                         f"young, and the record claims neither in particular."),
            })
            taken.append(best["p"])
            placed_here += 1
        for i in range(n_bushes):
            pool = [c for c in pool
                    if all(math.hypot(c["p"][0] - te, c["p"][1] - tn)
                           >= STEM_SPACING_M for te, tn in taken)]
            if not pool:
                refused.append(f"{sid}: no allowed ground for bush {i + 1}")
                break
            best = max(pool, key=lambda c: c["door"])
            band = z10[BUSH_SPECIES]["height_m"]
            h = round(band[0] + (band[1] - band[0]) * rnd(sid, f"bushh{i}"), 2)
            stems.append({
                "id": f"{sid}_bush_{i + 1}",
                "species": BUSH_SPECIES,
                "at_local_enu_m": list(best["p"]),
                "height_m": h,
                "confidence": "reconstructed",
                "note": (f"DEALT BY RULE for {sid}: the closest allowed ground to "
                         f"the house, which is where a dooryard bush stands. "
                         f"{h} m is inside the species' recorded band."),
            })
            taken.append(best["p"])
            placed_here += 1
        if placed_here:
            kept += 1
    return stems, refused, houses, kept, w.bank_count


def record(stems, refused, houses, kept, bank_count):
    trees = [s for s in stems if s["species"] != BUSH_SPECIES]
    bushes = [s for s in stems if s["species"] == BUSH_SPECIES]
    zone_poly = load(ZONE)["extent"]["polygon"]
    in_zone = sum(1 for s in stems if poly_contains(s["at_local_enu_m"], zone_poly))
    return {
        "_doc": (
            "A PLANTING RECORD, in the shape T-0091 established and its "
            "research_note asked the dooryard pass to reuse: woody stems whose "
            "position is STATED rather than dealt from the land. This one is "
            "GENERATED — tools/generate_dooryard_plantings.py holds the rule, "
            "prints why every house got what it got, and re-derives this file "
            "byte for byte in tools/check.sh."
        ),
        "id": "town_dooryard_plantings",
        "name": "The trees and bushes kept around the town's houses",
        "kind": "planting",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_dooryard_plantings.py",
        "generated_from": [
            "data/sidecars/1835/*.json",
            "data/structures/*.json",
            "data/streets/1835.json",
            "data/enclosures/*.json",
            "data/flora/zones/z10_settled_town.json",
            "data/terrain/epochs/e1834_harbor_cut/heightfield.json",
        ],
        "belongs_to": [],
        "in_enclosure": None,
        "zone": "z10_settled_town",
        "the_street_a_yard_is_measured_from": {
            "why_this_is_stated": (
                "A stem is seated AWAY FROM THE NEAREST STREET, because the yard "
                "is behind the house — so what 'the nearest street' is allowed to "
                "mean decides where every tree in this record stands, and until "
                "T-0255 it meant the nearest of all "
                + str(len(json.load(STREETS.open(encoding='utf-8'))["streets"]))
                + " records in data/streets/1835.json at any distance on either "
                "bank. Nobody chose that: a 23.91 m track laid on the SOUTH bank "
                "below the fort's north gate (T-0099) became the nearest street to "
                "a dwelling on the NORTH bank, with no crossing between the two "
                "for hundreds of metres, and turned that house's cottonwoods. The "
                "rule now has two bounds and both are measured rather than picked."
            ),
            "the_bank": (
                "A street is a house's street only where it stands on the same dry "
                "ground. The committed heightfield's land cells fall into "
                + str(bank_count) + " four-connected pieces — the West, South and "
                "North Divisions the river separates, and the lake shore east of "
                "the 1834 harbour cut — and that "
                "partition IS the river, read off the same field the renderer "
                "walks the visitor over. Each street's path is cut into the "
                "segments that lie in each piece and a house measures only the "
                "segments in its own, so Kinzie Street — which runs out of the "
                "West Division, across the North Branch at Wolf Point and into the "
                "North — is measured from a North Division house along its North "
                "Division reach and not across the water. This is a connected "
                "component and not a tolerance: there is no threshold to tune."
            ),
            "the_reach_m": YARD_STREET_REACH_M,
            "the_reach": (
                "68.72 m, and the figure is the plat's own. The deepest committed "
                "lot in data/traces/vectors/thompson_lots.json is 56.53 m deep "
                "(144 lots, 43.83-56.53 m), and the centreline of the street it "
                "fronts stands half of the plat's 80 ft module — 12.192 m — beyond "
                "its frontage, so no ground inside the platted town lies further "
                "than 68.72 m from the centreline of the street it fronts. Ground "
                "past that reach is no further 'away from the street' than ground "
                "at it. THE BOUND IS A CLAMP AND NOT A CLIFF: a cliff would score "
                "a house's far candidates above its near ones wherever the bound "
                "fell inside its own ring of candidate ground, and seat its trees "
                "outside its lot to escape a street."
            ),
            "what_is_not_bounded": (
                "The REFUSAL. No stem may stand in any street's travelled track, "
                "whichever bank that street is on and whoever fronts it — that "
                "refusal is about the two metres around the point, not about whose "
                "yard it is, and bounding it would let a stem grow up through a "
                "road."
            ),
        },
        "existence": {
            "value": True,
            "confidence": "inferred",
            "sources": ["chicagology_prefire273"],
            "note": (
                "THE TREATMENT IS THE OWNER'S BRIEF AND THE SPECIES ARE THE "
                "ZONE'S. Image 12 of data/sources/assets/owner_brief_2026_08_18/"
                "README.md — the circa-1833 view looking east — states the "
                "treatment generally: trees and bushes stand close around the "
                "houses, kept deliberately, and the owner asked for exactly this "
                "in as many words (ticket T-0074). The plates are tier-5 "
                "retrospective and are not source records here yet (T-0075), so "
                "they carry the FACT and no coordinate — the same reading "
                "T-0091 records for the Sauganash's yard. The cited source_id "
                "carries the other half: chicagology_prefire273 stands behind "
                "data/flora/zones/z10_settled_town.json, whose relict trees "
                "('Survivor elm in a part-cleared block') and dooryard currants "
                "(inferred there from the Fort Dearborn garden and Dr. Harmon's "
                "nursery) are the species every stem here names. Nothing is "
                "invented about WHAT stands by these houses; what is invented "
                "is which house keeps how many, and where each stem stands."
            ),
        },
        "stems": stems,
        "refused": refused,
        "research_note": (
            f"{len(trees)} DOORYARD TREES AND {len(bushes)} CURRANT BUSHES "
            f"ACROSS {kept} OF THE TOWN'S {houses} DWELLINGS, EVERY ONE OF THEM "
            "DEALT BY THE RULE IN tools/generate_dooryard_plantings.py — no "
            "source counts any house's trees, so the honest shape is a rule "
            "that says why each house got what it got, re-derived on every "
            "commit. THE DEAL IS DELIBERATELY THIN: at most two trees and two "
            "bushes to a house, under half a town of houses drawing any tree at "
            "all, and the dense party-wall blocks refuse themselves (a stem "
            "must clear every committed footprint by more than the renderer's "
            "own margin, so a rowhouse yard offers no allowed ground — the "
            "refusals below name each one). WHAT THE DENSITY IS NOT: ZONE 10's "
            "8-25/ha relict band binds the DEALT wood inside that zone's drawn "
            f"extent, and only {in_zone} of these {len(stems)} stems stand "
            "inside it; this record makes a HOUSEHOLD claim (a dooryard's "
            "stems), not an ecological one, and the two must not "
            "be added together. Whether any given tree was kept from the "
            "clearing or planted by the household is unknowable and unclaimed. "
            "Heights: trees in the LOW third of their recorded bands (cut-back "
            "if kept, young if planted); bushes anywhere in theirs. Every "
            "coordinate, count and height is reconstructed and claimed in "
            "docs/LIBERTIES.md L151. WHAT IS "
            "DELIBERATELY NOT HERE: the Lombardy poplars the ticket names are "
            "not dealt, because no committed flora zone record describes the "
            "species and the renderer refuses a stem the zone records do not "
            "carry — holding the poplar as a species is its own ticket; and the "
            "currant clumps are drawn without their July fruit, because the "
            "clonal draw path carries no berry (stated in trees.js). WHAT "
            "WOULD UPGRADE IT: T-0075's source records for the plates, or any "
            "sale notice, diary or view that counts or places a particular "
            "house's trees."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    args = ap.parse_args()
    stems, refused, houses, kept, bank_count = build()
    text = json.dumps(record(stems, refused, houses, kept, bank_count),
                      indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists():
            print(f"DOORYARD PLANTING DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"DOORYARD PLANTING DRIFT\n  - {OUT.relative_to(ROOT)} has "
                  f"drifted from the rule in tools/generate_dooryard_plantings.py")
            return 1
        print(f"verified {len(stems)} dooryard stems across {kept} of {houses} "
              f"dwellings ({len(refused)} refusal(s) for want of room)")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(stems)} stems across {kept} of "
          f"{houses} dwellings ({len(refused)} refusal(s) for want of room)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
