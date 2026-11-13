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
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import derive_doors_1812 as d1812  # noqa: E402

FORMAT = "c4d-doors-scene/1"
SCENES = ("1835", "1904")
FT = 0.3048
STEP_M = d1812.STEP_M

# T-3554 (owner, 2026-11-12: *"make sure they are openable and closeable for a person to enter
# and make sure that people can walk up the stairs instead of vanishing into the staircase"*).
# A 1904 house's built front leaf becomes a passage (house-doors.js): it is hung to swing, and
# the way up to it is read off the model's own stoop, tread by tread.
LEAF_MATS = ('door_leaf', 'door', 'door_panel')
WAY_CELL_M = 0.1           # the grid the way is found on
WAY_RISE_M = 0.26          # the most one step of the way climbs (a riser here is 0.15-0.19 m)
WAY_KNEE_M = 0.25          # anything from this far over the tread ...
WAY_HEAD_M = 1.8           # ... to a head's height over it is in the way
WAY_SKIRT_M = 0.35         # a skirt's half-width: the way keeps this far off a drop or a rail
WAY_EASE_M = 0.12          # house-doors.js RISER_EASE_M: the rise eased this far each side
WAY_GROUND_M = 0.12        # a top lower than this is the ground (the caller's ground answers)
WAY_BEFORE_M = 0.45        # house-doors.js PASSAGE_BEFORE_M: where one stops before the leaf
PAIR_OVER_M = 1.6          # an opening wider than this is hung as a pair of leaves
GROUND_MATS = ('turf', 'earth', 'lawn', 'grass')


def stoop_way(parts, front_u: float, vm: float, sill: float):
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
        if ground[cur] and not skirt[cur] and math.dist(cur, start) * WAY_CELL_M >= STEP_M:
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


def passage_plan(sid: str, leaf_tris, parts, mats) -> tuple[dict | None, str]:
    """A built front leaf as house-doors.js hangs a passage (its header's plan), in the
    structure's frame: d out of the wall (+u, toward the street), s along it (+v)."""
    u, v, y = leaf_tris[:, :, 0], -leaf_tris[:, :, 2], leaf_tris[:, :, 1]
    front, back = float(u.max()), float(u.min())
    jambs = [float(v.min()), float(v.max())]
    vm = (jambs[0] + jambs[1]) / 2
    sill, head = float(y.min()), float(y.max())
    way, why = stoop_way(parts, front, vm, sill)
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


def prairie_doors(sc: dict, glb: Path) -> tuple[list[dict], list[str]]:
    """Prairie plans run u toward the street. Read the built front leaf and stoop.

    A built leaf is a passage (T-3554): its plan (house-doors.js) hangs it to swing, and its
    way climbs the stoop read off the model; one answering stands at the way's foot. Draft
    houses without a door mesh keep an explicitly reconstructed entrance on that front, never
    a claim that the survey locates their door.
    """
    poly = np.asarray(sc['footprint']['polygon'], dtype=float)
    parts = d1812.load_triangles(glb)
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
        plan, why = passage_plan(sc['id'], tris[group], parts, set(names[group]))
        if plan is None:
            problems.append(f"{sc['id']}: its front leaf has no way up to it ({why})")
        else:
            foot = plan['way'][0]
            door.update({'leaf': world(u, v), 'step': world(foot[0], foot[1]), 'outward_deg': round(angle, 1),
                         'width_m': round(float(width), 2), 'passage': True,
                         'plan': {'name': 'Front door', **plan},
                         'reconstructed': 'Front leaf read from the built door material; the way up to it is read off the '
                                          "built stoop's treads (derive_doors_scene.py stoop_way), and one answering stands "
                                          "at its foot. The leaf opens and shuts as they pass (house-doors.js passages, "
                                          'T-3554); its hinge side and swing are reconstructed.'})
            return [door], problems
    if candidates:
        basis = 'Front leaf read from the built door material; the answering place is beyond its stoop. Walking and doorstep use are reconstructed.'
    else:
        u, v = float(poly[:, 0].max()), float((poly[:, 1].min() + poly[:, 1].max()) / 2)
        width = 1.2
        basis = 'No separate front leaf is modelled in this draft. A reconstructed entrance is placed at the middle of the street-facing front (the plan u axis); the survey does not attest a doorway here.'
    out_u = max(u, float(poly[:, 0].max()))
    for name, t in parts:
        if name.lower() != 'stoop_stone':
            continue
        pts = t.reshape(-1, 3)
        near = pts[(np.abs(-pts[:, 2] - v) < max(width, 2.5)) & (pts[:, 0] >= u)]
        if len(near):
            out_u = max(out_u, float(near[:, 0].max()))
    door.update({'leaf': world(u, v), 'step': world(out_u + STEP_M, v), 'outward_deg': round(angle, 1),
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


def derive(scene: str) -> tuple[dict, list[str]]:
    rows, problems = [], []
    backs = back_doors(scene) if scene == "1904" else {}
    for sid in sorted(wheres(scene)):
        f = ROOT / f"data/sidecars/{scene}/{sid}.json"
        if not f.exists():
            problems.append(f"{sid}: a day names it, but {scene} has no such building")
            continue
        sc = json.loads(f.read_text())
        if sid == "glessner_house":
            doors, h = glessner_doors(sc), None
        else:
            glb = ROOT / "assets" / sc["asset"]
            if not glb.exists():
                problems.append(f"{sid}: its model {sc['asset']} is not built")
                continue
            h = d1812.sha256(glb)
            doors, p = prairie_doors(sc, glb) if scene == '1904' else d1812.doors_of(sc, glb)
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
            row["asset_sha256"] = h
        rows.append(row)
    return {
        "format": FORMAT,
        "ticket": "T-3516",
        "generated_by": "tools/derive_doors_scene.py",
        "note": f"Where each {scene} building a drawn person's day goes into is entered, and where one who answers stands. Asking at a door, going in and out: renderers/web/js/human-days.js.",
        "structures": rows,
    }, problems


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
