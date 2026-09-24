#!/usr/bin/env python3
"""What the town's principal-street frontage is BUILT OF, documented against invented.

T-0022 (legacy K29). Two liberties on the business front — L99 and L100 — recorded the
same worry in the same words: the 665-roof programme apportions families by DISTRICT and
"has no notion of what a street was for", so "it will keep dealing cabins to commercial
frontage every time this lane reaches one". Both said the deal was "very likely wrong in
this particular". Neither measured it, and K29 proposed the remedy that follows from
believing it: a frontage term weighting the meanest dwelling families off the business
front.

**Measured, the worry is backwards, and this module is the measurement.** What the
committed dataset says stood on the town's principal streets is mixed in construction,
and what this project invented onto the same streets was not.

## What the evidence says, and it is not one witness

* **The documented record.** Log buildings stand on the principal-street line in this
  dataset already, and they are trade buildings, not strays behind the town: `hogan_store`
  (log, a store, on South Water), `philo_carpenter_log_shop` (log, a drug shop, on Lake),
  `madore_beaubien_house` (log, dwelling AND store, on South Water), `mansion_house` (log,
  a tavern, on Lake). One street back from the line, `james_kinzie_house` is a documented
  log RESIDENCE on Lake. The business front was not a frame-only street.
* **The only picture of the row.** The reference the owner supplied for this reach —
  "South Water Street in 1834", `data/sources/assets/owner_brief_2026_08_18/README.md`
  image 11 — draws the south-bank frontage as "roughly ten one-storey LOG AND FRAME
  buildings shoulder to shoulder facing the river, two two-storey frame stores anchoring
  the east end". The same plate is already the cited warrant for the party-line treatment
  itself (T-0078), so the row's fabric and the row's shape come from one witness, and this
  project accepted half of it.
* **The owner's ruling of 2026-08-27** on PR #371's fork, option (b): a business-front lot
  may carry a documented store at the street and an anonymous dwelling behind it. The
  business front is not a district a dwelling is kept out of.

## The number this was written to record

At the commit before T-0022, **15 invented buildings stood on South Water Street's line and
NOT ONE of them was log** — 13 of the 15 were the party-line river row itself — against a
documented record for the same line of 8 buildings, 1 of them log. Every log dwelling the
schedule had dealt those five blocks, all five, had been put on the Lake face instead, by
an arrangement rule the block recipes state in their own prose: "the two best dwellings the
schedule deals take its two free lots … and the two meanest take Lake". That rule is a
preference. It is not in the programme, it is not in a source, and the one picture of the
street refutes it.

So the schedule MAY deal log cabins to commercial frontage, K29's proposed re-apportionment
is refused on the evidence rather than deferred, and what moved instead was the arrangement.

## What is asserted, absolutely — there is no ratchet and no threshold

**A principal street's INVENTED frontage may not be more uniform in construction than the
documented record of the same street.** Concretely: where the research layer puts at least
one log building on a principal street's line, the anonymous layers standing on that same
line must put at least one there too. A floor of one, not a share — a share would be a
number somebody chose, and the plate gives no ratio.

The assertion runs over the anonymous layers TOGETHER — `recon_1835_*` and `inf_*` — rather
than per layer, because "what this project invented onto that street" is one claim about
1835 however many generators wrote it. Splitting it per layer would have carved an
exemption for the household row on Lake, and an exemption written to make a new gate pass
is the gate arriving already disbelieved.

## What is only reported

The whole census: every principal street, every layer, every construction class, on the
line and behind it. The ordinary streets are printed beside them because the comparison is
the point — a rule about the business front means nothing unless the back streets differ.

## Where the street-line band comes from

`STREET_LINE_M` is a MEASUREMENT, in the same spirit as `DEEP_MODE_M` in
`tools/measure_corridor_intrusion.py`, not a bar anybody picked. Setbacks from the platted
corridor edge on principal frontages are bimodal with a clean empty gap: the outermost
building on the line stands 1.61 m back (`thomas_church_store`) and the next building
anywhere is 3.81 m back (`recon_1835_west_008`). This is the midpoint of that gap. Run
`--setbacks` to print the distribution and see the gap for yourself.

## The trade share, which is the other half of the same census (T-0213)

The fabric assertion above is about what the frontage is MADE OF. `trade_share_by_class`
answers the neighbouring question — what the frontage is FOR — off the same rows, and
`tools/reconcile_665.py` reads it to weight the trade families onto the business front.

It reports, per class of the committed street hierarchy, the share of DOCUMENTED buildings
whose reconciliation credits them a trade family (C stores, F warehouses, W workshops).
Documented only: the invented layers are what the schedule produced, so weighting the
schedule by them would be the programme grading its own homework.

    tools/measure_frontage_fabric.py             the census
    tools/measure_frontage_fabric.py --setbacks  the distribution the band comes from
    tools/measure_frontage_fabric.py --trade     the trade share per street class
    tools/measure_frontage_fabric.py --gate      exit 1 on a uniformity the record refuses
    tools/measure_frontage_fabric.py --self-test break it in memory and watch it fire
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
STRUCTURES = DATA / "structures"

sys.path.insert(0, str(ROOT / "tools"))

from generate_plat_lots import point_in_polygon, point_to_ring_m  # noqa: E402
from measure_corridor_intrusion import is_street_furniture  # noqa: E402
from measure_street_frontage import layer_of, layer_of_record  # noqa: E402
from placement_policy_1835 import constant  # noqa: E402
from plat_corridors import corridors, sampled  # noqa: E402

# The empty gap in the setback distribution, at its midpoint. See the docstring; run
# --setbacks to re-derive it. A building at or inside this stands ON the street line;
# anything further back stands in the block behind it.
#
# IT IS NO LONGER TYPED HERE. T-1195 moved the five numbers three modules had each
# re-typed into `data/reconstruction/1835_placement_policy.json`, and that file's own
# assertion 5 reads this line: put a literal back and the gate names the module.
STREET_LINE_M = constant("street_line_m")

# The construction classes this census reads. `construction` is a committed form value on
# 344 phases and is the field the archetypes build walls from, so the material a visitor
# sees IS this field — nothing here interprets an archetype name.
LOG = "log"
FRAME = "frame"
OTHER = "other"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def principal_streets() -> dict[str, str]:
    """The town's principal streets, out of the committed street records.

    `traffic` is authored on `data/streets/1835.json` and sourced there to
    `chicago_dpw_1891_streets` — the file's own note reads "South Water and Lake are the
    early principal graded/turnpiked routes", which is Andreas's sentence that they "were
    the two principal thoroughfares of the village, and therefore were early turnpiked and
    graded" (`chicagology_prefire233`). This module reads that hierarchy; it does not
    author one, and a street re-classed there re-classes here in the same commit.
    """
    return {s["id"]: s["name_1835"] for s in load(DATA / "streets" / "1835.json")["streets"]
            if s.get("traffic") == "principal"}


def world_polygon(phase: dict, origin: tuple[float, float]) -> list[tuple[float, float]]:
    pos = phase["position"]
    theta = math.radians(float(pos.get("rotation_deg") or 0.0))
    cos, sin = math.cos(theta), math.sin(theta)
    e = float(pos["utm_e"]) - origin[0]
    n = float(pos["utm_n"]) - origin[1]
    return [(e + u * cos + v * sin, n - u * sin + v * cos)
            for u, v in phase["footprint"]["polygon"]]


def material_of(phase: dict) -> str:
    """log, frame, or other — read off the record's own committed `construction`."""
    value = (phase.get("form") or {}).get("construction")
    if isinstance(value, dict):
        value = value.get("value")
    if not value:
        return OTHER
    if value == LOG:
        return LOG
    return FRAME if FRAME in value else OTHER


def buildings() -> list[dict]:
    """Every committed building phase that stands somewhere, with its material and layer.

    Street furniture is excluded on `measure_corridor_intrusion.is_street_furniture` — a
    bridge deck lying in a street is the bridge doing its job, and it is not made of the
    frontage.
    """
    origin_doc = load(DATA / "datum.json")
    origin = (float(origin_doc["origin_utm_e"]), float(origin_doc["origin_utm_n"]))
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load(path)
        if is_street_furniture(doc):
            continue
        for phase in doc.get("phases") or []:
            position = phase.get("position") or {}
            polygon = (phase.get("footprint") or {}).get("polygon") or []
            if position.get("utm_e") is None or len(polygon) < 3:
                continue
            out.append({"id": doc["id"], "layer": layer_of(doc["id"]),
                        "material": material_of(phase),
                        "world": world_polygon(phase, origin)})
    return out


def water_rings() -> list[list[tuple[float, float]]]:
    """The scene epoch's committed water planform, in local ENU metres.

    Read off `terrain_spec.json`'s own `water_polygons` list rather than off a set of
    filenames typed here: that list is what `generators/terrain_gen.py` cuts the
    heightfield's channel from, so a reach added to the terrain is in this reading in
    the same commit, and the two cannot drift into disagreeing about where the river is.

    A ring the spec declares an ISLAND is land and is not returned — the bar between the
    piers is ground a person stands on, not water anybody is separated by. The entries
    the spec states as a RULE rather than as a traced polygon (`north_branch_wabansia`,
    and the open-lake fills) carry no `from` file and are outside this reading; all of
    them lie beyond the platted town, where there is no corridor to be credited with.
    """
    epoch = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
    spec = load(epoch / "terrain_spec.json")
    origin_doc = load(DATA / "datum.json")
    oe, on = float(origin_doc["origin_utm_e"]), float(origin_doc["origin_utm_n"])
    out = []
    for entry in spec.get("water_polygons") or []:
        source = entry.get("from")
        if not source:
            continue
        islands = entry.get("island_rings")
        if isinstance(islands, str):
            islands = json.loads(islands)
        islands = set(islands or [])
        for feature in load(epoch / source)["features"]:
            if (feature.get("properties") or {}).get("kind") not in (None, "water"):
                continue
            geometry = feature["geometry"]
            if geometry["type"] == "Polygon":
                polygons = [geometry["coordinates"]]
            elif geometry["type"] == "MultiPolygon":
                polygons = geometry["coordinates"]
            else:
                continue
            for polygon in polygons:
                for index, ring in enumerate(polygon):
                    if index in islands:
                        continue
                    out.append([(x - oe, y - on) for x, y, *_ in ring])
    return out


def _straddles(a, b, c, d) -> bool:
    """True where segment a-b and segment c-d cross."""
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = side(c, d, a), side(c, d, b)
    d3, d4 = side(a, b, c), side(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def over_water(a, b, water: list) -> bool:
    """True where the straight line from a to b passes over committed water."""
    for ring in water:
        for c, d in zip(ring, ring[1:] + ring[:1]):
            if _straddles(a, b, c, d):
                return True
    return False


def in_water(point, water: list) -> bool:
    """True where a point stands in committed water."""
    return any(point_in_polygon(point, ring) for ring in water)


def _nearest_on_polyline(point, path):
    """The nearest point of an open polyline — the street as its record draws it."""
    best, at = float("inf"), path[0]
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((point[0] - ax) * dx +
                                                     (point[1] - ay) * dy) / span))
        candidate = (ax + dx * t, ay + dy * t)
        distance = math.dist(point, candidate)
        if distance < best:
            best, at = distance, candidate
    return at


def _edge_candidates(points: list, ring: list) -> list:
    """(distance, footprint point, corridor point) — the nearest pair per ring edge.

    One candidate per edge rather than one per corridor, because the bank test can
    REFUSE the nearest point of a corridor and the next-nearest point of the same
    corridor may still be that footprint's frontage: Kinzie Street is dry for 1,300 m
    and under the harbour cut for the last 110, and a roof on the north bank must keep
    the street the cut did not take.
    """
    out = []
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        best = (float("inf"), None, None)
        for px, py in points:
            t = 0.0 if span == 0 else max(0.0, min(1.0, ((px - ax) * dx +
                                                         (py - ay) * dy) / span))
            corner = (ax + dx * t, ay + dy * t)
            distance = math.dist((px, py), corner)
            if distance < best[0]:
                best = (distance, (px, py), corner)
        if best[1] is not None:
            out.append(best)
    out.sort(key=lambda row: row[0])
    return out


def nearest_frontage(polygon: list[tuple[float, float]], lanes: dict,
                     water: list | None = None) -> tuple[str, float]:
    """(street id, setback) for the corridor this footprint stands nearest.

    Setback is measured from the corridor EDGE and is negative where the footprint reaches
    inside the roadway, so the documented buildings PR #371 found standing in South Water
    sort in front of the row rather than behind it.

    ## THE BANK TEST (T-1429), and it is two clauses because one does not reach

    Until T-1191 this reading was a straight line to the nearest corridor and nothing
    else, which was harmless while the north bank had no corridors: everything a
    north-side roof could be measured against was already across the water, and the
    readings were recorded as outliers with authored reasons saying so. T-1191 put the
    north bank's own streets in the reading, and the crossing now happens in BOTH
    directions — where it produces a FALSE CONFORMANCE rather than a stated outlier, an
    assertion about placement has stopped measuring placement.

    **Clause B, the bank.** A corridor separated from the footprint by the river is not
    that footprint's frontage. The water is the epoch's own committed planform (see
    `water_rings`); nothing here re-traces a bank.

    **Clause A, the submerged stretch, and the fort out-buildings are why it exists.**
    The bank clause alone does not reach `fort_dearborn_out_building_a` and `_b`. Both
    stand inside the military reservation on the south bank and were credited with
    Kinzie Street at 198.31 m and 195.52 m — but the point of Kinzie they were measured
    against is not on the north bank at all. Thompson's plat draws Kinzie east to the
    town line, and the 1834 harbour cut crosses it: the street's own centre line stands
    between 0.52 m and 4.52 m UNDER water from local east 995 to its terminus at 1100,
    and it is the south EDGE of that submerged corridor, clipping the dry spit at the
    channel's bank, that the ray reaches without crossing anything. So: **a point of
    corridor is frontage only where the street's own centre line, at the station nearest
    it, stands on land.** A stretch of street the harbour cut took is not a street.

    With both clauses the two out-buildings measure to Kinzie's dry end instead, 264 m
    off and across the channel, which Clause B then refuses — and they are outliers
    again with their reasons intact, which is what `placement_policy_1835` recorded
    before the north bank had corridors and could no longer say.

    A footprint no corridor reaches gets `(None, inf)`: the reservation and the river
    mouth hold roofs that front no street, and saying so is the honest reading.
    """
    water = water_rings() if water is None else water
    best_id, best = None, float("inf")
    points = sampled(polygon)
    for street_id, lane in lanes.items():
        ring, centre = lane["ring"], lane["centre"]
        near = float("inf")
        inside = [p for p in points if point_in_polygon(p, ring)]
        if inside:
            # a footprint reaching into the roadway is standing on that street's own
            # ground: there is no water between them to test for
            near = -max(point_to_ring_m(p, ring) for p in inside)
        else:
            for distance, point, corner in _edge_candidates(points, ring):
                if distance >= best:
                    break
                if in_water(_nearest_on_polyline(corner, centre), water):
                    continue
                if over_water(point, corner, water):
                    continue
                near = distance
                break
        if near < best:
            best_id, best = street_id, near
    return best_id, best


def census(records: list[dict] | None = None,
           streets: dict[str, str] | None = None) -> dict:
    """Every building assigned to the street it stands nearest, split on the line."""
    lanes = corridors()
    water = water_rings()
    principal = principal_streets() if streets is None else streets
    rows = []
    for record in (buildings() if records is None else records):
        street, setback = nearest_frontage(record["world"], lanes, water)
        rows.append({**record, "street": street, "setback_m": round(setback, 2),
                     "on_line": setback <= STREET_LINE_M,
                     "principal": street in principal})
    return {"principal": principal, "rows": rows}


def _tally(rows: list[dict], layer_test) -> dict[str, int]:
    out = {LOG: 0, FRAME: 0, OTHER: 0}
    for row in rows:
        if layer_test(row["layer"]):
            out[row["material"]] += 1
    return out


def _documented(layer: str) -> bool:
    return layer == "research"


def _invented(layer: str) -> bool:
    return layer != "research"


def failures(result: dict) -> list[str]:
    """The one assertion. See the docstring."""
    out = []
    for street in sorted(result["principal"]):
        line = [r for r in result["rows"] if r["street"] == street and r["on_line"]]
        documented = _tally(line, _documented)
        invented = _tally(line, _invented)
        if not documented[LOG] or not sum(invented.values()):
            continue
        if invented[LOG]:
            continue
        out.append(
            f"{result['principal'][street]}: the documented record puts "
            f"{documented[LOG]} log building(s) on this street's line and the "
            f"{sum(invented.values())} invented one(s) standing there are all frame or "
            f"plank. A reconstruction may not be more uniform than the record it "
            f"reconstructs — the 1834 view of this frontage draws it as log AND frame, "
            f"shoulder to shoulder")
    return out


# The families that make a building a place of trade, by the inventory's own letters:
# C stores and mixed use, F warehouses and freight, W workshops. T (inns and taverns) is
# NOT one of them — a tavern is a trade but the schedule's T families are lodging, and the
# South Water row the owner's plate draws is stores and a warehouse. Both readings are
# printed by --trade so the choice can be checked rather than taken on trust. Held by the
# placement policy since T-1195 — see STREET_LINE_M above.
TRADE_LETTERS = tuple(constant("trade_letters"))


def street_traffic() -> dict[str, str]:
    """Every committed street's traffic class, out of `data/streets/1835.json`.

    The same authored, sourced hierarchy `principal_streets` reads — this returns all three
    tiers rather than only the top one, because the trade share turns out to be monotone in
    them and a weighting that used only `principal` would throw the middle tier away.
    """
    return {s["id"]: s.get("traffic") for s in load(DATA / "streets" / "1835.json")["streets"]}


def documented_families() -> dict[str, str]:
    """structure id -> the family the committed reconciliation credits it.

    `data/reconstruction/1835_existing_roof_reconciliation.json` is the project's own
    reading of what each documented building WAS; nothing here re-types a record.
    """
    doc = load(DATA / "reconstruction" / "1835_existing_roof_reconciliation.json")
    return {r["structure_id"]: r["likely_family"]
            for r in doc["records"] if r.get("likely_family")}


def trade_share_by_class(result: dict | None = None,
                         letters: tuple[str, ...] = TRADE_LETTERS) -> dict[str, dict]:
    """Per traffic class, the share of documented buildings that carry a trade family.

    A building is assigned to the street its footprint stands nearest — the same
    assignment the fabric census makes — and only the research layer is counted. The
    return is `{class: {n, trade, share}}`, and a class the record says nothing about is
    absent rather than zero.
    """
    result = census() if result is None else result
    traffic = street_traffic()
    families = documented_families()
    out: dict[str, dict] = {}
    for row in result["rows"]:
        if row["layer"] != "research":
            continue
        family = families.get(row["id"])
        klass = traffic.get(row["street"])
        if not family or not klass:
            continue
        bucket = out.setdefault(klass, {"n": 0, "trade": 0, "share": 0.0})
        bucket["n"] += 1
        if family[0] in letters:
            bucket["trade"] += 1
    for bucket in out.values():
        bucket["share"] = bucket["trade"] / bucket["n"]
    return out


def _trade(result: dict) -> str:
    lines = ["   the share of DOCUMENTED buildings carrying a trade family, by the class "
             "of the street they stand nearest", ""]
    for label, letters in (("C/F/W  stores, warehouses, workshops", TRADE_LETTERS),
                           ("C/F/W/T  …and lodging, for comparison",
                            TRADE_LETTERS + ("T",))):
        lines += [f"   {label}", f"   {'class':<14}{'n':>5}{'trade':>7}{'share':>9}"]
        shares = trade_share_by_class(result, letters)
        for klass in ("principal", "ordinary", "light"):
            row = shares.get(klass)
            if not row:
                continue
            lines.append(f"   {klass:<14}{row['n']:>5}{row['trade']:>7}"
                         f"{row['share']:>9.4f}")
        lines.append("")
    lines.append("   tools/reconcile_665.py reads the first table (T-0213)")
    return "\n".join(lines)


def _table(result: dict) -> str:
    lines = [f"   the street line is a footprint reaching within {STREET_LINE_M:.2f} m of "
             f"a platted corridor edge",
             "",
             f"   {'street':<20}{'where':<13}{'layer':<12}{'n':>4}{'log':>6}"
             f"{'frame':>7}{'other':>7}"]
    principal = result["principal"]
    streets = sorted({r["street"] for r in result["rows"] if r["street"]},
                     key=lambda s: (s not in principal, s))
    for street in streets:
        name = principal.get(street, street.replace("_", " ").title())
        mark = "  *" if street in principal else "   "
        for where, on_line in (("on the line", True), ("behind", False)):
            for label, test in (("documented", _documented), ("invented", _invented)):
                rows = [r for r in result["rows"]
                        if r["street"] == street and r["on_line"] is on_line]
                tally = _tally(rows, test)
                total = sum(tally.values())
                if not total:
                    continue
                lines.append(f"{mark}{name:<20}{where:<13}{label:<12}{total:>4}"
                             f"{tally[LOG]:>6}{tally[FRAME]:>7}{tally[OTHER]:>7}")
    lines += ["", "   * a principal street of the committed street hierarchy — the "
              "town's business front"]
    return "\n".join(lines)


def _setbacks(result: dict) -> str:
    rows = sorted((r for r in result["rows"] if r["principal"]),
                  key=lambda r: r["setback_m"])
    lines = ["   every building on a principal-street frontage, by setback from the "
             "corridor edge", ""]
    previous = None
    for row in rows:
        gap = ""
        if previous is not None and row["setback_m"] - previous > 1.0:
            gap = f"   <-- {row['setback_m'] - previous:.2f} m gap"
        lines.append(f"   {row['setback_m']:>8.2f}  {row['id']:<46}{gap}")
        previous = row["setback_m"]
    return "\n".join(lines)


def _synthetic(material: str) -> list[dict]:
    """Two buildings on one street line — one documented, one invented — in memory.

    The polygons are placed by hand in the local frame at the South Water corridor's own
    edge, so the self-test exercises the assertion rather than the plat.
    """
    lanes = corridors()
    points = lanes["south_water"]["points"]
    (ax, ay), (bx, by) = points[len(points) // 2], points[len(points) // 2 + 1]
    length = math.dist((ax, ay), (bx, by))
    along = ((bx - ax) / length, (by - ay) / length)
    normal = (-along[1], along[0])
    out = []
    # The invented unit has no committed record, so its layer is read off a record built
    # here in the shape the reconstruction generators write — the same reading
    # `layer_of` performs on the committed tree, rather than a layer typed in beside it
    # (T-0221). The documented witness is a real record and is asked about by id.
    documented = {"id": "hogan_store"}
    invented = {"id": "recon_1835_synthetic_row_unit",
                "reconstruction": {"status": "inferred_anonymous"}}
    for index, (record, layer_material) in enumerate(
            ((documented, LOG), (invented, material))):
        # step off the centreline by the half-width plus a metre, on the south side
        sign = -1.0 if normal[1] > 0 else 1.0
        cx = ax + along[0] * (10.0 + index * 12.0) + normal[0] * sign * 13.2
        cy = ay + along[1] * (10.0 + index * 12.0) + normal[1] * sign * 13.2
        layer = (layer_of(record["id"]) if "reconstruction" not in record
                 else layer_of_record(record))
        out.append({"id": record["id"], "layer": layer, "material": layer_material,
                    "world": [(cx - 3, cy - 3), (cx + 3, cy - 3),
                              (cx + 3, cy + 3), (cx - 3, cy + 3)]})
    return out


def self_test() -> int:
    print("  the assertion, broken in memory against the committed corridors\n")
    checks = []
    streets = principal_streets()

    frame_row = census(_synthetic(FRAME), streets)
    on_line = [r for r in frame_row["rows"] if r["on_line"] and r["principal"]]
    checks.append(("both synthetic buildings land on a principal street line",
                   len(on_line) == 2, f"{len(on_line)} of 2"))

    out = failures(frame_row)
    checks.append(("an all-frame invented row beside a documented LOG building is caught",
                   any("more uniform" in m for m in out), "; ".join(out) or "nothing"))

    log_row = census(_synthetic(LOG), streets)
    out = failures(log_row)
    checks.append(("…and the same row with one log unit in it passes",
                   not out, "; ".join(out) or "clean"))

    # a street with no documented log building asserts nothing: the rule is a floor
    # taken from the record, not a quota this module invented
    no_witness = copy.deepcopy(_synthetic(FRAME))
    no_witness[0]["material"] = FRAME
    out = failures(census(no_witness, streets))
    checks.append(("a street whose own record carries no log building asserts nothing",
                   not out, "; ".join(out) or "clean"))

    # and an ORDINARY street is not the business front, whatever stands on it
    out = failures(census(_synthetic(FRAME), {}))
    checks.append(("an ordinary street is out of scope — the rule is about the "
                   "business front", not out, "; ".join(out) or "clean"))

    # THE BANK TEST (T-1429), against the committed water and the committed corridors.
    # Both clauses are exercised on the record that earned each of them, so a corridor
    # re-drawn or a reach added to the terrain moves these lines rather than passing
    # quietly.
    lanes = corridors()
    water = water_rings()
    checks.append(("the epoch's committed water planform is read and is not empty",
                   len(water) >= 4, f"{len(water)} ring(s)"))

    origin_doc = load(DATA / "datum.json")
    origin = (float(origin_doc["origin_utm_e"]), float(origin_doc["origin_utm_n"]))
    kinzie = lanes["kinzie"]
    checks.append(("Kinzie Street's east terminus stands in the harbour cut — the "
                   "submerged stretch clause has something to refuse",
                   in_water(kinzie["centre"][-1], water),
                   f"terminus {tuple(round(v, 1) for v in kinzie['centre'][-1])}"))
    checks.append(("…and its west end does not, so the clause refuses a STRETCH and "
                   "not the street", not in_water(kinzie["centre"][0], water),
                   f"west end {tuple(round(v, 1) for v in kinzie['centre'][0])}"))

    by_id = {r["id"]: r for r in buildings()}
    for record_id, expected in (("fort_dearborn_out_building_a", "lake"),
                                ("fort_dearborn_out_building_b", "lake")):
        record = by_id.get(record_id)
        street, setback = (nearest_frontage(record["world"], lanes, water)
                           if record else (None, float("inf")))
        checks.append((f"{record_id} is off the far bank's street and onto its own",
                       street == expected,
                       f"{street} at {setback:.2f} m" if record else "not committed"))
    # and the ray clause on its own, which is the half the fort case does not exercise:
    # a straight line from the reservation to the north bank crosses the water
    reservation = by_id.get("fort_dearborn_blockhouse")
    if reservation:
        here = reservation["world"][0]
        there = lanes["north_water"]["centre"][0] if "north_water" in lanes else None
        if there is None:
            there = kinzie["centre"][0]
        checks.append(("a straight line from the reservation to a north-bank street "
                       "crosses committed water", over_water(here, there, water),
                       f"{tuple(round(v, 1) for v in here)} to "
                       f"{tuple(round(v, 1) for v in there)}"))

    ok = True
    for label, passed, detail in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  {label} — {detail}")
        ok &= passed
    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 where an invented frontage is more uniform than the "
                             "documented record of the same street")
    parser.add_argument("--setbacks", action="store_true",
                        help="the distribution STREET_LINE_M is the gap in")
    parser.add_argument("--trade", action="store_true",
                        help="the documented trade share per class of street, which "
                             "tools/reconcile_665.py weights the business front by")
    parser.add_argument("--self-test", action="store_true",
                        help="break the assertion in memory and check that it fires")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    result = census()
    if args.setbacks:
        print(_setbacks(result))
        return 0
    if args.trade:
        print(_trade(result))
        return 0

    bad = failures(result)
    if args.gate:
        if bad:
            print("PRINCIPAL FRONTAGE FABRIC")
            for line in bad:
                print(f"  - {line}")
            return 1
        if not args.quiet:
            print(_table(result))
        streets = len(result["principal"])
        print(f"no principal frontage is more uniform than its own record "
              f"({streets} principal street(s) measured)")
        return 0

    print(_table(result))
    for line in bad:
        print(f"  FAIL  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
