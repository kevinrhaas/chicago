#!/usr/bin/env python3
"""What a party-line run was DEALT, and what it actually STANDS ON.

T-0199. Five documented South Water Street stores could not be reconciled with the
committed plat because each, put back on its own street line, seats on a platted lot
the 665-roof schedule had already dealt to the anonymous frontage run standing on that
block face — and `tools/generate_block_infill.py` refused, in its own words, to "deal a
roof to a lot that already carries one". T-0188 named all five in writing and left the
untangling to this instrument, because the question underneath them cannot be answered
by reading the recipe: **does the run stand on the lots it was dealt?**

Measured on the committed dataset, it does not, and not by a little. Of the eight
anonymous roofs on the three blocks in question, every one stands on lot 4 or lot 2 —
and the recipes deal those runs lots 0, 2 and 4. Three lots of frontage were entitled
and one or two were occupied, because a run PACKS from one end of its own strip and
`ROW_UNITS_PER_LOT` of its units fit inside a single lot of this grid.

**That gap is not a defect in the recipes; it is what T-0079 built.** Before the core
density standard a run carried exactly one roof per lot it was dealt, so "dealt" and
"stood on" were the same list and nothing distinguished them. T-0079 retired that — a
row is a claim about the FACE, bounded by the metres of frontage it stands on and not
by the conjectural side lines it crosses — and the two lists came apart the moment it
landed. Nothing measured them apart until a documented building wanted the difference.

So the refusal these five met was the PRE-T-0079 ceiling still standing at the gate:
one roof to a lot, applied to a layer whose whole point is that it is denser than the
lot grid. The rule this module authors is the same protection expressed in the unit
T-0079 established, and it is not looser where it matters:

    a run's frontage carries ROW_UNITS_PER_LOT units per lot it was dealt, and
    every roof already standing on those lots counts against that ceiling.

A block dealt one lot and carrying three units is at its ceiling under both rules, so
nothing that was refused for want of ground is now let through — `blk_lake_clark` and
both `blk_randolph_dearborn` deals sit at exactly 3 of 3 and a documented roof seating
on their lot would still fail. What changes is the block that was refused for want of
an ENTITLEMENT it was not using: three units against nine, with six units of frontage
unbuilt and a documented store standing out in the roadway because a list said the lot
was spoken for.

Nothing here authors a coordinate or a count. `ROW_UNITS_PER_LOT` is imported from
`tools/reconcile_665.py`, where the schedule deals against it; occupancy is
`tools/plat_occupancy.py`, the same module the gate and the schedule already share; and
the run's own units are read out of the committed records' `reconstruction.frontage`.

T-0233 ASKED WHETHER THE GAP IS A DEFECT OR A RESERVATION. IT IS A RESERVATION
--------------------------------------------------------------------------------
The reading above left one question open, and it had to be answered before anything
moved: a run dealt three lots and standing on one — **is the unbuilt remainder the
schedule HOARDING ground, or is it frontage the run is entitled to and has not filled
yet?** Both readings are defensible from the table alone. They are not defensible from
the code, and this is the argument from the code.

**It is a reservation, and the defect reading's promised payoff does not exist.** The
case for "defect" rested on one claim — that the schedule is charged for every lot it
deals, so shrinking the deals would recover headroom. Measured, the schedule is charged
for none of them:

    tools/reconcile_665.py:915    free = lots - len(available.get(block["id"], ()))
    tools/reconcile_665.py:813    available = exclusive_lots(grid, datum)

`free_lots` — the only thing `block_rooms()` turns into `principal_room`, and so the
only route from a lot to `schedulable_on_committed_ground` — is derived from committed
FOOTPRINTS through `plat_occupancy.exclusive_lots`. It has never read
`frontage["lots"]`. A lot a recipe dealt and nobody built on carries no footprint, so it
arrives at the schedule as FREE and the schedule deals principal room against it
already. There is no headroom to recover, because none was ever spent.

The table's own eight lots say the same thing from the other end. "Carries none of its
run's own roofs" is not "carries nothing", and the three cases are worth separating,
which is why `survey()` now classifies them (`idle_class` below):

    lot                                   what actually stands on it
    blk_south_water_franklin   lot 2      nothing
    blk_south_water_franklin   lot 4      the parcel's own yard building (a3_07)
    blk_south_water_wells      lot 0      H. Jones's store, and the parcel's a3_08
    blk_south_water_lasalle    lot 0      nothing
    blk_south_water_lasalle    lot 2      nothing
    blk_south_water_clark      lot 2      Pruyne & Kimball's drugstore
    blk_south_water_dearborn   lot 0      the Chicago American office, and a3_06
    blk_south_water_dearborn   lot 2      Frederick Thomas's shop

Five of the eight are built on — three by a documented store the owner's 2026-08-27
business-front clause seats there, three by the run's own parcel's yard buildings (two
lots carry both). **Three lots in the whole town carry nothing at all**, and every one
of those three reads free to the schedule: `blk_south_water_franklin` is `open` with 3
principal rooms and `blk_south_water_lasalle` with 6, dealt against exactly this ground.

T-1053 EMPTIED THAT TABLE, and it did so by answering the question the last paragraph
below asks rather than by re-deciding it. The eight rows are gone: every frontage entry
now declares exactly the ground its run stands across, the three yard buildings that
were standing in the yards of lots their households' roofs were not on have been
re-lotted onto the lots they serve, and the lots the owner's business-front clause was
reaching through the same list are named on a `business_front` field of their own — so
no lot in the town lost the ruling and no surrendered lot needed an `open_lots` reason
nobody had the evidence for. One did: `blk_south_water_franklin` lot 4, which carries
nothing at all now that the privy has left it, and the reason it can be written is that
the measurement is what found the lot empty. This survey therefore reports no idle
dealt lots today, and its self-test asserts that rather than asserting the population
it was written against.

So the headline figure was measuring the distance between two lists that T-0079 made
different ON PURPOSE, and reading it as waste. A run's deal is its STRIP —
`frontage_strip()` projects the dealt lots onto the face, requires them to adjoin, and
returns one continuous stretch that `check_frontage()` then holds every unit inside. To
re-deal a run only the lots it stands on would not free ground; it would make a new and
unsourced claim, that the rest of that face is not this run's frontage, and would owe
each surrendered lot a twelve-word `open_lots` reason nobody has the evidence to write.

The reservation is not free, and the one price it does pay is the right one: a dealt lot
is `built on by this parcel` in `generate_block_infill.py`'s four-class lot accounting,
so it cannot also be `named open in the recipe` or take a second principal roof. That IS
the reservation being registered. The single case where it cost something real — a
documented store refused the ground under it — the owner settled by rule in #371, and
`exclusive_lots` is why three of the eight lots above carry a store today.

What the ticket found, then, is its second half exactly: **the count was correct and
nobody could see it.** So this file is wired into `tools/check.sh` rather than left as a
command somebody remembers to run, and `--self-test` demonstrates the gate FAILING —
`blk_lake_clark` and both `blk_randolph_dearborn` deals sit at exactly 3 of 3, so one
synthetic roof on one of their lots is the fixture, and a gate nobody has watched fail
has not been tested.

    tools/measure_frontage_entitlement.py               the table
    tools/measure_frontage_entitlement.py --gate        no run over its own frontage
    tools/measure_frontage_entitlement.py --self-test   break it, in memory
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
RECIPE_PATH = DATA / "reconstruction" / "1835_platted_block_parcels.json"
LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"

sys.path.insert(0, str(ROOT / "tools"))

from plat_occupancy import exclusive_lots, lot_holders  # noqa: E402
from reconcile_665 import ROW_UNITS_PER_LOT  # noqa: E402


def distinct(ids) -> list[str]:
    """One lot's holder list, with each roof counted once, in the order it arrived.

    The whole of the behaviour `seated_lots` exists for (see below), and a named
    function rather than a comprehension because `survey()`'s injection path has to run
    THIS dedupe and not a second copy of it — otherwise `--self-test`'s "a roof listed
    twice is counted once" would be watching the fixture dedupe itself and would stay
    green with the real one deleted.
    """
    return list(dict.fromkeys(ids))


def seated_lots(grid: dict, datum: dict,
                exclude: set[str] | frozenset[str] = frozenset()
                ) -> dict[str, dict[int, list[str]]]:
    """`plat_occupancy.lot_holders`, with each lot's list reduced to distinct roofs.

    This module was written against a `seated_lots` of its own that deduped as it built
    the map. That function never reached `dev`: T-0233 salvaged this instrument alone,
    and by then #371 had independently given `plat_occupancy.lot_holders` the identical
    shape — `{block: {lot: [ids]}}` — for the owner's business-front clause. So the
    salvage imports dev's function rather than re-landing a second copy of it.

    The one behaviour that does not carry over is the dedupe, and it is not cosmetic
    here. `footprints()` yields EVERY committed phase, so a structure rebuilt on a
    footprint that seats on the same lot twice appears in that lot's list twice. Every
    caller on dev today reads the list for a NAME (`occupied_lots` takes `ids[0]`,
    the clause asks what is standing there), and a name is unharmed by a repeat. This
    module is the first caller that reads it as a COUNT, and a count is not: a
    two-phase rebuild would spend a lot's frontage twice and read a run over its
    ceiling that is not.

    Measured on the committed dataset 2026-08-27: **no lot lists any id twice**, so
    this changes no number today. It is here because the hazard is real and silent —
    the instrument would simply report a larger figure and look like a finding.

    Deliberately NOT pushed down into `lot_holders`: that function is shared with the
    gate and the schedule, its docstring promises "every structure standing on it", and
    narrowing a module eight callers rely on to suit one new reader is how a fix
    becomes a regression. The counting caller does the counting caller's work.
    """
    return {block: {index: distinct(ids) for index, ids in lots.items()}
            for block, lots in lot_holders(grid, datum, exclude).items()}


def run_ceiling(dealt_lots) -> int:
    """Units of party-line frontage the lots a run was dealt can carry.

    T-0079's figure, in T-0079's unit: the smallest lot on the committed grid carries
    23.56 m of frontage, the plat module keeps 1.5 m clear of a side line at each end
    of a run, and the committed party-line units average 6.072 m wide, so 3.39 units
    fit on the meanest lot in the town and the fourth does not.
    """
    return ROW_UNITS_PER_LOT * len(list(dealt_lots))


def frontage_load(dealt_lots, run_units, seated: dict[int, list[str]]
                  ) -> tuple[int, int, dict[int, list[str]]]:
    """(load, ceiling, the roofs already standing on the lots the run was dealt).

    `seated` is one block's slice of `plat_occupancy.seated_lots`, taken with the
    parcel's own records excluded — so what it names is everything the run did not
    build. The load is the run's units plus those roofs, because both are roofs on the
    same metres of frontage and the ceiling is a count of roofs.
    """
    standing = {index: list(seated.get(index, ())) for index in dealt_lots
                if seated.get(index)}
    load = int(run_units) + sum(len(ids) for ids in standing.values())
    return load, run_ceiling(dealt_lots), standing


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parcel_records() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """({block_id: everything this parcel built there}, {deal: its run's units}).

    A block may carry more than one deal (`blk_randolph_dearborn` carries two, on its
    two faces), so a run is identified by the recipe entry's own `programme_phase` and
    not by the block. Counting a block's runs together would read six units against one
    face's ceiling and refuse a town that is standing.
    """
    built: dict[str, list[str]] = {}
    units: dict[str, list[str]] = {}
    for path in sorted(STRUCTURES.glob("recon_1835_blk_*.json")):
        record = load(path)
        recon = record.get("reconstruction") or {}
        block = recon.get("block_id")
        if not block:
            continue
        built.setdefault(block, []).append(record["id"])
        if recon.get("frontage"):
            units.setdefault(recon["programme_phase"], []).append(record["id"])
    return built, units


def idle_class(holders: list[str], mine: set[str]) -> str:
    """What is actually standing on a lot the run was dealt and does not stand on.

    T-0233. "Carries none of its run's own roofs" is not "carries nothing", and reading
    the first as the second is what made eight lots look like hoarded ground. Three
    cases, and only one of them is empty frontage:

      `empty`     nothing stands there at all.
      `parcel`    the run's OWN parcel built there — a yard building serving the row,
                  which `generate_block_infill.py` permits precisely because the lot is
                  in `used`. The deal was spent, just not on a frontage unit.
      `documented` a researched roof stands at the street, seated by the owner's
                  2026-08-27 business-front clause. The run did not lose the ground; it
                  is sharing it, which is what the clause ruled it may do.

    The row carries the schedule's own reading of the same lot alongside this one —
    `exclusive_lots`, the map `reconcile_665.block_rooms()` counts its free lots out of
    — so the table can show that an idle lot is not withheld from the programme.
    """
    if not holders:
        return "empty"
    return "parcel" if set(holders) <= mine else "documented"


def survey(inject: dict[str, dict[int, list[str]]] | None = None) -> list[dict]:
    """One row per block face carrying a party-line run.

    `inject` adds roofs to a block's lots that are not on disk — `{block: {lot: [id]}}`,
    merged into the seated map after it is read. It is how `--self-test` puts a
    synthetic roof on a run that is at its ceiling and requires the gate to fail; the
    committed tree passes `inject=None` and reads exactly what it always read.
    """
    datum = load(DATA / "datum.json")
    grid = load(LOTS_PATH)
    blocks = {block["id"]: block for block in grid["blocks"]}
    recipe = load(RECIPE_PATH)
    built, units = parcel_records()
    available = exclusive_lots(grid, datum)
    inject = inject or {}

    rows: list[dict] = []
    for entry in recipe["blocks"]:
        frontage = entry.get("frontage")
        if not frontage:
            continue
        block_id = entry["block_id"]
        block = blocks.get(block_id)
        if block is None:
            continue
        mine = set(built.get(block_id, ()))
        seated = seated_lots({"blocks": [block]}, datum, exclude=mine).get(block_id, {})
        # every lot this run's own units seat on, by the same two tests
        theirs = seated_lots({"blocks": [block]}, datum).get(block_id, {})
        for index, ids in (inject.get(block_id) or {}).items():
            seated[index] = distinct(list(seated.get(index, ())) + list(ids))
            theirs[index] = distinct(list(theirs.get(index, ())) + list(ids))
        run = units.get(entry["programme_phase"], [])
        stands_on = sorted({index for index, ids in theirs.items()
                            if set(ids) & set(run)})
        dealt = list(frontage["lots"])
        load_n, ceiling, standing = frontage_load(dealt, len(run), seated)
        taken = set(available.get(block_id, ()))
        idle = {index: {"holders": list(theirs.get(index, ())),
                        "free_to_the_schedule": index not in taken}
                for index in dealt if index not in stands_on}
        for index, state in idle.items():
            state["state"] = idle_class(state["holders"], mine)
        rows.append({
            "block": block_id, "face": frontage["face"], "dealt": dealt,
            "stands_on": stands_on, "units": len(run), "load": load_n,
            "ceiling": ceiling, "standing": standing, "idle": idle,
        })
    return rows


def over_ceiling(rows: list[dict]) -> list[dict]:
    """Every run carrying more roofs than the lots it was dealt can hold."""
    return [r for r in rows if r["load"] > r["ceiling"]]


def report(rows: list[dict]) -> None:
    print(f"party-line frontage runs, dealt lots against the ground they stand on "
          f"({ROW_UNITS_PER_LOT} units per dealt lot)\n")
    print(f"{'block':<30} {'face':<6} {'dealt':<12} {'stands on':<12} "
          f"{'units':>5} {'load':>5} {'ceil':>5}  roofs already on the dealt lots")
    for row in rows:
        standing = ", ".join(f"lot {index}: {'+'.join(ids)}"
                             for index, ids in sorted(row["standing"].items())) or "—"
        print(f"{row['block']:<30} {row['face']:<6} "
              f"{str(row['dealt']):<12} {str(row['stands_on']):<12} "
              f"{row['units']:>5} {row['load']:>5} {row['ceiling']:>5}  {standing}")
    unused = sum(len(r["idle"]) for r in rows)
    print(f"\n{len(rows)} runs · {sum(r['units'] for r in rows)} units · "
          f"{unused} dealt lot(s) carry none of their run's own roofs")

    # T-0233. The line above is the one that read as a finding of waste, so the line
    # below is printed with it: what stands on those lots, and whether the schedule is
    # withholding them. It is not — `free to the schedule` is `exclusive_lots`, the map
    # `reconcile_665` counts its free lots out of, and it has never read a recipe's deal.
    idle = [(row["block"], index, state)
            for row in rows for index, state in sorted(row["idle"].items())]
    if not idle:
        return
    print(f"\nthose {len(idle)} lot(s), and what is standing on them")
    print(f"{'block':<30} {'lot':>4}  {'reads':<11} {'free to the schedule':<21} on it")
    for block, index, state in idle:
        who = ", ".join(state["holders"]) or "—"
        free = "yes" if state["free_to_the_schedule"] else "no"
        print(f"{block:<30} {index:>4}  {state['state']:<11} {free:<21} {who}")
    empty = [row for row in idle if row[2]["state"] == "empty"]
    print(f"\n{len(empty)} of them carry no roof at all"
          f"{': ' if empty else ''}"
          + ", ".join(f"{b} lot {i}" for b, i, _ in empty))
    withheld = [row for row in empty if not row[2]["free_to_the_schedule"]]
    print(f"{len(withheld) or 'none'} of those withheld from the 665-roof programme "
          f"— a dealt lot carries no footprint, so it reads free to `exclusive_lots` "
          f"and the schedule deals principal room against it (T-0233)")


def self_test() -> int:
    """Break the gate in memory and require it to fire.

    A check nobody has watched fail has not been tested, and this one passes on every
    tree it has ever been run on. The fixture the ticket named is the tightest run in
    the town: `blk_lake_clark` and both `blk_randolph_dearborn` deals stand at exactly
    `ROW_UNITS_PER_LOT` of `ROW_UNITS_PER_LOT`, so ONE more roof on one of their dealt
    lots is over the ceiling and nothing smaller is.
    """
    failures: list[str] = []

    def require(label: str, ok: bool, saw: object = "") -> None:
        if ok:
            print(f"  fires: {label}")
            return
        failures.append(label)
        print(f"  SELF-TEST FAIL: {label} — saw {saw!r}")

    clean = survey()
    require("the committed town is inside every run's own frontage",
            not over_ceiling(clean), [r["block"] for r in over_ceiling(clean)])

    # 1. the fixture: one synthetic roof on a lot a run at its ceiling was dealt.
    tight = [r for r in clean if r["load"] == r["ceiling"] and len(r["dealt"]) == 1]
    require("a run stands at exactly its own ceiling, so one roof is over it",
            bool(tight), [(r["block"], r["load"], r["ceiling"]) for r in clean])
    if not tight:
        return 1
    fixture = min(tight, key=lambda r: (r["block"], r["face"]))
    lot = fixture["dealt"][0]
    broken = survey(inject={fixture["block"]: {lot: ["synthetic_t0233_roof"]}})
    over = over_ceiling(broken)
    hit = [r for r in over if r["block"] == fixture["block"] and r["face"] == fixture["face"]]
    require(f"a roof on {fixture['block']} lot {lot} puts its run over the ceiling",
            bool(hit), [(r["block"], r["load"], r["ceiling"]) for r in over])
    if hit:
        require(f"…and it is over by exactly one roof: "
                f"{hit[0]['load']} against {hit[0]['ceiling']}",
                hit[0]["load"] == fixture["ceiling"] + 1,
                (hit[0]["load"], hit[0]["ceiling"]))
    require("…and it is the only run the fixture breaks", len(over) == 1,
            [r["block"] for r in over])

    # 2. the control. A gate that fires on an untouched tree is not measuring the roof.
    untouched = survey(inject={fixture["block"]: {lot: []}})
    require("an empty injection leaves every run where it was",
            not over_ceiling(untouched) and
            [r["load"] for r in untouched] == [r["load"] for r in clean],
            [r["load"] for r in untouched])

    # 3. the dedupe `seated_lots` exists for. A structure rebuilt on a footprint that
    #    seats twice on one lot must spend that lot's frontage ONCE — this module is the
    #    only caller that reads the holder list as a count, and a repeat would report a
    #    run over a ceiling it is inside.
    doubled = survey(inject={fixture["block"]: {lot: ["synthetic_t0233_roof",
                                                     "synthetic_t0233_roof"]}})
    twice = [r for r in doubled
             if r["block"] == fixture["block"] and r["face"] == fixture["face"]]
    require("a roof listed twice on one lot is counted once",
            bool(twice) and twice[0]["load"] == fixture["ceiling"] + 1,
            [r["load"] for r in twice])

    # 4. the classification. T-0233 wrote this against eight idle dealt lots standing in
    #    the committed town; T-1053 emptied that population — every frontage entry now
    #    declares exactly the ground its run stands across, so a dealt lot the run does
    #    not stand on no longer exists — and an assertion that the town HAS one would
    #    now be asserting the defect back. What is tested instead is the classifier
    #    itself, on the three holder shapes it exists to tell apart, and the invariant
    #    that whatever the town's idle lots are they read as one of the three.
    idle_rows = [r for r in clean if r["idle"]]
    require("no frontage entry declares a lot its run does not stand on",
            not idle_rows, [(r["block"], sorted(r["idle"])) for r in idle_rows])
    require("an idle lot with nothing on it reads empty",
            idle_class([], {"mine"}) == "empty", idle_class([], {"mine"}))
    require("an idle lot carrying only the parcel's own roof reads parcel",
            idle_class(["mine"], {"mine"}) == "parcel", idle_class(["mine"], {"mine"}))
    require("an idle lot carrying a roof the parcel did not build reads documented",
            idle_class(["a_store"], {"mine"}) == "documented",
            idle_class(["a_store"], {"mine"}))
    states = {state["state"] for row in clean for state in row["idle"].values()}
    require("every idle lot reads empty, parcel or documented",
            states <= {"empty", "parcel", "documented"}, sorted(states))

    if failures:
        print(f"\nSELF-TEST FAILED: {len(failures)} assertion(s) did not fire")
        return 1
    print("\n  self-test: every assertion fires when broken")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="fail if a run's frontage carries more roofs than it can")
    ap.add_argument("--self-test", action="store_true",
                    help="break the gate in memory and require it to fire")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    rows = survey()
    if not args.quiet:
        report(rows)

    if args.gate:
        over = over_ceiling(rows)
        for row in over:
            print(f"FAIL {row['block']} {row['face']} face: {row['units']} run unit(s) "
                  f"and {row['load'] - row['units']} roof(s) already standing on the "
                  f"{len(row['dealt'])} lot(s) it was dealt — {row['load']} against a "
                  f"ceiling of {row['ceiling']}", file=sys.stderr)
        if over:
            return 1
        print(f"\nOK — every run inside its own frontage: worst is "
              f"{max((r['load'], r['block']) for r in rows)[1]} at "
              f"{max(r['load'] for r in rows)} of "
              f"{max(rows, key=lambda r: r['load'])['ceiling']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
