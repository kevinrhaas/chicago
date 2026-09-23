#!/usr/bin/env python3
"""Father St. Cyr's Chicago register: the marriage page and the death page (T-0573).

    tools/read_st_cyr_register.py --build       write the records, the claims, the crosswalk
    tools/read_st_cyr_register.py --check       the gate
    tools/read_st_cyr_register.py --self-test   the gate's assertions still fire when broken

WHAT IS READ. Two pages of genealogytrails.com/ill/cook, both printing the first Chicago
Catholic church register out of the *Illinois Catholic Historical Review*, vol. 4 (July
1921 - April 1922): `marriages_catholic.txt`, the marriage register with the article's
commentary around it, and `church_catholicdeaths.txt`, the death and burial page. Nobody
in this project has seen the register, and nobody here has seen the Review either: the
reading is `transcription_mediated` twice over on every row.

THE COUNT THE TICKET CARRIED WAS WRONG, AND THE PAGE SAYS SO ITSELF. T-0573 was written
against "87 marriages of 1834-1839". The page carries 128. Eighty-seven is Father
O'Meara's SUBTOTAL, printed in the article's own tally near the foot of the page:

    Rev. John Mary Iranaeus St. Cyr, baptisms, 46; marriages, 22. Rev. Bernard Schaeffer,
    baptisms, 31; marriages, 18. Rev. Timothy O'Meara, baptisms, 195; marriages, 87.
    Besides these officiating clergymen there were 6 baptisms and 1 marriage by John F.
    Plunkett...

22 + 18 + 87 + 1 = 128, and this parse independently returns exactly 22 St. Cyr, 18
Schaeffer, 87 O'Meara and 1 Plunkett. That agreement is the strongest check available on
a list nobody can re-count against the book, so it is an ASSERTION here and not a remark:
`--check` fails if any of the four moves. The per-year figures the ticket carried (1836:8,
1837:36, 1838:21, 1839:12) were wrong for the same reason and the true ones are 1834:4,
1835:6, 1836:11, 1837:50, 1838:36, 1839:21.

NAMES ARE PEOPLE, which is `data/research/church/README.md`'s rule and the reason a row
here is a PERSON and not a marriage. An entry naming a groom, a bride and two witnesses
carries four readings. The 128 entries carry 513 named readings, and the entry-level
structure is kept beside them in `entries` so the marriage is not lost in the process.
The officiating priest is NOT one of the readings: he is the recorder, he is carried in
every row's `cells.priest`, and his own dates are a claim rather than a row.

TRAP 1, THE ONE THAT WOULD PLANT THREE HOUSEHOLDS IN THE WRONG TOWN. This page is titled
"First Chicago Marriage Records" and it is NOT all Chicago. Footnote 5 hangs off the third
of three May 1834 entries and reads: "They all (the last three couples) were married in
the home of Hy Durbin in the presence of several witnesses, Bear Creek, Sangamon County,
Illinois." The article's closing prose says the same thing again. So entries 2, 3 and 4
carry `place: "Bear Creek, Sangamon County, Illinois"` and `at_chicago: false` ON THE ROW
ITSELF — twelve readings of eight people who were never in this town on that day — and
the gate fails if that count moves. Entry 1 (N. Murphy and Mrs. M. Frauner) is Chicago:
the article names it as the first marriage St. Cyr performed here.

TRAP 2, THE BOURASSA PAIR. `Mark Bourassa` marries Josette Chevalier in March 1835 on the
marriage page; `Leon Bourrassa` buries a 28-day-old son on 2 July 1835 on the death page.
The ticket forbids joining them without a stated rule. They are NOT joined: the surnames
do not even fold equal (`bourassa` against `bourrassa`) and the forenames are different
names, not spellings of one. The refusal is written out in `crosswalk.json`, because an
absent merge and an unexamined pair look identical from the outside.

THE CROSSWALK. Only the SCENE-YEAR entries are crosswalked — the 1835 marriages and the
1835 deaths — against the named persons of `data/residents/`. The rule: surnames must
fold equal (case, punctuation, apostrophes), AND forenames must agree initial for initial
in one direction or the other. Surname-only agreement is a REFUSAL however good it looks.
Everything the rule reaches is a CANDIDATE, and a candidate becomes a merge only when a
second attribute agrees as well; that happened exactly once, for Thomas Owen.

THE LADDER, ratified 2026-09-03. A source later than 1835 never mints an 1835 resident on
its own. Most of this page is later than 1835 — 118 of the 128 entries are 1836-1839 —
and nothing here creates a resident. It corroborates, it enriches, and above all it DATES:
every row carries `describes_date`.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GT_TEXT = ROOT / "data" / "research" / "genealogytrails" / "text"
CHURCH = ROOT / "data" / "research" / "church"
RESIDENTS = ROOT / "data" / "residents" / "households"

MARRIAGE_CACHE = "marriages_catholic.txt"
DEATH_CACHE = "church_catholicdeaths.txt"
MARRIAGE_TEXT = "st_cyr_marriages_1834_1839.txt"
DEATH_TEXT = "st_cyr_deaths_1834_1837.txt"

MARRIAGE_LIST = "st_cyr_marriages_1834_1839"
DEATH_LIST = "st_cyr_deaths_1834_1837"

TICKET = "T-0573"
SOURCE_ID = "st_cyr_register_ichr_v4"

# The article's own tally, and the four spellings the register signs with.
PRIESTS = ("J. M. I. Saint Cyr", "Schaeffer", "T. O'Meara", "John F. Plunkett")
EXPECTED_BY_PRIEST = {"J. M. I. Saint Cyr": 22, "Schaeffer": 18,
                      "T. O'Meara": 87, "John F. Plunkett": 1}
EXPECTED_MARRIAGES = 128
EXPECTED_BY_YEAR = {"1834": 4, "1835": 6, "1836": 11,
                    "1837": 50, "1838": 36, "1839": 21}
EXPECTED_READINGS = 513
EXPECTED_BEAR_CREEK_ENTRIES = 3
EXPECTED_DEATHS = 11

MONTHS = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "april": "04",
          "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
          "aug": "08", "sept": "09", "sep": "09", "oct": "10", "nov": "11",
          "dec": "12"}

DATE_RE = re.compile(
    r"^(?:(?P<mon>[A-Za-z]+\.?)[ ]*(?P<day>\d{1,2})?[ ]*,[ ]*)?(?P<year>18\d{2})[ ]*,?[ ]*")

BEAR_CREEK = "Bear Creek, Sangamon County, Illinois"

FOOTNOTES = {
    "5": 'They all (the last three couples) were married in the home of Hy Durbin in the '
         'presence of several witnesses, Bear Creek, Sangamon County, Illinois.',
    "6": 'The name of Esther Edge appears at another place in the records. It appears that '
         'she was baptized on the 18th of October, 1837, by Father O\'Meara, who certifies '
         'that she was the daughter of Samuel Edge, was seventeen years old and that her '
         'sponsors were Timothy O\'Meara and Bridget Eagan.',
}

# Footnote 5 hangs off the THIRD of the three, and qualifies all three. The article's
# closing prose (line 141) states the same, which is why this is not a guess about scope.
BEAR_CREEK_ENTRIES = (2, 3, 4)

UNNAMED_WITNESS = "Several Witnesses"

TITLES = {"mr", "mr.", "mrs", "mrs.", "miss", "dr", "dr.", "rev", "rev.",
          "col", "col.", "capt", "capt.", "maj", "maj."}

# --------------------------------------------------------------------------- #
# The death page. Eleven entries, and they are PROSE — there is no delimiter to
# parse, so the structure is hand-read here and the gate proves each `as_read` is
# still byte-for-byte the line it was read from. `line` is 1-based into the
# committed text.
#
# The ticket said "nine deaths and burials, June 1834 to July 1836". The page
# carries ELEVEN entries: eight in that window and three more of February and
# March 1837, which the assessment's window excluded rather than missed. All
# eleven are read; the three of 1837 are marked `beyond_ticket_window`.
# --------------------------------------------------------------------------- #
DEATHS = [
    dict(n=1, line=9, date="1834-06", precision="month",
         people=[("decedent", "one of the daughters of M. Colewell", None),
                 ("parent", "M. Colewell", "agent of the Indians")],
         note="No forename and no age for the child; the father is named with his office. "
              "The burial rite is stated for this entry by the line that closes the group."),
    dict(n=2, line=10, date="1834-07", precision="month",
         people=[("decedent", "W. Brannen", None)],
         note="\"Newly arrived from Ireland\" — the page's own words, and the only "
              "origin statement on the death page."),
    dict(n=3, line=11, date="1834-10", precision="month",
         people=[("decedent", "John Hogan", None)],
         note="Died suddenly. No age, no relation, no residence."),
    dict(n=4, line=12, date="1835-06", precision="month",
         people=[("decedent", "William Bourque (Burke)", None)],
         note="SCENE YEAR. The page itself gives the alias in brackets, so both spellings "
              "are the source's and neither is this project's normalisation."),
    dict(n=5, line=14, date="1835-07-02", precision="day",
         people=[("decedent", "John Baptist, son of Leon Bourrassa", None),
                 ("parent", "Leon Bourrassa", None)],
         note="SCENE YEAR, dated to the day. 28 days old at burial, so born about 4 June "
              "1835 — arithmetic, and stated as an inference rather than read."),
    dict(n=6, line=15, date="1835-07-17", precision="day",
         people=[("decedent", "Julian Andrews", None)],
         note="SCENE YEAR. 18 days old, so born about 29 June 1835 by the same arithmetic. "
              "No parent is named, which is unusual for an infant burial and is the page's "
              "silence, not an omission here."),
    dict(n=7, line=17, date="1835-10-15", precision="day",
         people=[("decedent", "Thomas Owen", "agent of the Indians")],
         note="SCENE YEAR, and the one entry on either page that reaches an attested "
              "resident. Died at Chicago 15 October 1835; buried on the 17th."),
    dict(n=8, line=18, date="1836-07-16", precision="day",
         people=[("decedent", "John . . .", None)],
         note="The surname is LOST on the page — printed as an ellipsis — and none is "
              "invented. Stabbed; buried on the 17th before a large crowd of Germans."),
    dict(n=9, line=19, date="1837-02-14", precision="day", beyond=True,
         people=[("decedent", "Ann Donovan", None)],
         note="Beyond the window the ticket named. The page's own dates are inconsistent: "
              "the burial is written 11 February and the death \"the 14th inst.\", which "
              "puts the burial before the death. Both are carried as printed."),
    dict(n=10, line=20, date="1837-02-24", precision="day", beyond=True,
         people=[("decedent", "Celestain Vilmain", None)],
         note="Beyond the window the ticket named. Five months old."),
    dict(n=11, line=21, date="1837-03-01", precision="day", beyond=True,
         people=[("decedent", "Jerome Beaubien", None)],
         note="Beyond the window the ticket named. Died 1 March 1837, aged 2; buried on "
              "the 2nd. A Beaubien child, and the Beaubiens are a family this "
              "reconstruction already holds — the identity is NOT joined here."),
]

# The line that closes the first group of four and states the rite for them.
GROUP_RITE_LINE = 13


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, doc) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fold(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def tokens(forenames: str):
    out = []
    for raw in re.split(r"\s+", (forenames or "").strip()):
        t = raw.strip()
        if not t or t.lower() in TITLES:
            continue
        letters = re.sub(r"[^A-Za-z]", "", t)
        if letters:
            out.append(letters.lower())
    return out


def agrees(a, b) -> bool:
    """Initial for initial, in whichever direction is shorter. `G. S.` and `George`
    agree on their first token and the rule says so; that is why an agreement here is
    a CANDIDATE and not a merge."""
    if not a or not b:
        return False
    if len(a) > len(b):
        a, b = b, a
    for x, y in zip(a, b):
        if len(x) == 1 or len(y) == 1:
            if x[0] != y[0]:
                return False
        elif x != y:
            return False
    return True


def split_person(name: str):
    """(surname, forenames, forename_printed). The page prints `_____ Quinn` where it
    has no forename, and that blank is kept rather than repaired."""
    n = name.strip()
    if re.match(r"^_+\s", n):
        return n.split(None, 1)[1].strip(), "", False
    parts = [p for p in n.split() if p]
    if len(parts) == 1:
        return parts[0], "", True
    return parts[-1], " ".join(parts[:-1]), True


def text_lines(root: Path, name: str):
    """The committed church copy, held byte-identical to the genealogytrails cache it
    was taken from. The cache is senior."""
    text = root / "data" / "research" / "church" / "text" / name
    cache = root / "data" / "research" / "genealogytrails" / "text" / (
        MARRIAGE_CACHE if name == MARRIAGE_TEXT else DEATH_CACHE)
    if not text.exists():
        sys.exit("the committed domain text is missing: %s"
                 % text.relative_to(root))
    if cache.exists() and text.read_bytes() != cache.read_bytes():
        sys.exit("data/research/church/text/%s is not byte-identical to the "
                 "genealogytrails cache it was taken from — the cache is senior" % name)
    return text.read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------------- the marriages

def parse_marriages(root: Path = ROOT):
    lines = text_lines(root, MARRIAGE_TEXT)
    entries = []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        m = DATE_RE.match(s)
        if not m:
            continue
        rest = s[m.end():]
        priest = None
        for p in PRIESTS:
            if rest.rstrip(" 0123456789").endswith(p):
                priest = p
                break
        if priest is None:
            continue

        tail = rest.rstrip()
        footnotes = []
        fm = re.search(r"\s+(\d)$", tail)
        if fm:
            footnotes.append(fm.group(1))
            tail = tail[:fm.start()]
        body = tail[:len(tail) - len(priest)].rstrip().rstrip(",").rstrip()

        others_present = False
        parties = []
        for chunk in body.split(","):
            q = chunk.strip().strip('"').strip()
            if not q:
                continue
            if q.lower() == "and others":
                others_present = True
                continue
            om = re.search(r'\s*"?and others"?$', q, re.I)
            if om:
                q = q[:om.start()].strip()
                others_present = True
            fm2 = re.search(r"\s+(\d)\s*$", q)
            if fm2:
                footnotes.append(fm2.group(1))
                q = q[:fm2.start()].strip()
            parties.append(q)

        if len(parties) < 2:
            sys.exit("line %d parses to fewer than two parties: %r" % (i, s))

        year = m.group("year")
        mon = (m.group("mon") or "").strip(".").lower()
        day = m.group("day")
        if mon and mon not in MONTHS:
            sys.exit("line %d names the month %r, which is not one of the twelve"
                     % (i, m.group("mon")))
        if mon and day:
            date, precision = "%s-%s-%02d" % (year, MONTHS[mon], int(day)), "day"
        elif mon:
            date, precision = "%s-%s" % (year, MONTHS[mon]), "month"
        else:
            date, precision = year, "year"

        entries.append({
            "n": len(entries) + 1,
            "line": i,
            "as_printed": s,
            "date": date,
            "date_precision": precision,
            "year": year,
            "groom": parties[0],
            "bride": parties[1],
            "witnesses": parties[2:],
            "priest": priest,
            "others_present": others_present,
            "footnotes": footnotes,
        })

    if len(entries) != EXPECTED_MARRIAGES:
        sys.exit("the marriage page parses to %d entries, not the %d the article's own "
                 "tally adds up to (22 + 18 + 87 + 1). The count is the only independent "
                 "check this reading has; it is not absorbed." % (len(entries), EXPECTED_MARRIAGES))

    by_priest, by_year = {}, {}
    for e in entries:
        by_priest[e["priest"]] = by_priest.get(e["priest"], 0) + 1
        by_year[e["year"]] = by_year.get(e["year"], 0) + 1
    if by_priest != EXPECTED_BY_PRIEST:
        sys.exit("the per-priest counts are %s, and the article prints %s — the page's "
                 "own arithmetic is what verifies this reading"
                 % (by_priest, EXPECTED_BY_PRIEST))
    if by_year != EXPECTED_BY_YEAR:
        sys.exit("the per-year counts are %s, not %s" % (by_year, EXPECTED_BY_YEAR))
    return entries


def marriage_records(entries):
    """One row per NAMED PERSON. `Several Witnesses` names nobody and makes no row;
    it is carried on the entry instead, so the reader can see that witnesses stood
    there and that the page did not name them."""
    records = []
    for e in entries:
        bear = e["n"] in BEAR_CREEK_ENTRIES
        place = BEAR_CREEK if bear else "Chicago"
        roles = [("groom", e["groom"]), ("bride", e["bride"])]
        for w in e["witnesses"]:
            roles.append(("witness", w))
        seq = 0
        for role, name in roles:
            if name == UNNAMED_WITNESS:
                continue
            seq += 1
            surname, forenames, printed = split_person(name)
            notes = [
                "%s of marriage %d of %d, %s, celebrated by %s."
                % (role.capitalize(), e["n"], EXPECTED_MARRIAGES,
                   e["as_printed"].split(",")[0] if e["date_precision"] == "year"
                   else e["date"], e["priest"]),
            ]
            if bear:
                notes.append(
                    "NOT CHICAGO. Footnote 5 on this page places the last three couples "
                    "of May 1834 at %s, in the home of Hy Durbin, and the article's "
                    "closing prose repeats it. This person is not evidence of anybody "
                    "standing in Chicago." % BEAR_CREEK)
            if not printed:
                notes.append(
                    "The page prints a blank where the forename should be (%r); the "
                    "surname alone is carried and no forename is invented, which makes "
                    "this row a refusal in any crosswalk by the domain's own rule." % name)
            if e["others_present"]:
                notes.append("The entry adds \"and others\" after the named witnesses: "
                             "more people stood there and the page does not name them.")
            for f in e["footnotes"]:
                notes.append("Footnote %s travels with this entry: “%s”"
                             % (f, FOOTNOTES[f]))
            if role == "witness" and name == e["groom"]:
                notes.append("The page names the groom again as his own witness. Carried "
                             "as printed; a transcription slip is likelier than the fact, "
                             "and neither is asserted here.")
            records.append({
                "id": "st_cyr_marriage_%03d_%d" % (e["n"], seq),
                "as_read": name,
                "normalized": ("%s %s" % (forenames, surname)).strip() if printed else surname,
                "locator": {"list": MARRIAGE_LIST, "line": e["line"],
                            "text_file": MARRIAGE_TEXT, "entry": e["n"], "role": role},
                "reading": "transcription_mediated",
                "confidence": "documented",
                "describes_date": e["date"],
                "cells": {
                    "role": role,
                    "date_as_printed": e["as_printed"].split(",")[0] if e["date_precision"] == "year"
                                       else None,
                    "date": e["date"],
                    "date_precision": e["date_precision"],
                    "groom": e["groom"],
                    "bride": e["bride"],
                    "witnesses": e["witnesses"],
                    "priest": e["priest"],
                    "place": place,
                },
                "at_chicago": not bear,
                "surname": surname,
                "forenames": forenames,
                "forename_printed": printed,
                "notes": " ".join(notes),
            })
    if len(records) != EXPECTED_READINGS:
        sys.exit("the marriage page yields %d named readings, not the %d this reading "
                 "was written against" % (len(records), EXPECTED_READINGS))
    bear = sum(1 for e in BEAR_CREEK_ENTRIES for _ in [0])
    if bear != EXPECTED_BEAR_CREEK_ENTRIES:
        sys.exit("the Bear Creek group is no longer three entries")
    return records


# ---------------------------------------------------------------- the deaths

def death_records(root: Path = ROOT):
    lines = text_lines(root, DEATH_TEXT)
    if len(DEATHS) != EXPECTED_DEATHS:
        sys.exit("the hand-read death table holds %d entries, not %d"
                 % (len(DEATHS), EXPECTED_DEATHS))
    rite = lines[GROUP_RITE_LINE - 1].strip()
    if not rite.startswith("All were buried"):
        sys.exit("line %d of the death page no longer closes the first group with the "
                 "burial rite — the qualifier this reading carries onto entries 1-4 has "
                 "moved" % GROUP_RITE_LINE)
    records = []
    for d in DEATHS:
        if d["line"] < 1 or d["line"] > len(lines):
            sys.exit("death entry %d names line %d, which the page does not have"
                     % (d["n"], d["line"]))
        printed = lines[d["line"] - 1].strip()
        seq = 0
        for role, name, office in d["people"]:
            seq += 1
            surname, forenames, has_forename = split_person(
                name.split(",")[0] if role == "decedent" and "," in name else name)
            notes = ["%s of death entry %d of %d on Father St. Cyr's death page, %s."
                     % (role.capitalize(), d["n"], EXPECTED_DEATHS, d["date"]),
                     d["note"]]
            if d["n"] <= 4:
                notes.append("Line %d closes this group of four: “%s” — the "
                             "rite is stated for the group and not for the entry, and it "
                             "travels with it here." % (GROUP_RITE_LINE, rite))
            if d.get("beyond"):
                notes.append("Outside the June 1834 - July 1836 window T-0573 named. Read "
                             "anyway: the page carries eleven entries, the ticket counted "
                             "the eight inside its window, and leaving three unread to "
                             "match a number would be the wrong repair.")
            records.append({
                "id": "st_cyr_death_%02d_%d" % (d["n"], seq),
                "as_read": name,
                "normalized": ("%s %s" % (forenames, surname)).strip() if has_forename else surname,
                "locator": {"list": DEATH_LIST, "line": d["line"],
                            "text_file": DEATH_TEXT, "entry": d["n"], "role": role},
                "reading": "transcription_mediated",
                "confidence": "documented",
                "describes_date": d["date"],
                "cells": {
                    "role": role,
                    "date": d["date"],
                    "date_precision": d["precision"],
                    "office": office,
                    "entry_as_printed": printed,
                    "priest": "J. M. I. St. Cyr",
                    "place": "Chicago",
                },
                "at_chicago": True,
                "beyond_ticket_window": bool(d.get("beyond")),
                "surname": surname,
                "forenames": forenames,
                "forename_printed": has_forename,
                "notes": " ".join(notes),
            })
    return records


# ---------------------------------------------------------------- the crosswalk

def resident_people(root: Path = ROOT):
    out = []
    d = root / "data" / "residents" / "households"
    if not d.exists():
        sys.exit("the resident households are missing (%s) — the crosswalk target is gone"
                 % d.relative_to(root))
    for path in sorted(d.glob("*.json")):
        doc = load(path)
        for p in doc.get("persons") or []:
            name = (p.get("name") or "").strip()
            if not name:
                continue
            surname, forenames, printed = split_person(name)
            out.append({
                "person_id": p.get("id"),
                "household_id": doc.get("id"),
                "name": name,
                "grade": p.get("grade"),
                "occupation": (p.get("occupation") or {}).get("value"),
                "surname_key": fold(surname),
                "forename_keys": tokens(forenames),
            })
    return out


def crosswalk(records, people):
    """EVERY named reading on both pages against every named person in the town, and a
    written outcome for each — the same shape the civic domain's pass takes, where 134
    enrollments produced 134 rulings and not only the ones that hit.

    A ruling is not a merge. Everything the surname-and-initials rule reaches is a
    CANDIDATE; a candidate is promoted to a merge only where a second attribute agrees
    too, and that happened once on 531 readings. `scene_year` marks the 26 readings of
    1835 that T-0573's acceptance names: those are the ones a bridge ticket may act on
    at all, and the other 500 are ruled on so that a later sweep can see they were
    looked at, not so that anything may be built on them."""
    by_surname = {}
    for p in people:
        by_surname.setdefault(p["surname_key"], []).append(p)

    entries = []
    for rec in records:
        scene = str(rec["describes_date"]).startswith("1835")
        out = {
            "record_id": rec["id"],
            "as_read": rec["as_read"],
            "normalized": rec["normalized"],
            "role": rec["cells"]["role"],
            "describes_date": rec["describes_date"],
            "scene_year": scene,
            "outcome": None,
            "residents": [],
            "rule": None,
        }
        if not rec["forename_printed"]:
            out["outcome"] = "no_forename"
            out["rule"] = ("The page prints %r with a blank where the forename stands. A "
                           "surname alone separates nobody in a town of families, so the "
                           "row is carried, counted and never matched." % rec["as_read"])
            entries.append(out)
            continue
        hits = by_surname.get(fold(rec["surname"]), [])
        agreeing = [p for p in hits if agrees(tokens(rec["forenames"]), p["forename_keys"])]
        if not hits:
            out["outcome"] = "unmatched"
            out["rule"] = ("No person in data/residents/ carries a surname folding to %r."
                           % fold(rec["surname"]))
        elif not agreeing:
            out["outcome"] = "refusal"
            out["residents"] = [{"person_id": p["person_id"], "name": p["name"],
                                 "grade": p["grade"]} for p in hits]
            out["rule"] = ("The surname folds equal but no forename agrees initial for "
                           "initial: %r against %s. A surname-only agreement is always a "
                           "refusal."
                           % (rec["as_read"], ", ".join(repr(p["name"]) for p in hits)))
        else:
            out["outcome"] = "candidate"
            out["residents"] = [{"person_id": p["person_id"], "name": p["name"],
                                 "grade": p["grade"], "occupation": p["occupation"]}
                                for p in agreeing]
            out["rule"] = ("Surname folds equal and the forenames agree initial for "
                           "initial: %r against %s. That is a candidate and not a merge; "
                           "a merge needs a second attribute to agree as well."
                           % (rec["as_read"], ", ".join(repr(p["name"]) for p in agreeing)))
        if not scene:
            out["rule"] += (" NOT THE SCENE YEAR: this reading is dated %s and under the "
                            "ladder ratified 2026-09-03 it may date and corroborate and "
                            "may never mint or promote, whatever it reaches."
                            % rec["describes_date"])
        entries.append(out)

    for claim in CLAIMS:
        entries.append({
            "claim_id": claim["id"],
            "as_read": claim["normalized"],
            "role": "claim",
            "describes_date": claim["describes_date"],
            "scene_year": str(claim["describes_date"]).startswith("1835"),
            "outcome": "ruled_no_town_change",
            "residents": [],
            "rule": CLAIM_RULINGS[claim["id"]],
        })
    return entries


# What each prose claim was ruled to mean for the town. A claim is adjudicated the same
# way a name is: something was read, and somebody said what it does and does not change.
CLAIM_RULINGS = {
    "st_cyr_c001": "Ruled: it REMOVES three entries from Chicago rather than adding "
                   "anything to it. The eight people of the Bear Creek marriages are "
                   "marked at_chicago: false on their own rows and no household, resident "
                   "or presence follows from them.",
    "st_cyr_c002": "Ruled: it gives a second spelling of one witness — the register's "
                   "Thomas Witkins and the article's Thomas Watkins — and both are kept. "
                   "The pair is refused against the town's attested John Watkins in "
                   "crosswalk.json. Nothing is added to Jeremiah Porter's record either: "
                   "the anecdote is about a boat, not about this town.",
    "st_cyr_c003": "Ruled: it BOUNDS the register rather than populating it. St. Cyr was "
                   "the only Catholic priest at Chicago through 1835, which is why every "
                   "scene-year entry is signed by him; it corroborates "
                   "data/sources/catholic_chicago_st_cyr_1833.json and changes no person.",
    "st_cyr_c004": "Ruled: it is the VERIFICATION of the reading and not evidence about "
                   "the town — 22 + 18 + 87 + 1 = 128, which --check reproduces from the "
                   "entries. It also measures what is still unread: 282 baptisms, which "
                   "are T-0503's object.",
    "st_cyr_c005": "Ruled: NOTHING FOLLOWS. Charles McDonnell married in 1836 and opened "
                   "his book store in 1845; neither date reaches 1835 and no business "
                   "record is created. Filed so the next sweep of this page does not have "
                   "to find it again.",
}


# --------------------------------------------------------------------------- #
# The adjudications. Everything above is mechanical; these are judgements, and
# they are written out here so they read back without the code. `crosswalk.json`
# is gated by tools/research_domains.py: a merge needs a rule naming BOTH
# spellings verbatim and evidence[], a surname-only merge is always refused, and
# a refusal is declared as explicitly as a merge.
# --------------------------------------------------------------------------- #
MERGES = [
    {
        "into": "Thomas Jefferson Vance Owen",
        "from": "Thomas Owen",
        "rule": "The death page reads \"Died at Chicago the 15th of October, 1835, Thomas "
                "Owen, agent of the Indians\". The project's resident record for Thomas "
                "Jefferson Vance Owen is graded attested, gives his occupation as the "
                "Indian agent, and already carries \"He died at Chicago on 15 October "
                "1835\" out of Andreas. Surname folds equal; the register's Thomas Owen "
                "is a prefix of Thomas Jefferson Vance Owen initial for initial; and TWO "
                "further attributes agree independently — the office (agent of the "
                "Indians / indian_agent) and the exact date of death (15 October 1835). "
                "Three agreements from two sources that did not copy each other is the "
                "bar this domain sets for a merge, and a common-name coincidence does not "
                "reach it: no second man was the Indian agent at Chicago dying on that "
                "day.",
        "evidence": [
            "data/research/church/records/st_cyr_deaths_1834_1837.json st_cyr_death_07_1",
            "data/residents/households/hh_owen_thomas_jv.json — persons[0] "
            "(owen_thomas_jv, attested, occupation indian_agent)",
            "data/residents/households/hh_owen_thomas_jv.json — present_on_scene_date, "
            "sourced andreas_1884_v1",
        ],
        "supersedes": "gt_001 in data/research/genealogytrails/claims/"
                      "town_findings_genealogytrails.json, which filed the reading and "
                      "explicitly declined the merge because no rule had been stated. "
                      "This is the rule, and this is the adjudication it waited for.",
        "does_not_follow": "NOTHING IN data/residents/ IS EDITED BY THIS. The register "
                           "corroborates a death Andreas already gave; it adds no "
                           "residence, no household member and no placement, and under "
                           "the ladder ratified 2026-09-03 a corroboration is not a "
                           "promotion.",
    },
]

REFUSALS = [
    {
        "a": "John Murphy",
        "b": "John Murphy",
        "rule": "The register's John Murphy married Bridget Rogers at Chicago on 26 April "
                "1835. The project holds an attested resident John Murphy, tavern-keeper, "
                "in charge of the house from August 1834 to 1836, whose household already "
                "carries a wife, Harriet Murphy. The two spellings are IDENTICAL and that "
                "is exactly why this is refused rather than merged: John Murphy is among "
                "the commonest names in a town taking a large Irish Catholic influx, the "
                "only agreement available is the name itself, and the merge would marry "
                "the town's tavern-keeper to a second woman in the middle of the scene "
                "year on no evidence at all. A name agreeing with itself is not a second "
                "attribute.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_006_1",
            "data/residents/households/hh_murphy_john.json — murphy_john (attested, "
            "tavern_keeper) and murphy_harriet (inferred)",
        ],
    },
    {
        "a": "G. S. Lee",
        "b": "George Lee",
        "rule": "G. S. Lee witnessed the marriage of John Latzky and Potily Morris on 1 "
                "October 1835. George Lee is a letter-list name, graded inferred. The "
                "surnames fold equal and the first initials agree, so the mechanical rule "
                "reaches it — and it stops there: the S of G. S. Lee is unaccounted for, "
                "the resident is a projection off a list of letters waiting at the post "
                "office rather than an attestation, and a first initial is one attribute, "
                "not two.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_009_3",
            "data/residents/households/hh_lee_george.json — lee_george (inferred)",
        ],
    },
    {
        "a": "Mark Bourassa",
        "b": "Leon Bourrassa",
        "rule": "THE TRAP T-0573 NAMED. Mark Bourassa married Josette Chevalier at Chicago "
                "in March 1835 on the marriage page; Leon Bourrassa buried a 28-day-old "
                "son on 2 July 1835 on the death page. They are not joined. The surnames "
                "do not even fold equal — bourassa against bourrassa, one r against two — "
                "and Mark and Leon are two different forenames rather than two spellings "
                "of one. That the two pages print the same family within four months is "
                "worth recording and is not evidence of one man; a French Chicago family "
                "of the 1830s had brothers.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_005_1",
            "data/research/church/records/st_cyr_deaths_1834_1837.json st_cyr_death_05_2",
        ],
    },
    {
        "a": "Josette Chevalier",
        "b": "Catherine Chevalier Robinson",
        "rule": "Josette Chevalier is the bride of March 1835. Catherine Chevalier "
                "Robinson is an attested resident whose Chevalier is a middle name, her "
                "surname on the record being Robinson. The forenames disagree outright, "
                "and a shared family name that is not even in the same position in the two "
                "readings is the weakest link this domain recognises. Refused.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_005_2",
            "data/residents/households/hh_robinson_alexander.json — robinson_catherine "
            "(attested)",
        ],
    },
    {
        "a": "Thomas Witkins",
        "b": "John Watkins",
        "rule": "Thomas Witkins witnessed the marriage of Patrick Carroll and Mary Hogan "
                "on 21 April 1835 — and the SAME PAGE's prose calls him Thomas Watkins, "
                "which is a reading this project should keep. The resident it would reach "
                "is John Watkins, the attested North Side schoolteacher. The forenames are "
                "different names. Refused, and the near-miss is recorded because the "
                "surnames are close enough that the mechanical rule never even offered the "
                "pair — witkins does not fold to watkins — and a later sweep would "
                "otherwise meet it fresh.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_007_3",
            "data/research/church/claims/st_cyr_register_prose.json st_cyr_c002",
            "data/residents/households/hh_watkins_john.json — watkins_john (attested, "
            "schoolteacher)",
        ],
    },
    {
        "a": "Mary Hogan",
        "b": "John S. C. Hogan",
        "rule": "Mary Hogan is the bride of 21 April 1835. John S. C. Hogan is an attested "
                "resident. The surname folds equal and nothing else does: a surname-only "
                "agreement is always a refusal here, and the register gives no relation "
                "between them to reason from.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_007_2",
            "data/residents/households/hh_hogan_john_s_c.json — hogan_john_s_c (attested)",
        ],
    },
    {
        "a": "Mary Green",
        "b": "Major John Greene",
        "rule": "Mary Green married Michael Nolan on 29 August 1835. Major John Greene is "
                "an attested resident. The surnames do not fold equal — green against "
                "greene — and the forenames are a woman's and a man's. Recorded because "
                "the pair looks like a spelling variant at a glance and is not one.",
        "evidence": [
            "data/research/church/records/st_cyr_marriages_1834_1839.json "
            "st_cyr_marriage_008_2",
            "data/residents/households/hh_greene_john.json — greene_john (attested)",
        ],
    },
    {
        "a": "Julian Andrews",
        "b": "Davi Andrews",
        "rule": "Julian Andrews was eighteen days old when he was buried on 17 July 1835. "
                "Davi Andrews is a letter-list resident, graded attested on the list and "
                "an adult by the nature of that list. The surname folds equal, the "
                "forenames do not agree, and an infant cannot be an adult; the pair is "
                "refused as an identity. That the child may have been of that household "
                "is a different claim and this register does not make it — no parent is "
                "named in the entry.",
        "evidence": [
            "data/research/church/records/st_cyr_deaths_1834_1837.json st_cyr_death_06_1",
            "data/residents/households/hh_andrews_davi.json — andrews_davi",
        ],
    },
]

CLAIMS = [
    {
        "id": "st_cyr_c001",
        "kind": "event",
        "reading": "transcription_mediated",
        "quote": '5 At this point on the marriage record appears the following: "They all '
                 '(the last three couples) were married in the home of Hy Durbin in the '
                 'presence of several witnesses, Bear Creek, Sangamon County, Illinois."',
        "normalized": "Three of the four 1834 marriages on this page — John Simmons to "
                      "Mary Durbin on 20 May and the two of 21 May — were performed at "
                      "Bear Creek, Sangamon County, on St. Cyr's return journey from St. "
                      "Louis, not at Chicago.",
        "locator": {"text_file": MARRIAGE_TEXT, "lines": [12, 12], "list": MARRIAGE_LIST},
        "describes_date": "1834-05",
        "entities": ["John Simmons", "Mary Durbin", "John Vincent", "Marion Simmons",
                     "Henry Simmons", "Cery Logdson", "Hy Durbin"],
        "town_finding": True,
        "notes": "The page is titled \"First Chicago Marriage Records\" and three of its "
                 "first four entries are not Chicago at all. Carried onto those three "
                 "rows themselves as place and at_chicago: false, because a caveat filed "
                 "somewhere else is a caveat nobody reads.",
    },
    {
        "id": "st_cyr_c002",
        "kind": "person",
        "reading": "transcription_mediated",
        "quote": "The marriage of Patrick Carroll and Mary Hogan, which occurred on April "
                 "21, 1835, was witnessed by Thomas Watkins and Patrick Meleney.",
        "normalized": "The article reads the witness the register spells Thomas Witkins as "
                      "Thomas Watkins, and identifies him with the Watkins of the "
                      "cholera-ice incident on a lake boat that Rev. Jeremiah Porter "
                      "publicly objected to in 1834.",
        "locator": {"text_file": MARRIAGE_TEXT, "lines": [149, 149], "list": MARRIAGE_LIST},
        "describes_date": "1835-04-21",
        "entities": ["Thomas Watkins", "Patrick Carroll", "Mary Hogan", "Patrick Meleney",
                     "Jeremiah Porter"],
        "town_finding": True,
        "notes": "TWO READINGS OF ONE MAN ON ONE PAGE. The entry prints Thomas Witkins; "
                 "this paragraph prints Thomas Watkins. The record keeps the entry's "
                 "spelling in as_read and this claim keeps the article's, and the pair is "
                 "refused against the project's attested John Watkins in crosswalk.json. "
                 "The cholera story is also the page's only description of Rev. Jeremiah "
                 "Porter, whom this reconstruction already holds.",
    },
    {
        "id": "st_cyr_c003",
        "kind": "person",
        "reading": "transcription_mediated",
        "quote": "As will be remembered, Father St. Cyr arrived in Chicago on May 5, 1833, "
                 "and left Chicago in the latter part of March, 1837. 10 Father Bernard "
                 "Schaeffer, the next to arrive, was here early in May, 1836, and died "
                 "here October 2, 1837. 11",
        "normalized": "Father J. M. I. St. Cyr was at Chicago from 5 May 1833 to late "
                      "March 1837; Father Bernard Schaeffer arrived early in May 1836 and "
                      "died at Chicago on 2 October 1837.",
        "locator": {"text_file": MARRIAGE_TEXT, "lines": [164, 164], "list": MARRIAGE_LIST},
        "describes_date": "1833-1837",
        "entities": ["J. M. I. St. Cyr", "Bernard Schaeffer"],
        "town_finding": True,
        "notes": "The bound that makes the register usable: St. Cyr was the only Catholic "
                 "priest at Chicago through the whole of 1835, which is why every one of "
                 "the six scene-year marriages and every scene-year burial is signed by "
                 "him and by nobody else. It also independently supports "
                 "data/sources/catholic_chicago_st_cyr_1833.json, which was until now the "
                 "only thing bounding his ministry here.",
    },
    {
        "id": "st_cyr_c004",
        "kind": "notice",
        "reading": "transcription_mediated",
        "quote": "Rev. John Mary Iranaeus St. Cyr, baptisms, 46; marriages, 22. Rev. "
                 "Bernard Schaeffer, baptisms, 31; marriages, 18. Rev. Timothy O'Meara, "
                 "baptisms, 195; marriages, 87.",
        "normalized": "The article's own tally of the first Chicago church register: St. "
                      "Cyr 46 baptisms and 22 marriages, Schaeffer 31 and 18, O'Meara 195 "
                      "and 87, with 6 baptisms and 1 marriage by John F. Plunkett and 4 "
                      "baptisms by Bishop Brute.",
        "locator": {"text_file": MARRIAGE_TEXT, "lines": [171, 171], "list": MARRIAGE_LIST},
        "describes_date": "1834-1839",
        "entities": ["J. M. I. St. Cyr", "Bernard Schaeffer", "Timothy O'Meara",
                     "John F. Plunkett", "Simon William Gabriel Brute"],
        "town_finding": False,
        "notes": "THIS IS THE CHECK, and it is why the reading can be trusted without the "
                 "book. 22 + 18 + 87 + 1 = 128, and the parse of the entries above returns "
                 "22, 18, 87 and 1 by priest, independently. It is also where T-0573's "
                 "\"87 marriages\" came from: 87 is O'Meara's subtotal, not the page. The "
                 "baptism counts are the measure of what is still unread — 282 baptisms "
                 "are tallied here and this page prints none of them, which is the size of "
                 "T-0503's object.",
    },
    {
        "id": "st_cyr_c005",
        "kind": "business",
        "reading": "transcription_mediated",
        "quote": "The next name on the record which is more or less familiar is that of "
                 "Charles McDonnell, who married Ann Charles on September 20, 1836. "
                 "McDonnell, so we are told in the writings of some of the earlier "
                 "residents, was the first book seller in Chicago, a devout and active "
                 "Catholic gentleman, and a worthy member of all the early Catholic "
                 "societies.",
        "locator": {"text_file": MARRIAGE_TEXT, "lines": [153, 153], "list": MARRIAGE_LIST},
        "normalized": "Charles McDonnell, married at Chicago 20 September 1836, is "
                      "described as the town's first book seller; Bishop Quarter's diary "
                      "dates his Catholic book store to March 1845.",
        "describes_date": "1836-09-20",
        "entities": ["Charles McDonnell", "Ann Charles", "William Quarter"],
        "town_finding": False,
        "notes": "LATER EVIDENCE, and filed as a business claim only so the next sweep does "
                 "not have to find it again. The marriage is 1836 and the book store is "
                 "1845; neither reaches 1835 and no business record is created. The "
                 "article's own footnote is what dates the store, and it contradicts the "
                 "loose \"first book seller in Chicago\" the sentence opens with.",
    },
]


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #

GT_CLAIMS = ("data/research/genealogytrails/claims/"
             "town_findings_genealogytrails.json")

SUPERSEDES = {
    "gt_001": "SUPERSEDED BY T-0573. The reading is now a record — "
              "data/research/church/records/st_cyr_deaths_1834_1837.json "
              "st_cyr_death_07_1 — and the identity this claim explicitly declined to "
              "settle is settled: data/research/church/crosswalk.json merges 'Thomas "
              "Owen' into the attested resident 'Thomas Jefferson Vance Owen' on the "
              "office and the date of death agreeing as well as the name. This claim is "
              "kept, not deleted: it is the record of what was known when it was filed.",
    "gt_002": "SUPERSEDED BY T-0573. The reading is now two records — "
              "data/research/church/records/st_cyr_deaths_1834_1837.json "
              "st_cyr_death_05_1 (the infant) and st_cyr_death_05_2 (Leon Bourrassa) — "
              "and the Bourassa/Bourrassa pair this claim deliberately left open is now "
              "an explicit REFUSAL in data/research/church/crosswalk.json rather than an "
              "absence. This claim is kept, not deleted: it is the record of what was "
              "known when it was filed.",
}


def records_doc(entries, records, list_id, title, date, text_file, doc, ladder):
    return {
        "schema": 1,
        "_doc": doc,
        "generated_by": "tools/read_st_cyr_register.py --build",
        "source_id": SOURCE_ID,
        "describes_date": date,
        "list": {"id": list_id, "title": title, "date": date,
                 "date_confidence": "documented", "entries": len(entries)},
        "the_ladder": ladder,
        "records": records,
    }


def build(root: Path = ROOT, write: bool = True):
    entries = parse_marriages(root)
    mrecs = marriage_records(entries)
    drecs = death_records(root)

    marriages = records_doc(
        entries, mrecs, MARRIAGE_LIST,
        "Father St. Cyr's Chicago marriage register, 1834-1839, as printed in the "
        "Illinois Catholic Historical Review vol. 4",
        "1834-1839", MARRIAGE_TEXT,
        "GENERATED by tools/read_st_cyr_register.py --build out of "
        "data/research/church/text/%s, which is byte-identical to the genealogytrails "
        "cache it was taken from. ONE ROW IS ONE NAMED PERSON, not one marriage: the "
        "domain README's rule is that names are people, so an entry naming a groom, a "
        "bride and two witnesses carries four readings. The marriages themselves are "
        "kept in `entries` below. The officiating priest is the recorder rather than a "
        "reading and is carried in every row's cells.priest. Hand-edit and --check says "
        "so." % MARRIAGE_TEXT,
        "118 of these 128 entries are 1836-1839 and are LATER EVIDENCE: they date and "
        "corroborate and they never mint an 1835 resident on their own. The six of 1835 "
        "are scene-year presence on a named day, which is the strongest thing this page "
        "holds; even they are crosswalked rather than promoted, and nothing under "
        "data/residents/ is edited by this reading.")
    marriages["counts"] = {
        "entries": len(entries),
        "named_readings": len(mrecs),
        "by_priest": {p: sum(1 for e in entries if e["priest"] == p) for p in PRIESTS},
        "by_year": {y: sum(1 for e in entries if e["year"] == y)
                    for y in sorted({e["year"] for e in entries})},
        "by_role": {r: sum(1 for x in mrecs if x["cells"]["role"] == r)
                    for r in ("groom", "bride", "witness")},
        "entries_not_at_chicago": len(BEAR_CREEK_ENTRIES),
        "readings_not_at_chicago": sum(1 for x in mrecs if not x["at_chicago"]),
        "entries_with_unnamed_witnesses": sum(
            1 for e in entries if UNNAMED_WITNESS in e["witnesses"]),
        "entries_adding_and_others": sum(1 for e in entries if e["others_present"]),
        "readings_with_no_forename_printed": sum(
            1 for x in mrecs if not x["forename_printed"]),
    }
    marriages["the_article_s_own_tally"] = (
        "The article prints its own count near the foot of the page: St. Cyr 22 "
        "marriages, Schaeffer 18, O'Meara 87, Plunkett 1. That is 128, and this parse "
        "returns 22, 18, 87 and 1 independently. --check fails if any of the four moves. "
        "T-0573's \"87 marriages\" was O'Meara's subtotal read as the page total.")
    marriages["entries"] = [
        {"n": e["n"], "line": e["line"], "date": e["date"],
         "date_precision": e["date_precision"], "as_printed": e["as_printed"],
         "groom": e["groom"], "bride": e["bride"],
         "witnesses_named": [w for w in e["witnesses"] if w != UNNAMED_WITNESS],
         "witnesses_unnamed": UNNAMED_WITNESS in e["witnesses"],
         "and_others": e["others_present"], "priest": e["priest"],
         "place": BEAR_CREEK if e["n"] in BEAR_CREEK_ENTRIES else "Chicago",
         "at_chicago": e["n"] not in BEAR_CREEK_ENTRIES,
         "footnotes": [{"marker": f, "text": FOOTNOTES[f]} for f in e["footnotes"]],
         "record_ids": [x["id"] for x in mrecs if x["locator"]["entry"] == e["n"]]}
        for e in entries]

    deaths = records_doc(
        DEATHS, drecs, DEATH_LIST,
        "Father St. Cyr's Chicago death and burial page, 1834-1837, as printed in the "
        "Illinois Catholic Historical Review vol. 4",
        "1834-1837", DEATH_TEXT,
        "GENERATED by tools/read_st_cyr_register.py --build. The death page is PROSE — "
        "eleven sentences with no delimiter — so its structure is hand-read in the DEATHS "
        "table of the tool and the gate proves every entry_as_printed is still byte-for-"
        "byte the line it was read from. One row is one named person: an entry naming a "
        "child and its father carries two readings. Hand-edit and --check says so.",
        "Four of the eleven entries fall in 1835 and are scene-year deaths at Chicago on "
        "named days. A death is not a residence and none is asserted; the one identity "
        "this page settles, Thomas Owen, is settled in crosswalk.json and changes no "
        "resident record.")
    deaths["counts"] = {
        "entries": len(DEATHS),
        "named_readings": len(drecs),
        "in_the_ticket_window_june_1834_to_july_1836": sum(
            1 for d in DEATHS if not d.get("beyond")),
        "beyond_the_ticket_window": sum(1 for d in DEATHS if d.get("beyond")),
        "scene_year_1835": sum(1 for d in DEATHS if d["date"].startswith("1835")),
        "by_role": {r: sum(1 for x in drecs if x["cells"]["role"] == r)
                    for r in ("decedent", "parent")},
    }
    deaths["the_count_the_ticket_carried"] = (
        "T-0573 said \"nine deaths and burials, June 1834 to July 1836\". The page carries "
        "ELEVEN entries: eight inside that window and three of February and March 1837 "
        "outside it. All eleven are read. Nine is not a count this page supports at any "
        "boundary, and the discrepancy is reported rather than made to fit.")
    deaths["entries"] = [
        {"n": d["n"], "line": d["line"], "date": d["date"],
         "date_precision": d["precision"],
         "beyond_ticket_window": bool(d.get("beyond")),
         "as_printed": text_lines(root, DEATH_TEXT)[d["line"] - 1].strip(),
         "people": [{"role": r, "as_read": n, "office": o} for r, n, o in d["people"]],
         "record_ids": [x["id"] for x in drecs if x["locator"]["entry"] == d["n"]]}
        for d in DEATHS]

    claims = {
        "schema": 1,
        "_doc": "HAND-AUTHORED, and rebuilt from the committed text by "
                "tools/read_st_cyr_register.py --check, which fails on one changed "
                "character. The marriage page is a LIST wrapped in an ARTICLE, and the "
                "article carries things the entries cannot: which marriages were not at "
                "Chicago, which witness the author read differently from the register, "
                "how long each priest was here, and the register's own totals. Those are "
                "claims, and they live here rather than in a record row.",
        "generated_by": "tools/read_st_cyr_register.py --build",
        "source_id": SOURCE_ID,
        "claims": CLAIMS,
    }

    people = resident_people(root)
    walk = crosswalk(mrecs + drecs, people)
    by_outcome = {}
    for x in walk:
        by_outcome[x["outcome"]] = by_outcome.get(x["outcome"], 0) + 1
    pass_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_st_cyr_register.py --build. The mechanical pass, "
                "kept whole so a later sweep can see what was looked at and not only what "
                "was concluded. EVERY named reading on both pages and every prose claim "
                "carries a ruling here, against the named persons of data/residents/ — "
                "526 names, 5 claims — and `scene_year` marks the 26 of 1835 that a "
                "bridge ticket may act on at all. An `unmatched` row is a person no "
                "resident record carries a surname for and is the ordinary case; a "
                "`refusal` is a surname that folds equal with no forename that agrees; a "
                "`candidate` is what the rule reaches, and a candidate is not a merge. "
                "The adjudications are in crosswalk.json.",
        "generated_by": "tools/read_st_cyr_register.py --build",
        # T-0598: every ruling in this file rests on the register, stated once here
        # rather than on each of 531 rows. Without it a ruling that reaches a town
        # person names no source and cannot be carried to that person's card.
        "source_id": SOURCE_ID,
        "pass": TICKET,
        "target": "data/residents/households/*.json — every named person, at every grade",
        "targets_examined": len(people),
        "rule": "Surnames must fold equal after case and punctuation are dropped, AND the "
                "forenames must agree initial for initial in one direction or the other. "
                "A surname-only agreement is always a refusal. A row the page prints "
                "without a forename is reported no_forename, carried and never matched.",
        "counts": by_outcome,
        "merges_proposed": len(MERGES),
        "why_so_few": "One merge on 531 rulings. The town's resident file is mostly "
                      "letter-list projections of Anglo-American men; the register's "
                      "people are Irish, French and German Catholics, who are exactly the "
                      "part of this town the resident file is thinnest on — so a low reach "
                      "is the honest result and not a failure of the rule. And 500 of the "
                      "531 are dated 1836-1839, where the ladder forbids a merge from "
                      "changing anything even when the names agree.",
        "entries": walk,
    }

    identity = load(root / "data/research/church/crosswalk.json")
    identity["passes"] = [p for p in identity.get("passes") or []
                          if p.get("pass") != TICKET] + [{
        "pass": TICKET,
        "what": "The scene-year entries of Father St. Cyr's marriage and death pages "
                "against data/residents/.",
        "readings_examined": len(walk),
        "residents_examined": len(people),
        "merges": len(MERGES),
        "refusals": len(REFUSALS),
        "detail": "data/research/church/st_cyr_crosswalk.json",
    }]
    identity["merges"] = [m for m in identity.get("merges") or []
                          if m.get("pass") != TICKET] + [
        {**m, "pass": TICKET} for m in MERGES]
    identity["refusals"] = [r for r in identity.get("refusals") or []
                            if r.get("pass") != TICKET] + [
        {**r, "pass": TICKET} for r in REFUSALS]

    coverage = load(root / "data/research/church/coverage.json")
    coverage["declarations"] = [d for d in coverage.get("declarations") or []
                                if d.get("ticket") != TICKET] + [{
        "unit": "list",
        "ticket": TICKET,
        "items": [MARRIAGE_LIST, DEATH_LIST],
        "counts": {MARRIAGE_LIST: len(mrecs), DEATH_LIST: len(drecs)},
        "what_was_read": "Both pages of genealogytrails.com/ill/cook printing Father St. "
                         "Cyr's register out of the Illinois Catholic Historical Review "
                         "vol. 4: the marriage register (128 entries, 513 named readings) "
                         "and the death and burial page (11 entries, 13 named readings), "
                         "in full, including the article's prose and every footnote.",
        "what_was_not_read": "THE BAPTISMS. The same article tallies 282 baptisms by the "
                             "same three priests and this page prints none of them. They "
                             "are NOT undeclared any more: T-0503 read them off the "
                             "register's own eleven page images and declared all eleven "
                             "under its own ticket in this file. What this page did not "
                             "carry, the scans did.",
    }]

    gt = load(root / GT_CLAIMS)
    for claim in gt.get("claims") or []:
        if claim.get("id") in SUPERSEDES:
            claim["superseded_by"] = SUPERSEDES[claim["id"]]

    out = {
        "data/research/church/records/%s.json" % MARRIAGE_LIST: marriages,
        "data/research/church/records/%s.json" % DEATH_LIST: deaths,
        "data/research/church/claims/st_cyr_register_prose.json": claims,
        "data/research/church/st_cyr_crosswalk.json": pass_doc,
        "data/research/church/crosswalk.json": identity,
        "data/research/church/coverage.json": coverage,
        GT_CLAIMS: gt,
    }
    if write:
        for rel, doc in out.items():
            dump(root / rel, doc)
        print("st cyr register: %d marriage entries / %d named readings, %d death "
              "entries / %d named readings, %d merge(s), %d refusal(s)"
              % (len(entries), len(mrecs), len(DEATHS), len(drecs),
                 len(MERGES), len(REFUSALS)))
    return out


def rebuild_quote(root: Path, locator: dict):
    path = root / "data/research/church/text" / locator["text_file"]
    lines = path.read_text(encoding="utf-8").splitlines()
    first, last = locator["lines"]
    if first < 1 or last < first or last > len(lines):
        return None
    return "\n".join(lines[first - 1:last])


def check(root: Path = ROOT) -> list:
    bad = []
    try:
        want = build(root, write=False)
    except SystemExit as exc:
        return [str(exc)]
    for rel, doc in want.items():
        p = root / rel
        if not p.exists():
            bad.append("%s is missing — run tools/read_st_cyr_register.py --build" % rel)
        elif load(p) != doc:
            bad.append("%s is stale or hand-edited; regenerate it with "
                       "tools/read_st_cyr_register.py --build" % rel)

    # Every claim's quote, rebuilt out of the committed text. A tidied quote is
    # invisible to every other check here.
    for claim in CLAIMS:
        got = rebuild_quote(root, claim["locator"])
        if got is None:
            bad.append("claim %s names lines the page does not have" % claim["id"])
        elif re.sub(r"\s+", " ", claim["quote"]).strip() not in re.sub(r"\s+", " ", got):
            bad.append("claim %s does not quote the committed text verbatim at its "
                       "locator" % claim["id"])

    # The two findings T-0556 filed in passing must say they were superseded, and say
    # where. A duplicate reading nobody marked is how one page comes to be read twice.
    gt_path = root / GT_CLAIMS
    if not gt_path.exists():
        bad.append("%s is missing — the two findings this ticket supersedes live there"
                   % GT_CLAIMS)
    else:
        seen = {c.get("id"): c for c in load(gt_path).get("claims") or []}
        for cid in SUPERSEDES:
            if cid not in seen:
                bad.append("%s no longer carries %s, which this reading supersedes"
                           % (GT_CLAIMS, cid))
            elif not (seen[cid].get("superseded_by") or "").startswith("SUPERSEDED BY " + TICKET):
                bad.append("%s is not marked superseded by %s — a superseded finding "
                           "nobody marked gets read again" % (cid, TICKET))
    return bad


def _self_test() -> int:
    """Break each assertion in a copy of the tree and prove the gate says so."""
    def run(mutate, expect, label):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "4d"
            (work / "data" / "research").mkdir(parents=True)
            shutil.copytree(CHURCH, work / "data" / "research" / "church")
            shutil.copytree(ROOT / "data/research/genealogytrails",
                            work / "data" / "research" / "genealogytrails")
            shutil.copytree(RESIDENTS, work / "data" / "residents" / "households")
            mutate(work)
            try:
                bad = check(work)
            except SystemExit as exc:
                bad = [str(exc)]
            hit = [b for b in bad if expect in b]
            print(("  ok   " if hit else "  MISS ") + label)
            return bool(hit)

    def edit_json(rel, fn):
        def go(work):
            p = work / rel
            doc = json.loads(p.read_text(encoding="utf-8"))
            fn(doc)
            p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
        return go

    def edit_text(rel, fn):
        def go(work):
            p = work / rel
            p.write_text(fn(p.read_text(encoding="utf-8")), encoding="utf-8")
        return go

    print("self-test — every assertion, broken on purpose:")
    ok = []
    ok.append(run(edit_text("data/research/church/text/" + MARRIAGE_TEXT,
                            lambda t: t.replace("Mark Bourassa", "Marc Bourassa")),
                  "not byte-identical", "the committed text edited away from the cache"))
    ok.append(run(edit_json("data/research/church/records/%s.json" % MARRIAGE_LIST,
                            lambda d: d["records"].pop(0)),
                  "stale or hand-edited", "a marriage reading deleted by hand"))
    ok.append(run(edit_json("data/research/church/records/%s.json" % DEATH_LIST,
                            lambda d: d["records"][6].update(at_chicago=False)),
                  "stale or hand-edited", "a death row's place changed by hand"))
    ok.append(run(edit_json("data/research/church/crosswalk.json",
                            lambda d: d.update(merges=[])),
                  "stale or hand-edited", "the Owen merge removed by hand"))
    ok.append(run(edit_json("data/research/church/coverage.json",
                            lambda d: d.update(declarations=[])),
                  "stale or hand-edited", "the coverage declaration removed"))
    ok.append(run(edit_json(GT_CLAIMS,
                            lambda d: [c.pop("superseded_by", None)
                                       for c in d["claims"]]),
                  "not marked superseded", "gt_001/gt_002 left unmarked"))

    # The two structural assertions that stop the parse rather than returning a fault.
    ok.append(run(_both_texts(lambda t: t.replace(
                      "Oct. 27, 1835, Lawrence Smith, Mary Welsh, _____ O'Meara, "
                      "T. Welsh, J. M. I. Saint Cyr\n", "")),
                  "the article's own tally", "an entry dropped from both copies"))
    ok.append(run(_both_death_texts(lambda t: t.replace(
                      "All were buried according", "Some were buried according")),
                  "no longer closes the first group",
                  "the death page's group rite line moved"))

    print("%d of %d assertions fired" % (sum(ok), len(ok)))
    return 0 if all(ok) else 1


def _both_texts(fn):
    """Edit the church copy AND the genealogytrails cache together, so the byte-identity
    assertion stays satisfied and the assertion under test is the one that fires."""
    def go(work):
        for rel in ("data/research/church/text/" + MARRIAGE_TEXT,
                    "data/research/genealogytrails/text/" + MARRIAGE_CACHE):
            p = work / rel
            p.write_text(fn(p.read_text(encoding="utf-8")), encoding="utf-8")
    return go


def _both_death_texts(fn):
    def go(work):
        for rel in ("data/research/church/text/" + DEATH_TEXT,
                    "data/research/genealogytrails/text/" + DEATH_CACHE):
            p = work / rel
            p.write_text(fn(p.read_text(encoding="utf-8")), encoding="utf-8")
    return go


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    if args.build:
        build()
        return 0
    if args.check:
        bad = check()
        for b in bad:
            print("  FAIL  " + b)
        if not bad:
            print("  st cyr register: %d marriages (22 + 18 + 87 + 1, the article's own "
                  "tally), %d deaths, quotes verbatim, %d merge and %d refusals adjudicated"
                  % (EXPECTED_MARRIAGES, EXPECTED_DEATHS, len(MERGES), len(REFUSALS)))
        return 1 if bad else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
