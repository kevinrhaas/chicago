#!/usr/bin/env python3
"""T-3365 (T-1914): the moulded hoods of a K01 named-window front's lights, as 2009 Prairie's
photograph shows them (`street_front_windows.hoods`, built as `k01.wall.window_hood`):

  * a drip `band` over the paired light, its ends turned down as label stops, and a carved
    `pendant` standing up off its crown into the gable — both proud of the shaped gable's
    slab where they rise past its foot, so the slab does not swallow them;
  * two `consoles` under the oriel either side of the ground window;
  * a splayed `key` block over the small light, which takes the surround's lintel course off.

Held on the committed record; each refused out of its range.

    python3 tools/test_k01_window_hoods.py
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

SID = "mayer_house_2009_prairie"
failures = []


def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok:
        failures.append(what)


record = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
p = KP.from_phase(record["phases"][0], record)
hoods = {h["window"]: h for h in p.street_dress["hoods"]}
check(sorted(hoods) == [0, 1, 2], f"three hooded lights ({sorted(hoods)})")
check(set(hoods[0]) >= {"consoles"} and "band" not in hoods[0], "the ground window on two consoles")
check("key" in hoods[1], "the small light under a splayed key")
check({"band", "pendant"} <= set(hoods[2]), "the paired light under a drip band and its pendant")
b = hoods[2]["band"]
check(abs(b["bed_m"] - hoods[2]["head_m"]) < 1e-6 and b["top_m"] - b["stops"]["drop_m"] < b["bed_m"],
      "the band on the head, its stops hanging past it")
check(p.shaped_gable.get("takes_gutter") is True, "no street gutter across the gable's foot")

# the key stands for the small light's lintel: no surround lintel cell over it, the others kept
small = next(o for o in p.openings if abs(o.s_m - 6.32) < 1e-6)
paired = next(o for o in p.openings if abs(o.s_m - 4.02) < 1e-6)
a = K1.build(p, SID)
cells = [c for ci in range(4) for c in a.dress_cells(p.openings, 0.0, 99.0, ci, "brick", p.width_m)]
check(not any(abs(c[2] - small.head_m) < 1e-6 and c[0] < small.s_m < c[1] for c in cells),
      "the small light's surround lintel is off")
check(any(abs(c[2] - paired.head_m) < 1e-6 and c[0] < paired.s_m < c[1] for c in cells),
      "the paired light's surround lintel is kept")

inst = a.components["k01.wall.window_hood"]["instances"]
check(len(inst) == 3 and inst[2]["params"]["parts"] == ["band", "pendant"]
      and inst[2]["params"]["pendant_tiers"] == 4, "three hood instances, the paired light's in four tiers")
# the band and the pendant stand proud of the gable's slab (eave overhang + its proud)
slab = p.eave_overhang_m + p.shaped_gable["proud_m"]
seats = [f for fs in a.footprints.values() for f in fs if f[4] == "k01.window_hood"]
check(len(seats) == 3, f"each hood seated on the front ({len(seats)})")
# the street front faces +u: the band, one stone from its bed to its top, stands past the slab's
# face (its vertices on its bed line, which nothing else of the hood's shares)
band_u = [q[0] for q in a.prims["limestone_trim"].pos if abs(q[1] - b["bed_m"]) < 1e-6
          and -b["s_m"][1] - 1e-6 < q[2] < -b["s_m"][0] + 1e-6]
check(band_u and abs(max(band_u) - (p.depth_m + slab + b["proud_m"])) < 1e-6,
      f"the band stands {b['proud_m']} m proud of the gable's slab, not inside it")


def refused(mutate, what):
    r = copy.deepcopy(record)
    mutate(r["phases"][0]["form"])
    try:
        KP.from_phase(r["phases"][0], r)
    except KP.ParamError:
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what} (it resolved)")


def hd(f, k):
    return f["street_front_windows"]["value"]["hoods"][k]


refused(lambda f: hd(f, 0).update(window=9), "a hood on a window the front does not name")
refused(lambda f: hd(f, 0).update(window=2), "one light hooded twice")
refused(lambda f: hd(f, 0).update(cornice={}), "an unknown hood part")
refused(lambda f: hd(f, 0)["consoles"].update(at_m=[2.2, 4.31]), "a console inside the light's jamb")
refused(lambda f: hd(f, 0)["consoles"].update(width_m=[0.3, 0.2]), "a console narrowing upward")
refused(lambda f: hd(f, 1)["key"].update(width_m=[0.2, 0.5]), "a key narrower than its light")
refused(lambda f: hd(f, 1)["key"].update(from_m=8.0), "a key off its light's head")
refused(lambda f: hd(f, 2)["band"].update(s_m=[3.0, 5.57]), "a band short of the light's jamb")
refused(lambda f: hd(f, 2)["band"]["stops"].update(drop_m=0.2), "stops that do not hang past the mould")
refused(lambda f: hd(f, 2)["band"].update(proud_m=0.5), "a band 0.5 m proud")
refused(lambda f: hd(f, 2)["pendant"].update(from_m=12.0), "a pendant off its band's top")
refused(lambda f: hd(f, 2)["pendant"].update(tiers=[[12.5, 12.6, 0.48], [12.18, 12.32, 0.62]]),
        "pendant tiers out of order")
refused(lambda f: hd(f, 2)["pendant"].update(stem_m=0.7), "a pendant stem wider than its tiers")

if failures:
    print(f"FAIL  {len(failures)} check(s)")
    sys.exit(1)
print("PASS  window hoods, consoles, key and pendant")
