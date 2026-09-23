#!/usr/bin/env python3
"""A block face carries ONE street line, and it is measured rather than declared.

T-0104. Two generators build party-line rows onto the committed block faces —
`tools/generate_inferred_infill.py` (T-0077) and `tools/generate_block_infill.py`
(T-0078, T-0079, T-0105) — and each of them asserts that ITS OWN run stands on one
line. Neither could see the other. The Lake face of `blk_lake_clark` is built by
both, and it carried two: T-0077's four units 0.80 m off the face and T-0079's three
1.50 m off it, ten metres apart along the face and so not yet reading as a step. A
later parcel closing that gap would have put a 0.70 m jog in a street wall the whole
project describes as one line.

This is the gate beside the two, asking the committed dataset instead of a run: it
takes the face line out of the committed plat, projects every front wall onto it, and
refuses a face that carries more than one.

## What is asserted, absolutely — there is no ratchet here

1. **One line per face.** Every record declaring `reconstruction.frontage` on a
   (block, face) stands with its front wall on one line, to 5 mm — the tolerance both
   generators already use, and for their reason: a placement is rounded to the
   millimetre before it is written.
2. **A record's stated setback is the line it stands on.** `setback_m` is a claim
   about geometry and this measures it, so a hand-edited coordinate is a failure here
   even on a face only one generator ever touched.
3. **A party wall is on the same line from both sides.** A record naming `abuts`
   stands on its target's line, INCLUDING a target that declares no frontage of its
   own — which is the case the two run-local gates structurally cannot reach, because
   the target belongs to another generator.

## Nothing is banked — and the one thing that was, was repaired rather than relaxed

`inf_butcher_market` was the exception (T-0104, then T-0182). `recon_1835_south_d3_013`
shares a party wall with it and stood 0.016 m proud of the row's line, because
`tools/generate_inferred_households.py` placed the butcher from a hand-authored
`center_local_enu_m` at bearing 0 where this face runs at 0.465 — not merely off the
line, not parallel to it. Sixteen millimetres was invisible, so it was banked BY NAME
and by size while the repair waited on its own ticket.

T-0182 made the repair: the household layer's two Lake-face buildings now take their
line, bearing and outward offset from the same committed block boundary this module
reads, the party wall closes to 0 mm, and the bank is gone rather than widened. There
is no allowance list here now, and a residual that cannot be repaired should be a
ticket and a red gate rather than a name in a dictionary — that is what the bank cost
to carry, and why it is not being kept warm for the next one.

## What is only reported

Every record whose footprint stands within three metres of a face line inside that
face's span while declaring no frontage at all. That census is how the butcher and
`inf_bakery_lake` were found — both of them on this same face, both from the
household layer, neither visible to any gate that reads declarations.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"

sys.path.insert(0, str(ROOT / "tools"))
from block_faces import face_frame, project  # noqa: E402

# The tolerance both generators' own frontage gates use, for the same reason.
TOL_M = 0.005

# How near a face a record may stand while declaring nothing, before the census
# reports it. Three metres is the separation rule the household layer already runs.
NEAR_M = 3.0



def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def world_polygon(phase: dict, origin: tuple[float, float]) -> list[tuple[float, float]]:
    """The footprint in the scene's local ENU frame, under the renderer's rotation."""
    pos = phase["position"]
    polygon = phase["footprint"]["polygon"]
    local_e = pos["utm_e"] - origin[0]
    local_n = pos["utm_n"] - origin[1]
    theta = math.radians(float(pos.get("rotation_deg") or 0.0))
    cos, sin = math.cos(theta), math.sin(theta)
    return [(local_e + u * cos + v * sin, local_n - u * sin + v * cos)
            for u, v in polygon]


def records(structures: Path = STRUCTURES) -> list[dict]:
    """Every committed record that has a footprint standing somewhere, flattened to
    its first phase — which is the phase every frontage run writes."""
    out = []
    for path in sorted(structures.glob("*.json")):
        doc = load(path)
        for phase in doc.get("phases", []):
            pos = phase.get("position") or {}
            poly = (phase.get("footprint") or {}).get("polygon")
            if pos.get("utm_e") is None or pos.get("utm_n") is None or not poly:
                continue
            out.append({
                "id": doc["id"],
                "phase": phase,
                "frontage": ((doc.get("reconstruction") or {}).get("frontage") or None),
            })
            break
    return out


def frames() -> dict[tuple[str, str], dict]:
    """Every face of every committed block, derived — this module authors no line."""
    blocks = load(LOTS)["blocks"]
    return {(b["id"], face): face_frame(b, face)
            for b in blocks for face in ("north", "south", "east", "west")}


def measure(recs: list[dict], origin: tuple[float, float],
            faces: dict[tuple[str, str], dict]) -> dict:
    """Front wall and span of every record, against every face it is near."""
    walls: dict[str, dict] = {}
    near: dict[tuple[str, str], list[dict]] = {}
    for rec in recs:
        world = world_polygon(rec["phase"], origin)
        rec["world"] = world
        for key, frame in faces.items():
            pr = [project(frame, p) for p in world]
            alongs = [a for a, _ in pr]
            offs = [o for _, o in pr]
            # the front wall is the one nearest the street: the largest outward offset
            row = {"id": rec["id"], "front": -max(offs),
                   "along": (min(alongs), max(alongs)), "frontage": rec["frontage"]}
            declared = rec["frontage"] or {}
            if (declared.get("block"), declared.get("face")) == key:
                walls[rec["id"]] = dict(row, face=key, declared=True)
            elif (-NEAR_M <= row["front"] <= NEAR_M
                  and min(alongs) < frame["length"] and max(alongs) > 0.0):
                near.setdefault(key, []).append(row)
    return {"walls": walls, "near": near}


def failures(measured: dict) -> list[str]:
    walls = measured["walls"]
    by_face: dict[tuple[str, str], list[dict]] = {}
    for row in walls.values():
        by_face.setdefault(row["face"], []).append(row)

    out: list[str] = []
    for key, rows in sorted(by_face.items()):
        lines = sorted({round(r["front"], 3) for r in rows})
        if round(max(lines) - min(lines), 3) > TOL_M:
            where = "; ".join(f"{r['id']} at {r['front']:.3f} m"
                              for r in sorted(rows, key=lambda r: r["front"]))
            out.append(f"{key[0]} {key[1]} face carries {len(lines)} street lines "
                       f"({', '.join(f'{v:.3f}' for v in lines)} m) — a street wall "
                       f"is one wall. {where}")
        for row in sorted(rows, key=lambda r: r["id"]):
            stated = float(row["frontage"]["setback_m"])
            if abs(row["front"] - stated) > TOL_M:
                out.append(f"{row['id']} states a {stated:.3f} m setback on the "
                           f"{key[1]} face of {key[0]} and its front wall stands "
                           f"{row['front']:.3f} m off that line")

    for row in sorted(walls.values(), key=lambda r: r["id"]):
        target = row["frontage"].get("abuts")
        if not target:
            continue
        other = walls.get(target)
        front = other["front"] if other else None
        if front is None:
            # the party wall's other half belongs to a layer that declares no
            # frontage, so measure it against THIS record's face
            for cand in measured["near"].get(row["face"], []):
                if cand["id"] == target:
                    front = cand["front"]
                    break
        if front is None:
            out.append(f"{row['id']} names a party wall with {target}, which stands "
                       f"nowhere near the {row['face'][1]} face of {row['face'][0]}")
            continue
        # to the millimetre, because that is the precision a placement is written at
        gap = round(abs(front - row["front"]), 3)
        if gap > TOL_M:
            out.append(f"{row['id']} shares a party wall with {target} and their "
                       f"front walls are {gap:.3f} m apart. One wall, from "
                       f"either side")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 when a face carries more than one street line")
    parser.add_argument("--quiet", action="store_true",
                        help="print the assertion and the failures, not the census")
    parser.add_argument("--self-test", action="store_true",
                        help="prove each assertion fires when it is broken")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    datum = load(DATA / "datum.json")
    origin = (float(datum["origin_utm_e"]), float(datum["origin_utm_n"]))
    measured = measure(records(), origin, frames())
    bad = failures(measured)

    walls = measured["walls"]
    by_face: dict[tuple[str, str], list[dict]] = {}
    for row in walls.values():
        by_face.setdefault(row["face"], []).append(row)

    if not args.quiet:
        for key, rows in sorted(by_face.items()):
            # to the millimetre, the precision every placement is written at, so the
            # census and the assertion above are reading the same numbers
            fronts = [round(r["front"], 3) for r in rows]
            spread = round(max(fronts) - min(fronts), 3)
            rows = sorted(rows, key=lambda r: r["along"][0])
            print(f"   {key[0]} {key[1]:<5} {len(rows)} record(s), front walls "
                  f"{min(fronts):.3f}–{max(fronts):.3f} m off the face "
                  f"(spread {spread * 1000:.0f} mm)")
            for row in rows:
                print(f"       {row['along'][0]:7.2f} – {row['along'][1]:6.2f} m along  "
                      f"front {row['front']:.3f} m   {row['id']}")
            for cand in sorted(measured["near"].get(key, []),
                               key=lambda r: r["along"][0]):
                print(f"       {cand['along'][0]:7.2f} – {cand['along'][1]:6.2f} m along  "
                      f"front {cand['front']:.3f} m   {cand['id']}  "
                      f"(declares no frontage — reported, not asserted)")

    if bad:
        print("\n   STREET LINE FAILURES")
        for line in bad:
            print(f"     - {line}")
        return 1 if args.gate else 0

    faces = len(by_face)
    print(f"   {len(walls)} frontage record(s) across {faces} block face(s), and every "
          f"face is one street line. Party walls close from both sides.")
    return 0


# ---------------------------------------------------------------------------
# self-test: each assertion, broken on purpose


def _synthetic() -> tuple[list[dict], tuple[float, float], dict]:
    """One square block, one north face, two records sharing a party wall on it."""
    block = {"id": "blk_test", "boundary_local_enu_m":
             [[0.0, 0.0], [40.0, 0.0], [40.0, -40.0], [0.0, -40.0]]}
    faces = {("blk_test", "north"): face_frame(block, "north")}

    def rec(rid, east, width, setback, abuts=None):
        return {"id": rid,
                "phase": {"position": {"utm_e": east, "utm_n": -setback - 6.0,
                                       "rotation_deg": 0.0},
                          "footprint": {"polygon": [[0, 0], [width, 0],
                                                    [width, 6.0], [0, 6.0]]}},
                "frontage": {"block": "blk_test", "face": "north",
                             "setback_m": setback, "abuts": abuts}}
    recs = [rec("a", 2.0, 6.0, 1.5), rec("b", 8.0, 6.0, 1.5, abuts="a")]
    return recs, (0.0, 0.0), faces


def _run(recs, origin, faces) -> list[str]:
    import copy
    return failures(measure(copy.deepcopy(recs), origin, faces))


def self_test() -> int:
    recs, origin, faces = _synthetic()
    checks: list[tuple[str, bool, str]] = []

    base = _run(recs, origin, faces)
    checks.append(("a face built on one line, with its party wall closed, passes",
                   not base, "; ".join(base) or "clean"))

    import copy
    two = copy.deepcopy(recs)
    two[1]["frontage"]["setback_m"] = 0.8
    two[1]["phase"]["position"]["utm_n"] = -0.8 - 6.0
    out = _run(two, origin, faces)
    checks.append(("a SECOND setback on the same face is caught",
                   any("street lines" in m for m in out), "; ".join(out) or "nothing"))

    moved = copy.deepcopy(recs)
    moved[0]["phase"]["position"]["utm_n"] = -1.9 - 6.0
    out = _run(moved, origin, faces)
    checks.append(("a record that does not stand on the setback it states is caught",
                   any("and its front wall stands" in m for m in out),
                   "; ".join(out) or "nothing"))

    # the case neither run-local gate can reach: the other half of the party wall
    # belongs to a layer that declares no frontage of its own
    outside = copy.deepcopy(recs)
    outside[0]["frontage"] = None
    outside[0]["phase"]["position"]["utm_n"] = -0.8 - 6.0
    out = _run(outside, origin, faces)
    checks.append(("a party wall whose other half declares no frontage is still "
                   "measured, and a jog in it is caught",
                   any("party wall" in m and "apart" in m for m in out),
                   "; ".join(out) or "nothing"))

    tol = copy.deepcopy(recs)
    tol[0]["phase"]["position"]["utm_n"] = -1.5 - 6.0 - 0.004
    out = _run(tol, origin, faces)
    checks.append(("a 4 mm reading is rounding, not a second line",
                   not out, "; ".join(out) or "clean"))

    # T-0182 retired the one banked residual, so the assertion is now that the pair it
    # was written for gets no allowance either: 16 mm is a failure under these exact
    # names, and it is the size the bank used to permit.
    unbanked = copy.deepcopy(recs)
    unbanked[0]["id"] = "inf_butcher_market"
    unbanked[0]["frontage"] = None
    unbanked[1]["id"] = "recon_1835_south_d3_013"
    unbanked[1]["frontage"]["abuts"] = "inf_butcher_market"
    unbanked[0]["phase"]["position"]["utm_n"] = -1.5 - 6.0 + 0.016
    out = _run(unbanked, origin, faces)
    checks.append(("the party wall T-0104 banked at 16 mm is no longer excused",
                   any("party wall" in m and "apart" in m for m in out),
                   "; ".join(out) or "nothing"))

    unbanked[0]["phase"]["position"]["utm_n"] = -1.5 - 6.0
    out = _run(unbanked, origin, faces)
    checks.append(("…and the same pair standing on one line is clean",
                   not out, "; ".join(out) or "clean"))

    ok = True
    for label, passed, detail in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  {label} — {detail}")
        ok &= passed
    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
