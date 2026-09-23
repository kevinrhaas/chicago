#!/usr/bin/env python3
"""Fergus's death notices of Chicago's Old Settlers, read entry by entry (T-0574).

    tools/read_fergus_obits.py --build       write the text copy, the records and the crosswalk
    tools/read_fergus_obits.py --check       the gate
    tools/read_fergus_obits.py --self-test   the gate's assertions still fire when broken

THE SOURCE. One web page — `earlysettlerobits.txt` in this repository's Genealogy Trails
cache — carrying K. Torp's 2007 transcription of the OBITUARY printed in Robert Fergus's
*Directory of the City of Chicago, Illinois, for 1843* (Fergus Printing Company, 1896).
Twenty-three letter sections, and under them entries of the shape

    Allen, Col. James, U. S. Army, died, Fort Leavenworth, Kansas, August 23, 1846, aged 40.

— a surname, a title and forenames, often a trade, a manner of death, a place, a date and
an age. Lt. James Allen is the first name on the 1833 Chicago tax list.

WHY IT IS WORTH A RUN: AN AGE AT DEATH IS A BIRTH YEAR, and the residents layer is shorter
of birth years than it is of names. Nothing else this project has read dates its people
this way.

THE TRAP, STATED BEFORE THE WORK AND CARRIED ONTO EVERY RECORD. The list's own header says
it names "some of Chicago's Old Settlers, prior to 1843, and other well-known citizens who
arrived after 1843, together with others prominently connected with Illinois history".
So PRESENCE IN THIS LIST ESTABLISHES NOTHING ABOUT ARRIVAL — not before 1843, and certainly
not residence on 1 July 1835. Gov. Richard Yates, Henry Ward Beecher and Morris Birkbeck of
Edwards County are all in it. Every record carries `places_in_1835: false` and the header's
admission verbatim, and the crosswalk repeats it at the top of the file, because a later
reader meeting a matched name is exactly the reader who will forget it.

THE SEGMENTING RULE, because the transcription wraps a long entry and does not indent the
turn. An entry begins where a line begins with a SURNAME IN THE CURRENT LETTER SECTION:
the leading word is capitalised, has two letters or more, starts with the section's letter,
is not a month, and is followed either by a comma or by another capitalised word. Every
other line is the turn of the entry above. The rule has to be that particular because the
turned lines start with capitals too — "Aug. 1, 1860, aged 55-7-11." turns Ellen Kinzie's
entry under K, and "Oct. 12, 1877, a. 55-1-11." turns Daniel O'Hara's under O, where the
section letter alone would have made a new man of the month. And it may not simply require
a comma, because the printer or the transcriber drops it five times — "Kimberly Col. John
Ellis", "Kirk James Smith", "Scott. Maj. Martin", "Sweet Richard M." are entries.

THE ARITHMETIC IS THIS PROJECT'S, NOT THE PAGE'S. The page prints a date and an age; the
birth window is subtraction, and it is `inferred` with the subtraction written out on every
record. An age of "40" means at least forty completed years and less than forty-one, which
is a window of a year and gives two candidate birth years; "82-2-15" is exact to the day;
"89½" and "24 2/3" are read as months, which the volume's own "a. 48-6" spells out. Where
the age is printed truncated ("aged 5-.") or hedged ("aged about 50"), or the death carries
no year, NO birth year is derived and the record says which of those it was.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/research/genealogytrails/text/earlysettlerobits.txt"
DOMAIN = ROOT / "data/research/old_settlers"
TEXT = DOMAIN / "text/fergus_1843_old_settler_death_notices.txt"
RECORDS = DOMAIN / "death_notices.json"
CROSSWALK = DOMAIN / "death_notices_crosswalk_1835.json"
COVERAGE = DOMAIN / "coverage.json"
PEOPLE = DOMAIN / "people.json"
HH = ROOT / "data/residents/households"
SOURCE_ID = "fergus_1843_old_settler_death_notices"

SCHEMA = 1

# The transcriber's furniture and the page's own front matter. Lines 1-13 are the banner,
# the header, the source note and the A-Z navigation; the last three are the compiler's
# name and the transcriber's footer. coverage.json declares every one of them.
BODY_FROM, BODY_TO = 14, 813

HEADER_ADMISSION = (
    "Names, places * , dates, and ages at death\n"
    "of some of Chicago's Old Settlers, prior to 1843, and other well - known citizens "
    "who arrived after 1843, together\nwith others prominently connected with Illinois "
    "history:"
)
PLACE_DEFAULT = ("* In most cases, except as otherwise stated, the deaths occurred in "
                 "Chicago.")

SECTION = re.compile(r"^-?([A-Z])-?\s+SURNAMES$")
PARTICLE = r"(?:de|del|di|dos|du|la|le|van|von|der|den)"
# A surname may carry a particle — "Van de Velde, Rt.-Rev. Jas. Oliver" opens an entry
# under V, and a rule that stopped at the first word read "Van" and then refused the head
# because "de" is lower case, which silently folded the bishop into the entry above him.
HEAD = re.compile(
    r"^(?P<sn>[A-Z][A-Za-z'’\-]+(?:\s+%s\s+[A-Z][A-Za-z'’\-]+)*)"
    r"(?P<paren>\s*\([^)]*\))?(?P<sep>[,.]?)\s+(?P<rest>.*)$" % PARTICLE)

MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
          "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
          "December": 12, "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "Jun": 6, "Jul": 7,
          "Aug": 8, "Sept": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))

# The manners of death the page prints, longest first so "lost at sea" beats "lost" and
# "found frozen" is one phrase. `d.` is Fergus's own abbreviation and is only itself when
# it stands as a word with its stop — "D." is an initial and must not match.
MANNER = re.compile(
    r"(?<![A-Za-z])(lost at sea|found frozen|assassinated|massacred|suicided|suicide|"
    r"executed|drowned|murdered|perished|killed|burned|died|clied|hung|shot|lost|d\.)"
    r"(?![A-Za-z])")
# "clied" is the transcription's slip for "died" (Wm. Lockyer Loveday). It is read as a
# death and the slip is recorded on the record rather than corrected in the quote.
MANNER_SLIPS = {"clied": "the transcription prints 'clied'; it is 'died' misread, and the "
                         "quote is left as the page has it"}

# The age, as the volume prints it: "aged 72", "a. 89 1/2", "aged 82-2-15", "a, 79-11-16",
# "a 52", "aged about 50", and the two the transcription truncates, "aged 5-".
AGE = re.compile(
    r"\b(?:aged|age|a)[\.,]?\s*"
    r"(?P<val>(?:about\s+)?\d+(?:\s*[-–]\s*\d*){0,2}(?:\s*\d\s*/\s*\d)?"
    r"(?:\s*[½¾⅓⅔¼])?)")
FRACTION_MONTHS = {"½": 6, "¾": 9, "⅓": 4, "⅔": 8, "¼": 3,
                   "1/2": 6, "3/4": 9, "1/3": 4, "2/3": 8, "1/4": 3}

BORN = re.compile(
    r"\bborn\b(?P<where>[^;]*?)(?P<mon>%s)\.?\s+(?P<d>\d{1,2}),?\s*(?P<y>1[5-9]\d\d)"
    % "|".join(sorted({"January", "February", "March", "April", "May", "June", "July",
                       "August", "September", "October", "November", "December", "Jan",
                       "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sept", "Sep", "Oct",
                       "Nov", "Dec"}, key=len, reverse=True)))

# The earliest death the volume means to print is Marquette's, 1675. A year before that
# is a transcription slip, and there is one: "Seipp, Conrad, brewer, died January 28, 1590"
# for 1890. The quote is left as the page has it and the slip is named on the record; no
# birth window is derived from a year that cannot be right.
EARLIEST_PLAUSIBLE_DEATH = 1675

DATE_QUALIFIER = re.compile(r"\b(before|after|about|circa)\s*$", re.I)
TITLES = {"mrs", "miss", "mr", "dr", "capt", "col", "rev", "gen", "maj", "hon", "judge",
          "lieut", "lieu", "sergt", "sen", "senator", "gov", "dea", "prof", "maj.-gen",
          "rt.-rev", "rt", "st", "jr", "sr", "jun", "ex-gov"}

# ELEVEN HEADS CARRY NO COMMA after the surname, and for five of them the split the
# segmenter makes is not the split a reader wants. The note is written onto the record
# rather than the name quietly corrected: the quote is the page's, and the reading beside
# it says where the page and this project's grammar part company.
NAME_NOTES = {
    "Little Turtle": "The Miami war leader, and the list prints no surname for him. The "
                     "segmenter reads 'Little' as the surname and 'Turtle' as the given "
                     "name; both are halves of one name and neither is a surname.",
    "Saint Cyr": "Father John Mary Irenaeus St. Cyr, the first resident Catholic priest at "
                 "Chicago, whose register T-0573 reads. The volume prints 'Saint Cyr' "
                 "without a comma, so the segmenter reads 'Saint' as the surname; the "
                 "surname is 'St. Cyr'.",
    "Sears. Jr.": "The suffix is printed before the forename — 'Sears. Jr., John' — so the "
                  "given name reads 'Jr., John'.",
    "Shirup. M.": "No forename is printed, only the initial M., and the stop after the "
                  "surname is the printer's or the transcriber's.",
    "Jones (Bromfield) John": "The parenthesis follows the surname and carries an alternate "
                              "name; it is read as `surname_alternate`.",
}

# The transcriber's and the printer's standing confusions, folded out of a surname before
# it is compared. Identical to tools/crosswalk_fergus_1843.py's list on purpose: the two
# readings are of the same volume by the same transcriber, and a fold that differed between
# them would make the two crosswalks disagree for a reason that is about this project.
FOLD = [(r"[^a-z]", ""), (r"^mc", "mac"), (r"^m$", ""), (r"ii", "n"), (r"rn", "m"),
        (r"vv", "w"), (r"1", "l"), (r"0", "o")]


# ---------------------------------------------------------------- small helpers

def fold(name: str) -> str:
    s = (name or "").lower()
    for pat, rep in FOLD:
        s = re.sub(pat, rep, s)
    return s


def initial(given: str) -> str:
    for tok in (given or "").split():
        bare = tok.strip(".,'\"()").lower()
        if bare in TITLES or not bare:
            continue
        for ch in tok:
            if ch.isalpha():
                return ch.lower()
    return ""


def minus_ymd(d: date, y: int, m: int, days: int) -> date:
    """Subtract y years, then m months, then `days` days — in that order, which is how a
    printed age reads: the years are counted first."""
    month = d.month - m
    year = d.year - y
    while month <= 0:
        month += 12
        year -= 1
    day = min(d.day, [31, 29 if (year % 4 == 0 and (year % 100 or year % 400 == 0)) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day) - timedelta(days=days)


def last_day(year: int, month: int) -> int:
    return [31, 29 if (year % 4 == 0 and (year % 100 or year % 400 == 0)) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


# ---------------------------------------------------------------- segmenting

def read_lines():
    return CACHE.read_text(encoding="utf-8").splitlines()


def segment(lines):
    """The entries, each as (letter, first_line, last_line, joined_text)."""
    section, entries = None, []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        m = SECTION.match(s)
        if m:
            section = m.group(1)
            continue
        if i < BODY_FROM or i > BODY_TO or not s:
            continue
        h = HEAD.match(s)
        head = False
        if h and section and h.group("sn")[0] == section and h.group("sn") not in MONTHS:
            rest = h.group("rest")
            head = h.group("sep") == "," or bool(rest and rest[0].isupper())
        if head:
            entries.append([section, i, i, s])
        elif entries:
            entries[-1][2] = i
            entries[-1][3] += " " + s
        else:                                            # pragma: no cover - guarded
            raise AssertionError("line %d precedes every entry: %r" % (i, s))
    return entries


# ---------------------------------------------------------------- parsing one entry

def parse_age(text, from_pos):
    """The age as printed and as arithmetic. Searched from `from_pos` — the age follows the
    date in this list, and searching from the front finds house numbers instead."""
    m = None
    for cand in AGE.finditer(text):
        if cand.start() >= from_pos:
            m = cand
            break
    if m is None:
        for cand in AGE.finditer(text):
            m = cand
            break
    if m is None:
        return None
    printed = text[m.start():m.end()].strip().rstrip(".,;")
    val = re.sub(r"\s+", " ", m.group("val")).strip()
    out = {"as_printed": printed, "years": None, "months": None, "days": None,
           "precision": None, "approximate": False, "unreadable": False, "why": None}
    if val.lower().startswith("about"):
        out["approximate"] = True
        val = val.split(None, 1)[1]
    frac = None
    for token, months in FRACTION_MONTHS.items():
        if val.endswith(token):
            frac = months
            val = val[: -len(token)].strip()
            break
    if frac is None:
        fm = re.search(r"(\d)\s*/\s*(\d)$", val)
        if fm:
            frac = FRACTION_MONTHS.get("%s/%s" % (fm.group(1), fm.group(2)))
            val = val[: fm.start()].strip()
    parts = [p.strip() for p in re.split(r"[-–]", val)]
    if any(p == "" for p in parts):
        out["unreadable"] = True
        out["why"] = ("the transcription prints the age truncated (%r), so the number of "
                      "years is not on the page" % printed)
        return out
    nums = [int(p) for p in parts if p.isdigit()]
    if not nums:
        out["unreadable"] = True
        out["why"] = "no number could be read out of %r" % printed
        return out
    out["years"] = nums[0]
    if len(nums) > 1:
        out["months"] = nums[1]
    if len(nums) > 2:
        out["days"] = nums[2]
    if frac is not None:
        if out["months"] is None:
            out["months"] = frac
        # A printed "48-6½" does not occur; if it ever does the fraction is dropped rather
        # than guessed at, and the record says so.
        elif out["months"] != frac:
            out["why"] = ("the entry prints both months and a fraction; the months are "
                          "used and the fraction is not guessed at")
    out["precision"] = ("years_months_days" if out["days"] is not None
                        else "years_months" if out["months"] is not None else "years")
    if out["approximate"]:
        out["why"] = "the page hedges the age with 'about', so no window is derived from it"
    return out


def parse_death(text):
    """Manner, place, date, and where in the string the date ends."""
    out = {"manner_as_read": None, "manner_note": None, "place_as_read": None,
           "date_as_read": None,
           "date": None, "date_precision": None, "date_qualifier": None,
           "day_not_read_why": None, "date_end": 0}
    mm = MANNER.search(text)
    tail_from = mm.end() if mm else 0
    if mm:
        out["manner_as_read"] = mm.group(1)
        out["manner_note"] = MANNER_SLIPS.get(mm.group(1).lower())
    tail = text[tail_from:]
    dm = (re.search(r"(?P<mon>%s)\.?\s+(?P<d>\d{1,2})[\s,]+(?P<y>1[5-9]\d\d)" % MONTH_RE, tail)
          or re.search(r"(?P<mon>%s)\.?\s*,?\s*(?P<y>1[5-9]\d\d)" % MONTH_RE, tail)
          or re.search(r"(?<![\d\-])(?P<y>1[5-9]\d\d)(?![\d\-])", tail))
    if dm:
        gd = dm.groupdict()
        out["date_as_read"] = tail[dm.start():dm.end()]
        out["date_end"] = tail_from + dm.end()
        year = int(gd["y"])
        if gd.get("mon") and gd.get("d") and int(gd["d"]) >= 1 and \
                int(gd["d"]) <= last_day(year, MONTHS[gd["mon"]]):
            out["date"] = "%04d-%02d-%02d" % (year, MONTHS[gd["mon"]], int(gd["d"]))
            out["date_precision"] = "day"
        elif gd.get("mon") and gd.get("d"):
            # The transcription prints a day the month does not have — "Sept. 80, 1890" for
            # Morgan L. Keith. The day is not guessed at: the date drops to the month it can
            # be read at, and the record says why rather than silently gaining a 30th.
            out["date"] = "%04d-%02d" % (year, MONTHS[gd["mon"]])
            out["date_precision"] = "month"
            out["day_not_read_why"] = (
                "the transcription prints %r, and %s has no such day; the day is not "
                "guessed at and the date is read at the month"
                % (out["date_as_read"], gd["mon"]))
        elif gd.get("mon"):
            out["date"] = "%04d-%02d" % (year, MONTHS[gd["mon"]])
            out["date_precision"] = "month"
        else:
            out["date"] = "%04d" % year
            out["date_precision"] = "year"
        before = tail[: dm.start()]
        q = DATE_QUALIFIER.search(before.rstrip(" ,"))
        if q:
            out["date_qualifier"] = q.group(1).lower()
        place = before.strip(" ,;").lstrip(".").strip()
        place = re.sub(r"\b(before|after|about|circa)\s*$", "", place,
                       flags=re.I).strip(" ,;").lstrip(".").strip()
        out["place_as_read"] = place or None
    else:
        out["date_end"] = tail_from
        # A place is only a place when a manner of death introduced it. With no verb the
        # tail is the whole entry, and "Sweet Richard M." is a name, not a town.
        place = tail.strip(" ,;").lstrip(".").strip() if mm else ""
        out["place_as_read"] = place or None
    return out


def parse_born(text, death_start):
    """The page prints a date of birth for four of its people — "born Ayr, Scotland, Sept. 1,
    1822" — and where it does, the birth is DOCUMENTED and the arithmetic becomes a check on
    it rather than the only evidence. Only a `born` standing before the death clause counts:
    a date after it belongs to something else the entry goes on to say."""
    for m in BORN.finditer(text):
        if death_start and m.start() > death_start:
            continue
        try:
            when = date(int(m.group("y")), MONTHS[m.group("mon")], int(m.group("d")))
        except (KeyError, ValueError):
            continue
        return {"as_printed": text[m.start():m.end()],
                "date": when.isoformat(),
                "place_as_read": (m.group("where") or "").strip(" ,.;") or None,
                "confidence": "documented",
                "note": "the entry prints the birth; it is not derived"}
    return None


def derive_birth(dth, age):
    """The window the printed death and the printed age put the birth in, with the
    subtraction written out. `inferred`, always — the page states neither."""
    out = {"confidence": "inferred", "earliest": None, "latest": None,
           "earliest_date": None, "latest_date": None, "arithmetic": None,
           "not_derived_why": None}
    if age is None:
        out["not_derived_why"] = "the entry prints no age"
        return out
    if age["unreadable"] or age["approximate"]:
        out["not_derived_why"] = age["why"]
        return out
    if not dth["date"]:
        out["not_derived_why"] = ("the entry prints no year of death, so an age cannot be "
                                  "turned into a birth year")
        return out
    if int(dth["date"][:4]) < EARLIEST_PLAUSIBLE_DEATH:
        out["not_derived_why"] = (
            "the entry prints the death in %s, earlier than the earliest death this volume "
            "means to print (Marquette's, 1675), so the year is a transcription slip and no "
            "birth is derived from it. The quote is left as the page has it."
            % dth["date"][:4])
        return out
    if dth["date_qualifier"] in ("before", "after", "about", "circa"):
        out["not_derived_why"] = ("the death is printed as %r rather than as a date, so the "
                                  "subtraction has no fixed end" % (
                                      dth["date_qualifier"] + " " + dth["date_as_read"]))
        return out
    parts = [int(p) for p in dth["date"].split("-")]
    if dth["date_precision"] == "day":
        dmin = dmax = date(parts[0], parts[1], parts[2])
    elif dth["date_precision"] == "month":
        dmin = date(parts[0], parts[1], 1)
        dmax = date(parts[0], parts[1], last_day(parts[0], parts[1]))
    else:
        dmin, dmax = date(parts[0], 1, 1), date(parts[0], 12, 31)
    y, m, d = age["years"], age["months"], age["days"]
    if age["precision"] == "years_months_days":
        be, bl = minus_ymd(dmin, y, m, d), minus_ymd(dmax, y, m, d)
        span = ("An age printed to the day is exact: %d years, %d months and %d days back "
                "from the death" % (y, m, d))
    elif age["precision"] == "years_months":
        be = minus_ymd(dmin, y, m + 1, 0) + timedelta(days=1)
        bl = minus_ymd(dmax, y, m, 0)
        span = ("An age of %d years and %d months means at least that and less than %d "
                "years and %d months" % (y, m, y, m + 1))
    else:
        be = minus_ymd(dmin, y + 1, 0, 0) + timedelta(days=1)
        bl = minus_ymd(dmax, y, 0, 0)
        span = ("An age of %d completed years means at least %d and less than %d"
                % (y, y, y + 1))
    out["earliest_date"], out["latest_date"] = be.isoformat(), bl.isoformat()
    out["earliest"], out["latest"] = be.year, bl.year
    out["arithmetic"] = (
        "The page prints the death as %r and the age as %r. %s, so the birth falls between "
        "%s and %s: the birth year is %s. The subtraction is this project's; the page states "
        "no year of birth." % (
            dth["date_as_read"], age["as_printed"], span, be.isoformat(), bl.isoformat(),
            str(be.year) if be.year == bl.year else "%d or %d" % (be.year, bl.year)))
    return out


def parse_entry(section, first, last, text, seq):
    h = HEAD.match(text)
    surname = h.group("sn")
    alt = (h.group("paren") or "").strip()
    rest = h.group("rest")
    fields = [f.strip() for f in rest.split(",")]
    # "Huntoon, jr., Geo. M." — the suffix is printed in its own comma field, so a given
    # name read as fields[0] would be "jr." and the forenames would be filed as a trade.
    lead = 0
    while (lead + 1 < len(fields) and fields[lead]
           and all(t.strip(".,'\"()").lower() in TITLES or not t.strip(".,'\"()")
                   for t in fields[lead].split())):
        lead += 1
    given = ", ".join(fields[: lead + 1]).strip() if fields else ""
    # The trade sits between the name and the manner of death; where the manner comes
    # first there is no trade printed.
    mm = MANNER.search(rest)
    trade_zone = rest[: mm.start()] if mm else rest
    trade_fields = [f.strip(" .;") for f in trade_zone.split(",")[lead + 1:]
                    if f.strip(" .;")]
    trade = ", ".join(trade_fields) or None
    dth = parse_death(text)
    age = parse_age(text, dth["date_end"])
    birth = derive_birth(dth, age)
    printed = parse_born(text, dth["date_end"])
    if printed:
        birth["printed_on_the_page"] = printed
        birth["confidence"] = "documented"
        if birth["earliest"] is not None:
            agrees = birth["earliest_date"] <= printed["date"] <= birth["latest_date"]
            birth["printed_agrees_with_the_arithmetic"] = agrees
            birth["arithmetic"] += (
                " The page also prints the birth as %r, which %s the window — so here the "
                "subtraction is a CHECK on the page rather than the only evidence."
                % (printed["as_printed"],
                   "falls inside" if agrees else "falls OUTSIDE"))
    name = " ".join(x for x in [given.strip(" .;"), surname] if x).strip()
    rec = {
        "id": "fdn%04d" % seq,
        "letter_section": section,
        "as_read": text,
        "name_as_read": (surname + (" " + alt if alt else "") +
                         ((", " + given) if given else "")).strip(),
        "normalized": {
            "surname": surname,
            "surname_alternate": alt.strip("()") or None,
            "given_as_read": given or None,
            "name": name,
            "trade_or_office": trade,
            "manner_of_death": dth["manner_as_read"],
            "place_of_death_as_read": dth["place_as_read"],
            "place_default_chicago": dth["place_as_read"] is None,
            "death_date_as_read": dth["date_as_read"],
            "death_date": dth["date"],
            "death_date_precision": dth["date_precision"],
            "death_date_qualifier": dth["date_qualifier"],
            "death_day_not_read_why": dth["day_not_read_why"],
            "manner_note": dth["manner_note"],
            "death_year_implausible_why": (
                ("the printed year %s is earlier than the earliest death this volume means "
                 "to print (Marquette's, 1675); it is a transcription slip and is left as "
                 "the page has it" % dth["date"][:4])
                if dth["date"] and int(dth["date"][:4]) < EARLIEST_PLAUSIBLE_DEATH else None),
            "surname_split_note": next(
                (v for k, v in NAME_NOTES.items() if text.startswith(k)), None),
        },
        "age_at_death": age,
        "birth_year": birth,
        "birth_date_printed": printed,
        "reading": "transcription_mediated",
        "confidence": "documented",
        "source": SOURCE_ID,
        "locator": (
            "Robert Fergus, Directory of the City of Chicago, Illinois, for 1843 (Fergus "
            "Printing Company, 1896), OBITUARY, %s surnames, entry %r; read in K. Torp's "
            "2007 transcription at genealogytrails.com/ill/cook/earlysettlerobits.html, "
            "cached in this repository at data/research/old_settlers/text/"
            "fergus_1843_old_settler_death_notices.txt lines %d-%d"
            % (section, text[:60], first, last)),
        "spans": [[first, last]],
        "describes_date": (
            ("died %s" % dth["date"]) if dth["date"] else "death date not printed"),
        "describes_date_note": (
            "The date on this record is the DEATH, and a death is not a settlement. This "
            "list dates deaths; it dates no arrival, and the derived birth window is the "
            "only thing in the record that speaks to a year before 1843."),
        "places_in_1835": False,
        "places_in_1835_why": (
            "The list's own header admits it names \"some of Chicago's Old Settlers, prior "
            "to 1843, and other well - known citizens who arrived after 1843, together with "
            "others prominently connected with Illinois history\". Presence here therefore "
            "establishes neither residence in 1835 nor arrival before 1843."),
    }
    if dth["place_as_read"] is None:
        rec["normalized"]["place_default_note"] = PLACE_DEFAULT
    return rec


def build_records():
    lines = read_lines()
    entries = segment(lines)
    records = [parse_entry(sec, a, b, t, i + 1)
               for i, (sec, a, b, t) in enumerate(entries)]
    derived = [r for r in records if r["birth_year"]["earliest"] is not None]
    before_1836 = [r for r in derived if r["birth_year"]["latest"] <= 1835]
    doc = {
        "schema": SCHEMA,
        "domain": "old_settlers",
        "generated_by": "tools/read_fergus_obits.py --build",
        "source_id": SOURCE_ID,
        "what": (
            "Every entry of the OBITUARY printed in Robert Fergus's Directory of the City "
            "of Chicago for 1843 (1896) — names, trades, places, dates and ages at death of "
            "settlers and of other well-known citizens — read as it is printed, with the age "
            "kept verbatim beside the birth window it implies."),
        "reading": "transcription_mediated",
        "scene_relation": "later_evidence_only",
        "the_header_admission": HEADER_ADMISSION,
        "what_the_admission_costs_this_list": (
            "Presence in this list is not evidence of arrival before 1843 and never evidence "
            "of residence on 1 July 1835. Gov. Richard Yates, Henry Ward Beecher and Morris "
            "Birkbeck of Edwards County are all printed here. What the list gives is a DATE: "
            "a death, and through the age an interval the birth falls in. Under the ratified "
            "ladder (T-0513) that corroborates, enriches and dates; it never mints a resident "
            "and never lifts a grade."),
        "the_place_default": PLACE_DEFAULT,
        "the_arithmetic": (
            "Every birth window is `inferred` and carries its own subtraction. An age printed "
            "to the day ('82-2-15') is exact; an age in years and months ('48-6', and the "
            "fractions '89½' and '24 2/3', which are months the volume elsewhere spells out) "
            "gives a window of a month; a bare age in years gives a window of a year and so "
            "two candidate birth years. Where the age is truncated in the transcription, "
            "hedged with 'about', or the death carries no year, no window is derived and the "
            "record says which."),
        "counts": {
            "entries": len(records),
            "with_a_death_date": sum(1 for r in records if r["normalized"]["death_date"]),
            "with_a_printed_age": sum(1 for r in records if r["age_at_death"]),
            "birth_window_derived": len(derived),
            "birth_window_exact_to_a_year": sum(
                1 for r in derived
                if r["birth_year"]["earliest"] == r["birth_year"]["latest"]),
            "birth_window_wholly_before_1836": len(before_1836),
            "with_a_trade_or_office": sum(
                1 for r in records if r["normalized"]["trade_or_office"]),
            "died_outside_chicago": sum(
                1 for r in records if not r["normalized"]["place_default_chicago"]),
            "by_letter_section": {
                s: sum(1 for r in records if r["letter_section"] == s)
                for s in sorted({r["letter_section"] for r in records})},
        },
        "records": records,
    }
    return doc


# ---------------------------------------------------------------- the crosswalk

def residents():
    out = []
    for path in sorted(HH.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for p in doc.get("persons") or []:
            name = (p.get("name") or "").strip()
            if not name or (p.get("id") or "").endswith("_household"):
                continue
            parts = name.replace(",", " ").split()
            if len(parts) < 2:
                continue
            out.append({
                "person_id": p.get("id"),
                "household_id": doc.get("id"),
                "name": name,
                "surname": parts[-1],
                "given": " ".join(parts[:-1]),
                "grade": p.get("grade"),
                "occupation": ((p.get("occupation") or {}).get("value")),
            })
    return out


def row_of(rec):
    n = rec["normalized"]
    return {
        "record": rec["id"],
        "as_read": rec["as_read"],
        "trade_or_office": n["trade_or_office"],
        "manner_of_death": n["manner_of_death"],
        "place_of_death": n["place_of_death_as_read"],
        "death_date": n["death_date"],
        "age_as_printed": (rec["age_at_death"] or {}).get("as_printed"),
        "birth_year_earliest": rec["birth_year"]["earliest"],
        "birth_year_latest": rec["birth_year"]["latest"],
        "birth_year_arithmetic": rec["birth_year"]["arithmetic"],
    }


def beside_the_calumet_club(records):
    """T-0554 read the same genre a different way: John Wentworth's roll of forty old
    settlers dead since 1 January 1881, printed in the Tribune of 25 April 1882. Fergus's
    list runs to 1896 and covers those years, so the two overlap — and where both name one
    man, they can be held against each other. That is what this block does."""
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))["people"]
    roll = [p for p in people if p["roll"] == "wentworth_deaths_since_1881_01_01"]
    by_key = defaultdict(list)
    for r in records:
        k = (fold(r["normalized"]["surname"]), initial(r["normalized"]["given_as_read"] or ""))
        by_key[k].append(r)
    def spelled(given):
        for tok in (given or "").split():
            bare = tok.strip(".,'\"()").lower()
            if bare in TITLES or not bare:
                continue
            return bare if len(bare) > 1 else None
        return None

    agree, disagree, collisions, absent = [], [], [], []
    for p in roll:
        name = p["name_as_read"]
        parts = name.replace(",", " ").split()
        surname, given = parts[-1], " ".join(parts[:-1])
        hits = by_key.get((fold(surname), initial(given)), [])
        if not hits:
            absent.append({"wentworth": name, "died_as_read": p.get("died_as_read")})
            continue
        for h in hits:
            wd = (p.get("died_as_read") or "").strip()
            fd = h["normalized"]["death_date_as_read"]
            pair = {
                "wentworth": name,
                "wentworth_died_as_read": wd or None,
                "fergus_record": h["id"],
                "fergus_as_read": h["as_read"],
                "fergus_death_date": h["normalized"]["death_date"],
                "fergus_age_as_printed": (h["age_at_death"] or {}).get("as_printed"),
            }
            wy = re.search(r"1[5-9]\d\d", wd or "")
            fy = h["normalized"]["death_date"]
            wf, ff = spelled(given), spelled(h["normalized"]["given_as_read"] or "")
            same_man = not (wf and ff and wf != ff)
            pair["both_spell_the_forename"] = bool(wf and ff)
            if not same_man:
                pair["not_one_man"] = (
                    "The rule pairs these two on surname and initial, and the two lists spell "
                    "DIFFERENT forenames — %r and %r. They are two people, and the difference "
                    "in dates is the rule's, not the sources'. Recorded rather than dropped, "
                    "because a reader running the same rule will meet the same pair."
                    % (wf, ff))
                collisions.append(pair)
            elif wy and fy and fy[:4] == wy.group(0):
                agree.append(pair)
            else:
                pair["how_they_differ"] = (
                    "Both lists spell the same forename and they date the death differently: "
                    "Wentworth prints %r and Fergus prints %r. Neither is corrected against "
                    "the other. Both are transcriptions this project has not checked against "
                    "the printed pages, and either the two lists disagree about one man or "
                    "they are two men of one name — a finding, not an error to be resolved by "
                    "preference."
                    % (wd or "no date", h["normalized"]["death_date_as_read"] or "no date"))
                disagree.append(pair)
    return {
        "what": (
            "John Wentworth's roll of forty old settlers dead since 1 January 1881 (Chicago "
            "Tribune, 25 April 1882), read under T-0554, held against Fergus's list of the "
            "same genre. Both are lists of the deaths of Chicago's old settlers, compiled "
            "fourteen years apart by different hands, and Fergus's runs late enough to cover "
            "Wentworth's years."),
        "rule": (
            "Surname folded, first initial equal — the same rule the crosswalk uses. A name "
            "on Wentworth's roll that Fergus does not print is recorded as absent rather "
            "than as missing: Fergus's list is explicitly 'some of' the old settlers, so a "
            "silence in it is not evidence of anything."),
        "counts": {"wentworth_names": len(roll), "found_in_fergus_dates_agree": len(agree),
                   "found_in_fergus_dates_differ": len(disagree),
                   "paired_by_the_rule_but_not_one_man": len(collisions),
                   "not_in_fergus": len(absent)},
        "dates_agree": agree,
        "dates_differ": disagree,
        "paired_by_the_rule_but_not_one_man": collisions,
        "not_in_fergus": sorted(absent, key=lambda x: x["wentworth"]),
    }


def build_crosswalk(records):
    by_key, surnames = defaultdict(list), defaultdict(list)
    for r in records:
        f = fold(r["normalized"]["surname"])
        if not f:
            continue
        surnames[f].append(r)
        i = initial(r["normalized"]["given_as_read"] or "")
        if i:
            by_key[(f, i)].append(r)

    people = residents()
    matches, ambiguous, refusals = [], [], []
    for p in people:
        f, i = fold(p["surname"]), initial(p["given"])
        hits = by_key.get((f, i), [])
        if not hits:
            if f in surnames:
                refusals.append({
                    "resident": p["name"], "person_id": p["person_id"],
                    "surname_in_the_list": p["surname"],
                    "candidates": len(surnames[f]),
                    "rule": ("The surname %r is in Fergus's death notices and no entry under "
                             "it carries the initial %r of %r. A surname-only agreement is a "
                             "refusal, here as everywhere: the list prints eleven Smiths."
                             % (p["surname"], i.upper() or "-", p["name"])),
                })
            continue
        rows = [row_of(h) for h in hits]
        rec = {
            "resident": p["name"], "person_id": p["person_id"],
            "household_id": p["household_id"], "grade_1835": p["grade"],
            "occupation_1835": p["occupation"],
            "rule": ("Surname %r folds to the same string as the entry's, and the given name "
                     "of both begins %s." % (p["surname"], i.upper())),
            "resident_given_is_initial_only": all(
                len(t.strip(".,")) <= 1 for t in p["given"].split()
                if t.strip(".,").isalpha()),
            "entries": rows,
            "could_carry": sorted({k for k, v in {
                "date_of_death": any(x["death_date"] for x in rows),
                "birth_year": any(x["birth_year_earliest"] for x in rows),
                "trade": (not p["occupation"]) and any(x["trade_or_office"] for x in rows),
            }.items() if v}),
            "carry_rule": (
                "Whatever is carried is carried as evidence of a DEATH and of an interval "
                "the birth falls in, never as an 1835 fact and never as a grade. T-0513 "
                "consolidates and T-0514/T-0515 apply; this file changes no record."),
        }
        (matches if len(rows) == 1 else ambiguous).append(rec)

    claimed = defaultdict(list)
    for m in matches:
        claimed[m["entries"][0]["record"]].append(m)
    contested = []
    for _, rivals in sorted(claimed.items()):
        if len(rivals) > 1:
            for m in rivals:
                m["contested_with"] = [x["resident"] for x in rivals if x is not m]
                m["rule"] += (" CONTESTED: %d residents of 1835 meet this one entry on that "
                              "rule, and at most one of them is the person printed. The match "
                              "is not made." % len(rivals))
                contested.append(m)
    matches = [m for m in matches if "contested_with" not in m]

    return {
        "schema": SCHEMA,
        "domain": "old_settlers",
        "generated_by": "tools/read_fergus_obits.py --build",
        "source_id": SOURCE_ID,
        "_doc": (
            "Fergus's old-settler death notices against the 1835 residents layer. A PROPOSAL: "
            "it changes no resident record. READ THE NEXT FIELD BEFORE READING A MATCH."),
        "the_header_admission": HEADER_ADMISSION,
        "what_a_match_here_does_not_mean": (
            "It does not mean the person was in Chicago in 1835, and it does not mean they "
            "arrived before 1843 — the list's own header, quoted above, says it also names "
            "citizens who arrived later and others merely 'prominently connected with "
            "Illinois history'. A match means one thing: a name in the 1835 layer and a name "
            "in this list agree on surname and first initial, and the list gives that name a "
            "death date and an age. The date and the interval are the payload."),
        "rule": (
            "SURNAME must match after both are folded (case, punctuation and the "
            "transcriber's usual confusions removed), AND the first initial of the given name "
            "must match. A surname-only agreement is a REFUSAL, however good it looks. Where "
            "one 1835 person meets more than one entry the match is AMBIGUOUS and is filed as "
            "such; where two 1835 people meet one entry it is CONTESTED and no match is made."),
        "counts": {
            "residents_considered": len(people),
            "matched_one_entry": len(matches),
            "matched_more_than_one_ambiguous": len(ambiguous),
            "one_entry_contested_by_two_residents": len(contested),
            "surname_present_initial_absent_refused": len(refusals),
            "matches_carrying_a_birth_year": sum(
                1 for m in matches if "birth_year" in m["could_carry"]),
            "matches_carrying_a_date_of_death": sum(
                1 for m in matches if "date_of_death" in m["could_carry"]),
        },
        "matches": sorted(matches, key=lambda m: m["resident"]),
        "contested": sorted(contested, key=lambda m: m["resident"]),
        "ambiguous": sorted(ambiguous, key=lambda m: m["resident"]),
        "refusals": sorted(refusals, key=lambda m: m["resident"]),
        "beside_t0554_the_calumet_club": beside_the_calumet_club(records),
    }


# ---------------------------------------------------------------- gate

def problems(records_doc, crosswalk_doc, text, coverage):
    out = []
    fresh = build_records()
    if records_doc != fresh:
        out.append("death_notices.json does not match the reading — regenerate with --build")
    if crosswalk_doc != build_crosswalk(fresh["records"]):
        out.append("death_notices_crosswalk_1835.json does not match — regenerate")
    if text != CACHE.read_text(encoding="utf-8"):
        out.append("the domain's text copy is not byte-identical with the Genealogy Trails "
                   "cache it was taken from")
    decl = [d for d in coverage.get("declarations", []) if d.get("ticket") == "T-0574"]
    if not decl:
        out.append("coverage.json declares no T-0574 reading")
    else:
        want = decl[0].get("entries_read")
        if want != len(fresh["records"]):
            out.append("coverage.json declares %r entries and the text yields %d"
                       % (want, len(fresh["records"])))
    # Nothing in this list may claim the scene year, and nothing may be graded above the
    # reading. Both are one line of code and both are the failure this source invites.
    for r in fresh["records"]:
        if r["places_in_1835"] or r["reading"] != "transcription_mediated":
            out.append("record %s claims 1835 or a reading it cannot have" % r["id"])
            break
        by = r["birth_year"]
        printed = "printed_on_the_page" in by
        if by["confidence"] != ("documented" if printed else "inferred"):
            out.append("record %s grades its birth year %r, and the page %s print one"
                       % (r["id"], by["confidence"], "does" if printed else "does not"))
            break
    return out


def self_test():
    fresh = build_records()
    cross = build_crosswalk(fresh["records"])
    text = CACHE.read_text(encoding="utf-8")
    cov = json.loads(COVERAGE.read_text(encoding="utf-8"))
    assert not problems(fresh, cross, text, cov), "the gate does not pass on a clean tree"

    def fires(label, rd=None, cw=None, tx=None, cv=None):
        got = problems(rd if rd is not None else fresh,
                       cw if cw is not None else cross,
                       tx if tx is not None else text,
                       cv if cv is not None else cov)
        assert got, "assertion did not fire: " + label
        print("  fires:", label)

    bad = copy.deepcopy(fresh)
    bad["records"][0]["as_read"] = "Adams, E. F., died April 13, 1985, aged 72."
    fires("a hand-edited entry", rd=bad)
    bad = copy.deepcopy(fresh)
    bad["records"][3]["birth_year"]["confidence"] = "documented"
    fires("a birth year graded above inferred", rd=bad)
    bad = copy.deepcopy(fresh)
    bad["records"][5]["places_in_1835"] = True
    fires("an entry claiming the scene year", rd=bad)
    bad = copy.deepcopy(cross)
    bad["matches"] = bad["matches"][1:]
    fires("a match quietly dropped from the crosswalk", cw=bad)
    fires("a text copy that has drifted from its cache", tx=text.replace("Adams", "Adarns", 1))
    bad = copy.deepcopy(cov)
    for d in bad["declarations"]:
        if d.get("ticket") == "T-0574":
            d["entries_read"] = 743
    fires("a coverage count that no longer matches the text", cv=bad)
    bad = copy.deepcopy(cov)
    bad["declarations"] = [d for d in bad["declarations"] if d.get("ticket") != "T-0574"]
    fires("a reading with no coverage declaration", cv=bad)

    # The segmenter's own two traps, asserted directly because they are what a later
    # refactor would quietly undo.
    ids = {r["as_read"][:24]: r for r in fresh["records"]}
    assert not any(r["normalized"]["surname"] == "Oct" for r in fresh["records"]), \
        "the month that turns O'Hara's entry has become a man"
    assert any(r["name_as_read"].startswith("Sweet") for r in fresh["records"]), \
        "an entry whose printer dropped the comma has been lost"
    print("read_fergus_obits self-test: all assertions fire")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.build:
        DOMAIN.joinpath("text").mkdir(parents=True, exist_ok=True)
        TEXT.write_text(CACHE.read_text(encoding="utf-8"), encoding="utf-8")
        doc = build_records()
        RECORDS.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        cw = build_crosswalk(doc["records"])
        CROSSWALK.write_text(json.dumps(cw, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        print(json.dumps({"records": doc["counts"], "crosswalk": cw["counts"],
                          "beside_t0554": cw["beside_t0554_the_calumet_club"]["counts"]},
                         indent=1))
        return 0
    if args.check:
        got = problems(json.loads(RECORDS.read_text(encoding="utf-8")),
                       json.loads(CROSSWALK.read_text(encoding="utf-8")),
                       TEXT.read_text(encoding="utf-8"),
                       json.loads(COVERAGE.read_text(encoding="utf-8")))
        for g in got:
            print("fergus death notices:", g, file=sys.stderr)
        if got:
            return 1
        print("fergus death notices: %d entries rebuild from the committed text"
              % len(json.loads(RECORDS.read_text(encoding="utf-8"))["records"]))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
