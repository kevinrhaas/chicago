#!/usr/bin/env python3
"""T-2871: where is the north tower's finial, and does HABS 14's 27 px say the plan is wrong?

On HABS 14's re-solved camera (T-2850/T-2855) the model's finial tip lands about 27 px
image-right of the photograph's, while HABS 01 holds it within about 2 px. A joint fit
of the two tips alone puts the tip near W 39.7 / S 8.6, which a drum of radius about
8.6 ft, still tangent to 18th Street and still ending at W 48.3, would carry. This
reads the question three ways before anything is built:

1. THE TIP, picked by rule (the topmost dark row of the finial against the sky, its
   centroid), projected through both committed cameras and triangulated from them.
2. THE CONE'S WIDTH in HABS 01, whose camera was fitted with the tower EXCLUDED
   (habs-01-northwest.json solve.method), so it can measure the tower without having
   been bent to it. The cone stands against open sky in rows 10-34 px below the tip,
   clear of the stack to its right and the roofs to its left; both silhouette edges
   are read row by row at the sky/slate midpoint. A wider drum carries a wider cone:
   its width is a reading of the eave radius that the tip cannot give.
3. HABS 14'S OWN DEPTH. Every control in that camera lies in the north wall's plane
   except two model-derived off-plane points (the stack crest and the "tower depth"
   control), which it misses by about 15 px each; its eye sits on the 2.5 m bound.
   The camera is re-solved with tools/glessner_north_pairs.py's own solve, those two
   controls dropped in turn, and the as-built tip projected through each: the spread
   is how far this camera can be trusted off the wall's plane.

  python3 tools/glessner_north_finial_read.py          write data/comparisons/glessner/north-finial.json
  python3 tools/glessner_north_finial_read.py --check  exit 1 if stale, or if the record's tower stands
                                                       outside what the reading allows
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glessner_north_pairs as pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/comparisons/glessner/north-finial.json"
RECORD = ROOT / "data/structures/glessner_house.json"
VIEWS = ROOT / "data/reference_views/glessner_house"
FT = 0.3048
WEST_END_W = 48.3  # the drum's west extreme as built (W 41 + 7.35); both readings keep it
TIP_TOLERANCE_PX = 5.0  # HABS 01, the camera fitted without the tower, holds the built tip to 3
SHAPE_TOLERANCE_PX = 1.0  # the built cone's silhouette fit may be this much worse than the best
STALE_TOLERANCE = 0.5  # px, ft or ratio: another machine's JPEG decode and BLAS land a little apart
DARK = 110         # finial/cone against sky: the sky reads ~240, the backlit slate ~60
EDGE = 150         # the silhouette edge: midway between sky and slate
# Search windows (x0, y0, x1, y1) for the tip. Picked once by eye, then read by rule.
TIP_WINDOW = {"habs-01-northwest": (410, 440, 450, 475), "habs-14-north-inclined": (1295, 345, 1320, 362)}  # right of the pole
# Where the cone's silhouette stands clear against sky, as rows below each photograph's
# own tip: below the finial (HABS 01 ~8 px tall, HABS 14 ~11) and above whatever crosses
# it (HABS 01: the roofs at left from row 495, the stack at right from column 474;
# HABS 14: the pole and its lamp arm cover the cone's LEFT edge, so only the right is read).
EDGE_ROWS = {"habs-01-northwest": (12, 34), "habs-14-north-inclined": (14, 104)}
EDGE_SPAN = {"habs-01-northwest": (385, 470), "habs-14-north-inclined": (None, 1440)}
SCALES = np.round(np.arange(0.70, 1.401, 0.02), 2)  # the upper cone's base radius, as a share of the built
MODEL_ROWS = (4, 26)  # the model's rows below ITS cone apex, the same count of rows


def form():
    return json.loads(RECORD.read_text())["phases"][0]["form"]


def tower():
    f = form()
    t, pl = f["tower_north"]["value"], f["tower_north_plan"]["value"]
    prof = f["v4_detail"]["value"]["north_tower_roof"]["flare_profile_ft"]
    dr, dz = prof[-1]
    return {"W": pl["centre_W"], "S": pl["centre_S"], "r": pl["r_ft"], "eave_r": pl["eave_r_ft"],
            "cone_base_r": pl["eave_r_ft"] - dr, "cone_base_z": t["wall_top"][0] + dz,
            "apex_z": t["apex"][0], "tip_z": t["apex"][0] + t["finial_ft"]}


def camera(name):
    c = json.loads((VIEWS / f"{name}.json").read_text())
    if "basis_right_up_forward" in c:
        b = np.array(c["basis_right_up_forward"])
    else:  # HABS 01 is a level camera stored by yaw alone (tools/glessner_north_tower_review.py)
        a = math.radians(c["yaw_deg"])
        b = np.array([[math.cos(a), -math.sin(a), 0], [0, 0, 1], [math.sin(a), math.cos(a), 0]])
    return {"eye": np.array(c["eye"]), "basis": b, "f": c["focal_px"], "c": np.array(c["principal_px"]),
            "photo": (VIEWS / c["photo"]).resolve()}


def project(cam, pts_ft):
    xyz = np.array([pairs.metric(*p) for p in np.atleast_2d(pts_ft)])
    q = (xyz - cam["eye"]) @ cam["basis"].T
    return np.column_stack((cam["c"][0] + cam["f"] * q[:, 0] / q[:, 2], cam["c"][1] - cam["f"] * q[:, 1] / q[:, 2]))


def grey(cam):
    return np.asarray(Image.open(cam["photo"]).convert("L")).astype(float)


def read_tip(img, window):
    x0, y0, x1, y1 = window
    sub = img[y0:y1, x0:x1] < DARK
    rows = np.flatnonzero(sub.any(axis=1))
    top = rows[0]
    band = sub[top:top + 3]
    ys, xs = np.nonzero(band)
    return [round(float(x0 + xs.mean()), 1), round(float(y0 + top), 1)]


def crossing(row, lo, hi, step):
    """Sub-pixel column where the row first crosses EDGE walking from lo toward hi."""
    for x in range(lo, hi, step):
        a, b = row[x], row[x + step]
        if (a - EDGE) * (b - EDGE) <= 0 and a != b:
            return x + step * (a - EDGE) / (a - b)
    return None


def read_edges(img, tip, name):
    """[row, left or None, right] where the cone's silhouette meets the sky."""
    out = []
    (r0, r1), (lo, hi) = EDGE_ROWS[name], EDGE_SPAN[name]
    for dy in range(r0, r1 + 1, 2):
        y = int(round(tip[1])) + dy
        row = img[y]
        left = crossing(row, lo, int(tip[0]), 1) if lo is not None else None
        right = crossing(row, hi, int(tip[0]), -1)
        out.append([y, None if left is None else round(float(left), 2), round(float(right), 2)])
    return out


def slope(rows, values):
    """Pixels of column per pixel of row, least squares."""
    return float(np.polyfit(np.asarray(rows, float), np.asarray(values, float), 1)[0])


def photo_slopes(edges):
    e = np.array([[y, l if l is not None else np.nan, r] for y, l, r in edges], float)
    out = {"right_edge": slope(e[:, 0], e[:, 2])}
    if not np.isnan(e[:, 1]).any():
        out["width"] = slope(e[:, 0], e[:, 2] - e[:, 1])
    return out


def model_slopes(cam, t):
    apex_v = project(cam, [[t["W"], t["S"], t["apex_z"]]])[0][1]
    rows = np.arange(apex_v + MODEL_ROWS[0], apex_v + MODEL_ROWS[1] + 1, 2)
    m = model_edges(cam, t, rows)
    return {"right_edge": slope(rows, m[:, 1]), "width": slope(rows, m[:, 1] - m[:, 0])}


def cone_points(t, n_z=240, n_a=720):
    z = np.linspace(t["cone_base_z"], t["apex_z"], n_z)
    r = t["cone_base_r"] * (t["apex_z"] - z) / (t["apex_z"] - t["cone_base_z"])
    a = np.linspace(0, 2 * math.pi, n_a, endpoint=False)
    W = t["W"] + np.outer(r, np.cos(a)).ravel()
    S = t["S"] + np.outer(r, np.sin(a)).ravel()
    return np.column_stack((W, S, np.repeat(z, n_a)))


def model_edges(cam, t, rows):
    uv = project(cam, cone_points(t))
    out = []
    for y in rows:
        sel = uv[np.abs(uv[:, 1] - y) < 0.5]
        out.append([float(sel[:, 0].min()), float(sel[:, 0].max())] if len(sel) else [np.nan, np.nan])
    return np.array(out)


def shape_fit(cam, t, edges):
    """The cone's SIZE from its silhouette alone. For each scale of the upper cone's base
    radius (rise, centre and height kept), the model's edges are slid freely in the image
    (du, dv: the camera's offset and the finial's length both drop out) onto the
    photograph's; returns {scale: rms px}."""
    e = np.array([[y, l if l is not None else np.nan, r] for y, l, r in edges], float)
    out = {}
    for k in SCALES:
        tk = dict(t, cone_base_r=t["cone_base_r"] * k)
        uv = project(cam, cone_points(tk, n_z=200, n_a=360))
        top = math.floor(uv[:, 1].min())
        rows = np.arange(top, top + 260)
        idx = np.clip(np.round(uv[:, 1]).astype(int) - top, 0, len(rows) - 1)
        lo = np.full(len(rows), np.inf); hi = np.full(len(rows), -np.inf)
        np.minimum.at(lo, idx, uv[:, 0]); np.maximum.at(hi, idx, uv[:, 0])
        ok = np.isfinite(lo)
        rows, lo, hi = rows[ok], lo[ok], hi[ok]

        def res(x):
            v = e[:, 0] - x[1]
            r = [np.interp(v, rows, hi) + x[0] - e[:, 2]]
            if not np.isnan(e[:, 1]).any():
                r.append(np.interp(v, rows, lo) + x[0] - e[:, 1])
            return np.concatenate(r)
        x0 = [e[0, 2] - np.interp(e[0, 0], rows, hi), 0.0]
        fit = least_squares(res, x0, diff_step=1e-3)
        out[float(k)] = round(float(np.sqrt(np.mean(fit.fun ** 2))), 3)
    return out


def with_plan(base, W, S, eave_r):
    t = dict(base)
    over = base["eave_r"] - base["r"]
    t.update(W=W, S=S, eave_r=eave_r, r=eave_r - over, cone_base_r=eave_r - (base["eave_r"] - base["cone_base_r"]))
    return t


def tangent_plan(base, r):
    """Tangent to 18th Street (S 0), west extreme held at W 48.3, the built overhang kept."""
    return with_plan(base, WEST_END_W - r, r, r + base["eave_r"] - base["r"])


def evaluate(t, cams, tips, slopes):
    """Tip residuals in both views; the cone's slope against the photograph's, as a ratio
    (model / photograph: above 1 the model's cone is wider than the picture's)."""
    out = {}
    for name, cam in cams.items():
        uv = project(cam, [[t["W"], t["S"], t["tip_z"]]])[0]
        ms = model_slopes(cam, t)
        out[name] = {"tip_px": [round(float(v), 1) for v in uv],
                     "tip_residual_px": round(float(np.linalg.norm(uv - tips[name])), 1),
                     "tip_du_dv_px": [round(float(v), 1) for v in uv - tips[name]],
                     "cone_slope_ratio": {k: round(ms[k] / v, 3) for k, v in slopes[name].items()}}
    return out


def habs14_variants(t):
    """HABS 14 re-solved by tools/glessner_north_pairs.py with its off-plane controls varied."""
    image, seed, fixed, pr = pairs.controls()["habs-14-north-inclined"]
    out = {}
    for label, depth in [("both off-plane controls (committed)", pairs.DEPTH14),
                         ("stack crest only", pairs.DEPTH14[:1]),
                         ("tower-depth only", pairs.DEPTH14[1:])]:
        opt, err, f, c = pairs.solve(image, seed, fixed + depth, pr, free_principal=True)
        cam = {"eye": opt.x[:3], "basis": pairs.basis(*opt.x[3:6]), "f": f, "c": c}
        uv = project(cam, [[t["W"], t["S"], t["tip_z"]]])[0]
        out[label] = {"tip_px": [round(float(v), 1) for v in uv], "eye_m": [round(float(v), 2) for v in opt.x[:3]],
                      "focal_px": round(float(f), 1), "rms_px": round(float(np.sqrt(np.mean(err ** 2))), 2),
                      "sill_head_ft": [round(float(opt.x[7]), 2), round(float(opt.x[8]), 2)]}
    us = [v["tip_px"][0] for v in out.values()]
    return out, round(float(max(us) - min(us)), 1)


def derive():
    base = tower()
    names = ["habs-01-northwest", "habs-14-north-inclined"]
    cams = {n: camera(n) for n in names}
    imgs = {n: grey(cams[n]) for n in names}
    tips = {n: np.array(read_tip(imgs[n], TIP_WINDOW[n])) for n in names}
    edges = {n: read_edges(imgs[n], tips[n], n) for n in names}
    slopes = {n: photo_slopes(edges[n]) for n in names}

    # The tip triangulated from the two photographs' tips alone: the built height held,
    # then let free.
    def tip_res(x, z=None):
        p = [x[0], x[1], x[2] if z is None else z]
        return np.concatenate([project(cams[n], [p])[0] - tips[n] for n in names])
    held = least_squares(lambda x: tip_res(x, base["tip_z"]), [base["W"], base["S"]])
    free = least_squares(tip_res, [base["W"], base["S"], base["tip_z"]])

    # The tangent family: one radius r, centre (W 48.3 - r, S r), the built overhang and
    # flare kept, so the cone scales with the drum.
    family = []
    for r in np.round(np.arange(6.5, 10.01, 0.5), 2):
        t = tangent_plan(base, r)
        ev = evaluate(t, cams, tips, slopes)
        family.append({"r_ft": float(r), "centre_WS_ft": [round(float(t["W"]), 2), round(float(t["S"]), 2)],
                       "tip_residual_px": {n: ev[n]["tip_residual_px"] for n in names},
                       "cone_slope_ratio": {n: ev[n]["cone_slope_ratio"] for n in names}})

    variants, spread = habs14_variants(base)
    proposal = tangent_plan(base, WEST_END_W - 39.7)
    shape = {}
    for n in names:
        curve = shape_fit(cams[n], base, edges[n])
        best = min(curve, key=curve.get)
        near = [k for k, v in curve.items() if v <= curve[best] + 0.5]
        shape[n] = {"best_scale": best, "best_rms_px": curve[best],
                    "within_half_px_of_best": [min(near), max(near)],
                    "built_rms_px": curve[1.0],
                    "proposal_rms_px": curve[min(curve, key=lambda k: abs(k - proposal["cone_base_r"] / base["cone_base_r"]))],
                    "implied_eave_r_ft": round(base["cone_base_r"] * best + base["eave_r"] - base["cone_base_r"], 2)}
    r2 = lambda v: round(float(v), 2)
    return {
        "ticket": "T-2871",
        "not_a_reading": "No new archival source. The tips and the cone's silhouette edges are read by rule from the committed HABS photographs 1 and 14; the cameras are the committed ones, and HABS 14's re-solves use tools/glessner_north_pairs.py's own picks and solve.",
        "method": ("Tip: topmost row darker than %d in a fixed window, centroid of its dark pixels over three rows. "
                   "Cone: rows below each photograph's tip where the silhouette stands against sky, crossings at grey %d; "
                   "the slope of the cone's width (HABS 01, both edges) and of its right edge (HABS 14, the pole covers the left) "
                   "in pixels per row, against the model cone's at the same number of rows below its own apex, so the finial's "
                   "length does not enter. Fits are least squares in pixels." % (DARK, EDGE)),
        "photograph": {n: {"tip_px": tips[n].tolist(), "edges_px": edges[n],
                           "slope_px_per_row": {k: round(v, 3) for k, v in slopes[n].items()}} for n in names},
        "built": {"plan_WS_ft": [base["W"], base["S"]], "r_ft": base["r"], "eave_r_ft": base["eave_r"],
                  "tip_z_ft": base["tip_z"], "views": evaluate(base, cams, tips, slopes)},
        "tips_triangulated": {"height_held_WS_ft": [r2(held.x[0]), r2(held.x[1])],
                              "height_held_residual_px": [r2(v) for v in np.linalg.norm(held.fun.reshape(-1, 2), axis=1)],
                              "free_WSz_ft": [r2(v) for v in free.x],
                              "free_residual_px": [r2(v) for v in np.linalg.norm(free.fun.reshape(-1, 2), axis=1)]},
        "tangent_family": family,
        "cone_size_from_silhouette": shape,
        "proposal_W39_7": {"plan_WS_ft": [r2(proposal["W"]), r2(proposal["S"])], "r_ft": r2(proposal["r"]),
                           "eave_r_ft": r2(proposal["eave_r"]), "views": evaluate(proposal, cams, tips, slopes)},
        "habs14_camera_variants": variants,
        "habs14_built_tip_spread_px": spread,
    }


def close(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= STALE_TOLERANCE
    return a == b


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    result = derive()
    if a.check:
        if not OUT.exists() or not close(json.loads(OUT.read_text()), result):
            print("FAIL: north-finial.json is stale; run python3 tools/glessner_north_finial_read.py")
            return 1
    elif not OUT.exists() or not close(json.loads(OUT.read_text()), result):
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    # The ruling: the plan the record builds must keep HABS 01's tip and stand inside the
    # cone sizes HABS 01's silhouette allows. A plan moved to HABS 14's tip alone fails here.
    h01 = result["built"]["views"]["habs-01-northwest"]["tip_residual_px"]
    shape = result["cone_size_from_silhouette"]["habs-01-northwest"]
    worse = shape["built_rms_px"] - shape["best_rms_px"]
    if h01 > TIP_TOLERANCE_PX or worse > SHAPE_TOLERANCE_PX:
        print(f"FAIL: the record's north tower puts HABS 01's tip {h01} px off (allowed {TIP_TOLERANCE_PX}), or its "
              f"cone fits HABS 01's silhouette {worse:.2f} px worse than the best size (allowed {SHAPE_TOLERANCE_PX}) (T-2872)")
        return 1
    b, t, c = result["built"]["views"], result["tips_triangulated"], result["cone_size_from_silhouette"]
    print(f"built tip: HABS 01 {b['habs-01-northwest']['tip_residual_px']} px, HABS 14 {b['habs-14-north-inclined']['tip_residual_px']} px; "
          f"tips alone triangulate W {t['height_held_WS_ft'][0]} / S {t['height_held_WS_ft'][1]}; "
          f"HABS 14's camera moves the built tip {result['habs14_built_tip_spread_px']} px across its re-solves; "
          f"the cone's size from its silhouette: HABS 01 {c['habs-01-northwest']['best_scale']} "
          f"({c['habs-01-northwest']['within_half_px_of_best']}), HABS 14 {c['habs-14-north-inclined']['best_scale']} of the built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
