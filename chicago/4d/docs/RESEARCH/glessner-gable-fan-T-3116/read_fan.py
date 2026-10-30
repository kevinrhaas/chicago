#!/usr/bin/env python3
"""T-3116: the 18th Street gable's fan (and the light under it) read camera-free.

    python3 docs/RESEARCH/glessner-gable-fan-T-3116/read_fan.py          print + write readings.json
    python3 docs/RESEARCH/glessner-gable-fan-T-3116/read_fan.py --check  re-derive and compare

Neither camera is trusted above the north pairs: both draw sheet 6's crest high (HABS 14
about 15 px, HABS 01 about 12). So each photograph is read on its own vertical through the
stack and the light, scaled by features whose heights it does not set: sheet 6's crest and
both stones (T-3024's record), and the north pairs' sill and head (T-2850, solved on HABS 13
and 14 together). HABS 14 is inclined, so that vertical is a 1-D projective map (three
parameters, seven anchors); HABS 01 is level, so it is linear (two anchors). The same fit run
on the render, with the render's own rows, returns the built heights: its error is the
method's, and is taken off the photograph's reading.

Rows are hand picks off the side-by-sides in docs/RESEARCH/photo-match/glessner_house/
(GLB 22360520, before this ticket), read at 3-4x with a ruler, HABS 14's photograph also
read histogram-equalised. Heights are feet above north grade (ng)."""
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CREST_NG = 48.62 + 0.74 - 0.2      # sheet 6's printed crest, door datum -> ng
ANCHOR_NG = {"pair_sill": 19.83, "pair_head": 24.52, "date_foot": 43.3, "date_top": 44.75,
             "device_foot": 45.8, "device_top": 47.2, "crest": CREST_NG}
BUILT_NG = {"fan_crown": 39.15, "light_head": 35.2, "transom_top": 33.88, "transom_foot": 33.14,
            "light_sill": 29.0, "coping_meets": 43.3}

# HABS 14, column x ~975. The pairs' rows are the camera's (its solve fixes them; the print's
# white frames and the render's dark ones are not the same edge), interpolated to the stack.
H14 = {
    "photo": {"pair_sill": 734.6, "pair_head": 644.3, "date_foot": 324.5, "date_top": 302,
              "device_foot": 287, "device_top": 263, "crest": 230},
    "render": {"pair_sill": 734.6, "pair_head": 644.3, "date_foot": 307, "date_top": 280,
               "device_foot": 266, "device_top": 242.5, "crest": 216},
    "read_photo": {"fan_crown": 372, "light_head": 441, "transom_top": 472, "transom_foot": 487,
                   "light_sill": 553, "coping_meets": 333},
    "read_render": {"fan_crown": 378, "light_head": 447, "transom_top": 470, "transom_foot": 483,
                    "light_sill": 557, "coping_meets": 306},
}
# HABS 01, column x ~250 (pairs' heads interpolated between the two pairs).
H01 = {
    "photo": {"pair_head": 648, "crest": 444},
    "render": {"pair_head": 653.5, "crest": 431},
    "read_photo": {"fan_crown": 521, "light_head": 554, "light_sill": 607.5, "coping_meets": 501},
    "read_render": {"fan_crown": 524, "light_head": 560, "light_sill": 614, "coping_meets": 486},
}


def projective(anchors):
    A = np.array([[r, 1, -r * z] for z, r in anchors]); y = np.array([z for z, _ in anchors])
    (a, b, c), *_ = np.linalg.lstsq(A, y, rcond=None)
    return lambda r: float((a * r + b) / (c * r + 1))


def linear(anchors):
    (z0, r0), (z1, r1) = anchors
    return lambda r: z0 + (r - r0) * (z1 - z0) / (r1 - r0)


def read(view, fit):
    out = {}
    maps = {}
    for side in ("photo", "render"):
        anchors = [(ANCHOR_NG[k], r) for k, r in view[side].items()]
        f = fit(anchors)
        maps[side] = f
        out[f"{side}_anchor_residual_ft"] = round(max(abs(f(r) - z) for z, r in anchors), 2)
    for k in view["read_photo"]:
        photo = maps["photo"](view["read_photo"][k]); render = maps["render"](view["read_render"][k])
        bias = render - BUILT_NG[k]
        out[k] = {"photo_ng": round(photo, 2), "render_ng": round(render, 2), "built_ng": BUILT_NG[k],
                  "photo_over_built_ft": round(photo - bias - BUILT_NG[k], 2)}
    return out


def derive():
    h14 = read(H14, projective); h01 = read(H01, linear)
    keys = ("fan_crown", "light_head", "light_sill")
    mean = float(np.mean([v[k]["photo_over_built_ft"] for v in (h14, h01) for k in keys]))
    return {"ticket": "T-3116", "habs14": h14, "habs01": h01,
            "mean_rise_fan_head_sill_ft": round(mean, 2),
            "ruled": {"rise_ft": 1.0, "light_ng": [30.0, 36.2], "spring_ng": 35.45,
                      "transom_ng": [34.14, 34.88], "ring_ft": 4.7, "fan_crown_ng": 40.15,
                      "coping_meets_ng": "kept at 43.3 (T-3024)"}}


if __name__ == "__main__":
    out = derive()
    path = HERE / "readings.json"
    text = json.dumps(out, indent=1) + "\n"
    if "--check" in sys.argv:
        sys.exit(0 if path.read_text() == text else "readings.json differs from a re-derivation")
    path.write_text(text)
    print(text)
