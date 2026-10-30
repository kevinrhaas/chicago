#!/usr/bin/env python3
"""T-3027: Glessner's south stack in Taylor 2135, its plan place read against HABS sheets 6 and 4.

T-2858 refitted Taylor 2135's camera on the ten first-floor jambs and withheld the three stacks
as checks. The south stack's north face read 14.6 px left of the photograph, the middle stack's
7-8 px and the north stack's within 4 px, a gradient along the roof that the jambs below do not
show. This reads the stack's plan place (W 14.18-21.8, S 57.2-61.2) against the sheets, says
what the photograph would need of it, and asks whether the camera explains the rest.

The sheet picks below are this ticket's. The shaft edges are the drawn lines, found by column
(sheet 6) or as the per-row median of the rock-faced outline (sheet 4). The toes were picked by
eye on full-resolution crops, +/- 3 px. The photograph picks are T-2857's
(docs/RESEARCH/glessner-prairie-front-T-2857/read_front.py, STACKS); none is re-picked.

  python3 docs/RESEARCH/glessner-south-stack-T-3027/read_stack.py     write readings.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import glessner_prairie_front as G  # noqa: E402  T-2858's camera, record frame and stacks
import read_front as T  # noqa: E402  (on G's path) T-2857's picks

Image.MAX_IMAGE_PIXELS = None
SHEETS = ROOT.parent / "prairie_1904_v1/research/public"
OUT = HERE / "readings.json"

# Sheet 6, front (east) elevation, plotted from 1966 phototheodolite pairs. Horizontal scale is
# T-2857's (feet bar, SHEET_BAR), feet from the north corner. Vertical: its printed datum
# leaders, 0.00 at the door (y 5952) and 48.62 at the top of the north chimney (y 2374.5), the
# pair T-2222's toe heights stand on.
S6_STACKS = {"south": (3450, 3860), "middle": (5930, 6230)}       # search windows, x
S6_TOE_Y = {"south": 2912, "middle": 2816}                        # flashing's foot, by eye
S6_DATUM_Y = {0.0: 5952.0, 48.62: 2374.5}

# Sheet 4, Section A-A, looking east at the east wing's court face, north to the left. Horizontal
# scale is T-2206's (data/comparisons/glessner/section-readings.json): the outer wall planes at
# canvas x 218 and 1602 of a 1791-px canvas are the 74-ft Prairie length.
S4_STACKS = {"south": (6950, 7500, 1250, 1950), "middle": (3800, 4150, 1250, 1950)}
S4_TOE_Y = {"south": 2150, "middle": 2148}                        # west apron's foot, by eye
S4_STONE_FOOT_Y = {"south": 2030, "middle": 2035}


def sheet(n):
    return np.array(Image.open(SHEETS / f"glessner-habs-sheet-{n}.png").convert("L"))


def sheet6_readings():
    a = sheet(6)
    pxft = np.polyfit([b[0] for b in T.SHEET_BAR], [b[1] for b in T.SHEET_BAR], 1)[0]
    vft = (S6_DATUM_Y[0.0] - S6_DATUM_Y[48.62]) / 48.62
    out = {}
    for name, (x0, x1) in S6_STACKS.items():
        cols = np.where((a[2350:3000, x0:x1] < 110).mean(0) > 0.5)[0] + x0
        north, south = float(cols.max()), float(cols.min())          # north is to the right
        out[name] = {
            "shaft_x_px": [south, north],
            "S_ft": [round((T.SHEET_N_CORNER - north) / pxft, 2), round((T.SHEET_N_CORNER - south) / pxft, 2)],
            "east_toe_y_px": S6_TOE_Y[name],
            "east_toe_ft_above_door": round((S6_DATUM_Y[0.0] - S6_TOE_Y[name]) / vft, 2),
        }
    return out, round(float(pxft), 3), round(float(vft), 3)


def sheet4_readings():
    a = sheet(4)
    x_n, x_s = 218 * 9648 / 1791, 1602 * 9648 / 1791
    pxft = (x_s - x_n) / 74.0
    out = {}
    for name, (x0, x1, y0, y1) in S4_STACKS.items():
        lo, hi = [], []
        for y in range(y0, y1, 10):
            d = np.where(a[y, x0:x1] < 110)[0] + x0
            if len(d):
                lo.append(d.min())
                hi.append(d.max())
        n_x, s_x = float(np.median(lo)), float(np.median(hi))
        out[name] = {"shaft_x_px": [n_x, s_x],
                     "S_ft": [round((n_x - x_n) / pxft, 2), round((s_x - x_n) / pxft, 2)],
                     "west_toe_y_px": S4_TOE_Y[name], "stone_foot_y_px": S4_STONE_FOOT_Y[name]}
    return out, round(pxft, 3)


def camera(cam):
    return np.array(cam["eye"]), np.array(cam["basis_right_up_forward"]), cam["focal_px"], np.array(cam["principal_px"])


def stack_edges(e, B, f, c):
    """Render minus photograph for each stack's left, right and top, as T-2858 reads them: the
    shaft's top box through the camera plus the cap's own overhang, drawn through T-2221's."""
    old = G.TAYLOR_BEFORE
    oe, oB, of, oc = np.array(old["eye"]), np.array(old["basis_right_up_forward"]), old["focal_px"], np.array(old["principal_px"])
    out = {}
    for name, p in G.stacks().items():
        ph, rd = T.STACKS[name]
        o = G.silhouette(p, oe, oB, of, oc)
        n = G.silhouette(p, e, B, f, c)
        out[name] = {lab: round(float(n[i] + (rd[i] - o[i]) - ph[i]), 1)
                     for i, lab in enumerate(("left_x", "right_x", "top_y")) if ph[i] is not None and rd[i] is not None}
    return out


def box_width(e, B, f, c):
    """The south stack's top box across, in px, against the photograph's picked width."""
    lo, hi, _ = G.silhouette(G.stacks()["south"], e, B, f, c)
    ph = T.STACKS["south"][0]
    return round(float(hi - lo), 1), float(ph[1] - ph[0])


def needed(e, B, f, c, off):
    """The move, in feet, that would put the south stack's right edge on the photograph: north
    (S smaller) or west (W larger), each alone."""
    rows = {}
    for axis, d in (("north_ft", np.array([0.0, G.FT, 0.0])), ("west_ft", np.array([-G.FT, 0.0, 0.0]))):
        p = G.stacks()["south"]
        a = G.silhouette(p, e, B, f, c)[1]
        b = G.silhouette([x + d for x in p], e, B, f, c)[1]
        rows[axis] = round(float(-off / (b - a)), 2)
    return rows


def refit(use, free_principal):
    """T-2858's solve (controls, ten jambs) with the principal point freed and/or chosen stacks
    admitted as controls. Returns the camera's residuals and every stack's."""
    cam = G.TAYLOR_BEFORE
    c0 = np.array(cam["principal_px"])
    sheet6, _, _ = G.sheet6()
    model = G.built(sheet6)
    old = cam["controls_xyz_px"]
    pts = np.array([p[:3] for p in old], float)
    uv = np.array([p[3:] for p in old], float)
    wx = np.array([0.0 if abs(p[0] - T.FRONT_U) < 1e-3 else 1.0 for p in old])
    eye_s = (T.FRONT_LEN - cam["eye"][1]) / G.FT
    jambs, jx = [], []
    for k, v in T.PHOTO["taylor-2135-ne"].items():
        if k not in T.MODEL or not v:
            continue
        z = 4.6 if k == "door" else (9.2 + 14.5) / 2 + G.DOOR_DATUM
        for j, (sj, xj) in enumerate(zip(model[k], v)):
            w = G.REVEAL_FT if (k != "door" and G.seen_reveal(j, sj, eye_s)) else 0.0
            jambs.append(G.metric(w, sj, z))
            jx.append(xj)
    jambs, jx = np.array(jambs), np.array(jx, float)

    def unpack(x):
        return x[:3], G.basis(*x[3:6]), math.exp(x[6]), (x[7:9] if free_principal else c0)

    def residual(x):
        e, B, f, c = unpack(x)
        d = G.project(pts, e, B, f, c) - uv
        d[:, 0] *= wx
        r = [d.ravel(), G.project(jambs, e, B, f, c)[:, 0] - jx]
        if use:
            s = stack_edges(e, B, f, c)
            r.append(np.array([v for n in use for v in s[n].values()]))
        return np.concatenate(r)

    F = np.array(cam["basis_right_up_forward"][2])
    yaw0 = math.atan2(F[1], F[0])
    lo = [-np.inf, -np.inf, 1.0, -np.inf, -0.5, -0.2, math.log(500)]
    hi = [np.inf, np.inf, 2.5, np.inf, 0.5, 0.2, math.log(20000)]
    starts = []
    for dy in (-15, -10, -5, 0, 5, 10, 15):            # T-2858's starts, plus the principal's
        for k in (0.9, 1.0, 1.1):
            for dc in ((-300, 0, 300, 600) if free_principal else (0,)):
                x0 = [*cam["eye"], yaw0 + math.radians(dy), math.asin(F[2]), 0.0, math.log(cam["focal_px"] * k)]
                starts.append(np.r_[x0, c0[0] + dc, c0[1]] if free_principal else np.r_[x0])
    if free_principal:
        lo, hi = lo + [-2000, -2000], hi + [4000, 4000]
    opt = min((least_squares(residual, x0, bounds=(lo, hi), xtol=1e-12, ftol=1e-12, max_nfev=8000)
               for x0 in starts), key=lambda o: o.cost)
    e, B, f, c = unpack(opt.x)
    nc = len(pts) * 2
    r = residual(opt.x)
    used = np.r_[np.column_stack((wx, np.ones(len(wx)))).ravel(), np.ones(len(jx))] > 0
    base = r[:nc + len(jx)]
    return {
        "stacks_fitted": use,
        "principal": "free" if free_principal else "held",
        "principal_px": [round(float(v), 1) for v in c],
        "focal_px": round(f, 1),
        "eye": [round(float(v), 3) for v in e],
        "controls_and_jambs_rms_px": round(float(np.sqrt(np.mean(base[used] ** 2))), 2),
        "jamb_residual_px": [round(float(v), 1) for v in r[nc:nc + len(jx)]],
        "stacks_px": stack_edges(e, B, f, c),
    }


def main():
    s6, s6_pxft, s6_vft = sheet6_readings()
    s4, s4_pxft = sheet4_readings()
    rec = json.loads(G.RECORD.read_text())["phases"][0]["form"]
    ch, pl = rec["chimneys"]["value"], rec["chimney_plans"]["value"]
    cam = json.loads((G.VIEWS / "taylor-2135-ne.json").read_text())
    e, B, f, c = camera(cam)
    now = stack_edges(e, B, f, c)
    width = box_width(e, B, f, c)
    move = needed(e, B, f, c, now["south"]["right_x"])
    drop6 = round(s6["middle"]["east_toe_ft_above_door"] - s6["south"]["east_toe_ft_above_door"], 2)
    runs = [refit(["south", "middle", "north"], False), refit(["middle", "north"], True),
            refit(["south", "middle", "north"], True)]
    result = {
        "ticket": "T-3027",
        "source_id": "habs_glessner_house_il_1015_drawings",
        "locator": "HABS IL-1015 sheet 6 (front elevation, 1966 photogrammetric plot) and sheet 4 (Section A-A, 1963)",
        "record": {"south": {"S": ch["south"]["S"], "W": pl["south"]["W"]},
                   "middle": {"S": ch["middle"]["S"], "W": pl["middle"]["W"]}},
        "sheet6": {"px_per_ft": s6_pxft, "vertical_px_per_ft": s6_vft, "stacks": s6,
                   "east_toe_drop_south_below_middle_ft": drop6,
                   "record_east_face_step_ft": round(pl["middle"]["W"][0] - pl["south"]["W"][0], 2)},
        "sheet4": {"px_per_ft": s4_pxft, "stacks": s4,
                   "west_toes_level": abs(S4_TOE_Y["south"] - S4_TOE_Y["middle"]) <= 3},
        "taylor_2135": {
            "camera": "the committed refit (T-2858)",
            "stacks_px": now,
            "south_box_width_px_vs_photograph": list(width),
            "south_move_to_close_right_edge_ft": move,
            "refits": runs,
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"sheet 6: south S {s6['south']['S_ft']}, middle S {s6['middle']['S_ft']}; east toes "
          f"{s6['south']['east_toe_ft_above_door']} / {s6['middle']['east_toe_ft_above_door']} ft (south {drop6} ft lower)")
    print(f"sheet 4: south S {s4['south']['S_ft']}, middle S {s4['middle']['S_ft']}; west toes y "
          f"{S4_TOE_Y['south']} / {S4_TOE_Y['middle']}")
    print(f"Taylor 2135 now: {now}; south box {width[0]} px across, photograph {width[1]}; "
          f"to close the right edge alone: {move}")
    for r in runs:
        print(f"  refit principal {r['principal']:<5} stacks {','.join(r['stacks_fitted']) or '-':<19} "
              f"rms {r['controls_and_jambs_rms_px']:>5} jambs {r['jamb_residual_px']} stacks {r['stacks_px']}")


if __name__ == "__main__":
    main()
