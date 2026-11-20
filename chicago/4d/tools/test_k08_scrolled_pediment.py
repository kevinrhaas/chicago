"""T-3370: a K08 architrave may carry a scrolled pediment.

1936 Prairie's dining range, in the Chicagology photograph, has a tall carved hood over each of
its paired lights, rising about 1.1-1.2 m over their heads: two arms curling in over the arch to
a carved middle. The kit's architrave rose only as far as its storey held, with a keystone, so
the pair hoods stood about 0.5 m short and the wrong shape. This holds the kit to what the
ticket says:

  * the record's dining range carries two pediments (its two pairs), each adding band pieces
    to its architrave, and the cap of each stands its rise_m over its lights' heads;
  * a pediment rises past its storey's floor band but never onto the light over it: the attic's
    frieze lights stay clear of the chamber pair's;
  * a pediment beside a keystone, no prouder than its band, with volutes narrower than its arms,
    too low to clear its arch, or rising into the storey over it past that storey's lowest sill,
    is refused; and one the bay finds standing on a light over it is refused by the build.

    python3 tools/test_k08_scrolled_pediment.py
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


def raw_range(st):
    return next(b for b in st["phases"][-1]["form"]["bays"]["value"] if b["id"] == "dining_range")


def parsed_range(st, phase):
    p = KP.from_phase(phase, st)
    return next(b["variant"] for b in p.bays if b["id"] == "dining_range")


def pairs(t):
    return [w for st_ in t["storeys"] for w in st_["windows"] if w["opening"] == "k06.opening.sash_paired_round"]


def refused(edit, why):
    st, _ = record()
    st = copy.deepcopy(st)
    edit(raw_range(st))
    try:
        KP.from_phase(st["phases"][-1], st)
    except KP.ParamError as e:
        check(True, f"{why}: refused ({str(e)[:80]}...)")
        return
    check(False, f"{why}: refused")


def main() -> int:
    st, phase = record()
    v = parsed_range(st, phase)
    ps = pairs(v)
    check(len(ps) == 2 and all("pediment" in w["architrave"] and "key_m" not in w["architrave"] for w in ps),
          "the record's dining range carries a scrolled pediment over both its pairs, in place of a keystone")
    for tier in ("full", "light"):
        bay = K8.Bay(v, K8.load(), tier).build(board=False)
        check(bay.meta.get("pediments") == 2, f"{tier} tier: two pediments built ({bay.meta.get('pediments')})")
        bare_v = copy.deepcopy(v)
        for w in pairs(bare_v):
            w["architrave"].pop("pediment")
        bare = K8.Bay(bare_v, K8.load(), tier).build(board=False)
        extra = len(bay.prims["band"].pos) - len(bare.prims["band"].pos)
        check(extra > 0, f"{tier} tier: the pediments add band pieces ({extra} vertices)")
        if tier != "full":
            continue
        # each cap's top stands rise_m over its pair's heads, in the band added over the pair
        levels = bay.meta["levels_m"]
        key = lambda q: tuple(round(c, 4) for c in q)
        had = {key(q) for q in bare.prims["band"].pos}
        new = [q for q in bay.prims["band"].pos if key(q) not in had]
        for k, w in ((0, ps[0]), (1, ps[1])):
            head = levels[k] + w["sill_m"] + w["clear_height_m"]
            top = head + w["architrave"]["pediment"]["rise_m"]
            got = max((q[1] for q in new if head < q[1] < top + 0.3), default=None)
            check(got is not None and abs(got - top) < 0.01,
                  f"storey {k}'s pair: its cap's top at {got if got is None else round(got, 3)} m, "
                  f"{w['architrave']['pediment']['rise_m']} m over its heads ({top:.3f} m)")
        # the chamber pair's hood rises past the floor band, yet stays under the attic's lights
        ch = max(q[1] for q in new if levels[1] < q[1] < levels[3])
        attic = levels[2] + min(w["sill_m"] for w in v["storeys"][2]["windows"])
        check(levels[2] < ch < attic - 0.1, f"the chamber pair's hood ({ch:.2f} m) rises past the floor band "
                                           f"({levels[2]:.2f} m), under the attic's lights ({attic:.2f} m)")

    def on_pairs(f):
        def g(t):
            for w in pairs(t):
                f(w["architrave"])
        return g
    refused(on_pairs(lambda a: a.__setitem__("key_m", [0.3, 0.4])), "a pediment beside a keystone")
    refused(on_pairs(lambda a: a["pediment"].__setitem__("proud_m", 0.08)), "a pediment no prouder than its band")
    refused(on_pairs(lambda a: a["pediment"].__setitem__("scroll_m", 0.05)), "volutes narrower than the arms")
    refused(on_pairs(lambda a: a["pediment"].__setitem__("rise_m", 0.7)), "a pediment too low to clear its arch")

    def into_attic(t):
        for w in t["storeys"][2]["windows"]:
            w["sill_m"] = 0.4
    refused(into_attic, "a pediment rising into the storey over it past its lowest sill")

    # the bay's own check: a light over a pediment, which the params let by, refused by the build
    tall = copy.deepcopy(v)
    tall["storeys"][2]["windows"][0]["sill_m"] = 0.3
    try:
        K8.Bay(tall, K8.load(), "full").build(board=False)
        check(False, "a pediment standing on the light over it: refused by the build")
    except ValueError as e:
        check("scrolled pediment" in str(e), f"a pediment standing on the light over it: refused by the build ({str(e)[:70]}...)")

    print(f"\n{'FAIL' if failures else 'ok'}: {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
