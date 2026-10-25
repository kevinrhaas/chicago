#!/usr/bin/env python3
"""T-3065: the 18th Street stack's N-S depth, read off HABS sheet 6, and the stack through Taylor 2135.

Sheet 6 is the east elevation: it draws each stack edge-on, so a stack's drawn width is its N-S
depth. This finds each stack's two outline strokes (dark runs) at several rows above the ridge
and reports the centre-to-centre width at the sheet's 73.59 px/ft (T-3024's scale, from the 48.62
and 0.00 leaders). The middle and south stacks are the control: the record already carries their
N-S extents from this sheet. Then it projects the north stack's corners and date stones through
the committed Taylor 2135 camera, for the photograph's x.

  python3 docs/RESEARCH/glessner-stack-depth-T-3065/read_depth.py           write readings.json
  python3 docs/RESEARCH/glessner-stack-depth-T-3065/read_depth.py --check   exit 1 if it moved
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import glessner_prairie_front as G  # noqa: E402

SHEET6 = ROOT.parent / "prairie_1904_v1/research/public/glessner-habs-sheet-6.png"
OUT = HERE / "readings.json"
PX_PER_FT = 73.59
DARK = 110
# (stack, x window on the sheet, rows above the ridge cresting, record S extent)
STACKS = {"north": ((7880, 8105), (2370, 2390, 2410, 2430, 2470, 2500), (0.0, 2.6)),
          "middle": ((5960, 6200), (2380, 2410, 2450), (25.8, 28.6)),
          "south": ((3490, 3820), (2380, 2410, 2450), (57.2, 61.2))}


def strokes(a, row, x0, x1):
    """Centres of the outermost dark runs in [x0, x1) on a 5-row band."""
    r = a[row - 2:row + 3, x0:x1].mean(0)
    d = np.where(r < DARK)[0]
    runs, s = [], d[0]
    for p, q in zip(d[:-1], d[1:]):
        if q > p + 3:
            runs.append((s, p))
            s = q
    runs.append((s, d[-1]))
    runs = [r for r in runs if r[1] - r[0] >= 3]
    return x0 + (runs[0][0] + runs[0][1]) / 2, x0 + (runs[-1][0] + runs[-1][1]) / 2


def main():
    Image.MAX_IMAGE_PIXELS = None
    a = np.array(Image.open(SHEET6).convert("L")).astype(float)
    out = {"ticket": "T-3065", "sheet6_px_per_ft": PX_PER_FT, "stacks": {}}
    for name, ((x0, x1), rows, rec) in STACKS.items():
        w = [strokes(a, y, x0, x1) for y in rows]
        widths = [round((r - l) / PX_PER_FT, 2) for l, r in w]
        out["stacks"][name] = {"rows": list(rows), "strokes_px": [[round(l, 1), round(r, 1)] for l, r in w],
                               "depth_ft": widths, "depth_mean_ft": round(float(np.mean(widths)), 2),
                               "record_S": list(rec), "record_depth_ft": round(rec[1] - rec[0], 2)}
    cam = json.loads((G.VIEWS / "taylor-2135-ne.json").read_text())
    e, B, f, c = np.array(cam["eye"]), np.array(cam["basis_right_up_forward"]), cam["focal_px"], np.array(cam["principal_px"])
    pts = {"NE_z47": (15.25, 0, 47), "NW_z47": (22.35, 0, 47), "SE_z47": (15.25, 2.6, 47),
           "SE_z47_at_3.1": (15.25, 3.1, 47), "device_E_z45.8": (16.6, 0, 45.8), "device_W_z45.8": (21.0, 0, 45.8),
           "date_E_z43.3": (16.65, 0, 43.3), "date_W_z43.3": (20.95, 0, 43.3)}
    uv = G.project(np.array([G.metric(*p) for p in pts.values()]), e, B, f, c)
    out["taylor_2135_x_px"] = {k: round(float(u[0]), 1) for k, u in zip(pts, uv)}
    out["taylor_2135_photograph_x_px"] = {"left_edge": 991.5, "stone_joint": 1035, "stone_shadows_end": 1061,
                                          "right_edge": 1068, "note": "read by eye on an autocontrast crop at 8x"}
    if "--check" in sys.argv:
        ok = OUT.exists() and json.loads(OUT.read_text()) == json.loads(json.dumps(out))
        print("readings agree" if ok else "readings MOVED")
        sys.exit(0 if ok else 1)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for name, s in out["stacks"].items():
        print(f"{name:<7} sheet 6 {s['depth_mean_ft']} ft {s['depth_ft']}  record {s['record_depth_ft']} ft")
    print(out["taylor_2135_x_px"])


if __name__ == "__main__":
    main()
