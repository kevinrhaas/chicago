"""Every name the post office held a letter for becomes a resident (T-0378, T-0379).

    python3 tools/mint_letter_list_residents.py             write
    python3 tools/mint_letter_list_residents.py --check     re-derive and diff
    python3 tools/mint_letter_list_residents.py --report    the mint and every refusal
    python3 tools/mint_letter_list_residents.py --scale     what this pass did to the town
    python3 tools/mint_letter_list_residents.py --gate      the invariants the ruling owes
    python3 tools/mint_letter_list_residents.py --self-test those assertions, broken on purpose

WHAT THIS IS FOR, AND THE RULING THAT SET ITS SCALE.

The owner's ruling of 2026-08-28 is that a name in the post office's list of
uncalled-for letters is enough to make somebody a resident. `register_1835.json`
carries such people the town does not hold in the thousands, and
`tools/mint_documented_residents.py` cannot reach one of them: its pool is a
`new_resident` WITH a trade, and a letter-list name has none.

That left a question this pass could not answer for itself. Put the pool through the
refusals below and most of a thousand names survive — a town of a few hundred people
where three residents in four would be a name on a post-office list and nothing else.
That is a question about the SCALE of the reconstruction rather than about evidence, so
it was measured, put to the owner as ticket T-0379 with those numbers in view, and
ruled on 2026-08-30:

    HOLD ALL OF THEM. Every name the refusals admit joins the town.

So this pass no longer takes a slice of the pool. It mints the WHOLE admitted set — the
names the office held a letter for in several returns and the names it held one for
once, alike — and the ranking below decides precedence between them rather than
membership.

NO COUNT IS WRITTEN DOWN HERE, DELIBERATELY, and the ruling makes that stricter rather
than looser. The corpus grows on most weeks the loop runs, and a figure copied into
prose is wrong the next time a transcription lands — the ones this docstring used to
carry (1,530 in the pool, 726 surviving, ten in more than one return) were all stale
inside a fortnight, and the ticket's own headline figure, 705 survivors, was already
712 on the morning the ruling was implemented. Run `--scale`: it counts the town this
pass produced, on whatever the tree currently holds, and prints the share of it that is
a name on a post-office list and nothing else.

THE RANKING, AND WHY THIS PASS STILL HAS ONE. Membership is settled by the refusals now;
what the ranking decides is who wins refusal 8, one surname to one household. The
Democrat reprinted one return of uncalled-for letters over consecutive weekly issues, so
a name's MENTIONS are not its RETURNS: grouping a name's issues at a gap of more than
sixty days separates a reprint from a genuinely later list. A name held in two returns
sixteen months apart is somebody a correspondent kept believing was reachable at
Chicago, which is the strongest thing a letter list can say about residence, so those
names rank first. The rest follow by the DATE of the return that printed them, newest
first — a letter waiting on the scene date itself says more about who was at Chicago on
1 July 1835 than one waiting eighteen months earlier. Both halves are rules over the
whole pool rather than a choice within it.

WHAT THE RECORD CLAIMS, AND WHAT IT REFUSES TO.

A letter list gives a name and nothing else — no trade, no street, no household, no
arrival. So these records claim a PERSON and no more: `occupation` is `none_recorded`
graded `reconstructed`, exactly as this dataset already writes the absence of a trade for
a wife or a child, and the dwelling, the division, the origin, the family and the party
are each written unattested in their own block. `letter_list_only: true` rides on the
person, because the parent ticket's whole point is that the two evidence strengths must
stay distinguishable forever: a letter-list name and a man who advertised his shop are
not the same claim, and `renderers/web/js/residents.js` says so on the card.

THE LIMIT THIS PASS CANNOT CLOSE, stated rather than hidden. The Chicago post office
served the country around the town as well as the town, so an uncalled-for letter is
evidence that its writer believed the addressee reachable at Chicago and not proof that
he slept there. Refusal 6 catches the ones the corpus places somewhere else by name; it
cannot catch a settler the corpus never places at all. A scan read, a land record or a
second corpus that places one of these people outside the town retires that record, and
the note on every one of them says so. At fifteen records that limit was a footnote on
each of them; at the scale the ruling set it is a property of the town, and
docs/LIBERTIES.md L182 is where it is admitted as one.

THE REFUSALS, all eight of `mint_documented_residents.py`'s, on the same reasoning, plus
the precedence rule this pass owes the one beside it, and one precondition of its own
that the ruling made load-bearing:

  0. `no return this pass can date` — every record has to carry the DATE of the return
     that printed it (T-0379's ruling; `--gate` proves it), and a mention whose claim id
     carries no readable issue date cannot supply one. It refuses nobody in the corpus
     as it stands and is written down anyway, because the alternative to refusing such a
     name is minting a record the gate would then have to fail.

  1. `garbled`                — the transcription bracketed the name as uncertain.
  2. `a firm, not a person`.
  3. `first evidence after the scene date` — AGENTS.md rule 3.
  4. `no surname the corpus prints`.
  5. `a surname and nothing else` — index.json's `darwin_of_canada` decision.
  6. `placed where this project cannot put him in the town`.
  7. `the town already names a <Surname>` — and for this pass that INCLUDES the
     households `mint_documented_residents.py` minted. A man the papers give a trade is
     better evidenced than a name on a letter list, so where the two passes would reach
     for one family name the documented pass keeps it and this one gives way.
  8. `surname already minted` — one surname, one household, across this pass.

WHY THE POOL READS `enrich` BACK. Same as the documented pass: the register is compiled
FROM the committed town, so the moment this pass mints somebody the compiler stops calling
him `new_resident`. An `enrich` whose target is one of THIS pass's own person ids is read
back as what it is — this pass's previous answer — so the derivation still holds the run
after it lands.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rebuild_resident_index import rebuild  # noqa: E402  (the manifest's one owner)
from resident_mint_carry import carry_resident_mint  # noqa: E402  (T-1137)
from identity_master_guard import (  # noqa: E402  (T-0843)
    IdentityGuard, blind_person_ids, refusal as guard_refusal,
)

DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
NAME_RULINGS = (DATA / "research" / "newspapers"
                / "letter_list_1834_01_01_name_rulings.json")

SCENE_DATE = "1835-07-01"
PREFIX = "hh_ll_"
PERSON_PREFIX = "ll_"
DIVISION = "unplaced"

# The `list` a press row carries when it IS a return of uncalled-for letters. Every
# other value on that block is an ordinary reading of the papers.
LETTER_LIST_CLASS = "newspaper_letter_list"

# The gap that separates one return of uncalled-for letters from the next. The
# Democrat reprinted a list over two and three consecutive weekly issues, so
# anything at a week's distance is the SAME return read twice; the returns
# themselves are quarterly. Sixty days is wider than any reprint run in this
# corpus and narrower than any interval between returns in it, and the names this
# admits as two-return are unchanged anywhere from 30 to 200 days.
#
# It used to also be a THRESHOLD: `RETURNS_REQUIRED = 2` kept this pass to the names
# held in more than one return and left the rest to the owner's decision (T-0379).
# The decision came back HOLD ALL OF THEM on 2026-08-30, so the number of returns is
# no longer a gate on membership — it is the first key of the ranking, and what the
# ranking now settles is refusal 8's precedence and nothing else.
RETURN_GAP_DAYS = 60

# The number of returns above which a name is ranked ahead of the dated head. Not a
# threshold for entry any more; see above.
RANKED_FIRST_RETURNS = 2

# ---------------------------------------------------------------------------
# THE RETURNS, AND THE PRINTINGS EACH OF THEM RAN OVER (T-0425)
# ---------------------------------------------------------------------------
#
# A letter list is a RETURN — the office's statement of what was still uncalled
# for on one day — and the Democrat printed one return over as many consecutive
# issues as it took. So the date on the issue an extraction pass happened to reach
# is not the date of the evidence. T-0331 counted the 1 January 1834 return over
# NINE printings; the extraction that produced this project's claims reached the
# fourth and the ninth of them, and `hh_conger_thomas` was therefore dated
# 1834-03-04 — nine weeks late, by an accident of which impression was read.
#
# Every row below is the DATE LINE the printing itself sets, quoted verbatim, with
# the deposit issue it stands in. Nothing is amended to agree with anything: where
# the impressions disagree the tally is stated and the losing setting stays visible.
#
# TWO RULES DECIDE WHAT A ROW IS ALLOWED TO CLAIM, and both are here because the
# bound is `not_later_than` and a `not_later_than` bound may be weak but may never
# be wrong:
#
#   * WHERE THE PRINTED DAY IS NOT READ BUT THE MONTH IS, the row takes the LAST
#     day of the printed month. The 1835 returns are the case: `on the Stat: day /
#     ot March, 1895` and `on the 50th ... day of June, 1` each lose the day and
#     keep the month, and a letter held on any day of March was held by 31 March.
#     The project declines to read `Stat:` as `31st` when it does not have to.
#   * THE BOUND IS NEVER LATER THAN THE EARLIEST PRINTING that carries the name —
#     `bound_for()` takes the minimum — because a return cannot be dated after the
#     issue that printed it.
#
# `date: None` is a return whose date line this project cannot read at all. It is
# not a hole: the bound falls back to the earliest printing carrying the name,
# exactly as before T-0425, and the record's own note says which of the two it used.
RETURNS = (
    {
        "date": "1834-01-01",
        "said": "the return of 1 January 1834",
        "printings": ("1834-01-07", "1834-01-14", "1834-01-21", "1834-01-28",
                      "1834-02-04", "1834-02-11", "1834-02-18", "1834-02-25",
                      "1834-03-04"),
        "date_lines": (
            ("1834-01-07", "EMAINING in the Post-Offiee at Chic / go, Ill. "
                           "January [1,] 1834."),
            ("1834-01-28", "EMAINING in the Port-Offiee at Ch / go, Ill. "
                           "Fammuary 1, 1604."),
            ("1834-02-04", "EMAINING in the Post- / go, Ill, January 3, 1934."),
            ("1834-02-25", "REMAINISG in the Pest[-Office at Chica]go, Il "
                           "January 1, 63[4]."),
            ("1834-03-04", "List of L | etters / ost-Offiee at Chica- / 34."),
        ),
        "basis": "three of the four legible date lines set January 1 and the fourth "
                 "sets January 3, a broken 1 in a setting that also renders the year "
                 "1934; the ninth printing, which is the one this project extracted "
                 "its March names from, keeps nothing of the date but `34.` and is "
                 "placed on this return by T-0331's concordance over the body text "
                 "(tools/letter_list_printings.py)",
    },
    {
        "date": "1834-04-01",
        "said": "the return of 1 April 1834",
        "printings": ("1834-04-01", "1834-04-08", "1834-04-16"),
        "date_lines": (
            ("1834-04-01", "of Litera |: / the Post Office a Chi / day of peer mea"),
            ("1834-04-08", "and the re- EMAINIG in the P / ey. IM. on the first day"),
            ("1834-04-16", "ef Letters FFIC / the Post Office at Chicego, | Sy' of F "
                           "/ at day of April, 1834."),
        ),
        "basis": "no one impression sets the whole line: the second prints the day "
                 "(`on the first day`) and the third the month and year (`[fir]st day "
                 "of April, 1834`), and the first loses both. Two impressions read side "
                 "by side is the instrument data/research/newspapers/README.md "
                 "prescribes (T-0328)",
    },
    {
        "date": "1834-07-01",
        "said": "the return of 1 July 1834",
        "printings": ("1834-07-02", "1834-07-09", "1834-07-16"),
        "date_lines": (
            ("1834-07-02", "MAINING in the Post-Office at Chica- / go, Ill. "
                           "July 1, 1834."),
            ("1834-07-09", ", go, Ill. July 1, 1834."),
            ("1834-07-16", "EMAINING in the Post-Office at Chica- / go, I!. "
                           "July 1, 1834."),
        ),
        "basis": "three impressions, three identical date lines, nothing to weigh",
    },
    {
        "date": "1834-10-01",
        "said": "the return of 1 October 1834",
        "printings": ("1834-10-22",),
        "date_lines": (
            ("1834-10-22", "EMAINING in the Post Office at Chi / R cago, Hl. "
                           "Oct. 1, ViS4."),
            ("1834-10-22", "Chicago, Oct. 1, 1834."),
        ),
        "basis": "one impression, but the day and month are clean in the heading and "
                 "the year, which the heading mangles to `ViS4`, is set again five "
                 "columns away over the postmaster's signature. No other printing of "
                 "this return is in the deposit",
    },
    {
        "date": "1835-03-31",
        "said": "the return of March 1835",
        "printings": ("1835-05-20",),
        "date_lines": (
            ("1835-05-20", "a ago, Cook Go, Mlinvis, om the Stat: day / "
                           "ot March, 1895,:"),
        ),
        "basis": "the month and the year are printed and the day is not: `Stat:` is "
                 "not read, and no reading of it is supplied. A letter held on any day "
                 "of March 1835 was held by the 31st, so the month's last day is the "
                 "bound the printed line actually supports. The Chicago list runs seven "
                 "weeks behind its own return here, which is why this row matters: the "
                 "printing is 1835-05-20",
    },
    {
        "date": "1835-06-30",
        "said": "the return of June 1835",
        "printings": ("1835-07-01",),
        "date_lines": (
            ("1835-07-01", "o: Letters. / G in the Post Office at Chi- / "
                           "County Illinois, on the 50th"),
            ("1835-07-01", "EMAINI / cago, Co / day of June, 1"),
        ),
        "basis": "the segmenter cut this heading down the middle and the two crops "
                 "reassemble to `[List] of Letters / [R]EMAINI[NG] in the Post Office "
                 "at Chi[ca]go, Co[ok] County Illinois, on the [?]0th day of June, "
                 "1[835]`. `50th` is not a day of any month and is not read; the month "
                 "is, so the bound is the last day of June",
    },
    {
        "date": None,
        "said": "the return printed on 19 August 1835, which sets no date line this "
                "project can read",
        "printings": ("1835-08-19",),
        "date_lines": (),
        "basis": "the deposit holds this issue as a .docx with no transcription text "
                 "beside it, and the extracted letter-list claims carry names only — no "
                 "heading, no date line. Whether it is a return of its own or a late "
                 "printing of the 30 June return is not decided here, and the bound "
                 "falls back to the printing",
    },
)

RETURN_OF_PRINTING = {issue: entry for entry in RETURNS
                      for issue in entry["printings"]}


def bound_for(earliest_printing: str) -> tuple[str, dict | None]:
    """The arrival bound a name printed in this run owes, and the return behind it.

    `earliest_printing` is the ISO date of the first issue that carries the name —
    what `return_dates()` reports, and what this pass used to write into `arrival`
    on its own. Where the run's return is dated, the bound is the return's date;
    where it is not, it stays the printing. Either way it is never later than the
    printing, because a return cannot be dated after the issue that printed it.
    """
    entry = RETURN_OF_PRINTING.get(earliest_printing)
    if entry and entry["date"]:
        return min(entry["date"], earliest_printing), entry
    return earliest_printing, entry


# Everything below is shared with tools/mint_documented_residents.py, which is the
# pass this one sits beside. Importing it would make one pass's refusals depend on
# the other's file being loadable; the two are deliberately independent programmes
# over the same register, and each states its own rules in its own docstring.
TITLES = {"dr", "mr", "mrs", "miss", "jr", "sr", "esq", "capt", "col", "maj",
          "rev", "messrs"}
FEMALE_TITLES = {"mrs", "miss"}
MALE_TITLES = {"mr"}
FIRM = re.compile(r"&| and |\bco\b|\bcompany\b", re.I)
UNCERTAIN = re.compile(r"\[|uncertain", re.I)
BARE_TOWN = {"chicago", "the town of chicago"}
STREETS = DATA / "streets" / "1835.json"
STRUCTURES = DATA / "structures"
PAPERS = (("chicago_democrat_", "chicago_democrat_1833_1835"),
          ("chicago_american_", "chicago_american_1835"))
MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc, indent=1):
    return json.dumps(doc, indent=indent, ensure_ascii=False) + "\n"


def words(name: str) -> list[str]:
    name = re.sub(r"\[[^\]]*\]", "", name or "").replace(".", " ").replace(",", " ")
    return [w for w in re.split(r"\s+", name.strip())
            if w and w.lower().strip("'") not in TITLES]


def titles_in(name: str) -> set[str]:
    raw = re.sub(r"\[[^\]]*\]", "", name or "").replace(".", " ").replace(",", " ")
    return {w.lower().strip("'") for w in re.split(r"\s+", raw.strip())} & TITLES


def full_word(token: str) -> bool:
    """Is this token a name, or is it an initial standing in for one? (T-0638)

    The post office prints an initial as one letter and a stop (`C.`), sometimes as
    a digit where the type or the scan failed (`8.`), sometimes as a two-character
    cluster the same way (`II.`, `IS.`, `I1.`), and it abbreviates a forename to two
    letters (`Wm.`). None of those can be a family name; three letters or more, with
    a letter somewhere in them, is the shortest thing this corpus prints that can.
    Deliberately conservative: it decides only whether a token could BE the surname,
    never which token is.
    """
    token = token.strip("'")
    return len(token) >= 3 and any(c.isalpha() for c in token)


def surname_is_first_token(name: str) -> bool:
    """Does this printing put the family name FIRST, with no comma to say so?

    T-0638. `surname()` below reads the last token as the family name, which is right
    for `Joel C. Mills` and wrong for `Mills Joel C.` — the post office's lists print
    both orders and only sometimes punctuate the second. The tell is that the token
    the plain rule lands on is not a name at all but an initial, while an earlier
    token is: `Mills Joel C.` ends on `C.`, `Perry A. 8.` on `8.`, `Nelts Wm.` on an
    abbreviated forename. When that happens the family name is the FIRST full token.
    """
    parts = words(name)
    if not parts:
        return False
    if "," in name:
        head = words(name.partition(",")[0])
        picked = head[-1] if head else parts[0]
    else:
        picked = parts[-1]
    return not full_word(picked) and any(full_word(w) for w in parts)


def surname(name: str) -> str:
    """The family name, lowercased, from either order the papers print it in."""
    parts = words(name)
    if not parts:
        return ""
    if surname_is_first_token(name):
        picked = next(w for w in parts if full_word(w))
    elif "," in name:
        head = words(name.partition(",")[0])
        picked = head[-1] if head else parts[0]
    else:
        picked = parts[-1]
    return picked.lower().strip("'").replace("'", "")


UNREAD = "[?]"
"""The corpus's own marker for an initial the printing did not deliver.

It is not invented here. The Chicago list of 1 January 1834 is already carried with
it — `[?] Blodget`, `[?] T. Miner`, `[?] B. Northrop`, `[?] Gay` — under that
column's stated rule that a bare surname with no initial is minted with the marker
"rather than joined to anybody already in the gazetteer"
(data/research/newspapers/extracted/chicago_democrat_1834_01_28.json). It says the
character was not read. It never says which character it was.
"""


def unread_initial(token: str) -> bool:
    """Is this token an initial slot the reading did not deliver? (T-0721)

    A DIGIT IS NEVER PART OF A NAME — the same principle `split_name` states in
    consolidate_resident_evidence.py, where it is the guard that stops the 1843
    directory's `Reading Room (Y. M. A.), 37 Clark, 2d story` minting a person. Here
    it lands on three of the town's own cards, whose middle initial the scan set as
    `8.` (an S), `8.` again, and `I1.` (an H): `Abbot, 8. G.`, `Perry A. 8.`,
    `Gabbs, James I1.`.
    """
    return any(ch.isdigit() for ch in token)


def comma_is_not_the_divider(name: str) -> bool:
    """Does the first comma of this printing fail to be the surname/forename mark?

    T-1217. `display()` reorders around the FIRST comma, on the standing assumption
    that a comma in a letter-list line is the office's mark for "family name first".
    One printing in this corpus breaks that assumption by setting the family name in
    the MIDDLE: `Es,Jones, High`, whose first comma divides `Es` from `Jones, High`
    and is not a divider at all. Reordered around it the card reads `Jones, High Es`
    and LEADS with the family name, which is the one order a card must never be in.

    The condition is stated as what it literally is, so it can be counted: the family
    name `surname()` reads lies PAST the first comma while a word stands before it.
    That is the only way a first comma can be sitting where no divider belongs — a
    true surname-first printing has its family name in the head (`Hail, Aifred`), and
    a forename-first printing with a stray comma has it in the tail with an EMPTY
    head (`, Phitip D,`, whose surname the crop lost altogether, and which this rule
    therefore leaves exactly where it stands rather than promoting a lost reading).

    A SQUARE-BRACKET SUPPLY IS REFUSED HERE RATHER THAN REORDERED. `words()` drops
    bracketed text before `surname()` ever sees it, so on `Lo[vering], Richard` the
    family name comes back `richard` — the defect T-1155 carries, and this rule will
    not move a card on a reading it knows to be unreliable. Twelve readings in the
    pool are in that state and every one of them is left alone.

    MEASURED, as this ticket's acceptance requires, over the whole letter-list pool:
    1,970 distinct printings in data/research/newspapers/register_1835.json, of which
    877 carry a comma, of which this predicate is true of exactly ONE — `Es,Jones,
    High`. Across the 736 letter-list cards on disk it moves one card. The wider rule
    T-1121 measured and refused — put the token `surname()` picked last, wherever it
    fell — moved 84.
    """
    if "," not in name or "[" in name:
        return False
    fam = surname(name)
    if not fam:
        return False
    head = [w.lower().strip("'").replace("'", "") for w in words(name.partition(",")[0])]
    tail = [w.lower().strip("'").replace("'", "") for w in words(name.partition(",")[2])]
    return bool(head) and fam not in head and fam in tail


def display(name: str) -> str:
    """'Foot, S.' -> 'S. Foot'. The papers print both orders; a card shows one.

    T-0638 taught it the unpunctuated second order too: `Mills Joel C.` -> `Joel C.
    Mills`. Only the ORDER of the printed tokens moves, and the stop that followed
    the leading surname goes with it — no token is recased, respelled or dropped,
    because every one of these names is an OCR reading and this pass does not
    correct readings (the register of the ones that look misread is
    tools/register_letter_list_suspicions.py, written to
    data/research/residents/letter_list_reading_suspicions.json).

    T-1121 TAKES THE PRINTING'S PUNCTUATION OUT OF WHAT IS REORDERED. The comma
    is the mark that says which order a line is in; once the tokens have been put
    in the other order it is a mark saying something untrue, and `surname()` reads
    it and believes it. `Hugunin, Leonard, C.` sets a second comma inside the
    forename side, the reordering moved only the head, and the card read `Leonard,
    C. Hugunin` — which parses back as a surname-first printing and gives the
    family name `leonard`, against the record id and against the gazetteer's other
    printing of the same man. Deliberately the SMALLEST fix that closes it: a more
    general rule — put the token `surname()` picked last, wherever it fell — was
    measured over the 1,050-name pool and moved 84 readings, most of them correct
    ones, because a square-bracket supply and a bare honorific are not forenames
    (`[uncertain: Bester], James`, `Baby, Mrs.`). The rule is not the defect; what
    the reordering left behind was.

    T-0721 ADDS THE ONE THING A CARD MAY SAY ABOUT A READING, WHICH IS THAT THERE
    ISN'T ONE. An initial the scan set as a digit is replaced by `UNREAD`, and by
    nothing else: the surname is never touched, no letter is supplied, and the
    verbatim printing stays where verbatim printings belong — in the extracted
    column and in the gazetteer's `as_printed`, both of which this pass leaves
    alone. What changes is that the card stops asserting `8.` is a name.
    """
    if "," in name:
        if comma_is_not_the_divider(name):
            # T-1217. REORDER AROUND THE COMMA THE FAMILY NAME STANDS BEFORE,
            # NOT AROUND THE FIRST ONE. A card is forename-then-family, and in a
            # surname-first printing it is the office's comma that says which
            # tokens are the forenames: the ones AFTER it. On `Es,Jones, High`
            # that divider is the SECOND comma — the entry is `Jones, High`, and
            # `Es` stands in front of the family name where nothing of this name
            # belongs. So the forenames lead, what stood before the family name
            # follows them, and the family name ends the card: `High Es Jones`.
            #
            # `Es` IS KEPT AND NOT PROMOTED, which is the whole of the judgement
            # here. This project's own registry of suspected misreadings already
            # holds this printing (tools/register_letter_list_suspicions.py):
            # "reads as a run-on of two entries — the tail of one name and the
            # head of the next, set without the break between them", with the
            # right-hand side NULL, meaning the letters cannot be read with
            # confidence and the project declines to guess. A card must not turn
            # that into a forename. Leading with `Es` would do exactly that: every
            # crosswalk in the layer reads the first token's initial, and the card
            # would have acquired a new `inferred` tie to `E. M. Jones`, cabinet
            # and chair manufacturer of Dearborn street in 1844, off a letter the
            # project has said it cannot read.
            #
            # THE TRAP THE TICKET NAMES IS THE COMMA-ONLY FIX. Dropping the
            # punctuation and nothing else gives `Jones High Es`, whose last word
            # is `Es` — and compile_scene.py's `surname_of()` files a card under
            # its last word, so it would sort in the town directory under `es`,
            # away from the other Joneses. Moving the family name is what keeps
            # the directory right, and it is why the comma may only go once the
            # order has been made true.
            #
            # No token is recased, respelled, supplied or removed. The verbatim
            # setting stays where verbatim settings belong — the extracted column
            # and the gazetteer's `as_printed`, neither of which this touches.
            fam = surname(name)
            tokens = [t for t in re.split(r"[,\s]+", name.strip()) if t]
            at = next(i for i, t in enumerate(tokens)
                      if t.lower().strip("'.,").replace("'", "") == fam)
            shown = tokens[at + 1:] + tokens[:at] + [tokens[at]]
            return mark_unread(" ".join(shown), name)
        head, _, tail = name.partition(",")
        # T-1121. A CARD'S NAME IS ORDERED, NOT PUNCTUATED. The office sometimes
        # sets a SECOND comma inside the forename side — `Hugunin, Leonard, C.` —
        # and reordering around the first comma alone left that one standing, so
        # the card read `Leonard, C. Hugunin`. Given-first is the one order a card
        # shows and it says so by its order; a comma left in it is read straight
        # back as a surname-first printing, and `surname()` then answers `leonard`.
        # Only a comma the reordering has made UNTRUE is dropped, and it is
        # dropped only where it is measurably lying: where the family name read
        # off the ordered string with the comma is not the one read off it
        # without. No token is recased, respelled, supplied or removed, which is
        # what keeps this a reordering and not a correction of the reading.
        # (`Es,Jones, High` used to reach this branch and leave by it carrying a
        # comma that was right by accident; T-1217 turned it back above, because
        # its first comma is not a divider at all.)
        tail = tail.strip()
        shown = f"{tail} {head.strip()}".strip() if tail else head.strip()
        plain = re.sub(r"\s+", " ", shown.replace(",", " ")).strip()
        if surname(shown) != surname(plain):
            shown = plain
        return mark_unread(shown, name)
    tokens = name.split()
    if len(tokens) >= 2 and surname_is_first_token(name):
        moved = tokens[0]
        if full_word(moved) and moved.endswith("."):
            moved = moved[:-1]
        return mark_unread(" ".join(tokens[1:] + [moved]), name)
    return mark_unread(name.strip(), name)


def mark_unread(shown: str, printed: str) -> str:
    """Replace every unread initial in an ordered display name with `UNREAD`.

    THE FAMILY NAME IS NEVER MARKED. A card whose surname is the unreadable token
    has lost the only thing that could ever match it to anybody, and blanking it
    would turn a bad reading into a nameless record; that is a different fault and
    this pass leaves it exactly as printed for the register to carry. Nothing in the
    corpus is in that state today, and the assertion is here so that if one ever is,
    it is refused rather than quietly emptied.
    """
    if not any(unread_initial(t) for t in shown.split()):
        return shown
    fam = surname(printed)
    return " ".join(
        UNREAD if (unread_initial(token)
                   and token.lower().strip("'.,").replace("'", "") != fam)
        else token
        for token in shown.split()
    )


def slug(name: str) -> str:
    """T-0638: an apostrophe JOINS inside a token, it does not split it. The
    period's Scots and Irish prefix and its contracted forenames are one word each
    — `M'Clintock` is `mclintock`, not `m_clintock`, and `Fred'k` is `fredk` — so
    eight Scots and Irish surnames stop sorting under `m`. `St Cyr`, whose two parts
    are separated by a space and not an apostrophe, is untouched.
    """
    plain = " ".join(words(name)).lower().replace("'", "")
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", plain)).strip("_")


def plain_fragment(name: str) -> str:
    """surname_given..., the shape the hand-authored households already use.

    Duplicated from mint_documented_residents.py rather than imported — see this
    file's own note above on why the two passes are independent programmes.
    `plain_fragment("B. S. Morris")` -> `morris_b_s`; T-0599.
    """
    fam = surname(name)
    given: list[str] = []
    dropped = False
    for w in words(name):
        if not dropped and w.lower().strip("'").replace("'", "") == fam:
            dropped = True
            continue
        given.append(w)
    return slug(fam + " " + " ".join(given)) if given else slug(fam)


def minted_by(path, doc: dict, pass_name: str, legacy_prefix: str) -> bool:
    """Was this household minted by the named pass — recognized either by its
    legacy filename prefix or by its `source_pass` field (T-0599)."""
    return path.name.startswith(legacy_prefix) or doc.get("source_pass") == pass_name


def household_id(cand_name: str, prefix: str, pass_name: str, docs: dict,
                 taken_ids: set[str]) -> str:
    """The household id for a candidate — see mint_documented_residents.py's copy
    of this function for the full rationale. Duplicated rather than imported."""
    legacy_id = prefix + slug(cand_name)
    base_id = "hh_" + plain_fragment(cand_name)
    for hid in (legacy_id, base_id):
        path = HOUSEHOLDS / f"{hid}.json"
        if path in docs and minted_by(path, docs[path], pass_name, prefix):
            return hid
    candidate_id, n = base_id, 2
    while (HOUSEHOLDS / f"{candidate_id}.json") in docs or candidate_id in taken_ids:
        candidate_id = f"{base_id}_{n}"
        n += 1
    return candidate_id


def issue_date(claim_id: str) -> datetime.date | None:
    m = re.search(r"(\d{4})_(\d{2})_(\d{2})", claim_id.split("#")[0])
    if not m:
        return None
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def issue_of(claim_id: str) -> str:
    """'chicago_democrat_1834_06_11#c003' -> 'the Democrat of 11 June 1834, column 3'."""
    stem = claim_id.split("#")[0]
    col = claim_id.split("#")[1] if "#" in claim_id else ""
    d = issue_date(claim_id)
    if d is None:
        return claim_id
    paper = "the American" if "american" in stem else "the Democrat"
    tail = f", column {int(col[1:])}" if col.startswith("c") and col[1:].isdigit() else ""
    return f"{paper} of {d.day} {MONTHS[d.month - 1]} {d.year}{tail}"


def returns_of(mentions) -> list[list[str]]:
    """A name's mentions grouped into the RETURNS they are printings of.

    Consecutive issues carrying the same list are one return read more than once;
    a gap wider than RETURN_GAP_DAYS is the next list. Mentions with no readable
    issue date fall into the run they are printed among rather than being dropped.
    """
    dated = sorted(((issue_date(c), c) for c in mentions),
                   key=lambda p: (p[0] or datetime.date.min, p[1]))
    groups: list[list[str]] = []
    last: datetime.date | None = None
    for when, cid in dated:
        if not groups or (when and last and (when - last).days > RETURN_GAP_DAYS):
            groups.append([])
        groups[-1].append(cid)
        last = when or last
    return groups


def return_dates(mentions) -> list[str]:
    """The ISO date of each RETURN that printed a name, earliest first.

    A return is dated by the first of its printings that carries a readable issue
    date, which for a reprint run is the issue the list first appeared in. This is
    the machine-readable half of T-0379's ruling: every minted person carries the
    dates of the returns behind them, so a reader — and `--gate` — can tell a name
    printed on the scene date from one printed eighteen months earlier without
    parsing prose. A group no printing can date contributes nothing, and refusal 0
    then refuses the candidate rather than minting a record with a hole in it.
    """
    out = []
    for group in returns_of(mentions):
        for cid in group:
            when = issue_date(cid)
            if when:
                out.append(when.isoformat())
                break
    return out


def paper_for(claim_ids) -> list[str]:
    out = []
    for cid in claim_ids:
        for prefix, sid in PAPERS:
            if cid.startswith(prefix) and sid not in out:
                out.append(sid)
    return out


def cited(mentions) -> str:
    head = "; ".join(issue_of(c) for c in mentions[:6])
    if len(mentions) <= 6:
        return head
    return f"{head}, and {len(mentions) - 6} further mention(s)"


# ---------------------------------------------------------------------------
# what the town already holds
# ---------------------------------------------------------------------------

def in_town_places() -> set[str]:
    """Every place name this project can resolve INSIDE the town it models."""
    def norm(s):
        return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()

    places = set(BARE_TOWN)
    for street in load(STREETS)["streets"]:
        name = norm(street.get("name_1835"))
        if name:
            places.add(name)
            places.add(name.replace(" street", "").strip())
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load(path)
        if isinstance(doc.get("name"), str) and norm(doc["name"]):
            places.add(norm(doc["name"]))
        for aka in doc.get("aka") or []:
            if isinstance(aka, str) and norm(aka):
                places.add(norm(aka))
    return places


def town_family_names(docs: dict, index: dict, skip_prefix: str | None = PREFIX) -> set[str]:
    """The family names the committed dataset already has something to say about.

    THIS PASS'S OWN OUTPUT IS EXCLUDED and nothing else is — refusal 7's precedence
    rule, and this pass sits LAST in the three-way order that
    `mint_documented_residents.MINTED_PREFIXES` documents. The two passes above it
    skip these `hh_ll_` records, so neither derivation is changed by anything minted
    here; this one sees both `hh_doc_` and `hh_placed_` and gives way to them.

    `skip_prefix=None` is what --scale-report reads the town through: the cohort it
    prices is a LATER pass than this one, so the households this one has already
    minted are committed and standing, and a surname they hold is a surname the town
    names.

    T-0599: `skip_prefix` still names this pass's legacy prefix, but the test also
    recognizes a household minted by this pass AFTER that change — carrying a
    plain id and `source_pass: "letter_list"` instead — via `minted_by()`.
    """
    known: set[str] = set()
    for path, doc in docs.items():
        if skip_prefix and minted_by(path, doc, "letter_list", skip_prefix):
            continue
        for person in doc.get("persons") or []:
            fam = surname(person.get("name") or "")
            if fam:
                known.add(fam)
    for entry in index.get("researched_not_resident") or []:
        fam = surname(entry.get("name") or "")
        if fam:
            known.add(fam)
    return known


# ---------------------------------------------------------------------------
# the mint
# ---------------------------------------------------------------------------

def norm_place(s: str) -> str:
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def letter_list_pool(register: dict, own_pass: frozenset[str] = frozenset()) -> list[dict]:
    """Every letter-list-only name the town does not hold.

    Includes this pass's own previous answer, read back as an `enrich` on one of its
    own person ids — see the docstring's last paragraph. The legacy `ll_` prefix
    still says that on its own for any household not yet migrated to a plain id
    (T-0599); `own_pass` names the ones that have, by their own source_pass field.
    """
    return [p for p in register["persons"]
            if p.get("letter_list_only")
            and (p.get("action") == "new_resident"
                 or (p.get("action") == "enrich"
                     and (str(p.get("action_target") or "").startswith(PERSON_PREFIX)
                          or str(p.get("action_target") or "") in own_pass)))]


def apply_refusals(candidates: list[dict], gazetteer: dict, known: set[str],
                   in_town: set[str], guard=None, blind=frozenset()):
    """The nine refusals, in order, over an already-ranked list of candidates.

    Held apart from `mint` because --scale-report prices a DIFFERENT cohort out of
    the same pool, and the price is only worth anything if it is paid through these
    exact rules rather than a second implementation of them that could drift.
    Refusal 8 depends on the order it is handed, so ranking is the caller's job.

    `guard` is T-0843's ninth refusal — the identity master, consulted for the
    surnames the proxy in `known` is entitled not to see. It is a PARAMETER and not a
    module-level load because the caller owns the precedence: `blind` has to be the
    same households `known` skipped, and only the caller knows which cohort it is
    pricing. A caller that hands none gets the eight rules it always had.
    """
    taken: set[str] = set()
    accepted, refusals = [], []
    for cand in candidates:
        gaz = gazetteer[cand["id"]]
        name = cand["name"]
        fam = surname(name)
        outside = [p for p in (gaz.get("associated_places") or [])
                   if norm_place(p) not in in_town]
        reason = None
        if not return_dates(gaz["mentions"]):
            reason = "no return this pass can date"
        elif UNCERTAIN.search(name):
            reason = "garbled"
        elif FIRM.search(name):
            reason = "a firm, not a person"
        elif cand["first_seen"] > SCENE_DATE:
            reason = "first evidence after the scene date"
        elif not fam:
            reason = "no surname the corpus prints"
        elif len(words(name)) < 2:
            reason = "a surname and nothing else"
        elif outside:
            reason = ("placed where this project cannot put him in the town ("
                      + "; ".join(outside) + ")")
        elif fam in known:
            reason = f"the town already names a {fam.title()}"
        elif guard is not None and (hit := guard.holder(name, blind_to=blind)) is not None:
            reason = guard_refusal(hit)
        elif fam in taken:
            reason = "surname already minted"
        if reason:
            refusals.append((cand["id"], name, len(returns_of(gaz["mentions"])), reason))
            continue
        taken.add(fam)
        accepted.append((cand, gaz))
    return accepted, refusals


def first_return(gaz: dict) -> datetime.date:
    """The date of the earliest return that printed this name, for ranking."""
    dates = return_dates(gaz["mentions"])
    return datetime.date.fromisoformat(dates[0]) if dates else datetime.date.min


def rank(pool: list[dict], gazetteer: dict) -> list[dict]:
    """The whole pool in the order refusal 8 resolves collisions by (T-0379).

    Two bands, and each is a rule rather than a sample:

      * names the office held a letter for in more than one return, strongest
        first — a correspondent still writing months later is the strongest thing
        a letter list can say about residence;
      * then the rest by the date of the return that printed them, NEWEST first —
        with only one return to go on, `printings` counts a reprint run rather than
        evidence, and what does vary is how close the letter was to the scene date.

    Membership is not decided here. Every name in the pool is a candidate and the
    refusals settle it; this only decides which of two people sharing a surname the
    town keeps.
    """
    def returns(p):
        return len(returns_of(gazetteer[p["id"]]["mentions"]))

    multi = [p for p in pool if returns(p) >= RANKED_FIRST_RETURNS]
    single = [p for p in pool if returns(p) < RANKED_FIRST_RETURNS]
    multi.sort(key=lambda p: (-returns(p), -len(gazetteer[p["id"]]["mentions"]),
                              p["first_seen"], p["id"]))
    single.sort(key=lambda p: (-first_return(gazetteer[p["id"]]).toordinal(),
                               -len(gazetteer[p["id"]]["mentions"]),
                               p["first_seen"], p["id"]))
    return multi + single


def mint(docs: dict, index: dict):
    """Choose who joins the town. Returns (accepted, refusals)."""
    register = load(REGISTER)
    gazetteer = {p["id"]: p for p in load(GAZETTEER)["persons"]}
    known = town_family_names(docs, index)
    # T-0843. The surname test above skips this pass's own households — refusal 7's
    # precedence rule — which is exactly where a duplicate it minted last run would
    # hide. The identity master resolves on surname AND forename signature, so it
    # sees the collision the proxy cannot; it is consulted blind to the same
    # households, so this pass stays re-derivable against its own output.
    guard = IdentityGuard.load()
    blind = blind_person_ids(
        docs, lambda path, doc: minted_by(path, doc, "letter_list", PREFIX))
    in_town = in_town_places()
    own_pass = frozenset(doc["head"] for doc in docs.values()
                         if doc.get("source_pass") == "letter_list")

    return apply_refusals(rank(letter_list_pool(register, own_pass), gazetteer),
                          gazetteer, known, in_town, guard=guard, blind=blind)


# ---------------------------------------------------------------------------
# the records
# ---------------------------------------------------------------------------

def arrival_note(bound: str, earliest_printing: str, entry: dict | None) -> str:
    """Why this household's bound is the date it is, and which of the two rules set it.

    T-0425. The bound is the RETURN's date where the return is dated, and the earliest
    PRINTING that carries the name where it is not, and a reader may not have to guess
    which — so the note says so in its first six words either way.
    """
    tail = (f"Somebody was writing to this name at Chicago by {bound} and at no stated "
            f"time before it; nothing says when they came.")
    if entry and entry["date"]:
        late = (datetime.date.fromisoformat(earliest_printing)
                - datetime.date.fromisoformat(bound)).days
        printed = ("" if not late else
                   f" The earliest issue this project reads the name in is "
                   f"{earliest_printing}, {late} day{'' if late == 1 else 's'} later; "
                   f"that gap is an accident of which impression an extraction pass "
                   f"reached, and it is not evidence.")
        return (f"A BOUND FROM THE RETURN, NOT AN ARRIVAL. The office's list of letters "
                f"uncalled-for is a RETURN — its statement of what was still unclaimed "
                f"on ONE day — and the paper reprinted one return over as many "
                f"consecutive issues as it took, so the bound is dated by "
                f"{entry['said']} and not by the issue it was read in (T-0425).{printed} "
                f"{tail} The date lines the printings set, and how they were weighed, "
                f"stand beside this rule in tools/mint_letter_list_residents.py.")
    why = (f"{entry['said'].capitalize()} — so the bound falls back to the earliest "
           f"printing that carries the name"
           if entry else
           "This project holds no dated return for the list this name stands in, so the "
           "bound falls back to the earliest printing that carries the name")
    return (f"A BOUND FROM THE PAPER, NOT AN ARRIVAL. {why}, {bound}, and not to the "
            f"return behind it, which stands earlier by an unknown interval (T-0425). "
            f"{tail}")


def record(cand: dict, gaz: dict, docs: dict, taken_ids: set[str]) -> dict:
    name = display(cand["name"])
    fam = surname(cand["name"]).title()
    sources = paper_for(gaz["mentions"])
    where = cited(gaz["mentions"])
    printed = sorted({v["as_printed"] for v in gaz.get("variants") or []})
    groups = returns_of(gaz["mentions"])
    dates = return_dates(gaz["mentions"])
    returns_said = "; ".join(issue_of(g[0]) for g in groups)
    titles = titles_in(cand["name"])

    legacy_id = PREFIX + slug(cand["name"])
    hid = household_id(cand["name"], PREFIX, "letter_list", docs, taken_ids)
    pid = (PERSON_PREFIX + slug(cand["name"])) if hid == legacy_id else hid.removeprefix("hh_")
    span = (f"{cand['first_seen']} to {cand['last_seen']}"
            if cand["first_seen"] != cand["last_seen"] else cand["first_seen"])

    person = {
        "id": pid,
        "name": name,
        "relationship": "head",
        "grade": "attested",
    }
    if titles & FEMALE_TITLES:
        person["sex"] = "female"
    elif titles & MALE_TITLES:
        person["sex"] = "male"
    person["letter_list_only"] = True
    # The dates of the returns behind this person, machine-readable, because
    # T-0379's ruling made three quarters of the town letter-list-only and a
    # reader has to be able to tell a name printed on the scene date from one
    # printed eighteen months earlier without reading a paragraph. `--gate`
    # requires this list on every one of them.
    person["letter_list_returns"] = dates
    person["occupation"] = {
        "value": "none_recorded",
        "confidence": "reconstructed",
        "note": ("No source records an occupation for this person. A list of uncalled-for "
                 "letters prints a name and no trade, and this pass will not read one "
                 "in."),
    }
    person["sources"] = list(sources)
    if len(groups) > 1:
        held = (f"KNOWN ONLY FROM THE POST OFFICE, AND HELD THERE MORE THAN ONCE. The "
                f"papers print " + " and ".join(f"'{p}'" for p in printed)
                + f" in {len(groups)} separate returns of letters uncalled-for at the "
                f"Chicago post office — {returns_said} — across {span}. A name in a LATER "
                f"return is somebody still being written to, months on, which is the "
                f"strongest thing a letter list can say about residence and is why this "
                f"person outranks a single-return name of the same surname. ")
    else:
        held = (f"KNOWN ONLY FROM THE POST OFFICE, IN ONE RETURN. The papers print "
                + " and ".join(f"'{p}'" for p in printed)
                + f" in a single return of letters uncalled-for at the Chicago post "
                f"office — {returns_said}"
                + (f", reprinted over {len(groups[0])} consecutive issues"
                   if len(groups[0]) > 1 else "")
                + f" — dated {span}. ")
    unread = (
        f"AN INITIAL THIS PROJECT CANNOT READ, MARKED AS ONE. The card shows "
        f"'{name}': the scan sets a DIGIT where the middle initial goes, and a digit "
        f"is never part of a name, so the character is carried as {UNREAD} — the "
        f"marker the Chicago list of 1 January 1834 already uses for an initial the "
        f"printing did not deliver. NO LETTER IS SUPPLIED. The deposit holds two "
        f"transcriptions of this issue and no page image, and the alternate carries "
        f"no letter list at all, so there is no cleaner impression here to settle it "
        f"against and the project declines to guess (T-0721; the suspicion is "
        f"registered, ungraded, at data/research/residents/"
        f"letter_list_reading_suspicions.json). The verbatim setting is untouched "
        f"and quoted above; what has stopped is the card asserting that setting is a "
        f"name. A pass that reaches the page images settles it and this marker goes. "
    ) if UNREAD in name else ""
    person["note"] = (
        held
        + unread
        + f"Nothing else in the corpus names this person: no trade, no street, no "
        f"household, no arrival, so every other claim here is written unattested in its own "
        f"block. WHAT THAT IS WORTH: a correspondent believed a person of this name "
        f"reachable at Chicago on that date, and nothing further — not that they lived "
        f"here, kept a trade here, or were here on 1 July 1835. It is the weakest evidence "
        f"this project accepts for a resident, and a source placing them elsewhere retires "
        f"the record. THE ARGUMENT EVERY RECORD OF THIS KIND SHARES is written once instead "
        f"of once per file: the ruling of 2026-08-30 and what it cost the town "
        f"(docs/LIBERTIES.md L214), the refusals and the transcription standard behind the "
        f"reading (tools/mint_letter_list_residents.py). No figure is drawn (L1)."
    )

    present = "present" if cand["last_seen"] >= SCENE_DATE else "uncertain"
    doc = {
        "id": hid,
        "name": f"The {fam} household — a name from the post office's letter lists",
        "division": DIVISION,
        "head": pid,
    }
    if hid != legacy_id:
        # A genuinely new mint (T-0599): see mint_documented_residents.record()'s
        # matching comment — a household reusing its legacy id is unchanged.
        doc["source_pass"] = "letter_list"
    bound, entry = bound_for(dates[0])
    doc.update({
        "arrival": {
            "value": bound,
            "confidence": "inferred",
            "sources": list(sources),
            "note": arrival_note(bound, dates[0], entry),
            "precision": "not_later_than",
        },
        "party_size_on_arrival": {
            "value": None, "confidence": "reconstructed", "note": "Not attested.",
        },
        "origin": {
            "value": None, "confidence": "reconstructed", "note": "Not attested.",
        },
        "reason_for_coming": {
            "value": None, "confidence": "reconstructed", "note": "Not attested.",
        },
        "lives_at": {
            "value": None, "confidence": "reconstructed",
            "note": "Not attested: a letter list gives a name and no address.",
        },
        "works_at": {
            "value": None, "confidence": "reconstructed",
            "note": "Not attested. No trade is recorded, so there is no premises to seek.",
        },
        "present_on_scene_date": {
            "value": present,
            "confidence": "inferred",
            "sources": list(sources),
            "note": ((f"A letter was still waiting for this name at "
                      f"{issue_of(groups[-1][0])}, on or after the scene date, so the "
                      f"corpus puts somebody expecting them at Chicago at "
                      f"{cand['last_seen']}.")
                     if present == "present" else
                     (f"THE CORPUS STOPS BEFORE THE SCENE DATE. Nothing after "
                      f"{cand['last_seen']} follows this person to 1 July 1835 or says "
                      f"they left. `uncertain` rather than dropped — the distinction "
                      f"index.json draws for Jeremiah Porter, and a finding, not a "
                      f"gap.")),
        },
        "persons": [person],
        "touches_removal": False,
        "review_required": False,
        "research_note": (
            f"MINTED FROM THE LETTER LISTS (T-0378, T-0379). THE HOUSEHOLD IS A CONTAINER, "
            f"NOT AN ARGUMENT: every other record here argues for a household, and this "
            f"one argues for a PERSON. `data/residents/` cannot carry a person outside a "
            f"household, so one was written around them and told to claim nothing — one "
            f"member, no dwelling, no division, no trade, no family, no arrival beyond the "
            f"paper's bound. tools/mint_letter_list_residents.py derives the set and prints "
            f"every refusal, `--gate` proves no record here gained a roof, a trade or a "
            f"second member, and docs/LIBERTIES.md L214 carries the change of scale."
        ),
    })
    return doc


def carry_over(doc: dict, existing: dict) -> dict:
    """Keep later passes' findings when this letter-list mint rebuilds its card."""
    # A printed title is this pass's evidence for ``sex``; its absence after a new
    # reading is owned by this mint and must not be resurrected from the old card.
    return carry_resident_mint(doc, existing, owned_person_keys=("sex",))


def build(preload: dict | None = None):
    docs = ({p: json.loads(t) for p, t in preload.items() if p != INDEX}
            if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    index = (json.loads(preload[INDEX]) if preload is not None and INDEX in preload
             else load(INDEX))

    mine_paths = {p for p, doc in docs.items() if minted_by(p, doc, "letter_list", PREFIX)}
    accepted, refusals = mint(docs, index)

    files = {}
    seen: set[str] = set()
    for cand, gaz in accepted:
        doc = record(cand, gaz, docs, seen)
        existing = docs.get(HOUSEHOLDS / f"{doc['id']}.json") or {}
        carry_over(doc, existing)
        if doc["id"] in seen:
            raise SystemExit(f"two candidates mint the same household id {doc['id']}")
        seen.add(doc["id"])
        files[HOUSEHOLDS / f"{doc['id']}.json"] = dumps(doc, 1)

    # ONE OWNER FOR THE MANIFEST (T-0715). This pass used to mint its own rows and
    # keep every other row verbatim, so a household no pass owned could be regraded
    # elsewhere and go on carrying a stale row for ever. `final` is the whole layer
    # as this pass leaves it, and the derivation reads all of it.
    final = {path: doc for path, doc in docs.items() if path not in mine_paths}
    final.update({path: json.loads(text) for path, text in files.items()
                  if path != INDEX})
    rebuild(index, final)
    files[INDEX] = dumps(index, 1)
    return files, accepted, refusals, mine_paths


def report(accepted, refusals, docs: dict) -> None:
    print(f"MINTED — {len(accepted)} letter-list resident(s)")
    shown: set[str] = set()
    for cand, gaz in accepted:
        hid = household_id(cand["name"], PREFIX, "letter_list", docs, shown)
        shown.add(hid)
        groups = returns_of(gaz["mentions"])
        print(f"  {hid:30s} {display(cand['name'])[:26]:28s} "
              f"({len(groups)} return(s), {len(gaz['mentions'])} printing(s), "
              f"{cand['first_seen']}..{cand['last_seen']})")
    print(f"\nREFUSED — {len(refusals)} candidate(s) out of the same pool, with the reason")
    tally: dict[str, int] = {}
    for _cid, _name, _n, reason in refusals:
        tally[reason_key(reason)] = tally.get(reason_key(reason), 0) + 1
    for reason, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {reason}")
    print()
    for cid, name, n, reason in refusals:
        print(f"  {name[:30]:32s} {n} return(s)  {reason}")


def reason_key(reason: str) -> str:
    """A refusal reason without the particulars it names, for tallying."""
    key = reason.split(" (")[0]
    return ("the town already names that family"
            if key.startswith("the town already names") else key)


# ---------------------------------------------------------------------------
# the scale the owner's ruling set (T-0379), counted on the tree it is run on
# ---------------------------------------------------------------------------

def scale_report() -> None:
    """What this pass does to the town, re-derived rather than remembered.

    T-0379 asked the owner how many of the letter-list names the town should hold,
    and the answer on 2026-08-30 was ALL of the ones the refusals admit. That is the
    largest single change to the town's population this corpus can make, and the
    number it lands on moves every time a transcription lands, so it is measured here
    and written down nowhere else in this file. `docs/LIBERTIES.md` L182 carries a
    dated statement of it, and its Scope count is gated against this same data.
    """
    files, accepted, refusals, _mine_paths = build()
    index = json.loads(files[INDEX])
    gazetteer = {p["id"]: p for p in load(GAZETTEER)["persons"]}
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    own_pass = frozenset(doc["head"] for doc in docs.values()
                         if doc.get("source_pass") == "letter_list")
    pool = letter_list_pool(load(REGISTER), own_pass)
    multi = [p for p in pool
             if len(returns_of(gazetteer[p["id"]]["mentions"])) >= RANKED_FIRST_RETURNS]

    persons = index["counts"]["persons"]
    households = index["counts"]["households"]
    ll = index["counts"]["letter_list_only"]

    print("T-0379 — THE SCALE THE RULING SET, on this tree")
    print(f"\nTHE POOL — letter-list-only names the town did not already hold: {len(pool)}")
    print(f"  {len(multi):5d} printed in more than one return")
    print(f"  {len(pool) - len(multi):5d} printed in exactly ONE return")

    print(f"\nTHE REFUSALS over all {len(pool)}, in the order they are applied")
    tally: dict[str, int] = {}
    for _cid, _name, _n, reason in refusals:
        tally[reason_key(reason)] = tally.get(reason_key(reason), 0) + 1
    for reason, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {reason}")
    print(f"  {'-' * 5}")
    print(f"  {len(refusals):5d}  refused, and {len(accepted)} minted")

    print(f"\nTHE TOWN THIS PRODUCES")
    print(f"  households  {households - len(accepted):5d} -> {households}")
    print(f"  persons     {persons - len(accepted):5d} -> {persons}")
    print(f"  of the people a visitor can open, {ll / persons * 100:.1f}% are a name on a "
          f"post-office list and nothing else")

    print(f"\nBY THE RETURN THAT PRINTED THEM, newest first — the ladder the owner was")
    print(f"  shown before he ruled, now the shape of what stands.")
    by_return: dict = {}
    for cand, gaz in accepted:
        by_return.setdefault(return_dates(gaz["mentions"])[0], []).append(cand)
    for when in sorted(by_return, reverse=True):
        print(f"  {when}  {len(by_return[when]):5d}")


# ---------------------------------------------------------------------------
# the gate — what the ruling of 2026-08-30 owes, proved rather than asserted
# ---------------------------------------------------------------------------
#
# T-0379's acceptance in three clauses, and this is where each becomes checkable:
#
#   * every minted person carries `letter_list_only: true` AND the date of the
#     return that printed them — the ruling's own condition, because three quarters
#     of the town is now this cohort and a reader has to be able to date any one of
#     them;
#   * none of them gains a roof, a household or a trade from this pass alone. The
#     failure mode is silent and it is the one that would matter: a later generator
#     that deals roofs by household, or an occupancy pass that reads `persons`,
#     could put 700 invented dwellings in the town off the back of a post-office
#     list, and nothing about the records would look wrong;
#   * the manifest says which rows they are, because the Evidence panel splits on
#     that flag rather than on a mint tool's id prefix.
#
# `--check` already proves the records are what this pass derives. This proves the
# derivation is what the ruling permitted, which is a different question: `--check`
# would stay green if the pass itself started writing a trade onto every one.

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def press_contradicting(person: dict) -> list[dict]:
    """The rows of this person's `press_evidence[]` that are NOT letter lists.

    T-1005. `letter_list_only` is not decoration: `renderers/web/js/residents.js`
    prints a whole paragraph off it — "Only from the post office's lists of
    uncalled-for letters … it is the weakest evidence this project accepts for a
    resident" — and the land-sale ruling rule reads the flag as the written form
    of its own refusal test. The flag is written at MINT time, when a letter list
    is all there is; the consolidation passes add `press_evidence` to a card
    afterwards and never looked at it again. So seven cards reached dev asserting
    "known only from the post office" while carrying, on the same record, an
    ordinary reading of the papers — the exact confusion the flag exists to
    prevent, stated backwards.

    The test is one line, and it is one-directional on purpose. A person whose
    press block holds no letter list at all is not this pass's business, and 678
    of the cohort carry the reading in `letter_list_returns` and the note with no
    press block at all — so this may never SET the flag, only refuse it where the
    record itself contradicts it.
    """
    return [row for row in (person.get("press_evidence") or [])
            if row.get("list") != LETTER_LIST_CLASS]

# The two rules T-0425 allows an arrival note to open on, in the order
# `bound_for()` chooses between them: the return where the return is dated,
# the printing where it is not.
BOUND_MARKERS = ("A BOUND FROM THE RETURN", "A BOUND FROM THE PAPER")


def id_family_name(pid: str, name: str) -> bool:
    """Was this id minted off the family name this name gives? (T-1218)

    `plain_fragment()` builds a person id as the family name followed by whatever
    else the printing set, so the question is answerable without taking the id
    apart: the id either IS the slugged family name or begins with it and a stop.
    Deliberately the family name alone and not the whole fragment — fifteen cards
    differ from a re-minted fragment over an unread initial (`[?] G. Abbot`), a
    suffix (`Benjamin Jr. Swena`) or a printing whose order is its own ticket
    (jones_es_high, T-1217), and none of those is a disagreement about WHICH LETTERS
    THE SURNAME HAS, which is all this asks.
    """
    fam = slug(surname(name or ""))
    return bool(fam) and (pid == fam or str(pid or "").startswith(fam + "_"))


def ruled_renamings() -> dict[str, dict]:
    """person_id -> the adjudication that moved its displayed name off its id.

    T-1139 read nineteen lines of the return of 1 January 1834 where the page image
    and the transcription disagree, and three of them are rows where the card's
    letters moved and the id did not (its rule N5: an id is a handle, not a claim).
    Those three are the only licensed divergences in the cohort, and they are read
    from the RULING FILE rather than from the cards, so a card cannot license its
    own divergence by writing a `name_ruling` block onto itself.
    """
    if not NAME_RULINGS.exists():
        return {}
    out: dict[str, dict] = {}
    for row in load(NAME_RULINGS).get("rulings") or []:
        card = row.get("card") or {}
        pid, was, now = (card.get("person"), card.get("displayed_name_was"),
                         card.get("displayed_name_is"))
        if pid and was and now and was != now:
            out[pid] = dict(row)
    return out


def gate_problems(docs: dict, index: dict, structure_text: dict) -> list[str]:
    """Every way the minted cohort could stop being what the owner ruled for.

    Takes the tree as data so `--self-test` can break one invariant at a time and
    require this to name it. A gate that has never been seen to fail is an
    assertion about the code that wrote it.
    """
    problems: list[str] = []
    mine_paths = {path for path, doc in docs.items()
                 if minted_by(path, doc, "letter_list", PREFIX)}
    minted = {path: docs[path] for path in mine_paths}
    if not minted:
        return ["no letter-list household records at all — this pass mints the "
                "largest cohort in the town and an empty one is a failure, not a "
                "clean tree"]

    rows = {r["id"]: r for r in index.get("households") or []}
    flagged_persons = 0
    renamings = ruled_renamings()
    for path, doc in sorted(minted.items()):
        hid = doc.get("id")
        persons = doc.get("persons") or []
        if len(persons) != 1:
            problems.append(f"{hid}: {len(persons)} persons — a letter list names one "
                            f"person and this pass may not invent a household around them")
        for person in persons:
            pid = person.get("id")
            # T-1005. The flag's own justification is the test: it is what keeps a
            # letter list and a shopkeeper's advertisement from reading as the same
            # claim, so a person carrying BOTH may not carry the flag. This pass
            # mints the flag and this gate keeps it honest in both directions.
            contradicting = press_contradicting(person)
            if contradicting:
                if person.get("letter_list_only"):
                    where = ", ".join(sorted({str(r.get("locator")) for r in contradicting}))
                    problems.append(f"{hid}/{pid}: letter_list_only is true and "
                                    f"{len(contradicting)} press reading(s) on this same "
                                    f"record are not letter lists — {where}. The flag says "
                                    f"'known only from the post office' and the evidence "
                                    f"beside it says otherwise; one of the two is wrong")
            elif person.get("letter_list_only") is not True:
                problems.append(f"{hid}/{pid}: letter_list_only is "
                                f"{person.get('letter_list_only')!r} and must be true — it "
                                f"is what keeps this evidence and a shopkeeper's "
                                f"advertisement from reading as the same claim")
            if person.get("letter_list_only"):
                flagged_persons += 1
            # T-1121. A COMMA IN A CARD'S NAME MAY NOT CHANGE THE FAMILY NAME
            # IT GIVES. `display()` makes one order out of the two the papers
            # print, and a comma left standing in what it made is read straight
            # back as a surname-first printing: hugunin_leonard_c carried
            # `Leonard, C. Hugunin`, off the printed `Hugunin, Leonard, C.`, and
            # every reader of that card — `surname()` here, `surname_of()` in
            # compile_scene.py, the inverting rule in the 1840 crosswalk — took
            # `leonard` as the family name while the record id and the
            # gazetteer's other printing of the same man both said Hugunin.
            #
            # Stated as what it is and not one inch wider: the card is not where
            # a printing is kept verbatim (the extracted column and the
            # gazetteer's `as_printed` are, and neither is touched by this), so a
            # comma a card carries earns nothing — but it is only a DEFECT where
            # it moves the answer. jones_es_high carries one that does not, off a
            # line whose family name the type set in the middle, and it has its
            # own ticket rather than a migration smuggled into this one.
            shown = person.get("name") or ""
            # T-1217. A CARD ENDS ON ITS FAMILY NAME. Given-first is the one
            # order a card is in, and the town directory depends on that
            # literally: compile_scene.py's `surname_of()` files a person under
            # the LAST word of the name, so a card that leads with its family
            # name is filed under whatever trails it. jones_es_high read `Jones,
            # High Es` off a printing that sets the family name in the middle,
            # and only its comma — right by accident — kept it out of the
            # directory under `es`.
            #
            # Bracketed readings stand outside this assertion, not because they
            # are exempt but because `words()` strips a square-bracket supply
            # before `surname()` can see it, so the family name it returns for
            # `Lo[vering], Richard` is `richard`: T-1155's defect, and a gate may
            # not fire on a reading it cannot take. All 736 letter-list cards on
            # disk pass this.
            tokens = words(shown)
            if ("[" not in shown and tokens and surname(shown)
                    and tokens[-1].lower().strip("'").replace("'", "")
                    != surname(shown)):
                problems.append(f"{hid}/{pid}: display name {shown!r} does not end "
                                f"on its family name {surname(shown)!r} — a card is "
                                f"given-first and the town directory files it under "
                                f"its last word (T-1217)")
            if "," in shown and surname(shown) != surname(shown.replace(",", " ")):
                problems.append(f"{hid}/{pid}: display name {shown!r} reads the family "
                                f"name {surname(shown)!r} with its comma and "
                                f"{surname(shown.replace(',', ' '))!r} without it — an "
                                f"ordered name says its order by its order, and a comma "
                                f"left in one is read back as a surname-first printing "
                                f"(T-1121)")

            # T-1218. A CARD'S NAME GIVES THE FAMILY NAME ITS ID WAS MINTED OFF —
            # the assertion T-1121 reached for and could not make, because three
            # cards stood in its way: fraser_wm_h read `Wm. H. Frazer`,
            # provis_joshua read `Joshua Pruvis`, vandino_john read `John Vandine`.
            # Those three are not the comma fault. Neither reading is misordered
            # and no punctuation is involved; the card and the id disagree about
            # WHICH LETTERS the surname has, because one reading of a printed line
            # was minted into the id and a different reading of the same line was
            # later written onto the card.
            #
            # T-1139 ruled all three — the scan-verified reading of the ninth
            # impression overturns the transcription-mediated one, and under its
            # rule N5 the displayed name moves while the id, a handle cited by
            # every crosswalk, does not. So the assertion is made here WITH that
            # licence and with nothing else: the family name read off a card is the
            # one its id was minted off, unless the ruling file adjudicates that
            # exact card, in which case the id must be the handle of the reading
            # the ruling OVERTURNED and the card must wear the one it AWARDED.
            # Both halves matter. Without the first, an id could drift anywhere and
            # point at a ruling for cover; without the second, a card could be
            # respelled a third way over a ruling that never said so.
            shown_row = renamings.get(pid)
            if shown_row is None:
                if not id_family_name(pid, shown):
                    problems.append(f"{hid}/{pid}: the card reads {shown!r}, whose "
                                    f"family name is {slug(surname(shown))!r}, and the "
                                    f"id was minted off a different one — one reading "
                                    f"of the printed line is in the id and another is "
                                    f"on the card, and no ruling in "
                                    f"{NAME_RULINGS.relative_to(ROOT)} adjudicates it "
                                    f"(T-1218)")
            else:
                card_row = shown_row.get("card") or {}
                was, awarded = (card_row.get("displayed_name_was"),
                                card_row.get("displayed_name_is"))
                if not id_family_name(pid, was):
                    problems.append(f"{hid}/{pid}: the ruling on printed line "
                                    f"{shown_row.get('n')!r} says this card read "
                                    f"{was!r} before it moved, and the id was not "
                                    f"minted off that family name either — the id is "
                                    f"the overturned reading's handle or the licence "
                                    f"is not for this card (T-1218)")
                if shown != awarded:
                    problems.append(f"{hid}/{pid}: the card reads {shown!r} and its "
                                    f"ruling on printed line {shown_row.get('n')!r} "
                                    f"awards {awarded!r} — a card wears the reading it "
                                    f"was ruled onto, not a third one (T-1218)")
                block = person.get("name_ruling") or {}
                if block.get("displayed_name_was") != was:
                    problems.append(f"{hid}/{pid}: the card's own name_ruling says it "
                                    f"read {block.get('displayed_name_was')!r} before "
                                    f"it moved and {NAME_RULINGS.relative_to(ROOT)} "
                                    f"says {was!r} — the card must carry the "
                                    f"adjudication it stands on (T-1218)")
            dates = person.get("letter_list_returns")
            if not isinstance(dates, list) or not dates:
                problems.append(f"{hid}/{pid}: letter_list_returns is "
                                f"{dates!r} — every minted person owes the date of the "
                                f"return that printed them (T-0379's ruling)")
            else:
                for d in dates:
                    if not (isinstance(d, str) and ISO.match(d)):
                        problems.append(f"{hid}/{pid}: letter_list_returns carries "
                                        f"{d!r}, which is not an ISO date")
                if sorted(set(dates)) != list(dates):
                    problems.append(f"{hid}/{pid}: letter_list_returns {dates!r} is not "
                                    f"unique and ascending, so 'the newest return' cannot "
                                    f"be read off it")
            occ = person.get("occupation") or {}
            rr = person.get("resident_research") or {}
            independently_corroborated = bool(rr.get("asserted_identity") and rr.get("source_ids"))
            if occ.get("value") != "none_recorded" and not independently_corroborated:
                problems.append(f"{hid}/{pid}: occupation is {occ.get('value')!r} — a "
                                f"letter list gives no trade and this pass may not read "
                                f"one in without independently corroborated resident research")
        # T-0425. The bound belongs to the RETURN, not to the impression an
        # extraction pass happened to reach. It is gated rather than merely derived
        # because the failure is invisible on the card — `1834-03-04` looks like a
        # date somebody read, and it is nine weeks of a name's residence given away
        # to whichever printing a crop happened to catch. Only records whose arrival
        # is still this pass's own are held to it: a later pass that dates somebody
        # from a source of its own (T-0482 on `hh_orsemus_morrison`, `1833`) writes
        # its own reasoning into the note and is out of scope by construction.
        arrival = doc.get("arrival") or {}
        note = arrival.get("note") or ""
        returns = sorted({d for person in persons
                          for d in (person.get("letter_list_returns") or [])})
        if note.startswith(BOUND_MARKERS) and returns:
            want, entry = bound_for(returns[0])
            if arrival.get("value") != want:
                problems.append(
                    f"{hid}: arrival is {arrival.get('value')!r} and the earliest return "
                    f"printing behind this name is {returns[0]} — the bound owed is "
                    f"{want!r}, from {(entry or {}).get('said', 'the printing itself')} "
                    f"(T-0425)")
            elif not note.startswith(BOUND_MARKERS[0 if entry and entry["date"] else 1]):
                problems.append(
                    f"{hid}: arrival is {want!r} but its note opens on the wrong rule — "
                    f"a reader may not have to work out whether a bound came from the "
                    f"return or from the printing (T-0425)")
            if arrival.get("precision") != "not_later_than":
                problems.append(
                    f"{hid}: arrival precision is {arrival.get('precision')!r} — a "
                    f"letter-list bound is never anything but not_later_than")
        for key in ("lives_at", "works_at"):
            value = (doc.get(key) or {}).get("value")
            if value is not None:
                problems.append(f"{hid}: {key} is {value!r} — no roof, no premises. A "
                                f"letter-list name is a name the town knows, not a man "
                                f"with an address")
        if doc.get("division") != DIVISION:
            problems.append(f"{hid}: division is {doc.get('division')!r} and must be "
                            f"'{DIVISION}' — nothing places these people in the town")
        row = rows.get(hid)
        if row is None:
            problems.append(f"{hid}: no manifest row")
        elif bool(row.get("letter_list_only")) != any(p.get("letter_list_only")
                                                      for p in persons):
            # The row must say what the card says — T-1005 cleared the flag on seven
            # cards and the row has to follow, or the Evidence panel holds a household
            # apart from the town's evidenced ones on a flag its own record dropped.
            problems.append(f"{hid}: the manifest row says letter_list_only="
                            f"{bool(row.get('letter_list_only'))!r} and the card says "
                            f"{any(p.get('letter_list_only') for p in persons)!r} — the "
                            f"Evidence panel reads the row and the card is the master")

    mine_ids = {p.stem for p in mine_paths}
    for hid, row in rows.items():
        if row.get("letter_list_only") and hid not in mine_ids:
            problems.append(f"{hid}: a manifest row outside this pass claims "
                            f"letter_list_only")

    counted = index.get("counts", {}).get("letter_list_only")
    if counted != flagged_persons:
        problems.append(f"counts.letter_list_only is {counted!r} and {flagged_persons} "
                        f"persons carry the flag — the panel's own count sentence reads "
                        f"this number")

    # T-0599: a letter-list person's id is no longer always `ll_...` or found
    # under an `hh_ll_...` household — it is found by the FLAG, wherever it is
    # minted, so the structure check is built from that rather than a static
    # prefix pattern that a plain id would slip past.
    ll_person_ids = {p.get("id") for doc in docs.values()
                     for p in doc.get("persons") or []
                     if p.get("letter_list_only") and p.get("id")}
    if ll_person_ids:
        structure_ref = re.compile(
            r'"(?:' + "|".join(re.escape(pid) for pid in sorted(ll_person_ids)) + r')"')
        for name, text in sorted(structure_text.items()):
            hit = structure_ref.search(text)
            if hit:
                problems.append(f"data/structures/{name}: names {hit.group(0)} — a "
                                f"letter-list person has been given a building, which is "
                                f"exactly what the ruling of 2026-08-30 forbids this cohort")
    return problems


def read_tree():
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    index = load(INDEX)
    structures = {p.name: p.read_text(encoding="utf-8")
                  for p in sorted((DATA / "structures").glob("*.json"))}
    return docs, index, structures


def gate() -> int:
    docs, index, structures = read_tree()
    problems = gate_problems(docs, index, structures)
    for problem in problems:
        print(f"   {problem}")
    if problems:
        print(f"   {len(problems)} problem(s): the minted letter-list cohort is not what "
              f"the owner's ruling of 2026-08-30 permits")
        return 1
    minted = sum(1 for p, doc in docs.items() if minted_by(p, doc, "letter_list", PREFIX))
    print(f"   OK: {minted} letter-list household(s), every one carrying its returns' "
          f"dates, none with a roof, a trade or a second member")
    return 0


NAME_READING_CASES = (
    # printed as the post office set it,   surname,     the card's display name
    # --- surname printed FIRST, no comma to say so (T-0638, fault A) -----------
    ("Perry A. 8.", "perry", "A. [?] Perry"),
    ("Mason Sabrina A.", "mason", "Sabrina A. Mason"),
    ("merrich J. B.", "merrich", "J. B. merrich"),
    ("Mills Joel C.", "mills", "Joel C. Mills"),
    ("Hhelps Theodore E.", "hhelps", "Theodore E. Hhelps"),
    ("Mabbet Benjamin F.", "mabbet", "Benjamin F. Mabbet"),
    ("Norton Wm. H.", "norton", "Wm. H. Norton"),
    ("Preston Stephen II.", "preston", "Stephen II. Preston"),
    ("Bobinson George IS.", "bobinson", "George IS. Bobinson"),
    ("Pugsley John K.", "pugsley", "John K. Pugsley"),
    ("Pixley John L.", "pixley", "John L. Pixley"),
    ("Clapp. A. P.", "clapp", "A. P. Clapp"),
    ("Norton N. R.", "norton", "N. R. Norton"),
    ("Page Elisha S.", "page", "Elisha S. Page"),
    ("Orinsbey martin T.", "orinsbey", "martin T. Orinsbey"),
    ("Regera John V.", "regera", "John V. Regera"),
    ("Oakley Benjamin W.", "oakley", "Benjamin W. Oakley"),
    ("Nelts Wm.", "nelts", "Wm. Nelts"),
    # --- an initial the scan did not deliver (T-0721) --------------------------
    # The surname survives, the initial does not, and no letter is supplied for it.
    ("Abbot, 8. G.", "abbot", "[?] G. Abbot"),
    ("Gabbs, James I1.", "gabbs", "James [?] Gabbs"),
    # …and the clusters that are ugly but are still LETTERS stay exactly as printed,
    # because this pass marks what it cannot read and does not tidy what it can.
    ("Conkiin, Robert I.", "conkiin", "Robert I. Conkiin"),
    # …and the three the printing gives no forename at all
    ("McLoud I.", "mcloud", "I. McLoud"),
    ("Willinm G.", "willinm", "G. Willinm"),
    ("Ranwin O.", "ranwin", "O. Ranwin"),
    # --- given-first, which the rule must NOT touch ----------------------------
    ("Joel C. Mills", "mills", "Joel C. Mills"),
    ("B. S. Morris", "morris", "B. S. Morris"),
    ("A[n]drew W. Borland", "borland", "A[n]drew W. Borland"),
    ("John Bates Jr.", "bates", "John Bates Jr."),
    ("Joshua Hathaway jr.", "hathaway", "Joshua Hathaway jr."),
    # a mangled INITIAL beside a sound surname is fault C, not fault A: the id is
    # already right and T-0638's reordering rule must leave both of them alone.
    # T-0721 marks the initial as unread — from EITHER printed order, and the marked
    # form is then a fixed point, which is what lets a card carry it (three rows).
    ("8. G. Abbot", "abbot", "[?] G. Abbot"),
    ("James I1. Gabbs", "gabbs", "James [?] Gabbs"),
    ("[?] G. Abbot", "abbot", "[?] G. Abbot"),
    ("A. [?] Perry", "perry", "A. [?] Perry"),
    ("James [?] Gabbs", "gabbs", "James [?] Gabbs"),
    # --- the comma the papers do sometimes print -------------------------------
    ("Hail, Aifred", "hail", "Aifred Hail"),
    ("Foot, S.", "foot", "S. Foot"),
    # …and the SECOND comma, inside the forename side, which the reordering must
    # not carry into the card (T-1121). `Hugunin, Leonard, C.` is a printing this
    # corpus holds, and it minted hugunin_leonard_c, whose card read `Leonard, C.
    # Hugunin` and gave the family name `leonard` to every reader of it. The row
    # under it is the assertion that matters: the ordered name is a FIXED POINT
    # and gives the family name the printing gave, so no reader of the card can
    # answer differently from a reader of the line.
    ("Hugunin, Leonard, C.", "hugunin", "Leonard C. Hugunin"),
    ("Leonard C. Hugunin", "hugunin", "Leonard C. Hugunin"),
    # `Es,Jones, High` is the other printing this corpus holds with two commas,
    # and T-1217 is what its first comma turned out to be: not a divider. The
    # family name is set in the MIDDLE, so reordering around that comma led the
    # card with it (`Jones, High Es`). The divider is the SECOND comma, so the
    # forename `High` leads, the run-on remnant `Es` follows it unpromoted, and the
    # family name ends the card. The trap it avoids is the comma-only fix: dropping
    # the punctuation alone gives `Jones High Es`, whose last word is `Es`, and
    # compile_scene.py's `surname_of()` files a card under its last word — so that
    # card would have sorted in the town directory under `es`, away from the other
    # Joneses. (`surname()` here would still answer `jones`, by T-0638's first-token
    # rule; two readers of one card disagreeing is the defect, not a safety net.)
    ("Es,Jones, High", "jones", "High Es Jones"),
    # --- a genuine two-part surname, which must survive all of it --------------
    ("Rev. John Mary Irenaeus St Cyr", "cyr", "Rev. John Mary Irenaeus St Cyr"),
)

SLUG_CASES = (
    # the period's Scots and Irish prefix is ONE word, not a letter and a word
    ("Thomas M'Clintock", "thomas_mclintock", "mclintock_thomas"),
    ("Angus M'Vaughton", "angus_mvaughton", "mvaughton_angus"),
    ("Wm. B. M'Ewen", "wm_b_mewen", "mewen_wm_b"),
    ("John O. P'aylor", "john_o_paylor", "paylor_john_o"),
    # …and so is a contracted forename
    ("Tho's Allison", "thos_allison", "allison_thos"),
    ("Fred'k. Curtenius", "fredk_curtenius", "curtenius_fredk"),
    ("Sam'l. L. Selden", "saml_l_selden", "selden_saml_l"),
    ("Rob't. Starkweather", "robt_starkweather", "starkweather_robt"),
    # a space is not an apostrophe: St Cyr slugs exactly as it always has
    ("Rev. John Mary Irenaeus St Cyr", "john_mary_irenaeus_st_cyr",
     "cyr_john_mary_irenaeus_st"),
    # T-0721: the marker changes the DISPLAY name and nothing the id is built from,
    # which is the whole reason it may be applied to a committed record at all.
    ("Abbot, 8. G.", "abbot_8_g", "abbot_8_g"),
    ("Perry A. 8.", "perry_a_8", "perry_a_8"),
    ("Gabbs, James I1.", "gabbs_james_i1", "gabbs_james_i1"),
)


def name_reading_self_test() -> int:
    """T-0638. Every row of the ticket's own table, plus the forms the fix must not
    break, proved against `surname()`, `display()` and `slug()` directly.

    These are the three functions the household id, the household name and the
    person's display name are all derived from, so a regression here silently
    renames people. Fixtures, never the tree: the tree's own answer is gated
    separately by `--gate` and `--check`."""
    failed = 0
    for printed, want_surname, want_display in NAME_READING_CASES:
        got_s, got_d = surname(printed), display(printed)
        if got_s != want_surname:
            failed += 1
            print(f"   FAIL surname({printed!r}) -> {got_s!r}, expected {want_surname!r}")
        if got_d != want_display:
            failed += 1
            print(f"   FAIL display({printed!r}) -> {got_d!r}, expected {want_display!r}")
    # T-1121. The property the rows above only sample: whatever `display()` makes
    # of a printing, a reader of the CARD must land on the family name a reader of
    # the LINE does. This is the assertion that failed on `Hugunin, Leonard, C.`
    # — `surname()` said hugunin of the printing and leonard of the card it made.
    for printed, _want_surname, _want_display in NAME_READING_CASES:
        of_line, of_card = surname(printed), surname(display(printed))
        if of_line != of_card:
            failed += 1
            print(f"   FAIL surname({printed!r}) is {of_line!r} but the card it makes, "
                  f"{display(printed)!r}, reads {of_card!r}")
    for printed, want_slug, want_fragment in SLUG_CASES:
        got_slug, got_fragment = slug(printed), plain_fragment(printed)
        if got_slug != want_slug:
            failed += 1
            print(f"   FAIL slug({printed!r}) -> {got_slug!r}, expected {want_slug!r}")
        if got_fragment != want_fragment:
            failed += 1
            print(f"   FAIL plain_fragment({printed!r}) -> {got_fragment!r}, "
                  f"expected {want_fragment!r}")
    if failed:
        print(f"   {failed} name-reading assertion(s) failed")
        return 1
    print(f"   OK: all {len(NAME_READING_CASES)} name readings and "
          f"{len(SLUG_CASES)} slugs are what the papers print, and every card each "
          f"one makes reads back to the family name of its own line")
    return 0


def return_bound_self_test() -> int:
    """T-0425's own assertion: two printings of ONE return give ONE bound.

    Fixtures over the RETURNS table, not over the tree — the tree's answer is gated
    separately by `--gate`. What is proved here is the rule rather than a row: that
    every printing of a return agrees, that a bound is never later than the issue
    that carried it, and that a return this project cannot date falls back to the
    printing instead of inventing one.
    """
    failed = 0
    for entry in RETURNS:
        bounds = {bound_for(issue)[0] for issue in entry["printings"]}
        if entry["date"] and len(bounds) != 1:
            failed += 1
            print(f"   FAIL {entry['said']}: its printings give {sorted(bounds)} — one "
                  f"return owes one bound")
        for issue in entry["printings"]:
            got, _ = bound_for(issue)
            if got > issue:
                failed += 1
                print(f"   FAIL {issue}: bound {got} is later than the issue that "
                      f"printed it")
            if not entry["date"] and got != issue:
                failed += 1
                print(f"   FAIL {issue}: an undated return must fall back to the "
                      f"printing, not to {got}")
        if entry["date"] and not entry["date_lines"]:
            failed += 1
            print(f"   FAIL {entry['said']}: a dated return owes the date line it is "
                  f"read off")
    # The worked case the ticket names: the fourth and the ninth printing of the
    # 1 January 1834 return, nine weeks apart, are one piece of evidence.
    for pair in (("1834-01-28", "1834-03-04"), ("1834-07-02", "1834-07-16")):
        a, b = (bound_for(pair[0])[0], bound_for(pair[1])[0])
        if a != b:
            failed += 1
            print(f"   FAIL {pair[0]} and {pair[1]} print one return and give "
                  f"{a} and {b}")
    unknown, entry = bound_for("1899-01-01")
    if unknown != "1899-01-01" or entry is not None:
        failed += 1
        print(f"   FAIL a printing no return row claims must date itself, not "
              f"{unknown}")
    if failed:
        print(f"   {failed} return-bound assertion(s) failed")
        return 1
    print(f"   OK: {len(RETURNS)} return(s) over "
          f"{sum(len(e['printings']) for e in RETURNS)} printing(s), each return one "
          f"bound")
    return 0


def self_test() -> int:
    """Break each invariant on a copy of the tree and require the gate to name it."""
    if name_reading_self_test():
        return 1
    if return_bound_self_test():
        return 1
    docs, index, structures = read_tree()
    if gate_problems(docs, index, structures):
        print("   the committed tree does not pass its own gate; fix that first")
        return 1
    # A victim that still CARRIES the flag: T-1005 cleared it on seven cards, and a
    # mutation that drops a flag off a card which no longer has one asserts nothing.
    victim = next(p for p, doc in sorted(docs.items())
                 if minted_by(p, doc, "letter_list", PREFIX)
                 and (doc.get("persons") or [{}])[0].get("letter_list_only"))

    # The three cards T-1139 moved and T-1218 gates. Read from the ruling file so
    # this harness cannot be satisfied by a card that has quietly stopped being one.
    RULED = set(ruled_renamings())
    RULED_PATH = next((path for path, doc in sorted(docs.items())
                       if any(p.get("id") in RULED for p in doc.get("persons") or [])),
                      None)
    if not RULED or RULED_PATH is None:
        print("   no adjudicated renaming in the tree — T-1218's licence is untested")
        return 1

    def broken(mutate):
        d = json.loads(json.dumps({str(k): v for k, v in docs.items()}))
        d = {pathlib.Path(k): v for k, v in d.items()}
        i = json.loads(json.dumps(index))
        s = dict(structures)
        mutate(d, i, s)
        return gate_problems(d, i, s)

    def drop_flag(d, i, s):
        d[victim]["persons"][0].pop("letter_list_only")
        i["counts"]["letter_list_only"] -= 1

    def drop_dates(d, i, s):
        d[victim]["persons"][0]["letter_list_returns"] = []

    def give_a_roof(d, i, s):
        d[victim]["lives_at"]["value"] = "sauganash_hotel"

    def give_a_trade(d, i, s):
        d[victim]["persons"][0]["occupation"]["value"] = "carpenter"

    def give_a_household(d, i, s):
        d[victim]["persons"].append(dict(d[victim]["persons"][0], id="ll_invented_wife"))

    def unflag_the_row(d, i, s):
        for row in i["households"]:
            if row["id"] == d[victim]["id"]:
                row.pop("letter_list_only")

    def build_them_a_building(d, i, s):
        s["invented.json"] = '{"occupants": ["%s"]}' % d[victim]["persons"][0]["id"]

    # T-0425, and the pair of them is the assertion the ticket asks for: two
    # printings of ONE return must give ONE bound. `date_the_impression` moves a
    # bound back onto the issue it was read in — the defect itself — and
    # `wrong_rule` leaves the value right and the note claiming the other rule.
    def date_the_impression(d, i, s):
        for path, doc in sorted(d.items()):
            dates = (doc.get("persons") or [{}])[0].get("letter_list_returns") or []
            if dates and bound_for(dates[0])[0] != dates[0]:
                doc["arrival"]["value"] = dates[0]
                return
        raise AssertionError("no letter-list record whose return predates its printing")

    def blur_the_precision(d, i, s):
        d[victim]["arrival"]["precision"] = "exact"

    # T-1005. The eighth card: a flagged person gains an ordinary reading of the
    # papers — a shopkeeper's advertisement beside "known only from the post office".
    # This is how the seven arrived, one consolidation pass at a time.
    def advertise_a_shop(d, i, s):
        d[victim]["persons"][0].setdefault("press_evidence", []).append({
            "list": "newspaper_1833_1835",
            "as_read": "a shopkeeper's advertisement",
            "locator": "chicago_democrat_1834_08_13#c012",
            "record_id": "person_invented",
            "describes_date": "1834-08-13",
            "source": "chicago_democrat_1833_1835",
            "rule": "G1b",
        })

    # T-1121. The defect exactly as it stood on dev: a card whose ordered name
    # keeps the second comma of its printing. The mutation is the printing's own
    # — a comma after the first forename word, which is where `Hugunin, Leonard,
    # C.` left one — and it is put on a card whose family name a reader would
    # then get wrong, because a comma that moves nothing is not the defect.
    def punctuate_the_card(d, i, s):
        for path, doc in sorted(d.items()):
            if not minted_by(path, doc, "letter_list", PREFIX):
                continue
            person = (doc.get("persons") or [{}])[0]
            tokens = str(person.get("name") or "").split()
            if len(tokens) < 3 or "," in person["name"]:
                continue
            spoiled = " ".join([tokens[0] + ","] + tokens[1:])
            if full_word(tokens[0]) and surname(spoiled) != surname(person["name"]):
                person["name"] = spoiled
                return
        raise AssertionError("no card whose name a stray comma would re-read")

    # T-1218. The defect as it would arrive on a fresh card: one letter of the
    # surname re-read, the card moved and the id left where it was. No comma, no
    # reordering — the two readings simply spell the family name differently, and
    # before this gate nothing in the tree noticed.
    def respell_a_card(d, i, s):
        for path, doc in sorted(d.items()):
            if not minted_by(path, doc, "letter_list", PREFIX):
                continue
            person = (doc.get("persons") or [{}])[0]
            pid, shown = person.get("id"), str(person.get("name") or "")
            if pid in RULED or not id_family_name(pid, shown):
                continue
            fam = next((w for w in reversed(words(shown)) if full_word(w)), None)
            if not fam or len(fam) < 4:
                continue
            spoiled = shown.replace(fam, fam[:-2] + fam[-1] + fam[-2], 1)
            if not id_family_name(pid, spoiled):
                person["name"] = spoiled
                return
        raise AssertionError("no card whose surname a re-reading would move")

    # And the licence itself, in both directions it can be abused. A ruled card
    # respelled a THIRD way is the one the ruling file can catch and the card's own
    # `name_ruling` block cannot, because the block would still be sitting there
    # saying what it always said.
    def respell_a_ruled_card(d, i, s):
        doc = d[RULED_PATH]
        person = next(p for p in doc["persons"] if p["id"] in RULED)
        person["name"] = person["name"].replace("z", "s").replace("Z", "S") + "e"

    # A card that loses the adjudication it stands on keeps the divergence and
    # stops carrying the reason for it — which is how this class went unnoticed
    # long enough to need a ticket.
    def unrule_the_card(d, i, s):
        doc = d[RULED_PATH]
        person = next(p for p in doc["persons"] if p["id"] in RULED)
        person["name_ruling"]["displayed_name_was"] = person["name"]

    cases = [
        ("a card's ordered name keeps a comma", punctuate_the_card, "T-1121"),
        ("a card's surname is re-spelled off its id", respell_a_card, "T-1218"),
        ("a ruled card is re-spelled a third way", respell_a_ruled_card, "awards"),
        ("a ruled card drops the adjudication it stands on", unrule_the_card,
         "must carry the adjudication"),
        ("a person loses letter_list_only", drop_flag, "letter_list_only"),
        ("a person loses its returns' dates", drop_dates, "letter_list_returns"),
        ("a household gains a roof", give_a_roof, "lives_at"),
        ("a person gains a trade", give_a_trade, "occupation"),
        ("a household gains a second member", give_a_household, "persons"),
        ("the manifest row loses its flag", unflag_the_row, "manifest row"),
        ("a structure names one of them", build_them_a_building, "data/structures/"),
        ("a bound is dated by the impression, not the return", date_the_impression,
         "T-0425"),
        ("a bound stops being not_later_than", blur_the_precision, "precision"),
        ("a flagged person gains an ordinary press reading", advertise_a_shop,
         "not letter lists"),
    ]
    failed = 0
    for label, mutate, expect in cases:
        problems = broken(mutate)
        hit = [p for p in problems if expect in p]
        if hit:
            print(f"   caught: {label}")
        else:
            failed += 1
            print(f"   NOT CAUGHT: {label} — the gate said {problems or 'nothing'}")
    if failed:
        print(f"   {failed} assertion(s) do not fire when broken")
        return 1
    print(f"   OK: all {len(cases)} of the gate's assertions fire when broken")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and report any drift without writing")
    ap.add_argument("--report", action="store_true",
                    help="print the mint and every refusal")
    ap.add_argument("--scale", "--scale-report", dest="scale", action="store_true",
                    help="what the owner's ruling did to the town, counted here (T-0379)")
    ap.add_argument("--gate", action="store_true",
                    help="prove the minted cohort is what the ruling permits")
    ap.add_argument("--self-test", action="store_true",
                    help="break each of the gate's assertions and require it to fire")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.gate:
        return gate()
    if args.scale:
        scale_report()
        return 0

    files, accepted, refusals, mine_paths = build()
    if args.report:
        docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
        report(accepted, refusals, docs)
        return 0
    if args.check:
        drift = [p for p, text in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        stale = [p for p in sorted(mine_paths)
                 if p not in files]
        for p in drift + stale:
            print(f"   DRIFT: {p.relative_to(ROOT)}")
        if drift or stale:
            print(f"   {len(drift) + len(stale)} file(s) differ from what this pass "
                  f"derives")
            return 1
        print(f"   OK: {len(accepted)} letter-list resident(s) minted from the register, "
              f"{len(refusals)} candidate(s) refused")
        return 0

    for p in sorted(mine_paths):
        if p not in files:
            p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"minted {len(accepted)} letter-list resident(s); refused "
          f"{len(refusals)} candidate(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
