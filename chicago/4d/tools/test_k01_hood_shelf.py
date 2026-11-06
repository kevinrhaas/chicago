#!/usr/bin/env python3
"""T-1890: a hooded dormer's shelf may be SLATED, read as the hood's own flared eave.

1801 Prairie's three hooded dormers had their hoods standing on a pale stone shelf, so from the
street each dormer read as a stone slab with a dark notch over it. The Taylor print (c. 1895) and
HABS photographs 1 and 2 (1965) show no pale course at any hood's foot: the slate runs down to a
thin dark eave over the light's pale frame. This holds the kit and the record to that:

  * a hood may name `shelf`, "stone" (the default) or "slate"; anything else is refused;
  * a slated shelf's faces are all slated (role `cheek`, which the plan box slates), its
    geometry exactly the stone one's;
  * a hood without `shelf` builds exactly as before, its shelf in the dormer's stone;
  * 1801's three hoods carry slated shelves, and the street hood rises 1.8 m (the Taylor
    print puts its top about 0.33 m over the 1.5 m hood's).

    python3 tools/test_k01_hood_shelf.py
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


def shelf(kind):
    h = {"shelf_m": 0.12, "shelf_proud_m": 0.08, "rise_m": 1.5, "lean_m": 0.15, "taper_m": 0.3, "flare_m": 0.2}
    if kind:
        h["shelf"] = kind
    s, _ = K1.Assembly.dormer_hood(_Host(), {"hood": h}, k5, "z", 1, 0.0, -2.0, 0.0, 0.5, 10.0, 11.6)
    polys = s if isinstance(s, list) else [s]
    return polys


def geometry_checks():
    stone, slate, plain = shelf("stone"), shelf("slate"), shelf(None)
    roles = lambda ps: {pl.role for pl in ps}
    check(roles(plain) == roles(stone) and "dormer_face" in roles(plain) and "cheek" not in roles(plain),
          f"a hood without `shelf` keeps its stone shelf ({sorted(roles(plain))})")
    check("cheek" in roles(slate) and "dormer_face" not in roles(slate),
          f"a slated shelf's faces are all slated ({sorted(roles(slate))})")
    pts = lambda ps: sorted(tuple(round(c, 9) for c in q) for pl in ps for q in pl.v)
    check(pts(slate) == pts(stone), "its geometry exactly the stone shelf's")


def record_checks():
    st, phase = record()
    # T-1890 (2026-11-06): the hooded three; the flat-capped wall dormer beside them has no hood
    ds = [d for d in KP.from_phase(phase, st).mansard["dormers"] if d["head"] == "hood"]
    check([d["hood"].get("shelf") for d in ds] == ["slate"] * 3, "1801's three hoods stand on slated shelves")
    check([d["hood"]["rise_m"] for d in ds] == [1.8, 1.8, 2.2], "the street hood rises 1.8 m (Taylor print)")
    st, phase = record()
    phase["form"]["mansard"]["value"]["dormers"][0]["hood"]["shelf"] = "brick"
    try:
        KP.from_phase(phase, st)
        check(False, "a brick shelf: refused")
    except KP.ParamError as e:
        check(True, f"a brick shelf: refused ({str(e)[:70]}...)")


def main() -> int:
    geometry_checks()
    record_checks()
    if failures:
        print(f"test_k01_hood_shelf: {len(failures)} failed")
        return 1
    print("test_k01_hood_shelf: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
