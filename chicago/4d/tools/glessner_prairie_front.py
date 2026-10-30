#!/usr/bin/env python3
"""T-2858: Glessner's Prairie front on HABS sheet 6, and Taylor 2135 refitted on its openings.

T-2857 read the front against sheet 6 and the three street photographs
(docs/RESEARCH/glessner-prairie-front-T-2857/). It left three questions, answered here:

1. WIDTHS. Sheet 6 draws the first-floor lights 4.3-4.45 ft between their outer lines; the
   record built 3.9 ft, and the two oblique NE photographs fitted 3.9 ft better. They are
   oblique: from the north-east each light's south reveal faces the camera, so the visible
   edge of the glass on that side is the sash, about 0.6 ft behind the arris, and it is
   seen displaced toward the camera. Projecting each such jamb from the camera's eye
   (no free parameter), sheet 6's openings fit all three photographs better than 3.9 ft
   does; the frontal HABS 16 prefers the sheet at any reveal depth.
2. THE CORNERS. Fitted on sheet 6's openings, each photograph's corner pick reads where
   sheet 6 draws the downspout (0.90 ft in from the NE corner, 0.82 from the SE), which is
   what the pick stands on. The piers stand as built.
3. TAYLOR 2135'S CAMERA. It was fitted on five controls, two of them the downspouts taken
   for the corners, and registered every jamb about 20 px left. Refitted here on the ten
   first-floor jambs (x only; the far jamb at the sash plane) with the controls' heights,
   the downspouts at sheet 6's positions. T-3058 freed its principal point (held at T-2221's
   value, no pose reached the stacks) and admits the three stacks' centres and tops and the
   photograph's plumb edges, which hold the pitch the freed principal point would trade
   against; the stacks' widths are the check.

The photograph picks are T-2857's (read_front.py); none is re-picked here.

  python3 tools/glessner_prairie_front.py            write data/comparisons/glessner/prairie-front.json
  python3 tools/glessner_prairie_front.py --camera   also write the refitted Taylor 2135 camera
  python3 tools/glessner_prairie_front.py --check    exit 1 if the report is stale, if the
                                                     reference camera is not the refitted one, or
                                                     if the record's openings are not sheet 6's
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, least_squares

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/RESEARCH/glessner-prairie-front-T-2857"))
import read_front as T2857  # noqa: E402  the picks and the sheet's columns, as T-2857 left them

RECORD = ROOT / "data/structures/glessner_house.json"
VIEWS = ROOT / "data/reference_views/glessner_house"
OUT = ROOT / "data/comparisons/glessner/prairie-front.json"
VERTICALS = ROOT / "docs/RESEARCH/glessner-taylor-camera-T-3058/verticals.json"
STACK_NAMES = ("south", "middle", "north")
FT = 0.3048
DOOR_DATUM = 0.74        # frame_ft.door_datum_above_grade_ft
REVEAL_FT = 0.6          # arris to the visible sash edge; the model's sash runs 0.49-0.98 ft back
REVEAL_CASES = (0.0, 0.49, 0.6, 0.95)
LIGHTS = ("ff_A", "ff_B", "ff_C", "ff_D")

# Taylor 2135's camera as T-2857 rendered through it (T-2221's fit), frozen here: its controls
# seed the refit, and the render picks were drawn through it.
TAYLOR_BEFORE = {"eye": [88.88668939847942, 40.906072571055496, 1.7], "basis_right_up_forward": [[-0.5981975964161029, 0.8009742359169728, 0.02449304062828582], [0.014656074848174232, -0.01962418174761879, 0.9997000004805348], [-0.8012145999119349, -0.5983771092613404, 0]], "focal_px": 2301.6831823661023, "principal_px": [415.50272048928315, 815.5140668074222], "controls_xyz_px": [[49.149, 0, 0, 45, 875], [49.149, 22.5552, 0, 904, 920], [49.149, 0, 8.4856, 56, 529], [49.149, 22.5552, 8.4856, 909, 463], [10.2108, 22.5552, 7.0409, 1426, 674]]}


def metric(w, s, z):
    """The record's building frame (feet, W west of the Prairie face, S south of 18th
    Street, z above north grade) in metres, as the reference cameras use it."""
    return np.array([(161.25 - w) * FT, (74.0 - s) * FT, z * FT])


def basis(yaw, pitch, roll):
    f = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])
    r = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
    u = np.cross(r, f)
    return np.array([r * math.cos(roll) + u * math.sin(roll), u * math.cos(roll) - r * math.sin(roll), f])


def project(points, eye, B, f, c):
    q = (np.atleast_2d(points) - eye) @ B.T
    return np.column_stack((c[0] + f * q[:, 0] / q[:, 2], c[1] - f * q[:, 1] / q[:, 2]))


def sheet6():
    """Sheet 6's openings, feet from the north end (T-2857's columns)."""
    px = np.polyfit([b[0] for b in T2857.SHEET_BAR], [b[1] for b in T2857.SHEET_BAR], 1)[0]
    from_n = lambda x: round((T2857.SHEET_N_CORNER - x) / px, 2)
    out = {k: (from_n(a), from_n(b)) for k, (a, b) in T2857.SHEET.items() if k != "door_fan_centre"}
    down = {side: round(abs((T2857.SHEET_N_CORNER if side == "north" else T2857.SHEET_S_CORNER)
                            - (a + b) / 2) / px, 2) for side, (a, b) in T2857.SHEET_DOWNSPOUT.items()}
    return out, from_n(T2857.SHEET["door_fan_centre"][0]), down


def built(sheet):
    """The openings this ticket builds: sheet 6's first-floor lights (place and width) and
    second-floor north group; the door and the rest as the record had them (T-2857)."""
    m = dict(T2857.MODEL)
    for k in LIGHTS + ("2f_trio_N",):
        m[k] = sheet[k]
    return m


def eye_frame(view):
    cam = json.loads((VIEWS / f"{view}.json").read_text())
    e = np.array(cam["eye"])
    return (T2857.FRONT_LEN - e[1]) / FT, abs(e[0] - T2857.FRONT_U) / FT


def seen_reveal(j, s, eye_s):
    """A north jamb's reveal faces south, a south jamb's north: is it turned to the camera?"""
    return eye_s > s if j == 0 else eye_s < s


def camera_free(view, model, reveal_ft):
    """T-2857's one-dimensional projective fit, the far jambs at the sash plane."""
    eye_s, eye_n = eye_frame(view)
    s, x = [], []
    for k, v in T2857.PHOTO[view].items():
        if k in model and k in T2857.MODEL and v:
            for j, (sj, xj) in enumerate(zip(model[k], v)):
                if k != "door" and seen_reveal(j, sj, eye_s):
                    sj = sj + (eye_s - sj) * reveal_ft / (eye_n + reveal_ft)
                s.append(sj)
                x.append(xj)
    fx, r = T2857.homography_1d(np.array(s), np.array(x, float))
    corner = None
    for name, at in (("N_corner", 0.0), ("S_corner", 74.0)):
        if name in T2857.PHOTO[view]:
            corner = (name, brentq(lambda t: fx(t) - T2857.PHOTO[view][name], at - 15, at + 15))
    return float(np.sqrt(np.mean(r ** 2))), corner


def stacks():
    rec = json.loads(RECORD.read_text())["phases"][0]["form"]
    ch, pl = rec["chimneys"]["value"], rec["chimney_plans"]["value"]
    out = {}
    for name, key in (("south", "south"), ("middle", "middle"), ("north", "north_gable")):
        top = ch[key]["top"][0] + (DOOR_DATUM if ch[key]["top"][1] == "door" else 0.0)
        out[name] = [metric(w, s, top) for w in pl[key]["W"] for s in ch[key]["S"]]
    return out


def silhouette(points, eye, B, f, c):
    uv = project(np.array(points), eye, B, f, c)
    return uv[:, 0].min(), uv[:, 0].max(), uv[:, 1].min()


def committed_stacks():
    """The stacks through the camera as it stood before T-2858: render minus photograph."""
    out = {}
    for name, (ph, rd) in T2857.STACKS.items():
        out[name] = {label: rd[i] - ph[i] for i, label in enumerate(("left_x", "right_x", "top_y"))
                     if ph[i] is not None and rd[i] is not None}
    return out


def verticals():
    """The photograph's plumb edges (x, y, lean dx/dy, rows), read by T-3058's
    docs/RESEARCH/glessner-taylor-camera-T-3058/read_verticals.py; the gate never opens the image."""
    d = json.loads(VERTICALS.read_text())
    return np.array([[e["x"], e["y"], e["lean"], e["rows"]] for e in d["edges"]], float)


def lean_residual(B, f, c, edges):
    """Each plumb edge's lean against the line to the vertical vanishing point, in px over the
    edge's own length (so a lean read on more rows weighs more)."""
    v = B @ np.array([0.0, 0.0, 1.0])
    vx, vy, vw = c[0] * v[2] + f * v[0], c[1] * v[2] - f * v[1], v[2]
    want = (vx - edges[:, 0] * vw) / (vy - edges[:, 1] * vw)
    return (edges[:, 2] - want) * edges[:, 3]


def stack_offsets(eye, B, f, c):
    """Each stack's record box (its shaft at the record's top height) through the camera against
    T-2857's photograph picks: box minus photograph for the centre, the top and the width. The
    built cap reads within about 1 px of the box (T-3058, read_caps.py), so nothing is carried."""
    out = {}
    for name, p in stacks().items():
        lo, hi, top = silhouette(p, eye, B, f, c)
        ph = T2857.STACKS[name][0]
        out[name] = {"centre_x": (lo + hi - ph[0] - ph[1]) / 2, "top_y": top - ph[2],
                     "width": (hi - lo) - (ph[1] - ph[0])}
    return out


def solve_taylor(model, down, reveal_ft=REVEAL_FT):
    cam = TAYLOR_BEFORE
    c0 = np.array(cam["principal_px"])
    old = cam["controls_xyz_px"]
    # The two Prairie corners' x picks stand on the downspouts (T-2857), whose standoff from
    # the wall no source gives: they control height only. The gable foot keeps both.
    pts = np.array([p[:3] for p in old], float)
    uv = np.array([p[3:] for p in old], float)
    wx = np.array([0.0 if abs(p[0] - T2857.FRONT_U) < 1e-3 else 1.0 for p in old])
    jambs, jx = [], []
    eye_s = (T2857.FRONT_LEN - cam["eye"][1]) / FT
    for k, v in T2857.PHOTO["taylor-2135-ne"].items():
        if k not in T2857.MODEL or not v:
            continue
        z = 4.6 if k == "door" else (9.2 + 14.5) / 2 + DOOR_DATUM
        for j, (sj, xj) in enumerate(zip(model[k], v)):
            w = reveal_ft if (k != "door" and seen_reveal(j, sj, eye_s)) else 0.0
            jambs.append(metric(w, sj, z))
            jx.append(xj)
    jambs, jx = np.array(jambs), np.array(jx, float)
    edges = verticals()
    F = np.array(cam["basis_right_up_forward"][2])
    yaw0 = math.atan2(F[1], F[0])
    # T-3058: the principal point is free. T-2221 fitted it with five controls and T-2858 held
    # it, and held, no pose reaches the stacks (T-3027: the south stack -13 px with all three
    # admitted). Freed, it trades against pitch, so the photograph's own plumb edges hold the
    # pitch and roll, and the three stacks' centres and tops are controls; their widths are not
    # fitted, and are the check.
    lo = [-np.inf, -np.inf, 1.0, -np.inf, -0.5, -0.2, math.log(500), -2000, -2000]
    hi = [np.inf, np.inf, 2.5, np.inf, 0.5, 0.2, math.log(20000), 4000, 4000]

    def unpack(x):
        return x[:3], basis(*x[3:6]), math.exp(x[6]), x[7:9]

    def residual(x):
        eye, B, f, c = unpack(x)
        d = project(pts, eye, B, f, c) - uv
        d[:, 0] *= wx
        st = stack_offsets(eye, B, f, c)
        return np.r_[d.ravel(), project(jambs, eye, B, f, c)[:, 0] - jx,
                     [st[n][k] for n in STACK_NAMES for k in ("centre_x", "top_y")],
                     lean_residual(B, f, c, edges)]

    # Every start, the committed camera turned through +/-10 degrees, scaled 0.9-1.1 and its
    # principal point moved across the frame, ends at one camera (T-3058 README).
    starts = [np.r_[cam["eye"], yaw0 + math.radians(dy), math.asin(F[2]), 0.0, math.log(cam["focal_px"] * k),
                    c0[0] + dc, c0[1]]
              for dy in (-10, 0, 10) for k in (0.9, 1.0, 1.1) for dc in (-300, 0, 300, 600)]
    opt = min((least_squares(residual, x0, bounds=(lo, hi), x_scale="jac", xtol=1e-12, ftol=1e-12,
                             max_nfev=8000) for x0 in starts), key=lambda o: o.cost)
    eye, B, f, c = unpack(opt.x)
    r = residual(opt.x)
    nc, nj, ns = len(pts) * 2, len(jx), 2 * len(STACK_NAMES)
    ctrl_res = r[:nc].reshape(-1, 2)
    used = np.r_[np.column_stack((wx, np.ones(len(wx)))).ravel(), np.ones(nj)] > 0
    st = stack_offsets(eye, B, f, c)
    fit = r[nc + nj:nc + nj + ns]
    leans = r[nc + nj + ns:] / edges[:, 3]
    return {
        "eye": [round(float(v), 6) for v in eye],
        "yaw_deg": round((90.0 - math.degrees(opt.x[3])) % 360, 6),
        "pitch_deg": round(math.degrees(opt.x[4]), 3),
        "roll_deg": round(math.degrees(opt.x[5]), 3),
        "basis_right_up_forward": [[round(float(v), 10) for v in row] for row in B],
        "focal_px": round(f, 4),
        "principal_px": [round(float(v), 3) for v in c],
        "controls_xyz_px": [[round(float(v), 4) for v in p] + [float(u), float(w)] for p, (u, w) in zip(pts, uv)],
        "control_residual_px": [[None if not k else round(float(a), 2), round(float(b), 2)]
                                for k, (a, b) in zip(wx, ctrl_res)],
        "jamb_residual_px": [round(float(v), 2) for v in r[nc:nc + nj]],
        "rms_px": round(float(np.sqrt(np.mean(r[:nc + nj][used] ** 2))), 2),
        "stacks_px": {n: {k: round(float(v), 1) for k, v in row.items()} for n, row in st.items()},
        "stack_fit_rms_px": round(float(np.sqrt(np.mean(fit ** 2))), 1),
        "verticals": {"edges": len(edges), "lean_rms": round(float(np.sqrt(np.mean(leans ** 2))), 4)},
    }


def derive():
    sheet, door_fan, down = sheet6()
    model = built(sheet)
    before_stacks = committed_stacks()
    views = {}
    for view in T2857.PHOTO:
        rows = {}
        for d in REVEAL_CASES:
            before, _ = camera_free(view, T2857.MODEL, d)
            after, corner = camera_free(view, model, d)
            rows[f"{d:.2f}"] = {"record_before_rms_px": round(before, 2), "sheet6_rms_px": round(after, 2),
                                "corner": corner[0], "corner_pick_ft_from_N": round(corner[1], 2)}
        views[view] = rows
    taylor = solve_taylor(model, down)
    cases = {f"{d:.2f}": solve_taylor(model, down, d)["stack_fit_rms_px"] for d in REVEAL_CASES}
    return {
        "ticket": "T-2858",
        "not_a_reading": "a re-fit of T-2857's picks (docs/RESEARCH/glessner-prairie-front-T-2857/); nothing is re-picked",
        "sheet6_openings_ft_from_N": {k: list(v) for k, v in sheet.items()},
        "sheet6_door_fan_centre_ft_from_N": door_fan,
        "sheet6_downspouts_ft_in_from_corner": down,
        "built": {k: list(model[k]) for k in LIGHTS + ("2f_trio_N", "door")},
        "reveal_ft": REVEAL_FT,
        "camera_free": views,
        "taylor_2135_before_stacks_px": before_stacks,
        "taylor_2135": taylor,
        "taylor_2135_stack_fit_rms_by_reveal_px": cases,
        "rulings": {
            "widths": "sheet 6's outer lines: with any reveal 0.49-0.95 ft every photograph fits them at least as well as the record's 3.9 ft, and the frontal HABS 16 much better",
            "door": "kept at 30.4-35.4: sheet 6 gives only the fan's centre (32.53, its reveal hatched), and the photographs split on it (Taylor 2135 prefers the record, HABS 16 the sheet)",
            "corners": "kept: on sheet 6's openings each corner pick reads within about 0.5 ft of the downspout it stands on",
            "basement_grilles": "centred under the moved lights at the record's 3.9 ft; sheet 6 draws them centred under each light about 4.0 ft wide",
        },
    }


def record_openings():
    form = json.loads(RECORD.read_text())["phases"][0]["form"]["openings_prairie"]["value"]["items"]
    by = {i["what"]: i["at"] for i in form}
    return by


def close(a, b, tol=0.05):
    """Numbers to tolerance (CI's scipy lands a solve about 1e-7 from a runner's, and a
    rounded figure can tip a last digit), everything else exactly."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= tol
    return a == b


def camera_agrees(cam, t):
    return (np.abs(np.array(cam["eye"]) - np.array(t["eye"])).max() <= 0.01
            and np.abs(np.array(cam["basis_right_up_forward"]) - np.array(t["basis_right_up_forward"])).max() <= 1e-4
            and abs(cam["focal_px"] - t["focal_px"]) <= 0.5
            and np.abs(np.array(cam["principal_px"]) - np.array(t["principal_px"])).max() <= 0.5)


def check(result):
    errs = []
    if not close(json.loads(OUT.read_text()), json.loads(json.dumps(result))):
        errs.append(f"{OUT.relative_to(ROOT)} is stale: run python3 tools/glessner_prairie_front.py")
    cam = json.loads((VIEWS / "taylor-2135-ne.json").read_text())
    t = result["taylor_2135"]
    if not camera_agrees(cam, t):
        errs.append("taylor-2135-ne.json is not the refitted camera: run with --camera")
    rec = record_openings()
    lights = sorted(tuple(a) for a in rec["first-floor windows"])
    want = sorted(tuple(result["built"][k]) for k in LIGHTS)
    if lights != want:
        errs.append(f"first-floor windows {lights} are not sheet 6's {want}")
    if tuple(rec["second-floor group of three"]) != tuple(result["built"]["2f_trio_N"]):
        errs.append("the second-floor north group is not at sheet 6's place")
    grilles = sorted(tuple(a) for a in rec["basement lights, 3 x 3"])
    centres = sorted((a + b) / 2 for a, b in want)
    if len(grilles) != 4 or any(abs((a + b) / 2 - m) > 0.01 for (a, b), m in zip(grilles, centres)):
        errs.append("the basement grilles are not centred under the first-floor lights")
    for e in errs:
        print("FAIL", e)
    return not errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    result = derive()
    if a.check:
        ok = check(result)
        print("Glessner's Prairie front stands on sheet 6, Taylor 2135 refitted" if ok else "")
        sys.exit(0 if ok else 1)
    if not (OUT.exists() and close(json.loads(OUT.read_text()), json.loads(json.dumps(result)))):
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    t = result["taylor_2135"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    for view, rows in result["camera_free"].items():
        r = rows[f"{REVEAL_FT:.2f}"]
        print(f"  {view:<22} record {r['record_before_rms_px']:.2f} px -> sheet 6 {r['sheet6_rms_px']:.2f} px; "
              f"{r['corner']} pick at {r['corner_pick_ft_from_N']:.2f} ft from N")
    print(f"  Taylor 2135 refit: rms {t['rms_px']} px; jambs {t['jamb_residual_px']}; "
          f"principal {t['principal_px']}, f {t['focal_px']}, pitch {t['pitch_deg']}, roll {t['roll_deg']}; "
          f"stacks {t['stacks_px']} (centres and tops rms {t['stack_fit_rms_px']}); verticals {t['verticals']}")
    if a.camera:
        path = VIEWS / "taylor-2135-ne.json"
        cam = json.loads(path.read_text())
        if camera_agrees(cam, t):
            print(f"{path.relative_to(ROOT)} already agrees to tolerance; left untouched")
            return
        for k in ("eye", "yaw_deg", "basis_right_up_forward", "focal_px", "principal_px"):
            cam[k] = t[k]
        cam["solve"]["method"] = (
            "T-3058: fitted on the ten first-floor jambs of T-2857 (x only; each jamb whose reveal faces the "
            f"camera at the sash, {REVEAL_FT} ft behind the arris), the five earlier controls (the two "
            "Prairie-corner x picks put on sheet 6's downspouts, so they control height only), the three "
            "stacks' centres and tops (their record boxes against T-2857's picks; the built caps read within "
            "about 1 px of the boxes) and the photograph's plumb edges (docs/RESEARCH/"
            "glessner-taylor-camera-T-3058/verticals.json, each lean weighted by its length). Principal "
            "point, pitch and roll free; height bounded 1.0-2.5 m; every start ends at this camera. The "
            "stacks' widths are not fitted and are the check (tools/glessner_prairie_front.py; "
            "data/comparisons/glessner/prairie-front.json).")
        cam["solve"]["controls_xyz_px"] = t["controls_xyz_px"]
        cam["solve"]["residual_px"] = t["control_residual_px"]
        cam["solve"]["jamb_residual_px"] = t["jamb_residual_px"]
        cam["solve"]["rms_px"] = t["rms_px"]
        cam["solve"].pop("stack_checks_px", None)
        cam["solve"]["stacks_px"] = t["stacks_px"]
        cam["solve"]["stack_fit_rms_px"] = t["stack_fit_rms_px"]
        cam["solve"]["verticals"] = t["verticals"]
        path.write_text(json.dumps(cam, indent=2) + "\n")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
