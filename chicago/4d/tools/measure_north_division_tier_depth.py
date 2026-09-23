#!/usr/bin/env python3
"""How deep is the North Division's block tier? Read off the Thompson plat (T-1457).

T-0451 read this sheet ACROSS: the six north-south corridors between Kinzie Street and
North Water Street, and the seven blocks they divide. It never read the sheet DOWN, and
so the tier had a width and no depth. T-1436 went to cut the lots into those blocks and
could not, because nothing committed says where the tier's SOUTH face stands:

* Kinzie bounds it north, committed and `attested`.
* North Water bounds it south, and North Water is `reconstructed` — `tools/derive_north_
  water.py` cuts it from the river bank, and `street_control.json` §
  `north_bank.not_in_the_corridor_layer` refuses it a corridor in as many words, because
  "offsetting that polyline by half a module would invent a rectangle no sheet draws".
* Cutting the south face off that bank anyway gives block depths that swing from 92 m to
  139 m across seven blocks. T-1436 read that swing as an error and said so.

IT IS NOT AN ERROR. The plat draws the tier as a WEDGE, and this reading is how we know.

WHAT THE SHEET DRAWS. Every block carries FOUR horizontal lines, not two: the tier's
north face, the south edge of the upper lot row, the north edge of the lower lot row,
and the tier's south face. The two middle lines are an alley. Read in metres:

* The LOWER row is constant. 184.6, 181.5, 179.0, 178.8 and 177.0 ft across blocks 5 to
  1 — and the sheet LETTERS that row 180, once in every block, down the west edge of
  lot 4. The reading reproduces the plat's own figure to 0.2 ft in the mean.
* The UPPER row absorbs the whole wedge: 178.6, 191.9, 206.9, 221.2, 232.7 ft, growing
  monotonically eastward.
* The alley between them is 20.4-21.8 ft.

That is exactly what a surveyor does when a straight section line runs above a river
bank that falls away from it: hold the river frontage at one depth, and let the back row
take up the difference. The swing T-1436 could not believe is the plat's own.

AND THE SHEET'S OWN CHAINED FIGURES CLOSE ON IT. Block 1's east line, against the Due
North line, is lettered 260 over 180. The 260 is not the upper row alone (that measures
237 ft there): it is the upper row PLUS the alley, 258.9 ft as drawn. 260 + 180 = 440 ft
from the section line to the tier's south face; the sheet draws 435.6.

THE FIT, and the half of it that fails. Pixels become metres through a px-to-northing
fit anchored on three South Division corridors — Lake, Randolph and Washington — whose
two edges are measured on this same sheet and whose centrelines are committed. It lands
on 0.5344 m/px. T-0451's INDEPENDENT px-to-easting fit, from four north-south corridors,
landed on 0.5345. Two fits, two axes, four and three controls, agreeing to 0.012 %.

But the tier stands 400-700 px above the control band, and a one-dimensional fit does
not survive that extrapolation intact. Held out of the fit, committed Kinzie is missed
by +16.8 m at Franklin and +0.4 m at Wolcott — an error that runs with EASTING, which is
a shear, not a scale error. So this reading states DEPTHS, which are differences taken
at one easting and which the lettered 180 confirms, and it does NOT restate the tier's
absolute northings. The south face is published as a depth below the committed north
face, and T-1458 cuts the blocks on that.

WHAT THE SHEET WILL NOT GIVE. Block 6's two middle lines are not returned by the scan:
it is the block the plat draws its watercourse across and the freehand banks cross the
lot lines (T-0452). Block 7 gives all four, but its south face sits 1.7 m off the line
the other five share and leans steeper — block 7 fronts the North Branch, not the main
stem, and is excluded from the straight-line fit and reported apart.

    tools/measure_north_division_tier_depth.py              -> print the derivation
    tools/measure_north_division_tier_depth.py --self-test  -> the assertions
    tools/measure_north_division_tier_depth.py --gate       -> the assertions, quietly
    tools/measure_north_division_tier_depth.py --reread     -> re-measure the sheet
                                                               (needs Pillow and numpy)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
FT = 0.3048
CORRIDOR_M = 80 * FT

# T-0451's committed px-to-easting fit, re-derived there from four South Division
# corridors. This reading does not refit it; it is quoted so the two axes can be
# compared, and measure_north_division_streets.py is where it is proved.
A_E, B_E = 0.534506, -597.5716

# The blocks whose four lines the scan returns cleanly and which share one south face.
TIER_BLOCKS = ["5", "4", "3", "2", "1"]
# Read, but held out of the straight-line fit: it fronts the North Branch.
BRANCH_BLOCK = "7"
# The corridors the northing fit is anchored on. Both edges of each are measured.
FIT_CONTROL = ["lake", "randolph", "washington"]
# Held OUT of the fit, and the reason this reading publishes depths and not northings.
HOLDOUT = "kinzie"
# The sheet's own lettered figures, read at 4x (see the trace's `lettering` section).
LETTERED_LOWER_ROW_FT = 180.0
LETTERED_BLOCK_1_CHAIN_FT = 260.0


def load():
    reading = json.loads((ROOT / "data" / "traces"
                          / "thompson_north_division_streets.json").read_text())
    streets = json.loads((ROOT / "data" / "streets" / "1835.json").read_text())
    return reading, streets


def n_at(path, e):
    """The northing of a two-point-or-more centreline where it crosses easting `e`."""
    for (e0, n0), (e1, n1) in zip(path, path[1:]):
        if min(e0, e1) <= e <= max(e0, e1):
            t = 0.0 if e1 == e0 else (e - e0) / (e1 - e0)
            return n0 + t * (n1 - n0)
    return None


def fit_line(pts):
    n = len(pts)
    sx = sum(p for p, _ in pts)
    sy = sum(v for _, v in pts)
    sxx = sum(p * p for p, _ in pts)
    sxy = sum(p * v for p, v in pts)
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return a, (sy - a * sx) / n


def derive():
    reading, streets = load()
    tier = reading["north_tier_horizontals_px"]
    ctrl_px = reading["south_division_control_px"]
    by = {s["id"]: s for s in streets["streets"]}

    x_ref = tier["x_ref_px"]
    e_ref = A_E * x_ref + B_E

    # --- the px-to-northing fit, from the three South Division corridors ------------
    controls = []
    for sid in FIT_CONTROL:
        edges = ctrl_px[sid]
        ys = []
        for edge in ("north", "south"):
            a, b = fit_line([(p[0], p[1]) for p in edges[edge]])
            ys.append(a * x_ref + b)
        centre_px = (ys[0] + ys[1]) / 2.0
        controls.append({"id": sid, "centre_px": centre_px,
                         "drawn_width_px": ys[1] - ys[0],
                         "committed_n": n_at(by[sid]["path_local_enu_m"], e_ref)})
    a_n, b_n = fit_line([(c["centre_px"], c["committed_n"]) for c in controls])
    for c in controls:
        c["resid_m"] = a_n * c["centre_px"] + b_n - c["committed_n"]
        c["drawn_width_m"] = c["drawn_width_px"] * -a_n

    def N(py):
        return a_n * py + b_n

    # --- the tier, block by block ----------------------------------------------------
    blocks = []
    for bid in TIER_BLOCKS + [BRANCH_BLOCK]:
        row = tier["blocks"][bid]
        x = row["x_mid_px"]
        n_face, up_s, low_n, s_face = (N(row[k]) for k in
                                       ("north_face", "upper_row_south",
                                        "lower_row_north", "south_face"))
        blocks.append({
            "id": bid, "x_mid_px": x, "e": A_E * x + B_E,
            "north_face_n": n_face, "south_face_n": s_face,
            "upper_row_m": n_face - up_s, "alley_m": up_s - low_n,
            "lower_row_m": low_n - s_face, "depth_m": n_face - s_face,
            "upper_row_ft": (n_face - up_s) / FT, "alley_ft": (up_s - low_n) / FT,
            "lower_row_ft": (low_n - s_face) / FT, "depth_ft": (n_face - s_face) / FT,
            "in_fit": bid in TIER_BLOCKS,
        })

    # --- the south face as one straight line, over the five blocks that share it -----
    fitted = [b for b in blocks if b["in_fit"]]
    a_s, b_s = fit_line([(b["x_mid_px"], tier["blocks"][b["id"]]["south_face"])
                         for b in fitted])
    south_resid_px = {b["id"]: tier["blocks"][b["id"]]["south_face"]
                      - (a_s * b["x_mid_px"] + b_s) for b in fitted}
    branch = [b for b in blocks if not b["in_fit"]][0]
    branch_resid_px = (tier["blocks"][branch["id"]]["south_face"]
                       - (a_s * branch["x_mid_px"] + b_s))

    # --- the holdout: committed Kinzie was not in the fit ----------------------------
    holdout = []
    for b in fitted:
        centre = n_at(by[HOLDOUT]["path_local_enu_m"], b["e"])
        holdout.append({"id": b["id"], "e": b["e"], "read_n": b["north_face_n"],
                        "committed_kerb_n": centre - CORRIDOR_M / 2.0,
                        "resid_m": b["north_face_n"] - (centre - CORRIDOR_M / 2.0)})

    # --- the sheet's own chained figures at block 1's east line ----------------------
    b1 = tier["blocks"]["1"]
    x_e = tier["block_1_east_px"]
    def at_east(key):
        return b1[key] + b1["lean_" + key] * (x_e - b1["x_mid_px"])
    # y grows southward on the sheet, so the chain runs north face -> lower row -> south.
    chain_px = at_east("lower_row_north") - at_east("north_face")
    total_px = at_east("south_face") - at_east("north_face")

    return {"reading": reading, "x_ref": x_ref, "e_ref": e_ref,
            "fit": (a_n, b_n), "controls": controls, "blocks": blocks,
            "south_line": (a_s, b_s), "south_resid_px": south_resid_px,
            "branch_resid_px": branch_resid_px, "holdout": holdout,
            "chain_ft": chain_px * -a_n / FT, "total_ft": total_px * -a_n / FT}


def report(d):
    print(__doc__.strip().split("\n\n")[0])
    print()
    a_n, b_n = d["fit"]
    print(f"THE NORTHING FIT, from {len(d['controls'])} South Division corridors on this sheet")
    print(f"  N = {a_n:.6f} * px {b_n:+.4f}      ({-a_n:.4f} m/px, {-1/a_n:.2f} px/m)")
    print(f"  T-0451's independent easting fit, four other corridors: {A_E:.4f} m/px"
          f"  — the two axes agree to {abs(A_E + a_n) / A_E * 100:.3f} %")
    for c in d["controls"]:
        print(f"    {c['id']:<11} residual {c['resid_m']:+5.2f} m"
              f"   corridor drawn {c['drawn_width_m']:5.2f} m (80 ft = {CORRIDOR_M:.3f})")
    print()
    print("THE TIER, block by block, at each block's own middle")
    print("  blk        E    depth m   upper ft   alley ft   lower ft"
          "   (the sheet letters the lower row 180)")
    for b in d["blocks"]:
        mark = "" if b["in_fit"] else "   <- the North Branch block, held out"
        print(f"   {b['id']}  {b['e']:8.2f}   {b['depth_m']:7.2f}   {b['upper_row_ft']:8.1f}"
              f"   {b['alley_ft']:8.1f}   {b['lower_row_ft']:8.1f}{mark}")
    lower = [b["lower_row_ft"] for b in d["blocks"] if b["in_fit"]]
    print(f"  lower row mean {sum(lower)/len(lower):.1f} ft against the lettered"
          f" {LETTERED_LOWER_ROW_FT:.0f}")
    print()
    print("THE SOUTH FACE, one straight line across the five blocks that share it")
    for bid, r in d["south_resid_px"].items():
        print(f"    block {bid}  residual {r:+5.2f} px ({r * -d['fit'][0]:+5.2f} m)")
    print(f"    block {BRANCH_BLOCK}  residual {d['branch_resid_px']:+5.2f} px"
          f" ({d['branch_resid_px'] * -d['fit'][0]:+5.2f} m)  — held out")
    print()
    print("THE HOLDOUT — committed Kinzie was NOT in the fit, and this is why the")
    print("reading publishes depths and not northings")
    for h in d["holdout"]:
        print(f"    block {h['id']}  E {h['e']:7.2f}   read {h['read_n']:+8.2f}"
              f"   committed south kerb {h['committed_kerb_n']:+8.2f}"
              f"   resid {h['resid_m']:+6.2f} m")
    print()
    print("THE SHEET'S OWN CHAINED FIGURES, block 1's east line against the Due North line")
    print(f"    lettered {LETTERED_BLOCK_1_CHAIN_FT:.0f} (section line to the alley's south"
          f" edge)   drawn {d['chain_ft']:.1f} ft")
    print(f"    lettered {LETTERED_BLOCK_1_CHAIN_FT + LETTERED_LOWER_ROW_FT:.0f} in total"
          f"                                  drawn {d['total_ft']:.1f} ft")


def self_test(quiet=False):
    d = derive()
    fails = []

    def check(label, ok):
        if not ok:
            fails.append(label)
        if not quiet:
            print(f"  {'ok  ' if ok else 'FAIL'}  {label}")

    if not quiet:
        print("measure_north_division_tier_depth.py --self-test")
        print()

    a_n, _ = d["fit"]
    check("the northing fit lands on the easting fit's scale, within 0.1 % — two axes, "
          "seven controls, no shared arithmetic",
          abs(A_E + a_n) / A_E < 0.001)
    check("every fit control corridor is reproduced within 2 m",
          all(abs(c["resid_m"]) <= 2.0 for c in d["controls"]))
    check("each control's drawn corridor is an 80 ft street within 1.2 m",
          all(abs(c["drawn_width_m"] - CORRIDOR_M) <= 1.2 for c in d["controls"]))

    fitted = [b for b in d["blocks"] if b["in_fit"]]
    lower = [b["lower_row_ft"] for b in fitted]
    check("the lower lot row comes out the 180 ft the sheet letters in every block, "
          "within 5 ft — the check that the fit survives its extrapolation",
          all(abs(v - LETTERED_LOWER_ROW_FT) <= 5.0 for v in lower))
    check("...and to 1 ft in the mean",
          abs(sum(lower) / len(lower) - LETTERED_LOWER_ROW_FT) <= 1.0)
    check("the lower row is the CONSTANT one: it varies by under 8 ft across the tier",
          max(lower) - min(lower) < 8.0)
    check("the upper row is the WEDGE: it grows by more than 50 ft, west to east, "
          "monotonically",
          all(fitted[i]["upper_row_ft"] < fitted[i + 1]["upper_row_ft"]
              for i in range(len(fitted) - 1))
          and fitted[-1]["upper_row_ft"] - fitted[0]["upper_row_ft"] > 50.0)
    check("so the tier IS a wedge — 117 m deep at Franklin, 131 m at Wolcott — and the "
          "swing T-1436 called an error is the plat's own",
          abs(fitted[0]["depth_m"] - 116.9) < 1.0 and abs(fitted[-1]["depth_m"] - 131.3) < 1.0)
    check("the alley between the rows is a real alley, 18-24 ft in every block",
          all(18.0 <= b["alley_ft"] <= 24.0 for b in fitted))

    check("the south face is ONE straight line across those five blocks, to half a metre",
          all(abs(r * -a_n) <= 0.5 for r in d["south_resid_px"].values()))
    check("the North Branch block does NOT sit on it, which is why it is held out",
          abs(d["branch_resid_px"] * -a_n) > 1.0)

    worst = max(abs(h["resid_m"]) for h in d["holdout"])
    check("the held-out Kinzie line is MISSED, by more than 10 m at its worst — the "
          "shear that forbids publishing absolute northings up here",
          worst > 10.0)
    check("...and the miss runs with easting, monotonically, which is what makes it a "
          "shear and not scatter",
          all(d["holdout"][i]["resid_m"] > d["holdout"][i + 1]["resid_m"]
              for i in range(len(d["holdout"]) - 1)))

    check("block 1's lettered 260 is the upper row PLUS the alley, within 3 ft",
          abs(d["chain_ft"] - LETTERED_BLOCK_1_CHAIN_FT) <= 3.0)
    check("...and 260 + 180 closes on the drawn total within 6 ft",
          abs(d["total_ft"] - (LETTERED_BLOCK_1_CHAIN_FT + LETTERED_LOWER_ROW_FT)) <= 6.0)

    tier = d["reading"]["north_tier_horizontals_px"]
    check("the reading records that block 6's middle lines are NOT readable, and why",
          "6" not in tier["blocks"] and "watercourse" in tier["blocks_not_read"]["6"])
    check("the reading states it publishes depths, not northings",
          "depth" in tier["publishes"].lower()
          and "northing" in tier["does_not_publish"].lower())

    if not quiet:
        print()
        print("FAIL" if fails else "self-test OK — every assertion holds")
    if fails:
        for f in fails:
            print(f"  failed: {f}", file=sys.stderr)
        return 1
    return 0


def _scan(ink, method, xlo, xhi, ylo, yhi, cov):
    """Every horizontal line the sheet draws in a window, as (y at mid-x, lean).

    The sheet's horizontal strokes are not horizontal — the plat's east-west lines lean
    down to the east, and by DIFFERENT amounts at different latitudes (that is the shear
    this reading reports). So a row scan cannot be a single row sum the way T-0451's
    column scan could be: each candidate line is a lean AND an offset, kept when it is
    inked across `cov` of the window, then least-squares refitted through the per-column
    ink centroid with two outlier trims.
    """
    import numpy as np

    lo, hi, step = method["lean_search"]
    xs = np.arange(xlo, xhi)
    cands = []
    for lean in np.arange(lo, hi, step):
        dy = np.round(lean * (xs - xlo)).astype(int)
        for y0 in range(ylo, yhi):
            yy = y0 + dy
            if yy.max() >= ink.shape[0]:
                continue
            if float(ink[yy, xs].sum()) / len(xs) >= cov:
                cands.append((float(ink[yy, xs].sum()) / len(xs), float(lean), y0))
    cands.sort(reverse=True)
    half = method["refit_half_px"]
    out = []
    for _v, lean, y0 in cands:
        if any(abs(y0 + lean * (xhi - xlo) / 2.0 - o[0]) < method["merge_px"] for o in out):
            continue
        pts = []
        for x in range(xlo, xhi):
            yc = y0 + lean * (x - xlo)
            col = ink[int(yc - half):int(yc + half) + 1, x]
            if col.sum() < 1:
                continue
            ys = np.arange(int(yc - half), int(yc + half) + 1)
            pts.append((x, float((col * ys).sum() / col.sum())))
        if len(pts) < method["min_columns"]:
            continue
        X = np.array([p[0] for p in pts])
        Y = np.array([p[1] for p in pts])
        for _ in range(3):
            a, b = np.polyfit(X, Y, 1)
            s = (Y - (a * X + b)).std()
            if s == 0:
                break
            keep = np.abs(Y - (a * X + b)) <= 2.5 * max(s, 0.4)
            X, Y = X[keep], Y[keep]
        a, b = np.polyfit(X, Y, 1)
        out.append((round(float(a * (xlo + xhi) / 2.0 + b), 2), round(float(a), 4)))
    return sorted(out)


def reread():
    """Re-measure the sheet. Needs Pillow and numpy; the gate does not."""
    import numpy as np
    from PIL import Image

    reading, _ = load()
    tier = reading["north_tier_horizontals_px"]
    method = tier["method"]
    sheet = REPO / reading["sheet"]["path"]
    img = Image.open(sheet).convert("L")
    ink = (np.asarray(img, dtype=float) < method["ink_threshold"]).astype(np.float32)
    print(f"{sheet}  {img.size}")

    bad = 0
    faces = reading["north_tier_blocks"]["faces_px"]
    tol = method["reread_tolerance_px"]
    for bid, row in tier["blocks"].items():
        w, e = faces[bid]
        got = _scan(ink, method, int(w) + method["inset_px"], int(e) - method["inset_px"],
                    *method["tier_rows"], method["coverage"])[:4]   # the first four, ascending
        want = [row[k] for k in ("north_face", "upper_row_south",
                                 "lower_row_north", "south_face")]
        ok = len(got) == 4 and all(abs(g[0] - w0) <= tol for g, w0 in zip(got, want))
        print(f"  block {bid}: {len(got)} of 4 lines, "
              f"{'within tolerance of the committed reading' if ok else 'DIFFERS'}")
        if not ok:
            print(f"    committed {want}")
            print(f"    re-read    {[g[0] for g in got]}")
            bad += 1

    sfaces = reading["south_tier_blocks"]["faces_px"]
    ctrl = reading["south_division_control_px"]
    for sid in FIT_CONTROL:
        for edge in ("north", "south"):
            y0, y1 = ctrl[sid]["edge_rows"][edge]
            got = []
            for w, e in sfaces.values():
                xlo, xhi = int(w) + method["inset_px"], int(e) - method["inset_px"]
                hit = _scan(ink, method, xlo, xhi, y0, y1, method["control_coverage"])
                if len(hit) == 1:
                    got.append([round((xlo + xhi) / 2.0, 1), hit[0][0]])
            want = [[x, y] for x, y in ctrl[sid][edge]]
            ok = (len(got) == len(want)
                  and all(abs(g[1] - w0[1]) <= tol and g[0] == w0[0]
                          for g, w0 in zip(sorted(got), sorted(want))))
            print(f"  {sid} {edge} edge: {len(got)} sample(s), "
                  f"{'identical to the committed reading' if ok else 'DIFFERS'}")
            if not ok:
                print(f"    committed {want}")
                print(f"    re-read    {got}")
                bad += 1

    print("  every committed pixel re-read" if not bad else f"  {bad} disagreement(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    if "--gate" in sys.argv:
        raise SystemExit(self_test(quiet=True))
    if "--reread" in sys.argv:
        raise SystemExit(reread())
    report(derive())
