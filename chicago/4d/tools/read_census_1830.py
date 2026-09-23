#!/usr/bin/env python3
"""The 1830 federal schedule that contained Chicago, read off the film.

    tools/read_census_1830.py --build    write records/ and resident_crosswalk.json
    tools/read_census_1830.py --check    the generated files still match the text
    tools/read_census_1830.py --self-test  that check is non-destructive and still fires

WHAT WAS READ, AND WHY IT IS NOT CALLED "THE CHICAGO CENSUS". Chicago was enumerated
in 1830 inside the district the enumerator headed "Peoria & Putnam Counties &
Territory attached" — the whole of northern Illinois hung off two organised counties,
because Cook County did not exist until January 1831. The schedule never writes the
word Chicago. So the object here is the DISTRICT, and the Chicago settlement is a run
of households inside it. Anything that says otherwise is reading a later index back
into the page.

THE DEPOSIT. NARA microfilm M19, Illinois, reel 24, republished by the Internet
Archive as item `populationsc18300024unit` (Greene, Morgan, Sangamon, Calhoun, Pike,
Fulton, Knox, Henry, Adams, Hancock, Warren, Mercer, Peoria, Putnam and Jo Daviess
counties). The item carries NO text layer — its own OCR metadata says "language not
currently OCRable" — so nothing here was extracted; the leaves were fetched as
images, cropped and read by eye. Leaves n580 and n582 are the two read for T-0498.
`data/research/census_1830/text/peoria_putnam_1830_leaves_580_582.txt` is that
reading, committed, and every record below stands on one of its lines.

THE READING GRADE is `scan_verified` for every row: the page image itself was read,
not somebody's transcription of it. That is the stronger of the two grades and it is
claimed honestly — but see CONFIDENCE, which is a separate axis and is where the
hand's ambiguity is recorded.

CONFIDENCE. `documented` where the hand is unambiguous. `inferred` where letters are
genuinely open and the note carries the alternates. Nothing here is `conjectural`,
because a name nobody can read is not written down as a guess — it is written down as
what the ink does, and the alternates go in the note.

NORMALIZED is this project's spelling of the same person. It differs from `as_read`
only where the identification is secure and the reason is stated in NORMALIZE below.
Where it is not secure the normalized form is the reading, uppercased, and the guess
lives in the resident crosswalk as a CANDIDATE where it can be refused.

1830 IS FIVE YEARS EARLY, and this file mints nothing. A head of family on this
schedule stood in the district in the summer of 1830. Whether he was in Chicago on
1 July 1835 is a question for T-0513/T-0514, which have the ladder; the crosswalk
this tool writes is the input to that and not a substitute for it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = ROOT / "data" / "research" / "census_1830"
TEXTDIR = DOMAIN / "text"
# The two files --build owns, named once so that --check cannot go looking for a
# different set than --build writes (T-0856).
GENERATED = ("records/schedule_chicago_1830.json", "resident_crosswalk.json")
# Every committed reading of a leaf of this division, in leaf order. One file per pass:
# a pass declares the leaves it read and appends nothing to anybody else's file, so a
# later reader can see which run read which page without reading a diff.
TEXTS = ("peoria_putnam_1830_leaves_576_578.txt",
         "peoria_putnam_1830_leaves_580_582.txt",
         "peoria_putnam_1830_leaf_584.txt")
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SOURCE_ID = "census_1830_peoria_county_chicago_precinct"
TICKET = "T-0498, T-0605, T-0757"

# The film item, fixed so a later run can go back to the same pixels. Every record's
# locator cites the _w2400 derivative, which is what the leaves were read at. The item
# also serves a FULL-RESOLUTION derivative at .../page/{leaf}.jpg — about twice the
# linear resolution — and T-0757 re-read n586's family column and re-counted n576's and
# n580's name rows off that one. Both URLs are stable; the locators are not rewritten,
# because the reading they carry was made at the magnification they name.
ITEM = "populationsc18300024unit"
IMAGE_URL = "https://archive.org/download/%s/page/{leaf}_w2400.jpg" % ITEM
FULL_RES_IMAGE_URL = "https://archive.org/download/%s/page/{leaf}.jpg" % ITEM

# Rows whose letters are genuinely open. The value is what else the ink could be —
# never a preference, and never resolved by what would be convenient.
UNCERTAIN = {
    ("n580", 4): "The surname is four or five letters ending -hry/-lby: 'Sehry' as written, "
                 "'Selby' and 'Sebry' are equally available. No town person is claimed from it.",
    ("n580", 9): "The given name's first letter is an R or a B and the rest is 'ectel'/'ectal'. "
                 "The surname 'Vermett' is clear. A Vermet/Vermette family traded on the "
                 "Chicago river, which is a reason to look and not a reason to read.",
    ("n580", 16): "'Wellmacker' as written; 'Wellmaker' and 'Wallmacker' are available.",
    ("n580", 19): "'Vernosdal' as written; the Dutch 'Van Nosdal'/'Vannostrand' forms are "
                  "available and none of them is legible as such on the page.",
    ("n580", 20): "'Barkee' as written; 'Barker' is available — the final letter is a long e "
                  "or an r with no shoulder.",
    ("n580", 24): "'Julius Paren' as written. The French 'Pare'/'Paren' and 'Julien' are "
                  "available; the given name's ending is -ius or -ien.",
    ("n580", 25): "'Paylin' as written; 'Poylin' and 'Baylin' are available.",
    ("n580", 26): "'Murer' as written; 'Murier', 'Mercer' and 'Miner' are available.",
    ("n580", 30): "The given name is written 'Clouded' or 'Cloudes' — it is the French Claude "
                  "under an English hand, and the surname is the same 'LaFramboy' the line "
                  "above it carries.",
    ("n580", 31): "'Seco' as written, with no terminal r visible; 'Secor' is available and is "
                  "the form the later Chicago record uses.",
    ("n582", 10): "'Perkee' as written; 'Perkes', 'Parkee' and the French 'Pothier' are "
                  "available. The hand does not settle it.",
    ("n582", 16): "'Norman' as written; 'Naman' and 'Noman' are available.",
    ("n582", 22): "'Coval' as written; 'Covall', 'Covel' and 'Cowal' are available.",
    ("n582", 25): "'Mice' as written; 'Rice' and 'Nice' are available — the initial is a "
                  "capital M or R.",
    ("n582", 26): "'Gunner' as written; 'Gonier', 'Gunver' and 'Garnier' are available. A "
                  "French form is likely on this page and is not legible as one.",
}

# The only places this project's spelling departs from the reading, each with the
# reason it may. Nothing is normalised toward a famous name because it would be nice.
NORMALIZE = {
    "William Skammershorn": ("WILLIAM SCHERMERHORN",
        "The hand writes 'Skammershorn'; Schermerhorn is the same Dutch name and the "
        "enumerator spelt several of them phonetically on this leaf."),
    "Antoine Uilmet": ("ANTOINE OUILMETTE",
        "Ouilmette, the Grosse Pointe trader whose name the village of Wilmette carries. "
        "'Uilmet' is the enumerator dropping the leading O, which he does elsewhere."),
    "Joseph LaFramboy": ("JOSEPH LAFRAMBOISE",
        "LaFramboise, the trading family of the Chicago and St Joseph country. The "
        "enumerator writes the French -oise as -oy throughout this leaf."),
    "Clouded L Framboy": ("CLAUDE LAFRAMBOISE",
        "The same family, one line below Joseph. The given name is Claude under an "
        "English hand; the surname is written 'L, Framboy' with the article split off."),
    "John B Beaubien": ("JEAN BAPTISTE BEAUBIEN",
        "The enumerator anglicises Jean Baptiste to John B here and for two other men "
        "on this leaf; for Beaubien the identification is not in doubt."),
    "Archibald Clybourn": ("ARCHIBALD CLYBOURN",
        "Spelt as the project spells it. Recorded here so the pair is visible."),
    "U S Garrison Fort Dearborn — Maj John Fowle Commr": ("U.S. GARRISON, FORT DEARBORN",
        "Not a person. The enumerator braces two lines together and counts the garrison "
        "as one household under its commanding officer; the record is kept as an "
        "institution and is marked as one."),
}

# What each leaf's own totals row prints in the first five male columns, read off the
# page. Carried as a calibration the next reader can check a re-count against; the
# remaining columns of the totals row were not read and are not claimed.
LEAF_TOTALS = {
    "n576": {"first_five_male_columns_as_read": [25, 33, 23, 15, 39], "entries": 55,
             "page": 299, "division_page": 1, "ticket": "T-0605",
             "note": "As CORRECTED by the enumerator. He struck and rewrote six of the nine "
                     "cells and the recapitulation on n586 carries the same six corrections, "
                     "which is what binds this leaf to this division. The 55 entries were "
                     "RE-COUNTED for T-0757 off the full-resolution image in two crops "
                     "overlapping by one row (Hiram Cleaveland), independently of T-0605's "
                     "four crops, and stand. n586's page-1 family cell, re-read at the same "
                     "magnification, is 55 and not the 53 T-0605 read — so this leaf and the "
                     "recapitulation now agree."},
    "n578": {"first_five_male_columns_as_read": [37, 16, 29, 21, 37], "entries": 56,
             "page": 300, "division_page": 2, "ticket": "T-0605"},
    "n580": {"first_five_male_columns_as_read": [20, 9, 9, 2, 3], "entries": 39,
             "page": 301, "division_page": 3, "ticket": "T-0498",
             "note": "T-0498 read the fifth column as 3; the recapitulation's third row, "
                     "which is this leaf's totals row, prints 38. The reading is left as "
                     "T-0498 made it and the disagreement is recorded rather than patched. "
                     "The 39 entries were RE-COUNTED for T-0757 off the full-resolution image "
                     "in two crops overlapping by one row (John Paylin) and stand. n586's "
                     "page-3 family cell is 88 at that magnification and is NOT 38 or 39, so "
                     "this leaf and the recapitulation remain the division's one open "
                     "disagreement."},
    "n582": {"first_five_male_columns_as_read": [16, 5, 14, 8, 10], "entries": 28,
             "page": 302, "division_page": 4, "ticket": "T-0498"},
    "n584": {"first_five_male_columns_as_read": [15, 8, 8, 5, 13], "entries": 22,
             "page": 303, "division_page": 5, "ticket": "T-0605"},
}

# The recapitulation leaf. It carries no head of family and mints no record; it is here
# because it is the evidence that the names end on n584 and begin on n576.
RECAPITULATION = {
    "image": "n586",
    "page": 304,
    "text_file": "peoria_putnam_1830_recapitulation_n586.txt",
    "families_per_page_as_read": {"1": 55, "2": 56, "3": 88, "4": 28, "5": 22},
    "division_total_as_read": 199,
    "read_at": "Full-resolution page derivative, %s, 7170 x 6529 px — twice the linear "
               "resolution of the _w2400 derivative every record's locator cites. Cells "
               "autocontrasted and enlarged 7x; the two open cells 10x to 12x beside known "
               "glyphs from this same leaf. T-0757." % FULL_RES_IMAGE_URL.format(leaf="n586"),
    "image_url_full_res": FULL_RES_IMAGE_URL.format(leaf="n586"),
    "superseded_reading": "T-0605 read page 1 as 53 off the _w2400 derivative and offered 197 "
                          "as available for the total. T-0757 re-read both at twice that "
                          "magnification: page 1 is 55 (both digits are this hand's 5, "
                          "identical to the 5 of '15' in the page-1 male row and unlike the 3 "
                          "of '23' beside it) and the total is 199 (the leading 1 is carried "
                          "in on an approach stroke; both following figures are 9s).",
    "discrepancy": "The family column as re-read sums to 249, not to the 199 written under it, "
                   "and the leaves as read carry 200 heads. ONE cell of the five now disagrees "
                   "with the leaf it totals, not two: page 1 was a reading error and is "
                   "corrected to 55, which is what n576 carries; page 3 prints 88 against the "
                   "39 heads on n580 and is a real disagreement, left open. Recorded, not "
                   "resolved: nothing in this domain is graded on it.",
    "arithmetic_observation_not_adopted": "With page 3 taken as 38 the column would sum to 199 "
                   "exactly, so the copyist's own total is consistent with 38 and with nothing "
                   "else. That is an observation about his arithmetic and NOT a reading: the "
                   "ink is unambiguously 88 at full resolution (both digits are closed "
                   "figure-eights, matching the 8 of the page-3 male row's '38' and the 8 of "
                   "the page-4 family cell's '28'), and this project does not correct a page "
                   "to make a sum work. 38 would in any case still be one short of n580's 39.",
    "leaf_counts_re_derived": "T-0757 re-counted the name rows of n576 and n580 off the "
                   "full-resolution images, independently of T-0498's and T-0605's crops, in "
                   "two crops per leaf overlapping by one row so that no row falls in a seam "
                   "(Hiram Cleaveland on n576, John Paylin on n580). Both stand: 55 and 39.",
}


def read_text():
    """(text_file, line_number, leaf, entry, as_read) for every transcribed row.

    Read in LEAF order, not file order, so the records come out in the order the
    enumerator walked the division rather than the order the passes read it.
    """
    rows = []
    for name in TEXTS:
        path = TEXTDIR / name
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            m = re.match(r"^(n\d+)\t(\d+)\t(.+)$", line)
            if m:
                rows.append((name, n, m.group(1), int(m.group(2)), m.group(3).strip()))
    rows.sort(key=lambda r: (int(r[2][1:]), r[3]))
    return rows


def normalized_for(as_read: str) -> tuple:
    if as_read in NORMALIZE:
        return NORMALIZE[as_read]
    return (as_read.upper(), None)


def build_records():
    rows = read_text()
    records = []
    for text_file, line_no, leaf, entry, as_read in rows:
        norm, why = normalized_for(as_read)
        uncertain = UNCERTAIN.get((leaf, entry))
        note = []
        if uncertain:
            note.append("READING OPEN. " + uncertain)
        if why:
            note.append("NORMALISED. " + why)
        note.append("Entry %d of %d on leaf %s — page %d of the printed schedule, page %d of "
                    "5 in the enumerator's division headed 'Peoria & Putnam Counties & "
                    "Territory attached'. Presence in that district in the summer of 1830; "
                    "not a Chicago residence, and never an 1835 one."
                    % (entry, LEAF_TOTALS[leaf]["entries"], leaf,
                       LEAF_TOTALS[leaf]["page"], LEAF_TOTALS[leaf]["division_page"]))
        records.append({
            "id": "census1830_%s_%03d" % (leaf, entry),
            "as_read": as_read,
            "normalized": norm,
            "locator": {
                "image": leaf,
                "entry": entry,
                "line": line_no,
                "text_file": text_file,
                "item": ITEM,
                "image_url": IMAGE_URL.format(leaf=leaf),
            },
            "read_for": LEAF_TOTALS[leaf]["ticket"],
            "reading": "scan_verified",
            "confidence": "inferred" if uncertain else "documented",
            "notes": " ".join(note),
            "institution": as_read.startswith("U S Garrison"),
        })
    return records


# --- the crosswalk to the town's own people -------------------------------------

def town_people():
    """Every person in the town's households, by (surname, given) and by surname.

    The household FILE NAMES cannot be used for this: the ids run
    `hh_clybourne_archibald` beside `hh_ll_bennet_bailey` and `hh_doc_h_b_clarke`,
    where the surname is in a different position each time. `persons[].name` is the
    project's own spelling of the person and is what a reading has to be matched
    against.
    """
    by_pair, by_surname = {}, {}
    for path in sorted(HOUSEHOLDS.glob("hh_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for person in doc.get("persons") or []:
            name = str(person.get("name") or "").strip()
            parts = name_parts(name)
            if not parts:
                continue
            sur, giv = parts
            by_pair.setdefault((sur, giv), []).append((path.stem, name))
            by_surname.setdefault(sur, []).append((path.stem, name))
    return by_pair, by_surname


# The town spells several people with a second name in brackets — the Potawatomi and
# French names Chicago knew them by ("Billy Caldwell (Sauganash)", "Alexander Robinson
# (Che-che-pin-qua)"). Taking the last word of that as a surname turns Robinson into
# Che-che-pin-qua and loses the match, so the bracket is cut before the split. It is
# cut and not read: what is inside it is a name this project should carry, and doing
# that properly is a ticket of its own rather than a side effect of a census crosswalk.
BRACKET = re.compile(r"\([^)]*\)")
SUFFIXES = ("jr", "sr", "ii", "iii", "esq")
TITLES = ("mr", "mrs", "miss", "dr", "maj", "col", "capt", "rev", "the")


def name_parts(name: str):
    name = BRACKET.sub(" ", str(name))
    words = [w for w in re.split(r"[^A-Za-z]+", name) if w]
    words = [w for w in words if w.lower() not in TITLES]
    while words and words[-1].lower() in SUFFIXES:
        words.pop()
    if len(words) < 2:
        return None
    return words[-1].lower(), words[0].lower()


def surname_key(surname: str) -> str:
    """A surname reduced only as far as spelling variation this project has SEEN.

    Deliberately timid. It drops a silent terminal e (Clybourn/Clybourne — the town
    spells it with one and the enumerator without), collapses a doubled consonant,
    and does nothing else. It never makes two names equal; it only makes them worth
    LOOKING at, and everything it finds is written down as a candidate, not a merge.
    """
    s = surname.lower()
    s = re.sub(r"([a-z])\1", r"\1", s)
    s = re.sub(r"e$", "", s)
    return s


def build_crosswalk(records):
    by_pair, by_surname = town_people()
    by_variant = {}
    for sur, entries in by_surname.items():
        by_variant.setdefault(surname_key(sur), []).extend(entries)

    matched, variants, candidates, refusals = [], [], [], []
    institutions = []
    for rec in records:
        if rec["institution"]:
            institutions.append({
                "record_id": rec["id"],
                "outcome": "not_a_person",
                "source_id": SOURCE_ID,
                "as_read": rec["as_read"],
                "household": None,
                "rule": "%r is the United States garrison entered as one household under its "
                        "commanding officer. It is not a person and may never reach one: the "
                        "line names no soldier, and Major John Fowle is named as the officer "
                        "commanding rather than enumerated as a head of family. Ruled here so "
                        "the one record on these leaves that can never be crosswalked is not "
                        "left looking unexamined." % rec["as_read"],
            })
            continue
        parts = name_parts(rec["normalized"])
        if not parts:
            continue
        sur, giv = parts
        exact = by_pair.get((sur, giv))
        if exact:
            hid, town_name = exact[0]
            matched.append({
                "record_id": rec["id"],
                "outcome": "earlier_evidence",
                "source_id": SOURCE_ID,
                "as_read": rec["as_read"],
                "normalized": rec["normalized"],
                "household": hid,
                "town_name": town_name,
                "rule": "Surname and given name both agree between the 1830 reading %r and "
                        "the town person %r in household %s. The 1830 line is carried as "
                        "EARLIER EVIDENCE for that person and grades nothing on its own."
                        % (rec["as_read"], town_name, hid),
                "grade": "earlier_evidence",
            })
            continue
        near = [e for e in by_variant.get(surname_key(sur), [])
                if name_parts(e[1]) and name_parts(e[1])[1] == giv]
        if near:
            hid, town_name = near[0]
            variants.append({
                "record_id": rec["id"],
                "outcome": "surname_variant_candidate",
                "source_id": SOURCE_ID,
                "as_read": rec["as_read"],
                "normalized": rec["normalized"],
                "household": hid,
                "town_name": town_name,
                "rule": "The given names agree and the surnames differ only by a silent "
                        "terminal e or a doubled consonant: the 1830 reading %r against the "
                        "town person %r. CANDIDATE, not a merge — the identification is "
                        "T-0513's to make with the rest of the evidence in front of it."
                        % (rec["as_read"], town_name),
                "grade": "candidate",
            })
            continue
        same_surname = by_surname.get(sur) or by_variant.get(surname_key(sur))
        if same_surname:
            others = sorted({"%s (%s)" % (n, h) for h, n in same_surname})
            refusals.append({
                "record_id": rec["id"],
                "outcome": "refused_surname_only",
                "source_id": SOURCE_ID,
                "a": rec["as_read"],
                "b": "; ".join(others),
                "rule": "The 1830 reading %r shares only a surname with the town person(s) "
                        "%s. A surname match is a clue and not an identity, so it is REFUSED "
                        "rather than merged, and the refusal is written down so the next "
                        "sweep does not make the same match again."
                        % (rec["as_read"], "; ".join(others)),
                "evidence": ["census_1830 record %s" % rec["id"],
                             "data/residents/households/"],
            })
        else:
            candidates.append({
                "record_id": rec["id"],
                "outcome": "no_surname_in_town",
                "source_id": SOURCE_ID,
                "as_read": rec["as_read"],
                "normalized": rec["normalized"],
                "household": None,
                "note": "No person in the town's 825 households carries this surname. Either "
                        "the man had gone by 1835, or he lived in the part of the district "
                        "that was never Chicago — the Fox River and Du Page settlements are "
                        "in it too — or he is somebody the reconstruction has not found. All "
                        "three are findings and none of them is settled here.",
            })
    return matched, variants, candidates, refusals, institutions


def build(out: Path = DOMAIN):
    records = build_records()
    matched, variants, candidates, refusals, institutions = build_crosswalk(records)
    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_census_1830.py --build out of the committed readings "
                "at data/research/census_1830/text/ (%s). Hand-edit and --check says so. Every "
                "row is a hand reading of the film image named in its locator; the film "
                "carries no text layer and nothing here was extracted." % ", ".join(TEXTS),
        "generated_by": "tools/read_census_1830.py --build",
        "source_id": SOURCE_ID,
        "describes_date": "1830",
        "ticket": TICKET,
        "district": {
            "as_written": "Peoria & Putnam Counties & Territory attached",
            "note": "The enumerator's own heading, written once on leaf n580 and dittoed. "
                    "The schedule never writes 'Chicago'; there was no Chicago to write.",
            "leaves": "n576, n578, n580, n582, n584 — printed pages 299 to 303, being pages "
                      "1 to 5 of one enumerator's division, and n586 (page 304) its "
                      "recapitulation. The division is READ COMPLETE: every leaf of it has "
                      "been read head by head, and n586 carries no head of family.",
            "how_the_leaves_were_bound_to_the_district": "By the recapitulation on n586, whose "
                      "five page rows ARE the totals rows of n576, n578, n580, n582 and n584 — "
                      "page 1's row carries the same six struck-and-rewritten cells as n576's. "
                      "The heading itself is written on n580 only; the other four leaves leave "
                      "the county cell empty. T-0498 had guessed that n576-n579 belonged to the "
                      "county before this district, and the recapitulation disproves it for the "
                      "even leaves.",
        },
        "recapitulation": RECAPITULATION,
        "the_ladder": "An 1830 head of family is EARLIER EVIDENCE and never an 1835 residence "
                      "on its own. Under the ladder ratified 2026-09-03, this schedule "
                      "corroborates and dates; it does not mint.",
        "counts": {
            "records": len(records),
            "leaves": sorted(LEAF_TOTALS, key=lambda k: int(k[1:])),
            "by_leaf": {k: v["entries"] for k, v in LEAF_TOTALS.items()},
            "documented": sum(1 for r in records if r["confidence"] == "documented"),
            "inferred": sum(1 for r in records if r["confidence"] == "inferred"),
            "institutions": sum(1 for r in records if r["institution"]),
        },
        "leaf_totals_as_read": LEAF_TOTALS,
        "records": records,
    }
    (out / "records").mkdir(parents=True, exist_ok=True)
    write(out / "records" / "schedule_chicago_1830.json", doc)

    cross = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_census_1830.py --build. Every 1830 head of family "
                "against the town's 825 households, positive and negative alike. A match on "
                "surname AND given name is carried as EARLIER EVIDENCE; a match on surname "
                "alone is REFUSED and the refusal is written down, because an unrecorded "
                "refusal reads exactly like a pair nobody has looked at.",
        "generated_by": "tools/read_census_1830.py --build",
        "source_id": SOURCE_ID,
        "ticket": TICKET,
        "counts": {"matched": len(matched), "surname_variant_candidates": len(variants),
                   "no_surname_in_town": len(candidates),
                   "surname_only_refused": len(refusals),
                   "not_a_person": len(institutions)},
        "calibration": {
            "nhgis_peoria_county_1830_total_population": 1236,
            "note": "NHGIS ds5 1830 county table gives Peoria County 1,236 persons. The "
                    "division read here is complete at five leaves and %d heads of family, and "
                    "the enumerator's own recapitulation totals it at 199 families and 1,113 "
                    "free white males against 484 females as read. The NHGIS figure is a "
                    "COUNTY total and this division is Peoria and Putnam and everything hung "
                    "off them, so the two are still not the same object and no ratio is "
                    "claimed from them. What can now be checked is the division against "
                    "itself, and it does not close — see the recapitulation block."
                    % len(records),
            "verified": False,
        },
        "matched": matched,
        "surname_variant_candidates": variants,
        "not_a_person": institutions,
        "no_surname_in_town": candidates,
        "refusals": refusals,
    }
    write(out / "resident_crosswalk.json", cross)
    print("census_1830: %d records, %d matched, %d surname-variant candidates, %d "
          "surname-only refusals, %d with no surname in town"
          % (len(records), len(matched), len(variants), len(refusals), len(candidates)))
    return 0


def write(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check(quiet: bool = False) -> int:
    """Re-derive into a scratch tree and diff. It never writes into the domain.

    T-0856. This used to re-derive IN PLACE — snapshot the committed bytes, call
    `build()` over the top of them, compare. That reads as a check and behaves as a
    repair: the first run printed FAIL and left the file mended, the second printed
    pass, and the drift the first run found was gone before anyone could look at it.
    Which is exactly the state this ticket was filed from — `--check` had been red on
    `dev` for a day, and running it to confirm that was what silently healed it. A gate
    built on it would have been worse than none: green on the second commit of every
    day, and leaving the working tree dirty for every step of check.sh below it.
    """
    bad = []
    for rel in GENERATED:
        if not (DOMAIN / rel).exists():
            bad.append("%s: missing — run --build" % rel)
    if bad:
        for b in bad:
            print("FAIL %s" % b)
        return 1
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        build(out)
        for rel in GENERATED:
            if (out / rel).read_text(encoding="utf-8") != \
                    (DOMAIN / rel).read_text(encoding="utf-8"):
                bad.append("%s: does not match what the committed reading rebuilds — "
                           "either it was hand-edited, or something it derives from "
                           "moved underneath it. Run --build and read the diff." % rel)
    for b in bad:
        print("FAIL %s" % b)
    if not bad and not quiet:
        print("read_census_1830: the generated files match the committed reading")
    return 1 if bad else 0


def self_test() -> int:
    """--check must stay non-destructive, and must still catch a real drift."""
    failures = []
    before = {rel: (DOMAIN / rel).read_bytes() for rel in GENERATED}

    if check(quiet=True) != 0:
        failures.append("--check is red on the committed tree, so nothing below can be read")
    for rel, blob in before.items():
        if (DOMAIN / rel).read_bytes() != blob:
            failures.append("--check REWROTE %s: a gate that repairs what it checks "
                            "reports green on the second run" % rel)

    # A real drift, made and put back. The crosswalk is the file that moved under
    # T-0856, so it is the one the fixture edits.
    victim = DOMAIN / "resident_crosswalk.json"
    doc = json.loads(victim.read_text(encoding="utf-8"))
    doc["counts"]["matched"] = doc["counts"]["matched"] + 1
    try:
        victim.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        if check(quiet=True) == 0:
            failures.append("--check passed a hand-edited resident_crosswalk.json")
        if victim.read_bytes() == before["resident_crosswalk.json"]:
            failures.append("--check REPAIRED the hand-edit it was asked to report")
    finally:
        for rel, blob in before.items():
            (DOMAIN / rel).write_bytes(blob)

    for f in failures:
        print("FAIL %s" % f)
    if not failures:
        print("read_census_1830 --check: non-destructive, and still red on a drift")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.build:
        return build()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
