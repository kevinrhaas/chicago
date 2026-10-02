#!/usr/bin/env python3
"""The graded street section (T-1812): is every opened street's bed below its walks?

    python3 tools/check_street_section.py                 the report, street by street
    python3 tools/check_street_section.py --section south_water@500
                                                          one measured cross-section
    python3 tools/check_street_section.py --gate          exit 1 on any failure, quietly

`generators/terrain_gen.py` lowers the worked roadway of every opened street below
the ground its walks stand on, by the numbers in the 1835 terrain spec's
`street_sections` block. Two things can quietly undo that, and this is the check
for both:

1. **The painted road and the graded road are one width.** The renderer sizes the
   worked earth by `WORKED_SHARE` in `renderers/web/js/streets.js` (T-1811) and the
   generator by each class's `worked_share` in the spec. They are two copies of one
   number, so they are read here and must agree; if they drift, the road is painted
   on the shelf or the bed is cut under the grass.
2. **The committed heightfield actually carries the section.** Along each graded
   street, every 10 m, the ground on the line is compared with the ground just
   outside the worked width on both sides (their mean, so a natural cross-fall
   cancels). Away from crossings, bridge approaches, structures the spec keeps
   clear and the water, the median of that depth must be at least half the class's
   crown depth, on every street with at least MIN_STATIONS of them. A street the
   cut never reached — a stale heightfield, a dropped class — reads as zero and
   fails. A single station whose bed reads ABOVE its shelf is reported, not
   failed: the two-sided mean cancels a cross-fall but not a crest, and on a bank
   brow or the sand ridge the natural ground's own curvature outweighs a 0.1 m
   cut. The median is the claim; the outliers are where to look.

Pure Python; it reads the committed files and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

from heightfield import Heightfield  # noqa: E402
from terrain_gen import street_lines  # noqa: E402

EPOCH = "e1834_harbor_cut"
STREETS_JS = ROOT / "renderers" / "web" / "js" / "streets.js"
STATION_M = 10.0
SHELF_OUT_M = 1.0       # the shelf is read this far outside the worked edge
CROSSING_CLEAR_M = 14.0  # a station this near another graded street is a crossing
APPROACH_CLEAR_M = 6.0
MIN_STATIONS = 5
LATTICE_M = 0.005
FT = 0.3048


def worked_share_js() -> dict[str, float]:
    text = STREETS_JS.read_text()
    m = re.search(r"const WORKED_SHARE = \{([^}]*)\}", text)
    if not m:
        return {}
    return {k: float(v) for k, v in re.findall(r"(\w+):\s*([0-9.]+)", m.group(1))}


def seg_dist(e, n, pts):
    best = math.inf
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((e - ax) * dx + (n - ay) * dy) / l2))
        best = min(best, math.hypot(e - ax - t * dx, n - ay - t * dy))
    return best


def stations(pts, step):
    """(e, n, ue, un) every `step` metres along a polyline, unit tangent included."""
    out = []
    carry = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        if seg < 1e-9:
            continue
        ue, un = (bx - ax) / seg, (by - ay) / seg
        s = carry
        while s < seg:
            out.append((ax + ue * s, ay + un * s, ue, un))
            s += step
        carry = s - seg
    return out


def measure(hf, spec, streets):
    ss = spec["street_sections"]
    lines = street_lines(streets, ss)
    classes = {c["traffic"]: c for c in ss["classes"]}
    approaches = [[(float(p[0]), float(p[1])) for p in ap["line"]]
                  for ap in spec.get("approaches", [])]
    keep = ss.get("keep_clear", [])
    report = []
    for st in lines:
        others = [o["line"] for o in lines if o["id"] != st["id"]]
        crown_m = classes[st["traffic"]]["crown_depth_ft"] * FT
        depths = []
        above = []
        for e, n, ue, un in stations(st["line"], STATION_M):
            if any(seg_dist(e, n, o) < CROSSING_CLEAR_M for o in others):
                continue
            if any(seg_dist(e, n, a) < APPROACH_CLEAR_M for a in approaches):
                continue
            if any(math.hypot(e - k["e"], n - k["n"]) < k["outer_m"] + st["half_m"]
                   for k in keep):
                continue
            off = st["half_m"] + SHELF_OUT_M
            pts = [(e, n), (e - un * off, n + ue * off), (e + un * off, n - ue * off)]
            if not all(hf.covers(pe, pn) for pe, pn in pts):
                continue
            centre, left, right = (hf.height(pe, pn) for pe, pn in pts)
            if min(centre, left, right) <= 0.0:
                continue
            depth = 0.5 * (left + right) - centre
            depths.append(depth)
            if depth < -LATTICE_M:
                above.append((round(e, 1), round(n, 1), round(depth, 3)))
        report.append({
            "id": st["id"], "traffic": st["traffic"], "half_m": round(st["half_m"], 2),
            "stations": len(depths), "crown_m": round(crown_m, 3),
            "median_m": round(statistics.median(depths), 3) if depths else None,
            "min_m": round(min(depths), 3) if depths else None,
            "above": above,
        })
    return report


def section(hf, spec, streets, street_id, at_e):
    st = next(s for s in street_lines(streets, spec["street_sections"]) if s["id"] == street_id)
    best = None
    for e, n, ue, un in stations(st["line"], 0.5):
        if best is None or abs(e - at_e) < abs(best[0] - at_e):
            best = (e, n, ue, un)
    e, n, ue, un = best
    print(f"{street_id} at E {e:+.1f} N {n:+.1f} — worked half-width {st['half_m']:.2f} m; "
          f"offsets are to the left of the line's direction (+) and right (-)")
    print("  offset_m   ground_m   below_shelf_m")
    corridor = 12.192
    shelf = 0.5 * (hf.height(e - un * corridor, n + ue * corridor)
                   + hf.height(e + un * corridor, n - ue * corridor))
    for k in range(-26, 27):
        d = k * 0.5
        g = hf.height(e - un * d, n + ue * d)
        print(f"  {d:+7.1f}   {g:7.3f}   {shelf - g:+7.3f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--section", default=None, help="street_id@easting")
    args = ap.parse_args()

    ep = ROOT / "data" / "terrain" / "epochs" / EPOCH
    spec = json.loads((ep / "terrain_spec.json").read_text())
    ss = spec.get("street_sections")
    if not ss:
        print("FAIL the 1835 terrain spec has no street_sections block")
        return 1
    streets = json.loads((ROOT / ss["streets_file"]).read_text())
    hf = Heightfield.load(ep)
    if hf is None:
        print("FAIL no committed heightfield to measure")
        return 1

    if args.section:
        sid, at = args.section.split("@")
        section(hf, spec, streets, sid, float(at))
        return 0

    bad = []
    js = worked_share_js()
    for c in ss["classes"]:
        if js.get(c["traffic"]) != float(c["worked_share"]):
            bad.append(f"{c['traffic']}: the spec grades {c['worked_share']} of the corridor "
                       f"and streets.js paints {js.get(c['traffic'])}")
    report = measure(hf, spec, streets)
    for r in report:
        if not r["stations"]:
            continue
        if r["stations"] >= MIN_STATIONS and r["median_m"] < 0.5 * r["crown_m"]:
            bad.append(f"{r['id']}: the bed's median depth below its shelf is {r['median_m']} m "
                       f"over {r['stations']} station(s), under half the {r['crown_m']} m crown")
    measured = [r for r in report if r["stations"]]
    if not args.gate or bad:
        print(f"graded street section — {len(report)} opened street(s), {len(measured)} with "
              f"a measurable station (a station off a crossing, an approach, a kept-clear "
              f"structure and the water)")
        print("  street               class      half_m  stations  median_m  min_m")
        for r in report:
            print(f"  {r['id']:<20} {r['traffic']:<9} {r['half_m']:7.2f}  {r['stations']:8d}  "
                  f"{r['median_m'] if r['median_m'] is not None else '-':>8}  "
                  f"{r['min_m'] if r['min_m'] is not None else '-':>6}")
        above = sum(len(r["above"]) for r in report)
        print(f"  {above} station(s) read the bed above its shelf — natural crests the cut "
              f"does not outweigh: "
              + ", ".join(f"{r['id']} ({len(r['above'])})" for r in report if r["above"]))
    for b in bad:
        print(f"FAIL {b}")
    if not bad:
        print(f"STREET SECTION PASS — {len(measured)} street(s) graded below their walks; "
              f"spec and streets.js agree on the worked width")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
