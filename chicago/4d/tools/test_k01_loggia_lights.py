#!/usr/bin/env python3
"""T-1890: single lights named by wall, place and storey (`street_front_trim.lights`).

1801 Prairie's two lights over the loggia, the avenue front's and the 18th Street flank's,
each stand in a moulded frame under a projecting head in the Taylor print, their transom bar
about 0.75-1.0 m under the head. The K09 heads dressed the street front alone, and a K01
wall's transom light was K06's 0.45 m. This holds the kit and the record to what the ticket
says:

  * a light named in `lights` on a side wall wears its storey's `by_storey` head, and a side
    light it does not name keeps K01's flat lintel;
  * a named light's `tiers` reach its K06 variant; an unnamed light's variant has none;
  * a name that matches no square-headed light, or tiers out of range, is refused;
  * 1801's two lights over the loggia wear the kit's restrained surround on 0.8 m top lights;
  * and each stands between two carved pilasters (`pilasters`, read off the Taylor print and
    HABS 1965's photograph 2): a capital carries each end of the hood, which runs out over
    them and hangs no console, one lozenge to a shaft; the kit's surround elsewhere keeps its
    consoles, and pilasters out of range, or beside a light no surround dresses, are refused.

    python3 tools/test_k01_loggia_lights.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k09_frontage as K9  # noqa: E402

SID = "kimball_house_1801_prairie"
SURROUND = "k09.surround.rowhouse_restrained"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


class _Host:
    """Just what Assembly.kit_variant reads off its instance."""
    def __init__(self, p):
        self.p = p


def checks():
    st, phase = record()
    p = KP.from_phase(phase, st)
    sq = [o for o in p.openings if o.component == "k01.opening.sash_flat"]
    front = [o for o in sq if o.wall == "k01.wall.street_front" and abs(o.s_m - 1.6) < 1e-6]
    flank = [o for o in sq if o.wall == "k01.wall.side.south" and abs(o.s_m - 18.67) < 1e-6]
    check(len(front) == 1 and len(flank) == 1, "1801 has one light over the loggia on each face")
    if len(front) != 1 or len(flank) != 1:
        return
    check(K9.head(p, front[0]) == SURROUND and K9.head(p, flank[0]) == SURROUND,
          "both lights over the loggia wear the kit's restrained surround")
    others = [o for o in sq if o.wall == "k01.wall.side.south" and o is not flank[0]]
    check(others and all(K9.head(p, o) == K9.FLAT for o in others),
          f"the flank's other {len(others)} square lights keep K01's flat lintel")
    host = _Host(p)
    v = K1.Assembly.kit_variant(host, flank[0])
    check(v.get("tiers") == {"bar_m": 0.1, "lights_m": [0.8]}, f"the flank light's top light is 0.8 m ({v.get('tiers')})")
    check(all("tiers" not in K1.Assembly.kit_variant(host, o) for o in others), "an unnamed light has no tiers")
    for why, edit in (("a light at no opening", lambda e: e.update(s_m=3.3)),
                      ("a light on the wrong storey", lambda e: e.update(storey=0)),
                      ("a 1.6 m top light", lambda e: e.update(tiers={"bar_m": 0.1, "lights_m": [1.6]})),
                      ("an unknown key", lambda e: e.update(head=SURROUND)),
                      ("pilasters 0.02 m off the architrave", lambda e: e["pilasters"].update(gap_m=0.02)),
                      ("a pilaster foot over the sill", lambda e: e["pilasters"].update(foot_m=5.4)),
                      ("seven lozenges", lambda e: e["pilasters"]["lozenges"].update(count=7)),
                      ("a pilaster's unknown key", lambda e: e["pilasters"].update(fluted=True))):
        st, phase = record()
        edit(phase["form"]["street_front_trim"]["value"]["lights"][1])
        try:
            KP.from_phase(phase, st)
            check(False, f"{why}: refused")
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")


def pilasters():
    from archetypes import k09_trim as KT
    st, phase = record()
    p = KP.from_phase(phase, st)
    lts = p.street_front_trim["lights"]
    check(all(e.get("pilasters", {}).get("lozenges", {}).get("count") == 1 for e in lts),
          "both lights over the loggia carry pilasters, one lozenge to a shaft")
    a = K1.build(p, SID)
    inst = a.components.get(K9.PILASTER, {}).get("instances", [])
    check(len(inst) == 2, f"two pilastered lights are built ({len(inst)})")
    sur = [i["params"] for i in a.components[SURROUND]["instances"] if i["params"].get("consoles") is False]
    want = K9.pilaster_overhang(lts[0]["pilasters"])
    check(len(sur) == 2 and all(abs(q["overhang_m"] - want) < 1e-9 for q in sur),
          f"their hoods run {want} m past the architrave and hang no console")
    data = KT.load()
    v = next(x for x in data["variants"] if x["id"] == SURROUND)
    plain = {q.name for q in KT.build_variant(v, data).pieces}
    bare = {q.name for q in KT.build_variant(dict(v, consoles=False, overhang_m=want), data).pieces}
    check({"console 1", "console 2"} <= plain and not {"console 1", "console 2"} & bare,
          "the kit's surround keeps its consoles unless a light's pilasters carry its hood")
    st, phase = record()
    t = phase["form"]["street_front_trim"]["value"]
    t["by_storey"][1] = K9.FLAT
    try:
        KP.from_phase(phase, st)
        check(False, "pilasters beside a light no surround dresses: refused")
    except KP.ParamError as e:
        check(True, f"pilasters beside a light no surround dresses: refused ({str(e)[:50]}...)")


def main() -> int:
    checks()
    pilasters()
    if failures:
        print(f"test_k01_loggia_lights: {len(failures)} failed")
        return 1
    print("test_k01_loggia_lights: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
