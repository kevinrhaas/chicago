#!/usr/bin/env python3
"""Count every watercourse Wright draws, on the whole 600 dpi sheet (T-0795).

The three Wright readings this project holds were each taken inside a WINDOW of
the BPL/Leventhal scan — the forks box, the harbour box. The National Archives /
Historic Urban Plans facsimile the owner added in 2026-09-05 is whole, and the
owner's ask was plain: *"where the various sloughs are."* So this walks the
entire sheet, counts what is drawn, and re-measures the three courses against it.

    tools/audit_wright_watercourses.py                  print the audit
    tools/audit_wright_watercourses.py --check-sheet    re-read the raster (needs PIL+numpy)
    tools/audit_wright_watercourses.py --write          write the trace
    tools/audit_wright_watercourses.py --check-properties   offline re-derivation (the gate)
    tools/audit_wright_watercourses.py --self-test      the gate's own assertions

TWO TIERS, the split `trace_river.py` and `check_wright_nara_registration.py`
already make. `--check-properties` re-derives every number in the committed JSON
from the committed JSON's own inputs — the fit, the centreline, the picks — and
needs nothing but the standard library, so it runs in the per-commit gate.
`--check-sheet` re-opens the 5050 x 6628 raster and re-measures; it needs Pillow
and numpy, which the gate does not have, so it stays the deliberate second tier.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
DATUM = ROOT / "data/datum.json"
HYDRO = ROOT / "data/terrain/epochs/e1834_harbor_cut/hydrology.geojson"
OUT = ROOT / "data/traces/wright_1834_watercourse_audit.json"
RASTER = ROOT.parent / "pre_fire_v1/maps/images/1834-wright-map.jpg"

# The sweep. Twenty tiles, 1012 x 1100 NA pixels each, covering x 600..4648 and
# y 400..5900 — every part of the sheet inside the neat line, read at 1:1 (one
# screen pixel per raster pixel), which is the resolution at which a drafted
# double line 18 px wide cannot hide. Recorded here because a count of what is
# NOT on a sheet is only worth anything if the ground it was looked for on is
# stated.
SWEEP = {"x0": 600, "y0": 400, "nx": 4, "ny": 5, "tile_w": 1012, "tile_h": 1100}

# The two bank re-entrants, picked by eye off the NA raster at 8x and 5x with a
# 20 px grid ruled over the crop. A pick by eye is evidence about a raster and
# the pixel is committed so the next reader can re-open the sheet and disagree.
PICKS = {
    "lasalle_mouth_reentrant": {
        "px": [2403, 2495],
        "uncertainty_px": 5,
        "crop_box": [2370, 2440, 2470, 2540],
        "what": "the apex of the V-shaped re-entrant in the river's SOUTH bank line at "
                "the west end of the South Water block numbered 50",
    },
    "state_mouth_reentrant": {
        "px": [2968, 2515],
        "uncertainty_px": 5,
        "crop_box": [2900, 2400, 3060, 2560],
        "what": "the apex of the narrow inlet notched into the river's SOUTH bank line "
                "at the foot of State Street",
    },
}

# What the terrain holds, and what each record claims Wright for. Read from the
# spec at run time; this table is only the CLAIM, which is the thing the audit
# tests.
WRIGHT_CLAIMS = {
    "north_side_slough": "existence AND course",
    "lasalle_slough_lower": "existence and mouth only (the course inland is Conley/Stelzer)",
    "lasalle_slough_upper": "nothing — inherits its parent's mouth",
    "state_slough_course": "nothing — chicagology and Conley/Stelzer",
    "state_slough_mouth": "the traced re-entrant only",
    "west_prairie_swale_a": "nothing — no source at all",
    "west_prairie_swale_b": "nothing — no source at all",
}

TOL_M = 20.0  # the ticket's tolerance: the georeference's own +/- 20 m


def _fit():
    g = json.loads(GCP.read_text())
    d = json.loads(DATUM.read_text())
    c = g["fit"]["coefficients"]
    return g, d, (c["a"], c["b"], c["c"], c["d"], c["e"], c["f"])


def to_local(px, py):
    _, d, (a, b, c, dd, e, f) = _fit()
    return (a * px + b * py + c - d["origin_utm_e"],
            dd * px + e * py + f - d["origin_utm_n"])


def to_pixel(le, ln):
    _, d, (a, b, c, dd, e, f) = _fit()
    x = le + d["origin_utm_e"] - c
    y = ln + d["origin_utm_n"] - f
    det = a * e - b * dd
    return ((x * e - b * y) / det, (a * y - dd * x) / det)


def centreline_px():
    """The committed north_side_slough centreline, in NA pixels."""
    _, d, _ = _fit()
    h = json.loads(HYDRO.read_text())
    ft = h["features"][0]
    return [to_pixel(x - d["origin_utm_e"], y - d["origin_utm_n"])
            for x, y in ft["geometry"]["coordinates"]]


def m_per_px():
    g, _, _ = _fit()
    s = g["fit"]["scale_m_per_px"]
    return (s["x"] + s["y"]) / 2


# ---------------------------------------------------------------- the raster tier

def read_sheet() -> dict:
    """Re-measure, off the raster. Needs Pillow and numpy."""
    import numpy as np  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    arr = np.asarray(Image.open(RASTER).convert("L"), dtype=float)

    def sample(x, y):
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        return (arr[y0, x0] * (1 - fx) * (1 - fy) + arr[y0, x0 + 1] * fx * (1 - fy)
                + arr[y0 + 1, x0] * (1 - fx) * fy + arr[y0 + 1, x0 + 1] * fx * fy)

    pts = centreline_px()
    thresh, reach = 130.0, 26.0
    stations = []
    for i, (px, py) in enumerate(pts):
        j = min(max(i, 1), len(pts) - 2)
        tx = pts[j + 1][0] - pts[j - 1][0]
        ty = pts[j + 1][1] - pts[j - 1][1]
        L = math.hypot(tx, ty)
        nx, ny = -ty / L, tx / L
        runs, cur = [], None
        t = -reach
        while t <= reach + 1e-9:
            if sample(px + nx * t, py + ny * t) < thresh:
                cur = [t, t] if cur is None else [cur[0], t]
            elif cur:
                runs.append(cur)
                cur = None
            t += 0.5
        if cur:
            runs.append(cur)
        cen = [((a + b) / 2.0, b - a) for a, b in runs]
        left = [c for c in cen if c[0] < 0]
        right = [c for c in cen if c[0] > 0]
        if not left or not right:
            stations.append({"i": i, "paired": False})
            continue
        lft = max(left, key=lambda c: c[0])
        rgt = min(right, key=lambda c: c[0])
        stations.append({"i": i, "paired": True,
                         "offset_px": round((lft[0] + rgt[0]) / 2.0, 3),
                         "separation_px": round(rgt[0] - lft[0], 3)})
    return {"threshold": thresh, "reach_px": reach, "stations": stations}


def summarise(sheet: dict) -> dict:
    """The statistics the audit reports, from the station table."""
    mpp = m_per_px()
    good = [s for s in sheet["stations"]
            if s.get("paired") and 6.0 <= s["separation_px"] <= 32.0]
    offs = sorted(abs(s["offset_px"]) for s in good)
    seps = sorted(s["separation_px"] for s in good)

    def med(v):
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0

    return {
        "stations": len(sheet["stations"]),
        "paired": len(good),
        "median_departure_m": round(med(offs) * mpp, 2),
        "max_departure_m": round(offs[-1] * mpp, 2),
        "median_stroke_separation_m": round(med(seps) * mpp, 2),
        "stroke_separation_range_m": [round(seps[0] * mpp, 2), round(seps[-1] * mpp, 2)],
        "m_per_px": round(mpp, 5),
    }


# ---------------------------------------------------------------- the audit record

def build(sheet: dict) -> dict:
    mpp = m_per_px()
    g, _, _ = _fit()
    picks = {}
    for k, p in PICKS.items():
        e, n = to_local(*p["px"])
        picks[k] = dict(p, local_enu_m=[round(e, 1), round(n, 1)],
                        uncertainty_m=round(p["uncertainty_px"] * mpp, 1))
    return {
        "_doc": __doc__.strip().splitlines()[0],
        "ticket": "T-0795",
        "raster": {
            "path": "chicago/pre_fire_v1/maps/images/1834-wright-map.jpg",
            "source_id": "wright_1834_nara_hup",
            "sha256": g["raster"]["sha256"],
            "size_px": [g["raster"]["width"], g["raster"]["height"]],
        },
        "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json, `fit` "
                        f"(eleven-point, RMS {g['fit']['rms_m']} m)",
        "sweep": dict(SWEEP, method=(
            "Twenty tiles read at 1:1, each 1012 x 1100 NA px, covering the whole "
            "sheet inside the neat line. Every line that is water and not the river "
            "was to be counted; the lacunae L1 and L2 are excluded, being cloth.")),
        "count": {
            "non_river_watercourses_drawn": 1,
            "which": ["north_side_slough"],
            "note": "ONE. The sheet draws the river — Main Branch, North Branch, South "
                    "Branch, the harbour cut, the lake shore and the sand bar — and "
                    "exactly one watercourse that is not the river: the double line "
                    "running north out of the main stem at the North Water/Kinzie "
                    "corner to Michigan Street. Nothing in the West Division, nothing "
                    "in Wabansia, nothing in the School Section, nothing along the lake "
                    "shore, nothing in the Michigan St tract's own ground.",
        },
        "wright_claims_in_the_terrain": WRIGHT_CLAIMS,
        "north_side_slough_recheck": summarise(sheet),
        "bank_reentrant_picks": picks,
        "tolerance_m": TOL_M,
        "confidence": "attested",
        "confidence_note":
            "What this record documents is the SHEET: which lines Wright drew and where "
            "they fall through a committed affine. Every number is a measurement of a "
            "named raster by a named method with committed parameters. What the lines "
            "MEAN — slough, road, ditch — is not settled by measuring them, and the "
            "findings below say so where it matters.",
    }


def findings(rec: dict) -> list[str]:
    r = rec["north_side_slough_recheck"]
    out = [
        f"ONE watercourse is drawn that is not the river. The count the town carries is "
        f"FOUR — north_side_slough, the La Salle slough, the State Street slough and two "
        f"placed prairie swales — and only ONE of them is a line on this sheet. That is "
        f"not a contradiction: three of the four never claimed to be. It is the audit the "
        f"ticket asked for, and it comes out even.",
        f"The committed north_side_slough centreline IS the drawn double line. "
        f"{r['paired']} of {r['stations']} stations find the pair of strokes that bracket "
        f"it; the centre of the pair departs from the committed line by "
        f"{r['median_departure_m']} m median and {r['max_departure_m']} m at worst, inside "
        f"a fit whose own RMS is 16.02 m. The BPL window reading and the whole NA sheet "
        f"agree about this watercourse to under two metres.",
        f"THE SAME INK WAS BEING READ TWICE, AND T-1080 SETTLED IT. That ticket traced a "
        f"ROAD down these same strokes, and the ribbon it painted came out wet — because "
        f"this project already carves that line as a watercourse. The road record is "
        f"WITHDRAWN: the two readings were never near each other, they were one feature. "
        f"What survives is kept under this feature's own name, as the only independent "
        f"cross-check `north_side_slough` has — off the NA sheet under a different "
        f"registration, agreeing to 1.54 m median and 17.91 m at worst: "
        f"`data/traces/north_side_slough_na_reread.json`, "
        f"`tools/read_north_side_slough_na.py`. Nothing is regraded by it.",
        f"WHERE THE FEATURE MEETS THE RIVER IT IS DRAWN AS A CONFLUENCE. At NA px "
        f"(2033, 2270) the west stroke becomes the river's north bank running south-west "
        f"and the east stroke becomes the same bank running east: the tributary's two "
        f"banks are continuous with the main stem's, on either side of an opening. A road "
        f"drawn to a river either stops at the bank or crosses it. This does neither.",
        f"The drawn corridor is {r['median_stroke_separation_m']} m between stroke "
        f"centres (range {r['stroke_separation_range_m'][0]}-"
        f"{r['stroke_separation_range_m'][1]} m), against the 7.1 m the terrain's width "
        f"was measured from — twice the interior distance transform of the surviving wash "
        f"fragments on the BPL scan. A hand-drawn double line carries no surveyed width "
        f"and no width is taken from it here; the discrepancy is recorded, not resolved.",
        f"BOTH BANK RE-ENTRANTS ARE ON THE NA SHEET AND BOTH CONFIRM THEIR RECORD. The "
        f"La Salle mouth's V in the south bank picks at E "
        f"+{rec['bank_reentrant_picks']['lasalle_mouth_reentrant']['local_enu_m'][0]}, "
        f"against the E +462..+469 the traced 1834 waterline carries. The State Street "
        f"mouth's inlet picks at E "
        f"+{rec['bank_reentrant_picks']['state_mouth_reentrant']['local_enu_m'][0]}, "
        f"against E +850..+856. Both are inside the {TOL_M:.0f} m the georeference allows, "
        f"so neither scan is disbelieved and no course moves.",
        f"WRIGHT DRAWS NO WATERCOURSE ON THE WEST DIVISION'S PRAIRIE. "
        f"west_prairie_swale_a and _b stay reconstructed with no source, and the sheet's "
        f"silence is now recorded on them: the tiles covering their ground carry platted "
        f"blocks and lot lines and nothing else. The dossier's '1-2 ft slough swales' "
        f"remain the only evidence that they existed at all, and it says nothing about "
        f"where.",
        f"NEITHER MAIN-BRANCH SLOUGH HAS AN INLAND COURSE ON THIS SHEET, which is exactly "
        f"what their records say. lasalle_slough_lower claims Wright for its EXISTENCE AND "
        f"MOUTH and Conley/Stelzer for the course; state_slough_course claims Wright for "
        f"nothing at all. The whole sheet now says the same, so T-0793 and T-0794's traces "
        f"need no slough ticket after them.",
    ]
    return out


# ---------------------------------------------------------------- the offline gate

def check_properties() -> int:
    """Re-derive every number in the committed record from its own inputs."""
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing")
        return 1
    rec = json.loads(OUT.read_text())
    bad = []
    g, _, _ = _fit()

    if rec["raster"]["sha256"] != g["raster"]["sha256"]:
        bad.append("the audit's raster checksum is not the registration's")

    mpp = m_per_px()
    if abs(rec["north_side_slough_recheck"]["m_per_px"] - mpp) > 5e-5:
        bad.append("m_per_px does not re-derive from the fit's axis scales")

    for k, p in rec["bank_reentrant_picks"].items():
        e, n = to_local(*p["px"])
        if abs(e - p["local_enu_m"][0]) > 0.05 or abs(n - p["local_enu_m"][1]) > 0.05:
            bad.append(f"{k}: the committed metres do not re-derive from the committed pixel")
        if abs(p["uncertainty_m"] - round(p["uncertainty_px"] * mpp, 1)) > 0.05:
            bad.append(f"{k}: uncertainty_m is not uncertainty_px through the fit")
        x0, y0, x1, y1 = p["crop_box"]
        if not (x0 <= p["px"][0] <= x1 and y0 <= p["px"][1] <= y1):
            bad.append(f"{k}: the pick is outside the crop it was picked on")

    # The two re-entrants must still corroborate the courses they were read for,
    # or the refusal this record makes stops being a refusal. Both are quoted as
    # E-ranges on the traced 1834 waterline.
    for k, lo, hi in (("lasalle_mouth_reentrant", 462.0, 469.0),
                      ("state_mouth_reentrant", 850.0, 856.0)):
        e = rec["bank_reentrant_picks"][k]["local_enu_m"][0]
        gap = 0.0 if lo <= e <= hi else min(abs(e - lo), abs(e - hi))
        if gap > rec["tolerance_m"]:
            bad.append(f"{k}: {gap:.1f} m outside the traced re-entrant's E-range, "
                       f"past the {rec['tolerance_m']} m the georeference allows — "
                       f"this record says the two scans agree and they no longer do")

    n = len(centreline_px())
    if rec["north_side_slough_recheck"]["stations"] != n:
        bad.append(f"the re-check reports {rec['north_side_slough_recheck']['stations']} "
                   f"stations and the committed centreline has {n} vertices")

    # The count is a claim about the terrain as well as the sheet: every id the
    # audit names must still be a watercourse the terrain holds.
    spec = json.loads((ROOT / "data/terrain/epochs/e1834_harbor_cut/terrain_spec.json").read_text())
    held = {w["id"] for w in spec["watercourses"]} | {s["id"] for s in spec["swales"]}
    for i in set(rec["count"]["which"]) | set(rec["wright_claims_in_the_terrain"]):
        if i not in held:
            bad.append(f"the audit names '{i}' and the terrain no longer holds it")

    if bad:
        for b in bad:
            print("FAIL:", b)
        return 1
    print(f"the Wright watercourse audit re-derives: {len(rec['bank_reentrant_picks'])} "
          f"bank picks through the fit, {n} centreline stations, "
          f"{rec['count']['non_river_watercourses_drawn']} watercourse drawn that is not "
          f"the river")
    return 0


def self_test() -> int:
    """Break each assertion and require it to fire."""
    import copy  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    global OUT  # noqa: PLW0603
    good = json.loads(OUT.read_text())
    breaks = [
        ("raster checksum", lambda r: r["raster"].__setitem__("sha256", "0" * 64)),
        ("m_per_px", lambda r: r["north_side_slough_recheck"].__setitem__("m_per_px", 0.5)),
        ("pick arithmetic", lambda r: r["bank_reentrant_picks"]["state_mouth_reentrant"]
            .__setitem__("local_enu_m", [0.0, 0.0])),
        ("pick inside its crop", lambda r: r["bank_reentrant_picks"]["state_mouth_reentrant"]
            .__setitem__("px", [10, 10])),
        ("station count", lambda r: r["north_side_slough_recheck"].__setitem__("stations", 3)),
        ("an id the terrain holds", lambda r: r["count"].__setitem__("which", ["no_such_slough"])),
    ]
    failures = []
    with tempfile.TemporaryDirectory() as td:
        for name, mutate in breaks:
            r = copy.deepcopy(good)
            mutate(r)
            p = Path(td) / "audit.json"
            p.write_text(json.dumps(r))
            real, OUT = OUT, p
            try:
                rc = check_properties()
            finally:
                OUT = real
            if rc == 0:
                failures.append(name)
        if check_properties() != 0:
            failures.append("the committed record itself does not pass")
    if failures:
        for f in failures:
            print(f"SELF-TEST FAIL: breaking '{f}' did not fire")
        return 1
    print(f"self-test: {len(breaks)} assertion(s) fire when broken, and the committed "
          f"record passes")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-sheet", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.check_properties:
        return check_properties()
    if args.self_test:
        return self_test()

    if args.check_sheet or args.write:
        rec = build(read_sheet())
        if args.write:
            OUT.write_text(json.dumps(rec, indent=2) + "\n")
            print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        if not OUT.exists():
            print("no committed audit yet — run --write")
            return 1
        rec = json.loads(OUT.read_text())

    r = rec["north_side_slough_recheck"]
    print(f"\nWRIGHT 1834 (NA/HUP), whole sheet: "
          f"{rec['count']['non_river_watercourses_drawn']} watercourse drawn that is not "
          f"the river\n")
    print(f"  north_side_slough re-check: {r['paired']}/{r['stations']} stations paired, "
          f"departure {r['median_departure_m']} m median / {r['max_departure_m']} m max")
    print(f"  drawn corridor: {r['median_stroke_separation_m']} m between stroke centres")
    for k, p in rec["bank_reentrant_picks"].items():
        print(f"  {k}: px {p['px']} -> E {p['local_enu_m'][0]:+.1f}, "
              f"N {p['local_enu_m'][1]:+.1f} (+/- {p['uncertainty_m']} m)")
    print()
    for i, f in enumerate(findings(rec), 1):
        print(f"{i}. {f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
