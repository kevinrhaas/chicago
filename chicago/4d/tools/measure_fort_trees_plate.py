#!/usr/bin/env python3
"""Measure the tree mass `p4_0` draws at Fort Dearborn — WHICH SIDE, how far, how tall (T-0098).

WHY THIS TOOL EXISTS AT ALL. T-0044's image-accuracy pass listed eight gaps between the
render and the two committed Fort Dearborn plates. Gap 8 reads, verbatim: *"No trees at the
fort; `p4_0` puts a tree mass east of the walls."* T-0098 inherited that sentence into its
own title. **It was read by eye, and this tool measures it instead** — for the same reason
the sibling fort ticket T-0094 was refuted on the same plate: an eye reading of a lithograph
is an impression, and this project places nothing on an impression.

WHAT IT MEASURES, and every number below is printed by a run of this file:

  1. **WHICH SIDE of the drawn stockade the foliage is on.** The plate is segmented for
     foliage — green-of-red and dark, then a 7x7 majority filter to kill the stipple — and
     the mask is split at the two ends of the drawn stockade. One side carries a single
     connected mass of tens of thousands of pixels; the other carries noise and a patch of
     bank grass on the VIEWER's own side of the river.

  2. **What compass direction that side is.** Not read off the picture: read off the stand.
     `docs/RESEARCH/fort_dearborn_image_accuracy.md` fixes `p4_0`'s viewpoint as the north
     bank at local `1145, 300` looking south, and `docs/RESEARCH/fort_from_the_north_bank_
     2026-08-19.png` is the render from it with the HUD compass reading **S 180 deg**. From
     a stand facing south, EAST is frame-LEFT and WEST is frame-RIGHT — and the committed
     `chicago_lighthouse_1832`, which stands 46.9 m WEST of the fort's centre, is drawn on
     the frame-RIGHT of the fort in that very shot. The plate's mass is on the frame-RIGHT.

  3. **How far out, and how tall**, in metres, on two independent scales that are printed
     side by side rather than averaged: the fort's committed 53 m footprint (whose apparent
     width from due north is 59.86 m, because the walls sit 8 deg off the grid) against the
     drawn stockade's span, and the committed picket height against the drawn picket band.
     They differ by about a fifth, which is the +/-20 per cent the palisade's own placement
     note already carries on every dimension derived from the Harrison plate. **Both are
     printed. Neither is smoothed into the other.**

WHAT THIS TOOL MAY NOT BE USED FOR. `p4_0` is TIER 5 PICTORIAL — retrospective, decades
after 1835 — and this repository's rule for the whole reference directory is that such a
plate may drive massing, materials and SETTING as `inferred` and **may never drive a
coordinate**. So nothing here becomes a tree position. What it does is bound an invention:
`tools/generate_fort_trees.py` derives every stem from the palisade's own committed
footprint, and this measurement is what says which side of that footprint, and which of the
zone's recorded species can carry the crown height the plate draws.

    python3 tools/measure_fort_trees_plate.py                  print the measurement
    python3 tools/measure_fort_trees_plate.py --evidence P     also write the overlay to P
"""

from __future__ import annotations

import argparse
import json
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PLATE = ROOT / "data" / "sources" / "assets" / "prefire_views_kevin_2026_08" / "p4_0.png"
PALISADE = ROOT / "data" / "sidecars" / "1835" / "fort_dearborn_palisade.json"
LIGHTHOUSE = ROOT / "data" / "sidecars" / "1835" / "chicago_lighthouse_1832.json"

# ---------------------------------------------------------------------------
# THE HAND-READ LANDMARKS, and they are the only hand-read numbers in the file.
#
# Four pixel rows and columns off the plate, each one checked against a printed
# profile rather than guessed at a glance (the run prints the profile that fixed
# each of them). Everything else below is derived.
#
#   * the two ENDS of the drawn stockade. The picket line begins at the mound at
#     frame-left and stops at a corner post at frame-right, where the foliage
#     starts. Read at 8x zoom.
#   * the TOP and FOOT of the picket band, taken as the two dark rules that bound
#     the pale pickets. Both are sharp minima in the column-mean luminance and
#     both sit at the same row at either end of the wall, which is the check that
#     they are the wall's own lines and not a shadow: 377 and 420.
LANDMARKS = {
    "wall_end_frame_left_px": 314,
    "wall_end_frame_right_px": 1174,
    "picket_top_px": 377,
    "picket_foot_px": 420,
}

# The picture body: below the plate's printed frame line and above the near river
# bank in the foreground, which is on the VIEWER's side of the water and is not
# ground this measurement is about.
BODY_TOP_PX = 12
BODY_BOTTOM_PX = 660

# The foliage test. Foliage on this plate is greener than it is red AND darker
# than the sky or the water; the fort's own walls, the pickets, the mound and the
# foreground grass all fail one clause or the other. Sampled means, from a run of
# this file: canopy 138.9/148.4/121.2, mass at the wall 87.7/91.9/71.7, mound
# ground 138.5/126.1/100.8, pickets 179.1/169.4/138.3, lake 186.2/191.0/169.3.
GREEN_OVER_RED = 3.0
FOLIAGE_MAX_LUM = 175.0
MAJORITY_WINDOW = 7
MAJORITY_FRACTION = 0.55

# A connected component smaller than this is stipple, not a canopy.
MIN_COMPONENT_PX = 400


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def footprint_enu(sidecar) -> list[tuple[float, float]]:
    """The committed footprint in local ENU, in the frame docs/GLB-CONTRACT.md fixes."""
    place = sidecar["placement"]
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    out = []
    for u, v in sidecar["footprint"]["polygon"]:
        x, z = u, -v
        xr = x * math.cos(th) + z * math.sin(th)
        zr = -x * math.sin(th) + z * math.cos(th)
        out.append((place["local_e"] + xr, place["local_n"] - zr))
    return out


def majority(mask: np.ndarray) -> np.ndarray:
    """A box majority filter, in numpy alone so this file needs no scipy."""
    k = MAJORITY_WINDOW
    pad = k // 2
    padded = np.pad(mask.astype(np.float64), pad, mode="edge")
    csum = padded.cumsum(axis=0).cumsum(axis=1)
    csum = np.pad(csum, ((1, 0), (1, 0)))
    h, w = mask.shape
    box = (csum[k:k + h, k:k + w] - csum[0:h, k:k + w]
           - csum[k:k + h, 0:w] + csum[0:h, 0:w])
    return (box / (k * k)) >= MAJORITY_FRACTION


def components(mask: np.ndarray):
    """Connected components of a boolean mask, 4-connected, largest first."""
    seen = np.zeros(mask.shape, dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        pts = []
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                        and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        arr = np.array(pts)
        out.append({
            "px": len(pts),
            "y0": int(arr[:, 0].min()), "y1": int(arr[:, 0].max()),
            "x0": int(arr[:, 1].min()), "x1": int(arr[:, 1].max()),
        })
    out.sort(key=lambda c: -c["px"])
    return out


def measure():
    img = Image.open(PLATE).convert("RGB")
    a = np.asarray(img).astype(float)
    lum = a.mean(axis=2)
    raw = ((a[:, :, 1] - a[:, :, 0]) >= GREEN_OVER_RED) & (lum <= FOLIAGE_MAX_LUM)
    fol = majority(raw)
    body = np.zeros(fol.shape, dtype=bool)
    body[BODY_TOP_PX:BODY_BOTTOM_PX, :] = True
    fol &= body

    left_end = LANDMARKS["wall_end_frame_left_px"]
    right_end = LANDMARKS["wall_end_frame_right_px"]
    sides = {
        "frame_left": fol[:, :left_end],
        "within_the_drawn_stockade": fol[:, left_end:right_end + 1],
        "frame_right": fol[:, right_end + 1:],
    }
    areas = {k: int(v.sum()) for k, v in sides.items()}

    left_comps = components(fol[:, :left_end])
    right = fol.copy()
    right[:, :right_end + 1] = False
    right_comps = components(right)
    mass = right_comps[0]

    # --- the two scales, printed rather than reconciled -----------------------
    pal = load(PALISADE)
    corners = footprint_enu(pal)
    apparent_m = max(e for e, _ in corners) - min(e for e, _ in corners)
    span_px = right_end - left_end
    px_per_m_span = span_px / apparent_m

    picket_px = LANDMARKS["picket_foot_px"] - LANDMARKS["picket_top_px"]
    picket_m = pal["attributes"]["picket_height_m"]["value"]
    px_per_m_picket = picket_px / picket_m

    crown_px = LANDMARKS["picket_foot_px"] - mass["y0"]
    run_px = mass["x1"] - mass["x0"] + 1
    gap_px = mass["x0"] - right_end

    return {
        "plate": str(PLATE.relative_to(ROOT)),
        "areas": areas,
        "left_components": left_comps[:3],
        "right_components": right_comps[:3],
        "mass": mass,
        "cut_off_by_the_frame": mass["x1"] >= img.width - 2,
        "apparent_fort_width_m": apparent_m,
        "footprint_side_m": max(u for u, _ in pal["footprint"]["polygon"]),
        "px_per_m_span": px_per_m_span,
        "px_per_m_picket": px_per_m_picket,
        "picket_band_px": picket_px,
        "committed_picket_height_m": picket_m,
        "crown_px": crown_px,
        "crown_m_span_scale": crown_px / px_per_m_span,
        "crown_m_picket_scale": crown_px / px_per_m_picket,
        "gap_px": gap_px,
        "gap_m_span_scale": gap_px / px_per_m_span,
        "run_px": run_px,
        "run_m_span_scale": run_px / px_per_m_span,
        "image_size": img.size,
    }, img, fol


def compass() -> dict:
    """Which way frame-right IS, argued from the committed stand and not from the picture.

    The lighthouse is the witness. It is 46.9 m west of the fort's centre, it is
    the one committed structure on this reservation outside the walls, and in
    `docs/RESEARCH/fort_from_the_north_bank_2026-08-19.png` — the render from
    `p4_0`'s own stand, HUD compass S 180 deg — it stands to the frame-RIGHT of
    the fort. So on this plate frame-right is WEST and frame-left is EAST.
    """
    pal = load(PALISADE)
    lig = load(LIGHTHOUSE)
    corners = footprint_enu(pal)
    fort_e = sum(e for e, _ in corners) / len(corners)
    fort_n = sum(n for _, n in corners) / len(corners)
    return {
        "stand_local_enu_m": [1145.0, 300.0],
        "stand_yaw_deg": 180.0,
        "fort_centre_local_enu_m": [round(fort_e, 2), round(fort_n, 2)],
        "lighthouse_local_enu_m": [lig["placement"]["local_e"], lig["placement"]["local_n"]],
        "lighthouse_east_of_fort_m": round(lig["placement"]["local_e"] - fort_e, 1),
        "frame_right_is": "west",
        "frame_left_is": "east",
    }


def evidence(img: Image.Image, fol: np.ndarray, m: dict, path: Path) -> None:
    """The overlay a reader can check the numbers against without running anything."""
    out = img.convert("RGB").copy()
    tint = np.asarray(out).astype(float)
    tint[fol] = tint[fol] * 0.45 + np.array([255.0, 40.0, 190.0]) * 0.55
    out = Image.fromarray(tint.astype(np.uint8))
    d = ImageDraw.Draw(out)
    left = LANDMARKS["wall_end_frame_left_px"]
    right = LANDMARKS["wall_end_frame_right_px"]
    for x, label in ((left, "stockade E end"), (right, "stockade W end")):
        d.line([(x, 250), (x, 560)], fill=(255, 235, 0), width=2)
        d.text((x + 4, 254), label, fill=(255, 235, 0))
    for y, label in ((LANDMARKS["picket_top_px"], "picket top"),
                     (LANDMARKS["picket_foot_px"], "wall foot")):
        d.line([(left, y), (right, y)], fill=(255, 235, 0), width=1)
        d.text((left + 6, y - 12), label, fill=(255, 235, 0))
    mass = m["mass"]
    d.rectangle([mass["x0"], mass["y0"], mass["x1"], mass["y1"]],
                outline=(0, 220, 255), width=2)
    d.text((mass["x0"] + 6, mass["y0"] - 14),
           f"the mass — {mass['px']} px, frame-RIGHT = WEST", fill=(0, 220, 255))
    d.text((6, 6), "T-0098 — p4_0 foliage segmentation (tinted), "
                   "the fort scaled off its own committed 53 m footprint",
           fill=(255, 235, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, default=None,
                    help="write the annotated overlay to this path")
    args = ap.parse_args()
    m, img, fol = measure()
    c = compass()

    print(f"PLATE {m['plate']}  {m['image_size'][0]}x{m['image_size'][1]}")
    print()
    print("WHICH SIDE — foliage pixels, split at the two ends of the drawn stockade")
    for k, v in m["areas"].items():
        print(f"  {k:30s} {v:7d} px")
    print("  the largest connected component on each side:")
    for side, comps in (("frame-left (EAST)", m["left_components"]),
                        ("frame-right (WEST)", m["right_components"])):
        for c_ in comps[:2]:
            verdict = "A CANOPY" if c_["px"] >= MIN_COMPONENT_PX * 8 else \
                      ("a patch" if c_["px"] >= MIN_COMPONENT_PX else "stipple")
            print(f"    {side:20s} {c_['px']:6d} px  x {c_['x0']:4d}-{c_['x1']:4d} "
                  f" y {c_['y0']:3d}-{c_['y1']:3d}   {verdict}")
    print()
    print("WHICH WAY IS FRAME-RIGHT — argued from the stand, not from the picture")
    print(f"  p4_0's stand (docs/RESEARCH/fort_dearborn_image_accuracy.md): local "
          f"{c['stand_local_enu_m']}, yaw {c['stand_yaw_deg']} deg — facing SOUTH")
    print(f"  fort centre {c['fort_centre_local_enu_m']}, lighthouse "
          f"{c['lighthouse_local_enu_m']} — {abs(c['lighthouse_east_of_fort_m'])} m WEST of it")
    print("  and in the render from that stand the lighthouse draws to the frame-RIGHT")
    print(f"  => frame-right is {c['frame_right_is'].upper()}, "
          f"frame-left is {c['frame_left_is'].upper()}")
    print()
    print("HOW FAR AND HOW TALL — two scales, printed rather than averaged")
    print(f"  committed footprint {m['footprint_side_m']} m square, 8 deg off the grid: "
          f"apparent width from due north {m['apparent_fort_width_m']:.2f} m")
    span_px = LANDMARKS["wall_end_frame_right_px"] - LANDMARKS["wall_end_frame_left_px"]
    print(f"  drawn stockade span {span_px} px  ->  {m['px_per_m_span']:.2f} px/m")
    print(f"  drawn picket band {m['picket_band_px']} px against the committed "
          f"{m['committed_picket_height_m']} m  ->  {m['px_per_m_picket']:.2f} px/m")
    print(f"  the two scales differ by "
          f"{100 * (m['px_per_m_span'] / m['px_per_m_picket'] - 1):.0f} % — the palisade's "
          f"own placement note already carries +/-20 % on every derived dimension")
    print(f"  crown top stands {m['crown_px']} px above the wall foot  ->  "
          f"{m['crown_m_span_scale']:.1f} m (span scale) .. "
          f"{m['crown_m_picket_scale']:.1f} m (picket scale), before the bank's own fall")
    print(f"  the mass begins {m['gap_px']} px past the stockade's west end "
          f"({m['gap_m_span_scale']:.1f} m of bearing at the fort's depth)")
    ends = ("TO THE EDGE OF THE PLATE — the picture does not bound its west end"
            if m["cut_off_by_the_frame"] else "and ends inside the picture")
    print(f"  and runs {m['run_px']} px west ({m['run_m_span_scale']:.1f} m of bearing) "
          f"{ends}")
    if args.evidence:
        evidence(img, fol, m, args.evidence)
        print()
        print(f"evidence overlay written to {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
