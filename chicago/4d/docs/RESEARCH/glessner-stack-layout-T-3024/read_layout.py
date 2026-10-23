#!/usr/bin/env python3
"""T-3024: the 18th Street stack's vertical layout, read on HABS sheet 6 and through the
HABS 14 and HABS 01 cameras.

    python3 docs/RESEARCH/glessner-stack-layout-T-3024/read_layout.py          print + write readings.json
    python3 docs/RESEARCH/glessner-stack-layout-T-3024/read_layout.py --check  re-derive and compare

The picks are hand-read pixel rows (each image was read at 4-6x with a ruler; see README.md).
Heights are feet above the footprint's grade (G); `ng` = G - 0.2, `door` = G - 0.74
(frame_ft and grade_datum in data/structures/glessner_house.json)."""
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIEWS = ROOT / "data" / "reference_views" / "glessner_house"
FT = 0.3048
NG, DOOR = 0.2, 0.74
CREST_G = 48.62 + DOOR          # sheet 6: '48.62 +/- 0.02 AT TOP OF NORTH CHIMNEY' (door datum)

# --- HABS sheet 6 (east elevation; the stack edge-on, its north face on the right) ---------
SHEET6 = {
    "top_drawn_px": 2360,       # the stack's drawn top
    "top_leader_px": 2374.5,    # the 48.62 dimension's leader line
    "door_leader_px": 5952.5,   # the 0.00 AT DOOR leader line
    "device_stone_px": [2524, 2634],
    "date_stone_px": [2692, 2800],
    "coping_meets_px": 2775,    # the coping's rolled end against the stack's east side
}


def sheet6():
    s = SHEET6
    ppf = (s["door_leader_px"] - s["top_leader_px"]) / 48.62
    out = {"px_per_ft": round(ppf, 2)}
    for anchor in ("top_drawn_px", "top_leader_px"):
        g = lambda y: CREST_G - (y - s[anchor]) / ppf
        out[anchor.replace("_px", "")] = {
            "device_stone_ng": [round(g(s["device_stone_px"][1]) - NG, 2), round(g(s["device_stone_px"][0]) - NG, 2)],
            "date_stone_ng": [round(g(s["date_stone_px"][1]) - NG, 2), round(g(s["date_stone_px"][0]) - NG, 2)],
            "coping_meets_G": round(g(s["coping_meets_px"]), 2)}
    return out


# --- cameras -------------------------------------------------------------------------------
def camera(view):
    cam = json.loads((VIEWS / f"{view}.json").read_text())
    if "basis_right_up_forward" in cam:
        b = np.array(cam["basis_right_up_forward"])
    else:                       # a level camera: yaw only
        y = math.radians(cam["yaw_deg"])
        b = np.array([[math.cos(y), -math.sin(y), 0], [0, 0, 1.0], [math.sin(y), math.cos(y), 0]])
    return b, cam["focal_px"], cam["principal_px"], np.array(cam["eye"])


def read(view, x, y, s=0.0):
    """(W, z G) where pixel (x, y) meets the north face's plane at depth S s."""
    b, f, c, eye = camera(view)
    d = (x - c[0]) / f * b[0] + (c[1] - y) / f * b[1] + b[2]
    t = ((74 - s) * FT - eye[1]) / d[1]
    p = eye + t * d
    return round(161.25 - p[0] / FT, 2), round(p[2] / FT, 2)


def project(view, w, z, s=0.0):
    b, f, c, eye = camera(view)
    q = (np.array([(161.25 - w) * FT, (74 - s) * FT, z * FT]) - eye) @ b.T
    return round(c[0] + f * q[0] / q[2], 1), round(c[1] - f * q[1] / q[2], 1)


# HABS 14 picks (photograph; the render picks were read off the T-3046 side-by-side, GLB 5fff90bb)
H14 = {"crest": (973, 230), "device_top": (975, 262), "device_foot": (975, 287),
       "date_top": (975, 302), "date_foot": (975, 324), "cross_east": (920, 309),
       "cross_west": (1028, 313), "coping_meets_east": (907, 331), "coping_meets_west": (1043, 334),
       "fan_crown": (975, 385)}
H14_RENDER_BEFORE = {"crest": (973, 216), "device_top": (975, 240), "device_foot": (975, 265),
       "date_top": (975, 270), "date_foot": (975, 301), "cross_east": (928, 292),
       "cross_west": (1030, 282), "coping_meets_east": (912, 297), "coping_meets_west": (1043, 295),
       "fan_crown": (975, 397)}
# HABS 01 (level camera): rows only, on the stack's east edge; the render's from the same side-by-side
H01 = {"crest": 444, "coping_meets_east": 501, "fan_crown": 523}
H01_RENDER_BEFORE = {"crest": 432, "coping_meets_east": 482, "fan_crown": 525}


def habs14():
    photo = {k: read("habs-14-north-inclined", *v) for k, v in H14.items()}
    shift = CREST_G - photo["crest"][1]          # anchor the photograph on sheet 6's crest
    render = {k: read("habs-14-north-inclined", *v) for k, v in H14_RENDER_BEFORE.items()}
    out = {"crest_shift_ft": round(shift, 2), "crest_projects_to_px": project("habs-14-north-inclined", 18.8, CREST_G)}
    for k in H14:
        out[k] = {"photo_G": photo[k][1], "photo_on_crest_G": round(photo[k][1] + shift, 2),
                  "render_before_G": render[k][1], "W": photo[k][0]}
    return out


def habs01():
    # the stack's height scale on this camera, from the record's two stones' outer edges
    ppf = (project("habs-01-northwest", 18.8, 43.8)[1] - project("habs-01-northwest", 18.8, 47.4)[1]) / 3.6
    d = {k: round(((H01[k] - H01["crest"]) - (H01_RENDER_BEFORE[k] - H01_RENDER_BEFORE["crest"])) / ppf, 2)
         for k in ("coping_meets_east", "fan_crown")}
    return {"px_per_ft": round(ppf, 2), "photo_lower_than_built_from_crest_ft": d,
            "crest_minus_fan_px": {"photo": H01["fan_crown"] - H01["crest"],
                                   "render_before": H01_RENDER_BEFORE["fan_crown"] - H01_RENDER_BEFORE["crest"]}}


def derive():
    return {"ticket": "T-3024", "sheet6": sheet6(), "habs14": habs14(), "habs01": habs01(),
            "record_after": {"parapet_ft": 0.5, "date_stone_ng": [43.3, 44.75], "crosses_ng": 44.05,
                             "device_stone_ng": [45.8, 47.2]}}


if __name__ == "__main__":
    out = derive()
    path = HERE / "readings.json"
    text = json.dumps(out, indent=1) + "\n"
    if "--check" in sys.argv:
        sys.exit(0 if path.read_text() == text else "readings.json differs from a re-derivation")
    path.write_text(text)
    print(text)
