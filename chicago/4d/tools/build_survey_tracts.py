#!/usr/bin/env python3
"""The nine survey tracts of Wright's 1834 legend, as polygons (T-1101).

    tools/build_survey_tracts.py --build             re-read the raster's bands, rewrite the record
    tools/build_survey_tracts.py --check-properties  the gate: offline, re-derives every polygon and every count
    tools/build_survey_tracts.py --report            print what was placed and what was refused
    tools/build_survey_tracts.py --self-test         the gate's assertions still fire when broken

THE HOLE THIS CLOSES. Wright's legend names nine surveys and dates most of them, and
T-1096 measured the nine chips: nine names, six separable colours, and a per-pixel
spread inside one chip wider than the distance between some pairs of them. So a wash on
the sheet can be assigned to a CLASS of chips and not to a chip, and the two swatches
that name no tract at all — chip 6 `Surveyed. ——— 1833` and chip 8 `Surveyed in 1833` —
cannot be read off colour. Nothing had ever put any of the nine on the ground.

WHAT THIS FILE CLAIMS, AND IN WHAT ORDER OF CONFIDENCE.

  the polygons     Seven of the nine tracts are placed from ground this project ALREADY
                   holds — the committed reservation ring, the committed PLSS section
                   grid, Wabansia's committed seating, the committed street lines of
                   Kinzie's Addition and of the Original Town's four named bounds. Not
                   one boundary here is traced off the colour. The colour is the CHECK,
                   never the source, because a wash 17 px wide cannot carry a boundary
                   this project already knows to the metre.
  the adjudication Every band of every class is put through the polygons and lands on a
                   named tract, on unnamed ground, or in an exclusion. That is what
                   decides chips 6 and 8, and it is what the parent ticket asked for:
                   inside a class whose other members are named ground, the band that is
                   NOT on named ground belongs to the unnamed chip.
  the owners       Taken from the public-domain tract sales this project already holds
                   (`data/research/land_sales/entries.json`), which name the entryman,
                   the aliquot and the date. Where the register does not reach a tract,
                   the owner is REFUSED rather than supplied from narrative.

THE EXCLUSIONS, AND WHY THEY ARE MEASURED RATHER THAN DRAWN. Chip 8's largest region on
the whole sheet is 8,184 cells over the lake quadrant, and it is not a survey: it is the
foxing and the mounted repair the sheet's own caption describes. A hand-drawn damage box
would be an invention. The rule used instead is a property of what a survey tract IS —
Wright washed LAND — so a band whose centroid stands east of the committed lake shore, or
inside a committed lacuna box, or inside the legend column itself, or outside the neat
line, cannot be a tract wash whatever its colour. The lake quadrant region falls to the
first of those, measured, and its box is recorded so the next reader can disagree.

WHAT IS REFUSED HERE, and the refusals are the point.

  chip 3 Wabansia   carries NO band of its own class. T-1096 measured why: its boundary
                    stroke in the north-west has faded far enough to classify with chip
                    8's duller orange. The polygon stands on the committed seating; the
                    COLOUR evidence for it is absent and is recorded as absent.
  chip 2 Canal Com. its class has two bands, the fewest on the sheet, and NEITHER stands
                    on the Original Town: both sit at the Madison/State corner, 48 m and
                    146 m from it, where four tracts meet and the colours crowd. They cannot place a tract; the Original Town is
                    placed from its four named bounds instead and the colour is
                    recorded as insufficient rather than as agreement.
  chips 6 and 8     are not resolved, and the reason is measured rather than asserted.
                    EVERY ONE of their unnamed-ground bands — seven for chip 6, three for
                    chip 8, after the exclusions — falls in one of two places this
                    project's own geometry does not reach: beyond the four sections the
                    PLSS grid is carried across (L219), or north of where the committed
                    lake-shore trace ends. So the positional method does not fail here
                    for want of evidence; it runs out of GROUND. Carrying the grid
                    further, or committing the shore north of its present end, is what
                    would let these two chips be adjudicated at all, and that is a
                    better thing to leave behind than a polygon nobody could defend.

WHAT THIS COSTS THE PARENT TICKET, said plainly: T-0792 asked for nine tract polygons and
this file places seven. The two it refuses are the two the parent already knew were hard,
and the refusal now carries the number that would change it.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

RECORD = ROOT / "data" / "reconstruction" / "1835_survey_tracts.json"
SWATCHES = ROOT / "data" / "traces" / "wright_1834_legend_swatches.json"
NA_GCPS = ROOT / "data" / "traces" / "gcp" / "wright_1834_nara_hup_gcps.json"
STREETS = ROOT / "data" / "streets" / "1835.json"
WABANSIA = ROOT / "data" / "traces" / "wabansia_seating.json"
MICHIGAN_ST = ROOT / "data" / "traces" / "michigan_st_tract_seated.json"
LIGHTHOUSE = ROOT / "data" / "traces" / "wright_1834_lighthouse_glyph.json"
ENTRIES = ROOT / "data" / "research" / "land_sales" / "entries.json"

TARGET_DATE = "1835-07-01"
ACRE_M2 = 4046.8564

# The Addition's own streets, as `tools/read_kinzie_addition_streets.py` names them, plus
# the two the Addition shares with the town below it. The envelope of these lines is the
# only extent this project holds for chip 4; its shortfall against the patent acreage is
# measured below rather than hidden.
KINZIE_STREETS = ("superior_north", "huron_north", "erie_north", "ontario_north",
                  "ohio_north", "indiana_north", "illinois_north", "michigan_north",
                  "wolcott", "cass", "rush", "pine", "sand", "kinzie", "north_water")

# The Original Town's four bounds, as every account of the 1830 plat gives them, each one
# a street this project has already committed. `des_plaines_school_section` and
# `state` carry the two north-south lines; the plat's own reach north of Madison is not
# separately committed, and that is stated on the record rather than papered over.
ORIGINAL_TOWN_BOUNDS = {"west": "des_plaines_school_section", "east": "state",
                        "south": "madison", "north": "kinzie"}

CORNER_TOLERANCE_M = 25.0    # how far a committed street may stand from the section line
                             # it is being used as, before the cut is refused


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- geometry helpers

def ring_area(ring) -> float:
    a = 0.0
    for i in range(len(ring)):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % len(ring)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def inside(point, ring) -> bool:
    x, y = point
    hit = False
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            hit = not hit
    return hit


def ring_distance(point, ring) -> float:
    """Shortest distance from a point to a ring's edge, unsigned."""
    x, y = point
    best = float("inf")
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L))
        best = min(best, math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)))
    return best


def street(streets, sid):
    for s in streets:
        if s["id"] == sid:
            return s
    raise SystemExit(f"1835.json has no street {sid!r}")


def street_axis(streets, sid, axis: str) -> float:
    """The committed line's mean easting (axis 'e') or northing (axis 'n')."""
    path = street(streets, sid)["path_local_enu_m"]
    k = 0 if axis == "e" else 1
    return sum(p[k] for p in path) / len(path)


# ---------------------------------------------------------------- the nine polygons

def sections():
    """(to_grid, from_grid, box(section)) for T39N R14E, carried from G1 (L219)."""
    from resolve_land_tracts import section_grid, section_box   # noqa: PLC0415
    to_grid, from_grid, bearing, corner = section_grid()

    def ring(section):
        e0, e1, n0, n1 = section_box(section)
        return [list(from_grid(e0, n0)), list(from_grid(e1, n0)),
                list(from_grid(e1, n1)), list(from_grid(e0, n1))]

    return to_grid, from_grid, ring, bearing, corner


def shore_in_grid(to_grid):
    """The committed shore, in section-grid metres, ordered south to north."""
    from measure_no_build_ground import shore_line                # noqa: PLC0415
    pts = [tuple(to_grid(e, n)) for e, n in shore_line()]
    pts.sort(key=lambda p: p[1])
    for a, b in zip(pts, pts[1:]):
        if b[1] <= a[1]:
            raise SystemExit("the shore is not monotonic north in the section grid; "
                             "the fractional-section clip cannot be taken")
    return pts


def clip_east_at_shore(e0, e1, n0, n1, shore, from_grid):
    """A section rectangle cut on its east side by the shore polyline (grid metres)."""
    def shore_e(n):
        for a, b in zip(shore, shore[1:]):
            if a[1] <= n <= b[1]:
                t = (n - a[1]) / (b[1] - a[1])
                return a[0] + t * (b[0] - a[0])
        return None

    lo, hi = shore_e(n0), shore_e(n1)
    if lo is None or hi is None:
        raise SystemExit("the shore does not span this section's northings")
    ring = [(e0, n0), (min(max(lo, e0), e1), n0)]
    for x, y in shore:
        if n0 < y < n1:
            ring.append((min(max(x, e0), e1), y))
    ring += [(min(max(hi, e0), e1), n1), (e0, n1)]
    return [list(from_grid(x, y)) for x, y in ring]


def original_town_ring(streets, from_grid, to_grid):
    """The 1830 plat's four named bounds, each a committed street line."""
    w = street_axis(streets, ORIGINAL_TOWN_BOUNDS["west"], "e")
    e = street_axis(streets, ORIGINAL_TOWN_BOUNDS["east"], "e")
    s = street_axis(streets, ORIGINAL_TOWN_BOUNDS["south"], "n")
    n = street_axis(streets, ORIGINAL_TOWN_BOUNDS["north"], "n")
    return [[w, s], [e, s], [e, n], [w, n]], (w, e, s, n)


def section_9_remainder(ring9, ot_bounds, to_grid, from_grid):
    """Section 9 with the Original Town cut out of its south-east corner — the L that
    `Part of Canal Sec. No 9` must be if the two chips partition the section."""
    from resolve_land_tracts import section_box                   # noqa: PLC0415
    e0, e1, n0, n1 = section_box("09")
    w, e, s, n = ot_bounds
    ox0, _ = to_grid(w, s)
    ox1, oy0 = to_grid(e, s)
    _, oy1 = to_grid(w, n)
    gap_e, gap_n = abs(ox1 - e1), abs(oy0 - n0)
    if gap_e > CORNER_TOLERANCE_M or gap_n > CORNER_TOLERANCE_M:
        raise SystemExit(f"the Original Town's east/south bounds stand {gap_e:.1f} m / "
                         f"{gap_n:.1f} m off section 9's, past the {CORNER_TOLERANCE_M} m "
                         f"tolerance: the cut is refused")
    ring = [(e0, n0), (ox0, n0), (ox0, oy1), (e1, oy1), (e1, n1), (e0, n1)]
    return [list(from_grid(x, y)) for x, y in ring], {"east_gap_m": round(gap_e, 2),
                                                      "south_gap_m": round(gap_n, 2)}


def kinzie_envelope(streets):
    xs, ys = [], []
    for sid in KINZIE_STREETS:
        for x, y in street(streets, sid)["path_local_enu_m"]:
            xs.append(x)
            ys.append(y)
    # Kinzie Street and North Water Street run far west of the Addition; the Addition's
    # own north-south lines bound it, so the envelope is taken on those.
    own = [street_axis(streets, sid, "e") for sid in ("wolcott", "cass", "rush", "pine", "sand")]
    w, e = min(own), max(own)
    s = street_axis(streets, "kinzie", "n")
    n = max(ys)
    return [[w, s], [e, s], [e, n], [w, n]]


def build_polygons():
    """Every tract's ring, derived — never stored, never hand-authored."""
    from measure_no_build_ground import reservation_ring          # noqa: PLC0415
    from resolve_land_tracts import section_box                   # noqa: PLC0415
    to_grid, from_grid, ring_of, bearing, corner = sections()
    streets = load(STREETS)["streets"]
    shore = shore_in_grid(to_grid)

    res, _, _ = reservation_ring()
    ot, ot_bounds = original_town_ring(streets, from_grid, to_grid)
    sec9_rest, sec9_gaps = section_9_remainder(ring_of("09"), ot_bounds, to_grid, from_grid)
    e0, e1, n0, n1 = section_box("15")

    polys = {
        "us_military_reservation": [list(p) for p in res],
        "canal_commissioners_1830": ot,
        "wabansia": [list(p) for p in
                     load(WABANSIA)["tract_polygon_local_enu_m"]["polygon_local_enu_m"][:-1]],
        "kinzies_addition": kinzie_envelope(streets),
        "school_section": ring_of("16"),
        "fractional_section_15": clip_east_at_shore(e0, e1, n0, n1, shore, from_grid),
        "canal_section_9_remainder": sec9_rest,
    }
    return polys, {"section_9_cut": sec9_gaps, "original_town_bounds_local_m":
                   {"west_e": round(ot_bounds[0], 2), "east_e": round(ot_bounds[1], 2),
                    "south_n": round(ot_bounds[2], 2), "north_n": round(ot_bounds[3], 2)}}


# ---------------------------------------------------------------- the adjudication

CHIP_TRACT = {1: "us_military_reservation", 2: "canal_commissioners_1830",
              3: "wabansia", 4: "kinzies_addition", 5: "school_section",
              7: "fractional_section_15", 9: "canal_section_9_remainder"}
UNNAMED_CHIPS = (6, 8)


# THE TRACTS ARE NOT DISJOINT, because the surveys were not. Four of the nine chips are
# PLSS sections, which tile the township, and four of the others are plats that stand
# INSIDE one of those sections — Kinzie's Addition inside section 10, the Original Town
# and Wabansia inside section 9, the reservation inside section 10. So a band can be
# inside two tracts at once and the question "which tract is this wash" has a right
# answer: the most specific one. The order below is that answer, and it is the same order
# the ninth chip's own wording implies — `Part of Canal Sec. No 9` is what is LEFT of the
# section once the plats inside it are taken out.
PRECEDENCE = ("us_military_reservation", "wabansia", "kinzies_addition",
              "canal_commissioners_1830", "school_section", "fractional_section_15",
              "canal_section_9_remainder")


def exclusions(swatches):
    """What cannot be a tract wash, whatever its colour — each rule a property of what a
    survey tract IS, not a box drawn round an inconvenience."""
    na = load(NA_GCPS)
    return {
        "neat_line_px": swatches["method"]["neat_line_px"],
        "legend_box_px": swatches["method"]["legend_box_px"],
        "lacunae_px": [{"id": l["id"], "box": l["box"]} for l in na["lacunae"]["found"]],
        "water": ("east of the committed lake shore, or in the river — Wright washed "
                  "survey tracts, and a survey tract is land"),
    }


def classify(bands, polys, to_local, shore_grid, to_grid, excl, grid_rings):
    """Put every band through the polygons. One pass, one verdict each."""
    nl, lb = excl["neat_line_px"], excl["legend_box_px"]
    lac = [l["box"] for l in excl["lacunae_px"]]

    def shore_e(n):
        for a, b in zip(shore_grid, shore_grid[1:]):
            if a[1] <= n <= b[1]:
                t = (n - a[1]) / (b[1] - a[1])
                return a[0] + t * (b[0] - a[0])
        return None

    out = []
    for b in bands:
        cx, cy = b["centroid_px"]
        e, n = to_local(cx, cy)
        row = {"cells": b["cells"], "centroid_px": [round(cx, 1), round(cy, 1)],
               "local_m": [round(e, 1), round(n, 1)], "excluded": None, "on": None}
        gx, gy = to_grid(e, n)
        se = shore_e(gy)
        if not (nl["x0"] <= cx <= nl["x1"] and nl["y0"] <= cy <= nl["y1"]):
            row["excluded"] = "off_map"
        elif lb["x0"] <= cx <= lb["x1"] and lb["y0"] <= cy <= lb["y1"]:
            row["excluded"] = "in_legend"
        elif any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in lac):
            row["excluded"] = "lacuna"
        elif se is not None and gx > se:
            row["excluded"] = "water"
        else:
            hits = [t for t in PRECEDENCE if inside((e, n), polys[t])]
            row["on"] = hits[0] if hits else None
            if len(hits) > 1:
                row["also_inside"] = hits[1:]
            if row["on"] is None:
                # WHY THE GROUND IS UNNAMED matters more than the count. Two of this
                # project's own limits reach into this sheet, and a band that falls in
                # one of them is not evidence of an unrecorded survey — it is evidence
                # that the method has run out of ground.
                row["unnamed_because"] = (
                    "beyond_the_carried_section_grid"
                    if not any(inside((e, n), r) for r in grid_rings) else
                    "north_of_the_committed_shore"
                    if gy > shore_grid[-1][1] else
                    "inside_the_grid_and_on_no_tract")
        out.append(row)
    return out


def adjudicate(classes, rows_by_class, polys):
    """The parent ticket's method, applied and then judged: inside a class whose other
    members are named ground, the band that is NOT on named ground belongs to the
    unnamed chip — IF what is left is a tract-shaped thing rather than a scatter."""
    verdicts = {}
    for chip in UNNAMED_CHIPS:
        group = next(g for g in classes if chip in g)
        rows = rows_by_class[str(group)]
        mates = [CHIP_TRACT[c] for c in group if c != chip]
        live = [r for r in rows if not r["excluded"]]
        on_mate = [r for r in live if r["on"] in mates]
        spare = [r for r in live if r["on"] not in mates]
        named_elsewhere = [r for r in spare if r["on"]]
        unnamed = [r for r in spare if not r["on"]]
        pts = [r["local_m"] for r in unnamed]
        if pts:
            spread_e = max(p[0] for p in pts) - min(p[0] for p in pts)
            spread_n = max(p[1] for p in pts) - min(p[1] for p in pts)
        else:
            spread_e = spread_n = 0.0
        why = {}
        for r in unnamed:
            why[r.get("unnamed_because", "unstated")] = why.get(r.get("unnamed_because", "unstated"), 0) + 1
        clusters = single_linkage(unnamed, LINK_M)
        cells = sum(r["cells"] for r in unnamed) or 1
        biggest = max(clusters, key=lambda c: sum(r["cells"] for r in c), default=[])
        share = sum(r["cells"] for r in biggest) / cells
        coherent = len(biggest) >= MIN_CLUSTER_BANDS and share >= MIN_CLUSTER_SHARE
        verdicts[str(chip)] = {
            "class": group,
            "class_mates_named": mates,
            "bands_total": len(rows),
            "bands_excluded": len(rows) - len(live),
            "bands_on_a_class_mate": len(on_mate),
            "bands_on_other_named_ground": len(named_elsewhere),
            "bands_on_unnamed_ground": len(unnamed),
            "unnamed_spread_m": [round(spread_e, 1), round(spread_n, 1)],
            "clusters_at_link_m": {"link_m": LINK_M, "count": len(clusters),
                                   "largest_bands": len(biggest),
                                   "largest_cell_share": round(share, 3)},
            "unnamed_ground_is": why,
            "coherent": coherent,
            "wash_extent_local_m": bbox(biggest) if coherent else None,
            "why_not_placed": (
                "A boundary is never traced off a wash in this file, so no chip gets a "
                "polygon from colour — not even a coherent one. What a coherent cluster "
                "earns is a statement of WHERE the wash stands, graded conjectural."
                if coherent else
                "The unnamed-ground bands of this class do not cluster: "
                f"{len(clusters)} groups at {LINK_M} m linkage, the largest holding "
                f"{share:.0%} of the cells against the {MIN_CLUSTER_SHARE:.0%} this "
                "file requires. A survey tract is one connected piece of ground and a "
                "scatter is not one. AND THE SCATTER IS NOT RANDOM: "
                + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(why.items()))
                + " — so what is missing here is ground, not evidence. Carrying the "
                "PLSS grid past the four sections it is held to (L219), or committing "
                "the lake shore north of where its trace ends, is what would let this "
                "chip be adjudicated at all."),
            "unnamed_bands": sorted(unnamed, key=lambda r: -r["cells"])[:12],
        }
    return verdicts


# The wash-cluster rule, stated before it is applied. A survey tract is ONE connected
# piece of ground, so the bands of an unnamed chip that stand on unnamed ground must
# gather rather than scatter before they are allowed to say anything at all. 250 m is
# about two of the Original Town's blocks — the width of margin a boundary wash and its
# breaks occupy on this sheet — and the share is taken on CELLS, not on band count, so a
# cloud of forty-cell specks cannot outvote a real margin.
LINK_M = 250.0
MIN_CLUSTER_BANDS = 3
MIN_CLUSTER_SHARE = 0.60


def single_linkage(rows, link_m):
    groups = [[r] for r in rows]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if any(math.dist(a["local_m"], b["local_m"]) <= link_m
                       for a in groups[i] for b in groups[j]):
                    groups[i] += groups.pop(j)
                    merged = True
                    break
            if merged:
                break
    return sorted(groups, key=lambda g: -sum(r["cells"] for r in g))


def bbox(rows):
    if not rows:
        return None
    es = [r["local_m"][0] for r in rows]
    ns = [r["local_m"][1] for r in rows]
    return {"e0": round(min(es), 1), "n0": round(min(ns), 1),
            "e1": round(max(es), 1), "n1": round(max(ns), 1)}


# ---------------------------------------------------------------- the owners

def owners():
    """Who the public-domain tract register puts on each tract, and where it is silent.

    The register is an entry, not a chain of title: it says the patent for this ground was
    entered by this man on this date, and nothing about who held it on the scene date.
    That distinction is `resolve_land_tracts.py`'s and it is kept here."""
    rows = [r for r in load(ENTRIES)["entries"]
            if r["township"] == "39N" and r["range"] == "14E"]
    by_section = {}
    for r in rows:
        by_section.setdefault(r["section"], []).append(r)

    def entered(section, predicate, note):
        hits = [r for r in by_section.get(section, []) if predicate(r)]
        hits.sort(key=lambda r: r["date_purchased"])
        return {
            "entries": [{"purchaser": h["purchaser_normalized"],
                         "aliquot_as_read": h["aliquot_or_lot_as_read"],
                         "acres": h["acres"], "date": h["date_purchased"],
                         "type_of_sale": h["type_of_sale"]} for h in hits],
            "count": len(hits),
            "source_id": "isa_public_domain_land_tract_sales",
            "note": note,
        }

    before = lambda r: r["date_purchased"] <= TARGET_DATE      # noqa: E731
    return {
        "us_military_reservation": {
            "entries": [], "count": 0, "source_id": None,
            "refusal": ("RESERVED, not entered. The reservation is federal ground held "
                        "by the War Department and the register carries no patent for it "
                        "on the scene date. J. B. Beaubien's pre-emption over the south "
                        "fraction of section 10 is entered 1835-05-28 and is recorded "
                        "under that section, not here: it was litigated for years and "
                        "the reservation is not treated as his."),
        },
        "canal_commissioners_1830": entered(
            "09", lambda r: r["type_of_sale"] == "CN" and before(r),
            "The canal commissioners' own 1830 sale in section 9 — the survey the chip "
            "names. These are the quarter and half-quarter entries, NOT the town lots of "
            "the plat, which the register does not carry for this town."),
        "wabansia": {
            "entries": [], "count": 0, "source_id": None,
            "refusal": ("REFUSED, and the refusal is narrow. The register keys an entry "
                        "to a section and an aliquot; Wabansia is a PLAT, and no committed "
                        "record in this project says which section it was laid out in. "
                        "Its seated outline falls inside section 9's constructed square, "
                        "but a polygon falling inside a square is not a citation, and "
                        "picking the section 9 entries on that ground would be exactly "
                        "the arithmetic-dressed-as-evidence this file refuses elsewhere. "
                        "Sorting the register onto the tracts is T-1102's work."),
        },
        "kinzies_addition": entered(
            "10", lambda r: "NFR" in r["aliquot_or_lot_as_read"] and before(r),
            "The north fraction of section 10, entered by Robert A. Kinzie on "
            "1831-05-07. The register spells the surname two ways on one entry, and both "
            "rows are carried rather than silently merged."),
        "school_section": entered(
            "16", lambda r: r["type_of_sale"] == "SC" and before(r),
            "The school-section sale of 22-23 October 1833 — 337 rows, and the chip's "
            "own date. Only the count is carried here; the rows themselves belong to "
            "T-1102, which sorts every sale onto its tract."),
        "fractional_section_15": {
            "entries": [], "count": 0, "source_id": "isa_public_domain_land_tract_sales",
            "refusal": ("The register's only section-15 entry is Mark Noble Jr's "
                        "11.61-acre addition of 1836-05-31, after the scene date. On "
                        "1835-07-01 the fraction is unentered public land, and that is a "
                        "statement about the register and not about occupation."),
        },
        "canal_section_9_remainder": {
            "entries": [], "count": 0, "source_id": None,
            "refusal": ("The same seven 1830 canal entries cover section 9 as a whole; "
                        "which of them fall outside the Original Town is T-1102's "
                        "question, because it needs every entry sorted onto a polygon."),
        },
    }


# ---------------------------------------------------------------- what each tract is

TRACT_NOTES = {
    "us_military_reservation": {
        "boundary_from": "tools/measure_no_build_ground.py reservation_ring() — the "
                         "committed Fort Dearborn reservation: two constructed sides "
                         "(Madison's line and the section line from G1) and the traced "
                         "waterline for the third.",
        "geometry_confidence": "inferred",
        "geometry_note": "Inherited whole from the committed ring (L108, L182). This "
                         "file neither re-derives it nor moves it.",
        "sources": ["wright_1834_nara_hup"],
    },
    "canal_commissioners_1830": {
        "boundary_from": "the four streets every account of the 1830 plat names as its "
                         "bounds — Kinzie, State, Madison and Des Plaines — each taken "
                         "from its committed line in data/streets/1835.json.",
        "geometry_confidence": "conjectural",
        "geometry_note": "CONJECTURAL, and for a reason worth stating: the four bounds "
                         "above are the standard account of the 1830 plat, and NO source "
                         "record this project holds states them. `thompson_plat_1830` "
                         "carries the plat's figures — roughly 0.375 square miles, 80-ft "
                         "streets, 18-ft alleys — and not its perimeter. So the streets "
                         "are committed and the CHOICE of those four as the bounds is "
                         "not, which is a conjecture however ordinary it sounds, and it "
                         "is graded as one until a held source draws the line. What can "
                         "be checked is checked: all 19 committed plat blocks fall "
                         "inside the rectangle. It is also an ENVELOPE, bigger than the "
                         "plat: the printed "
                         "figure for the Original Town is three-eighths of a square "
                         "mile; the four bounds give more, because the plat's actual "
                         "west edge north of Randolph is not committed here and the "
                         "rectangle carries ground the plat did not. The over-run is "
                         "measured on this record rather than absorbed.",
        "sources": ["thompson_plat_1830", "wright_1834_nara_hup"],
    },
    "wabansia": {
        "boundary_from": "data/traces/wabansia_seating.json, `tract_polygon_local_enu_m` "
                         "— the outline T-1086 seated on the committed town grid.",
        "geometry_confidence": "inferred",
        "geometry_note": "Taken whole from the committed seating. NO band of Wabansia's "
                         "own colour class stands on it; the colour evidence is absent, "
                         "not weak, and T-1096 measured the reason.",
        "sources": ["wright_1834_nara_hup"],
    },
    "kinzies_addition": {
        "boundary_from": "the envelope of the Addition's own five north-south streets "
                         "(Wolcott, Cass, Rush, Pine, Sand), Kinzie Street on the south "
                         "and its northmost committed corridor on the north.",
        "geometry_confidence": "reconstructed",
        "geometry_note": "The streets are committed; the envelope round them is not a "
                         "traced boundary. It is SHORT of the patent, and the shortfall "
                         "is measured on this record: the envelope excludes the water "
                         "lots between North Water Street and the river and the "
                         "shore-cut blocks east of Sand Street, neither of them "
                         "committed geometry (T-0799, T-0800).",
        "sources": ["wright_1834_nara_hup", "isa_public_domain_land_tract_sales"],
    },
    "school_section": {
        "boundary_from": "section 16, T39N R14E, from the PLSS grid carried from G1 "
                         "(L219) — the school section by statute, one nominal mile "
                         "square.",
        "geometry_confidence": "inferred",
        "geometry_note": "The strongest colour agreement on the sheet: 13 of chip 5's "
                         "15 bands stand inside this square and the other two straddle "
                         "its south line. The square is not derived FROM the colour; the "
                         "colour is what confirms it.",
        "sources": ["isa_public_domain_land_tract_sales", "wright_1834_nara_hup"],
    },
    "fractional_section_15": {
        "boundary_from": "section 15, T39N R14E, from the same grid, cut on the east by "
                         "the committed lake shore — which is what makes it fractional.",
        "geometry_confidence": "reconstructed",
        "geometry_note": "Two constructed sides and a traced one. The shore is the 1835 "
                         "committed trace, not the 1834 sheet's, so the fraction's area "
                         "is a scene-date figure and not the surveyor's.",
        "sources": ["wright_1834_nara_hup"],
    },
    "canal_section_9_remainder": {
        "boundary_from": "section 9 with the Original Town cut out of its south-east "
                         "corner — the L the two chips must partition the section into "
                         "if chip 2 is the 1830 plat and chip 9 is what was left.",
        "geometry_confidence": "conjectural",
        "geometry_note": "CONJECTURAL BY INHERITANCE. The section square is constructed "
                         "(L219) and would be `reconstructed`, but the notch cut out of "
                         "it is the Original Town's west bound, which is conjectural — "
                         "so this ring can be no better than that one, and it is not "
                         "graded better. The cut is only taken because the Original "
                         "Town's east and "
                         "south bounds stand within tolerance of section 9's own lines; "
                         "the two gaps are printed on this record and the cut refuses "
                         "itself if either opens past 25 m.",
        "sources": ["isa_public_domain_land_tract_sales", "wright_1834_nara_hup"],
    },
}


def read_bands():
    """Re-read the raster and re-find every band of every class. The extraction is
    read_wright_legend_swatches's, unchanged and imported rather than copied, so the two
    records can never drift apart on method."""
    import numpy as np                                           # noqa: PLC0415
    from PIL import Image                                        # noqa: PLC0415
    import read_wright_legend_swatches as R                      # noqa: PLC0415
    Image.MAX_IMAGE_PIXELS = None
    working = ROOT.parent.parent / load(NA_GCPS)["raster"]["working_copy"]
    if not working.exists():
        raise FileNotFoundError(working)
    arr = np.asarray(Image.open(working).convert("RGB"), dtype=np.float32)
    sw = load(SWATCHES)
    medians = [c["median_rgb"] for c in sw["chips"]]
    groups = R.classes_from(medians)
    paper = sw["method"]["paper_rgb"]
    reps = [[sum(medians[i - 1][k] for i in g) / len(g) for k in range(3)] for g in groups]
    mx, mn = arr.max(2), arr.min(2)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    from_paper = np.linalg.norm(arr - np.array(paper, dtype=np.float32), axis=2)
    stack = np.stack([np.linalg.norm(arr - np.array(r, dtype=np.float32), axis=2) for r in reps])
    label, best = stack.argmin(0), stack.min(0)
    keep = (best < R.BAND_MATCH) & (from_paper > R.BAND_PAPER_MIN) & (sat > R.BAND_SAT_MIN)
    K = R.BAND_K
    H, W = arr.shape[0] // K, arr.shape[1] // K
    out = {}
    for gi, group in enumerate(groups):
        cover = ((label == gi) & keep)[:H * K, :W * K].reshape(H, K, W, K).mean(axis=(1, 3))
        mask = cover > R.BAND_COVER
        bridged = mask.copy()
        for axis in (0, 1):
            for shift in (1, -1):
                bridged |= np.roll(mask, shift, axis=axis)
        found = []
        for comp in R._components(bridged, R.BAND_MIN_CELLS):
            ys = [p[0] * K for p in comp]
            xs = [p[1] * K for p in comp]
            found.append({"cells": len(comp),
                          "centroid_px": [sum(xs) / len(xs), sum(ys) / len(ys)],
                          "box_px": [min(xs), min(ys), max(xs), max(ys)]})
        found.sort(key=lambda b: -b["cells"])
        out[str(group)] = found
    return groups, out


# ---------------------------------------------------------------- the record

def assemble(rows_by_class, classes, band_extent):
    import read_wright_legend_swatches as R                      # noqa: PLC0415
    sw = load(SWATCHES)
    polys, cuts = build_polygons()
    to_grid, from_grid, ring_of, bearing, corner = sections()
    own = owners()
    verdicts = adjudicate(classes, rows_by_class, polys)

    # Counted PER CLASS, because "a band stands on this tract" is only evidence about the
    # tract when the band carries the tract's OWN colour. A band of somebody else's class
    # sitting on it is the opposite of evidence.
    own_class = {t: 0 for t in polys}
    any_class = {t: 0 for t in polys}
    for key, rows in rows_by_class.items():
        group = json.loads(key)
        for r in rows:
            if not isinstance(r["on"], str):
                continue
            any_class[r["on"]] += 1
            if CHIP_TRACT.get(next((c for c in group if CHIP_TRACT.get(c) == r["on"]), None)):
                own_class[r["on"]] += 1

    tracts = []
    for chip_rec in sw["chips"]:
        chip = chip_rec["chip"]
        group = next(g for g in classes if chip in g)
        tid = CHIP_TRACT.get(chip)
        entry = {
            "chip": chip,
            "id": tid or f"unnamed_1833_chip_{chip}",
            "legend_text": chip_rec["legend"]["text"],
            "legend_reading": chip_rec["legend"]["reading"],
            "survey_date_year": chip_rec["legend"]["date"],
            "colour_class": group,
            "colour_class_is_the_chip_alone": len(group) == 1,
        }
        if tid is None:
            v = verdicts[str(chip)]
            entry.update({
                "placed": False,
                "polygon_local_enu_m": None,
                "why_not_placed": v["why_not_placed"],
                "positional_adjudication": {k: v[k] for k in
                                            ("class_mates_named", "bands_total",
                                             "bands_excluded", "bands_on_a_class_mate",
                                             "bands_on_other_named_ground",
                                             "bands_on_unnamed_ground",
                                             "unnamed_spread_m", "unnamed_ground_is",
                                             "clusters_at_link_m", "coherent",
                                             "wash_extent_local_m")},
                "wash_grade": "conjectural" if v["coherent"] else None,
                "geometry_confidence": None,
                "owner_on_scene_date": {"refusal": "no polygon, so no ground to own"},
            })
        else:
            ring = polys[tid]
            note = TRACT_NOTES[tid]
            area = ring_area(ring)
            entry.update({
                "placed": True,
                "polygon_local_enu_m": [[round(x, 2), round(y, 2)] for x, y in ring],
                "area_m2": round(area, 1),
                "area_acres": round(area / ACRE_M2, 2),
                "boundary_from": note["boundary_from"],
                "geometry_confidence": note["geometry_confidence"],
                "geometry_note": note["geometry_note"],
                "bands_of_its_own_class_standing_on_it": own_class[tid],
                "bands_of_any_class_standing_on_it": any_class[tid],
                "owner_on_scene_date": own[tid],
                "sources": note["sources"],
            })
        tracts.append(entry)

    checks = cross_checks(polys, tracts)
    return {
        "$schema_note": ("AUTHORED, and it authors no coordinate. Every ring below is "
                         "re-derived by tools/build_survey_tracts.py from ground this "
                         "project already committed; the gate rebuilds all of them and "
                         "refuses any drift. Nothing here is traced off a colour."),
        "id": "survey_tracts_1835",
        "target_date": TARGET_DATE,
        "ticket": "T-1101 (piece 1 of T-1097, itself piece 2 of T-0792)",
        "tool": "tools/build_survey_tracts.py",
        "reads": ["data/traces/wright_1834_legend_swatches.json",
                  "data/traces/gcp/wright_1834_nara_hup_gcps.json",
                  "data/streets/1835.json",
                  "data/traces/wabansia_seating.json",
                  "data/research/land_sales/entries.json"],
        "why_this_file_exists": (
            "Wright's legend is the only place on any sheet this project holds that says "
            "WHO SURVEYED WHAT GROUND AND WHEN. T-1096 measured its nine chips and found "
            "six separable colours, so the ground under a wash cannot be named from the "
            "wash. This file names it from geometry instead, and uses the washes only to "
            "check the naming and to adjudicate the two chips that name no tract."),
        "grades": (
            "`geometry_confidence` grades THE BOUNDARY and nothing else. `inferred` is a "
            "ring this project already committed and this file only carries. "
            "`reconstructed` is a ring built here out of committed parts — an envelope, "
            "a cut, a clip — which is a construction and says so. `conjectural` is a ring "
            "whose SHAPE is a construction but whose CHOICE of bounds rests on nothing "
            "this project holds: the Original Town's four named streets are the standard "
            "account and no source record here states them, and section 9's remainder "
            "inherits that because the notch cut out of it is that same west bound. No "
            "ring anywhere here is `documented`, because not one of the nine boundaries "
            "has been traced off a source that draws it."),
        "the_colour_is_a_check_not_a_source": (
            "A wash is 17 px of ink at 600 dpi, about 12 m of ground, and its class is "
            "one of six. Every boundary here is known to better than that from committed "
            "control, so reading one off a wash would be a loss of precision dressed as "
            "evidence. What the washes CAN do is agree or disagree, and where they "
            "disagree — Wabansia's absent class, chip 2's two corner bands — the record "
            "says so."),
        "exclusions": exclusions(load(SWATCHES)),
        "section_grid": {
            "control_point": "G1, State & Madison — the PLSS corner of sections 9/10/15/16",
            "control_point_local_enu": [round(corner[0], 3), round(corner[1], 3)],
            "bearing": round(bearing, 6),
            "liberty": "L219",
            "note": "Carried, not traced. Inherited from tools/resolve_land_tracts.py.",
        },
        "cuts": cuts,
        "tracts": tracts,
        "unnamed_chips": verdicts,
        "cross_checks": checks,
        "bands": {"classes": [str(g) for g in classes],
                  "by_class": rows_by_class,
                  "extent": band_extent},
        "summary": {
            "chips": len(tracts),
            "placed": sum(1 for t in tracts if t["placed"]),
            "refused": sum(1 for t in tracts if not t["placed"]),
            "bands_classified": sum(len(v) for v in rows_by_class.values()),
            "bands_excluded": sum(1 for v in rows_by_class.values() for r in v if r["excluded"]),
            "bands_on_a_named_tract": sum(1 for v in rows_by_class.values()
                                          for r in v if isinstance(r["on"], str)),
        },
    }


def cross_checks(polys, tracts):
    """Three claims this file can be caught on, each with a number attached."""
    lh = load(LIGHTHOUSE)["derived"]
    pt = (lh["local_e"], lh["local_n"])
    res = polys["us_military_reservation"]
    ot = next(t for t in tracts if t["id"] == "canal_commissioners_1830")
    ka = next(t for t in tracts if t["id"] == "kinzies_addition")
    patent = 102.29
    blocks = load(ROOT / "data/traces/vectors/thompson_lots.json")["blocks"]
    otring = polys["canal_commissioners_1830"]
    outside = [b["id"] for b in blocks
               if not all(inside(tuple(p), otring) for p in b["boundary_local_enu_m"])]
    return {
        "committed_plat_blocks_inside_the_original_town": {
            "claim": ("If the four streets are the 1830 plat's bounds, every block this "
                      "project has already generated from the Thompson module must fall "
                      "inside them. This does not prove the bounds — a bigger rectangle "
                      "would pass too — but a block outside would disprove them."),
            "blocks": len(blocks),
            "outside": outside,
            "confidence": "inferred",
        },
        "lighthouse_inside_the_reservation": {
            "claim": ("Wright's `L. House` glyph, committed at "
                      "data/traces/wright_1834_lighthouse_glyph.json, must stand INSIDE "
                      "chip 1's polygon — the parent ticket names it as the control the "
                      "blue swatch already has."),
            "inside": inside(pt, res),
            "distance_inside_m": round(ring_distance(pt, res), 2),
            "glyph_local_m": [lh["local_e"], lh["local_n"]],
            "confidence": "inferred",
        },
        "original_town_against_its_printed_area": {
            "claim": "The 1830 plat is printed as three-eighths of a square mile.",
            "printed_km2": round(0.375 * 2.589988, 4),
            "envelope_km2": round(ot["area_m2"] / 1e6, 4),
            "over_run_ratio": round((ot["area_m2"] / 1e6) / (0.375 * 2.589988), 3),
            "reading": ("The envelope over-runs the plat, as an envelope of four outer "
                        "bounds must. It is recorded, not corrected: correcting it would "
                        "mean inventing the plat's west edge north of Randolph."),
            "confidence": "inferred",
        },
        "kinzies_addition_against_its_patent": {
            "claim": ("Robert A. Kinzie entered the north fraction of section 10 at "
                      "102.29 acres on 1831-05-07."),
            "patent_acres": patent,
            "street_envelope_acres": ka["area_acres"],
            "shortfall_acres": round(patent - ka["area_acres"], 2),
            "reading": ("The envelope is SHORT, and it should be: the patent covers the "
                        "water lots and the shore-cut blocks the committed street lines "
                        "do not reach."),
            "confidence": "inferred",
        },
    }


# ---------------------------------------------------------------- the four entry points

def derive(bands_by_class, classes):
    """Everything downstream of the raster read, so --build and --check-properties run
    the SAME derivation and can only differ where the raster does."""
    polys, _ = build_polygons()
    to_grid, from_grid, ring_of, bearing, corner = sections()
    import read_wright_legend_swatches as R                      # noqa: PLC0415
    shore = shore_in_grid(to_grid)
    excl = exclusions(load(SWATCHES))
    grid_rings = [ring_of(sec) for sec in ("09", "10", "15", "16")]
    rows = {k: classify(v, polys, R.to_local, shore, to_grid, excl, grid_rings)
            for k, v in bands_by_class.items()}
    return rows


def build() -> int:
    try:
        classes, raw = read_bands()
    except ImportError as exc:
        print(f"SKIP --build: needs numpy and Pillow ({exc})", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"SKIP --build: the working copy is not in this checkout ({exc})", file=sys.stderr)
        return 3
    rows = derive(raw, classes)
    extent = {k: [{"cells": b["cells"], "box_px": b["box_px"]} for b in v[:1]]
              for k, v in raw.items()}
    doc = assemble(rows, classes, extent)
    RECORD.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    s = doc["summary"]
    print(f"wrote {RECORD.relative_to(ROOT)}: {s['placed']} of {s['chips']} chips placed, "
          f"{s['bands_classified']} bands classified, {s['bands_excluded']} excluded")
    return 0


def check_properties(doc: dict | None = None) -> int:
    """The gate. Offline: every polygon is rebuilt from committed inputs and every band
    verdict is re-taken from the band centroid the record itself carries."""
    doc = doc or load(RECORD)
    bad = []

    def want(cond, msg):
        if not cond:
            bad.append(msg)

    classes = [json.loads(c) for c in doc["bands"]["classes"]]
    raw = {k: [{"cells": r["cells"], "centroid_px": r["centroid_px"]} for r in v]
           for k, v in doc["bands"]["by_class"].items()}
    rows = derive(raw, classes)
    for k, v in rows.items():
        was = doc["bands"]["by_class"][k]
        want(len(v) == len(was), f"class {k}: {len(was)} bands stored, {len(v)} re-derived")
        for a, b in zip(v, was):
            want(a["on"] == b["on"] and a["excluded"] == b["excluded"],
                 f"class {k} band at {b['centroid_px']}: stored on={b['on']!r} "
                 f"excluded={b['excluded']!r}, re-derives on={a['on']!r} "
                 f"excluded={a['excluded']!r}")
            want(max(abs(x - y) for x, y in zip(a["local_m"], b["local_m"])) < 0.11,
                 f"class {k} band at {b['centroid_px']}: local metres drifted")

    polys, cuts = build_polygons()
    want(cuts == doc["cuts"], f"the cuts drifted: stored {doc['cuts']}, re-derived {cuts}")
    for t in doc["tracts"]:
        if not t["placed"]:
            want(t["polygon_local_enu_m"] is None,
                 f"chip {t['chip']} is refused but carries a polygon")
            want(t["geometry_confidence"] is None,
                 f"chip {t['chip']} is refused but carries a geometry confidence")
            continue
        if t["id"] not in polys:
            bad.append(f"{t['id']} is placed but this tool derives no polygon for it — "
                       f"a chip that names no tract may not be given one")
            continue
        ring = polys[t["id"]]
        stored = t["polygon_local_enu_m"]
        want(len(ring) == len(stored), f"{t['id']}: {len(stored)} stored vertices, "
                                       f"{len(ring)} re-derived")
        if len(ring) == len(stored):
            worst = max(math.dist(a, b) for a, b in zip(ring, stored))
            want(worst < 0.015, f"{t['id']}: a vertex moved {worst:.3f} m")
        area = ring_area(ring)
        want(abs(area - t["area_m2"]) < 1.0,
             f"{t['id']}: area {t['area_m2']} m2 stored, {area:.1f} re-derived")
        want(abs(area / ACRE_M2 - t["area_acres"]) < 0.02,
             f"{t['id']}: acres do not follow from the area")
        want(t["geometry_confidence"] in ("inferred", "reconstructed", "conjectural"),
             f"{t['id']}: geometry graded {t['geometry_confidence']!r} — a boundary this "
             f"project has never traced off a source may not be `documented`")
        want(t["geometry_note"], f"{t['id']}: a derived boundary needs its reasoning")

    # The refusals are gated, because they are the finding. If a future edit ever made an
    # unnamed chip's scatter look coherent, or gave Wabansia colour evidence it does not
    # have, the step must say so rather than let the prose stand unchallenged.
    for chip in UNNAMED_CHIPS:
        t = next(x for x in doc["tracts"] if x["chip"] == chip)
        want(not t["placed"], f"chip {chip} names no tract and may not be placed")
        want(t["why_not_placed"], f"chip {chip} needs its refusal stated")
    wab = next(t for t in doc["tracts"] if t["id"] == "wabansia")
    want(wab["bands_of_its_own_class_standing_on_it"] == 0,
         "Wabansia's colour refusal is recorded but it now carries bands of its own "
         "class — the refusal, or the band reading, is stale")

    cc = doc["cross_checks"]
    lh = load(LIGHTHOUSE)["derived"]
    d = ring_distance((lh["local_e"], lh["local_n"]), polys["us_military_reservation"])
    want(inside((lh["local_e"], lh["local_n"]), polys["us_military_reservation"]),
         "the `L. House` glyph has fallen outside chip 1's polygon")
    want(abs(d - cc["lighthouse_inside_the_reservation"]["distance_inside_m"]) < 0.02,
         f"the glyph stands {d:.2f} m inside, "
         f"{cc['lighthouse_inside_the_reservation']['distance_inside_m']} recorded")
    want(not cc["committed_plat_blocks_inside_the_original_town"]["outside"],
         "a committed plat block now stands outside the Original Town's four bounds: "
         f"{cc['committed_plat_blocks_inside_the_original_town']['outside']}")
    ka = next(t for t in doc["tracts"] if t["id"] == "kinzies_addition")
    want(ka["area_acres"] < cc["kinzies_addition_against_its_patent"]["patent_acres"],
         "the street envelope has grown past the patent it is supposed to fall short of")

    if bad:
        for m in bad:
            print(f"FAIL {m}")
        return 1
    s = doc["summary"]
    print(f"survey tracts: {s['placed']} of {s['chips']} chips placed and re-derived, "
          f"{s['bands_classified']} band verdicts re-taken, {s['refused']} chips refused")
    return 0


def report() -> int:
    doc = load(RECORD)
    print(f"THE NINE SURVEY TRACTS — {doc['target_date']}\n")
    for t in doc["tracts"]:
        if t["placed"]:
            print(f"  chip {t['chip']}  {t['legend_reading']}")
            print(f"          {t['area_acres']:>9.2f} acres   {t['geometry_confidence']:<14s}"
                  f" {t['bands_of_its_own_class_standing_on_it']} band(s) of its class on it")
            own = t["owner_on_scene_date"]
            if own.get("count"):
                first = own["entries"][0]
                print(f"          register: {own['count']} entr(y/ies), first "
                      f"{first['purchaser']} {first['date']}")
            else:
                print(f"          register: refused — {own['refusal'][:70]}…")
        else:
            v = t["positional_adjudication"]
            print(f"  chip {t['chip']}  {t['legend_reading']}  — NOT PLACED")
            print(f"          {v['bands_total']} bands, {v['bands_excluded']} excluded, "
                  f"{v['bands_on_a_class_mate']} on a class mate, "
                  f"{v['bands_on_unnamed_ground']} on unnamed ground")
            print(f"          {t['why_not_placed'][:150]}")
    print()
    for k, v in doc["cross_checks"].items():
        print(f"  {k}: " + ", ".join(f"{a}={b}" for a, b in v.items()
                                     if a not in ("claim", "reading", "confidence")))
    return 0


def self_test() -> int:
    base = load(RECORD)
    fired = []

    def fires(label, mutate):
        doc = json.loads(json.dumps(base))
        mutate(doc)
        out = io.StringIO()
        keep, sys.stdout = sys.stdout, out
        try:
            rc = check_properties(doc)
        finally:
            sys.stdout = keep
        fired.append((label, rc != 0))
        print(f"  {'fires' if rc != 0 else 'SILENT'}  {label}")

    def move_vertex(doc):
        t = next(x for x in doc["tracts"] if x["placed"])
        t["polygon_local_enu_m"][0][0] += 5.0

    def place_an_unnamed_chip(doc):
        t = next(x for x in doc["tracts"] if not x["placed"])
        t["placed"] = True
        t["polygon_local_enu_m"] = [[0, 0], [10, 0], [10, 10]]

    def upgrade_a_grade(doc):
        t = next(x for x in doc["tracts"] if x["placed"])
        t["geometry_confidence"] = "documented"

    def fake_a_band_verdict(doc):
        k = next(iter(doc["bands"]["by_class"]))
        doc["bands"]["by_class"][k][0]["on"] = "school_section"

    def give_wabansia_colour(doc):
        next(t for t in doc["tracts"] if t["id"] == "wabansia")[
            "bands_of_its_own_class_standing_on_it"] = 3

    def shrink_the_patent(doc):
        doc["cross_checks"]["kinzies_addition_against_its_patent"]["patent_acres"] = 1.0

    print("self-test — every assertion below must fire when its fact is broken")
    fires("a tract vertex moved 5 m", move_vertex)
    fires("an unnamed chip given a polygon", place_an_unnamed_chip)
    fires("a constructed boundary graded `documented`", upgrade_a_grade)
    fires("a band's verdict rewritten by hand", fake_a_band_verdict)
    fires("Wabansia given colour evidence it does not have", give_wabansia_colour)
    fires("the patent shrunk below the envelope it bounds", shrink_the_patent)
    silent = [l for l, ok in fired if not ok]
    if silent:
        print(f"SILENT: {len(silent)} assertion(s) did not fire: {silent}")
        return 1
    print(f"all {len(fired)} assertions fire")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.build:
        return build()
    if a.check_properties:
        return check_properties()
    if a.report:
        return report()
    if a.self_test:
        return self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
