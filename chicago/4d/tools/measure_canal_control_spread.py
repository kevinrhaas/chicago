#!/usr/bin/env python3
"""What the queued Kinzie x Canal correction costs Canal Street's platted corridor.

    tools/measure_canal_control_spread.py              print both readings side by side
    tools/measure_canal_control_spread.py --check      the committed numbers re-derive
    tools/measure_canal_control_spread.py --self-test  break each input, require a red

T-0421, found by T-0009 on 2026-08-29 while deriving every street's platted corridor from
its committed control. Canal is the one street with more than one control point that does
not agree with itself: `lake_canal` +0.00 m, `randolph_canal` +0.09 m, `kinzie_canal`
-2.24 m off its own drawn centreline, a spread of 2.33 m. No rigid translation puts the
corridor on all three and re-DRAWING the line is what the owner's ruling of 2026-08-29
forbids, so `plat_corridors.control_offsets()` returns `disagree` and Canal's corridor stays
on the drawn line.

WHAT THIS MEASURES, AND WHY IT IS NOT A REPAIR. The 2.33 m is not a doubt about where Canal
ran. `data/traces/street_control.json` has said since 2026-08-10 that two of the five
OpenStreetMap nodes averaged into `kinzie_canal` are the KINZIE STREET BIKEWAY crossing
Canal, about 6 m north of the roadway, and that the three road nodes' own mean is the
reading the North Branch bridge and this street's drawn line both stand on. That second
coordinate is committed as `control.kinzie_canal.road_only_reading` (T-0421 put it there;
until then it lived in three paragraphs of prose and nothing could re-derive it).

So this tool runs `control_offsets()` twice against the SAME committed lines -- once as the
control table stands, once with `kinzie_canal` moved to its own `road_only_reading` -- and
reports the spread each way. Committed: 2.33 m. Road-only: 0.09 m.

NOTHING MOVES ON EITHER READING, and the tool exists to keep that true rather than to argue
for a change. 0.09 m is still wider than the 0.01 m `plat_corridors.QUOTED_M` quotes offsets
to, so the verdict is `disagree` both ways and the corridor sits where it sat. What the
measurement settles is the ticket's question: whether Canal's block grid and its corridor
answer different questions (they do not -- the drawn line reproduces all three of its
control points to 9 cm) or whether the street is really 2.33 m of undecided (it is not --
that figure is this control entry's cycle path).

It also holds the bridge to the same field: `north_branch_bridge` declares
`centreline.control_variance_m: 2.93`, and that 2.93 m is exactly the northing between
`kinzie_canal` and its `road_only_reading`. Before this, the bridge's declared variance and
the control's queued correction were two prose numbers that happened to agree.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plat_corridors  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONTROL = ROOT / "data" / "traces" / "street_control.json"
STREETS = ROOT / "data" / "streets" / "1835.json"
BRIDGE = ROOT / "data" / "structures" / "north_branch_bridge.json"

STREET = "canal"
POINT = "kinzie_canal"

# The committed answers. Re-derived below from the two files on every run; stated here so
# that a change to either of them is a RED with a number in it rather than a silent move.
COMMITTED_SPREAD_M = 2.33
ROAD_ONLY_SPREAD_M = 0.09
BRIDGE_VARIANCE_M = 2.93
TOL_M = 0.01

# T-0421's own table, per control point, both readings. The SPREAD alone is invariant
# under a rigid translation of the drawn line, so a gate that checked only the spread
# would sleep through Canal being moved bodily — which is the one edit the ruling of
# 2026-08-29 is about. These are the offsets themselves.
COMMITTED_OFFSETS_M = {"lake_canal": 0.00, "randolph_canal": 0.09, "kinzie_canal": -2.24}
ROAD_ONLY_OFFSETS_M = {"lake_canal": 0.00, "randolph_canal": 0.09, "kinzie_canal": 0.01}


def _load(path):
    return json.loads(path.read_text())


def _spreads(control, streets):
    """Canal's control spread as committed, and with kinzie_canal on its road-only mean."""
    lines = plat_corridors.street_lines(streets)
    as_committed = plat_corridors.control_offsets(lines=lines, control=control)[STREET]

    road_only = copy.deepcopy(control)
    reading = road_only["control"][POINT]["road_only_reading"]
    road_only["control"][POINT]["utm_e"] = float(reading["utm_e"])
    road_only["control"][POINT]["utm_n"] = float(reading["utm_n"])
    corrected = plat_corridors.control_offsets(lines=lines, control=road_only)[STREET]
    return as_committed, corrected


def _bridge_variance(control, bridge):
    """The northing the bridge's declared variance is the size of."""
    point = control["control"][POINT]
    reading = point["road_only_reading"]
    return abs(float(point["utm_n"]) - float(reading["utm_n"]))


def _declared_variance(bridge):
    for phase in bridge["phases"]:
        derivation = (phase.get("position") or {}).get("derivation") or {}
        centreline = derivation.get("centreline") or {}
        if "control_variance_m" in centreline:
            return float(centreline["control_variance_m"]), derivation.get("control")
    return None, None


def _report(control, streets, bridge):
    bad = []
    as_committed, corrected = _spreads(control, streets)

    for label, got, want in (
        ("as committed", as_committed["spread_m"], COMMITTED_SPREAD_M),
        ("road-only", corrected["spread_m"], ROAD_ONLY_SPREAD_M),
    ):
        if got is None or abs(got - want) > TOL_M:
            bad.append(f"{STREET}'s control spread {label} is {got} m, not the "
                       f"committed {want} m")

    for label, block, want in (
        ("as committed", as_committed, COMMITTED_OFFSETS_M),
        ("road-only", corrected, ROAD_ONLY_OFFSETS_M),
    ):
        got = {p["control"]: p["offset_m"] for p in block["points"]}
        if set(got) != set(want):
            bad.append(f"{STREET} is controlled by {sorted(got)} {label}, not "
                       f"{sorted(want)}")
        for pid in sorted(set(got) & set(want)):
            if abs(got[pid] - want[pid]) > TOL_M:
                bad.append(f"{STREET} stands {got[pid]:+.2f} m off {pid} {label}, not the "
                           f"committed {want[pid]:+.2f} m")

    # The corridor does not move on either reading, and this is the assertion that says so.
    for label, block in (("as committed", as_committed), ("road-only", corrected)):
        if block["verdict"] != "disagree":
            bad.append(f"{STREET}'s verdict {label} is `{block['verdict']}`, not `disagree` "
                       f"— the corridor would move, which T-0421 says nothing does")
        if abs(float(block["offset_m"])) > TOL_M:
            bad.append(f"{STREET}'s corridor is translated {block['offset_m']} m "
                       f"{label}; it should stay on the drawn line")

    measured = _bridge_variance(control, bridge)
    declared, stands_on = _declared_variance(bridge)
    if declared is None:
        bad.append("north_branch_bridge declares no centreline.control_variance_m")
    elif abs(measured - declared) > TOL_M:
        bad.append(f"north_branch_bridge declares control_variance_m {declared} m, but "
                   f"{POINT} stands {measured:.2f} m north of its own road_only_reading")
    elif abs(declared - BRIDGE_VARIANCE_M) > TOL_M:
        bad.append(f"the bridge's declared variance is {declared} m, not the "
                   f"committed {BRIDGE_VARIANCE_M} m")
    if declared is not None and stands_on != POINT:
        bad.append(f"north_branch_bridge's centreline stands on `{stands_on}`, not `{POINT}`")

    return bad, as_committed, corrected, measured


def _print(as_committed, corrected, measured):
    print(f"{STREET}: the platted corridor's control, both readings of {POINT}")
    print()
    print(f"  {'control point':18s} {'as committed':>14s} {'road-only':>12s}")
    by_id = {p["control"]: p for p in corrected["points"]}
    for point in as_committed["points"]:
        pid = point["control"]
        print(f"  {pid:18s} {point['offset_m']:+13.2f} m "
              f"{by_id[pid]['offset_m']:+11.2f} m")
    print(f"  {'spread':18s} {as_committed['spread_m']:13.2f} m "
          f"{corrected['spread_m']:11.2f} m")
    print(f"  {'verdict':18s} {as_committed['verdict']:>15s} "
          f"{corrected['verdict']:>13s}")
    print()
    print(f"  the queued correction moves {POINT} {measured:.2f} m south, which is the "
          f"variance\n  north_branch_bridge declares; the corridor does not move on either "
          f"reading.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="the committed numbers re-derive from the committed data")
    ap.add_argument("--self-test", dest="self_test", action="store_true",
                    help="break each input in turn and require this tool to go red")
    a = ap.parse_args()

    control, streets, bridge = _load(CONTROL), _load(STREETS), _load(BRIDGE)

    if a.self_test:
        return self_test(control, streets, bridge)

    bad, as_committed, corrected, measured = _report(control, streets, bridge)
    if a.check:
        for line in bad:
            print("RED  " + line)
        print(f"canal control spread: {as_committed['spread_m']} m as committed, "
              f"{corrected['spread_m']} m on {POINT}'s road_only_reading; corridor "
              f"unmoved on both"
              if not bad else f"{len(bad)} disagreement(s)")
        return 1 if bad else 0

    _print(as_committed, corrected, measured)
    return 0


def self_test(control, streets, bridge):
    """Each break below MUST produce a red. A gate nobody has broken is not a gate."""
    ok = True

    def expect(label, ctl, sts, brg):
        nonlocal ok
        bad, *_ = _report(ctl, sts, brg)
        print(("PASS " if bad else "FAIL ") + label + (f" — {bad[0]}" if bad else ""))
        ok = ok and bool(bad)

    # 1. The road-only reading drifts: the two spreads stop being 2.33 and 0.09.
    broken = copy.deepcopy(control)
    broken["control"][POINT]["road_only_reading"]["utm_e"] += 1.0
    expect("a moved road_only_reading easting is caught", broken, streets, bridge)

    # 2. The road-only northing drifts away from the bridge's declared variance.
    broken = copy.deepcopy(control)
    broken["control"][POINT]["road_only_reading"]["utm_n"] += 0.5
    expect("a road_only_reading northing the bridge no longer answers for is caught",
           broken, streets, bridge)

    # 3. The control point itself moves, which is the queued correction being applied
    #    silently — the whole thing this entry says costs a re-bake.
    broken = copy.deepcopy(control)
    broken["control"][POINT]["utm_e"] += 0.5
    expect("a moved kinzie_canal control point is caught", broken, streets, bridge)

    # 4. Canal's drawn line moves.
    broken = copy.deepcopy(streets)
    for street in broken["streets"]:
        if street["id"] == STREET:
            street["path_local_enu_m"] = [[e + 0.5, n] for e, n in
                                          street["path_local_enu_m"]]
    expect("a moved canal centreline is caught", control, broken, bridge)

    # 5. The bridge stops declaring its variance.
    broken = copy.deepcopy(bridge)
    for phase in broken["phases"]:
        derivation = (phase.get("position") or {}).get("derivation") or {}
        (derivation.get("centreline") or {}).pop("control_variance_m", None)
    expect("an undeclared bridge variance is caught", control, streets, broken)

    # And the unbroken tree must be green, or every PASS above is worthless.
    bad, *_ = _report(control, streets, bridge)
    print(("PASS " if not bad else "FAIL ") + "the committed tree is green" +
          (f" — {bad[0]}" if bad else ""))
    ok = ok and not bad
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
