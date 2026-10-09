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
import ast
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


# The archetype bands whose roofs held a TRADE — a shop or store (C), a works (W), a
# freight store (F). T-1657. D and H are dwellings, A is outbuildings, I is churches,
# schools and the civic roofs, T is the inns (already named trade by trade in
# PUBLIC_TRADES, which is where the Sauganash and the Green Tree are ruled), and M is
# the fort. None of those is a counter, so none is asked to be one.
TRADE_BANDS = ("C", "W", "F")
CROSSWALK = DATA / "reconstruction" / "1835_family_archetype_crosswalk.json"


def commercial_family_trades() -> dict[str, str]:
    """`{band: function.value}` for every commercial or works archetype family.

    Resolved the way `generate_block_infill.place` resolves it for the record it
    writes — the FUNCTIONS row if the band has one, otherwise `canonical()` over the
    crosswalk's own label — and read out of `generate_block_infill.py`'s SYNTAX TREE
    rather than by importing it. Importing costs the whole generator's module body
    (the archetypes, the plat module, the no-build traces) to read one dict, and this
    tool is a gate that runs on every commit; `check_corridor_line.py` reads its
    subjects the same way and for the same reason.
    """
    tree = ast.parse((ROOT / "tools" / "generate_block_infill.py").read_text())
    functions: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "FUNCTIONS" for t in node.targets):
            functions = ast.literal_eval(node.value)
            break
    if not functions:
        raise SystemExit("tools/generate_block_infill.py carries no FUNCTIONS table, "
                         "so the archetype families' trade terms cannot be resolved")
    crosswalk = json.loads(CROSSWALK.read_text())
    families = crosswalk.get("families")
    if not families:
        raise SystemExit(f"{CROSSWALK.name} carries no families")
    out: dict[str, str] = {}
    for family in families:
        band = family["id"]
        if not band.startswith(TRADE_BANDS):
            continue
        out[band] = functions.get(band) or canonical(family["label"].lower())
    return out


def _signboards():
    """`generate_business_signboards` as a module, loaded from its path.

    It is not an importable package and this tool is not in its directory, so it is
    loaded by spec — the same way `check()` has read it since T-1311.
    """
    import importlib.util
    sys.path.insert(0, str(ROOT / "tools"))
    spec = importlib.util.spec_from_file_location(
        "_signboards", ROOT / "tools" / "generate_business_signboards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _trade_sets(mod=None) -> set[str]:
    """Every `function.value` either signage table rules on."""
    if mod is None:
        mod = _signboards()
    return set(getattr(mod, "PUBLIC_TRADES", {})) | set(getattr(mod, "WORKS_TRADES", {}))


def unruled_commercial_families(families: dict[str, str], vocab: set[str],
                               known: set[str]) -> list[tuple[str, str]]:
    """The commercial or works families the signage rule has not ruled on.

    A pure function of three sets so the gate can be broken in a self-test without
    editing the tables it gates — the shape T-1578 asked of every new gate step.
    A family whose term the vocabulary cannot spell is NOT here: no record can carry
    it, so there is no silence to catch yet, and the day the term is added is the day
    this list grows.
    """
    return [(band, term) for band, term in sorted(families.items())
            if term in vocab and term not in known]


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
        # AND THE OTHER DIRECTION, for the families the roof schedule deals in bulk
        # (T-1657). The loop above asks whether a named trade can be spelled; this one
        # asks whether a spellable COMMERCIAL OR WORKS family has been ruled on at all,
        # and it is the direction that kept the bug: `PUBLIC_TRADES` carried C2's
        # `store_residence` and W1's `blacksmith_shop` but none of C1, C3, C4, F1 or
        # F2, so the signboard rule's clause 2 and the hitching rule that imports the
        # same set never LOOKED at those roofs. A documented store standing in one
        # would have got no board, no post, and — the part this project cannot
        # tolerate — no refusal saying why. Nothing refused the omission.
        #
        # Asked of the archetype crosswalk rather than a list here, because that file
        # is where a family is authored, so a family added there is ruled on here on
        # the same commit. C, W and F are the bands with a customer: a D or H dwelling,
        # an A outbuilding, an I civic building and M's fort roofs are not trades and
        # are not asked about. The term is resolved exactly as `generate_block_infill`
        # resolves it — its FUNCTIONS row if it has one, otherwise the folding rule
        # over the crosswalk's label — and the question is only put where the SCHEMA
        # can spell the answer: a family whose term is not in the vocabulary cannot
        # stand in this town at all, and `--build`'s own refusal is what fires when
        # somebody tries. Add the term to the vocabulary tomorrow and this gate asks
        # about it the same day.
        for band, term in unruled_commercial_families(
                commercial_family_trades(), vocab, _trade_sets(mod)):
            problems.append(
                f"the {band} archetype family writes function.value {term!r} and no "
                f"trade set knows it - put it in generate_business_signboards."
                f"PUBLIC_TRADES if its customer came in off the street, or in "
                f"WORKS_TRADES if its trade was named on its front for a carter. "
                f"A commercial family in neither set gets no board, no hitching "
                f"post, and no refusal saying why")
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

    # T-1657's gate, proved by breaking it. The families are resolved the way the
    # generator resolves them, so the first assertion is that the resolution AGREES
    # with what the records actually carry: `store_residence` and
    # `wide_two_story_store_or_mixed_block` are both on committed roofs today, and one
    # of them comes from the FUNCTIONS row while the other comes from the crosswalk's
    # label, so the pair covers both branches.
    families = commercial_family_trades()
    assert families.get("C2") == "store_residence", families.get("C2")
    assert families.get("C4") == "wide_two_story_store_or_mixed_block", families.get("C4")
    assert families.get("W1") == "blacksmith_shop", families.get("W1")
    assert set(families) >= {"C1", "C2", "C3", "C4", "W1", "F1", "F2"}, sorted(families)
    assert not [b for b in families if b[0] not in TRADE_BANDS], \
        f"a band outside {TRADE_BANDS} is being asked to be a trade: {sorted(families)}"
    assert "D3" not in families and "A3" not in families and "H2" not in families, \
        "a dwelling or an outbuilding is being asked for a trade"
    # AND THE GATE ITSELF: a spellable commercial family in neither trade set is
    # refused, and one the vocabulary cannot spell is not asked about. Both halves,
    # because it is the second that keeps the gate honest about what it can see.
    known = _trade_sets()
    unruled = unruled_commercial_families(families, vocab, known)
    assert not unruled, (
        f"the gate's own subject is red: {unruled} name terms the schema carries and "
        f"no trade set knows")
    broken = unruled_commercial_families(
        dict(families, C9="tea_room"), vocab | {"tea_room"}, known)
    assert broken == [("C9", "tea_room")], (
        f"the gate does not catch a commercial family in neither trade set: {broken}")
    assert not unruled_commercial_families(
        dict(families, C9="tea_room"), vocab, known), \
        "the gate is asking about a term the schema's vocabulary cannot spell"
    assert not unruled_commercial_families(
        dict(families, C9="tea_room"), vocab | {"tea_room"}, known | {"tea_room"}), \
        "the gate refuses a family the signage rule HAS ruled on"
    # F4's `lumber_shed` is the live proof of the second half: an authored family that
    # is not asked about, because the vocabulary cannot spell it and so no roof in town
    # carries one. F3's `large_river_warehouse` stood here too until T-2022 built the
    # town's first F3 and the schema learned the term; WORKS_TRADES rules on it now, which
    # is the first half of this gate doing its job rather than the second.
    assert "large_river_warehouse" in known, \
        "F3's term is in the vocabulary and no trade set rules on it"
    for term in ("lumber_shed", "sawmill_boat_repair_or_riverside_shop"):
        assert term not in vocab, (
            f"{term!r} is in the vocabulary now, so a trade set has to rule on it - "
            f"which is what this gate will say on the next commit")
    print(f"SELF-TEST OK - {len(cases)} foldings, {len(RULINGS)} rulings, "
          f"{len(vocab)} terms, {len(families)} commercial families ruled")
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
