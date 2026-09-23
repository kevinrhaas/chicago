#!/usr/bin/env python3
"""What lies in the gap the re-centred South Water corridor opens, measured on the ground.

T-0419, and it is a MEASUREMENT with a question at the end of it — not a repair. The
owner ruled on 2026-08-29 (T-0009) that a platted corridor is derived from the street
CONTROL rather than from the drawn centreline. On `south_water` that translates the
corridor +8.58 m in northing. Its block faces do not move: `generate_plat_lots.block_edges`
offsets the DRAWN line by the same half-module, so the corridor and the blocks stop
abutting and a band of ground belongs to neither.

**The ticket forbids fixing it here, and this tool does not.** It moves nothing, writes
nothing into `data/`, and is not wired to any generator. It answers the three questions
the ticket's acceptance asks — how big the band is, how many lots and committed roofs it
holds, and how much of it is dry — and prices the fork so the owner can rule on it.

**There are TWO bands, not one.** The ticket names the southern one; the displacement
makes a second of the same size on the other side, and leaving it out would have priced
half the question:

* `abandoned` — inside the DRAWN corridor, outside the control one. It lies between the
  block's north face and the corridor's new south edge, and belongs to neither.
* `claimed` — inside the CONTROL corridor, outside the drawn one. The corridor takes it,
  and on this street what is on that side is the river.

**How the bands are measured.** A vertical scanline at `AREA_PITCH_M`, differenced in one
dimension against both rings. That is a Riemann sum over exact ring crossings rather than
a raster of point tests, so the areas are the polygons' own to the pitch, and it stays
honest where South Water bends onto the dry bank and a vertical cut through its corridor
is half as long again as the corridor is wide. Ground is sampled separately, on a square
grid, because dryness is a property of a place and not of a column.

**Dry means the same zero the rest of this project uses** — `measure_no_build_ground`'s
`WATER_SURFACE_M`, sampled from the committed 1834 heightfield, one millimetre above the
water rather than a freeboard. `--counterfactual` re-derives the whole plat grid with the
control-centred line standing in as the block grid's own control, which is the cost of the
branch that moves the lots.

    tools/measure_corridor_strip.py                 the table
    tools/measure_corridor_strip.py --counterfactual what branch A costs the grid
    tools/measure_corridor_strip.py --json          the readings, machine-readable
    tools/measure_corridor_strip.py --gate          the ratchet check.sh runs
    tools/measure_corridor_strip.py --self-test     the assertions still fire
    tools/measure_corridor_strip.py --write-baseline   only to record a ruling
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import generate_plat_lots as plat  # noqa: E402
from generate_plat_lots import DATA, load, point_in_polygon  # noqa: E402
from heightfield import Heightfield  # noqa: E402
from plat_corridors import control_offsets, corridors, sampled  # noqa: E402
from plat_occupancy import footprints, layers  # noqa: E402
from exact_sums import consistent_reading  # noqa: E402

BASELINE = ROOT / "tools" / "corridor_strip_baseline.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"

# The scanline pitch the areas are integrated at. 0.05 m over South Water's 716 m of
# drawn corridor is 14,000 columns and costs milliseconds; the figure it produces agrees
# with the analytic 8.58 m x length to under a square metre, which is the point of
# quoting it at all.
AREA_PITCH_M = 0.05
# The square grid dryness is sampled on. Coarser on purpose: the heightfield's own cell
# is metres, so sampling it finer than this measures the interpolation and not the ground.
GROUND_PITCH_M = 0.5
# The same zero `measure_no_build_ground` and `measure_south_bank_ground` use.
WATER_SURFACE_M = 0.0
# Footprint edges are sampled at this pitch before the band test, the same reason
# `plat_corridors.SAMPLE_M` exists: a band 8.58 m deep is narrower than several of the
# footprints that cross it, so a vertex test alone would miss a building that straddles it.
FOOTPRINT_PITCH_M = 0.5


def crossings(ring: list, easting: float) -> list[tuple[float, float]]:
    """The northing intervals a ring covers on the vertical line at `easting`.

    Even-odd, half-open on the lower vertex so a scanline through a vertex is counted
    once. Returns disjoint intervals in increasing northing.
    """
    hits = []
    count = len(ring)
    for i in range(count):
        ax, ay = ring[i]
        bx, by = ring[(i + 1) % count]
        if (ax <= easting < bx) or (bx <= easting < ax):
            hits.append(ay + (by - ay) * (easting - ax) / (bx - ax))
    hits.sort()
    return [(hits[i], hits[i + 1]) for i in range(0, len(hits) - 1, 2)]


def without(spans: list, cut: list) -> list:
    """`spans` minus `cut`, both lists of disjoint intervals in increasing order."""
    out = []
    for lo, hi in spans:
        pieces = [(lo, hi)]
        for cut_lo, cut_hi in cut:
            kept = []
            for piece_lo, piece_hi in pieces:
                if cut_hi <= piece_lo or cut_lo >= piece_hi:
                    kept.append((piece_lo, piece_hi))
                    continue
                if piece_lo < cut_lo:
                    kept.append((piece_lo, cut_lo))
                if cut_hi < piece_hi:
                    kept.append((cut_hi, piece_hi))
            pieces = kept
        out += pieces
    return out


class Bands:
    """The two bands one re-centred street's displacement opens, as a queryable pair."""

    def __init__(self, street_id: str, drawn: list, control: list) -> None:
        self.street_id = street_id
        self.drawn = drawn
        self.control = control
        eastings = [point[0] for point in drawn] + [point[0] for point in control]
        self.west, self.east = min(eastings), max(eastings)

    def spans(self, easting: float, band: str) -> list:
        drawn = crossings(self.drawn, easting)
        control = crossings(self.control, easting)
        if band == "abandoned":
            return without(drawn, control)
        if band == "claimed":
            return without(control, drawn)
        return without(drawn, without(drawn, control))  # the shared middle

    def holds(self, point: tuple[float, float], band: str) -> bool:
        easting, northing = point
        if not self.west <= easting <= self.east:
            return False
        return any(lo <= northing <= hi for lo, hi in self.spans(easting, band))

    def columns(self, band: str):
        easting = self.west + AREA_PITCH_M / 2
        while easting < self.east:
            yield easting, self.spans(easting, band)
            easting += AREA_PITCH_M


def band_geometry(bands: Bands, band: str) -> dict:
    """Area and the vertical-cut width distribution, integrated along the scanline."""
    area = 0.0
    widths = []
    for _, spans in bands.columns(band):
        cut = sum(hi - lo for lo, hi in spans)
        area += cut * AREA_PITCH_M
        if cut > 0:
            widths.append(cut)
    # min, mean and max of the same samples, asserted against each other: a mean
    # outside its own bounds is drift, not a measurement (T-1486).
    cut = (consistent_reading(widths, 2, label="corridor cut width (m)")
           if widths else (0.0, 0.0, 0.0))
    return {
        "area_m2": round(area, 1),
        "columns": len(widths),
        "cut_width_min_m": cut[0],
        "cut_width_max_m": cut[2],
        "cut_width_mean_m": cut[1],
    }


def band_samples(bands: Bands, band: str):
    """Every point of a square grid at `GROUND_PITCH_M` that falls inside a band.

    One generator for both of the questions asked about the ground, so the dryness and
    the lot overlap are answered over exactly the same points and cannot disagree about
    where the band is.
    """
    easting = bands.west + GROUND_PITCH_M / 2
    while easting < bands.east:
        for lo, hi in bands.spans(easting, band):
            northing = lo + GROUND_PITCH_M / 2
            while northing < hi:
                yield easting, northing
                northing += GROUND_PITCH_M
        easting += GROUND_PITCH_M


def band_ground(bands: Bands, band: str, field: Heightfield) -> dict:
    """How much of a band is dry, wet, or off the modelled ground entirely."""
    cell = GROUND_PITCH_M * GROUND_PITCH_M
    dry = wet = unmodelled = 0.0
    for easting, northing in band_samples(bands, band):
        if not field.covers(easting, northing):
            unmodelled += cell
        elif field.height(easting, northing) > WATER_SURFACE_M:
            dry += cell
        else:
            wet += cell
    total = dry + wet + unmodelled
    return {
        "sampled_m2": round(total, 1),
        "dry_m2": round(dry, 1),
        "wet_m2": round(wet, 1),
        "unmodelled_m2": round(unmodelled, 1),
        "dry_pct": round(100.0 * dry / total, 1) if total else 0.0,
    }


def band_lots(bands: Bands, band: str) -> list[dict]:
    """Every platted lot a band overlaps, and by how much — AREA, not contact.

    The abandoned band's south edge and the block's north face are the same offset of the
    same line, so every lot on the row TOUCHES the band along its whole frontage and none
    of them is in it. A contact test would have reported sixteen lots lapped and the
    answer to the ticket's own question would have been wrong by sixteen. So the overlap
    is measured as area over the band's own sample grid: a lot that merely abuts scores
    zero, and the day a redrawn line pushes a corridor into the lots, this counts it.
    """
    grid = json.loads(LOTS.read_text(encoding="utf-8"))
    candidates = []
    for block in grid["blocks"]:
        for lot in block["lots"]:
            polygon = [(float(e), float(n)) for e, n in lot["polygon"]]
            eastings = [e for e, _ in polygon]
            northings = [n for _, n in polygon]
            candidates.append((block["id"], lot, polygon,
                               (min(eastings), max(eastings), min(northings), max(northings))))
    cell = GROUND_PITCH_M * GROUND_PITCH_M
    lapped: dict[tuple, float] = {}
    for easting, northing in band_samples(bands, band):
        for block_id, lot, polygon, (w, e, s, n) in candidates:
            if not (w <= easting <= e and s <= northing <= n):
                continue
            if point_in_polygon((easting, northing), polygon):
                key = (block_id, lot.get("tier"), lot.get("plat_lot_number"))
                lapped[key] = lapped.get(key, 0.0) + cell
                break
    return [{"block": block_id, "tier": tier, "plat_lot_number": number,
             "overlap_m2": round(area, 1)}
            for (block_id, tier, number), area in sorted(lapped.items(), key=str)]


def band_structures(bands: Bands, band: str) -> list[dict]:
    """Every committed structure whose footprint laps a band, with its evidence layer."""
    datum = load(DATA / "datum.json")
    layer = layers()
    found: dict[str, int] = {}
    for structure_id, polygon in footprints(datum):
        points = sampled(polygon, FOOTPRINT_PITCH_M)
        lapped = sum(1 for point in points if bands.holds(point, band))
        if lapped:
            found[structure_id] = found.get(structure_id, 0) + lapped
    return [{"id": sid, "layer": layer.get(sid), "samples_in_band": found[sid]}
            for sid in sorted(found)]


def recentred_streets() -> dict:
    """Every street whose committed control does not reproduce its drawn line."""
    return {sid: v for sid, v in control_offsets().items() if v["verdict"] == "recentred"}


def measure() -> dict:
    field = Heightfield.load(EPOCH)
    if field is None:
        raise SystemExit("the 1834 epoch carries no committed heightfield")
    drawn_lanes = corridors(False)
    control_lanes = corridors(True)
    out = {"streets": {}}
    for street_id, offset in sorted(recentred_streets().items()):
        bands = Bands(street_id, drawn_lanes[street_id]["ring"],
                      control_lanes[street_id]["ring"])
        entry = {
            "name": drawn_lanes[street_id]["name"],
            "offset_m": offset["offset_m"],
            "control_points": [p["control"] for p in offset["points"]],
            "drawn_corridor_m2": round(band_geometry(bands, "abandoned")["area_m2"]
                                       + band_geometry(bands, "shared")["area_m2"], 1),
            "bands": {},
        }
        for band in ("abandoned", "claimed"):
            entry["bands"][band] = {
                **band_geometry(bands, band),
                "ground": band_ground(bands, band, field),
                "lots": band_lots(bands, band),
                "structures": band_structures(bands, band),
            }
        out["streets"][street_id] = entry
    return out


def counterfactual() -> dict:
    """Branch A priced: the plat grid re-derived with the control as the BLOCK grid's line.

    The ticket's fork is whether the block grid on this reach is offset from the control
    too. If it is, `block_edges` reads the control-centred line and the blocks move with
    it. This runs that derivation through the committed generator rather than reasoning
    about it, and reports what the grid loses.
    """
    before = plat.grid_from_inputs()
    original = plat.street_lines

    def shifted(streets: dict) -> dict:
        lines = original(streets)
        for street_id, offset in control_offsets(lines).items():
            if offset["verdict"] != "recentred":
                continue
            shift = float(offset["offset_m"])
            index = 1 if street_id in plat.EW_STREETS else 0
            lines[street_id]["points"] = [
                (e, n + shift) if index else (e + shift, n)
                for e, n in lines[street_id]["points"]]
            key = "mean_n" if index else "mean_e"
            lines[street_id][key] = lines[street_id][key] + shift
        return lines

    plat.street_lines = shifted
    try:
        after = plat.grid_from_inputs()
    finally:
        plat.street_lines = original

    was = {block["id"]: block for block in before["blocks"]}
    now = {block["id"]: block for block in after["blocks"]}
    lost = []
    for block_id in sorted(set(was) - set(now)):
        reason = next((o["reason"] for o in after["omitted"] if o["id"] == block_id), "")
        lost.append({"id": block_id, "lots": len(was[block_id]["lots"]), "reason": reason})
    moved = []
    recut = 0
    for block_id in sorted(set(was) & set(now)):
        if was[block_id]["boundary_local_enu_m"] == now[block_id]["boundary_local_enu_m"]:
            continue
        recut += sum(1 for a, b in zip(was[block_id]["lots"], now[block_id]["lots"])
                     if a["polygon"] != b["polygon"])
        moved.append({"id": block_id,
                      "depth_before_m": was[block_id]["depth_m"],
                      "depth_after_m": now[block_id]["depth_m"],
                      "lots": len(was[block_id]["lots"])})
    return {
        "blocks_before": before["summary"]["blocks"], "blocks_after": after["summary"]["blocks"],
        "lots_before": before["summary"]["lots"], "lots_after": after["summary"]["lots"],
        "blocks_moved": moved, "lots_recut": recut, "blocks_lost": lost,
        "roofs_on_lost_blocks": roofs_on([b["id"] for b in lost]),
        "roofs_on_moved_blocks": roofs_on([b["id"] for b in moved]),
    }


def roofs_on(block_ids: list[str]) -> dict:
    """Committed roofs standing on the lots of the named blocks, split by evidence layer.

    Centroid, not lap: the question is which roofs a re-cut lot schedule OWNS, and that
    is the test `plat_occupancy` already uses to decide whether a lot can see a building.
    """
    if not block_ids:
        return {"total": 0}
    grid = json.loads(LOTS.read_text(encoding="utf-8"))
    wanted = [b for b in grid["blocks"] if b["id"] in set(block_ids)]
    datum = load(DATA / "datum.json")
    layer = layers()
    found = set()
    for structure_id, polygon in footprints(datum):
        centroid = (sum(e for e, _ in polygon) / len(polygon),
                    sum(n for _, n in polygon) / len(polygon))
        for block in wanted:
            if any(point_in_polygon(centroid, lot["polygon"]) for lot in block["lots"]):
                found.add(structure_id)
                break
    counts: dict[str, int] = {"total": len(found)}
    for structure_id in found:
        key = layer.get(structure_id) or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def report(result: dict, cf: dict | None = None) -> None:
    for street_id, entry in result["streets"].items():
        print(f"\n{entry['name']} ({street_id}) — the corridor is re-centred "
              f"{entry['offset_m']:+.2f} m onto {', '.join(entry['control_points'])}")
        print(f"  the drawn corridor is {entry['drawn_corridor_m2']:,.0f} m2")
        for band, data in entry["bands"].items():
            ground = data["ground"]
            share = 100.0 * data["area_m2"] / entry["drawn_corridor_m2"]
            print(f"\n  {band.upper():<10} {data['area_m2']:,.0f} m2 "
                  f"({share:.0f}% of the corridor's own area), "
                  f"cut {data['cut_width_min_m']:.2f}-{data['cut_width_max_m']:.2f} m")
            print(f"    ground   {ground['dry_pct']:.1f}% dry "
                  f"({ground['dry_m2']:,.0f} m2 dry, {ground['wet_m2']:,.0f} m2 water, "
                  f"{ground['unmodelled_m2']:,.0f} m2 off the modelled field)")
            print(f"    lots     {len(data['lots'])} platted lots reach into it")
            print(f"    roofs    {len(data['structures'])} committed footprints lap it")
            for structure in data["structures"]:
                print(f"               {structure['id']}  ({structure['layer']})")
    if cf is None:
        return
    print("\nBRANCH A — the block grid moves with the control:")
    print(f"  the grid goes {cf['blocks_before']} blocks / {cf['lots_before']} lots "
          f"-> {cf['blocks_after']} / {cf['lots_after']}")
    for block in cf["blocks_moved"]:
        print(f"    {block['id']}: depth {block['depth_before_m']:.2f} -> "
              f"{block['depth_after_m']:.2f} m, {block['lots']} lots re-cut")
    for block in cf["blocks_lost"]:
        print(f"    LOST {block['id']} ({block['lots']} lots) — {block['reason']}")
    print(f"  {cf['lots_recut']} lots re-cut, "
          f"{cf['roofs_on_moved_blocks']['total']} committed roofs stand on them")
    print(f"  {cf['roofs_on_lost_blocks']['total']} committed roofs stand on the "
          f"block the grid loses")


def snapshot(result: dict, cf: dict) -> dict:
    """The figures the ratchet pins — the shape of the answer, not every metre of it."""
    streets = {}
    for street_id, entry in result["streets"].items():
        streets[street_id] = {
            "offset_m": entry["offset_m"],
            "bands": {band: {"area_m2": data["area_m2"],
                             "dry_pct": data["ground"]["dry_pct"],
                             "lots": len(data["lots"]),
                             "structures": [s["id"] for s in data["structures"]]}
                      for band, data in entry["bands"].items()},
        }
    return {
        "streets": streets,
        "counterfactual": {
            "blocks_after": cf["blocks_after"], "lots_after": cf["lots_after"],
            "lots_recut": cf["lots_recut"],
            "blocks_lost": [b["id"] for b in cf["blocks_lost"]],
            # What branch A would cost in built town. Pinned since 2026-09-13 because
            # it was the one figure in the fork that moved while the fork waited: the
            # roofs on the re-cut lots went 43 -> 53 and the roofs on the block the
            # grid loses went 9 -> 18 in fourteen days of ordinary building, and the
            # ratchet said nothing because it was pinning block and lot counts only.
            "roofs_on_moved_blocks": cf["roofs_on_moved_blocks"]["total"],
            "roofs_on_lost_blocks": cf["roofs_on_lost_blocks"]["total"],
        },
    }


def gate() -> int:
    if not BASELINE.exists():
        print(f"CORRIDOR STRIP\n  - {BASELINE.relative_to(ROOT)} is missing")
        return 1
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    current = snapshot(measure(), counterfactual())
    if current == baseline["reading"]:
        streets = ", ".join(current["streets"])
        print(f"corridor strip unchanged ({streets}); the fork is still the owner's")
        return 0
    print("CORRIDOR STRIP MOVED — T-0419 is a question about these figures, so a change "
          "here changes the question:")
    print(f"  baseline  {json.dumps(baseline['reading'], sort_keys=True)}")
    print(f"  now       {json.dumps(current, sort_keys=True)}")
    print("  If a ruling or a redrawn line made this right, re-run with --write-baseline "
          "and say which in the PR.")
    return 1


def self_test() -> int:
    """The assertions this tool's conclusions rest on, and a case that breaks each.

    A gate that has only ever been shown passing is a gate nobody has read. So each
    assertion here is run twice: once against the committed tree, and once against
    geometry built to violate it.
    """
    problems = []

    def rect(west, east, south, north):
        return [(west, south), (east, south), (east, north), (west, north)]

    # 1. A rigid translation gives up exactly as much as it takes, and the band it opens
    #    is exactly as deep as the translation. Both hold on the committed tree...
    result = measure()
    for street_id, entry in result["streets"].items():
        abandoned = entry["bands"]["abandoned"]["area_m2"]
        claimed = entry["bands"]["claimed"]["area_m2"]
        if abs(abandoned - claimed) > 1.0:
            problems.append(f"{street_id}: the bands differ by "
                            f"{abs(abandoned - claimed):.1f} m2, and a translation "
                            f"cannot do that")
        depth = entry["bands"]["abandoned"]["cut_width_max_m"]
        if abs(depth - abs(entry["offset_m"])) > 0.01:
            problems.append(f"{street_id}: the band cuts {depth:.2f} m at its widest "
                            f"but the corridor moved {entry['offset_m']:.2f} m")

    # ...and on a rectangle translated 3 m, where the answer is known by hand: a band
    # 3 m deep down a 10 m frontage, on both sides, and nothing left between.
    shifted = Bands("x", rect(0.0, 10.0, 0.0, 5.0), rect(0.0, 10.0, 3.0, 8.0))
    for band in ("abandoned", "claimed"):
        geometry = band_geometry(shifted, band)
        if abs(geometry["area_m2"] - 30.0) > 0.1:
            problems.append(f"a 3 m translation of a 10 m ring opened "
                            f"{geometry['area_m2']} m2 of {band}, not 30")
        if abs(geometry["cut_width_max_m"] - 3.0) > 0.01:
            problems.append(f"the {band} band cut {geometry['cut_width_max_m']} m, not 3")

    # 2. Two identical rings open no band at all — the case the whole tool reduces to
    #    when a street's control reproduces its own drawn line.
    same = rect(0.0, 10.0, 0.0, 5.0)
    if band_geometry(Bands("x", same, same), "abandoned")["area_m2"] != 0.0:
        problems.append("two identical rings opened a band between them")

    # 3. The interval difference has to be able to split a span in two rather than
    #    truncating it, because a corridor that moved ACROSS a ring would do exactly
    #    that and the area would come out half right.
    split = without([(0.0, 10.0)], [(4.0, 6.0)])
    if split != [(0.0, 4.0), (6.0, 10.0)]:
        problems.append(f"a cut through the middle of a span produced {split}")

    for problem in problems:
        print(f"  - {problem}")
    print("self-test: " + ("FAILED" if problems
                           else "the assertions hold, and still fire when broken"))
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counterfactual", action="store_true",
                        help="price branch A: re-derive the grid off the control line")
    parser.add_argument("--json", action="store_true", help="the readings, unrounded")
    parser.add_argument("--gate", action="store_true", help="the ratchet check.sh runs")
    parser.add_argument("--self-test", action="store_true",
                        help="the assertions still fire when broken")
    parser.add_argument("--write-baseline", action="store_true",
                        help="record a ruling — never to make a red gate green")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.gate:
        return gate()

    result = measure()
    if not result["streets"]:
        print("no committed street's control disagrees with its drawn line — "
              "T-0419's band does not exist on this tree")
        return 0
    cf = counterfactual() if (args.counterfactual or args.json
                              or args.write_baseline) else None
    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "_doc": ("T-0419. The band the re-centred South Water corridor opens, and "
                     "what branch A would cost the plat grid. Written by "
                     "tools/measure_corridor_strip.py --write-baseline; the fork is the "
                     "owner's and this file only pins the figures it is asked about."),
            "tool": "tools/measure_corridor_strip.py",
            "reading": snapshot(result, cf),
        }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.relative_to(ROOT)}")
        return 0
    if args.json:
        print(json.dumps({"measure": result, "counterfactual": cf},
                         indent=1, ensure_ascii=False))
        return 0
    report(result, cf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
