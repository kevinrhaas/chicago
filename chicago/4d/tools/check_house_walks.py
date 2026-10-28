#!/usr/bin/env python3
"""Every worked 1904 house can be walked into: a walk from the public walk to its door, through
an opening in its front boundary, that nothing solid stands across (T-3206).

The owner, 2026-10-27, of the worked Prairie houses: "make sure for the future that ... you have
their walkways to their house correct and the front gate/fence/borders ... some you have and
they look good, others are missing, cant enter, or are just plain wrong". This is the "for the
future" half. It reads what was BUILT, not what a record says: the component instances
`k01_frontage.to_glb` writes into each GLB's node extras (the K14 front walk's sockets and legs,
the K11 boundary's runs, gates and coping), and the sidecars the walker turns into solid
footprints (renderers/web/js/walker.js footprintsFrom). For every worked house — a
`k01_frontage` or `k16_timber` record with a phase in the 1904 scene; a `prairie_draft` is not
worked, and Glessner (`masonry_house`, its own pipeline and bake notes) is not one of these —
it requires:

  1. a walk: a `k14.yard.front_walk` instance, whose legs (`legs_m`, or the one straight leg its
     `stoop_foot` and `public_walk` sockets and `width_m` describe) run on from one to the next
     from the stoop's foot out to the public walk's inner edge;
  2. an opening: no leg crosses a run of the front boundary — a fence between its gates, a
     coping wall's laid runs, a garden's wall or fence, a stone-post line's rails — so the walk
     passes the boundary only where it is open or gated;
  3. a way in on foot: no leg, carried into the scene by the house's sidecar placement, lies
     across any footprint the walker holds solid (the house's own included), so a visitor
     walking up it is not stopped short of the door.

A house that fails and is in PENDING is reported and does not fail the gate: the 1600 and 1700
blocks' houses were worked before this rule, and their lanes (T-3204, T-3205) empty the list as
they fix each one. A PENDING house that now passes DOES fail the gate, so the list cannot rot:
take it out. So does a PENDING id that is not a worked 1904 house.

    python3 tools/check_house_walks.py --check       the gate (check.sh)
    python3 tools/check_house_walks.py --report      every worked house, pass or fail, and why
    python3 tools/check_house_walks.py --self-test   plants each fault and proves it is refused
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKED = ("k01_frontage", "k16_timber")
SCENE_DAY = dt.date(1904, 7, 1)
EPS = 0.02          # metres a leg may overlap a barrier's line or a footprint's edge by rounding
MARGIN = 0.05       # a leg must clear a laid run's end by this much to pass beside it

# The houses worked before this gate, which fail it today, each with the lane that fixes it.
# Those lanes take their entries out as they fix them; a passing entry fails the gate.
PENDING = {
    "goodman_house_1612_prairie": "T-3204",
    "house_1600_prairie": "T-3204",
    "house_1601_prairie": "T-3204",
    "house_1604_prairie": "T-3204",
    "house_1608_prairie": "T-3204",
    "house_1609_prairie": "T-3204",
    "house_1611_prairie": "T-3204",
    "house_1613_prairie": "T-3204",
    "house_1615_prairie": "T-3204",
    "house_1619_prairie": "T-3204",
    "house_1626_prairie": "T-3204",
    "house_1628_prairie": "T-3204",
    "house_1630_prairie": "T-3204",
    "house_1634_prairie": "T-3204",
    "house_1636_prairie": "T-3204",
    "law_house_1620_prairie": "T-3204",
    "dexter_house_1721_prairie": "T-3205",
    "house_1708_prairie": "T-3205",
    "house_1712_prairie": "T-3205",
    "house_1726_prairie": "T-3205",
    "house_1730_prairie": "T-3205",
    "house_1736_prairie": "T-3205",
    "kellogg_house_1709_prairie": "T-3205",
    "elbridge_keith_house_1900_prairie": "T-3207",   # onto K01 by T-3207 (#1385) after this gate was written; its walk is that lane's
    "pullman_house_1729_prairie": "T-3205",
    "walker_house_1720_prairie": "T-3205",
}


# -- reading what was built ----------------------------------------------------------------

def glb_extras(path: Path) -> dict:
    b = path.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])["nodes"][0].get("extras") or {}


def instances(extras: dict):
    """(component id, family, params, sockets) for every instance the GLB carries."""
    for c in (extras.get("k01") or extras.get("k16") or {}).get("components", []):
        for i in c.get("instances", []):
            yield c["id"], c.get("family"), i.get("params") or {}, i.get("sockets") or {}


def walk_legs(inst) -> list[tuple[float, float, float, float]] | None:
    """The front walk's legs as (u0, u1, s0, s1) in the house's frame (u = the assembly's X,
    out of the house; s = -Z, along the street front), or None where none was built."""
    for cid, _fam, prm, sk in inst:
        if cid != "k14.yard.front_walk":
            continue
        if prm.get("legs_m"):
            return [(l[0], l[1], l[2], l[3]) for l in prm["legs_m"]]
        foot, pub = sk["stoop_foot"], sk["public_walk"]
        s, w = -foot[2], prm["width_m"]
        return [(foot[0], pub[0], s - w / 2, s + w / 2)]
    return None


def barriers(inst, axis_s: float | None) -> list[tuple[float, float, float, float]]:
    """The front boundary's laid runs as segments (x0, s0, x1, s1) in the house's frame: what a
    walk may not cross. Openings — gates, a coping wall's open runs, the gaps a stone-post line
    leaves at the stair and the side passage — are what is left out."""
    inst = list(inst)
    gates = [(sk["opening"][0], -sk["opening"][2], prm["clear_m"]) for cid, _f, prm, sk in inst
             if cid == "k11.gate.walk_gate_on_piers"]
    out = []
    for cid, fam, prm, sk in inst:
        if fam == "fence" and "line_south" in sk:          # an iron (or boarded) street line
            x = sk["line_south"][0]
            a, b = sorted((-sk["line_south"][2], -sk["line_north"][2]))
            cuts = sorted((s - c / 2, s + c / 2) for gx, s, c in gates if abs(gx - x) < 0.05)
            lo = a
            for c0, c1 in cuts:
                if c0 > lo:
                    out.append((x, lo, x, min(c0, b)))
                lo = max(lo, c1)
            if lo < b:
                out.append((x, lo, x, b))
        elif "end_a" in sk and "end_b" in sk:              # a garden's wall or fence, a side run
            out.append((sk["end_a"][0], -sk["end_a"][2], sk["end_b"][0], -sk["end_b"][2]))
        elif "street_end" in sk and "rear_end" in sk:      # a wall or boards along a lot line
            out.append((sk["street_end"][0], -sk["street_end"][2], sk["rear_end"][0], -sk["rear_end"][2]))
        elif cid == "k11.wall.stone_coping_wall":
            x, t = sk["street"][0], prm["thickness_m"]
            lo = prm["lot_s_m"][0]
            for r in prm["runs"]:
                if not r.get("opening"):
                    out.append((x - t / 2, lo, x - t / 2, r["to_s_m"]))
                lo = r["to_s_m"]
        elif cid == "k11.fence.stone_posts_rails":
            if axis_s is None:
                continue
            x = sk["street"][0]                                    # the rails' centre line
            ea, eb = axis_s - prm["entrance_clear_m"] / 2, axis_s + prm["entrance_clear_m"] / 2
            out += [(x, 0.0, x, ea), (x, eb, x, prm["lot_s_m"][1])]
    return out


def _seg_hits_rect(seg, rect) -> bool:
    """Does segment (x0, s0, x1, s1) pass through the inside of rect (u0, u1, s0, s1), shrunk
    by EPS? Liang-Barsky clipping."""
    x0, y0, x1, y1 = seg
    u0, u1, r0, r1 = rect
    u0, u1, r0, r1 = u0 + EPS, u1 - EPS, r0 + EPS, r1 - EPS
    if u1 <= u0 or r1 <= r0:
        return False
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - u0), (dx, u1 - x0), (-dy, y0 - r0), (dy, r1 - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return t0 < t1


def _inside(pt, poly) -> bool:
    x, y = pt
    hit = False
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[i - 1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
    return hit


def _poly_hits_rect(poly, rect) -> bool:
    """Does a footprint polygon (in the house frame) overlap rect's inside, shrunk by EPS?"""
    u0, u1, r0, r1 = rect
    corners = [(u0 + EPS, r0 + EPS), (u1 - EPS, r0 + EPS), (u1 - EPS, r1 - EPS), (u0 + EPS, r1 - EPS)]
    if any(_inside(c, poly) for c in corners):
        return True
    if any(u0 + EPS < x < u1 - EPS and r0 + EPS < y < r1 - EPS for x, y in poly):
        return True
    return any(_seg_hits_rect((poly[i - 1][0], poly[i - 1][1], poly[i][0], poly[i][1]), rect) for i in range(len(poly)))


# -- the scene's solid footprints, as walker.js holds them ----------------------------------

def to_world(pl):
    th = math.radians(pl.get("rotation_deg") or 0.0)
    c, s, e0, n0 = math.cos(th), math.sin(th), pl.get("local_e") or 0.0, pl.get("local_n") or 0.0
    return lambda u, v: (e0 + u * c + v * s, n0 - u * s + v * c)


def to_frame(pl):
    th = math.radians(pl.get("rotation_deg") or 0.0)
    c, s, e0, n0 = math.cos(th), math.sin(th), pl.get("local_e") or 0.0, pl.get("local_n") or 0.0
    return lambda e, n: ((e - e0) * c - (n - n0) * s, (e - e0) * s + (n - n0) * c)


def solid_footprints(sidecars: dict) -> list[tuple[str, list]]:
    """walker.js footprintsFrom(): every sidecar footprint, in world e/n, less water-anchored
    decks, records another layer draws, and camps. Passages are not modelled here: a walk to a
    front door never runs through one."""
    out = []
    for sid, sc in sidecars.items():
        raw = sc.get("footprint")
        poly = raw if isinstance(raw, list) else (raw or {}).get("polygon")
        if not isinstance(poly, list) or len(poly) < 3:
            continue
        pl = sc.get("placement") or {}
        if pl.get("vertical_anchor") == "water" or sc.get("drawn_by") or sc.get("archetype") == "camp":
            continue
        w = to_world(pl)
        out.append((sid, [w(u, v) for u, v in poly]))
    return out


# -- the rule ------------------------------------------------------------------------------

def judge(sid, extras, sidecar, solids, yard_m=None) -> list[str]:
    """Why house `sid` cannot be walked into, as reasons; [] when it can. `yard_m` is the
    record's front_yard_m: the public walk's inner edge stands that far before the street front."""
    inst = list(instances(extras))
    legs = walk_legs(inst)
    if not legs:
        return ["no walk: the GLB carries no k14.yard.front_walk from the public walk to the door"]
    why = []
    foot = next(sk["stoop_foot"] for cid, _f, _p, sk in inst if cid == "k14.yard.front_walk")
    pub = next(sk["public_walk"] for cid, _f, _p, sk in inst if cid == "k14.yard.front_walk")
    if abs(legs[0][0] - foot[0]) > EPS:
        why.append(f"the walk does not start at the stoop's foot (u {legs[0][0]:.2f}, foot {foot[0]:.2f})")
    front = next((sk["base"][0] for cid, _f, _p, sk in inst if cid == "k01.wall.street_front"), None)
    edge = front + yard_m if front is not None and yard_m is not None else pub[0]
    if legs[-1][1] < edge - EPS:
        why.append(f"the walk stops at u {legs[-1][1]:.2f}, short of the public walk's inner edge at {edge:.2f}")
    for a, b in zip(legs, legs[1:]):
        touch_u = a[1] >= b[0] - EPS and b[1] >= a[0] - EPS
        touch_s = a[3] >= b[2] - EPS and b[3] >= a[2] - EPS
        if not (touch_u and touch_s):
            why.append(f"the walk's legs {a} and {b} do not meet")
    axis = (legs[0][2] + legs[0][3]) / 2
    for seg in barriers(inst, axis):
        for leg in legs:
            if _seg_hits_rect(seg, leg):
                why.append(f"the walk (u {leg[0]:.2f}-{leg[1]:.2f}, s {leg[2]:.2f}-{leg[3]:.2f}) crosses the boundary's "
                           f"run x {seg[0]:.2f}, s {seg[1]:.2f}-{seg[3]:.2f}: no opening or gate there")
    if sidecar is None:
        why.append("no 1904 sidecar places the house, so the walker cannot be asked")
        return why
    frame = to_frame(sidecar.get("placement") or {})
    for other, poly in solids:
        local = [frame(e, n) for e, n in poly]
        for leg in legs:
            if _poly_hits_rect(local, leg):
                who = "its own footprint" if other == sid else f"{other}'s footprint"
                why.append(f"the walk (u {leg[0]:.2f}-{leg[1]:.2f}, s {leg[2]:.2f}-{leg[3]:.2f}) runs into {who}, "
                           "which the walker holds solid: a visitor cannot walk up it")
                break
    return why


def _covers(phase) -> bool:
    r = phase.get("documented_range") or {}
    try:
        a = dt.date.fromisoformat(r["from"][:10])
        b = dt.date.fromisoformat(r["to"][:10])
    except (KeyError, TypeError, ValueError):
        return False
    return a <= SCENE_DAY <= b


def _front_yard(phase):
    kit = ((phase.get("form") or {}).get("entrance_kit") or {}).get("value") or {}
    return (kit.get("k01.opening.door_leaf") or {}).get("front_yard_m")


def worked_houses():
    """(id, phase id, front_yard_m) of every worked house with a phase in the 1904 scene."""
    for p in sorted((ROOT / "data" / "structures").glob("*.json")):
        try:
            st = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(st, dict) or st.get("archetype") not in WORKED:
            continue
        for ph in st.get("phases", []):
            if _covers(ph):
                yield st["id"], ph["id"], _front_yard(ph)


def load_sidecars() -> dict:
    out = {}
    for p in sorted((ROOT / "data" / "sidecars" / "1904").glob("*.json")):
        try:
            out[p.stem] = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
    return out


def run(houses, read_extras, sidecars, pending) -> tuple[list[str], list[str]]:
    """(failures, report lines)."""
    solids = solid_footprints(sidecars)
    fails, lines, seen = [], [], set()
    for sid, phase, yard_m in houses:
        seen.add(sid)
        try:
            ex = read_extras(sid, phase)
        except FileNotFoundError:
            why = [f"no GLB for its 1904 phase {phase}"]
        else:
            why = judge(sid, ex, sidecars.get(sid), solids, yard_m)
        if not why:
            if sid in pending:
                fails.append(f"{sid}: passes now; take it out of PENDING (it names {pending[sid]})")
            lines.append(f"  ok       {sid}")
            continue
        if sid in pending:
            lines.append(f"  pending  {sid} ({pending[sid]}): {why[0]}")
            continue
        fails += [f"{sid}: {w}" for w in why]
        lines.append(f"  FAIL     {sid}: {why[0]}")
    for sid in sorted(set(pending) - seen):
        fails.append(f"{sid}: in PENDING but not a worked house in the 1904 scene; take it out")
    return fails, lines


def _real_extras(sid, phase):
    return glb_extras(ROOT / "assets" / "gltf" / f"{sid}__{phase}.glb")


# -- the self-test: each fault planted on a synthetic house ---------------------------------

def _synthetic():
    """A house 10 m deep, its front at u 10, a stoop foot at u 12, the public walk at u 16, its
    fence on u 15.85 with a gate at s 4 (1.3 m), a walk through it; placed at the origin."""
    walk = {"id": "k14.yard.front_walk", "family": "yard", "instances": [
        {"params": {"width_m": 1.28, "flags": 4}, "sockets": {"stoop_foot": [12.0, 0.06, -4.0],
                                                               "public_walk": [16.0, 0.06, -4.0]}}]}
    fence = {"id": "k11.fence.spear_on_curb", "family": "fence", "instances": [
        {"params": {}, "sockets": {"line_south": [15.85, 0.0, 1.0], "line_north": [15.85, 0.0, -9.0]}}]}
    gate = {"id": "k11.gate.walk_gate_on_piers", "family": "gate", "instances": [
        {"params": {"clear_m": 1.3}, "sockets": {"opening": [15.85, 0.0, -4.0]}}]}
    front = {"id": "k01.wall.street_front", "family": "wall", "instances": [
        {"params": {}, "sockets": {"base": [10.0, 0.0, 0.0], "top": [10.0, 9.0, 0.0]}}]}
    ex = {"k01": {"components": [walk, fence, gate, front]}}
    sc = {"placement": {"local_e": 0.0, "local_n": 0.0, "rotation_deg": 0.0},
          "footprint": {"polygon": [[0, 0], [10, 0], [10, 8], [0, 8]]}}
    return ex, sc


def self_test() -> int:
    import copy
    bad = 0

    def case(name, ex, scs, pending, want_fail):
        nonlocal bad
        fails, _ = run([("h", "p", 6.0)], lambda s, p: ex, scs, pending)
        ok = bool(fails) == want_fail
        print(f"   self-test | {'ok  ' if ok else 'FAIL'} {name}: {fails[0] if fails else 'passes'}")
        bad += not ok

    ex, sc = _synthetic()
    case("a walk through its gate passes", ex, {"h": sc}, {}, False)
    e = copy.deepcopy(ex); e["k01"]["components"] = [c for c in e["k01"]["components"] if c["family"] != "yard"]
    case("no walk is refused", e, {"h": sc}, {}, True)
    e = copy.deepcopy(ex); e["k01"]["components"] = [c for c in e["k01"]["components"] if c["family"] != "gate"]
    case("a walk through a fence with no gate is refused", e, {"h": sc}, {}, True)
    e = copy.deepcopy(ex); e["k01"]["components"][2]["instances"][0]["sockets"]["opening"] = [15.85, 0.0, -7.0]
    case("a gate beside the walk, not on it, is refused", e, {"h": sc}, {}, True)
    e = copy.deepcopy(ex); e["k01"]["components"][0]["instances"][0]["sockets"]["public_walk"] = [14.0, 0.06, -4.0]
    case("a walk stopping short of the public walk is refused", e, {"h": sc}, {}, True)
    blocker = {"placement": {"local_e": 13.0, "local_n": 3.0, "rotation_deg": 0.0},
               "footprint": {"polygon": [[0, 0], [1, 0], [1, 2], [0, 2]]}}
    case("a footprint across the walk is refused", ex, {"h": sc, "shed": blocker}, {}, True)
    e = copy.deepcopy(ex); e["k01"]["components"][0]["instances"][0]["sockets"]["stoop_foot"] = [9.0, 0.06, -4.0]
    case("a walk run into the house's own footprint is refused", e, {"h": sc}, {}, True)
    coping = {"id": "k11.wall.stone_coping_wall", "family": "wall", "instances": [
        {"params": {"thickness_m": 0.3, "lot_s_m": [-1.0, 9.0],
                    "runs": [{"to_s_m": 7.0, "height_m": 0.4}, {"to_s_m": 9.0, "opening": True}]},
         "sockets": {"street": [16.0, 0, 0]}}]}
    e = copy.deepcopy(ex); e["k01"]["components"] = [e["k01"]["components"][0], coping, e["k01"]["components"][3]]
    case("a walk through a coping wall's laid run is refused", e, {"h": sc}, {}, True)
    e["k01"]["components"][0]["instances"][0]["params"]["legs_m"] = [
        [12.0, 13.6, 3.36, 4.64, "u"], [13.6, 14.88, 3.36, 8.64, "s"], [14.88, 16.0, 7.36, 8.64, "u"]]
    e["k01"]["components"][0]["instances"][0]["sockets"]["public_walk"] = [16.0, 0.06, -8.0]
    case("a turned walk out through the coping's opening passes", e, {"h": sc}, {}, False)
    e2 = copy.deepcopy(e); e2["k01"]["components"][0]["instances"][0]["params"]["legs_m"][1][0:2] = [13.6, 14.3]
    case("a turned walk whose legs do not meet is refused", e2, {"h": sc}, {}, True)
    case("a PENDING house that passes is refused (take it out)", ex, {"h": sc}, {"h": "T-0000"}, True)
    e = copy.deepcopy(ex); e["k01"]["components"] = []
    case("a PENDING house that fails is reported, not refused", e, {"h": sc}, {"h": "T-0000"}, False)
    # T-3222: a K16 front names its walk and its fence's runs under "k16", the runs by their ends
    k16 = {"k16": {"components": [copy.deepcopy(ex["k01"]["components"][0]), {
        "id": "k16.boundary.street_fence", "family": "fence", "instances": [
            {"params": {}, "sockets": {"end_a": [15.85, 0.0, 1.0], "end_b": [15.85, 0.0, -3.3]}},
            {"params": {}, "sockets": {"end_a": [15.85, 0.0, -4.7], "end_b": [15.85, 0.0, -9.0]}}]}]}}
    case("a K16 walk through its fence's gateway passes", k16, {"h": sc}, {}, False)
    e = copy.deepcopy(k16); e["k16"]["components"][1]["instances"][1]["sockets"]["end_a"] = [15.85, 0.0, -3.3]
    case("a K16 walk across its fence's run is refused", e, {"h": sc}, {}, True)
    fails, _ = run([], lambda s, p: ex, {"h": sc}, {"ghost": "T-0000"})
    ok = bool(fails)
    print(f"   self-test | {'ok  ' if ok else 'FAIL'} a PENDING id that is not a worked house is refused: "
          f"{fails[0] if fails else 'passes'}")
    bad += not ok
    print(f"   self-test | {'ok' if not bad else 'FAIL'}: {15 - bad} of 15 cases")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--report", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    houses = list(worked_houses())
    fails, lines = run(houses, _real_extras, load_sidecars(), PENDING)
    if a.report or fails:
        print("\n".join(lines))
    n_ok = sum(l.startswith("  ok") for l in lines)
    n_pend = sum(l.startswith("  pending") for l in lines)
    if fails:
        print("check_house_walks: FAIL")
        for f in fails:
            print(f"  {f}")
        return 1
    print(f"check_house_walks: ok — {n_ok} worked 1904 houses walked into from the public walk through an "
          f"opening; {n_pend} pending on their lanes (T-3204, T-3205, T-3207)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
