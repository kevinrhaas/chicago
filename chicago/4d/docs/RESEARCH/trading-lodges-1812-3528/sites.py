#!/usr/bin/env python3
"""The search that chose T-3528's ground, the Potawatomi lodges by the river (run from chicago/4d).

    python3 docs/RESEARCH/trading-lodges-1812-3528/sites.py

A 26 x 18 m ground qualifies when, on the committed e1830_natural heightfield, every 2 m sample
of it stands at or above 0.6 m with a spread of at most 0.2 m, every point 6 m outside it also
stands at or above 0.6 m (off the cut of the river and the creek), and it keeps 10 m from the
camp grounds, 15 m from every other 1812 footprint, 6 m from every worn trail (the August camp
paths too) and 4 m from the 1835 inferred households' footprints and reserved slots. Candidates
are listed nearest first to the centre of the gathering's mouth group; the record takes
(698, -34). The record itself is left out of the obstacles so the search reproduces after it
exists. The printed `pass` line is where camp paths were once skipped; they are kept.
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, "tools")
from heightfield import Heightfield
import check_structure_clearance as csc
import generate_inferred_households as gih
ORIGIN = (447072.7, 4637395.8)
hf = Heightfield.load(Path("data/terrain/epochs/e1830_natural"))
boxes = [(b["id"], b["box"]) for b in csc.buildings("1812") if b["id"] != "potawatomi_trading_lodges_1812"]
trails = json.load(open("data/enclosures/1812/worn_trails_1812.json"))["ground"]["trails"]
tpts = []
for t in trails:
    pass
    ln = t["line_local_enu_m"]
    for a, b in zip(ln, ln[1:]):
        k = max(1, int(math.hypot(b[0]-a[0], b[1]-a[1]) / 1.5))
        tpts += [(a[0]+(b[0]-a[0])*i/k, a[1]+(b[1]-a[1])*i/k) for i in range(k+1)]
inf = []
for p in sorted(Path("data/structures").glob("inf_*.json")):
    d = json.load(open(p))
    for ph in d.get("phases", []):
        pos = ph.get("position") or {}; poly = (ph.get("footprint") or {}).get("polygon")
        if pos.get("utm_e") is not None and poly: inf.append(gih.world_polygon(pos, poly, ORIGIN))
inf += [P for _, P in gih.reserved_slots()]
INF = [(min(x for x,_ in P), min(y for _,y in P), max(x for x,_ in P), max(y for _,y in P)) for P in inf]
def apart(e0,n0,L,D,box,g):
    x0,y0,x1,y1 = box
    return e0+L+g < x0 or x1+g < e0 or n0+D+g < y0 or y1+g < n0
def ok(e0,n0,L,D,ms):
    hs=[hf.height(e0+u,n0+v) for u in range(0,L+1,2) for v in range(0,D+1,2)]
    if min(hs)<0.6 or max(hs)-min(hs)>ms: return None
    ring=[hf.height(e0+u,n0+v) for u in range(-6,L+7,2) for v in (-6,D+6)]+[hf.height(e0+u,n0+v) for v in range(-6,D+7,2) for u in (-6,L+6)]
    if min(ring)<0.6: return None
    if not all(apart(e0,n0,L,D,b,4) for b in INF): return None
    for i,b in boxes:
        if not apart(e0,n0,L,D,b,10 if i.startswith(("potawatomi_camp","miami")) else 15): return None
    if any(e0-6<=x<=e0+L+6 and n0-6<=y<=n0+D+6 for x,y in tpts): return None
    return max(hs)-min(hs)
mouth=[b for i,b in boxes if i=="potawatomi_camp_1812_mouth"][0]
print("mouth box", mouth)
L,D=26,18
mx,my=(mouth[0]+mouth[2])/2,(mouth[1]+mouth[3])/2
c=[]
for e0 in range(600,1000,2):
    for n0 in range(-160,120,2):
        s=ok(e0,n0,L,D,0.2)
        if s is not None: c.append((math.hypot(e0+L/2-mx,n0+D/2-my),e0,n0,round(s,2)))
c.sort(); print(c[:15])
