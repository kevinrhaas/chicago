#!/usr/bin/env python3
"""Robert Fergus's *Directory of the City of Chicago, Illinois, for 1843* — read
entry by entry (T-0571).

`--build` reads the committed page text under
`data/research/directories/text/fergus_1843_page_00N.txt` and writes
`data/research/directories/claims/fergus_1843_directory_entries.json`.
`--check` rebuilds in memory and compares, so a hand-edit of the generated file
is caught the way `read_norris_1844.py` catches one; it also holds the per-page
counts declared in `coverage.json` to what the text actually yields, because a
declared page that quietly loses forty entries is exactly the hole coverage
exists to catch.

TWO SHAPES ON FOUR PAGES, and the segmenting rule is different for each because
the printer set them differently.

  Page 1, the BUSINESS DIRECTORY (lines 752-1204). Fergus groups these by trade
  under an ALL-CAPS heading and sets each card's subject in FULL CAPITALS at the
  head of its entry. So the heading is a line that shouts and ends in a stop, an
  entry begins where a line begins with a shouted name, and every other line is
  the turn of the entry above. The heading is carried onto the claim as
  `trade_heading`: it is the printer's own classification of the business and is
  worth more than anything a parser could infer from the prose.

  "Shouted" has to be defined carefully, because these cards list their partners
  and their eastern agents in the running prose and the transcription wraps them
  onto a line of their own: "J. R. Hall, Boston, agents", "W. Smith, Patrick
  Ballingall." both open a line with a capital. The head of a card is the leading
  run of tokens that are each an initial, an ampersand, or a word carrying two
  consecutive capitals — and it is a head only if at least one of those words
  does carry them. "C. McDONNELL" and "FREER & DeWOLF" are heads; "A. Rindge" and
  "J. Henry" are the middle of somebody's card.

  Pages 2-4, the ALPHABETICAL DIRECTORY. Fergus sets it in one alphabetical
  sequence broken by letter sections ("-A- Surnames", "H Surnames"). The web
  transcription this project holds wraps the long entries, and it does NOT
  indent the turn — so the indent trick that works for Norris is unavailable.
  The rule here is the directory's own organising principle instead: an entry
  begins where a line begins with a surname IN THE CURRENT LETTER SECTION. A
  turned line that opens with a capital opens with a place or a date — "Ill.,
  Nov. 25,1893, a. 80. ]" under A, "Feb. 22,1862" under B — and its initial is
  not the section's. Where the capital IS the section's letter and the head
  carries no comma, the entry grammar is absent too, and alphabetical order
  decides: `Cass` arriving after `Clarke & Co.` is the tail of that firm's
  address, not a new name.

  Seven times on page 2 the transcription runs a new entry onto the same line as
  the tail of the one before — "aged 84-6. Ballantine, David (B. & Sherman), ..."
  Those are cut mid-line and located with `spans`, which is what `spans` is for.
  Six more do it across a WRAP, where the tail is an obituary bracket closing on
  an age and the next entry follows it — "84-5-6] Cutmore, Henry, grocer" — and
  T-0987 stretch 13 cuts those the same way, giving the age back to the obituary
  above. See `OBITUARY_TAIL_RUN_ONS`.

1843 IS EIGHT YEARS LATE, and Fergus compiled it in 1896 out of the 1844 canvass.
Nothing here is an 1835 fact. Every claim carries `describes_date: "1843"`, and
the crosswalk is the only place a name in this volume may touch a person standing
in the scene of 1 July 1835.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
OUT = os.path.join(ROOT, "data/research/directories/claims/fergus_1843_directory_entries.json")
COVERAGE = os.path.join(ROOT, "data/research/directories/coverage.json")

PAGE = "fergus_1843_page_%03d"

# Page 1. The business directory and nothing else: the INTRODUCTORY, the civic
# and statistical account before it and the facsimile title-page after it are all
# prose or list-of-office shaped, and coverage.json says whose they are.
BUSINESS_FROM, BUSINESS_TO = 752, 1204

# The transcriber's own furniture, which appears on every page and is not Fergus.
FURNITURE = {"©2007 Kim Torp", "Genealogy Trails", "Back to the Index Page", "Surnames"}

SECTION = re.compile(r"^[-\s]*([A-Z])[-\s]*Surnames\s*$")
HEADING = re.compile(r"^[A-Z][A-Z&,\.\-' ]*\.$")
CAPS_RUN = re.compile(r"[A-Z]{2,}")
INITIAL = re.compile(r"^[A-Z][\.,\-]*$")
BRACKET = re.compile(r"\[[^\[\]]*\]")
FIRM = re.compile(r"\s&\s|&\s*Co\b|\bBrothers\b|\bHouse\b|\bMarket\b", re.I)
TITLES = {"mrs", "miss", "mr", "dr", "capt", "col", "rev", "gen", "maj", "jr", "sr", "sen"}
# Fergus's own abbreviation list, printed in his REMARKS: bet for between, res for
# residence, bds for boards. `cor` and `op.` are his too. The address begins at the
# first of them. Deliberately NOT `at`: "attorney at law" is a trade, and an `at`
# in the list cut sixteen hundred of them in half.
# `(?<!-)` because the compositor's HYPHEN is not a word boundary this rule may cut
# at (T-0987 stretch 5). `\b` holds on the far side of one, so `boarding-house`,
# `packing-house`, `poor-house` and Mark Beaubien's `light-house keeper` were each read
# as a trade ending in a hyphen and an address beginning "house …" — seven entries whose
# address was the tail of their own trade.
PLACE = re.compile(r"\b(?<!-)(?:res|bds|bet|cor|house|boards|residence|opp?|near|over)\.?\s", re.I)


def lines_of(page: int):
    with open(os.path.join(TEXT, PAGE % page + ".txt"), encoding="utf-8") as fh:
        return fh.read().splitlines()


def fold_surname(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def still_the_name(tok: str, toks, i: int) -> bool:
    """Is a comma-carrying token's comma one the name runs THROUGH?

    Three printed shapes say yes, and the volume sets all three:

      a suffix's own comma      `Bates, jr., John`  `Baumgarten, jr., Morris`
      a suffix standing after   `Bumpstead, Thomas, jr.`
      a comma between initials  `Stewart, E, A, watchmaker`  `Hamlin, E. H., Baptist`

    Everything else is the compositor closing the name and opening the trade,
    which is what `split_name` walks past when this returns False.
    """
    if tok.strip(".,'\"()").lower().strip(",") in TITLES:
        return True
    nxt = toks[i + 1] if i + 1 < len(toks) else ""
    if not nxt:
        return False
    return (nxt.strip(".,'\"()").lower() in TITLES
            or bool(re.fullmatch(r"[A-Z]", nxt.strip(".,"))))


def split_name(rest: str):
    """The leading run of name-shaped tokens after the surname comma.

    Stops at the first token that is lower-case or opens a parenthesis, which is
    where Fergus's trade begins: "Adams, Mrs. Maria, laundress" gives "Mrs.
    Maria"; "Allen, James Pierce (J. P A. & Co.) res 9 River" gives "James
    Pierce" and leaves the firm to the occupation.

    AND IT STOPS AT THE PRINTED COMMA (T-0987 stretch 5, the same defect
    stretch 4 fixed in `read_fergus_1839.py`). A capital and a count of four
    were the whole test, so the run walked straight past the comma the
    compositor set after the forenames and took the next capitalised word for
    another one: `Baumgarten, Maurice, Illinois, bet N. Dearborn and Wolcott`
    read a forename of "Maurice, Illinois" and left Illinois Street — the only
    street in the line — inside the name. A title or a suffix carries a comma
    of its own (`Bates, jr., John`), so its comma is not the one that closes
    the name.
    """
    given = []
    toks = rest.split()
    for i, tok in enumerate(toks):
        bare = tok.strip(".,'\"()").lower()
        if tok.startswith("("):
            break
        if bare in TITLES or re.fullmatch(r"[A-Z]", tok.strip(".,")) or (
                tok[:1].isupper() and len(given) < 4):
            # AND THE COMMA THE COMPOSITOR SET WITHOUT A SPACE AFTER IT is the same
            # comma: it sits inside a whitespace token, where the test below could
            # never see it. Keeping the comma on the kept half leaves the offset
            # `rest` is sliced at unchanged, so the trade comes back whole.
            inner = tok.find(",")
            if 0 <= inner < len(tok) - 1:
                given.append(tok[:inner + 1])
                break
            given.append(tok)
            if tok.rstrip(".").endswith(",") and not still_the_name(tok, toks, i):
                break
            continue
        break
    given_s = " ".join(given).strip(" ,.")
    return given_s, rest[len(" ".join(given)):].strip(" ,.")


# ---------------------------------------------------------------------------
# T-0987 stretch 12 — THE SEPARATOR THE COMPOSITOR SET AS A POINT.
#
# `split_entry` closes the surname at the first comma, because that is the format
# Fergus sets: `Surname, Given, trade, address`. Where the comma is not there the
# head runs on, and the surname this reading hands the crosswalk is not a surname
# at all — `Boyington. Charles H`, `Cook. George`, `Harding Charles`. The
# crosswalk reaches an 1835 person through the surname and nothing else, so a
# surname like that makes NO match and NO refusal: the entry leaves no trace in
# any pool this ticket counts. That is a hole in the denominator, and stretches 10
# and 11 measured the same hole in Norris 1844.
#
# TWENTY-SIX person entries in this volume carry a space inside their surname and
# are neither an institution, a real two-word name, nor the six `84-5-6] Cutmore`
# heads, which are a different defect and not this one. (Stretch 12 called those
# six a page-citation run-on. They are not: stretch 13 measured them and they are
# the obituary tail of the entry ABOVE, cut back to it below.) Twenty-five are
# repaired here and one is left alone.
#
# THE SECOND HAND. The committed text of this domain is K. Torp's 2007
# transcription on Genealogy Trails. This repository ALSO holds, under
# `data/research/books/text/fergus_26_29.txt`, the Internet Archive's own OCR of
# the printed volume — Fergus' Historical Series Nos. 26-29 bound in one, of which
# No. 28 IS this directory (source record `fergus_historical_series_26_29`). Two
# independent extractions of one printing, and neither was made from the other.
# Every row below carries what that second hand prints, verbatim with its own
# damage, so the comparison can be run again.
#
# WHAT THE TWO HANDS SAID, and the confidence follows it and is not chosen:
#
#   5  the printed volume sets a COMMA where this transcription sets a point
#      (Boyington, Goodwin, Graff, Houfe, Tarbox). The separator is DOCUMENTED:
#      the volume prints it, and Torp's point is this transcription's damage.
#   2  the printed volume sets a COMMA where this transcription sets NOTHING
#      (Harding, Seger). Also DOCUMENTED, and these two are the whole of the
#      no-separator class.
#  18  BOTH hands read a point. The surname is DOCUMENTED — two readings agree on
#      the letters — but that the point stands where the format sets a comma is
#      INFERRED, and the reason is stretch 10's and is stated again here: a
#      surname is never abbreviated, so a stop immediately after one cannot be an
#      abbreviation point. The five rows above are the corroboration that reading
#      had lacked: in five places out of twenty-three the second hand reads the
#      comma outright, so the point is a defect class in this printing and not a
#      punctuation Fergus chose.
#
# THE REPAIR MOVES THE READING ONLY. `quote` and `as_printed` keep the damage —
# a tidied quote cannot be found again — and every repaired claim states both
# readings in `normalized.surname_repair`. `--self-test` fails if a row stops
# matching exactly one entry, if a repaired entry stops reading its surname, or if
# a repair tidied a quote.
SECOND_HAND_SOURCE = "fergus_historical_series_26_29"
SECOND_HAND = (
    "The Internet Archive's OCR of the printed volume, committed at "
    "data/research/books/text/fergus_26_29.txt (archive.org item "
    "fergushistorical2629unse, the Allen County Public Library copy; No. 28 of "
    "Fergus' Historical Series IS this directory). Quoted verbatim, its own OCR "
    "damage left in, so the comparison re-runs.")

SURNAME_SEPARATOR_REPAIRS = [
    {"id": 'f1843_e0403', "as_read": 'Boyington. Charles H',
     "reading": 'Boyington, Charles H',
     "verdict": 'second_hand_comma', "confidence": 'documented',
     "second_hand": '3oyington, Ciiarles H.., <a])tain schooner CIkliIoUc^'},
    {"id": 'f1843_e1098', "as_read": 'Goodwin. Francis P',
     "reading": 'Goodwin, Francis P',
     "verdict": 'second_hand_comma', "confidence": 'documented',
     "second_hand": '<Jood\\vin, Francis \\\\. planemaker. res VV^ Lake'},
    {"id": 'f1843_e1109', "as_read": 'Graff. Peter',
     "reading": 'Graff, Peter',
     "verdict": 'second_hand_comma', "confidence": 'documented',
     "second_hand": 'Graflf, Peter, carpenter, res 3Ionroe. bet Clark and State'},
    {"id": 'f1843_e1326', "as_read": 'Houfe. Thomas',
     "reading": 'Houfe, Thomas',
     "verdict": 'second_hand_comma', "confidence": 'documented',
     "second_hand": "Houfc, Thomas, teamster, AA'm. Lill, bds .John Greenwood"},
    {"id": 'f1843_e2409', "as_read": 'Tarbox. C. F',
     "reading": 'Tarbox, C. F',
     "verdict": 'second_hand_comma', "confidence": 'documented',
     "second_hand": 'Tarbox, C. F., clerk, Orriligton Lunt, hds John B. iMitchcll'},
    {"id": 'f1843_e1204', "as_read": 'Harding Charles',
     "reading": 'Harding, Charles',
     "verdict": 'second_hand_supplies', "confidence": 'documented',
     "second_hand": 'Harding, Charles, captaio schooncu Ge7i. Thornton, bds Tremont House'},
    {"id": 'f1843_e2219', "as_read": 'Seger Joseph',
     "reading": 'Seger, Joseph',
     "verdict": 'second_hand_supplies', "confidence": 'documented',
     "second_hand": 'Seger, Jose])h, water carrier, res Dutch Settlement'},
    {"id": 'f1843_e0530', "as_read": 'Calighan. Mathew',
     "reading": 'Calighan, Mathew',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Calighan. ]\\Iathcw, carpenter, bds Edward Gavin'},
    {"id": 'f1843_e0553', "as_read": 'Carr. William',
     "reading": 'Carr, William',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Carr. AVilliam, sailor, res Canal, od Ward'},
    {"id": 'f1843_e0561', "as_read": 'Case. Elan',
     "reading": 'Case, Elan',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Ca^^e. Elan, carjtenter, Scoville & Gates'},
    {"id": 'f1843_e0690', "as_read": 'Constantine. Patrick',
     "reading": 'Constantine, Patrick',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": "<'onstantine. Patrick, laborer, res bet Michigan and Illinois. 5th Ward"},
    {"id": 'f1843_e0692', "as_read": 'Cook. George',
     "reading": 'Cook, George',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Cook. George, bartender, hds xVnierican Temperance House'},
    {"id": 'f1843_e0696', "as_read": 'Cook. Josiah P',
     "reading": 'Cook, Josiah P',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Cook. Josiah P.., baker, res ^Michigan ave'},
    {"id": 'f1843_e0702', "as_read": 'Cooley. Miss',
     "reading": 'Cooley, Miss',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Cooley. Miss, dress and cloak maker. 17.j Lake'},
    {"id": 'f1843_e0704', "as_read": 'Corbidge. John',
     "reading": 'Corbidge, John',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Corbidge. John, cutler and grinder. 11)7 Randolph'},
    {"id": 'f1843_e0954', "as_read": 'Fish. James P',
     "reading": 'Fish, James P',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Fish. James P., carpenter, res. Kinzie, east of Rush'},
    {"id": 'f1843_e1060', "as_read": 'Gauch. Jacob P',
     "reading": 'Gauch, Jacob P',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Gaueh. Jacob P., brewer, Indiana, bet Pine and Sand, res same'},
    {"id": 'f1843_e1245', "as_read": 'Heald. Alexander Hamilton',
     "reading": 'Heald, Alexander Hamilton',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'llcald. Alexander Hamilton, masoji. 1)ds Daniel Heald, ir.'},
    {"id": 'f1843_e1246', "as_read": 'Heald. jr',
     "reading": 'Heald, jr',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Ileald. jr., Daniel, mason. J'},
    {"id": 'f1843_e1256', "as_read": 'Herrick. Ira N.. contractor',
     "reading": 'Herrick, Ira N.. contractor',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Herrick. Ira X.. contractor, [d.. Park Manor, HI., Jan. 17, 1890'},
    {"id": 'f1843_e1341', "as_read": 'Howe. Fred. A',
     "reading": 'Howe, Fred. A',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Howe. Fred. A., jr., clerk, bds Frederick A. Howe'},
    {"id": 'f1843_e1630', "as_read": 'Lyman. Daniel',
     "reading": 'Lyman, Daniel',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": "Lyman. Daniel, miller, [died at Hyde I'ark, Aj^ril 10, 1882"},
    {"id": 'f1843_e1738', "as_read": 'Mann. J',
     "reading": 'Mann, J',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Mann. J., hatter, Israel Cyrus Stepliens'},
    {"id": 'f1843_e1858', "as_read": 'Munson. F. A',
     "reading": 'Munson, F. A',
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": 'Mimson. F. A., res Illinois Exchange, 192 Lake'},
    {"id": 'f1843_e1925', "as_read": "O'Neil. Michael",
     "reading": "O'Neil, Michael",
     "verdict": 'both_point', "confidence": 'inferred',
     "second_hand": "O'Xeil. Michael, carj)enter. res Dearborn, bet X. Water"},
]

# LEFT ALONE, and the reason is the second hand's and not a judgement about the
# entry. `Glansman. John, butcher, Western Market, cor N. Water and Clark` is the
# twenty-sixth, and it carries the same point as the eighteen. But the printed
# volume's OCR DROPPED THE HEAD OF THAT LINE: between `Gilson` and `Gleason` it
# prints only the line's tail, `AVater and Clark`, and no name. So there is no
# second reading of this separator to set against Torp's, and the one argument the
# eighteen rest on — two hands agreeing on the letters — is unavailable here.
# Repairing it would be assuming the class rather than reading it. It stays in the
# pool, uncounted, and this note says why.
SURNAME_SEPARATOR_LEFT_ALONE = [
    {"id": "f1843_e1088", "as_read": "Glansman. John",
     "why": "the second hand's OCR drops the head of this line and prints only its "
            "tail, `AVater and Clark`, so there is no second reading of the separator"},
    # AND ONE THAT IS NOT A NAME AT ALL. `Jan. 18, 1868, aged 77 1/4.` is the tail of
    # the obituary bracket on the entry above it, wrapped onto a line of its own by
    # the web transcription and segmented as an entry. It carries the run-on SHAPE and
    # none of the defect: there is no surname here to repair. It is a segmenting fault
    # and a different ticket's, and it is named here so the ratchet below does not have
    # to file it under institutions, which it is not.
    {"id": "f1843_e1434", "as_read": "Jan. 18",
     "why": "not an entry: the tail of the preceding entry's obituary bracket, wrapped "
            "onto its own line by the transcription and segmented as one. No surname to "
            "repair; a segmenting fault, recorded and left"},
]

# ---------------------------------------------------------------------------
# T-0987 stretch 13 — THE AGE THAT WAS READ AS A SURNAME.
#
# Stretch 12 filed this pool as "the page-citation run-on" and described it as a
# cross-reference Torp interpolates — `84-5-6] Cutmore`, six of them. MEASURED,
# THAT IS NOT WHAT THEY ARE, and this stretch says so before it repairs them.
# There is no cross-reference. Every one of the six is the TAIL OF THE OBITUARY
# BRACKET ON THE ENTRY ABOVE, wrapped onto the next line by the transcription and
# closed there before the next entry begins:
#
#   Cushing, Nathaniel Sawyer, house painter, ... [died, Lombard, Ill., May 13, 1889, aged
#   84-5-6] Cutmore, Henry, grocer. West Randolph, bet W Water and Canal
#
# So the digits are an AGE, they belong to the entry above, and the entry below
# begins after the bracket. It is the same defect `f1843_e1434` carries — the
# obituary tail wrapped onto a line of its own — with one difference that makes it
# worse: there the tail wrapped ALONE and became a nameless entry, while here the
# next entry follows it on the same line, so the tail is swallowed into a REAL
# person's head and that person's surname becomes `84-5-6 Cutmore`. Six people of
# the volume are unreachable by the crosswalk, which reaches an 1835 person through
# the surname and nothing else, and six obituaries lose their age.
#
# THE SEGMENTER ALREADY HAD THE ANSWER AND NEVER REACHED IT. `alpha_entries` cuts
# an entry mid-line and locates both halves with `spans` — the seven run-ons of
# page 2 are cut that way. These six never got there: the test for "does an entry
# begin on this line" strips leading non-letters before it looks (`lead`), so the
# line PASSES as the start of an entry and is then recorded from column 0, junk
# and all. The repair is to take the same cut the run-on path takes, at the end of
# the bracket, which puts the age back on the entry above and starts the new entry
# at its own surname. No new locator kind, no new claim, no change to any count
# `coverage.json` declares.
#
# THE SECOND HAND SETTLES IT, and is stretch 12's: the Internet Archive's OCR of
# the printed volume at `data/research/books/text/fergus_26_29.txt`. In ALL SIX it
# closes the age onto the obituary above and sets the next entry after it, so the
# reading below is `documented` in every row — two independent extractions of one
# printing agree on where the age belongs. Nothing was fetched for this stretch.
OBITUARY_TAIL_RUN_ONS = [
    {"id": 'f1843_e0754', "tail": '84-5-6]', "surname": 'Cutmore',
     "age_of": 'f1843_e0753', "age": '84-5-6',
     "second_hand": 'I  died,  Lombard.  111.,  May  13.  1889.  aged  84-5-0. '
                    'Cutraore,  Henry,  grocer.  West  liandolph,  bet  W  Water  and  Canal'},
    {"id": 'f1843_e1601', "tail": '84.]', "surname": 'Lindebner',
     "age_of": 'f1843_e1600', "age": '84',
     "second_hand": '[died.  Lake  Forest,  111.,  February  (J,  1892,  aged  84. '
                    'Lindebner,  Joseph,  tailor,  Edward  Manierre.  bds  same'},
    {"id": 'f1843_e1610', "tail": '74.]', "surname": 'Loomis',
     "age_of": 'f1843_e1609', "age": '74',
     "second_hand": '[died,  Paris,  France,  April  10,  1870,  aged  74. '
                    'Loomis.  Henry,  lumber  merchant,  cor  West  Water  and  I^andolph'},
    {"id": 'f1843_e1938', "tail": '71.]', "surname": 'Otis',
     "age_of": 'f1843_e1937', "age": '71',
     "second_hand": '[died,  Ann  Arbor,  Mich.,  January  23,  1S82,  aged  71. '
                    'r^tis,  Seth,  county  ])Oor-house  keeper       [died  April  27,  1847,  aged  70.'},
    {"id": 'f1843_e2310', "tail": '46]', "surname": 'Smith',
     "age_of": 'f1843_e2309', "age": '46',
     "second_hand": '[died.  Bureau  Co,.  111.,  October  2,  1862.  a.o-ed  46 '
                    "Smith,  Theophilus  AVa'sbington,  attorney  (S.  ct  Ballingall),  6  Clark"},
    {"id": 'f1843_e2676', "tail": '59]', "surname": 'Wright',
     "age_of": 'f1843_e2675', "age": '59',
     "second_hand": '[died,  Pbiladelpbia,  Pa..  Se])t.  2G,  1874,  aged  51). '
                    "\u25a0\\Vrigbt,  ^Irs.  Hulda,  M'id.  of  .Jobn,  IIG  3Iicbigan  ave,  s.-w.  cor  Madison"},
]

# The shape, so a SEVENTH cannot arrive unnoticed: a run of digits (with the
# hyphenated sixths Fergus sets for a part-year, `84-5-6`), an optional stop, and
# the bracket that closes the obituary above. `[Jackson Hall, 45 LaSalle ...` — the
# editorial bracket that IS its own entry — opens with a bracket and carries no
# digits before it, so it cannot match.
OBIT_TAIL = re.compile(r"^\s*\d[\d\-]*\s*\.?\](\s+)")


_REPAIR_BY_READ = {r["as_read"]: r for r in SURNAME_SEPARATOR_REPAIRS}
_OBIT_TAIL_BY_ID = {r["id"]: r for r in OBITUARY_TAIL_RUN_ONS}
_OBIT_TAIL_BY_AGE_OF = {r["age_of"]: r for r in OBITUARY_TAIL_RUN_ONS}


def repair_separator(body: str):
    """Lift a run-on surname before the comma is ever walked, or leave it alone.

    Returns `(body, row)`. Longest match first, so a row whose `as_read` is a
    prefix of another's cannot steal it.
    """
    for as_read in sorted(_REPAIR_BY_READ, key=len, reverse=True):
        if body.startswith(as_read):
            row = _REPAIR_BY_READ[as_read]
            return row["reading"] + body[len(as_read):], row
    return body, None


def split_entry(flat: str, shouted: bool):
    """name / occupation / address, best effort, out of one printed entry.

    Best effort is the honest word: nineteenth-century directory punctuation is
    not a grammar, `as_printed` carries the whole line, and `quote` carries it
    unedited. What the split is FOR is the crosswalk, which needs a surname and
    an initial and nothing else to be safe.
    """
    notes = [m.group(0)[1:-1].strip() for m in BRACKET.finditer(flat)]
    body = BRACKET.sub(" ", flat)
    body = re.sub(r"\s+", " ", body).strip(" ,.")
    # Fergus sets a handful of his own notes as a whole bracketed entry, in place
    # in the alphabet — "[Jackson Hall, 45 LaSalle, erected 1847 ...]". Stripping
    # the bracket leaves nothing, so the bracket IS the entry: read it as the body
    # and say so, rather than filing a claim with no name in it.
    editorial = not body and len(notes) == 1
    if editorial:
        body = notes[0]
    repair = None
    if shouted:
        # The business directory: the subject is the shouted run at the head.
        printed = shouted_head(body) or body.split(",")[0].strip(" ,.")
        rest = body[len(printed):].strip(" ,.")
        surname = given = None
        if not ("&" in printed or " AND " in printed):
            parts = [p for p in printed.split() if p.strip(".,")]
            if len(parts) >= 2:
                surname = parts[-1].strip(".,").title()
                given = " ".join(t if len(t.strip(".,")) <= 1 else t.title()
                                 for t in parts[:-1])
        firm = surname is None
    else:
        # T-0987 stretch 12: the separator, before the comma is walked. The repair
        # rewrites the leading run only; `flat` is untouched and becomes the quote.
        body, repair = repair_separator(body)
        head = body.split(",")[0].strip()
        firm = bool(FIRM.search(head)) or "&" in head
        if firm:
            printed, rest = head.strip(" ,."), body[len(head):].strip(" ,.")
            surname = given = None
        else:
            surname = head.strip(" .")
            given, rest = split_name(body[len(head):].strip(" ,."))
            printed = surname + (", " + given if given else "")
    m = PLACE.search(rest)
    occupation = (rest[:m.start()] if m else rest).strip(" ,.")
    address = (rest[m.start():] if m else "").strip(" ,.")
    out = {
        "printed_name": printed,
        "surname": surname,
        "given": given or None,
        "firm": bool(firm),
        "editorial_bracket": editorial,
        "occupation": occupation or None,
        "address": address or None,
        "bracket_notes": notes,
    }
    if repair is not None:
        # Both readings, on the claim, so nothing downstream has to take the repair
        # on trust: what this transcription printed, what the repair reads, what the
        # second hand prints, and which of the two the confidence rests on.
        out["surname_repair"] = {
            "as_read": repair["as_read"],
            "reading": repair["reading"],
            "verdict": repair["verdict"],
            "confidence": repair["confidence"],
            "second_hand": repair["second_hand"],
            "second_hand_source_id": SECOND_HAND_SOURCE,
            "second_hand_note": SECOND_HAND,
            "ticket": "T-0987 stretch 12",
        }
    return out


def shouted_head(line: str):
    """The leading run of shouted tokens, or None when the line does not shout.

    A token counts when it is an initial ("J.", "B.-"), an ampersand, or a word
    with two consecutive capitals in it. The run is a HEAD only when at least one
    of its words carries those two capitals, which is what separates "C.
    McDONNELL," opening a card from "J. R. Hall, Boston," turning one.
    """
    keep = []
    for tok in line.split():
        bare = tok.strip(".,;:-'’")
        if tok.startswith("(") or not bare:
            break
        if bare in ("&", "AND") or INITIAL.match(tok) or CAPS_RUN.search(bare):
            keep.append(tok)
            if tok.rstrip("'’").endswith(","):
                break
            continue
        break
    head = " ".join(keep).strip(" ,.-")
    if not head or not CAPS_RUN.search(head):
        return None
    return head


def business_entries(lines):
    """(heading, first_line, last_line) for every card in the business directory."""
    out, heading = [], None
    for i in range(BUSINESS_FROM, BUSINESS_TO + 1):
        line = lines[i - 1]
        s = line.strip()
        if not s or s in FURNITURE:
            continue
        if HEADING.match(s) and len(s) <= 40:
            heading = s.rstrip(".")
            continue
        if shouted_head(line):
            out.append([heading, i, i])
        elif out:
            out[-1][2] = i
    return out


def alpha_entries(lines):
    """(section, first, last, cut) for every entry on an alphabetical page.

    `cut` is None for an entry that owns whole lines, or the character offset in
    `first` at which it begins when the transcription ran it onto the tail of the
    entry above. An entry that is cut always ends on its own last line.
    """
    out, section, started, last_surname = [], None, False, ""
    for i, line in enumerate(lines, 1):
        s = line.strip()
        m = SECTION.match(s)
        if m:
            section, started, last_surname = m.group(1), True, ""
            continue
        if not started or not s or s in FURNITURE:
            continue
        lead = re.sub(r"^[^A-Za-z]+", "", line)
        starts = False
        if lead[:1].isupper() and lead[:1] == section:
            head = line[:45]
            surname = fold_surname(re.split(r"[,\.]", lead, 1)[0])
            # A head with a comma is entry grammar and is taken on sight. Without
            # one, alphabetical order is the test — the directory is sorted, and a
            # capitalised fragment that sorts BEFORE the entry above it is that
            # entry's tail, not a new name.
            starts = ("," in head) or surname >= last_surname
        if starts:
            # T-0987 stretch 13. `lead` stripped the leading non-letters to decide
            # that an entry begins here, and then the entry was recorded from
            # column 0 and kept them. Where those non-letters are the tail of the
            # obituary bracket above — an age and the bracket that closes it — the
            # cut belongs where the run-on path below puts one: the entry above
            # ENDS at the bracket, and this one BEGINS at its own surname.
            tail = OBIT_TAIL.match(line) if out else None
            if tail:
                out[-1] = [out[-1][0], out[-1][1], i, out[-1][3], tail.start(1)]
                out.append([section, i, i, tail.end(1)])
            else:
                out.append([section, i, i, None])
            last_surname = fold_surname(re.split(r"[,\.]", lead, 1)[0])
            continue
        if not out:
            continue
        out[-1][2] = i
        # A run-on: a new surname of this section, mid-line, after a closing
        # bracket or a stop. Seven of them, all on page 2.
        for mm in re.finditer(r"(?<=[\]\.\)])\s+([A-Z][a-z][A-Za-z'’\-]*),\s", line):
            if mm.group(1)[:1] != section:
                continue
            surname = fold_surname(mm.group(1))
            if surname < last_surname:
                continue
            cut = mm.end() - len(mm.group(0).lstrip())
            # The entry above now ENDS at the cut, so it needs spans too; the new
            # one begins there and runs on as usual.
            out[-1] = [out[-1][0], out[-1][1], i, out[-1][3], cut]
            out.append([section, i, i, cut])
            last_surname = surname
    return out


def locator(page, first, last, cut, ends_at, lines):
    if cut is None and ends_at is None:
        return {"text_file": PAGE % page + ".txt", "lines": [first, last],
                "page": PAGE % page, "printed_section": None}
    spans = []
    for n in range(first, last + 1):
        frm = cut if (n == first and cut is not None) else 0
        to = ends_at if (n == last and ends_at is not None) else len(lines[n - 1])
        spans.append({"line": n, "from": frm, "to": to})
    return {"text_file": PAGE % page + ".txt", "spans": spans, "page": PAGE % page,
            "printed_section": None}


def rebuild(locator_doc, lines):
    if "spans" in locator_doc:
        return "\n".join(lines[s["line"] - 1][s["from"]:s["to"]] for s in locator_doc["spans"])
    first, last = locator_doc["lines"]
    return "\n".join(lines[first - 1:last])


def build_claims():
    claims, per_page, warnings = [], {}, []
    n = 0

    lines = lines_of(1)
    for heading, first, last in business_entries(lines):
        n += 1
        loc = locator(1, first, last, None, None, lines)
        loc["printed_section"] = heading
        raw = rebuild(loc, lines)
        flat = re.sub(r"\s+", " ", raw).strip()
        norm = split_entry(flat, shouted=True)
        norm["as_printed"] = flat
        norm["section"] = "business directory"
        norm["trade_heading"] = heading
        claims.append(claim(n, norm, raw, loc, kind="business"))
    per_page[PAGE % 1] = n

    for page in (2, 3, 4):
        lines = lines_of(page)
        before = n
        rows = alpha_entries(lines)
        for row in rows:
            section, first, last, cut = row[0], row[1], row[2], row[3]
            ends_at = row[4] if len(row) > 4 else None
            n += 1
            loc = locator(page, first, last, cut, ends_at, lines)
            loc["printed_section"] = section
            raw = rebuild(loc, lines)
            flat = re.sub(r"\s+", " ", raw).strip()
            norm = split_entry(flat, shouted=False)
            norm["as_printed"] = flat
            cid = "f1843_e%04d" % n
            tail_row = _OBIT_TAIL_BY_ID.get(cid) or _OBIT_TAIL_BY_AGE_OF.get(cid)
            if tail_row is not None:
                # Both readings on both halves of the pair, so nothing downstream
                # takes the cut on trust: what this transcription ran together, what
                # the cut reads, and what the second hand prints for the same two
                # lines. `side` says which half this claim is.
                norm["obituary_tail_cut"] = {
                    "side": ("entry" if cid == tail_row["id"] else "obituary"),
                    "as_read": (tail_row["tail"] + " " + tail_row["surname"]
                                if cid == tail_row["id"] else
                                "the bracket left open, the age on the line below"),
                    "reading": ("the entry begins at %s; the age %s closes the "
                                "obituary of %s above"
                                % (tail_row["surname"], tail_row["age"],
                                   tail_row["age_of"])),
                    "entry": tail_row["id"],
                    "obituary": tail_row["age_of"],
                    "age": tail_row["age"],
                    "verdict": "second_hand_closes_the_age_above",
                    "confidence": "documented",
                    "second_hand": tail_row["second_hand"],
                    "second_hand_source_id": SECOND_HAND_SOURCE,
                    "second_hand_note": SECOND_HAND,
                    "ticket": "T-0987 stretch 13",
                }
            norm["section"] = "alphabetical directory"
            norm["trade_heading"] = None
            if not norm["printed_name"]:
                warnings.append("page %d line %d: an entry with no name" % (page, first))
            kind = "building" if norm["editorial_bracket"] else (
                "business" if norm["firm"] else "person")
            claims.append(claim(n, norm, raw, loc, kind=kind))
        per_page[PAGE % page] = n - before
    return claims, per_page, warnings


def claim(n, norm, raw, loc, kind):
    return {
        "id": "f1843_e%04d" % n,
        "kind": kind,
        "reading": "transcription_mediated",
        "quote": raw,
        "normalized": norm,
        "locator": loc,
        "describes_date": "1843",
        "entities": [norm["printed_name"]] if norm["printed_name"] else [],
        "town_finding": False,
        "notes": None,
    }


DOC = ("GENERATED by tools/read_fergus_1843.py --build out of the committed page text in "
       "data/research/directories/text/. Hand-edit and --check says so. Every entry of the "
       "business directory on page 1 and of the alphabetical directory on pages 2-4, one "
       "claim each, quote verbatim off the transcription and the reading beside it. 1843, "
       "not 1835 — see the crosswalk.")


def payload(claims, per_page):
    people = sum(1 for c in claims if c["kind"] == "person")
    buildings = sum(1 for c in claims if c["kind"] == "building")
    return {
        "schema": 1,
        "_doc": DOC,
        "generated_by": "tools/read_fergus_1843.py --build",
        "source_id": "fergus_chicago_directory_1843",
        "corpus": {
            "item": "genealogytrails cook county / 1843directory_1..4",
            "url": "https://genealogytrails.com/ill/cook/1843directory_1.html",
            "what": "K. Torp's 2007 transcription, on Genealogy Trails, of Robert Fergus, "
                    "Directory of the City of Chicago, Illinois, for 1843 (Fergus Historical "
                    "Series No. 28; Chicago: Fergus Printing Company, 1896). Four web pages: "
                    "the civic account and business directory, then the alphabetical "
                    "directory in A-G, H-O and P-Z.",
            "committed": True,
            "how": "Cached into this repository on 2026-09-03 by "
                   "tools/read_genealogytrails.py and copied here byte for byte. The text "
                   "under data/research/directories/text/ is identical to the cache under "
                   "data/research/genealogytrails/text/, so a line number means the same "
                   "thing in both.",
        },
        "reading_note": "transcription_mediated throughout, and doubly so: this is a web "
                        "transcription of Fergus's 1896 printing of a canvass made in 1843, "
                        "and nobody on this project has seen the page. The transcriber's "
                        "damage is left in every quote on purpose — 'accidentially', "
                        "'John S.Wright', 'aged - .' — because a tidied quote cannot be "
                        "found again. The repair, where one is safe, is in normalized, and "
                        "normalized is best effort: the split of a printed line into name / "
                        "occupation / address is a heuristic over punctuation that is not a "
                        "grammar.",
        "counts": {"claims": len(claims), "person": people, "building": buildings,
                   "business": len(claims) - people - buildings, "by_page": per_page},
        "claims": claims,
    }


def declared_counts():
    """The per-page counts this domain's coverage.json declares for T-0571."""
    with open(COVERAGE, encoding="utf-8") as fh:
        cov = json.load(fh)
    for dec in cov.get("declarations") or []:
        if dec.get("ticket") == "T-0571":
            return dec.get("entries_by_item") or {}
    return {}


INSTITUTIONS_AND_PARTICLES = 30
# T-0987 stretch 13 emptied this pool: all six were the obituary tail of the entry
# above, and the cut puts the age back and starts the entry at its own surname. A
# seventh would be a new defect, and this is where it would show.
OBITUARY_TAIL_RUN_ONS_LEFT = 0


def self_test():
    """The separator table is a ratchet, and this is the pawl.

    Four ways it rots, and each fails here: a row stops matching exactly one
    entry (the text was re-committed, or the segmenter moved); a repaired entry
    stops reading a bare surname; a repair tidies the quote it was supposed to
    leave damaged; or a NEW run-on surname arrives with no row and no reason for
    standing outside the table.
    """
    claims, _, _ = build_claims()
    fails = []

    # 1. every row fired, exactly once.
    fired = {}
    for c in claims:
        rep = c["normalized"].get("surname_repair")
        if rep:
            fired.setdefault(rep["as_read"], []).append(c["id"])
    for row in SURNAME_SEPARATOR_REPAIRS:
        got = fired.get(row["as_read"], [])
        if got != [row["id"]]:
            fails.append("%s: %r matched %r, expected exactly [%r]"
                         % (row["id"], row["as_read"], got, row["id"]))
    for as_read, got in fired.items():
        if as_read not in _REPAIR_BY_READ:
            fails.append("a repair fired from no row: %r on %r" % (as_read, got))

    by_id = {c["id"]: c for c in claims}

    # 2. each repaired entry now reads a surname with no space in it, and the
    #    repaired surname is the head of the row's own reading.
    for row in SURNAME_SEPARATOR_REPAIRS:
        c = by_id.get(row["id"])
        if c is None:
            fails.append("%s: no such entry any more" % row["id"])
            continue
        sn = c["normalized"].get("surname") or ""
        if not sn or " " in sn:
            fails.append("%s: repaired and still reads surname %r" % (row["id"], sn))
        elif not row["reading"].startswith(sn):
            fails.append("%s: reads surname %r, which is not the head of %r"
                         % (row["id"], sn, row["reading"]))
        # 3. the damage stays in the quote and in as_printed.
        for field in ("quote",):
            text = re.sub(r"\s+", " ", c[field])
            if row["as_read"] not in text:
                fails.append("%s: the repair tidied %s — %r is gone from it"
                             % (row["id"], field, row["as_read"]))
        if row["as_read"] not in c["normalized"]["as_printed"]:
            fails.append("%s: the repair tidied as_printed" % row["id"])
        if row["confidence"] != ("inferred" if row["verdict"] == "both_point"
                                 else "documented"):
            fails.append("%s: confidence %r does not follow verdict %r"
                         % (row["id"], row["confidence"], row["verdict"]))

    # 4. nothing new in the pool. A person surname carrying a space is either an
    #    institution or a real particle, a page-citation run-on, or the one entry
    #    the second hand cannot rule on. Anything else is a repair nobody made.
    left = {r["id"] for r in SURNAME_SEPARATOR_LEFT_ALONE}
    run_on = re.compile(r"^\d+[-\d]*[.\]]")
    unexplained, run_ons, other = [], 0, 0
    for c in claims:
        if c["kind"] != "person":
            continue
        sn = c["normalized"].get("surname") or ""
        if " " not in sn:
            continue
        if c["id"] in left:
            continue
        if run_on.match(sn):
            run_ons += 1
        elif "." in sn.split(" ")[0] and not sn.startswith("St."):
            unexplained.append((c["id"], sn))
        else:
            other += 1
    if unexplained:
        fails.append("run-on surnames with no row in the table: %r" % (unexplained,))
    if run_ons != OBITUARY_TAIL_RUN_ONS_LEFT:
        fails.append("surnames still carrying a wrapped obituary tail: %d, expected %d"
                     % (run_ons, OBITUARY_TAIL_RUN_ONS_LEFT))

    # 6. T-0987 stretch 13: every obituary-tail cut still fires, on BOTH halves, and
    #    the age it hands back is still on the obituary above. Four ways this rots: a
    #    row stops cutting (the text was re-committed or the segmenter moved); the cut
    #    lands in the wrong place and the entry reads a dirty surname; the age fails to
    #    reach the bracket above; or the pair stops being adjacent, which would mean an
    #    entry was gained or lost between them and the ids no longer name the pair.
    for row in OBITUARY_TAIL_RUN_ONS:
        entry, above = by_id.get(row["id"]), by_id.get(row["age_of"])
        if entry is None or above is None:
            fails.append("%s: the pair %s/%s no longer exists"
                         % (row["id"], row["age_of"], row["id"]))
            continue
        sn = entry["normalized"].get("surname") or ""
        if sn != row["surname"]:
            fails.append("%s: cut reads surname %r, expected %r"
                         % (row["id"], sn, row["surname"]))
        if row["tail"] in entry["normalized"]["as_printed"]:
            fails.append("%s: the tail %r is still on the entry"
                         % (row["id"], row["tail"]))
        if not above["normalized"]["as_printed"].rstrip().endswith(row["tail"]):
            fails.append("%s: the obituary above does not close on %r — it reads %r"
                         % (row["age_of"], row["tail"],
                            above["normalized"]["as_printed"][-30:]))
        for half in (entry, above):
            cut = half["normalized"].get("obituary_tail_cut")
            if not cut or cut["age"] != row["age"]:
                fails.append("%s: no obituary_tail_cut naming age %r"
                             % (half["id"], row["age"]))
    if other != INSTITUTIONS_AND_PARTICLES:
        fails.append("institutions and real particles: %d, expected %d"
                     % (other, INSTITUTIONS_AND_PARTICLES))

    # 5. the left-alone entry is still damaged; if it ever stops being, the note
    #    that explains why it was left alone has to be revisited.
    for row in SURNAME_SEPARATOR_LEFT_ALONE:
        c = by_id.get(row["id"])
        if c is None or c["normalized"].get("surname") != row["as_read"]:
            fails.append("%s: left alone as %r, now reads %r"
                         % (row["id"], row["as_read"],
                            c and c["normalized"].get("surname")))

    for f in fails:
        print("  " + f, file=sys.stderr)
    if fails:
        print("fergus 1843 separator repairs: %d failure(s)" % len(fails), file=sys.stderr)
        return 1
    doc = sum(1 for r in SURNAME_SEPARATOR_REPAIRS if r["confidence"] == "documented")
    print("fergus 1843: %d run-on surnames repaired (%d documented off the second hand, "
          "%d inferred from the format), %d left alone; %d obituary tails cut back onto "
          "the entry above (%d still swallowed), %d institutions or particles standing"
          % (len(SURNAME_SEPARATOR_REPAIRS), doc, len(SURNAME_SEPARATOR_REPAIRS) - doc,
             len(SURNAME_SEPARATOR_LEFT_ALONE), len(OBITUARY_TAIL_RUN_ONS), run_ons,
             other))
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    claims, per_page, warnings = build_claims()
    doc = payload(claims, per_page)
    if "--check" in sys.argv:
        with open(OUT, encoding="utf-8") as fh:
            got = json.load(fh)
        if got != doc:
            print("fergus 1843: the committed entries do not match the text — "
                  "regenerate with --build", file=sys.stderr)
            return 1
        declared = declared_counts()
        if declared != per_page:
            print("fergus 1843: coverage.json declares %r and the text yields %r"
                  % (declared, per_page), file=sys.stderr)
            return 1
        print("fergus 1843: %d entries, and they match the committed text and the "
              "counts coverage.json declares" % len(claims))
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    for w in warnings:
        print("  warning:", w)
    print("fergus 1843: %d entries (%d person, %d business, %d building) → %s"
          % (len(claims), doc["counts"]["person"], doc["counts"]["business"],
             doc["counts"]["building"], os.path.relpath(OUT, ROOT)))
    print("  by page:", json.dumps(per_page))
    return 0


if __name__ == "__main__":
    sys.exit(main())
