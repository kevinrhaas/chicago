#!/usr/bin/env python3
"""T-3730: a light in a K01 gable roof's end parapet, held on 2130 Prairie's record.

  * `gable_roof.ends.<side>.lights` stands each light in the parapet: the roof's one solid is
    cut to K06's reveal behind the parapet's face, K06 sets its sash in the recess and K01 its
    flat lintel, all on the gable's own wall component (`k01.wall.gable_end.<side>`);
  * a light that does not stand wholly in the parapet is refused: a sill under the soffit the
    parapet rises from, a lintel past the gable's top line, one at a corner, two lights with
    no pier between their lintels, or any spec the kit does not take.

    python3 tools/test_k01_gable_lights.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "murdoch_house_2130_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


def refused(change, why, says):
    st, phase = record()
    change(phase["form"]["gable_roof"]["value"]["ends"]["south"]["lights"])
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"refused: {why} ({e})")
        return
    check(False, f"refused: {why} (accepted)")


st, phase = record()
p = KP.from_phase(phase, st)
lights = p.gable["ends"]["south"]["lights"]
check(len(lights) == 1 and abs(lights[0]["u_m"] - (p.depth_m - 2.5)) < 1e-6,
      f"the south gable's one light resolves 2.5 m behind the front (u {lights[0]['u_m']})")
check("lights" not in p.gable["ends"]["north"], "the north gable names none")

a = K1.build(p, SID)
walls = a.components.get("k01.wall.gable_end.south", {}).get("instances", [])
check(len(walls) == 1 and walls[0]["params"]["openings"] == 1, "the south gable's face is one wall with one opening")
check("construction" not in (walls[0]["params"] if walls else {}),
      "the gable's face registers no construction of its own (the parapet's fabric is the roof's)")
sashes = [i for i in a.components["k01.opening.sash_flat"]["instances"]
          if i["params"]["wall"] == "k01.wall.gable_end.south"]
lt = lights[0]
ok = len(sashes) == 1 and all(abs(x - y) < 1e-3 for x, y in zip(sashes[0]["sockets"]["sill"], (lt["u_m"], 9.35, 0.0)))
check(ok, f"its K06 sash stands at its sill on the south wall's face ({sashes[0]['sockets']['sill'] if sashes else None})")
pts, tris = a.roof_shell
u0, u1 = lt["u_m"] - lt["width_m"] / 2, lt["u_m"] + lt["width_m"] / 2
reveal = [t for t in tris if t[3] == "reveal"
          and all(u0 - 1e-4 <= pts[i][0] <= u1 + 1e-4 and lt["sill_m"] - 1e-4 <= pts[i][1] <= lt["sill_m"] + lt["height_m"] + 1e-4
                  and -0.3 <= pts[i][2] <= 1e-4 for i in t[:3])]
check(len(reveal) >= 8, f"the roof's solid is cut for it: {len(reveal)} reveal faces in the light's hole")

refused(lambda ls: ls[0].update(sill_m=8.0), "a sill under the soffit the parapet stands on", "stands under the parapet")
refused(lambda ls: ls[0].update(sill_m=10.6), "a lintel past the gable's top line", "top line")
refused(lambda ls: ls[0].update(back_m=0.4), "a light at the front corner", "corners")
refused(lambda ls: ls.append(dict(ls[0], back_m=3.3)), "two lights with no pier between their lintels", "leaves no")
refused(lambda ls: ls[0].update(head="round"), "a key the kit does not take", "takes")
refused(lambda ls: ls[0].update(clear_width_m=2.0), "a light wider than 1.5 m", "0.4-1.5 m wide")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall ok")
