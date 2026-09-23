#!/usr/bin/env python3
"""What the face rule ranks, and where a NON-DWELLING stands (T-0024, ROADMAP K32).

The face rule as committed at T-A13 and T-A14 ranks DWELLINGS: the best dwellings the
schedule deals a block take its better street, the meanest take the back one. It is an
invention of this programme and every record that applies it says so.

`blk_randolph_clark` was the first block parcel ever dealt a STORE, and the rule said
nothing about one. T-A15 EXTENDED the ranking to cover it — commerce above the better
dwelling, on the reasoning that a store-residence's claim on the better frontage is
functional rather than social, "the only one of the six roofs whose purpose requires that
a stranger can find it" — put the C2 on Randolph and sent a D6 to the back street. That
extension was an invention about 1835 commerce made by an agent, and it was opened as
K32 rather than left as a private decision, because the schedule still holds C1…C4,
F1…F4, H3, T1 and W1…W5 for blocks not yet built and the same question arrives again the
moment one of them is dealt.

## What is settled, and it is reading 2 of the three the ROADMAP offered

**The face rule ranks dwellings only. A non-dwelling is placed by its own FUNCTION.**

Reading 1 was to keep the extension and rank commerce above dwellings; reading 3 was to
refuse the question and leave non-dwelling placement to each parcel's arrangement note.
Reading 2 is taken because it is the only one of the three that can be READ OFF THE
COMMITTED RECORD instead of argued: this project already holds 48 documented buildings its
own reconciliation credits a non-dwelling family, and where they stand is a measurement.

## The reading, and this module is what takes it

Per family letter, over the documented layer, by the traffic class the committed street
hierarchy authors in `data/streets/1835.json` for the street each building stands nearest:

    C  stores        15 records — 10 principal   5 ordinary   0 light
    F  warehouses     9 records —  9 principal   0 ordinary   0 light
    W  workshops      7 records —  2 principal   5 ordinary   0 light
    T  lodging        8 records —  3 principal   4 ordinary   1 light
    I  institutions   9 records —  1 principal   4 ordinary   4 light

Run this module with no arguments and the table above is what it prints, from the tree
rather than from this docstring. **Not one documented store, warehouse or workshop in this
town stands on a light street**, and that zero is the load-bearing figure: it is what makes
"a store takes the better face" a reading of the record rather than a preference about
frontage. It is a zero across the stores and the warehouses, two of the three letters a
block parcel may actually be dealt.

The letters that are not zero are stated rather than trimmed away. **W's one** arrived on
2026-09-06 with T-0883: `fort_dearborn_shop`, the garrison workshop the 1830 Harrison plan
letters on Fort Dearborn's outer ground, which this table puts **381 m** from the State
Street centreline — further off than T's, and for a harder reason than distance. The
military reservation was UNPLATTED in 1835 and no street crossed it (see
`data/reconstruction/1835_no_build_ground.json`), so a building inside the fort's fence has
no street frontage to take a better or a worse face of. The zero it breaks is a statement
about buildings that front streets, and this one does not front one. **T's one** is the
Steamboat Hotel, which this table puts 287 m from the State Street centreline: it does not
front State, State is simply the nearest committed line in a division that has almost no
street control yet, and the same artefact accounts for most of the invented residual at the
bottom of the printout. **I's four** are the lighthouse, the council house, St Mary's and
the Watkins school house — and `tools/generate_block_infill.py` refuses the institutional
families to a block parcel BY NAME anyway (L93, ROADMAP T-I3), so no rule about frontage
ever reaches them. The assertion below reads this table rather than a list typed beside it,
so it asserts nothing about a letter the record does not put a zero on.

The second reading is the SETBACK, and it is what the word "functional" in T-A15's
sentence actually buys. Thirteen of the fifteen documented stores stand ON the street
line — inside `measure_frontage_fabric.STREET_LINE_M`, the band that module derives from
the empty gap in the town's own setback distribution. The two that do not are both off the
platted grid: Robert Kinzie's store at Wolf Point, 27 m from the Lake Street line, and the
Miller house 138 m from South Water's. **Every documented store standing on a platted
street stands on its line.** A dwelling stands back at a typology setback of 4.0 to 7.5 m.
A store does not.

## What is asserted, and the scope is the rule's own

The face rule is a PLATTED BLOCK PARCEL rule, so the assertions run over the roofs those
parcels place — `recon_1835_blk_*` — and everything else is reported. Three of them stand
today: a C2 store-residence on `blk_randolph_clark` and two C3 stores in the party-line
run on `blk_south_water_dearborn`.

1. **No block-parcel non-dwelling stands on a frontage class its own family letter has no
   documented instance of.** Absolute: the record's zero on light streets is not a
   threshold this module chose, and an invented store on a light street would be the first
   one in Chicago.
2. **Every block-parcel COMMERCIAL roof stands on the street line.** Absolute, n=3.

Neither is a ratchet. Both were green the day they were written, which is the only kind of
absolute assertion worth adding — see the `--self-test`, which breaks each in memory.

## What this module deliberately does NOT assert

The North, West and phase-one parcels ran before any of this and place another 23
non-dwelling roofs. Seven of them are assigned to State Street here at 150 to 550 m of
setback, which is not a frontage — it is the nearest committed centreline in a division
that has almost no street control yet. Gating on those would be gating on the absence of a
street, so they are printed with their setbacks and asserted about nowhere. The two
invented warehouses standing nearest Randolph at 12.9 and 14.5 m, against a documented F
record that is 9-of-9 on principal streets, are a real residual and are printed as one.

    tools/measure_face_rule.py             the reading, documented and invented
    tools/measure_face_rule.py --gate      exit 1 on either assertion
    tools/measure_face_rule.py --self-test break both in memory and watch them fire
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT / "tools"))

from measure_frontage_fabric import (  # noqa: E402
    STREET_LINE_M, census, documented_families, street_traffic,
)

# The family letters that are not a dwelling. `A` is excluded on purpose: a yard building
# is placed by the ancillary clause — off the block alley, behind its own principal roof —
# which is a rule about the LOT and not about the street, and it long predates this one.
NON_DWELLING = "CFTWI"
COMMERCIAL = "C"
CLASSES = ("principal", "ordinary", "light")

# The block parcels' own prefix. The face rule is their rule; see the docstring.
BLOCK_PREFIX = "recon_1835_blk_"

# Reconstructed records carry their family in the id, which is how every other module in
# this tree reads it back — `recon_1835_<parcel>_<family>_<seq>`.
FAMILY_IN_ID = re.compile(r"_([a-z]\d)_\d+$")


def family_of(record_id: str) -> str | None:
    match = FAMILY_IN_ID.search(record_id)
    return match.group(1).upper() if match else None


def reading() -> dict:
    """Every building placed against the street it stands nearest, with its family."""
    traffic = street_traffic()
    documented = documented_families()
    rows = []
    for row in census()["rows"]:
        family = (documented.get(row["id"]) if row["layer"] == "research"
                  else family_of(row["id"]))
        if not family or family[0] not in NON_DWELLING:
            continue
        rows.append({"id": row["id"], "layer": row["layer"], "family": family,
                     "letter": family[0], "street": row["street"],
                     "class": traffic.get(row["street"]),
                     "setback_m": row["setback_m"], "on_line": row["on_line"],
                     "block_parcel": row["id"].startswith(BLOCK_PREFIX)})
    return {"rows": rows}


def documented_classes(rows: list[dict]) -> dict[str, dict[str, int]]:
    """letter -> {traffic class: how many DOCUMENTED buildings of it stand there}."""
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        if row["layer"] != "research":
            continue
        out.setdefault(row["letter"], {k: 0 for k in CLASSES})
        if row["class"] in CLASSES:
            out[row["letter"]][row["class"]] += 1
    return out


def failures(result: dict | None = None) -> list[str]:
    """The two assertions. See the docstring."""
    rows = (result or reading())["rows"]
    witness = documented_classes(rows)
    out = []
    for row in rows:
        if not row["block_parcel"]:
            continue
        seen = witness.get(row["letter"], {})
        if row["class"] in CLASSES and seen and seen.get(row["class"], 0) == 0:
            out.append(
                f"{row['id']} ({row['family']}) fronts {row['street']}, a "
                f"{row['class']} street, and no documented {row['letter']} building in "
                f"this town stands on one — it would be the first")
        if row["letter"] == COMMERCIAL and not row["on_line"]:
            out.append(
                f"{row['id']} ({row['family']}) stands {row['setback_m']} m back, off "
                f"the street line ({STREET_LINE_M} m). A commercial roof stands on it")
    return out


def _table(result: dict) -> str:
    rows = result["rows"]
    lines = ["\n   where a non-dwelling stands, by the class of the street it is nearest",
             "   (the documented reading is the rule; see the module docstring)\n",
             "   layer        letter      n   principal   ordinary      light"]
    for label, test in (("documented", lambda r: r["layer"] == "research"),
                        ("block parcels", lambda r: r["block_parcel"]),
                        ("other invented", lambda r: r["layer"] != "research"
                         and not r["block_parcel"])):
        lines.append(f"   {label}")
        for letter in NON_DWELLING:
            picked = [r for r in rows if test(r) and r["letter"] == letter]
            if not picked:
                continue
            counts = [sum(1 for r in picked if r["class"] == k) for k in CLASSES]
            lines.append(f"   {'':<12} {letter:<8} {len(picked):>4}"
                         + "".join(f"{c:>11}" for c in counts))
    lines.append("\n   every block-parcel non-dwelling, and where it stands\n")
    for row in sorted(rows, key=lambda r: r["id"]):
        if not row["block_parcel"]:
            continue
        lines.append(f"   {row['family']:<4} {row['id']:<44} {row['street']:<13}"
                     f"{str(row['class']):<11}{row['setback_m']:>7.2f} m"
                     f"{'  on the line' if row['on_line'] else '  set back'}")
    lines.append("\n   the residual this module reports and does not assert on:")
    for row in sorted(rows, key=lambda r: r["id"]):
        if row["layer"] == "research" or row["block_parcel"]:
            continue
        lines.append(f"   {row['family']:<4} {row['id']:<44} {row['street']:<13}"
                     f"{str(row['class']):<11}{row['setback_m']:>7.2f} m")
    return "\n".join(lines) + "\n"


def _synthetic(street: str, setback: float) -> dict:
    """One invented block-parcel store, in memory, beside the committed documented rows.

    Only the fields the assertions read are built: this exercises the two clauses, not
    the plat, which `tools/generate_block_infill.py` already re-derives on every commit.
    """
    result = reading()
    result["rows"] = result["rows"] + [{
        "id": "recon_1835_blk_synthetic_c1_01", "layer": "reconstruction",
        "family": "C1", "letter": "C", "street": street,
        "class": street_traffic().get(street), "setback_m": setback,
        "on_line": setback <= STREET_LINE_M, "block_parcel": True}]
    return result


def self_test() -> int:
    print("  both assertions, broken in memory against the committed reading\n")
    checks = []

    out = failures()
    checks.append(("the committed town passes both assertions",
                   not out, "; ".join(out) or "clean"))

    # The zero the first assertion rests on, and it is on two letters rather than five.
    # W, T and I are stated in the docstring and are not trimmed away: W's single
    # light-street instance is the fort's shop, 381 m off the nearest street and inside a
    # federal reservation no street crossed in 1835; T's stands 287 m off the street it is
    # nearest; and the institutional families are refused to a block parcel by name. The
    # assertion reads this witness rather than a list, so none of the three licenses
    # anything either way — and the two it does assert on, the stores and the warehouses,
    # are still zero across 25 buildings.
    witness = documented_classes(reading()["rows"])
    checks.append(("no documented store or warehouse stands on a light street, "
                   "which is what the first assertion rests on",
                   all(witness.get(k, {}).get("light", 0) == 0 for k in "CF"),
                   ", ".join(f"{k} {v['light']}" for k, v in sorted(witness.items()))))

    out = failures(_synthetic("washington", 1.5))
    checks.append(("a block-parcel store put on a light street is caught",
                   any("would be the first" in m for m in out),
                   "; ".join(out) or "nothing"))

    out = failures(_synthetic("randolph", 5.0))
    checks.append(("…and one left at a dwelling's typology setback is caught",
                   any("off the street line" in m for m in out),
                   "; ".join(out) or "nothing"))

    out = failures(_synthetic("randolph", 1.5))
    checks.append(("…and the same store on the better face, on the line, passes",
                   not out, "; ".join(out) or "clean"))

    ok = True
    for label, passed, detail in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  {label} — {detail}")
        ok &= passed
    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 where a block parcel places a non-dwelling the "
                             "documented record refuses")
    parser.add_argument("--self-test", action="store_true",
                        help="break both assertions in memory and watch them fire")
    parser.add_argument("--quiet", action="store_true",
                        help="print only the verdict")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    result = reading()
    if not args.quiet:
        print(_table(result))
    out = failures(result)
    if out:
        print("THE FACE RULE'S NON-DWELLING CLAUSE IS BREACHED")
        for message in out:
            print(f"  - {message}")
        return 1 if args.gate else 0
    print(f"  {sum(1 for r in result['rows'] if r['block_parcel'])} block-parcel "
          f"non-dwelling roof(s): every one on a frontage class the documented record "
          f"carries, every commercial one on the street line")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
