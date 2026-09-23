#!/usr/bin/env python3
"""Derive North Water Street's platted line from the committed north bank.

T-0226. North Water Street's committed line ran 477.4 m of its 843.3 m INSIDE the
terrain's water mask, in one unbroken run from [200.2, 55] to [675.4, 95.7], and
`renderers/web/js/streets.js` therefore drew no roadway at all across that reach:
R-BUG4 drops any panel whose centreline endpoint is wet, because a crossing is a
bridge's job and a ford is not something a ribbon may paint. Three of the street's
six authored bends stood in the river.

WHICH RECORD WAS WRONG, and this tool is the answer to that question rather than a
nudge to close the gap. The two candidates were the traced north bank and the street
line, and only one of them is a reading of a source:

  * The BANK is a trace. `data/terrain/epochs/e1834_harbor_cut/river.geojson` carries
    `traced_from: wright_1834`, the segmentation method, the IIIF region and its
    sha256, `affine_rms_m: 17.5` and a stated `uncertainty_m: 20`.
  * The STREET LINE was not. Its own note said so in its own words -- "a schematic
    bank-following path used for orientation and readout ... the committed street
    module does not yet carry enough control to claim this curve as a trace" -- it
    graded its geometry `reconstructed`, the bottom tier, and it has no entry in
    `data/traces/street_control.json`, which is where a street's control lives.
  * The project had ALREADY adjudicated the conflict, in the bank's favour and in
    writing. `data/reconstruction/1835_north_division_initial_parcel.json` places the
    North Division's roofs under the constraint "Reject any footprint whose sampled
    terrain cell is water; PROXIMITY TO NORTH WATER STREET NEVER OVERRIDES THE
    AUTHORITATIVE WATER MASK", and its occupied envelope's south edge is N +105 --
    north of every point the old street line held west of E +700.
  * And the disagreement was far too big to be tracing wobble: the old line ran from
    1 m to 86 m south of the bank along that reach, up to 4.3x the trace's own stated
    +/-20 m.

So the street line is the record that was wrong, the bank is left exactly as it is,
and the line is re-derived here FROM the bank rather than drawn beside it.

THE DERIVATION. North Water Street fronted the main stem on its north side, so its
platted corridor is laid with its SOUTH line on the committed bank and the centreline
falls half a platted street north of it -- 12.192 m, the `thompson_module_1830`
half-width committed in `data/traces/street_control.json` and applied town-wide. At
each 5 m station the north bank of the main stem is read off the committed
heightfield exactly as the renderer reads it (`terrain.isWater` is
`heightfield.sample(e, n) < -0.10`), and the required centreline is the OFFSET CURVE
of that bank -- the northern boundary of the traced bank dilated by a disc of the
half-width, which is the locus of points exactly half a street module from the bank
measured as DISTANCE. The polyline is then the fewest straight runs that stay north of
every station's requirement and never wander more than MAX_ABOVE_M beyond it, so the
drawn 6 m track sits clear of the water along the whole reach and no panel is trimmed.

WHY AN OFFSET CURVE AND NOT A RAISED BANK -- T-0307. Until 2026-08-29 the requirement
was the bank's RUNNING MAXIMUM over +/-15 m of easting, plus the half-width applied
NORTHWARD. Both halves of that are east-west assumptions, and the reach west of the
slough is not east-west: coming round Wolf Point into the forks the bank falls 45 m of
northing in 35 m of easting, a running maximum taken 15 m ahead of a bank that steep
adds most of that drop to the setback, and a northward offset buys only its cosine
back. Measured on that reach the road stood 41.5 m from the water where a half module
is 12.2 -- three and a half street widths, and the rule was doing exactly what it said.
The offset curve says the intended thing instead, in one clause that holds at any
bearing: the centreline is half a platted street from the bank, perpendicular. It
also subsumes the running maximum's job. Dilating by a 12.192 m disc cannot leave a
feature finer than that radius in its boundary, so the metre-scale notches a 2.5 m
heightfield cell reads out of a trace with +/-20 m of paper stretch are cleared by
construction -- at the module's own scale, and without a slope penalty.

THE SLOUGH IS CROSSED, NOT STOPPED AT -- T-0254, and it is why this tool derives TWO
reaches with a structure between them. The attested "Unnamed slough, north side"
(`hydrology.geojson`, confidence `attested`, Wright 1834 draws it running north out of
the main stem across Kinzie Street) meets the river in a funnel between E +170 and
E +270 reaching N +145; north of that funnel the channel settles to a steady 5-7 m.
A ribbon may not paint over a watercourse -- the town's other two slough crossings are
modelled STRUCTURES, `slough_log_bridge` and the La Salle Slough Crossing -- so the
street goes ROUND THE HEAD OF THE BAY and crosses the narrow reach above it on a third
one, `north_water_slough_crossing`, whose deck runs E +183 .. +195 at N +157.5.

  * the EAST reach runs from the deck's east end to E +830, as before;
  * the WEST reach runs from the deck's west end to the North Branch at E -30, laid on
    the same bank with the same setback;
  * ONE BEND STANDS IN THE WATER, at the deck's midpoint. That is deliberate and it is
    the thing R-BUG4 is for: `renderers/web/js/streets.js` drops a panel whose
    centreline endpoint is wet, so the two panels either side of that bend are dropped
    and the deck carries the crossing. Carrying the line across with dry bends at each
    shoulder would have drawn a 6.65 m ford in silence -- the fault T-0254 was filed to
    avoid, not a shortcut past it.

Each reach's offset curve is raised on ITS OWN BANK ONLY. The dilation reaches back
SETBACK_M along the bank, and looking across the crossing with it would be wrong: at
E +190 the funnel and the slough are one water run reaching N +165, and an offset that
saw it would push the street up the slough instead of over it.

THE TWO ENDS ARE EXEMPT FROM THE SETBACK, AND THE REST OF THE STREET IS GATED ON IT
-- T-0372. The clearance report above measures the drawn centreline against the water
mask in every direction, and it reads two figures far under the half module: 5.50 m at
the west terminus on the North Branch, and 8.50 m at the slough crossing's east
abutment. T-0372 asked which of three those are, and the answer is the first: the
street ended AT the fork and ON a bridgehead, and both are places where a town street
meets water on purpose rather than places where the setback failed. The other two were
refused with numbers:

  * RAISING THE REQUIREMENT ON THE WATER MASK -- `nearest_water(e, n) >= SETBACK_M`,
    which would see the branch and the bay as well as the main stem -- cannot be
    satisfied at a crossing. Measured here: to stand a half module off the water at the
    deck's east end the street would have to be 25.5 m north of it at E +196, and 15.0 m
    north at E +200. The deck is at N +157.5. That is not an approach to a bridge, it is
    a street that never reaches one, and T-0254 already ruled the street arrives AT the
    abutment. A bridgehead is next to water by construction; a setback is the wrong
    instrument to point at one.
  * RETREATING THE TERMINUS EAST until the branch is a half module off costs 11.0 m of
    centreline and lands the street's end at E -20, where nothing is. E_WEST_END is at
    the fork because that is where the street ended; moving it buys 6.7 m of clearance
    by making the terminus arbitrary instead of sourced.

THE EAST END IS THE MEETING WITH KINZIE -- T-0447, and it is the last piece of the
1834 schematic to go. Until 2026-09-04 the derived east reach stopped at E +830 and two
AUTHORED vertices carried the street on from there to [970, 270]. They were not derived
from anything: they are `[920, 190]` and `[970, 270]` verbatim off the hand-drawn line
T-0226 replaced everywhere else -- the line whose own note read "the committed street
module does not yet carry enough control to claim this curve as a trace" -- and they
survived only because they were dry, which is not a derivation. Measured against this
tool's own rule they stand 21.1 m and 6.7 m north of what the setback asks; measured
against the town they are worse, because the terminus at [970, 270] is 17.2 m NORTH OF
KINZIE STREET's committed line and North Water Street therefore ended in the block
beyond the street it runs to.

The owner's fault report for T-0447 called the whole course wrong. It is not: the open
reach is derived and holds. But BOTH of the excursions the report names are real and
they are opposite in kind, which is why they are answered separately.

  * THE DIP TO N +2.2 AT E +5 IS THE BANK'S, AND IT IS COMMITTED. It is the west
    reach's offset curve coming round Wolf Point into the forks, where the traced bank
    falls 45 m of northing in 35 m of easting; the street follows it half a module off
    and ends AT the fork, which T-0372 ruled on and did not move. It is a reading of
    the committed bank, not a draughtsman's line, and it stays.
  * THE CLIMB TO N +270 AT E +970 IS THE DRAUGHTSMAN'S, AND IT GOES. What replaces it
    is the same climb DERIVED: east of E +830 the main stem swings north-east into the
    mouth and its north bank climbs from N +92 to N +236 in 145 m of easting, so a
    street laid half a module off it climbs too. The reach is simply continued under
    the rule that already governs the rest of the street, and it is CUT where the
    offset curve crosses `kinzie`'s committed line -- E +973.6, N +252.9. East of that
    the requirement stands north of Kinzie Street, and the plat draws no pair of
    east-west streets that swap sides. So the east end is the crossing of two committed
    records, the bank and Kinzie, and a Kinzie that moves moves it.

    The climb is 148.1 m of derived line where it was 165.8 m of drawn line, the street
    is 1165.3 m where it was 1175.8 m, and the verge over that reach came in from
    12.00 .. 27.00 m to 12.00 .. 18.00 m. Nothing west of E +830 moved: the west reach,
    the crossing and the open reach east of the slough are vertex-for-vertex what they
    were, so this is the east end and not a re-derivation of the street.

    `--self-test` case 6 holds the terminus to being a genuine crossing rather than
    wherever the search began, and case 7 makes `north_bank` refuse a bank reading that
    runs into its own walk ceiling -- the way this reach would fail silently, since the
    bank climbs toward that ceiling and a truncated read would lay the street on it.

So the exemption is written down, BOUNDED, and gated at its own floor rather than the
whole street being loosened to 5 m -- a flat 5 m gate would stop testing the 96 per cent
of this street where the half module is the actual requirement, and the open reach
measures 12.00 m. Two tiers instead:

  * THE OPEN REACH holds CLEARANCE_FLOOR_M = 11.5 m, which is the half module less the
    fit's own BELOW_M give. Measured minimum today 12.00 m.
  * THE TWO ENDS hold END_FLOOR_M = 5.0 m, and they are named windows, not a tolerance:
    the last TERMINUS_EXEMPT_M of the street at the branch, and APPROACH_EXEMPT_M either
    side of the deck's span. Measured minima 5.50 m at the terminus, 9.00 m and 8.50 m
    on the crossing's two approaches. Together the windows are 32 m of 1175.8 m.

`--gate` enforces both tiers, so a future derivation that lets the street drift toward
the water anywhere else is refused, and one that walks either end further in is too.

    tools/derive_north_water.py            print the derivation
    tools/derive_north_water.py --write    write it into data/streets/1835.json
    tools/derive_north_water.py --gate     exit 1 if the committed line is not this one
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPOCH = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
STREETS = ROOT / "data" / "streets" / "1835.json"

# The renderer's own waterline (renderers/web/js/terrain.js SHORE_Y). Read it here
# rather than restating a number: a mask the ribbon disagrees with is the whole fault.
SHORE_Y = -0.10

SETBACK_M = 12.192          # half the 80 ft platted street module, thompson_module_1830
STATION_M = 5.0             # how finely the bank is read
MAX_ABOVE_M = 8.0           # how far a straight run may stand north of what it needs
BANK_STEP_M = 0.5           # how finely the traced bank is walked for the offset curve
BELOW_M = 0.5               # how far a run may fall short of the setback (see fit)
# THE EAST END (T-0447). The street runs east on the bank until the bank's own offset
# curve MEETS KINZIE STREET's committed line, and it ends there. Until 2026-09-04 the
# derivation stopped at E +830 and two authored vertices carried it on to [970, 270] --
# `TAIL = [[920.0, 190.0], [970.0, 270.0]]`, kept verbatim from the hand-drawn
# schematic T-0226 replaced everywhere else and commented "unchanged: dry, drawn, and
# not in question". They were the last surviving fragment of a line whose own note said
# "the committed street module does not yet carry enough control to claim this curve as
# a trace", and they stood 21.1 m north of what the setback rule asks at E +970 and
# 17.2 m north of KINZIE STREET ITSELF -- North Water Street ended in the block beyond
# the street it runs to. See the module docstring, THE EAST END IS THE MEETING WITH
# KINZIE.
E_EAST_LIMIT = 995.0        # how far east the bank is read while looking for the meeting
KINZIE = "kinzie"           # the committed line the east end is found against
BANK_WALK_N_MAX = 260.0     # north_bank's own walk ceiling, asserted against below

# THE CROSSING (T-0254). These three numbers are the deck's, and they are read off
# `data/structures/north_water_slough_crossing.json` rather than restated -- the
# structure record is the one that decides where the crossing is, and a deck that moves
# has to move the street with it or the two disagree in silence.
CROSSING = "north_water_slough_crossing"
# The North Branch. West of E -35 the widest water run at an easting is no longer the
# main stem: the branch merges into it and its north edge jumps from N +33 to N +216 in
# one 5 m step, so the setback rule has nothing to read. The street ends where the
# street ended -- at the branch.
E_WEST_END = -30.0

# THE CLEARANCE RULE AND ITS TWO EXEMPT ENDS -- T-0372; the reasoning is in the module
# docstring, THE TWO ENDS ARE EXEMPT. The floors are measured figures with margin, not
# tuned ones: the open reach reads 12.00 m today and the tightest end 5.50 m.
CLEARANCE_FLOOR_M = 11.5     # the open reach: the half module less the fit's BELOW_M
END_FLOOR_M = 5.0            # the terminus and the bridgeheads, where the street meets water
TERMINUS_EXEMPT_M = 10.0     # how far east of E_WEST_END the terminus window reaches
APPROACH_EXEMPT_M = 10.0     # how far either side of the deck the approach windows reach
CLEARANCE_STEP_M = 2.0       # how finely the drawn centreline is probed for the gate


def load_field():
    spec = json.loads((EPOCH / "heightfield.json").read_text())
    cols, rows = spec["cols"], spec["rows"]
    raw = (EPOCH / "heightfield.bin").read_bytes()
    grid = struct.unpack("<%dh" % (cols * rows), raw)
    cell, scale = spec["cell_m"], spec["scale"]
    oe, on = spec["origin_e"], spec["origin_n"]

    def sample(e, n):
        x = (e - oe) / cell
        y = (n - on) / cell
        if x < 0 or y < 0 or x > cols - 1 or y > rows - 1:
            return None
        x0, y0 = int(x), int(y)
        x1, y1 = min(x0 + 1, cols - 1), min(y0 + 1, rows - 1)
        fx, fy = x - x0, y - y0
        g = lambda c, r: grid[r * cols + c] * scale
        lo = g(x0, y0) * (1 - fx) + g(x1, y0) * fx
        hi = g(x0, y1) * (1 - fx) + g(x1, y1) * fx
        return lo * (1 - fy) + hi * fy

    def is_water(e, n):
        v = sample(e, n)
        return v is not None and v < SHORE_Y

    return is_water


def north_bank(is_water, e, step=0.25):
    """North edge of the MAIN STEM at this easting.

    Not "the first dry northing above the first water": the two committed slough
    cuts (`slough_log_bridge` at E 805-813 and the La Salle Slough Crossing at
    E 461-473) put a narrow south-side channel in the way, and a walk that starts
    below them answers with the drain's own north lip. The main stem is by a wide
    margin the widest water run on any of these eastings, so the widest run is the
    one that is asked, and its north end is the bank.
    """
    runs = []
    n = -80.0
    start = None
    while n < BANK_WALK_N_MAX:
        wet = is_water(e, n)
        if wet and start is None:
            start = n
        elif not wet and start is not None:
            runs.append((start, n))
            start = None
        n += step
    if start is not None:
        runs.append((start, n))
    if not runs:
        return None
    top = max(runs, key=lambda r: r[1] - r[0])[1]
    # THE WALK HAS A CEILING AND IT MUST NOT BIND (T-0447). East of the mouth the main
    # stem swings north-east and its bank climbs fast; a bank read that ran into the
    # ceiling would answer with the ceiling and the street would be laid on a number
    # this tool invented. Refuse instead. 5 m of headroom is two station steps of the
    # bank's own steepest climb.
    if top > BANK_WALK_N_MAX - 5.0:
        raise SystemExit("the north bank at E %.1f reads N %.1f, within 5 m of "
                         "north_bank's own walk ceiling of N %.1f -- raise the ceiling "
                         "and re-derive rather than laying the street on a truncated "
                         "reading" % (e, top, BANK_WALK_N_MAX))
    return top


def kinzie_line():
    """Kinzie Street's committed centreline, as a northing per easting.

    Read from the same file this tool writes, and it is a different record: North Water
    Street's east end is found AGAINST Kinzie, so a Kinzie that moves moves this
    terminus with it instead of leaving the two streets disagreeing about where they
    meet -- the same rule the crossing's deck is read under.
    """
    doc = json.loads(STREETS.read_text())
    path = [(float(e), float(n))
            for e, n in next(s for s in doc["streets"]
                             if s["id"] == KINZIE)["path_local_enu_m"]]

    def n_at(e):
        for i in range(len(path) - 1):
            e0, n0 = path[i]
            e1, n1 = path[i + 1]
            if min(e0, e1) <= e <= max(e0, e1):
                t = (e - e0) / (e1 - e0) if e1 != e0 else 0.0
                return n0 + (n1 - n0) * t
        raise SystemExit("E %.1f is off %s's committed line" % (e, KINZIE))

    return n_at


def deck():
    """The crossing's deck, read out of the structure record.

    Returns (west_end_e, east_end_e, centreline_n). The record's footprint polygon IS
    the deck -- u along the span, v across the width -- laid at the placement, exactly
    as tools/measure_slough_crossing.py reads it. Read rather than restated so a deck
    that is re-sized or re-sited moves this street with it instead of leaving the two
    records disagreeing about where the town crosses its own slough.
    """
    rec = json.loads((ROOT / "data" / "structures" / (CROSSING + ".json")).read_text())
    phase = rec["phases"][0]
    poly = [(float(u), float(v)) for u, v in phase["footprint"]["polygon"]]
    if float(phase["position"].get("rotation_deg", 0.0)) != 0.0:
        raise SystemExit("%s is no longer laid square; this tool reads an east-west "
                         "deck and would have to be taught the rotation" % CROSSING)
    e0 = float(phase["position"]["utm_e"])
    n0 = float(phase["position"]["utm_n"])
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    e0 -= float(datum["origin_utm_e"])
    n0 -= float(datum["origin_utm_n"])
    us = [u for u, _ in poly]
    vs = [v for _, v in poly]
    return e0 + min(us), e0 + max(us), n0 + 0.5 * (min(vs) + max(vs))


def offset_curve(raw):
    """The bank polyline dilated by a SETBACK_M disc, read as a northing per easting.

    `raw` is [(easting, bank northing)] for ONE reach. The bank between its stations is
    walked at BANK_STEP_M, and the requirement at an easting is the highest point any of
    those bank points holds a disc of radius SETBACK_M up to:

        need(e) = max over bank points p, |p.e - e| < SETBACK_M, of
                  p.n + sqrt(SETBACK_M^2 - (p.e - e)^2)

    which is exactly the upper boundary of the dilation. On a bank running east-west it
    is `bank + SETBACK_M`, the old rule; on a bank running at 35 degrees it is
    `bank + SETBACK_M / cos 35` northward, which is still SETBACK_M perpendicular --
    and that difference is the whole of T-0307.
    """
    dense = []
    for i in range(len(raw) - 1):
        e0, n0 = raw[i]
        e1, n1 = raw[i + 1]
        span = math.hypot(e1 - e0, n1 - n0)
        steps = max(1, int(span / BANK_STEP_M))
        for k in range(steps):
            t = k / steps
            dense.append((e0 + (e1 - e0) * t, n0 + (n1 - n0) * t))
    dense.append(raw[-1])

    def need(e):
        best = None
        for pe, pn in dense:
            dx = pe - e
            if abs(dx) >= SETBACK_M:
                continue
            n = pn + math.sqrt(SETBACK_M * SETBACK_M - dx * dx)
            if best is None or n > best:
                best = n
        if best is None:
            raise SystemExit("no bank within a half module of E %.1f" % e)
        return best

    return need


def stations(is_water, e_from, e_to, anchor=None):
    """Bank and required centreline at every station of ONE reach.

    The requirement is the bank's OFFSET CURVE at SETBACK_M -- `offset_curve` below --
    rather than a running maximum of the bank plus a northward setback. T-0307: the
    running maximum and the northward offset are both east-west assumptions, and they
    cost 29 m of extra verge where the bank turns into the forks at Wolf Point. The
    offset curve is the same claim stated as a distance, so it holds at any bearing,
    and its own radius clears the trace's metre-scale notches for free (see the module
    docstring, WHY AN OFFSET CURVE AND NOT A RAISED BANK).

    THE OFFSET IS RAISED ON THE REACH'S OWN BANK. It matters for the same reason the
    old smoothing window was clamped: a reach ends AT THE CROSSING, and the water on
    the far side of the deck is the slough, whose far bank is not this street's.

    `anchor` is (easting, northing) -- the deck's own abutment, imposed at the reach's
    crossing end: the
    street has to arrive AT the abutment, not at where the setback rule would have put
    it. The two differ by 7.6 m at the west abutment -- the bay's edge is still climbing
    there -- and that difference is the crossing's approach, carried by the fit's
    ordinary MAX_ABOVE_M slack rather than by a special case.
    """
    raw = []
    e = e_from
    while e <= e_to + 1e-9:
        bank = north_bank(is_water, e)
        if bank is None:
            raise SystemExit("no north bank at E %.1f" % e)
        raw.append((e, bank))
        e += STATION_M
    if abs(raw[-1][0] - e_to) > 1e-9:
        bank = north_bank(is_water, e_to)
        if bank is None:
            raise SystemExit("no north bank at E %.1f" % e_to)
        raw.append((e_to, bank))
    curve = offset_curve(raw)
    out = []
    for e, bank in raw:
        out.append((e, bank, curve(e)))
    if anchor is not None:
        ae, an = anchor
        for i, (e, bank, _) in enumerate(out):
            if abs(e - ae) < 1e-9:
                out[i] = (e, bank, an)
                break
        else:
            raise SystemExit("the deck's abutment at E %.1f is not a station of the "
                             "reach E %.1f .. %.1f" % (ae, e_from, e_to))
    return out


def clears(st, pts, i0, i1, slack):
    """Does the straight run pts[i0]->pts[i1] clear every station beneath it?"""
    e0, n0 = pts[i0]
    e1, n1 = pts[i1]
    for e, _, need in st:
        if e < min(e0, e1) - 1e-9 or e > max(e0, e1) + 1e-9:
            continue
        t = (e - e0) / (e1 - e0) if e1 != e0 else 0.0
        n = n0 + (n1 - n0) * t
        if n < need - BELOW_M or n > need + slack:
            return False
    return True


def fit(st):
    """Fewest straight runs that clear every station and stay within MAX_ABOVE_M.

    BELOW_M is the reason this is four runs and not ten. Held to the setback exactly,
    the fit has to break every time the bank rises a decimetre, and the town gets a
    street that changes bearing by a degree every 30 m -- which the joint probe reads
    as slivers of uncovered ground at bends too shallow to be bends. Half a metre of
    give is 2.5 % of the bank trace's own stated +/-20 m: immaterial to the claim, and
    the difference between a street and a jitter.
    """
    pts = [[st[0][0], st[0][2]]]
    i = 0
    while i < len(st) - 1:
        j = len(st) - 1
        while j > i + 1 and not clears(st, pts + [[st[j][0], st[j][2]]], len(pts) - 1, len(pts), MAX_ABOVE_M):
            j -= 1
        pts.append([st[j][0], st[j][2]])
        i = j
    # The greedy run has to stop the moment it cannot reach any further, which leaves
    # short stubs at every place the bank turns. Drop a bend whose neighbours can see
    # each other across it: fewer, longer runs, the same clearance guarantee.
    changed = True
    while changed and len(pts) > 2:
        changed = False
        for k in range(1, len(pts) - 1):
            if clears(st, pts, k - 1, k + 1, MAX_ABOVE_M):
                del pts[k]
                changed = True
                break
    return pts


def fit_reach(st):
    pts = [[round(e, 1), round(n, 1)] for e, n in fit(st)]
    # Rounding to a decimetre can only move a vertex 5 cm; lift any that fell short.
    for pt in pts:
        need = next(s for s in st if abs(s[0] - pt[0]) < 1e-6)[2]
        if pt[1] < need:
            pt[1] = round(need + 0.05, 1)
    return pts


def reach(is_water, e_from, e_to, anchor):
    st = stations(is_water, e_from, e_to, anchor)
    return fit_reach(st), st


def east_stations(is_water, e_from, anchor):
    """The east reach's stations, ending where the offset curve meets Kinzie Street.

    T-0447. The bank is read east to E_EAST_LIMIT so the offset curve is complete over
    the whole reach, and the reach is then CUT at the easting where that curve crosses
    `kinzie`'s committed line. East of the crossing the requirement stands NORTH of
    Kinzie Street: the bank has swung north-east into the mouth far enough that a line
    half a platted street off it would be on the far side of the street it runs to, and
    the plat draws no such pair. So the crossing is the street's east end, and it is
    derived from two committed records rather than authored -- the bank and Kinzie.

    Returns (stations, meeting easting).
    """
    st = stations(is_water, e_from, E_EAST_LIMIT, anchor)
    kin = kinzie_line()
    e_meet = None
    for i in range(1, len(st)):
        (ea, _ba, na), (eb, _bb, nb) = st[i - 1], st[i]
        da, db = na - kin(ea), nb - kin(eb)
        if da < 0.0 <= db:
            e_meet = round(ea + (eb - ea) * (-da) / (db - da), 1)
            break
    if e_meet is None:
        raise SystemExit("the bank's offset curve never meets %s between E %.1f and "
                         "E %.1f, so this street has no derived east end"
                         % (KINZIE, e_from, E_EAST_LIMIT))
    out = [s for s in st if s[0] < e_meet - 1e-9]
    out.append((e_meet, north_bank(is_water, e_meet), kin(e_meet)))
    return out, e_meet


def derive():
    is_water = load_field()
    w_end, e_end, n_deck = deck()
    west, st_w = reach(is_water, E_WEST_END, w_end, (w_end, n_deck))
    st_e, _e_meet = east_stations(is_water, e_end, (e_end, n_deck))
    east = fit_reach(st_e)
    # THE BEND IN THE WATER. One vertex at the deck's midpoint, and it is wet on
    # purpose: R-BUG4 drops a panel whose centreline endpoint is wet, so the two panels
    # that reach the abutments go with it and the deck is what a visitor crosses on.
    mid = [round(0.5 * (w_end + e_end), 1), round(n_deck, 1)]
    return west + [mid] + east, st_w + st_e, is_water


def report(path, st, is_water):
    print("North Water Street, derived from the committed north bank")
    print("  setback %.3f m north of the bank (half the 80 ft platted module)" % SETBACK_M)
    print("  %d authored bends, %s" % (len(path), " ".join("[%g, %g]" % (e, n) for e, n in path)))
    worst_low, worst_high = 99.0, 0.0
    wet = 0.0
    total = 0.0
    w_end, e_end, _n_deck = deck()
    for i in range(len(path) - 1):
        e0, n0 = path[i]
        e1, n1 = path[i + 1]
        length = ((e1 - e0) ** 2 + (n1 - n0) ** 2) ** 0.5
        total += length
        steps = max(1, int(length / 0.5))
        for k in range(steps + 1):
            t = k / steps
            e, n = e0 + (e1 - e0) * t, n0 + (n1 - n0) * t
            if is_water(e, n):
                wet += 0.5
    for e, bank, need in st:
        if w_end - 1e-9 <= e <= e_end + 1e-9:
            continue          # the deck's own span: measured by measure_slough_crossing
        n = at(path, e)
        worst_low = min(worst_low, n - bank)
        worst_high = max(worst_high, n - bank)
    print("  length %.1f m, of which wet centreline: %.1f m" % (total, wet))
    print("  clearance from the waterline, northward: %.2f m .. %.2f m"
          % (worst_low, worst_high))
    # THE NORTHWARD FIGURE IS NOT THE CLEARANCE A WALKER SEES: where the bank runs at
    # 30-60 degrees, as it does west of the slough coming round Wolf Point into the
    # forks, a road half a module clear of the water stands `SETBACK_M / cos(bearing)`
    # north of the bank, which is a larger number saying the same thing. The
    # perpendicular figure is the honest statement of how far the road is from the
    # water, and since T-0307 it is also the figure the derivation is built on -- the
    # requirement is the bank's offset curve, so anything above SETBACK_M here is the
    # fit's own MAX_ABOVE_M slack and nothing else.
    print("  clearance from the waterline, perpendicular: %.2f m .. %.2f m"
          % perpendicular_clearance(path, is_water, w_end, e_end))
    # PER REACH, because the two reaches are not the same problem (T-0307): the east
    # reach's bank runs roughly east-west and the west reach's turns Wolf Point.
    e_meet = path[-1][0]
    for label, lo_e, hi_e in (("west of the slough  ", E_WEST_END, w_end),
                              ("east of the slough  ", e_end, 830.0),
                              ("the climb to Kinzie ", 830.0, e_meet)):
        print("    %s: %.2f m .. %.2f m" % (
            (label,) + perpendicular_clearance(path, is_water, w_end, e_end,
                                               lo_e, hi_e)))
    # THE TWO-TIER CLEARANCE RULE -- T-0372. Reported per tier as well as per reach,
    # because the per-reach minima are the two exempt ends and they hide what the rest
    # of the street holds: west of the slough reads 5.50 m and 9.00 m of it is the last
    # eight metres at the fork.
    tiers = {}
    for e, n, where in clearance_probes(path, w_end, e_end):
        tier = where or "the open reach"
        d = nearest_water(is_water, e, n)
        lo, hi, count = tiers.get(tier, (999.0, 0.0, 0))
        tiers[tier] = (min(lo, d), max(hi, d), count + 1)
    print("  the clearance rule (T-0372): the open reach owes %.1f m, the two ends %.1f m"
          % (CLEARANCE_FLOOR_M, END_FLOOR_M))
    for tier in ("the open reach", "the west terminus at the North Branch",
                 "the slough crossing's approaches"):
        if tier not in tiers:
            continue
        lo, _hi, count = tiers[tier]
        floor = CLEARANCE_FLOOR_M if tier == "the open reach" else END_FLOOR_M
        print("    %-38s %5.2f m minimum over %3d probe(s), floor %.1f m"
              % (tier, lo, count, floor))
    breaches = clearance_gate(path, is_water)
    print("    exempt because the street MEETS the water there on purpose: it ends at "
          "the fork (T-0226) and is anchored on the crossing's abutments (T-0254); a "
          "half-module setback at the deck's east end would stand the street 15.0 m "
          "north of it and never reach the bridge")
    print("    breaches: %s" % ("none" if not breaches else "%d" % len(breaches)))
    _w, _e, n_deck = w_end, e_end, deck()[2]
    dry_edges = [q for q in edge_probes(path)
                 if not (w_end - 4.0 <= q[0] <= e_end + 4.0) and is_water(*q)]
    print("  the drawn 6 m track's own edges, off the deck: %s"
          % ("all dry" if not dry_edges else "%d WET" % len(dry_edges)))
    print("  bends standing in water: %s"
          % (" ".join("[%g, %g]" % (e, n) for e, n in path if is_water(e, n)) or "none"))
    print("  the crossing: %s, deck E %g .. %g at N %g" % (CROSSING, w_end, e_end, n_deck))


def perpendicular_clearance(path, is_water, w_end, e_end, e_from=None, e_to=None,
                            step=2.0):
    """Nearest water to the drawn centreline, off the deck's own span.

    The nearest point of a waterline is always square to it, so this IS the
    perpendicular clearance -- but it is found by looking in every direction rather
    than along one ray. Until T-0307 it pushed a ray square to the CHORD, both sides,
    which reads the true distance only where the bank happens to run parallel to the
    chord: at the street's west terminus on the North Branch the same vertex measured
    12.50 m against the old line's chord and 9.50 m against the new one's, with the
    vertex itself unmoved. A statistic that moves when nothing moved cannot carry a
    before-and-after, so the ray was replaced by an expanding ring.

    `e_from`/`e_to` bound the reach measured, so each reach can be reported on its own
    terms -- which is the whole point west of the slough.
    """
    lo, hi = 999.0, 0.0
    for i in range(len(path) - 1):
        e0, n0 = path[i]
        e1, n1 = path[i + 1]
        length = ((e1 - e0) ** 2 + (n1 - n0) ** 2) ** 0.5
        if length < 1e-9:
            continue
        for k in range(int(length / step) + 1):
            t = k * step / length
            e, n = e0 + (e1 - e0) * t, n0 + (n1 - n0) * t
            if w_end - 4.0 <= e <= e_end + 4.0:
                continue          # the deck's own reach; the crossing owns that water
            if e_from is not None and e < e_from - 1e-9:
                continue
            if e_to is not None and e > e_to + 1e-9:
                continue
            d = nearest_water(is_water, e, n)
            lo, hi = min(lo, d), max(hi, d)
    return lo, hi


def end_exemption(e, w_end, e_end):
    """Which of T-0372's two exempt ends this easting belongs to, or None.

    The windows are named places rather than a tolerance, and they are bounded: the
    street's last run down to the fork, and the ground either side of the crossing's
    deck where the line is anchored on the abutments instead of on the setback.
    """
    if e <= E_WEST_END + TERMINUS_EXEMPT_M:
        return "the west terminus at the North Branch"
    if w_end - APPROACH_EXEMPT_M <= e <= e_end + APPROACH_EXEMPT_M:
        return "the slough crossing's approaches"
    return None


def clearance_short_of(is_water, e, n, floor, step=0.5):
    """The distance to water if it is UNDER `floor`, else None.

    `nearest_water` with an early exit at the floor, and the reason for the second
    function is cost: the gate asks a yes-or-no question of 587 probes, and the honest
    answer for most of them is "further than 80 m", which the full search pays for one
    ring at a time. Bounded at the floor it is the same walk stopped where the answer
    stops mattering.
    """
    r = step
    while r <= floor + 1e-9:
        count = max(8, int(2 * math.pi * r / step))
        for k in range(count):
            a = 2 * math.pi * k / count
            if is_water(e + math.cos(a) * r, n + math.sin(a) * r):
                return r
        r += step
    return None


def clearance_probes(path, w_end, e_end, step=CLEARANCE_STEP_M):
    """Every probe on the drawn centreline off the deck's own span, with its tier."""
    for i in range(len(path) - 1):
        e0, n0 = path[i]
        e1, n1 = path[i + 1]
        length = math.hypot(e1 - e0, n1 - n0)
        if length < 1e-9:
            continue
        for k in range(int(length / step) + 1):
            t = k * step / length
            e, n = e0 + (e1 - e0) * t, n0 + (n1 - n0) * t
            if w_end - 4.0 <= e <= e_end + 4.0:
                continue          # the deck's own reach; the crossing owns that water
            yield e, n, end_exemption(e, w_end, e_end)


def clearance_gate(path, is_water):
    """T-0372's two-tier clearance rule, as a list of breaches.

    The open reach owes CLEARANCE_FLOOR_M and the two named ends owe END_FLOOR_M. A
    breach is returned as (easting, northing, distance, floor, tier) so the caller can
    say which rule was broken and where, rather than only that something was.
    """
    w_end, e_end, _n_deck = deck()
    bad = []
    for e, n, where in clearance_probes(path, w_end, e_end):
        floor = END_FLOOR_M if where else CLEARANCE_FLOOR_M
        d = clearance_short_of(is_water, e, n, floor)
        if d is not None:
            bad.append((e, n, d, floor, where or "the open reach"))
    return bad


def nearest_water(is_water, e, n, limit=80.0, step=0.5):
    """Distance from (e, n) to the closest wet cell in ANY direction, or `limit`."""
    r = step
    while r <= limit:
        count = max(8, int(2 * math.pi * r / step))
        for k in range(count):
            a = 2 * math.pi * k / count
            if is_water(e + math.cos(a) * r, n + math.sin(a) * r):
                return r
        r += step
    return limit


def at(path, e):
    for i in range(len(path) - 1):
        e0, n0 = path[i]
        e1, n1 = path[i + 1]
        if min(e0, e1) <= e <= max(e0, e1):
            t = (e - e0) / (e1 - e0) if e1 != e0 else 0.0
            return n0 + (n1 - n0) * t
    return path[-1][1]


def edge_probes(path, half=3.0, step=1.0):
    out = []
    for i in range(len(path) - 1):
        e0, n0 = path[i]
        e1, n1 = path[i + 1]
        length = ((e1 - e0) ** 2 + (n1 - n0) ** 2) ** 0.5
        ue, un = -(n1 - n0) / length, (e1 - e0) / length
        for k in range(int(length / step) + 1):
            t = k * step / length
            e, n = e0 + (e1 - e0) * t, n0 + (n1 - n0) * t
            out.append((e + ue * half, n + un * half))
            out.append((e - ue * half, n - un * half))
    return out


def self_test():
    """Every way T-0372's clearance rule could fail to bite, made to bite.

    A gate that has never been seen to refuse anything is a comment. Three of these
    walk a stretch of the committed line toward the water until its own tier's floor is
    broken; the fourth is the one that matters most, because it proves the two
    exemptions are LOAD-BEARING rather than decorative -- the committed terminus and
    abutment probes are under the open reach's floor and would be refused without them.
    """
    is_water = load_field()
    path, _st, _iw = derive()
    w_end, e_end, _n = deck()
    cases = 0
    fails = []

    def south(seg, drop):
        return [[e, n - drop] for e, n in seg]

    def bites(seg, label, limit=20.0):
        nonlocal cases
        cases += 1
        for drop in range(1, int(limit) + 1):
            if clearance_gate(south(seg, float(drop)), is_water):
                print("  fires: %s, %d m toward the water" % (label, drop))
                return
        fails.append("%s never refused within %g m of the water" % (label, limit))

    # 1-3. Each tier refuses its own stretch walked toward the water.
    bites([[375.0, 121.6], [410.0, 118.1]], "the open reach walked south")
    bites([[-30.0, 45.2], [-25.0, 44.2]], "the west terminus walked south")
    bites([[200.0, 156.9], [230.0, 141.3]], "the crossing's east approach walked south")

    # 4. The exemptions are load-bearing: the committed line's own end probes are
    # UNDER the open reach's floor, so without the two windows this gate would refuse
    # the line it is committed to hold.
    cases += 1
    exempt_under_open = [
        (e, n, where) for e, n, where in clearance_probes(path, w_end, e_end)
        if where and clearance_short_of(is_water, e, n, CLEARANCE_FLOOR_M) is not None
    ]
    if exempt_under_open:
        print("  fires: %d exempt probe(s) are under the open reach's %.1f m floor, so "
              "the two windows are what let the committed line stand"
              % (len(exempt_under_open), CLEARANCE_FLOOR_M))
    else:
        fails.append("no exempt probe is under the open floor, so the windows are "
                     "exempting nothing and the rule is one tier pretending to be two")

    # 5. The windows are BOUNDED -- a metre past either edge is open reach again.
    cases += 1
    edges = [
        (E_WEST_END + TERMINUS_EXEMPT_M - 1.0, "the west terminus at the North Branch"),
        (E_WEST_END + TERMINUS_EXEMPT_M + 1.0, None),
        (w_end - APPROACH_EXEMPT_M + 1.0, "the slough crossing's approaches"),
        (w_end - APPROACH_EXEMPT_M - 1.0, None),
        (e_end + APPROACH_EXEMPT_M - 1.0, "the slough crossing's approaches"),
        (e_end + APPROACH_EXEMPT_M + 1.0, None),
    ]
    wrong = [(e, want, end_exemption(e, w_end, e_end))
             for e, want in edges if end_exemption(e, w_end, e_end) != want]
    if wrong:
        fails.append("the exempt windows do not end where they say: %s" % (wrong,))
    else:
        print("  ok:    both windows end where they are declared to (6 edge cases)")

    # 6. THE EAST END IS A CROSSING, NOT A NUMBER -- T-0447. The terminus is only
    # derived if the offset curve is genuinely SOUTH of Kinzie Street a station before
    # it and NORTH of Kinzie a station after; a curve that merely grazed the line, or
    # one that had already been north of it for 200 m, would put the street's end
    # wherever the search happened to start.
    cases += 1
    st_e, e_meet = east_stations(is_water, e_end, (e_end, deck()[2]))
    kin = kinzie_line()
    before = st_e[-2]
    after = stations(is_water, e_meet, e_meet + 2 * STATION_M, None)[-1]
    gap_before = kin(before[0]) - before[2]
    gap_after = after[2] - kin(after[0])
    if gap_before > 0.0 and gap_after > 0.0:
        print("  ok:    the east end at E %+.1f is a crossing: the offset curve is "
              "%.2f m SOUTH of %s one station before it and %.2f m NORTH of it two "
              "stations after" % (e_meet, gap_before, KINZIE, gap_after))
    else:
        fails.append("the east end at E %+.1f is not a crossing of the offset curve "
                     "and %s (%.2f m before, %.2f m after), so the terminus is not "
                     "derived from those two records"
                     % (e_meet, KINZIE, gap_before, gap_after))

    # 7. THE BANK WALK'S CEILING REFUSES A TRUNCATED READ. north_bank answers with the
    # top of the widest wet run below BANK_WALK_N_MAX, so a ceiling that bound would
    # return the ceiling and this street would be laid on it. Proved by lowering the
    # ceiling under a reading the committed line depends on.
    cases += 1
    saved = globals()["BANK_WALK_N_MAX"]
    globals()["BANK_WALK_N_MAX"] = 120.0
    try:
        north_bank(is_water, e_meet)
        fails.append("north_bank did not refuse a bank read into its own walk ceiling")
    except SystemExit:
        print("  fires: north_bank refuses a bank reading that runs into its ceiling")
    finally:
        globals()["BANK_WALK_N_MAX"] = saved

    if fails:
        for f in fails:
            print("SELF-TEST FAIL: %s" % f)
        return 1
    print("SELF-TEST PASS — the clearance rule refuses every tier, its two exemptions "
          "are the ones holding the committed line up, and the east end is a crossing "
          "of two committed records (%d cases)" % cases)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    path, st, is_water = derive()
    doc = json.loads(STREETS.read_text())
    street = next(s for s in doc["streets"] if s["id"] == "north_water")

    if args.gate:
        committed = [[float(e), float(n)] for e, n in street["path_local_enu_m"]]
        if committed != [[float(e), float(n)] for e, n in path]:
            print("north_water's committed line is not the one this tool derives:")
            print("  committed %s" % committed)
            print("  derived   %s" % path)
            return 1
        # ONE bend may stand in water and exactly one: the crossing's, at the deck's
        # midpoint. Every other wet bend is the fault T-0226 found -- three of the old
        # line's six bends stood in the river and the roadway simply vanished.
        w_end, e_end, n_deck = deck()
        wet = [p for p in committed if is_water(*p)]
        expect = [round(0.5 * (w_end + e_end), 1), round(n_deck, 1)]
        if wet != [expect]:
            print("north_water's bends in water are %s; the only one allowed is the "
                  "crossing's, at %s" % (wet, expect))
            return 1
        # T-0372's two-tier clearance rule. The open reach owes the half module less
        # the fit's give; the terminus and the crossing's approaches owe END_FLOOR_M,
        # because a street that ends at a fork and crosses on a deck meets the water at
        # both on purpose. See the module docstring, THE TWO ENDS ARE EXEMPT.
        breaches = clearance_gate(path, is_water)
        if breaches:
            print("north_water's drawn centreline is closer to water than its own rule "
                  "allows, at %d probe(s):" % len(breaches))
            for e, n, d, floor, tier in breaches[:8]:
                print("  E %+.1f N %.1f  %.2f m from water, %s owes %.1f m"
                      % (e, n, d, tier, floor))
            return 1
        print("north_water: derived line committed, %d bends, one in water and it is "
              "%s's deck midpoint" % (len(committed), CROSSING))
        print("  clearance: the open reach clears %.1f m, and the two ends %.1f m -- "
              "the terminus at the fork and the crossing's approaches (T-0372)"
              % (CLEARANCE_FLOOR_M, END_FLOOR_M))
        return 0

    report(path, st, is_water)
    if args.write:
        # A surgical replacement, not a re-dump: the file is hand-formatted with
        # compact inline coordinate arrays and re-serialising it would rewrite every
        # street to make one line move.
        text = STREETS.read_text()
        anchor = '"id": "north_water"'
        i = text.index(anchor)
        key = text.index('"path_local_enu_m": [', i)
        end = text.index("\n", key)
        literal = "[" + ", ".join("[%g, %g]" % (e, n) for e, n in path) + "]"
        text = text[:key] + '"path_local_enu_m": ' + literal + "," + text[end:]
        STREETS.write_text(text)
        print("  written to %s" % STREETS.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
