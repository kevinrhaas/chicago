#!/usr/bin/env python3
"""The West Division's north-south module, derived, and the owner's shift report answered (T-0444).

The owner reported on 2026-08-31, from the dev preview against the Thompson plat
sheet: *"where you have what you say is canal, is where I am fairly sure where
Clinton should be, the Canal street is missing ... I think you have Clinton where
maybe Des Plaines is from the Thompson plat."*

This project does not move a street on a reading of a screenshot, so the report is
answered with arithmetic over committed files and nothing else. Three things are
computed here, and they are deliberately separated by how much they depend on:

1. **The spacing finding, which depends on no anchor at all.** A distance between
   two centrelines is the same wherever the grid is pinned, so `clinton -> canal`
   can be compared with the plat's own module without settling where either line
   belongs. It is short, and that is a finding rather than a question.

2. **The derived centrelines, which need exactly one anchor.** The river breaks the
   module between Market Street and West Water Street, so no arithmetic can place
   the West Division without one number from outside it. The anchor taken here is
   the committed west bank of the South Branch — `data/terrain/epochs/
   e1834_harbor_cut/river.geojson`, the feature named for the West Division shore,
   traced from Wright 1834 and graded `inferred` there. Its grade is inherited: no
   line derived below is better attested than the bank it is stepped from.

3. **The owner's shift, answered as a test rather than an opinion.** If the line
   committed as `canal` were really Clinton, then Canal and West Water lie one and
   two modules EAST of it. West Water cannot lie east of the river — it is the
   West Division's riverfront street — and that ceiling puts an upper bound on the
   module the shift would need. Comparing that bound with the plat's own module is
   what decides the report, and it decides it without appeal to any judgement.

WHAT IS NOT DONE HERE, AND THE TICKET IS EXPLICIT ABOUT IT: nothing moves. Moving
lines is T-0445. This module writes numbers and a memo.

WHAT IS STILL OWED (T-0444 acceptance 1). The West Division's lot dimensions and
block lot-counts are supposed to be read OFF THE PLAT SHEET and committed as data.
No plat sheet is committed to this repository — `chicago/reference/images/chicago/`
holds no survey — and this project's own rule refuses to trace the 1834 sheets at
all (`data/traces/vectors/thompson_lots.json`: "never traced off the 1834 sheets,
whose 3.7-4.5% anisotropic stretch would arrive as 4% of wobble in every block
face"). A search of archive.org for the Thompson plat on 2026-09-03 returned
nothing usable; that negative is recorded rather than passed over. So the lot
DEPTH used below is the 180 ft the committed South Division reproduces, and the
two-lots-across block count is the owner's own reading carried in T-0443 — both
are stated as the inferences they are, and neither is dressed up as a plat
reading. Acceptance 1 is therefore NOT met by this module; T-0444 stays open on it.

    tools/measure_west_division_module.py              → print the derivation
    tools/measure_west_division_module.py --self-test  → the assertions
"""
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FT = 0.3048

# The plat legend's own figures, as data/traces/vectors/thompson_lots.json carries
# them: 80 ft streets, 18 ft alleys. The lot depth is NOT from the legend — see the
# docstring's note on acceptance 1.
STREET_FT = 80.0
ALLEY_FT = 18.0
LOT_DEPTH_FT = 180.0

# The West Division's blocks are drawn two lots ACROSS by five down, so a
# north-south street module is a block DEPTH plus a street: two lot depths, the
# alley between them, and the street.
MODULE_FT = 2 * LOT_DEPTH_FT + ALLEY_FT + STREET_FT      # 458 ft

# East to west, the order the plat carries them in.
WEST_STREETS = ["west_water", "canal", "clinton", "jefferson", "des_plaines"]

# The tiers the bank is sampled at: the three South Division east-west streets that
# reach the water with a committed centreline. Kinzie is excluded deliberately — it
# meets the NORTH branch, not the South, and its bank easting is 128 m away.
BANK_TIERS = ["lake", "randolph", "washington"]


def load(rel):
    return json.loads((ROOT / rel).read_text())


def streets():
    return {s["id"]: s for s in load("data/streets/1835.json")["streets"]}


def mean_e(st):
    return statistics.fmean(p[0] for p in st["path_local_enu_m"])


def mean_n(st):
    return statistics.fmean(p[1] for p in st["path_local_enu_m"])


def west_bank():
    """The committed west bank of the South Branch, in local ENU metres."""
    datum = load("data/datum.json")
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    geo = load("data/terrain/epochs/e1834_harbor_cut/river.geojson")
    for f in geo["features"]:
        if "West Division shore" in (f["properties"].get("name") or ""):
            return [(e - oe, n - on) for e, n in f["geometry"]["coordinates"]]
    raise SystemExit("the West Division shore feature is not in the river geojson")


def bank_e_at(bank, northing):
    """Where the bank line crosses a given northing, by linear interpolation.

    The last crossing wins: the polyline runs up past Wolf Point and doubles back
    along the North Branch, so a southern northing can be met twice and the
    SOUTH BRANCH crossing is the later one in file order.
    """
    hit = None
    for (e1, n1), (e2, n2) in zip(bank, bank[1:]):
        lo, hi = sorted((n1, n2))
        if lo - 1e-9 <= northing <= hi + 1e-9 and abs(n2 - n1) > 1e-9:
            hit = e1 + (northing - n1) / (n2 - n1) * (e2 - e1)
    return hit


def derive():
    st = streets()
    bank = west_bank()

    samples = {t: bank_e_at(bank, mean_n(st[t])) for t in BANK_TIERS}
    anchor_bank = statistics.fmean(samples.values())

    # West Water is the riverfront street: its EAST kerb on the bank puts its
    # centreline half a street width west. That is the easternmost the street can
    # be, which is what makes it the right ceiling for the shift test below.
    west_water = anchor_bank - (STREET_FT / 2) * FT
    module_m = MODULE_FT * FT
    derived = {n: round(west_water - i * module_m, 2)
               for i, n in enumerate(WEST_STREETS)}

    canal_e, clinton_e = mean_e(st["canal"]), mean_e(st["clinton"])
    held_spacing = abs(canal_e - clinton_e)

    # The shift test. If the committed `canal` is Clinton, West Water sits two
    # modules east of it and may not pass the bank.
    max_module = (west_water - canal_e) / 2

    return {
        "bank_samples": {k: round(v, 3) for k, v in samples.items()},
        "anchor_bank_e": round(anchor_bank, 3),
        "module_ft": MODULE_FT,
        "module_m": round(module_m, 3),
        "derived": derived,
        "held": {"canal": round(canal_e, 2), "clinton": round(clinton_e, 2)},
        "held_spacing_m": round(held_spacing, 2),
        "held_spacing_ft": round(held_spacing / FT, 1),
        "short_by_m": round(module_m - held_spacing, 2),
        "short_by_ft": round((module_m - held_spacing) / FT, 1),
        "shift_max_module_m": round(max_module, 2),
        "shift_max_module_ft": round(max_module / FT, 1),
        "canal_offset_m": round(canal_e - derived["canal"], 2),
        "clinton_offset_m": round(clinton_e - derived["clinton"], 2),
    }


def report(d):
    print("== the plat's own module, West Division")
    print(f"   2 x {LOT_DEPTH_FT:.0f} ft lot depth + {ALLEY_FT:.0f} ft alley + "
          f"{STREET_FT:.0f} ft street = {d['module_ft']:.0f} ft = {d['module_m']} m")
    print()
    print("== 1. the spacing finding — no anchor, so no question")
    print(f"   committed clinton -> canal  {d['held_spacing_m']} m = {d['held_spacing_ft']} ft")
    print(f"   the plat's module           {d['module_m']} m = {d['module_ft']:.0f} ft")
    print(f"   SHORT BY {d['short_by_m']} m = {d['short_by_ft']} ft — half a lot depth")
    print()
    print("== 2. the anchor: the committed west bank of the South Branch")
    for k, v in d["bank_samples"].items():
        print(f"   at {k:11s} bank east {v:8.3f} m")
    print(f"   mean {d['anchor_bank_e']} m, grade inherited: inferred (Wright 1834)")
    print()
    print("== the five centrelines that follow")
    for n in WEST_STREETS:
        held = d["held"].get(n)
        note = "" if held is None else f"   committed {held:9.2f}  delta {held - d['derived'][n]:+7.2f} m"
        print(f"   {n:12s} {d['derived'][n]:9.2f}{note}")
    print()
    print("== 3. the owner's shift report, tested")
    print(f"   if the committed `canal` were Clinton, West Water lies two modules east of it")
    print(f"   and may not cross the bank, so the module could be at most "
          f"{d['shift_max_module_m']} m = {d['shift_max_module_ft']} ft")
    print(f"   the plat's module is {d['module_ft']:.0f} ft, which is "
          f"{d['module_ft'] - d['shift_max_module_ft']:.0f} ft more than that ceiling allows")
    print("   => the labels are NOT swapped; see docs/RESEARCH/west_division_module.md")


def self_test():
    d = derive()
    fail = []

    def ck(cond, msg):
        if not cond:
            fail.append(msg)

    # The module is the plat's arithmetic and not a fitted number.
    ck(d["module_ft"] == 458, "the two-lot module must be 458 ft")
    ck(abs(d["module_m"] - 139.598) < 0.01, "458 ft must be 139.598 m")

    # The finding that needs no anchor: the held pair is short by most of a lot depth.
    ck(d["short_by_ft"] > 80, "the held clinton->canal spacing must be short by more "
                              "than 80 ft, or finding 1 has stopped being true")
    ck(d["short_by_ft"] < 100, "short by more than 100 ft would mean the module changed")

    # The anchor is a real reading off the committed bank, not a constant.
    ck(len(d["bank_samples"]) == 3, "three tiers must sample the bank")
    ck(all(v is not None for v in d["bank_samples"].values()),
       "every tier must meet the bank line — a None means the polyline moved")
    ck(-20 < d["anchor_bank_e"] < 20, "the west bank at the South Division tiers sits "
                                      "within 20 m of the datum origin's easting")

    # The shift test's ceiling has to actually bind, or the test says nothing.
    ck(d["shift_max_module_ft"] < d["module_ft"],
       "the shift's ceiling must be BELOW the plat module, or the owner's reading is "
       "not excluded and this memo's answer is wrong")
    ck(d["shift_max_module_ft"] < 2 * LOT_DEPTH_FT + STREET_FT,
       "the ceiling must also exclude a two-lot-deep block with no alley")

    # The derived order is east to west, strictly.
    es = [d["derived"][n] for n in WEST_STREETS]
    ck(all(a > b for a, b in zip(es, es[1:])), "the five streets must step west")

    # West Water may not be in the river.
    ck(d["derived"]["west_water"] < d["anchor_bank_e"],
       "West Water's centreline must lie west of the bank")

    if fail:
        for m in fail:
            print(f"  FAIL {m}")
        print(f"SELF-TEST FAIL — {len(fail)} case(s)")
        return 1
    print(f"SELF-TEST PASS — the West Division module, its anchor and the shift "
          f"ceiling ({10} cases)")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    report(derive())
