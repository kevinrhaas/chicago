#!/usr/bin/env python3
"""T-3127: the width of the 18th Street gable's light, and the span of its fan, read on
HABS 14 and HABS 01 through the cameras the north pairs solved.

    python3 docs/RESEARCH/glessner-gable-light-T-3127/read_light.py          print + write readings.json
    python3 docs/RESEARCH/glessner-gable-light-T-3127/read_light.py --check  re-derive and compare

Both cameras are solved on the north wall's pair jambs (T-2850; HABS 01 level, by yaw), so
across the wall they are good where T-3116 found them high up the wall: a column read on the
print is carried to the north face's plane (S 74) and named by its plan W, the same
`face_w` the pairs' own jamb reading uses. The same picks taken on the render of the
build return the built jambs within the method's own error, and that error is taken off the
photograph's reading, as T-3116 did for its heights.

Columns are picks off the side-by-sides in docs/RESEARCH/photo-match/glessner_house/ (GLB
62d7f525..., before this ticket), each the half-way crossing of a column-mean profile across
the dark opening: HABS 14 over rows 505-540 (the sash) and 455-470 (the round head), HABS 01
over 585-600 and 560-570. The fan's span is read at the lower ends of its outer ring, where
it meets the wall's courses beside the spring (rougher picks: about 3 px each on HABS 14,
1 px each on HABS 01, where a pixel is about 0.2 ft)."""
import json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from glessner_north_pairs import face_w  # noqa: E402

VIEWS = ROOT / "data/reference_views/glessner_house"
BUILT = {"light_jambs_W": [18.05, 19.55], "fan_span_ft": 9.4}  # before this ticket

PICKS = {
    "habs-14-north-inclined": {
        "light": [  # row, photo [east, west], render [east, west]
            (520, [961.0, 999.0], [970.0, 997.0]),
            (462, [960.0, 998.5], [969.5, 996.5]),
        ],
        "fan": {"photo": (455, [890.0, 1070.0]), "render": (442, [895.0, 1067.0])},
    },
    "habs-01-northwest": {
        "light": [
            (590, [243.5, 253.5], [243.5, 251.5]),
            (565, [242.5, 253.5], [243.5, 251.5]),
        ],
        "fan": {"photo": (550, [228.0, 272.0]), "render": (550, [226.0, 267.0])},
    },
}


def camera(view):
    c = json.loads((VIEWS / f"{view}.json").read_text())
    if "basis_right_up_forward" not in c:  # HABS 01: a level camera stored by yaw alone
        a = math.radians(c["yaw_deg"])
        c["basis_right_up_forward"] = [[math.cos(a), -math.sin(a), 0], [0, 0, 1], [math.sin(a), math.cos(a), 0]]
    return c


def span(cam, row, xs):
    e, w = (face_w(cam, x, row) for x in xs)
    return e, w


def read(view):
    cam, p = camera(view), PICKS[view]
    rows = []
    for row, photo, render in p["light"]:
        pe, pw = span(cam, row, photo)
        re_, rw = span(cam, row, render)
        bias = (rw - re_) - (BUILT["light_jambs_W"][1] - BUILT["light_jambs_W"][0])
        rows.append({"row_px": row, "photo_W": [round(pe, 2), round(pw, 2)], "render_W": [round(re_, 2), round(rw, 2)],
                     "render_width_ft": round(rw - re_, 2), "photo_width_ft": round(pw - pe, 2),
                     "photo_width_less_method_ft": round(pw - pe - bias, 2),
                     "photo_centre_less_render_ft": round((pe + pw) / 2 - (re_ + rw) / 2, 2)})
    (pr, px), (rr, rx) = p["fan"]["photo"], p["fan"]["render"]
    pe, pw = span(cam, pr, px)
    re_, rw = span(cam, rr, rx)
    fan = {"photo_span_ft": round(pw - pe, 2), "render_span_ft": round(rw - re_, 2),
           "photo_span_scaled_ft": round((pw - pe) / (rw - re_) * BUILT["fan_span_ft"], 2)}
    return {"light": rows, "fan": fan}


def derive():
    out = {"ticket": "T-3127", "built_before": BUILT}
    for view in PICKS:
        out[view] = read(view)
    widths = [r["photo_width_less_method_ft"] for v in PICKS for r in out[v]["light"]]
    out["light_width_mean_ft"] = round(sum(widths) / len(widths), 2)
    out["fan_span_scaled_mean_ft"] = round(sum(out[v]["fan"]["photo_span_scaled_ft"] for v in PICKS) / len(PICKS), 2)
    out["ruled"] = {"light_W": [17.75, 19.85], "width_ft": 2.1, "centre_W": 18.8,
                    "head_ng": 36.2, "spring_ng": 35.15, "sill_ng": 30.0, "transom_ng": [34.14, 34.88],
                    "ring_ft": 5.0, "fan_crown_ng": 40.15, "fan_span_ft": 10.0}
    return out


if __name__ == "__main__":
    out = derive()
    path = HERE / "readings.json"
    text = json.dumps(out, indent=1) + "\n"
    if "--check" in sys.argv:
        sys.exit(0 if path.read_text() == text else "readings.json differs from a re-derivation")
    path.write_text(text)
    print(text)
