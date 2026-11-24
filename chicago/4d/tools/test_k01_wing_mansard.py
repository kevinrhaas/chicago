#!/usr/bin/env python3
"""T-3713: a K01 rear wing roofed with the house's own mansard, held on 2115 Prairie's record.

The Armour photograph shows 2115's north flank's slated face carried on behind the main body,
with two more dormers in it, over the 1911 sheet's '3B' rear range. So a K01 wing may say
`roof: {"kind": "mansard"}`:

  * it stands on the main rear wall, its wall top at the main eave, under a house roofed with
    a mansard, and names nothing else about its roof (its eave, curb and deck are the house's);
  * k01_frontage.roof builds the same ring stack over the wing and joins it into the main
    one, so a side face flush with the main body's is one slated plane back to the wing's rear,
    and the main mansard's dormers on that face may stand on it, clear of its rear hip;
  * the wing builds no roof, deck or wing slate of its own;
  * every refusal says why.

    python3 tools/test_k01_wing_mansard.py
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

SID = "armour_house_2115_prairie"
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
        check(says in str(e), f"{why}: refused ({str(e)[:110]}...)")
        return
    check(False, f"{why}: refused")


def wing(form):
    return next(w for w in form["rear_wings"]["value"] if w["id"] == "rear_range")


def main() -> int:
    st, phase = load()
    p = KP.from_phase(phase, st)
    w = next(x for x in p.rear_wings if x["id"] == "rear_range")
    u0 = w["rect"][0]
    check(w["roof"] == {"kind": "mansard"}, "2115's rear range is roofed with the house's mansard")
    check(abs(w["top_m"] - p.eave_m) < 1e-6, f"its wall top {w['top_m']} m is the main eave {p.eave_m} m")
    behind = [d for d in p.mansard["dormers"] if d["face"] == "south" and d["along_m"] < 0.0]
    check(len(behind) == 2 and all(u0 < d["along_m"] for d in behind),
          f"two of the north flank's dormers stand on the face carried over the range ({[d['along_m'] for d in behind]})")

    refused(lambda f: wing(f)["roof"].__setitem__("overhang_m", 0.3), "a mansard wing naming its own eave",
            "names nothing but its kind")
    refused(lambda f: wing(f).__setitem__("storey_heights_m", [4.0, 4.0]) or
            wing(f).__setitem__("sash_by_storey", wing(f)["sash_by_storey"]), "a mansard wing under the main eave",
            "is not the main eave")
    refused(lambda f: f["mansard"]["value"]["dormers"][-1].__setitem__("along_m", -5.5),
            "a dormer past the range's rear hip", "clear of the hips")
    def flat_range(f):
        ds = f["mansard"]["value"]["dormers"]
        del ds[-2:]
        wing(f)["roof"] = {"kind": "flat", "overhang_m": 0.3, "fascia_m": 0.4, "covering": "painted_tin_sheet"}
        wing(f)["storey_heights_m"] = [4.0, 4.5, 3.0]
        ds.append(dict(ds[-1], along_m=-1.0))
    refused(flat_range, "a flank dormer behind the main body over a flat wing", "clear of the hips")

    a = K1.build(p, SID)
    check("wing_slate" not in a.prims, "the range lays no wing slate of its own")
    E = p.eave_m
    over = [q for name in ("slate_covering", "mansard_slate") if name in a.prims
            for q in a.prims[name].pos if q[0] < u0 + 1.5 and q[1] > E + 1.0]
    check(len(over) > 0, f"the house's slate runs on over the range's rear (u < {u0 + 1.5:.2f}), above the eave")
    flank = [q for name in ("slate_covering", "mansard_slate") if name in a.prims
             for q in a.prims[name].pos if abs(q[2] - 0.6) < 0.05 and q[0] < -1.0]
    check(len(flank) > 0, "its north flank's foot is the main roof's fascia line, carried on behind the main body")
    if failures:
        print(f"test_k01_wing_mansard: {len(failures)} failed")
        return 1
    print("test_k01_wing_mansard: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
