#!/usr/bin/env python3
"""Market Street re-fitted off the plat's own module, not off N Wacker Drive (T-0827).

T-0451 read the North Division off the Thompson plat and found one line it could not
seat with the other five. The plat's Market corridor stands 9.08 m WEST of the committed
`market` line extended north — four times the worst of the other five — and the committed
`market`->`franklin` pitch is the one South Division pitch already off the plat's 400 ft
module. `market_north` was graded `inferred` rather than `attested` on that number alone,
and T-0827 is the ticket that settles which of the two lines is wrong.

WHAT THE COMMITTED LINE STANDS ON, and it is the whole of the case against it. `market`
has two vertices. The northern one IS `control.lake_market` in
data/traces/street_control.json to the centimetre — the modern centre of West Lake Street
crossing North Upper Wacker Drive, read off OpenStreetMap. No other control touches this
street anywhere on its run: `refused_control.market_south_water` records the one other
junction this project looked for on it and could not make. So the line is ONE modern
intersection and a bearing, and the intersection is on Wacker Drive, which was built in
1926 on ground made when the river was walled. Franklin, the street one module east, has
a real crossing of two named surface roadways at `control.south_water_franklin` and
reproduces from it to 0.03 m.

THE PITCH, FOUR WAYS. All four measure the same thing — Market's centre to Franklin's,
which is one 400 ft module of the plat — and three of them agree:

  * the platted module                             121.92 m
  * Wright 1834, the ladder east of the river      120.21 m   (below)
  * Thompson 1830, the North Division tier         124.81 m   (T-0451's reading)
  * THE COMMITTED LINES                            118.0-119.2 m

The two independently measured sheets BRACKET the module, 1.7 m under and 2.9 m over,
which is what two hand-drawn sheets carrying 3-4.5 % paper stretch should do. The
committed pitch lies outside that bracket on the low side, at every northing of its run.
Nothing else on this grid does: the other five South Division pitches read 121.8-123.6.

THE WRIGHT LADDER. data/traces/vectors/street_corridors_1834.json holds a traverse run
along Lake Street on the 1834 Wright sheet, reading every block boundary line it crosses
as pixels, committed as pixels, with the sheet's own affine beside them. Five of those
lines stand east of the river and they are the evidence here. What makes them readable
as a ladder is a coincidence of this plat: the street corridor is 80 ft and a block face
is 320 ft divided into four lots, so a lot line and a street corridor are the SAME 24.384 m
step. Market's centre to Franklin's is therefore five steps of one uniform ladder, and the
ladder's span can be measured without knowing which of its gaps is the street — which is
as well, because on this reach nothing tells you: the four gaps read 27.10, 23.74, 23.40
and 21.93 m and no gap is anywhere near the 18 ft of an alley.

Market's own corridor is NOT drawn on either sheet in a form this reading can take. Its
west side is the river bank the whole way — that is why Wacker Drive stands there now —
and the Wright traverse crosses 107 m of blank paper where the committed line runs. The
Thompson plat cuts block 21 off at the Wolf Point triangle before its west line, so the
south tier has no measured Market face either (T-0451 flagged its own south read as the
extrapolation it is). Market is the one street on this grid that no sheet fixes directly,
and the module is the only thing that ever fixed it.

THE RE-FIT is therefore the ticket's own words: Franklin stepped one module west, over
Market's committed northing extent, taking Franklin's bearing. It moves the line 2.72 m
west at Madison and 3.30 m west at Lake, and it is what `market` and `market_north` now
carry. The plat's North Division residual falls from -9.08 m to -5.18 m; the line stops
reproducing `lake_market` and stands 3.30 m west of it, which is the point of the exercise
and is recorded rather than regretted.

WHAT IT COSTS. The corridor moves 3.3 m toward the river at its north end. On
e1834_harbor_cut the centreline stays dry over its whole run either way (0.39-0.78 m at
5 m sampling); the west kerb is already under water north of about N -140 on the COMMITTED
line, and the re-fit puts it 0.5 m deeper there. A kerb over the modelled bank is a
statement about the bank's own traced position, not about the street: the same 17.5 m of
datum uncertainty bounds both.

    tools/measure_market_line.py              -> print the derivation
    tools/measure_market_line.py --self-test  -> the assertions
    tools/measure_market_line.py --gate       -> the assertions, quietly
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FT = 0.3048
MODULE_M = 400 * FT            # 121.92 m: an 80 ft corridor and a 320 ft block face
STEP_M = 80 * FT               # 24.384 m: a corridor, and a quarter of a block face
HALF_CORRIDOR_M = STEP_M / 2.0

# The northings `market` is committed between. The re-fit keeps them: this ticket moves
# the line across, not along.
N_SOUTH, N_LAKE = -400.0, -110.4

# The tier T-0451 reads the North Division at, so the residual before and after is the
# same number that ticket reported.
N_NORTH = 183.0

# THE LINE THIS REPLACED, kept here because a re-fit that cannot be compared to what it
# supersedes is not a re-fit, it is an assertion. These are the vertices `market` carried
# from T-0245 until T-0827 landed, and the northern one is `control.lake_market` to the
# centimetre. Every "before" figure below is measured off this, not off the record.
SUPERSEDED = [[86.9, -400.0], [89.2, -110.4]]


def load():
    streets = json.loads((ROOT / "data" / "streets" / "1835.json").read_text())
    control = json.loads((ROOT / "data" / "traces" / "street_control.json").read_text())
    corridors = json.loads((ROOT / "data" / "traces" / "vectors"
                            / "street_corridors_1834.json").read_text())
    return streets, control, corridors


def e_at(path, n):
    """The easting of a two-point street centreline at northing `n`."""
    (e0, n0), (e1, n1) = path[0], path[-1]
    return e0 + (e1 - e0) * (n - n0) / (n1 - n0)


def wright_ladder(corridors, datum_e):
    """The block boundary lines east of the river on the Wright along-Lake traverse.

    Every candidate the traverse recorded — street, alley, wide gap or rejection — carries
    the two boundary lines that bound it as native pixels. The set of those pixels IS the
    set of lines the traverse crossed, and each is turned into a local easting through the
    sheet's own committed affine. The river is the widest gap in that set; the ladder is
    what stands east of it.
    """
    sheet = corridors["sheets"]["wright_1834"]
    co = sheet["affine"]["coefficients"]
    trav = [t for t in sheet["traverses"] if t["id"] == "along_lake"][0]
    seen = {}
    for key, cands in trav.items():
        if not isinstance(cands, list):
            continue
        for cand in cands:
            if not isinstance(cand, dict):
                continue
            for x, y in cand.get("px", []):
                e = co["a"] * x + co["b"] * y + co["c"] - datum_e
                seen[round(e, 2)] = round(co["d"] * x + co["e"] * y + co["f"], 2)
    lines = sorted(seen)
    gaps = [(b - a, i) for i, (a, b) in enumerate(zip(lines, lines[1:]))]
    _width, river = max(gaps)
    return lines[: river + 1], lines[river + 1:]


def derive():
    streets, control, corridors = load()
    by = {}
    for s in streets["streets"]:
        by.setdefault(s["id"], s)

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    lake_market = control["control"]["lake_market"]
    ctrl_e = lake_market["utm_e"] - datum["origin_utm_e"]
    ctrl_n = lake_market["utm_n"] - datum["origin_utm_n"]

    franklin = by["franklin"]["path_local_enu_m"]
    market = by["market"]["path_local_enu_m"]
    before = SUPERSEDED

    # THE RE-FIT: Franklin stepped one module west, over Market's own northing extent.
    refit = [[round(e_at(franklin, N_SOUTH) - MODULE_M, 2), N_SOUTH],
             [round(e_at(franklin, N_LAKE) - MODULE_M, 2), N_LAKE]]

    west, east = wright_ladder(corridors, datum["origin_utm_e"])
    steps = [round(b - a, 2) for a, b in zip(east, east[1:])]
    wright_module = (east[-1] - east[0]) / len(steps) * 5.0

    # The plat's North Division corridor, before and after, at the tier's own northing.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "mnds", ROOT / "tools" / "measure_north_division_streets.py")
    mnds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mnds)
    nd = {r["id"]: r for r in mnds.derive()["rows"]}

    superseded_pitch = {n: e_at(franklin, n) - e_at(before, n)
                        for n in (N_SOUTH, N_LAKE, N_NORTH)}

    return dict(
        market=market, franklin=franklin, refit=refit,
        control=(round(ctrl_e, 2), round(ctrl_n, 2)),
        control_offset_before=round(e_at(before, ctrl_n) - ctrl_e, 2),
        control_offset_after=round(e_at(refit, ctrl_n) - ctrl_e, 2),
        move={n: round(e_at(refit, n) - e_at(before, n), 2)
              for n in (N_SOUTH, N_LAKE)},
        superseded=before, superseded_pitch=superseded_pitch,
        wright_west=west, wright_east=east, wright_steps=steps,
        wright_module=wright_module,
        thompson_pitch=nd["franklin"]["e_plat"] - nd["market"]["e_plat"],
        nd_resid_before=nd["market"]["e_plat"] - e_at(before, N_NORTH),
        nd_resid_after=nd["market"]["e_plat"] - e_at(refit, N_NORTH),
        nd_others={k: v["resid"] for k, v in nd.items() if k != "market"},
        market_north=by.get("market_north"),
    )


def report():
    d = derive()
    print(__doc__.split("\n")[0])
    print()
    print("THE COMMITTED LINE AND ITS ONE CONTROL")
    print(f"  control.lake_market      local E {d['control'][0]:8.2f}  N {d['control'][1]:8.2f}")
    print(f"  the line this replaced stood  {d['control_offset_before']:+.2f} m from it")
    print(f"  the committed line now stands {d['control_offset_after']:+.2f} m from it")
    print()
    print("THE PITCH, MARKET CENTRE TO FRANKLIN CENTRE")
    print(f"  the platted module                      {MODULE_M:7.2f} m")
    print(f"  Wright 1834, the ladder east of the river{d['wright_module']:7.2f} m")
    print(f"  Thompson 1830, the North Division tier   {d['thompson_pitch']:7.2f} m")
    for n, p in sorted(d["superseded_pitch"].items()):
        print(f"  the line this replaced, at N {n:+7.1f}   {p:7.2f} m")
    print()
    print("THE WRIGHT LADDER — block boundary lines east of the river, local easting")
    print("  " + "  ".join(f"{e:8.2f}" for e in d["wright_east"]))
    print("  steps " + "  ".join(f"{s:6.2f}" for s in d["wright_steps"])
          + f"   (a corridor and a lot are both {STEP_M:.3f} m here)")
    print(f"  {len(d['wright_west'])} lines stand west of the river gap and are not read here")
    print()
    print("THE RE-FIT — Franklin stepped one module west, over Market's own extent")
    print(f"  superseded {d['superseded']}")
    print(f"  committed  {d['market']}")
    print(f"  re-fitted  {d['refit']}")
    for n, m in sorted(d["move"].items()):
        print(f"    at N {n:+7.1f} the line moves {m:+.2f} m")
    print()
    print("THE PLAT'S NORTH DIVISION CORRIDOR, BEFORE AND AFTER")
    print(f"  market   {d['nd_resid_before']:+6.2f} m  ->  {d['nd_resid_after']:+6.2f} m")
    print("  the other five, unmoved: "
          + ", ".join(f"{k} {v:+.2f}" for k, v in d["nd_others"].items()))


def self_test(quiet=False):
    d = derive()
    fails = []

    def check(label, ok):
        if not ok:
            fails.append(label)
        if not quiet:
            print(f"  {'ok  ' if ok else 'FAIL'}  {label}")

    if not quiet:
        print("measure_market_line.py --self-test")
        print()

    check("the line this replaced had its north vertex ON the modern junction it was "
          "fitted to, to the centimetre — it was one control point and a bearing",
          abs(d["superseded"][-1][0] - d["control"][0]) < 0.01
          and abs(d["superseded"][-1][1] - d["control"][1]) < 0.01)
    check("the Wright traverse crosses five block boundary lines east of the river",
          len(d["wright_east"]) == 5)
    check("...spaced within 3 m of the plat's 80 ft step, every gap, so they are one "
          "uniform ladder and none of them is an 18 ft alley",
          all(abs(s - STEP_M) < 3.0 for s in d["wright_steps"]))
    check("...and five of those steps read the module to within 2 m",
          abs(d["wright_module"] - MODULE_M) < 2.0)
    check("the Thompson North Division tier reads the module to within 3 m",
          abs(d["thompson_pitch"] - MODULE_M) < 3.0)
    check("the two sheets BRACKET the module — one under it, one over",
          d["wright_module"] < MODULE_M < d["thompson_pitch"])
    check("the pitch this re-fit replaced lay outside that bracket at every northing "
          "of the run",
          all(p < d["wright_module"] for p in d["superseded_pitch"].values()))
    check("the re-fit is Franklin stepped exactly one module west, to the centimetre",
          all(abs((e_at(d["franklin"], n) - e) - MODULE_M) < 0.01 for e, n in d["refit"]))
    check("it keeps Market's committed northing extent — this moves the line across, "
          "not along",
          [n for _e, n in d["refit"]] == [N_SOUTH, N_LAKE])
    check("it moves the line west, between 2 and 4 m, at both ends",
          all(-4.0 < m < -2.0 for m in d["move"].values()))
    check("the plat's North Division residual falls by more than a third",
          abs(d["nd_resid_after"]) < abs(d["nd_resid_before"]) * 0.67)
    check("...and market is still the worst of the six, which the record says",
          all(abs(d["nd_resid_after"]) > abs(v) for v in d["nd_others"].values()))
    check("the committed line no longer reproduces lake_market: it stood on it, and "
          "now stands 3.3 m west of it",
          abs(d["control_offset_before"]) < 0.01
          and -3.5 < d["control_offset_after"] < -3.0)

    committed = d["market"]
    check("data/streets/1835.json carries the re-fitted market, to the centimetre",
          all(abs(a - b) < 0.01 for p, q in zip(committed, d["refit"]) for a, b in zip(p, q)))
    mn = d["market_north"]
    check("market_north is committed and collinear with the re-fitted parent, "
          "within 0.02 m",
          mn is not None
          and abs(e_at(mn["path_local_enu_m"], N_NORTH) - e_at(d["refit"], N_NORTH)) < 0.02)
    check("market_north cites T-0827 for the line it now stands on",
          mn is not None and "T-0827" in (mn.get("note") or ""))
    check("market says in its note that it is no longer fitted to N Wacker Drive",
          "T-0827" in (json.loads((ROOT / "data" / "streets" / "1835.json").read_text())
                       and next(s for s in json.loads(
                           (ROOT / "data" / "streets" / "1835.json").read_text())["streets"]
                           if s["id"] == "market")["note"]))

    if not quiet:
        print()
        print("FAIL" if fails else "self-test OK — every assertion holds")
    if fails:
        for f in fails:
            print(f"  failed: {f}", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if "--gate" in sys.argv:
        sys.exit(self_test(quiet=True))
    report()
