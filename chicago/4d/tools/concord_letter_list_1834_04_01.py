"""What each of the 193 printed lines of the 1 April 1834 return reaches (T-1141, out of T-1138).

    python3 tools/concord_letter_list_1834_04_01.py             write
    python3 tools/concord_letter_list_1834_04_01.py --check     re-derive and diff
    python3 tools/concord_letter_list_1834_04_01.py --report    the ledger, read out
    python3 tools/concord_letter_list_1834_04_01.py --self-test the assertions, broken

WHAT THIS IS FOR.

T-1138 read THREE lines of the Chicago post office's 1 April 1834 return at the page
images, because two transcriptions of one return set them differently and T-0321's rule
is that only the page may settle that. Three lines out of about a hundred and seventy,
and on its way past those three it could not help seeing a whole line the extraction has
no entity for, a second carried in prose and in no entity, and three minted names set
otherwise on the page. Five findings in the twenty-odd lines one pass happened to look
at. Whatever the rate is over the rest, it is not zero — so the rest was read.

`letter_list_1834_04_01_printed.json` is that reading: all 193 lines of the return as the
8 April impression sets them, in printed order, counted off the page rather than inferred
from the extraction. THIS file puts those lines beside what the project extracted, one row
per printed line, and says what each one reaches.

IT MINTS NOBODY AND MOVES NO CARD. Reading is one decision, counting is a second and
moving a card is a third (T-0424's distinction, and T-1010 kept it for January). The
readings this pass finds the image overturning are listed under `name_differs` and are
carried to T-1153, which owns the movement and the withdrawals it implies.

HOW A PRINTED LINE IS TIED TO A NAME THE PROJECT EXTRACTED. January's problem was that
its two crops read a column out of order and in pieces, so its tie rules are a ladder of
name tests. This return's problem is the opposite and the tie is stronger for it: each of
the six claims below transcribes ONE sub-column of ONE impression IN PRINTED ORDER, so a
claim's entities are a SUBSEQUENCE of that sub-column's lines and nothing else. The tie
is therefore an ORDER-PRESERVING alignment — the longest one, scored on name agreement —
and a claim that drops a line shows up as the gap it is instead of as a mis-tie further
down. `tied_by` records which test carried each pair:

  `text`      the entity's normalized name and the printed line agree exactly once both
              are folded (case, punctuation, the trailing letter-count digit and any
              [bracketed] glyph opened rather than dropped).
  `spelling`  the surnames are within two edits and the forenames do not contradict —
              `Hartsell`/`Hartecll`, `Saymore`/`Saymoro`, `Hugunin`/`Hugunit`. Two
              settings of one return differ by exactly this much.
  `surname`   the surnames agree and one side prints no forename at all, or one prints
              an initial the other's forename could abbreviate.
  `order`     no name test carried the pair, but the alignment has no other place to put
              it: the entities on either side are tied and this one stands between them.
              `Eli Bona` against the extraction's `Eli Benn` is this rule, and the row
              says so rather than pretending the two readings agree.

WHAT A ROW SAYS THE LINE REACHES. The same four outcomes January derives, by the same
route — out of `mint_letter_list_residents.py`'s own `mint()`, so this ledger cannot
drift from the pass it describes:

  `minted`        the letter-list pass minted a household for it, named here.
  `held_already`  the register ties the name to somebody the town already holds on other
                  evidence, so the line reaches a card that is not this cohort's.
  `refused`       the name was in the mint's pool and a named refusal turned it away.
                  Not a gap: a ruling.
  `unread`        no claim extracted from ANY of the three impressions carries this line.

THE HEADLINE, AND WHY THE COUNT IS THE POINT. The 1 April transcription reads 82 names in
its first sub-column and 81 in its second. The page sets 97 and 96. So THIRTY printed
lines are dropped by the transcription the cohort was minted from — and twenty-eight of
them are carried by another impression's claim, which is the corpus working as it should.
Two are carried by NONE, on any impression, and this pass is where they stop being
invisible: `P. Cook` and `Jeter Foster`. The 16 April extraction saw both and could not
read them, recording line 3835 as `p, Cock` and line 3855 as `Jeter oats` among its eight
debris lines; the 8 April impression sets them clean.

THE LETTERS, AND THE ONE FIGURE THE PAGE PRINTS ITSELF. The roster's 193 lines carry 218
letters once the trailing count digits are added, and the figure the office set at the
foot of the column is `21[8]` — its last digit inked thin against the column rule. The
tally is the measurement and the printed figure agrees with it; `--check` re-derives the
tally and fails if it moves.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import concord_letter_list_1834_01_01 as jan  # noqa: E402
import mint_letter_list_residents as mint_pass  # noqa: E402

from concord_letter_list_1834_01_01 import (  # noqa: E402
    BRACKET, edits, fold, forenames_agree, load, parts,
)

DATA = ROOT / "data"
ROSTER = DATA / "research" / "newspapers" / "letter_list_1834_04_01_printed.json"
CONTESTED = DATA / "research" / "newspapers" / "letter_list_1834_04_01_contested_lines.json"
EXTRACTED = DATA / "research" / "newspapers" / "extracted"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
HOUSEHOLDS = DATA / "residents" / "households"
OUT = DATA / "research" / "newspapers" / "letter_list_1834_04_01_concordance.json"

# The six claims this project has extracted from the three impressions of this one
# return, each one sub-column of one impression, each in printed order. The 1 April
# pair transcribes the whole of both sub-columns; the 8 April and 16 April claims were
# written to carry only what the 1 April transcription lost, which is why they hold
# few entities and why they are still needed here.
CLAIMS = (
    ("chicago_democrat_1834_04_01", "c001", "left"),
    ("chicago_democrat_1834_04_01", "c002", "right"),
    ("chicago_democrat_1834_04_08", "c001", "left"),
    ("chicago_democrat_1834_04_08", "c002", "right"),
    ("chicago_democrat_1834_04_16", "c016", "left"),
    ("chicago_democrat_1834_04_16", "c017", "right"),
)

# The postmaster signs the list and is not one of its addressee lines. He is an entity of
# the 1 April right-hand claim all the same, so the alignment has to be told.
SIGNATORY = "John S. C. Hogan"


# ---------------------------------------------------------------------------
# the tie: an order-preserving alignment of one claim onto one sub-column
# ---------------------------------------------------------------------------

def forenames_close(a: list[str], b: list[str]) -> bool:
    """Two forename readings of one name, allowing the misreading a type broke.

    `forenames_agree` refuses `Dadly` against `Dudly` and `Alason` against `Jason`,
    because for its own purpose — deciding whether two names in DIFFERENT places are one
    person — that refusal is right. Here the question is narrower and the answer is the
    other way: these are two readings of the SAME line of the SAME return, and a column
    that prints `Dadly Peck` and a transcription that reads `Dudly Peck` are not two
    Pecks. So a token pair may also differ by up to two letters, which is the distance a
    broken sort puts between two readings of one word, and no more.
    """
    if not a or not b:
        return True
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if (len(x) == 1 or len(y) == 1) and x[0] == y[0]:
            continue
        if min(len(x), len(y)) >= 4 and edits(x, y, ceiling=2) <= 2:
            continue
        return False
    return True


def agreement(printed: str, extracted: str) -> tuple[int, str] | None:
    """How well one reading matches one printed line, or None if it cannot be it."""
    pf, ef = fold(printed), fold(extracted)
    if pf and pf == ef:
        return 3, "text"
    pfam, pfore = parts(printed)
    efam, efore = parts(extracted)
    if not pfam or not efam:
        return None
    d = edits(pfam, efam, ceiling=2)
    if d > 2:
        return None
    if pfore and efore and forenames_agree(pfore, efore):
        return 2, "spelling"
    if pfore and efore and forenames_close(pfore, efore):
        return 2, "spelling"
    if not pfore or not efore:
        return 1, "surname"
    return None


def align(lines: list[dict], ents: list[dict]) -> list[tuple[int, dict, str]]:
    """Order-preserving alignment of a claim's entities onto a sub-column's lines.

    A claim reads one sub-column top to bottom, so entity i and entity i+1 cannot swap
    places: whatever line the first takes, the second takes a later one. The alignment
    that maximises total name agreement under that constraint is the tie, and because
    every entity MUST land somewhere (a transcription of this column cannot carry a name
    the column does not print) the recurrence charges a heavy penalty for leaving one
    unplaced rather than allowing it. What is free is leaving a LINE unmatched: that is
    the drop this whole pass exists to count.
    """
    n, m = len(lines), len(ents)
    UNPLACED = -100
    NEG = float("-inf")
    # best[i][j] = score of aligning the first j entities into the first i lines
    best = [[NEG] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        best[i][0] = 0
    for j in range(1, m + 1):
        best[0][j] = UNPLACED * j
        back[0][j] = ("skip_entity", None)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # line i carries no entity
            cand, how = best[i - 1][j], ("skip_line", None)
            # entity j takes line i
            fit = agreement(lines[i - 1]["as_printed"], ents[j - 1]["normalized"])
            if fit is not None and best[i - 1][j - 1] > NEG:
                score = best[i - 1][j - 1] + fit[0]
                if score > cand:
                    cand, how = score, ("match", fit[1])
            # entity j takes line i on order alone — the name tests all refused it
            if fit is None and best[i - 1][j - 1] > NEG:
                score = best[i - 1][j - 1]
                if score > cand:
                    cand, how = score, ("match", "order")
            # entity j is placed nowhere at all
            if best[i][j - 1] > NEG and best[i][j - 1] + UNPLACED > cand:
                cand, how = best[i][j - 1] + UNPLACED, ("skip_entity", None)
            best[i][j], back[i][j] = cand, how
    pairs: list[tuple[int, dict, str]] = []
    i, j = n, m
    while j > 0:
        move, how = back[i][j] if i > 0 else ("skip_entity", None)
        if move == "skip_line":
            i -= 1
        elif move == "match":
            pairs.append((lines[i - 1]["n"], ents[j - 1], how))
            i -= 1
            j -= 1
        else:
            pairs.append((0, ents[j - 1], "unplaced"))
            j -= 1
    pairs.reverse()
    return pairs


def claim_entities(issue_id: str, claim_id: str) -> list[dict]:
    path = EXTRACTED / f"{issue_id}.json"
    if not path.exists():
        return []
    for claim in load(path).get("claims", []):
        if claim.get("id") != claim_id:
            continue
        return [{"claim": f"{issue_id}#{claim_id}",
                 "issue": issue_id,
                 "as_printed": ent.get("as_printed"),
                 "normalized": ent.get("normalized") or ent.get("as_printed"),
                 "read_at_image": ent.get("read_at_image")}
                for ent in claim.get("entities", [])
                if fold(ent.get("normalized") or "") != fold(SIGNATORY)]
    return []


# ---------------------------------------------------------------------------
# what a tied line reaches
# ---------------------------------------------------------------------------

def build() -> dict:
    roster = load(ROSTER)
    rows = [{"n": l["n"], "column": l["column"], "as_printed": l["as_printed"]}
            for l in roster["lines"]]
    by_column = {c: [r for r in rows if r["column"] == c] for c in ("left", "right")}

    tied: dict[int, list[dict]] = {}
    unplaced: list[dict] = []
    for issue_id, claim_id, column in CLAIMS:
        ents = claim_entities(issue_id, claim_id)
        if not ents:
            continue
        for n, ent, how in align(by_column[column], ents):
            if how == "unplaced":
                unplaced.append({"claim": ent["claim"], "as_printed": ent["as_printed"],
                                 "extracted_as": ent["normalized"],
                                 "why": "the alignment of this claim onto its sub-column "
                                        "has no line for this reading"})
            else:
                tied.setdefault(n, []).append(dict(ent, tied_by=how))

    gaz = load(GAZETTEER)
    owner = jan.variant_owner(gaz)
    by_person = {p["id"]: p for p in load(REGISTER)["persons"]}
    minted, refused = jan.mint_outcomes()

    card_names, card_by_household = {}, {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = load(path)
        for person in doc.get("persons", []):
            card_names[person["id"]] = (doc["id"], person["name"])
            if person.get("relationship") == "head":
                card_by_household[doc["id"]] = person["name"]

    RANK = {"minted": 0, "held_already": 1, "refused": 2, "unresolved": 3}

    def outcome_for(ent: dict) -> dict:
        pid = owner.get((ent["claim"], fold(ent["as_printed"])))
        if pid is None:
            pid = owner.get((ent["claim"], fold(ent["normalized"])))
        reg = by_person.get(pid) if pid else None
        if pid and pid in minted:
            hid = minted[pid]
            return {"kind": "minted", "person": pid, "household": hid,
                    "card_name": card_by_household.get(hid),
                    "by": "tools/mint_letter_list_residents.py"}
        if pid and pid in refused:
            return {"kind": "refused", "person": pid, "reason": refused[pid],
                    "by": "tools/mint_letter_list_residents.py"}
        if reg and reg.get("action") in ("enrich", "replace_invented"):
            target = reg.get("action_target")
            hid, held = card_names.get(target, (None, None))
            return {"kind": "held_already", "person": pid, "resident": target,
                    "household": hid, "card_name": held, "action": reg["action"]}
        return {"kind": "unresolved", "person": pid,
                "why": "the extraction carries this line but the compiled register does "
                       "not resolve the reading to a person, so nothing downstream of "
                       "it reaches a card either"}

    lines, name_differs, dropped = [], [], []
    for row in rows:
        readings = tied.get(row["n"]) or []
        out = dict(row)
        if not readings:
            out["tie"] = None
            out["reaches"] = {
                "kind": "unread",
                "why": "no claim this project has extracted from any of the three "
                       "impressions of this return carries this line",
            }
            lines.append(out)
            dropped.append({"n": row["n"], "column": row["column"],
                            "as_printed": row["as_printed"],
                            "carried_by": [],
                            "rule": "carried by no claim of any impression — outside the "
                                    "mint's pool entirely, because the pool is built of "
                                    "ENTITIES and this line is not one"})
            continue

        out["tie"] = [{"tied_by": e["tied_by"], "claim": e["claim"],
                       "as_printed_in_that_printing": e["as_printed"],
                       "extracted_as": e["normalized"]} for e in readings]
        if any(e.get("read_at_image") for e in readings):
            # T-1138 read this line at all three impressions and the extraction now
            # carries what the page set, which is why it is NOT under `name_differs`.
            out["settled_at_the_image"] = {
                "ticket": "T-1138",
                "roster": "data/research/newspapers/letter_list_1834_04_01_contested_lines.json",
            }
        outcomes = [outcome_for(e) for e in readings]
        best = min(outcomes, key=lambda o: RANK[o["kind"]])
        others = [o for o in outcomes
                  if o.get("person") and o["person"] != best.get("person")]
        out["reaches"] = dict(best, also_resolved_to=sorted(
            {o["person"] for o in others})) if others else best

        carriers = {e["issue"] for e in readings}
        if "chicago_democrat_1834_04_01" not in carriers:
            dropped.append({
                "n": row["n"], "column": row["column"], "as_printed": row["as_printed"],
                "carried_by": sorted(e["claim"] for e in readings),
                "rule": "dropped by the 1 April transcription and carried by another "
                        "impression's claim, so it enters the mint's pool through that "
                        "claim and is minted or refused there",
                "reaches": out["reaches"]["kind"],
            })

        printed_fold = fold(row["as_printed"])
        disagree = [e for e in readings if fold(e["normalized"]) != printed_fold]
        if disagree:
            name_differs.append({
                "n": row["n"], "column": row["column"],
                "printed_as": row["as_printed"],
                "readings": [{"claim": e["claim"], "extracted_as": e["normalized"],
                              "tied_by": e["tied_by"]} for e in disagree],
                "card_name": out["reaches"].get("card_name"),
                "reaches": out["reaches"]["kind"],
            })
        lines.append(out)

    tally: dict[str, int] = {}
    for line in lines:
        tally[line["reaches"]["kind"]] = tally.get(line["reaches"]["kind"], 0) + 1

    def waiting(name: str) -> int:
        tail = name.split()[-1]
        return int(tail) if tail.isdigit() else 1

    letters = sum(waiting(r["as_printed"]) for r in rows)

    return {
        "schema": 1,
        "generated_by": "tools/concord_letter_list_1834_04_01.py",
        "_doc": __doc__,
        "return": dict(roster["return"], read_at=roster["printing_read"]["issue_id"]),
        "claims_read": [f"{i}#{c}" for i, c, _col in CLAIMS],
        "counts": {
            "printed_lines": len(rows),
            "left_sub_column": len(by_column["left"]),
            "right_sub_column": len(by_column["right"]),
            "letters_waiting": letters,
            "people_named": len(rows),
            "lines_the_1_april_transcription_drops": len(
                [d for d in dropped if d.get("carried_by") is not None]),
            "of_those_carried_by_another_impression": len(
                [d for d in dropped if d["carried_by"]]),
            "of_those_carried_by_no_claim_at_all": len(
                [d for d in dropped if not d["carried_by"]]),
            "reaches_a_card": tally.get("minted", 0) + tally.get("held_already", 0),
            "by_outcome": tally,
            "lines_whose_reading_the_page_disagrees_with": len(name_differs),
            "lines_already_settled_at_the_image": len(
                [l for l in lines if l.get("settled_at_the_image")]),
        },
        "lines": lines,
        "lines_the_1_april_transcription_drops": dropped,
        "name_differs": name_differs,
        "extracted_names_no_line_carries": unplaced,
    }


# ---------------------------------------------------------------------------
# report, check, self-test
# ---------------------------------------------------------------------------

def report(doc: dict) -> None:
    c = doc["counts"]
    print(f"\nTHE 1 APRIL 1834 RETURN, READ AT THE 8 APRIL IMPRESSION")
    print(f"  {c['printed_lines']} printed lines "
          f"({c['left_sub_column']} + {c['right_sub_column']}), "
          f"{c['letters_waiting']} letters waiting")
    print(f"\nWHAT THE LINES REACH")
    for kind, n in sorted(c["by_outcome"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {kind}")
    print(f"  {'-' * 5}")
    print(f"  {c['reaches_a_card']:5d}  reach a card")
    print(f"\nWHAT THE 1 APRIL TRANSCRIPTION DROPPED")
    print(f"  {c['lines_the_1_april_transcription_drops']:5d}  lines")
    print(f"  {c['of_those_carried_by_another_impression']:5d}  carried by another impression")
    print(f"  {c['of_those_carried_by_no_claim_at_all']:5d}  carried by no claim at all")
    for d in doc["lines_the_1_april_transcription_drops"]:
        if not d["carried_by"]:
            print(f"        line {d['n']:3d}  {d['as_printed']}")
    print(f"\nWHERE THE PAGE AND THE EXTRACTION SET A NAME DIFFERENTLY")
    print(f"  {len(doc['name_differs']):5d}  lines still standing on two readings")
    print(f"  {c['lines_already_settled_at_the_image']:5d}  already settled at the image "
          f"(T-1138), and therefore not among them")
    for d in doc["name_differs"][:60]:
        readings = " / ".join(r["extracted_as"] for r in d["readings"])
        print(f"        line {d['n']:3d}  page {d['printed_as']!r:34s} extraction {readings}")


def check() -> int:
    if not OUT.exists():
        print(f"FAIL {OUT} does not exist", file=sys.stderr)
        return 1
    want, have = build(), load(OUT)
    bad = 0
    for key in ("counts", "lines", "lines_the_1_april_transcription_drops",
                "name_differs", "extracted_names_no_line_carries", "claims_read"):
        if want[key] != have.get(key):
            print(f"FAIL {OUT.name}: `{key}` is not what the tree derives", file=sys.stderr)
            bad = 1
    roster = load(ROSTER)
    pl = roster["printed_length"]
    if pl["lines"] != len(roster["lines"]):
        print("FAIL the roster's stated printed length is not its own line count",
              file=sys.stderr)
        bad = 1
    if pl["letters_waiting"] != want["counts"]["letters_waiting"]:
        print("FAIL the roster's stated letter count is not the tally of its own lines",
              file=sys.stderr)
        bad = 1
    if pl["the_printed_total"]["read"] != want["counts"]["letters_waiting"]:
        print("FAIL the figure printed at the foot of the column and the roster's own "
              "tally have come apart", file=sys.stderr)
        bad = 1
    # T-1138's three lines are in this roster too, and they must still read what the
    # image made them read. A concordance that quietly re-set one of them back to the
    # 1 April transcription would resurrect a card the image withdrew.
    contested = {l["as_printed_at_image"] for l in load(CONTESTED)["lines"]}
    printed = {l["as_printed"] for l in roster["lines"]}
    missing = sorted(contested - printed)
    if missing:
        print(f"FAIL the roster has lost T-1138's image readings: {missing}",
              file=sys.stderr)
        bad = 1
    settled = want["counts"]["lines_already_settled_at_the_image"]
    if settled != len(load(CONTESTED)["lines"]):
        print(f"FAIL T-1138 settled {len(load(CONTESTED)['lines'])} lines of this return "
              f"and the concordance ties {settled} of them", file=sys.stderr)
        bad = 1
    if want["extracted_names_no_line_carries"]:
        print("FAIL a claim of this return carries a reading no printed line does — the "
              "roster and the extraction have come apart", file=sys.stderr)
        bad = 1
    if not bad:
        print(f"ok  {OUT.name}: {want['counts']['printed_lines']} lines, "
              f"{want['counts']['letters_waiting']} letters, "
              f"{want['counts']['lines_the_1_april_transcription_drops']} dropped by the "
              f"1 April transcription, "
              f"{want['counts']['of_those_carried_by_no_claim_at_all']} of them by every "
              f"claim the corpus holds")
    return bad


def self_test() -> int:
    """The assertions above, broken on purpose."""
    doc = build()
    fired = []

    def fires(what, fn):
        try:
            fn()
        except AssertionError:
            fired.append(what)
            print(f"   self-test |   fires: {what}")
            return
        print(f"   self-test | SILENT: {what}", file=sys.stderr)

    print("   self-test |   passes: the committed derivation, unmodified")
    assert doc["counts"]["printed_lines"] == 193
    assert doc["counts"]["letters_waiting"] == 218

    def order_preserving():
        for _issue, _claim, column in CLAIMS:
            pass
        # every claim's ties must run strictly down its sub-column
        seen: dict[str, int] = {}
        for line in doc["lines"]:
            for t in line["tie"] or []:
                assert t["claim"] not in seen or seen[t["claim"]] < line["n"], \
                    "a claim's ties run backwards up its own column"
                seen[t["claim"]] = line["n"]
    order_preserving()
    print("   self-test |   passes: every claim's ties run down its sub-column, never back up")

    fires("a line tied to two readings of the same claim",
          lambda: _assert_one_reading_per_claim(_double_up(doc)))
    fires("a sub-column whose lines do not sum to the printed length",
          lambda: _assert_length(dict(doc, counts=dict(doc["counts"],
                                                       left_sub_column=96))))
    fires("a letter tally that no longer matches the lines it is made of",
          lambda: _assert_letters(dict(doc, counts=dict(doc["counts"],
                                                        letters_waiting=217))))
    fires("a drop the ledger says is carried when no claim carries it",
          lambda: _assert_drops([dict(d, carried_by=["x#c001"]) if not d["carried_by"]
                                 else d
                                 for d in doc["lines_the_1_april_transcription_drops"]]))
    print(f"   self-test | {len(fired)} of 4 assertions fire when broken")
    return 0 if len(fired) == 4 else 1


def _double_up(doc):
    lines = [dict(l) for l in doc["lines"]]
    for line in lines:
        if line["tie"]:
            line["tie"] = line["tie"] + [dict(line["tie"][0])]
            break
    return lines


def _assert_one_reading_per_claim(lines):
    for line in lines:
        claims = [t["claim"] for t in line["tie"] or []]
        assert len(claims) == len(set(claims)), \
            f"line {line['n']} is tied twice to one claim"


def _assert_length(doc):
    c = doc["counts"]
    assert c["left_sub_column"] + c["right_sub_column"] == c["printed_lines"], \
        "the sub-columns do not sum to the printed length"


def _assert_letters(doc):
    def waiting(name):
        tail = name.split()[-1]
        return int(tail) if tail.isdigit() else 1
    assert doc["counts"]["letters_waiting"] == sum(
        waiting(l["as_printed"]) for l in doc["lines"]), \
        "the letter tally is not the tally of the lines"


def _assert_drops(drops):
    for d in drops:
        if d["carried_by"]:
            assert "carried by another impression" in d["rule"], \
                f"line {d['n']} is said to be carried and its rule says it is not"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    doc = build()
    if args.report:
        report(doc)
        return 0
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {doc['counts']['printed_lines']} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
