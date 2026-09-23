#!/usr/bin/env python3
"""The four readings the Chicago American prints against itself, re-derived.

Ticket T-0305. The American is the corpus's SECOND witness to the town in the
twelve weeks around the scene date, and `data/sources/chicago_american_1835.json`
says what that is worth: *"corroboration or contradiction of a Democrat address,
which is worth more than either paper alone"*. Four times in its thirteen issues
the run contradicts ITSELF, or fails to resolve a street it printed — and in each
case the disagreement is between two brackets in a transcription rather than
between two claims about 1835.

The four, and the whole of the problem in one line each:

1. **The tailor's street.** Edward Burton's standing card, copy-dated 27 June
   1835, is set four times. Two printings read Franklin street, one reads Lake
   street, and one resolves to neither.
2. **Wm. Sabine's Water street.** North on 13 and 20 June, South on 4 July.
3. **John Dave[s]'s Water street.** The card set immediately below Sabine's, and
   it moves with it — North on 13 and 20 June, South on 4 July.
4. **The cross street of S. B. Cobb's saddlery.** Lake Street is printed in all
   three American cards and the cross street is lost in every one of them, so the
   American cannot corroborate or refute the Democrat's 1833 "Lake and Canal".

**Why a tool and not a paragraph.** Every one of those readings is a quotation
from a committed extraction file, and every one of them could be changed by a
later reading pass without anybody noticing that this ticket's question had been
answered — or silently made worse. So the four are DECLARED here with the exact
substring each printing has to carry, and re-derived against
`data/research/newspapers/extracted/` on every run of `tools/check.sh`. If a
printing stops reading the way this file says it reads, the gate fails and says
which one.

The negative half is re-derived too, and it is the half that matters for the ask:
**the Democrat's seventy-three issues supply no address for the tailor, for
Sabine or for Dave[s]** — they appear there only in post-office letter lists,
which give a name and never a street. That is what makes these four questions
image-bound rather than corpus-bound, and the day an extraction pass finds a
Democrat card for one of them, this assertion fires instead of the finding
quietly going stale.

    python3 tools/measure_american_contradictions.py           # the table
    python3 tools/measure_american_contradictions.py --gate    # exit 1 on drift
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = ROOT / "data" / "research" / "newspapers" / "extracted"

# `open_because` says WHY each question is open, because the two shapes need
# different assertions: three of them are printed disagreements and the fourth is
# a street the paper never resolves at all. Declaring which shape a question has
# stops "the readings agree now" being read as "the question closed".
DISAGREE = "the printings disagree"
UNRESOLVED = "no printing resolves it"

QUESTIONS = [
    {
        "id": "tailor_street",
        "subject": "Edward Burton's New Fashionable Tailoring Establishment",
        "gazetteer_id": "business_a_new_tailoring_establishment_chicago_june_1835",
        "question": "Franklin street or Lake street?",
        "open_because": DISAGREE,
        # One standing advertisement, one copy date (27 June 1835), four settings.
        "printings": [
            {"claim": "chicago_american_1835_06_27#c009", "page": 3, "column": 5,
             "reads": "Franklin", "carries": "Shop in Frank"},
            {"claim": "chicago_american_1835_07_25#c002", "page": 3, "column": 4,
             "reads": "Franklin", "carries": "[F]r[an]kli[n street]"},
            {"claim": "chicago_american_1835_08_01#c005", "page": 3, "column": 6,
             "reads": None, "carries": "Laks runlie"},
            {"claim": "chicago_american_1835_08_15#c002", "page": 3, "column": 6,
             "reads": "Lake", "carries": "lake - str[eet]"},
        ],
        # Surname tokens to hunt for in the Democrat. Burton is not in it at all.
        "democrat_tokens": ["Burton"],
        "democrat_supplies_address": False,
    },
    {
        "id": "sabine_water_street",
        "subject": "Wm. Sabine, storage, forwarding and commission merchant",
        "gazetteer_id": "business_wm_sabine_storage_forwarding_and_commission_merchant",
        "question": "North Water Street or South Water Street?",
        "open_because": DISAGREE,
        "printings": [
            {"claim": "chicago_american_1835_06_13#c005", "page": 3, "column": 5,
             "reads": "North Water", "carries": "N[ORT]H WATER [S]TREET"},
            {"claim": "chicago_american_1835_07_04#c002", "page": 4, "column": 4,
             "reads": "South Water",
             "carries": "WM. SABINE, Storage, Forwarding [and] Commission Mercha[nt]. "
                        "[SO]UTH WATER STREET"},
        ],
        "democrat_tokens": ["Sabine"],
        "democrat_supplies_address": False,
    },
    {
        "id": "dave_water_street",
        "subject": "John Dave[s], the card set below Sabine's",
        "gazetteer_id": "business_john_dave_north_water_street",
        "question": "North Water Street or South Water Street?",
        "open_because": DISAGREE,
        "printings": [
            {"claim": "chicago_american_1835_06_13#c006", "page": 3, "column": 5,
             "reads": "North Water", "carries": "NORT[H] WATER STREET"},
            {"claim": "chicago_american_1835_07_04#c002", "page": 4, "column": 4,
             "reads": "South Water",
             "carries": "JOHN DAVIS […] [S]OUTH WATER STREET"},
        ],
        "democrat_tokens": ["Dave", "Davis"],
        "democrat_supplies_address": False,
    },
    {
        "id": "cobb_cross_street",
        "subject": "S. B. Cobb's saddle, harness and trunk manufactory",
        "gazetteer_id": "business_s_b_cobb_saddle_harness_and_trunk_manufactory",
        "question": "Which cross street does Lake Street meet it at?",
        "open_because": UNRESOLVED,
        "printings": [
            {"claim": "chicago_american_1835_06_08#c007", "page": 3, "column": 5,
             "reads": None, "carries": "corner of Lake an[d] [uncertain: Amor."},
            {"claim": "chicago_american_1835_06_13#c016", "page": 3, "column": 6,
             "reads": None, "carries": "at his shop, corner [o]f [… ][st]re[et]s"},
            {"claim": "chicago_american_1835_07_11#c008", "page": 3, "column": 6,
             "reads": None, "carries": "corner of [L]ake [an]d the [uncertain: Balle"},
        ],
        # Cobb is the one of the four the Democrat DOES place — "corner of Lake
        # and Canal-streets", 1833 — which is why this question is about
        # corroboration rather than about a missing address.
        "democrat_tokens": ["Cobb"],
        "democrat_supplies_address": True,
    },
]

# The two North readings on 1835-06-20 are quoted from the transcription rather
# than from a claim: the column is interleaved badly enough that neither card was
# extracted as a claim of its own, and the project's identification of the upper
# one as Sabine's is POSITIONAL — the name is not legible on that setting. They
# are held here anyway, because they are two of the three printings that say
# North and dropping them would make the disagreement look narrower than it is.
TRANSCRIPTION_READINGS = [
    {"issue": "chicago_american_1835_06_20", "line": 346, "reads": "North Water",
     "carries": "NORTH WATER STRERT",
     "whose": "Sabine's, by position in the column — the name is not legible here"},
    {"issue": "chicago_american_1835_06_20", "line": 360, "reads": "North Water",
     "carries": "NORTH WaTEM sTRERT",
     "whose": "John Davik['s]', named two lines above"},
]


def load_issue(issue_id: str) -> dict:
    path = EXTRACTED / f"{issue_id}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def text_path(issue_id: str) -> Path:
    return ROOT / "data" / "research" / "newspapers" / "text" / f"{issue_id}.txt"


def democrat_addresses(tokens: list[str]) -> list[tuple[str, str, str]]:
    """Democrat claims that name one of `tokens` AND carry a placement.

    A letter-list line gives a name and never a street, so the test is not "is he
    mentioned" but "does the mention come with an address". Anything this returns
    is a printing that could settle a question the American leaves open.

    The raw `quote` is deliberately NOT searched. It is the scanner's output and
    carries strings like "Cobb" inside words that are not names — searching it
    put G. Spring's Franklin Street office under Cobb's saddlery on the first run
    of this file. The reading is what a claim asserts; the quote is what the page
    looked like to a machine.
    """
    pat = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in tokens) + r")\b",
                     re.IGNORECASE)
    out = []
    for path in sorted(EXTRACTED.glob("chicago_democrat_*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for claim in doc.get("claims", []):
            biz = claim.get("business")
            if not isinstance(biz, dict):
                continue
            place = biz.get("placement") or {}
            if place.get("class") in (None, "none") and not biz.get("street"):
                continue
            blob = " ".join([claim.get("normalized") or "", biz.get("name") or "",
                             " ".join(biz.get("proprietors") or [])])
            if pat.search(blob):
                out.append((doc["issue_id"], claim["id"],
                            place.get("offset_normalized") or biz.get("street") or
                            place.get("anchor") or "(placed, no text)"))
    return out


def measure(questions: list[dict] | None = None,
            transcription: list[dict] | None = None) -> tuple[list[str], list[dict]]:
    """Returns (failures, per-question rows).

    Both declarations are parameters rather than globals so `--self-test` can
    break one at a time and prove the assertion fires. A gate nobody has watched
    fail is a gate nobody knows the shape of.
    """
    questions = QUESTIONS if questions is None else questions
    transcription = TRANSCRIPTION_READINGS if transcription is None else transcription
    failures: list[str] = []
    rows: list[dict] = []

    for q in questions:
        resolved: list[str] = []
        for p in q["printings"]:
            issue_id, claim_id = p["claim"].split("#")
            try:
                doc = load_issue(issue_id)
            except FileNotFoundError:
                failures.append(f"{q['id']}: {issue_id} is not a committed extraction")
                continue
            claim = next((c for c in doc.get("claims", []) if c.get("id") == claim_id), None)
            if claim is None:
                failures.append(f"{q['id']}: {p['claim']} no longer exists")
                continue
            loc = claim.get("locator") or {}
            if (loc.get("issue_page"), loc.get("column")) != (p["page"], p["column"]):
                failures.append(
                    f"{q['id']}: {p['claim']} has moved to page {loc.get('issue_page')} "
                    f"column {loc.get('column')}, and this file says page {p['page']} "
                    f"column {p['column']}")
            if p["carries"] not in (claim.get("normalized") or ""):
                failures.append(
                    f"{q['id']}: {p['claim']} no longer reads {p['carries']!r} — the "
                    f"reading this question rests on has changed, so the question has "
                    f"to be re-argued rather than left standing")
            if p["reads"]:
                resolved.append(p["reads"])

        distinct = sorted(set(resolved))
        if q["open_because"] == DISAGREE and len(distinct) < 2:
            failures.append(
                f"{q['id']}: declared open because the printings disagree, and they no "
                f"longer do ({distinct or 'nothing resolves'}) — close the question or "
                f"restate why it is open")
        if q["open_because"] == UNRESOLVED and resolved:
            failures.append(
                f"{q['id']}: declared open because no printing resolves it, and "
                f"{distinct} now does — close the question or restate it")

        addrs = democrat_addresses(q["democrat_tokens"])
        if q["democrat_supplies_address"] and not addrs:
            failures.append(
                f"{q['id']}: declared corroborated-by-the-Democrat and the Democrat now "
                f"places nothing under {q['democrat_tokens']}")
        if not q["democrat_supplies_address"] and addrs:
            failures.append(
                f"{q['id']}: the Democrat now carries an ADDRESS for "
                f"{q['democrat_tokens']} — {addrs} — so the corpus may settle this "
                f"question and it is no longer waiting on a page image")

        rows.append({"q": q, "resolved": distinct, "democrat": addrs})

    for t in transcription:
        path = text_path(t["issue"])
        if not path.is_file():
            failures.append(f"{t['issue']}: derived text is not committed")
            continue
        lines = path.read_text(encoding="utf-8").split("\n")
        idx = t["line"] - 1
        line = lines[idx] if 0 <= idx < len(lines) else ""
        if t["carries"] not in line:
            failures.append(
                f"{t['issue']} line {t['line']} no longer reads {t['carries']!r} "
                f"(it reads {line.strip()[:60]!r})")

    return failures, rows


def report(rows: list[dict]) -> None:
    print("THE FOUR READINGS THE CHICAGO AMERICAN CONTRADICTS ITSELF ON (T-0305)\n")
    for row in rows:
        q = row["q"]
        print(f"  {q['id']} — {q['subject']}")
        print(f"    {q['question']}   [open: {q['open_because']}]")
        for p in q["printings"]:
            issue, claim = p["claim"].split("#")
            date = issue.rsplit("_", 3)[-3:]
            print(f"      {'-'.join(date)}  p{p['page']} c{p['column']}  {claim}  "
                  f"reads {p['reads'] or '(unresolved)'}")
        if row["democrat"]:
            print(f"      the Democrat places it: "
                  f"{', '.join(f'{i}#{c}' for i, c, _ in row['democrat'])}")
        else:
            print("      the Democrat supplies no address for it in 73 issues")
        print()
    for t in TRANSCRIPTION_READINGS:
        print(f"  also, off the transcription: {t['issue']} line {t['line']} "
              f"reads {t['reads']} ({t['whose']})")
    print(f"\n  {len(rows)} question(s), none of them closeable from the corpus.")


SELF_TESTS = [
    ("a printing that has stopped existing", "no longer exists",
     lambda qs, tr: qs[1]["printings"][0].__setitem__("claim",
                                                      "chicago_american_1835_06_13#c999")),
    ("a printing that has moved column", "has moved to page",
     lambda qs, tr: qs[1]["printings"][0].__setitem__("column", 2)),
    ("a reading that no longer reads that way", "no longer reads",
     lambda qs, tr: qs[1]["printings"][0].__setitem__("carries", "EAST WATER STREET")),
    ("a disagreement that has collapsed", "no longer do",
     lambda qs, tr: qs[1]["printings"][1].__setitem__("reads", "North Water")),
    ("an unresolved street that has resolved", "now does",
     lambda qs, tr: qs[3]["printings"][0].__setitem__("reads", "Canal")),
    ("the Democrat turning out to carry the address after all", "no longer waiting on a page image",
     lambda qs, tr: qs[1].__setitem__("democrat_tokens", ["Cobb"])),
    ("a corroboration that has gone", "places nothing under",
     lambda qs, tr: qs[3].__setitem__("democrat_tokens", ["Nobody"])),
    ("a transcription line that has drifted", "no longer reads",
     lambda qs, tr: tr[0].__setitem__("line", 1)),
]


def self_test() -> int:
    """Break each declaration in turn and require the matching assertion to fire."""
    import copy as _copy

    failures, _ = measure()
    if failures:
        print("  FAIL  the unbroken declarations do not pass, so nothing below means "
              "anything")
        for f in failures:
            print(f"          {f}")
        return 1

    bad = 0
    for label, expect, break_it in SELF_TESTS:
        qs = _copy.deepcopy(QUESTIONS)
        tr = _copy.deepcopy(TRANSCRIPTION_READINGS)
        break_it(qs, tr)
        got, _ = measure(qs, tr)
        if any(expect in g for g in got):
            print(f"  ok    {label}")
        else:
            print(f"  FAIL  {label} — nothing said {expect!r}; got {got or 'no failure'}")
            bad += 1
    print(f"\n  SELF-TEST {'PASS' if not bad else 'FAIL'} — "
          f"{len(SELF_TESTS) - bad}/{len(SELF_TESTS)} assertions fire when broken")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any declared reading has drifted")
    ap.add_argument("--self-test", action="store_true",
                    help="prove each assertion fires when its declaration is broken")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    failures, rows = measure()
    if args.gate:
        for f in failures:
            print(f"  FAIL  {f}")
        if failures:
            print(f"\n  {len(failures)} declared reading(s) no longer hold.")
            return 1
        print(f"  ok    {len(QUESTIONS)} American contradiction(s) still read as "
              f"declared, and the Democrat still settles none of the three it is "
              f"silent on")
        return 0

    report(rows)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
