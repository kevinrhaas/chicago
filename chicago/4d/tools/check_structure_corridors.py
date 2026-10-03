#!/usr/bin/env python3
"""No building is newly drawn standing in ANY street corridor — the fort road included.

T-1743. The owner reported the Beaubien homestead as three identical log houses by the
fort, two of them standing on the fort road. They were: T-1712 placed
`beaubien_new_residence` and `beaubien_trading_post` 17.9 m east of the house, by eye, and
that easting is the centreline of `fort_road`, which `data/streets/1835.json` had already
drawn north to the fort's south gate. Both stood 0.0 m from the centreline. Nothing asked,
because the two corridor gates this project has both ask a narrower question:

* `measure_corridor_intrusion.py` measures the PLATTED corridors — the block grid and the
  tracts `generate_plat_lots.corridor_rings` builds, on the control line. `fort_road` is
  not platted (the reservation carried no plat in 1835), so it is not in that layer, and
  neither are the 34 other streets drawn off the grid: the school section's lines, the
  river roads, the north tract's alleys.
* every generator asks `plat_corridors.intrusion()` before it places a roof — the same
  platted layer, so a building a PERSON placed beside an unplatted road was never asked.

**This asks it of every street in `data/streets/1835.json`, at the width the street's own
record declares**, against every structure phase standing on the layer's `target_date`.
The corridor is the DRAWN centreline buffered square to each segment, flat at the drawn
ends (a corridor is only as long as the line this project committed), with the joins at
interior vertices filled. That is the drawn line in `docs/CORRIDOR-LINES.md`'s terms: the
question is whether a visitor walking the road as drawn walks into a wall.

**It is a ratchet, not an absolute, and the reason is measured.** On 2026-10-03, with the
Beaubien pair moved off the road, 48 phases of 41 records lap some corridor — most of them
buildings on `north_water`, whose drawn line runs along the bank the North Side's oldest
houses were placed on from sources. "A position with a source outranks a corridor
this project derived" (`measure_corridor_intrusion`), so those are banked here with their
depth, not moved. What the gate refuses:

* a lap that is not banked — a building newly drawn in a street, or a street newly drawn
  through a building;
* a banked lap that DEEPENS by more than a centimetre;
* a banked lap that has CLEARED, until the baseline is re-written, so the ratchet only
  ever tightens and a cleared building cannot walk back in silently.

    tools/check_structure_corridors.py                  the table
    tools/check_structure_corridors.py --gate           the ratchet check.sh runs
    tools/check_structure_corridors.py --self-test      break it three ways
    tools/check_structure_corridors.py --write-baseline only to record a repair
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STREETS = DATA / "streets" / "1835.json"
STRUCTURES = DATA / "structures"
DATUM = DATA / "datum.json"
BASELINE = ROOT / "tools" / "structure_corridor_baseline.json"

# Footprint edges are sampled at this pitch. The narrowest corridor drawn is a few metres
# wide and no footprint edge is shorter than this, so a lap cannot fall between samples.
SAMPLE_M = 0.25
# Depths are quoted, banked and compared to the centimetre: the footprint and the corridor
# are both derived, and the last millimetre is arithmetic rather than evidence.
PLACES = 2
TOLERANCE_M = 0.01


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def world_polygon(phase: dict, datum: dict) -> list:
    """The same transform as `plat_occupancy.world_polygon`, restated so this gate imports
    nothing that reads a corridor layer of its own."""
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def _ring_samples(poly: list, pitch: float) -> list:
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        steps = max(1, int(math.dist(a, b) / pitch))
        out += [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
                for k in range(steps)]
    return out


def _line_samples(points: list, pitch: float) -> list:
    out = []
    for a, b in zip(points, points[1:]):
        steps = max(1, int(math.dist(a, b) / pitch))
        out += [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps)
                for k in range(steps + 1)]
    return out


def _inside(point: tuple, poly: list) -> bool:
    x, y = point
    hit = False
    for i, (ax, ay) in enumerate(poly):
        bx, by = poly[(i + 1) % len(poly)]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            hit = not hit
    return hit


def depth_into(poly: list, line: list, half_width: float) -> float:
    """How far into a corridor a footprint's worst point stands, in metres (0 if clear).

    Measured from the corridor's edge, so a building whose wall touches the edge reads 0
    and one astride the centreline reads the whole half-width.
    """
    worst = 0.0
    for p in _ring_samples(poly, SAMPLE_M):
        for a, b in zip(line, line[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            span = dx * dx + dy * dy
            if span == 0:
                continue
            t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / span
            if 0.0 <= t <= 1.0:
                off = math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
                worst = max(worst, half_width - off)
        for v in line[1:-1]:
            worst = max(worst, half_width - math.dist(p, v))
    # a road running clean through a footprint wider than the corridor touches no sampled
    # wall point inside it, so ask the other way round too
    if any(_inside(q, poly) for q in _line_samples(line, 0.5)):
        worst = max(worst, half_width)
    return worst


def standing(structures: dict, target: str):
    """(structure_id, phase_id, phase) for every phase standing on the target date."""
    for sid in sorted(structures):
        record = structures[sid]
        for phase in record.get("phases") or []:
            pos = phase.get("position") or {}
            poly = (phase.get("footprint") or {}).get("polygon") or []
            if pos.get("utm_e") is None or len(poly) < 3:
                continue
            rng = phase.get("documented_range") or {}
            if not str(rng.get("from") or "0000") <= target <= str(rng.get("to") or "9999"):
                continue
            yield sid, phase["id"], phase


def laps(structures: dict | None = None, streets: dict | None = None,
         datum: dict | None = None) -> list[dict]:
    structures = structures if structures is not None else {
        p.stem: load(p) for p in sorted(STRUCTURES.glob("*.json"))}
    streets = streets or load(STREETS)
    datum = datum or load(DATUM)
    default = float(streets.get("corridor_width_m", 24.384))
    lines = []
    for street in streets["streets"]:
        pts = [(float(e), float(n)) for e, n in street["path_local_enu_m"]]
        half = float(street.get("corridor_width_m", default)) / 2.0
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box = (min(xs) - half, max(xs) + half, min(ys) - half, max(ys) + half)
        lines.append((street["id"], pts, half, box))
    rows = []
    for sid, pid, phase in standing(structures, streets["target_date"]):
        poly = world_polygon(phase, datum)
        px, py = [p[0] for p in poly], [p[1] for p in poly]
        for street_id, pts, half, (x0, x1, y0, y1) in lines:
            if max(px) < x0 or min(px) > x1 or max(py) < y0 or min(py) > y1:
                continue
            d = round(depth_into(poly, pts, half), PLACES)
            if d > 0:
                rows.append({"structure": sid, "phase": pid, "street": street_id,
                             "depth_m": d})
    return rows


def key(row: dict) -> str:
    return f"{row['structure']}.{row['phase']} in {row['street']}"


def verdict(rows: list[dict], banked: dict) -> list[str]:
    faults = []
    seen = set()
    for row in rows:
        k = key(row)
        seen.add(k)
        if k not in banked:
            faults.append(f"{k}: {row['depth_m']:.2f} m inside the corridor, and not banked "
                          f"— a building newly drawn standing in a street")
        elif row["depth_m"] > banked[k] + TOLERANCE_M:
            faults.append(f"{k}: {row['depth_m']:.2f} m deep, banked at {banked[k]:.2f} m "
                          f"— it has moved further into the street")
    for k in sorted(set(banked) - seen):
        faults.append(f"{k}: banked at {banked[k]:.2f} m and now CLEAR — re-write the "
                      f"baseline (--write-baseline) so the ratchet keeps the gain")
    return faults


def banked() -> dict:
    return {k: float(v) for k, v in load(BASELINE)["laps"].items()}


def self_test() -> int:
    structures = {p.stem: load(p) for p in sorted(STRUCTURES.glob("*.json"))}
    streets, datum, bank = load(STREETS), load(DATUM), banked()
    checks = []

    checks.append(("the committed tree passes", not verdict(laps(structures, streets, datum), bank)))

    # T-1712's place for the trading post, which is T-1743's whole fault: on the fort road.
    moved = copy.deepcopy(structures)
    pos = moved["beaubien_trading_post"]["phases"][0]["position"]
    pos["utm_e"], pos["utm_n"] = 448217.7, 4637554.3
    faults = verdict(laps(moved, streets, datum), bank)
    checks.append(("the trading post put back on the fort road is refused",
                   any("beaubien_trading_post" in f and "fort_road" in f for f in faults)))

    # a banked lap a metre deeper than its bank, asked by lowering the bank instead of
    # moving a sourced building
    first = sorted(bank)[0]
    worst = verdict(laps(structures, streets, datum), {**bank, first: bank[first] - 1.0})
    checks.append((f"a lap one metre deeper than banked is refused ({first})",
                   any(f.startswith(first) and "further into" in f for f in worst)))

    # a banked lap that has cleared is refused until re-banked
    stale = verdict(laps(structures, streets, datum),
                    {**bank, "nonexistent.phase in fort_road": 1.0})
    checks.append(("a banked lap that has cleared is refused until re-banked",
                   any("now CLEAR" in f for f in stale)))

    bad = [label for label, ok in checks if not ok]
    for label, ok in checks:
        print(f"{'ok  ' if ok else 'FAIL'} {label}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    rows = laps()
    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "_doc": ("Banked by tools/check_structure_corridors.py --write-baseline (T-1743). "
                     "Every structure phase standing on the 1835 street layer's target date "
                     "whose footprint laps a street corridor at that street's declared width, "
                     "with its depth in metres. A ratchet: re-write only to record a repair."),
            "laps": {key(r): r["depth_m"] for r in sorted(rows, key=key)},
        }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"banked {len(rows)} lap(s) in {BASELINE.relative_to(ROOT)}")
        return 0
    if args.gate:
        faults = verdict(rows, banked())
        for f in faults:
            print(f"FAIL {f}")
        if faults:
            return 1
        print(f"no building is newly drawn in a street corridor: {len(rows)} banked lap(s) "
              f"across {len({r['structure'] for r in rows})} record(s), none deeper")
        return 0
    for r in sorted(rows, key=lambda r: -r["depth_m"]):
        print(f"{r['depth_m']:6.2f} m  {r['structure']}.{r['phase']}  in {r['street']}")
    print(f"{len(rows)} lap(s) across {len({r['structure'] for r in rows})} record(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
