#!/usr/bin/env python3
"""T-1320: the kinship the BOOK corpus states, read, resolved and ruled.

    python3 tools/spend_book_kin.py              the reading, on stdout
    python3 tools/spend_book_kin.py --build      write the ruled ties onto the cards
    python3 tools/spend_book_kin.py --check      re-derive, and hold every candidate to a ruling
    python3 tools/spend_book_kin.py --self-test  the assertions of --check, broken on purpose

WHAT THIS IS FOR.

`tools/survey_stated_kin.py` (T-0734) declares its corpus, and the declaration is the
hole this pass fills: the church registers, and `the prose already quoted onto the
cards`. `tools/spend_stated_families.py` (T-1312) reads the same cards a second way, for
the marriage verb the survey's `<relation> of <Name>` pattern cannot see. Both read the
CARDS. Neither has ever read `data/research/books/claims/` — nine committed books, 275
adjudicated claims, Hurlbut and Hubbard and Moses and Kirkland and Fergus and Porter —
for the kinship they state. A book sentence only reached a card when somebody quoted it
onto one, and what was never quoted was never counted.

So this pass reads the books, and it reads them for one thing: A RELATIONSHIP BETWEEN TWO
PEOPLE THIS TOWN HOLDS. That is the only kind of kinship the dataset has a structure for
— `validate.py` says so in as many words, and the rule is quoted here because it decides
half the verdicts below:

    KIN IS INSIDE THE TOWN (T-0849) ... a row with no far end is not a weaker kin row, it
    is one with the whole checked part removed. A relative who was never in this scene (a
    parent in Montreal, a brother left in Vermont) is EVIDENCE, not structure.

NOBODY IS MINTED, BY EITHER HALF. The books name plenty of relatives who are nobody in
this dataset — Hubbard's sisters Mary and Abby at Danville, Porter's father at Machias,
Caton's bride at New Hartford. Each is ruled and none becomes a person: minting is the
four mints' and the reconstruction programme's, never a reading pass's. This pass writes
exactly two things, both onto cards that already exist: a kin row between two people the
town already holds, and a second source on a kin row that already stands.

HOW A NAME IN A BOOK BECOMES A PERSON, AND THE LINE THIS PASS WILL NOT CROSS.

The survey resolves a register entry BY BACK-LINK AND BY NOTHING ELSE, because most of
those people exist because of the entry that names them. A book has no such back-link and
a book sentence has no card whose head it must be, so BOTH ends float — and a pass that
married two floating names on a shared surname would be the worst identifier in this
repository. It therefore resolves by the committed identification and by nothing else:

  * `data/research/books/crosswalk.json` `merges` — the project's own written answer to
    'who is this book name', 35 of them, each with its rule and its evidence. A merge
    rewrites the book's name to the resident's.
  * then the residents layer, by the crosswalk's own matching rule (folded surname,
    forenames token for token, an initial matching the forename it abbreviates), and
    EXACTLY ONE person may match.
  * a `refusals` entry naming the pair BLOCKS it, whatever the names look like. The
    crosswalk has already refused 'Mr. John Kinzie' the elder against John Harris Kinzie
    his son, and this pass may not quietly re-make an identification the project declined.

A RESOLUTION IS A PROPOSAL; A WRITE IS A RULING. Everything above is DERIVED and moves
when the corpus moves. What happens to each candidate is AUTHORED, one at a time, in
`data/research/books/kin_rulings.json`, by somebody who has read the sentence — the same
split `kin_survey.json` / `kin_rulings.json` keeps, and for the same reason. `--check`
refuses while one candidate stands unanswered, so a book read into this corpus tomorrow
cannot arrive carrying a kinship nobody looked at.

The reader overrules the resolver and never the other way round. Moses and Kirkland's
William Jones folds onto the town's William Jones and is not him — the sentence itself
says he is the first NON-RESIDENT to buy a Chicago lot — and the ruling is where that is
said. A derivation cannot read a sentence; that is what the rulings file is for.

THE VERDICTS. Two write and seven do not.

  tie                  both ends are people this town holds, the crosswalk has identified
                       both, the relation is one validate.py knows an inverse for, and no
                       row says so yet. Written onto BOTH cards, reciprocally.
  corroborates         the cards already carry this tie and this reading states it too.
                       The ruling BINDS the book claim to both rows — `book_kin` names it,
                       so a row that lost its tie surfaces here — and adds whatever the
                       rows do not already have: the source id where it is a second and
                       independent statement, and the sentence in the note. THE GRADE DOES
                       NOT MOVE: a second recollection is a second recollection, and this
                       project does not promote a confidence because a claim got more
                       comfortable.
  relative_not_held    a source names a real relative OF A HELD RESIDENT who is nobody in
                       this dataset. Kin is inside the town: this is evidence for the
                       prose of a field the card already has, not a structure, and this
                       pass does not mint the relative to give the row a far end.
  identity_not_asserted  the crosswalk has not identified an end with the resident whose
                       name it folds onto, or has refused that pair outright.
  neither_end_held     the sentence is about people outside this town altogether.
  relation_undeclared  uncle, aunt, cousin, nephew. `validate.py` declares no inverse for
                       them, so the tie cannot be checked for reciprocity, and this
                       project does not write a claim its gate cannot read.
  not_a_kinship        the word is in the sentence and the relation is not: 'Father
                       O'Meara' is an honorific, 'the Noble brothers' is a firm style,
                       'none of the officers were married' is a negative about a class.
  later_only           the relationship is dated after the scene date of 1835-07-01.

WHAT A WRITTEN ROW CARRIES. `book_kin` names the claim that produced it, so the write is
re-derivable and a row this pass wrote can never be confused with one another pass wrote.
`--check` holds the layer to it both ways: every writing ruling is on both cards, and
every `book_kin` row on a card answers to a live claim and a live ruling.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from survey_stated_kin import Town, fold, load_town  # noqa: E402  the one matching rule

BOOKS = ROOT / "data" / "research" / "books"
CLAIMS = BOOKS / "claims"
CROSSWALK = BOOKS / "crosswalk.json"
RULINGS = BOOKS / "kin_rulings.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = "chicago4d.book_kin_rulings.v1"
TICKET = "T-1320"

# THE VOCABULARY IS THE CORPUS, so it is declared rather than tuned. Every claim whose
# reading or whose committed quote carries one of these words is a CANDIDATE and must be
# answered — including the ones where the word turns out not to be a relation at all,
# because 'Father O'Meara' is exactly the kind of near-miss a quietly narrowed pattern
# would drop and a reader catches in one second.
#
# WHAT IS NOT HERE, AND WHY. 'family', 'children', 'and family', 'household'. Those are
# the words a source COUNTS a family with and does not NAME one — 'the Gale family', 'the
# Fernando Jones family' — and a counted family is the reconstruction programme's
# (T-1314), on the other side of the refusal gate. This pass reads the NAMED.
KIN_VOCABULARY = re.compile(
    r"\b(wife|wives|husbands?|sons?|daughters?|brothers?|sisters?|fathers?|mothers?"
    r"|widows?|nephews?|nieces?|uncles?|aunts?|cousins?"
    r"|grand(?:son|daughter|father|mother)s?|step-?(?:son|daughter|father|mother)s?"
    r"|(?:brother|father|son|mother|daughter|sister)[- ]in[- ]law"
    r"|half[- ]?(?:brother|sister)s?|married|marriage|betrothed|wedded)\b", re.I)

WRITING = ("tie", "corroborates")
VERDICTS = WRITING + (
    "relative_not_held", "identity_not_asserted", "neither_end_held",
    "relation_undeclared", "not_a_kinship", "later_only",
)

# Exactly the relations validate.py declares an inverse for; checked against it at run
# time by --check, so the two cannot drift apart in silence.
INVERSES = {
    "brother": ("brother", "sister"), "sister": ("brother", "sister"),
    "half_brother": ("half_brother", "half_sister"),
    "half_sister": ("half_brother", "half_sister"),
    "husband": ("wife",), "wife": ("husband",),
    "father": ("son", "daughter"), "mother": ("son", "daughter"),
    "son": ("father", "mother"), "daughter": ("father", "mother"),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(text: str) -> str:
    return " ".join((text or "").split())


def claim_files() -> list[Path]:
    return sorted(CLAIMS.glob("*.json"))


def claims() -> list[dict]:
    """Every committed book claim, carrying the source it was read from."""
    out = []
    for path in claim_files():
        doc = read_json(path)
        for c in doc.get("claims") or []:
            out.append(dict(c, source_id=doc.get("source_id"),
                            file=str(path.relative_to(ROOT))))
    return sorted(out, key=lambda c: c["id"])


class Crosswalk:
    """The project's committed answer to 'who is this book name'."""

    def __init__(self, doc: dict):
        self.merges: dict[tuple, set] = {}
        for m in doc.get("merges") or []:
            self.merges.setdefault(tuple(fold(m.get("from") or "")), set()).add(
                norm(m.get("into") or ""))
        self.refused: set[tuple] = set()
        for r in doc.get("refusals") or []:
            self.refused.add((tuple(fold(r.get("a") or "")),
                              tuple(fold(r.get("b") or ""))))

    def names_for(self, as_read: str) -> list[str]:
        """The resident name(s) a merge rewrites this book name to, or the name itself."""
        merged = self.merges.get(tuple(fold(as_read)))
        return sorted(merged) if merged else [norm(as_read)]

    def refuses(self, as_read: str, resident_name: str) -> bool:
        return (tuple(fold(as_read)), tuple(fold(resident_name))) in self.refused


def resolve(as_read: str, town: Town, xwalk: Crosswalk) -> dict:
    """Who a book name is, by the committed identification and by nothing else."""
    hits, blocked = [], []
    for candidate in xwalk.names_for(as_read):
        for hid, pid, pname in town.resolve(candidate):
            if xwalk.refuses(as_read, pname):
                blocked.append(pname)
            else:
                hits.append({"household": hid, "person": pid, "name": pname})
    uniq = {(h["household"], h["person"]): h for h in hits}
    return {"as_read": norm(as_read), "held": sorted(uniq.values(),
                                                     key=lambda h: h["person"]),
            "refused_against": sorted(set(blocked))}


def derive() -> list[dict]:
    """Every book claim that states kinship, with both possible ends resolved."""
    town = Town(load_town())
    xwalk = Crosswalk(read_json(CROSSWALK))
    out = []
    for c in claims():
        text = f"{c.get('normalized') or ''}\n{c.get('quote') or ''}"
        terms = sorted({m.group(0).lower() for m in KIN_VOCABULARY.finditer(text)})
        if not terms:
            continue
        ends = [resolve(e, town, xwalk) for e in (c.get("entities") or [])]
        out.append({
            "claim": c["id"],
            "source": c.get("source_id"),
            "file": c["file"],
            "describes_date": c.get("describes_date"),
            "terms": terms,
            "reading": norm(c.get("normalized") or ""),
            "quote": norm(c.get("quote") or ""),
            "ends": ends,
            "held_ends": [e for e in ends if e["held"]],
        })
    return out


# --------------------------------------------------------------------------
# the writes: a kin row between two people this town already holds

def card(hid: str) -> dict:
    return read_json(HOUSEHOLDS / f"{hid}.json")


def kin_row(doc: dict, person: str, other_hid: str, other_pid: str):
    for row in doc.get("kin") or []:
        if (row.get("person") == person and row.get("household") == other_hid
                and row.get("value") == other_pid):
            return row
    return None


def build(rulings: dict, apply: bool = True) -> list[str]:
    """Write the ruled ties. Returns the lines describing what was written."""
    written = []
    for cid, r in sorted((rulings.get("rulings") or {}).items()):
        if r.get("ruling") not in WRITING:
            continue
        tie = r["tie"]
        pairs = ((tie["a"], tie["b"], tie["relation"]),
                 (tie["b"], tie["a"], tie["mirror"]))
        for near, far, relation in pairs:
            doc = card(near["household"])
            rows = doc.setdefault("kin", [])
            row = kin_row(doc, near["person"], far["household"], far["person"])
            if row is None:
                row = {"person": near["person"], "relation": relation,
                       "household": far["household"], "value": far["person"],
                       "confidence": tie["confidence"], "sources": [], "note": ""}
                rows.append(row)
                rows.sort(key=lambda k: (k.get("person") or "", k.get("value") or ""))
            if r["ruling"] == "tie":
                row["relation"] = relation
                row["confidence"] = tie["confidence"]
            if r["source"] not in (row.get("sources") or []):
                row["sources"] = sorted((row.get("sources") or []) + [r["source"]])
            addition = norm(r.get("note") or "")
            if addition and addition not in (row.get("note") or ""):
                row["note"] = norm(f"{row.get('note') or ''} {addition}")
            row["book_kin"] = sorted(set((row.get("book_kin") or []) + [cid]))
            written.append(f"{near['household']}/{near['person']} {relation} "
                           f"{far['household']}/{far['person']}  [{cid}]")
            if apply:
                path = HOUSEHOLDS / f"{near['household']}.json"
                path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                                encoding="utf-8")
    return written


# --------------------------------------------------------------------------
# the gate: every candidate answered, every answer honoured

def quote_problems(rulings: dict, by_claim: dict) -> list[str]:
    """A ruling quotes the sentence it answers; the claim must still say it.

    Either half of the claim counts. The `normalized` reading is what a person answers
    most of the time, but a kinship can live in the committed `quote` and not in the
    summary of it -- Gale's 'as a child to its mother' is in the book's own words and not
    in the sentence the claim files under them -- and a ruling may quote whichever it
    read.
    """
    problems = []
    for cid, r in sorted((rulings.get("rulings") or {}).items()):
        quoted = norm(r.get("reading") or "")
        cand = by_claim.get(cid)
        if not (quoted and cand):
            continue
        if quoted not in f"{cand['reading']} {cand.get('quote', '')}":
            problems.append(
                f"ruling '{cid}' quotes a reading the claim no longer carries. A ruling "
                f"is only worth anything while the source still says it; re-read the "
                f"claim rather than leaving an answer to a sentence that moved.")
    return problems


def check(quiet: bool = False, candidates: list[dict] | None = None,
          rulings: dict | None = None, docs: dict | None = None) -> list[str]:
    problems: list[str] = []
    candidates = derive() if candidates is None else candidates
    if rulings is None:
        if not RULINGS.exists():
            return [f"{RULINGS.relative_to(ROOT)} does not exist"]
        rulings = read_json(RULINGS)
    docs = load_town() if docs is None else docs
    ruled = rulings.get("rulings") or {}
    by_claim = {c["claim"]: c for c in candidates}

    problems += quote_problems(rulings, by_claim)

    for c in candidates:
        r = ruled.get(c["claim"])
        if r is None:
            problems.append(
                f"claim '{c['claim']}' states kinship ({', '.join(c['terms'])}) and "
                f"nobody has ruled on it. Every kinship the book corpus states is "
                f"answered in data/research/books/kin_rulings.json — written, or "
                f"refused with the reason.")
            continue
        if not norm(r.get("why") or ""):
            problems.append(f"ruling '{c['claim']}' carries no reason; a refusal is a "
                            f"finding and owes its reasoning")
        if r.get("ruling") not in VERDICTS:
            problems.append(f"ruling '{c['claim']}' has no verdict of {'|'.join(VERDICTS)}")

    for cid in sorted(ruled):
        if cid not in by_claim:
            problems.append(
                f"ruling '{cid}' answers a claim the corpus no longer states kinship in. "
                f"The corpus moved under the ruling; re-read it rather than leaving an "
                f"answer to a question nobody asked.")

    for cid, r in sorted(ruled.items()):
        if r.get("ruling") not in WRITING:
            continue
        tie = r.get("tie") or {}
        if tie.get("relation") not in INVERSES:
            problems.append(f"ruling '{cid}' writes relation '{tie.get('relation')}' — "
                            f"validate.py declares no inverse for it")
            continue
        if tie.get("mirror") not in INVERSES[tie["relation"]]:
            problems.append(
                f"ruling '{cid}' mirrors '{tie['relation']}' with '{tie.get('mirror')}', "
                f"which is not one of {list(INVERSES[tie['relation']])}. HALF IS THE "
                f"POINT: a half brother whose mirror says plain brother is the "
                f"flattening this vocabulary exists to catch.")
            continue
        if not norm(r.get("source") or ""):
            problems.append(f"ruling '{cid}' writes a row and cites no source")
        ends = [(tie.get("a") or {}), (tie.get("b") or {})]
        if ends[0].get("household") == ends[1].get("household"):
            problems.append(f"ruling '{cid}' links one household to itself; a "
                            f"relationship inside one household is persons[].relationship")
            continue
        for near, far, relation in ((ends[0], ends[1], tie["relation"]),
                                    (ends[1], ends[0], tie["mirror"])):
            doc = docs.get(near.get("household"))
            if doc is None:
                problems.append(f"ruling '{cid}' names household "
                                f"'{near.get('household')}', which this layer does not hold")
                continue
            row = kin_row(doc, near.get("person"), far.get("household"), far.get("person"))
            if row is None:
                problems.append(
                    f"ruling '{cid}' is {r['ruling']} and {near['household']} carries no "
                    f"kin row for {far.get('person')} — a ruling is written when the "
                    f"records say so, not when the ruling file does")
                continue
            if r["source"] not in (row.get("sources") or []):
                problems.append(
                    f"ruling '{cid}' is {r['ruling']} and the row on "
                    f"{near['household']} does not cite {r['source']}")
            if cid not in (row.get("book_kin") or []):
                problems.append(
                    f"the row on {near['household']} for {far.get('person')} does not "
                    f"name claim '{cid}' in book_kin, so the write is not re-derivable")

    # the reverse direction: a book_kin row nothing rules
    writing_claims = {cid for cid, r in ruled.items() if r.get("ruling") in WRITING}
    for hid, doc in sorted(docs.items()):
        for row in doc.get("kin") or []:
            for cid in row.get("book_kin") or []:
                if cid not in writing_claims:
                    problems.append(
                        f"{hid} carries a kin row citing claim '{cid}' and no ruling "
                        f"writes it. A row this pass wrote outlived its ruling.")

    if not quiet:
        for line in problems:
            print("  ERROR " + line)
    return problems


def report(candidates: list[dict]) -> None:
    ruled = (read_json(RULINGS).get("rulings") if RULINGS.exists() else {}) or {}
    print(f"KINSHIP STATED BY THE COMMITTED BOOK CORPUS ({TICKET})\n")
    print(f"  {len(claim_files()):6d}  books read")
    print(f"  {len(claims()):6d}  claims in the corpus")
    print(f"  {len(candidates):6d}  claims stating kinship")
    print(f"  {sum(1 for c in candidates if c['held_ends']):6d}  "
          f"…naming at least one person this town holds")
    by = Counter((ruled.get(c["claim"]) or {}).get("ruling", "UNRULED")
                 for c in candidates)
    print()
    for verdict, n in sorted(by.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:6d}  {verdict}")
    print()
    for c in candidates:
        r = ruled.get(c["claim"]) or {}
        print(f"  [{r.get('ruling', 'UNRULED'):20s}] {c['claim']}  ({c['source']})")
        print(f"       {c['reading'][:130]}")


def self_test() -> int:
    """Every assertion --check makes, broken on purpose."""
    fails = []

    def check_that(label, cond):
        if not cond:
            fails.append(label)
        print(("  ok   " if cond else "  FAIL ") + label)

    hh_a = {"id": "hh_a", "head": "p_a", "persons": [{"id": "p_a", "name": "John Doe"}]}
    hh_b = {"id": "hh_b", "head": "p_b", "persons": [{"id": "p_b", "name": "Sam Doe"}]}
    docs = {"hh_a": dict(hh_a), "hh_b": dict(hh_b)}
    cand = [{"claim": "bk_x_001", "source": "s", "file": "f", "describes_date": "1835",
             "terms": ["brother"], "reading": "John Doe, brother of Sam Doe.",
             "ends": [], "held_ends": []}]
    tie = {"a": {"household": "hh_a", "person": "p_a"},
           "b": {"household": "hh_b", "person": "p_b"},
           "relation": "brother", "mirror": "brother", "confidence": "inferred"}

    def ruling(**kw):
        base = {"ruling": "tie", "why": "w", "source": "s", "note": "n", "tie": tie}
        base.update(kw)
        return {"rulings": {"bk_x_001": base}}

    check_that("a kinship claim nobody has ruled on is an error",
               any("nobody has ruled" in p
                   for p in check(True, cand, {"rulings": {}}, docs)))
    check_that("a ruling with no reason is an error",
               any("no reason" in p for p in check(True, cand, ruling(why=" "), docs)))
    check_that("a ruling with no verdict is an error",
               any("no verdict" in p for p in check(True, cand, ruling(ruling="maybe"),
                                                    docs)))
    check_that("a ruling answering a claim that no longer states kinship is an error",
               any("no longer states" in p for p in check(True, [], ruling(), docs)))
    check_that("'tie' with no kin row on the record is an error",
               any("carries no kin row" in p for p in check(True, cand, ruling(), docs)))

    landed = {
        "hh_a": dict(hh_a, kin=[{"person": "p_a", "relation": "brother",
                                 "household": "hh_b", "value": "p_b",
                                 "sources": ["s"], "book_kin": ["bk_x_001"]}]),
        "hh_b": dict(hh_b, kin=[{"person": "p_b", "relation": "brother",
                                 "household": "hh_a", "value": "p_a",
                                 "sources": ["s"], "book_kin": ["bk_x_001"]}]),
    }
    check_that("'tie' with both reciprocal rows present passes",
               not check(True, cand, ruling(), landed))
    half = {"hh_a": json.loads(json.dumps(landed["hh_a"])), "hh_b": dict(hh_b)}
    check_that("a tie written on one card only is an error",
               any("carries no kin row" in p for p in check(True, cand, ruling(), half)))
    nosrc = json.loads(json.dumps(landed))
    for h in nosrc.values():
        for row in h.get("kin") or []:
            row["sources"] = ["something_else"]
    check_that("a written row that does not cite the book is an error",
               any("does not cite" in p for p in check(True, cand, ruling(), nosrc)))
    nolink = json.loads(json.dumps(landed))
    for h in nolink.values():
        for row in h.get("kin") or []:
            row["book_kin"] = []
    check_that("a written row that does not name its claim is an error",
               any("book_kin" in p for p in check(True, cand, ruling(), nolink)))
    check_that("a book_kin row no ruling writes is an error",
               any("outlived its ruling" in p
                   for p in check(True, cand, ruling(ruling="not_a_kinship"), landed)))
    check_that("a relation validate.py knows no inverse for is refused",
               any("no inverse" in p for p in check(
                   True, cand, ruling(tie=dict(tie, relation="uncle", mirror="nephew")),
                   landed)))
    check_that("a half brother mirrored as a plain brother is refused",
               any("flattening" in p for p in check(
                   True, cand, ruling(tie=dict(tie, relation="half_brother",
                                               mirror="brother")), landed)))
    check_that("a tie from one household to itself is refused",
               any("one household to itself" in p for p in check(
                   True, cand, ruling(tie=dict(tie, b={"household": "hh_a",
                                                       "person": "p_a"})), landed)))
    check_that("a ruling quoting a reading the claim no longer carries is an error",
               any("no longer carries" in p for p in check(
                   True, cand, ruling(reading="a sentence nowhere in this corpus"),
                   landed)))

    # The vocabulary and the resolver, on their own terms.
    check_that("the marriage verb is in the vocabulary the survey's pattern cannot see",
               bool(KIN_VOCABULARY.search("he married Welthyan Loomis in 1808")))
    check_that("'family' is NOT — a counted family is the reconstruction programme's",
               not KIN_VOCABULARY.search("the Gale family came ashore"))
    xwalk = Crosswalk({"merges": [{"from": "G. S. Hubbard", "into": "Gurdon S. Hubbard"}],
                       "refusals": [{"a": "J. Doe", "b": "John Doe"}]})
    check_that("a merge rewrites a book name to the resident it names",
               xwalk.names_for("G. S. Hubbard") == ["Gurdon S. Hubbard"])
    # 'J. Doe' folds onto 'John Doe' by the initial rule and would resolve; the crosswalk's
    # refusal is what stops it, which is the whole line this pass will not cross.
    check_that("a refused pair is blocked however well the names fold",
               resolve("J. Doe", Town(docs), xwalk)["held"] == []
               and resolve("J. Doe", Town(docs), xwalk)["refused_against"] == ["John Doe"])
    check_that("a book name nothing has identified resolves to nobody",
               resolve("Ezekiel Nobody", Town(docs), xwalk)["held"] == [])

    # The vocabulary this file declares must stay the one validate.py can check.
    try:
        import validate
        check_that("the writable relations are exactly validate.py's declared inverses",
                   {k: tuple(v) for k, v in INVERSES.items()}
                   == {k: tuple(v) for k, v in validate.RESIDENT_KIN_INVERSES.items()})
    except Exception as exc:                                  # pragma: no cover
        check_that(f"validate.py's inverse table is readable ({exc})", False)

    print(f"\n{len(fails)} failure(s)")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        problems = check()
        if problems:
            print(f"\n{len(problems)} problem(s) — see above")
            return 1
        print("the book corpus's kinship re-derives, and every claim carries a ruling")
        return 0
    if "--build" in argv:
        lines = build(read_json(RULINGS))
        for line in lines:
            print("  wrote " + line)
        print(f"{len(lines)} kin row(s) written or corroborated")
        return 0
    report(derive())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
