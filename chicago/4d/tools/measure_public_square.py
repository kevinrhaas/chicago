#!/usr/bin/env python3
"""How much of the public square was wet — asked of the committed ground.

T-0027, opened by T-E5(a). The ticket's question presumes a number can be read
off the square, and the first job here is to find out whether one can. It cannot,
and the reason is worth more than the number would have been.

    tools/measure_public_square.py          print the readings
    tools/measure_public_square.py --gate   exit 1 if an assertion below fails

WHAT THE READING SAYS. Sampled at 0.5 m over the committed platted block —
`blk_randolph_lasalle`, Randolph to Washington, Clark to LaSalle — the terrain
stands between +2.84 and +2.96 ft above the summer-1835 water surface and NOT ONE
SAMPLE reaches it. The wet fraction is zero, and it is zero for a structural
reason rather than a measured one: the whole block's relief is about an inch and a
half, which is INSIDE the terrain spec's own declared micro-relief amplitude
(+/-0.10 ft of value noise, seed 18350701, which `micro_relief.note` calls "a
texture, not a claim"). There is no basin here to hold water. Reading a wet
fraction off this ground would be reading the noise seed.

SO THE ANSWER TO "HOW MUCH" IS A DEPTH, NOT A FRACTION. `docs/research/
01-terrain-hydrology.md` row 15 puts the pond's bed at **+1.0 to +2.0 ft**. The
committed ground stands 0.84 ft above the top of that band and 1.96 ft above its
floor, so the pond the dossier describes cannot be laid on this block: it has to
be DUG, everywhere, out of the one land elevation in this box that rests on a
documentary sentence ("elevated only two to three feet above the river"). That is
the finding T-E5(a) could not reach, and it is why the extent was never the whole
question.

AND THE DRAIN IS ALREADY HERE. `state_slough_course` — zone 14, carved by T-0005
and amended by T-0118 — is committed with its head "just east of Clark between
Washington and Randolph (the square's drain)". Its head vertex stands about 34 m
off the block's east kerb and feathers to zero depth, so the scene contains the
pond's drain and not the pond. T-E5(a) found a bridge over a watercourse the scene
did not contain; this is that shape once more, one feature upstream.

WHAT IS ASSERTED, and each one is a way this reading can go wrong:

 1. NO OPEN WATER ON THE SQUARE. Absolute zero, because zero is what the terrain
    models. If a future bake ever cuts the basin, this fires — and it should: the
    records below would then be describing ground that has moved under them.
 2. THE TERRAIN MODELS NO LANDFORM HERE. The block's whole relief must stay
    inside the spec's declared micro-relief amplitude. This is what makes
    assertion 1 a statement about the MODEL rather than a claim about 1835, and it
    fails the moment anything gives this block a shape.
 3. THE SQUARE IS PLANTED AS THE FLORA DOSSIER NAMES IT. `docs/research/
    02-flora.md` heads ZONE 3 "SLOUGH & SEDGE MEADOW (Public Square -> Tremont
    House site -> river at State St)" — the square by name — and z03's committed
    extent is an ELEVATION BAND that cannot reach a block the terrain draws at the
    plain's height. The zone now also covers this block by polygon; this holds
    that the polygon is the block, and that the sward it plants actually wins
    there against every other community's extent.
 4. THE DRAIN STILL HEADS AT THE SQUARE. The one piece of positive evidence that
    this block collected water is a committed watercourse whose head is described
    as the square's own. A re-carve that walks the head away takes the ground for
    assertion 3 with it, silently, and nothing else joins the two files.

This file states no number about 1835. The block is the committed plat's, the
elevations are the committed heightfield's, the bed band is the dossier's and the
drain is the terrain spec's.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from heightfield import Heightfield  # noqa: E402

EPOCH = "e1834_harbor_cut"
BLOCK = "blk_randolph_lasalle"
ZONE = "z03_sedge_meadow"
DRAIN = "state_slough_course"
FT = 0.3048

# The step the block is sampled at. Five times finer than the 2.5 m grid: the
# field is read bilinearly by the walker and by the renderer, so a grid-step
# reading would quantise the answer to the generator's own lattice.
STEP_M = 0.5

# The dossier's own bed band for zone 15, in feet above the datum water surface.
# Quoted, not chosen: docs/research/01-terrain-hydrology.md row 15.
DOSSIER_BED_FT = (1.0, 2.0)

# How far the drain's head may stand off the block before assertion 4 fires. The
# head is a reconstructed vertex inside a +/-20 m georeference band on the sheets
# it is fitted to (docs/RESEARCH/main_branch_sloughs_1833.md), so this is set to
# catch the head LEAVING the square's edge, not to re-argue where it sits.
MAX_DRAIN_HEAD_M = 60.0


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inside(point, polygon) -> bool:
    x, y = point
    hit = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def segment_distance(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def ring_distance(point, ring) -> float:
    return min(segment_distance(point, ring[i], ring[(i + 1) % len(ring)])
               for i in range(len(ring)))


def reaches(extent: dict, points, heights, water_gap_m: float) -> bool:
    """Could this extent match anywhere on the block?

    The four kinds `renderers/web/js/flora.js` implements, asked of the square
    rather than of one point, so assertion 3 can say which communities actually
    contend here instead of comparing priority numbers and calling every higher
    one a rival. `water_gap_m` is the block's own shortest distance to modelled
    water, which is what a `buffer` extent is measured against.
    """
    box = extent.get("box") or {}
    be, bn = box.get("e"), box.get("n")
    kind = extent.get("kind")
    lo_hi = extent.get("elev_m") or [0.0, 0.0]
    band = extent.get("distance_m") or [0.0, 0.0]
    holes = extent.get("exclude_polygons") or []
    patches = extent.get("include_polygons") or []
    for (e, n), h in zip(points, heights):
        if be and not (be[0] <= e <= be[1]):
            continue
        if bn and not (bn[0] <= n <= bn[1]):
            continue
        if kind == "everywhere":
            ok = True
        elif kind == "elevation_band":
            ok = lo_hi[0] <= h <= lo_hi[1]
        elif kind == "polygon":
            ok = inside((e, n), extent.get("polygon") or [])
        elif kind == "buffer":
            ok = extent.get("of") == "water" and band[0] <= water_gap_m <= band[1]
        else:
            ok = False
        if not ok:
            ok = any(inside((e, n), patch) for patch in patches)
        if ok and not any(inside((e, n), hole) for hole in holes):
            return True
    return False


def measure() -> tuple[dict, list[str]]:
    problems: list[str] = []
    epoch_dir = DATA / "terrain" / "epochs" / EPOCH
    field = Heightfield.load(epoch_dir)
    if field is None:
        return {}, [f"{EPOCH}: no committed heightfield to measure against"]
    spec = load(epoch_dir / "terrain_spec.json")
    lots = load(DATA / "traces" / "vectors" / "thompson_lots.json")
    blocks = {b["id"]: b for b in lots["blocks"]}
    block = blocks.get(BLOCK)
    if block is None:
        return {}, [f"{BLOCK}: the plat module no longer emits the public square"]
    ring = [list(p) for p in block["boundary_local_enu_m"]]

    water_m = float(field.meta.get("water_surface_m", 0.0))
    e_min = min(p[0] for p in ring)
    e_max = max(p[0] for p in ring)
    n_min = min(p[1] for p in ring)
    n_max = max(p[1] for p in ring)

    points: list[tuple[float, float]] = []
    heights: list[float] = []
    wet = 0
    e = e_min
    while e <= e_max:
        n = n_min
        while n <= n_max:
            if inside((e, n), ring):
                h = field.height(e, n)
                points.append((e, n))
                heights.append(h)
                if h <= water_m:
                    wet += 1
            n += STEP_M
        e += STEP_M
    if not heights:
        return {}, [f"{BLOCK}: sampled no ground — the block and the heightfield do not meet"]
    ordered = sorted(heights)

    # The block's own shortest reach to modelled water, off the committed field
    # rather than off the traces: every cell at or below the water surface is
    # water, which is what a `buffer of water` extent is measured against.
    water_gap_m = float("inf")
    for j in range(field.rows):
        n = field.origin_n + j * field.cell_m
        if not (n_min - 400.0 <= n <= n_max + 400.0):
            continue
        for i in range(field.cols):
            ecell = field.origin_e + i * field.cell_m
            if not (e_min - 400.0 <= ecell <= e_max + 400.0):
                continue
            if field.height(ecell, n) <= water_m:
                water_gap_m = min(water_gap_m, ring_distance((ecell, n), ring))


    amplitude_ft = float((spec.get("micro_relief") or {}).get("amplitude_ft", 0.0))
    relief_m = ordered[-1] - ordered[0]
    bed_lo, bed_hi = (v * FT for v in DOSSIER_BED_FT)

    # The drain the spec's own note calls the square's.
    drain = next((s for s in spec.get("swales", []) if s.get("id") == DRAIN), None)
    head_m = None
    if drain is None:
        problems.append(f"{DRAIN}: the terrain spec no longer carries the square's drain, and "
                        f"the sedge extent on {BLOCK} rests on it heading here")
    else:
        head = drain["line"][0]
        head_m = ring_distance(head, ring)
        if head_m > MAX_DRAIN_HEAD_M:
            problems.append(f"{DRAIN} heads {head_m:.1f} m off the public square, past the "
                            f"{MAX_DRAIN_HEAD_M:.0f} m this reading allows — the one committed "
                            f"feature that says this block drained no longer touches it")

    # Assertion 1: absolute zero, because zero is what the terrain models.
    if wet:
        problems.append(f"{BLOCK}: {wet} of {len(heights)} samples stand at or below the water "
                        f"surface. The terrain now models water on the public square, and the "
                        f"records that say it does not — data/flora/zones/{ZONE}.json, "
                        f"data/terrain/1835_intown_water_dating.json zone 15 — are stale")
    # Assertion 2: no landform, or assertion 1 is not about the model.
    if relief_m > amplitude_ft * 2.0 * FT:
        problems.append(f"{BLOCK}: relief across the block is {relief_m / FT:.3f} ft, past the "
                        f"{amplitude_ft * 2.0:.2f} ft the spec's micro-relief can produce. The "
                        f"terrain now gives the square a shape, and 'no basin here' has stopped "
                        f"being a statement about the model")

    # Assertion 3: the sedge meadow reaches the block, and wins there.
    zones = load(DATA / "flora" / "index.json")["zones"]
    entry = next((z for z in zones if z["id"] == ZONE), None)
    covered = 0
    if entry is None:
        problems.append(f"{ZONE}: not in the flora manifest, so the square is planted by "
                        f"whatever the elevation band happens to match")
    else:
        polys = (entry.get("extent") or {}).get("include_polygons") or []
        mine = [p for p in polys if len(p) >= 3]
        rivals = [z["id"] for z in zones
                  if z["id"] != ZONE and z["priority"] > entry["priority"]
                  and reaches(z.get("extent") or {}, points, heights, water_gap_m)]
        # The ring is the committed plat's, vertex for vertex. Held here rather
        # than trusted, because the whole defence of this extent is that no
        # boundary was drawn by hand — in particular not one fitted around the
        # three county buildings standing on the block.
        drifted = [p for p in mine
                   if len(p) != len(ring)
                   or any(math.hypot(a[0] - b[0], a[1] - b[1]) > 0.01
                          for a, b in zip(p, ring))]
        if drifted or not mine:
            problems.append(f"{ZONE}: its include_polygons is not the committed {BLOCK} ring. "
                            f"The square's sward is planted on the platted block or on nothing; "
                            f"a hand-drawn boundary here is an extent somebody chose")
        e = e_min
        while e <= e_max:
            n = n_min
            while n <= n_max:
                if inside((e, n), ring) and any(inside((e, n), p) for p in mine):
                    covered += 1
                n += STEP_M
            e += STEP_M
        share = covered / len(heights)
        if share < 0.99:
            problems.append(f"{ZONE}: covers {share * 100:.1f} % of the public square by "
                            f"polygon. The dossier names the whole block, so a partial cover is "
                            f"an extent somebody fitted")
        if rivals:
            problems.append(f"{ZONE} sits at priority {entry['priority']} and "
                            f"{', '.join(rivals)} outrank it over this block; the square is "
                            f"planted by another community than the one its evidence names")

    return {
        "samples": len(heights),
        "sample_area_m2": block["area_m2"] / len(heights),
        "area_m2": block["area_m2"],
        "water_surface_m": water_m,
        "min_ft": ordered[0] / FT,
        "max_ft": ordered[-1] / FT,
        "mean_ft": (sum(heights) / len(heights)) / FT,
        "relief_in": relief_m / 0.0254,
        "micro_relief_amplitude_ft": amplitude_ft,
        "wet_samples": wet,
        "wet_fraction": wet / len(heights),
        "dossier_bed_ft": DOSSIER_BED_FT,
        "cut_to_bed_top_ft": (ordered[0] - bed_hi) / FT,
        "cut_to_bed_floor_ft": (ordered[-1] - bed_lo) / FT,
        "drain_head_m": head_m,
        "water_gap_m": water_gap_m,
        "sedge_cover": covered / len(heights) if heights else 0.0,
    }, problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 when one of the four assertions fails")
    args = parser.parse_args()

    row, problems = measure()
    if row:
        print(f"   the public square, {row['area_m2']:.0f} m2, sampled at {STEP_M} m "
              f"({row['samples']} samples, one per {row['sample_area_m2']:.2f} m2)")
        print(f"   ground        +{row['min_ft']:.2f} to +{row['max_ft']:.2f} ft above the "
              f"water surface (mean +{row['mean_ft']:.2f})")
        print(f"   relief        {row['relief_in']:.2f} in across the whole block, against "
              f"+/-{row['micro_relief_amplitude_ft']:.2f} ft of declared micro-relief")
        print(f"   WET FRACTION  {row['wet_fraction'] * 100:.1f} %  "
              f"({row['wet_samples']} of {row['samples']} samples at or below the water)")
        print(f"   the dossier's bed  +{row['dossier_bed_ft'][0]:.1f} to "
              f"+{row['dossier_bed_ft'][1]:.1f} ft — the committed ground stands "
              f"{row['cut_to_bed_top_ft']:.2f} to {row['cut_to_bed_floor_ft']:.2f} ft over it")
        if row["drain_head_m"] is not None:
            print(f"   the square's drain heads {row['drain_head_m']:.1f} m off the block edge, "
                  f"outside it")
        print(f"   sedge meadow  {row['sedge_cover'] * 100:.1f} % of the block")
    for problem in problems:
        print(f"   {problem}")
    if not problems:
        print("   no water is modelled on the public square, and nothing gives it a shape")
    return 1 if (problems and args.gate) else 0


if __name__ == "__main__":
    raise SystemExit(main())
