#!/usr/bin/env python3
"""T-2850: the north gable pairs' sill and head, measured by HABS 13 and HABS 14.

Both north cameras were fitted with the upper pairs' heights ASSUMED: T-2200's HABS 13
camera took the corridor rows' 19.25-22.25 ft as its upper-window controls, and T-2470's
HABS 14 camera took the 20.0-25.25 ft the record now builds. Neither photograph was ever
asked what the heights are, so a camera fitted on one assumption cannot test it.

This solve leaves the pairs' sill S and head H free. Each camera is refitted from the
controls whose heights are printed or not in question — the corner at grade, the narrow
first-floor light's course interval (HABS sheet 5's beds 8-15, 9.3044-14.7471 ft ng
since T-3045 laid the courses above bed 7 4.5 % over its printed inches) and, in HABS 14,
the east eave — plus every upper-window corner at its plan position (W, +/-0.4 ft) with
its height an unknown shared by the pair row. Pose, focal length, S and H are solved
together; the principal point is held at the plate's centre, and moved by 5% of the
plate in four directions as a sensitivity case.

The picks are T-2200's (HABS 13, observations.json) and T-2470's (HABS 14, the camera's
aperture_controls_W_z_px); none is re-picked here, so the reading cannot have been
steered by its own answer. The ruling stands on both photographs agreeing.

T-2868 adds the pairs' JAMBS. Each pair is two lights either side of a colonnette, and
the record had the inner jambs at the plan's 1.9-ft pier (sheet 3, +/-0.4 ft). The
photographs' stone-face edges (JAMB_PICKS, read off column-brightness profiles across
the upper sash) are carried through each solved camera onto the wall face (S 0); and,
because the solve itself took the inner corners at their plan W, they are read again
through a camera re-solved WITHOUT the inner corners, so the reading cannot be the
solve's own assumption handed back. The record's inner jambs must stand within
JAMB_TOLERANCE_FT of the photographs' mean.

  python3 tools/glessner_north_pairs.py           write data/comparisons/glessner/north-pairs.json
  python3 tools/glessner_north_pairs.py --cameras also write both solved cameras into
                                                  data/reference_views/glessner_house/
  python3 tools/glessner_north_pairs.py --check   exit 1 if stale, if a reference camera is not
                                                  the solved one, or if the record's pairs stand
                                                  outside the photographs' reading
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
GLESSNER = ROOT / "data/comparisons/glessner"
OUT = GLESSNER / "north-pairs.json"
RECORD = ROOT / "data/structures/glessner_house.json"
VIEWS = ROOT / "data/reference_views/glessner_house"
FT = 0.3048
RECESS_FT = 1.0  # glass set back in the wall, as T-2200 associates its window picks
TOLERANCE_FT = 0.5  # the record's pair bounds must sit within this of the reading
JAMB_TOLERANCE_FT = 0.15  # the record's inner jambs against the photographs' mean
INNER_W = (10.1, 12.0, 28.1, 30.0)  # the plan's inner jambs, which the solve takes as controls

# T-2868: x px of each jamb's STONE FACE edge across the upper sash (row_px), east pair
# then west pair, each in W order [outer, inner, inner, outer] (W rises westward from Prairie);
# None where a pole hides the edge. The inner edges are the colonnette
# capital's edges, which stand at the wall face: on the east pair each print shows the
# capital about 27 px wide over a shaft about 21 px wide, with a dark strip of shadow
# between shaft and sash. The west pair's pier is crossed by a utility pole in both
# prints: HABS 13 shows the capital either side of it, HABS 14 only its east edge.
JAMB_PICKS = {
    "habs-13-north-level": {"row_px": 222, "east": [829.5, 897.5, 925.5, 990.0],
                            "west": [None, 1277.0, 1303.0, None]},
    "habs-14-north-inclined": {"row_px": 682, "east": [765.5, 826.0, 851.5, 911.5],
                               "west": [None, None, 1206.5, None]},
}


def metric(w, s, z):
    return np.array([(161.25 - w) * FT, (74 - s) * FT, z * FT])


def basis(yaw, pitch, roll):
    f = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])
    r = np.array([math.sin(yaw), -math.cos(yaw), 0.0])
    u = np.cross(r, f)
    return np.array([r * math.cos(roll) + u * math.sin(roll), u * math.cos(roll) - r * math.sin(roll), f])


def project(points, pose, f, c):
    q = (np.asarray(points) - pose[:3]) @ basis(*pose[3:6]).T
    z = np.maximum(q[:, 2], 0.05)
    return np.column_stack((c[0] + f * q[:, 0] / z, c[1] - f * q[:, 1] / z))


def controls():
    """Per view: fixed controls [(id, W, S, z_ft, px)] and pair corners [(id, W, row, px)]."""
    obs = json.loads((GLESSNER / "observations.json").read_text())
    v13 = next(v for v in obs["views"] if v["id"] == "north-level")
    fixed13, pairs13 = [], []
    for p in v13["landmarks"]:
        w, s, z = p["building_ft"]
        s += p.get("recess_ft", 0)
        if p["id"].startswith(("upper-", "west-upper", "far-upper")):
            pairs13.append((p["id"], w, "head" if p["id"].endswith("head") else "sill", p["observed_px"]))
        else:
            fixed13.append((p["id"], w, s, z, p["observed_px"]))
    cam14 = json.loads((VIEWS / "habs-14-north-inclined.json").read_text())
    fixed14, pairs14 = [], []
    for w, z, px in cam14["solve"]["aperture_controls_W_z_px"]:
        if z in (20, 25.25):
            pairs14.append((f"W{w}-{'head' if z == 25.25 else 'sill'}", w, "head" if z == 25.25 else "sill", px))
        elif z in narrow_light():
            fixed14.append((f"narrow-W{w}-z{z}", w, RECESS_FT, z, px))
    v14 = next(v for v in obs["views"] if v["id"] == "north-inclined")
    for p in v14["landmarks"]:
        if p["id"] in ("corner-base", "east-eave"):
            w, s, z = p["building_ft"]
            fixed14.append((p["id"], w, s, z, p["observed_px"]))
    return {
        "habs-13-north-level": (v13["image_size"], v13["seed_camera_m"], fixed13, pairs13),
        "habs-14-north-inclined": (v14["image_size"], v14["seed_camera_m"], fixed14, pairs14),
    }


# T-2470's off-plane controls for HABS 14: the north gable stack's crest on the north
# face, and the north tower's depth control. Every other control is on the north wall's
# plane, and a plane alone cannot separate the camera's distance from its focal length.
DEPTH14 = [("stack-crest", 18.8, 0.0, 49.36, [973, 232]), ("tower-depth", 40.0, 18.5, 46.6, [1258, 372])]
HEIGHT_M = (1.0, 2.5)  # T-2200's camera-height assumption for both north plates


def solve(image, seed_m, fixed, pairs, offset=(0.0, 0.0), focal=None, free_principal=False):
    """Pose [, focal] [, principal shift], sill S and head H, by least squares."""
    c0 = np.array([image[0] / 2 + offset[0], image[1] / 2 + offset[1]])
    cam, target = np.array(seed_m, float)
    d = target - cam
    cam[2] = min(max(cam[2], HEIGHT_M[0] + 1e-3), HEIGHT_M[1] - 1e-3)
    x0 = np.r_[cam, math.atan2(d[1], d[0]), math.atan2(d[2], np.hypot(*d[:2])), 0.0,
               math.log(focal or image[0] * 38 / 36), 19.25, 22.25, 0.0, 0.0]
    fixed_xyz = np.array([metric(w, s, z) for _, w, s, z, _ in fixed])
    fixed_px = np.array([px for *_, px in fixed], float)
    pair_px = np.array([px for *_, px in pairs], float)

    def unpack(x):
        return (focal or math.exp(x[6])), c0 + (x[9:11] if free_principal else 0.0)

    def residual(x):
        f, c = unpack(x)
        pts = np.array([metric(w, RECESS_FT, x[7] if row == "sill" else x[8]) for _, w, row, _ in pairs])
        return np.r_[(project(fixed_xyz, x, f, c) - fixed_px).ravel(), (project(pts, x, f, c) - pair_px).ravel()]

    span = np.array([150, 150, 50, 1.0, 0.8, 0.18, 0.7, 8, 8, 300, 300])
    lo, hi = x0 - span, x0 + span
    lo[1] = 22.7  # in the street, north of the wall
    lo[2], hi[2] = HEIGHT_M
    opt = least_squares(residual, x0, bounds=(lo, hi), xtol=1e-12, ftol=1e-12, gtol=1e-10, max_nfev=8000)
    f, c = unpack(opt.x)
    err = np.linalg.norm(residual(opt.x).reshape(-1, 2), axis=1)
    return opt, err, f, c


def face_w(camera, x, y, s=0.0):
    """The W at which pixel (x, y) meets the north wall's plane at depth S s."""
    b = np.array(camera["basis_right_up_forward"])
    f, c, eye = camera["focal_px"], camera["principal_px"], np.array(camera["eye"])
    d = (x - c[0]) / f * b[0] + (c[1] - y) / f * b[1] + b[2]
    t = ((74 - s) * FT - eye[1]) / d[1]
    return 161.25 - (eye + t * d)[0] / FT


def read_jambs(camera, view):
    picks = JAMB_PICKS[view]
    return {pair: [None if x is None else round(float(face_w(camera, x, picks["row_px"])), 2) for x in picks[pair]]
            for pair in ("east", "west")}


def jambs(views, ctl, focal14):
    """T-2868: each pick through the solved camera and through one solved without the inner corners."""
    out = {}
    for name, v in views.items():
        image, seed, fixed, pairs = ctl[name]
        outer = [p for p in pairs if p[1] not in INNER_W]
        if name == "habs-14-north-inclined":
            opt, _, f, c = solve(image, seed, fixed + DEPTH14, outer, free_principal=True)
        else:
            opt, _, f, c = solve(image, seed, fixed, outer, focal=focal14)
        alt = {"eye": opt.x[:3].tolist(), "basis_right_up_forward": basis(*opt.x[3:6]).tolist(),
               "focal_px": float(f), "principal_px": [float(v) for v in c]}
        out[name] = {"solved_camera": read_jambs(v["camera"], name), "without_inner_corners": read_jambs(alt, name)}
    reading = {}
    for pair in ("east", "west"):
        inner = []
        for k in (1, 2):
            vals = [r[pair][k] for v in out.values() for r in v.values() if r[pair][k] is not None]
            inner.append(round(float(np.mean(vals)), 2))
        reading[pair] = {"inner_jambs_W": inner, "pier_ft": round(inner[1] - inner[0], 2)}
    return {"picks": JAMB_PICKS, "views": out, "reading": reading, "tolerance_ft": JAMB_TOLERANCE_FT}


def derive():
    ctl = controls()
    views, solved = {}, {}
    order = [("habs-14-north-inclined", True), ("habs-13-north-level", False)]
    for name, inclined in order:
        image, seed, fixed, pairs = ctl[name]
        if inclined:
            fixed = fixed + DEPTH14
            kw = {"free_principal": True}
        else:
            # The companion plate (same survey, same day's camera): HABS 13 has no
            # off-plane control in frame, so it takes HABS 14's focal length.
            kw = {"focal": solved["habs-14-north-inclined"]}
        opt, err, f, c = solve(image, seed, fixed, pairs, **kw)
        solved[name] = f
        w, h = image
        cases = np.array([solve(image, seed, fixed, pairs, (dx, dy), **kw)[0].x[7:9]
                          for dx, dy in ((-.05 * w, 0), (.05 * w, 0), (0, -.05 * h), (0, .05 * h))])
        ids = [i for i, *_ in fixed] + [i for i, *_ in pairs]
        views[name] = {
            "fixed_controls": len(fixed), "pair_corners": len(pairs),
            "focal": "solved, principal point free" if inclined else "HABS 14's, principal point at plate centre",
            "camera": {"eye": [round(float(v), 4) for v in opt.x[:3]],
                       "basis_right_up_forward": basis(*opt.x[3:6]).round(10).tolist(),
                       "focal_px": round(float(f), 3), "principal_px": [round(float(v), 2) for v in c]},
            "sill_ft": round(float(opt.x[7]), 2), "head_ft": round(float(opt.x[8]), 2),
            "principal_sensitivity_ft": {"sill": [round(float(cases[:, 0].min()), 2), round(float(cases[:, 0].max()), 2)],
                                         "head": [round(float(cases[:, 1].min()), 2), round(float(cases[:, 1].max()), 2)]},
            "rms_px": round(float(np.sqrt(np.mean(err ** 2))), 2), "max_px": round(float(err.max()), 2),
            "residual_px": {i: round(float(e), 2) for i, e in zip(ids, err)},
            "converged": bool(opt.success),
        }
    sills = [v["sill_ft"] for v in views.values()]
    heads = [v["head_ft"] for v in views.values()]
    return {
        "ticket": "T-2850",
        "not_a_reading": "A re-solve of picks already committed by T-2200 (HABS 13) and T-2470 (HABS 14); no new archival reading and no new pick.",
        "method": "Per photograph: pose, focal length and the pairs' shared sill S and head H solved together by least squares from fixed-height controls (corner at grade, the narrow first-floor light's course interval, beds 8-15 (9.3044-14.7471 ft since T-3045), in HABS 14 the east eave and T-2470's stack-crest and tower depth controls) and every upper-window corner at its plan W, 1 ft recess. HABS 14 solves its focal length and principal point; HABS 13, which has no off-plane control in frame, takes HABS 14's focal length with its principal point at the plate centre. Camera height bounded 1.0-2.5 m (T-2200). +/-5% principal-point moves are a sensitivity case, not a confidence interval.",
        "views": views,
        "reading_ft": {"sill": round(float(np.mean(sills)), 2), "head": round(float(np.mean(heads)), 2),
                       "views_disagree_by": {"sill": round(float(np.ptp(sills)), 2), "head": round(float(np.ptp(heads)), 2)}},
        "tolerance_ft": TOLERANCE_FT,
        "jambs": jambs(views, controls(), solved["habs-14-north-inclined"]),
    }


def record_jambs():
    """The record's inner jambs, east pair then west pair."""
    form = json.loads(RECORD.read_text())["phases"][0]["form"]
    pairs = sorted((it["at"] for it in form["openings_18th"]["value"]["items"] if it.get("style") == "north_gable_pair"),
                   key=lambda at: at[0][0])
    return {"east": [pairs[0][0][1], pairs[0][1][0]], "west": [pairs[1][0][1], pairs[1][1][0]]}


def narrow_light():
    """The narrow first-floor light's sill and head, ft ng: beds 8 and 15 (T-3045)."""
    form = json.loads(RECORD.read_text())["phases"][0]["form"]
    return tuple(form["opening_heights"]["value"]["openings_18th"]["first"])


def record_pairs():
    form = json.loads(RECORD.read_text())["phases"][0]["form"]
    return [it["z"] for it in form["openings_18th"]["value"]["items"] if it.get("style") == "north_gable_pair"]


CAMERA_KEYS = ("eye", "basis_right_up_forward", "focal_px", "principal_px")

# The solve is a least-squares fit, and another machine's BLAS/scipy lands it a few
# rounded digits away (CI read the basis 1e-7 off on T-2855), so --check compares
# numbers to these tolerances, never as text. Keyed by the nearest named field.
TOLERANCES = {"basis_right_up_forward": 1e-4, "eye": 0.01,  # unit vectors; metres
              "focal_px": 0.5, "principal_px": 0.5, "rms_px": 0.5, "max_px": 0.5, "residual_px": 0.5}
FT_TOLERANCE = 0.02  # every *_ft figure and views_disagree_by


def close(a, b, key=None):
    """True when a and b are the same structure with numbers equal to tolerance."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k], k if k in TOLERANCES or k.endswith("_ft")
                                                  or k == "views_disagree_by" else key) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, key) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return a == b
    tol = TOLERANCES.get(key, FT_TOLERANCE if key and (key.endswith("_ft") or key == "views_disagree_by") else 0)
    return abs(a - b) <= tol


def camera_drift(result):
    """The reference cameras must be the cameras this solve found (T-2850)."""
    drift = []
    for name, v in result["views"].items():
        cam = json.loads((VIEWS / f"{name}.json").read_text())
        if any(not close(cam.get(k), v["camera"][k], k) for k in CAMERA_KEYS) or cam.get("solve", {}).get("record") != f"data/comparisons/glessner/north-pairs.json#{name}":
            drift.append(name)
    return drift


def write_cameras(result):
    drift = camera_drift(result)
    for name, v in result["views"].items():
        if name not in drift:
            continue  # the committed camera agrees to tolerance; leave its bytes alone
        path = VIEWS / f"{name}.json"
        cam = json.loads(path.read_text())
        cam.update(v["camera"])
        solve = cam.setdefault("solve", {})
        solve["record"] = f"data/comparisons/glessner/north-pairs.json#{name}"
        solve["method"] = (f"T-2850: re-solved by tools/glessner_north_pairs.py with the north gable pairs' sill and head "
                           f"left free ({v['focal']}). Fixed controls: {v['fixed_controls']}; pair corners at plan W: "
                           f"{v['pair_corners']}. The pairs read sill {v['sill_ft']} ft, head {v['head_ft']} ft.")
        solve["coordinate_rms_px"] = v["rms_px"]
        solve["max_residual_px"] = v["max_px"]
        path.write_text(json.dumps(cam, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--cameras", action="store_true", help="also write the solved cameras into both reference views")
    a = ap.parse_args()
    result = derive()
    if a.check:
        if not OUT.exists() or not close(json.loads(OUT.read_text()), result):
            print("FAIL: north-pairs.json is stale; run python3 tools/glessner_north_pairs.py")
            return 1
        drift = camera_drift(result)
        if drift:
            print(f"FAIL: {drift} no longer carry the camera this solve finds; run with --cameras")
            return 1
    else:
        # Rewrite only on a real change: a re-solve that agrees to tolerance would
        # otherwise churn the last rounded digits on every machine it runs on.
        if not OUT.exists() or not close(json.loads(OUT.read_text()), result):
            OUT.write_text(json.dumps(result, indent=2) + "\n")
        if a.cameras:
            write_cameras(result)
    reading = result["reading_ft"]
    for name, v in result["views"].items():
        print(f"{name}: sill {v['sill_ft']} ft, head {v['head_ft']} ft; RMS {v['rms_px']} px over "
              f"{v['fixed_controls']} fixed + {v['pair_corners']} pair corners")
    bad = [z for z in record_pairs() if abs(z[0] - reading["sill"]) > TOLERANCE_FT or abs(z[1] - reading["head"]) > TOLERANCE_FT]
    if bad:
        print(f"FAIL: the record builds the north gable pairs at {bad}, outside {TOLERANCE_FT} ft of the "
              f"photographs' sill {reading['sill']} / head {reading['head']} ft")
        return 1
    jr = result["jambs"]["reading"]
    off = {pair: w for pair, w in record_jambs().items()
           if any(abs(a - b) > JAMB_TOLERANCE_FT for a, b in zip(w, jr[pair]["inner_jambs_W"]))}
    if off:
        print(f"FAIL: the record builds the pairs' inner jambs at {off}, outside {JAMB_TOLERANCE_FT} ft of the "
              f"photographs' {({p: r['inner_jambs_W'] for p, r in jr.items()})} (T-2868)")
        return 1
    print(f"PASS: the pairs' inner jambs stand within {JAMB_TOLERANCE_FT} ft of the photographs' "
          f"{({p: r['inner_jambs_W'] for p, r in jr.items()})} (T-2868)")
    print(f"PASS: the north gable pairs stand within {TOLERANCE_FT} ft of the photographs' reading "
          f"(sill {reading['sill']}, head {reading['head']} ft)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
