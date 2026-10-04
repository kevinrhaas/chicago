#!/usr/bin/env python3
"""Generate the kept ground of the improved town lots (T-2086).

WHY THIS EXISTS. The owner, 2026-10-04, verbatim: the town should be *"less 'weedy' in the
town area, in front of stores and houses, and in the house back yards and properties"* — and,
in the same breath, *"I don't want you to go crazy and cut all the beautiful plants and grass
and flowers ... I think we can improve the rendering and make it look more realistic and
accurate."* Until this record `z10_settled_town` grew one undifferentiated mix wherever it
reached: the trodden low layer (*Poa*, plantain, knotweed, clover) and, through every one of
its forb slots, lamb's-quarters, pigweed, ragweed, cocklebur, dock and vervain at 0.3-1.2 m —
in the middle of a yard somebody walked across to the privy six times a day as densely as on
the commons. Spread evenly, the tall weeds are what reads as "weedy".

WHAT A WORKING 1835 LOT LOOKS LIKE, and this is the reconstruction (docs/LIBERTIES.md, the
kept-lot liberty): the ground a household walks, its pigs and its cow crop and its children
trample is short. The weeds and flowers survive where scythe, hoof and foot do not reach — the
strip along a fence or lot line, the back corners of the lot, the foot of an outbuilding's
wall. So for every improved platted lot this writes:

  1. **the kept ring** — the lot polygon pulled in `STRIP_M` from every one of its lot lines,
     with its two REAR corners cut back `CORNER_M` along each line. Inside it the flora layer
     plants the zone's low layer and no forb in place; outside it, in the strip and the
     corners, the zone grows exactly as it did. The weeds are MOVED, not only cut: of the
     forb slots the ring turns out, `MOVED_SHARE` are re-seated in the strip beside the
     nearest lot line, so the fence foot carries the dense weedy fringe a real one does and
     the town's forb count does not rise. `renderers/web/js/flora.js` reads this through
     `main.js`'s `forbSeat` and nothing else: WHICH ground is kept, how wide the strip is and
     how many weeds it takes are stated here, in data;
  2. **refuges** — the foot of every outbuilding on the lot (the privies and stables of
     `data/yard/town_yard_outbuildings.json`, and every committed building standing behind
     the front one) grown by `REFUGE_M`. A forb in a refuge stands even inside the kept ring;
  3. **the worn paths** — a trodden line, `PATH_W_M` wide, from the back wall of the house
     the outbuilding belongs to (or the lot's front building) to the outbuilding's own wall.
     These are written as an enclosure-layer ground record (`data/enclosures/
     town_yard_paths.json`, treatment `road_earth`) because that is the layer that already
     lays worn earth on a drape and takes the sward off it; it is the same treatment the
     door aprons use, so a path is the town's own dirt and not a new canvas.

A VACANT LOT IS NOT A YARD and this writes nothing for one: a platted lot with no building
keeps the zone's planting. What it should be instead — a grazed, flowering prairie remnant —
is the other half of T-2086 and is a community question, not a lot-line question.

WHAT IS NOT DONE: no mown lawn (not 1835 — docs/RESEARCH/1835_photographic_fabric_
preparation.md), no new species, no change to any zone's abundance, and the dooryard gardens'
beds (T-1958) are untouched — their interiors already take the sward off and lay their own
ground. Every dimension below is invented and bounded in the liberty; none is a reading of
any particular yard.

    python3 tools/generate_kept_ground.py            write the two records
    python3 tools/generate_kept_ground.py --check    re-derive and diff (tools/check.sh)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_lot_line_fences as fences  # noqa: E402
from generate_dooryard_pickets import convex_overlap, poly_contains  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTBUILDINGS = DATA / "yard" / "town_yard_outbuildings.json"
TRADE_YARDS = DATA / "yard" / "town_trade_yards.json"
OUT_KEPT = DATA / "yard" / "town_kept_ground.json"
OUT_PATHS = DATA / "enclosures" / "town_yard_paths.json"
LIBERTY = "docs/LIBERTIES.md L376"

# THE LOT, in feet and recorded converted, per data/datum.json's units rule.
STRIP_M = 0.762       # 2½ ft along every lot line that the scythe and the hoof miss
CORNER_M = 2.438      # 8 ft cut back along each line at the two rear corners
REFUGE_M = 0.610      # 2 ft of weeds round the foot of an outbuilding wall
PATH_W_M = 0.914      # 3 ft — one person's worn way, not a cart's
PATH_CLEAR_M = 0.15   # a path stops this far off the walls it joins
MIN_PATH_M = 1.5      # shorter than this it is a doorstep, not a path
MOVED_SHARE = 0.35    # of the forbs the kept ring turns out, the share re-seated in the strip


def r2(p) -> list[float]:
    return [round(p[0], 2), round(p[1], 2)]


def area2(poly) -> float:
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
               - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def offset_convex(poly, d: float):
    """A convex polygon with every edge moved `d` metres INWARD (negative: outward), its
    corners re-found where neighbouring moved edges meet. None when it collapses."""
    pts = list(poly) if area2(poly) > 0 else list(reversed(poly))
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            continue
        nx, ny = -dy / ln, dx / ln          # inward normal of a counter-clockwise ring
        lines.append(((a[0] + nx * d, a[1] + ny * d), (dx / ln, dy / ln)))
    out = []
    for i in range(len(lines)):
        (p, u), (q, v) = lines[i - 1], lines[i]
        den = u[0] * v[1] - u[1] * v[0]
        if abs(den) < 1e-9:
            out.append(q)
            continue
        t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
        out.append((p[0] + u[0] * t, p[1] + u[1] * t))
    if len(out) < 3 or area2(out) <= 0.5:
        return None
    return out


def clip_half(poly, a, b):
    """Keep the part of a counter-clockwise polygon to the LEFT of the line a -> b."""
    def side(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def kept_ring(entry):
    """The lot pulled in from its lines, with the two rear corners cut back."""
    lot = entry["lot"]
    poly = lot["polygon"]
    inner = offset_convex(poly, STRIP_M)
    if inner is None:
        return None
    _front, (ra, rb), _sides = fences.lot_edges(entry["block"], lot)
    for c in (poly[ra], poly[rb]):
        # The inner ring's corner nearest this lot corner, and its two neighbours.
        k = min(range(len(inner)), key=lambda i: math.hypot(inner[i][0] - c[0],
                                                           inner[i][1] - c[1]))
        p, q, s = inner[k - 1], inner[k], inner[(k + 1) % len(inner)]

        def toward(a, b, dist):
            ln = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            t = min(dist / ln, 0.45)
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        # The cut runs from a point CORNER_M back along the incoming edge to one CORNER_M
        # along the outgoing edge, which leaves the corner itself on the cut's right.
        inner = clip_half(inner, toward(q, p, CORNER_M), toward(q, s, CORNER_M))
        if len(inner) < 3:
            return None
    return inner


def rect_of(at, bearing_deg, along, depth, grow=0.0):
    """An outbuilding's walls as ENU corners — the same frame `yard.js` builds it in:
    along (cos b, -sin b), out (sin b, cos b) in east-north."""
    b = math.radians(bearing_deg)
    ax, an = math.cos(b), -math.sin(b)
    ox, on = math.sin(b), math.cos(b)
    ha, hd = along / 2 + grow, depth / 2 + grow
    return [(at[0] + ax * sa * ha + ox * so * hd, at[1] + an * sa * ha + on * so * hd)
            for sa, so in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def exit_toward(poly, inside, target):
    """Where the ray from `inside` toward `target` leaves the convex `poly`."""
    dx, dy = target[0] - inside[0], target[1] - inside[1]
    best = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - inside[0]) * ey - (a[1] - inside[1]) * ex) / den
        s = ((a[0] - inside[0]) * dy - (a[1] - inside[1]) * dx) / den
        if 0 <= s <= 1 and 0 < t <= 1:
            best = max(best, t)
    return (inside[0] + dx * best, inside[1] + dy * best)


def path_ring(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    a = (a[0] + ux * PATH_CLEAR_M, a[1] + uy * PATH_CLEAR_M)
    b = (b[0] - ux * PATH_CLEAR_M, b[1] - uy * PATH_CLEAR_M)
    hx, hy = -uy * PATH_W_M / 2, ux * PATH_W_M / 2
    return [r2((a[0] + hx, a[1] + hy)), r2((a[0] - hx, a[1] - hy)),
            r2((b[0] - hx, b[1] - hy)), r2((b[0] + hx, b[1] + hy))]


def build():
    entries, sidecars = fences.survey()
    obs = fences.load(OUTBUILDINGS)["outbuildings"]
    by_lot: dict[str, list] = {}
    for ob in obs:
        by_lot.setdefault(ob["lot"], []).append(ob)
    # A store's working yard stays worn earth with its goods on it (T-1961); a house path
    # does not cut across one.
    trade = [[tuple(p) for p in lot["ground_quad_local_enu_m"]]
             for lot in fences.load(TRADE_YARDS).get("lots", [])
             if len(lot.get("ground_quad_local_enu_m") or []) >= 3]
    lots, paths, refused = [], [], []
    for entry in entries:
        lot_id = f"{entry['block']['id']}_lot{entry['index']}"
        ring = kept_ring(entry)
        if ring is None:
            refused.append({"lot": lot_id, "why": "the lot is too small to keep a yard "
                            f"inside a {STRIP_M} m strip"})
            continue
        poly = entry["lot"]["polygon"]
        (fa, fb), (ra, rb), _sides = fences.lot_edges(entry["block"], entry["lot"])
        fm = ((poly[fa][0] + poly[fb][0]) / 2, (poly[fa][1] + poly[fb][1]) / 2)
        rm = ((poly[ra][0] + poly[rb][0]) / 2, (poly[ra][1] + poly[rb][1]) / 2)
        depth = math.hypot(rm[0] - fm[0], rm[1] - fm[1])
        vx, vy = (rm[0] - fm[0]) / depth, (rm[1] - fm[1]) / depth

        def v_of(p):
            return (p[0] - fm[0]) * vx + (p[1] - fm[1]) * vy
        fps = {s: fp for s, fp in zip(entry["buildings"], entry["footprints"]) if len(fp) >= 3}
        if not fps:
            continue
        front = min(fps, key=lambda s: min(v_of(p) for p in fps[s]))
        back = max(v_of(p) for p in fps[front])
        # Every outbuilding: the dealt privies and stables, and every committed building
        # that stands wholly behind the front building's back wall.
        sheds = []
        for ob in sorted(by_lot.get(lot_id, []), key=lambda o: o["id"]):
            walls = rect_of(ob["at_local_enu_m"], ob["bearing_deg"], ob["along_m"],
                            ob["depth_m"])
            house = ob.get("belongs_to") if ob.get("belongs_to") in fps else front
            sheds.append((ob["id"], walls, house))
        for sid in sorted(fps):
            if sid != front and min(v_of(p) for p in fps[sid]) > back:
                sheds.append((sid, fps[sid], front))
        refuges = []
        for sid, walls, house in sheds:
            grown = offset_convex(walls, -REFUGE_M)
            if grown:
                refuges.append([r2(p) for p in reversed(grown)] if area2(grown) < 0
                               else [r2(p) for p in grown])
            hw = fps[house]
            hc, sc = centroid(hw), centroid(walls)
            start = exit_toward(hw, hc, sc)
            end = exit_toward(walls, sc, hc)
            if math.hypot(end[0] - start[0], end[1] - start[1]) < MIN_PATH_M + 2 * PATH_CLEAR_M:
                continue
            ring_p = path_ring(start, end)
            if not all(poly_contains(tuple(p), poly) for p in ring_p):
                continue
            if any(convex_overlap([tuple(p) for p in ring_p], q) for q in trade):
                continue
            paths.append({"lot": lot_id, "from": house, "to": sid, "ring": ring_p})
        lots.append({
            "lot": lot_id,
            "structures": sorted(fps),
            "kept_ring_local_enu_m": [r2(p) for p in ring],
            "refuges_local_enu_m": refuges,
        })
    return lots, paths, refused


EXISTENCE_NOTE = (
    "RECONSTRUCTED (T-2086, " + LIBERTY + "). No source describes where on an 1835 Chicago "
    "lot the ground was short and where the weeds stood. The owner asked on 2026-10-04 for a "
    "town 'less weedy ... in front of stores and houses, and in the house back yards' without "
    "cutting 'the beautiful plants and grass and flowers'. What bounds the reconstruction is "
    "the zone record's own grazing evidence (the town's code of 7 Nov 1833 against wandering "
    "pigs; cattle on the unfenced commons) and the plain mechanics of a used yard: ground a "
    "household walks, and its stock crops, is short; a fence line, a back corner and the foot "
    "of a wall are where scythe, hoof and foot do not reach. Cropped, not mown: a striped "
    "lawn is not 1835.")


def kept_record(lots, refused, n_paths) -> dict:
    return {
        "id": "town_kept_ground",
        "name": "The kept ground of the improved lots",
        "kind": "kept_ground",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_kept_ground.py",
        "generated_from": [
            "data/traces/vectors/thompson_lots.json",
            "data/sidecars/1835/",
            "data/yard/town_yard_outbuildings.json",
            "data/yard/town_trade_yards.json",
        ],
        "coordinates": "Local East-North-Up metres from data/datum.json's origin.",
        "existence": {"value": True, "confidence": "reconstructed", "sources": [],
                      "note": EXISTENCE_NOTE},
        "strip_m": STRIP_M,
        "moved_share": MOVED_SHARE,
        "rule": {
            "kept_ring": f"the improved lot's polygon pulled in {STRIP_M} m (2½ ft) from every "
                         f"lot line, its two rear corners cut back {CORNER_M} m (8 ft) along "
                         "each line; inside it the flora layer plants the zone's low layer "
                         f"and no forb in place, and re-seats {MOVED_SHARE:.0%} of the forbs "
                         "it turns out in the strip beside the nearest lot line",
            "refuges": f"every outbuilding's walls grown by {REFUGE_M} m (2 ft); a forb there "
                       "stands even inside the kept ring",
            "paths": f"{n_paths} worn path(s), {PATH_W_M} m (3 ft) wide, house back wall to "
                     "outbuilding wall — written to data/enclosures/town_yard_paths.json",
            "vacant_lots": "a platted lot with no building is not a yard and is not listed; "
                           "it keeps the zone's planting",
            "reader": "renderers/web/js/flora.js, through main.js forbSeat",
        },
        "counts": {"lots": len(lots), "refused": len(refused),
                   "refuges": sum(len(x["refuges_local_enu_m"]) for x in lots),
                   "paths": n_paths},
        "lots": lots,
        "refused": refused,
    }


def paths_record(paths) -> dict:
    return {
        "id": "town_yard_paths",
        "name": "The worn paths across the house yards",
        "aka": ["the way to the privy", "the yard paths"],
        "kind": "yard",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_kept_ground.py",
        "generated_from": [
            "data/traces/vectors/thompson_lots.json",
            "data/sidecars/1835/",
            "data/yard/town_yard_outbuildings.json",
        ],
        "belongs_to": sorted({p["from"] for p in paths}),
        "documented_range": {"from": "1835-07-01", "to": "1835-07-01",
                             "confidence": "reconstructed", "sources": [],
                             "note": "Dated to the scene: every house and outbuilding it "
                                     "joins is standing on it."},
        "existence": {"value": True, "confidence": "reconstructed", "sources": [],
                      "note": EXISTENCE_NOTE + " A path is the straight worn line from the "
                      "house's back wall to the outbuilding's, the way a daily errand wears "
                      "one. No fence is claimed."},
        "runs": [],
        "openings": [],
        "form": {},
        "ground": {"treatment": "road_earth", "confidence": "reconstructed",
                   "interior_local_enu_m": [p["ring"] for p in paths]},
        "paths": [{"lot": p["lot"], "from": p["from"], "to": p["to"]} for p in paths],
        "research_note": "Generated by tools/generate_kept_ground.py with the kept ground of "
                         "data/yard/town_kept_ground.json; the treatment is the door aprons' "
                         "road earth, so a path is the town's own dirt.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()
    lots, paths, refused = build()
    failed = 0
    for path, rec in ((OUT_KEPT, kept_record(lots, refused, len(paths))),
                      (OUT_PATHS, paths_record(paths))):
        text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                print(f"KEPT GROUND DRIFT\n  - {path.relative_to(ROOT)} has drifted from the "
                      "rule in tools/generate_kept_ground.py")
                failed = 1
        else:
            path.write_text(text, encoding="utf-8")
    if failed:
        return 1
    print(f"{'verified' if args.check else 'wrote'} {len(lots)} kept lot(s), "
          f"{sum(len(x['refuges_local_enu_m']) for x in lots)} refuge(s), "
          f"{len(paths)} path(s); {len(refused)} refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
