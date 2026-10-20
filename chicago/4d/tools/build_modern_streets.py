#!/usr/bin/env python3
"""Today's streets under every year — T-2741.

    tools/build_modern_streets.py --source Transportation.geojson --write
    tools/build_modern_streets.py --check     the committed file holds its shape (no network)
    tools/build_modern_streets.py --gate      the same, quiet, for tools/check.sh

The owner, 2026-10-17: "i do want to see the street you are standing on in the era and
i want the current modern day map overlaid on all of them 1812, 1835 and 1904 so you
have the current street name/address you are at". So the compass readout says, in every
year, the street you stand on as it was named THEN and the street and house number you
stand at TODAY, and the overview map can draw today's streets over the period ground.

WHAT THIS IS. A clip of the City of Chicago's own street centerline file — the
Department of Innovation and Technology's `osd-street-center-line` release on GitHub,
MIT-licensed, last edited 2014-10-15 — to the ground the three scenes cover, projected
into this project's local frame (data/datum.json: EPSG:26916 metres less the origin).
Each segment keeps its name, the grid coordinate it sits on (the City's own EWNS field:
Prairie Avenue is 300 E, Eighteenth Street 1800 S) and its block's address ranges, so
the renderer reads a house number off the segment rather than computing one from a
rule of thumb. Chicago's grid is NOT 800 numbers a mile near the Loop (Madison to
Roosevelt is 1200 numbers in about a mile; Roosevelt to Cermak 1000), which is exactly
why the numbers come off the City's ranges and not off a formula.

WHAT IT IS NOT. It is today's map, a navigation aid, and nothing in a period layer is
read off it or traced from it: no street, lot or building of 1812, 1835 or 1904 moves
because of it. Where it and a period street disagree by metres, both are shown as they
are; the 1835 records already carry their modern successor's name (`name_2026`) and
that is the town's own claim, unchanged.

WHAT IS LEFT OUT, AND WHY. Lower and middle levels (Lower Wacker and its kin), ramps,
expressway connectors and river centrelines (classes 7, 9, RIV and E, any segment
whose both ends sit below grade, and names carrying LOWER, RAMP or SUB) — a visitor
stands on the ground, and the upper street is the address. Vacated, proposed and
under-construction segments (STATUS V, P, UC, C) are dropped: they are not streets a
visitor could stand on today.

RENAMED SINCE THE FILE WAS CUT (2014), stated here rather than silently edited in:
Congress Parkway east of the river is Ida B. Wells Drive (City Council, 2019) and
Lake Shore Drive is Jean Baptiste Point DuSable Lake Shore Drive (City Council, 2021).
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "modern" / "streets.json"
DATUM = ROOT / "data" / "datum.json"

SOURCE_ID = "chicago_street_center_lines"
SOURCE_URL = ("https://raw.githubusercontent.com/Chicago/osd-street-center-line/"
              "master/data/Transportation.geojson")

# The ground the three scenes cover, plus a margin: the 1812/1835 heightfield spans
# east -705..1700, north -3800..1120 (e1830_natural / e1834_harbor_cut) and 1904's sits
# inside it. Local metres.
BOX = (-800.0, -4000.0, 2300.0, 1250.0)

KEEP_CLASS = {"1", "2", "3", "4", "5"}
DROP_STATUS = {"V", "P", "UC", "C"}
DROP_WORDS = ("LOWER", "RAMP", " SUB", "MIDDLE")

TYPES = {
    "AVE": "Ave", "ST": "St", "DR": "Dr", "BLVD": "Blvd", "PL": "Pl", "CT": "Ct",
    "RD": "Rd", "PKWY": "Pkwy", "TER": "Ter", "WAY": "Way", "LN": "Ln", "PLZ": "Plz",
    "EXPY": "Expy", "HWY": "Hwy", "SQ": "Sq", "ROW": "Row", "CIR": "Cir",
}

SIMPLIFY_M = 0.5


def doc_text() -> str:
    # Python 3.13 strips docstring indentation and 3.11 does not; cleandoc makes the
    # committed text the same under both (the gate runs 3.11).
    return inspect.cleandoc(__doc__ or "")


def title_word(w: str) -> str:
    if w[:1].isdigit():
        return w.lower()  # 18TH -> 18th
    if w in ("LA", "DE", "DU", "MC"):
        return w.title()
    return w.capitalize() if "'" not in w else w.title()


def street_name(p: dict) -> str | None:
    nam = (p.get("STREET_NAM") or "").strip()
    if not nam:
        return None
    words = [title_word(w) for w in nam.split()]
    name = " ".join(words)
    if name == "Lake Shore":
        name = "DuSable Lake Shore"
    if name == "La Salle":
        name = "LaSalle"  # the City's file splits it; the street signs do not
    typ = (p.get("STREET_TYP") or "").strip()
    pre = (p.get("PRE_DIR") or "").strip()
    suf = (p.get("SUF_DIR") or "").strip()
    out = " ".join(x for x in (pre, name, TYPES.get(typ, typ.title()), suf) if x)
    return out


def renamed(name: str, local_path: list[tuple[float, float]]) -> str:
    # Congress Parkway, Loop portion, east of the river -> Ida B. Wells Drive (2019).
    if name in ("W Congress Pkwy", "E Congress Pkwy", "E Congress Dr") and \
            min(e for e, _ in local_path) > -60:
        return name.split(" ")[0] + " Ida B. Wells Dr"
    return name


def rdp(pts: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    if len(pts) < 3:
        return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1e-9
    best, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * px - dx * py + bx * ay - by * ax) / L
        if d > best:
            best, idx = d, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return rdp(pts[: idx + 1], tol)[:-1] + rdp(pts[idx:], tol)


def axis_of(path: list[tuple[float, float]]) -> str:
    (ax, ay), (bx, by) = path[0], path[-1]
    ang = math.degrees(math.atan2(abs(bx - ax), abs(by - ay)))  # 0 = north-south
    if ang <= 20:
        return "ns"
    if ang >= 70:
        return "ew"
    return "diag"


def build(source: Path) -> dict:
    from pyproj import Transformer  # noqa: PLC0415 — only --write needs it

    datum = json.loads(DATUM.read_text())
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    t = Transformer.from_crs("EPSG:4326", "EPSG:26916", always_xy=True)
    raw = source.read_bytes()
    gj = json.loads(raw)
    names: list[str] = []
    name_ix: dict[str, int] = {}
    segs = []
    dropped = {"class": 0, "status": 0, "level": 0, "word": 0, "outside": 0, "unnamed": 0}
    e0, n0, e1, n1 = BOX
    for f in gj["features"]:
        p = f["properties"]
        g = f.get("geometry")
        if not g:
            continue
        if p.get("CLASS") not in KEEP_CLASS:
            dropped["class"] += 1
            continue
        if p.get("STATUS") in DROP_STATUS:
            dropped["status"] += 1
            continue
        if (p.get("F_ZLEV") or 0) < 0 and (p.get("T_ZLEV") or 0) < 0:
            dropped["level"] += 1
            continue
        nam = " " + (p.get("STREET_NAM") or "")
        if any(w in nam for w in DROP_WORDS):
            dropped["word"] += 1
            continue
        coords = g["coordinates"] if g["type"] == "LineString" else \
            [c for part in g["coordinates"] for c in part]
        local = []
        for lon, lat in coords:
            x, y = t.transform(lon, lat)
            local.append((x - oe, y - on))
        if not any(e0 <= e <= e1 and n0 <= n <= n1 for e, n in local):
            dropped["outside"] += 1
            continue
        name = street_name(p)
        if not name:
            dropped["unnamed"] += 1
            continue
        name = renamed(name, local)
        path = rdp(local, SIMPLIFY_M)
        axis = axis_of(path)
        ewns_dir = p.get("EWNS_DIR")
        coord = p.get("EWNS_COORD") or 0
        if ewns_dir in ("W", "S"):
            grid = -int(round(coord))
        elif ewns_dir in ("E", "N"):
            grid = int(round(coord))
        elif (p.get("STREET_NAM") or "") in ("STATE", "MADISON"):
            grid = 0
        else:
            grid = None
        if name not in name_ix:
            name_ix[name] = len(names)
            names.append(name)
        lf, lt = int(p.get("LOGICLF") or 0), int(p.get("LOGICLT") or 0)
        rf, rt = int(p.get("LOGICRF") or 0), int(p.get("LOGICRT") or 0)
        lpar = p.get("L_PARITY") or ("O" if lf % 2 else "E")
        flat = [round(v, 1) for pt in path for v in pt]
        segs.append([name_ix[name], axis, grid, int(p["CLASS"]), lf, lt, rf, rt, lpar, flat])
    segs.sort(key=lambda s: (names[s[0]], s[9][0], s[9][1]))
    return {
        "_doc": doc_text(),
        "ticket": "T-2741",
        "generated_by": "tools/build_modern_streets.py --write",
        "source": SOURCE_ID,
        "source_url": SOURCE_URL,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_edited": "2014-10-15",
        "frame": "local East-North metres: EPSG:26916 less data/datum.json origin_utm_e/n",
        "box_local_m": list(BOX),
        "simplify_m": SIMPLIFY_M,
        "renamed_since_source": {
            "Congress Pkwy (east of the river)": "Ida B. Wells Dr (City Council, 2019)",
            "Lake Shore Dr": "DuSable Lake Shore Dr (City Council, 2021)",
        },
        "fields": ["name", "axis", "grid", "class", "left_from", "left_to",
                   "right_from", "right_to", "left_parity", "path"],
        "field_notes": {
            "axis": "ns | ew | diag, from the segment's own end-to-end bearing",
            "grid": "the grid line the street sits on, signed: + north or east, - south or west "
                    "(City EWNS); null for a diagonal or where the City records none",
            "left_from": "the block's address range on the left side, from-node to to-node "
                         "(City LOGICLF..LOGICRT); 0 where that side carries no numbers",
            "path": "e0, n0, e1, n1, ... in the from-node to to-node order the ranges run",
        },
        "dropped": dropped,
        "counts": {"segments": len(segs), "names": len(names)},
        "names": names,
        "segments": segs,
    }


def check(doc: dict) -> list[str]:
    errs = []
    if doc.get("source") != SOURCE_ID:
        errs.append("source is not chicago_street_center_lines")
    if not (ROOT / "data" / "sources" / f"{SOURCE_ID}.json").exists():
        errs.append(f"data/sources/{SOURCE_ID}.json is missing")
    if doc.get("_doc") != doc_text():
        errs.append("_doc is stale against the tool's docstring: rerun --write")
    names = doc.get("names") or []
    segs = doc.get("segments") or []
    if doc.get("counts") != {"segments": len(segs), "names": len(names)}:
        errs.append("counts disagree with the file")
    if len(segs) < 500:
        errs.append(f"only {len(segs)} segments — the clip has lost the city")
    e0, n0, e1, n1 = doc.get("box_local_m") or BOX
    used = set()
    for i, s in enumerate(segs):
        if len(s) != 10:
            errs.append(f"segment {i}: {len(s)} fields")
            continue
        ni, axis, grid, cls, lf, lt, rf, rt, lpar, flat = s
        used.add(ni)
        if not (0 <= ni < len(names)) or not names[ni]:
            errs.append(f"segment {i}: bad name index")
        if axis not in ("ns", "ew", "diag"):
            errs.append(f"segment {i}: axis {axis!r}")
        if lpar not in ("E", "O"):
            errs.append(f"segment {i}: parity {lpar!r}")
        if len(flat) < 4 or len(flat) % 2:
            errs.append(f"segment {i}: path has {len(flat)} numbers")
            continue
        pts = list(zip(flat[::2], flat[1::2]))
        if not any(e0 - 1 <= e <= e1 + 1 and n0 - 1 <= n <= n1 + 1 for e, n in pts):
            errs.append(f"segment {i} ({names[ni]}): wholly outside the box")
    if used != set(range(len(names))):
        errs.append("names lists a street no segment uses")
    # Three anchors any reader can check against a street sign: the corners this project
    # already holds OSM control for (data/traces/prairie_1904_control.json and the Wright
    # GCPs) must fall on segments carrying those names.
    for want, (e, n) in {"S Prairie Ave": (1401.86, -3206.93), "E 18th St": (1401.86, -3206.93),
                         "N State St": (822.5, 633.0), "W Madison St": (800.0, -525.3)}.items():
        best = math.inf
        for s in segs:
            if names[s[0]] != want:
                continue
            fl = s[9]
            for k in range(0, len(fl) - 2, 2):
                ax, ay, bx, by = fl[k], fl[k + 1], fl[k + 2], fl[k + 3]
                dx, dy = bx - ax, by - ay
                L2 = dx * dx + dy * dy or 1e-9
                u = max(0.0, min(1.0, ((e - ax) * dx + (n - ay) * dy) / L2))
                best = min(best, math.hypot(e - ax - u * dx, n - ay - u * dy))
        if best > 12:
            errs.append(f"{want} lies {best:.1f} m from its control corner (more than 12 m)")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=Path)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    if a.write:
        if not a.source:
            print(f"--write needs --source (download {SOURCE_URL})", file=sys.stderr)
            return 2
        doc = build(a.source)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}: {doc['counts']} dropped {doc['dropped']}")
    doc = json.loads(OUT.read_text())
    errs = check(doc)
    for e in errs:
        print(f"FAIL modern streets: {e}")
    if not errs and not a.gate:
        print(f"ok modern streets: {doc['counts']['segments']} segments, "
              f"{doc['counts']['names']} names")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
