#!/usr/bin/env python3
"""How many invented names does ONE new household rewrite? (ROADMAP K20)

    python3 tools/measure_name_churn.py           the census
    python3 tools/measure_name_churn.py --gate    assert insertion-locality
    python3 tools/measure_name_churn.py --probes 60   sample harder

WHY THIS EXISTS.

`tools/generate_inferred_names.py` promises that "re-running produces the same
town... nobody has to wonder whether a name drifted", and that promise held: the
allocator is deterministic and `--check` proves the committed data re-derives.
What it did NOT promise, and what nobody had measured, is what happens when the
town GROWS. Two parcels measured it by accident and reported the same thing —
T-A2h saw two new people rename 25 of 94 reconstructed residents, and T-A5 saw a
ONE-household insertion rename 17 of the 33 invented persons in the files it
touched, dragging 24 files into a diff whose real content was one addition.

Both were anecdotes from parcels doing something else. This is the instrument.
It inserts a synthetic household into the layer IN MEMORY, re-runs the allocator,
and counts how many PRE-EXISTING persons come out with a different name. Nothing
is written and no record is touched: the probe household exists only inside this
process, which is why the measurement can be run on a clean tree at any time.

WHAT THE NUMBER MEANS.

A name here is invented, graded `reconstructed`, and owes nothing to any source,
so churn is not a provenance failure — every name in every reading is equally
honest. It is a REVIEW failure. A block parcel that adds four households and
rewrites a quarter of the town's names ships a diff in which the four real
additions cannot be found, and a genuine drift — a name that changed because
something is wrong — is invisible inside the noise. The gate below is therefore
about keeping the diff readable, not about the names.

The probe deliberately samples several trades: the bucket a person lands in is a
function of their occupation's community weighting, and the pools differ in size
by 2.7x, so a churn figure taken from one trade says nothing about the others.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Occupations to probe with. Chosen to cover every (community, sex) bucket the
# layer actually populates: the two big yankee/irish male buckets that most
# insertions land in, a boatman (french colonial on evidence), and the two
# female trades this dataset records.
PROBE_TRADES = ["carpenter", "labourer", "cooper", "boatman", "laundress", "domestic"]


def _names_tool():
    spec = importlib.util.spec_from_file_location(
        "generate_inferred_names", ROOT / "tools" / "generate_inferred_names.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probe_household(trade: str, k: int) -> tuple[pathlib.Path, dict]:
    """One synthetic household, shaped like the ones the programme writes.

    The id is what decides where the person lands — the allocator hashes it for
    the community draw and again for the deal order — so varying k is how this
    samples the hash space rather than one arbitrary point in it.
    """
    pid = f"churn_probe_{trade}_{k:03d}"
    doc = {
        "id": f"hh_{pid}",
        "name": "The probe household",
        "division": "south",
        "head": pid,
        "persons": [{
            "id": pid,
            "relationship": "head",
            "grade": "reconstructed",
            "occupation": {"value": trade, "confidence": "reconstructed"},
        }],
    }
    return ROOT / "data" / "residents" / "households" / f"hh_{pid}.json", doc


def _assigned(mod, docs: dict) -> dict[str, str]:
    """{person id: name} for one allocation over a given set of household docs."""
    # build() names in place on the docs it is handed, so hand it a copy and read
    # the names back off that rather than parsing its serialised output again.
    working = copy.deepcopy(docs)
    mod.build(preload=working)
    out = {}
    for doc in working.values():
        for person in doc.get("persons", []):
            if person.get("grade") == "reconstructed" and person.get("name"):
                out[person["id"]] = person["name"]
    return out


def measure(probes: int) -> dict:
    mod = _names_tool()
    base_docs = {p: mod.load(p) for p in sorted(mod.HOUSEHOLDS.glob("*.json"))}
    baseline = _assigned(mod, base_docs)

    rows = []
    for trade in PROBE_TRADES:
        for k in range(probes):
            path, doc = _probe_household(trade, k)
            grown = dict(base_docs)
            grown[path] = doc
            after = _assigned(mod, grown)
            renamed = [pid for pid, name in baseline.items()
                       if after.get(pid) != name]
            rows.append({"trade": trade, "k": k, "renamed": len(renamed),
                         "pressure": _pressure(mod, base_docs, doc)})
    return {"population": len(baseline), "rows": rows}


def _pressure(mod, base_docs: dict, probe: dict) -> float:
    """How far past its surname pool the bucket this probe lands in already is.

    The residual churn is a function of THIS, not of how big the layer is — which
    is the whole difference between the allocator this measures and the one it
    replaced. A bucket with room to spare renames nobody, because the newcomer
    takes a surname nobody wanted. A bucket already dealing its 36 surnames to 73
    men has no spare name at the floor, so the newcomer displaces somebody and
    that person displaces the next. Reported so the two readings cannot be
    confused: 8 renames at pressure 2.0 is a pool that is too small, and 8 at
    pressure 0.3 would be an allocator that is still not local.
    """
    pools = mod.load(mod.POOLS)
    by_id = {c["id"]: c for c in pools["communities"]}
    person = probe["persons"][0]
    occ = (person.get("occupation") or {}).get("value") or ""
    cid, _ = mod.community_for(pools, occ, person["id"])
    female = person.get("sex") == "female" or occ in mod.FEMALE_TRADES
    size = 0
    for doc in base_docs.values():
        for other in doc.get("persons", []):
            if other.get("grade") != "reconstructed":
                continue
            o_occ = (other.get("occupation") or {}).get("value") or ""
            o_cid, _ = mod.community_for(pools, o_occ, other["id"])
            o_female = other.get("sex") == "female" or o_occ in mod.FEMALE_TRADES
            if (o_cid, o_female) == (cid, female):
                size += 1
    return size / len(by_id[cid]["surnames"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="fail if one insertion rewrites more than --max names")
    ap.add_argument("--probes", type=int, default=12,
                    help="synthetic insertions per trade (default 12)")
    # The bar is not "zero", and it is deliberately not "today's number" either.
    #
    # It cannot be zero: a pool smaller than its bucket must reuse a surname, so
    # a newcomer necessarily displaces somebody and that person displaces the
    # next. Measured on the committed layer, the two buckets with room to spare
    # (pressure 0.14x) rename at most ONE, and the four dealing 36 surnames to 73
    # men (pressure 2.03x) rename at most ten. That is the pool being too small,
    # not the allocator being non-local, which is why `pressure` is in the report.
    #
    # It is 16 rather than 10 because what this must catch is the CLASS of
    # regression — an allocation that depends on how many people sort ahead of
    # you — and every measurement of that class has been far above 16: 73 here,
    # 25 in T-A2h, 17 in T-A5. Sixteen sits under the lowest of them and well over
    # today's worst, so ordinary growth inside these pools cannot turn the gate
    # red while a return to index dealing cannot slip under it. If this does fire
    # on growth, the answer is a wider pool — more attested seeds — and not a
    # higher number here.
    ap.add_argument("--max", type=int, default=16,
                    help="the most pre-existing names one insertion may rewrite")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    result = measure(args.probes)
    rows = result["rows"]
    counts = [r["renamed"] for r in rows]
    worst = max(counts)
    by_trade = {}
    for r in rows:
        by_trade.setdefault(r["trade"], []).append(r["renamed"])

    if not args.quiet:
        print(f"   {result['population']} reconstructed resident(s) carry an invented name")
        print(f"   {len(rows)} synthetic single-household insertions "
              f"({args.probes} per trade)")
        print(f"   {'trade':<16}{'pressure':>10}{'worst':>7}{'mean':>8}{'zero-churn':>12}")
        for trade, cs in by_trade.items():
            zero = sum(1 for c in cs if c == 0)
            pressure = max(r["pressure"] for r in rows if r["trade"] == trade)
            print(f"   {trade:<16}{pressure:>9.2f}x{max(cs):>7}"
                  f"{statistics.mean(cs):>8.2f}{zero:>7}/{len(cs)}")
        print(f"   worst case: {worst} of {result['population']} "
              f"({100 * worst / result['population']:.1f} %)")

    if args.gate:
        if worst > args.max:
            offender = max(rows, key=lambda r: r["renamed"])
            print(f"   FAIL: inserting one {offender['trade']} household renamed "
                  f"{offender['renamed']} pre-existing resident(s), over the "
                  f"{args.max} this layer allows. The allocator has stopped being "
                  f"insertion-local — see ROADMAP K20.")
            return 1
        print(f"   OK: one insertion rewrites at most {worst} pre-existing "
              f"name(s) (allowed {args.max})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
