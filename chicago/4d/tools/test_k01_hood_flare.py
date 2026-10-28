#!/usr/bin/env python3
"""T-1890: a hooded dormer's hood may FLARE at its foot.

1801 Prairie's three hooded dormers stand their hoods wider than the faces under them at the
foot and out in front of them, sweeping in to a narrow top: HABS photograph 1 shows the south
hood's foot about a third wider than its face, HABS photograph 2 and the Taylor print the other
two broad at the foot and standing out of the slate there. The kit's hood rose straight from the
face's own width and front. This holds the kit and the record to what the ticket says:

  * a hood may name `flare_m`, 0.05-0.3 m; outside that it is refused;
  * a flared hood's foot and shelf stand `flare_m` wider each side and `flare_m` further out,
    its top where the unflared hood's is, and the plan box that slates its cheeks spans it;
  * a hood without `flare_m` builds exactly as before;
  * 1801's three dormers flare 0.2 m, the south one's top eased to taper 0.17 (HABS 1).

    python3 tools/test_k01_hood_flare.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k05_roofs as k5  # noqa: E402

SID = "kimball_house_1801_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


class _Host:
    """Just what Assembly.dormer_hood reads off its instance."""
    HOOD_LIP_M = K1.Assembly.HOOD_LIP_M
    HOOD_BED_M = K1.Assembly.HOOD_BED_M
    HOOD_BACK_M = K1.Assembly.HOOD_BACK_M


def hood(flare):
    """One street-face hood (out along +z), face 1.0 m wide, its front at z 0, back at z -2."""
    h = {"shelf_m": 0.12, "shelf_proud_m": 0.08, "rise_m": 1.5, "lean_m": 0.15, "taper_m": 0.3}
    if flare:
        h["flare_m"] = flare
    host = _Host()
    shelf, body = K1.Assembly.dormer_hood(host, {"hood": h}, k5, "z", 1, 0.0, -2.0, 0.0, 0.5, 10.0, 11.6)
    pts = lambda ps: [q for pl in (ps if isinstance(ps, list) else [ps]) for q in getattr(pl, "v", ())]
    return pts(shelf), pts(body), host.gable_dormer_boxes[-1]


def geometry_checks():
    s0, b0, box0 = hood(0.0)
    s1, b1, box1 = hood(0.2)
    xs = lambda ps, lo, hi: [q[0] for q in ps if lo <= q[1] <= hi]
    zs = lambda ps, lo, hi: [q[2] for q in ps if lo <= q[1] <= hi]
    foot0, foot1 = max(xs(b0, 10.0, 10.2)), max(xs(b1, 10.0, 10.2))
    top0, top1 = max(xs(b0, 11.5, 11.7)), max(xs(b1, 11.5, 11.7))
    check(abs(foot0 - 0.5) < 1e-9 and abs(foot1 - 0.7) < 1e-9,
          f"the hood's foot stands 0.2 m wider each side ({foot0:.2f} -> {foot1:.2f} m)")
    check(abs(top0 - top1) < 1e-9 and abs(top1 - 0.2) < 1e-9, f"and its top stays the taper's ({top1:.2f} m)")
    check(abs(max(zs(b1, 10.0, 10.2)) - 0.2) < 1e-9 and abs(max(zs(b0, 10.0, 10.2))) < 1e-9,
          f"its foot's front 0.2 m out of the face ({max(zs(b1, 10.0, 10.2)):.2f} m)")
    check(abs(max(q[0] for q in s1) - max(q[0] for q in s0) - 0.2) < 1e-9
          and abs(max(q[2] for q in s1) - max(q[2] for q in s0) - 0.2) < 1e-9,
          "its shelf wider and further out with it")
    check(box1[1] - box1[0] - (box0[1] - box0[0]) > 0.39 and box1[3] > box0[3],
          f"the slating box spans the flared foot ({box0} -> {box1})")


def record_checks():
    st, phase = record()
    ds = KP.from_phase(phase, st).mansard["dormers"]
    check([d["hood"].get("flare_m") for d in ds] == [0.2, 0.2, 0.2], "1801's three hoods flare 0.2 m")
    check([d["hood"]["taper_m"] for d in ds] == [0.3, 0.3, 0.17], "the south hood's top eased to taper 0.17 (HABS 1)")
    for why, fl in (("a 0.02 m flare", 0.02), ("a 0.5 m flare", 0.5)):
        st, phase = record()
        phase["form"]["mansard"]["value"]["dormers"][0]["hood"]["flare_m"] = fl
        try:
            KP.from_phase(phase, st)
            check(False, f"{why}: refused")
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")


def main() -> int:
    geometry_checks()
    record_checks()
    if failures:
        print(f"test_k01_hood_flare: {len(failures)} failed")
        return 1
    print("test_k01_hood_flare: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
