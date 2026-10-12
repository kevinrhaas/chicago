#!/usr/bin/env python3
"""T-2191: the register's parent ties, written onto the cards a build writes whole.

    python3 tools/generated_card_kin.py              the ties, on stdout
    python3 tools/generated_card_kin.py --land       write the household-side rows
    python3 tools/generated_card_kin.py --check      both ends carry every tie, and nothing else
    python3 tools/generated_card_kin.py --self-test  the derivation, broken on purpose

WHY THIS EXISTS. The family pass (T-1335) read St Mary's register and found twelve
parent ties whose two ends are both cards the town holds, where one end is a card a BUILD
writes whole: a readmitted card (tools/readmit_borderline_roster.py, T-1172) or one of the
register's own underdocumented cards (tools/reconstruct_church_register.py, T-1504). A kin
row typed onto such a card is gone the next time its stage runs, and the kin survey
(tools/survey_stated_kin.py) reads households/ only, so it never proposes them. Thirteen
units stood `unresolved` on T-2191 for that reason and nothing else.

WHAT IS DERIVED, AND FROM WHAT. Nothing here is authored. A tie is read off ONE register
entry and resolved BY BACK-LINK, never by name — the rule T-0734 set:

  * the generated end is the card the build wrote from that row (the readmission's own
    `row_id`, or the underdocumented card's `entries_that_name_her[]`), passed in by the
    generator that owns the card;
  * the far end is the ONE households/ card whose person carries that entry's other row
    as its own evidence (`*_evidence[]` or `appearance_bounds[]`). Two claimants is an
    identity the town has not settled, and no tie is written onto either;
  * the parent's term is the register's role (`father`, `mother`); the child's term is
    READ OFF THE ENTRY'S OWN WORDS — `son`/`fils`, `daughter(s)`/`fille` — and never off a
    card's `sex`, which for most of the register's children is a draw. An entry that prints
    both words, or neither, writes no tie.

BOTH ENDS, ONE DERIVATION. The generator calls `kin_rows()` for its own card, and `--land`
writes the mirror onto the households/ card from the same `ties()`, so the two rows cannot
disagree. households/ cards are re-derived by the mints, which carry a `kin` block through
(tools/resident_mint_carry.py), so the household side survives a rebuild the way every
landed kin-survey row does. NOBODY IS MINTED AND NO HOUSEHOLD GAINS A MEMBER: a kin row is
the link between two cards the town already holds (T-1312, T-1320, T-0849).
"""
from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
GENERATED_DIRS = ("readmitted", "underdocumented")
REGISTER_FILE = "data/research/church/records/st_marys_baptisms_1833_1835.json"
REGISTER_SOURCE = "st_marys_baptismal_register_1833_1835"
ROW_PREFIX = f"church:{REGISTER_FILE}#records/"
TICKET = "T-2191"

PARENT_ROLES = ("father", "mother")
CHILD_WORDS = {"son": "son", "fils": "son",
               "daughter": "daughter", "daughters": "daughter",
               "fille": "daughter", "filles": "daughter"}
CHILD_WORD = re.compile(r"\b(" + "|".join(CHILD_WORDS) + r")\b", re.I)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def register_record_id(row_id: str) -> str | None:
    """`church:<register>#records/<id>#0` -> `<id>`; any other domain's row -> None."""
    row_id = str(row_id or "")
    if not row_id.startswith(ROW_PREFIX):
        return None
    return row_id[len(ROW_PREFIX):].split("#")[0] or None


@functools.lru_cache(maxsize=None)
def register() -> tuple[dict, dict]:
    """record id -> record, and (year_series, entry) -> the entry's records."""
    by_id, by_entry = {}, {}
    for r in read_json(ROOT / REGISTER_FILE).get("records") or []:
        loc = r.get("locator") or {}
        by_id[r["id"]] = r
        by_entry.setdefault((loc.get("year_series"), loc.get("entry")), []).append(r)
    return by_id, by_entry


@functools.lru_cache(maxsize=None)
def household_claims() -> dict[str, tuple[tuple[str, str], ...]]:
    """record id -> the (household, person) on households/ that claim it as their own.

    The same back-link spend_family_pass.claims() reads, restricted to households/: a
    person's `*_evidence[]` and `appearance_bounds[]`. Only households/ is a far end here,
    because a tie between two generated cards would need both builds to agree and no unit
    asks for one.
    """
    out: dict[str, list] = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = read_json(path)
        for p in doc.get("persons") or []:
            for key, block in p.items():
                if (key.endswith("_evidence") or key == "appearance_bounds") \
                        and isinstance(block, list):
                    for e in block:
                        rid = e.get("record_id") if isinstance(e, dict) else None
                        if isinstance(rid, str) and (path.stem, p.get("id")) not in out.get(rid, []):
                            out.setdefault(rid, []).append((path.stem, p.get("id")))
    return {k: tuple(v) for k, v in out.items()}


def role(r: dict) -> str:
    return str((r.get("cells") or {}).get("role") or (r.get("locator") or {}).get("role") or "")


def child_term(entry_text: str) -> str | None:
    """The one child word the entry prints, or None where it prints neither or both."""
    terms = {CHILD_WORDS[w.lower()] for w in CHILD_WORD.findall(entry_text or "")}
    return terms.pop() if len(terms) == 1 else None


def ties_for(hid: str, pid: str, record_ids, claims=None, reg=None) -> tuple[list, list]:
    """Every parent tie the register states between this generated card and a households/
    card, and every one it states and this derivation declines, with the reason."""
    claims = household_claims() if claims is None else claims
    by_id, by_entry = register() if reg is None else reg
    ties, declined = [], []
    for rid in sorted(set(record_ids)):
        me = by_id.get(rid)
        if me is None:
            continue
        loc = me.get("locator") or {}
        text = (me.get("cells") or {}).get("entry_as_read") or ""
        mine = role(me)
        if claims.get(rid):
            # The row is ALREADY a households/ person's evidence: this generated card is a
            # second card of one reading, which is the consolidation's to rule
            # (tools/consolidate_town_cards.py). Tying it would give the far end a second
            # parent; the households/ card owns the row and the kin survey owns its ties.
            declined.append({"record": rid, "other_record": None,
                             "why": (f"{rid} is already carried by households/ "
                                     f"{', '.join(h for h, _ in claims[rid])}: this card is "
                                     f"a duplicate of that one, and no tie is written onto a "
                                     f"duplicate")})
            continue
        if mine in PARENT_ROLES:
            others = [o for o in by_entry[(loc.get("year_series"), loc.get("entry"))]
                      if role(o) == "child"]
        elif mine == "child":
            others = [o for o in by_entry[(loc.get("year_series"), loc.get("entry"))]
                      if role(o) in PARENT_ROLES]
        else:
            continue
        for o in others:
            held = claims.get(o["id"]) or ()
            if not held:
                continue
            if len(held) > 1:
                declined.append({"record": rid, "other_record": o["id"],
                                 "why": (f"{o['id']} is claimed by {len(held)} households/ "
                                         f"cards ({', '.join(h for h, _ in held)}): the town "
                                         f"has not settled who the row is, so no tie is "
                                         f"written onto either")})
                continue
            term = child_term(text)
            if term is None:
                declined.append({"record": rid, "other_record": o["id"],
                                 "why": "the entry prints no single son/daughter word"})
                continue
            far_hid, far_pid = held[0]
            parent_rec, child_rec = (me, o) if mine in PARENT_ROLES else (o, me)
            parent_term = role(parent_rec)
            ties.append({
                "household": hid, "person": pid,
                "relation": parent_term if mine in PARENT_ROLES else term,
                "far_household": far_hid, "far_person": far_pid,
                "mirror": term if mine in PARENT_ROLES else parent_term,
                "records": [rid, o["id"]],
                "entry": f"{loc.get('entry')} of {loc.get('year_series')}",
                "entry_as_read": text,
                "child_word": next((w for w in CHILD_WORD.findall(text)), ""),
                "parent_as_read": parent_rec.get("as_read"),
                "child_as_read": child_rec.get("as_read"),
            })
    return ties, declined


def _row(near_hid, near_pid, relation, far_hid, far_pid, tie, generated_end: str) -> dict:
    return {
        "person": near_pid, "relation": relation,
        "household": far_hid, "value": far_pid,
        "confidence": "attested", "sources": [REGISTER_SOURCE],
        "note": (f"STATED IN THE REGISTER'S OWN WORDS, AND RESOLVED BY BACK-LINK, NOT BY "
                 f"NAME ({TICKET}). Entry {tie['entry']}: {tie['entry_as_read']} The two "
                 f"cards are the ones that carry this entry's rows ({tie['records'][0]}, "
                 f"{tie['records'][1]}), so no identification is made here. The parent's "
                 f"term is the register's role column; the child's is the entry's own word, "
                 f"'{tie['child_word']}'. {generated_end} is written whole by its build, and "
                 f"tools/generated_card_kin.py derives both rows of this tie from the one "
                 f"entry, so a rebuild writes them again rather than losing one."),
    }


def kin_rows(hid: str, pid: str, record_ids) -> list[dict]:
    """The generated card's own rows — what its build writes into `kin`."""
    ties, _ = ties_for(hid, pid, record_ids)
    rows = [_row(hid, pid, t["relation"], t["far_household"], t["far_person"], t, hid)
            for t in ties]
    return sorted(rows, key=lambda k: (k["person"], k["household"], k["value"]))


def with_kin(card: dict, rows: list[dict]) -> dict:
    """The card with `kin` in its conventional slot, immediately before `persons`."""
    card = {k: v for k, v in card.items() if k != "kin"}
    if not rows:
        return card
    out = {}
    for k, v in card.items():
        if k == "persons":
            out["kin"] = rows
        out[k] = v
    return out


def generated_cards() -> dict[str, tuple[str, str, list[str]]]:
    """hid -> (directory, head person, the register record ids the card stands on)."""
    out = {}
    for d in GENERATED_DIRS:
        for path in sorted((RESIDENTS / d).glob("*.json")):
            doc = read_json(path)
            rids = []
            rid = register_record_id((doc.get("readmission") or {}).get("row_id"))
            if rid:
                rids.append(rid)
            for e in (doc.get("underdocumented") or {}).get("entries_that_name_her") or []:
                if isinstance(e, dict) and e.get("record_id"):
                    rids.append(e["record_id"])
            if rids:
                out[path.stem] = (d, doc.get("head"), rids)
    return out


def ties() -> tuple[list, list]:
    all_ties, all_declined = [], []
    for hid, (_, pid, rids) in sorted(generated_cards().items()):
        t, d = ties_for(hid, pid, rids)
        all_ties += t
        all_declined += [dict(x, household=hid) for x in d]
    return all_ties, all_declined


def household_rows() -> dict[str, list[dict]]:
    """households/ hid -> the mirror rows the ties owe it."""
    out: dict[str, list] = {}
    for t in ties()[0]:
        out.setdefault(t["far_household"], []).append(
            _row(t["far_household"], t["far_person"], t["mirror"],
                 t["household"], t["person"], t, t["household"]))
    return out


def _is_ours(row: dict) -> bool:
    return f"({TICKET})" in str(row.get("note") or "")


def land(apply: bool = True) -> list[str]:
    """Write every tie's households/ row; withdraw ours that no tie derives any more."""
    owed = household_rows()
    drift = []
    touched = set(owed)
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = read_json(path)
        if any(_is_ours(k) for k in doc.get("kin") or []):
            touched.add(path.stem)
    for hid in sorted(touched):
        path = HOUSEHOLDS / f"{hid}.json"
        doc = read_json(path)
        kept = [k for k in doc.get("kin") or [] if not _is_ours(k)]
        rows = sorted(kept + owed.get(hid, []),
                      key=lambda k: (k.get("person") or "", k.get("value") or ""))
        new = with_kin(doc, rows)
        if new != doc:
            drift.append(f"data/residents/households/{hid}.json")
            if apply:
                path.write_text(json.dumps(new, indent=1, ensure_ascii=False) + "\n",
                                encoding="utf-8")
    return drift


def check() -> list[str]:
    problems = [f"{p}: does not carry the rows the register's ties owe it; run --land"
                for p in land(apply=False)]
    for hid, (d, pid, rids) in sorted(generated_cards().items()):
        doc = read_json(RESIDENTS / d / f"{hid}.json")
        if (doc.get("kin") or []) != kin_rows(hid, pid, rids):
            problems.append(f"data/residents/{d}/{hid}.json: its kin is not what the register "
                            f"derives; rebuild it with the generator that owns the card")
    return problems


def self_test() -> int:
    failures = []

    def case(label, ok):
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            failures.append(label)

    def rec(rid, r, entry=1, text="baptised Joseph son of Michel and Marguerite"):
        return {"id": rid, "as_read": rid, "locator": {"year_series": 1833, "entry": entry},
                "cells": {"role": r, "entry_as_read": text}}

    def reg(*rows):
        by_entry = {}
        for r in rows:
            by_entry.setdefault((1833, r["locator"]["entry"]), []).append(r)
        return {r["id"]: r for r in rows}, by_entry

    m, c, f = rec("m", "mother"), rec("c", "child"), rec("f", "father")
    one = {"c": (("hh_child", "child"),)}
    t, _ = ties_for("hh_m", "mum", ["m"], one, reg(m, c, f))
    case("a mother's row ties to the one card claiming the child",
         len(t) == 1 and t[0]["relation"] == "mother" and t[0]["mirror"] == "son")
    t, d = ties_for("hh_m", "mum", ["m"], {"c": (("hh_a", "a"), ("hh_b", "b"))}, reg(m, c))
    case("two cards claiming the far row write no tie, and say so", not t and len(d) == 1)
    t, _ = ties_for("hh_m", "mum", ["m"], {}, reg(m, c))
    case("a far row nobody carries writes nothing", not t)
    both = rec("m", "mother", text="baptised Pierre fils and Marie fille of X")
    t, d = ties_for("hh_m", "mum", ["m"], one, reg(both, rec("c", "child", text="")))
    case("an entry printing both child words writes no tie", not t and len(d) == 1)
    kid = rec("c", "child", text="baptised Isabelle daughter of Andrew and Adelaide")
    t, _ = ties_for("hh_c", "kid", ["c"], {"m": (("hh_mum", "mum"),)}, reg(kid, m))
    case("a child's row takes the entry's word and gives the parent's role back",
         len(t) == 1 and t[0]["relation"] == "daughter" and t[0]["mirror"] == "mother")
    t, d = ties_for("hh_dup", "dup", ["m"], dict(one, m=(("hh_mum", "mum"),)), reg(m, c))
    case("a generated card whose own row households/ carries is a duplicate, and is not tied",
         not t and len(d) == 1)
    sponsor = rec("s", "sponsor")
    t, _ = ties_for("hh_s", "s", ["s"], one, reg(sponsor, c))
    case("a sponsor is not kin", not t)
    case("a non-register row reads as no record id",
         register_record_id("newspapers:x.json#records/y#0") is None
         and register_record_id(ROW_PREFIX + "abc#0") == "abc")
    case("kin is slotted immediately before persons",
         list(with_kin({"a": 1, "persons": [], "z": 2}, [{"x": 1}])) == ["a", "kin", "persons", "z"])
    print(f"self-test | {len(failures)} failure(s)")
    return 1 if failures else 0


def report() -> int:
    t, d = ties()
    for x in t:
        print(f"  {x['household']}/{x['person']} is the {x['relation']} of "
              f"{x['far_household']}/{x['far_person']}  (entry {x['entry']})")
    for x in d:
        print(f"  declined {x['household']} {x['record']} -> {x['other_record']}: {x['why']}")
    print(f"generated-card kin: {len(t)} tie(s), {len(d)} declined")
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--land", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.land:
        for p in land():
            print(f"  wrote {p}")
        return 0
    if args.check:
        problems = check()
        for p in problems:
            print(f"  FAIL {p}")
        if not problems:
            print(f"  ok    {len(ties()[0])} register tie(s) onto generated cards carried on "
                  f"both ends")
        return 1 if problems else 0
    return report()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
