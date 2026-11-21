#!/usr/bin/env python3
"""T-3634: a dressed dormer pediment may carry a carved lunette in its tympanum.

Chicagology's photograph of 2017 Prairie shows its two mansard dormers as classical
pediments: pilasters either side of the lights, a frieze, a level cornice and, standing on
it in each tympanum, a carved lunette (a moulded ring round a fan). The kit's dressed
pediment (T-3307) built no lunette and laid its dress in painted timber only, so 2017's
dormers were plain stone gables. This holds the kit and the record to them:

  * 2017's record dresses both dormers and names a lunette on each, and both resolve, each
    standing at least 0.03 m clear of the raking cornice's inner line;
  * the lunette builds as a half disc on the cornice's top: every point within its radius,
    none under the cornice's top, none further out of the tympanum than its `proud_m`, the
    ring the furthest out and the cut between two leaves the least;
  * the kit refuses a lunette that reaches the raking cornice, an unknown or missing key,
    and numbers out of their bounds;
  * a dormer the record faces in the front's stone lays its dress in that stone's slot.

    python3 tools/test_k10_dormer_lunette.py
"""

from __future__ import annotations

import copy
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k10_frontage as K10  # noqa: E402

SID = "house_2017_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
ph = st["phases"][0]
p = KP.from_phase(ph, st)

# -- the record -----------------------------------------------------------------------------------
ds = p.mansard["dormers"]
check(len(ds) == 2 and all(d.get("dress", {}).get("lunette") for d in ds),
      "2017's two dormers are dressed pediments, each with a lunette")
for d in ds:
    ln = d["dress"]["lunette"]
    room = KP.lunette_clearance(d)
    check(ln["radius_m"] <= room - 0.03,
          f"its {ln['radius_m']} m lunette stands clear of the raking cornice ({room:.3f} m of tympanum)")
check(p.mansard.get("dormer_fabric") == "front_stone", "2017's dormers are faced in the front's stone")
check(K10.ROLE_MATERIAL.get("dormer") == "dormer_stone",
      "a stone dormer's dress is laid in the dormer's own stone slot")

# -- the geometry ---------------------------------------------------------------------------------
K = K10._kit()


def build(ln, hs=10.0, room=1.0):
    var = K.Variant({"id": "k10.dormer.lower_face_pediment", "kind": "dormer", "material": "timber"}, K.load())
    var.seed, var.rng = 1, random.Random(1)
    K10._lunette(var, K, ln, hs, room)
    return var.pieces


for d in ds:
    ln = d["dress"]["lunette"]
    pieces = build(ln)
    pts = [q for pc in pieces for q in pc.mesh.pos]
    names = {pc.name for pc in pieces}
    check(names == {"lunette ring", "lunette leaf", "lunette boss"}, f"a ring, leaves and a boss ({sorted(names)})")
    check(sum(pc.name == "lunette leaf" for pc in pieces) == ln["flutes"], f"{ln['flutes']} leaves in the fan")
    check(all(math.hypot(x, y - 10.0 - K10.LUNETTE_SEAT_M) <= ln["radius_m"] + 1e-6 for x, y, _ in pts), "every point within its radius")
    check(min(y for _, y, _ in pts) >= 10.0, "it stands on the cornice's top, none under it")
    check(all(-1e-9 <= z <= ln["proud_m"] + 1e-9 for _, _, z in pts), "none further out than its proud_m")
    front = lambda name: max(z for pc in pieces if pc.name == name for _, _, z in pc.mesh.pos)
    leaves = sorted({round(max(z for _, _, z in pc.mesh.pos), 6) for pc in pieces if pc.name == "lunette leaf"})
    check(front("lunette ring") == max(z for _, _, z in pts) and len(leaves) == 2 and leaves[0] < leaves[1],
          f"the ring stands furthest out, the leaves at two depths ({leaves})")

try:
    build(ds[0]["dress"]["lunette"], room=0.4)
    check(False, "a lunette reaching the raking cornice is refused (it built)")
except ValueError as e:
    check("raking cornice" in str(e), f"a lunette reaching the raking cornice is refused ({e})")

# -- what the kit refuses -------------------------------------------------------------------------


def refused(mut, needle, what):
    s = copy.deepcopy(st)
    mut(s["phases"][0]["form"]["mansard"]["value"]["dormers"][0])
    try:
        KP.from_phase(s["phases"][0], s)
    except KP.ParamError as e:
        check(needle in str(e), f"{what} (refused: {e})")
        return
    check(False, f"{what} (it resolved)")


def setl(**kw):
    return lambda d: d["dress"]["lunette"].update(kw)


refused(setl(radius_m=0.72), "tympanum", "a lunette wider than the tympanum")
refused(setl(flutes=3), "5-15", "a fan of three leaves")
refused(setl(proud_m=0.2), "0.02-0.1", "a lunette 0.2 m proud")
refused(setl(ring_m=0.2), "ring", "a ring over a third of the radius")
refused(lambda d: d["dress"]["lunette"].update(depth_m=0.1), "lunette takes", "an unknown key")
refused(lambda d: d["dress"]["lunette"].pop("flutes"), "lunette takes", "a missing key")
refused(lambda d: d["dress"].update(scroll=1), "may name consoles and a lunette", "an unknown dress part")

if failures:
    print(f"\n{len(failures)} check(s) FAILED")
    sys.exit(1)
print("\nall checks passed")
