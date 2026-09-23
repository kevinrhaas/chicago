#!/usr/bin/env python3
"""The Second Presbyterian roll, spent on the people it names (T-0992).

    python3 tools/spend_second_presbyterian_roll.py             write the ledger and the cards
    python3 tools/spend_second_presbyterian_roll.py --check     everything re-derives; nothing drifted
    python3 tools/spend_second_presbyterian_roll.py --report    person by person, what the roll says
    python3 tools/spend_second_presbyterian_roll.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. T-0962 widened the second hop of `tools/measure_research_spend.py` to read
the `matched` container, and the church domain entered that report for the first time: 83
rulings reached a person this town holds a card for, 83 were judgeable, and NOT ONE card
cited the roll. `grep -r second_presbyterian_chicago_1892 data/residents/` returned nothing.
The adjudication had been made — `data/research/church/second_presbyterian_crosswalk.json`
files 83 lines as `matched`, 37 as `ambiguous` and 330 as `refused` — and it had never
crossed into the town. This pass is that crossing, and nothing else.

WHAT THIS SOURCE IS, AND THE LIMIT THAT TRAVELS WITH IT. The roll is the 1892 printing of the
membership of the Second Presbyterian Church of Chicago, a church ORGANISED IN JUNE 1842 —
seven years after the scene this project reconstructs. Its admission dates run from
1842-06-01 to 1892-02-29; `second_presb_0371` is admitted 27 April 1859. An 1859 admission is
not 1835 evidence, and the crosswalk says so itself, in the file, in the sentence this pass
quotes onto every card rather than paraphrasing:

    "NOTHING. A line on a roll that opens in June 1842 cannot place a person in the town of
     July 1835, and this file makes no proposal that it does."

The ladder T-0505 ratified binds here exactly as it binds an 1840 head: the evidence is
handed to the card, the verdict is not.

WHAT IS AND IS NOT WRITTEN, in five rules — the first four are the rules
tools/spend_census_1840_heads.py and tools/spend_land_sales.py hold, unchanged, because the
defect they guard against is the same one. The fifth is this roll's own.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED, and only `matched`. This pass re-adjudicates
     nothing. The 37 `ambiguous` and the 330 `refused` write NOTHING: a rival still standing
     is not a ruling to spend, and that is the line MATCH_CONTAINERS draws.

  2. TWO FIELDS AND NO OTHERS. A person gains the source id in `sources` and a paragraph in
     `note`. Nothing else is touched — not a grade, not an arrival, not a claim block, not a
     placement, and above all not `present_on_scene_date`. `--self-test` holds that by
     diffing a record through the applier and asserting the changed key set.

  3. NO GRADE MOVES. The crosswalk mints and regrades nothing and neither does its spend.

  4. ONE PARAGRAPH PER PERSON. The crosswalk matches a person to exactly ONE roll line —
     `residents_matched_one_line` is the count's own name for it — so a person is told once,
     and the paragraph names the line, its printed page and its record id.

  5. A WIFE'S LINE IS HER HUSBAND'S NAME, AND THE CARD IS TOLD SO. 34 of the 83 matched
     lines are flagged `a_married_womans_entry` — the roll prints `Cook, Mrs. J. L.`
     throughout — and the crosswalk's own Mrs rule says what such a line has met: "a line
     flagged a_married_womans_entry that meets a MAN in the 1835 layer has met his name, not
     him". Suppressing those matches would make them invisible; writing them without the
     caution would make them look like a person on a roll. So the flag travels onto the card
     in the crosswalk's own words, and a reader can argue with it.

  6. A LINE MET BY SEVERAL TOWNSPEOPLE SAYS SO ON EVERY ONE OF THEIR CARDS (T-0995). Rule 4
     is about the PERSON — the crosswalk matches a person to exactly one line — and it says
     nothing whatever about the LINE, which may be met by several. `matched` means this
     RESIDENT met exactly one line; a resident meeting several is `ambiguous`. Five records
     are matched to two or three cards apiece, eleven cards in all, and each of the three
     Cooks read "carries 1 line whose surname and given initial agree with this person's" —
     true of each of them, and reading as though the line were about the one card in front of
     the reader. That is T-0700's failure exactly: a paragraph that is not false and is not
     the whole ruling either. So where a record reaches more than one person, every one of
     those cards NAMES THE OTHERS, and `--check` refuses a card that omits them. The clause
     is derived, never asserted: it names the rival person ids the crosswalk itself produces,
     and `--self-test` holds that a shared line names its rivals and an unshared one carries
     no such clause at all.

THE LEDGER IS NOT A CROSSWALK, deliberately, and for the reason the earlier passes gave:
`data/research/church/second_presbyterian_roll_spend_1835.json` carries no "crosswalk" in its
name so that `measure_research_spend.py` does not read a record of WRITES as a second
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
CHURCH = ROOT / "data" / "research" / "church"
CROSSWALK = CHURCH / "second_presbyterian_crosswalk.json"
LEDGER = CHURCH / "second_presbyterian_roll_spend_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1

# The only id written onto a card. The crosswalk states it at the top of the file and every
# matched line repeats it; this pass asserts they agree rather than assuming it.
SOURCE_ID = "second_presbyterian_chicago_1892"

# The sentence that says a paragraph is this pass's, so re-running it is idempotent and
# `--check` can find its own work without guessing.
MARKER = ("THE SECOND PRESBYTERIAN ROLL — A NAME ON A CHURCH LIST THAT OPENS IN 1842, "
          "AND NEVER AN 1835 FACT.")

# A WORDING THIS PASS HAS REPLACED — the second half of the once-each rule (T-0846). An
# applier here is add-only (`if MARKER not in note`), so rewriting the paragraph makes a
# re-run APPEND a second one saying the same thing in different words rather than overwrite
# the first, and neither `gaps` nor `strays` can see it. T-0677 measured exactly that on
# `spend_land_sales.py`: thirty-one cards doubled, `tools/check.sh` green. Any MARKER this
# pass retires belongs in this tuple from the commit that retires it, and `--check` then
# refuses a card still carrying it. Empty means this pass has never changed its wording.
SUPERSEDED_MARKERS: tuple = ()

# What the crosswalk carries as its container and this pass will write. `ambiguous` and
# `refused` are not here and must never be: a rival still standing is not a ruling to spend.
WRITTEN_CONTAINERS = ("matched",)

# The closing sentence of every paragraph — and, because another evidence writer may append
# after it, the boundary that tells this pass where its own words stop (T-0976).
LADDER_LIMIT = (
    "This pass WRITES THE EVIDENCE AND MOVES NO GRADE: under the ratified ladder (T-0513) the "
    "roll is handed to the card as a thing a reader may weigh, and the verdict stays with "
    "T-0515, which applies the ladder against every source at once.")

# The opening of rule 6's clause (T-0995), and the thing `--check` looks for when it asks
# whether a card whose roll line is met by several townspeople says so. A separate marker
# rather than a substring test on the names, so the gate can tell "this card names the wrong
# rivals" from "this card was never told the line is shared" and say which.
SHARED_MARKER = "THE SAME ROLL LINE IS MET BY OTHER TOWNSPEOPLE OF THIS NAME:"

# How many, in words, because the clause reads as a sentence and not as a table.
_COUNT_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def rulings() -> list:
    """One row per PERSON the crosswalk matches, in the file's own order by person id."""
    doc = load(CROSSWALK)
    rows = []
    for key in WRITTEN_CONTAINERS:
        for row in doc.get(key) or []:
            if not row.get("person_id") or not row.get("household_id"):
                continue
            rows.append(row)
    rows.sort(key=lambda r: r["person_id"])
    return rows


def shared_records(rows: list | None = None) -> dict:
    """record id -> every matched row that names it, for the records more than one row does.

    Rule 6 (T-0995). The crosswalk's `matched` container is indexed BY PERSON, so nothing in
    it can see that one printed line was met by three Cooks; only this regrouping can. Rows
    come back in `rulings()` order — by person id — so the clause a card is told is stable
    between runs and the ledger re-derives byte for byte.
    """
    if rows is None:
        rows = rulings()
    by: dict = {}
    for row in rows:
        for line in row["roll_lines"]:
            by.setdefault(line["record"], []).append(row)
    return {record: group for record, group in by.items() if len(group) > 1}


def _named(row: dict) -> str:
    """A rival as a reader would go and find them: the name the town holds, then the card."""
    return "%s (%s)" % (row.get("name") or row["person_id"], row["person_id"])


def _and_list(parts: list) -> str:
    if len(parts) == 1:
        return parts[0]
    return "%s and %s" % (", ".join(parts[:-1]), parts[-1])


def shared_clause(row: dict, shared: dict | None = None) -> str:
    """Rule 6's sentence for one card, or "" where this card's line reaches nobody else."""
    if shared is None:
        shared = shared_records()
    said = []
    for line in row["roll_lines"]:
        group = shared.get(line["record"])
        if not group:
            continue
        rivals = [r for r in group if r["person_id"] != row["person_id"]]
        if not rivals:
            continue
        rules = {r["rule"] for r in group}
        under = ("under this same rule " if len(rules) == 1 else "")
        said.append(
            "%s is matched %sto %s, so it is met by %s townspeople of this name, and it says "
            "which of them it was about no more than it says it was about this one — the test "
            "that decided it is a surname and a given initial agreeing, which cannot tell them "
            "apart."
            % (line["record"], under, _and_list([_named(r) for r in rivals]),
               _COUNT_WORDS.get(len(group), str(len(group)))))
    if not said:
        return ""
    return " %s %s" % (SHARED_MARKER, " ".join(said))


def where(row: dict) -> list:
    """Where each line of this ruling sits, as a reader would go back to it."""
    return ["%s, printed page %s" % (line["record"], line["printed_page"])
            for line in row["roll_lines"]]


def _admission(line: dict) -> str:
    """The one clause the roll's four printed columns come to, said plainly."""
    when, how = line.get("admitted"), line.get("how_admitted")
    if when and how:
        return "admitted %s by %s" % (when, how)
    if when:
        return "admitted %s, the roll not printing how" % when
    if how:
        return "admitted by %s, the roll not printing when" % how
    return "the roll printing neither when nor how the member was admitted"


def paragraph(row: dict, shared: dict | None = None) -> str:
    """What one person's card is told, and the whole of it.

    `shared` is rule 6's index (T-0995); a caller with it already in hand passes it so the
    whole pass regroups the crosswalk once rather than once per card.
    """
    doc = load(CROSSWALK)
    lines = row["roll_lines"]
    as_read = ", ".join("“%s”" % line["as_read"] for line in lines)
    admissions = "; ".join(_admission(line) for line in lines)
    mrs = ""
    if any(line.get("a_married_womans_entry") for line in lines):
        mrs = (" THE LINE IS A MARRIED WOMAN'S ENTRY, and the crosswalk's own Mrs rule governs "
               "what it can have met: “a line flagged a_married_womans_entry that meets a MAN "
               "in the 1835 layer has met his name, not him: it corroborates that the name was "
               "a Chicago name in the 1840s and it does not put that man on this roll.” The "
               "match is filed rather than suppressed, because a suppressed match is invisible "
               "and a flagged one can be argued with.")
    return (
        "%s The 1892 printed membership roll of the Second Presbyterian Church of Chicago, "
        "read line by line into this repository, carries %d line%s whose surname and given "
        "initial agree with this person's — %s (%s), %s. Under the rule that decided it: %s "
        "WHAT THE MATCH MINTS OR REGRADES: “%s”%s%s %s"
        % (MARKER, len(lines), "" if len(lines) == 1 else "s", as_read,
           "; ".join(where(row)), admissions, row["rule"].rstrip(".") + ".",
           (doc.get("mints_or_regrades") or "").strip(), mrs,
           shared_clause(row, shared), LADDER_LIMIT))


# --- the ledger ------------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = rulings()
    shared = shared_records(rows)
    xw = load(CROSSWALK)
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by tools/spend_second_presbyterian_roll.py (T-0992). Which of the "
            "Second Presbyterian roll crosswalk's `matched` rulings were written onto the "
            "card they name, and what each card was told. It is a record of WRITES, not of "
            "adjudications — the adjudication is second_presbyterian_crosswalk.json — and it "
            "deliberately carries no 'crosswalk' in its name so that "
            "measure_research_spend.py does not count a write as a second ruling."),
        "generated_by": "tools/spend_second_presbyterian_roll.py",
        "ticket": "T-0992",
        "source_id": SOURCE_ID,
        "reads": ["data/research/church/second_presbyterian_crosswalk.json"],
        "writes": "data/residents/households/*.json — persons[].sources and persons[].note",
        "carry_rule": xw.get("mints_or_regrades"),
        "counts": {
            "roll_records": (xw.get("counts") or {}).get("roll_records"),
            "matched": len(xw.get("matched") or []),
            "ambiguous_not_spent": len(xw.get("ambiguous") or []),
            "refused_not_spent": len(xw.get("refused") or []),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "married_womens_entries": sum(
                1 for r in rows if any(l.get("a_married_womans_entry") for l in r["roll_lines"])),
            # Rule 6 (T-0995). `matched` is indexed by person and cannot state either of these.
            "roll_lines_met_by_more_than_one_person": len(shared),
            "cards_naming_the_others_on_their_line": sum(
                1 for r in rows if shared_clause(r, shared)),
            "grades_changed": 0,
        },
        "people": [
            {"person_id": r["person_id"], "household_id": r["household_id"],
             "resident_name": r.get("name"), "grade_left_alone": r.get("grade"),
             "rule": r["rule"], "roll_lines": where(r),
             "as_read": [l["as_read"] for l in r["roll_lines"]],
             "others_on_the_same_roll_line": sorted(
                 other["person_id"]
                 for line in r["roll_lines"]
                 for other in shared.get(line["record"], [])
                 if other["person_id"] != r["person_id"]),
             "told": paragraph(r, shared)}
            for r in rows
        ],
    }


# --- the write -------------------------------------------------------------------------

def apply_to_person(person: dict, row: dict, shared: dict | None = None) -> bool:
    """The ONLY mutation this tool performs. Two keys, and rule 2 is held here."""
    changed = False
    if SOURCE_ID not in (person.get("sources") or []):
        person["sources"] = (person.get("sources") or []) + [SOURCE_ID]
        changed = True
    note = (person.get("note") or "").strip()
    want = paragraph(row, shared)
    if MARKER not in note:
        person["note"] = (note + " " + want).strip()
        changed = True
    elif _mine(note) != want:
        # A paragraph that no longer says what the crosswalk says is worse than none: it is
        # this pass's own words, stale, over a ruling that has since moved (T-0700).
        person["note"] = (_without_mine(note) + " " + want).strip()
        changed = True
    return changed


def _span(note: str) -> tuple[int, int]:
    # T-0976: another evidence writer may append after this paragraph. Owning everything from
    # MARKER to end-of-note silently deleted Fergus's later lists on the census pass.
    start = note.index(MARKER)
    end = note.find(LADDER_LIMIT, start)
    if end < 0:
        raise ValueError("the roll paragraph has no known closing boundary; "
                         "refusing to discard other evidence")
    return start, end + len(LADDER_LIMIT)


def _mine(note: str) -> str:
    start, end = _span(note)
    return note[start:end].strip()


def _without_mine(note: str) -> str:
    start, end = _span(note)
    return " ".join(part.strip() for part in (note[:start], note[end:]) if part.strip())


def retract_from_person(person: dict) -> bool:
    """The exact inverse of `apply_to_person`, for a card no ruling reaches any more.

    The roll re-derives whenever the town gains a card — T-0960's Mrs C. Taylor took the
    matched rows from 82 to 83 — and the same re-derivation can take a match away again when
    a second person of the same surname and initial arrives and the pair stops being unique.
    A withdrawn ruling must take its paragraph AND its citation off, or `strays` sees a
    sentence nothing on the card can account for and only a hand can clear it."""
    changed = False
    note = (person.get("note") or "").strip()
    if MARKER in note:
        person["note"] = _without_mine(note)
        changed = True
        # Only when this pass's own paragraph came off: the citation is what `apply` adds
        # beside it, and stripping one without the other leaves a source behind a card that
        # nothing on the card can account for.
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
        print("Second Presbyterian roll: withdrawn from %d resident record(s)" % dropped)
    return dropped


def apply(quiet: bool = False) -> int:
    touched = 0
    rows = rulings()
    shared = shared_records(rows)
    for row in rows:
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        if not path.exists():
            continue
        hh = load(path)
        for person in hh.get("persons") or []:
            if person.get("id") != row["person_id"]:
                continue
            if apply_to_person(person, row, shared):
                touched += 1
                dump(path, hh)
    if not quiet:
        print("Second Presbyterian roll: written onto %d resident record(s)" % touched)
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


def _gaps_over(row: dict, person: dict, shared: dict | None = None) -> list:
    """gaps() for one already-loaded person — what the self-test needs and the gate reuses."""
    out = []
    who = "%s/%s" % (row["household_id"], row["person_id"])
    if SOURCE_ID not in (person.get("sources") or []):
        out.append("%s — matched by the crosswalk and the card does not cite %s"
                   % (who, SOURCE_ID))
    note = person.get("note") or ""
    if MARKER not in note:
        out.append("%s — matched by the crosswalk and the card carries no paragraph" % who)
    elif _mine(note) != paragraph(row, shared):
        # T-0700's lesson, which T-0698 learned the same way: `gaps` asked whether a
        # paragraph was PRESENT and never whether it was RIGHT, so a card kept saying a
        # thing its ruling had stopped saying. A stale paragraph is a gate failure here.
        out.append("%s — the paragraph on the card no longer says what the crosswalk says"
                   % who)
    return out


def gaps(rows: list) -> list:
    """Every ruling has to be ON the record it names, or the ruling is only a file."""
    shared = shared_records(rows)
    bad = []
    for row in rows:
        person = _person(row)
        if person is None:
            bad.append("%s/%s — the record the ruling names does not exist"
                       % (row["household_id"], row["person_id"]))
            continue
        bad.extend(_gaps_over(row, person, shared))
    return bad


def _rivals_said(row: dict, person: dict, shared: dict) -> list:
    """Rule 6 over one already-loaded person — what the self-test needs and the gate reuses.

    `gaps` would already fire on any of this, because a paragraph that omits the clause is a
    paragraph that no longer says what the crosswalk says. It would fire saying THAT, though,
    and the reader would have to diff two paragraphs to find out which sentence moved. This
    asks rule 6's question in rule 6's own words, and names the card that is unsaid."""
    who = "%s/%s" % (row["household_id"], row["person_id"])
    note = person.get("note") or ""
    if MARKER not in note:
        return []            # `gaps` owns the card with no paragraph at all.
    mine = _mine(note)
    others = sorted(other["person_id"]
                    for line in row["roll_lines"]
                    for other in shared.get(line["record"], [])
                    if other["person_id"] != row["person_id"])
    if not others:
        if SHARED_MARKER in mine:
            return ["%s — names others on its roll line and no other person is matched to it"
                    % who]
        return []
    if SHARED_MARKER not in mine:
        return ["%s — its roll line is met by %d townsperson(s) more and the card does not "
                "say so: %s" % (who, len(others), ", ".join(others))]
    unsaid = [pid for pid in others if pid not in mine]
    if unsaid:
        return ["%s — says its roll line is shared and does not name %s"
                % (who, ", ".join(unsaid))]
    return []


def unsaid_rivals(rows: list) -> list:
    """Rule 6 (T-0995), over the cards as they stand: a roll line met by more than one
    townsperson names the others on every one of their cards, and only on theirs."""
    shared = shared_records(rows)
    bad = []
    for row in rows:
        person = _person(row)
        if person is None:
            continue        # `gaps` owns the missing record.
        bad.extend(_rivals_said(row, person, shared))
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


def unspendable() -> list:
    """The line rule 1 exists to hold: nothing outside `matched` may reach a card.

    A card cited by an `ambiguous` or `refused` row and carrying this pass's paragraph would
    mean a rival still standing had been spent — the one thing the crosswalk's ladder is for.
    Checked rather than trusted, because `rulings()` is the only thing between them."""
    doc = load(CROSSWALK)
    matched = {r.get("person_id") for r in doc.get("matched") or []}
    bad = []
    for key in ("ambiguous", "refused"):
        for row in doc.get(key) or []:
            pid, hh = row.get("person_id"), row.get("household_id")
            if not pid or pid in matched or not hh:
                continue
            path = HOUSEHOLDS / ("%s.json" % hh)
            if not path.exists():
                continue
            for person in load(path).get("persons") or []:
                if person.get("id") == pid and MARKER in (person.get("note") or ""):
                    bad.append("%s/%s — %s by the crosswalk and carries this pass's paragraph"
                               % (hh, pid, key))
    return bad


def check(quiet: bool = False) -> int:
    rows = rulings()
    if not LEDGER.exists():
        print("   the ledger is missing: %s" % LEDGER.relative_to(ROOT))
        return 1
    if load(LEDGER) != ledger_doc():
        print("   %s no longer re-derives from the crosswalk — re-run the tool"
              % LEDGER.relative_to(ROOT))
        return 1
    bad = gaps(rows) + strays(rows) + doubles() + unspendable() + unsaid_rivals(rows)
    if bad:
        for line in bad[:20]:
            print("   %s" % line)
        if len(bad) > 20:
            print("   …and %d more" % (len(bad) - 20))
        return 1
    if not quiet:
        shared = shared_records(rows)
        print("Second Presbyterian roll: %d matched ruling(s) on %d card(s), no strays, "
              "none written twice, no refusal spent; %d roll line(s) met by more than one "
              "townsperson, named on all %d of their cards"
              % (len(rows), len(rows), len(shared),
                 sum(1 for r in rows if shared_clause(r, shared))))
    return 0


def report() -> int:
    rows = rulings()
    shared = shared_records(rows)
    print("%-30s %-26s %-9s %-6s %-6s %s"
          % ("household", "person", "grade", "Mrs?", "share", "roll line"))
    print("-" * 138)
    for r in rows:
        mrs = "yes" if any(l.get("a_married_womans_entry") for l in r["roll_lines"]) else ""
        met = max([len(shared.get(l["record"], ())) for l in r["roll_lines"]] or [0])
        print("%-30s %-26s %-9s %-6s %-6s %s"
              % (r["household_id"], r["person_id"], r.get("grade"), mrs,
                 ("of %d" % met) if met else "", "; ".join(where(r))))
    print("-" * 138)
    print("%d people, %d household(s), %d married-woman entr(ies); nothing minted, no grade moved"
          % (len(rows), len({r["household_id"] for r in rows}),
             sum(1 for r in rows
                 if any(l.get("a_married_womans_entry") for l in r["roll_lines"]))))
    print("rule 6: %d roll line(s) met by more than one townsperson, reaching %d card(s)"
          % (len(shared), sum(1 for r in rows if shared_clause(r, shared))))
    for record, group in sorted(shared.items()):
        line = [l for l in group[0]["roll_lines"] if l["record"] == record][0]
        print("   %s  “%s”" % (record, line["as_read"]))
        for r in group:
            print("      %s" % _named(r))
    return 0


def self_test() -> int:
    fails = []
    fired = 0

    def fires(label, ok):
        # Counted rather than totted up by hand: the printed figure used to be a literal
        # `27 + 5 * len(rows)` kept in step with the body by memory, and rule 6 (T-0995)
        # fires a different number of assertions on a shared line than on a lone one, so
        # no literal can be right for both.
        nonlocal fired
        fired += 1
        if not ok:
            fails.append(label)

    doc = load(CROSSWALK)
    rows = rulings()
    fires("the crosswalk reaches at least one person", bool(rows))
    fires("rule 1: only `matched` is read",
          {r["person_id"] for r in rows} <= {r.get("person_id") for r in doc["matched"]})
    fires("rule 1: no ambiguous row is spent",
          not ({r.get("person_id") for r in doc.get("ambiguous") or []}
               & {r["person_id"] for r in rows}
               - {r.get("person_id") for r in doc["matched"]}))
    fires("rule 4: one row per person",
          len({r["person_id"] for r in rows}) == len(rows))
    fires("every matched row states the one source id this pass writes",
          all(r.get("source_id") == SOURCE_ID for r in doc["matched"]))

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
    fires("rule 3: the grade does not move", after["grade"] == "attested")
    fires("rule 2: present_on_scene_date does not move",
          after["present_on_scene_date"] == {"value": "present"})

    # Idempotence, and the stale-paragraph rule.
    again = json.loads(json.dumps(after))
    fires("re-running writes nothing", apply_to_person(again, row) is False)
    fires("…and leaves exactly one paragraph", again["note"].count(MARKER) == 1)
    fires("a clean record has no gap", _gaps_over(row, again) == [])

    sibling = "CENSUS: independently written later evidence survives."
    following = json.loads(json.dumps(after))
    following["note"] += " " + sibling
    fires("another writer's following paragraph is not roll drift",
          apply_to_person(following, row) is False)
    following["note"] = following["note"].replace("The 1892 printed membership roll",
                                                  "The 1893 printed membership roll")
    fires("refresh preserves the following writer's evidence",
          apply_to_person(following, row) and sibling in following["note"])
    fires("withdrawal preserves the following writer's evidence",
          retract_from_person(following) and following["note"] == before["note"] + " " + sibling)

    stale = json.loads(json.dumps(after))
    stale["note"] = stale["note"].replace("The 1892 printed membership roll",
                                          "The 1893 printed membership roll")
    fires("a stale paragraph is a gap", len(_gaps_over(row, stale)) == 1)
    fires("…and is rewritten rather than doubled",
          apply_to_person(stale, row) and stale["note"].count(MARKER) == 1)
    fires("…to what the crosswalk now says", _gaps_over(row, stale) == [])

    missing = json.loads(json.dumps(before))
    fires("a card citing nothing is a gap", len(_gaps_over(row, missing)) == 2)

    withdrawn = json.loads(json.dumps(after))
    fires("a withdrawn ruling takes its paragraph off", retract_from_person(withdrawn)
          and MARKER not in (withdrawn.get("note") or ""))
    fires("…and its citation with it", SOURCE_ID not in (withdrawn.get("sources") or []))
    fires("…and leaves the record otherwise exactly as it was found", withdrawn == before)
    fires("withdrawing twice writes nothing", retract_from_person(withdrawn) is False)
    untouched = json.loads(json.dumps(before))
    fires("a card this pass never wrote is left alone",
          retract_from_person(untouched) is False and untouched == before)

    # Rule 5, and the two things every paragraph must carry.
    shared = shared_records(rows)
    mrs_seen = plain_seen = False
    shared_seen = unshared_seen = False
    for r in rows:
        text = paragraph(r, shared)
        fires("every paragraph quotes the crosswalk's own mints-or-regrades sentence",
              "cannot place a person in the town of July 1835" in text)
        fires("every paragraph carries the ladder limit", LADDER_LIMIT in text)
        fires("every paragraph names its roll line", all(w in text for w in where(r)))
        fires("no paragraph claims an 1835 residency",
              "1835 resident" not in text and "resident in 1835" not in text)
        if any(l.get("a_married_womans_entry") for l in r["roll_lines"]):
            mrs_seen = True
            fires("rule 5: a married woman's entry says whose name it met",
                  "MARRIED WOMAN'S ENTRY" in text and "has met his name, not him" in text)
        else:
            plain_seen = True
            fires("rule 5: a plain line does not carry the Mrs caution",
                  "MARRIED WOMAN'S ENTRY" not in text)
        others = sorted(other["person_id"]
                        for line in r["roll_lines"]
                        for other in shared.get(line["record"], [])
                        if other["person_id"] != r["person_id"])
        if others:
            shared_seen = True
            fires("rule 6: a shared roll line says so", SHARED_MARKER in text)
            fires("rule 6: …and names every other townsperson matched to it",
                  all(pid in text for pid in others))
            fires("rule 6: …and counts them, this card included",
                  _COUNT_WORDS[len(others) + 1] + " townspeople of this name" in text)
            fires("rule 6: …and names none of them as this card",
                  text.count(r["person_id"]) == 0 or "(%s)" % r["person_id"] not in
                  text.split(SHARED_MARKER)[1])
        else:
            unshared_seen = True
            fires("rule 6: an unshared line carries no rivals clause",
                  SHARED_MARKER not in text)
    fires("rule 5 is exercised on both kinds of line", mrs_seen and plain_seen)
    fires("rule 6 is exercised on both kinds of line", shared_seen and unshared_seen)

    # Rule 6's index, and the gate that holds it — over synthetic cards, so the assertions
    # fire whatever the town currently looks like.
    fires("rule 6: the index keeps only records more than one row names",
          all(len(g) > 1 for g in shared.values()))
    fires("rule 6: every row in the index is a matched row",
          {x["person_id"] for g in shared.values() for x in g} <= {r["person_id"] for r in rows})
    fires("rule 6: the index is stable under re-derivation", shared_records(rows) == shared)

    a = {"name": "A Cook", "person_id": "cook_a", "household_id": "hh_cook_a",
         "grade": "inferred", "source_id": SOURCE_ID, "rule": "R.",
         "roll_lines": [{"record": "second_presb_9001", "as_read": "Cook, Mrs. J. L.",
                         "admitted": "1843-01-05", "how_admitted": "letter",
                         "printed_page": 183, "a_married_womans_entry": True}]}
    b = json.loads(json.dumps(a))
    b.update(name="B Cook", person_id="cook_b", household_id="hh_cook_b")
    lone = json.loads(json.dumps(a))
    lone.update(name="C Lone", person_id="lone_c", household_id="hh_lone_c")
    lone["roll_lines"][0]["record"] = "second_presb_9002"
    pair = shared_records([a, b, lone])
    fires("rule 6: two rows on one record are shared and a row alone is not",
          set(pair) == {"second_presb_9001"} and len(pair["second_presb_9001"]) == 2)
    fires("rule 6: the clause names the other and not this one",
          "cook_b" in shared_clause(a, pair) and "(cook_a)" not in shared_clause(a, pair))
    fires("rule 6: a row whose record nobody else names gets no clause",
          shared_clause(lone, pair) == "")

    card = {"id": "cook_a", "sources": [SOURCE_ID], "note": paragraph(a, pair)}
    fires("rule 6: a card that names its rivals passes", _rivals_said(a, card, pair) == [])
    stripped = {"id": "cook_a", "sources": [SOURCE_ID],
                "note": paragraph(a, pair).replace(shared_clause(a, pair), "")}
    fires("rule 6: a card whose clause was struck out is refused",
          any("does not say so" in m for m in _rivals_said(a, stripped, pair)))
    renamed = {"id": "cook_a", "sources": [SOURCE_ID],
               "note": paragraph(a, pair).replace("cook_b", "cook_z")}
    fires("rule 6: a card naming the wrong rival is refused",
          any("does not name cook_b" in m for m in _rivals_said(a, renamed, pair)))
    # Inside this pass's own span, not after it: a SHARED_MARKER appended past LADDER_LIMIT
    # is another writer's sentence and rule 6 must not read it as this card's claim.
    invented = {"id": "lone_c", "sources": [SOURCE_ID],
                "note": paragraph(lone, pair).replace(
                    LADDER_LIMIT, SHARED_MARKER + " second_presb_9002 … " + LADDER_LIMIT)}
    fires("rule 6: a card claiming a share its line does not have is refused",
          any("no other person is matched" in m for m in _rivals_said(lone, invented, pair)))
    fires("rule 6: a card with no paragraph is left to `gaps`",
          _rivals_said(a, {"id": "cook_a", "note": ""}, pair) == [])
    fires("rule 6: the clause is inside this pass's own span and not after it",
          SHARED_MARKER in _mine(card["note"]))
    later = {"id": "lone_c", "sources": [SOURCE_ID],
             "note": paragraph(lone, pair) + " " + SHARED_MARKER + " another writer's words."}
    fires("rule 6: a later writer's sentence past the ladder limit is not this card's claim",
          _rivals_said(lone, later, pair) == [])

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
    print("Second Presbyterian roll self-test: %d assertion(s) over %d ruling(s), "
          "%d failure(s)" % (fired, len(rows), len(fails)))
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
