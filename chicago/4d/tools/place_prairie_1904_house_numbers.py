#!/usr/bin/env python3
"""Put each 1904 house's street number where a house of its day carried it (T-3737).

    python3 tools/place_prairie_1904_house_numbers.py              # write data/house_numbers/1904.json
    python3 tools/place_prairie_1904_house_numbers.py --check      # the committed file is what this writes
    python3 tools/place_prairie_1904_house_numbers.py --self-test  # each fault the check refuses, planted

THE ASK. The owner, 2026-11-23: *"i noticed there were no street addresses on most of the
buildings could you do a sweep of what the street address numbers/plaque would have been on
most buildings and then include them accordingly?"*, then *"yes start with 1904"*.

THE NUMBER. The 1911 Sanborn sheets print every avenue lot's number, and the street grid
carries them (`addresses_1911`, data/street_grid/1904.json). The 1909 renumbering moved the
east-west streets' numbers but left this district's avenue numbers where they stood:
Glessner's 1800 is his own 1887 address, Pullman's 1729 and Coleman's 1811 are the numbers the
1880s sources print, and a building permit of June 1888 already gives 2110 (where.js says the
same, for the same reasons). So a lot on Prairie, Indiana or Calumet takes the sheet's number,
and a cross-street lot, or one whose note flags a pre-1909 number, takes none. Where the sheet
prints an old number in parentheses beside the new ('1918 (1936)', the Allerton house), the lot
changed in 1909 and 1904 takes the old one. Inferred: the
number is read for 1911 and carried seven years back on that ruling.

WHERE AND HOW IT WAS SHOWN. Three readings, all of the front door:
  * 1815's own photograph (`chicagology_1815_sears_two_views`, left print) shows light serif
    figures, "1815", centred on the door's transom glass, about a third of the light's height;
  * the Inter Ocean of 2 January 1887 describes 1612 as "the squarely-built house, with the
    number 1612 over the portals" (`chicagology_1612_prairie_occupants`);
  * Glessner's door carries 1800 in its own iron grille (Richardson's sheet 95, built by
    T-2216), so Glessner is left as it is and given nothing more.
Gilt or white-painted figures on the transom over the front door were the common way a house of
the 1880s and 1890s showed its number, and the two readings of this street agree with it. So:
  * a door with a transom light gets the figures centred on that light (`transom`);
  * a door without one gets them on the leaf's top rail (`leaf`), where a house without a
    transom carried brass figures.
1815 and 1612 are attested in form (their own reading); every other house's figures are
reconstructed by the rule above (docs/LIBERTIES.md L-prairie-house-numbers-3737).

HOW THE DOOR IS FOUND. Every 1904 structure's baked model (data/sidecars/1904 -> assets/gltf) is
read in its own frame, as tools/plant_prairie_1904_front_yards.py reads it: a door leaf is a
triangle in a door material (DOOR_MATS) whose foot stands below DOOR_FOOT_M. The leaves are
grouped into doors; a door is the lot's FRONT door when it faces the lot's street (its plane's
normal within FACE_COS of the way to the street) and stands within FRONT_REACH_M of the street
line. Its transom is the glass in the door's own plane, over its width, whose foot is at least
LEAF_SHARE of the doorway's height over the door's foot. One front door to a structure: the one nearest the street.
Only dwellings (`function` residence) take a number: not a shed, a stable or a church. A lot the
sheet gives several numbers gives each house the one its own record names (`symbolic_location`,
'1706 S. Prairie Avenue'), when the sheet prints it there; otherwise doors and numbers are paired
north to south only when they are as many, and a lot that cannot be paired shows none.

WHAT IT WRITES. data/house_numbers/1904.json: per number, the structure, the lot, the figures,
the spot (structure frame, metres: x, y, z as the GLB has them), the outward normal in that
frame, the figures' height, the form and its grade. renderers/web/js/house-numbers.js draws them
all from one canvas-drawn atlas in one draw, through buildings.js's `matrixOf`.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from plant_prairie_1904_front_yards import read_glb, DOOR_MATS, DOOR_FOOT_M  # noqa: E402

GRID = ROOT / "data" / "street_grid" / "1904.json"
SIDECARS = ROOT / "data" / "sidecars" / "1904"
ASSETS = ROOT / "assets"
OUT = ROOT / "data" / "house_numbers" / "1904.json"
LIBERTY = "L-prairie-house-numbers-3737"
TICKET = "T-3737"

AVENUES = ("prairie", "indiana", "calumet")
DOOR_GAP_M = 0.9          # leaves this close together are one door (a pair of leaves, a frame)
FACE_COS = 0.8            # a front door's plane faces the street within about 37 degrees
FRONT_REACH_M = 30.0      # ...and stands within this of the street line
LEAF_SHARE = 0.62         # a transom's foot stands at least this share of the doorway's height over its foot
PLANE_TOL_M = 0.25        # glass this near the door's plane is in the door
TRANSOM_MIN_M = 0.16      # a light shallower than this takes no figures
FIG_SHARE = 0.42          # figures' height as a share of the transom light's (1815: about a third to a half)
FIG_MIN_M, FIG_MAX_M = 0.09, 0.16   # 3.5 to 6.3 in, the period's transom figures
LEAF_FIG_M = 0.10         # brass figures on a leaf's top rail, 4 in
LEAF_RAIL_DROP_M = 0.22   # their middle this far under the leaf's head
PROUD_M = 0.012           # the figures stand this far in front of the face they are on

# Houses whose own model already draws the number, and the reading that says so.
OWN_NUMBER = {
    "glessner_house": "Sheet 95's grille carries 1800 in its top row (T-2216); the model draws it.",
}
# Houses whose figures are read off their own evidence: the form is attested there.
READ_FORM = {
    "sears_meeker_house_1815_prairie": {
        "sources": ["chicagology_1815_sears_two_views"],
        "note": "The left print shows light serif figures '1815' centred on the door's transom glass, "
                "about a third of the light's height.",
    },
    "goodman_house_1612_prairie": {
        "sources": ["chicagology_1612_prairie_occupants"],
        "note": "Inter Ocean, 2 January 1887: 'the squarely-built house, with the number 1612 over the "
                "portals'. Over the door: on its transom.",
    },
}
# What a house number was put over: a dwelling's front door (a house, a double house, flats).
FUNCTIONS = {"residence"}

# THE HANDS. A sign-writer lettered each transom by hand, so no two streets of the 1890s show one
# style: gold leaf or white enamel, a Roman, a block (grotesque) or a sloped letter, outlined
# or shaded in black, larger or smaller on the light. The owner, 2026-11-23, of the first cut:
# "they seem very bright and they are all identical?". Each house takes one of these hands,
# dealt by a stable hash of its structure id (`hand_of`), so neighbours differ and a rebake
# does not reshuffle them. 1815 keeps the light gilt Roman its photograph shows. Gold leaf on
# glass is lit by the street, not a lamp: the fills are leaf and enamel, the shading the dark edge.
# `scale` is the hand's share of the figure height the light allows (FIG_SHARE).
HANDS = {
    "gilt_roman":     {"face": "serif", "weight": "bold",   "style": "normal", "fill": "#cfae62", "edge": "#2e2312", "edge_px": 3, "scale": 1.0},
    "white_roman":    {"face": "serif", "weight": "normal", "style": "normal", "fill": "#d9d4c8", "edge": "#262422", "edge_px": 3, "scale": 0.9},
    "gilt_shaded":    {"face": "serif", "weight": "bold",   "style": "normal", "fill": "#c7a55a", "edge": "#0e0b07", "edge_px": 5, "scale": 0.95},
    "gilt_block":     {"face": "sans",  "weight": "bold",   "style": "normal", "fill": "#ccab63", "edge": "#2a2216", "edge_px": 3, "scale": 0.85},
    "gilt_italic":    {"face": "serif", "weight": "bold",   "style": "italic", "fill": "#d2b36b", "edge": "#2b2214", "edge_px": 3, "scale": 0.9},
    "white_block":    {"face": "sans",  "weight": "normal", "style": "normal", "fill": "#d0cbbf", "edge": "#1f1e1c", "edge_px": 4, "scale": 0.8},
}
HAND_READ = {"sears_meeker_house_1815_prairie": "gilt_roman"}


def hand_of(sid: str) -> str:
    """The hand a house's figures are lettered in: its photograph's, or dealt by its id."""
    if sid in HAND_READ:
        return HAND_READ[sid]
    import hashlib
    names = sorted(HANDS)
    return names[int(hashlib.sha1(sid.encode()).hexdigest(), 16) % len(names)]


def r3(x: float) -> float:
    return round(float(x), 3)


def tracked_models() -> set[str]:
    out = subprocess.run(["git", "ls-files", "-z", "assets/gltf"], cwd=ROOT, capture_output=True, check=True)
    return {s for s in out.stdout.decode().split("\0") if s}


def to_enu(place, x, z):
    """A point of the structure's frame (GLB x, z) on the plan, as buildings.js places it."""
    d = math.radians(place.get("rotation_deg") or 0.0)
    cd, sd = math.cos(d), math.sin(d)
    return (place["local_e"] + x * cd - z * sd, place["local_n"] - x * sd - z * cd)


def dir_to_enu(place, dx, dz):
    d = math.radians(place.get("rotation_deg") or 0.0)
    cd, sd = math.cos(d), math.sin(d)
    return (dx * cd - dz * sd, -dx * sd - dz * cd)


def inside(pt, poly) -> bool:
    x, y = pt
    c = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[i - 1]
        if (ya > y) != (yb > y) and x < (xb - xa) * (y - ya) / (yb - ya) + xa:
            c = not c
    return c


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L)) if L else 0.0
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy), (ax + t * dx, ay + t * dy)


def number_1904(printed: str) -> str:
    """The 1904 number from the sheet's label. The sheet prints a pre-1909 number in parentheses
    beside the new one where the two differ ('1918 (1936)': the Allerton house, 1936 Prairie Avenue
    from 1879, ruling r28-allerton); 1904 takes the old one."""
    m = re.fullmatch(r"\s*(\d+)\s*\((\d+)\)\s*", printed)
    return m.group(2) if m else printed.strip()


def numbered_lots(grid):
    """The avenue lots that take a number (where.js's rule), with their street line."""
    out = []
    for p in grid["parcels"]:
        if p.get("street") not in AVENUES or p.get("side") not in ("east", "west"):
            continue
        if not p.get("addresses_1911") or "pre-1909" in (p.get("note") or ""):
            continue
        ends = [v for k, v in p["corners_local_m"].items() if k.endswith("_street")]
        if len(ends) != 2:
            continue
        out.append({"id": p["id"], "street": p["street"], "side": p["side"], "numbers": [number_1904(a) for a in p["addresses_1911"]],
                    "poly": p["polygon_local_m"], "front": ends, "sources": p.get("sources", [])})
    return out


def doors_of(prims):
    """Each door of a model, in its own frame: its leaves' box, its plane's axis, and the glass in it."""
    door, glass = [], []
    for mat, pos, idx in prims:
        name = mat.lower()
        tri = pos[idx]
        if any(name.startswith(m) for m in DOOR_MATS):
            lo = tri[:, :, 1].min(axis=1)
            tri = tri[lo < DOOR_FOOT_M]
            if len(tri):
                door.append(tri)
        elif name.startswith("glass") or name.startswith("draft_glass"):
            glass.append(tri)
    if not door:
        return []
    tris = np.concatenate(door)
    gtris = np.concatenate(glass) if glass else np.zeros((0, 3, 3))
    # group the leaves on the plan: two triangles are one door when their plan boxes come within
    # DOOR_GAP_M of each other (a box's corners alone are too far apart to link a leaf by points)
    lo3, hi3 = tris.min(axis=1), tris.max(axis=1)
    lo2, hi2 = lo3[:, [0, 2]] - DOOR_GAP_M / 2, hi3[:, [0, 2]] + DOOR_GAP_M / 2
    near = np.all((lo2[:, None, :] <= hi2[None, :, :]) & (lo2[None, :, :] <= hi2[:, None, :]), axis=2)
    parent = list(range(len(tris)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, j in zip(*np.nonzero(np.triu(near, 1))):
        ri, rj = root(int(i)), root(int(j))
        if ri != rj:
            parent[ri] = rj
    members: dict[int, list] = {}
    for i in range(len(tris)):
        members.setdefault(root(i), []).append(i)
    groups = [tris[m].reshape(-1, 3) for m in members.values()]
    out = []
    for P in groups:
        lo, hi = P.min(axis=0), P.max(axis=0)
        ext = hi - lo
        if ext[1] < 1.5 or max(ext[0], ext[2]) < 0.6:
            continue   # a sliver, a knob plate, a frame end: not a door
        axis = 0 if ext[0] < ext[2] else 2   # the plane's normal is the thin axis
        out.append({"lo": lo, "hi": hi, "axis": axis, "pts": P, "glass": gtris})
    return out


def transom(d, outward):
    """The transom light over a door: (foot, head, plane) in the frame, or None."""
    lo, hi, axis, G = d["lo"], d["hi"], d["axis"], d["glass"]
    if not len(G):
        return None
    lat = 2 - axis
    plane = d["pts"][:, axis]
    pmin, pmax = plane.min(), plane.max()
    tlo, thi = G.min(axis=1), G.max(axis=1)
    # a light in the door's plane, over its width, starting above a leaf's height and no higher
    # than just over the door's head (a draft's transom sits on the leaf; a K07's inside its frame)
    sel = ((tlo[:, lat] >= lo[lat] - 0.02) & (thi[:, lat] <= hi[lat] + 0.02)
           & (tlo[:, axis] >= pmin - PLANE_TOL_M) & (thi[:, axis] <= pmax + PLANE_TOL_M)
           & (tlo[:, 1] >= lo[1] + LEAF_SHARE * (hi[1] - lo[1]) - 0.02) & (tlo[:, 1] <= hi[1] + 0.3))
    if sel.sum() < 2:
        return None
    g = G[sel].reshape(-1, 3)
    foot, head = float(g[:, 1].min()), float(g[:, 1].max())
    if head - foot < TRANSOM_MIN_M:
        return None
    face = float(g[:, axis].max()) if outward > 0 else float(g[:, axis].min())
    return foot, head, face, float(g[:, lat].min()), float(g[:, lat].max())


def place(grid=None, sidecars=None):
    grid = grid or json.loads(GRID.read_text())
    lots = numbered_lots(grid)
    tracked = tracked_models()
    found, skipped = [], []
    by_lot: dict[str, list] = {}
    files = sidecars if sidecars is not None else [json.loads(f.read_text()) for f in sorted(SIDECARS.glob("*.json"))]
    for sc in files:
        sid = sc.get("id")
        pl = sc.get("placement") or {}
        if "asset" not in sc or pl.get("local_e") is None:
            continue
        fn = (sc.get("attributes") or {}).get("function")
        fn = fn.get("value") if isinstance(fn, dict) else fn
        if fn not in FUNCTIONS:
            continue   # a shed, a stable, a church: no house number over its door
        if sid in OWN_NUMBER:
            skipped.append({"structure": sid, "why": OWN_NUMBER[sid]})
            continue
        glb = ASSETS / sc["asset"]
        if f"assets/{sc['asset']}" not in tracked or not glb.exists():
            continue
        best = None
        for d in doors_of(read_glb(glb)):
            mid = (d["lo"] + d["hi"]) / 2
            c = to_enu(pl, mid[0], mid[2])
            lot = next((l for l in lots if inside(c, l["poly"])), None)
            if not lot:
                continue
            dist, foot = seg_dist(c, *lot["front"])
            if dist > FRONT_REACH_M:
                continue
            to_st = ((foot[0] - c[0]) / (dist or 1), (foot[1] - c[1]) / (dist or 1))
            ax = d["axis"]
            nrm = (1.0, 0.0) if ax == 0 else (0.0, 1.0)
            ne = dir_to_enu(pl, *nrm)
            cos = ne[0] * to_st[0] + ne[1] * to_st[1]
            if abs(cos) < FACE_COS:
                continue
            outward = 1 if cos > 0 else -1
            if not best or dist < best[0]:
                best = (dist, d, lot, outward, c)
        if not best:
            continue
        dist, d, lot, outward, c = best
        m = re.match(r"\s*(\d+)", pl.get("symbolic_location") or "")
        own = m.group(1) if m and m.group(1) in lot["numbers"] else None
        by_lot.setdefault(lot["id"], []).append((sid, d, outward, c, own))
    lot_of = {l["id"]: l for l in lots}
    for lid in sorted(by_lot):
        lot, doors = lot_of[lid], by_lot[lid]
        numbers = lot["numbers"]
        owns = [t[4] for t in doors]
        if all(owns) and len(set(owns)) == len(owns):
            # each house's own record names its number, and the sheet prints it on this lot
            pairs = [(t, t[4]) for t in doors]
        elif len(doors) == 1 and len(numbers) == 1:
            pairs = [(doors[0], numbers[0])]
        elif len(doors) == len(numbers):
            # the avenues number southward: the northmost door takes the lowest number
            doors = sorted(doors, key=lambda t: -t[3][1])
            pairs = list(zip(doors, sorted(numbers, key=int)))
        else:
            for sid, *_ in doors:
                skipped.append({"structure": sid, "lot": lid, "why": (
                    f"{len(doors)} front door(s) on a lot the sheet numbers {', '.join(numbers)}: which door "
                    "carried which number is not read, so none is shown")})
            continue
        for (sid, d, outward, c, _own), number in pairs:
            ax, lat = d["axis"], 2 - d["axis"]
            lo, hi = d["lo"], d["hi"]
            n = [0.0, 0.0, 0.0]
            n[ax] = float(outward)
            t = transom(d, outward)
            if t:
                foot, head, face, l0, l1 = t
                h = min(FIG_MAX_M, max(FIG_MIN_M, FIG_SHARE * HANDS[hand_of(sid)]["scale"] * (head - foot)))
                y = (foot + head) / 2
                mid_lat = (l0 + l1) / 2
                form = "transom"
            else:
                plane = d["pts"][:, ax]
                face = float(plane.max() if outward > 0 else plane.min())
                h = LEAF_FIG_M
                y = float(hi[1]) - LEAF_RAIL_DROP_M
                mid_lat = float((lo[lat] + hi[lat]) / 2)
                form = "leaf"
            p = [0.0, 0.0, 0.0]
            p[ax] = face + outward * PROUD_M
            p[lat] = mid_lat
            p[1] = y
            read = READ_FORM.get(sid)
            found.append({
                "structure": sid, "lot": lid, "street": lot["street"], "number": number,
                "at": [r3(v) for v in p], "normal": [r3(v) for v in n], "height_m": r3(h), "form": form,
                "hand": hand_of(sid),
                "grade": "attested" if read else "reconstructed",
                "number_grade": "inferred",
                "sources": sorted(set((read or {}).get("sources", []) + lot["sources"])),
                **({"note": read["note"]} if read else {}),
            })
    found.sort(key=lambda f: (f["street"], int(f["number"]), f["structure"]))
    skipped.sort(key=lambda s: s["structure"])
    return found, skipped


def build():
    found, skipped = place()
    forms = {}
    for f in found:
        forms[f["form"]] = forms.get(f["form"], 0) + 1
    return {
        "_doc": ("The 1904 district's house numbers (T-3737). GENERATED by tools/place_prairie_1904_house_numbers.py "
                 "from data/street_grid/1904.json's lot numbers and the 1904 models' front doors -- do not hand-edit; "
                 "re-run the tool. `at` and `normal` are in each structure's own frame (metres, as its GLB), so "
                 "renderers/web/js/house-numbers.js carries them through buildings.js's matrixOf."),
        "scene": "1904",
        "target_date": "1904-07-01",
        "ticket": TICKET,
        "generated_by": "tools/place_prairie_1904_house_numbers.py",
        "liberty": LIBERTY,
        "number_rule": ("The 1911 Sanborn's number for each avenue lot, carried to 1904 because the 1909 renumbering "
                        "left this district's avenue numbers alone (Glessner's 1887 address is 1800; Pullman's 1729 and "
                        "Coleman's 1811 are the 1880s sources'; an 1888 permit gives 2110). Cross-street lots take none."),
        "form_rule": ("Sign-written figures centred on the front door's transom light, as 1815's photograph shows them "
                      "and as 1612 was 'the house with the number 1612 over the portals' (Inter Ocean, 2 Jan 1887); "
                      "on the leaf's top rail where a door has no transom. Glessner's 1800 is in its door grille already."),
        "hand_rule": ("Each transom was lettered by a sign-writer, so the houses differ: gold leaf or white enamel, a "
                      "Roman, block or sloped letter, outlined or shaded dark, larger or smaller on the light. Each "
                      "house's hand is dealt by a stable hash of its id; 1815 keeps the gilt Roman of its photograph."),
        "hands": HANDS,
        "summary": {"numbers": len(found), "forms": forms,
                    "hands": {h: sum(1 for f in found if f["hand"] == h) for h in sorted(HANDS)}, "attested_form": sum(1 for f in found if f["grade"] == "attested"),
                    "skipped": len(skipped)},
        "numbers": found,
        "skipped": skipped,
    }


def check(doc) -> list[str]:
    faults = hand_faults(doc)
    seen = set()
    for f in doc["numbers"]:
        key = (f["street"], f["number"])
        if key in seen:
            faults.append(f"{f['number']} {f['street']} is shown twice")
        seen.add(key)
        if f["structure"] in OWN_NUMBER:
            faults.append(f"{f['structure']} draws its own number, and is given another")
        if not (FIG_MIN_M <= f["height_m"] <= FIG_MAX_M) and f["form"] == "transom":
            faults.append(f"{f['structure']}: transom figures {f['height_m']} m tall")
        if f["grade"] == "attested" and f["structure"] not in READ_FORM:
            faults.append(f"{f['structure']}: attested with no reading of its own")
        if abs(sum(v * v for v in f["normal"]) - 1) > 1e-6:
            faults.append(f"{f['structure']}: normal is not a unit")
        if f.get("hand") not in doc.get("hands", {}):
            faults.append(f"{f['structure']}: hand {f.get('hand')!r} is not one of the file's hands")
        elif f["structure"] in HAND_READ and f["hand"] != HAND_READ[f["structure"]]:
            faults.append(f"{f['structure']}: lettered {f['hand']}, but its photograph shows {HAND_READ[f['structure']]}")
        if not f["number"].isdigit():
            faults.append(f"{f['structure']}: number {f['number']!r} is not figures")
    return faults


def hand_faults(doc) -> list[str]:
    """Neighbours differ: no hand holds more than a third of the street, and no run of four doors shares one."""
    faults = []
    rows = doc["numbers"]
    for h in doc.get("hands", {}):
        n = sum(1 for f in rows if f.get("hand") == h)
        if n > len(rows) / 3:
            faults.append(f"hand {h} letters {n} of {len(rows)} houses: the street reads as one hand")
    for street in {f["street"] for f in rows}:
        run = [f["hand"] for f in rows if f["street"] == street]
        for i in range(len(run) - 3):
            if len(set(run[i:i + 4])) == 1:
                faults.append(f"{street}: four doors in a row lettered {run[i]}")
                break
    return faults


def self_test() -> int:
    doc = build()
    ok = True
    base = check(doc)
    if base:
        print("self-test: the built file already faults:", base)
        return 1
    import copy
    cases = []
    d = copy.deepcopy(doc); d["numbers"].append(dict(d["numbers"][0])); cases.append(("a number shown twice", d))
    d = copy.deepcopy(doc); d["numbers"][0]["structure"] = "glessner_house"; cases.append(("Glessner given a second 1800", d))
    d = copy.deepcopy(doc); t = next(x for x in d["numbers"] if x["form"] == "transom"); t["height_m"] = 0.4; cases.append(("figures a foot tall", d))
    d = copy.deepcopy(doc); t = next(x for x in d["numbers"] if x["structure"] not in READ_FORM); t["grade"] = "attested"; cases.append(("attested without a reading", d))
    d = copy.deepcopy(doc); d["numbers"][0]["number"] = "18O0"; cases.append(("a letter for a figure", d))
    d = copy.deepcopy(doc)
    for x in d["numbers"]:
        if x["structure"] not in HAND_READ:
            x["hand"] = "gilt_roman"
    cases.append(("every house in one hand", d))
    d = copy.deepcopy(doc); d["numbers"][0]["hand"] = "neon"; cases.append(("a hand the file does not define", d))
    d = copy.deepcopy(doc); t = next(x for x in d["numbers"] if x["structure"] in HAND_READ); t["hand"] = "white_block"; cases.append(("1815 lettered off its photograph", d))
    for name, case in cases:
        got = check(case)
        print(f"   self-test | {name}: {'refused' if got else 'FAIL (passed)'}")
        ok &= bool(got)
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    doc = build()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        faults = check(doc)
        if not OUT.exists() or OUT.read_text() != text:
            faults.append(f"{OUT.relative_to(ROOT)} is not what the tool writes: re-run it")
        for f in faults:
            print("house numbers:", f)
        print("house numbers:", "OK" if not faults else "FAIL", f"({doc['summary']})")
        return 1 if faults else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {doc['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
