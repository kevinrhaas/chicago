#!/usr/bin/env python3
"""T-1886: a bay light's carved crest (`bays[].storeys[].windows[].crest`).

Chicagology's photograph of 1816 Prairie draws the windows of both its canted bays under carved
hoods with a raised, scrolled crown, as the flat front's are. T-3270 gave the front's K09
cornice hoods that crown (`street_front_trim.crest`); a K08 bay's lights wore K06's plain
lintel and nothing over it, so the bays' heads stood bare beside the front's. K08 now stands
the same carving on a bay light's lintel. This holds the kit and the record to it:

  * the key takes width_m (0.4-2.0 m), height_m (0.15-0.6 m) and proud_m (0.04-0.2 m), the
    front's ranges, and nothing else;
  * refused: a crest on a round-headed light, over voussoirs or a tympanum, on a frame bay,
    and one rising past its storey;
  * 1816's record: every light of both bays' two storeys over the basement crested, none in
    the basement; each bay builds with one crest per light, each standing on its light's
    lintel, no wider than it, and under the storey over it;
  * T-3370: `past_band: true` lets a crest rise past its storey's band into the storey over it
    (1936's tower pair), refused when it is not true, on a top storey, past the storey over it,
    or onto a light of the storey over it; 1936's tower pair builds so, into its blind stage.

    python3 tools/test_k08_bay_crest.py
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
from archetypes import k08_bays as K8  # noqa: E402

SID = "henderson_house_1816_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())


def parse(mut=None):
    s = copy.deepcopy(st)
    if mut:
        mut(s["phases"][0]["form"]["bays"]["value"][0])
    return KP.from_phase(s["phases"][0], s)


def refused(mut, what):
    try:
        parse(mut)
    except (KP.ParamError, ValueError):
        check(True, f"refused: {what}")
        return
    check(False, f"refused: {what}")


def upper(b):
    return b["storeys"][1]["windows"][0]


def set_(key, val):
    def m(b):
        upper(b)["crest"][key] = val
    return m


refused(set_("width_m", 0.3), "a crest narrower than 0.4 m")
refused(set_("height_m", 0.7), "a crest taller than 0.6 m")
refused(set_("proud_m", 0.3), "a crest prouder than 0.2 m")
refused(lambda b: upper(b)["crest"].update(depth_m=0.1), "a crest with a key it does not take")
refused(lambda b: upper(b).update(opening="k06.opening.sash_round_fanlight"), "a crest on a round-headed light")
refused(lambda b: upper(b).update(voussoirs={"stones": 5, "splay_m": 0.1, "proud_m": 0.03, "joint_m": 0.01,
                                              "bevel_m": 0.01}), "a crest over voussoirs")
refused(lambda b: b.update(fabric="frame"), "a crest on a frame bay")
refused(lambda b: upper(b).update(clear_height_m=3.9), "a crest rising past its storey")

# -- 1816's record ----------------------------------------------------------------------------
p = parse()
check(len(p.bays) == 2, "1816 has its two canted bays")
for b in p.bays:
    v = b["variant"]
    rows = [[w.get("crest") for w in s["windows"]] for s in v["storeys"]]
    check(all(c is None for c in rows[0]), f"{b['id']}: no crest on the basement's barred lights")
    check(all(c == {"height_m": 0.35, "proud_m": 0.1, "width_m": 1.0} for r in rows[1:] for c in r),
          f"{b['id']}: every light of the two storeys over it crested as the front's hoods are")
    built = K8.Bay(v, K8.load(), "full").build(board=False)
    lights = sum(len(w["at"]) for s in v["storeys"][1:] for w in s["windows"])
    check(built.meta.get("crests") == lights, f"{b['id']}: {built.meta.get('crests')} crests laid, one per light ({lights})")
    cv = built.prims.get("carving")
    check(cv is not None and len(cv.pos) > 0, f"{b['id']}: the crests are carving")
    if cv is not None and len(cv.pos):
        heads = built.prims["head"].pos
        top_head = max(q[1] for q in heads)
        check(max(q[1] for q in cv.pos) <= top_head + 0.35 + 1e-6,
              f"{b['id']}: no crest stands taller than its 0.35 m over the highest lintel")
        check(min(q[1] for q in cv.pos) >= min(q[1] for q in heads) - 1e-6,
              f"{b['id']}: every crest stands on a lintel, none below one")

# -- T-3370: a crest let past its storey's band ------------------------------------------------
refused(lambda b: upper(b)["crest"].update(past_band=False), "a crest's past_band that is not true")
refused(lambda b: b["storeys"][-1]["windows"][0].setdefault("crest", dict(upper(b)["crest"])).update(past_band=True)
        if b["storeys"][-1]["windows"] else (_ for _ in ()).throw(ValueError("no top light")),
        "a crest let past the band on the top storey")
SID2 = "house_1918_prairie"
st2 = json.loads((ROOT / "data" / "structures" / f"{SID2}.json").read_text())
ph2 = next(ph for ph in st2["phases"] if ph["form"].get("bays"))
p2 = KP.from_phase(ph2, st2)
tw = [b for b in p2.bays if any((w.get("crest") or {}).get("past_band")
                               for s_ in b["variant"]["storeys"] for w in s_["windows"])]
check(len(tw) == 1, "1936 has one bay whose crests are let past its band (the tower)")
if tw:
    v2 = tw[0]["variant"]
    k2 = next(k for k, s_ in enumerate(v2["storeys"]) if any((w.get("crest") or {}).get("past_band") for w in s_["windows"]))
    check(not v2["storeys"][k2 + 1]["windows"], "the storey over the tower pair is blind")
    built2 = K8.Bay(v2, K8.load(), "full").build(board=False)
    # the whole stage over the cornice takes the bay's meta for its own, so read the carving
    lv = built2.meta.get("levels_m")
    cv2 = [q for q in built2.prims["carving"].pos] if "carving" in built2.prims else []
    check(lv is not None and any(lv[k2 + 1] + 0.1 < q[1] < lv[k2 + 2] for q in cv2),
          "the tower pair's crests rise past the storey's band into the blind stage")
    check(lv is not None and all(q[1] < lv[k2 + 2] - 0.05 for q in cv2 if q[1] > lv[k2]),
          "and stop under the blind stage's top")

    def deeper(mut):
        s2 = copy.deepcopy(st2)
        ph = next(ph for ph in s2["phases"] if ph["form"].get("bays"))
        b = next(b for b in ph["form"]["bays"]["value"] if b["id"] == tw[0]["id"])
        mut(b)
        v3 = next(x for x in KP.from_phase(ph, s2).bays if x["id"] == tw[0]["id"])["variant"]
        K8.Bay(v3, K8.load(), "full").build(board=False)

    def taller_storey_over(b):
        b["storeys"][k2 + 1]["windows"] = [dict(next(w for w in b["storeys"][k2]["windows"] if w.get("crest")),
                                                sill_m=0.1, clear_height_m=1.2)]
        b["storeys"][k2 + 1]["windows"][0].pop("crest")
        b["storeys"][k2 + 1]["windows"][0].pop("surround", None)
    try:
        deeper(taller_storey_over)
        check(False, "refused: a crest let past the band onto a light of the storey over it")
    except (KP.ParamError, ValueError):
        check(True, "refused: a crest let past the band onto a light of the storey over it")

a = K1.build(p, SID)
check(a is not None, "1816 builds")

if failures:
    print(f"\n{len(failures)} check(s) failed")
    sys.exit(1)
print("\nall checks passed")
