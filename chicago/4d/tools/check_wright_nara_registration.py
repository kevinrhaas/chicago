#!/usr/bin/env python3
"""Hold the Wright NARA/Historic Urban Plans registration to its own arithmetic.

    tools/check_wright_nara_registration.py --check-properties
    tools/check_wright_nara_registration.py --self-test

`data/traces/gcp/wright_1834_nara_hup_gcps.json` is the registration that the whole
Wright band stands on — at 600 dpi it resolves ink the BPL scan does not, so the
Original Town's block numerals are read off it and nothing else. Until T-0862 that
file had NO GATE: `grep -i nara tools/check.sh` returned nothing, and a hand edit to
a coefficient, a residual or a checksum would have passed every gate this project
has, silently moving every reading taken through the fit.

This is the offline half, in the shape `trace_river.py --check-properties` set: it
reads committed files, needs no numpy, no scipy, no Pillow and no network, and runs
in milliseconds. It asserts three different KINDS of claim:

  the raster        the working copy is where the record says, its sha256 still
                    matches, the `-lg` duplicate is still byte-identical, and the
                    sheet's own JPEG header still says 5050 x 6628 at 600 dpi
                    (parsed here rather than through Pillow, so the gate has no
                    import that can make it skip — see T-1083 on why that matters)
  the fit           every number `fit`, `retained_fit` and `scan_to_scan` state
                    re-derives from the coefficients and the control points: each
                    control point's residual, the RMS, the axis scales, the rotation,
                    the axis-scale difference, and which point departs most between
                    the two scans
  the sheet         the scale bar's px-per-foot re-fits from its committed tick
                    columns, and each lacuna's ground extent re-derives from its box

The EXPENSIVE half — re-locating the eight correspondences off the raster by
normalised cross-correlation — is the deliberate second tier, exactly as
`trace_river.py` splits `--check-properties` from a full re-trace. Nothing here
re-picks a point; it holds the picked ones to the fit they were used to build.

SINCE T-1091 THE FIT IN FORCE IS FITTED ON ELEVEN POINTS, not eight: the eight
crossings in `gcps[]` plus the School Section's other three corners, which live in
the file `fit.control.extra_points_file` names because they are weaker and
differently sourced. The gate scores the fit against ALL of its control and holds
`fit.rms_m_on_the_eight` and `fit.rms_m_on_the_three_corners` separately, so the
2.20 m the adoption cost the original eight stays visible rather than averaged away.
The superseded eight-point fit is kept as `retained_fit` — seated traces are still
carried through it until T-1092 re-seats them, and the three corner pixels were
recovered by inverting it — so it is held to its own arithmetic too, against
`gcps[].residual_m_in_retained_8pt_fit`.

WHEN THE WORKING COPY IS ABSENT the raster lives outside this app's subtree, in
`chicago/pre_fire_v1/`, where the owner placed it. The three raster assertions then
report SKIP BY NAME and the arithmetic still runs — a narrow, loud skip, not the
whole step quietly exiting 0 (T-1083 is the ticket about gates that pass by skipping).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The raster is not in this app's subtree: it is the owner's working copy under
# chicago/pre_fire_v1/, two levels up, and the registration cites it by path.
REPO_ROOT = ROOT.parent.parent

GCPS = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
SOURCE = ROOT / "data/sources/wright_1834_nara_hup.json"

FEET_TO_M = 0.3048

# Tolerances. Every quantity below is stated in the file at a fixed number of
# decimals, so the tolerance is the rounding step of the stated figure and nothing
# looser: a mutated literal cannot hide inside it.
TOL_RESIDUAL_M = 0.05      # residual_m, rms_m: stated to 0.1 / 0.01
TOL_SCALE = 5e-5           # scale_m_per_px: stated to 4 dp
TOL_DEG = 0.0005           # rotation_deg: stated to 3 dp
TOL_PCT = 0.05             # axis_scale_difference_pct: stated to 1 dp
TOL_PX = 0.05              # scan_to_scan residuals: stated to 0.1
TOL_PX_PER_FOOT = 5e-6     # fit_px_per_foot: stated to 5 dp


def _apply(coeffs: dict, x: float, y: float) -> tuple[float, float]:
    """The affine the file states, in the order its coefficient names imply."""
    return (coeffs["a"] * x + coeffs["b"] * y + coeffs["c"],
            coeffs["d"] * x + coeffs["e"] * y + coeffs["f"])


def _rms(values) -> float:
    values = list(values)
    return math.sqrt(sum(v * v for v in values) / len(values))


def _least_squares_line(xs, ys) -> tuple[float, float]:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return slope, my - slope * mx


def jpeg_properties(path: Path) -> dict:
    """Width, height and dpi out of the JPEG's own markers — no Pillow.

    A gate that needs an optional import is a gate that can skip (T-1083), and the
    two markers this reads (SOFn for the frame, APP0/JFIF for the density) are the
    only ones it needs. Nothing here decodes a scanline.
    """
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG (no SOI marker)")
    out: dict = {}
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xDA:          # start of scan — the headers are behind us
            break
        seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6,
                      0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            out["height"], out["width"] = height, width
        elif marker == 0xE0 and data[i + 4:i + 9] == b"JFIF\x00":
            units, x_density, y_density = struct.unpack(">BHH", data[i + 11:i + 16])
            if units == 1:          # 1 = dots per inch, 2 = per cm, 0 = aspect only
                out["dpi_x"], out["dpi_y"] = x_density, y_density
        i += 2 + seglen
    if "width" not in out:
        raise ValueError("no SOF marker: the file carries no frame header")
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_properties(doc: dict | None = None, source: dict | None = None) -> int:
    if doc is None:
        if not GCPS.exists():
            print(f"FAIL {GCPS.relative_to(ROOT)} is not committed")
            return 1
        doc = json.loads(GCPS.read_text())
    if source is None:
        source = json.loads(SOURCE.read_text()) if SOURCE.exists() else {}

    bad: list[str] = []
    skipped: list[str] = []

    def near(label, got, want, tol):
        if got is None:
            bad.append(f"{label}: the file states nothing")
        elif abs(float(got) - want) > tol:
            bad.append(f"{label}: committed {got} != {want:.6g} re-derived here "
                       f"(tolerance {tol:g})")

    # ---- the raster -------------------------------------------------------
    raster = doc.get("raster") or {}
    working = REPO_ROOT / raster.get("working_copy", "")
    if not raster.get("working_copy"):
        bad.append("raster.working_copy: the registration names no working copy")
    elif not working.exists():
        skipped.append(f"the raster half: {raster['working_copy']} is not in this "
                       "checkout (it lives outside this app's subtree)")
    else:
        digest = sha256(working)
        if digest != raster.get("sha256"):
            bad.append(f"raster.sha256: committed {raster.get('sha256')} != {digest} "
                       f"on {raster['working_copy']}")
        # The duplicate finding is an assertion, not prose: the record says the two
        # files in the repository are one scan, so the gate re-checks that they are.
        claim = raster.get("duplicate_in_repository") or ""
        dup_path = claim.split(" is byte-identical")[0].strip()
        if not dup_path:
            bad.append("raster.duplicate_in_repository: the record names no duplicate")
        else:
            dup = REPO_ROOT / dup_path
            if not dup.exists():
                bad.append(f"raster.duplicate_in_repository: {dup_path} is not there")
            elif sha256(dup) != digest:
                bad.append(f"raster.duplicate_in_repository: {dup_path} is NOT "
                           "byte-identical to the working copy any more")
        props = jpeg_properties(working)
        for key, got in (("width", props.get("width")), ("height", props.get("height"))):
            if raster.get(key) != got:
                bad.append(f"raster.{key}: committed {raster.get(key)} != {got} "
                           "in the sheet's own frame header")
        if props.get("dpi_x") != raster.get("dpi") or props.get("dpi_y") != raster.get("dpi"):
            bad.append(f"raster.dpi: committed {raster.get('dpi')} != "
                       f"{props.get('dpi_x')}x{props.get('dpi_y')} in the JFIF header")

    # The source record repeats the raster's figures in its human-readable locator,
    # and two copies of a number drift. Hold the prose to the registration.
    locator = source.get("locator", "")
    if locator:
        for claim in (f"{raster.get('width')} x {raster.get('height')} px",
                      f"{raster.get('dpi')} dpi",
                      str(raster.get("sha256"))):
            if claim not in locator:
                bad.append(f"the source record's locator no longer says {claim!r}")
        if source.get("id") != raster.get("source_id"):
            bad.append(f"source id {source.get('id')!r} != raster.source_id "
                       f"{raster.get('source_id')!r}")

    # ---- the fit ----------------------------------------------------------
    gcps = doc.get("gcps") or []
    ids = [g.get("id") for g in gcps]
    if len(set(ids)) != len(ids):
        bad.append(f"the control points do not carry distinct ids: {ids}")
    fit = doc.get("fit") or {}
    coeffs = fit.get("coefficients") or {}

    def shape(label, block, scale_key="scale_m_per_px"):
        """The three numbers any affine here states about itself."""
        c = block["coefficients"]
        sx = math.hypot(c["a"], c["d"])
        sy = math.hypot(c["b"], c["e"])
        scale = block.get(scale_key) or {}
        near(f"{label}.{scale_key}.x", scale.get("x"), sx, TOL_SCALE)
        near(f"{label}.{scale_key}.y", scale.get("y"), sy, TOL_SCALE)
        near(f"{label}.rotation_deg", block.get("rotation_deg"),
             math.degrees(math.atan2(c["d"], c["a"])), TOL_DEG)
        # Stated against the MEAN of the two axis scales, which is how the 5.2 the
        # retained fit carries is reached; against x it would read 5.34.
        near(f"{label}.axis_scale_difference_pct", block.get("axis_scale_difference_pct"),
             (sy - sx) / ((sx + sy) / 2) * 100, TOL_PCT)

    # T-1091. The fit in force is fitted on eleven points and only eight of them are in
    # this file; the other three are named by fit.control.extra_points_file, and a gate
    # that scored the fit on the eight alone would demand the wrong RMS and would go
    # quiet the moment somebody dropped the corners out of the control.
    extra = []
    extra_path = ((fit.get("control") or {}).get("extra_points_file") or "").strip()
    if extra_path:
        ep = ROOT / extra_path
        if not ep.exists():
            bad.append(f"fit.control.extra_points_file: {extra_path} is not committed")
        else:
            extra = (json.loads(ep.read_text()).get("corners") or [])
            if not extra:
                bad.append(f"fit.control.extra_points_file: {extra_path} names no corners")
    stated_points = (fit.get("control") or {}).get("points")
    if stated_points is not None and stated_points != len(gcps) + len(extra):
        bad.append(f"fit.control.points: committed {stated_points} != "
                   f"{len(gcps) + len(extra)} points actually in the control")

    if sorted(coeffs) != list("abcdef"):
        bad.append(f"fit.coefficients: {sorted(coeffs)} is not a,b,c,d,e,f")
    elif not gcps:
        bad.append("the registration carries no control points")
    else:
        def residual(point, coefficients):
            px, py = point["pixel"]
            east, north = _apply(coefficients, px, py)
            modern = point.get("modern") or {}
            return math.hypot(east - modern["utm_e"], north - modern["utm_n"])

        residuals = []
        for g in gcps:
            r = residual(g, coeffs)
            residuals.append(r)
            near(f"gcp {g.get('id')} residual_m", g.get("residual_m"), r, TOL_RESIDUAL_M)
        corner_residuals = []
        for c in extra:
            r = residual(c, coeffs)
            corner_residuals.append(r)
            near(f"control point {c.get('id')} residual_m", c.get("residual_m"), r,
                 TOL_RESIDUAL_M)
        near("fit.rms_m", fit.get("rms_m"), _rms(residuals + corner_residuals),
             TOL_RESIDUAL_M)
        # Held apart on purpose: the eleven-point fit costs 2.20 m of RMS on the eight
        # it was refitted from, and that price is the whole argument of the adoption.
        # Averaged into one number it disappears.
        if "rms_m_on_the_eight" in fit:
            near("fit.rms_m_on_the_eight", fit["rms_m_on_the_eight"], _rms(residuals),
                 TOL_RESIDUAL_M)
        if "rms_m_on_the_three_corners" in fit and corner_residuals:
            near("fit.rms_m_on_the_three_corners", fit["rms_m_on_the_three_corners"],
                 _rms(corner_residuals), TOL_RESIDUAL_M)

        shape("fit", fit)

        # ---- the superseded fit, kept because things are still carried through it --
        retained = doc.get("retained_fit") or {}
        if retained:
            rc = retained.get("coefficients") or {}
            if sorted(rc) != list("abcdef"):
                bad.append(f"retained_fit.coefficients: {sorted(rc)} is not a,b,c,d,e,f")
            else:
                if rc == coeffs:
                    bad.append("retained_fit.coefficients: identical to the fit in "
                               "force, so nothing is actually retained")
                kept = []
                for g in gcps:
                    r = residual(g, rc)
                    kept.append(r)
                    near(f"gcp {g.get('id')} residual_m_in_retained_8pt_fit",
                         g.get("residual_m_in_retained_8pt_fit"), r, TOL_RESIDUAL_M)
                near("retained_fit.rms_m", retained.get("rms_m"), _rms(kept),
                     TOL_RESIDUAL_M)
                shape("retained_fit", retained)

    # ---- the two scans ----------------------------------------------------
    s2s = doc.get("scan_to_scan") or {}
    s_coeffs = s2s.get("coefficients") or {}
    if sorted(s_coeffs) != list("abcdef"):
        bad.append(f"scan_to_scan.coefficients: {sorted(s_coeffs)} is not a,b,c,d,e,f")
    elif gcps:
        departures = []
        for g in gcps:
            bx, by = g["bpl_pixel"]
            x, y = _apply(s_coeffs, bx, by)
            px, py = g["pixel"]
            r = math.hypot(x - px, y - py)
            departures.append((r, g.get("id")))
            near(f"gcp {g.get('id')} scan_to_scan_residual_px",
                 g.get("scan_to_scan_residual_px"), r, TOL_PX)
        near("scan_to_scan.rms_px", s2s.get("rms_px"),
             _rms(r for r, _ in departures), TOL_PX)
        worst_px, worst_id = max(departures)
        stated = s2s.get("max_departure") or {}
        if stated.get("gcp") != worst_id:
            bad.append(f"scan_to_scan.max_departure.gcp: committed {stated.get('gcp')!r} "
                       f"!= {worst_id!r}, which is where the two scans now disagree most")
        near("scan_to_scan.max_departure.px", stated.get("px"), worst_px, TOL_PX)

    # ---- the sheet's own scale bar ---------------------------------------
    for key, bar in sorted((doc.get("scale_bar") or {}).items()):
        if not isinstance(bar, dict) or "tick_px" not in bar:
            continue
        ticks = bar["tick_px"]
        feet = [float(k) for k in ticks]
        cols = [float(v) for v in ticks.values()]
        slope, intercept = _least_squares_line(feet, cols)
        near(f"scale_bar.{key}.fit_px_per_foot", bar.get("fit_px_per_foot"),
             abs(slope), TOL_PX_PER_FOOT)
        near(f"scale_bar.{key}.m_per_px", bar.get("m_per_px"),
             FEET_TO_M / abs(slope), TOL_SCALE)
        if bar.get("fit_residual_rms_px") is not None:
            near(f"scale_bar.{key}.fit_residual_rms_px", bar["fit_residual_rms_px"],
                 _rms(c - (slope * f + intercept) for f, c in zip(feet, cols)), 0.05)

    # ---- the lost paper ---------------------------------------------------
    lac = (doc.get("lacunae") or {}).get("found") or []
    if coeffs and sorted(coeffs) == list("abcdef"):
        sx = math.hypot(coeffs["a"], coeffs["d"])
        sy = math.hypot(coeffs["b"], coeffs["e"])
        for box in lac:
            x0, y0, x1, y1 = box["box"]
            if x1 <= x0 or y1 <= y0:
                bad.append(f"lacuna {box.get('id')}: box {box['box']} is not ordered "
                           "[x_min, y_min, x_max, y_max]")
                continue
            # Inclusive pixel counts, which is what the committed extents are on.
            want = [round((x1 - x0 + 1) * sx), round((y1 - y0 + 1) * sy)]
            if box.get("ground_extent_m") != want:
                bad.append(f"lacuna {box.get('id')} ground_extent_m: committed "
                           f"{box.get('ground_extent_m')} != {want} from its box")

    for line in skipped:
        print("SKIP", line)
    for line in bad:
        print("FAIL", line)
    if not bad:
        print(f"OK   the Wright NARA registration re-derives "
              f"({len(gcps) + len(extra)} control points, rms {fit.get('rms_m')} m, "
              f"{len(lac)} lacunae"
              + (f", retained 8pt fit rms {doc['retained_fit'].get('rms_m')} m"
                 if doc.get("retained_fit") else "") + ")"
              + (f" — {len(skipped)} raster assertion(s) skipped" if skipped else ""))
    return 1 if bad else 0


def self_test() -> int:
    """The gate's own assertions still fire when the registration is broken.

    In memory, against a copy: this file must never write to the record it gates.
    Each case names the clause it expects to be refused by, so a gate that goes
    quiet on one of them fails here rather than passing a mutated fit.
    """
    import contextlib
    import io

    doc = json.loads(GCPS.read_text())
    source = json.loads(SOURCE.read_text())

    def set_coeff(d, key, value):
        d["fit"]["coefficients"][key] = value

    cases = [
        ("a nudged affine coefficient",
         lambda d, s: set_coeff(d, "a", d["fit"]["coefficients"]["a"] + 1e-4),
         "fit.scale_m_per_px.x"),
        ("a hand-edited residual on one control point",
         lambda d, s: d["gcps"][3].update(residual_m=1.0),
         "gcp G4 residual_m"),
        ("an RMS that no longer matches the residuals",
         lambda d, s: d["fit"].update(rms_m=4.0),
         "fit.rms_m"),
        ("a rotation that does not come out of the coefficients",
         lambda d, s: d["fit"].update(rotation_deg=0.0),
         "fit.rotation_deg"),
        ("a mutated scan-to-scan coefficient",
         lambda d, s: d["scan_to_scan"]["coefficients"].update(c=0.0),
         "scan_to_scan.rms_px"),
        ("the wrong point named as the worst departure",
         lambda d, s: d["scan_to_scan"]["max_departure"].update(gcp="G1"),
         "max_departure.gcp"),
        ("a moved tick column on the scale bar",
         lambda d, s: d["scale_bar"]["nara_hup"]["tick_px"].update({"600": 2700}),
         "scale_bar.nara_hup.fit_residual_rms_px"),
        ("a lacuna's ground extent talked up",
         lambda d, s: d["lacunae"]["found"][0].update(ground_extent_m=[200, 400]),
         "lacuna L1 ground_extent_m"),
        ("a checksum edited in the registration",
         lambda d, s: d["raster"].update(sha256="0" * 64),
         "raster.sha256"),
        ("the raster's declared size disagreeing with the sheet",
         lambda d, s: d["raster"].update(width=4204),
         "raster.width"),
        ("the duplicate claim pointed at a file that is not the same scan",
         lambda d, s: d["raster"].update(
             duplicate_in_repository="chicago/4d/tools/check.sh is byte-identical to it"),
         "NOT byte-identical"),
        ("a source locator that has drifted from the registration",
         lambda d, s: s.update(locator="a working copy somewhere, 600 dpi"),
         "locator no longer says"),
        ("two control points minted with one id",
         lambda d, s: d["gcps"][1].update(id="G1"),
         "distinct ids"),
        # T-1091's four: the eleven-point fit, its two split RMS figures, and the
        # retained eight-point block that seated traces are still carried through.
        ("the three foot-control corners dropped out of the stated control",
         lambda d, s: d["fit"]["control"].update(points=8),
         "fit.control.points"),
        ("the price the adoption paid on the original eight talked down",
         lambda d, s: d["fit"].update(rms_m_on_the_eight=16.19),
         "fit.rms_m_on_the_eight"),
        ("a nudged coefficient in the retained fit",
         lambda d, s: d["retained_fit"]["coefficients"].update(e=-0.73),
         "retained_fit.rms_m"),
        ("the retained fit quietly replaced by the one in force",
         lambda d, s: d["retained_fit"].update(
             coefficients=copy.deepcopy(d["fit"]["coefficients"])),
         "nothing is actually retained"),
        ("a hand-edited residual under the retained fit",
         lambda d, s: d["gcps"][0].update(residual_m_in_retained_8pt_fit=1.0),
         "residual_m_in_retained_8pt_fit"),
    ]

    failures = 0
    for label, break_it, wanted in cases:
        broken = copy.deepcopy(doc)
        broken_source = copy.deepcopy(source)
        break_it(broken, broken_source)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check_properties(broken, broken_source)
        out = buf.getvalue()
        if rc == 0 or wanted not in out:
            print(f"  FAIL the gate does not catch {label} (wanted {wanted!r})")
            failures += 1
        else:
            print(f"  caught: {label}")

    # ...and it stays green on the committed record, so the cases above are
    # measuring the mutation rather than a gate that refuses everything.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = check_properties(copy.deepcopy(doc), copy.deepcopy(source))
    if rc != 0:
        print("  FAIL the gate refuses the committed registration")
        print(buf.getvalue().rstrip())
        failures += 1

    if failures:
        return 1
    print("  self-test: OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-properties", action="store_true",
                    help="hold the committed registration to its own arithmetic — "
                         "no numpy, no network; this is the half tools/check.sh runs")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the assertions above still fire when broken")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check_properties:
        return check_properties()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
