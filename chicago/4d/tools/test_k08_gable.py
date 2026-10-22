#!/usr/bin/env python3
"""T-2998: a K08 projection capped with a coped stone gable, held on 1801 Prairie's pavilion.

J. W. Taylor's c. 1895 photograph of the Kimball house shows its south pavilion carried up
past the main cornice as a steep stone gable: raking copings springing from blocks over the
pavilion's corners, a pinnacle on each and a finial at the apex, a slate ridge behind it. K08
capped a projection only with a hip, so:

  * a projection's roof may be a `gable`: its front carried up between two kneelers over the
    plan's front corners, a slope from each kneeler's inner face to a ridge on the plan's
    middle run back to the wall plane, a stone coping along each rake standing `upstand_m`
    over the roof's plane and proud of the face, and (when the roof names them) a pinnacle
    on each kneeler and a stone finial on the apex;
  * the front has no eaves, and the returns' eaves stop square on the front's plane, hidden
    in the kneelers;
  * every other roof builds exactly as before (the kit's own variants, byte for byte in
    their geometry);
  * a gable on any other plan, or one whose sizes do not fit, is refused, saying why.

    python3 tools/test_k08_gable.py
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


def pavilion():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    p = KP.from_phase(st["phases"][-1], st)
    return next(b for b in p.bays if b["id"] == "p_south")


def refused(v, why, says):
    try:
        K8.build_variant(v, board=False)
    except ValueError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:100]}...)")
        return
    check(False, f"{why}: built anyway")


def main() -> int:
    b = pavilion()
    v = b["variant"]
    rf = v["roof"]
    check(rf["kind"] == "gable" and v["kind"] == "projection", "1801's south pavilion is a projection under a gable")
    built = K8.build_variant(v, board=False)
    m, meta = built.meta, built.meta["roof"]
    pts = v["plan"]["points"]
    xl, p, xr = pts[1][0], pts[1][1], pts[2][0]
    xc = (xl + xr) / 2
    g = rf["gable"]
    xa = xl + g["kneeler"]["width_m"]
    y_top, y_e = m["wall_top_m"], m["eave_m"]

    # the roof: two slopes from the kneelers to a ridge on the middle, run back to the wall
    roof = built.prims["roof"].pos
    ridge = max(q[1] for q in roof)
    want = y_e + rf["pitch"] * (xc - xa)
    check(abs(ridge - want) < 1e-6 and abs(meta["ridge_m"] - want) < 1e-4,
          f"its ridge stands pitch x the gable's half-width over the eaves line ({ridge:.3f} m)")
    check(all(abs(q[0] - xc) < 1e-9 for q in roof if abs(q[1] - ridge) < 1e-9), "on the plan's middle")
    check(min(q[2] for q in roof) == 0.0 and max(q[2] for q in roof) < p, "run back from inside the front to the wall plane")
    check(min(q[0] for q in roof) >= xa - 1e-9 and max(q[0] for q in roof) <= xr - g["kneeler"]["width_m"] + 1e-9,
          "between the kneelers' inner faces")

    # the gable: the front carried up to the copings' beds, and the copings over it
    wall = built.prims["wall"].pos
    front = [q for q in wall if abs(q[2] - p) < 1e-9 and q[1] > y_top + 1e-6]
    under = y_e + rf["pitch"] * (xc - xa) + g["upstand_m"]
    check(front and abs(max(q[1] for q in front) - under) < 1e-6,
          f"its front rises over the wall top to the copings' bed at the apex ({under:.3f} m)")
    top = under + g["coping"]["height_m"]
    band = built.prims["band"].pos
    check(abs(max(q[1] for q in band if abs(q[0] - xc) < 1e-9 and q[1] < top + 0.01) - top) < 1e-6
          and abs(meta["gable_top_m"] - top) < 1e-4, f"its copings meet at the apex ({top:.3f} m)")
    check(any(abs(q[2] - (p + g["coping"]["proud_m"])) < 1e-9 and abs(q[1] - top) < 1e-6 for q in band),
          "proud of the face")
    y_k = y_e + g["upstand_m"] + g["coping"]["height_m"]
    check(abs(meta["kneeler_m"] - y_k) < 1e-4, f"they spring from the kneelers' tops ({y_k:.3f} m)")
    pn, fn = g["pinnacle"], g["finial"]
    check(abs(meta["pinnacle_top_m"] - (y_k + pn["shaft_m"] + pn["cap_m"])) < 1e-4
          and abs(max(q[1] for q in band if q[0] < xa) - meta["pinnacle_top_m"]) < 1e-6,
          f"a pinnacle stands on each kneeler (to {meta['pinnacle_top_m']} m)")
    check(abs(max(q[1] for q in band) - (top + fn["shaft_m"] + fn["cap_m"])) < 1e-6,
          f"and the finial on the apex (to {meta['finial_top_m']} m)")

    # the eaves: none on the front, the returns' stopped on its plane
    soffit = built.prims["soffit"].pos
    check(max(q[2] for q in soffit) <= p + 1e-9 and max(q[2] for q in built.prims["fascia"].pos) <= p + 1e-9,
          "the returns' eaves stop on the front's plane")
    check(not any(xl + 0.01 < q[0] < xr - 0.01 for q in soffit), "and the front has none")
    knee = [q for q in band if q[0] < xl - 1e-6]
    check(min(q[0] for q in knee) < min(q[0] for q in soffit) and max(q[2] for q in knee) > p
          and min(q[1] for q in knee) <= y_top + 1e-9, "the kneelers cover the returns' eaves")

    # every other roof as before: a hip on the same pavilion keeps its eaves round the front
    hip = copy.deepcopy(v)
    hip["roof"] = {"kind": "hip", "pitch": 1.6, "covering": rf["covering"]}
    hb = K8.build_variant(hip, board=False)
    check(max(q[2] for q in hb.prims["fascia"].pos) > p and "band" in hb.prims,
          "a hip on the same plan keeps its eaves round the front")
    for kv in K8.load()["variants"]:
        K8.build_variant(kv, board=False)
    check(True, "the kit's own variants all build")

    # refusals
    bad = copy.deepcopy(v)
    bad["kind"] = "bay"
    refused(bad, "a gable on a bay", "a gable stands on a projection's square plan")
    bad = copy.deepcopy(v)
    bad["plan"]["points"][2][1] = p + 0.2
    refused(bad, "a gable on a skewed front", "a gable stands on a projection's square plan")
    bad = copy.deepcopy(v)
    bad["roof"]["finial"] = True
    refused(bad, "a copper finial on a stone gable", "its finial is its own stone one")
    bad = copy.deepcopy(v)
    bad["roof"]["pitch"] = 0.6
    refused(bad, "a gable too flat to be coped", "a coped gable rises 1.0-3.0 m")
    bad = copy.deepcopy(v)
    bad["roof"]["gable"]["coping"]["width_m"] = 0.8
    refused(bad, "a coping deeper than the projection", "the coping's back")
    bad = copy.deepcopy(v)
    # wide enough on any face to leave under a metre between them (T-3015 widened 1801's to 4.15 m)
    bad["roof"]["gable"]["kneeler"]["width_m"] = (xr - xl) / 2 - 0.3
    refused(bad, "kneelers that leave no gable", "leave the gable a metre across")
    bad = copy.deepcopy(v)
    bad["roof"]["gable"]["kneeler"]["out_m"] = 0.0
    refused(bad, "a kneeler whose side is the fascia's", "so its side is not the fascia's")
    bad = copy.deepcopy(v)
    bad["roof"]["gable"]["pinnacle"]["width_m"] = 0.6
    refused(bad, "a pinnacle wider than its kneeler", "a pinnacle stands inside its kneeler")

    print(f"\n{'FAIL' if failures else 'ok'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
