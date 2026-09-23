#!/usr/bin/env python3
"""What the wash is, between Wright's grey bank shading and his inked bank line
on the North Branch reach — read against the legend's own swatches (T-1082).

    tools/read_north_branch_bank_wash.py --build             re-read both rasters, rewrite the record
    tools/read_north_branch_bank_wash.py --check-properties  the gate: offline, re-derives every number
    tools/read_north_branch_bank_wash.py --report            print the reading
    tools/read_north_branch_bank_wash.py --self-test         the gate's assertions still fire when broken

THE QUESTION. `tools/trace_north_branch.py` publishes a reach whose boundary is
short of Wright's ink by more than 10 m on 51 east-bank rows (728-779) and stands
OUTSIDE it on 34 west-bank rows, in five stretches. T-1078 measured both and filed
the cause as one thing — "a coloured wash between the grey bank wash and the ink,
behind a colour the tract layer has not identified" — and T-1082 asks which of
Wright's nine surveys washed that ground, because a bank drawn over NAMED ground
is exactly the error `hue_tol` 7 exists to prevent.

THE SCAN PROBLEM, WHICH HAD TO BE SOLVED FIRST AND IS THE REASON THIS FILE EXISTS.
`tools/read_wright_legend_swatches.py` read the nine legend chips on the NATIONAL
ARCHIVES / HISTORIC URBAN PLANS facsimile (`wright_1834_nara_hup`, 5050 x 6628),
because at 600 dpi a chip is 54 px wide there. The disputed band is located on the
BOSTON PUBLIC LIBRARY master (`wright_1834`, 4204 x 5166) and nowhere else: it is
17 px wide, and the two sheets' committed affines carry 17.5 m and 16.0 m of RMS,
so transferring a 17 px feature between them costs about 33 px of positional
uncertainty — twice the feature. Neither the colours nor the position carry across:

  * POSITION. Run offline here: of the 116 coloured BANDS the facsimile reading
    committed, the nearest to ANY of these six stretches is 235 m away, and the
    nearest to the east stretch — the one the ticket was opened on — is 481 m.
    The facsimile's band map has nothing at all on this reach.
  * COLOUR. The nine chips read DIFFERENT COLOURS on the two sheets — chip 1 is
    deep blue on the facsimile (44, 65, 93) and bare paper on the master
    (213, 194, 161); chip 8 is orange-brown there (180, 112, 39) and scarlet here
    (217, 77, 64). Seven of the nine stand more than 100 RGB units apart and the
    worst pair 223. The facsimile is a REPRINT, and its publisher's inks are not
    Wright's washes.

So this file reads the nine chips AGAIN, on the master, off the same legend — and
every comparison below is then same-sheet arithmetic. It does not touch the
facsimile reading, which remains correct about the sheet it was taken from.

HOW A WASH IS MATCHED TO A CHIP, AND WHY NOT BY DISTANCE. A legend chip is a
solid swatch; the ground is the same pigment laid thin. On the master the ground
washes sit 40 to 120 RGB units from their own chip simply for being diluted, so
nearest-colour — the facsimile reading's rule, which its uniform reprint inks
justify — matches nothing here. What survives dilution is DIRECTION: a wash of
chip k over paper p lies on the ray p -> k, at a fraction t of the way along it.
So each band is projected onto every reference's ray and carries two numbers, the
perpendicular residual (is it this pigment?) and t (how thin?).

WHAT IT FINDS, and it is a correction to a committed claim. The five west
stretches are NOT one fault with the east one:

  * rows 728-779, EAST — matches nothing. No chip's ray comes within 21 RGB units,
    and the one that comes closest needs t = 3.4, which is not a dilution at all.
    It is not the reach's own bank wash either. REFUSED: the colour is not one of
    the nine, and the reading stays that the sheet does not draw a bank there.
  * rows 707-710, 715-717 and 948-951, WEST — the reach's OWN GREY BANK WASH,
    residual 2.3 to 6.5 and t 1.05 to 1.19: Wright's bank shading laid a little
    heavier, not a colour. These three are not the fault T-1078 filed.
  * rows 922-939, WEST — a legend wash, residual 6.4 at t 0.40, of the master's
    class {3, 6, 7}. Named ground, so the boundary stays off it.
  * rows 1247-1251, WEST — three pixels on the splice row, where the boundary
    stands 0.7 m outside the ink. Refused for having nothing to read: three
    pixels, twice as dark as the bank wash (t 2.35), are an ink shoulder.

NOTHING IN THE TRACE MOVES. Every stretch either refuses identification or lands
on ground with a name, and both answers keep the boundary where it is.
docs/RESEARCH/north_branch_wabansia.md § 5 carries the outcome.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "data" / "traces" / "north_branch_bank_wash.json"
SWATCHES = ROOT / "data" / "traces" / "wright_1834_legend_swatches.json"

# ---------------------------------------------------------------------------
# the legend, on the MASTER sheet
# ---------------------------------------------------------------------------
# Found by the same argument the facsimile reading used and then frozen: the nine
# boxes are stable features of one scan, and re-finding them on every run would
# make the record depend on a threshold rather than on the paper. The column was
# located by its darkness against the margin (interior x 2682-2732, the inked
# border at 2678-2681 and 2734-2736 eroded away); the nine rows are the row runs
# of that column below luminance 205, and they are the same nine at 200 and 210.
LEGEND_REGION = (2520, 2940, 420, 700)       # the IIIF region fetched for them
CHIP_X0, CHIP_X1 = 2682, 2733                # interior, borders already eroded
CHIP_ROWS = [(3116, 3148), (3166, 3197), (3211, 3241), (3260, 3289), (3305, 3336),
             (3348, 3374), (3389, 3415), (3434, 3460), (3481, 3508)]
CHIP_EROSION_TOP, CHIP_EROSION_BOTTOM = 5, 4

# The nine stretches of the legend's wording are the facsimile reading's, unchanged
# — it is the same hand on the same sheet, and re-transcribing it here would let
# the two files drift on a question neither of them is asking.

# ---------------------------------------------------------------------------
# the rule
# ---------------------------------------------------------------------------
# Chips are grouped into separable colours at the facsimile reading's own
# threshold, so "separable" means the same thing on both sheets.
CLASS_THRESHOLD_RGB = 35.0

# A band is this pigment when its perpendicular residual from the pigment's
# dilution ray is under RAY_PERP_MAX. 12 is set by what the sheet itself spreads:
# the three stretches that land on the bank wash scatter 2.3 to 6.5 about their
# own ray, and the nearest rival ray to any of them is 10.2 away. 12 admits the
# first and excludes the second, and nothing in this file is decided in the two
# units between them.
RAY_PERP_MAX = 12.0

# ...and when t says it is a DILUTION. Below 0.05 the band is bare paper and the
# ray's direction is noise; above 1.25 it is darker than the solid swatch itself,
# which two passes of one wash can just reach and a different, darker thing is the
# likelier reading. Both ends are refusals, not adjustments.
T_MIN, T_MAX = 0.05, 1.25

# An assignment names the CLASS, never the chip: the classes are exactly what the
# chips can separate, and the facsimile reading refuses the same way (its § on the
# two ambiguous swatches). A band under RAY_PERP_MAX of chip 3's ray is a band of
# class {3, 6, 7} and this file says no more than that.

# The six stretches, from the committed baseline of tools/measure_north_branch_banks.py
# (`after.east.stretches` and `after.west.outside_stretches`). They are read here,
# not re-declared, so a re-measure that moves them cannot leave this file behind.
BASELINE = ROOT / "tools" / "north_branch_bank_baseline.json"


# ---------------------------------------------------------------------------
# arithmetic — shared by --build and --check-properties, so the gate re-derives
# the same numbers the build wrote rather than a second implementation of them
# ---------------------------------------------------------------------------

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dist_rgb(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def classes_from(medians):
    """Single-link grouping at CLASS_THRESHOLD_RGB, 1-based, sorted — the
    facsimile reading's grouping, by the same threshold on this sheet's chips."""
    n = len(medians)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if dist_rgb(medians[i], medians[j]) < CLASS_THRESHOLD_RGB:
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i + 1)
    return sorted(groups.values())


def ray(sample, paper, ref):
    """Project a band's colour onto the ray paper -> ref. Returns (perp, t)."""
    d = [ref[i] - paper[i] for i in range(3)]
    dd = sum(v * v for v in d)
    if dd == 0:
        return float("inf"), 0.0
    s = [sample[i] - paper[i] for i in range(3)]
    t = sum(s[i] * d[i] for i in range(3)) / dd
    perp = sum((s[i] - t * d[i]) ** 2 for i in range(3)) ** 0.5
    return perp, t


def rank_rays(sample, paper, refs):
    """Every reference, worst residual last. `refs` is an ordered [(name, rgb)]."""
    out = [{"ref": name, "perp": round(p, 1), "t": round(t, 2)}
           for name, (p, t) in ((n, ray(sample, paper, c)) for n, c in refs)]
    out.sort(key=lambda r: (r["perp"], r["ref"]))
    return out


def verdict(rays, classes, n_px):
    """The stated rule, applied. Returns (identified_as, why)."""
    if n_px < 20:
        return None, f"too few pixels to read a colour from ({n_px})"
    best = rays[0]
    if best["perp"] >= RAY_PERP_MAX:
        return None, (f"no reference's ray comes within {RAY_PERP_MAX:g} RGB units "
                      f"(nearest {best['ref']} at {best['perp']})")
    if not (T_MIN < best["t"] <= T_MAX):
        return None, (f"{best['ref']} is the nearest ray at {best['perp']}, but t "
                      f"{best['t']} is outside ({T_MIN:g}, {T_MAX:g}] — not a dilution")
    if best["ref"] == "bank_wash":
        return "bank_wash", (f"the reach's own grey bank wash, residual {best['perp']} "
                             f"at t {best['t']}")
    chip = int(best["ref"][len("chip"):])
    group = next(g for g in classes if chip in g)
    return ("class " + "+".join(str(c) for c in group),
            f"a legend wash of class {group}, residual {best['perp']} at t {best['t']}")


def band_box_distance_m(box, e, n):
    de = max(box["e0"] - e, 0.0, e - box["e1"])
    dn = max(box["n0"] - n, 0.0, n - box["n1"])
    return (de * de + dn * dn) ** 0.5


def nearest_facsimile_band(swatches, e, n):
    best = None
    for grp in swatches["bands_by_class"]:
        for b in grp["bands"]:
            d = band_box_distance_m(b["box_local_m"], e, n)
            if best is None or d < best[0]:
                best = (d, grp["class"])
    return {"distance_m": round(best[0], 1), "class": best[1]}


def stretches_from_baseline():
    b = load(BASELINE)["after"]
    out = [("east", tuple(s)) for s in b["east"]["stretches"]]
    out += [("west", tuple(s)) for s in b["west"]["outside_stretches"]]
    return out


# ---------------------------------------------------------------------------
# --build — the only half that opens a raster
# ---------------------------------------------------------------------------

def build() -> int:
    try:
        import numpy as np
        from scipy import ndimage as ndi
        from PIL import Image
    except ImportError as exc:
        print(f"SKIP --build: {exc} (pip install numpy scipy pillow)", file=sys.stderr)
        return 3
    import hashlib
    import io
    import urllib.request

    sys.path.insert(0, str(ROOT / "tools"))
    import trace_north_branch as tnb  # noqa: PLC0415
    import trace_river as tr  # noqa: PLC0415
    import measure_north_branch_banks as mnb  # noqa: PLC0415

    tnb.configure()
    P = tnb.PARAMS

    def fetch(region, cache):
        x, y, w, h = region
        path = Path("/tmp") / cache
        if path.exists():
            raw = path.read_bytes()
        else:
            url = f"{tr.IIIF}/{x},{y},{w},{h}/full/0/default.jpg"
            print(f"fetching {url}")
            with urllib.request.urlopen(url, timeout=180) as r:  # noqa: S310
                raw = r.read()
            path.write_bytes(raw)
        return (np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"), dtype=np.float32),
                hashlib.sha256(raw).hexdigest())

    # --- the legend, on the master -----------------------------------------
    leg, leg_sha = fetch(LEGEND_REGION, "wright_1834_legend_region.jpg")
    lx, ly = LEGEND_REGION[0], LEGEND_REGION[1]
    chips, medians = [], []
    swatches = load(SWATCHES)
    for i, (y0, y1) in enumerate(CHIP_ROWS, start=1):
        box = leg[y0 - ly + CHIP_EROSION_TOP:y1 - ly - CHIP_EROSION_BOTTOM,
                  CHIP_X0 - lx:CHIP_X1 - lx].reshape(-1, 3)
        med = [int(round(float(v))) for v in np.median(box, axis=0)]
        medians.append(med)
        chips.append({
            "chip": i,
            "legend": swatches["chips"][i - 1]["legend"],
            "box_px": {"x0": CHIP_X0, "y0": y0, "x1": CHIP_X1, "y1": y1},
            "sampled_px": int(box.shape[0]),
            "median_rgb": med,
            "sd_rgb": [round(float(v), 1) for v in box.std(axis=0)],
            "facsimile_median_rgb": swatches["chips"][i - 1]["median_rgb"],
            "against_the_facsimile_rgb": round(
                dist_rgb(med, swatches["chips"][i - 1]["median_rgb"]), 1),
        })
    groups = classes_from(medians)

    # --- the reach ----------------------------------------------------------
    coef, rms, n_gcp = tr.affine_from_gcps()
    cell_m = 0.5 * (abs(coef[0] ** 2 + coef[3] ** 2) ** 0.5
                    + abs(coef[1] ** 2 + coef[4] ** 2) ** 0.5)
    datum = load(ROOT / "data" / "datum.json")
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]
    to_utm = tr.make_to_utm(coef)
    raw, sha = tr.fetch_region(Path("/tmp") / "wright_1834_north_branch_region.jpg")
    rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB")).astype(np.float32)

    dark, tint = tr.wash_terms(rgb, np)
    ink = tr.ink_mask(rgb, np, P["ink_lum"])
    water, _ = tnb.channel(rgb, np, ndi, quiet=True)
    prof = {side: mnb.side_profile(water, ink, side, np, cell_m)
            for side in ("east", "west")}

    grey = (dark > P["dark_lo"]) & (dark < P["dark_hi"]) & (tint < P["hue_tol"])
    bank_wash_rgb = [round(float(v), 1) for v in np.median(rgb[grey], axis=0)]
    paper_all = [int(round(float(v))) for v in np.median(rgb[np.abs(dark) < 8], axis=0)]

    refs = [(f"chip{c['chip']}", c["median_rgb"]) for c in chips]
    refs.append(("bank_wash", bank_wash_rgb))

    out = []
    for side, (r0, r1) in stretches_from_baseline():
        pts = []
        for y in range(r0, r1 + 1):
            v = prof[side].get(y)
            if not v:
                continue
            b, ink_x = v[0], v[1]
            for x in range(min(b, ink_x) + 1, max(b, ink_x)):
                if not ink[y, x]:
                    pts.append((y, x))
        if not pts:
            out.append({"side": side, "rows": [r0, r1], "band_px": 0,
                        "identified_as": None, "why": "no band between boundary and ink"})
            continue
        ys = np.array([p[0] for p in pts])
        xs = np.array([p[1] for p in pts])
        y0, y1 = max(0, r0 - 40), min(rgb.shape[0], r1 + 40)
        x0, x1 = max(0, int(xs.min()) - 120), min(rgb.shape[1], int(xs.max()) + 120)
        wd, win = dark[y0:y1, x0:x1], rgb[y0:y1, x0:x1]
        paper = [int(round(float(v)))
                 for v in np.median(win[np.abs(wd) < 8].reshape(-1, 3), axis=0)]
        med = [int(round(float(v))) for v in np.median(rgb[ys, xs], axis=0)]
        d, t = dark[ys, xs], tint[ys, xs]
        coloured = tr.coloured_mask(d, t, P)
        mid = float(xs.mean()) + tnb.REGION[0], float(ys.mean()) + tnb.REGION[1]
        E, N = to_utm(mid[0], mid[1])
        rays = rank_rays(med, paper, refs)
        ident, why = verdict(rays, groups, len(pts))
        out.append({
            "side": side,
            "rows": [r0, r1],
            "band_px": len(pts),
            "mean_width_px": round(len(pts) / (r1 - r0 + 1), 1),
            "centroid_px": [round(mid[0], 1), round(mid[1], 1)],
            "centroid_local_m": [round(E - o_e, 1), round(N - o_n, 1)],
            "dark": {"median": round(float(np.median(d)), 1),
                     "min": round(float(d.min()), 1), "max": round(float(d.max()), 1)},
            "tint": {"median": round(float(np.median(t)), 1),
                     "min": round(float(t.min()), 1), "max": round(float(t.max()), 1)},
            "coloured_wash_share": round(float(coloured.mean()), 2),
            "local_paper_rgb": paper,
            "median_rgb": med,
            "rays": rays,
            "identified_as": ident,
            "why": why,
            "nearest_facsimile_band": nearest_facsimile_band(
                swatches, round(E - o_e, 1), round(N - o_n, 1)),
        })

    doc = {
        "_doc": __doc__.strip(),
        "ticket": "T-1082",
        "confidence": "documented",
        "source_id": "wright_1834",
        "rasters": {
            "master": {"iiif": tr.IIIF, "width": 4204, "height": 5166,
                       "legend_region": list(LEGEND_REGION),
                       "legend_region_sha256": leg_sha,
                       "reach_region": list(tnb.REGION),
                       "reach_region_sha256": sha},
            "facsimile": {"source_id": "wright_1834_nara_hup",
                          "read_by": "tools/read_wright_legend_swatches.py",
                          "note": "cited for its chips only; not re-read here"},
        },
        "method": {
            "class_threshold_rgb": CLASS_THRESHOLD_RGB,
            "ray_perp_max_rgb": RAY_PERP_MAX,
            "t_range": [T_MIN, T_MAX],
            "min_band_px": 20,
            "chip_column_px": {"x0": CHIP_X0, "x1": CHIP_X1},
            "chip_erosion_px": {"top": CHIP_EROSION_TOP, "bottom": CHIP_EROSION_BOTTOM},
            "map_scale_m_per_px": round(cell_m, 4),
            "affine_rms_m": round(rms, 2),
            "affine_gcps": n_gcp,
        },
        "legend_chips_on_the_master": {
            "chips": chips,
            "classes": groups,
            "separation_rgb": [[round(dist_rgb(a, b), 1) for b in medians] for a in medians],
            "worst_against_the_facsimile_rgb": round(
                max(c["against_the_facsimile_rgb"] for c in chips), 1),
            "finding": (
                "The same nine chips read on the two sheets are not the same nine "
                "colours: the worst pair is more than 150 RGB units apart and chip 1 "
                "is bare paper on the master and deep blue on the facsimile. The "
                "facsimile is a reprint and its inks are the publisher's. A wash on "
                "the master must therefore be matched against THESE chips, and the "
                "facsimile reading stays correct about the sheet it was taken from."),
        },
        "reach": {
            "paper_rgb": paper_all,
            "bank_wash_rgb": bank_wash_rgb,
            "bank_wash_px": int(grey.sum()),
        },
        "stretches": out,
        "ruling": {
            "trace_changed": False,
            "statement": (
                "No stretch moves the boundary. The east stretch's colour is not one "
                "of the nine at any dilution, so the reading stays that the sheet "
                "does not draw a bank there; rows 922-939 are a legend wash, which is "
                "ground with a name and is exactly what hue_tol 7 refuses; and rows "
                "707-710, 715-717 and 948-951 are the reach's own bank wash laid "
                "heavier, where the boundary already stands outside the ink and there "
                "is nothing to carry across."),
        },
    }
    RECORD.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    named = sum(1 for s in out if s["identified_as"])
    print(f"wrote {RECORD.relative_to(ROOT)}: 9 master chips, {len(groups)} separable "
          f"colours, {len(out)} stretches, {named} identified")
    return 0


# ---------------------------------------------------------------------------
# --check-properties — offline, no raster, no network. check.sh runs this.
# ---------------------------------------------------------------------------

def check_properties(doc=None) -> int:
    doc = doc if doc is not None else load(RECORD)
    swatches = load(SWATCHES)
    bad = []

    chips = doc["legend_chips_on_the_master"]["chips"]
    medians = [c["median_rgb"] for c in chips]

    if len(chips) != 9:
        bad.append(f"legend_chips_on_the_master.chips: {len(chips)} chips, expected 9")

    # the chips are the legend's own nine, in the legend's own order
    for i, c in enumerate(chips, start=1):
        if c["chip"] != i:
            bad.append(f"chips[{i - 1}].chip: {c['chip']}, expected {i}")
        want = swatches["chips"][i - 1]["legend"]
        if c["legend"] != want:
            bad.append(f"chips[{i - 1}].legend: does not match the facsimile reading's")
        if c["facsimile_median_rgb"] != swatches["chips"][i - 1]["median_rgb"]:
            bad.append(f"chips[{i - 1}].facsimile_median_rgb: not the committed facsimile chip")
        d = round(dist_rgb(c["median_rgb"], c["facsimile_median_rgb"]), 1)
        if abs(d - c["against_the_facsimile_rgb"]) > 0.05:
            bad.append(f"chips[{i - 1}].against_the_facsimile_rgb: {c['against_the_facsimile_rgb']}, "
                       f"re-derives to {d}")

    # every pairwise separation re-derives from the committed medians
    sep = doc["legend_chips_on_the_master"]["separation_rgb"]
    for i in range(len(medians)):
        for j in range(len(medians)):
            d = round(dist_rgb(medians[i], medians[j]), 1)
            if abs(sep[i][j] - d) > 0.05:
                bad.append(f"separation_rgb[{i}][{j}]: {sep[i][j]}, re-derives to {d}")

    # ...and so does the grouping, at the committed threshold
    groups = classes_from(medians)
    if doc["legend_chips_on_the_master"]["classes"] != groups:
        bad.append(f"legend_chips_on_the_master.classes: {doc['legend_chips_on_the_master']['classes']}, "
                   f"re-derives to {groups} at {CLASS_THRESHOLD_RGB} RGB units")
    if doc["method"]["class_threshold_rgb"] != CLASS_THRESHOLD_RGB:
        bad.append("method.class_threshold_rgb: not this file's literal")

    # THE REFUSAL IS GATED. The two sheets' chips must stay far enough apart that
    # carrying the facsimile's colours onto the master is refused — if a future
    # edit ever made them agree, the whole argument for re-reading the legend
    # falls, and this says so rather than letting the file quietly keep its shape.
    worst = round(max(c["against_the_facsimile_rgb"] for c in chips), 1)
    if abs(doc["legend_chips_on_the_master"]["worst_against_the_facsimile_rgb"] - worst) > 0.05:
        bad.append("worst_against_the_facsimile_rgb: does not re-derive from the chips")
    if worst < 100.0:
        bad.append(f"the two sheets' chips now agree to within {worst} RGB units — the "
                   "reason this file re-reads the legend no longer holds")

    # the stretches are the baseline's, and nothing has been dropped or invented
    want = [[side, [a, b]] for side, (a, b) in stretches_from_baseline()]
    got = [[s["side"], s["rows"]] for s in doc["stretches"]]
    if got != want:
        bad.append(f"stretches: {got}, but the committed baseline's are {want}")

    refs = [(f"chip{c['chip']}", c["median_rgb"]) for c in chips]
    refs.append(("bank_wash", doc["reach"]["bank_wash_rgb"]))

    for s in doc["stretches"]:
        tag = f"{s['side']} {s['rows'][0]}-{s['rows'][1]}"
        if not s.get("band_px"):
            continue
        # every ray re-derives from the committed band and paper colours
        rays = rank_rays(s["median_rgb"], s["local_paper_rgb"], refs)
        if rays != s["rays"]:
            bad.append(f"{tag}: rays do not re-derive from median_rgb and local_paper_rgb")
            continue
        ident, _ = verdict(rays, groups, s["band_px"])
        if ident != s["identified_as"]:
            bad.append(f"{tag}: identified_as {s['identified_as']!r}, the rule gives {ident!r}")
        near = nearest_facsimile_band(swatches, *s["centroid_local_m"])
        if near != s["nearest_facsimile_band"]:
            bad.append(f"{tag}: nearest_facsimile_band {s['nearest_facsimile_band']}, "
                       f"re-derives to {near}")

    # THE SECOND REFUSAL, also gated: the facsimile's band map has nothing on this
    # reach, and that is why position cannot identify the wash either.
    nearest = min(s["nearest_facsimile_band"]["distance_m"] for s in doc["stretches"]
                  if s.get("band_px"))
    if nearest < 100.0:
        bad.append(f"a facsimile band now stands {nearest} m from a stretch — position "
                   "may be able to identify these washes after all, and this file says "
                   "it cannot")

    # THE EAST STRETCH IS THE TICKET'S OWN QUESTION, and its answer is a refusal.
    east = next((s for s in doc["stretches"] if s["side"] == "east"), None)
    if east is None:
        bad.append("stretches: the east stretch is missing")
    elif east["identified_as"] is not None:
        bad.append(f"east {east['rows']}: identified as {east['identified_as']!r} — T-1082's "
                   "refusal has been overturned without the research note moving with it")

    # and nothing here may claim the trace moved: it did not.
    if doc["ruling"]["trace_changed"]:
        bad.append("ruling.trace_changed: true, but this reading moves no boundary")

    if bad:
        for line in bad:
            print(f"FAIL {line}", file=sys.stderr)
        return 1
    print(f"north branch bank wash: 9 master chips in {len(groups)} separable colours, "
          f"worst {worst} RGB from the facsimile's; {len(doc['stretches'])} stretches, "
          f"nearest facsimile band {nearest} m; the east stretch stays refused")
    return 0


# ---------------------------------------------------------------------------

def report() -> int:
    doc = load(RECORD)
    m = doc["legend_chips_on_the_master"]
    print(f"Wright 1834, the MASTER sheet ({doc['rasters']['master']['iiif'].rsplit('/', 1)[-1]})")
    print(f"  paper {doc['reach']['paper_rgb']}   grey bank wash {doc['reach']['bank_wash_rgb']}"
          f"  ({doc['reach']['bank_wash_px']:,} px)\n")
    print("  the legend's nine chips, and the same nine on the facsimile:")
    for c in m["chips"]:
        print(f"    {c['chip']}  {str(c['median_rgb']):18s} vs {str(c['facsimile_median_rgb']):18s}"
              f" {c['against_the_facsimile_rgb']:6.1f} apart   {c['legend']['reading']}")
    print(f"\n  separable colours at {doc['method']['class_threshold_rgb']:g} RGB units: "
          f"{m['classes']}\n")
    for s in doc["stretches"]:
        print(f"  {s['side']:5s} rows {s['rows'][0]}-{s['rows'][1]}  "
              f"{s['band_px']:4d} px, {s.get('mean_width_px', 0)} px wide  "
              f"dark {s['dark']['median']} tint {s['tint']['median']}  {s['median_rgb']}")
        for r in s["rays"][:3]:
            print(f"        {r['ref']:10s} perp {r['perp']:6.1f}  t {r['t']:5.2f}")
        print(f"        -> {s['identified_as'] or 'NOT IDENTIFIED'}: {s['why']}")
        print(f"        nearest facsimile band {s['nearest_facsimile_band']['distance_m']} m "
              f"(class {s['nearest_facsimile_band']['class']})")
    print(f"\n  {doc['ruling']['statement']}")
    return 0


def self_test() -> int:
    """Every assertion above, shown to fire when the thing it guards is broken."""
    import copy

    base = load(RECORD)
    if check_properties(copy.deepcopy(base)) != 0:
        print("FAIL self-test: the committed record does not pass its own gate", file=sys.stderr)
        return 1

    def breaks(label, mutate):
        d = copy.deepcopy(base)
        mutate(d)
        if check_properties(d) == 0:
            print(f"FAIL self-test: {label} did not fire", file=sys.stderr)
            return 1
        return 0

    bad = 0
    bad += breaks("a chip median moved",
                  lambda d: d["legend_chips_on_the_master"]["chips"][2].__setitem__(
                      "median_rgb", [10, 10, 10]))
    bad += breaks("a pairwise separation edited",
                  lambda d: d["legend_chips_on_the_master"]["separation_rgb"][0].__setitem__(1, 0.0))
    bad += breaks("the grouping edited",
                  lambda d: d["legend_chips_on_the_master"].__setitem__("classes", [[1]]))
    bad += breaks("the two sheets made to agree",
                  lambda d: [c.__setitem__("facsimile_median_rgb", c["median_rgb"])
                             or c.__setitem__("against_the_facsimile_rgb", 0.0)
                             for c in d["legend_chips_on_the_master"]["chips"]])
    bad += breaks("a stretch dropped", lambda d: d["stretches"].pop())
    bad += breaks("a band colour moved without its verdict",
                  lambda d: d["stretches"][1].__setitem__("median_rgb", [1, 2, 3]))
    bad += breaks("the east refusal overturned",
                  lambda d: next(s for s in d["stretches"]
                                 if s["side"] == "east").__setitem__("identified_as", "class 3+6+7"))
    bad += breaks("a facsimile band moved onto the reach",
                  lambda d: d["stretches"][0]["nearest_facsimile_band"].__setitem__(
                      "distance_m", 5.0))
    bad += breaks("the ruling made to claim a trace change",
                  lambda d: d["ruling"].__setitem__("trace_changed", True))
    if bad:
        return 1
    print("self-test: the record passes its own gate, and nine breakages all fire")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.build:
        return build()
    if a.check_properties:
        return check_properties()
    if a.self_test:
        return self_test()
    return report()


if __name__ == "__main__":
    sys.exit(main())
