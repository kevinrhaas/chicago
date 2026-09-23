#!/usr/bin/env python3
"""The 134 Black Hawk War veterans who enrolled AT CHICAGO in 1832 (T-0572).

    tools/read_blackhawk_war.py --build       write the records, the crosswalk, the pass
    tools/read_blackhawk_war.py --check       the gate
    tools/read_blackhawk_war.py --self-test   the gate's assertions still fire when broken

WHAT IS READ. The Illinois State Archives database that indexes volume 1 of Ellen M.
Whitney, *The Black Hawk War 1831-1832*, as republished by the Genealogy Trails
Transcription Team. 134 table rows, header excluded, each giving NAME, Rank, COMPANY,
PLACE OF ENROLLMENT and REGIMENT or BRIGADE. Nobody in this project has seen Whitney's
volume; the reading is `transcription_mediated` on every record, twice over.

THE TABLE IS READ OUT OF THE CACHED HTML, NOT THE FLATTENED TEXT, and that is the whole
reason this tool exists rather than a hand transcription. The text extraction drops an
EMPTY cell, so in `text/blackhawkwar.txt` a row reads

    AS KE WITT / INDIAN / CHICAGO / ODD

and nothing in it says whether `INDIAN` stands in the Rank column or the COMPANY column.
The cached page settles it: the Rank cell of that row is `&nbsp;` and `INDIAN` is the
COMPANY. Ninety-four of the 134 rows are that shape, so reading the text alone would have
mis-filed 94 of 134 cells or left them unplaced. `html/blackhawkwar.htm` was cached for
this ticket on 2026-09-03 beside the text that was already there.

THE TRAP THE TICKET NAMED, HELD AS AN ASSERTION. Names are printed in several forms and
NOT all carry a surname comma — `AS KE WITT` is a row, `WAB-ME-MIC` is a row. A reader
who filters on the comma silently drops the French and Potawatomi names, which are the
ones this reconstruction is least able to lose. So the parse anchors on the TABLE ROW and
never on the comma, and `--check` fails if the count is not exactly 134 or if the 83
comma-less names stop being carried.

PRESENCE IN 1832 IS NOT RESIDENCE IN 1835. Every one of these men demonstrably stood in
this town in 1832, three years before the scene, and that is all this source says. Under
the grading ladder the owner ratified on 2026-09-03 an enrollment alone never makes an
1835 resident: it corroborates, it enriches, and above all it DATES. Every record carries
`describes_date: "1832"`, the crosswalk proposes no merge, and `crosswalk.json` records
this pass with `merges: 0` and says why.

THE CROSSWALK RULE, written out so it reads back without the code:
  SURNAME must agree after folding (case, punctuation), AND the forenames must agree
  initial for initial in one direction or the other — the index prints `WILLIAM H` where
  the poll book prints `W. H.` and neither abbreviation is privileged. A surname-only
  agreement is a REFUSAL, however good it looks: these lists are full of families and a
  bare surname separates none of them. A name with no surname at all cannot enter a
  surname crosswalk, so it is reported `no_surname` — carried, counted, and never
  quietly dropped. Ambiguity is checked BOTH WAYS: one index row reaching two readings
  on the lists is a candidate, and so are two index rows reaching the same entry
  (`HARMON, ISAAC` and `HARMON, ISAAC D` both reach `Harmon, Isaac` on the 1833 tax
  list, and calling either a clean corroboration would hand the next pass two men and
  one voter without saying so).
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GT = ROOT / "data" / "research" / "genealogytrails"
CIVIC = ROOT / "data" / "research" / "civic"

HTML_CACHE = GT / "html" / "blackhawkwar.htm"
TEXT_CACHE = GT / "text" / "blackhawkwar.txt"
TEXT = CIVIC / "text" / "blackhawk_war_1832_chicago.txt"
RECORDS = CIVIC / "records" / "blackhawk_war_1832_chicago.json"
CROSSWALK = CIVIC / "blackhawk_war_crosswalk.json"
IDENTITY = CIVIC / "crosswalk.json"
COVERAGE = CIVIC / "coverage.json"
VOTERS = CIVIC / "records" / "voter_lists_1833_1835.json"

TICKET = "T-0572"
LIST_ID = "blackhawk_war_1832_chicago"
SOURCE_ID = "blackhawk_war_chicago_enrollments_isa"
PUBLICATION_SOURCE_ID = "chicago_voter_lists_1833_1835_irad"  # the same transcribers
VOTER_SOURCE_ID = "chicago_voter_lists_1833_1835_irad"

# The header row, asserted verbatim. A re-cached page that renumbers or renames a column
# fails here rather than silently re-filing 670 cells.
HEADER = ["NAME", "Rank", "COMPANY", "PLACE OF ENROLLMENT", "REGIMENT or BRIGADE"]
EXPECTED_ROWS = 134
EXPECTED_NO_COMMA = 83

TITLES = {"lt.", "lt", "col.", "col", "maj.", "maj", "major", "capt.", "capt",
          "dr.", "dr", "rev.", "rev", "mr.", "mr", "gen.", "gen", "hon.", "hon"}
SUFFIXES = {"jr.", "jr", "sr.", "sr", "ii", "iii", "2nd"}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, doc) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ---------------------------------------------------------------- the table

def table_rows(root: Path = ROOT):
    """Every <TR> of the cached page, as a list of cell strings with blanks kept."""
    path = root / HTML_CACHE.relative_to(ROOT)
    if not path.exists():
        sys.exit("the cached page is missing: %s — re-cache it before reading"
                 % path.relative_to(root))
    doc = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for tr in re.findall(r"<TR>(.*?)</TR>", doc, re.S | re.I):
        cells = []
        for td in re.finditer(r"<TD[^>]*>(.*?)</TD>", tr, re.S | re.I):
            text = re.sub(r"<[^>]+>", " ", td.group(1))
            text = htmllib.unescape(text)
            cells.append(re.sub(r"\s+", " ", text).strip())
        out.append(cells)
    return out


def text_lines(root: Path = ROOT):
    """The committed civic copy of the flattened page, asserted byte-identical to the
    genealogytrails cache it was taken from. The cache is senior."""
    text = root / TEXT.relative_to(ROOT)
    cache = root / TEXT_CACHE.relative_to(ROOT)
    if not text.exists():
        sys.exit("the committed domain text is missing: %s" % text.relative_to(root))
    if cache.exists() and text.read_bytes() != cache.read_bytes():
        sys.exit("data/research/civic/text/blackhawk_war_1832_chicago.txt is not "
                 "byte-identical to the genealogytrails cache it was taken from — "
                 "the cache is senior")
    return text.read_text(encoding="utf-8").splitlines()


def split_name(as_read: str):
    """`ADAMS, WILLIAM H` -> ('ADAMS', 'WILLIAM H'). `AS KE WITT` has no surname at all
    and is returned as such: the comma is what the index uses to mark one, and 83 of the
    134 names do not carry it."""
    if "," in as_read:
        surname, rest = as_read.split(",", 1)
        return surname.strip(), rest.strip()
    return "", as_read.strip()


def tokens(forenames: str):
    out = []
    for raw in re.split(r"\s+", (forenames or "").strip()):
        t = raw.strip()
        if not t or t.lower() in TITLES or t.lower() in SUFFIXES:
            continue
        letters = re.sub(r"[^A-Za-z]", "", t)
        if letters:
            out.append(letters.lower())
    return out


def reading_order(surname: str, forenames: str) -> str:
    """How this project spells the row. NOT a repair: the index sets every name in
    capitals and that is its typography, not a spelling, so the letters are carried
    through exactly and only the printed inversion `SURNAME, FORENAMES` is undone.
    Recasing and expanding an abbreviation are readings, and they belong to the identity
    layer rather than to the transcription."""
    if not surname:
        return forenames.strip()
    return ("%s %s" % (forenames.strip(), surname.strip())).strip()


def extract(root: Path = ROOT):
    rows = table_rows(root)
    body = []
    header_seen = False
    for cells in rows:
        if len(cells) != 5:
            continue
        if not header_seen and [c for c in cells] == HEADER:
            header_seen = True
            continue
        body.append(cells)
    if not header_seen:
        sys.exit("the cached page carries no header row reading %s — the columns this "
                 "tool files cells into are not the columns on the page" % HEADER)
    if len(body) != EXPECTED_ROWS:
        sys.exit("the cached page carries %d data rows, not the %d this reading was "
                 "written against and the inventory counted"
                 % (len(body), EXPECTED_ROWS))

    lines = text_lines(root)
    # Each row's NAME cell, found in the flattened text IN ORDER, so a record's locator
    # points at a line a person can go and look at. Order matters: `CAU O SETT` is
    # printed twice and the second occurrence is the second record.
    cursor = 0
    records = []
    for n, cells in enumerate(body, 1):
        name, rank, company, place, regiment = cells
        if place != "CHICAGO":
            sys.exit("row %d enrolls at %r, not CHICAGO — this list is the Chicago "
                     "enrollments and nothing else belongs in it" % (n, place))
        line_no = None
        for i in range(cursor, len(lines)):
            if lines[i].strip() == name:
                line_no, cursor = i + 1, i + 1
                break
        if line_no is None:
            sys.exit("row %d names %r and the committed text does not carry it at or "
                     "after line %d — the text and the page disagree" % (n, name, cursor + 1))
        surname, forenames = split_name(name)
        cell_note = []
        if not rank:
            cell_note.append("the Rank cell is empty on the page")
        if not regiment:
            cell_note.append("the REGIMENT or BRIGADE cell is empty on the page")
        records.append({
            "id": "blackhawk_1832_%03d" % n,
            "as_read": name,
            "normalized": reading_order(surname, forenames),
            "locator": {"list": LIST_ID, "line": line_no,
                        "text_file": "blackhawk_war_1832_chicago.txt",
                        "html_file": "genealogytrails/html/blackhawkwar.htm",
                        "entry": n},
            "reading": "transcription_mediated",
            "confidence": "documented",
            "describes_date": "1832",
            "cells": {
                "name": name,
                "rank": rank or None,
                "company": company or None,
                "place_of_enrollment": place,
                "regiment_or_brigade": regiment or None,
            },
            "notes": "Black Hawk War veterans enrolled at Chicago, row %d of %d. %s. "
                     "Enrollment at Chicago in 1832 places this man in the town three "
                     "years before the scene; it is not residence in 1835.%s"
                     % (n, EXPECTED_ROWS,
                        ("Surname %r; forenames as printed %r" % (surname, forenames))
                        if surname else
                        ("The index prints this name without a surname comma (%r), so it "
                         "has no surname to compare and none is invented" % name),
                        (" " + "; ".join(cell_note).capitalize() + ".") if cell_note else ""),
            "surname": surname,
            "forenames": forenames,
        })

    no_comma = sum(1 for r in records if not r["surname"])
    if no_comma != EXPECTED_NO_COMMA:
        sys.exit("%d of the %d names carry no surname comma, not the %d counted when "
                 "this reading was written — a comma filter is exactly what this ticket "
                 "forbids, so the change is reported rather than absorbed"
                 % (no_comma, len(records), EXPECTED_NO_COMMA))
    return records


# ---------------------------------------------------------------- the crosswalk

def fold(surname: str) -> str:
    return re.sub(r"[^a-z]", "", (surname or "").lower())


def agrees(a, b) -> bool:
    """Do two forename readings agree initial for initial, allowing the shorter to be a
    prefix of the longer? Neither direction is privileged: the index prints `WILLIAM H`
    where the poll book prints `W. H.`, and both are the same man abbreviated by
    different hands. A reading with no forename at all never reaches here."""
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


def voter_entries(root: Path = ROOT):
    path = root / VOTERS.relative_to(ROOT)
    if not path.exists():
        sys.exit("the voter lists are not read yet (%s) — the crosswalk target is "
                 "missing" % path.relative_to(root))
    out = []
    for rec in load(path).get("records") or []:
        as_read = rec.get("as_read") or ""
        surname, forenames = (as_read.split(",", 1) + [""])[:2] if "," in as_read \
            else (as_read, "")
        out.append({
            "record_id": rec.get("id"),
            "list": (rec.get("locator") or {}).get("list"),
            "line": (rec.get("locator") or {}).get("line"),
            "as_read": as_read,
            "normalized": rec.get("normalized"),
            "surname_key": fold(surname),
            "forename_keys": tokens(forenames),
        })
    return out


def crosswalk(records, voters):
    by_surname = {}
    for v in voters:
        by_surname.setdefault(v["surname_key"], []).append(v)

    entries, refusals = [], []
    for rec in records:
        fore = tokens(rec["forenames"]) if rec["surname"] else []
        out = {
            "record_id": rec["id"],
            "as_read": rec["as_read"],
            "normalized": rec["normalized"],
            "company": rec["cells"]["company"],
            "rank": rec["cells"]["rank"],
            "outcome": None,
            "voter_entries": [],
            "rule": None,
        }
        if not rec["surname"]:
            out["outcome"] = "no_surname"
            out["rule"] = ("The index prints %r without a surname comma, and the poll "
                           "and tax lists are indexed by surname: there is nothing to "
                           "compare, so the row is carried and counted and no match is "
                           "attempted. This is the trap the ticket named — 83 of the 134 "
                           "names are of this form and a comma filter would drop every "
                           "one of them." % rec["as_read"])
            entries.append(out)
            continue

        pool = by_surname.get(fold(rec["surname"]), [])
        if not pool:
            out["outcome"] = "unmatched"
            out["rule"] = ("No entry on any of the four lists of 1833-1835 carries the "
                           "surname %r." % rec["surname"])
            entries.append(out)
            continue

        if not fore:
            out["outcome"] = "unmatched"
            out["rule"] = ("The index prints the surname %r with no forename, and a bare "
                           "surname separates no member of a family; refused although "
                           "%d entr%s of the surname stand on the lists."
                           % (rec["surname"], len(pool), "y" if len(pool) == 1 else "ies"))
            entries.append(out)
            continue

        agree = [v for v in pool if agrees(fore, v["forename_keys"])]
        if agree:
            spellings = sorted({v["normalized"] for v in agree})
            out["voter_entries"] = [
                {"record_id": v["record_id"], "list": v["list"], "line": v["line"],
                 "as_read": v["as_read"], "normalized": v["normalized"]} for v in agree]
            if len(spellings) == 1:
                out["outcome"] = "corroborated"
                thin = (" The index prints a single bare initial here, which is the "
                        "weakest agreement this rule accepts." if len(fore) == 1
                        and len(fore[0]) == 1 else "")
                out["rule"] = ("One reading on the lists agrees with the index initial "
                               "for initial: %r against %r, on %d entr%s. Corroboration "
                               "only — the man enrolled at Chicago in 1832 and voted or "
                               "was taxed in 1833-1835, and this file asserts no "
                               "identity between the two records.%s"
                               % (rec["normalized"], spellings[0], len(agree),
                                  "y" if len(agree) == 1 else "ies", thin))
            else:
                out["outcome"] = "ambiguous"
                out["rule"] = ("%d different readings of the surname %r agree with the "
                               "index initial for initial (%s) and nothing printed in "
                               "either row separates them; an ambiguous agreement is a "
                               "candidate, never a merge."
                               % (len(spellings), rec["surname"], ", ".join(spellings)))
            entries.append(out)
            continue

        out["outcome"] = "unmatched"
        rival = pool[0]
        out["rule"] = ("The surname %r stands on the lists (%d entr%s) and no forename "
                       "reading agrees with the index's %r."
                       % (rec["surname"], len(pool), "y" if len(pool) == 1 else "ies",
                          rec["forenames"]))
        refusals.append({
            "pass": TICKET,
            "a": rec["normalized"],
            "b": rival["normalized"],
            "rule": "The surname agrees and the forenames do not: %r against %r. A "
                    "surname match is a clue, not an identity, and an 1832 enrollment "
                    "would not make one in 1835 even if it were."
                    % (rec["normalized"], rival["normalized"]),
            "evidence": [
                {"source_id": SOURCE_ID,
                 "locator": "%s entry %s" % (LIST_ID, rec["id"].rsplit("_", 1)[1])},
                {"source_id": VOTER_SOURCE_ID,
                 "locator": "%s line %s" % (rival["list"], rival["line"])},
            ],
        })
        entries.append(out)

    # CONTESTED IN THE OTHER DIRECTION. The rule above asks whether one index row
    # reaches more than one reading on the lists; it does not ask whether more than one
    # index row reaches the SAME entry. `HARMON, ISAAC` and `HARMON, ISAAC D` both agree
    # with `Harmon, Isaac` on the 1833 tax list, and reporting each as a clean
    # corroboration would hand the next pass two men and one voter without saying so.
    # Two rows contesting one entry is an ambiguity whichever way it is read.
    reached = {}
    for e in entries:
        for v in e["voter_entries"]:
            reached.setdefault(v["record_id"], []).append(e)
    for record_id, claimants in reached.items():
        if len(claimants) < 2:
            continue
        names = sorted({c["as_read"] for c in claimants})
        if len(names) < 2:
            continue
        for e in claimants:
            if e["outcome"] != "corroborated":
                continue
            e["outcome"] = "ambiguous"
            e["rule"] = ("%s More than one row of the index reaches the same entry "
                         "(%s), so the agreement does not identify a man in either "
                         "direction and is filed as a candidate."
                         % (e["rule"], ", ".join("%r" % n for n in names)))
    return entries, refusals


# ---------------------------------------------------------------- build / check

def build(root: Path = ROOT, write: bool = True):
    records = extract(root)
    voters = voter_entries(root)
    entries, refusals = crosswalk(records, voters)

    counts = {
        "rows": len(records),
        "with_surname_comma": sum(1 for r in records if r["surname"]),
        "without_surname_comma": sum(1 for r in records if not r["surname"]),
        "by_company": {},
        "by_rank": {},
    }
    for r in records:
        c = r["cells"]["company"] or "(blank)"
        k = r["cells"]["rank"] or "(blank)"
        counts["by_company"][c] = counts["by_company"].get(c, 0) + 1
        counts["by_rank"][k] = counts["by_rank"].get(k, 0) + 1

    records_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_blackhawk_war.py --build out of the cached page "
                "data/research/genealogytrails/html/blackhawkwar.htm, with every "
                "record's locator naming the line of "
                "data/research/civic/text/blackhawk_war_1832_chicago.txt it stands on. "
                "Hand-edit and --check says so. The reading is twice mediated — the "
                "Illinois State Archives indexed Whitney's volume, and the Genealogy "
                "Trails team transcribed the index — and nobody here has seen the book.",
        "generated_by": "tools/read_blackhawk_war.py --build",
        "source_id": SOURCE_ID,
        "describes_date": "1832",
        "list": {
            "id": LIST_ID,
            "title": "Black Hawk War veterans enrolled at Chicago, 1832",
            "date": "1832",
            "date_confidence": "documented",
            "entries": len(records),
        },
        "the_ladder": "An 1832 enrollment is EARLIER evidence and never an 1835 "
                      "residence on its own: it places the man in this town in 1832, "
                      "which is why it dates and corroborates rather than mints.",
        "counts": counts,
        "records": [{k: v for k, v in r.items() if k not in ("surname", "forenames")}
                    for r in records],
    }

    crosswalk_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_blackhawk_war.py --build. A PROPOSAL, not a "
                "decision: every one of the 134 enrollments set beside the 1833-1835 "
                "poll and tax lists under the rule at the head of that file. Nothing "
                "here merges anybody, and nothing here regrades a resident.",
        "generated_by": "tools/read_blackhawk_war.py --build",
        "ticket": TICKET,
        "source_id": SOURCE_ID,
        "crosswalk_target": "data/research/civic/records/voter_lists_1833_1835.json",
        "outcomes": {
            "corroborated": "The surname agrees and one reading of the forenames agrees "
                            "initial for initial. The same NAME stands on both; whether "
                            "it is the same MAN is a judgement this pass does not make.",
            "ambiguous": "Contested in one direction or the other: either more than "
                         "one distinct reading on the lists agrees with the index row, "
                         "or more than one index row agrees with the same entry. A "
                         "candidate, never a merge.",
            "unmatched": "Either no entry carries the surname, or one does and no "
                         "forename reading agrees. Refusals of the second kind are "
                         "written into crosswalk.json.",
            "no_surname": "The index prints the name without a surname comma — the "
                          "French and Potawatomi forms. Carried and counted; a "
                          "surname crosswalk cannot reach it.",
        },
        "counts": {
            "entries": len(entries),
            "corroborated": sum(1 for e in entries if e["outcome"] == "corroborated"),
            "ambiguous": sum(1 for e in entries if e["outcome"] == "ambiguous"),
            "unmatched": sum(1 for e in entries if e["outcome"] == "unmatched"),
            "no_surname": sum(1 for e in entries if e["outcome"] == "no_surname"),
            "refusals": len(refusals),
        },
        "entries": entries,
    }

    identity_path = root / IDENTITY.relative_to(ROOT)
    identity = load(identity_path) if identity_path.exists() else {
        "schema": 1, "domain": "civic", "passes": [], "merges": [], "refusals": []}
    identity["passes"] = [x for x in identity.get("passes") or []
                          if x.get("ticket") != TICKET] + [{
        "ticket": TICKET,
        "what": "The 134 Black Hawk War veterans who enrolled at Chicago in 1832, every "
                "row set beside the four voter and tax lists of 1833-1835 by "
                "tools/read_blackhawk_war.py under the rule at the head of that file.",
        "merges": 0,
        "refusals": len(refusals),
        "why_no_merges": "Enrollment at Chicago in 1832 is presence in 1832 and is NOT "
                         "residence in 1835, and the ratified ladder forbids an earlier "
                         "list from minting an 1835 person on its own. So this pass "
                         "proposes corroborations in blackhawk_war_crosswalk.json and "
                         "asserts no identity at all: the mint (T-0514) is where a merge "
                         "belongs, and it inherits these rows.",
    }]
    identity["refusals"] = [x for x in identity.get("refusals") or []
                            if x.get("pass") != TICKET] + refusals

    if write:
        dump(root / RECORDS.relative_to(ROOT), records_doc)
        dump(root / CROSSWALK.relative_to(ROOT), crosswalk_doc)
        dump(identity_path, identity)
    return records_doc, crosswalk_doc, refusals


def declared_count(root: Path = ROOT):
    """What coverage.json says this list holds. The ticket's acceptance: the count is
    declared there, and a missing row fails."""
    path = root / COVERAGE.relative_to(ROOT)
    if not path.exists():
        return None
    for dec in load(path).get("declarations") or []:
        if dec.get("ticket") == TICKET:
            return (dec.get("counts") or {}).get(LIST_ID)
    return None


def check(root: Path = ROOT) -> list:
    bad = []
    recs, cross, _ = build(root, write=False)
    for path, want in ((RECORDS, recs), (CROSSWALK, cross)):
        p = root / path.relative_to(ROOT)
        if not p.exists():
            bad.append("%s is missing — run tools/read_blackhawk_war.py --build" % p.name)
        elif load(p) != want:
            bad.append("%s is stale or hand-edited; regenerate with "
                       "tools/read_blackhawk_war.py --build" % p.name)
    declared = declared_count(root)
    if declared is None:
        bad.append("coverage.json declares no count for %s under %s — the range read has "
                   "to be declared before anything may cite it" % (LIST_ID, TICKET))
    elif declared != len(recs["records"]):
        bad.append("coverage.json declares %s rows for %s and the reading holds %d — a "
                   "missing row fails" % (declared, LIST_ID, len(recs["records"])))
    return bad


def _self_test() -> int:
    """Break each assertion in a copy of the tree and prove the gate says so."""
    def run(mutate, expect, label):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "4d"
            (work / "data" / "research").mkdir(parents=True)
            shutil.copytree(GT, work / "data" / "research" / "genealogytrails")
            shutil.copytree(CIVIC, work / "data" / "research" / "civic")
            mutate(work)
            try:
                bad = check(work)
            except SystemExit as exc:
                bad = [str(exc)]
            hit = [b for b in bad if expect in b]
            print(("  ok   " if hit else "  MISS ") + label)
            return bool(hit)

    def edit_json(path, fn):
        def go(work):
            p = work / path
            doc = json.loads(p.read_text())
            fn(doc)
            p.write_text(json.dumps(doc, indent=2))
        return go

    print("self-test — every assertion, broken on purpose:")
    ok = []
    ok.append(run(edit_json("data/research/civic/records/blackhawk_war_1832_chicago.json",
                            lambda d: d["records"].pop(0)),
                  "stale or hand-edited", "a record deleted by hand"))
    ok.append(run(edit_json("data/research/civic/coverage.json",
                            lambda d: [dec.update(counts={LIST_ID: 133})
                                       for dec in d["declarations"]
                                       if dec.get("ticket") == TICKET]),
                  "a missing row fails", "a coverage count that undercounts the list"))
    ok.append(run(lambda w: (w / "data/research/civic/records"
                             / "blackhawk_war_1832_chicago.json").unlink(),
                  "is missing", "the records file deleted"))
    ok.append(run(lambda w: (w / "data/research/genealogytrails/html/blackhawkwar.htm")
                  .write_text("<TABLE></TABLE>", encoding="utf-8"),
                  "no header row", "a cached page whose columns are gone"))

    def drop_a_row(work):
        p = work / "data/research/genealogytrails/html/blackhawkwar.htm"
        doc = p.read_text(encoding="utf-8", errors="replace")
        i = doc.upper().find("<TR>", doc.upper().find("ADAMS, WILLIAM H"))
        j = doc.upper().find("</TR>", i) + 5
        p.write_text(doc[:i] + doc[j:], encoding="utf-8")
    ok.append(run(drop_a_row, "data rows, not the 134", "a row lost from the page"))

    def break_text(work):
        p = work / "data/research/civic/text/blackhawk_war_1832_chicago.txt"
        p.write_text(p.read_text(encoding="utf-8").replace("AS KE WITT", "AS KE WIT"),
                     encoding="utf-8")
    ok.append(run(break_text, "byte-identical", "a domain text copy that has drifted"))

    print("%d of %d assertions fired" % (sum(ok), len(ok)))
    return 0 if all(ok) else 1


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
        recs, cross, refusals = build(write=True)
        print("Black Hawk War 1832: %d rows (%d with a surname comma, %d without); "
              "%d corroborated, %d ambiguous, %d unmatched, %d no_surname; "
              "%d refusal(s), 0 merges"
              % (recs["counts"]["rows"], recs["counts"]["with_surname_comma"],
                 recs["counts"]["without_surname_comma"],
                 cross["counts"]["corroborated"], cross["counts"]["ambiguous"],
                 cross["counts"]["unmatched"], cross["counts"]["no_surname"],
                 len(refusals)))
        return 0
    bad = check()
    for b in bad:
        print("  FAIL  " + b)
    if not bad:
        recs, cross, _ = build(write=False)
        print("  Black Hawk War 1832: %d rows, %d corroborated, %d ambiguous, "
              "%d unmatched, %d no_surname"
              % (recs["counts"]["rows"], cross["counts"]["corroborated"],
                 cross["counts"]["ambiguous"], cross["counts"]["unmatched"],
                 cross["counts"]["no_surname"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
