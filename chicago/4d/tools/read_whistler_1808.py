#!/usr/bin/env python3
"""read_whistler_1808.py — hold the reading of Whistler's 1808 draught of the FIRST fort.

T-2048 (piece 1 of 3 of T-0469). `data/traces/whistler_1808_fort_dearborn.json` reads
Captain John Whistler's draught of Fort Dearborn, dated in its parade 25 January 1808,
off the plate Quaife printed facing p. 164 (1913). It is the only plan of the fort
burned on 16 August 1812, and the only sheet in this dataset that states its own scale:
"The measurement of the Garrison including the Block Houses And Barrick are laid down
at twenty feet to the Inch". A reproduction does not keep the inch, so the scale is
MEASURED from the drafter's one dimension on the garrison: the flagstaff, lettered
"75 feete" along its length, drawn laid down from its foot at the centre of the parade.

    python3 tools/read_whistler_1808.py [--check]     # offline; run by check.sh
    python3 tools/read_whistler_1808.py --remeasure   # fetches the sheet (network)

`--check` holds what can be held without the raster, which the repository does not
commit (data/traces/README.md):
  * the scale is the staff's arithmetic (length / 75 ft), not a typed number;
  * every feet figure in the file is what its pixel box gives at that scale,
    so a hand-edited foot is refused;
  * the index is complete: all 34 numbers, each located, not located (with why),
    sheet-only (drawn, but where the sheet says it is not to scale), or omitted by
    the drafter. 33 and 34 MUST be the last, because the index says so;
  * the cross-checks the file says HOLD still hold on its own numbers;
  * (T-2049) the first fort's structure records are built FROM this reading: each
    `data/structures/first_fort_dearborn_*.json` names its register part, carries the
    part's measured plan dimensions (to 0.02 m) and its fort-frame box in its
    `symbolic_location`, and stands 1803-08-17 to 1812-08-16 — a range no committed
    scene date falls inside, so no scene draws the first fort beside the second one;
  * (T-2050) the fort is SEATED with one origin and one bearing: each record's utm point
    and rotation are what SEAT_LOCAL, SEAT_BEARING_DEG and its FACING give its box, and
    the two forts cannot resolve together — no second-fort phase opens inside the first
    fort's range, every scene resolves all fourteen first-fort records or none, and the
    1812 scene resolves all fourteen.

`--remeasure` fetches the working copy, refuses it if its sha256 has moved, and finds
the staff's two ends again: the longest near-continuous dark run in columns 994-1007,
bridging gaps of up to 12 px where the faint line crosses the north range's ink. It
must land on the file's own `staff_px`.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / "data" / "traces" / "whistler_1808_fort_dearborn.json"
SOURCES = ROOT / "data" / "sources"
STATUSES = {"located", "not_located", "sheet_only", "omitted_by_drafter"}
TOL_FT = 0.05
STAFF_COLS = range(994, 1008)
DARK = 140
MAX_GAP = 12


def feet(box, s, ox, oy):
    x0, y0, x1, y1 = box
    r = lambda v: round(v, 1)
    return {"e_ft": [r((x0 - ox) / s), r((x1 - ox) / s)],
            "n_ft": [r((oy - y1) / s), r((oy - y0) / s)],
            "size_ft": [r((x1 - x0) / s), r((y1 - y0) / s)]}


def same(a, b):
    return all(abs(p - q) <= TOL_FT for k in ("e_ft", "n_ft", "size_ft")
               for p, q in zip(a[k], b[k]))


def check(doc: dict) -> list[str]:
    errs: list[str] = []
    src = SOURCES / f"{doc['source_id']}.json"
    if not src.exists():
        return [f"source {doc['source_id']} has no record in data/sources/"]
    if doc["sheet"]["sha256"] not in json.loads(src.read_text())["locator"]:
        errs.append("the sheet's sha256 is not the one its source record pins")

    sc = doc["scale"]
    top, foot = sc["staff_px"]["top"], sc["staff_px"]["foot"]
    length = foot[1] - top[1] + 1
    if sc["staff_px"]["length"] != length:
        errs.append(f"staff length {sc['staff_px']['length']} px is not foot-top+1 = {length}")
    s = round(length / sc["staff_ft"], 4)
    if sc["px_per_ft"] != s:
        errs.append(f"px_per_ft {sc['px_per_ft']} is not {length} px / {sc['staff_ft']} ft = {s}")
    ox, oy = foot
    w, h = doc["sheet"]["size_px"]

    boxes: dict[str, list[int]] = {}

    def hold(label, node):
        box = node["sheet_px"]
        if not (0 <= box[0] < box[2] <= w and 0 <= box[1] < box[3] <= h):
            errs.append(f"{label}: box {box} is not a box on a {w} x {h} sheet")
            return
        boxes[label] = box
        if "fort_ft" in node and not same(node["fort_ft"], feet(box, s, ox, oy)):
            errs.append(f"{label}: fort_ft {node['fort_ft']} is not what {box} gives "
                        f"({feet(box, s, ox, oy)})")

    hold("parade", doc["parade"])
    numbers = []
    for row in doc["index"]:
        n, st = row["no"], row["status"]
        numbers.append(n)
        if st not in STATUSES:
            errs.append(f"index {n}: status {st!r} is not one of {sorted(STATUSES)}")
        if st == "located":
            if not row.get("parts") and not row.get("lines"):
                errs.append(f"index {n}: located, but carries neither parts nor lines")
            for p in row.get("parts", []):
                if "fort_ft" not in p:
                    errs.append(f"index {n} {p['label']}: inside the garrison, so it must carry feet")
                hold(p["label"], p)
        elif not row.get("why"):
            errs.append(f"index {n}: {st} must say why")
    if numbers != list(range(1, 35)):
        errs.append(f"the index is not the drafter's 1-34 in order: {numbers}")
    for n in (33, 34):
        row = next((r for r in doc["index"] if r["no"] == n), None)
        if row and row["status"] != "omitted_by_drafter":
            errs.append(f"index {n}: the index says it is 'Omited in their places', "
                        f"so it cannot be {row['status']}")

    # The cross-checks the file says hold, re-taken on its own numbers.
    claims = {c["check"]: c["result"] for c in doc["cross_checks"]}
    px, py = doc["parade"]["sheet_px"][0::2], doc["parade"]["sheet_px"][1::2]
    off = max(abs(sum(px) / 2 - ox), abs(sum(py) / 2 - oy)) / s
    if claims.get("the staff's foot is the parade's centre") == "holds" and off >= 1.0:
        errs.append(f"the staff's foot is {off:.2f} ft off the parade's centre; the file says it holds")
    nw, se = boxes.get("north-west blockhouse"), boxes.get("south-east blockhouse")
    if nw and se and claims.get("the two blockhouses agree") == "holds":
        d = max(abs((nw[2] - nw[0]) - (se[2] - se[0])), abs((nw[3] - nw[1]) - (se[3] - se[1]))) / s
        if d > 2.0:
            errs.append(f"the blockhouses differ by {d:.1f} ft; the file says they agree within 2")
    inner = {r["no"]: r for r in doc["index"]}[5]["lines"]
    iw = (inner["east"]["x_px"] - inner["west"]["x_px"]) / s
    ih = (inner["south"]["y_px"] - inner["north"]["y_px"]) / s
    if claims.get("the inner row encloses a square") == "holds" and abs(iw - ih) / max(iw, ih) > 0.02:
        errs.append(f"the inner row is {iw:.1f} x {ih:.1f} ft, not square within 2 percent")
    return errs


#: T-2049. Each first-fort record, the register part it is built from, and how its plan
#: reads the part: "ew" — width east-west, depth north-south; "ns" — width along a range
#: that runs north-south; "front" — an ELEVATION, so only the width is measured.
RECORDS = {
    "first_fort_dearborn_blockhouse_nw": ("north-west blockhouse", "ew"),
    "first_fort_dearborn_blockhouse_se": ("south-east blockhouse", "ew"),
    "first_fort_dearborn_commanding_officers_barracks": ("east range", "ns"),
    "first_fort_dearborn_officers_barracks": ("west range", "ns"),
    "first_fort_dearborn_soldiers_barracks_sw": ("south range, west of the gate", "ew"),
    "first_fort_dearborn_soldiers_barracks_se": ("south range, east of the gate", "ew"),
    "first_fort_dearborn_north_range": ("north range", "ew"),
    "first_fort_dearborn_magazine": ("magazine", "front"),
    "first_fort_dearborn_small_house_ne": ("small house, north-east", "front"),
    "first_fort_dearborn_small_house_sw": ("small house, south-west", "ew"),
    "first_fort_dearborn_parade": ("parade", "ew"),
    "first_fort_dearborn_flagstaff": ("flagstaff", None),
    "first_fort_dearborn_pickets_inner": (5, "ew"),
    "first_fort_dearborn_pickets_outer": (6, "ew"),
}
FIRST_FORT = ("1803-08-17", "1812-08-16")
FT_M = 0.3048
TOL_M = 0.02

#: T-2050. The seat: ONE origin and ONE bearing for the whole frame, so no record can be
#: moved against another. The staff's foot stands on the fort site at local E +1152,
#: N +221 (the Wright 1834 reading the second fort also hangs on: both forts stood on
#: "the same ground"), and the frame's north is grid north (the register's own inference
#: that the sheet's right is east). Each record's origin is its box's corner after its
#: FACING — degrees clockwise from the frame's north that its front faces, from what the
#: record says it faces — so a footprint anchored at its own (0, 0) lands on its box.
SEAT_LOCAL = (1152.0, 221.0)
SEAT_BEARING_DEG = 0.0
FACING = {
    "first_fort_dearborn_commanding_officers_barracks": 270,   # west, onto the parade
    "first_fort_dearborn_officers_barracks": 90,               # east, onto the parade
    "first_fort_dearborn_north_range": 180,                    # south, onto the parade
    "first_fort_dearborn_magazine": 180,                       # its arched front, south
    "first_fort_dearborn_small_house_ne": 180,                 # its front, south
}
#: which box edges (e index, n index into [e0, e1, n0, n1]) a facing anchors at
CORNER = {0: (0, 2), 90: (0, 3), 180: (1, 3), 270: (1, 2)}
SEAT_TOL_M = 0.01
BOX = re.compile(r"E ([+-][\d.]+)\.\.([+-][\d.]+) ft, N ([+-][\d.]+)\.\.([+-][\d.]+) ft")


def seat(box: list[float], facing: int, datum: dict) -> tuple[float, float, float]:
    """The UTM point and facade bearing the seat gives a record with this frame box."""
    ce, cn = box[CORNER[facing][0]] * FT_M, box[CORNER[facing][1]] * FT_M
    th = math.radians(SEAT_BEARING_DEG)
    e = SEAT_LOCAL[0] + ce * math.cos(th) + cn * math.sin(th)
    n = SEAT_LOCAL[1] - ce * math.sin(th) + cn * math.cos(th)
    return (datum["origin_utm_e"] + e, datum["origin_utm_n"] + n,
            (SEAT_BEARING_DEG + facing) % 360)


def two_forts() -> list[str]:
    """T-2050: the first fort and the second can never resolve into one scene.

    Held twice. Over ALL dates: every phase of every second-fort record opens after the
    first fort's range closes, so no date a scene could take resolves both. And over the
    committed scenes: each resolves all fourteen first-fort records or none of them, and
    the 1812 scene resolves all fourteen and no second-fort record.
    """
    errs: list[str] = []
    sdir = ROOT / "data" / "structures"
    first = {p.stem: json.loads(p.read_text()) for p in sdir.glob("first_fort_dearborn_*.json")}
    second = {p.stem: json.loads(p.read_text()) for p in sdir.glob("fort_dearborn_*.json")}
    for sid, st in sorted(second.items()):
        for ph in st.get("phases", []):
            frm = ph.get("documented_range", {}).get("from", "")
            if frm <= FIRST_FORT[1]:
                errs.append(f"{sid}/{ph.get('id')}: opens {frm}, inside the first fort's range "
                            f"(to {FIRST_FORT[1]}) — a date could draw both forts")

    def resolves(st: dict, d: str) -> bool:
        return any(ph["documented_range"]["from"] <= d <= ph["documented_range"]["to"]
                   for ph in st.get("phases", []) if "documented_range" in ph)

    for p in sorted((ROOT / "data" / "scenes").glob("*.json")):
        d = json.loads(p.read_text())["target_date"]
        f = sorted(s for s, st in first.items() if resolves(st, d))
        s2 = sorted(s for s, st in second.items() if resolves(st, d))
        if f and s2:
            errs.append(f"scene {p.stem} ({d}) resolves both forts: {f[0]} and {s2[0]}")
        if f and len(f) != len(first):
            errs.append(f"scene {p.stem} ({d}) resolves {len(f)} of the first fort's {len(first)} records")
        if p.stem == "1812" and len(f) != len(first):
            errs.append(f"the 1812 scene ({d}) does not resolve the first fort")
    return errs


def records(doc: dict) -> list[str]:
    """The first fort's structure records against the reading they are built from."""
    errs: list[str] = []
    s = doc["scale"]["px_per_ft"]
    ox, oy = doc["scale"]["staff_px"]["foot"]
    parts = {p["label"]: p["fort_ft"] for r in doc["index"] for p in r.get("parts", [])}
    parts["parade"] = doc["parade"]["fort_ft"]
    north = (parts["north range, west room"], parts["north range, east room"])
    parts["north range"] = {
        "e_ft": [north[0]["e_ft"][0], north[1]["e_ft"][1]], "n_ft": north[1]["n_ft"],
        "size_ft": [round(north[1]["e_ft"][1] - north[0]["e_ft"][0], 1), north[1]["size_ft"][1]]}
    for r in doc["index"]:
        if "lines" in r:
            L = r["lines"]
            x0, x1, y0, y1 = L["west"]["x_px"], L["east"]["x_px"], L["north"]["y_px"], L["south"]["y_px"]
            parts[r["no"]] = feet([x0, y0, x1, y1], s, ox, oy)
    have = {p.stem for p in (ROOT / "data" / "structures").glob("first_fort_dearborn_*.json")}
    for sid in sorted(have ^ set(RECORDS)):
        errs.append(f"{sid}: {'a first-fort record this reading does not map' if sid in have else 'mapped here, but no record'}")
    scenes = [json.loads(p.read_text())["target_date"] for p in (ROOT / "data" / "scenes").glob("*.json")]
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    for sid, (label, axis) in RECORDS.items():
        f = ROOT / "data" / "structures" / f"{sid}.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text())
        if len(st["phases"]) != 1:
            errs.append(f"{sid}: carries {len(st['phases'])} phases; the first fort has one")
            continue
        ph = st["phases"][0]
        rng = (ph["documented_range"]["from"], ph["documented_range"]["to"])
        if rng != FIRST_FORT:
            errs.append(f"{sid}: stands {rng[0]}..{rng[1]}, not the first fort's {FIRST_FORT[0]}..{FIRST_FORT[1]}")
        both = [d for d in scenes if rng[0] <= d <= rng[1]]
        if both and not (ROOT / "data" / "scenes" / "1812.json").exists():
            errs.append(f"{sid}: scene date {both[0]} resolves it, and no 1812 scene exists to own it")
        pos = ph["position"]
        m = BOX.search(pos.get("symbolic_location", ""))
        if not m:
            errs.append(f"{sid}: symbolic_location carries no fort-frame box to seat")
        elif pos.get("utm_e") is None or pos.get("utm_n") is None:
            errs.append(f"{sid}: not seated — the 1812 scene draws it, so it needs the seat's utm point")
        else:
            e, n, rot = seat([float(x) for x in m.groups()], FACING.get(sid, 0), datum)
            off = math.hypot(pos["utm_e"] - e, pos["utm_n"] - n)
            if off > SEAT_TOL_M or float(pos.get("rotation_deg") or 0.0) != rot:
                errs.append(f"{sid}: stands at {pos['utm_e']}, {pos['utm_n']} turned "
                            f"{pos.get('rotation_deg')}, not where the seat puts its box "
                            f"({e:.2f}, {n:.2f} turned {rot}): {off:.2f} m off")
        if axis is None:
            continue
        part = parts[label]
        e_ft, n_ft = part["e_ft"], part["n_ft"]
        loc = ph["position"].get("symbolic_location", "")
        want_e = f"E {e_ft[0]:+.1f}..{e_ft[1]:+.1f} ft"
        if want_e not in loc:
            errs.append(f"{sid}: symbolic_location does not carry the register's {want_e}")
        if axis != "front" and f"N {n_ft[0]:+.1f}..{n_ft[1]:+.1f} ft" not in loc:
            errs.append(f"{sid}: symbolic_location does not carry the register's N box")
        poly = ph["footprint"]["polygon"]
        w = max(p[0] for p in poly) - min(p[0] for p in poly)
        d = max(p[1] for p in poly) - min(p[1] for p in poly)
        ew, ns = (part["size_ft"][0] * FT_M, part["size_ft"][1] * FT_M)
        want = {"ew": (ew, ns), "ns": (ns, ew), "front": (ew, None)}[axis]
        if abs(w - want[0]) > TOL_M or (want[1] is not None and abs(d - want[1]) > TOL_M):
            errs.append(f"{sid}: footprint {w:.2f} x {d:.2f} m is not the register's "
                        f"{label!r} at {want[0]:.2f}" + (f" x {want[1]:.2f} m" if want[1] else " m wide"))
    return errs


def fetch(doc: dict) -> bytes:
    cache = Path("/tmp") / "chicago4d-whistler-1808.png"
    if not cache.exists():
        with urllib.request.urlopen(doc["sheet"]["url"], timeout=60) as r:
            cache.write_bytes(r.read())
    data = cache.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != doc["sheet"]["sha256"]:
        raise SystemExit(f"the working copy's sha256 is {got}, not the pinned "
                         f"{doc['sheet']['sha256']} — the sheet has moved; re-read it")
    return data


def remeasure(doc: dict) -> list[str]:
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(fetch(doc))).convert("L")
    w, h = im.size
    px = im.load()
    dark_rows = [y for y in range(h) if min(px[x, y] for x in STAFF_COLS) < DARK]
    runs, start, prev = [], None, None
    for y in dark_rows:
        if start is None or y - prev > MAX_GAP:
            if start is not None:
                runs.append((start, prev))
            start = y
        prev = y
    if start is not None:
        runs.append((start, prev))
    top, foot = max(runs, key=lambda r: r[1] - r[0])
    want = doc["scale"]["staff_px"]
    print(f"   staff: top y {top}, foot y {foot}, {foot - top + 1} px "
          f"= {(foot - top + 1) / doc['scale']['staff_ft']:.4f} px/ft")
    errs = []
    if [top, foot] != [want["top"][1], want["foot"][1]]:
        errs.append(f"the staff measures y {top}-{foot}; the file says "
                    f"{want['top'][1]}-{want['foot'][1]}")
    return errs


def main() -> int:
    doc = json.loads(TRACE.read_text())
    errs = check(doc) + records(doc) + two_forts()
    if "--remeasure" in sys.argv:
        errs += remeasure(doc)
    if errs:
        for e in errs:
            print(f"FAIL: {e}")
        return 1
    rows = doc["index"]
    count = {st: sum(1 for r in rows if r["status"] == st) for st in sorted(STATUSES)}
    print(f"OK: Whistler 1808 at {doc['scale']['px_per_ft']} px/ft off the 75 ft staff; "
          f"34 index numbers — " + ", ".join(f"{v} {k}" for k, v in count.items())
          + f"; {len(RECORDS)} first-fort records built from it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
