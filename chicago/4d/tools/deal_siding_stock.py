#!/usr/bin/env python3
"""Deal a clapboard stock to every NAMED frame building — T-0049, docs/LIBERTIES.md L148.

Until T-0049 every frame building in the town wore one course rhythm: the
archetypes' shared 0.14 m (~5.5 in) constant. That uniformity is an artefact of
the generator, not a finding about the town — no source states the exposed face
of any Chicago building's siding, and a town supplied by separate shipments of
sawn lumber (by scow from St Joseph — docs/research/02-flora.md) did not side
every building from one pile.

So the exposure is RECONSTRUCTED, invented within a bound, and this tool is the
deal for the NAMED half of the town. The set of four period mill sidings and the
separation rule are authored once in `tools/siding_stock.py`, which the parcel
recipes import for the anonymous half (T-0112) — one set, two populations, and no
second opinion about what a board is.

The rule, in full — deterministic, so the committed records re-derive:

1. Only NAMED frame records are dealt here (archetype frame_dwelling /
   frame_storefront / frame_tavern, id not prefixed recon_/inf_ and not owned by
   the inferred-household programme's buildings list). Derived records re-derive
   byte-exact from their recipes and cannot be hand-edited — so **their recipes
   deal them**, and this tool reads what those recipes wrote and treats each as a
   fixed neighbour at the stock it actually wears. Until T-0112 it assumed 0.140 m
   for all of them, which was true only because nothing had dealt them yet.
2. Only the phase the 1835 scene resolves is dealt, and only when its resolved
   cladding is clapboard — a vertical-board wall has no course to expose. A
   derived record with a vertical-board wall is not a neighbour either, for the
   same reason: there is no course on it to collide with.
3. The base stock is keyed to the phase's construction season
   ((year + quarter) % 4): buildings sided from the same season's shipments tend
   toward the same stock, which is the one supply fact the deal can lean on. It is
   a tendency, not evidence about any building — the note on every value says so.
   (The anonymous records cannot use this key: their `1835-01-01` is the
   programme's count-unit convention rather than a construction season, so it
   would deal all 131 of them one stock. `tools/siding_stock.py` says what they
   use instead and why.)
4. Then the deal advances a building's stock until no other clapboard frame wall
   within NEIGHBOUR_M shares it — named ones in id order, derived ones fixed at
   what their recipe dealt them. That separation is not a claim about 1835; it is
   the surface variety T-0049 reconstructs, recorded as such.

Run with no arguments to (re)write the named records. `--check` verifies the
committed values still re-derive from this rule AND that every invented clapboard
frame roof in the town carries a stock from the set, so a recipe that quietly
stopped dealing is a failure here rather than 131 identical walls nobody notices.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"
sys.path.insert(0, str(ROOT / "tools"))

# The set, the separation distance and the advance rule are the shared ones. This file
# owns only the NAMED half's key and note; everything a recipe also needs lives there.
from siding_stock import (DEFAULT_M, FRAME_ARCHETYPES, NEIGHBOUR_M,  # noqa: E402
                          STOCKS, advance, cladding_of, exposure_of,
                          hangs_clapboard, is_invented)

GENERATED_PREFIXES = ("recon_", "inf_")
# The inferred-household programme regenerates its buildings' records byte-exact
# (tools/generate_inferred_households.py --check), named ones included, so the
# deal must not write into them any more than into a recon_ record. Its
# `buildings` list is the ownership roster.
HOUSEHOLD_PROGRAMME = ROOT / "data" / "reconstruction" / "1835_inferred_household_programme.json"
TARGET = dt.date(1835, 7, 1)

STOCK_VALUES = frozenset(m for _, m in STOCKS)

NOTE = ("INVENTED WITHIN A STOCK SET, NOT DERIVED. No source states the exposed face "
        "of any Chicago building's siding. The value is one of four period mill "
        "sidings — 4.5, 5, 5.5 or 6 in to the weather; this record wears {inches} — "
        "dealt by tools/deal_siding_stock.py: keyed to the phase's construction "
        "season, because buildings sided from the same season's shipments of St "
        "Joseph sawn lumber tend toward one stock, then advanced so no frame "
        "building within 60 m shares this one's. The separation is the surface "
        "variety T-0049 reconstructs, not a claim about 1835. docs/LIBERTIES.md "
        "L148 owns the invention.")


def resolve_phase(structure: dict) -> dict | None:
    """The scene rule, identical to generators/build.py and tools/validate.py."""
    hits = []
    for ph in structure.get("phases", []):
        r = ph.get("documented_range", {})
        try:
            frm = dt.date.fromisoformat(r["from"])
            to = dt.date.fromisoformat(r["to"])
        except (KeyError, ValueError):
            continue
        if frm <= TARGET <= to:
            hits.append(ph)
    if len(hits) > 1:
        raise SystemExit(f"{structure['id']}: {len(hits)} phases cover {TARGET}")
    return hits[0] if hits else None


def frame_records() -> list[tuple[Path, dict, dict]]:
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        st = json.loads(path.read_text(encoding="utf-8"))
        if st.get("archetype") not in FRAME_ARCHETYPES:
            continue
        ph = resolve_phase(st)
        if ph is None:
            continue
        out.append((path, st, ph))
    return out


def position_of(ph: dict) -> tuple[float, float] | None:
    pos = ph.get("position") or {}
    e, n = pos.get("utm_e"), pos.get("utm_n")
    return None if e is None or n is None else (float(e), float(n))


def season_key(ph: dict) -> int:
    # Year plus quarter, not year*4+quarter: any multiple of len(STOCKS) folds to
    # zero under the modulus, which would silently erase one of the two terms.
    d = dt.date.fromisoformat(ph["documented_range"]["from"])
    return (d.year + (d.month - 1) // 3) % len(STOCKS)


def programme_owned() -> frozenset[str]:
    doc = json.loads(HOUSEHOLD_PROGRAMME.read_text(encoding="utf-8"))
    return frozenset(b["id"] for b in doc.get("buildings", []))


def is_derived(st: dict, owned: frozenset[str]) -> bool:
    """True when another tool regenerates this record byte-exact."""
    return st["id"].startswith(GENERATED_PREFIXES) or st["id"] in owned


def deal() -> dict[str, tuple[str, float]]:
    """structure id -> (inches label, exposure m) for every named clapboard record."""
    records = frame_records()
    owned = programme_owned()
    taken: list[tuple[float, float, float]] = []          # (e, n, exposure) already fixed
    for _, st, ph in records:
        if not is_derived(st, owned):
            continue
        # What the recipe dealt it, not an assumed default — and only if it hangs
        # boards at all. A derived vertical-board wall exposes no course and cannot
        # collide with one.
        if not hangs_clapboard(st.get("archetype"), ph.get("form")):
            continue
        pos = position_of(ph)
        if pos is not None:
            taken.append((*pos, exposure_of(ph.get("form"))))
    dealt: dict[str, tuple[str, float]] = {}
    for _, st, ph in records:
        if is_derived(st, owned):
            continue
        if cladding_of(ph.get("form")) != "clapboard":
            continue
        pos = position_of(ph)
        near = set()
        if pos is not None:
            near = {m for e, n, m in taken
                    if math.hypot(e - pos[0], n - pos[1]) <= NEIGHBOUR_M}
        inches, metres = advance(season_key(ph), near)
        dealt[st["id"]] = (inches, metres)
        if pos is not None:
            taken.append((*pos, metres))
    return dealt


def recipe_half(records: list[tuple[Path, dict, dict]]) -> list[str]:
    """T-0112's gate: every invented clapboard frame roof carries a dealt stock.

    The recipes deal it and their own `--check` holds them to the value byte for
    byte, so nothing here can drift silently — but nothing there would notice a
    recipe that stopped dealing altogether, because a record with no
    `siding_exposure_m` is a perfectly well-formed record. It just puts 131
    buildings back on one course, which is the defect T-0112 closed, and it would
    do it invisibly: the walls would still render, all alike.
    """
    problems = []
    for _, st, ph in records:
        if not is_invented(st):
            continue
        if not hangs_clapboard(st.get("archetype"), ph.get("form")):
            continue
        got = (ph.get("form") or {}).get("siding_exposure_m")
        if not isinstance(got, dict):
            problems.append(f"{st['id']}: an invented clapboard wall with no dealt "
                            f"stock — its recipe is no longer dealing one, so it is "
                            f"back on the archetypes' {DEFAULT_M} m default")
        elif got.get("value") not in STOCK_VALUES:
            problems.append(f"{st['id']}: siding_exposure_m is {got.get('value')!r}, "
                            f"which is not one of the four period stocks")
    return problems


def census(records: list[tuple[Path, dict, dict]]) -> str:
    """How much of the town's clapboard still stands beside its own stock."""
    walls = []
    for _, st, ph in records:
        if not hangs_clapboard(st.get("archetype"), ph.get("form")):
            continue
        pos = position_of(ph)
        if pos is not None:
            walls.append((pos, exposure_of(ph.get("form"))))
    pairs = shared = 0
    for i, (pa, ma) in enumerate(walls):
        for pb, mb in walls[i + 1:]:
            if math.hypot(pa[0] - pb[0], pa[1] - pb[1]) <= NEIGHBOUR_M:
                pairs += 1
                shared += ma == mb
    if not pairs:
        return "no two clapboard walls stand within 60 m of each other"
    return (f"{len(walls)} clapboard wall(s); {shared} of {pairs} pairs standing "
            f"within {NEIGHBOUR_M:g} m share a stock ({shared / pairs:.1%})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the committed values still re-derive from the rule")
    args = ap.parse_args()

    dealt = deal()
    owned = programme_owned()
    records = frame_records()
    drift = []
    changed = 0
    for path, st, ph in records:
        want = dealt.get(st["id"])
        got = (ph.get("form") or {}).get("siding_exposure_m")
        if want is None:
            if got is not None and not is_derived(st, owned):
                drift.append(f"{st['id']}: carries siding_exposure_m but the rule "
                             f"deals it none")
            continue
        inches, metres = want
        attr = {"value": metres, "confidence": "reconstructed",
                "note": NOTE.format(inches=inches)}
        if got == attr:
            continue
        if args.check:
            drift.append(f"{st['id']}: siding_exposure_m has drifted from the deal"
                         if got is not None else
                         f"{st['id']}: the rule deals a stock and the record has none")
            continue
        ph.setdefault("form", {})["siding_exposure_m"] = attr
        path.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        changed += 1
    if args.check:
        # Re-read, so the recipe half is judged on the committed tree rather than on
        # the copy this run has been editing in memory.
        drift += recipe_half(frame_records())
    if drift:
        print("SIDING STOCK DRIFT")
        for item in drift:
            print(f"  - {item}")
        return 1
    mode = "verified" if args.check else f"dealt ({changed} record(s) rewritten)"
    print(f"{mode}: {len(dealt)} named frame building(s) carry a stock; "
          f"{len(STOCKS)} stocks in the set")
    print(f"  town: {census(records)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
