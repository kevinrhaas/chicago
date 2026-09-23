#!/usr/bin/env python3
"""What a rights check actually blocks.

ROADMAP K41. AGENTS.md hard rule 6 and `docs/PROVENANCE.md` say the same thing in
almost the same words:

    A source whose `rights_status` is `check_required` may be cited in text but
    must not have assets derived from it.

and PROVENANCE.md adds four words: **"The validator enforces this."**

What the validator enforces is a comparison between two fields of the SAME source
record — `rights_status` against `asset_use` — inside `run_license_check`:

    if s["rights_status"] in ("check_required", "restricted") \
            and s["asset_use"] == "geometry":  error

`asset_use` is the source's own declaration of how the project intends to use it.
So the gate fires when a record says, in one field, that its rights are unresolved
and, in another, that geometry is traced from it — that is, when an author has
already written the violation down. It never asks what the town was built from.

This asks. The question needs a definition of "derived", and this project already
has one that no reviewer has to supply: `generators/archetypes/*_params.py`
declares `CONSUMED`, the set of form attributes whose value the generator reads,
and `generators/terrain_inputs.py` declares the same map for the ground. An
attribute inside that set reaches a vertex by construction — it is the definition
`tools/validate.py` already uses to demand a `geometry:` declaration on everything
outside it. A footprint polygon is in by the same argument: `from_phase` reads the
polygon for the massing's width and depth.

    tools/measure_rights_derivation.py              print the census
    tools/measure_rights_derivation.py --gate       exit 1 on a divergence
    tools/measure_rights_derivation.py --self-test  break each assertion, in memory
    tools/measure_rights_derivation.py --update     rewrite the baseline

FOUR ASSERTIONS. The first is absolute and restates the old rule where the real
measurement now lives; the rest hold a banked population exact in both directions.

1.  **(absolute) No unresolved source declares a deriving use.** `asset_use` in
    `geometry` or `texture` on a `check_required` or `restricted` source. This is
    `run_license_check`'s rule, kept — it is a real thing to refuse — and it is
    kept here as well so that the label test and the derivation test are read
    together rather than one standing in for the other.

2.  **A geometry-bearing citation of an unresolved source must be banked.** A new
    one fails. The bank is `tools/rights_derivation_baseline.json`, keyed by
    record, phase and attribute, and it is a record of what was measured, not a
    permission: every entry in it is a value the mesh is built from whose only
    standing is a source nobody has checked the rights on.

3.  **(absolute) The bank may not outlive the data.** An entry that is no longer
    in the tree fails until it is un-banked with `--update` in the same commit.
    A repair here is a claim — the rights check was done, or the value found
    other support — and a bank that keeps its ghosts overstates a fault and
    hides the repair that fixed it.

4.  **A banked entry may improve and may not worsen.** Its set of unresolved
    sources may not grow, and an attribute corroborated by a source outside the
    blocked set may not become one that stands on blocked support alone. The
    sole-support set is the population that matters: an attribute with an
    unblocked source beside the unresolved one loses nothing if the unresolved
    one is struck out.

WHAT THIS DOES NOT DECIDE, AND WILL NOT. Whether reading "two storeys, frame" out
of a copyrighted web page and building a box from it *is* deriving an asset from
that page is a question about rights, not about data, and `docs/PLAN.md` reads it
the narrow way — *"blocks derived assets, e.g. Conley/Stelzer, but not textual
citation … Stanford renewal check before any derivative texture"* — while
AGENTS.md and PROVENANCE.md read it the wide way. The two readings give different
answers for every entry in the bank. This measures the population under the wide
reading, holds it where it is, and leaves the reading to the owner: see
`docs/ROADMAP.md` K41 for the three routes.

SCOPE, STATED RATHER THAN IMPLIED. The buildings and the ground are covered
because those are the two things this project declares a read-set for. `data/flora`
and `data/fauna` cite unresolved sources too — 202 and 30 citations on the zone
records as this was written — and no `CONSUMED` map exists for either, so "which
of a zone's figures reaches a vertex" has no answer here yet to gate on. That is
K41's residual and it is written up in the ROADMAP box rather than left silent.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASELINE = ROOT / "tools" / "rights_derivation_baseline.json"

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

# Unresolved: the rights question has been asked and not answered. `cleared` is a
# check_required source whose check came back, so it is resolved and its entries
# leave the bank — that is the way out, and assertion 3 is what makes taking it
# visible.
BLOCKED_STATUSES = ("check_required", "restricted")

# The uses that put a source's own expression into the artefact rather than its
# facts into a record. These are what rule 6 refuses outright.
DERIVING_USES = ("geometry", "texture")

# Counted for the census only — the two layers with no declared read-set. Kept as
# data so the residual is a number in the output rather than a sentence in a doc.
UNGATED_LAYERS = ("flora", "fauna")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_sources() -> dict[str, dict]:
    out = {}
    for path in sorted((DATA / "sources").glob("*.json")):
        rec = load(path)
        if isinstance(rec, dict) and rec.get("id"):
            out[rec["id"]] = rec
    return out


def blocked_ids(sources: dict[str, dict]) -> set[str]:
    return {sid for sid, s in sources.items()
            if s.get("rights_status") in BLOCKED_STATUSES}


def archetype_consumed() -> dict[str, frozenset]:
    """The form attributes each archetype's generator reads.

    Imported from `tools/validate.py` rather than re-walked here: the gate that
    demands a `geometry:` declaration outside this set and the gate that asks
    what an unresolved source is built into have to mean the same thing by
    "reaches a vertex", and two copies of the loop would not stay that way.
    """
    import validate  # noqa: PLC0415
    return validate.archetype_consumed()


def ground_consumed() -> dict[str, frozenset]:
    import terrain_inputs  # noqa: PLC0415
    return {k: frozenset(v) for k, v in getattr(terrain_inputs, "CONSUMED", {}).items()}


def structure_entries(blocked: set[str]) -> dict[str, dict]:
    """Every geometry-bearing attribute of a building that cites an unresolved source."""
    consumed = archetype_consumed()
    out: dict[str, dict] = {}
    for path in sorted((DATA / "structures").glob("*.json")):
        st = load(path)
        if not isinstance(st, dict) or not st.get("id"):
            continue
        known = consumed.get(st.get("archetype"))
        if known is None:
            # No params module for this archetype yet. "We have not written the
            # generator" and "the generator reads nothing" are different states.
            continue
        for ph in st.get("phases", []):
            attrs: dict[str, dict] = {}
            fp = ph.get("footprint")
            if isinstance(fp, dict):
                attrs["footprint"] = fp
            for attr, a in sorted((ph.get("form") or {}).items()):
                if attr in known and isinstance(a, dict):
                    attrs[f"form.{attr}"] = a
            for attr, a in attrs.items():
                cited = [s for s in (a.get("sources") or []) if isinstance(s, str)]
                hit = sorted({s for s in cited if s in blocked})
                if not hit:
                    continue
                out[f"{st['id']}/{ph.get('id')}/{attr}"] = {
                    "kind": "structure",
                    "blocked_sources": hit,
                    "sole_support": len(hit) == len(set(cited)),
                    "confidence": a.get("confidence"),
                }
    return out


def ground_entries(blocked: set[str]) -> dict[str, dict]:
    """The same question of the terrain spec, one granularity coarser.

    A ground claim carries its sources on the block rather than on the field, so
    a block is geometry-bearing when any of the figures it states is in
    `terrain_inputs.CONSUMED` for its group. That is coarser than the structure
    side and says so: the citation supports the block, and at least one figure of
    the block reaches the surface.
    """
    import compile_scene  # noqa: PLC0415
    consumed = ground_consumed()
    sources = read_sources()
    out: dict[str, dict] = {}
    epochs_dir = DATA / "terrain" / "epochs"
    if not epochs_dir.exists() or not consumed:
        return out
    for epoch_dir in sorted(p for p in epochs_dir.iterdir() if p.is_dir()):
        spec_path = epoch_dir / "terrain_spec.json"
        if not spec_path.exists():
            continue
        for claim in compile_scene.ground_claims(load(spec_path), sources):
            group = str(claim.get("id", "")).split(".")[0]
            known = consumed.get(group)
            if not known:
                continue
            if not any(f.get("key") in known for f in claim.get("fields") or []):
                continue
            cited = [s for s in (claim.get("sources") or []) if isinstance(s, str)]
            hit = sorted({s for s in cited if s in blocked})
            if not hit:
                continue
            out[f"terrain/{epoch_dir.name}/{claim['id']}"] = {
                "kind": "ground",
                "blocked_sources": hit,
                "sole_support": len(hit) == len(set(cited)),
                "confidence": claim.get("confidence"),
            }
    return out


def ungated_citations(blocked: set[str]) -> dict[str, int]:
    """The residual, counted rather than described."""
    counts = {}
    for layer in UNGATED_LAYERS:
        n = 0
        for path in sorted((DATA / layer).rglob("*.json")) if (DATA / layer).exists() else []:
            def walk(o) -> None:
                nonlocal n
                if isinstance(o, dict):
                    for s in o.get("sources") or []:
                        if isinstance(s, str) and s in blocked:
                            n += 1
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(load(path))
        counts[layer] = n
    return counts


def read_bank() -> dict[str, dict]:
    if not BASELINE.exists():
        return {}
    return load(BASELINE).get("entries", {})


def evaluate(found: dict[str, dict], bank: dict[str, dict],
             sources: dict[str, dict]) -> list[str]:
    """The four assertions, as a pure function of what was measured.

    Pure so `--self-test` can break each one in memory against the real tree
    rather than against a fixture that stops resembling it.
    """
    problems: list[str] = []

    # 1 — absolute: the label test, kept and restated here.
    for sid, s in sorted(sources.items()):
        if s.get("rights_status") in BLOCKED_STATUSES \
                and s.get("asset_use") in DERIVING_USES:
            problems.append(
                f"source {sid}: rights_status is '{s['rights_status']}' and asset_use is "
                f"'{s['asset_use']}' — the rights check has to come back before anything "
                f"is traced from this work")

    # 2 — a new geometry-bearing citation of an unresolved source.
    for key in sorted(set(found) - set(bank)):
        e = found[key]
        problems.append(
            f"{key} is built from {', '.join(e['blocked_sources'])}, whose rights are "
            f"unresolved, and it is not in {BASELINE.name}. Resolve the rights check, cite "
            f"a source that is clear of it, or bank the decision with --update in this "
            f"commit and say in the message which of those you chose")

    # 3 — absolute: the bank may not outlive the data.
    for key in sorted(set(bank) - set(found)):
        problems.append(
            f"{key} is banked and is no longer a geometry-bearing citation of an unresolved "
            f"source. That is a repair, and recording it is part of making it: re-run with "
            f"--update in the commit that did it")

    # 4 — a banked entry may improve and may not worsen.
    for key in sorted(set(found) & set(bank)):
        now, was = found[key], bank[key]
        gained = sorted(set(now["blocked_sources"]) - set(was.get("blocked_sources") or []))
        if gained:
            problems.append(
                f"{key} has gained an unresolved source ({', '.join(gained)}) since it was "
                f"banked — the fault may shrink and may not grow")
        if now["sole_support"] and not was.get("sole_support"):
            problems.append(
                f"{key} stood on a source outside the blocked set when it was banked and "
                f"now stands on unresolved support alone — the corroboration it had is the "
                f"thing that made it survivable")
    return problems


def measure() -> tuple[dict, list[str]]:
    sources = read_sources()
    blocked = blocked_ids(sources)
    found = structure_entries(blocked)
    found.update(ground_entries(blocked))
    bank = read_bank()
    census = {
        "sources": len(sources),
        "blocked": sorted(blocked),
        "deriving_declared": sorted(sid for sid, s in sources.items()
                                    if s.get("asset_use") in DERIVING_USES),
        "found": found,
        "sole": sorted(k for k, e in found.items() if e["sole_support"]),
        "attested_sole": sorted(k for k, e in found.items()
                                if e["sole_support"] and e.get("confidence") == "attested"),
        "records": sorted({k.split("/")[0] for k in found}),
        "ungated": ungated_citations(blocked),
    }
    return census, evaluate(found, bank, sources)


def print_census(c: dict) -> None:
    print("AGENTS.md rule 6: a check_required source may be cited in text but must not "
          "have assets derived from it.\n")
    print(f"  {len(c['blocked'])} of {c['sources']} source(s) have unresolved rights")
    print(f"  {len(c['deriving_declared'])} source(s) declare a deriving asset_use, and "
          f"none of them is one of those {len(c['blocked'])} — which is the whole of what "
          f"the label test can see")
    print(f"\n  {len(c['found'])} geometry-bearing attribute(s) on {len(c['records'])} "
          f"record(s) cite an unresolved source:")
    for key in sorted(c["found"]):
        e = c["found"][key]
        mark = "SOLE" if e["sole_support"] else "    "
        print(f"    {mark} {key:<58} {e.get('confidence') or '-':<12} "
              f"{', '.join(e['blocked_sources'])}")
    print(f"\n  {len(c['sole'])} of them stand on unresolved support alone, "
          f"{len(c['attested_sole'])} of those graded attested")
    for layer, n in sorted(c["ungated"].items()):
        print(f"  residual: data/{layer} carries {n} citation(s) of an unresolved source "
              f"and has no declared read-set, so nothing here gates it")


def self_test() -> int:
    """Break each assertion in memory, against the real tree.

    K37's lesson, applied at the moment the gate is written rather than three
    parcels later: a gate nobody has watched fail is a gate nobody knows fires.
    """
    sources = read_sources()
    blocked = blocked_ids(sources)
    found = structure_entries(blocked)
    found.update(ground_entries(blocked))
    bank = read_bank()
    if not found or not bank:
        print("SELF-TEST FAIL: nothing measured, so no assertion can be exercised")
        return 1

    key = sorted(found)[0]
    corroborated = next((k for k, e in found.items() if not e["sole_support"]), None)
    blocked_id = sorted(blocked)[0]

    cases: list[tuple[str, dict, dict, dict]] = []

    s2 = copy.deepcopy(sources)
    s2[blocked_id]["asset_use"] = "geometry"
    cases.append(("1 an unresolved source declaring a deriving use", found, bank, s2))

    f2 = copy.deepcopy(found)
    f2["invented_record/invented_phase/form.construction"] = {
        "kind": "structure", "blocked_sources": [blocked_id],
        "sole_support": True, "confidence": "inferred"}
    cases.append(("2 a new geometry-bearing citation", f2, bank, sources))

    f3 = copy.deepcopy(found)
    f3.pop(key)
    cases.append(("3 a banked entry that left the data", f3, bank, sources))

    b4 = copy.deepcopy(bank)
    b4[key]["blocked_sources"] = []
    cases.append(("4a a banked entry gaining an unresolved source", found, b4, sources))

    if corroborated:
        b5 = copy.deepcopy(bank)
        b5[corroborated]["sole_support"] = False
        f5 = copy.deepcopy(found)
        f5[corroborated]["sole_support"] = True
        cases.append(("4b corroboration lost", f5, b5, sources))

    ok = True
    for label, f, b, s in cases:
        problems = evaluate(f, b, s)
        clean = evaluate(found, bank, sources)
        fired = len(problems) > len(clean)
        print(f"  {'fires' if fired else 'SILENT'}  {label}")
        ok = ok and fired
    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true", help="exit 1 on a divergence")
    ap.add_argument("--quiet", action="store_true", help="print only the verdict")
    ap.add_argument("--self-test", action="store_true",
                    help="break each assertion in memory and check that it fires")
    ap.add_argument("--update", action="store_true", help="rewrite the baseline")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    census, problems = measure()

    if args.update:
        BASELINE.write_text(json.dumps({
            "_doc": "Every geometry-bearing attribute whose evidence includes a source "
                    "whose rights are unresolved (check_required or restricted), as of the "
                    "last deliberate change. Geometry-bearing means the archetype's "
                    "CONSUMED set or the footprint polygon the params read; on the ground "
                    "it means a spec block with at least one figure in "
                    "terrain_inputs.CONSUMED. This is a measurement, not a permission: "
                    "tools/measure_rights_derivation.py holds it exact in both directions, "
                    "so a new one fails and a repaired one has to be un-banked here in the "
                    "commit that repaired it. Read ROADMAP K41 before adding a line.",
            "entries": {k: census["found"][k] for k in sorted(census["found"])},
        }, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE.relative_to(ROOT)} ({len(census['found'])} entries)")
        return 0

    if not args.gate and not args.quiet:
        print_census(census)

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1
    if args.gate or args.quiet:
        print(f"rights derivation: {len(census['found'])} geometry-bearing attribute(s) on "
              f"{len(census['records'])} record(s) are built from a source whose rights are "
              f"unresolved, {len(census['sole'])} of them with no other support "
              f"({len(census['attested_sole'])} graded attested); the population is banked "
              f"and may not grow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
