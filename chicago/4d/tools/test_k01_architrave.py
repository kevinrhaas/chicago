#!/usr/bin/env python3
"""T-1881: a K01 named street window's round head framed by a moulded architrave.

1729 Prairie's record carries them, off the 1890 Albertype plate: every round-arched light of
the Prairie front, on both storeys, stands in a moulded band down its jambs and round its arch,
with an impost block at the springing, and the principal storey's under a keystone too. The
`architrave` key on a `street_front_windows` entry builds them. This holds the committed
record's assembly to that:

  * the three named lights left on the front's own wall are framed, the principal storey's
    keyed, the second storey's not (T-1881, 2026-11-01: the north and south bays' lights stand on
    the two pavilions either side of the stepped-in centre, as K08 lights);
  * the pavilions' four K08 lights framed the same way by the bays' `architrave` key (T-1881,
    2026-11-01, from PR 1550): the principal storey's keyed, the second storey's not, at both tiers;
  * each architrave's band springs where its light's round head springs and wraps the light,
    and stands clear of the front's rusticated piers (street_front_pavilions);
  * refused: voussoirs and an architrave on one light, an architrave over a flat head, a band
    out of its range, an unknown key, and two architraves run into one another, and the same
    for a bay light's.

    python3 tools/test_k01_architrave.py
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

SID = "pullman_house_1729_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record(edit=None):
    st = copy.deepcopy(json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text()))
    phase = st["phases"][-1]
    if edit:
        edit(phase["form"]["street_front_windows"]["value"]["windows"])
    return st, phase


def refused(edit, says, what):
    st, phase = record(edit)
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"refused: {what} ({e})")
        return
    check(False, f"refused: {what} — it was accepted")


st, phase = record()
wins = phase["form"]["street_front_windows"]["value"]["windows"]
p = KP.from_phase(phase, st)
arcs = p.street_dress.get("architraves", ())
check(len(arcs) == 2 and len(wins) == 2, f"both of the south part's named lights are framed ({len(arcs)})")
check(not p.street_dress.get("voussoirs"), "no light on the front is still turned in voussoirs")
keyed = sorted(a["s_m"] for a in arcs if a.get("key_m"))
check(keyed == sorted(w["s_m"] for w in wins if w["storey"] == 0 and "architrave" in w),
      f"the principal storey's lights are keyed, the second storey's not ({keyed})")
check(all(a.get("impost_m") for a in arcs), "every architrave steps out in an impost at its springing")
a = K1.build(p, st["id"])
meta = getattr(a, "architrave_meta", [])
check(len(meta) == 2, f"the assembly framed two lights ({len(meta)})")
for m in meta:
    w = next(w for w in wins if "architrave" in w and abs(w["s_m"] - m["s_m"]) < 1e-6 and abs(w["sill_m"] - m["sill_m"]) < 1e-6)
    spring = w["sill_m"] + w["height_m"] - w["width_m"] / 2
    check(abs(m["spring_m"] - spring) < 0.02 and abs(m["radius_m"] - w["width_m"] / 2) < 0.02,
          f"s {m['s_m']}: the band springs with the light's round head ({m['spring_m']} m, r {m['radius_m']} m)")
    b = next(x for x in arcs if x["s_m"] == m["s_m"] and x["sill_m"] == m["sill_m"])["band_m"]
    check(m["outer_m"][0] < w["s_m"] - w["width_m"] / 2 and m["outer_m"][1] > w["s_m"] + w["width_m"] / 2
          and abs(m["outer_m"][1] - m["outer_m"][0] - w["width_m"] - 2 * b) < 1e-3,
          f"s {m['s_m']}: and wraps the light, {b} m broad each side")
piers = [pp["s_m"] for pp in phase["form"]["street_front_pavilions"]["value"]["piers"]
         if pp.get("wall", "k01.wall.street_front") == "k01.wall.street_front"]
for r in arcs:
    lo, hi = r["s_m"] - r["half_m"], r["s_m"] + r["half_m"]
    check(all(hi <= p0 or lo >= p1 for p0, p1 in piers), f"s {r['s_m']}: clear of the piers ({lo:.2f}-{hi:.2f} m)")

refused(lambda ws: ws[1].update(voussoirs={"ring_m": 0.25, "stones": 13, "proud_m": 0.05, "key_m": [0.22, 0.3]}),
        "not both", "voussoirs and an architrave on one light")
refused(lambda ws: ws[0]["architrave"].update(band_m=0.6), "architrave: a 0.1-0.45 m band", "a band out of range")
refused(lambda ws: ws[0]["architrave"].update(hood=True), "architrave takes", "an unknown key")
refused(lambda ws: ws[0]["architrave"].update(key_m=[0.3, 0.1]), "key_m", "a keystone lower than the band")
refused(lambda ws: ws.append(dict(ws[0], s_m=12.9)), "runs into", "two architraves run into one another")


# T-1881 (2026-11-01): the two pavilions' K08 lights framed by the bays' `architrave` key, each
# with the architrave it carried as a K01 light (principal storey keyed, second storey not)
from archetypes import k08_bays as K8  # noqa: E402


def bay_light(ph, bid="p_entry", storey=1):
    b = next(b for b in ph["form"]["bays"]["value"] if b["id"] == bid)
    return b["storeys"][storey]["windows"][0]


# round 3 (the owner's sketch, 2026-11-01): the forward block carries a light at each storey,
# the principal storey's keyed; the entry carries its one upper light over the door, unkeyed
for bid, keyed in (("p_block", [True, False]), ("p_entry", [False])):
    var = next(b for b in p.bays if b["id"] == bid)["variant"]
    ar = [w.get("architrave") for s_ in var["storeys"] for w in s_["windows"]]
    check(len(ar) == len(keyed) and all(ar) and [("key_m" in a) for a in ar] == keyed,
          f"{bid}'s lights carry architraves, only the principal storey's keyed ({ar})")
    for tier in ("full", "light"):
        bay = K8.Bay(var, K8.load(), tier=tier)
        bay.build()
        check(bay.meta.get("architraves") == len(keyed), f"K08 frames {bid}'s lights at the {tier} tier")


def bay_refused(edit, says, what):
    st_, ph = record()
    edit(bay_light(ph))
    try:
        KP.from_phase(ph, st_)
    except KP.ParamError as e:
        check(says in str(e), f"refused: {what} ({e})")
        return
    check(False, f"refused: {what} — it was accepted")


bay_refused(lambda w: w.update(opening="k06.opening.sash_2over2_flat"), "round-headed",
            "a bay architrave round a flat head")
bay_refused(lambda w: w["architrave"].update(band_m=0.05), "0.1-0.45 m band", "a bay architrave's band out of range")
bay_refused(lambda w: w["architrave"].update(hood=True), "takes band_m", "an unknown bay architrave key")
bay_refused(lambda w: w.update(voussoirs={"stones": 5, "splay_m": 0.1, "proud_m": 0.04, "joint_m": 0.01,
                                          "bevel_m": 0.01}), "without a surround, voussoirs",
            "a bay architrave beside voussoirs")
bay_refused(lambda w: w["architrave"].update(key_m=[0.3, 0.1]), "key_m", "a bay keystone lower than its band")

print(f"\n{'FAIL' if failures else 'PASS'}: test_k01_architrave — {len(failures)} failure(s)")
sys.exit(1 if failures else 0)
