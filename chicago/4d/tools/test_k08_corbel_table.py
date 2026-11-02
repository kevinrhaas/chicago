#!/usr/bin/env python3
"""T-1890: a K08 storey may stand on a corbel table, and a gable panel may be carved as a fan.

1801 Prairie's 18th Street section, read off the Taylor print and HABS photograph 2, carries
its third storey on a corbel table at about 9.45 m (a stone course on a row of stepped
corbels) and a coped wall dormer about 3.2 m across over it, a fan carved in its tympanum.
The kit laid a floor band at every storey line, a leafy relief in every gable panel and a
gable no more than a metre in from its front's corners. This holds the kit and the record to
what the ticket says:

  * a storey naming `corbel_table` stands on a course `course_m` deep and `proud_m` out under
    its floor line, in place of the floor band, with a row of corbels under the course down to
    `height_m` under the line, as many as the run holds at `pitch_m`;
  * the light tier keeps the course and drops the corbels;
  * a gable panel whose relief is `kind: fan` lays a half wheel on the panel (a ring, rays and
    a hub), the leafy relief's keys refused beside it;
  * a gable may stand up to 1.5 m in from its front's corners, and no further;
  * a corbel table on the ground storey, or out of its ranges, is refused by the record's params;
  * 1801's p_flank builds from its record with its corbel table, fan gable and finial.

    python3 tools/test_k08_corbel_table.py
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


def flank_entry(phase):
    return next(b for b in phase["form"]["bays"]["value"] if b["id"] == "p_flank")


def flank_variant(st=None, phase=None):
    if st is None:
        st, phase = record()
    p = KP.from_phase(phase, st)
    return next(b for b in p.bays if b["id"].endswith("p_flank"))["variant"]


def built(v, tier="full"):
    return K8.Bay(copy.deepcopy(v), K8.load(), tier).build(board=False)


def record_checks():
    v = flank_variant()
    ct = v["storeys"][2]["corbel_table"]
    b = built(v)
    m = b.meta
    line = m["levels_m"][2]
    check(abs(line - 9.45) < 1e-6 and abs(m["wall_top_m"] - 12.4) < 1e-6,
          f"p_flank's third storey stands on the 9.45 m line under a 12.4 m wall top ({m['levels_m']}, {m['wall_top_m']})")
    cor = b.prims["corbel"].pos
    check(bool(cor) and min(q[1] for q in cor) >= line - ct["height_m"] - 1e-6
          and max(q[1] for q in cor) <= line - ct["course_m"] + 1e-6,
          f"the corbels hang from the course down to {line - ct['height_m']:.2f} m")
    front = (K8.locate(b.runs, b.plan, {"at": [0.5]})[0][0])
    run = b.runs[front]
    n_front = int((run.L - 2 * ct["margin_m"] - ct["block_m"]) // ct["pitch_m"]) + 1
    check(m.get("corbel_table", 0) >= n_front,
          f"the front's run carries its row: {m.get('corbel_table')} corbels, at least {n_front} on the front")
    course = [q for q in b.prims["band"].pos if abs(q[1] - (line - ct["course_m"])) < 1e-6]
    check(bool(course), f"the course is laid in the band's stone, its bed {ct['course_m']} m under the line")
    hb = K8.part(v, K8.load(), "floor_band")["height_m"]
    stray = [q for q in b.prims["band"].pos if abs(q[1] - (line + hb / 2)) < 1e-6]
    check(not stray, f"no floor band is laid over the corbel table's line (none at {line + hb / 2:.3f} m)")
    under = [q for q in b.prims["band"].pos if abs(q[1] - (m["levels_m"][1] + hb / 2)) < 1e-6]
    check(bool(under), "the storey line under it keeps its floor band")
    lt = built(v, "light")
    check("corbel" not in lt.prims or not lt.prims["corbel"].pos, "the light tier drops the corbels")
    check(bool(lt.prims["band"].pos), "and keeps the course")
    rf = m["roof"]
    check(rf["kind"] == "gable" and rf.get("panel", {}).get("fan", {}).get("rays") == 13
          and rf["panel"]["fan"]["radius_m"] > 0.5,
          f"its wall dormer is a coped gable with a fan of 13 rays ({rf.get('panel')})")
    check(abs(rf["finial_top_m"] - 15.15) < 0.35,
          f"its finial's top at {rf['finial_top_m']} m, near the 15.15 m both pictures read")


def kit_refusals():
    v = flank_variant()
    g = v["roof"]["gable"]
    for why, mut in (("a fan beside a leafy relief's keys", lambda g: g["panel"]["relief"].update(stem_m=0.1)),
                     ("a fan of 3 rays", lambda g: g["panel"]["relief"].update(rays=3)),
                     ("a gable 2.6 m in from a corner", lambda g: g.update(inset_m=[2.6, 1.4]))):
        w = copy.deepcopy(v)
        mut(w["roof"]["gable"])
        try:
            built(w)
            check(False, f"{why}: refused")
        except ValueError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")
    w = copy.deepcopy(v)
    w["roof"]["gable"]["inset_m"] = [1.5, 1.5]
    try:
        built(w)
        check(True, "a gable 1.5 m in from both corners builds")
    except ValueError as e:
        check(False, f"a gable 1.5 m in from both corners builds ({e})")
    # T-1890: the section stands at the 1911 sheet's 0.1 m, a shallow projection 6.97 m across, its
    # wall dormer where the Taylor print stands it (a shallow gable may stand 2.5 m in)
    check(v.get("shallow") is True and g["inset_m"] == [1.489, 2.281],
          f"1801's is a shallow section's, 1.489 and 2.281 m in ({g['inset_m']})")


def param_refusals():
    for why, mut in (("a corbel table under the ground storey",
                      lambda e: e["storeys"][0].update(corbel_table=copy.deepcopy(e["storeys"][2]["corbel_table"]))),
                     ("a corbel table 2 m deep", lambda e: e["storeys"][2]["corbel_table"].update(height_m=2.0)),
                     ("corbels closer than their own width", lambda e: e["storeys"][2]["corbel_table"].update(pitch_m=0.2)),
                     ("a corbel table missing its margin", lambda e: e["storeys"][2]["corbel_table"].pop("margin_m"))):
        st, phase = record()
        mut(flank_entry(phase))
        try:
            KP.from_phase(phase, st)
            check(False, f"{why}: refused")
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")


def main() -> int:
    record_checks()
    kit_refusals()
    param_refusals()
    if failures:
        print(f"test_k08_corbel_table: {len(failures)} failed")
        return 1
    print("test_k08_corbel_table: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
