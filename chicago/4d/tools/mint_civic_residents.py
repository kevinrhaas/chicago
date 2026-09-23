"""The people the town's own lists name and the residents layer never held (T-0514).

    python3 tools/mint_civic_residents.py --build      write
    python3 tools/mint_civic_residents.py --check      re-derive and diff
    python3 tools/mint_civic_residents.py --report     the mint and every refusal
    python3 tools/mint_civic_residents.py --scale      what this pass did to the town
    python3 tools/mint_civic_residents.py --gate       the invariants this pass owes
    python3 tools/mint_civic_residents.py --self-test  those assertions, broken on purpose

WHAT THIS PASS IS, AND THE RULING IT APPLIES.

The owner ratified a grading ladder on 2026-09-03 — quoted in full in T-0514 and in
`docs/RESEARCH/resident-grading-policy.md` — and T-0513 spent it: `tools/consolidate_
resident_evidence.py --build` reads the seven source domains, clusters them into
identities, and writes `data/research/residents/grading_proposal.json`, which says per
identity what the ladder makes of it. That file is a PROPOSAL and nothing in it was ever
written onto a card. Measured on `dev` before this pass: of the 85 men on the 1835 poll
list only 37 had even a surname in the residents layer. Half the voter-list men — Bread,
Pixby, Kennicott, Ulrich, Trowbridge, Alvin Calhoun — were in no record at all, and the
muster rolls, the tax list, the St Cyr register and the death notices were in the same
position.

This pass writes those people. It mints a household and a person for every identity the
proposal grades `attested` or `inferred` (`projected_resident` included) that the town
does not already carry, on the evidence of the CIVIC lists (poll, tax, muster), the
CHURCH register, the contemporary PRESS, the BOOKS (the two directories and the old
settlers' death notices) and the 1840 CENSUS — every domain except the post office's
lists of uncalled-for letters, which belongs to the pass beside this one.

NO COUNT IS WRITTEN DOWN HERE, DELIBERATELY, for the reason
`mint_letter_list_residents.py` gives at length: the corpus grows most weeks the loop
runs and a figure copied into prose is wrong by the next transcription. Run `--report`
for the mint and every refusal, `--scale` for what the pass is worth to the town.

WHERE IT SITS AMONG THE MINTS, AND WHY IT IS BESIDE THE LETTER LISTS RATHER THAN ABOVE.

T-0514 asked for this pass ABOVE `mint_letter_list_residents.py` in the precedence
`mint_documented_residents.MINTED_PREFIXES` documents, so that where two passes reach
for one family name the better-evidenced one keeps it. Working it showed the precedence
is not what these two passes need, and refusal 3 is why.

That refusal makes the two pools DISJOINT by construction: an identity whose only source
inside the scene year is a post-office letter list is refused here, because the pass
beside this one has already ruled on exactly that pool and the owner's ruling of
2026-08-30 held all of it. Nothing this pass mints rests on a letter list, and nothing
the letter-list pass mints rests on anything else. Two passes over disjoint pools do not
need a precedence between them.

What they do need is not to read each other's output as a prior claim, and that IS a
change to the family-name test: `town_family_names`'s `skip` now carries `("civic",
"hh_civic_")` in all three older mints. The reason is that refusal — "the town already
names a <Surname>" — is a proxy for identity resolution over evidence that is a bare
name, and it is the right proxy there: a letter addressed to `Smith` at Chicago is
probably the Smith the town already holds. This pass does not need the proxy. Its
identities come from the consolidation, which resolves on surname AND forename
signature against every domain at once, and refusal 2 hands back every identity that
resolution reaches. Letting the older passes see these households instead would retire
hundreds of committed letter-list records on a surname collision alone — a deletion the
owner has not ruled on, and the opposite of the one he did make.

WHAT THE RECORD CLAIMS, AND WHAT IT REFUSES TO.

The same claim the three passes before it make, and no more: a PERSON, inside a
household container that is the only way `data/residents/` can carry one. `division` is
`unplaced`; `lives_at` and `works_at` are null with the note saying why — the placement
sweep assigns homes and workplaces once the resident list is complete, which is the
owner's own sequencing and not this pass's to pre-empt. `occupation` reads
`none_recorded`, the residents vocabulary's own word for an absent record: a poll list,
a muster roll and a baptismal entry each print a name and no trade, and where a later
directory prints one it is a trade of 1843, which T-0633 exists to back-project under a
rule this pass does not have. `origin`, `party_size_on_arrival`, `reason_for_coming` and
the family are each written unattested in their own block. No figure is drawn (L1).

`arrival` is a BOUND and says so: `not_later_than` the earliest record inside the scene
year that names the person, at that record's own precision — a full date where the
paper gives one, the year's end where a list gives only a year. Where that bound falls
after 1 July 1835 the validator warns that it straddles the scene date; the note says so
in words, which is what the validator asks for, and `present_on_scene_date` is
`uncertain` rather than `present` for exactly those people.

`present_on_scene_date` is `present` only where the record BRACKETS the day — the person
is named at Chicago at or before 1 July 1835 and named again at or after it. Everyone
else is `uncertain` with the reason: the lists stop before the scene date and nothing
follows them to it. `uncertain` rather than dropped is the distinction index.json draws
for Jeremiah Porter, and it is a finding, not a gap.

THE EVIDENCE BLOCKS, and one deviation from the ticket that is recorded rather than
hidden. T-0514 asked for `civic_evidence[]`, `census_evidence[]` (1830),
`church_evidence[]` and `book_evidence[]`. Four notes on that:

  * There is no 1830 census domain in the consolidation to read — `read_census_1840` is
    the only census reader it has, and `census_1830_peoria_county_chicago_precinct` is a
    source the identity master never offers. `census_evidence[]` therefore carries 1840
    rows, which are LATER evidence and can never be a residency source on their own
    (refusal 3 and the ladder's G0 both say so); they corroborate a person the scene-year
    record already reaches.
  * `press_evidence[]` is added, because the ticket's four blocks have no home for the
    contemporary newspapers and the ladder's G1b — a Chicago paper of 1833-1835 printing
    the person by name in the town — is the largest single rung in this pool.
  * Every row carries the ladder rule id that fired for the identity, the list it was
    read from, the transcription AS READ, the locator and the source id, so a card can
    show the reading and a reader can go back to the page.
  * The books are the two directories and the old settlers' death notices together:
    both are a later book's recollection of an earlier town, and the ladder treats them
    the same way.

THE TENSION WITH `mint_placed_residents.py`, stated rather than buried. That pass put
the register's tradeless `new_resident` people through a residency test derived from the
corpus (L213) and refused 382 of them — "a name printed in a Chicago paper is not a
Chicago resident". The owner's ladder, ratified a fortnight later, reads the same
evidence differently at G1b. This pass applies the ladder, because the ladder is the
ratified rule and T-0514 is the instruction to spend it; `--report` counts how many of
the people it mints that older test had refused, so the disagreement stays visible and
countable instead of being settled quietly. docs/LIBERTIES.md L215 is where it is
admitted.

THE REFUSALS, in the order they fire, each one printed by `--report`:

  1. `the ladder does not reach this identity`   — the proposal grades it
     `not_1835_resident` or abstains (G0, G5). Nothing is minted from an 1839 directory
     or an 1840 census appearance alone, which is the ladder's own first sentence.
  2. `the town already carries this person`      — the consolidation resolved the
     identity onto a committed card. T-0515 regrades those; this pass never touches one.
  3. `the town has researched this person and left them out` — index.json's
     `researched_not_resident` list is the exclusions-style half of this dataset and it
     outranks any mint. A finding that somebody is NOT in this scene was argued once and
     is not quietly reversed by a pass that reads the same name off a list.
  4. `an 1832 enrollment alone is earlier evidence and never mints` — the Black Hawk War
     enrollment record states its own ladder: "An 1832 enrollment is EARLIER evidence and
     never an 1835 residence on its own: it places the man in this town in 1832, which is
     why it dates and corroborates rather than mints"
     (`data/research/civic/records/blackhawk_war_1832_chicago.json`, `the_ladder`). That
     reading is the project's and this pass does not overturn it from a rung the
     consolidation assigns generically. It also keeps this pass away from the 94 rows the
     index prints in the INDIAN company with no surname comma at all: their names cannot
     be read in a surname-first model without inventing an order for them, and any record
     touching the removal is subject to AGENTS.md's standing constraint rather than to a
     mint tool's judgement.
  5. `the post office's letter lists are the pass beside this one's pool` — every
     appearance inside the scene year is a letter list. See above.
 5b. `every scene-year reading is a church entry the register places outside Chicago`
     — St Cyr married three couples at Bear Creek, Sangamon County in May 1834 and his
     register carries those entries beside the Chicago ones. The rows say so themselves
     (`at_chicago: false`); this pass reads the field and mints nobody off them. T-1129.
  6. `a firm, not a person` — and it fires before the surname rule below, because "&
     Co" reads as a two-letter family name and the firm is the truer finding.
  7. `the transcription bracketed the name as uncertain`.
  8. `no name the corpus prints as a family name` — nothing that could be a surname.
  9. `no appearance inside the scene year` — there is no record to bound an arrival at
     or before the scene date with, so minting one would assert an arrival the sources
     do not reach. A later-only source is never a residency source.
 10. `a duplicate of a person the town already carries` — the id this identity would
     take is already a person's. The consolidation did not link them and this pass will
     not overwrite a card to find out; it is a merge for the consolidation to make.
 12. `no evidence block this pass writes` — no appearance in a domain with a block.
"""
from __future__ import annotations

import argparse
import calendar
import functools
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
PROPOSAL = DATA / "research" / "residents" / "grading_proposal.json"
MASTER = DATA / "research" / "residents" / "identity_master.json"

sys.path.insert(0, str(ROOT / "tools"))
from rebuild_resident_index import rebuild  # noqa: E402  (the manifest's one owner)
from resident_mint_carry import carry_resident_mint  # noqa: E402  (T-1137)
from mint_documented_residents import (  # noqa: E402  (shared, deliberately)
    FIRM, PAPERS, SCENE_DATE, UNCERTAIN, display, dumps, household_id, load,
    minted_by, plain_fragment, slug, surname, words,
)

PASS_NAME = "civic"
PREFIX = "hh_civic_"      # legacy shape only; T-0599 ids are plain and this never fires
DIVISION = "unplaced"
SCENE_YEAR = 1835

# The proposal's grades this pass writes. `not_1835_resident` and the abstention are
# refusal 1; `reconstructed` is not a grade any mint may assign (index.json keeps it at
# zero after the 2026-09-02 synthesis and this pass does not reopen it).
MINTABLE_GRADES = ("attested", "inferred")

LETTER_LIST_CLASS = "newspaper_letter_list"

# The 1832 muster, and the reading the project already committed to for it. Quoted from
# `data/research/civic/records/blackhawk_war_1832_chicago.json`'s own `the_ladder` field
# so the two cannot drift apart silently. See refusal 4.
MUSTER_CLASS = "muster_1832"
# THE PLACE REFUSAL (T-1049), as the identity master names it. A reading the resolved
# place vocabulary puts outside the town is not a Chicago appearance, so this pass must
# not read one: not into `press_evidence`, not into the sources a card cites, and — the
# one that would have been hardest to see — not into `arrival_block`, where a Michigan
# City notice of February 1834 would otherwise have set a man's bound at Chicago. The
# master keeps the row under its own class; this pass simply does not spend it.
REFUSED_CLASSES = {"newspaper_out_of_town"}
NO_DATE = "not read from this record"

# THE PROPERTY REFUSAL (T-1117), and it is a different refusal from the place one above.
# A tax list is a roll of what the town ASSESSED, and a town assesses GROUND: the
# non-resident owner of a town lot stands on it for the lot, and so does a dead man's
# estate. The 1833 list proves that out of its own membership rather than out of an
# argument — entry 110 is "Wolcott, Alexander", and this project's own source
# (fergus_1843_old_settler_death_notices, fdn0742) prints "Wolcott, Dr. Alexander,
# Indian agent, died Oct. 25, 1830, aged 40; his will was the first probated in Cook
# County." A man three years dead was not in the town; his estate was, and the probate
# is how it got onto the roll. On its own face the list settles nothing either way:
# the published transcription is names only — no valuation, no lot, no amount, no
# residence column (civic claims v001) — so it marks no payer resident and no payer
# non-resident, and the distinction it would have to draw is not on the page.
# So it cannot carry the one claim that is about a BODY ON A DAY. It is no leg of the
# presence bracket. What it still does is date and corroborate a NAME in the town's own
# paper, which is the whole of what the owner's ratified ladder spends it on at G2b, so
# no grade moves here and the arrival bound stands as a bound on the RECORD — restated
# in those words rather than withdrawn. docs/RESEARCH/tax_list_1833_not_a_residence_check.md
# is the reading and the count.
NOT_A_PRESENCE_CLASS = {"tax_1833"}
PROPERTY_ROLL_NOTE = ("THE 1833 TAX LIST IS A PROPERTY ROLL, NOT A RESIDENCE CHECK (T-1117): "
                      "it names the owner of ground inside the town, resident or not, and its "
                      "own entry 110 is a man three years dead. It bounds the town's RECORD of "
                      "this name and not the day this person reached Chicago")
# THE PLACE-IN-1835 REFUSAL (T-1131), and it is a THIRD refusal, reached from the data
# rather than listed here. A research domain may declare, on every record it publishes,
# that membership of its list is no evidence of where that person was in 1835 —
# `places_in_1835: false`, with the reason beside it. `death_notices.json` has carried
# that field since the obituary was read, because the OBITUARY's own header admits it
# prints "some of Chicago's Old Settlers, prior to 1843, and other well - known citizens
# who arrived after 1843, together with others prominently connected with Illinois
# history". Nothing read the field, so the refusal existed in the corpus and not in any
# derivation: `hh_wolcott_alexander` read `present` for 1 July 1835 on a bracket whose
# at-or-before leg was the man's own death notice of 25 October 1830.
#
# THE REFUSAL IS ASYMMETRIC, AND THE ASYMMETRY IS WHAT THE FIELD ITSELF SAYS. The
# at-or-before leg of the presence bracket is exactly the claim `places_in_1835: false`
# denies — that this source puts the person at Chicago by the scene date. The after leg
# is a different claim, about a LATER day, and the record does make it on its own face:
# a man who died at Chicago in 1885 was at Chicago in 1885. So a class the field refuses
# may still close the bracket from above, and a blanket refusal would have been wrong on
# seven cards whose only at-or-after leg is a death notice. `tax_1833` is refused on
# BOTH legs and for a different reason (T-1117): a property roll names ground and not a
# person, so it is no leg of the bracket at any date.
#
# WHAT A REFUSED AT-OR-BEFORE LEG LEAVES BEHIND is a reading of the record, not a gap —
# see `presence_block`. A death is the one appearance that is terminal: a man dead
# before the scene date was not merely unrecorded on it, he was ABSENT from it.
PLACE_CLAIM_DOMAINS = {
    # the research file that publishes the declaration -> the evidence class the
    # identity master gives its rows. One entry today; the mechanism is the point.
    DATA / "research" / "old_settlers" / "death_notices.json": "death_notice",
}
# The one class in the refusal whose date is a DEATH rather than an appearance, which is
# what lets `absent` be read off it. Another class could join the refusal above without
# joining this one, and the reading below would then stay `uncertain` for it.
DEATH_CLASS = "death_notice"
PLACE_REFUSAL_FIELD = "places_in_1835"
DEATH_NOTICE_NOTE = ("A DEATH NOTICE IS NOT A PRESENCE (T-1131): the old settlers' "
                     "obituary declares `places_in_1835: false` on every record it "
                     "publishes, because its own header admits it prints citizens who "
                     "arrived after 1843. It dates a death; it never says the man was "
                     "standing in the town on 1 July 1835")


@functools.lru_cache(maxsize=None)
def not_in_1835_classes() -> frozenset:
    """The evidence classes whose own domain says they place nobody in 1835.

    Read from the domain, never asserted here, and UNANIMITY is the bar: the class is
    refused only if every record the file publishes carries `places_in_1835: false`. A
    file that has stopped saying it, or that says it of some rows and not others, is a
    ruling that has moved — the class drops out of the refusal, `--self-test` goes red
    on the class it expects to find, and the ticket reopens rather than the rule being
    re-argued from this comment.
    """
    refused = set()
    for path, cls in PLACE_CLAIM_DOMAINS.items():
        if not path.exists():
            continue
        records = load(path).get("records") or []
        if records and all(r.get(PLACE_REFUSAL_FIELD) is False for r in records):
            refused.add(cls)
    return frozenset(refused)


# THE NOT-CHICAGO REFUSAL (T-1129), and it is a FOURTH refusal — the first one this
# pass reads at the granularity of a RECORD rather than a class. A parish register is a
# priest's book, not a town's roll: St Cyr rode down the state in May 1834 and married
# three couples in a house at Bear Creek, Sangamon County, and his register carries those
# entries on the same pages as the Chicago ones. The reader that transcribed it said so
# on every affected row — `at_chicago: false`, with the footnote that places them — and
# `read_st_cyr_register.py`'s own docstring names the trap in capitals. Nothing read the
# field, so four households stood in the 1835 town on a marriage celebrated 180 miles
# away, and their arrival notes said in the project's own words that "church_1833_1835
# names this person at Chicago by 20 May 1834" — a false statement inside a provenance
# artifact, which is worse than a misplacement.
#
# WHY A RECORD AND NOT A CLASS. The place refusal above (T-1131) is unanimous by
# construction: a whole file declares that its membership places nobody. Here the same
# file carries Chicago entries and Sangamon County entries, and the distinction is
# printed per row. So the refusal is read per row, off the corpus, and never asserted
# here — a row the reader stops marking drops out of the refusal and `--self-test` goes
# red on the six it expects, which reopens this ticket rather than re-arguing it from
# this comment.
#
# WHAT IT REFUSES, exactly: an identity whose every scene-year reading is one of these
# rows has no Chicago appearance at all, and is not minted (refusal 5b). An identity
# that ALSO holds a clean reading still mints — but the out-of-town row is dropped from
# the evidence this pass writes, so it never becomes a church_evidence block, never
# cites its source on the card, and above all never sets the arrival bound. That last is
# the same asymmetry T-1049 drew for a Michigan City notice: the record is real, the
# reading is real, and neither says the person was at Chicago.
CHURCH_RECORDS = DATA / "research" / "church" / "records"
AT_CHICAGO_FIELD = "at_chicago"
NOT_CHICAGO_NOTE = ("A PARISH REGISTER IS NOT A TOWN ROLL (T-1129): the reading itself "
                    "carries `at_chicago: false`, because the entry was celebrated "
                    "outside Chicago. It dates an act; it never says the person was at "
                    "Chicago")


@functools.lru_cache(maxsize=None)
def not_chicago_records() -> frozenset:
    """Church readings whose own row says the entry was not at Chicago (T-1129).

    Read from `data/research/church/records/`, every file, never a list kept here: the
    reader that transcribed the register is the only thing that knows which of its pages
    were written at Chicago, and a hand copy of its answer would go stale the first time
    another leaf was read.
    """
    out = set()
    if not CHURCH_RECORDS.exists():
        return frozenset()
    for path in sorted(CHURCH_RECORDS.glob("*.json")):
        for record_row in (load(path) or {}).get("records") or []:
            if record_row.get(AT_CHICAGO_FIELD) is False and record_row.get("id"):
                out.add(record_row["id"])
    return frozenset(out)


MUSTER_LADDER = ("An 1832 enrollment is EARLIER evidence and never an 1835 residence on "
                 "its own: it places the man in this town in 1832, which is why it dates "
                 "and corroborates rather than mints")

# Which block each domain of the identity master writes to, and the words a note uses
# for it. `census_1840` is LATER evidence: it corroborates, it never carries a record on
# its own — see the docstring on the ticket's `census_evidence[] (1830)`.
BLOCKS = {
    "civic": ("civic_evidence", "the town's own civic lists"),
    "church": ("church_evidence", "the St Cyr register"),
    "newspapers": ("press_evidence", "the Chicago papers of 1833-1835"),
    "directories": ("book_evidence", "the printed directories"),
    "old_settlers": ("book_evidence", "the old settlers' death notices"),
    "census_1840": ("census_evidence", "the 1840 federal census of Cook County"),
}
BLOCK_KEYS = ("civic_evidence", "census_evidence", "church_evidence",
              "book_evidence", "press_evidence")

# The identity master names its census pages' source by the domain rather than by a
# source record — `read_census_1840`'s own fallback — and the newspapers reader hands
# every mention one domain label for two papers. Both are resolved here, because a
# person's `sources[]` has to name a file in data/sources/ or the validator fails it.
SOURCE_ALIAS = {"census_1840_cook_county": "census_1840_chicago_familysearch_images"}
NEWSPAPER_DOMAIN_SOURCE = "chicago_newspapers_1833_1835"

MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")

YEAR = re.compile(r"(1[6-9]\d\d)")
ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
YEAR_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
# The two orders the sources print a day in. `April 8, 1835` and `Dec. 1, 1848` are what
# the old settlers' notices give; `d. 14 Mar. 1861` is the other order the same book
# uses. The day is optional in both, because `July 1835` and `Sept., 1835` are printed
# too and a month with no day is still narrower than a year.
PRINTED_DATE = re.compile(r"([A-Za-z]{3,9})\.?\s*,?\s*(?:(\d{1,2})\s*,?\s*)?(1[6-9]\d\d)")
DAY_FIRST_DATE = re.compile(r"(\d{1,2})\s+([A-Za-z]{3,9})\.?\s*,?\s*(1[6-9]\d\d)")
MONTH_NUMBER = {}
for _i, _m in enumerate(MONTHS, start=1):
    MONTH_NUMBER[_m.lower()] = _i
    MONTH_NUMBER[_m[:3].lower()] = _i
MONTH_NUMBER["sept"] = 9


# ---------------------------------------------------------------------------
# dates: what a record says about WHEN, read as loosely as the sources write it
# ---------------------------------------------------------------------------

def year_of(value) -> int | None:
    m = YEAR.search(str(value or ""))
    return int(m.group(1)) if m else None


def _day_range(year: int, month: int | None, day: int | None) -> tuple[str, str] | None:
    """The first and last day a (year, month?, day?) reading permits."""
    if not 1 <= year <= 9999:
        return None
    if month is None:
        return (f"{year:04d}-01-01", f"{year:04d}-12-31")
    if not 1 <= month <= 12:
        return None
    last = calendar.monthrange(year, month)[1]
    if day is None:
        return (f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}")
    if not 1 <= day <= last:
        # a day the month cannot hold is a misreading of the day, not of the month
        return (f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}")
    return (f"{year:04d}-{month:02d}-{day:02d}",) * 2


def date_range(value) -> tuple[str, str] | None:
    """The EARLIEST and the LATEST day a `describes_date` permits, or None.

    A `describes_date` is a range and not a point, because the sources write dates as
    loosely as they please. A full ISO date is a single day. A bare year runs from 1
    January to 31 December — the list says the man was there THAT YEAR, not that he was
    there in January and not that he was there on New Year's Eve. `1834-06` is the month.
    And a printed day — the old settlers' `April 8, 1835`, `Dec. 1, 1848`, the other
    order's `d. 14 Mar. 1861` — is read for its MONTH AND DAY where the page gives them
    (T-1136) and not merely for its year: the page prints the day, and throwing it away
    was what let a death three months before the scene date be read as 31 December.

    Which END of the range a caller wants is the caller's question and never this
    function's — see `bracket_legs`, where the two legs want opposite ends.
    """
    s = str(value or "").strip()
    if not s:
        return None
    if ISO.match(s):
        return (s, s)
    if m := YEAR_MONTH.match(s):
        if rng := _day_range(int(m.group(1)), int(m.group(2)), None):
            return rng
    for pattern, day_first in ((DAY_FIRST_DATE, True), (PRINTED_DATE, False)):
        if not (m := pattern.search(s)):
            continue
        name, day = (m.group(2), m.group(1)) if day_first else (m.group(1), m.group(2))
        month = MONTH_NUMBER.get(name.lower().rstrip("."))
        if month is None:
            continue
        if rng := _day_range(int(m.group(3)), month, int(day) if day else None):
            return rng
    y = year_of(s)
    return _day_range(y, None, None) if y else None


def bound_of(value) -> str | None:
    """The LATEST day a `describes_date` permits, as an ISO date, or None.

    This is the end an arrival bound wants — `not_later_than` is the whole of what an
    arrival claims — and the end the AT-OR-BEFORE leg of the presence bracket wants,
    because that leg holds only if EVERY day the record permits falls at or before the
    scene date. For the opposite end, and the leg that wants it, see `floor_of`.
    """
    rng = date_range(value)
    return rng[1] if rng else None


def floor_of(value) -> str | None:
    """The EARLIEST day a `describes_date` permits, as an ISO date, or None.

    The end the AT-OR-AFTER leg of the presence bracket wants (T-1136). That leg holds
    only if every day the record permits falls at or after the scene date, so a bare
    `1835` — which may describe 2 January as easily as 31 December — closes no bracket
    over 1 July, and a death notice of `April 8, 1835` closes none either.
    """
    rng = date_range(value)
    return rng[0] if rng else None


def in_window(app: dict) -> bool:
    """Does this appearance describe a date inside the scene year or before it?"""
    y = year_of(app.get("describes_date"))
    return y is not None and y <= SCENE_YEAR


def pretty(iso: str) -> str:
    m = ISO.match(iso or "")
    if not m:
        return iso
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


# ---------------------------------------------------------------------------
# the pool, and the refusals
# ---------------------------------------------------------------------------

def source_of(app: dict) -> str | None:
    """The source id an appearance cites, resolved to a file in data/sources/."""
    sid = app.get("source_id")
    if sid == NEWSPAPER_DOMAIN_SOURCE:
        loc = str(app.get("locator") or "")
        for prefix, paper in PAPERS:
            if loc.startswith(prefix):
                return paper
        return None
    return SOURCE_ALIAS.get(sid, sid)


def has_family_name(name: str) -> bool:
    """Is there a token here that could BE a family name? (the letter-list pass's rule 4)"""
    fam = surname(name)
    return bool(fam) and len(re.sub(r"[^a-z]", "", fam)) >= 3


def bracketed_name_appearance(app: dict) -> bool:
    """Whether an in-window appearance carries a bracketed name reading (T-1115).

    Later directory annotations also use square brackets, for death notes and
    editorial context. They are not evidence this pass may use to mint a person
    in 1835 and they must not poison a separate clean scene-year reading.
    """
    raw = app.get("as_read")
    return in_window(app) and isinstance(raw, str) and bool(UNCERTAIN.search(raw))


def not_chicago_appearance(app: dict) -> bool:
    """Whether this appearance is a church reading its own row places outside Chicago."""
    return (app.get("domain") == "church"
            and app.get("record_id") in not_chicago_records())


def mintable_appearances(appearances: list) -> list:
    """The evidence this mint may write: never a bracketed scene-year name, and never
    a church reading the register itself places outside the town (T-1129)."""
    return [a for a in appearances
            if not bracketed_name_appearance(a) and not not_chicago_appearance(a)]


def decide(row: dict, appearances: list, town_person_ids: set,
           excluded: set | None = None, own: set | None = None,
           taken_above: set | None = None) -> tuple[bool, str]:
    """The nine refusals, in order. Returns (accepted, reason) — reason is '' if minted.

    A pure function of its arguments so `--self-test` can fire every rule at a fixture
    instead of at the tree, which is what keeps the assertions meaningful when the
    corpus grows.
    """
    name = row.get("name") or ""
    if row.get("grade") not in MINTABLE_GRADES:
        return False, (f"the ladder does not reach this identity "
                       f"({row.get('rule')} → {row.get('grade')})")
    if row.get("canonical_person_id") and row["canonical_person_id"] not in (own or set()):
        return False, (f"the town already carries this person "
                       f"({row['canonical_person_id']})")
    if plain_fragment(name) in (excluded or set()):
        return False, (f"the town has researched this person and left them out "
                       f"({plain_fragment(name)})")
    uncertain_readings = [a.get("as_read") for a in appearances
                          if bracketed_name_appearance(a)]
    scene_year = [a for a in appearances
                  if in_window(a) and not bracketed_name_appearance(a)]
    if scene_year and all(a.get("evidence_class") == MUSTER_CLASS for a in scene_year):
        return False, "an 1832 enrollment alone is earlier evidence and never mints"
    if scene_year and all(a.get("evidence_class") == LETTER_LIST_CLASS for a in scene_year):
        return False, "the post office's letter lists are the pass beside this one's pool"
    # T-1129, refusal 5b. Every scene-year reading is a church entry whose own row says
    # the act was not celebrated at Chicago, so there is no Chicago appearance to bound
    # an arrival with — the same shape as refusal 9 below, reached one step earlier so
    # the reason names the register rather than reading as a plain absence of evidence.
    if scene_year and all(not_chicago_appearance(a) for a in scene_year):
        outside = sorted({a.get("record_id") for a in scene_year})
        return False, ("every scene-year reading is a church entry the register places "
                       f"outside Chicago ({', '.join(outside)})")
    if FIRM.search(name):
        return False, "a firm, not a person"
    # T-1115. `row.name` is the consolidation's rebuilt display name, not the
    # source reading. The clusterer has already stripped square brackets by the
    # time it writes that value, so checking it alone made this refusal dead:
    # `H. G. Hub[…]` arrived here as `H G Hub` and minted The Hub household.
    # Read the in-window appearances' verbatim `as_read` values as well. A
    # bracketed appearance is excluded from the mint; a separate clean reading
    # may still support the identity, while a name resting only on the bracketed
    # reading reaches refusal 7.
    if UNCERTAIN.search(name) or (uncertain_readings and not scene_year):
        return False, "the transcription bracketed the name as uncertain"
    if not has_family_name(name):
        return False, "no name the corpus prints as a family name"
    if not scene_year:
        return False, "no appearance inside the scene year"
    if plain_fragment(name) in (taken_above or set()):
        return False, (f"the residency-tested pass above this one takes this person "
                       f"({plain_fragment(name)})")
    if plain_fragment(name) in town_person_ids:
        return False, (f"a duplicate of a person the town already carries "
                       f"({plain_fragment(name)})")
    if not any(a.get("domain") in BLOCKS for a in appearances):
        return False, "no evidence block this pass writes"
    return True, ""


# ---------------------------------------------------------------------------
# the record
# ---------------------------------------------------------------------------

def evidence_blocks(row: dict, appearances: list) -> tuple[dict, list]:
    """The per-domain evidence blocks, and the source ids they cite."""
    blocks: dict = {k: [] for k in BLOCK_KEYS}
    sources: list = []
    for app in sorted(appearances, key=lambda a: (str(a.get("describes_date") or ""),
                                                  str(a.get("record_id") or ""))):
        spec = BLOCKS.get(app.get("domain"))
        if not spec:
            continue
        sid = source_of(app)
        if not sid:
            continue
        key, _ = spec
        blocks[key].append({
            "list": app.get("evidence_class"),
            "as_read": app.get("as_read"),
            "locator": app.get("locator"),
            "record_id": app.get("record_id"),
            # Six old-settlers death notices carry no date the reader captured. The
            # absence is written down rather than left as an empty field: `bound_of`
            # reads no year out of it, so such a row can never become an arrival bound,
            # and the validator's own rule (an evidence row states its date) is met by
            # saying there is none rather than by leaving the key blank.
            "describes_date": app.get("describes_date") or NO_DATE,
            "source": sid,
            "rule": row.get("rule"),
        })
        if sid not in sources:
            sources.append(sid)
    return {k: v for k, v in blocks.items() if v}, sorted(sources)


def arrival_block(appearances: list, sources: list) -> dict:
    scene_year = [a for a in appearances if in_window(a)]
    dated = sorted(((b, str(a.get("record_id") or ""), a) for a in scene_year
                    if (b := bound_of(a.get("describes_date")))), key=lambda t: t[:2])
    value, _rid, app = dated[0]
    late = value > SCENE_DATE
    cls = app.get("evidence_class")
    roll = cls in NOT_A_PRESENCE_CLASS
    names = ("stands against this person's name by "
             if roll else "names this person at Chicago by ")
    note = (f"A BOUND FROM THE RECORD, NOT AN ARRIVAL. {app.get('list') or cls} "
            f"{names}{pretty(value)} and nothing says when they came. ")
    if late:
        note += ("THE BOUND FALLS AFTER THE SCENE DATE and the record says so rather than "
                 "narrowing it: the earliest source that names this person is later than "
                 "1 July 1835, so they may have arrived after the day this scene models. "
                 "present_on_scene_date is `uncertain` for that reason.")
    elif roll:
        # The bound stands and its CLAIM shrinks (T-1117). `arrival` is structurally a
        # dated `not_later_than` on every household the validator will accept, and this
        # record does give one honestly: the town's assessor had this name on his roll by
        # then. What it does not give is the man at Chicago, so the sentence that used to
        # say so is gone rather than softened, and the claim about the day now lives only
        # in present_on_scene_date — which this same refusal has withdrawn to `uncertain`.
        note += (PROPERTY_ROLL_NOTE + ". The bound is at or before the scene date, so the "
                 "town's own paper carries this name by 1 July 1835; whether the man it "
                 "names was standing in the town is a claim this record cannot make, and "
                 "present_on_scene_date says `uncertain` for that reason.")
    else:
        # AND THE ARRIVAL BOUND IS NOT TOUCHED BY THE PLACE-IN-1835 REFUSAL (T-1131),
        # which is a rule about the presence bracket and not about this one. A man who
        # died at Chicago in 1830 WAS at Chicago by 1830 to die there, so `not_later_than
        # 1830-12-31` is honest and the sentence below stays true of him: it says he had
        # been at Chicago at some time by the scene date, which is all an arrival bound
        # ever asserted. The claim this ticket refuses — that he was standing in the town
        # ON the day — lives in present_on_scene_date alone, and is settled there.
        note += ("The bound is at or before the scene date, so the person was at Chicago "
                 "by 1 July 1835 on this record's own evidence.")
    return {
        "value": value,
        "confidence": "inferred",
        "sources": sources,
        "note": note,
        "precision": "not_later_than",
    }


def bracket_legs(appearances: list) -> tuple[list, list, list]:
    """Which side of the presence bracket each appearance may stand on.

    THREE ANSWERS AND NOT TWO, because the two refusals this pass carries are different
    shapes. `tax_1833` is refused on BOTH legs (T-1117): a property roll names the owner
    of ground inside the town — resident, absent or three years dead — so it is no leg of
    the bracket at any date. A class the domain declares `places_in_1835: false` (T-1131)
    is refused on the AT-OR-BEFORE leg alone: that leg is the very claim the declaration
    denies, while the after leg is a claim about a later day the record does make. The
    refused at-or-before rows come back as the third list rather than being dropped,
    because what they say is a finding — see `presence_block`.

    EACH LEG READS THE END OF THE DATE RANGE NEAREST THE SCENE DATE, AND THEY ARE
    OPPOSITE ENDS (T-1136). A `describes_date` permits a RANGE of days — a bare `1835`
    permits all 365 of them — and a leg holds only if EVERY day the record permits falls
    on that leg's side of 1 July 1835. So the at-or-before leg tests the LATEST permitted
    day and the at-or-after leg tests the EARLIEST. Reading one number for both is what
    let a death notice of `April 8, 1835` — three months before the scene date — close a
    bracket over it as 31 December, and it is what let every bare `1835` do the same.
    A record that straddles the day is NEITHER leg: it is honestly silent about which
    side of 1 July its day fell on, and silence is `uncertain` (see `presence_block`),
    never a bracket.
    """
    refused_classes = not_in_1835_classes()
    before: list = []
    after: list = []
    refused_before: list = []
    for app in appearances:
        cls = app.get("evidence_class")
        if cls in NOT_A_PRESENCE_CLASS:
            continue
        span = date_range(app.get("describes_date"))
        if not span:
            continue
        earliest, latest = span
        if earliest >= SCENE_DATE:
            after.append(app)
        if latest <= SCENE_DATE:
            (refused_before if cls in refused_classes else before).append(app)
    return before, after, refused_before


def death_before_the_day(refused_before: list, before: list) -> str | None:
    """The day this person died, if the record says he was dead before the scene date.

    Narrow on purpose, and it says no three ways. It reads only `DEATH_CLASS` — another
    class may join the `places_in_1835` refusal without its date being a death, and the
    reading below would stay `uncertain` for it. It wants ONE death: two notices that
    disagree on the year are an identity question and not a death. And it defers to any
    record that places the person at Chicago AFTER the death and at or before the scene
    date, because that is a contradiction the mint must not resolve by picking a side —
    a tax roll is not one of those records, which is the whole of T-1117.
    """
    days = {b for app in refused_before
            if app.get("evidence_class") == DEATH_CLASS
            and (b := bound_of(app.get("describes_date"))) and b < SCENE_DATE}
    if len(days) != 1:
        return None
    died = days.pop()
    if any((b := bound_of(app.get("describes_date"))) and b > died for app in before):
        return None
    return died


def presence_block(appearances: list, sources: list) -> dict:
    before, after, refused_before = bracket_legs(appearances)
    if before and after:
        return {
            "value": "present",
            "confidence": "inferred",
            "sources": sources,
            "note": ("THE RECORD BRACKETS THE DAY. This person is named at Chicago at or "
                     "before 1 July 1835 and named again at or after it, so the sources "
                     "reach across the scene date rather than stopping at one side of it. "
                     "Inferred, not documented: no source says where they were on the day."),
        }
    died = death_before_the_day(refused_before, before)
    if died:
        return {
            "value": "absent",
            "confidence": "attested",
            "sources": sources,
            # A DEATH IS THE ONE APPEARANCE THAT IS TERMINAL. Everywhere else this pass
            # withdraws to `uncertain`, because a silence is a place the sources have not
            # looked. A death is not a silence: the record says the man stopped, and it
            # dates the stopping before the day this scene models. `absent` is therefore
            # the honest reading and `uncertain` would be the flattering one.
            "note": (f"THE RECORD PLACES THIS PERSON NOWHERE ON THE DAY, BECAUSE HE WAS "
                     f"DEAD. The old settlers' obituary dates the death "
                     f"{pretty(died)}, before the scene date of 1 July 1835, and no "
                     f"record that places a person at Chicago names this one after it. "
                     + DEATH_NOTICE_NOTE + " — so it cannot be the at-or-before leg of a "
                     "bracket, and a later source on the far side cannot close one over a "
                     "dead man. `absent` and not `uncertain`: a silence is somewhere the "
                     "sources have not looked, and a death is not a silence."),
        }
    refused = sorted({a.get("evidence_class") for a in appearances
                      if a.get("evidence_class") in NOT_A_PRESENCE_CLASS})
    note = ("THE RECORD DOES NOT REACH THE DAY. Every source that names this person "
            "falls on one side of 1 July 1835, and nothing follows them to it or says "
            "they left. `uncertain` rather than dropped — the distinction index.json "
            "draws for Jeremiah Porter, and a finding, not a gap.")
    if refused:
        note += (" AND THE BRACKET THIS CARD ONCE HAD IS WITHDRAWN, NOT LOST: its "
                 f"at-or-before leg was {', '.join(refused)} alone. "
                 + PROPERTY_ROLL_NOTE + ", so it cannot say this person was here to be "
                 "followed across the day. Withdrawn to `uncertain` and not to `absent` — "
                 "no source places this person anywhere else on 1 July 1835 either, and a "
                 "man who was taxed for ground in the town may perfectly well have been "
                 "standing on it.")
    if refused_before and not before:
        note += (" THE AT-OR-BEFORE LEG OFFERED HERE IS ONE THIS PASS MAY NOT STAND ON: "
                 + DEATH_NOTICE_NOTE + ". `uncertain` and not `absent` — this card's "
                 "refused leg does not date a single death before the day, or another "
                 "record names this person at Chicago after it, so what the sources leave "
                 "is a gap rather than an end.")
    return {
        "value": "uncertain",
        "confidence": "inferred",
        "sources": sources,
        "note": note,
    }


def unattested(note: str) -> dict:
    return {"value": None, "confidence": "reconstructed", "note": note}


def carry_over(doc: dict, prior: dict | None, retracted: set | None = None) -> dict:
    """Keep what another pass wrote, at that writer's marker boundary (T-1137).

    ``BLOCK_KEYS`` and ``resident_subtype`` are this mint's optional answers: if the
    new derivation omits one, an old card may not put it back.  ``retracted`` has the
    same ownership rule for a source this pass used to derive.  Everything else is
    carried by the shared four-mint contract, including a foreign note suffix even
    when this mint's own prose changed.
    """
    if not prior or prior.get("source_pass") != PASS_NAME:
        return doc
    return carry_resident_mint(
        doc, prior,
        owned_person_keys=BLOCK_KEYS + ("resident_subtype",),
        retracted_sources=retracted,
    )


def record(row: dict, appearances: list, docs: dict, taken_ids: set,
           established: dict | None = None) -> dict:
    # T-0970: a newly matched spelling adds evidence to an existing person. It
    # cannot rename the card and thereby evade carry_over's exact household lookup.
    # Only this mint's own card, explicitly named by canonical_person_id, qualifies.
    previous = next((p for p in (established or {}).get("persons", [])
                     if p.get("id") == row.get("canonical_person_id")), None)
    name = previous["name"] if previous else display(row.get("name") or "")
    hid = established["id"] if previous else household_id(name, PREFIX, PASS_NAME, docs, taken_ids)
    pid = previous["id"] if previous else plain_fragment(name)
    n = 2
    while pid in taken_ids:
        pid, n = f"{plain_fragment(name)}_{n}", n + 1
    blocks, sources = evidence_blocks(row, appearances)
    lists = sorted({str(e["list"]) for rows in blocks.values() for e in rows})
    arrival = arrival_block(appearances, sources)
    person = {
        "id": pid,
        "name": name,
        "relationship": "head",
        "grade": row["grade"],
        # The manifest's own flag for which pass wrote this person, so a card and the
        # Evidence panel can hold the civic cohort apart from the letter-list one
        # without fetching a thousand records (the letter lists' `letter_list_only`
        # does the same job for the pass beside this one).
        "civic_mint": True,
        "ladder_rule": row.get("rule"),
        "occupation": {
            "value": "none_recorded",
            "confidence": "reconstructed",
            "note": ("No source in this pass's evidence records an occupation for this "
                     "person. A poll list, a tax list, a muster roll and a baptismal "
                     "entry each print a name and no trade, and where a later directory "
                     "prints one it is a trade of 1843 — T-0633 is the rule for "
                     "back-projecting that, and this pass does not have it."),
        },
        "sources": sources,
        "note": note_for(row, lists, arrival),
    }
    person.update(blocks)
    if row.get("resident_subtype"):
        person["resident_subtype"] = row["resident_subtype"]
    fam = surname(name).title() or name
    return {
        "id": hid,
        "name": f"The {fam} household — a name the town's own records carry",
        "division": DIVISION,
        "head": pid,
        "source_pass": PASS_NAME,
        "arrival": arrival,
        "party_size_on_arrival": unattested("Not attested."),
        "origin": unattested("Not attested."),
        "reason_for_coming": unattested("Not attested."),
        "lives_at": unattested(
            "Not attested: the lists that name this person give no address. The placement "
            "sweep assigns homes once the resident list is complete (T-0514, the owner's "
            "own sequencing) and this pass will not guess one."),
        "works_at": unattested(
            "Not attested. No trade is recorded here, so there is no premises to seek; "
            "T-0633 is where a later directory's address gets back-projected."),
        "present_on_scene_date": presence_block(appearances, sources),
        "persons": [person],
        "touches_removal": False,
        "review_required": False,
        "research_note": (
            "MINTED FROM THE CONSOLIDATED CIVIC, CHURCH, PRESS, BOOK AND CENSUS EVIDENCE "
            "(T-0513, T-0514). THE HOUSEHOLD IS A CONTAINER, NOT AN ARGUMENT: every other "
            "record here is written unattested in its own block, because the lists that "
            "name this person name a person and not a family. What is claimed is that the "
            "sources cited on the member below name them at Chicago, and the grade is the "
            "owner's ratified ladder applied by "
            "tools/consolidate_resident_evidence.py --build and spent by "
            "tools/mint_civic_residents.py, which prints every refusal. "
            "docs/LIBERTIES.md L215 carries the liberty and the tension with L213."),
    }


def note_for(row: dict, lists: list, arrival: dict) -> str:
    rung = {
        "G1a": "THE 1835 POLL LIST AND A SECOND INDEPENDENT SOURCE.",
        "G1b": "A CONTEMPORARY CHICAGO PAPER OF 1833-1835 PRINTS THIS PERSON BY NAME IN THE TOWN.",
        "G2a": "THE 1835 POLL LIST ALONE.",
        "G2b": "AN 1833 OR 1834 LIST — POLL, TAX OR MUSTER — WITH ANOTHER SOURCE.",
        "G2c": "THE ST CYR REGISTER OF 1833-1835 NAMES THIS PERSON IN THE PARISH.",
        "G2d": "HUBBARD, FERGUS OR NORRIS NAMES THIS PERSON WITH A TRADE OR AN ADDRESS.",
        "G2e": "A CHICAGO POST-OFFICE LETTER LIST OF 1833-1835 AND NOTHING STRONGER.",
        "G3": "A SINGLE APPEARANCE AND NOTHING ELSE.",
        "G4": "TWO OR MORE APPEARANCES, NONE OF A CLASS A HIGHER RUNG ACCEPTS.",
    }.get(row.get("rule"), "THE LADDER'S OWN READING OF THIS EVIDENCE.")
    head = ""
    if row.get("resident_subtype") == "projected_resident":
        head = ("PROJECTED RESIDENT. Documented once and corroborated by nothing else, so "
                "the weakest rung of `inferred` the owner's ladder defines. ")
    return (
        f"{head}{rung} Read from {', '.join(lists)}. "
        f"THE GRADE IS THE OWNER'S RATIFIED LADDER OF 2026-09-03 ({row.get('rule')}), applied "
        f"to every identity at once by tools/consolidate_resident_evidence.py and spent onto "
        f"this card by tools/mint_civic_residents.py; the evidence blocks below carry the "
        f"reading AS READ, its locator and the record it came from, so the page can be gone "
        f"back to. WHAT IS RECONSTRUCTED: everything except the person and the sources — no "
        f"dwelling, no trade, no origin, no family, no party. {arrival['note']} "
        f"No figure is drawn (L1)."
    )


# ---------------------------------------------------------------------------
# the build
# ---------------------------------------------------------------------------

def town_person_ids(docs: dict) -> set:
    return {p.get("id") for doc in docs.values() for p in doc.get("persons") or []}


def excluded_ids(index: dict) -> set:
    """The people this project researched and left OUT of the scene, by id and by name.

    index.json's `researched_not_resident` is the exclusions-style half of the dataset
    and adding to it is preferred to deleting from it. A mint that seated one of them
    would reverse an argued finding by accident. Refusal 3.
    """
    out: set = set()
    for entry in index.get("researched_not_resident") or []:
        if entry.get("id"):
            out.add(entry["id"])
        if entry.get("name"):
            out.add(plain_fragment(entry["name"]))
    return out


def placed_takes(docs: dict, index: dict) -> set:
    """The people `mint_placed_residents.py` mints, asked of the pass itself.

    Refusal 10. Asked rather than hard-coded because the answer moves with the register,
    and a list copied into this file would be a precedence rule that silently stopped
    being one. The town it is asked about is the town WITHOUT this pass's own output, so
    the question is the precedence question — who would take this person if this pass did
    not exist — and not a reading of what this pass has already done.
    """
    import mint_placed_residents as placed
    accepted = placed.mint(docs, index)[0]
    return {plain_fragment(display(cand["name"])) for cand in
            (a[0] if isinstance(a, tuple) else a for a in accepted)}


def pool(docs: dict, proposal: dict, master: dict, index: dict, own: set):
    """Every identity the proposal offers, put through `decide()` in a stable order.

    WHY THE POOL READS ITS OWN ANSWER BACK, and it is the same reason the three passes
    beside this one do. `grading_proposal.json` is compiled FROM the committed town, so
    the moment this pass seats somebody the consolidation starts resolving that identity
    onto the card it just wrote and hands back a `canonical_person_id` for them. Read
    naively, refusal 2 would then fire on every person this pass has ever minted and the
    next `--build` would delete all of them. A canonical id that points at one of THIS
    pass's own people is read as what it is — this pass's previous answer — so the
    derivation still holds the run after it lands.

    `town_layer` appearances are dropped for the same reason and a second one: the
    consolidation's own reader says that layer is "not a source — it is what the sources
    are spent onto", so letting it into the refusals would mean an identity that rests on
    the 1832 muster alone stops resting on the muster alone the moment this pass declines
    it and something else seats them.
    """
    apps = {i["id"]: [a for a in (i.get("appearances") or [])
                      if a.get("domain") != "town_layer"
                      and a.get("evidence_class") not in REFUSED_CLASSES]
            for i in master.get("identities", [])}
    known = town_person_ids(docs)
    excluded = excluded_ids(index)
    above = placed_takes(docs, index)
    accepted, refusals = [], []
    for row in sorted(proposal.get("proposals", []), key=lambda r: r["identity"]):
        appearances = apps.get(row["identity"], [])
        ok, reason = decide(row, appearances, known, excluded, own, above)
        if ok:
            accepted.append((row, mintable_appearances(appearances)))
        else:
            refusals.append((row, reason))
    return accepted, refusals


def build(preload: dict | None = None):
    docs = ({p: json.loads(t) for p, t in preload.items() if p != INDEX}
            if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    index = (json.loads(preload[INDEX]) if preload is not None and INDEX in preload
             else load(INDEX))
    proposal, master = load(PROPOSAL), load(MASTER)

    mine_paths = {p for p, doc in docs.items() if minted_by(p, doc, PASS_NAME, PREFIX)}
    # This pass must not read its OWN output back as "the town already carries this
    # person" — refusal 2 and refusal 8 would both fire on the second run and delete
    # every household the first one seated. See mint_documented_residents.MINTED_PREFIXES.
    others = {p: d for p, d in docs.items() if p not in mine_paths}
    own = {person.get("id") for path in mine_paths
           for person in docs[path].get("persons") or []}
    established = {person.get("id"): docs[path] for path in mine_paths
                   for person in docs[path].get("persons") or []}
    accepted, refusals = pool(others, proposal, master, index, own)

    # What each identity's REFUSED readings were citing, so `carry_over` can tell this
    # pass's own retraction from another pass's addition (T-1049).
    retracted = {i["id"]: {sid for a in (i.get("appearances") or [])
                           if a.get("evidence_class") in REFUSED_CLASSES
                           and (sid := source_of(a))}
                 for i in master.get("identities", [])}

    files = {}
    taken: set = set()
    for row, appearances in accepted:
        doc = record(row, appearances, others, taken,
                     established.get(row.get("canonical_person_id")))
        doc = carry_over(doc, docs.get(HOUSEHOLDS / f"{doc['id']}.json"),
                         retracted.get(row["identity"], set()))
        if doc["id"] in taken:
            raise SystemExit(f"two identities mint the same household id {doc['id']}")
        taken.add(doc["id"])
        taken.add(doc["persons"][0]["id"])
        files[HOUSEHOLDS / f"{doc['id']}.json"] = dumps(doc, 1)

    # ONE OWNER FOR THE MANIFEST (T-0715). This pass used to mint its own rows and
    # keep every other row verbatim, so a household no pass owned could be regraded
    # elsewhere and go on carrying a row that said something else. `final` is the
    # whole layer as this pass leaves it, and the derivation reads all of it.
    final = dict(others)
    final.update({path: json.loads(text) for path, text in files.items()})
    rebuild(index, final)
    files[INDEX] = dumps(index, 1)
    return files, accepted, refusals, mine_paths


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------

def reason_key(reason: str) -> str:
    return reason.split(" (")[0]


def report(accepted, refusals) -> None:
    print(f"MINTED — {len(accepted)} civic/church/press/book resident(s)")
    by_rule: dict = {}
    by_grade: dict = {}
    for row, _apps in accepted:
        by_rule[row["rule"]] = by_rule.get(row["rule"], 0) + 1
        key = (row["grade"], row.get("resident_subtype") or "-")
        by_grade[key] = by_grade.get(key, 0) + 1
    for (grade, sub), n in sorted(by_grade.items()):
        print(f"  {n:5d}  {grade} / {sub}")
    for rule, n in sorted(by_rule.items()):
        print(f"  {n:5d}  {rule}")
    print(f"\nREFUSED — {len(refusals)} identity/identities out of the same pool, with the reason")
    tally: dict = {}
    for _row, reason in refusals:
        tally[reason_key(reason)] = tally.get(reason_key(reason), 0) + 1
    for reason, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {reason}")
    print()
    for row, _apps in accepted:
        print(f"  MINT   {row['identity'][:44]:46s} {row['rule']:4s} {row['grade']}")
    for row, reason in refusals:
        print(f"  REFUSE {row['identity'][:44]:46s} {reason}")


def scale_report() -> None:
    """What this pass is worth to the town, re-derived rather than remembered."""
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    mine = {p: d for p, d in docs.items() if minted_by(p, d, PASS_NAME, PREFIX)}
    persons = sum(len(d.get("persons") or []) for d in docs.values())
    ours = sum(len(d.get("persons") or []) for d in mine.values())
    grades: dict = {}
    domains: dict = {}
    for d in mine.values():
        for p in d.get("persons") or []:
            grades[p["grade"]] = grades.get(p["grade"], 0) + 1
            for key in BLOCK_KEYS:
                if p.get(key):
                    domains[key] = domains.get(key, 0) + 1
    print(f"{len(docs)} household(s), {persons} person(s) in the town")
    print(f"{len(mine)} household(s), {ours} person(s) from this pass "
          f"({(100.0 * ours / persons if persons else 0):.1f}% of the town)")
    for grade, n in sorted(grades.items()):
        print(f"  {n:5d}  {grade}")
    for key, n in sorted(domains.items()):
        print(f"  {n:5d}  carry {key}")


# ---------------------------------------------------------------------------
# T-0515 — the SECOND mode: regrade the people the town already carries
#
# `--build` above mints the identities the town does NOT hold. Its refusal 2 —
# "the town already carries this person" — hands every one of the others to this
# mode, and `grading_proposal.json` lists them as `changes_to_existing_people`:
# 162 rows, each a rule of the owner's ratified ladder fired against an identity
# whose card is already committed.
#
# THE TWO RULES THIS MODE IS BUILT AROUND, both from the ticket and both about
# what the ladder may NOT do:
#
#   * "nothing may be graded DOWN without a recorded refusal". A downgrade is
#     therefore never silent here. Where it fires, the grade it takes away is
#     written onto the person as a refusal with the rule that took it; where it
#     is declined, the decline is written the same way. Either way the reading
#     is on the card and a later run can see it was ruled on rather than missed.
#
#   * The consolidation sees SEVEN domains and no more. Its own G5 says so in
#     the ladder's words — it "abstains rather than demote a resident on evidence
#     it has not read". That abstention is a proposal with no grade in it and is
#     refused here rather than applied. And the same reasoning reaches further
#     than G5 does: 44 of the 45 downgrades this proposal offers fall on cards
#     that cite Andreas, Kinzie's Waubun, a dated Democrat issue or a research
#     package the consolidation never read. A rung fired on the evidence it
#     could see is not a finding about the evidence it could not, so those are
#     declined for the reason G5 declines its own, and the decline is recorded.
#     The one downgrade whose card cites nothing outside the ladder's field of
#     view is applied.
#
# WHAT IT WRITES on a person it regrades: `grade`, `resident_subtype`, the
# per-domain evidence blocks `evidence_blocks()` derives for the mint above, the
# union of the sources those rows cite, and a `resident_research` stamp naming
# the rule and the date. Everything else on the card belongs to the pass that
# wrote it and is left alone. The write is a pure function of the proposal, the
# identity master and the committed tree, so `--regrade --check` re-derives it —
# and reads its own answer back the way `--build` does. Once a regrade lands, the
# consolidation rebuilds against the card it wrote and stops proposing the change,
# so the steady state is nought applied with the refusals still standing. A hand-edit
# to one of those grades puts the proposal back and the gate says so, which is the
# thing it is there to catch.
# ---------------------------------------------------------------------------

# THE NAME TEST THE REGRADE OWES, and the reason it exists. The consolidation
# merges an identity on a surname and a compatible forename, and its D-rules are
# loose enough that `id_albee_clark_b` — Clark B. Albee, printed once by the post
# office — carries Fergus's 1843 line for *Cyrus P.* Albee. Read naively, that
# line is the second source that takes `projected_resident` off him. It is not:
# it is a different man with the same surname. So an evidence row corroborates
# here only when the forename it prints AGREES with the identity's — the same
# word, an initial, or one of the abbreviations these volumes actually set. Rows
# that fail are not attached and do not count towards a rung, and a proposal left
# with nothing is refused as one the evidence rows do not support.
#
# The abbreviations are the printers' own, taken from the entries in the corpus
# rather than invented: a directory of the 1840s sets Wm., Jas., Chas., Thos.
FORENAME_ABBREV = {
    "wm": "william", "willm": "william", "will": "william",
    "jas": "james", "jos": "joseph", "jno": "john", "jon": "john",
    "chas": "charles", "thos": "thomas", "geo": "george", "robt": "robert",
    "saml": "samuel", "danl": "daniel", "benj": "benjamin", "edwd": "edward",
    "edw": "edward", "richd": "richard", "rich": "richard", "nathl": "nathaniel",
    "nath": "nathaniel", "alexr": "alexander", "alex": "alexander",
    "fredk": "frederick", "fred": "frederick", "patk": "patrick",
    "michl": "michael", "matt": "matthew", "abm": "abraham", "andw": "andrew",
    "chrisr": "christopher", "hy": "henry", "hen": "henry", "theo": "theodore",
    "elizth": "elizabeth", "eliz": "elizabeth", "margt": "margaret",
    "cathe": "catherine", "cath": "catherine", "sar": "sarah",
}
NAME_NOISE = {"mr", "mrs", "miss", "dr", "capt", "col", "gen", "rev", "hon",
              "maj", "esq", "jr", "sr", "or", "and", "the", "of"}


def name_tokens(value: str) -> list:
    return [t for t in re.split(r"[^A-Za-z]+", str(value or "").lower())
            if t and t not in NAME_NOISE]


def expand(token: str) -> str:
    return FORENAME_ABBREV.get(token, token)


def forename_agrees(forename: str, surname_of: str, printed: str) -> bool:
    """Does the name this row PRINTS agree with the forename of the identity?

    True when the row prints no forename at all — a bare surname is silent, not a
    contradiction — and when any forename token it does print is the identity's,
    its initial, or a printed abbreviation of it.
    """
    want = [t for t in name_tokens(forename) if t != surname_of]
    got = [t for t in name_tokens(printed) if t != surname_of]
    if not want or not got:
        return True
    head = expand(want[0])
    for t in got:
        t = expand(t)
        if t == head or (len(t) == 1 and t == head[0]) or (len(head) == 1 and head == t[0]):
            return True
    return False


def agreeing(identity: dict, appearances: list) -> tuple:
    """(the rows whose printed forename agrees, the ones it does not)."""
    fore = identity.get("forename") or ""
    sur = (identity.get("surname") or "").lower()
    keep, drop = [], []
    for app in appearances:
        printed = app.get("normalized") or app.get("as_read")
        (keep if forename_agrees(fore, sur, printed) else drop).append(app)
    return keep, drop


REGRADE_DATE = "2026-09-04"

# The abstention. `to.grade` is null on these rows and the ladder says why.
ABSTAIN_RULE = "G5"

# The sources a regrade may reason about: the ones the identity master itself
# cites for this identity. A card citing anything else is outside the ladder's
# field of view — see the note above.
def in_view(appearances: list) -> set:
    view: set = set()
    for app in appearances:
        sid = app.get("source_id")
        if not sid:
            continue
        view.add(sid)
        view.add(SOURCE_ALIAS.get(sid, sid))
        if app.get("domain") == "newspapers":
            for _prefix, paper in PAPERS:
                view.add(paper)
    return view


def people_by_id(docs: dict) -> dict:
    out = {}
    for path, doc in docs.items():
        for person in doc.get("persons") or []:
            if person.get("id"):
                out[person["id"]] = (path, person)
    return out


def regrade_refusal(change: dict, applied: bool, unseen: list) -> dict:
    """The refusal a downgrade writes onto the person, whichever way it went."""
    if applied:
        return {
            "regraded_on": REGRADE_DATE,
            "rule": change["rule"],
            # `withheld`, not `refused`, and `regraded_on`, not `date`: the read-map
            # gate reads a field's LEAF name across the renderer, and a leaf called
            # `date` or `refused` collides with text the walkthrough genuinely reads.
            # A distinct leaf keeps the gate's phantom test meaningful (T-0515).
            "withheld": change["from"]["grade"],
            "reason": (f"The ladder's {change['rule']} is the highest rung this identity's "
                       f"evidence reaches, and every source this card cites was read by the "
                       f"consolidation that fired it. The grade it held is refused rather "
                       f"than kept, and the refusal is the record (T-0515)."),
        }
    return {
        "regraded_on": REGRADE_DATE,
        "rule": change["rule"],
        "withheld": f"the downgrade to {change['to']['grade']}",
        "reason": (f"This card rests on {len(unseen)} thing(s) the consolidation did not read — "
                   f"{', '.join(unseen[:4])}{' and others' if len(unseen) > 4 else ''}. "
                   f"{change['rule']} fired on the seven domains the ladder reads and says "
                   f"nothing about the evidence outside them, so the grade stands. The same "
                   f"reasoning the ladder's own G5 gives for abstaining (T-0515)."),
    }


def regrade_decisions(docs: dict, proposal: dict, master: dict):
    """Every proposed change to a committed person, ruled on. Pure — see build().

    Returns (applied, refusals): `applied` is a list of (change, path, person_id,
    blocks, sources, refusal|None); `refusals` is a list of (change, reason).
    """
    idents = {i["id"]: i for i in master.get("identities", [])}
    apps = {i["id"]: [a for a in (i.get("appearances") or [])
                      if a.get("domain") != "town_layer"
                      and a.get("evidence_class") not in REFUSED_CLASSES]
            for i in master.get("identities", [])}
    people = people_by_id(docs)
    applied, refusals = [], []
    for change in sorted(proposal.get("changes_to_existing_people", []),
                         key=lambda c: (c.get("person_id") or "", c.get("identity") or "")):
        pid = change.get("person_id")
        found = people.get(pid)
        if not found:
            refusals.append((change, "the town no longer carries this person"))
            continue
        path, person = found
        if change["rule"] == ABSTAIN_RULE or change["to"].get("grade") is None:
            refusals.append((change, "the ladder abstains on this identity (G5) and an "
                                     "abstention is not a grade"))
            continue
        identity = idents.get(change["identity"], {})
        appearances, disagree = agreeing(identity, apps.get(change["identity"], []))
        blocks, sources = evidence_blocks(change, appearances)
        if not blocks:
            refusals.append((change, "the evidence rows do not support the proposal: no "
                                     "appearance in a domain this pass writes a block for"))
            continue
        # Every rung this mode applies rests on a SECOND thing — a second source
        # for G1a/G1b, a list plus another for G2b/G2e, more than one appearance
        # for the subtype it takes off. One surviving class is not that, and a
        # proposal that only had two because a same-surname stranger supplied one
        # of them is refused rather than quietly applied.
        classes = {e.get("list") for rows in blocks.values() for e in rows}
        if len(classes) < 2 and disagree:
            refusals.append((change, "the evidence rows do not support the proposal: its "
                                     "second source prints a forename this identity does "
                                     "not carry"))
            continue
        refusal = None
        if change["direction"] == "down":
            unseen = sorted(set(person.get("sources") or []) - in_view(appearances))
            # A research pass that ASSERTED this identity is a second reading the
            # ladder has not made. `synthesize_resident_research.py` promotes a
            # letter-list person to `attested` only on an adjudicated outcome with
            # a stated discriminator (christy_nathan's paired-name continuity in
            # T-0484 is the one this proposal reaches), and a rung fired on the
            # bare classes of the same two sources is not a finding about that
            # argument. Declining also keeps the tree self-consistent: the
            # synthesis would put the grade straight back.
            if not unseen and (person.get("resident_research") or {}).get("asserted_identity"):
                unseen = ["an adjudicated resident_research outcome "
                          f"({(person['resident_research'] or {}).get('ticket') or 'unticketed'}"
                          f", {(person['resident_research'] or {}).get('outcome')})"]
            if unseen:
                refusals.append((change, f"a downgrade on evidence the ladder has not read "
                                         f"({len(unseen)} source(s) outside its seven domains)"))
                # The decline is written onto the person all the same: it is the
                # record that the proposal was ruled on rather than missed.
                applied.append((change, path, pid, {}, [], regrade_refusal(change, False, unseen)))
                continue
            refusal = regrade_refusal(change, True, [])
        applied.append((change, path, pid, blocks, sources, refusal))
    return applied, refusals


def apply_regrade(docs: dict, index: dict, applied: list) -> set:
    """Write the decisions onto the tree in memory. Returns the paths touched."""
    people = people_by_id(docs)
    touched: set = set()
    for change, path, pid, blocks, sources, refusal in applied:
        _p, person = people[pid]
        if blocks:
            if change["to"].get("grade"):
                person["grade"] = change["to"]["grade"]
            sub = change["to"].get("resident_subtype")
            if sub:
                person["resident_subtype"] = sub
            else:
                person.pop("resident_subtype", None)
            for key, rows in blocks.items():
                person[key] = rows
            person["sources"] = sorted(set(person.get("sources") or []) | set(sources))
            rr = person.setdefault("resident_research", {})
            rr["regraded_on"] = REGRADE_DATE
            rr["rule"] = change["rule"]
        if refusal is not None:
            rr = person.setdefault("resident_research", {})
            keep = [r for r in (rr.get("refusals") or [])
                    if not (r.get("rule") == refusal["rule"]
                            and r.get("regraded_on") == refusal["regraded_on"])]
            rr["refusals"] = keep + [refusal]
        touched.add(path)

    # The manifest rows and the counts the panels read. Re-derived from the WHOLE
    # tree rather than from the rows this run touched (T-0715): a run where the
    # proposal is already spent touches nothing, and used to leave every drifted row
    # exactly as it found it.
    rebuild(index, docs)
    return touched


def regrade(preload: dict | None = None):
    docs = ({p: json.loads(t) for p, t in preload.items() if p != INDEX}
            if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    index = (json.loads(preload[INDEX]) if preload is not None and INDEX in preload
             else load(INDEX))
    proposal, master = load(PROPOSAL), load(MASTER)
    applied, refusals = regrade_decisions(docs, proposal, master)
    touched = apply_regrade(docs, index, applied)
    files = {path: dumps(docs[path], 1) for path in touched}
    files[INDEX] = dumps(index, 1)
    return files, applied, refusals


def regrade_report(applied, refusals) -> None:
    real = [a for a in applied if a[3]]
    declines = [a for a in applied if not a[3]]
    print(f"REGRADED — {len(real)} person(s) the town already carried")
    by_rule: dict = {}
    by_move: dict = {}
    for change, _path, _pid, _b, _s, _r in real:
        by_rule[change["rule"]] = by_rule.get(change["rule"], 0) + 1
        move = (f"{change['from']['grade']}/{change['from'].get('resident_subtype') or '-'}"
                f" -> {change['to']['grade']}/{change['to'].get('resident_subtype') or '-'}")
        by_move[move] = by_move.get(move, 0) + 1
    for move, n in sorted(by_move.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {move}")
    for rule, n in sorted(by_rule.items()):
        print(f"  {n:5d}  {rule}")
    print(f"\nREFUSED — {len(refusals)} proposal(s), with the reason "
          f"({len(declines)} of them written onto the person as a refusal)")
    tally: dict = {}
    for _change, reason in refusals:
        tally[reason_key(reason)] = tally.get(reason_key(reason), 0) + 1
    for reason, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {reason}")
    print()
    for change, _path, pid, blocks, _s, refusal in sorted(real, key=lambda a: a[2]):
        print(f"  REGRADE {pid[:36]:38s} {change['rule']:4s} "
              f"{change['direction']:12s} {'+refusal' if refusal else ''}")
    for change, reason in sorted(refusals, key=lambda c: c[0].get('person_id') or ''):
        print(f"  REFUSE  {(change.get('person_id') or '')[:36]:38s} {change['rule']:4s} {reason}")


def regrade_counts(docs: dict, index: dict) -> dict:
    people = [p for d in docs.values() for p in d.get("persons") or []]
    out = {"attested": 0, "inferred": 0, "projected_resident": 0}
    for person in people:
        out[person["grade"]] = out.get(person["grade"], 0) + 1
        if person.get("resident_subtype") == "projected_resident":
            out["projected_resident"] += 1
    out["census_1840_linked"] = (index.get("counts") or {}).get("census_1840_linked")
    return out


# ---------------------------------------------------------------------------
# the gate — the invariants this pass owes, proved on whatever tree it is run on
# ---------------------------------------------------------------------------

def gate_problems(docs: dict, index: dict) -> list:
    problems = []
    rows = {r["id"]: r for r in index.get("households") or []}
    mine = {p: d for p, d in docs.items() if minted_by(p, d, PASS_NAME, PREFIX)}
    for path, doc in sorted(mine.items()):
        where = doc.get("id") or path.stem
        people = doc.get("persons") or []
        if len(people) != 1:
            problems.append(f"{where}: {len(people)} member(s); this pass mints households "
                            f"of one and never invents a family")
        for p in people:
            if not p.get("civic_mint"):
                problems.append(f"{where}/{p.get('id')}: lost civic_mint, the flag that keeps "
                                f"this cohort's evidence strength legible")
            if not any(p.get(k) for k in BLOCK_KEYS):
                problems.append(f"{where}/{p.get('id')}: carries no evidence block; a person "
                                f"minted here is minted FROM a reading and must show it")
            if p.get("occupation", {}).get("value") != "none_recorded":
                problems.append(f"{where}/{p.get('id')}: gained a trade; no source in this "
                                f"pass records one")
            if p.get("grade") not in MINTABLE_GRADES:
                problems.append(f"{where}/{p.get('id')}: grade {p.get('grade')!r} is not one "
                                f"this pass may assign")
            if not p.get("sources"):
                problems.append(f"{where}/{p.get('id')}: cites no source")
            for key in BLOCK_KEYS:
                for e in p.get(key) or []:
                    if not e.get("as_read") or not e.get("rule"):
                        problems.append(f"{where}/{p.get('id')}: an evidence row without a "
                                        f"reading or the rule that fired it")
                    if bracketed_name_appearance(e):
                        problems.append(f"{where}/{p.get('id')}: civic-minted from bracketed "
                                        f"name evidence {e['as_read']!r}; T-1115 requires the "
                                        f"verbatim reading to reach refusal 7")
            classes = {e.get("list") for k in BLOCK_KEYS for e in p.get(k) or []}
            if classes and classes <= {LETTER_LIST_CLASS}:
                problems.append(f"{where}/{p.get('id')}: rests on a letter list alone, which "
                                f"is the pass beside this one's pool")
            if classes and classes <= {MUSTER_CLASS}:
                problems.append(f"{where}/{p.get('id')}: rests on the 1832 muster alone, and "
                                f"an 1832 enrollment dates a man rather than minting him")
        for key in ("lives_at", "works_at"):
            if (doc.get(key) or {}).get("value"):
                problems.append(f"{where}: gained a {key}; the placement sweep does that, "
                                f"once the resident list is complete")
        arr = doc.get("arrival") or {}
        if arr.get("precision") != "not_later_than":
            problems.append(f"{where}: arrival precision {arr.get('precision')!r}; every "
                            f"arrival this pass writes is a BOUND and says so")
        if (doc.get("present_on_scene_date") or {}).get("value") == "present" \
                and not (doc.get("present_on_scene_date") or {}).get("note"):
            problems.append(f"{where}: present_on_scene_date without its reasoning")
        # THE PROPERTY REFUSAL, PROVED ON THE CARD (T-1117). presence_block keeps the
        # 1833 tax list out of the bracket, but a refusal that lives only in the code
        # that writes the file can be undone without anything going red. So the tree is
        # asked directly: a household that says `present` must own a record which places
        # the PERSON at or before the day, and a tax roll is not one — it names the
        # owner of ground inside the town, resident, absent or three years dead.
        # AND THE PLACE-IN-1835 REFUSAL ON THE SAME CARD (T-1131). Same question, second
        # class of answer: a source whose own domain declares `places_in_1835: false` may
        # not be the at-or-before leg either. It is asked of the tree and not only of the
        # derivation for the same reason — and this refusal is deliberately NOT applied
        # to the after leg, because a death notice may perfectly well close the bracket
        # from above. THE AFTER LEG ITSELF IS ASKED ABOUT SINCE T-1136, below: a
        # different question, about the DATE a record permits rather than the class it
        # belongs to.
        if (doc.get("present_on_scene_date") or {}).get("value") == "present":
            refused_classes = NOT_A_PRESENCE_CLASS | set(not_in_1835_classes())
            evidence = [e for p in people for k in BLOCK_KEYS for e in p.get(k) or []]
            legs = [e for e in evidence if e.get("list") not in refused_classes
                    and (b := bound_of(e.get("describes_date"))) and b <= SCENE_DATE]
            if not legs:
                offered = sorted({e.get("list") for e in evidence
                                  if e.get("list") in refused_classes
                                  and (b := bound_of(e.get("describes_date")))
                                  and b <= SCENE_DATE})
                problems.append(f"{where}: reads `present` with no at-or-before leg but "
                                f"{', '.join(offered) or 'nothing'}. The 1833 tax list is "
                                f"a property roll and names owners and estates, not people "
                                f"at the place (T-1117); a death notice dates a death and "
                                f"declares `places_in_1835: false` for its whole class "
                                f"(T-1131). Neither can carry a claim about where a man "
                                f"stood on 1 July 1835")
            # AND THE FAR LEG, ON THE SAME CARD (T-1136). A bracket has two legs and
            # only one of them was ever asked of the tree. The at-or-after leg holds
            # only if EVERY day the record permits falls at or after the scene date, so
            # a bare `1835` — which may describe 2 January as easily as 31 December —
            # closes nothing over 1 July, and neither does a death notice printed
            # `April 8, 1835`. A death notice is NOT refused here, unlike above: a man
            # who died at Chicago in 1885 was at Chicago in 1885, and that is a real far
            # leg. Only the property roll is refused on this side as on the other.
            far = [e for e in evidence if e.get("list") not in NOT_A_PRESENCE_CLASS
                   and (f := floor_of(e.get("describes_date"))) and f >= SCENE_DATE]
            if not far:
                straddling = sorted({e.get("list") for e in evidence
                                     if e.get("list") not in NOT_A_PRESENCE_CLASS
                                     and (b := bound_of(e.get("describes_date")))
                                     and b >= SCENE_DATE})
                problems.append(f"{where}: reads `present` with no at-or-after leg but "
                                f"{', '.join(straddling) or 'nothing'}. A record whose "
                                f"date range STRADDLES 1 July 1835 is silent about which "
                                f"side of the day it fell on, and a silence closes no "
                                f"bracket (T-1136)")
        # THE NOT-CHICAGO REFUSAL, PROVED ON THE CARD (T-1129). The refusal above lives
        # in `decide()`, and a refusal that lives only in the code that writes the file
        # can be undone — by a hand edit, by another pass, by a carry-over — without
        # anything going red. So the tree is asked directly: a card whose church readings
        # are ALL rows the register places outside Chicago, and which holds no other
        # evidence block, is a person standing in this town on a marriage celebrated 180
        # miles away. It is asked of every card here, not only of this pass's, because
        # the four T-1129 found were this pass's and the next one need not be.
        church = [e for p in people for e in p.get("church_evidence") or []]
        other = [e for p in people for k in BLOCK_KEYS if k != "church_evidence"
                 for e in p.get(k) or []]
        if church and not other and all(e.get("record_id") in not_chicago_records()
                                        for e in church):
            problems.append(f"{where}: rests on church reading(s) "
                            f"{', '.join(sorted(e.get('record_id') or '?' for e in church))} "
                            f"and nothing else, and every one of them carries "
                            f"`at_chicago: false` — the register places that entry outside "
                            f"Chicago, so the card claims a town the record denies (T-1129)")
        row = rows.get(where)
        if row is None:
            problems.append(f"{where}: minted here and absent from the manifest")
        elif not row.get("civic_mint"):
            problems.append(f"{where}: the manifest row does not carry civic_mint")
    counted = (index.get("counts") or {}).get("civic_mint")
    actual = sum(1 for d in mine.values() for p in d.get("persons") or []
                 if p.get("civic_mint"))
    if counted != actual:
        problems.append(f"counts.civic_mint is {counted!r} and the tree holds {actual}")
    return problems


def read_tree():
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    return docs, load(INDEX)


def gate() -> int:
    docs, index = read_tree()
    problems = gate_problems(docs, index)
    for p in problems:
        print(f"   {p}")
    if problems:
        print(f"   {len(problems)} problem(s)")
        return 1
    mine = sum(1 for p, d in docs.items() if minted_by(p, d, PASS_NAME, PREFIX))
    print(f"   OK: {mine} civic-minted household(s) claim a person, a reading and no more")
    return 0


# ---------------------------------------------------------------------------
# the assertions, broken on purpose
# ---------------------------------------------------------------------------

def _row(**kw):
    base = {"identity": "id_fixture", "name": "Ezra Fixture", "canonical_person_id": None,
            "rule": "G1a", "grade": "attested", "resident_subtype": None,
            "evidence": [], "evidence_classes": []}
    base.update(kw)
    return base


def _app(**kw):
    base = {"domain": "civic", "record_id": "poll_1835_999",
            "source_id": "chicago_voter_lists_1833_1835_irad", "as_read": "E. Fixture",
            "normalized": "Ezra Fixture", "locator": "poll_1835",
            "describes_date": "1835", "evidence_class": "poll_1835"}
    base.update(kw)
    return base


REFUSAL_CASES = (
    ("a mint the ladder does not reach",
     _row(grade="not_1835_resident", rule="G0"), [_app()], set(),
     "the ladder does not reach"),
    ("a person the town already carries",
     _row(canonical_person_id="fixture_ezra"), [_app()], set(),
     "the town already carries"),
    ("a later-only source used as a residency source",
     _row(rule="G3", grade="inferred"),
     [_app(domain="directories", source_id="fergus_chicago_directory_1843",
           locator="South Water", describes_date="1843", evidence_class="directory_1843")],
     set(), "no appearance inside the scene year"),
    ("a letter list as the only scene-year source",
     _row(rule="G2e", grade="inferred"),
     [_app(domain="newspapers", source_id="chicago_newspapers_1833_1835",
           locator="chicago_democrat_1834_07_02#c032", describes_date="1834-07-02",
           evidence_class="newspaper_letter_list")],
     set(), "the pass beside this one's pool"),
    ("a duplicate of an existing person",
     _row(), [_app()], {"fixture_ezra"}, "a duplicate of a person the town already carries"),
    ("an 1832 enrollment and nothing else",
     _row(rule="G3", grade="inferred"),
     [_app(source_id="blackhawk_war_chicago_enrollments_isa", locator="muster",
           describes_date="1832", evidence_class="muster_1832")],
     set(), "an 1832 enrollment alone"),
    ("a firm, not a person",
     _row(name="Fixture & Co"), [_app()], set(), "a firm, not a person"),
    ("a bracketed display name",
     _row(name="Ezra [Fixture]"), [_app()], set(), "bracketed the name as uncertain"),
    ("a half surname whose brackets were stripped from the display name",
     _row(name="H G Hub"), [_app(as_read="H. G. Hub[…]")], set(),
     "bracketed the name as uncertain"),
    ("an internal supply whose brackets were stripped from the display name",
     _row(name="E K Zie"), [_app(as_read="E. K[in]zie")], set(),
     "bracketed the name as uncertain"),
    # T-1129. The fixture cites a REAL row of the register — `st_cyr_marriage_002_2`,
    # Mary Durbin, married at Bear Creek in Sangamon County on 20 May 1834 — because the
    # refusal is read from the corpus and a fixture id would test the tool against
    # itself. If the reader stops marking that row, this case goes red, which is the
    # point: the ruling moved and the ticket reopens.
    ("a church entry the register places outside Chicago, and nothing else",
     _row(name="Mary Durbin", rule="G2c", grade="inferred"),
     [_app(domain="church", source_id="st_cyr_register_ichr_v4",
           record_id="st_cyr_marriage_002_2", locator="bride", as_read="Mary Durbin",
           describes_date="1834-05-20", evidence_class="church_1833_1835")],
     set(), "the register places outside Chicago"),
    ("a name with nothing that could be a surname",
     _row(name="E. S."), [_app()], set(), "no name the corpus prints as a family name"),
    ("a mint with no evidence block",
     _row(rule="G3", grade="inferred"),
     [_app(domain="town_layer", evidence_class="town_layer")], set(),
     "no evidence block this pass writes"),
)


def self_test() -> int:
    failed = 0
    for label, row, apps, known, want in REFUSAL_CASES:
        ok, reason = decide(row, apps, known, set(), set(), set())
        if ok or want not in reason:
            failed += 1
            print(f"   FAIL {label}: accepted={ok} reason={reason!r}, wanted {want!r}")
    ok, reason = decide(_row(), [_app()], set(), set(), set(), set())
    if not ok:
        failed += 1
        print(f"   FAIL the control case is refused: {reason!r}")
    # THE NOT-CHICAGO REFUSAL (T-1129), and every edge it is supposed to have: the set is
    # read from the corpus, it refuses the whole identity when nothing else stands inside
    # the window, and it drops the reading rather than the person when something does.
    bear_creek = {"st_cyr_marriage_002_1", "st_cyr_marriage_002_2",
                  "st_cyr_marriage_003_1", "st_cyr_marriage_003_2",
                  "st_cyr_marriage_004_1", "st_cyr_marriage_004_2"}
    if not bear_creek <= not_chicago_records():
        failed += 1
        print(f"   FAIL the register no longer marks the Bear Creek marriages "
              f"`at_chicago: false` — missing "
              f"{sorted(bear_creek - not_chicago_records())}. The refusal is read from "
              f"data/research/church/, so reopen T-1129 rather than re-arguing it here")
    _bear = dict(domain="church", source_id="st_cyr_register_ichr_v4",
                 record_id="st_cyr_marriage_002_2", locator="bride",
                 as_read="Mary Durbin", describes_date="1834-05-20",
                 evidence_class="church_1833_1835")
    ok, reason = decide(_row(), [_app(**_bear), _app(describes_date="1834",
                                                     evidence_class="poll_1834",
                                                     record_id="poll_1834_999",
                                                     locator="poll_1834")],
                        set(), set(), set(), set())
    if not ok:
        failed += 1
        print(f"   FAIL a Bear Creek reading beside a clean poll entry refused the whole "
              f"identity; the refusal is about the READING: {reason!r}")
    kept = mintable_appearances([_app(**_bear), _app()])
    if any(a.get("record_id") == "st_cyr_marriage_002_2" for a in kept):
        failed += 1
        print("   FAIL a reading the register places outside Chicago is still spent onto "
              "the card, where it would cite its source and bound an arrival (T-1129)")
    mixed = [_app(record_id="press_uncertain", as_read="H. G. Hub[…]"),
             _app(record_id="poll_clean", as_read="Hubbard, Henry G.")]
    ok, reason = decide(_row(name="Henry G Hubbard"), mixed,
                        set(), set(), set(), set())
    if not ok:
        failed += 1
        print(f"   FAIL a clean independent appearance cannot rescue an identity from a "
              f"separate bracketed reading: {reason!r}")
    if [a["record_id"] for a in mintable_appearances(mixed)] != ["poll_clean"]:
        failed += 1
        print("   FAIL a surviving identity still writes its bracketed appearance onto the card")
    ok, reason = decide(_row(), [_app()], set(), set(), set(), {"fixture_ezra"})
    if ok or "the residency-tested pass above this one" not in reason:
        failed += 1
        print(f"   FAIL this pass does not give way to the pass above it: {reason!r}")
    ok, reason = decide(_row(canonical_person_id="fixture_ezra"), [_app()], set(), set(),
                        {"fixture_ezra"})
    if not ok:
        failed += 1
        print(f"   FAIL this pass refuses its OWN previous answer read back: {reason!r}")
    ok, reason = decide(_row(), [_app()], set(), {"fixture_ezra"}, set(), set())
    if ok or "researched this person and left them out" not in reason:
        failed += 1
        print(f"   FAIL a researched-and-excluded person is minted: {reason!r}")
    if MUSTER_LADDER not in json.dumps(
            load(DATA / "research" / "civic" / "records"
                 / "blackhawk_war_1832_chicago.json").get("the_ladder", "")):
        failed += 1
        print("   FAIL the muster's own ladder line has moved; refusal 4 quotes a "
              "sentence the record no longer makes")

    # the record itself, on the control fixture: the shape the gate then polices
    doc = record(_row(), [_app()], {}, set())
    person = doc["persons"][0]
    for label, cond in (
            ("the person carries the civic_mint flag", person.get("civic_mint")),
            ("the person carries an evidence block", person.get("civic_evidence")),
            ("the evidence row carries the rule that fired", 
             (person.get("civic_evidence") or [{}])[0].get("rule") == "G1a"),
            ("the arrival is a bound", doc["arrival"]["precision"] == "not_later_than"),
            ("the arrival bound is the year's end, not its start",
             doc["arrival"]["value"] == "1835-12-31"),
            ("a bound after the scene date leaves presence uncertain",
             doc["present_on_scene_date"]["value"] == "uncertain"),
            ("no dwelling is dealt", doc["lives_at"]["value"] is None),
            ("no trade is read in", person["occupation"]["value"] == "none_recorded"),
            ("the source resolves to a file, not a domain label",
             person["sources"] == ["chicago_voter_lists_1833_1835_irad"]),
    ):
        if not cond:
            failed += 1
            print(f"   FAIL {label}")

    # THE PROPERTY REFUSAL STILL FIRES (T-1117). A tax roll may not bracket the day, and
    # the same evidence on a poll list still may — otherwise the refusal would be a
    # blanket that quietly emptied the bracket for everyone.
    taxed = record(_row(), [_app(describes_date="1833", evidence_class="tax_1833",
                                 record_id="tax_1833_999", locator="tax_1833"),
                            _app(domain="directories", describes_date="1843",
                                 evidence_class="directory_1843",
                                 record_id="f1843_999", locator="F",
                                 source_id="fergus_chicago_directory_1843")], {}, set())
    if taxed["present_on_scene_date"]["value"] != "uncertain":
        failed += 1
        print("   FAIL the 1833 tax list brackets the scene date again; it is a property "
              "roll and names no person at the place (T-1117)")
    if "PROPERTY ROLL" not in taxed["present_on_scene_date"]["note"]:
        failed += 1
        print("   FAIL a withdrawn bracket does not say what withdrew it")
    if "PROPERTY ROLL" not in taxed["arrival"]["note"]:
        failed += 1
        print("   FAIL an arrival bound off a tax roll still reads as a man at Chicago")
    # THE PLACE-IN-1835 REFUSAL (T-1131), and every edge it is supposed to have. The
    # class is read from the domain, refuses the at-or-before leg, reads `absent` off a
    # death before the day, and leaves the after leg alone.
    if not_in_1835_classes() != frozenset({DEATH_CLASS}):
        failed += 1
        print(f"   FAIL the domains no longer declare places_in_1835: false for "
              f"{DEATH_CLASS!r} — got {sorted(not_in_1835_classes())}. The refusal is "
              f"read from data/research/, so reopen T-1131 rather than re-arguing it here")

    def _death(**kw):
        base = dict(domain="old_settlers", source_id="fergus_1843_old_settler_death_notices",
                    record_id="fdn0999", locator="F", as_read="Fixture, Ezra",
                    describes_date="Oct. 25, 1830", evidence_class=DEATH_CLASS)
        base.update(kw)
        return _app(**base)

    _dir = dict(domain="directories", describes_date="1843",
                evidence_class="directory_1843", record_id="f1843_999", locator="F",
                source_id="fergus_chicago_directory_1843")
    dead = record(_row(), [_death(), _app(**_dir)], {}, set())
    if dead["present_on_scene_date"]["value"] != "absent":
        failed += 1
        print("   FAIL a death five years before the scene date still brackets the day; "
              "a death notice is not a presence (T-1131)")
    if "places_in_1835" not in dead["present_on_scene_date"]["note"]:
        failed += 1
        print("   FAIL the withdrawn bracket does not name the declaration that withdrew it")
    if dead["arrival"]["precision"] != "not_later_than" \
            or dead["arrival"]["value"] != "1830-10-25":
        failed += 1
        print("   FAIL the place-in-1835 refusal moved the ARRIVAL bound; it is a rule "
              "about the presence bracket and a man who died at Chicago was at Chicago. "
              "The bound is the notice's printed DAY, `Oct. 25, 1830`, and not the end of "
              "its year (T-1136): the page gives the day and the bound may not throw it "
              "away and call the loss precision")
    # the after leg is NOT swallowed: a real leg below, a death notice above
    survives = record(_row(), [_app(describes_date="1834", evidence_class="poll_1834",
                                    record_id="poll_1834_999", locator="poll_1834"),
                               _death(describes_date="April 13, 1885")], {}, set())
    if survives["present_on_scene_date"]["value"] != "present":
        failed += 1
        print("   FAIL the place-in-1835 refusal has swallowed the AFTER leg too; a man "
              "who died at Chicago in 1885 was at Chicago in 1885 (T-1131)")
    # and a contradiction is not resolved by picking a side
    disputed = record(_row(), [_death(),
                               _app(describes_date="1834", evidence_class="poll_1834",
                                    record_id="poll_1834_999", locator="poll_1834")],
                      {}, set())
    if disputed["present_on_scene_date"]["value"] != "uncertain":
        failed += 1
        print("   FAIL a death read as `absent` over a later record that names the man in "
              "the town; that is an identity question and this pass does not settle it")
    # a refused leg with no usable one left says which leg it refused
    alone = record(_row(), [_death(), _death(record_id="fdn0998",
                                             describes_date="Oct. 25, 1831")], {}, set())
    if alone["present_on_scene_date"]["value"] != "uncertain" \
            or "places_in_1835" not in alone["present_on_scene_date"]["note"]:
        failed += 1
        print("   FAIL two death notices that disagree on the year are read as one death")
    forced_dead = json.loads(json.dumps(dead))
    forced_dead["present_on_scene_date"]["value"] = "present"
    if not any("T-1131" in p for p in gate_problems(
            {pathlib.Path("hh_fixture.json"): forced_dead},
            {"households": [{"id": forced_dead["id"], "civic_mint": True,
                             "present_on_scene_date": "present"}]})):
        failed += 1
        print("   FAIL the gate accepts `present` carried by a death notice alone")

    # T-1136: THE TWO LEGS READ OPPOSITE ENDS OF THE DATE RANGE.
    for label, value, want in (
            ("a full date is a single day", "1835-05-20", ("1835-05-20", "1835-05-20")),
            ("a bare year runs the whole year", "1835", ("1835-01-01", "1835-12-31")),
            ("a year-month is the month", "1834-06", ("1834-06-01", "1834-06-30")),
            ("a printed day is read for its day", "April 8, 1835",
             ("1835-04-08", "1835-04-08")),
            ("an abbreviated month is read too", "Dec. 1, 1848",
             ("1848-12-01", "1848-12-01")),
            ("the other printed order is read too", "d. 14 Mar. 1861",
             ("1861-03-14", "1861-03-14")),
            ("a month with no day is still narrower than a year", "July 1835",
             ("1835-07-01", "1835-07-31")),
            ("a day the month cannot hold withdraws to the month", "Feb. 30, 1835",
             ("1835-02-01", "1835-02-28")),
            ("no date is no range", "", None),
    ):
        if date_range(value) != want:
            failed += 1
            print(f"   FAIL {label}: date_range({value!r}) is {date_range(value)!r}, "
                  f"wanted {want!r}")
    # the bare year that straddles the day closes no bracket over it, on either leg
    straddle = record(_row(), [_app(describes_date="1834", evidence_class="poll_1834",
                                    record_id="poll_1834_999", locator="poll_1834"),
                               _app(describes_date="1835", evidence_class="poll_1835",
                                    record_id="poll_1835_999", locator="poll_1835")],
                      {}, set())
    if straddle["present_on_scene_date"]["value"] != "uncertain":
        failed += 1
        print("   FAIL a bare `1835` closes the bracket over 1 July again; it may "
              "describe 2 January as easily as 31 December and says nothing about which "
              "side of the day the man was on (T-1136)")
    # AND A DEATH BEFORE THE DAY CANNOT CLOSE IT FROM ABOVE, HOWEVER THE PAGE PRINTS IT.
    # `hh_vanderbogart_henry`'s shape, which is what found this: two at-or-before legs
    # that are real, a death notice printed `April 8, 1835` for its only far leg, and one
    # of those legs dated AFTER the death. The death is no far leg — 8 April is three
    # months before the day — and it is no `absent` either, because a record names the
    # man at Chicago after it and this pass does not settle that contradiction (T-1131).
    # What is left is a card with no far leg at all, and that is `uncertain`.
    _press = dict(evidence_class="press_1833_1835", locator="press",
                  source_id="chicago_newspapers_1833_1835", domain="newspapers")
    vanderbogart = record(_row(), [_app(describes_date="1834-02-04",
                                        record_id="press_999", **_press),
                                   _app(describes_date="1835-05-20",
                                        record_id="press_998", **_press),
                                   _death(describes_date="April 8, 1835")], {}, set())
    if vanderbogart["present_on_scene_date"]["value"] != "uncertain":
        failed += 1
        print("   FAIL a death notice printed `April 8, 1835` — three months BEFORE the "
              "scene date — still closes the bracket over 1 July; its year was read and "
              "its day was thrown away (T-1136)")
    # and read alone, that same notice is a death and not a silence
    early_death = record(_row(), [_app(describes_date="1834-02-04",
                                       record_id="press_999", **_press),
                                  _death(describes_date="April 8, 1835")], {}, set())
    if early_death["present_on_scene_date"]["value"] != "absent":
        failed += 1
        print("   FAIL reading the notice's printed DAY lost the `absent` it earns: with "
              "no record naming the man after 8 April 1835 he was dead before the day")
    # a real far leg still closes: a bare 1843 is wholly after the day
    forced_far = json.loads(json.dumps(straddle))
    forced_far["present_on_scene_date"]["value"] = "present"
    if not any("T-1136" in p for p in gate_problems(
            {pathlib.Path("hh_fixture.json"): forced_far},
            {"households": [{"id": forced_far["id"], "civic_mint": True,
                             "present_on_scene_date": "present"}]})):
        failed += 1
        print("   FAIL the gate accepts `present` whose far leg straddles the scene date")

    polled = record(_row(), [_app(describes_date="1834", evidence_class="poll_1834",
                                  record_id="poll_1834_999", locator="poll_1834"),
                             _app(domain="directories", describes_date="1843",
                                  evidence_class="directory_1843",
                                  record_id="f1843_999", locator="F",
                                  source_id="fergus_chicago_directory_1843")], {}, set())
    if polled["present_on_scene_date"]["value"] != "present":
        failed += 1
        print("   FAIL the property refusal has swallowed the poll lists too")
    forced = json.loads(json.dumps(taxed))
    forced["present_on_scene_date"]["value"] = "present"
    if not any("property roll" in p for p in gate_problems(
            {pathlib.Path("hh_fixture.json"): forced},
            {"households": [{"id": forced["id"], "civic_mint": True,
                             "present_on_scene_date": "present"}]})):
        failed += 1
        print("   FAIL the gate accepts `present` carried by a tax roll alone")

    # T-1115's tree-side witness. The decision fixture above proves a new bad
    # reading is refused; this mutation proves an already-committed card cannot
    # keep one if a generator or hand edit bypasses decide().
    bracketed = record(_row(), [_app()], {}, set())
    bracketed["persons"][0]["civic_evidence"][0]["as_read"] = "H. G. Hub[…]"
    if not any("bracketed name evidence" in p for p in gate_problems(
            {pathlib.Path("hh_fixture.json"): bracketed},
            {"households": [{"id": bracketed["id"], "civic_mint": True,
                             "present_on_scene_date":
                                 bracketed["present_on_scene_date"]["value"]}],
             "counts": {"civic_mint": 1}})):
        failed += 1
        print("   FAIL the gate accepts a civic-minted card carrying bracketed name evidence")

    # a foreign block on one of this pass's cards survives a re-derivation
    base = record(_row(), [_app()], {}, set())
    prior = json.loads(json.dumps(base))
    prior["directories"] = {"note": "written by another pass"}
    prior["persons"][0]["resident_research"] = {"ticket": "T-0485"}
    kept = carry_over(record(_row(), [_app()], {}, set()), prior)
    prior["persons"][0]["sources"] = (prior["persons"][0]["sources"]
                                      + ["chicago_tribune_1882_04_25_old_settler_deaths"])
    prior["persons"][0]["note"] = prior["persons"][0]["note"] + " THE ROLL IS WORTH THIS."
    kept = carry_over(record(_row(), [_app()], {}, set()), prior)
    if kept.get("directories") != {"note": "written by another pass"} \
            or kept["persons"][0].get("resident_research") != {"ticket": "T-0485"}:
        failed += 1
        print("   FAIL another pass's findings do not survive a re-derivation")
    if "chicago_tribune_1882_04_25_old_settler_deaths" not in kept["persons"][0]["sources"] \
            or not kept["persons"][0]["note"].endswith("THE ROLL IS WORTH THIS."):
        failed += 1
        print("   FAIL a citation another pass wrote onto the card does not survive")

    # T-1137's exact failure: changing one character of this mint's prefix used to
    # make the startswith() carry fail and silently cut every marked paragraph after
    # it.  The appended finding owns its marker, so the derived prose may now move.
    marked = json.loads(json.dumps(base))
    marked["persons"][0]["note"] += " OLD SETTLERS, 1882 — THE ROLL IS WORTH THIS."
    changed = record(_row(), [_app()], {}, set())
    changed["persons"][0]["note"] += " DERIVED PROSE CHANGED."
    survived = carry_over(changed, marked)
    if not survived["persons"][0]["note"].endswith(
            "OLD SETTLERS, 1882 — THE ROLL IS WORTH THIS."):
        failed += 1
        print("   FAIL changed derived prose silently deletes another pass's finding")
    if carry_over(record(_row(), [_app()], {}, set()),
                  dict(prior, source_pass="letter_list")).get("directories"):
        failed += 1
        print("   FAIL carry_over took a record that is not this pass's")

    # a kinship another pass ruled on comes back in the slot the layer keeps for it
    with_kin = carry_over(record(_row(), [_app()], {}, set()),
                          dict(prior, kin=[{"person": "p", "relation": "wife",
                                            "household": "hh_x", "value": "q",
                                            "confidence": "attested"}]))
    if "kin" not in with_kin:
        failed += 1
        print("   FAIL a kin row written by another pass is re-derived away")
    elif list(with_kin).index("kin") != list(with_kin).index("persons") - 1:
        failed += 1
        print("   FAIL a carried kin block does not land immediately before persons")

    # the two source labels the identity master hands over unresolved
    if source_of(_app(domain="newspapers", source_id="chicago_newspapers_1833_1835",
                      locator="chicago_democrat_1835_02_11#c003")) \
            != "chicago_democrat_1833_1835":
        failed += 1
        print("   FAIL a Democrat mention does not resolve to the Democrat")
    if source_of(_app(domain="census_1840", source_id="census_1840_cook_county")) \
            != "census_1840_chicago_familysearch_images":
        failed += 1
        print("   FAIL the census domain label does not resolve to a committed source")

    # and the gate's own assertions, broken on a copy of the committed tree
    docs, index = read_tree()
    if gate_problems(docs, index):
        print("   the committed tree does not pass its own gate; fix that first")
        return 1
    mine = [p for p, d in docs.items() if minted_by(p, d, PASS_NAME, PREFIX)]
    if mine:
        victim = sorted(mine)[0]

        def broken(mutate):
            d = {pathlib.Path(k): v for k, v in
                 json.loads(json.dumps({str(k): v for k, v in docs.items()})).items()}
            i = json.loads(json.dumps(index))
            mutate(d, i)
            return gate_problems(d, i)

        cases = [
            ("a person loses its evidence blocks",
             lambda d, i: [d[victim]["persons"][0].pop(k)
                           for k in BLOCK_KEYS if k in d[victim]["persons"][0]],
             "no evidence block"),
            ("a person loses the civic_mint flag",
             lambda d, i: d[victim]["persons"][0].pop("civic_mint"), "civic_mint"),
            ("a household gains a roof",
             lambda d, i: d[victim]["lives_at"].update(value="sauganash_hotel"), "lives_at"),
            ("a person gains a trade",
             lambda d, i: d[victim]["persons"][0]["occupation"].update(value="carpenter"),
             "gained a trade"),
            ("a household gains an invented wife",
             lambda d, i: d[victim]["persons"].append(
                 dict(d[victim]["persons"][0], id="invented_wife")), "member(s)"),
            ("the arrival stops being a bound",
             lambda d, i: d[victim]["arrival"].update(precision="year"), "arrival precision"),
            ("the manifest row loses the flag",
             lambda d, i: [r.pop("civic_mint") for r in i["households"]
                           if r["id"] == d[victim]["id"]], "civic_mint"),
        ]
        for label, mutate, want in cases:
            found = broken(mutate)
            if not any(want in p for p in found):
                failed += 1
                print(f"   FAIL {label}: the gate did not name it ({found[:2]})")
    if failed:
        print(f"   {failed} assertion(s) failed")
        return 1
    print(f"   OK: {len(REFUSAL_CASES)} refusals, the record's own shape and the gate's "
          f"assertions all fire")
    return 0


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--scale", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--regrade", action="store_true",
                    help="T-0515: apply the ladder to the people the town already carries")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.regrade:
        files, applied, refusals = regrade()
        if args.report:
            regrade_report(applied, refusals)
            return 0
        if args.check:
            stale = [path for path, text in sorted(files.items())
                     if not path.exists() or path.read_text(encoding="utf-8") != text]
            for path in stale:
                print(f"   {path.relative_to(ROOT)} does not match the regrade")
            if stale:
                print(f"   {len(stale)} file(s) differ; run --regrade")
                return 1
            print(f"   OK: {len([a for a in applied if a[3]])} regraded person(s) re-derive "
                  f"byte for byte, {len(refusals)} refused")
            return 0
        for path, text in sorted(files.items()):
            path.write_text(text, encoding="utf-8")
        print(f"wrote {len(files)} file(s); "
              f"{len([a for a in applied if a[3]])} regraded, {len(refusals)} refused")
        return 0
    if args.gate:
        return gate()
    if args.scale:
        scale_report()
        return 0

    files, accepted, refusals, mine_paths = build()
    if args.report:
        report(accepted, refusals)
        return 0
    if args.check:
        stale = []
        for path, text in sorted(files.items()):
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(path)
        for path in sorted(mine_paths):
            if path not in files:
                stale.append(path)
        for path in stale:
            print(f"   {path.relative_to(ROOT)} does not match the derivation")
        if stale:
            print(f"   {len(stale)} file(s) differ; run --build")
            return 1
        print(f"   OK: {len(accepted)} civic resident(s) re-derive byte for byte")
        return 0

    for path in sorted(mine_paths):
        if path not in files:
            path.unlink()
    for path, text in sorted(files.items()):
        path.write_text(text, encoding="utf-8")
    print(f"wrote {len(files)} file(s); {len(accepted)} minted, {len(refusals)} refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
