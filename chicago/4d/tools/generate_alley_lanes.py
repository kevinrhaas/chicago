#!/usr/bin/env python3
"""The block alleys of the 1835 town drawn as trodden lanes, out to the street's track at
each end. (T-2095)

## The fault this closes

The owner, 2026-10-04, asking for a town that reads as lived in: "the sides of the
roads", "the alleys, any frontages or paths" still read as prairie (T-2087). The plat
model has cut a mid-block alley through 32 blocks since T-0380
(`data/traces/vectors/thompson_lots.json`, `alley_local_enu_m`), the yard outbuildings
stand "off the alley" behind every built lot (T-1960), and yet nothing on the ground
said an alley was there: since T-2085 it was the same short town turf as the back yards
either side of it, and a visitor could not find it.

## What this writes

`data/enclosures/town_alley_lanes.json`, an enclosure-layer record with no fence — the
shape of `town_entrance_aprons.json` (T-1984): only a `ground` block whose interior is
one ring per lane. `yards.js` lays it in the road's own dirt (`road_earth`, T-2013) and
`main.js`'s sward block-list refuses the prairie inside it. No new renderer layer, and
no new draw call: the lanes join the door aprons in the one `road_earth` mesh.

## The rule

* WHICH ALLEYS. Every alley strip the plat model places, on a block where at least one
  structure stands on the scene date. A lane is worn by the traffic of the yards it
  serves; an alley on an empty block is a line on a survey, and it stays turf. Blocks
  the plat model gives no alley (Wabansia, where the sheet rules none, and the unlotted
  blocks of Kinzie's Addition) get none here either: this tool never adds an alley.
* WHERE IN THE ALLEY. A worn band LANE_W_M wide down the strip's own centreline — a
  cart's wheels and the horse between them — leaving the alley's edges either side in
  the town's turf (T-2085), with a slow wobble so the edge is walked, not ruled.
* AT EACH END. Out along the alley's axis across the street corridor to the travelled
  track of the cross street when one lies within MOUTH_REACH_M, and MOUTH_INTO_TRACK_M
  onto it, widening by MOUTH_FLARE_M where carts swing in — so the lane meets the road
  in the road's own grit with no seam. Where the cross street is unopened (no track)
  the lane stops MOUTH_SPILL_M past the block edge.
* NOTHING STANDS IN IT. A lane is cut short where a committed footprint (grown by
  CLEAR_M) stands across it, and the cut is printed: a building in an alley is a fact
  about the reconstruction that someone should see.

## What is invented

All of it but the strip (docs/LIBERTIES.md, the lane's liberty): no source says which
1835 blocks were alleyed, where the alley ran, or that it was worn. The strip is the plat
model's (itself `reconstructed`, `module.alley_note`); the width of the worn band, the
wobble and the mouth are bounded by a cart's track and nothing else.

    python3 tools/generate_alley_lanes.py           write the record
    python3 tools/generate_alley_lanes.py --check   re-derive and diff
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

import generate_business_signboards as gbs  # noqa: E402
import generate_frontage_works as gfw  # noqa: E402

LOTS = ROOT / "data" / "traces" / "vectors" / "thompson_lots.json"
SIDECARS = ROOT / "data" / "sidecars" / "1835"
STREETS = ROOT / "data" / "streets" / "1835.json"
OUT = ROOT / "data" / "enclosures" / "town_alley_lanes.json"
INDEX = ROOT / "data" / "enclosures" / "index.json"

# THE WORN BAND (reconstructed). A cart's wheels stand about 1.5 m apart (a 5 ft gauge)
# and a horse walks between the shafts; 2.4 m is that track with a hand either side.
LANE_W_M = 2.4
WOBBLE_M = 0.22                # how far the edge wanders off the centreline offset
WOBBLE_PERIOD_M = 9.0          # ...and over what length
STATION_M = 3.0                # the ring's vertex spacing along the lane
MOUTH_REACH_M = 16.0           # a cross street's track this close past the block edge
MOUTH_INTO_TRACK_M = 0.4
MOUTH_FLARE_M = 1.2            # how much wider the lane is at the track, each side
MOUTH_FLARE_LEN_M = 4.0        # ...over the last few metres
MOUTH_SPILL_M = 1.5            # no track ahead: how far past the block edge it runs
CLEAR_M = 0.5                  # a footprint grown by this much stops a lane
MIN_SEGMENT_M = 4.0            # a cut that leaves less than this is not drawn


def _r(x: float) -> float:
    return round(x, 2)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _tracks() -> list[tuple[str, list, float]]:
    """`(id, centreline, half track width)` for every OPENED 1835 street — a street
    whose record states a travelled track. An unopened line (track 0) has no road for
    a lane to meet."""
    out = []
    for st in load(STREETS).get("streets", []):
        path = [tuple(q) for q in st.get("path_local_enu_m", [])]
        w = float(st.get("track_width_m") or 0.0)
        if len(path) >= 2 and w > 0:
            out.append((st["id"], path, w / 2.0))
    return out


def _in_track(pt, tracks):
    for sid, path, half in tracks:
        if gfw._nearest_on_path(pt, path)[0] <= half:
            return sid
    return None


def _footprints() -> list[tuple[str, list]]:
    """`(structure id, ring in local ENU)` for every committed 1835 footprint, placed by
    the GLB contract's own composition (`generate_business_signboards._to_enu`)."""
    out = []
    for p in sorted(SIDECARS.glob("*.json")):
        sc = load(p)
        if not isinstance(sc, dict) or not sc.get("id"):
            continue
        poly = (sc.get("footprint") or {}).get("polygon") or []
        place = sc.get("placement") or {}
        if len(poly) < 3 or place.get("local_e") is None:
            continue
        out.append((sc["id"], [gbs._to_enu(u, v, place) for u, v in poly]))
    return out


def _pip(pt, poly) -> bool:
    x, y = pt
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _seg_dist(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy or 1e-12
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(a[0] + dx * t - p[0], a[1] + dy * t - p[1])


def _poly_dist(p, poly) -> float:
    """Distance from a point to a polygon: 0 inside it."""
    if _pip(p, poly):
        return 0.0
    return min(_seg_dist(p, poly[i - 1], poly[i]) for i in range(len(poly)))


def axis_of(strip: list) -> tuple[tuple, tuple, float, float]:
    """The alley strip's centreline as `(start, end, length, width)`: the midpoints of
    its two SHORT sides. The strip is the quad the plat model writes, corners in order."""
    q = [tuple(p) for p in strip[:4]]
    sides = [(q[i], q[(i + 1) % 4]) for i in range(4)]
    lens = [math.dist(a, b) for a, b in sides]
    k = 0 if lens[0] + lens[2] < lens[1] + lens[3] else 1
    s0, s1 = sides[k], sides[k + 2]
    mid = lambda s: ((s[0][0] + s[1][0]) / 2.0, (s[0][1] + s[1][1]) / 2.0)  # noqa: E731
    a, b = mid(s0), mid(s1)
    width = (lens[k] + lens[k + 2]) / 2.0
    return a, b, math.dist(a, b), width


def mouth(end, outward, tracks) -> tuple[float, str | None]:
    """How far past the block edge the lane runs at one end, and the street it meets."""
    t = 0.0
    while t <= MOUTH_REACH_M:
        sid = _in_track((end[0] + outward[0] * t, end[1] + outward[1] * t), tracks)
        if sid:
            return t + MOUTH_INTO_TRACK_M, sid
        t += 0.25
    return MOUTH_SPILL_M, None


def _wobble(seed: int, s: float, side: int) -> float:
    ph = (seed % 997) / 997.0 * 2 * math.pi + side * 1.9
    return WOBBLE_M * (0.65 * math.sin(2 * math.pi * s / WOBBLE_PERIOD_M + ph)
                       + 0.35 * math.sin(2 * math.pi * s / (WOBBLE_PERIOD_M * 0.43) + 2.3 * ph))


def lane_ring(seed, a, u, s0, s1, half, flare0, flare1, total0, total1) -> list:
    """One lane segment as a ring in local ENU, from along-axis `s0` to `s1` (metres from
    the alley's start `a`, along unit `u`). `flare0/1` say whether the segment's ends are
    street mouths; `total0/1` are where those mouths end (the flare's last metres)."""
    nrm = (-u[1], u[0])
    count = max(1, int(math.ceil((s1 - s0) / STATION_M)))
    stations = [s0 + (s1 - s0) * i / count for i in range(count + 1)]
    # The flare's own vertices, so the widening is drawn and not interpolated away.
    for edge, on in ((total0, flare0), (total1, flare1)):
        if on:
            for d in (MOUTH_FLARE_LEN_M, MOUTH_FLARE_LEN_M / 2):
                x = edge + d if edge == total0 else edge - d
                if s0 < x < s1:
                    stations.append(x)
    stations = sorted(set(round(x, 3) for x in stations))

    def width(s, side):
        w = half + _wobble(seed, s, side)
        for edge, on, sign in ((total0, flare0, 1), (total1, flare1, -1)):
            if on:
                d = (s - edge) * sign
                if d < MOUTH_FLARE_LEN_M:
                    k = 1.0 - max(0.0, d) / MOUTH_FLARE_LEN_M
                    w += MOUTH_FLARE_M * k * k
        return w

    left, right = [], []
    for s in stations:
        c = (a[0] + u[0] * s, a[1] + u[1] * s)
        wl, wr = width(s, 0), width(s, 1)
        left.append([_r(c[0] + nrm[0] * wl), _r(c[1] + nrm[1] * wl)])
        right.append([_r(c[0] - nrm[0] * wr), _r(c[1] - nrm[1] * wr)])
    # Counter-clockwise in east/north, as every apron ring is: yards.js ear-clips
    # in the ring's own winding, and a clockwise ring's triangles face down and are
    # culled — drawn, counted, and invisible.
    return right + left[::-1]


def _area2(ring) -> float:
    return sum(ring[i - 1][0] * ring[i][1] - ring[i][0] * ring[i - 1][1]
               for i in range(len(ring)))


def blocked_spans(a, u, s_lo, s_hi, length, half, feet) -> list[tuple[float, float, str]]:
    """The along-axis spans a grown footprint stands across, `(from, to, structure)`.
    The lane is tested at the width it is drawn: its wobble down the alley, and its
    flare too past the block edges, where the mouth widens."""
    nrm = (-u[1], u[0])
    out = []
    ends = [(a[0] + u[0] * s + nrm[0] * half * k, a[1] + u[1] * s + nrm[1] * half * k)
            for s in (s_lo, s_hi) for k in (-1, 1)]
    pad = half + WOBBLE_M + MOUTH_FLARE_M + CLEAR_M
    lo_e, hi_e = min(p[0] for p in ends) - pad, max(p[0] for p in ends) + pad
    lo_n, hi_n = min(p[1] for p in ends) - pad, max(p[1] for p in ends) + pad
    for sid, ring in feet:
        if (max(p[0] for p in ring) < lo_e or min(p[0] for p in ring) > hi_e
                or max(p[1] for p in ring) < lo_n or min(p[1] for p in ring) > hi_n):
            continue
        hit = []
        s = s_lo
        while s <= s_hi:
            c = (a[0] + u[0] * s, a[1] + u[1] * s)
            w = half + WOBBLE_M + (MOUTH_FLARE_M if s < 0 or s > length else 0.0)
            for k in (-1.0, -0.5, 0.0, 0.5, 1.0):
                p = (c[0] + nrm[0] * w * k, c[1] + nrm[1] * w * k)
                if _poly_dist(p, ring) <= CLEAR_M:
                    hit.append(s)
                    break
            s += 0.25
        if hit:
            out.append((min(hit) - 0.25, max(hit) + 0.25, sid))
    return sorted(out)


def build() -> dict:
    lots = load(LOTS)
    tracks = _tracks()
    feet = _footprints()
    rings, lanes, left_turf, cuts = [], [], [], []
    half = LANE_W_M / 2.0
    for blk in lots.get("blocks", []):
        strip = blk.get("alley_local_enu_m")
        if not strip or len(strip) < 4:
            continue
        boundary = blk.get("boundary_local_enu_m") or []
        on_block = sorted(sid for sid, ring in feet
                          if _pip((sum(p[0] for p in ring) / len(ring),
                                   sum(p[1] for p in ring) / len(ring)), boundary))
        if not on_block:
            left_turf.append(blk["id"])
            continue
        a, b, length, strip_w = axis_of(strip)
        u = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
        hw = min(half, strip_w / 2.0 - 0.6)
        m0, street0 = mouth(a, (-u[0], -u[1]), tracks)
        m1, street1 = mouth(b, u, tracks)
        s_lo, s_hi = -m0, length + m1
        seed = zlib.crc32(blk["id"].encode())
        spans = blocked_spans(a, u, s_lo, s_hi, length, hw, feet)
        pieces, cur = [], s_lo
        for f, t, sid in spans:
            if f > cur:
                pieces.append((cur, f))
            if t > cur:
                cur = t
            cuts.append({"alley_of": blk["id"], "structure_id": sid,
                         "from_m": _r(f), "to_m": _r(t)})
        if cur < s_hi:
            pieces.append((cur, s_hi))
        drawn = 0.0
        for k, (p0, p1) in enumerate(pieces):
            if p1 - p0 < MIN_SEGMENT_M:
                continue
            ring = lane_ring(seed + k, a, u, p0, p1, hw,
                             p0 == s_lo and street0 is not None,
                             p1 == s_hi and street1 is not None, s_lo, s_hi)
            rings.append(ring)
            drawn += p1 - p0
        lanes.append({
            "alley_of": blk["id"],
            "grid": blk.get("grid"),
            "strip_width_m": _r(strip_w),
            "worn_width_m": _r(2 * hw),
            "alley_length_m": _r(length),
            "meets": [street0, street1],
            "drawn_m": _r(drawn),
            "served": on_block,
        })
    served = sorted({s for x in lanes for s in x["served"]})
    return {
        "id": "town_alley_lanes",
        "name": "The trodden lanes down the town's block alleys",
        "aka": ["the alleys", "the back lanes"],
        "kind": "yard",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_alley_lanes.py",
        "generated_from": ["data/traces/vectors/thompson_lots.json", "data/sidecars/1835/",
                           "data/streets/1835.json"],
        "belongs_to": served,
        "documented_range": {
            "from": "1835-07-01", "to": "1835-07-01", "confidence": "reconstructed",
            "sources": [],
            "note": "Dated to the scene: every lane is worn by the yards standing on it."},
        "existence": {
            "value": True, "confidence": "reconstructed", "sources": [],
            "note": ("RECONSTRUCTED (T-2095, docs/LIBERTIES.md). No source says which "
                     "1835 blocks were alleyed, where the alley ran or that it was worn: "
                     "the strip is the plat model's own mid-block alley "
                     "(thompson_lots.json `module.alley_note`, itself reconstructed), "
                     "and a lane is drawn down it only where a structure stands on the "
                     "block to wear it. The owner asked on 2026-10-04 for the alleys to "
                     "read as used ground and not prairie (T-2087). No fence is claimed.")},
        "runs": [],
        "openings": [],
        "form": {},
        "ground": {
            "treatment": "road_earth",
            "confidence": "reconstructed",
            "interior_local_enu_m": rings,
            "note": (f"One ring per lane piece: a band {LANE_W_M} m wide down the plat "
                     "strip's own centreline (narrower where the strip is, leaving "
                     f"0.6 m of turf each side), its edges wandering {WOBBLE_M} m over "
                     f"{WOBBLE_PERIOD_M} m, carried at each end across the corridor to "
                     f"the cross street's track when one lies within {MOUTH_REACH_M} m "
                     f"and {MOUTH_INTO_TRACK_M} m onto it, widening {MOUTH_FLARE_M} m "
                     f"each side over the last {MOUTH_FLARE_LEN_M} m; {MOUTH_SPILL_M} m "
                     "past the block edge where the cross street has no track. Cut "
                     f"where a committed footprint grown by {CLEAR_M} m stands across "
                     "it. Reconstructed — bounded by the plat strip and a cart's track.")},
        "lanes": lanes,
        "left_in_turf": [{"alley_of": x, "why": "no structure stands on this block on "
                          "the scene date, so nothing wears its alley"} for x in left_turf],
        "cut_by_structures": cuts,
        "research_note": ("Generated. The strip is read from the plat model the lots, the "
                          "fences and the yard outbuildings all read, so the lane cannot "
                          "disagree with the lot lines about where the alley is."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rec = build()
    text = re.sub(r"\[\s+(-?[\d.]+),\s+(-?[\d.]+)\s+\]", r"[\1, \2]",
                  json.dumps(rec, indent=1)) + "\n"
    listed = {e.get("id") for e in load(INDEX).get("enclosures", [])}
    cw = [i for i, r in enumerate(rec["ground"]["interior_local_enu_m"]) if _area2(r) <= 0]
    if cw:
        print(f"ALLEY LANES: rings {cw} are not counter-clockwise; yards.js would cull them")
        return 1
    if rec["id"] not in listed:
        print(f"ALLEY LANES: {INDEX.relative_to(ROOT)} does not list {rec['id']}")
        return 1
    summary = (f"{len(rec['lanes'])} alleys drawn as lanes "
               f"({sum(x['drawn_m'] for x in rec['lanes']):.0f} m, "
               f"{len(rec['ground']['interior_local_enu_m'])} rings), "
               f"{len(rec['left_in_turf'])} left in turf, "
               f"{len(rec['cut_by_structures'])} cut by a structure")
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"ALLEY LANE DRIFT\n  - {OUT.relative_to(ROOT)} does not re-derive; run "
                  "python3 tools/generate_alley_lanes.py")
            return 1
        print(f"alley lanes: {summary}")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {summary}")
    for c in rec["cut_by_structures"]:
        print(f"  cut: {c['alley_of']} by {c['structure_id']} "
              f"{c['from_m']}..{c['to_m']} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
