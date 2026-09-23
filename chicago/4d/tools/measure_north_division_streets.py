#!/usr/bin/env python3
"""The North Division's north-south streets, read off the Thompson plat (T-0451).

T-0451 measured `data/streets/1835.json` and found ONE north-south street standing
north of the main stem — `wolcott` — where the plat carries the North Division's whole
grid. Seven numbered blocks cannot be bounded east and west by one line, so the tiers
between Kinzie Street and North Water Street had no cross streets and a walker saw
unbroken ground where the sheet shows blocks.

This is the reading that closes it, and its shape is T-0445's: seat what the sheet and
the modelled ground can carry, and state in numbers what they cannot.

WHAT THE SHEET SAYS, and the negative half is the important half:

* The North Division carries ONE tier of blocks between Kinzie Street and North Water
  Street, numbered 1 at the east end against the Due North line and 7 at the west end
  against the North Branch. Six 80-ft corridors stand between them.
* The sheet NAMES its north-south streets — MARKET, FRANKLIN, WELLS, LA SALLE, CLARKE
  (with an E) and DEARBORN, lettered once each in the Randolph-Washington tier — and it
  names NONE of them north of the river. Every North Division corridor carries the
  figure 80 at its head and a vertical ST. and nothing else.
* But it draws them as ONE LINE. Read as pixels on the sheet, the North Division's
  corridor centres stand within 1.5 px — 0.8 m through the fit — of the South Division
  corridors of the same street on four of the six, and the whole tier's block pitch is
  the South Division's own to 0.6 m in the mean.

So the six lines are seated as the committed South Division streets continued north from
North Water Street to Kinzie Street, and the NAME each carries is the sheet's own name on
the same line SOUTH of the river. That is a carry, not a North Division reading, and the
record says so: `wolcott` is this project's standing proof that a North Division name
could differ from the South Division name on the same line.

WHAT IS NOT SEATED THE SAME WAY. Five of the six lines agree with the plat's own module
to 2.4 m and are graded `attested`, on the owner's T-0713 ruling that a street the plat
draws is attested. `market_north` does not: the plat's corridor stands 9.2 m west of the
committed `market` line extended, four times the worst of the other five, and the
committed `market->franklin` pitch (118.5 m) is the one South Division pitch that is
already off the plat's 400 ft module. The anomaly is in the committed line — it is fitted
to modern N Wacker Drive, which was built on made ground after the river was walled — not
in the North Division, and `market_north` is graded `inferred` until that is settled.

    tools/measure_north_division_streets.py              -> print the derivation
    tools/measure_north_division_streets.py --self-test  -> the assertions
    tools/measure_north_division_streets.py --gate       -> the assertions, quietly
    tools/measure_north_division_streets.py --reread     -> re-measure the sheet itself
                                                            (needs Pillow and numpy)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
FT = 0.3048
MODULE_M = 400 * FT           # 4 x 80 ft lots + one 80 ft street = 121.92 m
CORRIDOR_M = 80 * FT          # 24.384 m

# The street each corridor continues, west to east. The NAME is the sheet's own
# lettering in the South Division; the id is this project's.
LINES = ["market", "franklin", "wells", "lasalle", "clark", "dearborn"]

# The four South Division corridors the fit is anchored on: both their block faces are
# measured, so the corridor centre is a reading and not an extrapolation.
FIT_CONTROL = ["wells", "lasalle", "clark", "dearborn"]

# The block pairs, west to east, that bound each corridor in each tier.
NORTH_PAIRS = {"market": ("7", "6"), "franklin": ("6", "5"), "wells": ("5", "4"),
               "lasalle": ("4", "3"), "clark": ("3", "2"), "dearborn": ("2", "1")}
SOUTH_PAIRS = {"wells": ("20", "19"), "lasalle": ("19", "18"),
               "clark": ("18", "17"), "dearborn": ("17", "16")}

# The northing each tier is read at. Both are the tier's own middle, and the grid's
# bearing is 0.36 degrees east of north, so moving the reference 50 m moves an easting
# by 0.3 m — a tenth of the scatter the fit already carries.
N_SOUTH = -55.0
N_NORTH = 183.0

# The 1834 traverse band for the north-south pitch, from docs/RESEARCH/thompson_plat_grid.md
# section 5 — the independent measurement T-0451 acceptance 3 asks this to be reported against.
TRAVERSE_BAND = (116.6, 123.2)


def load():
    reading = json.loads((ROOT / "data" / "traces"
                          / "thompson_north_division_streets.json").read_text())
    streets = json.loads((ROOT / "data" / "streets" / "1835.json").read_text())
    return reading, streets


def e_at(path, n):
    """The easting of a two-point street centreline at northing `n`."""
    (e0, n0), (e1, n1) = path[0], path[-1]
    return e0 + (e1 - e0) * (n - n0) / (n1 - n0)


def n_at(path, e):
    """The northing of a polyline where it crosses easting `e` (northernmost crossing)."""
    best = None
    for (e0, n0), (e1, n1) in zip(path, path[1:]):
        if min(e0, e1) <= e <= max(e0, e1):
            t = 0.0 if e1 == e0 else (e - e0) / (e1 - e0)
            n = n0 + t * (n1 - n0)
            best = n if best is None else max(best, n)
    return best


def fit_line(pts):
    n = len(pts)
    sx = sum(p for p, _ in pts)
    sy = sum(v for _, v in pts)
    sxx = sum(p * p for p, _ in pts)
    sxy = sum(p * v for p, v in pts)
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - a * sx) / n
    return a, b


def derive():
    reading, streets = load()
    by = {}
    for s in streets["streets"]:
        by.setdefault(s["id"], s)

    nf = {k: v for k, v in reading["north_tier_blocks"]["faces_px"].items()}
    sf = {k: v for k, v in reading["south_tier_blocks"]["faces_px"].items()}

    north_px, south_px = {}, {}
    for sid, (w, e) in NORTH_PAIRS.items():
        north_px[sid] = (nf[w][1] + nf[e][0]) / 2.0
    for sid, (w, e) in SOUTH_PAIRS.items():
        south_px[sid] = (sf[w][1] + sf[e][0]) / 2.0

    # The fit: pixels to local easting, anchored on four measured South Division corridors.
    control = [(south_px[s], e_at(by[s]["path_local_enu_m"], N_SOUTH)) for s in FIT_CONTROL]
    a, b = fit_line(control)
    fit_resid = {s: a * south_px[s] + b - e_at(by[s]["path_local_enu_m"], N_SOUTH)
                 for s in FIT_CONTROL}

    # The corridors the sheet closes on an end block's outer face rather than between two
    # blocks: half a platted corridor off that face.
    half = CORRIDOR_M / 2.0 / a
    south_px["franklin"] = sf["20"][0] - half
    south_px["state"] = sf["16"][1] + half
    north_px["state"] = nf["1"][1] + half

    rows = []
    # Market has no measured south face: block 21 is the Wolf Point triangle and the plat
    # cuts it off before its west line. Its south corridor is the module stepped once west
    # of Franklin's, and it is flagged as the extrapolation it is.
    south_px["market"] = south_px["franklin"] - MODULE_M / a
    extrapolated = {"market", "franklin", "state"}

    for sid in LINES:
        path = by[sid]["path_local_enu_m"]
        e_plat = a * north_px[sid] + b
        e_line = e_at(path, N_NORTH)
        rows.append({
            "id": sid,
            "north_px": north_px[sid],
            "south_px": south_px[sid],
            "dpx": north_px[sid] - south_px[sid],
            "dm": (north_px[sid] - south_px[sid]) * a,
            "e_plat": e_plat,
            "e_line": e_line,
            "resid": e_plat - e_line,
            "extrapolated": sid in extrapolated,
        })

    # Block pitch, corridor centre to corridor centre, in each tier.
    order = LINES + ["state"]
    pitch_n, pitch_s = [], []
    for i in range(len(order) - 1):
        pitch_n.append((order[i], order[i + 1], (north_px[order[i + 1]] - north_px[order[i]]) * a))
        pitch_s.append((order[i], order[i + 1], (south_px[order[i + 1]] - south_px[order[i]]) * a))

    # The seated records, and where each one runs.
    nw = by["north_water"]["path_local_enu_m"]
    kz = by["kinzie"]["path_local_enu_m"]
    seats = []
    for sid in LINES:
        rid = sid + "_north"
        path = by[sid]["path_local_enu_m"]
        # The south end is North Water Street's committed centreline where this line meets
        # it; the north end is Kinzie Street's. That is the file's own convention — a
        # north-south street's path ends on the centreline of the east-west street it meets.
        n0 = n_at(nw, e_at(path, 150.0))
        n1 = kz[0][1] + (kz[-1][1] - kz[0][1]) * (e_at(path, 250.0) - kz[0][0]) / (kz[-1][0] - kz[0][0])
        seats.append({
            "id": rid,
            "committed": by.get(rid),
            "n_from": n0,
            "n_to": n1,
            "e_from": e_at(path, n0),
            "e_to": e_at(path, n1),
        })

    return {
        "fit": (a, b),
        "fit_resid": fit_resid,
        "rows": rows,
        "pitch_north": pitch_n,
        "pitch_south": pitch_s,
        "seats": seats,
        "streets": by,
        "reading": reading,
        "north_px": north_px,
        "south_px": south_px,
    }


def report(d):
    a, b = d["fit"]
    print(__doc__.split("\n\n")[0])
    print()
    print(f"THE FIT, from {len(d['fit_resid'])} measured South Division corridors")
    print(f"  E = {a:.6f} * px  {b:+.4f}      ({a:.4f} m/px, {1/a:.2f} px/m)")
    print(f"  an 80 ft corridor is {CORRIDOR_M / a:.1f} px on this sheet")
    for sid, r in d["fit_resid"].items():
        print(f"    {sid:9s} residual {r:+6.2f} m")
    print()
    print("THE SAME LINE, NORTH AND SOUTH OF THE RIVER — corridor centres on the sheet")
    print(f"  {'street':10s} {'north px':>9s} {'south px':>9s} {'d px':>6s} {'d m':>7s}")
    for r in d["rows"]:
        print(f"  {r['id']:10s} {r['north_px']:9.2f} {r['south_px']:9.2f} "
              f"{r['dpx']:+6.2f} {r['dm']:+7.2f}")
    print()
    print(f"THE NORTH DIVISION CORRIDOR against the committed line, at N {N_NORTH:+.0f}")
    print(f"  {'street':10s} {'plat E':>8s} {'line E':>8s} {'resid':>7s}")
    for r in d["rows"]:
        print(f"  {r['id']:10s} {r['e_plat']:8.2f} {r['e_line']:8.2f} {r['resid']:+7.2f}")
    print()
    print("BLOCK PITCH, corridor centre to corridor centre, both tiers of one sheet")
    print(f"  platted module {MODULE_M:.2f} m (400 ft); 1834 traverse band "
          f"{TRAVERSE_BAND[0]}-{TRAVERSE_BAND[1]} m")
    print(f"  {'from':10s} {'to':10s} {'north':>8s} {'south':>8s}")
    for (f, t, pn), (_, _, ps) in zip(d["pitch_north"], d["pitch_south"]):
        print(f"  {f:10s} {t:10s} {pn:8.2f} {ps:8.2f}")
    mn = sum(p for _, _, p in d["pitch_north"]) / len(d["pitch_north"])
    ms = sum(p for _, _, p in d["pitch_south"]) / len(d["pitch_south"])
    print(f"  {'mean':10s} {'':10s} {mn:8.2f} {ms:8.2f}")
    print()
    print("THE SEATED LINES, North Water Street to Kinzie Street")
    for s in d["seats"]:
        got = "committed" if s["committed"] else "ABSENT"
        conf = s["committed"]["geometry_confidence"] if s["committed"] else "-"
        print(f"  {s['id']:16s} ({s['e_from']:7.2f},{s['n_from']:7.2f}) -> "
              f"({s['e_to']:7.2f},{s['n_to']:7.2f})  {got} {conf}")


def self_test(quiet=False):
    d = derive()
    fails = []

    def check(label, ok):
        if not ok:
            fails.append(label)
        if not quiet:
            print(f"  {'ok  ' if ok else 'FAIL'}  {label}")

    if not quiet:
        print("measure_north_division_streets.py --self-test")
        print()

    a, _b = d["fit"]
    check("the sheet's scale comes out near the 0.54 m/px T-0452 read independently",
          abs(a - 0.5402) < 0.01)
    check("every fit control corridor is reproduced within 0.5 m",
          all(abs(r) <= 0.5 for r in d["fit_resid"].values()))

    rows = {r["id"]: r for r in d["rows"]}
    measured = [r for r in d["rows"] if not r["extrapolated"]]
    check("the four corridors measured on BOTH tiers cross the river within 1.5 px "
          "of themselves — the sheet draws one line, not two",
          len(measured) == 4 and all(abs(r["dpx"]) <= 1.5 for r in measured))
    agree = [r for r in d["rows"] if r["id"] != "market"]
    check("five of the six stand within 2.4 m of the committed line extended, at the "
          "tier's own northing",
          all(abs(r["resid"]) <= 2.4 for r in agree))
    check("market is the one that does not, and after T-0827 re-fitted its parent off "
          "the plat's module it is out by 5.2 m rather than the 9.08 m this reading found",
          -5.5 < rows["market"]["resid"] < -4.9)

    pn = [p for _, _, p in d["pitch_north"]]
    ps = [p for _, _, p in d["pitch_south"]]
    check("the North Division's block pitch is the platted module to within 3 m, every span",
          all(abs(p - MODULE_M) <= 3.0 for p in pn))
    check("...and its mean is the South Division's own mean to within 0.7 m",
          abs(sum(pn) / len(pn) - sum(ps) / len(ps)) <= 0.7)
    check(f"...and every span lies inside the 1834 traverse band widened by the sheet's "
          f"own 3 % stretch ({TRAVERSE_BAND[0]:.1f}-{TRAVERSE_BAND[1] * 1.03:.1f} m)",
          all(TRAVERSE_BAND[0] <= p <= TRAVERSE_BAND[1] * 1.03 for p in pn))

    st = d["streets"]
    for s in d["seats"]:
        sid = s["id"]
        rec = s["committed"]
        check(f"{sid} is committed to data/streets/1835.json", rec is not None)
        if not rec:
            continue
        path = rec["path_local_enu_m"]
        check(f"{sid} runs from North Water Street to Kinzie Street, within 0.05 m",
              abs(path[0][0] - s["e_from"]) < 0.05 and abs(path[0][1] - s["n_from"]) < 0.05
              and abs(path[-1][0] - s["e_to"]) < 0.05 and abs(path[-1][1] - s["n_to"]) < 0.05)
        parent = sid[: -len("_north")]
        check(f"{sid} is collinear with the committed {parent}, within 0.02 m",
              abs(e_at(path, N_NORTH) - e_at(st[parent]["path_local_enu_m"], N_NORTH)) < 0.02)
        check(f"{sid} cites the plat that draws it", "thompson_plat_1830" in rec["sources"])
        check(f"{sid} says in its note that the plat letters no name in the North Division",
              "letters no name" in rec["note"].lower())

    check("all six carry the plat's attestation, as T-0713 ruled — market_north since "
          "T-0827 settled the parent line it stands on",
          all(st[s + "_north"]["geometry_confidence"] == "attested" for s in LINES))
    check("market_north's note says which ticket moved its parent under it",
          "T-0827" in st["market_north"]["note"])
    check("wolcott is not disturbed: it is still the line on the town's east boundary",
          "wolcott" in st and st["wolcott"]["geometry_confidence"] == "attested")

    lettering = d["reading"]["lettering"]
    check("the reading records the sheet's own spelling CLARKE for the Clark corridor",
          lettering["south_division_names_as_lettered"]["clark"] == "CLARKE")
    check("...and records that no North Division corridor is named at all",
          lettering["north_division_names"].startswith("NONE"))

    if not quiet:
        print()
        print("FAIL" if fails else "self-test OK — every assertion holds")
    if fails:
        for f in fails:
            print(f"  failed: {f}", file=sys.stderr)
        return 1
    return 0


def reread():
    """Re-measure the sheet. Needs Pillow and numpy; the gate does not."""
    from PIL import Image
    import numpy as np

    reading, _ = load()
    sheet = REPO / reading["sheet"]["path"]
    img = Image.open(sheet).convert("L")
    ink = (np.asarray(img, dtype=float) < reading["method"]["ink_threshold"]).astype(np.float32)
    print(f"{sheet}  {img.size}")

    def scan(band, xlo, xhi):
        (x0, y0), slope = band["y0_at_x"], band["dy_dx"]
        d0, d1 = band["rows"]
        n = d1 - d0
        prof = []
        for x in range(xlo, xhi):
            top = int(round(y0 + slope * (x - x0))) + d0
            prof.append(float(ink[top:top + n, x].sum()))
        thr = reading["method"]["column_coverage"] * n
        out, i = [], 0
        while i < len(prof):
            if prof[i] >= thr:
                j = i
                while j < len(prof) and prof[j] >= thr:
                    j += 1
                seg = prof[i:j]
                tot = sum(seg)
                c = xlo + i + sum(v * k for k, v in enumerate(seg)) / tot
                out.append(round(c, 1))
                i = j
            else:
                i += 1
        return out

    for key, band, span in (("north_tier_strokes_px", reading["method"]["north_band"], (1030, 2680)),
                            ("south_tier_strokes_px", reading["method"]["south_band"], (1400, 2700))):
        got = scan(band, *span)
        same = got == reading[key]
        print(f"  {key}: {len(got)} strokes, {'identical to the committed reading' if same else 'DIFFERS'}")
        if not same:
            print(f"    committed {reading[key]}")
            print(f"    re-read    {got}")
            return 1
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    if "--gate" in sys.argv:
        raise SystemExit(self_test(quiet=True))
    if "--reread" in sys.argv:
        raise SystemExit(reread())
    report(derive())
