#!/usr/bin/env python3
"""Where the 1835 and 1904 people's homes are entered (T-3516), as derive_doors_1812.py does for 1812.

    python3 tools/derive_doors_scene.py            write data/humans/doors_1835.json, doors_1904.json
    python3 tools/derive_doors_scene.py --check    the gate: each file is what the records say

The owner, 2026-11-08: *"They can take breaks and go in and out of houses and buildings"*, for
all years. renderers/web/js/human-days.js takes a person in by the door of the building their
day has them in, and offers Ask for them there. Which buildings: those named by a drawn
person's day (`behaviour.day[].spans[].where`) in data/humans/instances/<year>/.

  1835  the town's buildings draw their door leaves into their own models, as 1812's do, so a
        building's doors are read off its model by derive_doors_1812.py's `doors_of`.
  1904  Glessner's house is one model with no door material; its doors are read from its
        record, in its own plan frame (W feet west of the Prairie face, S feet south of the
        Eighteenth Street face, house-doors.js glessnerFrontPlan's frame):
          service_stair  the court's service entrance (openings_court_north, at the head of the
                         north court service stair, v4_detail.north_court_service_stair): one
                         answering stands STEP_M out from the foot of the flight. Since T-3524
                         the door is a passage (house-doors.js): who goes in climbs the flight
                         and the landing to it, it opens and shuts, and only then are they in.
          north_entry    the servants' entry off Eighteenth Street (v4_detail.north_entry_alcove):
                         one answering stands on the walk STEP_M out from the alcove's front
                         steps; a passage too (T-3524), up the front steps and the stair inside
                         to its side door.
          stable         the stable's carriage doorway on Eighteenth Street
                         (openings_stable_doors).
        The family's front door is house-doors.js's own (T-3442) and is not listed here.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import derive_doors_1812 as d1812  # noqa: E402
import prairie_barriers as pb  # noqa: E402

FORMAT = "c4d-doors-scene/2"   # /2 (T-3596): rows name their model by its build inputs, not its bytes
SCENES = ("1835", "1904")
FT = 0.3048
STEP_M = d1812.STEP_M

# T-3554 (owner, 2026-11-12: *"make sure they are openable and closeable for a person to enter
# and make sure that people can walk up the stairs instead of vanishing into the staircase"*).
# A 1904 house's built front leaf becomes a passage (house-doors.js): it is hung to swing, and
# the way up to it is read off the model's own stoop, tread by tread.
LEAF_MATS = ('door_leaf', 'door', 'door_panel', 'draft_door')
DRAFT_LEAF = 'draft_door'  # a draft's drawn door: hung where its stoop reaches it, else a reconstructed entrance
WAY_CELL_M = 0.1           # the grid the way is found on
WAY_RISE_M = 0.26          # the most one step of the way climbs (a riser here is 0.15-0.19 m)
WAY_KNEE_M = 0.25          # anything from this far over the tread ...
WAY_HEAD_M = 1.8           # ... to a head's height over it is in the way
WAY_SKIRT_M = 0.35         # a skirt's half-width: the way keeps this far off a drop or a rail
WAY_EASE_M = 0.12          # house-doors.js RISER_EASE_M: the rise eased this far each side
WAY_GROUND_M = 0.12        # a top lower than this is the ground (the caller's ground answers)
STOOP_PAD_M = 0.3          # a back stoop's flight past its laid run_m (back-yards.js fits it to the ground)
WAY_BEFORE_M = 0.45        # house-doors.js PASSAGE_BEFORE_M: where one stops before the leaf
PAIR_OVER_M = 1.6          # an opening wider than this is hung as a pair of leaves
GROUND_MATS = ('turf', 'earth', 'lawn', 'grass')


def stoop_way(parts, front_u: float, vm: float, sill: float, free=lambda u, v: True):
    """The way from the ground, up the stoop, to WAY_BEFORE_M before the leaf at (front_u, vm),
    in the model's plan (u = x, v = -z, y up): ([[u, v, y | None], ...] outside to in, '') with
    y None on the ground, or (None, why). Found on a WAY_CELL_M grid over the tops of what is
    built there: a step climbs at most WAY_RISE_M, nothing stands in the way between a knee and
    a head over the tread, and the way keeps a skirt's width off every drop and every rail."""
    u0, u1 = front_u - 0.3, front_u + 9.0
    v0, v1 = vm - 7.0, vm + 7.0
    nu, nv = int(round((u1 - u0) / WAY_CELL_M)) + 1, int(round((v1 - v0) / WAY_CELL_M)) + 1
    gu = u0 + np.arange(nu) * WAY_CELL_M
    gv = v0 + np.arange(nv) * WAY_CELL_M
    cap = sill + 0.15
    top = np.full((nu, nv), -np.inf)
    lo = np.full((nu, nv), np.inf)
    hi = np.full((nu, nv), -np.inf)
    tris = [t for name, t in parts if name.lower() not in LEAF_MATS and not any(g in name.lower() for g in GROUND_MATS)]
    T = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
    U, V, Y = T[:, :, 0], -T[:, :, 2], T[:, :, 1]
    keep = (U.max(1) >= u0) & (U.min(1) <= u1) & (V.max(1) >= v0) & (V.min(1) <= v1) & (Y.min(1) < cap + WAY_HEAD_M)
    U, V, Y = U[keep], V[keep], Y[keep]

    def cell(x, y):
        return int(round((x - u0) / WAY_CELL_M)), int(round((y - v0) / WAY_CELL_M))

    for k in range(len(U)):
        a, b, c = (np.array([U[k, i], V[k, i]]) for i in range(3))
        i0 = max(0, int(math.floor((U[k].min() - u0) / WAY_CELL_M)))
        i1 = min(nu - 1, int(math.ceil((U[k].max() - u0) / WAY_CELL_M)))
        j0 = max(0, int(math.floor((V[k].min() - v0) / WAY_CELL_M)))
        j1 = min(nv - 1, int(math.ceil((V[k].max() - v0) / WAY_CELL_M)))
        if i1 < i0 or j1 < j0:
            continue
        e0, e1 = b - a, c - a
        den = e0[0] * e1[1] - e0[1] * e1[0]
        if abs(den) < 1e-9:
            # A face standing on edge: it stands over the cells its edges cross.
            n = max(2, int(math.hypot(np.ptp(U[k]), np.ptp(V[k])) / 0.05) + 2)
            for p, q in ((a, b), (b, c), (c, a)):
                for t in np.linspace(0, 1, n):
                    iu, iv = cell(*(p + (q - p) * t))
                    if 0 <= iu < nu and 0 <= iv < nv:
                        lo[iu, iv] = min(lo[iu, iv], Y[k].min())
                        hi[iu, iv] = max(hi[iu, iv], Y[k].max())
            continue
        PU, PV = np.meshgrid(gu[i0:i1 + 1], gv[j0:j1 + 1], indexing='ij')
        du, dv = PU - a[0], PV - a[1]
        s = (du * e1[1] - dv * e1[0]) / den
        t = (e0[0] * dv - e0[1] * du) / den
        inside = (s >= -1e-6) & (t >= -1e-6) & (s + t <= 1 + 1e-6)
        if not inside.any():
            continue
        y = Y[k, 0] + s * (Y[k, 1] - Y[k, 0]) + t * (Y[k, 2] - Y[k, 0])
        sl, sh, st = lo[i0:i1 + 1, j0:j1 + 1], hi[i0:i1 + 1, j0:j1 + 1], top[i0:i1 + 1, j0:j1 + 1]
        np.minimum(sl, np.where(inside, y, np.inf), out=sl)
        np.maximum(sh, np.where(inside, y, -np.inf), out=sh)
        np.maximum(st, np.where(inside & (y <= cap), y, -np.inf), out=st)
    ground = ~np.isfinite(top) | (top < WAY_GROUND_M)
    h = np.where(ground, 0.0, top)
    blocked = (hi > h + WAY_KNEE_M) & (lo < h + WAY_HEAD_M)
    edge = blocked.copy()
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        edge |= np.abs(np.roll(h, (di, dj), axis=(0, 1)) - h) > WAY_RISE_M
    from scipy import ndimage
    skirt = ndimage.binary_dilation(edge, iterations=int(math.ceil(WAY_SKIRT_M / WAY_CELL_M)))
    start = cell(front_u + WAY_BEFORE_M, vm)
    if blocked[start]:
        return None, 'something stands before the leaf'
    # Out from the door, cheapest first, to the first open ground clear of every edge and
    # at least STEP_M out from where it started: the foot of the stoop.
    best, prev, pq, goal = {start: 0.0}, {}, [(0.0, start)], None
    while pq:
        g, cur = heapq.heappop(pq)
        if g > best[cur]:
            continue
        if ground[cur] and not skirt[cur] and math.dist(cur, start) * WAY_CELL_M >= STEP_M and free(gu[cur[0]], gv[cur[1]]):
            goal = cur
            break
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                nx = (cur[0] + di, cur[1] + dj)
                if (di, dj) == (0, 0) or not (0 <= nx[0] < nu and 0 <= nx[1] < nv) or blocked[nx]:
                    continue
                if abs(h[nx] - h[cur]) > WAY_RISE_M or nx[0] < start[0]:
                    continue
                ng = g + math.hypot(di, dj) * WAY_CELL_M * (4.0 if skirt[nx] else 1.0)
                if ng < best.get(nx, math.inf):
                    best[nx], prev[nx] = ng, cur
                    heapq.heappush(pq, (ng, nx))
    if goal is None:
        return None, 'no way down from the door to the ground'
    cells = [goal]
    while cells[-1] != start:
        cells.append(prev[cells[-1]])
    pts = [(float(gu[i]), float(gv[j]), None if ground[i, j] else float(h[i, j])) for i, j in cells]
    # The grid's staircase of cells straightened: keep a point only where the way turns or
    # changes height, and at each riser one point either side of it, WAY_EASE_M off.
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        if p[2] != q[2]:
            mu, mv = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            du, dv = q[0] - p[0], q[1] - p[1]
            L = math.hypot(du, dv)
            out.append((mu - du / L * WAY_EASE_M, mv - dv / L * WAY_EASE_M, p[2]))
            out.append((mu + du / L * WAY_EASE_M, mv + dv / L * WAY_EASE_M, q[2]))
        out.append(q)
    simple = [out[0]]
    for b, c in zip(out[1:], out[2:]):
        a = simple[-1]
        if a[2] == b[2] == c[2] and abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-6:
            continue
        simple.append(b)
    simple.append(out[-1])
    return [[round(u, 3), round(v, 3), None if y is None else round(y, 3)] for u, v, y in simple], ''


def passage_plan(sid: str, leaf_tris, parts, mats, free=lambda u, v: True) -> tuple[dict | None, str]:
    """A built front leaf as house-doors.js hangs a passage (its header's plan), in the
    structure's frame: d out of the wall (+u, toward the street), s along it (+v)."""
    u, v, y = leaf_tris[:, :, 0], -leaf_tris[:, :, 2], leaf_tris[:, :, 1]
    front, back = float(u.max()), float(u.min())
    jambs = [float(v.min()), float(v.max())]
    vm = (jambs[0] + jambs[1]) / 2
    sill, head = float(y.min()), float(y.max())
    way, why = stoop_way(parts, front, vm, sill, free)
    if way is None:
        return None, why
    r = lambda x: round(float(x), 3)
    plan = {
        'origin': [r(front), r(vm)], 'outward': [1, 0], 'along': [0, 1],
        # The opening a hair wider than the leaf, so the leaf's own edges lie within it.
        'jambs': [r(jambs[0] - vm - 0.01), r(jambs[1] - vm + 0.01)], 'sill': r(sill), 'head': r(head),
        'leaf': {'front': 0, 'back': r(back - front), 's': [r(jambs[0] - vm), r(jambs[1] - vm)], 'foot': r(sill), 'top': r(head)},
        'hinge': 'right', 'pair': bool(jambs[1] - jambs[0] > PAIR_OVER_M),
        # The vestibule reaches out to the leaf's face: the model has no reveal where the leaf stood.
        'revealBack': -0.005, 'leafBoxBack': r(back - front - 0.03),
        'leafMaterials': sorted(mats),
        'way': way,
        'grades': {'leaf': 'inferred', 'hinge': 'reconstructed', 'swing': 'reconstructed', 'vestibule': 'reconstructed', 'treads': 'inferred'},
    }
    return plan, ''


def wheres(scene: str) -> set[str]:
    out = set()
    folder = ROOT / f"data/humans/instances/{scene}"
    for f in sorted(folder.glob("hi_*.json")):
        rec = json.loads(f.read_text())
        if rec.get("display") != "shown":
            continue
        for v in (rec.get("behaviour") or {}).get("day") or []:
            for s in v.get("spans") or []:
                if s.get("indoors") and s.get("where") and not s.get("away"):
                    out.add(s["where"])
    inside = ROOT / f"data/humans/inside_{scene}.json"
    if inside.exists():
        out.update(p['home'] for p in json.loads(inside.read_text()).get('people', []))
    return out


FRONT_SKIRT_M = 0.35        # the doorway's line: its half-width and a skirt's either side
FRONT_REACH_M = 12.0        # how far before the front the model's building is read
FRONT_GROUND_M = 0.1        # a top lower than this is ground work (walk stones, kerbs), not in the way
FRONT_GAP_M = 0.6          # open ground this wide in the doorway's line ends what is built before the front
FRONT_PASSED = ('fence', 'gate', 'walk', 'pier', 'kerb', 'curb')   # the lot's front line and its walk: passed by a gate, walked on


def frame_house_front_door(sc: dict):
    """A frame house record's own front door (k16_timber.py `frame_house` blocks): the first door
    hung on a block's east wall, the street side of a Prairie plan, as (u, v, clear width) in the
    model's plan, or None. An east wall runs from its block's (u1, v0) corner toward +v and a
    door's `centre_m` is measured along it (k16_timber.py SIDE_RUN, side_frame)."""
    fh = (((sc.get('attributes') or {}).get('frame_house') or {}).get('value') or {})
    for b in fh.get('blocks') or []:
        for w in b.get('walls') or []:
            if w.get('side') != 'east' or not w.get('doors'):
                continue
            u0, v0, u1, v1 = b['rect_uv']
            d = w['doors'][0]
            return float(u1), float(v0) + float(d['centre_m']), float(d.get('clear_width_m') or 1.0)
    return None


def prairie_doors(sc: dict, glb: Path, parts=None, got=None) -> tuple[list[dict], list[str]]:
    """Prairie plans run u toward the street. Read the built front leaf and stoop.

    A built leaf is a passage (T-3554): its plan (house-doors.js) hangs it to swing, and its
    way climbs the stoop read off the model; one answering stands at the way's foot. A draft's
    drawn door is hung the same way where its stoop reaches it. Draft houses without a door
    mesh (or whose drawn door no stoop reaches) keep an explicitly reconstructed entrance on
    that front, never a claim that the survey locates their door; its answering place stands
    on open ground before everything the model builds there (prairie_barriers.py).
    """
    poly = np.asarray(sc['footprint']['polygon'], dtype=float)
    parts = d1812.load_triangles(glb) if parts is None else parts
    # T-3554: where a body may stand, a skirt's width off whatever the model builds outside its walls.
    free = pb.standing(pb.mask(parts, poly) if got is None else got)
    leaves = [(name.lower(), t) for name, t in parts if name.lower() in LEAF_MATS]
    floor = float(val(sc, 'principal_floor_m') or 2.5)
    candidates = []
    if leaves:
        tris = np.concatenate([t for _, t in leaves])
        names = np.concatenate([[n] * len(t) for n, t in leaves])
        low = tris[:, :, 1].min(axis=1) < floor + .3
        tris, names = tris[low], names[low]
        centres = np.stack([tris[:, :, 0].mean(1), -tris[:, :, 2].mean(1)], 1)
        for group in d1812.clusters_within(centres, .8):
            uv = np.stack([tris[group][:, :, 0].ravel(), -tris[group][:, :, 2].ravel()], 1)
            lo, hi = uv.min(0), uv.max(0)
            if hi[1] - lo[1] >= .5:
                candidates.append(((lo + hi) / 2, hi[1] - lo[1], group))
    pl = sc['placement']
    angle = (90 + float(pl.get('rotation_deg') or 0)) % 360
    world = lambda u, v: dict(zip(('local_e', 'local_n'), (round(x, 2) for x in d1812.to_world(float(u), float(v), pl))))
    door = {'id': sc['id'] + ':front'}
    problems = []
    if candidates:
        (u, v), width, group = max(candidates, key=lambda x: x[0][0])
        plan, why = passage_plan(sc['id'], tris[group], parts, set(names[group]), free)
        drawn = set(names[group]) == {DRAFT_LEAF}
        if plan is None and not drawn:
            problems.append(f"{sc['id']}: its front leaf has no way up to it ({why})")
        elif plan is not None:
            foot = plan['way'][0]
            door.update({'leaf': world(u, v), 'step': world(foot[0], foot[1]), 'outward_deg': round(angle, 1),
                         'width_m': round(float(width), 2), 'passage': True,
                         'plan': {'name': 'Front door', **plan},
                         'reconstructed': 'Front leaf read from the built door material; the way up to it is read off the '
                                          "built stoop's treads (derive_doors_scene.py stoop_way), and one answering stands "
                                          "at its foot. The leaf opens and shuts as they pass (house-doors.js passages, "
                                          'T-3554); its hinge side and swing are reconstructed.'})
            return [door], problems
    if candidates and drawn:
        basis = ("The draft's drawn front door has no stoop in the draft that reaches it, so it is not hung to swing; "
                 'the answering place is on open ground before the front. Walking and doorstep use are reconstructed.')
    elif candidates:
        basis = 'Front leaf read from the built door material; the answering place is beyond its stoop. Walking and doorstep use are reconstructed.'
    elif (hung := frame_house_front_door(sc)) is not None:
        u, v, width = hung
        basis = ("The front door the frame house record hangs on its street wall (frame_house blocks), which "
                 'the model builds there; the answering place is at the foot of what the model builds before it. '
                 'Walking and doorstep use are reconstructed.')
    else:
        u, v = float(poly[:, 0].max()), float((poly[:, 1].min() + poly[:, 1].max()) / 2)
        width = 1.2
        basis = 'No separate front leaf is modelled in this draft. A reconstructed entrance is placed at the middle of the street-facing front (the plan u axis); the survey does not attest a doorway here.'
    out_u = max(u, float(poly[:, 0].max()))
    # T-3553 (Kevin, 2026-11-13): Find on Mrs. Grey set him down inside 2010 Prairie. Its entrance
    # was put on the footprint's front, which stands inside the front block the model builds
    # before it: a hollow room the barrier mask (walls only) reads as free. So the answering place
    # stands past everything the model builds above the ground in the doorway's line and joined
    # to the front (front blocks, bays, porches and their steps), not a gap further on (the lot's
    # fence and gate posts, passed by its gate).
    spans = []
    for name, t in parts:
        low = name.lower()
        if low == 'stoop_stone':
            pts = t.reshape(-1, 3)
            near = pts[(np.abs(-pts[:, 2] - v) < max(width, 2.5)) & (pts[:, 0] >= u)]
            if len(near):
                out_u = max(out_u, float(near[:, 0].max()))
            continue
        if any(k in low for k in FRONT_PASSED):
            continue
        tu, tv, ty = t[:, :, 0], -t[:, :, 2], t[:, :, 1]
        hw = width / 2 + FRONT_SKIRT_M
        keep = ((tv.max(1) >= v - hw) & (tv.min(1) <= v + hw) & (ty.max(1) > FRONT_GROUND_M)
                & (tu.max(1) >= u - .05) & (tu.min(1) <= u + FRONT_REACH_M))
        spans += zip(tu.min(1)[keep].tolist(), tu.max(1)[keep].tolist())
    for lo, hi in sorted(spans):
        if lo > out_u + FRONT_GAP_M:
            break
        out_u = max(out_u, hi)
    # T-3554: the answering place stands clear of whatever the model builds before this front
    # (a draft's front rooms and bays reach past its footprint), a skirt's width off it.
    step_u = out_u + STEP_M
    for _ in range(400):
        if free(step_u, v):
            break
        step_u += pb.CELL_M
    step_u = round(step_u, 2)
    door.update({'leaf': world(u, v), 'step': world(step_u, v), 'outward_deg': round(angle, 1),
                 'width_m': round(float(width), 2), 'reconstructed': basis})
    return [door], problems


def back_doors(scene: str) -> dict[str, dict]:
    """T-3554: each 1904 house's back door (data/back_yards/<scene>.json, laid by
    lay_prairie_1904_back_yards.py on its built rear wall), as a passage back-yards.js hangs:
    its leaf swings out over its landing, and its way runs up the middle of its stoop. One
    answering stands STEP_M beyond the stoop's foot."""
    f = ROOT / f"data/back_yards/{scene}.json"
    if not f.exists():
        return {}
    out = {}
    for lot in json.loads(f.read_text()).get("lots", []):
        for d in lot.get("doors") or []:
            sid = d.get("structure")
            if not sid or d.get("leaf") is False or not d.get("stoop") or sid in out:
                continue
            th = math.radians(float(d.get("facing_deg") or 0))
            run = float(d["stoop"].get("run_m") or 0.3)
            at = lambda s: {"local_e": round(d["e"] + math.sin(th) * s, 2), "local_n": round(d["n"] + math.cos(th) * s, 2)}
            out[sid] = {"id": sid + ":back", "leaf": at(0.0), "step": at(run + STEP_M),
                        "outward_deg": round(float(d.get("facing_deg") or 0) % 360, 1), "width_m": round(float(d.get("width_m") or 0.95), 2),
                        "passage": True, "back": True,
                        "reconstructed": "The kitchen door on the rear wall, as the back yards lay it (" + d["id"] + "); it swings out "
                                         "over its landing and shuts as people pass (back-yards.js, house-doors.js passages, "
                                         "T-3554), and the way is the middle of its stoop."}
    return out


def box_row(rid: str, e: float, n: float, bearing: float, u0: float, u1: float, half: float, what: str) -> dict:
    """A barrier row for one built box beside no house model (a back stoop, a street-front stoop
    or mounting block): its plan runs u out along `bearing` from (e, n), v along its face, the
    box covering u0..u1 out and `half` either side, on prairie_barriers' cell grid (whole cells,
    never less than the box)."""
    c = pb.CELL_M
    ni, nj = max(1, math.ceil((u1 - u0) / c - 1e-6)), max(1, math.ceil(2 * half / c - 1e-6))
    return {"structure": rid, "placement": {"local_e": round(e, 3), "local_n": round(n, 3),
                                            "rotation_deg": round((bearing - 90) % 360, 3)},
            "barrier": {"cell": c, "u0": round(u0 + c / 2, 3), "v0": round(-half + c / 2, 3), "count": 1,
                        "rects": f"0 {ni} 0 {nj}"},
            "what": what}


def stoop_rows(scene: str) -> list[dict]:
    """T-3554 (owner, 2026-11-13, of a maid standing half inside the bottom steps of a front stoop:
    "she cannot stand where there are stairs like that, no one should be able to"): the stairs no
    house model carries, as barrier rows. 1904: each back door's stoop as the back yards lay it
    (landing and flight, from the wall out run_m, STOOP_PAD_M more for the flight the renderer
    fits to the ground there). 1835: every part of a street-front fitting standing higher than a
    riser (prairie_barriers.KNEE_M: a stoop's landing and step, a mounting block's two steps, a
    tie rail), not the wagon aprons' planks laid on the walk."""
    rows = []
    if scene == "1904":
        f = ROOT / "data/back_yards/1904.json"
        for lot in json.loads(f.read_text()).get("lots", []) if f.exists() else []:
            for d in lot.get("doors") or []:
                st = d.get("stoop") or {}
                if not st.get("run_m") or not all(isinstance(d.get(k), (int, float)) for k in ("e", "n", "facing_deg")):
                    continue
                rows.append(box_row(d["id"] + ":stoop", d["e"], d["n"], float(d["facing_deg"]), 0.0,
                                    float(st["run_m"]) + STOOP_PAD_M, max(float(st.get("width_m") or 1.2), float(d.get("width_m") or 0.95)) / 2,
                                    "back stoop"))
    if scene == "1835":
        fits = []
        for f in sorted((ROOT / "data/frontage").glob("*.json")):
            doc = json.loads(f.read_text())
            if isinstance(doc, dict) and str(doc.get("scene", scene)) == scene:
                fits += doc.get("fittings") or []
        for fit in fits:
            for part in fit.get("parts") or []:
                at = part.get("at_local_enu_m")
                if not at or float(part.get("top_m") or 0) <= pb.KNEE_M or not part.get("len_m"):
                    continue
                depth = float(part.get("depth_m") or part.get("thick_m") or 0.1)
                rows.append(box_row(f"{fit['id']}:{part['part']}", at[0], at[1], float(fit.get("facade_bearing_deg") or 0),
                                    -depth / 2, depth / 2, float(part["len_m"]) / 2, fit.get("kind") or "fitting"))
    return rows


def val(sc: dict, name: str):
    v = (sc.get("attributes") or {}).get(name)
    return v["value"] if isinstance(v, dict) and "value" in v else v


def glessner_doors(sc: dict) -> list[dict]:
    frame = val(sc, "frame_ft")
    L, D = float(frame["length_ft"]), float(frame["depth_ft"])
    pl = sc["placement"]
    th = math.radians(float(pl.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)

    def world(W: float, S: float) -> dict:
        e, n = d1812.to_world((L - W) * FT, (D - S) * FT, pl)
        return {"local_e": round(e, 2), "local_n": round(n, 2)}

    def outward(du: float, dv: float) -> float:
        de, dn = du * c + dv * s, -du * s + dv * c
        return round((math.degrees(math.atan2(de, dn)) + 360) % 360, 1)

    detail = val(sc, "v4_detail") or {}
    out = []
    stair = detail.get("north_court_service_stair")
    court = next((o for o in (val(sc, "openings_court_north") or {}).get("items", []) if o.get("kind") == "door"), None)
    if stair and court:
        W = sum(stair["flight_W"]) / 2
        foot = max(stair["flight_S"])
        out.append({"id": "glessner_house:service_stair", "leaf": world(W, foot), "step": world(W, foot + STEP_M / FT),
                    "outward_deg": outward(0, -1), "width_m": round((max(stair["flight_W"]) - min(stair["flight_W"])) * FT, 2),
                    "passage": True,
                    "reconstructed": "up the north court service stair and its landing to the door (" + court["what"]
                                     + "), which opens and shuts as they pass (house-doors.js passages, T-3524); "
                                     "the line walked is the flight's middle"})
    alcove = detail.get("north_entry_alcove")
    if alcove:
        # The front steps (masonry_house_v4_detail.py north_entry) run out over the walk on the
        # arch's west half, from its west jamb to the cheek; one answering stands out past them.
        W = (max(alcove["opening_W"]) + max(alcove["cheek_W"])) / 2
        out_S = -(float(alcove["front_run_ft"]) + STEP_M / FT)
        out.append({"id": "glessner_house:north_entry", "leaf": world(W, alcove["back_S"] / 2), "step": world(W, out_S),
                    "outward_deg": outward(0, 1), "width_m": round((max(alcove["opening_W"]) - min(alcove["opening_W"])) * FT, 2),
                    "passage": True,
                    "reconstructed": "up the alcove's front steps and the stair inside it to its side door, which opens "
                                     "and shuts as they pass (house-doors.js passages, T-3524); the line walked is the steps' middle"})
    stable = next((o for o in (val(sc, "openings_stable_doors") or {}).get("items", []) if o.get("kind") == "doors"), None)
    if stable:
        W = sum(stable["at"]) / 2
        out.append({"id": "glessner_house:stable", "leaf": world(W, 0.0), "step": world(W, -STEP_M / FT),
                    "outward_deg": outward(0, 1), "width_m": round((max(stable["at"]) - min(stable["at"])) * FT, 2)})
    return out


BARRIERS = "prairie_barriers/3"   # bump when prairie_barriers.py reads a model differently
FLOORS = "prairie_floors/5"       # bump when prairie_barriers.floor reads a model differently

_MANIFEST: dict | None = None


def model_id(sc: dict, glb: Path) -> tuple[str, str]:
    """T-3596: which model a reading was taken from, as (field, hash).

    Named by the hash of what BUILT it — assets/manifest.json's `inputs_sha256`, the same
    hash the staleness gate compares (generators/mesh_inputs.py) — and not by the file's
    bytes. The bytes are not reproducible across machines: CI's content build re-baked 59
    unchanged 1835 models on 2026-11-14 and came out with the same geometry and a few
    last-digit TEXCOORD floats different (bates_auction_room: 2 bytes of 63,120, all in one
    UV view), and every such model's `asset_sha256` then said doors_1835.json was stale.
    This tool reads positions, never UVs, so a re-bake of the same inputs reads the same
    doors. An asset the manifest does not list keeps the old byte hash, under its old name."""
    global _MANIFEST
    if _MANIFEST is None:
        try:
            _MANIFEST = json.loads((ROOT / "assets/manifest.json").read_text()).get("assets", {})
        except (OSError, ValueError):
            _MANIFEST = {}
    name = sc["asset"].split("/", 1)[1] if sc["asset"].startswith("gltf/") else sc["asset"]
    h = (_MANIFEST.get(name) or {}).get("inputs_sha256")
    return ("model_inputs_sha256", h) if h else ("asset_sha256", d1812.sha256(glb))


def barrier_cache(scene: str) -> dict:
    """The walls the last run read, by structure, kept while the model, its placement and its
    footprint are unchanged (reading them is the slow part of this tool)."""
    f = ROOT / f"data/humans/doors_{scene}.json"
    try:
        old = json.loads(f.read_text())
    except (OSError, ValueError):
        return {}
    if old.get("barriers_by") != BARRIERS:
        return {}
    return {r["structure"]: r for r in old.get("structures", []) + old.get("barriers", []) if "barrier" in r or "floor" in r}


def barrier_of(sc: dict, glb: Path, h: str, cache: dict, parts=None, got=None) -> dict | None:
    key = hashlib.sha256(json.dumps([BARRIERS, h, d1812._placement(sc), sc["footprint"]["polygon"]], sort_keys=True).encode()).hexdigest()[:16]
    hit = (cache.get(sc["id"]) or {}).get("barrier")
    if hit and hit.get("key") == key:
        return hit
    if got is None:
        got = pb.mask(d1812.load_triangles(glb) if parts is None else parts, sc["footprint"]["polygon"])
    plan = pb.plan_of(got)
    return {"key": key, **plan} if plan else None


def floor_of(sc: dict, glb: Path, h: str, cache: dict, parts=None) -> dict | None:
    """The owner, 2026-11-14 ("Anywhere there are stairs I should be able to climb"): the tops
    of the house's stoops and porches the visitor climbs (prairie_barriers.floor), cached like
    its barrier."""
    key = hashlib.sha256(json.dumps([FLOORS, h, sc["footprint"]["polygon"]], sort_keys=True).encode()).hexdigest()[:16]
    hit = (cache.get(sc["id"]) or {}).get("floor")
    if hit and hit.get("key") == key:
        return hit
    plan = pb.floor_plan(pb.floor(d1812.load_triangles(glb) if parts is None else parts, sc["footprint"]["polygon"]))
    return {"key": key, **plan} if plan else None


def barrier_rows(scene: str, rows: list, cache: dict) -> list[dict]:
    """T-3554: the other built Prairie Avenue houses' barriers, which no day goes into but a
    neighbour's day walks beside."""
    have = {r["structure"] for r in rows}
    out = []
    for f in sorted((ROOT / f"data/sidecars/{scene}").glob("*.json")):
        sid = f.stem
        if sid in have or "prairie" not in sid or sid == "glessner_house":
            continue
        try:
            sc = json.loads(f.read_text())
        except ValueError:
            continue
        if not isinstance(sc, dict) or not sc.get("asset") or not (sc.get("footprint") or {}).get("polygon"):
            continue
        glb = ROOT / "assets" / sc["asset"]
        if not glb.exists():
            continue
        h = model_id(sc, glb)[1]
        plan = barrier_of(sc, glb, h, cache)
        fl = floor_of(sc, glb, h, cache)
        if plan or fl:
            row = {"structure": sid, "placement": d1812._placement(sc)}
            if plan:
                row["barrier"] = plan
            if fl:
                row["floor"] = fl
            out.append(row)
    return out


def derive(scene: str) -> tuple[dict, list[str]]:
    rows, problems = [], []
    backs = back_doors(scene) if scene == "1904" else {}
    cache = barrier_cache(scene) if scene == "1904" else {}
    for sid in sorted(wheres(scene)):
        f = ROOT / f"data/sidecars/{scene}/{sid}.json"
        if not f.exists():
            problems.append(f"{sid}: a day names it, but {scene} has no such building")
            continue
        sc = json.loads(f.read_text())
        if sid == "glessner_house":
            doors, (hk, h) = glessner_doors(sc), (None, None)
        else:
            glb = ROOT / "assets" / sc["asset"]
            if not glb.exists():
                problems.append(f"{sid}: its model {sc['asset']} is not built")
                continue
            hk, h = model_id(sc, glb)
            plan = floor = None
            if scene == '1904':
                parts = d1812.load_triangles(glb)
                got = pb.mask(parts, sc['footprint']['polygon'])
                doors, p = prairie_doors(sc, glb, parts, got)
                plan = barrier_of(sc, glb, h, cache, parts, got)
                floor = floor_of(sc, glb, h, cache, parts)
            else:
                doors, p = d1812.doors_of(sc, glb)
            problems += p
            doors = [{k: (round(float(v), 2) if isinstance(v, float) or type(v).__name__.startswith("float") else v)
                      for k, v in x.items()} for x in doors]
            for x in doors:
                for k in ("leaf", "step"):
                    x[k] = {a: round(float(b), 2) for a, b in x[k].items()}
            if sid in backs:
                doors.append(backs[sid])
        if not doors:
            problems.append(f"{sid}: no door found; who is in it cannot be asked for")
            continue
        row = {"structure": sid, "name": sc.get("name") or sid, "placement": d1812._placement(sc), "doors": doors}
        if h:
            row[hk] = h
        if plan:
            # T-3554: what the model builds outside its walls (stoop, area walls, railings,
            # bays), which a day's walk keeps a skirt's width off (human-days.js, human-spacing.js).
            row["barrier"] = plan
        if sid != "glessner_house" and floor:
            # The tops of its stoop and porches, which the visitor climbs (walker.js decks).
            row["floor"] = floor
        rows.append(row)
    out = {
        "format": FORMAT,
        "ticket": "T-3516",
        "generated_by": "tools/derive_doors_scene.py",
        "note": f"Where each {scene} building a drawn person's day goes into is entered, and where one who answers stands. Asking at a door, going in and out: renderers/web/js/human-days.js.",
        "structures": rows,
    }
    if scene == "1904":
        out["barriers_by"] = BARRIERS
        out["barriers_note"] = ("T-3554: a `barrier` is what a house model builds outside its footprint between a "
                                "knee and a head over the ground (tools/prairie_barriers.py): plan rectangles of its "
                                "cells, `rects` four integers each (i0 i1 j0 j1, half-open), cell (i, j) centred on "
                                "u0 + i*cell, v0 + j*cell of the model's plan (u = x, v = -z), turned into local E/N "
                                "by the placement. `barriers` carries them for the built Prairie houses no day goes into.")
        out["barriers"] = barrier_rows(scene, rows, cache)
        out["floors_by"] = FLOORS
        out["floors_note"] = ("The owner, 2026-11-14 (\"Anywhere there are stairs I should be able to climb\"): a "
                              "`floor` is the tops a house model builds outside its walls that a visitor climbs, its "
                              "stoop's treads and landing and its porches (tools/prairie_barriers.py floor): `rects`, "
                              "plan rectangles of one height, five integers each (i0 i1 j0 j1 half-open, then the top in "
                              "centimetres over the model's ground), and `walls`, the same for the rails and cheeks "
                              "beside them, standing past any step. house-floors.js lays them as walker decks.")
    stoops = stoop_rows(scene)
    if stoops:
        out["stoops_note"] = ("T-3554 (owner, 2026-11-13: \"no one should be able to\" stand in stairs): the stairs "
                              "no house model carries, as `barriers` rows of one box each (derive_doors_scene.py "
                              "stoop_rows; `what` says which): " + ("the back yards' stoops." if scene == "1904" else
                              "the street fronts' stoops, mounting blocks and tie rails."))
        out["barriers"] = out.get("barriers", []) + stoops
    return out, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    for scene in SCENES:
        out = ROOT / f"data/humans/doors_{scene}.json"
        data, problems = derive(scene)
        for p in problems:
            print(f"doors_{scene}: {p}", file=sys.stderr)
        bad |= bool(problems)
        text = json.dumps(data, indent=1) + "\n"
        if args.check:
            if not out.exists() or out.read_text() != text:
                print(f"FAIL doors_{scene}: {out.relative_to(ROOT)} is not what the records say; run python3 tools/derive_doors_scene.py", file=sys.stderr)
                bad = 1
                continue
            n = sum(len(s["doors"]) for s in data["structures"])
            print(f"doors_{scene}: {n} doors on {len(data['structures'])} buildings")
        else:
            out.write_text(text)
            print(f"wrote {out.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
