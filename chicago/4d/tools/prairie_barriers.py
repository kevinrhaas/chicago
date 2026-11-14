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
