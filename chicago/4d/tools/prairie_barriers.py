#!/usr/bin/env python3
"""T-3554 — what a 1904 Prairie Avenue house has built outside its walls that a person must walk round.

The owner, 2026-11-12: "when people walk they dont cut themselves and swipe though a sidewalk
their dresses are wide ... their path sometimes cuts through a wall or barrier people should not
be able to walk through walls or barriers". A house's footprint keeps people out of its walls
(walker.js footprintsFrom), but its stoop, its area and coping walls, its iron railings and its
bays stand outside that footprint, and nothing kept a day's walk out of them.

`barriers(sc, glb)` reads them off the house model: on a CELL_M grid of the model's plan
(u = x, v = -z, y up), a cell is in the way where any face of the model passes between a knee
(KNEE_M) and a head (HEAD_M) over the ground there, outside the footprint's own walls. The cells
are returned as axis-aligned rectangles of the plan, turned into local E/N (`walls`, each a
four-corner ring, the shape human-days.js clearWayOf and human-spacing.js keepOutOf read).

`clear_point` / `clear_leg` ask a set of those rings whether a body stands, or walks, a skirt's
half-width (SKIRT_M) off all of them: prairie_people.py places a day's outdoor points with them.

T-3554 (owner, 2026-11-13, of a maid standing half inside the bottom steps of a front stoop: "she
cannot stand where there are stairs like that, no one should be able to"): the band starts at a
riser's height (KNEE_M), not a knee's. A stoop's bottom tread (0.15-0.18 m on these models) and
its second (0.3-0.35 m) are stairs to stand clear of as much as its rails are; the walks the models
lay are ground one stands on: flags at grade or raised to 0.124 m (1828's, Ream's), and whatever is
named a walk, paving or cinder (WALK_MATS).

Run alone it reports, per house, how many rings and how much ground they cover.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import derive_doors_1812 as d1812  # noqa: E402

CELL_M = 0.1      # the grid the barriers are read on
KNEE_M = 0.14     # anything from a riser's height over the ground (a stoop's bottom tread, 0.15 m and
                  # up; the highest walk is 0.124 m) ...
HEAD_M = 1.8      # ... to a head's height is in a walker's way
SKIRT_M = 0.35    # a skirt's half-width (derive_doors_scene.py WAY_SKIRT_M)
LEG_M = SKIRT_M - CELL_M / 2   # what a walk keeps off a barrier, less the half cell it is read on
                               # (house-barriers.js BARRIER_SKIRT_M)
SKIP_MATS = ("door_leaf", "door", "door_panel")       # hung by house-doors.js, swung open to pass
GROUND_MATS = ("turf", "earth", "lawn", "grass")
WALK_MATS = ("walk", "paving", "cinder")              # flat walks laid at grade: ground one stands on
MIN_CELLS = 2     # a speck smaller than this is a modelling crumb, not a barrier


def mask(parts, poly):
    """The plan's cells a walker cannot stand in: (mask, u0, v0), or None when nothing stands."""
    tris = [t for n, t in parts if n.lower() not in SKIP_MATS and not any(g in n.lower() for g in GROUND_MATS + WALK_MATS)]
    if not tris:
        return None
    T = np.concatenate(tris)
    U, V, Y = T[:, :, 0], -T[:, :, 2], T[:, :, 1]
    keep = (Y.max(1) > KNEE_M) & (Y.min(1) < HEAD_M)
    # A face wholly inside a convex footprint, a cell and more off its edges, stands only over
    # cells the footprint takes back below: skip it (most of a house's faces; the slow part).
    P = np.asarray(poly, float)
    if convex(P):
        inner = np.ones(len(U), bool)
        for k in range(3):
            inner &= inside_poly(U[:, k], V[:, k], P) & (edge_dist(U[:, k], V[:, k], P) > 1.5 * CELL_M)
        keep &= ~inner
    U, V, Y = U[keep], V[keep], Y[keep]
    if not len(U):
        return None
    u0, v0 = math.floor(U.min() / CELL_M) * CELL_M - CELL_M, math.floor(V.min() / CELL_M) * CELL_M - CELL_M
    nu = int(math.ceil((U.max() - u0) / CELL_M)) + 2
    nv = int(math.ceil((V.max() - v0) / CELL_M)) + 2
    gu, gv = u0 + np.arange(nu) * CELL_M, v0 + np.arange(nv) * CELL_M
    m = np.zeros((nu, nv), bool)
    den = (U[:, 1] - U[:, 0]) * (V[:, 2] - V[:, 0]) - (V[:, 1] - V[:, 0]) * (U[:, 2] - U[:, 0])
    on_edge = np.abs(den) < 1e-6
    # A face standing on edge (a wall, a picket, a railing's bar) stands over the cells its edges
    # cross, wherever its height reaches the band: each edge asked every half cell.
    if on_edge.any():
        EU, EV = U[on_edge], V[on_edge]
        n = np.maximum(2, (np.hypot(np.ptp(EU, axis=1), np.ptp(EV, axis=1)) / (CELL_M / 2)).astype(int) + 2)
        idx = np.repeat(np.arange(len(n)), n)
        t = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)) / (n[idx] - 1)
        for a, b in ((0, 1), (1, 2), (2, 0)):
            x = EU[idx, a] + (EU[idx, b] - EU[idx, a]) * t
            y = EV[idx, a] + (EV[idx, b] - EV[idx, a]) * t
            m[np.rint((x - u0) / CELL_M).astype(int), np.rint((y - v0) / CELL_M).astype(int)] = True
    for k in np.flatnonzero(~on_edge):
        a, b, c = (np.array([U[k, i], V[k, i]]) for i in range(3))
        e0, e1 = b - a, c - a
        den = e0[0] * e1[1] - e0[1] * e1[0]
        i0, i1 = int(math.floor((U[k].min() - u0) / CELL_M)), int(math.ceil((U[k].max() - u0) / CELL_M))
        j0, j1 = int(math.floor((V[k].min() - v0) / CELL_M)), int(math.ceil((V[k].max() - v0) / CELL_M))
        PU, PV = np.meshgrid(gu[i0:i1 + 1], gv[j0:j1 + 1], indexing="ij")
        du, dv = PU - a[0], PV - a[1]
        s = (du * e1[1] - dv * e1[0]) / den
        t = (e0[0] * dv - e0[1] * du) / den
        inside = (s >= -1e-6) & (t >= -1e-6) & (s + t <= 1 + 1e-6)
        y = Y[k, 0] + s * (Y[k, 1] - Y[k, 0]) + t * (Y[k, 2] - Y[k, 0])
        m[i0:i1 + 1, j0:j1 + 1] |= inside & (y > KNEE_M) & (y < HEAD_M)
    # Inside the footprint is the house's own walls' business (walker.js keeps people out).
    PU, PV = np.meshgrid(gu, gv, indexing="ij")
    m &= ~inside_poly(PU, PV, np.asarray(poly, float))
    from scipy import ndimage
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m &= np.isin(lab, 1 + np.flatnonzero(sizes >= MIN_CELLS))
    return (m, u0, v0) if m.any() else None


# --- what a visitor climbs: the tops the model builds outside its walls ----------------------
# The owner, 2026-11-14: "Anywhere there are stairs I should be able to climb". A house model's
# stoops, porches and terraces stand outside its footprint, and the visitor's walk (walker.js)
# stood on the terrain under them: the ground ran on under the steps, so the steps could not be
# climbed. `floor(parts, poly)` reads the tops one stands on: on the CELL_M grid, the highest face
# up to FLOOR_CAP_M over the ground in each cell, the ground where that is under FLOOR_GROUND_M;
# a cell is in the way where a face stands between FLOOR_KNEE_M and HEAD_M over its own top (a rail,
# a cheek wall, a pier); the floor is every top a body reaches from the ground outside, a step of
# at most FLOOR_STEP_M at a time and never through what is in the way; and every cell in the way
# (or too high to step onto) beside that floor is a wall, FLOOR_WALL_M over the floor beside it, so
# the walker's step rule turns one back from a rail or off a cheek as it would from a wall.
FLOOR_GROUND_M = 0.12   # a top lower than this is the ground (derive_doors_scene.py WAY_GROUND_M)
FLOOR_CAP_M = 2.6       # tops are read below this (a porch's floor, never its roof)
FLOOR_BIN_M = 0.1       # the heights over a cell are filed in bins this deep
FLOOR_KNEE_M = 0.25     # a face this far over a top, to a head's height, is in the way (derive_doors_scene.py WAY_KNEE_M)
FLOOR_STEP_M = 0.3      # the most one step climbs (walker.js WALK.stepUp is 0.35)
FLOOR_WALL_M = 1.0      # a wall beside the floor stands this far over it, past any step
FLOOR_IN_M = 3.0        # how far into the footprint a doorway's reveal or a recessed porch is read
FLOOR_MIN_TOP_M = 0.4   # a floor rises this far somewhere, or it is a coping, not a stair


def floor(parts, poly):
    """The tops a visitor climbs outside the footprint: (heights, walls, u0, v0) with heights a
    float grid of the model's plan, NaN where the ground answers, and walls the cells of it that
    are walls beside the floor (cell (i, j) centred on u0 + i*cell, v0 + j*cell), or None where
    the model builds nothing one climbs."""
    tris = [t for n, t in parts if n.lower() not in SKIP_MATS and not any(g in n.lower() for g in GROUND_MATS)]
    if not tris:
        return None
    T = np.concatenate(tris)
    U, V, Y = T[:, :, 0], -T[:, :, 2], T[:, :, 1]
    keep = (Y.max(1) > FLOOR_GROUND_M) & (Y.min(1) < FLOOR_CAP_M + HEAD_M)
    P = np.asarray(poly, float)
    if convex(P):
        inner = np.ones(len(U), bool)
        for k in range(3):
            inner &= inside_poly(U[:, k], V[:, k], P) & (edge_dist(U[:, k], V[:, k], P) > FLOOR_IN_M + 2 * CELL_M)
        keep &= ~inner
    U, V, Y = U[keep], V[keep], Y[keep]
    if not len(U):
        return None
    u0, v0 = math.floor(U.min() / CELL_M) * CELL_M - 2 * CELL_M, math.floor(V.min() / CELL_M) * CELL_M - 2 * CELL_M
    nu = int(math.ceil((U.max() - u0) / CELL_M)) + 3
    nv = int(math.ceil((V.max() - v0) / CELL_M)) + 3
    gu, gv = u0 + np.arange(nu) * CELL_M, v0 + np.arange(nv) * CELL_M
    # Each cell's faces filed by height, in FLOOR_BIN_M bins (bit k: something between k and k+1
    # bins up), and the highest face in each bin up to the cap: a top is one with nothing over
    # it from FLOOR_KNEE_M to HEAD_M (a porch's floor under its roof, never the roof).
    nb = int(round(FLOOR_CAP_M / FLOOR_BIN_M))
    bits = np.zeros((nu, nv), np.uint64)
    tops = np.full((nb + 1, nu, nv), -np.inf, np.float32)
    binof = lambda y: np.clip(np.floor(np.asarray(y) / FLOOR_BIN_M), 0, 63).astype(np.int64)
    den = (U[:, 1] - U[:, 0]) * (V[:, 2] - V[:, 0]) - (V[:, 1] - V[:, 0]) * (U[:, 2] - U[:, 0])
    on_edge = np.abs(den) < 1e-6
    if on_edge.any():
        # A face standing on edge stands over the cells its edges cross, its whole height.
        EU, EV, EY = U[on_edge], V[on_edge], Y[on_edge]
        n = np.maximum(2, (np.hypot(np.ptp(EU, axis=1), np.ptp(EV, axis=1)) / (CELL_M / 2)).astype(int) + 2)
        idx = np.repeat(np.arange(len(n)), n)
        t = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)) / (n[idx] - 1)
        blo, bhi = binof(EY.min(1))[idx], binof(EY.max(1))[idx]
        run = ((np.uint64(1) << (bhi - blo + 1).astype(np.uint64)) - np.uint64(1)) << blo.astype(np.uint64)
        run = np.where(bhi - blo >= 63, np.uint64(0xFFFFFFFFFFFFFFFF) << blo.astype(np.uint64), run)
        for a, b in ((0, 1), (1, 2), (2, 0)):
            x = np.rint((EU[idx, a] + (EU[idx, b] - EU[idx, a]) * t - u0) / CELL_M).astype(int)
            y = np.rint((EV[idx, a] + (EV[idx, b] - EV[idx, a]) * t - v0) / CELL_M).astype(int)
            np.bitwise_or.at(bits, (x, y), run)
    for k in np.flatnonzero(~on_edge):
        a, b, c = (np.array([U[k, i], V[k, i]]) for i in range(3))
        e0, e1 = b - a, c - a
        d = e0[0] * e1[1] - e0[1] * e1[0]
        i0, i1 = int(math.floor((U[k].min() - u0) / CELL_M)), int(math.ceil((U[k].max() - u0) / CELL_M))
        j0, j1 = int(math.floor((V[k].min() - v0) / CELL_M)), int(math.ceil((V[k].max() - v0) / CELL_M))
        PU, PV = np.meshgrid(gu[i0:i1 + 1], gv[j0:j1 + 1], indexing="ij")
        du, dv = PU - a[0], PV - a[1]
        s = (du * e1[1] - dv * e1[0]) / d
        t = (e0[0] * dv - e0[1] * du) / d
        inside = (s >= -1e-6) & (t >= -1e-6) & (s + t <= 1 + 1e-6)
        if not inside.any():
            continue
        y = Y[k, 0] + s * (Y[k, 1] - Y[k, 0]) + t * (Y[k, 2] - Y[k, 0])
        bk = binof(y)
        bits[i0:i1 + 1, j0:j1 + 1] |= np.where(inside, np.uint64(1) << bk.astype(np.uint64), np.uint64(0))
        for q in np.unique(bk[inside & (bk <= nb)]):
            sl = tops[q, i0:i1 + 1, j0:j1 + 1]
            np.maximum(sl, np.where(inside & (bk == q), y, -np.inf).astype(np.float32), out=sl)
    PU, PV = np.meshgrid(gu, gv, indexing="ij")
    # The house's own, walker.js keeps one out of; but its doorways' reveals and porches recessed
    # into the front are climbed to (FLOOR_IN_M in from the footprint's edge).
    out = inside_poly(PU, PV, P) & (edge_dist(PU, PV, P) > FLOOR_IN_M)
    k0 = int(math.ceil(FLOOR_KNEE_M / FLOOR_BIN_M)) + 1          # the band over a top starts here ...
    k1 = int(math.ceil(HEAD_M / FLOOR_BIN_M)) + 1                # ... and runs to here (bins)
    clear_over = lambda b: (bits >> np.uint64(b + k0)) & np.uint64((1 << (k1 - k0)) - 1) == 0
    # The highest top with a head's clearance over it; the ground where that is the ground's.
    h = np.zeros((nu, nv))
    has = np.zeros((nu, nv), bool)
    ground_ok = ((bits >> np.uint64(k0)) & np.uint64((1 << (k1 - k0)) - 1)) == 0
    for q in range(nb + 1):
        ok = np.isfinite(tops[q]) & clear_over(q)
        h = np.where(ok, tops[q], h)
        has |= ok
    ground = (~has | (h < FLOOR_GROUND_M)) & ground_ok
    h = np.where(ground, 0.0, h)
    # In the way: a cell where nothing is stood on clear of what is over it (a wall, a rail).
    blocked = (~has & ~ground_ok) | out
    # Up from the open ground outside, a step at a time.
    from collections import deque
    reached = ground & ~blocked
    q = deque(zip(*np.nonzero(reached)))
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x, y = i + di, j + dj
            if 0 <= x < nu and 0 <= y < nv and not reached[x, y] and not blocked[x, y] and h[x, y] <= h[i, j] + FLOOR_STEP_M:
                reached[x, y] = True
                q.append((x, y))
    from scipy import ndimage
    # A top narrower than a body (a cheek wall's coping, a rail's foot) is not stood on, and a
    # floor is a stair's or a porch's only where it rises past a step or two (FLOOR_MIN_TOP_M):
    # a lawn's coping is the ground's business, not a stair.
    fl = ndimage.binary_opening(reached & ~ground, structure=np.ones((3, 3), bool))
    lab, n = ndimage.label(fl)
    if n:
        tops = ndimage.maximum(np.where(fl, h, 0.0), lab, range(1, n + 1))
        fl &= np.isin(lab, 1 + np.flatnonzero(np.asarray(tops) >= FLOOR_MIN_TOP_M))
    if not fl.any():
        return None
    heights = np.where(fl, h, np.nan)
    # The walls beside it: whatever is built there and is not the floor (a rail, a cheek, a
    # top too high or too narrow to stand on), next to a floor cell.
    near = ndimage.maximum_filter(np.where(fl, h, -np.inf), size=3)
    wall = ~fl & ~out & (near > -np.inf) & (blocked | ~ground)
    heights = np.where(wall, near + FLOOR_WALL_M, heights)
    ii, jj = np.nonzero(np.isfinite(heights))
    a0, a1, b0, b1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    return heights[a0:a1, b0:b1], wall[a0:a1, b0:b1], u0 + a0 * CELL_M, v0 + b0 * CELL_M


def floor_plan(got) -> dict | None:
    """`floor`'s grid for the data file: `rects` the floor and `walls` the walls beside it, each
    rectangles of one height, five integers apiece (i0 i1 j0 j1 half-open, then the top in
    centimetres over the model's ground), in one string; cell (i, j) centred on u = u0 + i * cell,
    v = v0 + j * cell of the model's plan, the grid ni by nj cells."""
    if got is None:
        return None
    g, wall, u0, v0 = got
    cm = np.where(np.isfinite(g), np.rint(g * 100), -1).astype(int)

    def runs(which):
        out = []
        for val in sorted(set(cm[which & (cm >= 0)].ravel().tolist())):
            out += [(a, b, c, d, val) for a, b, c, d in rectangles(which & (cm == val))]
        return " ".join(" ".join(str(x) for x in r) for r in sorted(out)), len(out)
    rects, n = runs(~wall)
    walls, m = runs(wall)
    return {"cell": CELL_M, "u0": round(float(u0), 3), "v0": round(float(v0), 3), "ni": int(g.shape[0]), "nj": int(g.shape[1]),
            "count": n, "rects": rects, "wall_count": m, "walls": walls}


def standing(got, r=SKIRT_M):
    """`free(u, v)`: whether a body stands at plan (u, v) at least `r` off every cell of `mask`'s
    (to within half a cell; off the grid is free)."""
    if got is None:
        return lambda u, v: True
    from scipy import ndimage
    m, u0, v0 = got
    k = int(math.ceil((r + CELL_M / 2) / CELL_M))
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    disk = (xx * xx + yy * yy) * CELL_M ** 2 <= (r + CELL_M / 2) ** 2 + 1e-9
    bad = ndimage.binary_dilation(np.pad(m, k), structure=disk)
    u0, v0 = u0 - k * CELL_M, v0 - k * CELL_M

    def free(u, v):
        i, j = int(round((u - u0) / CELL_M)), int(round((v - v0) / CELL_M))
        return not (0 <= i < bad.shape[0] and 0 <= j < bad.shape[1]) or not bad[i, j]
    return free


def convex(P) -> bool:
    d = np.roll(P, -1, axis=0) - P
    cross = d[:, 0] * np.roll(d, -1, axis=0)[:, 1] - d[:, 1] * np.roll(d, -1, axis=0)[:, 0]
    return bool(len(P) >= 3 and ((cross >= -1e-9).all() or (cross <= 1e-9).all()))


def edge_dist(X, Y, P):
    best = np.full(np.shape(X), np.inf)
    for a, b in zip(P, np.roll(P, -1, axis=0)):
        d = b - a
        L2 = float(d @ d) or 1e-12
        t = np.clip(((X - a[0]) * d[0] + (Y - a[1]) * d[1]) / L2, 0, 1)
        best = np.minimum(best, np.hypot(X - a[0] - t * d[0], Y - a[1] - t * d[1]))
    return best


def inside_poly(X, Y, P):
    hit = np.zeros(X.shape, bool)
    for (x1, y1), (x2, y2) in zip(P, np.roll(P, -1, axis=0)):
        if y1 == y2:
            continue
        cross = (y1 > Y) != (y2 > Y)
        hit ^= cross & (X < (x2 - x1) * (Y - y1) / (y2 - y1) + x1)
    return hit


def rectangles(m):
    """The cells as rectangles [i0, i1, j0, j1) — runs along v merged down u where they match."""
    out, open_ = [], {}
    for i in range(m.shape[0] + 1):
        runs = set()
        if i < m.shape[0]:
            row = np.concatenate([[False], m[i], [False]])
            d = np.flatnonzero(np.diff(row.astype(np.int8)))
            runs = {(int(d[k]), int(d[k + 1])) for k in range(0, len(d), 2)}
        for key in [k for k in open_ if k not in runs]:
            out.append((open_.pop(key), i, *key))
        for r in runs:
            open_.setdefault(r, i)
    return sorted(out)


def barriers(sc: dict, glb: Path) -> list[list[list[float]]]:
    """The house's barriers as rings in local E/N, each the four corners of a plan rectangle."""
    return rings_of(mask(d1812.load_triangles(glb), sc["footprint"]["polygon"]), sc["placement"])


def plan_of(got) -> dict | None:
    """`mask`'s cells for the data file: the plan rectangles as cell indices, four to a
    rectangle (i0 i1 j0 j1, half-open), in one string of integers; cell (i, j) is centred on
    u = u0 + i * cell, v = v0 + j * cell of the model's plan."""
    if got is None:
        return None
    m, u0, v0 = got
    rects = rectangles(m)
    return {"cell": CELL_M, "u0": round(float(u0), 3), "v0": round(float(v0), 3), "count": len(rects),
            "rects": " ".join(f"{a} {b} {c} {d}" for a, b, c, d in rects)}


def rings_from_plan(plan: dict | None, pl: dict) -> list[list[list[float]]]:
    """A data file's `barrier` plan as rings in local E/N (placement `pl`)."""
    if not plan:
        return []
    c, u0, v0 = plan["cell"], plan["u0"], plan["v0"]
    k = [int(x) for x in plan["rects"].split()]
    rings = []
    for i0, i1, j0, j1 in zip(k[0::4], k[1::4], k[2::4], k[3::4]):
        ua, ub = u0 + (i0 - 0.5) * c, u0 + (i1 - 0.5) * c
        va, vb = v0 + (j0 - 0.5) * c, v0 + (j1 - 0.5) * c
        rings.append([list(d1812.to_world(u, v, pl)) for u, v in ((ua, va), (ub, va), (ub, vb), (ua, vb))])
    return rings


def rings_of(got, pl: dict) -> list[list[list[float]]]:
    """`mask`'s cells as rings in local E/N (placement `pl`), each a plan rectangle's corners."""
    if got is None:
        return []
    m, u0, v0 = got
    rings = []
    for i0, i1, j0, j1 in rectangles(m):
        ua, ub = u0 + (i0 - 0.5) * CELL_M, u0 + (i1 - 0.5) * CELL_M
        va, vb = v0 + (j0 - 0.5) * CELL_M, v0 + (j1 - 0.5) * CELL_M
        rings.append([[round(x, 2) for x in d1812.to_world(u, v, pl)] for u, v in ((ua, va), (ub, va), (ub, vb), (ua, vb))])
    return rings


# --- asking a set of rings (local E/N), as a day's walker will -------------------------------

def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy or 1e-12
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _inside(p, ring):
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _cross(a, b, c, d):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (o(a, b, c) > 0) != (o(a, b, d) > 0) and (o(c, d, a) > 0) != (o(c, d, b) > 0)


class Rings:
    """A set of rings with a coarse index, for many point and leg questions."""

    def __init__(self, rings, cell=4.0):
        self.rings, self.cell, self.grid = [list(map(tuple, r)) for r in rings], cell, {}
        for k, r in enumerate(self.rings):
            es, ns = [p[0] for p in r], [p[1] for p in r]
            for gi in range(int(math.floor(min(es) / cell)), int(math.floor(max(es) / cell)) + 1):
                for gj in range(int(math.floor(min(ns) / cell)), int(math.floor(max(ns) / cell)) + 1):
                    self.grid.setdefault((gi, gj), []).append(k)

    def near(self, e0, n0, e1, n1):
        c = self.cell
        seen = set()
        for gi in range(int(math.floor(e0 / c)), int(math.floor(e1 / c)) + 1):
            for gj in range(int(math.floor(n0 / c)), int(math.floor(n1 / c)) + 1):
                for k in self.grid.get((gi, gj), ()):
                    if k not in seen:
                        seen.add(k)
                        yield self.rings[k]

    def clearance(self, p) -> float:
        """How far `p` stands from the nearest ring (0 inside one); inf past 4 m."""
        best = math.inf
        for r in self.near(p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4):
            if _inside(p, r):
                return 0.0
            for a, b in zip(r, r[1:] + r[:1]):
                best = min(best, _seg_dist(p, a, b))
        return best

    def clear_point(self, p, r=SKIRT_M) -> bool:
        return self.clearance(p) >= r

    def clear_leg(self, a, b, r=LEG_M) -> bool:
        """Whether a body walking a -> b keeps `r` off every ring the whole way."""
        L = math.dist(a, b)
        for q in self.near(min(a[0], b[0]) - r, min(a[1], b[1]) - r, max(a[0], b[0]) + r, max(a[1], b[1]) + r):
            for c, d in zip(q, q[1:] + q[:1]):
                if _cross(a, b, c, d) or _seg_dist(c, a, b) < r or _seg_dist(d, a, b) < r \
                        or _seg_dist(a, c, d) < r or _seg_dist(b, c, d) < r:
                    return False
            if L < 1e-9 and _inside(a, q):
                return False
        return True


def main() -> int:
    import json
    import time
    doors = json.loads((ROOT / "data/humans/doors_1904.json").read_text())
    total = 0
    t = time.time()
    for row in doors["structures"] + doors.get("barriers", []):
        rings = rings_from_plan(row.get("barrier"), row["placement"])
        total += len(rings)
        area = sum(abs((r[1][0] - r[0][0]) * (r[2][1] - r[1][1]) - (r[1][1] - r[0][1]) * (r[2][0] - r[1][0])) for r in rings)
        print(f"{row['structure']}: {len(rings)} ring(s), {area:.1f} m²")
    print(f"{total} rings on {len(doors['structures'])} buildings ({time.time() - t:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
