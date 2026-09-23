#!/usr/bin/env python3
"""Is the anonymous town a distribution, or one building stamped out?

ROADMAP T-V1. R-G1 scored `south_water` 3.38 and put the reason on historical
accuracy rather than on the renderer: a horizon row of one gable form, at one width,
one pitch and one eave height, repeated at even spacing. **Uniformity is itself a
claim and no source makes it** — the crosswalk authors every family's footprint and
eave as a RANGE, and a generator that collapses that range to a point has invented a
town where every carpenter built the same shed.

This measures it, per parcel, per family:

  * how many roofs share a footprint AND an eave with another roof of their own
    family — the stamp, counted;
  * how many carry a value outside the band their own note cites — which is a
    provenance fault rather than a visual one, and is ROADMAP K25's subject: a note
    that cites a band says *the invention is bounded by the specification*, and
    where the value is outside the band the note is wrong about its own source.

## What it gates, and what it only reports

**The gate's subject is a sentence the data itself makes.** 138 of the 218 anonymous
records say, in their own footprint note, that the rectangle was `sampled
deterministically` inside the family's authored footprint band. That claim is held to
what it says: the footprint is inside the band, and no two roofs of one family in one
parcel were dealt the same rectangle. It fails if the sampling in
`tools/family_bands.py` is ever widened past a band or collapsed back to a constant.

**The eave is not gated, and finding out why is what this tool was written for.** No
record claims a sampled eave, and the census says why that matters: the note on every
eave value cites the family band — *"Type-level choice within the D3 band"* — and 40
of the 218 values are outside the band they cite. The phase-one parcel is the sharp
case, because it samples its FOOTPRINT and carries the sentence saying so while its
eave is still one constant per family: **18 of its 48 roofs**. A note that cites a band
is a provenance claim, so those 40 notes are wrong about their own source rather than
merely imprecise. That is ROADMAP K25's subject and T-V1(b)'s consequence, and both
need the bake: the three parcels holding all 40 are canonical Blender bakes, changing
a dimension stales every one of them, and the nightly bake builds from `dev` — so the
fix cannot reach `dev` through a gate it would turn red on the way.

**Do not read a pass here as "the town is a distribution."** Read the census.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"
CROSSWALK = ROOT / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json"
PREFIX = "recon_1835_"
SAMPLED_MARK = "sampled deterministically"

FOOTPRINT_RE = re.compile(r"^\s*(\d+)x(\d+)\s*-\s*(\d+)x(\d+)")
RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$")
FT = 0.3048
# A hair of slack, because every committed dimension is a rounded metre value and a
# band edge is a whole foot. 1 mm cannot hide a building outside its typology.
EPS = 0.0015


def bands() -> dict[str, dict]:
    table = {}
    for fam in json.loads(CROSSWALK.read_text(encoding="utf-8"))["families"]:
        geom = fam.get("key_geometry_parameters") or {}
        entry = {"eave_m": None, "width_m": None, "depth_m": None}
        m = RANGE_RE.match(str(geom.get("eave_ft") or ""))
        if m:
            entry["eave_m"] = (float(m.group(1)) * FT, float(m.group(2)) * FT)
        m = FOOTPRINT_RE.match(str(geom.get("footprint_ft") or ""))
        if m:
            lo_w, lo_d, hi_w, hi_d = (int(m.group(i)) for i in (1, 2, 3, 4))
            entry["width_m"] = (lo_w * FT, hi_w * FT)
            entry["depth_m"] = (lo_d * FT, hi_d * FT)
        table[fam["id"]] = entry
    return table


def massing(record: dict) -> tuple[float, float, float]:
    """(width, depth, eave) in metres, off the committed polygon and form."""
    phase = record["phases"][0]
    poly = phase["footprint"]["polygon"]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    wall = phase["form"].get("wall_height_m")
    eave = float(wall["value"]) if isinstance(wall, dict) else float(wall or 0)
    return (round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), eave)


def survey() -> dict[str, dict]:
    table = bands()
    parcels: dict[str, dict] = {}
    for path in sorted(STRUCTURES.glob(f"{PREFIX}*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        recon = rec.get("reconstruction") or {}
        parcel = recon.get("programme_phase") or "(unattributed)"
        family = recon.get("family")
        phase = rec["phases"][0]
        entry = parcels.setdefault(parcel, {
            "roofs": 0, "sampled": 0, "by_family": collections.defaultdict(list),
            "outside": [], "plan_outside": [],
        })
        entry["roofs"] += 1
        if SAMPLED_MARK in (phase["footprint"].get("note") or ""):
            entry["sampled"] += 1
        width, depth, eave = massing(rec)
        entry["by_family"][family].append((width, depth, eave))
        band = table.get(family) or {}
        for label, value, span in (("eave", eave, band.get("eave_m")),
                                   ("width", width, band.get("width_m")),
                                   ("depth", depth, band.get("depth_m"))):
            if span and not (span[0] - EPS <= value <= span[1] + EPS):
                entry["outside" if label == "eave" else "plan_outside"].append(
                    f"{rec['id']} {label} {value:.3f} m is outside the {family} band "
                    f"{span[0]:.2f}-{span[1]:.2f} m, and its note cites that band")
    for entry in parcels.values():
        entry["duplicates"] = sum(
            n - 1 for shapes in entry["by_family"].values()
            for n in collections.Counter(shapes).values() if n > 1)
        entry["twin_plans"] = sum(
            n - 1 for shapes in entry["by_family"].values()
            for n in collections.Counter((w, d) for w, d, _ in shapes).values() if n > 1)
        entry["distinct"] = sum(len(set(v)) for v in entry["by_family"].values())
    return parcels


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="fail if a parcel that claims to sample its bands does not")
    args = ap.parse_args()
    parcels = survey()

    failures: list[str] = []
    print(f"   {'parcel':44} roofs  plans  twins  eaves out  claims sampling")
    for name, e in sorted(parcels.items()):
        claims = e["sampled"] == e["roofs"]
        mark = "yes" if claims else ("part" if e["sampled"] else "NO")
        plans = e["roofs"] - e["twin_plans"]
        print(f"   {name:44} {e['roofs']:5} {plans:6} {e['twin_plans']:6}"
              f" {len(e['outside']):10}  {mark}")
        if claims:
            if e["twin_plans"]:
                failures.append(f"{name} says its footprints are {SAMPLED_MARK} inside "
                                f"the family band, and {e['twin_plans']} of its "
                                f"{e['roofs']} roofs were dealt a rectangle another "
                                f"roof of their own family already has")
            failures.extend(e["plan_outside"])

    # The census. Not a failure, and the reason it is not is in the module docstring.
    owed = sum(len(e["outside"]) for e in parcels.values())
    stamped = sum(e["duplicates"] for e in parcels.values())
    for name, e in sorted(parcels.items()):
        if not (e["duplicates"] or e["outside"]):
            continue
        print(f"\n   {name} — owed to ROADMAP T-V1(b) and K25, both of which need the bake:")
        if e["duplicates"]:
            print(f"     {e['duplicates']} of {e['roofs']} roofs share a footprint AND an "
                  f"eave with another roof of their own family; "
                  f"{e['distinct']} distinct massings in all")
        for line in e["outside"][:3]:
            print(f"     {line}")
        if len(e["outside"]) > 3:
            print(f"     ... and {len(e['outside']) - 3} more eave(s) outside the cited band")

    if failures:
        print("\n   MASSING VARIETY FAILURES")
        for line in failures:
            print(f"     - {line}")
        return 1
    total = sum(e["roofs"] for e in parcels.values())
    print(f"\n   {total} anonymous roof(s). Every footprint that claims to be sampled "
          f"inside its family band is, and is unique within its family and parcel. "
          f"NOT ASSERTED and owed: {stamped} stamped massing(s) and {owed} eave(s) "
          f"outside the band their own note cites.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
