#!/usr/bin/env python3
"""T-3044 (of T-3026): Glessner's rock-faced courses read on Taylor 2135, against the render through its camera.

Two questions, both asked of the same photograph and the same solved camera
(data/reference_views/glessner_house/taylor-2135-ne.json):

1. HEIGHTS. Where do the photograph's bed joints stand, against the printed course string
   the model lays (record v4_detail.ashlar_courses_in) and sheet 6's drawn beds (T-2986)?
2. RELIEF. Does a high course throw a deeper shadow than a low one, in the photograph and in
   the render, and by how much?

Method. Each face is sampled along vertical lines in the wall's own plane (u, v, z through the
camera), so every number below is in feet on the wall, never in pixels. A pier's profile is the
median across its columns, which keeps the continuous bed joints and drops the staggered
vertical ones. The render is the same camera's view of the committed GLB, so the render's beds
are the printed string's (each sits 0.09 ft high in this read: the dark line is the lip's
shadow, not the joint's centre; the photograph's lines carry the same bias, so differences
cancel it).

The camera's own vertical scale is not trusted as measured: the photograph's window heads and
sills against the render's register it (`openings`), and the courses are read RELATIVE to that.
A free fit then stretches the render's profile about bed 7 until it best correlates with the
photograph's, pier by pier.

  python3 docs/RESEARCH/glessner-course-reading-T-3044/read_courses.py --render <png>

<png> is the bare render `node tools/photo_match.mjs data/reference_views/glessner_house/
taylor-2135-ne.json` prints (it goes to a temp folder). Writes readings.json and
pier-n2.png beside this file.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d, map_coordinates

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMERA = ROOT / "data/reference_views/glessner_house/taylor-2135-ne.json"
RECORD = ROOT / "data/structures/glessner_house.json"
FT = 0.3048
U_PRAIRIE = (161.25 - 0) * FT          # the Prairie face, W 0 (glessner_prairie_front.metric)
V_NORTH = 74.0 * FT                    # the 18th Street face, S 0
NG_OVER_WALK = 0.20                    # record grade_datum
DOOR_OVER_WALK = 0.74                  # record frame_ft.door_datum_above_grade_ft
# Sheet 6's beds 8-23 as T-2986 measured them (inches), on its bed 7 at 7.62-7.73 ft door.
SHEET6_COURSES_8_23 = [15.5, 8.2, 12.1, 8.6, 10.6, 8.5, 10.3, 8.2, 19.3, 9.6, 12.1, 17.9, 8.6, 9.2, 8.8, 9.7]
SHEET6_BED7_DOOR = (7.62 + 7.73) / 2
# Piers that run clear from the walk to the second floor in this photograph, ft from the NE
# corner along the Prairie face: north of the lamp post, between ff_B and the door under the
# 2f gap, south of the door short of the tree. Openings per data/comparisons/glessner/prairie-front.json.
PIERS = {"N1": (4.6, 6.8, "N"), "N2": (21.0, 25.6, "N"), "S1": (39.9, 42.3, "S")}
# Window columns for the registration, inside each opening's glass.
WINDOWS = {"N": [(8.2, 10.8), (17.0, 19.9)], "S": [(45.6, 48.6), (54.8, 57.6)]}
# (edge, the model's height over the walk, the sign of d(brightness)/dz at it)
EDGES = [("ff sill", 9.45, -1), ("ff head", 15.04, +1), ("2f head", 25.0, +1)]


def camera():
    c = json.loads(CAMERA.read_text())
    return (np.array(c["eye"]), np.array(c["basis_right_up_forward"]), c["focal_px"],
            c["principal_px"], (CAMERA.parent / c["photo"]).resolve())


EYE, BASIS, F, C, PHOTO = camera()


def project(points):
    q = (np.atleast_2d(points) - EYE) @ BASIS.T
    return np.column_stack((C[0] + F * q[:, 0] / q[:, 2], C[1] - F * q[:, 1] / q[:, 2]))


def face_point(face, t, z):
    """t ft from the NE corner along the face, z ft over the Prairie walk."""
    if face == "prairie":
        return [U_PRAIRIE, V_NORTH - t * FT, z * FT]
    return [U_PRAIRIE - t * FT, V_NORTH, z * FT]


def gray(path):
    return np.asarray(Image.open(path).convert("L"), dtype=float)


def profile(img, face, t0, t1, zs, smooth=1.5):
    acc = []
    for t in np.arange(t0, t1, 0.2):
        p = project(np.array([face_point(face, t, z) for z in zs]))
        acc.append(map_coordinates(img, [p[:, 1], p[:, 0]], order=1))
    m = np.median(acc, 0)
    return gaussian_filter1d(m, smooth) if smooth else m


def norm(x):
    x = x - gaussian_filter1d(x, 60)
    return (x - x.mean()) / x.std()


def printed_beds():
    rec = json.loads(RECORD.read_text())
    courses = rec["phases"][0]["form"]["v4_detail"]["value"]["ashlar_courses_in"]
    return courses, NG_OVER_WALK + np.cumsum(courses) / 12.0


def openings(photo, render):
    """photo z = s * render z + o, per half of the front, from the window edges."""
    zs = np.arange(6, 27, 0.01)
    out = {}
    for half, cols in WINDOWS.items():
        r_all, p_all, edges = [], [], []
        for t0, t1 in cols:
            pair = {}
            for name, img in (("photo", photo), ("render", render)):
                g = np.gradient(profile(img, "prairie", t0, t1, zs, smooth=2))
                pair[name] = [float(zs[np.argmax(sg * g * ((zs > z - 1.0) & (zs < z + 1.4)))]) for _, z, sg in EDGES]
            r_all += pair["render"]
            p_all += pair["photo"]
            edges.append({"columns_ft": [t0, t1], **{k: [round(v, 2) for v in vs] for k, vs in pair.items()}})
        s, o = np.polyfit(r_all, p_all, 1)
        out[half] = {"scale": round(float(s), 4), "offset_ft": round(float(o), 3),
                     "rms_ft": round(float(np.sqrt(np.mean((s * np.array(r_all) + o - p_all) ** 2))), 3),
                     "edges": edges}
    return out


def fit(pz, z, r, zs, pivot):
    best = (-1.0, 1.0, 0.0)
    for k in np.arange(0.96, 1.08, 0.0025):
        for off in np.arange(-0.4, 0.4, 0.01):
            cc = np.corrcoef(pz, norm(np.interp((z - off - pivot) / k + pivot, zs, r)))[0, 1]
            if cc > best[0]:
                best = (cc, k, off)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    args = ap.parse_args()
    photo, render = gray(PHOTO), gray(args.render)
    courses, beds = printed_beds()
    bed7 = float(beds[6])
    sheet6 = [SHEET6_BED7_DOOR + DOOR_OVER_WALK]
    for c in SHEET6_COURSES_8_23:
        sheet6.append(sheet6[-1] + c / 12)
    cal = openings(photo, render)
    zs = np.arange(0, 26, 0.01)
    z = np.arange(8.0, 22.6, 0.01)
    piers, relief_rows = {}, []
    for key, (t0, t1, half) in PIERS.items():
        p = profile(photo, "prairie", t0, t1, zs)
        r = profile(render, "prairie", t0, t1, zs)
        s, o = cal[half]["scale"], cal[half]["offset_ft"]
        pz = norm(np.interp(s * z + o, zs, p))          # the photograph, on the model's heights
        cc0 = np.corrcoef(pz, norm(np.interp(z, zs, r)))[0, 1]
        cc, k, off = fit(pz, z, r, zs, bed7)
        piers[key] = {"ft_from_NE": [t0, t1], "corr_printed": round(float(cc0), 3),
                      "free": {"corr": round(float(cc), 3), "scale_about_bed7": round(float(k), 4),
                               "offset_ft": round(float(off), 2),
                               "bed23_over_door_ft": round(bed7 + off + k * (beds[22] - bed7) - DOOR_OVER_WALK, 2)}}
        # RELIEF: each course 8-22's lower-lip shadow against its own median, on the fitted beds.
        praw = profile(photo, "prairie", t0, t1, np.arange(0, 26, 0.005), smooth=0)
        rraw = profile(render, "prairie", t0, t1, np.arange(0, 26, 0.005), smooth=0)
        zz = np.arange(0, 26, 0.005)
        for i in range(7, 22):
            for src, prof, place in (("photo", praw, lambda q: s * (bed7 + off + k * (q - bed7)) + o),
                                     ("render", rraw, lambda q: q + 0.09)):
                lo, hi = place(beds[i - 1]), place(beds[i])
                band = prof[(zz > lo + 0.03 * (hi - lo)) & (zz < hi - 0.03 * (hi - lo))]
                if len(band) < 5:
                    continue
                med = float(np.median(band))
                lip = float(band[: max(2, len(band) // 4)].min())
                relief_rows.append({"pier": key, "course": i + 1, "in": courses[i], "src": src,
                                    "lip": round((med - lip) / med, 4)})
    relief = {}
    for src in ("photo", "render"):
        tall = [q["lip"] for q in relief_rows if q["src"] == src and q["in"] >= 11.5]
        low = [q["lip"] for q in relief_rows if q["src"] == src and q["in"] < 11.5]
        relief[src] = {"high_courses": len(tall), "low_courses": len(low),
                       "high_lip": round(float(np.mean(tall)), 3), "low_lip": round(float(np.mean(low)), 3),
                       "high_over_low": round(float(np.mean(tall) / np.mean(low)), 2)}
    # The 18th Street face near the corner, uncalibrated, beside the Prairie corner pier the same way.
    corner = {}
    for face, t0, t1 in (("north", 15, 24.5), ("north", 1.5, 3.0), ("prairie", 4.6, 6.8)):
        p = norm(np.interp(z, zs, profile(photo, face, t0, t1, zs)))
        r = profile(render, face, t0, t1, zs)
        cc, k, off = fit(p, z, r, zs, 8.0)
        corner[f"{face} {t0}-{t1} ft"] = {"corr": round(float(cc), 3), "scale_uncalibrated": round(float(k), 4)}
    out = {
        "ticket": "T-3044",
        "camera": str(CAMERA.relative_to(ROOT)),
        "printed_beds_over_walk_ft": [round(float(b), 2) for b in beds],
        "sheet6_beds_7_23_over_walk_ft": [round(b, 2) for b in sheet6],
        "openings_registration": cal,
        "piers": piers,
        "relief_lower_lip": relief,
        "relief_rows": relief_rows,
        "corner_faces_uncalibrated": corner,
    }
    (HERE / "readings.json").write_text(json.dumps(out, indent=1) + "\n")
    figure(photo, render, beds, piers["N2"], cal["N"], bed7)
    print(json.dumps({k: out[k] for k in ("openings_registration", "piers", "relief_lower_lip",
                                          "corner_faces_uncalibrated")}, indent=1)[:6000])


def figure(photo, render, beds, pier, cal, bed7, ppf=24, z0=7.0, z1=24.0):
    """Pier N2: the photograph on the model's heights (left), the render (right); printed
    beds ticked in the middle, the photograph's fitted beds ticked on its edge."""
    t0, t1 = pier["ft_from_NE"]
    zs = np.arange(z1, z0, -1 / ppf)
    ts = np.arange(t0, t1, 1 / ppf)
    s, o = cal["scale"], cal["offset_ft"]
    k, off = pier["free"]["scale_about_bed7"], pier["free"]["offset_ft"]

    def strip(img, zmap):
        a = np.zeros((len(zs), len(ts)))
        for i, t in enumerate(ts):
            pts = project(np.array([face_point("prairie", t, zmap(q)) for q in zs]))
            a[:, i] = map_coordinates(img, [pts[:, 1], pts[:, 0]], order=1)
        return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))

    a = strip(photo, lambda q: s * q + o)
    b = strip(render, lambda q: q)
    w, gap = a.width, 70
    out = Image.new("L", (2 * w + gap, a.height), 255)
    out.paste(a, (0, 0))
    out.paste(b, (w + gap, 0))
    d = ImageDraw.Draw(out)
    for i, bz in enumerate(beds):
        y = int((z1 - bz) * ppf)
        if 0 <= y < a.height:
            d.line([(w + 35, y), (w + gap, y)], fill=0)
            d.text((w + 38, y - 11), str(i + 1), fill=0)
        fy = int((z1 - (bed7 + off + k * (bz - bed7))) * ppf)
        if 0 <= fy < a.height and i >= 6:
            d.line([(w, fy), (w + 30, fy)], fill=0)
    out.save(HERE / "pier-n2.png", optimize=True)


if __name__ == "__main__":
    main()
