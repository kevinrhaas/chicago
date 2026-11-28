#!/usr/bin/env python3
"""T-3634: 2021 Prairie's open street front and its picket fence, held on its record.

  * an open front (`boundary.layout: open`) may name `side_pickets`: a low timber picket
    fence of pointed pickets on two rails between square posts, along a SIDE lot line from
    `u_m[0]` to `u_m[1]` (2021's photograph: white pickets before the south wing, the
    street front itself open);
  * it is built on the record's line, posts no more than 2.4 m apart, every picket in the
    fence's own painted slot, and nothing of it stands before the street front;
  * a run off the lot line, within 0.3 m of the house or a rear wing, too short, out to
    the public walk, too tall, or naming a key the kit does not take is refused.

    python3 tools/test_k11_side_pickets.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k11_frontage as F  # noqa: E402

SID = "high_house_2021_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
phase = st["phases"][-1]
B = phase["form"]["boundary"]["value"]
check(B.get("layout") == "open" and "fence" not in B and "entrance_gate" not in B,
      "2021's street front is open: no fence or gate across it")
sp = B.get("side_pickets") or {}
check(sp == {"s_m": 14.85, "u_m": [-5.2, 11.3], "height_m": 0.9},
      f"its pickets run on the south lot line, s 14.85, X -5.2..11.3, 0.9 m high ({sp})")

p = KP.from_phase(phase, st)
a = K.build(p, SID)
pr = a.prims.get("fence_pickets")
check(pr is not None, "the pickets have their own painted slot")
pr = pr or a.prim("fence_pickets")
xs = [q[0] for q in pr.pos]
zs = [q[2] for q in pr.pos]
ys = [q[1] for q in pr.pos]
check(len(pr.idx) > 0, f"the pickets are laid in their own painted slot ({len(pr.idx) // 3} triangles)")
if pr.pos:
    check(abs(min(zs) - -14.85) < 1e-6, f"their outer face is on the lot line, Z -14.85 ({min(zs):.4f})")
    check(max(zs) - min(zs) < 0.25, f"the run is one line, under 0.25 m through ({max(zs) - min(zs):.3f})")
    check(abs(min(xs) - -5.2) < 1e-6 and abs(max(xs) - 11.3) < 1e-6,
          f"from X -5.2 to 11.3 ({min(xs):.3f}..{max(xs):.3f})")
    check(abs(max(ys) - 0.9) < 1e-6, f"their points stand 0.9 m over grade ({max(ys):.3f})")
posts = a.boundary.get("side_pickets_x_m") or []
gaps = [b - c for c, b in zip(posts, posts[1:])]
check(len(posts) >= 2 and max(gaps) <= 2.4 + 1e-6, f"{len(posts)} posts, none more than 2.4 m apart")
check("fence_boards" not in a.prims, "no boarded fence is laid")
check(a.boundary.get("openings_s_m") == [[-0.49, 14.89]], "the whole street front is the opening")


def refused(change, why, says):
    t = copy.deepcopy(B)
    change(t)
    try:
        F.open_spec(p, t)
    except ValueError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


refused(lambda t: t["side_pickets"].update(s_m=14.0), "a run off the lot line", "side lot line")
refused(lambda t: t["side_pickets"].update(s_m=-0.28), "a run against the house's north wall", "within 0.3 m")
refused(lambda t: (t.update(lot_s_m=[-0.49, 13.6]), t["side_pickets"].update(s_m=13.6)),
        "a run within 0.3 m of the south wing", "within 0.3 m")
refused(lambda t: t["side_pickets"].update(u_m=[10.8, 11.3]), "a run under a metre long", "at least 1.0 m")
refused(lambda t: t["side_pickets"].update(u_m=[-5.2, 14.8]), "a run out to the public walk", "public walk")
refused(lambda t: t["side_pickets"].update(height_m=1.5), "a picket fence 1.5 m high", "0.6-1.2 m")
refused(lambda t: t["side_pickets"].update(gate=True), "a key the kit does not take", "takes")
refused(lambda t: t.update(fence="k11.fence.side_boards"), "an open front that names a fence", "lays nothing")

if failures:
    print(f"\nFAIL: {len(failures)} check(s)")
    sys.exit(1)
print("\nPASS")
