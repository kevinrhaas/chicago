"""T-3385: read a monochrome picture's tones inside the build's own surfaces.

    python3 tone_read.py <idpass-prefix> [--overlay out.jpg]

idpass.mjs rendered, from the picture's own camera, which material of the build covers each
pixel and which way that face looks. Each class mask is eroded (a camera fit is good to a few
pixels; an eroded mask keeps the reading off the edges), then the picture's median grey and
its 25th-75th percentiles are taken inside it. Printed as one JSON line per picture.
"""
import json, sys, re
import numpy as np
from PIL import Image
from scipy import ndimage

CLASSES = [
    ("brick_front", r"^(brick|brick_front|bay_brick|brick_unit_.*|draft_brick)$", (1,)),
    ("brick_side", r"^(brick|brick_front|brick_unit_.*|draft_brick)$", (2, 3)),
    ("stone_front", r"^(limestone_trim|dress_stone|rough_stone_trim|bay_stone|carved_trim|stoop_stone|dormer_stone)$", (1,)),
    ("trim_front", r"^(limestone_trim|dress_stone|carved_trim|draft_trim|draft_stone)$", (1,)),
    ("trim_side", r"^(limestone_trim|dress_stone)$", (2, 3)),
    ("stone_side", r"^(limestone_trim|dress_stone|rough_stone_trim|bay_stone)$", (2, 3)),
    ("slate", r"^(slate_covering|wing_slate|bay_slate|.*slate.*|draft_roof)$", (1, 2, 3, 4)),
    ("paint", r"^(fascia|frieze_panel|cornice.*|porch.*|bay_frame|bay_strip_paint)$", (1, 2, 3)),
    ("glass", r"^(glass|backing|curtain|blind)$", (1, 2, 3)),
]


def read(prefix, overlay=None, erode=3):
    meta = json.load(open(prefix + ".json"))
    ids = np.asarray(Image.open(prefix + ".png").convert("RGB")).astype(int)
    mat = ids[..., 0] + 256 * ids[..., 1]
    face = ids[..., 2]
    photo = Image.open(meta["photo"]).convert("L")
    if meta.get("mirrored"):
        photo = photo.transpose(Image.FLIP_LEFT_RIGHT)
    photo = photo.resize((ids.shape[1], ids.shape[0]))
    g = np.asarray(photo).astype(float)
    names = meta["names"]
    out = {"camera": meta["camera"]}
    masks = {}
    for cname, rx, faces in CLASSES:
        sel = [i + 1 for i, n in enumerate(names) if re.match(rx, n)]
        m = np.isin(mat, sel) & np.isin(face, faces)
        m = ndimage.binary_erosion(m, iterations=erode)
        masks[cname] = m
        if m.sum() < 40:
            continue
        v = g[m]
        out[cname] = {"n": int(m.sum()), "median": round(float(np.median(v)), 1),
                      "p25": round(float(np.percentile(v, 25)), 1), "p75": round(float(np.percentile(v, 75)), 1)}
    sky = (mat == 0)
    sky = ndimage.binary_erosion(sky, iterations=8)
    sky[int(sky.shape[0] * 0.45):] = False
    if sky.sum() > 200:
        out["sky_top"] = round(float(np.median(g[sky])), 1)
    out["print_white_p99"] = round(float(np.percentile(g, 99)), 1)
    out["print_black_p1"] = round(float(np.percentile(g, 1)), 1)
    if overlay:
        rgb = np.stack([g, g, g], -1)
        cols = {"brick_front": (255, 60, 40), "brick_side": (255, 160, 40), "stone_front": (60, 200, 255),
                "stone_side": (60, 120, 255), "trim_front": (0, 255, 255), "trim_side": (0, 160, 160), "slate": (160, 60, 255), "paint": (60, 255, 80), "glass": (255, 255, 0)}
        for k, m in masks.items():
            edge = m & ~ndimage.binary_erosion(m, iterations=2)
            rgb[edge] = cols[k]
        Image.fromarray(rgb.astype(np.uint8)).save(overlay, quality=85)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    ov = a[a.index("--overlay") + 1] if "--overlay" in a else None
    print(json.dumps(read(a[0], ov)))
