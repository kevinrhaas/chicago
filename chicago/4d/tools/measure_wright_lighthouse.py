#!/usr/bin/env python3
"""Hold the lighthouse's coordinate to the glyph it was read off.

`data/traces/wright_1834_lighthouse_glyph.json` records the resource pixel where
Wright's 1834 sheet draws the ring labelled *L. House*, and
`data/structures/chicago_lighthouse_1832.json` carries the coordinate that pixel
lands on. Those are the same statement written in two files, and two files agree
until the day one of them matters — a later run that nudges the record for some
unrelated reason would quietly detach it from its evidence, and the note would go
on citing a reading the number no longer comes from.

So this recomputes the coordinate from the committed pixel, through
`tools/wright_px.py` and the one fitted affine this project keeps, and refuses a
record that has drifted from it. It re-derives nothing about the SHEET: the pick
is an eyeball reading of a raster and cannot be gated, which is exactly why the
pixel is committed rather than only the metres.

    tools/measure_wright_lighthouse.py            # report
    tools/measure_wright_lighthouse.py --check    # gate
    tools/measure_wright_lighthouse.py --self-test
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from wright_px import to_local  # noqa: E402 — ROOT must be on the path first

TRACE = ROOT / "data/traces/wright_1834_lighthouse_glyph.json"
RECORD = ROOT / "data/structures/chicago_lighthouse_1832.json"
PHASE = "tower_1832"

# A tenth of a metre. The trace stores the derived point rounded to centimetres and
# the record stores UTM to centimetres, so the two can differ by rounding and by
# nothing else; anything larger is a record that has moved away from its evidence.
TOLERANCE_M = 0.1


def _load() -> tuple[dict, dict]:
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    return trace, record


def _phase(record: dict) -> dict:
    for ph in record["phases"]:
        if ph["id"] == PHASE:
            return ph
    raise SystemExit(f"{RECORD.name}: no phase '{PHASE}'")


def measure(trace: dict, record: dict) -> dict:
    px, py = trace["glyph"]["pixel"]
    local_e, local_n = to_local(float(px), float(py))
    datum = json.loads((ROOT / "data/datum.json").read_text(encoding="utf-8"))
    utm_e = local_e + datum["origin_utm_e"]
    utm_n = local_n + datum["origin_utm_n"]

    pos = _phase(record)["position"]
    drift = math.hypot(utm_e - pos["utm_e"], utm_n - pos["utm_n"])

    declared = trace["derived"]
    trace_drift = math.hypot(local_e - declared["local_e"], local_n - declared["local_n"])

    return {
        "pixel": [px, py],
        "recomputed_local": (local_e, local_n),
        "recomputed_utm": (utm_e, utm_n),
        "record_utm": (pos["utm_e"], pos["utm_n"]),
        "record_confidence": pos.get("confidence"),
        "record_sources": pos.get("sources") or [],
        "drift_record_m": drift,
        "drift_trace_m": trace_drift,
    }


def report(m: dict) -> None:
    print(f"Wright 1834 'L. House' glyph, resource pixel {m['pixel'][0]}, {m['pixel'][1]}")
    print("  recomputed local ENU   %+9.2f E  %+9.2f N" % m["recomputed_local"])
    print("  recomputed UTM 16N     %.2f  %.2f" % m["recomputed_utm"])
    print("  record carries         %.2f  %.2f" % m["record_utm"])
    print("  record drift from the reading   %.3f m" % m["drift_record_m"])
    print("  trace's own derived point drift %.3f m" % m["drift_trace_m"])
    print("  position graded '%s' on %s"
          % (m["record_confidence"], ", ".join(m["record_sources"]) or "no source"))


def check(trace: dict, record: dict) -> int:
    m = measure(trace, record)
    failed = 0
    if m["drift_trace_m"] > TOLERANCE_M:
        print("FAIL: %s's own `derived` block is %.3f m from what its pixel recomputes to"
              % (TRACE.name, m["drift_trace_m"]))
        failed = 1
    if m["drift_record_m"] > TOLERANCE_M:
        print("FAIL: %s stands %.3f m from the glyph it cites. The coordinate and the "
              "reading are the same statement; move one and you must move the other, or "
              "say in the note that the record no longer comes from the sheet."
              % (RECORD.name, m["drift_record_m"]))
        failed = 1
    src = m["record_sources"]
    if trace["raster"]["source_id"] not in src:
        print("FAIL: the position is derived from the Wright sheet and does not cite "
              "'%s'" % trace["raster"]["source_id"])
        failed = 1
    if m["record_confidence"] == "attested":
        print("FAIL: a glyph centre read off a lithograph through a 17.5 m RMS affine is "
              "not an attested coordinate — the sheet locates the tower, it does not "
              "survey it")
        failed = 1
    if not failed:
        report(m)
    return failed


def self_test() -> int:
    trace, record = _load()
    failures = []

    if check(trace, record) != 0:
        failures.append("the committed pair does not pass its own gate")

    moved = json.loads(json.dumps(record))
    _phase(moved)["position"]["utm_e"] += 5.0
    if check(trace, moved) == 0:
        failures.append("a record moved 5 m off its glyph passed")

    detached = json.loads(json.dumps(trace))
    detached["derived"]["local_e"] += 3.0
    if check(detached, record) == 0:
        failures.append("a trace whose derived block disagrees with its own pixel passed")

    uncited = json.loads(json.dumps(record))
    _phase(uncited)["position"]["sources"] = ["andreas_1884_v1"]
    if check(trace, uncited) == 0:
        failures.append("a position that does not cite the sheet it was read off passed")

    promoted = json.loads(json.dumps(record))
    _phase(promoted)["position"]["confidence"] = "attested"
    if check(trace, promoted) == 0:
        failures.append("a glyph reading promoted to attested passed")

    for f in failures:
        print("SELF-TEST FAIL: " + f)
    if not failures:
        print("self-test: 5 assertion(s) fire")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    trace, record = _load()
    if args.check:
        return check(trace, record)
    report(measure(trace, record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
