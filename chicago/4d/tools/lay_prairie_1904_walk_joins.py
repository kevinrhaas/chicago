#!/usr/bin/env python3
"""Join every 1904 house walk to the public walk it was laid to reach (T-3274).

    python3 tools/lay_prairie_1904_walk_joins.py              # write data/street_section/walk_joins_1904.json
    python3 tools/lay_prairie_1904_walk_joins.py --check      # the committed file is what this writes
    python3 tools/lay_prairie_1904_walk_joins.py --report     # every walk end, how far it stood off, joined or not
    python3 tools/lay_prairie_1904_walk_joins.py --self-test  # plants each case and proves it is handled

THE FAULT. The owner, 2026-10-31, of the Pullman glasshouse ground at 18th Street and Calumet
Avenue: "there is a gap there between sidewalk and walkway. I see that all over the place ...
make the walk connect correctly based on the photos". Every period picture of the district that
shows a house walk at the street (Glessner, HABS c. 1923; Pullman, Inland 1894 and Lowe c. 1897;
the 1700 and 1800 blocks' photographs) shows it running on until it meets the public walk. In
the app it stopped on a strip of grass, for one reason: the city code (1905, sec. 2062: "All
walks to be laid on a line one foot from and parallel with the lot line") puts the public walk a
foot outside the lot line (data/street_grid/1904.json's `margin` band, T-3233 the lot's own
grass), and the yards' builders (K14 k14_yard.py, K16 k16_yard.py / k16_timber.py, K13's
`grounds`) lay each walk to the lot line, `front_yard_m` before the street front, and stop. Where
a house's traced front and its recorded front yard do not quite meet the traced street line, the
strip was wider still (1812 Prairie's 1.6 m). Measured on dev 2026-10-31: 39 of 48 front walks,
all 11 side service walks, 1729's two drives and the Pullman glasshouse ground's walk and drive
stood 0.18-1.6 m short; nine front walks already met.

THE FIX, here and not in 48 GLBs. Each walk's street end is read off what was BUILT (the
component instances the K01/K16 GLBs carry in their node extras, as tools/check_house_walks.py
reads them; a K13 record's `grounds` rows), carried into the scene by its 1904 sidecar
placement, and measured to the nearest public walk band of the street grid. Where it stands off
by more than MEET_M and no more than REACH_M, a join is laid: a paved strip the walk's own width,
from its end (tucked TUCK_M back under it) square across to the public walk's inner edge (TUCK_M
into it). The renderer (street-grid.js) draws each join as a piece of the face's walk band, in
its material and at its level, so the house walk and the public walk read as one paved way.
What paved that foot is not recorded anywhere read; the join is reconstructed
(docs/LIBERTIES.md L-prairie-walk-joins-3274), and the fact that the walks met is what the
pictures attest. An end farther than REACH_M from any public walk is not a street end (a
service walk's rear, a drive's door end) and is left alone.

A walk moved or rebuilt by its own lane leaves this file stale: `--check` (tools/check.sh) then
fails and names the house; rerun this tool.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_house_walks as H  # noqa: E402

GRID = ROOT / "data" / "street_grid" / "1904.json"
OUT = ROOT / "data" / "street_section" / "walk_joins_1904.json"
GLTF = ROOT / "assets" / "gltf"
STRUCTURES = ROOT / "data" / "structures"
MEET_M = 0.02      # an end this close to the public walk already meets it
REACH_M = 2.5      # an end farther than this from every public walk is not a street end
TUCK_M = 0.04      # a join runs this far under the house walk's end and into the public walk
SIDE_JOINT_M = 0.01  # K14's JOINT_M: a gated service walk's street piece stands this clear of its south pier
LIBERTY = "L-prairie-walk-joins-3274"


# -- geometry ------------------------------------------------------------------------------

def _closest_on_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return (a[0] + t * dx, a[1] + t * dy)


def nearest_walk(p, walks):
    """(distance, nearest point, face id) from p to the public walk bands; 0 inside one."""
    best = (math.inf, None, None)
    for fid, poly in walks:
        if H._inside(p, poly):
            return (0.0, p, fid)
        for i in range(len(poly)):
            q = _closest_on_seg(p, poly[i - 1], poly[i])
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            if d < best[0]:
                best = (d, q, fid)
    return best


def join_for(end, walks):
    """The join for one walk end {id, house, kind, corners: [P0, P1] (world e/n)}: a dict with
    the measured gap, and the paved polygon where one is laid."""
    hits = [nearest_walk(p, walks) for p in end["corners"]]
    gap = max(h[0] for h in hits)
    rec = {"id": end["id"], "house": end["house"], "kind": end["kind"], "gap_m": round(gap, 3),
           "face": hits[0][2] if hits[0][2] == hits[1][2] else min(hits, key=lambda h: h[0])[2]}
    if gap <= MEET_M:
        rec["state"] = "meets"
        return rec
    if gap > REACH_M:
        rec["state"] = "not a street end"
        return rec
    # square across: both corners step along the one direction from the end's middle to the walk
    (p0, p1), (q0, q1) = end["corners"], (hits[0][1], hits[1][1])
    dx = ((q0[0] - p0[0]) + (q1[0] - p1[0])) / 2
    dy = ((q0[1] - p0[1]) + (q1[1] - p1[1])) / 2
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    # each corner's own reach along that direction, to the band's edge
    def reach(p, q):
        return max(0.0, (q[0] - p[0]) * ux + (q[1] - p[1]) * uy)
    r0, r1 = reach(p0, q0), reach(p1, q1)
    a0 = (p0[0] - ux * TUCK_M, p0[1] - uy * TUCK_M)
    a1 = (p1[0] - ux * TUCK_M, p1[1] - uy * TUCK_M)
    b1 = (p1[0] + ux * (r1 + TUCK_M), p1[1] + uy * (r1 + TUCK_M))
    b0 = (p0[0] + ux * (r0 + TUCK_M), p0[1] + uy * (r0 + TUCK_M))
    rec["state"] = "joined"
    rec["width_m"] = round(math.hypot(p1[0] - p0[0], p1[1] - p0[1]), 3)
    rec["polygon_local_m"] = [[round(x, 3), round(y, 3)] for x, y in (a0, a1, b1, b0)]
    return rec


# -- reading what was built ---------------------------------------------------------------

def _ends_of_glb(sid, extras, world):
    """The street ends a K01/K16 GLB's yard instances name, each as two corners in the house's
    frame (u, s), carried into the world by `world`."""
    inst = list(H.instances(extras))
    out = []
    side_gates = [(sk["opening"][0], -sk["opening"][2], prm["clear_m"]) for cid, _f, prm, sk in inst
                  if cid == "k11.gate.walk_gate_on_piers"]
    for cid, _fam, prm, sk in inst:
        if cid == "k14.yard.front_walk":
            legs = prm.get("legs_m")
            if legs:
                u0, u1, s0, s1 = max(legs, key=lambda l: l[1])[:4]
            else:
                u1, s, w = sk["public_walk"][0], -sk["public_walk"][2], prm["width_m"]
                s0, s1 = s - w / 2, s + w / 2
            out.append(("front_walk", [(u1, s0), (u1, s1)]))
        elif cid == "k14.yard.service_walk":
            legs = prm.get("legs_m")
            if legs:
                u0, u1, s0, s1 = max(legs, key=lambda l: l[1])[:4]
            else:
                # K14 (k14_yard.py): it runs from `rear_end` `length_m` out to the lot line; behind
                # a gated front its street piece is the side gate's clear width (sa + JOINT .. sb),
                # behind an open front the passage's whole width
                u1 = sk["rear_end"][0] + prm["length_m"]
                s = -sk["gate"][2]
                g = next((c for gx, gs, c in side_gates if abs(gs - s) < 0.3 and gx < u1 + 0.05), None)
                if g is not None:
                    s0, s1 = s - g / 2 + SIDE_JOINT_M, s + g / 2
                else:
                    s0, s1 = s - prm["width_m"] / 2, s + prm["width_m"] / 2
            out.append(("service_walk", [(u1, s0), (u1, s1)]))
        elif cid == "k14.yard.drive":
            # a drive names its two ends' centres; its street end's edge runs square to it, so
            # it is turned onto the public walk below (`_square_to_walk`)
            w = prm["width_m"]
            for key in ("from", "to"):
                u, s = sk[key][0], -sk[key][2]
                out.append(("drive", [(u, s), w]))
    ends = []
    for k, (kind, geo) in enumerate(out):
        if kind == "drive":
            ends.append({"kind": kind, "centre": world(*geo[0]), "width": geo[1], "n": k})
        else:
            ends.append({"kind": kind, "corners": [world(*geo[0]), world(*geo[1])], "n": k})
    return ends


def _path_ends(srf):
    """A gravel surface laid along a curve (T-3273's `path_m` [[u, v, lift], ...] centreline,
    `width_m` [start, end], `samples` steps a span): its two ends' edges, in (u, v), exactly as
    k13_conservatories._gravel_path draws them -- the Catmull-Rom curve through the points with
    its ends doubled, each end's edge square to the chord to its neighbouring sample, the start
    `width_m[0]` wide and the end `width_m[1]`. The worn `edge_m` margin is turf, not walk, and
    is left out."""
    pts = [tuple(map(float, q[:2])) for q in srf["path_m"]]
    n = srf.get("samples", 6)
    w0, w1 = srf["width_m"] if isinstance(srf["width_m"], list) else (srf["width_m"],) * 2
    ext = [pts[0]] + pts + [pts[-1]]

    def at(i, t):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        return tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                            + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t * t * t) for j in range(2))
    last = len(ext) - 3
    # the first two samples and the last two, as the generator's own loop lays them
    first, second = at(1, 0.0), (at(1, 1 / n) if n > 1 else at(min(2, last), 0.0))
    end, before = at(last, 1.0), at(last, (n - 1) / n)

    def edge(c, a, b, w):
        du, dv = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(du, dv) or 1.0
        nu, nv = -dv / ln, du / ln
        h = w / 2
        return [(c[0] - nu * h, c[1] - nv * h), (c[0] + nu * h, c[1] + nv * h)]
    return edge(first, first, second, w0), edge(end, before, end, w1)


def _ends_of_grounds(record, world):
    """A K13 record's `grounds` gravel (T-3164, the Pullman glasshouse ground): each surface's
    first and last rows [u, v_a, v_b, lift] are its two ends, or, for one laid along a curve
    (`path_m`, T-3273), the edges its first and last sections are drawn on."""
    out = []
    for ph in record.get("phases", []):
        if not H._covers(ph):
            continue
        v = ((ph.get("form") or {}).get("conservatory") or {}).get("value") or {}
        gr = (v.get("pavilion") or {}).get("grounds") or {}
        for srf in gr.get("gravel", []):
            if "path_m" in srf:
                pairs = _path_ends(srf)
            else:
                rows = srf["rows_m"]
                pairs = [[(r[0], r[1]), (r[0], r[2])] for r in (rows[0], rows[-1])]
            for which, (a, b) in zip(("first", "last"), pairs):
                out.append({"kind": f"grounds_{srf['id']}", "corners": [world(*a), world(*b)],
                            "n": f"{srf['id']}_{which}"})
    return out


def _square_to_walk(end, walks):
    """A drive's end: its centre's nearest public walk point gives the way out; its edge runs
    square to that, the drive's width long."""
    c = end["centre"]
    d, q, _f = nearest_walk(c, walks)
    if q is None or d == 0.0:
        return [c, c] if q is None else None
    ux, uy = (q[0] - c[0]) / d, (q[1] - c[1]) / d
    h = end["width"] / 2
    return [(c[0] - uy * h, c[1] + ux * h), (c[0] + uy * h, c[1] - ux * h)]


def public_walks(grid):
    return [(f["id"], poly) for f in grid["faces"] for poly in (f.get("bands") or {}).get("walk", [])]


def walk_ends(sidecars, glb_extras, records):
    """Every walk end in the 1904 scene: (house id, kind, corners) in world e/n."""
    ends = []
    for sid, extras in glb_extras:
        sc = sidecars.get(sid)
        if not sc:
            continue
        world = H.to_world(sc.get("placement") or {})
        for e in _ends_of_glb(sid, extras, world):
            ends.append({"house": sid, **e})
    for rec in records:
        sc = sidecars.get(rec["id"])
        if not sc:
            continue
        world = H.to_world(sc.get("placement") or {})
        for e in _ends_of_grounds(rec, world):
            ends.append({"house": rec["id"], **e})
    return ends


def lay(ends, walks):
    joins = []
    for e in ends:
        if "centre" in e:
            corners = _square_to_walk(e, walks)
            if corners is None:     # its centre stands on the public walk
                joins.append({"id": f"{e['house']}:{e['kind']}:{e['n']}", "house": e["house"], "kind": e["kind"],
                              "gap_m": 0.0, "state": "meets"})
                continue
            e = {**e, "corners": corners}
        e = {**e, "id": f"{e['house']}:{e['kind']}:{e['n']}"}
        joins.append(join_for(e, walks))
    return joins


def _real_inputs():
    sidecars = H.load_sidecars()
    glbs = []
    for sid, sc in sorted(sidecars.items()):
        asset = sc.get("asset") or ""
        p = ROOT / "assets" / asset
        if not asset.endswith(".glb") or not p.exists():
            continue
        if p.read_bytes()[:4] != b"glTF":
            continue
        try:
            ex = H.glb_extras(p)
        except (ValueError, KeyError, IndexError):
            continue
        if ex.get("k01") or ex.get("k16"):
            glbs.append((sid, ex))
    records = []
    for p in sorted(STRUCTURES.glob("*.json")):
        try:
            st = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(st, dict) and st.get("archetype") == "k13_conservatories" and st["id"] in sidecars:
            records.append(st)
    return sidecars, glbs, records


def build():
    grid = json.loads(GRID.read_text())
    walks = public_walks(grid)
    joins = lay(walk_ends(*_real_inputs()), walks)
    laid = [j for j in joins if j["state"] == "joined"]
    doc = {
        "_doc": ("GENERATED by tools/lay_prairie_1904_walk_joins.py (T-3274) from the built walks of the 1904 "
                 "houses (their GLBs' K14/K16 yard instances, K13 `grounds` rows), their sidecar placements and "
                 "the public walk bands of data/street_grid/1904.json -- do not hand-edit; re-run the tool. Each "
                 "join is a paved strip from a house walk's street end square across the one-foot margin (1905 "
                 "code sec. 2062) to the public walk; street-grid.js draws it as part of that face's walk."),
        "scene": "1904",
        "ticket": "T-3274",
        "generated_by": "tools/lay_prairie_1904_walk_joins.py",
        "liberty": LIBERTY,
        "tier": "reconstructed",
        "sources": ["chicago_revised_municipal_code_1905"],
        "rule": {"meet_m": MEET_M, "reach_m": REACH_M, "tuck_m": TUCK_M},
        "summary": {"walk_ends": len(joins), "joined": len(laid),
                    "already_met": sum(j["state"] == "meets" for j in joins),
                    "not_street_ends": sum(j["state"] == "not a street end" for j in joins),
                    "widest_gap_m": max((j["gap_m"] for j in laid), default=0.0)},
        "joins": [{k: j[k] for k in ("id", "house", "kind", "face", "gap_m", "width_m", "polygon_local_m")} for j in laid],
    }
    return doc, joins


def render(doc) -> str:
    head = {k: v for k, v in doc.items() if k != "joins"}
    text = json.dumps(head, indent=1, ensure_ascii=False)[:-2]
    rows = ",\n".join("  " + json.dumps(j, separators=(", ", ": "), ensure_ascii=False) for j in doc["joins"])
    return text + ',\n "joins": [\n' + rows + "\n ]\n}\n"


# -- self-test -----------------------------------------------------------------------------

def self_test() -> int:
    bad = 0

    def case(name, ok, why):
        nonlocal bad
        print(f"   self-test | {'ok  ' if ok else 'FAIL'} {name}: {why}")
        bad += not ok

    # a public walk band from e 20.3 to 22.1 along n, a house at the origin facing +e (u = e, s = n)
    walks = [("face", [[20.3, -10.0], [20.3, 30.0], [22.1, 30.0], [22.1, -10.0]])]
    world = H.to_world({"local_e": 0.0, "local_n": 0.0, "rotation_deg": 0.0})
    walk = {"k01": {"components": [{"id": "k14.yard.front_walk", "family": "yard", "instances": [
        {"params": {"width_m": 1.2}, "sockets": {"stoop_foot": [12.0, 0.06, -4.0], "public_walk": [20.0, 0.06, -4.0]}}]}]}}
    j = lay([{"house": "h", **e} for e in _ends_of_glb("h", walk, world)], walks)[0]
    case("a walk ending a foot short is joined", j["state"] == "joined" and abs(j["gap_m"] - 0.3) < 1e-6, j)
    poly = j.get("polygon_local_m", [])
    case("the join runs from under the walk's end into the public walk",
         len(poly) == 4 and abs(poly[0][0] - (20.0 - TUCK_M)) < 1e-3 and abs(poly[2][0] - (20.3 + TUCK_M)) < 1e-3
         and abs(abs(poly[1][1] - poly[0][1]) - 1.2) < 1e-3, poly)
    walk["k01"]["components"][0]["instances"][0]["sockets"]["public_walk"] = [20.4, 0.06, -4.0]
    j = lay([{"house": "h", **e} for e in _ends_of_glb("h", walk, world)], walks)[0]
    case("a walk that reaches the public walk is left alone", j["state"] == "meets", j["state"])
    walk["k01"]["components"][0]["instances"][0]["sockets"]["public_walk"] = [14.0, 0.06, -4.0]
    j = lay([{"house": "h", **e} for e in _ends_of_glb("h", walk, world)], walks)[0]
    case("an end far from every public walk is not a street end", j["state"] == "not a street end", j["state"])
    turned = {"k01": {"components": [{"id": "k14.yard.front_walk", "family": "yard", "instances": [
        {"params": {"width_m": 1.28, "legs_m": [[12.0, 13.6, 3.36, 4.64, "u"], [13.6, 14.88, 3.36, 8.64, "s"],
                                               [14.88, 19.7, 7.36, 8.64, "u"]]},
         "sockets": {"stoop_foot": [12.0, 0.06, -4.0], "public_walk": [19.7, 0.06, -8.0]}}]}]}}
    j = lay([{"house": "h", **e} for e in _ends_of_glb("h", turned, world)], walks)[0]
    case("a turned walk is joined at its last leg's end", j["state"] == "joined" and abs(j["gap_m"] - 0.6) < 1e-6
         and min(p[1] for p in j["polygon_local_m"]) > 7.3, j)
    service = {"k01": {"components": [
        {"id": "k14.yard.service_walk", "family": "yard", "instances": [
            {"params": {"length_m": 20.0, "width_m": 3.0}, "sockets": {"rear_end": [0.0, 0.035, -1.5], "gate": [19.4, 0.035, -1.7]}}]},
        {"id": "k11.gate.walk_gate_on_piers", "family": "gate", "instances": [
            {"params": {"clear_m": 1.0}, "sockets": {"opening": [19.6, 0.0, -1.7]}}]}]}}
    j = lay([{"house": "h", **e} for e in _ends_of_glb("h", service, world)], walks)[0]
    case("a gated service walk is joined at its side gate's width", j["state"] == "joined"
         and abs(j["width_m"] - (1.0 - SIDE_JOINT_M)) < 1e-3, j.get("width_m"))
    drive = {"k01": {"components": [{"id": "k14.yard.drive", "family": "yard", "instances": [
        {"params": {"width_m": 2.4}, "sockets": {"from": [19.9, 0.1, -10.0], "to": [5.0, 0.1, -10.0]}}]}]}}
    js = lay([{"house": "h", **e} for e in _ends_of_glb("h", drive, world)], walks)
    case("a drive's street end is joined square to the walk, its far end left", js[0]["state"] == "joined"
         and abs(js[0]["width_m"] - 2.4) < 1e-3 and js[1]["state"] == "not a street end", [x["state"] for x in js])
    rec = {"id": "g", "phases": [{"documented_range": {"from": "1890-01-01", "to": "1910-01-01"}, "form": {
        "conservatory": {"value": {"pavilion": {"grounds": {"gravel": [{"id": "walk", "rows_m": [
            [19.5, 1.0, 2.8, 0.0], [10.0, 1.0, 2.8, 0.0]]}]}}}}}}]}
    js = lay([{"house": "g", **e} for e in _ends_of_grounds(rec, world)], walks)
    case("a K13 ground's walk is joined at the row nearest the street", js[0]["state"] == "joined"
         and abs(js[0]["gap_m"] - 0.8) < 1e-6 and js[1]["state"] == "not a street end", [x["state"] for x in js])
    curved = {"id": "g", "phases": [{"documented_range": {"from": "1890-01-01", "to": "1910-01-01"}, "form": {
        "conservatory": {"value": {"pavilion": {"grounds": {"gravel": [{"id": "turn", "path_m": [
            [10.0, 4.0, 0.0], [14.0, 6.0, 0.0], [17.0, 10.0, 0.0], [18.0, 10.0, 0.0], [19.6, 10.0, 0.0]],
            "width_m": [3.0, 2.0], "samples": 5, "edge_m": 0.35}]}}}}}}]}
    js = lay([{"house": "g", **e} for e in _ends_of_grounds(curved, world)], walks)
    pl = js[1].get("polygon_local_m", [])
    case("a K13 ground's curved gravel (path_m) is joined at its curve's street end, its end's width wide",
         js[1]["state"] == "joined" and abs(js[1]["gap_m"] - 0.7) < 1e-6 and abs(js[1]["width_m"] - 2.0) < 1e-3
         and len(pl) == 4 and abs(min(p[1] for p in pl) - 9.0) < 1e-3 and js[0]["state"] == "not a street end",
         [(x["state"], x["gap_m"], x.get("width_m")) for x in js])
    turned_world = H.to_world({"local_e": 30.0, "local_n": 0.0, "rotation_deg": 180.0})
    walk["k01"]["components"][0]["instances"][0]["sockets"]["public_walk"] = [7.4, 0.06, -4.0]
    j = lay([{"house": "h", **e} for e in _ends_of_glb("h", walk, turned_world)], walks)[0]
    case("a house facing west across the street is joined from its own side", j["state"] == "joined"
         and abs(j["gap_m"] - 0.5) < 1e-6 and max(p[0] for p in j["polygon_local_m"]) < 22.6 + 2 * TUCK_M
         and min(p[0] for p in j["polygon_local_m"]) > 22.1 - 2 * TUCK_M, j)
    print(f"   self-test | {'ok' if not bad else 'FAIL'}: {11 - bad} of 11 cases")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true")
    g.add_argument("--report", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    doc, joins = build()
    if a.report:
        for j in sorted(joins, key=lambda j: -j["gap_m"]):
            print(f"  {j['state']:17s} {j['gap_m']:6.2f} m  {j['id']}")
    text = render(doc)
    if a.check:
        old = OUT.read_text() if OUT.exists() else ""
        if old != text:
            have = {j["id"]: j for j in (json.loads(old).get("joins", []) if old else [])}
            want = {j["id"]: j for j in doc["joins"]}
            moved = sorted(k for k in set(have) | set(want) if have.get(k) != want.get(k))
            print("lay_prairie_1904_walk_joins: FAIL — data/street_section/walk_joins_1904.json is not what the "
                  "built walks give (a house's walk or placement moved?); re-run "
                  "`python3 tools/lay_prairie_1904_walk_joins.py`. Changed: " + (", ".join(moved[:12]) or "the header"))
            return 1
        s = doc["summary"]
        print(f"lay_prairie_1904_walk_joins: ok — {s['joined']} walk ends joined to the public walk "
              f"(widest gap {s['widest_gap_m']} m), {s['already_met']} already meet it")
        return 0
    if not a.report:
        OUT.write_text(text)
        s = doc["summary"]
        print(f"wrote {OUT.relative_to(ROOT)}: {s['joined']} joins, {s['already_met']} ends already meet, "
              f"{s['not_street_ends']} not street ends")
    return 0


if __name__ == "__main__":
    sys.exit(main())
