#!/usr/bin/env python3
"""Norris's *General Directory and Business Advertiser of the City of Chicago for
the Year 1844* — the directory proper, read entry by entry (T-0555).

`--build` reads the committed page text under
`data/research/directories/text/norris_1844_leaf_*.txt` and writes
`data/research/directories/claims/norris_1844_directory_entries.json`.
`--check` rebuilds in memory and compares, so a hand-edit of the generated file
is caught the way `read_voter_lists.py` catches one.

THE STRUCTURE IS THE INDENT. Norris sets every entry flush left and turns the
long ones in about half an inch. The committed text keeps that: a turned line
carries two leading spaces, taken off the word coordinates of the scan, so the
entry boundaries survive the trip from image to text and can be checked by eye.

1844 IS NINE YEARS LATE. Nothing here is an 1835 fact. Every claim carries
`describes_date: "1844"`, and the crosswalk is the only place a name in this
volume is allowed to touch a person in the 1835 scene.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
OUT = os.path.join(ROOT, "data/research/directories/claims/norris_1844_directory_entries.json")

# The directory proper: leaves 31-75 of the scan, printed pages 21-65.
FIRST_LEAF, LAST_LEAF, LEAF_TO_PRINTED = 31, 75, -10

# Prose inside the directory pages, skipped by line number because there is no
# rule that separates it from an entry — it is the compiler talking, not a name.
SKIP = {
    31: range(1, 26),   # the title band and Norris's REMARKS on abbreviations
    72: range(18, 28),  # the ADDENDA notice
    75: range(15, 30),  # Norris's own General Intelligence Agency card
}
# The addenda — "names accidentally omitted above" — begins mid-leaf 72.
ADDENDA_FROM = (72, 28)

FIRM = re.compile(r"^[^,]{0,40}\s&\s|&\s*Co\b|\bBrothers\b", re.I)
TITLES = {"mrs", "miss", "mr", "dr", "capt", "col", "rev", "gen", "maj", "jr", "sr", "sen"}
# Norris's own abbreviations, printed in his preface: h for house, r for residence,
# b for between. Two things had to be said about them that were not (T-0987 stretch 5):
#
#   `(?<!-)` — the compositor's HYPHEN is not a word boundary this rule may cut at.
#   `\b` holds on the far side of one, so `boarding-house` read as a trade ending in
#   a hyphen and an address beginning "house …".
#
#   THE SINGLE LETTERS ARE LOWER CASE AND A MAN'S INITIAL IS NOT. The whole pattern
#   was compiled `re.I`, so `h`, `r` and `b` matched the capital initials this volume
#   sets everywhere — and the address began at the first of them. `Adams, R. E. W,
#   physician, corner of Clark and Lake streets` cut at the `R.` of the man's own
#   name and left him no trade at all and an address of "E. W, physician, corner of
#   Clark and Lake streets"; `Beer, Adam, shoemaker, at J. B. Mitchell's` cut at the
#   `B.` of his employer and read a trade of "shoemaker, at J". 271 of the 2,073
#   entries were cut at an initial. The abbreviation WORDS stay case-blind (`res`,
#   `Res`); the three single letters do not.
#
#   AND `b` IS NOT ONE OF THEM. It stands for BETWEEN — Norris says so himself, in
#   the REMARKS this pattern was built from: "b stands for between; Rand for
#   Randolph; Mad for Madison; Wash for Washinglon". Between is a qualifier on the
#   street already named, not a word that opens a place, and reading it as a starter
#   cut 175 entries in the middle of their own location. See PLACE_B_AS_PLACE below.
PLACE = re.compile(r"\b(?<!-)(?:(?i:house|residence|res|boards|bds)|[hr])\.?\s")

# …AND `House` IS ALSO THE NAME OF A BUILDING, WHICH THIS RULE CANNOT SEE (T-1021,
# found in passing and named here so the next run does not rediscover it). The word
# is matched case-blind, so a capitalised `House` standing inside a hotel's proper
# name opens the address at the wrong word. It is four entries, all of them printed:
#
#     n1844_e0402  Cook, Geo. barkeeper, at American Temperance House res same
#     n1844_e0849  Hisiley, Geo. House of Entertainment, S. Water st.'near Lasalle st
#     n1844_e1629  Skinner & Smith, Mansion House. 6G Lake street
#     n1844_e1764  Thomas & Wheelock, Washington Coffee House, Tremont House
#
# Norris prints his abbreviation lower case — `house Adams st.` — which is the same
# tell the single letters already use, so the repair is narrow. It is a separate
# ruling about the PLACE rule and is not made here.

# …AND THE SUPERSEDED PATTERN IS KEPT SO THE RULE CAN BE RE-MEASURED, NOT ASSERTED
# (T-1022). The case rule above landed inside another ticket's stretch and was never
# priced, so the count that mattered — how many entries' READING it moves — was
# carried as a guess. `--self-test` now re-reads the whole volume through this
# pattern and prices it against the committed one, which is the only form of the
# claim that cannot go stale:
#
#   185  entries print an upper-case `H.` or `R.` token at all
#   140  of them have that capital as the FIRST place-shaped token in the line —
#        usually inside the NAME, which the split never cuts at, so the reading stands
#    45  entries have their occupation or address actually MOVE, and all 45 are the
#        defect exactly: under the case-blind pattern each one's address began at a
#        one-letter initial. There is no other reason an entry moves, which is what
#        makes every one of the 45 a repair rather than a trade.
#
# THE NUMBERS WERE 294 / 275 / 95 UNTIL T-1114, and they fell because this pattern
# stopped carrying `b`, not because the rule changed. The old superseded pattern
# differed from the committed one in TWO things — case, and whether `b` opens a place
# — so it priced neither cleanly, and half its moves were capital `B.` initials that
# the between rule now accounts for on its own. Each pattern below differs from
# `PLACE` in exactly one thing, and prices exactly that.
#
# Downstream, `crosswalk_norris_1844.py` carries `could_carry_address` 82 → 81. The
# single match that stopped carrying one is Joseph Bradley (n1844_e0186, `clerk, at
# W. H. Adams & Co.'s`), whose case-blind "address" was `H. Adams & Co.'s` — the tail
# of his employer's firm and never a place. The lost match is a false one; nothing a
# resident could stand on was given up. `could_carry_occupation` holds at 59 and
# every other crosswalk count is unchanged.
#
# …and since T-1114 this pattern differs from the committed one in CASE ALONE. It
# carried `b` as well, from the reading that `b` is a place mark; it is not, and that
# is priced separately by PLACE_B_AS_PLACE below. A superseded pattern that differs in
# two things prices neither, so the `b` came out and the count was re-measured: 45.
PLACE_CASE_BLIND = re.compile(r"\b(?:h|house|res|residence|r|boards|bds)\.?\s", re.I)
CASE_RULE_MOVES = 45   # …and the price, held by --self-test against a re-read

# `b` IS BETWEEN, AND BETWEEN IS NOT A PLACE (T-1114).
#
# The pattern above opened an address at a lowercase `b`, on the reading that Norris's
# three abbreviations are all place marks. Two of them are: `h` is house and `r` is
# residence. The third is not, and the book says so on the first page of the directory
# proper, in the REMARKS this whole band was read from:
#
#     "Abbreviations, which occur only in a very few words, will readily be
#      understood; b stands for BETWEEN; Rand for Randolph; Mad for Madison …
#      The word street, in some instances, is omitted. The place of business
#      uniformly precedes the residence."   — leaf 31, printed page 21
#
# Between qualifies the street ALREADY NAMED. Cutting at it therefore severs a location
# from its own street and hands half of each to a different field:
#
#     Wheeler, laborer, Washington st, b Wells and Franklin sts
#        was  occupation "laborer, Washington st"   address "b Wells and Franklin sts"
#        now  one location, entire, and no address at all
#
# 494 lowercase `b` tokens stand in this volume and every one of them is followed by a
# street name — `Clark` 61 times, `Lake` 52, `Wolcott` and `Cass` 23 each. The two lines
# in which a `b` precedes `at` (`Horton, B. at Mrs. Boyer's`) print it CAPITALISED,
# because it is a man's initial, and the case rule above already keeps those out.
#
# THE PRICE, RE-MEASURED BY `--self-test` AGAINST THE SUPERSEDED PATTERN: 175 entries
# move, and each one moves for this defect and no other — under the old pattern every
# one of the 175 had an address beginning at `b `, which is asserted rather than
# described. 164 of them lose an address that was only ever the tail of a location and
# keep it whole in the trade line; the other 11 GAIN the residence the old cut buried,
# because Norris had set a real `res` or `house` further along the line and the `b`
# reached it first:
#
#     Bristol, tailor, Clark st. b Lake and Water sts. res Illinois st. b Clark …
#        was  address "b Lake and Water sts. res Illinois st. b Clark and Dearborn sts"
#        now  address "res Illinois st. b Clark and Dearborn sts" — his house, alone
#
# Those 11 are the plainest possible demonstration of the preface's other sentence: the
# place of business uniformly precedes the residence, and the old rule read the join.
PLACE_B_AS_PLACE = re.compile(r"\b(?<!-)(?:(?i:house|residence|res|boards|bds)|[hrb])\.?\s")
B_RULE_MOVES = 175              # …and 11 of them recover a residence, asserted below
B_RULE_RECOVERS_ADDRESS = 11


# THE STREET NORRIS PRINTS WITH NO PLACE-ABBREVIATION BEFORE IT (T-1113).
#
# `PLACE` cuts a trade from an address at Norris's own `h`/`res`/`b`. Where he sets
# none there is nothing to cut at, and the whole tail stays in `occupation` — 304 of
# the 2,073 entries name a street that way, because a shop's address IS its trade line
# ("grocer, 175 Lake st"). That volume-scale question is not this rule and is filed
# separately; what is repaired here is the entry where the street reached the NAME.
#
# The forename walk takes a capitalised token while it has fewer than three, so a
# street set straight after the surname is read as a third forename and the trade then
# begins at the bare word `st`:
#
#     Brown, S. B. Ohio st. b Cass and Rush sts   →  given "S. B. Ohio", trade "st"
#     Intelligence Office, Clark st. opposite …   →  given "Clark",     trade "st. …"
#
# THE TEST IS THE WORD THAT FOLLOWS, NOT A LIST OF STREETS. A capitalised token with a
# street designator immediately after it is the street's name — Norris has no forename
# that a `st`, `street` or `avenue` follows. Holding a gazetteer here would fail on the
# scanner's spellings (`Wash.`, `Frank.`, `Lasatte`) and would have to be kept in step
# with the street layer; the designator is set by the same compositor as the street and
# travels with it. A ONE-LETTER token is exempt: `Geo. W. Water street` sets an initial
# before the street, and `W.` is as likely the man's as the street's West — see the
# residual noted with n1844_e0807 below.
#
# It moves seven entries and all seven are the defect. `--self-test` re-reads the whole
# volume with the rule off and prices it, the same way the case rule is priced.
STREET_DESIGNATOR = re.compile(r"^(?:st|street|streets|sts|av|ave|avenue|alley|road"
                               r"|lane|court)$", re.I)
STREET_RULE = True          # …turned off by --self-test, to re-read and price it


def street_ahead(toks, i: int) -> bool:
    """True when toks[i] is a street's NAME — capitalised, more than one letter, and
    the very next token is a designator Norris only ever sets after a street."""
    if not STREET_RULE or i + 1 >= len(toks):
        return False
    tok = toks[i].strip(".,'\"")
    if len(tok) < 2 or not tok[:1].isupper() or tok.lower() in TITLES:
        return False
    return bool(STREET_DESIGNATOR.match(toks[i + 1].strip(".,;:'\"")))


# …AND THE SEVEN, WITH WHAT EACH READS AFTER THE RULE. The second hand — Kim Torp's
# independent transcription, compared entry by entry in
# data/research/directories/second_readings/norris_1844_genealogytrails.json — prints
# the same street in every one of them, so the street is the printed page's and not
# this scan's OCR.
STREET_IN_FORENAME = {
    # T-1114 added the fourth column: the street these entries were named for is now
    # read out of the trade line into place_of_business, which is where five of the seven
    # keep it. `Water street` is not a trade and never was.
    # id:          (given,      occupation,  place_of_business,                  address)
    "n1844_e0220": ("S. B", None,
                    "Ohio st. b Cass and Rush sts", None),
    "n1844_e0276": ("Dennis S", "Lake Street House",
                    "135 Lake st (Sec card)", None),
    "n1844_e0328": ("Thos", None,
                    "Wolcott st. b Illinois and Indiana sts", None),
    "n1844_e0567": ("George A", None,
                    "Clark st market", "res Farmers' Exchange"),
    "n1844_e0677": ("Mrs", None,
                    "Wash. st. b Frank, and Market sts", None),
    "n1844_e0807": ("Geo. W", None,
                    "Water street", "house Wabash st"),
    "n1844_e1993": (None, None,
                    "Clark st. opposite Saloon, over J; B. F. Rus sell's Land Office",
                    None),
}

# WHAT IT COSTS DOWNSTREAM, MEASURED (T-1113). `consolidate_resident_evidence.py`
# gathers an identity on surname plus forenames, so a street inside the forename minted
# a person: `id_brown_s_b_ohio` stood beside the Simon B. Brown whom Fergus 1843 puts
# on Ohio between Cass and Rush — the same street the phantom was named for. Five such
# identities fold into the person they were always part of (Brown, Cady, Chapman, Ellis,
# Hart, and the Intelligence Office into the 1843 intelligence office at 38 Clark), and
# `n1844_e0677` becomes an R1 refusal, because `Galvin, Mrs.` names no forename once the
# street is off it. identities 6,817 → 6,812, appearances 10,546 → 10,545. The 1844
# crosswalk is unmoved — none of these twelve entries reaches an 1835 resident, and
# `could_carry_address` holds at 81.

# THE RESIDUAL, STATED RATHER THAN HIDDEN (n1844_e0807). `Hart, Geo. W. Water street,
# house Wabash st` reads a forename of "Geo. W" and a trade line beginning "Water
# street", and the `W.` may belong to either side: George W. Hart, or the West Water
# street this volume names a dozen times. Both hands print it the same, so no reading
# settles it. The rule leaves the initial with the man because that is where the walk
# already had it; what it fixes there is the street inside the name, not the initial.


# THE STREET THAT IS THE FIRM'S AND NOT THE MAN'S — REFUSED, WITH THE REASON (T-1113).
#
# Five entries print a street after `of <firm>` or `at <employer>'s` and no place
# abbreviation anywhere. Reading that street into `address` would be the easy repair
# and a false one: `of B. & Sherman, Dearborn street` is where the PARTNERSHIP stands,
# not where David Ballentine sleeps, and this project's `address` is a residence —
# Norris marks one with `h`, `res` or `b` and marks none of these. A business street
# landed on a resident's card as a home is a provenance defect that no downstream
# reader could see, so all five stay refused and say why here and on the claim.
#
# THE SIXTH OF THEM IS THE PRINTED LINE RUNNING OUT. `Magie, H. H. of H. H. M. & Co.
# house` ends AT the abbreviation with no street after it. The ticket expected that to
# need a page-image read; it does not. The second hand typed the same line from a
# different copy of the printed book and ends at the same word — the comparison scores
# the pair identical, ratio 1.0 — so the shortfall is the printed page's, not this
# scan's, and there is no street on the page to go and read.
ADDRESS_REFUSED = {
    "n1844_e0062": ("firm_address",
                    "of B. & Sherman: Dearborn street bet Kinzie and Michigan is the "
                    "partnership's address, and Norris sets no h/res/b for the man"),
    "n1844_e0817": ("firm_address",
                    "of H. & Shur: South Water st is the partnership's address, and "
                    "Norris sets no h/res/b for the man"),
    "n1844_e1206": ("printed_line_short",
                    "the line ends at the abbreviation — 'of H. H. M. & Co. house' "
                    "with no street after it. The second hand reads it identically "
                    "off a different copy (ratio 1.0), so the page prints no street"),
    "n1844_e1470": ("employer_address",
                    "at B. W. Raymond's: 122 Lake st is the employer's shop, and "
                    "Norris sets no h/res/b for the man"),
    "n1844_e1858": ("employer_address",
                    "clerk at J. B. Busch's: Clark st is the employer's premises, and "
                    "Norris sets no h/res/b for the man"),
}
ADDRESS_REFUSED_NOTE = (
    "address is a RESIDENCE in this reading, and Norris marks one with h or res. "
    "This entry names a street with no such mark, so the street is not read into "
    "address; where the street is the place the trade is carried on it is read into "
    "place_of_business instead (T-1114). See tools/read_norris_1844.py, ADDRESS_REFUSED.")


# THE PLACE OF BUSINESS IS ITS OWN FIELD, AND NORRIS SAYS WHICH PLACE IT IS (T-1114).
#
# THE FIELD QUESTION, DECIDED FIRST. T-1113 ruled that a street with no dwelling mark is
# not a residence and must not land in `address`, and refused five entries on it. That
# ruling is right and it left 468 entries naming a street with nowhere to put it — a
# shop's address IS its trade line, and Norris prints no `h` or `res` in front of one.
# The question this ticket had to settle is whether the reading should hold a second
# field for that place, and the book settles it in the same sentence that settles `b`:
#
#     "The place of business uniformly precedes the residence."   — leaf 31
#
# So the unmarked street is not an unclassified location the reading has to guess at.
# It is the PLACE OF BUSINESS, named by the compiler's own convention, and it is a
# different kind of fact from a residence: one is where a man could be found trading,
# the other where he slept. They are therefore two fields and not one, and `address`
# stays what T-1113 made it. `place_of_business` is `documented` in the same sense the
# rest of this reading is — it is what the printed line says — and nothing in it may
# ever be promoted into `address`, because the preface distinguishes them and this
# reading is not entitled to collapse the distinction.
#
# AND A FIRM'S STREET IS THE FIRM'S. The ticket asked whether it belongs on a partner's
# card. It does not, and the new field does not change that: `n1844_e0062` reads
# `of B. & Sherman, Dearborn street bet Kinzie and Michigan`, whose place_of_business is
# where the PARTNERSHIP stands. ADDRESS_REFUSED already refuses it as his residence;
# place_of_business says whose place it is without claiming it is his home. The five
# refusals are unchanged and still carry their reason.
#
# THE CUT — AN OPENER, NOT A GAZETTEER. The place begins at the first token that can
# only open one, taken at a boundary the compositor's own comma marks:
#
#   * a house number followed by a capitalised word  — "156 Lake st"
#   * `corner` / `cor` / `near` / `opposite` / `opp`  — "corner of Lake and Wells sts"
#   * a street: an optional direction (`N.`, `So.`, `North`), a capitalised name of
#     more than one letter, and a designator — "Clark st", "N. Water street"
#   * …or that same street with the designator ABSENT, which the preface warns of
#     ("The word street, in some instances, is omitted") and which is only read when a
#     direction stands in front of it and a qualifier behind: "S. Water, b Clark and
#     Dearborn". Both fences are needed; without them "Mansion House" reads as a street.
#
# TWO GUARDS, EACH PUT THERE BY AN ENTRY THAT BROKE WITHOUT IT:
#
#   `after_street` — what follows the designator may not be a fresh capitalised word.
#   `Lake Street House, 135 Lake st` is a HOTEL named after a street, and without this
#   the whole line reads as a location and Dennis S. Brainard loses his trade. With it
#   the cut falls at the house number, where it belongs: trade "Lake Street House",
#   place "135 Lake st".
#
#   the walk back — the comma is where the cut is LOOKED for, not where the place must
#   start. `physician, office Clark street, opposite City Hotel` has no comma before
#   `Clark`, so the scan first sees `opposite` and would cut a location in half again.
#   From an accepted opener the rule walks back to the earliest street whose own tail
#   reaches it, and takes that instead: trade "physician, office", place the whole of
#   "Clark street, opposite City Hotel".
#
# THE PRICE, RE-MEASURED BY `--self-test` WITH THE RULE OFF: 503 entries carry a
# place_of_business, and their `occupation` is the trade alone where it was the trade and
# the location run together. No entry gains or loses an `address`; the rule reads only
# the trade line. 20 of the 498 have no trade at all in front of the place, which is
# Norris printing a location and nothing else, and those read an occupation of null.
#
# WHAT IS STILL REFUSED, COUNTED RATHER THAN HIDDEN. About 250 further entries name
# something place-shaped that this rule will not cut, and they stay whole in
# `occupation` on purpose. Three kinds, all seen: the scan's own damage inside the
# street (`Clark st_.`, `betweeri`, `c W. Water`), a line with no comma anywhere to cut
# at (`laborer 3d ward south of Jackson st`), and a ward or a landmark standing where a
# street would (`2d ward, North of Jackson st`). Each would need either a gazetteer —
# refused above, and by T-1113 before it — or a page-image read, and a wrong cut here
# writes a false trade onto a card. They are left for the reading that can see the page.
PLACE_OF_BUSINESS_RULE = True      # …turned off by --self-test, to re-read and price it
PLACE_OF_BUSINESS_ENTRIES = 503
PLACE_OF_BUSINESS_NOTE = (
    "the place the trade is carried on, read out of the trade line Norris prints it "
    "in. His preface: 'The place of business uniformly precedes the residence.' It is "
    "NOT a residence and may not be read into address. See tools/read_norris_1844.py, "
    "PLACE_OF_BUSINESS_RULE.")

DESIGNATOR = re.compile(r"^(?:st|street|streets|sts|av|ave|avenue|alley|road|lane|court)$",
                        re.I)
DIRECTION = re.compile(r"^(?:n|s|e|w|no|so|north|south|east|west)$", re.I)
PLACE_OPENER = re.compile(r"^(?:corner|cor|near|opposite|opp)$", re.I)
HOUSE_NUMBER = re.compile(r"^\d+$")
# Words that may stand inside a location between its street and a later opener.
PLACE_PARTICLE = {"b", "bet", "between", "near", "cor", "corner", "opposite", "opp",
                  "and", "of", "the", "no", "nos"}
# …and the narrower set the omitted designator is read behind: a qualifier that can
# only follow a street. `and` is not one of them — it joins two streets in a corner.
STREET_QUALIFIER = {"b", "bet", "between", "near", "cor", "corner", "opposite", "opp"}


def _bare(tok: str) -> str:
    return tok.strip(".,;:'\"()-").lower()


def _bp_capitalised(tok: str) -> bool:
    s = tok.strip(".,;:'\"()-")
    return bool(s) and s[:1].isupper()


def _comma_closed(tok: str) -> bool:
    """The compositor's comma, whatever punctuation he set after it."""
    return tok.rstrip(".;:'\"()").endswith(",")


def after_street(toks, j: int) -> bool:
    """What follows a street designator may not be a fresh capitalised word — that is
    a name the street is part of ("Lake Street House"), not a location."""
    if j >= len(toks):
        return True
    if toks[j].startswith("("):
        return True     # "(See card)" — Norris's cross-reference to an advertisement
    b = _bare(toks[j])
    if not b or b[:1].isdigit() or DIRECTION.match(b):
        return True
    return not _bp_capitalised(toks[j])


def street_at(toks, i: int) -> int:
    """Index just past the street beginning at toks[i], or 0 if none begins there."""
    j = i
    if DIRECTION.match(_bare(toks[j])) and j + 1 < len(toks) and _bp_capitalised(toks[j + 1]):
        j += 1
    s = toks[j].strip(".,;:'\"()-")
    if len(s) < 2 or not s[:1].isupper() or _bare(toks[j]) in TITLES:
        return 0
    if j + 1 < len(toks) and DESIGNATOR.match(_bare(toks[j + 1])):
        return j + 2
    # The designator Norris's preface says he sometimes omits — read only behind a
    # direction and in front of a qualifier, which is what keeps a name out.
    if j > i and j + 1 < len(toks) and _bare(toks[j + 1]) in STREET_QUALIFIER:
        return j + 1
    return 0


def place_opens_at(toks, i: int) -> bool:
    if PLACE_OPENER.match(_bare(toks[i])) and i + 1 < len(toks) and (
            _bp_capitalised(toks[i + 1]) or _bare(toks[i + 1]) == "of"):
        return True
    s = toks[i].strip(".,;:'\"()")
    if HOUSE_NUMBER.fullmatch(s) and i + 1 < len(toks) and _bp_capitalised(toks[i + 1]):
        return True
    end = street_at(toks, i)
    return bool(end) and after_street(toks, end)


def split_place_of_business(occupation):
    """(trade, place_of_business) — the place read out of the trade line, or None."""
    if not PLACE_OF_BUSINESS_RULE or not occupation:
        return occupation, None
    toks = occupation.split()
    for i in range(len(toks)):
        if i and not _comma_closed(toks[i - 1]):
            continue
        if not place_opens_at(toks, i):
            continue
        for k in range(i):
            end = street_at(toks, k)
            if end and end <= i and after_street(toks, end) and all(
                    _bare(t) in PLACE_PARTICLE or _capitalised(t) or not _bare(t)
                    or _bare(t)[:1].isdigit() or DESIGNATOR.match(_bare(t))
                    or DIRECTION.match(_bare(t)) for t in toks[end:i]):
                i = k
                break
        return (" ".join(toks[:i]).strip(" ,.") or None,
                " ".join(toks[i:]).strip(" ,.") or None)
    return occupation, None

# FIRM OR PERSON IS DECIDED ON THE LEADING TOKENS, NOT ON THE FIRST COMMA (T-1013).
#
# The first version of this test read `FIRM` against the text before the first
# comma. That catches the style with no comma in it — `Sicar & Co. groceries and
# boarding house` — and misses the INVERTED style this volume uses constantly,
# where the surname is set first so the firm files under its alphabet:
#
#     Jones, B. & Co. dry goods and groceries, S. Water, b Clark and Dearborn
#
# Before the comma stands `Jones`, so thirty entries of that shape were read as
# people, and the firm filter in `crosswalk_norris_1844.py` — which exists so a
# company is never matched to a resident of 1835 — never saw them.
#
# THE RULE IS NOT "THE LINE CONTAINS `& Co.`". 124 entries carry that string and
# most of them are people: `Bradley, Joseph, clerk, at W. H. Adams & Co.'s` is a
# clerk naming his employer, and `Burley, A. G. of A. G. B. & Co.` is a partner
# giving his residence. What separates them is WHERE the marker stands. Norris
# sets the name first and the trade after it, so walk the leading tokens and stop
# at the first plain lower-case word (the trade has started) or at `of` (the
# partnership preposition, which can only follow a man's own name). A firm marker
# inside that prefix is a firm; the same marker after it belongs to somebody
# else's firm.
#
# The prefix is also the firm's NAME, so the two readings cannot disagree.
OF_STOP = re.compile(r"(?:^|[^A-Za-z])of(?![A-Za-z0-9])", re.I)
# Lower-case words that are still part of a name, not the start of a trade.
NAME_PARTICLES = {"and", "the", "de", "du", "van"}


def firm_name(prefix):
    """A firm's name ends where its marker does: the ampersand and the partner
    after it. Norris sets the address straight on — `Clyburn & Hovey, Clark st.
    b Lake and Water` — so a name that ran to the end of the prefix would take
    the street with it."""
    for i, tok in enumerate(prefix):
        if tok.startswith("&"):
            return prefix[:i + 2]
    return prefix


def name_prefix(head):
    """The leading run Norris sets before the trade — the name, however styled."""
    keep = []
    for tok in head.split():
        if OF_STOP.search(tok):
            break
        bare = tok.strip(".,'\"")
        if bare.islower() and bare not in NAME_PARTICLES:
            break
        keep.append(tok)
    return keep


# THE SCANNER WELDS `of` ONTO ITS NEIGHBOUR, AND THEN THE STOP WORD IS NOT A WORD.
#
# Three entries of the partner-residence shape lost the space around `of`, so the
# prefix walk above would run straight past the preposition, reach the firm marker
# and read a man as his own company. Two of them the boundary-insensitive OF_STOP
# catches on its own, because what follows `of` is not a letter:
#
#     Eddy, Ira B.-of Eddy & Co. res Michigan avenue
#     Smith, George, of'G. S. & Co. res City Hotel
#
# The third is character damage rather than a lost space — `ofJ5.` for `of B.` —
# and no rule about word boundaries can see it. It is repaired here on the same
# terms as the forename repairs below (T-0695): the reading moves, the quote and
# `as_printed` keep the damage, and the row cites the second hand that read the
# same line off the printed page. Widening OF_STOP to swallow `ofJ5` would also
# swallow every real word beginning in those two letters, which is why this is a
# table of named entries and not a looser regex.
WELDED_OF = [
    {"surname": "Raymond", "as_read": "ofJ5.", "reading": "of B.",
     "second_reading": "Raymond, B.W. of B.W.R. & Co., h Wash. b Clark & Lasalle",
     "file": "1844dir2.txt", "line": 350},
]


# THE SCANNER'S AMPERSAND, AND THE SEVEN FIRMS THAT READ AS MEN (T-1021).
#
# `FIRM` needs a real `&`. archive.org sets this volume's ampersand as `<fc`, `6c`
# or `it` in seven entries, so the test never fires and each reads as a man whose
# surname is the whole partnership — seven Lake, Water and Clark street TRADES,
# with printed addresses, filed under a name no compositor set:
#
#     Ballentine <fc Sherman, dry goods and groceries, 122 Lake street
#     Bowen 6c Cole, dry goods and groceries, 66 Lake street
#     Bracken it Tuller, dry goods and groceries, 161 Lake st
#     Crauer <fc Sanser, builders, Clark st. b Randolph and Michigan sts
#     Gould it Dodge, ball alley and grocery, South Water st. b State and Dearborn
#     Hamilton <fc White, dry goods and grocery store, 139 Lake st
#     Skinner 6c .Smith, Mansion House. 6G Lake street
#
# T-1018 REFUSED them rather than damage them — capping the comma-derived name at
# the prefix would have truncated `Bowen 6c Cole` to `Bowen` and minted a man who
# is not in the book — and left the ruling to this ticket. Here it is made.
#
# THE RULING IS THE BOOK'S OWN, NOT THIS TOOL'S GUESS. Norris prints every one of
# the seven partnerships a SECOND time, in a partner's own entry or a clerk's, and
# on those lines the scanner set the ampersand correctly:
#
#     n1844_e0062  Ballentine, David, of B. & Sherman, Dearborn street bet Kinzie…
#     n1844_e0167  Bowen, Erastus, of B. & Cole, house Michigan avenue
#     n1844_e0179  Bracken, John, of Bracken & Tuller, res Wabash avenue
#     n1844_e1555  Sanser, John W. of Cruver & S. house cor Clark and Michigan sts
#     n1844_e0507  Dodge, Martin, of Gould & Dodge, res N. Gould's
#     n1844_e0783  Hamilton, Robert P. of H. & White, res T. E. Hamilton's
#     n1844_e1654  Smith, J. F. of Skinner & S., Mansion House
#
# So the question each row answers is not "is this a firm" — the volume says it is,
# twice — but "which character did the compositor set", and the second hand (Kim
# Torp's transcription, cited by file and line) answers that off the printed page.
# Where SHE disagrees with this reading she is quoted in `second_hand_disagrees`
# and nothing here is moved to match her: Crauer/Cruver is a SURNAME disagreement
# this repair does not touch, and it stands unresolved.
#
# THE TRAP, AND WHY THIS IS A TABLE. `it` is an English word and `6c` is how this
# scanner sets `&c.` — `Surdam. S. J. stoves, &c. 132 Lake st`. A rule loose enough
# to read those three tokens as ampersands wherever they stand would weld `stoves
# it` into a partnership, so this is a table of NAMED SPANS, exactly as WELDED_OF
# above is a table and not a wider OF_STOP. It touches seven entries and can touch
# no eighth, which `--self-test` asserts from both ends: each span matches exactly
# one entry, and any entry the `Name <conj> Name` SHAPE still reaches with no row
# here stays a T-1018 refusal and fails the OVERRUN_CLASSES ratchet.
#
# The reading moves and the quote keeps the damage, the standing convention. One
# row lifts a second character with the ampersand and says so.
CONJ_AMPERSAND = [
    {"span": "Ballentine <fc Sherman", "reading": "Ballentine & Sherman",
     "as_read": "<fc", "printed_page": 22,
     "same_volume": ("n1844_e0062", "Ballentine, David, of B. & Sherman, Dearborn "
                     "street bet Kinzie and Michigan"),
     "second_reading": "Ballentine & Sherman, dry goods & groceries, 122 Lake st",
     "file": "1844directory.txt", "line": 88, "second_hand_disagrees": None},
    {"span": "Bowen 6c Cole", "reading": "Bowen & Cole",
     "as_read": "6c", "printed_page": 25,
     "same_volume": ("n1844_e0167", "Bowen, Erastus, of B. & Cole, house Michigan avenue"),
     "second_reading": "Bowen & Cole, dry goods & groceries, 66 Lake st",
     "file": "1844directory.txt", "line": 196, "second_hand_disagrees": None},
    {"span": "Bracken it Tuller", "reading": "Bracken & Tuller",
     "as_read": "it", "printed_page": 25,
     "same_volume": ("n1844_e0179", "Bracken, John, of Bracken & Tuller, res Wabash avenue"),
     "second_reading": "Bracken & Tuller, dry goods and groceries, 161 Lake st",
     "file": "1844directory.txt", "line": 208, "second_hand_disagrees": None},
    {"span": "Crauer <fc Sanser", "reading": "Crauer & Sanser",
     "as_read": "<fc", "printed_page": 31,
     "same_volume": ("n1844_e1555", "Sanser, John W. of Cruver & S. house cor Clark "
                     "and Michigan sts"),
     "second_reading": "Cruver & Sanser, builders, Clark st. b Randolph & Michigan sts",
     "file": "1844directory.txt", "line": 474,
     "second_hand_disagrees": "Kim Torp reads the first partner's surname CRUVER, and "
                              "so does this volume's own second printing of the firm "
                              "(n1844_e1555, n1844_e0993, n1844_e1778). The ampersand "
                              "is the only character this row lifts: the u/a of the "
                              "surname is a separate reading, it needs the page image, "
                              "and it is left standing as the scanner set it."},
    {"span": "Gould it Dodge", "reading": "Gould & Dodge",
     "as_read": "it", "printed_page": 37,
     "same_volume": ("n1844_e0507", "Dodge, Martin, of Gould & Dodge, res N. Gould's"),
     "second_reading": "Gould & Dodge, ball alley and grocery, South Water st. b State "
                       "& Dearborn sts",
     "file": "1844directory.txt", "line": 759, "second_hand_disagrees": None},
    {"span": "Hamilton <fc White", "reading": "Hamilton & White",
     "as_read": "<fc", "printed_page": 38,
     "same_volume": ("n1844_e0783", "Hamilton, Robert P. of H. & White, res T. E. "
                     "Hamilton's"),
     "second_reading": "Hamilton & White, dry goods and grocery store, 139 Lake st",
     "file": "1844directory.txt", "line": 828, "second_hand_disagrees": None},
    {"span": "Skinner 6c .Smith", "reading": "Skinner & Smith",
     "as_read": "6c", "printed_page": 55,
     "same_volume": ("n1844_e1654", "Smith, J. F. of Skinner & S., Mansion House"),
     "second_reading": "Skinner & Smith, Mansion house, 86 Lake st",
     "file": "1844dir2.txt", "line": 513,
     "also_lifts": ("the stray full stop the scanner set before Smith. It is the same "
                    "line and the same sort, both witnesses print the partner's name "
                    "clean, and left standing it would name the firm `Skinner & "
                    ".Smith`. The quote keeps it."),
     "second_hand_disagrees": None},
]

# …AND EVERY OTHER ENTRY IN THE VOLUME THAT CARRIES ONE OF THESE TOKENS (T-1021).
#
# This is the trap, enumerated. Twenty-one entries print `<fc`, `6c`, `&c` or a bare
# `it` outside the seven spans above, and not one of them is a partnership the firm
# test is missing. They fall into four kinds:
#
#   a PERSON naming somebody else's firm      `Parker, John, of P. 6c Dpdge, ho Dearborn`
#   `&c.` closing a stock list                `hardware, iron, nails, &c. 128 Lake st`
#   the scanner's `at`, set as `;it`          `cabinet maker ;it J. B. Weir's`
#   a firm already read as one, on `& Co.`    `Wheeler, Wm. & Co. hardwaid, &c. 145 Lake st`
#
# A rule that read those tokens as ampersands wherever they stood would take all
# twenty-one — welding `nails &c` and `maker ;it` into partnerships. The table above
# cannot reach them, because it matches a whole span at the head of an entry, and this
# asserts it: by id, by the printed line, and by what each must READ as. Three of them
# are firms and stay firms; the other eighteen are men and stay men. A re-read that
# moves one fails here rather than silently widening what the repair touches.
#
# The value is (firm, as printed).
CONJ_UNTOUCHED = {
    "n1844_e0191": (False, "Brand, Alexander, of Murray <fc Brand, res cor Illinois aud Cass "
                           "sts"),
    "n1844_e0268": (False, "Buuerfield, Justin, of B. <fc Collins, res c Michigan and Rush "
                           "sts"),
    "n1844_e0350": (False, "Clark, F. of C. Haines, &c Co. res American Temperance House"),
    "n1844_e0355": (False, "Clark, L. W. hardware, iron, nails, &c. 128 Lake st. cor Clark "
                           "st. (See card)"),
    "n1844_e0366": (False, "Cleaver, Joseph, cabinet maker ;it J. B. Weir's"),
    "n1844_e0496": (False, "Dike, Henry, of Morey &c D. res Isaac Dike's"),
    "n1844_e0652": (False, "Frink. John, of F. Walker <fc Co. h Rand. st. b Clark and "
                           "Dearborn"),
    "n1844_e0710": (False, "Goodrich, Grant, of Spr'mjr <fc G. h Illinois st. b Cass and Rush "
                           "sts"),
    "n1844_e0713": (False, "Goodsell, L. B. dry goods, &c. Dearborn st. b Lake & S. Water'"),
    "n1844_e0716": (True, "Goss, S. W. & Co. dry goods, &c. !J8 Lake st"),
    "n1844_e1024": (False, "King. Tuthill, clothing, dry goods, &c., 115 Lake st. h Clark st"),
    "n1844_e1095": (False, "Leonard, J. W. clerk, ;it Clark, Haines & Co.'s"),
    "n1844_e1103": (False, "Lill, V/m. of L. & Diversy, brewers, n Sand <fc Chicago Avenue"),
    "n1844_e1334": (False, "Nauberger, Hugh, at P. Fund 6c Co.'s"),
    "n1844_e1393": (False, "Parker, John, of P. 6c Dpdge, ho Dearborn st. b Wash & Monroe"),
    "n1844_e1493": (False, "Roberts, D. L. Chicago Temperance House, Lasalle b Lake <fc'S. "
                           "Water sts (bee card)"),
    "n1844_e1693": (False, "Stearns, M. Grdry goods, &c. 136 Lake st"),
    "n1844_e1695": (False, "Stein, Charles, of Sirausel &c S. h Lasalle st near Lake"),
    "n1844_e1734": (False, "Surdam. S. J. stoves, &c. 132 Lake st"),
    "n1844_e1828": (True, "Walker, C. & Co. dry goods, gro. leather, &c. S. Water st. b State "
                          "and Dearborn sts (See card)"),
    "n1844_e1877": (True, "Wheeler, Wm. & Co. hardwaid, &c. 145 Lake st. (See card)"),
}


# HEALED AT THE SOURCE (T-0987 stretch 10). Three of T-1018's sixty-nine no longer
# read past the end of their name, because the reason they did was a destroyed
# surname and SURNAME_IMAGE_REPAIRS lifts it before the comma is ever walked. They
# are kept by id rather than deleted: T-1018's classification of them was right when
# it was made, and the ratchet now asserts the opposite — that they carry NO overrun —
# so a repair that stops firing is caught here as well as in its own table.
OVERRUN_HEALED = {
    "n1844_e0276": "empty_prefix",        # <'ady, Dennis S. — the C read as two marks
    # T-1023 — the rest of the empty_prefix class, healed at the head of the line.
    "n1844_e0009": "empty_prefix",        # the turned tail of Adams, R. E. W: no name
    "n1844_e0278": "empty_prefix",        # * '.ilhoun      -> Calhoun
    "n1844_e0771": "empty_prefix",        # llageman        -> Hageman
    "n1844_e1637": "empty_prefix",        # v; Smith        -> Smith
    "n1844_e0700": "repaired",            # Gilmorc. Win. laborer
    "n1844_e0756": "repaired",            # JrisivoM. David D. res D. S. Griswold's
    # T-0987 stretch 11 — the whole split_surname class, read off the page image.
    "n1844_e0198": "split_surname",       # Brine kerb off  -> Brinckerhoff
    "n1844_e1075": "split_surname",       # Lurk in         -> Larkin
    "n1844_e1872": "split_surname",       # Went worth      -> Wentworth
    "n1844_e1937": "split_surname",       # Woi thinglnm    -> Worthingham
    # T-1021 — the whole firm_conj class, ruled firms on the volume's own second
    # printing of each partnership and healed by CONJ_AMPERSAND lifting the character.
    "n1844_e0063": "firm_conj",           # Ballentine <fc Sherman -> Ballentine & Sherman
    "n1844_e0168": "firm_conj",           # Bowen 6c Cole          -> Bowen & Cole
    "n1844_e0180": "firm_conj",           # Bracken it Tuller      -> Bracken & Tuller
    "n1844_e0439": "firm_conj",           # Crauer <fc Sanser      -> Crauer & Sanser
    "n1844_e0719": "firm_conj",           # Gould it Dodge         -> Gould & Dodge
    "n1844_e0787": "firm_conj",           # Hamilton <fc White     -> Hamilton & White
    "n1844_e1629": "firm_conj",           # Skinner 6c .Smith      -> Skinner & Smith
}

def header_like(line: str) -> bool:
    """A running head: short, and either shouting or mostly scanner noise."""
    s = line.strip()
    if not s or len(s) > 45:
        return False
    if len(s) <= 3:
        return True
    letters = [c for c in s if c.isalpha()]
    return not letters or sum(c.isupper() for c in letters) / len(letters) > 0.7


def leaf_lines(leaf: int):
    path = os.path.join(TEXT, "norris_1844_leaf_%03d.txt" % leaf)
    return open(path, encoding="utf-8").read().splitlines()


def clean_head(text: str) -> str:
    """Strip the scanner's marginal droppings from the front of an entry line.

    The left margin of this scan collects specks — a stray quote, a bullet, a
    lone letter — which land in the OCR ahead of the surname. They are removed
    from the READING only; `quote` keeps them, because the quote has to be
    findable in the committed text.
    """
    return re.sub(r"^[^A-Za-z]*(?:[a-zA-Z]\s)?", "", text).strip()


# THE FIRST COMMA IS NOT ALWAYS NORRIS'S NAME COMMA (T-1018).
#
# `split_entry` takes a person's name as everything before the first comma, which is
# how Norris set it — `Crissman, John M. laborer`. archive.org's OCR loses that comma
# constantly, setting a full stop or nothing at all, and then the name runs on into
# whatever follows: `Wells. Andrew S. of Johoimett W. & Co. h Rand st. b Lasalle and
# Wells` read as a surname of thirteen words, with the trade and the street lost
# inside it.
#
# `name_prefix()` (T-1013) already knows where a name ends — it walks the leading
# tokens and stops at the trade or at `of` — so the repair is to CAP the comma-derived
# name at that prefix. 69 entries read past it. The cap is right for 46 of them and
# would do damage in the other 23, so each of those four classes is refused by name
# and the refusal is written onto the claim.
#
#   firm_branch (7)    The entry is a firm, and the firm branch below never uses the
#                      comma at all — it takes the name from `firm_name(prefix)`. The
#                      overrun is in a span that is not read. Nothing to repair.
#
#   firm_conj (7)      The scanner set the ampersand as `<fc`, `6c` or `it`, so FIRM
#                      never fired and `Bowen & Cole` is read as a man. Capping would
#                      truncate it to `Bowen` and MINT A MAN WHO IS NOT IN THE BOOK —
#                      strictly worse than the run-on. The span is exactly
#                      `Name <conj> Name`, which is what this refusal tests. Widening
#                      FIRM to read those three tokens as ampersands is a separate
#                      ruling about firm/person classification, and `it` is an English
#                      word, so it was filed as its own ticket rather than smuggled in.
#                      THAT TICKET IS MADE (T-1021, CONJ_AMPERSAND above): all seven
#                      are ruled firms on the book's own second printing of each
#                      partnership, the character is lifted by named span, and with it
#                      lifted there is no overrun left — the name and the prefix are
#                      the same three tokens — so the seven move to OVERRUN_HEALED.
#                      The refusal is kept and now stands EMPTY on this reading: it is
#                      the net under the table, so an eighth span of this shape is
#                      refused rather than read, and fails the ratchet below for having
#                      no row in OVERRUN_CLASSES.
#
#   split_surname (4)  The comma IS Norris's name comma and the prefix stops INSIDE a
#                      surname the scanner broke in two: `Went worth, Geo. W.`,
#                      `Lurk in, Timothy`, `Woi thinglnm, Wm.`, `Brine kerb off, John`.
#                      `name_prefix` breaks on the lower-case second half. Capping
#                      would read Wentworth as `Went`. The tell is that the span holds
#                      no capitalised token after the first — no forename, no initial,
#                      so no trade can have started — and a forename stands after the
#                      comma.
#
#   empty_prefix (5)   The reading begins at the trade, so the prefix is empty and the
#                      cap would set the surname to `''` — which drops the claim out of
#                      crosswalk_norris_1844.py, silently, because it skips a claim
#                      with no surname. These are turned lines the entry-boundary rule
#                      mis-cut (`ady` for `<'ady, Dennis S.`) or margin droppings. They
#                      need a ruling of their own; an empty prefix is a REFUSAL.
#
# A refused entry reads exactly as it did before this ticket, and says so on the claim
# in `normalized.name_overrun`. `--self-test` asserts the counts of all five classes.
OVERRUN_CONJ = {"<fc", "6c", "it", "fc", "ic"}

# The 69, by class and by entry id — the self-test's ratchet (see there).
OVERRUN_CLASSES = {
    # --- repaired
    "n1844_e0104": "repaired",            # Bearup^ John I. teacher
    "n1844_e0139": "repaired",            # Birdf J. H. at Dr. Biuinard's
    "n1844_e0275": "repaired",            # Bir/.zard. S. laborer
    "n1844_e0429": "repaired",            # Crissman John M. laborer
    "n1844_e0430": "repaired",            # Crocker Josiah D. white washer
    "n1844_e0550": "repaired",            # Eachus. Virgil H. tailor
    "n1844_e0574": "repaired",            # Enos Wra. C. jr. at A. Clyburn's
    "n1844_e0615": "repaired",            # Flint. Mrs. house Adams st. b Clinton and Jefferson sfs
    "n1844_e0706": "repaired",            # Godnrd. H. B. clerk
    "n1844_e0749": "repaired",            # Greyhnn. W. hostler
    "n1844_e0754": "repaired",            # Griswold. Clns. E. clerk
    "n1844_e0795": "repaired",            # Harmon Charles L. dry goods and groceries
    "n1844_e0918": "repaired",            # Hugunin. L. C. at United States Hotel
    "n1844_e0942": "repaired",            # Jeffries. Gco. warehouse man
    "n1844_e0948": "repaired",            # Jocelyn. J.H. barkeeper at Western Hotel
    "n1844_e1019": "repaired",            # Kimberly Ed. S. physician
    "n1844_e1031": "repaired",            # Kinzie. John H. register land office
    "n1844_e1123": "repaired",            # Lowe. Samuel A. clerk
    "n1844_e1354": "repaired",            # Norton. C. C. of N. & Case
    "n1844_e1388": "repaired",            # Paine. James S. saddler
    "n1844_e1418": "repaired",            # Penton. D. R. at Dr. Britickerhoff's
    "n1844_e1427": "repaired",            # Peterson. GPO. captain schooner St. Joseph
    "n1844_e1443": "repaired",            # Plagge G. shoemaker
    "n1844_e1451": "repaired",            # Powless. John shoemaker
    "n1844_e1460": "repaired",            # Ransom. J. W. res corner Monroe and Clark st
    "n1844_e1502": "repaired",            # Robinson. P. P. boot maker
    "n1844_e1522": "repaired",            # Rowlatt. W. Bethel clergyman
    "n1844_e1525": "repaired",            # Rowley Tlios. E. teamster
    "n1844_e1533": "repaired",            # Russell. C. G. of Rew & Russell
    "n1844_e1590": "repaired",            # Sharer.\"Geo. tailor
    "n1844_e1696": "repaired",            # Steel. J. H. h Lake st. b Water and Canal sts
    "n1844_e1700": "repaired",            # Stevens S. tailor
    "n1844_e1734": "repaired",            # Surdam. S. J. stoves
    "n1844_e1766": "repaired",            # Thompson. Leonard W. carpenter
    "n1844_e1783": "repaired",            # Truesdell. Geo. \\V. clothier
    "n1844_e1830": "repaired",            # Walker. Martin O. of Frink
    "n1844_e1839": "repaired",            # Walton. J. W. dry goods and groceries
    "n1844_e1844": "repaired",            # Ward Mrs. res near North Branch Bridge
    "n1844_e1868": "repaired",            # Wells. Andrew S. of Johoimett W. & Co. h Rand st. b Lasall
    "n1844_e1891": "repaired",            # Wicker. C. G. of C. G. Wicker & Go. res Tremont
    "n1844_e1893": "repaired",            # Wicker. J. H. at C. G. Wicker & Go's
    "n1844_e1936": "repaired",            # AVorcester. D. L. at H. Norton & Co.'s
    "n1844_e1966": "repaired",            # Dennis. Edward M. res Dr. Smith's
    "n1844_e1985": "repaired",            # Greenwood. Theophilus S. house Ontario st. b Dearborn and 
    # --- firm_branch
    "n1844_e0357": "firm_branch",         # Clarke & Co. druggists
    "n1844_e0547": "firm_branch",         # Dyer & Chapin dry goods and groceries
    "n1844_e0554": "firm_branch",         # Eddy & Co. dealers in iron
    "n1844_e1429": "firm_branch",         # Pfund & Co. bakers
    "n1844_e1623": "firm_branch",         # Sicar & Co. groceries
    "n1844_e1817": "firm_branch",         # WTadsworth. E. S. & J. dry goods and groceries
    "n1844_e1892": "firm_branch",         # Wicker. C. G. & Co. dry goods and groceries
    # --- firm_conj: RULED, AND HEALED AT THE SOURCE (T-1021). The seven rows moved
    # to OVERRUN_HEALED below. They no longer read past the end of their name at all:
    # with the ampersand lifted, the comma-derived name and the prefix are the same
    # three tokens, so there is no overrun left to refuse.
    # --- split_surname
    #     T-1018 named four here and refused to cap them, which was the right refusal
    #     and not a reading. T-0987 stretch 11 read all four off the page image, so
    #     they are repaired at the source now and stand in OVERRUN_HEALED below.
    # --- empty_prefix
    #     T-1018 named five and refused to cap any of them, which was the right
    #     refusal and not a reading. All five are read at the source now and stand in
    #     OVERRUN_HEALED below — one off the page image (T-0987 stretch 10), three off
    #     the second hand, and one ruled a turned line rather than a name at all
    #     (T-1023). The class is EMPTY and the self-test holds it empty: a sixth entry
    #     that reads past an empty prefix is a new fault and must be ruled, not filed.
}


def _capitalised(tok: str) -> bool:
    bare = tok.strip(".,'\"<>;:&")
    return bool(bare) and bare[0].isupper()


def overrun_refusal(head: str, prefix, span: str):
    """Why the comma-derived name must NOT be capped at the prefix, or None."""
    toks = span.split()
    over = toks[len(prefix):]
    after = head.split(",", 1)[1].strip() if "," in head else ""
    first_after = after.split()[0] if after else ""
    if not prefix:
        return ("empty_prefix", "the reading begins at the trade, so there is no name to "
                "cap to; an empty surname would drop the claim out of the crosswalk")
    if len(toks) == 3 and over[0] in OVERRUN_CONJ and _capitalised(over[1]):
        return ("firm_conj", "the scanner set this firm's ampersand as %r, so the firm "
                "test never fired; capping would truncate it to a man who is not in "
                "the book" % over[0])
    if not any(_capitalised(t) for t in toks[1:]) and first_after and (
            _capitalised(first_after) or first_after.strip(".,").lower() in TITLES):
        return ("split_surname", "the comma is Norris's own, and the prefix stops inside "
                "a surname the scanner broke in two")
    return None


def still_the_name(tok: str, toks, i: int) -> bool:
    """Is a comma-carrying token's comma one the name runs THROUGH?

    Three printed shapes say yes, and Norris sets all three:

      a suffix's own comma      `Bosworth, jr., Ezra`
      a suffix standing after   `Bumpstead, Thomas, jr. house Wells st.`
      a comma between initials  `Fuller, Andrew, E. clerk` where the scanner set
                                the stop of `Andrew E.` as a comma

    Everything else is the compositor closing the name and opening the trade,
    which is the boundary `split_entry` walks past when this returns False.
    """
    if tok.strip(".,'\"()").lower().strip(",") in TITLES:
        return True
    nxt = toks[i + 1] if i + 1 < len(toks) else ""
    if not nxt:
        return False
    return (nxt.strip(".,'\"()").lower() in TITLES
            or bool(re.fullmatch(r"[A-Z]", nxt.strip(".,"))))


def split_entry(text: str):
    """name / occupation / address, best effort, out of one printed entry."""
    text, surname_repair = repair_surname(text)
    head, head_repair = repair_welded_of(clean_head(text))
    head, conj_repair = repair_conj_ampersand(head)
    prefix = name_prefix(head)
    firm = bool(FIRM.search(" ".join(prefix) + ","))
    if "," in head:
        surname, rest = head.split(",", 1)
    else:
        surname, rest = head, ""
    # T-1018. The comma-derived name runs past the end of the name — cap it at the
    # prefix, unless one of the four named classes refuses.
    overrun = None
    capped = False
    if len(surname.split()) > len(prefix):
        reason = ("firm_branch", "the firm branch takes the name from firm_name(prefix) "
                  "and never reads the comma span") if firm else \
            overrun_refusal(head, prefix, surname)
        if reason:
            overrun = {"refused": reason[0], "why": reason[1],
                       "as_split_on_comma": surname.strip(" .&")}
        else:
            overrun = {"repaired": True, "name": " ".join(prefix),
                       "as_split_on_comma": surname.strip(" .&")}
            # With no name comma inside the prefix, Norris's surname is the first
            # token of it and every token after is a forename. `split(None, n)`
            # returns the untouched remainder as its last element, so the trade and
            # the street come back whole however the scanner spaced them.
            parts = head.split(None, len(prefix))
            surname, capped = prefix[0], True
            rest = parts[len(prefix)] if len(parts) > len(prefix) else ""
    surname, rest = surname.strip(" .&"), rest.strip()
    given = []
    if capped:
        # The forenames are the prefix tail, already delimited by the walk — not a
        # guess off the far side of a comma, so the token test below cannot help.
        given = prefix[1:]
    elif not firm:
        toks = rest.split()
        for i, tok in enumerate(toks):
            bare = tok.strip(".,'\"").lower()
            # T-1113. A capitalised token a street designator follows is the street's
            # name, and the name ended before it.
            if street_ahead(toks, i):
                break
            if bare in TITLES or re.fullmatch(r"[A-Z]", tok.strip(".,")) or (
                    tok[:1].isupper() and len(given) < 3 and not PLACE.fullmatch(tok + " ")):
                # AND THE COMMA THE COMPOSITOR SET WITHOUT A SPACE AFTER IT is the
                # same comma. `Cleaver, T. B.,soap and oil factory` and `Wilson,
                # Maihew,ship carpenter` put it inside a whitespace token, where the
                # test below could never see it, and read forenames of "T. B.,soap"
                # and "Maihew,ship". Keeping the comma on the kept half leaves the
                # offset `rest` is sliced at unchanged, so the trade comes back whole.
                inner = tok.find(",")
                if 0 <= inner < len(tok) - 1:
                    given.append(tok[:inner + 1])
                    break
                given.append(tok)
                # THE PRINTED COMMA CLOSES THE NAME (T-0987 stretch 5, the defect
                # stretch 4 fixed in `read_fergus_1839.py` and this stretch found
                # unfixed here and in Fergus 1843). A capital and a count of three
                # were the whole test, so the run walked past the comma Norris set
                # after the forenames and took the word after it for another one:
                # `Baumgarteu, Morris, Illinois street, b Dearborn and Wolcott`
                # read a forename of "Morris, Illinois" and left Illinois Street
                # inside the name; `Hanson, Abraham, Methodist clergymen` read
                # "Abraham, Methodist" and lost the trade the comma opened.
                if tok.rstrip(".").endswith(",") and not still_the_name(tok, toks, i):
                    break
                continue
            break
        rest = rest[len(" ".join(given)):].strip(" ,.")
    given_s = " ".join(given).strip(" ,.")
    m = PLACE.search(rest)
    occupation = (rest[:m.start()] if m else rest).strip(" ,.")
    address = (rest[m.start():] if m else "").strip(" ,.")
    if not occupation and address:
        occupation, address = "", address
    if firm:
        # A firm's name is the very run the test was decided on, and its trade is
        # what follows: "Sicar & Co. | groceries and boarding house".
        name = " ".join(firm_name(prefix))
        printed = name.strip(" ,.") or head.split(",")[0].strip()
        tail = head[len(name):].strip(" ,.")
        m = PLACE.search(tail)
        occupation = (tail[:m.start()] if m else tail).strip(" ,.")
        address = (tail[m.start():] if m else "").strip(" ,.")
    else:
        printed = surname + (", " + given_s if given_s else "")
    # T-1114. The place of business stands inside the trade line, because Norris prints
    # no mark in front of it; it is read out into its own field and never into address.
    trade, place_of_business = split_place_of_business(occupation or None)
    out = {
        "printed_name": printed,
        "surname": None if firm else surname,
        "given": None if firm else (given_s or None),
        "firm": firm,
        "occupation": trade,
        "address": address or None,
    }
    if place_of_business:
        out["place_of_business"] = place_of_business
        out["place_of_business_note"] = PLACE_OF_BUSINESS_NOTE
    if head_repair:
        out["head_repair"] = head_repair
    if surname_repair:
        out["surname_repair"] = surname_repair
    if conj_repair:
        out["conj_repair"] = conj_repair
    if overrun:
        out["name_overrun"] = overrun
    return out


# GARBLED FORENAMES, REPAIRED (T-0695)
#
# archive.org's OCR sets characters no compositor ever did — `C!;as.` for Chas.,
# `Alonzt> C.` for Alonzo C., a stray quote welded onto Edward and Patrick.
# `tools/name_agreement.garbled()` names them, and a crosswalk refusal raised
# against one of them is a transcription defect, not two people disagreeing.
#
# THE REPAIR MOVES THE READING ONLY. `quote` and `normalized.as_printed` keep
# the damage — the reading_note below is the standing convention, and a tidied
# quote cannot be found again. `normalized.given`, `normalized.printed_name` and
# the claim's `entities` carry the repair, and every repaired claim states it in
# `normalized.given_repair`, so a reader of the card sees both readings.
#
# THE EVIDENCE IS THE SECOND READING, NOT THIS TOOL'S GUESS. Kim Torp typed this
# same directory from the printed page for genealogytrails.com in 2002, off a
# different copy; her transcription is cached at
# `data/research/genealogytrails/text/` and every row below cites it by file and
# line, so the repair can be argued with against a hand that was not this one.
# Where SHE cannot read the token either, the entry stays damaged — see
# UNREPAIRED. Nothing here is inferred from the person the crosswalk would like
# to match: `Hale, J>ctij. F.` reads Benj. F., not the John Hale of 1835.
#
# `surname` + `as_read` is the key, and `--self-test` fails if a row stops
# matching exactly one entry or if a new garbled forename appears with no row.
REPAIRS = [
    {"surname": "Barry", "as_read": 'Edward"', "reading": "Edward",
     "second_reading": "Barry, Edward, laborer, house near North Branch Bridge",
     "file": "1844directory.txt", "line": 109},
    {"surname": "Burch", "as_read": "G/H", "reading": "G.H",
     "second_reading": "Burch, G.H. of Newberry & B, res City Hotel",
     "file": "1844directory.txt", "line": 268},
    {"surname": "Frost", "as_read": "Ge>~", "reading": "Geo",
     "second_reading": "Frost, Geo., h Michigan ave",
     "file": "1844directory.txt", "line": 691},
    {"surname": "Hale", "as_read": "J>ctij. F", "reading": "Benj. F",
     "second_reading": "Hale, Benj. F., botanic physician, 185 Lake st res Wells st",
     "file": "1844directory.txt", "line": 817},
    {"surname": "Kane", "as_read": 'Patrick"', "reading": "Patrick",
     "second_reading": "Kane, Patrick, drayman, house Kinzie st b Clark & Lasalle sts",
     "file": "1844directory.txt", "line": 1032},
    {"surname": "Leach", "as_read": "Patrick^", "reading": "Patrick",
     "second_reading": "Leach, Patrick, laborer, N. Water st. b Dearborn & Wolcott sts",
     "file": "1844directory.txt", "line": 1132},
    {"surname": "Lill", "as_read": "V/m", "reading": "Wm",
     "second_reading": "Lill, Wm. of L. & Diversy, brewers, n Sand & Chicago Ave.",
     "file": "1844directory.txt", "line": 1153},
    {"surname": "Peck", "as_read": "A/.el", "reading": "Azel",
     "second_reading": "Peck, Azel, builder, h Clinton b Washington & Madison sts",
     "file": "1844dir2.txt", "line": 289},
    {"surname": "Perrior", "as_read": 'William"', "reading": "William",
     "second_reading": "Perrior, William, jailor, res Jail buildings",
     "file": "1844dir2.txt", "line": 305},
    {"surname": "Wesencraft", "as_read": "C!;as", "reading": "Chas",
     "second_reading": "Wesencraft, Chas., carpenter and wagon maker, c Clin and Monroe",
     "file": "1844dir2.txt", "line": 764},
    {"surname": "Wood", "as_read": "Alonzt> C", "reading": "Alonzo C",
     "second_reading": "Wood, Alonzo C., mason builder, house Cass st., b Indiana and Ohio",
     "file": "1844dir2.txt", "line": 815},
]

# The damage the second reading cannot lift either. Left exactly as the scanner
# set it, and named here so the next run does not spend itself rediscovering it.
UNREPAIRED = []

# T-0903. THE SECOND HAND CANNOT ALWAYS BE ASKED, AND SOMETIMES THERE IS NO NEED.
# The eleven repairs above rest on Kim Torp's transcription. UNREPAIRED held the one
# she could not lift and said what it would take — "It needs the page image" — and
# these four are read off that image. Two classes:
#
#   * Couch, where the second hand wrote "(can't read)" and only the scan can answer.
#   * The compositor's W set by the scanner as two V's. `name_agreement.garbled()`
#     looks for a character no compositor set, and `VV` is made entirely of letters,
#     so the sweep above cannot see this class at all — which is why three of them
#     sat in the file with nothing said about them. The self-test below now asserts
#     that every `VV` in a forename is accounted for here.
#
# The repair goes in the READING. The quote and as_printed keep the damage, and every
# row asserts the token it replaces, so a re-read that moves a line fails the build
# instead of writing the wrong forename onto the wrong man.
IMAGE_SOURCE = (
    "the archive.org scan the OCR is itself made from, item generaldirectory19norr. "
    "Each line was located by its own word coordinates in "
    "generaldirectory19norr_djvu.xml, cropped from the page image on that bounding "
    "box, enlarged and read by eye. The page images are at "
    "https://archive.org/download/generaldirectory19norr/page/leafNN.jpg.")

# THE COORDINATE SPACE IS PER LEAF, NOT PER BOOK (T-0900).
#
# The djvu XML writes each leaf's word boxes in that leaf's OWN pixel space, and this
# scan's leaves are not one size: leaf 31 is 1592 x 2860 and leaves 40, 42 and 49 are
# 1564 x 2912. The first version of this block quoted a single "1592 x 2860" for the
# whole book, which is the size of the first leaf T-0903 happened to read; a reader who
# took it for the coordinate space and cropped leaf 40 by it would land off the line and
# conclude the citation was invented. So every row below carries its OWN leaf size and
# the word box it was cropped on, and a reader reproduces the crop with:
#
#   leaf N's OBJECT in generaldirectory19norr_djvu.xml (index N-1) — its width/height
#   are `leaf_px`, and `word_box` is that WORD element's coords, left,bottom,right,top.
COORDINATE_SPACE = (
    "The word box is this leaf's own OBJECT coordinates in "
    "generaldirectory19norr_djvu.xml, left,bottom,right,top, and leaf_px is the pixel "
    "size of leafNN.jpg, which is that same space. The leaves of this scan are NOT all "
    "one size — do not carry one leaf's dimensions to another.")

IMAGE_REPAIRS = [
    {"surname": "Couch", "as_read": "Iia", "reading": "Ira", "leaf": 40,
     "leaf_px": [1564, 2912], "word_box": "271,2163,358,2125",
     "reads": "Couch, Ira, proprietor of the Tremont House, corner of Lake and Dearborn sts",
     "why": "the r of Ira read as an i. UNREPAIRED asked for this line by name: Kim "
            "Torp reads the same token '(can't read)', so the page image is the only "
            "witness there is, and it prints Ira.",
     "reread": "Ira — the second stroke is an r, with the shoulder and no dot",
     "second_reading": None},
    {"surname": "Abbott", "as_read": "VV", "reading": "W", "leaf": 31,
     "leaf_px": [1592, 2860], "word_box": "248,1776,328,1742",
     "reads": "Abbott, W. clerk at Ward Rathbone's, residence same",
     "why": "the compositor's W set by the scanner as two V's",
     "reread": "W. — one sort, and the Ward two words along is set from the same one",
     "second_reading": "Abbott, W., clerk at Ward Rathbone's, residence same"},
    {"surname": "Day", "as_read": "VVm. Lasalle House", "reading": "Wm. Lasalle House",
     "leaf": 42, "leaf_px": [1564, 2912], "word_box": "199,617,319,582",
     "reads": "Day, Wm. Lasalle House, corner of Lasalle and Randolph sts",
     "why": "the same W. Only the damaged token is repaired: the splitter reads "
            "'Lasalle House' as part of the given name because the line prints no "
            "comma after the forename, and that is a parse, not a transcription defect",
     "reread": "Wm. — and the line prints no comma after it, as the why says",
     "second_reading": "Day, Wm., Lasalle House, corner of Lasalle & Randolph sts"},
    {"surname": "Hequenbourg", "as_read": "G. VV", "reading": "G. W", "leaf": 49,
     "leaf_px": [1564, 2912], "word_box": "495,1758,574,1725",
     "reads": "Hequenbourg, G. W. clerk, at B. F. Sherman's, res same",
     "why": "the same W, on the second of two initials",
     "reread": "G. W. — the second initial is one sort, spaced as an initial",
     "second_reading": "Hequenbourg, G.W., clerk, at B.F. Sherman's, res same"},
]

# T-0900 RE-READ ALL FOUR, off the same leaf images and off nobody's notes.
#
# T-0900 was filed by T-0695 for the Couch line alone and T-0903 answered it the same
# day, so the ticket outlived its work. Closing it on T-0903's say-so would have been
# the cheap move and the wrong one: an image repair is a single hand on a token, and
# this project's whole case for `documented` is that a reading can be gone back to. So
# each row's box was re-cropped from the leaf image and read again, cold, by a second
# hand — the `reread` field above is what that hand saw. All four stand.
#
# It is also what found the coordinate-space defect: the crop only lands on the line
# when the leaf's own dimensions are used, which is how a reader learns that the one
# size quoted for the whole book was wrong.
REREAD_BY = ("T-0900, an independent second reading off the same leaf image, cropped "
             "on the word box recorded with the row.")

# The scanner's W. Letters only, so `name_agreement.garbled()` is blind to it and the
# self-test has to look for it by hand.
SCANNER_W = "VV"

REPAIR_SOURCE = ("Kim Torp's transcription of Norris 1844 for genealogytrails.com "
                 "(\u00a9 2002), cached at data/research/genealogytrails/text/ by "
                 "tools/read_genealogytrails.py --fetch. An independent hand, typed "
                 "from a different copy of the same printed book.")


# THE SURNAME THE CROSSWALK CANNOT SEE (T-0987 stretch 10)
#
# `crosswalk_norris_1844.py` reaches an 1835 person through the SURNAME and nothing
# else: a fold, then the first initial. So a surname the scanner destroyed does not
# make a bad match — it makes NO match, and no refusal either. The entry is not in
# the pool at all, and nothing downstream can tell the difference between a name the
# volume does not print and a name it prints that this reading could not read.
#
# `data/research/directories/second_readings/norris_1844_genealogytrails.json` is where
# they were found — it had held them since T-0576 and nothing had gone back to it.
# That file is a COMPARISON of the committed reading against Kim Torp's independent
# transcription, and its own README says a reconciliation lands in `../claims/` and is
# said there. Of its 67 disagreeing entries, 25 disagree about the SURNAME. Every one of the 25 was cropped from the archive.org page image on its own
# word box and read by eye — the same discipline as IMAGE_REPAIRS above, and the same
# citation fields, so a reader can go back to the ink.
#
# WHAT THE INK SAID, in three classes:
#
#   sixteen repaired (below). The scanner set a character no compositor did —
#   `Buticifit'ld` for Butterfield, `(JrisivoM` for Griswold, `Hjolrnes` for Holmes,
#   `JYIcCanny` for McCanny — or a letter for its neighbour: `Bolsford`, `Hasted`,
#   `Patient`, `Gilmorc`. The image prints the second hand's reading in all fourteen.
#
#   two UPHELD, and they matter as much. `Sealey, George` and `Kautenburger, Peter`
#   are where Kim Torp is wrong and the OCR is right; the image prints Sealey and
#   Kautenburger. Nothing is repaired and the rows are kept, because a reconciliation
#   that only ever moved toward the second hand would not be a reading of the page.
#
#   seven left alone. Four are firms whose ampersand the scanner set as `<fc`, `it`,
#   `6c` or `A;` — T-1018 refuses that class by name and files it as its own ruling
#   about firm/person classification, and this stretch does not smuggle it in. Two are
#   firms the ampersand DID reach, `Moseley & SIcCord` and `Whit'mc, Magill & Co.`,
#   whose garbled span the firm branch never reads and no crosswalk ever sees. One,
#   `Jones, K. K.`, has the surname right already and disagrees only about a speck in
#   the left margin, which `clean_head` was written to drop.
#
# THREE OF THE FOURTEEN ALSO LOSE THE FORENAME, and that is the separator. Norris sets
# `Surname, Given`; this printing sets a proportion of those commas with the tail
# unprinted, and the image shows a clean round point after Bates, Gilmore and
# Woodbury. T-1018's cap catches most of that class, but not where the run-on is only
# two words long — `Bates. John` read as one surname with a given name of `jr`,
# `Woodbnry. Hiram` with no given name at all, and `Ryat). John` with a trade of
# `boaniing`. The surname is DOCUMENTED, read off the image. That the point stands
# where the format sets a comma is INFERRED, and the reasoning is that a surname is
# never abbreviated, so a stop immediately after one cannot be an abbreviation point.
#
# THE REPAIR MOVES THE READING ONLY. `quote` and `normalized.as_printed` keep the
# damage, exactly as T-0695 and T-0903 do, and every repaired claim states both
# readings in `normalized.surname_repair`. `as_read` is the head of the printed line
# and `--self-test` fails if a row stops matching exactly one entry.
SURNAME_IMAGE_REPAIRS = [
    {"as_read": "TJarnes,", "reading": "Barnes,", "surname": "Barnes", "leaf": 33,
     "leaf_px": [1592, 2860], "word_box": "43,586,226,546",
     "reads": "Barnes, Hamilton, carpenter, Randolph street, between Clark and "
              "Lasalle street, house Madison street, West of Clark street",
     "why": "the B set as TJ — the bowl of the B broken open and the stem read as a "
            "separate letter",
     "reread": "Barnes — one sort, and the Barnes two lines above is set from the same",
     "second_reading": "Barnes, Hamilton, carpenter, Randolph st, bet Clark & Lasalle "
                       "st, house Madison st, West of Clark st"},
    {"as_read": "Bates.", "reading": "Bates,", "surname": "Bates", "leaf": 33, "separator": True,
     "leaf_px": [1592, 2860], "word_box": "61,1837,200,1803",
     "reads": "Bates. John, jr. auction and commission merchant, 174 Lake street "
              "house South Water street (See card)",
     "why": "the separator. The surname reads Bates and the mark after it is a clean "
            "point with no tail; the two Bates entries above it set the same comma "
            "with one. Read as one surname the entry lost John to the surname and "
            "kept `jr` as the forename",
     "reread": "Bates — and a round point, not a comma; the ink is a full stop",
     "second_reading": "Bates, John, jr., auction & commission merchant, 174 Lake st "
                       "house South Water st"},
    {"as_read": "Bolsford, 1.", "reading": "Botsford, I.", "surname": "Botsford",
     "leaf": 35, "leaf_px": [1592, 2860], "word_box": "53,708,258,670",
     "reads": "Botsford, I. tailor, Wells st. b Randolph and Washington streets",
     "why": "the t read as an l, and the initial I set as a figure 1 — which is not a "
            "letter, so the entry carried no initial at all and the `1.` went into "
            "the trade. The Botsford two lines below is set from the same sorts",
     "reread": "Botsford, I. — the initial is a capital I, serifed top and bottom",
     "second_reading": "Botsford, I. (or L.?), tailor, Wells st b Randolph & "
                       "Washington sts"},
    {"as_read": "Buticifit'ld,", "reading": "Butterfield,", "surname": "Butterfield",
     "leaf": 37, "leaf_px": [1592, 2860], "word_box": "108,1858,353,1820",
     "reads": "Butterfield, Jonas, captain, res Franklin st",
     "why": "characters no compositor set. Four other Butterfields stand around it on "
            "the same page, spelled",
     "reread": "Butterfield — and the four neighbours read the same",
     "second_reading": "Butterfield, Jonas, captain, res Franklin st"},
    {"as_read": "<'ady,", "reading": "Cady,", "surname": "Cady", "leaf": 37,
     "leaf_px": [1592, 2860], "word_box": "109,2141,244,2099",
     "reads": "Cady, Dennis S. Lake Street House, 135 Lake st (See card)",
     "why": "the C set as two marks. T-1018 names this entry as its empty_prefix "
            "class — clean_head strips the `<'` and the surname read `ady`, so the "
            "only Cady the volume prints was filed under a name that is not one",
     "reread": "Cady — a C with the aperture open at the right, then ady",
     "second_reading": "Cady, Dennis, S Lake Street House, 135 Lake st"},
    {"as_read": "Gilmorc.", "reading": "Gilmore,", "surname": "Gilmore", "leaf": 46, "separator": True,
     "leaf_px": [1564, 2912], "word_box": "109,2042,304,2006",
     "reads": "Gilmore. Wm. laborer, h N. Branch, n river",
     "why": "the final e read as a c, and the separator set as a point. The forename "
            "survived on T-1018's cap; the surname did not",
     "reread": "Gilmore — the last letter closes, and the mark after it is a point",
     "second_reading": "Gilmore, Wm., laborer, h N. Branch, n river"},
    {"as_read": "(JrisivoM.", "reading": "Griswold,", "surname": "Griswold", "leaf": 47, "separator": True,
     "leaf_px": [1564, 2912], "word_box": "138,2487,348,2452",
     "reads": "Griswold, David D. res D. S. Griswold's",
     "why": "characters no compositor set. Three other Griswolds stand around it on "
            "the same page, spelled, and the entry's own address names a fourth",
     "reread": "Griswold — and the D. S. Griswold's it gives as an address is set "
               "from the same sorts two lines above",
     "second_reading": "Griswold, David D., res D.S. Griswold's"},
    {"as_read": "Hagcman,,", "reading": "Hageman,", "surname": "Hageman", "leaf": 48,
     "leaf_px": [1564, 2912], "word_box": "75,1053,280,1011",
     "reads": "Hageman, ———, turner, at Blair's",
     "why": "the e read as a c, and the em rule the compositor set for the missing "
            "forename read as a second comma. Two other Hagemans stand above it",
     "reread": "Hageman — and the mark after the comma is a rule, not a name",
     "second_reading": "Hageman, -- (sic), turner, at Blair's"},
    {"as_read": "Hi^gins,", "reading": "Higgins,", "surname": "Higgins", "leaf": 49,
     "leaf_px": [1564, 2912], "word_box": "121,2182,312,2141",
     "reads": "Higgins, E. milk dealer, Canal st. 3d ward",
     "why": "a caret for the first g. The Higgins on the two lines below are spelled",
     "reread": "Higgins — two g's, and the neighbours read the same",
     "second_reading": "Higgins, F., milder dealer, Canal st 3d ward"},
    {"as_read": "Hjolrnes,", "reading": "Holmes,", "surname": "Holmes", "leaf": 50,
     "leaf_px": [1564, 2912], "word_box": "79,1855,268,1817",
     "reads": "Holmes, Mrs. house Lasalle street, b Washington and Madison",
     "why": "characters no compositor set — an rn for the m, and a j struck into the "
            "o. Three other Holmeses stand above it on the same page",
     "reread": "Holmes — and the address reads Madison, which is where the second "
               "hand reads Clinton; the committed reading has that right",
     "second_reading": "Holmes, Mrs, house Lasalle st, b Washington and Clinton"},
    {"as_read": "Hasted,", "reading": "Husted,", "surname": "Husted", "leaf": 51,
     "leaf_px": [1564, 2912], "word_box": "128,1664,305,1626",
     "reads": "Husted, H. H. clothing store, 97½ Lake, res at F. C. Sherman's— "
              "(See card)",
     "why": "the u read as an a",
     "reread": "Husted — the second letter has no crossbar and closes at the foot",
     "second_reading": "Husted, H.H., clothing store, 97 ½ Lake, res at F.C. "
                       "Sherman's"},
    {"as_read": "Jofies,", "reading": "Jones,", "surname": "Jones", "leaf": 52,
     "leaf_px": [1564, 2912], "word_box": "66,2014,224,1975",
     "reads": "Jones, Tarleton, lumber merchant, S. W. st, at bridge, res Mrs. "
              "Green's (See card)",
     "why": "the n read as fi. Five other Joneses stand around it on the same page",
     "reread": "Jones — and the Jones on the line above is set from the same sorts",
     "second_reading": "Jones, Tarleton, lumber merchant, S.W. st, at bridge, res "
                       "Mrs. Green's"},
    {"as_read": "JYIcCanny,,", "reading": "McCanny,", "surname": "McCanny", "leaf": 56,
     "leaf_px": [1564, 2912], "word_box": "72,569,283,525",
     "reads": "McCanny, ———, clerk, at H. M. Stow's",
     "why": "the M set as JYI, and the em rule for the missing forename read as a "
            "second comma. Three McCartys and a McCarthy stand above it",
     "reread": "McCanny — an M, then a small-capital c; the mark after the comma is "
               "a rule",
     "second_reading": "McCanny, ---(sic), clerk, at H.M. Stow's"},
    {"as_read": "Patient,", "reading": "Pattent,", "surname": "Pattent", "leaf": 61,
     "leaf_px": [1564, 2912], "word_box": "134,795,291,757",
     "reads": "Pattent, ——— res Mrs. Green's",
     "why": "the second t read as an i, which turns the surname into an English word "
            "and hides it. Pattee and Patten stand on the two lines above",
     "reread": "Pattent — the fourth letter is a t with its crossbar",
     "second_reading": "Pattent, -- (sic), res Mrs. Green's"},
    {"as_read": "Ryat).", "reading": "Ryan,", "surname": "Ryan", "leaf": 63, "separator": True,
     "leaf_px": [1564, 2912], "word_box": "135,2586,270,2543",
     "reads": "Ryan, John, boarding house, South Water street",
     "why": "the n welded to the comma and read as `t)`. Read as one surname the "
            "entry lost John to the surname and kept `boaniing` as the trade. The "
            "Ryan on the line above is set from the same sorts",
     "reread": "Ryan — and the mark after it carries a tail, unlike Bates and Gilmore",
     "second_reading": "Ryan, John, boarding house, South Water st"},
    {"as_read": "\"Woodbnry.", "reading": "Woodbury,", "surname": "Woodbury", "leaf": 71, "separator": True,
     "leaf_px": [1564, 2912], "word_box": "99,2300,361,2254",
     "reads": "Woodbury. Hiram, clerk, at T. W. Salisbury's",
     "why": "the u read as an n, and the separator set as a point. Read as one "
            "surname the entry lost Hiram to the surname and carried no forename. "
            "The Woodbury on the line above is spelled",
     "reread": "Woodbury — and a round point after it, as Bates and Gilmore set",
     "second_reading": "Woodbury, A.J., clerk, at Bristol & Porter's house Monroe st "
                       "(the second hand reads the line ABOVE this one; both entries "
                       "stand in the committed text)"},
]

# WHERE THE SECOND HAND IS WRONG. Read off the same images, on the same terms, and
# kept because a reconciliation that only ever moved one way would not be a reading.
SURNAME_UPHELD = [
    {"as_read": "Sealey,", "surname": "Sealey", "leaf": 64, "leaf_px": [1564, 2912],
     "reads": "Sealey, George, grocer, S. Water st",
     "why": "Kim Torp reads `Scaley (Sealy?)` and says so with her own query. The "
            "image prints Sealey: an e in the second position, and the y carries the "
            "ey of the fifth and sixth. The committed reading stands",
     "second_reading": "Scaley (Sealy?), George, grocer, S. Water st"},
    {"as_read": "Kautenburger,", "surname": "Kautenburger", "leaf": 73,
     "leaf_px": [1564, 2912],
     "reads": "Kautenburger, Peter, laborer, \" \" \"",
     "why": "Kim Torp reads Kantenburger. The image prints Kautenburger, with a u. "
            "Her line also expands this entry's three ditto marks to `house Dutch "
            "Settlement`, which is what the two entries above it print and what the "
            "marks carry — that reading is not disputed and is not a surname, so "
            "it is recorded here and not applied",
     "second_reading": "Kantenburger, Peter, laborer, house Dutch Settlement"},
]


# THE OTHER THIRTY-SEVEN (T-0987 stretch 11)
#
# Stretch 10 repaired sixteen surnames the scan destroyed, found through the second
# reading's own list of disagreements. It closed by measuring what that list could NOT
# see: 68 person entries still hold a space inside their surname, and once the twelve
# real two-word names, the eight institutions and the eleven firm conjunctions T-1018
# owns are set aside, THIRTY-SEVEN remain — entries whose surname hides them from
# `crosswalk_norris_1844.py` exactly as those sixteen did, and which the comparison
# never flagged because it folds punctuation and spacing before it compares.
#
# THAT FOLD IS THE FINDING. Every one of the thirty-seven is in the comparison's
# `identical` or `agrees` bucket, carrying the second hand's correct line — Brinckerhoff
# for `Brine kerb off`, Larkin for `Lurk in`, Wentworth for `Went worth` — and nothing
# had gone back to it, because the file's own summary counts only `differs`. The answer
# had been in the repository since T-0576.
#
# All thirty-seven were cropped from the archive.org leaf image on their own word box,
# enlarged and read, and then read a SECOND time on a fresh crop at a different
# magnification, in an order shuffled so the reader could not carry the first pass's
# expectation down the page. Both passes are recorded: `reread` is the second.
#
# WHAT THE INK SAID ABOUT THE SEPARATOR, which is where this stretch corrects the one
# before it. Stretch 10 wrote that this printing "sets a proportion of those commas with
# the tail unprinted". For the ten it read, that was what the image showed. Across the
# twenty-seven here it is the MINORITY case:
#
#     15  a comma, tail and all, that the SCANNER read as a point
#     10  a round point on the baseline, with nothing below it
#      2  undecided — the two passes disagreed (Klien, Lahy)
#
# So the common cause is the OCR, not the compositor, and `separator_mark` on every row
# says which one this entry is. The remaining ten of the thirty-seven are not separator
# cases at all: five surnames the scan broke into words (Brinckerhoff, Larkin, McWard,
# Wentworth, Worthingham), one comma welded into the letter beside it (Bandle), one real
# two-word surname with a damaged letter (Van Drezer, whose z was set as a solidus), and
# THREE WHERE THE COMMA IS NOT IN THE INK AT ALL.
#
# THOSE THREE ARE `inferred`, AND THE DISTINCTION IS THE POINT. Brown, Butterfield and
# Carson show clean paper between surname and forename — no comma, no point, no mark of
# any kind, at sixteen times magnification. The surname is still DOCUMENTED, because the
# letters are on the page; the separator this reading supplies is not, so those rows
# carry `confidence: inferred` and the reasoning T-0987 stretch 10 argued: Norris sets
# `Surname, Given` throughout, and a forename standing alone after a surname is that
# format with its comma omitted. Nothing else in the entry moves.
#
# THE REPAIR MOVES THE READING ONLY, on the same terms as every row above: `quote` and
# `normalized.as_printed` keep the damage, `--self-test` fails if a row stops matching
# exactly one entry, and the crosswalk is re-derived in the same commit.

SURNAME_IMAGE_REPAIRS_STRETCH_11 = [
    {"as_read": "Bandlej Willis,",
     "reading": "Bandle, Willis,",
     "surname": "Bandle", "leaf": 32, "leaf_px": [1592, 2860],
     "word_box": "83,2769,259,2727", "separator_mark": "welded",
     "separator": True,
     "reads": "Bandle, Willis, b'smith, at Stow's Foundry, h N. Branch, 4th ward",
     "why": "the name comma welded to the e beside it and read as a j tail, so the "
            "surname swallowed the forename. The image prints a comma, on the baseline "
            "with its tail, and the e closes before it",
     "reread": "Bandle, — the mark is a comma, tail and all; the e beside it is whole",
     "second_reading": "Bandle, Willis, b'smith, at Stow's Foundry, h N. Branch, 4th "
                      "ward",
     "second_reading_bucket": "agrees", "entry": "n1844_e0066"},
    {"as_read": "Brine kerb off, John,",
     "reading": "Brinckerhoff, John,",
     "surname": "Brinckerhoff", "leaf": 36, "leaf_px": [1592, 2860],
     "word_box": "77,263,194,222", "separator_mark": "comma",
     "separator": True,
     "reads": "Brinckerhoff, John, physician, Clark st. office 143 Lake st. check- "
              "ered drug store (See card)",
     "why": "one surname set as three words. The scan broke Brinckerhoff at two of its "
            "own letter joins; the image prints it as one sort run with no space in "
            "it, and the comma after it is the volume's name comma",
     "reread": "Brinckerhoff, — one word, and a comma with a tail",
     "second_reading": "Brinckerhoff, John, physician, Clark st office 143 Lake st "
                      "checkered drug store",
     "second_reading_bucket": "agrees", "entry": "n1844_e0198"},
    {"as_read": "Brown Clement,",
     "reading": "Brown, Clement,",
     "surname": "Brown", "leaf": 36, "leaf_px": [1592, 2860],
     "word_box": "76,1003,243,967", "separator_mark": "absent",
     "separator": True, "confidence": "inferred",
     "reads": "Brown, Clement, res Sauganash",
     "why": "the separator is not in the ink. The image shows clean paper between "
            "Brown and Clement and no mark of any kind, so this is the compositor's "
            "omission and not the scanner's loss. The surname is what the page prints; "
            "the comma is supplied",
     "reread": "Brown  Clement — a word space, wider than this setting's, and nothing "
               "in it",
     "second_reading": "Brown, Clement, res Sauganash",
     "second_reading_bucket": "identical", "entry": "n1844_e0210"},
    {"as_read": "Butterfield George,",
     "reading": "Butterfield, George,",
     "surname": "Butterfield", "leaf": 37, "leaf_px": [1592, 2860],
     "word_box": "107,1714,340,1680", "separator_mark": "absent",
     "separator": True, "confidence": "inferred",
     "reads": "Butterfield, George, res Tremont House",
     "why": "the same omission. Clean paper between Butterfield and George, no mark; "
            "four other Butterfields on the same leaf carry their comma",
     "reread": "Butterfield George — nothing between them but paper",
     "second_reading": "Butterfield, George res Tremont House",
     "second_reading_bucket": "identical", "entry": "n1844_e0267"},
    {"as_read": "Carson James,",
     "reading": "Carson, James,",
     "surname": "Carson", "leaf": 38, "leaf_px": [1564, 2912],
     "word_box": "101,777,260,742", "separator_mark": "absent",
     "separator": True, "confidence": "inferred",
     "reads": "Carson, James, carpenter, residence State st",
     "why": "the same omission, and the third of three. Clean paper between Carson and "
            "James",
     "reread": "Carson James — no mark, and the gap is a word space",
     "second_reading": "Carson, James, carpenter, residence State st",
     "second_reading_bucket": "identical", "entry": "n1844_e0299"},
    {"as_read": "Connell. John,",
     "reading": "Connell, John,",
     "surname": "Connell", "leaf": 40, "leaf_px": [1564, 2912],
     "word_box": "98,1128,287,1094", "separator_mark": "comma",
     "separator": True,
     "reads": "Connell, John, laborer, Wolcott st. b Water & Kinzie sts",
     "why": "THE SCANNER'S POINT, NOT THE COMPOSITOR'S. The image prints a comma with "
            "its tail below the baseline; the OCR set it as a stop and the surname "
            "then ran on to take the forename with it",
     "reread": "Connell, — the tail is there, curving left under the baseline",
     "second_reading": "Connell, John, laborer, Wolcott st b Water & Kinzie sts",
     "second_reading_bucket": "identical", "entry": "n1844_e0395"},
    {"as_read": "D;ma. Patrick,",
     "reading": "Dana, Patrick,",
     "surname": "Dana", "leaf": 41, "leaf_px": [1564, 2912],
     "word_box": "138,2170,278,2136", "separator_mark": "point",
     "separator": True,
     "reads": "Dana, Patrick, teamster, at A. S. Sherman's",
     "why": "the n read as a semicolon and an m — and after it a clean round point "
            "with no tail, where the format sets a comma",
     "reread": "Dana. — four letters, and a round point sitting on the baseline",
     "second_reading": "Dana, Patrick, teamster, at A.S. Sherman's",
     "second_reading_bucket": "agrees", "entry": "n1844_e0460"},
    {"as_read": "Frink. John,",
     "reading": "Frink, John,",
     "surname": "Frink", "leaf": 45, "leaf_px": [1564, 2912],
     "word_box": "112,1921,255,1886", "separator_mark": "point",
     "separator": True,
     "reads": "Frink, John, of F. Walker <fc Co. h Rand. st. b Clark and Dearborn",
     "why": "a round point where the format sets a comma",
     "reread": "Frink. — a point, square on the baseline, no tail",
     "second_reading": "Frink, John, of F. Walker & co., h Rand. st. b Clark & Dearborn",
     "second_reading_bucket": "agrees", "entry": "n1844_e0652"},
    {"as_read": "Green. Russell,",
     "reading": "Green, Russell,",
     "surname": "Green", "leaf": 47, "leaf_px": [1564, 2912],
     "word_box": "128,1891,283,1857", "separator_mark": "point",
     "separator": True,
     "reads": "Green, Russell, clerk, at J. M. Underwood's",
     "why": "a round point where the format sets a comma",
     "reread": "Green. — a point on the baseline; nothing descends",
     "second_reading": "Green, Russell, clerk, at J.M. Underwood's",
     "second_reading_bucket": "identical", "entry": "n1844_e0744"},
    {"as_read": "Hall. Edward,",
     "reading": "Hall, Edward,",
     "surname": "Hall", "leaf": 48, "leaf_px": [1564, 2912],
     "word_box": "75,1231,195,1196", "separator_mark": "point",
     "separator": True,
     "reads": "Hall, Edward, saddler and harness maker, at S. 13. C'obb's",
     "why": "a round point where the format sets a comma. The trade is separated by a "
            "second point on the same line, which is this printing's habit and not "
            "repaired here",
     "reread": "Hall. — a point, and a second one after Edward",
     "second_reading": "Hall, Edward, saddler and harness maker, at S.B. Cobb's",
     "second_reading_bucket": "agrees", "entry": "n1844_e0777"},
    {"as_read": "King. Tuthill,",
     "reading": "King, Tuthill,",
     "surname": "King", "leaf": 53, "leaf_px": [1564, 2912],
     "word_box": "158,1842,284,1799", "separator_mark": "comma",
     "separator": True,
     "reads": "King, Tuthill, clothing, dry goods, &c., 115 Lake st. h Clark st",
     "why": "the scanner's point for the compositor's comma; the tail is in the ink",
     "reread": "King, — the tail runs down beside the g's",
     "second_reading": "King, Tuthill, clothing, dry goods, &c., 115 Lake st. h Clark "
                      "st",
     "second_reading_bucket": "identical", "entry": "n1844_e1024"},
    {"as_read": "Klien. Matthias,",
     "reading": "Klien, Matthias,",
     "surname": "Klien", "leaf": 53, "leaf_px": [1564, 2912],
     "word_box": "166,2425,303,2392", "separator_mark": "undecided",
     "separator": True,
     "reads": "Klien, Matthias, baker, North Water st. house same",
     "why": "the separator, and the two hands of this reading disagreed about it — a "
            "mark with a short descender on one crop and a round point on the other. "
            "Undecided, and it does not change the split: a stop cannot follow an "
            "unabbreviated surname. Kim Torp reads the surname Klein; the image prints "
            "Klien, i before e, and the committed spelling stands",
     "reread": "Klien + a mark that may carry a tail — the two readings did not agree",
     "second_reading": "Klein, Matthias, baker, North Water st, house same",
     "second_reading_bucket": "agrees", "entry": "n1844_e1037"},
    {"as_read": "Lahy. Sylvester,",
     "reading": "Lahy, Sylvester,",
     "surname": "Lahy", "leaf": 54, "leaf_px": [1564, 2912],
     "word_box": "70,1091,212,1047", "separator_mark": "undecided",
     "separator": True,
     "reads": "Lahy, Sylvester, laborer, North Water st. near Franklin",
     "why": "the separator, and the two hands disagreed here too: a tail on the first "
            "crop, none on the second, with the y's descender standing beside it "
            "either way",
     "reread": "Lahy + a mark the y's tail crowds; undecided",
     "second_reading": "Lahy, Sylvester, laborer, North water st. near Franklin",
     "second_reading_bucket": "identical", "entry": "n1844_e1059"},
    {"as_read": "Lurk in, Timothy,",
     "reading": "Larkin, Timothy,",
     "surname": "Larkin", "leaf": 54, "leaf_px": [1564, 2912],
     "word_box": "74,1819,177,1786", "separator_mark": "comma",
     "separator": True,
     "reads": "Larkin, Timothy, mason, house Kinzie st. b Frank, and Wells sts",
     "why": "one surname set as two words and an a read as a u. The image prints "
            "Larkin, one sort run, and a comma after it",
     "reread": "Larkin, — no space inside it, and a comma with a tail",
     "second_reading": "Larkin, Timothy, mason, house Kinzie st. b frank. and Wells sts",
     "second_reading_bucket": "agrees", "entry": "n1844_e1075"},
    {"as_read": "Lowe. Oscar,",
     "reading": "Lowe, Oscar,",
     "surname": "Lowe", "leaf": 55, "leaf_px": [1564, 2912],
     "word_box": "151,1798,297,1764", "separator_mark": "comma",
     "separator": True,
     "reads": "Lowe, Oscar, clerk, E. S. & J. Wadsworth",
     "why": "the scanner's point for the compositor's comma",
     "reread": "Lowe, — the tail is under the e",
     "second_reading": "Lowe, Oscar, clerk, E.S. & J. Wadsworth",
     "second_reading_bucket": "identical", "entry": "n1844_e1121"},
    {"as_read": "Me Ward, James,",
     "reading": "McWard, James,",
     "surname": "McWard", "leaf": 57, "leaf_px": [1564, 2912],
     "word_box": "157,856,226,822", "separator_mark": "comma",
     "separator": True,
     "reads": "McWard, James, harness maker at Horton's",
     "why": "the Scottish prefix set as a separate word and its c read as an e. The "
            "image prints McWard closed up, the c riding small against the W",
     "reread": "McWard, — one word, the c small and tight to the W",
     "second_reading": "McWard, James, harness maker at Horton's",
     "second_reading_bucket": "agrees", "entry": "n1844_e1203"},
    {"as_read": "Marsallani. Louis,",
     "reading": "Marsallani, Louis,",
     "surname": "Marsallani", "leaf": 57, "leaf_px": [1564, 2912],
     "word_box": "156,2097,394,2064", "separator_mark": "point",
     "separator": True,
     "reads": "Marsallani, Louis, stone quarrier, res Chas. McDonnell's",
     "why": "a round point where the format sets a comma. Kim Torp reads the surname "
            "Marsallam; the image prints an n and an i, and the committed spelling "
            "stands",
     "reread": "Marsallani. — ends n-i, and a point on the baseline",
     "second_reading": "Marsallam, Louis, stone quarrier, res Chas. McDonell's",
     "second_reading_bucket": "agrees", "entry": "n1844_e1230"},
    {"as_read": "Merriam. Mrs. Mary,",
     "reading": "Merriam, Mrs. Mary,",
     "surname": "Merriam", "leaf": 58, "leaf_px": [1564, 2912],
     "word_box": "94,1206,299,1171", "separator_mark": "comma",
     "separator": True,
     "reads": "Merriam, Mrs. Mary, boarding house, Lake st b State & Wabash",
     "why": "the scanner's point for the compositor's comma; the title and forename "
            "follow it",
     "reread": "Merriam, — a comma, tail below the m",
     "second_reading": "Merriam, Mrs. Mary, boarding house, Lake st b State & Wabash",
     "second_reading_bucket": "identical", "entry": "n1844_e1263"},
    {"as_read": "Otlaway. Charles,",
     "reading": "Ottaway, Charles,",
     "surname": "Ottaway", "leaf": 60, "leaf_px": [1564, 2912],
     "word_box": "109,2312,303,2269", "separator_mark": "point",
     "separator": True,
     "reads": "Ottaway, Charles, grocer, 175 Lake st",
     "why": "the double t read as t-l, and a round point where the format sets a comma",
     "reread": "Ottaway. — two t's, and a point with no tail",
     "second_reading": "Ottaway, Charles, grocer, 175 Lake st",
     "second_reading_bucket": "agrees", "entry": "n1844_e1381"},
    {"as_read": "Pierce. Asahel,",
     "reading": "Pierce, Asahel,",
     "surname": "Pierce", "leaf": 61, "leaf_px": [1564, 2912],
     "word_box": "154,2541,316,2506", "separator_mark": "comma",
     "separator": True,
     "reads": "Pierce, Asahel, blacksmith. S. Water st. b Lake and Randolph sts house "
              "Lake st. 4th ward",
     "why": "the scanner's point for the compositor's comma. Kim Torp reads the "
            "forename Asabel; the image prints Asahel and the committed reading stands",
     "reread": "Pierce, — a tail below the e",
     "second_reading": "Pierce, Asabel, blacksmith, S. Water st. b Lake and Randolph "
                      "sts, house Lake st. 4th ward",
     "second_reading_bucket": "agrees", "entry": "n1844_e1435"},
    {"as_read": "Pierce. Royal,",
     "reading": "Pierce, Royal,",
     "surname": "Pierce", "leaf": 61, "leaf_px": [1564, 2912],
     "word_box": "154,2630,318,2597", "separator_mark": "point",
     "separator": True,
     "reads": "Pierce, Royal, cooper",
     "why": "a round point where the format sets a comma — and the Pierce three lines "
            "above carries a comma, so the two are set differently on one page",
     "reread": "Pierce. — a point, and no tail at this magnification",
     "second_reading": "Pierce, Royal, cooper",
     "second_reading_bucket": "identical", "entry": "n1844_e1436"},
    {"as_read": "Pike. Daniel,",
     "reading": "Pike, Daniel,",
     "surname": "Pike", "leaf": 61, "leaf_px": [1564, 2912],
     "word_box": "156,2679,280,2642", "separator_mark": "comma",
     "separator": True,
     "reads": "Pike, Daniel, laborer, hnuse North \"Water st. near Franklin st",
     "why": "the scanner's point for the compositor's comma",
     "reread": "Pike, — the tail is clear",
     "second_reading": "Pike, Daniel, laborer, house North Water st. near Franklin st",
     "second_reading_bucket": "agrees", "entry": "n1844_e1437"},
    {"as_read": "Rhiner. Henry,",
     "reading": "Rhines, Henry,",
     "surname": "Rhines", "leaf": 62, "leaf_px": [1564, 2912],
     "word_box": "116,2446,293,2410", "separator_mark": "comma",
     "separator": True,
     "reads": "Rhines, Henry, deputy sheriff, h Lasalle st. b Lake and Randolph",
     "why": "the terminal s read as an r, and a comma read as a point",
     "reread": "Rhines, — the last letter is an s, and the mark carries a tail",
     "second_reading": "Rhines, Henry, deputy sheriff, h Lasalle st. b Lake and "
                      "Randolph",
     "second_reading_bucket": "agrees", "entry": "n1844_e1482"},
    {"as_read": "iRuss. John,",
     "reading": "Russ, John,",
     "surname": "Russ", "leaf": 63, "leaf_px": [1564, 2912],
     "word_box": "125,2259,266,2225", "separator_mark": "point",
     "separator": True,
     "reads": "Russ, John, teamster, house cor Clinton and Madison",
     "why": "a speck in the left margin read as an i, and a round point where the "
            "format sets a comma",
     "reread": "Russ. — nothing before the R but a margin mark, and a point after",
     "second_reading": "Russ, John, teamster, house cor Clinton & Madison",
     "second_reading_bucket": "agrees", "entry": "n1844_e1532"},
    {"as_read": "Simpson. John,",
     "reading": "Simpson, John,",
     "surname": "Simpson", "leaf": 65, "leaf_px": [1564, 2912],
     "word_box": "119,1966,321,1922", "separator_mark": "comma",
     "separator": True,
     "reads": "Simpson, John, mason, house Canal st. b Adams and Jackson sts",
     "why": "the scanner's point for the compositor's comma, over a stain that runs "
            "under the line",
     "reread": "Simpson, — a tail, and the stain sits below it",
     "second_reading": "Simpson, John, mason, house Canal st. b Adams and Jackson sts",
     "second_reading_bucket": "identical", "entry": "n1844_e1625"},
    {"as_read": "Stockton. John,",
     "reading": "Stockton, John,",
     "surname": "Stockton", "leaf": 67, "leaf_px": [1564, 2912],
     "word_box": "137,1108,345,1073", "separator_mark": "comma",
     "separator": True,
     "reads": "Stockton, John, carpenter, h Illinois st. b Pine and Sand sts",
     "why": "the scanner's point for the compositor's comma",
     "reread": "Stockton, — a comma, tail below the n",
     "second_reading": "Stockton, John, carpenter, h Illinois st, P Pine and Sand sts",
     "second_reading_bucket": "agrees", "entry": "n1844_e1711"},
    {"as_read": "Sturtevan.t. Noah,",
     "reading": "Sturtevant, Noah,",
     "surname": "Sturtevant", "leaf": 67, "leaf_px": [1564, 2912],
     "word_box": "135,1842,370,1803", "separator_mark": "comma",
     "separator": True,
     "reads": "Sturtevant, Noah, painter, at J. I. Dow's, h Market st",
     "why": "a point set INSIDE the surname, between its n and its t, and the real "
            "separator read as a point as well. The image prints Sturtevant whole and "
            "a comma after it",
     "reread": "Sturtevant, — no stop inside the word, and a tail on the mark after it",
     "second_reading": "Sturtevant, Noah, painter, at J.I. Dow's. h Market st",
     "second_reading_bucket": "agrees", "entry": "n1844_e1725"},
    {"as_read": "Taylor. Solomon,",
     "reading": "Taylor, Solomon,",
     "surname": "Taylor", "leaf": 68, "leaf_px": [1564, 2912],
     "word_box": "121,1022,290,975", "separator_mark": "comma",
     "separator": True,
     "reads": "Taylor, Solomon, boot and shoemaker, 152^ Lake st. house West Water st. "
              "b Randolph and Washington sts , (See card)",
     "why": "the scanner's point for the compositor's comma",
     "reread": "Taylor, — the tail runs under the r",
     "second_reading": "Taylor, Solomon, boot & shoemaker, 152 ½ Lake st. house West "
                      "Water st. b Randolph & Washington sts",
     "second_reading_bucket": "agrees", "entry": "n1844_e1757"},
    {"as_read": "Van Dre/er, E.",
     "reading": "Van Drezer, E.",
     "surname": "Van Drezer", "leaf": 69, "leaf_px": [1564, 2912],
     "word_box": "135,920,237,887", "separator_mark": "comma",
     "separator": True,
     "reads": "Van Drezer, E. Eagle Tavern. Dearborn st",
     "why": "not a broken surname at all: Van Drezer is two words on the page, as Van "
            "Sickle and Van Vlack are, and only its z was set as a solidus. The comma "
            "after it is printed",
     "reread": "Van Drezer, — the fourth letter of Drezer is a z, and a comma follows",
     "second_reading": "Van Drezer, E. Eagle Tavern, Dearborn st",
     "second_reading_bucket": "agrees", "entry": "n1844_e1803"},
    {"as_read": "Ward. James,",
     "reading": "Ward, James,",
     "surname": "Ward", "leaf": 70, "leaf_px": [1564, 2912],
     "word_box": "106,449,256,413", "separator_mark": "comma",
     "separator": True,
     "reads": "Ward, James, mason, house Randolph st",
     "why": "the scanner's point for the compositor's comma",
     "reread": "Ward, — a comma, tail below the d",
     "second_reading": "Ward, James, mason, house Randolph st",
     "second_reading_bucket": "identical", "entry": "n1844_e1843"},
    {"as_read": "Warring. Klias,",
     "reading": "Warring, Elias,",
     "surname": "Warring", "leaf": 70, "leaf_px": [1564, 2912],
     "word_box": "108,927,319,881", "separator_mark": "comma",
     "separator": True,
     "reads": "Warring, Elias, teamster, house b Wells and Frankin sts",
     "why": "a comma read as a point, and the forename's E read as a K — the two arms "
            "of the E joined to its stem by a heavy inking",
     "reread": "Warring, Elias — a tail on the mark, and the forename opens with an E",
     "second_reading": "Warring, Elias, teamster, house b Wells and Frankin sts",
     "second_reading_bucket": "agrees", "entry": "n1844_e1853"},
    {"as_read": "Welch. William,",
     "reading": "Welch, William,",
     "surname": "Welch", "leaf": 70, "leaf_px": [1564, 2912],
     "word_box": "110,1433,284,1398", "separator_mark": "comma",
     "separator": True,
     "reads": "Welch, William, laborer, h Clark st. b N. Water and Kirfzie sts",
     "why": "the scanner's point for the compositor's comma",
     "reread": "Welch, — a short tail under the h",
     "second_reading": "Welch, William, laborer, h Clark st. b N. Water & Kinzie sts",
     "second_reading_bucket": "agrees", "entry": "n1844_e1864"},
    {"as_read": "s Went worth, Geo. W.",
     "reading": "Wentworth, Geo. W.",
     "surname": "Wentworth", "leaf": 70, "leaf_px": [1564, 2912],
     "word_box": "68,1905,112,1866", "separator_mark": "comma",
     "separator": True,
     "reads": "Wentworth, Geo. W. nst. editor Chicago Democrat, res U. S. Hotel",
     "why": "one surname set as two words, with a margin speck read as an s before it. "
            "The image prints Wentworth closed up and a comma after it",
     "reread": "Wentworth, — one word, and the speck stands off in the margin",
     "second_reading": "Wentworth, Geo. W., ast. editor Chicago Democrat, res U.S. "
                      "Hotel",
     "second_reading_bucket": "agrees", "entry": "n1844_e1872"},
    {"as_read": "Wliite. Christopher,",
     "reading": "White, Christopher,",
     "surname": "White", "leaf": 70, "leaf_px": [1564, 2912],
     "word_box": "117,2413,284,2379", "separator_mark": "point",
     "separator": True,
     "reads": "White, Christopher, at Turner's livery stable",
     "why": "the h read as l-i, and a round point where the format sets a comma",
     "reread": "White. — an h, and a point with no tail",
     "second_reading": "White, Christopher, at Turner's livery stable",
     "second_reading_bucket": "agrees", "entry": "n1844_e1881"},
    {"as_read": "White. Isaac,",
     "reading": "White, Isaac,",
     "surname": "White", "leaf": 70, "leaf_px": [1564, 2912],
     "word_box": "118,2506,279,2471", "separator_mark": "comma",
     "separator": True,
     "reads": "White, Isaac, butcher at Reynold's",
     "why": "the scanner's point for the compositor's comma",
     "reread": "White, — a tail below the e",
     "second_reading": "White, Isaac, butcher at Reynold's",
     "second_reading_bucket": "identical", "entry": "n1844_e1883"},
    {"as_read": "Woi thinglnm, Wm.",
     "reading": "Worthingham, Wm.",
     "surname": "Worthingham", "leaf": 71, "leaf_px": [1564, 2912],
     "word_box": "107,2564,206,2532", "separator_mark": "comma",
     "separator": True,
     "reads": "Worthingham, Wm. mason, h Monroe st. b State .md Clark st",
     "why": "one surname set as two words, with the r lost and the ha read as ln. The "
            "image prints Worthingham whole, and a comma after it",
     "reread": "Worthingham, — one word, r and h both there, and a comma",
     "second_reading": "Worthingham, Wm., mason, h Monroe st b State & Clark st",
     "second_reading_bucket": "agrees", "entry": "n1844_e1937"},
    {"as_read": "Gill. Edmund,",
     "reading": "Gill, Edmund,",
     "surname": "Gill", "leaf": 73, "leaf_px": [1564, 2912],
     "word_box": "107,834,214,799", "separator_mark": "point",
     "separator": True,
     "reads": "Gill, Edmund, tailor, house Ohio st. b Clark and Dearborn sts",
     "why": "a round point where the format sets a comma",
     "reread": "Gill. — a point, square on the baseline",
     "second_reading": "Gill, Edmund, tailor, house Ohio st. b Clark & Dearborn sts",
     "second_reading_bucket": "identical", "entry": "n1844_e1981"},
]

SURNAME_REREAD_BY_11 = (
    "T-0987 stretch 11, a second reading off a fresh crop of the same word box at a "
    "different magnification, taken in a shuffled order so the first pass could not "
    "be carried down the page. Where the two passes disagreed the row says so and "
    "the separator is left undecided.")
for _row in SURNAME_IMAGE_REPAIRS_STRETCH_11:
    _row["reread_by"] = SURNAME_REREAD_BY_11
SURNAME_IMAGE_REPAIRS += SURNAME_IMAGE_REPAIRS_STRETCH_11

# THE MARGIN'S SPECKS ARE NOT PART OF THE NAME (T-1023)
#
# T-1018 refused five entries as `empty_prefix`: the reading begins at the trade or
# mid-word, so there is no name to cap the comma span to, and capping would set
# `surname` to `''` — which `crosswalk_norris_1844.py` skips WITHOUT SAYING SO. Five
# men would leave the town's reach in silence. One of the five, `<'ady, Dennis S.`,
# was read off the page image by T-0987 stretch 10 and stands in OVERRUN_HEALED.
# This is the other four, and two more of the same class the overrun test never saw.
#
# THE DAMAGE IS AT THE HEAD OF THE LINE, WHERE THIS SCAN'S LEFT MARGIN COLLECTS INK.
# `clean_head()` already drops a speck that stands apart from the surname — a stray
# quote, a bullet, a lone letter and a space. It cannot drop one the scanner WELDED
# to the first letter (`vButterfield`, `iStrail`, `llageman`), and it cannot restore
# a capital the speck ate (`* '.ilhoun` for Calhoun). Either way the entry is filed
# under a name the volume does not print.
#
# READ AGAINST THE SECOND HAND, NOT OFF THE IMAGE, and the row says which. T-0987
# stretch 10 cropped its 16 surnames from the page image because the second hand and
# the OCR DISAGREED and something had to break the tie. Here they do not disagree:
# the OCR keeps every letter of the surname but the first, the second hand prints the
# whole word, and the volume's own alphabetical run brackets it on both sides — the
# `Calhoun, Alvin` set one line above, the `Hageman, F.` and `Hageman, ——` set one and
# two lines below, four spelled Butterfields around a fifth, `Stowe` above `Strang`.
# Three witnesses that agree do not need a fourth. Where they had NOT agreed, this
# table would not be the instrument; the image would.
#
# THE REPAIR MOVES THE READING ONLY. `quote` and `normalized.as_printed` keep the
# damage, exactly as REPAIRS and SURNAME_IMAGE_REPAIRS do, and the claim states both
# readings in `normalized.surname_repair`. `--self-test` fails if a row stops matching
# exactly one entry, or matches one whose surname it does not change.
MARGIN_SURNAME_REPAIRS = [
    {"as_read": "vButterfield,", "reading": "Butterfield,", "surname": "Butterfield",
     "why": "a speck welded to the B. clean_head drops a lone letter that stands "
            "apart from the name; this one has no space after it, so the surname "
            "read `vButterfield` and no Butterfield in the volume is spelled so",
     "brackets": "Butterfit'd, Wm. one line above and Butlerworih one line below — the "
                 "run is Butterfield, and four of them stand on this page",
     "file": "1844directory.txt", "line": 304,
     "second_reading": "Butterfield, Carver, printer of the Prairie Farmer, 112 Lake st"},
    {"as_read": "* '.ilhoun,", "reading": "Calhoun,", "surname": "Calhoun",
     "why": "the C eaten by a speck in the margin. clean_head strips `* '.` and the "
            "surname read `ilhoun`, so the John Calhoun who printed the Chicago "
            "Democrat was filed under a name that is not one",
     "brackets": "Calhoun, Alvin one line above and Calighan one line below — the "
                 "alphabetical run admits no other word here",
     "file": "1844directory.txt", "line": 309,
     "second_reading": "Calhoun, John, printer, house State st b Wash and Madison sts"},
    {"as_read": "llageman,", "reading": "Hageman,", "surname": "Hageman",
     "why": "the H set as two l's — its stems read and its crossbar lost. The "
            "surname read `llageman`, which sorts nowhere near the H's",
     "brackets": "Haeni one line above, and Hageman, F. and Hageman, —— one and two "
                 "lines below, both spelled",
     "file": "1844directory.txt", "line": 812,
     "second_reading": "Hageman, Christopher, grocer, N. Water st. b Clark & Dearborn"},
    {"as_read": "v; Smith,", "reading": "Smith,", "surname": "Smith",
     "why": "a speck and a semicolon in the margin ahead of a surname that is "
            "otherwise whole. clean_head drops a lone letter followed by a space; "
            "`v;` is a letter followed by a point, so the surname read `v; Smith`",
     "brackets": "Smith, Andrew one line above and Smith, Benjamin one line below — "
                 "the Smith run, and this entry prints Smith with it",
     "file": "1844dir2.txt", "line": 521,
     "second_reading": "Smith, Abial, printer, Dem. Office, res lake Street House"},
    {"as_read": "iStrail,", "reading": "Strail,", "surname": "Strail",
     "why": "a speck welded to the S, as with Butterfield above — no space, so "
            "clean_head cannot see it and the surname read `iStrail`",
     "brackets": "Stowe, W. H. one line above and Strang one line below; and the "
                 "second hand's own Casey entry names `Isaac Strail's` as an address",
     "file": "1844dir2.txt", "line": 602,
     "second_reading": "Strail, Isaac, dry goods & groceries, Clark st b S. Water & Lake"},
]

MARGIN_SURNAME_WHY = (
    "The head of the printed line carries a mark from this scan's left margin — "
    "welded to the first letter, or standing where the first letter was. The quote "
    "keeps it and the reading does not.")


SURNAME_IMAGE_SOURCE = IMAGE_SOURCE
SURNAME_REREAD_BY = ("T-0987 stretch 10, read off the leaf image cropped on the word "
                     "box recorded with the row, against the second hand rather than "
                     "on its say-so.")


def repair_surname(text: str):
    """Lift a surname the scanner destroyed, BEFORE the head is cleaned or split, so
    the comma walk and the firm test both see the name the page prints. Returns
    (text, repair record or None) — the caller keeps the damage in `quote`."""
    stripped = text.lstrip()
    for row in SURNAME_IMAGE_REPAIRS:
        if stripped.startswith(row["as_read"]):
            return stripped.replace(row["as_read"], row["reading"], 1), {
                "as_read": row["as_read"],
                "reading": row["reading"],
                "surname": row["surname"],
                "why": row["why"],
                # The LETTERS are always documented — they are on the page. The
                # SEPARATOR is not always: three entries (T-0987 stretch 11) print no
                # mark at all between surname and forename, and the comma this reading
                # supplies is the format's, not the compositor's. Those rows say so.
                "confidence": row.get("confidence", "documented"),
                "separator_mark": row.get("separator_mark"),
                "evidence": {
                    "source": SURNAME_IMAGE_SOURCE,
                    "coordinate_space": COORDINATE_SPACE,
                    "leaf": row["leaf"],
                    "leaf_px": row["leaf_px"],
                    "word_box": row["word_box"],
                    "reads": row["reads"],
                    "reread": row["reread"],
                    "reread_by": row.get("reread_by", SURNAME_REREAD_BY),
                    "second_reading": row["second_reading"],
                },
                "ticket": "T-0987",
            }
    for row in MARGIN_SURNAME_REPAIRS:
        if stripped.startswith(row["as_read"]):
            return stripped.replace(row["as_read"], row["reading"], 1), {
                "as_read": row["as_read"],
                "reading": row["reading"],
                "surname": row["surname"],
                "why": row["why"],
                # DOCUMENTED. Every letter of the reading is printed somewhere the
                # row names — in the OCR itself but the first, in the second hand
                # whole, and in the volume's own neighbours. Nothing here is supplied
                # by the format, so there is no separator to grade (see above).
                "confidence": "documented",
                "evidence": {
                    "source": REPAIR_SOURCE,
                    "file": "data/research/genealogytrails/text/" + row["file"],
                    "line": row["line"],
                    "reads": row["second_reading"],
                    "and_the_volume_itself": row["brackets"],
                    "why_not_the_image": (
                        "The second hand, the OCR's own surviving letters and the "
                        "alphabetical run agree. The page image is what breaks a "
                        "TIE between the two hands (T-0987 stretch 10); there is "
                        "no tie here."),
                },
                "ticket": "T-1023",
            }
    return text, None


def repair_welded_of(head):
    """Lift a `of` the scanner welded into its neighbour, so the prefix walk can
    see the stop word. Returns (head, repair record or None) — the caller keeps
    the damaged text in `quote` and `as_printed`."""
    for row in WELDED_OF:
        if head.startswith(row["surname"]) and row["as_read"] in head:
            return head.replace(row["as_read"], row["reading"], 1), {
                "as_read": row["as_read"],
                "reading": row["reading"],
                "why": "The scanner welded the partnership `of` into the token beside "
                       "it, so the entry read as its own firm rather than as a partner "
                       "giving his residence; the quote keeps the damage.",
                "evidence": {
                    "source": REPAIR_SOURCE,
                    "file": "data/research/genealogytrails/text/" + row["file"],
                    "line": row["line"],
                    "reads": row["second_reading"],
                },
                "ticket": "T-1013",
            }
    return head, None


def repair_conj_ampersand(head):
    """Lift an ampersand the scanner set as `<fc`, `6c` or `it`, BEFORE the prefix
    walk and the firm test, so a partnership is read as one. Returns (head, repair
    record or None) — the caller keeps the damaged text in `quote` and `as_printed`.

    Matched on the whole printed span, never on the conjunction alone: see
    CONJ_AMPERSAND for why the loose rule is the wrong one."""
    for row in CONJ_AMPERSAND:
        if head.startswith(row["span"]):
            evidence = {
                "and_the_same_volume_prints_the_partnership": {
                    "claim": row["same_volume"][0],
                    "reads": row["same_volume"][1],
                    "note": "Norris sets the ampersand correctly on this line, so the "
                            "firm is ruled on the book's own second printing of it.",
                },
                "second_hand": {
                    "source": REPAIR_SOURCE,
                    "file": "data/research/genealogytrails/text/" + row["file"],
                    "line": row["line"],
                    "reads": row["second_reading"],
                },
            }
            if row.get("second_hand_disagrees"):
                evidence["and_where_the_second_hand_disagrees"] = row["second_hand_disagrees"]
            if row.get("also_lifts"):
                evidence["this_row_also_lifts"] = row["also_lifts"]
            return head.replace(row["span"], row["reading"], 1), {
                "as_read": row["as_read"],
                "reading": "&",
                "span_as_read": row["span"],
                "span_reading": row["reading"],
                "printed_page": row["printed_page"],
                "why": "The scanner set this firm's ampersand as %r, so the firm test "
                       "never fired and the partnership read as a man whose surname was "
                       "the whole firm; the quote keeps the damage." % row["as_read"],
                "evidence": evidence,
                "ticket": "T-1021",
            }
    return head, None


def apply_repair(norm):
    """Repair a garbled forename READING in place, and say so. Returns the row."""
    for row in REPAIRS:
        if norm["surname"] == row["surname"] and norm["given"] == row["as_read"]:
            norm["given"] = row["reading"]
            norm["printed_name"] = norm["surname"] + ", " + row["reading"]
            norm["given_repair"] = {
                "as_read": row["as_read"],
                "reading": row["reading"],
                "why": "The printed forename as the scanner set it carries characters "
                       "no compositor did; the quote keeps them and the reading does not.",
                "evidence": {
                    "source": REPAIR_SOURCE,
                    "file": "data/research/genealogytrails/text/" + row["file"],
                    "line": row["line"],
                    "reads": row["second_reading"],
                },
                "ticket": "T-0695",
            }
            return row
    for row in IMAGE_REPAIRS:
        if norm["surname"] == row["surname"] and norm["given"] == row["as_read"]:
            norm["given"] = row["reading"]
            norm["printed_name"] = norm["surname"] + ", " + row["reading"]
            evidence = {
                "source": IMAGE_SOURCE,
                "image": "https://archive.org/download/generaldirectory19norr/page/"
                         "leaf%d.jpg" % row["leaf"],
                "leaf_px": row["leaf_px"],
                "word_box": row["word_box"],
                "coordinate_space": COORDINATE_SPACE,
                "reads": row["reads"],
                "read_a_second_time": {"by": REREAD_BY, "reads": row["reread"]},
            }
            if row["second_reading"]:
                evidence["and_the_second_hand_agrees"] = row["second_reading"]
            else:
                evidence["the_second_hand_cannot_help"] = (
                    "Kim Torp reads this token '(can't read)'. The page image is the "
                    "only witness, which is what UNREPAIRED said it would take.")
            norm["given_repair"] = {
                "as_read": row["as_read"],
                "reading": row["reading"],
                "why": row["why"],
                "evidence": evidence,
                "ticket": "T-0903",
            }
            return row
    return None


# THE TURNED LINE THE SCANNER UN-INDENTED (T-1023)
#
# Norris sets an entry too long for the measure by turning it and INDENTING the tail,
# and `build_claims` reads that indent: a line beginning with two spaces belongs to
# the entry above. One line in the volume is a turned tail with no indent, because the
# scan's left margin dropped ink into the space the compositor left:
#
#     Adams, R. E. W, physician, corner of Clark and Lake streets,-
#     . -house Clark street (See card)
#
# Read as its own entry it became n1844_e0009 — a man whose surname is "house Clark
# street (See card)", which is how he reached `identity_master.json` as
# `id_street_house_clark`. It is also why R. E. W. Adams has no address: the `house`
# that opens his residence is on the line the reading threw away.
#
# ONE LINE, NAMED, NOT A RULE. The volume was swept for the class (every unindented
# line in leaves 31-75 whose head reads lower-case after `clean_head`) and outside
# Norris's own prose, which SKIP already drops, this is the only one; the rest are
# margin specks welded to a capital, which MARGIN_SURNAME_REPAIRS reads. A general
# rule — "a line that cannot begin a name is a turned line" — would have to be
# measured against 2,073 entries before it could be trusted, and it would buy exactly
# this one line. So the boundary rule is UNCHANGED and the exception is a row with a
# citation, which `--self-test` holds to the text.
#
# THE ID IS KEPT. n1844_e0009 is cited from `identity_master.json`,
# `grading_proposal.json` and the second-hand comparison; ids are allocated by
# position, so folding the line away would renumber all 2,064 entries after it. The
# tail is JOINED to the entry above — which is what makes the address land — and the
# id stays, carrying a claim that says what it is and holds no name. The crosswalk
# passes over it by the surname test, as before, but no longer in silence: it now
# names every claim it sets aside and why (see crosswalk_norris_1844.py).
TURNED_LINES = {
    (31, 34): {
        "joins": "n1844_e0008",
        "why": "the turned tail of the Adams, R. E. W entry above it, un-indented "
               "because the scanner read ink in the margin where the indent is. "
               "The entry as printed is one line and its turn.",
        "evidence": {
            "source": REPAIR_SOURCE,
            "file": "data/research/genealogytrails/text/1844directory.txt",
            "line": 33,
            "reads": "Adams, R.E.W. physician, corner of Clark and Lake sts, "
                     "house Clark st",
            "and_the_volume_itself": "the line above ends in a comma and a rule, "
                                     "which is the compositor's turn, and the tail "
                                     "carries no name of its own",
        },
        "ticket": "T-1023",
    },
}


def build_claims():
    claims, warnings = [], []
    n = repaired = 0
    for leaf in range(FIRST_LEAF, LAST_LEAF + 1):
        lines = leaf_lines(leaf)
        printed = leaf + LEAF_TO_PRINTED
        skip = SKIP.get(leaf, ())
        entries = []  # (first_line, last_line)
        for i, line in enumerate(lines, 1):
            if i in skip:
                continue
            if i <= 3 and header_like(line):
                continue
            if line.startswith("  "):
                if entries:
                    entries[-1][1] = i
                else:
                    warnings.append("leaf %d line %d: a turned line with no entry above it"
                                    % (leaf, i))
                continue
            entries.append([i, i])
        for first, last in entries:
            n += 1
            raw = "\n".join(lines[first - 1:last])
            turned = TURNED_LINES.get((leaf, first))
            tail = TURNED_LINES.get((leaf, last + 1))
            read_lines = lines[first - 1:last]
            if tail is not None:
                # The turn belongs to THIS entry: read the two together, so the
                # address the tail opens lands. Its own claim keeps its id below.
                # THE TAIL'S OWN MARGIN INK IS DROPPED FROM THE READING and kept in
                # the quote, exactly as clean_head does at the head of an entry —
                # `. -house Clark street` joined raw would put a hyphen in front of
                # `house`, and PLACE refuses a hyphenated one (it is the guard that
                # keeps `boarding-house` from opening an address), so the residence
                # would not land even after the join.
                raw = raw + "\n" + lines[last]
                read_lines = read_lines + [clean_head(lines[last])]
            flat = re.sub(r"\s+", " ", raw.replace("-\n", "")).strip()
            read_flat = re.sub(r"\s+", " ",
                               "\n".join(read_lines).replace("-\n", "")).strip()
            if turned is not None:
                # A tail with no name of its own. It is read with the entry above and
                # is not a person; the claim exists so the id keeps its place and says
                # out loud what the line is.
                norm = {"printed_name": None, "surname": None, "given": None,
                        "firm": False, "occupation": None, "address": None,
                        "turned_line": turned}
            else:
                norm = split_entry(read_flat)
                if apply_repair(norm):
                    repaired += 1
                if tail is not None:
                    norm["turned_line_joined"] = {
                        "line": last + 1, "reads": lines[last].strip(),
                        "why": tail["why"], "evidence": tail["evidence"],
                        "ticket": tail["ticket"]}
            norm["as_printed"] = flat
            after = (leaf, first) >= ADDENDA_FROM
            norm["section"] = "addenda" if after else "directory"
            cid = "n1844_e%04d" % n
            # T-1113. The street this entry prints is refused an address, and the claim
            # carries the reason rather than leaving a reader to guess at a null.
            if cid in ADDRESS_REFUSED:
                cls, why = ADDRESS_REFUSED[cid]
                norm["address_refused"] = {"class": cls, "why": why,
                                           "rule": ADDRESS_REFUSED_NOTE}
            claims.append({
                "id": cid,
                "kind": "turned_line" if turned is not None else (
                    "business" if norm["firm"] else "person"),
                "reading": "transcription_mediated",
                "quote": raw,
                "normalized": norm,
                "locator": {
                    "text_file": "norris_1844_leaf_%03d.txt" % leaf,
                    "lines": [first, last + 1 if tail is not None else last],
                    "page": "norris_1844_leaf_%03d" % leaf,
                    "printed_page": printed,
                },
                "describes_date": "1844",
                "entities": [norm["printed_name"]] if norm["printed_name"] else [],
                "town_finding": False,
                "notes": None,
            })
    if repaired != len(REPAIRS) + len(IMAGE_REPAIRS):
        warnings.append("%d of %d garbled-forename repairs fired — see --self-test"
                        % (repaired, len(REPAIRS) + len(IMAGE_REPAIRS)))
    return claims, warnings


DOC = ("GENERATED by tools/read_norris_1844.py --build out of the committed page text in "
       "data/research/directories/text/. Hand-edit and --check says so. Every entry in the "
       "directory proper and its addenda, one claim each, quote verbatim off the OCR and the "
       "reading beside it. 1844, not 1835 — see the crosswalk.")


def payload(claims):
    people = sum(1 for c in claims if c["kind"] == "person")
    return {
        "schema": 1,
        "_doc": DOC,
        "generated_by": "tools/read_norris_1844.py --build",
        "source_id": "norris_directory_1844",
        "corpus": {
            "item": "generaldirectory19norr",
            "url": "https://archive.org/details/generaldirectory19norr",
            "what": "University of Illinois scan of the T. F. Bohan republication (1903) of "
                    "J. W. Norris, General Directory and Business Advertiser of the City of "
                    "Chicago for the Year 1844 (Chicago: Ellis & Fergus). 132 leaves.",
            "committed": True,
            "how": "The word coordinates of archive.org's OCR (generaldirectory19norr_djvu.xml) "
                   "give each line its left edge; a line set in more than 45/400 inch from the "
                   "page's own margin is a turned line and is committed with two leading spaces. "
                   "Nothing else about the text is touched.",
        },
        "reading_note": "transcription_mediated throughout: this is archive.org's OCR of the "
                        "printed page, machine-read and not checked against the image by eye. "
                        "The damage is left in every quote on purpose — 'Win.' for 'Wm.', "
                        "'ISickalls' for 'Nickalls' — because a tidied quote cannot be found "
                        "again. The repair, where one is safe, is in normalized. A forename the "
                        "scanner garbled beyond a compositor's alphabet is repaired against Kim "
                        "Torp's independent transcription of the same directory, and the repaired "
                        "entry carries normalized.given_repair with both readings and the citation "
                        "(T-0695); where that second hand cannot read the token either, the damage "
                        "stands.",
        "counts": {"claims": len(claims), "person": people, "business": len(claims) - people,
                   "given_repairs": sum(1 for c in claims
                                        if "given_repair" in c["normalized"]),
                   "address_refusals": sum(1 for c in claims
                                           if "address_refused" in c["normalized"]),
                   "places_of_business": sum(1 for c in claims
                                          if "place_of_business" in c["normalized"])},
        "claims": claims,
    }


def self_test():
    """The repair table against the book: every row fires exactly once, nothing
    is repaired that was not garbled, and nothing garbled is left unaccounted."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import name_agreement as na
    claims, _ = build_claims()
    fired = []
    for row in REPAIRS:
        hits = [c for c in claims
                if c["normalized"].get("given_repair", {}).get("as_read") == row["as_read"]
                and c["normalized"]["surname"] == row["surname"]]
        if len(hits) != 1:
            fired.append("repair %s/%r fired on %d entries, not 1 — the reading moved "
                         "under the table" % (row["surname"], row["as_read"], len(hits)))
            continue
        norm = hits[0]["normalized"]
        if not na.garbled(row["as_read"]):
            fired.append("repair %s/%r repairs a forename that is not garbled"
                         % (row["surname"], row["as_read"]))
        if na.garbled(norm["given"]):
            fired.append("repair %s/%r leaves the reading garbled: %r"
                         % (row["surname"], row["as_read"], norm["given"]))
        if row["as_read"] not in norm["as_printed"] or row["as_read"] not in hits[0]["quote"]:
            fired.append("repair %s/%r tidied the quote — the damage must stand there"
                         % (row["surname"], row["as_read"]))
    # T-0903. The page-image repairs, held to the same three rules as the eleven
    # above — fires exactly once, does not repair a reading that was already sound,
    # and does not tidy the quote — plus one the second hand cannot be asked for: an
    # image repair must name the leaf its reading was cropped from.
    for row in IMAGE_REPAIRS:
        hits = [c for c in claims
                if c["normalized"].get("given_repair", {}).get("as_read") == row["as_read"]
                and c["normalized"]["surname"] == row["surname"]]
        if len(hits) != 1:
            fired.append("image repair %s/%r fired on %d entries, not 1 — the reading "
                         "moved under the table" % (row["surname"], row["as_read"], len(hits)))
            continue
        norm = hits[0]["normalized"]
        if row["as_read"] == row["reading"]:
            fired.append("image repair %s/%r is a no-op" % (row["surname"], row["as_read"]))
        if row["as_read"] not in norm["as_printed"] or row["as_read"] not in hits[0]["quote"]:
            fired.append("image repair %s/%r tidied the quote — the damage must stand there"
                         % (row["surname"], row["as_read"]))
        ev = norm["given_repair"]["evidence"]
        if not ev.get("image"):
            fired.append("image repair %s/%r cites no page image, which is the only "
                         "thing that makes it checkable" % (row["surname"], row["as_read"]))
        # T-0900. A page image is only checkable if the reader can find the LINE on it.
        # The word box and the leaf's own pixel size are what make the crop reproducible,
        # and quoting one leaf's size for another is exactly the mistake this catches.
        if not re.fullmatch(r"\d+,\d+,\d+,\d+", row.get("word_box") or ""):
            fired.append("image repair %s/%r cites no word box, so the crop it was read "
                         "from cannot be reproduced" % (row["surname"], row["as_read"]))
        px = row.get("leaf_px") or []
        if len(px) != 2 or not all(isinstance(v, int) and 500 < v < 6000 for v in px):
            fired.append("image repair %s/%r states no plausible leaf size, which is the "
                         "coordinate space its word box is in"
                         % (row["surname"], row["as_read"]))
        elif row["word_box"]:
            l, b, r_, t = (int(v) for v in row["word_box"].split(","))
            if not (0 <= l < r_ <= px[0] and 0 <= t < b <= px[1]):
                fired.append("image repair %s/%r has a word box outside its own leaf: "
                             "%s is not inside %dx%d"
                             % (row["surname"], row["as_read"], row["word_box"], *px))
        if not (row.get("reread") or "").strip():
            fired.append("image repair %s/%r was read by one hand only — T-0900 requires "
                         "a second reading off the image"
                         % (row["surname"], row["as_read"]))

    # The scanner's W is letters only, so na.garbled() is blind to it: nothing above
    # would ever name this class. Assert it by hand instead of trusting the sweep.
    for c in claims:
        norm = c["normalized"]
        as_read = norm.get("given_repair", {}).get("as_read", norm.get("given")) or ""
        if SCANNER_W in as_read and (norm["surname"], as_read) not in \
                {(r["surname"], r["as_read"]) for r in IMAGE_REPAIRS}:
            fired.append("%s reads a forename carrying the scanner's %r with no row in "
                         "IMAGE_REPAIRS — garbled() cannot see this class"
                         % (c["id"], SCANNER_W))
        if SCANNER_W in (norm.get("given") or ""):
            fired.append("%s still reads the scanner's %r after repair"
                         % (c["id"], SCANNER_W))

    known = {(r["surname"], r["as_read"]) for r in REPAIRS}
    known |= {(r["surname"], r["as_read"]) for r in IMAGE_REPAIRS}
    known |= {(r["surname"], r["as_read"]) for r in UNREPAIRED}
    for c in claims:
        norm = c["normalized"]
        as_read = norm.get("given_repair", {}).get("as_read", norm.get("given"))
        if norm.get("given") and na.garbled(as_read or "") and (norm["surname"], as_read) not in known:
            fired.append("%s reads a garbled forename %r with no row in REPAIRS or "
                         "UNREPAIRED" % (c["id"], as_read))
    # T-1013. THE FIRM TEST, AND THE THREE ENTRIES THAT LOOK LIKE FIRMS AND ARE NOT.
    #
    # `& Co.` appears in 124 entries and most of them are people naming somebody
    # else's firm, so the test rests entirely on the marker standing INSIDE the
    # leading name run. Three partner-residence entries lost the space around the
    # `of` that ends that run — two to a boundary OF_STOP still sees, one to
    # character damage WELDED_OF lifts — and each would read as its own company
    # if the walk ran past the preposition. They are asserted by their printed
    # text, so a re-read that moves a line fails here instead of quietly minting
    # four men as firms.
    by_printed = {}
    for c in claims:
        by_printed.setdefault(c["normalized"]["as_printed"], []).append(c)
    for printed in ("Eddy, Ira B.-of Eddy & Co. res Michigan avenue",
                    "Smith, George, of'G. S. & Co. res City Hotel",
                    "Raymond, B. W. ofJ5. W. R. & Co. h Wash, b Clark and Lasalle"):
        hits = by_printed.get(printed, [])
        if len(hits) != 1:
            fired.append("the welded-`of` entry %r is in the reading %d times, not 1 — "
                         "the text moved under the test" % (printed[:40], len(hits)))
        elif hits[0]["normalized"]["firm"]:
            fired.append("%s reads %r as a firm: the walk ran past the partnership "
                         "`of` and made a man his own company"
                         % (hits[0]["id"], printed[:40]))
    for row in WELDED_OF:
        hits = [c for c in claims
                if c["normalized"].get("head_repair", {}).get("as_read") == row["as_read"]]
        if len(hits) != 1:
            fired.append("welded-`of` repair %r fired on %d entries, not 1"
                         % (row["as_read"], len(hits)))
            continue
        if row["as_read"] not in hits[0]["quote"]:
            fired.append("welded-`of` repair %r tidied the quote — the damage must "
                         "stand there" % row["as_read"])
        if OF_STOP.search(row["as_read"]):
            fired.append("welded-`of` repair %r repairs a token OF_STOP already sees, "
                         "so the table is doing the regex's work" % row["as_read"])
    # T-1021. THE SCANNER'S AMPERSAND, AND THE TRAP EITHER SIDE OF IT.
    #
    # CONJ_AMPERSAND reads `<fc`, `6c` and `it` as `&` in seven NAMED SPANS. The whole
    # risk is the other direction: `it` is an English word and `6c` is how this scanner
    # sets `&c.`, so a rule that read those tokens wherever they stood would weld
    # `stoves it` into a partnership and mint firms out of grocers' stock lists. The
    # table cannot do that — it matches a whole span at the head of the entry — and
    # this asserts it from both ends.
    #
    # FIRST, EACH ROW. Exactly one entry, ruled a firm, named as the row reads it, and
    # the damage still standing in the quote. Each row's ruling rests on Norris's OWN
    # second printing of the partnership, so that line is asserted present with a real
    # ampersand in it: if a re-read moves it, the evidence for the repair is gone and
    # this fails rather than the repair quietly carrying on without it.
    conj_by_id = {c["id"]: c for c in claims}
    for row in CONJ_AMPERSAND:
        hits = [c for c in claims
                if c["normalized"].get("conj_repair", {}).get("span_as_read") == row["span"]]
        if len(hits) != 1:
            fired.append("conj-ampersand repair %r fired on %d entries, not 1"
                         % (row["span"], len(hits)))
            continue
        c = hits[0]
        if row["span"] not in c["quote"]:
            fired.append("conj-ampersand repair %r tidied the quote — the damage must "
                         "stand there" % row["span"])
        if not c["normalized"]["firm"]:
            fired.append("%s carries the conj-ampersand repair %r and still reads as a "
                         "person — the firm test did not fire on the lifted `&`"
                         % (c["id"], row["span"]))
        if c["normalized"]["printed_name"] != row["reading"]:
            fired.append("%s is repaired to %r and names itself %r"
                         % (c["id"], row["reading"], c["normalized"]["printed_name"]))
        witness = conj_by_id.get(row["same_volume"][0])
        if witness is None:
            fired.append("the same-volume witness %s for %r is not in the reading"
                         % (row["same_volume"][0], row["span"]))
        elif " & " not in witness["normalized"]["as_printed"]:
            fired.append("the same-volume witness %s for %r no longer prints a plain "
                         "ampersand, so the ruling has lost its evidence"
                         % (row["same_volume"][0], row["span"]))
    # SECOND, THE TRAP. Every entry in the volume that carries one of these tokens
    # ANYWHERE is enumerated here with what it must read as, and only the seven may
    # carry the repair. Nineteen of them are the trap in person: `&c.` closing a
    # grocer's stock list, and the conjunction standing inside a partner's or a
    # clerk's entry — `of P. 6c Dpdge`, `at P. Fund 6c Co.'s` — where the man, not the
    # firm, is the entry. All of them must stay people.
    conj_seen = {c["id"] for c in claims if c["normalized"].get("conj_repair")}
    conj_want = set()
    for row in CONJ_AMPERSAND:
        conj_want |= {c["id"] for c in claims
                      if c["normalized"].get("conj_repair", {}).get("span_as_read") == row["span"]}
    for cid in sorted(conj_seen - conj_want):
        fired.append("%s carries a conj-ampersand repair with no row in CONJ_AMPERSAND"
                     % cid)
    if len(conj_seen) != len(CONJ_AMPERSAND):
        fired.append("%d entries carry a conj-ampersand repair and the table has %d rows"
                     % (len(conj_seen), len(CONJ_AMPERSAND)))
    for cid, (firm, printed) in CONJ_UNTOUCHED.items():
        c = conj_by_id.get(cid)
        if c is None:
            fired.append("%s is named in CONJ_UNTOUCHED and is not in the reading" % cid)
            continue
        if c["normalized"]["as_printed"] != printed:
            fired.append("%s is named in CONJ_UNTOUCHED and its printed text moved — the "
                         "witness is stale: %r" % (cid, c["normalized"]["as_printed"][:60]))
        if c["normalized"].get("conj_repair"):
            fired.append("%s carries one of these tokens in a stock list, an address or "
                         "a partner's entry and the repair reached it: %r"
                         % (cid, printed[:60]))
        if c["normalized"]["firm"] != firm:
            fired.append("%s must read firm=%s and reads firm=%s — the conjunction "
                         "rule moved a man into a firm or a firm out of one: %r"
                         % (cid, firm, c["normalized"]["firm"], printed[:60]))
    tokened = {c["id"] for c in claims
               if re.search(r"<fc|6c|&c|\bit\b", c["normalized"]["as_printed"])}
    for cid in sorted(tokened - set(CONJ_UNTOUCHED) - conj_want):
        fired.append("%s prints a scanner conjunction and has no row in CONJ_AMPERSAND "
                     "or CONJ_UNTOUCHED: %r"
                     % (cid, conj_by_id[cid]["normalized"]["as_printed"][:60]))
    # The two readings of a firm cannot disagree: the name is the run the test was
    # decided on, so a business whose name carries no firm marker is a contradiction.
    for c in claims:
        if c["normalized"]["firm"] and not FIRM.search(c["normalized"]["printed_name"] + ","):
            fired.append("%s is read as a business but its name %r carries no firm "
                         "marker" % (c["id"], c["normalized"]["printed_name"]))
    # T-1018. THE 69 ENTRIES WHOSE NAME RAN PAST THE END OF THE NAME, BY CLASS.
    #
    # The cap is right for 46 and would do damage in 23, so the four refusals are
    # asserted BY ENTRY ID, not by count: the whole risk of this repair is that a
    # re-read moves a line, a refusal stops firing, and the entry is quietly capped
    # to `Went` or to `''`. An entry that leaves its class fails here.
    #
    # `empty_prefix` is the one the acceptance names, because capping to an empty
    # surname is SILENT — crosswalk_norris_1844.py skips a claim with no surname and
    # says nothing — so it is asserted twice: by id, and by the surname it keeps.
    by_id = {c["id"]: c for c in claims}
    for cid, want in OVERRUN_CLASSES.items():
        c = by_id.get(cid)
        if c is None:
            fired.append("%s is named in OVERRUN_CLASSES and is not in the reading" % cid)
            continue
        got = c["normalized"].get("name_overrun")
        got = "repaired" if (got or {}).get("repaired") else (got or {}).get("refused")
        if got != want:
            fired.append("%s was %s by T-1018 and now reads %r — the line moved under "
                         "the classifier" % (cid, want, got))
    for cid, was in OVERRUN_HEALED.items():
        c = by_id.get(cid)
        if c is None:
            fired.append("%s is named in OVERRUN_HEALED and is not in the reading" % cid)
        elif c["normalized"].get("name_overrun"):
            fired.append("%s was %s by T-1018 and healed at the source — by the "
                         "surname read off the page image, or by the ampersand "
                         "CONJ_AMPERSAND lifts; it reads past the end of its name again"
                         % (cid, was))
    seen = {c["id"] for c in claims if c["normalized"].get("name_overrun")}
    for cid in sorted(seen - set(OVERRUN_CLASSES)):
        fired.append("%s reads past the end of its name with no row in OVERRUN_CLASSES: "
                     "%r" % (cid, by_id[cid]["normalized"]["name_overrun"]))
    for cid, want in OVERRUN_CLASSES.items():
        if want == "empty_prefix" and cid in by_id and not by_id[cid]["normalized"]["surname"]:
            fired.append("%s was capped to an empty surname, which drops it out of the "
                         "crosswalk with nothing said" % cid)
    # T-0987 stretch 5. The three places the split cut at the wrong character, each
    # asserted on a line Norris printed and then swept over the whole reading, because
    # a rule proved on one entry and broken everywhere else reads green.
    SPLIT_CASES = {
        # the printed comma closes the name
        # …its trade is empty since T-1114 moved the street into place_of_business, so
        # the street it was asserted on is asserted there instead, just below.
        "n1844_e0098": ("Morris", None),
        "n1844_e0791": ("Abraham", "Methodist clergymen"),
        # …and the comma set with no space after it is the same comma
        "n1844_e0367": ("T. B", "soap and oil factory"),
        "n1844_e1918": ("Maihew", "ship carpenter"),
        # …and a suffix or an initial standing after it is not the end of the name
        "n1844_e0235": ("Thomas, jr", None),
        # the abbreviation is lower case and a man's initial is not
        "n1844_e0113": ("Adam", "shoemaker, at J. B. Mitchell's"),
        "n1844_e0135": ("A", "clerk at H. O. Stone's"),
        # …and T-1022's own line, the one the ticket was written on
        "n1844_e1936": ("D. L", "at H. Norton & Co.'s"),
    }
    for cid, (given, occupation) in SPLIT_CASES.items():
        c = by_id.get(cid)
        if c is None:
            fired.append("%s is named in SPLIT_CASES and is not in the reading" % cid)
            continue
        got = c["normalized"]
        if got.get("given") != given:
            fired.append("%s reads a forename of %r, not %r — the split moved"
                         % (cid, got.get("given"), given))
        if occupation is not None and got.get("occupation") != occupation:
            fired.append("%s reads a trade of %r, not %r — the split moved"
                         % (cid, got.get("occupation"), occupation))
    if (by_id.get("n1844_e0098", {}).get("normalized", {}).get("place_of_business")
            != "Illinois street, b Dearborn and Wolcott sts"):
        fired.append("n1844_e0098 reads a place of business of %r — the printed comma "
                     "that closes the name, or the place cut, moved"
                     % (by_id.get("n1844_e0098", {}).get("normalized", {})
                        .get("place_of_business")))
    for c in claims:
        n = c["normalized"]
        if re.match(r"^[A-Z]\.?\s", n.get("address") or ""):
            fired.append("%s begins its address at %r — PLACE cut at a capital, which "
                         "is a man's initial in this volume and never Norris's own "
                         "abbreviation" % (c["id"], (n["address"] or "")[:24]))
        if re.search(r",\S", n.get("given") or ""):
            fired.append("%s reads a forename of %r — the comma inside it was set "
                         "without a space and still closes the name"
                         % (c["id"], n["given"]))

    # T-0987 stretch 10. Every surname read off the page image must still be reading
    # the line it was read off. The ratchet is the same as the forename repairs': a
    # row that stops matching exactly one entry is a re-map that moved a line, and it
    # fails the build rather than writing the wrong surname onto the wrong man.
    for row in SURNAME_IMAGE_REPAIRS:
        hit = [c for c in claims
               if (c["normalized"].get("surname_repair") or {}).get("as_read")
               == row["as_read"]]
        if len(hit) != 1:
            fired.append("the surname repair %r fires on %d entries, not 1"
                         % (row["as_read"], len(hit)))
            continue
        if hit[0]["normalized"].get("surname") != row["surname"]:
            fired.append("%s reads a surname of %r after the repair, not %r"
                         % (hit[0]["id"], hit[0]["normalized"].get("surname"),
                            row["surname"]))
        if row["as_read"] not in hit[0]["quote"]:
            fired.append("%s no longer quotes %r — the damage the repair asserts is "
                         "not in the committed text" % (hit[0]["id"], row["as_read"]))
    # T-1023. The margin repairs carry the same ratchet, and one more: the row must
    # say something. A row whose `as_read` still matched but whose surname the reading
    # already got right would be a repair that repairs nothing, and the next reader
    # would trust it.
    for row in MARGIN_SURNAME_REPAIRS:
        hit = [c for c in claims
               if (c["normalized"].get("surname_repair") or {}).get("as_read")
               == row["as_read"]]
        if len(hit) != 1:
            fired.append("the margin surname repair %r fires on %d entries, not 1"
                         % (row["as_read"], len(hit)))
            continue
        if hit[0]["normalized"].get("surname") != row["surname"]:
            fired.append("%s reads a surname of %r after the margin repair, not %r"
                         % (hit[0]["id"], hit[0]["normalized"].get("surname"),
                            row["surname"]))
        if row["as_read"] not in hit[0]["quote"]:
            fired.append("%s no longer quotes %r — the damage the margin repair "
                         "asserts is not in the committed text"
                         % (hit[0]["id"], row["as_read"]))
        if row["as_read"].lstrip().startswith(row["reading"]):
            fired.append("the margin surname repair %r changes nothing — the reading "
                         "was already right" % (row["as_read"],))
        # AND THE SPELLING IS THE SECOND HAND'S, NOT THE ROW'S. Without this a row
        # could carry any name at all: `surname`, `reading` and the claim would all
        # agree with each other and with nothing on the page.
        if row["reading"].rstrip(",") != row["surname"]:
            fired.append("the margin surname repair %r reads %r and calls the surname "
                         "%r" % (row["as_read"], row["reading"], row["surname"]))
        if not row["second_reading"].startswith(row["surname"] + ","):
            fired.append("the second hand at %s:%d does not open with %r — the margin "
                         "repair is spelling a name its own citation does not"
                         % (row["file"], row["line"], row["surname"]))
        # The second hand has to be quotable where the row says it is.
        try:
            line = open(os.path.join(ROOT, "data/research/genealogytrails/text",
                                     row["file"]), encoding="utf-8").read(
                                         ).splitlines()[row["line"] - 1]
        except (OSError, IndexError):
            line = None
        if line is None or line.strip() != row["second_reading"]:
            fired.append("%s:%d does not read %r — the second hand the margin repair "
                         "cites has moved" % (row["file"], row["line"],
                                              row["second_reading"]))

    # T-1023. The turned line is an exception to the boundary rule, held to the text
    # on both sides: the tail must still be where the row says, the entry above must
    # have swallowed it, and the tail's own claim must hold no name — because the one
    # thing this ruling must never do is mint a man out of an address.
    for (leaf, line_no), row in TURNED_LINES.items():
        lines = leaf_lines(leaf)
        tail = [c for c in claims
                if (c["normalized"].get("turned_line") or {}).get("joins")]
        tail = [c for c in tail if c["locator"]["lines"] == [line_no, line_no]
                and c["locator"]["page"] == "norris_1844_leaf_%03d" % leaf]
        if len(tail) != 1:
            fired.append("leaf %d line %d is named a turned line and %d claim(s) say "
                         "so" % (leaf, line_no, len(tail)))
            continue
        t = tail[0]
        if t["kind"] != "turned_line":
            fired.append("%s is a turned line and is filed as a %r, which is what the "
                         "crosswalk and the identity layer read" % (t["id"], t["kind"]))
        if t["normalized"]["surname"] or t["normalized"]["printed_name"]:
            fired.append("%s is a turned line and carries a name — the ruling has "
                         "minted a man out of an address" % t["id"])
        if t["entities"]:
            fired.append("%s is a turned line and reaches the identity layer as %r"
                         % (t["id"], t["entities"]))
        if t["id"] != "n1844_e%04d" % (int(row["joins"][-4:]) + 1):
            fired.append("%s is the turned line of %s, which is not the claim above it"
                         % (t["id"], row["joins"]))
        above = [c for c in claims if c["id"] == row["joins"]]
        if not above:
            fired.append("%s is named as the entry a turned line joins and is not in "
                         "the reading" % row["joins"])
        elif above[0]["locator"]["lines"][1] != line_no:
            fired.append("%s does not read through line %d — the turned line it was "
                         "joined to is loose again" % (row["joins"], line_no))
        elif lines[line_no - 1].strip() not in above[0]["quote"]:
            fired.append("%s does not quote the turned line at leaf %d line %d"
                         % (row["joins"], leaf, line_no))

    for row in SURNAME_UPHELD:
        hit = [c for c in claims
               if c["normalized"].get("surname") == row["surname"]
               and row["as_read"] in c["quote"]]
        if len(hit) != 1:
            fired.append("the upheld surname %r stands on %d entries, not 1 — the "
                         "committed reading it upholds has moved"
                         % (row["surname"], len(hit)))

    # T-1022. THE CASE RULE IS PRICED BY RE-READING, NOT BY A REMEMBERED NUMBER.
    # The whole volume is read a second time through the superseded case-blind
    # pattern and the two readings are diffed. Two things are asserted, and the
    # second is the one that makes the first mean anything: that a known number of
    # entries move, and that EVERY entry which moves does so because its case-blind
    # address began at a one-letter initial — the defect itself. An entry moving for
    # any other reason would be a trade, not a repair, and fails here.
    global PLACE
    kept = PLACE
    try:
        PLACE = PLACE_CASE_BLIND
        case_blind = {c["id"]: c["normalized"] for c in build_claims()[0]}
    finally:
        PLACE = kept
    moved = [c for c in claims
             if (c["normalized"].get("occupation"), c["normalized"].get("address"))
             != (case_blind.get(c["id"], {}).get("occupation"),
                 case_blind.get(c["id"], {}).get("address"))]
    if len(moved) != CASE_RULE_MOVES:
        fired.append("the case rule moves %d entries, not the %d it is priced at — "
                     "re-measure it and rewrite the band above PLACE_CASE_BLIND "
                     "rather than editing this number to pass"
                     % (len(moved), CASE_RULE_MOVES))
    for c in moved:
        was = case_blind.get(c["id"], {}).get("address") or ""
        if not re.match(r"^[A-Z]\.?\s", was):
            fired.append("%s moves under the case rule and its case-blind address "
                         "was %r, which does not begin at a one-letter initial — the "
                         "rule changed a reading for some reason other than the "
                         "defect, and that is a trade, not a repair" % (c["id"], was[:32]))

    # T-1114. `b` IS BETWEEN — PRICED THE SAME WAY, by re-reading the whole volume with
    # the superseded pattern and requiring every entry that moves to move for THIS
    # defect: under the old rule its address began at a `b`, and under no other reading
    # does one. The 11 that come out of it holding a residence are asserted separately,
    # because they are the half of the repair a bare count cannot show.
    kept = PLACE
    try:
        PLACE = PLACE_B_AS_PLACE
        b_as_place = {c["id"]: c["normalized"] for c in build_claims()[0]}
    finally:
        PLACE = kept
    b_moved = [c for c in claims
               if (c["normalized"].get("occupation"), c["normalized"].get("address"))
               != (b_as_place.get(c["id"], {}).get("occupation"),
                   b_as_place.get(c["id"], {}).get("address"))]
    if len(b_moved) != B_RULE_MOVES:
        fired.append("the between rule moves %d entries, not the %d it is priced at — "
                     "re-measure it and rewrite the band above PLACE_B_AS_PLACE rather "
                     "than editing this number to pass" % (len(b_moved), B_RULE_MOVES))
    for c in b_moved:
        was = b_as_place.get(c["id"], {}).get("address") or ""
        if not re.match(r"^b\b", was):
            fired.append("%s moves under the between rule and its old address was %r, "
                         "which does not begin at a `b` — the rule changed a reading "
                         "for some reason other than the defect" % (c["id"], was[:32]))
    recovered = [c for c in b_moved if c["normalized"].get("address")]
    if len(recovered) != B_RULE_RECOVERS_ADDRESS:
        fired.append("%d of the moved entries keep an address, not the %d priced — the "
                     "residences the old cut buried are the point of the repair"
                     % (len(recovered), B_RULE_RECOVERS_ADDRESS))
    for c in recovered:
        if not PLACE.match((c["normalized"]["address"] + " ")):
            fired.append("%s keeps an address of %r, which does not open at one of "
                         "Norris's own place marks" % (c["id"], c["normalized"]["address"]))

    # T-1114. THE PLACE OF BUSINESS, PRICED WITH THE RULE OFF. It reads the trade line
    # and nothing else, so the one thing that must not move is `address`: a business
    # street reaching a residence field is the provenance defect T-1113 refused five
    # entries to prevent, and it would be invisible downstream.
    global PLACE_OF_BUSINESS_RULE
    PLACE_OF_BUSINESS_RULE = False
    try:
        no_place = {c["id"]: c["normalized"] for c in build_claims()[0]}
    finally:
        PLACE_OF_BUSINESS_RULE = True
    carried = [c for c in claims if c["normalized"].get("place_of_business")]
    if len(carried) != PLACE_OF_BUSINESS_ENTRIES:
        fired.append("%d entries carry a place of business, not the %d priced — re-measure "
                     "it and rewrite the band above PLACE_OF_BUSINESS_RULE rather than "
                     "editing this number to pass"
                     % (len(carried), PLACE_OF_BUSINESS_ENTRIES))
    for c in claims:
        n, was = c["normalized"], no_place.get(c["id"], {})
        if n.get("address") != was.get("address"):
            fired.append("%s changes its address when the place-of-business rule is on — "
                         "the rule reads the trade line and may not touch a residence"
                         % c["id"])
        letters = lambda t: re.sub(r"[^0-9A-Za-z]", "", t or "")
        joined = letters(n.get("occupation")) + letters(n.get("place_of_business"))
        if n.get("place_of_business") and joined != letters(was.get("occupation")):
            fired.append("%s loses text at the place cut: %r + %r is not the trade line "
                         "%r it was read from" % (c["id"], n.get("occupation"),
                                                  n.get("place_of_business"),
                                                  was.get("occupation")))
        if n.get("place_of_business") and not n.get("place_of_business_note"):
            fired.append("%s carries a place of business with no note saying it is not a "
                         "residence" % c["id"])

    # T-1113. THE STREET RULE IS PRICED THE SAME WAY — re-read with it off, and every
    # entry that moves must have had a street inside its forename. The named readings
    # are asserted too, because a price with nothing behind it only says a number
    # changed; these say WHICH lines, and what each one now reads.
    global STREET_RULE
    STREET_RULE = False
    try:
        no_street = {c["id"]: c["normalized"] for c in build_claims()[0]}
    finally:
        STREET_RULE = True
    shape = lambda n: (n.get("given"), n.get("occupation"), n.get("place_of_business"),
                       n.get("address"))
    street_moved = [c for c in claims
                    if shape(c["normalized"]) != shape(no_street.get(c["id"], {}))]
    if sorted(c["id"] for c in street_moved) != sorted(STREET_IN_FORENAME):
        fired.append("the street rule moves %s, not the %d entries it is priced at — "
                     "re-measure it and rewrite STREET_IN_FORENAME rather than editing "
                     "the table to pass"
                     % (sorted(c["id"] for c in street_moved), len(STREET_IN_FORENAME)))
    for c in street_moved:
        was = no_street.get(c["id"], {}).get("given") or ""
        tail = was.split()[-1].strip(" .,") if was.split() else ""
        if not tail or not re.search(r"\b%s\b\.?\s+(?:st|street|streets|sts|av|ave"
                                    r"|avenue|alley|road|lane|court)\b"
                                    % re.escape(tail), c["normalized"]["as_printed"],
                                    re.I):
            fired.append("%s moves under the street rule and its old forename ended "
                         "at %r, which the printed line does not follow with a street "
                         "designator — the rule changed a reading for some reason "
                         "other than the defect" % (c["id"], was))
    for cid, (given, occupation, place, address) in STREET_IN_FORENAME.items():
        c = by_id.get(cid)
        if c is None:
            fired.append("%s is named in STREET_IN_FORENAME and is not in the reading"
                         % cid)
            continue
        got = c["normalized"]
        if (got.get("given"), got.get("occupation"), got.get("place_of_business"),
                got.get("address")) != (given, occupation, place, address):
            fired.append("%s reads given=%r trade=%r place=%r address=%r, not "
                         "%r/%r/%r/%r — the street rule moved"
                         % (cid, got.get("given"), got.get("occupation"),
                            got.get("place_of_business"), got.get("address"),
                            given, occupation, place, address))
    # …and the refusals hold. A refusal that quietly starts landing an address is the
    # provenance defect the band exists to prevent, so it fails the build.
    STREET_TAIL = re.compile(r"\b(?:st|street|sts|streets|avenue|av)\b\.?", re.I)
    for cid, (cls, why) in ADDRESS_REFUSED.items():
        c = by_id.get(cid)
        if c is None:
            fired.append("%s is named in ADDRESS_REFUSED and is not in the reading"
                         % cid)
            continue
        got = c["normalized"]
        if got.get("address") is not None:
            fired.append("%s is refused an address and now carries %r — %s"
                         % (cid, got["address"], why))
        if (got.get("address_refused") or {}).get("class") != cls:
            fired.append("%s does not carry its refusal on the claim" % cid)
        if cls != "printed_line_short" and not STREET_TAIL.search(
                "%s %s" % (got.get("occupation") or "", got.get("place_of_business") or "")):
            fired.append("%s is refused because its street belongs to a firm, and its "
                         "trade line no longer prints a street at all — the refusal is "
                         "answering a line that moved" % cid)
    if fired:
        for line in fired:
            print("  " + line, file=sys.stderr)
        print("norris 1844 --self-test: %d case(s) failed" % len(fired), file=sys.stderr)
        return 1
    from collections import Counter
    tally = Counter(OVERRUN_CLASSES.values())
    print("norris 1844 --self-test: %d forename repairs hold against the second hand "
          "and %d against the page image (each read twice, on a reproducible crop), "
          "%d left damaged on purpose"
          % (len(REPAIRS), len(IMAGE_REPAIRS), len(UNREPAIRED)))
    print("norris 1844 --self-test: %d printed lines hold the three split rules, and "
          "no entry in %d begins an address at a capital or keeps an unspaced comma "
          "inside a forename" % (len(SPLIT_CASES), len(claims)))
    print("norris 1844 --self-test: the case rule re-read against the whole volume — "
          "%d of %d entries move and every one of them had a case-blind address "
          "beginning at a one-letter initial" % (CASE_RULE_MOVES, len(claims)))
    print("norris 1844 --self-test: the between rule re-read against the whole volume — "
          "%d entries move, every one of them had an address beginning at a `b`, and "
          "%d of them recover the residence the old cut had buried"
          % (B_RULE_MOVES, B_RULE_RECOVERS_ADDRESS))
    print("norris 1844 --self-test: %d entries carry a place of business read out of the "
          "trade line, none of them moves an address, and every one says on the claim "
          "that it is not a residence" % PLACE_OF_BUSINESS_ENTRIES)
    print("norris 1844 --self-test: %d surnames read off the page image on their own "
          "word box, %d of them carrying the name separator away with them; %d places the second hand is "
          "wrong and the committed reading stands"
          % (len(SURNAME_IMAGE_REPAIRS),
             sum(1 for r in SURNAME_IMAGE_REPAIRS if r.get("separator")),
             len(SURNAME_UPHELD)))
    print("norris 1844 --self-test: the street rule re-read against the whole volume — "
          "%d entries move and every one of them had a street inside its forename; "
          "%d streets are refused an address and each says why on the claim"
          % (len(STREET_IN_FORENAME), len(ADDRESS_REFUSED)))
    print("norris 1844 --self-test: %d surnames lifted out of the margin's ink against "
          "the second hand and the volume's own alphabetical run, and %d turned line(s) "
          "the scanner un-indented read with the entry above rather than as a man"
          % (len(MARGIN_SURNAME_REPAIRS), len(TURNED_LINES)))
    print("norris 1844 --self-test: %d names read past the end of the name — %d capped "
          "at the prefix, %s, and %d healed at the source"
          % (len(OVERRUN_CLASSES) + len(OVERRUN_HEALED), tally["repaired"],
             ", ".join("%d refused %s" % (n, k) for k, n in sorted(tally.items())
                       if k != "repaired"), len(OVERRUN_HEALED)))
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    claims, warnings = build_claims()
    doc = payload(claims)
    if "--check" in sys.argv:
        got = json.load(open(OUT, encoding="utf-8"))
        if got != doc:
            print("norris 1844: the committed entries do not match the text — "
                  "regenerate with --build", file=sys.stderr)
            return 1
        print("norris 1844: %d entries, and they match the committed text" % len(claims))
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    for w in warnings:
        print("  warning:", w)
    print("norris 1844: %d entries (%d person, %d business) → %s"
          % (len(claims), doc["counts"]["person"], doc["counts"]["business"],
             os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
