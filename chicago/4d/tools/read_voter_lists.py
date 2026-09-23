#!/usr/bin/env python3
"""Read the four Chicago voter lists of 1833-1835 into the civic domain, and
crosswalk every entry to the residents layer (T-0493).

    tools/read_voter_lists.py --build    write the records, the crosswalk, coverage
    tools/read_voter_lists.py --check    re-derive and refuse a stale committed file

`--check` holds all THREE files this tool writes — the records, voter_crosswalk.json
and the T-0493 rows of the domain's civic/crosswalk.json — and tools/check.sh runs it
(T-1029). It used to hold the first two only, and the third drifted for eleven days.

WHY THIS IS A TOOL AND NOT A HAND-TYPED FILE. `data/research/civic/README.md` says
the records here are hand-authored, and for a book that is right — somebody must
decide what a paragraph says. A POLL BOOK is not that. It is 345 printed rows in
one committed text file, and the only honest reading of row 214 is "whatever line
214 says". Typing them by hand would introduce exactly the class of error the
`as_read` field exists to exclude, and nothing downstream could tell a typo from a
19th-century spelling. So the rows are DERIVED, the derivation is re-run by the
gate, and a committed file that has drifted from the text fails.

WHAT IS STILL A JUDGEMENT, and therefore is not in here: which entry is which
resident. `--build` proposes matches under the written rules below and every one
of them is a rule, not a guess; the merges and the refusals it cannot decide are
carried to `crosswalk.json`, where a person has to look at them.

THE MATCHING RULES, in the order they are tried. They are deliberately meaner than
a genealogist would be, because this file feeds a MINT (T-0514) and a name that
gets into the town wrongly is very hard to get back out.

  1. SURNAME-ONLY IS ALWAYS A REFUSAL. `Blinn`, `Whistler`, `Pennozer` — the lists
     are full of families and a bare surname separates none of them. Same rule
     `research_domains.check_crosswalk` enforces, applied one step earlier.
  2. A match needs the surname AND a forename discriminator that AGREES: either
     the forenames are equal, or the entry's initials are consistent with the
     resident's forenames initial for initial. `W. H. Adams` reaches
     `William Hanford Adams`; `J. Calhoun` does not reach `Alvin Calhoun`.
  3. If more than one resident survives rule 2, the entry is a CANDIDATE and names
     its rivals. Two Marks Beaubien would both be wrong.
  4. An entry that reaches no resident but appears in the v1 workbook's bridge
     rows (`census_1835_bridge_candidates.json`) is a CANDIDATE against that row.
  5. Everything else is UNMATCHED, which is a finding and not a failure.

NOTHING HERE MINTS OR REGRADES A RESIDENT. T-0514 and T-0515 do that, from the
consolidation, under the owner's grading ladder recorded in T-0493.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path as _ToolsPath

sys.path.insert(0, str(_ToolsPath(__file__).resolve().parent))
from reconstructed_person import is_reconstructed  # noqa: E402
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CIVIC = ROOT / "data" / "research" / "civic"
TEXT = CIVIC / "text" / "voter_lists_1833_1835.txt"
DEPOSIT = ROOT.parent / "reference" / "voter-roll" / \
    "Early_Chicago_Voter_Lists_1833-1835_Transcription.txt"
RECORDS = CIVIC / "records" / "voter_lists_1833_1835.json"
CROSSWALK = CIVIC / "voter_crosswalk.json"
IDENTITY = CIVIC / "crosswalk.json"
BRIDGE = ROOT / "data" / "research" / "residents" / "census_1835_bridge_candidates.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SOURCE_ID = "chicago_voter_lists_1833_1835_irad"

# The four lists, keyed by the line the transcription prints their heading on. The
# heading lines are read out of the committed text and asserted, so a re-transcribed
# deposit fails here rather than silently renumbering 345 locators.
LISTS = [
    {
        "id": "poll_1833",
        "heading_line": 20,
        "heading": "Poll List for the First Election of Board of Trustees of the Town of Chicago (10",
        "first": 22, "last": 51,
        "title": "Poll list of the first election of the Board of Trustees of the "
                 "Town of Chicago, 10 August 1833",
        "date": "1833-08-10",
        "date_confidence": "documented",
    },
    {
        "id": "tax_1833",
        "heading_line": 52,
        "heading": "Tax List of the Town of Chicago - 1833",
        "first": 53, "last": 167,
        "title": "Tax list of the Town of Chicago, 1833",
        "date": "1833",
        "date_confidence": "documented",
    },
    {
        "id": "poll_1834",
        "heading_line": 168,
        "heading": "Election Returns - Poll List of 1834",
        "first": 170, "last": 284,
        "title": "Election returns — poll list of 1834, filed 11 August 1834",
        "date": "1834-08-11",
        "date_confidence": "documented",
    },
    {
        "id": "poll_1835",
        "heading_line": 285,
        "heading": "1835 Poll List",
        "first": 286, "last": 372,
        "title": "Poll list of 1835",
        "date": "1835",
        "date_confidence": "inferred",
    },
]

# Lines inside a list's span that are not entries. The page break is the printed
# artefact of the deposit PDF, not a row.
SKIP = ("", "--- SOURCE PDF PAGE 2 ---", "BACK -- HOME", "©Genealogy Trails")

# Courtesy and rank titles the lists print in front of a name. They are stripped for
# MATCHING and kept in `as_read`, because "Col. J. B. Beaubien" and "J. B. Beaubien"
# are the same man and the rank is a town finding in its own right.
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


def split_name(as_read: str):
    """`Owen, Col. T. J. V.` -> ('Owen', 'Col. T. J. V.'). A row with no comma is a
    surname standing alone, which rule 1 refuses."""
    if "," in as_read:
        surname, rest = as_read.split(",", 1)
        return surname.strip(), rest.strip()
    return as_read.strip(), ""


def tokens(forenames: str):
    """The forename tokens, titles removed, each marked as an initial or a word."""
    out = []
    for raw in re.split(r"\s+", forenames.strip()):
        t = raw.strip()
        if not t:
            continue
        if t.lower() in TITLES or t.lower() in SUFFIXES:
            continue
        letters = re.sub(r"[^A-Za-z]", "", t)
        if not letters:
            continue
        out.append({"raw": t, "letters": letters,
                    "initial": len(letters) == 1 or t.endswith(".") and len(letters) <= 2})
    return out


def titles_in(forenames: str):
    return [t for t in re.split(r"\s+", forenames.strip())
            if t and t.lower() in TITLES]


def normalize(surname: str, forenames: str) -> str:
    """How this project spells the row. Never a repair — abbreviations are kept as
    printed, because expanding `Wm.` to `William` is a reading and belongs to the
    identity layer, not to the transcription."""
    fore = " ".join(t["raw"] for t in tokens(forenames))
    ranks = " ".join(titles_in(forenames))
    core = ("%s %s" % (fore, surname)).strip()
    return ("%s %s" % (ranks, core)).strip() if ranks else core


def name_key(surname: str, forenames: str):
    """(surname, [forename letter-groups]) lowercased, for comparison."""
    return slug(surname), [t["letters"].lower() for t in tokens(forenames)]


def compatible(entry_fore, res_fore) -> bool:
    """Do the entry's forenames AGREE with the resident's, initial for initial?

    Agreement is not laxity: a token that is a bare initial matches a word with the
    same first letter, a word matches only the same word, and the entry may name
    FEWER forenames than the resident (`W. H. Adams` reaches `William Hanford
    Adams`) but never more or different ones. An entry with no forename at all
    never reaches here — rule 1 has already refused it.
    """
    if not entry_fore:
        return False
    if len(entry_fore) > len(res_fore):
        return False
    for e, r in zip(entry_fore, res_fore):
        if len(e) == 1 or len(r) == 1:
            if e[0] != r[0]:
                return False
        elif e != r:
            return False
    return True


def read_text():
    if not TEXT.exists():
        sys.exit("the committed domain text is missing: %s" % TEXT)
    if DEPOSIT.exists() and TEXT.read_bytes() != DEPOSIT.read_bytes():
        sys.exit("the committed domain text is not byte-identical to the read-only "
                 "deposit at %s — the deposit is senior" % DEPOSIT)
    return TEXT.read_text(encoding="utf-8").splitlines()


def extract(lines):
    records = []
    for spec in LISTS:
        got = lines[spec["heading_line"] - 1]
        if got != spec["heading"]:
            sys.exit("line %d of the committed text reads %r, not the heading %r this "
                     "tool was written against — re-read the lists before trusting a "
                     "single locator" % (spec["heading_line"], got, spec["heading"]))
        n = 0
        for line_no in range(spec["first"], spec["last"] + 1):
            raw = lines[line_no - 1]
            if raw.strip() in SKIP:
                continue
            n += 1
            surname, forenames = split_name(raw)
            toks = tokens(forenames)
            records.append({
                "id": "%s_%03d" % (spec["id"], n),
                "as_read": raw,
                "normalized": normalize(surname, forenames),
                "locator": {"list": spec["id"], "line": line_no,
                            "text_file": "voter_lists_1833_1835.txt",
                            "entry": n},
                "reading": "transcription_mediated",
                "confidence": "documented",
                "notes": "%s, entry %d. Surname %r; %s." % (
                    spec["title"], n, surname,
                    "no forename is printed" if not toks else
                    "forenames as printed %r" % forenames),
                "surname": surname,
                "forenames": forenames,
                "list": spec["id"],
            })
    return records


def residents():
    """Every named person in the residents layer, with the surname/forename split
    the matcher compares on."""
    people = []
    for path in sorted(glob.glob(str(HOUSEHOLDS / "*.json"))):
        doc = load(Path(path))
        for person in doc.get("persons") or []:
            # T-1171: a person the reconstruction programme DREW is not a name any source printed.
            # Matching one to a printed name would be this project reading its own invention
            # back as evidence. reconstructed_person.py holds the rule.
            if is_reconstructed(person):
                continue
            name = (person.get("name") or "").strip()
            if not name:
                continue
            parts = [p for p in re.split(r"\s+", name) if p]
            parts = [p for p in parts if p.lower() not in TITLES]
            if len(parts) < 2:
                surname, fore = parts[0] if parts else name, ""
            else:
                tail = parts[-1]
                if tail.lower() in SUFFIXES and len(parts) > 2:
                    surname, fore = parts[-2], " ".join(parts[:-2])
                else:
                    surname, fore = tail, " ".join(parts[:-1])
            key_s, key_f = name_key(surname, fore)
            people.append({
                "person_id": person.get("id"),
                "household_id": doc.get("id"),
                "name": name,
                "grade": person.get("grade"),
                "surname_key": key_s,
                "forename_keys": key_f,
            })
    return people


def bridge_rows():
    if not BRIDGE.exists():
        return {}
    rows = load(BRIDGE).get("rows") or []
    by_poll = {}
    for row in rows:
        poll = (row.get("1835 Poll") or "").strip()
        if poll:
            by_poll.setdefault(poll, row)
    return by_poll


def crosswalk(records, people, bridge):
    by_surname = {}
    for p in people:
        by_surname.setdefault(p["surname_key"], []).append(p)

    entries, refusals = [], []
    for rec in records:
        surname, forenames = rec["surname"], rec["forenames"]
        toks = tokens(forenames)
        key_s, key_f = name_key(surname, forenames)
        pool = by_surname.get(key_s, [])
        out = {
            "record_id": rec["id"],
            "list": rec["list"],
            "as_read": rec["as_read"],
            "normalized": rec["normalized"],
            "outcome": None,
            "matched_resident": None,
            "household_id": None,
            "discriminator": None,
            "candidate": None,
            "rivals": [],
            "rule": None,
        }

        # Rule 1 — a surname standing alone is always a refusal, however many
        # residents carry it.
        if not toks:
            out["outcome"] = "unmatched"
            out["rule"] = (
                "surname-only: the entry %r prints no forename, and a bare surname "
                "separates no member of a family; refused whether or not the "
                "residents layer carries the surname (%d do)."
                % (rec["as_read"], len(pool)))
            if pool:
                refusals.append({
                    "pass": "T-0493",
                    "a": rec["normalized"],
                    "b": pool[0]["name"],
                    "rule": "A surname-only entry is always a refusal: %r prints no "
                            "forename, so nothing in it can separate %r from the other "
                            "bearers of the surname."
                            % (rec["normalized"], pool[0]["name"]),
                    "evidence": [
                        {"source_id": SOURCE_ID,
                         "locator": "%s line %d" % (rec["locator"]["list"],
                                                    rec["locator"]["line"])},
                        {"resident": pool[0]["person_id"]},
                    ],
                })
            entries.append(out)
            continue

        agree = [p for p in pool if compatible(key_f, p["forename_keys"])]
        if len(agree) == 1:
            p = agree[0]
            out["outcome"] = "matched"
            out["matched_resident"] = p["person_id"]
            out["household_id"] = p["household_id"]
            out["discriminator"] = (
                "forenames agree initial for initial: entry %r against resident %r"
                % (rec["normalized"], p["name"]))
            out["rule"] = ("one resident of the surname %r agrees with the entry's "
                           "forenames; %d bearer(s) of the surname were considered."
                           % (surname, len(pool)))
        elif len(agree) > 1:
            out["outcome"] = "candidate"
            out["rivals"] = [p["person_id"] for p in agree]
            out["rule"] = ("%d residents of the surname %r agree with the entry's "
                           "forenames and nothing in the printed row separates them; "
                           "an ambiguous match is a candidate, never a merge."
                           % (len(agree), surname))
            refusals.append({
                "pass": "T-0493",
                "a": rec["normalized"],
                "b": agree[0]["name"],
                "rule": "Ambiguous: the entry %r agrees equally with %s, and the "
                        "printed row carries nothing that separates them."
                        % (rec["normalized"],
                           " and ".join(repr(p["name"]) for p in agree)),
                "evidence": [
                    {"source_id": SOURCE_ID,
                     "locator": "%s line %d" % (rec["locator"]["list"],
                                                rec["locator"]["line"])},
                    {"residents": [p["person_id"] for p in agree]},
                ],
            })
        else:
            row = bridge.get(rec["as_read"])
            if row is not None:
                out["outcome"] = "candidate"
                out["candidate"] = {
                    "source": "census_1835_bridge_candidates.json",
                    "row": row.get("row"),
                    "preferred_name": row.get("Preferred Name"),
                    "tier": row.get("1835 Tier"),
                    "recommendation": row.get("Include Recommendation"),
                }
                out["rule"] = ("no resident of the surname %r agrees with the entry's "
                               "forenames (%d bearer(s) considered), and the v1 "
                               "workbook's bridge rows carry the entry verbatim."
                               % (surname, len(pool)))
            else:
                out["outcome"] = "unmatched"
                out["rule"] = ("no resident of the surname %r agrees with the entry's "
                               "forenames (%d bearer(s) of the surname considered), "
                               "and no bridge row carries the entry."
                               % (surname, len(pool)))
                if pool:
                    refusals.append({
                        "pass": "T-0493",
                        "a": rec["normalized"],
                        "b": pool[0]["name"],
                        "rule": "The surname agrees and the forenames do not: %r "
                                "against %r. A surname match is a clue, not an "
                                "identity."
                                % (rec["normalized"], pool[0]["name"]),
                        "evidence": [
                            {"source_id": SOURCE_ID,
                             "locator": "%s line %d" % (rec["locator"]["list"],
                                                        rec["locator"]["line"])},
                            {"resident": pool[0]["person_id"]},
                        ],
                    })
        entries.append(out)
    return entries, refusals


def build(write=True):
    lines = read_text()
    recs = extract(lines)
    people = residents()
    entries, refusals = crosswalk(recs, people, bridge_rows())

    per_list = {}
    for spec in LISTS:
        ids = [e for e in entries if e["list"] == spec["id"]]
        per_list[spec["id"]] = {
            "entries": len(ids),
            "matched": sum(1 for e in ids if e["outcome"] == "matched"),
            "candidate": sum(1 for e in ids if e["outcome"] == "candidate"),
            "unmatched": sum(1 for e in ids if e["outcome"] == "unmatched"),
        }
    surnames = sorted({slug(r["surname"]) for r in recs})

    records_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_voter_lists.py --build out of "
                "data/research/civic/text/voter_lists_1833_1835.txt, which is a "
                "byte-identical copy of the read-only deposit. Hand-edit and --check "
                "says so. The reading is the transcription's, twice mediated (Schulz "
                "then Genealogy Trails); nothing here was read off the IRAD original.",
        "generated_by": "tools/read_voter_lists.py --build",
        "source_id": SOURCE_ID,
        "publication_source_id": "chicago_genealogist_1993_voter_lists",
        "lists": [{k: spec[k] for k in ("id", "title", "date", "date_confidence")}
                  | {"entries": per_list[spec["id"]]["entries"]} for spec in LISTS],
        "counts": {"entries": len(recs), "distinct_surnames": len(surnames)},
        "records": [{k: r[k] for k in
                     ("id", "as_read", "normalized", "locator", "reading",
                      "confidence", "notes")} for r in recs],
    }

    crosswalk_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_voter_lists.py --build. Every entry of the "
                "four lists, crosswalked to data/residents/ and to the v1 workbook's "
                "bridge rows under the matching rules stated at the head of the tool. "
                "An outcome here is an OUTCOME, not a promotion: nothing in this file "
                "mints or regrades a resident (T-0514, T-0515 do that).",
        "generated_by": "tools/read_voter_lists.py --build",
        # T-0598. Every ruling in this file rests on the four lists and on nothing
        # else, so the file says so once rather than 345 times. Without it nothing
        # could carry a ruling here onto a resident card: `persons[].sources` is a
        # list of SOURCE IDS, and a crosswalk that names a person and not a source
        # can only be spent by a human rereading the whole file.
        "source_id": SOURCE_ID,
        "publication_source_id": "chicago_genealogist_1993_voter_lists",
        "crosswalk_target": "data/residents/households/*.json",
        "residents_compared": len(people),
        "counts": {
            "entries": len(entries),
            "matched": sum(1 for e in entries if e["outcome"] == "matched"),
            "candidate": sum(1 for e in entries if e["outcome"] == "candidate"),
            "unmatched": sum(1 for e in entries if e["outcome"] == "unmatched"),
            "per_list": per_list,
        },
        "entries": entries,
    }
    # The identity file is the domain's, not this ticket's: everything another pass
    # wrote is carried through untouched, and only rows tagged with this pass are
    # replaced. A tool that rewrites crosswalk.json wholesale would silently delete
    # the judgements the next six tickets are about to put in it.
    identity = load(IDENTITY) if IDENTITY.exists() else {
        "schema": 1, "domain": "civic", "passes": [], "merges": [], "refusals": []}
    identity["passes"] = [x for x in identity.get("passes") or []
                          if x.get("ticket") != "T-0493"] + [{
        "ticket": "T-0493",
        "what": "The four voter lists of 1833-1835, every entry crosswalked to the "
                "residents layer by tools/read_voter_lists.py under the matching "
                "rules at the head of that file.",
        "merges": 0,
        "refusals": len(refusals),
        "why_no_merges": "A merge here would be a claim that a poll entry and a "
                         "resident record are the same man, and this ticket does not "
                         "make that claim for anybody: where the rules agree the "
                         "entry is reported as matched in voter_crosswalk.json, and "
                         "where they do not it is reported as a refusal. The mint "
                         "(T-0514) is where a merge belongs.",
    }]
    identity["refusals"] = [x for x in identity.get("refusals") or []
                            if x.get("pass") != "T-0493"] + refusals
    if write:
        dump(RECORDS, records_doc)
        dump(CROSSWALK, crosswalk_doc)
        dump(IDENTITY, identity)
    return records_doc, crosswalk_doc, refusals, identity


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.build:
        recs, cross, refusals, _ = build(write=True)
        print("voter lists: %d entries, %d distinct surnames; %d matched, "
              "%d candidate, %d unmatched; %d refusal(s) proposed"
              % (recs["counts"]["entries"], recs["counts"]["distinct_surnames"],
                 cross["counts"]["matched"], cross["counts"]["candidate"],
                 cross["counts"]["unmatched"], len(refusals)))
        return 0
    if args.check:
        recs, cross, _, identity = build(write=False)
        bad = []
        # T-1029. The identity file is checked ALONGSIDE the two this tool owns
        # outright, and it is checked the same way it is written: `build(write=False)`
        # loads the committed crosswalk.json and splices only the rows tagged with
        # this pass, so comparing the result back against the file asks exactly one
        # question — are T-0493's `passes` entry and refusals what the rules derive
        # today? Another pass's rows are on both sides of the comparison and cannot
        # fail it. Without this step the refusal count sat at 82 while the tool
        # derived 26 for eleven days, because nothing re-derived it and nothing asked.
        for path, want in ((RECORDS, recs), (CROSSWALK, cross), (IDENTITY, identity)):
            if not path.exists():
                bad.append("%s is missing — run --build" % path.name)
            elif load(path) != want:
                bad.append("%s is stale or hand-edited; regenerate with "
                           "tools/read_voter_lists.py --build" % path.name)
        for b in bad:
            print("  FAIL  " + b)
        declared = next((p["refusals"] for p in identity.get("passes") or []
                         if p.get("ticket") == "T-0493"), None)
        print("  voter lists: %d entries, %d matched, %d candidate, %d unmatched; "
              "T-0493 declares %s refusal(s) in crosswalk.json"
              % (recs["counts"]["entries"], cross["counts"]["matched"],
                 cross["counts"]["candidate"], cross["counts"]["unmatched"], declared))
        return 1 if bad else 0
    ap.error("one of --build or --check")


if __name__ == "__main__":
    sys.exit(main())
