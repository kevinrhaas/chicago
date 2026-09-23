#!/usr/bin/env python3
"""The city register of 1839 and the lists of mayors and sheriffs, out of Fergus 1839,
printed pages 38-39 (T-0665).

T-0506 read the alphabetical directory (printed 5-36) and the churches and hotels
(printed 37). T-0664 read the charter election of 2 May 1837 (printed 40-46) and, in
passing, committed the page text of the two leaves BETWEEN them without reading them
out. This reads those two leaves, and they hold three different objects:

  printed 38 (leaf 50)  THE CITY REGISTER — the officers of the city of Chicago in
                        1839, office by office and ward by ward: the mayor, twelve
                        aldermen, the corporation newspaper, the high constable, six
                        assessors, the chief engineer and his two assistants, eight
                        single-holder offices, seven school inspectors, four police
                        constables, six fire wardens and a board of health of three.
  printed 39 (leaf 51)  THE MAYORS OF THE CITY OF CHICAGO, 1837-1873, and THE SHERIFFS
                        OF COOK COUNTY, 1831-1874, each an election-year table, with
                        two coroners who served ex officio between sheriffs.

  tools/read_fergus_1839_register.py --build     write the claims file
  tools/read_fergus_1839_register.py --check     rebuild in memory and diff (the gate)
  tools/read_fergus_1839_register.py --report    the register by office, the two tables
                                                 by year, and what reaches the scene date
  tools/read_fergus_1839_register.py --self-test the assertions, fired on broken input

WHAT DATE THIS IS, and it is the whole difficulty of these two pages. The city register
is 1839's, four years after the scene date. The mayors table BEGINS in 1837, because —
as its own headnote says — Chicago was not a city until March 1837; on 1 July 1835 the
place had no mayor and no aldermen, and every name on printed page 38 holds an office
that did not exist in the town. So the register is biography, never geography: it says
these men were in Chicago in 1839, and it may corroborate a man the project already
holds. It cannot put anybody in the town of 1835.

THE ONE LINE THAT REACHES THE SCENE DATE is in the sheriffs' table, and it is not
printed there — it is derived. Cook County was organised in 1831 and the table gives
ELECTION years, not terms: 1834 Silas W. Sherman, then 1836 Silas W. Sherman. The scene
date falls inside the term the 1834 row opens, so the sheriff of Cook County on 1 July
1835 was Silas W. Sherman. That is an INFERENCE from the table's own cadence and it is
filed as one, in `derivations` and not among the transcribed claims, with the reasoning
and the refusal beside it.

THE COMPILER'S WARNING BINDS THESE PAGES TOO. Printed page 3: the volume is Fergus's
1876 completion, out of Old Settlers' recollections, of a list set up from memory in
1839. The mayors' table runs to 1873 and the sheriffs' to 1874, so both were plainly set
in 1876 and not in 1839 — they are a retrospect, and the 1830s rows are the oldest and
weakest end of one.

THE STRUCTURE IS A LINE MAP, not a sniffer, for the reason read_fergus_1839_election.py
gives: the register runs six offices over three lines apiece and breaks a man's surname
across a line end ("Thoc. / Brock"), and a rule general enough to segment that is a
guess wearing a rule's clothes.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
OUT = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_city_register.json")
COVERAGE = os.path.join(ROOT, "data/research/directories/coverage.json")

LEAF_TO_PRINTED = -12
REGISTER_LEAF, TABLES_LEAF = 50, 51
REGISTER_YEAR = "1839"
SCENE_DATE = "1835-07-01"

WARD_NAME = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth"}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6}

# ---------------------------------------------------------------- printed page 38
# ONE OFFICE, ONE MAN, ONE LINE: (line, office). The line is "Office — Name."; the name
# is parsed off the em-dash, never retyped.
SINGLE = [
    (2, "mayor"), (23, "high_constable"), (29, "city_clerk"),
    # printed "C o elector — Erast us Bowen ." — the OCR broke both the office and the
    # man. The office is written out here because a parser cannot recover it; the NAME
    # is still parsed off the page and keeps its damage.
    (30, "collector"), (31, "treasurer"), (32, "street_commissioner"),
    (33, "city_attorney"), (34, "city_physician"), (35, "city_surveyor"),
    (36, "sealer_of_weights_and_measures"),
]
# The office the OCR destroyed, and the reading that repairs it. Recorded per claim.
OFFICE_OCR_REPAIR = {30: "C  o  elector"}

# THE ALDERMEN: (heading line, ward, [name lines]). Two aldermen to a ward, one to a
# line, under a printed ward heading.
ALDERMEN = [(4, 1, [5, 6]), (7, 2, [8, 9]), (10, 3, [11, 12]),
            (13, 4, [14, 15]), (16, 5, [17, 18]), (19, 6, [20, 21])]

# SIX WARDS ON ONE SEMICOLON-SEPARATED RUN, wrapped over three lines apiece and broken
# mid-surname: (first line, last line, office). Joined, then split on the semicolon the
# page sets between wards.
WARD_RUNS = [(24, 26, "assessor"), (42, 44, "fire_warden")]

# A LIST OF NAMES UNDER ONE OFFICE, wrapped: (first, last, office, expected count).
# The count is the page's own — seven school inspectors, four police constables — and it
# is asserted, because a comma the OCR dropped would silently lose a man.
NAME_RUNS = [(37, 39, "school_inspector", 7), (40, 41, "police_constable", 4)]

# The chief engineer and his two assistants share printed line 27, which carries two
# offices and one name; the assistants' names are on line 28, joined by "and".
ENGINEER_LINE, ASSISTANTS_LINE = 27, 28
# The board of health, printed as three surnames under a collective "Drs." and nothing
# else. Surname-only names cannot meet this project's matching rule, which wants an
# agreeing first initial, so each carries surname_only and expects to be refused.
BOARD_OF_HEALTH_LINE = 45
# The corporation newspaper: an office of the city held by a NEWSPAPER, not a man.
NEWSPAPER_LINE = 22

# ---------------------------------------------------------------- printed page 39
# The two tables, as (first line, last line, office). Each row is "YEAR  Name."
TABLE_RUNS = [
    (3, 34, "mayor_of_chicago"),
    (37, 49, "sheriff_of_cook_county"),
    (53, 59, "sheriff_of_cook_county"),
    (63, 65, "sheriff_of_cook_county"),
]
# The two coroners who served ex officio between sheriffs, each set over three lines.
# (first, last, the year the service opens) — the year is printed inside the sentence,
# not in the table's year column, so it is picked out by the map rather than parsed.
EX_OFFICIO = [(50, 52, "1855"), (60, 62, "1870")]
# The two headnotes the tables carry, each an act of a legislature and a town finding.
HEADNOTES = [(2, "1837-03", "Chicago was incorporated as a city in March 1837"),
             (36, "1831", "Cook County was organized in 1831")]

# THE YEAR COLUMN AS THE OCR SET IT. Seven rows are damaged and every one of them is
# written out, because a general repair rule over a year column is exactly the sniffer
# this file refuses: it would read "i860" as 1860 and would just as happily read a
# printer's error as one. Anything not in this map must parse as four plain digits.
YEAR_OCR_REPAIR = {"1S50": 1850, "1 853": 1853, "1 857": 1857, "1S59": 1859,
                   "i860": 1860, "11864": 1864, "1 1 866": 1866}
YEAR_ROW = re.compile(r"^\s*(\S(?:.*?\S)?)\s\s+([A-Za-z].*)$")


def leaf_lines(leaf: int):
    path = os.path.join(TEXT, "fergus_1839_leaf_%03d.txt" % leaf)
    return open(path, encoding="utf-8").read().splitlines()


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_name(raw: str) -> str:
    """A printed name as a name. The OCR damage is LEFT IN — 'John 11. Kinzie', 'Wm. If.
    Brown', 'Jacob R Ay nor' — because a tidied name cannot be found again on the page.
    Only the punctuation the register sets between and after entries comes off."""
    return flat(raw).strip(" .,;:•*·’'—-")


def after_dash(line: str) -> str:
    """The body of an 'Office — Name.' line. Both dashes the scan uses, and the plain
    hyphen it falls back to when the em-dash did not survive."""
    parts = re.split(r"\s[—–-]\s|—|–", line, maxsplit=1)
    return parts[1] if len(parts) > 1 else line


def ward_of(text: str):
    m = re.match(r"\s*(first|second|third|fourth|fifth|sixth)\s+ward\b", text, re.I)
    return ORDINALS[m.group(1).lower()] if m else None


def parse_year(raw: str):
    """(year as an int, whether this reading repaired the OCR). Four plain digits, or a
    row in the explicit repair map, or nothing — there is no third way in."""
    s = raw.strip()
    if re.fullmatch(r"\d{4}", s):
        return int(s), False
    if s in YEAR_OCR_REPAIR:
        return YEAR_OCR_REPAIR[s], True
    raise AssertionError(
        "the year column of Fergus 1839 printed page 39 holds %r, which is neither four "
        "plain digits nor a row of YEAR_OCR_REPAIR. Add it to the map by eye or fix the "
        "line map — a year is not guessed here." % raw)


def locator(leaf: int, first: int, last: int):
    return {"text_file": "fergus_1839_leaf_%03d.txt" % leaf,
            "lines": [first, last],
            "page": "fergus_1839_leaf_%03d" % leaf,
            "printed_page": leaf + LEAF_TO_PRINTED}


class Builder:
    def __init__(self):
        self.claims = []
        self.warnings = []

    def add(self, leaf, first, last, kind, name, normalized, describes_date,
            town_finding=False, notes=None, quote=None):
        raw = quote if quote is not None else "\n".join(
            leaf_lines(leaf)[first - 1:last])
        n = len(self.claims) + 1
        norm = {"as_printed": flat(raw) if name is None else name, "name": name}
        norm.update(normalized)
        self.claims.append({
            "id": "f1839_r%04d" % n,
            "kind": kind,
            "reading": "transcription_mediated",
            "quote": raw,
            "normalized": norm,
            "locator": locator(leaf, first, last),
            "describes_date": describes_date,
            "entities": [name] if name else [],
            "town_finding": town_finding,
            "notes": notes,
        })

    # ------------------------------------------------------------ printed page 38
    def register(self):
        L, lines = REGISTER_LEAF, leaf_lines(REGISTER_LEAF)

        for ln, office in SINGLE:
            name = clean_name(after_dash(lines[ln - 1]))
            assert name, "leaf %03d line %d yields no name for %s" % (L, ln, office)
            self.add(L, ln, ln, "person", name,
                     {"role": office, "office": office, "ward": None, "ward_name": None,
                      "body": "city_of_chicago"},
                     REGISTER_YEAR,
                     notes=("The OCR set this office as %r; the office is written out by "
                            "this reading and the name is still parsed off the page."
                            % OFFICE_OCR_REPAIR[ln]) if ln in OFFICE_OCR_REPAIR else None)

        for heading, ward, name_lines in ALDERMEN:
            assert ward_of(lines[heading - 1]) == ward, (
                "leaf %03d line %d is not the %s ward heading the map claims"
                % (L, heading, WARD_NAME[ward]))
            for ln in name_lines:
                name = clean_name(lines[ln - 1])
                assert name, "leaf %03d line %d yields no alderman" % (L, ln)
                self.add(L, ln, ln, "person", name,
                         {"role": "alderman", "office": "alderman", "ward": ward,
                          "ward_name": WARD_NAME[ward], "body": "city_of_chicago"},
                         REGISTER_YEAR,
                         notes="The ward is a ward of the CITY of 1839, whose six wards "
                               "were drawn in 1837. It is not a location in the town of "
                               "1835 and places no house.")

        self.add(L, NEWSPAPER_LINE, NEWSPAPER_LINE, "civic", None,
                 {"role": "corporation_newspaper",
                  "value": clean_name(after_dash(lines[NEWSPAPER_LINE - 1]))},
                 REGISTER_YEAR, town_finding=True,
                 notes="An office of the city held by a newspaper rather than a man.")

        for first, last, office in WARD_RUNS:
            body = after_dash(flat("\n".join(lines[first - 1:last])))
            parts = [p for p in (flat(x) for x in body.split(";")) if p]
            assert len(parts) == 6, (
                "leaf %03d lines %d-%d should hold one %s for each of the six wards and "
                "the semicolons yield %d" % (L, first, last, office, len(parts)))
            for part in parts:
                ward = ward_of(part)
                assert ward, "%r carries no ward heading" % part
                name = clean_name(part.split(",", 1)[1]) if "," in part else ""
                assert name, "%r carries no name" % part
                self.add(L, first, last, "person", name,
                         {"role": office, "office": office, "ward": ward,
                          "ward_name": WARD_NAME[ward], "body": "city_of_chicago",
                          "column_run_on": True},
                         REGISTER_YEAR,
                         notes="Six wards share one semicolon-separated run set over "
                               "three printed lines; this claim is one ward of it and "
                               "quotes the whole run.")

        for first, last, office, want in NAME_RUNS:
            body = after_dash(flat("\n".join(lines[first - 1:last])))
            names = [n for n in (clean_name(p) for p in body.split(",")) if n]
            assert len(names) == want, (
                "leaf %03d lines %d-%d should hold %d %ss and the commas yield %d: %r"
                % (L, first, last, want, office, len(names), names))
            for name in names:
                self.add(L, first, last, "person", name,
                         {"role": office, "office": office, "ward": None,
                          "ward_name": None, "body": "city_of_chicago",
                          "column_run_on": True},
                         REGISTER_YEAR,
                         notes="One of %d names the page sets in a single run under this "
                               "office; the claim quotes the whole run." % want)

        eng = lines[ENGINEER_LINE - 1]
        chief = clean_name(after_dash(eng.split(";")[0]))
        assert chief, "leaf %03d line %d yields no chief engineer" % (L, ENGINEER_LINE)
        self.add(L, ENGINEER_LINE, ENGINEER_LINE, "person", chief,
                 {"role": "chief_engineer", "office": "chief_engineer", "ward": None,
                  "ward_name": None, "body": "city_of_chicago"},
                 REGISTER_YEAR,
                 notes="The line carries the chief engineer's name and the heading for "
                       "the assistant engineers, whose names are on the line below.")
        assistants = [clean_name(p) for p in
                      re.split(r"\band\b", flat(lines[ASSISTANTS_LINE - 1]))]
        assistants = [a for a in assistants if a]
        assert len(assistants) == 2, (
            "leaf %03d line %d should hold two assistant engineers and yields %r"
            % (L, ASSISTANTS_LINE, assistants))
        for name in assistants:
            self.add(L, ASSISTANTS_LINE, ASSISTANTS_LINE, "person", name,
                     {"role": "assistant_engineer", "office": "assistant_engineer",
                      "ward": None, "ward_name": None, "body": "city_of_chicago",
                      "column_run_on": True},
                     REGISTER_YEAR,
                     notes="The two assistant engineers share one line under the heading "
                           "printed at the end of the line above.")

        boh = flat(lines[BOARD_OF_HEALTH_LINE - 1])
        body = re.sub(r"\bDrs\.\s*", "", after_dash(boh))
        surnames = [clean_name(p) for p in re.split(r",|\band\b", body)]
        surnames = [s for s in surnames if s]
        assert len(surnames) == 3, (
            "leaf %03d line %d should hold a board of health of three and yields %r"
            % (L, BOARD_OF_HEALTH_LINE, surnames))
        for name in surnames:
            self.add(L, BOARD_OF_HEALTH_LINE, BOARD_OF_HEALTH_LINE, "person", name,
                     {"role": "board_of_health", "office": "board_of_health",
                      "ward": None, "ward_name": None, "body": "city_of_chicago",
                      "surname_only": True, "honorific": "Dr"},
                     REGISTER_YEAR,
                     notes="The page prints three surnames under a collective 'Drs.' and "
                           "no given name. A surname without an initial cannot meet this "
                           "project's matching rule, and this claim expects a refusal "
                           "rather than a match.")

    # ------------------------------------------------------------ printed page 39
    def tables(self):
        L, lines = TABLES_LEAF, leaf_lines(TABLES_LEAF)

        for ln, date, what in HEADNOTES:
            self.add(L, ln, ln, "civic", None, {"role": "constitution", "value": what},
                     date, town_finding=True,
                     notes="A headnote the table prints above itself, and the reason its "
                           "first row falls where it does.")

        for first, last, office in TABLE_RUNS:
            for ln in range(first, last + 1):
                raw = lines[ln - 1]
                m = YEAR_ROW.match(raw)
                assert m, ("leaf %03d line %d is not a YEAR  Name row: %r — the table "
                           "line map is wrong" % (L, ln, raw))
                year, repaired = parse_year(m.group(1))
                name = clean_name(m.group(2))
                assert name, "leaf %03d line %d yields no name" % (L, ln)
                self.add(L, ln, ln, "person", name,
                         {"role": office, "office": office, "ward": None,
                          "ward_name": None,
                          "body": ("city_of_chicago" if office == "mayor_of_chicago"
                                   else "cook_county"),
                          "year_as_printed": m.group(1), "year": year,
                          "year_ocr_repaired": repaired, "ex_officio": False},
                         str(year),
                         notes=("The OCR set the year as %r; this reading repairs it from "
                                "an explicit map, and the table's own ascending order is "
                                "what checks the repair." % m.group(1)) if repaired else
                               "The table prints the year a man was ELECTED, not the term "
                               "he served; the term runs to the next row of the table.")

        for first, last, year in EX_OFFICIO:
            raw = flat("\n".join(lines[first - 1:last]))
            name = clean_name(raw.split(",", 1)[0])
            assert name, "leaf %03d lines %d-%d yield no coroner" % (L, first, last)
            self.add(L, first, last, "person", name,
                     {"role": "sheriff_of_cook_county", "office": "coroner",
                      "ward": None, "ward_name": None, "body": "cook_county",
                      "year_as_printed": None, "year": int(year),
                      "year_ocr_repaired": False, "ex_officio": True},
                     year,
                     notes="A coroner serving as sheriff ex officio between two sheriffs. "
                           "The page sets the span in a sentence rather than in the year "
                           "column, and the year here is the year that service opens.")


# ------------------------------------------------------------------ the derivations
def derivations(claims):
    """What these two pages say about 1 July 1835, which is nothing they print.

    Filed apart from `claims` on purpose: a claim in this repository is a transcription
    of a printed line, and neither of these is printed. Both cite the claim ids they
    rest on, and neither writes anything to the town."""
    by_id = {c["id"]: c for c in claims}

    def rows(office, year):
        return [c["id"] for c in claims
                if c["normalized"].get("office") == office
                and c["normalized"].get("year") == year]

    first_mayor = [c for c in claims
                   if c["normalized"].get("office") == "mayor_of_chicago"][0]
    register_men = sum(1 for c in claims if c["kind"] == "person"
                       and c["locator"]["page"] == "fergus_1839_leaf_%03d" % REGISTER_LEAF)
    e1834, e1836 = rows("sheriff_of_cook_county", 1834), rows("sheriff_of_cook_county", 1836)
    assert len(e1834) == 1 and len(e1836) == 1, (
        "the sheriffs' table should hold exactly one 1834 row and one 1836 row and holds "
        "%d and %d" % (len(e1834), len(e1836)))
    sherman = by_id[e1834[0]]["normalized"]["name"]
    assert by_id[e1836[0]]["normalized"]["name"] == sherman, (
        "the derivation below reads the 1836 row as the same man re-elected, and it is "
        "not: %r then %r" % (sherman, by_id[e1836[0]]["normalized"]["name"]))

    return [
        {
            "id": "f1839_r_d01",
            "what": "The sheriff of Cook County on the scene date was %s." % sherman,
            "kind": "civic",
            "confidence": "inferred",
            "describes_date": SCENE_DATE,
            "rests_on": e1834 + e1836,
            "reasoning": "Fergus's table gives ELECTION years, not terms: the county was "
                         "organized in 1831, the table's rows run 1831, 1832, 1834, 1836, "
                         "1838, and %s stands against both 1834 and 1836. The term the "
                         "1834 row opens therefore covers 1 July 1835, and no other row "
                         "of the table can." % sherman,
            "refusal": "The page does not print a term for any sheriff, and this project "
                       "has read no commission, no county record and no newspaper naming "
                       "the sheriff in July 1835. So this is `inferred` from the table's "
                       "own cadence and may not be graded `documented` on this source. It "
                       "is also a retrospect: the table runs to 1874 and was set in 1876 "
                       "out of recollection, per the compiler's warning on printed page 3.",
            "writes_to_the_town": False,
        },
        {
            "id": "f1839_r_d02",
            "what": "Chicago had no mayor, no aldermen and no city offices on the scene "
                    "date, and none of the %d office-holders in the city register of "
                    "1839 held a city office in 1835, because there were none to hold."
                    % register_men,
            "kind": "civic",
            "confidence": "documented",
            "describes_date": SCENE_DATE,
            "rests_on": [c["id"] for c in claims
                         if c["normalized"].get("role") == "constitution"
                         and c["describes_date"] == "1837-03"] + [first_mayor["id"]],
            "reasoning": "The mayors' table prints its own reason for beginning where it "
                         "does — 'City incorporated, March, 1837' — and its first row is "
                         "%s in 1837, twenty-one months after the scene date. In July "
                         "1835 Chicago was an incorporated TOWN under a board of trustees, "
                         "so every office on printed page 38 postdates the scene."
                         % first_mayor["normalized"]["name"],
            "refusal": "This is a NEGATIVE finding and it is the useful one here: it "
                       "forbids reading the city register back onto the town. It does not "
                       "say who the town's trustees were in 1835 — these two pages do not "
                       "print them, and this reading does not go looking.",
            "writes_to_the_town": False,
        },
    ]


CORPUS = {
    "item": "fergusdirectoryo00ferg",
    "url": "https://archive.org/details/fergusdirectoryo00ferg",
    "what": "Allen County Public Library Genealogy Center scan of Robert Fergus, "
            "Fergus' Directory of the City of Chicago, 1839 (Chicago: Fergus Printing "
            "Company, 1876). 86 leaves. Printed pages 38-39 are leaves 50-51.",
    "committed": True,
    "how": "The page text was committed by T-0664 with tools/fetch_fergus_1839_pages.py, "
           "which is the derivation read_fergus_1839.py describes: archive.org's OCR word "
           "coordinates give each line its left edge, and a line set more than 25 px right "
           "of the median line start of its own page is committed with two leading spaces.",
}

READING_NOTE = (
    "transcription_mediated throughout: archive.org's OCR of the printed page, machine-read "
    "and not checked against the image by eye. The damage is left in every name on purpose — "
    "'John 11. Kinzie', 'Wm. If. Brown', 'Jacob R Ay nor', 'Erast us Bowen' — because a "
    "tidied name cannot be found again on the page. TWO THINGS ARE REPAIRED and both are "
    "written out rather than sniffed: one office heading the OCR destroyed ('C o elector'), "
    "and seven years of the tables' year column, from an explicit map whose result is checked "
    "by the tables' own ascending order. Six lines of the register set all six wards in one "
    "semicolon-separated run wrapped over three printed lines, and a name broken across a "
    "line end ('Thoc. / Brock') is joined before it is split; those claims carry "
    "column_run_on and quote the whole run.")

DATE_NOTE = (
    "1839 AND LATER, NEVER 1835. The city register is the register of 1839, four years after "
    "the scene date; the two tables run to 1873 and 1874. Chicago was not a city until March "
    "1837, which the mayors' table says of itself, so no office on printed page 38 existed in "
    "the town of 1835 and no man is placed in it by holding one. Under the ratified grading "
    "ladder a later appearance alone never makes an 1835 resident, and nothing in this file "
    "mints or regrades anybody. The compiler's warning on printed page 3 binds these pages as "
    "it binds the directory: the volume is Fergus's 1876 completion, out of Old Settlers' "
    "recollections, of a list set up from memory in 1839 — and a table running to 1874 is "
    "plainly 1876's work, not 1839's.")

DERIVATION_NOTE = (
    "TWO FINDINGS ABOUT THE SCENE DATE ARE DERIVED AND ARE NOT CLAIMS. A claim in this "
    "repository is a transcription of a printed line; neither of these is printed. They live "
    "in `derivations`, each citing the claim ids it rests on, each carrying its confidence, "
    "its reasoning and its refusal, and neither writes anything to the town.")


def payload(claims, derived):
    by_office = {}
    for c in claims:
        office = c["normalized"].get("office") or c["normalized"].get("role")
        by_office[office] = by_office.get(office, 0) + 1
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_fergus_1839_register.py --build out of the "
                "committed page text in data/research/directories/text/. Hand-edit and "
                "--check says so. Fergus' Directory of the City of Chicago, 1839, printed "
                "pages 38-39: the city register of 1839 office by office and ward by ward, "
                "the mayors of Chicago 1837-1873, and the sheriffs of Cook County "
                "1831-1874 with the two coroners who served ex officio between them.",
        "generated_by": "tools/read_fergus_1839_register.py --build",
        "source_id": "fergus_chicago_directory_1839",
        "corpus": CORPUS,
        "reading_note": READING_NOTE,
        "date_note": DATE_NOTE,
        "derivation_note": DERIVATION_NOTE,
        "counts": {
            "claims": len(claims),
            "persons": sum(1 for c in claims if c["kind"] == "person"),
            "city_register_persons": sum(
                1 for c in claims if c["kind"] == "person"
                and c["locator"]["printed_page"] == REGISTER_LEAF + LEAF_TO_PRINTED),
            "mayors": by_office.get("mayor_of_chicago", 0),
            "sheriffs": sum(1 for c in claims
                            if c["normalized"].get("role") == "sheriff_of_cook_county"),
            "ex_officio_sheriffs": sum(1 for c in claims
                                       if c["normalized"].get("ex_officio")),
            "town_findings": sum(1 for c in claims if c["town_finding"]),
            "years_ocr_repaired": sum(1 for c in claims
                                      if c["normalized"].get("year_ocr_repaired")),
            "surname_only": sum(1 for c in claims
                                if c["normalized"].get("surname_only")),
            "derivations": len(derived),
            "by_office": {k: by_office[k] for k in sorted(by_office)},
        },
        "derivations": derived,
        "claims": claims,
    }


def build():
    b = Builder()
    b.register()
    b.tables()
    check_tables_ascend(b.claims)
    return b.claims, derivations(b.claims), b.warnings


def check_tables_ascend(claims):
    """The year column, read back. Seven of its rows were repaired from a map, and the
    only check the page itself offers is that both tables ascend. A repair that turned
    1853 into 1S53's neighbour would break it.

    The two ex-officio coroners are held to a different rule, because their year is not
    in the year column at all — it is inside a sentence — so what can be checked is that
    each falls after the sheriff printed above it and no later than the one below."""
    for office in ("mayor_of_chicago", "sheriff_of_cook_county"):
        years = [c["normalized"]["year"] for c in claims
                 if c["normalized"].get("office") == office
                 and not c["normalized"].get("ex_officio")]
        assert years == sorted(years), (
            "the %s table does not ascend after the year repairs: %r" % (office, years))

    printed = sorted(
        ((c["locator"]["lines"][0], c["normalized"]["year"]) for c in claims
         if c["normalized"].get("office") == "sheriff_of_cook_county"
         and not c["normalized"].get("ex_officio")))
    for c in claims:
        if not c["normalized"].get("ex_officio"):
            continue
        line, year = c["locator"]["lines"][0], c["normalized"]["year"]
        before = [y for ln, y in printed if ln < line]
        after = [y for ln, y in printed if ln > line]
        assert before and after and before[-1] < year <= after[0], (
            "the ex-officio service opening in %d is set on leaf line %d, between the "
            "sheriffs elected %r and %r, and it does not sit in that gap"
            % (year, line, before[-1:], after[:1]))


def declared_counts():
    """The per-leaf counts coverage.json declares for T-0665, which is the second opinion
    on the segmenting — the guard T-0571 put on the 1843 directory and T-0664 on the poll."""
    doc = json.load(open(COVERAGE, encoding="utf-8"))
    for dec in doc["declarations"]:
        if dec["ticket"] == "T-0665":
            return dec.get("counts")
    return None


def against_declaration(claims):
    want = declared_counts()
    if want is None:
        return ["coverage.json declares no T-0665 reading, and the reading has to be "
                "declared before it can be checked"]
    got = {}
    for c in claims:
        got[c["locator"]["page"]] = got.get(c["locator"]["page"], 0) + 1
    if got != want:
        return ["coverage.json declares %r and the text yields %r" % (want, got)]
    return []


def report(claims, derived):
    reg = [c for c in claims
           if c["locator"]["printed_page"] == REGISTER_LEAF + LEAF_TO_PRINTED]
    print("the city register of 1839, printed page 38 — %d claims" % len(reg))
    seen = []
    for c in reg:
        office = c["normalized"].get("office") or c["normalized"]["role"]
        if office not in seen:
            seen.append(office)
    for office in seen:
        rows = [c for c in reg if (c["normalized"].get("office")
                                   or c["normalized"]["role"]) == office]
        names = ", ".join(r["normalized"]["name"] or r["normalized"]["value"]
                          for r in rows)
        print("  %-32s %2d  %s" % (office, len(rows), names[:96]))
    for office, label in (("mayor_of_chicago", "mayors of Chicago"),
                          ("sheriff_of_cook_county", "sheriffs of Cook County")):
        rows = [c for c in claims if c["normalized"].get("office") == office
                or (office == "sheriff_of_cook_county"
                    and c["normalized"].get("role") == office)]
        years = [r["normalized"]["year"] for r in rows]
        print("\nthe %s, printed page 39 — %d rows, %d to %d"
              % (label, len(rows), min(years), max(years)))
        for r in rows:
            if r["normalized"]["year"] <= 1840:
                print("    %4d  %-26s %s" % (r["normalized"]["year"],
                                             r["normalized"]["name"],
                                             "ex officio" if r["normalized"]["ex_officio"]
                                             else ""))
        print("    … and %d rows after 1840" % sum(1 for y in years if y > 1840))
    print("\nwhat reaches the scene date, %s — %d derivations, and neither is printed"
          % (SCENE_DATE, len(derived)))
    for d in derived:
        print("  [%s] %s" % (d["confidence"], d["what"]))
        print("      because: %s" % d["reasoning"])
        print("      refusal: %s" % d["refusal"])


def self_test():
    """The assertions, fired on input broken the way the page could break them."""
    ok = 0
    try:
        parse_year("18O5")
    except AssertionError:
        ok += 1
    else:
        print("a year outside the repair map was guessed, not refused", file=sys.stderr)
        return 1
    claims, _, _ = build()
    bent = json.loads(json.dumps(claims))
    for c in bent:
        if c["normalized"].get("office") == "sheriff_of_cook_county" \
                and c["normalized"].get("year") == 1836:
            c["normalized"]["year"] = 1830
    try:
        check_tables_ascend(bent)
    except AssertionError:
        ok += 1
    else:
        print("a year repair that broke the table's order went unnoticed", file=sys.stderr)
        return 1
    bent = json.loads(json.dumps(claims))
    for c in bent:
        if c["normalized"].get("office") == "sheriff_of_cook_county" \
                and c["normalized"].get("year") == 1836:
            c["normalized"]["name"] = "Somebody Else"
    try:
        derivations(bent)
    except AssertionError:
        ok += 1
    else:
        print("the scene-date derivation did not notice that the 1836 row names a "
              "different man", file=sys.stderr)
        return 1
    print("fergus 1839 city register: %d assertions fire when broken" % ok)
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    claims, derived, warnings = build()
    doc = payload(claims, derived)
    if "--report" in sys.argv:
        report(claims, derived)
        for w in warnings:
            print("  warning:", w)
        return 0
    if "--check" in sys.argv:
        bad = against_declaration(claims)
        if bad:
            for b in bad:
                print("fergus 1839 city register:", b, file=sys.stderr)
            return 1
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("fergus 1839 city register: %s does not match the committed text — "
                  "regenerate with --build" % os.path.relpath(OUT, ROOT), file=sys.stderr)
            return 1
        print("fergus 1839 city register: %d claims (%d persons, %d derivations), and "
              "they match the committed text at the counts coverage.json declares"
              % (len(claims), doc["counts"]["persons"], len(derived)))
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    for w in warnings:
        print("  warning:", w)
    print("fergus 1839 city register: %d claims — %d persons (%d in the register of "
          "1839), %d mayors, %d sheriffs of whom %d ex officio, %d town findings, "
          "%d derivations"
          % (len(claims), doc["counts"]["persons"], doc["counts"]["city_register_persons"],
             doc["counts"]["mayors"], doc["counts"]["sheriffs"],
             doc["counts"]["ex_officio_sheriffs"], doc["counts"]["town_findings"],
             doc["counts"]["derivations"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
