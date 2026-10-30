#!/usr/bin/env python3
"""Is it the Cornell camera or the stable roof's plane that draws the slope 1.3 times long? (T-3080)

T-3072 counted about 43 courses between the Cornell c. 1887 print's own ridge (the foot of the
cresting) and eave on the roof plane over the stable's alley end, and about 42 on HABS
photograph 1 of 1963. Through the committed cameras the Cornell print puts 22-23 ft of slope
between those edges and HABS 1 puts 17-17.5 ft. The committed Cornell camera is a west-wall
homography on two reconstructed eave heights; T-2758 re-solved it at the stable on measured
controls only (data/comparisons/glessner/stable-roof-heights.json: the corners at grade and up
their arrises, the carriage doorway's east jamb and 12.6 ft soffit, the loft opening's jambs),
and it re-solved HABS 1 on the printed doorway too. None of those fits saw a roof point.

This reads the same count, through every one of those cameras, with T-3072's own plane fit
and counter (read_module.py), and then asks where the model's plane begins and ends on each
counted column: the model's tile vertices lying on the fitted plane within 0.15 m of the
column's line across it give the plane's top and foot, in the print's rows and in height.

Needs the gitignored GLB: python3 tools/recover_glessner_v4.py --materialize

  python3 docs/RESEARCH/glessner-roof-slope-camera-T-3080/read_slope.py    writes readings.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "glessner-roof-module-T-3072"))
import read_module as rm  # noqa: E402  T-3072's plane fit, camera and course counter

FITS = ROOT / "data/comparisons/glessner/stable-roof-heights.json"
COURSE_IN = 5.0                    # HABS's measured exposure (L-glessner-roof-tiles-2203)
ON_PLANE_M = 0.12                  # a tile vertex this close to the fitted plane lies on it
ON_LINE_M = 0.15                   # ... and this close to the column's line across it
# The plane's straight ridge runs E-W at y 18.0 m, z 12.05 m from the alley gable (x -0.15) to
# the turret, whose foot it runs up into from x 5.1 m (z 12.83 at y 17.04). The counted columns
# meet the ridge at x 1.4-4.3 m; a vertex past this bound is the turret's saddle, not the ridge.
WEST_OF_TURRET_X_M = 4.9

# Every camera that sees the plane: the committed view, then T-2758's measured-control fits.
# T-2758's pixel-aspect fits of HABS 1 (1.02-1.06) are left out: read_module's camera has
# square pixels, and the square doorway fit already brackets them (3.92 px RMS, the same).
CAMERAS = {
    "cornell-northwest-west-windows": ("cornell", ["committed", "roof_pitched", "roof_level"]),
    "habs-01-northwest": ("habs01", ["committed", "doorway", "doorway_eye_height", "doorway_lean"]),
}


def camera(view, fit):
    cam = rm.Camera(view)
    if fit is not None:
        cam.e = np.array(fit["eye"], float)
        cam.B = np.array(fit["basis_right_up_forward"], float)
        cam.f = float(fit["focal_px"])
        cam.c = np.array(fit["principal_px"], float)
        assert float(fit.get("pixel_aspect", 1.0)) == 1.0, fit
    return cam


def plane_line(cam, c, nrm, x):
    """The column's line across the plane: one point per print row."""
    ys = np.arange(0, cam.size[1], 1.0)
    d = cam.ray(np.full_like(ys, float(x)), ys)
    t = ((c - cam.e) @ nrm) / (d @ nrm)
    k = t > 0
    return ys[k], cam.e + d[k] * t[k, None]


def main():
    fits = json.loads(FITS.read_text())
    V = rm.roof_vertices()
    out = {"ticket": "T-3080", "glb": str(rm.GLB.relative_to(ROOT)), "fits": str(FITS.relative_to(ROOT)),
           "course_in": COURSE_IN, "views": {}}
    for view, (key, names) in CAMERAS.items():
        field, edges = rm.COUNT_EDGES[view]
        img = np.asarray(Image.open(rm.Camera(view).photo).convert("L"), float)
        rows = []
        for name in names:
            fit = None if name == "committed" else fits[key][name]["camera"]
            what = fits[key][name]["what"]
            rms = fits[key][name]["rms_px"]
            cam = camera(view, fit)
            c, nrm, down, pitch, _ = rm.fit_plane(cam, V, field)
            on = V[(np.abs((V - c) @ nrm) < ON_PLANE_M) & (V[:, 0] < WEST_OF_TURRET_X_M)]
            cols = []
            for x, (yr, ye) in edges.items():
                got = [rm.count_courses(cam, img, c, nrm, down, xx, yr, ye) for xx in range(x - 3, x + 4)]
                n = float(np.mean([g[0] for g in got]))
                ft = float(np.mean([g[1] for g in got]))
                ys, L = plane_line(cam, c, nrm, x)
                dist, idx = cKDTree(L).query(on)
                k = dist < ON_LINE_M
                mz = on[k, 2]
                mr = ys[idx[k]]
                pz = (float(L[np.searchsorted(ys, yr), 2]), float(L[np.searchsorted(ys, ye), 2]))
                cols.append({
                    "column": x, "print_ridge_row": yr, "print_eave_row": ye,
                    "courses": round(n, 1), "camera_slope_ft": round(ft, 2),
                    "camera_course_in": round(ft * 12 / n, 2),
                    "model_top_row": int(mr.min()), "model_foot_row": int(mr.max()),
                    "model_top_m": round(float(mz.max()), 2), "model_foot_m": round(float(mz.min()), 2),
                    "print_ridge_on_plane_m": round(pz[0], 2), "print_eave_on_plane_m": round(pz[1], 2),
                    "ridge_below_model_top_m": round(float(mz.max()) - pz[0], 2),
                    "eave_below_model_foot_m": round(float(mz.min()) - pz[1], 2),
                })
            sin = np.sin(np.radians(pitch))
            model_ft = float(np.median([(r["model_top_m"] - r["model_foot_m"]) / sin / rm.IN / 12 for r in cols]))
            row = {"camera": name, "what": what, "rms_px_on_measured_controls": rms,
                   "plane_pitch_deg": round(pitch, 1), "model_slope_ft": round(model_ft, 1),
                   "model_courses_at_5in": round(model_ft * 12 / COURSE_IN, 1),
                   "print_courses": [min(r["courses"] for r in cols), max(r["courses"] for r in cols)],
                   "camera_course_in": [min(r["camera_course_in"] for r in cols), max(r["camera_course_in"] for r in cols)],
                   "camera_slope_ft": [min(r["camera_slope_ft"] for r in cols), max(r["camera_slope_ft"] for r in cols)],
                   "columns": cols}
            rows.append(row)
            print(view, name, f"rms {rms}", "course", row["camera_course_in"], "slope", row["camera_slope_ft"],
                  "model", row["model_slope_ft"], "ft",
                  "ridge below model top", [r["ridge_below_model_top_m"] for r in cols],
                  "eave below model foot", [r["eave_below_model_foot_m"] for r in cols])
        out["views"][view] = rows
    (HERE / "readings.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
