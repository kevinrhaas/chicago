#!/usr/bin/env python3
"""The figures T-1460 asks the owner about, pinned so they cannot drift while he decides.

    tools/measure_west_swale_corridors.py             print the reading
    tools/measure_west_swale_corridors.py --gate      exit 1 if the reading has moved
    tools/measure_west_swale_corridors.py --self-test prove each assertion still fires

THE QUESTION IS NOT THIS FILE'S TO ANSWER. The West recipe's fourth terrain rule
(`terrain_and_hydrology_gate.rules[3]`) says *"Do not place a roof in the two
conjectural west-prairie swales until their alignments are reviewed after the west
terrain extension; move the roof rather than flattening the swale."* T-1416 made the
extension, T-1444 took the reading, and the reading does not say what the rule
assumed: the rule's remedy assumes the swale is the fixed thing, and the swale is the
CONJECTURAL thing — `confidence: reconstructed`, `sources: []`, and T-0795 walked the
whole Wright 1834 sheet and it draws no watercourse anywhere on the West Division
prairie. Which way that fork goes is the owner's, and T-1460 is where he is asked.

WHAT THIS DOES INSTEAD is what `measure_corridor_strip.py` does for T-0419's fork: it
pins the figures the question is asked ABOUT. A question that waits on a person waits
in real time — T-1460 was filed 2026-09-20 — and in that time the town goes on being
built around it. Its distances had ALREADY moved before anything measured them: the
ticket states recon_1835_west_005 at 22.7 m and recon_1835_west_011 at 26.4 m, and
they now read 25.5 m and 24.5 m, because T-1545 and T-1570 re-seated West Division
roofs off platted street corridors and no reader joined those moves to this corridor.
Nothing was broken by that — the eight are still the eight — but the owner would have
been deciding on numbers that were quietly two and a half metres stale, and nothing
anywhere would have said so.

WHAT IS ASSERTED, and each one is a way the question can go stale under him:

 1. THE HEADS STILL BEGIN NOWHERE. Each alignment's head sits at E -320.0 m, which was
    the west wall of the modelled field when the lines were drawn. Since T-1416 the
    field reaches E -705.0 m, so each head now stands `HEAD_GAP_M` inside the ground,
    in open modelled prairie. That gap IS the finding — a drain ending at the edge of
    the model reads as a drain leaving the model, and a drain beginning 385 m inside it
    reads as nothing at all. If the field is extended again, or an alignment redrawn,
    this number moves and the question has changed.
 2. THE CORRIDOR HOLDS THE SAME EIGHT ROOFS, at the same distances. Membership is
    already frozen in `generate_west_infill.SWALE_CORRIDOR_OCCUPANTS` and that gate
    fires on an arrival or a departure. It does NOT fire on a roof that stays inside
    and moves, which is exactly what happened twice. The distances are pinned here.
 3. SWALE_B'S CORRIDOR IS STILL EMPTY. Only one of the two alignments is in conflict
    with anything, and that asymmetry is half the reason the fork is worth asking
    about. A roof arriving in swale_b's corridor makes it a different question.
 4. NO ROOF IS STANDING IN A HOLE. The cut is 0.75 ft over a 30 m half-width — about
    0.008 m per metre — so every one of the eight passes the generator's own 0.35 m
    relief-across-footprint contract and its dry-ground test with room to spare. THIS
    IS WHAT MAKES T-1460 A PROVENANCE QUESTION AND NOT A GEOMETRY DEFECT, and it is
    the assertion that would change its character if it ever stopped being true.
 5. THE TWO READERS AGREE. This reading and the generator's frozen set are two readers
    of one fact, and they are required to say the same thing.

Every figure below is read from the committed tree — `data/terrain/epochs/
e1834_harbor_cut/terrain_spec.json`, its heightfield, and the 55 committed
`recon_1835_west_*` records. The only numbers authored here are the pinned reading and
its tolerances, which is what a pin is.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

EPOCH = "e1834_harbor_cut"
PREFIX = "recon_1835_west_"

# The heads were drawn on the old west wall; the field has since gone past it (T-1416).
HEAD_E_M = -320.0
HEAD_GAP_M = 385.0
HEAD_GAP_TOL_M = 1.0

# The reading, re-taken 2026-09-29 against the committed tree. Footprint-corner distance
# in metres to `west_prairie_swale_a`'s centreline, which carries a 30 m half-width.
#
# THE TOLERANCE IS 2.0 m AND IT IS NOT ROUNDING. The recipe states +/-20 m of working
# uncertainty on its own layout controls and this parcel slides slots by up to 12.25 m to
# clear a platted street, so a re-seat is ordinary and legitimate. What is NOT ordinary is
# a re-seat landing on an open owner question without anybody noticing, which is what
# 2.0 m catches: under it nothing has really moved; over it, the figures T-1460 quotes are
# no longer the figures, and the fix is to re-measure, re-pin HERE, and say so on the
# ticket. A red step is not a fault in the town. It is the question needing a new reading.
PINNED_M = {
    "recon_1835_west_002": 3.20,
    "recon_1835_west_003": 8.93,
    "recon_1835_west_012": 12.25,
    "recon_1835_west_013": 14.30,
    "recon_1835_west_009": 16.40,
    "recon_1835_west_001": 19.22,
    "recon_1835_west_011": 24.52,
    "recon_1835_west_005": 25.46,
}
DISTANCE_TOL_M = 2.0

# The generator's own contracts, restated here only to report the margin each roof keeps.
MAX_RELIEF_M = 0.35
MIN_DRY_M = -0.10


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def point_segment_distance(px: float, py: float,
                           a: tuple[float, float], b: tuple[float, float]) -> float:
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    span = dx * dx + dy * dy
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def polyline_distance(pt: tuple[float, float], line: list) -> float:
    return min(point_segment_distance(pt[0], pt[1], a, b) for a, b in zip(line, line[1:]))


def world_polygon(record: dict, datum: dict) -> list[tuple[float, float]]:
    """The footprint in local ENU metres. `rotation_deg` is a COMPASS BEARING.

    This is `generate_west_infill.world_polygon`'s convention and it must stay that
    convention: turning the rectangle the other way puts recon_1835_west_005 (bearing
    91 deg) 11 m further from the centreline and drops it out of the corridor, which is
    a reading of nothing at all.
    """
    phase = record["phases"][0]
    pos, poly = phase["position"], phase["footprint"]["polygon"]
    theta = math.radians(float(pos.get("rotation_deg") or 0))
    cos, sin = math.cos(theta), math.sin(theta)
    e0 = float(pos["utm_e"]) - float(datum["origin_utm_e"])
    n0 = float(pos["utm_n"]) - float(datum["origin_utm_n"])
    return [(e0 + u * cos + v * sin, n0 - u * sin + v * cos) for u, v in poly]


def west_records() -> list[dict]:
    return [load(p) for p in sorted((DATA / "structures").glob(f"{PREFIX}*.json"))]


def west_prairie_swales(spec: dict) -> list[dict]:
    return [s for s in spec.get("swales", []) if s["id"].startswith("west_prairie_")]


def take_reading(spec: dict, records: list[dict], datum: dict, field) -> dict:
    grid = spec["grid"]
    swales = west_prairie_swales(spec)
    polygons = [(r["id"], world_polygon(r, datum)) for r in records]

    heads = {}
    for swale in swales:
        head = [float(v) for v in swale["line"][0]]
        heads[swale["id"]] = {
            "head_e_m": round(head[0], 3),
            "head_n_m": round(head[1], 3),
            "gap_from_west_edge_m": round(head[0] - float(grid["e_min_m"]), 3),
            "ground_at_head_m": (round(float(field.height(*head)), 3)
                                 if field is not None and field.covers(*head) else None),
        }

    corridors = {}
    for swale in swales:
        line = [(float(e), float(n)) for e, n in swale["line"]]
        half = float(swale["half_width_m"])
        inside = {}
        for sid, poly in polygons:
            d = min(polyline_distance(pt, line) for pt in poly)
            if d <= half:
                inside[sid] = round(d, 2)
        corridors[swale["id"]] = {
            "half_width_m": half,
            "depth_ft": float(swale["depth_ft"]),
            "confidence": swale.get("confidence"),
            "sources": swale.get("sources") or [],
            "occupants": dict(sorted(inside.items(), key=lambda kv: kv[1])),
        }

    standing = {}
    if field is not None:
        for sid, poly in polygons:
            if sid not in corridors["west_prairie_swale_a"]["occupants"]:
                continue
            heights = [float(field.height(e, n)) for e, n in poly]
            standing[sid] = {"relief_m": round(max(heights) - min(heights), 3),
                             "lowest_m": round(min(heights), 3)}

    return {"epoch": EPOCH, "west_edge_m": float(grid["e_min_m"]),
            "records_measured": len(records), "heads": heads,
            "corridors": corridors, "standing": standing}


def assertions(reading: dict, frozen: set | None) -> list[str]:
    """Every way the figures T-1460 asks about can have moved. Empty means none have."""
    problems: list[str] = []

    # --- 1: the heads still begin nowhere ---------------------------------
    for sid, head in sorted(reading["heads"].items()):
        if abs(head["head_e_m"] - HEAD_E_M) > HEAD_GAP_TOL_M:
            problems.append(
                f"{sid}'s head has moved off the old west wall: E {head['head_e_m']:g} m, "
                f"not the E {HEAD_E_M:g} m T-1460 measured. The alignment has been "
                f"redrawn — re-take the reading and re-pin it here.")
        if abs(head["gap_from_west_edge_m"] - HEAD_GAP_M) > HEAD_GAP_TOL_M:
            problems.append(
                f"{sid} now begins {head['gap_from_west_edge_m']:g} m inside the west "
                f"edge of the modelled ground, not the {HEAD_GAP_M:g} m T-1460 measured. "
                f"Either the field moved or the line did; T-1460's first finding is "
                f"about this number and it is no longer that number.")

    # --- 2: the same eight roofs, at the same distances --------------------
    occupants = reading["corridors"]["west_prairie_swale_a"]["occupants"]
    arrived = sorted(set(occupants) - set(PINNED_M))
    left = sorted(set(PINNED_M) - set(occupants))
    if arrived:
        problems.append(
            f"west_prairie_swale_a's corridor has gained {', '.join(arrived)}. The "
            f"corridor may not quietly acquire a roof while T-1460 is open.")
    if left:
        problems.append(
            f"west_prairie_swale_a's corridor has lost {', '.join(left)}. That is a "
            f"release and it changes the price of every option T-1460 offers.")
    for sid, pinned in sorted(PINNED_M.items(), key=lambda kv: kv[1]):
        now = occupants.get(sid)
        if now is None:
            continue
        if abs(now - pinned) > DISTANCE_TOL_M:
            problems.append(
                f"{sid} stands {now:.2f} m from the centreline; T-1460 is being asked "
                f"about {pinned:.2f} m. It has been re-seated by "
                f"{abs(now - pinned):.2f} m — re-pin the reading and tell the ticket.")

    # --- 3: swale_b's corridor is still empty ------------------------------
    b = reading["corridors"].get("west_prairie_swale_b", {}).get("occupants") or {}
    if b:
        problems.append(
            f"west_prairie_swale_b's corridor is no longer empty: {', '.join(sorted(b))}. "
            f"T-1460 asks about one alignment in conflict and one clear of everything; "
            f"with both occupied it is a different question.")

    # --- 4: no roof is standing in a hole ----------------------------------
    for sid, s in sorted(reading["standing"].items()):
        if s["relief_m"] > MAX_RELIEF_M:
            problems.append(
                f"{sid} now stands across {s['relief_m']:.3f} m of relief, over the "
                f"{MAX_RELIEF_M:g} m contract: the swale has stopped being a shallow "
                f"drain under this roof and T-1460 is no longer only a provenance "
                f"question.")
        if s["lowest_m"] < MIN_DRY_M:
            problems.append(
                f"{sid} reaches {s['lowest_m']:.3f} m, below the {MIN_DRY_M:g} m "
                f"dry-ground floor: it is standing in water, not in a swale corridor.")

    # --- 5: the two readers agree ------------------------------------------
    if frozen is not None:
        mine = {(sid, "west_prairie_swale_a") for sid in occupants}
        mine |= {(sid, "west_prairie_swale_b") for sid in b}
        if mine != frozen:
            problems.append(
                f"this reading and generate_west_infill.SWALE_CORRIDOR_OCCUPANTS "
                f"disagree about who stands in the corridors: "
                f"{sorted(mine ^ frozen)}. Two readers of one fact must say one thing.")
    return problems


def frozen_set():
    try:
        from generate_west_infill import SWALE_CORRIDOR_OCCUPANTS  # noqa: PLC0415
    except Exception:                                              # noqa: BLE001
        return None
    return set(SWALE_CORRIDOR_OCCUPANTS)


def heightfield():
    try:
        from heightfield import Heightfield  # noqa: PLC0415
    except Exception:                        # noqa: BLE001
        return None
    return Heightfield.load(DATA / "terrain" / "epochs" / EPOCH)


def report(reading: dict, problems: list[str]) -> None:
    print(f"west-prairie swale corridors, epoch {reading['epoch']}, "
          f"{reading['records_measured']} West Division records read")
    print(f"  the modelled ground's west edge: E {reading['west_edge_m']:g} m")
    for sid, head in sorted(reading["heads"].items()):
        ground = ("—" if head["ground_at_head_m"] is None
                  else f"{head['ground_at_head_m']:+.3f} m")
        print(f"  {sid}: head E {head['head_e_m']:g} N {head['head_n_m']:g}, "
              f"{head['gap_from_west_edge_m']:g} m inside the west edge, "
              f"ground there {ground}")
    for sid, c in sorted(reading["corridors"].items()):
        src = ", ".join(c["sources"]) or "no source"
        print(f"  {sid}: {c['half_width_m']:g} m half-width, {c['depth_ft']:g} ft deep, "
              f"{c['confidence']} ({src}) — {len(c['occupants'])} roof(s) inside")
        for rid, d in c["occupants"].items():
            pin = PINNED_M.get(rid)
            drift = "" if pin is None else f"  (pinned {pin:.2f}, {d - pin:+.2f})"
            stand = reading["standing"].get(rid)
            relief = "" if stand is None else f"  relief {stand['relief_m']:.3f} m"
            print(f"      {rid}  {d:.2f} m{drift}{relief}")
    if reading["standing"]:
        worst = max(s["relief_m"] for s in reading["standing"].values())
        print(f"  deepest relief across any occupant's footprint: {worst:.3f} m "
              f"of the {MAX_RELIEF_M:g} m contract — no roof is standing in a hole")
    for p in problems:
        print(f"  FAIL {p}")
    print("  the reading T-1460 is asked about has not moved" if not problems
          else f"  {len(problems)} figure(s) have moved under an open owner question")


def self_test() -> int:
    """Break each assertion and prove it fires. No committed file is touched."""
    import copy  # noqa: PLC0415
    base = {
        "epoch": EPOCH, "west_edge_m": -705.0, "records_measured": 55,
        "heads": {"west_prairie_swale_a": {"head_e_m": -320.0, "head_n_m": -120.0,
                                           "gap_from_west_edge_m": 385.0,
                                           "ground_at_head_m": 1.2},
                  "west_prairie_swale_b": {"head_e_m": -320.0, "head_n_m": 200.0,
                                           "gap_from_west_edge_m": 385.0,
                                           "ground_at_head_m": 1.3}},
        "corridors": {
            "west_prairie_swale_a": {"half_width_m": 30.0, "depth_ft": 0.75,
                                     "confidence": "reconstructed", "sources": [],
                                     "occupants": {k: v for k, v in PINNED_M.items()}},
            "west_prairie_swale_b": {"half_width_m": 26.0, "depth_ft": 0.6,
                                     "confidence": "reconstructed", "sources": [],
                                     "occupants": {}}},
        "standing": {sid: {"relief_m": 0.08, "lowest_m": 0.9} for sid in PINNED_M},
    }
    frozen = {(sid, "west_prairie_swale_a") for sid in PINNED_M}
    ok, fails = 0, 0

    def check(name: str, condition: bool) -> None:
        nonlocal ok, fails
        if condition:
            ok += 1
        else:
            fails += 1
            print(f"  SELF-TEST FAIL {name}")

    check("the unbroken reading raises nothing", not assertions(base, frozen))

    b = copy.deepcopy(base)
    b["heads"]["west_prairie_swale_a"]["head_e_m"] = -705.0
    b["heads"]["west_prairie_swale_a"]["gap_from_west_edge_m"] = 0.0
    check("a redrawn head is caught", len(assertions(b, frozen)) >= 2)

    b = copy.deepcopy(base)
    b["heads"]["west_prairie_swale_b"]["gap_from_west_edge_m"] = 700.0
    check("a field extended further west is caught", assertions(b, frozen))

    b = copy.deepcopy(base)
    b["corridors"]["west_prairie_swale_a"]["occupants"]["recon_1835_west_004"] = 28.0
    check("a ninth roof arriving is caught", assertions(b, frozen))

    b = copy.deepcopy(base)
    del b["corridors"]["west_prairie_swale_a"]["occupants"]["recon_1835_west_005"]
    check("one of the eight leaving is caught", assertions(b, frozen))

    b = copy.deepcopy(base)
    b["corridors"]["west_prairie_swale_a"]["occupants"]["recon_1835_west_002"] = 9.0
    check("a roof re-seated inside the corridor is caught",
          any("re-seated" in p for p in assertions(b, frozen)))

    b = copy.deepcopy(base)
    b["corridors"]["west_prairie_swale_a"]["occupants"]["recon_1835_west_002"] = 4.5
    check("a re-seat inside the tolerance is not caught", not assertions(b, frozen))

    b = copy.deepcopy(base)
    b["corridors"]["west_prairie_swale_b"]["occupants"]["recon_1835_west_029"] = 20.0
    check("a roof arriving in swale_b is caught",
          any("swale_b" in p for p in assertions(b, frozen)))

    b = copy.deepcopy(base)
    b["standing"]["recon_1835_west_002"]["relief_m"] = 0.60
    check("a roof that starts standing in a hole is caught",
          any("relief" in p for p in assertions(b, frozen)))

    b = copy.deepcopy(base)
    b["standing"]["recon_1835_west_002"]["lowest_m"] = -0.40
    check("a roof standing in water is caught",
          any("dry-ground" in p for p in assertions(b, frozen)))

    check("the two readers disagreeing is caught",
          any("disagree" in p for p in assertions(base, frozen | {("x", "y")})))
    check("a missing generator import does not invent a disagreement",
          not assertions(base, None))

    print(f"  self-test: {ok} passed, {fails} failed")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any figure T-1460 asks about has moved")
    ap.add_argument("--self-test", action="store_true",
                    help="prove each assertion still fires when broken")
    ap.add_argument("--json", action="store_true", help="print the reading as JSON")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    spec = load(DATA / "terrain" / "epochs" / EPOCH / "terrain_spec.json")
    field = heightfield()
    reading = take_reading(spec, west_records(), load(DATA / "datum.json"), field)
    problems = assertions(reading, frozen_set())

    if args.json:
        print(json.dumps({"reading": reading, "problems": problems}, indent=2))
    else:
        report(reading, problems)
    return 1 if (args.gate and problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
