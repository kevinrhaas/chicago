#!/usr/bin/env python3
"""Trace the 1904 Prairie Avenue street, alley, block and parcel grid (T-0474).

    python3 tools/trace_prairie_1904_grid.py            # (re)write data/street_grid/1904.json
    python3 tools/trace_prairie_1904_grid.py --check    # re-derive, change nothing
    python3 tools/trace_prairie_1904_grid.py --self-test

WHAT THIS IS. The urban framework the 1904 Prairie Avenue scene stands on, read off
the three Sanborn 1911 sheets Glessner House supplied (vol. 3, sheets 20, 28 and 35:
E. 16th to E. 22nd Street, Indiana Avenue to Calumet Avenue and the Illinois Central)
through the georeference T-1250 fitted to them (data/traces/gcp/). It writes one file,
data/street_grid/1904.json, which the renderer's street-grid layer draws and which
every Prairie Avenue landmark ticket cites a parcel and a street face from:

  streets      each street's carriageway, curb line to curb line, per segment
  faces        each block's street edges, laid out as four bands measured from the
               street (property) line: a 1-ft margin, the walk, the parkway, the curb
  alleys       the alleys as drawn, at their drawn widths
  blocks       the superblocks between streets (two lot tiers and their alley)
  parcels      the lots the sheets draw on both faces of Prairie Avenue, 16th to 22nd,
               each with the 1911 address(es) printed on it and the Prairie library's
               frontage row(s) for them

THE PICKS ARE READINGS, AND THE PIXELS ARE ON COMMITTED RASTERS. Every line below was
read on the committed sheet images (their sha256 are checked by
tools/georef_prairie_1904.py, whose street-line picks this tool IMPORTS rather than
repeats): lot lines and alley lines as peaks of a median darkness profile across the
line (the method T-1250 used), at the column or row stated; curves and jogs as vertices
read on enlargements with a 50-px grid. Nothing is taken from a modern street map.

TIERS. The geometry is a 1911 survey carried to 1904, so every line is INFERRED for 1904
-- Glessner House's reading that only 1609-1611 and 1620 Prairie changed between 1904
and 1911 on these sheets is what carries it, and it is a reading about buildings, not
street lines (docs/RESEARCH/prairie_1904_street_grid.md). The sidewalk space (14 ft on a
66-ft street, 10 ft on a 50-ft one) and the walk's one-foot set-back from the lot line
are the city's own defaults, from the Revised Municipal Code of 1905, secs. 2072 and
2062 (data/sources/chicago_revised_municipal_code_1905.json) -- INFERRED, because the
code yields to any block-level order and is dated 20 March 1905. The walk's width, the
curb's width and therefore the parkway are RECONSTRUCTED (docs/LIBERTIES.md L293).
No material is claimed for anything: that is T-1728.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from georef_prairie_1904 import SHEETS as GEOREF, line_fit  # noqa: E402

ROOT = HERE.parent
REPO = ROOT.parents[1]
GCP_DIR = ROOT / "data" / "traces" / "gcp"
OUT = ROOT / "data" / "street_grid" / "1904.json"
LIBRARY_FRONTAGES = REPO / "chicago" / "prairie_1904_v1" / "data" / "map_frontages.csv"
FT = 0.3048

SHEET_KEY = {"20": "sanborn_1911_v3_sheet_20", "28": "sanborn_1911_v3_sheet_28", "35": "sanborn_1911_v3_sheet_35"}
SHEET_SOURCE = {"20": "sanborn_1911_chicago_v3_sheet_20", "28": "sanborn_1911_chicago_v3_sheet_28",
                "35": "sanborn_1911_chicago_v3_sheet_35"}
CODE_1905 = "chicago_revised_municipal_code_1905"

# ---------------------------------------------------------------------------
# THE PICKS (pixels on the committed rasters). A 'v' line is x as a function of y,
# an 'h' line y as a function of x, exactly as tools/georef_prairie_1904.py fits
# them; a polyline is its vertices in order. Street lines the georeference already
# read are not repeated -- they are GEOREF[sheet]['lines'][name].

LINES: dict[str, dict[str, tuple]] = {
    "20": {
        # The alley between the Indiana and Prairie lots, 16th to 18th. Profile peaks
        # across rows 1600/3000/4500/5800; 118-124 px = 20 ft, printed "20'".
        "alley_w_w": ("v", [[2109.4, 1600], [2107.5, 3000], [2101.1, 4500], [2101.1, 5800]]),
        "alley_w_e": ("v", [[2231.7, 1600], [2225.2, 3000], [2224.9, 4500], [2225.6, 5800]]),
        # The Illinois Central right-of-way line the east-face lots end on: the first of
        # the tracks' lines, read every 400 rows (half-width 2 px); straight to 0.5 px.
        "ic_row": ("v", [[4111.6, 1100], [4231.2, 1500], [4350.7, 1900], [4467.5, 2300], [4583.9, 2700],
                         [4704.7, 3100], [4823.2, 3500], [4941.4, 3900], [5060.0, 4300], [5179.0, 4700],
                         [5295.1, 5100], [5414.9, 5500], [5533.7, 5900]]),
    },
    "28": {
        # E. 18th Street's two property lines, read WITHIN each block rather than across
        # the sheet: the drawn lines are not one straight line each (the south line drops
        # 5.5 px across the Glessner block, then stands 9 px higher east of Prairie).
        # Profile peaks, half-width 5 px, in front yards and street band only.
        "s18_n_a": ("h", [[700, 785.7], [950, 787.5], [1200, 789.5], [1400, 790.5], [1628, 791.4]]),
        "s18_n_b": ("h", [[2100, 780.8], [2500, 784.9], [3000, 790.8], [3400, 794.8]]),
        "s18_s_c": ("h", [[700, 1189.8], [950, 1191.1], [1200, 1192.8], [1400, 1194.0], [1628, 1195.3]]),
        "s18_s_d": ("h", [[2068, 1186.2], [2100, 1186.3], [2500, 1189.8], [3000, 1194.1], [3300, 1196.3]]),
        # The 24-ft alley behind the Prairie west-face lots (printed "24'"), 146 px wide.
        "alley_w_w": ("v", [[439.6, 1400], [426.7, 3000], [420.3, 4300], [409.7, 5800]]),
        "alley_w_e": ("v", [[585.7, 1400], [572.7, 3000], [562.8, 4300], [554.6, 5800]]),
        # The rear line of 1801 and 1811 Prairie, north of the east alley's head.
        "rear_1801_1811": ("v", [[2959.6, 1300], [2953.9, 1850]]),
        # The east alley's head: the 1811/1815 line carried across the alley.
        "alley_e_head": ("h", [[2920, 1975.8], [2960, 1976.5]]),
        # A cut across E. 18th Street where its lines begin to curve into Calumet Av.
        "cut_18th_calumet": ("v", [[3300, 700], [3300, 1300]]),
    },
    "35": {
        # The two alleys, 20th to 22nd (printed 20' north of 21st, 18' south of it; this
        # copy is 1.64 px per foot, so the drawn widths read 20-22 ft).
        "alley_w_w": ("v", [[439.5, 700], [441.1, 1200], [443.5, 1600]]),
        "alley_w_e": ("v", [[476.0, 700], [474.7, 1200], [474.9, 1600]]),
        "alley_e_w": ("v", [[1170.4, 400], [1170.3, 700], [1172.0, 1200], [1173.4, 1600]]),
        "alley_e_e": ("v", [[1203.0, 400], [1202.0, 1200], [1203.0, 1600]]),
    },
}

POLYLINES: dict[str, dict[str, list]] = {
    "28": {
        # Calumet Avenue's west line: E. 18th Street's south line bending into it at
        # the cut, the curve (profile peaks by column, then by row), the diagonal, the
        # bend at about (4312, 3586) where the diagonal meets the straight south run.
        "calumet_w": [[3300, 1196.3], [3420, 1210.2], [3480, 1229.9], [3540, 1258.0], [3600, 1304.3],
                      [3660, 1384.7], [3726.3, 1600], [3785.2, 1800], [3843.4, 2000], [3902.6, 2200],
                      [3961.5, 2400], [4020.7, 2600], [4079.8, 2800], [4257.1, 3400], [4312.1, 3586],
                      [4310.4, 3800], [4307.3, 4000], [4296.8, 5000], [4287.6, 5800], [4285.0, 6200]],
        # Calumet Avenue's east line: E. 18th Street's north line bending into it (the
        # "66'" printed across the curve), read by column to where it joins the IC fan
        # at about (4000, 1134); the diagonal beyond is the west line's diagonal moved
        # 66 ft (397.9 px) across it, and meets the straight run at about (4705, 3511).
        "calumet_e": [[3300, 794.0], [3400, 794.8], [3460, 795.3], [3520, 795.9], [3580, 805.5],
                      [3640, 821.9], [3700, 846.8], [3760, 881.2], [3820, 926.8], [3880, 989.5],
                      [4000, 1133.6], [4705.0, 3511.0], [4698.5, 4000], [4685.1, 5000], [4677.8, 5800],
                      [4675.0, 6200]],
        # The rear line of the Prairie east-face lots and the west line of the east
        # alley: straight at x ~2890 from the alley's head, a jog east at y 2780, the
        # barn's chamfered corner (the later of the two drawn lines, the lot line), then
        # straight south. Profile peaks (half-width 2-4 px) at the rows given.
        "alley_e_w": [[2892.3, 1976], [2892.3, 2100], [2888.9, 2400], [2887.2, 2650], [2887.0, 2779.9],
                      [2950.0, 2779.9], [2969.1, 2850], [3014.9, 2950], [3061.1, 3050], [3106.9, 3150],
                      [3111.1, 3300], [3104.9, 4000], [3098.6, 5000], [3093.8, 5800], [3092.0, 6200]],
        "alley_e_e": [[3009.0, 1976], [3009.0, 2100], [3012.6, 2650], [3059.4, 2850], [3101.5, 2950],
                      [3154.8, 3050], [3219.5, 3150], [3228.8, 3300], [3221.1, 4000], [3215.1, 5000],
                      [3211.2, 5800], [3210.0, 6200]],
    },
}

# The lot lines on each face of Prairie Avenue, north to south: the sheet column the
# profile was read at, and the row of each peak. Every line between the two cross
# streets that crosses the front yard AND the middle of the lot is here; a line seen at
# one column only (a wall, a bay, a label) is not. Labels are the addresses the sheet
# prints in the street band beside the lot, with the row of the label's centre, read on
# the band crops; a lot with no label printed has none.
FACES = [
    {"id": "prairie_w_16_18", "street": "prairie", "side": "west", "sheet": "20", "block": "blk_indiana_prairie_16_18",
     "front": ("line", "20", "prairie_w"), "rear": ("line", "20", "alley_w_e"),
     "north": ("line", "20", "s16_s"), "south": ("line", "28", "s18_n_a"),
     "column": 3290,
     "lot_lines": [1472.4, 1643.0, 1816.9, 2123.0, 2327.3, 2480.2, 2645.3, 2793.4, 2951.6, 3087.9, 3256.6,
                   3404.2, 3557.3, 3809.2, 4248.1, 4398.1, 4703.8, 5190.5, 5555.8, 5906.6],
     "labels": [["1600", 1360], ["1604", 1550], ["1608", 1710], ["1612", 1960], ["1616", 2240], ["1620", 2590],
                ["1626", 2860], ["1628", 3020], ["1630", 3180], ["1634", 3330], ["1636", 3480], ["1638", 3700],
                ["1700", 3880], ["1702", 3990], ["1706", 4140], ["1708", 4330], ["1712", 4500], ["1720", 4900],
                ["1726", 5390], ["1730", 5670], ["1736", 5980]]},
    {"id": "prairie_e_16_18", "street": "prairie", "side": "east", "sheet": "20", "block": "blk_prairie_ic_16_18",
     "front": ("line", "20", "prairie_e"), "rear": ("line", "20", "ic_row"),
     "north": ("line", "20", "s16_n"), "south": ("line", "28", "s18_n_b"),
     "column": 3760,
     "lot_lines": [1261.2, 1505.0, 1802.7, 1956.2, 2106.8, 2285.8, 2439.4, 2583.7, 2761.8, 2925.1, 3076.7,
                   3189.2, 3530.9, 4182.0, 4783.8, 5189.1],
     "labels": [["1601", 1050], ["1605", 1330], ["1607", 1550], ["1611", 1700], ["1613", 1860], ["1615", 2020],
                ["1619", 2190], ["1621", 2360], ["1623", 2510], ["1625", 2670], ["1637", 3340], ["1701", 3760],
                ["1709", 4290], ["1721", 5010], ["1729", 5620]]},
    {"id": "prairie_w_18_20", "street": "prairie", "side": "west", "sheet": "28", "block": "blk_indiana_prairie_18_20",
     "front": ("line", "28", "prairie_w"), "rear": ("line", "28", "alley_w_e"),
     "north": ("line", "28", "s18_s_c"), "south": ("line", "28", "s20_n"),
     "column": 1628, "columns": [{"from_row": 3500, "column": 1605}],
     "column_note": "rows above 3500 read at column 1628, below at 1605 (the street line leans)",
     "lot_lines": [1645.4, 1874.9, 2043.9, 2491.0, 2901.1, 3161.7, 3492.2, 3636.4, 3942.1, 4546.0, 4885.7, 5880.9],
     "labels": [["1800", 1250], ["1808", 1740], ["1812", 1960], ["1816", 2230], ["1824", 2650], ["1828", 3040],
                ["1834", 3320], ["1900", 3790], ["1906", 4060], ["1908", 4250], ["1912", 4730],
                ["1918 (1936)", 5260], ["1936", 5950]]},
    {"id": "prairie_e_18_20", "street": "prairie", "side": "east", "sheet": "28", "block": "blk_prairie_calumet_18_20",
     "front": ("line", "28", "prairie_e"), "rear": ("poly_join", "28", ["rear_1801_1811", "alley_e_w"]),
     "north": ("line", "28", "s18_s_d"), "south": ("line", "28", "s20_n"),
     "column": 2068, "columns": [{"from_row": 3500, "column": 2046}],
     "column_note": "rows above 3500 read at column 2068, below at 2046",
     "lot_lines": [1693.5, 1969.3, 2427.7, 2772.7, 3256.0, 3744.1, 4749.4, 5118.8, 5723.4],
     "labels": [["1801", 1300], ["1811", 1810], ["1815", 2100], ["1823", 2600], ["1827", 2950], ["1901", 3450],
                ["1905", 4130], ["1919", 5030], ["1923", 5300], ["1945", 5900]]},
    {"id": "prairie_w_20_21", "street": "prairie", "side": "west", "sheet": "35", "block": "blk_indiana_prairie_20_21",
     "front": ("line", "35", "prairie_w"), "rear": ("line", "35", "alley_w_e"),
     "north": ("line", "28", "s20_s"), "south": ("line", "35", "s21_n"),
     "column": 560, "column_note": "mid-block, between the houses and the rear buildings (this copy is 1.64 px/ft)",
     "lot_lines": [599.0, 789.2],
     "labels": [["2000", 312], ["2010", 445], ["2018", 572], ["2026", 662], ["2036", 835]]},
    {"id": "prairie_w_21_22", "street": "prairie", "side": "west", "sheet": "35", "block": "blk_indiana_prairie_21_22",
     "front": ("line", "35", "prairie_w"), "rear": ("line", "35", "alley_w_e"),
     "north": ("line", "35", "s21_s"), "south": ("line", "35", "s22_n"),
     "column": 560,
     "lot_lines": [1121.5, 1163.9, 1207.6, 1288.2, 1369.7, 1462.5, 1536.0],
     "labels": [["2100", 1040], ["2108", 1140], ["2110", 1190], ["2112", 1245], ["2120", 1330], ["2126", 1420],
                ["2130", 1500], ["2140", 1630]]},
    {"id": "prairie_e_20_21", "street": "prairie", "side": "east", "sheet": "35", "block": "blk_prairie_calumet_20_21",
     "front": ("line", "35", "prairie_e"), "rear": ("line", "35", "alley_e_w"),
     "north": ("line", "28", "s20_s"), "south": ("line", "35", "s21_n"),
     "column": 895, "columns": [{"rows": [385.2, 598.3], "column": 1000}],
     "column_note": "front yards at column 895; 385.2 and 598.3 read at column 1000, where they are clear",
     "lot_lines": [310.3, 347.3, 385.2, 433.1, 473.5, 517.0, 598.3, 681.5, 763.0, 805.5, 846.5],
     "labels": [["2001", 290], ["2003", 330], ["2005", 365], ["2009", 410], ["2011", 450], ["2013", 495],
                ["2017", 555], ["2021", 630], ["2027", 735], ["2031", 785], ["2033", 825], ["2035", 862]]},
    {"id": "prairie_e_21_22", "street": "prairie", "side": "east", "sheet": "35", "block": "blk_prairie_calumet_21_22",
     "front": ("line", "35", "prairie_e"), "rear": ("line", "35", "alley_e_w"),
     "north": ("line", "35", "s21_s"), "south": ("line", "35", "s22_n"),
     "column": 895,
     "lot_lines": [1121.2, 1202.6, 1301.6, 1368.8, 1450.7, 1534.5, 1614.5],
     "labels": [["2101", 1025], ["2109", 1150], ["2115", 1245], ["2123", 1335], ["2125", 1400], ["2127", 1475],
                ["2129", 1515], ["2141", 1680]]},
]

# ---------------------------------------------------------------------------
# THE STREET SECTION. Widths in feet from the street (property) line outward into
# the street. Revised Municipal Code of 1905, sec. 2072: the sidewalk space is 14 ft
# on a street 66-80 ft wide and 10 ft on one 50-60 ft wide; sec. 2062: the walk is
# laid one foot from and parallel with the lot line; sec. 2077: the rest of the space
# may be a grass plat. The walk's width and the curb's are this project's choices.

CROSS_SECTIONS = {
    "row_66": {
        "applies_to": "streets 66 ft wide (Prairie, Indiana, Calumet, 18th, 20th, 21st, 22nd)",
        "sidewalk_space_ft": {"value": 14.0, "tier": "inferred", "sources": [CODE_1905],
                              "note": "sec. 2072's default for streets 66 to 80 ft wide, 'unless a different width shall be specified in the order'. A city-wide rule in the code of 20 March 1905, carried to this block and to 1 July 1904; no block-level order for these streets has been read."},
        "bands": [
            {"band": "margin", "from_ft": 0.0, "to_ft": 1.0, "tier": "inferred", "sources": [CODE_1905],
             "note": "sec. 2062: 'All walks to be laid on a line one foot from and parallel with the lot line'. What covered the foot is not stated; it is drawn as the parkway's ground."},
            {"band": "walk", "from_ft": 1.0, "to_ft": 7.0, "tier": "reconstructed", "sources": [CODE_1905],
             "note": "6 ft: one of the walk widths sec. 2062 lays out in 5-by-6-ft blocks (5, 6, 10, 12 ... ft). Bounded by the 14-ft space less the 1-ft margin and a curb. No source states this block's walk. L293."},
            {"band": "parkway", "from_ft": 7.0, "to_ft": 13.5, "tier": "reconstructed", "sources": [CODE_1905],
             "note": "The remainder of the sidewalk space: sec. 2077's 'courts or open spaces ... for planting trees or for grass plats'. Its width follows from the walk's and the curb's, so it is reconstructed with them. L293."},
            {"band": "curb", "from_ft": 13.5, "to_ft": 14.0, "tier": "reconstructed", "sources": [CODE_1905],
             "note": "6 in: sec. 2072 asks only for curbing 'not less than three inches in thickness'. Width only; its reveal above the gutter is not drawn and not claimed. L293."},
        ],
    },
    "row_50": {
        "applies_to": "streets 50 ft wide (E. 16th Street, which sheet 20 prints as 50 ft)",
        "sidewalk_space_ft": {"value": 10.0, "tier": "inferred", "sources": [CODE_1905],
                              "note": "sec. 2072's default for streets 50 to 60 ft wide. Sheet 20 labels E. 16th Street '(Boulevard)'; a boulevard ordinance could have set another width, and none has been read."},
        "bands": [
            {"band": "margin", "from_ft": 0.0, "to_ft": 1.0, "tier": "inferred", "sources": [CODE_1905],
             "note": "sec. 2062, as on the 66-ft streets."},
            {"band": "walk", "from_ft": 1.0, "to_ft": 6.0, "tier": "reconstructed", "sources": [CODE_1905],
             "note": "5 ft: the narrowest walk sec. 2062 names, in a space 4 ft narrower than the 66-ft streets'. L293."},
            {"band": "parkway", "from_ft": 6.0, "to_ft": 9.5, "tier": "reconstructed", "sources": [CODE_1905],
             "note": "The remainder of the space. L293."},
            {"band": "curb", "from_ft": 9.5, "to_ft": 10.0, "tier": "reconstructed", "sources": [CODE_1905],
             "note": "6 in, as on the 66-ft streets. L293."},
        ],
    },
}

STREETS = {
    "prairie": {"name_1904": "Prairie Avenue", "printed": "Prairie Av. Blvd.", "name_2026": "South Prairie Avenue",
                "row_width_ft": 66, "cross_section": "row_66",
                "width_note": "printed 66' on sheets 20, 28 and 35; the drawn band reads 65.0 ft at sheet 28's bar (T-1250)"},
    "indiana": {"name_1904": "Indiana Avenue", "printed": "Indiana Av.", "name_2026": "South Indiana Avenue",
                "row_width_ft": 66, "cross_section": "row_66",
                "width_note": "printed 66' on sheets 20 and 35; sheet 20 draws both lines (67.6 ft at its bar), sheet 35 only the east line"},
    "calumet": {"name_1904": "Calumet Avenue", "printed": "Calumet Av.", "name_2026": "South Calumet Avenue (re-laid north of 21st)",
                "row_width_ft": 66, "cross_section": "row_66",
                "width_note": "printed 66' across the curve on sheet 28 and at 20th and 22nd on sheet 35; sheet 35 draws only the west line"},
    "e16th": {"name_1904": "East Sixteenth Street", "printed": "E. 16th St. (Boulevard)", "name_2026": "East 16th Street",
              "row_width_ft": 50, "cross_section": "row_50",
              "width_note": "printed 50 at Indiana on sheet 20; drawn 50.1 ft at its bar (T-1250)"},
    "e18th": {"name_1904": "East Eighteenth Street", "printed": "E. 18th St.", "name_2026": "East 18th Street",
              "row_width_ft": 66, "cross_section": "row_66",
              "width_note": "printed 66' on sheet 28; drawn 66.8 ft at its bar (T-1250)"},
    "e20th": {"name_1904": "East Twentieth Street", "printed": "E. 20th St.", "name_2026": "vacated between Indiana and Calumet",
              "row_width_ft": 66, "cross_section": "row_66",
              "width_note": "printed 66' on sheets 28 and 35"},
    "e21st": {"name_1904": "East Twenty-first Street", "printed": "E. 21st St.", "name_2026": "East 21st Street",
              "row_width_ft": 66, "cross_section": "row_66",
              "width_note": "printed 66' at Indiana on sheet 35"},
    "e22nd": {"name_1904": "East Twenty-second Street", "printed": "E. 22nd St.", "name_2026": "East Cermak Road",
              "row_width_ft": 66, "cross_section": "row_66",
              "width_note": "printed 66' at Indiana and Calumet on sheet 35"},
}

# Local lines that are not a single sheet's reading, each with the reason it exists.
DERIVED_LINES = {
    "indiana_e_18_20": {
        "how": "the straight line through sheet 20's Indiana east line at its row 6000 and sheet 35's at its row 300",
        "why": "Indiana Avenue between 18th and 20th is on sheet 27, which was not supplied; the two sheets either side draw the line 2 m apart in easting over 290 m, so it is carried straight between them",
        "tier": "inferred",
    },
    "indiana_w_18_22": {
        "how": "the Indiana east line moved 66 ft west",
        "why": "sheets 28 and 35 stop at Indiana's east line; 66 ft is printed on the street",
        "tier": "inferred",
    },
    "calumet_e_20_22": {
        "how": "sheet 35's Calumet west line moved 66 ft east",
        "why": "sheet 35 stops at Calumet's west line; 66 ft is printed on the street",
        "tier": "inferred",
    },
}

# Superblocks: the edges in counter-clockwise order (west, south, east, north) and what
# lies across each. A street edge carries a sidewalk space; a railway edge does not.
BLOCKS = [
    {"id": "blk_indiana_prairie_16_18", "sheet": "20", "edges": [
        {"ref": ("line", "20", "indiana_e"), "kind": "street", "street": "indiana"},
        {"ref": ("line", "28", "s18_n_a"), "kind": "street", "street": "e18th"},
        {"ref": ("line", "20", "prairie_w"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "20", "s16_s"), "kind": "street", "street": "e16th"}]},
    {"id": "blk_prairie_ic_16_18", "sheet": "20", "edges": [
        {"ref": ("line", "20", "prairie_e"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "28", "s18_n_b"), "kind": "street", "street": "e18th"},
        {"ref": ("poly", "28", "calumet_e"), "kind": "street", "street": "calumet"},
        {"ref": ("line", "20", "ic_row"), "kind": "railway", "street": None},
        {"ref": ("line", "20", "s16_n"), "kind": "unmapped", "street": None,
         "note": "the Illinois Central 16th Street station ground north of the block; E. 16th Street ends at Prairie"}]},
    {"id": "blk_indiana_prairie_18_20", "sheet": "28", "edges": [
        {"ref": ("local", "indiana_e_18_20"), "kind": "street", "street": "indiana"},
        {"ref": ("line", "28", "s20_n"), "kind": "street", "street": "e20th"},
        {"ref": ("line", "28", "prairie_w"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "28", "s18_s_c"), "kind": "street", "street": "e18th"}]},
    {"id": "blk_prairie_calumet_18_20", "sheet": "28", "edges": [
        {"ref": ("line", "28", "prairie_e"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "28", "s20_n"), "kind": "street", "street": "e20th"},
        {"ref": ("poly", "28", "calumet_w"), "kind": "street", "street": "calumet"},
        {"ref": ("line", "28", "s18_s_d"), "kind": "street", "street": "e18th"}]},
    {"id": "blk_indiana_prairie_20_21", "sheet": "35", "edges": [
        {"ref": ("line", "35", "indiana_e"), "kind": "street", "street": "indiana"},
        {"ref": ("line", "35", "s21_n"), "kind": "street", "street": "e21st"},
        {"ref": ("line", "35", "prairie_w"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "28", "s20_s"), "kind": "street", "street": "e20th"}]},
    {"id": "blk_indiana_prairie_21_22", "sheet": "35", "edges": [
        {"ref": ("line", "35", "indiana_e"), "kind": "street", "street": "indiana"},
        {"ref": ("line", "35", "s22_n"), "kind": "street", "street": "e22nd"},
        {"ref": ("line", "35", "prairie_w"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "35", "s21_s"), "kind": "street", "street": "e21st"}]},
    {"id": "blk_prairie_calumet_20_21", "sheet": "35", "edges": [
        {"ref": ("line", "35", "prairie_e"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "35", "s21_n"), "kind": "street", "street": "e21st"},
        {"ref": ("line", "35", "calumet_w"), "kind": "street", "street": "calumet"},
        {"ref": ("line", "28", "s20_s"), "kind": "street", "street": "e20th"}]},
    {"id": "blk_prairie_calumet_21_22", "sheet": "35", "edges": [
        {"ref": ("line", "35", "prairie_e"), "kind": "street", "street": "prairie"},
        {"ref": ("line", "35", "s22_n"), "kind": "street", "street": "e22nd"},
        {"ref": ("line", "35", "calumet_w"), "kind": "street", "street": "calumet"},
        {"ref": ("line", "35", "s21_s"), "kind": "street", "street": "e21st"}]},
]

# The alleys: their two drawn lines, cut by the block's cross-street edges.
ALLEYS = [
    {"id": "alley_indiana_prairie_16_18", "block": "blk_indiana_prairie_16_18", "sheet": "20", "printed_width_ft": 20,
     "sides": [("line", "20", "alley_w_w"), ("line", "20", "alley_w_e")],
     "cuts": [("line", "20", "s16_s"), ("line", "28", "s18_n_a")]},
    {"id": "alley_indiana_prairie_18_20", "block": "blk_indiana_prairie_18_20", "sheet": "28", "printed_width_ft": 24,
     "sides": [("line", "28", "alley_w_w"), ("line", "28", "alley_w_e")],
     "cuts": [("line", "28", "s18_s_c"), ("line", "28", "s20_n")]},
    {"id": "alley_prairie_calumet_18_20", "block": "blk_prairie_calumet_18_20", "sheet": "28", "printed_width_ft": 20,
     "sides": [("poly", "28", "alley_e_w"), ("poly", "28", "alley_e_e")],
     "cuts": [("line", "28", "alley_e_head"), ("line", "28", "s20_n")],
     "note": "Its head is the 1811/1815 lot line: 1801 and 1811 run back past it to the greenhouse lot. It narrows and jogs east where the lots of 1827 and 1901 run deeper, as drawn."},
    {"id": "alley_indiana_prairie_20_21", "block": "blk_indiana_prairie_20_21", "sheet": "35", "printed_width_ft": 20,
     "sides": [("line", "35", "alley_w_w"), ("line", "35", "alley_w_e")],
     "cuts": [("line", "28", "s20_s"), ("line", "35", "s21_n")]},
    {"id": "alley_indiana_prairie_21_22", "block": "blk_indiana_prairie_21_22", "sheet": "35", "printed_width_ft": 18,
     "sides": [("line", "35", "alley_w_w"), ("line", "35", "alley_w_e")],
     "cuts": [("line", "35", "s21_s"), ("line", "35", "s22_n")]},
    {"id": "alley_prairie_calumet_20_21", "block": "blk_prairie_calumet_20_21", "sheet": "35", "printed_width_ft": 20,
     "sides": [("line", "35", "alley_e_w"), ("line", "35", "alley_e_e")],
     "cuts": [("line", "28", "s20_s"), ("line", "35", "s21_n")]},
    {"id": "alley_prairie_calumet_21_22", "block": "blk_prairie_calumet_21_22", "sheet": "35", "printed_width_ft": 18,
     "sides": [("line", "35", "alley_e_w"), ("line", "35", "alley_e_e")],
     "cuts": [("line", "35", "s21_s"), ("line", "35", "s22_n")]},
]

# The carriageways, one per street segment: the two property lines it lies between
# (each offset inward by its sidewalk space to its curb line) and the two lines that
# end it. Segments run THROUGH their intersections to the far side of the cross street,
# so crossing carriageways overlap there and no seam can open between them.
SEGMENTS = [
    {"id": "indiana_16_18", "street": "indiana", "sheet": "20",
     "sides": [("line", "20", "indiana_w"), ("line", "20", "indiana_e")],
     "cuts": [("line", "20", "s16_n"), ("line", "28", "s18_s_c")]},
    {"id": "indiana_18_20", "street": "indiana", "sheet": "28",
     "sides": [("local", "indiana_w_18_22"), ("local", "indiana_e_18_20")],
     "cuts": [("line", "28", "s18_n_a"), ("line", "35", "s20_s")]},
    {"id": "indiana_20_22", "street": "indiana", "sheet": "35",
     "sides": [("local", "indiana_w_18_22"), ("line", "35", "indiana_e")],
     "cuts": [("line", "28", "s20_n"), ("line", "35", "s22_s")]},
    {"id": "prairie_16_18", "street": "prairie", "sheet": "20",
     "sides": [("line", "20", "prairie_w"), ("line", "20", "prairie_e")],
     "cuts": [("line", "20", "s16_n"), ("line", "28", "s18_s_c")]},
    {"id": "prairie_18_20", "street": "prairie", "sheet": "28",
     "sides": [("line", "28", "prairie_w"), ("line", "28", "prairie_e")],
     "cuts": [("line", "28", "s18_n_a"), ("line", "28", "s20_s")]},
    {"id": "prairie_20_22", "street": "prairie", "sheet": "35",
     "sides": [("line", "35", "prairie_w"), ("line", "35", "prairie_e")],
     "cuts": [("line", "28", "s20_n"), ("line", "35", "s22_s")]},
    {"id": "calumet_18_20", "street": "calumet", "sheet": "28",
     "sides": [("poly", "28", "calumet_w"), ("poly", "28", "calumet_e")],
     "cuts": [("line", "28", "cut_18th_calumet"), ("line", "28", "s20_s")]},
    {"id": "calumet_20_22", "street": "calumet", "sheet": "35",
     "sides": [("line", "35", "calumet_w"), ("local", "calumet_e_20_22")],
     "cuts": [("line", "28", "s20_n"), ("line", "35", "s22_s")]},
    {"id": "e16th_indiana_prairie", "street": "e16th", "sheet": "20",
     "sides": [("line", "20", "s16_n"), ("line", "20", "s16_s")],
     "cuts": [("line", "20", "indiana_w"), ("line", "20", "prairie_e")]},
    {"id": "e18th_indiana_prairie", "street": "e18th", "sheet": "28",
     "sides": [("line", "28", "s18_n_a"), ("line", "28", "s18_s_c")],
     "cuts": [("local", "indiana_w_18_22"), ("line", "28", "prairie_e")]},
    {"id": "e18th_prairie_calumet", "street": "e18th", "sheet": "28",
     "sides": [("line", "28", "s18_n_b"), ("line", "28", "s18_s_d")],
     "cuts": [("line", "28", "prairie_w"), ("line", "28", "cut_18th_calumet")]},
    {"id": "e20th_indiana_calumet", "street": "e20th", "sheet": "28",
     "sides": [("line", "28", "s20_n"), ("line", "28", "s20_s")],
     "cuts": [("local", "indiana_w_18_22"), ("local", "calumet_e_20_22")]},
    {"id": "e21st_indiana_calumet", "street": "e21st", "sheet": "35",
     "sides": [("line", "35", "s21_n"), ("line", "35", "s21_s")],
     "cuts": [("local", "indiana_w_18_22"), ("local", "calumet_e_20_22")]},
    {"id": "e22nd_indiana_calumet", "street": "e22nd", "sheet": "35",
     "sides": [("line", "35", "s22_n"), ("line", "35", "s22_s")],
     "cuts": [("local", "indiana_w_18_22"), ("local", "calumet_e_20_22")]},
]

# ---------------------------------------------------------------------------
# geometry


def r2(x: float) -> float:
    return round(x + 0.0, 2)


def pt(p) -> list[float]:
    return [r2(p[0]), r2(p[1])]


def coeffs(sheet: str) -> dict:
    return json.loads((GCP_DIR / f"{SHEET_KEY[sheet]}_gcps.json").read_text(encoding="utf-8"))["fit"]["coefficients"]


_CO: dict[str, dict] = {}


def to_local(sheet: str, px: float, py: float) -> tuple[float, float]:
    if sheet not in _CO:
        _CO[sheet] = coeffs(sheet)
    c = _CO[sheet]
    return (c["a"] * px + c["b"] * py + c["c"], c["d"] * px + c["e"] * py + c["f"])


def sheet_line(sheet: str, name: str):
    spec = LINES.get(sheet, {}).get(name) or GEOREF[SHEET_KEY[sheet]]["lines"][name]
    axis, p, q = line_fit(*spec)
    size = GEOREF[SHEET_KEY[sheet]]["size"]
    if axis == "v":
        a, b = (p + q * 0, 0.0), (p + q * size[1], float(size[1]))
    else:
        a, b = (0.0, p + q * 0), (float(size[0]), p + q * size[0])
    return (to_local(sheet, *a), to_local(sheet, *b))


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def unit(a):
    L = math.hypot(*a)
    return (a[0] / L, a[1] / L)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def offset_line(line, d, toward=None):
    a, b = line
    u = unit(sub(b, a))
    n = (u[1], -u[0])
    if toward is not None and dot(n, sub(toward, a)) < 0:
        n = (-n[0], -n[1])
    return (add(a, mul(n, d)), add(b, mul(n, d)))


def line_x(l1, l2):
    """Intersection of two infinite lines, or None when parallel."""
    p, r = l1[0], sub(l1[1], l1[0])
    q, s = l2[0], sub(l2[1], l2[0])
    den = cross(r, s)
    if abs(den) < 1e-12:
        return None
    t = cross(sub(q, p), s) / den
    return add(p, mul(r, t))


def seg_param(poly, i, p):
    a, b = poly[i], poly[i + 1]
    ab = sub(b, a)
    return dot(sub(p, a), ab) / dot(ab, ab)


def poly_line_x(poly, line, prefer: str):
    """Where a polyline meets a line. End segments are extended. `prefer` is 'start'
    or 'end': the hit nearest that end of the polyline wins. A polyline that begins
    (or ends) ON the line, tangentially, meets it at that vertex."""
    end_pt = poly[0] if prefer == "start" else poly[-1]
    lu = unit(sub(line[1], line[0]))
    off = abs(cross(lu, sub(end_pt, line[0])))
    if off < 0.3:
        return end_pt, (0.0 if prefer == "start" else float(len(poly) - 1))
    hits = []
    for i in range(len(poly) - 1):
        x = line_x((poly[i], poly[i + 1]), line)
        if x is None:
            continue
        t = seg_param(poly, i, x)
        lo = -1e9 if i == 0 else 0.0
        hi = 1e9 if i == len(poly) - 2 else 1.0
        if lo - 1e-9 <= t <= hi + 1e-9:
            hits.append((i + t, x))
    if not hits:
        raise SystemExit(f"a polyline does not meet the line it is cut by (prefer {prefer})")
    hits.sort(key=lambda h: h[0])
    s, x = hits[0] if prefer == "start" else hits[-1]
    return x, s


def sub_poly(poly, s0, s1):
    """The polyline between arc parameters s0 and s1 (vertex index + fraction), in
    that order, endpoints included."""
    def at(s):
        i = min(max(int(math.floor(s)), 0), len(poly) - 2)
        t = s - i
        return add(poly[i], mul(sub(poly[i + 1], poly[i]), t))
    out = [at(s0)]
    if s0 <= s1:
        out += [poly[k] for k in range(len(poly)) if s0 < k < s1]
    else:
        out += [poly[k] for k in range(len(poly) - 1, -1, -1) if s1 < k < s0]
    out.append(at(s1))
    return out


def offset_poly(poly, d, toward):
    """Offset a polyline by d toward the side `toward` (a point) lies on, mitring
    each interior vertex."""
    mid = len(poly) // 2
    i = min(mid, len(poly) - 2)
    u = unit(sub(poly[i + 1], poly[i]))
    n = (u[1], -u[0])
    sign = 1.0 if dot(n, sub(toward, poly[i])) >= 0 else -1.0
    out = []
    for k in range(len(poly)):
        ns = []
        if k > 0:
            u = unit(sub(poly[k], poly[k - 1]))
            ns.append((u[1] * sign, -u[0] * sign))
        if k < len(poly) - 1:
            u = unit(sub(poly[k + 1], poly[k]))
            ns.append((u[1] * sign, -u[0] * sign))
        if len(ns) == 1:
            m = ns[0]
        else:
            s = add(ns[0], ns[1])
            m = mul(s, 1.0 / (1.0 + dot(ns[0], ns[1])))
        out.append(add(poly[k], mul(m, d)))
    return out


class Geo:
    """Resolves a reference to a local line or polyline, once."""

    def __init__(self):
        self.cache: dict = {}

    def get(self, ref):
        key = json.dumps(ref)
        if key in self.cache:
            return self.cache[key]
        kind = ref[0]
        if kind == "line":
            val = ("line", sheet_line(ref[1], ref[2]))
        elif kind == "poly":
            val = ("poly", [to_local(ref[1], *p) for p in POLYLINES[ref[1]][ref[2]]])
        elif kind == "poly_join":
            # A rear line made of a straight line then a polyline: the line down to where
            # the polyline's first vertex stands level with it, then the polyline.
            ln = self.get(("line", ref[1], ref[2][0]))[1]
            pl = self.get(("poly", ref[1], ref[2][1]))[1]
            head = self.get(("line", "28", "alley_e_head"))[1]
            corner = line_x(ln, head)
            val = ("poly", [ln[0], corner, *pl])
        elif kind == "local":
            val = ("line", self.local(ref[1]))
        else:
            raise SystemExit(f"unknown reference {ref}")
        self.cache[key] = val
        return val

    def local(self, name):
        if name == "indiana_e_18_20":
            l20 = sheet_line("20", "indiana_e")
            l35 = sheet_line("35", "indiana_e")
            axis20, p20, q20 = line_fit(*GEOREF[SHEET_KEY["20"]]["lines"]["indiana_e"])
            axis35, p35, q35 = line_fit(*GEOREF[SHEET_KEY["35"]]["lines"]["indiana_e"])
            a = to_local("20", p20 + q20 * 6000, 6000)
            b = to_local("35", p35 + q35 * 300, 300)
            return (a, b)
        if name == "indiana_w_18_22":
            e = self.local("indiana_e_18_20")
            return offset_line(e, 66 * FT, toward=add(e[0], (-100.0, 0.0)))
        if name == "calumet_e_20_22":
            w = sheet_line("35", "calumet_w")
            return offset_line(w, 66 * FT, toward=add(w[0], (100.0, 0.0)))
        raise SystemExit(f"unknown local line {name}")


def meet(geo: Geo, a_ref, b_ref):
    """Corner between consecutive edges a -> b; returns (point, param_on_a, param_on_b)."""
    ka, va = geo.get(a_ref)
    kb, vb = geo.get(b_ref)
    if ka == "line" and kb == "line":
        return line_x(va, vb), None, None
    if ka == "poly" and kb == "line":
        x, s = poly_line_x(va, vb, prefer="end")
        return x, s, None
    if ka == "line" and kb == "poly":
        x, s = poly_line_x(vb, va, prefer="start")
        return x, None, s
    raise SystemExit("two polyline edges meet; not supported")


def block_outline(geo: Geo, block: dict):
    edges = block["edges"]
    n = len(edges)
    corners = [meet(geo, edges[i - 1]["ref"], edges[i]["ref"]) for i in range(n)]
    paths = []
    for i, e in enumerate(edges):
        c_in, c_out = corners[i], corners[(i + 1) % n]
        kind, val = geo.get(e["ref"])
        if kind == "line":
            paths.append([c_in[0], c_out[0]])
        else:
            s0, s1 = c_in[2], c_out[1]
            paths.append(sub_poly(val, s0, s1))
    return [c[0] for c in corners], paths


def polygon_area(poly) -> float:
    return 0.5 * sum(cross(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def seg_normal(a, b):
    u = unit(sub(b, a))
    return (u[1], -u[0])


def ring_bands(geo: Geo, block: dict):
    """The sidewalk-space bands of every street edge of a block, mitred at street-street
    corners and cut square along the neighbouring edge elsewhere."""
    corners, paths = block_outline(geo, block)
    ring = [p for path in paths for p in path[:-1]]
    if polygon_area(ring) <= 0:
        raise SystemExit(f"{block['id']}: the outline is not counter-clockwise")
    edges = block["edges"]
    n = len(edges)
    out = []
    for i, e in enumerate(edges):
        if e["kind"] != "street":
            continue
        xs = CROSS_SECTIONS[STREETS[e["street"]]["cross_section"]]
        bounds = [0.0] + [b["to_ft"] * FT for b in xs["bands"]]
        path = paths[i]
        prev_e, next_e = edges[i - 1], edges[(i + 1) % n]
        prev_path, next_path = paths[i - 1], paths[(i + 1) % n]

        def boundary(k, bounds=bounds, path=path, prev_e=prev_e, next_e=next_e,
                     prev_path=prev_path, next_path=next_path):
            d = bounds[k]
            pts = []
            m = len(path)
            for j in range(m):
                if 0 < j < m - 1:
                    n1 = seg_normal(path[j - 1], path[j])
                    n2 = seg_normal(path[j], path[j + 1])
                    s = add(n1, n2)
                    pts.append(add(path[j], mul(s, d / (1.0 + dot(n1, n2)))))
                    continue
                if j == 0:
                    a, b = path[0], path[1]
                    nb = prev_e
                    npth = prev_path
                    nseg = (npth[-2], npth[-1])
                else:
                    a, b = path[-2], path[-1]
                    nb = next_e
                    npth = next_path
                    nseg = (npth[0], npth[1])
                me = offset_line((a, b), d, toward=add(a, seg_normal(a, b)))
                if nb["kind"] == "street" and d > 0:
                    nxs = CROSS_SECTIONS[STREETS[nb["street"]]["cross_section"]]
                    nd = ([0.0] + [bb["to_ft"] * FT for bb in nxs["bands"]])[k]
                    other = offset_line(nseg, nd, toward=add(nseg[0], seg_normal(*nseg)))
                else:
                    other = nseg
                x = line_x(me, other)
                pts.append(x if x is not None else me[0 if j == 0 else 1])
            return pts

        lines = [boundary(k) for k in range(len(bounds))]
        for k, band in enumerate(xs["bands"]):
            inner, outer = lines[k], lines[k + 1]
            quads = [[pt(inner[j]), pt(inner[j + 1]), pt(outer[j + 1]), pt(outer[j])] for j in range(len(inner) - 1)]
            out.append({"edge": i, "band": band["band"], "polygons": quads})
    return corners, paths, out


def side_curb(geo: Geo, ref, other_ref, space_m):
    kind, val = geo.get(ref)
    okind, oval = geo.get(other_ref)
    probe = oval[len(oval) // 2] if okind == "poly" else mul(add(oval[0], oval[1]), 0.5)
    if kind == "line":
        # a point on the other side, level with this line's middle
        if okind == "line":
            mid = mul(add(val[0], val[1]), 0.5)
            u = unit(sub(val[1], val[0]))
            nrm = (u[1], -u[0])
            probe = line_x((mid, add(mid, nrm)), oval) or probe
        return "line", offset_line(val, space_m, toward=probe)
    return "poly", offset_poly(val, space_m, toward=probe)


def clip_between(geo: Geo, kind, val, cut_a, cut_b):
    la = geo.get(cut_a)[1]
    lb = geo.get(cut_b)[1]
    if kind == "line":
        return [line_x(val, la), line_x(val, lb)]
    xa, sa = poly_line_x(val, la, prefer="start")
    xb, sb = poly_line_x(val, lb, prefer="end")
    return sub_poly(val, sa, sb)


RIBBON_STEP_M = 5.0


def resample(poly, n):
    """n + 1 points spaced evenly by arc length along a polyline."""
    cum = [0.0]
    for i in range(len(poly) - 1):
        cum.append(cum[-1] + dist(poly[i], poly[i + 1]))
    total = cum[-1]
    out = []
    j = 0
    for k in range(n + 1):
        t = total * k / n
        while j < len(poly) - 2 and cum[j + 1] < t:
            j += 1
        seg = cum[j + 1] - cum[j]
        f = 0.0 if seg == 0 else (t - cum[j]) / seg
        out.append(add(poly[j], mul(sub(poly[j + 1], poly[j]), min(max(f, 0.0), 1.0))))
    return out


def strip(geo: Geo, sides, cuts, spaces):
    """The polygon between two side lines offset inward, cut at both ends -- and the
    same area as a list of quads between the two sides paired by arc length (one quad
    where both sides are straight, one every RIBBON_STEP_M along a curve), which is
    what the renderer tessellates."""
    ka, a = side_curb(geo, sides[0], sides[1], spaces[0])
    kb, b = side_curb(geo, sides[1], sides[0], spaces[1])
    pa = clip_between(geo, ka, a, cuts[0], cuts[1])
    pb = clip_between(geo, kb, b, cuts[0], cuts[1])
    poly = pa + list(reversed(pb))
    if polygon_area(poly) < 0:
        poly = list(reversed(poly))
    if len(pa) == 2 and len(pb) == 2:
        n = 1
    else:
        la = sum(dist(pa[i], pa[i + 1]) for i in range(len(pa) - 1))
        lb = sum(dist(pb[i], pb[i + 1]) for i in range(len(pb) - 1))
        n = max(1, math.ceil(max(la, lb) / RIBBON_STEP_M))
    ra, rb = resample(pa, n), resample(pb, n)
    quads = []
    for i in range(n):
        q = [ra[i], ra[i + 1], rb[i + 1], rb[i]]
        if polygon_area(q) < 0:
            q = [ra[i], rb[i], rb[i + 1], ra[i + 1]]
        quads.append([pt(v) for v in q])
    return [pt(v) for v in poly], quads


def ref_label(ref) -> str:
    if ref[0] in ("line", "poly"):
        return f"sheet {ref[1]} {ref[0]} {ref[2]}"
    if ref[0] == "poly_join":
        return f"sheet {ref[1]} {' + '.join(ref[2])}"
    return f"derived line {ref[1]}"


PLACE_WORDS = {"indiana": "Indiana", "prairie": "Prairie", "calumet": "Calumet", "ic": "the Illinois Central",
               "16": "16th", "18": "18th", "20": "20th", "21": "21st", "22": "22nd"}


def block_words(block_id: str) -> str:
    """'blk_indiana_prairie_18_20' -> 'Indiana to Prairie, 18th to 20th Street'."""
    a, b, n, s_ = block_id.replace("blk_", "").split("_")
    return f"{PLACE_WORDS[a]} to {PLACE_WORDS[b]}, {PLACE_WORDS[n]} to {PLACE_WORDS[s_]} Street"


def segment_words(seg_id: str) -> str:
    """'prairie_18_20' -> 'Prairie Avenue, 18th to 20th Street';
    'e18th_indiana_prairie' -> 'East Eighteenth Street, Indiana to Prairie Avenue'."""
    parts = seg_id.split("_")
    street = STREETS[parts[0]]["name_1904"]
    if parts[1].isdigit():
        return f"{street}, {PLACE_WORDS[parts[1]]} to {PLACE_WORDS[parts[2]]} Street"
    return f"{street}, {PLACE_WORDS[parts[1]]} to {PLACE_WORDS[parts[2]]} Avenue"


def library_rows() -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {}
    if not LIBRARY_FRONTAGES.exists():
        return rows
    with LIBRARY_FRONTAGES.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("street", "").endswith("Prairie Avenue"):
                rows.setdefault(r["sheet"], []).append(r)
    return rows


def library_numbers(address: str) -> set[str]:
    """The house numbers a library address names: '1607–1611' -> the run of numbers on
    that side between them, '1916 (1930)' -> both."""
    out: set[str] = set()
    for a, b in re.findall(r"(\d+)\s*[–-]\s*(\d+)", address):
        out |= {str(k) for k in range(int(a), int(b) + 1, 2)}
    out |= set(re.findall(r"\d+", address))
    return out


# Where this reading of the sheet and the Prairie library's (map_frontages.csv) print
# a different number for the same frontage. The library calls its readings tentative
# until this ticket checks them; each of these was re-read on an 8x enlargement of the
# label on the full-resolution sheet.
READ_AGAINST_LIBRARY = {
    "1605": ("frontage-20-023", "The sheet prints 1605 beside the Illinois Central 16th St. station lot; the "
             "library reads 1603. The station is the same frontage."),
    "1721": ("frontage-20-034", "The sheet prints 1721; the library reads 1719 for the same two-bayed house."),
    "1918": ("frontage-28-047", "The stacked label reads '1918' over '(1936)' (the parenthesised figure is "
             "unambiguous); the library read '1916 (1930)' at medium confidence and asked for it to be resolved. "
             "What the parenthesised number means -- the number before the 1909 renumbering, or a second "
             "entrance -- is not settled here."),
}


def parcels_for(geo: Geo, face: dict, lib: dict[str, list[dict]]):
    front = geo.get(face["front"])[1]
    rear_kind, rear = geo.get(face["rear"])
    north = geo.get(face["north"])[1]
    south = geo.get(face["south"])[1]
    sheet = face["sheet"]
    col = face["column"]
    dn = unit(sub(north[1], north[0]))
    ds = unit(sub(south[1], south[0]))
    d = unit(add(dn, ds)) if dot(dn, ds) > 0 else unit(sub(dn, ds))
    lot_lines = [north]
    for y in face["lot_lines"]:
        c = col
        for rule in face.get("columns", []):
            if ("from_row" in rule and y >= rule["from_row"]) or y in rule.get("rows", []):
                c = rule["column"]
        p = to_local(sheet, c, y)
        lot_lines.append((p, add(p, d)))
    lot_lines.append(south)
    rows = lib.get(sheet, [])
    side = face["side"]
    by_addr = {}
    for r in rows:
        if r["side"] == side:
            by_addr.setdefault(r["address"], []).append(r)
    labels = face["labels"]
    bounds = [None] + face["lot_lines"] + [None]
    out = []
    used_labels = set()
    for i in range(len(lot_lines) - 1):
        la, lb = lot_lines[i], lot_lines[i + 1]
        fa, fb = line_x(front, la), line_x(front, lb)
        if rear_kind == "line":
            ra, rb = line_x(rear, la), line_x(rear, lb)
            rear_mid = []
        else:
            ra, sa = poly_line_x(rear, la, prefer="start")
            rb, sb = poly_line_x(rear, lb, prefer="start")
            mid = sub_poly(rear, sb, sa)
            rear_mid = mid[1:-1]
            ra, rb = mid[-1], mid[0]
        poly = [fa, fb, rb, *rear_mid, ra]
        if polygon_area(poly) < 0:
            poly = list(reversed(poly))
        y0 = bounds[i] if bounds[i] is not None else -1e9
        y1 = bounds[i + 1] if bounds[i + 1] is not None else 1e9
        here = [lab for lab in labels if y0 < lab[1] < y1]
        for lab in here:
            used_labels.add(lab[0])
        addrs = [lab[0] for lab in here]
        frontage_ft = dist(fa, fb) / FT
        depth_ft = (dist(fa, ra) + dist(fb, rb)) / 2 / FT
        lib_ids, disagreements = [], []
        for a in addrs:
            first = a.split()[0]
            hit = [r for r in rows if r["side"] == side and first in library_numbers(r["address"])]
            for h in hit:
                if h["id"] not in lib_ids:
                    lib_ids.append(h["id"])
            if first in READ_AGAINST_LIBRARY:
                row, why = READ_AGAINST_LIBRARY[first]
                disagreements.append({"printed": a, "library_row": row, "reading": why})
                if row not in lib_ids:
                    lib_ids.append(row)
            elif not hit:
                raise SystemExit(f"{face['id']}: {a} matches no library row and no ruling says why")
        out.append({
            "poly": poly, "addresses": addrs, "frontage_ft": frontage_ft, "depth_ft": depth_ft,
            "library_frontage_ids": lib_ids, "disagreements": disagreements,
            "lot_line_rows": [bounds[i], bounds[i + 1]], "front": (fa, fb), "rear": (ra, rb),
        })
    missing = [lab[0] for lab in labels if lab[0] not in used_labels]
    if missing:
        raise SystemExit(f"{face['id']}: labels fall on no lot: {missing}")
    return out


def parcel_ids(face: dict, parcels: list[dict]) -> list[str]:
    ids = []
    for i, p in enumerate(parcels):
        if p["addresses"]:
            ids.append("prairie_" + p["addresses"][0].split()[0])
        else:
            prev = next((q["addresses"][-1].split()[0] for q in reversed(parcels[:i]) if q["addresses"]), "n")
            nxt = next((q["addresses"][0].split()[0] for q in parcels[i + 1:] if q["addresses"]), "s")
            ids.append(f"prairie_{prev}_{nxt}")
    # a run of unlabelled lots between the same two addresses is lettered north to south
    for base in {i for i in ids if ids.count(i) > 1}:
        k = 0
        for j, v in enumerate(ids):
            if v == base:
                ids[j] = f"{base}_{'abcdefgh'[k]}"
                k += 1
    if len(set(ids)) != len(ids):
        raise SystemExit(f"{face['id']}: duplicate parcel ids {ids}")
    return ids


# ---------------------------------------------------------------------------


def build() -> dict:
    geo = Geo()
    lib = library_rows()

    blocks_out, faces_out, alleys_out, segs_out, parcels_out = [], [], [], [], []
    block_by_id = {}
    for b in BLOCKS:
        corners, paths, bands = ring_bands(geo, b)
        outline = [p for path in paths for p in path[:-1]]
        rec = {
            "id": b["id"],
            "where": block_words(b["id"]),
            "outline_local_m": [pt(p) for p in outline],
            "area_m2": r2(polygon_area(outline)),
            "edges": [],
            "sources": sorted({SHEET_SOURCE[e["ref"][1]] for e in b["edges"] if e["ref"][0] != "local"}
                              | ({SHEET_SOURCE["20"], SHEET_SOURCE["35"]} if any(e["ref"][0] == "local" for e in b["edges"]) else set())),
            "geometry_tier": "inferred",
        }
        for i, e in enumerate(b["edges"]):
            face_id = None
            if e["kind"] == "street":
                face_id = f"{e['street']}__{b['id'].replace('blk_', '')}"
            rec["edges"].append({"line": ref_label(e["ref"]), "kind": e["kind"], "street": e["street"],
                                 "face": face_id, **({"note": e["note"]} if e.get("note") else {})})
        blocks_out.append(rec)
        block_by_id[b["id"]] = (b, corners, paths)
        for band in bands:
            e = b["edges"][band["edge"]]
            fid = f"{e['street']}__{b['id'].replace('blk_', '')}"
            face = next((f for f in faces_out if f["id"] == fid), None)
            if face is None:
                xs_id = STREETS[e["street"]]["cross_section"]
                path = paths[band["edge"]]
                face = {"id": fid, "street": e["street"], "block": b["id"], "cross_section": xs_id,
                        "where": f"{STREETS[e['street']]['name_1904']}, beside the block {block_words(b['id'])}",
                        "street_line_local_m": [pt(p) for p in path],
                        "length_m": r2(sum(dist(path[j], path[j + 1]) for j in range(len(path) - 1))),
                        "street_line_tier": "derived" if e["ref"][0] == "local" else "inferred",
                        "street_line_from": ref_label(e["ref"]),
                        "bands": {}}
                faces_out.append(face)
            face["bands"][band["band"]] = band["polygons"]

    for a in ALLEYS:
        poly, quads = strip(geo, a["sides"], a["cuts"], [0.0, 0.0])
        alleys_out.append({"id": a["id"], "block": a["block"], "where": f"behind the lots of {block_words(a['block'])}",
                           "printed_width_ft": a["printed_width_ft"],
                           "polygon_local_m": poly, "quads_local_m": quads, "area_m2": r2(abs(polygon_area(poly))),
                           "geometry_tier": "inferred", "sources": [SHEET_SOURCE[a["sheet"]]],
                           "drawn_from": [ref_label(s) for s in a["sides"]],
                           **({"note": a["note"]} if a.get("note") else {})})

    for s in SEGMENTS:
        st = STREETS[s["street"]]
        space = CROSS_SECTIONS[st["cross_section"]]["sidewalk_space_ft"]["value"] * FT
        poly, quads = strip(geo, s["sides"], s["cuts"], [space, space])
        derived = [ref_label(x) for x in s["sides"] if x[0] == "local"]
        segs_out.append({"id": s["id"], "street": s["street"], "where": segment_words(s["id"]),
                         "polygon_local_m": poly, "quads_local_m": quads,
                         "area_m2": r2(abs(polygon_area(poly))),
                         "between": [ref_label(x) for x in s["sides"]],
                         "geometry_tier": "inferred", "sources": sorted({SHEET_SOURCE[s["sheet"]], CODE_1905}),
                         **({"derived_sides": derived} if derived else {})})

    for f in FACES:
        parcels = parcels_for(geo, f, lib)
        ids = parcel_ids(f, parcels)
        face_id = f"{f['street']}__{f['block'].replace('blk_', '')}"
        for pid, p in zip(ids, parcels):
            fa, fb = p["front"]
            ra, rb = p["rear"]
            rec = {
                "id": pid,
                "addresses_1911": p["addresses"],
                "street": "prairie", "side": f["side"], "block": f["block"], "street_face": face_id,
                "where": f"the {f['side']} side of Prairie Avenue, in the block {block_words(f['block'])}",
                "polygon_local_m": [pt(q) for q in p["poly"]],
                "corners_local_m": ({"NE_street": pt(fa), "SE_street": pt(fb), "SW_rear": pt(rb), "NW_rear": pt(ra)}
                                    if f["side"] == "west" else
                                    {"NW_street": pt(fa), "SW_street": pt(fb), "SE_rear": pt(rb), "NE_rear": pt(ra)}),
                "frontage_ft": round(p["frontage_ft"], 1),
                "depth_ft": round(p["depth_ft"], 1),
                "area_m2": r2(abs(polygon_area(p["poly"]))),
                "geometry_tier": "inferred",
                "sources": [SHEET_SOURCE[f["sheet"]]] + ([SHEET_SOURCE["28"]] if f["south"][1] == "28" and f["sheet"] != "28" else []),
                "read": f"lot lines at sheet {f['sheet']} rows {p['lot_line_rows']} (profile peaks at column {f['column']}); "
                        f"front {ref_label(f['front'])}, rear {ref_label(f['rear'])}",
                "library_frontage_ids": p["library_frontage_ids"],
            }
            if p["disagreements"]:
                rec["library_disagreements"] = p["disagreements"]
            if not p["addresses"]:
                rec["note"] = "No address is printed beside this lot on the 1911 sheet."
            parcels_out.append(rec)

    glessner = next(p for p in parcels_out if p["id"] == "prairie_1800")
    doc = {
        "_doc": ("The 1904 Prairie Avenue street, alley, block and parcel grid (T-0474). GENERATED by "
                 "tools/trace_prairie_1904_grid.py from picks written in that tool on the committed Sanborn 1911 "
                 "sheets 20, 28 and 35, through the T-1250 georeference in data/traces/gcp/ -- do not hand-edit; "
                 "re-run the tool. Local ENU metres of data/datum.json. The renderer's street-grid layer draws "
                 "carriageways, the four sidewalk-space bands of every block face, the alleys and the parcel "
                 "lines in neutral surfaces: no material is claimed for any of them (T-1728 owns the surfaces). "
                 "docs/RESEARCH/prairie_1904_street_grid.md is the reading; docs/LIBERTIES.md L293 the inventions."),
        "scene": "1904",
        "target_date": "1904-07-01",
        "ticket": "T-0474",
        "generated_by": "tools/trace_prairie_1904_grid.py",
        "frame": "local ENU metres, data/datum.json",
        "sources": sorted({*SHEET_SOURCE.values(), CODE_1905}),
        "geometry_standard": ("Every line is a reading of a 1911 sheet carried to 1904, so every line is INFERRED for "
                              "1904: the street and lot lines are assumed unchanged 1904-1911, which Glessner House's "
                              "reading of these sheets (only 1609-1611 and 1620 Prairie changed) supports for the "
                              "buildings and does not state for the lines. Where a sheet stops at a street's near "
                              "line, its far line is that line moved the printed width (derived_lines)."),
        "surface_standard": ("No material, colour or texture is claimed: the renderer draws each band in a neutral "
                             "tone that tells the bands apart. The carriageway's paving, the curb's stone or timber, "
                             "the walk's plank, stone or cement and the parkway's grass are T-1728's to source."),
        "cross_sections": CROSS_SECTIONS,
        "streets": {k: {**v, "row_width_tier": "inferred",
                        "row_width_sources": sorted({SHEET_SOURCE[s] for s in ("20", "28", "35")})}
                    for k, v in STREETS.items()},
        "derived_lines": DERIVED_LINES,
        "rulings": {
            "glessner_lot_frontage": {
                "question": "T-1731 left the frontage of 1800 Prairie at 74 or 77 ft, and the 1800/1808 line, for this ticket.",
                "ruling_ft": glessner["frontage_ft"],
                "tier": "inferred",
                "sources": [SHEET_SOURCE["28"], "habs_glessner_house_il_1015_drawings"],
                "parcel": "prairie_1800",
                "reading": ("Sheet 28 draws the 1800/1808 lot line at row 1645.4 and E. 18th Street's south line at "
                            "row 1195.3 where they meet Prairie Avenue (profile peaks at column 1628, in the front "
                            "yard): 450.1 px at the printed bar's 6.029 px per foot is 74.7 ft, and through the "
                            "fit the parcel's street frontage measures "
                            f"{glessner['frontage_ft']} ft. The sheet's own scale is good to about 1.5 per cent "
                            "(its 66-ft bands read 65.0 to 66.8 ft; the house, 74'-0\" on HABS sheet 2, draws "
                            "73.0 ft), so the reading is 74.7 +/- 1.1 ft."),
                "why_not_77": "77 ft is 2.3 ft (14 px) beyond the drawn line, twice the sheet's scale uncertainty. The 2 x 30 + 17 ft arithmetic T-1731 offered assumes 30-ft lots, which nothing read states.",
                "why_not_74": ("The drawn line stands 10 px (1.7 ft) south of the house's drawn south face: the lot "
                               "is a little wider than the 74'-0\" house. HABS sheets 2-3 draw a 1'-6\" brick wall "
                               "just south of the east wing, and the line falls at that wall's south face within "
                               "the reading's tolerance, so the wall stands on the Glessner side of it."),
                "for_T-1732": ("Place the house with its north face on the parcel's north (E. 18th Street) line and "
                               "its east face 14.7 ft behind the parcel's street line (T-1731's placement); the "
                               "parcel is prairie_1800, face prairie__indiana_prairie_18_20."),
            },
        },
        "blocks": blocks_out,
        "faces": faces_out,
        "alleys": alleys_out,
        "carriageways": segs_out,
        "parcels": parcels_out,
    }
    return doc


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def contract(doc: dict) -> list[str]:
    bad = []
    parcels = {p["id"]: p for p in doc["parcels"]}
    g = parcels.get("prairie_1800")
    if not g:
        bad.append("there is no parcel prairie_1800 for the Glessner House to stand on")
    elif not 73.5 <= g["frontage_ft"] <= 76.0:
        bad.append(f"prairie_1800's frontage reads {g['frontage_ft']} ft, outside the 73.5-76.0 ft the sheet allows")
    elif not 170 <= g["depth_ft"] <= 182:
        bad.append(f"prairie_1800's depth reads {g['depth_ft']} ft against T-1731's 175.95")
    for p in doc["parcels"]:
        if p["frontage_ft"] <= 5 or p["depth_ft"] <= 30:
            bad.append(f"{p['id']}: a {p['frontage_ft']} x {p['depth_ft']} ft lot is a misread line, not a lot")
        if p["area_m2"] <= 0:
            bad.append(f"{p['id']}: a parcel with no area")
    # the lots of a face tile it: frontages sum to the face's lot-line span
    by_face: dict[str, list] = {}
    for p in doc["parcels"]:
        by_face.setdefault(p["block"] + p["side"], []).append(p)
    for key, ps in by_face.items():
        total = sum(p["frontage_ft"] for p in ps)
        # the shortest face is 20th-21st, 377 ft between two 66-ft streets
        if not 300 <= total <= 1400:
            bad.append(f"{key}: its lots' frontages sum to {total:.0f} ft, which is not a block face")
    want = {b["band"] for xs in doc["cross_sections"].values() for b in xs["bands"]}
    for f in doc["faces"]:
        if set(f["bands"]) != want:
            bad.append(f"{f['id']}: bands {sorted(f['bands'])} are not the section's {sorted(want)}")
    for xs_id, xs in doc["cross_sections"].items():
        span = xs["bands"][-1]["to_ft"]
        if abs(span - xs["sidewalk_space_ft"]["value"]) > 1e-9:
            bad.append(f"{xs_id}: its bands reach {span} ft, not the {xs['sidewalk_space_ft']['value']}-ft sidewalk space")
        for a, b in zip(xs["bands"], xs["bands"][1:]):
            if abs(a["to_ft"] - b["from_ft"]) > 1e-9:
                bad.append(f"{xs_id}: a gap between {a['band']} and {b['band']}")
        for b in xs["bands"]:
            if b["tier"] not in ("attested", "inferred", "reconstructed"):
                bad.append(f"{xs_id}.{b['band']}: '{b['tier']}' is not a tier")
    for c in doc["carriageways"]:
        if c["area_m2"] < 500:
            bad.append(f"{c['id']}: a {c['area_m2']} m2 carriageway is a degenerate strip")
    for b in doc["blocks"]:
        # the smallest superblocks are the 20th-21st pair, about 13,200 m2
        if not 8000 <= b["area_m2"] <= 60000:
            bad.append(f"{b['id']}: a {b['area_m2']} m2 block is not one of these superblocks")
    faces = {f["id"] for f in doc["faces"]}
    for p in doc["parcels"]:
        if p["street_face"] not in faces:
            bad.append(f"{p['id']}: cites street face {p['street_face']}, which the grid does not lay out")
    return bad


def check() -> list[str]:
    doc = build()
    bad = []
    if not OUT.exists():
        bad.append(f"{OUT.relative_to(ROOT)} is missing; run tools/trace_prairie_1904_grid.py")
    elif OUT.read_text(encoding="utf-8") != dumps(doc):
        bad.append(f"{OUT.relative_to(ROOT)} is not what the tool derives; re-run it (or revert a hand edit)")
    return bad + contract(doc)


def self_test() -> int:
    base = build()
    cases = []

    saved = copy.deepcopy(FACES)
    FACES[2]["lot_lines"][0] = 1665.0   # the 1800/1808 line misread 20 px (3.3 ft) south
    cases.append(("a 1800/1808 line misread 3.3 ft south moves the Glessner frontage outside the sheet's band",
                  any("prairie_1800's frontage" in b for b in contract(build()))))
    FACES[:] = copy.deepcopy(saved)

    FACES[2]["labels"].append(["9999", FACES[2]["lot_lines"][0]])   # centred ON a lot line
    try:
        build()
        ok = False
    except SystemExit as e:
        ok = "labels fall on no lot" in str(e)
    cases.append(("an address label centred on a lot line, which belongs to no lot, is refused", ok))
    FACES[:] = copy.deepcopy(saved)

    doc = copy.deepcopy(base)
    doc["cross_sections"]["row_66"]["bands"][1]["to_ft"] = 8.0
    cases.append(("a section whose bands no longer meet is refused",
                  any("gap between" in b for b in contract(doc))))

    doc = copy.deepcopy(base)
    doc["parcels"][0]["street_face"] = "nowhere"
    cases.append(("a parcel citing a face the grid does not lay out is refused", bool(contract(doc))))

    doc = copy.deepcopy(base)
    doc["faces"][0]["bands"].pop("curb")
    cases.append(("a face missing a band is refused", bool(contract(doc))))

    cases.append(("the committed file is what the tool derives", not check()))
    for label, ok in cases:
        print(("   ok   " if ok else "   FAIL ") + label)
    return 0 if all(ok for _, ok in cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        bad = check()
        for b in bad:
            print("FAIL", b)
        if not bad:
            doc = build()
            g = next(p for p in doc["parcels"] if p["id"] == "prairie_1800")
            print(f"OK the 1904 Prairie Avenue grid re-derives: {len(doc['carriageways'])} carriageways, "
                  f"{len(doc['faces'])} block faces, {len(doc['alleys'])} alleys, {len(doc['parcels'])} parcels; "
                  f"prairie_1800 {g['frontage_ft']} x {g['depth_ft']} ft")
        return 1 if bad else 0
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dumps(doc), encoding="utf-8")
    for c in doc["carriageways"]:
        print(f"  carriageway {c['id']:26s} {c['area_m2']:9.1f} m2")
    for b in doc["blocks"]:
        print(f"  block {b['id']:30s} {b['area_m2']:9.1f} m2")
    for p in doc["parcels"]:
        print(f"  parcel {p['id']:22s} {p['frontage_ft']:6.1f} x {p['depth_ft']:6.1f} ft  {p['addresses_1911']} "
              f"{p['library_frontage_ids']} {p.get('library_disagreements', '')}")
    bad = contract(doc)
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
