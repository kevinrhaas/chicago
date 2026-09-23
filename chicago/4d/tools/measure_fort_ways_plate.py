#!/usr/bin/env python3
"""Measure the travelled ways the two Fort Dearborn plates draw — rows 1, 2 and 6 (T-0197).

WHY THIS TOOL EXISTS. `docs/RESEARCH/fort_dearborn_image_accuracy.md` compares the render
against `p4_0.png` and `p4_1.png` row by row, and it has seeded a run of tickets. Three of
its eight rows have been struck as wrong, each by a run that went and MEASURED the plate
instead of looking at it (T-0094 row 3, T-0095 rows 4 and 5, T-0098 the compass word in
row 8). Every struck row shared one method: a person compared a lithograph to a render by
eye and wrote down the difference. T-0197 audits what is left, and this file is the
measurement half of that audit — rows 1, 2 and 6, which had never been measured and had
between them already put TWO built ways on the reservation.

WHAT IT MEASURES, and every number below is printed by a run of this file:

  1. **ROW 2 — the track descending the bank to the water.** `p4_0`'s bank is segmented for
     bare trodden ground (warm — red over green — and paler than the sward, then a 7x7
     majority filter to kill the stipple). One connected mass carries it: it begins AT THE
     GATE at the wall's foot and descends frame-right to the drawn waterline. Its per-row
     centre, its drift, its head's distance from the gate work the plate raises, and the
     gap between its own foot and the water are all printed.

  2. **ROW 1 — "both plates show a travelled way at the fort".** The half about `p4_0` is
     row 2's track and nothing else: the plate draws no second way. The half about `p4_1`
     is measured by a detector normalised to each window's OWN quartiles, so the two plates'
     very different palettes are comparable — and it is run twice on `p4_1`, once on the
     fort's ground and once on the house-group bank at frame-left, which is the positive
     control that makes the null at the fort mean something.

  3. **ROW 6 — the flagstaff.** The tallest thin dark vertical standing in the sky over the
     fort, its truck, its flag, and — the number the row never asked for — WHERE ALONG THE
     DRAWN WALL IT STANDS. `data/exclusions.json` assigns `p4_0`'s flagstaff to Whistler's
     FIRST fort and locates that one IN THE PARADE. This one is not in the parade.

WHAT THIS TOOL MAY NOT BE USED FOR. Both plates are TIER 5 PICTORIAL — retrospective,
decades after 1835 — and this repository's rule for the whole reference directory is that
such a plate may drive massing, materials and SETTING as `inferred` and **may never drive a
coordinate**. Nothing here becomes a path point. A monocular plate cannot give the LENGTH
of a line running away from the viewer either, so the metric figures printed for the track
bound its across-view offset at the fort's own depth and are stated as bounds, never as a
measurement of the track.

    python3 tools/measure_fort_ways_plate.py                 print the measurement
    python3 tools/measure_fort_ways_plate.py --gate --quiet  the three assertions, silent when green
    python3 tools/measure_fort_ways_plate.py --self-test     prove those assertions still fire
    python3 tools/measure_fort_ways_plate.py --evidence P    also write the overlay to P
    python3 tools/measure_fort_ways_plate.py --write-baseline
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATES = ROOT / "data" / "sources" / "assets" / "prefire_views_kevin_2026_08"
P4_0 = PLATES / "p4_0.png"
P4_1 = PLATES / "p4_1.png"
PALISADE = ROOT / "data" / "sidecars" / "1835" / "fort_dearborn_palisade.json"
STREETS = ROOT / "data" / "streets" / "1835.json"
BASELINE = ROOT / "tools" / "fort_ways_plate_baseline.json"

# ---------------------------------------------------------------------------
# THE HAND-READ LANDMARKS, and they are the only hand-read numbers in the file.
#
# p4_0's four are taken verbatim from tools/measure_fort_trees_plate.py so that
# the two readings of this sheet cannot drift apart: the two ENDS of the drawn
# stockade, and the TOP and FOOT of the picket band (the two dark rules that
# bound the pale pickets, both sharp minima in the column-mean luminance).
P4_0_LANDMARKS = {
    "wall_end_frame_left_px": 314,
    "wall_end_frame_right_px": 1174,
    "picket_top_px": 377,
    "picket_foot_px": 420,
}

# p4_1's two, read at 4x against a printed profile: the drawn stockade's own ends
# (the pale palisade begins at 378 and the dark return ends at 755) and the wall's
# foot line at 288, below which the bank runs to the water.
P4_1_LANDMARKS = {
    "wall_end_frame_left_px": 378,
    "wall_end_frame_right_px": 755,
    "wall_foot_px": 288,
    "bank_bottom_px": 325,
}

# The p4_1 positive control: the bank at frame-left, among the house group, where
# the draughtsman DID draw a trodden way. Its purpose is to prove the detector
# fires on this plate's palette before a null at the fort is believed.
P4_1_CONTROL = {"x0": 100, "x1": 378, "y0": 262, "y1": 310}

# p4_0's bank body: below the picket foot, above the foreground water. The same
# BODY_BOTTOM the trees tool uses, less the strip of near-bank on the VIEWER's own
# side of the river, which is not ground this measurement is about.
P4_0_BANK = {"x0": 320, "x1": 1200, "y0": 421, "y1": 645}

# The bare-ground test on p4_0. Bare trodden earth here is WARMER than the sward
# and PALER than it; the river fails the warmth clause (R-G 0.5) and the sky fails
# it twice over (R-G -5.3). Sampled means, from a run of this file: track below the
# gate 185.6/169.8/134.7, track at the shore 166.5/154.2/123.0, bank sward
# 123.9/111.3/87.4, river 181.0/180.4/148.7, sky 221.4/226.7/202.0.
BARE_WARMTH = 6.0
BARE_MIN_LUM = 150.0
WATER_MAX_WARMTH = 3.0
WATER_MIN_LUM = 140.0
# …and paler than this is the SKY, which passes both water clauses (R-G -5.3) and,
# left in, joined the river round the edges of the sheet into one 668,564 px mass
# that put the shore 150 px above where it is drawn.
WATER_MAX_LUM = 200.0
MAJORITY_WINDOW = 7
MAJORITY_FRACTION = 0.55

# The quartile detector used on BOTH plates, so their palettes are comparable: a
# 9 px box mean to kill the stipple, then anything standing above the window's own
# third quartile by half its own interquartile range.
SMOOTH_WINDOW = 9
WAY_IQR_K = 0.5
# …and the stiffer threshold a real drawn way survives and a texture artefact does not.
WAY_IQR_K_HARD = 2.0

# The flagstaff test: a thin vertical darker than the sky by this much, standing in
# the sky band over the fort. The flag is the red-dominant patch beside its truck.
STAFF_SKY_DROP = 45.0
STAFF_BAND = {"x0": 620, "x1": 900, "y0": 140, "y1": 330}
FLAG_WARMTH = 22.0
FLAG_MAX_LUM = 210.0

# T-0095's reading of the two roofed, lanterned works this same plate raises, as
# fractions of the drawn wall run. Quoted so the staff's own fraction can be put
# beside them without re-deriving them here.
WORKS_ALONG_WALL = (0.435, 0.521)


class NoReader(Exception):
    """Pillow or numpy is not installed, so the sheet cannot be re-read."""


class PlateError(Exception):
    """The plate is on disk but the detector could not read it."""


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def banked():
    return load(BASELINE)["reading"]


# ---------------------------------------------------------------------------
# the image half


def _np():
    try:
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover - environment dependent
        raise NoReader(str(e)) from e
    return np, Image


def majority(mask, np):
    """A box majority filter, in numpy alone so this file needs no scipy."""
    k = MAJORITY_WINDOW
    pad = k // 2
    padded = np.pad(mask.astype(float), pad, mode="edge")
    csum = padded.cumsum(axis=0).cumsum(axis=1)
    csum = np.pad(csum, ((1, 0), (1, 0)))
    h, w = mask.shape
    box = (csum[k:k + h, k:k + w] - csum[0:h, k:k + w]
           - csum[k:k + h, 0:w] + csum[0:h, 0:w])
    return (box / (k * k)) >= MAJORITY_FRACTION


def box_mean(arr, k, np):
    pad = k // 2
    padded = np.pad(arr, pad, mode="edge")
    csum = padded.cumsum(axis=0).cumsum(axis=1)
    csum = np.pad(csum, ((1, 0), (1, 0)))
    h, w = arr.shape
    return (csum[k:k + h, k:k + w] - csum[0:h, k:k + w]
            - csum[k:k + h, 0:w] + csum[0:h, 0:w]) / (k * k)


def components(mask, np):
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
            "rows": arr[:, 0], "cols": arr[:, 1],
        })
    out.sort(key=lambda c: -c["px"])
    return out


def footprint_enu(sidecar):
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


def scales():
    """The two independent px-per-metre scales, printed side by side and never averaged.

    The fort's committed 53 m footprint is 8 deg off the grid, so its apparent width
    from due north is wider than 53 m; and the committed picket height spans the drawn
    picket band. They differ by about a fifth, which is the +/-20 per cent the palisade's
    own placement note already carries on every dimension derived from the Harrison plate.
    """
    pal = load(PALISADE)
    corners = footprint_enu(pal)
    apparent_m = max(e for e, _ in corners) - min(e for e, _ in corners)
    span_px = P4_0_LANDMARKS["wall_end_frame_right_px"] - P4_0_LANDMARKS["wall_end_frame_left_px"]
    picket_px = P4_0_LANDMARKS["picket_foot_px"] - P4_0_LANDMARKS["picket_top_px"]
    picket_m = pal["attributes"]["picket_height_m"]["value"]
    return {
        "apparent_footprint_m": apparent_m,
        "px_per_m_span": span_px / apparent_m,
        "picket_height_m": picket_m,
        "px_per_m_picket": picket_px / picket_m,
    }


def along_wall(col):
    lo = P4_0_LANDMARKS["wall_end_frame_left_px"]
    hi = P4_0_LANDMARKS["wall_end_frame_right_px"]
    return (col - lo) / (hi - lo)


def read_p4_0():
    """Rows 1, 2 and 6, all off p4_0."""
    np, Image = _np()
    if not P4_0.exists():
        raise PlateError(f"{P4_0.name} is not on disk")
    a = np.asarray(Image.open(P4_0).convert("RGB")).astype(float)
    lum = a.mean(axis=2)
    warmth = a[:, :, 0] - a[:, :, 1]

    body = np.zeros(lum.shape, dtype=bool)
    body[P4_0_BANK["y0"]:P4_0_BANK["y1"], P4_0_BANK["x0"]:P4_0_BANK["x1"]] = True
    bare = majority((warmth >= BARE_WARMTH) & (lum >= BARE_MIN_LUM), np) & body
    # THE RIVER, not every grey patch: the largest connected mass of the water test.
    # A shadow under the embankment passes the same two clauses over a few hundred
    # pixels, and taking any of them as "the water" put the shore 150 px too high.
    below_wall = np.zeros(lum.shape, dtype=bool)
    below_wall[P4_0_BANK["y0"]:, :] = True
    wmask = majority((warmth <= WATER_MAX_WARMTH) & (lum >= WATER_MIN_LUM)
                     & (lum <= WATER_MAX_LUM), np) & below_wall
    wcomps = components(wmask, np)
    if not wcomps:
        raise PlateError("no water segmented on this plate at all")
    water = np.zeros(lum.shape, dtype=bool)
    water[wcomps[0]["rows"], wcomps[0]["cols"]] = True

    comps = components(bare, np)
    if not comps:
        raise PlateError("no bare ground segmented below the wall at all")
    mass = comps[0]

    # the mass's centre, row by row, and the drift that says which way it runs
    rows, centres, widths = [], [], []
    for y in range(mass["y0"], mass["y1"] + 1):
        cols = mass["cols"][mass["rows"] == y]
        if cols.size < 8:
            continue
        rows.append(y)
        centres.append(float(cols.mean()))
        widths.append(int(cols.max() - cols.min() + 1))
    drift = float(np.polyfit(rows, centres, 1)[0]) if len(rows) > 2 else 0.0

    # where the mass meets the wall, and where the gate work stands
    head_cols = mass["cols"][mass["rows"] <= mass["y0"] + 4]
    head_left = int(head_cols.min())
    gate_work_col = P4_0_LANDMARKS["wall_end_frame_left_px"] + WORKS_ALONG_WALL[1] * (
        P4_0_LANDMARKS["wall_end_frame_right_px"] - P4_0_LANDMARKS["wall_end_frame_left_px"])

    # the gap between the mass's own foot and the drawn waterline, column by column
    only_mass = np.zeros(lum.shape, dtype=bool)
    only_mass[mass["rows"], mass["cols"]] = True
    gaps = []
    for x in range(760, 1200, 10):
        b = np.nonzero(only_mass[:, x])[0]
        if not b.size:
            continue
        foot = int(b[-1])
        # the first water row BELOW the bare ground's own foot in this column: the
        # river shows above the bank too, and that reach is not the shore this asks about
        w = np.nonzero(water[foot:, x])[0]
        if w.size:
            gaps.append((int(w[0]), x))
    gaps.sort()

    # the second-way test: is there any OTHER bare mass on this bank worth the name
    second = comps[1]["px"] if len(comps) > 1 else 0

    # --- row 6, the flagstaff ------------------------------------------------
    sky = float(np.percentile(lum[STAFF_BAND["y0"]:STAFF_BAND["y1"],
                                  400:1100], 80))
    dark = lum <= (sky - STAFF_SKY_DROP)
    best = (0, 0, 0)
    for x in range(STAFF_BAND["x0"], STAFF_BAND["x1"]):
        col = dark[STAFF_BAND["y0"]:STAFF_BAND["y1"], x]
        cur = 0
        for i, v in enumerate(col):
            cur = cur + 1 if v else 0
            if cur > best[0]:
                best = (cur, x, STAFF_BAND["y0"] + i - cur + 1)
    staff_run, staff_col, staff_top = best

    flag = (warmth >= FLAG_WARMTH) & (lum <= FLAG_MAX_LUM)
    fy, fx = np.nonzero(flag[STAFF_BAND["y0"]:staff_top + 140,
                             STAFF_BAND["x0"]:STAFF_BAND["x1"]])
    flag_box = None
    if fy.size:
        flag_box = {
            "px": int(fy.size),
            "y0": int(fy.min()) + STAFF_BAND["y0"], "y1": int(fy.max()) + STAFF_BAND["y0"],
            "x0": int(fx.min()) + STAFF_BAND["x0"], "x1": int(fx.max()) + STAFF_BAND["x0"],
        }

    sc = scales()
    above_px = P4_0_LANDMARKS["picket_top_px"] - staff_top
    return {
        "way": {
            "mass_px": mass["px"],
            "y0": mass["y0"], "y1": mass["y1"], "x0": mass["x0"], "x1": mass["x1"],
            "head_left_col": head_left,
            "head_offset_from_gate_work_px": round(head_left - gate_work_col, 1),
            "head_along_wall": round(along_wall(head_left), 4),
            "drift_cols_per_row": round(drift, 4),
            "centre_at_top": round(centres[0], 1) if centres else None,
            "centre_at_foot": round(centres[-1], 1) if centres else None,
            "min_gap_to_waterline_px": gaps[0][0] if gaps else None,
            "min_gap_at_col": gaps[0][1] if gaps else None,
            "second_mass_px": second,
        },
        "staff": {
            "col": staff_col,
            "top_row": staff_top,
            "dark_run_px": staff_run,
            "along_wall": round(along_wall(staff_col), 4),
            "above_picket_top_px": above_px,
            "above_picket_top_m_span": round(above_px / sc["px_per_m_span"], 2),
            "above_picket_top_m_picket": round(above_px / sc["px_per_m_picket"], 2),
            "flag": flag_box,
        },
        "scales": {k: round(v, 4) for k, v in sc.items()},
    }


def quartile_way(path, box, np, Image):
    """The way detector, normalised to the window's OWN quartiles so palettes compare."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    sm = box_mean(a.mean(axis=2), SMOOTH_WINDOW, np)
    win = sm[box["y0"]:box["y1"], box["x0"]:box["x1"]]
    q1, q3 = (float(np.percentile(win, 25)), float(np.percentile(win, 75)))
    iqr = q3 - q1
    full = np.zeros(sm.shape, dtype=bool)
    full[box["y0"]:box["y1"], box["x0"]:box["x1"]] = True
    out = {"p25": round(q1, 1), "p75": round(q3, 1), "iqr": round(iqr, 1),
           "window_px": int(win.size)}
    for name, k in (("soft", WAY_IQR_K), ("hard", WAY_IQR_K_HARD)):
        comps = components((sm >= q3 + k * iqr) & full, np)
        c = comps[0] if comps else None
        out[name] = {
            "k": k,
            "threshold": round(q3 + k * iqr, 1),
            "largest_px": c["px"] if c else 0,
            "y0": c["y0"] if c else None, "y1": c["y1"] if c else None,
            "x0": c["x0"] if c else None, "x1": c["x1"] if c else None,
        }
    return out


def read_p4_1():
    """Row 1's other half: does p4_1 draw a travelled way AT the fort?"""
    np, Image = _np()
    if not P4_1.exists():
        raise PlateError(f"{P4_1.name} is not on disk")
    fort = {"x0": P4_1_LANDMARKS["wall_end_frame_left_px"],
            "x1": P4_1_LANDMARKS["wall_end_frame_right_px"],
            "y0": P4_1_LANDMARKS["wall_foot_px"],
            "y1": P4_1_LANDMARKS["bank_bottom_px"]}
    return {
        "fort_ground": quartile_way(P4_1, fort, np, Image),
        "house_group_control": quartile_way(P4_1, P4_1_CONTROL, np, Image),
    }


def read_plates():
    r = read_p4_0()
    r["p4_1"] = read_p4_1()
    return r


# ---------------------------------------------------------------------------
# the record half — what the town has been built to, on these rows' authority


def records():
    streets = {s["id"]: s for s in load(STREETS)["streets"]}
    out = {}
    for sid in ("fort_road", "fort_bank_track"):
        s = streets.get(sid)
        if s is None:
            out[sid] = None
            continue
        path = s["path_local_enu_m"]
        out[sid] = {
            "geometry_confidence": s.get("geometry_confidence"),
            "start": path[0],
            "end": path[-1],
            "easting_change_m": round(path[-1][0] - path[0][0], 3),
            "length_m": round(sum(
                math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)), 3),
        }
    return out


def assess(reading, rec):
    """Every finding this file can make, as a dict the self-test can perturb."""
    track = rec.get("fort_bank_track")
    road = rec.get("fort_road")
    return {
        "track_present": track is not None,
        "track_easting_change_m": track["easting_change_m"] if track else 0.0,
        "track_length_m": track["length_m"] if track else 0.0,
        "track_confidence": track["geometry_confidence"] if track else None,
        "road_confidence": road["geometry_confidence"] if road else None,
        "plate_drift_cols_per_row": reading["way"]["drift_cols_per_row"],
        "plate_head_along_wall": reading["way"]["head_along_wall"],
        "plate_staff_along_wall": reading["staff"]["along_wall"],
    }


def findings(a):
    """The three assertions. The first two ask the TOWN about the plate, so they gate."""
    bad = []
    if not a["track_present"]:
        bad.append("fort_bank_track is gone from data/streets/1835.json — the record row 2 "
                   "was measured against")
    elif a["track_easting_change_m"] >= 0.0:
        bad.append(f"fort_bank_track runs EAST out of the north gate "
                   f"({a['track_easting_change_m']:+.2f} m of easting). p4_0 draws its bare "
                   f"corridor descending frame-RIGHT, which this plate's own settled stand "
                   f"makes WEST — see docs/RESEARCH/fort_dearborn_image_accuracy.md § row 8.")
    for who, key in (("fort_bank_track", "track_confidence"), ("fort_road", "road_confidence")):
        if a[key] not in (None, "reconstructed"):
            bad.append(f"{who}.geometry_confidence is '{a[key]}'. Rows 1 and 2 of the "
                       f"image-accuracy table are readings of TIER 5 retrospective plates, "
                       f"and this measurement confirming what they draw is not a warrant to "
                       f"promote a line nobody traced. A plate may never drive a coordinate.")
    return bad


def drift(fresh, base):
    """The plate is committed and cannot change, so a moved reading is a moved detector."""
    out = []
    checks = (
        ("way.mass_px", 0.02), ("way.head_left_col", 0.02), ("way.drift_cols_per_row", 0.10),
        ("staff.col", 0.01), ("staff.top_row", 0.02), ("staff.along_wall", 0.02),
        ("p4_1.fort_ground.hard.largest_px", 0.25),
        ("p4_1.house_group_control.hard.largest_px", 0.25),
    )
    for path, tol in checks:
        a, b = fresh, base
        for part in path.split("."):
            a = a.get(part) if isinstance(a, dict) else None
            b = b.get(part) if isinstance(b, dict) else None
        if a is None or b is None:
            continue
        if abs(b) < 1e-9:
            if abs(a) > 1e-9:
                out.append(f"the reading of {path} moved from {b} to {a} on a committed plate")
            continue
        if abs(a - b) / abs(b) > tol:
            out.append(f"the reading of {path} moved from {b} to {a} on a committed plate — "
                       f"the sheet cannot change, so the detector did")
    return out


def self_test(a, re_read):
    """Prove each assertion still fires when the thing it guards is broken."""
    cases = [
        ("the track swung back east", {**a, "track_easting_change_m": +12.0}),
        ("the track's confidence promoted on the plate", {**a, "track_confidence": "inferred"}),
        ("the road's confidence promoted on the plate", {**a, "road_confidence": "documented"}),
        ("the track deleted", {**a, "track_present": False}),
    ]
    ok = True
    for label, broken in cases:
        if not findings(broken):
            print(f"   FAIL the assertion for '{label}' did not fire")
            ok = False
    if findings(a):
        print("   FAIL the tree as committed is already red")
        ok = False
    if ok:
        print(f"   all {len(cases)} assertions fire when broken, and none fires on the "
              f"committed tree" + ("" if re_read else " (plate not re-read)"))
    return 0 if ok else 1


def show(reading, rec):
    w = reading["way"]
    s = reading["staff"]
    sc = reading["scales"]
    print("   ROW 2 — the track descending the bank, measured on p4_0")
    print(f"     one bare mass carries it: {w['mass_px']:,} px, rows {w['y0']}-{w['y1']}, "
          f"cols {w['x0']}-{w['x1']}")
    print(f"     it meets the wall's foot at column {w['head_left_col']}, "
          f"{w['head_offset_from_gate_work_px']:+.1f} px from the gate work p4_0 raises at "
          f"{WORKS_ALONG_WALL[1]:.3f} of the wall — {w['head_along_wall']:.3f} of that run")
    print(f"     its centre runs {w['centre_at_top']} -> {w['centre_at_foot']}, drifting "
          f"{w['drift_cols_per_row']:+.3f} columns a row: frame-RIGHT, which is WEST")
    print(f"     at its closest its foot comes within {w['min_gap_to_waterline_px']} px of "
          f"the drawn waterline, at column {w['min_gap_at_col']} — "
          f"{w['min_gap_to_waterline_px'] / sc['px_per_m_span']:.1f}-"
          f"{w['min_gap_to_waterline_px'] / sc['px_per_m_picket']:.1f} m read at the FORT's "
          f"depth, and the foot is nearer the viewer than the fort, so both are upper "
          f"bounds. What is between is the plate's own dark shore rule: the corridor "
          f"descends the bank to the shore.")
    print(f"     the next bare mass on this bank is {w['second_mass_px']:,} px: there is no "
          f"second way")
    print("   ROW 1 — 'both plates show a travelled way at the fort'")
    f = reading["p4_1"]["fort_ground"]
    c = reading["p4_1"]["house_group_control"]
    print(f"     p4_0: the way it draws IS row 2's track. Nothing else on this bank.")
    print(f"     p4_1 at the fort   (p75 {f['p75']}, IQR {f['iqr']}): largest pale mass "
          f"{f['soft']['largest_px']} px at +0.5 IQR, {f['hard']['largest_px']} px at +2.0 IQR")
    print(f"     p4_1 control       (p75 {c['p75']}, IQR {c['iqr']}): largest pale mass "
          f"{c['soft']['largest_px']} px at +0.5 IQR, {c['hard']['largest_px']} px at +2.0 IQR"
          f" — rows {c['hard']['y0']}-{c['hard']['y1']}, cols {c['hard']['x0']}-{c['hard']['x1']}")
    print(f"     the same detector, same settings, same plate: it finds the house-group way "
          f"and finds nothing at the fort")
    print("   ROW 6 — the flagstaff, and where it stands")
    print(f"     the tallest thin dark vertical in the sky over the fort: column {s['col']}, "
          f"truck at row {s['top_row']}, {s['dark_run_px']} px of staff before the roof takes it")
    if s["flag"]:
        fl = s["flag"]
        print(f"     the flag: {fl['px']} red-dominant px, rows {fl['y0']}-{fl['y1']}, "
              f"cols {fl['x0']}-{fl['x1']} — flying frame-LEFT of the truck")
    print(f"     it stands at {s['along_wall']:.3f} of the drawn wall run, BETWEEN the two "
          f"roofed lanterned works at {WORKS_ALONG_WALL[0]} and {WORKS_ALONG_WALL[1]} — over "
          f"the gate, and not in the parade")
    print(f"     it rises {s['above_picket_top_px']} px over the picket head: "
          f"{s['above_picket_top_m_span']} m on the footprint scale, "
          f"{s['above_picket_top_m_picket']} m on the picket scale (never averaged)")
    print(f"   the two scales: {sc['px_per_m_span']} px/m on the fort's "
          f"{sc['apparent_footprint_m']} m apparent footprint, {sc['px_per_m_picket']} px/m on "
          f"its {sc['picket_height_m']} m picket")
    t = rec.get("fort_bank_track")
    if t:
        print(f"   the town, for comparison: fort_bank_track runs "
              f"{-t['easting_change_m']:.2f} m WEST over {t['length_m']:.2f} m, "
              f"'{t['geometry_confidence']}'. The plate agrees on the DIRECTION and cannot "
              f"fix the length — a line running away from a monocular viewer has none.")


def evidence(path):
    np, Image = _np()
    from PIL import ImageDraw  # noqa: PLC0415
    img = Image.open(P4_0).convert("RGB")
    a = np.asarray(img).astype(float)
    lum = a.mean(axis=2)
    warmth = a[:, :, 0] - a[:, :, 1]
    body = np.zeros(lum.shape, dtype=bool)
    body[P4_0_BANK["y0"]:P4_0_BANK["y1"], P4_0_BANK["x0"]:P4_0_BANK["x1"]] = True
    bare = majority((warmth >= BARE_WARMTH) & (lum >= BARE_MIN_LUM), np) & body
    comps = components(bare, np)
    mass = np.zeros(lum.shape, dtype=bool)
    mass[comps[0]["rows"], comps[0]["cols"]] = True
    tint = np.asarray(img).astype(float)
    tint[mass] = tint[mass] * 0.45 + np.array([255.0, 90.0, 40.0]) * 0.55
    out = Image.fromarray(tint.astype("uint8"))
    d = ImageDraw.Draw(out)
    lo, hi = P4_0_LANDMARKS["wall_end_frame_left_px"], P4_0_LANDMARKS["wall_end_frame_right_px"]
    for x in (lo, hi):
        d.line([(x, 340), (x, 470)], fill=(0, 90, 255), width=3)
    for y in (P4_0_LANDMARKS["picket_top_px"], P4_0_LANDMARKS["picket_foot_px"]):
        d.line([(lo, y), (hi, y)], fill=(0, 90, 255), width=2)
    r = read_p4_0()
    sx = r["staff"]["col"]
    d.line([(sx, r["staff"]["top_row"]), (sx, r["staff"]["top_row"] + r["staff"]["dark_run_px"])],
           fill=(0, 200, 90), width=3)
    for frac in WORKS_ALONG_WALL:
        x = int(lo + frac * (hi - lo))
        d.line([(x, 300), (x, 340)], fill=(255, 0, 200), width=3)
    out.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero on a finding (the record assertions)")
    ap.add_argument("--quiet", action="store_true", help="print only findings")
    ap.add_argument("--json", action="store_true", help="print the reading as JSON")
    ap.add_argument("--self-test", action="store_true", help="prove the assertions fire")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--evidence", metavar="PATH", help="write the segmentation overlay")
    args = ap.parse_args()

    rec = records()
    reading = None
    try:
        reading = read_plates()
    except NoReader:
        pass
    except PlateError as e:
        print(f"   FAIL {e}")
        return 1

    if reading is None:
        # No image library. The RECORD assertions still run, against the banked
        # reading — said out loud every time, so a green line here is never mistaken
        # for the sheet having been re-read.
        base = banked()
        a = assess(base, rec)
        if args.self_test:
            return self_test(a, re_read=False)
        bad = findings(a)
        if not args.quiet or bad:
            print("   Pillow is not installed, so the LITHOGRAPHS WERE NOT RE-READ. Standing "
                  f"on the banked reading in {BASELINE.name}: the bare mass meeting the wall "
                  f"at {base['way']['head_along_wall']:.3f} of the run, the flagstaff at "
                  f"{base['staff']['along_wall']:.3f}. Only the assertions about the RECORD "
                  "are live here.")
        for g in bad:
            print(f"   FAIL {g}")
        return 1 if (bad and args.gate) else 0

    if args.evidence:
        print(f"   wrote {evidence(args.evidence)}")

    fresh = json.loads(json.dumps(reading))
    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "$note": "T-0197. The banked reading of the two Fort Dearborn plates by "
                     "tools/measure_fort_ways_plate.py. The plates are committed and cannot "
                     "change, so this exists for two reasons: CI installs no image library "
                     "and would otherwise skip the plate half in silence, and a detector edit "
                     "that quietly moves the reading is a thing this project has been bitten "
                     "by. Regenerate with --write-baseline, and only ever with the reason in "
                     "the commit.",
            "reading": fresh,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        show(reading, rec)
        print(f"\n   wrote {BASELINE.name}")
        return 0

    a = assess(reading, rec)
    if args.self_test:
        return self_test(a, re_read=True)
    if args.json:
        print(json.dumps(fresh, indent=2, sort_keys=True))
        return 0

    bad = findings(a) + (drift(fresh, banked()) if BASELINE.exists() else [])
    if not args.quiet or bad:
        show(reading, rec)
    for g in bad:
        print(f"   FAIL {g}")
    if not bad and not args.quiet:
        print("   rows 1, 2 and 6 are measured, and nothing has been built past what they say")
    return 1 if (bad and args.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
