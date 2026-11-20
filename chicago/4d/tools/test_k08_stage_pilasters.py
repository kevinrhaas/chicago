"""T-3370: a K08 bay's pilasters may stand in some storeys alone, on a whole stage's ring, and
a K08 architrave may stand on colonnettes.

1936 Prairie's belvedere, in the Chicagology photograph, has a pilaster at each corner from its
balcony's floor to the frieze under its brackets, and each of its arched lights stands in a
frame on a slender column each side, carrying the arch's impost. The kit's pilasters ran every
storey of a bay, and its architrave had no columns, so neither was built. This holds the kit
to what the ticket says:

  * the record's tower carries pilasters at both ends of all four runs of its whole stage
    (eight shafts), in the belvedere's storey alone: none stands below that storey's floor
    line, and all of them reach the eaves;
  * its four belvedere lights are framed (four architraves), each frame on two colonnettes
    prouder than its band and standing past the band's outer edge;
  * pilasters naming no storey, a storey under a whole stage, an index out of range or out of
    order, and columns under no impost or no prouder than the band, are refused.

    python3 tools/test_k08_stage_pilasters.py
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

SID = "house_1918_prairie"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record():
    st = json.loads((ROOT / "data" / "structures" / f"{SID}.json").read_text())
    return st, st["phases"][-1]


def raw_tower(st):
    return next(b for b in st["phases"][-1]["form"]["bays"]["value"] if b["id"] == "tower")


def parsed_tower(st, phase):
    p = KP.from_phase(phase, st)
    return next(b["variant"] for b in p.bays if b["id"] == "tower")


def refused(edit, why):
    st, phase = record()
    st = copy.deepcopy(st)
    phase = st["phases"][-1]
    edit(raw_tower(st))
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(True, f"{why}: refused ({str(e)[:80]}...)")
        return
    check(False, f"{why}: refused")


def main() -> int:
    st, phase = record()
    v = parsed_tower(st, phase)
    check(v["pilasters"].get("storeys") == [4], "the record's tower names its belvedere's storey for its pilasters")
    bay = K8.Bay(v, K8.load(), "full").build(board=False)
    check(bay.meta.get("pilasters", {}).get("shafts") == 8,
          f"eight pilaster shafts, both ends of the whole stage's four runs ({bay.meta.get('pilasters')})")
    check(bay.meta.get("architraves") == 4, f"four framed belvedere lights ({bay.meta.get('architraves')})")
    levels = bay.meta["levels_m"]
    y_floor, y_top = levels[4], levels[5]
    band = list(bay.prims["band"].pos)
    lo = copy.deepcopy(v)
    lo.pop("pilasters")
    bare = K8.Bay(lo, K8.load(), "full").build(board=False)
    extra = len(bay.prims["band"].pos) - len(bare.prims["band"].pos)
    check(extra > 0, f"the pilasters add band pieces ({extra} vertices)")
    # what the pilasters add stands in the belvedere alone, from its floor line to its eaves
    key = lambda q: tuple(round(c, 4) for c in q)
    had = {key(q) for q in bare.prims["band"].pos}
    ys = [q[1] for q in bay.prims["band"].pos if key(q) not in had]
    check(bool(ys) and y_floor - 0.01 <= min(ys) and max(ys) <= y_top + 0.01,
          f"the pilasters stand between the belvedere's floor ({y_floor:.2f} m) and its eaves ({y_top:.2f} m): "
          f"{min(ys):.2f}-{max(ys):.2f} m" if ys else "the pilasters stand in the belvedere")
    # the colonnettes: with columns the frames carry more pieces than without
    nc = copy.deepcopy(v)
    for st_ in nc["storeys"]:
        for w in st_["windows"]:
            if w.get("architrave"):
                w["architrave"].pop("columns", None)
    plain = K8.Bay(nc, K8.load(), "full").build(board=False)
    check(len(bay.prims["band"].pos) > len(plain.prims["band"].pos),
          "the belvedere's frames stand on colonnettes (more band pieces than frames without them)")

    def set_storeys(sy):
        def f(t):
            t["pilasters"]["storeys"] = sy
        return f
    refused(set_storeys([]), "pilasters naming no storey")
    refused(set_storeys([2, 4]), "pilasters in a storey under the whole stage")
    refused(set_storeys([9]), "pilasters in a storey the tower has not")
    refused(set_storeys([4, 3]), "pilasters' storeys out of order")

    def no_impost(t):
        t["storeys"][4]["windows"][0]["architrave"].pop("impost_m")
    refused(no_impost, "colonnettes under no impost")

    def flush(t):
        t["storeys"][4]["windows"][0]["architrave"]["columns"]["proud_m"] = 0.07
    refused(flush, "colonnettes no prouder than the band")

    print(f"\n{'FAIL' if failures else 'ok'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
