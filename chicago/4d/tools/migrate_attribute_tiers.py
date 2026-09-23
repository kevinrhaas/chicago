#!/usr/bin/env python3
"""Per-attribute tiers on the resident layer — attested, inferred, reconstructed, unknown (T-1158).

    python3 tools/migrate_attribute_tiers.py             the coverage table, on stdout
    python3 tools/migrate_attribute_tiers.py --build     lift every card and write the coverage
    python3 tools/migrate_attribute_tiers.py --check     re-derive both and refuse a hand-edit
    python3 tools/migrate_attribute_tiers.py --self-test the assertions of the contract, broken

WHAT THIS IS FOR.

The owner, 2026-09-17: *"note for each attribute of each person what is attested,
inferred or reconstructed and reasons why."* The layer already grades a PERSON
(`grade`, the ladder rung) and it already puts a `confidence` on an attribute. What
it could not say is which of the three tiers a given attribute STANDS ON once the
reconstruction bands start filling attributes in — because `confidence:
"reconstructed"` is already spoken for, and it means the opposite of what the tier
will mean.

THE COLLISION, AND HOW IT IS RESOLVED. 7,314 claim blocks in the household cards
carry `confidence: "reconstructed"` over a value that asserts NOTHING — 6,160 with
`value: null` and a note reading "Not attested.", and 1,154 occupations whose value
is the sentinel `none_recorded`. That is not an invented value; it is the absence of
one, written down. Once a band actually invents a value, `reconstructed` has to mean
the invention, so the two readings cannot share a word.

So a fourth tier is added — `unknown`, meaning *nothing is asserted yet* — and the
migration below reads every not-asserted `reconstructed` block as `unknown`. What is
left under `reconstructed` is 40 blocks across the whole layer: twelve conjectured
arrival years, origins and presences, and twenty-eight addresses back-projected from
a later directory. Those are real reconstructions and they are the ones that now owe
a `basis` and a `replaceable_by`.

THE SHAPE (additive — no existing field moves, and `confidence` is untouched):

    {"value": "1826", "confidence": "reconstructed", "tier": "reconstructed",
     "note": "...",
     "basis": {"kind": "rule", "id": "arrival_conjecture", "note": "..."},
     "seed": "<deterministic seed>",              # kind "model" only
     "replaceable_by": {"kind": "person", "match": "..."}}

`tier` is DERIVED from `confidence` and the value and may not disagree with that
derivation — `validate.py` refuses the disagreement, which is what stops a tier being
quietly promoted above the evidence its own confidence admits to.

WHY THE EXISTING LAYER'S TIERS ARE DERIVED RATHER THAN WRITTEN INTO THE CARDS, which
is the one design decision here worth arguing with. The obvious move is to write `tier`
into all 1,258 household records, and it was tried first. It cannot stand: those bytes
are owned by NINE derivations that each rebuild a card from its sources and compare the
result to the committed file —

    synthesize_resident_research.py --drift    mint_documented_residents.py --check
    mint_civic_residents.py --check            mint_placed_residents.py --check
    back_project_addresses.py --check          back_project_residences.py --check
    qualify_later_trades.py --check            survey_stated_kin.py --write
    the four directory crosswalks

— and none of them knows the field exists, so ten of `check.sh`'s steps go red the
moment a tier lands in a card, and stay red until every writer emits one. Teaching nine
writers is real work and it belongs with T-1144's convergence pass, which owns the
drift in that layer. A field nine writers silently drop is a field that lies.

So the tier of an EXISTING value is derived, here and in `attribute-tiers.js`, from the
provenance the card already carries, and the derivation is published as a table. What a
record MAY carry, and what `validate.py` refuses if it carries it wrongly, is the full
shape below — because the reconstruction bands (T-1167 onward) mint their own records
and need somewhere to write a tier, and a value invented without a basis and without a
seed has to be refusable at the moment it is written.

TWO RULES THAT ARE NOT OBVIOUS, AND ARE THE POINT.

  * A `reconstructed` value owes a BASIS of one of two kinds, and they carry
    different evidence. `kind: "model"` was DRAWN — from a population, household or
    occupation model — so it owes the `seed` that redraws it; a drawn value nobody can
    redraw is not reproducible and this project does not ship one. `kind: "rule"` was
    ARGUED — the earliest year the evidence forces, an address carried back from an
    1843 directory — so it owes the rule's id and the reasoning, and it has no seed,
    because nothing was drawn. Requiring a seed of an argued value would mean
    inventing one, which is the failure this whole file exists to prevent.
  * EVERY RECONSTRUCTED VALUE SAYS WHAT WOULD RETIRE IT. The owner: *"so if we get
    new research … we can replace the reconstructed person or business with an
    inferred or attested one later."* `replaceable_by.match` is not a guess about the
    future; it is the definition of the attribute read back as a search — what
    retires a reconstructed arrival is a source that dates the arrival. The table
    below is that reading, one row an attribute, and it is why the migration can
    write the field without inventing anything.

RUN `--build` AFTER ANY WRITER. The table counts the committed cards, so a pass that
changes one changes the table; `--check` is wired into `check.sh` and goes red when the
two part company, which is the intended way to find out.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
TIER_TABLE = DATA / "research" / "residents" / "attribute_tiers.json"

# The four tiers, best evidenced first. `unknown` is last on purpose: it is not a
# weaker claim than `reconstructed`, it is the absence of a claim.
TIERS = ("attested", "inferred", "reconstructed", "unknown")

# How a reconstructed value came to exist. See the docstring: drawn owes a seed,
# argued owes a rule.
BASIS_KINDS = ("model", "rule")

# What a replacement would be a record OF.
REPLACEABLE_KINDS = ("person", "household", "business")

# Values that assert nothing. `none_recorded` is the occupation layer's own sentinel
# and reads in its own words: the trade is not recorded. An absence written down is
# still an absence.
NOT_ASSERTED = (None, "", "none_recorded")

# What would retire a reconstructed value, one row an attribute. Every row is the
# attribute's own definition read back as a search; nothing here is a prediction.
REPLACEABLE_BY = {
    "arrival": ("person", "a dated source that says when this person came to Chicago"),
    "origin": ("person", "a source that says where this person came from"),
    "reason_for_coming": ("person", "a source that says why this person came"),
    "party_size_on_arrival": ("household", "a source that counts the party this household arrived in"),
    "lives_at": ("household", "a source that places this household at a named Chicago address"),
    "works_at": ("household", "a source that places this household's work at a named premises"),
    "present_on_scene_date": ("household",
                              "a source that puts this household at Chicago on 1 July 1835, "
                              "or takes it away"),
    "persons[].occupation": ("person",
                             "a source that records this person's trade inside the scene window"),
    "directories.people[].back_projection": (
        "person", "an 1835-window source that gives this person a Chicago work address"),
    "directories.people[].residence_back_projection": (
        "person", "an 1835-window source that gives this person a Chicago home address"),
}

# The rule each surviving reconstructed value was argued under, one row an attribute.
# These are the arguments the blocks' own notes already make; the id names the argument
# so a reader can find every value that rests on it.
BASIS_RULE = {
    "arrival": ("arrival_earliest_year_forced",
                "No source dates the coming. The value is the earliest year the committed "
                "evidence forces, carried at the precision the note states."),
    "origin": ("origin_uncited_literature",
               "The origin is repeated in the Chicago literature and could not be traced to "
               "a source this project holds, so it is carried as a conjecture that cites "
               "nothing."),
    "present_on_scene_date": ("inferred_household_hypothesis",
                              "Presence on the scene date IS this household's hypothesis: the "
                              "record exists because the town of 1 July 1835 demonstrably needed "
                              "a household of this trade."),
    # The two back-projections are separate rules and separate liberties, and the
    # blocks' own notes say why: a shopfront is capital sunk into one street's trade
    # and a lodging is a month's rent, so a home is carried back on a weaker argument
    # than a shop is. One id for both would hide that.
    "directories.people[].back_projection": (
        "address_back_projection",
        "The work address is a later directory's, carried back to the scene window under "
        "docs/ADDRESS-BACK-PROJECTION.md (liberty L218) rather than read from an 1835 "
        "source. What is claimed is the street face and nothing narrower."),
    "directories.people[].residence_back_projection": (
        "residence_back_projection",
        "The home address is a later directory's, carried back to the scene window under "
        "docs/RESIDENCE-BACK-PROJECTION.md (liberty L223) rather than read from an 1835 "
        "source. What is claimed is the street face and nothing narrower."),
}

# Two cards argue their reconstructed value under a DIFFERENT rule from the rest of
# their attribute, and their own notes say so. The default above would misdescribe
# them, and a basis that misdescribes is worse than none: it would file a figure in
# general circulation under "the earliest year the evidence forces" and make the
# dataset sound better evidenced than it is. Overriding by card is the honest cost of
# that, and the table is short enough to read.
BASIS_RULE_BY_CARD = {
    ("hh_adams_william_h", "arrival"): (
        "arrival_bound_from_the_record",
        "Not an arrival date. The evidence bears only that the person was at Chicago at "
        "some point in the year, so the value is the last day that evidence can reach, at "
        "`not_later_than` precision — a bound rather than a date."),
    ("hh_beaubien_mark", "arrival"): (
        "arrival_uncited_literature",
        "The year is the figure in general circulation in the Chicago literature and no "
        "passage this project holds gives it, so it is carried as a conjecture that cites "
        "nothing."),
}


def not_asserted(value) -> bool:
    """True when the block's value says nothing — null, empty, or the trade sentinel."""
    return value in NOT_ASSERTED


def tier_for(block: dict) -> str | None:
    """The tier a block's EXISTING provenance supports. Never above its confidence.

    This is the whole migration in four lines, and it is also the rule `validate.py`
    holds a written `tier` to, so a card cannot claim a tier its confidence does not
    already admit to.
    """
    if not isinstance(block, dict) or "confidence" not in block or "value" not in block:
        return None
    conf = block.get("confidence")
    if conf == "reconstructed":
        return "unknown" if not_asserted(block.get("value")) else "reconstructed"
    if conf in ("attested", "inferred"):
        return conf
    return None


# --------------------------------------------------------------------------
# the contract — imported by validate.py, broken on purpose by --self-test
# --------------------------------------------------------------------------

def check_tier_block(where: str, key: str, block: dict, error) -> None:
    """Refuse a tier that is not earned. `error(where, message)` is the reporter.

    Silent on a block that carries no `tier`: the old shape stands until `--build`
    lifts it, and a structure record that never adopts the shape is not in breach.
    """
    has_extras = any(k in block for k in ("basis", "seed", "replaceable_by"))
    tier = block.get("tier")
    if tier is None:
        if has_extras:
            error(where, f"{key}: carries basis/seed/replaceable_by with no `tier` — "
                         f"the reconstruction fields belong to a reconstructed tier")
        return

    if tier not in TIERS:
        error(where, f"{key}: unknown tier '{tier}', not one of {sorted(TIERS)}")
        return

    want = tier_for(block)
    if want is not None and tier != want:
        error(where, f"{key}: tier '{tier}' disagrees with the evidence the block carries "
                     f"(confidence '{block.get('confidence')}' over "
                     f"{'no asserted value' if not_asserted(block.get('value')) else 'a value'} "
                     f"reads '{want}') — a tier is derived, never promoted")

    if tier != "reconstructed":
        if has_extras:
            error(where, f"{key}: tier '{tier}' carries basis/seed/replaceable_by — only a "
                         f"reconstructed value owes them")
        return

    basis = block.get("basis")
    if not isinstance(basis, dict):
        error(where, f"{key}: reconstructed requires a `basis` naming the model row or the "
                     f"rule the value was drawn from")
        return
    stray = sorted(set(basis) - {"kind", "id", "note"})
    if stray:
        error(where, f"{key}: basis carries unknown key(s) {stray}")
    kind = basis.get("kind")
    if kind not in BASIS_KINDS:
        error(where, f"{key}: basis.kind '{kind}' is not one of {sorted(BASIS_KINDS)}")
    if not str(basis.get("id") or "").strip():
        error(where, f"{key}: basis.id must name the model row or the rule")
    if not str(basis.get("note") or "").strip():
        error(where, f"{key}: basis.note must state why this value follows from that basis")

    seed = block.get("seed")
    if kind == "model":
        if not str(seed or "").strip():
            error(where, f"{key}: a value DRAWN from a model requires the `seed` that redraws "
                         f"it — a draw nobody can reproduce is not a reconstruction")
    elif seed is not None:
        error(where, f"{key}: a value argued from a rule carries no `seed`; nothing was drawn, "
                     f"and a seed that redraws nothing is decoration")

    rep = block.get("replaceable_by")
    if not isinstance(rep, dict):
        error(where, f"{key}: reconstructed requires `replaceable_by` saying what evidence "
                     f"would retire this value")
        return
    stray = sorted(set(rep) - {"kind", "match"})
    if stray:
        error(where, f"{key}: replaceable_by carries unknown key(s) {stray}")
    if rep.get("kind") not in REPLACEABLE_KINDS:
        error(where, f"{key}: replaceable_by.kind '{rep.get('kind')}' is not one of "
                     f"{sorted(REPLACEABLE_KINDS)}")
    if not str(rep.get("match") or "").strip():
        error(where, f"{key}: replaceable_by.match must say which evidence retires the value")


# --------------------------------------------------------------------------
# walking the layer
# --------------------------------------------------------------------------

def walk_blocks(node, prefix: str = ""):
    """Every claim block in a record, with the attribute path that names it.

    The path collapses list indices to `[]` so a coverage table counts an ATTRIBUTE
    rather than one row a person.
    """
    if isinstance(node, dict):
        if "confidence" in node and "value" in node:
            yield prefix, node
            return
        for k, v in node.items():
            yield from walk_blocks(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        for v in node:
            yield from walk_blocks(v, f"{prefix}[]")


def cards() -> list[Path]:
    return sorted(HOUSEHOLDS.glob("*.json"))


def lift(card_id: str, path: str, block: dict) -> dict:
    """One block, lifted into the shape at the tier its own provenance supports.

    Rebuilt key by key so `tier` sits beside the `confidence` it is derived from and
    the reconstruction fields land at the end, where a diff reads them together.
    """
    tier = tier_for(block)
    if tier is None:
        return block
    out: dict = {}
    for k, v in block.items():
        if k in ("tier", "basis", "seed", "replaceable_by"):
            continue
        out[k] = v
        if k == "confidence":
            out["tier"] = tier
    if "tier" not in out:
        out["tier"] = tier
    if tier == "reconstructed":
        rule = BASIS_RULE_BY_CARD.get((card_id, path)) or BASIS_RULE.get(path)
        rep = REPLACEABLE_BY.get(path)
        if rule is None or rep is None:
            raise SystemExit(
                f"FAIL {path}: a reconstructed value on an attribute with no rule and no "
                f"replacement row. Add it to BASIS_RULE/REPLACEABLE_BY in "
                f"tools/migrate_attribute_tiers.py — this tool will not invent one.")
        out["basis"] = {"kind": "rule", "id": rule[0], "note": rule[1]}
        out["replaceable_by"] = {"kind": rep[0], "match": rep[1]}
    return out


def reconstructed_rows() -> list[dict]:
    """Every genuinely reconstructed value in the layer, with the basis it rests on.

    Forty rows out of ten and a half thousand claims, and they are the ones a reader and
    a reconstruction band both need: the value this project supplied rather than read,
    the rule or model it came from, and the evidence that would retire it.
    """
    rows: list[dict] = []
    for f in cards():
        doc = json.loads(f.read_text(encoding="utf-8"))
        for path, block in walk_blocks(doc):
            if tier_for(block) != "reconstructed":
                continue
            rows.append({"card": f.stem, "attribute": path, **lift(f.stem, path, block)})
    return sorted(rows, key=lambda r: (r["card"], r["attribute"]))


def derive() -> dict:
    by_tier: Counter = Counter()
    by_attribute: dict = {}
    blocks = 0
    on_the_card = 0
    rules: Counter = Counter()
    for f in cards():
        doc = json.loads(f.read_text(encoding="utf-8"))
        for path, block in walk_blocks(doc):
            tier = tier_for(block)
            if tier is None:
                continue
            blocks += 1
            by_tier[tier] += 1
            row = by_attribute.setdefault(path, {t: 0 for t in TIERS})
            row[tier] += 1
            if block.get("tier") is not None:
                on_the_card += 1
    for r in reconstructed_rows():
        rules[(r.get("basis") or {}).get("id") or "(none)"] += 1
    return {
        "cards": len(cards()),
        "blocks": blocks,
        "tiers_written_on_the_card": on_the_card,
        "by_tier": {t: by_tier.get(t, 0) for t in TIERS},
        "by_attribute": {k: by_attribute[k] for k in sorted(by_attribute)},
        "reconstructed_by_basis": dict(sorted(rules.items())),
    }


def payload() -> dict:
    return {
        "schema": "attribute_tiers/1",
        "generated_by": "tools/migrate_attribute_tiers.py",
        "_doc": ("T-1158. Which tier every attribute of every household and person stands "
                 "on - attested, inferred, reconstructed, or unknown, meaning nothing is "
                 "asserted yet - together with every genuinely reconstructed value and the "
                 "basis it rests on. DERIVED from the committed cards: rebuild with --build, "
                 "and --check refuses a hand-edit and a card that has moved under it. "
                 "renderers/web/js/attribute-tiers.js derives the same tier for the card a "
                 "visitor opens, and tools/check_attribute_tiers.mjs holds the two answers "
                 "together."),
        "vocabulary": {
            "tiers": list(TIERS),
            "basis_kinds": list(BASIS_KINDS),
            "replaceable_kinds": list(REPLACEABLE_KINDS),
            "not_asserted_values": [None, "", "none_recorded"],
        },
        "counts": derive(),
        "reconstructed": reconstructed_rows(),
    }


def render(p: dict) -> str:
    c = p["counts"]
    lines = [f"attribute tiers: {c['blocks']} block(s) on {c['cards']} card(s), "
             f"{len(p['reconstructed'])} reconstructed value(s)"]
    for t in TIERS:
        lines.append(f"  tier  {t:16} {c['by_tier'][t]}")
    lines.append("  per attribute (attested / inferred / reconstructed / unknown):")
    for attr, row in c["by_attribute"].items():
        lines.append(f"    {attr:48} {row['attested']:5} {row['inferred']:5} "
                     f"{row['reconstructed']:5} {row['unknown']:6}")
    for rule, n in c["reconstructed_by_basis"].items():
        lines.append(f"  basis {rule:32} {n}")
    return "\n".join(lines)


def build() -> int:
    p = payload()
    TIER_TABLE.parent.mkdir(parents=True, exist_ok=True)
    TIER_TABLE.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {TIER_TABLE.relative_to(ROOT)}")
    print(render(p))
    return 0


def check() -> int:
    if not TIER_TABLE.exists():
        print(f"FAIL {TIER_TABLE.relative_to(ROOT)} is missing", file=sys.stderr)
        return 1
    p = payload()
    committed = json.loads(TIER_TABLE.read_text(encoding="utf-8"))
    bad = [k for k in ("vocabulary", "counts", "reconstructed") if committed.get(k) != p[k]]
    if bad:
        print(f"FAIL {TIER_TABLE.relative_to(ROOT)} does not re-derive: {bad} differ. Rebuild "
              f"with --build; the file is derived and a hand-edit loses.", file=sys.stderr)
        return 1
    # Every row this table publishes is held to the contract it documents, so the table
    # cannot ship a reconstruction that a RECORD carrying the same shape would be refused
    # for. The two would otherwise drift apart the moment a rule above is tightened.
    errs: list = []
    for row in p["reconstructed"]:
        check_tier_block(row["card"], row["attribute"], row,
                         lambda w, m: errs.append(f"{w}: {m}"))
    if errs:
        print(f"FAIL the derived table publishes {len(errs)} row(s) the tier contract "
              f"refuses: {errs[:3]}", file=sys.stderr)
        return 1
    print("ok  " + render(p))
    return 0



def self_test() -> int:
    """Break each refusal on purpose; a gate that cannot fail is not a gate."""
    errs: list = []

    def err(where, msg):
        errs.append((where, msg))

    def run(block):
        errs.clear()
        check_tier_block("t", "attr", block, err)
        return list(errs)

    argued = {
        "value": "1826", "confidence": "reconstructed", "tier": "reconstructed",
        "note": "n",
        "basis": {"kind": "rule", "id": "arrival_earliest_year_forced", "note": "n"},
        "replaceable_by": {"kind": "person", "match": "a dated source"},
    }
    drawn = {
        "value": "cooper", "confidence": "reconstructed", "tier": "reconstructed", "note": "n",
        "basis": {"kind": "model", "id": "1835_population_model#trades.cooper", "note": "n"},
        "seed": "t1158:cooper:0017",
        "replaceable_by": {"kind": "person", "match": "a source that records the trade"},
    }
    unknown = {"value": None, "confidence": "reconstructed", "tier": "unknown", "note": "n"}
    attested = {"value": "1835-07-01", "confidence": "attested", "tier": "attested",
                "sources": ["s"]}

    cases = [
        ("an argued reconstruction passes", argued, False),
        ("a drawn reconstruction passes", drawn, False),
        ("a not-asserted value reads unknown", unknown, False),
        ("an attested attribute passes", attested, False),
        ("a tier that is not one", {**argued, "tier": "probable"}, True),
        ("a tier promoted above its confidence", {**unknown, "tier": "attested"}, True),
        ("a reconstructed tier over a not-asserted value", {**unknown, "tier": "reconstructed"}, True),
        ("an unknown tier over a real invention", {**argued, "tier": "unknown"}, True),
        ("a reconstruction with no basis", {k: v for k, v in argued.items() if k != "basis"}, True),
        ("a basis of no declared kind", {**argued, "basis": {**argued["basis"], "kind": "vibes"}}, True),
        ("a basis that names no rule", {**argued, "basis": {**argued["basis"], "id": " "}}, True),
        ("a basis that states no reasoning", {**argued, "basis": {**argued["basis"], "note": ""}}, True),
        ("a basis carrying an unknown key", {**argued, "basis": {**argued["basis"], "why": "x"}}, True),
        ("a drawn value with no seed", {k: v for k, v in drawn.items() if k != "seed"}, True),
        ("an argued value carrying a seed", {**argued, "seed": "x"}, True),
        ("a reconstruction with no replacement rule",
         {k: v for k, v in argued.items() if k != "replaceable_by"}, True),
        ("a replacement of no declared kind",
         {**argued, "replaceable_by": {"kind": "roof", "match": "m"}}, True),
        ("a replacement that names no evidence",
         {**argued, "replaceable_by": {"kind": "person", "match": "  "}}, True),
        ("a replacement carrying an unknown key",
         {**argued, "replaceable_by": {**argued["replaceable_by"], "when": "soon"}}, True),
        ("an attested attribute carrying a seed", {**attested, "seed": "x"}, True),
        ("the reconstruction fields with no tier at all",
         {"value": "1826", "confidence": "reconstructed", "note": "n",
          "basis": {"kind": "rule", "id": "r", "note": "n"}}, True),
        ("the old shape, untouched", {"value": None, "confidence": "reconstructed",
                                      "note": "Not attested."}, False),
    ]
    failed = 0
    for label, block, want_error in cases:
        got = run(block)
        ok = bool(got) == want_error
        print(("ok   " if ok else "FAIL ") + label + ("" if ok else f"  -> {got}"))
        failed += 0 if ok else 1

    derivations = [
        ("a null value under reconstructed", {"value": None, "confidence": "reconstructed"}, "unknown"),
        ("the trade sentinel", {"value": "none_recorded", "confidence": "reconstructed"}, "unknown"),
        ("an invented value", {"value": "1826", "confidence": "reconstructed"}, "reconstructed"),
        ("an inferred value", {"value": "1834", "confidence": "inferred"}, "inferred"),
        ("an attested value", {"value": "1834", "confidence": "attested"}, "attested"),
        ("something that is not a claim block", {"value": "1834"}, None),
    ]
    for label, block, want in derivations:
        got = tier_for(block)
        ok = got == want
        print(("ok   " if ok else "FAIL ") + f"derives {label}" + ("" if ok else f"  -> {got}"))
        failed += 0 if ok else 1

    # A writer that drops the tier must be caught, not tolerated.
    dropped = {k: v for k, v in argued.items() if k not in ("tier", "basis", "replaceable_by")}
    ok = lift("hh_x", "arrival", dropped).get("tier") == "reconstructed"
    print(("ok   " if ok else "FAIL ") + "a dropped tier is re-derived by the lift")
    failed += 0 if ok else 1

    print(f"{failed} failure(s)")
    return 1 if failed else 0


def main(argv) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--build" in argv:
        return build()
    if "--check" in argv:
        return check()
    print(render(payload()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
