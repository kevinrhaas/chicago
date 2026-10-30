#!/usr/bin/env python3
"""T-3097: 1801 Prairie's second-storey lights, held on its record.

  * K01's side_bays take windows read off a picture ({s_m, sill_m, width_m, height_m, head}),
    as north_bays do: each laid once on the south wall at its own sill, the plain numbers
    still a column on every storey;
  * on an all-stone house's side face, a read round head stands in the coursing under no
    flat arch, its spandrels laid in the wall's stone;
  * the read windows on that wall are held to north_bays' rules (the ordinary sash's width,
    clear of each other and of the wall's ends).

    python3 tools/test_k01_side_read_windows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "kimball_house_1801_prairie"
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
    change(phase["form"])
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


st, phase = record()
p = KP.from_phase(phase, st)
south = sorted((o.s_m, o.sill_m, o.component) for o in p.openings if o.wall == "k01.wall.side.south")
front = [o for o in p.openings if o.wall == "k01.wall.street_front" and o.component == "k01.opening.sash_flat"]
check(not any(abs(s - 15.6) < 1e-6 for s, _, _ in south), "no sash a storey at 15.6 m, where the print has the pair")
pair = [(s, y) for s, y, c in south if c == KP.ROUND_PLAIN]
check([round(s, 2) for s, _ in pair] == [14.93, 16.03] and all(abs(y - 6.08) < 1e-6 for _, y in pair),
      f"the round-headed pair is laid once, at its own sill ({pair})")
check(sum(1 for s, _, _ in south if abs(s - 18.67) < 1e-6) == 1 and not any(abs(s - 18.9) < 1e-6 for s, _, _ in south),
      "the light over the side arch is laid once, at 18.67 m, off the arch's axis")
check(sum(1 for s, _, _ in south if abs(s - 1.6) < 1e-6) == 2, "the plain number (1.6 m) is still a column on both storeys")
check(len(front) == 1 and abs(front[0].sill_m - 5.4) < 1e-6 and abs(front[0].head_m - 7.7) < 1e-6,
      f"the front's second-storey light stands 5.4-7.7 m ({[(o.sill_m, o.head_m) for o in front]})")
check(tuple(round(s, 2) for s in p.side_bays) == (1.6, 14.93, 16.03, 18.67), f"side_bays reads as centres ({p.side_bays})")

a = K1.build(p, SID)
dressed = a.components.get("k01.opening.street_dress", {}).get("instances", [])
check(len(dressed) == 2, f"each read round head's spandrels are dressed in the flank's stone ({len(dressed)})")

refused(lambda f: f["side_bays"]["value"][1].update(width_m=0.5), "a read light narrower than the sash with no reason",
        "side_bays[1].width_m")
refused(lambda f: f["side_bays"]["value"][2].update(s_m=15.2), "two read lights on one pier too narrow",
        "meets another read window")
refused(lambda f: f["side_bays"]["value"][3].update(s_m=20.2), "a read light at the wall's end", "within 0.45 m")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nall ok")
