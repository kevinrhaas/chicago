#!/usr/bin/env python3
"""What the two lines out of the Sauganash's drawn apex actually are.

    python3 tools/sauganash_apex_lines.py            print the reading
    python3 tools/sauganash_apex_lines.py --gate     fail if the finding flips

T-0617 measured Braunhold's plate and banked the reading in
`tools/sauganash_plate_baseline.json`. Row 10 of
`docs/RESEARCH/sauganash_image_accuracy.md` recorded that the near gable's apex sits
at (648, 350) with a line of image slope -0.318 running out of it to the left and one
of +0.095 to the right, and called the right-hand one a ridge on the strength of the
asymmetry. Row 11 then left the roof PITCH unresolved and handed it to T-0626.

T-0626's answer is that there is no rake on that apex to take a pitch from. This file
is the arithmetic, and it is arithmetic and not a detector: it opens no image, needs
no Pillow and no numpy, and runs anywhere the banked JSON does.

THE METHOD, in one paragraph. A line lying in a vertical plane has its vanishing point
on the vertical through that plane's horizontal vanishing point. The plate gives both
horizontal vanishing points and its own focal length — `perspective_test` recovered
f = 3665 px from their orthogonality about the sheet's centre, which is also the check
that the sheet is a constructed perspective at all. So project each apex line onto the
vertical through the vanishing point of the plane it lies in, read that vanishing
point's height against the horizon, and the angle between the two 3-vectors IS the
line's slope in the world.

THE RESULT: both come out horizontal. The left line reads 1.35 degrees and the right
0.11, where a 38 degree rake in the same plane would have been DRAWN at image slope
-1.99 against the -0.318 measured. Two ridges, not a ridge and a rake — which is the
second mass the owner reported missing, at the main block's own ridge height, running
away at right angles, and it is why `data/structures/sauganash_hotel.json` carries a
cross wing whose span it does not get to choose.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tools" / "sauganash_plate_baseline.json"

# The sheet Braunhold's plate was measured on. The principal point is its centre,
# which is the same assumption `perspective_test` made when it recovered the focal
# length, and the assert below is that assumption re-checked rather than restated.
PLATE_W, PLATE_H = 2017, 1296

# A world line within this many degrees of horizontal is a ridge, not a rake. No roof
# in this dataset is pitched under 10 degrees (frame_tavern_params bounds it there),
# so the two readings cannot both be roof slopes and be under this.
HORIZONTAL_DEG = 3.0


def _elevation(vp_x: float, vp_y: float, apex: tuple[float, float],
               slope: float, f: float, p: tuple[float, float]) -> tuple[float, float]:
    """Where the apex line's vanishing point lands, and its world slope in degrees."""
    y = apex[1] + slope * (vp_x - apex[0])
    d1 = (vp_x - p[0], vp_y - p[1], f)
    d2 = (vp_x - p[0], y - p[1], f)
    dot = sum(a * b for a, b in zip(d1, d2))
    n1 = math.sqrt(sum(a * a for a in d1))
    n2 = math.sqrt(sum(a * a for a in d2))
    return y, math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))


def _drawn_slope_of(pitch_deg: float, vp_x: float, vp_y: float,
                    apex: tuple[float, float], f: float,
                    p: tuple[float, float]) -> float:
    """The image slope a rake of this pitch would have been drawn at, in that plane."""
    d1 = (vp_x - p[0], vp_y - p[1], f)
    n1 = math.sqrt(sum(a * a for a in d1))
    lo, hi = 0.0, 20000.0
    for _ in range(80):
        mid = (lo + hi) / 2
        d2 = (d1[0], d1[1] + mid, f)
        n2 = math.sqrt(sum(a * a for a in d2))
        ang = math.degrees(math.acos(sum(a * b for a, b in zip(d1, d2)) / (n1 * n2)))
        lo, hi = (mid, hi) if ang < pitch_deg else (lo, mid)
    return ((vp_y + lo) - apex[1]) / (vp_x - apex[0])


def read() -> dict:
    r = json.loads(BASELINE.read_text())["reading"]
    f = r["perspective_test"]["focal_px"]
    p = (PLATE_W / 2.0, PLATE_H / 2.0)   # measure_sauganash_plate.py line 572
    v_se = (r["se_vanishing"]["x"], r["se_vanishing"]["y"])
    v_end = (r["end_vanishing"]["x"], r["end_vanishing"]["y"])

    # The principal point this file assumes is the one the banked f was recovered
    # under, or every number below is measured against a different camera.
    got = -((v_se[0] - p[0]) * (v_end[0] - p[0]) + (v_se[1] - p[1]) * (v_end[1] - p[1]))
    if abs(got - r["perspective_test"]["f_squared"]) > 1.0:
        raise SystemExit(
            f"the sheet centre ({p[0]}, {p[1]}) does not reproduce the banked focal "
            f"length: f^2 comes out {got:.1f} against {r['perspective_test']['f_squared']}. "
            f"Either the plate's dimensions in this file are wrong or the baseline was "
            f"rebanked under a different principal point.")

    apex = tuple(r["roof"]["apex"])
    left_y, left_deg = _elevation(*v_end, apex, r["roof"]["left_rake_slope"], f, p)
    right_y, right_deg = _elevation(*v_se, apex, r["roof"]["right_rake_slope"], f, p)
    return {
        "focal_px": f, "principal_point": list(p), "apex": list(apex),
        "left": {"plane": "the gable-end face", "vanishing_point_y": round(left_y, 1),
                 "below_horizon_px": round(left_y - v_end[1], 1),
                 "world_deg": round(left_deg, 2),
                 "image_slope": r["roof"]["left_rake_slope"],
                 "a_38_deg_rake_would_be_drawn_at":
                     round(_drawn_slope_of(38.0, *v_end, apex, f, p), 3)},
        "right": {"plane": "the five-bay street face", "vanishing_point_y": round(right_y, 1),
                  "below_horizon_px": round(right_y - v_se[1], 1),
                  "world_deg": round(right_deg, 2),
                  "image_slope": r["roof"]["right_rake_slope"]},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    out = read()
    if not args.quiet:
        print(json.dumps(out, indent=2))
    bad = [k for k in ("left", "right") if out[k]["world_deg"] > HORIZONTAL_DEG]
    if bad:
        print(f"BOTH LINES OUT OF THE APEX ARE NO LONGER HORIZONTAL: {bad} read "
              f"{[out[k]['world_deg'] for k in bad]} deg against a {HORIZONTAL_DEG} deg "
              f"ceiling. The Sauganash's cross wing is built on their being two ridges "
              f"meeting at one apex; if that has stopped being true the record's "
              f"cross_wing derivation is stale and must be rewritten, not re-tuned.")
        return 1
    if args.quiet:
        print(f"both apex lines horizontal: {out['left']['world_deg']} deg and "
              f"{out['right']['world_deg']} deg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
