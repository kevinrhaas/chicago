#!/usr/bin/env python3
"""The Calumet Club's Old Settlers' receptions, read out of the documents they were printed in.

    tools/old_settlers.py --build       write receptions.json, people.json, crosswalk.json
    tools/old_settlers.py --check       the gate
    tools/old_settlers.py --self-test   the gate's assertions still fire when broken

T-0554. The owner asked for "the old settlers club ... their meetings ... add residents
accordingly make sure you include citations" and pointed at chicagology's Golden Age page
063, which reprints three Chicago Tribune documents of 1882: the fourth annual reception's
announcement with John Wentworth's roll of settlers who had died since 1 January 1881, an
interview with Capt. Thomas S. Eells of the arrival of 1832, and the report of the
reception of 18 May 1882 with the 118 guests who were present.

TWO THINGS THIS FILE IS CAREFUL ABOUT, because they are the two ways a source like this
goes wrong:

1. THE CLUB'S CRITERION IS NOT THE SCENE DATE. Its guests were residents of Chicago
   "prior to the 1st day of January, 1840, and were then 21 years of age". A name on the
   1882 roster therefore says the person was here some time before 1840 — it does NOT put
   them in the town on 1 July 1835. Under the ratified ladder (T-0513) a later
   recollection alone is never an 1835 resident; it corroborates, enriches and dates. So
   nothing here mints a resident, and nothing here regrades one: people.json carries a
   PROPOSED rung with the reason, for T-0513 to consolidate and T-0514/T-0515 to apply.
2. THE READING IS TRANSCRIPTION-MEDIATED. This project has not seen the Tribune pages.
   Every name is carried `as_read` exactly as the page prints it, slips and all, and the
   quote gate rebuilds each one out of the committed text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "data" / "research" / "old_settlers"
TEXT = DOMAIN / "text" / "chicago_tribune_1882_calumet_old_settlers.txt"
TEXT_1879 = DOMAIN / "text" / "calumet_club_1879_registry.txt"
RESIDENTS = ROOT / "data" / "residents"
SOURCES = ROOT / "data" / "sources"

SCHEMA = 1

# The three documents, and the source record each name is cited to.
SRC_PAGE = "chicagology_goldenage_063"
SRC_DEATHS = "chicago_tribune_1882_04_25_old_settler_deaths"
SRC_EELLS = "chicago_tribune_1882_05_17_eells_interview"
SRC_RECEPTION = "chicago_tribune_1882_05_19_fourth_reception"
SRC_1879 = "calumet_club_early_chicago_1879"

TITLES = {"rev.", "dr.", "col.", "capt.", "hon.", "mr.", "gen.", "judge"}
SUFFIXES = {"jr.", "jr", "sr.", "sr", "sen.", "sen", "jun.", "jun", "ii", "iii", "2d"}

# Surname spellings this file bridges, and WHY. A bridge is a declared judgement, not a
# fuzzy match: the reason has to be a statement about the documents, never a resemblance.
SPELLING_BRIDGES = {
    "beaubien": {
        "residents_spelling": "beaubien",
        "why": "no bridge needed; the surname is spelled the same in both places",
    },
    "hail": {
        "residents_spelling": "hall",
        "why": "the SAME page prints both: the death roll of 25 April 1882 has "
               "\"William A. Hail\" and the reception report of 19 May 1882 has "
               "\"William A. Hall, who was employed at Fort Dearborn as a gunsmith\". "
               "The page disagrees with itself about one man, which is recorded as a "
               "finding rather than resolved, and no resident is merged on it.",
        "merge": False,
    },
    "schock": {
        "residents_spelling": "schoch",
        "why": "the same page prints \"Adam Schock\" in the death roll and \"Adam "
               "Schoch, a soldier of Napoleon in the Italian and Spanish wars\" in the "
               "report. Recorded as the page's own variance; not a merge on its own.",
        "merge": False,
    },
}

# Nine lines of the guest roster fail their own punctuation — a comma set as a period, or
# no comma at all between the forename and the address. The split is DECLARED here rather
# than guessed by a rule, because a rule general enough to read "Freeman, Robert.
# Naperville" is general enough to read a forename out of a street name. `as_read` stays
# verbatim in every case; only the split is asserted.
LINE_FIXES = {
    "Clarke, Henry 92 Washington street, Chicago.":
        ("Henry", "92 Washington street, Chicago", "no comma after the forename"),
    "Morgan, P. R.. 705 Carroll avenue, Chicago.":
        ("P. R.", "705 Carroll avenue, Chicago", "the comma after the initials is set as a period"),
    "Saltonstall, F. G.. 125 La Salle street, Chicago.":
        ("F. G.", "125 La Salle street, Chicago", "the comma after the initials is set as a period"),
    "Wood, Alonzo C.. 240 Lexington street, Chiengo.":
        ("Alonzo C.", "240 Lexington street, Chiengo", "the comma after the initial is set as a period"),
    "Hamilton, P. D. Michigan avenue and Forty-fifth street, Chicago,":
        ("P. D.", "Michigan avenue and Forty-fifth street, Chicago", "no comma after the initials"),
    "Haines, E. M. Waukegan, Ill.":
        ("E. M.", "Waukegan, Ill.", "no comma after the initials"),
    "Freeman, Robert. Naperville, Ill.":
        ("Robert", "Naperville, Ill.", "the comma after the forename is set as a period"),
    "Grannis, S. W. Park Ridge, IlL.":
        ("S. W.", "Park Ridge, IlL.", "no comma after the initials"),
    "Taylor, Lewis,D., Glencoe, Cook Co., Ill.":
        ("Lewis D.", "Glencoe, Cook Co., Ill.", "the space between forename and initial is set as a comma"),
    "Carter, 1. B., 55 Twentieth street, Chicago.":
        ("1. B.", "55 Twentieth street, Chicago",
         "the first initial is set as the figure 1 — almost certainly I or J, and left "
         "as the page has it rather than guessed at"),
}

# A forename spelled two ways across the two documents. Declared, with the reason, and
# used only where the surname already matches and the residents layer holds one bearer.
FORENAME_BRIDGES = {
    "bennett": ("bennet", "the same forename with the final consonant doubled: the "
                          "papers' post-office return prints 'Bailey, Bennet' and "
                          "Wentworth's roll prints 'Bennett Bailey'"),
}



def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def text_lines() -> list[str]:
    """The committed transcription, minus its provenance header."""
    return [l for l in TEXT.read_text(encoding="utf-8").split("\n") if not l.startswith("#")]


def text_lines_1879() -> list[str]:
    """The committed transcription of the 1879 registry plate, minus its header."""
    return [l for l in TEXT_1879.read_text(encoding="utf-8").split("\n")
            if not l.startswith("#")]


# --- reading the two rosters -------------------------------------------------------

DEATH_START = "he should be at once notified:"
DEATH_END = "Chicago Tribune, May 17, 1882"
GUEST_START = "Names of Old Settlers Present, Residents and of Age Prior to 1840."
GUEST_END = "Well Welcomed."

DEATH_ROW = re.compile(r"^(?P<name>[^,]+(?:,\s*(?:Jr\.|Sr\.))?)[,.]\s*(?P<when>[A-Z][^,]*[,.]?\s*\d{4})\.?$")
# The surname stops at the FIRST comma or period, because the page sets several of them
# with a period where a comma belongs ("Blackman. Edwin, 70 La Salle street") and a
# greedy surname swallows the forename whole.
GUEST_ROW = re.compile(r"^(?P<surname>[^,.]+)[,.]\s*(?P<forename>[^,]+),\s*(?P<where>.+?)\.?$")


def slice_between(lines: list[str], start: str, end: str) -> list[str]:
    try:
        i = next(n for n, l in enumerate(lines) if l.strip() == start or l.strip().endswith(start))
        j = next(n for n, l in enumerate(lines) if n > i and l.strip() == end)
    except StopIteration:
        raise SystemExit("old_settlers: the committed text no longer carries %r ... %r" % (start, end))
    return [l.strip() for l in lines[i + 1:j] if l.strip()]


def read_death_roll(lines: list[str]) -> list[dict]:
    out = []
    for raw in slice_between(lines, DEATH_START, DEATH_END):
        m = DEATH_ROW.match(raw)
        if not m:
            raise SystemExit("old_settlers: unread death-roll line %r" % raw)
        name = m.group("name").strip()
        out.append({
            "as_read": raw,
            "name_as_read": name,
            "normalized": normalize_plain(name),
            "died_as_read": m.group("when").strip().rstrip("."),
        })
    return out


def read_guest_roster(lines: list[str]) -> list[dict]:
    out = []
    for raw in slice_between(lines, GUEST_START, GUEST_END):
        parse_note = None
        if raw in LINE_FIXES:
            forename, where, parse_note = LINE_FIXES[raw]
            surname = raw.split(",")[0].strip()
        else:
            m = GUEST_ROW.match(raw)
            if not m:
                raise SystemExit("old_settlers: unread guest-roster line %r" % raw)
            surname, forename = m.group("surname").strip(), m.group("forename").strip()
            where = m.group("where").strip().rstrip(".")
            if re.search(r"\d", forename) or len(forename.split()) > 3:
                raise SystemExit("old_settlers: line %r splits into a forename %r that "
                                 "is not a forename — declare it in LINE_FIXES"
                                 % (raw, forename))
        row = {
            "as_read": raw,
            "name_as_read": "%s, %s" % (surname, forename),
            "normalized": normalize_plain("%s %s" % (forename, surname)),
            "residence_1882_as_read": where,
        }
        if parse_note:
            row["parse_note"] = ("the page's punctuation fails here — %s; the split is "
                                 "declared in tools/old_settlers.py LINE_FIXES and the "
                                 "line is carried verbatim in as_read" % parse_note)
        out.append(row)
    return out



# --- the 1879 registry, read off the plate ------------------------------------------
# T-0577. The FIRST reception's printed proceedings set the registry as a five-column
# plate, sideways on pages 84-90, and the Internet Archive's OCR destroys it. The plate
# was therefore read off the PAGE IMAGES and committed column by column in
# text/calumet_club_1879_registry.txt, where " | " is the transcriber's column mark and
# everything between the marks is verbatim. This reader asserts nothing the plate does
# not print: a blank column stays blank, and the arrival YEAR is taken only where the
# date-of-arrival cell opens with four digits.

REG_YEAR = re.compile(r"^(1[78]\d\d)\b")


def read_1879_registry(lines: list[str]) -> tuple[list[dict], dict]:
    """(one row per registrant, in plate order; the three aggregate tables)."""
    people_rows: list[dict] = []
    tables: dict[str, list[dict]] = {}
    page = None
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("[page "):
            page = line.strip("[]").split()[1]
            continue
        if line.startswith("@"):
            parts = [c.strip() for c in line[1:].split("|")]
            if len(parts) != 3:
                raise SystemExit("old_settlers: unread aggregate cell %r" % raw)
            table, label, count = parts
            if not count.isdigit():
                raise SystemExit("old_settlers: aggregate cell %r has no count" % raw)
            tables.setdefault(table, []).append({"as_read": label, "count": int(count)})
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) != 5:
            raise SystemExit("old_settlers: the 1879 registry line %r does not carry the "
                             "plate's five columns" % raw)
        name, arrival, birthplace, age, address = cols
        if "," not in name:
            raise SystemExit("old_settlers: 1879 registry name %r has no surname comma" % raw)
        surname, forename = name.split(",", 1)
        surname, forename = surname.strip(), forename.strip().rstrip(",")
        if not forename:
            raise SystemExit("old_settlers: 1879 registry line %r has no forename" % raw)
        m = REG_YEAR.match(arrival)
        people_rows.append({
            "as_read": line,
            "page": page,
            "name_as_read": "%s, %s" % (surname, forename),
            "normalized": normalize_plain("%s %s" % (forename, surname)),
            "arrival_as_read": arrival or None,
            "arrival_year": int(m.group(1)) if m else None,
            "birthplace_as_read": birthplace or None,
            "age_1879_as_read": age or None,
            "residence_1879_as_read": address or None,
        })
    if not people_rows:
        raise SystemExit("old_settlers: the 1879 registry transcription is empty")
    return people_rows, tables


# The plate's PLACES OF BIRTH table counts states and countries; the registrants' own
# birthplace cells are towns, counties and abbreviations. Reconciling the two needs a
# declared mapping from the cell to the table's label, and this is it — an explicit list,
# never a guess. A cell that matches nothing lands in `unassigned` and is REPORTED, which
# is the honest outcome and the reason the reconciliation is worth having.
BIRTH_LABELS = {
    "Conn.": "Connecticut", "Connecticut": "Connecticut",
    "N.Y.": "New York", "N. Y.": "New York", "New York": "New York",
    "New York City": "New York",
    "Mass.": "Massachusetts", "Massachusetts": "Massachusetts",
    "Vt.": "Vermont", "Vermont": "Vermont",
    "N. H.": "N. Hampshire", "N.H.": "N. Hampshire",
    "New Hampshire": "N. Hampshire",
    "Penn.": "Pennsylvania", "Pennsylvania": "Pennsylvania",
    "Philadelphia": "Pennsylvania",
    "N. J.": "New Jersey", "N.J.": "New Jersey", "New Jersey": "New Jersey",
    "State of New Jersey": "New Jersey",
    "Maine": "Maine", "Md.": "Maryland", "Baltimore": "Maryland",
    "Ky.": "Kentucky", "Mich.": "Michigan", "Va.": "Virginia", "Virginia": "Virginia",
    "North Carolina": "N. Carolina",
    "England": "England", "Eng.": "England",
    "Ireland": "Ireland",
    "Scotland": None,
}


def birth_label(cell: str | None) -> str | None:
    """The PLACES OF BIRTH label the plate would file this birthplace under, or None."""
    if not cell:
        return None
    cell = cell.split("[")[0].strip().rstrip(".").strip()
    if not cell:
        return None
    parts = [p.strip() for p in cell.split(",") if p.strip()]
    for part in reversed(parts):
        if part in BIRTH_LABELS:
            return BIRTH_LABELS[part]
        if (part + ".") in BIRTH_LABELS:
            return BIRTH_LABELS[part + "."]
    return None


def reconcile_1879(rows: list[dict], tables: dict) -> dict:
    """The plate's own aggregates against the names this project actually read."""
    printed_birth = {c["as_read"]: c["count"] for c in tables.get("places_of_birth", [])}
    printed_years = {c["as_read"]: c["count"] for c in tables.get("years_of_arrival", [])
                     if c["as_read"] != "Total"}
    printed_ages = {c["as_read"]: c["count"] for c in tables.get("ages", [])}

    read_birth: dict[str, int] = {}
    unassigned = []
    for r in rows:
        label = birth_label(r["birthplace_as_read"])
        if label is None:
            unassigned.append({"name_as_read": r["name_as_read"],
                               "birthplace_as_read": r["birthplace_as_read"]})
        else:
            read_birth[label] = read_birth.get(label, 0) + 1
    read_years: dict[str, int] = {}
    for r in rows:
        if r["arrival_year"] is not None:
            k = str(r["arrival_year"])
            read_years[k] = read_years.get(k, 0) + 1
    read_ages: dict[str, int] = {}
    for r in rows:
        a = (r["age_1879_as_read"] or "").strip()
        if a.isdigit():
            read_ages[a] = read_ages.get(a, 0) + 1

    def delta(printed: dict, read: dict) -> list:
        out = []
        for k in sorted(set(printed) | set(read), key=lambda x: (len(x), x)):
            pv, rv = printed.get(k, 0), read.get(k, 0)
            if pv != rv:
                out.append({"label": k, "printed": pv, "read": rv, "delta": rv - pv})
        return out

    return {
        "what": "The proceedings tabulate the 149 who \"signed the registry during the "
                "evening\"; the plate on pages 84-90 prints the register itself, which "
                "carries MORE names than that. Both counts are the document's own and "
                "both are kept. Every table below is the plate's arithmetic set beside "
                "the names this project read out of it.",
        "printed_count_of_signers": 149,
        "printed_count_basis": "\"of the settlers of Chicago prior to 1840, one hundred "
                               "and forty-nine registered their names out of the large "
                               "number invited\" (printed page 72), and the YEARS OF "
                               "ARRIVAL table's own \"Total ... 149\"",
        "names_read_off_the_register": len(rows),
        "excess_over_printed_count": len(rows) - 149,
        "why_the_two_differ": "the proceedings say so on the same page: \"Many left "
                             "without knowing that there was a registry being kept. A "
                             "few called afterward and signed the registry, and all "
                             "Chicago settlers, prior to 1840, are now requested to do "
                             "so.\" The three tables count the evening's signers; the "
                             "printed register is the fuller book. THIS IS NOT "
                             "RESOLVED HERE — the plate does not say which entries were "
                             "the later ones, and nothing in this project guesses. One "
                             "corroboration that the register outruns the tables: "
                             "Robert Fergus registered as born at Glasgow, Scotland, and "
                             "the PLACES OF BIRTH table has no Scotland at all.",
        "printed_tables_sum_to": {
            "places_of_birth": sum(printed_birth.values()),
            "years_of_arrival": sum(printed_years.values()),
            "ages": sum(printed_ages.values()),
        },
        "places_of_birth": {"printed": printed_birth, "read": read_birth,
                            "differences": delta(printed_birth, read_birth),
                            "unassigned": unassigned,
                            "mapping": "cell-to-label by the declared list in "
                                       "tools/old_settlers.py BIRTH_LABELS; an "
                                       "unmapped cell is reported, not forced"},
        "years_of_arrival": {"printed": printed_years, "read": read_years,
                             "differences": delta(printed_years, read_years)},
        "ages": {"printed": printed_ages, "read": read_ages,
                 "differences": delta(printed_ages, read_ages)},
    }


def normalize_plain(name: str) -> str:
    """Reorder and de-space. NOT a spelling correction: the page's letters are kept."""
    s = re.sub(r"\s+", " ", name).strip().rstrip(".,")
    s = s.replace("Chi-cago", "Chicago")
    return s


def name_key(name: str) -> tuple[str, str, list[str]]:
    """(surname, first-forename initial, forename tokens) — the identity key, lowercased."""
    toks = [t for t in re.split(r"\s+", name.strip()) if t]
    toks = [t for t in toks if t.lower() not in TITLES]
    while toks and toks[-1].lower().strip(".,") in SUFFIXES:
        toks = toks[:-1]
    if not toks:
        return ("", "", [])
    # "Beaubien, Medore B." arrives here already reordered, so the surname is last.
    surname = toks[-1].lower().strip(".,")
    fore = [t.lower().strip(".,") for t in toks[:-1]]
    # A two-word surname the page writes with a space: keep the particle with it.
    if len(toks) >= 3 and toks[-2].lower() in {"van", "de", "der", "la", "mc"}:
        surname = (toks[-2] + " " + toks[-1]).lower().strip(".,")
        fore = [t.lower().strip(".,") for t in toks[:-2]]
    return (surname, (fore[0][:1] if fore else ""), fore)


# --- the residents layer, and what may be said to be one person ---------------------

def resident_index() -> list[dict]:
    rows = []
    for path in sorted((RESIDENTS / "households").glob("*.json")):
        h = load(path)
        # OS2A READS THE RECORD'S OWN SPELLING OF THE NAME, AND NOT A DIRECTORY'S (T-0632).
        # The rule's discriminator is that the resident's record spells the roster's
        # forename somewhere in it, and it is implemented as a scan of the whole file.
        # `tools/spend_directories.py` now puts a `directories` block on 129 of these
        # records holding what Fergus 1839/1843 and Norris 1844 print against the person
        # — and those entries were matched to the person on SURNAME PLUS INITIAL, which
        # is the very rule OS2A exists to strengthen. Letting the block into the scan
        # makes the test circular: it would merge a roster name because a directory
        # matched on initials spells it out, and it silently added three merges the
        # moment the block landed. The block is excluded, so this rule reads what it
        # always read.
        # T-0678 ADDS THE SECOND BLOCK, for exactly the reason the first one is here.
        # `tools/spend_old_settlers.py` writes Fergus's death notices onto these cards,
        # and a notice prints a forename — "Flint, Dr. Austin" lands on the card of
        # "A. W. Flint". Left in the scan it hands OS2A the spelling OS2A exists to find
        # independently, and the roster merge then follows from this project's own write:
        # measured, it added two merges the moment the block landed, which is the same
        # count the directories block silently added when it did.
        record_source = {k: v for k, v in h.items()
                         if k not in ("directories", "old_settler_deaths")}
        record_text = json.dumps(record_source, ensure_ascii=False)
        for p in h.get("persons") or []:
            surname, initial, fore = name_key(p.get("name") or "")
            # A DEATH THE RECORD ITSELF CARRIES. Fergus's 1843 old-settler death notices
            # are already spent onto some of these cards, and a man who died before a
            # reception cannot have signed its register. The index carries the date so
            # the contradiction can be stated on the card rather than hidden by a merge.
            death = next((b for b in (p.get("book_evidence") or [])
                          if b.get("list") == "death_notice"), None)
            rows.append({
                "person_id": p.get("id"), "household_id": h.get("id"),
                "name": p.get("name"), "grade": p.get("grade"),
                "surname": surname, "initial": initial, "forenames": fore,
                "record_text": (record_text + " " + (p.get("id") or "")).lower(),
                "death_notice_as_read": (death or {}).get("as_read"),
                "death_notice_date": (death or {}).get("describes_date"),
                "file": "data/residents/households/%s" % path.name,
            })
    return rows


RULES = {
    "OS1": "surname equal AND both sides spell the first forename out AND they agree "
           "(a middle initial, where both give one, must agree too) → MERGED. Only an "
           "OS1 merge may be written onto a resident record.",
    "OS2A": "surname equal AND the forename initial agrees AND the resident's own "
            "record spells the roster's forename somewhere in it — its id, its name or "
            "its research note → MERGED. The spelling is the discriminator the roster "
            "does not supply.",
    "OS2": "surname equal AND the forename initial agrees AND the residents layer holds "
           "exactly ONE bearer, but neither side spells the forename out → PROBABLE, "
           "and probable is not merged. It goes to the identity master (T-0513) as a "
           "proposal and touches no record. THE CASE THAT SETTLED THIS: the roster's "
           "\"Clarke, Henry\" would have merged, on a single-bearer rule, into the "
           "documented 'H. B. Clarke' of the 1835 papers — and a guest alive in May "
           "1882 must have been alive in May 1882, a test this project cannot apply "
           "because its resident records carry no death dates.",
    "OS3": "surname equal AND the first-forename initials differ → NEVER one person "
           "(the newspapers' rule, kept here unchanged)",
    "OS4": "surname equal but the roster gives initials only and the residents layer "
           "holds more than one bearer → candidate, not a merge",
    "OS5": "no bearer of the surname in the residents layer → unmatched",
}


def death_on_the_record(r: dict) -> dict:
    """What the merged-into record already says about this man's death, if anything."""
    if not r.get("death_notice_date"):
        return {}
    return {"record_death_notice_as_read": r["death_notice_as_read"],
            "record_death_notice_date": r["death_notice_date"]}


def match(person: dict, residents: list[dict]) -> dict:
    surname, initial, fore = name_key(person["normalized"])
    bearers = [r for r in residents if r["surname"] == surname]
    if not bearers:
        return {"rule": "OS5", "outcome": "unmatched", "person_id": None,
                "why": "no bearer of the surname '%s' in the residents layer" % surname}
    same_initial = [r for r in bearers if r["initial"] == initial]
    if not same_initial:
        return {"rule": "OS3", "outcome": "refused", "person_id": None,
                "why": "the residents layer has %d bearer(s) of '%s', none with the "
                       "forename initial '%s'; same surname, different forename initial "
                       "never merges" % (len(bearers), surname, initial)}
    roster_fore = fore[0] if fore else ""
    bridged = FORENAME_BRIDGES.get(roster_fore)

    def spelled_agrees(r) -> bool:
        if not (roster_fore and len(roster_fore) > 2 and r["forenames"]
                and len(r["forenames"][0]) > 2):
            return False
        if r["forenames"][0] == roster_fore:
            return True
        return bool(bridged and r["forenames"][0] == bridged[0])

    spelled = [r for r in same_initial if spelled_agrees(r)]
    if len(spelled) == 1:
        r = spelled[0]
        mid_roster = [t for t in fore[1:] if t]
        mid_res = [t for t in r["forenames"][1:] if t]
        if mid_roster and mid_res and mid_roster[0][:1] != mid_res[0][:1]:
            return {"rule": "OS3", "outcome": "refused", "person_id": None,
                    "why": "forename agrees but the middle initials disagree "
                           "('%s' against '%s')" % (mid_roster[0], mid_res[0])}
        why = "surname and spelled-out forename agree, one bearer"
        if bridged and r["forenames"][0] == bridged[0]:
            why += "; the forename is bridged — %s" % bridged[1]
        return {"rule": "OS1", "outcome": "merged", "person_id": r["person_id"],
                "household_id": r["household_id"], "resident_name": r["name"],
                "resident_grade": r["grade"], "why": why,
                **death_on_the_record(r)}
    if len(same_initial) == 1 and len(bearers) == 1:
        r = same_initial[0]
        if roster_fore and len(roster_fore) > 2 and roster_fore in r["record_text"]:
            return {"rule": "OS2A", "outcome": "merged", "person_id": r["person_id"],
                    "household_id": r["household_id"], "resident_name": r["name"],
                    "resident_grade": r["grade"],
                    "why": "one bearer of the surname, the forename initial agrees, and "
                           "the resident's own record spells the roster's forename "
                           "'%s' — the discriminator the roster's initials do not "
                           "supply" % roster_fore,
                    **death_on_the_record(r)}
        return {"rule": "OS2", "outcome": "probable", "person_id": None,
                "probable_person_id": r["person_id"],
                "household_id": r["household_id"], "resident_name": r["name"],
                "resident_grade": r["grade"],
                "why": "one bearer of the surname in the whole residents layer and the "
                       "forename initial agrees, but neither side spells the forename "
                       "out and nothing discriminates. PROBABLE, NOT MERGED: no record "
                       "is written on it"}
    return {"rule": "OS4", "outcome": "candidate", "person_id": None,
            "candidates": [r["person_id"] for r in same_initial],
            "why": "%d bearers of '%s' share the forename initial '%s'; the roster does "
                   "not discriminate between them" % (len(same_initial), surname, initial)}


# --- the ladder, proposed and never applied ----------------------------------------

def proposed_rung(person: dict, m: dict) -> dict:
    """What the ratified ladder (T-0513) says about this name. A PROPOSAL."""
    dated = person.get("arrival_year")
    if m["outcome"] == "probable":
        return {
            "rung": "no_change",
            "reason": "a probable identity is not an identity. The row is a proposal for "
                      "the cross-source identity master (T-0513); nothing is written on "
                      "a resident record from it.",
        }
    if m["outcome"] == "merged":
        reason = ("the person is already in the residents layer at grade '%s'. This "
                  "source is a later recollection: it corroborates and dates, and "
                  "under the ratified ladder it cannot lift a rung by itself. The "
                  "citation goes on the record; the grade is T-0515's to revisit "
                  "with a contemporary second source." % m.get("resident_grade"))
        if dated:
            reason += (" What this roll adds that the 1882 one could not: the man's own "
                       "date of arrival, %s, registered in his own hand in 1879. That "
                       "is a DATED RECOLLECTION and it is worth what the ladder says a "
                       "recollection is worth — it is not a contemporary record of %d."
                       % ((person.get("arrival_as_read") or "").rstrip(", ") or dated, dated))
        return {"rung": "no_change", "reason": reason}
    unmatched = {
        "rung": "not_a_resident_on_this_evidence",
        "reason": "the club's criterion is residence in Chicago prior to 1 January 1840 "
                  "and majority by then — which does not place the person in the town on "
                  "1 July 1835. '1839/1840 alone is never a 1835 resident (later "
                  "evidence only)'; a reception roster of 1882 is weaker still. Minting "
                  "waits on a contemporary source (T-0514).",
    }
    if dated:
        unmatched["reason"] += (
            " This man is NOT in the residents layer and registered %s as his date of "
            "arrival in 1879. That is a lead for T-0514 to run down in a contemporary "
            "record — it is not a mint." % ((person.get("arrival_as_read") or "").rstrip(", ") or dated))
    return unmatched


# --- the receptions -----------------------------------------------------------------

DEATH_YEAR = re.compile(r"(1[78]\d\d)")


def registered_after_a_documented_death(rows: list[dict]) -> list[dict]:
    """Merges the residents layer's own death notice contradicts. NOT resolved here."""
    out = []
    for r in rows:
        m = r["residents_layer"]
        stamped = m.get("record_death_notice_date")
        if m["outcome"] != "merged" or not stamped:
            continue
        y = DEATH_YEAR.search(stamped)
        event = 1879 if r["roll"].startswith("registry_1879") else 1882
        if not y or int(y.group(1)) >= event:
            continue
        out.append({
            "row": r["id"], "roll": r["roll"], "as_read": r["name_as_read"],
            "person_id": m["person_id"], "rule": m["rule"],
            "record_death_notice": "%s — %s" % (m["record_death_notice_as_read"], stamped),
            "the_contradiction": "the roll of %d prints this man alive and the record it "
                                 "merges into carries a death notice of %s"
                                 % (event, stamped),
            **({"age_on_the_register": r["age_1879_as_read"]}
               if r.get("age_1879_as_read") else {}),
        })
    return out


def receptions(guests: list[dict], deaths: list[dict],
               registry_1879: list[dict] | None = None,
               reconciliation: dict | None = None,
               contradictions: list[dict] | None = None) -> dict:
    return {
        "schema": SCHEMA,
        "domain": "old_settlers",
        "generated_by": "tools/old_settlers.py --build",
        "what": "The Calumet Club of Chicago's annual receptions to the Old Settlers — "
                "the meetings the owner asked about — as a source SERIES: one row per "
                "reception, with its date, where it was held, where its roster is "
                "printed, and how many names that roster carries. A row is DECLARED "
                "whether or not this project has read its roster yet; 'roster_read' is "
                "the honest field, and an unread roster is a hole this file makes "
                "visible rather than a silence.",
        "the_club": {
            "name": "The Calumet Club of Chicago",
            "organized": "1878",
            "first_rooms": "the residence of the late Gen. Anson Stager, Michigan "
                           "Avenue at Eighteenth Street",
            "own_building": "Michigan Avenue, north-east corner of Twentieth Street; "
                            "Burnham and Root; under construction in 1882 and occupied "
                            "from 1884",
            "criterion_for_a_guest": "residents of Chicago prior to the 1st day of "
                                     "January, 1840, who were then 21 years of age",
            "sources": [SRC_PAGE, SRC_RECEPTION],
            "note": "The criterion is the reason this series cannot make an 1835 "
                    "resident on its own: it reaches to the end of 1839.",
        },
        "receptions": [
            {
                "id": "calumet_1879_first",
                "ordinal": 1,
                "date": "1879-05-27",
                "date_as_printed": "Tuesday evening, May 27, 1879",
                "venue": "the Calumet Club's rooms, Michigan Avenue at Eighteenth Street",
                "venue_basis": "INFERRED, and the inference is the 1888 Chicago Clubs "
                               "Illustrated: the club, organised in 1878, \"occupied for "
                               "the first few years of its existence the residence of the "
                               "late General Anson Stager, at the corner of Michigan "
                               "Avenue and Eighteenth Street\". The proceedings of 1879 "
                               "were not read for the address.",
                "host": "The Calumet Club of Chicago",
                "roster_printed_in": "Early Chicago: Reception to the Settlers of "
                                     "Chicago Prior to 1840, by the Calumet Club, of "
                                     "Chicago (Chicago, 1879) — the club's own printed "
                                     "proceedings, reprinted in the Fergus Historical "
                                     "Series",
                "roster_names": len(registry_1879 or []),
                "roster_names_basis": "READ off the printed register, pages 84-90, entry "
                                      "by entry. The proceedings' OWN count of the men "
                                      "who signed during the evening is 149 (\"of the "
                                      "settlers of Chicago prior to 1840, one hundred "
                                      "and forty-nine registered their names out of the "
                                      "large number invited\", printed page 72), and the "
                                      "printed register carries more than that. Both "
                                      "counts are kept; reconciliation_1879 sets them "
                                      "side by side.",
                "roster_names_printed_count_of_signers": 149,
                "roster_read": True,
                "roster_read_how": "off the PAGE IMAGES of the Internet Archive copy "
                                   "earlychicagorece00calu (its own text PDF, rendered "
                                   "at 300 dpi and rotated upright — the plate is set "
                                   "sideways). The item's OCR text layer keeps the "
                                   "proceedings' prose and DESTROYS this plate, so "
                                   "nothing in the register comes from it. The "
                                   "transcription is committed at "
                                   "data/research/old_settlers/text/"
                                   "calumet_club_1879_registry.txt.",
                "carries_year_of_arrival": True,
                "reconciliation_1879": reconciliation,
                "sources": [SRC_1879],
                "note": "THE ONE ROSTER IN THE SERIES THAT DATES ITS PEOPLE, and this "
                        "pass read it: each man's own date of arrival, birthplace, age "
                        "and 1879 post-office address. The three aggregate tables of "
                        "printed page 72 were read off the same plate — including the "
                        "YEARS OF ARRIVAL table, which this project had previously "
                        "recorded as unreadable because the Internet Archive OCR "
                        "mangles it. A year of arrival is still NOT an 1835 residence: "
                        "it is a recollection registered in 1879, and every person row "
                        "here says so.",
            },
            {
                "id": "calumet_1880_second",
                "ordinal": 2,
                "date": "1880",
                "date_as_printed": None,
                "venue": "the Calumet Club's rooms, Michigan Avenue at Eighteenth Street",
                "venue_basis": "INFERRED from the 1888 Chicago Clubs Illustrated's "
                               "statement that the club held the Stager residence at "
                               "Michigan Avenue and Eighteenth Street for its first few "
                               "years. No report of this reception has been read.",
                "host": "The Calumet Club of Chicago",
                "roster_printed_in": "Chicago Tribune, the morning after the reception — "
                                     "issue not yet located",
                "roster_names": None,
                "roster_names_basis": None,
                "roster_read": False,
                "carries_year_of_arrival": None,
                "sources": [SRC_RECEPTION],
                "note": "DECLARED, NOT READ. The existence and the ordinal are the "
                        "arithmetic of the 1882 report: the reception of 18 May 1882 is "
                        "the FOURTH annual and its report says \"As on the three "
                        "previous occasions\", which places the second in 1880 and the "
                        "third in 1881. Nothing here states its date or its roster.",
            },
            {
                "id": "calumet_1881_third",
                "ordinal": 3,
                "date": "1881",
                "date_as_printed": None,
                "venue": "the Calumet Club's rooms, Michigan Avenue at Eighteenth Street",
                "venue_basis": "INFERRED from the 1888 Chicago Clubs Illustrated's "
                               "statement that the club held the Stager residence at "
                               "Michigan Avenue and Eighteenth Street for its first few "
                               "years. No report of this reception has been read.",
                "host": "The Calumet Club of Chicago",
                "roster_printed_in": "Chicago Tribune, the morning after the reception — "
                                     "issue not yet located",
                "roster_names": 160,
                "roster_names_basis": "the 1882 report's own comparison: \"there were in "
                                      "the house the following-named guests—118 in "
                                      "number—while the number at the third reception "
                                      "was 160\"",
                "roster_read": False,
                "carries_year_of_arrival": None,
                "sources": [SRC_RECEPTION],
                "note": "DECLARED, NOT READ. The count is the 1882 report's, not a "
                        "reading of the 1881 roster. The club's photograph gallery grew "
                        "\"since May, 1881\", which dates the third reception to May.",
            },
            {
                "id": "calumet_1882_fourth",
                "ordinal": 4,
                "date": "1882-05-18",
                "date_as_printed": "the 18th of May [1882], Thursday evening",
                "venue": "the Calumet Club's club-room, Michigan Avenue at Eighteenth "
                         "Street — the club's own building on Twentieth Street was still "
                         "\"under process of construction\"",
                "venue_basis": "the Tribune of 25 April 1882 says the reception is held in "
                               "\"their club-room\" and that the club cannot invite more "
                               "guests until \"their large building now under process of "
                               "construction shall be completed\"; that the club-room was "
                               "then the Stager residence at Michigan and Eighteenth is the "
                               "1888 Chicago Clubs Illustrated's, not the Tribune's.",
                "host": "The Calumet Club of Chicago; Vice-President J. W. Doane "
                        "welcomed the guests, the Hon. John Wentworth answered for the "
                        "old settlers",
                "roster_printed_in": "Chicago Tribune, 19 May 1882, under \"Names of Old "
                                     "Settlers Present, Residents and of Age Prior to "
                                     "1840\"; the year's deaths in the Tribune of 25 "
                                     "April 1882",
                "roster_names": len(guests),
                "roster_names_basis": "read line by line off the roster as chicagology "
                                      "063 reprints it; the report's own count of the "
                                      "guests in the house is 118",
                "roster_read": True,
                "carries_year_of_arrival": False,
                "sources": [SRC_RECEPTION, SRC_DEATHS, SRC_EELLS, SRC_PAGE],
                "note": "THE ROSTER THIS PASS READ. It gives each guest's 1882 "
                        "post-office address and NOT a year of arrival, which is why "
                        "every person row here carries a null arrival year: the "
                        "addresses are where these men lived in 1882, forty-seven years "
                        "after the scene date, and are never read as 1835 residences.",
            },
        ],
        "declared_and_unresolved": [
            {
                "id": "os_q_registered_after_a_documented_death",
                "question": "%d merge(s) put a man at a Calumet Club reception whose "
                            "own resident record carries a death notice from BEFORE "
                            "that reception. The identity rules cannot see this: they "
                            "read names, and this project's resident records carry no "
                            "death dates except where Fergus's 1843 old-settler death "
                            "notices were spent onto a card."
                            % len(contradictions or []),
                "cases": contradictions or [],
                "not_resolved_because": "the likeliest reading is that the CARD is two "
                                        "men and not that the register is wrong — "
                                        "'Wolcott, Alexander' is the clearest case: the "
                                        "same card carries Fergus's death notice for Dr "
                                        "Alexander Wolcott, Indian agent, \"died Oct. "
                                        "25, 1830, aged 40\" (born about 1790) AND the "
                                        "1843 directory's \"Wolcott, Alex., surveyor "
                                        "... [died Aug. 11, 1884, a. 69]\" (born about "
                                        "1815), and the register's man gives his age as "
                                        "64 in 1879, which is the SURVEYOR's birth year "
                                        "and not the agent's. Splitting a resident "
                                        "record is an identity ruling and belongs to "
                                        "the identity master, not to a source reader: "
                                        "no merge is withdrawn here and no record is "
                                        "split.",
                "for": "T-0513 (consolidation), which holds the identity master. The "
                       "citation this pass writes onto each of these cards states the "
                       "contradiction in the note, so the card itself carries it.",
            },
            {
                "id": "os_q_1883_ordinal",
                "question": "This project already cites an 1883 old-settlers reception as "
                            "the SEVENTH annual (data/sources/"
                            "chicago_old_settlers_hugunin_1883.json, \"Old Settlers of "
                            "Chicago, Seventh Annual Reception proceedings, 1883\"), and "
                            "a Tribune report of 18 May 1883 beside it "
                            "(resident_research_tribune_mitchell_1883). But the Tribune "
                            "of 25 April 1882 calls the reception of 18 May 1882 the "
                            "FOURTH annual, which makes 1883 the fifth. One of the two "
                            "ordinals is wrong, or they count different bodies.",
                "not_resolved_because": "the evidence in hand is a transcription of the "
                                        "1882 Tribune and a citation written from a "
                                        "different document. Neither existing source "
                                        "record is altered on that.",
                "for": "whoever reads the 1883 proceedings (the Lane Family copy is "
                       "already cited) — the title page will settle it.",
            },
            {
                "id": "os_q_death_count",
                "question": "The reception report of 19 May 1882 says \"no less than "
                            "thirty-five of the 414 who are known & Chicago's old "
                            "settlers having gone to their rest during the year\", and "
                            "Vice-President Doane repeats thirty-five from the floor. "
                            "Wentworth's published list, printed on 25 April 1882 and "
                            "read here, carries %d names." % len(deaths),
                "not_resolved_because": "the list is dated three weeks before the "
                                        "reception and covers deaths \"since the 1st of "
                                        "January, 1881\" — sixteen and a half months, "
                                        "not \"during the year\". The two counts are "
                                        "answering different questions, and the page "
                                        "does not say so.",
                "for": "the consolidation pass (T-0513), which should carry both counts "
                       "rather than pick one.",
            },
            {
                "id": "os_q_hail_hall",
                "question": "\"William A. Hail\" in the death roll of 25 April 1882 and "
                            "\"William A. Hall, who was employed at Fort Dearborn as a "
                            "gunsmith\" in the report of 19 May 1882 are one man under "
                            "two spellings, on the same web page.",
                "not_resolved_because": "both spellings are carried as_read and no "
                                        "resident is merged on either. A Fort Dearborn "
                                        "gunsmith is a placeable trade and worth the "
                                        "original.",
                "for": "the Fort Dearborn trades work and T-0513.",
            },
        ],
    }


ARRIVAL_BASIS_1879 = (
    "the registry's own DATE OF ARRIVAL column, in the man's own registration of 27 May "
    "1879 — a RECOLLECTION set down forty to sixty years after the fact, not a "
    "contemporary record of his arrival. It dates the claim and does not prove it."
)

PLACES_WHY_1879 = (
    "the club's criterion is residence in Chicago before 1 January 1840 and majority by "
    "then, and the year in the DATE OF ARRIVAL column is what the man himself said in "
    "1879. A self-reported arrival year at or before 1835 is a dated recollection and "
    "not a residence on 1 July 1835: under the ratified ladder (T-0513) it corroborates "
    "and enriches, and minting waits on a contemporary source (T-0514)."
)


def people(guests: list[dict], deaths: list[dict], residents: list[dict],
           registry_1879: list[dict] | None = None) -> dict:
    rows = []
    for n, g in enumerate(registry_1879 or [], 1):
        m = match(g, residents)
        year = g["arrival_year"]
        rows.append({
            "id": "os1879r%03d" % n,
            "roll": "registry_1879_05_27",
            "as_read": g["as_read"],
            "name_as_read": g["name_as_read"],
            "normalized": g["normalized"],
            "reading": "page_image",
            "confidence": "documented",
            "source": SRC_1879,
            "locator": "Early Chicago: Reception to the Settlers of Chicago Prior to "
                       "1840, by the Calumet Club, of Chicago (Chicago, 1879), \"NAMES "
                       "OF OLD SETTLERS OF CHICAGO, REGISTERED AT THE CALUMET CLUB\", "
                       "printed page %s, entry \"%s\"; read off the page images of the "
                       "Internet Archive copy earlychicagorece00calu, whose OCR text "
                       "layer destroys this plate"
                       % (g["page"] or "84-90", g["name_as_read"]),
            "describes_date": ("the man registered on 27 May 1879 and gave %s as his "
                               "date of arrival in Chicago"
                               % ((g["arrival_as_read"] or "").rstrip(", ") or "no date")),
            "arrival_year": year,
            "arrival_as_read": g["arrival_as_read"],
            "arrival_year_basis": ARRIVAL_BASIS_1879,
            "arrival_at_or_before_1835": (year is not None and year <= 1835),
            "arrival_at_or_before_1835_is_not_a_residence": True,
            "birthplace_as_read": g["birthplace_as_read"],
            "age_1879_as_read": g["age_1879_as_read"],
            "residence_1879_as_read": g["residence_1879_as_read"],
            "trade_or_office": None,
            "places_in_1835": False,
            "places_in_1835_why": PLACES_WHY_1879,
            "residents_layer": m,
            "proposed": proposed_rung(g, m),
        })
    for n, g in enumerate(guests, 1):
        m = match(g, residents)
        rows.append({
            "id": "os1882g%03d" % n,
            "roll": "guests_present_1882_05_18",
            "as_read": g["as_read"],
            "name_as_read": g["name_as_read"],
            "normalized": g["normalized"],
            "reading": "transcription_mediated",
            "confidence": "documented",
            "source": SRC_RECEPTION,
            "locator": "Chicago Tribune, 19 May 1882, report of the Calumet Club's "
                       "fourth annual reception to the Old Settlers of Chicago, list "
                       "\"Names of Old Settlers Present, Residents and of Age Prior to "
                       "1840\", entry \"%s\"; read at chicagology.com/goldenage/"
                       "goldenage063/" % g["name_as_read"],
            "describes_date": "1882-05-18; the person's Chicago residence is placed only "
                              "'prior to 1 January 1840'",
            "arrival_year": None,
            "arrival_year_basis": "the 1882 guest roster gives no year of arrival — it "
                                  "gives an 1882 post-office address",
            "trade_or_office": None,
            "residence_1882_as_read": g["residence_1882_as_read"],
            "places_in_1835": False,
            "places_in_1835_why": "the roster's only claim about time is the club's "
                                  "criterion: resident before 1 January 1840 and of age "
                                  "by then.",
            "residents_layer": m,
            "proposed": proposed_rung(g, m),
        })
    for n, d in enumerate(deaths, 1):
        m = match(d, residents)
        rows.append({
            "id": "os1882d%03d" % n,
            "roll": "wentworth_deaths_since_1881_01_01",
            "as_read": d["as_read"],
            "name_as_read": d["name_as_read"],
            "normalized": d["normalized"],
            "reading": "transcription_mediated",
            "confidence": "documented",
            "source": SRC_DEATHS,
            "locator": "Chicago Tribune, 25 April 1882, \"THE OLD SETTLERS. Deaths "
                       "During the Year.\", John Wentworth's list of old settlers dead "
                       "since 1 January 1881, entry \"%s\"; read at chicagology.com/"
                       "goldenage/goldenage063/" % d["as_read"],
            "describes_date": "died %s; Chicago residence placed only 'prior to 1 "
                              "January 1840'" % d["died_as_read"],
            "arrival_year": None,
            "arrival_year_basis": "the death roll gives a date of death and no year of "
                                  "arrival",
            "died_as_read": d["died_as_read"],
            "trade_or_office": None,
            "places_in_1835": False,
            "places_in_1835_why": "a death in 1881 or 1882 says nothing about 1835 "
                                  "beyond the club's pre-1840 criterion.",
            "residents_layer": m,
            "proposed": proposed_rung(d, m),
        })
    counts = {"rows": len(rows), "registry_1879": len(registry_1879 or []),
              "guests": len(guests), "deaths": len(deaths),
              "dated_by_the_1879_registry": sum(
                  1 for r in rows if r.get("arrival_year") is not None),
              "arrival_at_or_before_1835": sum(
                  1 for r in rows if r.get("arrival_at_or_before_1835"))}
    for rule in RULES:
        counts[rule] = sum(1 for r in rows if r["residents_layer"]["rule"] == rule)
    for outcome in ("merged", "probable", "candidate", "refused", "unmatched"):
        counts[outcome] = sum(1 for r in rows
                              if r["residents_layer"]["outcome"] == outcome)
    return {
        "schema": SCHEMA,
        "domain": "old_settlers",
        "generated_by": "tools/old_settlers.py --build",
        "what": "THREE rolls. The register of the Calumet Club's FIRST Old Settlers' "
                "reception, 27 May 1879, read off the printed plate of Early Chicago "
                "(pages 84-90) — the one roll in the series that carries each man's own "
                "year of arrival, birthplace and age. And the two rolls chicagology 063 "
                "reprints: the 118 guests "
                "present at the Calumet Club's fourth annual Old Settlers' reception of "
                "18 May 1882, and John Wentworth's roll of settlers dead since 1 "
                "January 1881 — read as it is printed, matched against the residents "
                "layer under declared rules, and carrying the ladder rung this source "
                "PROPOSES and does not apply.",
        "scene_relation": "later_evidence_only",
        # WHERE THIS FILE'S NAMED UNITS LIVE (T-0678). The registry and the spend measure
        # count an entry of `records` or `claims`; this file calls its array `people`,
        # because a roll of settlers is people, and both instruments read 327 rolls as
        # zero for as long as nobody said so. One declared key is cheaper than renaming
        # an array every consumer already reads, and it is checked rather than trusted:
        # research_domains.py --check names the array and fails if it is not there.
        "units_in": "people",
        "identity_rules": RULES,
        "spelling_bridges": SPELLING_BRIDGES,
        "counts": counts,
        "people": rows,
    }


def crosswalk(doc: dict) -> dict:
    merges, probable, refusals = [], [], []
    for r in doc["people"]:
        m = r["residents_layer"]
        # T-0598: the source each row was read out of, carried through from
        # people.json rather than restated. This domain reads two rolls with two
        # different source records, so the statement belongs on the ENTRY: a
        # file-level one would be true of the file and false of every row in it.
        source_id = r.get("source")
        if m["outcome"] == "merged":
            merges.append({"id": r["id"], "as_read": r["name_as_read"],
                           "source_id": source_id,
                           "person_id": m["person_id"], "household_id": m["household_id"],
                           "resident_name": m["resident_name"], "rule": m["rule"],
                           "evidence": m["why"]})
        elif m["outcome"] == "probable":
            probable.append({"id": r["id"], "as_read": r["name_as_read"],
                             "source_id": source_id,
                             "probable_person_id": m["probable_person_id"],
                             "household_id": m["household_id"],
                             "resident_name": m["resident_name"], "rule": m["rule"],
                             "why": m["why"]})
        else:
            refusals.append({"id": r["id"], "as_read": r["name_as_read"],
                             "source_id": source_id,
                             "rule": m["rule"], "outcome": m["outcome"], "why": m["why"],
                             **({"candidates": m["candidates"]} if m.get("candidates") else {})})
    return {
        "schema": SCHEMA,
        "domain": "old_settlers",
        "generated_by": "tools/old_settlers.py --build",
        "what": "Which of these names are people the residents layer already holds, "
                "which are probably them and are NOT written on a record, and which are "
                "refused. A refusal is as much a finding as a merge: it is the reason "
                "the next run does not have to make the judgement again.",
        "rules": RULES,
        "only_merges_are_written": "The enrichment pass writes a citation onto a "
                                   "resident record for an OS1 or OS2A merge and for "
                                   "nothing else. Probable, candidate, refused and "
                                   "unmatched rows touch no record.",
        "merges": merges,
        "probable": probable,
        "refusals": refusals,
        "counts": {"merges": len(merges), "probable": len(probable),
                   "refusals": len(refusals)},
    }


# --- the citation, written onto the resident records the merges name --------------

MARKER = "OLD SETTLERS, 1882"
MARKER_1879 = "OLD SETTLERS, 1879"


def marker(row: dict) -> str:
    return MARKER_1879 if row["roll"].startswith("registry_1879") else MARKER

LADDER_LIMIT = (
    "Under the ratified ladder (T-0513) a later recollection corroborates, enriches and "
    "dates and cannot lift a rung by itself, so this record's GRADE IS UNCHANGED by it: "
    "T-0513 consolidates the identity and T-0515 regrades."
)


def contradiction_clause(row: dict) -> str:
    """Where this card already carries a death notice the register contradicts."""
    m = row["residents_layer"]
    stamped = m.get("record_death_notice_date")
    if not stamped:
        return ""
    y = DEATH_YEAR.search(stamped)
    if not y or int(y.group(1)) >= 1879:
        return ""
    return (" AND THIS CARD CONTRADICTS ITSELF ON THE POINT: it already carries a death "
            "notice, \u201c%s\u201d, dated %s — before the register was signed. A man "
            "dead by then did not sign it, so either the register's entry is another "
            "man of the same name or this card is two men. Nothing is withdrawn and no "
            "record is split here; the case is filed in "
            "data/research/old_settlers/receptions.json under "
            "os_q_registered_after_a_documented_death for the identity master (T-0513)."
            % (m.get("record_death_notice_as_read"), stamped))


def citation_note(row: dict) -> str:
    """What goes on the resident record, and what it is careful not to say."""
    m = row["residents_layer"]
    rule = "%s — %s" % (m["rule"], m["why"])
    if row["roll"].startswith("registry_1879"):
        return (
            "%s — A DATE THIS MAN GAVE FOR HIMSELF, AND STILL NOT A FACT ABOUT 1835. "
            "The Calumet Club's FIRST reception to the settlers of Chicago prior to "
            "1840, 27 May 1879, printed its register in the proceedings (Early Chicago, "
            "Chicago, 1879, pages 84-90), and this man's entry reads \u201c%s\u201d — "
            "name, his own date of arrival, his birthplace, his age and his 1879 "
            "post-office address, in the register's five columns. The date of arrival is "
            "HIS RECOLLECTION, set down forty to sixty years after the event; the "
            "address is where he lived in 1879 and is never read as an 1835 residence. "
            "%s%s Identity by rule %s (data/research/old_settlers/crosswalk.json)."
            % (MARKER_1879, row["as_read"], LADDER_LIMIT, contradiction_clause(row), rule))
    if row["roll"].startswith("guests"):
        return (
            "%s — CORROBORATION, NOT A NEW FACT ABOUT 1835. The Calumet Club's fourth "
            "annual reception to the settlers of Chicago prior to 1840, held 18 May "
            "1882, printed this man among the guests present as \u201c%s\u201d (Chicago "
            "Tribune, 19 May 1882). The club's criterion was residence in Chicago before "
            "1 January 1840 and majority by then: the roster therefore corroborates a "
            "pre-1840 Chicago residence and says he was alive in 1882. It gives NO year "
            "of arrival, and the address it prints is where he lived in 1882, "
            "forty-seven years after the scene date \u2014 it is not an 1835 residence and "
            "is not read as one. %s Identity by rule %s "
            "(data/research/old_settlers/crosswalk.json)."
            % (MARKER, row["as_read"], LADDER_LIMIT, rule))
    return (
        "%s \u2014 A DATE OF DEATH, AND NOTHING ABOUT 1835. John Wentworth's roll of old "
        "settlers who had died since 1 January 1881, kept for the Calumet Club and "
        "printed in the Chicago Tribune of 25 April 1882, carries \u201c%s\u201d. That "
        "corroborates a Chicago residence before 1840 and fixes the END of this life, "
        "which this record did not carry; it is not an arrival and it places nobody in "
        "the town on 1 July 1835. %s Identity by rule %s "
        "(data/research/old_settlers/crosswalk.json)."
        % (MARKER, row["as_read"], LADDER_LIMIT, rule))


def citation_source(row: dict) -> str:
    if row["roll"].startswith("registry_1879"):
        return SRC_1879
    return SRC_RECEPTION if row["roll"].startswith("guests") else SRC_DEATHS


def apply_citations(quiet: bool = False) -> int:
    """Write the citation onto the resident records the OS1/OS2A merges name."""
    docs = build_docs()
    touched = 0
    for row in docs["people.json"]["people"]:
        m = row["residents_layer"]
        if m["outcome"] != "merged":
            continue
        path = RESIDENTS / "households" / ("%s.json" % m["household_id"])
        h = load(path)
        for person in h["persons"]:
            if person.get("id") != m["person_id"]:
                continue
            sid = citation_source(row)
            changed = False
            if sid not in (person.get("sources") or []):
                person["sources"] = (person.get("sources") or []) + [sid]
                changed = True
            note = (person.get("note") or "").strip()
            if marker(row) not in note:
                person["note"] = (note + " " + citation_note(row)).strip()
                changed = True
            if changed:
                touched += 1
                dump(path, h)
    if not quiet:
        print("old settlers: citation written onto %d resident record(s)" % touched)
    return touched


def citation_gaps(docs: dict) -> list:
    """Every merge has to be ON the record it names, or the merge is only a file."""
    bad = []
    for row in docs["people.json"]["people"]:
        m = row["residents_layer"]
        if m["outcome"] != "merged":
            continue
        path = RESIDENTS / "households" / ("%s.json" % m["household_id"])
        if not path.exists():
            bad.append("%s: household %s no longer exists" % (row["id"], m["household_id"]))
            continue
        person = next((p for p in load(path)["persons"]
                       if p.get("id") == m["person_id"]), None)
        if person is None:
            bad.append("%s: person %s is no longer in %s"
                       % (row["id"], m["person_id"], m["household_id"]))
            continue
        if citation_source(row) not in (person.get("sources") or []):
            bad.append("%s merges into %s and that record does not cite '%s' — run "
                       "--apply-citations" % (row["id"], m["person_id"], citation_source(row)))
        if marker(row) not in (person.get("note") or ""):
            bad.append("%s merges into %s and that record's note does not say what the "
                       "old-settlers roll is worth — run --apply-citations"
                       % (row["id"], m["person_id"]))
    return bad


# --- build / check ------------------------------------------------------------------

OUTPUTS = ("receptions.json", "people.json", "crosswalk.json")


def build_docs() -> dict:
    lines = text_lines()
    guests = read_guest_roster(lines)
    deaths = read_death_roll(lines)
    reg_1879, tables_1879 = read_1879_registry(text_lines_1879())
    reconciliation = reconcile_1879(reg_1879, tables_1879)
    res = resident_index()
    ppl = people(guests, deaths, res, reg_1879)
    contradictions = registered_after_a_documented_death(ppl["people"])
    return {
        "receptions.json": receptions(guests, deaths, reg_1879, reconciliation,
                                      contradictions),
        "people.json": ppl,
        "crosswalk.json": crosswalk(ppl),
    }


def build(quiet: bool = False) -> None:
    docs = build_docs()
    for name, doc in docs.items():
        dump(DOMAIN / name, doc)
    if not quiet:
        c = docs["people.json"]["counts"]
        print("old settlers: %d name(s) read (%d on the 1879 register, %d guests, %d "
              "deaths); %d merged into the residents layer"
              % (c["rows"], c["registry_1879"], c["guests"], c["deaths"], c["merged"]))


def check(quiet: bool = False, domain: Path | None = None) -> list:
    global DOMAIN, TEXT, TEXT_1879
    if domain is not None:
        DOMAIN = domain
        TEXT = domain / "text" / TEXT.name
        TEXT_1879 = domain / "text" / TEXT_1879.name
    bad = []
    for t in (TEXT, TEXT_1879):
        if not t.exists():
            return ["data/research/old_settlers/text/%s is missing" % t.name]
    docs = build_docs()
    for name, want in docs.items():
        path = DOMAIN / name
        if not path.exists():
            bad.append("data/research/old_settlers/%s is missing — run --build" % name)
            continue
        if load(path) != want:
            bad.append("data/research/old_settlers/%s does not match what the committed "
                       "text rebuilds; regenerate it with --build" % name)

    # every quote this domain rests on has to be IN the committed transcription
    blob = "\n".join(text_lines() + text_lines_1879())
    for r in docs["people.json"]["people"]:
        if r["as_read"] not in blob:
            bad.append("%s: %r is not in the committed transcription" % (r["id"], r["as_read"]))
    claims_path = DOMAIN / "claims.json"
    if claims_path.exists():
        for c in load(claims_path).get("claims") or []:
            if c.get("quote") and c["quote"] not in blob:
                bad.append("claim %s: its quote is not in the committed transcription — "
                           "a quote nobody can rebuild is not a quote" % c.get("id"))

    if domain is None:
        bad += citation_gaps(docs)

    # every source id named anywhere in this domain has to resolve
    if SOURCES.exists():
        known = {p.stem for p in SOURCES.glob("*.json")}
        named = set()
        for name in OUTPUTS + ("claims.json",):
            path = DOMAIN / name
            if not path.exists():
                continue
            for sid in re.findall(r'"(?:source|sources)": (?:"([a-z0-9_]+)"|\[([^\]]*)\])',
                                  path.read_text(encoding="utf-8")):
                if sid[0]:
                    named.add(sid[0])
                named.update(re.findall(r'"([a-z0-9_]+)"', sid[1]))
        for sid in sorted(named - known):
            bad.append("source '%s' is named under data/research/old_settlers/ and does "
                       "not resolve in data/sources/" % sid)

    if not quiet:
        for b in bad:
            print("  FAIL  " + b)
        c = docs["people.json"]["counts"]
        print("  %d name(s) read; %d merged, %d refused or unmatched"
              % (c["rows"], c["merged"], c["rows"] - c["merged"]))
    return bad


def self_test() -> int:
    """The gate's own assertions, fired against deliberate damage in a copy."""
    import shutil
    import tempfile
    failures = []

    def run(label, mutate, expect):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "old_settlers"
            shutil.copytree(DOMAIN, copy)
            mutate(copy)
            saved = (DOMAIN, TEXT, TEXT_1879)
            try:
                bad = check(quiet=True, domain=copy)
            finally:
                (globals()["DOMAIN"], globals()["TEXT"],
                 globals()["TEXT_1879"]) = saved
            hit = any(expect in b for b in bad)
            print("  %s  %s" % ("ok  " if hit else "MISS", label))
            if not hit:
                failures.append((label, bad))

    def edit(path, fn):
        d = load(path)
        fn(d)
        dump(path, d)

    run("a hand-edited people.json is caught",
        lambda c: edit(c / "people.json",
                       lambda d: d["people"][0].update({"places_in_1835": True})),
        "people.json does not match")
    run("a hand-edited receptions.json is caught",
        lambda c: edit(c / "receptions.json",
                       lambda d: d["receptions"][0].update({"roster_read": False})),
        "receptions.json does not match")
    run("a hand-edited 1879 registry cell is caught",
        lambda c: (c / "text" / TEXT_1879.name).write_text(
            (c / "text" / TEXT_1879.name).read_text(encoding="utf-8")
            .replace("Hubbard, Gurdon S. | 1818, Oct. 1,",
                     "Hubbard, Gurdon S. | 1835, Oct. 1,"), encoding="utf-8"),
        "people.json does not match")
    run("a deleted 1879 transcription is caught",
        lambda c: (c / "text" / TEXT_1879.name).unlink(),
        "%s is missing" % TEXT_1879.name)
    run("a hand-edited crosswalk.json is caught",
        lambda c: edit(c / "crosswalk.json",
                       lambda d: d["merges"].append({"id": "invented"})),
        "crosswalk.json does not match")
    run("a claim quoting something the transcription does not carry is caught",
        lambda c: edit(c / "claims.json",
                       lambda d: d["claims"].append(
                           {"id": "invented", "quote": "he was here on 1 July 1835"})),
        "not in the committed transcription")
    run("a source id that does not resolve is caught",
        lambda c: edit(c / "claims.json",
                       lambda d: d["claims"][0].update({"source": "no_such_source"})),
        "does not resolve in data/sources/")
    run("a deleted output is caught",
        lambda c: (c / "people.json").unlink(),
        "people.json is missing")
    if failures:
        print("OLD SETTLERS SELF-TEST FAIL — %d assertion(s) did not fire" % len(failures))
        return 1
    print("OK: the old-settlers gate's assertions still fire")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply-citations", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.build:
        build()
        return 0
    if a.apply_citations:
        apply_citations()
        return 0
    bad = check()
    if bad:
        print("OLD SETTLERS FAIL — %d problem(s)" % len(bad))
        return 1
    print("OK: the old-settlers rolls rebuild from the committed transcription")
    return 0


if __name__ == "__main__":
    sys.exit(main())
