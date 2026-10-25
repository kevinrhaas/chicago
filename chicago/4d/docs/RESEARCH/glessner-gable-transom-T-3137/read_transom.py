#!/usr/bin/env python3
"""T-3137: the 18th Street gable light's transom, and the count of its fan's voussoirs,
read on HABS 14 with HABS 17 as the second picture.

    python3 docs/RESEARCH/glessner-gable-transom-T-3137/read_transom.py            print + write readings.json
    python3 docs/RESEARCH/glessner-gable-transom-T-3137/read_transom.py --check    re-derive and compare
    python3 docs/RESEARCH/glessner-gable-transom-T-3137/read_transom.py --profile  re-measure the fan's joints

The transom is read camera-free, as T-3116 read the fan: HABS 14 on T-3116's own vertical
(its projective map through sheet 6's crest, both stack stones and the north pairs' sill and
head, seven anchors), HABS 17 linearly between the light's ruled head (36.2) and sill (30.0),
which stand 63 px apart there. Each edge is picked as the half-way crossing of a
column-mean profile through the light; the same picks on the render of the build (GLB
6ba8c9f7..., T-3127's bake, before this ticket) return the built transom, and that error is
taken off the photograph's reading.

The fan's joints are read on HABS 14 (about 18 px to the foot) as minima of a polar
profile: the side-by-side's intensity averaged along each ray from the spring's centre
between radii 35 and 75 px, detrended by a 12-degree Gaussian. On the render that profile
returns all ten joints of the 11 built voussoirs (17.2 degrees apart), so it can see joints
that close. `--profile` re-runs it on the committed side-by-side."""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "docs/RESEARCH/glessner-gable-fan-T-3116"))
import read_fan  # noqa: E402  T-3116's anchors and projective map, unchanged

BUILT = {"light_head": 36.2, "transom_top": 34.88, "transom_foot": 34.14, "light_sill": 30.0}

# HABS 14, column x 972-988 (photograph) and the same columns on the render.
H14 = {"photo": {"light_head": 439.5, "transom_top": 474.0, "transom_foot": 487.5, "light_sill": 552.5},
       "render": {"light_head": 429.5, "transom_top": 452.0, "transom_foot": 465.5, "light_sill": 538.5}}
# HABS 17, the light's column: x 1265-1273 on the photograph, 1263-1265 on the render (its
# camera draws the light about 4 px west and 13 px lower than the print).
H17 = {"photo": {"light_head": 360.5, "transom_top": 380.3, "transom_foot": 384.5, "light_sill": 423.3},
       "render": {"light_head": 373.5, "transom_top": 385.3, "transom_foot": 391.5, "light_sill": 426.0}}

# Joint minima (degrees from the west spring, through the crown) on HABS 14's fan.
FAN = {"centre_px": {"photo": [979, 452], "render": [982.5, 443]},
       "photo_joints_deg": [30, 53, 75, 101, 125, 151],
       "render_joints_deg": [13, 29, 45, 63, 80, 97, 115, 134, 151, 168],
       "voussoirs_built": 11}


def h14():
    out = {}
    for side in ("photo", "render"):
        f = read_fan.projective([(read_fan.ANCHOR_NG[k], r) for k, r in read_fan.H14[side].items()])
        out[side] = {k: f(r) for k, r in H14[side].items()}
    return out


def h17():
    out = {}
    for side in ("photo", "render"):
        p = H17[side]
        scale = (BUILT["light_head"] - BUILT["light_sill"]) / (p["light_sill"] - p["light_head"])
        out[side] = {k: BUILT["light_head"] - (r - p["light_head"]) * scale for k, r in p.items()}
    return out


def less_method(raw):
    rows = {}
    for k in ("transom_top", "transom_foot", "light_head", "light_sill"):
        bias = raw["render"][k] - BUILT[k]
        photo = raw["photo"][k] - bias
        rows[k] = {"photo_ng": round(raw["photo"][k], 2), "render_ng": round(raw["render"][k], 2),
                   "built_ng": BUILT[k], "photo_less_method_ng": round(photo, 2),
                   "photo_over_built_ft": round(photo - BUILT[k], 2)}
    rows["transom_centre_over_built_ft"] = round(
        (rows["transom_top"]["photo_over_built_ft"] + rows["transom_foot"]["photo_over_built_ft"]) / 2, 2)
    return rows


def derive():
    a, b = less_method(h14()), less_method(h17())
    b["note"] = "head and sill are this view's scale, so they read as built by construction"
    gaps = [y - x for x, y in zip(FAN["photo_joints_deg"], FAN["photo_joints_deg"][1:])]
    rgaps = [y - x for x, y in zip(FAN["render_joints_deg"], FAN["render_joints_deg"][1:])]
    mean = sum(gaps) / len(gaps)
    fan = {**FAN, "photo_joint_spacing_deg": round(mean, 1), "render_joint_spacing_deg": round(sum(rgaps) / len(rgaps), 1),
           "voussoirs_read": round(180 / mean),
           "keyed": "no joint within 10 degrees of the crown (75 and 101): a keystone, so an odd count"}
    drop = round((a["transom_centre_over_built_ft"] + b["transom_centre_over_built_ft"]) / 2, 2)
    return {"ticket": "T-3137", "built_before": BUILT, "habs14": a, "habs17": b,
            "transom_centre_mean_over_built_ft": drop, "fan": fan,
            "ruled": {"transom_ng": [33.74, 34.48], "drop_ft": 0.4, "stilt_over_transom_ft": round(35.15 - 34.48, 2),
                      "voussoirs": 7, "head_ng": 36.2, "spring_ng": 35.15, "sill_ng": 30.0}}


def profile():
    import numpy as np
    from PIL import Image
    from scipy.ndimage import gaussian_filter1d, map_coordinates
    im = np.asarray(Image.open(ROOT / "docs/RESEARCH/photo-match/glessner_house/habs-14-north-inclined-side-by-side.jpg").convert("L"), float)
    for side, off in (("photo", 0), ("render", 1824)):
        cx, cy = FAN["centre_px"][side]
        ang = np.arange(5, 176, 1.0)
        rs = np.arange(35, 75, 1.0)
        p = np.array([map_coordinates(im, [cy - rs * np.sin(t), off + cx - rs * np.cos(t)], order=1).mean()
                      for t in np.radians(ang)])
        p -= gaussian_filter1d(p, 12)
        print(side, [int(ang[i]) for i in range(2, len(p) - 2) if p[i] == p[i - 2:i + 3].min() and p[i] < -4])


if __name__ == "__main__":
    if "--profile" in sys.argv:
        profile(); sys.exit(0)
    out = derive()
    path = HERE / "readings.json"
    text = json.dumps(out, indent=1) + "\n"
    if "--check" in sys.argv:
        sys.exit(0 if path.read_text() == text else "readings.json differs from a re-derivation")
    path.write_text(text)
    print(text)
