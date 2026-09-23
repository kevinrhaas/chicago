#!/usr/bin/env python3
"""The 1840 census heads, spent on the people they name (T-0698).

    python3 tools/spend_census_1840_heads.py             write the ledger and the cards
    python3 tools/spend_census_1840_heads.py --check     everything re-derives; nothing drifted
    python3 tools/spend_census_1840_heads.py --report    person by person, what the sheet says
    python3 tools/spend_census_1840_heads.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. `data/research/census_1840/resident_crosswalk.json` adjudicates every
named head on the 1840 left sheets against the 1835 name pools, and its `matched` and
`candidate` rulings name a person this town holds a card for. Until this pass those
rulings lived only in the crosswalk. `tools/measure_research_spend.py`'s second hop is
the instrument that says so: a ruling naming a person whose CARD has not learned it is
counted `unwritten`, and the census_1840 ceiling on that hop is 0.

T-0670 found the shape of the problem from the other end. The crosswalk had gone stale —
declared against 849 residents and 17 sheets while the town held 1,404 and 25 — and
rebuilding it re-derived one more ruling than the domain had spent, so the gate failed
and the run reverted rather than rule. This pass is the ruling, generalised: whatever the
crosswalk reaches, the card is told.

WHAT THIS SOURCE IS, AND THE LIMIT THAT TRAVELS WITH IT. A head on an 1840 left sheet is
a name written down five years after the 1835-07-01 scene. The crosswalk states the limit
at the top of its own file — "LATER EVIDENCE ONLY… an 1839 or 1840 appearance alone is
never an 1835 resident, and 1840 household composition is never back-projected" — and
that sentence is quoted onto every card rather than paraphrased.

WHAT IS AND IS NOT WRITTEN, in four rules — the rules tools/spend_land_sales.py holds,
unchanged, because the defect they guard against is the same one.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED. This pass re-adjudicates nothing. It reads
     the `matched` and `candidate` heads and writes those. The 761 refusals are rivals
     still standing and write nothing — a refusal is not a spend.

  2. TWO FIELDS AND NO OTHERS. A person gains the source id in `sources` and a paragraph
     in `note`. Nothing else is touched — not a grade, not an arrival, not a claim block,
     not a placement, and above all not `present_on_scene_date`. `--self-test` holds that
     by diffing a record through the applier and asserting the changed key set.

  3. NO GRADE MOVES, and a CANDIDATE SAYS SO IN ITS OWN PARAGRAPH. `matched` and
     `candidate` are different things and are written differently: a candidate's
     paragraph states, in its own words, that nothing independent of the name was found
     and that the project asserts no identity from it. Reading the two the same way is
     precisely what the crosswalk's ladder exists to prevent.

  4. ONE PARAGRAPH PER PERSON, NOT PER HEAD. A person the sheets carry twice is told
     once, in a paragraph naming every sheet, page and line behind the ruling.

THE LEDGER IS NOT A CROSSWALK, deliberately, and for the reason the earlier passes gave:
`data/research/census_1840/head_spend_1835.json` carries no "crosswalk" in its name so
that `measure_research_spend.py` does not read a record of WRITES as a second
adjudication and report the pass grading its own homework.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(Path(__file__).resolve().parent))

# THE ONCE-EACH RULE lives in one place (T-0846). `gaps` asks whether this pass's
# paragraph is PRESENT and `strays` whether an unruled card carries one; neither can
# see a card that carries it TWICE, which is what an add-only applier produces when the
# wording changes between runs. T-0677 measured that on this series and closed it in one
# tool; three copies later the copies had already drifted apart, so the rule is shared.
import spend_write_once  # noqa: E402
CENSUS = ROOT / "data" / "research" / "census_1840"
CROSSWALK = CENSUS / "resident_crosswalk.json"
LEDGER = CENSUS / "head_spend_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1

# The sheets, and the only id written onto a card. The crosswalk states it at the top of
# the file and every proposed later-census block states the same one.
SOURCE_ID = "census_1840_chicago_familysearch_images"

# The sentence that says a paragraph is this pass's, so re-running it is idempotent and
# `--check` can find its own work without guessing.
MARKER = "THE 1840 FEDERAL CENSUS — A HEAD FIVE YEARS AFTER THE SCENE, AND NEVER AN 1835 FACT."

# A WORDING THIS PASS HAS REPLACED — the second half of the once-each rule (T-0846). An
# applier here is add-only (`if MARKER not in note`), so rewriting the paragraph makes a
# re-run APPEND a second one saying the same thing in different words rather than overwrite
# the first, and neither `gaps` nor `strays` can see it. T-0677 measured exactly that on
# `spend_land_sales.py`: thirty-one cards doubled, `tools/check.sh` green. Any MARKER this
# pass retires belongs in this tuple from the commit that retires it, and `--check` then
# refuses a card still carrying it. Empty means this pass has never changed its wording.
SUPERSEDED_MARKERS: tuple = ()

# What the crosswalk carries as `outcome` and this pass will write. `refused` is not here
# and must never be: a rival still standing is not a ruling to spend.
WRITTEN_OUTCOMES = ("matched", "candidate")

LADDER_LIMIT = (
    "This pass WRITES THE EVIDENCE AND MOVES NO GRADE. Under the ratified ladder (T-0513) "
    "a second independent source is what lifts a projected resident, and an 1840 head is a "
    "second source about CONTINUED RESIDENCE rather than about who was living at Chicago "
    "on 1 July 1835. T-0515 applies the ladder against every source at once; this pass "
    "hands it the evidence and not the verdict."
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def sheets(row: dict) -> list:
    """Where each head of this ruling sits, as the reader would go back to it."""
    return ["%s, printed page %s, line %s"
            % (h["familysearch_id"], h["printed_page"], h["line"])
            for h in row["heads"]]


def rulings() -> list:
    """One row per PERSON the crosswalk reaches, folding the heads that name them.

    Rule 4. A person carried on two sheets is one row here and is told once; the row
    keeps every head behind it so the paragraph can name them all.
    """
    doc = load(CROSSWALK)
    by_person = {}
    for head in doc.get("heads") or []:
        if head.get("outcome") not in WRITTEN_OUTCOMES:
            continue
        pid, hh = head.get("person_id"), head.get("household_id")
        if not pid or not hh:
            continue
        row = by_person.setdefault(pid, {
            "person_id": pid, "household_id": hh,
            "resident_name": head.get("resident_name"), "heads": [],
        })
        row["heads"].append(head)
    rows = []
    for pid in sorted(by_person):
        row = by_person[pid]
        row["heads"].sort(key=lambda h: (h["printed_page"] or 0, h["line"] or 0))
        # matched outranks candidate: a person matched on one sheet and a candidate on
        # another is a matched person, and the paragraph says which sheet did which.
        row["outcome"] = ("matched" if any(h["outcome"] == "matched" for h in row["heads"])
                          else "candidate")
        row["rules"] = sorted({h["rule"] for h in row["heads"]})
        rows.append(row)
    return rows


def paragraph(row: dict) -> str:
    """What one person's card is told, and the whole of it."""
    doc = load(CROSSWALK)
    heads = row["heads"]
    as_read = ", ".join("“%s”" % h["as_read"] for h in heads)
    where = "; ".join(sheets(row))
    if row["outcome"] == "matched":
        verdict = (
            "This project has ruled the head a MATCH for this person: the full name agrees, "
            "it is unique on both sides, and a discriminator independent of the name — "
            "%s — separately places the same person in Chicago after the 1840 book was "
            "taken." % _discriminator_phrase(heads))
    else:
        verdict = (
            "This project has ruled the head a CANDIDATE and no more: the name agrees and is "
            "unique on both sides, but %s. A candidate is not an identity — nothing is "
            "asserted from it, no household of 1840 is carried back, and the ruling is "
            "recorded so that a reader can see it was made rather than missed."
            % _candidate_why(heads))
    return (
        "%s The 1840 federal census of Chicago, read line by line off the left sheets in "
        "this repository, carries %d head%s of this name — %s (%s). %s Under the rule that "
        "decided it (%s), by the crosswalk's own ladder "
        "(data/research/census_1840/resident_crosswalk.json). %s %s"
        % (MARKER, len(heads), "" if len(heads) == 1 else "s", as_read, where, verdict,
           ", ".join(row["rules"]), doc.get("scene_relation", "").strip(), LADDER_LIMIT))


def _discriminator_phrase(heads: list) -> str:
    kinds = sorted({d.get("kind") for h in heads for d in (h.get("discriminators") or [])
                    if d.get("kind")})
    return ", ".join(k.replace("_", " ") for k in kinds) if kinds else "stated on the ruling"


def _candidate_why(heads: list) -> str:
    if any(h["rule"].startswith("L6a") for h in heads):
        return ("the reader graded the name on the sheet low, and a low-confidence read caps "
                "at a candidate however well the name agrees")
    return "nothing independent of the name was found"


# --- the ledger ------------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = rulings()
    xw = load(CROSSWALK)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by tools/spend_census_1840_heads.py (T-0698). Which of the 1840 head "
            "crosswalk's resident rulings were written onto the card they name, and what "
            "each card was told. It is a record of WRITES, not of adjudications — the "
            "adjudication is resident_crosswalk.json — and it deliberately carries no "
            "'crosswalk' in its name so that measure_research_spend.py does not count a "
            "write as a second ruling."),
        "generated_by": "tools/spend_census_1840_heads.py",
        "ticket": "T-0698",
        "source_id": SOURCE_ID,
        "reads": ["data/research/census_1840/resident_crosswalk.json"],
        "writes": "data/residents/households/*.json — persons[].sources and persons[].note",
        "carry_rule": xw.get("scene_relation"),
        "counts": {
            "heads_adjudicated": len(xw.get("heads") or []),
            "rulings_that_reach_a_person": sum(len(r["heads"]) for r in rows),
            "people_written": len(rows),
            "matched": sum(1 for r in rows if r["outcome"] == "matched"),
            "candidate": sum(1 for r in rows if r["outcome"] == "candidate"),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
        },
        "people": [
            {"person_id": r["person_id"], "household_id": r["household_id"],
             "resident_name": r["resident_name"], "outcome": r["outcome"],
             "rules": r["rules"], "sheets": sheets(r),
             "as_read": [h["as_read"] for h in r["heads"]],
             "told": paragraph(r)}
            for r in rows
        ],
    }


# --- the write -------------------------------------------------------------------------

def apply_to_person(person: dict, row: dict) -> bool:
    """The ONLY mutation this tool performs. Two keys, and rule 2 is held here."""
    changed = False
    if SOURCE_ID not in (person.get("sources") or []):
        person["sources"] = (person.get("sources") or []) + [SOURCE_ID]
        changed = True
    note = (person.get("note") or "").strip()
    want = paragraph(row)
    if MARKER not in note:
        person["note"] = (note + " " + want).strip()
        changed = True
    elif _mine(note) != want:
        # A paragraph that no longer says what the crosswalk says is worse than none:
        # it is this pass's own words, stale, over a ruling that has since moved.
        person["note"] = (_without_mine(note) + " " + want).strip()
        changed = True
    return changed


def _span(note: str) -> tuple[int, int]:
    # T-0976: another evidence writer may append after this paragraph. Owning
    # everything from MARKER to end-of-note silently deleted Fergus's later lists.
    start = note.index(MARKER)
    end = note.find(LADDER_LIMIT, start)
    if end < 0:
        raise ValueError("census paragraph has no known closing boundary; refusing to discard other evidence")
    return start, end + len(LADDER_LIMIT)


def _mine(note: str) -> str:
    start, end = _span(note)
    return note[start:end].strip()


def _without_mine(note: str) -> str:
    start, end = _span(note)
    return " ".join(part.strip() for part in (note[:start], note[end:]) if part.strip())


def retract_from_person(person: dict) -> bool:
    """The exact inverse of `apply_to_person`, for a card no ruling reaches any more.

    `strays` has always been able to SEE a withdrawn ruling whose paragraph still stood —
    it says so in its own docstring — and nothing could ever clear one, so the gate could
    only be satisfied by hand. T-0963 is the first reading to withdraw one: a second
    "John Davis" arrives on printed 212 and the crosswalk refuses BOTH heads under L5
    (`name_is_not_unique`), so the match written onto hh_davis_john by T-0698 is no longer
    a ruling this pass may spend. A refusal is never spent, so the card must carry neither
    the paragraph nor the citation this pass put there — and the withdrawal stays legible
    in the ledger, which is derived and re-derives to a row that is simply gone.
    """
    changed = False
    note = (person.get("note") or "").strip()
    if MARKER in note:
        person["note"] = _without_mine(note)
        changed = True
        # Only when this pass's own paragraph came off: the citation is what `apply` adds
        # beside it, and stripping one without the other leaves a source behind a card
        # that nothing on the card can account for.
        sources = person.get("sources") or []
        if SOURCE_ID in sources:
            person["sources"] = [s for s in sources if s != SOURCE_ID]
    return changed


def retract(quiet: bool = False) -> int:
    ruled = {r["person_id"] for r in rulings()}
    dropped = 0
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hh = load(path)
        moved = False
        for person in hh.get("persons") or []:
            if person.get("id") in ruled:
                continue
            if retract_from_person(person):
                dropped += 1
                moved = True
        if moved:
            dump(path, hh)
    if not quiet and dropped:
        print("1840 census heads: withdrawn from %d resident record(s)" % dropped)
    return dropped


def apply(quiet: bool = False) -> int:
    touched = 0
    for row in rulings():
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        if not path.exists():
            continue
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row):
                touched += 1
                dump(path, hh)
    if not quiet:
        print("1840 census heads: written onto %d resident record(s)" % touched)
    return touched


def build(quiet: bool = False) -> int:
    dump(LEDGER, ledger_doc())
    retract(quiet=quiet)
    apply(quiet=quiet)
    if not quiet:
        print("wrote %s" % LEDGER.relative_to(ROOT))
    return 0


# --- the gate --------------------------------------------------------------------------

def _person(row: dict):
    path = HOUSEHOLDS / ("%s.json" % row["household_id"])
    if not path.exists():
        return None
    for person in load(path).get("persons") or []:
        if person.get("id") == row["person_id"]:
            return person
    return None


def _gaps_over(row: dict, person: dict) -> list:
    """gaps() for one already-loaded person — what the self-test needs and the gate reuses."""
    out = []
    who = "%s/%s" % (row["household_id"], row["person_id"])
    if SOURCE_ID not in (person.get("sources") or []):
        out.append("%s — ruled %s by the crosswalk and the card does not cite %s"
                   % (who, row["outcome"], SOURCE_ID))
    note = person.get("note") or ""
    if MARKER not in note:
        out.append("%s — ruled %s by the crosswalk and the card carries no paragraph"
                   % (who, row["outcome"]))
    elif _mine(note) != paragraph(row):
        # T-0698's own lesson, learned from T-0700: `gaps` asked whether a paragraph was
        # PRESENT and never whether it was RIGHT, so a card kept saying "candidate" after
        # its ruling had become a match. A stale paragraph is a gate failure here.
        out.append("%s — the paragraph on the card no longer says what the crosswalk says"
                   % who)
    return out


def gaps(rows: list) -> list:
    """Every ruling has to be ON the record it names, or the ruling is only a file."""
    bad = []
    for row in rows:
        person = _person(row)
        if person is None:
            bad.append("%s/%s — the record the ruling names does not exist"
                       % (row["household_id"], row["person_id"]))
            continue
        bad.extend(_gaps_over(row, person))
    return bad


def strays(rows: list) -> list:
    """A card carrying this pass's paragraph that no ruling reaches. The mirror of gaps:
    without it a ruling could be withdrawn and its paragraph would stand for ever."""
    ruled = {r["person_id"] for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        for person in load(path).get("persons") or []:
            if MARKER in (person.get("note") or "") and person.get("id") not in ruled:
                bad.append("%s/%s — carries this pass's paragraph and no ruling reaches it"
                           % (path.stem, person.get("id")))
    return bad


def doubles() -> list:
    """One paragraph per person, once. A tool re-run must never leave two.

    T-0846 moved the rule itself into `tools/spend_write_once.py`, where the six passes
    that write a paragraph share one implementation. The copy that stood here counted the
    marker and nothing else; the shared rule also refuses a SUPERSEDED wording standing
    beside the current one, which is the half this pass never had.
    """
    return spend_write_once.doubles(MARKER, SUPERSEDED_MARKERS, HOUSEHOLDS)


def check(quiet: bool = False) -> int:
    rows = rulings()
    if not LEDGER.exists():
        print("   the ledger is missing: %s" % LEDGER.relative_to(ROOT))
        return 1
    if load(LEDGER) != ledger_doc():
        print("   %s no longer re-derives from the crosswalk — re-run the tool"
              % LEDGER.relative_to(ROOT))
        return 1
    bad = gaps(rows) + strays(rows) + doubles()
    if bad:
        for line in bad[:20]:
            print("   %s" % line)
        if len(bad) > 20:
            print("   …and %d more" % (len(bad) - 20))
        return 1
    if not quiet:
        print("1840 census heads: %d ruling(s) on %d card(s), no strays, none written twice"
              % (sum(len(r["heads"]) for r in rows), len(rows)))
    return 0


def report() -> int:
    rows = rulings()
    print("%-30s %-26s %-10s %-38s %s"
          % ("household", "person", "outcome", "rule(s)", "sheet(s)"))
    print("-" * 130)
    for r in rows:
        print("%-30s %-26s %-10s %-38s %s"
              % (r["household_id"], r["person_id"], r["outcome"],
                 ", ".join(r["rules"]), "; ".join(sheets(r))))
    print("-" * 130)
    print("%d people, %d head(s), %d matched, %d candidate"
          % (len(rows), sum(len(r["heads"]) for r in rows),
             sum(1 for r in rows if r["outcome"] == "matched"),
             sum(1 for r in rows if r["outcome"] == "candidate")))
    return 0


def self_test() -> int:
    fails = []

    def fires(label, ok):
        if not ok:
            fails.append(label)

    rows = rulings()
    fires("the crosswalk reaches at least one person", bool(rows))
    fires("no refusal is ever spent",
          all(h["outcome"] in WRITTEN_OUTCOMES for r in rows for h in r["heads"]))
    fires("one row per person, rule 4",
          len({r["person_id"] for r in rows}) == len(rows))

    # Rule 2, held by diffing a record through the applier.
    row = rows[0]
    before = {"id": row["person_id"], "name": "X", "grade": "attested",
              "sources": ["andreas_1884_v1"], "note": "Something already said.",
              "present_on_scene_date": {"value": "present"}}
    after = json.loads(json.dumps(before))
    apply_to_person(after, row)
    changed = {k for k in after if json.dumps(after[k]) != json.dumps(before.get(k))}
    fires("rule 2: exactly `sources` and `note` move", changed == {"sources", "note"})
    fires("rule 2: the earlier note is kept", "Something already said." in after["note"])
    fires("rule 2: the grade does not move", after["grade"] == "attested")
    fires("rule 2: present_on_scene_date does not move",
          after["present_on_scene_date"] == {"value": "present"})

    # Idempotence, and the stale-paragraph rule that `gaps` used not to hold.
    again = json.loads(json.dumps(after))
    fires("re-running writes nothing", apply_to_person(again, row) is False)
    fires("…and leaves exactly one paragraph", again["note"].count(MARKER) == 1)
    fires("a clean record has no gap", _gaps_over(row, again) == [])
    sibling = "FERGUS: independently written later evidence survives."
    following = json.loads(json.dumps(after))
    following["note"] += " " + sibling
    fires("another writer's following paragraph is not census drift",
          apply_to_person(following, row) is False)
    following["note"] = following["note"].replace("The 1840 federal census", "The 1841 census")
    fires("refresh preserves the following writer's evidence",
          apply_to_person(following, row) and sibling in following["note"])
    fires("withdrawal preserves the following writer's evidence",
          retract_from_person(following) and following["note"] == before["note"] + " " + sibling)

    stale = json.loads(json.dumps(after))
    stale["note"] = stale["note"].replace("The 1840 federal census", "The 1841 census")
    fires("a stale paragraph is a gap", len(_gaps_over(row, stale)) == 1)
    fires("…and is rewritten rather than doubled",
          apply_to_person(stale, row) and stale["note"].count(MARKER) == 1)
    fires("…to what the crosswalk now says", _gaps_over(row, stale) == [])

    missing = json.loads(json.dumps(before))
    fires("a card citing nothing is a gap", len(_gaps_over(row, missing)) == 2)

    # T-0963: the withdrawal. `strays` could always see a ruling that had gone away and
    # nothing could clear it, so the inverse is held here as tightly as the write is.
    withdrawn = json.loads(json.dumps(after))
    fires("a withdrawn ruling takes its paragraph off", retract_from_person(withdrawn)
          and MARKER not in (withdrawn.get("note") or ""))
    fires("…and its citation with it", SOURCE_ID not in (withdrawn.get("sources") or []))
    fires("…and leaves the record otherwise exactly as it was found",
          withdrawn == before)
    fires("withdrawing twice writes nothing", retract_from_person(withdrawn) is False)
    untouched = json.loads(json.dumps(before))
    fires("a card this pass never wrote is left alone",
          retract_from_person(untouched) is False and untouched == before)

    # A candidate must say so, and a match must not be written as one.
    for r in rows:
        text = paragraph(r)
        if r["outcome"] == "candidate":
            fires("a candidate's paragraph says CANDIDATE and asserts nothing",
                  "CANDIDATE and no more" in text and "A candidate is not an identity" in text)
        else:
            fires("a match's paragraph says MATCH", "ruled the head a MATCH" in text)
        fires("every paragraph carries the ladder limit", LADDER_LIMIT in text)
        fires("every paragraph names its sheets",
              all(s in text for s in sheets(r)))

    # THE ONCE-EACH RULE, both directions (T-0846). The copy that stood in this file counted
    # the marker and never looked for a SUPERSEDED wording — the half `spend_land_sales.py`
    # had and this one did not. The rule now comes out of `tools/spend_write_once.py`, and
    # these three assertions are what says it still fires from here.
    fires("the once-each rule is silent on the card the applier writes",
          spend_write_once.doubles_over("hh_x", after, MARKER, SUPERSEDED_MARKERS) == [])
    twice = json.loads(json.dumps(after))
    twice["note"] = twice["note"] + " " + twice["note"]
    fires("the once-each rule fires on a card carrying this paragraph twice",
          any("2 times" in d for d in spend_write_once.doubles_over(
              "hh_x", twice, MARKER, SUPERSEDED_MARKERS)))
    rival = json.loads(json.dumps(after))
    rival["note"] = rival["note"] + " A SUPERSEDED WORDING OF THE SAME PASS. …"
    fires("the once-each rule fires on a superseded paragraph left standing",
          any("superseded" in d for d in spend_write_once.doubles_over(
              "hh_x", rival, MARKER, ("A SUPERSEDED WORDING OF THE SAME PASS.",))))
    fires("this pass declares its superseded wordings as a tuple",
          isinstance(SUPERSEDED_MARKERS, tuple))

    for line in fails:
        print("   FAIL: %s" % line)
    print("1840 census heads self-test: %d assertion group(s), %d failure(s)"
          % (22 + 4 * len(rows), len(fails)))
    return 1 if fails else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check(quiet=args.quiet)
    if args.report:
        return report()
    return build(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
