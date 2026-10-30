#!/usr/bin/env python3
"""Which carries the stable roof's eight extra courses: the ridge's height, its plan line or the plane's pitch? (T-3095, the first piece of T-3094)

T-3072 counted 41.7-43.9 courses on the c. 1887 Cornell print and 40.6-42.7 on HABS photograph 1
between the foot of the ridge roll (under the cresting) and the eave of the north slope of the
stable's E-W ridge, over the alley end. The model lays 51 there at HABS's 5 in. T-3080 showed
that every camera fitted on measured controls (T-2758, no roof point in any fit) puts the
prints' eave on the model's and the roll's foot 0.3-1.1 m below the model's ridge.

A count and a camera answer different questions, so each candidate roof is put to both:

  A  the pitch stands (42.5 degrees) and the ridge comes down the same plane, so its plan line
     moves north;
  B  the plan line stands (the ridge over S 14.6, in line with the 18th Street range's) and the
     ridge comes down by flattening the plane about its eave;
  C  the ridge's height stands and the plane steepens about its eave, so the ridge moves north.

For each family, the ridge height where the plane's own length gives the print's count, and
the ridge height where each camera's ray through the print's roll foot meets that family's
plane. A family that is the roof must give the same ridge both ways.

Model frame (the GLB's, z over north grade): the plane runs from its tile foot at y 22.71 m,
z 7.65 to its tiled top at y 17.96, z 12.01 (read off the committed GLB's tile vertices). The
ridge roll's foot is put 0.09 m (z) under the tiled top, which is where a 0.14 m roll (the
record's roof_edges.cap_radius_m) bears on a 42.5 degree slope; that offset moves every family
alike and cannot separate them.

Needs the gitignored GLB only for the plane check: python3 tools/recover_glessner_v4.py --materialize

  python3 docs/RESEARCH/glessner-stable-ridge-T-3095/read_ridge.py     writes readings.json, ridge-candidates.jpg
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "glessner-roof-module-T-3072"))
import read_module as rm  # noqa: E402  T-3072's cameras, count edges and GLB reader

FITS = ROOT / "data/comparisons/glessner/stable-roof-heights.json"
COUNTS = HERE.parent / "glessner-roof-module-T-3072/readings.json"
IN = 0.0254
COURSE_M = 5 * IN                  # HABS's measured exposure (L-glessner-roof-tiles-2203)
FOOT = np.array([22.71, 7.65])     # the plane's tile foot (y, z), model and prints agree (T-3080)
TOP = np.array([17.96, 12.01])     # the model's tiled top (y, z)
ROLL_M = 0.09                      # roll foot under the tiled top, z
FT = 0.3048
GRADE_TO_RECORD_M = 0.245          # the tiled surface stands this far over the record's roof line
CAMERAS = {
    "cornell-northwest-west-windows": ("cornell", ["roof_pitched", "roof_level"]),
    "habs-01-northwest": ("habs01", ["doorway", "doorway_eye_height", "doorway_lean"]),
}


def family_plane(fam, top_z):
    """(y, z) of the tiled top for a family at a given top height."""
    if fam == "A":                 # same pitch: slide up the model's plane
        k = (TOP[1] - FOOT[1]) / (FOOT[0] - TOP[0])
        return np.array([FOOT[0] - (top_z - FOOT[1]) / k, top_z])
    if fam == "B":                 # same plan line
        return np.array([TOP[0], top_z])
    raise ValueError(fam)


def roll_foot(top):
    k = (top[1] - FOOT[1]) / (FOOT[0] - top[0])
    return top - np.array([-ROLL_M / k, ROLL_M])


def slope_courses(top):
    return float(np.hypot(*(roll_foot(top) - FOOT)) / COURSE_M)


def top_from_count(fam, n):
    lo, hi = 9.0, 14.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if slope_courses(family_plane(fam, mid)) < n:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def top_from_ray(fam, e, d):
    """The family's top height whose roll-foot line the ray (eye e, direction d) meets."""
    def miss(z):
        f = roll_foot(family_plane(fam, z))
        # signed vertical gap between the ray and the plane's line through FOOT and f, at the ray's crossing
        n = np.array([-(f[1] - FOOT[1]), f[0] - FOOT[0]])      # normal in (y, z)
        t = ((np.array([FOOT[0], FOOT[1]]) - e[1:]) @ n) / (d[1:] @ n)
        p = e[1:] + d[1:] * t
        s = (p - FOOT) @ (f - FOOT) / ((f - FOOT) @ (f - FOOT))
        return s - 1.0             # the ray meets the plane above (+) or below (-) the roll foot
    lo, hi = 9.0, 14.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if miss(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def camera(view, fit):
    cam = rm.Camera(view)
    cam.e = np.array(fit["eye"], float)
    cam.B = np.array(fit["basis_right_up_forward"], float)
    cam.f = float(fit["focal_px"])
    cam.c = np.array(fit["principal_px"], float)
    return cam


def plane_check():
    V = rm.roof_vertices()
    s = V[(V[:, 0] > 0.5) & (V[:, 0] < 2.0) & (V[:, 1] > 17.9)]
    A = np.column_stack((s[:, 1], np.ones(len(s))))
    k = np.ones(len(s), bool)
    for _ in range(6):
        co, *_ = np.linalg.lstsq(A[k], s[k, 2], rcond=None)
        k = np.abs(s[:, 2] - A @ co) < 0.12
    P = s[k]
    return {"pitch_deg": round(float(np.degrees(np.arctan(-co[0]))), 2),
            "foot_yz": [round(float(P[:, 1].max()), 2), round(float(P[:, 2].min()), 2)],
            "top_yz": [round(float(P[:, 1].min()), 2), round(float(P[:, 2].max()), 2)]}


def record(top):
    """The record's terms (ft over north grade, S from the 18th Street wall) for a tiled top."""
    ridge_ft = (top[1] - GRADE_TO_RECORD_M) / FT
    s_ft = 14.6 + (TOP[0] - top[0]) / FT
    return round(ridge_ft, 2), round(s_ft, 2)


def main():
    fits = json.loads(FITS.read_text())
    counts = json.loads(COUNTS.read_text())
    out = {"ticket": "T-3095", "course_in": 5.0, "roll_foot_below_top_m": ROLL_M,
           "model": {"foot_yz": FOOT.tolist(), "top_yz": TOP.tolist(),
                     "courses_at_5in": round(slope_courses(TOP), 1), "record_ridge_ft_S": record(TOP)}}
    try:
        out["model"]["glb_plane_check"] = plane_check()
    except FileNotFoundError:
        out["model"]["glb_plane_check"] = "GLB not materialized"
    cols = {}
    for view, (key, names) in CAMERAS.items():
        edges = rm.COUNT_EDGES[view][1]
        got = {c["column"]: c["courses"] for c in
               next(r for r in json.loads((HERE.parent / "glessner-roof-slope-camera-T-3080/readings.json").read_text())
                    ["views"][view] if r["camera"] == "committed")["columns"]}
        for name in names:
            cam = camera(view, fits[key][name]["camera"])
            for x, (yr, _ye) in edges.items():
                d = cam.ray(np.array([float(x)]), np.array([float(yr)]))[0]
                cols.setdefault((view, x), {"view": view, "column": x, "print_courses": got[x], "cameras": {}})
                cols[(view, x)]["cameras"][name] = {
                    "rms_px": fits[key][name]["rms_px"],
                    **{f"top_z_{fam}": round(top_from_ray(fam, cam.e, d), 3) for fam in "AB"}}
    rows = []
    for c in cols.values():
        for fam in "AB":
            c[f"top_z_{fam}_from_count"] = round(top_from_count(fam, c["print_courses"]), 3)
        rows.append(c)
    out["columns"] = rows
    summary = {}
    for fam in "AB":
        cam_z = [v[f"top_z_{fam}"] for c in rows for v in c["cameras"].values()]
        cnt_z = [c[f"top_z_{fam}_from_count"] for c in rows]
        gap = [v[f"top_z_{fam}"] - c[f"top_z_{fam}_from_count"] for c in rows for v in c["cameras"].values()]
        mid = family_plane(fam, float(np.median(cnt_z)))
        summary[fam] = {
            "top_z_from_count": [min(cnt_z), max(cnt_z)],
            "top_z_from_cameras": [min(cam_z), max(cam_z)],
            "camera_minus_count_m": [round(min(gap), 3), round(float(np.median(gap)), 3), round(max(gap), 3)],
            "median_count_top_yz": [round(float(mid[0]), 2), round(float(mid[1]), 3)],
            "pitch_deg": round(float(np.degrees(np.arctan((mid[1] - FOOT[1]) / (FOOT[0] - mid[0])))), 1),
            "record_ridge_ft_S": record(mid),
        }
    # C: the top's height stands; the count fixes the run, so the plan line moves north.
    n = float(np.median([c["print_courses"] for c in rows]))
    L = n * COURSE_M + ROLL_M / np.sin(np.arctan((TOP[1] - FOOT[1]) / (FOOT[0] - TOP[0])))
    run = float(np.sqrt(max(L ** 2 - (TOP[1] - FOOT[1]) ** 2, 0)))
    cy = FOOT[0] - run
    cams = []
    for view, (key, names) in CAMERAS.items():
        for name in names:
            cam = camera(view, fits[key][name]["camera"])
            p, _ = cam.project(np.array([[2.0, cy, TOP[1]], [2.0, TOP[0], TOP[1]]]))
            cams.append(round(float(p[0, 1] - p[1, 1]), 1))
    summary["C"] = {"top_yz": [round(cy, 2), TOP[1]],
                    "pitch_deg": round(float(np.degrees(np.arctan((TOP[1] - FOOT[1]) / run))), 1),
                    "ridge_row_shift_px_vs_model": cams,
                    "note": "negative rows are higher in the print; the prints' roll foot lies BELOW the model's top"}
    out["families"] = summary
    for fam, v in summary.items():
        print(fam, json.dumps(v))
    (HERE / "readings.json").write_text(json.dumps(out, indent=1) + "\n")
    figure(summary, fits)


def figure(summary, fits):
    """ridge-candidates.jpg: each family's ridge at its count height (solid) over two measured cameras."""
    from PIL import Image, ImageDraw, ImageOps
    lines = {"model": (TOP, (220, 30, 30)), "A": (np.array(summary["A"]["median_count_top_yz"]), (200, 0, 200)),
             "B": (np.array(summary["B"]["median_count_top_yz"]), (0, 170, 0)),
             "C": (np.array(summary["C"]["top_yz"]), (0, 110, 255))}
    tiles = []
    for view, key, name, box, s in (("cornell-northwest-west-windows", "cornell", "roof_level", (1000, 160, 1330, 480), 2),
                                   ("habs-01-northwest", "habs01", "doorway", (1380, 300, 1650, 560), 3)):
        cam = camera(view, fits[key][name]["camera"])
        im = ImageOps.autocontrast(Image.open(cam.photo).convert("L"), cutoff=0.5).convert("RGB")
        d = ImageDraw.Draw(im)
        for top, col in lines.values():
            P = np.column_stack((np.linspace(-0.15, 4.5, 30), np.full(30, top[0]), np.full(30, top[1])))
            d.line([tuple(q) for q in cam.project(P)[0]], fill=col, width=1)
        tiles.append(im.crop(box).resize(((box[2] - box[0]) * s, (box[3] - box[1]) * s), Image.LANCZOS))
    h = max(t.size[1] for t in tiles)
    out = Image.new("RGB", (sum(t.size[0] for t in tiles) + 8, h), "white")
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.size[0] + 8
    out.save(HERE / "ridge-candidates.jpg", quality=88)


if __name__ == "__main__":
    main()
