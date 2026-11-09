#!/usr/bin/env python3
"""Lay out the 1904 district's back and side yards: back doors and their steps, paved terraces,
walks to the coach house, the alley and the front, gangways, drying yards and gardens (T-3488).

    python3 tools/lay_prairie_1904_back_yards.py              # write data/back_yards/1904.json
    python3 tools/lay_prairie_1904_back_yards.py --check      # the committed file is what this writes,
                                                              # and nothing it lays stands in a building
    python3 tools/lay_prairie_1904_back_yards.py --report     # one line a lot: what was laid and why not
    python3 tools/lay_prairie_1904_back_yards.py --self-test  # each fault the check refuses, planted

THE ASK. The owner, 2026-11-07: *"for the 1904 backyards i imagine there are patios and
entertaining space near the rear doors and walkways to the carriage houses and to the front steps
and maybe in gangways etc so lay those out also for 1904 with correct textured surfaces as you lay
out the gardens. dont wildly invent things, a lot has been done for pullman, so dont change things
that are documented, but enhance them logically based on the backyards and rear and side areas of
the houses"*; and of the gardens: *"if you see or have knowledge of backyard gardens in 1904
include them"*.

WHAT THE SOURCES SAY (the research note of 2026-11-07, docs/RESEARCH/prairie_1904_back_yards.md).
No source read names a kitchen garden, a tennis lawn, an arbor or a rose garden on any lot of the
drawn district. What they do attest is lawns and shade trees on the SIDE yards of the double lots
(Field, Allerton, Doane, Pullman's 18th Street court), vines on walls (Glessner's court, Pullman),
glass at Pullman and Field, brick yard walls on the alley (2005, 2010, 2036, 2140, Sanborn 1911),
and stables on the alley with 5-18 m of yard between them and the house. The 1900 census puts a
coachman's family over many stables and a laundress in 16 of the carded households: the back yard
was the kitchen's and the stable's working court. So this tool lays a working court, not a
pleasure garden, and keeps whatever the pictures and the K12/K14 kits already built:

  * a BACK DOOR on the main house's rear wall where its model has none (no worked model was built
    with one; every house of the period had a kitchen door), placed on a stretch of wall with no
    window in the door's way, its sill at the house's first floor or 1.5 m, whichever is lower, and
    its STEPS (a landing and straight flight, wood on a frame house, stone on a masonry one);
  * a PAVED TERRACE at the foot of those steps (brick laid herringbone, or stone flags on a stone
    front), sized to the lot: a few metres on a narrow lot, an outdoor room of up to 6 x 5 m where a
    double lot gives the house a side yard;
  * WALKS on the yard's own routes, found on the lot's plan and laid straight with as few turns as
    the ground allows: from the terrace to the coach house's yard door or to its paved workyard
    (K12), to the alley gate where there is no coach house, and down the side passage (the
    GANGWAY) to the side service walk the K14 kit laid, or to the front walk at the stoop's foot;
  * a DRYING YARD of trodden earth with two clothes posts where the 1900 census enumerates a
    laundress in the household, and on small lots;
  * a KITCHEN GARDEN of a few dug beds against the sunny fence on the modest lots only (Indiana and
    Calumet, frame and flat buildings), seeded so most have none: the only place one appears, and
    reconstructed (no source names one).
The lots the sources draw are left as drawn: Glessner's court (1800 Prairie, its own model and the
HABS lawn and drive), Pullman's house lot and glasshouse ground (1729 Prairie, 1800 Calumet: the
K13 grounds and drives), and Field's south lawn (1905) take no paving here.

Every piece is RECONSTRUCTED (docs/LIBERTIES.md L-prairie-back-yards-3488) except the drying yards
of a household whose laundress the census names, which are inferred from that enumeration. Each
lot is seeded by its parcel id, so a re-run lays the same yard and no two neighbours match.

WHAT IT KEEPS CLEAR. The district's plan raster is read as tools/plant_prairie_1904_front_yards.py
reads it (every 1904 model and trace on a 0.25 m raster), plus each structure's own cells, windows
and doors. A surface never runs under any building's wall or a fence, coping or stoop (0.05 m off
them), never leaves its lot, and never lies over a walk the kits already built (it stops at it);
a walk is laid only where its whole width fits; a front-yard plant's crown is a wall to it.
`--check` holds the committed file to those rules against the models as they stand now (a rebake
that moves a wall over a terrace fails and names it), and to being what this tool writes.

It writes data/back_yards/1904.json, which renderers/web/js/back-yards.js draws.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import random
import re
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import plant_prairie_1904_front_yards as F  # noqa: E402

GRID = ROOT / "data" / "street_grid" / "1904.json"
SIDECARS = ROOT / "data" / "sidecars" / "1904"
STRUCTURES = ROOT / "data" / "structures"
HOUSEHOLDS = ROOT / "data" / "residents_1904" / "households"
FRONT = ROOT / "data" / "front_yards" / "1904.json"
OUT = ROOT / "data" / "back_yards" / "1904.json"
LIBERTY = "L-prairie-back-yards-3488"
TICKET = "T-3488"
RES = 0.25                 # the lot raster, metres a cell (the district raster's)
WALL_GAP_M = 0.05          # a surface's edge off a building's wall, a fence or a stoop
GLASS_MATS = ("glass", "draft_glass", "k12_glass")
TURF_MATS = ("yard_turf", "turf", "lawn")
RISER_M = 0.18             # a back step's rise
TREAD_M = 0.28             # ... and its going
LANDING_M = 1.1            # the landing at the door, out from the wall, where the flight is 3 risers or more
SILL_MAX_M = 1.5           # a back door stands no higher than this over the house's bed
DOOR_W_M = 0.95
DOOR_H_M = 2.2
GRADE_DOOR_H_M = 2.0       # a kitchen door at grade, under a high first floor's windows
WINDOW_CLEAR_M = 0.3       # a back door's leaf stands this far clear of a window's glass, in plan
SURFACE_LIFT_M = 0.03      # a yard surface's top over the terrain
TURF_LIFT_M = 0.05         # ... over a kit's baked lawn (K14's LAWN_Y 0.035), so it is not buried in it
TURN_COST = 6.0            # a walk's turn costs this many cells of straight run
MIN_GANGWAY_M = 0.9        # a side passage narrower than this takes no gangway
GANGWAY_REACH_M = 3.5      # a gangway turns into the front yard to a front walk no farther than this from the passage
# The lots whose back and side yards the sources draw, and whose models already build them: no
# paving here. Each says why, for the report and the file.
LEFT_AS_DRAWN = {
    "prairie_1800": "The Glessner court: its own model draws the HABS lawn and carriage drive, and "
                    "the museum records the 1887 fountain and flower beds as dropped.",
    "prairie_1729": "The Pullman house lot: the K13 grounds, drives and terraces are drawn from the "
                    "1894 plate and the Detroit Publishing views.",
    "calumet_1800": "The Pullman glasshouse ground: drawn from the Inland Architect plate of 1894 and "
                    "Lowe's print of c. 1897.",
    "prairie_1905": "The Field south lawn: 'a spacious lawn and scattered shade-trees' (Artistic "
                    "Houses, 1883), open still in the c. 1905 photograph; no paving is recorded.",
}
# Materials: the texture ids are assets/textures/prairie_1904_pbr/manifest.json's.
MATERIALS = {
    "yard_brick": {"texture": "yard_brick_herringbone", "tile_m": 1.782, "label": "brick paving, laid herringbone"},
    "flags": {"texture": "bluestone_flags", "tile_m": 2.4, "label": "stone flagging"},
    "cement": {"texture": "portland_cement_walk", "tile_m": 1.83, "label": "Portland cement walk"},
    "cinder": {"texture": "earth_and_cinders", "tile_m": 4.0, "label": "cinders"},
    "gravel": {"texture": "pea_gravel", "tile_m": 1.0, "label": "gravel"},
    "trodden": {"texture": "beaten_earth", "tile_m": 3.0, "label": "trodden earth"},
    "loam": {"texture": "garden_loam", "tile_m": 2.0, "label": "dug garden soil"},
}
KIND_WORDS = {
    "rear_terrace": "paved terrace at the back door",
    "yard_walk": "walk across the yard",
    "coach_walk": "walk to the coach house",
    "alley_walk": "walk to the alley gate",
    "gangway": "gangway down the side passage",
    "front_walk": "walk round to the front steps",
    "drying_yard": "drying yard",
    "garden_bed": "kitchen garden bed",
}
# Crops a small 1904 city kitchen garden grows on 1 July (the same kinds gardens.js grows for the
# 1812 officers' garden, so their season rows already exist there).
GARDEN_CROPS = ["cabbage", "pole_bean", "onion", "lettuce", "beet", "carrot"]


def seed_of(key: str) -> int:
    return int(hashlib.sha256(("back:" + key).encode()).hexdigest()[:8], 16)


def r2(x: float) -> float:
    return round(float(x), 2)


# ---------------------------------------------------------------- the district

class District:
    """The front-yard planter's district raster, plus each structure's own cells, glass and doors."""

    def __init__(self, laid=None):
        self.grid, self.parcels, self.plan, self.house, self.by_parcel = laid or F.lay_district()
        plan = self.plan
        self.owner = np.full(plan.tall.shape, -1, np.int32)     # which structure's wall stands on a cell
        self.turf = np.zeros(plan.tall.shape, bool)             # a kit's baked lawn
        self.sids: list[str] = []
        self.meta: dict[str, dict] = {}
        tracked = F.tracked_models()
        for f in sorted(SIDECARS.glob("*.json")):
            sc = json.loads(f.read_text())
            if "placement" not in sc or "asset" not in sc or "id" not in sc:
                continue
            pl = sc["placement"]
            if pl.get("local_e") is None:
                continue
            glb = F.ASSETS / sc["asset"]
            if f"assets/{sc['asset']}" not in tracked or not glb.exists():
                continue
            k = len(self.sids)
            self.sids.append(sc["id"])
            self.meta[sc["id"]] = self._meta(sc)
            self.meta[sc["id"]].update(self._lay(k, pl, F.read_glb(glb)))

    def _meta(self, sc):
        sid, arch = sc["id"], sc.get("archetype") or ""
        kind = "house"
        rec = STRUCTURES / f"{sid}.json"
        form = {}
        if rec.exists():
            r = json.loads(rec.read_text())
            for ph in r.get("phases", []):
                if ph.get("form"):
                    form = ph["form"]
        de = (form.get("draft_elevation") or {}).get("value") or {}
        if "coach" in sid or arch == "k12_coach_house" or de.get("kind") == "service":
            kind = "coach"
        if arch == "k13_conservatories":
            kind = "glass"
        frame = arch in ("k16_timber",) or (form.get("construction") or {}).get("value") in ("frame", "wood")
        stone = any(w in json.dumps(form.get("bays", {}))[:4000] for w in ("stone", "sandstone", "limestone",
                                                                             "granite"))
        wings = [w for w in ((form.get("rear_wings") or {}).get("value") or []) if isinstance(w, dict)]
        wing_floor = min([w["floor_m"] for w in wings if isinstance(w.get("floor_m"), (int, float))] or [None]) \
            if any(isinstance(w.get("floor_m"), (int, float)) for w in wings) else None
        return {"archetype": arch, "kind": kind, "frame": bool(frame), "stone": bool(stone),
                "wing_floor_m": wing_floor, "principal_floor_m": de.get("principal_floor_m")}

    def _lay(self, k, place, prims):
        plan = self.plan
        d = math.radians(place.get("rotation_deg") or 0.0)
        cd, sd = math.cos(d), math.sin(d)
        e, n = place["local_e"], place["local_n"]
        glass, doors = [], []
        tall = np.zeros(plan.tall.shape, bool)
        for mat, pos, idx in prims:
            we = e + pos[:, 0] * cd - pos[:, 2] * sd
            wn = n - pos[:, 0] * sd - pos[:, 2] * cd
            en = np.stack([we, wn], axis=1)
            y = pos[:, 1]
            tri, ty = en[idx], y[idx]
            lo, hi = ty.min(axis=1), ty.max(axis=1)
            name = mat.lower()
            if any(g in name for g in F.GROUND_MATS):
                if any(t in name for t in TURF_MATS):
                    plan.lay_triangles(self.turf, tri)
                continue
            stand = (lo < F.LOW_TOP_M) & (hi > F.FLAT_M) & (hi >= F.TALL_M)
            if stand.any():
                plan.lay_triangles(tall, tri[stand])
            if name in GLASS_MATS or name.endswith("_glass"):
                c = tri.mean(axis=1)
                for (ge, gn), a, b in zip(c, lo, hi):
                    glass.append((float(ge), float(gn), float(a), float(b)))
            if any(name.startswith(m) for m in F.DOOR_MATS):
                for i in range(len(tri)):
                    doors.append((float(tri[i, :, 0].mean()), float(tri[i, :, 1].mean()), float(lo[i]), float(hi[i])))
        self.owner[tall & (self.owner < 0)] = k
        # door leaves into one door each (their triangles' centres within 1.2 m)
        merged = []
        for de_, dn, lo, hi in doors:
            for g in merged:
                if math.hypot(de_ - g[0] / g[4], dn - g[1] / g[4]) < 1.2:
                    g[0] += de_; g[1] += dn; g[2] = min(g[2], lo); g[3] = max(g[3], hi); g[4] += 1
                    break
            else:
                merged.append([de_, dn, lo, hi, 1])
        return {"glass": np.asarray(glass, float).reshape(-1, 4),
                "doors": [(g[0] / g[4], g[1] / g[4], g[2], g[3]) for g in merged]}


def laundress_structures() -> dict[str, list[str]]:
    """structure id -> the household person ids the 1900 census enumerates as a laundress."""
    out: dict[str, list[str]] = {}
    for f in sorted(HOUSEHOLDS.glob("*.json")):
        h = json.loads(f.read_text())
        homes = [a.get("place_or_structure_id") for a in h.get("associated_with", [])
                 if a.get("kind") == "home" and a.get("resolves_to") == "structure"]
        who = [p["id"] for p in h.get("persons", [])
               if "laundress" in json.dumps(p.get("occupation") or "").lower()]
        if who:
            for sid in homes:
                if sid:
                    out.setdefault(sid, []).extend(who)
    return out


def front_plant_disks(lots) -> list[tuple[float, float, float]]:
    """Every front-yard plant's crown as a disk (e, n, r): a walk keeps off it."""
    out = []
    for lot in lots:
        for row in lot.get("shrubs", []) + lot.get("trees", []):
            r = (0.45 if row[2] in ("maple", "linden") else row[4] / 2) + 0.1
            out.append((row[0], row[1], r))
        for b in lot.get("beds", []):
            out.append((b[0], b[1], max(b[2], b[3]) + 0.2))
    return out


# ---------------------------------------------------------------- one lot, in its own frame

class Lot:
    """A parcel's ground resampled in its own frame: s along the street line, d into the lot."""

    def __init__(self, p, dist: District, disks):
        self.ok = False
        self.p = p
        fr = F.lot_frame(p)
        if fr is None:
            return
        self.A, self.su, self.nu, self.width = fr
        poly = np.asarray(p["polygon_local_m"], float)
        dd = (poly - self.A) @ self.nu
        ss = (poly - self.A) @ self.su
        self.depth = float(dd.max())
        # the frame's window covers the whole polygon (a lot on a curve runs past its street chord)
        s = np.arange(min(-1.0, float(ss.min()) - 1.0), max(self.width, float(ss.max())) + 1.0, RES) + RES / 2
        d = np.arange(min(-1.0, float(dd.min()) - 1.0), self.depth + 1.0, RES) + RES / 2
        self.S, self.D = np.meshgrid(s, d)          # rows run in d, columns in s
        E = self.A[0] + self.S * self.su[0] + self.D * self.nu[0]
        N = self.A[1] + self.S * self.su[1] + self.D * self.nu[1]
        self.E, self.N = E, N
        plan = dist.plan
        r = np.clip(np.floor((N - plan.n0) / RES).astype(int), 0, plan.h - 1)
        c = np.clip(np.floor((E - plan.e0) / RES).astype(int), 0, plan.w - 1)
        self.inlot = F.inside(E, N, poly)
        self.owner = dist.owner[r, c]
        self.house = dist.house[r, c]
        self.low = plan.low[r, c]
        self.paved = plan.paved[r, c]
        self.turf = dist.turf[r, c]
        self.other_lot = plan.lots[r, c] & ~self.inlot
        sids = dist.by_parcel.get(p["id"], set())
        self.sids = [sid for sid in dist.sids if sid in sids]
        self.meta = {sid: dist.meta[sid] for sid in self.sids}
        self.kidx = {sid: dist.sids.index(sid) for sid in self.sids}
        mains = [sid for sid in self.sids if self.meta[sid]["kind"] == "house"]
        if not mains:
            return
        area = {sid: int((self.owner == self.kidx[sid]).sum()) for sid in mains}
        self.main = max(mains, key=lambda x: (area[x], x))
        self.coaches = [sid for sid in self.sids if self.meta[sid]["kind"] == "coach"]
        self.C = self.solid(np.isin(self.owner, [self.kidx[x] for x in self.coaches])) if self.coaches else \
            np.zeros(self.S.shape, bool)
        # The main house's plan: the district's filled house raster (a model's walls closed and filled,
        # and the traced footprint where no model stands), the parts of it that hold the main model's
        # walls, less the coach house's.
        own = self.owner == self.kidx[self.main]
        comp, _n = ndimage.label(self.house & self.inlot & ~ndimage.binary_dilation(self.C, iterations=1))
        keep = np.unique(comp[own & (comp > 0)])
        self.H = np.isin(comp, keep[keep > 0]) | (own & self.inlot)
        if self.H.sum() < 20:
            return
        # walls: every structure's cells, this lot's or a neighbour's, and the traced houses
        self.walls = self.house | self.H | self.C
        for k in np.unique(self.owner[self.owner >= 0]):
            self.walls |= self.solid(self.owner == k)
        self.front = float(self.D[self.H].min())
        self.rear = float(self.D[self.H].max())
        self.s_lo, self.s_hi = float(self.S[self.H].min()), float(self.S[self.H].max())
        # front-yard plant crowns are walls to a walk
        self.crowns = np.zeros(self.S.shape, bool)
        for e, n, rr in disks:
            if abs(e - E.mean()) < 80 and abs(n - N.mean()) < 80:
                self.crowns |= (E - e) ** 2 + (N - n) ** 2 <= rr * rr
        # a wall's own low work (its plinth, a water table, a cellar light's sill) stands at its foot:
        # a terrace or a back step may lie against it, a fence on a side line stays a fence
        dh = ndimage.distance_transform_edt(~self.H) * RES
        foot = self.low & (dh <= 0.6) & (self.S > 0.35) & (self.S < self.width - 0.35) & (self.D > self.front + 2.0)
        # does an alley run behind the lot (not the railway's fence, not a neighbour's yard)?
        rear = [np.array(v, float) for k_, v in p["corners_local_m"].items() if k_.endswith("_rear")]
        mid = (rear[0] + rear[1]) / 2 if len(rear) == 2 else None
        self.on_alley = mid is not None and any(
            F.inside(np.array([mid[0] + dx]), np.array([mid[1] + dy]), np.asarray(a["polygon_local_m"], float))[0]
            for a in dist.grid.get("alleys", []) for dx, dy in ((0, 0), (1.5, 0), (-1.5, 0), (0, 1.5), (0, -1.5)))
        self.blocked = self.walls | (self.low & ~foot) | self.other_lot | ~self.inlot
        self.free_dist = ndimage.distance_transform_edt(~self.blocked) * RES
        self.ok = True

    @staticmethod
    def solid(m):
        """A model's wall cells closed and filled: the building's whole plan (a model is its walls)."""
        if not m.any():
            return m
        return ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=3)) | m

    # -- frame <-> world

    def world(self, s, d):
        return (r2(self.A[0] + s * self.su[0] + d * self.nu[0]), r2(self.A[1] + s * self.su[1] + d * self.nu[1]))

    def frame(self, e, n):
        v = np.array([e, n]) - self.A
        return float(v @ self.su), float(v @ self.nu)

    def rect_poly(self, s0, s1, d0, d1):
        return [list(self.world(s0, d0)), list(self.world(s1, d0)), list(self.world(s1, d1)), list(self.world(s0, d1))]

    def bearing(self, vec_frame) -> float:
        """The compass bearing of a direction given in the frame (ds, dd)."""
        v = vec_frame[0] * self.su + vec_frame[1] * self.nu
        return r2(math.degrees(math.atan2(v[0], v[1])) % 360.0)

    def cells(self, s0, s1, d0, d1):
        return (self.S >= s0) & (self.S <= s1) & (self.D >= d0) & (self.D <= d1)

    def fits(self, s0, s1, d0, d1, extra=None) -> bool:
        if s0 < self.S[0, 0] or s1 > self.S[0, -1] or d0 < self.D[0, 0] or d1 > self.D[-1, 0]:
            return False
        m = self.cells(s0, s1, d0, d1)
        if not m.any():
            return False
        bad = self.blocked | (extra if extra is not None else False)
        if (m & bad).any() or not bool((self.free_dist[m] >= WALL_GAP_M).all()):
            return False
        # the rect's edges reach half a cell past its cells' centres: they stay in the lot too
        out = self.cells(s0 - RES, s1 + RES, d0 - RES, d1 + RES) & (~self.inlot | self.other_lot)
        return not out.any()


# ---------------------------------------------------------------- the pieces

def back_door(L: Lot, rng):
    """The main house's back door: one its model carries on the rear, or a new one on a stretch of
    the rear wall with no window in its way. Returns a dict or None."""
    meta = L.meta[L.main]
    k = L.kidx[L.main]
    H = L.H
    # the rear profile: per column of s, the house's rearmost cell
    cols = np.where(H.any(axis=0))[0]
    if not len(cols):
        return None
    rear_d = np.full(L.S.shape[1], np.nan)
    for c in cols:
        rows = np.where(H[:, c])[0]
        rear_d[c] = L.D[rows.max(), c] + RES / 2
    s_of = L.S[0]
    # a model's own rear door: a leaf whose plan point stands within 1 m of the rear profile
    dist_doors = []
    for de_, dn, lo, hi in DIST.meta[L.main]["doors"]:
        ds, dd = L.frame(de_, dn)
        c = int(np.argmin(np.abs(s_of - ds)))
        if not np.isnan(rear_d[c]) and abs(dd - rear_d[c]) < 1.0 and dd > L.front + 4.0:
            dist_doors.append((ds, rear_d[c], lo))
    floor = meta["wing_floor_m"] or meta["principal_floor_m"]
    if floor is None:
        fronts = [lo for de_, dn, lo, hi in DIST.meta[L.main]["doors"]
                  if L.frame(de_, dn)[1] < L.front + 4.0]
        floor = min(fronts) if fronts else 0.6
    sill = min(max(float(floor), RISER_M), SILL_MAX_M)
    if dist_doors:
        ds, dd, lo = sorted(dist_doors, key=lambda t: -t[1])[0]
        return {"s": ds, "d": dd, "sill": max(lo, 0.0), "leaf": False, "height": DOOR_H_M}
    glass = DIST.meta[L.main]["glass"]
    gsd = np.array([L.frame(g[0], g[1]) for g in glass]) if len(glass) else np.zeros((0, 2))
    half = DOOR_W_M / 2
    # The door at the first floor, up its flight; and where no stretch of wall has room for that
    # flight or is clear of the first floor's windows, the door at grade a step up, under them
    # (the raised basement's kitchen door of a house whose first floor stands high).
    tries = [(sill, DOOR_H_M)] + ([(RISER_M, GRADE_DOOR_H_M)] if sill > 2 * RISER_M else [])
    cands = []
    for sill, door_h in tries:
        n = max(1, int(round(sill / RISER_M)))
        out_m = (LANDING_M if n >= 3 else 0.0) + (n - (1 if n >= 3 else 0)) * TREAD_M
        need = out_m + 1.2
        for c in cols:
            rd = rear_d[c]
            s = s_of[c]
            if s - half < L.s_lo + 0.5 or s + half > L.s_hi - 0.5:
                continue
            span = np.abs(s_of - s) <= half + 0.3
            if np.any(np.isnan(rear_d[span])) or np.nanmax(np.abs(rear_d[span] - rd)) > 0.3:
                continue                      # not a flat stretch of wall
            # the yard behind it, its whole width, clear of every wall, fence and the lot line
            if not L.fits(s - half - 0.2, s + half + 0.2, rd + WALL_GAP_M + 0.05, rd + need):
                continue
            # no window's glass in the door's way, in plan along the wall and up the door's height
            if len(gsd):
                near = (np.abs(gsd[:, 1] - rd) < 0.7) & (np.abs(gsd[:, 0] - s) < half + WINDOW_CLEAR_M)
                z = glass[:, 2:4]
                hit = near & (z[:, 1] > sill - 0.05) & (z[:, 0] < sill + door_h + 0.15)
                if hit.any():
                    continue
            cands.append((s, rd))
        if cands:
            break
    if not cands:
        return None
    # the rearmost stretch (the kitchen's, in the rear wing) and, on it, nearest the side passage
    # the rearmost stretch (the kitchen's, in the rear wing) and, on it, nearest the side passage
    # the yard is widest on
    rd_max = max(rd for _s, rd in cands)
    back = [(s, rd) for s, rd in cands if rd >= rd_max - 0.3]
    wide_lo = L.s_lo > (L.width - L.s_hi)
    back.sort(key=lambda t: (t[0] if wide_lo else -t[0]))
    pick = back[min(len(back) - 1, int(len(back) * rng.uniform(0.0, 0.25)))]
    return {"s": float(pick[0]), "d": float(pick[1]), "sill": sill, "leaf": True, "height": door_h}


def stoop_extent(sill):
    n = max(1, int(round(sill / RISER_M)))
    landing = LANDING_M if n >= 3 else 0.0
    return n, landing, landing + (n - (1 if n >= 3 else 0)) * TREAD_M


def fit_rect(L: Lot, s0, s1, d0, d1, s_core, d_min, extra=None):
    """Shrink [s0, s1] x [d0, d1] (d0 fixed at the wall) until it fits, keeping s_core covered and
    at least d_min deep. Returns the rect or None."""
    for _ in range(80):
        if L.fits(s0, s1, d0, d1, extra):
            return s0, s1, d0, d1
        # trim the side that hits, else the depth
        lw = L.fits(s0, (s0 + s1) / 2, d0, d1, extra)
        rw = L.fits((s0 + s1) / 2, s1, d0, d1, extra)
        if not lw and s0 + RES <= s_core[0]:
            s0 += RES
        elif not rw and s1 - RES >= s_core[1]:
            s1 -= RES
        elif d1 - RES >= d0 + d_min:
            d1 -= RES
        elif s0 + RES <= s_core[0]:
            s0 += RES
        elif s1 - RES >= s_core[1]:
            s1 -= RES
        else:
            return None
    return None


def route(L: Lot, start_mask, goal_mask, width, avoid):
    """The cheapest walk `width` wide from any start cell to any goal cell over free ground, with
    turns priced, as a list of (s, d) cell centres. None if none."""
    half = width / 2 + WALL_GAP_M
    ok = (L.free_dist >= half) & ~avoid
    # the walk's centre may stand where its half-width keeps off what blocks, and off `avoid`
    if avoid.any():
        ok &= ndimage.distance_transform_edt(~avoid) * RES >= half
    h, w = ok.shape
    starts = np.argwhere(start_mask & ok)
    goals = goal_mask & ok
    if not len(starts) or not goals.any():
        return None
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    INF = 1e18
    best = np.full((h, w, 4), INF)
    prev = {}
    pq = []
    for r, c in starts:
        for k in range(4):
            best[r, c, k] = 0.0
            heapq.heappush(pq, (0.0, int(r), int(c), k))
    end = None
    while pq:
        cost, r, c, k = heapq.heappop(pq)
        if cost > best[r, c, k]:
            continue
        if goals[r, c]:
            end = (r, c, k)
            break
        for k2, (dr, dc) in enumerate(dirs):
            r2_, c2 = r + dr, c + dc
            if not (0 <= r2_ < h and 0 <= c2 < w) or not ok[r2_, c2]:
                continue
            nc = cost + 1.0 + (TURN_COST if k2 != k else 0.0)
            if nc < best[r2_, c2, k2]:
                best[r2_, c2, k2] = nc
                prev[(r2_, c2, k2)] = (r, c, k)
                heapq.heappush(pq, (nc, r2_, c2, k2))
    if end is None:
        return None
    path = [end]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    return [(float(L.S[r, c]), float(L.D[r, c])) for r, c, _k in reversed(path)]


def path_rects(path, width):
    """A cell path as straight runs, each a rect [s0, s1, d0, d1] `width` wide, overlapping at turns."""
    if not path or len(path) < 2:
        return []
    runs = []
    a = path[0]
    prev = path[0]
    direction = None
    for p in path[1:]:
        dv = (round(p[0] - prev[0], 3), round(p[1] - prev[1], 3))
        if direction is not None and dv != direction:
            runs.append((a, prev))
            a = prev
        direction = dv
        prev = p
    runs.append((a, prev))
    half = width / 2
    out = []
    for (s0, d0), (s1, d1) in runs:
        out.append([min(s0, s1) - half, max(s0, s1) + half, min(d0, d1) - half, max(d0, d1) + half])
    return out


def real_walks(L: Lot):
    """The kits' walks on the lot: flat paving in pieces of 2 m2 or more (not a splash stone, a
    grate's frame or a step's tread)."""
    lab, n = ndimage.label(L.paved & L.inlot)
    if not n:
        return np.zeros(L.S.shape, bool)
    size = ndimage.sum(np.ones(lab.shape), lab, index=np.arange(1, n + 1)) * RES * RES
    keep = np.flatnonzero(size >= 2.0) + 1
    return np.isin(lab, keep)


# ---------------------------------------------------------------- the lot's yard

def lay_lot(p, laundry, disks):
    pid = p["id"]
    rng = random.Random(seed_of(pid))
    L = Lot(p, DIST, disks)
    if not L.ok:
        return None, "no house on it"
    if pid in LEFT_AS_DRAWN:
        return None, "left as drawn: " + LEFT_AS_DRAWN[pid]
    meta = L.meta[L.main]
    worked = meta["archetype"] in ("k01_frontage", "k16_timber")
    wide = L.width >= 18.0                     # a double lot or better (60 ft and over)
    modest = p.get("street") in ("indiana", "calumet") or not worked
    yard_free = L.inlot & ~L.blocked & (L.D > L.rear)
    if yard_free.sum() * RES * RES < 6.0:
        return None, "no yard behind the house"
    surfaces, doors, posts, crops = [], [], [], []
    taken = np.zeros(L.S.shape, bool)              # what this lot has laid so far
    grade = "reconstructed"

    def add(kind, mat, rect, order=0, g=None, note=None, along=None):
        s0, s1, d0, d1 = [float(x) for x in rect]
        # a walk starts at the terrace's edge, never on it (a second paving over the first)
        if terrace and kind != "rear_terrace":
            t0, t1, u0, u1 = terrace
            if s0 < t1 and s1 > t0 and d0 < u1 and d1 > u0:
                if s0 >= t0 - 0.01 and s1 <= t1 + 0.01:
                    if d1 > u1:
                        d0 = max(d0, u1)
                    elif d0 < u0:
                        d1 = min(d1, u0)
                elif d0 >= u0 - 0.01 and d1 <= u1 + 0.01:
                    if s1 > t1:
                        s0 = max(s0, t1)
                    elif s0 < t0:
                        s1 = min(s1, t0)
                if s1 - s0 < 0.3 or d1 - d0 < 0.3:
                    return False
        m = L.cells(s0, s1, d0, d1) & L.inlot
        if not m.any():
            return False
        # stop at a walk a kit already built: a run whose cells are mostly paved is not laid
        if (m & L.paved).sum() > 0.6 * m.sum():
            return False
        taken[m] = True
        along_v = (1.0, 0.0) if along is None else along
        surfaces.append({
            "id": f"{pid}:{kind}:{len(surfaces)}", "kind": kind, "material": mat,
            "polygon_local_m": L.rect_poly(s0, s1, d0, d1),
            "along_deg": L.bearing(along_v),
            "lift_m": TURF_LIFT_M if (m & L.turf).any() else SURFACE_LIFT_M,
            "order": order, "grade": g or grade,
            "note": note or f"{KIND_WORDS[kind].capitalize()}, in {MATERIALS[mat]['label']}: reconstructed "
                            f"({LIBERTY}).",
        })
        return True

    # --- the back door, its steps and the terrace
    door = back_door(L, rng)
    terrace = None
    paving = ("flags" if meta["stone"] and rng.random() < 0.6 else "yard_brick") if worked else \
        ("yard_brick" if rng.random() < 0.55 else "cement")
    if door:
        n, landing, out_m = stoop_extent(door["sill"])
        ds, dd = door["s"], door["d"]
        sw = 1.6 if landing else 1.2
        doors.append({
            "id": f"{pid}:back_door", "structure": L.main,
            "e": L.world(ds, dd)[0], "n": L.world(ds, dd)[1],
            "facing_deg": L.bearing((0.0, 1.0)),
            "sill_m": r2(door["sill"]), "width_m": DOOR_W_M, "height_m": door["height"],
            "leaf": door["leaf"],
            "stoop": {"depth_m": r2(landing), "width_m": sw, "risers": n, "run_m": r2(out_m),
                      "material": "wood" if (meta["frame"] or not worked) else "stone"},
            "grade": "reconstructed",
            "note": ("The back door the model carries, " if not door["leaf"] else
                     "The kitchen door on the rear wall: no picture shows this house's rear, and every "
                     "house of the period had one; placed on a stretch of wall with no window in its way, ")
                    + f"its sill {door['sill']:.2f} m up, {n} steps down to the yard ({LIBERTY}).",
        })
        stoop_mask = L.cells(ds - sw / 2 - 0.05, ds + sw / 2 + 0.05, dd, dd + out_m + 0.05)
        if wide and worked:
            tw, td = rng.uniform(4.2, 6.0), rng.uniform(3.2, 4.6)
        elif worked:
            tw, td = rng.uniform(3.0, 4.2), rng.uniform(2.2, 3.0)
        else:
            tw, td = rng.uniform(2.0, 3.0), rng.uniform(1.4, 2.2)
        rect = fit_rect(L, ds - tw / 2, ds + tw / 2, dd + WALL_GAP_M, dd + out_m + td,
                        (ds - sw / 2, ds + sw / 2), out_m + 1.0)
        if rect:
            terrace = rect
            add("rear_terrace", paving, rect, order=0,
                note=f"A paved terrace at the back door, in {MATERIALS[paving]['label']}: the kitchen's "
                     "and the household's outdoor room. No source shows this yard; its size follows the "
                     f"lot's ({LIBERTY}).")
        taken |= stoop_mask
    walk_mat = paving if worked and paving != "flags" else ("cement" if worked else "cinder")
    walk_w = 1.2 if worked else 1.0

    # where the walks start: the terrace's far edge on the door's line (a walk leaves a terrace
    # straight out from the steps), else anywhere on it, else the foot of the steps
    walks = real_walks(L)
    starts = []
    if terrace:
        s0, s1, d0, d1 = terrace
        ds = door["s"]
        starts.append(L.cells(ds - 0.3, ds + 0.3, d1 - 0.6, d1))
        starts.append(L.cells(s0, s1, d0 + 0.5, d1))
    elif door:
        _n, _l, out_m = stoop_extent(door["sill"])
        starts.append(L.cells(door["s"] - 0.6, door["s"] + 0.6, door["d"] + out_m, door["d"] + out_m + 0.6))

    def walk_from(goal, width, avoid=None, limit=None):
        avoid = np.zeros(L.S.shape, bool) if avoid is None else avoid
        for st in starts:
            path = route(L, st, goal, width, avoid)
            if path and (limit is None or len(path) * RES <= limit):
                return path
        return None

    # --- to the coach house: its yard door, or its workyard's paving (K12)
    if starts and L.coaches:
        goal = np.zeros(L.S.shape, bool)
        for sid in L.coaches:
            for de_, dn, lo, hi in DIST.meta[sid]["doors"]:
                cs, cd = L.frame(de_, dn)
                if lo < 0.6 and cd < float(L.D[L.C].max()) - 1.5:      # a door on the yard side, at grade
                    goal |= (np.abs(L.S - cs) < 0.6) & (np.abs(L.D - cd) < 1.6)
        yard_walks = walks & (L.D > L.rear)
        goal |= ndimage.binary_dilation(yard_walks, iterations=2) & ~walks
        if goal.any():
            path = walk_from(goal, walk_w)
            # a stable path is as often raked gravel as paving
            coach_mat = "gravel" if worked and rng.random() < 0.35 else walk_mat
            if path:
                for rc in path_rects(path, walk_w):
                    add("coach_walk", coach_mat, rc, order=1,
                        note=f"The walk from the back door to the coach house, in {MATERIALS[coach_mat]['label']} "
                             f"({LIBERTY}).")
    # --- no coach house, and an alley behind: a walk to the alley gate, where the ash box stood
    if starts and not L.coaches and L.on_alley:
        goal = L.inlot & (L.D >= L.depth - 0.8)
        path = walk_from(goal, 1.0, limit=40.0)
        if path:
            for rc in path_rects(path, 1.0):
                add("alley_walk", "cinder" if modest else walk_mat, rc, order=1,
                    note=f"A walk from the back door to the alley, where the ash box and the deliveries "
                         f"were ({LIBERTY}).")

    # --- round to the front: down the side passage to the K14 service walk, or to the front walk
    # near the stoop's foot (not across the front lawn by the street)
    if starts:
        lo_gap, hi_gap = L.s_lo, L.width - L.s_hi
        gap = max(lo_gap, hi_gap)
        if gap >= MIN_GANGWAY_M + 2 * WALL_GAP_M:
            gw = min(walk_w, gap - 0.35)
            in_passage = (L.S < L.s_lo) | (L.S > L.s_hi)
            side_walks = walks & (L.D < L.rear) & (L.D > L.front - 1.0) & in_passage
            # the front walk, near the stoop's foot, and only where it comes within GANGWAY_REACH_M of
            # a side passage: a gangway does not cross the front lawn along the street to reach it
            near_side = (L.S < L.s_lo + GANGWAY_REACH_M) | (L.S > L.s_hi - GANGWAY_REACH_M)
            stoop_walk = walks & (L.D < L.front) & (L.D >= L.front - 3.5) & near_side
            target = side_walks | stoop_walk
            goal = ndimage.binary_dilation(target, iterations=2) & ~walks
            avoid = L.crowns | (L.D < L.front - 3.5) | ((L.D < L.front) & ~near_side & ~in_passage)
            if goal.any():
                path = walk_from(goal, gw, avoid, limit=L.depth * 1.5)
                if path:
                    for rc in path_rects(path, gw):
                        kind = "gangway" if rc[2] > L.front - 0.3 else "front_walk"
                        add(kind, walk_mat, rc, order=1,
                            note=f"The {KIND_WORDS[kind]}, in {MATERIALS[walk_mat]['label']}: the way "
                                 f"tradesmen and the household came round from the street to the back "
                                 f"({LIBERTY}).")

    # --- the drying yard: where the census names a laundress, and on most small lots
    who = [w for sid in L.sids for w in laundry.get(sid, [])]
    want_dry = bool(who) or (modest and rng.random() < 0.55)
    if want_dry:
        dw, dd_ = (6.0, 4.0) if who else (4.5, 3.2)
        free = L.inlot & ~L.blocked & ~L.paved & ~ndimage.binary_dilation(taken, iterations=2) & (L.D > L.rear + 1.0)
        dist_in = ndimage.distance_transform_edt(free) * RES
        best = None
        for frac in (1.0, 0.8, 0.6):
            hw, hd = dw * frac / 2, dd_ * frac / 2
            ok = dist_in >= min(hw, hd)
            idx = np.argwhere(ok)
            for r, c in idx[np.argsort(-dist_in[ok], kind="stable")][:200]:
                s, d = float(L.S[r, c]), float(L.D[r, c])
                rect = (s - hw, s + hw, d - hd, d + hd)
                if L.fits(*rect, extra=ndimage.binary_dilation(taken, iterations=1) | L.paved):
                    best = rect
                    break
            if best:
                break
        if best:
            g = "inferred" if who else "reconstructed"
            add("drying_yard", "trodden", best, order=0, g=g,
                note=("The drying yard: the 1900 census enumerates a laundress in this household, so the "
                      "wash was done and hung at home; the yard's place and size are reconstructed "
                      f"({LIBERTY})." if who else
                      f"A drying yard of trodden earth, with its clothes posts ({LIBERTY})."))
            s0, s1, d0, d1 = best
            pa = L.world(s0 + 0.3, (d0 + d1) / 2)
            pb = L.world(s1 - 0.3, (d0 + d1) / 2)
            posts.append({"kind": "clothes_post", "e": pa[0], "n": pa[1], "height_m": 2.3, "arm_m": 0.9,
                          "facing_deg": L.bearing((1.0, 0.0)), "line_to": len(posts) + 1, "grade": g})
            posts.append({"kind": "clothes_post", "e": pb[0], "n": pb[1], "height_m": 2.3, "arm_m": 0.9,
                          "facing_deg": L.bearing((1.0, 0.0)), "line_to": None, "grade": g})

    # --- a kitchen garden: modest lots only, seeded so most have none
    if modest and rng.random() < 0.35:
        free = L.inlot & ~L.blocked & ~L.paved & ~ndimage.binary_dilation(taken, iterations=3) & (L.D > L.rear + 1.0)
        # against the fence the sun falls on: the yard's north side (the side line whose outward
        # normal points north)
        north = 1 if (L.su[1] > 0) else -1           # +s runs north when su points north
        bw, bd = rng.uniform(2.4, 3.6), rng.uniform(3.0, 4.5)
        dist_in = ndimage.distance_transform_edt(free) * RES
        best = None
        order_s = np.argsort(-L.S[0] * north, kind="stable")
        for c in order_s:
            for r in np.argsort(L.D[:, c], kind="stable"):
                if dist_in[r, c] < 0.3:
                    continue
                s, d = float(L.S[r, c]), float(L.D[r, c])
                rect = (s - bw / 2, s + bw / 2, d - bd / 2, d + bd / 2)
                if L.fits(*rect, extra=ndimage.binary_dilation(taken, iterations=2) | L.paved):
                    best = rect
                    break
            if best:
                break
        if best:
            add("garden_bed", "loam", best, order=0,
                note="A kitchen garden of a few dug rows against the sunny fence. No source names a garden "
                     f"on any lot of the district: this one is reconstructed ({LIBERTY}).",
                along=(0.0, 1.0))
            s0, s1, d0, d1 = best
            rows = []
            nrow = max(2, int((s1 - s0 - 0.3) / 0.55))
            kinds = rng.sample(GARDEN_CROPS, k=min(3, len(GARDEN_CROPS)))
            for i in range(nrow):
                s = s0 + 0.3 + i * (s1 - s0 - 0.6) / max(1, nrow - 1)
                a, b = L.world(s, d0 + 0.25), L.world(s, d1 - 0.25)
                rows.append([a[0], a[1], b[0], b[1], kinds[i % len(kinds)]])
            crops.append({"bed": surfaces[-1]["id"], "rows": rows})

    # --- what grows: the side lawn's shade trees and border, creeper on the stable, a lilac at the fence
    shrubs, trees, creeper = [], [], []
    keep_off = L.blocked | L.paved | ndimage.binary_dilation(taken, iterations=2)
    for dd_ in doors:
        ds_, dd2 = L.frame(dd_["e"], dd_["n"])
        keep_off |= (L.S - ds_) ** 2 + (L.D - dd2) ** 2 <= 2.0 ** 2
    room = ndimage.distance_transform_edt(~keep_off) * RES
    behind_front = L.inlot & (L.D > L.front + 1.0)
    planted: list[tuple[float, float, float]] = []

    def clear(s, d, r, k=1.0):
        return all(math.hypot(s - a, d - b) >= (r + rr) * k for a, b, rr in planted)

    def place(mask, r, score, k=1.0):
        idx = np.flatnonzero(mask & (room >= r))
        for i in idx[np.argsort(score.flat[idx], kind="stable")][:600]:
            s, d = float(L.S.flat[i]), float(L.D.flat[i])
            if clear(s, d, r, k):
                return s, d
        return None

    side_lo, side_hi = L.s_lo, L.width - L.s_hi
    strip = max(side_lo, side_hi)
    lawn_side = -1 if side_lo >= side_hi else 1
    side_mask = behind_front & (L.D < L.rear + 4.0) & ((L.S < L.s_lo - 1.0) if lawn_side < 0 else (L.S > L.s_hi + 1.0))
    if worked and strip >= 8.0:
        # a side lawn: one shade tree on a strip of 8-12 m, two to 20 m, three past it, spaced
        n_trees = 1 if strip < 12.0 else (2 if strip < 20.0 else 3)
        for _ in range(n_trees):
            key = "maple" if rng.random() < 0.6 else "linden"
            h, w = r2(rng.uniform(7.5, 10.5)), r2(rng.uniform(4.5, 6.5))
            mid = (L.s_lo / 2) if lawn_side < 0 else ((L.s_hi + L.width) / 2)
            score = np.abs(L.S - mid) + 0.3 * np.abs(L.D - (L.front + L.rear) / 2) + rng.random() * 0.01
            at = place(side_mask, 2.2, score, k=1.6)
            if not at:
                break
            planted.append((at[0], at[1], w / 2))
            e, n = L.world(*at)
            trees.append([e, n, key, h, w])
        # a shrub border along the outer side line
        line_s = 0.0 if lawn_side < 0 else L.width
        n_sh = rng.randint(2, 5)
        for _ in range(n_sh):
            key = rng.choice(["lilac", "lilac", "spiraea", "hydrangea"])
            band = F.PLANTS[key] if hasattr(F, "PLANTS") else None
            h = r2(rng.uniform(*(band["h"] if band else (1.2, 2.4))))
            w = r2(rng.uniform(*(band["w"] if band else (1.2, 2.0))))
            score = np.abs(np.abs(L.S - line_s) - (w / 2 + F.SIDE_LINE_CLEAR_M)) + rng.random() * 0.3 * \
                np.abs(L.D - rng.uniform(L.front + 2, L.rear))
            at = place(side_mask, w / 2, score)
            if not at:
                break
            planted.append((at[0], at[1], w / 2))
            e, n = L.world(*at)
            shrubs.append([e, n, key, h, w])
    # creeper on the coach house's yard face (a third of them), Virginia creeper's habit on a stable
    if L.coaches and rng.random() < 0.33:
        cols = np.where(L.C.any(axis=0))[0]
        if len(cols):
            face_d = {c: float(L.D[np.where(L.C[:, c])[0].min(), c]) - RES / 2 for c in cols}
            mids = sorted(cols, key=lambda c: abs(L.S[0, c] - float(np.mean(L.S[0, cols]))))
            for c in mids[:6]:
                s, d = float(L.S[0, c]), face_d[c]
                r_ = int(np.argmin(np.abs(L.D[:, 0] - (d - 0.4))))
                if L.inlot[r_, c] and not taken[r_, c] and not L.paved[r_, c] and not L.walls[r_, c]:
                    e, n = L.world(s, d - 0.02)
                    creeper.append([e, n, L.bearing((0.0, -1.0)), r2(rng.uniform(2.5, 4.5)), r2(rng.uniform(2.8, 4.8))])
                    break
    # a lilac or two at the back fence of a lot with no stable
    if not L.coaches and (L.depth - L.rear) > 8.0:
        for _ in range(rng.randint(1, 2)):
            band = F.PLANTS["lilac"] if hasattr(F, "PLANTS") else {"h": (2.2, 3.2), "w": (1.8, 2.6)}
            h, w = r2(rng.uniform(*band["h"])), r2(rng.uniform(*band["w"]))
            corner = 0.0 if rng.random() < 0.5 else L.width
            score = np.abs(L.S - corner) + np.abs(L.D - L.depth) + rng.random() * 0.01
            at = place(L.inlot & (L.D > L.rear + 3.0), w / 2 + 0.3, score)
            if not at:
                break
            planted.append((at[0], at[1], w / 2))
            e, n = L.world(*at)
            shrubs.append([e, n, "lilac", h, w])

    if not surfaces and not doors:
        return None, "nothing fitted"
    scheme = "service_court"
    if wide and worked:
        scheme = "side_lawn"
    if modest:
        scheme = "drying_yard" if want_dry else "service_court"
    lot = {
        "parcel": pid, "addresses": p.get("addresses_1911", []), "street": p.get("street"),
        "side": p.get("side"), "structures": L.sids, "scheme": scheme, "grade": grade,
        "sources": ["census_1900_chicago_t623_roll245"] if who else [],
        "note": "",
        "surfaces": surfaces, "doors": doors, "posts": posts, "crops": crops,
        "shrubs": shrubs, "trees": trees, "creeper": creeper, "beds": [],
    }
    return lot, None


DIST: District | None = None


def build():
    global DIST
    DIST = District()
    return build_from(DIST)


def build_from(dist):
    laundry = laundress_structures()
    disks = front_plant_disks(json.loads(FRONT.read_text())["lots"]) if FRONT.exists() else []
    lots, report = [], []
    for p in DIST.parcels:
        lot, why = lay_lot(p, laundry, disks)
        if lot:
            lots.append(lot)
            report.append(f"{p['id']}: {len(lot['surfaces'])} surfaces, {len(lot['doors'])} doors, "
                          f"{len(lot['posts'])} posts ({lot['scheme']})")
        else:
            report.append(f"{p['id']}: none — {why}")
    lots.sort(key=lambda l: l["parcel"])
    summary = {"lots": len(lots),
               "surfaces": sum(len(l["surfaces"]) for l in lots),
               "doors": sum(len(l["doors"]) for l in lots),
               "posts": sum(len(l["posts"]) for l in lots),
               "gardens": sum(len(l["crops"]) for l in lots)}
    by_kind: dict[str, int] = {}
    for l in lots:
        for s in l["surfaces"]:
            by_kind[s["kind"]] = by_kind.get(s["kind"], 0) + 1
    summary["by_kind"] = dict(sorted(by_kind.items()))
    data = {
        "_doc": "The 1904 district's back and side yards (T-3488): back doors and their steps, paved "
                "terraces, walks to the coach house, the alley and the front, gangways, drying yards and "
                "kitchen gardens. GENERATED by tools/lay_prairie_1904_back_yards.py from "
                "data/street_grid/1904.json, the 1904 sidecars' baked models, the 1900 census household "
                "cards and data/front_yards/1904.json -- do not hand-edit; re-run the tool. Local ENU "
                "metres of data/datum.json. Shrubs, trees, creeper and beds use data/front_yards/1904.json's "
                "row formats.",
        "scene": "1904", "target_date": "1904-07-01", "ticket": TICKET,
        "generated_by": "tools/lay_prairie_1904_back_yards.py", "liberty": LIBERTY,
        "materials": MATERIALS, "kinds": KIND_WORDS, "summary": summary, "lots": lots,
    }
    return data, report


CHECK_SLACK_M = 0.12       # --check lets a rebake move a wall this much over a surface's edge


def collisions(data, dist=None) -> list[str]:
    """Every surface, stoop and plant that stands where it must not, on the models as they are now."""
    dist = dist or DIST
    plan = dist.plan
    P = {p["id"]: p for p in dist.parcels}
    out = []
    lots_mask = plan.lots
    for lot in data["lots"]:
        p = P.get(lot["parcel"])
        if p is None:
            out.append(f"{lot['parcel']}: no such parcel")
            continue
        own = np.zeros(plan.tall.shape, bool)
        plan.lay_polygon(own, p["polygon_local_m"])
        walls = dist.house | (dist.owner >= 0)
        hard = walls | (plan.low & ~ndimage.binary_dilation(dist.house, iterations=3))
        slack = int(math.ceil(CHECK_SLACK_M / RES))
        hard_core = ndimage.binary_erosion(hard, iterations=1) if slack else hard
        for srf in lot["surfaces"]:
            m = np.zeros(plan.tall.shape, bool)
            poly = np.asarray(srf["polygon_local_m"], float)
            # the polygon shrunk by the slack, so an edge cell shared with a wall is not a fault
            c = poly.mean(axis=0)
            shrunk = c + (poly - c) * np.maximum(0.0, 1.0 - CHECK_SLACK_M / np.maximum(
                np.linalg.norm(poly - c, axis=1, keepdims=True), 1e-6))
            plan.lay_polygon(m, shrunk)
            if (m & hard_core).sum() > 2:
                out.append(f"{lot['parcel']} {srf['id']}: stands on a building, a fence or a stoop "
                           f"({int((m & hard_core).sum())} cells)")
            if (m & ~own).sum() > 4:
                out.append(f"{lot['parcel']} {srf['id']}: runs out of its lot ({int((m & ~own).sum())} cells)")
            if srf["material"] not in data["materials"]:
                out.append(f"{lot['parcel']} {srf['id']}: names no material of the file")
            if srf.get("grade") not in ("attested", "inferred", "reconstructed"):
                out.append(f"{lot['parcel']} {srf['id']}: no grade")
        for dr in lot["doors"]:
            if dr["structure"] not in dist.meta:
                out.append(f"{lot['parcel']} {dr['id']}: names no 1904 structure")
            if not 0.0 <= dr["sill_m"] <= SILL_MAX_M + 0.6:
                out.append(f"{lot['parcel']} {dr['id']}: sill {dr['sill_m']} m")
    return out


def self_test() -> int:
    """Plant each fault --check refuses, and prove it is refused."""
    global DIST
    DIST = DIST or District()
    data, _ = build_from(DIST)
    fails = 0
    base = collisions(data)
    if base:
        print("self-test: the tool's own file has faults:", base[:5])
        fails += 1
    lot = next(l for l in data["lots"] if l["surfaces"] and l["doors"])
    house = DIST.sids.index(lot["doors"][0]["structure"])
    rr, cc = np.argwhere(DIST.owner == house)[len(np.argwhere(DIST.owner == house)) // 2]
    e, n = DIST.plan.centre(rr, cc)
    cases = {
        "a terrace laid over the house": lambda d: d["lots"][d["lots"].index(lot)]["surfaces"][0].update(
            polygon_local_m=[[e - 2, n - 2], [e + 2, n - 2], [e + 2, n + 2], [e - 2, n + 2]]),
        "a walk run into the next lot": lambda d: d["lots"][d["lots"].index(lot)]["surfaces"][0].update(
            polygon_local_m=[[x + 40.0, y] for x, y in d["lots"][d["lots"].index(lot)]["surfaces"][0]["polygon_local_m"]]),
        "an unknown material": lambda d: d["lots"][d["lots"].index(lot)]["surfaces"][0].update(material="marble"),
        "a door on no structure": lambda d: d["lots"][d["lots"].index(lot)]["doors"][0].update(structure="nobody"),
    }
    for name, plant in cases.items():
        d = json.loads(json.dumps(data))
        lot = next(l for l in d["lots"] if l["parcel"] == lot["parcel"])
        plant(d)
        got = collisions(d)
        ok = bool(got)
        print(f"   self-test | {'ok  ' if ok else 'FAIL'} {name}: {got[:1] if got else 'not refused'}")
        fails += 0 if ok else 1
    # numpy's default sort puts equal values in an order its build and the CPU choose; the
    # layout takes the first spot that fits in sorted order, so that order is the output
    # (CI's runners disagreed on it, T-3488). Every numpy sort here is a stable one.
    own = unstable_sorts(Path(__file__).read_text())
    planted = unstable_sorts("for r in np." + "argsort(-dist[ok])[:200]:\n")
    print(f"   self-test | {'ok  ' if planted else 'FAIL'} an unstable numpy sort is refused: "
          f"{planted[:1] if planted else 'not refused'}")
    fails += 0 if planted else 1
    if own:
        print("self-test: the tool's own numpy sorts are not stable:", own[:3])
        fails += 1
    print("self-test: " + ("PASS" if not fails else f"FAIL ({fails})"))
    return 1 if fails else 0


def unstable_sorts(src: str) -> list[str]:
    """Lines calling np.argsort / np.sort without kind="stable"."""
    return [f"line {i}: {line.strip()}" for i, line in enumerate(src.splitlines(), 1)
            if re.search(r"np\.(arg)?sort\(", line) and 'kind="stable"' not in line
            and not line.lstrip().startswith("#") and "re.search" not in line]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    data, report = build()
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if a.report:
        print("\n".join(report))
        print(json.dumps(data["summary"]))
        return 0
    if a.check:
        bad = collisions(data)
        if not OUT.exists() or OUT.read_text() != text:
            print("back yards: data/back_yards/1904.json is not what the tool writes; re-run it")
            # name what moved, so a red on another machine can be read from its log
            if OUT.exists():
                import difflib
                diff = list(difflib.unified_diff(OUT.read_text().splitlines(), text.splitlines(),
                                                 "committed", "this run", n=1, lineterm=""))
                print(f"  {len(diff)} diff lines; the first 40:")
                print("\n".join("  " + line for line in diff[:40]))
            return 1
        if bad:
            print("back yards: " + "\n  ".join(bad))
            return 1
        print(f"back yards: {data['summary']}")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {data['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
