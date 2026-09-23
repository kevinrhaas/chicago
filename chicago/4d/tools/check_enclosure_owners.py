#!/usr/bin/env python3
"""Every fence in this town can say whose ground it stands on — checked, not asserted.

T-0637. The enclosure layer used to hold 289 lot-line runs and 13 dooryard runs that
belonged to nobody, and the fix (tools/enclosure_owners.py) is a DERIVATION, which means it
is only worth anything if it stays derivable. This is that gate, and it asks three things.

1. EVERY RUN ANSWERS. A run on a generated record carries a `belongs_to` naming the lot, the
   committed buildings on it and the households the committed index puts in those buildings
   — or an explicit `refused` token saying why not. A run on a HAND-AUTHORED record answers
   at the record level instead, through `belongs_to` or `structure_id`, which is how the
   Sauganash's yard and the pound have always answered. A run that answers neither way is
   the failure this file exists to catch.

2. THE HAND-AUTHORED YARDS ARE NOT OVERWRITTEN, and the derivation is run against them
   anyway and REPORTED. Where their ground is platted the two answers are compared; where it
   is not — the Western's wagon yard and the estray pen both stand off the plat — the
   derivation has nothing to say and says so. Nothing here edits a hand-authored record: an
   authored owner is evidence somebody read, and a derivation that disagrees with one is a
   finding to print, not a value to replace.

3. NOTHING NAMES A THING THAT ISN'T THERE. Every structure id in a `belongs_to` is a file in
   data/structures/ and every household id is in the committed household index. That is the
   check that would have caught the stale-prose problem this join deliberately steps around
   (T-0516): 53 of the 59 household ids the relevant `occupants` notes name belong to
   households the 2026-09-02 synthesis removed.

    python3 tools/check_enclosure_owners.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_dooryard_pickets import poly_contains  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENCLOSURES = DATA / "enclosures"
STRUCTURES = DATA / "structures"
LOTS_PATH = DATA / "traces" / "vectors" / "thompson_lots.json"
SIDECARS = DATA / "sidecars" / "1835"

# The records whose runs are generated, and therefore carry their own ownership.
GENERATED = {"town_lot_line_boards", "town_lot_line_pickets", "town_lot_line_rails",
             "town_dooryard_pickets"}
# The records written by hand against a building, whose authored owner is evidence.
AUTHORED = ["sauganash_yard", "western_hotel_wagon_yard", "estray_pen"]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lot_occupancy() -> tuple[dict, list]:
    lots = load(LOTS_PATH)
    occ: dict[str, list[str]] = {}
    for path in sorted(SIDECARS.glob("*.json")):
        pl = (load(path).get("placement") or {})
        if pl.get("local_e") is None:
            continue
        for block in lots["blocks"]:
            for i, lot in enumerate(block["lots"]):
                if poly_contains((pl["local_e"], pl["local_n"]), lot["polygon"]):
                    occ.setdefault(f"{block['id']}_lot{i}", []).append(path.stem)
    return occ, lots


def lot_of(point, lots) -> str | None:
    for block in lots["blocks"]:
        for i, lot in enumerate(block["lots"]):
            if poly_contains(point, lot["polygon"]):
                return f"{block['id']}_lot{i}"
    return None


def main() -> int:
    errors: list[str] = []
    households = {hh["id"] for hh in
                  load(DATA / "residents" / "index.json").get("households", [])}
    occ, lots = lot_occupancy()

    runs = joined = refused = 0
    for path in sorted(ENCLOSURES.glob("*.json")):
        if path.stem == "index":
            continue
        rec = load(path)
        answered_at_record = bool(rec.get("belongs_to")) or bool(rec.get("structure_id"))
        for run in rec.get("runs", []):
            runs += 1
            entries = run.get("belongs_to")
            if not entries:
                if path.stem in GENERATED:
                    errors.append(f"{path.name}: run {run.get('id')} carries no belongs_to — "
                                  f"a generated run has to say whose ground it stands on")
                elif not answered_at_record:
                    errors.append(f"{path.name}: run {run.get('id')} belongs to nobody, and "
                                  f"the record names neither a belongs_to nor a structure_id")
                continue
            for entry in entries:
                for sid in entry.get("structures", []):
                    if not (STRUCTURES / f"{sid}.json").exists():
                        errors.append(f"{path.name}: run {run.get('id')} bounds {sid}, which "
                                      f"is not a structure in this repository")
                for hh in entry.get("households", []):
                    if hh["id"] not in households:
                        errors.append(f"{path.name}: run {run.get('id')} names household "
                                      f"{hh['id']}, which the committed index does not hold")
                if not entry.get("households") and not entry.get("refused"):
                    errors.append(f"{path.name}: run {run.get('id')} has no household on "
                                  f"{entry.get('lot')} and no recorded refusal either")
            if any(e.get("households") for e in entries):
                joined += 1
            else:
                refused += 1

    print(f"enclosure ownership: {runs} run(s) on the layer; {joined} joined to a household, "
          f"{refused} bounding structures only with a recorded refusal")

    # The hand-authored yards, re-derived and REPORTED. Never overwritten.
    for name in AUTHORED:
        path = ENCLOSURES / f"{name}.json"
        if not path.exists():
            continue
        rec = load(path)
        authored = set(rec.get("belongs_to") or ([rec["structure_id"]]
                                                 if rec.get("structure_id") else []))
        derived: set[str] = set()
        unplatted = 0
        for run in rec.get("runs", []):
            pts = run["path_local_enu_m"]
            mid = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            lot = lot_of(mid, lots)
            if lot is None:
                unplatted += 1
                continue
            derived.update(occ.get(lot, []))
        if unplatted and not derived:
            print(f"  {name}: authored {sorted(authored)}; the derivation has NOTHING to "
                  f"compare — {unplatted} run(s) stand on ground the plat does not divide "
                  f"into lots, so the authored owner is the only answer and it stands")
            continue
        if authored <= derived:
            extra = sorted(derived - authored)
            print(f"  {name}: authored {sorted(authored)}; the derivation AGREES" +
                  (f", and finds {extra} standing on the same lot — a second building on the "
                   f"ground, not a second owner of the yard, so the authored value stands"
                   if extra else ""))
        else:
            print(f"  {name}: DISAGREEMENT REPORTED — authored {sorted(authored)}, the lot "
                  f"holds {sorted(derived)}. The authored value is left exactly as it is; "
                  f"an owner somebody read out of a source is not overwritten by a "
                  f"centroid test.")
        for sid in authored:
            if not (STRUCTURES / f"{sid}.json").exists():
                errors.append(f"{name}: belongs_to names {sid}, which is not a structure in "
                              f"this repository")

    if errors:
        print("ENCLOSURE OWNERSHIP FAILURES")
        for e in errors:
            print(f"  - {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
