#!/usr/bin/env python3
"""Hold the 1904 street surfaces to their grid, their sources and their liberties (T-1728).

    python3 tools/check_street_surfaces.py --check       # the contract, on the committed files
    python3 tools/check_street_surfaces.py --self-test   # prove each rule by breaking it
    python3 tools/check_street_surfaces.py --table       # print every face / roadway / alley's surface

WHAT IT GUARDS. data/street_surfaces/1904.json is AUTHORED: it says what every
carriageway, alley and sidewalk band of data/street_grid/1904.json (T-0474) was made of
on 1 July 1904. The ticket's acceptance is that every surface has a material, a tier and
an existence range that bounds the scene date, and that nothing is claimed past its
evidence. So the contract is:

  * COVERAGE. Every carriageway and alley in the grid, and every band of every face, has
    a surface; nothing in the surfaces file names a piece of grid that does not exist.
  * TIERS. attested | inferred | reconstructed, and nothing else. An attested or inferred
    surface cites at least one source; an ATTESTED one cites a tier-1 or tier-2 record
    that is not on the file's `bounding_only_sources` list -- the 1904 paving report and
    the 1905 code bound what a block could have been and never say what one was (the
    Prairie library's own warning, made a rule) -- and an INFERRED one cannot rest on
    those alone either. A reconstructed one names a liberty, and that liberty is a
    heading in docs/LIBERTIES.md.
  * SOURCES. Every source id resolves to data/sources/<id>.json (AGENTS.md rule 1).
  * THE RANGE. `exists.from` <= the scene date <= `exists.to`, each with its basis in
    words. A year alone reads as the whole year on the side that is least generous: a
    `from` year counts from 1 January, a `to` year until 31 December.
  * MATERIALS. Each names a directory of assets/textures/prairie_1904_pbr/ holding a
    material.json whose id matches, its eight engine-neutral maps and the three web maps
    the renderer binds, and `bounded_by` sources that resolve.
  * PIECES. A carriageway cut into pieces cuts at a carriageway the grid has, and only its
    last piece runs to the end.

It reads; it writes nothing.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SURFACES = ROOT / "data" / "street_surfaces" / "1904.json"
GRID = ROOT / "data" / "street_grid" / "1904.json"
SOURCES = ROOT / "data" / "sources"
LIBERTIES = ROOT / "docs" / "LIBERTIES.md"
TEXTURES = ROOT / "assets"
TIERS = ("attested", "inferred", "reconstructed")
MASTER = ("basecolor", "normal_gl", "normal_dx", "roughness", "height16", "ao", "metallic", "orm")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def day(text: str, side: str) -> dt.date:
    """'1904-07-01' | '1904-07' | '1904' -> a date, least generous on its side."""
    m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", str(text))
    if not m:
        raise ValueError(f"not a date: {text!r}")
    y, mo, d = int(m[1]), m[2], m[3]
    if d:
        return dt.date(y, int(mo), int(d))
    if mo:
        mo = int(mo)
        if side == "from":
            return dt.date(y, mo, 1)
        nxt = dt.date(y + (mo == 12), mo % 12 + 1, 1)
        return nxt - dt.timedelta(days=1)
    return dt.date(y, 1, 1) if side == "from" else dt.date(y, 12, 31)


def source_tiers() -> dict:
    out = {}
    for p in SOURCES.glob("*.json"):
        try:
            out[p.stem] = load(p).get("tier")
        except (OSError, json.JSONDecodeError):
            out[p.stem] = None
    return out


def liberty_ids() -> set:
    try:
        return set(re.findall(r"^### (L\d+) —", LIBERTIES.read_text(encoding="utf-8"), re.M))
    except OSError:
        return set()


def check_surface(where: str, s: dict, doc: dict, target: dt.date, tiers: dict, libs: set) -> list:
    bad = []
    mat = s.get("material")
    if mat not in (doc.get("materials") or {}):
        bad.append(f"{where}: material {mat!r} is not in the materials table")
    tier = s.get("tier")
    if tier not in TIERS:
        bad.append(f"{where}: tier {tier!r} is not one of {', '.join(TIERS)}")
    srcs = s.get("sources") or []
    for sid in srcs:
        if sid not in tiers:
            bad.append(f"{where}: source {sid!r} does not resolve in data/sources/")
    if tier in ("attested", "inferred") and not srcs:
        bad.append(f"{where}: an {tier} surface cites no source")
    bounding = set(doc.get("bounding_only_sources") or [])
    if tier == "attested" and not any((tiers.get(sid) or 9) <= 2 and sid not in bounding for sid in srcs):
        bad.append(f"{where}: attested, but no tier-1 or tier-2 record of THIS block among its sources "
                   f"(a bounding-only source cannot attest a block)")
    if tier == "inferred" and srcs and all(sid in bounding for sid in srcs):
        bad.append(f"{where}: inferred from bounding-only sources, which say nothing of this block")
    if tier == "reconstructed":
        lib = s.get("liberty")
        if not lib:
            bad.append(f"{where}: reconstructed with no liberty named")
        elif lib not in libs:
            bad.append(f"{where}: liberty {lib} is not a heading in docs/LIBERTIES.md")
    ex = s.get("exists") or {}
    try:
        lo, hi = day(ex.get("from"), "from"), day(ex.get("to"), "to")
        if not lo <= target <= hi:
            bad.append(f"{where}: in place {ex.get('from')} to {ex.get('to')} does not bound {target}")
    except (TypeError, ValueError) as e:
        bad.append(f"{where}: existence range unreadable ({e})")
    for k in ("from_basis", "to_basis"):
        if not str(ex.get(k) or "").strip():
            bad.append(f"{where}: no {k} for its existence range")
    if not str(s.get("note") or "").strip():
        bad.append(f"{where}: no note saying what the surface rests on")
    return bad


def contract(doc: dict, grid: dict, tiers: dict | None = None, libs: set | None = None,
             textures: Path = TEXTURES) -> list:
    tiers = source_tiers() if tiers is None else tiers
    libs = liberty_ids() if libs is None else libs
    bad = []
    target = day(doc.get("target_date", ""), "from")
    if doc.get("target_date") != grid.get("target_date"):
        bad.append(f"target date {doc.get('target_date')} is not the grid's {grid.get('target_date')}")

    # materials and their maps
    for mid, m in (doc.get("materials") or {}).items():
        d = textures / doc.get("texture_library", "textures/prairie_1904_pbr/") / m.get("texture", "")
        sheet_p = d / "material.json"
        if not sheet_p.exists():
            bad.append(f"material {mid}: no material.json at {sheet_p.relative_to(ROOT) if sheet_p.is_relative_to(ROOT) else sheet_p}")
            continue
        sheet = load(sheet_p)
        if sheet.get("id") != d.name:
            bad.append(f"material {mid}: material.json id {sheet.get('id')!r} is not its directory {d.name!r}")
        for suf in MASTER:
            ext = "png"
            if not (d / f"{d.name}_{suf}.{ext}").exists():
                bad.append(f"material {mid}: map {d.name}_{suf}.png is missing")
        for suf, name in (sheet.get("web") or {}).items():
            if not (d / name).exists():
                bad.append(f"material {mid}: web map {name} is missing")
        if set((sheet.get("web") or {}).keys()) != {"basecolor", "normal_gl", "orm"}:
            bad.append(f"material {mid}: material.json must name the three web maps the renderer binds")
        for sid in m.get("bounded_by") or []:
            if sid not in tiers:
                bad.append(f"material {mid}: bounding source {sid!r} does not resolve")

    for sid in (doc.get("authority") or {}).get("sources") or []:
        if sid not in tiers:
            bad.append(f"authority: source {sid!r} does not resolve")

    # carriageways
    cw_ids = {c["id"] for c in grid.get("carriageways", [])}
    cws = doc.get("carriageways") or {}
    for cid in sorted(cw_ids - set(cws)):
        bad.append(f"carriageway {cid}: the grid draws it and no surface is given")
    for cid in sorted(set(cws) - cw_ids):
        bad.append(f"carriageway {cid}: named in the surfaces file, not in the grid")
    for cid, s in cws.items():
        if not isinstance(s.get("priority", 0), int):
            bad.append(f"carriageway {cid}: priority must be an integer")
        pieces = s.get("pieces")
        if pieces:
            for i, p in enumerate(pieces):
                last = i == len(pieces) - 1
                if last and p.get("until"):
                    bad.append(f"carriageway {cid}: its last piece must run to the end, not until {p['until']}")
                if not last and p.get("until") not in cw_ids:
                    bad.append(f"carriageway {cid}: piece {i} cuts at {p.get('until')!r}, which the grid does not have")
                bad += check_surface(f"carriageway {cid} piece {i}", p, doc, target, tiers, libs)
        else:
            bad += check_surface(f"carriageway {cid}", s, doc, target, tiers, libs)

    # alleys
    al_ids = {a["id"] for a in grid.get("alleys", [])}
    als = doc.get("alleys") or {}
    for aid in sorted(al_ids - set(als)):
        bad.append(f"alley {aid}: the grid draws it and no surface is given")
    for aid in sorted(set(als) - al_ids):
        bad.append(f"alley {aid}: named in the surfaces file, not in the grid")
    for aid, s in als.items():
        bad += check_surface(f"alley {aid}", s, doc, target, tiers, libs)

    # bands: a default per band, overridable per face
    bands = doc.get("bands") or {}
    faces = doc.get("faces") or {}
    face_ids = {f["id"] for f in grid.get("faces", [])}
    for fid in sorted(set(faces) - face_ids):
        bad.append(f"face {fid}: named in the surfaces file, not in the grid")
    grid_bands = sorted({b for f in grid.get("faces", []) for b in (f.get("bands") or {})})
    for b in grid_bands:
        missing = [f["id"] for f in grid.get("faces", []) if b in (f.get("bands") or {})
                   and b not in bands and b not in (faces.get(f["id"]) or {})]
        if missing:
            bad.append(f"band {b}: {len(missing)} face(s) have no surface for it, e.g. {missing[0]}")
    for b, s in bands.items():
        if b not in grid_bands:
            bad.append(f"band {b}: named in the surfaces file, not a band the grid lays out")
        bad += check_surface(f"band {b}", s, doc, target, tiers, libs)
        for xs in (s.get("blocks") or {}):
            if xs not in (grid.get("cross_sections") or {}):
                bad.append(f"band {b}: walk blocks for cross-section {xs!r}, which the grid does not have")
    for fid, over in faces.items():
        for b, s in over.items():
            bad += check_surface(f"face {fid} {b}", s, doc, target, tiers, libs)
    return bad


def table(doc: dict, grid: dict) -> str:
    mats = doc.get("materials", {})
    name = lambda s: mats.get(s.get("material"), {}).get("name", s.get("material"))
    rows = ["| roadway | material | tier | in place |", "|---|---|---|---|"]
    for c in grid.get("carriageways", []):
        s = doc["carriageways"][c["id"]]
        for p in (s.get("pieces") or [s]):
            label = c["where"] + (f" (to {p['until']})" if p.get("until") else (" (rest)" if s.get("pieces") else ""))
            rows.append(f"| {label} | {name(p)} | {p['tier']} | {p['exists']['from']} – {p['exists']['to']} |")
    rows += ["", "| alley | material | tier |", "|---|---|---|"]
    for a in grid.get("alleys", []):
        s = doc["alleys"][a["id"]]
        rows.append(f"| {a['id']} | {name(s)} | {s['tier']} |")
    rows += ["", "| face | walk | curb | parkway | margin |", "|---|---|---|---|---|"]
    for f in grid.get("faces", []):
        over = (doc.get("faces") or {}).get(f["id"], {})
        cells = []
        for b in ("walk", "curb", "parkway", "margin"):
            s = over.get(b) or doc["bands"].get(b)
            cells.append(f"{name(s)} ({s['tier']})")
        rows.append(f"| {f['where']} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def check() -> list:
    for p in (SURFACES, GRID):
        if not p.exists():
            return [f"{p.relative_to(ROOT)} is missing"]
    return contract(load(SURFACES), load(GRID))


def self_test() -> int:
    base, grid = load(SURFACES), load(GRID)
    tiers, libs = source_tiers(), liberty_ids()
    cases = []

    def breaks(label, mutate, needle):
        doc = copy.deepcopy(base)
        mutate(doc)
        found = [b for b in contract(doc, grid, tiers, libs) if needle in b]
        cases.append((label, bool(found)))

    breaks("a carriageway the grid draws with no surface is refused",
           lambda d: d["carriageways"].pop("prairie_18_20"), "no surface is given")
    breaks("an alley named that the grid does not have is refused",
           lambda d: d["alleys"].__setitem__("alley_nowhere", d["alleys"]["alley_indiana_prairie_16_18"]),
           "not in the grid")
    breaks("a tier outside the three is refused",
           lambda d: d["carriageways"]["prairie_16_18"].__setitem__("tier", "documented"), "is not one of")
    breaks("an invented source id is refused",
           lambda d: d["carriageways"]["prairie_16_18"]["sources"].append("a_source_nobody_wrote"),
           "does not resolve")
    breaks("an attested surface resting only on a bounding report is refused",
           lambda d: d["carriageways"]["prairie_16_18"].__setitem__("sources", ["alvord_street_paving_report_1904"]),
           "bounding-only source cannot attest")
    breaks("a reconstructed surface with no liberty is refused",
           lambda d: d["bands"]["walk"].pop("liberty"), "no liberty named")
    breaks("a liberty number that is not in LIBERTIES.md is refused",
           lambda d: d["bands"]["walk"].__setitem__("liberty", "L99999"), "not a heading")
    breaks("a range that ends before the scene date is refused",
           lambda d: d["carriageways"]["prairie_20_22"]["exists"].__setitem__("to", "1903-12-31"), "does not bound")
    breaks("a range that starts after the scene date is refused",
           lambda d: d["carriageways"]["prairie_16_18"]["exists"].__setitem__("from", "1904-08"), "does not bound")
    breaks("a range with no basis is refused",
           lambda d: d["bands"]["curb"]["exists"].__setitem__("to_basis", ""), "no to_basis")
    breaks("a band with no surface on any face is refused",
           lambda d: d["bands"].pop("curb"), "have no surface")
    breaks("a piece that cuts at a street the grid lacks is refused",
           lambda d: d["carriageways"]["calumet_20_22"]["pieces"][0].__setitem__("until", "e99th"),
           "does not have")
    breaks("a material with no texture directory is refused",
           lambda d: d["materials"]["sheet_asphalt"].__setitem__("texture", "roadway/nothing_here"),
           "no material.json")
    cases.append(("a year alone reads least generously: 'from 1904' holds, 'to 1904' holds, 'from 1905' fails",
                  day("1904", "from") <= dt.date(1904, 7, 1) <= day("1904", "to") and
                  day("1905", "from") > dt.date(1904, 7, 1)))
    cases.append(("the committed surfaces pass", not contract(base, grid, tiers, libs)))
    for label, ok in cases:
        print(("   ok   " if ok else "   FAIL ") + label)
    return 0 if all(ok for _, ok in cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.table:
        print(table(load(SURFACES), load(GRID)))
        return 0
    bad = check()
    for b in bad:
        print("FAIL", b)
    if not bad:
        doc = load(SURFACES)
        tally = {}
        for s in list(doc["carriageways"].values()) + list(doc["alleys"].values()) + list(doc["bands"].values()):
            for p in (s.get("pieces") or [s]):
                tally[p["tier"]] = tally.get(p["tier"], 0) + 1
        print(f"OK the 1904 street surfaces cover the grid: {len(doc['carriageways'])} carriageways, "
              f"{len(doc['alleys'])} alleys, {len(doc['bands'])} bands, {len(doc['materials'])} materials; "
              + ", ".join(f"{n} {t}" for t, n in sorted(tally.items())))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
