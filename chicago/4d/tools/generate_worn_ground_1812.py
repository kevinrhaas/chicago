#!/usr/bin/env python3
"""Generate the worn paths, trails and worn yards of the 1812 scene (T-3339).

    python3 tools/generate_worn_ground_1812.py            write the records
    python3 tools/generate_worn_ground_1812.py --check    re-derive and diff, write nothing

WHY THIS EXISTS. The owner, 2026-11-03: *"in 1812 I get that there are not formal roads but I
would expect worn paths almost roads from the fort entrance and even out south, I thought there
was the road to Vincennes, so can you add natural worn paths and worn areas around the buildings
that would be sensible and paths connecting, vary them based on density and some can be very
light"*, and *"do whatever research you can to make them accurate and don't overdo it but be
sensible and logical and make it look natural"*. The 1812 ground was one unbroken sward from
the fort's gate to the box's edge: no trace of a garrison of some seventy men, a trading
family's horses and carts, or the trails that brought the Potawatomi and the traders in.

WHAT THE SOURCES SAY, and so what is drawn (every one is `existence` on its trail):

  * THE LAKE-SHORE TRAIL. Andreas (1884, v1, the evacuation of 15 August 1812): "Along the lake
    shore ran a beaten Indian trail, which was the path pursued", with the sand hills "at about
    one hundred yards distance" west of it. Currey (1912): "The line of march lay along the
    shore of the lake toward the south. In the absence of roads ... the margin of the lake was
    usually preferred". Quaife (1923, ch. II): the Chicago road from Detroit "followed the beach
    the remaining sixty miles to Chicago". ATTESTED that it existed; its line is the committed
    evacuation route's (data/terrain/1812_evacuation_route.geojson) set a little inland of the
    waterline it is drawn on.
  * THE VINCENNES TRACE. Quaife (1923, ch. III): the trail from the Wabash to Chicago was an
    ancient Potawatomi thoroughfare; Heald rode up it with his bride in 1811 and the Wabash
    bands "hastened northward ... along the ancient trail" in August 1812; it was Hubbard's
    trail, and the State road of 1834 "was forced to follow the old track". INFERRED that it
    reached the fort; its line south of the outlet is the 1835 scene's reconstructed State road
    (data/streets/1835.json `state_road_south`, L381), so the land reads the same in both years.
  * THE SOUTH-BANK PATH TO THE FORKS AND UP THE SOUTH BRANCH. Currey (1912), the Lee's Place
    attack of April 1812: the discharged soldier and the boy crossed to the east side, "made a
    run for the woods ... and directed their course toward the fort", and "did not slacken their
    speed until they had reached the river somewhere near the present location of State Street
    bridge", calling across to Burns, and ran on to the fort. Andreas: the Hardscrabble cabin
    "stood near the most frequented trail that led to the Desplaines". Whistler's 1808 draught
    and Quaife (1913) put the company cornfield and a house at the forks. INFERRED.
  * THE NORTH-BANK PATH, KINZIE'S TO BURNS'S. Currey (1912): Mrs. Kinzie, at the Burns house,
    "ran to her own home, a quarter of a mile distant". INFERRED.
  * LEE'S PLACE TO ITS CANOES. Currey (1912): the soldier "walked ... down the path toward the
    canoes tied up at the river bank". ATTESTED.
  * THE GARRISON'S OWN WAYS, gate to wharf, to the stables, the agency, the gardens and the
    shops, and the Kinzie house to its landing (Wau-Bun: the pirogues "kept moored near the
    house"). No source draws one; that people walked between the doors a source places is
    this project's reading. RECONSTRUCTED.

THE RULE, so that nothing here is a hand-drawn line: each path is the least-cost route over the
committed 1812 ground (data/terrain/epochs/e1830_natural/heightfield.json, and the South Branch
apron past the box's south edge) between two derived end points (a door, a landing, a junction
on another path, a waypoint read off a source line), where:
  - open water costs a ford (a path may cross a creek, never run down a river) and a structure's
    footprint, its garden and the fort's own ground are not crossed at all;
  - low wet ground costs more than dry (a trail keeps to "the most favorable ground", Hubbard's
    own words for the State road's commissioners);
  - a path that follows a bank prefers to keep a stated distance from the water.
The route is then smoothed and given a slow lateral wander, sized by the path's form, so it
meanders the way a trodden line across grass does, and pinned at both ends. Every alignment is
`reconstructed`; docs/LIBERTIES.md L-t3339-worn-ground-1812 owns the rule, the costs, the wear
figures and the yards.

THE WORN YARDS. Each building that people and stock came and went from carries a ring of
trodden or hoof-worn earth: the convex hull of its footprint pushed out a few metres, feathered
into the sward by renderers/web/js/yards.js. `wear` (0..1) scales how bare it is. A garden is
never worn, and the Kinzie house keeps the "broad green space" Wau-Bun puts between it and the
river: its yard is behind the house only.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "enclosures" / "1812"
SIDECARS = DATA / "sidecars" / "1812"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_fort_parade_ground import _to_enu, _point_in_ring  # noqa: E402

TICKET = "T-3339"
LIBERTY = "L-t3339-worn-ground-1812"
SCENE_DATE = "1812-08-14"
TRAILS_ID = "worn_trails_1812"
TRAILS_FILE = f"{TRAILS_ID}.json"

GRID_M = 5.0          # the route grid; fine enough for a footpath on a plain this flat
JOIN_COST = 0.4       # walking an already-worn line costs this share of open grass (T-3512)
WET_Y = 0.75          # ground under this height above the lake is the low wet prairie
WATER_Y = -0.10       # terrain.js SHORE_Y: below it the renderer calls the ground water

# --------------------------------------------------------------------------------------------
# the ground
# --------------------------------------------------------------------------------------------


def _raster(meta_path: Path) -> tuple[dict, np.ndarray]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    raw = np.fromfile(meta_path.parent / meta["bin"], dtype="<i2").astype(np.float64)
    return meta, (raw * meta["scale"] + meta.get("offset", 0.0)).reshape(meta["rows"], meta["cols"])


EPOCH = DATA / "terrain" / "epochs" / "e1830_natural"
BOX_META, BOX = _raster(EPOCH / "heightfield.json")
APRON_META, APRON = _raster(EPOCH / "apron_south_branch.json")


def _bilinear(meta: dict, grid: np.ndarray, e: np.ndarray, n: np.ndarray) -> np.ndarray:
    c = (e - meta["origin_e"]) / meta["cell_m"]
    r = (n - meta["origin_n"]) / meta["cell_m"]
    c = np.clip(c, 0, meta["cols"] - 1.000001)
    r = np.clip(r, 0, meta["rows"] - 1.000001)
    c0 = np.floor(c).astype(int)
    r0 = np.floor(r).astype(int)
    fc = c - c0
    fr = r - r0
    return (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
            + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)


def height(e, n):
    """The committed ground at (e, n): the box, or the South Branch apron south of it."""
    e = np.asarray(e, dtype=np.float64)
    n = np.asarray(n, dtype=np.float64)
    box = BOX_META["box_local_enu_m"]
    apr = APRON_META["box_local_enu_m"]
    in_box = (e >= box["e"][0]) & (e <= box["e"][1]) & (n >= box["n"][0]) & (n <= box["n"][1])
    in_apron = (e >= apr["e"][0]) & (e <= apr["e"][1]) & (n >= apr["n"][0]) & (n < apr["n"][1])
    out = np.full(e.shape, np.nan)
    if in_box.any():
        out[in_box] = _bilinear(BOX_META, BOX, e[in_box], n[in_box])
    sel = in_apron & ~in_box
    if sel.any():
        out[sel] = _bilinear(APRON_META, APRON, e[sel], n[sel])
    return out


# --------------------------------------------------------------------------------------------
# the structures and what a path may not cross
# --------------------------------------------------------------------------------------------


def _sidecar(sid: str) -> dict:
    return json.loads((SIDECARS / f"{sid}.json").read_text(encoding="utf-8"))


def footprint(sid: str) -> list[list[float]]:
    d = _sidecar(sid)
    place = d["placement"]
    poly = (d.get("footprint") or {}).get("polygon") or []
    return [list(_to_enu(u, v, place)) for u, v in poly]


def centre(ring) -> tuple[float, float]:
    return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))


def _all_footprints() -> dict[str, list]:
    out = {}
    for path in sorted(SIDECARS.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or "placement" not in d:
            continue
        if not (d.get("footprint") or {}).get("polygon"):
            continue
        out[path.stem] = footprint(path.stem)
    return out


FOOTPRINTS = _all_footprints()
# What no path or yard may lie on: every footprint but the fort's own interior pieces (a path
# ends AT the fort's gate; the stockade's footprint covers everything inside it) and the
# camp records, which are open ground whose own extents are the camp's.
GARDENS = ("first_fort_outer_officers_garden", "first_fort_outer_sutlers_garden",
           "kinzie_garden_1812", "forks_company_cornfield_1812", "coursoll_field_1812")


def _grow(ring, d):
    """A ring pushed out d metres about its centre, corner for corner (the footprints are
    rectangles, so this is their offset to well inside a centimetre)."""
    cx, cy = centre(ring)
    out = []
    for x, y in ring:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        k = (L + d * math.sqrt(2)) / L if len(ring) == 4 else (L + d) / L
        out.append([cx + dx * k, cy + dy * k])
    return out


def _bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), max(xs), min(ys), max(ys)


def obstacles(grow_m: float = 1.2) -> list[tuple[str, list, tuple]]:
    obs = []
    for sid, ring in FOOTPRINTS.items():
        if sid.startswith("potawatomi_camp"):
            continue
        if sid.startswith("first_fort_dearborn_") and sid != "first_fort_dearborn_pickets_outer":
            continue
        if sid.startswith("lees_place_haystack"):
            continue
        g = _grow(ring, grow_m)
        obs.append((sid, g, _bbox(g)))
    return obs


# What a finished line is held to (1.2 m clear of every footprint) and what the router steers
# by (3.5 m clear, so the smoothing and the wander cannot carry a line back onto a building).
OBSTACLES = obstacles()
ROUTE_OBSTACLES = obstacles(3.5)


def _planted_stems() -> list[tuple[str, float, float]]:
    """Every TREE a 1812 planting record stands (the shore cottonwoods, the massacre saplings,
    Kinzie's poplars): a trail goes round a recorded tree, never under it, or the planter
    would refuse the tree for standing on the travelled track."""
    out = []
    for path in sorted((ROOT / "data/flora/plantings").glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if str(r.get("scene")) != "1812":
            continue
        for st in r.get("stems", []):
            if float(st.get("height_m", 0)) >= 3.0:
                e, n = st["at_local_enu_m"]
                out.append((f"{r['id']}/{st['id']}", float(e), float(n)))
    return out


PLANTED = _planted_stems()
STEM_ROUTE_CLEAR_M = 4.5   # the router's berth round a planted tree
STEM_CLEAR_M = 1.2         # what a finished line's edge is held to, past its half-width


def blocked(e: float, n: float, allow: tuple = ()) -> str | None:
    for sid, ring, (x0, x1, y0, y1) in OBSTACLES:
        if sid in allow:
            continue
        if x0 <= e <= x1 and y0 <= n <= y1 and _point_in_ring(ring, e, n):
            return sid
    return None


# --------------------------------------------------------------------------------------------
# the route
# --------------------------------------------------------------------------------------------


def _water_distance(water: np.ndarray, cap_cells: int) -> np.ndarray:
    """Cells' distance to the nearest water cell, in cells, by repeated 8-neighbour dilation
    (a chamfer that slightly overstates diagonals; the bank preference is a soft one)."""
    dist = np.where(water, 0.0, np.inf)
    front = water.copy()
    for k in range(1, cap_cells + 1):
        grown = front.copy()
        grown[1:, :] |= front[:-1, :]
        grown[:-1, :] |= front[1:, :]
        grown[:, 1:] |= front[:, :-1]
        grown[:, :-1] |= front[:, 1:]
        grown[1:, 1:] |= front[:-1, :-1]
        grown[:-1, :-1] |= front[1:, 1:]
        grown[1:, :-1] |= front[:-1, 1:]
        grown[:-1, 1:] |= front[1:, :-1]
        new = grown & ~front
        dist[new] = k
        front = grown
    return dist


def route(a, b, *, bank_m=None, ford=True, margin_m=260.0, allow=(), via_box=None, extra=(),
          join=()):
    """The least-cost route from a to b on the GRID_M lattice (A*), as local ENU points.
    `extra` is more (sid, ring, bbox) obstacles for this route alone (T-3512: the camp
    grounds a camp path is not bound for). `join` is lines already worn: walking on one is
    cheaper (JOIN_COST), and the route ENDS where it first reaches one, so a new path runs
    into an old one the way a desire line does instead of being drawn beside it."""
    e0 = min(a[0], b[0]) - margin_m
    e1 = max(a[0], b[0]) + margin_m
    n0 = min(a[1], b[1]) - margin_m
    n1 = max(a[1], b[1]) + margin_m
    if via_box:
        e0, e1 = min(e0, via_box[0]), max(e1, via_box[1])
        n0, n1 = min(n0, via_box[2]), max(n1, via_box[3])
    cols = int(math.ceil((e1 - e0) / GRID_M)) + 1
    rows = int(math.ceil((n1 - n0) / GRID_M)) + 1
    E = e0 + np.arange(cols) * GRID_M
    N = n0 + np.arange(rows) * GRID_M
    EE, NN = np.meshgrid(E, N)
    H = height(EE.ravel(), NN.ravel()).reshape(rows, cols)
    off = np.isnan(H)
    water = (H < WATER_Y) & ~off
    cost = np.ones((rows, cols))
    cost += np.clip((WET_Y - np.nan_to_num(H, nan=WET_Y)) / WET_Y, 0, 1) * 1.6
    if bank_m:
        dw = _water_distance(water, int(2.5 * bank_m / GRID_M) + 2) * GRID_M
        dev = (np.minimum(dw, 2.5 * bank_m) - bank_m) / bank_m
        cost += 2.2 * dev * dev
    cost[water] = 45.0 if ford else np.inf
    cost[off] = np.inf
    for sid, ring, (x0, x1, y0, y1) in list(ROUTE_OBSTACLES) + list(extra):
        if sid in allow or x1 < e0 or x0 > e1 or y1 < n0 or y0 > n1:
            continue
        c0 = max(0, int((x0 - e0) / GRID_M) - 1)
        c1 = min(cols - 1, int((x1 - e0) / GRID_M) + 1)
        r0 = max(0, int((y0 - n0) / GRID_M) - 1)
        r1 = min(rows - 1, int((y1 - n0) / GRID_M) + 1)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if _point_in_ring(ring, E[c], N[r]):
                    cost[r, c] = np.inf

    for _sid, se, sn in PLANTED:
        if se < e0 - 10 or se > e1 + 10 or sn < n0 - 10 or sn > n1 + 10:
            continue
        near = (EE - se) ** 2 + (NN - sn) ** 2 <= STEM_ROUTE_CLEAR_M ** 2
        cost[near] = np.inf

    def cell(p):
        return (int(round((p[1] - n0) / GRID_M)), int(round((p[0] - e0) / GRID_M)))

    on_join = np.zeros((rows, cols), dtype=bool)
    for line in join:
        for (x0_, y0_), (x1_, y1_) in zip(line[:-1], line[1:]):
            k = max(1, int(math.hypot(x1_ - x0_, y1_ - y0_) / 1.5))
            for j in range(k + 1):
                r_, c_ = cell((x0_ + (x1_ - x0_) * j / k, y0_ + (y1_ - y0_) * j / k))
                on_join[max(0, r_ - 1):max(0, r_ + 2), max(0, c_ - 1):max(0, c_ + 2)] = True
    cost[on_join & np.isfinite(cost)] *= JOIN_COST

    start, goal = cell(a), cell(b)
    cost[start] = min(cost[start], 1.0) if np.isfinite(cost[start]) else 1.0
    cost[goal] = min(cost[goal], 1.0) if np.isfinite(cost[goal]) else 1.0
    INF = float("inf")
    g = np.full((rows, cols), INF)
    came = np.full((rows, cols), -1, dtype=np.int64)
    g[start] = 0.0
    heap = [(0.0, start)]
    steps = [(-1, -1, 1.4142), (-1, 0, 1.0), (-1, 1, 1.4142), (0, -1, 1.0), (0, 1, 1.0),
             (1, -1, 1.4142), (1, 0, 1.0), (1, 1, 1.4142)]
    gr, gc = goal
    while heap:
        f, (r, c) = heapq.heappop(heap)
        if (r, c) == goal:
            break
        gcur = g[r, c]
        if f - math.hypot(r - gr, c - gc) > gcur + 1e-9:
            continue
        for dr, dc, w in steps:
            rr, cc = r + dr, c + dc
            if rr < 0 or cc < 0 or rr >= rows or cc >= cols:
                continue
            k = cost[rr, cc]
            if k == INF:
                continue
            ng = gcur + w * 0.5 * (cost[r, c] + k)
            if ng < g[rr, cc]:
                g[rr, cc] = ng
                came[rr, cc] = r * cols + c
                heapq.heappush(heap, (ng + math.hypot(rr - gr, cc - gc), (rr, cc)))
    if g[goal] == INF:
        raise SystemExit(f"WORN GROUND: no route from {a} to {b}")
    path = []
    cur = goal
    while True:
        path.append((E[cur[1]], N[cur[0]]))
        if cur == start:
            break
        k = came[cur]
        cur = (int(k // cols), int(k % cols))
    path.reverse()
    if join:
        # end at the first cell on a worn line, past the route's first few metres
        for i in range(2, len(path)):
            if on_join[cell(path[i])]:
                end = path[i]
                line = min(join, key=lambda L: math.dist(nearest_on(L, end), end))
                return [list(a)] + [list(p) for p in path[1:i]] + [nearest_on(line, end)]
    pts = [list(a)] + [list(p) for p in path[1:-1]] + [list(b)]
    return pts


# --------------------------------------------------------------------------------------------
# shaping a route into a trodden line
# --------------------------------------------------------------------------------------------


def _dp(pts, tol):
    """Douglas-Peucker: the grid's stair steps out, the route's bends in."""
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0]), np.array(pts[-1])
    ab = b - a
    L = np.hypot(*ab) or 1e-9
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        p = np.array(pts[i])
        d = abs(ab[0] * (a[1] - p[1]) - ab[1] * (a[0] - p[0])) / L
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return _dp(pts[: idx + 1], tol)[:-1] + _dp(pts[idx:], tol)


def _chaikin(pts, rounds=3):
    for _ in range(rounds):
        out = [pts[0]]
        for p, q in zip(pts[:-1], pts[1:]):
            out.append([0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]])
            out.append([0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]])
        out.append(pts[-1])
        pts = out
    return pts


def _resample(pts, step):
    seg = [math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts[:-1], pts[1:])]
    total = sum(seg)
    k = max(1, int(round(total / step)))
    out = []
    i, acc = 0, 0.0
    for j in range(k + 1):
        s = total * j / k
        while i < len(seg) - 1 and acc + seg[i] < s:
            acc += seg[i]
            i += 1
        t = 0.0 if seg[i] == 0 else min(1.0, max(0.0, (s - acc) / seg[i]))
        p, q = pts[i], pts[i + 1]
        out.append([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t])
    return out, total


def _wander(pts, amp, seed):
    """A slow lateral meander, zero at both ends, so a trodden line does not read as a rule."""
    if amp <= 0 or len(pts) < 3:
        return pts
    s = [0.0]
    for p, q in zip(pts[:-1], pts[1:]):
        s.append(s[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    total = s[-1]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p, q = pts[i - 1], pts[i + 1]
        tx, ty = q[0] - p[0], q[1] - p[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        env = min(1.0, s[i] / 25.0, (total - s[i]) / 25.0)
        w = (0.6 * math.sin(s[i] / 47.0 + seed) + 0.3 * math.sin(s[i] / 19.0 + 2.1 * seed)
             + 0.1 * math.sin(s[i] / 7.3 + 3.7 * seed))
        out.append([pts[i][0] + nx * amp * env * w, pts[i][1] + ny * amp * env * w])
    out.append(pts[-1])
    return out


FORM = {
    # half-width of the worn core, metres; the wander's amplitude
    "tread": {"wander": 1.4},
    "two_track": {"wander": 0.9},
    "band": {"wander": 0.8},
}


def shape(raw, form, seed, step=3.0):
    pts = _dp(raw, GRID_M * 0.55)
    pts = _chaikin(pts, 3)
    pts, _ = _resample(pts, step)
    pts = _wander(pts, FORM[form]["wander"], seed)
    pts = _skirt(pts, HALF_WIDTH[form] + STEM_CLEAR_M + 0.35)
    return [[round(p[0], 2), round(p[1], 2)] for p in pts]


# The widest half-width each form is drawn at (paths() sets the widths), for the berth a
# finished line keeps round a planted tree.
HALF_WIDTH = {"tread": 0.5, "two_track": 1.2, "band": 0.7}
SKIRT_EASE_M = 6.0


def _skirt(pts, reach):
    """Bend a finished line round every planted tree it passes within `reach` of, the way a
    path goes round a trunk: the nearest point is pushed out to `reach` and the push eases
    off along the line over SKIRT_EASE_M either side. The ends never move (they are doors
    and gates)."""
    pts = [list(p) for p in pts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    near = [(se, sn) for _sid, se, sn in PLANTED
            if min(xs) - reach - 10 <= se <= max(xs) + reach + 10
            and min(ys) - reach - 10 <= sn <= max(ys) + reach + 10]
    if not near:
        return pts
    for _ in range(6):
        moved = False
        # put a vertex at each segment's closest approach, so a chord cannot cut the berth
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy
            ins = []
            for se, sn in near:
                if L2 == 0:
                    continue
                t = ((se - a[0]) * dx + (sn - a[1]) * dy) / L2
                if 0.08 < t < 0.92 and _seg_dist(se, sn, a, b) < reach:
                    ins.append((t, [a[0] + t * dx, a[1] + t * dy]))
            out.extend(q for _t, q in sorted(ins))
            out.append(b)
        pts = out
        arc = [0.0]
        for a, b in zip(pts[:-1], pts[1:]):
            arc.append(arc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        for se, sn in near:
            push = None
            for i in range(1, len(pts) - 1):
                d = math.hypot(pts[i][0] - se, pts[i][1] - sn)
                if d < reach and (push is None or d < push[1]):
                    push = (i, d)
            if push is None:
                continue
            i, d = push
            ux, uy = pts[i][0] - se, pts[i][1] - sn
            L = math.hypot(ux, uy) or 1.0
            k = reach - d + 0.05
            vx, vy = ux / L * k, uy / L * k
            for j in range(1, len(pts) - 1):
                w = 1.0 - abs(arc[j] - arc[i]) / SKIRT_EASE_M
                if w > 0:
                    pts[j][0] += vx * w
                    pts[j][1] += vy * w
            moved = True
        if not moved:
            break
    return pts


def _seg_dist(px, py, a, b):
    """Distance from (px, py) to the segment a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))


def length(pts):
    return sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts[:-1], pts[1:]))


def nearest_on(line, p):
    best = None
    for a, b in zip(line[:-1], line[1:]):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        q = [ax + dx * t, ay + dy * t]
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        if best is None or d < best[0]:
            best = (d, q)
    return best[1]


def door(sid, toward, out_m=1.6):
    """The point just outside a building's footprint on the side facing `toward`."""
    ring = FOOTPRINTS[sid]
    cx, cy = centre(ring)
    dx, dy = toward[0] - cx, toward[1] - cy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    # march out from the centre until clear of the grown footprint
    grown = _grow(ring, 1.25)
    t = 0.0
    while _point_in_ring(grown, cx + ux * t, cy + uy * t):
        t += 0.25
    return [cx + ux * (t + out_m), cy + uy * (t + out_m)]


# --------------------------------------------------------------------------------------------
# the derived end points
# --------------------------------------------------------------------------------------------


def _datum():
    d = json.loads((DATA / "datum.json").read_text(encoding="utf-8"))
    return d["origin_utm_e"], d["origin_utm_n"]


def evacuation_line():
    oe, on = _datum()
    g = json.loads((DATA / "terrain" / "1812_evacuation_route.geojson").read_text(encoding="utf-8"))
    f = next(x for x in g["features"] if x.get("id") == "evacuation_route_1812")
    return [[x - oe, y - on] for x, y in f["geometry"]["coordinates"]]


def state_road_line():
    d = json.loads((DATA / "streets" / "1835.json").read_text(encoding="utf-8"))
    s = next(x for x in d["streets"] if x["id"] == "state_road_south")
    return s["path_local_enu_m"]


OUTER = json.loads((SIDECARS / "first_fort_dearborn_pickets_outer.json").read_text(encoding="utf-8"))
_PO = FOOTPRINTS["first_fort_dearborn_pickets_outer"]
# The main gate in the outer row's south side, at the archetype's gate_offset_m from its centre
# (fort-gates.js / T-3319): the walk out of it starts 2.5 m south of the pickets.
GATE_OFFSET_M = -2.83
_x0, _x1, _y0, _y1 = _bbox(_PO)
GATE = [round((_x0 + _x1) / 2 + GATE_OFFSET_M, 2), round(_y0 - 2.5, 2)]


def inland(line, metres, lo_n=None, hi_n=None):
    """Each vertex of a waterline set `metres` inland (west, toward higher ground), clamped dry."""
    out = []
    for p in line:
        if (lo_n is not None and p[1] < lo_n) or (hi_n is not None and p[1] > hi_n):
            continue
        e = p[0] - metres
        while height(e, p[1]) < 0.25 and e > p[0] - 4 * metres:
            e -= 2.0
        out.append([e, p[1]])
    return out


# --------------------------------------------------------------------------------------------
# the paths
# --------------------------------------------------------------------------------------------

SRC = {
    "andreas": "andreas_1884_v1",
    "currey": "currey_1912_story_of_old_fort_dearborn",
    "quaife23": "quaife_1923_chicagos_highways",
    "quaife13": "quaife_1913",
    "waubun": "kinzie_waubun_1856",
    "whistler": "whistler_1808_fort_dearborn_draught",
    "hubbard": "hubbard_autobiography_1911",
}


def paths():
    out = []
    evac = evacuation_line()
    lee = FOOTPRINTS["lee_house_1812"]
    lee_c = centre(lee)

    # 1. The fort's road south: out of the main gate and down the old channel's west bank to the
    #    Lee house at the outlet, where the lake-shore trail and the Vincennes trace part.
    lee_door = door("lee_house_1812", (lee_c[0] + 20, lee_c[1] + 30))
    fork = [lee_door[0] + 18.0, lee_door[1] - 22.0]
    road_raw = route(GATE, fork, bank_m=32.0, ford=False,
                     allow=("first_fort_dearborn_pickets_outer",))
    road = shape(road_raw, "two_track", 0.7)
    out.append({
        "id": "fort_road_south_1812",
        "name": "The fort's road south, from the main gate down the river to the outlet",
        "form": "two_track", "width_m": 2.4, "wear": 0.85, "treatment": "trodden_earth",
        "existence": {"confidence": "inferred", "sources": [SRC["andreas"], SRC["currey"]],
                      "note": "The evacuation column of 15 August 1812 - soldiers, a 'train of wagons' with the women and children, two officers' wives on horseback (Currey) - went this way out of the gate to the lake shore, and the beaten trail it took (Andreas) left from here. A garrison's carts, the Lee family's and the traders' traffic to the outlet would have worn it into a two-rut track."},
        "alignment": "reconstructed: the least-cost route from the gate to the Lee house, keeping about 32 m back from the old channel's west bank",
        "line_local_enu_m": road,
    })

    # 2. The lake-shore trail: from the fork, out to the beach and south along it, the
    #    evacuation route's own line set 18 m inland of the waterline it is drawn on.
    beach = [p for p in evac if p[1] < -600]
    beach_in = inland(beach, 18.0)
    shore_raw = [fork] + route(fork, beach_in[0], ford=False, margin_m=120)[1:] + beach_in[1:]
    shore = shape(shore_raw, "tread", 1.3, step=4.0)
    out.append({
        "id": "lake_shore_trail_1812",
        "name": "The beaten Indian trail along the lake shore, south toward Fort Wayne and Detroit",
        "form": "tread", "width_m": 1.0, "wear": 0.5, "treatment": "trodden_earth",
        "existence": {"confidence": "attested", "sources": [SRC["andreas"], SRC["currey"], SRC["quaife23"]],
                      "note": "Andreas: 'Along the lake shore ran a beaten Indian trail, which was the path pursued', the sand hills about a hundred yards west of it. Quaife (1923): the road from Detroit 'followed the beach the remaining sixty miles to Chicago'. On sand the tread shows faintly."},
        "alignment": "reconstructed: the committed evacuation route (data/terrain/1812_evacuation_route.geojson) set 18 m inland of the waterline it follows, so the tread runs on the dry upper beach",
        "line_local_enu_m": shore,
    })

    # 3. The Vincennes trace: from the fork south on the sand plain, joining the 1835 State
    #    road's reconstructed line where it leaves the outlet's ground and following it south.
    sr = state_road_line()
    join = next(p for p in sr if p[1] <= -890)
    tail = [p for p in sr if p[1] < join[1]]
    trace_raw = route(fork, join, ford=False, margin_m=160) + tail
    trace = shape(trace_raw, "tread", 2.3, step=4.0)
    out.append({
        "id": "vincennes_trace_1812",
        "name": "The Vincennes trace, the Potawatomi trail south to the Wabash",
        "form": "tread", "width_m": 0.9, "wear": 0.7, "treatment": "trodden_earth",
        "existence": {"confidence": "inferred", "sources": [SRC["quaife23"], SRC["hubbard"]],
                      "note": "Quaife (1923, ch. III): an ancient Potawatomi thoroughfare from Lake Michigan to the Wabash; Captain Heald rode up it with his bride in the spring of 1811, and in August 1812 the Wabash bands 'hastened northward with utmost speed along the ancient trail'. It became Hubbard's trail and, in 1834, the State road, which 'was forced to follow the old track'. Latrobe (1833, in Andreas) on such a trail near Chicago: 'the deep, black, narrow trail'."},
        "alignment": "reconstructed: from the fork at the outlet, the least-cost route to the 1835 scene's reconstructed State road (data/streets/1835.json state_road_south, L381) and that line south to the box's edge, so the undeveloped land reads the same in 1812 and 1835",
        "line_local_enu_m": trace,
    })

    # 4. The south-bank path west to the forks: from the agency's houses along the main stem's
    #    south bank to the Clark house at the forks.
    agent = FOOTPRINTS["first_fort_outer_agents_house"]
    clark_c = centre(FOOTPRINTS["forks_house_clark_1812"])
    a4 = door("first_fort_outer_interpreters_house", (0, 0))
    b4 = door("forks_house_clark_1812", (clark_c[0] + 2.0, clark_c[1] + 100.0))
    sb_raw = route(a4, b4, bank_m=28.0, ford=True, margin_m=220)
    sb = shape(sb_raw, "tread", 2.6, step=3.0)
    out.append({
        "id": "south_bank_path_1812",
        "name": "The path along the river's south bank, from the agency to the forks",
        "form": "tread", "width_m": 0.8, "wear": 0.45, "treatment": "trodden_earth",
        "existence": {"confidence": "inferred", "sources": [SRC["currey"], SRC["whistler"], SRC["quaife13"]],
                      "note": "Currey (1912): the man and boy escaping Lee's Place in April 1812 ran 'toward the fort' and 'reached the river somewhere near the present location of State Street bridge', calling across to Burns, then ran on along the bank to the fort. Whistler's draught and Quaife (1913) put the company cornfield and a house at the forks, which the garrison worked."},
        "alignment": "reconstructed: the least-cost route from the interpreter's house to the Clark house, keeping about 28 m back from the south bank; it fords the State Street creek near its mouth",
        "line_local_enu_m": sb,
    })

    # 5. On up the South Branch's east bank toward Lee's Place: from the Clark house south
    #    along the bank to the farm's haystacks, across the river from the cabin.
    hay = [centre(FOOTPRINTS[f"lees_place_haystack_1812_{k}"]) for k in "abcd"]
    hay_c = [sum(p[0] for p in hay) / 4, sum(p[1] for p in hay) / 4]
    b5 = [hay_c[0] + 14.0, hay_c[1] + 26.0]
    a5 = door("forks_house_clark_1812", (clark_c[0], clark_c[1] - 100))
    br_raw = route(a5, b5, bank_m=45.0, ford=False, margin_m=200, via_box=(-1800, 900, -4500, 0))
    br = shape(br_raw, "tread", 3.1, step=4.0)
    out.append({
        "id": "south_branch_path_1812",
        "name": "The path up the South Branch's east bank, toward Lee's Place",
        "form": "tread", "width_m": 0.7, "wear": 0.3, "treatment": "trodden_earth",
        "existence": {"confidence": "inferred", "sources": [SRC["currey"], SRC["andreas"]],
                      "note": "Currey (1912): from the haystacks on the east side of the river at Lee's Place the two 'made a run for the woods which were near at hand and directed their course toward the fort'. Andreas: the Hardscrabble cabin stood 'near the most frequented trail that led to the Desplaines'. Lightly worn: a farm three miles out."},
        "alignment": "reconstructed: the least-cost route from the forks to the farm's haystacks, keeping about 45 m back from the east bank, through the bank timber",
        "line_local_enu_m": br,
    })

    # 6. Lee's Place: the cabin down to its canoes.
    cab = FOOTPRINTS["lees_place_cabin_1812"]
    cab_c = centre(cab)
    th = math.radians(151.0 - 90.0)  # the cabin's front faces the river, bearing ~151
    landing = [cab_c[0] + 30.0 * math.sin(math.radians(151.0)), cab_c[1] + 30.0 * math.cos(math.radians(151.0))]
    while height(landing[0], landing[1]) < 0.05:
        landing = [landing[0] - 2.0 * math.sin(math.radians(151.0)), landing[1] - 2.0 * math.cos(math.radians(151.0))]
    a6 = door("lees_place_cabin_1812", landing)
    lp = shape(route(a6, landing, ford=False, margin_m=40, allow=("lees_place_field_fence_1812",)),
               "tread", 4.0, step=2.0)
    out.append({
        "id": "lees_place_landing_path_1812",
        "name": "Lee's Place: the path from the cabin down to the canoes",
        "form": "tread", "width_m": 0.8, "wear": 0.5, "treatment": "trodden_earth",
        "existence": {"confidence": "attested", "sources": [SRC["currey"]],
                      "note": "Currey (1912): the discharged soldier 'walked in a deliberate manner down the path toward the canoes tied up at the river bank'."},
        "alignment": "reconstructed: straight from the cabin's river front to the bank, down the bank's normal the cabin is seated on",
        "line_local_enu_m": lp,
    })

    # 7. The north-bank path: the Kinzie house west past Ouilmette's, Lalime's and Lemai's to
    #    the Burns house.
    a7 = door("kinzie_house_1812", (0, 330))
    b7 = door("burns_house_1812", (1200, 340))
    nb_raw = route(a7, b7, bank_m=22.0, ford=True, margin_m=160)
    nb = shape(nb_raw, "tread", 1.9, step=3.0)
    out.append({
        "id": "north_bank_path_1812",
        "name": "The path along the north bank, from the Kinzie house to the Burns house",
        "form": "tread", "width_m": 0.8, "wear": 0.45, "treatment": "trodden_earth",
        "existence": {"confidence": "inferred", "sources": [SRC["currey"], SRC["waubun"]],
                      "note": "Currey (1912): Mrs. Kinzie, at the Burns house, 'ran to her own home, a quarter of a mile distant'. Ouilmette's, Lalime's and Lemai's houses stood along the same bank between them."},
        "alignment": "reconstructed: the least-cost route from the Kinzie house to the Burns house, keeping about 22 m back from the north bank",
        "line_local_enu_m": nb,
    })

    # 8. Short ways round the fort and the Kinzie house: faint, reconstructed.
    short = [
        ("fort_gate_to_wharf_1812", "From the main gate round to the wharf", GATE,
         door("first_fort_wharf", (1150, 200), out_m=0.6), "band", 1.4, 0.6,
         "The landing the drafter numbers 27, 122 ft from the pickets: boats, water and stores came and went by it."),
        ("fort_road_to_stables_1812", "To the stables", None, "first_fort_outer_stable_middle", "tread", 1.0, 0.55,
         "Horses led out and in, and the hay and dung carried, every day."),
        ("fort_road_to_agency_1812", "To the agent's house and the factory", None, "first_fort_outer_agents_house", "tread", 0.9, 0.5,
         "The Indian agency and the United States factory, where the trade was done."),
        ("fort_road_to_officers_garden_1812", "To the officers' garden", None, "first_fort_outer_officers_garden", "tread", 0.7, 0.3,
         "A garden's daily traffic: light."),
        ("fort_road_to_sutlers_garden_1812", "To the sutler's garden", None, "first_fort_outer_sutlers_garden", "tread", 0.7, 0.25,
         "A garden's daily traffic: light."),
        ("fort_road_to_merchants_shop_1812", "To the merchant's shop", None, "first_fort_outer_merchants_shop", "tread", 0.8, 0.4,
         "A shop outside the gate."),
        ("fort_road_to_armourers_shop_1812", "To the armourer's shop", None, "first_fort_outer_armourers_shop", "tread", 0.8, 0.35,
         "The armourer's work came from the garrison and the Potawatomi alike."),
    ]
    for sid, name, a, target, form, width, wear, why in short:
        if a is None:
            tc = centre(FOOTPRINTS[target])
            b = door(target, GATE, out_m=1.2)
            a = nearest_on(road, b) if math.dist(nearest_on(road, b), b) < math.dist(GATE, b) else GATE
        else:
            b = target
        raw = route(a, b, ford=False, margin_m=60,
                    allow=("first_fort_dearborn_pickets_outer",) + ((target,) if isinstance(target, str) and target in FOOTPRINTS else ()))
        line = shape(raw, form, 1.7 + len(sid) % 5, step=2.0)
        if isinstance(target, str):
            CROSSES[sid] = (target,)  # a path ends at its own building's door
        out.append({
            "id": sid, "name": name, "form": form, "width_m": width, "wear": wear, "treatment": "trodden_earth",
            "existence": {"confidence": "reconstructed", "sources": [SRC["whistler"]],
                          "note": f"Whistler's 1808 draught places the building; that a path was worn to it is this project's reading. {why}"},
            "alignment": "reconstructed: the least-cost route from the fort's road (or the gate) to the door",
            "line_local_enu_m": line,
        })

    # The Kinzie house to its landing: the pirogues 'kept moored near the house' (Wau-Bun).
    kz = FOOTPRINTS["kinzie_house_1812"]
    kc = centre(kz)
    n = kc[1] - 10.0
    while height(kc[0], n) > 0.15:
        n -= 1.0
    landing = [kc[0] - 3.0, n + 3.0]
    a9 = door("kinzie_house_1812", landing)
    kl = shape(route(a9, landing, ford=False, margin_m=40, allow=("kinzie_house_1812_green",)),
               "tread", 2.2, step=2.0)
    out.append({
        "id": "kinzie_landing_path_1812",
        "name": "The Kinzie house down to its landing, across from the fort",
        "form": "tread", "width_m": 0.9, "wear": 0.55, "treatment": "trodden_earth",
        "existence": {"confidence": "inferred", "sources": [SRC["waubun"], SRC["currey"]],
                      "note": "Wau-Bun, through Currey (1912): 'by means of two old pirogues, or dugouts, that were kept moored near the house', the family crossed to the fort. The house faced the river across its 'broad green space', so one path crossed the green."},
        "alignment": "reconstructed: from the front door straight down to the bank opposite the fort",
        "line_local_enu_m": kl,
    })
    out.extend(camp_paths(out))
    return out


# --------------------------------------------------------------------------------------------
# T-3512: the camp's own paths
# --------------------------------------------------------------------------------------------
#
# The owner, 2026-11-08: *"The camps are also missing natural worn paths to each other and the
# river and maybe even to the fort or factor house or important paths, make them natural."*
# A gathering of some seven hundred people camped for days in groups a few dozen metres apart
# wore its own lines across the grass: between the groups, down to the water every lodge drew
# from (Wau-Bun ch. XIX: water dipped "from a stream that flowed near"), and to the factory and
# the agency the gathering had come to trade at and be counselled by (Heald: they came "from all
# quarters" for the factory's goods). Currey makes the creek their "favorite camping place", so
# these lines were older than the August camp. No source draws one; every line, width and wear
# is reconstructed under the same least-cost rule as the rest of this file, liberty
# L-t3339-worn-ground-1812 (extended by T-3512).
#
# THE RULE: the camp grounds (tools/generate_camp_ground_1812.py's worn patches) are joined by
# their minimum spanning tree plus every other link shorter than CAMP_LOOP_M that the tree left
# out (people walk the short way, so a camp has loops); each ground whose worn edge is within
# CAMP_WATER_M of open water has a path down to the bank, nearest first, a later one ending
# where it meets one already worn and sharing a landing within CAMP_LANDING_M; and the ground
# nearest the factory has a path toward the agency's door, which ends where it meets the
# south-bank path that runs on there. A path starts on its camp's worn edge and steers round
# every other camp ground.

CAMP_LOOP_M = 75.0     # a link the tree left out is walked too if it is shorter than this
CAMP_WATER_M = 170.0   # a camp this near open water wears its own path down to it
CAMP_BANK_M = 3.0      # the water path ends this far up from the waterline
CAMP_LANDING_M = 70.0  # a group's landing this near one already worn is that one


def _camp_patches():
    """Each camp ground's id and worn ring, as tools/generate_camp_ground_1812.py derives it."""
    import generate_camp_ground_1812 as cg
    return [(sc["id"], cg.blob(sc)) for sc in cg.camps()]


def _ring_toward(ring, target, out_m=0.0):
    """Where a ray from the ring's middle toward `target` leaves the ring, `out_m` beyond it."""
    cx, cy = centre(ring)
    dx, dy = target[0] - cx, target[1] - cy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    best = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = ux * ey - uy * ex
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - cx) * ey - (a[1] - cy) * ex) / den
        s = ((a[0] - cx) * uy - (a[1] - cy) * ux) / den
        if t > 0 and 0 <= s <= 1:
            best = max(best, t)
    return [cx + ux * (best + out_m), cy + uy * (best + out_m)]


def _dry_between(a, b, step=1.0):
    """True when the straight line a-b crosses no open water."""
    n = max(2, int(math.dist(a, b) / step))
    return all(height(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) >= WATER_Y
               for i in range(n + 1))


def _nearest_dry_bank(p, reach):
    """The dry point CAMP_BANK_M up from the open water nearest `p`, within `reach`, or None."""
    step = 2.5
    n = int(reach / step)
    ee = p[0] + (np.arange(-n, n + 1) * step)
    nn = p[1] + (np.arange(-n, n + 1) * step)
    E, N = np.meshgrid(ee, nn)
    H = height(E.ravel(), N.ravel()).reshape(E.shape)
    wet = np.nan_to_num(H, nan=9.0) < WATER_Y
    if not wet.any():
        return None
    d = np.hypot(E - p[0], N - p[1])
    d[~wet] = np.inf
    k = np.unravel_index(np.argmin(d), d.shape)
    if not np.isfinite(d[k]) or d[k] > reach:
        return None
    we, wn = E[k], N[k]
    ux, uy = p[0] - we, p[1] - wn
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L
    t = 0.0
    while height(we + ux * t, wn + uy * t) < 0.15 and t < 40:
        t += 0.5
    return [float(we + ux * (t + CAMP_BANK_M)), float(wn + uy * (t + CAMP_BANK_M))]


def camp_paths(existing):
    # the Potawatomi groups only: Wells's Miami escort camped apart, by the fort, and came in
    # on the 13th (it keeps its own worn ground and needs no path across the gathering's)
    patches = [(sid, r) for sid, r in _camp_patches() if sid.startswith("potawatomi_camp")]
    if not patches:
        return []
    camp_obs = {sid: (sid, _grow(ring, 2.0) if False else ring, _bbox(ring)) for sid, ring in patches}
    # every other camp ground, grown 2.5 m, is an obstacle to a camp path not bound for it
    grown = {}
    for sid, ring in patches:
        cx, cy = centre(ring)
        g = [[cx + (x - cx) * (1 + 2.5 / max(1.0, math.hypot(x - cx, y - cy))),
              cy + (y - cy) * (1 + 2.5 / max(1.0, math.hypot(x - cx, y - cy)))] for x, y in ring]
        grown[sid] = (sid, g, _bbox(g))
    del camp_obs

    def others(*keep):
        return [v for k, v in grown.items() if k not in keep]

    cen = {sid: centre(ring) for sid, ring in patches}
    rings = dict(patches)
    ids = [sid for sid, _r in patches]
    # the spanning tree (Prim) and the loops it left out
    edges = sorted((math.dist(cen[a], cen[b]), a, b) for i, a in enumerate(ids) for b in ids[i + 1:])
    inn = {ids[0]}
    tree = []
    while len(inn) < len(ids):
        d, a, b = min((d, a, b) for d, a, b in edges if (a in inn) != (b in inn))
        tree.append((d, a, b))
        inn |= {a, b}
    tree_set = {(a, b) for _d, a, b in tree}
    links = list(tree) + [(d, a, b) for d, a, b in edges if (a, b) not in tree_set and d < CAMP_LOOP_M]
    out = []
    short = lambda sid: sid.replace("potawatomi_camp_1812_", "").replace("_camp_1812", "")
    for d, a, b in sorted(links, key=lambda x: (x[1], x[2])):
        pa = _ring_toward(rings[a], cen[b], -1.0)
        pb = _ring_toward(rings[b], cen[a], -1.0)
        raw = route(pa, pb, ford=True, margin_m=60, extra=others(a, b))
        seed = (zlib_crc(a + b) % 997) / 97.0
        line = shape(raw, "tread", seed, step=2.5)
        loop = (a, b) not in tree_set
        out.append({
            "id": f"camp_path_{short(a)}_to_{short(b)}_1812",
            "name": f"A camp path between the {short(a).replace('_', ' ')} and {short(b).replace('_', ' ')} groups",
            "form": "tread", "width_m": 0.8 if loop else 1.0, "wear": 0.4 if loop else 0.55,
            "treatment": "trodden_earth", "fords": True,
            "existence": {"confidence": "reconstructed", "sources": [SRC["currey"], SRC["waubun"]],
                          "note": "Currey (1912): 'groups of Indian wigwams clustered along the creek', the Potawatomi's 'favorite camping place'. That the groups wore paths between them is this project's reading of a camp of some seven hundred people a few dozen metres apart."},
            "alignment": "reconstructed: the least-cost route between the two groups' worn edges, round every other group" + ("; a short link the spanning tree left out" if loop else ""),
            "line_local_enu_m": line,
        })
    # to the water: nearest first, each joining a water path already worn if it meets one,
    # and a landing within CAMP_LANDING_M of one already used is shared (a bank is walked to
    # where it is easy to dip from, and the next group finds the path there)
    wanted = []
    for sid in ids:
        bank = _nearest_dry_bank(cen[sid], CAMP_WATER_M + 25.0)
        if bank is not None:
            wanted.append((math.dist(cen[sid], bank), sid, bank))
    landings, water_lines = [], []
    for _d, sid, bank in sorted(wanted):
        ring = rings[sid]
        # shared only on this side of the water: a landing across the slough (T-3517) is
        # another group's, and walking round the slough's head to it is no path to water
        shared = next((q for q in landings if math.dist(q, bank) < CAMP_LANDING_M
                       and _dry_between(q, bank)), None)
        bank = shared or bank
        start = _ring_toward(ring, bank, -1.0)
        if math.dist(start, bank) < 6.0 or math.dist(start, bank) > CAMP_WATER_M:
            continue
        try:
            raw = route(start, bank, ford=False, margin_m=40, extra=others(sid), join=water_lines)
        except SystemExit:
            continue   # no dry way down (the bank is built on): the group draws elsewhere
        line = shape(raw, "tread", (zlib_crc(sid) % 991) / 89.0, step=2.0)
        if not shared:
            landings.append(bank)
        water_lines.append(line)
        out.append({
            "id": f"camp_water_path_{short(sid)}_1812",
            "name": f"The {short(sid).replace('_', ' ')} group's path down to the water",
            "form": "tread", "width_m": 1.0, "wear": 0.6, "treatment": "trodden_earth",
            "existence": {"confidence": "reconstructed", "sources": [SRC["waubun"]],
                          "note": "Wau-Bun ch. XIX: at the wigwam Mrs. Helm was led to, water was dipped 'from a stream that flowed near'. Every lodge carried its water, every day, so each group wore a path to the bank, and the groups behind ran theirs into it."},
            "alignment": "reconstructed: the least-cost route from the group's worn edge to the dry bank above the nearest open water, ending where it meets a water path already worn",
            "line_local_enu_m": line,
        })
    # to the factory and the agency, from the ground nearest them: the line ends at the agent's
    # house door, where the fort's own path to the agency and the factory already runs
    fac_c = centre(FOOTPRINTS["first_fort_outer_factory"])
    hub = min(ids, key=lambda s: math.dist(cen[s], fac_c))
    b = door("first_fort_outer_agents_house", cen[hub], out_m=1.2)
    a = _ring_toward(rings[hub], b, -1.0)
    sbl = [t["line_local_enu_m"] for t in existing if t["id"] == "south_bank_path_1812"]
    raw = route(a, b, ford=True, margin_m=120, extra=others(hub),
                allow=("first_fort_outer_agents_house",), join=sbl)
    CROSSES["camp_path_to_factory_1812"] = ("first_fort_outer_agents_house",)
    out.append({
        "id": "camp_path_to_factory_1812",
        "name": "The camp's path to the agency and the factory",
        "form": "tread", "width_m": 1.1, "wear": 0.65, "treatment": "trodden_earth", "fords": True,
        "existence": {"confidence": "inferred", "sources": [SRC["waubun"], SRC["currey"]],
                      "note": "The gathering had come for the factory's goods and the agent's council (Wau-Bun ch. XVIII: the council 'on the afternoon of the 12th'; the goods given out on the 14th). The traffic between the camp and the agency would have worn the camp's busiest line."},
        "alignment": f"reconstructed: the least-cost route from the nearest group ({short(hub).replace('_', ' ')}) toward the agent's house door, beside the factory, ending where it meets the south-bank path that runs on to it",
        "line_local_enu_m": shape(raw, "tread", 3.3, step=2.5),
    })
    return out


def zlib_crc(text):
    import zlib
    return zlib.crc32(text.encode("utf-8"))


# --------------------------------------------------------------------------------------------
# the worn yards
# --------------------------------------------------------------------------------------------


def _hull(points):
    pts = sorted(set((round(p[0], 4), round(p[1], 4)) for p in points))
    if len(pts) <= 2:
        return [list(p) for p in pts]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return [list(p) for p in lower[:-1] + upper[:-1]]


def _clip_half(ring, axis, value, keep_above):
    out = []
    for i in range(len(ring)):
        p, q = ring[i], ring[(i + 1) % len(ring)]
        pin = (p[axis] >= value) == keep_above
        qin = (q[axis] >= value) == keep_above
        if pin:
            out.append(p)
        if pin != qin:
            t = (value - p[axis]) / (q[axis] - p[axis])
            out.append([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t])
    return out


YARDS = [
    # id, structures, treatment, grow_m, feather_m, wear, why
    ("stables", ["first_fort_outer_stable_north", "first_fort_outer_stable_middle", "first_fort_outer_stable_south"],
     "worn_earth", 5.0, 8.0, 0.75, "Three stables in a row: hoof-worn ground in front of and between them."),
    ("agents_house", ["first_fort_outer_agents_house"], "trodden_earth", 3.5, 6.0, 0.55,
     "The Indian agent's house: callers came and went."),
    ("bake_house", ["first_fort_outer_bake_house"], "trodden_earth", 3.0, 5.0, 0.5, "The garrison's bake house."),
    ("factory", ["first_fort_outer_factory"], "trodden_earth", 4.0, 6.0, 0.6,
     "The United States factory, the government trading house: the busiest door outside the pickets."),
    ("interpreters_house", ["first_fort_outer_interpreters_house"], "trodden_earth", 3.0, 5.0, 0.4, "The interpreter's house."),
    ("merchants_shop", ["first_fort_outer_merchants_shop"], "trodden_earth", 3.0, 5.0, 0.45, "The merchant's shop."),
    ("armourers_shop", ["first_fort_outer_armourers_shop"], "trodden_earth", 3.0, 5.0, 0.45, "The armourer's shop."),
    ("kinzie_yard", ["kinzie_house_1812", "kinzie_bake_house_1812", "kinzie_dairy_1812", "kinzie_lodging_house_1812",
                     "kinzie_stable_1812"],
     "worn_earth", 3.5, 7.0, 0.6, "The Kinzie house's working yard behind it: stable, dairy, bake house and the men's lodging house. Its front keeps Wau-Bun's 'broad green space' to the river."),
    ("kinzie_horse_mill", ["kinzie_horse_mill_1812"], "worn_earth", 3.0, 4.0, 0.55,
     "A horse mill: a horse walked its round."),
    ("ouilmette_house", ["ouilmette_house_1812"], "trodden_earth", 3.0, 5.0, 0.4, "Ouilmette's dooryard."),
    ("lalime_house", ["lalime_house_1812"], "trodden_earth", 3.0, 5.0, 0.4, "Lalime's dooryard."),
    ("lemai_house", ["lemai_house_1812"], "trodden_earth", 1.2, 3.0, 0.35, "Lemai's dooryard."),
    ("burns_house", ["burns_house_1812"], "trodden_earth", 3.0, 5.0, 0.4, "The Burns family's dooryard."),
    ("lee_house", ["lee_house_1812"], "trodden_earth", 3.0, 5.0, 0.4, "The Lee family's town house at the outlet."),
    ("forks_house_clark", ["forks_house_clark_1812"], "trodden_earth", 2.5, 4.0, 0.35, "The house at the forks beside the cornfield."),
    ("forks_house_soldier", ["forks_house_soldier_1812"], "trodden_earth", 2.5, 4.0, 0.3, "The discharged soldier's house at the forks."),
    ("lees_place_cabin", ["lees_place_cabin_1812"], "trodden_earth", 3.5, 5.0, 0.45, "Lee's Place: the farm's cabin."),
    # T-3401: Wau-Bun ch. XVIII has the cattle "standing among the haystacks" and the soldier
    # pulling hay for them there, so the stack yard is ground the stock stood on, grazed and
    # trodden down round the stacks' feet, and not the standing prairie.
    ("lees_place_stack_yard", ["lees_place_haystack_1812_a", "lees_place_haystack_1812_b",
                               "lees_place_haystack_1812_c", "lees_place_haystack_1812_d"],
     "worn_earth", 3.0, 7.0, 0.5,
     "Lee's Place's stack yard: the cattle stood among the haystacks and were foddered from them (Wau-Bun ch. XVIII)."),
]


def yard_record(yid, structures, treatment, grow, feather, wear, why):
    pts = []
    for sid in structures:
        pts.extend(_grow(FOOTPRINTS[sid], grow))
    ring = _hull(pts)
    if yid == "kinzie_yard":
        # behind the house only: the green in front of it stays green.
        kz = FOOTPRINTS["kinzie_house_1812"]
        ring = _clip_half(ring, 1, max(p[1] for p in kz) - 1.0, True)
        # and short of the garden north of it (Kirkland's "trees, fences, grass plats").
        ring = _clip_half(ring, 1, min(p[1] for p in FOOTPRINTS["kinzie_garden_1812"]) - 1.5, False)
    # Counter-clockwise, as every interior yards.js lays.
    area2 = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(ring, ring[1:] + ring[:1]))
    if area2 < 0:
        ring = ring[::-1]
    ring = [[round(p[0], 2), round(p[1], 2)] for p in ring]
    # assertions
    gardens = [g for g in GARDENS if g in FOOTPRINTS]
    garden_clash = []
    for g in gardens:
        gr = FOOTPRINTS[g]
        if any(_point_in_ring(gr, *p) for p in ring) or any(_point_in_ring(ring, *p) for p in gr):
            garden_clash.append(g)
    skirt = _grow(ring, feather) if len(ring) == 4 else [
        [p[0] + (p[0] - centre(ring)[0]) / (math.hypot(p[0] - centre(ring)[0], p[1] - centre(ring)[1]) or 1) * feather,
         p[1] + (p[1] - centre(ring)[1]) / (math.hypot(p[0] - centre(ring)[0], p[1] - centre(ring)[1]) or 1) * feather]
        for p in ring]
    hs = height([p[0] for p in ring], [p[1] for p in ring])
    wet = int(np.sum(hs < WATER_Y))
    srcs = set()
    for sid in structures:
        pl = _sidecar(sid).get("placement") or {}
        srcs.update(pl.get("position_sources") or [])
    rid = f"worn_yard_1812_{yid}"
    return rid, {
        "_doc": (
            f"A WORN YARD ({TICKET}). The ground round {', '.join(structures)} as trodden earth "
            "feathered into the sward by renderers/web/js/yards.js. NOT ONE COORDINATE HERE IS "
            "AUTHORED - the ring is the convex hull of the buildings' committed footprints pushed "
            f"out {grow:.1f} m, written by tools/generate_worn_ground_1812.py and re-derived byte for "
            f"byte by tools/check.sh. It draws no fence (`runs: []`). docs/LIBERTIES.md {LIBERTY}."
        ),
        "id": rid,
        "name": f"Worn ground: {why.split(':')[0].rstrip('.')}",
        "kind": "worn_yard",
        "scene": "1812",
        "target_date": SCENE_DATE,
        "structure_ids": structures,
        "coordinates": "Local East-North-Up metres from data/datum.json's origin.",
        "existence": {
            "confidence": "reconstructed",
            "note": f"{why} That the ground round a used building was worn bare in patches is this project's reading; no source describes it. docs/LIBERTIES.md {LIBERTY}.",
            "sources": sorted(srcs),
        },
        "runs": [],
        "runs_note": "EMPTY, AND DELIBERATELY: worn ground round a building, not a fenced yard.",
        "ground": {
            "treatment": treatment,
            "confidence": "reconstructed",
            "note": "worn_earth where stock stood and wheels turned; trodden_earth at a dooryard.",
            "interior_local_enu_m": ring,
            "fringe_ring_local_enu_m": ring,
            "feather_m": feather,
            "wear": wear,
            "wear_note": "How bare the ground is, 0..1: the share of the treatment drawn and of the sward taken away. Sized by the traffic the building drew.",
        },
        "assertions": [
            {"id": "no_garden_worn", "claim": "the yard lies on no garden or field footprint",
             "clashes": garden_clash, "holds": not garden_clash},
            {"id": "dry_ground", "claim": "no corner of the yard lies on water",
             "wet_corners": wet, "holds": wet == 0},
        ],
    }


# --------------------------------------------------------------------------------------------
# the records
# --------------------------------------------------------------------------------------------


# The fences a path goes through by a gate: the Kinzie green's paling between the house and
# its landing, and the worm fence round Lee's field, inside which the cabin stands.
CROSSES = {
    "kinzie_landing_path_1812": ("kinzie_house_1812_green",),
    "lees_place_landing_path_1812": ("lees_place_field_fence_1812",),
}


def trails_record():
    ps = paths()
    bad_water, bad_struct, bad_tree = [], [], []
    for p in ps:
        line = p["line_local_enu_m"]
        hs = height([q[0] for q in line], [q[1] for q in line])
        wet = int(np.sum(hs < WATER_Y))
        p["length_m"] = round(length(line), 1)
        p["wet_vertices"] = wet
        if wet and p["id"] not in ("south_bank_path_1812", "north_bank_path_1812") and not p.get("fords"):
            bad_water.append(f"{p['id']}: {wet}")
        allow = ("first_fort_dearborn_pickets_outer", "first_fort_wharf") + CROSSES.get(p["id"], ())
        hits = sorted({blocked(q[0], q[1], allow=allow) for q in line} - {None})
        # a path may end AT its target's door, never cross another building
        hits = [h for h in hits if not any(h in str(x) for x in (p["id"],))]
        if hits:
            bad_struct.append(f"{p['id']}: {hits}")
        reach = p["width_m"] / 2 + STEM_CLEAR_M
        for sid, se, sn in PLANTED:
            d = min(_seg_dist(se, sn, line[i], line[i + 1]) for i in range(len(line) - 1))
            if d < reach:
                bad_tree.append(f"{p['id']}: {sid} {d:.1f} m")
    total = round(math.fsum(p["length_m"] for p in ps), 1)
    return {
        "_doc": (
            f"THE WORN PATHS AND TRAILS OF 1812 ({TICKET}). Drawn by renderers/web/js/yards.js as "
            "ribbons of trodden earth draped on the committed ground, the sward thinned under them. "
            "NOT ONE COORDINATE HERE IS AUTHORED: each line is the least-cost route over the 1812 "
            "ground between derived end points, smoothed and given a slow wander, written by "
            "tools/generate_worn_ground_1812.py (its docstring is the rule and the sources) and "
            f"re-derived byte for byte by tools/check.sh. docs/LIBERTIES.md {LIBERTY}."
        ),
        "id": TRAILS_ID,
        "name": "The worn paths and trails of 1812",
        "kind": "trails",
        "scene": "1812",
        "target_date": SCENE_DATE,
        "coordinates": "Local East-North-Up metres from data/datum.json's origin.",
        "existence": {
            "confidence": "inferred",
            "note": "Each trail states its own existence and sources; every alignment is reconstructed.",
            "sources": sorted({s for p in ps for s in p["existence"]["sources"]}),
        },
        "runs": [],
        "runs_note": "EMPTY, AND DELIBERATELY: these are trodden lines on open ground, not fences.",
        "ground": {
            "treatment": "trodden_earth",
            "confidence": "reconstructed",
            "note": "Each trail names its own treatment and form: `tread` a single worn foot-and-hoof line, `two_track` a cart's two ruts with a lighter median, `band` a broad trodden way. `wear` (0..1) is how bare it is, set by the traffic the sources and the buildings imply; the faintest are barely there.",
            "trails": ps,
        },
        "census": {"trails": len(ps), "metres": total},
        "assertions": [
            {"id": "no_trail_on_water",
             "claim": "no vertex of any trail lies on water, except where the two bank paths and the camp paths marked `fords` cross a creek (the renderer leaves the ford's wet ground undrawn)",
             "found": bad_water, "holds": not bad_water},
            {"id": "no_trail_through_a_building",
             "claim": "no vertex of any trail lies on a structure's footprint (grown 1.2 m) other than the picket row its gate opens in and the wharf it ends at",
             "found": bad_struct, "holds": not bad_struct},
            {"id": "no_trail_under_a_planted_tree",
             "claim": f"no trail's edge comes within {STEM_CLEAR_M} m of a tree a 1812 planting record stands",
             "found": bad_tree, "holds": not bad_tree},
        ],
    }


def manifest_entries() -> list[dict]:
    """The records this tool writes into data/enclosures/1812/index.json, in order. Read by
    tools/generate_fort_parade_ground.py too, which writes the same manifest."""
    out = [{"id": TRAILS_ID, "file": TRAILS_FILE}]
    for y in YARDS:
        rid = f"worn_yard_1812_{y[0]}"
        out.append({"id": rid, "file": f"{rid}.json"})
    return out


def text(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()
    outs = [(OUT_DIR / TRAILS_FILE, text(trails_record()))]
    for y in YARDS:
        rid, rec = yard_record(*y)
        outs.append((OUT_DIR / f"{rid}.json", text(rec)))
    from generate_fort_parade_ground import INDEX_1812, index_1812
    outs.append((INDEX_1812, text(index_1812())))
    bad = []
    for path, body in outs:
        rec = json.loads(body)
        for a in rec.get("assertions", []):
            if not a.get("holds"):
                bad.append(f"{path.relative_to(ROOT)}: assertion {a['id']} fails — {a['claim']} ({a})")
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                bad.append(f"{path.relative_to(ROOT)} is not what the rule derives — run "
                           "python3 tools/generate_worn_ground_1812.py")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
    if bad:
        print("WORN GROUND 1812 FAIL\n  " + "\n  ".join(bad))
        return 1
    rec = json.loads(outs[0][1])
    print(f"WORN GROUND 1812 {'PASS' if args.check else 'written'} — {rec['census']['trails']} trails, "
          f"{rec['census']['metres']:.0f} m, and {len(YARDS)} worn yards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
