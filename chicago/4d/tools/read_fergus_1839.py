#!/usr/bin/env python3
"""*Fergus' Directory of the City of Chicago, 1839* — read entry by entry (T-0506).

`--build` reads the committed page text under
`data/research/directories/text/fergus_1839_leaf_*.txt` and writes two claims files:
`claims/fergus_1839_directory_entries.json`, the alphabetical directory on printed
pages 5-36, and `claims/fergus_1839_town_findings.json`, the churches, hotels and
public places on printed page 37. `--check` rebuilds in memory and compares, so a
hand-edit of either generated file is caught the way `read_norris_1844.py` catches
one.

THE STRUCTURE IS THE INDENT, exactly as in Norris 1844: an entry is set flush left
and its continuation is turned in, and the committed text keeps that with two
leading spaces taken off the word coordinates of the scan.

1839 IS FOUR YEARS LATE, and this volume is later still. Two facts about it govern
every use downstream, and both are the compiler's own words on printed page 3:

  * The 1839 original was six blank pages at the back of the City's Laws and
    Ordinances, filled with "the names of the business men of the City ... no
    canvass was necessary, and the names were never written". What is printed here
    is Fergus's 1876 COMPLETION of that list out of the recollections of the Old
    Settlers he names on printed page 4 — so an entry is 1839 evidence recalled in
    1876, not an 1839 record.
  * "There were no numbers on any street (except Lake Street,) at that time — the
    numbers now given are those of the present day." EVERY STREET NUMBER IN THIS
    DIRECTORY EXCEPT ON LAKE STREET IS AN 1876 NUMBER. It locates nothing in 1839
    and less in 1835. The street NAME is the reading that survives; the number is
    carried in `as_printed` and marked in `normalized.number_is_1876`.

Nothing here is an 1835 fact. Every claim carries `describes_date: "1839"`, and the
crosswalk is the only place a name in this volume may touch a person in the scene.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
OUT = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_directory_entries.json")
OUT_TOWN = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_town_findings.json")

# The alphabetical directory: leaves 17-48 of the scan, printed pages 5-36.
FIRST_LEAF, LAST_LEAF, LEAF_TO_PRINTED = 17, 48, -12
# The churches, hotels and public places, printed page 37.
TOWN_LEAF = 49

# Prose and furniture inside the directory pages, skipped by line number because no
# rule separates it from an entry — it is the compiler talking, or the scanner.
SKIP = {
    44: (55, 56),  # the footnote on the man hanged in 1840 — two lines, not an entry
}

# The specks the left margin of this scan collects — a stray backslash, a bullet, a
# lone digit — land in the OCR as their own line and are indented enough to read as
# turned. A turned line carrying fewer than three letters is one of those, and it is
# left in the committed text and attached to no entry.
def dropping(line: str) -> bool:
    return sum(c.isalpha() for c in line) < 3

FIRM = re.compile(r"^[^,]{0,40}\s&\s|&\s*Co\b|\bBrothers\b", re.I)
TITLES = {"mrs", "miss", "mr", "dr", "capt", "col", "rev", "gen", "maj", "jr", "sr",
          "sen", "hon", "esq", "prof", "lieut", "gov", "judge"}
PLACE = re.compile(r"\b(?:h|house|res|residence|r|boards|bds|b)\.?\s", re.I)
# A street number, and whether it is on Lake street — the one street the compiler
# says was numbered in 1839.
NUMBER = re.compile(r"\b\d{1,3}\b")
LAKE = re.compile(r"\bLake\b", re.I)

STREET_WORD = r"(?:st|street|streets|sts|ave|avenue|av|road|rd|alley|place|court|square)"
# The head of a street name is a PROPER NOUN and the volume prints it capitalised. The
# pattern was compiled re.I, which made `[A-Z]` match a lower-case letter too, so the
# joining words this directory sets between two streets were read as street names of
# their own: `cor. Clark and Randolph sts` yielded "and Randolph sts", `bet Dearborn and
# State sts` yielded "and State sts", and `clerk Steamer Geo. W. Dole, for St. Joseph`
# yielded "for St" — a street out of a destination. The street WORD stays case-blind
# (the volume sets `st`, `St`, `STREET`); the NAME does not, and the joining words are
# refused by name as well, because `And` opens a line often enough to be capitalised.
STREET_NAME = r"[A-Z][A-Za-z'’]+"
JOINER = {"and", "bet", "between", "cor", "corner", "near", "for", "opp", "opposite",
          "over", "the", "to", "of", "on", "at", "from", "next"}
STREET = re.compile(
    r"\b((?:North|South|East|West|N|S|E|W|No|So)\.?\s+)?"
    r"(" + STREET_NAME + r"(?:\s+" + STREET_NAME + r")?)\s+(?i:" + STREET_WORD + r")\b\.?")


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
    path = os.path.join(TEXT, "fergus_1839_leaf_%03d.txt" % leaf)
    return open(path, encoding="utf-8").read().splitlines()


def clean_head(text: str) -> str:
    """Strip the scanner's marginal droppings from the front of an entry line."""
    return re.sub(r"^[^A-Za-z]*(?:[a-zA-Z]\s)?", "", text).strip()


def streets_in(text: str):
    """Every street named in an address, as printed. A clue, not a gazetteer."""
    found, seen = [], set()
    for m in STREET.finditer(text or ""):
        # `and Randolph sts` — the two-word name form catching a joiner in front of the
        # real head. Drop the joiner and keep the street; if nothing is left, it was
        # never a street.
        name = re.sub(r"\s+", " ", m.group(2)).strip()
        head = name.split()[0].strip(".,").lower()
        if head in JOINER:
            rest_of_name = name.split()[1:]
            if not rest_of_name:
                continue
            s = re.sub(r"\s+", " ", m.group(0)).strip(" .")
            s = s[s.index(name.split()[1]):] if name.split()[1] in s else s
        else:
            s = re.sub(r"\s+", " ", m.group(0)).strip(" .")
        key = s.lower()
        if key not in seen:
            seen.add(key)
            found.append(s)
    return found


# ---------------------------------------------------------------------------
# T-0987 stretch 13 — THE SURNAME THE SCAN BROKE, AND THE COMMA IT DROPPED.
#
# `split_entry` closes the surname at the first comma, because that is the format
# Fergus sets: `Surname, Given, trade, address`. ELEVEN person entries in this
# volume hand the crosswalk a surname with a space in it, and the crosswalk reaches
# an 1835 person through the surname and nothing else — so each of the eleven makes
# no match and no refusal and leaves no trace in any pool T-0987 counts. Stretches
# 10 to 12 measured and closed exactly this hole in Norris 1844 and Fergus 1843.
#
# FOUR of the eleven stand outside: `St. Palais` and `State Bank Branch` are a real
# particle and an institution, and the two `Wheeler k` firms are the scan reading an
# ampersand as a `k`, which is T-1018's class and not this one. SEVEN are repaired
# below, in two shapes the printer and the scanner are each responsible for one of:
#
#   4  THE SCAN BROKE ONE SURNAME IN TWO. The comma is printed and is in the right
#      place; the space inside the surname is not in the type. `Gilbert on, Francis`,
#      `Snow hook, Wm. B.`, `Stark weather, Chas. R.`, `Wick wire, Capt. William`.
#   3  THE COMMA IS ABSENT and the head runs on into the forename: `Densmore Eleazer
#      W.`, `Johnson John`, `Scammon J. Young`.
#
# THERE IS NO SECOND HAND FOR THIS VOLUME, and this table does not pretend one.
# The committed text here is ALREADY archive.org's OCR of the Allen County scan, so
# the trick stretch 12 used on Fergus 1843 — set the web transcription against the
# printed volume's own OCR — has nothing to set against it. Stretch 12 left that as
# an open question; this stretch answers it by asking a different question instead.
# Every row is corroborated, or not, by a source that IS committed here:
#
#   * THE SAME VOLUME, elsewhere on the same page or in its own civic lists. The
#     strongest witness there is: `Gilberton, Ralph, laborer,` is the NEXT LINE after
#     `Gilbert on, Francis, laborer,` on leaf 27, and `J. Young Scammon,` is printed
#     whole in the volume's own list on leaf 54.
#   * A LATER DIRECTORY of the same town, which is a different printing and a
#     different transcription: Fergus 1843 (through the second hand of stretch 12)
#     and Norris 1844.
#   * THE ALPHABET, which every row passes and none rests on alone: a repaired
#     surname has to sort where the volume set the line, and all seven do —
#     `Snowhook` between `Snow, Ira` and `Soden`, `Wickwire` between `Wicker, Joel`
#     at the foot of leaf 47 and `Wiggins` below it.
#
# `documented` is used only where a source PRINTS the repaired form; where the
# alphabet and the format are the whole of the argument the row is `inferred` and
# says so. The repair moves the READING only: `quote` keeps the damage, because a
# tidied quote cannot be found again, and every repaired claim states both readings
# in `normalized.surname_repair`. `--self-test` is the ratchet.
SURNAME_REPAIRS = [
    {"id": 'f1839_e0545', "as_read": 'Gilbert on', "reading": 'Gilberton',
     "shape": 'scan_broke_the_surname', "confidence": 'documented',
     "witness": "the same volume, leaf 27, the VERY NEXT LINE: `Gilberton,  Ralph,  "
                "laborer,` — one surname set twice on one page, broken once"},
    {"id": 'f1839_e1381', "as_read": 'Snow hook', "reading": 'Snowhook',
     "shape": 'scan_broke_the_surname', "confidence": 'documented',
     "witness": "Norris's Chicago directory of 1844, leaf 52 of the committed scan "
                "and the genealogytrails transcription of it, both `Snowhook, W.B., "
                "grocer`; and the volume sets the line between `Snow, Ira` and "
                "`Soden, William`, where Snowhook sorts and Snow does not"},
    {"id": 'f1839_e1401', "as_read": 'Stark weather', "reading": 'Starkweather',
     "shape": 'scan_broke_the_surname', "confidence": 'documented',
     "witness": "Fergus's directory of 1843 through the printed volume's own OCR "
                "(`fergus_historical_series_26_29`): `Starkweather,  Charles  Robert,  "
                "assistant  postma-ter,  res  120  State`; and Norris 1844, "
                "`Starkweather, C. Robt, ast P.M.` — the same assistant postmaster, "
                "printed whole by two later directories"},
    {"id": 'f1839_e1607', "as_read": 'Wick wire', "reading": 'Wickwire',
     "shape": 'scan_broke_the_surname', "confidence": 'inferred',
     "witness": "NO source committed here prints this surname, in any spelling — the "
                "one row of the seven with no witness but the page. What stands is the "
                "format and the alphabet: the comma is printed after `wire`, so the "
                "whole of `Wick wire` is the surname the volume set, and the line opens "
                "leaf 48 between `Wicker, Joel II.` at the foot of leaf 47 and "
                "`Wiggins, William` below it, which is where Wickwire sorts"},
    {"id": 'f1839_e0377', "as_read": 'Densmore Eleazer W.',
     "reading": 'Densmore, Eleazer W.',
     "shape": 'comma_absent', "confidence": 'documented',
     "witness": "Fergus 1843 through the printed volume's own OCR: `Densmore,  Eleazer "
                "\"Woodworth,  clerk.` — the comma printed, and the forename run out in "
                "full; and the Calumet Club's 1879 registry of old settlers, `Densmore, "
                "Eleazer W. | 1835, Sept. | Paris, N.Y.`"},
    {"id": 'f1839_e1297', "as_read": 'Scammon J. Young',
     "reading": 'Scammon, J. Young',
     "shape": 'comma_absent', "confidence": 'documented',
     "witness": "the same volume, leaf 54, which sets the name whole in a subscribers' "
                "list: `J.  Young  Scammon,` — and four further printings of `J. Y. "
                "Scammon` on leaves 34, 50 and 61. Surname and forename are the "
                "volume's own, in the volume's own type; only the comma is missing"},
    {"id": 'f1839_e0794', "as_read": 'Johnson John', "reading": 'Johnson, John',
     "shape": 'comma_absent', "confidence": 'inferred',
     "witness": "no hand prints a separator for THIS line. The argument is the format "
                "and nothing else: the volume sets `Surname, Given` and sets the very "
                "same employer's other men that way three lines apart (`Matthews,  "
                "George,  blacksmith,  Joseph  Willemin`), and `Johnson, John` is "
                "printed with its comma by Fergus 1843 and Norris 1844 — of other men, "
                "which is why this row is inferred and not documented"},
]

_REPAIR_BY_READ_1839 = {r["as_read"]: r for r in SURNAME_REPAIRS}
_REPAIR_BY_ID_1839 = {r["id"]: r for r in SURNAME_REPAIRS}


def repair_surname(head: str):
    """Lift a broken or run-on surname before the comma is walked, or leave it.

    Longest match first, so a row whose `as_read` is a prefix of another's cannot
    steal it. Returns `(head, row)`.
    """
    for as_read in sorted(_REPAIR_BY_READ_1839, key=len, reverse=True):
        if head.startswith(as_read):
            row = _REPAIR_BY_READ_1839[as_read]
            return row["reading"] + head[len(as_read):], row
    return head, None


def split_entry(text: str):
    """name / occupation / address, best effort, out of one printed entry."""
    head = clean_head(text)
    # T-0987 stretch 13: the surname, before the comma is walked. The repair rewrites
    # the leading run only; `text` is untouched and is what becomes the quote.
    head, repair = repair_surname(head)
    firm = bool(FIRM.search(head.split(",")[0] + ","))
    if "," in head:
        surname, rest = head.split(",", 1)
    else:
        surname, rest = head, ""
    surname, rest = surname.strip(" .&"), rest.strip()
    given = []
    if not firm:
        # `consumed` is what the loop ATE and `given` is what it KEPT: they differ by
        # the loose comma below, which is punctuation the name does not carry but the
        # slice at the end of the loop has to account for, or the forename's last
        # letters are left standing at the head of the trade ("n, contractor").
        consumed = []
        for tok in rest.split():
            bare = tok.strip(".,'\"").lower()
            if bare in TITLES or re.fullmatch(r"[A-Z]", tok.strip(".,")) or (
                    tok[:1].isupper() and len(given) < 3 and not PLACE.fullmatch(tok + " ")):
                given.append(tok)
                consumed.append(tok)
                # THE PRINTED COMMA CLOSES THE NAME. Without this the loop ran on past
                # it and took the next capitalised word for a forename, because a
                # capital and a count of three were the whole test: `Beaubien, John B.,
                # Michigan ave.` read "Michigan" as part of the name and left the
                # address as the tail of its own qualifier, `So. Water sts` — the wrong
                # street. The volume sets a comma after the given names and before the
                # trade, so the comma is the boundary the compositor actually printed.
                # A title or a suffix carries a comma of its own — the volume sets
                # `Bates, jr., John` and `Baumgarten, jr., Morris` — so its comma is
                # not the one that closes the name.
                if tok.rstrip(".").endswith(",") and bare.strip(",") not in TITLES:
                    break
                continue
            # THE SUFFIX'S COMMA, SET OFF BY A SPACE (T-0987 stretch 8). The clause
            # above waives the comma that a title or a suffix carries — but only when
            # the compositor set it TIGHT, `jr.,`. Six entries in this volume set it
            # loose, `Archdale, jr. , John, contractor`, so the comma arrives as a
            # token of its own, matches nothing, and breaks the loop: the forename is
            # left behind and `jr` stands as the given name. It is the same waiver and
            # the same comma, and the forename it was losing is the whole of what the
            # crosswalk keys a man on — `King, jr. , John` was reaching John Lyle King
            # on the J of `jr.`, which is a letter of a suffix and not of a name.
            if given and not tok.strip(",.") and given[-1].strip(".,'\"").lower() in TITLES:
                consumed.append(tok)
                # attached to the suffix, so the reading prints as the volume's own
                # tight form does — `Archdale, jr., John`, not `Archdale, jr. John`.
                given[-1] = given[-1] + tok
                continue
            break
        rest = rest[len(" ".join(consumed)):].strip(" ,.")
    given_s = " ".join(given).strip(" ,.")
    m = PLACE.search(rest)
    occupation = (rest[:m.start()] if m else rest).strip(" ,.")
    address = (rest[m.start():] if m else "").strip(" ,.")
    if firm:
        keep = []
        for tok in head.split(",")[0].split():
            if tok.islower() and tok.strip(".") not in ("and", "of", "the", "de", "du", "van"):
                break
            keep.append(tok)
        printed = " ".join(keep).strip(" ,.") or head.split(",")[0].strip()
    else:
        printed = surname + (", " + given_s if given_s else "")
    # The trade and the address are not reliably separated by the comma in this
    # volume — many entries run "carpenter, Monroe street, near Dearborn". Take the
    # address as everything from the first street name onward when PLACE found none.
    if not address:
        sm = STREET.search(occupation)
        if sm:
            cut = sm.start()
            # A house number stands in front of its street: "carpenter, 154 Clark
            # street" splits after the trade, not after the number.
            back = re.search(r"(\d{1,3})\s*$", occupation[:cut])
            if back:
                cut = back.start(1)
            address, occupation = occupation[cut:].strip(" ,."), \
                occupation[:cut].strip(" ,.")
    streets = streets_in(address)
    numbers = NUMBER.findall(address or "")
    out = {
        "printed_name": printed,
        "surname": None if firm else surname,
        "given": None if firm else (given_s or None),
        "firm": firm,
        "occupation": occupation or None,
        "address": address or None,
        "streets": streets,
        # The compiler's own warning, applied: a number off Lake street is 1876's.
        "number_is_1876": bool(numbers) and not LAKE.search(address or ""),
    }
    if repair is not None:
        # Both readings on the claim, so nothing downstream takes the repair on
        # trust: what the scan printed, what the repair reads, which of the two
        # shapes it is, and the committed witness the confidence rests on.
        out["surname_repair"] = {
            "as_read": repair["as_read"],
            "reading": repair["reading"],
            "shape": repair["shape"],
            "confidence": repair["confidence"],
            "witness": repair["witness"],
            "ticket": "T-0987 stretch 13",
        }
    return out


def build_entries():
    claims, warnings = [], []
    n = 0
    for leaf in range(FIRST_LEAF, LAST_LEAF + 1):
        lines = leaf_lines(leaf)
        printed = leaf + LEAF_TO_PRINTED
        skip = SKIP.get(leaf, ())
        entries = []  # [first_line, last_line]
        for i, line in enumerate(lines, 1):
            if i in skip:
                continue
            if i <= 3 and header_like(line):
                continue
            if line.startswith("  "):
                if dropping(line):
                    continue
                if entries and entries[-1][1] == i - 1:
                    entries[-1][1] = i
                else:
                    warnings.append("leaf %d line %d: a turned line with no entry above it"
                                    % (leaf, i))
                continue
            if not line.strip():
                continue
            entries.append([i, i])
        for first, last in entries:
            n += 1
            raw = "\n".join(lines[first - 1:last])
            # The scan sets an end-of-line break as `-` or as `¬`; both join the word
            # back up. Eleven lines carry the second form and one of them is an address:
            # `La¬ / Salle st cor. So. Water` read as a street called "Salle".
            flat = re.sub(r"\s+", " ", re.sub(r"[-¬]\n\s*", "", raw)).strip()
            norm = split_entry(flat)
            norm["as_printed"] = flat
            claims.append({
                "id": "f1839_e%04d" % n,
                "kind": "business" if norm["firm"] else "person",
                "reading": "transcription_mediated",
                "quote": raw,
                "normalized": norm,
                "locator": {
                    "text_file": "fergus_1839_leaf_%03d.txt" % leaf,
                    "lines": [first, last],
                    "page": "fergus_1839_leaf_%03d" % leaf,
                    "printed_page": printed,
                },
                "describes_date": "1839",
                "entities": [norm["printed_name"]] if norm["printed_name"] else [],
                "town_finding": False,
                "notes": None,
            })
    return claims, warnings


# Printed page 37 is not a name list: it is the town itself, set out in four blocks
# the page separates by heading and by nothing else. The line map is written out
# here rather than sniffed, because forty lines read by eye beat a rule that has to
# guess whether "Egan Row" is a building or a business.
TOWN_LINES = [
    (2, 9, "building", "church"),
    (11, 25, "business", "hotel"),
    (26, 33, "building", "public_office"),
    (34, 37, "building", "public_room"),
    (38, 39, "building", "row"),
    (40, 40, "landscape", "settlement"),
    (41, 42, "event", "fire"),
]
TOWN_SKIP = {10}  # the centred HOTELS. heading


def build_town():
    lines = leaf_lines(TOWN_LEAF)
    claims, n = [], 0
    for first, last, kind, category in TOWN_LINES:
        i = first
        while i <= last:
            if i in TOWN_SKIP:
                i += 1
                continue
            end = i
            while end + 1 <= last and lines[end].startswith("  ") and not dropping(lines[end]) \
                    and (end + 1) not in TOWN_SKIP:
                end += 1
            n += 1
            raw = "\n".join(lines[i - 1:end])
            flat = re.sub(r"\s+", " ", raw).strip()
            name = clean_head(flat).split(",")[0].strip()
            claims.append({
                "id": "f1839_t%03d" % n,
                "kind": kind,
                "reading": "transcription_mediated",
                "quote": raw,
                "normalized": {
                    "as_printed": flat,
                    "name": name,
                    "category": category,
                    "streets": streets_in(flat),
                },
                "locator": {
                    "text_file": "fergus_1839_leaf_%03d.txt" % TOWN_LEAF,
                    "lines": [i, end],
                    "page": "fergus_1839_leaf_%03d" % TOWN_LEAF,
                    "printed_page": TOWN_LEAF + LEAF_TO_PRINTED,
                },
                "describes_date": "1839",
                "entities": [name] if name else [],
                "town_finding": True,
                "notes": None,
            })
            i = end + 1
    return claims


CORPUS = {
    "item": "fergusdirectoryo00ferg",
    "url": "https://archive.org/details/fergusdirectoryo00ferg",
    "what": "Allen County Public Library Genealogy Center scan of Robert Fergus, "
            "Fergus' Directory of the City of Chicago, 1839 (Chicago: Fergus Printing "
            "Company, 1876). 86 leaves.",
    "committed": True,
    "how": "The word coordinates of archive.org's OCR (fergusdirectoryo00ferg_djvu.xml) "
           "give each line its left edge; a line set more than 25 px right of the "
           "MEDIAN line start of its own page — the page is 2238 px wide and the turn "
           "measures about 50 px — is a turned line and is committed with two leading "
           "spaces. Nothing else about the text is touched.",
}

READING_NOTE = (
    "transcription_mediated throughout: this is archive.org's OCR of the printed page, "
    "machine-read and not checked against the image by eye. The damage is left in every "
    "quote on purpose — 'CHICAGO DIEECTQEY' for the title, 'lxls' for 'bds', 'Columbian "
    "blouse' for 'Columbian House' — because a tidied quote cannot be found again. The "
    "repair, where one is safe, is in normalized, and normalized is best effort: the split "
    "of one printed line into name / trade / address is a heuristic over inconsistent "
    "nineteenth-century punctuation.")

DATE_NOTE = (
    "TWO WARNINGS FROM THE COMPILER HIMSELF, printed page 3, and they bind every use of "
    "this file. (1) The 1839 original was six pages of business men's names set up from "
    "memory at the back of the City's Laws and Ordinances; what is printed here is "
    "Fergus's 1876 completion of it from the recollections of the Old Settlers he thanks "
    "on printed page 4. An entry is 1839 evidence RECALLED IN 1876. (2) 'There were no "
    "numbers on any street (except Lake Street,) at that time — the numbers now given are "
    "those of the present day.' Every street number here off Lake street is an 1876 "
    "number and locates nothing in 1839; normalized.number_is_1876 says which. The street "
    "NAME is the reading that survives.")


def payload(claims, town=False):
    if town:
        return {
            "schema": 1,
            "_doc": "GENERATED by tools/read_fergus_1839.py --build out of the committed page "
                    "text. Printed page 37 of the volume: the churches, the hotels, the public "
                    "offices and rooms, the two named rows and the Dutch Settlement, one claim "
                    "each, with the footnote that records the Tremont House fire of 27 October "
                    "1839. Town findings, not names.",
            "generated_by": "tools/read_fergus_1839.py --build",
            "source_id": "fergus_chicago_directory_1839",
            "corpus": CORPUS,
            "reading_note": READING_NOTE,
            "date_note": DATE_NOTE,
            "counts": {"claims": len(claims)},
            "claims": claims,
        }
    people = sum(1 for c in claims if c["kind"] == "person")
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_fergus_1839.py --build out of the committed page text "
                "in data/research/directories/text/. Hand-edit and --check says so. Every entry "
                "in the alphabetical directory, printed pages 5-36, one claim each, quote "
                "verbatim off the OCR and the reading beside it. 1839, not 1835 — see the "
                "crosswalk.",
        "generated_by": "tools/read_fergus_1839.py --build",
        "source_id": "fergus_chicago_directory_1839",
        "corpus": CORPUS,
        "reading_note": READING_NOTE,
        "date_note": DATE_NOTE,
        "counts": {"claims": len(claims), "person": people,
                   "business": len(claims) - people},
        "claims": claims,
    }


# The four that stand OUTSIDE the table and are not defects of it: a real particle,
# an institution, and the two firms whose ampersand the scan set as a `k` (T-1018).
SURNAME_SPACE_STANDING = 4


def self_test():
    """The repair table is a ratchet, and this is the pawl.

    Four ways it rots: a row stops matching exactly one entry (the text was
    re-committed, or the segmenter moved); a repaired entry still reads a surname
    with a space in it; a repair TIDIED the quote it was meant to leave damaged;
    or a new broken surname arrives with no row and no reason for standing outside
    the table.
    """
    claims, _ = build_entries()
    fails = []

    fired = {}
    for c in claims:
        rep = (c.get("normalized") or {}).get("surname_repair")
        if rep:
            fired.setdefault(rep["as_read"], []).append(c["id"])
    for row in SURNAME_REPAIRS:
        got = fired.get(row["as_read"], [])
        if got != [row["id"]]:
            fails.append("%s: %r matched %r, expected exactly [%r]"
                         % (row["id"], row["as_read"], got, row["id"]))
    for as_read, got in fired.items():
        if as_read not in _REPAIR_BY_READ_1839:
            fails.append("a repair fired from no row: %r on %r" % (as_read, got))

    by_id = {c["id"]: c for c in claims}
    for row in SURNAME_REPAIRS:
        c = by_id.get(row["id"])
        if c is None:
            fails.append("%s: no such entry any more" % row["id"])
            continue
        sn = (c["normalized"].get("surname") or "")
        if not sn or " " in sn:
            fails.append("%s: repaired and still reads surname %r" % (row["id"], sn))
        elif not row["reading"].startswith(sn):
            fails.append("%s: reads surname %r, which is not the head of %r"
                         % (row["id"], sn, row["reading"]))
        flat = re.sub(r"\s+", " ", c["quote"])
        if re.sub(r"\s+", " ", row["as_read"]) not in flat:
            fails.append("%s: the repair tidied the quote — %r is gone from it"
                         % (row["id"], row["as_read"]))
        if row["confidence"] not in ("documented", "inferred"):
            fails.append("%s: confidence %r is neither" % (row["id"], row["confidence"]))
        if row["confidence"] == "documented" and not row["witness"]:
            fails.append("%s: documented and cites no witness" % row["id"])

    # Nothing new in the pool. A person surname carrying a space is either repaired
    # above or one of the four that stand outside; anything else is a repair nobody
    # made, and it is invisible to every reader until this fails.
    standing = 0
    for c in claims:
        if c.get("kind") != "person":
            continue
        sn = (c.get("normalized") or {}).get("surname") or ""
        if " " in sn:
            standing += 1
    if standing != SURNAME_SPACE_STANDING:
        fails.append("person surnames still carrying a space: %d, expected %d"
                     % (standing, SURNAME_SPACE_STANDING))

    for f in fails:
        print("  " + f, file=sys.stderr)
    if fails:
        print("fergus 1839 surname repairs: %d failure(s)" % len(fails), file=sys.stderr)
        return 1
    doc = sum(1 for r in SURNAME_REPAIRS if r["confidence"] == "documented")
    broke = sum(1 for r in SURNAME_REPAIRS if r["shape"] == "scan_broke_the_surname")
    print("fergus 1839: %d surnames repaired (%d the scan broke in two, %d the comma "
          "was absent from; %d documented off a committed witness, %d inferred from "
          "the format and the alphabet), %d standing outside the table"
          % (len(SURNAME_REPAIRS), broke, len(SURNAME_REPAIRS) - broke, doc,
             len(SURNAME_REPAIRS) - doc, standing))
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    claims, warnings = build_entries()
    town = build_town()
    docs = [(OUT, payload(claims)), (OUT_TOWN, payload(town, town=True))]
    if "--check" in sys.argv:
        for path, doc in docs:
            got = json.load(open(path, encoding="utf-8"))
            if got != doc:
                print("fergus 1839: %s does not match the committed text — regenerate "
                      "with --build" % os.path.relpath(path, ROOT), file=sys.stderr)
                return 1
        print("fergus 1839: %d entries and %d town findings, and they match the "
              "committed text" % (len(claims), len(town)))
        return 0
    for path, doc in docs:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    for w in warnings:
        print("  warning:", w)
    print("fergus 1839: %d entries (%d person, %d business) and %d town findings"
          % (len(claims), payload(claims)["counts"]["person"],
             payload(claims)["counts"]["business"], len(town)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
