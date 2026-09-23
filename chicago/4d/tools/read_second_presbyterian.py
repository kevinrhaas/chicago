#!/usr/bin/env python3
"""The roll of the Second Presbyterian Church of Chicago, 1842-1892 (T-0583).

    tools/read_second_presbyterian.py --fetch   FETCH the scan, commit the roll text
                                                and the row map (NETWORK)
    tools/read_second_presbyterian.py --build   write the records and the crosswalk
    tools/read_second_presbyterian.py --check   rebuild in memory and diff (the gate)
    tools/read_second_presbyterian.py --report  what the roll holds, and what it reached
    tools/read_second_presbyterian.py --self-test  the judging rules, fired against breakage

WHY THIS BOOK IS HERE. T-0570 read the Newberry Library's genealogical card index and
found fifty-four Chicago cards citing one work this project did not hold: `Chicago, Ill.
Second Presb. Ch., 1842-92. (Grant)`. T-0583 is the ticket for finding it. It is *The
Second Presbyterian Church of Chicago, June 1st, 1842, to June 1st, 1892* (Chicago:
Knight, Leonard & Co., 1892), John C. Grant editor — the Newberry card's `(Grant)` —
and printed page 153 opens A LIST OF MEMBERS OF THE CHURCH, 1842-1892, whose lines run
154-206: a name, how the member was admitted, the date, and for the closed roll a remark.

WHAT IT CAN AND CANNOT SAY ABOUT 1835. The congregation was organised in June 1842 out
of the First Presbyterian Church, which was organised in 1833 by people who were here.
So the roll is LATER EVIDENCE and never an 1835 fact: the earliest date it carries is
seven years after the scene date, and under the ratified ladder a later appearance alone
never makes an 1835 resident. Every record here therefore carries
`beyond_ticket_window: true` and the crosswalk beside it mints nobody and regrades
nobody. What the roll DOES give is corroboration — that a surname this project holds
from the 1835 town was still a Chicago surname in the 1840s, and, where a first initial
agrees too, a candidate for the same person.

THE COLUMNS ARE THE HAZARD, not the spelling. archive.org's OCR reads a four-column
table in the order the scanner met the ink, so the flat committed text puts a name
beside somebody else's date: on printed page 192 it runs `King, Edward / Letter. /
October 31, 1855. / Dismissed. / W. / Profession. / Dismissed. / King, Henry /
September i, 1858.`, which is two printed rows shuffled into one another. The fix is
the thing the flat text throws away — the word COORDINATES — and it is the same fix
`read_fergus_1839_lots.py` makes for the same reason. `--fetch` renders each roll leaf
into the committed text AND writes, beside it, the [line, from, to] spans of that text
which make up each printed cell. `--build` and `--check` then run OFFLINE out of the
committed text plus that map, so a span that points at the wrong ink fails the gate.

THE COLUMN BANDS ARE DERIVED PER LEAF, NOT HARD-CODED. The book is set with a recto and
a verso offset and the two differ by about seventy pixels, so a band that found the date
column on printed page 192 found the remarks column on 193. Each leaf's bands are taken
from its own ink: the left edge of the leftmost `Profession.`/`Letter.` opens the
`how_admitted` column, the leftmost month name opens `when_admitted`, and the leftmost
`Dismissed.`/`Deceased.` opens `remarks`. Those three anchors are written into the
committed row map, so the derivation is re-runnable and is not re-guessed at build time.

WHAT IS RECORDED, and why it is a subset. The roll is about 2,300 lines long and nearly
all of it is Chicago of the 1860s, 70s and 80s — people who cannot bear on the scene at
all. T-0583 asks for "the entries naming surnames this project holds", and that is what
`records` carries: one record per roll line whose surname folds to the surname of a
person in `data/residents/`. The counts state the whole roll so the subset can never be
mistaken for the book.

A NUMERAL IS READ OR IT IS REFUSED. This scan sets `1` as `i` and `l` constantly —
`September i, 1848` is 1 September 1848 — so a date token that is otherwise all digits
has `i`, `l` and `I` read as 1 and `O` as 0, and NOTHING ELSE is repaired. A date that
does not parse after that is null with its ink kept in `as_printed`; it is never
recovered from the run of dates around it.
"""
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crosswalk_fergus_1839 import fold, initial, residents, split_name  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = os.path.join(ROOT, "data/research/church")
TEXT = os.path.join(DOMAIN, "text/second_presbyterian_roll_1892.txt")
MAP = os.path.join(DOMAIN, "second_presbyterian_rowmap.json")
RECORDS = os.path.join(DOMAIN, "records/second_presbyterian_members_1842_1892.json")
CROSSWALK = os.path.join(DOMAIN, "second_presbyterian_crosswalk.json")

ITEM = "secondpresbyterian00chic"
URL = "https://archive.org/download/%s/%s_djvu.xml" % (ITEM, ITEM)
SOURCE_ID = "second_presbyterian_chicago_1892"
LEAF_TO_PRINTED = -86
SCENE_CUTOFF = "1835-07-01"

# The three rolls the book prints, by leaf (1-based, the OBJECT index of the djvu plus
# one — the same convention read_fergus_1839_lots.py uses). Read off the section
# headings on printed pages 153, 157 and 176.
SECTIONS = [
    {"list": "absent_members", "leaves": (240, 242),
     "heading": "NAMES OF ABSENT MEMBERS, WHOSE RESIDENCE AND CHRISTIAN STANDING ARE "
                "UNKNOWN TO THE SESSION"},
    {"list": "present_members", "leaves": (243, 261), "heading": "PRESENT MEMBERS"},
    {"list": "dismissed_deceased_or_ordained", "leaves": (262, 292),
     "heading": "NAMES OF MEMBERS DISMISSED, DECEASED OR ORDAINED TO THE MINISTRY"},
]

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")
HOW = ("Profession", "Letter", "Certificate", "Examination", "Restoration")
REMARKS = ("Deceased", "Dismissed", "Died", "Suspended", "Excommunicated", "Ordained",
           "Restored")
MONTH_NO = {m: i + 1 for i, m in enumerate(MONTHS)}

# A row's words sit within about ten pixels of one another vertically and the printer's
# leading is about fifty-five. Anything under this gap is the same printed row.
ROW_PX = 25
# THE SECOND PASS, and the reason there are two. A name too long for its column is set
# on a second line — `Barry, Mrs. William Tayl` / `or` — and the OCR gives that line a
# row of its own, twenty-five to forty-five pixels below its own row's other cells. So
# adjacent groups are merged back while they CAN be: two groups may join only when they
# COLLIDE IN NO COLUMN. Two printed rows both carry a name and both carry a date, so
# they collide and stay apart; the two fragments of one printed row land in different
# columns and rejoin. read_fergus_1839_lots.py splits and remerges for the same reason.
MERGE_PX = 45
# Everything above this y on a roll leaf is the running head and the column heads.
HEAD_PX = 540
# A column band opens this far left of the anchor that names it — the widest overhang
# measured on these leaves is nineteen pixels, on the `September` of printed page 205.
BAND_PAD = 40


# ---------------------------------------------------------------- the scan (network)

def page_words(page):
    """Every word of a leaf as x, vertical centre, text, and its span in the render.

    The line index and character offsets are into the text this same function renders,
    so the committed text and the map cannot disagree: one pass makes both.
    """
    words, lines = [], []
    for line in page.iter("LINE"):
        bodies, boxes = [], []
        for w in line.findall("WORD"):
            body = (w.text or "").strip()
            if not body:
                continue
            bodies.append(body)
            boxes.append([int(v) for v in w.get("coords").split(",")])
        if not bodies:
            continue
        lines.append(" ".join(bodies))
        at = 0
        for body, (x0, y1, x1, y0) in zip(bodies, boxes):
            words.append({"x": x0, "y": (y0 + y1) // 2, "t": body,
                          "line": len(lines), "a": at, "b": at + len(body)})
            at += len(body) + 1
    return lines, words


def anchors(words):
    """The three column anchors of one leaf, taken from the leaf's own ink.

    The MEDIAN left edge, not the leftmost. A column of forty-four aligned words has a
    median that moves by a pixel or two and a minimum that any one stray moves the whole
    way: printed page 171 carries a `May` far out in the names column, and reading the
    anchor off it put every `Letter.` on that page into the date cell.
    """
    def median_left(pred):
        xs = sorted(w["x"] for w in words if pred(w["t"]))
        return xs[len(xs) // 2] if xs else None
    return {
        "how": median_left(lambda t: t.rstrip(".,") in HOW),
        "when": median_left(lambda t: t.rstrip(".,") in MONTHS),
        "remarks": median_left(lambda t: t.rstrip(".,") in REMARKS),
    }


def cells_of(row, anc):
    """One printed row split into its four cells on the leaf's own anchors."""
    edges = []
    for name in ("how", "when", "remarks"):
        x = anc.get(name)
        edges.append(None if x is None else x - BAND_PAD)
    out = {"name": [], "how_admitted": [], "when_admitted": [], "remarks": []}
    for w in sorted(row, key=lambda w: w["x"]):
        if edges[2] is not None and w["x"] >= edges[2]:
            out["remarks"].append(w)
        elif edges[1] is not None and w["x"] >= edges[1]:
            out["when_admitted"].append(w)
        elif edges[0] is not None and w["x"] >= edges[0]:
            out["how_admitted"].append(w)
        else:
            out["name"].append(w)
    return out


def spans_of(ws):
    """The committed-text spans a cell's words occupy, merged where they adjoin."""
    out = []
    for w in sorted(ws, key=lambda w: (w["line"], w["a"])):
        if out and out[-1]["line"] == w["line"] and out[-1]["to"] + 1 == w["a"]:
            out[-1]["to"] = w["b"]
        else:
            out.append({"line": w["line"], "from": w["a"], "to": w["b"]})
    return out


def fetch(xml_path=None):
    """Render the roll leaves into one committed text and map every printed cell to it."""
    data = open(xml_path, "rb").read() if xml_path else \
        urllib.request.urlopen(URL, timeout=300).read()
    pages = ET.fromstring(data).findall(".//OBJECT")
    text, rows, offset = [], [], 0
    for section in SECTIONS:
        first, last = section["leaves"]
        for leaf in range(first, last + 1):
            lines, words = page_words(pages[leaf - 1])
            text.append("== leaf %d — printed page %d — %s"
                        % (leaf, leaf + LEAF_TO_PRINTED, section["list"]))
            text.extend(lines)
            base = offset + 1          # the `== leaf` banner takes one line
            offset += len(lines) + 1
            anc = anchors(words)
            body = sorted([w for w in words if w["y"] >= HEAD_PX],
                          key=lambda w: (w["y"], w["x"]))
            tight = []
            for w in body:
                if tight and w["y"] - tight[-1][-1]["y"] <= ROW_PX:
                    tight[-1].append(w)
                else:
                    tight.append([w])
            grouped = []
            for group in tight:
                columns = {k for k, ws in cells_of(group, anc).items() if ws}
                if (grouped and group[0]["y"] - grouped[-1][0][-1]["y"] <= MERGE_PX
                        and not (columns & grouped[-1][1])):
                    grouped[-1][0].extend(group)
                    grouped[-1][1] |= columns
                else:
                    grouped.append([list(group), columns])
            for group, _ in grouped:
                cell = cells_of(group, anc)
                if not cell["name"]:
                    continue
                rows.append({
                    "list": section["list"], "leaf": leaf,
                    "printed_page": leaf + LEAF_TO_PRINTED,
                    "y": group[0]["y"],
                    "name": [dict(s, line=s["line"] + base) for s in spans_of(cell["name"])],
                    "how_admitted": [dict(s, line=s["line"] + base)
                                     for s in spans_of(cell["how_admitted"])],
                    "when_admitted": [dict(s, line=s["line"] + base)
                                      for s in spans_of(cell["when_admitted"])],
                    "remarks": [dict(s, line=s["line"] + base)
                                for s in spans_of(cell["remarks"])],
                })
    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_second_presbyterian.py --fetch, over the "
                "network, out of the word coordinates of %s_djvu.xml. Every cell names "
                "the [line, from, to] spans of the committed roll text it is made of, "
                "so the reading built from it is rebuilt and checked OFFLINE. "
                "Hand-edit and --check says so." % ITEM,
        "generated_by": "tools/read_second_presbyterian.py --fetch",
        "item": ITEM,
        "leaf_to_printed": LEAF_TO_PRINTED,
        "sections": SECTIONS,
        "rows": rows,
    }
    return "\n".join(text) + "\n", doc


# ------------------------------------------------------------------ the reading

def ink(lines, spans):
    """The verbatim ink of a cell, out of the committed text, exactly as its spans cut it."""
    return " ".join(lines[s["line"] - 1][s["from"]:s["to"]] for s in spans).strip()


def digits(token):
    """A numeral this scan set with letters, and NOTHING ELSE repaired.

    `September i, 1848` is 1 September 1848: the printer's 1 comes back off the scan as
    `i` or `l` all through this book, and `0` as `O`. A token that is otherwise all
    digits has those four letters read as the numerals they are. A token that is not is
    refused, because a repair that reaches further is a guess wearing a reading's
    clothes.
    """
    s = token.strip(" .,;:")
    if not s:
        return None
    swapped = s.translate(str.maketrans({"i": "1", "l": "1", "I": "1", "O": "0"}))
    return swapped if swapped.isdigit() else None


def read_date(text):
    """(iso, precision) for a `September i, 1848.` cell, or (None, None) if refused."""
    tokens = text.replace(",", " ").split()
    month = day = year = None
    for tok in tokens:
        bare = tok.strip(" .,;:")
        if bare in MONTH_NO:
            month = MONTH_NO[bare]
            continue
        num = digits(tok)
        if num is None:
            continue
        if len(num) == 4 and num.startswith("1"):
            year = int(num)
        elif len(num) <= 2 and 1 <= int(num) <= 31 and day is None:
            day = int(num)
    if year is None:
        return None, None
    if month is None:
        return "%04d" % year, "year"
    if day is None:
        return "%04d-%02d" % (year, month), "month"
    return "%04d-%02d-%02d" % (year, month, day), "day"


def read_how(text):
    for word in text.split():
        if word.strip(" .,;:") in HOW:
            return word.strip(" .,;:").lower()
    return None


def read_remark(text):
    for word in text.split():
        if word.strip(" .,;:*") in REMARKS:
            return word.strip(" .,;:*").lower()
    return None


TITLE = re.compile(r"^(Mrs|Miss|Mr|Dr|Rev|Capt|Col|Gen|Maj|Hon)\.?$")
# WHAT IS ON THESE PAGES AND IS NOT A ROLL LINE. Two things, and both are dropped by
# what they SAY rather than by where they sit, because their position moves with the
# leaf: the column heads, which fall below the running-head band on the leaves whose
# type is set low, and the footnote the closed roll carries under its last line.
NOT_A_ROLL_LINE = re.compile(r"^[^A-Za-z]*(Names\b|Joined\s+another\s+Communion)")
# A heading is set in capitals and a name never is, so a name cell carrying no lower-case
# letter at all is the section heading broken across the columns — `NAMES OF ABSENT` /
# `MEMBERS.` on printed page 154, `PRESENT` / `MEMBERS.` on 157.
ALL_CAPS = re.compile(r"^[^a-z]+$")
# THE PRINTER'S COMMA, READ AS A FULL STOP. This scan turns the comma after a surname
# into a period about forty times — `Henderson. Mrs. Thomas`, `Armour. Geo. A.` — and a
# surname is one word, so a period standing between one word and a capitalised rest is
# that comma. Nothing wider is repaired: `Page Charles L.`, which lost its punctuation
# altogether, is kept whole with no forename rather than split on a guess.
SURNAME_STOP = re.compile(r"^((?:Van|Von|De|Del|La|Le)\s+)?([A-Z][A-Za-z'\-]+)[.;]\s+(?=[A-Z])")
# …and the words a surname is never made of on its own, so `St. Clair, John` is not cut
# into a surname `St` and a forename `Clair, John`.
NOT_A_SURNAME = ("St", "Mr", "Mrs", "Miss", "Dr", "Rev", "Jr", "Sr", "Van", "Von", "De")


def read_name(text):
    """(surname, forenames, title) out of a roll line's name cell.

    The roll is set `Surname, Title Forename Initial` — `Kimball, Miss Frances M.` — so
    the comma is the split and the title is lifted out of the forenames rather than
    folded into them. A cell with no comma is a wrapped continuation the row map has
    already rejoined, or it is not a name at all, and it is returned as a surname with
    no forename so the caller can refuse it.
    """
    flat = re.sub(r"\s+", " ", text).strip()
    m = SURNAME_STOP.match(flat)
    if m and m.group(2) not in NOT_A_SURNAME and "," not in flat[:m.end()]:
        flat = (m.group(1) or "") + m.group(2) + ", " + flat[m.end():]
    if "," not in flat:
        return flat.strip(" ."), "", None
    surname, rest = flat.split(",", 1)
    parts = rest.strip().split()
    title = None
    if parts and TITLE.match(parts[0].strip(".")):
        title = parts[0].strip(".")
        parts = parts[1:]
    return surname.strip(" ."), " ".join(parts).strip(" ,"), title


def leaf_text():
    with open(TEXT, encoding="utf-8") as fh:
        return fh.read().splitlines()


def roll():
    """Every printed row of the roll, rebuilt offline out of the text and the map."""
    lines = leaf_text()
    rowmap = json.loads(open(MAP, encoding="utf-8").read())
    out, dropped = [], []
    for row in rowmap["rows"]:
        cell = {k: ink(lines, row[k])
                for k in ("name", "how_admitted", "when_admitted", "remarks")}
        if NOT_A_ROLL_LINE.match(cell["name"]) or ALL_CAPS.match(cell["name"] or "x"):
            dropped.append(cell["name"])
            continue
        surname, forenames, title = read_name(cell["name"])
        if not surname or not re.search(r"[A-Za-z]{2}", surname):
            dropped.append(cell["name"])
            continue
        when, precision = read_date(cell["when_admitted"])
        out.append({
            "list": row["list"], "leaf": row["leaf"],
            "printed_page": row["printed_page"],
            "as_printed": {k: (v or None) for k, v in cell.items()},
            "surname": surname, "forenames": forenames, "title": title,
            "how_admitted": read_how(cell["how_admitted"]),
            "admitted": when, "admitted_precision": precision,
            "remark": read_remark(cell["remarks"]),
            "spans": (row["name"] + row["how_admitted"] + row["when_admitted"]
                      + row["remarks"]),
        })
    return out, dropped


def build():
    rows, dropped = roll()
    people = residents()
    held = {}
    for person in people:
        held.setdefault(fold(person["surname"]), []).append(person)

    records, n = [], 0
    for row in rows:
        key = fold(row["surname"])
        if key not in held:
            continue
        n += 1
        name = "%s, %s" % (row["surname"], row["forenames"]) if row["forenames"] \
            else row["surname"]
        entry_as_printed = " | ".join(
            v for v in (row["as_printed"]["name"], row["as_printed"]["how_admitted"],
                        row["as_printed"]["when_admitted"], row["as_printed"]["remarks"])
            if v)
        records.append({
            "id": "second_presb_%04d" % n,
            "as_read": entry_as_printed,
            "normalized": name,
            "locator": {
                # `page` is the unit this reading declares its coverage in, and the key
                # has to be the coverage item verbatim: research_domains.py reaches a
                # declared page only through a locator that names it.
                "page": "second_presbyterian_1892_printed_%d" % row["printed_page"],
                "roll": row["list"],
                "text_file": "second_presbyterian_roll_1892.txt",
                "spans": row["spans"],
                "line": min(s["line"] for s in row["spans"]),
                "printed_page": row["printed_page"],
                "leaf": row["leaf"],
            },
            "reading": "transcription_mediated",
            "confidence": "documented",
            "describes_date": row["admitted"],
            "cells": {
                "role": "member",
                "how_admitted": row["how_admitted"],
                "admitted": row["admitted"],
                "admitted_precision": row["admitted_precision"],
                "remark": row["remark"],
                "title": row["title"],
                "entry_as_printed": entry_as_printed,
                "congregation": "Second Presbyterian Church of Chicago",
                "place": "Chicago",
            },
            "at_chicago": True,
            "beyond_ticket_window": True,
            "surname": row["surname"],
            "forenames": row["forenames"] or None,
            "forename_printed": bool(row["forenames"]),
            "notes": None if row["admitted"] else
                     "the admission date is destroyed in the scan and is left null "
                     "rather than recovered from the dates around it",
        })

    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_second_presbyterian.py --build out of the "
                "committed roll text and the committed row map beside it. Hand-edit "
                "and --check says so. The Second Presbyterian Church of Chicago, June "
                "1st, 1842, to June 1st, 1892 (Chicago: Knight, Leonard & Co., 1892), "
                "printed pages 154-206 (153 carries the heading and no line): A LIST OF MEMBERS OF THE CHURCH, 1842-1892. "
                "ONE RECORD PER ROLL LINE WHOSE SURNAME THIS PROJECT ALREADY HOLDS — "
                "counts state the whole roll, so this subset is never the book.",
        "generated_by": "tools/read_second_presbyterian.py --build",
        "source_id": SOURCE_ID,
        "describes_date": "1842-06-01/1892-06-01",
        "list": "second_presbyterian_members_1842_1892",
        "the_ladder": "LATER EVIDENCE, ALWAYS. The earliest line on this roll is June "
                      "1842, seven years after the scene date, so no record here is an "
                      "1835 fact and every one carries beyond_ticket_window true. The "
                      "congregation was gathered in 1842 out of the First Presbyterian "
                      "Church, organised 1833 by people who were here, which is why the "
                      "surnames overlap the town at all — and the overlap is a lead, "
                      "not a residency. Nothing here mints a person or regrades one; "
                      "T-0513 owns the ladder.",
        "records": records,
        "counts": {
            "roll_lines_read": len(rows),
            "mapped_lines_that_are_not_roll_lines": len(dropped),
            "roll_lines_with_no_how_admitted_cell":
                sum(1 for r in rows if r["how_admitted"] is None),
            "roll_lines_by_list": {s["list"]: sum(1 for r in rows if r["list"] == s["list"])
                                   for s in SECTIONS},
            "distinct_surnames_on_the_roll": len({fold(r["surname"]) for r in rows}),
            "records": len(records),
            "records_with_a_date": sum(1 for r in records if r["describes_date"]),
            "records_whose_date_the_scan_destroyed":
                sum(1 for r in records if not r["describes_date"]),
            "earliest_admission": min([r["describes_date"] for r in records
                                       if r["describes_date"]] or [None]),
            "scene_cutoff": SCENE_CUTOFF,
            "records_on_or_before_the_cutoff":
                sum(1 for r in records if r["describes_date"]
                    and r["describes_date"] <= SCENE_CUTOFF),
        },
    }
    return doc, crosswalk(records, people)


def crosswalk(records, people):
    """The roll against the 1835 layer. Surname AND first initial, or it is a refusal."""
    by_key, surnames = {}, {}
    for rec in records:
        key = fold(rec["surname"])
        surnames.setdefault(key, []).append(rec)
        i = initial(rec["forenames"] or "")
        if i:
            by_key.setdefault((key, i), []).append(rec)

    matched, ambiguous, refused = [], [], []
    for person in people:
        key, i = fold(person["surname"]), initial(person["given"])
        hits = by_key.get((key, i), []) if i else []
        # `source_id` on the ROW, not only on the document: consolidate_resident_evidence
        # reads a crosswalk row for the sources a ruling rests on, and a row that states
        # none is filed as `states_no_source` and cannot be spent onto a card.
        row = {"name": person["name"], "person_id": person["person_id"],
               "household_id": person["household_id"], "grade": person["grade"],
               "source_id": SOURCE_ID}
        if not hits:
            if key in surnames:
                row["candidates_under_that_surname"] = len(surnames[key])
                row["rule"] = ("The surname %r stands on the Second Presbyterian roll "
                               "and no line under it carries the initial %r of %r. A "
                               "surname-only agreement is a refusal."
                               % (person["surname"], (i or "-").upper(), person["name"]))
                refused.append(row)
            continue
        row["rule"] = ("Surname %r folds to the same string as the roll line's, and the "
                       "given name of both begins %s." % (person["surname"], i.upper()))
        row["roll_lines"] = [{"record": h["id"], "as_read": h["as_read"],
                              "admitted": h["cells"]["admitted"],
                              "how_admitted": h["cells"]["how_admitted"],
                              "printed_page": h["locator"]["printed_page"],
                              "a_married_womans_entry": h["cells"]["title"] == "Mrs"}
                             for h in hits]
        (matched if len(hits) == 1 else ambiguous).append(row)

    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_second_presbyterian.py --build. Hand-edit and "
                "--check says so. The 1842-1892 roll of the Second Presbyterian Church "
                "of Chicago against the people data/residents/ holds for July 1835.",
        "generated_by": "tools/read_second_presbyterian.py --build",
        "source_id": SOURCE_ID,
        "ticket": "T-0583",
        "rule": "crosswalk_fergus_1839's rule, imported rather than restated: SURNAME "
                "must match after both are folded AND the first initial of the given "
                "name must match. A surname-only agreement is a REFUSAL and is filed, "
                "because an absent match reads exactly like a pair nobody looked at.",
        "mints_or_regrades": "NOTHING. A line on a roll that opens in June 1842 cannot "
                             "place a person in the town of July 1835, and this file "
                             "makes no proposal that it does. What a match IS: the same "
                             "surname and initial, in Chicago, within seven years — a "
                             "lead for a later pass that is allowed to write people.",
        "the_mrs_rule": "THE ROLL NAMES A WIFE UNDER HER HUSBAND'S NAME — `Cook, Mrs. J. "
                        "L.`, `Fullerton, Mrs. A. N.` — so a line flagged "
                        "a_married_womans_entry that meets a MAN in the 1835 layer has "
                        "met his name, not him: it corroborates that the name was a "
                        "Chicago name in the 1840s and it does not put that man on this "
                        "roll. The flag is carried on every matched line for that reason, "
                        "and no match is suppressed because of it — a suppressed match is "
                        "invisible and a flagged one can be argued with.",
        "what_it_does_not_give": [
            "An 1835 residency, or any part of one.",
            "A death or a departure. The roll's `Dismissed` means dismissed to another "
            "church by letter, and `Deceased` is dated by the roll's own closing, not "
            "by the death.",
            "A household. The roll names wives as `Mrs. <husband's name>` throughout, "
            "so a woman's own forename is frequently not on the page at all.",
        ],
        "counts": {
            "roll_records": len(records),
            "residents_considered": len(people),
            "residents_matched_one_line": len(matched),
            "residents_ambiguous": len(ambiguous),
            "residents_surname_only_refused": len(refused),
        },
        "matched": matched,
        "ambiguous": ambiguous,
        "refused": refused,
    }


def write(path, doc):
    with open(path, "w", encoding="utf-8") as fh:
        if isinstance(doc, str):
            fh.write(doc)
            return
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def self_test() -> int:
    """The rules that do this reading's judging, fired against cases that break them."""
    bad = []

    def want(got, expect, what):
        if got != expect:
            bad.append("%s: expected %r, got %r" % (what, expect, got))

    # 1. the numeral, read where the scan set a letter for it and refused elsewhere
    want(digits("i"), "1", "the scan's i is the printer's 1")
    want(digits("1848."), "1848", "a clean year is read")
    want(digits("l2,"), "12", "the scan's l is the printer's 1")
    want(digits("Sept"), None, "a word is not a numeral")
    want(digits("i8s8"), None, "a token this rule cannot finish is refused, not guessed")
    want(read_date("September i, 1848."), ("1848-09-01", "day"), "a full date is read")
    want(read_date("May 1848."), ("1848-05", "month"), "a date with no day keeps its "
         "precision rather than inventing the first of the month")
    want(read_date("Dismissed."), (None, None), "a cell with no date is refused")

    # 2. the name, split on the printer's comma with the title lifted out
    want(read_name("Kimball, Miss Frances M."), ("Kimball", "Frances M.", "Miss"),
         "a title is not a forename")
    want(read_name("King, Henry W., Jr."), ("King", "Henry W., Jr.", None),
         "a suffix stays with the forenames, and only the FIRST comma splits the cell")
    want(read_name("Ogden,  Mrs.  William  B."), ("Ogden", "William B.", "Mrs"),
         "the roll's Mrs. <husband> form is kept exactly as it stands")

    # 3. and the three of them, on the committed reading itself
    rows, dropped = roll()
    want(bool(rows), True, "the roll still rebuilds out of the committed text")
    want(all(r["printed_page"] >= 153 for r in rows), True,
         "no row is read off a page before the roll begins")
    want(all(r["admitted"] is None or r["admitted"] >= "1842" for r in rows), True,
         "no line on this roll predates the congregation")
    doc, cross = build()
    want(all(r["beyond_ticket_window"] for r in doc["records"]), True,
         "every record is later evidence and says so")
    want(all(r["describes_date"] is None or r["describes_date"] > SCENE_CUTOFF
             for r in doc["records"]), True,
         "nothing dated on or before the scene cutoff reaches a record as an 1835 fact")
    want(doc["counts"]["records_on_or_before_the_cutoff"], 0,
         "and the count that would catch it if one did is zero")
    want(all(not m.get("mints") for m in cross["matched"]), True,
         "the crosswalk proposes and mints nothing")

    if bad:
        print("second presbyterian self-test: " + "; ".join(bad), file=sys.stderr)
        return 1
    print("second presbyterian: the numeral, the name and the ladder all fire")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if "--fetch" in sys.argv:
        local = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--from=")),
                     None)
        text, doc = fetch(local)
        write(TEXT, text)
        write(MAP, doc)
        print("roll text: %d lines; row map: %d printed rows"
              % (len(text.splitlines()), len(doc["rows"])))
        return 0
    doc, cross = build()
    if "--build" in sys.argv:
        write(RECORDS, doc)
        write(CROSSWALK, cross)
        print("  wrote %d records of %d roll lines, and %d matched residents"
              % (len(doc["records"]), doc["counts"]["roll_lines_read"],
                 cross["counts"]["residents_matched_one_line"]))
        return 0
    if "--report" in sys.argv:
        c, x = doc["counts"], cross["counts"]
        print("SECOND PRESBYTERIAN CHURCH OF CHICAGO — the roll of 1842-1892")
        print("  %d roll lines read on printed pages 154-206 %s"
              % (c["roll_lines_read"], c["roll_lines_by_list"]))
        print("  %d distinct surnames; %d lines carry a surname this project holds"
              % (c["distinct_surnames_on_the_roll"], c["records"]))
        print("  earliest admission read: %s; dates the scan destroyed: %d"
              % (c["earliest_admission"], c["records_whose_date_the_scan_destroyed"]))
        print("  against the 1835 layer: %d matched, %d ambiguous, %d surname-only refused"
              % (x["residents_matched_one_line"], x["residents_ambiguous"],
                 x["residents_surname_only_refused"]))
        for row in cross["matched"]:
            line = row["roll_lines"][0]
            print("   %-28s %-46s %s" % (row["name"], line["as_read"][:46],
                                         line["admitted"]))
        return 0
    bad = []
    for path, want in ((RECORDS, doc), (CROSSWALK, cross)):
        if not os.path.exists(path):
            bad.append("%s is not committed" % os.path.basename(path))
        elif json.loads(open(path, encoding="utf-8").read()) != want:
            bad.append("%s no longer rebuilds out of the committed text and row map"
                       % os.path.basename(path))
    if bad:
        print("second presbyterian: " + "; ".join(bad), file=sys.stderr)
        return 1
    print("second presbyterian roll: %d records and %d matched residents rebuild"
          % (len(doc["records"]), cross["counts"]["residents_matched_one_line"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
