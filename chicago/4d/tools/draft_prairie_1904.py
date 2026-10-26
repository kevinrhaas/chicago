#!/usr/bin/env python3
"""The Prairie Avenue district draft builder: one kit-built record per building (T-2329).

    python3 tools/draft_prairie_1904.py            write every drafted block's records
    python3 tools/draft_prairie_1904.py --check    re-derive in memory; refuse if a
                                                   committed record differs, or if a
                                                   drafted building has no record
    python3 tools/draft_prairie_1904.py --self-test

The owner's district pass (2026-10-08) drafts the whole of Prairie Avenue as a
serviceable first model that the per-building tickets then refine in place. This tool is
that pass's builder, and it is DATA-DRIVEN: it reads

  * the traced Sanborn footprints   data/traces/prairie_1904_footprints_s<sheet>.json
  * the sheet census                chicago/prairie_1904_v1/data/sheet_census/sheet-<sheet>.json
  * the T-1837 frontage register    tickets/evidence/T-1837-prairie-1904-architectural-study/
                                    frontage-register.csv (the tickets repo), or the copy of
                                    the rows it needs that this tool commits beside the rules
  * the draft rules                 data/components/prairie_1904/draft_prairie_1904.json

and writes `data/structures/<id>.json`, archetype `prairie_draft`, for every building on
every block side the rules name. The next block (T-2160, T-2161, T-2162) is drafted by
adding its sheet and frontage rows to the rules — not by editing this file.

THE PLAN. Each traced part is scan-filled on a 0.25 m grid in its lot's own frame (u from
the rear lot line toward the street, v along the street front) and replaced by the
largest rectangles that fit INSIDE the fill (max_rects, coverage in the rules). The
rectangles are therefore never larger than the Sanborn polygon, and never the parcel's.
The main part's largest rectangle is the main body; its other rectangles are wings or,
standing at the front and shallow, bays; the sheet's ranges, porches and stone fronts
keep their roles. A building's record is placed at its main body's rear corner, rotated
to its lot.

THE ELEVATION. Storeys come from the map's printed notation (`3B`, `2½S.B.; rear2B`):
the leading figure is the full storeys, a ½ is a roof storey, `rearN` sets the ranges;
for service buildings the census reading (`2-storey brick BARN`), unless the frontage row's
`services` entry carries a dated 1904 count (`storeys_1904`, with its own sources). Everything else —
heights, roof, bays, entrance, features — is the rules' family row overlaid with the
frontage's own row, and is RECONSTRUCTED; the record says so attribute by attribute.

Records already standing that are NOT drafts are never overwritten: the rules' `skip`
names them (Glessner, the 1808 K01 assembly, a coach house another ticket is building).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
RULES = ROOT / "data" / "components" / "prairie_1904" / "draft_prairie_1904.json"
REGISTER_ROWS = ROOT / "data" / "components" / "prairie_1904" / "draft_prairie_1904_register.json"
REGISTER_CSV = (ROOT / "tickets" / "evidence" / "T-1837-prairie-1904-architectural-study"
                / "frontage-register.csv")
GRID = ROOT / "data" / "street_grid" / "1904.json"
DATUM = ROOT / "data" / "datum.json"
STRUCTURES = ROOT / "data" / "structures"
SOURCE = "sanborn_1911_chicago_v3_sheet_28"
PHASE = "draft_1904"
ARCHETYPE = "prairie_draft"
REGISTER_KEYS = ("frontage_id", "address", "side", "sheet", "raw_story_notation", "map_material",
                 "family", "front_tickets", "rear_ticket")


def trace_path(sheet: str) -> Path:
    return ROOT / "data" / "traces" / f"prairie_1904_footprints_s{sheet}.json"


def census_path(sheet: str, block: dict | None = None) -> Path:
    # a block off Prairie Avenue reads its own census beside the rules (T-2982's "35x")
    if (block or {}).get("census_file"):
        return ROOT / block["census_file"]
    return REPO / "chicago" / "prairie_1904_v1" / "data" / "sheet_census" / f"sheet-{sheet}.json"


#: The streets a drafted lot faces, as the record names them: (in an address, on a card,
#: in an id). Prairie Avenue's are the names every earlier draft record carries.
STREETS = {
    "prairie": ("S. Prairie Avenue", "Prairie Avenue", "prairie"),
    "calumet": ("S. Calumet Avenue", "Calumet Avenue", "calumet"),
    "e20th": ("E. Twentieth Street", "East Twentieth Street", "e20th"),
    "michigan": ("S. Michigan Avenue", "Michigan Avenue", "michigan"),
    "indiana": ("S. Indiana Avenue", "Indiana Avenue", "indiana"),
    "e21st": ("E. Twenty-first Street", "East Twenty-first Street", "e21st"),
    "e16th": ("E. Sixteenth Street", "East Sixteenth Street", "e16th"),
    "e18th": ("E. Eighteenth Street", "East Eighteenth Street", "e18th"),
}


def register_rows(sheets) -> dict:
    """The register rows the draft reads. The register lives in the tickets repo, which a
    CI checkout of the code may not have, so the rows this pass reads are committed beside
    the rules and refreshed from the CSV whenever it is present."""
    if REGISTER_CSV.exists():
        rows = {}
        with REGISTER_CSV.open() as fh:
            for r in csv.DictReader(fh):
                if r["sheet"].strip() in sheets:
                    rows[r["frontage_id"]] = {k: r[k].strip() for k in REGISTER_KEYS}
        return rows
    return json.loads(REGISTER_ROWS.read_text())["rows"]


# ---------------------------------------------------------------- geometry

def lot_frame(parcel: dict):
    c = parcel["corners_local_m"]
    st = [v for k, v in sorted(c.items()) if k.endswith("_street")]
    rr = [v for k, v in sorted(c.items()) if k.endswith("_rear")]
    ms = [sum(x) / len(st) for x in zip(*st)]
    p0 = [sum(x) / len(rr) for x in zip(*rr)]
    u = [ms[0] - p0[0], ms[1] - p0[1]]
    n = math.hypot(*u)
    u = [u[0] / n, u[1] / n]
    v = [-u[1], u[0]]
    return p0, u, v


def to_uv(frame, p):
    p0, u, v = frame
    d = (p[0] - p0[0], p[1] - p0[1])
    return (d[0] * u[0] + d[1] * u[1], d[0] * v[0] + d[1] * v[1])


def scanfill(poly, cell):
    """Cells (i, j) whose centres fall inside `poly` (u, v), on a grid anchored at 0."""
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    i0, i1 = math.floor(min(us) / cell), math.ceil(max(us) / cell)
    j0, j1 = math.floor(min(vs) / cell), math.ceil(max(vs) / cell)
    cells = set()
    n = len(poly)
    for j in range(j0, j1):
        y = (j + 0.5) * cell
        xs = []
        for k in range(n):
            (ax, ay), (bx, by) = poly[k], poly[(k + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for i in range(max(i0, math.ceil(a / cell - 0.5)), min(i1, math.floor(b / cell - 0.5)) + 1):
                cells.add((i, j))
    return cells


def max_rect(cells):
    """The largest axis-aligned rectangle of cells (histogram method). (i0, j0, i1, j1) inclusive."""
    if not cells:
        return None
    is_ = [c[0] for c in cells]
    js = [c[1] for c in cells]
    I0, I1, J0, J1 = min(is_), max(is_), min(js), max(js)
    heights = [0] * (I1 - I0 + 1)
    best, out = 0, None
    for j in range(J0, J1 + 1):
        for i in range(I0, I1 + 1):
            heights[i - I0] = heights[i - I0] + 1 if (i, j) in cells else 0
        stack = []
        for k in range(len(heights) + 1):
            h = heights[k] if k < len(heights) else 0
            start = k
            while stack and stack[-1][1] >= h:
                s, sh = stack.pop()
                area = sh * (k - s)
                if area > best:
                    best, out = area, (I0 + s, j - sh + 1, I0 + k - 1, j)
                start = s
            stack.append((start, h))
    return out


def footprint_uv(sid: str, frame, datum) -> list:
    """Another record's footprint in a lot frame: its polygon turned by its rotation (clockwise,
    x east at 0 degrees, as the draft's own placements are) and set at its UTM position."""
    ph = json.loads((STRUCTURES / f"{sid}.json").read_text())["phases"][0]
    pos = ph["position"]
    t = math.radians(pos["rotation_deg"])
    oe, on = pos["utm_e"] - datum["origin_utm_e"], pos["utm_n"] - datum["origin_utm_n"]
    return [to_uv(frame, (oe + x * math.cos(t) + y * math.sin(t), on - x * math.sin(t) + y * math.cos(t)))
            for x, y in ph["footprint"]["polygon"]]


def close_cells(cells, gap):
    """Fill runs of up to `gap` empty cells lying between filled ones along either axis: the
    drawn line between two traced buildings that stand as one (T-2351's joined coach house)."""
    out = set(cells)
    for (i, j) in cells:
        for di, dj in ((1, 0), (0, 1)):
            for n in range(2, gap + 2):
                if (i + di * n, j + dj * n) in cells:
                    if all((i + di * k, j + dj * k) not in cells for k in range(1, n)):
                        out |= {(i + di * k, j + dj * k) for k in range(1, n)}
                    break
    return out


def rects_for(poly, fit, front_from_u=None, keep_out=(), close=0):
    """Rectangles inside `poly`, largest first. With `front_from_u` (a frontage row's
    `front_body_from_u_m`) the first is the largest in front of that lot-frame u, so a
    house traced in one piece with its rear range keeps its street body as the main.
    `poly` may be a list of rings, filled as one (with `close`, across the line between)."""
    cell = fit["cell_m"]
    rings = poly if poly and isinstance(poly[0][0], (list, tuple)) else [poly]
    cells = set().union(*(scanfill(r, cell) for r in rings))
    if close:
        cells = close_cells(cells, close)
    for k in keep_out:
        cells -= scanfill(k, cell)
    fill = frozenset(cells)
    total = len(cells)
    out = []
    while cells and len(out) < fit["max_rects"]:
        pool = cells
        if front_from_u is not None and not out:
            pool = {c for c in cells if c[0] * cell >= front_from_u} or cells
        r = max_rect(pool)
        if r is None:
            break
        i0, j0, i1, j1 = r
        w, d = (i1 - i0 + 1) * cell, (j1 - j0 + 1) * cell
        if w * d < fit["min_rect_m2"] or min(w, d) < fit["min_side_m"]:
            break
        out.append((round(i0 * cell, 3), round(j0 * cell, 3), round((i1 + 1) * cell, 3), round((j1 + 1) * cell, 3)))
        cells -= {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)}
        if 1 - len(cells) / total >= fit["coverage"]:
            break
    covered = 1 - len(cells) / total if total else 0.0
    if fit.get("sliver_m"):
        out = merge_slivers(out, fill, cell, fit)
    return out, covered


def merge_slivers(rects, fill, cell, fit):
    """Fold each thin rectangle into the one it lies against (T-2690, the owner's sweep of
    2026-10-16: "this is not a sensible structure, there are several tall towers").

    A part traced a little off the lot's square, or with a shallow step in a wall, fills as
    its largest rectangle plus strips one to two metres thick along its sides. Each strip
    was built as a full-height piece under its own cornice, so a house stood flanked by
    slabs that read from the street as freestanding towers. A rectangle thinner than
    `sliver_m` is joined to a neighbour it touches when the box over both is at least
    `sliver_fill` inside the traced fill (so a notch the Sanborn draws stays a notch) and
    reaches no further than `sliver_overlap` into any other rectangle. Order is kept: a
    strip folded into the first rectangle widens the main body; the strip is gone."""
    rs = [tuple(r) for r in rects]

    def cells_of(r):
        return [(i, j) for i in range(round(r[0] / cell), round(r[2] / cell))
                for j in range(round(r[1] / cell), round(r[3] / cell))]

    def touches(a, b):
        eps = cell * 0.5
        gap_u = max(a[0], b[0]) - min(a[2], b[2])
        gap_v = max(a[1], b[1]) - min(a[3], b[3])
        return (gap_u <= eps and gap_v < -eps) or (gap_v <= eps and gap_u < -eps)

    while True:
        best = None
        for i, a in enumerate(rs):
            if min(a[2] - a[0], a[3] - a[1]) >= fit["sliver_m"]:
                continue
            for j, b in enumerate(rs):
                if j == i or not touches(a, b):
                    continue
                u = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
                cs = cells_of(u)
                share = len([c for c in cs if c in fill]) / len(cs)
                if share < fit["sliver_fill"]:
                    continue
                if any(_inside_share(r, u) > fit.get("sliver_overlap", 0.25) for k, r in enumerate(rs)
                       if k not in (i, j)):
                    continue
                key = (share, _area(b))
                if best is None or key > best[0]:
                    best = (key, i, j, u)
        if best is None:
            return [tuple(round(x, 3) for x in r) for r in rs]
        _, i, j, u = best
        rs[min(i, j)] = u
        del rs[max(i, j)]


def _area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def _gap(r, s):
    """Clear distance between two rectangles (0 when they touch or overlap)."""
    du = max(r[0] - s[2], s[0] - r[2], 0.0)
    dv = max(r[1] - s[3], s[1] - r[3], 0.0)
    return math.hypot(du, dv)


def _close_gap(r, s):
    """`r` stretched across the clear strip to meet `s` on each axis it stands apart on."""
    u0, v0, u1, v1 = r
    if r[0] > s[2]:
        u0 = s[2]
    elif r[2] < s[0]:
        u1 = s[0]
    if r[1] > s[3]:
        v0 = s[3]
    elif r[3] < s[1]:
        v1 = s[1]
    return (u0, v0, u1, v1)


def _touches(r, s, eps=0.3):
    """Two plan rectangles that share an edge or overlap (within `eps` metres)."""
    return max(r[0], s[0]) - min(r[2], s[2]) <= eps and max(r[1], s[1]) - min(r[3], s[3]) <= eps


def _inside_share(r, s):
    du = min(r[2], s[2]) - max(r[0], s[0])
    dv = min(r[3], s[3]) - max(r[1], s[1])
    return max(0.0, du) * max(0.0, dv) / _area(r)


# ---------------------------------------------------------------- notation

def storeys_of(notation: str):
    """(full storeys, half storey?, rear storeys or None, bay storeys or None)."""
    m = re.match(r"\s*(\d)(½)?", notation or "")
    full = int(m.group(1)) if m else 2
    half = bool(m and m.group(2))
    rear = re.search(r"rear\s*(\d)", notation or "")
    bay = re.search(r"bay\s*(\d)", notation or "")
    return full, half, (int(rear.group(1)) if rear else None), (int(bay.group(1)) if bay else None)


def service_storeys(reading: str):
    m = re.search(r"(\d)(½)?-storey", reading or "")
    return (int(m.group(1)), bool(m.group(2))) if m else (1, False)


def construction_of(material: str, kind: str, trace_material: str) -> str:
    mat = (material or "").lower()
    if kind == "service":
        return {"brick": "brick", "stone": "stone", "frame": "frame"}.get(trace_material, "brick")
    if "stone front" in mat:
        return "brick_with_stone_front"
    if mat.startswith("stone") and "brick" in mat:
        return "stone_with_brick_rear"
    if mat.startswith("stone"):
        return "stone"
    if "frame" in mat:
        return "frame"
    return "brick"


def family_row(rules, family: str) -> dict:
    for row in rules["families"]:
        if row["match"].lower() in (family or "").lower():
            return {k: v for k, v in row.items() if k != "match"} | {"family_rule": row["match"] or "(default)"}
    raise SystemExit("draft rules: no default family row")


# ---------------------------------------------------------------- records

def seed_of(sid: str) -> int:
    return int(hashlib.sha256(f"prairie_draft:{sid}".encode()).hexdigest()[:8], 16)


def _attr(value, confidence, note, sources=None, geometry=None):
    a = {"value": value, "confidence": confidence}
    if sources:
        a["sources"] = sources
    a["note"] = note
    if geometry:
        a["geometry"] = geometry
    return a


def build_records(rules=None) -> dict:
    rules = rules or json.loads(RULES.read_text())
    datum = json.loads(DATUM.read_text())
    grid = {p["id"]: p for p in json.loads(GRID.read_text())["parcels"]}
    sheets = sorted(rules["blocks"])
    reg = register_rows(sheets)
    hts = rules["heights"]
    fit = rules["fit"]
    out = {}
    for sheet in sheets:
        block = rules["blocks"][sheet]
        trace = json.loads(trace_path(sheet).read_text())
        census = json.loads(census_path(sheet, block).read_text())
        polys = {}
        for f in census["frontages"]:
            for p in f["polygons"]:
                polys[p["id"]] = (f, p)
        for vg in census.get("vacant_ground", []):
            polys[vg["id"]] = (None, vg)
        fronts = {f["frontage_id"]: f for f in census["frontages"]}
        # two traced buildings the census rules one (2108/2110's coach house), and a trace's
        # census assignment the sheet corrects (2140's two rear buildings): block rows
        joins = {j["into"]: j for j in block.get("join", [])}
        joined = {j["from"] for j in joins.values()}
        fixes = {k: v for k, v in block.get("census_fix", {}).items() if not k.startswith("_")}
        traced = {b["id"]: (pc, b) for pc in trace["parcels"] for b in pc["buildings"]}
        vacant = {v["id"]: v for v in census.get("vacant_ground", [])}
        for parcel in plate_parcels(block, fronts, polys, vacant) + trace["parcels"]:
            side = parcel["side"]
            if side not in block["sides"]:
                continue
            frame = lot_frame(grid[parcel["parcel_id"]])
            lot = [to_uv(frame, p) for pid in parcel.get("lot_parcels", [parcel["parcel_id"]])
                   for p in grid[pid]["polygon_local_m"]]
            lot_v = (min(p[1] for p in lot), max(p[1] for p in lot))
            street_u = max(p[0] for p in lot)
            house_sid = None
            house_by_fid = {}
            bs = []
            for b in parcel["buildings"]:
                if b["id"] in joined:
                    continue
                if b["id"] in fixes:
                    b = {**b, "census_ids": fixes[b["id"]]["census_ids"], "census_fix": fixes[b["id"]]}
                if b["id"] in joins:
                    b = join_building(b, parcel, joins[b["id"]], traced, grid, frame)
                elif b["kind"] != "front" and block.get("service_outline") and b.get("polygon_local_m"):
                    # sheet 35 crosses its stables corner to corner, and the trace splits each
                    # along the cross into four triangles: the building's outline is its fill
                    b = {**b, "parts": [{"id": "outline", "role": "main", "material": b["parts"][0]["material"],
                                         "area_m2": b["area_m2"], "rings": [b["polygon_local_m"]]}]}
                bs.append(b)
            for b in split_townhouses(bs, polys, rules):
                if any(c in rules["skip"] for c in b["census_ids"]):
                    continue
                f, cp = polys[b["census_ids"][0]]
                fid = f["frontage_id"] if f else None
                frow = rules["frontages"].get(fid, {}) if fid else {}
                if frow.get("skip"):
                    continue
                if frow.get("merged_into"):
                    fid = frow["merged_into"]
                    frow = rules["frontages"][fid]
                kind = "house" if b["kind"] == "front" else "service"
                row = reg.get(fid, {}) if fid else {}
                # a lot several census frontages share (sheet 35's 2000, 2010 and 2018) keeps each
                # house's own number and gives each stable its own frontage's house
                shared = bool(parcel.get("frontage_shares"))
                rec = draft_record(rules, block, sheet, parcel, b, kind, f, cp, fid, frow, row, frame,
                                   b["join"]["lot_v"] if b.get("join") else lot_v,
                                   street_u, datum, hts, fit, house_by_fid.get(fid) if shared else house_sid,
                                   polys, shared, grid[parcel["parcel_id"]].get("street"))
                if kind == "house" and not (house_sid and b.get("split_of")):
                    house_sid = rec["id"]
                if kind == "house":
                    house_by_fid[fid] = rec["id"]
                out[rec["id"]] = rec
    for site in rules.get("sites", []):
        rec = site_record(rules, site, datum, json.loads(GRID.read_text()))
        out[rec["id"]] = rec
    return out


def _line_meet(p, d, q, e):
    """Where the line through p along d meets the line through q along e (2-D)."""
    den = d[0] * e[1] - d[1] * e[0]
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + t * d[0], p[1] + t * d[1])


def site_record(rules, site, datum, grid) -> dict:
    """A drafted building that stands on no traced sheet and no 1904 parcel (T-2982:
    Second Presbyterian, on Michigan Avenue west of every committed Sanborn sheet). Its
    plan comes from a measured drawing, read into the site row as rectangles in metres
    (u toward the street from the front face, v along the front from the building's
    southernmost face); its corner is set where two street lines the project already
    measures meet, each moved in by the row's setback."""
    faces = {f["id"]: f["street_line_local_m"] for f in grid["faces"]}
    pl = site["place"]
    a, b = faces[pl["along_face"]]
    n_ = math.hypot(b[0] - a[0], b[1] - a[1])
    north = [(a[0] - b[0]) / n_, (a[1] - b[1]) / n_] if b[1] < a[1] else [(b[0] - a[0]) / n_, (b[1] - a[1]) / n_]
    u = [north[1], -north[0]]                      # toward the street: east, square to the avenue
    if pl["front"] == "west":
        u = [-u[0], -u[1]]
    v = [-u[1], u[0]]
    # T-3038: the row measures v NORTHWARD from the building's southernmost face, but the
    # record's frame is a rotation, so v = u turned left: north for a front on the east, south
    # for a front on the west. A west-fronted site's v figures are mirrored into that frame
    # (First Presbyterian, T-3009, stood its plan southward from 21st Street's north line,
    # across the roadway and onto the next block, until this).
    flip = 1.0 if v[0] * north[0] + v[1] * north[1] > 0 else -1.0
    vm = [v[0] * flip, v[1] * flip]                # the row's own v: northward
    c = pl["avenue_centre_local_m"]
    k = pl["half_row_m"] + pl["setback_front_m"]
    front_pt = (c[0] - u[0] * k, c[1] - u[1] * k)
    s0, s1 = faces[pl["cross_face"]]
    m = math.hypot(s1[0] - s0[0], s1[1] - s0[1])
    sd = ((s1[0] - s0[0]) / m, (s1[1] - s0[1]) / m)
    sn = (-sd[1], sd[0]) if -sd[1] * vm[0] + sd[0] * vm[1] > 0 else (sd[1], -sd[0])   # into the block
    side_pt = (s0[0] + sn[0] * pl["setback_side_m"], s0[1] + sn[1] * pl["setback_side_m"])
    corner = _line_meet(front_pt, north, side_pt, sd)

    def mirror(r):
        return [r[0], r[1], r[2], r[3]] if flip > 0 else [r[0], -r[3], r[2], -r[1]]
    parts_m = [dict(q, rect_m=mirror(q["rect_m"])) for q in site["parts"]]
    mu0, mv0, mu1, mv1 = parts_m[0]["rect_m"]
    parts = [{"id": f"r{n + 1}", "role": q["role"], "storeys": q["storeys"], "roof": q["roof"],
              **({"pitch_deg": q["pitch_deg"]} if "pitch_deg" in q else {}),
              "rect": [round(q["rect_m"][0] - mu0, 3) + 0.0, round(q["rect_m"][1] - mv0, 3) + 0.0,
                       round(q["rect_m"][2] - mu0, 3) + 0.0, round(q["rect_m"][3] - mv0, 3) + 0.0],
              "from": q["from"]} for n, q in enumerate(parts_m)]
    lo_v = min(q["rect_m"][1] for q in parts_m) - pl["setback_side_m"]
    hi_v = max(q["rect_m"][3] for q in parts_m) + pl["setback_side_m"]
    plan = {"parts": parts, "lot_v": [round(lo_v - mv0, 3) + 0.0, round(hi_v - mv0, 3) + 0.0],
            "street_u": round(pl["setback_front_m"] - mu0, 3)}
    oe = corner[0] + u[0] * mu0 + v[0] * mv0
    on = corner[1] + u[1] * mu0 + v[1] * mv0
    rot = round(((math.degrees(math.atan2(u[0], u[1])) % 360 - 90 + 180) % 360) - 180, 3)
    sid = site["id"]
    seed = seed_of(sid)
    el = site["elevation"]
    feats = [{**ft, "at": [round(ft["at_m"][0] - mu0, 3), round(ft["at_m"][1] * flip - mv0, 3) + 0.0]}
             for ft in el.get("features", [])]
    for ft in feats:
        ft.pop("at_m", None)
    elev = {"kind": "house", "seed": seed, "principal_floor_m": el["principal_floor_m"],
            "storey_heights_m": el["storey_heights_m"], "roof_pitch_deg": el["roof_pitch_deg"],
            "mansard_lower_m": 3.0, "front_bays": el["front_bays"], "entrance": el["entrance"],
            "side_spacing_m": el["side_spacing_m"], "chimneys": 0, "brackets": False, "attic_dormers": False,
            "stone": el.get("stone", "stone"), "features": feats,
            "draft_label": {"pass": site["pass"], "refined_by": site["refined_by"]}}
    if u[1] * 0 + v[1] < 0:
        elev["v_toward"] = "south"
    src = site["sources"]
    notes = site["notes"]
    # T-3011: a row no measured drawing gives (Indiana's 18th-20th face, re-stood from its
    # neighbours' drafted bodies) says its own tiers; every other site keeps the defaults
    tier = site.get("confidence", {})
    return {
        "id": sid,
        "name": site["name"],
        "aka": sorted(site.get("aka", [])),
        "archetype": ARCHETYPE,
        # a site the sheet alone names (T-3009's First Presbyterian) is inferred, not attested
        "function": _attr(site["function"], site.get("function_confidence", "attested"), notes["function"], src),
        "review_required": False,
        "research_note": (
            f"A DISTRICT DRAFT ({site['pass']}, the owner's district pass of 2026-10-08): a serviceable first model, "
            f"complete from the street, the walks, the alley and the air, that {', '.join(site['refined_by'])} refines "
            f"in place under this same id. Written by tools/draft_prairie_1904.py from the rules' site row "
            f"(data/components/prairie_1904/draft_prairie_1904.json; liberty {site['liberty']}). {notes['research']}"),
        "phases": [{
            "id": PHASE,
            "documented_range": {"from": "1904-07-01", "to": "1911-12-31", "confidence": "inferred", "sources": src,
                                 "note": notes["range"],
                                 # T-3037: what the range's end is, where the site's sources say
                                 **({"to_is": site["to_is"]} if site.get("to_is") else {})},
            "position": {
                "utm_e": round(datum["origin_utm_e"] + oe, 3), "utm_n": round(datum["origin_utm_n"] + on, 3),
                "rotation_deg": rot,
                "symbolic_location": site["where"],
                "confidence": "reconstructed",
                "note": (f"The rear corner of the main body (u {mu0:.3f}, v {mv0:.3f} m from the building's front and "
                         f"southernmost faces), set from the corner at local ({corner[0]:.2f}, {corner[1]:.2f}): "
                         f"{notes['position']} Rotation {rot} degrees squares the plan to the avenue."),
                "derivation": {"method": "not_derivable",
                               "reason": "The four derivation methods re-derive from the 1835 files; this position is "
                                         "re-derived from the 1904 street grid's faces and the rules' site row by "
                                         "tools/draft_prairie_1904.py --check instead."}},
            "footprint": {
                # the row's outline of every part when it gives one (the walker's walls and the
                # context's give-way read this polygon), else the main body
                "polygon": ([[round(q[0] - mu0, 3) + 0.0, round(q[1] * flip - mv0, 3) + 0.0] for q in site["outline_m"]]
                            if site.get("outline_m") else
                            [[0.0, 0.0], [round(mu1 - mu0, 3), 0.0], [round(mu1 - mu0, 3), round(mv1 - mv0, 3)],
                             [0.0, round(mv1 - mv0, 3)]]),
                "confidence": tier.get("footprint", "inferred"), "sources": src,
                "note": notes["footprint"]},
            "form": {
                "stories": _attr(el["stories"], "reconstructed", notes["stories"]),
                "construction": _attr(site["construction"], tier.get("construction", "attested"), notes["construction"], src),
                "draft_plan": _attr(plan, tier.get("plan", "inferred"), notes["plan"], src),
                "draft_elevation": _attr(elev, "reconstructed",
                                         f"RECONSTRUCTED by the site row: {notes['elevation']} The seed {seed} only "
                                         f"tints the fabric inside +-6 %. Liberty {site['liberty']}."),
                "draft": _attr({"pass": site["pass"], "liberty": site["liberty"], "register_row": site["register_row"],
                                "census_ids": [], "trace_building": None, "seed": seed,
                                "replaceable_by": site["refined_by"],
                                "card": f"District draft — refined by {', '.join(site['refined_by'])}."},
                               "reconstructed",
                               "The draft's own provenance: the pass that wrote it, the rows it read and the "
                               "tickets that replace it attribute by attribute under this id.",
                               geometry="record_only"),
            },
        }],
    }


def join_building(b, parcel, j, traced, grid, frame) -> dict:
    """One building out of two traced on neighbouring lots (sheet 35's 2108/2110 coach house,
    drawn across both lots and divided on the line): the two outlines are filled as one part,
    the drawn line between them closed, and the lot line kept as the party wall's plan v."""
    opc, other = traced[j["from"]]
    lots = {pid: [to_uv(frame, q) for q in grid[pid]["polygon_local_m"]]
            for pid in (parcel["parcel_id"], opc["parcel_id"])}
    mine, theirs = lots[parcel["parcel_id"]], lots[opc["parcel_id"]]
    mv = (min(q[1] for q in mine), max(q[1] for q in mine))
    tv = sum(q[1] for q in theirs) / len(theirs)
    every = [q[1] for ring in lots.values() for q in ring]
    return {**b, "census_ids": b["census_ids"] + other["census_ids"],
            "parts": [{"id": f"{b['id']}+{other['id']}", "role": "main", "material": b["parts"][0]["material"],
                       "area_m2": round(b["area_m2"] + other["area_m2"], 2),
                       "rings": [b["polygon_local_m"], other["polygon_local_m"]]}],
            "join": {**j, "with": other["id"], "lot_parcels": [parcel["parcel_id"], opc["parcel_id"]],
                     "lot_v": (min(every), max(every)), "party_v": mv[0] if tv < mv[0] else mv[1]}}


def plate_parcels(block, fronts, polys, vacant=None) -> list:
    """Houses the 1911 sheet does not draw but the census stands for 1904 on an earlier
    plate (sheet 20's 1620, carried from Robinson 1886): the block's `plates` rows give the
    outline in that plate's pixels, and its GCP file's similarity carries them to local
    metres, so the house is drafted from the plate the way a traced house is from the sheet.
    A plate row on ground the sheet leaves unnumbered names its census `vacant_id` instead of
    a frontage (1635, ruled standing by T-2443), and has no frontage row of its own."""
    out = []
    for pl in block.get("plates", []):
        co = json.loads((ROOT / pl["gcps"]).read_text())["fit"]["coefficients"]
        ring = [[round(co["a"] * x + co["b"] * y + co["c"], 2), round(co["d"] * x + co["e"] * y + co["f"], 2)]
                for x, y in pl["polygon_px"]]
        f = fronts[pl["frontage_id"]] if pl.get("frontage_id") else {**(vacant or {})[pl["vacant_id"]], "frontage_id": None}
        polys[pl["id"]] = (f, {"id": pl["id"], "kind": "front", "reading_1911": "", "reading_plate": pl["reading"]})
        area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1]))) / 2
        out.append({"parcel_id": pl["parcel_id"], "side": f["side"], "lot_parcels": pl["lot_parcels"],
                    "buildings": [{"id": pl["id"], "kind": "front", "census_ids": [pl["id"]], "plate": pl,
                                   "parts": [{"id": "p1", "role": "main", "material": pl["material"],
                                              "area_m2": round(area, 2), "polygon_local_m": ring}]}]})
    return out


def split_townhouses(buildings, polys, rules):
    """One traced building whose census ids belong to two frontages, each of whose rows
    names its own traced part (`house_part`), is two houses (sheet 20's 1700 and 1706,
    one U-shaped block on one lot): each keeps its own census id and its own part."""
    for b in buildings:
        rows = [(cid, rules["frontages"].get(polys[cid][0]["frontage_id"], {}))
                for cid in b["census_ids"] if polys[cid][0]]
        split = [(cid, r) for cid, r in rows if r.get("house_part")]
        if len(split) < 2:
            yield b
            continue
        for cid, r in split:
            part = next(p for p in b["parts"] if p["id"] == r["house_part"])
            yield {**b, "id": f"{b['id']}/{part['id']}", "census_ids": [cid], "split_of": b["id"],
                   "parts": [{**part, "role": "main"}]}


def draft_record(rules, block, sheet, parcel, b, kind, f, cp, fid, frow, row, frame, lot_v, street_u,
                 datum, hts, fit, house_sid, polys=None, shared=False, grid_street=None):
    plate = b.get("plate")
    join = b.get("join")
    if plate:
        # a plate house carries its own frontage overlay: 1609 and 1611 are one census frontage's lost pair
        frow = {**frow, **plate.get("frontage", {})}
    # a row may correct the register's reading of the sheet (it reads 1719 where the sheet prints 1721)
    row = {**row, **frow.get("register", {})}
    # a service-kind building that is no one's stable names its own use (sheet 20's 16th Street station)
    use = frow.get("use") if kind == "service" else None
    front_use = use
    # a front that is no house names its own use too (1605-1613 Indiana's ice-cream works,
    # rising on the target date: T-3130), with the dated sources that rule it beside the sheet
    house_use = frow.get("use") if kind == "house" else None
    # one of several service buildings on a lot names its own id suffix and, if it is no one's
    # stable, its use (2140's three-storey alley building beside its stable)
    svc = frow.get("services", {}).get(cp.get("id"), {}) if kind == "service" else {}
    use = svc.get("use", use)
    src = plate["source"] if plate else block.get("source", SOURCE)
    cen = block.get("census_ticket", "T-1841")
    fit_note = plate["fit_note"] if plate else block.get(
        "fit_note", "the georeference's independent check is 1.47 m RMS")
    # ---- the plan: rectangles inside each traced part, in the lot frame
    pieces = []
    order = {"main": 0, "stone_front": 1, "range": 2, "porch": 3}
    # a record already standing on part of the traced fabric (1729's K13 conservatory wing) is kept out of the fill
    # T-3151: or a band of the lot by its depth from the street line, {"from_street_m": [a, b]}, for
    # fabric the sheet draws joined to a house but rules out of 1904 (1801's and 1807's 1911 shops)
    keep = [footprint_uv(k, frame, datum) if isinstance(k, str) else
            [(street_u - k["from_street_m"][1], -500.0), (street_u - k["from_street_m"][0], -500.0),
             (street_u - k["from_street_m"][0], 500.0), (street_u - k["from_street_m"][1], 500.0)]
            for k in frow.get("keep_out", [])]
    tparts = b["parts"]
    if kind == "house" and frow.get("main_part"):
        # the house's body is the part the row names, not the trace's largest (217 East
        # Twentieth Street's 3½-storey front, smaller in plan than its 3-storey rear range)
        tparts = [{**q, "role": "main" if q["id"] == frow["main_part"] else
                   ("range" if q["role"] == "main" else q["role"])} for q in tparts]
    for part in sorted(tparts, key=lambda p: (order.get(p["role"], 9), -p["area_m2"], p["id"])):
        if part.get("rings"):
            poly = [[to_uv(frame, q) for q in ring] for ring in part["rings"]]
        else:
            poly = [to_uv(frame, q) for q in part["polygon_local_m"]]
        rs, cov = rects_for(poly, fit, frow.get("front_body_from_u_m")
                            if part["role"] == "main" and kind == "house" else None, keep,
                            close=(join or {}).get("close_cells", 0) or (
                                frow.get("close_cells", 0) if kind == "house" else
                                block.get("service_outline", {}).get("close_cells", 0)))
        for k, r in enumerate(rs):
            pieces.append({"trace_part": part["id"], "trace_role": part["role"], "material": part["material"],
                           "rect": r, "k": k, "coverage": round(cov, 3)})
    if plate and plate.get("fills_lot"):
        # a plate house drawn filling its lot wall to wall (1635) stands between the 1911 strip's
        # own lines, not wherever the plate's 4.5 m fit carries its outline across them
        for p in pieces:
            p["rect"] = [p["rect"][0], lot_v[0], p["rect"][2], lot_v[1]]
    if not pieces or pieces[0]["trace_role"] != "main":
        # a building whose largest traced part is not a 'main' (a crossed stable) still has a body
        pieces.sort(key=lambda p: -_area(p["rect"]))
    kept = []
    for p in pieces:
        if any(_inside_share(p["rect"], q["rect"]) >= fit["swallowed"] for q in kept):
            continue
        if p["trace_role"] == "porch" and min(p["rect"][2] - p["rect"][0], p["rect"][3] - p["rect"][1]) < 1.2:
            continue
        kept.append(p)
    main = kept[0]
    mu0, mv0, mu1, mv1 = main["rect"]
    narrow = fit.get("min_body_m")
    if kind == "house" and narrow and mv1 - mv0 < narrow:
        # a street body narrower than any house of the avenue (the fit kept a 4 m strip of a
        # skewed outline, and three storeys of it stood like a tower) is widened about its
        # middle to the narrowest row house the drafts build, inside its own lot (T-2690)
        mid = min(max((mv0 + mv1) / 2, lot_v[0] + narrow / 2), lot_v[1] - narrow / 2)
        mv0, mv1 = round(mid - narrow / 2, 3), round(mid + narrow / 2, 3)
        main = kept[0] = {**main, "rect": (mu0, mv0, mu1, mv1), "widened": True}
        kept = [main] + [q for q in kept[1:] if _inside_share(q["rect"], main["rect"]) < fit["swallowed"]]

    # ---- storeys and family
    notation = row.get("raw_story_notation", "") if kind == "house" else ""
    if kind == "house":
        full, half, rear_n, bay_n = storeys_of(notation)
        if plate:
            full, half = plate["stories"], False
    else:
        full, half = service_storeys(cp.get("reading_1911", ""))
        rear_n = bay_n = None
        if svc.get("storeys_1904"):
            # a dated source nearer the scene than the 1911 sheet counts the storeys itself
            # (1811's '2 story stable' of April 1904, a 1½-storey garage by 1911: T-3099)
            full, half = svc["storeys_1904"]["value"], False
    fam = family_row(rules, row.get("family", "")) if kind == "house" else {"roof": "gable", "pitch_deg": 40,
                                                                             "chimneys": 0, "family_rule": "service"}
    if kind == "house":
        fam = fam | {k: v for k, v in frow.items() if k in ("roof", "pitch_deg", "chimneys", "stone", "brackets")}
    roof = fam["roof"]
    if kind == "house" and half and roof in ("hip", "hip_steep"):
        frow = {**frow, "attic_dormers": True}

    parts = []
    for n, p in enumerate(kept):
        r = p["rect"]
        depth = r[2] - r[0]
        if n == 0:
            role, st, rf = "main", full, roof
        elif p["trace_role"] == "porch":
            role, st, rf = "porch", 1, "flat"
        elif p["trace_role"] == "stone_front":
            role, st, rf = "stone_front", full, "flat"
        elif kind == "house" and fit.get("detached_front_m") is not None and r[0] >= mu1 + fit["detached_front_m"]:
            # a piece standing clear in front of the street wall is the entrance porch or
            # portico the sheet draws there (1729's Prairie portico), never a storeyed bay
            # standing free on the lawn like a tower (T-2690)
            role, st, rf = "porch", 1, "flat"
        elif r[0] >= mu1 - 4.0 and depth <= 4.0 and kind == "house":
            role, st, rf = "bay", (full if p["trace_role"] == "main" or p["material"] == "stone" else 1), "flat"
        elif p["trace_role"] == "main":
            big = min(depth, r[3] - r[1]) >= 4.5 and _area(r) >= 30
            role, st = "wing", (frow.get("wing_storeys", full) if kind == "house" else full)
            rf = ("mansard" if roof == "mansard" else "hip") if big and kind == "house" else (
                "gable" if kind == "service" and big else "flat")
        else:
            role = "range"
            st = rear_n if rear_n else max(1, full - 1)
            rf = "flat"
        if kind == "service" and role in ("main", "wing", "range"):
            st = min(st, full) if role != "main" else full
        if (kind == "house" and fit.get("detached_front_m") is not None and mu1 < r[0] and r[1] < mv1 and r[3] > mv0
                and (role == "stone_front" or (role in ("bay", "porch") and r[0] < mu1 + fit["detached_front_m"]))):
            # a bay or porch the fit left a strip of lawn short of the street wall stands
            # against it, and a stone front IS that wall's face: the gap is the rectangles',
            # not the sheet's, and a veneer standing clear of its house is a slab (T-2690)
            r = (mu1, r[1], r[2], r[3])
            depth = r[2] - r[0]
        if role in ("wing", "bay", "range") and fit.get("sliver_m") and min(depth, r[3] - r[1]) < fit["sliver_m"]:
            # a strip no neighbour could take (merge_slivers) stands one storey under a flat
            # roof, a side entry or lean-to against the wall, never a full-height slab (T-2690)
            st, rf = 1, "flat"
        if (role in ("wing", "bay", "range") and st > 1 and fit.get("stray_m2") and _area(r) < fit["stray_m2"]
                and not any(_touches(r, q["rect"]) for q in kept if q is not p)):
            # a small piece touching nothing of its building (1729's 4 x 2.5 m range standing
            # 2 m off the side wall) is an outbuilding of one storey, not a two-storey shaft
            st, rf = 1, "flat"
        if n and fit.get("snap_gap_m") and role in ("wing", "bay", "range", "porch"):
            others = [q["rect"] for q in kept if q is not p]
            near = min(others, key=lambda s: _gap(r, s)) if others else None
            if near is not None and not _touches(r, near) and _gap(r, near) <= fit["snap_gap_m"]:
                # a piece left a few metres clear of everything else of its building (1729's
                # 5 m stone range 2.5 m off the south wall) reads as a tower on the lawn: the
                # sheet draws one building, so it stands against its nearest wall (T-2738)
                r = _close_gap(r, near)
                depth = r[2] - r[0]
        parts.append({"id": f"r{n + 1}", "role": role, "storeys": st, "roof": rf,
                      "rect": [round(r[0] - mu0, 3) + 0.0, round(r[1] - mv0, 3) + 0.0,
                               round(r[2] - mu0, 3) + 0.0, round(r[3] - mv0, 3) + 0.0],
                      "from": f"{b['id']} {p['trace_part']} ({p['trace_role']}, {p['material']}), "
                              f"rectangle {p['k'] + 1} of that part; the part's rectangles cover "
                              f"{p['coverage']:.0%} of its fill"})
    # `+ 0.0`: a body widened against its lot line would write -0.0, which JSON readers
    # in the browser take as 0 and the boot packer then refuses as a different record
    lot_v_local = [round(lot_v[0] - mv0, 3) + 0.0, round(lot_v[1] - mv0, 3) + 0.0]
    street_local = round(street_u - mu0, 3)

    # ---- identity
    num = (row.get("address", "") or "").split(" ")[0] if kind == "house" or fid else ""
    addr = (num if b.get("split_of") or plate or shared else "") or parcel["parcel_id"].split("_", 1)[1]
    slug = frow.get("slug") or "house"
    street = STREETS[(grid_street or "prairie")]
    base_id = f"{slug}_{addr}_{street[2]}" if f else f"shed_{addr}_{street[2]}"
    if kind == "service":
        # a lot whose house this pass does not draft names it (`house_id`): 1638's K16 front, 1620's plate house
        owner_sid = house_sid or frow.get("house_id")
        sid = f"{owner_sid}_{svc.get('suffix', 'coach_house')}" if owner_sid and f else base_id
    else:
        sid = base_id
    seed = seed_of(sid)
    front_tickets = row.get("front_tickets", "") if kind == "house" or front_use else ""
    # a row may name its own rear ticket (T-2982: each Calumet barn is its own house's ticket's)
    rear_ticket = frow.get("rear_ticket") or block["rear_ticket"][parcel["side"]]
    # a side drafted by a later ticket names its own pass and liberty (T-2330 drafts block 28's east)
    side_rules = block.get("by_side", {}).get(parcel["side"], {})
    # and a frontage a later ticket drafts on a block already drafted names its own (T-3068's
    # Indiana lots, ruled after T-3019 stood the rest of the block face)
    pass_ = frow.get("pass") or side_rules.get("pass", block.get("pass", rules["ticket"]))
    liberty = frow.get("liberty") or side_rules.get("liberty", block["liberty"])
    refined_by = [t.strip() for t in (front_tickets.split(",") if front_tickets else [rear_ticket]) if t.strip()]

    # ---- elevation
    width = mv1 - mv0
    bays = frow.get("front_bays") or max(2, min(6, round(width / hts["front_bay_m"])))
    feats = []
    for ft in (frow.get("features", []) if kind == "house" else []):
        ft = dict(ft)
        if "at_m" in ft:
            # a feature the row places itself (Second Presbyterian's tower, read off the HABS plan)
            at = [float(x) for x in ft.pop("at_m")]
            ft.pop("corner", None)
        elif ft.pop("on", None) == "bay":
            # a turret standing on the sheet's own round front bay (2130's), centred on it
            bay = next(p["rect"] for p in parts if p["role"] == "bay")
            at = [round((bay[0] + bay[2]) / 2, 3), round((bay[1] + bay[3]) / 2, 3)]
        else:
            corner = ft.pop("corner")
            r = ft.get("radius_m", 1.9)
            at = [round(mu1 - mu0 - r * 0.35, 3), round((r * 0.35) if corner == "front_v0" else (width - r * 0.35), 3)]
        feats.append({**ft, "at": at})
    if join and join.get("party_wall"):
        feats.append({"kind": "party_wall", "v": round(join["party_v"] - mv0, 3)})
    elev = {
        "kind": kind,
        "seed": seed,
        "principal_floor_m": hts["principal_floor_m"] if kind == "house" else 0.0,
        "storey_heights_m": hts["storey_heights_m"] if kind == "house" else hts["service_storey_heights_m"],
        "roof_pitch_deg": fam["pitch_deg"],
        "mansard_lower_m": hts["mansard_lower_m"],
        "front_bays": bays,
        "entrance": frow.get("entrance", "north"),
        "side_spacing_m": hts["side_spacing_m"] if kind == "house" else hts["service_side_spacing_m"],
        "chimneys": fam.get("chimneys", 0),
        "brackets": bool(fam.get("brackets", False)),
        "attic_dormers": bool(frow.get("attic_dormers", False)) and kind == "house",
        "stone": fam.get("stone", "stone"),
        "features": feats,
        "draft_label": {"pass": pass_, "refined_by": refined_by},
    }
    if kind == "house" and frow.get("works"):
        # a house still building on the target date (2126's Robbins house): its shell, not its roof
        elev["works"] = {k: v for k, v in frow["works"].items() if k != "note"}
    if kind == "service" and frow.get("station"):
        # a railway station's platform, canopy, door and nameboards (1605, T-2399)
        elev["station"] = {k: v for k, v in frow["station"].items() if k != "note"}
    if frame[2][1] < 0:
        # the plan's v axis runs along the front; on the east side of the avenue it points
        # south, so the archetype is told which way high v faces before it reads `entrance`
        elev["v_toward"] = "south"
    plan = {"parts": parts, "lot_v": lot_v_local, "street_u": street_local}

    # ---- placement
    p0, u, v = frame
    oe = p0[0] + u[0] * mu0 + v[0] * mv0
    on = p0[1] + u[1] * mu0 + v[1] * mv0
    bearing_u = math.degrees(math.atan2(u[0], u[1])) % 360
    rot = round(((bearing_u - 90 + 180) % 360) - 180, 3)
    utm_e = round(datum["origin_utm_e"] + oe, 3)
    utm_n = round(datum["origin_utm_n"] + on, 3)
    construction = construction_of(row.get("map_material", ""), kind, main["material"])
    census_ids = list(b["census_ids"])
    fam_name = row.get("family", "") if kind == "house" else ""
    where = f"{addr.replace('_', '-')} {street[0]}"
    if kind == "house":
        label = (row.get("address") or where).replace(f" {street[0]}", "")
        # T-2439: a frontage whose household is ruled names it on the card; the draft stays the draft
        who = f"{frow['household']['name']}, " if frow.get("household") else ""
        name = f"{label} {street[1]} — {who}{fam_name} (district draft; refined by {', '.join(refined_by)})"
        reading = cp.get('reading_1911', '')
        ruling = (f or {}).get('decision_1904', 'present_as_mapped')
        if house_use:
            name = f"{label} {street[1]} — {house_use['name']} (district draft; refined by {', '.join(refined_by)})"
        function = _attr(house_use["function"], "inferred",
                         f"The 1911 sheet reads '{reading}'. {house_use['note']} "
                         f"Carried to 1904 on the {cen} census ruling ({ruling}).",
                         [src] + [s_ for s_ in house_use.get("sources", []) if s_ != src]) if house_use else _attr(
                         "residence", "inferred", plate["function_note"], [src]) if plate else _attr(
                         "residence", "inferred",
                         f"The 1911 sheet marks the building 'D' (dwelling): '{reading}'. "
                         f"Carried to 1904 on the {cen} census ruling ({ruling})." if "(D)" in reading else
                         f"The 1911 sheet labels the building with a 1911 use, '{reading}', which the draft does not "
                         f"carry back to 1904 (the T-1837 register warns not to assume the 1904 use from it). "
                         f"The register's family row, '{fam_name}', names it a house, so the 1904 function is "
                         f"inferred residence on that row and the {cen} census ruling ({ruling}).",
                         [src])
    elif use:
        name = f"{where} — {use['name']} (district draft; refined by {', '.join(refined_by)})"
        # T-3013: a use a directory names (2129's livery in the 1904 Blue Book) cites it beside the sheet
        function = _attr(use["function"], "inferred",
                         f"The 1911 sheet reads '{cp.get('reading_1911', '')}'. " + (cp.get("note_1904") or "")
                         + f" Carried to 1904 on the {cen} census ruling ({(f or {}).get('decision_1904')}).",
                         [src] + use.get("sources", []))
    elif join:
        # one building on two lots: both halves' readings, and the ruling that makes them one
        _, ocp = polys[b["census_ids"][-1]]
        name = f"{where} — {join['name']} (district draft; refined by {rear_ticket})"
        function = _attr("barn_or_carriage_shed", "inferred",
                         f"The 1911 sheet reads '{cp.get('reading_1911', '')}' and '{ocp.get('reading_1911', '')}'. "
                         f"{cp.get('note_1904') or ''} {join['note']}".replace("  ", " "), [src])
    else:
        owner = f"the house at {frow.get('house_address', addr)}" if f else "neither neighbour (the sheet does not show whose)"
        name = (f"{where} — the alley building of {owner} (district draft; refined by {rear_ticket})"
                if f else f"The shed on the strip between 1834 and 1900 Prairie Avenue (district draft; refined by {rear_ticket})")
        function = _attr("barn_or_carriage_shed", "inferred",
                         f"The 1911 sheet reads '{cp.get('reading_1911', '')}'. "
                         + (cp.get("note_1904") or "Backcast to 1904 as a yard outbuilding on the census ruling."),
                         [src])
    if b.get("census_fix"):
        # the trace gave this building its neighbour's census id; the sheet, read again, corrects it
        function["note"] += f" {b['census_fix']['note']}"
    if kind == "house" and frow.get("works"):
        function["note"] += f" {frow['works']['note']}"
    if kind == "house" and frow.get("household"):
        function["note"] += f" {frow['household']['note']}"
    drawn = "; ".join(p["from"] for p in parts)
    rec = {
        "id": sid,
        "name": name,
        "aka": sorted({where} | set(frow.get("aka", []) if kind == "house" else (join or {}).get("aka", []))),
        "archetype": ARCHETYPE,
        "function": function,
        # T-3037: a build year a source prints (the district's markers), from the frontage row.
        **({"built": frow["built"]} if kind == "house" and frow.get("built") else {}),
        "review_required": False,
        "research_note": (
            f"A DISTRICT DRAFT ({pass_}, the owner's district pass of 2026-10-08): a serviceable first model, "
            f"complete from the street, the walks, the alley and the air, that {', '.join(refined_by)} refine{'s' if len(refined_by) == 1 else ''} "
            f"in place under this same id. Written by tools/draft_prairie_1904.py from the "
            f"{plate['label'] if plate else f'sheet {sheet} trace'} "
            f"({b['id']}{' and ' + join['with'] + ', filled as one building' if join else ''}), the {cen} census ({', '.join(census_ids)}) and the T-1837 register row {fid or 'none'}"
            f"{' (' + fam_name + ')' if fam_name else ''}; every height, roof, opening and feature is the draft rules' "
            f"reconstruction (data/components/prairie_1904/draft_prairie_1904.json; liberty {liberty})."),
        "phases": [{
            "id": PHASE,
            "documented_range": plate["documented_range"] if plate else {
                "from": "1904-07-01", "to": "1911-12-31", "confidence": "inferred", "sources": [src],
                "note": ("The draft claims the 1904 target and no more: the 1911 sheet draws the building and the "
                         f"{cen} census rules it present in 1904 "
                         f"({(f or {}).get('decision_1904') or cp.get('decision_1904', 'present_as_mapped')}). "
                         "Its building and loss dates are the per-building ticket's to read."),
                # T-3037: the 1911 sheet shows it standing then; 1 July 1904 is the scene's bound.
                "to_is": "seen"},
            "position": {
                "utm_e": utm_e, "utm_n": utm_n, "rotation_deg": rot,
                "symbolic_location": f"{where}, parcel {parcel['parcel_id']} (data/street_grid/1904.json), "
                                     f"{parcel['side']} side of {street[1]}, {block['where']}.",
                "confidence": "inferred", "sources": [src],
                "note": (f"The rear corner of the main body's rectangle (lot frame u {mu0:.3f}, v {mv0:.3f} m from "
                         f"the middle of the rear lot line), through the T-1250 fit of the "
                         f"{'plate' if plate else 'sheet'}: {fit_note}. Rotation {rot} degrees turns the plan's u axis onto the "
                         f"lot's own rear-to-street line."),
                "derivation": {"method": "not_derivable",
                               "reason": "The four derivation methods re-derive from the 1835 files; this position is "
                                         "re-derived from the traced sheet and the 1904 parcel by tools/draft_prairie_1904.py "
                                         "--check instead."}},
            "footprint": {
                "polygon": [[0.0, 0.0], [round(mu1 - mu0, 3), 0.0], [round(mu1 - mu0, 3), round(mv1 - mv0, 3)],
                            [0.0, round(mv1 - mv0, 3)]],
                "confidence": "inferred", "sources": [src],
                "note": ("The main body: the largest rectangle that fits inside the traced main part (u toward the "
                         "street, v along the front)"
                         + (f", widened to {fit['min_body_m']} m along the front because the fitted strip was "
                            f"narrower than any house of the avenue (T-2690)" if main.get("widened") else "")
                         + ". The building's other rectangles are in draft_plan.")},
            "form": {
                "stories": _attr(plate["stories"], "reconstructed", plate["stories_note"]) if plate else _attr(
                                 full, svc["storeys_1904"]["confidence"], svc["storeys_1904"]["note"],
                                 svc["storeys_1904"]["sources"]) if svc.get("storeys_1904") else _attr(
                                 full, "attested",
                                 (f"'{notation}' printed on the 1911 sheet: {full} full storeys"
                                  f"{' and a half storey in the roof' if half else ''}." if kind == "house" else
                                  f"The census reading '{cp.get('reading_1911', '')}': {full} storeys"
                                  f"{' and a half' if half else ''}."), [src]),
                "construction": _attr(plate["construction"], "inferred", plate["construction_note"], [src])
                if plate else _attr(construction, "attested" if kind == "house" else "inferred",
                                      (f"The register reads the map's colours as '{row.get('map_material', '')}'."
                                       if kind == "house" else
                                       f"The trace's fabric colour on the main part: {main['material']}."), [src]),
                "draft_plan": _attr(plan, "inferred",
                                    f"Rectangles fitted inside the traced parts by the rules' fit (cell {fit['cell_m']} m, "
                                    f"at most {fit['max_rects']} a part, to {fit['coverage']:.0%} cover): {drawn}. Roles: "
                                    f"the main part's largest rectangle is the main body; a shallow rectangle at the "
                                    f"front is a bay; the sheet's ranges, porches and stone fronts keep their roles. "
                                    f"Storeys per piece and roof per piece are the draft rules' (reconstructed).",
                                    [src]),
                "draft_elevation": _attr(elev, "reconstructed",
                                         f"RECONSTRUCTED by the draft rules, family row '{fam['family_rule']}'"
                                         f"{' overlaid with the frontage row: ' + frow['why'] if frow.get('why') else ''} "
                                         f"Heights are the rules' starting values inside RECONSTRUCTION-RULES.md's ranges; "
                                         f"bays, entrance side, chimneys and dormers are counts the family rules choose, "
                                         f"and the seed {seed} only tints the fabric inside +-6 %. Liberty {liberty}."
                                         f"{' ' + frow['station']['note'] if kind == 'service' and frow.get('station') else ''}"),
                "draft": _attr({"pass": pass_, "liberty": liberty, "register_row": fid, "census_ids": census_ids,
                                "trace_building": b["id"] if not join else f"{b['id']}+{join['with']}", "seed": seed, "replaceable_by": refined_by,
                                "card": f"District draft — refined by {', '.join(refined_by)}."},
                               "reconstructed",
                               "The draft's own provenance: the pass that wrote it, the rows it read and the "
                               "tickets that replace it attribute by attribute under this id.",
                               geometry="record_only"),
            },
        }],
    }
    return rec


def dump(rec) -> str:
    return json.dumps(rec, indent=2, ensure_ascii=False) + "\n"


def drafted_on_disk() -> dict:
    out = {}
    for p in sorted(STRUCTURES.glob("*.json")):
        try:
            st = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(st, dict) and st.get("archetype") == ARCHETYPE and refined_on_builder(st) is None:
            out[st["id"]] = p
    return out


def refined_on_builder(st: dict):
    """T-2538: a building whose per-building ticket refines its draft IN PLACE ON THIS BUILDER
    (because the kit that will carry it, K01, cannot build it yet) keeps the archetype and
    drops the pass's `draft` attribute: its record is then written by that ticket from its
    own sources, not by these rules. It is exempt here only while the rules' `skip` names it
    by id, so a draft that has merely lost its `draft` is still refused. Returns the skip's
    reason, or None for a record of the pass itself."""
    if any("draft" in (ph.get("form") or {}) for ph in st.get("phases") or []):
        return None
    skip = json.loads(RULES.read_text()).get("skip", {})
    return next((why for why in skip.values() if f"`{st.get('id')}`" in why), None)


def check(records, read=None) -> list[str]:
    """`read` stands in for the committed tree (the self-test hands it a bent copy, so the
    gate's refusal is proved without writing a byte the parallel pool could see)."""
    read = read or (lambda p: p.read_text() if p.exists() else None)
    bad = []
    have = drafted_on_disk()
    for sid, rec in records.items():
        p = STRUCTURES / f"{sid}.json"
        text = read(p)
        if text is None:
            bad.append(f"{sid}: no record — run python3 tools/draft_prairie_1904.py")
        elif text != dump(rec):
            bad.append(f"{sid}: the committed record is not what the draft rules build — re-run the tool, "
                       f"never hand-edit a draft (a per-building ticket that refines one changes its archetype, "
                       f"or drops `draft` for its own `refined_by` and skips the census id here)")
    for sid in sorted(set(have) - set(records)):
        bad.append(f"{sid}: a prairie_draft record the rules no longer build")
    return bad


def self_test() -> int:
    fails = []
    fit = {"cell_m": 0.25, "max_rects": 3, "coverage": 0.9, "min_rect_m2": 2.5, "min_side_m": 1.2}
    # an L: 10 x 4 plus 4 x 6 — two rectangles, never one box over the notch
    L = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]
    rs, cov = rects_for(L, fit)
    if len(rs) != 2 or abs(sum(_area(r) for r in rs) - 64) > 1.5:
        fails.append(f"an L-shaped part fits as {rs}, not two rectangles covering 64 m2")
    if any(_inside_share(r, (0, 0, 10, 10)) < 1 for r in rs) or max(_area(r) for r in rs) > 40.5:
        fails.append("a fitted rectangle reaches outside the traced part")
    # a rectangle is one rectangle
    rs, cov = rects_for([(0, 0), (8, 0), (8, 5), (0, 5)], fit)
    if rs != [(0.0, 0.0, 8.0, 5.0)]:
        fails.append(f"an 8 x 5 rectangle fits as {rs}")
    # T-2690: a skewed outline's side strip folds into the body; a real notch stays a notch
    sk = [(0, 0), (12, 0), (12, 6), (7, 6), (7, 7.5), (0, 7.5)]
    sfit = {**fit, "sliver_m": 2.5, "sliver_fill": 0.9, "sliver_overlap": 0.25}
    rs, cov = rects_for(sk, sfit)
    if not rs or min(r[3] - r[1] for r in rs[:1]) < 7.5 or any(min(r[2] - r[0], r[3] - r[1]) < 2.5 for r in rs):
        fails.append(f"a body with a 1.5 m strip along one side fits as {rs}, not one body with no strip")
    rs, cov = rects_for(L, sfit)
    if len(rs) != 2:
        fails.append(f"the sliver fold swallowed an L's real notch: {rs}")
    # the notation
    for txt, want in (("3B", (3, False, None, None)), ("2½S.B.; bay4B; rear2B", (2, True, 2, 4)),
                      ("3S.B.; rear2B", (3, False, 2, None))):
        if storeys_of(txt) != want:
            fails.append(f"storeys_of({txt!r}) = {storeys_of(txt)}, not {want}")
    if service_storeys("2½-storey brick GARAGE on the alley") != (2, True):
        fails.append("a 2½-storey garage reading is not two storeys and a half")
    # the check refuses a hand edit, and a missing record, read from a stand-in tree
    recs = build_records()
    if recs:
        sid = sorted(recs)[0]
        bent = json.loads(dump(recs[sid]))
        bent["name"] += " (edited)"
        target = STRUCTURES / f"{sid}.json"
        if not any(sid in b for b in check(recs, lambda p: dump(bent) if p == target else dump(recs[p.stem]))):
            fails.append("--check accepts a hand-edited draft record")
        if not any("no record" in b for b in check(recs, lambda p: None if p == target else dump(recs[p.stem]))):
            fails.append("--check accepts a drafted building with no record")
    for f in fails:
        print(f"  self-test | FAIL {f}")
    print(f"draft_prairie_1904 --self-test: {'ok' if not fails else 'FAIL'} ({8 - min(8, len(fails))} of 8 cases)")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    recs = build_records()
    if args.check:
        bad = check(recs)
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        print(f"draft_prairie_1904 --check: {'ok' if not bad else 'FAIL'} — {len(recs)} draft record(s)")
        return 1 if bad else 0
    rules = json.loads(RULES.read_text())
    rows = register_rows(sorted(rules["blocks"]))
    if REGISTER_CSV.exists():
        REGISTER_ROWS.write_text(json.dumps({
            "_doc": "The T-1837 frontage-register rows the district draft reads, copied from the tickets repo's "
                    "evidence/T-1837-prairie-1904-architectural-study/frontage-register.csv by "
                    "tools/draft_prairie_1904.py so the gate can re-derive the drafts without that checkout.",
            "rows": {k: rows[k] for k in sorted(rows)}}, indent=2, ensure_ascii=False) + "\n")
    for sid, rec in sorted(recs.items()):
        (STRUCTURES / f"{sid}.json").write_text(dump(rec))
        print(f"draft_prairie_1904: wrote data/structures/{sid}.json")
    for sid, p in drafted_on_disk().items():
        if sid not in recs:
            p.unlink()
            print(f"draft_prairie_1904: removed {p.relative_to(ROOT)} (no longer drafted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
