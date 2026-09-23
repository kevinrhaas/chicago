#!/usr/bin/env python3
"""`persons[].dated_bounds[]` has MORE THAN ONE OWNER, and this module is the rule (T-1332).

    python3 tools/dated_bounds_block.py --self-test   the merge rules, over built rows

WHY THIS EXISTS. T-1326 introduced the block and wrote it the only way a single owner ever
needs to: `person["dated_bounds"] = my_rows`, replaced whole, so a doubled or a superseded
row cannot survive a run. That is the right discipline and this module keeps it. What it
cannot survive is a SECOND pass, and T-1332 is the second pass — the land register's dated
appearances belong in the same block, because two blocks carrying one fact is the
duplication the queue exists to avoid, and the ticket says so in as many words.

Written naively, the second pass is a mutual wipe: whichever of the two ran last would own
the block and the other's `--check` would go red on 236 or 77 cards. Worse, it would go red
NON-DETERMINISTICALLY — `check.sh` runs the two gates in file order and a developer running
them in the other order would see the opposite failure.

So ownership is explicit and the ORDER IS TOTAL:

  * A ROW BELONGS TO THE PASS WHOSE SOURCE IT CITES. `sources` is already how T-1326's own
    stray check decides what is its to police (`b["sources"] == [SOURCE_ID]`), so this
    module makes that the declaration rather than a coincidence. One source id, one owner,
    stated in `OWNERS` below.
  * A PASS REPLACES ITS OWN GROUP AND TOUCHES NO OTHER. `merge()` substitutes the caller's
    rows for the caller's group and carries every other group through unchanged.
  * THE GROUPS ARE ORDERED BY `OWNERS`, NOT BY WHO RAN LAST. That is what makes both
    passes' byte-for-byte `--check` true at the same time, in either run order. A row
    citing a source no owner claims is a fault the owning pass's stray check reports; it is
    carried through last rather than dropped, because silently deleting evidence is worse
    than reporting it.
"""
from __future__ import annotations

import argparse
import json
import sys

BLOCK = "dated_bounds"

# source id -> the pass that owns every row citing it. The order of this tuple IS the
# order the groups appear in on the card.
OWNERS = (
    ("chicago_voter_lists_1833_1835_irad", "tools/spend_civic_roll_bounds.py"),
    ("isa_public_domain_land_tract_sales", "tools/spend_land_sale_bounds.py"),
    # T-1343 IS ONE PASS AND TWO OWNERS, because the town printed two papers and a row is
    # owned by the source it cites. `tools/spend_press_bounds.py` writes both groups and
    # replaces each of them whole; splitting them here rather than giving the pass one
    # synthetic "press" source keeps the rule above literally true — one source id, one
    # owner — and keeps the Democrat's rows and the American's in a stated order.
    ("chicago_democrat_1833_1835", "tools/spend_press_bounds.py"),
    ("chicago_american_1835", "tools/spend_press_bounds.py"),
)
OWNED = tuple(source for source, _ in OWNERS)


def owner_of(row) -> str | None:
    """The source id whose owner wrote this row, or None if no owner claims it."""
    if not isinstance(row, dict):
        return None
    sources = row.get("sources")
    if not isinstance(sources, list) or len(sources) != 1:
        return None
    return sources[0] if sources[0] in OWNED else None


def block_of(person: dict) -> list:
    block = person.get(BLOCK)
    return block if isinstance(block, list) else []


def mine(person: dict, source_id: str) -> list:
    """The rows on this card that belong to the pass citing `source_id`."""
    return [row for row in block_of(person) if owner_of(row) == source_id]


def merge(person: dict, source_id: str, rows: list) -> list:
    """The block this card should carry once `source_id`'s owner has written `rows`."""
    groups = {source: [] for source in OWNED}
    groups[source_id] = list(rows)
    unclaimed = []
    for row in block_of(person):
        owner = owner_of(row)
        if owner is None:
            unclaimed.append(row)
        elif owner != source_id:
            groups[owner].append(row)
    merged = []
    for source in OWNED:
        merged.extend(groups[source])
    return merged + unclaimed


def insert_after(row: dict, key: str, value, after: str) -> None:
    """One field, in a stable slot — the convention `resident_mint_carry` already uses.

    A NEW KEY APPENDED AT THE END IS NOT A STABLE SLOT, and two gates measure that rather
    than assert it: `tools/spend_person_sex_age.py --check` and
    `tools/reconstruct_sex_age.py` both re-derive a whole card and compare it byte for
    byte, and both pop `sex`, `sex_basis`, `age_band` and `birth_year` and re-append them.
    A block written after those keys therefore lands BEFORE them on the next re-derivation
    and 235 cards read as drift — measured, on T-1326's branch, before this existed. The
    slot is immediately after `sources`, which every person these passes write to carries,
    because the block is evidence and belongs beside the sources it cites.
    """
    rebuilt = {}
    for old_key, old_value in row.items():
        rebuilt[old_key] = old_value
        if old_key == after:
            rebuilt[key] = value
    if key not in rebuilt:
        rebuilt[key] = value
    row.clear()
    row.update(rebuilt)


def write(person: dict, source_id: str, rows: list) -> bool:
    """Put `rows` on the card as `source_id`'s group. True if the card changed."""
    merged = merge(person, source_id, rows)
    if block_of(person) == merged and (BLOCK in person or not merged):
        return False
    if BLOCK in person:
        person[BLOCK] = merged
    else:
        insert_after(person, BLOCK, merged, "sources")
    return True


def self_test() -> int:
    failures = []

    def ok(label, cond):
        print("  %s %s" % ("ok:  " if cond else "FAIL:", label))
        if not cond:
            failures.append(label)

    # T-1343 ADDED A THIRD AND FOURTH OWNER, so the fixtures name the two they exercise
    # rather than unpacking the tuple — the point of every case below is that a pass
    # rewrites ITS OWN group, and that is the same argument at two owners or at twenty.
    civic, land = OWNED[0], OWNED[1]
    press = OWNED[2]
    c1 = {"record_id": "poll_1835_001", "sources": [civic]}
    l1 = {"record_id": "ls0959", "sources": [land]}
    l2 = {"record_id": "ls0960", "sources": [land]}
    p1 = {"record_id": "chicago_democrat_1834_12_03#c014", "sources": [press]}
    stray = {"record_id": "x", "sources": ["somebody_elses_volume"]}

    ok("a row is owned by the single source it cites", owner_of(c1) == civic)
    ok("a row citing two sources is owned by neither",
       owner_of({"sources": [civic, land]}) is None)
    ok("a row citing an unclaimed source is unowned", owner_of(stray) is None)

    person = {"id": "p", "sources": ["s"], BLOCK: [c1], "sex": "male"}
    ok("a pass writing its own group leaves the other group alone",
       merge(person, land, [l1, l2]) == [c1, l1, l2])
    ok("…and the civic pass rewriting its own group does not move the land group",
       merge({BLOCK: [c1, l1, l2]}, civic, [c1]) == [c1, l1, l2])
    ok("the group order is OWNERS' order and not the order the passes ran in",
       merge({BLOCK: [l1, l2]}, civic, [c1]) == [c1, l1, l2])
    ok("a pass writing an empty group removes its own rows and only those",
       merge({BLOCK: [c1, l1, l2]}, land, []) == [c1])
    ok("an unclaimed row is carried through rather than deleted",
       merge({BLOCK: [stray, c1]}, land, [l1]) == [c1, l1, stray])
    ok("`mine` sees only the caller's rows",
       mine({BLOCK: [c1, l1, l2, stray]}, land) == [l1, l2])
    ok("a third owner writing its group leaves the first two alone",
       merge({BLOCK: [c1, l1, l2]}, press, [p1]) == [c1, l1, l2, p1])
    ok("…and an earlier owner rewriting its group does not move the third's",
       merge({BLOCK: [c1, l1, l2, p1]}, civic, [c1]) == [c1, l1, l2, p1])
    ok("every owned source names exactly one owner",
       len(dict(OWNERS)) == len(OWNERS) == len(OWNED))

    card = {"id": "p", "grade": "projected", "sources": ["s"], "note": "n"}
    ok("the first write lands in the slot after `sources`, not at the end",
       write(card, land, [l1]) and list(card) == ["id", "grade", "sources", BLOCK, "note"])
    ok("a second identical write changes nothing", write(card, land, [l1]) is False)
    ok("a write by the other owner changes the card once",
       write(card, civic, [c1]) and card[BLOCK] == [c1, l1])
    before = json.dumps(card, sort_keys=True)
    ok("…and is idempotent too", write(card, civic, [c1]) is False
       and json.dumps(card, sort_keys=True) == before)

    print("  %d failure(s)" % len(failures))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
