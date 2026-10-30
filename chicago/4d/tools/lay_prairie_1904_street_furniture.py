#!/usr/bin/env python3
"""Lay the 1904 district's street furniture: the gas lamps on the parkways (T-3199).

    python3 tools/lay_prairie_1904_street_furniture.py           # write data/street_furniture/1904.json
    python3 tools/lay_prairie_1904_street_furniture.py --check   # the committed file is what this writes

WHAT IT READS. The block faces, their bands and the alleys of data/street_grid/1904.json
(T-0474), the carriage walks of data/street_section/1904.json (T-2474), the parkway elms
of data/street_trees/1904.json (T-2473), and the source records in data/sources/ that the
pictured items cite (their citation lines are copied in, so a card can show them). It
writes data/street_furniture/1904.json, which renderers/web/js/street-furniture.js draws.

THE LAMPS (the owner, 2026-10-27: "I do see evidence of streetlamps at the corners of
major streets, and also from the photo"). Every picture of the district's streets around
the scene date shows cast-iron gas lamp posts on the parkways: at the corners (Glessner's
in J. W. Taylor's photograph no. 2135, Pullman's in the Detroit Publishing view, Tucker's
at 22nd Street in the Greene stereograph, the Ward engraving's at 20th) and in front of
houses mid-block (1811, opposite 1721, 1708, 1816, 1905, 2120, 2140), and Pullman's where
the 18th Street walk turns into Calumet Avenue (Taylor no. 16554, T-1934). So:

  * one lamp at every intersection corner of the district's drawn streets, on the parkway
    in the corner square where two sidewalk spaces meet, 1.5 ft inside both curbs: that is
    the curb-return corner, between where the two corner crossings land (Taylor 2135 shows
    it on a stone pad level with the walk between the two crossing ramps; the other corners
    have none, the Pullman and Tucker corners being grass), and clear of both walks;
  * the pictured mid-block lamps at their pictured lots, on the parkway just off the walk
    (the 1811, 1905 and 2120 photographs show them there);
  * and the rest of each face at a reconstructed spacing, about one per 160 ft, staggered
    across the street, moved along the parkway clear of an elm, a carriage walk or an
    alley mouth.

The post, read off 1811, Taylor 2135 and 2140: a fluted cast-iron column on a moulded
base, a ladder bar under the lantern, a four-sided lantern tapering out to its top, a
pyramidal cap and a finial; about 3 m. Every lamp is gas: the electric standards appear
only in pictures dated after 1904. The scene has no night, so no lamp is lit.

GRADES. A lamp a picture shows where it stands is attested; the rest are reconstructed,
recorded at docs/LIBERTIES.md L-prairie-street-lamps-3199. Deterministic: no randomness
but a fixed per-face phase, so a re-run lays the same lamps.

THE POLES AND WIRES (T-3202) stand clear of what is built (T-3225). The owner, 2026-10-28: "some
of the electrical poles and lines are intersecting with buildings". The tool lays every 1904
structure near a pole line (its baked model, git-carried, placed as buildings.js places it; a model
git does not carry, Glessner's, as its footprint walled to 15 m; the context city's kept blocks as
boxes) on a plan raster of heights, and holds each pole, its crossarm and each sagging wire clear of
it. It refuses to write a placement that runs into a structure, and --check refuses a committed file
that does, naming the pole or span and the structure:

    python3 tools/lay_prairie_1904_street_furniture.py --self-test   # breaks the clearance four ways
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "data" / "street_grid" / "1904.json"
SECTION = ROOT / "data" / "street_section" / "1904.json"
TREES = ROOT / "data" / "street_trees" / "1904.json"
SOURCES = ROOT / "data" / "sources"
OUT = ROOT / "data" / "street_furniture" / "1904.json"

FT = 0.3048
CORNER_INSET_FT = 1.5        # a corner lamp's centre, inside the parkway's curb edge on both streets
WALK_OFFSET_M = 0.40         # a mid-block lamp's centre, off the walk's outer edge (the 1811 photograph)
LAMP_SPACING_FT = 160.0      # about one per 150-200 ft per side, as the pictures' runs read
CORNER_CLEAR_M = 14.0        # no rule lamp this near a face's end (the corner lamp stands there)
ATTESTED_CLEAR_FRAC = 0.45   # a rule lamp within this share of a spacing of a pictured one gives way
TREE_CLEAR_M = 1.6           # plan distance from an elm's trunk
WALK_CLEAR_M = 0.6           # beyond a carriage walk's edge
ALLEY_CLEAR_M = 1.5          # beyond an alley mouth's edge
NUDGE_STEP_M = 0.25
NUDGE_MAX_M = 6.0
CORNER_MIN_SIN = math.sin(math.radians(45))   # two faces meeting at less than this are a curve, not a corner

# T-3219: the post as the 1811 photograph shows it whole and near (its heights scaled from the
# print to a 3.12 m lamp), checked against Taylor 2135 and 2140's second view.
LAMP = {
    "height_m": 3.12,
    "foot_m": {"r": 0.115, "plinth_r": 0.135, "to": 0.59},
    "collar_m": {"to": 0.7, "r": 0.12},
    "boss_m": {"to": 0.97, "r": 0.12, "leaves": 8},
    "shaft_r_m": [0.065, 0.055],
    "capital_m": {"from": 2.03, "to": 2.2, "r": 0.085},
    "ladder_bar_m": {"at": 2.23, "w": 0.36},
    "lantern_m": {"foot": 2.45, "top": 2.77, "w_foot": 0.17, "w_top": 0.44},
    "rim_m": {"w": 0.48, "h": 0.035},
    "roof_m": {"top": 3.03, "w_top": 0.1},
    "vent_m": {"w": 0.14, "h": 0.05},
    "footing_m": {"w": 0.8, "h": 0.02},
}

# T-1934: the one lamp no 1811-type post stands for, Pullman's at the 18th Street walk's turn into
# Calumet Avenue, as Taylor's no. 16554 shows it: a plain post about 4.9 m to its cap, painted pale
# (it prints lighter than the sunlit stone behind it), a small bar a third of the way down, a slim
# neck, a wide shallow globe with its top lit and its underside dark, and a small dark cap. Read
# off the print's column at x 795 (its foot at y 605, the cap's top at y 503, the globe y 507-515
# and 13 px wide, the bar at y 537), scaled by the district post's render at the same place
# (65 px for 3.12 m).
GLOBE_LAMP = {
    "height_m": 4.9,
    "base_m": {"r": 0.1, "to": 0.5},
    "shaft_r_m": [0.075, 0.06],
    "ladder_bar_m": {"at": 3.3, "w": 0.3},
    "neck_m": {"from": 3.95, "to": 4.33, "r": 0.04},
    "globe_m": {"centre": 4.52, "r": 0.29, "ry": 0.19},
    "cap_m": {"from": 4.7, "r": 0.08},
}
LAMP_BY_CLASS = {"globe_post": GLOBE_LAMP}

# The pictured corner lamps: (streets, the corner's quadrant of the crossing) -> what shows it.
ATTESTED_CORNERS = {
    (frozenset({"prairie", "e18th"}), "SW"): {
        "sources": ["taylor_2135_glessner_exterior_1887_1889"],
        "note": "The Glessner corner: J. W. Taylor's photograph no. 2135 (c. 1887-89) shows the post on a "
                "small stone footing at the curb corner, between the two crossing ramps.",
    },
    (frozenset({"prairie", "e18th"}), "NE"): {
        "sources": ["loc_det_4a08065_pullman_residence", "ghm_blog_pullman_completed"],
        "note": "The Pullman corner: the Detroit Publishing view (1890s) and the Glessner House Museum's halftone "
                "of the finished house show the post in a curbed grass plot at the curb corner.",
    },
    (frozenset({"prairie", "e22nd"}), "NW"): {
        "sources": ["nypl_dennis_tucker_1010_prairie_stereo"],
        "note": "The Tucker corner: P. B. Greene's stereograph (c. 1876-81) shows the post in a curbed grass plot "
                "at the curb corner; later photographs of the house show the same kind of lamp on its parkway.",
    },
    (frozenset({"prairie", "e20th"}), "NE"): {
        "sources": ["ghm_ward_1887_prairie_north_from_20th"],
        "note": "The Ward Bros. engraving of 1887, looking north from 20th Street, draws a lamp post at the "
                "east parkway's corner.",
    },
}

# T-3231: the one corner a picture shows on a stone pad (Taylor 2135, level with the walk
# between the crossing ramps). The owner doubted the raised footings once drawn at every
# corner; the Pullman and Tucker pictures show their posts in grass.
FOOTING_CORNERS = {(frozenset({"prairie", "e18th"}), "SW")}

# The pictured mid-block lamps: on Prairie Avenue's parkway at a lot, read off each picture.
# `at` is the share of the way along the lot's frontage from its north end. A lamp a picture
# puts on a face no lot's street side runs along (T-1934: the 18th Street walk's turn into
# Calumet Avenue) names its `face` and `at_m`, metres along it from its first point, instead.
ATTESTED_MIDBLOCK = [
    {"key": "1801_1811", "parcel": "prairie_1811", "at": 0.0,
     "sources": ["chicagology_1811_ames_photo"],
     "note": "The 1811 photograph shows the lamp on the parkway beside the walk at the house's north lot line "
             "(the same lamp stands at the right edge of the early photograph of 1801)."},
    {"key": "1708", "parcel": "prairie_1708", "at": 0.5,
     "sources": ["glessner_blog_1708_1706_1700_christmas_photo"],
     "note": "The Glessner townhouses photograph shows a street lamp in front of 1708, at the left of the row."},
    {"key": "opposite_1721", "parcel": "prairie_1720", "at": 0.8,
     "sources": ["ghm_blog_1721_dexter_c1888"],
     "note": "George Glessner's photograph of 1721 (c. 1888), taken from the west walk opposite it, has the "
             "lamp in its right foreground, a little south of the camera."},
    {"key": "1816_1824", "parcel": "prairie_1816", "at": 1.0,
     "sources": ["chicagology_1816_henderson_photo"],
     "note": "The 1816 photograph, taken from the walk south-east of the house, shows the lamp beyond the "
             "house's south flank, at its south lot line."},
    {"key": "1905", "parcel": "prairie_1905", "at": 0.3,
     "sources": ["chicagology_1905_field_photo"],
     "note": "The Field house photograph shows the lamp on the parkway beside the walk, before the house's "
             "north part."},
    {"key": "2120", "parcel": "prairie_2120", "at": 0.6,
     "sources": ["chicagology_2120_gorton_photo"],
     "note": "The 2120 photograph shows the lamp on the parkway beside the walk, just south of the stoop."},
    {"key": "2140", "parcel": "prairie_2140", "at": 0.3,
     "sources": ["chicagology_2140_photo_b"],
     "note": "The second 2140 photograph shows the lamp on the parkway beside the walk at the Prairie "
             "Avenue porch."},
    {"key": "pullman_court", "face": "calumet__prairie_ic_16_18", "at_m": 3.1, "parcel": "prairie_1729",
     "class": "globe_post",
     "sources": ["aic_taylor_16554_pullman_from_sw"],
     "note": "J. W. Taylor's photograph no. 16554 (1890s), from the yard across 18th Street, shows the post at "
             "the street edge of the walk before Pullman's palm-house wing, where the curb turns into Calumet "
             "Avenue (x 795, its foot at y 607: u 10.0 m east of the palm house's centre through the print's "
             "solved camera, data/reference_views/pullman_house_1729_prairie_conservatory/"
             "taylor_16554_from_south.json). Its form is read from the same print: a pale-painted post about "
             "4.9 m to its cap, taller than the district's, with a shallow globe for its head (the globe_post "
             "class, T-1934)."},
]

# Stretches of a face that pictures see whole and show no lamp on: the rule stands none there
# (T-1934). An empty stretch is a reading too, as it is for the parkway trees
# (data/street_trees/pictured_1904.json).
PICTURED_EMPTY = [
    {"face": "e18th__prairie_ic_16_18", "from_m": 0.0, "to_m": 62.92,
     "seen_by": ["aic_taylor_16554_pullman_from_sw", "loc_det_4a08066_pullman_residence"],
     "why": "Taylor's no. 16554 (1890s) sees 18th Street's north walk whole from the house's 18th Street "
            "porch to its turn into Calumet Avenue, and the Detroit Publishing view of c. 1900 sees it from "
            "the Prairie Avenue corner past the palm house: neither shows a post on it. The one lamp 16554 "
            "shows stands where the walk turns (lamp.pictured.pullman_court); the rule's mid-block lamp "
            "would have rendered before the porch's arch (16554 x 206), where the print shows none."},
]

# ---- the hydrants (T-3201) ----
HYDRANT_CORNER_ALONG_M = 3.5   # a corner hydrant's distance along its face from the block corner
HYDRANT_CURB_INSET_M = 0.45    # a hydrant's centre, inside the parkway's curb edge
HYDRANT_WALK_OFFSET_M = 0.35   # ...or off the walk's outer edge, where a picture puts it there
HYDRANT_LONG_FACE_M = 150.0    # a face at least this long takes a mid-block hydrant as well
HYDRANT_LAMP_CLEAR_M = 2.0     # plan distance from a lamp
HYDRANT_TREE_CLEAR_M = 1.8     # plan distance from an elm's trunk
CROSSING_CLEAR_M = 0.5         # beyond a corner crossing's strip (T-3200)
# Which corner of an intersection takes its hydrant, by the intersection's place in the
# district (west to east, then north to south): the four quadrants in turn.
CORNER_CYCLE = ["NE", "SW", "NW", "SE"]

HYDRANT = {
    "height_m": 0.85, "barrel_d_m": 0.21, "foot_d_m": 0.34, "band_at_m": 0.62,
    "nozzles_at_m": 0.5, "nozzle_d_m": 0.09,
}

# The pictured hydrants: on a face, `along_m` from its end at the street `end`, on the
# parkway's walk or curb side.
ATTESTED_HYDRANTS = [
    {"key": "pullman", "face": "prairie__prairie_ic_16_18", "end": "e18th", "along_m": 8.0, "side": "walk",
     "sources": ["loc_det_4a08065_pullman_residence", "ghm_blog_pullman_completed"],
     "note": ("Pullman's: the Detroit Publishing view and the Glessner House Museum's halftone of the finished "
              "house show a post hydrant on the Prairie Avenue parkway beside the walk, a few metres north of "
              "the corner lamp at 18th Street. Read off the owner's crop of the Detroit view: a barrel on a "
              "flared foot, a band under a domed bonnet with an operating nut, side nozzle caps. Not a "
              "hitching post: none is shown at Pullman's.")},
    {"key": "pullman_stable", "face": "calumet__prairie_ic_16_18", "end": None, "along_m": 14.2, "side": "walk",
     "sources": ["aic_taylor_16554_pullman_from_sw"],
     "note": ("Pullman's stable: J. W. Taylor's no. 16554 (1890s) shows a post hydrant on the walk at the foot "
              "of the low wall before the stable, about 3.7 m short of the stable's east end, where 18th "
              "Street's north walk turns into Calumet Avenue. Placed along its ray through the print's solved "
              "camera (x 1065 px), on the walk's street edge (T-1934, the owner, 2026-10-30: 'there is a "
              "hydrant in that photo'). Its form is the district's post hydrant; the print is too small to "
              "read its parts. Calumet Avenue curves into 18th Street here, so there is no corner: "
              "`end: None` measures from the face's own start, where 18th Street's face ends.")},
    {"key": "tucker", "face": "prairie__indiana_prairie_21_22", "end": "e22nd", "along_m": 6.0, "side": "curb",
     "sources": ["chicagology_2140_photo_b"],
     "note": ("Tucker's: the second 2140 photograph has a post hydrant of the same type in its left foreground, "
              "on the Prairie Avenue parkway toward 22nd Street.")},
]

STREET_ORDER = ["indiana", "prairie", "calumet", "e16th", "e18th", "e20th", "e21st", "e22nd"]


# --------------------------------------------------------------------------- geometry

def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def dot(p, q):
    return p[0] * q[0] + p[1] * q[1]


def unit(v):
    d = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / d, v[1] / d)


def bearing(t):
    """Compass bearing of a plan direction (east, north), degrees."""
    return math.degrees(math.atan2(t[0], t[1])) % 360


class Face:
    """A block face's street line as a polyline, with the side the street lies on."""

    def __init__(self, rec, xs):
        self.rec = rec
        self.id = rec["id"]
        self.street = rec["street"]
        self.block = rec["block"]
        self.line = [tuple(p) for p in rec["street_line_local_m"]]
        self.acc = [0.0]
        for p, q in zip(self.line, self.line[1:]):
            self.acc.append(self.acc[-1] + math.dist(p, q))
        self.length = self.acc[-1]
        bands = {b["band"]: b for b in xs["bands"]}
        self.walk_to = bands["walk"]["to_ft"] * FT
        self.park_from = bands["parkway"]["from_ft"] * FT
        self.park_to = bands["parkway"]["to_ft"] * FT
        # Which side of the line the street is: read off the first curb quad's middle.
        curb = rec["bands"]["curb"][0]
        mid = ((curb[0][0] + curb[2][0]) / 2, (curb[0][1] + curb[2][1]) / 2)
        a, b = self.line[0], self.line[1]
        t = unit(sub(b, a))
        n = (-t[1], t[0])
        self.sign = 1.0 if dot(sub(mid, a), n) >= 0 else -1.0

    def seg(self, s):
        for i in range(1, len(self.line)):
            if s <= self.acc[i] or i == len(self.line) - 1:
                return i
        return len(self.line) - 1

    def frame(self, s):
        """(point on the line, tangent, outward normal) at distance s along it."""
        i = self.seg(s)
        a, b = self.line[i - 1], self.line[i]
        L = (self.acc[i] - self.acc[i - 1]) or 1.0
        f = (s - self.acc[i - 1]) / L
        p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        t = unit(sub(b, a))
        n = (-t[1] * self.sign, t[0] * self.sign)
        return p, t, n

    def at(self, s, across):
        p, t, n = self.frame(s)
        return (p[0] + n[0] * across, p[1] + n[1] * across), t

    def project(self, q):
        """(distance along, signed distance across toward the street) of q."""
        best = (float("inf"), 0.0, 0.0)
        for i in range(1, len(self.line)):
            a, b = self.line[i - 1], self.line[i]
            v = sub(b, a)
            L2 = dot(v, v) or 1.0
            u = max(0.0, min(1.0, dot(sub(q, a), v) / L2))
            p = (a[0] + v[0] * u, a[1] + v[1] * u)
            d = math.dist(p, q)
            if d < best[0]:
                t = unit(v)
                n = (-t[1] * self.sign, t[0] * self.sign)
                best = (d, self.acc[i - 1] + math.sqrt(L2) * u, dot(sub(q, a), n))
        return best[1], best[2]

    def end_frame(self, which):
        """The corner end of the face: its point and the tangent pointing INTO the face."""
        if which == 0:
            return self.line[0], unit(sub(self.line[1], self.line[0]))
        return self.line[-1], unit(sub(self.line[-2], self.line[-1]))


def quadrant(v):
    """The compass quadrant a plan direction points to."""
    return ("N" if v[1] >= 0 else "S") + ("E" if v[0] >= 0 else "W")


def solve2(n1, d1, n2, d2):
    """x with x.n1 = d1 and x.n2 = d2."""
    det = n1[0] * n2[1] - n1[1] * n2[0]
    return ((d1 * n2[1] - d2 * n1[1]) / det, (n1[0] * d2 - n2[0] * d1) / det)


def r2(x):
    return round(x, 2)


# --------------------------------------------------------------------------- clearances

def blocked_intervals(face, section_walks, alleys):
    """Intervals along the face a lamp may not stand in: carriage walks and alley mouths."""
    out = []
    for w in section_walks.get(face.id, []):
        s, _ = face.project(tuple(w["at"]))
        half = w["width_ft"] * FT / 2 + WALK_CLEAR_M
        out.append((s - half, s + half, "carriage walk"))
    for al in alleys:
        hits = [face.project(tuple(p)) for p in al["polygon_local_m"]]
        near = [s for s, across in hits if abs(across) < 8.0 and -1.0 < s < face.length + 1.0]
        if len(near) >= 2:
            out.append((min(near) - ALLEY_CLEAR_M, max(near) + ALLEY_CLEAR_M, "alley"))
    return out


def clear_spot(face, s, across, blocked, trees, lo, hi):
    """The nearest place along the face to s, within [lo, hi], clear of the blocked
    intervals and of every elm trunk; None when there is none within NUDGE_MAX_M."""
    def ok(x):
        if not lo <= x <= hi:
            return False
        if any(a < x < b for a, b, _ in blocked):
            return False
        p, _ = face.at(x, across)
        return all(math.dist(p, t) >= TREE_CLEAR_M for t in trees)
    k = 0
    while k * NUDGE_STEP_M <= NUDGE_MAX_M:
        for x in ((s,) if k == 0 else (s + k * NUDGE_STEP_M, s - k * NUDGE_STEP_M)):
            if ok(x):
                return x
        k += 1
    return None


# --------------------------------------------------------------------------- the lamps

def source_lines(ids):
    out = {}
    for sid in sorted(set(ids)):
        rec = json.loads((SOURCES / f"{sid}.json").read_text())
        out[sid] = {k: rec[k] for k in ("citation", "url", "tier", "date") if rec.get(k) is not None}
    return out


def corners(faces):
    """Every intersection corner where two faces of one block meet at an angle."""
    by_block = {}
    for f in faces.values():
        by_block.setdefault(f.block, []).append(f)
    out = []
    for block, fs in sorted(by_block.items()):
        for i, A in enumerate(fs):
            for B in fs[i + 1:]:
                for ea in (0, 1):
                    for eb in (0, 1):
                        pa, ta = A.end_frame(ea)
                        pb, tb = B.end_frame(eb)
                        if math.dist(pa, pb) > 1.0:
                            continue
                        if abs(ta[0] * tb[1] - ta[1] * tb[0]) < CORNER_MIN_SIN:
                            continue   # a curved return (Calumet at 18th), not a corner
                        O = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                        _, _, na = A.frame(0.0 if ea == 0 else A.length)
                        _, _, nb = B.frame(0.0 if eb == 0 else B.length)
                        da = A.park_to - CORNER_INSET_FT * FT
                        db = B.park_to - CORNER_INSET_FT * FT
                        x = solve2(na, da, nb, db)
                        P = (O[0] + x[0], O[1] + x[1])
                        # The lamp stands in the crossing's corner opposite the way it lies from the block.
                        q = quadrant((-x[0], -x[1]))
                        streets = sorted([A.street, B.street], key=STREET_ORDER.index)
                        out.append({"faces": (A, B), "O": O, "P": P, "quadrant": q, "streets": streets,
                                    "heading": bearing(ta if A.street == streets[0] else tb)})
    return out


def lay_lamps(grid, section, trees_doc):
    xs = grid["cross_sections"]
    faces = {f["id"]: Face(f, xs[f["cross_section"]]) for f in grid["faces"]}
    parcels = {p["id"]: p for p in grid["parcels"]}
    walks = {}
    for w in (section or {}).get("carriage_walks", {}).get("walks", []):
        walks.setdefault(w["face"], []).append(w)
    trees_by_face = {}
    for t in (trees_doc or {}).get("trees", []):
        trees_by_face.setdefault(t["face"], []).append((t["e"], t["n"]))
    all_trees = [p for v in trees_by_face.values() for p in v]

    items = []
    # 1. The corners.
    for c in corners(faces):
        key = (frozenset(c["streets"]), c["quadrant"])
        att = ATTESTED_CORNERS.get(key)
        P = c["P"]
        cid = f"lamp.corner.{c['streets'][0]}.{c['streets'][1]}.{c['quadrant'].lower()}"
        item = {
            "id": cid, "kind": "gas_lamp", "e": r2(P[0]), "n": r2(P[1]),
            "heading_deg": round(c["heading"], 1), "footing": key in FOOTING_CORNERS,
            "place": "corner", "streets": c["streets"], "corner": c["quadrant"],
            "faces": sorted(f.id for f in c["faces"]),
            "grade": "attested" if att else "reconstructed",
            "sources": att["sources"] if att else [],
        }
        if att:
            item["note"] = att["note"]
        else:
            item["liberty"] = "L-prairie-street-lamps-3199"
        items.append(item)
    seen = {}
    for it in items:
        if it["id"] in seen:
            raise SystemExit(f"street furniture: two corners named {it['id']}")
        seen[it["id"]] = it
    unused = [k for k in ATTESTED_CORNERS if not any(
        frozenset(i.get("streets", [])) == k[0] and i.get("corner") == k[1] for i in items)]
    if unused:
        raise SystemExit(f"street furniture: a pictured corner lamp found no corner: {unused}")

    # 2. The pictured mid-block lamps, at their lots.
    pinned = {}
    for m in ATTESTED_MIDBLOCK:
        p = parcels[m["parcel"]]
        if "face" in m:
            face = faces[m["face"]]
            s = m["at_m"]
        else:
            face = faces[p["street_face"]]
            ends = [tuple(v) for k, v in p["corners_local_m"].items() if k.endswith("_street")]
            north, south = sorted(ends, key=lambda v: -v[1])
            q = (north[0] + (south[0] - north[0]) * m["at"], north[1] + (south[1] - north[1]) * m["at"])
            s, _ = face.project(q)
        across = face.walk_to + WALK_OFFSET_M
        blocked = blocked_intervals(face, walks, grid.get("alleys", []))
        s2 = clear_spot(face, s, across, blocked, trees_by_face.get(face.id, []), 0.0, face.length)
        if s2 is None:
            raise SystemExit(f"street furniture: no clear spot for the pictured lamp {m['key']}")
        P, t = face.at(s2, across)
        item = {
            "id": f"lamp.pictured.{m['key']}", "kind": "gas_lamp", "e": r2(P[0]), "n": r2(P[1]),
            "heading_deg": round(bearing(t), 1), "footing": False,
            "place": "mid-block", "face": face.id, "parcel": p["id"],
            "grade": "attested", "sources": m["sources"], "note": m["note"],
            "moved_m": r2(abs(s2 - s)),
        }
        if "class" in m:
            if m["class"] not in LAMP_BY_CLASS:
                raise SystemExit(f"street furniture: the pictured lamp {m['key']} names no lamp class {m['class']}")
            item["class"] = m["class"]
        items.append(item)
        pinned.setdefault(face.id, []).append(s2)

    # 3. The rest of each face, at the reconstructed spacing, staggered across the street.
    spacing = LAMP_SPACING_FT * FT
    for fid in sorted(faces):
        face = faces[fid]
        usable = face.length - 2 * CORNER_CLEAR_M
        if usable <= spacing * 0.5:
            continue
        # Faces on the street's north or east side take the half-step: the two files alternate.
        _, _, n0 = face.frame(face.length / 2)
        half = 0.5 if (n0[0] < -0.5 or n0[1] < -0.5) else 0.0
        k = max(1, round(face.length / spacing))
        step = face.length / k
        targets = [step * (i + half) for i in range(0 if half else 1, k + (1 if half else 0))]
        across = face.walk_to + WALK_OFFSET_M
        blocked = blocked_intervals(face, walks, grid.get("alleys", []))
        trees = trees_by_face.get(face.id, [])
        for j, s in enumerate(targets):
            if not CORNER_CLEAR_M <= s <= face.length - CORNER_CLEAR_M:
                continue
            if any(abs(s - x) < ATTESTED_CLEAR_FRAC * step for x in pinned.get(fid, [])):
                continue
            if any(e["face"] == fid and e["from_m"] <= s <= e["to_m"] for e in PICTURED_EMPTY):
                continue
            s2 = clear_spot(face, s, across, blocked, trees, CORNER_CLEAR_M, face.length - CORNER_CLEAR_M)
            if s2 is None:
                continue
            P, t = face.at(s2, across)
            items.append({
                "id": f"lamp.rule.{fid}#{j:02d}", "kind": "gas_lamp", "e": r2(P[0]), "n": r2(P[1]),
                "heading_deg": round(bearing(t), 1), "footing": False,
                "place": "mid-block", "face": fid,
                "grade": "reconstructed", "sources": [], "liberty": "L-prairie-street-lamps-3199",
            })
    # A last guard: nothing stands within a trunk's reach, whatever placed it.
    for it in items:
        for t in all_trees:
            if math.dist((it["e"], it["n"]), t) < 1.0:
                raise SystemExit(f"street furniture: {it['id']} stands in an elm at {t}")
    return items


def poly_dist(q, poly):
    """Plan distance from q to a polygon: 0 inside it."""
    inside = False
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        if (a[1] > q[1]) != (b[1] > q[1]) and q[0] < a[0] + (q[1] - a[1]) * (b[0] - a[0]) / ((b[1] - a[1]) or 1e-12):
            inside = not inside
    if inside:
        return 0.0
    best = float("inf")
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        v = sub(b, a)
        L2 = dot(v, v) or 1.0
        u = max(0.0, min(1.0, dot(sub(q, a), v) / L2))
        best = min(best, math.dist(q, (a[0] + v[0] * u, a[1] + v[1] * u)))
    return best


def crossing_polys(section):
    """The corner crossings' strips (T-3200), flat and ramp, when the section carries them."""
    out = []
    cc = (section or {}).get("corner_crossings") or []
    if isinstance(cc, dict):  # the section writes {ticket, liberty, ..., crossings: [...]}
        cc = cc.get("crossings") or []
    for c in cc:
        for k in ("flat", "ramp"):
            q = c.get(k)
            if q and len(q) >= 3:
                out.append([tuple(p) for p in q])
    return out


def face_end_s(face, corner):
    """Distance along `face` of its end at a corner, and the sign that walks away from it."""
    if math.dist(face.line[0], corner["O"]) <= math.dist(face.line[-1], corner["O"]):
        return 0.0, 1.0
    return face.length, -1.0


def lay_hydrants(grid, section, trees_doc, lamps):
    xs = grid["cross_sections"]
    faces = {f["id"]: Face(f, xs[f["cross_section"]]) for f in grid["faces"]}
    walks = {}
    for w in (section or {}).get("carriage_walks", {}).get("walks", []):
        walks.setdefault(w["face"], []).append(w)
    trees = [(t["e"], t["n"]) for t in (trees_doc or {}).get("trees", [])]
    lamp_at = [(i["e"], i["n"]) for i in lamps]
    crossings = crossing_polys(section)
    alleys = grid.get("alleys", [])
    cs = corners(faces)

    def clear(face, s, across, blocked, lo, hi, step_sign=0):
        """The nearest clear spot along the face to s (or only away from a corner, step_sign)."""
        k = 0
        while k * NUDGE_STEP_M <= NUDGE_MAX_M:
            cands = (s,) if k == 0 else ((s + step_sign * k * NUDGE_STEP_M,) if step_sign
                                         else (s + k * NUDGE_STEP_M, s - k * NUDGE_STEP_M))
            for x in cands:
                if not lo <= x <= hi or any(a < x < b for a, b, _ in blocked):
                    continue
                p, _ = face.at(x, across)
                if any(math.dist(p, t) < HYDRANT_TREE_CLEAR_M for t in trees):
                    continue
                if any(math.dist(p, t) < HYDRANT_LAMP_CLEAR_M for t in lamp_at):
                    continue
                if any(poly_dist(p, c) < CROSSING_CLEAR_M for c in crossings):
                    continue
                return x
            k += 1
        return None

    def item(hid, f, s, across, **kw):
        P, t = f.at(s, across)
        return {"id": hid, "kind": "fire_hydrant", "e": r2(P[0]), "n": r2(P[1]),
                "heading_deg": round(bearing(t), 1), **kw}

    items = []
    taken = set()
    # 1. The pictured ones.
    for h in ATTESTED_HYDRANTS:
        face = faces[h["face"]]
        if h["end"] is None:
            # a face with no corner at this end (a street curving into the next): from its start
            c, s0, sign = None, 0.0, 1.0
        else:
            c = next(c for c in cs if face in c["faces"] and h["end"] in c["streets"])
            s0, sign = face_end_s(face, c)
        across = (face.walk_to + HYDRANT_WALK_OFFSET_M) if h["side"] == "walk" else (face.park_to - HYDRANT_CURB_INSET_M)
        blocked = blocked_intervals(face, walks, alleys)
        s = clear(face, s0 + sign * h["along_m"], across, blocked, 0.0, face.length)
        if s is None:
            raise SystemExit(f"street furniture: no clear spot for the pictured hydrant {h['key']}")
        where = {"place": "corner", "streets": c["streets"], "corner": c["quadrant"]} if c else \
            {"place": "mid-block"}
        items.append(item(f"hydrant.pictured.{h['key']}", face, s, across, **where, face=face.id, grade="attested",
                          sources=h["sources"], note=h["note"],
                          moved_m=r2(abs(s - (s0 + sign * h["along_m"])))))
        if c:
            taken.add(frozenset(c["streets"]))
    # 2. One per intersection, at a corner taken in turn, along the avenue's face.
    by_x = {}
    for c in cs:
        by_x.setdefault(tuple(c["streets"]), []).append(c)
    order = sorted(by_x, key=lambda k: (STREET_ORDER.index(k[1]), STREET_ORDER.index(k[0])))
    for idx, key in enumerate(order):
        if frozenset(key) in taken:
            continue
        here = {c["quadrant"]: c for c in by_x[key]}
        want = next((q for j in range(4) for q in [CORNER_CYCLE[(idx + j) % 4]] if q in here), None)
        c = here[want]
        A, B = c["faces"]
        face = A if A.street == key[0] else B          # the avenue's face (Indiana, Prairie, Calumet)
        s0, sign = face_end_s(face, c)
        across = face.park_to - HYDRANT_CURB_INSET_M
        blocked = blocked_intervals(face, walks, alleys)
        lo, hi = (0.0, face.length)
        s = clear(face, s0 + sign * HYDRANT_CORNER_ALONG_M, across, blocked, lo, hi, step_sign=sign)
        if s is None:
            continue
        items.append(item(f"hydrant.corner.{key[0]}.{key[1]}.{want.lower()}", face, s, across, place="corner",
                          streets=list(key), corner=want, face=face.id, grade="reconstructed", sources=[],
                          liberty="L-prairie-hydrants-3201"))
    # 3. Mid-block on the long faces, one side of each street.
    for fid in sorted(faces):
        face = faces[fid]
        if face.length < HYDRANT_LONG_FACE_M:
            continue
        _, _, n0 = face.frame(face.length / 2)
        if not (n0[0] < -0.5 or n0[1] < -0.5):
            continue
        across = face.park_to - HYDRANT_CURB_INSET_M
        blocked = blocked_intervals(face, walks, alleys)
        s = clear(face, face.length / 2, across, blocked, CORNER_CLEAR_M, face.length - CORNER_CLEAR_M)
        if s is None:
            continue
        items.append(item(f"hydrant.mid.{fid}", face, s, across, place="mid-block", face=fid,
                          grade="reconstructed", sources=[], liberty="L-prairie-hydrants-3201"))
    return items


# --------------------------------------------------------------------------- the poles and wires (T-3202)

POLE_SPACING_M = 34.0          # about 110 ft between poles on a line
POLE_CURB_INSET_M = 0.35       # a street pole's centre, inside the parkway's curb edge
POLE_ALLEY_INSET_M = 0.45      # an alley pole's centre, inside the alley's edge
POLE_MOUTH_IN_M = 2.5          # an alley line's end pole, in from the alley's mouth
POLE_TREE_CLEAR_M = 1.5        # plan distance from an elm's trunk
POLE_ITEM_CLEAR_M = 1.5        # plan distance from a lamp or a hydrant
ALLEY_LINE_JOIN_M = 12.0       # two alley ends this near across a street are one line, spanned over it

POLE = {
    "street": {"height_m": 10.5, "butt_d_m": 0.30, "top_d_m": 0.19, "arms": 1, "pins": 6,
               "arm_len_m": 2.4, "arm_below_top_m": 0.45},
    # The alley poles are drawn as Glessner's, the one line pole pictured (and so share its draws).
    "alley": {"height_m": 10.5, "butt_d_m": 0.30, "top_d_m": 0.19, "arms": 1, "pins": 6,
              "arm_len_m": 2.4, "arm_below_top_m": 0.45},
    "trolley": {"height_m": 9.0, "butt_d_m": 0.28, "top_d_m": 0.19, "arms": 0, "pins": 0,
                "span_at_m": 6.6},
}
WIRE_SAG_FRAC = 0.012          # a line wire's sag, as a share of its span
TROLLEY = {"contact_h_m": 5.6, "contact_gap_m": 3.0, "span_sag_m": 0.35}

# Glessner's pole: the c. 1887 photograph from the north-west shows a pole with a crossarm of
# about six pins on the 18th Street parkway at the stable's north-west corner, by the alley.
GLESSNER_POLE = {"face": "e18th__indiana_prairie_18_20", "alley": "alley_indiana_prairie_18_20",
                 "past_alley_m": 2.0, "sources": ["cornell_adw_glessner_stable_1887"]}
# 18th Street's line runs west from Glessner's pole to Indiana Avenue; Taylor 2135 and the
# Detroit view show no pole on 18th Street east of the alley.
POLE_18TH_NOTE_SOURCES = ["taylor_2135_glessner_exterior_1887_1889", "loc_det_4a08065_pullman_residence"]
TROLLEY_SOURCES = ["chicagology_2140_photo_a"]
TROLLEY_FACES = ["e22nd__indiana_prairie_21_22", "e22nd__prairie_calumet_21_22"]
STREET_WIDTH_FT = {"row_66": 66.0, "row_50": 50.0}


def alley_edges(al):
    """The alley's two long edges as polylines, north to south: (west, east)."""
    qs = al["quads_local_m"]
    west = [tuple(qs[0][0])] + [tuple(q[1]) for q in qs]
    east = [tuple(qs[0][3])] + [tuple(q[2]) for q in qs]
    if west[0][1] < west[-1][1]:
        west.reverse(); east.reverse()
    return west, east


def poly_len(pl):
    return sum(math.dist(a, b) for a, b in zip(pl, pl[1:]))


def poly_at(pl, s):
    """Point and unit tangent at distance s along a polyline."""
    acc = 0.0
    for a, b in zip(pl, pl[1:]):
        L = math.dist(a, b)
        if s <= acc + L or b == pl[-1]:
            f = (s - acc) / (L or 1.0)
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), unit(sub(b, a))
        acc += L
    return pl[-1], unit(sub(pl[-1], pl[-2]))


# --------------------------------------------------------------------------- what the poles stand clear of (T-3225)
#
# The owner, 2026-10-28, from an alley in the dev preview: "some of the electrical poles and lines
# are intersecting with buildings". T-3202 kept the poles clear of the elms, lamps and hydrants
# and of nothing built, so an alley pole 0.45 m inside the alley stood with its 2.4 m crossarm in
# the gable of Glessner's coach house, and the wires, hung from that arm's outer pins 0.7 m over
# the lot line, ran through the coach houses that stand on it. Everything below asks the question
# of the structures' own baked models.

BUILT_RES_M = 0.25             # the plan raster of what is built, metres a cell
BUILT_FLAT_M = 0.12            # a triangle wholly below this lies on the ground (a walk, a yard)
POLE_BODY_CLEAR_M = 0.15       # a pole's face from any wall, fence, stoop or roof edge
ARM_CLEAR_M = 0.30             # a crossarm (and its insulators) over the highest roof beneath it
WIRE_CLEAR_M = 0.30            # a wire over the highest roof, wall or fence beneath it
UNTRACKED_TOP_M = 15.0         # a model git does not carry stands as its footprint, this tall...
UNTRACKED_PAD_M = 0.6          # ...and this much wider, for the eaves and copings the footprint leaves out
ALLEY_INSETS_M = (0.45, 0.9, 1.4, 1.9, 2.4)   # an alley pole's offset inside its edge, the first first
ALLEY_SLIDES_M = tuple(x * sgn for x in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0) for sgn in (1, -1))
INSET_COST = 2.0               # a metre further into the alley weighs as two metres along it
OTHER_SIDE_COST = 8.0          # the alley's west side, only where the east side cannot take the pole
SIDECARS = ROOT / "data" / "sidecars" / "1904"
ASSETS = ROOT / "assets"
CONTEXT = ROOT / "data" / "context" / "1904.json"
CLEARANCE_NOTE = ("No pole, crossarm or wire touches a 1904 structure (T-3225): tested on the baked models and "
                  "the context city's blocks as a plan raster of their heights, a pole's face 0.15 m off any wall, "
                  "fence or roof edge, a crossarm 0.3 m over the roof beneath it, every wire 0.3 m over whatever it "
                  "crosses as it sags. An alley pole the rule puts into a coach house slides along the alley, then "
                  "stands further into it, then crosses to its west side; a span through a building steps its "
                  "poles further in, or is not hung. `moved` lists the poles off the rule's spot, "
                  "`spans_not_hung` the spans left out.")


def read_glb(path):
    """Each primitive's material name, positions (x, y, z) and triangles, from a binary glTF."""
    import struct
    import numpy as np
    b = path.read_bytes()
    jlen = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack("<I", b[off:off + 4])[0]
    binc = b[off + 8:off + 8 + blen]
    mats = [m.get("name", "") for m in j.get("materials", [])]

    def acc(i):
        a = j["accessors"][i]
        v = j["bufferViews"][a["bufferView"]]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 0)
        if stride and stride != n * np.dtype(dt).itemsize:
            raw = np.frombuffer(binc, np.uint8, count=stride * a["count"], offset=start).reshape(a["count"], stride)
            return raw[:, :n * np.dtype(dt).itemsize].copy().view(dt).reshape(a["count"], n)
        return np.frombuffer(binc, dt, count=a["count"] * n, offset=start).reshape(a["count"], n)

    out = []
    for node in j.get("nodes", []):
        if "mesh" not in node:
            continue
        for p in j["meshes"][node["mesh"]]["primitives"]:
            if p.get("mode", 4) != 4:
                continue
            pos = acc(p["attributes"]["POSITION"]).astype(np.float64)
            idx = acc(p["indices"]).reshape(-1, 3).astype(np.int64) if "indices" in p else \
                np.arange(len(pos)).reshape(-1, 3)
            out.append((mats[p["material"]] if "material" in p else "", pos, idx))
    return out


class Built:
    """The 1904 structures near the pole lines, as plan rasters of the highest point built over
    each cell (metres above the structure's own ground). One raster per region: each alley and
    the street faces that carry poles, each widened to take the poles, their arms and the wires.

    A structure is its baked model (data/sidecars/1904/<id>.json -> assets/<asset>, placed by
    local_e, local_n and rotation_deg exactly as renderers/web/js/buildings.js places it: the
    bearing turns it CLOCKWISE). A model git does not carry (Glessner's, rebuilt from its recovery
    package by publish.sh) is read from its sidecar footprint instead, walled to UNTRACKED_TOP_M
    and padded by UNTRACKED_PAD_M, so the tool writes the same file on every checkout."""

    def __init__(self, rects):
        import numpy as np
        self.np = np
        self.rects = []
        for e0, n0, e1, n1 in rects:
            w = int(math.ceil((e1 - e0) / BUILT_RES_M))
            h = int(math.ceil((n1 - n0) / BUILT_RES_M))
            self.rects.append((e0, n0, e1, n1, np.zeros((h, w), np.float32), np.full((h, w), -1, np.int32)))
        self.names = []

    def _sid(self, name):
        self.names.append(name)
        return len(self.names) - 1

    def touches(self, e0, n0, e1, n1):
        return any(e0 <= r[2] and e1 >= r[0] and n0 <= r[3] and n1 >= r[1] for r in self.rects)

    def lay_points(self, sid, pts):
        """pts: (N, 3) world e, n, height."""
        np = self.np
        for e0, n0, e1, n1, top, who in self.rects:
            c = np.floor((pts[:, 0] - e0) / BUILT_RES_M).astype(np.int64)
            r = np.floor((pts[:, 1] - n0) / BUILT_RES_M).astype(np.int64)
            ok = (c >= 0) & (c < top.shape[1]) & (r >= 0) & (r < top.shape[0])
            if not ok.any():
                continue
            c, r, z = c[ok], r[ok], pts[ok, 2].astype(np.float32)
            np.maximum.at(top, (r, c), z)
            who[r[top[r, c] == z], c[top[r, c] == z]] = sid

    def lay_model(self, name, place, prims):
        np = self.np
        d = math.radians(place.get("rotation_deg") or 0.0)
        cd, sd = math.cos(d), math.sin(d)
        e, n = place["local_e"], place["local_n"]
        sid = None
        for mat, pos, idx in prims:
            if any(g in mat.lower() for g in ("turf", "earth", "lawn", "grass")):
                continue
            we = e + pos[:, 0] * cd - pos[:, 2] * sd
            wn = n - pos[:, 0] * sd - pos[:, 2] * cd
            tri = np.stack([we, wn, pos[:, 1]], axis=1)[idx]          # (T, 3 corners, e n y)
            tri = tri[tri[:, :, 2].max(axis=1) > BUILT_FLAT_M]
            if not len(tri):
                continue
            lo, hi = tri[:, :, :2].min(axis=1), tri[:, :, :2].max(axis=1)
            near = np.zeros(len(tri), bool)
            for e0, n0, e1, n1, _, _ in self.rects:
                near |= (lo[:, 0] <= e1) & (hi[:, 0] >= e0) & (lo[:, 1] <= n1) & (hi[:, 1] >= n0)
            tri = tri[near]
            if not len(tri):
                continue
            if sid is None:
                sid = self._sid(name)
            a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
            edge = np.max(np.stack([np.hypot(*(b - a)[:, :2].T), np.hypot(*(c - b)[:, :2].T),
                                    np.hypot(*(a - c)[:, :2].T)]), axis=0)
            k = np.clip(np.ceil(edge / (BUILT_RES_M * 0.7)).astype(int), 1, 400)
            for kk in np.unique(k):
                sel = k == kk
                uu, vv = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1))
                keep = (uu + vv) <= kk
                u, v = uu[keep] / kk, vv[keep] / kk
                w = 1 - u - v
                pts = (a[sel, None] * w[None, :, None] + b[sel, None] * u[None, :, None]
                       + c[sel, None] * v[None, :, None])
                self.lay_points(sid, pts.reshape(-1, 3))

    def lay_prism(self, name, poly, top_m, pad_m):
        """A footprint walled to top_m, widened by pad_m."""
        np = self.np
        P = np.asarray(poly, float)
        sid = None
        for e0, n0, e1, n1, top, who in self.rects:
            lo, hi = P.min(axis=0) - pad_m, P.max(axis=0) + pad_m
            c0, r0 = max(0, int((lo[0] - e0) / BUILT_RES_M)), max(0, int((lo[1] - n0) / BUILT_RES_M))
            c1 = min(top.shape[1], int((hi[0] - e0) / BUILT_RES_M) + 1)
            r1 = min(top.shape[0], int((hi[1] - n0) / BUILT_RES_M) + 1)
            if c1 <= c0 or r1 <= r0:
                continue
            rr, cc = np.mgrid[r0:r1, c0:c1]
            pe, pn = e0 + (cc + 0.5) * BUILT_RES_M, n0 + (rr + 0.5) * BUILT_RES_M
            inside = np.zeros(pe.shape, bool)
            dist = np.full(pe.shape, np.inf)
            for i in range(len(P)):
                (ae, an), (be, bn) = P[i - 1], P[i]
                cross = ((an > pn) != (bn > pn)) & (pe < ae + (pn - an) * (be - ae) / ((bn - an) or 1e-12))
                inside ^= cross
                ve, vn = be - ae, bn - an
                L2 = ve * ve + vn * vn or 1.0
                u = np.clip(((pe - ae) * ve + (pn - an) * vn) / L2, 0.0, 1.0)
                dist = np.minimum(dist, np.hypot(pe - (ae + ve * u), pn - (an + vn * u)))
            m = inside | (dist <= pad_m)
            if not m.any():
                continue
            if sid is None:
                sid = self._sid(name)
            sub_top = top[r0:r1, c0:c1]
            sub_who = who[r0:r1, c0:c1]
            upd = m & (sub_top < top_m)
            sub_top[upd] = top_m
            sub_who[upd] = sid

    def top_at(self, pts, radius=0.0):
        """The highest point built within `radius` of each plan point: (heights, structure ids)."""
        np = self.np
        pts = np.asarray(pts, float).reshape(-1, 2)
        best = np.zeros(len(pts), np.float32)
        bwho = np.full(len(pts), -1, np.int32)
        k = int(math.ceil(radius / BUILT_RES_M))
        offs = [(dx * BUILT_RES_M, dy * BUILT_RES_M) for dx in range(-k, k + 1) for dy in range(-k, k + 1)
                if (dx * dx + dy * dy) * BUILT_RES_M ** 2 <= (radius + BUILT_RES_M * 0.71) ** 2]
        for dx, dy in offs:
            q = pts + (dx, dy)
            for e0, n0, e1, n1, top, who in self.rects:
                c = np.floor((q[:, 0] - e0) / BUILT_RES_M).astype(np.int64)
                r = np.floor((q[:, 1] - n0) / BUILT_RES_M).astype(np.int64)
                ok = (c >= 0) & (c < top.shape[1]) & (r >= 0) & (r < top.shape[0])
                h = np.zeros(len(q), np.float32)
                w = np.full(len(q), -1, np.int32)
                h[ok] = top[r[ok], c[ok]]
                w[ok] = who[r[ok], c[ok]]
                up = h > best
                best[up] = h[up]
                bwho[up] = w[up]
        return best, bwho

    def name(self, sid):
        return self.names[sid] if sid >= 0 else "?"


def tracked_assets():
    import subprocess
    try:
        out = subprocess.run(["git", "ls-files", "-z", "assets"], cwd=ROOT, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return {s for s in out.stdout.decode().split("\0") if s}


def pole_regions(grid):
    """Where poles, arms and wires can be: each alley widened 5 m, the pole faces' street widened."""
    xs = grid["cross_sections"]
    faces = {f["id"]: Face(f, xs[f["cross_section"]]) for f in grid["faces"]}
    rects = []
    for al in grid.get("alleys", []):
        P = al["polygon_local_m"]
        es, ns = [p[0] for p in P], [p[1] for p in P]
        rects.append((min(es) - 5.0, min(ns) - 5.0, max(es) + 5.0, max(ns) + 5.0))
    for fid in [GLESSNER_POLE["face"]] + TROLLEY_FACES:
        f = faces[fid]
        width = STREET_WIDTH_FT[f.rec["cross_section"]] * FT
        pts = [f.at(s, a)[0] for s in (0.0, f.length) for a in (-4.0, width + 4.0)]
        es, ns = [p[0] for p in pts], [p[1] for p in pts]
        rects.append((min(es), min(ns), max(es), max(ns)))
    return rects


def in_poly(q, poly):
    inside = False
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        if (a[1] > q[1]) != (b[1] > q[1]) and q[0] < a[0] + (q[1] - a[1]) * (b[0] - a[0]) / ((b[1] - a[1]) or 1e-12):
            inside = not inside
    return inside


def context_box(e, n, w, d, bearing, grow=0.0):
    """A context building's plan rectangle, as renderers/web/js/context.js corners()."""
    t = math.radians(bearing)
    u = (math.sin(t), math.cos(t))
    v = (u[1], -u[0])
    hd, hw = d / 2 + grow, w / 2 + grow
    return [(e + su * u[0] * hd + sv * v[0] * hw, n + su * u[1] * hd + sv * v[1] * hw)
            for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1))]


def lay_built(grid):
    """Every 1904 structure that reaches a pole region, on a Built raster: the placed models, and
    the faded context city's stand-in blocks (data/context/1904.json) the renderer keeps, each as
    its box walled to its eave and roof rise."""
    built = Built(pole_regions(grid))
    tracked = tracked_assets()
    footprints = []
    for f in sorted(SIDECARS.glob("*.json")):
        sc = json.loads(f.read_text())
        pl = sc.get("placement") or {}
        if "asset" not in sc or pl.get("local_e") is None:
            continue
        fp = (sc.get("footprint") or {}).get("polygon") or []
        th = math.radians(float(pl.get("rotation_deg") or 0.0))
        cth, sth = math.cos(th), math.sin(th)
        world = [(pl["local_e"] + u * cth + v * sth, pl["local_n"] - u * sth + v * cth) for u, v in fp]
        if len(world) >= 3:
            footprints.append(world)
        glb = ASSETS / sc["asset"]
        carried = tracked is not None and f"assets/{sc['asset']}" in tracked and glb.exists()
        if carried:
            prims = read_glb(glb)
            # a cheap first look: the model's own reach about its anchor
            r = max((float(built.np.abs(p[:, [0, 2]]).max()) for _, p, _ in prims if len(p)), default=0.0)
            if not built.touches(pl["local_e"] - r, pl["local_n"] - r, pl["local_e"] + r, pl["local_n"] + r):
                continue
            built.lay_model(sc["id"], pl, prims)
        elif len(world) >= 3:
            built.lay_prism(sc["id"], world, UNTRACKED_TOP_M, UNTRACKED_PAD_M)
    if CONTEXT.exists():
        ctx = json.loads(CONTEXT.read_text())
        at = {k: i for i, k in enumerate(ctx["fields"]["buildings"])}
        for k, b in enumerate(ctx["buildings"]):
            e, n, w, d, brg = (b[at["e"]], b[at["n"]], b[at["width_m"]], b[at["depth_m"]], b[at["bearing_deg"]])
            R = math.hypot(w, d) / 2 + 1.0
            if not built.touches(e - R, n - R, e + R, n + R):
                continue
            # the renderer drops a block that touches a placed structure's footprint, grown 1 m
            rect = context_box(e, n, w, d, brg, 1.0)
            if any(in_poly((e, n), fp) or any(in_poly(c, fp) for c in rect) or any(in_poly(c, rect) for c in fp)
                   for fp in footprints):
                continue
            built.lay_prism(f"context block {k} ({ctx['enums']['rule'][b[at['rule']]]})",
                            context_box(e, n, w, d, brg), b[at["eave_m"]] + b[at["rise_m"]], 0.0)
    return built


def pin_offsets(m):
    """Where a crossarm's pins stand along it, as renderers/web/js/street-furniture.js pinOffsets."""
    n = m.get("pins", 0)
    L = m.get("arm_len_m", 1.8)
    if not n:
        return []
    half = math.ceil(n / 2)
    out = []
    for i in range(half):
        z = 0.25 + (L / 2 - 0.35) * (0 if half == 1 else i / (half - 1)) + 0.05
        out += [z, -z]
    return sorted(out[:n])


def arm_dir(heading_deg):
    """A pole's crossarm direction in plan (east, north): its local z, square to heading_deg."""
    a = math.radians(90.0 - heading_deg)
    return (math.sin(a), -math.cos(a))


def pole_hits(p, m, built):
    """What a pole or its crossarm runs into: [(part, structure, height)]."""
    out = []
    r = m["butt_d_m"] / 2 + POLE_BODY_CLEAR_M
    h, w = built.top_at([(p["e"], p["n"])], r)
    if h[0] > BUILT_FLAT_M:
        out.append(("pole", built.name(int(w[0])), float(h[0])))
    if m.get("arms"):
        y = m["height_m"] - m["arm_below_top_m"] - 0.06 - ARM_CLEAR_M
        ax = arm_dir(p["heading_deg"])
        half = m["arm_len_m"] / 2
        ts = [i * 0.1 - half for i in range(int(round(2 * half / 0.1)) + 1)]
        h, w = built.top_at([(p["e"] + ax[0] * t, p["n"] + ax[1] * t) for t in ts], 0.1)
        i = int(h.argmax())
        if h[i] > y:
            out.append(("crossarm", built.name(int(w[i])), float(h[i])))
    return out


def wire_paths(w, poles, models, wire_model):
    """Each wire of a span as (a, b, y_a, y_b, sag): plan ends, heights above ground, mid sag.
    Mirrors renderers/web/js/street-furniture.js: a line span joins each pin to the pin on the
    same side of the other pole's arm, seen along the span."""
    if w["kind"] == "line":
        a, b = poles[w["from"]], poles[w["to"]]
        ma, mb = models[a["class"]], models[b["class"]]
        span = math.dist((a["e"], a["n"]), (b["e"], b["n"])) or 1.0
        d = ((b["e"] - a["e"]) / span, (b["n"] - a["n"]) / span)

        def pins(p, m):
            ax = arm_dir(p["heading_deg"])
            pts = [(p["e"] + ax[0] * z, p["n"] + ax[1] * z) for z in pin_offsets(m)]
            return sorted(pts, key=lambda v: (v[0] - p["e"]) * -d[1] + (v[1] - p["n"]) * d[0])
        pa, pb = pins(a, ma), pins(b, mb)
        n = min(len(pa), len(pb))
        ya = ma["height_m"] - ma["arm_below_top_m"] + 0.24
        yb = mb["height_m"] - mb["arm_below_top_m"] + 0.24
        sag = wire_model["sag_frac"] * span
        out = []
        for i in range(n):
            j = round(i * (len(pa) - 1) / max(1, n - 1))
            k = round(i * (len(pb) - 1) / max(1, n - 1))
            out.append((pa[j], pb[k], ya, yb, sag))
        return out
    t = wire_model["trolley"]
    if w["kind"] == "trolley_span":
        a, b = poles[w["from"]], poles[w["to"]]
        h = models["trolley"]["span_at_m"]
        return [((a["e"], a["n"]), (b["e"], b["n"]), h, h, t["span_sag_m"])]
    if w["kind"] == "trolley_contact":
        hangs = []
        for ia, ib in w["between_spans"]:
            a, b = poles[ia], poles[ib]
            L = math.dist((a["e"], a["n"]), (b["e"], b["n"])) or 1.0
            hangs.append((((a["e"] + b["e"]) / 2, (a["n"] + b["n"]) / 2), ((b["e"] - a["e"]) / L, (b["n"] - a["n"]) / L)))
        g = t["contact_gap_m"] / 2
        out = []
        for s in (-1, 1):
            p0 = (hangs[0][0][0] + hangs[0][1][0] * s * g, hangs[0][0][1] + hangs[0][1][1] * s * g)
            p1 = (hangs[1][0][0] + hangs[1][1][0] * s * g, hangs[1][0][1] + hangs[1][1][1] * s * g)
            out.append((p0, p1, t["contact_h_m"], t["contact_h_m"], 0.08))
        return out
    return []


def span_hit(paths, built):
    """The first place a wire comes within WIRE_CLEAR_M of what is built under it:
    (structure, metres along, wire height, built height) or None."""
    np = built.np
    for a, b, ya, yb, sag in paths:
        L = math.dist(a, b)
        n = max(2, int(L / 0.1))
        f = np.linspace(0.0, 1.0, n + 1)
        pts = np.stack([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f], axis=1)
        y = ya + (yb - ya) * f - 4 * sag * f * (1 - f)
        h, w = built.top_at(pts, 0.05)
        bad = np.nonzero(h > y - WIRE_CLEAR_M)[0]
        if len(bad):
            i = int(bad[0])
            return built.name(int(w[i])), float(f[i] * L), float(y[i]), float(h[i])
    return None


def wire_label(w):
    if "between_spans" in w:
        return " / ".join("-".join(s) for s in w["between_spans"])
    return f"{w['from']} -> {w['to']}"


def intersections(items, wires, models, wire_model, built):
    """Every pole, crossarm or wire that runs into a 1904 structure, one line each."""
    poles = {i["id"]: i for i in items if i["kind"] == "utility_pole"}
    out = []
    for p in poles.values():
        for part, sid, h in pole_hits(p, models[p["class"]], built):
            what = "stands in" if part == "pole" else "reaches"
            out.append(f"{p['id']}: its {part} {what} {sid} (built {h:.2f} m high there)")
    for w in wires:
        hit = span_hit(wire_paths(w, poles, models, wire_model), built)
        if hit:
            sid, at, y, h = hit
            out.append(f"{w['kind']} {wire_label(w)}: a wire runs through {sid} {at:.1f} m along "
                       f"(wire {y:.2f} m, built {h:.2f} m)")
    return out


def lay_poles(grid, section, trees_doc, items, built):
    xs = grid["cross_sections"]
    faces = {f["id"]: Face(f, xs[f["cross_section"]]) for f in grid["faces"]}
    alleys = {a["id"]: a for a in grid.get("alleys", [])}
    walks = {}
    for w in (section or {}).get("carriage_walks", {}).get("walks", []):
        walks.setdefault(w["face"], []).append(w)
    trees = [(t["e"], t["n"]) for t in (trees_doc or {}).get("trees", [])]
    others = [(i["e"], i["n"]) for i in items]
    crossings = crossing_polys(section)

    def free(p):
        return (all(math.dist(p, t) >= POLE_TREE_CLEAR_M for t in trees)
                and all(math.dist(p, o) >= POLE_ITEM_CLEAR_M for o in others)
                and all(poly_dist(p, c) >= CROSSING_CLEAR_M for c in crossings))

    def built_clear(p, t, cls):
        """The pole and its crossarm stand clear of every structure (T-3225)."""
        return not pole_hits({"e": r2(p[0]), "n": r2(p[1]), "heading_deg": round(bearing(t), 1)}, POLE[cls], built)

    def on_face(face, s, across, lo, hi, cls):
        blocked = blocked_intervals(face, walks, list(alleys.values()))
        k = 0
        while k * NUDGE_STEP_M <= NUDGE_MAX_M:
            for x in ((s,) if k == 0 else (s + k * NUDGE_STEP_M, s - k * NUDGE_STEP_M)):
                if lo <= x <= hi and not any(a < x < b for a, b, _ in blocked):
                    p, t = face.at(x, across)
                    if free(p) and built_clear(p, t, cls):
                        return x, p, t
            k += 1
        return None

    poles, wires = [], []

    def pole(pid, p, t, cls, grade, sources, line, liberty=None, **kw):
        rec = {"id": pid, "kind": "utility_pole", "e": r2(p[0]), "n": r2(p[1]), "heading_deg": round(bearing(t), 1),
               "place": line, "class": cls, "grade": grade, "sources": sources}
        if liberty:
            rec["liberty"] = liberty
        rec.update(kw)
        poles.append(rec)
        others.append(p)
        return rec

    # 1. 18th Street: Glessner's pole by the alley, then west to Indiana.
    face = faces[GLESSNER_POLE["face"]]
    al = alleys[GLESSNER_POLE["alley"]]
    ss = [face.project(tuple(q))[0] for q in al["polygon_local_m"] if abs(face.project(tuple(q))[1]) < 8.0]
    # The face runs east to west; "past the alley" is toward Prairie, the smaller s.
    s0 = min(ss) - ALLEY_CLEAR_M - GLESSNER_POLE["past_alley_m"]
    across = face.park_to - POLE_CURB_INSET_M
    hit = on_face(face, s0, across, 0.0, face.length, "street")
    if not hit:
        raise SystemExit("street furniture: no clear spot for Glessner's pole")
    names = {k: v.get("name_1904", k) for k, v in grid["streets"].items()}
    w18 = f"on the south parkway of {names['e18th']}"
    line18 = [pole("pole.18th.glessner", hit[1], hit[2], "street", "attested", GLESSNER_POLE["sources"], "e18th",
                   where=f"{w18}, at the north-west corner of Glessner's stable by the alley",
                   note=("Glessner's: the c. 1887 photograph of the stable from the north-west shows a wooden pole "
                         "with a crossarm of about six pins on the 18th Street parkway at the stable's corner, "
                         "by the alley."))]
    s = hit[0] + POLE_SPACING_M
    k = 1
    while s <= face.length - 6.0:
        h = on_face(face, s, across, s - 4.0, face.length - 4.0, "street")
        if h:
            line18.append(pole(f"pole.18th#{k:02d}", h[1], h[2], "street", "inferred",
                               GLESSNER_POLE["sources"] + POLE_18TH_NOTE_SOURCES, "e18th",
                               liberty="L-prairie-utility-poles-3202", where=w18))
            k += 1
        s += POLE_SPACING_M
    # ...and one more short of Indiana Avenue's corner, where the line goes on beyond the district.
    last_s = face.project((line18[-1]["e"], line18[-1]["n"]))[0]
    if face.length - 8.0 - last_s > 0.5 * POLE_SPACING_M:
        h = on_face(face, face.length - 8.0, across, last_s + 10.0, face.length - 4.0, "street")
        if h:
            line18.append(pole(f"pole.18th#{k:02d}", h[1], h[2], "street", "inferred",
                               GLESSNER_POLE["sources"] + POLE_18TH_NOTE_SOURCES, "e18th",
                               liberty="L-prairie-utility-poles-3202", where=w18))
    # 2. The alleys: a line down each, on its east side, an end pole in from each mouth. Each pole
    #    stands clear of what is built (T-3225): where the rule's spot puts the pole or its crossarm
    #    into a coach house, it slides along the alley, then steps further into it, and only then
    #    crosses to the west side; where a span's wires would run through a building, the span's
    #    poles step further into the alley until they clear it, or the span is not hung.
    wire_model = {"sag_frac": WIRE_SAG_FRAC, "trolley": TROLLEY}
    moved, spans_dropped = [], []

    class Spot:
        """An alley pole's place: its edge, the distance along it, and how far inside it."""

        def __init__(self, pid, aid, side, edge, x, inset, dk):
            self.pid, self.aid, self.side, self.edge, self.x, self.inset, self.dk = pid, aid, side, edge, x, inset, dk

        def rec(self, inset=None):
            q, t = poly_at(self.edge, self.x)
            sgn = 1.0 if self.side == "east" else -1.0   # walking south, west is to the right
            ins = self.inset if inset is None else inset
            p = (q[0] + t[1] * sgn * ins, q[1] - t[0] * sgn * ins)
            return {"id": self.pid, "e": r2(p[0]), "n": r2(p[1]), "heading_deg": round(bearing(t), 1),
                    "class": "alley"}, p, t

    def spot_ok(sp, inset=None):
        r, p, t = sp.rec(inset)
        return free(p) and not pole_hits(r, POLE["alley"], built)

    def recs(*xs):
        return {x["id"]: x for x in xs}

    def span_ok(ra, rb):
        w = {"kind": "line", "from": ra["id"], "to": rb["id"]}
        return span_hit(wire_paths(w, recs(ra, rb), POLE, wire_model), built) is None

    alley_lines = []   # per alley: (aid, [Spot])
    for aid in sorted(alleys):
        west, east = alley_edges(alleys[aid])
        L = poly_len(east)
        Lw = poly_len(west)
        n = max(1, round((L - 2 * POLE_MOUTH_IN_M) / POLE_SPACING_M))
        step = (L - 2 * POLE_MOUTH_IN_M) / n
        spots = []
        for j in range(n + 1):
            s = POLE_MOUTH_IN_M + j * step
            pid = f"pole.{aid.replace('alley_', 'alley.')}#{j:02d}"
            # T-3202's own order first (the east side, 0.45 m in, up to 3 m along), then further
            # along and further in, then the west side.
            cands = []
            for side, extra in (("east", 0.0), ("west", OTHER_SIDE_COST)):
                for inset in ALLEY_INSETS_M:
                    for dk in (0.0,) + ALLEY_SLIDES_M:
                        if side == "east" and inset == ALLEY_INSETS_M[0] and abs(dk) <= 3.0:
                            cost = abs(dk)
                        else:
                            cost = 3.0 + abs(dk) + INSET_COST * (inset - ALLEY_INSETS_M[0]) + extra
                        cands.append((cost, side, inset, dk))
            cands.sort(key=lambda c: c[0])
            got = None
            for _, side, inset, dk in cands:
                edge, Le = (east, L) if side == "east" else (west, Lw)
                x = min(max((s + dk) * Le / L, 1.0), Le - 1.0)
                sp = Spot(pid, aid, side, edge, x, inset, dk)
                if spot_ok(sp):
                    got = sp
                    break
            if got:
                spots.append(got)
            else:
                moved.append({"pole": pid, "dropped": "no clear place within 6 m along its alley, on either side"})
        alley_lines.append((aid, spots))

    # The spans: along each alley, then across the cross streets where one alley's foot meets the
    # next one's head, then from Glessner's pole into the alley behind it. A span through a
    # building first steps its alley poles further in (never Glessner's: its photograph places it).
    spans = []   # [a, b, grade] where a, b are Spot or a fixed record
    for aid, spots in alley_lines:
        for a, b in zip(spots, spots[1:]):
            spans.append([a, b, "reconstructed"])
    ends = [(aid, sp[0], sp[-1]) for aid, sp in alley_lines if sp]
    for aid, head, foot in ends:
        for bid, head2, _ in ends:
            fr, hr = foot.rec()[0], head2.rec()[0]
            if bid != aid and math.dist((fr["e"], fr["n"]), (hr["e"], hr["n"])) < 2 * POLE_MOUTH_IN_M + 66 * FT + ALLEY_LINE_JOIN_M \
                    and abs(fr["e"] - hr["e"]) < ALLEY_LINE_JOIN_M and hr["n"] < fr["n"]:
                spans.append([foot, head2, "reconstructed"])
    head = next((h for aid, h, _ in ends if aid == GLESSNER_POLE["alley"]), None)
    glessner_rec = {"id": line18[0]["id"], "e": line18[0]["e"], "n": line18[0]["n"],
                    "heading_deg": line18[0]["heading_deg"], "class": "street"}
    if head:
        spans.append([glessner_rec, head, "inferred"])

    def r_of(x, inset=None):
        return x.rec(inset)[0] if isinstance(x, Spot) else x

    kept = []
    for sp in spans:
        a, b, _ = sp
        if span_ok(r_of(a), r_of(b)):
            kept.append(sp)
            continue
        movable = [x for x in (a, b) if isinstance(x, Spot)]
        fixed = False
        for ins in ALLEY_INSETS_M:
            trial = {x: max(x.inset, ins) for x in movable}
            if all(trial[x] == x.inset for x in movable):
                continue
            if not all(spot_ok(x, trial[x]) for x in movable):
                continue
            ra = r_of(a, trial.get(a)) if isinstance(a, Spot) else a
            rb = r_of(b, trial.get(b)) if isinstance(b, Spot) else b
            if not span_ok(ra, rb):
                continue
            # ...and every span already hung from a pole that steps in still clears.
            ok = True
            for ka, kb, _ in kept:
                if ka in trial or kb in trial:
                    if not span_ok(r_of(ka, trial.get(ka)) if isinstance(ka, Spot) else ka,
                                   r_of(kb, trial.get(kb)) if isinstance(kb, Spot) else kb):
                        ok = False
                        break
            if ok:
                for x in movable:
                    x.inset = trial[x]
                fixed = True
                break
        if fixed:
            kept.append(sp)
        else:
            spans_dropped.append(f"{r_of(a)['id']} -> {r_of(b)['id']}")

    for aid, spots in alley_lines:
        for sp in spots:
            rec, p, t = sp.rec()
            pole(sp.pid, p, t, "alley", "reconstructed", [], "alley", liberty="L-prairie-utility-poles-3202",
                 alley=aid, where=f"in the alley {alleys[aid]['where']}")
            if sp.side != "east" or sp.inset != ALLEY_INSETS_M[0] or abs(sp.dk) > 3.0:
                moved.append({"pole": sp.pid, "side": sp.side, "inset_m": sp.inset, "along_m": sp.dk})
    for a, b, grade in kept:
        if grade == "reconstructed":
            wires.append({"from": r_of(a)["id"], "to": r_of(b)["id"], "kind": "line", "grade": grade})
    # 18th Street's line: along the parkway, and from Glessner's pole into the alley behind it.
    for a, b in zip(line18, line18[1:]):
        wires.append({"from": a["id"], "to": b["id"], "kind": "line", "grade": "inferred"})
    for a, b, grade in kept:
        if grade == "inferred":
            wires.append({"from": r_of(a)["id"], "to": r_of(b)["id"], "kind": "line", "grade": grade})
    # 3. 22nd Street's trolley: poles on both curbs, a span wire between each pair, two contact
    #    wires along the street over the tracks.
    pairs = []
    for fid in TROLLEY_FACES:
        face = faces[fid]
        width = STREET_WIDTH_FT[face.rec["cross_section"]] * FT
        across = face.park_to - POLE_CURB_INSET_M
        far_across = width - across        # the far side's parkway, measured from this face's line
        n = max(1, round((face.length - 12.0) / POLE_SPACING_M))
        step = (face.length - 12.0) / n
        for j in range(n + 1):
            s = 6.0 + j * step
            h = on_face(face, s, across, 4.0, face.length - 4.0, "trolley")
            if not h:
                continue
            q, t = face.at(h[0], far_across)
            a = pole(f"pole.trolley.{fid.split('__')[1]}.n#{j:02d}", h[1], h[2], "trolley", "reconstructed",
                     [], "e22nd", liberty="L-prairie-utility-poles-3202",
                     where=f"on the north parkway of {names['e22nd']}")
            b = pole(f"pole.trolley.{fid.split('__')[1]}.s#{j:02d}", q, t, "trolley", "reconstructed",
                     [], "e22nd", liberty="L-prairie-utility-poles-3202", beyond_district=True,
                     where=f"on the south side of {names['e22nd']}, across from the district")
            pairs.append((h[0] + (0 if fid == TROLLEY_FACES[0] else 1000), a, b))
    pairs.sort(key=lambda x: (x[1]["e"]))
    for _, a, b in pairs:
        wires.append({"from": a["id"], "to": b["id"], "kind": "trolley_span", "grade": "inferred",
                      "sources": TROLLEY_SOURCES})
    for (_, a1, b1), (_, a2, b2) in zip(pairs, pairs[1:]):
        wires.append({"between_spans": [[a1["id"], b1["id"]], [a2["id"], b2["id"]]], "kind": "trolley_contact",
                      "grade": "inferred", "sources": TROLLEY_SOURCES})
    return poles, wires, {"moved": moved, "spans_not_hung": spans_dropped}


def build(built=None):
    grid = json.loads(GRID.read_text())
    section = json.loads(SECTION.read_text()) if SECTION.exists() else None
    trees = json.loads(TREES.read_text()) if TREES.exists() else None
    if built is None:
        built = lay_built(grid)
    items = lay_lamps(grid, section, trees)
    items += lay_hydrants(grid, section, trees, items)
    poles, wires, cleared = lay_poles(grid, section, trees, items, built)
    items += poles
    order = {"corner": 0, "mid-block": 1}
    items.sort(key=lambda i: (i["kind"], order.get(i["place"], 9), i["id"]))
    cited = [s for i in items for s in i["sources"]]
    lamps = [i for i in items if i["kind"] == "gas_lamp"]
    hydrants = [i for i in items if i["kind"] == "fire_hydrant"]
    poles = [i for i in items if i["kind"] == "utility_pole"]
    return {
        "_doc": ("The 1904 district's street furniture (T-3199): the gas lamps, (T-3201) the fire hydrants and (T-3202) the poles and wires. GENERATED by "
                 "tools/lay_prairie_1904_street_furniture.py from data/street_grid/1904.json, "
                 "data/street_section/1904.json and data/street_trees/1904.json -- do not hand-edit; re-run the "
                 "tool. Local ENU metres of data/datum.json; heading_deg is the compass bearing of the street "
                 "line the item stands along. Drawn by renderers/web/js/street-furniture.js. "
                 "docs/RESEARCH/prairie_1904_street_furniture.md is the reading; docs/LIBERTIES.md "
                 "L-prairie-street-lamps-3199, L-prairie-hydrants-3201 and L-prairie-utility-poles-3202 the "
                 "inventions. `wires` join poles by id; the renderer hangs them from the poles' pins."),
        "scene": "1904",
        "target_date": "1904-07-01",
        "ticket": "T-3199",
        "generated_by": "tools/lay_prairie_1904_street_furniture.py",
        "kinds": {
            "gas_lamp": {
                "name": "gas street lamp",
                "form": ("A cast-iron post: a plain round foot on a plinth, a moulded collar, a leafed boss at "
                         "knee height, a slender shaft, a bell capital under a knobbed ladder bar, four scrolled "
                         "arms bent up into the foot of a clear four-sided lantern that tapers out to an iron waist "
                         "band, a steep glazed top on iron hips, a small cap, vent and knob; painted iron. About "
                         "3.1 m. The Glessner corner's lamp stands on a stone pad level with the walk."),
                "form_grade": "attested",
                "form_sources": ["chicagology_1811_ames_photo", "taylor_2135_glessner_exterior_1887_1889",
                                 "chicagology_2140_photo_b"],
                "form_note": ("Read off the 1811 photograph, Taylor's no. 2135 and the second 2140 photograph, the "
                              "three that show a post whole and near; its parts and heights from the 1811 print, "
                              "the clearest (T-3219). Every lamp is drawn with that one post. 1904 "
                              "is gas: electric standards appear only in pictures dated after it. The scene is a "
                              "July morning with no night, so no lamp is lit."),
                "model_m": LAMP,
                "model_by_class": LAMP_BY_CLASS,
                "name_by_class": {"globe_post": "globe lamp post"},
                "form_by_class": {
                    "globe_post": ("A plain post about 4.9 m to its cap, painted pale, on a plain base, with a small "
                                   "bar a third of the way down, a slim neck and a wide shallow globe under a small "
                                   "dark cap."),
                },
                "form_sources_by_class": {"globe_post": ["aic_taylor_16554_pullman_from_sw"]},
                "form_note_by_class": {
                    "globe_post": ("Read off Taylor's no. 16554 (1890s), the one picture that shows it: its heights "
                                   "from the print's column scaled by the district post at the same place, its "
                                   "paint from its tone (it prints lighter than the sunlit stone behind it; the "
                                   "print is monochrome, so the pale is a tone, not a colour). The print cannot say "
                                   "whether it burned gas or electricity, nor what its base and globe are made of "
                                   "at this size; it is kept with the gas lamps for its place. Not lit: the scene "
                                   "is a July morning."),
                },
                "what": "A cast-iron gas lamp post",
                "what_by_class": {"globe_post": "A pale-painted lamp post with a globe head"},
                "ticket": "T-3199",
                "rule_note": "The pictures show such lamps at the district's corners and along its parkways",
            },
            "fire_hydrant": {
                "name": "fire hydrant",
                "form": ("A post fire hydrant: a cast-iron barrel about 0.85 m tall on a flared foot, a band under a "
                         "domed bonnet with an operating nut on top, and two side nozzles with caps; painted iron."),
                "form_grade": "attested",
                "form_sources": ["loc_det_4a08065_pullman_residence", "ghm_blog_pullman_completed",
                                 "chicagology_2140_photo_b"],
                "form_note": ("Read off the owner's crop of the Detroit Publishing Pullman view, the museum's halftone "
                              "of the same corner and the second 2140 photograph, which show one type. The prints are "
                              "monochrome; the Detroit view prints the hydrant lighter than the lamp posts, so it is "
                              "drawn a mid grey, and its colour is reconstructed."),
                "model_m": HYDRANT,
                "what": "A cast-iron post fire hydrant",
                "ticket": "T-3201",
                "rule_note": ("The pictures show post hydrants on the parkway at Pullman's corner and at 22nd Street; "
                              "the city's hydrants stood at its corners and along its long blocks"),
            },
            "utility_pole": {
                "name": "utility pole",
                "name_by_class": {"street": "utility pole", "alley": "utility pole", "trolley": "trolley-wire pole"},
                "form": ("A wooden pole, 9 to 11 m, tapering from its butt; a line pole carries a crossarm with "
                         "pins and glass insulators, a trolley-wire pole carries the span wire over the street."),
                "form_grade": "inferred",
                "form_sources": ["cornell_adw_glessner_stable_1887"],
                "form_note": ("Glessner's pole in the c. 1887 photograph is a plain wooden pole with one crossarm of "
                              "about six pins; every line pole is drawn after it. The trolley poles' form is not "
                              "pictured: drawn as plain wooden poles."),
                "model_m": POLE,
                "what": "A wooden pole carrying overhead wires",
                "what_by_class": {"trolley": "A pole holding the span wire of the street railway's overhead"},
                "ticket": "T-3202",
                "rule_note": "Glessner's pole is pictured on 18th Street; the lines down the alleys are drawn by rule",
                "rule_note_by_class": {
                    "street": "The photograph of Glessner's stable shows the line's pole at the alley",
                    "trolley": ("A photograph at 22nd and Prairie shows rails and trolley wires in 22nd Street; "
                                "the poles that carried them are not pictured"),
                },
            },
        },
        "placement": {
            "gas_lamp": {
                "liberty": "L-prairie-street-lamps-3199",
                "corner_inset_ft": CORNER_INSET_FT,
                "walk_offset_m": WALK_OFFSET_M,
                "spacing_ft": LAMP_SPACING_FT,
                "corner_clear_m": CORNER_CLEAR_M,
                "tree_clear_m": TREE_CLEAR_M,
                "note": ("A lamp at every intersection corner of the district's drawn streets, in the corner square "
                         "1.5 ft inside both curbs (the curb-return corner, between where the two crossings land), "
                         "on the parkway (the Glessner corner's on a stone pad level with the walk, as Taylor 2135 "
                         "shows); the pictured mid-block lamps at their lots; the rest of every face "
                         "at about 160 ft, the two sides of a street staggered, on the parkway 0.4 m off the walk, "
                         "each moved along the parkway clear of an elm, a carriage walk or an alley mouth. A corner "
                         "where a face meets a curved return (Calumet at 18th) has no corner of its own. No "
                         "rule lamp stands on a stretch the pictures see whole and show empty (pictured_empty)."),
                "pictured_empty": PICTURED_EMPTY,
            },
            "fire_hydrant": {
                "liberty": "L-prairie-hydrants-3201",
                "corner_along_m": HYDRANT_CORNER_ALONG_M,
                "curb_inset_m": HYDRANT_CURB_INSET_M,
                "long_face_m": HYDRANT_LONG_FACE_M,
                "note": ("The two pictured hydrants where their pictures put them (Pullman's on the Prairie Avenue "
                         "parkway beside the walk north of 18th Street, Tucker's near the curb toward 22nd Street); "
                         "then one at every other intersection, at its corners taken in turn, on the avenue's "
                         "parkway 3.5 m from the corner and 0.45 m inside the curb; and one mid-block on one side "
                         "of every block face 150 m long or more. Each stands in the grass, clear of the walks, the "
                         "corner crossings, the carriage walks, the lamps and the elms."),
            },
            "utility_pole": {
                "liberty": "L-prairie-utility-poles-3202",
                "spacing_m": POLE_SPACING_M,
                "clearance": {
                    "pole_face_m": POLE_BODY_CLEAR_M, "crossarm_over_roof_m": ARM_CLEAR_M,
                    "wire_over_roof_m": WIRE_CLEAR_M, "alley_insets_m": list(ALLEY_INSETS_M),
                    "note": CLEARANCE_NOTE,
                    "moved": cleared["moved"],
                    "spans_not_hung": cleared["spans_not_hung"],
                },
                "note": ("Glessner's pole where the photograph shows it, on 18th Street's south parkway at the "
                         "stable's corner by the alley; the line on west from it to Indiana Avenue at about 34 m "
                         "(Taylor 2135 and the Detroit view show no pole on 18th Street east of the alley); a line "
                         "down every alley on its east side, its end poles 2.5 m in from the mouths and spanned "
                         "across the cross streets where alleys meet; none on the Prairie Avenue parkways. Each "
                         "pole clear of the elms, lamps, hydrants, carriage walks and alley mouths, and every pole, "
                         "crossarm and wire clear of the buildings, coach houses and fences."),
                "note_by_class": {
                    "trolley": ("22nd Street's overhead: a pair of plain poles at about 34 m, one in the north "
                                "parkway by the curb and one opposite it across the street, a span wire between "
                                "them at 6.6 m and two contact wires along the street over the tracks at 5.6 m."),
                },
            },
        },
        "wire_model": {"sag_frac": WIRE_SAG_FRAC, "trolley": TROLLEY},
        "street_names": {k: v.get("name_1904", k) for k, v in grid["streets"].items()},
        "sources": source_lines(cited + [sid for e in PICTURED_EMPTY for sid in e["seen_by"]]
                                + ["chicagology_1811_ames_photo", "taylor_2135_glessner_exterior_1887_1889",
                                         "chicagology_2140_photo_b", "loc_det_4a08065_pullman_residence",
                                         "ghm_blog_pullman_completed", "cornell_adw_glessner_stable_1887",
                                         "chicagology_2140_photo_a"]),
        "summary": {
            "items": len(items),
            "gas_lamps": len(lamps),
            "fire_hydrants": len(hydrants),
            "utility_poles": len(poles),
            "wires": len(wires),
            "corner_lamps": sum(i["place"] == "corner" for i in lamps),
            "attested": sum(i["grade"] == "attested" for i in items),
            "inferred": sum(i["grade"] == "inferred" for i in items),
            "reconstructed": sum(i["grade"] == "reconstructed" for i in items),
        },
        "items": items,
        "wires": wires,
    }


def dump(doc):
    """Indented, one item to a line: the file diffs by item."""
    items = doc.pop("items")
    wires = doc.pop("wires", [])
    head = json.dumps(doc, indent=1, ensure_ascii=False)[:-2]
    line = lambda xs: ",\n".join("  " + json.dumps(x, separators=(", ", ": "), ensure_ascii=False) for x in xs)
    doc["items"] = items
    doc["wires"] = wires
    return head + f',\n "items": [\n{line(items)}\n ],\n "wires": [\n{line(wires)}\n ]\n}}\n'


def poles_clear(doc, built):
    """T-3225: no pole, crossarm or wire of `doc` runs into a 1904 structure. [] when none does."""
    return intersections(doc["items"], doc["wires"], doc["kinds"]["utility_pole"]["model_m"],
                         doc["wire_model"], built)


def self_test(built):
    """Break the clearance check four ways (each must fire); the placement and a low fence pass."""
    import copy
    doc = build(built)
    np = built.np
    fails = 0

    def expect(label, d, want, b=built):
        nonlocal fails
        got = poles_clear(d, b)
        hit = [g for g in got if want in g] if want else got
        ok = bool(hit) if want else not got
        print(f"{'ok  ' if ok else 'FAIL'} {label}: " + ("; ".join(got[:2]) if got else "nothing intersects"))
        fails += 0 if ok else 1

    expect("the committed placement", doc, None)
    poles = [i for i in doc["items"] if i["kind"] == "utility_pole" and i["class"] == "alley"]
    p0 = poles[0]
    # 1. a pole moved onto the highest point of the first structure laid
    e0, n0, e1, n1, top, who = built.rects[0]
    r, c = np.unravel_index(int(top.argmax()), top.shape)
    d = copy.deepcopy(doc)
    q = next(i for i in d["items"] if i["id"] == p0["id"])
    q["e"], q["n"] = r2(e0 + (c + 0.5) * BUILT_RES_M), r2(n0 + (r + 0.5) * BUILT_RES_M)
    expect("a pole stood in a building", d, f"{p0['id']}: its pole stands in")

    # The rest add a made-up structure to a copy of the raster beside the first alley pole.
    def with_box(name, centre, half_e, half_n, top_m):
        b = copy.copy(built)
        b.rects = [(re0, rn0, re1, rn1, t.copy(), w.copy()) for re0, rn0, re1, rn1, t, w in built.rects]
        b.names = built.names + [name]
        sid = len(b.names) - 1
        xs = np.arange(centre[0] - half_e, centre[0] + half_e + 1e-9, BUILT_RES_M / 2)
        ys = np.arange(centre[1] - half_n, centre[1] + half_n + 1e-9, BUILT_RES_M / 2)
        gx, gy = np.meshgrid(xs, ys)
        b.lay_points(sid, np.stack([gx.ravel(), gy.ravel(), np.full(gx.size, top_m)], axis=1))
        return b
    m = doc["kinds"]["utility_pole"]["model_m"]["alley"]
    ax = arm_dir(p0["heading_deg"])
    # 2. a tall narrow wall under the crossarm's end, clear of the pole itself
    tip = (p0["e"] + ax[0] * (m["arm_len_m"] / 2 - 0.1), p0["n"] + ax[1] * (m["arm_len_m"] / 2 - 0.1))
    expect("a gable under the crossarm", doc, f"{p0['id']}: its crossarm reaches self-test gable",
           with_box("self-test gable", tip, 0.2, 0.2, m["height_m"]))
    # 3. a roof under the middle of the first alley span, as high as the wires
    w = next(x for x in doc["wires"] if x["kind"] == "line" and x["from"] == p0["id"])
    p1 = next(i for i in doc["items"] if i["id"] == w["to"])
    mid = ((p0["e"] + p1["e"]) / 2, (p0["n"] + p1["n"]) / 2)
    expect("a roof under a span", doc, f"line {p0['id']} -> {p1['id']}: a wire runs through self-test roof",
           with_box("self-test roof", mid, 1.5, 1.5, m["height_m"] - m["arm_below_top_m"]))
    # 4. ...and a fence there is passed over
    expect("a fence under a span (passes)", doc, None, with_box("self-test fence", mid, 1.5, 1.5, 1.8))
    # 5. a trolley span wire through a building in 22nd Street
    t = next(x for x in doc["wires"] if x["kind"] == "trolley_span")
    a = next(i for i in doc["items"] if i["id"] == t["from"])
    b = next(i for i in doc["items"] if i["id"] == t["to"])
    mid = ((a["e"] + b["e"]) / 2, (a["n"] + b["n"]) / 2)
    expect("a building under the trolley span", doc, "trolley_span", with_box("self-test block", mid, 2.0, 2.0, 8.0))
    print(f"{'all four faults caught, the clear cases passed' if not fails else f'{fails} case(s) wrong'}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    built = lay_built(json.loads(GRID.read_text()))
    if a.self_test:
        return self_test(built)
    doc = build(built)
    text = dump(doc)
    json.loads(text)
    hits = poles_clear(doc, built)
    if hits:
        print(f"street furniture: {len(hits)} pole(s), crossarm(s) or span(s) run into a 1904 structure (T-3225):")
        for h in hits:
            print(f"  {h}")
        return 1
    if a.check:
        have = OUT.read_text() if OUT.exists() else ""
        if have:
            committed = json.loads(have)
            old = poles_clear(committed, built)
            if old:
                print(f"street furniture: the committed {OUT.relative_to(ROOT)} has {len(old)} pole(s), crossarm(s) "
                      "or span(s) running into a 1904 structure (T-3225):")
                for h in old:
                    print(f"  {h}")
                return 1
        have = OUT.read_text() if OUT.exists() else ""
        if have != text:
            print(f"street furniture: {OUT.relative_to(ROOT)} is not what the tool writes -- re-run "
                  "python3 tools/lay_prairie_1904_street_furniture.py")
            return 1
        print(f"street furniture: {doc['summary']}, as written")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {doc['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
