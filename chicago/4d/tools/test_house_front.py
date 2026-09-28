#!/usr/bin/env python3
"""H1's centre hall, held to the entry that requires it. (T-1686)

WHY THIS EXISTS. `plan` decides where a house's front door goes, and five anonymous
parcels each decided it separately, beside their form values. All five gave H1 —
"Larger one-and-a-half-story house", `required_variant: center_hall_one_and_half`,
variants "5 bays; center hall; kitchen ell; small porch" — the three-bay `hall_parlour`
front of a cottage, with the door off centre against the partition. Seven roofs stood on
it, three of them in the Randolph-Washington tier where the placement policy seats the
town's merchants and professionals.

Nothing failed. `validate()` was satisfied, the crosswalk was satisfied by everything it
bands, and `band_notes` correctly reported H1's `plan` as a value the specification
speaks to — while the value itself was the opposite of what it says.

So this holds three things the reading depends on:

1. **the reading is unambiguous** — exactly one family of the thirty-five names a centre
   hall, and exactly one states a bare bay count rather than a range, and it is the same
   family. A crosswalk edit that makes a second family say either fails here rather than
   silently widening `house_front`'s answer.
2. **the town stands on it** — every committed H1 record carries the plan and the bay
   count its own entry states, and `frame_dwelling` can build that plan.
3. **the rule is asked, not retyped** — all five parcels call `house_front`, and none of
   them assigns a plan or a bay count of its own beside the call. That is the fault
   `tools/roof_form.py` was written for, one attribute over.

And the fourth thing, which is the other half of the ticket: **H2's two refusals are
refusals and not omissions.** Its entry offers a hip and a Greek doorway. The hip is
refused by `frame_dwelling_params.ROOF_TYPES`, which carries gable and shed and says so
loudly; the Greek doorway is refused BY DATE, and the date stands on a committed record —
`data/exclusions.json` § `clarke_house`, the earliest Greek Revival house in Chicago,
built 1836, earliest scene 1837. A refusal whose evidence is only a comment is checked
here against the record that actually carries it.

    python3 tools/test_house_front.py
    python3 tools/test_house_front.py --self-test   # the assertions must fire
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

import house_front  # noqa: E402
from archetypes.frame_dwelling_params import PLANS, ROOF_TYPES  # noqa: E402

STRUCTURES = ROOT / "data" / "structures"
EXCLUSIONS = ROOT / "data" / "exclusions.json"

# The five parcels that author a dwelling's plan. Named rather than globbed: a new
# parcel is a deliberate addition and should arrive with its own line here.
PARCELS = (
    "generate_block_infill.py",
    "generate_inferred_infill.py",
    "generate_north_infill.py",
    "generate_west_infill.py",
    "generate_inferred_households.py",
)

FAILED: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK  ' if ok else 'FAIL'}: {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def committed(family: str) -> list[tuple[str, dict]]:
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if (rec.get("reconstruction") or {}).get("family") == family:
            out.append((rec["id"], rec))
    return out


def form_value(rec: dict, field: str):
    value = (rec["phases"][-1].get("form") or {}).get(field)
    return value.get("value") if isinstance(value, dict) else value


def main(break_it: bool = False) -> int:
    families = [f["id"] for f in json.loads(
        (ROOT / "data" / "reconstruction"
         / "1835_family_archetype_crosswalk.json").read_text(encoding="utf-8"))["families"]]

    # ---- 1. the reading is unambiguous -----------------------------------
    hall = [f for f in families if house_front.entry_names_centre_hall(f)]
    bays = [f for f in families if house_front.stated_bays(f) is not None]
    check("exactly one family's entry names a centre hall", hall == ["H1"], ", ".join(hall))
    check("exactly one family's entry states a bare bay count, and it is the same one",
          bays == hall == ["H1"], ", ".join(bays))
    check("the bare-bay pattern declines a range",
          house_front.stated_bays("D7") is None and house_front.stated_bays("D1") is None,
          'D7 is "3/5 bays" and D1 is "2/3 bays"')
    check("a family whose entry says nothing keeps the parcel's own default",
          house_front.plan_for("D4", "hall_parlour") == "hall_parlour"
          and house_front.bays_for("D7", 5) == 5)

    # ---- 2. the town stands on it ----------------------------------------
    check("frame_dwelling can build the plan the entry requires", "centre_passage" in PLANS)
    stated = 3 if break_it else house_front.stated_bays("H1")
    want_plan = "hall_parlour" if break_it else "centre_passage"
    h1 = committed("H1")
    check("every committed H1 record stands behind a centre hall",
          bool(h1) and all(form_value(r, "plan") == want_plan for _, r in h1),
          ", ".join(i for i, r in h1 if form_value(r, "plan") != want_plan) or f"{len(h1)} roofs")
    check("…and at the bay count its own entry states",
          bool(h1) and all(form_value(r, "bays") == stated for _, r in h1),
          ", ".join(i for i, r in h1 if form_value(r, "bays") != stated) or f"{stated} bays")

    # ---- 3. the rule is asked, not retyped -------------------------------
    for name in PARCELS:
        text = (ROOT / "tools" / name).read_text(encoding="utf-8")
        asks = "house_front" in text and "plan_for(" in text and "bays_for(" in text
        check(f"{name} asks house_front for the plan and the bay count", asks)

    # ---- 4. H2's two refusals are refusals, not omissions -----------------
    h2_roof = str(house_front._families().get("H2", {}).get("roof") or "").lower()
    check("H2's own roof line offers a hip", "hip" in h2_roof, h2_roof)
    check("…and the archetype refuses it rather than carrying it",
          "hip" not in ROOF_TYPES, "ROOF_TYPES is " + ", ".join(ROOF_TYPES))
    clarke = next((e for e in json.loads(EXCLUSIONS.read_text(encoding="utf-8"))["excluded"]
                   if e["id"] == "clarke_house"), None)
    check("the Greek doorway's refusal stands on a committed exclusion, not on a comment",
          clarke is not None and "1836" in str(clarke.get("reason")),
          (clarke or {}).get("reason", "clarke_house is not excluded"))
    check("…and that exclusion's earliest scene is after this one",
          clarke is not None and str(clarke.get("earliest_scene")) > "1835")
    note = house_front.mapping_note("H2")
    check("the refusal is on the record a visitor opens, not only in Python",
          "Greek doorway" in note and "hip" in note and "1836" in note)
    block_h = [(i, r) for i, r in committed("H1") + committed("H2")
               if i.startswith("recon_1835_blk_")]
    check("every H roof of the platted blocks carries its mapping note",
          bool(block_h) and all("T-1686" in str(r.get("research_note")) for _, r in block_h),
          f"{len(block_h)} roofs")

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"house front OK — {len(h1)} H1 roofs behind a centre hall at "
          f"{stated} bays, H2's hip and Greek doorway refused and recorded, "
          f"{len(PARCELS)} parcels asking one rule")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("SELF-TEST: H1 is read as a three-bay hall-parlour cottage again; "
              "the committed-record checks must fire.")
        rc = main(break_it=True)
        if rc == 0:
            print("SELF-TEST FAILED: the assertions passed on the cottage front.")
            sys.exit(1)
        print("self-test OK — the assertions fire when H1 loses its centre hall.")
        sys.exit(0)
    sys.exit(main())
