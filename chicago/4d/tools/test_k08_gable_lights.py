#!/usr/bin/env python3
"""T-3634: a K08 projection's coped gable may carry lights cut in its face.

Chicagology's photograph of 2017 Prairie shows two small lights side by side in the south
projection's gable, on its foot either side of its middle. The bay kit cut no light in a
gable's face, so they were not built. This holds the kit and the record to them:

  * 2017's record names the two lights on its gable (`roof.gable.lights`), and they resolve
    and build: two K06 openings on the gable's run, over the wall top, their holes either
    side of the gable's middle, each on its own pane recess;
  * the gable's face is cut round each hole, so no face of the gable's wall stands across a
    light, and the face that is left covers the gable's outline less the holes exactly;
  * the kit refuses a light that runs into the copings, past a kneeler, onto another light
    or off the gable's run, an unknown key, and a gable light on a bay with no gable;
  * a gable with no lights is drawn as the one face it always was.

    python3 tools/test_k08_gable_lights.py
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402

SID = "house_2017_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def refused(v, needle, what):
    try:
        K8.Bay(v, K8.load(), "full").build(board=False)
    except ValueError as e:
        check(needle in str(e), f"{what} (refused: {e})")
        return
    check(False, f"{what} (it built)")


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]
bay = next(b for b in KP.from_phase(ph, st).bays if b["id"] == "south_gable")
v = bay["variant"]

# -- the record -----------------------------------------------------------------------------------
lights = v["roof"]["gable"].get("lights") or []
check(len(lights) == 1 and lights[0]["at"] == [0.4043, 0.5957],
      "2017's gable names its pair of lights, either side of the gable's middle")

# -- the build ------------------------------------------------------------------------------------
data = K8.load()
b = K8.Bay(v, data, "full").build(board=False)
gl = [w for w in b.windows if w.get("gable")]
y_top = b.meta["wall_top_m"]
check(len(gl) == 2 and all(w["storey"] == len(v["storeys"]) for w in gl),
      f"the gable's two lights are built, over its {len(v['storeys'])} storeys")
check(all(w["y_all"][0] >= y_top - 1e-6 for w in gl),
      f"each stands on the wall top {y_top:.3f} m or over it ({[w['y_all'] for w in gl]})")
check(all(w["panes"] for w in gl), "each light is glazed")
holes = sorted(b.gable_holes)
check(len(holes) == 2 and abs((holes[0][0] + holes[1][1]) / 2) < 0.01,
      f"their holes stand either side of the gable's middle ({[tuple(round(c, 3) for c in h[:4]) for h in holes]})")
check(all(abs((h[1] - h[0]) - 0.62) < 1e-6 and abs((h[3] - h[2]) - 1.12) < 1e-6 for h in holes),
      "each hole is the record's 0.62 by 1.12 m")

# the gable's wall faces: those in its plane, over the wall top
p = max(q[1] for q in v["plan"]["points"])
wall = b.prims["wall"]
tris = []
for t in range(0, len(wall.idx), 3):
    tri = [wall.pos[wall.idx[t + j]] for j in range(3)]
    if all(abs(q[2] - p) < 1e-6 and q[1] >= y_top - 1e-6 for q in tri):
        tris.append(tri)


def tri_area(tri):
    (ax, ay, _), (bx, by, _), (cx, cy, _) = tri
    return abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2


def inside(pt, h):
    return h[0] + 1e-6 < pt[0] < h[1] - 1e-6 and h[2] + 1e-6 < pt[1] < h[3] - 1e-6


over_hole = [t for t in tris for h in holes
             if inside(((t[0][0] + t[1][0] + t[2][0]) / 3, (t[0][1] + t[1][1] + t[2][1]) / 3), h)]
check(tris and not over_hole, f"no face of the gable's wall stands across a light ({len(tris)} triangles)")
rf = b.meta["roof"]
plain = copy.deepcopy(v)
del plain["roof"]["gable"]["lights"]
b0 = K8.Bay(plain, data, "full").build(board=False)
tris0 = []
w0 = b0.prims["wall"]
for t in range(0, len(w0.idx), 3):
    tri = [w0.pos[w0.idx[t + j]] for j in range(3)]
    if all(abs(q[2] - p) < 1e-6 and q[1] >= y_top - 1e-6 for q in tri):
        tris0.append(tri)
a_cut, a_whole = sum(map(tri_area, tris)), sum(map(tri_area, tris0))
a_holes = sum((h[1] - h[0]) * (h[3] - h[2]) for h in holes)
check(abs(a_whole - a_cut - a_holes) < 1e-6,
      f"the face left is the gable's outline less the holes exactly ({a_whole:.4f} - {a_holes:.4f} = {a_cut:.4f})")
check(not b0.gable_holes and not [w for w in b0.windows if w.get("gable")] and len(tris0) == 3,
      f"a gable with no lights is the one face it always was ({len(tris0)} triangles)")
check(b0.meta["roof"] == rf, "the lights move nothing of the gable's roof, copings or finial")

# the bay kit's own rules (closed, one pane layer, recesses, doubled faces) on 2017's bay
import check_bay_kit as CB  # noqa: E402
got = CB.check_variant(v, data)
check(not got, f"2017's bay keeps every bay-kit rule with its gable lights ({got})")

# -- the refusals ---------------------------------------------------------------------------------
def with_light(**kw):
    x = copy.deepcopy(v)
    x["roof"]["gable"]["lights"][0].update(kw)
    return x


refused(with_light(sill_m=0.9), "under the copings' beds", "a light run up into the copings")
refused(with_light(at=[0.25, 0.75]), "", "a light past a kneeler or off the gable's run")
refused(with_light(at=[0.48, 0.52]), "apart", "two lights run onto each other")
refused(with_light(sill_m=1.6), "sill_m", "a sill over 1.5 m")
refused(with_light(colour="red"), "not ['colour']", "an unknown key")
x = copy.deepcopy(v)
x["roof"]["gable"]["lights"] = []
b1 = K8.Bay(x, data, "full").build(board=False)
check(not b1.gable_holes, "an empty list is no lights")
x = copy.deepcopy(v)
x["roof"]["gable"]["lights"] = [x["roof"]["gable"]["lights"][0]] * 5
refused(x, "1-4", "five lights")

if failures:
    print(f"\nFAIL {len(failures)} check(s)")
    sys.exit(1)
print("\nOK: a coped gable's lights are cut in its face, and refused where they do not fit")
