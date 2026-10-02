#!/usr/bin/env python3
"""The yard-by-household rule: what a dwelling's yard holds says whose house it is.

T-1959, piece 2 of T-1212. The owner's ask for the yards is one sentence — *"lot-line and
dooryard fences, gardens, woodpiles, wells, privies and stables assigned by household type"*
— and T-1212 put the rule in the placement policy, beside the fabric rule (T-1816) that
already says whose house a roof is. This module is that rule's home. It holds the WOODPILE
column today; the wells, privies and stables (T-1960) and the trade goods (T-1961) are the
columns still to be written into it, and they go here rather than into a module of their own,
for the reason `placement_policy_1835.py` exists at all: one rule, one home, one table the
build tickets build by.

WHO THE HOUSEHOLD IS — read, never re-dealt. The class is the fabric rule's own:

1. **The roof's `fabric_basis.class`**, where `tools/fabric_rule_1835.py` dealt one. That is
   every reconstructed roof, and it already prefers the keeper a seat WROTE onto the roof
   (their trade) over the family's label. Reading it here means a merchant's painted house
   and a merchant's woodpile can never disagree about who lives there.
2. **A household that lives there**, for a documented roof the fabric rule does not touch:
   `enclosure_owners.household_links()` (the committed `lives_at` join), and that
   household's trade through `seat_known_1835.TRADE_CLAUSE` — the same two reads the fabric
   rule makes for a keeper.
3. **The occupation a reconstruction names** (`reconstruction.occupation`, the inferred
   dwellings), through the same clause table.
4. **Otherwise a tradesman's** — the town's modal household, stated as the default so a
   documented house nobody has a trade for is not quietly made poorer or richer than the
   evidence says. The card says when this is the basis.

WHAT THE HOUSE IS — the second axis, the wealth INSIDE a class. A labourer's family in a
shanty and one in a log cabin did not keep wood the same way, and nor did a tradesman in a
one-room cottage and one in a two-storey house. The house is read off the roof's own family
label and archetype, never off a deal.

WHAT EACH HOUSEHOLD KEEPS (`WOODPILE`). Every cell is reconstructed; the bounds are:

* the town burned wood — the Chicago Democrat's weekly price current quotes firewood by the
  cord through the summer of 1835 (`chicago_democrat_1833_1835`, 27 May 1835 c001: $2.50
  the cord; 12 August 1835 c002: $2.00);
* a cord is 8 ft long, 4 ft high and 4 ft wide, and the wood of the country round Chicago was
  white oak, hickory, white ash and maple — the quartermaster's notice for five hundred
  cords at Fort Dearborn (4 June 1835 c008, reprinted 1 July c018);
* July is the low point of a household's year in wood: a winter's stock was laid in through
  the autumn and sledded in on the snow, so every pile here is dealt at less than its full
  height, and the houses that bought by the cord show it as cords.

Money is what separates the rows. A merchant's or a keeper's household BOUGHT its wood, and it
came as cordwood — 4 ft sticks racked 8 ft long — so their piles are cords. A tradesman's
household bought less at a time and sawed it to the stove's length, so its piles are short
ricks of 2 ft wood by the back door, with a chopping block. A labourer's household in a cabin
hauled its own, so its pile is unsplit lengths on two skids, worked off with an axe at the
block; and a shanty kept what came to hand — mill slabs and drift — in a heap. None of this is
a reading of any one house. It is a bound on a reconstruction, written down where it can be
argued with, and it is docs/LIBERTIES.md L356.

    python3 tools/yard_rule_1835.py              print the rule as the policy carries it
    python3 tools/yard_rule_1835.py --self-test  the rule's guarantees, by breaking them
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"

#: The fabric rule's classes this rule reads. `works` is the fabric rule's class for a
#: heavy-trades household — a smith, a tanner — and it keeps a tradesman's house.
CLASS_ALIASES = {"works": "tradesman", "freight": "tradesman", "yard": "tradesman"}
CLASSES = ("labourer", "tradesman", "merchant", "keeper")

#: The house inside a class. Families from the reconstruction spec's own labels
#: (`fabric_rule_1835.CLASS_OF_FAMILY` quotes them); a documented roof without a family
#: is read by its archetype and, for a frame house, by its footprint.
LARGER_FAMILIES = {"D5", "D6", "D7", "H1", "H2"}
LARGER_HOUSE_M2 = 55.0

#: The woodpile column of the rule. `rule` is the id a card and a record cite; `kinds` is
#: what yard.js draws; every range is dealt inside, per house, by a hash of the roof id.
WOODPILE: dict[str, dict] = {
    "shanty": {
        "rule": "Y-W1", "who": "a labourer's shanty",
        "kind": "slab_heap", "pieces": (7, 12), "block": False,
        "why": "a shanty bought no cords; it kept what came to hand — mill slabs off the "
               "sawmills and wood off the shore — in a loose heap at the wall",
    },
    "cabin": {
        "rule": "Y-W2", "who": "a labourer's log cabin",
        "kind": "log_heap", "logs": (3, 5), "log_length_m": (2.4, 3.6), "block": True,
        "why": "a cabin household hauled its own, as unsplit lengths laid on two skids, "
               "and worked them off with an axe at the block as the fire wanted",
    },
    "cottage": {
        "rule": "Y-W3", "who": "a tradesman's cottage",
        "kind": "cordwood", "stick": "stove", "ricks": (1, 1),
        "length_m": (1.6, 2.6), "height_m": (0.6, 1.1), "block": True,
        "why": "a tradesman bought a little at a time and sawed it to the stove's length: one "
               "short rick of 2 ft wood by the back door, and the block beside it",
    },
    "house": {
        "rule": "Y-W4", "who": "a tradesman's larger house",
        "kind": "cordwood", "stick": "stove", "ricks": (1, 2),
        "length_m": (2.2, 3.4), "height_m": (0.7, 1.2), "block": True,
        "why": "more rooms, more fires: a longer rick of stove wood, a second on some",
    },
    "merchant": {
        "rule": "Y-W5", "who": "a merchant's or professional man's house",
        "kind": "cordwood", "stick": "cord", "ricks": (1, 2),
        "length_m": (2.44, 2.44), "height_m": (0.75, 1.22), "block": True,
        "why": "money bought the wood by the cord, delivered as 4 ft sticks racked 8 ft long, "
               "and a household that bought by the cord shows it as cords",
    },
    "keeper": {
        "rule": "Y-W6", "who": "a boarding house, tavern or hotel",
        "kind": "cordwood", "stick": "cord", "ricks": (2, 3),
        "length_m": (2.44, 2.44), "height_m": (0.9, 1.22), "block": True,
        "why": "a house that cooked for the public burned the most and bought the most: two "
               "or three cords racked behind it even at the summer's low",
    },
}

#: class x house -> row. The table IS the rule: `--self-test` refuses a class or a house it
#: does not cover, so a new family cannot fall through to a silent default.
ROW_OF: dict[tuple[str, str], str] = {
    ("labourer", "shanty"): "shanty", ("labourer", "log"): "cabin",
    ("labourer", "small"): "cottage", ("labourer", "larger"): "cottage",
    ("tradesman", "shanty"): "cottage", ("tradesman", "log"): "cottage",
    ("tradesman", "small"): "cottage", ("tradesman", "larger"): "house",
    ("merchant", "shanty"): "merchant", ("merchant", "log"): "merchant",
    ("merchant", "small"): "merchant", ("merchant", "larger"): "merchant",
    ("keeper", "shanty"): "keeper", ("keeper", "log"): "keeper",
    ("keeper", "small"): "keeper", ("keeper", "larger"): "keeper",
}

FABRIC_CLASS = re.compile(r'"fabric_basis": \{\s*"rule": "[^"]+",\s*"class": "(\w+)"')


def fraction(sid: str, what: str) -> float:
    """A stable number in [0, 1) for one roof and one question — the deal's only dice."""
    digest = hashlib.sha256(f"yard:{what}:{sid}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2 ** 64


@lru_cache(maxsize=1)
def _lives_at() -> dict[str, list[str]]:
    from enclosure_owners import household_links  # noqa: E402
    return household_links()[0]


@lru_cache(maxsize=1)
def _trade_class() -> dict[str, str]:
    """trade -> household class, through the table the seats were dealt by."""
    import fabric_rule_1835 as fabric  # noqa: E402
    return {trade: fabric.CLASS_OF_CLAUSE[clause]
            for trade, clause in fabric._trade_clause().items()
            if clause in fabric.CLASS_OF_CLAUSE}


def _class_of_trade(trade: str | None) -> str | None:
    if not trade:
        return None
    klass = _trade_class().get(trade)
    return CLASS_ALIASES.get(klass, klass) if klass else None


def household(sid: str, sidecar: dict, structure_text: str) -> dict:
    """{class, by, household, trade}: who lives in `sid`, by the order in the docstring."""
    m = FABRIC_CLASS.search(structure_text or "")
    if m:
        klass = CLASS_ALIASES.get(m.group(1), m.group(1))
        return {"class": klass, "by": "fabric_rule", "household": None, "trade": None}
    import fabric_rule_1835 as fabric  # noqa: E402
    for hid in sorted(_lives_at().get(sid, [])):
        try:
            hh = fabric._household(hid)
        except (OSError, ValueError):
            continue
        klass = _class_of_trade(hh.get("trade"))
        if klass:
            return {"class": klass, "by": "household_trade", "household": hid,
                    "trade": hh["trade"]}
    occupation = (sidecar.get("reconstruction") or {}).get("occupation")
    klass = _class_of_trade(occupation)
    if klass:
        return {"class": klass, "by": "reconstruction_occupation", "household": None,
                "trade": occupation}
    function = str(((sidecar.get("attributes") or {}).get("function") or {}).get("value")
                   or "")
    if any(w in function for w in ("tavern", "hotel", "inn", "boarding")):
        return {"class": "keeper", "by": "function", "household": None, "trade": None}
    return {"class": "tradesman", "by": "default", "household": None, "trade": None}


def house(sidecar: dict, area_m2: float) -> str:
    """shanty · log · small · larger — the wealth inside a class, read off the roof."""
    family = (sidecar.get("reconstruction") or {}).get("family") or ""
    archetype = sidecar.get("archetype")
    if family == "D2" or archetype == "outbuilding":
        return "shanty"
    if family == "D1" or archetype == "log_dwelling":
        return "log"
    if family in LARGER_FAMILIES or (not family and area_m2 >= LARGER_HOUSE_M2):
        return "larger"
    return "small"


def row_for(klass: str, house_kind: str) -> tuple[str, dict]:
    name = ROW_OF[(klass, house_kind)]
    return name, WOODPILE[name]


def policy_table() -> dict:
    """The rule as the placement policy prints it (T-1195's file, T-1212's clause)."""
    return {
        "ticket": "T-1959",
        "dealt_by": "tools/yard_rule_1835.py — tools/generate_woodpiles.py deals "
                    "data/yard/town_woodpiles.json through it",
        "household_order": [
            "1. the roof's fabric_basis.class (tools/fabric_rule_1835.py), which already "
            "prefers a written keeper's trade to the family label",
            "2. a household whose lives_at names the roof, by its trade "
            "(seat_known_1835.TRADE_CLAUSE)",
            "3. the occupation the reconstruction names, by the same table",
            "4. a tavern, hotel or boarding house by its function is a keeper's",
            "5. otherwise a tradesman's, said so on the record"],
        "house": {
            "shanty": "family D2, or a dwelling drawn on the outbuilding archetype",
            "log": "family D1, or a log_dwelling",
            "larger": f"families {', '.join(sorted(LARGER_FAMILIES))}, or a documented "
                      f"frame house of {LARGER_HOUSE_M2:g} m2 or more",
            "small": "every other dwelling"},
        "woodpile": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                         for kk, vv in v.items()} for k, v in WOODPILE.items()},
        "row_of_class_and_house": {f"{k[0]} x {k[1]}": v for k, v in ROW_OF.items()},
        "still_to_write": "wells; privies and stables (T-1960) and trade goods by trade (T-1961) are their own records in data/yard/",
        "liberty": "L356",
    }


def self_test() -> int:
    ok = True

    def expect(label: str, passed: bool, detail: str = "") -> None:
        nonlocal ok
        print(f"  {'ok  ' if passed else 'FAIL'}  {label}{' — ' + detail if detail else ''}")
        ok &= passed

    houses = ("shanty", "log", "small", "larger")
    missing = [(c, h) for c in CLASSES for h in houses if (c, h) not in ROW_OF]
    expect("every class x house has a row", not missing, str(missing))
    stray = [v for v in ROW_OF.values() if v not in WOODPILE]
    expect("every row names a woodpile the rule defines", not stray, str(stray))
    ids = [v["rule"] for v in WOODPILE.values()]
    expect("rule ids are unique", len(ids) == len(set(ids)), str(ids))
    for name, row in WOODPILE.items():
        if row["kind"] == "cordwood":
            lo, hi = row["height_m"]
            expect(f"{name}: a July pile is dealt at or under a full cord's 1.22 m",
                   0 < lo <= hi <= 1.22, f"{lo}-{hi}")
    # The dice are the roof's own: the same id always gets the same pile, two ids do not.
    expect("the deal is deterministic", fraction("a", "x") == fraction("a", "x"))
    expect("the deal differs house to house", fraction("a", "x") != fraction("b", "x"))
    # Breaking the table must be caught: drop a cell and the coverage test has to see it.
    broken = dict(ROW_OF)
    broken.pop(("merchant", "log"))
    caught = [(c, h) for c in CLASSES for h in houses if (c, h) not in broken]
    expect("a dropped cell is caught", caught == [("merchant", "log")], str(caught))
    # The household order: a roof the fabric rule dealt is read by its class, never re-dealt.
    text = '{"fabric_basis": {"rule": "F-M", "class": "merchant"}}'
    expect("a fabric class is read first",
           household("x", {}, text)["class"] == "merchant")
    expect("a works class keeps a tradesman's house",
           household("x", {}, text.replace("merchant", "works"))["class"] == "tradesman")
    expect("a tavern by its function is a keeper's",
           household("x", {"attributes": {"function": {"value": "tavern_inn"}}}, "")
           ["class"] == "keeper")
    expect("nothing known is a tradesman's, and says so",
           household("zz_none", {}, "") == {"class": "tradesman", "by": "default",
                                           "household": None, "trade": None})
    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    print(json.dumps(policy_table(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
