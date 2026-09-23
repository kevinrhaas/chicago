#!/usr/bin/env python3
"""The structure `function` vocabulary, closed and migrated (T-1311).

`data/structures/*.json` carried `function.value` as a FREE STRING, and 384
records had spelled it 109 different ways. Three of those ways were the same
word twice:

    blacksmith_shop                     AND  blacksmith shop
    store_residence                     AND  store-residence
    cooper, wagon, or wheelwright shop  AND  cooper, wagon or wheelwright shop

That is not a spelling nuisance. `function.value` is what the signage rule
(`generate_business_signboards.py` PUBLIC_TRADES / WORKS_TRADES), the yard
goods, the building-material rule and the register's occupation crosswalk all
read, and every one of them matches the value EXACTLY. A blacksmith's shop
spelled with a space is a blacksmith's shop those rules cannot see. The free
string made that failure silent and unbounded: nothing refused the 110th
spelling.

So the field is enumerated. `data/structures.schema.json` now carries the
vocabulary as `function.value.enum`, which is the single source of truth — this
tool READS it rather than holding a second copy, so the schema is what refuses
the rest, at the same gate that validates every other structure attribute.

## The migration

One mechanical rule, applied to all 109:

    lower-case, drop apostrophes, every other run of non-alphanumerics becomes a
    single `_`, strip the ends.

It is mechanical on purpose: a hand-written 109-row table is a place for a
judgement to hide. And it is the rule that merges the three collisions above,
by construction rather than by a ruling — `blacksmith shop` and
`blacksmith_shop` are the same string under it.

Three values were not vocabulary at all but a SENTENCE, and the rule would have
turned each into a 70-character term:

    "dwelling; used as John Watkins' school in 1833, use on the scene date
     unattested"

Each is a building whose documented use ENDED before the scene date and whose
use ON it is unattested — the construction `watkins_school_house.json`,
`chappel_infant_school.json` and `philo_carpenter_log_shop.json` share and
explain at length in their own `function.note`. RULINGS below compresses each
to a term that says the same three things (the built form, the former use, that
the current use is unattested) and nothing more; the reasoning stays where it
already is, in the note, untouched. The term keeps the former use in it because
the record does: dropping it would upgrade "nobody knows what was happening
inside on 1 July 1835" to a plain dwelling, which is the invention all three
notes exist to refuse.

## What this tool does NOT do

It does not rename a trade, merge two trades that are different trades, or
decide that `freight_shed` and `freight_or_storage_shed` are one thing. Those
are readings, and a migration is not the place to take one.

    tools/normalise_structure_function.py --build       migrate the records
    tools/normalise_structure_function.py --check       every value is canonical
    tools/normalise_structure_function.py --self-test   the assertions
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
SCHEMA = DATA / "structures.schema.json"

# The three sentences, and the term each becomes. Keyed on the exact string the
# records carried before the migration, so this table stays readable as the
# record of what happened rather than becoming a second vocabulary.
RULINGS = {
    "dwelling; used as John Watkins' school in 1833, use on the scene date "
    "unattested": "dwelling_former_school_use_unattested",
    "log house; infant school 1833-34, use on the scene date unattested":
        "log_house_former_school_use_unattested",
    "log cabin; Chicago's first drug store 1832, let 1832-33, Eliza Chappel's "
    "school 1833-34; use on the scene date unattested":
        "log_cabin_former_store_and_school_use_unattested",
}


def canonical(value: str) -> str:
    """The enum term for a free string. Mechanical, except for RULINGS."""
    if value in RULINGS:
        return RULINGS[value]
    folded = value.strip().lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "_", folded).strip("_")


def vocabulary() -> list[str]:
    """The enum, read from the schema — the one place it is written down."""
    schema = json.loads(SCHEMA.read_text())
    enum = schema["$defs"]["structure_function"]["properties"]["value"].get("enum")
    if not enum:
        raise SystemExit("data/structures.schema.json carries no function vocabulary")
    return enum


def records():
    for path in sorted(STRUCTURES.glob("*.json")):
        yield path, json.loads(path.read_text())


# A vocabulary term that READS like a place people lodge for pay. Deliberately wide:
# it only decides which terms the population profile must have RULED on (T-1323), and a
# false positive costs one line in NOT_LODGING_FUNCTIONS saying why it is not one.
LODGING_SHAPED = re.compile(r"hotel|tavern|\binn\b|inn_|_inn|boarding|lodging|coffee")


FUNCTION_VALUE = re.compile(
    r'("function"\s*:\s*\{\s*"value"\s*:\s*)("(?:[^"\\\\]|\\\\.)*")')


def rewrite(path: pathlib.Path, raw: str, value: str) -> None:
    """Replace the function value IN THE BYTES, and touch nothing else.

    Not a re-dump. 384 records and they are not dumped alike: 36 indent by one
    space rather than two, and `fort_dearborn_garrison_garden.json` escapes one
    em-dash out of thirty, so NO dump reproduces it. A migration that reformats
    is a migration nobody can review - the one line that matters disappears into
    150 lines of re-indentation, and a reviewer cannot see that the note was not
    touched. So the edit is made where the value is written, and the record is
    re-parsed afterwards to prove the file is still the record it was.
    """
    hits = FUNCTION_VALUE.findall(raw)
    if len(hits) != 1:
        raise SystemExit(f"{path.name}: {len(hits)} places look like the function "
                         f"value, so the edit has no unambiguous target")
    out = FUNCTION_VALUE.sub(
        lambda m: m.group(1) + json.dumps(value, ensure_ascii=False), raw, count=1)
    after = json.loads(out)
    before = json.loads(raw)
    before["function"]["value"] = value
    if after != before:
        raise SystemExit(f"{path.name}: the edited bytes are not the record with its "
                         f"function value replaced")
    path.write_text(out)


def build() -> int:
    vocab = set(vocabulary())
    changed, refused = [], []
    for path, doc in records():
        fn = doc.get("function")
        if not isinstance(fn, dict) or "value" not in fn:
            continue
        was = fn["value"]
        now = canonical(was)
        if now not in vocab:
            refused.append(f"{path.name}: {was!r} -> {now!r}, which the schema's "
                           f"vocabulary does not carry")
            continue
        if now == was:
            continue
        fn["value"] = now
        rewrite(path, path.read_text(), now)
        changed.append(f"{path.name}: {was!r} -> {now!r}")
    for line in changed:
        print(f"  {line}")
    print(f"migrated {len(changed)} record(s)")
    if refused:
        print("\nREFUSED - a value with no term. Add the term to the schema's "
              "vocabulary, or state the reading that maps it onto one:",
              file=sys.stderr)
        for line in refused:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


def check() -> int:
    """Every committed value is a vocabulary term and is its own canonical form.

    Two questions, not one. The schema answers the first on its own, and
    `validate.py` asks it of every record. The second is this tool's: a term
    that is IN the vocabulary but is not what `canonical()` would produce means
    the migration rule and the vocabulary have drifted apart, and the next free
    string to arrive would be normalised onto something the schema refuses.
    """
    vocab = set(vocabulary())
    problems = []
    for path, doc in records():
        fn = doc.get("function")
        if not isinstance(fn, dict) or "value" not in fn:
            problems.append(f"{path.name}: no function.value")
            continue
        value = fn["value"]
        if value not in vocab:
            problems.append(f"{path.name}: function.value {value!r} is not in the "
                            f"schema's vocabulary")
        elif canonical(value) != value:
            problems.append(f"{path.name}: function.value {value!r} is not its own "
                            f"canonical form ({canonical(value)!r})")
    # The signage rule reads this field by exact match, and a trade it names that
    # the vocabulary cannot spell is a sign that can never be dealt. This is the
    # collision that started T-1311, asked as a standing question.
    sys.path.insert(0, str(ROOT / "tools"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_signboards", ROOT / "tools" / "generate_business_signboards.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                                    # noqa: BLE001
        problems.append(f"the signage rule could not be read to compare "
                        f"vocabularies: {exc}")
    else:
        for name in ("PUBLIC_TRADES", "WORKS_TRADES"):
            for trade in sorted(getattr(mod, name, {})):
                if trade not in vocab:
                    problems.append(f"generate_business_signboards.{name} names "
                                    f"{trade!r}, which no structure can spell - the "
                                    f"schema's vocabulary does not carry it")
    # The population profile's lodging test reads this field by exact match too, and it
    # named three terms no structure could spell for as long as the vocabulary has been
    # closed — so every tavern household counted as a dwelling (T-1323). Asked in BOTH
    # directions, because the second is the one that kept the bug: a lodging-shaped term
    # the profile has not ruled on is refused, so adding `inn` to the schema tomorrow
    # cannot silently leave the profile blind to it.
    spec = importlib.util.spec_from_file_location(
        "_profile", ROOT / "tools" / "profile_population_1835.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                                    # noqa: BLE001
        problems.append(f"the population profile's lodging test could not be read to "
                        f"compare vocabularies: {exc}")
    else:
        lodging = set(getattr(mod, "LODGING_FUNCTIONS", ()))
        not_lodging = set(getattr(mod, "NOT_LODGING_FUNCTIONS", ()))
        for term in sorted(lodging | not_lodging):
            if term not in vocab:
                problems.append(f"profile_population_1835 rules on {term!r}, which no "
                                f"structure can spell - the schema's vocabulary does "
                                f"not carry it")
        for term in sorted(lodging & not_lodging):
            problems.append(f"profile_population_1835 has {term!r} in BOTH "
                            f"LODGING_FUNCTIONS and NOT_LODGING_FUNCTIONS - a term is "
                            f"lodging for pay or it is not")
        for term in sorted(vocab):
            if LODGING_SHAPED.search(term) and term not in lodging | not_lodging:
                problems.append(f"the vocabulary term {term!r} reads like lodging and "
                                f"profile_population_1835 rules on it neither way - put "
                                f"it in LODGING_FUNCTIONS or, with its reason, in "
                                f"NOT_LODGING_FUNCTIONS")
    # The card's own copy of the vocabulary. `store-residence` sat in it as a dead
    # key for as long as the free string existed, which is what a second spelling
    # costs on the visible side: the card kept a branch nothing could reach.
    popup = (ROOT / "renderers" / "web" / "js" / "popup.js").read_text()
    block = popup.split("const FUNCTION_WORDS = {", 1)[-1].split("\n};", 1)[0]
    keys = re.findall(r"^\s*(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_][A-Za-z0-9_]*))\s*:",
                      block, re.M)
    for quoted, dquoted, bare in keys:
        key = quoted or dquoted or bare
        if key not in vocab:
            problems.append(f"renderers/web/js/popup.js FUNCTION_WORDS names {key!r}, "
                            f"which no structure can spell - a dead branch on the card")
    if problems:
        print(f"FAIL {len(problems)} problem(s):", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"OK {len(list(records()))} structures, {len(vocab)} terms, every "
          f"function.value canonical")
    return 0


def self_test() -> int:
    cases = [
        ("blacksmith shop", "blacksmith_shop"),
        ("blacksmith_shop", "blacksmith_shop"),
        ("store-residence", "store_residence"),
        ("store_residence", "store_residence"),
        ("cooper, wagon or wheelwright shop", "cooper_wagon_or_wheelwright_shop"),
        ("cooper, wagon, or wheelwright shop", "cooper_wagon_or_wheelwright_shop"),
        ("one-and-a-half-story frame cottage", "one_and_a_half_story_frame_cottage"),
        ("commanding officer's quarters", "commanding_officers_quarters"),
        ("sutler's store", "sutlers_store"),
        ("  Trading House  ", "trading_house"),
    ]
    for value, want in cases:
        got = canonical(value)
        assert got == want, f"canonical({value!r}) = {got!r}, wanted {want!r}"
    for was, term in RULINGS.items():
        assert canonical(was) == term, f"the ruling for {was!r} is not applied"
        assert "_" in term and term == canonical(term), \
            f"the ruling term {term!r} is not a canonical term"
    vocab = set(vocabulary())
    for term in vocab:
        assert canonical(term) == term, \
            f"the vocabulary carries {term!r}, which is not its own canonical form"
    assert canonical("Brand New Trade") == "brand_new_trade"
    assert "brand_new_trade" not in vocab, \
        "the vocabulary is supposed to be closed - an unseen term is in it"
    print(f"SELF-TEST OK - {len(cases)} foldings, {len(RULINGS)} rulings, "
          f"{len(vocab)} terms")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.build:
        return build()
    if args.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
