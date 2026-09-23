#!/usr/bin/env python3
"""The ten group rows, split by division, against the roofs that actually stand there.

Ticket T-0211, found by T-0032 (PR #388). `data/reconstruction/1835_building_inventory.json`
carries the same aggregate three ways — `family_targets` (35 families), `district_group_matrix`
(10 groups x 4 divisions) and `districts` (4 totals) — and `tools/reconcile_665.py` asserts
that all three sum to `roof_total` and that each group's families sum to that group's row.
**Nothing asserted anything about a group's split BY DIVISION**, and the two views were
authored independently. T-0032 found what that permits: the `institutional_public` row read
south 10 / west 1 / north 1 while the named institutional records stand south 5 / west 1 /
north 3. Every sum closed, and the schedule was apportioning phantom headroom in one division
while telling another it had room for a building already standing in it.

## Why the I3 repair does not generalise, and what is asserted instead

An institutional row can be held to a census because Chicago's public buildings are
enumerable. Dwellings, stores and barns are not: an anonymous dwelling is a legitimate
count-unit toward a documented aggregate, so "the row equals what stands" is the WRONG
assertion for the other nine rows. A row 74 roofs above what stands is the programme working
as intended.

What this asserts is the weaker pair the ticket asks for, and it is enough to catch the fault:

1. **The matrix is internally addable, by division as well as by group.** Each row's four
   cells sum to that row's own `total`, and each division's ten cells sum to that division's
   own `target`. Neither was asserted anywhere before this. The second is what makes the
   shed below an identity rather than a coincidence.
2. **Every division already OVER its group row is DECLARED, and no new one appears.** A
   ratchet, in the shape `tools/measure_band_claims.py` uses: the residual is real, it may
   shrink, it may not grow, and a division going newly over a row fails here. This is the
   half `reconcile_665.py` could not report, because
   `max(0, matrix[g][district] - built[(district, g)])` clamps the negative away: a row that
   is wrong by six roofs looked exactly like a row that is right.

## What the overshoot costs, which is why it is worth a gate

The clamp does not just hide the breach — it silently RE-SPENDS it. A division's ten clamped
group heads then sum to MORE than that division's remainder (by exactly the overshoot, since
the cells sum to the target), and `reconcile_665.py` sheds the difference one slot at a time
from whichever group has the most head at that moment. So the North Division's seven
overshooting roofs were paid for out of its ordinary dwellings, and until this ticket nothing
anywhere said so. Both figures are now written into the programme document —
`remaining.district_group_rows_overshot` and `remaining.district_group_slots_shed` — so the
ledger reports the transfer it makes.

**Six of those seven are repaired.** T-0283 moved the freight row's split — north 1 → 7 out of
south 17 → 11, with ordinary_dwellings swapping the other way so that both row totals and all
four district targets stand — and the North's shed fell from 7 slots to 1. The one that is left
is the L93 institutional liberty, which is not an authoring fault: it is this gate and
`measure_institutional_claims.py` reading one liberty differently, and it moves when the liberty
is retired. The argument is `district_group_matrix_note` in the inventory.

    tools/measure_group_district_rows.py              print the 10 x 4 audit
    tools/measure_group_district_rows.py --gate       fail on drift or a new overshoot
    tools/measure_group_district_rows.py --self-test  break each assertion, confirm it fires
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RECON = DATA / "reconstruction"

sys.path.insert(0, str(ROOT / "tools"))

DISTRICTS = ("south", "west", "north", "fort")

# THE DECLARED OVERSHOOT — every (division, group) pair where more roofs stand than that
# division's row allows, with the size of the breach and what the roofs are. Measured
# 2026-08-28 against the committed records; a ratchet, not a licence. `over` may fall and
# may not rise, an undeclared pair fails, and a pair repaired to zero must be retired from
# this table rather than left standing as a stale allowance.
#
# A breach is not repairable by editing a cell on its own: the cells sum to their division's
# target and to their group's total, so moving one moves four other numbers and the 662-roof
# programme with them. That is a decision about the authored target, so a declaration here is
# a holding position while the ticket that has to make it is open. T-0283 made that decision
# for the freight row on 2026-08-29 — see `district_group_matrix_note` in the inventory — and
# the declaration went with it. The one left is not a fault at all: it is two gates reading
# one liberty differently, and it moves when the liberty does.
DECLARED_OVERSHOOT = {
    ("north", "institutional_public"): {
        "over": 1,
        "why": "T-0032 set this row to the NAMED institutional census — south 5 / west 1 / "
               "north 3 — and `tools/measure_institutional_claims.py` holds it there. This "
               "counts every roof that stands, named or not, so it also counts "
               "recon_1835_north_i2_015, the one anonymous school docs/LIBERTIES.md records "
               "at L93 as a liberty taken rather than deleted. The two gates disagree by "
               "exactly that liberty, and both readings are correct for their own question. "
               "The row moves when L93 is retired, not before.",
    },
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def standing_by_district_group() -> dict[tuple[str, str], int]:
    """Roofs that stand, keyed by (division, group).

    Derived through `reconcile_665.standing_roofs` rather than re-counted here, so this
    gate and the ledger it audits can never be counting different towns — the fault T-0032
    was bitten by was two documents answering one question separately.
    """
    import reconcile_665 as ledger  # noqa: PLC0415

    grid = load(DATA / "traces" / "vectors" / "thompson_lots.json")
    datum = load(DATA / "datum.json")
    rows = ledger.standing_roofs(grid, datum, ledger.occupied_lots(grid, datum))
    built: dict[tuple[str, str], int] = {}
    for row in rows:
        n = row["roofs_min"]
        if not n:
            continue
        key = (row["district"], ledger.group_of(row["family"]))
        built[key] = built.get(key, 0) + n
    return built


def audit(inventory: dict, built: dict[tuple[str, str], int]) -> list[dict]:
    """One row per (group, division): the target, what stands, and the signed gap."""
    matrix = inventory["district_group_matrix"]
    out = []
    for group, row in matrix.items():
        for district in DISTRICTS:
            target, standing = row[district], built.get((district, group), 0)
            out.append({"group": group, "district": district, "target": target,
                        "standing": standing, "gap": target - standing})
    return out


def shed_by_district(inventory: dict,
                     built: dict[tuple[str, str], int]) -> dict[str, dict[str, int]]:
    """Which groups pay for each division's overshoot, and by how much.

    The same arithmetic `reconcile_665.py` runs, kept here so the audit and the ledger
    cannot drift apart: clamp each group head at zero, then shed whatever that leaves
    above the division's own remainder, one slot at a time from the group with the most
    head. The total shed is the overshoot exactly, whenever assertion 1 holds — which is
    why the two are asserted together.
    """
    matrix = inventory["district_group_matrix"]
    shed: dict[str, dict[str, int]] = {}
    for district in DISTRICTS:
        head = {g: max(0, matrix[g][district] - built.get((district, g), 0)) for g in matrix}
        standing = sum(built.get((district, g), 0) for g in matrix)
        remainder = inventory["districts"][district]["target"] - standing
        taken: dict[str, int] = {}
        for _ in range(max(0, sum(head.values()) - remainder)):
            group = sorted(head, key=lambda g: (-head[g], g))[0]
            head[group] -= 1
            taken[group] = taken.get(group, 0) + 1
        shed[district] = dict(sorted(taken.items()))
    return shed


def addable_findings(inventory: dict) -> list[str]:
    """Assertion 1: the matrix adds up in BOTH directions, and to the totals beside it."""
    matrix = inventory["district_group_matrix"]
    findings = []
    for group, row in matrix.items():
        cells = sum(row[d] for d in DISTRICTS)
        if cells != row["total"]:
            findings.append(
                f"the {group} row's four divisions sum to {cells} and the row's own total "
                f"is {row['total']}. The split by division and the group total were "
                f"authored separately and nothing read them together.")
    for district in DISTRICTS:
        cells = sum(matrix[g][district] for g in matrix)
        target = inventory["districts"][district]["target"]
        if cells != target:
            findings.append(
                f"the {district} division's ten group cells sum to {cells} and its own "
                f"target is {target}. Every group head reconcile_665.py apportions comes "
                f"out of this column, so a column that does not equal its division's "
                f"target sheds or invents roofs with no record of doing either.")
    return findings


def overshoot_findings(rows: list[dict], table: dict | None = None) -> list[str]:
    """Assertion 2: every division over its group row is declared, at no more than its
    declared size, and no declaration outlives the breach it describes.

    `table` defaults to the committed DECLARED_OVERSHOOT. The self-test passes a synthetic
    one, so the three ratchet cases below keep testing the ratchet whatever the live table
    happens to hold — T-0283 retired the one declaration big enough to fall without
    vanishing, and the cases that read it went stale in the same commit.
    """
    if table is None:
        table = DECLARED_OVERSHOOT
    findings = []
    over = {(r["district"], r["group"]): -r["gap"] for r in rows if r["gap"] < 0}
    for key, size in sorted(over.items()):
        district, group = key
        declared = table.get(key)
        if declared is None:
            findings.append(
                f"the {district} division stands {size} roof(s) OVER its {group} row and "
                f"the breach is not declared. reconcile_665.py clamps the negative away, so "
                f"the row reads as satisfied while the division quietly sheds {size} slot(s) "
                f"from another group to pay for it. Declare it in DECLARED_OVERSHOOT with "
                f"what the roofs are, or repair the row.")
        elif size > declared["over"]:
            findings.append(
                f"the {district} division's {group} overshoot has GROWN from "
                f"{declared['over']} to {size}. This is a ratchet: the residual may fall "
                f"and may not rise.")
    for key, declared in sorted(table.items()):
        district, group = key
        size = over.get(key, 0)
        if size == 0:
            findings.append(
                f"the {district} division is no longer over its {group} row and the "
                f"declaration is still here. A repaired breach is retired from "
                f"DECLARED_OVERSHOOT, not left standing as an allowance for the next one.")
        elif size < declared["over"]:
            findings.append(
                f"the {district} division's {group} overshoot has fallen from "
                f"{declared['over']} to {size}. Lower the declaration in the same commit "
                f"that lowered the breach, or the ratchet stops holding at the new figure.")
    return findings


def findings(inventory: dict, rows: list[dict]) -> list[str]:
    return addable_findings(inventory) + overshoot_findings(rows)


def self_test() -> int:
    """Break each assertion in memory and confirm it is noticed."""
    inventory = load(RECON / "1835_building_inventory.json")
    built = standing_by_district_group()
    rows = audit(inventory, built)

    live = findings(inventory, rows)
    if live:
        print("   FAIL  the committed dataset does not pass, so the self-test has no "
              "clean starting point")
        for line in live:
            print(f"          {line}")
        return 1
    print("   ok    the committed dataset passes, so a break below is this test's own doing")

    ok = True

    def case(label: str, got: list[str], expect: str) -> None:
        nonlocal ok
        hit = any(expect in f for f in got)
        print(f"   {'ok  ' if hit else 'FAIL'}  {label}")
        if not hit:
            print(f"          expected a finding containing {expect!r}, got {got}")
            ok = False

    def copy(doc):
        return json.loads(json.dumps(doc))

    moved = copy(inventory)
    moved["district_group_matrix"]["barns_stables"]["north"] = 18
    case("a row whose divisions no longer sum to its own total is caught",
         addable_findings(moved),
         "the barns_stables row's four divisions sum to 74 and the row's own total is 73")

    column = copy(inventory)
    column["district_group_matrix"]["barns_stables"]["north"] = 18
    column["district_group_matrix"]["barns_stables"]["total"] = 73
    case("...and so is a division column that no longer equals its own target",
         addable_findings(column),
         "the north division's ten group cells sum to 153 and its own target is 152")

    # T-0032's fault had two halves and this gate can only see one of them. The NORTH
    # half — a row of 1 with roofs standing above it — is a breach and fails below. The
    # SOUTH half — a row of 10 with 5 standing — is phantom headroom, and that is the
    # shape nine of these ten rows legitimately have (see the module docstring): a row
    # 74 roofs above what stands is the programme working. Only an enumerable group can
    # be held to its census, which is what tools/measure_institutional_claims.py does for
    # this one row and why it stays a separate gate.
    t0032 = copy(inventory)
    t0032["district_group_matrix"]["institutional_public"].update(
        south=10, west=1, north=1, total=12)
    case("the north half of the apportionment T-0032 corrected is caught",
         overshoot_findings(audit(t0032, built)),
         "the north division's institutional_public overshoot has GROWN from 1 to 3")

    tight = copy(inventory)
    tight["district_group_matrix"]["ordinary_dwellings"]["west"] = 20
    case("a new, undeclared division breach fails",
         overshoot_findings(audit(tight, built)),
         "the west division stands 1 roof(s) OVER its ordinary_dwellings row")

    # The three ratchet cases run against a SYNTHETIC declaration, not the live table.
    # They used to drive the freight row, and T-0283 repaired that row out from under
    # them; a declaration of size 1 — which is all the live table now holds — cannot fall
    # without disappearing, so "fallen from" would have had no case at all. The synthetic
    # table declares the North's freight row at 6 as it stood before the repair, which is
    # the shape the ratchet exists for.
    was = {("north", "warehouses_freight"): {"over": 6, "why": "synthetic, self-test only"}}
    before = copy(inventory)
    before["district_group_matrix"]["warehouses_freight"].update(south=17, north=1)
    before["district_group_matrix"]["ordinary_dwellings"].update(south=170, north=90)

    grown = {(d, g): n + (3 if (d, g) == ("north", "warehouses_freight") else 0)
             for (d, g), n in built.items()}
    case("a declared breach that GROWS fails — the ratchet only falls",
         overshoot_findings(audit(before, grown), was),
         "warehouses_freight overshoot has GROWN from 6 to 9")

    healed = {(d, g): (1 if (d, g) == ("north", "warehouses_freight") else n)
              for (d, g), n in built.items()}
    case("a declaration that outlives its breach fails",
         overshoot_findings(audit(before, healed), was),
         "no longer over its warehouses_freight row and the declaration is still here")

    shrunk = {(d, g): (4 if (d, g) == ("north", "warehouses_freight") else n)
              for (d, g), n in built.items()}
    case("...and so does one left at a figure the breach has fallen below",
         overshoot_findings(audit(before, shrunk), was),
         "warehouses_freight overshoot has fallen from 6 to 3")

    # And the repair itself: the row T-0283 moved is no longer over, and the committed
    # table no longer declares it. Both halves, because either alone passes vacuously.
    live_rows = audit(inventory, built)
    freight_north = next(r for r in live_rows
                         if (r["district"], r["group"]) == ("north", "warehouses_freight"))
    repaired = (freight_north["gap"] >= 0
                and ("north", "warehouses_freight") not in DECLARED_OVERSHOOT)
    print(f"   {'ok  ' if repaired else 'FAIL'}  T-0283's repair holds: the North's freight "
          f"row is not over and carries no declaration")
    if not repaired:
        ok = False

    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 when the matrix does not add up in both directions, "
                             "or a division is over a group row without declaring it")
    parser.add_argument("--quiet", action="store_true",
                        help="print the assertion and the failures, not the audit")
    parser.add_argument("--self-test", action="store_true",
                        help="break each assertion in memory and confirm it fires")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    inventory = load(RECON / "1835_building_inventory.json")
    built = standing_by_district_group()
    rows = audit(inventory, built)
    shed = shed_by_district(inventory, built)
    failures = findings(inventory, rows)

    if not args.quiet:
        print(f"   {'group':<23}{'division':<10}{'target':>7}{'stands':>8}{'gap':>7}")
        for row in rows:
            mark = ""
            if row["gap"] < 0:
                key = (row["district"], row["group"])
                mark = "  OVER" + (" (declared)" if key in DECLARED_OVERSHOOT else "")
            print(f"   {row['group']:<23}{row['district']:<10}{row['target']:>7}"
                  f"{row['standing']:>8}{row['gap']:>+7}{mark}")
        print("\n   WHAT THE OVERSHOOT COSTS EACH DIVISION")
        for district in DISTRICTS:
            over = sum(-r["gap"] for r in rows
                       if r["district"] == district and r["gap"] < 0)
            paid = ", ".join(f"{g} {n}" for g, n in shed[district].items()) or "nothing"
            print(f"     {district:<7} over its rows by {over:>2} roof(s); "
                  f"reconcile_665.py sheds {sum(shed[district].values()):>2} slot(s) to pay "
                  f"for it, from {paid}")

    if failures:
        print("\n   GROUP-ROW FAILURES")
        for line in failures:
            print(f"     - {line}")
        return 1 if args.gate else 0

    total_over = sum(-r["gap"] for r in rows if r["gap"] < 0)
    clear = sum(1 for r in rows if r["gap"] >= 0)
    n = len(DECLARED_OVERSHOOT)
    print(f"\n   the matrix adds up by group and by division; {clear} of the "
          f"{len(rows)} (group, division) cells hold roofs they have room for, and the "
          f"{n} that {'does' if n == 1 else 'do'} not "
          f"{'is' if n == 1 else 'are'} declared, at {total_over} roof(s)"
          f"{'.' if n == 1 else ' between them.'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
