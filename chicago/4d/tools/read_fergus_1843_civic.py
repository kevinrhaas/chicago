#!/usr/bin/env python3
"""Robert Fergus's *Directory of the City of Chicago, Illinois, for 1843* — page 1,
the CIVIC ACCOUNT above the business directory, read entry by entry (T-0589).

`--build` reads lines 37-750 of the committed page text at
`data/research/directories/text/fergus_1843_page_001.txt` and writes
`data/research/directories/claims/fergus_1843_civic.json`. `--check` rebuilds in
memory and compares, so a hand-edit of the generated file is caught the way
`read_fergus_1843.py` catches one; it also holds the count `coverage.json`
declares, because a declared range that quietly loses forty entries is exactly
the hole coverage exists to catch.

WHY THIS IS A SEPARATE READING FROM T-0571's. T-0571 read the DIRECTORY on this
page — the 174 classified business cards of lines 752-1204 — and the alphabetical
directory on pages 2-4. Above the business directory sits a different document:
the mayor and the common council, the county, state and United-States officers
and the courts, twenty-odd churches and societies with their ministers and their
memberships, the newspapers, the post-office and its mails, the military and fire
companies, Rush Medical College, the common schools, the ward population count of
1 August 1843 and the port's exports and imports. Its shape is not a list of
names and its kinds are not a directory's: `civic` for an office or a membership,
`building` for a church with a street, `business` for a newspaper office, `price`
for the trade tables, `shipping` for the vessels, `household` for the count of
families.

THE SEGMENTING RULE, and it has to be stated because the transcription's line
breaks are the transcriber's `<br>`s and not the printer's.

  1. A LINE CONTINUES THE ONE ABOVE when the line above is at least 88 characters
     long — the transcription's own wrap band runs 88 to 121 — AND does not end in
     terminal punctuation. 63 of the 714 lines are wraps by that rule and every one
     of them is a wrap.
  2. ONE EXCEPTION, and it is named rather than tuned away: line 261 ends the
     Hydraulic Company's list of directors on 'Smith Jones Sherwood', 96 characters
     and no stop, and line 262 opens a complete new sentence — 'Applications for
     water to be made to Smith J. Sherwood, 144 Lake Street.' No length threshold
     separates it from line 408, which is 96 characters, ends on 'It' and is a
     genuine wrap. The transcriber simply did not punctuate the end of a list.
  3. A LOGICAL LINE ENDING IN A COLON IS A HEADING. It carries no claim of its own
     — the one exception is a transposed table's caption, which is what dates the
     table and is claimed with it —
     — it is not a statement about the town — and is carried instead on every claim
     beneath it as `printed_section`, down to the next heading. Four headings the
     printer set with a full stop rather than a colon are named in HEADING_STOPS.
  4. EVERY OTHER LOGICAL LINE IS ONE CLAIM, except inside the three TRANSPOSED
     TABLES, where the transcription runs a table's columns down the page one cell
     to a line and a row is only a row when its cells are read back together: the
     ward population count, the exports-and-imports table which interleaves two
     columns four lines to the year, and the vessels arrived and cleared.

1843 IS EIGHT YEARS LATE. Nothing here is an 1835 fact and `describes_date` says
so on every claim — the year the STATEMENT describes, T-0567's rule, which is 1843
for all but the trade tables that date their own rows and the post-office's
history of the mails, which runs from 1832. A founding date inside an entry —
the Lyceum 'Instituted Dec. 2, 1834' — is dated 1843, because the entry is the
1843 canvass describing a body then standing and the founding year is carried
verbatim in the quote.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
OUT = os.path.join(ROOT, "data/research/directories/claims/fergus_1843_civic.json")
COVERAGE = os.path.join(ROOT, "data/research/directories/coverage.json")

PAGE = "fergus_1843_page_001"
CIVIC_FROM, CIVIC_TO = 37, 750

# The wrap band of this transcription, measured over lines 37-750: no line exceeds
# 121 characters and no line shorter than 88 is ever continued.
WRAP_MIN = 88
TERMINAL = (".", ":", ";", '"', "”", "]", "!", "?")
# Rule 2. The one place the wrap rule is wrong, and the line it is wrong at.
NOT_A_WRAP = {262: "the close of the Hydraulic Company's directors, unpunctuated; "
                   "line 262 opens a new sentence"}

# Rule 3. Headings the printer set with a stop instead of a colon.
HEADING_STOPS = {"Aldermen.", "Chicago Repeal Association.", "Young Men's Lyceum.",
                 "Hydraulic Company."}

# Rule 4. The three transposed tables, found by their own heading text so that a
# line number never has to be trusted. Each names the heading it starts at and the
# first line BELOW it that is no longer part of the table.
POP_HEAD, POP_END = "Wards:", "Port of Chicago:"
TRADE_HEAD, TRADE_END = "Exports :", "Articles Exported during the Year 1842:"
VESSEL_HEAD, VESSEL_END = ("Vessels arrived and cleared during the years 1842-3:",
                           "A number of vessels left port this year without being reported.")

# The trade blocks that are NOT transposed: a commodity and its quantity, one to a
# line, under a heading that dates the whole block.
ARTICLE_BLOCKS = {
    "Articles Exported during the Year 1842:": "1842",
    "Articles Exported during the Year 1843:": "1843",
    "Articles Imported During the Year 1843": "1843",
}

NUMERIC = re.compile(r"^\$?[\d,][\d,.]*$")
STREET = re.compile(r"\b(?:Street|Streets|Avenue|Av\.|st\b|corner|cor\.)", re.I)
NEWS_SECTIONS = {"Newspaper Offices and Publication Days",
                 "Book and Job Printing-office"}
RELIGIOUS = "Religious Societies and Associations"

# The post-office's history of the mails: one paragraph, and it describes the
# eleven years from the horseback mail of 1832 to the forty-eight mails a week of
# 1843. Named by its opening rather than dated 1843 like everything around it.
MAIL_HISTORY = "A weekly mail from the East was received here on horseback in 1832"

# A name is a comma- or dash-delimited segment whose every token is a personal-name
# token and none of which is a role. Deliberately narrow: the quote carries every
# name verbatim, and inventing a name list that is nearly right is worse for a
# later crosswalk than a short one that is right.
NAME_TOKEN = re.compile(r"^(?:[A-Z][A-Za-z'’\-]*\.?|[A-Z]\.|de|von|van|jr\.?|sr\.?|\(jr\.\))$")
ROLES = {
    "mayor", "clerk", "treasurer", "attorney", "surveyor", "collector", "marshal",
    "commissioner", "commissioners", "sheriff", "sheriffs", "coroner", "recorder",
    "assessor", "physician", "inspector", "constable", "constables", "president",
    "prest", "vice-president", "vice-presidents", "vice-prest", "secretary",
    "sec'y", "librarian", "director", "directors", "manager", "managers", "com",
    "committee", "foreman", "ass't-foreman", "assistant-foreman", "steward",
    "judge", "justice", "juistice", "justices", "reporter", "chancery", "master",
    "captain", "lieutenant", "lieut", "cornet", "sergeant", "chief-engineer",
    "governor", "lieutenant-governor", "lieut", "auditor", "postmaster",
    "professor", "prof", "prosector", "principal", "pastor", "pastors", "rector",
    "agent", "keeper", "register", "receiver", "congress", "district", "ward",
    "wards", "street", "streets", "avenue", "church", "company", "society",
    "scholars", "esq", "hon", "rev", "d", "school", "seminary", "office",
    "deputy", "assistant", "editor", "editors", "proprietor", "members",
    "total", "totals", "americans", "germans", "norwegians", "irish", "males",
    "females", "board", "health", "beef", "pork", "state", "county", "city",
    "united-states", "notaries", "public", "police", "military", "fire",
    "engine", "hose", "hook-and-ladder", "guards", "cavalry", "lodge", "lyceum",
    "association", "institute", "college", "dispensary", "schools", "teachers",
    "visitors", "trustees", "faculty", "port", "chicago", "harbor", "light-house",
    "works", "land-office", "poor", "master", "house", "poor-house", "sealer",
    "weights", "measures", "measures.", "bank", "arrived", "cleared",
    "arrives", "closes",
}

# The mail table and the newspapers set a day where a name would sit — 'Arrives
# Sunday, Wednesday, and Friday', 'Better Covenant , Saturday'. A day is never a
# Chicagoan, so it disqualifies a segment; but it is not a ROLE either, and
# role_follows must not read 'Saturday' as the office 'Better Covenant' holds.
CALENDAR = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "sept", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "oct", "nov", "dec",
}
ROLES |= CALENDAR

# A stop after one of these is Fergus abbreviating, not ending a sentence. Without
# them the segmenter cuts 'Wm. B. Ogden' after 'Wm' and files half a man.
ABBREV = ("Wm", "Chas", "Geo", "Jas", "Jos", "Benj", "Thos", "Saml", "Robt",
          "Danl", "Jno", "Edw", "Alex", "Fred", "Nath", "Rev", "Hon", "Capt",
          "Col", "Gen", "Maj", "Dr", "Esq", "Mr", "Mrs", "Sen", "St", "Co",
          "No", "Ill", "Wis", "Sec", "Prest", "Lieut", "Prof", "Bldgs")
ABBREV_RE = re.compile(r"\b(%s)\.\s" % "|".join(ABBREV))
SENTENCE = re.compile(r"(?<=[a-z])\.\s")


def lines_of():
    with open(os.path.join(TEXT, PAGE + ".txt"), encoding="utf-8") as fh:
        return fh.read().splitlines()


def logical(lines):
    """[first, last] 1-based inclusive pairs over CIVIC_FROM..CIVIC_TO."""
    out = []
    for n in range(CIVIC_FROM, CIVIC_TO + 1):
        prev = lines[n - 2] if n > 1 else ""
        wrap = (n > CIVIC_FROM and n not in NOT_A_WRAP
                and len(prev) >= WRAP_MIN and not prev.rstrip().endswith(TERMINAL))
        if wrap:
            out[-1][1] = n
        else:
            out.append([n, n])
    return [tuple(p) for p in out]


def flat(lines, first, last):
    return re.sub(r"\s+", " ", "\n".join(lines[first - 1:last])).strip()


def is_heading(text):
    return text.endswith(":") or text in HEADING_STOPS


def find(rows, lines, text):
    """The one logical row whose flattened text is exactly `text`."""
    hit = [i for i, (a, b) in enumerate(rows) if flat(lines, a, b) == text]
    if len(hit) != 1:
        raise SystemExit("fergus 1843 civic: %r appears %d times in lines %d-%d, and "
                         "the reading needs it exactly once"
                         % (text, len(hit), CIVIC_FROM, CIVIC_TO))
    return hit[0]


def names_in(text, roles_follow=False):
    """`roles_follow` is the newspaper rows' rule. Fergus sets a paper's TITLE in
    exactly a name's shape — 'Better Covenant', 'Western Citizen' — so under those
    two headings a segment is a name only when the segment AFTER it is the role he
    printed for it: 'Seth Barnes, editor and proprietor.'
    """
    out = []
    masked = ABBREV_RE.sub(lambda m: m.group(1) + ".\x00", text)
    segs = [s.replace("\x00", " ").strip().strip(".") for s in
            re.split(r",| - |- |;| and |(?<=[a-z])\.\s", masked)]
    for k, seg in enumerate(segs):
        toks = [t for t in seg.split() if t]
        if len(toks) < 2 or not all(NAME_TOKEN.match(t) for t in toks):
            continue
        if any(t.lower().strip(".'") in ROLES for t in toks):
            continue
        if not any(len(t.strip(".")) > 2 for t in toks):
            continue
        if roles_follow and not role_follows(segs, k):
            continue
        out.append(" ".join(toks))
    return out


def role_follows(segs, k):
    """True when the first segment after `k` that is not itself a name is a role.

    'Zebina Eastman and Asa B. Brown, editors' prints the role once for two men,
    so the look-ahead has to step over the names between.
    """
    for seg in segs[k + 1:]:
        toks = [t for t in seg.split() if t]
        if len(toks) > 1 and all(NAME_TOKEN.match(t) for t in toks) and \
                not any(t.lower().strip(".'") in ROLES for t in toks):
            continue      # another man sharing the role printed once below
        return any(t.lower().strip(".'") in ROLES - CALENDAR for t in toks)
    return False


def office_of(text):
    """(person, office) when the row is one man and the office he holds, else (None, None).

    Fergus sets these two ways and only two: 'James M. Lowe, Clerk.' and
    'Inspector of Beef and Pork - Archibald Clybourn.'
    """
    body = text.rstrip(".")
    m = re.match(r"^([^,]+),\s+([A-Z][^,]*)$", body)
    if m and "." in m.group(2):
        # 'Orson Smith, Health Officer.Collector. Marshal. Street Commissioner.' —
        # the transcription ran four offices together and printed a holder for one.
        # Reading it as Orson Smith's office would invent three appointments.
        return None, None
    if m and len(names_in(m.group(1))) == 1 and not names_in(m.group(2)):
        return names_in(m.group(1))[0], m.group(2).strip()
    m = re.match(r"^([^-]+?)\s*-\s+(.+)$", body)
    if m and not names_in(m.group(1)) and len(names_in(m.group(2))) == 1:
        return names_in(m.group(2))[0], m.group(1).strip()
    return None, None


def claim(n, kind, quote, loc, norm, date, town_finding, note=None):
    return {
        "id": "f1843c%04d" % n,
        "kind": kind,
        "reading": "transcription_mediated",
        "quote": quote,
        "normalized": norm,
        "locator": loc,
        "describes_date": date,
        "entities": norm.get("names") or [],
        "town_finding": town_finding,
        "notes": note,
    }


def loc_of(first, last, section, region):
    return {"text_file": PAGE + ".txt", "lines": [first, last], "page": PAGE,
            "printed_section": section, "region": region}


def population_rows(rows, lines, start, end):
    """label + its run of numeric cells. Six wards, then Totals, then — where the
    printer set one — the footing of the block above it.

    The seven column labels under 'Wards:' carry no cells of their own and are the
    key to every row below, so they are gathered into one claim rather than seven.
    """
    out, i, group = [], start, None
    heads = []
    j = start + 1
    while j < end:
        t = flat(lines, *rows[j])
        if NUMERIC.match(t) or is_heading(t):
            break
        heads.append(t)
        j += 1
    if heads:
        out.append((start, j - 1, "column heads", [], None))
        i = j
    while i < end:
        a, b = rows[i]
        text = flat(lines, a, b)
        if is_heading(text) and NUMERIC.match(text) is None:
            group = text.rstrip(":").strip() if text != POP_HEAD else None
            i += 1
            continue
        cells, j = [], i + 1
        while j < end:
            t = flat(lines, *rows[j])
            if not NUMERIC.match(t):
                break
            cells.append(t)
            j += 1
        out.append((i, j - 1, text, cells, group))
        if len(cells) == 8:
            # The printer's footing under a block closes it: 3,792 males, 3,190
            # females, 65 coloured. What follows belongs to no group.
            group = None
        i = max(j, i + 1)
    return out


def build_claims():
    lines = lines_of()
    rows = logical(lines)
    pop_a, pop_b = find(rows, lines, POP_HEAD), find(rows, lines, POP_END)
    tr_a, tr_b = find(rows, lines, TRADE_HEAD), find(rows, lines, TRADE_END)
    ve_a, ve_b = find(rows, lines, VESSEL_HEAD), find(rows, lines, VESSEL_END)

    claims, n, section, article_year = [], 0, None, None
    i = 0
    while i < len(rows):
        first, last = rows[i]
        text = flat(lines, first, last)

        # ---- the ward population count, 1 August 1843
        if i == pop_a:
            for a, b, label, cells, group in population_rows(rows, lines, pop_a, pop_b):
                n += 1
                lo, hi = rows[a][0], rows[b][1]
                by_ward = cells[:6] if len(cells) >= 7 else []
                total = cells[6] if len(cells) >= 7 else (cells[0] if len(cells) == 1 else None)
                footing = cells[7] if len(cells) == 8 else None
                date = "1840" if label == "Population 1840" else (
                    "1840-1843" if label == "Increase" else "1843")
                kind = "household" if label.startswith("Whole number of Families") else "civic"
                claims.append(claim(
                    n, kind, "\n".join(lines[lo - 1:hi]),
                    loc_of(lo, hi, POP_HEAD.rstrip(":"), "population"),
                    {"as_printed": flat(lines, lo, hi), "row": label, "group": group,
                     "by_ward": by_ward, "total": total, "block_footing": footing,
                     "names": []},
                    date, True,
                    "The census taken by Jas. W. Norris, 1 August 1843, under the "
                    "authority of the Common Council. Wards run 1st to 6th, left to "
                    "right, and `total` is the printer's own Totals column."))
            i = pop_b
            continue

        # ---- exports and imports by year: two columns interleaved, four lines a year
        if i == tr_a:
            n += 1
            head_lo, head_hi = rows[tr_a][0], rows[tr_a + 1][1]
            claims.append(claim(
                n, "price", "\n".join(lines[head_lo - 1:head_hi]),
                loc_of(head_lo, head_hi, "Port of Chicago", "trade"),
                {"as_printed": flat(lines, head_lo, head_hi),
                 "row": "column heads", "names": []},
                "1843", True,
                "The two column heads of the exports-and-imports table, which the "
                "transcription sets one above the other and then runs down the page "
                "four lines to the year."))
            j = tr_a + 2
            while j + 3 < tr_b:
                year, exports = flat(lines, *rows[j]), flat(lines, *rows[j + 1])
                year2, imports = flat(lines, *rows[j + 2]), flat(lines, *rows[j + 3])
                if year != year2:
                    raise SystemExit("fergus 1843 civic: the exports column reads %r "
                                     "where the imports column reads %r" % (year, year2))
                n += 1
                lo, hi = rows[j][0], rows[j + 3][1]
                claims.append(claim(
                    n, "price", "\n".join(lines[lo - 1:hi]),
                    loc_of(lo, hi, "Port of Chicago", "trade"),
                    {"as_printed": flat(lines, lo, hi), "row": year,
                     "exports": exports, "imports": imports, "names": []},
                    year, True,
                    "Value at the Custom-House, and the compiler's own warning above "
                    "the table is that it is considerably below the true amount: a "
                    "great many vessels arrived and departed unreported."))
                j += 4
            i = tr_b
            continue

        # ---- vessels arrived and cleared, 1842 and 1843
        if i == ve_a:
            n += 1
            lo, hi = rows[ve_a][0], rows[ve_a][1]
            claims.append(claim(
                n, "shipping", "\n".join(lines[lo - 1:hi]),
                loc_of(lo, hi, "Port of Chicago", "vessels"),
                {"as_printed": text, "row": "caption", "names": []},
                "1842-1843", True, None))
            j = ve_a + 1
            while j + 2 < ve_b + 1 and j + 2 <= ve_b - 1:
                label = flat(lines, *rows[j])
                v1842, v1843 = flat(lines, *rows[j + 1]), flat(lines, *rows[j + 2])
                n += 1
                lo, hi = rows[j][0], rows[j + 2][1]
                claims.append(claim(
                    n, "shipping", "\n".join(lines[lo - 1:hi]),
                    loc_of(lo, hi, "Port of Chicago", "vessels"),
                    {"as_printed": flat(lines, lo, hi), "row": label.rstrip("."),
                     "y1842": v1842.split("- ")[-1], "y1843": v1843.split("- ")[-1],
                     "names": []},
                    "1842-1843", True,
                    "Set as a column: the label, then 1842, then 1843."))
                j += 3
            i = ve_b
            continue

        # ---- everything else: one logical line, one claim
        if is_heading(text):
            section = text.rstrip(":").strip()
            if text in ARTICLE_BLOCKS:
                article_year = ARTICLE_BLOCKS[text]
            elif not text.startswith("Articles"):
                article_year = None
            i += 1
            continue
        if text in ARTICLE_BLOCKS:      # the 1843 imports head carries no colon
            section, article_year = text, ARTICLE_BLOCKS[text]
            i += 1
            continue

        person, office = office_of(text)
        names = names_in(text, roles_follow=section in NEWS_SECTIONS)
        region = "trade" if article_year else None
        if article_year:
            kind = "price"
        elif section in NEWS_SECTIONS:
            kind = "business"
        elif section == RELIGIOUS and STREET.search(text):
            kind = "building"
        else:
            kind = "civic"
        date = article_year or "1843"
        note = None
        if text.startswith(MAIL_HISTORY):
            date, note = "1832-1843", (
                "The post-office's own history of the mails, and it describes the "
                "eleven years from the horseback mail of 1832 to the forty-eight "
                "mails a week of 1843 rather than 1843 alone.")
        norm = {"as_printed": text, "section": section, "person": person,
                "office": office, "names": names}
        if article_year:
            m = re.match(r"^(.+?),?\s*-?\s*([\d,][\d,.]*)\s*(.*)$", text)
            norm["article"] = m.group(1).strip(" ,-\"") if m else None
            norm["quantity"] = m.group(2) if m else None
            norm["unit"] = (m.group(3).strip(" .") or None) if m else None
        n += 1
        claims.append(claim(n, kind, "\n".join(lines[first - 1:last]),
                            loc_of(first, last, section, region), norm, date,
                            person is None, note))
        i += 1
    return claims


DOC = ("GENERATED by tools/read_fergus_1843_civic.py --build out of the committed page "
       "text in data/research/directories/text/. Hand-edit and --check says so. Lines "
       "37-750 of page 1 — the civic account above the business directory: the city, "
       "county, state and United-States officers and the courts; the churches and "
       "societies with their ministers and memberships; the newspapers, the post-office "
       "and its mails; the military and fire companies; Rush Medical College, the "
       "dispensary, the common schools and the Female Seminary; the ward population "
       "count of 1 August 1843; and the port's exports, imports and vessels. Every "
       "statement is a claim, the quote is verbatim off the transcription and the "
       "reading is beside it. 1843, not 1835.")


def payload(claims):
    by_kind = {}
    for c in claims:
        by_kind[c["kind"]] = by_kind.get(c["kind"], 0) + 1
    return {
        "schema": 1,
        "_doc": DOC,
        "generated_by": "tools/read_fergus_1843_civic.py --build",
        "source_id": "fergus_chicago_directory_1843",
        "corpus": {
            "item": "genealogytrails cook county / 1843directory_1",
            "url": "https://genealogytrails.com/ill/cook/1843directory_1.html",
            "what": "K. Torp's 2007 transcription, on Genealogy Trails, of Robert Fergus, "
                    "Directory of the City of Chicago, Illinois, for 1843 (Fergus "
                    "Historical Series No. 28; Chicago: Fergus Printing Company, 1896). "
                    "This reading takes the first web page's CITY, COUNTY, STATE, AND "
                    "U.-S. OFFICERS, SCHOOLS, CHURCHES, SOCIETIES, STATISTICS, ETC. — "
                    "its lines 37-750. T-0571 read the business directory below it.",
            "committed": True,
            "how": "Cached into this repository on 2026-09-03 by "
                   "tools/read_genealogytrails.py and copied here byte for byte, so a "
                   "line number means the same thing in both.",
        },
        "reading_note": "transcription_mediated throughout, and doubly so: this is a web "
                        "transcription of Fergus's 1896 printing of a canvass made in "
                        "1843, and nobody on this project has seen the page. The "
                        "transcriber's damage is left in every quote on purpose — "
                        "'Mahlon Dickerson Ogden, Juistice.', 'Att'y-GeneraL', 'at 8}4 "
                        "a.m.', 'John B. Weir -¦ Vice-Presidents.' — because a tidied "
                        "quote cannot be found again. The repair, where one is safe, is "
                        "in normalized, and normalized is best effort. `names` is "
                        "deliberately narrow: a segment is a name only when every token "
                        "of it is a name token and none is a role word, so a line that "
                        "lists nine managers may yield fewer than nine. The quote carries "
                        "all of them, and a crosswalk is where a name in this volume may "
                        "touch a person standing in 1835 — not this file.",
        "date_note": "describes_date names the year the STATEMENT describes, T-0567's "
                     "rule. That is 1843 for all but four things: the exports-and-imports "
                     "table, whose rows date themselves 1836 to 1842; the articles "
                     "exported in 1842 and imported in 1843; the vessels, counted across "
                     "1842-1843; and the post-office's history of the mails, which runs "
                     "from 1832. A founding date inside an 1843 entry — the Chicago "
                     "Lyceum 'Instituted Dec. 2, 1834' — stays 1843, because the entry is "
                     "the 1843 canvass describing a body then standing and the founding "
                     "year is carried verbatim in the quote. NOTHING HERE IS AN 1835 FACT.",
        "counts": {"claims": len(claims), "by_kind": by_kind,
                   "by_item": {PAGE: len(claims)}},
        "claims": claims,
    }


def declared_counts():
    with open(COVERAGE, encoding="utf-8") as fh:
        cov = json.load(fh)
    for dec in cov.get("declarations") or []:
        if dec.get("ticket") == "T-0589":
            return dec.get("entries_by_item") or {}
    return {}


def main():
    claims = build_claims()
    doc = payload(claims)
    if "--check" in sys.argv:
        with open(OUT, encoding="utf-8") as fh:
            got = json.load(fh)
        if got != doc:
            print("fergus 1843 civic: the committed reading does not match the text — "
                  "regenerate with --build", file=sys.stderr)
            return 1
        declared = declared_counts()
        if declared != doc["counts"]["by_item"]:
            print("fergus 1843 civic: coverage.json declares %r and the text yields %r"
                  % (declared, doc["counts"]["by_item"]), file=sys.stderr)
            return 1
        print("fergus 1843 civic: %d claims, and they match the committed text and the "
              "count coverage.json declares" % len(claims))
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("fergus 1843 civic: %d claims → %s" % (len(claims), os.path.relpath(OUT, ROOT)))
    print("  by kind:", json.dumps(doc["counts"]["by_kind"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
