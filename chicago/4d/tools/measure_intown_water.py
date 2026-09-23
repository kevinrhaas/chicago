#!/usr/bin/env python3
"""Where the in-town water this project defers stands at the scene date.

ROADMAP T-E5(a). The dating itself is authored in
`data/terrain/1835_intown_water_dating.json`; this is the command that prints it and
the gate `tools/check.sh` runs, for the same reason `tools/measure_reserved_ground.py`
and `tools/measure_no_build_ground.py` exist — a rule nobody can run is a rule the next
parcel has to remember, and a deferral nobody can list is a claim nobody re-reads.

    tools/measure_intown_water.py          print the table
    tools/measure_intown_water.py --gate   exit 1 if a deferral is undated

THE GATE IS A CORRESPONDENCE, IN BOTH DIRECTIONS, and that is the whole of its value.
The terrain spec's `not_modelled_in_this_box` is where a feature gets deferred, and it
is a list of prose: before this, a fifth in-town water feature could be added to it, or
a dated one silently dropped from the dating record, and nothing anywhere would notice.
So the gate fails on a deferred water feature with no dating entry AND on a dating entry
naming a zone the spec does not defer — a dating record that can go stale silently is a
way of turning the question back off.

WHICH ZONES IT COVERS IS DECLARED, NOT SNIFFED. Matching on the word "water" in a prose
`why` is exactly the class of bug R-W4a and the smoke's own `/terrain|water/i` filter
were: a regex over prose that reads like a rule until a name changes under it. The four
zones are named in the dating record, and the spec entry is found by number.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATING_PATH = DATA / "terrain" / "1835_intown_water_dating.json"
SPEC_GLOB = "terrain/epochs/*/terrain_spec.json"

# The vocabulary of `tools/validate.py`. Named here rather than imported because this
# gate must run when the validator is the thing being changed.
CONFIDENCE = ("attested", "inferred", "reconstructed")
VALUES = ("present", "not_established")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def deferred_zones() -> dict[int, dict]:
    """dossier_zone -> the spec entry deferring it, across every committed epoch."""
    out: dict[int, dict] = {}
    for spec_path in sorted(DATA.glob(SPEC_GLOB)):
        spec = load(spec_path)
        for entry in spec.get("not_modelled_in_this_box", []):
            zone = entry.get("dossier_zone")
            if zone is not None:
                out[zone] = {**entry, "epoch": spec.get("epoch"), "spec": spec_path.name}
    return out


def measure() -> tuple[list[dict], list[str]]:
    """(rows, problems). One row per dated in-town water feature."""
    doc = load(DATING_PATH)
    spec_entries = deferred_zones()
    problems: list[str] = []
    rows: list[dict] = []

    source_ids = {p.stem for p in (DATA / "sources").glob("*.json")}
    seen: set[int] = set()

    for feature in doc.get("features", []):
        zone = feature.get("dossier_zone")
        name = feature.get("name", "?")
        where = f"in-town water zone {zone} ({name})"

        if zone in seen:
            problems.append(f"{where}: duplicate dossier_zone in the dating record")
        seen.add(zone)

        # Direction one: the dating record may not name a zone the spec does not defer.
        # A dating entry for a feature that is now MODELLED is not a harmless leftover —
        # it is a graded claim about a scene, still being read, describing ground the
        # scene no longer treats that way.
        spec_entry = spec_entries.get(zone)
        if spec_entry is None:
            problems.append(
                f"{where}: dated here, but no terrain spec defers dossier zone {zone}. "
                f"Either the feature is modelled now — in which case its dating belongs "
                f"with the claim that models it — or the zone number is wrong.")

        dating = feature.get("at_scene_date") or {}
        value = dating.get("value")
        conf = dating.get("confidence")
        srcs = dating.get("sources") or []
        note = (dating.get("note") or "").strip()

        if value not in VALUES:
            problems.append(f"{where}: at_scene_date.value '{value}' is not one of "
                            f"{sorted(VALUES)}")
        if conf not in CONFIDENCE:
            problems.append(f"{where}: at_scene_date.confidence '{conf}' is not one of "
                            f"{sorted(CONFIDENCE)}")
        for s in srcs:
            if s not in source_ids:
                problems.append(f"{where}: source '{s}' does not resolve in data/sources/")
        if conf == "attested" and not srcs:
            problems.append(
                f"{where}: dated `attested` with no source. The strongest grade this "
                f"project has is the one that needs evidence, and a date is evidence "
                f"about a scene rather than about a place.")
        if conf == "inferred" and not note:
            problems.append(
                f"{where}: dated `inferred` with no reasoning recorded — that is what "
                f"separates an inference from a guess, and it is the whole reason this "
                f"file exists.")
        if not (feature.get("dossier_row") or "").strip():
            problems.append(f"{where}: no dossier_row — the feature's own existence grade "
                            f"is quoted here, not re-graded, so it has to be quoted")

        rows.append({
            "zone": zone, "name": name, "value": value, "confidence": conf,
            "sources": srcs, "deferred": spec_entry is not None,
            "epoch": (spec_entry or {}).get("epoch", "-"),
        })

    # Direction two: a deferral that mentions one of these features by name and is not
    # dated here. The set of in-town water zones is the dating record's own; a zone the
    # spec defers and this file has never heard of is only a problem if it is one of
    # them, which is what `covers_dossier_zones` declares.
    declared = doc.get("covers_dossier_zones") or []
    for zone in declared:
        if zone not in seen:
            problems.append(
                f"in-town water zone {zone}: declared covered by "
                f"{DATING_PATH.name} and has no dating entry")
        if zone not in spec_entries:
            problems.append(
                f"in-town water zone {zone}: declared covered, but no terrain spec "
                f"defers it")

    return rows, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if a deferred in-town water feature is undated")
    args = ap.parse_args()

    rows, problems = measure()

    if not args.gate:
        print(f"{'zone':>4}  {'feature':<34} {'at 1835-07-01':<16} {'grade':<12} sources")
        for r in sorted(rows, key=lambda r: r["zone"] or 0):
            print(f"{r['zone']:>4}  {r['name']:<34} {r['value']:<16} "
                  f"{r['confidence']:<12} {', '.join(r['sources'])}")
        present = sum(1 for r in rows if r["value"] == "present")
        print(f"\n{len(rows)} deferred in-town water feature(s): {present} placed at the "
              f"scene date, {len(rows) - present} not established. None is modelled — "
              f"this record dates the deferrals, it does not lift them.")

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1
    if args.gate:
        print(f"in-town water: {len(rows)} deferred feature(s), each dated against "
              f"1835-07-01 with a resolving source or recorded reasoning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
