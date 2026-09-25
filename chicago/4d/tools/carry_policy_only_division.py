#!/usr/bin/env python3
"""T-1523: the policy-only rung's dealt division, carried onto the household card.

    tools/carry_policy_only_division.py --build      write the block onto every rung-5 card
    tools/carry_policy_only_division.py --check      re-derive, diff, re-assert every limit
    tools/carry_policy_only_division.py --self-test  break the assertions and require them to fire
    tools/carry_policy_only_division.py --report     print the counts

WHAT THIS IS FOR.

`tools/seat_known_1835.py` deals rung 5 of the address book (T-1522): the 1,305
households no source places anywhere get a division off the reconstruction order
book's own household target by division, and a class off the town model's employment
distribution. That deal lived in `data/reconstruction/1835_address_book.json` AND
NOWHERE ELSE, so the household card and `data/residents/index.json` still read
`unplaced` for every one of them and the People view's division filter was short of
1,305 households — 2,041 of 3,292 people in it had no division to filter by. T-1522's
own record named this carry-back as owed, and this file is it.

THE SCALAR `division` ON THE CARD DOES NOT MOVE, AND THAT IS DELIBERATE.

A dealt division is not a division a source states, and three things in the tree read
the card's own `division` as if it were:

  * `rebuild_resident_index.DWELLING_CLAUSES` counts `a_stated_division` — a division
    that is not `unplaced` — as the clause under which T-1476's ruling makes a record a
    HOUSE. Writing the dealt value into the scalar would silently turn 1,305 people
    awaiting a household into houses and move the `houses` count by six times its size,
    on a deal that claims no roof at all.
  * `seat_known_1835.py`'s own assertion 13 defines rung 5 as exactly the households
    whose record reads `unplaced`. Moving the scalar would empty the rung it is derived
    from — the deal would erase its own input on the next `--build`.
  * The order book, the lodging model and the staffing mint apportion by the card's
    division. A dealt division spends no bucket (T-1522's `nothing_is_minted`), so it
    must not arrive where a bucket is counted.

So the dealt value is carried as its OWN block, `division_reconstructed`, and the
scalar keeps saying what the sources say: nothing. The readers that want a division to
show a visitor take the block; the readers that want a division a source states take
the scalar; and neither can be mistaken for the other.

IT IS CARRIED THROUGH THE CARRY SLOT THE MINT STAGES USE.

`tools/carry_stage_blocks.py` (T-1169) is how a reconstruction stage writes onto a
record four mints re-derive byte for byte: the stage marks every block it owns with
`written_by_stage`, and each mint re-derives its record and then seats the marked
blocks back into it. This block carries that marker, and `carry_stage_blocks.AFTER`
seats it directly after `division` — so a mint's `--build` re-derives a carried card
byte for byte and cannot delete the carry.

WHAT THE BLOCK SAYS, AND WHY EACH FIELD IS THERE.

    value            the dealt division
    confidence       `reconstructed`, always. No source is behind either half of it.
    tier             the same word, for the attribute-tier readers
    band             the band the deal put this household in, division and clause
    clause           the placement-policy clause the dealt class falls under
    note             the sentence a visitor reads: that BOTH halves are dealt, from
                     which committed model, and that it is the weakest seat the ladder
                     makes
    basis            the file and the member the deal came off, so it can be re-read
    seed             the digest that placed it, both axes, verbatim from the row
    replaceable_by   what retires it: any source that places this household at all
    written_by_stage the carry slot's marker

WHAT THIS FILE REFUSES TO DO. It invents nothing. Every field above is copied or
restated from the address-book row that already committed it, and `--check` re-derives
the whole block from that row and compares it to what is on disk. A card carrying this
block that the book deals no division for is a FAULT rather than a stale leftover, and
a rung-5 row whose card does not carry the block is a fault too — a ledger and a layer
that can disagree in silence is how T-1522's deal came to be invisible in the first
place.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

ADDRESS_BOOK = ROOT / "data" / "reconstruction" / "1835_address_book.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

TICKET = "T-1523"
STAGE = "policy_only_division"
MARKER = "written_by_stage"
BLOCK = "division_reconstructed"
RUNG = "policy_only"

# The one place a reader is sent to re-read the deal itself.
BASIS_NOTE = ("data/reconstruction/1835_address_book.json#policy_only_deal — the "
              "division off the reconstruction order book's household target by "
              "division, the class off the town model's employment_shape_1840 "
              "distribution, dealt exact by largest remainder on a seeded order.")

REPLACEABLE_BY = {
    "kind": "household",
    "match": "any source that places this household in a division or nearer",
}


class Refused(Exception):
    """A limit this pass will not cross."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc: dict) -> str:
    """One space of indent, exactly as the four mints write a household card.

    `mint_documented_residents.dumps` is the shape every card on disk carries, and
    each mint's --check compares the file it derives BYTE for byte. Writing a card
    at any other indent reformats the whole file and puts all four into drift on
    every household this pass touches — measured here, at indent 2, on 1,305 cards.
    """
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def dealt_rows() -> list[dict]:
    """The address book's rung-5 household rows, in the book's own order."""
    book = load(ADDRESS_BOOK)
    return [r for r in book["rows"]
            if r.get("kind") == "household" and r.get("rung") == RUNG]


def block_for(row: dict) -> dict:
    """The block this stage writes for one rung-5 row, derived from the row alone."""
    seat = row["seat"]
    return {
        "value": seat["division"],
        "confidence": "reconstructed",
        "tier": "reconstructed",
        "band": seat["id"],
        "clause": seat["clause"],
        "note": row["words"],
        "basis": {"kind": "model", "id": "policy_only_deal", "note": BASIS_NOTE},
        "seed": row["seed"],
        "replaceable_by": dict(REPLACEABLE_BY),
        MARKER: STAGE,
    }


def carded() -> dict[str, dict]:
    """Every household card that carries this stage's block today, by household id."""
    out: dict[str, dict] = {}
    for path in sorted(HOUSEHOLDS.glob("hh_*.json")):
        doc = load(path)
        block = doc.get(BLOCK)
        if isinstance(block, dict) and block.get(MARKER) == STAGE:
            out[doc.get("id") or path.stem] = block
    return out


def seated(doc: dict, block: dict) -> dict:
    """`doc` with the block seated directly after `division`, so field order is fixed.

    The same seat `carry_stage_blocks.AFTER` gives it, so a mint that re-derives this
    record and carries the block back writes the identical bytes.
    """
    out: dict = {}
    for key, value in doc.items():
        if key == BLOCK:
            continue
        out[key] = value
        if key == "division":
            out[BLOCK] = block
    if BLOCK not in out:
        out[BLOCK] = block
    return out


def assertions(rows: list[dict], cards: dict[str, dict]) -> None:
    """Every limit this pass holds, over the book's rows and the cards on disk.

    The order matters: a block's own SHAPE is held before it is held against the row it
    must re-derive from. Checked the other way round, the re-derivation diff catches
    every mutation first and each shape limit below would be proved by a refusal it did
    not make — a self-test firing the wrong assertion is worse than no self-test.
    """
    want = {row["id"]: block_for(row) for row in rows}

    # 1. The book and the layer name the same households. Either direction is a fault:
    # a dealt row whose card does not carry it is the invisibility T-1522 left behind,
    # and a carried card the book deals nothing for is a block nothing re-derives.
    missing = sorted(set(want) - set(cards))
    if missing:
        raise Refused(f"{len(missing)} rung-5 household(s) the book deals a division for "
                      f"carry no {BLOCK} block, so the town still cannot see them: "
                      f"{', '.join(missing[:5])}")
    stray = sorted(set(cards) - set(want))
    if stray:
        raise Refused(f"{len(stray)} household(s) carry a {BLOCK} block the address book "
                      f"deals no division for: {', '.join(stray[:5])}")

    # 2. Nothing on a card is dressed above its tier. Both halves of the band are dealt,
    # so the block says `reconstructed` and its note says it is dealt.
    for hid, block in sorted(cards.items()):
        if block.get("confidence") != "reconstructed" or block.get("tier") != "reconstructed":
            raise Refused(f"{hid}: a dealt division is reconstruction and must say so")
        if "dealt" not in (block.get("note") or ""):
            raise Refused(f"{hid}: a dealt division whose note does not say it is dealt")
        if not block.get("seed") or "division:" not in block["seed"]:
            raise Refused(f"{hid}: a dealt division must carry the digest that placed it")
        if not block.get("replaceable_by"):
            raise Refused(f"{hid}: a reconstructed attribute must say what retires it")

    # 3. No coordinate, lot or roof rides in on a dealt band. T-1522's deal claims none
    # and neither may its carry.
    for hid, block in sorted(cards.items()):
        for forbidden in ("lot", "lot_id", "coordinates", "local_enu_m", "structure",
                          "structure_id", "lives_at"):
            if forbidden in block:
                raise Refused(f"{hid}: a dealt band carries no {forbidden}")

    # 4. Every block re-derives from its own row, field for field. This is what makes the
    # block a copy of a committed adjudication rather than a second opinion on it.
    for hid in sorted(want):
        if cards[hid] != want[hid]:
            raise Refused(f"{hid}: its {BLOCK} block does not re-derive from the address "
                          "book row that deals it")

    # 5. The scalar the mints own is untouched. This is the whole reason the block
    # exists: `rebuild_resident_index`'s `a_stated_division` dwelling clause reads the
    # scalar, so a dealt division arriving there would make 1,305 houses out of nothing.
    for hid in sorted(want):
        path = HOUSEHOLDS / f"{hid}.json"
        if not path.exists():
            raise Refused(f"{hid}: the book deals a division for a household with no card")
        if (load(path).get("division") or "unplaced") != "unplaced":
            raise Refused(f"{hid}: its own `division` no longer reads `unplaced`. The "
                          "dealt division belongs in the block, never in the scalar — "
                          "rung 5 IS the households whose record places them nowhere, so "
                          "moving the scalar would erase the rung it is derived from")

    # 6. The carry slot is wired, read from the source rather than trusted. A mint that
    # stopped carrying would delete every block above on its next --build.
    import carry_stage_blocks
    if carry_stage_blocks.AFTER.get(BLOCK) != "division":
        raise Refused(f"carry_stage_blocks.AFTER does not seat {BLOCK} after `division`, "
                      "so a mint would re-seat it elsewhere and its own byte comparison "
                      "would drift")


def build(write: bool = True) -> int:
    rows = dealt_rows()
    changed = 0
    for row in rows:
        path = HOUSEHOLDS / f"{row['id']}.json"
        if not path.exists():
            print(f"  FAIL {row['id']}: rung 5 names a household with no card on disk")
            return 1
        doc = load(path)
        block = block_for(row)
        if doc.get(BLOCK) == block:
            continue
        changed += 1
        if write:
            path.write_text(dumps(seated(doc, block)), encoding="utf-8")
    # A card carrying the block the book no longer deals is removed, not left behind.
    ids = {row["id"] for row in rows}
    for hid in sorted(set(carded()) - ids):
        path = HOUSEHOLDS / f"{hid}.json"
        doc = load(path)
        doc.pop(BLOCK, None)
        changed += 1
        if write:
            path.write_text(dumps(doc), encoding="utf-8")
    print(f"  {'wrote' if write else 'would write'} {changed} card(s); "
          f"{len(rows)} rung-5 household(s) carry a dealt division")
    return 0


def check() -> int:
    rows = dealt_rows()
    try:
        assertions(rows, carded())
    except Refused as exc:
        print(f"  FAIL {exc}")
        return 1
    print(f"  OK: {len(rows)} rung-5 household(s) carry the division the address book "
          f"deals them, every block re-derived from its own row, and every card's own "
          f"`division` still reads `unplaced`")
    return 0


def report() -> int:
    rows = dealt_rows()
    by_division: dict[str, int] = {}
    for row in rows:
        d = row["seat"]["division"]
        by_division[d] = by_division.get(d, 0) + 1
    print(f"{TICKET} — the policy-only rung's dealt division, on the card")
    print(f"  rung-5 households: {len(rows)}")
    for d, n in sorted(by_division.items()):
        print(f"    {d:<14} {n}")
    print(f"  cards carrying the block: {len(carded())}")
    return 0


def self_test() -> int:
    """Break every limit above on purpose and require each one to fire.

    The rows and the cards are fixtures, not the committed layer: an assertion proved by
    mutating the real tree is an assertion that can only be tested once.
    """
    faults: list[str] = []
    fired: list[str] = []

    row = {
        "id": "hh_fixture", "kind": "household", "rung": RUNG,
        "seat": {"kind": "division_band", "id": "west/labourer_dwellings",
                 "division": "west", "clause": "labourer_dwellings"},
        "tier": "reconstructed",
        "words": "No source places this household anywhere, so both halves of this band "
                 "are dealt rather than read.",
        "seed": "hh_fixture|T-1522|division:aaaa|class:bbbb",
        "band": {"band": "west/labourer_dwellings", "clause": "labourer_dwellings"},
    }
    good = block_for(row)

    def fires(name, rows, cards):
        fired.append(name)
        try:
            assertions(rows, cards)
        except Refused as exc:
            print(f"  fires: {name} -> {str(exc)[:110]}")
            return
        faults.append(name)

    def holds(name, rows, cards):
        fired.append(name)
        try:
            assertions(rows, cards)
        except Refused as exc:
            faults.append(name)
            print(f"  FAIL {name} should hold and refused: {str(exc)[:110]}")
            return
        print(f"  holds: {name}")

    # The fixture household has no card on disk, so limit 4 reads a missing card. It is
    # exercised against the committed layer instead, at the end.
    import carry_stage_blocks
    real = dealt_rows()[:1]
    real_id = real[0]["id"]

    holds("one dealt row whose card carries the right block",
          real, {real_id: block_for(real[0])})
    fires("a dealt row whose card carries nothing", real, {})
    fires("a card carrying a block the book deals nothing for",
          real, {real_id: block_for(real[0]), "hh_not_dealt": good})
    fires("a block that does not re-derive from its own row",
          real, {real_id: {**block_for(real[0]), "value": "north"}})
    fires("a dealt division dressed above its tier",
          real, {real_id: {**block_for(real[0]), "confidence": "inferred"}})
    fires("a dealt division whose note stops saying it was dealt",
          real, {real_id: {**block_for(real[0]), "note": "This household lived somewhere."}})
    fires("a dealt division that loses the digest that placed it",
          real, {real_id: {**block_for(real[0]), "seed": ""}})
    fires("a dealt division with nothing that would retire it",
          real, {real_id: {**block_for(real[0]), "replaceable_by": None}})
    fires("a dealt band that carries a roof",
          real, {real_id: {**block_for(real[0]), "structure_id": "x"}})

    # Limit 6 — the wiring. Unwire the carry slot in memory and require the refusal.
    was = carry_stage_blocks.AFTER.pop(BLOCK, None)
    fires("the carry slot stops seating the block after `division`",
          real, {real_id: block_for(real[0])})
    if was is not None:
        carry_stage_blocks.AFTER[BLOCK] = was

    # Limit 4 — the scalar. Proved by seating a block on a household whose own
    # `division` a source DOES state, which is what moving the scalar would look like.
    placed = None
    for path in sorted(HOUSEHOLDS.glob("hh_*.json")):
        doc = load(path)
        if (doc.get("division") or "unplaced") != "unplaced":
            placed = doc["id"]
            break
    if placed is None:
        faults.append("no household with a stated division to test limit 4 against")
    else:
        fake = {**row, "id": placed}
        fires("a dealt division on a household whose record states one",
              [fake], {placed: block_for(fake)})

    # And the block's own shape, which the derivation must keep.
    if good[MARKER] != STAGE:
        faults.append("the block does not carry the carry slot's marker")
    if good["value"] != "west" or good["band"] != "west/labourer_dwellings":
        faults.append("the block does not restate its own row's band")

    print(f"  {len(fired)} assertion(s) exercised")
    for f in faults:
        print(f"  FAIL {f}")
    return 1 if faults else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --build, derive and report without writing")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.build:
        return build(write=not args.dry_run)
    if args.check:
        return check()
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
