#!/usr/bin/env python3
"""T-3510: the 1812 river's crossing boats, written into data/boats/crossings_1812.json.

Kevin, 2026-11-08: "In 1812 there are no bridges so can you in all scenes and areas where we
might want to cross like at some of the docks which need to me made photographic wood and at
the forks at hardscrabble, at logical places up and down the river provide a small period
appropriate boat or canoe that looks photographic correct and allow me to walk up to the boat
and interact is board and cross river ... The boats should look a bit different, different
wood weathering and slightly different shape". Then: "Don't add a bunch of docks, in most
cases you should board from the bank other than maybe around the fort".

So every boat here is drawn up on a bank (one rides at the fort's wharf), and no landing stage
is built. Each row below is authored: the bank it is drawn up on, the bearing it crosses on,
its kind, its hull and its look. Everything else is DERIVED here from the committed 1812
ground (data/terrain/epochs/e1830_natural/, the box heightfield and the South Branch apron)
and refused if the ground will not carry it:

  - the two waterlines, marched along the crossing bearing (the water is ground below 0, the
    1812 water surface, exactly as terrain.js `isWater` reads it);
  - the rest pose on each bank: the hull along the crossing line, bow up the bank with a
    third of it on the ground and its stern afloat;
  - the launch and landing poses, the hull wholly afloat a little off each waterline;
  - where the visitor stands on each bank, dry ground beside the bow, clear of every 1812
    footprint;
  - the water under the whole path, which must float the hull's own draft.

The runtime (renderers/web/js/crossings.js) builds each hull from these numbers, lays it on
the ground it reads itself, and plays Cross: step in, push off, paddle or row across, run
ashore, step out. `--check` re-derives the file and refuses any difference.

    python3 tools/lay_crossing_boats_1812.py          write the file
    python3 tools/lay_crossing_boats_1812.py --check  refuse a file that is not what this writes
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "boats" / "crossings_1812.json"
EPOCH = ROOT / "data" / "terrain" / "epochs" / "e1830_natural"
DATUM = ROOT / "data" / "datum.json"
STRUCTURES = ROOT / "data" / "structures"
LIBERTY = "L-1812-crossing-boats-3510"
SCENE_DATE = "1812-08-14"

# Paddled and rowed at a steady working pace, metres a second (an unhurried canoe makes
# 1.5-2; a laden pirogue less). The crossing's own clock is the runtime's; this is its pace.
SPEED_M_S = 1.6
# Water a hull wants under its keel beyond its draft, everywhere on the path.
UNDER_KEEL_M = 0.10
# How much of a drawn-up hull lies on the bank, as a share of its length.
ON_BANK_SHARE = 0.30
# The steepest bank a hull is drawn up on: its bow may sit this far above the water.
BOW_RISE_MAX_M = 0.65
# A launched hull lies this far off the waterline (its near end), so it floats whole.
LAUNCH_CLEAR_M = 0.9
# The visitor stands this far up the bank from the bow, and this far to one side.
STAND_UP_M = 1.4
STAND_SIDE_M = 1.1
# Dry ground: a stand must be this far above the water, and this far from any footprint.
STAND_DRY_M = 0.06
STAND_CLEAR_M = 1.2
# A drawn-up hull's plan keeps this far off any footprint.
HULL_CLEAR_M = 0.4

KIND_WORDS = {
    "dugout": "dugout (pirogue)",
    "bark_canoe": "elm-bark canoe",
    "skiff": "plank skiff",
}

# The fort's wharf, Whistler's no. 27: the one boat that rides at a landing stage.
WHARF_ID = "first_fort_wharf"

SOURCES_KINZIE = ["moses_kirkland_history_of_chicago_v1", "kinzie_waubun_1856"]
SOURCES_LEES = ["currey_1912_story_of_old_fort_dearborn", "moses_kirkland_history_of_chicago_v1"]

# ---------------------------------------------------------------------------------------
# The authored rows. `bank` is a point on the near bank's dry ground, a few metres from
# the water; `bearing` is the compass bearing the boat crosses on. Hull figures in metres.
# `look`: `tone` the wood's (or bark's) colour in sRGB 0-1, `grey` how far the sun and
# water have silvered it (0 new, 1 grey), `dark` the wet and tarred band at the waterline,
# `moss` a green cast in the bilge, `seed` the run of small differences along the hull.
# ---------------------------------------------------------------------------------------
BOATS = [
    {
        "id": "kinzie_pirogue_1812_a",
        "name": "The Kinzies' old pirogue",
        "kind": "dugout",
        "bank": [1150.6, 311.0], "bearing": 186.0,
        "banks": {"a": "the Kinzie house", "b": "the fort side"},
        "hull": {"length_m": 7.2, "beam_m": 0.82, "depth_m": 0.42, "sheer_m": 0.07, "rocker_m": 0.05,
                 "fullness": 4.2, "end_m": 0.36, "thick_m": 0.055, "draft_m": 0.17},
        "look": {"tone": [0.47, 0.42, 0.36], "grey": 0.62, "dark": 0.55, "moss": 0.25, "seed": 1101},
        "existence": {
            "confidence": "attested", "sources": SOURCES_KINZIE,
            "note": ("Moses and Kirkland (1895), of April 1812, after Wau-Bun: 'The family was hurried into "
                     "two old pirogues [dug-out tree-trunks] that were moored near the house and paddled with "
                     "all possible haste across the river to take refuge in the fort.' The two pirogues are "
                     "theirs; their size, wood, shape and where on the bank each lies are reconstructed."),
        },
    },
    {
        "id": "kinzie_pirogue_1812_b",
        "name": "The Kinzies' second pirogue",
        "kind": "dugout",
        "bank": [1144.8, 311.6], "bearing": 183.0,
        "banks": {"a": "the Kinzie house", "b": "the fort side"},
        "hull": {"length_m": 5.9, "beam_m": 0.70, "depth_m": 0.37, "sheer_m": 0.10, "rocker_m": 0.07,
                 "fullness": 3.1, "end_m": 0.30, "thick_m": 0.05, "draft_m": 0.15},
        "look": {"tone": [0.42, 0.33, 0.25], "grey": 0.35, "dark": 0.7, "moss": 0.1, "seed": 1102},
        "existence": {
            "confidence": "attested", "sources": SOURCES_KINZIE,
            "note": ("The second of the 'two old pirogues ... moored near the house' (Moses and Kirkland 1895, "
                     "after Wau-Bun). Smaller and browner than the first, an older log less silvered; its form "
                     "is reconstructed."),
        },
    },
    {
        "id": "fort_wharf_skiff_1812",
        "name": "The garrison's skiff at the wharf",
        "kind": "skiff",
        "wharf": WHARF_ID, "bearing": 8.0,
        "banks": {"a": "the fort's wharf", "b": "the Kinzie side"},
        "hull": {"length_m": 5.1, "beam_m": 1.32, "depth_m": 0.5, "sheer_m": 0.16, "rocker_m": 0.04,
                 "transom": 0.62, "flare": 0.22, "thick_m": 0.03, "draft_m": 0.16},
        "look": {"tone": [0.50, 0.44, 0.36], "grey": 0.5, "dark": 0.85, "moss": 0.15, "seed": 1201},
        "existence": {
            "confidence": "reconstructed", "sources": ["whistler_1808_fort_dearborn_draught"],
            "note": ("A post on a river kept boats: Whistler's 1808 draught names the wharf (no. 27) and the "
                     "company's stores came by water. No source names or describes a boat of the garrison in "
                     "August 1812; this small flat-bottomed skiff of sawn plank, tied at the wharf, is "
                     "reconstructed."),
        },
    },
    {
        "id": "burns_skiff_1812",
        "name": "The Burns family's skiff",
        "kind": "skiff",
        "bank": [794.0, 96.0], "bearing": 178.0,
        "banks": {"a": "the Burns house", "b": "the south bank path"},
        "hull": {"length_m": 4.4, "beam_m": 1.18, "depth_m": 0.44, "sheer_m": 0.2, "rocker_m": 0.06,
                 "transom": 0.55, "flare": 0.3, "thick_m": 0.028, "draft_m": 0.14},
        "look": {"tone": [0.44, 0.40, 0.33], "grey": 0.75, "dark": 0.6, "moss": 0.35, "seed": 1202},
        "existence": {
            "confidence": "reconstructed", "sources": ["moses_kirkland_history_of_chicago_v1"],
            "note": ("In April 1812 the man and boy escaping Lee's Place 'called across' the river to Burns's "
                     "family (Moses and Kirkland 1895), who lived on the north bank opposite the path. A family "
                     "there kept a boat to cross; this skiff, its build and where it lies are reconstructed."),
        },
    },
    {
        "id": "camp_mouth_canoe_1812_a",
        "name": "An elm-bark canoe at the camp by the creek mouth",
        "kind": "bark_canoe",
        "bank": [772.0, 14.0], "bearing": 4.0,
        "banks": {"a": "the camp by the creek mouth", "b": "the north bank by the Burns house"},
        "hull": {"length_m": 5.6, "beam_m": 0.92, "depth_m": 0.34, "sheer_m": 0.12, "rocker_m": 0.06,
                 "upturn_m": 0.24, "fullness": 1.7, "thick_m": 0.012, "draft_m": 0.12},
        "look": {"tone": [0.36, 0.31, 0.26], "grey": 0.2, "dark": 0.4, "moss": 0.0, "seed": 1301},
        "existence": {
            "confidence": "reconstructed", "sources": ["kinzie_waubun_1856", "currey_1912_story_of_old_fort_dearborn"],
            "note": ("The Potawatomi families gathered at Chicago in August 1812 camped by the river (Wau-Bun; "
                     "Currey 1912), and on these rivers the canoe was how people and goods moved. The canoes of "
                     "the Chicago country were most often of elm bark, birch being scarce this far south. This "
                     "canoe is equipment, not a person, and is reconstructed: its size, its sewing and where it "
                     "lies are ours."),
            "standing_constraint_note": ("Drawn unmanned at the camp's landing. AGENTS.md's standing constraint "
                                         "stands: no ceremony or council is staged, and the camp's own records "
                                         "keep their review flags and reasons."),
        },
    },
    {
        "id": "camp_mouth_canoe_1812_b",
        "name": "A small elm-bark canoe at the camp by the creek mouth",
        "kind": "bark_canoe",
        "bank": [764.5, 13.0], "bearing": 358.0,
        "banks": {"a": "the camp by the creek mouth", "b": "the north bank west of the Burns house"},
        "hull": {"length_m": 4.3, "beam_m": 0.8, "depth_m": 0.3, "sheer_m": 0.08, "rocker_m": 0.08,
                 "upturn_m": 0.18, "fullness": 1.4, "thick_m": 0.012, "draft_m": 0.11},
        "look": {"tone": [0.42, 0.36, 0.30], "grey": 0.45, "dark": 0.3, "moss": 0.0, "seed": 1302},
        "existence": {
            "confidence": "reconstructed", "sources": ["kinzie_waubun_1856"],
            "note": ("A second, smaller elm-bark canoe of the camp's, lighter and more weathered; reconstructed "
                     "as the first is."),
            "standing_constraint_note": ("Drawn unmanned. No ceremony or council is staged."),
        },
    },
    {
        "id": "forks_pirogue_1812",
        "name": "The garrison's pirogue at the forks",
        "kind": "dugout",
        "bank": [118.0, -66.0], "bearing": 318.0,
        "banks": {"a": "the forks house", "b": "the point between the branches"},
        "hull": {"length_m": 6.4, "beam_m": 0.76, "depth_m": 0.4, "sheer_m": 0.05, "rocker_m": 0.03,
                 "fullness": 5.0, "end_m": 0.42, "thick_m": 0.06, "draft_m": 0.16},
        "look": {"tone": [0.55, 0.47, 0.37], "grey": 0.45, "dark": 0.5, "moss": 0.2, "seed": 1103},
        "existence": {
            "confidence": "reconstructed", "sources": ["whistler_1808_fort_dearborn_draught", "quaife_1913"],
            "note": ("Whistler's draught and Quaife (1913) put the company's cornfield and a house at the forks, "
                     "which the garrison worked; the soldier's house stands across the water on the point. A "
                     "dugout to cross between them is reconstructed."),
        },
    },
    {
        "id": "lees_place_canoe_1812",
        "name": "Lee's Place canoe",
        "kind": "bark_canoe",
        "bank": [-1641.4, -4245.4], "bearing": 152.0,
        "banks": {"a": "the Lee's Place cabin", "b": "the haystacks"},
        "hull": {"length_m": 5.0, "beam_m": 0.86, "depth_m": 0.33, "sheer_m": 0.1, "rocker_m": 0.05,
                 "upturn_m": 0.2, "fullness": 1.6, "thick_m": 0.012, "draft_m": 0.12},
        "look": {"tone": [0.33, 0.29, 0.25], "grey": 0.3, "dark": 0.5, "moss": 0.0, "seed": 1303},
        "existence": {
            "confidence": "attested", "sources": SOURCES_LEES,
            "note": ("Currey (1912), of 6 April 1812 at Lee's Place: the discharged soldier 'walked in a "
                     "deliberate manner down the path toward the canoes tied up at the river bank'. Lee's Place, "
                     "later Hardscrabble, was 'on the northwestern side of the South branch, near its forks' "
                     "(Moses and Kirkland 1895), its haystacks across the water. The canoes are attested; that "
                     "this one is of elm bark, its size and shape are reconstructed."),
        },
    },
    {
        "id": "lees_place_pirogue_1812",
        "name": "Lee's Place pirogue",
        "kind": "dugout",
        "bank": [-1646.6, -4241.0], "bearing": 156.0,
        "banks": {"a": "the Lee's Place cabin", "b": "the haystacks"},
        "hull": {"length_m": 5.4, "beam_m": 0.72, "depth_m": 0.36, "sheer_m": 0.12, "rocker_m": 0.08,
                 "fullness": 2.6, "end_m": 0.26, "thick_m": 0.05, "draft_m": 0.14},
        "look": {"tone": [0.38, 0.31, 0.24], "grey": 0.55, "dark": 0.45, "moss": 0.3, "seed": 1104},
        "existence": {
            "confidence": "attested", "sources": SOURCES_LEES,
            "note": ("The second of 'the canoes tied up at the river bank' at Lee's Place (Currey 1912). A "
                     "dugout is the farm's likeliest second boat; its kind and form are reconstructed."),
        },
    },
    {
        "id": "lee_house_pirogue_1812",
        "name": "The Lee family's pirogue",
        "kind": "dugout",
        "bank": [1192.0, -345.0], "bearing": 78.0,
        "banks": {"a": "the Lee house", "b": "the spit"},
        "hull": {"length_m": 4.9, "beam_m": 0.68, "depth_m": 0.34, "sheer_m": 0.09, "rocker_m": 0.06,
                 "fullness": 3.6, "end_m": 0.3, "thick_m": 0.045, "draft_m": 0.13},
        "look": {"tone": [0.58, 0.52, 0.44], "grey": 0.8, "dark": 0.35, "moss": 0.15, "seed": 1105},
        "existence": {
            "confidence": "reconstructed", "sources": ["kinzie_waubun_1856", "currey_1912_story_of_old_fort_dearborn"],
            "note": ("The Lee family's town house stood on the lake shore near the river's outlet (Wau-Bun; "
                     "Currey 1912), with the spit across the water. A dugout drawn up below the house to cross "
                     "to the spit is reconstructed."),
        },
    },
    {
        "id": "south_branch_pirogue_1812",
        "name": "A trader's pirogue on the South Branch",
        "kind": "dugout",
        "bank": [226.0, -1385.0], "bearing": 268.0,
        "banks": {"a": "the South Branch path", "b": "the west bank"},
        "hull": {"length_m": 6.8, "beam_m": 0.8, "depth_m": 0.4, "sheer_m": 0.06, "rocker_m": 0.04,
                 "fullness": 3.8, "end_m": 0.38, "thick_m": 0.055, "draft_m": 0.16},
        "look": {"tone": [0.36, 0.29, 0.22], "grey": 0.25, "dark": 0.75, "moss": 0.1, "seed": 1106},
        "existence": {
            "confidence": "reconstructed", "sources": ["andreas_1884_v1", "currey_1912_story_of_old_fort_dearborn"],
            "note": ("The South Branch was the road to the portage and the Desplaines, and the path up its east "
                     "bank ran to Lee's Place (Andreas; Currey 1912). A trader's dugout drawn up where the path "
                     "comes to the water is reconstructed."),
        },
    },
    {
        "id": "north_branch_canoe_1812",
        "name": "An elm-bark canoe on the North Branch",
        "kind": "bark_canoe",
        "bank": [-60.0, 420.0], "bearing": 258.0,
        "banks": {"a": "the North Branch's east bank", "b": "its west bank"},
        "hull": {"length_m": 4.7, "beam_m": 0.84, "depth_m": 0.31, "sheer_m": 0.14, "rocker_m": 0.07,
                 "upturn_m": 0.28, "fullness": 1.5, "thick_m": 0.012, "draft_m": 0.11},
        "look": {"tone": [0.30, 0.27, 0.24], "grey": 0.15, "dark": 0.55, "moss": 0.0, "seed": 1304},
        "existence": {
            "confidence": "reconstructed", "sources": ["kinzie_waubun_1856"],
            "note": ("The North Branch was travelled by canoe; an elm-bark canoe drawn up on its east bank is "
                     "reconstructed."),
            "standing_constraint_note": "Drawn unmanned.",
        },
    },
]


# ---------------------------------------------------------------------------------------
# The ground, read as terrain.js reads it: the box heightfield, and outside the box, inside
# its cut, the South Branch apron. Bilinear, the same sampler the mesh is built on.
# ---------------------------------------------------------------------------------------
class Ground:
    def __init__(self) -> None:
        import struct
        self.grids = []
        for name in ("heightfield.json", "apron_south_branch.json"):
            meta = json.loads((EPOCH / name).read_text())
            raw = (EPOCH / meta["bin"]).read_bytes()
            count = meta["rows"] * meta["cols"]
            vals = struct.unpack(f"<{count}h", raw[: count * 2])
            self.grids.append((meta, vals))
        self.box = self.grids[0][0]
        self.apron = self.grids[1][0]

    @staticmethod
    def _bil(meta, vals, e, n):
        c = (e - meta["origin_e"]) / meta["cell_m"]
        r = (n - meta["origin_n"]) / meta["cell_m"]
        c0, r0 = math.floor(c), math.floor(r)
        if c0 < 0 or r0 < 0 or c0 + 1 >= meta["cols"] or r0 + 1 >= meta["rows"]:
            return None
        fc, fr = c - c0, r - r0
        cols, s = meta["cols"], meta["scale"]
        v00 = vals[r0 * cols + c0]; v01 = vals[r0 * cols + c0 + 1]
        v10 = vals[(r0 + 1) * cols + c0]; v11 = vals[(r0 + 1) * cols + c0 + 1]
        return ((v00 * (1 - fc) + v01 * fc) * (1 - fr) + (v10 * (1 - fc) + v11 * fc) * fr) * s + meta["offset"]

    def h(self, e: float, n: float) -> float | None:
        box = self.box
        inside = (box["origin_e"] <= e <= box["origin_e"] + (box["cols"] - 1) * box["cell_m"]
                  and box["origin_n"] <= n <= box["origin_n"] + (box["rows"] - 1) * box["cell_m"])
        if not inside:
            cut = self.apron["cut_local_enu_m"]
            if cut["e"][0] <= e <= cut["e"][1] and cut["n"][0] <= n <= cut["n"][1]:
                return self._bil(*self.grids[1], e, n)
            return None
        return self._bil(*self.grids[0], e, n)


def unit(bearing: float) -> tuple[float, float]:
    r = math.radians(bearing)
    return math.sin(r), math.cos(r)


def r2(v: float) -> float:
    return round(v + 0.0, 2)


def footprints_1812() -> list[tuple[str, list[tuple[float, float]]]]:
    """Every structure standing on the scene date, its footprint in local ENU (walker.js's rule)."""
    datum = json.loads(DATUM.read_text())
    out = []
    for f in sorted(STRUCTURES.glob("*.json")):
        rec = json.loads(f.read_text())
        poly = (rec.get("footprint") or {}).get("polygon")
        for ph in rec.get("phases", []):
            rng = ph.get("documented_range") or {}
            fr, to = str(rng.get("from") or ""), str(rng.get("to") or "9999")
            if not fr or fr[:10] > SCENE_DATE or to[:10] < SCENE_DATE:
                continue
            p = ph.get("position") or {}
            poly = ((ph.get("footprint") or {}).get("polygon")) or poly
            if "utm_e" not in p or not poly:
                break
            e0 = p["utm_e"] - datum["origin_utm_e"]
            n0 = p["utm_n"] - datum["origin_utm_n"]
            th = math.radians(p.get("rotation_deg") or 0.0)
            c, s = math.cos(th), math.sin(th)
            out.append((rec["id"], [(e0 + u * c + v * s, n0 - u * s + v * c) for u, v in poly],
                        (e0, n0, p.get("rotation_deg") or 0.0, poly)))
            break
    return out


def inside(e, n, pts) -> bool:
    hit = False
    j = len(pts) - 1
    for i in range(len(pts)):
        (xi, yi), (xj, yj) = pts[i], pts[j]
        if (yi > n) != (yj > n) and e < (xj - xi) * (n - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def dist_to_poly(e, n, pts) -> float:
    if inside(e, n, pts):
        return 0.0
    best = math.inf
    for i in range(len(pts)):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((e - ax) * dx + (n - ay) * dy) / L2))
        best = min(best, math.hypot(e - (ax + t * dx), n - (ay + t * dy)))
    return best


class Refused(Exception):
    pass


def march(ground: Ground, e, n, d, start=0.0, limit=260.0, step=0.25):
    """Distances along d from (e, n) where the ground first turns to water and back to land."""
    t, wet_from = start, None
    while t <= limit:
        h = ground.h(e + d[0] * t, n + d[1] * t)
        if h is None:
            raise Refused(f"the crossing runs off the 1812 ground at {t:.1f} m")
        if wet_from is None and h < 0:
            wet_from = t
        elif wet_from is not None and h >= 0:
            return wet_from, t
        t += step
    raise Refused("no far bank within reach")


def lay(row: dict, ground: Ground, fps) -> dict:
    hull = row["hull"]
    L, draft = hull["length_m"], hull["draft_m"]
    d = unit(row["bearing"])
    side = (d[1], -d[0])            # to the right of the crossing
    back = (row["bearing"] + 180.0) % 360.0

    if "wharf" in row:
        wid, wpts, (we, wn, wrot, wpoly) = next((f for f in fps if f[0] == row["wharf"]), (None, None, (0, 0, 0, None)))
        if not wid:
            raise Refused(f"its wharf {row['wharf']} is not standing on {SCENE_DATE}")
        th = math.radians(wrot)
        c, s = math.cos(th), math.sin(th)
        to_w = lambda u, v: (we + u * c + v * s, wn - u * s + v * c)
        us = [p[0] for p in wpoly]; vs = [p[1] for p in wpoly]
        u_mid, v_out = (min(us) + max(us)) / 2, max(vs)
        beam = hull["beam_m"]
        # Moored along the wharf's river face, a hand's breadth off it, bow upstream (west).
        rest_c = to_w(u_mid, v_out + beam / 2 + 0.12)
        along = (c, -s)                                   # the wharf's own +u, as a bearing
        along_brg = math.degrees(math.atan2(along[0], along[1])) % 360
        rest_brg = (along_brg + 180.0) % 360.0
        stand_a = to_w(u_mid + 0.6, v_out - 0.9)
        rest_a = {"e": r2(rest_c[0]), "n": r2(rest_c[1]), "bearing": round(rest_brg, 1), "afloat": True}
        launch_a = (rest_c[0] + d[0] * 2.2, rest_c[1] + d[1] * 2.2)
        wa_t = 0.0
        e0, n0 = rest_c
        _, land_t = march(ground, e0, n0, d, start=0.0)
        w_far = (e0 + d[0] * land_t, n0 + d[1] * land_t)
        wa = None
        for k in range(0, 40):
            h = ground.h(launch_a[0], launch_a[1])
            if h is not None and h <= -(draft + UNDER_KEEL_M):
                break
            launch_a = (launch_a[0] + d[0] * 0.25, launch_a[1] + d[1] * 0.25)
        else:
            raise Refused("the wharf's skiff has no water to launch into")
        stand_a_dry = True
    else:
        e0, n0 = row["bank"]
        h0 = ground.h(e0, n0)
        if h0 is None or h0 < 0:
            raise Refused(f"its bank point ({e0}, {n0}) is not dry 1812 ground")
        wa_t, land_t = march(ground, e0, n0, d)
        wa = (e0 + d[0] * wa_t, n0 + d[1] * wa_t)
        w_far = (e0 + d[0] * land_t, n0 + d[1] * land_t)
        rest_a, stand_a = drawn_up(ground, wa, d, back, L, side, fps, row["id"], "a")
        launch_a = afloat_from(ground, wa, d, L, draft)

    rest_b, stand_b = drawn_up(ground, w_far, (-d[0], -d[1]), row["bearing"], L, (-side[0], -side[1]), fps, row["id"], "b")
    launch_b = afloat_from(ground, w_far, (-d[0], -d[1]), L, draft)

    # The water under the whole path, from one launch to the other, must float the hull.
    path_len = math.hypot(launch_b[0] - launch_a[0], launch_b[1] - launch_a[1])
    if path_len < 6.0:
        raise Refused(f"the river here is too narrow for a {L} m hull to turn and cross ({path_len:.1f} m)")
    shallow = 0.0
    k = 0
    while k * 0.5 <= path_len:
        t = k * 0.5
        e, n = launch_a[0] + d[0] * t, launch_a[1] + d[1] * t
        h = ground.h(e, n)
        if h is None or h > -(draft + UNDER_KEEL_M):
            shallow = max(shallow, (h if h is not None else 9) + draft + UNDER_KEEL_M)
        k += 1
    if shallow > 0.0:
        raise Refused(f"the path runs {shallow:.2f} m too shallow for its {draft} m draft")

    return {
        "id": row["id"],
        "name": row["name"],
        "kind": row["kind"],
        "kind_words": KIND_WORDS[row["kind"]],
        "existence": row["existence"],
        "hull": hull,
        "look": row["look"],
        "liberty": LIBERTY,
        "starts": "a",
        "crossing": {
            "bearing": round(row["bearing"], 1),
            "path_m": r2(path_len),
            "seconds": round(path_len / SPEED_M_S, 1),
        },
        "banks": {
            "a": {"name": row["banks"]["a"], "rest": rest_a, "stand": [r2(stand_a[0]), r2(stand_a[1])],
                  "launch": [r2(launch_a[0]), r2(launch_a[1])],
                  **({"wharf": row["wharf"]} if "wharf" in row else {})},
            "b": {"name": row["banks"]["b"], "rest": rest_b, "stand": [r2(stand_b[0]), r2(stand_b[1])],
                  "launch": [r2(launch_b[0]), r2(launch_b[1])]},
        },
    }


def afloat_from(ground, w, into_water, L, draft):
    """Where a hull launched from waterline w floats whole: at least half its length and
    LAUNCH_CLEAR_M out, and on to where the water under it takes its draft (a shoaling
    shore is waded off, and run onto, over the last few metres)."""
    t = L / 2 + LAUNCH_CLEAR_M
    while t < L / 2 + 30.0:
        e, n = w[0] + into_water[0] * t, w[1] + into_water[1] * t
        h = ground.h(e, n)
        if h is not None and h <= -(draft + UNDER_KEEL_M):
            return (e, n)
        t += 0.25
    raise Refused("no water deep enough to float the hull within 30 m of the bank")


def drawn_up(ground, w, into_water, bow_bearing, L, side, fps, bid, label):
    """The hull drawn up at waterline w: bow up the bank, ON_BANK_SHARE of it ashore."""
    up = (-into_water[0], -into_water[1])        # from the water up the bank
    share = ON_BANK_SHARE
    while True:
        bow = (w[0] + up[0] * share * L, w[1] + up[1] * share * L)
        hb = ground.h(*bow)
        if hb is not None and hb <= BOW_RISE_MAX_M:
            break
        share -= 0.04
        if share < 0.12:
            raise Refused(f"bank {label}: too steep to draw a hull up ({hb} m at the bow)")
    centre = (bow[0] - up[0] * L / 2, bow[1] - up[1] * L / 2)
    # The hull's plan must stand clear of every 1812 footprint (fences and houses alike).
    for k in range(9):
        f = -0.5 + k / 8
        for s in (-1, 0, 1):
            pe = centre[0] + up[0] * f * L + side[0] * s * 0.6
            pn = centre[1] + up[1] * f * L + side[1] * s * 0.6
            hit = next((fid for fid, pts, _ in fps if dist_to_poly(pe, pn, pts) < HULL_CLEAR_M), None)
            if hit:
                raise Refused(f"bank {label}: the drawn-up hull would lie on {hit}")
    rest = {"e": r2(centre[0]), "n": r2(centre[1]), "bearing": round(bow_bearing % 360.0, 1), "afloat": False}
    # The visitor stands up the bank from the bow and to one side of it, on dry ground.
    for up_m in (STAND_UP_M, STAND_UP_M + 0.8, STAND_UP_M + 1.6, STAND_UP_M + 2.6):
        for sgn in (1, -1):
            st = (bow[0] + up[0] * up_m + side[0] * STAND_SIDE_M * sgn,
                  bow[1] + up[1] * up_m + side[1] * STAND_SIDE_M * sgn)
            h = ground.h(*st)
            if h is None or h < STAND_DRY_M:
                continue
            if any(dist_to_poly(st[0], st[1], pts) < STAND_CLEAR_M for _, pts, _ in fps):
                continue
            return rest, st
    raise Refused(f"bank {label}: no dry, clear ground to stand on beside the bow")


def build() -> dict:
    ground = Ground()
    fps = footprints_1812()
    boats, refused = [], []
    for row in BOATS:
        try:
            boats.append(lay(row, ground, fps))
        except Refused as why:
            refused.append(f"{row['id']}: {why}")
    if refused:
        raise SystemExit("lay_crossing_boats_1812: refused —\n  " + "\n  ".join(refused))
    wharves = []
    for wid in sorted({row["wharf"] for row in BOATS if "wharf" in row}):
        _, _, (we, wn, wrot, wpoly) = next(f for f in fps if f[0] == wid)
        rec = json.loads((STRUCTURES / f"{wid}.json").read_text())
        form = next(ph for ph in rec["phases"] if ph.get("form"))["form"]
        us = [p[0] for p in wpoly]; vs = [p[1] for p in wpoly]
        # The crib top is the deck height above the 1812 water; the puncheons lie on it.
        wharves.append({"id": wid, "e": r2(we), "n": r2(wn), "rotation_deg": wrot,
                        "u": [min(us), max(us)], "v": [min(vs), max(vs)],
                        "deck_m": form["deck_height_m"]["value"], "seed": 3510,
                        "deck": "split-log puncheons, flat face up, laid across the crib from the bank out"})
    counts = {"boats": len(boats)}
    for b in boats:
        counts[b["kind"]] = counts.get(b["kind"], 0) + 1
    return {
        "_doc": ("GENERATED by tools/lay_crossing_boats_1812.py (T-3510) - do not hand-edit; --check "
                 "re-derives it. The 1812 river has no bridge, so boats lie drawn up at its crossings and "
                 "renderers/web/js/crossings.js lets a visitor on foot Cross in any of them: step in, push "
                 "off, paddle or row over, run ashore, step out. Each boat stays on the bank it was taken to. "
                 "The hulls are built at load from `hull` and coloured by `look`; their wood and bark are the "
                 "scene's own sheets (the hewn-log relief of the 1812 log houses, the camp's elm bark), so the "
                 f"layer adds no texture. Positions and poses are derived from the 1812 ground; see {LIBERTY}."),
        "id": "crossings_1812",
        "scene": "1812",
        "target_date": SCENE_DATE,
        "coordinates": ("Local East-North-Up metres from data/datum.json's origin. The 1812 water surface is "
                        "Z = 0. `bearing` is a compass bearing (clockwise from north) of the bow."),
        "speed_m_s": SPEED_M_S,
        "counts": counts,
        "liberty": LIBERTY,
        "wharves": wharves,
        "boats": boats,
    }


def dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = dump(build())
    if args.check:
        have = OUT.read_text() if OUT.exists() else ""
        if have != text:
            print(f"lay_crossing_boats_1812: {OUT.relative_to(ROOT)} is not what this tool writes; "
                  "re-run python3 tools/lay_crossing_boats_1812.py")
            return 1
        print(f"lay_crossing_boats_1812: {OUT.relative_to(ROOT)} re-derives byte for byte")
        return 0
    OUT.write_text(text)
    print(f"lay_crossing_boats_1812: wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
