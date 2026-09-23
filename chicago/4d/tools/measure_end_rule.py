#!/usr/bin/env python3
"""What the end rule can actually tell apart on a block face, under either criterion.

ROADMAP K31, ticket T-0023. The END RULE is this programme's answer to "which of the
roofs a block was dealt goes where along its frontage": the better roof stands nearer
the Dearborn Street drawbridge, the only crossing of the main stem in July 1835. T-A8,
T-A9 and T-A10 asserted it as a compass direction; T-A11 replaced the compass with a
measurement — STRAIGHT-LINE distance from the lot to the bridge — and every block since
has quoted that criterion.

**It has thinned on every block since it was written, and T-A15 declared it exhausted**:
2.93x at T-A12, 1.13x at T-A13, 1.11x at T-A14, 1.02x at T-A15, where it separated
three lots of `blk_randolph_clark` by 7.5 m. K31 opened on the successor question and
warned that the answer must not be picked on a block where the candidates agree.

This is the command K31 asked for: it prints the number, so the next block parcel
inherits the decision instead of re-arguing it. **What it measured, on the whole
platted grid: the straight line falls below the floor on 12 of the 36 block faces —
including the back face of the block the rule was written on — and the two criteria
name the same nearest lot on 36 of 36. The rule's ORDER was never in doubt; only
whether it could still be called reasoned.** T-0023 decided it on those numbers and
the recipe's `placement_rule.end_rule` carries the decision.

WHAT IT MEASURES, and why each piece is here.

*Two criteria, side by side.* `straight` is T-A11's, as committed: the distance from a
point on the face to the bridge's south abutment. `network` is the candidate K31 names
first — distance along the committed street centrelines, which is what a resident
actually walked. Neither is evidence about 1835; both are ways of ordering an invention,
and the record says so wherever the rule is applied.

*The point measured is the FRONTAGE, not the lot — and the two parcels that measured
this criterion did not measure the same point.* A roof placed by this programme stands
on its own street frontage, so the frontage is where the criterion should be read.

* **T-A11 read the frontage.** On `blk_south_water_clark` it reported 35.6 / 55.5 /
  78.1 / 101.7 m at lots 6 / 4 / 2 / 0, and 126.3 → 158.2 m on the back street. This
  command reads 34.38 / 53.90 / 76.44 / 99.98 m and 125.97 → 157.25 m: **every one of
  the eight within 1.7 m**, ratio 2.908 against T-A11's 2.86. It reproduces.
* **T-A15 read the lot centroid.** On `blk_randolph_clark` it reported 318.3 / 321.1 /
  325.8 m and L106 names the point in passing — "the 49.3 m between the lot 2 and lot 6
  **centroids**". At the frontage the same three lots read 299.77 / 294.83 / 291.91 m,
  **26.4 m nearer**, which is the 26.5 m from a lot's frontage to its middle. The ORDER
  is the same and the SPREAD, which is what the exhaustion claim rests on, reproduces:
  **7.86 m against T-A15's 7.5 m.**

So the finding T-A15 recorded stands, and the criterion had been read at two points
26.5 m apart on two blocks without either parcel saying which. That is the ordinary
reason a measurement becomes a command.

*The floor is the placement's own declared invention.* A criterion means nothing below
the noise of the thing it is ordering. The recipe's `placement_rule` says in terms that
a setback "is a period typology and not a measurement of this lot", and the setbacks
dealt to principal slots across every committed block parcel span a stated range — read
out of the recipe here rather than typed, so it cannot drift. A setback moves a roof
along the face's outward normal, which on this row points broadly at the bridge, so that
range is admitted positional invention measured along the very axis the criterion grades.
**A criterion whose step between two neighbouring roofs is smaller than that range is
grading its own noise.**

*The step is reported at both scales the rule is asked to work at, and that distinction
is the finding.* Until T-0079 a block carried one principal roof per platted lot, so the
end rule ordered LOTS — about 24.6 m apart. The core density standard retired that
ceiling: a party-line run now stands three units on a single lot, about 6 m apart, and
the rule has been ordering UNITS WITHIN ONE LOT ever since without anyone saying so. The
`unit` column is the step the rule actually has to work with today.

    tools/measure_end_rule.py                      every block of the platted grid
    tools/measure_end_rule.py blk_randolph_clark   one block, both its street faces
    tools/measure_end_rule.py --row randolph       the Randolph-Washington row
    tools/measure_end_rule.py --list               name every lot and both readings
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from block_faces import face_frame, project  # noqa: E402
from plat_occupancy import world_polygon  # noqa: E402

# The mean width of the committed party-line units, from the core density standard's own
# derivation in tools/reconcile_665.py: eighteen units, 5.04 m to 6.75 m, mean 6.072 m.
# It is the step the end rule has between two neighbours inside a run.
PARTY_LINE_UNIT_M = 6.072

BRIDGE_RECORD = "dearborn_street_drawbridge"
BRIDGE_STREET = "dearborn"


# ---------------------------------------------------------------- the bridge

def bridge_abutment() -> tuple[float, float]:
    """The drawbridge's SOUTH abutment, in the scene's local frame.

    The record's own note names it: "the south abutment at the foot of Dearborn on
    South Water Street", and the deck polygon is committed. The abutment is the
    midpoint of the deck's southern edge, derived from that polygon rather than typed
    — the note quotes local E +699.17, N +20.72 for the polygon's own origin corner
    and this lands 1.5 m west of it, on the centre of the same edge.
    """
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    record = json.loads(
        (ROOT / "data" / "structures" / f"{BRIDGE_RECORD}.json").read_text(encoding="utf-8"))
    deck = world_polygon(record["phases"][0], datum)
    south = sorted(deck, key=lambda p: p[1])[:2]
    return ((south[0][0] + south[1][0]) / 2, (south[0][1] + south[1][1]) / 2)


# ---------------------------------------------------------------- the walking network

def _segment_intersection(p1, p2, p3, p4):
    denominator = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(denominator) < 1e-12:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / denominator
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / denominator
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


def chainage(path, point) -> tuple[float, float]:
    """(distance along the polyline to the nearest point on it, distance off it)."""
    best_off, best_run, run = float("inf"), 0.0, 0.0
    for i in range(len(path) - 1):
        (ax, ay), (bx, by) = path[i], path[i + 1]
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        t = 0.0 if length_sq == 0 else max(
            0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy) / length_sq))
        px, py = ax + t * dx, ay + t * dy
        off = math.hypot(point[0] - px, point[1] - py)
        if off < best_off:
            best_off, best_run = off, run + math.hypot(px - ax, py - ay)
        run += math.hypot(dx, dy)
    return best_run, best_off


class StreetNetwork:
    """The committed street centrelines as a walking graph.

    Nodes are (street id, chainage) pairs: one at every crossing of two committed
    centrelines, plus whatever chainages a caller asks about. Edges run along a street
    between consecutive nodes and cost their own length; a crossing joins two streets
    at zero cost, which is the corner a walker turns. Nothing here authors a
    coordinate — every street is `data/streets/1835.json` as committed, and a street
    the dataset does not carry is a street this measurement cannot walk.
    """

    def __init__(self, extra: dict[str, list[float]] | None = None):
        streets = json.loads(
            (ROOT / "data" / "streets" / "1835.json").read_text(encoding="utf-8"))["streets"]
        self.paths = {s["id"]: [tuple(p) for p in s["path_local_enu_m"]] for s in streets}
        self.names = {s["id"]: s.get("name_1835") or s["id"] for s in streets}
        self.chainages = {sid: set() for sid in self.paths}
        self.crossings: list[tuple[str, float, str, float]] = []
        ids = list(self.paths)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                for k in range(len(self.paths[a]) - 1):
                    for m in range(len(self.paths[b]) - 1):
                        point = _segment_intersection(
                            self.paths[a][k], self.paths[a][k + 1],
                            self.paths[b][m], self.paths[b][m + 1])
                        if point is None:
                            continue
                        ca = round(chainage(self.paths[a], point)[0], 4)
                        cb = round(chainage(self.paths[b], point)[0], 4)
                        self.chainages[a].add(ca)
                        self.chainages[b].add(cb)
                        self.crossings.append((a, ca, b, cb))
        for sid, values in (extra or {}).items():
            self.chainages[sid].update(round(v, 4) for v in values)

    def distances_from(self, street: str, at: float) -> dict[tuple[str, float], float]:
        """Walking distance from one point on the network to every node of it."""
        source = (street, round(at, 4))
        self.chainages[street].add(source[1])
        adjacency: dict[tuple[str, float], list[tuple[tuple[str, float], float]]] = {}

        def join(u, v, weight):
            adjacency.setdefault(u, []).append((v, weight))
            adjacency.setdefault(v, []).append((u, weight))

        for sid, values in self.chainages.items():
            ordered = sorted(values)
            for i in range(len(ordered) - 1):
                join((sid, ordered[i]), (sid, ordered[i + 1]), ordered[i + 1] - ordered[i])
        for a, ca, b, cb in self.crossings:
            join((a, ca), (b, cb), 0.0)

        best = {source: 0.0}
        queue = [(0.0, source)]
        while queue:
            cost, node = heapq.heappop(queue)
            if cost > best.get(node, float("inf")):
                continue
            for neighbour, weight in adjacency.get(node, ()):
                stepped = cost + weight
                if stepped < best.get(neighbour, float("inf")):
                    best[neighbour] = stepped
                    heapq.heappush(queue, (stepped, neighbour))
        return best


# ---------------------------------------------------------------- the floor

def declared_setback_range() -> tuple[float, float, int]:
    """(smallest, largest, how many) setback dealt to a principal slot by any block parcel.

    Read out of the recipe rather than typed. The recipe's own `placement_rule` grades
    these as "a period typology and not a measurement of this lot", so their spread is
    the positional invention the programme admits to along the face's outward normal —
    the axis the end rule is grading along.
    """
    recipe = json.loads((ROOT / "data" / "reconstruction"
                         / "1835_platted_block_parcels.json").read_text(encoding="utf-8"))
    setbacks = [float(slot["setback_m"])
                for block in recipe["blocks"]
                for slot in block.get("slots", [])
                if slot.get("inventory_class") == "principal_functional"
                and slot.get("setback_m") is not None]
    if not setbacks:
        raise SystemExit("no principal slot in the recipe declares a setback")
    return min(setbacks), max(setbacks), len(setbacks)


# ---------------------------------------------------------------- the measurement

def frontage_points(block: dict, face: str) -> list[tuple[int, float, tuple[float, float]]]:
    """(lot index, distance along the face, the point) for every lot that reaches this face.

    The point is the midpoint of the lot's own stretch of the block face — where a roof
    dealt to that lot stands, rather than the middle of the lot behind it.
    """
    frame = face_frame(block, face)
    found = []
    for index, lot in enumerate(block.get("lots") or []):
        spans = [project(frame, tuple(p)) for p in lot["polygon"]]
        if max(offset for _, offset in spans) < -0.5:
            continue                                    # this lot is on the other tier
        along = (min(s for s, _ in spans) + max(s for s, _ in spans)) / 2
        found.append((index, along,
                      (frame["origin"][0] + frame["along"][0] * along,
                       frame["origin"][1] + frame["along"][1] * along)))
    return sorted(found, key=lambda f: f[1])


def reading(rows: list[dict], key: str) -> dict:
    """Spread, ratio and the criterion's WORST step between two neighbours.

    The worst step, not the average: a criterion is only as good as the least it can
    tell apart anywhere on the face, and straight-line distance is markedly non-linear
    on the blocks nearest the bridge — the very blocks where it has to work hardest.
    """
    values = [r[key] for r in rows]
    near, far = min(values), max(values)
    steps = [(abs(values[i + 1] - values[i]), rows[i + 1]["along_m"] - rows[i]["along_m"])
             for i in range(len(values) - 1)]
    lot_step, run = min(steps, key=lambda s: s[0]) if steps else (0.0, 1.0)
    return {
        "near": near, "far": far, "spread": far - near,
        "ratio": (far / near) if near else float("inf"),
        "lot_step": lot_step,
        "unit_step": (lot_step / run * PARTY_LINE_UNIT_M) if run else 0.0,
        "nearest_lot": min(rows, key=lambda r: r[key])["lot"],
    }


def measure(block_ids: list[str]):
    blocks = {b["id"]: b for b in json.loads(
        (ROOT / "data" / "traces" / "vectors"
         / "thompson_lots.json").read_text(encoding="utf-8"))["blocks"]}
    bridge = bridge_abutment()

    # Every point the measurement will ask about has to be a node of the graph before
    # the graph is built, so the walk is collected first and routed once.
    plain = StreetNetwork()
    asked: dict[str, list[float]] = {}
    plan = []
    for block_id in block_ids:
        block = blocks.get(block_id)
        if block is None:
            raise SystemExit(f"no committed block called {block_id!r}")
        for face in ("north", "south"):
            street = block["bounded_by"]["north" if face == "north" else "south"]
            if street not in plain.paths:
                continue
            points = frontage_points(block, face)
            if not points:
                continue
            for _, _, point in points:
                asked.setdefault(street, []).append(chainage(plain.paths[street], point)[0])
            plan.append((block_id, face, street, points))

    network = StreetNetwork(extra=asked)
    at, off = chainage(network.paths[BRIDGE_STREET], bridge)
    from_bridge = network.distances_from(BRIDGE_STREET, at)

    out = []
    for block_id, face, street, points in plan:
        rows = []
        for index, along, point in points:
            walked, _ = chainage(network.paths[street], point)
            rows.append({
                "lot": index,
                "along_m": along,
                "straight_m": math.dist(point, bridge),
                "network_m": from_bridge[(street, round(walked, 4))],
            })
        out.append({
            "block": block_id, "face": face, "street": street, "rows": rows,
            "straight": reading(rows, "straight_m"),
            "network": reading(rows, "network_m"),
        })
    return out, bridge, off


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blocks", nargs="*", help="block ids (default: every platted block)")
    parser.add_argument("--row", help="every block whose north face is this street")
    parser.add_argument("--list", action="store_true", help="name every lot and both readings")
    args = parser.parse_args()

    grid = json.loads((ROOT / "data" / "traces" / "vectors"
                       / "thompson_lots.json").read_text(encoding="utf-8"))["blocks"]
    if args.blocks:
        wanted = args.blocks
    elif args.row:
        wanted = [b["id"] for b in grid if b["bounded_by"].get("north") == args.row]
        if not wanted:
            print(f"no committed block fronts {args.row!r} on its north face")
            return 1
    else:
        wanted = [b["id"] for b in grid]

    faces, bridge, off = measure(wanted)
    low, high, count = declared_setback_range()
    floor = high - low

    print("THE END RULE — the better roof stands nearer the Dearborn Street drawbridge.\n")
    print(f"  bridge south abutment  local E {bridge[0]:+.2f}, N {bridge[1]:+.2f} "
          f"({off:.2f} m off the Dearborn centreline)")
    print(f"  party-line unit        {PARTY_LINE_UNIT_M:.3f} m, the committed mean "
          f"(tools/reconcile_665.py)")
    print(f"  the floor              {floor:.2f} m — the range of setbacks the recipe deals "
          f"its {count} principal")
    print(f"                         slots ({low:.1f} m to {high:.1f} m), which it grades a "
          f"typology and not a measurement.\n")
    print("  straight = T-A11's committed criterion.  network = distance walked along the "
          "committed streets.")
    print("  A step at or below the floor is the criterion grading the placement's own "
          "declared invention.\n")

    header = (f"  {'block':28s} {'face':6s} {'criterion':9s} {'spread':>9s} {'ratio':>7s} "
              f"{'lot step':>9s} {'unit step':>10s}  verdict")
    print(header)
    print("  " + "-" * (len(header) - 2))
    disagreements = 0
    for entry in faces:
        for name in ("straight", "network"):
            read = entry[name]
            graded = read["unit_step"] > floor
            verdict = "grades" if graded else "BELOW THE FLOOR"
            print(f"  {entry['block']:28s} {entry['face']:6s} {name:9s} "
                  f"{read['spread']:8.2f}m {read['ratio']:7.3f} "
                  f"{read['lot_step']:8.2f}m {read['unit_step']:9.2f}m  {verdict}")
        if entry["straight"]["nearest_lot"] != entry["network"]["nearest_lot"]:
            disagreements += 1
            print(f"  {'':28s} {'':6s} *** the two criteria name a different nearest lot")
        if args.list:
            for row in entry["rows"]:
                print(f"      lot {row['lot']}  along {row['along_m']:7.2f} m   "
                      f"straight {row['straight_m']:8.2f} m   network {row['network_m']:8.2f} m")
        print()

    print(f"  The two criteria name the same nearest lot on {len(faces) - disagreements} of "
          f"{len(faces)} faces measured.")
    print("  Neither criterion is evidence about 1835. Both order an invention, and every "
          "record that\n  applies one says so.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
