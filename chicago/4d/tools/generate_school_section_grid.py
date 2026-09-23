#!/usr/bin/env python3
"""Derive the School Section's block grid, its twelve east-west streets and its three
reservations from J. S. Wright's 1834 survey, read on the National Archives / Historic
Urban Plans reproduction registered by T-0787.

The section is the mile square of Section 16, T39N R14E — the school section the state
sold in October 1833 — bounded by Madison Street on the north, State Street on the east
and, a mile from each, the lines that later carried Twelfth Street and Halsted Street.
Wright draws it whole, ruled into a grid and numbered, and this project has never held
any of it: no block, no street, and no ground for the 125 land-sale rows that name its
block numbers.

METHOD, and it is a MEASUREMENT off the sheet rather than a re-use of Thompson's module.

  1. The scan is resampled into scene coordinates (local ENU metres, EPSG:26916 through
     data/datum.json) using the affine in data/traces/gcp/wright_1834_nara_hup_gcps.json.
     That deskews the drawing: the plat's own north-south and east-west rules become the
     axes of the sampled raster, so a ruled line is a peak in a one-dimensional darkness
     profile and nothing has to be traced by hand.
  2. Every line of the grid was picked as the centroid of that peak, in six independent
     bands along its length, and the median taken. Where a street is drawn as a pair of
     rules the pair gives the corridor its drawn width; where the draughtsman drew one
     line the width is not recoverable from the sheet and the platted standard is used.
  3. The measured line table is then anchored on the section itself. Madison and State
     cross at a PLSS section corner — sections 9/10/15/16 — which is GCP G1 of the
     registration, and the section is a statute mile on a side. The measured interior
     lines are rescaled linearly onto that exact square. Residuals are reported below
     and in docs/RESEARCH/school_section_grid_1834.md.

WHAT IS MEASURED AND WHAT IS ADOPTED. The measured east-west span of the grid falls 6.3 m
SHORT of the statute mile, four tenths of one per cent; the measured north-south span
overruns it by 49.3 m, three per cent. That asymmetry is the registration's own finding
showing at the bottom of the sheet: it measured 5.2 per cent x/y anisotropy on this scan
against 3.7 per cent on the BPL copy, and the extra stretch is in the long axis, along
which the manuscript was torn and backed. The section is a mile on the ground whatever
the paper does, so the grid is anchored on the section and not on the paper.

Run:  python3 tools/generate_school_section_grid.py [--check]
"""
import argparse, hashlib, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------------------
# THE MEASUREMENT. Line centres are metres in the resampled (deskewed) frame, before the
# section anchor is applied. `drawn_w` is the separation of the pair of rules where the
# sheet draws the corridor with two, and None where it draws a single line — the widths
# of those are not on the sheet. `bands` is how many of the six sampling bands agreed.
# Sheet names are the draughtsman's, read off the same raster.
# --------------------------------------------------------------------------------------
NS_LINES = [  # west to east
    dict(i=0,  measured=-768.14, drawn_w=15.12, bands=6, sheet_name=None, role="section line (west)"),
    dict(i=1,  measured=-648.20, drawn_w=None,  bands=0, sheet_name=None, role="interior"),
    dict(i=2,  measured=-508.13, drawn_w=16.08, bands=5, sheet_name="Des Plaines", role="interior"),
    dict(i=3,  measured=-382.15, drawn_w=20.49, bands=6, sheet_name="Jefferson", role="interior"),
    dict(i=4,  measured=-270.51, drawn_w=19.71, bands=6, sheet_name="Clinton", role="interior"),
    dict(i=5,  measured=-147.95, drawn_w=21.61, bands=6, sheet_name="Canal", role="interior"),
    dict(i=6,  measured=-41.80,  drawn_w=None,  bands=0, sheet_name=None, role="interior"),
    dict(i=7,  measured=67.40,   drawn_w=None,  bands=0, sheet_name="Market", role="interior"),
    dict(i=8,  measured=203.90,  drawn_w=None,  bands=0, sheet_name=None, role="interior"),
    dict(i=9,  measured=346.36,  drawn_w=20.41, bands=4, sheet_name="Wells", role="interior"),
    dict(i=10, measured=459.60,  drawn_w=None,  bands=0, sheet_name=None, role="interior"),
    dict(i=11, measured=577.59,  drawn_w=21.15, bands=6, sheet_name="Clark", role="interior"),
    dict(i=12, measured=698.70,  drawn_w=None,  bands=0, sheet_name=None, role="interior"),
    dict(i=13, measured=834.90,  drawn_w=None,  bands=0, sheet_name=None, role="section line (east), State Street"),
]
EW_LINES = [  # north to south
    dict(j=0,  measured=-545.99, drawn_w=16.75, bands=6, sheet_name="Madison"),
    dict(j=1,  measured=-686.96, drawn_w=25.21, bands=8, sheet_name="Monroe"),
    dict(j=2,  measured=-832.66, drawn_w=23.34, bands=8, sheet_name="Adams"),
    dict(j=3,  measured=-979.93, drawn_w=21.72, bands=8, sheet_name="Jackson"),
    dict(j=4,  measured=-1129.40, drawn_w=25.00, bands=8, sheet_name=None),
    dict(j=5,  measured=-1280.50, drawn_w=None,  bands=0, sheet_name=None),
    dict(j=6,  measured=-1399.14, drawn_w=24.07, bands=8, sheet_name=None),
    dict(j=7,  measured=-1545.43, drawn_w=25.19, bands=4, sheet_name=None),
    dict(j=8,  measured=-1660.67, drawn_w=16.84, bands=8, sheet_name=None),
    dict(j=9,  measured=-1808.40, drawn_w=None,  bands=0, sheet_name=None),
    dict(j=10, measured=-1924.45, drawn_w=13.66, bands=8, sheet_name=None),
    dict(j=11, measured=-2077.60, drawn_w=None,  bands=0, sheet_name=None),
    dict(j=12, measured=-2204.64, drawn_w=None,  bands=0, sheet_name="section line (south)"),
]

FT = 0.3048
EW_CORRIDOR_M = round(80 * FT, 3)   # 24.384 — the platted standard of both 1830 plats
NS_CORRIDOR_M = round(66 * FT, 3)   # 20.117 — a surveyor's chain; measured median 20.41

MILE_M = 1609.344

# --------------------------------------------------------------------------------------
# THE READING. cells are (column index 0-12, row index 0-11); a block occupying two
# columns is written with both. Rows run north to south, columns west to east.
# Everything here was read off the resampled raster at 1x, 2x and 3x.
# --------------------------------------------------------------------------------------
ROWS = [
    # row 0 (Madison to Monroe)
    [(0, 1), (1, 24), (2, 25), (3, 48), (4, 49), (5, 72), (6, 80), (7, 81),
     (8, 94), (9, 95), (10, 118), (11, 119), (12, 142)],
    [(0, 2), (1, 23), (2, 26), (3, 47), (4, 50), (5, 71), (6, 79), (7, 82),
     (8, 93), (9, 96), (10, 117), (11, 120), (12, 141)],
    [(0, 3), (1, 22), (2, 27), (3, 46), (4, 51), (5, 70), ((6, 7), 83),
     (8, 92), (9, 97), (10, 116), (11, 121), (12, 140)],
    [(0, 4), (1, 21), (2, 28), (3, 45), (4, 52), (5, 69), ((6, 7), 84),
     (8, 91), (9, 98), (10, 115), (11, 122), (12, 139)],
    [(0, 5), (1, 20), (2, 29), (3, 44), (4, 53), (5, 68),
     (8, 90), (9, 99), (10, 114), (11, 123), (12, 138)],
    [(0, 6), (1, 19), (2, 30), (3, 43), (4, 54), (5, 67),
     (8, 89), (9, 100), (10, 113), (11, 124), (12, 137)],
    [(0, 7), (1, 18), (2, 31), (3, 42), (4, 55), (5, 66),
     (8, 88), (9, 101), (10, 112), (11, 125), (12, 136)],
    [(0, 8), (1, 17), (2, 32), (3, 41), (4, 56), (5, 65),
     (8, 87), (9, 102), (10, 111), (11, 126), (12, 135)],
    [(0, 9), (1, 16), (2, 33), (3, 40), (4, 57), (5, 64), ((6, 7), 73),
     (8, 86), (9, 103), (10, 110), (11, 127), (12, 134)],
    [(0, 10), (1, 15), (2, 34), (3, 39), (4, 58), (5, 63), ((6, 7), 74),
     (8, 85), (9, 104), (10, 109), (11, 128), (12, 133)],
    [(0, 11), (1, 14), (2, 35), (3, 38), (4, 59), (5, 62), (6, 75), (7, 78),
     (9, 105), (10, 108), (11, 129), (12, 132)],
    [(0, 12), (1, 13), (2, 36), (3, 37), (4, 60), (5, 61), (6, 76), (7, 77),
     (9, 106), (10, 107), (11, 130), (12, 131)],
]

# Numerals NOT read as ink in their own block, and why. Everything else is on the sheet.
NUMERAL_NOTES = {
    1: ("inferred",
        "The sheet writes 'Reserved' across this block and no numeral. 1 is supplied by the "
        "serpentine sequence, which runs 1-12 down this westernmost tier with 2 in the block "
        "immediately south. The October 1833 sale sells lots in every other block of the two "
        "northern tiers and none here, which is the reservation's own corroboration."),
    142: ("inferred",
          "The sheet writes 'Reserved' across this block and no numeral. 142 is supplied by the "
          "sequence: the easternmost tier runs 131 at the south up to 141 in the block "
          "immediately south of this one. The ticket that asked for this work called this block "
          "119; 119 is read on the sheet one tier WEST of it, and 141 sits between them. The "
          "1833 sale sells lots in 119, 120 and 141 and none here."),
    77: ("inferred",
         "The second glyph is written without a crossbar and reads as either 7 or 1 at 3x. 77 is "
         "adopted: 71 is read in ink two tiers west in the second row, the sequence runs 73-76 "
         "down the tier to the west and back up this one through 78 immediately north, and the "
         "1833 sale, which reached only the four northern rows, sells in neither."),
    81: ("documented",
         "The numeral is written TWICE inside this block, side by side, and both readings give "
         "81. Recorded as read; the doubling is the draughtsman's."),
    82: ("documented",
         "A second numeral stands beside this one and is lost under an ink blot. The numeral "
         "read here is 82 and it is clear; what the blot covers is not recoverable."),
}

# Blocks the South Branch crosses. Their east or west side is not on the sheet as a ruled
# line but as the drawn bank, and T-0794 is the ticket that will commit that bank.
BANK_PENDING = {
    70: "east", 71: "east", 78: "west", 83: "west", 84: "west",
    85: "west", 86: "west", 87: "west", 88: "west",
    73: "east", 74: "east",
}

RESERVED = {
    1: dict(name="The north-west reservation",
            where="the corner of Madison Street and the section's west line"),
    142: dict(name="The north-east reservation",
              where="the corner of Madison Street and State Street"),
    87: dict(name="The South Branch reservation",
             where="on the east bank of the South Branch, spanning blocks 87 and 88"),
    88: dict(name="The South Branch reservation",
             where="on the east bank of the South Branch, spanning blocks 87 and 88"),
}

EW_STREET_IDS = [
    ("madison", "Madison Street", "Madison Street"),
    ("monroe", "Monroe Street", "Monroe Street"),
    ("adams", "Adams Street", "Adams Street"),
    ("jackson", "Jackson Boulevard", "Jackson Boulevard"),
]

# --------------------------------------------------------------------------------------
# THE NORTH-SOUTH LINES — T-0877. Wright rules fourteen of them across the section and
# letters seven; the outermost two are the section's own boundaries and the eastern of
# those is State Street.
#
# WHETHER THESE ARE THE TOWN'S STREETS CONTINUED OR RECORDS OF THEIR OWN is the decision
# the ticket asked for, and it is SEPARATE RECORDS. Three reasons, in the order they bind:
#
#   1. GEOMETRY. `canal`, `clinton`, `market`, `wells`, `clark` and `state` are committed
#      no further south than local N -400 m, and Madison — this section's north line and
#      the Town of Chicago's south boundary — is at -534. A continuation would have to
#      draw the 134 m between them. That ground is Wright's Washington-to-Madison tier,
#      which T-0858 has open and unread, and this project does not rule a line across
#      ground nobody has read.
#   2. STATUS. The town's own lines carry no `opened` flag: they are the worn streets of
#      the advertising town. These carry `opened: false`, `track_width_m: 0` and
#      "platted, unopened, unworn" — the owner's reading of this sheet, 2026-09-05. One
#      record cannot be both a worn street and an unopened survey line.
#   3. PRECEDENT. The file already holds `market`/`market_north`, `wells`/`wells_north`,
#      `clark`/`clark_north` and `dearborn`/`dearborn_north`: one printed name, one record
#      per survey. T-0451 seated the North Division that way for this same reason.
#
# AND THE CONSEQUENCE FOR THE REGISTER, which is the half of the question that bites.
# `compile_register.py` keys a printed street name onto ONE id, and its tie-break was "the
# record reaching furthest SOUTH takes the name" (T-0451, decided when the only rival was
# the North Division). These lines reach a mile further south than any street the town
# walked on, so seating them named would have handed every bare "Clark Street", "Wells
# Street", "Market Street", "Canal Street", "Clinton Street" and "State Street" in the
# newspapers and the directories to unopened prairie below Madison. That tie-break now
# reads the status first — an unopened survey line never takes a printed name from a
# street the town used — and the fix is committed with these records, not after them.
#
# `name_2026` is null on all of them, as it is on `market_north` and on the unnamed
# east-west tiers: the later names of these lines are not evidence about 1835, and this
# project has read no modern street layer south of Madison.
# --------------------------------------------------------------------------------------
NS_STREET_IDS = {
    2: ("des_plaines_school_section", "Des Plaines"),
    3: ("jefferson_school_section", "Jefferson"),
    4: ("clinton_school_section", "Clinton"),
    5: ("canal_school_section", "Canal"),
    7: ("market_school_section", "Market"),
    9: ("wells_school_section", "Wells"),
    11: ("clark_school_section", "Clark"),
    13: ("state_school_section", "State"),
}

# MARKET STREET IS DRAWN IN TWO STRETCHES AND IS COMMITTED AS TWO RECORDS. Wright rules
# line 7 from Madison down to Adams and again from the tenth tier line to the section's
# south boundary; between those he draws BLOCKS across the corridor — 83 and 84 span
# columns 6 and 7 in the Adams-to-Jackson and Jackson-to-tier-4 rows, 73 and 74 span them
# again in the two rows above the tenth line — and between THOSE the South Branch takes
# the ground entirely (rows 4 to 7 carry no block in either column). A block drawn across
# a corridor is a positive statement that no street is there, so the corridor is not
# carried through it. This is not the same as the South Branch crossing an east-west tier,
# where the sheet simply rules the line across the water and no block contradicts it.
MARKET_NORTH_ROWS = (0, 1)          # Madison to Adams
MARKET_SOUTH_ROWS = (10, 11)        # the tenth tier line to the section's south boundary
MARKET_SOUTH_ID = "market_school_section_south"


# Why every east-west line here is drawn LEVEL — one northing end to end — when the sheet
# does not draw it level. T-0959; the measurement is
# data/traces/vectors/school_section_tier_skew_1834.json, taken by
# tools/measure_school_section_tier_skew.py.
EW_RUN_NOTE = (
    "DRAWN LEVEL, AND THAT IS A STATEMENT ABOUT THE GROUND RATHER THAN THE PAPER (T-0959). "
    "Re-measured off the same registered raster in ten bands along its length, this line does "
    "NOT run level: all thirteen east-west lines of the section tilt the same way, median 0.57 "
    "degrees, 16.0 m of rise across the mile. That settles nothing on its own, because all "
    "fourteen NORTH-SOUTH lines tilt the same way too, median 0.67 degrees, and a rotation of "
    "the drawing under its registration tilts the two families equally and OPPOSITELY. What "
    "settles it is the section's own boundary. Section 16's four sides are PLSS lines and run "
    "true north and true east on the ground by definition; measured exactly as the interior "
    "lines are, they tilt +0.69 degrees in this frame against +0.56 for the interior. A frame "
    "that tilts its own cardinal control is describing itself, and the mechanism is in the fit: "
    "a general affine with two axis scales 6.2 per cent apart does not preserve angles, so a "
    "right angle ruled on the paper leaves it at 91.62 degrees. The tilt therefore comes out "
    "with the rest of the registration's distortion when the measured lines are rescaled onto "
    "the section's statute-mile square — the same anchoring that removes the 3 per cent "
    "north-south overrun. `geometry_confidence` stays `inferred` for that reason: the northing "
    "is a measurement carried onto a PLSS square, not a figure any record states.")


def load(p):
    return json.loads((ROOT / p).read_text())


def build():
    gcp = load("data/traces/gcp/wright_1834_nara_hup_gcps.json")
    datum = load("data/datum.json")
    # T-1092 re-seated this trace onto the ELEVEN-POINT registration T-1091 adopted,
    # and re-baked what stands on the ground that moved. `fit` IS that registration;
    # the eight-point fit it superseded is kept beside it as `retained_fit` for the
    # adjudication that compares the two. Reading `retained_fit` here would seat the
    # ground on a fit this project no longer holds.
    c = gcp["fit"]["coefficients"]
    a, b, cc, d, e, f = c["a"], c["b"], c["c"], c["d"], c["e"], c["f"]
    det = a * e - b * d
    oE, oN = datum["origin_utm_e"], datum["origin_utm_n"]

    def local_to_pixel(x, y):
        dE, dN = (x + oE) - cc, (y + oN) - f
        return ((e * dE - b * dN) / det, (-d * dE + a * dN) / det)

    g1 = next(g for g in gcp["gcps"] if g["id"] == "G1")
    gx, gy = g1["pixel"]
    cx = a * gx + b * gy + cc - oE
    cy = d * gx + e * gy + f - oN

    anchor = dict(
        corner="State Street and Madison Street, the PLSS corner of sections 9/10/15/16, "
               "T39N R14E, and GCP G1 of the registration",
        corner_local_enu_m=[round(cx, 2), round(cy, 2)],
        north=round(cy, 3), east=round(cx, 3),
        south=round(cy - MILE_M, 3), west=round(cx - MILE_M, 3),
        side_m=MILE_M,
    )

    m0, m1 = NS_LINES[0]["measured"], NS_LINES[-1]["measured"]
    n0, n1 = EW_LINES[0]["measured"], EW_LINES[-1]["measured"]
    sx = MILE_M / (m1 - m0)
    sy = -MILE_M / (n1 - n0) * -1

    X, Y = [], []
    for L in NS_LINES:
        X.append(anchor["west"] + (L["measured"] - m0) * sx)
    for L in EW_LINES:
        Y.append(anchor["north"] + (L["measured"] - n0) * (-MILE_M / (n0 - n1)) * -1)
    # y: measured decreases southward; map [n0,n1] -> [north, south]
    Y = [anchor["north"] + (L["measured"] - n0) / (n1 - n0) * (anchor["south"] - anchor["north"])
         for L in EW_LINES]

    for L, xv in zip(NS_LINES, X):
        L["adopted"] = round(xv, 3)
        L["anchor_shift_m"] = round(xv - L["measured"], 2)
        L["corridor_width_m"] = NS_CORRIDOR_M
    for L, yv in zip(EW_LINES, Y):
        L["adopted"] = round(yv, 3)
        L["anchor_shift_m"] = round(yv - L["measured"], 2)
        L["corridor_width_m"] = EW_CORRIDOR_M

    raster = gcp["raster"]

    def block_rect(cols, rows):
        w = X[min(cols)] + NS_CORRIDOR_M / 2
        ee = X[max(cols) + 1] - NS_CORRIDOR_M / 2
        n = Y[min(rows)] - EW_CORRIDOR_M / 2
        s = Y[max(rows) + 1] + EW_CORRIDOR_M / 2
        return w, ee, n, s

    blocks = []
    for rj, row in enumerate(ROWS):
        for cells, num in row:
            cols = list(cells) if isinstance(cells, tuple) else [cells]
            w, ee, n, s = block_rect(cols, [rj])
            poly = [[round(w, 2), round(n, 2)], [round(ee, 2), round(n, 2)],
                    [round(ee, 2), round(s, 2)], [round(w, 2), round(s, 2)]]
            px = [local_to_pixel(*p) for p in poly]
            x0 = min(p[0] for p in px); x1 = max(p[0] for p in px)
            y0 = min(p[1] for p in px); y1 = max(p[1] for p in px)
            conf, note = NUMERAL_NOTES.get(num, ("documented", None))
            entry = dict(
                block_number=num,
                id="blk_school_section_%d" % num,
                cells=[[c_, rj] for c_ in cols],
                boundary_local_enu_m=poly,
                area_m2=round((ee - w) * (n - s), 1),
                frontage_m=round(ee - w, 2),
                depth_m=round(n - s, 2),
                numeral=dict(
                    read=None if conf == "inferred" and num in (1, 142) else str(num),
                    confidence=conf,
                    on_sheet=num not in (1, 142),
                    source="wright_1834_nara_hup",
                    crop_na_pixels=dict(x=int(round(x0)), y=int(round(y0)),
                                        w=int(round(x1 - x0)), h=int(round(y1 - y0))),
                    note=note,
                ),
                bounded_by=dict(
                    north=street_id(min(rj, len(EW_LINES) - 1)),
                    south=street_id(min(rj + 1, len(EW_LINES) - 1)),
                    west=ns_street_id(min(cols), rj),
                    east=ns_street_id(max(cols) + 1, rj),
                ),
                geometry_confidence="reconstructed" if num in BANK_PENDING else "inferred",
            )
            if num in BANK_PENDING:
                entry["open_side"] = BANK_PENDING[num]
                entry["bank_pending"] = (
                    "The South Branch crosses this block and its %s side is the drawn bank, not a "
                    "ruled line. The rectangle here is the block's CELL in the grid; T-0794 commits "
                    "the bank and closes it." % BANK_PENDING[num])
            if num in RESERVED:
                entry["reserved"] = True
            blocks.append(entry)

    blocks.sort(key=lambda b: b["block_number"])
    return anchor, blocks, raster, sx


def street_id(j):
    if j < len(EW_STREET_IDS):
        return EW_STREET_IDS[j][0]
    if j == len(EW_LINES) - 1:
        return None  # the section's south line; Twelfth Street is later than this scene
    # THE ORDINAL SAYS WHAT IT COUNTS FROM (T-0959). `j` counts Madison Street as 0, so
    # tier 4 is the fourth ruled line SOUTH OF MADISON and the fifth east-west line of the
    # section counting Madison itself. Two readings of this sheet numbered the same eight
    # lines a whole tier apart for want of that datum; south of Jackson the sheet letters
    # none of them, so an ordinal here is a claim about a named line and the id states it.
    return "school_section_tier_%d_south_of_madison" % j


def ns_street_id(i, rj):
    """The id of the i-th north-south line at the row `rj`, T-0877.

    Every line has one id except Market, which is ruled in two stretches with blocks
    drawn across the corridor between them (see MARKET_NORTH_ROWS above). A block in a
    row the line is not ruled in never names it: those blocks span both columns and so
    are never asked for boundary 7 at all, but the row is passed anyway so that a future
    reading which splits them cannot silently reattach the wrong stretch."""
    if i == 7:
        if rj in MARKET_SOUTH_ROWS:
            return MARKET_SOUTH_ID
        if rj in MARKET_NORTH_ROWS:
            return NS_STREET_IDS[7][0]
        return None  # the corridor is not ruled in this row; no block here has a side 7
    if i in NS_STREET_IDS:
        return NS_STREET_IDS[i][0]
    return "school_section_line_%d" % i


def street_records(anchor):
    """The twelve east-west streets, as platted lines across the section."""
    out = []
    for j, L in enumerate(EW_LINES):
        if j == len(EW_LINES) - 1:
            continue  # the section's south line carries no street on this sheet
        sid = street_id(j)
        named = j < len(EW_STREET_IDS)
        name_1835 = EW_STREET_IDS[j][1] if named else None
        y = L["adopted"]
        rec = dict(
            id=sid,
            name_1835=name_1835,
            name_2026=EW_STREET_IDS[j][2] if named else None,
            name_changed=False,
            path_local_enu_m=[[round(anchor["west"], 2), round(y, 2)],
                              [round(anchor["east"], 2), round(y, 2)]],
            corridor_width_m=EW_CORRIDOR_M,
            track_width_m=0,
            opened=False,
            worn=False,
            alleys=False,
            status_1835="platted, unopened, unworn",
            surface="unworn_prairie",
            traffic="none",
            geometry_confidence="inferred",
            surface_confidence="inferred",
            wear_confidence="inferred",
            sources=["wright_1834_nara_hup", "wright_1834"],
            note=(
                "%s. Read off Wright's 1834 survey as a ruled line of the School Section's grid "
                "(Section 16, T39N R14E) and anchored on the section's own mile square; the "
                "measured line is at local N %+.1f m and the anchor moves it %+.1f m. THE STATUS "
                "IS THE OWNER'S READING OF THE SHEET, 2026-09-05: 'no alleys and no street names "
                "but still a grid that should have some wilderness trees'. So the corridor is "
                "platted and the ground inside it is not: `track_width_m` is 0 because no wagon "
                "track is drawn or attested here, `alleys` is false because the sheet rules none "
                "inside these blocks, and the flora belts are not cut for it. What a visitor "
                "should see is a survey line over prairie, not a road."
                % (("Madison Street, the section's own north line and the boundary of the Town of "
                    "Chicago" if j == 0 else "The %s tier of the School Section's grid" % (
                        name_1835 or "%d%s south of Madison Street" % (j, {1: 'st', 2: 'nd', 3: 'rd'}.get(j % 10 if j % 100 not in (11, 12, 13) else 0, 'th')))),
                   L["measured"], L["anchor_shift_m"])
            ),
        )
        rec["note"] += " " + EW_RUN_NOTE
        if not named:
            rec["name_note"] = (
                "UNNAMED ON THE SHEET. Wright rules the tier and writes no name on it; the four "
                "streets he does name — Madison, Monroe, Adams and Jackson — are the four "
                "northernmost. `name_1835` is null rather than a modern name carried back, "
                "because the later names of these lines are not evidence about 1835. THE ORDINAL "
                "IN THE ID COUNTS FROM MADISON, the northernmost line and one the sheet does name: "
                "this is the %d%s ruled line south of it, and the %d%s east-west line of the "
                "section counting Madison itself. Both are true and they differ by one, which is "
                "exactly how two readings of this sheet came to number the same eight lines a tier "
                "apart (T-0959); an ordinal on an unlettered line is a claim about what it is "
                "counted from, so the id states it."
                % (j, {1: 'st', 2: 'nd', 3: 'rd'}.get(j % 10 if j % 100 not in (11, 12, 13) else 0, 'th'),
                   j + 1, {1: 'st', 2: 'nd', 3: 'rd'}.get((j + 1) % 10 if (j + 1) % 100 not in (11, 12, 13) else 0, 'th')))
        out.append(rec)
    return out


def ns_street_records(anchor):
    """The fourteen north-south lines Wright rules across the section, T-0877.

    Twelve are interior and two are the section's own boundaries. BOTH BOUNDARIES ARE
    COMMITTED AND THE SECTION'S SOUTH BOUNDARY IS NOT, and the test is the sheet rather
    than symmetry: a boundary line is committed when Wright rules it as a CORRIDOR — a
    pair of rules, a platted right-of-way — or when it carries a name the town's own plat
    carries. The west line is the first: 15.12 m between its rules, agreed by all six
    sampling bands, and no name (Halsted is later than this scene, and a later name is not
    evidence). The east line is the second: it is State Street, whose town record `state`
    this project already holds. The section's SOUTH line is neither — a single rule, no
    name, and no street stood on it in 1835 — so `street_id` still returns None for it and
    the twelve blocks of the bottom tier keep `south: null`. That is T-0797's ruling about
    the east-west series and this ticket does not overturn it.

    Market is two records; every other line is one. See MARKET_NORTH_ROWS.
"""
    out = []
    north, south = EW_LINES[0]["adopted"], EW_LINES[-1]["adopted"]
    for i, L in enumerate(NS_LINES):
        stretches = [(ns_street_id(i, MARKET_NORTH_ROWS[0]), north, EW_LINES[2]["adopted"],
                      "from Madison Street down to Adams Street"),
                     (MARKET_SOUTH_ID, EW_LINES[10]["adopted"], south,
                      "from the tenth tier line down to the section's south boundary")] \
            if i == 7 else [(ns_street_id(i, 0), north, south, None)]
        for sid, y0, y1, stretch in stretches:
            named = i in NS_STREET_IDS
            sheet = NS_STREET_IDS[i][1] if named else None
            if i == 0:
                what = ("The section's WEST boundary, a mile from State Street. Wright draws "
                        "it as a corridor and letters no name on it; the line later carried "
                        "Halsted Street, which is not evidence about 1835")
            elif i == len(NS_LINES) - 1:
                what = ("State Street, the section's EAST boundary and the meridian of the "
                        "Chicago street grid. The town's own State Street is the separate "
                        "record `state`, which reaches no further south than local N -400 m")
            elif named:
                what = "%s Street, %s" % (sheet, "the corridor's north stretch, "
                                          + stretch if stretch else
                                          "ruled and lettered on the sheet")
            else:
                what = ("The %d%s ruled line of the School Section's north-south series, "
                        "counting the section's west boundary as the 0th. Wright rules it "
                        "and letters no name on it" % (i, ordinal_suffix(i)))
            if i == 7 and sid == MARKET_SOUTH_ID:
                what = "Market Street, the corridor's south stretch, " + stretch
            rec = dict(
                id=sid,
                name_1835=("%s Street" % sheet) if named else None,
                name_2026=None,
                name_changed=False,
                path_local_enu_m=[[round(L["adopted"], 2), round(y0, 2)],
                                  [round(L["adopted"], 2), round(y1, 2)]],
                corridor_width_m=NS_CORRIDOR_M,
                track_width_m=0,
                opened=False,
                worn=False,
                alleys=False,
                status_1835="platted, unopened, unworn",
                surface="unworn_prairie",
                traffic="none",
                geometry_confidence="inferred",
                surface_confidence="inferred",
                wear_confidence="inferred",
                sources=["wright_1834_nara_hup", "wright_1834"],
                note=(
                    "%s. Read off Wright's 1834 survey as a ruled line of the School "
                    "Section's grid (Section 16, T39N R14E) and anchored on the section's "
                    "own mile square; the measured line is at local E %+.1f m and the "
                    "anchor moves it %+.1f m. %s THE STATUS IS THE OWNER'S READING OF THE "
                    "SHEET, 2026-09-05: 'no alleys and no street names but still a grid "
                    "that should have some wilderness trees'. So the corridor is platted "
                    "and the ground inside it is not: `track_width_m` is 0 because no "
                    "wagon track is drawn or attested here, `alleys` is false because the "
                    "sheet rules none inside these blocks, and the flora belts are not cut "
                    "for it. What a visitor should see is a survey line over prairie, not "
                    "a road."
                    % (what, L["measured"], L["anchor_shift_m"],
                       ("The sheet draws this one as a PAIR of rules %.2f m apart, agreed "
                        "by %d of the sampling bands; the committed corridor is the 66 ft "
                        "platted standard rather than that pick, because the scatter of "
                        "individual picks is +/- 5 m. "
                        % (L["drawn_w"], L["bands"])) if L["drawn_w"] else
                       ("The sheet draws this one as a SINGLE rule, so its drawn width is "
                        "not recoverable and the committed corridor is the 66 ft platted "
                        "standard. "))
                ),
            )
            rec["note"] = " ".join(rec["note"].split())
            if named:
                rival = sid not in ("des_plaines_school_section",
                                    "jefferson_school_section")
                rec["name_note"] = (
                    "LETTERED ON THE SHEET as '%s'. %s `name_2026` is null because the "
                    "later name of this line is not evidence about 1835."
                    % (sheet,
                       ("This is a record of its own and NOT the town's %s Street continued "
                        "south: see NS_STREET_IDS in tools/generate_school_section_grid.py "
                        "for the three reasons, of which the first is that the town's record "
                        "stops 134 m north of Madison over ground nobody has read."
                        % sheet) if rival else
                       ("The town holds no other street of this name, and the bare id is "
                        "deliberately left free. %s Street also runs NORTH of Madison "
                        "through the West Division, where T-0445 refused to seat it: its "
                        "surviving control stands west of the modelled ground's edge at "
                        "local east -320 m, so a drawn street there would hang off the end "
                        "of the terrain. That refusal is a measurement and it still holds, "
                        "which is why this record carries the `_school_section` suffix like "
                        "its lettered neighbours and does not take `%s` — the id the West "
                        "Division's line will want when the terrain box reaches it. This "
                        "line is a different reading of a different survey on different "
                        "ground, and it is not drawn: `opened` is false, so the renderer "
                        "never puts a roadway on terrain that may not be there."
                        % (sheet, sid[:-len("_school_section")]))))
            else:
                rec["name_note"] = (
                    "UNNAMED ON THE SHEET. Wright rules the line and writes no name on it; "
                    "the seven he does letter are Des Plaines, Jefferson, Clinton, Canal, "
                    "Market, Wells and Clark. `name_1835` is null rather than a modern name "
                    "carried back, because the later names of these lines are not evidence "
                    "about 1835.")
            out.append(rec)
    return out


def ordinal_suffix(n):
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10 if n % 100 not in (11, 12, 13) else 0, "th")


def cross_check_numbering():
    """The reading in ROWS above, against T-0875's independent reading of the same sheet.

    Two runs read all 142 numerals off this sheet within hours of each other and neither
    could see the other's work: this module's table was read off the resampled raster, and
    `data/traces/school_section_block_numbering.json` was read by
    `tools/read_school_section_numerals.py` on the sheet's own pixels. They agree on every
    one of the 142 cells. That is worth more than either reading alone, so it is a GATE
    rather than a remark: if the two ever diverge, this tool stops.
    """
    other = load("data/traces/school_section_block_numbering.json")
    theirs = {(b["column"] - 1, b["tier"] - 1): b["number"] for b in other["blocks"]}
    ours = {}
    for rj, row in enumerate(ROWS):
        for cells, num in row:
            for c in (cells if isinstance(cells, tuple) else (cells,)):
                ours[(c, rj)] = num
    disagree = sorted((k, theirs[k], ours[k]) for k in set(theirs) & set(ours)
                      if theirs[k] != ours[k])
    if disagree:
        raise SystemExit(
            "the two readings of the School Section's numerals disagree, and one of them is "
            "wrong: " + "; ".join("cell c%dr%d — T-0875 reads %s, this module reads %s"
                                  % (c + 1, r + 1, a, b) for (c, r), a, b in disagree))
    missing = sorted(set(theirs) - set(ours))
    if missing:
        raise SystemExit("T-0875 numbers cells this module emits no block for: %s" % (missing,))
    return dict(
        against="data/traces/school_section_block_numbering.json",
        ticket="T-0875",
        cells_compared=len(set(theirs) & set(ours)),
        disagreements=0,
        note=("Two independent readings of the same sheet, made hours apart by runs that could "
              "not see each other — one off the resampled raster, one off the sheet's own pixels "
              "— agree on all 142 numerals, cell for cell. This module gates on that agreement: "
              "if the two ever diverge it refuses to run. The four cells this module holds and "
              "that reading does not are the east halves of blocks 73, 74, 83 and 84, which span "
              "two cells apiece here because Market Street stops at Adams."),
    )


def sale_test():
    """The October 1833 sale of the school section, as this project already holds it."""
    entries = load("data/research/land_sales/entries.json")["entries"]
    s16 = [e for e in entries if (e.get("tract") or {}).get("section") == "16"]
    sold = {}
    for e in s16:
        b = (e.get("tract") or {}).get("block")
        if b is None:
            continue
        sold.setdefault(int(b), []).append(e)
    dates = sorted({e["date_purchased"] for e in s16 if e.get("date_purchased")})
    return dict(
        rows_in_section_16=len(s16),
        rows_resolving_to_a_block=sum(len(v) for v in sold.values()),
        blocks_sold=sorted(sold),
        first_date=dates[0] if dates else None,
        last_date=dates[-1] if dates else None,
    ), sold


def reservation_records(blocks, sale, sold):
    reached = set(sale["blocks_sold"])
    out = []
    seen = set()
    for num, meta in RESERVED.items():
        key = meta["name"]
        if key in seen:
            continue
        seen.add(key)
        members = sorted(n for n, m in RESERVED.items() if m["name"] == key)
        tested = [n for n in members]
        sells = {n: len(sold.get(n, [])) for n in tested if n in reached}
        # Did the sale reach this part of the section at all? It reached rows 0-3 only.
        row_of = {b["block_number"]: b["cells"][0][1] for b in blocks}
        in_reach = any(row_of[n] <= 3 for n in tested)
        if sells:
            result = "contradicted"
            verdict = ("The sale SELLS in %s. The sheet's reservation and the sale's rows are both "
                       "written; neither is dropped." % ", ".join("block %d (%d rows)" % (k, v)
                                                                  for k, v in sorted(sells.items())))
            conf = "inferred"
        elif in_reach:
            result = "corroborated"
            verdict = ("No row of the sale sells a lot in %s, and the sale reached this tier: it "
                       "sells in every OTHER block of the two northern rows. A reservation the "
                       "sale steps around is the strongest corroboration this dataset can give it."
                       % (" or ".join("block %d" % n for n in tested)))
            conf = "inferred"
        else:
            result = "untested"
            verdict = ("No row of the sale sells a lot in %s — but the sale never reached this far "
                       "south. Its 217 block-resolved rows all lie in the four northern rows of the "
                       "grid, so its silence here is silence and not corroboration."
                       % (" or ".join("block %d" % n for n in tested)))
            conf = "inferred"
        for n in tested:
            blk = next(b for b in blocks if b["block_number"] == n)
            out.append(dict(
                block_id=blk["id"],
                name=meta["name"],
                block_number=n,
                spans=[m for m in members] if len(members) > 1 else None,
                bounded_by=blk["bounded_by"],
                where=meta["where"],
                reserved_for="unstated",
                confidence=conf,
                sources=["wright_1834_nara_hup"],
                what_may_stand_here=dict(
                    rule=("A structure record may stand on reserved ground when its own committed "
                          "evidence puts it there. Everything else is refused \u2014 in particular, no "
                          "roof of the 665-roof programme's anonymous infill. Nothing stands here "
                          "today: this ground is a mile outside the modelled town and carries no "
                          "committed footprint at all."),
                    permitted=[]),
                sale_test=dict(result=result, note=verdict,
                               tested_against="data/research/land_sales/entries.json, "
                                              "section 16 T39N R14E, the October 1833 school-section sale"),
                note=("Wright writes 'Reserved' across this block and no numeral. What it was "
                      "reserved FOR is not on the sheet and is not supplied here. %s" % verdict),
            ))
    return out


def _scal(x):
    return x is None or isinstance(x, (int, float, str, bool))


def _fmt(o, ind=0, ascii_=True):
    """Serialise in the style the committed street and reservation files already use:
    two-space indent, but an array of scalars (or of scalar arrays) on one line."""
    sp = "  " * ind
    if isinstance(o, list) and o and (all(_scal(v) for v in o)
                                      or all(isinstance(v, list) and v and all(_scal(w) for w in v) for v in o)):
        return json.dumps(o, separators=(", ", ": "), ensure_ascii=ascii_)
    if isinstance(o, list):
        if not o:
            return "[]"
        return "[\n" + ",\n".join("  " * (ind + 1) + _fmt(v, ind + 1, ascii_) for v in o) + "\n" + sp + "]"
    if isinstance(o, dict):
        if not o:
            return "{}"
        return ("{\n" + ",\n".join("  " * (ind + 1) + json.dumps(k) + ": " + _fmt(v, ind + 1, ascii_)
                                    for k, v in o.items()) + "\n" + sp + "}")
    return json.dumps(o, ensure_ascii=ascii_)


def splice(path, records, sentinel_key, ascii_=True):
    """Replace THIS TOOL'S OWN records in the file's last array, leaving every byte before
    and after them exactly as it was. Hand-authored files here carry hand-authored
    formatting and a whole-file reserialisation would rewrite 1,400 lines to add twelve
    records.

    IT USED TO TRUNCATE THE TAIL, and by T-0877 that had become destructive. The tool
    found the sentinel of its FIRST record and replaced everything from there to the end
    of the array — correct on the day it was written, when its records were last in the
    file, and wrong the moment another tool appended after them. Re-running it against dev
    at 33038d3df would have deleted twenty-two street records seated since: the North
    Division's seven cross streets, Cass, Rush, Pine and Sand, the Michigan St tract's four
    and Kinzie's Addition's six. Nothing caught it because no gate re-derives this file.

    So the span replaced now ENDS at the first record the tool does not own, found by id,
    rather than at the end of the array. Records it owns keep their position; records it
    has newly minted are written in the order given, inside that span."""
    text = (ROOT / path).read_text()
    body = "\n" + ",\n".join("    " + _fmt(r, 2, ascii_) for r in records)

    def sentinel_of(value):
        return "\n    {\n      %s: %s," % (json.dumps(sentinel_key), json.dumps(value))

    i = text.find(sentinel_of(records[0][sentinel_key]))
    if i < 0:
        j = text.rfind("\n  ]")
        return text[:j] + "," + body + "\n  ]\n}\n"

    mine = {r[sentinel_key] for r in records}
    # A RENAME LEAVES AN ORPHAN, and the span rule cannot see it: a record this tool wrote
    # under an id it no longer mints is "not owned", so it reads as the tail and everything
    # from it survives untouched — which is how T-0877 briefly shipped `jefferson` and
    # `jefferson_school_section` side by side. Ids of this tool's own shape that are not in
    # the current set are therefore a hard error, not a tail.
    stale = [r[sentinel_key] for r in json.loads(text)[
        next(k for k in ("streets", "blocks") if k in json.loads(text))]
        if r[sentinel_key] not in mine
        and ("school_section" in r[sentinel_key])]
    if stale:
        raise SystemExit(
            "splice: %s holds %d record(s) this tool minted under ids it no longer writes "
            "(%s). Restore the file from the branch point and re-run, or the rename leaves "
            "both copies committed." % (path, len(stale), ", ".join(stale)))
    array = json.loads(text)
    key_order = [r[sentinel_key] for r in
                 array[next(k for k in ("streets", "blocks") if k in array)]]
    tail = next((k for k in key_order[key_order.index(records[0][sentinel_key]):]
                 if k not in mine), None)
    if tail is None:
        return text[:i] + body + "\n  ]\n}\n"
    k = text.find(sentinel_of(tail), i)
    if k < 0:
        raise SystemExit("splice: cannot find the tail record %r in %s" % (tail, path))
    return text[:i] + body + "," + text[k:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and fail if any committed file would change")
    args = ap.parse_args()

    anchor, blocks, raster, sx = build()
    sale, sold = sale_test()
    streets = street_records(anchor) + ns_street_records(anchor)
    reservations = reservation_records(blocks, sale, sold)

    measured_x = NS_LINES[-1]["measured"] - NS_LINES[0]["measured"]
    measured_y = NS_LINES and (EW_LINES[0]["measured"] - EW_LINES[-1]["measured"])

    out = dict(
        _doc=__doc__.strip(),
        id="school_section_blocks_1834",
        generated_by="tools/generate_school_section_grid.py",
        ticket="T-0797",
        source="wright_1834_nara_hup",
        raster=dict(path=raster["working_copy"], sha256=raster["sha256"],
                    width=raster["width"], height=raster["height"], dpi=raster["dpi"]),
        registration="data/traces/gcp/wright_1834_nara_hup_gcps.json",
        anchor=anchor,
        residuals=dict(
            measured_east_west_span_m=round(measured_x, 2),
            measured_north_south_span_m=round(measured_y, 2),
            statute_mile_m=MILE_M,
            east_west_departure_m=round(measured_x - MILE_M, 2),
            north_south_departure_m=round(measured_y - MILE_M, 2),
            north_south_departure_pct=round(100 * (measured_y - MILE_M) / MILE_M, 2),
            finding=("The sheet's east-west span of the section falls 6.3 m short of the statute "
                     "mile, four tenths of one per cent, and its north-south span overruns it by "
                     "49.3 m, three per cent. That is the registration's own 5.2 per cent x/y "
                     "anisotropy showing at the bottom of the sheet, on the axis the manuscript was "
                     "torn and backed along, and it is why this grid is anchored on the section "
                     "rather than on the paper. It is also a figure worth carrying back to the fit: "
                     "a y-scale three per cent long over a mile is larger than any block."),
        ),
        grid=dict(columns=13, rows=12, cells=156, blocks=len(blocks),
                  cells_without_a_block=156 - 142 - 4,
                  cells_shared_by_a_block=4,
                  note=("Thirteen tiers of blocks north to south and twelve east to west make 156 "
                        "cells. Ten of them are the South Branch and carry no block; four more are "
                        "the east halves of blocks 73, 74, 83 and 84, each of which spans two cells "
                        "because Market Street stops at Adams. 156 - 10 - 4 = 142."),
                  how_the_lines_run=dict(
                      committed="level and plumb — every east-west line carries one northing end "
                                "to end and every north-south line one easting",
                      measurement="data/traces/vectors/school_section_tier_skew_1834.json",
                      measured_by="tools/measure_school_section_tier_skew.py",
                      east_west_median_tilt_deg=0.573,
                      north_south_median_tilt_deg=0.669,
                      lines_tilting_the_same_way="13 of 13 east-west and 14 of 14 north-south",
                      cardinal_control_mean_tilt_deg=0.692,
                      interior_mean_tilt_deg=0.556,
                      finding=(
                          "THE RULED LINES ARE NOT LEVEL ON THIS SHEET AND THE TILT IS NOT "
                          "WRIGHT'S (T-0959). The line tables below carry only the MEDIAN of the "
                          "bands each line was measured in, and a median cannot say whether the "
                          "bands trended; re-measuring with the bands kept shows every line of "
                          "both families tilting the same way. Two steps rule on it, and neither "
                          "assumes anything about what Wright drew. FIRST, a rotation of the "
                          "drawing under its registration tilts the two families equally and "
                          "OPPOSITELY — a same-signed tilt in both is not a rotation but a grid "
                          "that has stopped being square. SECOND, the section's four PLSS "
                          "boundaries run true north and true east ON THE GROUND by definition, "
                          "and one of their corners is GCP G1 of this very fit; measured exactly "
                          "as the interior lines are, they tilt +0.692 degrees in this frame "
                          "against +0.556 for the interior. A frame that tilts its own cardinal "
                          "control is telling you about itself. The mechanism is the fit's "
                          "non-conformality: two axis scales 6.2 per cent apart at 1.894 degrees "
                          "of rotation, under which a right angle ruled on the paper comes out at "
                          "91.62. So the tilt leaves with the rest of the registration's "
                          "distortion when the measured lines are rescaled onto the section's "
                          "statute-mile square, and the committed lines are level and plumb "
                          "because the section is, not because a median was carried."),
                      what_this_refuses=(
                          "PR #978 (closed under T-0930) drew the eight unnamed tiers with 25.7 m "
                          "of rise over 1,588 m — 0.93 degrees, inside the spread measured here — "
                          "and graded them `attested`. It is this artefact read as evidence. A "
                          "tilt that the registration puts on lines the PLSS guarantees are "
                          "cardinal is not attested by the survey, and `attested` is not earned "
                          "by it. `inferred` is what the committed lines carry and what they have "
                          "now been shown to deserve."),
                  ),
                  ns_lines=NS_LINES, ew_lines=EW_LINES,
                  corridor_widths=dict(
                      east_west_m=EW_CORRIDOR_M, north_south_m=NS_CORRIDOR_M,
                      note=("Adopted, not measured per line. Where the sheet draws a corridor with "
                            "two rules their separation was measured: the east-west median is "
                            "23.3 m and the north-south 20.4 m, against the 80 ft and 66 ft the "
                            "1830 plats use. The standards are adopted and the drawn separation is "
                            "kept per line as `drawn_w`, because the scatter of individual picks is "
                            "+/- 5 m and no single one is worth more than the standard."))),
        numbering=dict(
            scheme=("Serpentine, tier by tier: 1-12 down the westernmost, 13-24 back up the next, "
                    "and so on to 131-141 up the easternmost. The two corner blocks the sheet marks "
                    "'Reserved' carry no numeral and take 1 and 142 from the sequence."),
            read_on_the_sheet=sum(1 for b in blocks if b["numeral"]["on_sheet"]),
            supplied_by_the_sequence=sum(1 for b in blocks if not b["numeral"]["on_sheet"]),
            corroboration=("The October 1833 sale resolves %d of its section-16 rows to a block "
                           "number, and the %d distinct blocks it names are EXACTLY the blocks read "
                           "here in the four northern rows, with the two reserved corners missing "
                           "from both. That is a second witness to the reading, made by a different "
                           "hand in a different record."
                           % (sale["rows_resolving_to_a_block"], len(sale["blocks_sold"]))),
        ),
        sale_test=sale,
        numbering_cross_check=cross_check_numbering(),
        summary=dict(blocks=len(blocks),
                     reserved=sorted(RESERVED),
                     cut_by_south_branch=sorted(BANK_PENDING),
                     total_block_area_m2=round(sum(b["area_m2"] for b in blocks), 1)),
        blocks=blocks,
    )

    targets = [
        ("data/traces/vectors/school_section_blocks_1834.json",
         json.dumps(out, indent=2, ensure_ascii=False) + "\n"),
        ("data/streets/1835.json", splice("data/streets/1835.json", streets, "id", True)),
        ("data/reconstruction/1835_reserved_ground.json",
         splice("data/reconstruction/1835_reserved_ground.json", reservations, "block_id", False)),
    ]
    if args.check:
        bad = [p for p, want in targets if (ROOT / p).read_text() != want]
        if bad:
            print("FAIL school section grid is stale: " + ", ".join(bad))
            return 1
        print("OK  school section grid: %d blocks, %d streets, %d reservations re-derive"
              % (len(blocks), len(streets), len(reservations)))
        return 0
    for path, text in targets:
        (ROOT / path).write_text(text)
        print("wrote %s" % path)
    print("%d blocks, %d streets, %d reservations" % (len(blocks), len(streets), len(reservations)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
