#!/usr/bin/env python3
"""T-1890: a K08 cap's finial may be TURNED over a crocketed collar, in a sheet metal of its own,
and a hooded dormer's face may be SLATED round a pale frame.

1801 Prairie's round tower, read off the Taylor print, carries a turned and knobbed pinnacle
over a crocketed collar at its cone's apex, pale against the slate; its hooded dormers' faces
are slate with a pale frame round each light (the Taylor print, and HABS photograph 1 for the
south one). The kit laid a plain spike in the cap's slate, and the dormers' faces in stone. This
holds the kit and the record to what the ticket says:

  * a cap's finial may name `form: turned`, a `collar_m` 0.2-0.8 m out on a cone only, and a
    `fabric` from FINIAL_FABRICS; a spike's collar, a collar on a pyramid, an unknown form or
    fabric are refused;
  * 1801's tower builds its turned finial to 20.02 m over a collar 0.45 m out, ringed with
    crockets, every face of it the `finial` role, and the plain spike is unchanged;
  * a hooded dormer's face may be `slate` with a `frame_m` 0.05 m wide up to 0.05 m short of its
    surround; a frame on a stone face is refused; 1801's three dormers are slated and framed.

    python3 tools/test_k08_turned_finial.py
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


def entry(phase, bid):
    return next(b for b in phase["form"]["bays"]["value"] if b["id"] == bid)


def resolved(bid):
    st, phase = record()
    return next(b for b in KP.from_phase(phase, st).bays if b["id"] == bid)


def built(v):
    return K8.Bay(copy.deepcopy(v), K8.load(), "full").build(board=False)


def tower_checks():
    b = resolved("tower")
    f = b["variant"]["overrides"]["finial"]
    check(f == {"height_m": 2.9, "radius_m": 0.14, "collar_m": 0.45, "form": "turned"},
          f"the tower's finial is turned, 2.9 m over a collar 0.45 m out ({f})")
    check(b.get("finial_fabric") == "zinc_sheet" and KP.FINIAL_FABRICS["zinc_sheet"] == "k04_zinc_sheet",
          f"and laid in zinc sheet, not the cap's slate ({b.get('finial_fabric')})")
    bay = built(b["variant"])
    m = bay.meta["finial"]
    check(m["form"] == "turned" and abs(m["top_m"] - 20.02) < 0.01, f"its tip at 20.02 m, on the cone T-1890 raised to both pictures ({m})")
    check(m.get("collar_m") == 0.45 and m.get("crockets") == K8.Bay.CROCKETS * len(K8.Bay.CROCKET_TIERS),
          f"its collar ringed with {m.get('crockets')} crockets")
    apex = bay.meta["roof"]["apex"]
    ys = [p[1] for p in bay.prims["finial"].pos]
    check(min(ys) < apex[1] - 0.45 * bay.meta["roof"]["pitch"] + 0.01 and abs(max(ys) - m["top_m"]) < 1e-6,
          f"the collar reaches down the cone to its rim and the turning up to the tip ({min(ys):.2f}-{max(ys):.2f} m)")
    # the plain spike is the kit's, untouched
    v = copy.deepcopy(b["variant"])
    v["overrides"]["finial"] = {"height_m": 2.6, "radius_m": 0.14}
    s = built(v).meta["finial"]
    check(set(s) == {"top_m"} and abs(s["top_m"] - (apex[1] + 2.6)) < 1e-6, f"a plain spike is the kit's ({s})")


def tower_refusals():
    for why, mut in (("an unknown form", lambda f: f.update(form="urn")),
                     ("a spike's collar", lambda f: f.update(form="spike")),
                     ("a collar 1.0 m out", lambda f: f.update(collar_m=1.0)),
                     ("an unknown fabric", lambda f: f.update(fabric="gold_leaf")),
                     ("an unknown key", lambda f: f.update(crockets=12))):
        st, phase = record()
        mut(entry(phase, "tower")["finial"])
        try:
            KP.from_phase(phase, st)
            check(False, f"{why}: refused")
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")


def dormer_checks():
    st, phase = record()
    p = KP.from_phase(phase, st)
    ds = p.mansard["dormers"]
    check(len(ds) == 3 and all(d["hood"].get("face") == "slate" and d["hood"].get("frame_m") == 0.1 for d in ds),
          "1801's three hooded dormers are slated, each light in a 0.1 m frame")
    for why, mut in (("a frame on a stone face", lambda h: (h.pop("face"))),
                     ("a frame as wide as its surround", lambda h: h.update(frame_m=0.2)),
                     ("a face of brick", lambda h: h.update(face="brick"))):
        st, phase = record()
        mut(phase["form"]["mansard"]["value"]["dormers"][0]["hood"])
        try:
            KP.from_phase(phase, st)
            check(False, f"{why}: refused")
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:70]}...)")


def main() -> int:
    tower_checks()
    tower_refusals()
    dormer_checks()
    if failures:
        print(f"test_k08_turned_finial: {len(failures)} failed")
        return 1
    print("test_k08_turned_finial: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
