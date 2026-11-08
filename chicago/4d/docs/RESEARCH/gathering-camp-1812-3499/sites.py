#!/usr/bin/env python3
"""The search that chose T-3499's camp grounds (run from chicago/4d).

    python3 docs/RESEARCH/gathering-camp-1812-3499/sites.py

A ground qualifies when, on the committed e1830_natural heightfield, every 2 m sample of its
rectangle stands at or above 0.6 m with a spread of at most 0.14 m (0.3 m for the Miami
camp), every point 6 m outside it also stands at or above 0.6 m (so it is off the creek's
cut), and it keeps 10 m from the other camp grounds, 15 m from every other 1812 footprint,
6 m from every 1812 worn trail and 4 m from the 1835 inferred households' footprints and
reserved slots (tools/generate_inferred_households.py holds every record of any date 3 m
from those). The Miami camp also keeps 4 m from the T-3497 wagon roads. Grounds are picked
greedily, nearest first to the six T-3342 grounds' centre (the fort for the Miamis), with
no two picks closer than 10 m. T-3499's own records are left out of the obstacles so the
search reproduces after they exist.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "tools")
from heightfield import Heightfield  # noqa: E402
import check_structure_clearance as csc  # noqa: E402
import generate_inferred_households as gih  # noqa: E402

OWN = {"potawatomi_camp_1812_" + s for s in
       "south_west north_flat south_bend head_west prairie_west far_west south_prairie".split()}
OWN.add("miami_escort_camp_1812")
ORIGIN = (447072.7, 4637395.8)

hf = Heightfield.load(Path("data/terrain/epochs/e1830_natural"))
boxes = [(b["id"], b["box"]) for b in csc.buildings("1812") if b["id"] not in OWN]
trails = json.load(open("data/enclosures/1812/worn_trails_1812.json"))["ground"]["trails"]
tpts = []
for t in trails:
    ln = t["line_local_enu_m"]
    for a, b in zip(ln, ln[1:]):
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 1.5))
        tpts += [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(k + 1)]
inf = []
for p in sorted(Path("data/structures").glob("inf_*.json")):
    d = json.load(open(p))
    for ph in d.get("phases", []):
        pos = ph.get("position") or {}
        poly = (ph.get("footprint") or {}).get("polygon")
        if pos.get("utm_e") is not None and poly:
            inf.append(gih.world_polygon(pos, poly, ORIGIN))
inf += [P for _, P in gih.reserved_slots()]
INF_BOX = [(min(x for x, _ in P), min(y for _, y in P), max(x for x, _ in P), max(y for _, y in P))
           for P in inf]
ROADS = [(1078, 85, 1198, 147), (1095, -455, 1225, 60)]   # T-3497's two driven roads


def apart(e0, n0, L, D, box, g):
    x0, y0, x1, y1 = box
    return e0 + L + g < x0 or x1 + g < e0 or n0 + D + g < y0 or y1 + g < n0


def ok(e0, n0, L, D, max_spread, roads=False):
    hs = [hf.height(e0 + u, n0 + v) for u in range(0, L + 1, 2) for v in range(0, D + 1, 2)]
    if min(hs) < 0.6 or max(hs) - min(hs) > max_spread:
        return False
    ring = [hf.height(e0 + u, n0 + v) for u in range(-6, L + 7, 2) for v in (-6, D + 6)] + \
           [hf.height(e0 + u, n0 + v) for v in range(-6, D + 7, 2) for u in (-6, L + 6)]
    if min(ring) < 0.6:
        return False
    if not all(apart(e0, n0, L, D, b, 4) for b in INF_BOX):
        return False
    if roads and not all(apart(e0, n0, L, D, b, 4) for b in ROADS):
        return False
    for i, b in boxes:
        if not apart(e0, n0, L, D, b, 10 if i.startswith("potawatomi_camp") else 15):
            return False
    return not any(e0 - 6 <= x <= e0 + L + 6 and n0 - 6 <= y <= n0 + D + 6 for x, y in tpts)


def pick(cands, n, L, D):
    got = []
    for d, e0, n0 in sorted(cands):
        if all(not (e0 < e + L + 10 and e < e0 + L + 10 and n0 < m + D + 10 and m < n0 + D + 10)
               for _, e, m in got):
            got.append((d, e0, n0))
        if len(got) >= n:
            break
    return got


camp = [b for i, b in boxes if i.startswith("potawatomi_camp")]
cx = sum((b[0] + b[2]) / 2 for b in camp) / len(camp)
cy = sum((b[1] + b[3]) / 2 for b in camp) / len(camp)
cands = [(math.hypot(e0 + 18 - cx, n0 + 14 - cy), e0, n0)
         for e0 in range(480, 820, 4) for n0 in range(-380, 0, 4) if ok(e0, n0, 36, 28, 0.14)]
print("Potawatomi grounds (SW corner E, N), nearest first:")
for d, e0, n0 in pick(cands, 7, 36, 28):
    print(f"  {e0:5d} {n0:5d}   {d:6.1f} m from the camp's centre")

fort = [b for i, b in boxes if i == "first_fort_dearborn_pickets_outer"][0]
fx, fy = (fort[0] + fort[2]) / 2, (fort[1] + fort[3]) / 2
m = [(math.hypot(e0 + 15 - fx, n0 + 12 - fy), e0, n0)
     for e0 in range(860, 1140, 4) for n0 in range(-160, 330, 4) if ok(e0, n0, 30, 24, 0.3, True)]
print("Miami camp:", pick(m, 1, 30, 24))
