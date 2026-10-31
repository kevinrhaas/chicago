#!/usr/bin/env python3
"""T-2900: the two kit pieces 1801 Prairie's east range needed, held on its record.

The 1911 sheet runs the Kimball house's east range from the 18th Street wall to v 18.3,
behind a gabled section only 6 m wide, and J. W. Taylor's c. 1895 photograph shows a small
round turret at the range's north-east corner with its eaves level with the range's. So:

  * a K01 wing may run past its host wall's ends when its record says `past_host`: it still
    stands on at least WING_HOST_MIN_M of that wall, past it it has a front wall of its own
    (drawn only there), its roof is cut only along the host so its eaves run round the
    front, and the front's lights stand clear inside the stretches past the host;
  * a K08 corner turret (`corner`) stands on a rear wing's wall at one of its ends: its ring
    within TURRET_CORNER_M of the end wall's plane and never past it, its wall top the
    wing's own, its centre allowed inside the wall, and its cone whole over the wing's roof
    with nothing closed behind it on the wall plane;
  * every refusal around both says why.

    python3 tools/test_k01_wing_past_host.py
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
from archetypes import k08_bays as K8  # noqa: E402

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def load():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


def refused(change, why, says):
    st, _ = load()
    st = copy.deepcopy(st)
    phase = st["phases"][-1]
    change(phase["form"])
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:100]}...)")
        return
    check(False, f"{why}: refused")


def wing(form, wid):
    return next(w for w in form["rear_wings"]["value"] if w["id"] == wid)


def turret(form):
    return next(b for b in form["bays"]["value"] if b["id"] == "turret")


def faces(pr, normal, test):
    """The area of a prim's triangles facing `normal` whose every vertex passes `test`."""
    area = 0.0
    for t in range(0, len(pr.idx), 3):
        tri = [pr.pos[i] for i in pr.idx[t:t + 3]]
        n = pr.nrm[pr.idx[t]]
        if sum(n[k] * normal[k] for k in range(3)) < 0.99 or not all(test(q) for q in tri):
            continue
        a, b, c = tri
        ab = [b[k] - a[k] for k in range(3)]
        ac = [c[k] - a[k] for k in range(3)]
        cr = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        area += math.sqrt(sum(x * x for x in cr)) / 2
    return area


def main() -> int:
    st, phase = load()
    p = KP.from_phase(phase, st)
    r2 = next(w for w in p.rear_wings if w["id"] == "r2")
    r3 = next(w for w in p.rear_wings if w["id"] == "r3")
    u0, u1, v0, v1 = r2["rect"]
    check(r2.get("past_host") == ((6.0, 18.3),) and r2["host_span_m"] == (0.0, 6.0),
          f"1801's east range stands on r3b's 6 m (the sheet's rectangle behind the gabled section) and runs past it to v 18.3 "
          f"(past {r2.get('past_host')}, on {r2['host_span_m']})")
    check("past_host" not in r3, "the gabled section, inside the main rear wall, runs past nothing")
    check(r2["roof"]["axis"] == "v", "the range's hip runs along it")

    # refusals: the wing piece
    refused(lambda f: wing(f, "r2").pop("past_host"), "a wing past its host that does not say so",
            "says past_host")
    refused(lambda f: wing(f, "r3").__setitem__("past_host", True), "past_host on a wing inside its host",
            "inside its host")
    refused(lambda f: wing(f, "r2").__setitem__("rect", [-17.9, -8.5, 5.5, 18.3]),
            "a wing standing on 0.5 m of its host wall", "under the 1.0 m a wing stands on")
    refused(lambda f: wing(f, "r2")["windows"].__setitem__("front", [4.0]), "a front light behind the host",
            "not 0.30 m clear inside")
    refused(lambda f: wing(f, "r3").setdefault("windows", {}).__setitem__("front", [3.0]), "a front on a wing with none",
            "has no front wall")

    # refusals: the corner turret
    refused(lambda f: turret(f).__setitem__("s_m", 1.3), "a turret's ring past the end wall's plane",
            "never past the end wall's plane")
    refused(lambda f: turret(f).__setitem__("s_m", 1.8), "a turret's ring 0.4 m inside its end",
            "stands 0-0.3 m inside it")
    refused(lambda f: turret(f).__setitem__("corner", "right"), "a turret at the wrong end",
            "inside its right end")
    refused(lambda f: turret(f)["storeys"][1].__setitem__("height_m", 4.1), "a turret whose eaves are not the wing's",
            "its eaves are the wing's own")
    refused(lambda f: turret(f).__setitem__("variant", "k08.tower.octagonal"), "an octagonal corner turret",
            "on a round tower only")
    refused(lambda f: turret(f).pop("corner"), "the turret without `corner` (T-2842's rule then holds)",
            "centre -0.3 m proud")
    refused(lambda f: f["bays"]["value"].append({**turret(f), "id": "t2", "wall": "k01.wall.side.south",
                                                 "s_m": 1.4}),
            "a corner turret on a main wall", "stands on a rear wing's wall")

    # T-3001: r3b, the rest of the sheet's rectangle, is slated too and its hip stands where r2's
    # would show past the cut, so it is decked flat here and the slate near r2's front is r2's own
    st2, phase2 = load()
    wing(phase2["form"], "r3b")["roof"] = {"kind": "flat", "overhang_m": 0.3, "fascia_m": 0.3,
                                           "covering": "painted_tin_sheet"}
    p = KP.from_phase(phase2, st2)
    a = K1.build(p, SID)
    stone = [a.prims[m] for m in ("rough_stone_trim", "brick", "limestone_trim") if m in a.prims]
    on_front = lambda lo, hi: lambda q: abs(q[0] - u1) < 2e-3 and lo - 1e-3 <= -q[2] <= hi + 1e-3
    past = sum(faces(pr, (1.0, 0.0, 0.0), on_front(6.0, v1)) for pr in stone)
    behind = sum(faces(pr, (1.0, 0.0, 0.0), on_front(0.0, 6.0 - 0.01)) for pr in stone)
    want = (v1 - 6.0) * r2["top_m"]
    check(past > 0.75 * want, f"its front is walled past the host ({past:.1f} m2 of about {want:.1f} less its lights)")
    check(behind == 0.0, f"and nothing along the host, which is the host's wall ({behind:.2f} m2)")
    slate = a.prims["wing_slate"]
    # T-1890: r2's eave is pulled in to 0.05 m so its box stays behind the frontispieces' faces
    eave = [q for q in slate.pos if q[0] > u1 + 0.02 and -q[2] > 6.5]
    check(bool(eave), f"its slate runs past its front where it runs past the host ({len(eave)} vertices)")
    cut = [q for q in slate.pos if u1 + 0.1 < q[0] < r3["rect"][0] - 0.1 and -q[2] < 5.9 and q[1] < 13.0]
    check(not cut, f"and is cut off at its front along the host ({len(cut)} vertices past it)")

    t = next(b for b in p.bays if b["id"] == "turret")
    v = t["variant"]
    check(t.get("corner") == "left" and v.get("cap_whole"), "the turret is a corner turret with a whole cap")
    whole = K8.build_variant(v, board=False)
    cut_v = copy.deepcopy(v)
    cut_v.pop("cap_whole")
    halved = K8.build_variant(cut_v, board=False)
    pos = whole.prims["roof"].pos
    cz = v["plan"]["centre_proud_m"]
    angles = {int(math.degrees(math.atan2(q[2] - cz, q[0])) % 360 // 30) % 12 for q in pos
              if math.hypot(q[0], q[2] - cz) > 0.5}
    check(len(angles) == 12, f"its cone stands whole round its axis ({len(angles)} of 12 sectors)")
    check(len(halved.prims["roof"].pos) < len(pos), "where an ordinary tower's, centre in the wall, is cut by it")
    check("roof_back" not in whole.prims, "and has no back closed on the wall plane")
    check(abs(whole.meta["wall_top_m"] - r2["top_m"]) < 1e-6,
          f"its wall top is the range's ({whole.meta['wall_top_m']} m)")
    # nothing of it closed on the range's wall plane over the wall head (T-2787's closure is a tower past the eave's)
    stone_bay = a.prims["bay_stone"]
    s0, s1 = t["span_m"]
    back = faces(stone_bay, (0.0, 0.0, -1.0), lambda q: abs(q[2] + 0.001) < 2e-3 and q[1] >= r2["top_m"] - 1e-3
                 and u0 + s0 - 0.5 <= q[0] <= u0 + s1 + 0.5)
    check(back == 0.0, f"the assembly closes nothing behind it over the wall head ({back:.2f} m2)")

    if failures:
        print(f"test_k01_wing_past_host: {len(failures)} failed")
        return 1
    print("test_k01_wing_past_host: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
