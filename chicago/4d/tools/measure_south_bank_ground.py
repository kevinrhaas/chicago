#!/usr/bin/env python3
"""Is there ground on the south bank at the Dearborn reach a building could stand on?

T-0134. The plate the town was built from here — image 3 of the owner's brief of
2026-08-18 — draws low warehouses on BOTH banks of the reach below the drawbridge.
T-0133 built the north side, four freight sheds standing back from North Water Street,
and left the south side empty with a sentence in every one of their records: the
platted South Water Street corridor reaches to within about 1.7 m of the traced 1834
waterline, so there is no ground there that is not the street.

That sentence was one spot reading taken by hand at one station, and the whole south
bank of the reach was refused on it. This is the reading as a command, over the whole
reach and at every tolerance the refusal could turn on, so the refusal reproduces —
and so it FAILS the day the ground changes and the question is genuinely open again.

**What it asks.** Over the south bank from the Dearborn crossing east to the United
States Reservation's west line, can the smallest footprint family F1 allows — 18 x 32 ft,
the freight shed of the plate — be put down at all, on ground that is

* above the water surface in the committed heightfield (`WATER_SURFACE_M`, the same
  zero `measure_no_build_ground.py` uses),
* outside every platted street corridor (`plat_corridors`, the module the placement
  gate itself asks), and
* off the refused ground of the Reservation and the sand bar
  (`measure_no_build_ground`, so the two answers cannot disagree).

**Every bound is the permissive one, on purpose.** A refusal is only worth having if it
survives the most generous reading of its own inputs: the rectangle may stand at ANY
bearing rather than square to the street, it is the SMALLEST the family allows rather
than the median, dry means one millimetre above the water rather than a freeboard, and
the relief clause is reported at the generators' own 0.30 m, at the 0.35 m the north
bank sheds quoted, at a metre, and with no relief clause at all. If the answer is still
zero with the clause switched off, the finding does not rest on the clause.

**A corridor is not the travelled way** — L79, and `plat_corridors` says so at length.
This tool does not decide whether a building may stand inside the legal corridor; that
question is the ticket's, and the ticket's answer is written up in
`docs/RESEARCH/south_bank_dearborn_ground.md`. What this measures is the narrower and
purely physical half: whether the question can be side-stepped by finding ground
outside the corridor. It cannot.

    tools/measure_south_bank_ground.py            the table
    tools/measure_south_bank_ground.py --gate     the ratchet check.sh runs
    tools/measure_south_bank_ground.py --self-test   the assertions still fire
    tools/measure_south_bank_ground.py --json     the readings, machine-readable
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from heightfield import Heightfield  # noqa: E402
from measure_no_build_ground import (  # noqa: E402
    EPOCH, WATER_SURFACE_M, bar_ring, inside, reservation_ring,
)
from plat_corridors import corridors, intrusion  # noqa: E402

BASELINE = ROOT / "tools" / "south_bank_ground_baseline.json"
DATA = ROOT / "data"

# THE REACH. Its west end is the Dearborn Street drawbridge — the crossing the plate is
# drawn from and the thing that makes this reach the one the plate shows. Its east end is
# the Reservation's west line, because east of that the ground was never open to a private
# builder and `measure_no_build_ground.py` already refuses it. Both are RESOLVED from
# committed records below rather than typed here, for the reason `data/datum.json` is
# re-derived rather than stored: a typed vertex cannot be wrong loudly.
BRIDGE = "dearborn_street_drawbridge"
# The north edge of the box. The south bank's ground and the river are both under it; the
# NORTH bank is not, and that is the whole job of this number — the north shore of the main
# stem at this reach stands past local N 90, so a rectangle cannot wander across the water
# and report itself as south-bank ground. It is not a claim about where the bank is.
BOX_N_M = 45.0
BOX_S_M = 0.0

# The smallest footprint family F1 — freight or storage shed — is allowed, from the
# reconstruction spec's own band, in feet. The smallest, because a refusal has to refuse
# the easiest case.
INVENTORY = DATA / "reconstruction" / "1835_building_inventory.json"
FAMILY = "F1"
FT_M = 0.3048

# The sweep. A half-metre mask and a metre of position step is finer than the 2.5 m
# heightfield cell the ground itself is committed at, so the grid is not what decides this.
MASK_M = 0.5
STEP_M = 1.0
BEARING_STEP_DEG = 15

# The relief clauses this is reported at. 0.30 is `generate_block_infill.MAX_RELIEF_M`,
# the walker's step tolerance three infill generators hold themselves to; 0.35 is the
# figure the north bank sheds' own notes quote; 1.00 and None are there so the finding
# can be seen not to rest on either.
RELIEF_TOLERANCES = [0.30, 0.35, 1.00, None]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def reach() -> tuple[float, float]:
    """(west, east) of the reach in local ENU metres, resolved from committed records."""
    datum = load(DATA / "datum.json")
    bridge = load(DATA / "structures" / f"{BRIDGE}.json")
    placed = [p for p in bridge["phases"] if (p.get("position") or {}).get("utm_e")]
    if not placed:
        raise SystemExit(f"{BRIDGE} carries no placed phase; the reach has no west end")
    west = float(placed[0]["position"]["utm_e"]) - float(datum["origin_utm_e"])
    ring, _, _ = reservation_ring()
    # The Reservation's west line is its westernmost edge; where that line meets this
    # bank is the east end of the reach.
    east = min(e for e, n in ring if BOX_S_M <= n <= BOX_N_M)
    if not (west < east):
        raise SystemExit(f"the reach reads backwards: {west:.1f} to {east:.1f}")
    return west, east


def platted_end() -> float:
    """The east end of South Water Street's committed platted line, in local ENU.

    The reach runs past it. West of this the question is "is there ground outside the
    street"; east of it there IS no street, and ground there answers a different
    question — which is why the two are reported apart rather than averaged into one
    count that would read as ground the plate's warehouses could have used.
    """
    for street in load(DATA / "streets" / "1835.json")["streets"]:
        if street["id"] == "south_water":
            return float(street["path_local_enu_m"][-1][0])
    raise SystemExit("data/streets/1835.json no longer carries south_water")


def footprint_m() -> tuple[float, float]:
    """The smallest F1 footprint the reconstruction spec allows, in metres."""
    bands = load(INVENTORY)["family_bands_ft"]
    if FAMILY not in bands:
        raise SystemExit(f"the inventory carries no band for family {FAMILY}")
    # `[lo_w, lo_d, hi_w, hi_d]`, the order `generate_inferred_infill.dimensions` reads.
    w_lo, d_lo, _, _ = bands[FAMILY]
    return round(w_lo * FT_M, 4), round(d_lo * FT_M, 4)


class Ground:
    """Is a point buildable at all — dry, out of the roadway, and not refused ground."""

    def __init__(self) -> None:
        self.hf = Heightfield.load(EPOCH)
        if self.hf is None:
            raise SystemExit("the 1834 epoch carries no committed heightfield")
        self.lanes = corridors()
        ring, _, _ = reservation_ring()
        self.refused = [ring, bar_ring()]

    def height(self, e: float, n: float) -> float | None:
        return self.hf.height(e, n) if self.hf.covers(e, n) else None

    def free(self, e: float, n: float) -> bool:
        h = self.height(e, n)
        if h is None or h <= WATER_SURFACE_M:
            return False
        if intrusion([(e, n)], self.lanes)[0] is not None:
            return False
        return not any(inside((e, n), ring) for ring in self.refused)


def strip(ground: Ground, west: float, east: float) -> list[dict]:
    """Per station, the run of buildable ground on the river side of the corridor."""
    rows = []
    e = west
    while e <= east + 1e-9:
        run, best = [], []
        n = BOX_S_M
        while n <= BOX_N_M + 1e-9:
            if ground.free(e, n):
                run.append(n)
            else:
                if len(run) > len(best):
                    best = run
                run = []
            n += MASK_M
        if len(run) > len(best):
            best = run
        if best:
            heights = [ground.height(e, n) for n in best]
            rows.append({"e": round(e, 1), "n_from": round(best[0], 2),
                         "n_to": round(best[-1], 2),
                         "width_m": round(best[-1] - best[0] + MASK_M, 2),
                         "relief_m": round(max(heights) - min(heights), 2)})
        else:
            rows.append({"e": round(e, 1), "n_from": None, "n_to": None,
                         "width_m": 0.0, "relief_m": None})
        e += STEP_M
    return rows


def fits(ground: Ground, west: float, east: float,
         width: float, depth: float) -> list[dict]:
    """Every position and bearing at which the smallest F1 footprint would stand.

    The rectangle is sampled on a half-metre lattice INCLUDING its corners, because a
    footprint whose middle is dry and whose corner is in the river is not a building.
    """
    out = []
    us = [i * MASK_M for i in range(int(width / MASK_M) + 1)]
    vs = [i * MASK_M for i in range(int(depth / MASK_M) + 1)]
    us = sorted(set(us + [width]))
    vs = sorted(set(vs + [depth]))
    bearings = [math.radians(d) for d in range(0, 180, BEARING_STEP_DEG)]
    e0 = west
    while e0 <= east + 1e-9:
        n0 = BOX_S_M
        while n0 <= BOX_N_M + 1e-9:
            for theta in bearings:
                cos, sin = math.cos(theta), math.sin(theta)
                heights, ok = [], True
                for u in us:
                    for v in vs:
                        e = e0 + u * cos - v * sin
                        n = n0 + u * sin + v * cos
                        if not (west - width - depth <= e <= east + width + depth):
                            ok = False
                            break
                        if not ground.free(e, n):
                            ok = False
                            break
                        heights.append(ground.height(e, n))
                    if not ok:
                        break
                if ok:
                    out.append({"e": round(e0, 1), "n": round(n0, 1),
                                "bearing_deg": round(math.degrees(theta), 1),
                                "relief_m": round(max(heights) - min(heights), 3)})
            n0 += STEP_M
        e0 += STEP_M
    return out


def measure() -> dict:
    west, east = reach()
    width, depth = footprint_m()
    ground = Ground()
    rows = strip(ground, west, east)
    placements = fits(ground, west, east, width, depth)
    widest = max(rows, key=lambda r: r["width_m"])
    end = platted_end()
    platted_rows = [r for r in rows if r["e"] <= end]
    widest_platted = max(platted_rows, key=lambda r: r["width_m"])

    def counted(subset):
        out = {}
        for tol in RELIEF_TOLERANCES:
            key = "none" if tol is None else f"{tol:.2f}"
            out[key] = sum(1 for p in subset if tol is None or p["relief_m"] <= tol)
        return out

    by_tolerance = counted(placements)
    on_street = counted([p for p in placements if p["e"] <= end])
    return {
        "reach": {"west_m": round(west, 2), "east_m": round(east, 2),
                  "west_is": BRIDGE, "east_is": "the Reservation's west line"},
        "footprint_m": {"width": width, "depth": depth, "family": FAMILY},
        "widest_free_strip": widest,
        "free_stations": sum(1 for r in rows if r["width_m"] > 0),
        "stations": len(rows),
        "fits": by_tolerance,
        "platted_end_m": round(end, 2),
        "widest_free_strip_beside_the_street": widest_platted,
        "fits_beside_the_street": on_street,
        "strip": rows,
    }


def report(result: dict, json_out: bool = False) -> str:
    if json_out:
        return json.dumps(result, indent=1)
    r, f = result["reach"], result["footprint_m"]
    widest = result["widest_free_strip"]
    lines = [
        f"   the south bank from {r['west_is']} (local E {r['west_m']:.1f}) east to "
        f"{r['east_is']} (E {r['east_m']:.1f})",
        f"   {result['free_stations']} of {result['stations']} stations carry ANY dry "
        f"ground outside a platted corridor",
        f"   the widest such strip is {widest['width_m']:.2f} m, at E {widest['e']:.1f} "
        f"(N {widest['n_from']} to {widest['n_to']}, {widest['relief_m']:.2f} m of relief)",
        f"   the smallest footprint family {f['family']} allows is "
        f"{f['width']:.3f} x {f['depth']:.3f} m; positions it would stand at, "
        f"at any bearing:",
    ]
    for key, count in result["fits"].items():
        clause = "no relief clause" if key == "none" else f"relief <= {key} m"
        lines.append(f"      {clause:<22} {count}")
    beside = result["widest_free_strip_beside_the_street"]
    lines += [
        f"   BESIDE THE PLATTED STREET — west of South Water's own east end "
        f"(E {result['platted_end_m']:.1f}), which is the frontage the plate draws:",
        f"      the widest free strip is {beside['width_m']:.2f} m, at E {beside['e']:.1f}",
    ]
    for key, count in result["fits_beside_the_street"].items():
        clause = "no relief clause" if key == "none" else f"relief <= {key} m"
        lines.append(f"      {clause:<22} {count}")
    return "\n".join(lines)


def gate(quiet: bool = False) -> int:
    result = measure()
    baseline = load(BASELINE)
    failures: list[str] = []

    for key, count in result["fits"].items():
        was = baseline["fits"].get(key)
        if was is None:
            failures.append(f"the baseline carries no reading at relief {key}")
        elif count != was:
            failures.append(
                f"the smallest F1 footprint now stands at {count} position(s) with "
                f"relief {key}, and the baseline recorded {was} — T-0134's finding is "
                f"that this reach carries NO ground outside its own street, so a change "
                f"here re-opens the question rather than being a number to update")

    for key, count in result["fits_beside_the_street"].items():
        was = (baseline.get("fits_beside_the_street") or {}).get(key)
        if was is None:
            failures.append(f"the baseline carries no beside-the-street reading at {key}")
        elif count != was:
            failures.append(
                f"beside the platted street the smallest F1 footprint now stands at "
                f"{count} position(s) with relief {key}, and the baseline recorded "
                f"{was} — this is the frontage the plate draws, and a fit appearing "
                f"here is T-0134 re-opening")

    for field in ("widest_free_strip", "widest_free_strip_beside_the_street"):
        widest = result[field]["width_m"]
        was = baseline[field]["width_m"]
        if abs(widest - was) > 0.01:
            failures.append(f"{field} moved {was:.2f} -> {widest:.2f} m; re-read the "
                            f"finding before banking it")

    if not quiet or failures:
        print(report(result))
    for line in failures:
        print(f"   {line}")
    return 1 if failures else 0


def self_test() -> int:
    """The assertions still fire when the ground under them moves."""
    problems = []
    ground = Ground()
    west, east = reach()
    width, depth = footprint_m()

    # 1. A rectangle standing in the middle of the river is refused.
    wet = fits(ground, 760.0, 760.0, width, depth)
    if any(p for p in wet if p["n"] > 30):
        problems.append("a footprint standing in open water was accepted")

    # 2. The sweep is not vacuous: the same rectangle DOES stand on the plateau south of
    #    the corridor, which is where the town's own South Water frontage is built.
    class Unplatted(Ground):
        def free(self, e, n):
            h = self.height(e, n)
            return h is not None and h > WATER_SURFACE_M
    loose = fits(Unplatted(), 770.0, 780.0, width, depth)
    if not loose:
        problems.append("with the corridor rule off, nothing fits anywhere on the "
                        "reach — the sweep is refusing for the wrong reason")

    # 3. The reach's own ends are resolved, not typed.
    if not (west < east):
        problems.append("the reach does not read west to east")

    for line in problems:
        print(f"   {line}")
    if not problems:
        print("   3 assertions fire")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true", help="the ratchet check.sh runs")
    parser.add_argument("--self-test", action="store_true", dest="self_test",
                        help="the assertions still fire")
    parser.add_argument("--json", action="store_true", help="machine-readable")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--write-baseline", action="store_true", dest="write",
                        help="record the reading, only when the finding is re-read")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.gate:
        return gate(quiet=args.quiet)
    result = measure()
    if args.write:
        payload = {k: v for k, v in result.items() if k != "strip"}
        payload["$note"] = (
            "T-0134. The reading this project's refusal of the plate's south-bank "
            "warehouses stands on. Written by "
            "tools/measure_south_bank_ground.py --write-baseline, and only when the "
            "finding has been re-read: a fit appearing on this reach is the question "
            "re-opening, not a number to bank."
        )
        BASELINE.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        print(f"   wrote {BASELINE.relative_to(ROOT)}")
    print(report(result, json_out=args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
