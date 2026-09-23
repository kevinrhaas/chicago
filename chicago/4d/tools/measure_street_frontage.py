#!/usr/bin/env python3
"""How much building each committed street carries, so the face rule stops being a memory.

ROADMAP T-A14. Every block parcel since T-A8 has had to decide which of its two faces is
the better street, and every one of them has answered from the street's documented use —
"South Water is the business front" — which says nothing at all about a block bounded by
Randolph and Washington. T-A13 was the first to measure it instead, counting structures
within 25 m of each street's committed centreline, and reported Lake 12, Randolph 2 and
South Water 9.

**Those three numbers do not reproduce.** Under the filter T-A13's own note states — every
documented or inferred structure whose footprint centroid stands within 25 m of the
committed centreline — the committed record gives materially different counts, and the
filter that would give T-A13's is not written down anywhere in the repository. The
measurement was right to make and the finding it supported (Lake is the better face, by a
wide margin) survives every filter this tool can express; what did not survive is the
number, because it was derived by hand and thrown away.

So it is a command now. A parcel that needs the face rule runs this and quotes it. The
three layers are reported separately and never merged, because they are not the same kind
of evidence and one of them cannot vote:

* **research** — the documented layer. Records recovered from sources. This is the layer
  the face rule is actually asking about.
* **inferred_household** — the trade-census layer. Positions are argued, not recovered.
* **reconstruction** — the anonymous count-units the block parcels themselves place. A
  block parcel that let this layer decide its arrangement would be reading its own output
  back as evidence: the row of blocks built along South Water is why South Water looks
  built up in this layer, and nothing else.

The centroid is the test rather than the whole footprint, because a footprint that laps a
25 m band is not thereby "on" that street, and because T-A13 used the centroid and this
tool exists to make its measurement repeatable rather than to replace it.

    tools/measure_street_frontage.py                  every committed street
    tools/measure_street_frontage.py randolph washington
    tools/measure_street_frontage.py --radius 30 lake
    tools/measure_street_frontage.py --list randolph  name every record counted
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from plat_occupancy import LAYERS, footprints, layer_of_record, layers  # noqa: E402

DEFAULT_RADIUS_M = 25.0

__all__ = ["LAYERS", "layer_of", "layer_of_record"]


def layer_of(structure_id: str) -> str:
    """Which of the three evidence layers a committed record belongs to.

    Read off THE RECORD, in `plat_occupancy.layer_of_record` — the one place this
    project decides it (T-0221). This function is the same question asked about a
    committed id, and it is kept here because two other measurements import it from
    here; it is a lookup now rather than a second reading.

    Until T-0221 it answered from the ID PREFIX instead, and that answer was wrong for
    `physicians_office`: an inferred-household roof whose filename carries no prefix,
    which therefore read as `research` — the documented layer — everywhere this function
    is used, including the absolute assertion in
    `tools/measure_corridor_intrusion.py --gate` that no GENERATED roof may lap a
    platted street. Nothing in the tree was ever mis-scored by it, and the gate's reach
    is one record wider for it being closed.

    A record built in memory has no committed id; ask `layer_of_record` about it
    directly rather than teaching this function to guess from a name again.
    """
    try:
        return layers()[structure_id]
    except KeyError:
        raise KeyError(
            f"{structure_id!r} is not a committed structure record, so its evidence "
            f"layer cannot be read from one; pass the record to layer_of_record()"
        ) from None


def _distance_to_segment(point, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = point, a, b
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def distance_to_street(street: dict, point) -> float:
    path = street["path_local_enu_m"]
    return min(_distance_to_segment(point, path[i], path[i + 1]) for i in range(len(path) - 1))


def centroids() -> dict[str, tuple[float, float]]:
    """One point per structure — the centroid of its first placed footprint."""
    datum = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
    placed: dict[str, tuple[float, float]] = {}
    for structure_id, polygon in footprints(datum):
        if structure_id in placed:
            continue
        placed[structure_id] = (sum(x for x, _ in polygon) / len(polygon),
                                sum(y for _, y in polygon) / len(polygon))
    return placed


def measure(street_ids: list[str], radius: float) -> list[dict]:
    streets = {s["id"]: s for s in json.loads(
        (ROOT / "data" / "streets" / "1835.json").read_text(encoding="utf-8"))["streets"]}
    points = centroids()
    rows = []
    for street_id in street_ids:
        street = streets[street_id]
        near = sorted(((structure_id, distance_to_street(street, point))
                       for structure_id, point in points.items()
                       if distance_to_street(street, point) <= radius),
                      key=lambda row: row[1])
        rows.append({
            "street": street_id,
            "name": street.get("name_1835") or street_id,
            "counts": {layer: sum(1 for sid, _ in near if layer_of(sid) == layer)
                       for layer in LAYERS},
            "records": [(sid, round(distance, 1)) for sid, distance in near],
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("streets", nargs="*", help="street ids (default: all committed streets)")
    parser.add_argument("--radius", type=float, default=DEFAULT_RADIUS_M,
                        help=f"band half-width in metres (default {DEFAULT_RADIUS_M})")
    parser.add_argument("--list", action="store_true", help="name every record counted")
    args = parser.parse_args()

    streets = json.loads((ROOT / "data" / "streets" / "1835.json").read_text(
        encoding="utf-8"))["streets"]
    known = [s["id"] for s in streets]
    wanted = args.streets or known
    for street_id in wanted:
        if street_id not in known:
            print(f"no committed street called {street_id!r}; have: {', '.join(known)}")
            return 1

    print(f"structures whose footprint centroid is within {args.radius:g} m of the "
          f"committed centreline\n")
    print(f"  {'street':16s} {'research':>9s} {'household':>10s} {'reconstruction':>15s} {'total':>7s}")
    for row in measure(wanted, args.radius):
        counts = row["counts"]
        total = sum(counts.values())
        print(f"  {row['street']:16s} {counts['research']:9d} "
              f"{counts['inferred_household']:10d} {counts['reconstruction']:15d} {total:7d}")
        if args.list:
            for structure_id, distance in row["records"]:
                print(f"      {distance:6.1f} m  {layer_of(structure_id):18s} {structure_id}")
    print("\nThe reconstruction column is this programme's own output and cannot vote on "
          "its own arrangement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
