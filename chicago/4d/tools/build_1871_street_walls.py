#!/usr/bin/env python3
"""T-3804: the 1871 street walls round the jaunt stops, matched to the period street views.

    python3 tools/build_1871_street_walls.py           # write data/context/1871/street_walls.json
    python3 tools/build_1871_street_walls.py --check   # the committed file still stands on its inputs

The generated 1871 city (generators/city_1871_emit.py) fills each downtown block with rows
facing one street, so the other street of a corner block shows the rows' side walls and
the gaps between them, and the rows' storeys and fronts are drawn from the whole city's mix.
The period views show something else on these business streets: party wall to party wall,
four and five storeys, Italianate stone and brick fronts with hooded arched windows, cast-iron
shop fronts, bracketed cornices and here and there a mansard. This tool writes, for the block
faces round the jaunt stops (the faces `directory_fronts.json` already calibrates):

  * `profiles`, one per street, read from the views listed in each (storeys, the mix of stone,
    brick and painted fronts, window heads, ground storeys, cornices, mansards, balconies);
  * `rows`, a restyle of every generated shop front standing on those faces: its storeys and
    height brought to its street's, its front's material and its style drawn from the profile;
  * `fill`, new attached fronts where a face has none (the side walls and gaps), each sized
    to the gap and set on the face's own front line, never into a row or a landmark;
  * `buildings`, the named buildings these faces held in 1871 that the stops look at
    (the St. James Hotel, McVicker's Theatre, the long marble block facing the Court House
    square on Clark Street, Crosby's neighbour to the west), each on the rows that stand
    where the sources put it and built to its picture.

Every number here is a reconstruction bounded by those views (docs/LIBERTIES.md
L-1871-street-walls); the named buildings' identities and places are attested or inferred
as each one says. renderers/web/js/city-context.js reads the file at load and
renderers/web/js/city-fronts.js builds the fronts.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "data" / "context" / "1871.json"
DIRECTORY = ROOT / "data" / "context" / "1871" / "directory_fronts.json"
OUT = ROOT / "data" / "context" / "1871" / "street_walls.json"
SIDECARS = ROOT / "data" / "sidecars" / "1871"
SOURCES = ROOT / "data" / "sources"
LIBERTY = "L-1871-street-walls"

# Kit eave heights per storey count (data/context/1871/kit.json commercial_N).
KIT = {3: ("commercial_3", 11.5), 4: ("commercial_4", 15.2), 5: ("commercial_5", 18.5), 6: ("commercial_6", 22.0)}

# ---------------------------------------------------------------------------
# PROFILES. Weights are shares of a face's fronts; every one is a reconstruction
# bounded by the views named (forms read from the pictures; no pixel is sampled).
PROFILES = {
    "lake": {
        "label": "Lake Street, the old wholesale row",
        "sources": ["nypl_carbutt_lake_street_east_from_clark_stereo"],
        "note": "Carbutt's 'Lake street, East from Clark': attached four- and five-storey fronts party wall to party wall, segmental and round-headed windows in hooded surrounds, bracketed cornices, lettered friezes, cast-iron shop fronts under awnings. The late-1860s Lake Street stereoview in the owner's references (rights not yet traced, so read only) shows the same row with cream stone fronts, a mansard or two, round-arched iron arcades and an iron balcony.",
        "storeys": {4: .45, 5: .55}, "facade": {"stone": .5, "brick": .25, "painted": .25},
        "heads": {"segmental": .45, "round": .4, "hood": .15}, "ground": {"piers": .55, "arcade": .45},
        "cornice": {"bracketed": .7, "heavy": .3}, "mansard": .18, "balcony": .14, "top": .2,
    },
    "clark_square": {
        "label": "Clark Street facing the Court House square",
        "sources": ["nypl_carbutt_clark_street_north_from_washington_stereo"],
        "note": "Carbutt's 'Clark street, North from Washington': on the east side, facing the square, one long pale stone front of five storeys, its windows round-headed in even rows, an iron balcony along the first upper storey, a lettered frieze under the cornice and an arched ground floor under awnings.",
        "storeys": {5: 1.0}, "facade": {"stone": 1.0}, "heads": {"round": 1.0}, "ground": {"arcade": 1.0},
        "cornice": {"heavy": 1.0}, "mansard": 0, "balcony": 1.0, "top": 0, "tone": 0,
    },
    "clark": {
        "label": "Clark Street",
        "sources": ["nypl_carbutt_clark_street_north_from_washington_stereo", "nypl_carbutt_lake_street_east_from_clark_stereo"],
        "note": "Carbutt's Clark Street view: pale stone and brick fronts of four and five storeys, round and segmental heads, awnings.",
        "storeys": {4: .45, 5: .55}, "facade": {"stone": .45, "brick": .35, "painted": .2},
        "heads": {"round": .45, "segmental": .4, "hood": .15}, "ground": {"piers": .6, "arcade": .4},
        "cornice": {"bracketed": .75, "heavy": .25}, "mansard": .12, "balcony": .1, "top": .2,
    },
    "state": {
        "label": "State Street",
        "sources": ["nypl_carbutt_booksellers_row_state_street_stereo"],
        "note": "Carbutt's 'Book Seller's Row, State Street': a five-storey pale stone ('Athens marble') front of identical units, round-arched windows in even rows, a heavy bracketed cornice, iron and glass shop fronts under awnings.",
        "storeys": {4: .35, 5: .65}, "facade": {"stone": .6, "brick": .25, "painted": .15},
        "heads": {"round": .55, "segmental": .3, "hood": .15}, "ground": {"piers": .6, "arcade": .4},
        "cornice": {"heavy": .55, "bracketed": .45}, "mansard": .15, "balcony": .1, "top": .1,
    },
    "lasalle": {
        "label": "LaSalle Street",
        "sources": ["nypl_carbutt_140_chamber_of_commerce"],
        "note": "Carbutt's Chamber of Commerce card shows across LaSalle a brick block of five storeys under a tall mansard; Kurz's 1865 'La Salle Street from Court House Square' in the owner's references (rights not yet traced, so read only) shows the street as attached stone fronts of four and five storeys with arched windows, several under mansards.",
        "storeys": {4: .45, 5: .55}, "facade": {"stone": .5, "brick": .35, "painted": .15},
        "heads": {"round": .5, "segmental": .35, "hood": .15}, "ground": {"piers": .65, "arcade": .35},
        "cornice": {"bracketed": .6, "heavy": .4}, "mansard": .3, "balcony": .1, "top": .15,
    },
    "cross": {
        "label": "Randolph, Washington, Madison and Dearborn",
        "sources": ["nypl_carbutt_lake_street_east_from_clark_stereo", "loc_stereo_1s47902_crosbys_opera_house"],
        "note": "The business streets between: Carbutt's Lake Street and Crosby's Opera House cards show four- and five-storey brick and stone fronts, segmental heads on the brick, round on the stone, bracketed cornices.",
        "storeys": {4: .5, 5: .4, 3: .1}, "facade": {"brick": .45, "stone": .35, "painted": .2},
        "heads": {"segmental": .5, "round": .35, "hood": .15}, "ground": {"piers": .7, "arcade": .3},
        "cornice": {"bracketed": .75, "heavy": .25}, "mansard": .1, "balcony": .08, "top": .2,
    },
}
FACE_PROFILE = {"lake": "lake", "clark": "clark", "state": "state", "lasalle": "lasalle"}
# The four faces bounding the Court House square have no fronts: its fence and lawn.
SQUARE_FACES = {"clark_w_randolph_washington", "lasalle_e_randolph_washington",
                "randolph_s_clark_lasalle", "washington_n_clark_lasalle"}

# ---------------------------------------------------------------------------
# NAMED BUILDINGS. `rows` are generated rows restyled into the building; `wing` is a new
# front added where the generated city leaves a gap the building filled.
BUILDINGS = [
    {
        "id": "st_james_hotel_1871", "name": "St. James Hotel",
        "rows": ["context1871_core_0193_037_s_r00", "context1871_core_0193_037_s_r01", "context1871_core_0193_037_s_r02"],
        "wing": {"face": "washington_n_state_dearborn", "from_e": 791.05, "to_e": 810.62, "depth_m": 24.0},
        "storeys": 5, "facade": "brick", "tone": 4,
        "style": {"heads": "round", "pair": True, "attic": True, "ground": "piers", "cornice": "parapet", "awning": True},
        "lettering": "ST. JAMES HOTEL",
        "grade": "inferred",
        "sources": ["edwards_chicago_directory_1871", "andreas_1885_v2", "loc_stereo_1s47902_crosbys_opera_house"],
        "identity": "Edwards' 1871 directory: 'St. James Hotel, Washington Libbey propr. State, nw. cor. Washington'. Andreas (vol. 2, p. 508): the Stewart House at the corner of State and Washington, 'including Nos. 92, 94, 96 and 98' State, reopened as the Merchants' Hotel, burnt, 're-built on a larger scale' and opened in January 1868 as the St. James, kept by Libby & Harlow until the fire.",
        "place": "The State Street front from the Washington corner north over the three generated rows there (about 41 m, the corner and Nos. 92-98 at the directory's spacing), and its Washington Street front from the corner west to Crosby's.",
        "form": "Carbutt's card of Crosby's Opera House shows the corner building beside it before 1868: five storeys of brick, paired round-arched windows in hooded surrounds on three upper storeys, an arcaded attic of small arched windows under a bracketed cornice with blocks along its parapet, a shop storey under awnings. The St. James that replaced it in 1867-68 is not pictured; it is built in the same form at the same height, which is reconstructed.",
    },
    {
        "id": "crosbys_west_neighbour_1871", "name": "Brick block west of Crosby's Opera House",
        "rows": ["context1871_core_0210_004_n_r06"],
        "storeys": 5, "facade": "brick", "tone": 0,
        "style": {"heads": "segmental", "top": True, "ground": "house", "cornice": "heavy", "awning": False},
        "grade": "reconstructed",
        "sources": ["loc_stereo_1s47902_crosbys_opera_house"],
        "identity": "Unnamed: the front standing against Crosby's west wall in Carbutt's card. Its owner and firms are not identified.",
        "place": "The first generated row west of the opera house on Washington Street, as the card shows it.",
        "form": "The card shows five storeys of red brick, plain segmental-headed sash windows on stone sills, round-headed windows in the top storey, a heavy cornice on large scroll brackets, and a ground storey of windows and an arched door over an areaway rather than a shop front.",
    },
    {
        "id": "mcvickers_theatre_1871", "name": "McVicker's Theatre",
        "rows": ["context1871_core_0116_006_s_r03", "context1871_core_0116_006_s_r04"],
        "storeys": 4, "eave_m": 17.0, "facade": "brick", "tone": 3,
        "style": {"heads": "hood", "ground": "porch", "cornice": "bracketed", "tower": True, "awning": False},
        "lettering": "McVICKER'S THEATRE",
        "grade": "inferred",
        "sources": ["edwards_chicago_directory_1871", "andreas_1885_v2", "andreas_1885_v2_mcvickers_theatre_plate"],
        "identity": "Edwards' 1871 directory lists McVicker's Theatre on 'Madison, bet. Dearborn and State'; Andreas (vol. 2, pp. 597-599) gives its building in 1857 and its remodelling in 1871, when 'nothing but the walls of the old theater remained', reopened on 29 August, six weeks before the fire.",
        "place": "On Madison Street's south side east of the Tribune building, over the two generated rows there; its exact lots are not recorded, so the place along the block is reconstructed.",
        "form": "Andreas's engraving (p. 598) of the 1857 theatre: a four-storey brick front with corniced hoods over its windows, a bracketed cornice with the name lettered under it, a belvedere over the middle with its own cornice and flagstaff, and an iron colonnade carrying a balcony across the ground storey. The 1871 remodelling kept the walls, so the front is taken as the engraving shows it; that it kept its porch and belvedere is reconstructed.",
    },
    {
        "id": "clark_street_marble_block_1871", "name": "Marble front facing the Court House square",
        "rows": [],  # the whole face takes profile clark_square
        "face": "clark_e_randolph_washington",
        "grade": "reconstructed",
        "sources": ["nypl_carbutt_clark_street_north_from_washington_stereo"],
        "identity": "Unnamed: the long pale stone front Carbutt photographed on the east side of Clark Street from Washington north. The directory places the firms in it by number; the building itself is not named in the sources read.",
        "place": "Clark Street's east side between Washington and Randolph, opposite the Court House square.",
        "form": "Five storeys of pale stone under one heavy cornice, round-headed windows in even rows, an iron balcony along the first upper storey, an arched ground floor under awnings.",
    },
]

# ---------------------------------------------------------------------------
def fnv(s: str) -> int:
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def pick(weights: dict, key: str):
    """A deterministic weighted choice."""
    u = (fnv(key) % 10007) / 10007
    acc = 0.0
    items = list(weights.items())
    for k, w in items:
        acc += w
        if u < acc:
            return k
    return items[-1][0]


def chance(p: float, key: str) -> bool:
    return (fnv(key) % 10007) / 10007 < p


def landmark_polys():
    out = []
    for f in sorted(glob.glob(str(SIDECARS / "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if not isinstance(d, dict) or not d.get("footprint") or "placement" not in d:
            continue
        p = d["placement"]
        if p.get("vertical_anchor") == "water":
            continue
        th = math.radians(p.get("rotation_deg", 0))
        c, s = math.cos(th), math.sin(th)
        fp = d["footprint"]
        polys = fp.get("polygons") or [fp.get("polygon")]
        for poly in polys:
            if poly:
                out.append((d.get("id", Path(f).stem),
                            [(p["local_e"] + u * c + v * s, p["local_n"] - u * s + v * c) for u, v in poly]))
    return out


def inside(x, y, P):
    r = False
    j = len(P) - 1
    for i in range(len(P)):
        a, b = P[i], P[j]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            r = not r
        j = i
    return r


def corners(b):
    w, d = b["width_m"], b["depth_m"]
    r = -b["bearing_deg"] * math.pi / 180
    c, s = math.cos(r), math.sin(r)
    return [(b["e"] + c * x + s * z, b["n"] + s * x - c * z) for x, z in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]


def dropped(b, lms):
    """city-context.js droppedByStructure: the centre inside a landmark, or a landmark corner inside the row."""
    w, d = b["width_m"], b["depth_m"]
    r = -b["bearing_deg"] * math.pi / 180
    c, s = math.cos(r), math.sin(r)
    for _, P in lms:
        if inside(b["e"], b["n"], P):
            return True
        for e, n in P:
            dx, dz = e - b["e"], -(n - b["n"])
            x, z = c * dx - s * dz, s * dx + c * dz
            if abs(x) < w / 2 + .25 and abs(z) < d / 2 + .25:
                return True
    return False


def clip_band(poly, o0, o1):
    """Sutherland-Hodgman clip of a (t, o) polygon to o0 <= o <= o1; returns t-range or None."""
    def clip(pts, keep, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ka, kb = keep(a), keep(b)
            if kb:
                if not ka:
                    out.append(inter(a, b))
                out.append(b)
            elif ka:
                out.append(inter(a, b))
        return out

    def at(o):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (o - a[1]) / (b[1] - a[1]), o)
    pts = clip(poly, lambda p: p[1] >= o0, at(o0))
    if pts:
        pts = clip(pts, lambda p: p[1] <= o1, at(o1))
    if len(pts) < 2:
        return None
    return min(p[0] for p in pts), max(p[0] for p in pts)


def face_frame(f):
    a, b = f["a"], f["b"]
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    # The side's inward direction (away from the street's centre line).
    nrm = (-u[1], u[0])
    want = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0)}[f["side"]]
    if nrm[0] * want[0] + nrm[1] * want[1] < 0:
        nrm = (-nrm[0], -nrm[1])
    return a, u, nrm, L


def to_to(a, u, nrm, e, n):
    return (e - a[0]) * u[0] + (n - a[1]) * u[1], (e - a[0]) * nrm[0] + (n - a[1]) * nrm[1]


def style_of(prof, key):
    st = {
        "heads": pick(prof["heads"], key + ":heads"),
        "ground": pick(prof["ground"], key + ":ground"),
        "cornice": pick(prof["cornice"], key + ":cornice"),
    }
    if chance(prof["mansard"], key + ":mansard"):
        st["mansard"] = True
    if chance(prof["balcony"], key + ":balcony"):
        st["balcony"] = True
    if chance(prof["top"], key + ":top"):
        st["top"] = True
    return st


def build():
    ctx = json.load(open(CONTEXT))
    dfr = json.load(open(DIRECTORY))
    lms = landmark_polys()
    rows = [b for b in ctx["buildings"] if not dropped(b, lms)] if True else []
    near = [b for b in rows if 250 < b["e"] < 1100 and -800 < b["n"] < 100]
    byid = {b["id"]: b for b in near}
    named_rows = {rid: bd for bd in BUILDINGS for rid in bd["rows"]}
    face_override = {bd["face"]: bd for bd in BUILDINGS if bd.get("face")}

    out_rows, fill, report = {}, [], []
    # Each street's front line: the median offset of the shop fronts standing on it.
    street_offs = {}
    for f in dfr["faces"]:
        a, u, nrm, L = face_frame(f)
        for b in near:
            P = corners(b)
            r = -b["bearing_deg"] * math.pi / 180
            out = (-math.sin(r), math.cos(r))
            t, o = to_to(a, u, nrm, (P[0][0] + P[1][0]) / 2, (P[0][1] + P[1][1]) / 2)
            if -(out[0] * nrm[0] + out[1] * nrm[1]) > .7 and f["half_m"] - 4 < o < f["half_m"] + 6 and -1 < t < L + 1:
                street_offs.setdefault(f["street"], []).append(o)
    street_front = {k: sorted(v)[len(v) // 2] for k, v in street_offs.items()}
    for f in dfr["faces"]:
        a, u, nrm, L = face_frame(f)
        street = f["street"].split()[0].lower()
        pid = FACE_PROFILE.get(street, "cross")
        if f["id"] in face_override:
            pid = "clark_square"
        prof = PROFILES[pid]
        # The rows standing on this face: front facing the street, its front centre on the face's band.
        on, occ, offs = [], [], []
        band0 = street_front.get(f["street"], f["half_m"]) - .5
        for b in near:
            P = corners(b)
            tp = [to_to(a, u, nrm, e, n) for e, n in P]
            r = -b["bearing_deg"] * math.pi / 180
            out = (-math.sin(r), math.cos(r))
            fe, fn = (P[0][0] + P[1][0]) / 2, (P[0][1] + P[1][1]) / 2
            t, o = to_to(a, u, nrm, fe, fn)
            facing = -(out[0] * nrm[0] + out[1] * nrm[1])
            if facing > .7 and f["half_m"] - 4 < o < f["half_m"] + 6 and -1 < t < L + 1 and b["kit"].startswith("commercial"):
                on.append((t, b))
                offs.append(o)
            span = clip_band(tp, band0, band0 + 10.5)
            if span:
                occ.append(span)
        for _, P in lms:
            span = clip_band([to_to(a, u, nrm, e, n) for e, n in P], band0, band0 + 10.5)
            if span:
                # city-context.js drops a row a landmark's corner comes within 0.25 m of.
                occ.append((span[0] - .4, span[1] + .4))
        if f["id"] in SQUARE_FACES:
            continue
        # Restyle the rows on the face.
        for t, b in on:
            if b["id"] in named_rows:
                continue
            key = b["id"]
            storeys = pick(prof["storeys"], key + ":storeys") if b["kit"] != "commercial_6" or 6 not in prof["storeys"] else 6
            kit, eave = KIT[storeys]
            facade = pick(prof["facade"], key + ":facade")
            tone = prof.get("tone", b.get("tone", 0))
            if "tone" in prof:  # one front, one height and one stone (the marble block)
                out_rows[key] = [kit, eave, facade, tone, style_of(prof, key), pid]
                continue
            out_rows[key] = [kit, round(eave * (0.97 + 0.06 * ((fnv(key + ':h') % 100) / 100)), 2), facade, tone, style_of(prof, key), pid]
        # Fill the gaps.
        front_o = sorted(offs)[len(offs) // 2] if offs else street_front.get(f["street"], f["half_m"])
        lo, hi = f["cross_half_m"][0] + .3, L - f["cross_half_m"][1] - .3
        occ.sort()
        free, cur = [], lo
        for t0, t1 in occ:
            if t1 <= cur:
                continue
            if t0 > cur:
                free.append((cur, min(t0, hi)))
            cur = max(cur, t1)
        if cur < hi:
            free.append((cur, hi))
        base = next((b.get("base_m", 3.2) for _, b in on), 3.2)
        for g0, g1 in free:
            g0, g1 = g0 + .02, g1 - .02
            span = g1 - g0
            if span < 4.5:
                continue
            n_lots = max(1, round(span / 10.5))
            widths = [8.5 + 4 * ((fnv(f"{f['id']}:{g0:.1f}:{k}") % 100) / 100) for k in range(n_lots)]
            sc = span / sum(widths)
            t = g0
            for k, w0 in enumerate(widths):
                w = w0 * sc
                tc = t + w / 2
                t += w
                fid = f"street_wall_1871_{f['id']}_{int(round(tc))}"
                # Depth: as far back as the block allows, 8 to 22 m.
                depth = 22.0
                for step in range(1, 45):
                    d = step * .5
                    hit = False
                    for dt in (-w / 2 + .3, 0, w / 2 - .3):
                        pe = a[0] + u[0] * (tc + dt) + nrm[0] * (front_o + d)
                        pn = a[1] + u[1] * (tc + dt) + nrm[1] * (front_o + d)
                        if any(inside(pe, pn, corners(b)) for b in near if abs(b["e"] - pe) < 40 and abs(b["n"] - pn) < 40) \
                                or any(inside(pe, pn, P) for _, P in lms):
                            hit = True
                            break
                    if hit:
                        depth = max(8.0, d - .3)
                        break
                ce = a[0] + u[0] * tc + nrm[0] * (front_o + depth / 2)
                cn = a[1] + u[1] * tc + nrm[1] * (front_o + depth / 2)
                bearing = math.degrees(math.atan2(-nrm[0], -nrm[1]))
                storeys = pick(prof["storeys"], fid + ":storeys")
                kit, eave = KIT[storeys]
                facade = pick(prof["facade"], fid + ":facade")
                tone = prof.get("tone", fnv(fid) % 12)
                if dropped({"e": ce, "n": cn, "width_m": w - .04, "depth_m": depth, "bearing_deg": bearing}, lms):
                    continue
                fill.append([fid, round(ce, 2), round(cn, 2), round(w - .04, 2), round(depth, 2),
                             round(eave * (0.97 + 0.06 * ((fnv(fid + ':h') % 100) / 100)), 2), round(bearing, 2),
                             kit, tone, facade, style_of(prof, fid), pid, base])
        report.append((f["id"], pid, len(on), sum(1 for x in fill if x[0].startswith(f"street_wall_1871_{f['id']}_"))))

    # Named buildings.
    named = []
    for bd in BUILDINGS:
        rec = {k: bd[k] for k in ("id", "name", "grade", "sources", "identity", "place", "form")}
        rec["rows"] = list(bd["rows"])
        if bd.get("face"):
            rec["face"] = bd["face"]
            rec["rows"] = sorted(k for k, v in out_rows.items() if v[5] == "clark_square")
            for k in rec["rows"]:
                out_rows[k][3] = 0
        else:
            st = dict(bd["style"])
            storeys = bd["storeys"]
            kit, eave = KIT[min(6, max(3, storeys))]
            eave = bd.get("eave_m", eave)
            for rid in bd["rows"]:
                if rid not in byid:
                    raise SystemExit(f"{bd['id']}: row {rid} is not a standing generated row")
                out_rows[rid] = [kit, eave, bd["facade"], bd["tone"], {k: v for k, v in st.items() if k != "tower"}, bd["id"]]
            if st.get("tower"):
                # One belvedere over the middle of the whole front, on the row that holds it:
                # [e, n] of the front's middle and the belvedere's width.
                ends = [c for rid in bd["rows"] for c in corners(byid[rid])[:2]]
                ax = (ends[1][0] - ends[0][0], ends[1][1] - ends[0][1])
                L0 = math.hypot(*ax)
                ax = (ax[0] / L0, ax[1] / L0)
                ts = [(c[0] - ends[0][0]) * ax[0] + (c[1] - ends[0][1]) * ax[1] for c in ends]
                tm = (min(ts) + max(ts)) / 2
                me, mn = ends[0][0] + ax[0] * tm, ends[0][1] + ax[1] * tm
                width = min(8.0, (max(ts) - min(ts)) * .38)
                host = min(bd["rows"], key=lambda rid: math.dist((byid[rid]["e"], byid[rid]["n"]), (me, mn)))
                for rid in bd["rows"]:
                    P = corners(byid[rid])
                    q = [(c[0] - ends[0][0]) * ax[0] + (c[1] - ends[0][1]) * ax[1] for c in P[:2]]
                    if min(q) - .01 <= tm <= max(q) + .01:
                        host = rid
                out_rows[host][4] = {**out_rows[host][4], "tower": [round(me, 2), round(mn, 2), round(width, 2)]}
            if bd.get("wing"):
                wg = bd["wing"]
                face = next(f for f in dfr["faces"] if f["id"] == wg["face"])
                a, u, nrm, L = face_frame(face)
                e0, e1 = wg["from_e"], wg["to_e"]
                # The wing's front on the face's line, its own rows' offset.
                n_front = a[1] + nrm[1] * (wg.get("front_o", face["half_m"]) + .36)
                ce, cn = (e0 + e1) / 2, n_front + nrm[1] * wg["depth_m"] / 2
                wid = f"{bd['id']}_wing"
                fill.append([wid, round(ce, 2), round(cn, 2), round(e1 - e0, 2), wg["depth_m"], eave,
                             round(math.degrees(math.atan2(-nrm[0], -nrm[1])), 2), kit, bd["tone"], bd["facade"], st, bd["id"], 3.2])
                rec["rows"].append(wid)
            if bd.get("lettering"):
                rec["lettering"] = bd["lettering"]
        named.append(rec)

    # Fill rows must not stand in each other: drop any whose footprint overlaps an earlier one.
    kept = []
    named_ids = {bd["id"] for bd in BUILDINGS}
    for x in sorted(fill, key=lambda x: 0 if x[11] in named_ids else 1):
        b = {"e": x[1], "n": x[2], "width_m": x[3], "depth_m": x[4], "bearing_deg": x[6]}
        P = corners(b)
        clash = False
        for y in kept:
            Q = corners({"e": y[1], "n": y[2], "width_m": y[3] - .2, "depth_m": y[4] - .2, "bearing_deg": y[6]})
            if any(inside(e, n, Q) for e, n in P) or any(inside(e, n, P) for e, n in Q):
                clash = True
                break
        if not clash:
            kept.append(x)
    fill = kept

    doc = {
        "_doc": "T-3804. The 1871 street walls round the jaunt stops: per-street profiles read from the period street views, a restyle of each generated shop front on the stops' block faces, new attached fronts where a face had only side walls and gaps, and the named buildings the stops look at. Written by tools/build_1871_street_walls.py; read by renderers/web/js/city-context.js, built by renderers/web/js/city-fronts.js. Every form is reconstructed (L-1871-street-walls) unless a building says otherwise.",
        "schema": "chicago-1871-street-walls-v1",
        "ticket": "T-3804",
        "scene": "1871",
        "liberty": LIBERTY,
        "fields": {"rows": ["kit", "eave_m", "facade", "tone", "style", "profile_or_building"],
                   "fill": ["id", "e", "n", "width_m", "depth_m", "eave_m", "bearing_deg", "kit", "tone", "facade", "style", "profile_or_building", "base_m"]},
        "profiles": {k: {kk: vv for kk, vv in v.items()} for k, v in PROFILES.items()},
        "buildings": named,
        "rows": dict(sorted(out_rows.items())),
        "fill": fill,
    }
    for p in doc["profiles"].values():
        p["storeys"] = {str(k): v for k, v in p["storeys"].items()}
    return doc, report


def check(doc):
    problems = []
    ctx = json.load(open(CONTEXT))
    ids = {b["id"] for b in ctx["buildings"]}
    for rid in doc["rows"]:
        if rid not in ids:
            problems.append(f"row {rid} is not in data/context/1871.json")
    seen = set()
    for x in doc["fill"]:
        if x[0] in seen or x[0] in ids:
            problems.append(f"fill id {x[0]} is not unique")
        seen.add(x[0])
    lms = landmark_polys()
    for x in doc["fill"]:
        b = {"e": x[1], "n": x[2], "width_m": x[3], "depth_m": x[4], "bearing_deg": x[6]}
        if dropped(b, lms):
            problems.append(f"fill {x[0]} stands in a landmark's footprint")
    srcs = set()
    for p in doc["profiles"].values():
        srcs.update(p["sources"])
    for bd in doc["buildings"]:
        srcs.update(bd["sources"])
        if bd["grade"] not in ("attested", "inferred", "reconstructed"):
            problems.append(f"{bd['id']}: grade {bd['grade']}")
    for s in sorted(srcs):
        if not (SOURCES / f"{s}.json").exists():
            problems.append(f"source {s} does not resolve in data/sources/")
    lib = (ROOT / "docs" / "LIBERTIES.md").read_text()
    if f"### {LIBERTY} " not in lib:
        problems.append(f"{LIBERTY} is not in docs/LIBERTIES.md")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.check:
        doc = json.load(open(OUT))
        problems = check(doc)
        for p in problems:
            print("street walls 1871:", p)
        print(f"street walls 1871: {len(doc['rows'])} fronts restyled, {len(doc['fill'])} added, {len(doc['buildings'])} named"
              + (" — OK" if not problems else f" — {len(problems)} problem(s)"))
        sys.exit(1 if problems else 0)
    doc, report = build()
    OUT.write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n")
    if args.report:
        for r in report:
            print(*r)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['rows'])} fronts restyled, {len(doc['fill'])} added, "
          f"{len(doc['buildings'])} named, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
