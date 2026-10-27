#!/usr/bin/env python3
"""T-1890: an oriel may be ROUND, and may stand on a rear wing's wall.

1801 Prairie's gabled section on 18th Street, read off the Taylor print and HABS photograph 2,
carries a round oriel on a deep stepped corbel over its principal storey, a balustrade round its
top. The kit's oriel was canted only, and a rear wing's wall carried a tower or a full-height
projection only. This holds the kit and the record to what the ticket says:

  * an oriel's plan may be a bow, `chord_m` 1.0-4.0 m and `rise_m` 0.2 m to half its chord (at
    most 1.2 m), and a bow's keys beside a canted plan's are refused;
  * a round oriel's corbel courses reach back from the bow's crown, so the lowest still bears on
    the wall, and they step down under its floor as a canted oriel's do;
  * an oriel may stand on a rear wing's wall, on one of that wing's floors; a bay may not;
  * 1801's gable_oriel builds from its record on the r3 range's 5.0 m floor, its balcony round
    its top, and p_gable's principal storey carries the three round-arched lights.

    python3 tools/test_k08_round_oriel.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


def entry(phase, bid):
    return next(b for b in phase["form"]["bays"]["value"] if b["id"] == bid)


def resolved(bid, st=None, phase=None):
    if st is None:
        st, phase = record()
    p = KP.from_phase(phase, st)
    return next(b for b in p.bays if b["id"] == bid)


def built(v, tier="full"):
    return K8.Bay(copy.deepcopy(v), K8.load(), tier).build(board=False)


def record_checks():
    b = resolved("gable_oriel")
    v = b["variant"]
    check(b.get("wing") == "r3" and v["kind"] == "oriel" and v["plan"] == {"kind": "bow", "chord_m": 2.7, "rise_m": 0.6},
          f"gable_oriel is a round oriel on the r3 range ({b.get('wing')}, {v['plan']})")
    check(abs(v["base"] - 5.0) < 1e-9, f"it stands on the range's 5.0 m floor ({v['base']})")
    bay = built(v)
    m = bay.meta
    cb = m["corbel"]
    check(cb["courses"] == 6 and abs(cb["reach_m"] - 0.6) < 1e-3 and cb["bearing_m"] >= 0.08 - 1e-9,
          f"its six corbel courses reach back from the bow's 0.6 m crown and still bear on the wall ({cb})")
    check(abs(cb["bottom_m"] - 3.8) < 1e-6, f"the corbel's foot at 3.8 m ({cb['bottom_m']})")
    check(abs(m["wall_top_m"] - 9.2) < 1e-6, f"its wall top at 9.2 m ({m['wall_top_m']})")
    check(bool(bay.prims.get("corbel") and bay.prims["corbel"].pos), "the corbel is built")
    check("balcony" in v and v["balcony"].get("fabric") == "stone", "a stone balustrade stands round its top")
    st, phase = record()
    g = entry(phase, "p_gable")
    w = g["storeys"][0]["windows"]
    check(len(w) == 1 and w[0]["opening"] == "k06.opening.sash_round_fanlight" and len(w[0]["at"]) == 3,
          "p_gable's principal storey carries three round-arched lights")
    check("floor_balcony" not in g and not g["storeys"][1]["windows"],
          "p_gable carries no floor balcony of its own, and no light behind the oriel")


def param_refusals():
    for why, mut in (("a round oriel rising past half its chord", lambda e: e["plan"].update(rise_m=1.5, chord_m=2.7)),
                     ("a round oriel 4.5 m on its chord", lambda e: e["plan"].update(chord_m=4.5)),
                     ("a bow's keys beside a canted plan's",
                      lambda e: e["plan"].update(points=[[-1.0, 0.0], [-0.5, 0.5], [0.5, 0.5], [1.0, 0.0]])),
                     ("an oriel off the range's floors", lambda e: e.update(base_m=6.0)),
                     ("a bay on a rear wing's wall", lambda e: e.update(variant="k08.bay.bowed"))):
        st, phase = record()
        mut(entry(phase, "gable_oriel"))
        try:
            KP.from_phase(phase, st)
            check(False, f"{why}: refused")
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")


def canted_unchanged():
    """A canted oriel's corbel still reaches from its plan's front, not from any crown."""
    kit = {x["id"]: x for x in K8.load()["variants"]}
    v = copy.deepcopy(kit["k08.oriel.canted_corbelled"])
    m = built(v).meta["corbel"]
    front = max(z for _, z in v["plan"]["points"])
    check(abs(m["reach_m"] - front) < 1e-6, f"the kit's canted oriel reaches {m['reach_m']} m, its front's {front} m")


def main() -> int:
    record_checks()
    param_refusals()
    canted_unchanged()
    if failures:
        print(f"test_k08_round_oriel: {len(failures)} failed")
        return 1
    print("test_k08_round_oriel: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
