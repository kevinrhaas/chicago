#!/usr/bin/env python3
"""Read Glessner's roof course module in roof-plane inches, through each picture's solved camera (T-3072).

T-3025 read the Cornell print's stable-roof courses as a ratio against the render's, where the
render's course was 3.4-3.7 px, close to its texture's sampling limit. Here no render is needed:
the committed GLB lays every tile as geometry, so a plane fitted to its roof-tile vertices
where a band of pixel columns crosses the roof gives each pixel a place on the slope. Each
column's intensities are resampled onto the slope's distance in inches and the course period is
read from the summed Hann-windowed spectrum. The same reading on the GLB's own tile vertices
(their downslope positions) shows what the method returns where the answer is known.

The period reading leans on the camera's scale on the plane. The second reading does not: the
courses between a print's own ridge (the foot of the cresting) and the plane's eave, picked on
4x strips of each print, are counted as the unwrapped phase of the band-passed column. A count
is unchanged by any warping of the column, so two prints of one plane that count the same
courses between the same two edges show the same module whatever their cameras say.

Needs the gitignored GLB: python3 tools/recover_glessner_v4.py --materialize

  python3 docs/RESEARCH/glessner-roof-module-T-3072/read_module.py      write readings.json
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import hilbert

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GLB = ROOT / "assets/gltf/glessner_house__as_built_1887.glb"
VIEWS = ROOT / "data/reference_views/glessner_house"
IN = 0.0254
STEP_IN = 0.25                     # resampling step along the slope
BAND_IN = (4.0, 9.0)               # periods searched: brackets 5 in and T-3025's 6.4 in

# Fields of one roof plane, clear of cupola, stacks, cresting and eaves, in each print's own
# pixels (columns x0-x1, rows y0-y1). Picked on the prints at full size.
FIELDS = {
    "cornell-northwest-west-windows": [
        ("stable west slope, T-3025's band 1", (1000, 1030, 300, 450)),
        ("stable west slope, T-3025's band 2", (1040, 1080, 300, 450)),
        ("stable west slope, T-3025's band 3", (1090, 1120, 300, 450)),
    ],
    "habs-01-northwest": [
        ("stable west slope (the Cornell plane), band 1", (1440, 1480, 405, 520)),
        ("stable west slope (the Cornell plane), band 2", (1490, 1530, 395, 520)),
        ("stable west slope (the Cornell plane), band 3", (1540, 1570, 385, 515)),
        ("long west roof, band 1", (800, 850, 505, 580)),
        ("long west roof, band 2", (880, 940, 500, 578)),
        ("long west roof, band 3", (1000, 1060, 470, 570)),
    ],
    "taylor-2135-ne": [
        ("18th Street roof, band 1", (420, 480, 330, 450)),
        ("18th Street roof, band 2", (520, 580, 320, 450)),
        ("18th Street roof, band 3", (600, 660, 315, 450)),
        ("18th Street roof, band 4", (760, 800, 300, 440)),
    ],
}

SAMPLING_LIMIT_PX = 3.0            # a 5 in course drawn under this many pixels is not resolved

# The stable's west slope in the two prints that show it from the north-west, 87 years apart:
# the print's own ridge row (foot of the cresting) and eave row at three columns, read on 4x
# strips (same-plane-strips.jpg). Counted over columns x-3..x+3.
COUNT_EDGES = {
    "cornell-northwest-west-windows": ((1040, 1080, 300, 450), {1040: (290, 472), 1060: (280, 470), 1080: (272, 467)}),
    "habs-01-northwest": ((1490, 1530, 395, 520), {1480: (390, 528), 1500: (385, 527), 1520: (380, 525)}),
}


def roof_vertices():
    b = GLB.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    off = 20 + n + 8
    out = []
    for prim in j["meshes"][0]["primitives"]:
        if not j["materials"][prim.get("material", 0)]["name"].startswith("roof_plane"):
            continue
        a = j["accessors"][prim["attributes"]["POSITION"]]
        v = j["bufferViews"][a["bufferView"]]
        start = off + v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 12)
        raw = np.frombuffer(b, np.uint8, count=stride * a["count"], offset=start).reshape(-1, stride)
        p = raw[:, :12].copy().view("<f4").reshape(-1, 3).astype(float)
        out.append(np.column_stack((p[:, 0], -p[:, 2], p[:, 1])))
    return np.concatenate(out)


class Camera:
    def __init__(self, view):
        cam = json.loads((VIEWS / f"{view}.json").read_text())
        self.e = np.array(cam["eye"], float)
        if "basis_right_up_forward" in cam:
            self.B = np.array(cam["basis_right_up_forward"], float)
        else:                      # a level camera: heading clockwise from north (photo_match.mjs)
            y = np.radians(cam["yaw_deg"])
            self.B = np.array([[np.cos(y), -np.sin(y), 0], [0, 0, 1], [np.sin(y), np.cos(y), 0]])
        self.f = float(cam["focal_px"])
        self.c = np.array(cam["principal_px"], float)
        self.photo = (VIEWS / cam["photo"]).resolve()
        self.size = cam["image_px"]

    def project(self, P):
        q = (P - self.e) @ self.B.T
        return np.column_stack((self.c[0] + self.f * q[:, 0] / q[:, 2],
                                self.c[1] - self.f * q[:, 1] / q[:, 2])), q[:, 2]

    def ray(self, x, y):
        d = np.stack([(x - self.c[0]) / self.f, -(y - self.c[1]) / self.f, np.ones_like(x)], -1) @ self.B
        return d / np.linalg.norm(d, axis=-1, keepdims=True)


def fit_plane(cam, V, field):
    """The nearest roof plane under the field: vertices projecting inside it, the front depth layer."""
    x0, x1, y0, y1 = field
    uv, z = cam.project(V)
    k = (uv[:, 0] >= x0) & (uv[:, 0] <= x1) & (uv[:, 1] >= y0) & (uv[:, 1] <= y1) & (z > 0)
    P, z = V[k], z[k]
    # keep the nearest surface: per pixel cell, the minimum depth, then a 0.5 m shell over it
    P = P[z < np.percentile(z, 5) + 4.0]
    for _ in range(4):
        c = P.mean(0)
        nrm = np.linalg.svd(P - c)[2][2]
        r = (P - c) @ nrm
        P = P[np.abs(r) < max(0.05, 3 * np.std(r))]
    c = P.mean(0)
    nrm = np.linalg.svd(P - c)[2][2]
    if nrm[2] < 0:
        nrm = -nrm
    down = np.array([0.0, 0.0, -1.0]) - nrm * (-nrm[2])
    down /= np.linalg.norm(down)
    pitch = float(np.degrees(np.arccos(nrm[2])))
    return c, nrm, down, pitch, P


def spectrum(series):
    """Summed power of a list of (s_in, value) series resampled on STEP_IN."""
    power, nfft = None, 4096
    for s, val in series:
        if len(s) < 8:
            continue
        o = np.argsort(s)
        s, val = s[o], val[o]
        grid = np.arange(s[0], s[-1], STEP_IN)
        if len(grid) < 32:
            continue
        g = np.interp(grid, s, val)
        g = g - np.polyval(np.polyfit(grid, g, 2), grid)
        g *= np.hanning(len(g))
        p = np.abs(np.fft.rfft(g, n=nfft)) ** 2
        power = p if power is None else power + p
    f = np.fft.rfftfreq(nfft, d=STEP_IN)
    with np.errstate(divide="ignore"):
        per = 1 / f
    band = (per > BAND_IN[0]) & (per < BAND_IN[1])
    i = np.argmax(np.where(band, power, 0))
    # parabolic refinement of the peak in frequency
    a, b_, c_ = power[i - 1], power[i], power[i + 1]
    d = 0.5 * (a - c_) / (a - 2 * b_ + c_)
    fp = f[i] + d * (f[1] - f[0])
    snr = float(power[i] / np.median(power[band]))
    return float(1 / fp), snr


def read_print(cam, img, field, c, nrm, down):
    x0, x1, y0, y1 = field
    series, px_per_in = [], []
    for x in range(x0, x1):
        ys = np.arange(y0, y1, dtype=float)
        d = cam.ray(np.full_like(ys, x), ys)
        t = ((c - cam.e) @ nrm) / (d @ nrm)
        P = cam.e + d * t[:, None]
        s = ((P - c) @ down) / IN
        series.append((s, img[y0:y1, x]))
        px_per_in.append(len(ys) / abs(s[-1] - s[0]))
    per, snr = spectrum(series)
    return per, snr, float(np.mean(px_per_in))


def read_glb(P, c, down):
    """The GLB's own course: tile-vertex downslope positions as a density series."""
    s = ((P - c) @ down) / IN
    h, e = np.histogram(s, bins=np.arange(s.min(), s.max(), STEP_IN))
    return spectrum([(0.5 * (e[1:] + e[:-1]), h.astype(float))])


def count_courses(cam, img, c, nrm, down, x, yr, ye):
    """Courses between rows yr and ye at column x: unwrapped phase of the band-passed profile."""
    ys = np.arange(yr + 2, ye - 1, dtype=float)           # two rows clear of each edge
    d = cam.ray(np.full_like(ys, x), ys)
    t = ((c - cam.e) @ nrm) / (d @ nrm)
    s = (((cam.e + d * t[:, None]) - c) @ down) / IN       # only to make the band stationary
    g = np.arange(s[0], s[-1], 0.1)
    v = np.interp(g, s, img[yr + 2:ye - 1, x])
    v = v - np.polyval(np.polyfit(g, v, 3), g)
    F = np.fft.rfft(v)
    f = np.fft.rfftfreq(len(v), 0.1)
    F[(f < 1 / 10) | (f > 1 / 3.5)] = 0
    ph = np.unwrap(np.angle(hilbert(np.fft.irfft(F, len(v)))))
    return abs(ph[-1] - ph[0]) / (2 * np.pi) * (ye - yr) / (ye - 1 - yr - 2), abs(s[-1] - s[0]) / 12


def main():
    V = roof_vertices()
    out = {"ticket": "T-3072", "glb": str(GLB.relative_to(ROOT)), "step_in": STEP_IN,
           "band_in": list(BAND_IN), "views": {}}
    for view, fields in FIELDS.items():
        cam = Camera(view)
        img = np.asarray(Image.open(cam.photo).convert("L"), float)
        assert [img.shape[1], img.shape[0]] == list(cam.size), (view, img.shape)
        rows = []
        for label, field in fields:
            c, nrm, down, pitch, P = fit_plane(cam, V, field)
            per, snr, ppi = read_print(cam, img, field, c, nrm, down)
            gper, gsnr = read_glb(P, c, down)
            rows.append({"field": label, "columns_rows": list(field), "plane_pitch_deg": round(pitch, 1),
                         "five_in_course_px": round(5 * ppi, 2),
                         "at_sampling_limit": bool(5 * ppi < SAMPLING_LIMIT_PX),
                         "plane_vertices": int(len(P)), "print_px_per_in": round(ppi, 3),
                         "print_course_in": round(per, 2), "print_peak_snr": round(snr, 1),
                         "glb_course_in": round(gper, 2), "glb_peak_snr": round(gsnr, 1)})
            print(view, rows[-1])
        out["views"][view] = rows
    out["ridge_to_eave_counts"] = {}
    for view, (field, edges) in COUNT_EDGES.items():
        cam = Camera(view)
        img = np.asarray(Image.open(cam.photo).convert("L"), float)
        c, nrm, down, _, _ = fit_plane(cam, V, field)
        rows = []
        for x, (yr, ye) in edges.items():
            got = [count_courses(cam, img, c, nrm, down, xx, yr, ye) for xx in range(x - 3, x + 4)]
            n = np.array([g[0] for g in got])
            ft = float(np.mean([g[1] for g in got]))
            rows.append({"column": x, "ridge_row": yr, "eave_row": ye, "courses": round(float(n.mean()), 1),
                         "courses_sd": round(float(n.std()), 1), "camera_slope_ft": round(ft, 2),
                         "camera_course_in": round(ft * 12 / float(n.mean()), 2)})
            print(view, rows[-1])
        out["ridge_to_eave_counts"][view] = rows
    (HERE / "readings.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
