#!/usr/bin/env python3
"""The West Division's east-west tiers, and what Carroll and Fulton imply (T-0446).

T-0446 reports that four east-west streets reach west of the river — `kinzie`,
`lake`, `randolph`, `washington` — while the plat's West Division carries six,
north to south **Kinzie, Carroll, Fulton, Lake, Randolph, Washington**. Two
platted tiers had no street between them, and 370.2 m of ground between Kinzie
and Lake was drawn as one unbroken block where the sheet draws three.

This module is the arithmetic behind seating them, and it reads committed files
only. Three things are separated by how much they depend on:

1. **The tier band, which needs no anchor.** A distance between two centrelines
   is the same wherever the grid is pinned. The West Division's tiers now step
   Kinzie → Carroll → Fulton → Lake, and that band is compared with the South
   Division's own east-west spacings — which is what T-0446 acceptance 2 asks
   for, and it is the comparison that makes the seating checkable rather than
   decorative.

2. **Fulton, which is held by control and not by arithmetic.** West Fulton
   Street still crosses all four of the West Division's north-south streets on
   the ground, so its line is fitted to four surviving intersections exactly as
   the rest of this file's West Division lines are. The four readings are
   recorded in the street's own `note`; the fit is re-measured here from the
   committed path.

3. **Carroll, which is the one interpolation, and is graded for it.** Modern
   Carroll Avenue does not survive inside the plat — the Union Station
   approaches and the Kennedy took it — so its centreline is the midpoint of
   `kinzie` and `fulton`. The two single-module steps from either neighbour
   BRACKET that midpoint, and the half-bracket is this line's uncertainty. The
   assertions below hold the midpoint inside its own bracket, so a later move of
   Kinzie or Fulton cannot quietly leave Carroll behind.

WHAT THIS DOES NOT CLAIM. It does not settle the West Division's north-south
module — that is T-0444, and `tools/measure_west_division_module.py` owns it.
The two answers do not agree, and §4 of the report says so in numbers rather
than reconciling them: T-0444 derives a 458 ft north-south module from a
two-lots-deep block, and the tier band measured here is a good deal tighter than
that. Which of the two the plat's West Division actually carries is a reading of
the sheet, and no sheet is committed to this repository.

    tools/measure_west_division_tiers.py              → print the derivation
    tools/measure_west_division_tiers.py --self-test  → the assertions
"""
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FT = 0.3048

# North to south, the order the plat carries the West Division's tiers in.
WEST_TIERS = ["kinzie", "carroll", "fulton", "lake", "randolph", "washington"]

# The two seated by T-0446.
SEATED = ["carroll", "fulton"]

# The South Division's own east-west streets, north to south. `south_water`
# is excluded deliberately: it follows the main stem rather than the plat's
# module, so a spacing taken off it measures the river and not the grid.
SOUTH_TIERS = ["lake", "randolph", "washington"]

# Where the West Division band is measured. This easting is inside the
# reconstruction's west clip (-320) and east of Clinton, so every tier carries a
# real segment there rather than an extrapolation.
WEST_PROBE_E = -250.0

# The South Division band is measured well east of the forks, clear of the
# river's own influence on the corridor.
SOUTH_PROBE_E = 500.0

# The platted street width, from the plat legend as data/streets/1835.json's
# `corridor_width_m` carries it: 80 ft.
STREET_FT = 80.0


def load(rel):
    return json.loads((ROOT / rel).read_text())


def streets():
    return {s["id"]: s for s in load("data/streets/1835.json")["streets"]}


def north_at(st, easting):
    """Where a street's PLATTED line stands at an easting, extrapolating its end
    segment if the easting is off the end. Extrapolation is honest here and only
    here: every tier is a straight run west of the river, and the probe is
    inside the committed span in any case — the fallback exists so a shortened
    path turns up as a moved number rather than a crash."""
    p = st["path_local_enu_m"]
    for a, b in zip(p, p[1:]):
        if min(a[0], b[0]) - 1e-9 <= easting <= max(a[0], b[0]) + 1e-9:
            return a[1] + (easting - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
    a, b = (p[0], p[1]) if easting < p[0][0] else (p[-2], p[-1])
    return a[1] + (easting - a[0]) / (b[0] - a[0]) * (b[1] - a[1])


def band(st, ids, easting):
    """Consecutive north-to-south spacings of a list of tiers, at one easting."""
    ns = [north_at(st[i], easting) for i in ids]
    return ns, [ns[i] - ns[i + 1] for i in range(len(ns) - 1)]


def derive():
    st = streets()

    west_n, west_gaps = band(st, WEST_TIERS, WEST_PROBE_E)
    south_n, south_gaps = band(st, SOUTH_TIERS, SOUTH_PROBE_E)

    # The Kinzie-to-Lake reach, which is the ground T-0446 says was drawn as one
    # block where the plat draws three.
    kinzie_lake = north_at(st["kinzie"], WEST_PROBE_E) - north_at(st["lake"], WEST_PROBE_E)

    # Carroll's bracket: one Fulton-to-Lake module south of Kinzie, and one north
    # of Fulton. The midpoint must lie between the two, or the interpolation has
    # stopped being an interpolation.
    k = north_at(st["kinzie"], WEST_PROBE_E)
    f = north_at(st["fulton"], WEST_PROBE_E)
    lk = north_at(st["lake"], WEST_PROBE_E)
    module = f - lk
    bracket = sorted((k - module, f + module))
    carroll = north_at(st["carroll"], WEST_PROBE_E)

    return {
        "west_probe_e": WEST_PROBE_E,
        "west_tiers": {i: round(v, 2) for i, v in zip(WEST_TIERS, west_n)},
        "west_gaps": {f"{a}->{b}": round(g, 2)
                      for a, b, g in zip(WEST_TIERS, WEST_TIERS[1:], west_gaps)},
        "south_probe_e": SOUTH_PROBE_E,
        "south_gaps": {f"{a}->{b}": round(g, 2)
                       for a, b, g in zip(SOUTH_TIERS, SOUTH_TIERS[1:], south_gaps)},
        "kinzie_lake_m": round(kinzie_lake, 2),
        "west_band_mean_m": round(statistics.fmean(west_gaps[:3]), 2),
        "south_band_mean_m": round(statistics.fmean(south_gaps), 2),
        "carroll_n": round(carroll, 2),
        "carroll_bracket": [round(bracket[0], 2), round(bracket[1], 2)],
        "carroll_half_bracket_m": round((bracket[1] - bracket[0]) / 2, 2),
        "seated": {i: st[i]["geometry_confidence"] for i in SEATED},
        "seated_sources": {i: st[i]["sources"] for i in SEATED},
    }


def report(d):
    print(f"== the West Division's tiers, at local east {d['west_probe_e']:.0f} m")
    for i in WEST_TIERS:
        mark = "  <- seated by T-0446" if i in SEATED else ""
        print(f"   {i:11s} north {d['west_tiers'][i]:8.2f}{mark}")
    print()
    print("== 1. the tier band, which needs no anchor")
    for k, v in d["west_gaps"].items():
        print(f"   {k:22s} {v:7.2f} m = {v / FT:6.1f} ft")
    print(f"   Kinzie to Lake is {d['kinzie_lake_m']} m of ground, which the plat "
          f"draws as three tiers and this file drew as one")
    print()
    print(f"== 2. against the South Division, at local east {d['south_probe_e']:.0f} m")
    for k, v in d["south_gaps"].items():
        print(f"   {k:22s} {v:7.2f} m = {v / FT:6.1f} ft")
    print(f"   West Division band mean  {d['west_band_mean_m']} m")
    print(f"   South Division band mean {d['south_band_mean_m']} m")
    print(f"   the West Division's tiers are "
          f"{d['south_band_mean_m'] - d['west_band_mean_m']:.2f} m tighter")
    print()
    print("== 3. Carroll, the one interpolation")
    print(f"   midpoint of kinzie and fulton   north {d['carroll_n']}")
    print(f"   bracketed by the two one-module steps  {d['carroll_bracket']}")
    print(f"   so this line's uncertainty is +/- {d['carroll_half_bracket_m']} m, "
          f"and it is the largest of any West Division street's")
    print()
    print("== 4. what this does NOT settle")
    print(f"   T-0444 derives a {2 * 180 + 18 + 80:.0f} ft north-south module from a "
          f"two-lots-deep block;")
    print(f"   the tier band measured here is {d['west_band_mean_m'] / FT:.0f} ft. "
          f"The two do not agree and no")
    print( "   committed sheet can be read to choose between them — "
           "see docs/RESEARCH/west_division_tiers.md")


def self_test():
    d = derive()
    fail = []

    def ck(cond, msg):
        if not cond:
            fail.append(msg)

    # The two tiers exist at all. This is acceptance 1, asserted rather than assumed.
    ck(set(SEATED) <= set(d["west_tiers"]),
       "carroll and fulton must both be in data/streets/1835.json")

    # Every seated line carries a grade and sources, which is the other half of
    # acceptance 1 — a line with no provenance is worse than an absent one here.
    for i in SEATED:
        ck(d["seated"].get(i) in ("attested", "inferred", "reconstructed"),
           f"{i} must carry a stated geometry_confidence")
        ck(bool(d["seated_sources"].get(i)), f"{i} must carry sources")

    # The plat's order, strictly north to south. A tier that crosses its
    # neighbour is the failure this catches.
    ns = [d["west_tiers"][i] for i in WEST_TIERS]
    ck(all(a > b for a, b in zip(ns, ns[1:])),
       "the six tiers must step south in the plat's order")

    # The band is regular enough to be one grid. A gap outside this range means a
    # tier moved and nobody re-derived the two that were interpolated from it.
    for k, v in d["west_gaps"].items():
        if k.startswith(("kinzie", "carroll", "fulton->lake")):
            ck(100.0 < v < 145.0, f"{k} at {v} m is outside any plausible tier module")

    # Carroll must stay INSIDE its own bracket. This is the assertion that keeps
    # the interpolation true if kinzie or fulton is ever re-derived.
    lo, hi = d["carroll_bracket"]
    ck(lo <= d["carroll_n"] <= hi,
       f"carroll at {d['carroll_n']} has left the bracket {d['carroll_bracket']} its "
       f"two neighbours put it in — re-derive it rather than leaving it behind")
    ck(d["carroll_half_bracket_m"] < 10.0,
       "carroll's bracket has opened past 10 m, which is wider than the reading "
       "its note states and the note must be corrected with it")

    # The finding of §2: the West Division's tiers really are tighter than the
    # South Division's, and it is a finding rather than a rounding error.
    ck(d["west_band_mean_m"] < d["south_band_mean_m"],
       "the West Division band must measure tighter than the South Division's, or "
       "the comparison T-0446 acceptance 2 asks for has changed sign")
    ck(d["south_band_mean_m"] - d["west_band_mean_m"] > 5.0,
       "the difference between the two bands must exceed 5 m to be worth reporting")

    # The reach the ticket opened with.
    ck(360.0 < d["kinzie_lake_m"] < 380.0,
       "Kinzie to Lake must still measure about 370 m; the two seated tiers divide "
       "exactly that reach and nothing else")

    if fail:
        for m in fail:
            print(f"  FAIL {m}")
        print(f"SELF-TEST FAIL — {len(fail)} case(s)")
        return 1
    print("SELF-TEST PASS — the West Division's tiers, the band they imply and "
          "Carroll's bracket (13 cases)")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    report(derive())
