#!/usr/bin/env python3
"""What the North Division's ground actually covers, and where its timber stops.

Ticket T-1722, the GROUND half of the memo's build order item 4
(`docs/RESEARCH/1835_north_division_extent_and_infill.md`): *"Trace the North Branch
beyond N +400 and extend terrain/hydrology/flora/collision to N +760."*

Three of those four had already arrived by the time this was written and nothing said
so. The box carries to local **N +1120**, the North Branch and both its banks are traced
to **N +1079.21**, and the lake margin to **N +1117.30** — all of it landed with the
terrain extension that raised the north wall from +400. The FLORA did not follow. The
North Division's timber, `data/flora/zones/z06_dense_forest.json`, still carried the
19-vertex ring that was cut to the OLD box: a straight artificial edge along N +340 and
a second along E +340, neither of them a boundary of anything. North of Michigan Street
the whole division — Kinzie's Addition, the Rush–Pine fringe, the lake-shore ground —
was therefore matching `z01_wet_prairie` and `z02_mesic_prairie`, whose exclusion ring
was the same stale shape, and rendering as open prairie. Andreas documents the North
Side as carrying *"a body of thrifty heavy growth of timber"*.

**So this does not invent an extent; it re-derives the one the record already claims.**
`z06`'s own extent note says what the polygon IS — *"the North Division inside the box:
the land north of the main stem and east of the North Branch, traced off the waterline
of the committed heightfield"* — and the waterline that sentence names is committed,
three named runs of it, each tagged `north_division` in the terrain spec's `shore_runs`:

    north_branch_east_bank    branches.geojson   the forks to Wright's north survey line
    north_division_shore      river.geojson      east bank of the branch, north bank of
                                                 the main stem, through the forks box
    north_shore_harbor_reach  shoreline.geojson  north bank of the main stem, the north
                                                 pier's inner face, the lake shore north

Walked in that order they are one continuous land boundary from the branch's traced head
down to the forks, east along the main stem and north up the lake shore to the box wall.
The ring closes along the wall itself, which is the one inference in it and is stated in
the record: north of the last traced bank vertex the boundary is carried straight north
to N +1120, because the trace ends at Wright's survey line and the ground does not.

WHAT THE SANDY HILLS AND THE MARSHY PLACES DO, which is Andreas's own exception clause:
nothing here has to cut them out. `z06` sits at priority 25, under `z05_riverbank_timber`
(30), `z09_sand_prairie` (40), `z08_lakeshore` (45), `z03_sedge_meadow` (55) and
`z04_marsh` (70). The beach, the foredune, the relict ridges and the wet ground all win
on the overlap already. The timber is the FLOOR of the North Division, which is exactly
the shape of the sentence that documents it.

WHAT THIS DOES NOT CARRY. The hydrology layer is not short and this says so rather than
extending it: `hydrology.geojson` holds one watercourse, the unnamed north-side slough,
and its record states that Wright draws it *"ending at Michigan Street"*. Its northern
end at local N +341.7 is a DOCUMENTED end, not a tracing window. There is nothing above
it on the sheet to carry, and carrying one would be an invention.

    tools/measure_northern_ground.py             the report
    tools/measure_northern_ground.py --write     re-derive the three flora records
    tools/measure_northern_ground.py --gate      the two assertions
    tools/measure_northern_ground.py --self-test prove both assertions still fire

The two assertions:

* **The committed flora ring is the derived one.** `z06`'s extent, and the mirror of it
  that `z01` and `z02` carry as `exclude_polygons`, and the denormalised copies in
  `data/flora/index.json`, all four vertex-for-vertex. The day the waterline moves or
  the box wall moves, this fails at the commit instead of leaving the North Division's
  timber standing on a boundary that is no longer there — which is precisely how the
  +340 edge survived the extension that made it meaningless.
* **The division's ground reaches the memo's line.** The derived ring's north edge is at
  or beyond local N +760 m, which is the coverage the 665-roof programme's North balance
  is composed against in `tools/reconcile_665.py`.

Exit 0 pass, 1 on a failed assertion, 2 if the inputs cannot be read.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPOCH = ROOT / "data/terrain/epochs/e1834_harbor_cut"
FLORA = ROOT / "data/flora"

# The three committed runs of the North Division's waterline, in the order a walker
# meets them going from the branch's traced head round to the lake. Each is a
# `shore_runs` entry in terrain_spec.json tagged `division: north_division`; the names
# are the feature names inside the geojson, matched on their leading clause.
RUNS = (
    ("branches.geojson", "East bank of the North Branch", "north_branch_east_bank"),
    ("river.geojson", "North Division shore", "north_division_shore"),
    ("shoreline.geojson", "North shore of the harbour reach", "north_shore_harbor_reach"),
)

# Douglas-Peucker tolerance for the derived ring. The runs themselves are simplified at
# 1.78 m (their own provenance says so) and every vertex on them carries ±20 m of
# affine residual — the two 1834 sheets disagree about the forks by 58 m. 10 m is half
# that uncertainty and takes 121 vertices to 35, which is a ring the renderer tests per
# candidate plant. It is a drafting tolerance, never a claim about the shore.
SIMPLIFY_M = 10.0

# The memo's line, the one build order item 4 asks the ground to reach.
MEMO_LINE_N_M = 760.0

ZONE_FILE = FLORA / "zones/z06_dense_forest.json"
MIRROR_FILES = (FLORA / "zones/z01_wet_prairie.json", FLORA / "zones/z02_mesic_prairie.json")
MIRROR_IDS = ("z01_wet_prairie", "z02_mesic_prairie")
INDEX_FILE = FLORA / "index.json"


def die(msg: str) -> None:
    print(f"measure_northern_ground: {msg}", file=sys.stderr)
    raise SystemExit(2)


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except OSError as exc:
        die(f"cannot read {path}: {exc}")


def datum() -> tuple[float, float]:
    d = load(ROOT / "data/datum.json")
    return d["origin_utm_e"], d["origin_utm_n"]


def _vertices(geometry: dict) -> list[list[float]]:
    kind = geometry["type"]
    if kind == "LineString":
        return geometry["coordinates"]
    if kind == "MultiLineString":
        return [p for part in geometry["coordinates"] for p in part]
    die(f"a shore run may only be a line, not {kind}")
    return []


def run_local(filename: str, prefix: str) -> list[tuple[float, float]]:
    """One committed run, in local ENU metres."""
    oe, on = datum()
    for feature in load(EPOCH / filename)["features"]:
        name = feature["properties"].get("name") or ""
        if name.startswith(prefix):
            return [(round(x - oe, 3), round(y - on, 3)) for x, y in _vertices(feature["geometry"])]
    die(f"{filename} carries no feature whose name starts '{prefix}'")
    return []


def _splice(head: list, tail: list) -> list:
    """Join two runs at the tail vertex nearest the head's last one.

    The runs overlap where they were traced off different sheets of the same water —
    `north_division_shore` ends 76 m east of where `north_shore_harbor_reach` begins,
    both of them on the main stem's north bank. Cutting the tail at its nearest vertex
    keeps the boundary single-valued instead of doubling back over itself.
    """
    def d2(p, q):
        return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    cut = min(range(len(tail)), key=lambda i: d2(head[-1], tail[i]))
    return head + tail[cut:]


def _simplify(points: list, tol: float) -> list:
    """Douglas-Peucker, iterative-free and deterministic."""
    if len(points) < 3:
        return list(points)

    def perpendicular(p, a, b):
        (x, y), (x1, y1), (x2, y2) = p, a, b
        dx, dy = x2 - x1, y2 - y1
        span = dx * dx + dy * dy
        if span == 0:
            return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / span))
        return ((x - (x1 + t * dx)) ** 2 + (y - (y1 + t * dy)) ** 2) ** 0.5

    far = max(range(1, len(points) - 1),
              key=lambda i: perpendicular(points[i], points[0], points[-1]))
    if perpendicular(points[far], points[0], points[-1]) > tol:
        return _simplify(points[:far + 1], tol)[:-1] + _simplify(points[far:], tol)
    return [points[0], points[-1]]


def _area_ha(ring: list) -> float:
    total = 0.0
    for i, (x1, y1) in enumerate(ring):
        x2, y2 = ring[(i + 1) % len(ring)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0 / 1e4


def field_box() -> dict:
    meta = load(EPOCH / "heightfield.json")["box_local_enu_m"]
    return {"e_min_m": meta["e"][0], "e_max_m": meta["e"][1],
            "n_min_m": meta["n"][0], "n_max_m": meta["n"][1]}


def north_division_polygon(tol: float = SIMPLIFY_M) -> list[list[float]]:
    """The North Division's land ring, derived from the committed waterline."""
    box = field_box()
    walked: list[tuple[float, float]] = []
    for filename, prefix, _id in RUNS:
        run = run_local(filename, prefix)
        walked = run if not walked else _splice(walked, run)
    # Close along the box's own north wall: east end of the lake shore straight up to
    # it, west along it, and back down to the branch's last traced vertex.
    wall = box["n_max_m"]
    ring = walked + [(walked[-1][0], wall), (walked[0][0], wall)]
    return [[round(e, 2), round(n, 2)] for e, n in _simplify(ring, tol)]


def committed_rings() -> dict:
    zone = load(ZONE_FILE)
    index = load(INDEX_FILE)
    by_id = {z["id"]: z for z in index["zones"]}
    rings = {"z06_dense_forest": zone["extent"].get("polygon"),
             "index:z06_dense_forest": by_id["z06_dense_forest"]["extent"].get("polygon")}
    for path, zid in zip(MIRROR_FILES, MIRROR_IDS):
        holes = load(path)["extent"].get("exclude_polygons") or []
        rings[zid] = holes[0] if holes else None
        holes = by_id[zid]["extent"].get("exclude_polygons") or []
        rings[f"index:{zid}"] = holes[0] if holes else None
    return rings


def hydrology_reach() -> dict:
    oe, on = datum()
    features = load(EPOCH / "hydrology.geojson")["features"]
    north = None
    for feature in features:
        for _x, y in _vertices(feature["geometry"]):
            local = y - on
            north = local if north is None else max(north, local)
    return {"watercourses": len(features), "n_max_m": round(north or 0.0, 2),
            "documented_end": "Michigan Street — Wright draws the slough ending there, "
                              "so this is the watercourse's end and not a tracing window"}


def traced_water() -> dict:
    oe, on = datum()
    reach = {}
    for filename, prefix, run_id in RUNS:
        run = run_local(filename, prefix)
        reach[run_id] = {"vertices": len(run),
                         "n_min_m": round(min(p[1] for p in run), 2),
                         "n_max_m": round(max(p[1] for p in run), 2)}
    branch = None
    for feature in load(EPOCH / "branches.geojson")["features"]:
        if (feature["properties"].get("name") or "").startswith("Chicago River, North Branch"):
            branch = max(y - on for ring in feature["geometry"]["coordinates"] for _x, y in ring)
    reach["north_branch_water"] = {"n_max_m": round(branch or 0.0, 2)}
    return reach


def measure() -> dict:
    derived = north_division_polygon()
    committed = committed_rings()
    box = field_box()
    return {
        "field": box,
        "traced_water": traced_water(),
        "hydrology": hydrology_reach(),
        "north_division": {
            "derived_polygon": derived,
            "derived_vertices": len(derived),
            "derived_area_ha": round(_area_ha(derived), 2),
            "derived_n_max_m": round(max(p[1] for p in derived), 2),
            "derived_e_max_m": round(max(p[0] for p in derived), 2),
            "memo_line_n_m": MEMO_LINE_N_M,
            "simplify_tolerance_m": SIMPLIFY_M,
        },
        "flora": {
            "records": {k: (None if v is None else len(v)) for k, v in committed.items()},
            "committed_area_ha": {k: (None if v is None else round(_area_ha(v), 2))
                                  for k, v in committed.items()},
            "disagree": sorted(k for k, v in committed.items() if v != derived),
        },
    }


def coverage_figures(m: dict) -> dict:
    """The flat figures `tools/reconcile_665.py` writes into the programme's coverage."""
    nd = m["north_division"]
    return {
        "field_north_edge_n_m": m["field"]["n_max_m"],
        "north_branch_water_n_max_m": m["traced_water"]["north_branch_water"]["n_max_m"],
        "north_branch_east_bank_n_max_m": m["traced_water"]["north_branch_east_bank"]["n_max_m"],
        "lake_shore_n_max_m": m["traced_water"]["north_shore_harbor_reach"]["n_max_m"],
        "hydrology_n_max_m": m["hydrology"]["n_max_m"],
        "timbered_ground_ha": nd["derived_area_ha"],
        "timbered_ground_n_max_m": nd["derived_n_max_m"],
        "memo_line_n_m": nd["memo_line_n_m"],
        "ground_reaches_memo_line": nd["derived_n_max_m"] >= nd["memo_line_n_m"],
    }


def _ring_block(pad: str, step: str, compact: bool, ring: list) -> list[str]:
    inner = pad + step
    if compact:
        return [f"{inner}[{e:g},{n:g}]," for e, n in ring[:-1]] \
            + [f"{inner}[{ring[-1][0]:g},{ring[-1][1]:g}]"]
    lines = []
    for i, (e, n) in enumerate(ring):
        tail = "" if i == len(ring) - 1 else ","
        lines += [f"{inner}[", f"{inner}{step}{e:g},", f"{inner}{step}{n:g}", f"{inner}]{tail}"]
    return lines


def _replace_ring(text: str, key: str, ring: list) -> str:
    """Swap one ring into a record IN THE FILE'S OWN HAND.

    These four files are authored, not generated, and they do not share a layout:
    `z01` is plain two-space JSON, `z06` writes its vertices as compact `[e,n]` pairs
    at one-space indent, `z02` is a third thing again. Re-dumping any of them would put
    a four-thousand-line reformat in a diff whose subject is thirty-five vertices, so
    this rewrites the bracketed block and leaves every other byte alone.
    """
    head = re.search(rf'^([ \t]*)"{key}": \[[ \t]*\n', text, re.M)
    if not head:
        die(f"no \"{key}\" array to rewrite")
    pad = head.group(1)
    start, cursor, depth = head.start(), head.end() - 1, 1
    while depth:
        cursor += 1
        if text[cursor] == "[":
            depth += 1
        elif text[cursor] == "]":
            depth -= 1
    body = text[head.end():cursor]
    nested = key == "exclude_polygons"
    if nested:
        # One ring inside the list of rings: descend one bracket and recurse on layout.
        inner_head = re.search(r'^([ \t]*)\[[ \t]*\n', body, re.M)
        if not inner_head:
            die(f"\"{key}\" holds no ring to rewrite")
        pad = inner_head.group(1)
        body = body[inner_head.end():]
    lines = [ln for ln in body.split("\n") if ln.strip()]
    step = " " * max(1, len(lines[0]) - len(lines[0].lstrip()) - len(pad)) if lines else " "
    compact = bool(lines and re.match(r'^\s*\[-?[\d.]+\s*,\s*-?[\d.]+\s*\],?$', lines[0]))
    block = "\n".join(_ring_block(pad, step, compact, ring))
    if nested:
        return text[:start] + f'{head.group(1)}"{key}": [\n{pad}[\n{block}\n{pad}]\n' \
            + text[cursor:]
    return text[:start] + f'{pad}"{key}": [\n{block}\n{pad}]' + text[cursor + 1:]


def write(m: dict) -> int:
    """Re-derive the three flora records and the manifest's denormalised copies."""
    ring = m["north_division"]["derived_polygon"]
    ZONE_FILE.write_text(_replace_ring(ZONE_FILE.read_text(), "polygon", ring))
    for path in MIRROR_FILES:
        path.write_text(_replace_ring(path.read_text(), "exclude_polygons", ring))
    # The manifest's `extent` is a denormalised copy and `tools/validate.py` fails the
    # build when it drifts, so it is taken WHOLE from the zone record rather than patched
    # vertex by vertex — that way an extent note rewritten beside the ring travels with it.
    authored = {ZONE_FILE.stem: load(ZONE_FILE)["extent"]}
    for path in MIRROR_FILES:
        authored[path.stem] = load(path)["extent"]
    index = load(INDEX_FILE)
    for entry in index["zones"]:
        if entry["id"] in authored:
            entry["extent"] = authored[entry["id"]]
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote a {len(ring)}-vertex ring into z06, z01, z02 and the manifest")
    return 0


def report(m: dict) -> None:
    nd = m["north_division"]
    print("THE NORTH DIVISION'S GROUND")
    print(f"  field north edge          local N {m['field']['n_max_m']:+.1f} m")
    for key, run in m["traced_water"].items():
        print(f"  {key:<26}local N {run['n_max_m']:+.2f} m")
    print(f"  hydrology                 local N {m['hydrology']['n_max_m']:+.2f} m "
          f"({m['hydrology']['watercourses']} watercourse, a documented end)")
    print(f"  timbered ground           {nd['derived_area_ha']:.2f} ha, "
          f"{nd['derived_vertices']} vertices, north to N {nd['derived_n_max_m']:+.2f} m")
    print(f"  the memo's line           local N {nd['memo_line_n_m']:+.1f} m — "
          f"{'reached' if nd['derived_n_max_m'] >= nd['memo_line_n_m'] else 'NOT REACHED'}")
    if m["flora"]["disagree"]:
        print("  flora records off the derived ring: "
              + ", ".join(m["flora"]["disagree"]))
    else:
        print("  flora records             all four agree with the derived ring")


def gate(m: dict) -> int:
    problems = []
    if m["flora"]["disagree"]:
        problems.append(
            "the committed North Division timber ring is not the one the waterline "
            "derives: " + ", ".join(m["flora"]["disagree"])
            + " — run tools/measure_northern_ground.py --write")
    nd = m["north_division"]
    if nd["derived_n_max_m"] < nd["memo_line_n_m"]:
        problems.append(
            f"the division's derived ground stops at local N {nd['derived_n_max_m']:+.2f} m, "
            f"short of the memo's N {nd['memo_line_n_m']:+.1f} m that the 665-roof "
            "programme's North balance is composed against")
    for line in problems:
        print(f"  FAIL: {line}")
    return 1 if problems else 0


def self_test() -> int:
    ok = True
    m = measure()

    broken = json.loads(json.dumps(m))
    broken["flora"]["disagree"] = ["z06_dense_forest"]
    if gate(broken) == 0:
        ok = False
        print("  SELF-TEST FAIL: a flora ring off the waterline did not fail the gate")

    broken = json.loads(json.dumps(m))
    broken["north_division"]["derived_n_max_m"] = MEMO_LINE_N_M - 1.0
    if gate(broken) == 0:
        ok = False
        print("  SELF-TEST FAIL: ground short of the memo's line did not fail the gate")

    if gate(m) != 0:
        ok = False
        print("  SELF-TEST FAIL: the committed dataset does not pass its own gate")

    print("\nSELF-TEST PASS" if ok else "\nSELF-TEST FAIL")
    return 0 if ok else 1


KNOWN_ARGS = {"--gate", "--self-test", "--quiet", "--write"}


def main() -> int:
    args = set(sys.argv[1:])
    if args - KNOWN_ARGS:
        die(f"unknown argument(s): {' '.join(sorted(args - KNOWN_ARGS))}")
    if "--self-test" in args:
        return self_test()
    m = measure()
    if "--write" in args:
        return write(m)
    if "--quiet" not in args:
        report(m)
    if "--gate" in args:
        return gate(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
