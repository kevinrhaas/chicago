#!/usr/bin/env python3
"""T-3634: 2017 Prairie's gable as Chicagology's photograph shows it.

The photograph draws the south projection's steep gable standing on a moulded cornice with a
row of dentils across its foot, deep bargeboards under both rakes running down to that cornice
at the projection's corners, and a small triangle of diamond lattice in its peak. So K08's
coped gable takes three new parts:

  * `foot_cornice` {height_m, proud_m, dentils {width_m, drop_m, spacing_m, out_m}, fillet}:
    a shelf under the wall top from kneeler to kneeler, dentils under it across the front, a
    fillet at their foot; refused shallower than the copings' proud, with dentils past the
    shelf, or deeper than the windowless top storey it hangs in;
  * `bargeboards` {depth_m, proud_m}: a board under each coping's bed; refused prouder than
    the coping lets it be, and the gable's lights must clear its foot;
  * `ventilator` {height_m, gap_m, proud_m, bar_m, cell_m}: a latticed triangle under the
    apex; refused when it would reach down onto the lights.

Every one is opt-in, so a gable naming none builds as it did (the K01 family's other meshes
rebuild byte-identical; validate.py --stale holds that).

    python3 tools/test_k08_gable_dress.py
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

SID = "house_2017_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())

# catch the bay's own meta as K01 builds it
seen = {}
_orig = K8.Bay._gable


def _spy(self, world, y_top, y_e, ov):
    out = _orig(self, world, y_top, y_e, ov)
    seen[self.v["id"]] = {"roof": dict(self.meta["roof"]), "y_top": y_top, "prims": set(self.prims) | set(world.prims)}
    return out


K8.Bay._gable = _spy


def build(edit=None):
    r = copy.deepcopy(st)
    if edit:
        edit(r["phases"][0]["form"]["bays"]["value"][0]["roof"]["gable"])
    seen.clear()
    K1.build(KP.from_phase(r["phases"][0], r), SID)
    return next(iter(seen.values()))


def refused(edit, why, needle):
    try:
        build(edit)
    except (ValueError, KP.ParamError) as e:
        check(needle in str(e), f"refused: {why} ({str(e)[:140]})")
        return
    check(False, f"refused: {why} (it was accepted)")


m = build()
r = m["roof"]
fc = r.get("foot_cornice", {})
check(fc.get("dentils") == 21 and fc.get("shelf_m") == [8.8, 9.0] and fc.get("fillet_m") == [8.52, 8.6],
      f"2017's gable stands on a shelf over 21 dentils and a fillet: {fc}")
check(r.get("bargeboards") == {"depth_m": 0.27, "proud_m": 0.1}, f"...bargeboards under both rakes: {r.get('bargeboards')}")
vt = r.get("ventilator", {})
check(vt.get("bars", 0) >= 10 and abs(vt["y_m"][1] - vt["y_m"][0] - 0.55) < 1e-6,
      f"...a 0.55 m latticed ventilator in its peak: {vt}")
check(abs(r["gable_top_m"] - 12.2) < 0.01, f"...its apex at the photograph's 12.2 m: {r['gable_top_m']}")
check(vt.get("y_m", [0, 99])[1] < r["ridge_m"] + 0.15 - 0.27, f"the ventilator stands under the bargeboards' foot: {vt}")
check("backing" in m["prims"], "the ventilator's field is dark behind its lattice")

# opt-in: the same gable without the three parts builds none of them
bare = build(lambda g: [g.pop(k) for k in ("foot_cornice", "bargeboards", "ventilator")])["roof"]
check(not ({"foot_cornice", "bargeboards", "ventilator"} & set(bare)), f"a gable naming none builds none: {bare}")

refused(lambda g: g["foot_cornice"].update(proud_m=0.1), "a shelf shallower than the copings' proud",
        "foot cornice 0.1-0.4 m high")
refused(lambda g: g["foot_cornice"]["dentils"].update(out_m=0.3), "dentils standing out past the shelf",
        "foot cornice 0.1-0.4 m high")
refused(lambda g: g["foot_cornice"].update(height_m=0.35), "a cornice deeper than the windowless top storey",
        "windowless top storey")
refused(lambda g: g["foot_cornice"].update(color="red"), "an unknown key", "foot cornice takes")
refused(lambda g: g["bargeboards"].update(proud_m=0.14), "bargeboards as proud as the copings",
        "inside the copings' proud")
refused(lambda g: g["bargeboards"].update(depth_m=0.45), "bargeboards hanging down onto the gable's lights",
        "and any bargeboards")
refused(lambda g: g["ventilator"].update(height_m=1.1), "a ventilator reaching down onto the lights",
        "0.3 m over the gable's lights")
refused(lambda g: g["ventilator"].update(cell_m=0.04), "a lattice finer than two bars a cell", "ventilator 0.2-1.2 m")

if failures:
    print(f"\n{len(failures)} FAILED")
    sys.exit(1)
print("\nall passed")
