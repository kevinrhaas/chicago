#!/usr/bin/env python3
"""T-1350: a RULED READING supersedes the bound a mint derives, and cannot be reverted.

THE HOLE THIS CLOSES. Four passes mint `data/residents/households/*.json` from their
registers and derive `arrival` as a `not_later_than` BOUND — the earliest day a
committed record names the person, never the day they came. That is the right default
and it is the whole of what those registers can say. But a reading sometimes says more:
Moses and Kirkland's list of the spring of 1833 names men the town's paper does not
print until a year later, and their Baptist catalogue of 19 October 1833 puts three men
in the settlement two months before the tax roll gets to them. A reading like that
SUPERSEDES the derived bound.

Until now it could not. `carry_stage_blocks.carry()` carries a reconstruction stage's
blocks back across a mint's rewrite, and there was no equivalent for a reading, so a
hand-written `arrival` survived exactly until the next `--build` and then went away
without a word. T-1340 spent fifty-two book rulings onto the layer, watched seven of
them fail to reach the cards the crosswalk had already joined them to, and wrote the
failure down rather than leaving it as a silence. This is the mechanism it wanted.

AND SPENDING A READING HAS A PRICE THE LEDGER CHARGES BY THE CLAIM (T-1367). A card that
cites a claim id asserts that claim in `research_spend_ledger`, and the ledger's unit is
the WHOLE claim — so citing a fourteen-name catalogue on three cards marks all fourteen
names spent, and the eleven it reached nobody with fall off
`data/reconstruction/1835_borderline_roster.json`. Measured on this branch, 2026-09-19:
spending bk_mose2_010 that way dropped ten people T-1172 had re-admitted the day before.
So an entry here is cheap only where the claim is already asserted, which bk_mose1_005 is
(hh_kimball_walter cites it). Before adding one, run `readmit_borderline_roster.py
--check` and look at what leaves the roster. T-1367 owns the finer grain.

WHAT IT IS. A committed ledger — `data/research/residents/arrival_supersessions.json`
— naming, per household, the reading that supersedes the mint's bound, the crosswalk
merge that joins that reading to this card, the derived bound AS IT STOOD when the
ruling was made, and the block to write instead. The mints consult it where they derive
`arrival`, so everything downstream of the field — including the person note
`mint_civic_residents.py` composes out of it — is written from the superseded value.

WHAT IT IS NOT, AND THE FOUR REFUSALS THAT KEEP IT SO. It is not a way to write any
date onto any card:

  1. NO IDENTITY IS MADE HERE. An entry must name a merge already committed to a
     crosswalk, in that crosswalk's own words. Joining a reading to a card is the
     crosswalk's job and stays there; this file only spends a join that exists.
  2. NO READING IS INVENTED HERE. An entry must name a claim id that exists in the
     claims file it names, and the source must be in `data/sources/`.
  3. A SUPERSESSION MUST SUPERSEDE. The ruled value has to be EARLIER than the bound
     it replaces. A reading no earlier than the register's own bound tells the card
     nothing it does not already hold, and an entry that moved a date LATER would be
     loosening a bound while claiming to tighten one.
  4. THE GRADE CEILING IS THE SOURCE'S. A claim read `transcription_mediated` may not
     be graded above `inferred`, whatever it plainly prints — the rule T-1322 set for
     the settlers table of this same compiler, kept here.

AND THE DRIFT IS LOUD, WHICH IS THE POINT. Each entry banks the derived bound it was
ruled against. If a mint hands this module a DIFFERENT bound — the register grew a
column, an identity gained an appearance — the ruling was made against evidence that
has moved, and `supersede()` REFUSES rather than overwriting the new bound with an old
ruling. A human re-rules and re-banks. That is the opposite of the failure above: the
old behaviour lost the reading in silence, this one stops the build and says which
card and which two dates.

  python3 tools/supersede_arrival.py --check
  python3 tools/supersede_arrival.py --self-test
  python3 tools/supersede_arrival.py --report
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "research" / "residents" / "arrival_supersessions.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
SOURCES = ROOT / "data" / "sources"

# The mints that derive `arrival` and must therefore consult this ledger. Named rather
# than discovered, for the reason `carry_stage_blocks.WIRED_MINTS` is: a mint that
# quietly stopped consulting would revert a ruled reading on its next `--build`, which
# is the exact failure this module exists to end, and a shorter list would hide it.
WIRED_MINTS = {
    "tools/mint_documented_residents.py",
    "tools/mint_letter_list_residents.py",
    "tools/mint_placed_residents.py",
    "tools/mint_civic_residents.py",
}
# The wiring asserted below, and the ORDER is part of it: `carry` seats a
# reconstruction stage's blocks back into the re-derived record, and `supersede` then
# rules on the `arrival` that record actually carries. If a stage ever did own an
# `arrival` block, the two would meet here and the refusal below would say so out loud
# rather than one of them quietly winning.
CALL = "supersede(carry(doc))"

# Refusal 4. What a reading of each kind may be graded at, at most. `scan_verified` is
# absent deliberately: no claim spent through this file has been read off a scan yet,
# and a ceiling for a reading nobody has made would be a rule with no case.
CEILING = {
    "transcription_mediated": "inferred",
}
GRADES = ["reconstructed", "conjectural", "inferred", "attested", "documented"]


def load_ledger(path: Path | None = None) -> dict:
    path = path or LEDGER
    if not path.exists():
        return {"entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


_INDEX: dict | None = None


def by_household(ledger: dict | None = None) -> dict:
    """The ledger keyed by household. Cached: a mint asks this once per record."""
    global _INDEX
    if ledger is not None:
        return {e["household"]: e for e in ledger.get("entries") or []}
    if _INDEX is None:
        _INDEX = {e["household"]: e for e in load_ledger().get("entries") or []}
    return _INDEX


class Reverted(SystemExit):
    """A mint derived a bound the standing ruling was not made against."""


def supersede_block(hid: str, arrival: dict, index: dict | None = None) -> dict:
    """`arrival` as the ruled reading leaves it, or unchanged if nothing rules on it.

    Idempotent: handed the block it has already written, it returns it. Handed the
    bound the ruling was banked against, it returns the ruling. Handed anything else
    it refuses — see the drift paragraph above.
    """
    entry = (by_household() if index is None else index).get(hid)
    if not entry:
        return arrival
    ruled = entry["arrival"]
    if arrival == ruled:
        return dict(ruled)
    banked = entry["supersedes"]
    got = {k: arrival.get(k) for k in banked}
    if got != banked:
        raise Reverted(
            f"{hid}: the register has moved under a standing arrival ruling. "
            f"{LEDGER.relative_to(ROOT)} banks the derived bound "
            f"{banked.get('value')} ({banked.get('precision')}) and this mint now "
            f"derives {got.get('value')} ({got.get('precision')}). The ruling "
            f"({entry['ruled_by']}, claim {entry['claim']['id']}) was made against "
            f"evidence that has changed: re-rule it and re-bank the bound. Nothing "
            f"is written until that is done."
        )
    return dict(ruled)


def supersede(doc: dict, index: dict | None = None) -> dict:
    """`doc` with its `arrival` superseded by the ruled reading, if one rules on it.

    The doc-level form, and the one every mint calls at its write site so the wiring
    reads the same in all four. A mint that composes other fields OUT of `arrival`
    calls `supersede_block` where it derives the field instead, so those fields are
    written from the superseded value too — `mint_civic_residents.py` does, because
    its person note quotes the arrival note verbatim.
    """
    arrival = doc.get("arrival")
    if not isinstance(arrival, dict):
        return doc
    out = supersede_block(doc.get("id"), arrival, index)
    if out is arrival or out == arrival:
        return doc
    return {k: (out if k == "arrival" else v) for k, v in doc.items()}


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

def check_entry(entry: dict, claims_cache: dict) -> list:
    """Every refusal above, applied to one entry. Returns the failures as strings."""
    bad = []
    hid = entry.get("household") or "<no household>"

    # Refusal 2, first half: the card exists.
    card = HOUSEHOLDS / f"{hid}.json"
    if not card.exists():
        return [f"{hid}: no such household record at {card.relative_to(ROOT)}"]

    ruled, banked = entry.get("arrival") or {}, entry.get("supersedes") or {}

    # Refusal 2: the reading exists, in the file this entry names.
    claim = entry.get("claim") or {}
    cpath = ROOT / str(claim.get("file") or "")
    if not cpath.exists():
        bad.append(f"{hid}: claims file {claim.get('file')!r} does not exist")
    else:
        if str(cpath) not in claims_cache:
            claims_cache[str(cpath)] = {
                c["id"]: c for c in json.loads(cpath.read_text(encoding="utf-8")).get("claims") or []
            }
        found = claims_cache[str(cpath)].get(claim.get("id"))
        if not found:
            bad.append(f"{hid}: {claim.get('file')} carries no claim {claim.get('id')!r}")
        else:
            # Refusal 4: the grade ceiling is the reading's own.
            cap = CEILING.get(found.get("reading"))
            if cap and GRADES.index(ruled.get("confidence") or "reconstructed") > GRADES.index(cap):
                bad.append(
                    f"{hid}: claim {claim.get('id')} is read {found.get('reading')!r} and "
                    f"nothing off it may be graded above {cap!r} — this entry writes "
                    f"{ruled.get('confidence')!r}"
                )
            if str(claim.get("id")) not in (ruled.get("note") or ""):
                bad.append(f"{hid}: the arrival note does not cite claim {claim.get('id')} — "
                           f"a reader of the card cannot reach the page it came off")

    # Refusal 1: the identity is the crosswalk's, and it is already committed there.
    cross = entry.get("crosswalk") or {}
    xpath = ROOT / str(cross.get("file") or "")
    if not xpath.exists():
        bad.append(f"{hid}: crosswalk {cross.get('file')!r} does not exist")
    else:
        merges = json.loads(xpath.read_text(encoding="utf-8")).get("merges") or []
        if not any(m.get("into") == cross.get("into") and m.get("from") == cross.get("from")
                   and m.get("claim_id") == claim.get("id") for m in merges):
            bad.append(
                f"{hid}: {cross.get('file')} carries no merge of {cross.get('from')!r} into "
                f"{cross.get('into')!r} on claim {claim.get('id')} — an identity is the "
                f"crosswalk's to make and this file may only spend one it already made")

    # Refusal 2, second half: the sources are registered ones.
    for sid in ruled.get("sources") or []:
        if not (SOURCES / f"{sid}.json").exists():
            bad.append(f"{hid}: arrival cites source {sid!r}, which is not in data/sources/")

    # Refusal 3: a supersession supersedes.
    if not banked.get("value") or not ruled.get("value"):
        bad.append(f"{hid}: an entry needs both the banked bound and the ruled value")
    elif str(ruled["value"]) >= str(banked["value"]):
        bad.append(
            f"{hid}: the ruled value {ruled['value']} is not earlier than the bound it "
            f"replaces ({banked['value']}) — a reading that does not tighten the bound "
            f"supersedes nothing")

    # And the layer agrees with the ledger: the card carries what this file rules.
    on_disk = json.loads(card.read_text(encoding="utf-8")).get("arrival")
    if on_disk != ruled:
        bad.append(f"{hid}: the committed card's arrival is not the one this ledger rules — "
                   f"card {(on_disk or {}).get('value')!r}, ledger {ruled.get('value')!r}")
    return bad


def cmd_check() -> int:
    missing = [m for m in sorted(WIRED_MINTS)
               if CALL not in (ROOT / m).read_text(encoding="utf-8")]
    for m in missing:
        print(f"  FAIL {m} derives `arrival` and does not call {CALL} - its next --build "
              f"would silently revert every ruled reading this ledger holds")
    ledger, cache = load_ledger(), {}
    bad = []
    for entry in ledger.get("entries") or []:
        for line in check_entry(entry, cache):
            print(f"  FAIL {line}")
            bad.append(line)
    if missing or bad:
        return 1
    n = len(ledger.get("entries") or [])
    kinds = sorted({e.get("kind") for e in ledger.get("entries") or []})
    print(f"  OK: {len(WIRED_MINTS)} mint(s) consult the ledger; {n} ruled reading(s) "
          f"supersede a derived bound ({', '.join(kinds) or 'none yet'}), each joined by a "
          f"committed crosswalk merge and each earlier than the bound it replaces")
    return 0


def cmd_report() -> int:
    for e in load_ledger().get("entries") or []:
        print(f"{e['household']}: {e['supersedes']['value']} ({e['supersedes']['precision']}) "
              f"-> {e['arrival']['value']} ({e['arrival']['precision']})  "
              f"{e['kind']}  {e['claim']['id']}  {e['ruled_by']}")
    return 0


def self_test() -> int:
    failures = 0

    def check(name, got, want):
        nonlocal failures
        if got != want:
            failures += 1
            print(f"  FAIL {name}: {got!r} != {want!r}")
        else:
            print(f"  ok    {name}")

    banked = {"value": "1834-02-18", "precision": "not_later_than"}
    ruled = {"value": "1833-03-01", "confidence": "inferred", "sources": ["s"],
             "note": "the spring of 1833", "precision": "season"}
    index = {"hh_x": {"household": "hh_x", "ruled_by": "T-1340", "kind": "arrival",
                      "claim": {"id": "bk_x", "file": "f"}, "supersedes": banked,
                      "arrival": ruled}}
    mint = {"id": "hh_x", "arrival": dict(banked, confidence="inferred", sources=["p"],
                                          note="A BOUND FROM THE PAPER"), "persons": []}

    out = supersede(json.loads(json.dumps(mint)), index)
    check("the ruled reading replaces the bound the mint derived", out["arrival"], ruled)
    check("and nothing else on the record moves", [k for k in out], ["id", "arrival", "persons"])

    again = supersede(json.loads(json.dumps(out)), index)
    check("handed its own output it is a no-op, so a second hook cannot double-apply",
          again["arrival"], ruled)

    other = {"id": "hh_y", "arrival": dict(mint["arrival"])}
    check("a card no reading rules on is untouched",
          supersede(json.loads(json.dumps(other)), index)["arrival"], mint["arrival"])

    moved = json.loads(json.dumps(mint))
    moved["arrival"]["value"] = "1833-11-26"
    try:
        supersede(moved, index)
        check("a bound the ruling was NOT made against is refused", "no refusal", "Reverted")
    except Reverted as exc:
        check("a bound the ruling was NOT made against is refused",
              "1833-11-26" in str(exc) and "1834-02-18" in str(exc), True)

    # the refusals, each on its own case, read through the real gate
    real = by_household()
    cache: dict = {}
    entries = list(load_ledger().get("entries") or [])
    check("the committed ledger passes its own gate",
          [l for e in entries for l in check_entry(e, cache)], [])
    if entries:
        loosened = json.loads(json.dumps(entries[0]))
        loosened["arrival"]["value"] = "1899-01-01"
        check("refusal 3: a reading LATER than the bound is not a supersession",
              any("supersedes nothing" in l for l in check_entry(loosened, cache)), True)
        upgraded = json.loads(json.dumps(entries[0]))
        upgraded["arrival"]["confidence"] = "documented"
        check("refusal 4: a transcription-mediated reading cannot be graded above inferred",
              any("may be graded above" in l or "graded above" in l
                  for l in check_entry(upgraded, cache)), True)
        unjoined = json.loads(json.dumps(entries[0]))
        unjoined["crosswalk"]["from"] = "Somebody Else"
        check("refusal 1: a join no crosswalk made is refused",
              any("crosswalk's to make" in l for l in check_entry(unjoined, cache)), True)
        invented = json.loads(json.dumps(entries[0]))
        invented["claim"]["id"] = "bk_nobody_999"
        check("refusal 2: a claim id no claims file carries is refused",
              any("carries no claim" in l for l in check_entry(invented, cache)), True)
        check("every entry names a household this layer holds",
              sorted(real) == sorted(e["household"] for e in entries), True)

    missing = [m for m in sorted(WIRED_MINTS)
               if CALL not in (ROOT / m).read_text(encoding="utf-8")]
    check("every mint that derives an arrival still consults the ledger", missing, [])
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return cmd_check()
    if args.report:
        return cmd_report()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
