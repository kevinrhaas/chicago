"""Terrain for one epoch: spec + traced vectors -> heightfield + GLB.

    # heightfield only (no Blender needed — numpy is the one dependency)
    python3 generators/terrain_gen.py --epoch e1834_harbor_cut

    # heightfield AND the terrain / water GLBs
    blender -b -noaudio --factory-startup --python generators/terrain_gen.py -- --glb

Inputs, all committed:

    data/datum.json                                   origin and vertical datum
    data/terrain/epochs/<e>/terrain_spec.json         the authored zone table
    data/terrain/epochs/<e>/river.geojson             traced water polygon + bank runs
    data/terrain/epochs/<e>/hydrology.geojson         traced secondary watercourses
    data/terrain/epochs/<e>/shoreline.geojson         the harbour reach, the bar and the lake
    data/terrain/epochs/<e>/branches.geojson          the branches beyond the forks window
    data/terrain/epochs/<e>/south_branch_below_twelfth.geojson
                                                      the South Branch below Twelfth
                                                      Street, off Rees & Rucker 1849

Outputs:

    data/terrain/epochs/<e>/heightfield.json          runtime meta (what the renderer reads)
    data/terrain/epochs/<e>/heightfield.bin           int16 samples, row 0 = SOUTH
    assets/gltf/terrain__<e>.glb                      the ground
    assets/gltf/water__<e>.glb                        the water surface
    assets/manifest.json                              input hashes for the staleness gate

How the surface is built, and why it is built this way
------------------------------------------------------
Everything hangs off ONE geometric quantity: the signed distance from the traced
waterline. Land elevation is a function of distance inland; channel depth is a
function of distance offshore; both are zero at the waterline, so the ground
surface crosses Z = 0 exactly along the line traced off the Wright 1834 survey
and the water plane needs no separate shoreline geometry — it is simply the
plane Z = 0, and the terrain occludes it wherever the terrain is above it.

Land is assigned to a DIVISION by which of the three traced bank runs it is
nearest to. That is not a convenience: the North, South and West Divisions were
*defined* by the river, so deriving them from the river rather than drawing
three polygons by hand keeps the zone boundaries honest and keeps them correct
if the trace is ever refit.

Refuses to run while data/datum.json is unverified, for the same reason
generators/build.py does.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FT = 0.3048

# `generators/` on the path at IMPORT time, not part-way through main(). Run as
# `python3 generators/terrain_gen.py` it is already sys.path[0] and the flat
# imports below (terrain_inputs, mesh_inputs, common.mesh) resolve by luck; run as
# `blender --python generators/terrain_gen.py` sys.path[0] is elsewhere and the
# staleness hash — which is computed BEFORE the two inserts main() used to do —
# died on ModuleNotFoundError. The GLB half of this generator is a rare, deliberate
# invocation, which is exactly why nothing caught it.
if str(ROOT / "generators") not in sys.path:
    sys.path.insert(0, str(ROOT / "generators"))

try:
    import numpy as np
except ImportError:                                   # pragma: no cover
    np = None

try:
    import bpy                                        # noqa: F401
    HAVE_BPY = True
except ImportError:
    HAVE_BPY = False

# Confidence channel, docs/GLB-CONTRACT.md. Least confident wins.
CONF_DOCUMENTED, CONF_INFERRED, CONF_CONJECTURAL = 0.0, 0.5, 1.0

# The skirt carries the terrain's own edge heights outward so the river does not
# end in mid-air at the box boundary and the horizon is ground rather than void.
# It is an apron on the box's four sides rather than a radial scaling, because
# the box stopped being square when the ground was extended east: scaling a
# 2020 x 800 m rectangle radially would push the east edge out by a quarter of
# what it pushes the north edge, which is backwards. The margin is AT LEAST the
# distance at which renderers/web/js/world.js's haze is total, so the skirt's own
# outer edge can never be seen from anywhere inside the box.
SKIRT_MARGIN_MIN_M = 1500.0

# The signed container `gltf-transform` quantises POSITION into. It is 32767 and
# not 32768: a normalized int16 is `raw / 32767` by the glTF specification, which
# is what makes the ladder below symmetric about the mesh's own centre.
INT16_FULL_SCALE = 32767


def skirt_margin_m(span_m: float, cell_m: float) -> tuple[float, int]:
    """The apron's width, DERIVED so the publish step's lattice divides the grid.

    THE ARTEFACT THIS ENDS (T-0152). `tools/web_derivatives.sh` quantises the
    published ground's POSITION under ONE UNIFORM node scale, and that scale is
    set by the mesh's widest axis — the box plus two skirt margins. Measured on
    the bytes that shipped on 2026-08-23: scale 2510 m, translation at the mesh's
    own centre, rung `scale / 32767` = 76.6 mm, and every shipped vertex exactly
    `round((p - centre) / rung)` rungs from that centre (378,581 of 378,582 axis
    values reproduced to the bit; the one exception is a half-rung tie). So the
    quantiser is not approximate and it is not opaque: it is a ladder, and the
    only question is whether the generator's vertices stand on its rungs.

    They did not. 2.5 m of grid was 32.64 rungs, so a ground vertex was displaced
    in plan by up to half a rung, conformed at the displaced position by
    `renderers/web/js/terrain.js`, and therefore held the field's height for the
    WRONG PLACE. R-W6 named the cost — (slope x displacement) — and reasoned that
    "flat platted prairie cannot show this artefact at any bit depth". The east
    extension brought in bank faces at 60-90 %, which can: 56 of the field's
    259,689 sample points stood past the 22 mm road lift, worst 77.1 mm, one of
    them 0.1 m from the centreline of North Water Street.

    16 bits is the format's maximum and the master is 5.8 MB too big to ship
    uncompressed, so neither of the two obvious answers was available. This is
    the third: make the rung an exact submultiple of the grid, and the
    displacement is not reduced but ABOLISHED — every vertex the generator writes
    is already on a rung, so the quantiser rounds it to itself.

    The margin is what buys that, because the margin is what sets the scale:

        rung   = (span + 2 * margin) / 2 / 32767
        margin = 32767 * cell / k - span / 2        for rung = cell / k

    `span` is the box's WIDEST horizontal side, because that is the axis
    `gltf-transform` takes its uniform scale from. It was written as the
    east-west side until T-0464, which is not the same thing and only looked
    like it while the box was wider than it was tall: 2 020 x 930 m. The
    southern extension makes the box 2 020 x 4 200 m, so north-south is now the
    widest side and the margin has to be bought against IT or the rung stops
    dividing the grid and the plan displacement T-0152 abolished comes back.
    Taking the widest side costs a coarser rung — the apron has to reach the
    haze on the long axis, so `k` halves once, 32 to 16, and the rung goes
    78.125 mm to 156.25 mm. That costs nothing measurable, and this
    is why: the rung's job here is to DIVIDE 2.5 m, not to be small. 2.5 / 16 is
    exact, so every ground vertex still stands on a rung and the quantiser still
    rounds it to itself — plan displacement 0.0 mm at either rung. Height is not
    at risk either way, because terrain.js conforms the drawn ground to the
    field at the vertex's shipped (E, N); it is the PLAN position that has to be
    right, and it is.

    `k` is a POWER OF TWO, which is one more constraint than commensurability
    needs and is worth the metre or two it costs. `gltf-transform` quantises to a
    bit depth and stores the result in the container above it, so asking for
    fewer bits multiplies the rung by a power of two — under a power-of-two `k`
    the lattice stays commensurate at every depth from 11 bits up, and the
    generator is not silently coupled to a number that lives in a shell script.
    The largest such `k` is taken, since a finer ladder costs nothing here and
    the coarsest the search will accept is the one whose apron still reaches the
    haze distance.

    Returns the margin and the `k` it was derived from; the caller ASSERTS the
    result on the vertices themselves rather than trusting this arithmetic.
    """
    half = 0.5 * span_m
    k = 1
    while INT16_FULL_SCALE * cell_m / (k * 2) >= half + SKIRT_MARGIN_MIN_M:
        k *= 2
    return INT16_FULL_SCALE * cell_m / k - half, k


# The water plane has to reach past the skirt or the ground would run out over
# open water at the horizon.
WATER_MARGIN_EXTRA_M = 200.0


# How far a vertex may stand off the publish step's POSITION ladder before the
# generator refuses to export. A micron: the arithmetic in skirt_margin_m() is
# exact in binary and lands within 1e-9 of a rung, so this is four orders of
# magnitude of slack over the residual and four orders under the 22 mm road lift
# the whole exercise is protecting.
LATTICE_RESIDUAL_TOLERANCE_M = 1e-6


def check_quantisation_lattice(verts, e0, e1, n0, n1, margin_m, cell_m, k):
    """REFUSE to export a ground whose vertices do not stand on the publish rung.

    skirt_margin_m() is arithmetic, and arithmetic about a third-party tool is a
    belief until something checks it against the vertices that will actually be
    written. This is that check, and it is a refusal rather than a report for the
    same reason MESH_FIT_TOLERANCE_M is: a ground that quietly stops being
    commensurate is a ground that quietly goes back to holding the field's height
    for the wrong place, and nothing downstream of the bake would say so until
    somebody re-ran tools/measure_terrain_horizontal.mjs.

    The model it asserts is the one recovered from the shipped bytes: uniform
    node scale = half the widest extent, translation = the mesh's own centre,
    rung = scale / 32767.

    Returns the rung, in metres.
    """
    es = [v[0] for v in verts]
    ns = [v[1] for v in verts]
    ys = [v[2] for v in verts]
    spans = (max(es) - min(es), max(ns) - min(ns), max(ys) - min(ys))
    # The quantiser takes its uniform scale from the widest axis, so the margin
    # must have been bought against whichever of E and N that is — which is the
    # north-south side since T-0464 and was the east-west side before it. What
    # would break the derivation outright is HEIGHT becoming the widest axis:
    # skirt_margin_m() knows nothing about relief, so a box taller than it is
    # wide would set the rung off an axis no apron can reach.
    if spans[2] >= max(spans[0], spans[1]):
        raise SystemExit(
            f"REFUSING: the ground's widest axis is vertical "
            f"({spans[0]:.3f} x {spans[1]:.3f} x {spans[2]:.3f} m). The quantiser takes its "
            f"uniform scale from the widest axis, so skirt_margin_m() would be deriving the "
            f"apron against an axis it cannot reach. See T-0152.")
    rung = 0.5 * max(spans[0], spans[1]) / INT16_FULL_SCALE
    centre = (0.5 * (min(es) + max(es)), 0.5 * (min(ns) + max(ns)))
    worst, worst_at = 0.0, None
    for e, n, _y in verts:
        for axis, coord in enumerate((e, n)):
            q = (coord - centre[axis]) / rung
            off = abs(q - round(q)) * rung
            if off > worst:
                worst, worst_at = off, (e, n)
    if worst > LATTICE_RESIDUAL_TOLERANCE_M:
        raise SystemExit(
            f"REFUSING: a ground vertex stands {worst * 1000:.3f} mm off the POSITION ladder "
            f"tools/web_derivatives.sh will quantise it onto (rung {rung * 1000:.4f} mm, "
            f"grid cell / {cell_m / rung:.4f}), worst at E {worst_at[0]:.1f} N {worst_at[1]:.1f}. "
            f"The publish step would displace it in plan, terrain.js would then conform it to "
            f"the field's height for the wrong place, and the drawn ground would leave the road "
            f"lift on the steep east banks. Expected the rung to be the grid cell / {k}. "
            f"See T-0152 and skirt_margin_m().")
    # Stated as a fraction of the grid because that is the property, and the
    # margin is only how it was bought.
    assert abs(cell_m / rung - k) < 1e-6, (
        f"the rung is the grid cell / {cell_m / rung:.6f}, not / {k}")
    return rung

# A boundary landform's taper may not be shorter than this many publish rungs.
# Under one rung the two ring vertices would land on the same lattice position,
# which is a degenerate quad — `from_pydata` accepts one and the decimate
# modifier then segfaults on it (the same trap the skirt ring's own assert
# guards). A termination that short is also below the mesh's own resolution, so
# nothing is lost by carrying it instead.
SKIRT_TERMINATION_MIN_RUNGS = 4


def ring_local(feats, ref, origin):
    """One traced ring in local ENU metres, open (no repeated closing vertex)."""
    o_e, o_n = origin
    f = feats[ref["feature"]]
    coords = f["geometry"]["coordinates"][int(ref.get("ring", 0))]
    return [(c[0] - o_e, c[1] - o_n) for c in coords][:-1]


def _first_exit(ring, scan_axis, scan_at, out_axis, bound, sign):
    """Walking outward from the box edge, how far out the ring is first crossed.

    The SMALLEST positive outward distance, not the largest: walking south from a
    point inside the ring, the first boundary crossing is where the landform ends.
    A ring that re-enters further out (a second lobe the box has cut off from the
    first) is not attached to this boundary vertex and is not this vertex's taper.

    Returns None when the ring is never crossed outward of `bound` on that line.
    """
    best = None
    for i in range(len(ring)):
        a, b = ring[i - 1], ring[i]
        lo, hi = a[scan_axis], b[scan_axis]
        if not ((lo <= scan_at < hi) or (hi <= scan_at < lo)):
            continue
        t = (scan_at - lo) / (hi - lo)
        d = sign * (a[out_axis] + t * (b[out_axis] - a[out_axis]) - bound)
        if d > 0 and (best is None or d < best):
            best = d
    return best


def skirt_terminations(spec, feats, origin, h_m, rung_m):
    """Which boundary vertices stand on a landform that ENDS inside the skirt.

    THE RULE, AND WHY IT IS A RULE ABOUT EVIDENCE RATHER THAN ABOUT THE BAR
    (T-0939). The apron carries each boundary vertex outward at its own height,
    which is right when the boundary is a CROSS-SECTION of ground that continues
    — and the mainland's is: its traced shore runs stop at the edge of the
    tracing window, which is a place the reading stopped, not a place the land
    did. It is wrong when the boundary cuts a landform that ENDS, because then
    1.55 km of apron is extruded from a section of something 36 m long. The owner
    photographed exactly that: the 1834 sand bar leaving the box at a constant
    +1.21 m and running to the haze as a straight ribbon three and a half times
    longer than the island it is a section of.

    The only evidence that can say a landform ends is a CLOSED traced outline
    that the box truncates, and the spec already holds those — `islands`, "land
    the water goes round", each resolved to a ring in `shoreline.geojson`. So
    this asks every island ring, on every one of the four edges, two questions:
    is the boundary vertex inside the ring, and how far past the edge does the
    ring reach on that vertex's own line? The second answer is the taper LENGTH,
    read off the trace rather than chosen — for the sand bar it runs from 1.4 m
    at its western edge to 35.8 m at the tip and back to 2.0 m at its eastern,
    which is the hook Wright drew.

    Where the apron arrives is the WATER the landform stands in: the boundary
    heights either side of the run, interpolated across it. That is what the
    skirt would have carried there had the landform not been in the way, so the
    run's apron rejoins its neighbours' instead of ending in a wall.

    Lengths are snapped to the publish step's POSITION rung, because the vertices
    this places have to stand on that lattice like every other ground vertex
    (see skirt_margin_m and check_quantisation_lattice). The snap is at most half
    a rung — 39 mm against the +/-20 m the planform itself carries.

    Returns {edge: [run, ...]} with each run
    {"landform", "index0", "extent_m": [...], "base_y": [...]}, indexed along
    that edge's own axis (columns from the west on the south and north edges,
    rows from the south on the west and east edges). An edge with no truncated
    landform is absent, and a box with none returns {} — which is the case where
    this changes nothing at all.
    """
    g = spec["grid"]
    cell = float(g["cell_m"])
    e0, e1 = float(g["e_min_m"]), float(g["e_max_m"])
    n0, n1 = float(g["n_min_m"]), float(g["n_max_m"])
    rows, cols = h_m.shape
    # name: (scan axis, count, coordinate along the edge, out axis, bound,
    #        outward sign, the heightfield row/column that edge is)
    edges = {
        "south": (0, cols, lambda i: e0 + i * cell, 1, n0, -1, lambda i: h_m[0, i]),
        "north": (0, cols, lambda i: e0 + i * cell, 1, n1, +1, lambda i: h_m[rows - 1, i]),
        "west": (1, rows, lambda i: n0 + i * cell, 0, e0, -1, lambda i: h_m[i, 0]),
        "east": (1, rows, lambda i: n0 + i * cell, 0, e1, +1, lambda i: h_m[i, cols - 1]),
    }
    floor_m = SKIRT_TERMINATION_MIN_RUNGS * rung_m
    out = {}
    for isl in spec.get("islands", []):
        ring = ring_local(feats, isl["ring"], origin)
        for name, (sa, count, at, oa, bound, sign, edge_h) in edges.items():
            along = np.array([at(i) for i in range(count)], float)
            fixed = np.full(count, bound, float)
            E, N = (along, fixed) if sa == 0 else (fixed, along)
            inside = point_in_ring(E, N, ring)
            reach = {}
            for i in range(count):
                if not inside[i]:
                    continue
                d = _first_exit(ring, sa, at(i), oa, bound, sign)
                if d is None:
                    continue
                snapped = round(d / rung_m) * rung_m
                if snapped >= floor_m:
                    reach[i] = snapped
            if not reach:
                continue
            for run in _contiguous(sorted(reach)):
                lo, hi = run[0], run[-1]
                # The water either side of the run — the height the skirt would
                # have carried here had the landform not been standing in it.
                west_y = float(edge_h(max(0, lo - 1)))
                east_y = float(edge_h(min(count - 1, hi + 1)))
                span = max(1, hi + 1 - lo + 1)
                base = [west_y + (east_y - west_y) * (k + 1) / span
                        for k in range(len(run))]
                out.setdefault(name, []).append({
                    "landform": isl["id"],
                    "index0": lo,
                    "extent_m": [round(reach[i], 6) for i in run],
                    "base_y": [round(b, 6) for b in base],
                })
    return out


def _contiguous(indices):
    """Split a sorted index list into runs of consecutive integers."""
    runs = []
    for i in indices:
        if runs and i == runs[-1][-1] + 1:
            runs[-1].append(i)
        else:
            runs.append([i])
    return runs


# How far the decimated ground mesh may depart from the heightfield the walker
# samples. 30 mm is well under the resolution of anything a person notices on
# foot and two orders under the relief being modelled.
MESH_FIT_TOLERANCE_M = 0.03


def _unbuffer():
    """Blender block-buffers the script's stdout, so a crash loses every print
    that would have told you where it crashed. Line-buffer it."""
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:  # noqa: BLE001
        pass


def argv_after_ddash() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def load(p: Path):
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# vector helpers — exact distances, no rasterised approximations
# ---------------------------------------------------------------------------

def seg_distance(E, N, pts):
    """Distance from every grid point to a polyline, exactly. `pts` is a list of
    (e, n). Vectorised over the grid, looped over the (few dozen) segments."""
    best = np.full(E.shape, np.inf, np.float64)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 < 1e-12:
            d = np.hypot(E - ax, N - ay)
        else:
            t = np.clip(((E - ax) * dx + (N - ay) * dy) / L2, 0.0, 1.0)
            d = np.hypot(E - (ax + t * dx), N - (ay + t * dy))
        np.minimum(best, d, out=best)
    return best


def seg_distance_along(E, N, pts):
    """As `seg_distance`, but also returns the ARC LENGTH along the polyline at
    each grid point's nearest point on it — the coordinate a swale's authored
    `depth_profile` is stated in. Measured from the line's FIRST vertex, in
    metres, so the profile reads in the same direction the line is written."""
    best = np.full(E.shape, np.inf, np.float64)
    along = np.zeros(E.shape, np.float64)
    acc = 0.0
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length < 1e-6:
            d = np.hypot(E - ax, N - ay)
            a_here = np.full(E.shape, acc)
        else:
            t = np.clip(((E - ax) * dx + (N - ay) * dy) / (length * length), 0.0, 1.0)
            d = np.hypot(E - (ax + t * dx), N - (ay + t * dy))
            a_here = acc + t * length
        closer = d < best
        best = np.where(closer, d, best)
        along = np.where(closer, a_here, along)
        acc += length
    return best, along


def point_in_ring(E, N, ring):
    """Crossing-number point-in-polygon, vectorised over the grid."""
    inside = np.zeros(E.shape, bool)
    n = len(ring)
    for i in range(n):
        ax, ay = ring[i - 1]
        bx, by = ring[i]
        if ay == by:
            continue
        cond = (ay > N) != (by > N)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (bx - ax) * (N - ay) / (by - ay) + ax
        inside ^= cond & (E < xint)
    return inside


def carry_run_north(pts, to_n):
    """A traced run with its northern tip carried due north to `to_n`.

    The tip has to be an END of the polyline — a run whose northernmost vertex
    is in its middle is a bend, not a truncation, and carrying THAT north would
    put a spur through the middle of a bank. Refused rather than guessed at.
    """
    i = max(range(len(pts)), key=lambda k: pts[k][1])
    if i not in (0, len(pts) - 1):
        raise ValueError(f"northernmost vertex {i} of {len(pts)} is not an end of "
                         f"the run, so it is a bend and not the end of a tracing "
                         f"window; refusing to carry it north")
    tip = (pts[i][0], to_n)
    return ([tip] + list(pts)) if i == 0 else (list(pts) + [tip])


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def value_noise(E, N, wavelength, seed):
    """Two-dimensional value noise with smoothstep interpolation. Deterministic
    from `seed`; no dependency on any RNG's stream order."""
    gx = E / wavelength
    gy = N / wavelength
    x0 = np.floor(gx).astype(np.int64)
    y0 = np.floor(gy).astype(np.int64)
    fx, fy = gx - x0, gy - y0

    def h(ix, iy):
        k = (ix * np.int64(374761393) + iy * np.int64(668265263)
             + np.int64(seed) * np.int64(2246822519))
        k = (k ^ (k >> np.int64(13))) * np.int64(1274126177)
        k = k ^ (k >> np.int64(16))
        return (k & np.int64(0xFFFFFF)) / float(0xFFFFFF)

    sx, sy = smoothstep(fx), smoothstep(fy)
    a = h(x0, y0) * (1 - sx) + h(x0 + 1, y0) * sx
    b = h(x0, y0 + 1) * (1 - sx) + h(x0 + 1, y0 + 1) * sx
    return (a * (1 - sy) + b * sy) * 2.0 - 1.0


# ---------------------------------------------------------------------------
# the field
# ---------------------------------------------------------------------------

def profile(E, knots):
    """A quantity that varies west-to-east, read off a piecewise-linear table.

    The town's terrain varies along E and not along distance from the river:
    the plain west of State Street stands two to three feet over the water and
    the ground east of it nine to ten, and the break between them is a line
    running north-south. So every level the spec states — bank crest, plain,
    bank face width — is a table of (local E, value) knots rather than a scalar.
    Constant outside the first and last knot, which is what `np.interp` does and
    what "no evidence past here" should do.
    """
    xs = [float(k[0]) for k in knots]
    ys = [float(k[1]) for k in knots]
    return np.interp(E, xs, ys)


def build_field(spec, feats, origin):
    """Returns (h_m, conf, water_mask, meta, geom) on the spec's grid.

    h_m[row][col], row 0 = SOUTH edge, col 0 = WEST edge — the layout
    renderers/web/js/terrain.js's Heightfield sampler requires.

    `feats` is every traced feature the epoch owns, by id, across river.geojson,
    hydrology.geojson, shoreline.geojson and branches.geojson. The spec decides
    which of them the field reads; loading a file does not put its features in
    the ground.
    """
    o_e, o_n = origin
    g = spec["grid"]
    cell = float(g["cell_m"])
    e0, e1 = float(g["e_min_m"]), float(g["e_max_m"])
    n0, n1 = float(g["n_min_m"]), float(g["n_max_m"])
    cols = int(round((e1 - e0) / cell)) + 1
    rows = int(round((n1 - n0) / cell)) + 1
    E, N = np.meshgrid(e0 + cell * np.arange(cols), n0 + cell * np.arange(rows))

    def to_local(coords):
        return [(c[0] - o_e, c[1] - o_n) for c in coords]

    def ring_of(spec_ref):
        f = feats[spec_ref["feature"]]
        return to_local(f["geometry"]["coordinates"][int(spec_ref.get("ring", 0))])[:-1]

    # The traced shore runs, in local metres. Resolved before the water mask
    # because `southern_lake` below is stated against the SHORE and not against
    # the water wash, and the waterline needs them anyway.
    shore_runs = {s["id"]: to_local(feats[s["id"]]["geometry"]["coordinates"])
                  for s in spec["shore_runs"]}
    # A TRACED RUN THAT STOPS AT THE EDGE OF ITS WINDOW HAS NOT REACHED THE END
    # OF WHAT IT DRAWS. `skirt_terminations` says the same thing about the box's
    # own walls — "a place the reading stopped, not a place the land did" — and
    # the north wall is where it started to matter: the North Branch's two banks
    # end on the line Wright ruled across the top of his sheet, and the
    # harbour-reach shore ends 2.7 m short of the box. Left there, the waterline
    # north of each is measured to the run's last VERTEX rather than to a bank,
    # which stands the ground off a cliff and silences the lake rule that reads
    # the run per row. Each carry is declared in the spec, run by run, and
    # carries the tip's own easting rather than the bearing of its last segment:
    # the minimal continuation, because a bearing is a claim about where the
    # line bends above the sheet.
    for cy in spec.get("trace_carries", []):
        shore_runs[cy["run"]] = carry_run_north(shore_runs[cy["run"]],
                                                float(cy["to_n_m"]))

    # ---- what is water ----------------------------------------------------
    # Union of the traced water polygons, minus their islands. The sand bar is
    # LAND inside water — the interior ring of the harbour-reach polygon — so
    # membership has to understand islands and not only banks.
    in_water = np.zeros(E.shape, bool)
    islands = np.zeros(E.shape, bool)
    for wp in spec["water_polygons"]:
        body = point_in_ring(E, N, ring_of({"feature": wp["feature"], "ring": 0}))
        for r in wp.get("island_rings", []):
            hole = point_in_ring(E, N, ring_of({"feature": wp["feature"], "ring": r}))
            body &= ~hole
            islands |= hole
        in_water |= body
    # The traced polygons stop at the edge of the traced window, which is not a
    # shore. Beyond it the sheet is still lake, and calling it land would be the
    # largest false claim available here. The rule is stated per ROW rather than
    # as a hand-drawn line, so it cannot drift away from the trace it extends:
    # east of the easternmost traced water in a row there is nothing else.
    lake_rule = spec.get("open_lake")
    if lake_rule:
        guard = float(lake_rule["east_of_m"])
        idx = np.arange(E.shape[1])[None, :]
        east = np.where(in_water & (E > guard), idx, -1).max(axis=1)
        in_water |= (idx > east[:, None]) & (east >= 0)[:, None] & (E > guard)
    # The same argument, made where the water wash runs out instead of where the
    # tracing window does. South of the sand bar's traced hook the harbour trace
    # carries the SHORE — the east edge of Fractional Section 15, a surveyed line
    # — all the way to the foot of the sheet, but its water wash south of there
    # is patches rather than a margin, so `open_lake`'s per-row test ("east of
    # the easternmost traced WATER") measures from a patch and leaves the ground
    # between two patches standing as dry land. It came out as a 4.8 m plateau of
    # mainland sand ridge in the middle of Lake Michigan. This rule measures from
    # the traced SHORE instead: south of the stated line, every cell east of the
    # row's easternmost crossing of a named shore run is lake. Islands are
    # subtracted after it, exactly as they are after `open_lake`, so the bar's
    # southern hook is not touched by it.
    # ONE RULE STATED AT BOTH ENDS. `northern_lake` is the same sentence at the
    # other end of the same trace, and it is here for the same reason: the
    # harbour-reach polygon's NORTH edge is the top of the tracing window, and
    # Wright's wash frays across it — between N +1114.8 and +1118.0 it reads as
    # two lobes with a 25 m notch between them, and the ground inside that notch
    # is not east of the row's easternmost water. It came out as a one-cell
    # causeway of 8.2 ft sand ridge standing in Lake Michigan at N +1117.5,
    # which is the southern fault exactly, found at the far end of the box by
    # T-1123's extension. The two blocks are read by one loop so neither can
    # drift away from the other.
    for key, sign in (("southern_lake", -1.0), ("northern_lake", +1.0)):
        rule = spec.get(key)
        if not rule:
            continue
        n_cap = float(rule["south_of_n_m" if sign < 0 else "north_of_n_m"])
        east_edge = np.full(E.shape[0], -np.inf)
        for rid in rule["shore_runs"]:
            pts = shore_runs[rid]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if y1 == y2:
                    continue
                lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
                beyond = (N[:, 0] > n_cap) if sign > 0 else (N[:, 0] < n_cap)
                sel = (N[:, 0] >= lo) & (N[:, 0] <= hi) & beyond
                if not sel.any():
                    continue
                t = (N[sel, 0] - y1) / (y2 - y1)
                east_edge[sel] = np.maximum(east_edge[sel], x1 + t * (x2 - x1))
        # AND THE SHORE DOES NOT END AT TWELFTH STREET EITHER -- and since
        # T-1151 it does not have to be HELD to not end there. This is where
        # `southern_lake.beyond_the_trace` stood: below south_shore_harbor_reach's
        # last vertex at N -2159.9 every row's east_edge was -inf, the rule could
        # not fire, and 355 x 1 640 m of Lake Michigan came out as dry prairie --
        # the same false coast the rule above exists to prevent -- so the edge
        # held that vertex's easting, E +1347.4, for the whole 1 640 m to the
        # floor. It was conjectural and it was the lake's half of L239.
        #
        # REES & RUCKER 1849 draws the pre-fill shore beside this reach, and
        # tools/trace_lake_shore_rees_1849.py traces it into an ordinary shore
        # run (`lake_shore_below_twelfth`) which the loop above already knows how
        # to read. So there is no held easting here any more and no code behind
        # one: the shore falls away south-east from E +1298.9 at the splice to
        # E +1689.6 at the floor, 390 m of easting the held value denied. What
        # the trace does NOT relax is `evidence_limit`, which still writes every
        # vertex below N -2149.4 conjectural, water and land alike; nor does it
        # blend the 49 m step at the row where the two surveys abut, which is
        # this shore's documented post-pier erosion and is left in the data.
        in_water |= (E > east_edge[:, None]) & np.isfinite(east_edge)[:, None]

    # AND THE RIVER DOES NOT END AT TWELFTH STREET EITHER -- and since T-1150 it
    # does not have to be RULED to not end there. This is where `southern_branch`
    # stood: a held easting that carried the channel's own 45.3 m cross-section
    # at N -2110 due south, 1 690 m, to the box floor, because `branches.geojson`
    # stops on the School Section's south line and Wright's sheet stops there
    # with it. It was conjectural, it was recorded as L239, and its own note said
    # where the answer lived -- "a source this corpus does not hold".
    #
    # The corpus holds one now. REES & RUCKER 1849 reaches a mile and a quarter
    # past Cermak Road; it is georeferenced in data/traces/gcp/
    # rees_rucker_1849_gcps.json at RMS 25.0 m and traced by
    # tools/trace_south_branch_rees_1849.py into an ordinary water polygon and
    # two ordinary bank runs, which the loops above already know how to read.
    # So there is no rule here any more, and no code: the branch bends east to
    # E +567 about Sixteenth Street and swings south-west toward the portage, and
    # at the box floor its centre stands 521 m west of where the held easting put
    # it. What the trace does NOT relax is `evidence_limit`, which still writes
    # every vertex below N -2149.4 conjectural, water and land alike.

    # THE SPLICES — where two tracing windows are declared to abut and the
    # sampled row between them falls inside neither ring. The windows meet on a
    # shared map row, but each closes with its own SLANTED chord across the
    # channel and the two chords are neither parallel nor coincident: at the
    # forks/North-Branch splice the forks polygon reaches E -160.3 at N +402.5
    # and the branch polygon starts at -195.4, so 35 m of channel belongs to
    # neither and stands as a 2.5 m-wide, 1.0 m-high weir across the river. The
    # southern splice carries the identical bar at N -405 (E +5 to +32.5) and
    # has done since T-0219 committed it; T-1123 built the northern twin and
    # this repairs both, because it is one seam mechanism and not two.
    #
    # The water is spanned from the traced BANKS either side of the seam rather
    # than from either polygon: the runs that meet at a splice are named in the
    # spec, the vertex of each nearest the band is its tip, and the span is the
    # hull of the west tips to the hull of the east tips. It is a union and can
    # only ADD water, never take a traced cell away, and it reaches one sampled
    # row per splice.
    for sp in spec.get("splices", []):
        lo, hi = sorted(float(x) for x in sp["n_range"])
        mid = 0.5 * (lo + hi)
        def tip(rid, at=mid):
            return min(shore_runs[rid], key=lambda q: abs(q[1] - at))
        west = min(tip(r)[0] for r in sp["west_runs"])
        east = max(tip(r)[0] for r in sp["east_runs"])
        in_water |= ((N >= lo) & (N <= hi) & (E >= west) & (E <= east))

    in_water &= ~islands

    # ---- the waterline ----------------------------------------------------
    # Distance is taken to the traced SHORE RUNS and the island rings, never to
    # the water polygons' own boundaries: those boundaries close across the
    # traced window (the forks polygon at E +390, the harbour polygon at E +314
    # and again out in the lake), and a window edge is a place the tracing
    # stopped, not a bank. Measuring to it would raise a bank across open water.
    waterlines = [seg_distance(E, N, pts) for pts in shore_runs.values()]
    for isl in spec.get("islands", []):
        r = ring_of(isl["ring"])
        waterlines.append(seg_distance(E, N, r + [r[0]]))
    d_shore = np.minimum.reduce(waterlines)

    # ---- the north-side slough, buffered off its traced centreline -------
    slough_feat = feats.get("north_side_slough")
    wc = {w["id"]: w for w in spec.get("watercourses", [])}
    if slough_feat is not None:
        line = to_local(slough_feat["geometry"]["coordinates"])
        s_half = 0.5 * float(slough_feat["properties"]["drafted_width_m"])
        d_slough = seg_distance(E, N, line)
        in_slough = d_slough < s_half
        slough_bed = float(wc["north_side_slough"]["bed_ft"])
        slough_efold = float(wc["north_side_slough"].get("e_fold_m", 9.0))
    else:
        d_slough = np.full(E.shape, 1e9)
        in_slough = np.zeros(E.shape, bool)
        s_half, slough_bed, slough_efold = 0.0, 0.0, 9.0

    water = in_water | in_slough
    # distance INTO the water from the nearest waterline, and distance INLAND
    d_in = np.where(in_water, d_shore, 0.0)
    d_in = np.maximum(d_in, np.where(in_slough, s_half - d_slough, 0.0))
    d_land = np.minimum(np.where(in_water, 1e9, d_shore),
                        np.where(in_slough, 1e9, d_slough - s_half))
    d_land = np.maximum(d_land, 0.0)

    # ---- channel bed: inverse-distance blend of the reach beds -----------
    wsum = np.zeros(E.shape)
    bsum = np.zeros(E.shape)
    fsum = np.zeros(E.shape)
    default_efold = float(spec["channel_profile"]["e_fold_m"])
    for r in spec["reaches"]:
        anchors = r.get("anchors") or [[r["anchor_e"], r["anchor_n"]]]
        rf = float(r.get("e_fold_m", default_efold))
        for a_e, a_n in anchors:
            dd = np.maximum(np.hypot(E - float(a_e), N - float(a_n)), 1.0)
            w = 1.0 / (dd * dd)
            wsum += w
            bsum += w * float(r["bed_ft"])
            fsum += w * rf
    bed_ft = bsum / wsum
    efold = fsum / wsum
    bed_ft = np.where(in_slough & ~in_water, slough_bed, bed_ft)
    efold = np.where(in_slough & ~in_water, slough_efold, efold)
    depth_ft = bed_ft * (1.0 - np.exp(-d_in / efold))

    # ---- which division is this land in ----------------------------------
    # By which traced shore it is nearest to, still: the divisions were DEFINED
    # by the river. A division may own more than one run now, because the forks
    # trace and the harbour-reach trace are two windows onto one bank.
    divisions = spec["divisions"]
    dists = np.stack([
        np.minimum.reduce([seg_distance(E, N, shore_runs[s["id"]])
                           for s in spec["shore_runs"] if s["division"] == div["id"]])
        for div in divisions])
    nearest = np.argmin(dists, axis=0)
    # South of the evidence there is no traced shore to be nearest TO, so this
    # becomes a Voronoi diagram of two trace ENDPOINTS and it flips: at E +405
    # the ground steps 1.4 ft between N -2900 and N -3100 because the West
    # Division's endpoint became the closer one. A division is a thing the RIVER
    # makes, and the river is not down there. Every row below the limit takes the
    # division map of the last row the evidence reaches, so the relief bands each
    # division declares carry south with it rather than being cut off from the
    # ground they explain. See T-0464 and the carry below.
    ev_limit = spec.get("evidence_limit")
    ev_below = N[:, 0] < float(ev_limit["south_of_n_m"]) if ev_limit else None
    if ev_below is not None and ev_below.any() and not ev_below.all():
        ev_ref = int(np.argmax(~ev_below))
        nearest = np.where(ev_below[:, None], nearest[ev_ref][None, :], nearest)

    level_ft = np.zeros(E.shape)
    face = np.full(E.shape, float(spec["bank"]["face_m"]))
    band = {}
    for i, div in enumerate(divisions):
        mine = nearest == i
        crest = profile(E, div["crest_profile"])
        plain = profile(E, div["plain_profile"])
        lv = crest + (plain - crest) * np.clip(d_land / float(div["far_m"]), 0.0, 1.0)
        for m in spec.get("marsh_strips", []):
            if m["applies_to"] != div["id"]:
                continue
            w_m, b_m = float(m["width_m"]), float(m["blend_m"])
            wgt = 1.0 - smoothstep((d_land - (w_m - b_m)) / b_m)
            if m.get("e_taper"):
                wgt = wgt * profile(E, m["e_taper"])
            lv = lv * (1.0 - wgt) + float(m["level_ft"]) * wgt
            band.setdefault("marsh_strip", np.zeros(E.shape, bool))
            band["marsh_strip"] |= mine & (wgt > 0.01)
        level_ft = np.where(mine, lv, level_ft)
        face = np.where(mine, profile(E, div["face_profile"]), face)
        for rb in spec.get("relief_bands", []):
            if rb["applies_to"] != div["id"]:
                continue
            lo, hi = rb["e_range"]
            band.setdefault(rb["id"], np.zeros(E.shape, bool))
            band[rb["id"]] |= mine & (E >= float(lo)) & (E <= float(hi))

    # ---- south of the evidence, the land surface is CARRIED, not computed --
    # Every profile above is a function of E and of distance to a traced shore,
    # and south of Twelfth Street there is no traced shore: the South Branch
    # stops at N -2149.6 and south_shore_harbor_reach at N -2159.9, both at the
    # foot of Wright's sheet. Below that `nearest` becomes a Voronoi diagram of
    # two trace ENDPOINTS, and it flips — at E +405 the ground steps 1.4 ft
    # between N -2900 and N -3100 because the West Division's endpoint became the
    # closer one. That step is an artefact of where two tracings happened to
    # stop, it breaks the dossier's own flatness rule, and it is a relief claim
    # made by arithmetic rather than by a source.
    #
    # So the surface is carried south instead, exactly as the skirt carries a
    # boundary vertex outward at its own height: every row below the limit takes
    # the land level and the bank face of the last row the evidence reaches. The
    # north-south gradient of the frame is then zero by construction, which is
    # the honest answer — this ground is a container for the 1812 and 1880s
    # epochs, not a reconstruction of 1835, and evidence_limit marks every
    # vertex of it conjectural. The WATER is not carried: it is left to the
    # traced polygons and to southern_lake's rules, so nothing here invents a
    # river running due south. See T-0464.
    if ev_below is not None and ev_below.any() and not ev_below.all():
        level_ft = np.where(ev_below[:, None], level_ft[ev_ref][None, :], level_ft)
        face = np.where(ev_below[:, None], face[ev_ref][None, :], face)
        for _m in band.values():
            _m[ev_below] = _m[ev_ref]

    # ---- islands: land the water goes round ------------------------------
    conj_land = np.zeros(E.shape, bool)
    for isl in spec.get("islands", []):
        m = islands & point_in_ring(E, N, ring_of(isl["ring"]))
        level_ft = np.where(m, float(isl["crest_ft"]), level_ft)
        face = np.where(m, float(isl["face_m"]), face)
        band.setdefault(isl["id"], np.zeros(E.shape, bool))
        band[isl["id"]] |= m
        if isl.get("confidence") == "reconstructed":
            conj_land |= m

    # ---- mounds: the one piece of high ground the record names ------------
    for md in spec.get("mounds", []):
        rr = np.hypot(E - float(md["centre_e"]), N - float(md["centre_n"]))
        flat, out = float(md["flat_radius_m"]), float(md["outer_radius_m"])
        w = 1.0 - smoothstep((rr - flat) / max(1e-9, out - flat))
        level_ft = level_ft + float(md["rise_ft"]) * w
        band.setdefault(md["id"], np.zeros(E.shape, bool))
        band[md["id"]] |= rr <= out

    # ---- swales: the prairie drains and the in-town sloughs ----------------
    # One cut field, combined by MAX rather than by sum (T-0118): the slough
    # courses are single watercourses written as more than one entry, and where
    # two entries meet at a shared vertex the sum used to dig a joint deeper
    # than either entry states (the -5.0 ft State joint L149 recorded as a
    # convenience). With max, entries whose depths agree at the join carve one
    # continuous bed and no entry can deepen another. Nothing else changes:
    # no two swales cross, so away from the joins max and sum are the same
    # number.
    #
    # `depth_ft` remains the entry's one stated depth. An entry may add a
    # `depth_profile` — [[along_m, depth_ft], ...] knots in arc length from the
    # line's first vertex, linearly interpolated, held constant beyond the
    # ends — so a course can feather out to grade at its head instead of
    # running its full cut to the last vertex and stopping (the open-trench
    # fault), and a two-entry watercourse can grade through its join instead
    # of stepping (the dry-sill fault). The profile's deepest knot must equal
    # `depth_ft`, so the figure a reader (and the Evidence panel) sees is the
    # depth the ground actually reaches.
    swale_cut = np.zeros(E.shape)
    for s in spec.get("swales", []):
        pts = [tuple(p) for p in s["line"]]
        depth = float(s["depth_ft"])
        knots = s.get("depth_profile")
        if knots:
            deepest = max(float(k[1]) for k in knots)
            if abs(deepest - depth) > 1e-6:
                raise SystemExit(
                    f"swale '{s.get('id')}': depth_profile reaches {deepest} ft "
                    f"but depth_ft states {depth} ft — the stated figure must "
                    f"be the depth the ground reaches")
            dd, along = seg_distance_along(E, N, pts)
            d_ft = np.interp(along, [float(k[0]) for k in knots],
                             [float(k[1]) for k in knots])
        else:
            dd = seg_distance(E, N, pts)
            d_ft = depth
        hw = float(s["half_width_m"])
        prof = np.clip(1.0 - (dd / hw) ** 2, 0.0, 1.0)
        cut = d_ft * prof
        np.maximum(swale_cut, cut, out=swale_cut)
        conj_land |= cut > 0.02
    level_ft = level_ft - swale_cut
    band["swales"] = conj_land.copy()

    # ---- micro-relief -----------------------------------------------------
    mr = spec.get("micro_relief", {})
    amp = float(mr.get("amplitude_ft", 0.0))
    micro = np.zeros(E.shape)
    if amp > 0:
        waves = mr.get("wavelengths_m", [50.0])
        seed = int(mr.get("seed", 1))
        for k, wl in enumerate(waves):
            micro += value_noise(E, N, float(wl), seed + 977 * k) / (k + 1)
        micro *= amp / max(1e-9, sum(1.0 / (k + 1) for k in range(len(waves))))
    # ...but NOT over the carried frame. The noise is declared in the spec as "a
    # texture, not a claim" — it exists so ground the sources call dead flat
    # still reads as ground under a walker's feet, and so walking gives motion
    # parallax. South of evidence_limit there are no sources and there is no
    # walker: the nearest a camera gets is the town, 1.6 km north, which is past
    # the distance at which world.js's haze is total. So the texture buys nothing
    # down there and costs a great deal, because it is what stops the planar
    # dissolve collapsing a surface that is otherwise EXACTLY planar — one
    # evidenced row repeated 661 times. Measured on this bake: with the texture
    # everywhere the extension ships a 27,019,736-byte master and a 2,646,392-byte
    # web derivative; stopped at Madison it ships 17,919,344 and 1,819,896 — 9.10
    # MB of master and 807 KiB of published payload, for ground nothing walks on
    # and no camera resolves. That is the measured storage reason the ticket asks
    # for before the field is allowed to change, and the 2.5 m cell is preserved
    # either way (T-0464).
    south_limit = mr.get("south_limit_n_m")
    if amp > 0 and south_limit is not None:
        micro = np.where(N < float(south_limit), 0.0, micro)

    # ---- assemble ---------------------------------------------------------
    # The bank ramp is an ease-OUT (steepest at the waterline, flattening into
    # the plain), not a smoothstep. Two reasons, and the second is the one that
    # matters. Physically, a natural bank in alluvium is undercut by the flow and
    # is steepest right at the water. Numerically, a smoothstep leaves the ground
    # almost exactly flat for the first metre inland, so the surface's Z = 0
    # contour — which IS the drawn waterline, since the water is the plane Z = 0 —
    # is badly conditioned and snaps to cell boundaries. An ease-out crosses zero
    # with a definite slope and the shoreline comes out crisp.
    t_bank = np.clip(d_land / face, 0.0, 1.0)
    ramp = 1.0 - (1.0 - t_bank) ** 2
    h_ft = np.where(water, depth_ft, (level_ft + micro) * ramp)

    # ---- bridge approach earthworks (T-0046) ------------------------------
    # Every bridge deck ends on the traced waterline, where the bank ramp above
    # puts the ground at exactly zero — so without these, no deck can be entered
    # from its bank. Each approach is a graded road corridor along its spec line
    # (deck-end first): a `fill` RAISES the ground to `deck_ft` at the deck end,
    # falling inland at `grade`, level for `half_width_m` either side of the
    # line with `side_slope` shoulders beyond, and carries the crest
    # `end_overhang_m` past the deck end into the shallows — the fill the log
    # abutment cribs retain, and the only place this generator deliberately
    # raises traced water above the plane. A `cut` is the mirror: the ground is
    # graded DOWN to the deck at the end, rising inland at the same grade, and
    # carried the same overhang under the deck (on land only) so the ends read
    # down to the crossing rather than standing proud beside it. Both are
    # applied as max()/min() against the assembled surface, so each dies
    # out exactly where the natural ground takes over — no toe step, no berm.
    # The crest is packed one seat BELOW the deck surface, not flush with it.
    # Physically that is what an earth approach against a plank deck is — the
    # fill packs under the plank line and the last step onto the boards is a
    # step. Numerically it is load-bearing: the walker resolves its floor as
    # max(deck, ground) over the deck polygon, and a crest quantised to the
    # heightfield's 5 mm lattice can land a float's width ABOVE the deck it was
    # authored to meet, which would put the walker on ground instead of planks
    # for the first stride of every crossing. 0.06 ft (18 mm) clears both the
    # quantisation and the bilinear mixing while staying far inside the 0.35 m
    # step-up rule.
    APPROACH_SEAT_FT = 0.06
    for ap in spec.get("approaches", []):
        (a_e, a_n), (b_e, b_n) = [(float(p[0]), float(p[1])) for p in ap["line"]]
        length = math.hypot(b_e - a_e, b_n - a_n)
        ux, uy = (b_e - a_e) / length, (b_n - a_n) / length
        t_ap = (E - a_e) * ux + (N - a_n) * uy
        d_ap = np.abs(-(E - a_e) * uy + (N - a_n) * ux)
        shoulder_ft = np.maximum(d_ap - float(ap["half_width_m"]), 0.0) \
            * float(ap["side_slope"]) / FT
        fall_ft = float(ap["grade"]) * np.maximum(t_ap, 0.0) / FT
        over = float(ap["end_overhang_m"])
        before = h_ft
        if ap["mode"] == "fill":
            target = float(ap["deck_ft"]) - APPROACH_SEAT_FT - fall_ft - shoulder_ft
            zone = (t_ap >= -over) & (t_ap <= length) \
                & np.where(water, (t_ap <= over) & (d_ap <= float(ap["half_width_m"])),
                           True)
            h_ft = np.where(zone, np.maximum(h_ft, target), h_ft)
        else:
            target = float(ap["deck_ft"]) - APPROACH_SEAT_FT + fall_ft + shoulder_ft
            zone = (t_ap >= -over) & (t_ap <= length) & ~water
            h_ft = np.where(zone, np.minimum(h_ft, target), h_ft)
        touched = np.abs(h_ft - before) > 1e-6
        conj_land |= touched & ~water
        band.setdefault(f"approach_{ap['id']}", np.zeros(E.shape, bool))
        band[f"approach_{ap['id']}"] |= touched

    conf = np.where(water, CONF_CONJECTURAL, CONF_INFERRED)
    conf = np.where(conj_land & ~water, CONF_CONJECTURAL, conf)
    # The box is a FRAME and the frame now reaches a mile and a half past the
    # last thing this corpus says about ground (T-0464). Extending a division's
    # plain profile into that is not an inference from a source, it is the
    # generator having nowhere to stop, so every vertex down there is marked
    # conjectural rather than carrying the inferred grade its neighbours earn.
    ev = spec.get("evidence_limit")
    if ev:
        conf = np.where(N < float(ev["south_of_n_m"]), CONF_CONJECTURAL, conf)

    meta = {
        "cols": cols, "rows": rows, "cell_m": cell,
        "origin_e": e0, "origin_n": n0,
        "box": {"e": [e0, e1], "n": [n0, n1]},
        "min_m": float((h_ft * FT).min()), "max_m": float((h_ft * FT).max()),
        "water_fraction": float(water.mean()),
        "land_min_ft": float(h_ft[~water].min()), "land_max_ft": float(h_ft[~water].max()),
    }
    geom = {"E": E, "N": N, "d_land": d_land, "face": face,
            "swale": conj_land, "bands": band, "cell": cell}
    return h_ft * FT, conf, water, meta, geom


# ---------------------------------------------------------------------------
# gradient audit — the dossier's own flatness rule, checked rather than claimed
# ---------------------------------------------------------------------------

def gradient_audit(h_m, water, geom, spec):
    """Check, rather than claim, the dossier's own flatness rule: outside the
    zones that earn relief, hold local gradients under 0.5 ft per 300 ft.

    The zones that DO earn relief are named ONE BY ONE, each with the dossier
    zone that licenses it, and each is reported with its own worst gradient
    rather than swept into a single excused remainder. The dossier's modelling
    rule 1 exempts zones 3-7 and the fort mound by name; the State Street
    break-of-slope is exempted here as well, because zone 10 states its own fall
    as "~5-6 ft over 300 ft" and cannot obey a 0.5 ft rule while doing that. The
    exemption is written down in the spec's `relief_bands`, not decided here.
    """
    cell = geom["cell"]
    # The rule is about the FALL ACROSS A 300-FT BLOCK — the drainage grade of
    # the plain — not about the cell-to-cell derivative, which on any real
    # ground is dominated by surface texture. So the baseline is a 300 ft
    # (91.44 m) chord, and the sub-block roughness is reported separately
    # instead of being smuggled into the same number.
    k = max(1, int(round(300.0 * FT / cell)))
    # The shore exclusion is per cell, because the bank face is: 6 m where the
    # crest is a 2 ft alluvial bank at the forks and 25 m where it is a 9 ft
    # sand ridge falling to the lake.
    shore = geom["d_land"] < 2.5 * geom["face"]
    marsh_m = max((float(m["width_m"]) + float(m["blend_m"])
                   for m in spec.get("marsh_strips", [])), default=0.0)

    bands = dict(geom["bands"])
    bands["bank_face"] = shore
    relief_any = np.zeros(h_m.shape, bool)
    for m in bands.values():
        relief_any |= m
    # The carried frame is not audited as plain, and is reported on its own line
    # instead. The dossier's modelling rule is a statement about the town's
    # ground; south of evidence_limit there is no reconstruction for it to be a
    # statement about, only the last evidenced row carried south (T-0464). Its
    # north-south gradient is the micro-relief texture and nothing else, and its
    # east-west gradient is that one row's, so auditing it as plain would report
    # the SAME east-west slope 660 more times and call each repeat a separate
    # failure. The skirt, which is the same idea one step further out, has never
    # been audited either.
    ev = spec.get("evidence_limit")
    frame = (geom["N"] < float(ev["south_of_n_m"])) if ev else np.zeros(h_m.shape, bool)
    ok = (~water) & (~relief_any) & (geom["d_land"] >= marsh_m) & (~frame)

    de = (h_m[:, k:] - h_m[:, :-k]) / FT
    dn = (h_m[k:, :] - h_m[:-k, :]) / FT
    ve = ok[:, k:] & ok[:, :-k]
    vn = ok[k:, :] & ok[:-k, :]
    block = np.concatenate([np.abs(de[ve]), np.abs(dn[vn])]) if (ve.any() or vn.any()) \
        else np.zeros(1)

    gy, gx = np.gradient(h_m, cell)
    slope = np.hypot(gx, gy) * 300.0
    rough = slope[ok] if ok.any() else np.zeros(1)
    relief = (~water) & ~ok
    rel = slope[relief] if relief.any() else np.zeros(1)

    fr = frame & (~water) & (~relief_any)
    fde = np.abs(de)[fr[:, k:] & fr[:, :-k]]
    fdn = np.abs(dn)[fr[k:, :] & fr[:-k, :]]
    carried = {
        "cells": int(fr.sum()),
        "block_max": round(float(max(fde.max() if fde.size else 0.0,
                                     fdn.max() if fdn.size else 0.0)), 3),
        "north_south_block_max": round(float(fdn.max()) if fdn.size else 0.0, 3),
        "note": "the ground carried south of evidence_limit, excluded from the plain "
                "audit and measured here instead. The surface is one evidenced row "
                "repeated, so north_south_block_max is the micro-relief texture and "
                "nothing else (the spec's own +/- 0.10 ft, two octaves), and the "
                "east-west figure is that row's own, already audited where it stands.",
    }

    per_zone = {}
    for name, m in sorted(bands.items()):
        mm = m & (~water)
        per_zone[name] = {
            "cells": int(mm.sum()),
            "cell_max": round(float(slope[mm].max()), 3) if mm.any() else 0.0,
        }

    return {
        "baseline_ft": 300.0,
        "shore_exclusion_m": [round(float((2.5 * geom["face"]).min()), 1),
                              round(float((2.5 * geom["face"]).max()), 1)],
        "marsh_exclusion_m": round(marsh_m, 1),
        "plain_cells_audited": int(ok.sum()),
        "carried_frame": carried,
        "plain_block_max": round(float(block.max()), 3),
        "plain_block_mean": round(float(block.mean()), 4),
        "passes": bool(block.max() <= 0.5),
        "plain_cell_roughness_max": round(float(rough.max()), 3),
        "shore_and_swale_cell_max": round(float(rel.max()), 3),
        "relief_zones_ft_per_300ft": per_zone,
    }


# ---------------------------------------------------------------------------
# writing
# ---------------------------------------------------------------------------

def write_heightfield(out_dir: Path, h_m, meta, spec, inputs_sha: str):
    scale = float(spec["grid"]["scale_m"])
    q = np.rint(h_m / scale).astype(np.int16)
    err = float(np.abs(q.astype(np.float64) * scale - h_m).max())
    (out_dir / "heightfield.bin").write_bytes(q.tobytes(order="C"))

    doc = {
        "_doc": "Runtime heightfield meta for terrain epoch e1834_harbor_cut. Row 0 is the "
                "SOUTH edge and column 0 the WEST edge; the sample at [0][0] sits exactly on "
                "(origin_e, origin_n) in local ENU metres from data/datum.json. Elevation in "
                "metres above the summer-1835 water surface: y = raw * scale + offset. "
                "GENERATED by generators/terrain_gen.py — do not hand-edit.",
        "epoch": spec["epoch"],
        "spec": "terrain_spec.json",
        "bin": "heightfield.bin",
        "encoding": "int16",
        "scale": scale,
        "offset": 0.0,
        "cols": meta["cols"], "rows": meta["rows"],
        "cell_m": meta["cell_m"],
        "origin_e": meta["origin_e"], "origin_n": meta["origin_n"],
        "box_local_enu_m": meta["box"],
        "min_m": round(meta["min_m"], 4), "max_m": round(meta["max_m"], 4),
        "quantisation_error_m": round(err, 5),
        "water_surface_m": 0.0,
        "water_fraction": round(meta["water_fraction"], 4),
        "relief_ft": {
            "land_min": round(meta["land_min_ft"], 3),
            "land_max": round(meta["land_max_ft"], 3),
            "channel_min": round(meta["min_m"] / FT, 3),
        },
        "gradient_audit_ft_per_300ft": meta.get("gradient_audit"),
        "skirt": meta.get("skirt"),
        "glb": {
            "ground": f"gltf/terrain__{spec['epoch']}.glb",
            "water": f"gltf/water__{spec['epoch']}.glb",
        },
        "inputs_sha256": inputs_sha,
    }
    (out_dir / "heightfield.json").write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def inputs_hash(paths) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(Path(p).read_bytes())
    return h.hexdigest()


def terrain_inputs_sha(ep_dir: Path) -> str:
    """Everything that determines this epoch's ground and water meshes.

    One definition, called both by the bake that writes `inputs_sha256` into
    `assets/manifest.json` and by `tools/validate.py`, which recomputes it to
    decide whether the committed GLB still matches its inputs. Two copies of this
    list would agree until the day one of them mattered.

    Nothing on this path imports bpy — the meshing does, this does not.
    """
    import terrain_inputs  # noqa: PLC0415 — flat import, generators/ is on sys.path

    return terrain_inputs.terrain_inputs_sha(ep_dir)


# ---------------------------------------------------------------------------
# meshing (bpy)
# ---------------------------------------------------------------------------

def build_meshes(h_m, conf, spec, epoch, outdir: Path, decimate_deg: float,
                 terminations=None):
    from math import radians

    from common.mesh import reset_scene, simple_material  # noqa: PLC0415

    g = spec["grid"]
    cell = float(g["cell_m"])
    e0, n0 = float(g["e_min_m"]), float(g["n_min_m"])
    e1, n1 = float(g["e_max_m"]), float(g["n_max_m"])
    rows, cols = h_m.shape

    def enu_to_blender(e, n, y):
        # glTF export runs with export_yup=True, which maps Blender +Z to glTF
        # +Y and Blender +Y to glTF -Z. So authoring (E, N, up) as Blender
        # (x=E, y=N, z=up) lands as glTF (x=E, y=up, z=-N) — exactly the ENU
        # convention docs/GLB-CONTRACT.md pins.
        return (e, n, y)

    results = []

    # ---- ground -----------------------------------------------------------
    reset_scene()
    verts, confs = [], []
    for r in range(rows):
        n = n0 + r * cell
        for c in range(cols):
            verts.append(enu_to_blender(e0 + c * cell, n, float(h_m[r, c])))
            confs.append(float(conf[r, c]))
    faces = []
    for r in range(rows - 1):
        base = r * cols
        for c in range(cols - 1):
            i = base + c
            faces.append((i, i + 1, i + 1 + cols, i + cols))

    # skirt: carry each boundary vertex outward to a larger rectangle, keeping
    # its own height, so the channel continues past the box instead of stopping.
    # The width is DERIVED rather than round — see skirt_margin_m(), T-0152.
    m, lattice_k = skirt_margin_m(max(e1 - e0, n1 - n0), cell)
    # Clockwise seen from above, each corner listed exactly once — a repeated
    # index here produces a degenerate quad, which from_pydata accepts and the
    # decimate modifier then segfaults on.
    ring_idx = ([r * cols for r in range(rows)]                              # west, S->N
                + [(rows - 1) * cols + c for c in range(1, cols)]            # north, W->E
                + [r * cols + cols - 1 for r in range(rows - 2, -1, -1)]     # east, N->S
                + [c for c in range(cols - 2, 0, -1)])                       # south, E->W
    assert len(set(ring_idx)) == len(ring_idx), "skirt ring visits a vertex twice"
    # WHERE THE APRON IS A SECTION OF SOMETHING THAT ENDS (T-0939). Carrying a
    # boundary vertex outward is right for ground that continues and wrong for a
    # landform the box has cut: the 1834 sand bar left this edge at +1.21 m and
    # was extruded 1.55 km south as a straight ribbon, three and a half times
    # longer than the island it is a section of, which is what the owner
    # photographed. skirt_terminations() reads which boundary vertices those are
    # and how far past the edge each one's landform actually reaches, off the
    # traced ring rather than off a number chosen to look right.
    #
    # The apron gains ONE more ring to say it with. Each boundary vertex has an
    # outward distance `t` and an arrival height: over a termination, its own
    # taper length and the water beside it; everywhere else, the deepest
    # termination on the box and its own carried height — which makes the extra
    # ring a subdivision of a flat strip and moves nothing. Where no landform is
    # truncated at all there is no extra ring, and this is the mesh it has always
    # been.
    ends = {}
    for name, runs in (terminations or {}).items():
        for run in runs:
            for k, i in enumerate(range(run["index0"], run["index0"] + len(run["extent_m"]))):
                idx = (0, i) if name == "south" else \
                      (rows - 1, i) if name == "north" else \
                      (i, 0) if name == "west" else (i, cols - 1)
                v = idx[0] * cols + idx[1]
                # A corner belongs to two edges. The shorter taper wins: it is
                # the one whose landform ends sooner on this vertex's own line.
                prior = ends.get(v)
                if prior is None or run["extent_m"][k] < prior[0]:
                    ends[v] = (run["extent_m"][k], run["base_y"][k])
    t_default = max((t for t, _ in ends.values()), default=0.0)

    outer = {}
    mid = {}
    eps = 0.5 * cell
    for i in ring_idx:
        e, n, y = verts[i]
        end = ends.get(i)
        y_out = end[1] if end else y
        if t_default > 0.0:
            t = end[0] if end else t_default
            mid[i] = len(verts)
            verts.append((e0 - t if e <= e0 + eps else (e1 + t if e >= e1 - eps else e),
                          n0 - t if n <= n0 + eps else (n1 + t if n >= n1 - eps else n),
                          y_out))
            confs.append(confs[i])
        oe = e0 - m if e <= e0 + eps else (e1 + m if e >= e1 - eps else e)
        on = n0 - m if n <= n0 + eps else (n1 + m if n >= n1 - eps else n)
        outer[i] = len(verts)
        verts.append((oe, on, y_out))
        confs.append(confs[i])
    # Wound so the skirt's normal points up, matching the grid above it: the
    # boundary runs clockwise from above, so the quad is a -> b -> outer_b ->
    # outer_a, not the other way round.
    for a, b in zip(ring_idx, ring_idx[1:] + ring_idx[:1]):
        if mid:
            faces.append((a, b, mid[b], mid[a]))
            faces.append((mid[a], mid[b], outer[b], outer[a]))
        else:
            faces.append((a, b, outer[b], outer[a]))
    if ends:
        print(f"skirt terminations: {len(ends)} boundary vertices stand on a landform the "
              f"box truncates; tapers {min(t for t, _ in ends.values()):.3f}..{t_default:.3f} m, "
              f"the apron elsewhere subdivided at {t_default:.3f} m and unmoved")

    rung = check_quantisation_lattice(verts, e0, e1, n0, n1, m, cell, lattice_k)
    print(f"skirt margin {m:.6f} m (grid cell / {lattice_k}); the publish step's "
          f"POSITION rung is {rung * 1000:.4f} mm and every ground vertex stands on one")

    ground = _emit(f"terrain__{epoch}", verts, faces, confs,
                   simple_material("terrain_ground", (0.36, 0.35, 0.22, 1.0), 1.0),
                   {"terrain_epoch": epoch, "layer": "ground"}, decimate_deg)
    fit = mesh_vs_field(ground, h_m, spec)
    print(f"ground mesh vs heightfield: max {fit['max_m'] * 1000:.0f} mm, "
          f"rms {fit['rms_m'] * 1000:.1f} mm over {fit['samples']:,} rays "
          f"({fit['misses']} misses)")
    if fit["max_m"] > MESH_FIT_TOLERANCE_M:
        raise SystemExit(
            f"REFUSING: the decimated ground mesh departs from the heightfield by "
            f"{fit['max_m'] * 1000:.0f} mm, over the {MESH_FIT_TOLERANCE_M * 1000:.0f} mm "
            f"tolerance. The walker's eye is pinned to the heightfield, so it would visibly "
            f"float or sink. Lower --decimate-deg.")
    ground_res = _export(ground, outdir / f"terrain__{epoch}.glb")
    ground_res["fit"] = fit
    results.append(ground_res)

    # ---- water ------------------------------------------------------------
    reset_scene()
    w = m + WATER_MARGIN_EXTRA_M
    wv = [(e0 - w, n0 - w, 0.0), (e1 + w, n0 - w, 0.0),
          (e1 + w, n1 + w, 0.0), (e0 - w, n1 + w, 0.0)]
    water = _emit(f"water__{epoch}", wv, [(0, 1, 2, 3)], [CONF_DOCUMENTED] * 4,
                  simple_material("terrain_water", (0.18, 0.24, 0.24, 1.0), 0.15),
                  {"terrain_epoch": epoch, "layer": "water"}, 0.0)
    results.append(_export(water, outdir / f"water__{epoch}.glb"))
    return results


def _emit(name, verts, faces, confs, material, extras, decimate_deg):
    import bpy  # noqa: PLC0415

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if me.validate(verbose=False):
        raise SystemExit(f"{name}: mesh failed validation — degenerate or duplicate faces")
    attr = me.attributes.new(name="_CONFIDENCE", type="FLOAT", domain="POINT")
    attr.data.foreach_set("value", confs)
    me.materials.append(material)
    for poly in me.polygons:
        poly.use_smooth = True

    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for k, v in extras.items():
        ob[k] = v

    bpy.context.view_layer.objects.active = ob
    if decimate_deg > 0:
        mod = ob.modifiers.new("planar", "DECIMATE")
        mod.decimate_type = "DISSOLVE"
        mod.angle_limit = math.radians(decimate_deg)
        mod.delimit = {"NORMAL"}
        bpy.ops.object.modifier_apply(modifier=mod.name)
    tri = ob.modifiers.new("tri", "TRIANGULATE")
    tri.min_vertices = 4
    bpy.ops.object.modifier_apply(modifier=tri.name)
    _face_the_sky(name, ob)
    return ob


# THE GROUND IS A HEIGHTFIELD, AND THAT IS A TESTABLE STATEMENT ABOUT EVERY FACE.
#
# Both surfaces this module emits are single-valued functions of (E, N): one
# height per plan position, by construction, with no overhangs and no vertical
# walls anywhere in the grid or the skirt. Seen from directly above, therefore,
# **every triangle must cover positive plan area and be wound counter-clockwise.**
# A face that covers zero plan area is standing on edge; a face wound the other
# way is facing the ground it is made of. Neither is terrain.
#
# The dissolve-plus-triangulate pass above produces a few of each, and it has
# since the decimation was added — T-0014 (was ROADMAP T-BUG2), banked as "79
# ground vertices face downward" and pinned by tools/smoke_renderer.mjs so the
# number could only fall. Measured on the shipped master 2026-08-23, the defect
# decomposes exactly, with nothing left over:
#
#   • 33 triangles wound BACKWARDS — plan area -3.125 to -25.0 m², ordinary
#     full-size ground triangles whose winding the n-gon triangulation reversed.
#     A vertex with only these as neighbours gets a normal pointing straight
#     down; one that also touches good faces gets a normal dragged toward the
#     horizon.
#   • 197 triangles standing EDGE-ON — plan area exactly 0.0: slivers in a
#     plane of constant E (91) or constant N (90), or three points collinear in
#     plan (16). They are the necks of keyholes the planar dissolve leaves in
#     its n-gons, which is also where the mesh's 15 one-triangle vertices come
#     from. They draw nothing from any direction that matters and they carry a
#     horizontal normal into whatever they touch.
#
# The classifier is not a tuned threshold, which is what makes this a repair
# rather than a mask: the grid puts every vertex on a 2.5 m lattice, so plan
# areas are multiples of half a cell, and the histogram has a clean gap either
# side of nothing — 197 faces at exactly 0.0 m², then the smallest honest
# triangle at 3.125 m². There is no third population and no judgement call.
#
# Deleting an edge-on face cannot open a hole in the ground, for the same reason
# it is being deleted: it covers no plan area, so the surface's vertical
# projection is unchanged. `mesh_vs_field()` is the instrument that says so out
# loud — it ray-casts the result against the heightfield from above and reports
# its misses, and it reports 0 of 28,890 after this pass as it did before.
#
# NOT FIXED BY CHANGING THE TRIANGULATOR, which was tried first and is the
# obvious move: `ngon_method="CLIP"` (ear clipping, robust on concave n-gons
# where BEAUTY is not) makes it WORSE — 42 backwards faces instead of 33 and
# 9,483 sub-mm² slivers instead of 188, measured on this same mesh. The
# triangulation Blender picks is not the thing to argue with; the invariant is.
def _face_the_sky(name, ob):
    """Delete edge-on faces and re-wind backwards ones. Returns nothing; refuses."""
    import bmesh  # noqa: PLC0415

    def plan_area(face):
        # Shoelace in Blender's own (x=E, y=N). Positive is counter-clockwise
        # from above, which is the winding the grid quads are authored with.
        co = [v.co for v in face.verts]
        return 0.5 * sum(a.x * b.y - b.x * a.y
                         for a, b in zip(co, co[1:] + co[:1]))

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    edge_on = [f for f in bm.faces if plan_area(f) == 0.0]
    backwards = [f for f in bm.faces if plan_area(f) < 0.0]
    for f in backwards:
        f.normal_flip()
    if edge_on:
        bmesh.ops.delete(bm, geom=edge_on, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    left = [f for f in bm.faces if plan_area(f) <= 0.0]
    if left:
        bm.free()
        raise SystemExit(
            f"REFUSING: {name} still has {len(left)} face(s) covering no plan area "
            f"after the heightfield repair. The surface is not single-valued and "
            f"something upstream of the triangulator changed.")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    print(f"{name}: faced the sky — re-wound {len(backwards)} backwards face(s), "
          f"dropped {len(edge_on)} edge-on face(s) and {len(loose)} vertex(es) "
          f"left loose by them")


def mesh_vs_field(ob, h_m, spec, stride=3):
    """Measure the ground mesh against the heightfield the WALKER samples.

    They are generated from the same grid, but the planar-dissolve pass that
    keeps the triangle count down is free to flatten anything whose face-pair
    angle is under the limit, and nothing about that bounds the accumulated
    error across a merged region. So it gets measured rather than argued about:
    a visitor whose eye is pinned to a heightfield the mesh does not match will
    see themselves float or sink, and that is exactly the failure this project
    should not ship.
    """
    from mathutils import Vector  # noqa: PLC0415
    from mathutils.bvhtree import BVHTree  # noqa: PLC0415

    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    g = spec["grid"]
    cell = float(g["cell_m"])
    e0, n0 = float(g["e_min_m"]), float(g["n_min_m"])
    rows, cols = h_m.shape
    down = Vector((0, 0, -1))
    worst, sq, n_hit, n_miss = 0.0, 0.0, 0, 0
    for r in range(0, rows, stride):
        n = n0 + r * cell
        for c in range(0, cols, stride):
            e = e0 + c * cell
            hit = bvh.ray_cast(Vector((e, n, 60.0)), down)
            if hit[0] is None:
                n_miss += 1
                continue
            d = abs(hit[0].z - float(h_m[r, c]))
            worst = max(worst, d)
            sq += d * d
            n_hit += 1
    rms = math.sqrt(sq / n_hit) if n_hit else 0.0
    return {"samples": n_hit, "misses": n_miss,
            "max_m": round(worst, 4), "rms_m": round(rms, 5)}


def _export(ob, out: Path):
    import bpy  # noqa: PLC0415

    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(
        filepath=str(out), export_format="GLB", use_selection=True,
        export_yup=True, export_apply=True,
        export_attributes=True, export_extras=True,
        export_cameras=False, export_lights=False, export_normals=True,
    )
    tris = len(ob.data.polygons)
    print(f"built {out.name}  {out.stat().st_size:,} bytes  {tris:,} tris  "
          f"{len(ob.data.vertices):,} verts")
    return {"path": out, "tris": tris, "verts": len(ob.data.vertices)}


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", default="e1834_harbor_cut")
    ap.add_argument("--glb", action="store_true", help="also build the GLBs (needs Blender)")
    ap.add_argument("--decimate-deg", type=float, default=0.03,
                    help="planar-dissolve angle limit for the ground mesh; 0 disables. "
                         "Picked by measurement, not taste: the loosest limit whose mesh "
                         "still tracks the heightfield inside MESH_FIT_TOLERANCE_M, and it "
                         "throws away two thirds of the triangles a plain grid would carry. "
                         "0.04 deg held that bound (16 mm max, 3 mm rms) until T-0118's "
                         "graded slough beds; against them it departs 34 mm, over the 30 mm "
                         "tolerance, and 0.03 tracks at 2 mm for 8 KB more GLB.")
    ap.add_argument("--out", default=str(ROOT / "assets" / "gltf"))
    args = ap.parse_args(argv_after_ddash())
    _unbuffer()

    if np is None:
        print("REFUSING: numpy is required (pip install numpy). Blender ships it.")
        return 2

    datum = load(ROOT / "data" / "datum.json")
    if not datum.get("verified"):
        print("REFUSING TO BUILD: data/datum.json is not verified.\n"
              "Fixing the origin after geometry exists means regenerating everything.\n"
              "See docs/EPOCHS.md and docs/RESEARCH/datum_derivation.md.")
        return 2

    ep_dir = ROOT / "data" / "terrain" / "epochs" / args.epoch
    spec = load(ep_dir / "terrain_spec.json")
    feats = {}
    for name in ("river.geojson", "hydrology.geojson", "shoreline.geojson",
                 "branches.geojson", "south_branch_below_twelfth.geojson",
                 "lake_shore_below_twelfth.geojson"):
        for f in load(ep_dir / name)["features"]:
            feats[f["id"]] = f
    origin = (datum["origin_utm_e"], datum["origin_utm_n"])

    h_m, conf, water, meta, geom = build_field(spec, feats, origin)
    audit = gradient_audit(h_m, water, geom, spec)
    audit["rule"] = ("docs/research/01-terrain-hydrology.md modelling rule 1: outside the zones "
                     "that earn relief, hold local gradients under 0.5 ft per 300 ft")
    meta["gradient_audit"] = audit

    # The apron's rule, written where the renderer can read it. Both sides of
    # the bake have to carry a boundary vertex outward the same way or the seam
    # at the box edge opens, and since T-0939 that rule has a data half: which
    # boundary vertices stand on a landform the box truncates, and how far out
    # each one's own trace reaches. Publishing it here is what keeps
    # renderers/web/js/terrain.js's conformGroundToField() from having to know
    # about islands, or to drift away from this generator's answer.
    _g = spec["grid"]
    _margin, _k = skirt_margin_m(max(float(_g["e_max_m"]) - float(_g["e_min_m"]),
                                     float(_g["n_max_m"]) - float(_g["n_min_m"])),
                                 float(_g["cell_m"]))
    _rung = float(_g["cell_m"]) / _k
    meta["skirt"] = {
        "_doc": "The apron outside the modelled box. It carries each boundary vertex "
                "outward at its own height, EXCEPT over a landform whose traced outline "
                "ends inside the apron: there the ground falls from the boundary height "
                "to base_y, reaching it at extent_m and holding it beyond. Indices run "
                "along the named edge — columns from the west on south/north, rows from "
                "the south on west/east. See generators/terrain_gen.skirt_terminations "
                "and T-0939.",
        "margin_m": round(_margin, 6),
        "position_rung_m": round(_rung, 9),
        "terminations": skirt_terminations(spec, feats, origin, h_m, _rung),
    }

    sha = terrain_inputs_sha(ep_dir)
    doc = write_heightfield(ep_dir, h_m, meta, spec, sha)

    bx, bn = meta["box"]["e"], meta["box"]["n"]
    print(f"grid {doc['cols']}x{doc['rows']} @ {doc['cell_m']} m  "
          f"(E {bx[0]:+.0f}..{bx[1]:+.0f}, N {bn[0]:+.0f}..{bn[1]:+.0f} — "
          f"{bx[1] - bx[0]:.0f} x {bn[1] - bn[0]:.0f} m)")
    print(f"relief: land {meta['land_min_ft']:+.2f} .. {meta['land_max_ft']:+.2f} ft, "
          f"channel floor {meta['min_m'] / FT:+.2f} ft; water covers "
          f"{100 * meta['water_fraction']:.1f}% of the box")
    print(f"quantisation error {doc['quantisation_error_m'] * 1000:.2f} mm "
          f"(dossier asks for <= 0.25 ft = 76 mm)")
    ga = meta["gradient_audit"]
    print(f"gradient audit (fall across a 300 ft chord): plain max {ga['plain_block_max']} ft "
          f"(mean {ga['plain_block_mean']}) — {'PASS' if ga['passes'] else 'OVER THE 0.5 RULE'}; "
          f"plain cell roughness {ga['plain_cell_roughness_max']}, "
          f"shore and swales {ga['shore_and_swale_cell_max']}")
    print(f"wrote {(ep_dir / 'heightfield.bin').relative_to(ROOT)} "
          f"({(ep_dir / 'heightfield.bin').stat().st_size:,} bytes)")

    if not args.glb:
        print("\nheightfield only; re-run under Blender with --glb for the meshes")
        return 0
    if not HAVE_BPY:
        print("\n--glb asked for but bpy is not importable. Run:\n"
              "  blender -b -noaudio --factory-startup --python generators/terrain_gen.py "
              "-- --glb")
        return 2

    built = build_meshes(h_m, conf, spec, args.epoch, Path(args.out),
                         args.decimate_deg, meta.get("skirt", {}).get("terminations"))

    manifest_path = ROOT / "assets" / "manifest.json"
    manifest = load(manifest_path) if manifest_path.exists() else {}
    manifest.setdefault("assets", {})
    manifest["blender"] = bpy.app.version_string.split()[0]
    # Terrain and structures share one manifest and therefore one declaration of
    # what its hashes mean; see generators/mesh_inputs.py.
    from mesh_inputs import SCHEME  # noqa: PLC0415

    manifest["inputs_scheme"] = SCHEME
    for b in built:
        p: Path = b["path"]
        manifest["assets"][p.name] = {
            "kind": "generated",
            "generator": "generators/terrain_gen.py",
            "terrain_epoch": args.epoch,
            "layer": "water" if p.name.startswith("water__") else "ground",
            "inputs_sha256": sha,
            "bytes": p.stat().st_size,
            "triangles": b["tris"],
            **({"mesh_vs_heightfield": b["fit"]} if "fit" in b else {}),
            "baked_ao": False,
        }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"\nmanifest updated: {len(built)} terrain asset(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
