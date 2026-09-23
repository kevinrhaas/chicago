#!/usr/bin/env python3
"""Generate the platted block and lot grid from the module, not from a trace.

ROADMAP K7. The 1830 Thompson plat is a PARAMETER source in this dataset — no open
high-resolution scan of it exists and the surviving artifact is a Canal Commissioners'
working copy — so its geometry is generated analytically from the module it fixes
(80-ft streets, 18-ft alleys) and snapped to the street lines this project has already
committed. Tracing the 1834 sheets instead would bake their 3.7-4.5% anisotropic paper
stretch into every block face: the corridors those draughtsmen drew run about 5 ft wide
of 80 on both sheets, which is stretch and pen placement rather than a wider street.

What each part of the output is entitled to claim, and why:

* A **block boundary** is a street centreline offset by half the platted corridor. The
  centrelines are `data/streets/1835.json`, whose own geometry confidence is `inferred`,
  and the half-width is the module. Arithmetic on inferred inputs is inferred, so that is
  what the block edges carry.
* A **lot line** is `conjectural` and stays that way. Four lots to a block face is read
  off the owner's crop of Wright's sheet at the Clark reach — block 18's north row runs
  4 3 2 and its south row 5 6 7 (`docs/RESEARCH/clark_reach_bulge_1834.md` § 8) — and a
  reading of ONE block does not document the subdivision of the other seventeen. The
  alley is worse off: 18 ft is the module, but nothing in `data/sources/` says which
  blocks were alleyed or where the alley ran inside them.
* A block is emitted only where the committed centrelines of all four of its bounding
  streets actually REACH it. Extending a street line past where this project has drawn it
  would be an invention dressed as geometry, so those blocks are listed in `omitted` with
  the street that falls short — which is the same list as the street control still owed
  under ROADMAP § S9.

Thompson's block NUMBERS reach six blocks of this grid and no more. The owner's crop
carries two numerals side by side in the South Water tier — 19 west of 18, the stream in
the La Salle corridor between them — and that fixes the step (one per block) and the
direction (falling eastward) along a row. Counting along that row numbers the tier's six
blocks, and block 16 lands on Dearborn-State, where G. Spring's 'LOT No. 7, in block No.
16 ... on Lake street' and the Mansion House's own Andreas-and-Botsford placement already
agree it should. Nothing outside the tier is numbered: how the run passes from one row to
the next is not readable from two numerals in one row. The judgement, the identification
and the refusals live in `data/traces/thompson_block_numbering.json`; this module only
stamps them. Block ids stay named for the streets that bound them, which is a description
that never goes wrong.

    tools/generate_plat_lots.py            regenerate data/traces/vectors/thompson_lots.json
    tools/generate_plat_lots.py --check    fail if the committed file is not what the
                                           module and the street lines re-derive
    tools/generate_plat_lots.py --report   where the dataset's structures fall on the grid
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
SIDECARS = DATA / "sidecars" / "1835"

FT_M = 0.3048
ALLEY_FT = 18.0
LOT_FRONTAGE_FT = 80.0

# The plat's module pitch runs 116-143 m; every larger gap between two consecutive
# streets in this table is the river, not a block. Named rather than tuned: it is the
# rule that keeps a "block" from being generated across the South Branch.
MAX_PITCH_M = 200.0

# Ordered north to south, and west to east. Restricted to the South and West Division
# grid on purpose: the north-side streets (Kinzie, North Water, Wolcott, Michigan) are
# the ones ROADMAP § S9 still records as owing control, and a block generated between
# two lines that are not yet fixed would look exactly like one that is.
EW_STREETS = ["south_water", "lake", "randolph", "washington"]
NS_STREETS = ["clinton", "canal", "market", "franklin", "wells", "lasalle", "clark",
              "dearborn", "state"]

SOURCE_IDS = ["thompson_plat_1830", "hathaway_1834", "wright_1834", "osm_streets_2026"]

RESERVED_PATH = DATA / "reconstruction" / "1835_reserved_ground.json"
NUMBERING_PATH = DATA / "traces" / "thompson_block_numbering.json"
TRACTS_PATH = DATA / "reconstruction" / "1835_survey_tracts.json"
WEST_DIVISION_PATH = DATA / "traces" / "thompson_west_division_lots.json"

# T-1104's precedence clause, carried here rather than re-invented, because the layer is
# not a partition: a tract whose ring is defined as what another tract leaves over yields
# any block a non-residual tract covers at least half of. Named, not inferred from the
# grade — `canal_section_9_remainder`'s own `boundary_from` says it is the residual.
RESIDUAL_TRACTS = {"canal_section_9_remainder"}
MAJORITY = 0.50
# Below this an overlap is the clip's own rounding, not a statement that a block is on a
# tract. 1 m2 against blocks of 10,000 m2 and up.
TOUCH_M2 = 1.0


def block_numbering() -> dict:
    """Thompson's own block numbers, for the blocks this project can reach them.

    Authored in `data/traces/thompson_block_numbering.json` and read here, the same
    shape as `reserved_blocks()`: the file carries a reading and a judgement, this
    module carries none, and the numbers land on blocks whose geometry is derived
    exactly as it was before. T-0358.

    The numerals are read off the georeferenced BPL scan of Wright's 1834 sheet, one
    crop per block, cut from that block's own committed street lines — so which block
    carries a numeral is settled by the fit and not by counting from a neighbour. The
    run turns out to REVERSE tier by tier (South Water falls eastward, Lake rises,
    Randolph falls), which is why the earlier reading was right to refuse to count
    across a tier. Blocks outside the reach of the committed grid stay unnumbered.
    """
    doc = load(NUMBERING_PATH)
    return {b["block_id"]: b for b in doc["blocks"]}, doc


def reserved_blocks() -> dict[str, dict]:
    """Blocks this project holds evidence were not private building ground.

    The module knows how to subdivide a block and has no way to ask whether the block
    was ever offered in lots. Four lots to a face is the plat's rule for ground for
    sale; drawing it on ground the town held in common asserts a sale that never
    happened, and the 665-roof programme reads the result as somewhere to build.
    So a reserved block keeps its BOUNDARY — which is derived from the street lines
    like every other block's and is not in question — and loses its SUBDIVISION.
    """
    if not RESERVED_PATH.exists():
        return {}
    return {b["block_id"]: b for b in load(RESERVED_PATH)["blocks"]}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------- the survey tract under a block


def survey_tracts() -> list[dict]:
    """The placed rings of `data/reconstruction/1835_survey_tracts.json`, and nothing else.

    T-1101 built the layer that says WHO SURVEYED WHAT GROUND. Until it existed this
    module had no way to ask which survey a block stood in, so it chose one street width
    and one block module for the whole town and said so nowhere. It can ask now. Reading
    the layer is not the same as obeying it — what the answer is worth is decided in
    `module_for`, on the arithmetic, and both are written onto every block.
    """
    doc = load(TRACTS_PATH)
    return [{
        "id": t["id"],
        "ring": [(float(e), float(n)) for e, n in t["polygon_local_enu_m"]],
        "geometry_confidence": t["geometry_confidence"],
        "residual": t["id"] in RESIDUAL_TRACTS,
    } for t in doc["tracts"] if t.get("placed") and t.get("polygon_local_enu_m")]


def tract_of(ring: list, tracts: list[dict]) -> dict:
    """Which survey tract a block stands in, under T-1104's precedence clause.

    The clipper is imported from `tools/sort_land_sales_onto_tracts.py` rather than
    written again: two implementations of the same overlap would be two answers to the
    same question, and that file's `--self-test` already holds this one to six
    constructed cases.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    from sort_land_sales_onto_tracts import overlap_area  # noqa: PLC0415

    area = polygon_area(ring)
    shares = []
    for tract in tracts:
        overlap = overlap_area(ring, tract["ring"])
        if overlap > TOUCH_M2:
            shares.append({"tract": tract["id"], "share": round(overlap / area, 4),
                           "residual": tract["residual"],
                           "geometry_confidence": tract["geometry_confidence"]})
    if not shares:
        return {"tract": None, "share": 0.0, "on": [],
                "why": "no placed tract ring in the layer covers this block"}
    shares.sort(key=lambda s: -s["share"])
    best = shares[0]
    clause = None
    if best["residual"]:
        outright = [s for s in shares[1:]
                    if not s["residual"] and s["share"] >= MAJORITY]
        if outright:
            best = outright[0]
            clause = ("the residual yielded: a non-residual tract covers this block by "
                      f"{best['share']:.0%} and canal_section_9_remainder is the layer's "
                      "only residual ring")
    return {
        "tract": best["tract"],
        "share": best["share"],
        "geometry_confidence": best["geometry_confidence"],
        "on": [s["tract"] for s in shares],
        "precedence_clause_fired": clause,
    }


# ------------------------------------------------------ the module under a block


def west_division() -> dict:
    """The West Division's own module, as the Thompson sheet PRINTS it (T-0689).

    Two columns of 180-ft lots backing onto a north-south alley, five 75 3/5-ft lots to
    a column, and the block square at 378 ft — a different ARRANGEMENT from the South
    Division's four-to-a-face with an east-west alley, not just a different frontage.
    The street set is taken from the block table's own `bounded_*_by` fields, so which
    streets are West Division streets is read off that file too and not asserted here.
    """
    doc = load(WEST_DIVISION_PATH)
    streets = set()
    for entry in doc["blocks"]:
        streets.add(entry["bounded_west_by"])
        streets.add(entry["bounded_east_by"])
    figures = doc["the_west_division_block"]
    return {
        "streets": {s for s in streets if s.replace("_", "").isalpha()},
        "lot_frontage_ft": float(figures["lot_frontage_ft"]),
        "lot_depth_ft": float(figures["lot_depth_ft"]),
        "alley_width_ft": float(figures["alley_width_ft"]),
        "block_east_west_ft": float(figures["block_east_west_ft"]),
        "block_north_south_ft": float(figures["block_north_south_ft_five_row_tiers"]),
        "street_module_ft": float(figures["north_south_street_module_ft"]),
        "confidence": figures["confidence"],
        "printed_frontage": figures["lot_frontage_as_printed"],
        "authored_in": "data/traces/thompson_west_division_lots.json",
    }


def module_for(entry: dict, bounded_by: dict, west: dict, spacing_ft: float) -> dict:
    """Which module this block was subdivided on, and — where another one is held — why not it.

    T-1105. The South Division module is the only one this file can BUILD, and for
    nineteen blocks out of nineteen that is also the only one the evidence allows. Two of
    them stand west of the river, where the plat prints a different arrangement; the
    arithmetic that refuses it is computed here and carried on the block, so a reader
    sees a refusal with a figure rather than a silent 80 ft.
    """
    taken = {
        "module": "south_division_thompson_1830",
        "lot_frontage_ft": LOT_FRONTAGE_FT,
        "alley_width_ft": ALLEY_FT,
        "alley_runs": "east-west, mid-block",
        "chosen_by": "the only module this generator can seat on the committed street lines",
    }
    if not {bounded_by["west"], bounded_by["east"]} <= west["streets"]:
        taken["division"] = "south"
        return taken

    taken["division"] = "west"
    face_ft = entry["frontage_m"] / FT_M
    depth_ft = entry["depth_m"] / FT_M
    columns_ft = 2 * west["lot_depth_ft"] + west["alley_width_ft"]
    rows = depth_ft / west["lot_frontage_ft"]
    taken["west_division_module_refused"] = {
        "module": "west_division_thompson_1830",
        "authored_in": west["authored_in"],
        "confidence_of_the_figures": west["confidence"],
        "what_it_asks_for": (
            f"two columns of {west['lot_depth_ft']:.0f} ft lots backing onto an "
            f"{west['alley_width_ft']:.0f} ft north-south alley — {columns_ft:.0f} ft "
            f"east to west — and {west['printed_frontage']} ft of frontage to a lot, "
            f"{west['block_north_south_ft']:.0f} ft north to south"),
        "what_the_committed_lines_give": {
            "east_west_face_ft": round(face_ft, 1),
            "north_south_depth_ft": round(depth_ft, 1),
        },
        "the_arithmetic": (
            f"the two lot columns alone need {2 * west['lot_depth_ft']:.0f} ft and this "
            f"block's face is {face_ft:.1f} ft, so the arrangement does not fit before "
            f"the alley is cut; {west['block_east_west_ft']:.0f} ft is "
            f"{west['block_east_west_ft'] - face_ft:.1f} ft more than the block has. "
            f"North to south {depth_ft:.1f} ft divides into {rows:.2f} lots of "
            f"{west['printed_frontage']} ft, and a plat does not print a fifth of a lot."),
        "why_the_lines_and_not_the_module": (
            "the module is `documented` — figures printed on the sheet and numerals "
            f"counted in a block — and it closes exactly at {west['block_east_west_ft']:.0f} "
            "ft each way. What does not close is this project's West Division street "
            f"spacing: Clinton to Canal is committed at {spacing_ft:.1f} ft against "
            f"the plat's own {west['street_module_ft']:.0f} ft. Seating the printed module "
            "would mean moving those lines, which is T-0445's ticket and not this one's, "
            "and the same short spacing is what T-0444 reported."),
        "so": ("this block keeps the South Division subdivision it was already built on, "
               "and says here that it is not the module the West Division plat prints"),
    }
    return taken


# ---------------------------------------------------------------- geometry helpers

def unit(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy)
    if length == 0:
        raise SystemExit("a street segment of zero length cannot carry a direction")
    return dx / length, dy / length


def offset_polyline(points: list[tuple[float, float]], distance: float,
                    toward: tuple[float, float]) -> list[tuple[float, float]]:
    """Shift a polyline `distance` metres to the side `toward` points at.

    Each vertex moves along its own segment normal; consecutive offset segments are
    joined by intersecting them (a miter), which is exact for the near-straight lines
    these streets are and does not fold on the shallow bends South Water carries.
    """
    segments = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        ux, uy = unit(bx - ax, by - ay)
        nx, ny = -uy, ux
        if nx * toward[0] + ny * toward[1] < 0:
            nx, ny = -nx, -ny
        segments.append(((ax + nx * distance, ay + ny * distance),
                         (bx + nx * distance, by + ny * distance)))
    out = [segments[0][0]]
    for first, second in zip(segments, segments[1:]):
        crossing = line_intersection(first[0], first[1], second[0], second[1])
        out.append(crossing if crossing else first[1])
    out.append(segments[-1][1])
    return out


def line_intersection(p1, p2, p3, p4):
    """Intersection of the infinite lines through p1p2 and p3p4, or None if parallel."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-9:
        return None
    a = x1 * y2 - y1 * x2
    b = x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / denominator,
            (a * (y3 - y4) - (y1 - y2) * b) / denominator)


def cross_polyline(polyline: list[tuple[float, float]], line: tuple, reach_m: float):
    """Where `polyline` crosses the infinite `line`, and the vertex it happens after.

    Returns (point, index, extrapolated_m). A crossing found on one of the polyline's
    own segments is a street that reaches the block. A crossing beyond its ends is
    reported with how far past the drawn end it lies, so the caller can refuse it.
    """
    (lx1, ly1), (lx2, ly2) = line

    def side(p):
        return (lx2 - lx1) * (p[1] - ly1) - (ly2 - ly1) * (p[0] - lx1)

    for index, (a, b) in enumerate(zip(polyline, polyline[1:])):
        sa, sb = side(a), side(b)
        if sa == 0 or sb == 0 or (sa > 0) != (sb > 0):
            point = line_intersection(a, b, (lx1, ly1), (lx2, ly2))
            if point:
                return point, index, 0.0
    # No segment straddles it: extend the nearer end and measure the reach.
    best = None
    for end, neighbour, index in ((polyline[0], polyline[1], -1),
                                  (polyline[-1], polyline[-2], len(polyline) - 1)):
        point = line_intersection(end, neighbour, (lx1, ly1), (lx2, ly2))
        if point is None:
            continue
        gap = math.dist(point, end)
        if best is None or gap < best[2]:
            best = (point, index, gap)
    if best is None or best[2] > reach_m:
        return None, None, (best[2] if best else float("inf"))
    return best


def polyline_between(polyline, start, start_index, end, end_index):
    """The run of `polyline` from one crossing to the other, ends included."""
    if start_index <= end_index:
        middle = polyline[start_index + 1:end_index + 1]
    else:
        middle = list(reversed(polyline[end_index + 1:start_index + 1]))
    return [start] + middle + [end]


def resample(chain: list[tuple[float, float]], fraction: float) -> tuple[float, float]:
    """The point `fraction` of the way along a chain, by arc length."""
    lengths = [math.dist(a, b) for a, b in zip(chain, chain[1:])]
    target = sum(lengths) * fraction
    for (a, b), length in zip(zip(chain, chain[1:]), lengths):
        if target <= length or length == 0:
            t = 0.0 if length == 0 else target / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        target -= length
    return chain[-1]


def chain_length(chain) -> float:
    return sum(math.dist(a, b) for a, b in zip(chain, chain[1:]))


def polygon_area(ring) -> float:
    total = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total) / 2.0


def point_in_polygon(point, ring) -> bool:
    e, n = point
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > n) != (by > n):
            x = ax + (n - ay) * (bx - ax) / (by - ay)
            if x > e:
                inside = not inside
    return inside


def rounded(points, places: int = 2):
    return [[round(e, places), round(n, places)] for e, n in points]


# ---------------------------------------------------------------- the grid itself

def street_lines(streets: dict) -> dict:
    lines = {}
    for street in streets["streets"]:
        points = [(float(e), float(n)) for e, n in street["path_local_enu_m"]]
        lines[street["id"]] = {
            "id": street["id"],
            "name": street["name_1835"],
            "points": points,
            "mean_e": sum(p[0] for p in points) / len(points),
            "mean_n": sum(p[1] for p in points) / len(points),
            "confidence": street.get("geometry_confidence", "reconstructed"),
        }
    return lines


def block_edges(lines: dict, half_width: float) -> dict:
    """Both platted edges of every street: the block faces the corridor is cut between."""
    edges = {}
    for street_id, street in lines.items():
        if street_id in EW_STREETS:
            edges[street_id] = {
                "south": offset_polyline(street["points"], half_width, (0.0, -1.0)),
                "north": offset_polyline(street["points"], half_width, (0.0, 1.0)),
            }
        elif street_id in NS_STREETS:
            edges[street_id] = {
                "east": offset_polyline(street["points"], half_width, (1.0, 0.0)),
                "west": offset_polyline(street["points"], half_width, (-1.0, 0.0)),
            }
    return edges


def build_block(north_id, south_id, west_id, east_id, lines, edges, reach_m):
    """The quadrilateral between four platted corridors, or why it cannot be built."""
    north_edge = edges[north_id]["south"]
    south_edge = edges[south_id]["north"]
    west_edge = edges[west_id]["east"]
    east_edge = edges[east_id]["west"]
    west_line = (west_edge[0], west_edge[-1])
    east_line = (east_edge[0], east_edge[-1])
    north_line = (north_edge[0], north_edge[-1])
    south_line = (south_edge[0], south_edge[-1])

    nw, nw_i, nw_gap = cross_polyline(north_edge, west_line, reach_m)
    ne, ne_i, ne_gap = cross_polyline(north_edge, east_line, reach_m)
    sw, sw_i, sw_gap = cross_polyline(south_edge, west_line, reach_m)
    se, se_i, se_gap = cross_polyline(south_edge, east_line, reach_m)
    for point, gap, street_id in ((nw, nw_gap, north_id), (ne, ne_gap, north_id),
                                  (sw, sw_gap, south_id), (se, se_gap, south_id)):
        if point is None:
            return None, (f"{lines[street_id]['name']}'s committed centreline stops "
                          f"{gap:.0f} m short of this block")
    for edge_id, edge, near, far in ((west_id, west_edge, north_line, south_line),
                                     (east_id, east_edge, north_line, south_line)):
        for line in (near, far):
            point, _, gap = cross_polyline(edge, line, reach_m)
            if point is None:
                return None, (f"{lines[edge_id]['name']}'s committed centreline stops "
                              f"{gap:.0f} m short of this block")

    # AND THE TWO ROWS MUST NOT HAVE CROSSED. Four crossings can all be found and still
    # describe no block: where an east-west street bends onto the dry bank it can converge
    # on the row below it to less than a corridor, and then the block's north-west corner
    # falls SOUTH of its south-west one. The ring is a bowtie, `polygon_area` returns the
    # difference of its two lobes rather than nothing, and the block is emitted with a
    # plausible area and a plausible depth. Measured 2026-08-29 by T-0183 at
    # blk_south_water_market, where closing South Water's west end onto Market's corridor
    # produced a 4,411 m2 "block" 36.85 m deep whose north-west corner stood 14.9 m south
    # of its south-west one. It is `node_rule`'s own failure mode one layer down — an
    # answer that looks right rather than no answer — so it is refused here by name.
    for corner_n, corner_s, side in ((nw, sw, "west"), (ne, se, "east")):
        depth = corner_n[1] - corner_s[1]
        if depth <= 0.0:
            return None, (f"{lines[north_id]['name']} and {lines[south_id]['name']} have "
                          f"crossed by this block's {side} corner \u2014 their platted "
                          f"corridors overlap by {-depth:.1f} m there, so what lies between "
                          "them is not a block")

    north_chain = polyline_between(north_edge, nw, nw_i, ne, ne_i)
    south_chain = polyline_between(south_edge, sw, sw_i, se, se_i)
    ring = north_chain + list(reversed(south_chain))
    return {"ring": ring, "north_chain": north_chain, "south_chain": south_chain}, None


def subdivide(block: dict, alley_m: float, frontage_m: float) -> dict:
    """Two tiers of lots either side of a mid-block alley, fronting the E-W streets."""
    north_chain, south_chain = block["north_chain"], block["south_chain"]
    frontage = (chain_length(north_chain) + chain_length(south_chain)) / 2.0
    count = max(1, round(frontage / frontage_m))
    stations = []
    for index in range(count + 1):
        fraction = index / count
        top = resample(north_chain, fraction)
        bottom = resample(south_chain, fraction)
        depth = math.dist(top, bottom)
        # The alley is centred, so each tier is (depth - alley) / 2 deep at this station.
        a = (0.5 - alley_m / (2 * depth)) if depth else 0.0
        b = (0.5 + alley_m / (2 * depth)) if depth else 1.0
        stations.append({
            "top": top,
            "alley_north": (top[0] + (bottom[0] - top[0]) * a,
                            top[1] + (bottom[1] - top[1]) * a),
            "alley_south": (top[0] + (bottom[0] - top[0]) * b,
                            top[1] + (bottom[1] - top[1]) * b),
            "bottom": bottom,
            "depth": depth,
        })
    lots = []
    for index in range(count):
        left, right = stations[index], stations[index + 1]
        lots.append({
            "tier": "north",
            "frontage_m": round(math.dist(left["top"], right["top"]), 2),
            "depth_m": round((left["depth"] + right["depth"]) / 2 / 2 - alley_m / 2, 2),
            "polygon": rounded([left["top"], right["top"],
                                right["alley_north"], left["alley_north"]]),
        })
        lots.append({
            "tier": "south",
            "frontage_m": round(math.dist(left["bottom"], right["bottom"]), 2),
            "depth_m": round((left["depth"] + right["depth"]) / 2 / 2 - alley_m / 2, 2),
            "polygon": rounded([left["alley_south"], right["alley_south"],
                                right["bottom"], left["bottom"]]),
        })
    alley = rounded([stations[0]["alley_north"], stations[-1]["alley_north"],
                     stations[-1]["alley_south"], stations[0]["alley_south"]])
    return {"lots": lots, "alley": alley, "frontage_m": frontage, "count": count}


def stamp_number(entry: dict, record: dict, scheme: dict) -> None:
    """Put the plat's number on a block, and the scheme's numbers on its lots.

    The lots are numbered by where they LIE, not by the order the subdivision
    emitted them: the scheme runs 1-4 east to west along the north row and 5-8 west
    to east along the south row, and reading that off a list index would make the
    numbering depend on which way `data/streets/1835.json` happens to draw a street.
    """
    entry["plat_block_number"] = {
        "number": record["number"],
        "confidence": record["confidence"],
        "numeral_on_sheet": record["numeral_on_sheet"],
        "sources": record["sources"],
        "authored_in": "data/traces/thompson_block_numbering.json",
        "note": record["note"],
    }
    lots = entry.get("lots") or []
    per_face = len(lots) // 2
    if per_face != 4 or len(lots) != 2 * per_face:
        # The scheme is 1-4 and 5-8. A block the module divided some other way is
        # left unnumbered rather than renumbered to fit, and says so.
        entry["plat_block_number"]["lots_not_numbered"] = (
            f"the module divided this block into {len(lots)} lot(s), and the scheme read "
            "off block 18 numbers four to a face; a scheme stretched to fit is an invention")
        return
    north = sorted((l for l in lots if l["tier"] == "north"),
                   key=lambda l: -sum(pt[0] for pt in l["polygon"]) / len(l["polygon"]))
    south = sorted((l for l in lots if l["tier"] == "south"),
                   key=lambda l: sum(pt[0] for pt in l["polygon"]) / len(l["polygon"]))
    for index, lot in enumerate(north + south):
        lot["plat_lot_number"] = index + 1
        lot["plat_lot_confidence"] = scheme["confidence"]


def grid_from_inputs() -> dict:
    control = load(DATA / "traces" / "street_control.json")
    streets = load(DATA / "streets" / "1835.json")
    module = control["platted_street"]
    half_width = float(module["half_width_m"])
    alley_m = round(ALLEY_FT * FT_M, 4)
    frontage_m = round(LOT_FRONTAGE_FT * FT_M, 4)
    # A crossing may be sought this far past a drawn centreline's end: half a corridor,
    # which is the distance a street line stops short of the far kerb when it is drawn
    # to the junction it ends at rather than through it. Anything further is refused.
    reach_m = half_width

    lines = street_lines(streets)
    missing = [s for s in EW_STREETS + NS_STREETS if s not in lines]
    if missing:
        raise SystemExit(f"street table is missing {', '.join(missing)}")
    edges = block_edges(lines, half_width)

    rows = sorted((s for s in EW_STREETS), key=lambda s: -lines[s]["mean_n"])
    columns = sorted((s for s in NS_STREETS), key=lambda s: lines[s]["mean_e"])

    field = None
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from heightfield import Heightfield  # noqa: PLC0415
        field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    except Exception:  # pragma: no cover - the field is committed; absence is reported
        field = None
    if field is None:
        raise SystemExit("cannot build the grid: the committed heightfield is missing")

    reserved = reserved_blocks()
    numbers, numbering_doc = block_numbering()
    tracts = survey_tracts()
    west = west_division()
    # The one spacing the West Division refusal turns on, re-derived here from the same
    # committed centrelines every block edge is offset from — never a figure typed in.
    spacing_ft = abs(lines["clinton"]["mean_e"] - lines["canal"]["mean_e"]) / FT_M
    blocks, omitted = [], []
    for north_id, south_id in zip(rows, rows[1:]):
        pitch_n = abs(lines[north_id]["mean_n"] - lines[south_id]["mean_n"])
        for west_id, east_id in zip(columns, columns[1:]):
            block_id = f"blk_{north_id}_{west_id}"
            pitch_e = abs(lines[east_id]["mean_e"] - lines[west_id]["mean_e"])
            bounded_by = {"north": north_id, "south": south_id,
                          "west": west_id, "east": east_id}
            if pitch_n > MAX_PITCH_M or pitch_e > MAX_PITCH_M:
                omitted.append({
                    "id": block_id, "bounded_by": bounded_by,
                    "reason": (f"the streets are {max(pitch_n, pitch_e):.0f} m apart, past "
                               f"the {MAX_PITCH_M:.0f} m the plat's module allows a block "
                               f"— what lies between them is the river, not a block")})
                continue
            built, why = build_block(north_id, south_id, west_id, east_id,
                                     lines, edges, reach_m)
            if built is None:
                omitted.append({"id": block_id, "bounded_by": bounded_by, "reason": why})
                continue
            ring = built["ring"]
            wet = [p for p in ring if not field.covers(*p) or field.height(*p) < 0.0]
            if wet:
                omitted.append({
                    "id": block_id, "bounded_by": bounded_by,
                    "reason": (f"{len(wet)} of {len(ring)} corners fall on water or beyond "
                               "the modelled ground; a platted block there is not something "
                               "this dataset can stand behind")})
                continue
            divided = subdivide(built, alley_m, frontage_m)
            entry = {
                "id": block_id,
                "bounded_by": bounded_by,
                "boundary_local_enu_m": rounded(ring),
                "area_m2": round(polygon_area(ring), 1),
                "frontage_m": round(divided["frontage_m"], 2),
                "frontage_ft": round(divided["frontage_m"] / FT_M, 1),
                "depth_m": round(polygon_area(ring) / divided["frontage_m"], 2),
                "lots_per_face": divided["count"],
                "alley_local_enu_m": divided["alley"],
                "lots": divided["lots"],
            }
            entry["survey_tract"] = tract_of(ring, tracts)
            entry["module"] = module_for(entry, bounded_by, west, spacing_ft)
            hold = reserved.get(block_id)
            if hold:
                # The boundary stays; the subdivision goes. `lots_per_face` reports what
                # the module WOULD have drawn, so the withdrawal is visible here rather
                # than looking like a block the generator failed on.
                entry["reserved"] = {
                    "reserved_for": hold["reserved_for"],
                    "name": hold["name"],
                    "confidence": hold["confidence"],
                    "sources": hold["sources"],
                    "authored_in": "data/reconstruction/1835_reserved_ground.json",
                    "note": "This block is not subdivided. See the reservation record for "
                            "the evidence and for what may stand here.",
                }
                entry["lots_per_face_withheld"] = entry.pop("lots_per_face")
                entry["alley_local_enu_m"] = None
                entry["lots"] = []
            blocks.append(entry)

    scheme = numbering_doc["lot_numbering"]
    for entry in blocks:
        record = numbers.get(entry["id"])
        if record:
            stamp_number(entry, record, scheme)
    for entry in omitted:
        record = numbers.get(entry["id"])
        if record:
            # A block the grid cannot draw still had a number on the plat. Carrying it
            # here keeps the two facts — the plat numbered it, this project cannot
            # place it — in one place instead of one contradicting the other's absence.
            entry["plat_block_number"] = {
                "number": record["number"],
                "confidence": record["confidence"],
                "numeral_on_sheet": record["numeral_on_sheet"],
                "sources": record["sources"],
                "authored_in": "data/traces/thompson_block_numbering.json",
                "note": record["note"],
            }
    unplaced = sorted(set(numbers) - {b["id"] for b in blocks} - {o["id"] for o in omitted})
    if unplaced:
        raise SystemExit("data/traces/thompson_block_numbering.json numbers "
                         f"{', '.join(unplaced)}, which the grid neither builds nor omits")

    return assemble(blocks, omitted, module, alley_m, frontage_m, reach_m, lines,
                    numbering_doc, tracts, west, spacing_ft)


def _count_tracts(blocks: list) -> dict:
    counts: dict[str, int] = {}
    for block in blocks:
        key = block["survey_tract"]["tract"] or "no placed ring covers it"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def assemble(blocks, omitted, module, alley_m, frontage_m, reach_m, lines,
             numbering_doc, tracts, west, spacing_ft) -> dict:
    faces = [lot["frontage_m"] for b in blocks for lot in b["lots"]]
    return {
        "_doc": (
            "The platted block and lot grid, generated from the Thompson module and snapped "
            "to this project's committed street lines — never traced off the 1834 sheets, "
            "whose 3.7-4.5% anisotropic stretch would arrive as 4% of wobble in every block "
            "face. A block edge here is a street centreline from data/streets/1835.json "
            "offset by half the platted corridor; a lot line is the module divided into it. "
            "Written by tools/generate_plat_lots.py, which re-derives this file byte for byte "
            "offline on every commit (tools/check.sh). Block ids name the streets that bound "
            "a block, which is a description and not a claim. Thompson's own block NUMBERS "
            "are carried separately, in `plat_block_number`, read block by block off the "
            "georeferenced Wright 1834 scan — see `block_numbering` below and "
            "data/traces/thompson_block_numbering.json. A block left unnumbered here is one "
            "the sheet was not read on, and the authored file says which and why."),
        "tool": "tools/generate_plat_lots.py",
        "generated_from": [
            "data/traces/street_control.json",
            "data/streets/1835.json",
            "data/sources/thompson_plat_1830.json",
        ],
        "sources": SOURCE_IDS,
        "module": {
            "street_width_m": module["width_m"],
            "street_width_ft": module["width_ft"],
            "street_confidence": module["confidence"],
            "alley_width_m": alley_m,
            "alley_width_ft": ALLEY_FT,
            "alley_confidence": "reconstructed",
            "alley_note": (
                "18 ft is the module the Thompson plat source record carries and the figure "
                "the 1834 traverses read (17.1-18.7 ft), so the WIDTH is as well attested as "
                "the street. Everything else about it is not: nothing in data/sources/ says "
                "which blocks were alleyed, or whether the alley ran with the long axis of a "
                "block or across it. The mid-block east-west alley generated here is the "
                "arrangement the lot rows on Wright's block 18 imply, and it is a conjecture "
                "in exactly the way its confidence says. The 16 ft dissent recorded in "
                "data/traces/street_control.json is not settled by the traverses: two feet is "
                "inside that method's error."),
            "lot_frontage_m": frontage_m,
            "lot_frontage_ft": LOT_FRONTAGE_FT,
            "lot_confidence": "reconstructed",
            "lot_note": (
                "Four lots to a block face, 80 ft each, is a reading of ONE block: the owner's "
                "crop of Wright's sheet at the Clark reach carries block 18's north row "
                "numbered 4 3 2 and its south row 5 6 7 "
                "(docs/RESEARCH/clark_reach_bulge_1834.md § 8), which is four lots across a "
                "block of about 320 ft. Applying it to the other blocks is inference from a "
                "single instance and it is graded as the conjecture it is. Lots carry a "
                "`plat_lot_number` ONLY inside a numbered block, under the scheme the same "
                "crop shows on block 18 — 1-4 east to west along the north row, 5-8 west to "
                "east along the south row — and that number is `conjectural` wherever it "
                "appears, because it is put on a line no sheet drew. Nothing else in this "
                "file is numbered: a numbering invented to look complete is exactly what "
                "this project does not do."),
        },
        "survey_tract_layer": {
            "why_this_section_exists": (
                "T-1105. Until T-1101 built the survey-tract layer this generator chose ONE "
                "street width and ONE block module for the whole town because there was no "
                "layer to ask, and the choice was invisible: nothing on a block said which "
                "survey it stood in or which module it had been given. Both are now stamped "
                "on every block, so a block that takes the Original Town's module takes it "
                "on the record."),
            "read": "data/reconstruction/1835_survey_tracts.json",
            "rings_read": [t["id"] for t in tracts],
            "rule": (
                "a block takes the tract that covers the most of it, by clipped area, using "
                "the clipper in tools/sort_land_sales_onto_tracts.py"),
            "the_precedence_clause": (
                "EXCEPT that a residual tract — one whose ring is defined as what another "
                "tract leaves over — yields any block a non-residual tract covers at least "
                "50% of. canal_section_9_remainder is the layer's only residual. T-1104 "
                "states this clause for parcels; a second statement of it would be a second "
                "answer, so it is the same clause and the same clipper."),
            "what_the_layer_answers_here": {
                "blocks_sorted": len(blocks),
                "by_tract": _count_tracts(blocks),
                "finding": (
                    "THE LAYER DOES NOT DISCRIMINATE THIS GRID. All nineteen generated "
                    "blocks fall in canal_commissioners_1830 and no other placed ring "
                    "touches one, which the tract record itself already says — its "
                    "geometry_note reports all 19 inside the rectangle. So the question "
                    "T-1105 asks the layer, the layer cannot answer: no block here stands "
                    "in Wabansia or Kinzie's Addition, and a per-tract module would change "
                    "nothing about what is built. What DOES vary inside this one tract is "
                    "the DIVISION, because the river runs through the Original Town and "
                    "the plat gives its two sides different blocks."),
                "the_grade_is_inherited": (
                    "canal_commissioners_1830 is `conjectural` — its four bounds are the "
                    "standard account of the 1830 plat and no source record here states "
                    "them. Any module chosen off that ring would be conjectural for that "
                    "reason alone. None is: the module below is chosen off the street "
                    "lines, and the tract is carried as a finding, not used as an input."),
            },
            "the_west_division_module": {
                "held": west["authored_in"],
                "confidence_of_the_figures": west["confidence"],
                "printed": (
                    f"lots {west['printed_frontage']} ft on the front and "
                    f"{west['lot_depth_ft']:.0f} ft deep, two columns backing onto an "
                    f"{west['alley_width_ft']:.0f} ft NORTH-SOUTH alley, the block square "
                    f"at {west['block_east_west_ft']:.0f} ft, the street module "
                    f"{west['street_module_ft']:.0f} ft"),
                "streets_it_governs": sorted(west["streets"]),
                "blocks_of_this_grid_inside_it": sorted(
                    b["id"] for b in blocks
                    if b["module"].get("division") == "west"),
                "refused_on_every_one_of_them": (
                    "and the refusal is arithmetic, not preference. Two lot columns alone "
                    f"need {2 * west['lot_depth_ft']:.0f} ft; the committed faces west of "
                    "the river are "
                    + ", ".join(
                        f"{b['module']['west_division_module_refused']['what_the_committed_lines_give']['east_west_face_ft']:.1f} ft"
                        for b in blocks if b["module"].get("division") == "west")
                    + ". The arrangement does not fit before the alley is cut."),
                "what_is_short_is_the_spacing_not_the_module": (
                    f"Clinton to Canal is committed at {spacing_ft:.1f} ft against the "
                    f"plat's {west['street_module_ft']:.0f} ft — "
                    f"{west['street_module_ft'] - spacing_ft:.1f} ft short, the same "
                    "finding tools/measure_west_division_module.py reports and the owner "
                    "reported on 2026-08-31. Seating the printed module means moving those "
                    "centrelines, which is T-0445 and is deliberately not done here: this "
                    "generator writes what the committed lines give and records what the "
                    "sheet asks for beside it."),
                "what_would_change_if_the_lines_moved": (
                    "the two West Division blocks would be subdivided the other way about "
                    "— columns and a north-south alley instead of faces and an east-west "
                    "one — so this is a refusal that will be worth revisiting the day "
                    "T-0445 settles the spacing, and not before."),
            },
            "omitted_blocks_carry_no_tract": (
                "an omitted block has no ring to clip, by definition — it is omitted "
                "because the grid could not draw one — so it is sorted onto no tract "
                "rather than onto one guessed from its bounding streets"),
        },
        "method": {
            "block_edge": ("a street centreline offset by half the platted corridor "
                           f"({module['half_width_m']} m), the four offsets intersected"),
            "reach_m": reach_m,
            "reach_note": (
                "A block is emitted only where the committed centrelines of all four of its "
                "bounding streets reach it, allowing at most half a corridor of extension for "
                "a line drawn to a junction rather than through it. Everything refused is in "
                "`omitted` with the street that falls short, which is the same list of street "
                "control ROADMAP § S9 still records as owed."),
            "max_pitch_m": MAX_PITCH_M,
            "water_rule": ("a block with a corner on water or beyond the modelled ground is "
                           "omitted rather than drawn over the river"),
            "lot_subdivision": ("the block's north and south faces divided in the same "
                                "proportion, joined station to station, with a centred "
                                "alley taken out of the middle"),
        },
        "block_numbering": {
            "authored_in": "data/traces/thompson_block_numbering.json",
            "read": numbering_doc["reading"]["what_it_carries"],
            "source": numbering_doc["reading"]["source"],
            "step": numbering_doc["reading"]["step"],
            "direction": numbering_doc["reading"]["direction"],
            "lot_scheme": numbering_doc["lot_numbering"]["scheme"],
            "lot_confidence": numbering_doc["lot_numbering"]["confidence"],
            "refused": [r["scope"] for r in numbering_doc["refused"]],
            "note": ("Each numeral is read on a crop cut to that block's own committed "
                     "ground, so the reading is identified by the georeference rather than "
                     "counted from a neighbour. `numeral_on_sheet` on each block says which "
                     "numbers are read and which are not, and the authored file carries the "
                     "reading, the crop regions and the refusals in full."),
        },
        "confidence": "inferred",
        "confidence_note": (
            "The blocks are arithmetic on inferred inputs — street lines whose own geometry "
            "confidence is `inferred`, offset by a module width the street control also grades "
            "`inferred` — so `inferred` is the most this grid can carry. The lots and the "
            "alleys inside those blocks are `conjectural` and are recorded separately for that "
            "reason: a visitor is entitled to know that the block face is a defensible "
            "position and the line dividing it is not."),
        "summary": {
            "blocks": len(blocks),
            "omitted": len(omitted),
            "reserved": sum(1 for b in blocks if b.get("reserved")),
            "numbered": sum(1 for b in blocks if b.get("plat_block_number")),
            "numbered_omitted": sum(1 for o in omitted if o.get("plat_block_number")),
            "lots": sum(len(b["lots"]) for b in blocks),
            "numbered_lots": sum(1 for b in blocks for l in b["lots"]
                                 if l.get("plat_lot_number")),
            "block_frontage_ft": {
                "min": round(min((b["frontage_ft"] for b in blocks), default=0.0), 1),
                "median": round(sorted(b["frontage_ft"] for b in blocks)[len(blocks) // 2], 1)
                if blocks else 0.0,
                "max": round(max((b["frontage_ft"] for b in blocks), default=0.0), 1),
            },
            "lot_frontage_ft": {
                "min": round(min(faces, default=0.0) / FT_M, 1),
                "max": round(max(faces, default=0.0) / FT_M, 1),
            },
        },
        "blocks": blocks,
        "omitted": omitted,
    }


# ---------------------------------------------------------------- the cross-check

def corridor_rings(lines: dict, half_width: float) -> dict:
    """The platted corridor of every grid street, as a closed ring.

    A corridor is only as long as the centreline this project has committed, so a
    building beyond a street's drawn end is not reported as standing in it.
    """
    rings = {}
    for street_id, street in lines.items():
        if street_id in EW_STREETS:
            left, right = (0.0, 1.0), (0.0, -1.0)
        elif street_id in NS_STREETS:
            left, right = (-1.0, 0.0), (1.0, 0.0)
        else:
            continue
        a = offset_polyline(street["points"], half_width, left)
        b = offset_polyline(street["points"], half_width, right)
        rings[street_id] = a + list(reversed(b))
    return rings


def point_to_ring_m(point, ring) -> float:
    """Shortest distance from a point to a ring's edges."""
    best = float("inf")
    px, py = point
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        dx, dy = bx - ax, by - ay
        span = dx * dx + dy * dy
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
        best = min(best, math.dist(point, (ax + dx * t, ay + dy * t)))
    return best


def world_footprint(record: dict) -> list:
    """A sidecar's footprint polygon in local ENU, oriented and placed."""
    placement = record["placement"]
    theta = math.radians(float(placement.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0, n0 = float(placement["local_e"]), float(placement["local_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos)
            for u, v in record["footprint"]["polygon"]]


def report(grid: dict) -> int:
    """Where the dataset's own buildings fall on this grid."""
    from plat_corridors import intrusion  # noqa: PLC0415 - avoids an import cycle

    control = load(DATA / "traces" / "street_control.json")
    half_width = float(control["platted_street"]["half_width_m"])
    lines = street_lines(load(DATA / "streets" / "1835.json"))
    corridors = corridor_rings(lines, half_width)
    lanes = {sid: {"name": lines[sid]["name"], "ring": ring, "points": lines[sid]["points"]}
             for sid, ring in corridors.items()}
    rings = {b["id"]: [tuple(p) for p in b["boundary_local_enu_m"]] for b in grid["blocks"]}
    footprint_hits = []

    placed = 0
    in_block, in_street, off_grid = [], [], []
    for path in sorted(SIDECARS.glob("*.json")):
        record = load(path)
        placement = record.get("placement") or {}
        if placement.get("local_e") is None:
            continue
        point = (float(placement["local_e"]), float(placement["local_n"]))
        if point == (0.0, 0.0):
            continue
        placed += 1
        confidence = placement.get("position_confidence")
        home = next((bid for bid, ring in rings.items() if point_in_polygon(point, ring)), None)
        street = next((sid for sid, ring in corridors.items()
                       if point_in_polygon(point, ring)), None)
        if home:
            in_block.append((record["id"], point, confidence, home, 0.0))
        elif street:
            in_street.append((record["id"], point, confidence, street,
                              point_to_ring_m(point, corridors[street])))
        else:
            off_grid.append((record["id"], point, confidence, None, 0.0))
        lane, depth = intrusion(world_footprint(record), lanes)
        if lane:
            footprint_hits.append((record["id"], confidence, lane, depth))

    print(f"{placed} placed structures against {len(rings)} generated blocks:")
    print(f"  {len(in_block):4d} stand inside a block")
    print(f"  {len(in_street):4d} stand INSIDE A PLATTED STREET CORRIDOR")
    print(f"  {len(off_grid):4d} stand outside this grid altogether (the North Division, the "
          "fort, the West Division beyond Clinton, and the blocks in `omitted`)")
    by_confidence = {}
    for _, _, confidence, _, _ in in_street:
        by_confidence[confidence] = by_confidence.get(confidence, 0) + 1
    if in_street:
        print("\nin a street corridor, by position confidence: "
              + ", ".join(f"{k}: {v}" for k, v in sorted(by_confidence.items(), key=str)))
        print("`depth` is how far the record's centre lies inside the corridor. Anything "
              "under a few metres is inside the georeference's own ±20 m and says little; a "
              "centre 8-12 m in is a building standing in the middle of the street.")
        for sid, point, confidence, street, depth in sorted(in_street, key=lambda r: -r[4]):
            print(f"  - {sid:44s} ({point[0]:8.1f}, {point[1]:8.1f})  "
                  f"{str(confidence):12s} {lines[street]['name']:20s} depth {depth:5.1f} m")

    # A centre in the road is the loud case; a FOOTPRINT in the road is the common one,
    # and it is the question the placement gate in tools/generate_inferred_households.py
    # actually asks. The two lists differ because a building can front a street with its
    # centre well clear of the corridor and half its depth inside it.
    if footprint_hits:
        print(f"\n{len(footprint_hits)} structure(s) put some part of a footprint inside a "
              "platted corridor. The plat is the LEGAL corridor, not the travelled way "
              "(L79: 5.8-10.5 m of visible track inside 80 ft), so this is a measurement "
              "against the plat rather than a list of defects — but no generated placement "
              "is allowed to be here.")
        for sid, confidence, lane, depth in sorted(footprint_hits, key=lambda r: -r[3]):
            print(f"  - {sid:44s} {str(confidence):12s} {lanes[lane]['name']:20s} "
                  f"reaches {depth:5.1f} m in")
    return 0


def self_test() -> int:
    """The crossed-corner refusal fires, and it fires on the case that produced it.

    T-0183. The owner ruled on 2026-08-29 that South Water Street's committed west end
    should be CLOSED onto Market's corridor. Executed on the line as committed, that
    closure does not open `blk_south_water_market`: South Water's west approach has already
    converged onto Lake Street by the time it reaches Market, so the block's north-west
    corner falls south of its south-west one and the ring is a bowtie. This rebuilds that
    exact case from the committed inputs and asserts the refusal, so nobody has to take the
    measurement on trust — and asserts a real block still builds, so the guard cannot pass
    by refusing everything.
    """
    import copy  # noqa: PLC0415

    streets = load(DATA / "streets" / "1835.json")
    control = load(DATA / "traces" / "street_control.json")
    half_width = float(control["platted_street"]["half_width_m"])
    cases, failed = 0, 0

    def build(doc):
        lines = street_lines(doc)
        return lines, build_block("south_water", "lake", "market", "franklin",
                                  lines, block_edges(lines, half_width), half_width)

    # 1. As committed: the north row simply does not reach the block.
    cases += 1
    _, (built, why) = build(streets)
    if built is not None or "stops" not in (why or ""):
        print(f"  NOT REFUSED as committed: {why}")
        failed += 1
    else:
        print(f"  ok:    as committed \u2014 {why}")

    # 2. Closed onto Market's corridor: the crossing is found, and the corners are inverted.
    closed = copy.deepcopy(streets)
    for street in closed["streets"]:
        if street["id"] == "south_water":
            street["path_local_enu_m"] = [[89.27, -101]] + street["path_local_enu_m"]
    cases += 1
    lines, (built, why) = build(closed)
    if built is not None or "have crossed" not in (why or ""):
        print(f"  GUARD DID NOT FIRE on the closed west end: {why}")
        failed += 1
    else:
        print(f"  fires: the closure the ruling asks for \u2014 {why}")

    # 3. And the guard is not refusing everything: the block east of it still builds.
    cases += 1
    lines = street_lines(streets)
    built, why = build_block("south_water", "lake", "franklin", "wells",
                             lines, block_edges(lines, half_width), half_width)
    if built is None:
        print(f"  A REAL BLOCK WAS REFUSED: {why}")
        failed += 1
    else:
        print("  ok:    blk_south_water_franklin still builds "
              f"({polygon_area(built['ring']):.0f} m2)")

    # 4. AND THE GROUND IS THE REASON, not the drawn line. Push South Water as far north
    #    at Market's easting as the committed heightfield allows — its north corridor edge
    #    exactly on the waterline — and measure what is left between it and Lake Street.
    #    If that ever exceeds a lot's own depth the finding recorded on
    #    `refused_control.market_south_water` is stale and wants re-reading.
    cases += 1
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from heightfield import Heightfield  # noqa: PLC0415
        field = Heightfield.load(DATA / "terrain" / "epochs" / "e1834_harbor_cut")
    except Exception as exc:  # pragma: no cover - the field is committed
        print(f"  the committed heightfield did not load: {exc}")
        return 1
    market = next(s for s in streets["streets"] if s["id"] == "market")
    lake = next(s for s in streets["streets"] if s["id"] == "lake")
    corner_e = market["path_local_enu_m"][-1][0]
    waterline = -140.0
    while waterline < 60.0:
        if not (field.covers(corner_e, waterline) and field.height(corner_e, waterline) >= 0.0):
            break
        waterline += 0.1
    lake_line = [(float(e), float(n)) for e, n in lake["path_local_enu_m"]]
    lake_n = next(a[1] + (corner_e - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
                  for a, b in zip(lake_line, lake_line[1:]) if a[0] <= corner_e <= b[0])
    headroom = (waterline - 2 * half_width) - (lake_n + half_width)
    if headroom > LOT_FRONTAGE_FT * FT_M:
        print(f"  THE GROUND HAS CHANGED: {headroom:.1f} m of block depth at Market now")
        failed += 1
    else:
        print(f"  ok:    the ground, not the line \u2014 South Water carried as far north at "
              f"Market as the committed waterline (local N {waterline:.1f}) allows leaves "
              f"{headroom:.1f} m between it and Lake Street")

    # 5. T-1105. The survey-tract layer is asked, and the West Division refusal is
    #    re-derived rather than trusted. Both halves matter: that the layer answers the
    #    same tract for every block is the finding, and that the printed West Division
    #    arrangement will not seat on the committed faces is the reason the refusal
    #    stands. If either stops being true this gate should be the thing that says so.
    cases += 1
    tracts = survey_tracts()
    west = west_division()
    lines = street_lines(streets)
    spacing_ft = abs(lines["clinton"]["mean_e"] - lines["canal"]["mean_e"]) / FT_M
    grid = load(OUT_PATH) if OUT_PATH.exists() else None
    if grid is None:
        print("  the committed grid is missing; nothing to check the layer against")
        failed += 1
    else:
        sorted_to = {t["id"] for t in tracts if any(
            b["survey_tract"]["tract"] == t["id"] for b in grid["blocks"])}
        stated = set(grid["survey_tract_layer"]["what_the_layer_answers_here"]["by_tract"])
        if sorted_to != stated:
            print(f"  THE LAYER'S ANSWER MOVED: blocks now sort onto {sorted(sorted_to)}, "
                  f"the record says {sorted(stated)}")
            failed += 1
        else:
            print(f"  ok:    {len(grid['blocks'])} blocks sort onto {sorted(stated)}, "
                  "which is what the record says")

    cases += 1
    columns_ft = 2 * west["lot_depth_ft"] + west["alley_width_ft"]
    west_blocks = [b for b in (grid["blocks"] if grid else [])
                   if b["module"].get("division") == "west"]
    if not west_blocks:
        print("  NO WEST DIVISION BLOCK on this grid — the refusal has nothing to refuse")
        failed += 1
    else:
        seatable = [b for b in west_blocks
                    if b["frontage_m"] / FT_M >= columns_ft]
        if seatable:
            print("  THE REFUSAL IS STALE: the printed West Division arrangement now "
                  f"seats on {', '.join(b['id'] for b in seatable)} — re-read it")
            failed += 1
        else:
            faces = ", ".join(f"{b['frontage_m'] / FT_M:.1f}" for b in west_blocks)
            print(f"  ok:    the West Division arrangement needs {columns_ft:.0f} ft of "
                  f"face and the committed blocks give {faces} ft; Clinton to Canal is "
                  f"{spacing_ft:.1f} ft against the plat's "
                  f"{west['street_module_ft']:.0f} ft")

    if failed:
        print(f"SELF-TEST FAIL — {failed} of {cases}")
        return 1
    print(f"SELF-TEST PASS — the crossed-corner refusal fires on the case that "
          f"produced it, the ground says why, and the survey-tract layer's answer and the "
          f"West Division refusal are both re-derived ({cases} cases)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed grid is not what the inputs re-derive")
    parser.add_argument("--report", action="store_true",
                        help="report where the dataset's structures fall on the grid")
    parser.add_argument("--self-test", action="store_true",
                        help="the crossed-corner refusal fires on the case that produced it")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    grid = grid_from_inputs()
    if args.report:
        return report(grid)

    text = json.dumps(grid, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT_PATH.exists():
            print(f"PLAT GRID DRIFT\n  - {OUT_PATH.relative_to(ROOT)} is missing")
            return 1
        if OUT_PATH.read_text(encoding="utf-8") != text:
            print("PLAT GRID DRIFT\n  - data/traces/vectors/thompson_lots.json is not what "
                  "the module and the committed street lines re-derive")
            return 1
    else:
        OUT_PATH.write_text(text, encoding="utf-8")
    mode = "verified" if args.check else "generated"
    print(f"{mode} {grid['summary']['blocks']} platted blocks "
          f"({grid['summary']['lots']} lots, {grid['summary']['omitted']} omitted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
