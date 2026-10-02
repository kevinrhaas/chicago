#!/usr/bin/env python3
"""Measure how far the Harrison 1830 reading sits from the derived 1812 pre-cut shore.

    python3 tools/measure_shore_1812_harrison.py           measure and write the reading
    python3 tools/measure_shore_1812_harrison.py --check   re-measure and diff against it

WHY (T-1286). `shore_1812_pre_cut` is DERIVED from Wright's 1834 survey with the
harbour works taken out (`tools/derive_shore_1812.py`), because no survey of the
pre-cut mouth exists; the owner ruled on 2026-09-17 that Wright carries it. The only
pre-cut sheet this project holds is Harrison's of February 1830, read through the
fort-anchored transform T-0883 stated (`tools/trace_shoreline_1830.py`). It is unscaled,
re-engraved in 1884 and admits memory additions, so it cannot carry the line — but it
is a second reading of the same landform by a different method, and how far it sits
from the derived line is the only honest statement of what the post-cut base costs.

THIS CHANGES NO GEOMETRY. It reads two committed files and writes one measurement.

METHOD. Each Harrison line is walked at a fixed step and every station is measured to
the nearest point on the derived 1812 lines (shores, the bar's ring, and the declared
spit attachment, which is reported apart because it claims only where the bar met the
mainland). A station whose nearest point is the free END of a derived line has no
counterpart on it — the derived file stops there — and is counted, not measured. The
distribution is by LENGTH of Harrison line, not by vertex, so a wiggle the tracer kept
does not outvote a straight reach. It is binned by distance from the transform's own
anchor, because a single-anchor transform's errors grow with distance from it, and a
disagreement that grows the same way says something different from one that does not.

THE MOUTH. Harrison letters "Old Mouth of River very shallow" at the foot of the bar,
where the tracer places its declared `old_mouth` cut. That cut's centre is set beside
the two mouth stations the derived state's reading band holds, as northings: the
comparison the derivation itself makes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DERIVED = ROOT / "data" / "terrain" / "epochs" / "e1830_natural" / "shoreline.geojson"
HARRISON = ROOT / "data" / "terrain" / "harrison_1830_pre_cut_reading.geojson"
OUT = ROOT / "data" / "terrain" / "1812_harrison_cross_check.json"

STEP_M = 2.0
BIN_M = 100.0
# Where the comparison is split for the sentence the 1812 file quotes: near the fort,
# where the transform is anchored, and down the old southward channel.
NEAR_M, FAR_M = 100.0, 200.0
# The derived feature that claims only where the bar met the mainland, not a shore.
ATTACHMENT_KIND = "unmodelled_gap"
TARGET_KINDS = {"shore", "bar", ATTACHMENT_KIND}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines_of(feature: dict) -> list[list[list[float]]]:
    g = feature["geometry"]
    if g["type"] == "LineString":
        return [g["coordinates"]]
    if g["type"] == "Polygon":
        return [g["coordinates"][0]]
    raise SystemExit(f"FAIL unexpected geometry {g['type']} on {feature.get('id')}")


def segments(derived: dict, origin: tuple[float, float]) -> list[tuple]:
    out = []
    for f in derived["features"]:
        kind = f["properties"].get("kind")
        if kind not in TARGET_KINDS:
            continue
        for line in lines_of(f):
            pts = [(e - origin[0], n - origin[1]) for e, n in line]
            closed = pts[0] == pts[-1]
            for i in range(len(pts) - 1):
                free_a = i == 0 and not closed
                free_b = i == len(pts) - 2 and not closed
                out.append((f["id"], kind, pts[i], pts[i + 1], free_a, free_b))
    return out


def nearest(p, segs):
    best = None
    for fid, kind, a, b, free_a, free_b in segs:
        dx, dy = b[0] - a[0], b[1] - a[1]
        ll = dx * dx + dy * dy
        t = 0.0 if ll == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ll))
        q = (a[0] + t * dx, a[1] + t * dy)
        d = math.dist(p, q)
        if best is None or d < best[0]:
            best = (d, fid, kind, (free_a and t == 0.0) or (free_b and t == 1.0))
    return best


def stations(line):
    """Points every STEP_M along the line, each standing for STEP_M of it."""
    out = []
    for a, b in zip(line, line[1:]):
        seg = math.dist(a, b)
        k = max(1, round(seg / STEP_M))
        for j in range(k):
            t = (j + 0.5) / k
            out.append(((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), seg / k))
    return out


def weighted_pct(rows, q):
    rows = sorted(rows)
    total = sum(w for _, w in rows)
    acc = 0.0
    for d, w in rows:
        acc += w
        if acc >= q * total:
            return d
    return rows[-1][0]


def summary(rows):
    if not rows:
        return {"length_m": 0.0}
    return {
        "length_m": round(sum(w for _, w in rows), 1),
        "median_m": round(weighted_pct(rows, 0.5), 1),
        "p90_m": round(weighted_pct(rows, 0.9), 1),
        "max_m": round(max(d for d, _ in rows), 1),
        "mean_m": round(sum(d * w for d, w in rows) / sum(w for _, w in rows), 1),
        "share_within_20_m": round(sum(w for d, w in rows if d <= 20.0)
                                   / sum(w for _, w in rows), 3),
    }


def evidence_sentence(near: dict, far: dict, gap: float) -> str:
    """The sentence derive_shore_1812.py's evidence_limit carries, word for word."""
    return (
        f"The one pre-cut sheet held, Harrison's of February 1830 (unscaled, re-engraved "
        f"in 1884), was measured against these lines (T-1286, "
        f"data/terrain/1812_harrison_cross_check.json): within {NEAR_M:g} m of the fort its "
        f"banks sit a median {near['median_m']:.0f} m and at most {near['max_m']:.0f} m "
        f"from them, but down the old southward channel, {FAR_M:g} m and more from the "
        f"fort, they sit {far['median_m']:.0f} m away at the median and up to "
        f"{far['max_m']:.0f} m, and it letters the old mouth {gap:.0f} m north of the "
        f"adopted station. That disagreement is filed, not resolved.")


def measure() -> dict:
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    origin = (datum["origin_utm_e"], datum["origin_utm_n"])
    derived = json.loads(DERIVED.read_text())
    harrison = json.loads(HARRISON.read_text())
    segs = segments(derived, origin)
    anchor = tuple(harrison["transform"]["anchor_local_enu_m"])

    band = next(f for f in derived["features"]
                if f["properties"].get("kind") == "mouth_outlet_reading_band")
    bar = next(f for f in derived["features"] if f["properties"].get("kind") == "bar")
    cut = harrison["cuts"]["old_mouth"]["box_px"]
    tf = harrison["transform"]
    cx, cy = (cut[0] + cut[2]) / 2, (cut[1] + cut[3]) / 2
    old_mouth = (tf["anchor_local_enu_m"][0] + (cx - tf["anchor_px"][0]) * tf["scale_m_per_px"],
                 tf["anchor_local_enu_m"][1] - (cy - tf["anchor_px"][1]) * tf["scale_m_per_px"])
    adopted = band["properties"]["stations"][band["properties"]["adopted"]]["local"]
    bar_tip = bar["properties"]["south_tip_local"]

    every, per_feature, per_target, bins = [], {}, {}, {}
    no_counterpart = {}
    lowest_n = None
    for f in harrison["features"]:
        line = [(e - origin[0], n - origin[1]) for e, n in f["geometry"]["coordinates"]]
        lowest_n = min([lowest_n] + [p[1] for p in line] if lowest_n is not None
                       else [p[1] for p in line])
        rows = []
        for p, w in stations(line):
            d, fid, kind, at_free_end = nearest(p, segs)
            if at_free_end:
                no_counterpart[f["id"]] = no_counterpart.get(f["id"], 0.0) + w
                continue
            rows.append((d, w))
            every.append((d, w))
            per_target.setdefault(fid, []).append((d, w))
            r = math.dist(p, anchor)
            key = int(r // BIN_M)
            bins.setdefault(key, []).append((d, w))
        per_feature[f["id"]] = summary(rows)
    near = summary([r for k, v in bins.items() if (k + 1) * BIN_M <= NEAR_M for r in v])
    far = summary([r for k, v in bins.items() if k * BIN_M >= FAR_M for r in v])
    gap = round(old_mouth[1] - adopted[1])

    return {
        "_doc": (
            "How far the Harrison 1830 pre-cut reading sits from the derived 1812 shore. "
            "GENERATED by tools/measure_shore_1812_harrison.py from the two committed files "
            "named under `inputs`; do not hand-edit (check.sh re-measures it). It is a "
            "MEASUREMENT and changes no geometry: Wright 1834 carries shore_1812_pre_cut by "
            "the owner's ruling of 2026-09-17, and docs/RESEARCH/shore_1812_pre_cut.md section "
            "6 says what these numbers mean and what they do not settle (T-1286)."),
        "inputs": {
            "derived": {"path": str(DERIVED.relative_to(ROOT)), "sha256": sha(DERIVED)},
            "harrison": {"path": str(HARRISON.relative_to(ROOT)), "sha256": sha(HARRISON)},
        },
        "method": {
            "step_m": STEP_M,
            "weighting": "by length of Harrison line",
            "targets": "derived features of kind " + ", ".join(sorted(TARGET_KINDS)),
            "no_counterpart": ("a station whose nearest derived point is the free end of a "
                               "derived line is counted under `no_counterpart_m`, not measured"),
            "bins": f"distance from the transform's anchor (local E/N {list(anchor)}), {BIN_M:g} m",
        },
        "overall": summary(every),
        "by_harrison_line": per_feature,
        "by_nearest_derived_feature": {k: summary(v) for k, v in sorted(per_target.items())},
        "by_distance_from_anchor": [
            dict(from_m=k * BIN_M, to_m=(k + 1) * BIN_M, **summary(v))
            for k, v in sorted(bins.items())],
        "near_the_fort": dict(within_m=NEAR_M, **near),
        "down_the_old_channel": dict(beyond_m=FAR_M, **far),
        "evidence_sentence": evidence_sentence(near, far, gap),
        "no_counterpart_m": {k: round(v, 1) for k, v in sorted(no_counterpart.items())},
        "mouth": {
            "harrison_old_mouth_local": [round(old_mouth[0], 2), round(old_mouth[1], 2)],
            "harrison_old_mouth_from": "centre of the trace's declared `old_mouth` cut, where "
                                       "Harrison letters 'Old Mouth of River very shallow'",
            "adopted_station_local": adopted,
            "wright_bar_tip_local": bar_tip,
            "northing_gap_to_adopted_m": round(old_mouth[1] - adopted[1], 1),
            "northing_gap_to_bar_tip_m": round(old_mouth[1] - bar_tip[1], 1),
            "harrison_sheet_reaches_north_m": round(lowest_n, 1),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = measure()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    rel = OUT.relative_to(ROOT)
    limit = json.loads(DERIVED.read_text()).get("evidence_limit", "")
    if doc["evidence_sentence"] not in limit:
        print(f"FAIL {DERIVED.relative_to(ROOT)} evidence_limit does not carry the measured "
              f"sentence; put this, word for word, in tools/derive_shore_1812.py and "
              f"re-derive:\n  {doc['evidence_sentence']}")
        return 1
    if args.check:
        if not OUT.exists():
            print(f"FAIL {rel} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"FAIL {rel} is not what the committed lines measure today — "
                  f"re-run tools/measure_shore_1812_harrison.py and re-read section 6 "
                  f"of docs/RESEARCH/shore_1812_pre_cut.md against the new numbers")
            return 1
        print(f"OK {rel} re-measures from the committed lines")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
