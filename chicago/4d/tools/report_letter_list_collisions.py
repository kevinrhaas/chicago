#!/usr/bin/env python3
"""Every surname collision the corrected letter-list reading uncovered, derived twice.

WHY THIS EXISTS (T-0660). The post office printed a name in either order and, until
T-0638, `mint_letter_list_residents.surname()` read the LAST token as the family name
in both. `Mills Joel C.` was therefore minted under the surname `c` and `Joel C. Mills`
would have been minted under `mills`, and the pass's refusals 7 and 8 — one household
per surname in the town, one per surname in this pass — never saw the two printings as
landing on one family name. T-0638 corrected the reading and deliberately did not act
on what it revealed, because acting RETIRES RECORDS.

WHAT THIS TOOL IS. The instrument T-0660's first acceptance clause asks for: the pairs
DERIVED rather than hand-assembled, by running the pass's own `mint()` twice over the
same committed tree — once with the pre-T-0638 reading of a printed name, once with the
corrected one — and reporting every candidate the corrected reading refuses that the old
one accepted, with the two printings side by side and the record that holds the surname
instead.

WHAT IT DELIBERATELY DOES NOT DO. It retires nothing and writes nothing into
`data/residents/`. Which of a colliding pair survives is not a question a tool may
answer here: the pairs are not all duplicates. `Joel C. Mills` and `Philo C. Mills` are
two different men who may not both hold `mills`, and the pass's `rank()` — which sorts
single-return names by the NEWEST return — would keep `B. Osborn` over `Wm. Osborn`, an
initial over a written given name. Retiring a record removes a person from the town, so
the rule that picks the survivor is the owner's ruling, and this report is what makes it
a decidable one.

THE SECOND FINDING, and the reason this report exists as a file rather than a paragraph
in a PR: the committed letter-list cohort is a long way out of step with what its own
tool now derives, and only a small part of that is this fault. `check.sh` runs the
pass's `--gate` and not its `--check`, so the drift has never been red. The report
counts it, and splits it by cause.

    python3 tools/report_letter_list_collisions.py            # print the report
    python3 tools/report_letter_list_collisions.py --write    # write the committed copy
    python3 tools/report_letter_list_collisions.py --check    # committed copy still true?
    python3 tools/report_letter_list_collisions.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mint_letter_list_residents as m  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/RESEARCH/letter-list-surname-collisions.md"


# ---------------------------------------------------------------------------
# the two readings
# ---------------------------------------------------------------------------

def pre_t0638_surname(name: str) -> str:
    """The family name as the pass read it BEFORE T-0638: the last printed token.

    Kept here rather than in the pass, because the pass has one reading and this
    report needs two. It is the exact body of `surname()` as of 9d962929, with the
    apostrophe handling of the current one so that fault B (T-0638's other half)
    does not leak into a diff that is about fault A.
    """
    parts = m.words(name)
    if not parts:
        return ""
    if "," in name:
        head = m.words(name.partition(",")[0])
        picked = head[-1] if head else parts[0]
    else:
        picked = parts[-1]
    return picked.lower().strip("'").replace("'", "")


def mint_with(reading, docs: dict, index: dict):
    """`mint()` run under a given reading of a printed name.

    Every one of the pass's own rules is used unchanged — the pool, the ranking and
    all nine refusals — because a second implementation of them would be measuring
    something other than the pass.
    """
    original = m.surname
    m.surname = reading
    try:
        return m.mint(docs, index)
    finally:
        m.surname = original


# ---------------------------------------------------------------------------
# what a record carries, which is what survivorship turns on
# ---------------------------------------------------------------------------

def committed_letter_list(docs: dict) -> dict:
    """Committed letter-list households, keyed by the display name on the card."""
    out = {}
    for path, doc in docs.items():
        if m.minted_by(path, doc, "letter_list", m.PREFIX):
            for person in doc.get("persons") or []:
                out[person["name"]] = (path.stem, doc, person)
    return out


def attachment(doc: dict, person: dict) -> list[str]:
    """The downstream things a record carries that a retirement would strand."""
    carried = []
    research = person.get("resident_research")
    if research:
        carried.append(f"research row {research.get('ticket', '?')}"
                       f" ({research.get('outcome', '?')})")
    directories = doc.get("directories") or {}
    for source in directories.get("sources") or []:
        carried.append(f"directory {source}")
    for key in ("census_1840", "bridge_1840", "crosswalk"):
        if doc.get(key) or person.get(key):
            carried.append(key)
    return carried


def holder_of(fam: str, docs: dict, accepted_names: dict) -> str:
    """Who holds the family name the refusal names — the survivor, whoever they are.

    Two shapes, because the two refusals mean different things. Refusal 7 ("the town
    already names a X") points OUTSIDE this pass, at a household some other pass
    minted. Refusal 8 ("surname already minted") points at a candidate this same pass
    accepted earlier in `rank()` order.
    """
    outside = []
    for path, doc in sorted(docs.items()):
        if m.minted_by(path, doc, "letter_list", m.PREFIX):
            continue
        for person in doc.get("persons") or []:
            if m.surname(person.get("name") or "") == fam:
                outside.append(f"{person['name']} ({path.stem})")
    if outside:
        return "; ".join(outside[:3]) + (" …" if len(outside) > 3 else "")
    inside = [f"{name}" for name, f in accepted_names.items() if f == fam]
    return "; ".join(sorted(inside)) or "—"


# ---------------------------------------------------------------------------
# the derivation
# ---------------------------------------------------------------------------

def derive() -> dict:
    docs = {p: m.load(p) for p in sorted(m.HOUSEHOLDS.glob("*.json"))}
    index = m.load(m.INDEX)

    new_accepted, new_refused = mint_with(m.surname, docs, index)
    old_accepted, _old_refused = mint_with(pre_t0638_surname, docs, index)

    new_by_id = {cand["id"]: cand for cand, _ in new_accepted}
    old_by_id = {cand["id"]: cand for cand, _ in old_accepted}
    reasons = {cid: reason for cid, _name, _n, reason in new_refused}
    returns = {cand["id"]: len(m.returns_of(gaz["mentions"]))
               for cand, gaz in new_accepted}
    printings = {cand["id"]: len(gaz["mentions"]) for cand, gaz in new_accepted}
    for cand, gaz in old_accepted:
        returns.setdefault(cand["id"], len(m.returns_of(gaz["mentions"])))
        printings.setdefault(cand["id"], len(gaz["mentions"]))

    accepted_names = {m.display(cand["name"]): m.surname(cand["name"])
                      for cand, _ in new_accepted}
    committed = committed_letter_list(docs)

    pairs = []
    for cid in sorted(set(old_by_id) - set(new_by_id)):
        printed = old_by_id[cid]["name"]
        shown = m.display(printed)
        stem, doc, person = committed.get(shown, (None, None, None))
        pairs.append({
            "printed": printed,
            "display": shown,
            "old_surname": pre_t0638_surname(printed),
            "new_surname": m.surname(printed),
            "reason": reasons.get(cid, "—"),
            "committed": stem,
            "returns": returns.get(cid, 0),
            "printings": printings.get(cid, 0),
            "carries": attachment(doc, person) if doc else [],
            "holder": holder_of(m.surname(printed), docs, accepted_names),
        })

    admitted = []
    for cid in sorted(set(new_by_id) - set(old_by_id)):
        printed = new_by_id[cid]["name"]
        admitted.append({
            "printed": printed,
            "display": m.display(printed),
            "old_surname": pre_t0638_surname(printed),
            "new_surname": m.surname(printed),
            "returns": returns.get(cid, 0),
            "printings": printings.get(cid, 0),
        })

    # the committed cohort against its own derivation, split by cause
    shown_ids: set[str] = set()
    derived_ids = set()
    for cand, _gaz in new_accepted:
        hid = m.household_id(cand["name"], m.PREFIX, "letter_list", docs, shown_ids)
        shown_ids.add(hid)
        derived_ids.add(hid)
    committed_ids = {path.stem for path, doc in docs.items()
                     if m.minted_by(path, doc, "letter_list", m.PREFIX)}
    derived_names = {m.display(cand["name"]) for cand, _ in new_accepted}
    refused_by_name = {m.display(name): reason
                       for _cid, name, _n, reason in new_refused}
    this_fault = {p["display"] for p in pairs}
    causes: dict[str, int] = {}
    for hid in sorted(committed_ids - derived_ids):
        name = docs[m.HOUSEHOLDS / f"{hid}.json"]["persons"][0]["name"]
        if name in derived_names:
            key = "the record stands under a different id (a rename, not a retirement)"
        elif name in this_fault:
            key = "THIS FAULT — the corrected reading collides it with another record"
        elif name in refused_by_name:
            key = ("the town gained this surname from another pass after the mint "
                   f"({m.reason_key(refused_by_name[name])})")
        else:
            key = "no longer in the pool the register offers"
        causes[key] = causes.get(key, 0) + 1

    return {
        "pool": len(new_accepted) + len(new_refused),
        "new_accepted": len(new_accepted),
        "old_accepted": len(old_accepted),
        "committed": len(committed_ids),
        "derived": len(derived_ids),
        "pairs": pairs,
        "admitted": admitted,
        "causes": causes,
        "residual": residual_comma_fault(docs, index),
    }


def residual_comma_fault(docs: dict, index: dict) -> list[dict]:
    """Printings the CORRECTED reading still takes a given name off as the surname.

    `surname_is_first_token()` fires when the token the plain rule lands on is an
    initial and some earlier token is a full word. With a comma in the printing that
    test can pick the token before the comma when the family name is the one after
    it: `Augustus H, Conant` reads `augustus`. Reported, not fixed — a change to
    `surname()` re-derives the whole cohort, which is the very thing T-0660 exists to
    put to the owner first.
    """
    own = frozenset(doc["head"] for doc in docs.values()
                    if doc.get("source_pass") == "letter_list")
    out = []
    for cand in m.letter_list_pool(m.load(m.REGISTER), own):
        name = cand["name"]
        if "," not in name or not m.surname_is_first_token(name):
            continue
        head = m.words(name.partition(",")[0])
        tail = m.words(name.partition(",")[2])
        if not tail or not m.full_word(tail[0]):
            continue          # nothing after the comma that could be a family name
        if m.surname(name) == tail[0].lower().strip("'").replace("'", ""):
            continue          # already reading the token after the comma
        if m.UNCERTAIN.search(name):
            continue          # garbled, and refusal 2 drops it before this matters
        out.append({"printed": name, "reads": m.surname(name),
                    "after_the_comma": tail[0], "head": " ".join(head)})
    return out


# ---------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------

def lines(d: dict) -> list[str]:
    out = [
        "# The surname collisions the corrected letter-list reading uncovered",
        "",
        "DERIVED, NOT WRITTEN. Every number and every row below is produced by",
        "`tools/report_letter_list_collisions.py`, which runs",
        "`mint_letter_list_residents.mint()` twice over the committed tree — once under the",
        "pre-T-0638 reading of a printed name, once under the corrected one — and reports the",
        "difference. `--check` re-derives it and fails if this file has drifted from what the",
        "tree now says, so it cannot quietly go stale.",
        "",
        "T-0843 MOVED ONE ROW OUT OF THIS REPORT AND THE REASON IS WORTH READING. The pass",
        "now consults the cross-domain identity master before it writes a card, so",
        "`Norton N. R.` is refused under BOTH readings — the master resolves the initials",
        "onto the committed Nelson R. Norton whichever token the old rule took for a",
        "surname. It was never a difference between the two readings; the surname test was",
        "simply too blunt to see it under one of them. The count below fell by one",
        "accordingly, and nothing was retired to make that happen.",
        "",
        "T-0660 asks for this list before anything is retired, and the reason is in the third",
        "section: the pass's own ranking would not always keep the better record, and two of",
        "these collisions are not duplicates at all but two different men who cannot both hold",
        "one family name.",
        "",
        "## The two readings, over the same pool",
        "",
        f"* the pool the register offers this pass: **{d['pool']}** candidates",
        f"* accepted under the pre-T-0638 reading: **{d['old_accepted']}**",
        f"* accepted under the corrected reading: **{d['new_accepted']}**",
        f"* candidates the correction REFUSES that the old reading accepted: "
        f"**{len(d['pairs'])}**",
        f"* candidates the correction ADMITS that the old reading refused: "
        f"**{len(d['admitted'])}**",
        "",
        "## The collisions — what the paper printed, and who holds the surname instead",
        "",
        "`old` and `new` are the family name each reading takes off the printing. `holds it`",
        "is the record the refusal defers to — the survivor, if a survivor is what the owner",
        "rules for. `carries` is what a retirement would strand.",
        "",
        "| printed | as a card shows it | old | new | refused because | holds it | returns | carries |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in d["pairs"]:
        out.append(
            f"| `{p['printed']}` | {p['display']} | `{p['old_surname']}` | "
            f"`{p['new_surname']}` | {p['reason']} | {p['holder']} | {p['returns']} | "
            f"{', '.join(p['carries']) or '—'} |")
    out += [
        "",
        "## Why a tool may not pick the survivor",
        "",
        "* **They are not all duplicates.** `Joel C. Mills` and `Philo C. Mills` are two",
        "  different men. Refusal 8 is a rule about how much one pass may assert on a family",
        "  name, not a statement that two records are one person — so applying it here",
        "  removes a person rather than merging two.",
        "* **`rank()` is blind to how good a record is.** It orders single-return names by",
        "  the NEWEST return, so where two printings of one surname both stand, the survivor",
        "  is whichever letter was printed later — not the one with the fuller name, the",
        "  research row or the directory match.",
        "* **The loser can be the better-attested record.** The `carries` column above is the",
        "  measure of that, and it is not empty.",
        "",
        "## The committed cohort against its own derivation",
        "",
        f"The tree holds **{d['committed']}** letter-list households. The pass, run today",
        f"against that same tree, derives **{d['derived']}**. `check.sh` runs this pass's",
        "`--gate` and not its `--check`, so the gap has never been red. Split by cause:",
        "",
        "| households | cause |",
        "|---|---|",
    ]
    for cause, n in sorted(d["causes"].items(), key=lambda kv: -kv[1]):
        out.append(f"| {n} | {cause} |")
    out += [
        "",
        "**This is the finding that resizes T-0660.** The ticket was filed believing the",
        "retirements were the collisions. Most of them are not: they are records whose",
        "surname the town acquired from a LATER pass, long after this cohort was minted, and",
        "retiring them is a separate ruling about a separate rule.",
        "",
        "## The candidates the correction admits",
        "",
        "The other half of the same diff, and none of them is committed today.",
        "",
        "| printed | as a card would show it | old | new | returns |",
        "|---|---|---|---|---|",
    ]
    for a in d["admitted"]:
        out.append(f"| `{a['printed']}` | {a['display']} | `{a['old_surname']}` | "
                   f"`{a['new_surname']}` | {a['returns']} |")
    out += [
        "",
        "## A residual fault in the corrected reading",
        "",
        "Reported here rather than fixed, because a change to `surname()` re-derives the",
        "whole cohort — the thing this ticket exists to put to the owner before it happens.",
        "",
    ]
    if d["residual"]:
        out += ["| printed | reads the surname as | after the comma |", "|---|---|---|"]
        for r in d["residual"]:
            out.append(f"| `{r['printed']}` | `{r['reads']}` | `{r['after_the_comma']}` |")
        out += [
            "",
            "A comma says the family name is the group BEFORE it. When that group ends on an",
            "initial, `surname_is_first_token()` fires and takes the first full word of the",
            "whole printing — the given name — instead of the full word after the comma.",
        ]
    else:
        out.append("None in the pool as it stands.")
    out += [
        "",
        "---",
        "",
        "Generated by `tools/report_letter_list_collisions.py --write`. Do not hand-edit:",
        "`--check` compares this file against a fresh derivation.",
    ]
    return out


def render() -> str:
    return "\n".join(lines(derive())) + "\n"


def self_test() -> int:
    """The report is only worth anything if the two readings really are two."""
    failures = []
    if pre_t0638_surname("Mills Joel C.") != "c":
        failures.append("the pre-T-0638 reading no longer takes the trailing initial")
    if m.surname("Mills Joel C.") != "mills":
        failures.append("the corrected reading no longer takes the leading surname")
    if pre_t0638_surname("Joel C. Mills") != m.surname("Joel C. Mills"):
        failures.append("the two readings disagree on a printing they must agree on")
    d = derive()
    if not d["pairs"]:
        failures.append("no collision derived at all — the diff cannot be empty while "
                        "T-0660 is open")
    if any(p["new_surname"] == p["old_surname"] and "already minted" not in p["reason"]
           for p in d["pairs"]):
        failures.append("a collision is reported whose surname did not move and whose "
                        "refusal is not a within-pass one")
    for line in failures:
        print(f"   FAIL: {line}")
    if failures:
        return 1
    print(f"   OK: {len(d['pairs'])} collision(s), {len(d['admitted'])} admission(s), "
          f"both readings behave")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the committed report")
    ap.add_argument("--check", action="store_true",
                    help="re-derive and fail if the committed report has drifted")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    text = render()
    if args.write:
        REPORT.write_text(text, encoding="utf-8")
        print(f"   wrote {REPORT.relative_to(ROOT)}")
        return 0
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != text:
            print(f"   DRIFT: {REPORT.relative_to(ROOT)} is not what the tree derives")
            return 1
        print(f"   OK: {REPORT.relative_to(ROOT)} matches a fresh derivation")
        return 0
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
