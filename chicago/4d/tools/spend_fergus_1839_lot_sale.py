#!/usr/bin/env python3
"""Fergus 1839's Fort Dearborn Addition lot sale, spent on the people it names (T-0681).

    python3 tools/spend_fergus_1839_lot_sale.py             write the ledger and the cards
    python3 tools/spend_fergus_1839_lot_sale.py --check     everything re-derives; nothing drifted
    python3 tools/spend_fergus_1839_lot_sale.py --report    person by person, what they bid on
    python3 tools/spend_fergus_1839_lot_sale.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. T-0666 (PR #791) read the Fort Dearborn Addition lot sale of 10-24 June
1839 out of Fergus' Chicago Directory for 1839 — printed pages 47-49, 100 distinct bidders
— and crosswalked them against the town. Eleven bidders match a person this project holds a
card for. Not one of those eleven cards was told what the sale says about them, and three
of the eleven named a card that cited nothing the ruling rests on at all.

That three is not an estimate: `tools/research_spend_baseline.json` carries it as the
directories domain's write-hop ceiling, raised by T-0635 with the sentence "The number is 3,
it is T-0666's to pay, and T-0681 is filed to pay it… The ceiling comes back down to 0 when
T-0681 lands." This is that pass, and it pays EVERY match rather than the visible three: a
card that cites the volume only because Fergus' 1837 poll or its 1839 city register happened
to name the same household reads as written to the second hop while the lot sale itself has
reached nobody.

THE COUNT IS THE CROSSWALK'S, NOT THIS FILE'S. T-0685 (PR #935) settled four more bidders
while this pass was being written and the matches went from eleven to fifteen; the pass
picked them up on its next run because it reads `residents.matches` and holds no list of its
own. No number here is hard-coded, and `--check` re-derives the ledger from the crosswalk
rather than comparing it to a total somebody wrote down.

A SEPARATE PASS, NOT AN EXTENSION OF THE LATER-LISTS ONE, and the reason is the paragraph
already on those eight cards. `tools/spend_fergus_1839_later_lists.py` writes one paragraph
per person naming the two lists it reads; folding a third list into it would mean rewriting
101 paragraphs that are already correct about what they say, to add a sentence that is true
of eleven of them. Every previous pass in this series — civic, the later lists, the land
tract sales, the directories — is its own tool, its own ledger and its own marker, and this
one keeps that shape. A card met by two passes carries two paragraphs, each saying what its
own source says.

THE FOUR RULES, unchanged from passes 1-3 because the defect they guard against is the same.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED. This pass re-adjudicates nothing. It reads
     `residents.matches` and writes exactly those. The `contested` and `ambiguous` rows
     are rivals still standing; the surname-only rows are refusals; and the voter,
     letter-list and 1840-head pools match a row in another reading rather than a card in
     this town, so there is nothing to write them onto.

  2. TWO FIELDS AND NO OTHERS. A person gains the source id in `sources` and a paragraph in
     `note`. Not a grade, not an arrival, not a claim block, not a placement, and above all
     not `lives_at` — see rule 3. `--self-test` holds it by diffing a record through the
     applier and asserting the changed key set.

  3. THE LOT IS NOT A LOCATION, and the crosswalk says so itself: the Fort Dearborn
     Addition is the Beaubien, or Reservation, lands, which in July 1835 were the garrison's
     ground and were not platted into lots at all. A block and a lot number from this sale
     place no house, no shop and no household in the town this project builds. That sentence
     travels onto every card this pass writes, quoted rather than paraphrased.

  4. NO GRADE MOVES. A sale four years after the scene date is a second source about
     CONTINUED RESIDENCE, not about July 1835. T-0515 applies the ratified ladder against
     every source at once; this pass hands it the evidence and not the verdict.

THE LEDGER IS NOT A CROSSWALK, deliberately, and for the reason pass 1 gave:
`data/research/directories/fergus_1839_lot_sale_spend_1835.json` carries no "crosswalk" in
its name so that `measure_research_spend.py` does not read a record of WRITES as a second
adjudication and report the pass grading its own homework.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(Path(__file__).resolve().parent))

# THE ONCE-EACH RULE lives in one place (T-0846). `gaps` asks whether this pass's
# paragraph is PRESENT and `strays` whether an unruled card carries one; neither can
# see a card that carries it TWICE, which is what an add-only applier produces when the
# wording changes between runs. T-0677 measured that on this series and closed it in one
# tool; three copies later the copies had already drifted apart, so the rule is shared.
import spend_write_once  # noqa: E402
DIRECTORIES = ROOT / "data" / "research" / "directories"
LOTS = DIRECTORIES / "fergus_1839_lots_crosswalk_1835.json"
LEDGER = DIRECTORIES / "fergus_1839_lot_sale_spend_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1

# The volume, and the only id written onto a card. The crosswalk states it at the top of
# the file, and it is the same volume the later-lists pass reads: one book, three lists.
SOURCE_ID = "fergus_chicago_directory_1839"

# The sentence that says a paragraph is this pass's, so re-running it is idempotent and
# `--check` can find its own work without guessing. It must not be a prefix of, or contain,
# the later-lists pass's marker: the two passes meet on the same cards.
MARKER = ("FERGUS 1839'S FORT DEARBORN ADDITION LOT SALE — JUNE 1839 EVIDENCE, "
          "NEVER AN 1835 FACT.")

# A WORDING THIS PASS HAS REPLACED — the second half of the once-each rule (T-0846). An
# applier here is add-only (`if MARKER not in note`), so rewriting the paragraph makes a
# re-run APPEND a second one saying the same thing in different words rather than overwrite
# the first, and neither `gaps` nor `strays` can see it. T-0677 measured exactly that on
# `spend_land_sales.py`: thirty-one cards doubled, `tools/check.sh` green. Any MARKER this
# pass retires belongs in this tuple from the commit that retires it, and `--check` then
# refuses a card still carrying it. Empty means this pass has never changed its wording.
SUPERSEDED_MARKERS: tuple = ()

LADDER_LIMIT = (
    "This pass WRITES THE EVIDENCE AND MOVES NO GRADE. Under the ratified ladder (T-0513) a "
    "second independent source is what lifts a projected resident, and a lot sale four years "
    "after the scene date is a second source about CONTINUED RESIDENCE rather than about "
    "July 1835. T-0515 applies the ladder against every source at once; this pass hands it "
    "the evidence and not the verdict."
)

# What the sale is, in one clause, so a card carries the occasion and not just a date.
OCCASION = ("the sale of the Fort Dearborn Addition, 10-24 June 1839, printed in Fergus' "
            "Chicago Directory for 1839 at pages 47-49")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# --- what the file says ----------------------------------------------------------------

def lot_entry(bid: dict, lot: dict) -> dict:
    """One lot row of the sale table, reduced to what a card is told about it."""
    return {
        "claim_id": lot["claim"],
        "list": "ft_dearborn_addition_lot_sale_1839",
        "bidder_as_printed": bid.get("bidder_as_printed"),
        "block": lot.get("block"),
        "lot": lot.get("lot"),
        "amount_usd": lot.get("amount_usd"),
        "printed_page": lot.get("printed_page"),
        "describes_date": "1839-06",
        # The table's three shorthands, kept rather than flattened: a ditto mark under the
        # name above is not the name printed again, a brace that gathers this lot with the
        # one above it under a single name and a single price is not a name printed on this
        # row at all, and a block carried forward from an earlier row is not a block printed
        # on this one.
        "bidder_ditto": bool(lot.get("bidder_ditto")),
        "bidder_braced": bool(lot.get("bidder_braced")),
        "block_carried": bool(lot.get("block_carried")),
    }


def matches() -> list:
    """One row per PERSON, in the crosswalk's own order.

    A ledger that re-sorted its input would stop being a re-derivation of it, so the order
    here is `residents.matches` as the crosswalk files it.
    """
    rows = []
    for row in load(LOTS)["residents"]["matches"]:
        entries = [lot_entry(bid, lot)
                   for bid in (row.get("bids_1839") or [])
                   for lot in (bid.get("lots") or [])]
        rows.append({
            "household_id": row["household_id"],
            "person_id": row["person_id"],
            "name": row.get("name"),
            "source_id": SOURCE_ID,
            "grade_1835": row.get("grade_1835"),
            "rule": row.get("rule"),
            "entries": entries,
            "total_usd": sum(b.get("amount_read_usd") or 0
                             for b in (row.get("bids_1839") or [])),
            "prices_the_scan_destroyed": sum(
                b.get("lots_whose_price_the_scan_destroyed") or 0
                for b in (row.get("bids_1839") or [])),
        })
    return rows


def carry_rule() -> str:
    """The crosswalk's OWN limit, quoted rather than paraphrased."""
    return load(LOTS)["carry_rule"]


def what_it_does_not_give() -> str:
    """…and its own statement of what a bid may never be read as."""
    return load(LOTS)["what_the_sale_does_not_give"]


# --- what a card is told ---------------------------------------------------------------

def _cite(e: dict) -> str:
    where = "printed page %s" % e["printed_page"] if e.get("printed_page") else "unpaged"
    block = "block %s" % e["block"] if e.get("block") is not None else "an uncarried block"
    lot = "lot %s" % e["lot"] if e.get("lot") is not None else "an unread lot"
    amount = "$%s" % f"{e['amount_usd']:,}" if e.get("amount_usd") is not None else "no price the scan preserved"
    return "%s %s at %s (%s, %s)" % (block, lot, amount, e["claim_id"], where)


def shorthand_note(row: dict) -> str:
    """What the table printed and what it carried — never silently the same thing."""
    ditto = sum(1 for e in row["entries"] if e["bidder_ditto"])
    braced = sum(1 for e in row["entries"] if e.get("bidder_braced"))
    carried = sum(1 for e in row["entries"] if e["block_carried"])
    parts = []
    if ditto:
        parts.append("%d of those rows %s the bidder as a ditto mark under the name "
                     "above rather than the name itself"
                     % (ditto, "prints" if ditto == 1 else "print"))
    if braced:
        parts.append("%d %s no name and no price at all: a printer's brace gathers %s "
                     "with the lot above under one name and one amount, and that amount "
                     "is printed over the pair and is not divided here"
                     % (braced, "carries" if braced == 1 else "carry",
                        "it" if braced == 1 else "them"))
    if carried:
        parts.append("%d %s the block number forward from the last row that printed one"
                     % (carried, "carries" if carried == 1 else "carry"))
    if row["prices_the_scan_destroyed"]:
        parts.append("%d %s no price the scan preserved"
                     % (row["prices_the_scan_destroyed"],
                        "carries" if row["prices_the_scan_destroyed"] == 1 else "carry"))
    if not parts:
        return ""
    return ("The sale table's own shorthand, recorded and not flattened: %s. "
            % ("; ".join(parts)))


def paragraph(row: dict) -> str:
    """What one person's card is told, and the whole of it."""
    n = len(row["entries"])
    printed = sorted({e["bidder_as_printed"] for e in row["entries"]
                      if e.get("bidder_as_printed")})
    parts = [MARKER, "This person bid at %s." % OCCASION]
    if printed:
        parts.append("The bidder is printed as %s."
                     % " and ".join("\u201c%s\u201d" % q for q in printed))
    parts.append("%d lot row%s%s: %s."
                 % (n, "" if n == 1 else "s",
                    ", $%s in all" % f"{row['total_usd']:,}" if row["total_usd"] else "",
                    "; ".join(_cite(e) for e in row["entries"])))
    shorthand = shorthand_note(row).strip()
    if shorthand:
        parts.append(shorthand)
    parts.append(carry_rule())
    parts.append(what_it_does_not_give())
    parts.append("Identity by the crosswalk's own rule: %s "
                 "(data/research/directories/fergus_1839_lots_crosswalk_1835.json)."
                 % (row["rule"] or "stated in the crosswalk"))
    parts.append(LADDER_LIMIT)
    return " ".join(parts)


# --- the ledger ------------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = matches()
    counts = load(LOTS)["counts"]
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by tools/spend_fergus_1839_lot_sale.py. The ledger of T-0681: which "
            "of the Fort Dearborn Addition lot-sale crosswalk's resident matches "
            "were written onto the card they name, and what each card was told. It is a "
            "record of WRITES, not of adjudications — the adjudication is "
            "fergus_1839_lots_crosswalk_1835.json — and it deliberately carries no "
            "'crosswalk' in its name so that measure_research_spend.py does not count a "
            "write as a second ruling."),
        "generated_by": "tools/spend_fergus_1839_lot_sale.py",
        "ticket": "T-0681",
        "pass": "the Fort Dearborn Addition lot sale of June 1839",
        "source_id": SOURCE_ID,
        "reads": ["data/research/directories/fergus_1839_lots_crosswalk_1835.json"],
        "writes": "data/residents/households/*.json — persons[].sources and persons[].note",
        "carry_rule": carry_rule(),
        "what_the_sale_does_not_give": what_it_does_not_give(),
        "counts": {
            "matched_rulings": counts["residents_matched_one_bidder"],
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "lots_carried": sum(len(r["entries"]) for r in rows),
            "dollars_carried": sum(r["total_usd"] for r in rows),
            "lot_rows_bidder_dittoed": sum(1 for r in rows for e in r["entries"]
                                           if e["bidder_ditto"]),
            "lot_rows_bidder_braced": sum(1 for r in rows for e in r["entries"]
                                          if e.get("bidder_braced")),
            "lot_rows_block_carried": sum(1 for r in rows for e in r["entries"]
                                          if e["block_carried"]),
        },
        "not_written": [
            {
                "rule": "F1",
                "why": ("a `contested` or `ambiguous` row is a rival still standing: the "
                        "crosswalk did not choose between the bearers of the name, and a "
                        "card that cited the volume anyway would print an undecided "
                        "identity as a decided one"),
                "rulings": (counts["residents_ambiguous"]
                            + counts["residents_contested"]),
            },
            {
                "rule": "F2",
                "why": ("a surname-only agreement is a refusal in this crosswalk's own "
                        "rule — the directory lists forty-one Smiths — and refusals are "
                        "not spent"),
                "rulings": counts["residents_surname_only_refused"],
            },
            {
                "rule": "F3",
                "why": ("the voter, letter-list and 1840-head pools match a row in ANOTHER "
                        "reading rather than a person this town holds a card for. They are "
                        "corroboration between readings and there is no card to write them "
                        "onto; T-0515 is the pass that rules on the letter list"),
                "rulings": (counts["voters_matched_one_bidder"]
                            + counts["letter_list_matched_one_bidder"]
                            + counts["heads_1840_matched_one_bidder"]),
            },
            {
                "rule": "F4",
                "why": ("no placement is written. The Addition was the garrison's "
                        "reservation in 1835 and was not platted into lots at all, so its "
                        "block and lot number are ground that did not exist on the scene "
                        "date and can locate nobody on it"),
                "rulings": 0,
            },
        ],
        "people": [
            {
                "household_id": r["household_id"],
                "person_id": r["person_id"],
                "name": r["name"],
                "source_id": r["source_id"],
                "grade_1835": r["grade_1835"],
                "rule": r["rule"],
                "total_usd": r["total_usd"],
                "entries": r["entries"],
                "written": paragraph(r),
            }
            for r in rows
        ],
    }


# --- the write -------------------------------------------------------------------------

def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs. Two keys, and rule 2 is held here."""
    changed = False
    existing = person.get("sources") or []
    if SOURCE_ID not in existing:
        # SORTED IF IT ARRIVED SORTED. Most of these cards are minted by
        # tools/mint_civic_residents.py, which re-derives a person's sources as the sorted
        # union of what the ladder reads and what the card already carried. A plain append
        # therefore leaves a minted card one position away from its own derivation, and
        # that pass's --check fails with "does not match the derivation" — which is how
        # this was found, on hh_bronson_arthur and hh_king_nehemiah. A card whose order is
        # NOT sorted is carrying an order somebody chose, and this pass appends to it
        # rather than tidying it.
        grown = existing + [SOURCE_ID]
        person["sources"] = sorted(grown) if existing == sorted(existing) else grown
        changed = True
    note = (person.get("note") or "").strip()
    fresh = paragraph(row)
    if MARKER not in note:
        person["note"] = (note + " " + fresh).strip()
        changed = True
    elif fresh not in note:
        # THE PARAGRAPH IS REFRESHED, NOT LEFT (T-0779). This used to append or do
        # nothing, and doing nothing was wrong the moment the reading under it moved:
        # T-0779 corrected `O. II. Thompson` to O. H. Thompson off the page image and
        # hh_thompson_o_i went on printing the mangle, because its card already carried a
        # paragraph and this pass only ever looked for the marker. A card that quotes a
        # reading must quote the reading it has. The extent replaced is MARKER to the end
        # of this paragraph's own closing sentence: both are fixed strings, the paragraph
        # is contiguous because every pass appends at the end of the note, and the closing
        # sentence is taken at its FIRST occurrence at or after the marker so that a later
        # pass ending the same way cannot be swallowed.
        start = note.index(MARKER)
        tail = note.index(LADDER_LIMIT, start) + len(LADDER_LIMIT)
        person["note"] = (note[:start] + fresh + note[tail:]).strip()
        changed = True
    return changed


def apply(quiet: bool = False) -> int:
    touched = 0
    for row in matches():
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        if not path.exists():
            continue
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, hh)
    if not quiet:
        print("fergus 1839 lot sale: written onto %d resident record(s)" % touched)
    return touched


def build(quiet: bool = False) -> int:
    dump(LEDGER, ledger_doc())
    apply(quiet=quiet)
    if not quiet:
        print("wrote %s" % LEDGER.relative_to(ROOT))
    return 0


# --- the gate --------------------------------------------------------------------------

def _person(row: dict):
    path = HOUSEHOLDS / ("%s.json" % row["household_id"])
    if not path.exists():
        return None
    for person in load(path).get("persons") or []:
        if person.get("id") == row["person_id"]:
            return person
    return None


def _gaps_over(row: dict, person: dict) -> list:
    """gaps() for one already-loaded person — what the self-test needs and the gate reuses."""
    out = []
    if SOURCE_ID not in (person.get("sources") or []):
        out.append("%s/%s — matched by the crosswalk and the card does not cite %s"
                   % (row["household_id"], row["person_id"], SOURCE_ID))
    if MARKER not in (person.get("note") or ""):
        out.append("%s/%s — matched by the crosswalk and the card carries no paragraph"
                   % (row["household_id"], row["person_id"]))
    return out


def gaps(rows: list) -> list:
    """Every ruling has to be ON the record it names, or the ruling is only a file."""
    bad = []
    for row in rows:
        person = _person(row)
        if person is None:
            bad.append("%s/%s — the record the ruling names does not exist"
                       % (row["household_id"], row["person_id"]))
            continue
        bad += _gaps_over(row, person)
    return bad


def strays(rows: list) -> list:
    """…and a card may not carry this pass's paragraph without a ruling behind it."""
    ruled = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        for person in hh.get("persons") or []:
            if MARKER not in (person.get("note") or ""):
                continue
            if (hh.get("id"), person.get("id")) not in ruled:
                bad.append("%s/%s — carries this pass's paragraph and no crosswalk match "
                           "names them" % (hh.get("id"), person.get("id")))
    return bad


def doubles() -> list:
    """…and a card says this pass's source ONCE, however many passes have written it.

    The third direction, and the one `gaps` and `strays` are both blind to: `gaps` asks
    whether the paragraph is PRESENT and `strays` whether an unruled card carries one, so a
    card carrying it TWICE answers both correctly. T-0677 measured that hole on
    `spend_land_sales.py` — thirty-one cards each doubled by re-running a superseded version
    of the tool, and `tools/check.sh` green over all of it. T-0846 gives this pass the same
    rule, out of `tools/spend_write_once.py` so that six passes hold one implementation.
    """
    return spend_write_once.doubles(MARKER, SUPERSEDED_MARKERS, HOUSEHOLDS)


def check(quiet: bool = False) -> int:
    rows = matches()
    if not LEDGER.exists():
        print("   the ledger is missing: %s" % LEDGER.relative_to(ROOT))
        return 1
    if load(LEDGER) != ledger_doc():
        print("   %s no longer re-derives from the crosswalk — re-run the tool"
              % LEDGER.relative_to(ROOT))
        return 1
    bad = gaps(rows) + strays(rows) + doubles()
    if bad:
        for line in bad[:20]:
            print("   %s" % line)
        if len(bad) > 20:
            print("   …and %d more" % (len(bad) - 20))
        return 1
    if not quiet:
        print("fergus 1839 lot sale: %d lot row(s) on %d card(s), no strays, none written "
              "twice"
              % (sum(len(r["entries"]) for r in rows), len(rows)))
    return 0


def report() -> int:
    rows = matches()
    print("%-34s %-26s %5s %10s  %s" % ("household", "person", "lots", "usd", "pages"))
    print("-" * 88)
    for r in rows:
        pages = ",".join(str(p) for p in sorted({e["printed_page"] for e in r["entries"]
                                                 if e.get("printed_page")}))
        print("%-34s %-26s %5d %10s  %s" % (r["household_id"], r["person_id"],
                                            len(r["entries"]),
                                            f"{r['total_usd']:,}", pages))
    print("-" * 88)
    print("%d people, %d lot rows, $%s"
          % (len(rows), sum(len(r["entries"]) for r in rows),
             f"{sum(r['total_usd'] for r in rows):,}"))
    return 0


def self_test() -> int:
    fails = []

    def want(label, cond):
        if not cond:
            fails.append(label)

    rows = matches()
    want("the crosswalk must name at least one person", bool(rows))
    want("every row must name a household and a person",
         all(r["household_id"] and r["person_id"] for r in rows))
    want("every lot row must name the claim it was read into",
         all(e["claim_id"] for r in rows for e in r["entries"]))
    want("every paragraph must carry the marker",
         all(MARKER in paragraph(r) for r in rows))
    want("every paragraph must quote the crosswalk's own carry rule",
         all(carry_rule() in paragraph(r) for r in rows))
    want("every paragraph must say the lot is not a location",
         all(what_it_does_not_give() in paragraph(r) for r in rows))
    # The two markers meet on the same cards; neither may contain the other, or one pass's
    # gate would read the other pass's paragraph as its own.
    other = ("FERGUS 1839'S LATER LISTS — 1837 AND 1839 EVIDENCE, NEVER AN 1835 FACT.")
    want("this marker must not collide with the later-lists pass's",
         MARKER not in other and other not in MARKER)

    # Rule 2, held over a synthetic record: two keys move and no others.
    before = {"id": "x", "name": "X", "grade": "projected_resident",
              "sources": ["some_source"], "note": "Existing sentence.",
              "lives_at": {"value": None, "confidence": "reconstructed"}}
    after = json.loads(json.dumps(before))
    apply_to_person(after, rows[0])
    moved = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    want("the applier moved keys other than sources and note: %s" % sorted(moved),
         moved == {"sources", "note"})
    want("the grade must not move", after["grade"] == before["grade"])
    want("no placement may be written", after["lives_at"] == before["lives_at"])
    want("the earlier note must survive", before["note"] in after["note"])
    want("the citation must be added, not replaced", "some_source" in after["sources"])
    want("a sorted sources list must stay sorted",
         after["sources"] == sorted(after["sources"]))

    # …and an order somebody chose is appended to, not tidied.
    chosen = {"id": "x", "sources": ["z_source", "a_source"], "note": ""}
    apply_to_person(chosen, rows[0])
    want("an unsorted sources list must keep its order",
         chosen["sources"] == ["z_source", "a_source", SOURCE_ID])

    # …and it must be idempotent: a second application changes nothing.
    twice = json.loads(json.dumps(after))
    apply_to_person(twice, rows[0])
    want("a second application must change nothing", twice == after)

    # The gate must FIRE when its two failures are staged.
    stripped = json.loads(json.dumps(after))
    stripped["sources"] = ["some_source"]
    want("gaps must fire on a card that stopped citing the source",
         any("does not cite" in g for g in _gaps_over(rows[0], stripped)))
    silent = json.loads(json.dumps(after))
    silent["note"] = "Existing sentence."
    want("gaps must fire on a card that carries no paragraph",
         any("no paragraph" in g for g in _gaps_over(rows[0], silent)))

    # THE ONCE-EACH RULE, both directions (T-0846). `gaps` and `strays` are both blind to a
    # card that carries this pass's paragraph twice — the one answers "present", the other
    # "ruled" — and an add-only applier produces exactly that when the wording changes
    # between runs. The card the applier actually writes must stay silent; the same card
    # with the paragraph appended again, and the same card carrying a superseded wording
    # beside it, must both fault.
    want("the once-each rule must stay silent on the card the applier writes",
         spend_write_once.doubles_over("hh_x", after, MARKER, SUPERSEDED_MARKERS) == [])
    doubled = json.loads(json.dumps(after))
    doubled["note"] = doubled["note"] + " " + doubled["note"]
    want("the once-each rule must fire on a card carrying this pass's paragraph twice",
         any("2 times" in d for d in spend_write_once.doubles_over(
             "hh_x", doubled, MARKER, SUPERSEDED_MARKERS)))
    rival = json.loads(json.dumps(after))
    rival["note"] = rival["note"] + " A SUPERSEDED WORDING OF THE SAME PASS. …"
    want("the once-each rule must fire on a superseded paragraph left standing",
         any("superseded" in d for d in spend_write_once.doubles_over(
             "hh_x", rival, MARKER, ("A SUPERSEDED WORDING OF THE SAME PASS.",))))
    want("this pass must declare its superseded wordings as a tuple",
         isinstance(SUPERSEDED_MARKERS, tuple))

    for line in fails:
        print("   %s" % line)
    print("fergus 1839 lot sale self-test: %s" % ("FAILED" if fails else "ok"))
    return 1 if fails else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check(quiet=args.quiet)
    if args.report:
        return report()
    return build(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
