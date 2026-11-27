#!/usr/bin/env python3
"""T-3713: a K01 mansard may stop short of a side wall, the strip beyond it railed and flat.

2115 Prairie's front south of its pavilion: the Armour photograph draws no mansard over it and
its cornice under a low railing, and the Tribune's 1928 halftone shows the roof line dropping
from the pavilion's crown to a railing with sky over it. The record names `mansard.short_end`
(wall, width_m, balustrade); this holds the kit to it:

  * resolved: the mansard (ring, curb, ridge, crown and deck) is read on the plan `width_m`
    narrower, and the ridge falls by the half-width lost at the deck's pitch;
  * the build: no roof face of the mansard's stands over the strip above the wall head but the
    strip's deck, the deck's top is at the wall head across the strip, out to the fascia; and
    the balustrade stands on it, its top `height_m` over the wall head;
  * as-was: without short_end the mansard is T-3712's (curb, ridge and roof reach the wall);
  * refused: a south short end, a strip under 1 m or over a third of the front, a short end
    beside walled ends, and a balustrade out of its bounds.

    python3 tools/test_k01_mansard_short.py
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

SID = "armour_house_2115_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    return json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def form(st):
    return st["phases"][0]["form"]


def params(st):
    return KP.from_phase(st["phases"][0], st)


def refused(change, what):
    st = record()
    change(form(st)["mansard"]["value"])
    try:
        params(st)
    except KP.ParamError as e:
        check(True, f"refused: {what} ({str(e)[:90]})")
        return
    check(False, f"refused: {what}")


st = record()
p = params(st)
m = p.mansard
se = m.get("short_end")
W, D, E, o = p.width_m, p.depth_m, p.eave_m, p.eave_overhang_m
check(se is not None and se["wall"] == "north" and abs(se["width_m"] - 2.04) < 1e-9,
      "2115 names a 2.04 m short end on its north (the real south) wall")
mw = W - se["width_m"]

# the plain mansard, as T-3712/T-3713 built it before the short end
plain = record()
mv = form(plain)["mansard"]["value"]
del mv["short_end"]
pp = params(plain)
run = m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
drop = (W - mw) / 2 * math.tan(math.radians(p.roof_pitch_deg))
check(abs((pp.mansard["ridge_m"] - m["ridge_m"]) - drop) < 1e-3,
      f"the ridge falls {drop:.3f} m, the half-width lost at the deck's pitch")
check(abs(m["curb_m"] - pp.mansard["curb_m"]) < 1e-9, "the curb's height is the plain mansard's")
check(abs(m["deck"]["curb"][3] - (mw + o - run)) < 1e-3,
      f"the deck's north curb stands at v {m['deck']['curb'][3]}, inside the shortened ring")
check(abs(pp.mansard["deck"]["curb"][3] - (W + o - run)) < 1e-3, "as-was: the plain deck's curb runs to the wall")
check("short_end" not in pp.mansard, "as-was: no short end on the plain mansard")

# the build
a = K1.build(p, SID)
roof_pts, _ = a.roof_shell
zstrip = -W + se["width_m"]
over = [q for q in roof_pts if -W - o - 1e-6 < q[2] < zstrip - o - 0.05]
check(bool(over) and max(q[1] for q in over) <= E + 1e-4,
      "nothing of the roof shell stands over the strip above the wall head"
      + (f" ({max(q[1] for q in over):.3f} m against {E} m)" if over else ""))
check(any(abs(q[2] - (-W - o)) < 1e-4 and abs(q[1] - E) < 1e-4 for q in roof_pts),
      "the strip's deck runs out to the fascia past the north wall, at the wall head")
check(any(q[2] > zstrip + 0.05 and q[1] > E + 1.0 for q in roof_pts), "the mansard stands over the main body")
a0 = K1.build(pp, SID)
check(max(q[1] for q in a0.roof_shell[0] if q[2] < zstrip - o - 0.05) > E + 1.0,
      "as-was: the plain mansard stands over the strip")
# the balustrade: the front's trim stone over the strip's deck, its dies' tops 0.08 m over its rail
bal = se["balustrade"]
stone = [q for q in a.prims["limestone_trim"].pos if q[2] < zstrip - o + 1e-6 and E - 1e-6 <= q[1]]
top = max((q[1] for q in stone), default=None)
check(top is not None and abs(top - (E + bal["height_m"] + 0.08)) < 1e-4,
      f"the balustrade stands on the deck, its dies' tops {bal['height_m'] + 0.08:.2f} m over the wall head")
check(any(abs(q[1] - (E + bal["height_m"])) < 1e-4 for q in stone), "its rail's top is height_m over the wall head")
check(any(abs(q[0] - (D + o - bal["inset_m"])) < 1e-4 for q in stone),
      "its street run's face stands inset_m inside the fascia")

# refused
refused(lambda m_: m_["short_end"].update(wall="south"), "a short end on the south (low-v) wall")
refused(lambda m_: m_["short_end"].update(width_m=0.8), "a strip under 1 m")
refused(lambda m_: m_["short_end"].update(width_m=4.5), "a strip over a third of the front")
refused(lambda m_: m_["short_end"]["balustrade"].update(height_m=1.5), "a balustrade over 1.2 m")
refused(lambda m_: m_["short_end"]["balustrade"].update(bar_m=0.3), "a baluster as thick as the rail")
refused(lambda m_: m_["short_end"].pop("balustrade"), "a short end with no balustrade")
refused(lambda m_: m_.update(walled_ends=[{"wall": "south", "party": False, "upstand_m": 0.3}]),
        "a short end beside walled ends")

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
