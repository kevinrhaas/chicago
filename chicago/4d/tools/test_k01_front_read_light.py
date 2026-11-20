#!/usr/bin/env python3
"""T-3562: 1815 Prairie's narrow light over the door, held on its record.

  * an upper storey's `front_bays_by_storey` entry may be a light read off the picture
    ({s_m, sill_m, width_m, height_m, head, why_not_ordinary}), laid once on the street
    front at its own sill and size as one narrow light; the storey's plain numbers are
    still its columns;
  * such a light is held to the side walls' read-window rules (the narrow light's reason
    and width, the front's own length for its ends) and kept clear of the street front's
    windows and door;
  * the principal storey takes none: its entries are the door's bay and columns.

    python3 tools/test_k01_front_read_light.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "sears_meeker_house_1815_prairie"
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
    change(phase["form"]["front_bays_by_storey"]["value"])
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


st, phase = record()
p = KP.from_phase(phase, st)
front = [o for o in p.openings if o.wall == "k01.wall.street_front" and o.component == "k01.opening.sash_flat"]
light = [o for o in front if abs(o.s_m - 4.22) < 1e-6]
check(len(light) == 1, f"the narrow light is laid once, at 4.22 m ({len(light)})")
if light:
    o = light[0]
    check(abs(o.width_m - 0.43) < 1e-6 and abs(o.sill_m - 6.19) < 1e-6 and abs(o.head_m - 7.28) < 1e-6,
          f"at its own size and sill: 0.43 m across, 6.19-7.28 m ({o.width_m}, {o.sill_m}, {o.head_m})")
    check(o.narrow and o.plain, "one light a sash, its head read")
check(sorted(round(o.sill_m, 2) for o in front if abs(o.s_m - 6.1) < 1e-6) == [2.15, 5.85],
      "the plain number (6.1 m) is still a column on both storeys")
check(len(front) == 3, f"three street sashes: two in the column, one read ({len(front)})")

refused(lambda v: v["1"][0].pop("why_not_ordinary"), "a read light narrower than the sash with no reason",
        "width_m")
refused(lambda v: v["1"][0].update(sill_m=4.6), "a read light down on the door's hood", "meets a window or the door")
refused(lambda v: v["1"][0].update(s_m=5.6), "a read light against the column's window",
        "meets a window or the door")
refused(lambda v: v.update({"0": [{**v["1"][0], "sill_m": 2.5}, 3.36, 6.1]}), "a read light on the principal storey",
        "on an upper storey")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
