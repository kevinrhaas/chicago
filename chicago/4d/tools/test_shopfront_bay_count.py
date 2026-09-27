#!/usr/bin/env python3
"""The specification's shop-bay counts, read in the specification's own words.

WHY THIS EXISTS (T-1665). The reconstruction crosswalk asks C3, the narrow
two-storey store, for "2-3 shop bays". The archetype builds one. Read naively
that is a town missing a bay on every store it has, and worse than missing: the
crosswalk's top of range appeared to need 7.702 m of frontage where C3's own
authored band tops out at 6.706 m, so the family looked unsatisfiable by
construction. T-1665 was filed to settle which reading of that bay count is
meant BEFORE any geometry moved, and the answer moves none.

THE READING. Two counts wear the word "bay" and differ by one. This project's
`shopfront_bays` counts SHOW WINDOWS, with the door added separately by
`frame_storefront_params.shopfront_width_m`. The specification's bay is a FACADE
bay — one vertical division of the elevation, a window or the door. The witness
is in the crosswalk itself: D4 is "3/5 bays; center or side door" and H1 is
"5 bays; center hall". A centre door has to be centred in an odd count, and read
the door out of the count and both sentences contradict themselves. So the
specification counts the door, `facade_bays` is the mapping, and C3's "2-3 shop
bays" asks for `shopfront_bays` of 1 or 2.

WHAT THAT MAKES TRUE OF THE TOWN, measured here rather than remembered:

  * all seven committed C3 records carry 2 facade bays — INSIDE the crosswalk's
    2-3, at the bottom of it;
  * 3 facade bays needs 6.077 m of frontage and four of the seven have it, so the
    top of C3's range is reachable and was never impossible;
  * it is not taken, because `SHOPFRONT_MAX_FRACTION` refuses it: 4.877 m of
    opening on a 6.08-6.45 m front is 75.6% to 80.3% of the wall.

AND OF C4, WHICH IS WHAT T-1667 ASKED. The town's single C4, the wide two-storey
store, carried 2 facade bays against an authored 4-6, and T-1665 measured that as
the fraction rule refusing 69.8% of a 9.319 m front rather than a footprint that
could not hold the bays. It now STATES `shopfront_bays: 3` — 4 facade bays, the
bottom of its own band — because `SHOPFRONT_MAX_FRACTION` is the default for a
record that says nothing and the specification does not say nothing about C4.
The frontage affords exactly that and no more: 6.502 m of opening leaves 1.408 m
of plain wall at each end, 0.81 m more than `PIER_MIN_M` asks, and the next count
up needs 9.328 m against a 9.319 m front — short by 9 mm. So `SPEC_SHORTFALL`
below is EMPTY, and gate 4 is what keeps a stated count honest: it may move a
roof INTO its family's band and it may not carry one past the band or past the
frame.

AND THE DEFECT THAT FALLS OUT OF LOOKING. `default_shopfront_bays` has a `return
1` FLOOR below its 45% ceiling, and on a narrow gable front the floor is what
answers: on twenty of the committed shopfronted phases it puts 50.0% to 66.7% of
the frontage into opening, over a stated maximum of 45%, and said nothing about
it. `shopfront_bay_verdict` now says which branch answered, and gate 3 below
holds the override to fronts that genuinely cannot afford the next count up — so
the fraction rule cannot be quietly overruled on a front wide enough to keep it.
Gate 3 measures the fronts the RULE answers on; a record that states its own count
is not one of them and is counted separately, or the census reads a stated front as
a floor the rule chose.

    python3 tools/test_shopfront_bay_count.py
    python3 tools/test_shopfront_bay_count.py --self-test   # the assertions fire
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import frame_storefront_params as P  # noqa: E402

CROSSWALK = ROOT / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json"
STRUCTURES = ROOT / "data" / "structures"
ARCHETYPE = "frame_storefront"

FAILED: list[str] = []


def check(what: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {what}{f' — {detail}' if detail else ''}")
    if not ok:
        FAILED.append(what)


# A bay range as the crosswalk writes it: "2-3 shop bays", "4-6 bays", "2/3 bays",
# "5 bays", "5-8 bays". The separator is not standardised in the source and is not
# normalised here — reading it as written is the point of this file.
BAY_RANGE = re.compile(r"\b(\d+)\s*(?:-|/|to)\s*(\d+)\s+(?:shop\s+)?bays\b")
BAY_ONE = re.compile(r"\b(\d+)\s+(?:shop\s+)?bays\b")
# "center hall", and also "center or side door" — the qualifier sits between the
# word and the opening, and reading only the tight form lost D4, which is one of the
# two witnesses the whole argument rests on.
CENTRE_DOOR = re.compile(r"cent(?:er|re)\b(?:\s+or\s+\w+)?\s+(?:door|hall)")

# FAMILIES WHOSE BAY COUNT THIS ARCHETYPE'S SHOPFRONT ANSWERS. A dwelling's bay
# count is its window rhythm and is built by frame_dwelling's fenestration, which is
# a different rule with a different ticket; naming the storefront families here
# keeps this gate about the front it can actually measure.
SHOP_BAY_FAMILIES = ("C3", "C4")

# THE ONE FAMILY WHOSE COMMITTED RECORDS FALL OUTSIDE THEIR OWN RANGE, with the
# measurement and the ticket that owns it. Keyed by FAMILY and asserted as a
# SUPERSET, not an equality: a family that comes back into band is work being
# FINISHED, and a gate that goes red for that is a gate somebody deletes. A family
# that falls out of band and is NOT named here is the red this table is for.
#
# EMPTY SINCE T-1667, 2026-09-27, and kept rather than deleted: the one row it ever
# held — the single C4 at 2 facade bays against an authored 4-6 — was resolved by
# that record stating `shopfront_bays: 3`, and the table's job is not to list the
# shortfall but to make an UNANNOUNCED one red. An empty table is the strongest
# reading of it, not a dead one.
SPEC_SHORTFALL: dict[str, str] = {}


def family_bay_ranges(crosswalk: dict) -> dict[str, tuple[int, int]]:
    """Every family's authored bay range, read off the string that states it."""
    out: dict[str, tuple[int, int]] = {}
    for fam in crosswalk["families"]:
        text = " ".join(str(v) for v in fam.get("key_geometry_parameters", {}).values())
        m = BAY_RANGE.search(text)
        if m:
            out[fam["id"]] = (int(m.group(1)), int(m.group(2)))
            continue
        m = BAY_ONE.search(text)
        if m:
            out[fam["id"]] = (int(m.group(1)), int(m.group(1)))
    return out


def centre_door_witnesses(crosswalk: dict) -> list[tuple[str, tuple[int, int]]]:
    """The families that name a bay count AND a centre door or centre hall.

    These are the evidence for the reading. A centre door is centred in an odd
    number of bays, so their counts must be odd — under the door-INCLUSIVE reading.
    """
    out = []
    ranges = family_bay_ranges(crosswalk)
    for fam in crosswalk["families"]:
        text = " ".join(str(v) for v in fam.get("key_geometry_parameters", {}).values())
        if CENTRE_DOOR.search(text) and fam["id"] in ranges:
            out.append((fam["id"], ranges[fam["id"]]))
    return out


def storefront_phases() -> list[tuple[str, str, dict, object]]:
    """Every committed `frame_storefront` phase, with its family where it has one."""
    rows = []
    for path in sorted(STRUCTURES.glob("*.json")):
        rec = json.loads(path.read_text())
        if rec.get("archetype") != ARCHETYPE:
            continue
        phase = rec["phases"][-1]
        m = re.search(r"\b([CDFHTW]\d)\b", rec.get("name", ""))
        rows.append((rec["id"], m.group(1) if m else "", phase,
                     P.from_phase(phase, rec)))
    return rows


def main(break_it: str = "") -> int:
    crosswalk = json.loads(CROSSWALK.read_text())
    ranges = family_bay_ranges(crosswalk)
    witnesses = centre_door_witnesses(crosswalk)
    rows = storefront_phases()
    print(f"{len(rows)} committed {ARCHETYPE} phase(s); "
          f"{len(ranges)} family bay range(s) in the crosswalk\n")

    # 1. THE READING IS RE-DERIVED FROM THE SOURCE, NOT REMEMBERED. If the
    #    crosswalk ever stops carrying a witness, the argument for `facade_bays` has
    #    gone with it and this gate says so instead of carrying on quietly.
    if break_it == "reading":
        witnesses = [(f, (lo + 1, hi + 1)) for f, (lo, hi) in witnesses]
    check("the crosswalk still names a bay count beside a centre door",
          len(witnesses) >= 1, f"witnesses {[w[0] for w in witnesses]}")
    for fam, (lo, hi) in witnesses:
        check(f"{fam}'s centre-door bay counts are odd, so the door is one of them",
              lo % 2 == 1 and hi % 2 == 1, f"{lo}-{hi}")
    #    …and the door-EXCLUSIVE reading is refused by the same sentence: strip the
    #    door out and the counts become even, which no centre door sits in.
    check("the door-exclusive reading contradicts every witness it is tried on",
          all((lo - 1) % 2 == 0 and (hi - 1) % 2 == 0 for _, (lo, hi) in witnesses)
          and len(witnesses) >= 1,
          f"{len(witnesses)} witness(es)")

    # 2. THE MAPPING, AND WHAT IT MAKES OF THE TOWN. Every committed storefront in a
    #    family with an authored shop-bay range is in band, or its family is named in
    #    SPEC_SHORTFALL with its measurement.
    out_of_band: dict[str, list[str]] = {}
    in_band = 0
    for rid, fam, phase, p in rows:
        if fam not in SHOP_BAY_FAMILIES or fam not in ranges:
            continue
        lo, hi = ranges[fam]
        bays = P.facade_bays(p.shopfront_bays) if p.shopfront else 0
        if break_it == "band" and fam == "C3":
            bays = hi + 2
        if lo <= bays <= hi:
            in_band += 1
        else:
            out_of_band.setdefault(fam, []).append(f"{rid} {bays} bays vs {lo}-{hi}")
    check("every storefront out of its family's bay band has that family on the record",
          set(out_of_band) <= set(SPEC_SHORTFALL),
          f"unaccounted {sorted(set(out_of_band) - set(SPEC_SHORTFALL))}"
          if set(out_of_band) - set(SPEC_SHORTFALL) else f"{in_band} in band")
    for fam in sorted(out_of_band):
        print(f"        {fam}: " + "; ".join(out_of_band[fam]))
    for fam in sorted(set(SPEC_SHORTFALL) - set(out_of_band)):
        print(f"        {fam}: RESOLVED — back inside its band; the row may go")

    # 3. THE FLOOR DOES NOT OVERRULE THE FRACTION ON A FRONT THAT CAN KEEP IT. The
    #    `return 1` floor answers on the narrow gable fronts, and on twenty of them
    #    it answers ABOVE the 45% the same rule states. That is the honest answer
    #    there — a door and one 5 ft window is the least a shop front can be — but it
    #    must never be the answer on a front where the next count up WOULD have
    #    satisfied the fraction, because then the floor is not a floor, it is the
    #    rule being skipped. Two assertions, over every shopfronted phase: the
    #    verdict agrees with the integer the builder is handed, and every floor is a
    #    floor the frontage forced.
    over, floors, stated_rows = [], 0, []
    for rid, fam, phase, p in rows:
        if not p.shopfront:
            continue
        front = p.width_m
        if "shopfront_bays" in phase.get("form", {}):
            # The RECORD answered, not the rule. Its count is gate 4's business; let
            # the census here read it as a floor and the reported "N on the floor"
            # becomes a claim about a rule that was never consulted.
            stated_rows.append((rid, fam, phase, p, front))
            continue
        bays, why, frac = P.shopfront_bay_verdict(front)
        if break_it == "floor":
            bays, why, frac = 1, P.BAY_FLOOR_OVER_FRACTION, P.shopfront_width_m(1) / front
        if break_it == "afford":
            why, frac = P.BAY_FLOOR_OVER_FRACTION, P.shopfront_width_m(bays) / front
        if bays != P.default_shopfront_bays(front):
            check(f"{rid}: the verdict is the count the builder is handed", False,
                  f"verdict {bays} vs built {P.default_shopfront_bays(front)}")
            continue
        if why == P.BAY_WITHIN_FRACTION:
            continue
        floors += 1
        if why == P.BAY_FLOOR_OVER_FRACTION:
            over.append((rid, front, frac))
        afford = P.shopfront_width_m(2) <= front * P.SHOPFRONT_MAX_FRACTION
        check(f"{rid}: the floor is one the frontage forced, not the rule skipped",
              not afford,
              f"front {front:.2f} m, one window and the door is {frac * 100:.1f}% of it")
    # 4. A STATED COUNT MAY COME INTO ITS BAND AND MAY NOT LEAVE IT, OR THE FRAME
    #    (T-1667). `from_phase` reads `shopfront_bays` off the record when it is
    #    there, which is how the C4 reaches the 4 facade bays its family authors and
    #    the 45% default cannot give it. That override has to be bounded at both
    #    ends or it is simply a way to write any front at all: the count it states
    #    must be inside the family's authored band, and the frontage must hold it
    #    with `PIER_MIN_M` of wall left at each end — the same refusal
    #    `FrameStorefrontParams.validate` makes, asserted here so a record cannot be
    #    committed in a state only the bake would reject.
    for rid, fam, phase, p, front in stated_rows:
        bays = P.facade_bays(p.shopfront_bays)
        need = P.shopfront_width_m(p.shopfront_bays)
        if break_it == "stated_band":
            bays = bays + 9
        if break_it == "stated_afford":
            need = front + 1.0
        if fam in ranges:
            lo, hi = ranges[fam]
            check(f"{rid}: the count it states is inside {fam}'s authored band",
                  lo <= bays <= hi, f"{bays} facade bays vs {lo}-{hi}")
        check(f"{rid}: the frontage holds the count it states",
              need <= front - 2 * P.PIER_MIN_M,
              f"{need:.3f} m of opening on a {front:.3f} m front leaves "
              f"{(front - need) / 2:.3f} m each end, minimum {P.PIER_MIN_M:.2f} m")
    if stated_rows:
        print(f"\n  {len(stated_rows)} front(s) state their own count, so the "
              f"{P.SHOPFRONT_MAX_FRACTION:.0%} default did not decide them:")
        for rid, fam, phase, p, front in stated_rows:
            _, why, _ = P.shopfront_bay_verdict(front)
            print(f"        {rid} {fam}: {P.facade_bays(p.shopfront_bays)} facade bays, "
                  f"{P.shopfront_width_m(p.shopfront_bays) / front * 100:.1f}% of the "
                  f"front; the default would have said "
                  f"{P.facade_bays(P.default_shopfront_bays(front))} ({why})")

    if over:
        lo = min(o[2] for o in over)
        hi = max(o[2] for o in over)
        print(f"\n  {floors} front(s) reach the floor, {len(over)} of them OVER the "
              f"{P.SHOPFRONT_MAX_FRACTION:.0%} ceiling: {lo * 100:.1f}% to "
              f"{hi * 100:.1f}% of the frontage in opening")

    print()
    if FAILED:
        print(f"{len(FAILED)} check(s) FAILED")
        return 1
    print(f"shop-bay reading OK — {in_band} storefront(s) inside their authored band, "
          f"{len(stated_rows)} of them on a count the record states, "
          f"{floors} on the floor ({len(over)} of them over the ceiling), "
          f"{len(witnesses)} crosswalk witness(es) for the door-inclusive reading")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        rc = 0
        for mode, what in (("reading", "the crosswalk's witnesses lose their odd counts"),
                           ("band", "a C3 is pushed outside its authored band"),
                           ("floor", "every front is told it fell to the floor"),
                           ("afford", "a front wide enough for the rule is called a "
                                      "floor anyway"),
                           ("stated_band", "a stated count is pushed outside its "
                                           "family's authored band"),
                           ("stated_afford", "a stated count is made wider than its "
                                             "own frontage")):
            FAILED.clear()
            print(f"SELF-TEST: {what}; the assertions must fire.")
            if main(break_it=mode) == 0:
                print(f"SELF-TEST FAILED: the assertions passed on a broken {mode}.")
                rc = 1
            print()
        if rc == 0:
            print("self-test OK — each assertion fires when its own input is bent.")
        sys.exit(rc)
    sys.exit(main())
