#!/usr/bin/env python3
"""The community of every person in the 1835 layer, read off what the layer already says.

    python3 tools/derive_person_community.py              write data/residents/community.json
    python3 tools/derive_person_community.py --check      it re-derives; nothing has drifted
    python3 tools/derive_person_community.py --report     rule by rule, what fired and what did not
    python3 tools/derive_person_community.py --self-test  the rules below, held over what it derives

WHY THIS EXISTS. T-1177 asked for the under-documented cohorts of 1835 — the Native and
Metis town, the free Black residents and their businesses, the Irish and German Catholic
town the register implies — to be identified, tiered and reviewable. Its first acceptance
clause is the one everything else stands on: a `community` attribute on every person and
household, drawn from a closed vocabulary, each value tiered, and filterable in the
People view. Without it there is nothing to filter and no share to measure against, so
T-1375 is that clause and nothing else.

WHAT IT DOES NOT DO, said plainly because the ticket it came from is about people the
record has wronged. This pass READS NO SOURCE. It mints nobody, upgrades no confidence,
invents no citation and writes no name. Every value it assigns is read off a field that is
already committed, and is graded no higher than that field. Where the layer holds nothing,
the answer is `unknown` and stays `unknown` — a majority of this town, and the honest
number the cohort tickets exist to shrink. T-1376 reads the Native and Metis sources,
T-1377 the free Black ones, T-1378 the businesses and the Irish and German shares.

THE THREE RULES, in the order they fire, each named on the record it writes.

  1. `reconstruction_community` — a reconstructed person drawn from one of the name pools
     of data/reconstruction/1835_invented_name_pools.json carries that pool's community on
     the card already (`persons[].reconstruction.community`). It is taken as it stands, at
     tier `reconstructed`, because the person is reconstructed. The pool named
     `french_colonial` resolves to the vocabulary's `french_canadian` through the rules
     file's alias table; no record is rewritten for a rename.

  2. `stated_community` — the household's `origin` sentence states a community or a
     descent rather than only a place: "his father an Irish officer in the British army,
     his mother Potawatomi"; "of a French colonial family". The tier is the origin block's
     OWN confidence, uncapped, because the sentence is the evidence. A stated descent
     speaks only for the head and the relations who share those parents — a wife does not
     take her husband's descent.

  3. `origin_region` — the household's `origin` states a place. A place is not a community,
     so this is an inference about the person and the tier is the origin block's confidence
     CAPPED AT `inferred`: an attested Vermont origin yields an inferred `yankee`. It
     speaks for the household's family and for nobody else under its roof — not the
     boarder, the lodger, the servant, the clerk, the apprentice, the journeyman or the
     unnamed `household_member`.

  And where none fires, `unknown`, with the basis saying which silence it was: the
  household records no origin, the origin is one this project has decided it cannot read
  into a community, or this person is not one the household's origin speaks for.

THE COVERAGE RULE IS THE SAFETY PROPERTY. Every distinct `origin.value` in
data/residents/ must be accounted for exactly once in data/residents/community_rules.json
— as a stated community, as a region, or as explicitly unreadable. `--check` fails when
one is not, so a new origin string cannot enter the layer without somebody deciding what
it means. A silent fall-through to `unknown` is exactly the failure this pass would
otherwise make invisible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
RULES = RESIDENTS / "community_rules.json"
OUT = RESIDENTS / "community.json"

TIER_ORDER = ["attested", "inferred", "reconstructed"]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cap(tier: str | None, ceiling: str) -> str:
    """The weaker of a field's own confidence and a rule's ceiling."""
    if tier not in TIER_ORDER:
        return ceiling
    return TIER_ORDER[max(TIER_ORDER.index(tier), TIER_ORDER.index(ceiling))]


def household_files(rules) -> list[tuple[str, Path]]:
    """Every household the scene compiles, in the three places they live.

    The mints' own directory (data/residents/index.json), the re-admissions T-1172 minted
    outside it, the trade households T-1347 drew, and the Native and Metis men T-1376
    carded. compile_scene.py walks exactly these and this pass must walk the same town or
    the People view would carry rows this file has never seen.

    THE VISITORS ARE THE ONE SET NOT WALKED HERE, and that is a gap and not a decision:
    T-1353 minted 307 transients into data/reconstruction/1835_transient_persons.json after
    this pass was written, compile_scene.py carries them onto People rows, and their
    `community` therefore reads off nothing. Filed on T-1179, which converges the layer.
    """
    out: list[tuple[str, Path]] = []
    index = load(RESIDENTS / "index.json")
    for entry in index.get("households", []):
        out.append((entry["file"], RESIDENTS / entry["file"]))
    for name in ("1835_readmissions.json", "1835_trade_households.json",
                 "1835_native_and_metis.json", "1835_free_black.json"):
        path = DATA / "reconstruction" / name
        if not path.exists():
            continue
        for minted in load(path).get("minted", []):
            out.append((minted["file"], RESIDENTS / minted["file"]))
    return [(rel, p) for rel, p in out if p.exists()]


def derive(rules) -> dict:
    aliases = {k: v for k, v in rules["pool_aliases"].items() if not k.startswith("_")}
    vocab = [v["value"] for v in rules["vocabulary"]]
    descent = set(rules["who_a_household_origin_speaks_for"]["descent_relationships"])
    family = set(rules["who_a_household_origin_speaks_for"]["origin_relationships"])
    stated = {r["origin"]: r for r in rules["stated_community"]}
    region = {r["origin"]: r for r in rules["origin_region"]}
    unreadable = {r["origin"]: r for r in rules["unreadable_origin"]}

    persons: dict[str, dict] = {}
    households: dict[str, dict] = {}
    unaccounted: set[str] = set()

    for rel, path in household_files(rules):
        hh = load(path)
        origin = hh.get("origin") or {}
        value = origin.get("value") if isinstance(origin, dict) else origin
        conf = origin.get("confidence") if isinstance(origin, dict) else None
        if value and value not in stated and value not in region and value not in unreadable:
            unaccounted.add(value)

        for person in hh.get("persons", []) or []:
            pid = person.get("id")
            relationship = person.get("relationship")
            reconstruction = person.get("reconstruction") or {}
            pool = reconstruction.get("community")
            row: dict
            if pool:
                row = {"value": aliases.get(pool, pool), "tier": "reconstructed",
                       "rule": "reconstruction_community"}
            elif value in stated and relationship in descent:
                row = {"value": stated[value]["community"], "tier": cap(conf, "attested"),
                       "rule": "stated_community"}
            elif value in region and relationship in family:
                row = {"value": region[value]["community"], "tier": cap(conf, "inferred"),
                       "rule": "origin_region"}
            else:
                row = {
                    "value": "unknown", "tier": None,
                    "rule": ("no_origin_recorded" if not value
                             else "origin_unreadable" if value in unreadable
                             else "origin_does_not_speak_for_this_person"),
                }
            if row["value"] not in vocab:
                raise SystemExit(f"{pid}: `{row['value']}` is not in the vocabulary")
            if pid in persons:
                raise SystemExit(f"duplicate person id {pid} — check_unique_ids should have caught it")
            persons[pid] = row
            if person.get("relationship") == "head" or hh.get("head") == pid:
                households[hh["id"]] = dict(row, head=pid, file=rel)
        households.setdefault(hh["id"], {
            "value": "unknown", "tier": None, "rule": "no_head_person",
            "head": hh.get("head"), "file": rel,
        })

    if unaccounted:
        raise SystemExit(
            "these origin strings are in the layer and not in community_rules.json:\n  "
            + "\n  ".join(sorted(unaccounted))
            + "\nDecide what each means — a stated community, a region, or unreadable — "
              "before this pass can run. A silent fall-through to `unknown` is the one "
              "failure this file exists to make impossible.")

    def tally(rows, key):
        counts: dict = {}
        for r in rows:
            counts[r[key]] = counts.get(r[key], 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0]))))

    rows = list(persons.values())
    unknown = sum(1 for r in rows if r["value"] == "unknown")
    return {
        "id": "1835_community",
        "ticket": "T-1375",
        "parent_ticket": "T-1177",
        "derived_by": "tools/derive_person_community.py",
        "rules": "data/residents/community_rules.json",
        "rule_notes": {
            "reconstruction_community":
                "The name pool this reconstructed person was drawn from "
                "(data/reconstruction/1835_invented_name_pools.json). Evidence about the "
                "town's composition, not about a person.",
            "stated_community":
                "The household's origin sentence states a community or a descent. The tier "
                "is that block's own confidence: the sentence is the evidence. Which "
                "sentence, and what it says, is in the rules file beside the origin string.",
            "origin_region":
                "Read from where the household came, which is not the same claim as what "
                "community it belonged to — hence a tier no better than inferred.",
            "no_origin_recorded": "This household records no origin.",
            "origin_unreadable":
                "The household's origin is one the rules file has decided it cannot read "
                "into a community. The reason is written beside that origin string.",
            "origin_does_not_speak_for_this_person":
                "A household's origin is evidence about its family and not about everyone "
                "under its roof — a boarder, lodger, servant, clerk, apprentice, journeyman "
                "or unnamed household member is not one it speaks for.",
            "no_head_person": "No person of this household carries its head's id.",
        },
        "not_a_reading": "Derived, never hand-edited. Every value is read off a committed "
                         "field — a household's origin block or a reconstructed person's "
                         "own pool community — and graded no higher than the field it came "
                         "from. No source was read to write this file and nobody was minted.",
        "counts": {
            "persons": len(rows),
            "households": len(households),
            "known": len(rows) - unknown,
            "unknown": unknown,
            "by_community": tally(rows, "value"),
            "by_tier": tally(rows, "tier"),
            "by_rule": tally(rows, "rule"),
            "households_by_community": tally(list(households.values()), "value"),
        },
        "persons": dict(sorted(persons.items())),
        "households": dict(sorted(households.items())),
    }


def rendered(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def report(doc: dict) -> None:
    c = doc["counts"]
    print(f"{c['persons']} people in {c['households']} households")
    print(f"  known {c['known']}  unknown {c['unknown']} "
          f"({c['unknown'] / c['persons']:.1%})")
    for label, key in (("community", "by_community"), ("tier", "by_tier"), ("rule", "by_rule")):
        print(f"  by {label}:")
        for k, v in c[key].items():
            print(f"    {str(k):>18}  {v:>5}")


def self_test(doc: dict, rules: dict) -> None:
    """The rules above, held over what this pass actually derived."""
    persons = doc["persons"]
    vocab = {v["value"] for v in rules["vocabulary"]}
    assert persons, "no people"

    # Every value is in the closed vocabulary, and every known value carries a tier.
    for pid, r in persons.items():
        assert r["value"] in vocab, f"{pid}: {r['value']} outside the vocabulary"
        if r["value"] == "unknown":
            assert r["tier"] is None and r["rule"].startswith(("no_", "origin_unread",
                "origin_does_not")), f"{pid}: unknown with a tier"
        else:
            assert r["tier"] in TIER_ORDER, f"{pid}: {r['value']} with no tier"

    # Rule 3 may never beat `inferred`: a place is not a community.
    for pid, r in persons.items():
        if r["rule"] == "origin_region":
            assert r["tier"] in ("inferred", "reconstructed"), \
                f"{pid}: an origin region reached {r['tier']}"

    # Rule 1 is always reconstructed, because the person is.
    for pid, r in persons.items():
        if r["rule"] == "reconstruction_community":
            assert r["tier"] == "reconstructed", f"{pid}: a pool community at {r['tier']}"

    # The two stated descents are the only `metis` in the layer today, and they are the
    # heads themselves. If a later ticket adds more, this number is what it changes.
    metis = [p for p, r in persons.items() if r["value"] == "metis"]
    assert all(persons[p]["rule"] == "stated_community" for p in metis), \
        "a metis value that no source sentence states"

    # The pool alias resolved: no record reaches the view under the pool's own name.
    assert not [p for p, r in persons.items() if r["value"] == "french_colonial"], \
        "the french_colonial pool name reached a person row"

    # The free Black town is written by ONE stage and reaches this pass the way every
    # other reconstruction does — off `reconstruction.community`, never off an origin
    # string and never off a surname (T-1377). Same shape as the `metis` rule above: the
    # value is allowed, the ROUTE it arrived by is what is asserted.
    free_black = [p for p, r in persons.items() if r["value"] == "free_black"]
    assert all(persons[p]["rule"] == "reconstruction_community" for p in free_black), \
        "a free_black value this pass read off an origin string rather than off the stage"

    # No cohort this pass is forbidden to write has been written.
    for forbidden in ("german", "potawatomi", "ottawa", "ojibwe"):
        assert not [p for p, r in persons.items() if r["value"] == forbidden], \
            f"{forbidden} was assigned by a pass that reads no sources"

    print(f"self-test ok — {len(persons)} people, {len(metis)} of stated descent, "
          f"{len(free_black)} free Black, every one of them off the stage that wrote them")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    args = parser.parse_args()

    rules = load(RULES)
    doc = derive(rules)

    if args.self_test:
        self_test(doc, rules)
        return 0
    if args.report:
        report(doc)
        return 0
    if args.check:
        if not OUT.exists():
            print(f"{OUT.relative_to(ROOT)} is missing — run this tool without --check")
            return 1
        if OUT.read_text(encoding="utf-8") != rendered(doc):
            print(f"{OUT.relative_to(ROOT)} does not re-derive from data/residents/ and "
                  f"{RULES.relative_to(ROOT)}. Re-run tools/derive_person_community.py; "
                  f"this file is derived and is never hand-edited.")
            return 1
        print(f"{OUT.relative_to(ROOT)} re-derives ({doc['counts']['persons']} people)")
        return 0

    OUT.write_text(rendered(doc), encoding="utf-8")
    report(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
