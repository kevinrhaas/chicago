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
houses mid-block (1811, opposite 1721, 1708, 1816, 1905, 2120, 2140). So:

  * one lamp at every intersection corner of the district's drawn streets, on the parkway
    in the corner square where two sidewalk spaces meet, 1.5 ft inside both curbs: that is
    the curb-return corner, between where the two corner crossings land (Taylor 2135 shows
    it on a small stone footing between the two crossing ramps), and clear of both walks;
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

LAMP = {
    "height_m": 3.1, "base_w_m": 0.36, "base_h_m": 0.45, "column_d_m": [0.15, 0.10],
    "flutes": 8, "ladder_bar_m": {"at": 2.32, "w": 0.52}, "lantern_m": {"foot": 2.42, "top": 2.86,
    "w_foot": 0.22, "w_top": 0.40}, "cap_top_m": 3.0, "finial_top_m": 3.1,
    "footing_m": {"w": 0.95, "h": 0.16},
}

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

# The pictured mid-block lamps: on Prairie Avenue's parkway at a lot, read off each picture.
# `at` is the share of the way along the lot's frontage from its north end.
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
            "heading_deg": round(c["heading"], 1), "footing": True,
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
        items.append({
            "id": f"lamp.pictured.{m['key']}", "kind": "gas_lamp", "e": r2(P[0]), "n": r2(P[1]),
            "heading_deg": round(bearing(t), 1), "footing": False,
            "place": "mid-block", "face": face.id, "parcel": p["id"],
            "grade": "attested", "sources": m["sources"], "note": m["note"],
            "moved_m": r2(abs(s2 - s)),
        })
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
        c = next(c for c in cs if face in c["faces"] and h["end"] in c["streets"])
        s0, sign = face_end_s(face, c)
        across = (face.walk_to + HYDRANT_WALK_OFFSET_M) if h["side"] == "walk" else (face.park_to - HYDRANT_CURB_INSET_M)
        blocked = blocked_intervals(face, walks, alleys)
        s = clear(face, s0 + sign * h["along_m"], across, blocked, 0.0, face.length)
        if s is None:
            raise SystemExit(f"street furniture: no clear spot for the pictured hydrant {h['key']}")
        items.append(item(f"hydrant.pictured.{h['key']}", face, s, across, place="corner",
                          streets=c["streets"], corner=c["quadrant"], face=face.id, grade="attested",
                          sources=h["sources"], note=h["note"],
                          moved_m=r2(abs(s - (s0 + sign * h["along_m"])))))
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


def lay_poles(grid, section, trees_doc, items):
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

    def on_face(face, s, across, lo, hi):
        blocked = blocked_intervals(face, walks, list(alleys.values()))
        k = 0
        while k * NUDGE_STEP_M <= NUDGE_MAX_M:
            for x in ((s,) if k == 0 else (s + k * NUDGE_STEP_M, s - k * NUDGE_STEP_M)):
                if lo <= x <= hi and not any(a < x < b for a, b, _ in blocked):
                    p, t = face.at(x, across)
                    if free(p):
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
    hit = on_face(face, s0, across, 0.0, face.length)
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
        h = on_face(face, s, across, s - 4.0, face.length - 4.0)
        if h:
            line18.append(pole(f"pole.18th#{k:02d}", h[1], h[2], "street", "inferred",
                               GLESSNER_POLE["sources"] + POLE_18TH_NOTE_SOURCES, "e18th",
                               liberty="L-prairie-utility-poles-3202", where=w18))
            k += 1
        s += POLE_SPACING_M
    # ...and one more short of Indiana Avenue's corner, where the line goes on beyond the district.
    last_s = face.project((line18[-1]["e"], line18[-1]["n"]))[0]
    if face.length - 8.0 - last_s > 0.5 * POLE_SPACING_M:
        h = on_face(face, face.length - 8.0, across, last_s + 10.0, face.length - 4.0)
        if h:
            line18.append(pole(f"pole.18th#{k:02d}", h[1], h[2], "street", "inferred",
                               GLESSNER_POLE["sources"] + POLE_18TH_NOTE_SOURCES, "e18th",
                               liberty="L-prairie-utility-poles-3202", where=w18))
    # 2. The alleys: a line down each, on its east side, an end pole in from each mouth.
    ends = []
    for aid in sorted(alleys):
        west, east = alley_edges(alleys[aid])
        edge = east
        L = poly_len(edge)
        n = max(1, round((L - 2 * POLE_MOUTH_IN_M) / POLE_SPACING_M))
        step = (L - 2 * POLE_MOUTH_IN_M) / n
        line = []
        for j in range(n + 1):
            s = POLE_MOUTH_IN_M + j * step
            got = None
            for dk in [0] + [d * sgn for d in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0) for sgn in (1, -1)]:
                x = min(max(s + dk, 1.0), L - 1.0)
                q, t = poly_at(edge, x)
                inward = (t[1], -t[0])   # walking south on the east edge, west is to the right
                p = (q[0] + inward[0] * POLE_ALLEY_INSET_M, q[1] + inward[1] * POLE_ALLEY_INSET_M)
                if free(p):
                    got = (p, t)
                    break
            if got:
                line.append(pole(f"pole.{aid.replace('alley_', 'alley.')}#{j:02d}", got[0], got[1], "alley",
                                 "reconstructed", [], "alley", liberty="L-prairie-utility-poles-3202",
                                 alley=aid, where=f"in the alley {alleys[aid]['where']}"))
        if line:
            ends.append((aid, line[0], line[-1]))
        for a, b in zip(line, line[1:]):
            wires.append({"from": a["id"], "to": b["id"], "kind": "line", "grade": "reconstructed"})
    # The alley lines run on across the cross streets where one alley's foot meets the next one's head.
    for aid, head, foot in ends:
        for bid, head2, _ in ends:
            if bid != aid and math.dist((foot["e"], foot["n"]), (head2["e"], head2["n"])) < 2 * POLE_MOUTH_IN_M + 66 * FT + ALLEY_LINE_JOIN_M \
                    and abs(foot["e"] - head2["e"]) < ALLEY_LINE_JOIN_M and head2["n"] < foot["n"]:
                wires.append({"from": foot["id"], "to": head2["id"], "kind": "line", "grade": "reconstructed"})
    # 18th Street's line: along the parkway, and from Glessner's pole into the alley behind it.
    for a, b in zip(line18, line18[1:]):
        wires.append({"from": a["id"], "to": b["id"], "kind": "line", "grade": "inferred"})
    head = next((h for aid, h, _ in ends if aid == GLESSNER_POLE["alley"]), None)
    if head:
        wires.append({"from": line18[0]["id"], "to": head["id"], "kind": "line", "grade": "inferred"})
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
            h = on_face(face, s, across, 4.0, face.length - 4.0)
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
    return poles, wires


def build():
    grid = json.loads(GRID.read_text())
    section = json.loads(SECTION.read_text()) if SECTION.exists() else None
    trees = json.loads(TREES.read_text()) if TREES.exists() else None
    items = lay_lamps(grid, section, trees)
    items += lay_hydrants(grid, section, trees, items)
    poles, wires = lay_poles(grid, section, trees, items)
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
                "form": ("A fluted cast-iron post on a moulded base, a ladder bar under the lantern, a four-sided "
                         "glass lantern tapering out to its top, a pyramidal cap and a finial; painted iron. About "
                         "3 m. Corner lamps stand on a small stone footing."),
                "form_grade": "attested",
                "form_sources": ["chicagology_1811_ames_photo", "taylor_2135_glessner_exterior_1887_1889",
                                 "chicagology_2140_photo_b"],
                "form_note": ("Read off the 1811 photograph, Taylor's no. 2135 and the second 2140 photograph, the "
                              "three that show a post whole and near. Every lamp is drawn with that one post. 1904 "
                              "is gas: electric standards appear only in pictures dated after it. The scene is a "
                              "July morning with no night, so no lamp is lit."),
                "model_m": LAMP,
                "what": "A cast-iron gas lamp post",
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
                         "on a stone footing; the pictured mid-block lamps at their lots; the rest of every face "
                         "at about 160 ft, the two sides of a street staggered, on the parkway 0.4 m off the walk, "
                         "each moved along the parkway clear of an elm, a carriage walk or an alley mouth. A corner "
                         "where a face meets a curved return (Calumet at 18th) has no corner of its own."),
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
                "note": ("Glessner's pole where the photograph shows it, on 18th Street's south parkway at the "
                         "stable's corner by the alley; the line on west from it to Indiana Avenue at about 34 m "
                         "(Taylor 2135 and the Detroit view show no pole on 18th Street east of the alley), and "
                         "into the alley behind it; a line down every alley on its east side, its end poles 2.5 m in "
                         "from the mouths and spanned across the cross streets where alleys meet; none on the "
                         "Prairie Avenue parkways. Each pole clear of the elms, lamps, hydrants, carriage walks "
                         "and alley mouths."),
                "note_by_class": {
                    "trolley": ("22nd Street's overhead: a pair of plain poles at about 34 m, one in the north "
                                "parkway by the curb and one opposite it across the street, a span wire between "
                                "them at 6.6 m and two contact wires along the street over the tracks at 5.6 m."),
                },
            },
        },
        "wire_model": {"sag_frac": WIRE_SAG_FRAC, "trolley": TROLLEY},
        "street_names": {k: v.get("name_1904", k) for k, v in grid["streets"].items()},
        "sources": source_lines(cited + ["chicagology_1811_ames_photo", "taylor_2135_glessner_exterior_1887_1889",
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = dump(doc)
    json.loads(text)
    if a.check:
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
