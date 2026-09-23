#!/usr/bin/env python3
"""The charter election of 2 May 1837, out of Fergus 1839, printed pages 40-46 (T-0664).

`read_fergus_1839.py` read the alphabetical directory (printed 5-36) and the churches
and hotels (printed 37). This reads the next seven pages, and they are a different
object: not a directory of 1839 but the POLL of the city's first election, ward by
ward and voter by voter, with the two party tickets that preceded it, the polling
places, the judges of election, the volume's own vote totals and the ward boundaries
those totals are counted under.

  tools/read_fergus_1839_election.py --build     write the claims file
  tools/read_fergus_1839_election.py --check     rebuild in memory and diff (the gate)
  tools/read_fergus_1839_election.py --report    the poll counted against Fergus's own
                                                 totals, ward by ward

WHAT DATE THIS IS. Every claim here `describes_date: "1837-05-02"` — the day of the
poll — and NOT 1839 and emphatically not 1835. A man who voted in Chicago in May 1837
is not thereby a resident of Chicago in July 1835; he is a name that may corroborate
one. The crosswalk is the only place this list may touch a person in the scene, and
under the ratified grading ladder a later appearance alone never makes an 1835
resident.

WHY IT IS WORTH READING ANYWAY. It is the closest thing to a complete adult-male roll
between the 1833-1835 poll lists and the 1840 census: 709 men by Fergus's own count,
each placed in a ward, and a name that appears in the 1835 poll AND here AND in 1840
is a man who stayed.

THE COMPILER'S WARNING BINDS THIS TOO. Printed page 3: the volume is Fergus's 1876
completion, out of Old Settlers' recollections, of a list set up from memory. These
pages are a poll RECALLED AND RESET IN 1876, not the poll book. Two of Fergus's own
arithmetic lines disagree with the names he printed beside them, and `--report` prints
the disagreement rather than reconciling it.

THE STRUCTURE IS A LINE MAP, not a sniffer. The OCR of a four-column poll list does
not read in printed order — on printed page 44 the FIFTH WARD heading lands ABOVE five
names and the candidate heading lands BELOW them — so the segments are written out
here by eye, the way `read_fergus_1839.py` writes out printed page 37. A sniffer over
this page would be a guess wearing a rule's clothes.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
OUT = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_election_1837.json")
COVERAGE = os.path.join(ROOT, "data/research/directories/coverage.json")

LEAF_TO_PRINTED = -12
OGDEN, KINZIE = "William B. Ogden", "John H. Kinzie"

# THE POLL, printed pages 41-46 (leaves 53-58): (leaf, first line, last line, ward,
# the candidate the column is voting for). Inclusive, 1-based, over the committed text.
POLL = [
    (53, 8, 109, 1, OGDEN),
    (54, 4, 67, 1, KINZIE),
    (54, 70, 150, 2, OGDEN),
    (55, 3, 66, 2, OGDEN),
    (55, 68, 160, 2, KINZIE),
    (56, 5, 36, 3, OGDEN),
    (56, 38, 40, 3, KINZIE),
    (56, 43, 91, 4, OGDEN),
    (56, 93, 96, 4, KINZIE),
    (56, 98, 102, 5, OGDEN),
    (56, 104, 113, 5, OGDEN),
    (57, 5, 47, 5, OGDEN),
    (57, 49, 50, 5, KINZIE),
    (57, 53, 125, 6, OGDEN),
    (57, 127, 141, 6, KINZIE),
    (58, 2, 57, 6, KINZIE),
]

# The five lines the OCR sets between the FIFTH WARD heading and the candidate heading
# under it. The ward is the page's, and it is printed; the CANDIDATE is this reading's
# inference — Ogden's column is the one a ward's block opens with on every other page
# in the range, and Kinzie's heading for the fifth ward comes later, at leaf 57 line 48.
# Recorded per claim rather than smoothed away.
COLUMN_ORDER_INFERRED = {(56, n) for n in range(98, 103)}

# A poll line the OCR ran together out of two or three columns. Six lines in the range
# do it, and they are written out rather than split by a rule, because every rule that
# separates "Thomas Bishop  John Gage" from "S. Willis Grannis" also separates some
# man's own two-word surname from his given name.
MERGED = {
    (54, 18): ["Oliver  H.  Thompson,", "Elijah  K.  Ilubbard,"],
    (56, 39): ["David  Bradley", "James  Crawford"],
    (56, 40): ["Charles  A.  Lawber", "Henry  Burke"],
    (56, 38): ["Thomas  Bishop", "John  Gage"],
    (56, 93): ["Edward  Perkins", "Antoine  Loupean", "Edward  Parsons"],
    (56, 94): ["William  Forsyth", "John  Ludby", "James  Kinzie"],
    (56, 95): ["Francis  Chapron", "Daniel  Elston", "David  Cox"],
}

# Fergus's own totals, printed page 46, lines 58-70. Read here so the reading can be
# counted against them; they are ALSO committed as claims below.
PRINTED_WARD_TOTALS = {1: 170, 2: 238, 3: 38, 4: 59, 5: 60, 6: 144}
PRINTED_TOTAL = 709

# THE TICKETS, THE POLLING PLACES AND THE JUDGES, printed page 40 (leaf 52).
# (line, party, role, office) — the names are parsed out of the line, never retyped.
TICKET_LINES = [
    (5, "Whig", "nominee", "mayor"), (7, "Whig", "nominee", "high_constable"),
    (9, "Whig", "nominee", "alderman"), (10, "Whig", "nominee", "alderman"),
    (11, "Whig", "nominee", "alderman"), (12, "Whig", "nominee", "alderman"),
    (14, "Whig", "nominee", "assessor"), (15, "Whig", "nominee", "assessor"),
    (18, "Democratic", "nominee", "mayor"), (20, "Democratic", "nominee", "high_constable"),
    (22, "Democratic", "nominee", "alderman"), (23, "Democratic", "nominee", "alderman"),
    (24, "Democratic", "nominee", "alderman"), (25, "Democratic", "nominee", "alderman"),
    (26, "Democratic", "nominee", "alderman"), (27, "Democratic", "nominee", "alderman"),
    (39, None, "judge_of_election", "judge_of_election"),
    (40, None, "judge_of_election", "judge_of_election"),
    (41, None, "judge_of_election", "judge_of_election"),
    (42, None, "judge_of_election", "judge_of_election"),
    (43, None, "judge_of_election", "judge_of_election"),
    (44, None, "judge_of_election", "judge_of_election"),
]
# The polling places, printed page 40 lines 31-37; the fourth ward's runs over two lines.
POLLING = [(31, 31), (32, 32), (33, 33), (34, 35), (36, 36), (37, 37)]
# The town findings on the same pages: an absence Fergus records, his two totals tables
# and the six ward boundaries the totals are counted under.
TICKET_LEAF, POLL_END_LEAF = 52, 58
FINDINGS = [
    (52, 29, 29, "absence", "The names of the assessors on the Democratic ticket could "
                            "not be found in 1876"),
    (58, 58, 65, "tally", "Total votes in Chicago in 1837 by wards"),
    (58, 66, 70, "tally", "Total votes in Chicago in 1837 by divisions"),
    (58, 72, 72, "boundary", "First ward"), (58, 73, 73, "boundary", "Second ward"),
    (58, 74, 74, "boundary", "Third ward"), (58, 75, 75, "boundary", "Fourth ward"),
    (58, 76, 76, "boundary", "Fifth ward"), (58, 77, 77, "boundary", "Sixth ward"),
]

ORDINALS = {"ist": 1, "1st": 1, "2d": 2, "2nd": 2, "3d": 3, "3rd": 3,
            "4th": 4, "5th": 5, "6th": 6}
WARD_NAME = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth"}
# The tail of a run-on ward line: "... Erastus Bowen.  4th Ward" — the marker for the
# NEXT column, which the em-dash split leaves stuck to this column's names.
TRAILING_WARD = re.compile(r"\s+(ist|1st|2d|2nd|3d|3rd|4th|5th|6th)\s+\S{1,6}\s*$", re.I)
SWORN = re.compile(r"\bsworn\b", re.I)
# A heading that fell inside a poll segment is a map error, and it would ship as a
# voter named FOR WILLIAM B. OGDEN. Shouting plus one of the volume's structural words
# is a heading; "S. Ward," and "E. T. Ward" are men, and are not shouting.
HEADING = re.compile(r"^[^a-z]*$")
STRUCTURAL = re.compile(r"\b(FOR|WARD|ELECTION|VOTERS|MAYOR|LIST)\b")


def leaf_lines(leaf: int):
    path = os.path.join(TEXT, "fergus_1839_leaf_%03d.txt" % leaf)
    return open(path, encoding="utf-8").read().splitlines()


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def dropping(line: str) -> bool:
    """The scanner's specks: a line carrying fewer than three letters is not a name."""
    return sum(c.isalpha() for c in line) < 3


def clean_name(raw: str) -> str:
    """A printed poll line as a name. The OCR damage is LEFT IN — 'Curtis I iavens'
    stays — because a tidied name cannot be found again on the page. Only the
    punctuation the list sets between entries comes off, and the 'sworn' the clerk
    wrote beside eleven of them, which is carried in its own field."""
    s = flat(raw)
    s = SWORN.sub("", s)
    return s.strip(" .,;:•*·’'—-")


def em_split(line: str):
    """A ward line as (ward number, its text), one tuple per column the line holds.

    'ist Ward — Chas. L. Harmon, Giles Spring.' is one column; 'ist Ward — Erastus
    Bowen.  4th Ward — Wm. Forsyth.' is two, and the second column's marker is left
    stuck to the first column's names by the split, which TRAILING_WARD takes off."""
    parts = re.split(r"[—–]", line)
    if len(parts) < 2:
        return []
    out, marker = [], parts[0]
    for i, part in enumerate(parts[1:], start=1):
        last = i == len(parts) - 1
        body, next_marker = part, None
        if not last:
            m = TRAILING_WARD.search(part)
            if m:
                body, next_marker = part[:m.start()], m.group(0)
            else:
                body, next_marker = part, ""
        tok = flat(marker).split()
        ward = ORDINALS.get(tok[0].lower().strip(".,")) if tok else None
        out.append((ward, flat(body)))
        marker = next_marker or ""
    return out


def names_in(text: str):
    """The names a ticket or judges line holds, split on the comma the list sets."""
    return [n for n in (clean_name(p) for p in text.split(",")) if n and not dropping(n)]


def locator(leaf: int, first: int, last: int):
    return {"text_file": "fergus_1839_leaf_%03d.txt" % leaf,
            "lines": [first, last],
            "page": "fergus_1839_leaf_%03d" % leaf,
            "printed_page": leaf + LEAF_TO_PRINTED}


def build():
    claims, warnings, n = [], [], 0
    # ---- the poll
    for leaf, first, last, ward, candidate in POLL:
        lines = leaf_lines(leaf)
        for ln in range(first, last + 1):
            raw = lines[ln - 1]
            if HEADING.match(raw) and STRUCTURAL.search(raw.upper()):
                raise AssertionError(
                    "leaf %03d line %d is a heading, not a voter: %r — the POLL line map "
                    "is wrong" % (leaf, ln, raw))
            if dropping(raw):
                warnings.append("leaf %03d line %d is a speck, not a voter: %r"
                                % (leaf, ln, raw))
                continue
            for piece in MERGED.get((leaf, ln), [raw]):
                name = clean_name(piece)
                if not name:
                    continue
                n += 1
                claims.append({
                    "id": "f1839_v%04d" % n,
                    "kind": "person",
                    "reading": "transcription_mediated",
                    "quote": raw,
                    "normalized": {
                        "as_printed": flat(piece),
                        "name": name,
                        "role": "voter",
                        "ward": ward,
                        "ward_name": WARD_NAME[ward],
                        "voted_for": candidate,
                        "sworn": bool(SWORN.search(piece)),
                        "column_run_on": (leaf, ln) in MERGED,
                        "candidate_inferred": (leaf, ln) in COLUMN_ORDER_INFERRED,
                    },
                    "locator": locator(leaf, ln, ln),
                    "describes_date": "1837-05-02",
                    "entities": [name],
                    "town_finding": False,
                    "notes": ("The OCR sets this line between the FIFTH WARD heading and "
                              "the candidate heading under it; the ward is printed, the "
                              "candidate is this reading's inference from the column order "
                              "every other page in the range keeps."
                              if (leaf, ln) in COLUMN_ORDER_INFERRED else
                              "The OCR ran two or three columns of the poll into one line; "
                              "this claim is one column of it and quotes the whole line."
                              if (leaf, ln) in MERGED else None),
                })
    # ---- the two tickets and the judges of election
    lines = leaf_lines(TICKET_LEAF)
    for ln, party, role, office in TICKET_LINES:
        raw = lines[ln - 1]
        columns = em_split(raw) or [(None, raw)]
        for ward, body in columns:
            for name in names_in(body):
                n += 1
                claims.append({
                    "id": "f1839_v%04d" % n,
                    "kind": "person",
                    "reading": "transcription_mediated",
                    "quote": raw,
                    "normalized": {
                        "as_printed": name, "name": name, "role": role,
                        "ward": ward, "ward_name": WARD_NAME.get(ward),
                        "party": party, "office": office,
                        "elected": party == "Democratic" or None,
                    },
                    "locator": locator(TICKET_LEAF, ln, ln),
                    "describes_date": "1837-05-02",
                    "entities": [name],
                    "town_finding": False,
                    "notes": ("Fergus prints '(Elected.)' against the Democratic ticket as "
                              "a whole, not against each name on it."
                              if party == "Democratic" else None),
                })
    # ---- the polling places
    for first, last in POLLING:
        raw = "\n".join(lines[first - 1:last])
        columns = em_split(flat(raw))
        ward, body = columns[0] if columns else (None, flat(raw))
        n += 1
        claims.append({
            "id": "f1839_v%04d" % n,
            "kind": "building",
            "reading": "transcription_mediated",
            "quote": raw,
            "normalized": {"as_printed": flat(raw), "name": clean_name(body),
                           "role": "polling_place", "ward": ward,
                           "ward_name": WARD_NAME.get(ward)},
            "locator": locator(TICKET_LEAF, first, last),
            "describes_date": "1837-05-02",
            "entities": [clean_name(body)],
            "town_finding": True,
            "notes": "A house named as a polling place in 1837, two years after the scene "
                     "date. It says the house stood in 1837; it says nothing about 1835.",
        })
    # ---- the findings: an absence, two tallies, six boundaries
    for leaf, first, last, category, what in FINDINGS:
        raw = "\n".join(leaf_lines(leaf)[first - 1:last])
        n += 1
        claims.append({
            "id": "f1839_v%04d" % n,
            # The closed research vocabulary has no word for "the town said this"; a
            # tally, a ward boundary and a recorded absence are all acts of the
            # corporation, and `civic` is the word it does have for those.
            "kind": "event" if category == "absence" else "civic",
            "reading": "transcription_mediated",
            "quote": raw,
            "normalized": {"as_printed": flat(raw), "name": what, "role": category},
            "locator": locator(leaf, first, last),
            "describes_date": "1837-05-02",
            "entities": [],
            "town_finding": True,
            "notes": None,
        })
    return claims, warnings


def tally(claims):
    got = {}
    for c in claims:
        if c["normalized"].get("role") == "voter":
            got[c["normalized"]["ward"]] = got.get(c["normalized"]["ward"], 0) + 1
    return got


CORPUS = {
    "item": "fergusdirectoryo00ferg",
    "url": "https://archive.org/details/fergusdirectoryo00ferg",
    "what": "Allen County Public Library Genealogy Center scan of Robert Fergus, "
            "Fergus' Directory of the City of Chicago, 1839 (Chicago: Fergus Printing "
            "Company, 1876). 86 leaves. Printed pages 40-46 are leaves 52-58.",
    "committed": True,
    "how": "tools/fetch_fergus_1839_pages.py, which is the derivation "
           "read_fergus_1839.py describes: archive.org's OCR word coordinates give each "
           "line its left edge, and a line set more than 25 px right of the median line "
           "start of its own page is committed with two leading spaces.",
}

READING_NOTE = (
    "transcription_mediated throughout: archive.org's OCR of the printed page, machine-read "
    "and not checked against the image by eye. The damage is left in every name on purpose — "
    "'Curtis I iavens', 'Oeorge \\V. Merrill', 'John Iv. Bot'er' — because a tidied name "
    "cannot be found again on the page, and a poll list is worth nothing if its lines cannot "
    "be found. The four-column layout is the second hazard: six lines of the range ran two or "
    "three columns together and are split by an explicit map, and five lines on printed page "
    "44 are set by the OCR between a ward heading and its candidate heading, so their "
    "candidate carries candidate_inferred: true.")

DATE_NOTE = (
    "1837, NOT 1835 AND NOT 1839. This is the poll of Chicago's first city election, Tuesday "
    "2 May 1837, twenty-two months after the scene date. A man voting here is a name that MAY "
    "corroborate an 1835 resident; under the ratified grading ladder a later appearance alone "
    "never makes one, and nothing in this file mints or regrades anybody. Fergus's own warning "
    "on printed page 3 binds these pages as it binds the directory: the volume is his 1876 "
    "completion, out of Old Settlers' recollections, of a list set up from memory in 1839, so "
    "this is a poll RESET IN 1876 and not the poll book.")

ARITHMETIC_NOTE = (
    "FERGUS'S OWN ARITHMETIC DOES NOT MATCH THE NAMES HE PRINTED, in the FIRST WARD and "
    "therefore in the total, and the disagreement is committed rather than reconciled: "
    "counts_printed is his table on printed page 46 and counts_read is the reading. Neither is "
    "corrected to the other. SETTLED OFF THE PAGE IMAGES FOR T-0667, in "
    "../fergus_1839_first_ward_scan.json: printed pages 41-42 carry 167 LINES OF TYPE in the "
    "first ward — three columns of 34, then 22, 22 and 21 — on a leading that never doubles, "
    "with no ink below either block and no cell holding two names, and the numeral in the "
    "table was reopened and is 170 rather than a misread 167. So the three names are missing "
    "from the LIST and not from this reading: archive.org's OCR lost nothing here and neither "
    "did the segmenter. WHAT THE PIXELS CANNOT SAY is why the table says three more — a "
    "compositor dropping three lines, or a total that survived from 1837 in front of names "
    "reconstructed from recollection in 1876, which is what the volume's own headnote on "
    "printed page 3 warns this list is. No name is invented to close the gap.")


def payload(claims):
    got = tally(claims)
    voters = sum(got.values())
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_fergus_1839_election.py --build out of the committed "
                "page text in data/research/directories/text/. Hand-edit and --check says so. "
                "Fergus' Directory of the City of Chicago, 1839, printed pages 40-46: the two "
                "party tickets for the charter election of 2 May 1837, the polling places, the "
                "judges of election, the poll itself voter by voter and ward by ward, Fergus's "
                "two totals tables and the six ward boundaries they are counted under.",
        "generated_by": "tools/read_fergus_1839_election.py --build",
        "source_id": "fergus_chicago_directory_1839",
        "corpus": CORPUS,
        "reading_note": READING_NOTE,
        "date_note": DATE_NOTE,
        "arithmetic_note": ARITHMETIC_NOTE,
        "counts": {
            "claims": len(claims),
            "voters": voters,
            "nominees": sum(1 for c in claims if c["normalized"].get("role") == "nominee"),
            "judges": sum(1 for c in claims
                          if c["normalized"].get("role") == "judge_of_election"),
            "polling_places": sum(1 for c in claims
                                  if c["normalized"].get("role") == "polling_place"),
            "town_findings": sum(1 for c in claims if c["town_finding"]),
            "counts_read": {WARD_NAME[w]: got.get(w, 0) for w in sorted(WARD_NAME)},
            "counts_printed": {WARD_NAME[w]: PRINTED_WARD_TOTALS[w] for w in sorted(WARD_NAME)},
            "total_read": voters,
            "total_printed": PRINTED_TOTAL,
        },
        "claims": claims,
    }


def report(claims):
    got = tally(claims)
    print("the poll of 2 May 1837, counted against Fergus's own table on printed page 46")
    print("  %-8s %7s %7s %7s" % ("ward", "read", "printed", "delta"))
    for w in sorted(WARD_NAME):
        d = got.get(w, 0) - PRINTED_WARD_TOTALS[w]
        print("  %-8s %7d %7d %+7d" % (WARD_NAME[w], got.get(w, 0),
                                       PRINTED_WARD_TOTALS[w], d))
    total = sum(got.values())
    print("  %-8s %7d %7d %+7d" % ("TOTAL", total, PRINTED_TOTAL, total - PRINTED_TOTAL))
    for kind in ("nominee", "judge_of_election", "polling_place"):
        print("  %s: %d" % (kind, sum(1 for c in claims
                                      if c["normalized"].get("role") == kind)))


def declared_counts():
    """The per-leaf counts coverage.json declares for T-0664. A segmenter that loses a
    column of a poll list is invisible to every other gate in this repository, so the
    declaration is the second opinion — the same guard read_fergus_1843.py keeps."""
    doc = json.load(open(COVERAGE, encoding="utf-8"))
    for dec in doc["declarations"]:
        if dec["ticket"] == "T-0664":
            return dec["counts"]
    return None


def against_declaration(claims):
    want = declared_counts()
    if want is None:
        return ["coverage.json declares no T-0664 reading, and the reading has to be "
                "declared before it can be checked"]
    got = {}
    for c in claims:
        got[c["locator"]["page"]] = got.get(c["locator"]["page"], 0) + 1
    if got != want:
        return ["coverage.json declares %r and the text yields %r" % (want, got)]
    return []


def main():
    claims, warnings = build()
    doc = payload(claims)
    if "--report" in sys.argv:
        report(claims)
        for w in warnings:
            print("  warning:", w)
        return 0
    if "--check" in sys.argv:
        bad = against_declaration(claims)
        if bad:
            for b in bad:
                print("fergus 1839 election:", b, file=sys.stderr)
            return 1
        got = json.load(open(OUT, encoding="utf-8"))
        if got != doc:
            print("fergus 1839 election: %s does not match the committed text — regenerate "
                  "with --build" % os.path.relpath(OUT, ROOT), file=sys.stderr)
            return 1
        print("fergus 1839 election: %d claims (%d voters), and they match the committed "
              "text at the counts coverage.json declares"
              % (len(claims), doc["counts"]["voters"]))
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    for w in warnings:
        print("  warning:", w)
    print("fergus 1839 election: %d claims — %d voters, %d nominees, %d judges, "
          "%d polling places, %d town findings"
          % (len(claims), doc["counts"]["voters"], doc["counts"]["nominees"],
             doc["counts"]["judges"], doc["counts"]["polling_places"],
             doc["counts"]["town_findings"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
