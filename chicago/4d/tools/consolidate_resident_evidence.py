#!/usr/bin/env python3
"""One identity, every source: the cross-domain consolidation of the resident research.

WHY THIS EXISTS, in the owner's words (2026-09-03): "make sure there is consolidation
tickets that build out the full cross source corroboration of these people, like if you
have found and matched philo carpenter from those multiple sources, you should have all
of those in the resident data for him eventually".

THE DEFECT IT MEASURES. Counted across the residents layer on 2026-09-03: 742 of 825
household records cite exactly ONE source, 70 cite two, 13 cite three, and nothing cites
more. Ninety per cent of the town rests on a single source while the crosswalks in
`data/research/` hold rulings nobody has spent. `tools/measure_research_spend.py` puts the
other end of the same fact at 109 rulings reaching a town person and 0 reaching that
person's card. hh_carpenter_philo.json is the worked example: it cites `andreas_1884_v1`
alone while the crosswalks have already ruled the 1833 poll, the 1833 tax list, the 1834
poll and a newspaper person for the same man.

WHAT THIS TOOL DOES, AND WHAT IT DELIBERATELY DOES NOT. It reads every landed domain,
puts one row per IDENTITY against every appearance of that identity anywhere, applies the
owner's ratified grading ladder as a PROPOSAL, and stops. It writes NO household file.
T-0514 mints people from this and T-0515 regrades them; keeping the proposal separate from
the application is what lets the owner read a diff of 849 grades before any of them moves.

IT IS INCREMENTAL BY DESIGN. Wave 1 of the source sweep is open-ended — the owner adds
sources as he finds them — so a consolidation sequenced after "all sweeps land" is
sequenced after never. This runs again after every few sources; a pass that finds nothing
newly closed says so and costs a run nothing.

THE MERGE RULES ARE THE NEWSPAPERS' RULES, because they are already ratified in
`data/research/newspapers/identity.json`: surname-only is always a refusal, and the same
surname with a different forename initial NEVER merges. Two rules are added for the
cross-domain case and both are conservative: an initial-only forename attaches to a full
forename only when exactly ONE full forename in that surname carries the initial (two
rivals is a refusal, not a coin toss), and a name that could be read two ways is refused
with its rivals named. Every merge and every refusal carries a rule id so a later reader
can count which fired.

    tools/consolidate_resident_evidence.py --build       write the three data files
    tools/consolidate_resident_evidence.py --check       they still re-derive; invariants hold
    tools/consolidate_resident_evidence.py --self-test   the assertions still fire when broken
    tools/consolidate_resident_evidence.py --report      the tables, to stdout
    tools/consolidate_resident_evidence.py --coverage    who the ladder has ruled on, and
                                                         who it has not, with the reason

WHO IT HAS RULED ON (T-0692). A grade is only worth something if it can be argued with,
and a person the ladder never looked at carries a grade that means whatever the pass that
wrote it meant. `--coverage` walks every person record in `data/residents/` and puts it in
exactly one state — the rung is on the card, or the rung is ruled and unwritten, or the
ladder cannot see the person and here is why. `--check` fails if that account is not
total, so a person can never again go silently ungraded.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconstructed_person import is_reconstructed  # noqa: E402
import resolve_place_vocabulary  # noqa: E402  (T-1049 — the corpus that says where a place is)

RESEARCH = ROOT / "data" / "research"
RESIDENTS = ROOT / "data" / "residents"
OUT_DIR = RESEARCH / "residents"
MASTER = OUT_DIR / "identity_master.json"
COVERAGE = OUT_DIR / "source_coverage.json"
PROPOSAL = OUT_DIR / "grading_proposal.json"
LADDER_COVERAGE = OUT_DIR / "ladder_coverage.json"
POLICY = ROOT / "docs" / "RESEARCH" / "resident-grading-policy.md"
INDEX = RESIDENTS / "index.json"
CARD_RULINGS = RESIDENTS / "card_merge_rulings.json"
CONFLATIONS = RESIDENTS / "card_conflation_rulings.json"

SCENE_YEAR = 1835
GENERATED_BY = "tools/consolidate_resident_evidence.py --build"

# ---------------------------------------------------------------------------
# THE RULES. Ids are stable and are cited by every row that fires them; the policy
# doc restates them in prose for a human, and this table is what the code obeys.

MERGE_RULES = {
    "M1": "Identical normalised name — same surname, same forename tokens, letter for letter.",
    "M2": "An initial-only forename attaches to the ONE full forename of that surname carrying "
          "the initial. Two or more rivals is R3, never a choice. EVERY initial the reading "
          "prints is compared, not just the leading one (T-1120): where the reading and the "
          "anchor both set a name-part at a position and those parts begin with different "
          "letters, M2 does not fire and R7 refuses.",
    "M3": "A middle initial present on one reading and absent on the other, forename and surname "
          "agreeing, and no rival of that surname carrying a different middle initial.",
    "D1": "A merge already declared by a domain's own crosswalk or by the newspapers' identity.json. "
          "A declared merge outranks every derived rule; this tool never overturns an adjudication.",
}

REFUSAL_RULES = {
    "R1": "Surname only. A record that names no forename can never be merged onto a person "
          "(the newspapers' rule, and the whole of the Newberry finding aid).",
    "R2": "Same surname, different forename initial. Never merges — the newspapers' rule, "
          "stated in identity.json's refused_merges.",
    "R3": "An initial-only forename with two or more rival full forenames of that surname. "
          "Refused with the rivals named rather than guessed at.",
    "R4": "Same surname and same forename initial, but two different full forenames "
          "(Jonathan against John). Two men until something says otherwise.",
    "R7": "SAME LEADING INITIAL, DISAGREEING MIDDLE (T-1120). An initial-only reading and the one full forename M2 would attach it to both set a name-part after the forename, and those parts begin with different letters: `B. S. Sherman` against `Sherman, Benj. F.`. R4 already says two different full forenames behind one initial are two men; this is that fact one position to the right, and M3 exists precisely because the readable case is a middle initial present on ONE side — present on both and different is a disagreement, not a silence. R6's own initials test has compared every position since T-0951; M2 compared only the leading one, and folded across the difference. Two men until something says otherwise.",
    "D2": "A refusal already declared by a domain's own crosswalk or by identity.json.",
    "R6": "A FEMALE HONORIFIC STANDING ON A MAN'S OWN NAME. `Mrs Rufus Brown` is not "
          "Rufus Brown: the honorific strip leaves the husband's forename tokens on both "
          "readings, so M1 fires and folds a wife onto her husband. A reading whose "
          "forename tokens are ENTIRELY those of a reading of the same surname printed "
          "WITHOUT a female honorific is a different person and never merges onto it. "
          "The test is the printed page and not the shape of the name: ONE SOURCE has "
          "to set both readings, which is what keeps `Mrs. Sabrina Mason` on `Mason "
          "Sabrina A.` and `Mrs. Eliza Haight` on the census's Eliza Haight (T-0723). "
          "It reaches two printings: the honorific reading whose forename tokens are "
          "exactly the bare reading's, and (T-0951) the honorific reading printed on "
          "her husband's INITIALS where his own entry sets the forename in full and "
          "exactly one full forename of that surname fits — `Hadley, Mrs. T. G.` beside "
          "`Hadley, Timothy Gibson`, both in Fergus 1843. Two fits is a refusal, not a "
          "choice.",
    "R5": "A PRINTED NAME THIS SPLITTER CANNOT READ AS (surname, forename) AT ALL — a firm "
          "style, an institution, a digit standing where an initial was misread, a "
          "description rather than a name, or more forename tokens than the cap allows. "
          "Distinct from R1, which is the true surname-only case: R1 says the record names "
          "no forename, and saying that of 'Rev. John Mary Irenaeus St Cyr' or of "
          "'8. G. Abbot' would be false of the record. Every R5 row carries WHICH guard "
          "fired, because a refusal whose stated reason is untrue of the page is barely "
          "better than no refusal at all (T-0692).",
}

# T-1004. ONE CARD, TWO MEN — the rules that take a reading OFF a person, and the only
# rules in this file that are not derived from the name. `declared_anchors` below forces
# a reading ONTO a person a crosswalk matched; nothing could force one off, so a card
# gathered a second man in silence and every downstream reading of it was about whichever
# man the reader assumed. The verdicts live in data/residents/card_conflation_rulings.json
# with their reasoning; these are the grounds a verdict may stand on.
SPLIT_RULES = {
    "X1": "ONE VOLUME PRINTS BOTH MEN. The same book sets two entries whose names differ "
          "only by tokens the merge rules ignore, and a directory does not enter one man "
          "twice under two spellings. The fact R6 already rests on, about the page rather "
          "than the name, applied to two men instead of to a wife and her husband.",
    "X2": "THE ENTRY'S OWN QUALIFIER NAMES THE OTHER MAN. An initial-only reading carries "
          "a trade, an employer or an address, and another volume prints that qualifier "
          "against a FULL forename of the surname. M2 attaches an initial to the one full "
          "forename the TOWN holds a card for, which is a fact about the rest of the town "
          "and not evidence about the reading (T-0697, in the other direction).",
    "X3": "THE ARITHMETIC REFUSES IT. A printed age fixes a birth year and the birth year "
          "puts the man at an age on the scene date that the record folded onto him cannot "
          "describe. A man born about 1835 did not write to the post office in 1834.",
    "X0": "RECORDED, NOT SPLIT. The evidence says a card gathers two men and does not say "
          "which reading is whose, or the fold is a landed adjudication only the owner may "
          "reverse. Nothing moves; the ruling is written and gated the other way round.",
}


# The ratified ladder, 2026-09-03, verbatim in the policy doc. One rung, one id, and the
# rung records what class of evidence it accepts.
GRADE_RULES = {
    "G0": ("not_1835_resident", "Every appearance describes a date after the scene year. "
           "1839/1840 alone is never an 1835 resident — later evidence only."),
    "G1a": ("attested", "The 1835 poll list and at least one other independent source."),
    "G1b": ("attested", "A contemporary record naming the person in Chicago — the 1833-1835 "
            "newspapers, which print the person by name in the town."),
    "G1c": ("attested", "CONVERGENCE — two or more independent in-window records from "
            "DIFFERENT class families (the town's civic lists · the contemporary press, "
            "letter lists included · the parish register). Two bodies that did not copy "
            "each other naming one man inside the scene window. A letter list is never "
            "promoted on its own by this rung; it only COUNTS TOWARD convergence."),
    "G2a": ("inferred", "The 1835 poll list alone."),
    "G2b": ("inferred", "An 1833 or 1834 list (poll, tax, muster) with another source."),
    "G2c": ("inferred", "The St Cyr register 1833-1835 — a party to a marriage or burial "
            "in the parish inside the scene window."),
    "G2d": ("inferred", "Hubbard or Fergus or Norris naming a person the town already carries, "
            "with a trade or an address."),
    "G2e": ("inferred", "A Chicago post-office letter list of 1833-1835 and nothing stronger. "
            "The list names a person whose mail is at Chicago; this tool declines to read that "
            "as the ladder's `contemporary record naming the person in Chicago` and grades it "
            "down. See the policy doc — it is the one reading put back to the owner."),
    "G3": ("inferred", "A single appearance and nothing else: documented once, placed by nothing. "
           "Carries resident_subtype `projected_resident`."),
    "G4": ("inferred", "Two or more appearances, none of them of a class a rung above accepts. "
           "Carries resident_subtype `projected_resident` until a rung above fires."),
    "G5": (None, "NO PROPOSAL. The town already carries this person and every appearance this "
           "consolidation can see describes a date after the scene year — their card rests on "
           "sources outside these seven domains (Andreas, the newspapers' own register). The "
           "ladder abstains rather than demote a resident on evidence it has not read; the row "
           "is listed as a conflict for the owner."),
}
GRADE_ORDER = {None: 1, "not_1835_resident": 0, "inferred": 1, "attested": 2}

# Evidence classes, and which rung may spend them. `contemporary` is the 1833-1835 press;
# `later` is anything the ladder forbids from standing alone.
CONTEMPORARY_CLASSES = {"newspaper_1833_1835"}
LETTER_LIST_CLASS = "newspaper_letter_list"
# THE PLACE REFUSAL (T-1049). The gazetteer is a reading of two Chicago papers, and a
# Chicago paper prints men who are not at Chicago: its agents at Michigan City, its
# correspondents at Green Bay, the Albany house whose advertisement it carries. Before
# T-1048 every one of them was handed to the pool as `newspaper_1833_1835`, and merge
# rule M1 — identical normalised name — put them on whatever Chicago card shared the
# name. `hh_miller_samuel` carried David Carver's Michigan City agent that way.
#
# The refusal is a CLASS and not a deletion. A dropped reading is invisible: nobody can
# count it, argue with it, or find the man again when a later source places him in the
# town after all. So the appearance is kept, in the master, under a name — exactly the
# shape LETTER_LIST_CLASS already uses for the other reading this project will not spend.
# What the class does NOT do is appear in any set below: no rung reads it, no family
# counts it, and `independent_records` does not let it corroborate.
#
# WHERE `outside` COMES FROM: `resolve_place_vocabulary.person_resolution()`, the corpus
# T-1048 committed, which resolves each printed place against the bare town, the
# committed 1835 streets and the committed structure names before anything refuses. It
# answers `outside` only when at least one of a person's places resolves outside the town
# and NONE resolves inside it or is undecided. A man with one Chicago address is a
# Chicago appearance whatever else his record carries.
OUT_OF_TOWN_CLASS = "newspaper_out_of_town"
POLL_1835 = "poll_1835"
EARLY_LIST_CLASSES = {"poll_1833", "tax_1833", "poll_1834", "muster_1832"}
CHURCH_SCENE_CLASS = "church_1833_1835"
DIRECTORY_CLASSES = {"directory_1843", "directory_1844", "book_recollection"}
LATER_CLASSES = {"census_1840", "directory_1843", "directory_1844", "death_notice",
                 "church_after_1835", "finding_aid"}

# THE SCENE WINDOW, hoisted out of grade() so the record counter and the rungs read the
# same set. Everything here describes 1832-1835; everything in LATER_CLASSES does not.
SCENE_WINDOW_CLASSES = (CONTEMPORARY_CLASSES | EARLY_LIST_CLASSES
                        | {POLL_1835, CHURCH_SCENE_CLASS, LETTER_LIST_CLASS})

# THE CLASS FAMILIES — who MADE the record, which is what independence turns on. Two
# entries in one family may be one body's habit; one entry in each of two families is two
# bodies that did not copy each other. G1c is the only rung that reads this.
CLASS_FAMILIES = {
    "civic": EARLY_LIST_CLASSES | {POLL_1835},
    "press": CONTEMPORARY_CLASSES | {LETTER_LIST_CLASS},
    "church": {CHURCH_SCENE_CLASS},
}

# ---------------------------------------------------------------------------
# Name normalisation. Deliberately small: this layer decides who is who, so every
# transformation it makes has to be one a reader would make out loud.

HONORIFICS = {"mr", "mrs", "miss", "dr", "rev", "capt", "col", "gen", "lt", "sergt",
              "sgt", "maj", "hon", "esq", "jr", "sr", "widow", "mme", "madame"}
# THE FEMALE TITLES, held apart from the rest of HONORIFICS because they carry a fact the
# others do not: a woman printed under her husband's name. `Mrs Rufus Brown` and `Rufus
# Brown` are two people, and the strip above makes them one reading (T-0723). R6 reads
# this set and nothing else does.
FEMALE_HONORIFICS = {"mrs", "miss", "madame", "mme", "widow"}
ABBREVIATED = {"jno": "john", "jas": "james", "wm": "william", "geo": "george",
               "chas": "charles", "thos": "thomas", "robt": "robert", "jos": "joseph",
               "saml": "samuel", "danl": "daniel", "benj": "benjamin", "edw": "edward",
               "richd": "richard", "alexr": "alexander", "alex": "alexander", "hy": "henry", "nathl": "nathaniel"}

# A COMPOUND SURNAME IS ONE SURNAME (T-0724). This corpus prints the particle with a
# space — `Rev. John Mary Irenaeus St Cyr`, `Cornelius C. Van Horn`, `H. Van Den Bogart`,
# `Calvin De Wolf` — and a splitter that takes only the LAST token reads the priest as a
# `Cyr` and leaves `St` standing among his forenames, which is what pushed him over the
# four-token cap and kept the man who kept the G2c register off the ladder entirely.
# Worse than the cap: `St Cyr` and `Cyr` are two different surnames, so the old reading
# was one rival `Cyr` away from merging him onto somebody else.
#
# The list is CLOSED and it is a list of PRINTINGS, not of languages. Every entry below
# is one this project has actually read in the corpus, and the rule a reader would say
# out loud is "the particle belongs to the name that follows it". Guessing at compounds
# beyond what is printed is exactly how one Cyr becomes another man's.
# Trimmed to exactly this on the evidence: a first draft carried `ste`, `des`, `del`,
# `da` and `di` on the strength of the languages rather than the corpus, and `ste`
# immediately took the forename off `Ste Beadieston` — a man the letter lists print
# `Beadieston, Ste`, whose only printing in the whole corpus is that one. A particle
# nobody here has printed can only cost a reading; it can never win one.
SURNAME_PARTICLES = {"st", "van", "von", "de", "den", "der", "du", "la", "le",
                     "mc", "mac"}


def clean(token: str) -> str:
    return re.sub(r"[^a-z]", "", (token or "").lower())


def name_shaped(token: str) -> bool:
    """Is this token printed the way a forename is — capitalised, or a bare initial?

    The particle rule leans on this and nothing else does. `Peterson. GPO. captain
    schooner St. Joseph` is a Norris directory line with a vessel read into the name,
    and the ONLY thing on the page separating it from `Rev. John Mary Irenaeus St Cyr`
    is that the word before its particle is `schooner` and the word before the priest's
    is `Irenaeus`. A trade is set lower case; a forename is not.
    """
    letters = re.sub(r"[^A-Za-z]", "", token or "")
    return bool(letters) and (letters[0].isupper() or len(letters) == 1)


# ---------------------------------------------------------------------------
# THE TWO MARKS A SQUARE BRACKET MAKES, AND THEY ARE OPPOSITES (T-1155).
#
# Until this existed both sites below ran one regex —
# `re.sub(r"[\[(][^\])]*[\])]", " ", text)` — that deleted a bracket group and
# everything inside it before tokenising. That is right for a PARENTHESIS, which on a
# directory line is an annotation about the man ("Arnold, Isaac Newton, (A. & Ogden,)").
# It is wrong for a square bracket, which in this corpus is the transcriber saying
# WHICH LETTERS the page would not give up. Deleting those letters does not lose a
# note; it loses part of the name, and the name is the key:
#
#   `E. K[in]zie`         -> ` E. K zie`        -> surname `zie`
#   `Esth[e]r M. Bailey`  -> ` Esth r M. Bailey`-> forenames `esth`, `r`
#   `T[e]mple, John T.`   -> ` T mple, John T.` -> surname `tmple`
#   `[W]ade, afarvin R.`  -> ` ade, afarvin R.` -> surname `ade`
#
# Measured on the committed identity master before the repair: 627 appearances carried
# a supply of this shape, and the ids minted off them read `id_ad_el_s_jon_s` for Adiel
# S. Jones and `id_alker_gerge_c` for a Walker.
#
# THE TELL IS WELDING, NOT THE DELIMITER. A supply is set INSIDE a word — a letter
# stands immediately either side of it — because that is what supplying a letter looks
# like. A bracket group standing FREE, with whitespace or an end of string on both
# sides, is the 1843/44 directories' own annotation ("[died July 25, 1886, aged 86½]",
# "[moved to Lockport, Ill.]"): 988 appearances of that shape, and splicing those in
# would read a death date into a man's forenames. So free groups keep the old deletion.
#
# TWO MARKS ARE DELETED WHEREVER THEY STAND, welded or not:
#   `[?]`            — the transcriber could supply NO letter. `compile_gazetteer.
#                      unmarked()` deletes it for exactly this parse and the arithmetic
#                      is the same either way: `[?]rah` cleans to `rah` spliced or cut.
#   `[uncertain: …]` — the wrapper says the printed form supports no reading at all.
#                      Reading its contents as a name here would promote a refusal into
#                      an identity, which is T-1027's question and not this repair's.
#                      119 appearances; their refusals stand unchanged.
#
# ONE FREE GROUP IS STILL A SUPPLY: A SINGLE SUPPLIED LETTER. `[M]. B. Beaubien`,
# `Mark [B.] Beaubien`, `Stephen [F] Black` — the supplied word IS one letter, so there
# is no letter beside the bracket for the welding test to find, and deleting it deletes
# a whole initial. 64 free groups in the committed master are of that shape, against 56
# `[P]. [R]. F[ie]ld`-style readings that the welding test alone refused outright for
# naming no forename. A LETTER IS THE WHOLE RULE: `[Henry] G.` keeps the old deletion,
# because a supplied FORENAME is what T-0855's `bracket_conflict` reads off `as_read`
# to catch a bad fold, and `[d. 1860.]`, `[J/S]` and `[Dr.]` are not single letters
# either.
MARKUP_GROUP = re.compile(r"[\[(][^\])]*[\])]")
SUPPLIED_INITIAL = re.compile(r"^[A-Za-z]\.?$")


def unmark(text: str) -> str:
    """A printed name with the transcriber's markup off and the supplied letters kept."""

    def one(m: re.Match) -> str:
        whole = m.group(0)
        if whole[0] == "(":
            return " "
        inner = whole[1:-1]
        flat = inner.strip().lower()
        if flat == "?" or flat.startswith("uncertain"):
            return " "
        if SUPPLIED_INITIAL.match(inner.strip()):
            return inner
        subject, (start, end) = m.string, m.span()
        before = subject[start - 1] if start else ""
        after = subject[end] if end < len(subject) else ""
        return inner if (before.isalpha() or after.isalpha()) else " "

    return MARKUP_GROUP.sub(one, text)


def split_name(text: str) -> tuple[str, list[str]] | None:
    """(surname_key, forename tokens) out of a printed name, or None if it names nobody."""
    return split_name_or_reason(text)[0]


def split_name_or_reason(text: str) -> tuple[tuple[str, list[str]] | None, str | None]:
    """(parsed, reason). Exactly one of the two is set.

    Handles both orders — 'Adams, W. H.' and 'W. H. Adams' — because the sources print
    both and the comma is what tells them apart.

    THE REASON HALF EXISTS BECAUSE A REFUSAL HAS TO BE TRUE (T-0692). Every guard below
    used to return a bare None, `cluster` filed all of them as R1 "names no forename",
    and the residents layer ended up with seven cards refused for a reason that is false
    of four of them: '8. G. Abbot' prints a forename initial, and 'Rev. John Mary
    Irenaeus St Cyr' prints three forenames. The guards are unchanged; what changes is
    that each one now says which one it was."""
    if not text or not isinstance(text, str):
        return None, "the record prints no name at all"
    text = text.replace("&", " and ")
    if " and " in text.lower():
        # a firm style, not a person
        return None, ("the name joins two parties with 'and' — a firm style or a "
                      "description of a household, not one person")
    # A bracket holds what the printing could not: "William Cr[…]" is a man whose name
    # the column cut, and identity.json has already ruled on him. `unmark` keeps a
    # supplied letter and drops an annotation (T-1155) — but a DIGIT is never part of a
    # name, and the 1843 directory lists institutions in the same alphabetical run as
    # people ("Reading Room (Y. M. A.), 37 Clark, 2d story"), which is how an identity
    # called `a` got minted once.
    text = unmark(text)
    if "," in text:
        surname_part, _, given_part = text.partition(",")
    else:
        parts = [p for p in re.split(r"\s+", text.strip()) if p]
        while parts and clean(parts[-1]) in HONORIFICS:
            parts.pop()              # "John Bates Jr." is a Bates, not a Jr.
        if not parts:
            return None, "the name is an honorific and nothing else"
        if len(parts) > 1 and len(clean(parts[-1])) == 1:
            # PRINTED SURNAME FIRST, and the trailing initial is the tell. The letter
            # lists set "Mason Sabrina A." and "Norton N. R." with no comma at all, and
            # reading the last token as the surname made thirty of the town's own cards
            # unparseable — a name ending in a lone initial is never a surname.
            end = 1
            while end < len(parts) - 1 and clean(parts[end - 1]) in SURNAME_PARTICLES:
                end += 1        # "St Cyr N. R." — the particle carries the token after it
            surname_part, given_part = " ".join(parts[:end]), " ".join(parts[end:])
        else:
            start = len(parts) - 1
            while start > 0 and clean(parts[start - 1]) in SURNAME_PARTICLES:
                start -= 1      # "Van Den Bogart" is one surname, and so is "St Cyr"
            if start and not name_shaped(parts[start - 1]):
                # The particle is preceded by a word that is not printed as a forename,
                # which on a directory line means the trade has been read into the name.
                # Give the particle back: the reading falls to the token count below and
                # is refused there, which is what it was before this rule existed.
                start = len(parts) - 1
            surname_part, given_part = " ".join(parts[start:]), " ".join(parts[:start])
    tokens = [t for t in re.split(r"[\s.]+", given_part) if clean(t)]
    if any(ch.isdigit() for ch in surname_part + given_part):
        return None, ("a digit stands inside the printed name. On a directory line that "
                      "is an address and the row is an institution; on a town card it is "
                      "an OCR misreading of an initial (S. read as 8, H. as I1), so the "
                      "name as stored is not a name the town ever used")
    surname = clean(surname_part)
    # A SURNAME IS NOT AN INITIAL, AND A ROOM IS NOT A MAN. The 1843 and 1844
    # directories list institutions in the same alphabetical run as people, and a
    # naive read of "Reading Room (Y. M. A.), 37 Clark" takes "A.)" for the surname
    # and mints an identity called `a`. One letter is never a surname, and a bracket
    # or a digit in a printed name is the mark of an institution or an address.
    if not surname or len(surname) < 2 or surname in HONORIFICS:
        return None, ("the surname reads as one letter or as an honorific, which is a "
                      "room or an institution in the directory's alphabetical run, "
                      "never a man")

    if len(tokens) > 4:
        return None, (f"{len(tokens)} forename tokens, and the splitter caps at four. "
                      "The compound surnames this corpus prints are joined to the name "
                      "before the count now (T-0724), so a reading still over the cap "
                      "is a line whose trade, address or description has been read "
                      "into the name")
    given = []
    for token in tokens:
        key = clean(token)
        if key in HONORIFICS:
            continue
        given.append(ABBREVIATED.get(key, key))
    return (surname, given), None


def female_honorific(text: str) -> str | None:
    """A female title LEADING a printed name — `Mrs Rufus Brown` — or None.

    T-0723. `split_name_or_reason` strips every honorific, which is right for `John
    Bates Jr.` and wrong for `Mrs Rufus Brown`: what the strip throws away there is the
    only thing on the page saying she is not him. This reads the title back off the
    printed string so `cluster` can hold the pair apart.

    THE TITLE HAS TO LEAD, and that is the whole of the test: the husband-name form
    prints it directly in front of the name it qualifies — `Mrs. Geo. Anderson`,
    `Atkinson, Mrs. Joseph`, `Brown, Mrs. Rufus B.` — so the title is the first token of
    the string, or the first token after the comma in the surname-first printings. A
    title that TRAILS a forename is an annotation on a woman's own name and not a
    husband's: the letter lists set `Gooding, Caroline Miss`, and reading that as a
    husband called Caroline would split one woman into two.
    """
    if not text or not isinstance(text, str):
        return None
    text = unmark(text)
    head = text.partition(",")[2] if "," in text else text
    first = next((clean(t) for t in re.split(r"[\s.]+", head) if clean(t)), None)
    return first if first in FEMALE_HONORIFICS else None


def forename_signature(given: list[str]) -> tuple[str, ...]:
    return tuple(given)


def is_initial(token: str) -> bool:
    return len(token) == 1


def as_printed(token: str) -> str:
    """A name-part the way the page sets it — `F.` for an initial, `Tuttle` for a name."""
    return token.upper() + "." if is_initial(token) else token.title()


def initials_disagree(given: list[str], signature: tuple[str, ...]) -> int | None:
    """T-1120. The first position after the forename where two readings of one name
    set name-parts beginning with DIFFERENT letters -> that index, else None.

    Compares only positions both readings fill: a middle initial present on one side
    and absent on the other is M3's case and stays M3's case. `Ambrose` against `A.`
    agrees — the test is the letter, because a directory abbreviates and a census does
    not, and the same man is printed both ways. `S.` against `F.` does not agree, and
    nothing in this corpus abbreviates Franklin as S.

    Position 0 is skipped: M2's caller has already matched the forename initial, and
    R2/R4 own the ways that one can differ.
    """
    for i in range(1, min(len(given), len(signature))):
        if given[i][0] != signature[i][0]:
            return i
    return None


# ---------------------------------------------------------------------------
# READING THE DOMAINS. Each reader yields appearance dicts; nothing here interprets,
# it only says where a name was printed and what date that printing describes.


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def year_of(value) -> int | None:
    if not value:
        return None
    match = re.search(r"(1[78]\d\d)", str(value))
    return int(match.group(1)) if match else None


def appearance(domain, record_id, source_id, as_read, normalized, locator,
               describes_date, evidence_class):
    return {
        "domain": domain,
        "record_id": record_id,
        "source_id": source_id,
        "as_read": as_read,
        "normalized": normalized,
        "locator": locator,
        "describes_date": describes_date,
        "evidence_class": evidence_class,
    }


def read_civic():
    out = []
    path = RESEARCH / "civic" / "records" / "voter_lists_1833_1835.json"
    doc = load(path) or {}
    for record in doc.get("records", []):
        listname = (record.get("locator") or {}).get("list") or "civic_list"
        out.append(appearance(
            "civic", record["id"], doc.get("source_id"), record.get("as_read"),
            record.get("normalized"), listname, str(year_of(listname) or ""), listname))
    path = RESEARCH / "civic" / "records" / "blackhawk_war_1832_chicago.json"
    doc = load(path) or {}
    for record in doc.get("records", []):
        out.append(appearance(
            "civic", record["id"], doc.get("source_id"), record.get("as_read"),
            record.get("normalized"), record.get("company") or "muster",
            "1832", "muster_1832"))
    return out


# THE CHURCH RECORD FILES, EVERY ONE OF THEM NAMED (T-0841). `read_church()` used to
# carry a two-name tuple, and two more readings sat beside them on disk that nothing in
# this tool read and nothing in this tool said it did not read. That is the defect T-0841
# found: St Mary's baptismal register — 267 named readings, the only kinship evidence this
# project holds — was invisible to the ladder, and the only way to notice was to go and
# look at the directory. A domain missing from `NO_PERSON_ROWS` reads like one nobody
# looked at; a FILE missing from here read like one that was.
#
# So the rule is the same rule NO_PERSON_ROWS keeps at the domain level, one level down:
# every `*.json` in `data/research/church/records/` is either READ below or DECLARED
# unread WITH ITS REASON, `invariants()` fails if a file on disk is neither, and a reading
# that lands tomorrow cannot go quiet — the gate names it the first time it runs.
CHURCH_RECORDS_READ = ("st_cyr_marriages_1834_1839.json", "st_cyr_deaths_1834_1837.json")
CHURCH_RECORDS_NOT_READ = {
    "st_marys_baptisms_1833_1835.json":
        "St Mary's baptismal register 1833-1835, 267 named readings over 57 entries. Its "
        "CROSSWALK already reaches this tool — declared_rulings() and person_links() rglob "
        "every *crosswalk*.json and pick up st_marys_baptisms_crosswalk.json's 8 merges, "
        "18 refusals and 275 rulings — but its RECORD rows do not, so the register rules "
        "on who is who here and never testifies to anybody's presence. Reading it is not a "
        "no-op and it is not the tool's call: G2c accepts `a party to a marriage or "
        "burial`, a baptism is neither, and reading the rows under that class would widen "
        "a rung the owner ratified. Measured on this dev: it moves 137 people onto G2c and "
        "mints 131 identities. T-0841 puts the question to him.",
    "second_presbyterian_members_1842_1892.json":
        "The Second Presbyterian roll, June 1842 to June 1892, 938 records. LATER EVIDENCE "
        "in full — the earliest line on it postdates the scene by seven years and every "
        "record carries beyond_ticket_window — so every row would land in "
        "`church_after_1835` and grade G0, which is what the ladder already says about a "
        "person this roll alone names. It is spent instead by "
        "tools/spend_second_presbyterian_roll.py against its own crosswalk, where a later "
        "roll can corroborate a person the town already carries rather than propose one. "
        "Declared here so the silence is a ruling and not an oversight (T-0841).",
}


def undeclared_church_records() -> list[str]:
    """Church readings on disk that read_church() neither reads nor declares (T-0841)."""
    records = RESEARCH / "church" / "records"
    if not records.is_dir():
        return []
    accounted = set(CHURCH_RECORDS_READ) | set(CHURCH_RECORDS_NOT_READ)
    problems = []
    for path in sorted(records.glob("*.json")):
        if path.name not in accounted:
            problems.append(
                f"data/research/church/records/{path.name} is a church reading the ladder "
                "neither reads nor declares: add it to CHURCH_RECORDS_READ, or to "
                "CHURCH_RECORDS_NOT_READ with the reason it stays out (T-0841)")
    for name in CHURCH_RECORDS_READ:
        if not (records / name).exists():
            problems.append(
                f"read_church() reads data/research/church/records/{name} and the file is "
                "not there — the domain is reading less than it says it does (T-0841)")
    for name, why in CHURCH_RECORDS_NOT_READ.items():
        if not (records / name).exists():
            problems.append(
                f"CHURCH_RECORDS_NOT_READ declares {name} and no such file exists — a "
                "declaration about nothing (T-0841)")
        elif not why:
            problems.append(
                f"{name} is declared unread with no reason (T-0841: the silence is a "
                "ruling or it is an oversight, and only a reason tells them apart)")
    return problems


def read_church():
    out = []
    for name in CHURCH_RECORDS_READ:
        doc = load(RESEARCH / "church" / "records" / name) or {}
        for record in doc.get("records", []):
            year = year_of(record.get("describes_date"))
            klass = (CHURCH_SCENE_CLASS if year and year <= SCENE_YEAR
                     else "church_after_1835")
            out.append(appearance(
                "church", record["id"], doc.get("source_id"), record.get("as_read"),
                record.get("normalized"),
                (record.get("locator") or {}).get("role") or name,
                record.get("describes_date"), klass))
    return out


def read_census_1840():
    out = []
    for path in sorted((RESEARCH / "census_1840" / "pages").glob("*.json")):
        doc = load(path) or {}
        # T-0966: recapitulation rows are page numbers, never household names.
        if doc.get("page_kind") == "recapitulation":
            continue
        for record in doc.get("records", []):
            if not (record.get("normalized") or record.get("as_read")):
                continue
            out.append(appearance(
                "census_1840",
                f"{doc.get('familysearch_id') or path.stem}:{record.get('line')}",
                doc.get("source_id") or "census_1840_cook_county",
                record.get("as_read"), record.get("normalized"),
                f"{doc.get('printed_page')}:{record.get('line')}",
                "1840", "census_1840"))
    return out


def read_directories():
    out = []
    for name, klass, when in (
            ("fergus_1843_directory_entries.json", "directory_1843", "1843"),
            ("norris_1844_directory_entries.json", "directory_1844", "1844")):
        doc = load(RESEARCH / "directories" / "claims" / name) or {}
        for claim in doc.get("claims", []):
            norm = claim.get("normalized") or {}
            if not isinstance(norm, dict) or norm.get("firm"):
                continue
            printed = norm.get("printed_name")
            if not printed:
                continue
            entry = appearance(
                "directories", claim["id"], doc.get("source_id"), claim.get("quote"),
                printed, norm.get("address") or norm.get("place_of_business")
                or norm.get("section"), when, klass)
            entry["occupation"] = norm.get("occupation")
            entry["address"] = norm.get("address")
            # T-1114. Norris prints the place a trade is carried on inside the trade
            # line and marks it with nothing, so the 1844 reading holds it in its own
            # field. It is not a residence and must not be read as one — carried here
            # so a place that used to reach the card inside `occupation` still does.
            entry["place_of_business"] = norm.get("place_of_business")
            out.append(entry)
    return out


def read_old_settlers():
    doc = load(RESEARCH / "old_settlers" / "death_notices.json") or {}
    out = []
    for record in doc.get("records", []):
        norm = record.get("normalized") or {}
        name = norm.get("name") if isinstance(norm, dict) else norm
        out.append(appearance(
            "old_settlers", record["id"], doc.get("source_id"),
            record.get("name_as_read") or record.get("as_read"), name,
            record.get("letter_section"),
            (norm.get("death_date_as_read") if isinstance(norm, dict) else None),
            "death_notice"))
    return out


def read_newspapers():
    doc = load(RESEARCH / "newspapers" / "gazetteer.json") or {}
    out = []
    for person in doc.get("persons", []):
        year = year_of(person.get("first_seen"))
        if not year or year > SCENE_YEAR:
            klass = "newspaper_after_1835"
        elif resolve_place_vocabulary.person_resolution(person) == "outside":
            # THE PLACE REFUSAL (T-1049), and it sits BELOW the date test on purpose:
            # `newspaper_after_1835` is a refusal about WHEN and this one is about WHERE,
            # and a reading that fails the date never reaches the town at all, so the
            # older class keeps its rows and its count unchanged.
            klass = OUT_OF_TOWN_CLASS
        elif person.get("letter_list_only"):
            # THE ONE PLACE THE LADDER NEEDED READING. A post-office list of letters
            # remaining uncalled-for names a person whose MAIL is at Chicago. Whether
            # that is "a contemporary record naming the person in Chicago" is the whole
            # question, and this tool takes the cautious half: a letter-list-only name
            # is inferred (G2e), not attested. The policy doc puts the fork to the owner.
            klass = LETTER_LIST_CLASS
        else:
            klass = "newspaper_1833_1835"
        out.append(appearance(
            "newspapers", person["id"], "chicago_newspapers_1833_1835",
            person.get("name"), person.get("name"),
            (person.get("mentions") or [None])[0],
            person.get("first_seen"), klass))
    return out


# T-1172. `data/residents/readmitted/` is the RECONSTRUCTION, not the research: the
# borderline roster's names offered back at the reconstructed tier by
# tools/readmit_borderline_roster.py. The research instruments below measure what the
# sources say and what has been spent of them, and a reconstruction is neither. Reading it
# here would let an invention raise the research meter, join a crosswalk, or stand as a
# rival card in an identity ruling — which is the exact boundary that stage is built on.
READMITTED_DIR = "readmitted"


def town_records(root):
    """Every committed resident record EXCEPT the reconstruction's own."""
    return [p for p in sorted(root.rglob("*.json")) if p.parent.name != READMITTED_DIR]

def read_town():
    """The residents layer itself. Not a source — it is what the sources are spent onto —
    but an identity has to be able to say which card it already stands on."""
    out = []
    for path in town_records(RESIDENTS):
        doc = load(path)
        if not isinstance(doc, dict) or not isinstance(doc.get("persons"), list):
            continue
        for person in doc["persons"]:
            # T-1171: a drawn person is not an APPEARANCE. Nothing printed their name, so
            # an identity built on one would be this layer corroborating its own invention.
            if is_reconstructed(person):
                continue
            if not person.get("id"):
                continue
            entry = appearance(
                "residents", person["id"], None, person.get("name"),
                person.get("name"), doc.get("id"), None, "town_layer")
            entry["household_id"] = doc.get("id")
            entry["grade"] = person.get("grade")
            entry["resident_subtype"] = person.get("resident_subtype")
            entry["cited_sources"] = sorted(set(person.get("sources") or []))
            out.append(entry)
    return out


READERS = {
    "civic": read_civic,
    "church": read_church,
    "census_1840": read_census_1840,
    "directories": read_directories,
    "old_settlers": read_old_settlers,
    "newspapers": read_newspapers,
    "residents": read_town,
}

# Domains that hold no person-level rows, and why. Named here rather than omitted,
# because a domain missing from the coverage table reads like one nobody looked at.
NO_PERSON_ROWS = {
    "newberry_index": ("finding_aid",
                       "6,728 cards, every one of them a SURNAME heading a locality with no "
                       "forename. R1 refuses all of them by construction: a finding aid names "
                       "a book, not a man. Counted as refusals, never as appearances."),
    "census_1830": ("unread", "The named schedule has not been found; the repo holds county "
                    "aggregates only (T-0498)."),
    "genealogytrails": ("inventory", "An inventory of sections, graded for what each one "
                        "might yield; no names read out of them yet (T-0556)."),
    "books": ("claims", "19 claims about the American Fur Company's trade, none of them a "
              "person-level record; the men they name are already newspaper persons."),
}


# ---------------------------------------------------------------------------
# THE DECLARED ADJUDICATIONS. A crosswalk that has already ruled outranks anything
# derived here: this tool consolidates rulings, it does not second-guess them.


def declared_rulings():
    """(merges, refusals) as name pairs already adjudicated somewhere in the corpus."""
    merges, refusals = [], []
    identity = load(RESEARCH / "newspapers" / "identity.json") or {}
    for row in identity.get("merges", []):
        merges.append({"a": row.get("from"), "b": row.get("into"), "rule": "D1",
                       "declared_in": "newspapers/identity.json#merges",
                       "evidence": row.get("merge_rule")})
    for row in identity.get("refused_merges", []):
        refusals.append({"a": row.get("from"), "b": row.get("into"), "rule": "D2",
                         "declared_in": "newspapers/identity.json#refused_merges",
                         "evidence": row.get("refused_because")})
    for path in sorted(RESEARCH.rglob("*crosswalk*.json")):
        doc = load(path)
        if not isinstance(doc, dict):
            continue
        where = str(path.relative_to(RESEARCH))
        for key, rows in doc.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                a, b = row.get("a") or row.get("from"), row.get("b") or row.get("into")
                if not (isinstance(a, str) and isinstance(b, str)):
                    continue
                target = refusals if "refus" in key else merges if "merge" in key else None
                if target is None:
                    continue
                target.append({"a": a, "b": b,
                               "rule": "D2" if target is refusals else "D1",
                               "declared_in": f"{where}#{key}",
                               "evidence": row.get("evidence") or row.get("rule")
                               or row.get("note")})
    return merges, refusals


def person_links():
    """person_id -> the source ids the rulings that reach them rest on, with the ruling.

    This is the half of the consolidation that T-0598 makes mechanical: a crosswalk that
    states no source id cannot be spent onto a card, and there are 103 of those today.
    They are collected anyway, marked `states_no_source`, so the count is visible."""
    links = defaultdict(list)
    for path in sorted(RESEARCH.rglob("*crosswalk*.json")):
        doc = load(path)
        if not isinstance(doc, dict):
            continue
        where = str(path.relative_to(RESEARCH))
        domain = path.relative_to(RESEARCH).parts[0]
        for key, rows in doc.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                people = []
                for field in ("person_id", "resident", "matched_resident", "household_id"):
                    value = row.get(field)
                    if isinstance(value, str) and value:
                        people.append(value)
                for field in ("person_ids", "residents"):
                    value = row.get(field)
                    if isinstance(value, list):
                        people.extend(v for v in value if isinstance(v, str))
                if not people:
                    continue
                rests = set()
                for disc in row.get("discriminators") or []:
                    if isinstance(disc, dict) and disc.get("source_id"):
                        rests.add(disc["source_id"])
                for sup in row.get("same_name_support") or []:
                    if isinstance(sup, dict) and sup.get("source_id"):
                        rests.add(sup["source_id"])
                if row.get("source_id"):
                    rests.add(row["source_id"])
                for person in sorted(set(people)):
                    links[person].append({
                        "domain": domain,
                        "declared_in": f"{where}#{key}",
                        "outcome": row.get("outcome") or key,
                        "rests_on": sorted(rests),
                        "states_no_source": not rests,
                    })
    return links



# An appearance row as the master carries it. `as_read` is CLIPPED, and the clip is
# deliberate: a directory entry's own quote runs to a paragraph, and eight megabytes of
# re-printed source text in a file whose subject is WHO SOMEBODY IS makes the file
# unreadable to buy nothing — the quote is one `record_id` lookup away in its own domain.
AS_READ_CLIP = 120


def compact(member) -> dict:
    as_read = member.get("as_read")
    if isinstance(as_read, str):
        as_read = " ".join(as_read.split())
        if len(as_read) > AS_READ_CLIP:
            as_read = as_read[:AS_READ_CLIP].rstrip() + "…"
    row = {
        "domain": member["domain"], "record_id": member["record_id"],
        "source_id": member.get("source_id"), "as_read": as_read,
        "locator": member.get("locator"),
        "describes_date": member.get("describes_date"),
        "evidence_class": member["evidence_class"],
    }
    if member.get("normalized") and member.get("normalized") != member.get("as_read"):
        row["normalized"] = member["normalized"]
    for field in ("occupation", "place_of_business", "address"):
        if member.get(field):
            row[field] = member[field]
    return row


# ---------------------------------------------------------------------------
# CLUSTERING. One bucket per surname; inside a bucket, full forenames are the anchors
# and initial-only readings attach to them only when exactly one anchor fits.


def cluster(appearances, splits=None):
    """-> (identities, refusals). An identity is a surname plus one forename signature.

    `splits` is T-1004's ruling table, (domain, record_id) -> verdict, and it is the one
    thing here that overrules the name rules DOWNWARDS: a reading named in it is held out
    of its surname's anchoring and anchored among the other ruled-out readings instead,
    exactly as R6 holds a wife out of her husband's bucket. It defaults to EMPTY rather
    than to the committed file so that a caller passing fixtures — every self-test below
    — gets the derived rules alone; build() passes declared_splits().
    """
    splits = splits or {}
    buckets = defaultdict(list)
    unnamed = []
    for entry in appearances:
        parsed, reason = split_name_or_reason(
            entry.get("normalized") or entry.get("as_read"))
        if not parsed:
            unnamed.append((entry, "R5", reason))
            continue
        if not parsed[1]:
            unnamed.append((entry, "R1",
                            "names no forename, so it can never be merged onto a person"))
            continue
        surname, given = parsed
        entry["_surname"] = surname
        entry["_given"] = given
        entry["_female"] = female_honorific(
            entry.get("normalized") or entry.get("as_read"))
        buckets[surname].append(entry)

    identities, refusals = [], []
    for entry, rule, why in unnamed:
        refusals.append({
            "rule": rule,
            "why": why,
            "domain": entry["domain"], "record_id": entry["record_id"],
            "as_read": entry.get("as_read"),
        })

    def anchor(rows, surname, refusals):
        """One surname's readings folded into anchors by M2 and M3. -> signature -> members.

        Hoisted out of the loop below for T-0723: the wives R6 holds apart from their
        husbands are a bucket of their own and have to be anchored by the same rules —
        `Mrs Rufus Brown` and `Brown, Mrs. Rufus B.` are one woman, and it is M3 that
        says so.
        """
        anchors = {}                     # signature -> members, for full-forename readings
        pending = []
        for entry in rows:
            given = entry["_given"]
            if is_initial(given[0]):
                pending.append(entry)
            else:
                anchors.setdefault(forename_signature(given), []).append(entry)
        # M3: fold a bare 'John Smith' into 'John H. Smith' when there is exactly one
        # such reading and no rival middle initial.
        for signature in sorted(anchors, key=len):
            if len(signature) != 1:
                continue
            rivals = [s for s in anchors if len(s) > 1 and s[0] == signature[0]]
            if len(rivals) == 1:
                anchors[rivals[0]].extend(anchors.pop(signature))
        for entry in pending:
            given = entry["_given"]
            fits = [s for s in anchors if s and s[0][0] == given[0][0]]
            exact = [s for s in anchors if forename_signature(given) == tuple(t[0] for t in s)]
            chosen = None
            # T-1120. M2 compares EVERY initial the reading prints, not the leading one
            # alone. `fits` is matched on given[0] only, so a sole fit can still disagree
            # one position to the right — `B. S. Sherman` reaching `Sherman, Benj. F.` —
            # and folding there crosses a difference the page states. R7 refuses it.
            # `exact` needs every position equal, so it can never be the disagreeing one.
            clash = initials_disagree(given, fits[0]) if len(fits) == 1 else None
            if len(fits) == 1 and clash is None:
                chosen = fits[0]
                entry["_merge_rule"] = "M2"
            elif len(exact) == 1:
                chosen = exact[0]
                entry["_merge_rule"] = "M2"
            elif clash is not None:
                refusals.append({
                    "rule": "R7",
                    "why": ("an initial-only forename and the one full forename of that "
                            "surname it fits set different letters after the forename"),
                    "domain": entry["domain"], "record_id": entry["record_id"],
                    "as_read": entry.get("as_read"),
                    "anchor": " ".join(fits[0]).title() + " " + surname.title(),
                    "disagreeing_position": clash,
                    "reading_prints": as_printed(given[clash]),
                    "anchor_prints": as_printed(fits[0][clash]),
                })
            elif len(fits) > 1:
                refusals.append({
                    "rule": "R3",
                    "why": "an initial-only forename with rival full forenames of the same surname",
                    "domain": entry["domain"], "record_id": entry["record_id"],
                    "as_read": entry.get("as_read"),
                    "rivals": sorted(" ".join(s).title() + " " + surname.title() for s in fits),
                })
            if chosen is not None:
                anchors[chosen].append(entry)
            else:
                anchors.setdefault(forename_signature(given), []).append(entry)
        return anchors

    for surname in sorted(buckets):
        rows = buckets[surname]
        # T-1004. THE READINGS A RULING TAKES OFF A PERSON, held out before anything is
        # anchored. The shape is R6's below — pull them from `rows`, say so once for the
        # surname, and anchor them among THEMSELVES at the foot of the loop — because the
        # need is the same: a reading that the name rules would fold onto a card, held
        # apart by a fact the name cannot carry. The difference is only where the fact
        # comes from. R6 reads it off the page automatically; these are adjudicated one at
        # a time in data/residents/card_conflation_rulings.json, because no rule could
        # have derived that a 69-year-old's death in 1888 is not the man on an 1833 tax
        # list. Held out, not dropped: the reading stands as an identity of its own, the
        # ladder grades it, and where every appearance of it describes a date after the
        # scene year G0 makes it `not_1835_resident` and no card is ever minted.
        ruled_out = [e for e in rows if (e["domain"], e["record_id"]) in splits]
        if ruled_out:
            refusals.append({
                "rule": sorted({str(splits[(e["domain"], e["record_id"])].get("rule"))
                                for e in ruled_out})[0],
                "why": ("a ruling in data/residents/card_conflation_rulings.json takes "
                        "these readings off the person the name rules folded them onto: "
                        "one card was gathering two men"),
                "surname": surname,
                "records": sorted(e["record_id"] for e in ruled_out),
                "held_apart": sorted(
                    {f"{splits[(e['domain'], e['record_id'])].get('belongs_to')}"
                     f" (off {splits[(e['domain'], e['record_id'])].get('off')},"
                     f" {splits[(e['domain'], e['record_id'])].get('rule')})"
                     for e in ruled_out}),
                "declared_in": "residents/card_conflation_rulings.json#cards",
            })
            rows = [e for e in rows if e not in ruled_out]
        # R6, T-0723. A woman whose only printed name is her husband's. The honorific is
        # stripped before the tokens are compared, so `Mrs Rufus Brown` and `Rufus Brown`
        # arrive here letter for letter identical and M1 folds her onto him.
        #
        # THE PAGE HAS TO SAY SO, and this is what keeps the rule from inventing women.
        # `Mrs. Eliza Haight` and `Mrs. Diana Hamilton` are the SAME shape — a leading
        # title on forename tokens the corpus also prints bare — and they are one woman
        # each, printed under her own name. Nothing about the tokens tells Eliza from
        # Rufus; this splitter holds no lexicon of men's names and guessing one is how a
        # real woman gets torn off her own evidence. So R6 fires only where a SOURCE
        # PRINTS BOTH READINGS: Fergus 1843 sets `Brown, Rufus B.` at entry 458 and
        # `Brown, Mrs. Rufus B.` at 459, and a directory does not enter one person twice
        # under two spellings. That is a fact about the page rather than about the name.
        #
        # THE SECOND TEST, T-0951: THE SAME PAGE, AND THE HUSBAND PRINTED IN FULL.
        # The letter-for-letter test above is exactly right for `Mrs. Rufus B. Brown`
        # and it misses the commonest way a directory sets this pair, which is with the
        # wife on her husband's INITIALS and the husband under his whole name three
        # entries away. Fergus 1843 prints `Hadley, Mrs. T. G. (Reed), dress and cloak
        # maker, 147½ Lake` at e1164 and `Hadley, Timothy Gibson (Howard & H.), res
        # alley bet N. Dearborn and Wolcott` at e1166 — two entries, two trades, two
        # addresses — and because `T. G.` is not `Timothy Gibson` letter for letter, R6
        # never looked and M2 folded her onto him by the ordinary initial rule. So the
        # test is widened to the corpus's OWN initial rule: an initials-only honorific
        # reading reaches the one full forename of that surname its initials fit,
        # IN ITS OWN SOURCE, and is refused where more than one fits (R3's discipline).
        #
        # THE GUARD THAT MATTERS IS UNCHANGED: one source has to print both. That is
        # what keeps `Mrs. Eliza Haight` on the census's `Eliza Haight` and `Mrs.
        # Sabrina Mason` on `Mason Sabrina A.`, and it is why this widening does NOT
        # reach `Taylor, Mrs. C.` (T-0960) — the papers print her, and every bare
        # Charles Taylor is in the census or a directory, so no page holds the pair.
        #
        # WHAT IT STILL DOES NOT REACH: `Mrs. Wm. B. Egan`, the Democrat's letter list
        # of 1 April 1834. No body prints a bare `Wm. B. Egan` beside her, and the town
        # already holds the woman under her own forename — Emeline Egan, off Andreas —
        # so the reading is hers and the ruling that says so is in
        # data/residents/card_merge_rulings.json rather than in this rule.
        wives = []
        if any(e.get("_female") for e in rows):
            husbands = defaultdict(set)
            for entry in rows:
                if not entry.get("_female"):
                    husbands[forename_signature(entry["_given"])].add(
                        entry.get("source_id"))
            printed_together = {
                forename_signature(e["_given"])
                for e in rows if e.get("_female") and e.get("source_id")
                and e["source_id"]
                in husbands.get(forename_signature(e["_given"]), ())}
            by_initials = {}
            for entry in rows:
                signature = forename_signature(entry["_given"])
                source = entry.get("source_id")
                if not (entry.get("_female") and source and signature
                        and all(is_initial(t) for t in signature)):
                    continue
                if source in husbands.get(signature, ()):
                    continue
                fits = [s for s in husbands
                        if source in husbands[s] and len(s) == len(signature)
                        and any(not is_initial(t) for t in s)
                        and all(t[0] == i for t, i in zip(s, signature))]
                if len(fits) == 1:
                    by_initials[id(entry)] = fits[0]
            if printed_together or by_initials:
                printed_together |= {forename_signature(e["_given"])
                                     for e in rows if id(e) in by_initials}
                wives = [e for e in rows if e.get("_female")
                         and (forename_signature(e["_given"]) in husbands
                              or id(e) in by_initials)]
        if wives:
            proof = sorted({e["source_id"] for e in wives if e.get("source_id")
                            and forename_signature(e["_given"]) in printed_together})
            refusals.append({
                "rule": "R6",
                "why": ("a female honorific standing on a man's own name: these readings "
                        "carry the husband's forename tokens and nothing else, so the "
                        "honorific strip makes them identical to his. A wife is not her "
                        "husband and never merges onto him"),
                "surname": surname,
                "honorifics": sorted({e["_female"] for e in wives}),
                "held_apart": sorted(
                    {" ".join(forename_signature(e["_given"])).title() + " "
                     + surname.title() for e in wives}),
                "records": sorted({e["record_id"] for e in wives}),
                "printed_together_in": proof,
            })
            rows = [e for e in rows if e not in wives]
        anchors = anchor(rows, surname, refusals)
        # R2/R4 ARE STATED ONCE PER SURNAME, NOT ONCE PER PAIR, and the difference is
        # 17,726 rows against 1,100. Every identity left standing in a bucket is left
        # standing because of one of these two rules, and enumerating the cross product
        # of 40 Smiths says nothing the bucket does not already say. The bucket names
        # what it holds apart and which rule holds each pair apart, which is the fact.
        signatures = sorted(anchors)
        if len(signatures) > 1:
            initials = Counter(s[0][0] for s in signatures)
            refusals.append({
                "rule": "R2" if len(initials) > 1 else "R4",
                "why": ("this surname holds more than one identity: readings with different "
                        "forename initials never merge (R2), and two different full forenames "
                        "behind one initial are two men until something says otherwise (R4)"),
                "surname": surname,
                "held_apart": [" ".join(sig).title() + " " + surname.title()
                               for sig in signatures],
                "distinct_initials": len(initials),
            })
        for signature in signatures:
            members = anchors[signature]
            identities.append({
                "id": "id_" + surname + "_" + ("_".join(signature) or "x"),
                "surname": surname,
                "forename": " ".join(signature),
                "members": members,
                "merge_rules": sorted({m.get("_merge_rule", "M1") for m in members}),
            })
        # The wives R6 held apart, anchored among THEMSELVES by the same rules. The
        # identity carries the honorific in its id and in a field of its own, because a
        # card that reads `Rufus B Brown` twice with nothing to tell the two apart is
        # exactly the confusion this rule exists to end.
        if wives:
            for honorific in sorted({e["_female"] for e in wives}):
                mine = [e for e in wives if e["_female"] == honorific]
                her_anchors = anchor(mine, surname, refusals)
                for signature in sorted(her_anchors):
                    members = her_anchors[signature]
                    identities.append({
                        "id": "id_" + surname + "_" + honorific + "_"
                              + ("_".join(signature) or "x"),
                        "surname": surname,
                        "forename": " ".join(signature),
                        "honorific": honorific,
                        "members": members,
                        "merge_rules": sorted({m.get("_merge_rule", "M1")
                                               for m in members}),
                        "held_apart_by": "R6",
                    })
        # T-1004's readings, anchored among themselves by the same rules. The identity
        # carries the ruling's own X-rule in `held_apart_by`, so the master says WHICH
        # ground took it off its card and a reader is never left to infer it from the id.
        if ruled_out:
            for signature, members in sorted(
                    anchor(ruled_out, surname, refusals).items()):
                verdicts = [splits[(m["domain"], m["record_id"])] for m in members]
                identities.append({
                    "id": "id_" + surname + "_" + ("_".join(signature) or "x"),
                    "surname": surname,
                    "forename": " ".join(signature),
                    "members": members,
                    "merge_rules": sorted({m.get("_merge_rule", "M1") for m in members}),
                    "held_apart_by": sorted({str(v.get("rule")) for v in verdicts})[0],
                    "held_apart_from": sorted({str(v.get("off")) for v in verdicts}),
                })
    return identities, refusals



# ---------------------------------------------------------------------------
# THE DECLARED ANCHORS, and this is the half of the ticket that actually SPENDS a
# ruling. A crosswalk that has already matched a read record to a person in the town
# outranks every rule derived here: `W. H. Adams` on the 1833 poll and `William Hanford
# Adams` on the card were refused by R3 (two rival Adamses of that initial) while
# civic/voter_crosswalk.json had matched them a month ago. Derived caution that
# overturns a landed adjudication is not caution, it is the tool ignoring the corpus.

POSITIVE_OUTCOMES = {"matched", "merged", "match"}
POSITIVE_KEYS = {"merges", "matches", "heads", "entries"}
RECORD_STR_KEYS = ("record_id", "id", "claim_id", "lead_id")
RECORD_LIST_KEYS = ("record_ids", "entries", "entries_1843", "entries_1844", "cards_1844")
PERSON_STR_KEYS = ("person_id", "matched_resident")
PERSON_LIST_KEYS = ("person_ids",)


def _record_ids(row) -> list:
    out = []
    for key in RECORD_STR_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value:
            out.append(value)
    for key in RECORD_LIST_KEYS:
        value = row.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for inner in ("claim", "record_id", "id", "entry_id"):
                    if isinstance(item.get(inner), str):
                        out.append(item[inner])
                        break
    return out


def _person_ids(row) -> list:
    out = []
    for key in PERSON_STR_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value:
            out.append(value)
    for key in PERSON_LIST_KEYS:
        value = row.get(key)
        if isinstance(value, list):
            out.extend(v for v in value if isinstance(v, str))
    return out


def declared_splits(path=None) -> dict:
    """(domain, record_id) -> the ruling that takes that reading off its person.

    T-1004. The ONLY input to this tool that overrules the name rules downwards. It is
    read from data/residents/card_conflation_rulings.json, where each verdict carries the
    person it comes off, the man it belongs to, the rule it stands on and its reasoning.
    Only `state: "split"` rulings appear here — an `X0` ruling is RECORDED and moves
    nothing, and is gated by conflation_problems() instead.
    """
    doc = load(path or CONFLATIONS)
    if not isinstance(doc, dict):
        return {}
    splits = {}
    for card in doc.get("cards", []):
        if not isinstance(card, dict) or card.get("state") != "split":
            continue
        for row in card.get("off_the_card", []):
            domain, record_id = row.get("domain"), row.get("record_id")
            if not (isinstance(domain, str) and isinstance(record_id, str)):
                continue
            splits[(domain, record_id)] = {
                "rule": row.get("rule"),
                "off": card.get("person_id"),
                "card": card.get("card"),
                "belongs_to": row.get("belongs_to"),
                "as_read": row.get("as_read"),
                "for": row.get("for"),
                "declared_in": "residents/card_conflation_rulings.json#cards",
            }
    return splits


def declared_anchors():
    """(domain, record_id) -> {person_id, declared_in, rule} for every LANDED match.

    THE DOMAIN IS THE DIRECTORY, UNLESS THE ROW SAYS OTHERWISE (T-0839). A crosswalk
    lives under the domain it reads — data/research/directories/... adjudicates the
    directories — and that is where the key comes from. One adjudication is not about a
    domain at all: the town-card merge names a person who was split across SEVERAL
    domains at once, and its rows carry a `domains` list saying which. A row that names
    its own domains is anchored in each of them; every other row is unchanged.
    """
    anchors = {}
    for path in sorted(RESEARCH.rglob("*crosswalk*.json")):
        doc = load(path)
        if not isinstance(doc, dict):
            continue
        parts = path.relative_to(RESEARCH).parts
        domain = parts[0]
        where = str(path.relative_to(RESEARCH))
        for key, rows in doc.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                outcome = row.get("outcome")
                positive = (outcome in POSITIVE_OUTCOMES
                            or (outcome is None and key in POSITIVE_KEYS))
                if not positive:
                    continue
                people = _person_ids(row)
                if len(people) != 1:
                    continue
                stated = [d for d in (row.get("domains") or []) if isinstance(d, str)]
                for record_id in _record_ids(row):
                    for one in (stated or [domain]):
                        anchors[(one, record_id)] = {
                            "person_id": people[0],
                            "declared_in": f"{where}#{key}",
                            "rule": "D1",
                        }
    return anchors


def apply_anchors(identities, refusals, anchors):
    """Move every anchored appearance onto the identity that holds its person.

    Returns the D1 merges it made, so the master can say which derived refusals a
    landed adjudication overruled."""
    home = {}
    for identity in identities:
        for member in identity["members"]:
            if member["domain"] == "residents":
                home[member["record_id"]] = identity
    made = []
    overruled = set()
    for identity in list(identities):
        for member in list(identity["members"]):
            anchor = anchors.get((member["domain"], member["record_id"]))
            if not anchor:
                continue
            target = home.get(anchor["person_id"])
            if target is None or target is identity:
                continue
            identity["members"].remove(member)
            member["_merge_rule"] = "D1"
            target["members"].append(member)
            target["merge_rules"] = sorted(set(target["merge_rules"]) | {"D1"})
            overruled.add((member["domain"], member["record_id"]))
            made.append({
                "a": member.get("normalized") or member.get("as_read"),
                "b": target["forename"].title() + " " + target["surname"].title(),
                "rule": "D1",
                "declared_in": anchor["declared_in"],
                "evidence": f"{member['domain']}:{member['record_id']} was matched to "
                            f"{anchor['person_id']} there; the landed adjudication outranks "
                            f"anything derived here",
            })
    kept = [i for i in identities if i["members"]]
    survived = [r for r in refusals
                if (r.get("domain"), r.get("record_id")) not in overruled]
    return kept, survived, made


# ---------------------------------------------------------------------------
# THE LADDER, applied as a proposal.


def in_window_records(identity):
    """The distinct RECORDS naming this identity inside the scene window.

    INDEPENDENCE IS A PROPERTY OF THE RECORD — a distinct list, taken on a distinct
    occasion, by a distinct body — and NOT of the `source_id` that digitised it. This
    function exists because the rungs used to count source_ids and got it wrong (T-0699):
    every Chicago poll, tax and muster list in this project was published by IRAD under
    the single id `chicago_voter_lists_1833_1835_irad`, so

      Willard Jones   tax_1833 + poll_1834 + poll_1835   len(sources) == 1
      Byran Guisin    tax_1833 + poll_1834               len(sources) == 1

    Jones missed G1a and was graded G2a, "The 1835 poll list ALONE", which is false of his
    own evidence blocks; Guisin missed G2b and fell two rungs to G4 `projected_resident`.
    Three lists taken in three different years by the town are three records. That one
    archive digitised them together is a fact about the archive.
    """
    return {(m["evidence_class"], m.get("describes_date"))
            for m in identity["members"]
            if m["evidence_class"] in SCENE_WINDOW_CLASSES}


def independent_records(identity):
    """Every distinct record naming this identity, in the window or after it.

    G1a and G2b are worded "and at least one other independent source" / "with another
    source" — the owner did not require the second one to be inside the window, because
    the FIRST one already carries the 1835 claim and the second corroborates the identity.
    So this counts across all classes; only G1c, which has no in-window anchor of its own
    to rest on, insists that its records be in-window.

    What it must NOT do is count `source_id`s. That was the defect: a man on three IRAD
    lists reads as one source, and a man on the 1835 poll plus an 1843 directory reads as
    two. Same evidence, opposite verdicts, decided by who digitised it.
    """
    return {(m["evidence_class"], m.get("describes_date"))
            for m in identity["members"] if m["domain"] != "residents"
            and m["evidence_class"] != OUT_OF_TOWN_CLASS}


def in_window_families(identity):
    """Which class families name this identity inside the scene window."""
    classes = {m["evidence_class"] for m in identity["members"]}
    return {name for name, members in CLASS_FAMILIES.items() if classes & members}


def grade(identity):
    classes = {m["evidence_class"] for m in identity["members"]}
    domains = {m["domain"] for m in identity["members"]}
    sources = {m["source_id"] for m in identity["members"] if m.get("source_id")}
    on_a_card = "residents" in domains
    evidence_domains = domains - {"residents"}
    n = len([m for m in identity["members"] if m["domain"] != "residents"
             and m["evidence_class"] != OUT_OF_TOWN_CLASS])

    scene_window = (CONTEMPORARY_CLASSES | EARLY_LIST_CLASSES
                    | {POLL_1835, CHURCH_SCENE_CLASS, LETTER_LIST_CLASS})
    if not (classes & scene_window) and classes <= (LATER_CLASSES
                                                    | {"newspaper_after_1835", "town_layer",
                                                       OUT_OF_TOWN_CLASS}):
        if on_a_card:
            return "G5", None, None
        if evidence_domains:
            return "G0", "not_1835_resident", None
    records = independent_records(identity)
    if POLL_1835 in classes and len(records) > 1:
        return "G1a", "attested", None
    if classes & CONTEMPORARY_CLASSES:
        return "G1b", "attested", None
    # G1c — CONVERGENCE, and it sits here because it is an `attested` rung that the two
    # above it cannot reach: neither the 1835 poll nor the contemporary press is present,
    # but two DIFFERENT bodies name the man inside the window. The owner's reading, in his
    # words: "the letter list places someone as likely there, AND there are voter records".
    if len(in_window_families(identity)) > 1 and len(in_window_records(identity)) > 1:
        return "G1c", "attested", None
    if POLL_1835 in classes:
        return "G2a", "inferred", None
    if classes & EARLY_LIST_CLASSES and len(records) > 1:
        return "G2b", "inferred", None
    if CHURCH_SCENE_CLASS in classes:
        return "G2c", "inferred", None
    # G3 SITS HERE, above the two rungs below it, and the order is the ruling. The owner
    # defined projected_resident as "a single appearance with nothing else", and the rungs
    # that outrank it are the ones he named a lone source for — the 1835 poll, the parish
    # register, the contemporary press. A lone letter-list name is not one of those, and
    # the layer already agrees: the 706 `ll_*` people it carries are inferred and
    # projected_resident today, which is what this rung re-derives.
    if n <= 1:
        return "G3", "inferred", "projected_resident"
    if LETTER_LIST_CLASS in classes:
        return "G2e", "inferred", None
    if on_a_card and classes & DIRECTORY_CLASSES and any(
            m.get("occupation") or m.get("address") for m in identity["members"]):
        return "G2d", "inferred", None
    return "G4", "inferred", "projected_resident"


# ---------------------------------------------------------------------------
# BUILD


def place_refusals(rows: list) -> dict:
    """Every reading the place vocabulary refused, by name, so it can be argued with.

    A refusal nobody can see is indistinguishable from a bug. This block names each one:
    the identity it was offered to, the printed place that decided it, and — the part
    that matters — whether the identity STANDS ON A CARD, because those are the readings
    that were being spent on the town before T-1049 and the ones an owner would want to
    check first. The corpus that ruled each place is
    data/research/newspapers/place_vocabulary.json; this block cites the string, not a
    copy of the reasoning, so the two cannot drift.
    """
    gazetteer = {p["id"]: p for p in (load(RESEARCH / "newspapers" / "gazetteer.json")
                                      or {}).get("persons", [])}
    refused = []
    for row in rows:
        for entry in row["appearances"]:
            if entry["evidence_class"] != OUT_OF_TOWN_CLASS:
                continue
            person = gazetteer.get(entry["record_id"], {})
            refused.append({
                "identity": row["id"],
                "gazetteer_person": entry["record_id"],
                "as_read": entry.get("as_read"),
                "places_as_printed": resolve_place_vocabulary.places_of(person),
                "on_a_card": row.get("canonical_person_id"),
            })
    return {
        "_doc": "GENERATED. Newspaper readings the resolved place vocabulary "
                "(data/research/newspapers/place_vocabulary.json, T-1048) places outside "
                "the town, and nowhere inside it. They are carried as evidence class "
                f"`{OUT_OF_TOWN_CLASS}`: no rung spends one, no class family counts one, "
                "and `independent_records` does not let one corroborate. Kept rather than "
                "dropped so the refusal can be counted and argued with.",
        "readings": len(refused),
        "readings_on_an_identity_the_town_carries":
            sum(1 for r in refused if r["on_a_card"]),
        "refused": sorted(refused, key=lambda r: (r["identity"], r["gazetteer_person"])),
    }


def build():
    appearances = []
    for domain, reader in READERS.items():
        appearances.extend(reader())
    splits = declared_splits()
    identities, refusals = cluster(appearances, splits)
    # T-1004. A CONFLATION RULING OUTRANKS THE ANCHOR IT CONTRADICTS, and this is the one
    # place in this tool where a declared adjudication is set aside. `apply_anchors` exists
    # because derived caution must not overturn a landed match, and it is right — but the
    # match it lands is itself derived where a crosswalk matched on the name alone. Norris
    # 1844's `King, N. clerk, at T. King's` was crossed onto Nehemiah King by the
    # directories' own crosswalk, on M2's count of cards, and the ruling that takes it off
    # him rests on Fergus 1839 printing `King, Nathaniel, clerk, Tuthill King` — the page,
    # against a count. Both are declared; the later one was made with the page in hand and
    # it names the anchor it overrules. The override is not silent: every one is written
    # into the master's declared_refusals with the anchor it displaced.
    anchors = declared_anchors()
    overruled_anchors = [
        {"a": splits[key]["as_read"], "b": anchor["person_id"], "rule": splits[key]["rule"],
         "declared_in": splits[key]["declared_in"],
         "evidence": f"{key[0]}:{key[1]} was crossed onto {anchor['person_id']} by "
                     f"{anchor['declared_in']}; T-1004's conflation ruling takes it off "
                     f"that card and gives it to {splits[key]['belongs_to']}. "
                     + str(splits[key].get("for") or "")}
        for key, anchor in sorted(anchors.items()) if key in splits]
    anchors = {k: v for k, v in anchors.items() if k not in splits}
    identities, refusals, anchored = apply_anchors(identities, refusals, anchors)
    declared_merges, declared_refusals = declared_rulings()
    declared_merges = anchored + declared_merges
    declared_refusals = overruled_anchors + declared_refusals
    links = person_links()

    rows = []
    for identity in sorted(identities, key=lambda i: i["id"]):
        members = identity["members"]
        town = [m for m in members if m["domain"] == "residents"]
        canonical = town[0]["record_id"] if town else None
        # EVERY town card this identity absorbed, not only the one `canonical` names.
        # `canonical` is `town[0]` and always was, so an identity holding two cards
        # reported one and dropped the other in silence — which is how `brown_mrs_rufus`
        # and `norton_n_r` came to have no proposal row at all (T-0692). The merge is
        # not changed here; what changes is that the row now SAYS what it absorbed.
        town_person_ids = sorted({m["record_id"] for m in town})
        rests_on, unsourced = set(), 0
        for ruling in links.get(canonical, []) if canonical else []:
            rests_on.update(ruling["rests_on"])
            unsourced += 1 if ruling["states_no_source"] else 0
        cited = set()
        for entry in town:
            cited.update(entry.get("cited_sources") or [])
        offered = {m["source_id"] for m in members if m.get("source_id")}
        row = {
            "id": identity["id"],
            "surname": identity["surname"],
            "forename": identity["forename"],
            "canonical_person_id": canonical,
            "town_person_ids": town_person_ids,
            "household_id": town[0].get("household_id") if town else None,
            "merge_rules": identity["merge_rules"],
            "honorific": identity.get("honorific"),
            "held_apart_by": identity.get("held_apart_by"),
            "held_apart_from": identity.get("held_apart_from"),
            "appearances": [compact(m) for m in members],
            "domains": sorted({m["domain"] for m in members}),
            "sources_offered": sorted(offered),
            "sources_cited_on_the_card": sorted(cited),
            "sources_the_card_has_not_learned":
                sorted(offered - cited - {None}) if canonical else [],
            "rulings_reaching_this_person": len(links.get(canonical, [])) if canonical else 0,
            "rulings_that_state_no_source": unsourced,
        }
        # A row says what it HAS. 5,800 of these identities stand on no card, and six
        # null-or-empty fields apiece on that many rows is a megabyte and a half of the
        # file saying nothing — the reader learns the same thing from the key's absence.
        rows.append({k: v for k, v in row.items()
                     if v or k in ("id", "surname", "forename", "appearances", "domains")})

    master = {
        "schema": 1,
        "_doc": "GENERATED by tools/consolidate_resident_evidence.py --build. One row per "
                "identity, every appearance of that identity in every landed domain, and the "
                "rule that merged or refused each reading. Hand-edit and --check says so.",
        "generated_by": GENERATED_BY,
        "scene_year": SCENE_YEAR,
        "merge_rules": MERGE_RULES,
        "refusal_rules": REFUSAL_RULES,
        "split_rules": SPLIT_RULES,
        "counts": {
            "identities": len(rows),
            "appearances": sum(len(r["appearances"]) for r in rows),
            "identities_on_a_card": sum(1 for r in rows if r.get("canonical_person_id")),
            "identities_in_two_or_more_domains":
                sum(1 for r in rows if len(r["domains"]) > 1),
            "derived_refusals": len(refusals),
            "declared_merges": len(declared_merges),
            "appearances_moved_by_a_landed_adjudication": len(anchored),
            "declared_refusals": len(declared_refusals),
            "appearances_taken_off_a_card_by_a_conflation_ruling": len(declared_splits()),
            "appearances_refused_as_out_of_town": sum(
                1 for r in rows for a in r["appearances"]
                if a["evidence_class"] == OUT_OF_TOWN_CLASS),
            "identities_carrying_an_out_of_town_reading": sum(
                1 for r in rows if any(a["evidence_class"] == OUT_OF_TOWN_CLASS
                                       for a in r["appearances"])),
        },
        "place_refusals": place_refusals(rows),
        "identities": rows,
        "refusals": refusals,
        "declared_merges": declared_merges,
        "declared_refusals": declared_refusals,
    }

    # ---- coverage -------------------------------------------------------
    per_domain = {}
    by_domain_ids = defaultdict(set)
    for row in rows:
        for entry in row["appearances"]:
            by_domain_ids[entry["domain"]].add(row["id"])
    read_counts = Counter()
    matched = Counter()
    for row in rows:
        for entry in row["appearances"]:
            read_counts[entry["domain"]] += 1
            if row.get("canonical_person_id") and entry["domain"] != "residents":
                matched[entry["domain"]] += 1
    for domain in sorted(READERS):
        per_domain[domain] = {
            "names_read": read_counts[domain],
            "identities": len(by_domain_ids[domain]),
            "appearances_on_an_identity_the_town_already_carries": matched[domain],
            "unmatched": read_counts[domain] - matched[domain],
        }
    for domain, (kind, why) in sorted(NO_PERSON_ROWS.items()):
        per_domain[domain] = {"names_read": 0, "identities": 0,
                              "appearances_on_an_identity_the_town_already_carries": 0,
                              "unmatched": 0, "holds": kind, "why": why}
    overlap = {}
    domain_names = sorted(by_domain_ids)
    for index, a in enumerate(domain_names):
        for b in domain_names[index:]:
            shared = len(by_domain_ids[a] & by_domain_ids[b])
            if shared:
                overlap[f"{a}|{b}"] = shared
    town_rows = sum(1 for _ in TOWN_GRADES)
    coverage = {
        "schema": 1,
        "_doc": "GENERATED by tools/consolidate_resident_evidence.py --build. What each domain "
                "was worth against the others: names read, how many landed on an identity the "
                "town already carries, and how far any two domains overlap.",
        "generated_by": GENERATED_BY,
        "domains": per_domain,
        "overlap": overlap,
        "town_rows_this_tool_could_not_parse": {
            "persons_in_the_layer": town_rows,
            "persons_this_tool_placed_on_an_identity": read_counts["residents"],
            "why": "a card whose name is a surname alone, a firm style, or an honorific with "
                   "no forename cannot be split into (surname, forename) and is refused by R1 "
                   "like any other source reading. They are named in the master's refusals.",
        },
        "negative_searches_recorded": {
            "derived_refusals_by_rule": dict(Counter(r["rule"] for r in refusals)),
            "declared_refusals": len(declared_refusals),
        },
    }

    # ---- proposal -------------------------------------------------------
    proposals, conflicts, changes = [], [], []
    tally = Counter()
    subtally = Counter()
    for row in rows:
        rule, proposed, subtype = grade({"members": row["appearances"]})
        tally[proposed] += 1
        subtally[subtype] += 1
        entry = {
            "identity": row["id"],
            "name": (row["forename"] + " " + row["surname"]).title().strip(),
            "canonical_person_id": row.get("canonical_person_id"),
            "rule": rule,
            "grade": proposed,
            "resident_subtype": subtype,
            "evidence": [f"{a['domain']}:{a['record_id']}" for a in row["appearances"]
                         if a["domain"] != "residents"][:12],
            "evidence_classes": sorted({a["evidence_class"] for a in row["appearances"]}),
        }
        proposals.append(entry)
        if row.get("canonical_person_id"):
            current = TOWN_GRADES.get(row["canonical_person_id"], {})
            current_grade = current.get("grade")
            current_sub = current.get("resident_subtype")
            if current_grade != proposed or current_sub != subtype:
                changes.append({
                    "identity": row["id"],
                    "person_id": row["canonical_person_id"],
                    "from": {"grade": current_grade, "resident_subtype": current_sub},
                    "to": {"grade": proposed, "resident_subtype": subtype},
                    "rule": rule,
                    "direction": ("up" if GRADE_ORDER.get(proposed, 1) >
                                  GRADE_ORDER.get(current_grade, 1) else
                                  "down" if GRADE_ORDER.get(proposed, 1) <
                                  GRADE_ORDER.get(current_grade, 1) else "subtype_only"),
                })
        if rule == "G5":
            conflicts.append({
                "identity": row["id"], "kind": "abstention", "rule": "G5",
                "person_id": row.get("canonical_person_id"),
                "why": "the town carries this person and every appearance this consolidation "
                       "can see describes a date after the scene year; their card rests on "
                       "sources outside these domains, so the ladder does not rule",
                "evidence_classes": sorted({a["evidence_class"] for a in row["appearances"]}),
            })
        elif changes and changes[-1]["identity"] == row["id"] and \
                changes[-1]["direction"] == "down":
            conflicts.append({
                "identity": row["id"], "kind": "downgrade", "rule": rule,
                "person_id": row.get("canonical_person_id"),
                "why": "the ladder proposes a lower grade than the card carries; the card was "
                       "graded on evidence this consolidation may not read, so the disagreement "
                       "is listed rather than resolved",
                "from": changes[-1]["from"], "to": changes[-1]["to"],
            })

    proposal = {
        "schema": 1,
        "_doc": "GENERATED by tools/consolidate_resident_evidence.py --build. The owner's "
                "ratified ladder applied to every identity AS A PROPOSAL. Nothing here is "
                "written to a household file: T-0514 mints and T-0515 regrades from this.",
        "generated_by": GENERATED_BY,
        "ladder": {rule_id: {"grade": g, "says": says}
                   for rule_id, (g, says) in GRADE_RULES.items()},
        "baseline_668": {"attested": 117, "inferred": 731,
                         "projected_resident": 706, "persons": 848},
        "counts": {
            "identities": len(proposals),
            "by_grade": {str(k): v for k, v in tally.items()},
            "by_subtype": {str(k): v for k, v in subtally.items()},
            "by_rule": dict(Counter(p["rule"] for p in proposals)),
            "proposed_changes_to_existing_people": len(changes),
            "conflicts": len(conflicts),
        },
        "proposals": proposals,
        "changes_to_existing_people": changes,
        "conflicts": conflicts,
    }
    return master, coverage, proposal


TOWN_GRADES: dict = {}


def _load_town_grades():
    TOWN_GRADES.clear()
    for path in town_records(RESIDENTS):
        doc = load(path)
        if not isinstance(doc, dict) or not isinstance(doc.get("persons"), list):
            continue
        for person in doc["persons"]:
            if person.get("id") and not is_reconstructed(person):
                TOWN_GRADES[person["id"]] = person


# The long arrays are written ONE ROW PER LINE. Pretty-printing 6,600 identities at
# indent=1 costs seven megabytes against five, and this file is rebuilt every
# consolidation pass — a new blob each time. One row per line is smaller, greppable by
# name, and gives a diff that shows which identities changed rather than which lines did.
LINE_ARRAYS = ("identities", "refusals", "declared_merges", "declared_refusals",
               "proposals", "changes_to_existing_people", "conflicts", "person_records")


def dump(path: Path, doc) -> str:
    out = ["{"]
    keys = list(doc)
    for index, key in enumerate(keys):
        tail = "," if index < len(keys) - 1 else ""
        value = doc[key]
        if key in LINE_ARRAYS and isinstance(value, list):
            if not value:
                out.append(f" {json.dumps(key)}: []{tail}")
                continue
            out.append(f" {json.dumps(key)}: [")
            for position, row in enumerate(value):
                comma = "," if position < len(value) - 1 else ""
                out.append("  " + json.dumps(row, ensure_ascii=False,
                                             separators=(",", ":")) + comma)
            out.append(f" ]{tail}")
        else:
            body = json.dumps(value, indent=1, ensure_ascii=False).replace("\n", "\n ")
            out.append(f" {json.dumps(key)}: {body}{tail}")
    out.append("}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# LADDER COVERAGE (T-0692) — WHICH PEOPLE THE LADDER HAS ACTUALLY RULED ON.
#
# The ticket was opened on a count of 18: of the 54 people graded `inferred` while citing
# two or more sources, 18 carried no `ladder_rule` at all, and it read that as "the
# consolidation never reached them". Measuring the WHOLE layer rather than that subset says
# something different, and the difference is the point of this pass:
#
#   1,404 person records · 531 carry a rung on the card · 873 do not.
#   Of those 873, the ladder has ALREADY ruled on 864 — the rung is sitting in
#   grading_proposal.json and nothing ever wrote it onto the card.
#   NINE have no proposal row at all, and those nine are the real gap.
#
# So the fault is a SPEND, not a READ, for all but nine people, and the nine each have a
# nameable reason that the tool already knew and never said out loud:
#
#   * SEVEN are R1 refusals the master has recorded since it was written — a name the
#     splitter cannot turn into (surname, forename): a digit where an initial was misread
#     ("8. G. Abbot", "A. 8. Perry", "James I1. Gabbs"), a surname with no forename at all
#     ("Beckford", "Mrs Temple"), a description rather than a name ("Heacock's wife and
#     children, unnamed"), and one true name the four-token cap turns away
#     ("Rev. John Mary Irenaeus St Cyr").
#   * TWO are absorbed: their row IS on an identity, but `canonical_person_id` is
#     `town[0]` and the identity holds two town cards, so the second one fell out in
#     silence. `brown_mrs_rufus` is folded onto `brown_rufus` — a wife whose only printed
#     name is her husband's, and the honorific strip makes the two indistinguishable —
#     and `norton_n_r` onto `norton_nelson_r`, where the merge is right and the town
#     simply carries the man twice.
#
# THIS PASS MEASURES AND NAMES. It writes no household file and moves no grade: the ticket
# is explicit that the regrade must not ride in the same PR as the measurement, and the
# abstentions here are listed for the owner exactly as the 44 proposed downgrades already
# are. Nobody is downgraded to close the gap.

COVERAGE_STATES = {
    "rule_on_the_card": "The card carries a `ladder_rule`. The ladder has ruled and the "
                        "ruling is written down where a reader of the card can see it.",
    "proposed_not_written": "The ladder HAS ruled this person — the rung is in "
                            "grading_proposal.json — and no pass has written it onto the "
                            "card. A spend, not a reading.",
    "ruled_but_disputed": "The ladder ruled this person and its rung DISAGREES with the "
                          "grade or the subtype the card carries, so the row is on the "
                          "owner's conflict list rather than written onto the card. "
                          "Nothing is graded down to close a coverage gap (T-0720).",
    "absorbed_by_another_card": "The person's row stands on an identity the ladder ruled, "
                                "but that identity names a DIFFERENT town card as its "
                                "canonical person, so the rung was never offered to this "
                                "one. Two cards, one identity.",
    "refused_no_identity": "The consolidation built no identity for this name and said so "
                           "at the time: the refusal is in identity_master.json with its "
                           "rule. The ladder abstains, and here is the reason it abstained.",
}


def ladder_coverage(master, proposal):
    """Every person record in the layer against what the ladder can say about it."""
    by_town_id, canonical_of = {}, {}
    for row in master["identities"]:
        for person_id in row.get("town_person_ids") or []:
            by_town_id[person_id] = row["id"]
            canonical_of[person_id] = row.get("canonical_person_id")
    ruling = {entry["identity"]: entry for entry in proposal["proposals"]}
    # T-0720. A row the proposal itself lists as a change to a committed person is a
    # DISAGREEMENT between the ladder and the card, not an unspent rung: the spend pass
    # may not write it and no pass may apply it without the owner. Held apart here so
    # that `proposed_not_written` means what it says — a rung nobody has spent — and
    # goes to nought when the spend has run.
    disputed = {change["person_id"]
                for change in proposal.get("changes_to_existing_people", [])}
    refused = {}
    for refusal in master["refusals"]:
        if refusal.get("domain") == "residents":
            refused.setdefault(refusal["record_id"], refusal)

    records, states, by_proposed_rule, refusal_rules = [], Counter(), Counter(), Counter()
    by_disputed_rule = Counter()
    total = 0
    for path in town_records(RESIDENTS):
        doc = load(path)
        if not isinstance(doc, dict) or not isinstance(doc.get("persons"), list):
            continue
        for person in doc["persons"]:
            # T-1171: the ladder grades people the SOURCES name. A drawn person has no
            # evidence for a rung to weigh and no grade a rung could check, so they are
            # not a record this coverage is silent about — they are not its subject.
            if is_reconstructed(person):
                continue
            person_id = person.get("id")
            if not person_id:
                continue
            total += 1
            if person.get("ladder_rule"):
                states["rule_on_the_card"] += 1
                continue
            identity_id = by_town_id.get(person_id)
            entry = ruling.get(identity_id) if identity_id else None
            row = {
                "person_id": person_id,
                "household_id": doc.get("id"),
                "name": person.get("name"),
                "grade_on_the_card": person.get("grade"),
                "resident_subtype": person.get("resident_subtype"),
                "sources": sorted(set(person.get("sources") or [])),
                "identity": identity_id,
            }
            if entry and canonical_of.get(person_id) == person_id:
                row["proposed_rule"] = entry["rule"]
                row["proposed_grade"] = entry["grade"]
                if person_id in disputed:
                    row["state"] = "ruled_but_disputed"
                    row["why"] = (f"the ladder's {entry['rule']} disagrees with the grade "
                                  "this card carries; the row is on the owner's conflict "
                                  "list in ladder_spend.json and the card is left alone")
                    by_disputed_rule[entry["rule"]] += 1
                else:
                    row["state"] = "proposed_not_written"
                    row["why"] = (f"the ladder ruled this person {entry['rule']} in "
                                  "grading_proposal.json; no pass has written that rung "
                                  "onto the card")
                    by_proposed_rule[entry["rule"]] += 1
            elif entry:
                row["state"] = "absorbed_by_another_card"
                row["proposed_rule"] = entry["rule"]
                row["proposed_grade"] = entry["grade"]
                row["absorbed_by"] = canonical_of.get(person_id)
                row["why"] = (f"identity {identity_id} holds this card and "
                              f"{canonical_of.get(person_id)}, and the proposal names the "
                              "other one; the rung was ruled for the identity and never "
                              "offered to this card")
            elif person_id in refused:
                refusal = refused[person_id]
                row["state"] = "refused_no_identity"
                row["refusal_rule"] = refusal["rule"]
                row["why"] = refusal.get("why")
                refusal_rules[refusal["rule"]] += 1
            else:
                row["state"] = "unclassified"
                row["why"] = ("neither a rung, nor a refusal, nor an identity — the "
                              "invariant that forbids this row is in invariants()")
            states[row["state"]] += 1
            records.append(row)

    return {
        "schema": 1,
        "_doc": "GENERATED by tools/consolidate_resident_evidence.py --build (T-0692). "
                "Every person record in data/residents/ that carries no `ladder_rule`, "
                "against what the ratified ladder can say about it. NOTHING HERE IS "
                "APPLIED: the ticket keeps the measurement and the regrade in separate "
                "passes, and a rung listed here is an offer, not a change.",
        "generated_by": GENERATED_BY,
        "states": {name: {"says": says, "people": states.get(name, 0)}
                   for name, says in COVERAGE_STATES.items()},
        "counts": {
            "person_records": total,
            "carry_a_rule": states.get("rule_on_the_card", 0),
            "carry_no_rule": len(records),
            "proposed_not_written_by_rule": dict(sorted(by_proposed_rule.items())),
            "ruled_but_disputed_by_rule": dict(sorted(by_disputed_rule.items())),
            "refused_by_rule": dict(sorted(refusal_rules.items())),
            "the_ladder_has_never_looked": (states.get("absorbed_by_another_card", 0)
                                            + states.get("refused_no_identity", 0)
                                            + states.get("unclassified", 0)),
            "on_the_owners_conflict_list": states.get("ruled_but_disputed", 0),
        },
        "person_records": records,
    }


def cmd_build(write=True):
    _load_town_grades()
    master, coverage, proposal = build()
    ladder = ladder_coverage(master, proposal)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = [(MASTER, master), (COVERAGE, coverage), (PROPOSAL, proposal),
             (LADDER_COVERAGE, ladder)]
    if write:
        for path, doc in files:
            path.write_text(dump(path, doc), encoding="utf-8")
            print(f"  wrote {path.relative_to(ROOT)}")
    return master, coverage, proposal, ladder


def deferred_card_clusters(path: Path = CARD_RULINGS) -> dict:
    """The duplicate clusters T-0839's ruling pass deliberately left standing.

    A deferred entry names the cards, the ticket that owns them and why — it is a
    written ruling that the cards are duplicates and that a NAMED ticket is moving
    them, which is the only thing that may hold the gate below open. Anything else
    carrying two cards on one identity is a duplicate nobody has ruled on.
    """
    doc = load(path) or {}
    return {frozenset(row.get("cards") or []): row for row in doc.get("deferred") or []}


def conflation_problems(master, doc=None) -> list[str]:
    """T-1004. THE CONFLATION RULINGS, HELD TO WHAT THEY CLAIM.

    A ruling that quietly stops being true is worse than no ruling: the next pass reads
    it instead of the page. So each one is re-proved against the master this run built,
    and the two states are gated in OPPOSITE directions, which is the whole point of
    writing an X0 down at all.

      split     — the reading must be OFF the person it was ruled off, on an identity
                  held apart by the ruling's own rule, and that identity must stand on
                  no card where the ruling says the second man is not in the layer.
                  A ruling whose reading has drifted back onto its card is red.
      recorded  — the readings named in `still_on_the_card` must STILL be on that
                  person. Nothing moves for an X0, so the only way it can go stale is
                  for something else to move it, and that is exactly what this catches.

    `name_as_ruled` is checked the same way: the card carries the name the ruling gives
    it, or the ruling is not in force.
    """
    doc = doc if doc is not None else load(CONFLATIONS)
    if not isinstance(doc, dict):
        return ["data/residents/card_conflation_rulings.json is missing or unreadable"]
    problems = []
    home, names, carded = {}, {}, {}
    for row in master["identities"]:
        for entry in row["appearances"]:
            home[(entry["domain"], entry["record_id"])] = row
            if entry["domain"] == "residents":
                names[entry["record_id"]] = entry.get("as_read")
                carded[entry["record_id"]] = row
    for card in doc.get("cards", []):
        who, state = card.get("person_id"), card.get("state")
        where = f"conflation ruling on {who}"
        if who not in names:
            problems.append(f"{where}: no person of that id stands in the residents layer")
            continue
        if card.get("name_as_ruled") and names[who] != card["name_as_ruled"]:
            problems.append(f"{where}: the card reads {names[who]!r} and the ruling gives "
                            f"it {card['name_as_ruled']!r}")
        if state == "split":
            for row in card.get("off_the_card", []):
                key = (row.get("domain"), row.get("record_id"))
                rule = row.get("rule")
                if rule not in SPLIT_RULES:
                    problems.append(f"{where}: {key[1]} cites unknown split rule {rule}")
                if not row.get("for"):
                    problems.append(f"{where}: {key[1]} is ruled off and states no reason")
                holder = home.get(key)
                if holder is None:
                    problems.append(f"{where}: {key[1]} is not a reading this corpus holds")
                    continue
                if holder is carded.get(who):
                    problems.append(f"{where}: {key[1]} is ruled off this card and is "
                                    f"still on it — the split is not in force")
                    continue
                if holder.get("held_apart_by") != rule:
                    problems.append(f"{where}: {key[1]} stands on {holder['id']}, which is "
                                    f"held apart by {holder.get('held_apart_by')} and not "
                                    f"by the ruling's {rule}")
                if (card.get("second_man_in_the_layer") is False
                        and holder.get("canonical_person_id")):
                    problems.append(
                        f"{where}: the ruling says the second man is not in the layer and "
                        f"{holder['id']} now stands on card "
                        f"{holder['canonical_person_id']}")
        elif state == "recorded":
            if not card.get("open_question_for_the_owner") and not card.get("for"):
                problems.append(f"{where}: recorded as gathering two men and states nothing")
            for record_id in card.get("still_on_the_card", []):
                holder = next((r for r in (home.get((d, record_id)) for d in
                               ("civic", "newspapers", "directories", "old_settlers",
                                "church", "census_1840", "residents")) if r), None)
                if holder is None:
                    problems.append(f"{where}: {record_id} is not a reading this corpus holds")
                elif holder is not carded.get(who):
                    problems.append(f"{where}: {record_id} is recorded as still on this "
                                    f"card and has moved to {holder['id']} — the ruling "
                                    f"is stale and needs re-reading, not re-stating")
        else:
            problems.append(f"{where}: state {state!r} is neither split nor recorded")
    return problems


def invariants(master, proposal, ladder=None, deferred=None) -> list[str]:
    """The assertions the acceptance names. Each returns a sentence, or nothing."""
    problems = list(undeclared_church_records())
    seen = {}
    for row in master["identities"]:
        if row["id"] in seen:
            problems.append(f"identity {row['id']} appears in two rows")
        seen[row["id"]] = row
    anchored = defaultdict(list)
    for row in master["identities"]:
        for entry in row["appearances"]:
            anchored[(entry["domain"], entry["record_id"])].append(row["id"])
    for key, holders in anchored.items():
        if len(holders) > 1:
            problems.append(f"{key[0]}:{key[1]} is claimed by {len(holders)} identities")
    for refusal in master["refusals"]:
        if refusal["rule"] not in REFUSAL_RULES and refusal["rule"] not in SPLIT_RULES:
            problems.append(f"a refusal cites unknown rule {refusal['rule']}")
        if not refusal.get("why"):
            problems.append("a refusal states no reason")
    for row in master["identities"]:
        for rule in row["merge_rules"]:
            if rule not in MERGE_RULES:
                problems.append(f"identity {row['id']} cites unknown merge rule {rule}")
    # T-0843. ONE IDENTITY, ONE CARD — the gate that stops the NEXT duplicate.
    #
    # T-0839 found 39 surname clusters holding 110 town cards that were fewer people
    # and PR #929 folded 42 of them under written rulings; `consolidate_town_cards.py
    # --check` gates that every candidate cluster carries one. That is ruling COVERAGE
    # over the duplicates that exist. This is the other half, and the owner's ticket is
    # explicit that it is the half that matters: a minting pass that writes a new card
    # for a person the town already holds fails HERE, in the file whose whole job is to
    # say what one identity is, rather than silently in the population count.
    #
    # The test is the master's own answer to its own question. An identity carrying two
    # `town_person_ids` is an identity the master's M1/M2/M3 merged and the town wrote
    # twice — nothing derived here, just the row read back. The only way past it is a
    # DEFERRAL: a written entry in data/residents/card_merge_rulings.json naming the
    # cards, the ticket that owns them and the reason. Two stand today, both handed to
    # T-0723 by name, and neither may be widened without editing that file and saying so.
    deferred = deferred_card_clusters() if deferred is None else deferred
    for row in master["identities"]:
        cards = row.get("town_person_ids") or []
        if len(cards) < 2:
            continue
        entry = deferred.get(frozenset(cards))
        if entry is None:
            problems.append(
                f"identity {row['id']} stands on {len(cards)} town cards "
                f"({', '.join(cards)}) and nothing rules on them: one person, one card "
                "— either merge them under a ruling in data/residents/"
                "card_merge_rulings.json or defer them there to a named ticket (T-0843)")
        elif not entry.get("to") or not entry.get("why"):
            problems.append(
                f"identity {row['id']} is deferred without a ticket or a reason "
                "(T-0843: a deferral is a written ruling, not a silence)")
    for entry in proposal["proposals"]:
        rule = entry["rule"]
        if rule not in GRADE_RULES:
            problems.append(f"{entry['identity']} cites unknown grade rule {rule}")
            continue
        allowed = GRADE_RULES[rule][0]
        if GRADE_ORDER.get(entry["grade"], 1) > GRADE_ORDER.get(allowed, 1):
            problems.append(f"{entry['identity']} is graded {entry['grade']} above what "
                            f"{rule} allows ({allowed})")
        if entry["grade"] != "not_1835_resident" and not entry["evidence_classes"]:
            problems.append(f"{entry['identity']} is graded on no evidence")
    # T-0692. THE COVERAGE IS TOTAL OR IT IS NOTHING. The whole value of the ladder is
    # that a grade is checkable, and a person the ladder never looked at has a grade that
    # means whatever the pass that wrote it meant. So: every person record is either
    # ruled or refused WITH ITS REASON, the two halves add up to the layer, and no row is
    # allowed to sit in `unclassified` — the state that says the tool met a person it has
    # no account of at all.
    if ladder is not None:
        counts = ladder["counts"]
        if counts["carry_a_rule"] + counts["carry_no_rule"] != counts["person_records"]:
            problems.append(
                f"ladder coverage does not add up: {counts['carry_a_rule']} with a rung "
                f"+ {counts['carry_no_rule']} without against "
                f"{counts['person_records']} person records")
        stranded = [row["person_id"] for row in ladder["person_records"]
                    if row["state"] == "unclassified"]
        if stranded:
            problems.append(
                f"{len(stranded)} person record(s) are neither ruled nor refused, so "
                f"nothing says why the ladder is silent about them "
                f"(first: {', '.join(stranded[:5])})")
        for row in ladder["person_records"]:
            if not row.get("why"):
                problems.append(f"{row['person_id']} is uncovered by the ladder and the "
                                "coverage states no reason")
                break
    return problems



# ---------------------------------------------------------------------------
# THE LADDER, WHERE A BROWSER CAN READ IT (T-0668).
#
# `GRADE_RULES` above is the ratified ladder and it is Python. The reader is
# JavaScript, and until this block existed nothing under `data/` carried the text
# of a rung — so a card printing `G2c` beside a person's grade would have printed
# a code whose meaning lives in a file no visitor opens. That is the same defect
# the 1840 bridge had (T-0491): a verdict shown without the reasoning that reached
# it is an assertion.
#
# ONE SOURCE OF TRUTH, NOT TWO. The rung text is not re-typed into the manifest by
# hand and it is not re-typed into the renderer either. `--write-vocabulary` copies
# it out of `GRADE_RULES`, and `--check` — which `tools/check.sh` runs — fails if
# the manifest and the constant ever drift apart. Editing one without the other is
# a gate failure rather than a silent lie on 531 cards.


def ladder_vocabulary() -> list:
    """The ratified ladder as the manifest carries it, in the ladder's own order.

    A LIST of rungs and not an object keyed by rung id, because
    `tools/measure_layer_reads.py` walks a manifest structurally: an object would
    declare `ladder_rules.G2c.rule` as a figure of its own, eleven rungs would be
    twenty-one figures, and every rung added later would be a new unread figure the
    gate would demand be re-banked. A list of records is three figures, whatever the
    ladder grows to.
    """
    return [{"rung": rule, "grade": grade, "rule": text}
            for rule, (grade, text) in GRADE_RULES.items()]


def cmd_write_vocabulary() -> int:
    if not INDEX.exists():
        print(f"  FAIL {INDEX.relative_to(ROOT)} is missing")
        return 1
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    vocab = index.setdefault("vocabulary", {})
    vocab["ladder_rules"] = ladder_vocabulary()
    INDEX.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    print(f"  wrote {len(vocab['ladder_rules'])} rung(s) to "
          f"{INDEX.relative_to(ROOT)} vocabulary.ladder_rules")
    return 0


def vocabulary_problems() -> list:
    """Where the manifest's copy of the ladder disagrees with GRADE_RULES."""
    if not INDEX.exists():
        return [f"{INDEX.relative_to(ROOT)} is missing"]
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    got = (index.get("vocabulary") or {}).get("ladder_rules")
    want = ladder_vocabulary()
    if got is None:
        return ["vocabulary.ladder_rules is missing from data/residents/index.json — "
                "the card prints a rung id and nothing under data/ says what it means. "
                "Run --write-vocabulary."]
    if got == want:
        return []
    if not isinstance(got, list):
        return ["vocabulary.ladder_rules must be a list of rungs"]
    by_id = {row.get("rung"): row for row in got}
    problems = []
    for row in want:
        rung = row["rung"]
        if rung not in by_id:
            problems.append(f"vocabulary.ladder_rules is missing rung {rung}")
        elif by_id[rung] != row:
            problems.append(f"vocabulary.ladder_rules disagrees with GRADE_RULES on "
                            f"rung {rung} — the manifest says {by_id[rung]!r}")
    for rung in by_id:
        if rung not in {row["rung"] for row in want}:
            problems.append(f"vocabulary.ladder_rules carries rung {rung}, "
                            f"which the ladder no longer has")
    if not problems:
        problems.append("vocabulary.ladder_rules holds the rungs in an order the ladder "
                        "does not — the card prints them in file order")
    return problems


def cmd_check() -> int:
    failures = 0
    _load_town_grades()
    master, coverage, proposal = build()
    ladder = ladder_coverage(master, proposal)
    for path, doc in ((MASTER, master), (COVERAGE, coverage), (PROPOSAL, proposal),
                      (LADDER_COVERAGE, ladder)):
        if not path.exists():
            print(f"  FAIL {path.relative_to(ROOT)} is missing — run --build")
            failures += 1
            continue
        if path.read_text(encoding="utf-8") != dump(path, doc):
            print(f"  FAIL {path.relative_to(ROOT)} does not re-derive from the sources — "
                  "hand-edited, or a source moved under it. Run --build.")
            failures += 1
        else:
            print(f"  ok    {path.relative_to(ROOT)} re-derives")
    problems = invariants(master, proposal, ladder)
    # T-1004. The conflation rulings are held to what they claim against the master this
    # run built. It is not in invariants() because invariants() is exercised by fixtures
    # — two-identity masters that hold none of the real town — and a ruling about Erastus
    # Bowen has nothing to say about those. It belongs here, where the master is the town.
    conflations = conflation_problems(master)
    for problem in conflations[:10]:
        print(f"  FAIL {problem}")
    failures += 1 if conflations else 0
    if not conflations:
        ruled = load(CONFLATIONS) or {}
        cards = ruled.get("cards") or []
        split = sum(len(c.get("off_the_card") or []) for c in cards
                    if c.get("state") == "split")
        print(f"  ok    {len(cards)} card(s) ruled on for gathering two men — {split} "
              f"reading(s) held off the card they were folded onto, and every ruling "
              f"still says what the master says")
    for problem in problems[:10]:
        print(f"  FAIL {problem}")
    failures += 1 if problems else 0
    if not problems:
        counts = master["counts"]
        print(f"  ok    {counts['identities']} identities over {counts['appearances']} "
              f"appearances; {counts['identities_in_two_or_more_domains']} stand in two or "
              f"more domains; {counts['derived_refusals']} refusals, every one with a rule")
    if not POLICY.exists():
        print(f"  FAIL {POLICY.relative_to(ROOT)} is missing — the ladder has to be written down")
        failures += 1
    else:
        text = POLICY.read_text(encoding="utf-8")
        missing = [r for r in GRADE_RULES if r not in text]
        if missing:
            print(f"  FAIL the policy doc does not carry rung(s) {', '.join(missing)}")
            failures += 1
        else:
            print("  ok    the policy doc carries every rung of the ratified ladder")
    drift = vocabulary_problems()
    for problem in drift[:5]:
        print(f"  FAIL {problem}")
    failures += 1 if drift else 0
    if not drift:
        print(f"  ok    data/residents/index.json carries all {len(GRADE_RULES)} rung(s) "
              f"verbatim, so the card can print what a rung says")
    return failures


# ---------------------------------------------------------------------------
# SELF-TEST. Each case breaks one thing and asserts the gate notices.


def cmd_self_test() -> int:
    failures = 0

    # ---- T-0699: the rungs count RECORDS, and convergence is a rung ----------
    def ident(*members):
        return {"members": [dict(domain=d, evidence_class=c, describes_date=y,
                                 source_id=sid, record_id=f"r{i}")
                            for i, (d, c, y, sid) in enumerate(members)]}

    def rung(*members):
        return grade(ident(*members))[0]

    IRAD = "chicago_voter_lists_1833_1835_irad"

    def case(name, got, want):
        nonlocal failures
        if got == want:
            print(f"  ok    {name} → {got}")
        else:
            print(f"  FAIL  {name} → {got}, wanted {want}")
            failures += 1

    # (a) THE DEFECT. Three lists, three years, one archive. Counting source_ids
    # made this "the 1835 poll list ALONE" (G2a) — false of the record.
    case("three IRAD lists under one source_id reach G1a",
         rung(("civic", "tax_1833", "1833", IRAD),
              ("civic", "poll_1834", "1834", IRAD),
              ("civic", "poll_1835", "1835", IRAD)), "G1a")
    case("…and the 1835 poll genuinely alone is still G2a",
         rung(("civic", "poll_1835", "1835", IRAD)), "G2a")
    case("two early lists under one source_id reach G2b, not G4",
         rung(("civic", "tax_1833", "1833", IRAD),
              ("civic", "poll_1834", "1834", IRAD)), "G2b")

    # (b) CONVERGENCE. Two bodies that did not copy each other, in the window.
    case("a poll list and a letter list converge to G1c",
         rung(("civic", "poll_1834", "1834", IRAD),
              ("press", "newspaper_letter_list", "1835-05-20", "democrat")), "G1c")
    case("…but a letter list ALONE is never promoted by it",
         rung(("press", "newspaper_letter_list", "1835-05-20", "democrat")), "G3")
    case("…nor are two letter lists, which are one family",
         rung(("press", "newspaper_letter_list", "1834-04-01", "democrat"),
              ("press", "newspaper_letter_list", "1835-05-20", "democrat")), "G2e")
    case("…nor are two civic lists, which are also one family",
         rung(("civic", "tax_1833", "1833", IRAD),
              ("civic", "poll_1834", "1834", IRAD)), "G2b")
    case("the parish register converges with a civic list too",
         rung(("civic", "poll_1834", "1834", IRAD),
              ("church", "church_1833_1835", "1834", "stcyr")), "G1c")

    # (c) THE GUARD. G0 survives: later evidence never attests on its own.
    case("two later sources and nothing in-window stay not_1835_resident",
         rung(("books", "directory_1843", "1843", "fergus"),
              ("books", "death_notice", "1855", "fergus")), "G0")
    case("…and a later source cannot lift a lone letter list into convergence",
         rung(("press", "newspaper_letter_list", "1835-05-20", "democrat"),
              ("books", "directory_1843", "1843", "fergus")), "G2e")


    # ---- T-0841: a church reading on disk that nothing reads and nothing declares ----
    #
    # The defect was silent for as long as the file list lived in a tuple inside
    # read_church(): St Mary's baptismal register sat in data/research/church/records/
    # and no output of this tool mentioned it either way. The gate has to fire on the
    # SHAPE of that — a file accounted for by neither table — not on those two names, so
    # the case takes the accounting away rather than the file.
    global CHURCH_RECORDS_READ, CHURCH_RECORDS_NOT_READ
    kept_read, kept_unread = CHURCH_RECORDS_READ, CHURCH_RECORDS_NOT_READ
    try:
        CHURCH_RECORDS_READ, CHURCH_RECORDS_NOT_READ = (), {}
        undeclared = undeclared_church_records()
        if not undeclared:
            print("  FAIL a church reading nothing reads and nothing declares passed the gate")
            failures += 1
        else:
            print(f"  ok    an unaccounted church reading fails the gate → {undeclared[0][:72]}…")
        CHURCH_RECORDS_READ, CHURCH_RECORDS_NOT_READ = kept_read, dict(
            kept_unread, **{n: "" for n in kept_unread})
        silent = undeclared_church_records()
        if not any("no reason" in problem for problem in silent):
            print("  FAIL a church reading declared unread with no reason was accepted")
            failures += 1
        else:
            print("  ok    …and declaring one unread without a reason is not a declaration")
        CHURCH_RECORDS_READ, CHURCH_RECORDS_NOT_READ = kept_read, dict(
            kept_unread, **{"a_reading_that_is_not_there.json": "a reason for nothing"})
        phantom = undeclared_church_records()
        if not any("declaration about nothing" in problem for problem in phantom):
            print("  FAIL a declaration naming a file that does not exist was accepted")
            failures += 1
        else:
            print("  ok    …and a declaration about a file that is not there fails too")
    finally:
        CHURCH_RECORDS_READ, CHURCH_RECORDS_NOT_READ = kept_read, kept_unread
    if undeclared_church_records():
        print("  FAIL the church record tables do not account for the readings on disk")
        failures += 1
    else:
        print("  ok    every church reading on disk is read or declared, with its reason")

    def assert_fires(what, master, proposal):
        nonlocal failures
        problems = invariants(master, proposal)
        if problems:
            print(f"  ok    {what} → {problems[0]}")
        else:
            print(f"  FAIL {what} did not fire")
            failures += 1

    base_master = {"identities": [{"id": "id_smith_john", "surname": "smith",
                                  "forename": "john", "merge_rules": ["M1"],
                                  "appearances": [{"domain": "civic", "record_id": "x1",
                                                   "evidence_class": "poll_1835"}]}],
                   "refusals": [{"rule": "R1", "why": "names no forename"}]}
    base_proposal = {"proposals": [{"identity": "id_smith_john", "rule": "G2a",
                                    "grade": "inferred", "evidence_classes": ["poll_1835"]}]}
    problems = invariants(base_master, base_proposal)
    if problems:
        print(f"  FAIL the clean fixture is not clean: {problems[0]}")
        failures += 1
    else:
        print("  ok    the clean fixture passes, so a firing below means something")

    broken = json.loads(json.dumps(base_master))
    broken["refusals"][0]["rule"] = "M1"
    assert_fires("a surname-only row claiming a MERGE rule", broken, base_proposal)

    broken = json.loads(json.dumps(base_master))
    broken["refusals"][0].pop("why")
    assert_fires("a refusal that states no reason", broken, base_proposal)

    broken = json.loads(json.dumps(base_master))
    broken["identities"].append(json.loads(json.dumps(broken["identities"][0])))
    assert_fires("one identity standing in two rows", broken, base_proposal)

    broken_proposal = json.loads(json.dumps(base_proposal))
    broken_proposal["proposals"][0]["grade"] = "attested"
    assert_fires("a grade above what its rung allows", base_master, broken_proposal)

    broken_proposal = json.loads(json.dumps(base_proposal))
    broken_proposal["proposals"][0]["evidence_classes"] = []
    assert_fires("a grade resting on no evidence", base_master, broken_proposal)

    # The ladder's copy in the manifest (T-0668). The card prints a rung id; if the
    # manifest can drift from GRADE_RULES without the gate noticing, 531 cards can
    # print a rung whose text is wrong, which is worse than printing no text at all.
    real = vocabulary_problems()
    if real:
        print(f"  FAIL vocabulary.ladder_rules does not agree with GRADE_RULES: {real[0]}")
        failures += 1
    else:
        print("  ok    vocabulary.ladder_rules agrees with GRADE_RULES as committed")
    saved = dict(GRADE_RULES)
    try:
        GRADE_RULES["G2c"] = ("attested", "a rung nobody ratified")
        if vocabulary_problems():
            print("  ok    a rung whose text or grade drifts from the ladder is caught")
        else:
            print("  FAIL a drifted rung was not caught")
            failures += 1
        GRADE_RULES["G9z"] = ("inferred", "a rung the manifest has never heard of")
        if any("G9z" in p for p in vocabulary_problems()):
            print("  ok    a rung the manifest is missing is named in the failure")
        else:
            print("  FAIL a missing rung was not named")
            failures += 1
    finally:
        GRADE_RULES.clear()
        GRADE_RULES.update(saved)

    # The merge rules themselves, on names rather than fixtures.
    cases = [
        ("Adams, W. H.", ("adams", ["w", "h"])),
        ("William Hanford Adams", ("adams", ["william", "hanford"])),
        ("Jno. L. Wilson", ("wilson", ["john", "l"])),
        ("Mrs. M. Frauner", ("frauner", ["m"])),
        ("Mason Sabrina A.", ("mason", ["sabrina", "a"])),
        ("John Bates Jr.", ("bates", ["john"])),
        ("BEAUMONT & SKINNER", None),
        ("Reading Room (Y. M. A.), 37 Clark, 2d story", None),
        ("Abbott", None),
        # T-1155 — a supplied letter is part of the name, an annotation is not.
        ("E. K[in]zie", ("kinzie", ["e"])),
        ("Esth[e]r M. Bailey", ("bailey", ["esther", "m"])),
        ("T[e]mple, John T.", ("temple", ["john", "t"])),
        ("[W]ade, afarvin R.", ("wade", ["afarvin", "r"])),
        ("Sam[l] Anderson", ("anderson", ["samuel"])),
        ("[?] G. Abbot", ("abbot", ["g"])),
        ("Hubbard, [Henry] G.", ("hubbard", ["g"])),
        ("Adams, Benjamin F. [died July 25, 1886, aged 86½].", ("adams", ["benjamin", "f"])),
        ("[uncertain: Abey Blankinship]", None),
    ]
    for text, want in cases:
        got = split_name(text)
        if got is not None and got[1] == []:
            got = None
        if want is None:
            ok = got is None
        else:
            ok = got == (want[0], want[1])
        print(f"  {'ok   ' if ok else 'FAIL'} split_name({text!r}) -> {got}")
        failures += 0 if ok else 1

    # ---- T-1155: THE MUTATION THAT SHIPPED -----------------------------------
    # The defect was `unmark` being one blanket delete, so the cases above are not
    # enough on their own: they would still pass if a later edit deleted a bracket
    # group and its contents in some new way that happened to leave these keys alone.
    # So run the OLD rule beside the new one and require the two to DISAGREE on every
    # supply and AGREE on every annotation. A change that goes back to discarding
    # bracket contents fails here, in a name, rather than silently in the ids.
    def discard(text):
        return MARKUP_GROUP.sub(" ", text)

    for text, want in [("E. K[in]zie", ("kinzie", ["e"])),
                       ("Esth[e]r M. Bailey", ("bailey", ["esther", "m"])),
                       ("T[e]mple, John T.", ("temple", ["john", "t"])),
                       ("[W]ade, afarvin R.", ("wade", ["afarvin", "r"])),
                       ("Sam[l] Anderson", ("anderson", ["samuel"]))]:
        got, mutated = split_name(text), split_name(discard(text))
        if got == want and mutated != want:
            print(f"  ok    {text!r} keeps its supplied letters, and discarding them "
                  f"gives {mutated} instead")
        else:
            print(f"  FAIL  {text!r} -> {got}, wanted {want}; the discarding rule gives "
                  f"{mutated}, so the supply is not being kept")
            failures += 1

    for text in ["Adams, Benjamin F. [died July 25, 1886, aged 86½].",
                 "Austin, Chamberlin, farmer [carpenter], res Illinois bet N. Clark",
                 "[?] G. Abbot", "[?]rah Fowler", "Hubbard, [Henry] G.",
                 "Dani[e]l O. [uncertain: Robian]".replace("[e]", "e"),
                 "[uncertain: Abey Blankinship]",
                 "Reading Room (Y. M. A.), 37 Clark, 2d story"]:
        if split_name(text) == split_name(discard(text)):
            print(f"  ok    {text!r} is annotation, unread or parenthesis — unchanged")
        else:
            print(f"  FAIL  {text!r} moved: {split_name(text)} against the deleting "
                  f"rule's {split_name(discard(text))}. Only a welded supply may move")
            failures += 1

    # ---- T-1004: ONE CARD, TWO MEN -------------------------------------------
    # The rule is `splits`, and it is the only thing in this file that overrules a name.
    # These four cases are it and its two edges: a reading named in a ruling leaves its
    # card and stands on an identity of its own; a reading NOT named is untouched, so the
    # rule cannot reach past its ruling; and the gate that holds a ruling to what it says
    # fires in BOTH directions — a split that stopped splitting, and an X0 whose readings
    # moved when the ruling says they did not.
    def split_bucket(splits):
        return cluster([
            {"domain": d, "record_id": rid, "normalized": name, "as_read": name,
             "evidence_class": "directory_1843", "source_id": src}
            for rid, name, d, src in (
                ("d1", "Bowen, Erastus", "directories", "fergus_1843"),
                ("d2", "Bowen, Erastus Selden", "directories", "fergus_1843"),
                ("t0", "Erastus Bowen", "residents", None))], splits)

    ids, refs = split_bucket({("directories", "d2"): {
        "rule": "X1", "off": "bowen_erastus_selden", "belongs_to": "the veterinary surgeon",
        "as_read": "Bowen, Erastus Selden", "for": "Fergus prints both men",
        "declared_in": "test"}})
    apart = [i for i in ids if i.get("held_apart_by") == "X1"]
    kept = [i for i in ids if not i.get("held_apart_by")]
    if (len(apart) == 1 and len(kept) == 1
            and {m["record_id"] for m in apart[0]["members"]} == {"d2"}
            and {m["record_id"] for m in kept[0]["members"]} == {"d1", "t0"}
            and apart[0].get("held_apart_from") == ["bowen_erastus_selden"]
            and any(r["rule"] == "X1" for r in refs)):
        print("  ok    a ruled reading leaves the card it was folded onto (X1)")
    else:
        print(f"  FAIL  the conflation ruling did not split the card: "
              f"{[(i['id'], sorted(m['record_id'] for m in i['members'])) for i in ids]}")
        failures += 1

    ids, _ = split_bucket({})
    if len(ids) == 1 and len(ids[0]["members"]) == 3:
        print("  ok    …and with no ruling the same three readings are one man again")
    else:
        print(f"  FAIL  the splitter reached past its ruling: {[i['id'] for i in ids]}")
        failures += 1

    # The gate on the ruling file itself, against a master this test builds by hand.
    def conflation_master(*rows):
        return {"identities": [
            {"id": i, "canonical_person_id": c, "held_apart_by": h,
             "appearances": [{"domain": d, "record_id": r, "as_read": a}
                             for d, r, a in apps]}
            for i, c, h, apps in rows]}

    on_card = ("id_x_a", "p1", None,
               [("residents", "p1", "Erastus Bowen"), ("directories", "e1", "Bowen, Erastus")])
    held = ("id_x_b", None, "X1", [("directories", "e2", "Bowen, Erastus Selden")])
    ruling = {"cards": [{"card": "hh_x", "person_id": "p1", "state": "split",
                         "name_as_ruled": "Erastus Bowen",
                         "second_man_in_the_layer": False,
                         "off_the_card": [{"domain": "directories", "record_id": "e2",
                                           "rule": "X1", "for": "the page prints both"}]}]}
    cases = [
        ("a ruling in force is not reported", conflation_master(on_card, held), ruling, False),
        ("a split that stopped splitting is caught",
         conflation_master(("id_x_a", "p1", None,
                            [("residents", "p1", "Erastus Bowen"),
                             ("directories", "e2", "Bowen, Erastus Selden")])), ruling, True),
        ("a card renamed out from under its ruling is caught",
         conflation_master(("id_x_a", "p1", None,
                            [("residents", "p1", "Erastus Selden Bowen")]), held), ruling, True),
        ("a second man who has since got a card is caught",
         conflation_master(on_card, ("id_x_b", "p2", "X1",
                                     [("directories", "e2", "Bowen, Erastus Selden")])),
         ruling, True),
        ("a split ruling that states no reason is caught", conflation_master(on_card, held),
         {"cards": [{"person_id": "p1", "state": "split", "off_the_card": [
             {"domain": "directories", "record_id": "e2", "rule": "X1"}]}]}, True),
        ("an X0 whose readings have moved off the card is caught",
         conflation_master(on_card, held),
         {"cards": [{"person_id": "p1", "state": "recorded", "for": "three initials",
                     "still_on_the_card": ["e2"]}]}, True),
        ("an X0 whose readings are where it says is not reported",
         conflation_master(on_card, held),
         {"cards": [{"person_id": "p1", "state": "recorded", "for": "three initials",
                     "still_on_the_card": ["e1"]}]}, False),
    ]
    for what, master_doc, doc, want_problem in cases:
        got = bool(conflation_problems(master_doc, doc))
        if got == want_problem:
            print(f"  ok    {what}")
        else:
            print(f"  FAIL  {what}: {conflation_problems(master_doc, doc)}")
            failures += 1

    # ---- T-0723: A WIFE IS NOT HER HUSBAND -----------------------------------
    # The honorific strip is right for `John Bates Jr.` and it is what folded
    # `Mrs Rufus Brown` onto `Rufus Brown`. These four cases are the rule and its two
    # edges; break R6 and the first two fail, loosen it and the last two do.
    def bucket(*rows):
        ids, refs = cluster([
            {"domain": d, "record_id": rid, "normalized": name, "as_read": name,
             "evidence_class": "directory_1843", "source_id": src}
            for rid, name, d, src in rows])
        return ids, refs

    ids, refs = bucket(
        ("d1", "Brown, Rufus B.", "directories", "fergus_1843"),
        ("d2", "Brown, Mrs. Rufus B.", "directories", "fergus_1843"),
        ("t0", "Rufus Brown", "residents", None),
        ("t1", "Mrs Rufus Brown", "residents", None))
    wife = [i for i in ids if i.get("held_apart_by") == "R6"]
    husband = [i for i in ids if not i.get("held_apart_by")]
    if (len(wife) == 1 and len(husband) == 1
            and {m["record_id"] for m in wife[0]["members"]} == {"d2", "t1"}
            and any(r["rule"] == "R6" for r in refs)):
        print("  ok    a female honorific on the husband's own name is held apart (R6)")
    else:
        print(f"  FAIL  Mrs Rufus Brown was not held apart from Rufus Brown: "
              f"{[(i['id'], sorted(m['record_id'] for m in i['members'])) for i in ids]}")
        failures += 1

    ids, _ = bucket(
        ("d1", "Gooding, Caroline", "newspapers", "papers"),
        ("d2", "Gooding, Caroline Miss", "newspapers", "papers"))
    if len(ids) == 1:
        print("  ok    a title TRAILING a woman's own forename never splits her")
    else:
        print("  FAIL  'Gooding, Caroline Miss' was split off her own card")
        failures += 1

    ids, _ = bucket(
        ("c1", "Eliza Haight", "census_1840", "census_1840_cook_county"),
        ("d1", "Haight, Mrs. Eliza", "directories", "fergus_1843"))
    if len(ids) == 1:
        print("  ok    a leading title no ONE source prints beside the bare name merges")
    else:
        print("  FAIL  Mrs Eliza Haight was split from the census's Eliza Haight on no "
              "evidence but the shape of the name")
        failures += 1

    # ---- T-0951: THE SAME PAGE, AND THE HUSBAND PRINTED IN FULL --------------
    ids, refs = bucket(
        ("d1", "Hadley, Timothy Gibson", "directories", "fergus_1843"),
        ("d2", "Hadley, Mrs. T. G.", "directories", "fergus_1843"),
        ("d3", "Hadley, Elijah W.", "directories", "fergus_1843"))
    wife = [i for i in ids if i.get("held_apart_by") == "R6"]
    if (len(wife) == 1 and {m["record_id"] for m in wife[0]["members"]} == {"d2"}
            and any(r["rule"] == "R6" for r in refs)):
        print("  ok    an initials-only honorific reaches the full forename it fits (R6)")
    else:
        print(f"  FAIL  'Hadley, Mrs. T. G.' stayed on Timothy Gibson Hadley: "
              f"{[(i['id'], sorted(m['record_id'] for m in i['members'])) for i in ids]}")
        failures += 1

    ids, _ = bucket(
        ("d1", "Hadley, Timothy Gibson", "directories", "fergus_1843"),
        ("d2", "Hadley, Mrs. T. G.", "directories", "fergus_1843"),
        ("d3", "Hadley, Thomas Gray", "directories", "fergus_1843"))
    if not any(i.get("held_apart_by") == "R6" for i in ids):
        print("  ok    …and two full forenames fitting the initials refuse it (R3)")
    else:
        print("  FAIL  R6 chose between two husbands the initials both fit")
        failures += 1

    ids, _ = bucket(
        ("d1", "Hadley, Timothy Gibson", "directories", "fergus_1843"),
        ("d2", "Hadley, Mrs. T. G.", "directories", "norris_1844"))
    if not any(i.get("held_apart_by") == "R6" for i in ids):
        print("  ok    …and no ONE source printing both still stands the rule down")
    else:
        print("  FAIL  R6 fired across two bodies — the same-page guard is gone")
        failures += 1

    ids, _ = bucket(
        ("d1", "Mason Sabrina A.", "directories", "fergus_1843"),
        ("d2", "Mrs. Sabrina Mason", "directories", "fergus_1843"))
    if len(ids) == 1:
        print("  ok    M3 still joins a woman printed with and without her title")
    else:
        print("  FAIL  R6 fired on tokens that are not the other reading's, letter for "
              "letter — the exact-match half of the rule is gone")
        failures += 1

    surname_only = cluster([{"domain": "newberry_index", "record_id": "nbi_1",
                             "normalized": "Abbott", "as_read": "Abbott",
                             "evidence_class": "finding_aid", "source_id": "s"}])
    if surname_only[0] or not any(r["rule"] == "R1" for r in surname_only[1]):
        print("  FAIL a surname-only reading was allowed to become an identity")
        failures += 1
    else:
        print("  ok    a surname-only reading becomes a refusal, never an identity")

    # ---- T-0692: A REFUSAL HAS TO BE TRUE OF THE RECORD IT REFUSES ----------
    # Each of these was filed as R1 "names no forename" before this pass, and that
    # sentence is false of every one of them. R1 is now reserved for the record that
    # genuinely prints no forename; R5 says which guard actually fired.
    # `Rev. John Mary Irenaeus St Cyr` used to stand third in this list. He is no longer
    # refused at all — T-0724 joined the particle to the surname and brought him inside
    # the cap — so his place is taken by a directory line that genuinely IS over it.
    for text, rule, must_say in [
            ("8. G. Abbot", "R5", "digit"),
            ("Enos Wra. C. jr. at A. Clyburn's", "R5", "four"),
            ("Heacock's wife and children, unnamed", "R5", "'and'"),
            ("Abbott", "R1", "no forename"),
    ]:
        _, refused = cluster([{"domain": "residents", "record_id": "p", "normalized": text,
                               "as_read": text, "evidence_class": "town_layer",
                               "source_id": None}])
        rows = [r for r in refused if r.get("record_id") == "p"]
        ok = len(rows) == 1 and rows[0]["rule"] == rule and must_say in rows[0]["why"]
        print(f"  {'ok   ' if ok else 'FAIL'} {text!r} is refused {rule} and says why"
              f" -> {rows[0]['rule'] + ': ' + rows[0]['why'][:60] if rows else 'no refusal'}")
        failures += 0 if ok else 1

    # ---- T-0692: THE COVERAGE INVARIANT ------------------------------------
    # A person record the ladder is silent about, with nothing saying why, is exactly
    # what this ticket was opened over. The gate has to notice it.
    stranded = {"counts": {"person_records": 2, "carry_a_rule": 1, "carry_no_rule": 1},
                "person_records": [{"person_id": "ghost_1", "state": "unclassified",
                                    "why": "n/a"}]}
    if any("neither ruled nor refused" in p for p in
           invariants(base_master, base_proposal, stranded)):
        print("  ok    a person the ladder never looked at is caught by the gate")
    else:
        print("  FAIL an unclassified person record was allowed through")
        failures += 1
    miscounted = {"counts": {"person_records": 9, "carry_a_rule": 1, "carry_no_rule": 1},
                  "person_records": []}
    if any("does not add up" in p for p in
           invariants(base_master, base_proposal, miscounted)):
        print("  ok    coverage that does not account for the whole layer is caught")
    else:
        print("  FAIL a partial coverage was allowed through")
        failures += 1

    rivals = cluster([
        {"domain": "d", "record_id": "1", "normalized": "John Smith",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "2", "normalized": "James Smith",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "3", "normalized": "J. Smith",
         "evidence_class": "poll_1835", "source_id": "s"},
    ])
    if not any(r["rule"] == "R3" for r in rivals[1]):
        print("  FAIL 'J. Smith' against two rival Smiths did not refuse")
        failures += 1
    else:
        print("  ok    an initial-only forename with two rivals is refused, not guessed")

    # ---- T-1120: M2 reads every initial, not just the leading one -----------
    sherman = cluster([
        {"domain": "d", "record_id": "1", "normalized": "Benjamin F. Sherman",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "2", "normalized": "B. S. Sherman",
         "evidence_class": "poll_1835", "source_id": "s"},
    ])
    crossed = [r for r in sherman[1] if r["rule"] == "R7"]
    if len(sherman[0]) == 2 and len(crossed) == 1 and crossed[0]["record_id"] == "2":
        print("  ok    a disagreeing middle initial refuses the fold (R7)")
    else:
        print("  FAIL 'B. S. Sherman' folded onto 'Benjamin F. Sherman' across the middle")
        failures += 1

    # M3's case is untouched: the middle initial is present on ONE side only.
    silent = cluster([
        {"domain": "d", "record_id": "1", "normalized": "Benjamin F. Sherman",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "2", "normalized": "B. Sherman",
         "evidence_class": "poll_1835", "source_id": "s"},
    ])
    if len(silent[0]) == 1 and not any(r["rule"] == "R7" for r in silent[1]):
        print("  ok    …and a middle initial absent on one side still merges")
    else:
        print("  FAIL 'B. Sherman' was refused for a middle initial it never printed")
        failures += 1

    # THE LETTER IS THE TEST, not the length: a directory abbreviates what a card spells.
    spelled = cluster([
        {"domain": "d", "record_id": "1", "normalized": "J. Ambrose Wight",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "2", "normalized": "Joseph A. Wight",
         "evidence_class": "poll_1835", "source_id": "s"},
    ])
    if not any(r["rule"] == "R7" for r in spelled[1]):
        print("  ok    …and `Ambrose` against `A.` is agreement, not a clash")
    else:
        print("  FAIL an abbreviated middle name was read as a different letter")
        failures += 1

    # ---- T-0843: one identity, one card ------------------------------------
    def only_cards(*rows):
        return {"identities": [{"id": i, "surname": "x", "forename": "y",
                                "merge_rules": ["M1"], "appearances": [],
                                "town_person_ids": list(cards)} for i, cards in rows],
                "refusals": []}

    empty_proposal = {"proposals": []}
    twinned = invariants(only_cards(("id_hubbard_gurdon", ["hubbard_g_s", "hubbard_gurdon"])),
                         empty_proposal, deferred={})
    if not any("one person, one card" in problem for problem in twinned):
        print("  FAIL an identity standing on two town cards did not fail the gate")
        failures += 1
    else:
        print("  ok    an identity on two town cards fails until something rules on them")

    ruled = invariants(only_cards(("id_hubbard_gurdon", ["hubbard_g_s", "hubbard_gurdon"])),
                       empty_proposal,
                       deferred={frozenset(["hubbard_g_s", "hubbard_gurdon"]):
                                 {"to": "T-0000", "why": "a stated reason"}})
    if ruled:
        print(f"  FAIL a deferral naming a ticket and a reason did not open the gate: {ruled}")
        failures += 1
    else:
        print("  ok    …and a deferral naming a ticket and a reason is what opens it")

    silent = invariants(only_cards(("id_hubbard_gurdon", ["hubbard_g_s", "hubbard_gurdon"])),
                        empty_proposal,
                        deferred={frozenset(["hubbard_g_s", "hubbard_gurdon"]): {"to": "T-0000"}})
    if not any("without a ticket or a reason" in problem for problem in silent):
        print("  FAIL a deferral that states no reason was accepted")
        failures += 1
    else:
        print("  ok    a deferral that states no reason is not a ruling")

    single = invariants(only_cards(("id_hubbard_gurdon", ["hubbard_gurdon"])),
                        empty_proposal, deferred={})
    if single:
        print(f"  FAIL one identity on one card was reported as a duplicate: {single}")
        failures += 1
    else:
        print("  ok    one identity on one card says nothing")

    different = cluster([
        {"domain": "d", "record_id": "1", "normalized": "John Smith",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "2", "normalized": "Peter Smith",
         "evidence_class": "poll_1835", "source_id": "s"},
    ])
    if len(different[0]) != 2 or not any(r["rule"] == "R2" for r in different[1]):
        print("  FAIL two different forename initials of one surname were merged")
        failures += 1
    else:
        print("  ok    same surname, different initial — two identities and a stated refusal")

    # ---- T-0724: A COMPOUND SURNAME IS ONE SURNAME -------------------------
    # The priest is the case that opened the ticket, but he is not the only one: the
    # corpus prints `Van`, `De`, `La`, `Mc` and `Von` with a space too, and every one of
    # these readings was giving away its particle to the forenames. Each `want` below is
    # a printing this project has actually read.
    for text, want in [
            ("Rev. John Mary Irenaeus St Cyr", ("stcyr", ["john", "mary", "irenaeus"])),
            ("J. M. I. St Cyr", ("stcyr", ["j", "m", "i"])),
            ("Cornelius C. Van Horn", ("vanhorn", ["cornelius", "c"])),
            ("Calvin De Wolf", ("dewolf", ["calvin"])),
            ("Dr Henry Van der Bogart", ("vanderbogart", ["henry"])),
            ("H. Van Den Bogart", ("vandenbogart", ["h"])),
            ("Joseph La Frombois", ("lafrombois", ["joseph"])),
            ("David Mc Kee", ("mckee", ["david"])),
            # THE COUNTER-CASE, and the reason the fix is a particle rule and not a
            # raised cap: `Cyr` is a different surname from `St Cyr`, and a splitter
            # that merely counted higher would have put the priest on this man.
            ("John Cyr", ("cyr", ["john"])),
            # A surname printed alone keeps its particle and stays surname-only, which
            # is a refusal one line below — never a man called `De`.
            ("De Camp", ("decamp", [])),
            # The surname-first printing takes the particle forward, not backward.
            ("St Cyr N. R.", ("stcyr", ["n", "r"])),
    ]:
        got = split_name(text)
        ok = got == (want[0], want[1])
        print(f"  {'ok   ' if ok else 'FAIL'} split_name({text!r}) -> {got}")
        failures += 0 if ok else 1

    # A TRADE IS NOT A FORENAME. Norris sets a vessel into this line, and the particle
    # rule would happily have made `St. Joseph` the man's surname and `captain schooner`
    # two of his forenames. The word before the particle is lower case, so the rule
    # stands down and the line falls back to the token count that always refused it.
    schooner = "Peterson. GPO. captain schooner St. Joseph"
    parsed, why = split_name_or_reason(schooner)
    if parsed is not None or "four" not in (why or ""):
        print(f"  FAIL a directory line with a vessel in it parsed as a man -> {parsed}")
        failures += 1
    else:
        print("  ok    a trade before the particle stands the rule down, and the line "
              "is still refused")

    particled = cluster([
        {"domain": "d", "record_id": "1", "normalized": "John Mary Irenaeus St Cyr",
         "evidence_class": "poll_1835", "source_id": "s"},
        {"domain": "d", "record_id": "2", "normalized": "John Cyr",
         "evidence_class": "poll_1835", "source_id": "s"},
    ])
    surnames = sorted(i["surname"] for i in particled[0])
    if surnames != ["cyr", "stcyr"]:
        print(f"  FAIL a St Cyr and a Cyr did not stay two surnames -> {surnames}")
        failures += 1
    else:
        print("  ok    St Cyr and Cyr are two surnames, and no identity spans both")

    particle_only = cluster([{"domain": "d", "record_id": "1", "normalized": "De Camp",
                              "as_read": "De Camp", "evidence_class": "finding_aid",
                              "source_id": "s"}])
    if particle_only[0] or not any(r["rule"] == "R1" for r in particle_only[1]):
        print("  FAIL 'De Camp' was read as a forename 'De' and minted an identity")
        failures += 1
    else:
        print("  ok    a bare compound surname is a refusal, not a man called 'De'")
    return failures


def cmd_report(master, coverage, proposal):
    print("\nidentities by the domains that name them")
    print(f"  {master['counts']['identities']} identities, "
          f"{master['counts']['appearances']} appearances, "
          f"{master['counts']['identities_in_two_or_more_domains']} in two or more domains")
    print(f"\n{'domain':18} {'read':>7} {'ids':>7} {'on a card':>10} {'unmatched':>10}")
    print("-" * 56)
    for domain, row in coverage["domains"].items():
        print(f"{domain:18} {row['names_read']:>7} {row['identities']:>7} "
              f"{row['appearances_on_an_identity_the_town_already_carries']:>10} "
              f"{row['unmatched']:>10}")
    # T-0841. The church domain's row above is two readings of four, and the report used
    # to say so nowhere. A reader counting `church 520` had no way to learn that the
    # baptismal register's 267 readings are not in it.
    print("\nchurch readings on disk the ladder does not read, and why (T-0841)")
    for name, why in sorted(CHURCH_RECORDS_NOT_READ.items()):
        print(f"  {name}")
        print(f"    {' '.join(why.split())[:96]}…")
    print("\nproposed grades against the #668 baseline "
          "(117 attested / 731 inferred / 706 projected / 848 persons)")
    for name, count in sorted(proposal["counts"]["by_grade"].items(),
                              key=lambda kv: str(kv[0])):
        print(f"  {str(name):22} {count}")
    print("  by rung: " + ", ".join(f"{k}={v}" for k, v in
                                    sorted(proposal["counts"]["by_rule"].items())))
    print(f"  proposed changes to existing people: "
          f"{proposal['counts']['proposed_changes_to_existing_people']}; "
          f"conflicts: {proposal['counts']['conflicts']}")



def cmd_coverage(ladder):
    """The T-0692 report: who the ladder has ruled on, and who it has not."""
    counts = ladder["counts"]
    print("\nWHO THE LADDER HAS RULED ON")
    print(f"  person records in data/residents/          {counts['person_records']:>6}")
    print(f"  carrying a ladder_rule on the card         {counts['carry_a_rule']:>6}")
    print(f"  carrying none                              {counts['carry_no_rule']:>6}")
    print("\n  OF THOSE, BY WHAT THE LADDER CAN SAY")
    for name, block_ in ladder["states"].items():
        if name == "rule_on_the_card":
            continue
        print(f"    {name:<26} {block_['people']:>6}")
    print("\n  A RUNG ALREADY RULED AND NEVER WRITTEN ONTO THE CARD")
    for rule, n in counts["proposed_not_written_by_rule"].items():
        print(f"    {rule:<6} {GRADE_RULES[rule][0] or 'no proposal':<18} {n:>6}   "
              f"{GRADE_RULES[rule][1][:58]}")
    if not counts["proposed_not_written_by_rule"]:
        print("    none — tools/spend_ladder_rungs.py has spent them (T-0720)")
    print("\n  RULED, AND THE RUNG DISAGREES WITH THE CARD — the owner's conflict list, "
          f"{counts.get('on_the_owners_conflict_list', 0)} people")
    for rule, n in counts.get("ruled_but_disputed_by_rule", {}).items():
        print(f"    {rule:<6} {GRADE_RULES[rule][0] or 'no proposal':<18} {n:>6}   "
              f"{GRADE_RULES[rule][1][:58]}")
    print("\n  THE LADDER HAS NEVER LOOKED — "
          f"{counts['the_ladder_has_never_looked']} people, each with its reason")
    for row in ladder["person_records"]:
        if row["state"] in ("proposed_not_written", "rule_on_the_card",
                            "ruled_but_disputed"):
            continue
        tag = row.get("refusal_rule") or row["state"]
        print(f"    {row['person_id']:<28} {str(row['name'])[:34]:<36} "
              f"{row['grade_on_the_card'] or '-':<10} {tag}")
        print(f"      {row['why']}")
    print("\n  sources cited by the people with no rung, most-cited first")
    tally = Counter()
    for row in ladder["person_records"]:
        tally.update(row["sources"])
    for source, n in tally.most_common(10):
        print(f"    {source:<44} {n:>6}")
    print(f"\n  the full list, one person per line: "
          f"{LADDER_COVERAGE.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--coverage", action="store_true",
                        help="who the ladder has ruled on and who it has not (T-0692)")
    parser.add_argument("--write-vocabulary", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 1 if cmd_self_test() else 0
    if args.write_vocabulary:
        return cmd_write_vocabulary()
    if args.check:
        return 1 if cmd_check() else 0
    if args.build or args.report or args.coverage:
        master, coverage, proposal, ladder = cmd_build(write=args.build)
        if args.report:
            cmd_report(master, coverage, proposal)
        if args.coverage:
            cmd_coverage(ladder)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
