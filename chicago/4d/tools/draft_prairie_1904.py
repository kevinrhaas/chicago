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
for service buildings the census reading (`2-storey brick BARN`). Everything else —
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


def census_path(sheet: str) -> Path:
    return REPO / "chicago" / "prairie_1904_v1" / "data" / "sheet_census" / f"sheet-{sheet}.json"


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


def rects_for(poly, fit, front_from_u=None):
    """Rectangles inside `poly`, largest first. With `front_from_u` (a frontage row's
    `front_body_from_u_m`) the first is the largest in front of that lot-frame u, so a
    house traced in one piece with its rear range keeps its street body as the main."""
    cell = fit["cell_m"]
    cells = scanfill(poly, cell)
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
    return out, (1 - len(cells) / total) if total else 0.0


def _area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


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
        census = json.loads(census_path(sheet).read_text())
        polys = {}
        for f in census["frontages"]:
            for p in f["polygons"]:
                polys[p["id"]] = (f, p)
        for vg in census.get("vacant_ground", []):
            polys[vg["id"]] = (None, vg)
        for parcel in trace["parcels"]:
            side = parcel["side"]
            if side not in block["sides"]:
                continue
            frame = lot_frame(grid[parcel["parcel_id"]])
            lot = [to_uv(frame, p) for p in grid[parcel["parcel_id"]]["polygon_local_m"]]
            lot_v = (min(p[1] for p in lot), max(p[1] for p in lot))
            street_u = max(p[0] for p in lot)
            house_sid = None
            for b in parcel["buildings"]:
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
                rec = draft_record(rules, block, sheet, parcel, b, kind, f, cp, fid, frow, row, frame, lot_v,
                                   street_u, datum, hts, fit, house_sid)
                if kind == "house":
                    house_sid = rec["id"]
                out[rec["id"]] = rec
    return out


def draft_record(rules, block, sheet, parcel, b, kind, f, cp, fid, frow, row, frame, lot_v, street_u,
                 datum, hts, fit, house_sid):
    # ---- the plan: rectangles inside each traced part, in the lot frame
    pieces = []
    order = {"main": 0, "stone_front": 1, "range": 2, "porch": 3}
    for part in sorted(b["parts"], key=lambda p: (order.get(p["role"], 9), -p["area_m2"], p["id"])):
        poly = [to_uv(frame, q) for q in part["polygon_local_m"]]
        rs, cov = rects_for(poly, fit, frow.get("front_body_from_u_m")
                            if part["role"] == "main" and kind == "house" else None)
        for k, r in enumerate(rs):
            pieces.append({"trace_part": part["id"], "trace_role": part["role"], "material": part["material"],
                           "rect": r, "k": k, "coverage": round(cov, 3)})
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

    # ---- storeys and family
    notation = row.get("raw_story_notation", "") if kind == "house" else ""
    if kind == "house":
        full, half, rear_n, bay_n = storeys_of(notation)
    else:
        full, half = service_storeys(cp.get("reading_1911", ""))
        rear_n = bay_n = None
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
        elif r[0] >= mu1 - 4.0 and depth <= 4.0 and kind == "house":
            role, st, rf = "bay", (full if p["trace_role"] == "main" or p["material"] == "stone" else 1), "flat"
        elif p["trace_role"] == "main":
            big = min(depth, r[3] - r[1]) >= 4.5 and _area(r) >= 30
            role, st = "wing", full
            rf = ("mansard" if roof == "mansard" else "hip") if big and kind == "house" else (
                "gable" if kind == "service" and big else "flat")
        else:
            role = "range"
            st = rear_n if rear_n else max(1, full - 1)
            rf = "flat"
        if kind == "service" and role in ("main", "wing", "range"):
            st = min(st, full) if role != "main" else full
        parts.append({"id": f"r{n + 1}", "role": role, "storeys": st, "roof": rf,
                      "rect": [round(r[0] - mu0, 3), round(r[1] - mv0, 3), round(r[2] - mu0, 3), round(r[3] - mv0, 3)],
                      "from": f"{b['id']} {p['trace_part']} ({p['trace_role']}, {p['material']}), "
                              f"rectangle {p['k'] + 1} of that part; the part's rectangles cover "
                              f"{p['coverage']:.0%} of its fill"})
    lot_v_local = [round(lot_v[0] - mv0, 3), round(lot_v[1] - mv0, 3)]
    street_local = round(street_u - mu0, 3)

    # ---- identity
    num = (row.get("address", "") or "").split(" ")[0] if kind == "house" or fid else ""
    addr = parcel["parcel_id"].split("_", 1)[1]
    slug = frow.get("slug") or "house"
    base_id = f"{slug}_{addr}_prairie" if f else f"shed_{addr}_prairie"
    if kind == "service":
        sid = f"{house_sid}_coach_house" if house_sid and f else base_id
    else:
        sid = base_id
    seed = seed_of(sid)
    front_tickets = row.get("front_tickets", "") if kind == "house" else ""
    rear_ticket = block["rear_ticket"][parcel["side"]]
    # a side drafted by a later ticket names its own pass and liberty (T-2330 drafts block 28's east)
    side_rules = block.get("by_side", {}).get(parcel["side"], {})
    pass_ = side_rules.get("pass", rules["ticket"])
    liberty = side_rules.get("liberty", block["liberty"])
    refined_by = [t.strip() for t in (front_tickets.split(",") if front_tickets else [rear_ticket]) if t.strip()]

    # ---- elevation
    width = mv1 - mv0
    bays = frow.get("front_bays") or max(2, min(6, round(width / hts["front_bay_m"])))
    feats = []
    for ft in (frow.get("features", []) if kind == "house" else []):
        ft = dict(ft)
        corner = ft.pop("corner")
        r = ft.get("radius_m", 1.9)
        at = [round(mu1 - mu0 - r * 0.35, 3), round((r * 0.35) if corner == "front_v0" else (width - r * 0.35), 3)]
        feats.append({**ft, "at": at})
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
    where = f"{addr.replace('_', '-')} S. Prairie Avenue"
    if kind == "house":
        label = (row.get("address") or where).replace(" S. Prairie Avenue", "")
        name = f"{label} Prairie Avenue — {fam_name} (district draft; refined by {', '.join(refined_by)})"
        reading = cp.get('reading_1911', '')
        ruling = (f or {}).get('decision_1904', 'present_as_mapped')
        function = _attr("residence", "inferred",
                         f"The 1911 sheet marks the building 'D' (dwelling): '{reading}'. "
                         f"Carried to 1904 on the T-1841 census ruling ({ruling})." if "(D)" in reading else
                         f"The 1911 sheet labels the building with a 1911 use, '{reading}', which the draft does not "
                         f"carry back to 1904 (the T-1837 register warns not to assume the 1904 use from it). "
                         f"The register's family row, '{fam_name}', names it a house, so the 1904 function is "
                         f"inferred residence on that row and the T-1841 census ruling ({ruling}).",
                         [SOURCE])
    else:
        owner = f"the house at {addr}" if f else "neither neighbour (the sheet does not show whose)"
        name = (f"{where} — the alley building of {owner} (district draft; refined by {rear_ticket})"
                if f else f"The shed on the strip between 1834 and 1900 Prairie Avenue (district draft; refined by {rear_ticket})")
        function = _attr("barn_or_carriage_shed", "inferred",
                         f"The 1911 sheet reads '{cp.get('reading_1911', '')}'. "
                         + (cp.get("note_1904") or "Backcast to 1904 as a yard outbuilding on the census ruling."),
                         [SOURCE])
    drawn = "; ".join(p["from"] for p in parts)
    rec = {
        "id": sid,
        "name": name,
        "aka": sorted({where} | set(frow.get("aka", []) if kind == "house" else [])),
        "archetype": ARCHETYPE,
        "function": function,
        "review_required": False,
        "research_note": (
            f"A DISTRICT DRAFT ({pass_}, the owner's district pass of 2026-10-08): a serviceable first model, "
            f"complete from the street, the walks, the alley and the air, that {', '.join(refined_by)} refine{'s' if len(refined_by) == 1 else ''} "
            f"in place under this same id. Written by tools/draft_prairie_1904.py from the sheet {sheet} trace "
            f"({b['id']}), the T-1841 census ({', '.join(census_ids)}) and the T-1837 register row {fid or 'none'}"
            f"{' (' + fam_name + ')' if fam_name else ''}; every height, roof, opening and feature is the draft rules' "
            f"reconstruction (data/components/prairie_1904/draft_prairie_1904.json; liberty {liberty})."),
        "phases": [{
            "id": PHASE,
            "documented_range": {
                "from": "1904-07-01", "to": "1911-12-31", "confidence": "inferred", "sources": [SOURCE],
                "note": ("The draft claims the 1904 target and no more: the 1911 sheet draws the building and the "
                         "T-1841 census rules it present in 1904 "
                         f"({(f or {}).get('decision_1904') or cp.get('decision_1904', 'present_as_mapped')}). "
                         "Its building and loss dates are the per-building ticket's to read.")},
            "position": {
                "utm_e": utm_e, "utm_n": utm_n, "rotation_deg": rot,
                "symbolic_location": f"{where}, parcel {parcel['parcel_id']} (data/street_grid/1904.json), "
                                     f"{parcel['side']} side of Prairie Avenue, {block['where']}.",
                "confidence": "inferred", "sources": [SOURCE],
                "note": (f"The rear corner of the main body's rectangle (lot frame u {mu0:.3f}, v {mv0:.3f} m from "
                         f"the middle of the rear lot line), through the T-1250 fit of the sheet: the georeference's "
                         f"independent check is 1.47 m RMS. Rotation {rot} degrees turns the plan's u axis onto the "
                         f"lot's own rear-to-street line."),
                "derivation": {"method": "not_derivable",
                               "reason": "The four derivation methods re-derive from the 1835 files; this position is "
                                         "re-derived from the traced sheet and the 1904 parcel by tools/draft_prairie_1904.py "
                                         "--check instead."}},
            "footprint": {
                "polygon": [[0.0, 0.0], [round(mu1 - mu0, 3), 0.0], [round(mu1 - mu0, 3), round(mv1 - mv0, 3)],
                            [0.0, round(mv1 - mv0, 3)]],
                "confidence": "inferred", "sources": [SOURCE],
                "note": ("The main body: the largest rectangle that fits inside the traced main part (u toward the "
                         "street, v along the front). The building's other rectangles are in draft_plan.")},
            "form": {
                "stories": _attr(full, "attested",
                                 (f"'{notation}' printed on the 1911 sheet: {full} full storeys"
                                  f"{' and a half storey in the roof' if half else ''}." if kind == "house" else
                                  f"The census reading '{cp.get('reading_1911', '')}': {full} storeys"
                                  f"{' and a half' if half else ''}."), [SOURCE]),
                "construction": _attr(construction, "attested" if kind == "house" else "inferred",
                                      (f"The register reads the map's colours as '{row.get('map_material', '')}'."
                                       if kind == "house" else
                                       f"The trace's fabric colour on the main part: {main['material']}."), [SOURCE]),
                "draft_plan": _attr(plan, "inferred",
                                    f"Rectangles fitted inside the traced parts by the rules' fit (cell {fit['cell_m']} m, "
                                    f"at most {fit['max_rects']} a part, to {fit['coverage']:.0%} cover): {drawn}. Roles: "
                                    f"the main part's largest rectangle is the main body; a shallow rectangle at the "
                                    f"front is a bay; the sheet's ranges, porches and stone fronts keep their roles. "
                                    f"Storeys per piece and roof per piece are the draft rules' (reconstructed).",
                                    [SOURCE]),
                "draft_elevation": _attr(elev, "reconstructed",
                                         f"RECONSTRUCTED by the draft rules, family row '{fam['family_rule']}'"
                                         f"{' overlaid with the frontage row: ' + frow['why'] if frow.get('why') else ''} "
                                         f"Heights are the rules' starting values inside RECONSTRUCTION-RULES.md's ranges; "
                                         f"bays, entrance side, chimneys and dormers are counts the family rules choose, "
                                         f"and the seed {seed} only tints the fabric inside +-6 %. Liberty {liberty}."),
                "draft": _attr({"pass": pass_, "liberty": liberty, "register_row": fid, "census_ids": census_ids,
                                "trace_building": b["id"], "seed": seed, "replaceable_by": refined_by,
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
        if isinstance(st, dict) and st.get("archetype") == ARCHETYPE:
            out[st["id"]] = p
    return out


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
                       f"never hand-edit a draft (a per-building ticket that refines one changes its archetype)")
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
    print(f"draft_prairie_1904 --self-test: {'ok' if not fails else 'FAIL'} ({6 - min(6, len(fails))} of 6 cases)")
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
