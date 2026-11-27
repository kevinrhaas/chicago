#!/usr/bin/env python3
"""T-3562: 1815 Prairie's narrow light over the door, held on its record.

  * an upper storey's `front_bays_by_storey` entry may be a light read off the picture
    ({s_m, sill_m, width_m, height_m, head, why_not_ordinary}), laid once on the street
    front at its own sill and size as one narrow light; the storey's plain numbers are
    still its columns;
  * such a light is held to the side walls' read-window rules (the narrow light's reason
    and width, the front's own length for its ends) and kept clear of the street front's
    windows and door;
  * T-3634: the principal storey may take one too (2021 Prairie's narrow light between the
    arched porch and the broad window), its sill on the principal floor or over it; one
    under it is a basement light, and is refused.

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
# T-3562 (the owner's ruling, 2026-11-21): the 1902 remodel's one-storey bay stands before the
# principal storey, so its only street opening is the door (front_bays_by_storey "0"); the
# column at 6.1 m is the second storey's alone
check(sorted(round(o.sill_m, 2) for o in front if abs(o.s_m - 6.1) < 1e-6) == [5.85],
      "the plain number (6.1 m) is still the second storey's column")
check(len(front) == 2, f"two street sashes: one in the column, one read ({len(front)})")

refused(lambda v: v["1"][0].pop("why_not_ordinary"), "a read light narrower than the sash with no reason",
        "width_m")
refused(lambda v: v["1"][0].update(s_m=-0.3), "a read light past the front's north corner", "wall's ends")
refused(lambda v: v["1"][0].update(s_m=5.6), "a read light against the column's window",
        "meets a window or the door")
refused(lambda v: v.update({"0": [{**v["1"][0], "sill_m": 0.5}, -0.7]}), "a read light under the principal floor",
        "principal floor")

# T-3634: 2021 Prairie's principal storey takes the narrow light read between its porch and
# its broad window, laid once at its own size beside the storey's columns
st21 = json.loads((ROOT / "data" / "structures" / "high_house_2021_prairie.json").read_text())
p21 = KP.from_phase(st21["phases"][-1], st21)
f21 = [o for o in p21.openings if o.wall == "k01.wall.street_front" and o.component == "k01.opening.sash_flat"]
nl = [o for o in f21 if abs(o.s_m - 4.86) < 1e-6]
check(len(nl) == 1 and nl[0].narrow and nl[0].plain and abs(nl[0].sill_m - 2.3) < 1e-6
      and abs(nl[0].width_m - 0.65) < 1e-6,
      f"2021's narrow principal-storey light is laid once, 0.65 m across on a 2.3 m sill ({len(nl)})")
check(sorted(round(o.s_m, 2) for o in f21 if o.sill_m < 5.0) == [4.86, 7.4],
      "2021's principal storey: the read light and the broad light's column (the porch's bay is its door)")

if failures:
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
