#!/usr/bin/env python3
"""Generate the 1812 settlement's yard goods: the wood, the casks and the carts (T-3458).

WHAT THIS IS. The owner, 2026-11-07, of the 1812 scene: *"add correct photographic and
historically correct items around the buildings that likely would be in place, probably wood
piles, and other things from the era that are necessary and sensible and correctly placed in a
logical area in and around each of the properties"*. This tool writes
`data/yard/1812/yard_goods_1812.json` and its manifest `data/yard/1812/index.json`, which the
yard layer (renderers/web/js/yard.js, `yard_dir` in data/scenes/1812.json) draws with the same
woodpiles, chopping blocks, casks, cases and carts it draws in 1835. Nothing here is baked.

WHAT EACH PLACE GETS, BY WHAT IT WAS (the `KIT` table below):
  * a HOUSE (every 1812 dwelling: the Kinzie house and its men's lodging house, Ouilmette,
    Lalime, Lemai, the Burns and Lee houses, the two houses at the forks, Lee's Place, and the
    agent's and the interpreter's houses outside the fort) burned wood every day of the year
    for its kitchen fire: a rick of split wood against its back wall, a chopping block in front
    of it with the split billets lying round, and a water cask at a back corner;
  * a BAKE HOUSE (the garrison's, and the Kinzies') fired an oven, which eats more wood than a
    hearth: a heap of unsplit lengths as well as a long rick;
  * the FACTORY, the government trading house, and the MERCHANT's shop kept trade goods that
    came in casks and cases (the factory's goods were given out on the 14th, the scene date);
  * the ARMOURER's shop, a smithy: a slack-tub cask by the door and a heap of slabs;
  * the garrison's STABLES and the Kinzie stable: a two-wheeled cart, and at the garrison's a
    four-wheeled wagon too (the evacuation of the 15th went out with wagons, Quaife 1913);
  * LEE'S PLACE, the farm: a cart by the cabin.

WHERE A THING STANDS IS A RULE, NOT A COORDINATE. A building's FRONT is its footprint's max-v
edge (docs/GLB-CONTRACT.md); its BACK is the min-v edge, its gables the two u edges, every
footprint turned CLOCKWISE by its bearing (tools/check_structure_clearance.py's convention).
A rick is racked a hand's gap off the back wall and slid along it from the corner the record's
seed picks; when the back is taken the gables are tried, then the rick is shortened, then the
item is refused IN WRITING. Every corner of every item must stand on dry ground inside the
modelled terrain, outside every footprint grown by a clearance (a building, a fence, a garden,
the fort's pickets), off every worn trail's trodden width, clear of every planted 1812 stem, and
clear of every item already placed. A cart stands on the building's own worn yard
(data/enclosures/1812/worn_yard_1812_*.json), at the open point nearest the door side.

EVERY ITEM IS RECONSTRUCTED: its position, size and count are this tool's
(docs/LIBERTIES.md L-t3458-yard-goods-1812). What is not invented is that a house of 1812
burned wood and that the garrison had wagons; the record's `existence` says why.

    python3 tools/generate_yard_goods_1812.py            write the record and the manifest
    python3 tools/generate_yard_goods_1812.py --check    re-derive and diff, with assertions
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_worn_ground_1812 as wg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "yard" / "1812"
OUT = OUT_DIR / "yard_goods_1812.json"
INDEX = OUT_DIR / "index.json"
RECORD_ID = "yard_goods_1812"
TICKET = "T-3458"
LIBERTY = "L-t3458-yard-goods-1812"
SCENE_DATE = "1812-08-14"

WALL_GAP_M = 0.45        # a rick racked a hand's gap off the wall, for the air
FOOTPRINT_CLEAR_M = 0.25  # an item's corner from any other footprint (its own wall: the gap)
FENCE_CLEAR_M = 0.6      # from a fence, a garden paling or the fort's pickets
TRAIL_CLEAR_M = 0.6      # past a worn trail's trodden half-width
STEM_CLEAR_M = 1.0       # from a planted stem (a tree, a currant bush)
ITEM_CLEAR_M = 0.35      # between two items
DRY_Y = wg.WATER_Y + 0.15
FENCES = {"palisade"}

# What a stick and a log are: the 1835 record's own figures (data/yard/town_woodpiles.json),
# restated here because this record owns its own claims.
CORD_DEPTH_M = 1.22      # a 4 ft cordwood stick, racked as cut
STOVE_DEPTH_M = 0.61     # a 4 ft stick sawn in two for the hearth's fire-dogs


# --------------------------------------------------------------------------------------------
# what each place gets
# --------------------------------------------------------------------------------------------

HOUSE = "house"
BAKE = "bake_house"
STORE = "store"
SMITH = "smithy"
STABLE = "stable"
FARM = "farm"

# id -> (what it is, size class 0..2, a short reason the card can carry)
KIT = {
    "kinzie_house_1812": (HOUSE, 2, "The Kinzie house, the largest household in the place: its kitchen fire burned all year."),
    "kinzie_lodging_house_1812": (HOUSE, 1, "The lodging house for the Kinzies' French engagés."),
    "kinzie_bake_house_1812": (BAKE, 1, "The Kinzies' bake house: an oven is fired with more wood than a hearth."),
    "kinzie_stable_1812": (STABLE, 0, "The Kinzie stable: the household's cart stands in the yard by it."),
    "ouilmette_house_1812": (HOUSE, 0, "Antoine Ouilmette's house."),
    "lalime_house_1812": (HOUSE, 0, "Jean Lalime's house."),
    "lemai_house_1812": (HOUSE, 0, "Lemai's house."),
    "burns_house_1812": (HOUSE, 0, "The Burns family's cabin."),
    "lee_house_1812": (HOUSE, 0, "The Lee family's town house."),
    "forks_house_clark_1812": (HOUSE, 0, "The house at the forks."),
    "forks_house_soldier_1812": (HOUSE, 0, "The discharged soldier's house at the forks."),
    "lees_place_cabin_1812": (FARM, 1, "Lee's Place, a working farm: wood for the cabin, and a cart."),
    "first_fort_outer_agents_house": (HOUSE, 1, "The Indian agent's house."),
    "first_fort_outer_interpreters_house": (HOUSE, 0, "The interpreter's house."),
    "first_fort_outer_bake_house": (BAKE, 2, "The garrison's bake house: its oven baked a company's bread."),
    "first_fort_outer_factory": (STORE, 2, "The United States factory: its trade goods came in casks and cases."),
    "first_fort_outer_merchants_shop": (STORE, 0, "The merchant's shop."),
    "first_fort_outer_armourers_shop": (SMITH, 0, "The armourer's shop, a smithy: a slack tub at the door and slabs for the fire."),
    "first_fort_outer_stable_middle": (STABLE, 1, "The garrison's stables: the post's wagon and cart stand in the stable yard."),
}


def seed_of(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0x7FFFFFFF


class Rng:
    """A small, stable generator (xorshift32) seeded per place, so a re-derive is byte for byte."""

    def __init__(self, seed: int):
        self.s = (seed or 1) & 0xFFFFFFFF

    def __call__(self) -> float:
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.s = s & 0xFFFFFFFF
        return self.s / 4294967296.0


# --------------------------------------------------------------------------------------------
# the ground and what an item may not stand on
# --------------------------------------------------------------------------------------------


def r2(v: float) -> float:
    return round(v + 0.0, 2)


def _seg_dist(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-12
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


def _ring_dist(ring, e, n) -> float:
    return min(_seg_dist(e, n, *ring[i], *ring[(i + 1) % len(ring)]) for i in range(len(ring)))


def _sidecar_archetype(sid: str) -> str:
    return wg._sidecar(sid).get("archetype") or ""


ARCH = {sid: _sidecar_archetype(sid) for sid in wg.FOOTPRINTS}


def _trails():
    d = json.loads((DATA / "enclosures" / "1812" / "worn_trails_1812.json").read_text(encoding="utf-8"))
    out = []
    for t in d["ground"]["trails"]:
        out.append((t["id"], t["line_local_enu_m"], float(t.get("width_m", 1.0)) / 2 + TRAIL_CLEAR_M))
    return out


TRAILS = _trails()


def _stems():
    out = []
    for path in sorted((DATA / "flora" / "plantings").glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if str(r.get("scene")) != "1812":
            continue
        for st in r.get("stems", []):
            e, n = st["at_local_enu_m"]
            out.append((f"{r['id']}/{st['id']}", float(e), float(n)))
    return out


STEMS = _stems()


def _yards():
    out = {}
    for path in sorted((DATA / "enclosures" / "1812").glob("worn_yard_1812_*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        ring = r["ground"]["interior_local_enu_m"]
        for sid in r.get("structure_ids", []):
            out[sid] = ring
    return out


YARDS = _yards()


def _own_fences():
    """The fences a building stands INSIDE (Lee's Place's cabin in its field's worm fence): its
    own enclosure, where its yard goods stand too. Only the inside counts; the line is kept."""
    out = {}
    for sid in KIT:
        ring = wg.FOOTPRINTS.get(sid)
        if not ring:
            continue
        c = wg.centre(ring)
        out[sid] = tuple(f for f, fr in wg.FOOTPRINTS.items()
                         if ARCH.get(f) in FENCES and f != sid and wg._point_in_ring(fr, *c))
    return out


OWN_FENCES = _own_fences()


def refusal(pts, own: str, placed) -> str | None:
    """Why an item whose outline is `pts` may not stand, or None."""
    hs = wg.height([p[0] for p in pts], [p[1] for p in pts])
    for p, h in zip(pts, hs):
        if not math.isfinite(h):
            return f"off the modelled ground at ({p[0]:.1f}, {p[1]:.1f})"
        if h < DRY_Y:
            return f"on wet ground at ({p[0]:.1f}, {p[1]:.1f})"
    probe = list(pts) + [[sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]]
    for sid, ring in wg.FOOTPRINTS.items():
        if sid.startswith("potawatomi_camp") or sid in OWN_FENCES.get(own, ()):
            continue
        fence = ARCH.get(sid) in FENCES
        clear = FENCE_CLEAR_M if fence else FOOTPRINT_CLEAR_M
        for e, n in probe:
            inside = wg._point_in_ring(ring, e, n)
            if fence:
                # a fence is a line: an item may stand on either side of it but not on it, and
                # never inside a garden or a field (nobody stacks wood in the beds)
                if inside and sid != "first_fort_dearborn_pickets_outer":
                    return f"inside {sid}"
                if _ring_dist(ring, e, n) < clear:
                    return f"on the line of {sid}"
            else:
                if inside:
                    return f"inside {sid}"
                if sid != own and _ring_dist(ring, e, n) < clear:
                    return f"against {sid}"
    for sid in OWN_FENCES.get(own, ()):
        for e, n in probe:
            if _ring_dist(wg.FOOTPRINTS[sid], e, n) < FENCE_CLEAR_M:
                return f"on the line of {sid}"
            if not wg._point_in_ring(wg.FOOTPRINTS[sid], e, n):
                return f"outside its own {sid}"
    for tid, line, half in TRAILS:
        for e, n in probe:
            if min(_seg_dist(e, n, *line[i], *line[i + 1]) for i in range(len(line) - 1)) < half:
                return f"on the trail {tid}"
    for stid, se, sn in STEMS:
        for e, n in probe:
            if math.hypot(e - se, n - sn) < STEM_CLEAR_M:
                return f"under the planted stem {stid}"
    for other in placed:
        for e, n in probe:
            if wg._point_in_ring(other, e, n) or _ring_dist(other, e, n) < ITEM_CLEAR_M:
                return "against an item already placed"
        for e, n in other:
            if wg._point_in_ring(pts, e, n):
                return "over an item already placed"
    return None


# --------------------------------------------------------------------------------------------
# a building's frame
# --------------------------------------------------------------------------------------------


class Frame:
    """A footprint's own frame: u along its first edge, v across it, turned clockwise."""

    def __init__(self, sid: str):
        d = wg._sidecar(sid)
        self.place = d["placement"]
        poly = d["footprint"]["polygon"]
        self.u0 = min(p[0] for p in poly)
        self.u1 = max(p[0] for p in poly)
        self.v0 = min(p[1] for p in poly)
        self.v1 = max(p[1] for p in poly)

    def enu(self, u, v):
        return list(wg._to_enu(u, v, self.place))

    def dir(self, du, dv):
        a = self.enu(0, 0)
        b = self.enu(du, dv)
        return (b[0] - a[0], b[1] - a[1])

    def walls(self):
        """(name, a point at the wall's start, along unit (u, v), out unit (u, v), length)."""
        return {
            "back": ((self.u0, self.v0), (1, 0), (0, -1), self.u1 - self.u0),
            "front": ((self.u0, self.v1), (1, 0), (0, 1), self.u1 - self.u0),
            "left gable": ((self.u0, self.v0), (0, 1), (-1, 0), self.v1 - self.v0),
            "right gable": ((self.u1, self.v0), (0, 1), (1, 0), self.v1 - self.v0),
        }


def compass(de, dn) -> float:
    return (math.degrees(math.atan2(de, dn)) + 360.0) % 360.0


def wood_bearing(de, dn) -> float:
    """yard.js lays a stack's length along (cos b, -sin b) in (E, N): a compass bearing - 90."""
    return r2((compass(de, dn) - 90.0) % 360.0)


def box(c, along, across, half_l, half_d):
    (ae, an), (ce, cn) = along, across
    return [[c[0] + ae * sl * half_l + ce * sd * half_d, c[1] + an * sl * half_l + cn * sd * half_d]
            for sl, sd in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def unit(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


# --------------------------------------------------------------------------------------------
# the dealing
# --------------------------------------------------------------------------------------------


def deal_rick(sid, fr: Frame, rng, length, depth, height, placed, walls_order, stick):
    """A rick against a wall: the first wall, corner and length that stand."""
    W = fr.walls()
    tried = []
    for name in walls_order:
        (u, v), (au, av), (ou, ov), wall_len = W[name]
        along = unit(fr.dir(au, av))
        out = unit(fr.dir(ou, ov))
        L = min(length, wall_len - 0.6)
        while L >= 1.2:
            starts = [0.3, wall_len - 0.3 - L, (wall_len - L) / 2]
            if rng() < 0.5:
                starts[0], starts[1] = starts[1], starts[0]
            for s in starts:
                mid_u = u + au * (s + L / 2) + ou * (WALL_GAP_M + depth / 2)
                mid_v = v + av * (s + L / 2) + ov * (WALL_GAP_M + depth / 2)
                c = fr.enu(mid_u, mid_v)
                pts = box(c, along, out, L / 2, depth / 2)
                why = refusal(pts, sid, placed)
                if why is None:
                    return {"kind": "cordwood", "at_local_enu_m": [r2(c[0]), r2(c[1])],
                            "bearing_deg": wood_bearing(*along), "length_m": r2(L), "depth_m": r2(depth),
                            "height_m": r2(height), "stick": stick, "wall": name}, pts, out, c
                tried.append(f"{name}: {why}")
            L -= 0.6
    return None, tried, None, None


def deal_near(sid, centre, out, rng, half, placed, reach=(1.6, 2.4, 3.2), spread=(0.0, 0.8, -0.8, 1.6, -1.6)):
    """A small item `half` across, set out from `centre` along `out`: the first spot that stands."""
    side = (-out[1], out[0])
    for d in reach:
        for s in spread:
            c = [centre[0] + out[0] * d + side[0] * s, centre[1] + out[1] * d + side[1] * s]
            pts = box(c, side, out, half, half)
            if refusal(pts, sid, placed) is None:
                return c, pts
    return None, None


def deal_place(sid: str, refused: list) -> dict | None:
    what, size, why = KIT[sid]
    fr = Frame(sid)
    rng = Rng(seed_of(RECORD_ID, sid))
    placed = []
    items = []
    wagons = []

    def note_refused(item, reason):
        refused.append({"structure_id": sid, "item": item, "why": reason})

    def add(item, pts):
        item["seed"] = seed_of(sid, len(items), item["kind"])
        items.append(item)
        placed.append(pts)

    back_first = ["back", "left gable", "right gable"]
    if rng() < 0.5:
        back_first = ["back", "right gable", "left gable"]

    if what in (HOUSE, FARM, BAKE, STORE):
        stick = "cord" if what in (BAKE, FARM) or size >= 2 else "stove"
        depth = CORD_DEPTH_M if stick == "cord" else STOVE_DEPTH_M
        length = {0: 2.4, 1: 3.6, 2: 4.8}[size] + rng() * 0.8
        height = 0.95 + 0.35 * rng() + 0.1 * size
        rick, pts, out, c = deal_rick(sid, fr, rng, length, depth, height, placed, back_first, stick)
        if rick is None:
            note_refused("cordwood", "; ".join(pts[-3:]) or "no wall stands")
        else:
            wall = rick.pop("wall")
            add(rick, pts)
            # the chopping block, out in front of the rick, with the split billets round it
            bc, bpts = deal_near(sid, c, out, rng, 0.3, placed, reach=(depth / 2 + 1.5, depth / 2 + 2.2, depth / 2 + 3.0))
            if bc is None:
                note_refused("chopping_block", f"no open ground in front of the rick on the {wall}")
            else:
                add({"kind": "chopping_block", "at_local_enu_m": [r2(bc[0]), r2(bc[1])],
                     "bearing_deg": rick["bearing_deg"], "billets": 3 + int(rng() * 4)}, bpts)
            # an oven's wood: unsplit lengths as well, heaped beyond the rick
            if what in (BAKE, FARM):
                along = unit((math.cos(math.radians(rick["bearing_deg"])), -math.sin(math.radians(rick["bearing_deg"]))))
                for k in (1, -1):
                    hc = [c[0] + along[0] * k * (rick["length_m"] / 2 + 2.2) + out[0] * 0.6,
                          c[1] + along[1] * k * (rick["length_m"] / 2 + 2.2) + out[1] * 0.6]
                    logs = 4 + int(rng() * 3) + size
                    hpts = box(hc, along, out, 1.7, (0.36 * logs * 0.6 + 0.3) / 2 + 0.1)
                    if refusal(hpts, sid, placed) is None:
                        add({"kind": "log_heap", "at_local_enu_m": [r2(hc[0]), r2(hc[1])],
                             "bearing_deg": rick["bearing_deg"], "logs": logs, "log_length_m": r2(3.0 + rng() * 0.6)}, hpts)
                        break
                else:
                    note_refused("log_heap", "no open ground at either end of the rick")

    # a water cask at a back corner: the household's water, carried up from the river or lake
    if what in (HOUSE, FARM, BAKE, SMITH):
        W = fr.walls()
        corners = [("back", 0.55), ("back", None), ("left gable", 0.55), ("right gable", 0.55),
                   ("left gable", None), ("right gable", None)]
        for name, at in corners:
            (u, v), (au, av), (ou, ov), wall_len = W[name]
            s = at if at is not None else wall_len - 0.55
            c = fr.enu(u + au * s + ou * (0.32 + 0.12), v + av * s + ov * (0.32 + 0.12))
            pts = box(c, unit(fr.dir(au, av)), unit(fr.dir(ou, ov)), 0.3, 0.3)
            if refusal(pts, sid, placed) is None:
                add({"kind": "barrel", "pose": "upright", "at_local_enu_m": [r2(c[0]), r2(c[1])],
                     "bearing_deg": r2(compass(*fr.dir(ou, ov)))}, pts)
                break
        else:
            note_refused("barrel", "every corner is taken")

    # trade goods: casks and cases along a gable, off the front corner, where they were landed
    if what == STORE:
        W = fr.walls()
        casks = 3 + 2 * size
        cases = 1 + size
        for name in ("left gable", "right gable"):
            (u, v), (au, av), (ou, ov), wall_len = W[name]
            along = unit(fr.dir(au, av))
            out = unit(fr.dir(ou, ov))
            batch, bpts = [], []
            # the casks two abreast in a rank from the front corner, the cases beyond them
            slots = [("barrel", divmod(k, 2), 0.62, 0.3) for k in range(casks)]
            s0 = wall_len - 0.5 - ((casks + 1) // 2) * 0.62 - 0.35
            slots += [("crate", (k, 0), 1.2, 0.55) for k in range(cases)]
            for kind, (row, col), pitch, half in slots:
                s = (wall_len - 0.5 - row * pitch) if kind == "barrel" else (s0 - row * pitch - 0.25)
                if s < 0.4:
                    break
                off = 0.45 + col * 0.62 if kind == "barrel" else 0.5
                c = fr.enu(u + au * s + ou * off, v + av * s + ov * off)
                pts = box(c, along, out, half, 0.3 if kind == "barrel" else 0.38)
                if refusal(pts, sid, placed) is not None:
                    break
                batch.append({"kind": kind, **({"pose": "upright"} if kind == "barrel" else {"tier": 0}),
                              "at_local_enu_m": [r2(c[0]), r2(c[1])],
                              "bearing_deg": r2(compass(*out)) if kind == "barrel" else wood_bearing(*along)})
                bpts.append(pts)
            if len(batch) >= 3:
                for it, p in zip(batch, bpts):
                    add(it, p)
                break
        else:
            note_refused("trade goods", "neither gable has open ground for the casks")

    # the smithy: a slack tub by the door and a heap of slabs for the fire
    if what == SMITH:
        W = fr.walls()
        (u, v), (au, av), (ou, ov), wall_len = W["front"]
        out = unit(fr.dir(ou, ov))
        door = fr.enu(u + au * wall_len * 0.5, v + av * wall_len * 0.5)
        for s in (2.0, -2.0, 2.8, -2.8):  # beside the doorway, clear of its swing
            c = [door[0] + out[0] * 0.6 + unit(fr.dir(au, av))[0] * s,
                 door[1] + out[1] * 0.6 + unit(fr.dir(au, av))[1] * s]
            pts = box(c, unit(fr.dir(au, av)), out, 0.3, 0.3)
            if refusal(pts, sid, placed) is None:
                add({"kind": "barrel", "pose": "upright", "at_local_enu_m": [r2(c[0]), r2(c[1])],
                     "bearing_deg": r2(compass(*out))}, pts)
                break
        for name in back_first:
            (u, v), (au, av), (ou, ov), wall_len = W[name]
            c = fr.enu(u + au * wall_len * 0.5 + ou * 1.4, v + av * wall_len * 0.5 + ov * 1.4)
            along = unit(fr.dir(au, av))
            pts = box(c, along, unit(fr.dir(ou, ov)), 0.9, 0.7)
            if refusal(pts, sid, placed) is None:
                add({"kind": "slab_heap", "at_local_enu_m": [r2(c[0]), r2(c[1])],
                     "bearing_deg": wood_bearing(*along), "pieces": 9 + int(rng() * 5)}, pts)
                break
        else:
            note_refused("slab_heap", "no wall has open ground")

    # carts and wagons on the building's own worn yard, nose out from the door side
    if what in (STABLE, FARM):
        yard = YARDS.get(sid)
        want = ["cart"] + (["farm_box"] if what == STABLE and size >= 1 else [])
        if yard is None:
            note_refused("cart", "no worn yard is recorded for it")
        else:
            W = fr.walls()
            (u, v), (au, av), (ou, ov), wall_len = W["front"]
            out = unit(fr.dir(ou, ov))
            along = unit(fr.dir(au, av))
            door = fr.enu(u + au * wall_len * 0.5, v + av * wall_len * 0.5)
            for kind in want:
                L, Wd = (3.6, 1.7) if kind == "cart" else (5.4, 1.9)
                done = False
                for d in (4.0, 5.5, 7.0, 8.5, 10.0):
                    for s in (0.0, 3.0, -3.0, 6.0, -6.0, 9.0, -9.0):
                        c = [door[0] + out[0] * d + along[0] * s, door[1] + out[1] * d + along[1] * s]
                        # stood across the yard, its shafts or tongue toward the door side
                        turn = 25.0 * (rng() - 0.5)
                        hd = compass(*along) + turn
                        fwd = (math.sin(math.radians(hd)), math.cos(math.radians(hd)))
                        side = (-fwd[1], fwd[0])
                        pts = box(c, fwd, side, L / 2, Wd / 2)
                        # on the stable's own worn yard; a farm's cart anywhere in its dooryard
                        if what == STABLE and not wg._point_in_ring(yard, *c):
                            continue
                        if refusal(pts, sid, placed) is None:
                            wagons.append({"id": f"{sid}_{kind}", "kind": kind, "belongs_to": sid,
                                           "in_yard_of": sid, "tilt": False, "yoke": False,
                                           "confidence": "reconstructed",
                                           "at_local_enu_m": [r2(c[0]), r2(c[1])], "bearing_deg": r2(hd % 360.0)})
                            placed.append(pts)
                            done = True
                            break
                    if done:
                        break
                if not done:
                    note_refused(kind, "no open ground on its worn yard")

    if not items and not wagons:
        return None
    return {"structure_id": sid, "name": wg._sidecar(sid).get("name"), "what": what,
            "why_goods": why, "confidence": "reconstructed", "items": items, "wagons": wagons}


# --------------------------------------------------------------------------------------------
# the record
# --------------------------------------------------------------------------------------------


def build() -> tuple[dict, dict]:
    refused: list = []
    lots = []
    for sid in sorted(KIT):
        if sid not in wg.FOOTPRINTS:
            refused.append({"structure_id": sid, "item": "everything", "why": "it has no sidecar in the 1812 scene"})
            continue
        lot = deal_place(sid, refused)
        if lot:
            lots.append(lot)
    wagons = [w for lot in lots for w in lot.pop("wagons")]
    counts = {}
    for lot in lots:
        for it in lot["items"]:
            counts[it["kind"]] = counts.get(it["kind"], 0) + 1
    for w in wagons:
        counts[w["kind"]] = counts.get(w["kind"], 0) + 1
    record = {
        "_doc": ("The 1812 settlement's yard goods (T-3458): a woodpile, a chopping block and a water cask at "
                 "every house, an oven's wood at the two bake houses, casks and cases at the factory and the "
                 "merchant's shop, a slack tub and slabs at the armourer's, carts at the stables and at Lee's "
                 "Place. GENERATED by tools/generate_yard_goods_1812.py from the 1812 sidecars, fences, worn "
                 "yards, trails and plantings, and re-derived byte for byte by tools/check.sh. Drawn by "
                 f"renderers/web/js/yard.js. Every item is reconstructed: docs/LIBERTIES.md {LIBERTY}."),
        "id": RECORD_ID,
        "name": "Wood, casks and carts round the 1812 houses",
        "kind": "yard_goods",
        "scene": "1812",
        "target_date": SCENE_DATE,
        "coordinates": "Local East-North-Up metres from data/datum.json's origin.",
        "counts": dict(sorted(counts.items())),
        "existence": {
            "value": "the 1812 households and the post kept firewood, water, trade goods and carts at their doors",
            "confidence": "reconstructed",
            "sources": [],
            "note": ("THE OWNER'S REQUEST, NOT A SOURCE (2026-11-07, T-3458): the things a frontier household and "
                     "a garrison post could not do without, at each place, sensibly placed. What bounds it: every "
                     "fire in 1812 Chicago, kitchen, oven and forge, burned wood, so a pile stands at every hearth; "
                     "the government factory's trade goods were given out on the scene date, so its casks and "
                     "cases are at its door; the evacuation of the 15th went out with wagons (Quaife 1913, as the "
                     "battle jaunt quotes him), so the post had them, and here they stand in its stable yard. No "
                     f"source places any one of these objects. docs/LIBERTIES.md {LIBERTY}."),
        },
        "form": {
            "stove_stick_m": {"value": STOVE_DEPTH_M, "confidence": "reconstructed",
                              "note": "A 4 ft stick sawn in two for a hearth's fire-dogs; no source gives a length."},
            "log_m": {"value": [0.32, 0.22], "confidence": "reconstructed",
                      "note": "An unsplit length a man could carry or a horse drag in; as the 1835 record's."},
            "block_m": {"value": [0.5, 0.46], "confidence": "reconstructed",
                        "note": "A chopping block sawn off a butt log, about knee high; as the 1835 record's."},
            "slab_m": {"value": [1.4, 0.26, 0.06], "confidence": "reconstructed",
                       "note": "Bark-edged slabs, the offcuts of hewing; as the 1835 record's."},
            "barrel_height_m": {"value": 0.84, "confidence": "reconstructed",
                                "note": "A cask on its head; the 1835 layer's own cask."},
            "barrel_belly_diameter_m": {"value": 0.53, "confidence": "reconstructed", "note": "As the 1835 layer's."},
            "barrel_head_diameter_m": {"value": 0.45, "confidence": "reconstructed", "note": "As the 1835 layer's."},
            "crate_size_m": {"value": [1.05, 0.72, 0.62], "confidence": "reconstructed",
                             "note": "A packing case of trade goods; as the 1835 layer's."},
            "cart_m": {"value": [1.98, 1.07, 0.5, 1.42, 0.86, 2.44], "confidence": "reconstructed",
                       "note": "A two-wheeled cart, the frontier's commonest vehicle; as the 1835 layer's."},
        },
        "rule": {
            "value": ("A rick against the back wall (then a gable), racked a hand's gap off it; a block in front "
                      "of the rick; a cask at a back corner; trade goods along a gable from the front corner; a "
                      "cart on the building's own worn yard off its front. Nothing on wet ground, in or against a "
                      "footprint, on a fence or in a garden, on a worn trail, under a planted stem, or on another item."),
            "confidence": "reconstructed",
            "note": f"tools/generate_yard_goods_1812.py; {LIBERTY}.",
        },
        "lots": lots,
        "wagons": wagons,
        "refused": refused,
        "research_note": ("WHAT WOULD MOVE ANY OF THIS: a recollection, inventory or claim of 1812 Chicago naming a "
                          "woodpile, a cart, a cask or a well at a particular house; the factory's own returns for "
                          "1812, which would say what goods it held; a view of the post's out-buildings. WHAT THIS "
                          "DOES NOT DRAW: an ash hopper, a soap kettle, a well sweep or a canoe drawn up (no model "
                          "of any yet), anyone working, and nothing inside the fort's pickets."),
    }
    index = {
        "_doc": ("Manifest for the 1812 yard layer (T-3458): the yard goods round the 1812 houses. A static host "
                 "cannot be globbed, so the renderer fetches this file and then exactly the records it names. "
                 "data/scenes/1812.json names `yard_dir: yard/1812/`; the 1835 town reads data/yard/index.json."),
        "version": 1,
        "scene": "1812",
        "scene_date": SCENE_DATE,
        "coordinates": "Local East-North-Up metres from data/datum.json's origin.",
        "yard": [{"id": RECORD_ID, "file": OUT.name}],
    }
    return record, index


def assertions(record: dict) -> list[str]:
    bad = []
    pts_all = []
    for lot in record["lots"]:
        for it in lot["items"]:
            pts_all.append((lot["structure_id"], it))
    for w in record["wagons"]:
        pts_all.append((w["belongs_to"], w))
    for sid, it in pts_all:
        e, n = it["at_local_enu_m"]
        for other, ring in wg.FOOTPRINTS.items():
            if ARCH.get(other) in FENCES or other.startswith("potawatomi_camp"):
                continue
            if wg._point_in_ring(ring, e, n):
                bad.append(f"{sid}: a {it['kind']} at ({e}, {n}) stands inside {other}")
        h = float(wg.height([e], [n])[0])
        if not math.isfinite(h) or h < DRY_Y:
            bad.append(f"{sid}: a {it['kind']} at ({e}, {n}) is off dry ground")
    houses = [s for s, k in KIT.items() if k[0] in (HOUSE, FARM)]
    have = {lot["structure_id"] for lot in record["lots"] if any(i["kind"] == "cordwood" for i in lot["items"])}
    for s in houses:
        if s not in have:
            bad.append(f"{s}: a house with no woodpile")
    return bad


def text(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="re-derive and diff; write nothing")
    args = ap.parse_args()
    record, index = build()
    bad = assertions(record)
    for b in bad:
        print(f"yard goods 1812: FAIL {b}")
    if bad:
        return 1
    want = {OUT: text(record), INDEX: text(index)}
    if args.check:
        stale = [p for p, t in want.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        for p in stale:
            print(f"yard goods 1812: {p.relative_to(ROOT)} is stale; run python3 tools/generate_yard_goods_1812.py")
        if stale:
            return 1
        c = record["counts"]
        print(f"yard goods 1812: {len(record['lots'])} places, " + ", ".join(f"{v} {k}" for k, v in c.items())
              + f"; {len(record['refused'])} refused in writing — re-derived byte for byte")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p, t in want.items():
        p.write_text(t, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(record['lots'])} places, {record['counts']}) and {INDEX.relative_to(ROOT)}")
    for r in record["refused"]:
        print(f"  refused: {r['structure_id']} {r['item']}: {r['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
