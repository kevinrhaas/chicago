#!/usr/bin/env python3
"""T-3626 (T-1916): the stone frame of a K01 named-window front, as the Inland Architect's
1895 plate draws 2013 Prairie's (`street_front_windows.frame`, built as `k01.wall.front_frame`):

  * pilasters up both sides of the three-light storeys and in the piers between their lights;
  * a raised border round a sunk panel under each third-storey light;
  * one corniced hood across the frame, its corona further out than its frieze;
  * two oval lights, each a moulded ring round a dark field, standing proud of the brick.

Held on the committed record; every part refused out of its range, over a light or in another.

    python3 tools/test_k01_front_frame.py
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

SID = "reid_house_2013_prairie"
failures = []


def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


record = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(record["phases"][0], record)
fr = p.street_dress["frame"]
# T-3626: four frame pilasters under the hood, and the border up the front's south edge
check(len(fr["pilasters"]) == 5, f"five strips: four pilasters and the south edge's border ({len(fr['pilasters'])})")
check(len(fr["panels"]) == 3, f"a panel under each third-storey light ({len(fr['panels'])})")
check(len(fr["hoods"]) == 1 and fr["hoods"][0]["corona"]["proud_m"] > fr["hoods"][0]["proud_m"],
      "one hood, its corona further out than its frieze")
check(sorted(o["s_m"] for o in fr["ovals"]) == [0.83, 6.54], "the two ovals at 0.83 and 6.54 m")
hood = fr["hoods"][0]
under_hood = [q for q in fr["pilasters"] if q["s_m"][1] <= hood["s_m"][1] + 1e-6]
check(len(under_hood) == 4 and all(abs(q["to_m"] - hood["bed_m"]) < 1e-6 for q in under_hood),
      "the pilasters carry the hood")
border = [q for q in fr["pilasters"] if q not in under_hood]
check(len(border) == 1 and abs(border[0]["s_m"][1] - p.width_m) < 1e-6 and border[0]["to_m"] > hood["top_m"],
      "the south edge's border runs up the corner past the hood")
front = [o for o in p.openings if o.wall == "k01.wall.street_front"]
lun = [o for o in front if o.component == "k01.opening.street_sash_round"]
check(len(lun) == 1 and lun[0].sill_m > hood["top_m"], "the round-headed lunette stands over the hood")
under = [o for o in front if o.sill_m < hood["bed_m"] < o.head_m + 0.5 and o.sill_m > 9.0]
check(under and all(o.head_m <= hood["bed_m"] + 1e-6 for o in under), "every third-storey light under the hood")

a = K1.build(p, SID)
inst = a.components["k01.wall.front_frame"]["instances"]
check(len(inst) == 1 and inst[0]["params"] == {"pilasters": 5, "panels": 3, "hoods": 1, "ovals": 2},
      "one frame instance counting its parts")
seats = [f for fs in a.footprints.values() for f in fs if f[4] == "k01.front_frame"]
check(len(seats) == 1, f"the frame seated on the front ({len(seats)})")
# the street front faces +u at the front block's depth: every frame vertex at or proud of it
lim = [q for q in a.prims["limestone_trim"].pos if 5.9 < q[1] < 11.85 and q[0] > p.depth_m - 1e-6]
check(lim and max(q[0] for q in lim) <= p.depth_m + hood["corona"]["proud_m"] + 1e-6,
      "nothing of the frame stands further out than the hood's corona")
dark = [q for q in a.prims["backing"].pos if 6.6 < q[1] < 8.0 and q[0] > p.depth_m - 1e-6]
check(dark and min(q[0] for q in dark) > p.depth_m, "the ovals' dark fields stand in front of the brick, not in it")


def refused(mutate, what):
    r = copy.deepcopy(record)
    mutate(r["phases"][0]["form"]["street_front_windows"]["value"]["frame"])
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it resolved)")


refused(lambda f: f.update(cornice=[]), "an unknown key")
refused(lambda f: f["pilasters"][0].update(s_m=[2.0, 2.3]), "a pilaster over a light")
refused(lambda f: f["pilasters"][0].update(proud_m=0.3), "a pilaster 0.3 m proud")
refused(lambda f: f["panels"][0].update(border_m=0.2), "a panel's border wider than a third of its field")
refused(lambda f: f["hoods"][0]["corona"].update(proud_m=0.05), "a corona behind its frieze")
refused(lambda f: f["hoods"][0].update(bed_m=11.2), "a hood over the narrow lights' heads")
refused(lambda f: f["ovals"][0].update(s_m=2.36), "an oval on a light")
refused(lambda f: f["ovals"][0].update(ring_m=0.3), "an oval's ring wider than a quarter of it")
refused(lambda f: f["panels"].append({"s_m": [2.0, 2.6], "bed_m": 8.4, "top_m": 9.5, "border_m": 0.05,
                                      "proud_m": 0.03}), "a panel lying on a pilaster")

print()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("all passed")
