#!/usr/bin/env python3
"""The north bank has no platted corridor, so its frontages are measured off the TRACK.

T-0947. Two reconciliations of one ruling (PRs #974 and #975, both written 2026-09-06)
put the Steamboat Hotel 36.79 m apart, and both were green. They could both be green
because the rule each applied lived in a building's own `position.note` and nothing
re-computed either one: `validate.py --stale` asks whether a mesh matches the record it
was baked from, not whether a record matches the rule it says it follows.

## What the rule IS, and where it already was

North of the river this project's placements do not offset from the platted module. They
offset from the street AS DRAWN, and the arithmetic is stated four times over in the
Dearborn sheds' own notes:

    North Water Street's travelled track, data/streets/1835.json, `track_width_m` 6.0:
    ... its north edge is 3.00 m north of [the drawn centreline]. The front wall is set
    2.00 m back from that edge — 5.00 m from the centreline, leaving the front wall
    2.00 m clear of the drawn ribbon

`KERB` is read from the street record's own `track_width_m`, so a street re-drawn there
re-derives here in the same commit; `CLEARANCE_M` is the 2.00 m those notes state. Their
sum is the frontage line, and `docs/RESEARCH/street_module_1830.md` § 11 is where the
rule is now argued rather than repeated per building.

## Why not the platted module

`data/traces/street_control.json` applies the 80 ft Thompson module town-wide to Lake,
Market, Canal, Randolph and Kinzie. Its `measured` block records eleven corridors read
off the two 1834 sheets, and every one of them is in the Original Town or the West
Division — **not one north-bank corridor has ever been read**. `tools/plat_corridors.py`
agrees by construction: `generate_plat_lots.EW_STREETS` and `NS_STREETS` name no
north-bank street, so `north_water` and `kinzie` have no corridor ring and no record has
ever been reported lapping one. Half a module a street is not known to carry is not a
frontage rule; it is a number borrowed from the other side of the river.

## What this gate holds, and it is a ratchet and not a bar

Every committed building phase whose street face stands within `BAND_M` of the committed
`north_water` centreline is measured, and each falls into one of three verdicts:

* **on_rule** — the face reproduces `SETBACK_M` to `TOL_M`. These may not drift.
* **exception** — a record that stands somewhere else for a reason the baseline names.
  Each is held to its own committed setback within `EXCEPTION_TOL_M`.
* **unbaselined** — a north-bank frontage that is neither. The gate FAILS on one, which
  is the assertion T-0947 wanted: a new answer to this question cannot land silently.

Five of the exceptions are buildings drawn INSIDE the drawn track. That is a real fault
of this dataset and it is recorded rather than repaired here — these are documented
placements whose coordinate comes from a corner or a source, and a position with a source
outranks a ribbon this project traced. `measure_corridor_intrusion` states the same rule
for the platted grid.

    tools/measure_north_bank_frontage.py                 the table
    tools/measure_north_bank_frontage.py --gate          the ratchet check.sh runs
    tools/measure_north_bank_frontage.py --self-test     move a roof and watch it fire
    tools/measure_north_bank_frontage.py --write-baseline only to record a repair
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from measure_corridor_intrusion import is_street_furniture  # noqa: E402
from measure_frontage_fabric import world_polygon  # noqa: E402
from plat_occupancy import layer_of_record  # noqa: E402

DATA = ROOT / "data"
BASELINE = ROOT / "tools" / "north_bank_frontage_baseline.json"

STREET_ID = "north_water"
# 2.00 m is the clearance the north-bank placements state beyond the drawn kerb; the kerb
# itself is half the street record's own `track_width_m` and is never written down here.
CLEARANCE_M = 2.00
# The band that counts as "a frontage on this street". 25 m is not a new number: it is
# `tools/fronting_street.FRONTAGE_BAND_M`, set by T-A13/T-A14 and quoted by every block
# parcel since.
BAND_M = 25.0
# 0.20 m, not a tighter figure, and the reason is the street rather than the placement:
# the face is measured to the nearest point of a POLYLINE, which at a vertex is a
# corner-to-corner distance and not the perpendicular the rule is stated in. The four
# Dearborn sheds, all placed by the rule, read 4.85-5.05 m for exactly that reason.
TOL_M = 0.20
EXCEPTION_TOL_M = 0.25
SAMPLE_M = 0.25


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def origin() -> tuple[float, float]:
    d = load(DATA / "datum.json")
    return float(d["origin_utm_e"]), float(d["origin_utm_n"])


def street() -> dict:
    for s in load(DATA / "streets" / "1835.json")["streets"]:
        if s["id"] == STREET_ID:
            return s
    raise SystemExit(f"no committed street {STREET_ID}")


def setback_m(track_width_m: float) -> float:
    """The frontage line: the drawn kerb plus the stated clearance."""
    return track_width_m / 2.0 + CLEARANCE_M


def _point_to_segment(p, a, b) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    span = dx * dx + dy * dy
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / span))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_to_line(p, path) -> float:
    return min(_point_to_segment(p, path[i], path[i + 1]) for i in range(len(path) - 1))


def sampled(polygon, pitch: float = SAMPLE_M):
    """A polygon's vertices plus points along its edges, so a long wall cannot slip past."""
    out = []
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(1, int(length / pitch))
        for j in range(steps):
            out.append((a[0] + (b[0] - a[0]) * j / steps, a[1] + (b[1] - a[1]) * j / steps))
    return out


def frontages(overrides: dict | None = None) -> list[dict]:
    """Every committed building phase whose face stands within BAND_M of the street."""
    o = origin()
    path = street()["path_local_enu_m"]
    rows = []
    for f in sorted((DATA / "structures").glob("*.json")):
        record = load(f)
        for phase in record.get("phases", []):
            pos = phase.get("position") or {}
            if pos.get("utm_e") is None or not (phase.get("footprint") or {}).get("polygon"):
                continue
            # A bridge deck lying in a street is the bridge doing its job — the same
            # reading `measure_corridor_intrusion` takes of the platted grid.
            if is_street_furniture(record):
                continue
            key = f"{record['id']}__{phase['id']}"
            if overrides and key in overrides:
                phase = json.loads(json.dumps(phase))
                phase["position"]["utm_e"], phase["position"]["utm_n"] = overrides[key]
            face = min(point_to_line(q, path) for q in sampled(world_polygon(phase, o)))
            if face > BAND_M:
                continue
            rows.append({"key": key, "id": record["id"], "phase": phase["id"],
                         "layer": layer_of_record(record), "face_m": round(face, 3)})
    rows.sort(key=lambda r: r["face_m"])
    return rows


def verdicts(baseline: dict, overrides: dict | None = None) -> list[dict]:
    rule = setback_m(float(street()["track_width_m"]))
    on_rule = set(baseline["on_rule"])
    exceptions = baseline["exceptions"]
    out = []
    for row in frontages(overrides):
        row["rule_m"] = round(rule, 3)
        if row["key"] in on_rule:
            row["verdict"] = "on_rule"
            row["drift_m"] = round(row["face_m"] - rule, 3)
            row["ok"] = abs(row["face_m"] - rule) <= TOL_M
        elif row["key"] in exceptions:
            held = float(exceptions[row["key"]]["face_m"])
            row["verdict"] = "exception"
            row["drift_m"] = round(row["face_m"] - held, 3)
            row["ok"] = abs(row["face_m"] - held) <= EXCEPTION_TOL_M
            row["reason"] = exceptions[row["key"]]["reason"]
        else:
            row["verdict"] = "unbaselined"
            row["drift_m"] = None
            row["ok"] = False
        out.append(row)
    return out


def table(rows: list[dict]) -> str:
    rule = rows[0]["rule_m"] if rows else setback_m(float(street()["track_width_m"]))
    lines = [f"North Water Street frontages — the rule is {rule:.2f} m from the committed "
             f"centreline (kerb {float(street()['track_width_m'])/2:.2f} + clearance "
             f"{CLEARANCE_M:.2f})", "",
             f"{'face m':>7} {'drift':>7}  {'verdict':12} record"]
    for r in rows:
        drift = "     —" if r["drift_m"] is None else f"{r['drift_m']:+7.3f}"
        mark = " " if r["ok"] else "!"
        lines.append(f"{r['face_m']:7.3f} {drift}  {r['verdict']:12} {mark}{r['key']}")
    return "\n".join(lines)


def gate(quiet: bool = False) -> int:
    baseline = load(BASELINE)
    rows = verdicts(baseline)
    bad = [r for r in rows if not r["ok"]]
    seen = {r["key"] for r in rows}
    gone = [k for k in list(baseline["on_rule"]) + list(baseline["exceptions"])
            if k not in seen]
    if not quiet:
        print(table(rows))
        print()
    for r in bad:
        if r["verdict"] == "unbaselined":
            print(f"FAIL {r['key']} fronts North Water Street at {r['face_m']:.3f} m and "
                  f"the baseline does not know it. Put it on the rule, or record it as an "
                  f"exception with a reason.")
        else:
            print(f"FAIL {r['key']} has drifted {r['drift_m']:+.3f} m off its "
                  f"{r['verdict']} figure.")
    for k in gone:
        print(f"FAIL {k} is baselined here and no longer fronts North Water Street. "
              f"Re-write the baseline in the commit that moved it.")
    if bad or gone:
        return 1
    if not quiet:
        print(f"OK  {len(rows)} north-bank frontages, "
              f"{sum(1 for r in rows if r['verdict'] == 'on_rule')} on the rule, "
              f"{sum(1 for r in rows if r['verdict'] == 'exception')} baselined exceptions.")
    return 0


def self_test() -> int:
    """Slide an on-rule roof 3 m off the frontage line, in memory, and watch the gate fire."""
    baseline = load(BASELINE)
    key = baseline["on_rule"][0]
    sid, pid = key.split("__", 1)
    record = load(DATA / "structures" / f"{sid}.json")
    phase = next(p for p in record["phases"] if p["id"] == pid)
    pos = phase["position"]
    moved = {key: (float(pos["utm_e"]), float(pos["utm_n"]) + 3.0)}
    before = [r for r in verdicts(baseline) if r["key"] == key][0]
    after = [r for r in verdicts(baseline, moved) if r["key"] == key][0]
    print(f"{key}: committed {before['face_m']:.3f} m (ok={before['ok']}), "
          f"moved 3 m north {after['face_m']:.3f} m (ok={after['ok']})")
    if before["ok"] and not after["ok"]:
        print("OK  the assertion fires when a roof leaves the frontage line.")
        return 0
    print("FAIL the self-test did not fire — the gate is not holding what it claims.")
    return 1


def write_baseline() -> int:
    baseline = load(BASELINE)
    rule = setback_m(float(street()["track_width_m"]))
    exceptions = dict(baseline["exceptions"])
    for row in frontages():
        if row["key"] in baseline["on_rule"]:
            continue
        entry = exceptions.get(row["key"], {"reason": "UNEXPLAINED — write the reason."})
        entry["face_m"] = row["face_m"]
        exceptions[row["key"]] = entry
    baseline["exceptions"] = dict(sorted(exceptions.items()))
    baseline["rule_m"] = round(rule, 3)
    BASELINE.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BASELINE.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true", help="the ratchet check.sh runs")
    ap.add_argument("--self-test", action="store_true", help="break the assertion in memory")
    ap.add_argument("--write-baseline", action="store_true", help="only to record a repair")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.write_baseline:
        return write_baseline()
    if args.gate:
        return gate(args.quiet)
    print(table(verdicts(load(BASELINE))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
