#!/usr/bin/env python3
"""T-3687 — the Great Fire's map and clock, data/fire/1871.json.

The file is authored by hand in the accounts' own terms: street corners and places
by their modern latitude and longitude, river reaches by the scene's own river
lines, and an hour for each place with its source. This tool carries the corners
into the scene's local east/north metres and writes them beside what they came
from, so the renderer (renderers/web/js/city-fire.js) reads metres and never
re-derives a map.

  python3 tools/fire_1871.py --write   derive the local outlines, controls and areas
  python3 tools/fire_1871.py --check   the file agrees with its derivation and its sources
  python3 tools/fire_1871.py --self-test

The conversion is an affine fit, latitude/longitude to local metres, through the
modern OpenStreetMap controls the 1871 city's own map alignment rests on
(data/context/1871/plan.json); over the burnt district its residual is a few metres,
far inside the accounts' own precision ("about twelve o'clock", "the line of
Congress Street").

T-3751 (the owner, 2026-11-26: "The jaunt stops at the Field Building, but the building does
not burn"; "Ensure the visual state of the environment corresponds to the chronology and events
described in the narration"): a named structure may carry `burning_by`, the hour an account
or the jaunt's own evidence has it alight, which the renderer keeps to exactly (no jitter, its
rise begun so that it is burning at that hour). And `goods` are the household goods the
fleeing families heaped on open ground (Washington Square, the old cemetery): this tool lays
each heap on its open ground (`local_heaps`, clear of the ground's own graves and fences, the
jaunt's stand and its people), and the renderer burns them by their place's hour or by the
goods' own window.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRE = ROOT / "data/fire/1871.json"
PLAN = ROOT / "data/context/1871/plan.json"
RIVERS = ROOT / "data/terrain/epochs/e1871_prefire/river.geojson"
SOURCES = ROOT / "data/sources"
CONTEXT = ROOT / "data/context/1871.json"
SIDECARS = ROOT / "data/sidecars/1871"
JAUNTS = ROOT / "data/jaunts"
SCENE = ROOT / "data/scenes/1871.json"
FATES = {"walls_stand", "roof_burns", "collapses", "survives"}
GRADES = {"attested", "inferred", "reconstructed"}
ACRE_M2 = 4046.8564224


def fit_affine(plan: dict):
    """Least squares local (e, n) = A · (lon, lat, 1) through the plan's modern controls."""
    rows = []
    for c in plan["map_control"]["controls"]:
        m = c.get("modern_control") or {}
        if all(k in m for k in ("lat", "lon", "local_e", "local_n")):
            rows.append((m["lon"], m["lat"], m["local_e"], m["local_n"]))
    if len(rows) < 6:
        raise SystemExit("fire_1871: too few modern controls in data/context/1871/plan.json")
    lon0 = sum(r[0] for r in rows) / len(rows)
    lat0 = sum(r[1] for r in rows) / len(rows)

    def solve(target: int):
        # normal equations for [a, b, c] in v = a*x + b*y + c, x/y centred
        sxx = sxy = sx = syy = sy = n = 0.0
        sxv = syv = sv = 0.0
        for lon, lat, e, nn in rows:
            x, y, v = lon - lon0, lat - lat0, (e, nn)[target]
            sxx += x * x; sxy += x * y; sx += x; syy += y * y; sy += y; n += 1
            sxv += x * v; syv += y * v; sv += v
        m = [[sxx, sxy, sx, sxv], [sxy, syy, sy, syv], [sx, sy, n, sv]]
        for i in range(3):  # Gauss-Jordan
            p = max(range(i, 3), key=lambda r: abs(m[r][i]))
            m[i], m[p] = m[p], m[i]
            for r in range(3):
                if r != i:
                    f = m[r][i] / m[i][i]
                    m[r] = [a - f * b for a, b in zip(m[r], m[i])]
        return [m[i][3] / m[i][i] for i in range(3)]

    ce, cn = solve(0), solve(1)

    def to_local(lat: float, lon: float):
        x, y = lon - lon0, lat - lat0
        return (ce[0] * x + ce[1] * y + ce[2], cn[0] * x + cn[1] * y + cn[2])

    res = [math.hypot(*(a - b for a, b in zip(to_local(lat, lon), (e, n)))) for lon, lat, e, n in rows]
    rms = math.sqrt(sum(r * r for r in res) / len(res))
    return to_local, rms


def river_lines() -> dict:
    doc = json.loads(RIVERS.read_text())
    return {f["properties"]["id"]: f["geometry"]["coordinates"] for f in doc["features"]}


def slice_line(line, axis: int, a: float, b: float):
    """The reach of `line` between coordinate `a` and `b` on `axis` (0 e, 1 n), ordered a -> b.
    The line must cross each value once; the reach runs along the line between the two crossings."""
    def crossing(v):
        for i in range(len(line) - 1):
            p, q = line[i], line[i + 1]
            lo, hi = sorted((p[axis], q[axis]))
            if lo <= v <= hi and p[axis] != q[axis]:
                t = (v - p[axis]) / (q[axis] - p[axis])
                return i + t, [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]
        # Past the line's end: its nearer end stands in.
        ends = [(0.0, line[0]), (len(line) - 1.0, line[-1])]
        return min(ends, key=lambda x: abs(x[1][axis] - v))
    (ia, pa), (ib, pb) = crossing(a), crossing(b)
    pts = [pa]
    if ia < ib:
        pts += [line[k] for k in range(math.floor(ia) + 1, math.ceil(ib)) if ia < k < ib]
    else:
        pts += [line[k] for k in range(math.ceil(ia) - 1, math.floor(ib), -1) if ib < k < ia]
    pts.append(pb)
    return [[round(x, 1), round(y, 1)] for x, y in pts]


def polygon_area(pts) -> float:
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2


def inside(e: float, n: float, poly) -> bool:
    res = False
    j = len(poly) - 1
    for i in range(len(poly)):
        a, b = poly[i], poly[j]
        if (a[1] > n) != (b[1] > n) and e < (b[0] - a[0]) * (n - a[1]) / (b[1] - a[1]) + a[0]:
            res = not res
        j = i
    return res


def footprint_world(side: dict):
    """A sidecar's footprint polygon and composition boxes in scene metres (walker.js footprintToWorld)."""
    pl = side["placement"]
    th = math.radians(pl.get("rotation_deg") or 0)
    c, s_ = math.cos(th), math.sin(th)
    e0, n0 = pl.get("local_e") or 0, pl.get("local_n") or 0

    def to_world(u, v):
        return [e0 + u * c + v * s_, n0 - u * s_ + v * c]
    return to_world, side["footprint"]["polygon"]


def lay_heaps(goods: dict) -> list:
    """Heaps of goods on a structure's open ground, deterministic from the goods' seed: inside the
    footprint less `margin_m`, clear of its own blocks (graves, fence, gateways) by `clear_m`, of
    each other by `apart_m`, of the jaunt stands named in `clear_of` and of the stop's people by
    `stand_r_m`. Each heap is [e, n, bearing_deg, seed]."""
    side = json.loads((SIDECARS / f"{goods['within']}.json").read_text())
    to_world, poly = footprint_world(side)
    us, vs = [p[0] for p in poly], [p[1] for p in poly]
    margin, clear, apart = goods.get("margin_m", 2.5), goods.get("clear_m", 1.2), goods.get("apart_m", 4.0)
    blocks = []
    form = json.loads((ROOT / f"data/structures/{goods['within']}.json").read_text())["phases"][-1].get("form", {})
    for b in ((form.get("composition") or {}).get("value") or {}).get("blocks", []):
        u0, v0, u1, v1 = b["box"]
        blocks.append((min(u0, u1) - clear, min(v0, v1) - clear, max(u0, u1) + clear, max(v0, v1) + clear))
    keep_out = []
    scene = json.loads(SCENE.read_text())
    anchors = {a["id"]: a for a in scene["anchors"]}
    r_stand = goods.get("stand_r_m", 4.5)
    for aid in goods.get("clear_of", []):
        a = anchors[aid]
        keep_out.append((a["local_e"], a["local_n"], r_stand))
        for path in sorted(JAUNTS.glob("the-great-fire*.json")):
            for stop in json.loads(path.read_text())["stops"]:
                if stop["destination"].get("id") != aid:
                    continue
                for c in (stop.get("stage") or {}).get("cast", []):
                    keep_out.append((c["at"][0], c["at"][1], 1.6))
                    for beat in c.get("beats", []):
                        for q in beat.get("walk", []):
                            keep_out.append((q[0], q[1], 1.4))
    rng = random.Random(goods["seed"])
    heaps, tries = [], 0
    while len(heaps) < goods["heaps"] and tries < 20000:
        tries += 1
        u = rng.uniform(min(us) + margin, max(us) - margin)
        v = rng.uniform(min(vs) + margin, max(vs) - margin)
        if any(b[0] <= u <= b[2] and b[1] <= v <= b[3] for b in blocks):
            continue
        e, n = to_world(u, v)
        if any(math.hypot(e - k[0], n - k[1]) < k[2] for k in keep_out):
            continue
        if any(math.hypot(e - h[0], n - h[1]) < apart for h in heaps):
            continue
        heaps.append([round(e, 2), round(n, 2), round(rng.uniform(0, 360), 1), rng.randrange(1, 10 ** 6)])
    if len(heaps) < goods["heaps"]:
        raise SystemExit(f"fire_1871: goods {goods['id']}: only {len(heaps)} of {goods['heaps']} heaps fit on {goods['within']}")
    return heaps


def ground_of(goods: dict) -> list:
    """T-3751: the open ground a `scorch` goods entry burns over (the fire ran through the square's
    grass between the heaps): its footprint's corners in local metres, which the renderer covers with
    ragged scorch from the place's own hour."""
    side = json.loads((SIDECARS / f"{goods['within']}.json").read_text())
    to_world, poly = footprint_world(side)
    return [[round(c, 2) for c in to_world(u, v)] for u, v in poly]


def derive(doc: dict) -> dict:
    """The derived fields, from the authored ones; never reads a derived field."""
    to_local, rms = fit_affine(json.loads(PLAN.read_text()))
    rivers = river_lines()
    out = {"rms_m": round(rms, 2), "zones": {}, "controls": {}, "spared": {}}
    for z in doc["zones"]:
        poly = []
        for step in z["outline"]:
            if "river" in step:
                line = rivers[step["river"]]
                axis, a, b = (1, step["from_n"], step["to_n"]) if "from_n" in step else (0, step["from_e"], step["to_e"])
                poly += slice_line(line, axis, a, b)
            elif "local" in step:
                poly.append([float(step["local"][0]), float(step["local"][1])])
            else:
                e, n = to_local(step["lat"], step["lon"])
                poly.append([round(e, 1), round(n, 1)])
        # A closed ring, consecutive duplicates dropped.
        ring = [p for i, p in enumerate(poly) if i == 0 or p != poly[i - 1]]
        if ring[0] == ring[-1]:
            ring.pop()
        out["zones"][z["id"]] = {"local": ring, "acres": round(polygon_area(ring) / ACRE_M2)}
    # T-3689: a place built on the 1871 plan's own streets (a named structure the scene
    # stands) carries `plan_local`, the scene's metres, and that is where the fire is;
    # its lat/lon stays the modern pointer it was read from, and `plan_note` says why
    # the two differ (the plan is a tracing of Mitchell's 1870 map, not the modern grid).
    for c in doc["controls"]:
        e, n = c["plan_local"] if "plan_local" in c else to_local(c["lat"], c["lon"])
        out["controls"][c["id"]] = [round(e, 1), round(n, 1)]
    for s in doc.get("spared", []):
        e, n = s["plan_local"] if "plan_local" in s else to_local(s["lat"], s["lon"])
        out["spared"][s["id"]] = [round(e, 1), round(n, 1)]
    out["goods"] = {g["id"]: lay_heaps(g) for g in doc.get("goods", [])}
    out["ground"] = {g["id"]: ground_of(g) for g in doc.get("goods", []) if g.get("scorch")}
    return out


def apply(doc: dict, d: dict) -> dict:
    doc["conversion"]["rms_m"] = d["rms_m"]
    for z in doc["zones"]:
        z["acres"] = d["zones"][z["id"]]["acres"]
        z["local"] = d["zones"][z["id"]]["local"]
    for c in doc["controls"]:
        c["local"] = d["controls"][c["id"]]
    for s in doc.get("spared", []):
        s["local"] = d["spared"][s["id"]]
    for g in doc.get("goods", []):
        g["local_heaps"] = d["goods"][g["id"]]
        if g["id"] in d["ground"]:
            g["local_ground"] = d["ground"][g["id"]]
        else:
            g.pop("local_ground", None)
    return doc


def stamp(t: str) -> datetime:
    return datetime.strptime(t, "%Y-%m-%dT%H:%M")


def problems(doc: dict) -> list[str]:
    bad = []
    known = {p.stem for p in SOURCES.glob("*.json")}

    def cite(where, ids):
        if not ids:
            bad.append(f"{where}: no sources")
        for s in ids or []:
            if s not in known:
                bad.append(f"{where}: source {s} does not resolve in data/sources/")
    cite("file", doc.get("sources"))
    cite("wind", doc["wind"].get("sources"))
    cite("rain", doc["rain"].get("sources"))
    start, end = stamp(doc["start"]), stamp(doc["end"])
    d = derive(doc)
    if doc["conversion"].get("rms_m") != d["rms_m"]:
        bad.append("conversion.rms_m is stale: run tools/fire_1871.py --write")
    for z in doc["zones"]:
        cite(f"zone {z['id']}", z.get("sources"))
        if z.get("grade") not in GRADES:
            bad.append(f"zone {z['id']}: grade {z.get('grade')}")
        if z.get("local") != d["zones"][z["id"]]["local"] or z.get("acres") != d["zones"][z["id"]]["acres"]:
            bad.append(f"zone {z['id']}: local outline is stale: run tools/fire_1871.py --write")
        if len(d["zones"][z["id"]]["local"]) < 3:
            bad.append(f"zone {z['id']}: fewer than three corners")
    ids = set()
    for c in doc["controls"]:
        if c["id"] in ids:
            bad.append(f"control {c['id']}: duplicate id")
        ids.add(c["id"])
        cite(f"control {c['id']}", c.get("sources"))
        if c.get("grade") not in GRADES:
            bad.append(f"control {c['id']}: grade {c.get('grade')}")
        if not c.get("locator"):
            bad.append(f"control {c['id']}: no locator")
        if c.get("grade") == "inferred" and not (c.get("note") or c.get("locator")):
            bad.append(f"control {c['id']}: inferred without reasoning")
        try:
            t = stamp(c["t"])
            if not (start <= t <= end):
                bad.append(f"control {c['id']}: {c['t']} outside the fire's {doc['start']}..{doc['end']}")
        except (KeyError, ValueError):
            bad.append(f"control {c['id']}: hour is not YYYY-MM-DDTHH:MM")
        if "plan_local" in c and not c.get("plan_note"):
            bad.append(f"control {c['id']}: plan_local without a plan_note saying why")
        if c.get("local") != d["controls"][c["id"]]:
            bad.append(f"control {c['id']}: local position is stale: run tools/fire_1871.py --write")
        e, n = d["controls"][c["id"]]
        if not any(inside(e, n, z["local"]) for z in d["zones"].values()):
            bad.append(f"control {c['id']}: ({e}, {n}) is outside every burnt zone")
    for s in doc.get("spared", []):
        cite(f"spared {s['id']}", s.get("sources"))
        if s.get("local") != d["spared"][s["id"]]:
            bad.append(f"spared {s['id']}: local position is stale: run tools/fire_1871.py --write")
    for sid, rec in doc.get("structures", {}).items():
        if rec.get("fate") not in FATES:
            bad.append(f"structure {sid}: fate {rec.get('fate')}")
        pin = rec.get("burning_by")
        if pin is not None:
            cite(f"structure {sid} burning_by", pin.get("sources"))
            if pin.get("grade") not in GRADES:
                bad.append(f"structure {sid}: burning_by grade {pin.get('grade')}")
            if not (pin.get("locator") or pin.get("note")):
                bad.append(f"structure {sid}: burning_by without a locator or reasoning")
            if rec.get("fate") == "survives" or sid in doc.get("survivors", []):
                bad.append(f"structure {sid}: a survivor cannot be burning by an hour")
            try:
                if not (start <= stamp(pin["t"]) <= end):
                    bad.append(f"structure {sid}: burning_by {pin['t']} outside the fire's {doc['start']}..{doc['end']}")
            except (KeyError, ValueError):
                bad.append(f"structure {sid}: burning_by hour is not YYYY-MM-DDTHH:MM")
    gids = set()
    for g in doc.get("goods", []):
        if g["id"] in gids:
            bad.append(f"goods {g['id']}: duplicate id")
        gids.add(g["id"])
        cite(f"goods {g['id']}", g.get("sources"))
        if g.get("grade") not in GRADES:
            bad.append(f"goods {g['id']}: grade {g.get('grade')}")
        if not g.get("locator") or not g.get("note"):
            bad.append(f"goods {g['id']}: needs a locator for what is attested and a note for what is reconstructed")
        if not (SIDECARS / f"{g.get('within')}.json").exists():
            bad.append(f"goods {g['id']}: no 1871 sidecar for {g.get('within')}")
            continue
        if g.get("local_heaps") != d["goods"].get(g["id"]):
            bad.append(f"goods {g['id']}: local heaps are stale: run tools/fire_1871.py --write")
        if g.get("local_ground") != d["ground"].get(g["id"]):
            bad.append(f"goods {g['id']}: local ground is stale: run tools/fire_1871.py --write")
        try:
            if "appear" in g and not (start <= stamp(g["appear"]) <= end):
                bad.append(f"goods {g['id']}: appear {g['appear']} outside the fire")
        except ValueError:
            bad.append(f"goods {g['id']}: appear is not YYYY-MM-DDTHH:MM")
        if g.get("catch") not in (None, "place") or (g.get("catch") is None and g.get("window") is None):
            bad.append(f"goods {g['id']}: burns by catch 'place' or by its own window")
        w = g.get("window")
        if w is not None:
            try:
                if not (start <= stamp(w["from"]) <= stamp(w["to"]) <= end) or not (0 < w.get("share", 0) <= 1):
                    bad.append(f"goods {g['id']}: window {w} is not inside the fire with a share in (0, 1]")
            except (KeyError, ValueError):
                bad.append(f"goods {g['id']}: window hours are not YYYY-MM-DDTHH:MM")
    for z in doc["zones"]:
        if z.get("burnt_at"):
            try:
                if stamp(z["burnt_at"]) >= start:
                    bad.append(f"zone {z['id']}: burnt_at must be before the fire starts")
            except ValueError:
                bad.append(f"zone {z['id']}: burnt_at is not YYYY-MM-DDTHH:MM")
    try:
        if not (start <= stamp(doc["rain"]["t"]) <= end):
            bad.append("rain: outside the fire")
    except ValueError:
        bad.append("rain: hour is not YYYY-MM-DDTHH:MM")
    return bad


def report(doc: dict) -> None:
    """What the outline holds of the context city, and its acres against the Board's."""
    ctx = json.loads(CONTEXT.read_text())
    zones = {z["id"]: z for z in doc["zones"]}
    counts = {k: 0 for k in zones}
    for b in ctx["buildings"]:
        e, n = (b["e"], b["n"]) if isinstance(b, dict) else (b[1], b[2])
        for k, z in zones.items():
            if inside(e, n, z["local"]):
                counts[k] += 1
                break
    for k, z in zones.items():
        rep = z.get("reported_acres")
        print(f"  {k:16} {z['acres']:5d} acres{f' (the Board: about {rep})' if rep else ''}; "
              f"{counts[k]} context buildings")


def self_test() -> int:
    sq = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert inside(5, 5, sq) and not inside(15, 5, sq)
    assert abs(polygon_area(sq) - 100) < 1e-9
    line = [[0, 0], [0, 10], [5, 20]]
    assert slice_line(line, 1, 5, 15) == [[0, 5], [0, 10], [2.5, 15]]
    assert slice_line(line, 1, 15, 5) == [[2.5, 15], [0, 10], [0, 5]]
    to_local, rms = fit_affine(json.loads(PLAN.read_text()))
    e, n = to_local(41.8820455, -87.6278089)  # State and Madison, control M1
    assert math.hypot(e - 837.63, n + 525.27) < 25, (e, n)
    assert rms < 25, rms
    doc = json.loads(FIRE.read_text())
    broken = json.loads(json.dumps(doc))
    broken["controls"][0]["sources"] = ["no_such_source_3687"]
    broken["controls"][1]["t"] = "1871-10-12T09:00"
    broken["zones"][0]["local"] = [[0, 0], [1, 0], [0, 1]]
    broken["structures"]["field_leiter_1871"]["burning_by"]["t"] = "1871-10-11T08:00"
    broken["structures"]["chicago_water_tower_1871"] = {"fate": "survives", "burning_by": {"t": "1871-10-09T03:00", "grade": "inferred", "sources": ["andreas_1885_v2"], "note": "x"}}
    broken["goods"][0]["local_heaps"] = broken["goods"][0]["local_heaps"][1:]
    broken["goods"][0]["local_ground"] = broken["goods"][0]["local_ground"][1:]
    found = problems(broken)
    assert any("field_leiter_1871: burning_by 1871-10-11T08:00 outside" in p for p in found), found
    assert any("chicago_water_tower_1871: a survivor" in p for p in found), found
    assert any("heaps are stale" in p for p in found), found
    assert any("ground is stale" in p for p in found), found
    assert any("no_such_source_3687" in p for p in found), found
    assert any("outside the fire" in p for p in found), found
    assert any("stale" in p for p in found), found
    print("FIRE 1871 SELF-TEST PASS — corners carried by the controls' fit, river reaches sliced both ways, "
          "unresolved sources, hours outside the fire and stale outlines refused; a landmark's burning_by "
          "outside the fire or on a survivor, and stale heaps of goods, refused")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    doc = json.loads(FIRE.read_text())
    if a.write:
        doc = apply(doc, derive(doc))
        FIRE.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {FIRE.relative_to(ROOT)} (fit rms {doc['conversion']['rms_m']} m)")
        report(doc)
        return 0
    bad = problems(doc)
    for p in bad:
        print(f"FAIL {p}")
    if bad:
        return 1
    print(f"FIRE 1871 PASS — {len(doc['zones'])} zones, {len(doc['controls'])} timed places, "
          f"{len(doc.get('spared', []))} spared, every source resolves and every outline is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
