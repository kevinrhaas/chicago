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
    shallow = b["variant"]
    # T-3047: 1801's pavilion is now shallow (0.1 m proud, its gable a parapet carried back past
    # the wall plane, below); the deep gable is held on the same pavilion stood 0.6 m proud
    # T-1890: 1801's gable now carries the slated cross roof behind it (held below); the
    # gable's own checks are made on the pavilion without it
    cross = copy.deepcopy(shallow)
    shallow = copy.deepcopy(shallow)
    shallow["roof"]["gable"].pop("behind", None)
    v = copy.deepcopy(shallow)
    v.pop("shallow", None)
    # T-1890: 1801's canted face stopped under its cornice is a shallow pavilion's; held below
    v["plan"].pop("chamfer_top_m", None)
    # T-3073: the deep gable is held square on the front; 1801's own inset is held below
    v["roof"]["gable"].pop("inset_m", None)
    for q in v["plan"]["points"][1:3]:
        q[1] = 0.6
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

    # T-3047: the shallow pavilion's gable, as 1801 stands it: no roof in front of the plane, the
    # parapet and kneelers carried back to the copings' back and closed under it over the wall top
    check(shallow.get("shallow") is True and max(q[1] for q in shallow["plan"]["points"]) < 0.3,
          "1801's pavilion stands shallow")
    sb = K8.build_variant(shallow, board=False)
    sp = shallow["plan"]["points"][1][1]
    zb = sp + g["coping"]["proud_m"] - g["coping"]["width_m"]
    sband = sb.prims["band"].pos
    check("roof" not in sb.prims and sb.meta["roof"]["planes"] == 0, "a shallow gable has no roof in front of the plane")
    # (over the wall top: under it a chamfer's bands run on behind the plane, T-3048)
    over = [q for q in sband if q[1] > sb.meta["wall_top_m"] + 0.005]
    check(abs(min(q[2] for q in over) - zb) < 1e-9, f"its parapet carried back to the copings' back ({zb:.2f} m)")
    sy = sb.meta["wall_top_m"]
    under_top = [q for q in sband if abs(q[1] - sy) < 1e-9]
    check(any(abs(q[0] - pts[1][0]) < 1e-9 and abs(q[2] - zb) < 1e-9 for q in under_top)
          and any(abs(q[0] - pts[2][0]) < 1e-9 and abs(q[2] - sp) < 1e-9 for q in under_top),
          "and closed under it over the wall top, back to front")
    check(sb.host_holes and all(h[3] <= sy for h in sb.host_holes),
          f"its {len(sb.host_holes)} window holes are its host's to open")
    bad = copy.deepcopy(shallow)
    bad["roof"]["gable"]["coping"]["width_m"] = 0.15
    refused(bad, "a shallow gable whose copings stop short of the plane", "on a shallow projection")

    # T-3073: 1801's gable stops short of the chamfer on the Taylor photograph: its corners
    # stand inset_m in from the front's, its middle, rakes and pinnacles with them, and its
    # kneelers still run out over the front's corners. T-3108 set 1801's own gable back on its
    # whole (narrowed) face, so the inset is held here at T-3073's 0.41 m on a copy of it
    shallow = copy.deepcopy(shallow)
    shallow["roof"]["gable"]["inset_m"] = [0.0, 0.41]
    sb = K8.build_variant(shallow, board=False)
    sband = sb.prims["band"].pos
    il, ir = shallow["roof"]["gable"]["inset_m"]
    sxl, sxr = shallow["plan"]["points"][1][0], shallow["plan"]["points"][2][0]
    gl, gr = sxl + il, sxr - ir
    sm = sb.meta["roof"]
    check(ir > 0 and abs(sm["apex"][0] - (gl + gr) / 2) < 1e-4,
          f"1801's gable stands {ir} m in from the chamfer, its middle at {sm['apex'][0]:.3f} m")
    kw = g["kneeler"]["width_m"]
    pw = g["pinnacle"]["width_m"]
    tops = [q for q in sband if abs(q[1] - sm["pinnacle_top_m"]) < 1e-6]
    check(tops and all(min(abs(q[0] - (gl + kw / 2)), abs(q[0] - (gr - kw / 2))) < pw / 2 + 1e-6 for q in tops),
          "its pinnacles stand over its own corners' kneelers")
    ov, ko = sb.meta["overhang_m"], g["kneeler"]["out_m"]
    knees = [q[0] for q in sband if abs(q[1] - sm["kneeler_m"]) < 1e-6]
    check(knees and abs(max(knees) - (sxr + ov + ko)) < 1e-6 and abs(min(knees) - (sxl - ov - ko)) < 1e-6
          and any(abs(x - (gr - kw)) < 1e-6 for x in knees),
          "and its kneelers still run out over the front's corners")
    square = copy.deepcopy(shallow)
    square["roof"]["gable"]["inset_m"] = [0.0, 0.0]
    bare = copy.deepcopy(shallow)
    bare["roof"]["gable"].pop("inset_m")
    a, b = K8.build_variant(square, board=False), K8.build_variant(bare, board=False)
    check(all(a.prims[k].pos == b.prims[k].pos for k in b.prims) and a.prims.keys() == b.prims.keys(),
          "an inset of nothing builds the square gable exactly")
    bad = copy.deepcopy(shallow)
    bad["roof"]["gable"]["inset_m"] = [0.0, 1.6]
    refused(bad, "a gable inset past 1.5 m (T-1890 widened the bound from a metre)", "stands its corners 0-1.5 m in")

    # T-1890: the cross roof behind 1801's gable (the Taylor photograph and HABS photograph 1): a
    # level ridge on the gable's middle under its copings, two slopes from the side walls' tops
    # run back from the parapet's back, slated cheeks under them and the end closed
    bh = cross["roof"]["gable"].get("behind")
    check(bool(bh), "1801's pavilion carries a roof behind its gable")
    if bh:
        cb = K8.build_variant(cross, board=False)
        cm = cb.meta["roof"]["behind"]
        rp = cb.prims["roof"].pos
        xl_, xc_, xr_ = cm["x_m"]
        ridge = [q for q in rp if abs(q[1] - bh["ridge_m"]) < 1e-9]
        check(ridge and all(abs(q[0] - xc_) < 1e-9 for q in ridge)
              and abs(min(q[2] for q in ridge) + bh["run_back_m"]) < 1e-9,
              f"its ridge level at {bh['ridge_m']} m on the gable's middle, run back {bh['run_back_m']} m")
        check(cb.meta["roof"]["planes"] == 0 and max(q[2] for q in rp) < 0.0,
              "nothing of it in front of the wall plane (the parapet is the gable's face)")
        check(bh["ridge_m"] <= cb.meta["roof"]["gable_top_m"] - 0.1 - 0.18,
              "its ridge under the copings' beds")
        feet = [bh["cheek_from_m"]] * 2 if not isinstance(bh["cheek_from_m"], list) else bh["cheek_from_m"]
        check(any(abs(q[0] - xl_) < 1e-9 and abs(q[1] - feet[0]) < 1e-9 for q in rp)
              and any(abs(q[0] - xr_) < 1e-9 and abs(q[1] - feet[1]) < 1e-9 for q in rp),
              f"its cheeks from {feet[0]} and {feet[1]} m")
        a_ = copy.deepcopy(cross)
        a_["roof"]["gable"]["behind"]["ridge_m"] = cb.meta["roof"]["gable_top_m"]
        refused(a_, "a roof behind the gable over its copings", "0.1 m or more under the copings")
        a_ = copy.deepcopy(cross)
        a_["roof"]["gable"]["behind"]["run_back_m"] = 0.2
        refused(a_, "a roof behind the gable that stops in its parapet", "runs back 0.5-8 m")
        a_ = copy.deepcopy(cross)
        a_["roof"]["gable"]["behind"]["cheek_from_m"] = 13.5
        refused(a_, "cheeks rising from under the wall top by less than a metre", "a metre or more under")
        a_ = copy.deepcopy(v)   # the deep gable held above, given the same roof behind it
        a_["roof"]["gable"]["behind"] = copy.deepcopy(bh)
        refused(a_, "a roof behind a deep projection's gable", "a shallow pavilion's")

    print(f"\n{'FAIL' if failures else 'ok'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
