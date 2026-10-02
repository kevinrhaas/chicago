#!/usr/bin/env python3
"""Every door in the 1835 town, once, with where it is and which way it faces — and the
trodden ground in front of each. (T-1984)

## The fault this closes

The owner, walking Lake Street on dev on 2026-10-02: *"goods or furntiture in front of
doors … and also in and around in front of buildings there is prairie grass, that would
be worn down and not be wild prairie right in front of the entrance to buildings"*.

Both halves have one cause. Nothing in the town's layers asked WHERE A DOOR IS before
putting something down. The archetypes have stated their front elevations since T-0459
and T-0520 (`generators/archetypes/facade_openings.py`), but the only reader was the
signboard generator: the frontage layer still put a store's stoop at
`FIT_DOOR_ALONG = 0.5` — "the door is not on any record: the middle of the front" — so
on an off-centre shop door the steps stood under the show window, and the sward was
planted right up to every threshold in town.

## What this writes

1. **`data/enclosures/town_entrance_aprons.json`**, an enclosure-layer record with no
   fence: only a `ground` block whose interior is one apron per door. `yards.js` lays
   it as trodden earth and `main.js`'s sward block-list refuses the prairie inside it,
   exactly as it does inside a fenced yard (T-0124). No new renderer layer.
2. **`data/enclosures/town_entrances.json`**'s sibling list — every door with its
   structure, its kind, its centre on the wall line in local ENU, its outward bearing
   and its width — lives inside the same record under `entrances`, so the frontage
   generator and the doorway sweep read one list.

## Where the doors come from

`facade_openings.front_wall` for every archetype it reads (frame_storefront,
frame_dwelling since T-1984, log_dwelling, outbuilding): a `door`, `shop_door` or a
ground-level `open_bay`. `frame_tavern` has no reader; both its schemes centre the
front door on the front wall, 1.2 m wide (`frame_tavern.py`, "the front gable: centred
door" and "four plus a centred door below"), and that is what is read here, by name.
Fort, palisade, bridge, pier and camp records carry no street door and are not read.

## What is invented

The apron — its depth, its flare and the fact of it — is reconstructed (docs/LIBERTIES.md
L357): no source measures the trodden ground at any 1835 Chicago door. What bounds it is
the building and the door it serves: a strip along the whole front wall, the drip line
and the boots, and from each door a path a step either side of it, out across the walk
and the verge to the street's track where a street lies in front, otherwise two and a
half paces into the yard.

    python3 tools/generate_entrances.py           write the record
    python3 tools/generate_entrances.py --check   re-derive and diff; also refuses any
                                                  two holes on a read front that run
                                                  together (the merged openings, T-1984)
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

import generate_business_signboards as gbs  # noqa: E402
import generate_frontage_works as gfw  # noqa: E402

SIDECARS = ROOT / "data" / "sidecars" / "1835"
OUT = ROOT / "data" / "enclosures" / "town_entrance_aprons.json"
INDEX = ROOT / "data" / "enclosures" / "index.json"
STREETS = ROOT / "data" / "streets" / "1835.json"

ENTRANCE_KINDS = ("door", "shop_door", "open_bay")
GROUND_Z_M = 0.30          # an opening whose foot is above this is a loft or a window
TAVERN_DOOR_W_M = 1.2      # frame_tavern.py's front door, w/2 +- 0.6, both schemes

# THE WORN GROUND (reconstructed, L357). Two parts, one ring per front:
#  * a STRIP the length of the front wall and a little past its corners — the drip
#    line, the boots at the door and the shoulder of everyone who stood against the
#    wall; the owner's "in and around in front of buildings";
#  * a PATH out from each door, widest at the door and narrowing as it goes, across
#    the walk and the verge to the street's track when one is in front, otherwise two
#    and a half paces out to where it meets the yard.
STRIP_DEPTH_M = 1.4
STRIP_PAST_CORNER_M = 0.4
PATH_SIDE_AT_STRIP_M = 1.2     # either side of the door, where the path leaves the strip
PATH_SIDE_OUT_M = 0.7          # ...and where it ends
PATH_DEPTH_M = 3.4             # with no street in front: where it meets the yard
PATH_TO_STREET_M = 14.0        # a street track this close in front: the path runs to it
PATH_INTO_TRACK_M = 0.3
PATH_ROUND_M = 0.35

# The least wall between two holes on one front (T-1984); the two archetypes that
# set out their fronts by bay state the same figure.
OPENING_GAP_M = 0.15
SHOPFRONT = frozenset({"shop_door", "show_window"})


def _r(x: float) -> float:
    return round(x, 2)


def _sidecars() -> list[dict]:
    out = []
    for p in sorted(SIDECARS.glob("*.json")):
        sc = json.loads(p.read_text(encoding="utf-8"))
        # A phase `drawn_by` another layer has no mesh and no door: the estray pen
        # is a roofless fence (T-0051), and its gateway is the enclosure's own.
        if isinstance(sc, dict) and sc.get("id") and sc.get("archetype") \
                and not sc.get("drawn_by"):
            out.append(sc)
    return out


def front_doors(sc: dict) -> tuple[list[dict], str | None]:
    """The ground-level doors on `sc`'s front wall, as `{kind, u0, u1}` in footprint
    `u`, and the reader that answered — or ([], None) where nothing reads it."""
    arch = sc["archetype"]
    if arch == "frame_tavern":
        poly = (sc.get("footprint") or {}).get("polygon") or []
        if len(poly) < 3:
            return [], None
        u0, u1, _v = gbs._front_edge(poly)
        c = (u0 + u1) / 2.0
        return ([{"kind": "door", "u0": c - TAVERN_DOOR_W_M / 2,
                  "u1": c + TAVERN_DOOR_W_M / 2}], "frame_tavern centred front door")
    wall = gbs._front_wall(sc["id"])
    if wall is None:
        return [], None
    doors = [{"kind": o["kind"], "u0": o["u0"], "u1": o["u1"]}
             for o in wall["openings"]
             if o["kind"] in ENTRANCE_KINDS and o["z0"] < GROUND_Z_M]
    return doors, f"facade_openings.{arch}"


def merged_openings(sc: dict) -> list[str]:
    """Holes on `sc`'s front that run together: overlapping, or closer than
    OPENING_GAP_M, at overlapping heights. A shopfront's door and show window are one
    joinery unit with a mullion between them and are not two holes."""
    wall = gbs._front_wall(sc["id"])
    if wall is None:
        return []
    holes = [o for o in wall["openings"]
             if o["kind"] in gbs.facade_openings.HOLE_KINDS]
    bad = []
    for i, a in enumerate(holes):
        for b in holes[i + 1:]:
            if {a["kind"], b["kind"]} <= SHOPFRONT:
                continue
            if a["z0"] >= b["z1"] or b["z0"] >= a["z1"]:
                continue
            gap = max(b["u0"] - a["u1"], a["u0"] - b["u1"])
            if gap < OPENING_GAP_M - 1e-6:
                bad.append(f"{sc['id']}: {a['kind']} {a['u0']:.2f}-{a['u1']:.2f} and "
                           f"{b['kind']} {b['u0']:.2f}-{b['u1']:.2f} stand {gap:.2f} m "
                           f"apart at overlapping heights — one hole, not two")
    return bad


def _streets() -> list[tuple[list, float]]:
    """`(centreline, half track width)` for every 1835 street, from the same file the
    street renderer and the frontage generator read."""
    doc = json.loads(STREETS.read_text(encoding="utf-8"))
    return [([tuple(q) for q in st.get("path_local_enu_m", [])],
             float(st.get("track_width_m") or 7.0) / 2.0)
            for st in doc.get("streets", []) if len(st.get("path_local_enu_m", [])) >= 2]


def _in_track(pt, streets) -> bool:
    return any(gfw._nearest_on_path(pt, path)[0] <= half for path, half in streets)


def path_depth(door_enu, outward, streets) -> float:
    """How far the trodden path runs out of a door: to the travelled track of the
    street in front when one is within PATH_TO_STREET_M — the customer crosses
    whatever lies between, walk or verge, to reach the door — and otherwise
    PATH_DEPTH_M, to where it meets the yard. It stops PATH_INTO_TRACK_M short of
    nothing: it laps that far onto the track so no blade stands at the join."""
    t = PATH_DEPTH_M
    while t <= PATH_TO_STREET_M:
        pt = (door_enu[0] + outward[0] * t, door_enu[1] + outward[1] * t)
        if _in_track(pt, streets):
            return max(PATH_DEPTH_M, t + PATH_INTO_TRACK_M)
        t += 0.25
    return PATH_DEPTH_M


def _front_ring(fu0: float, fu1: float, doors: list, to_enu) -> list:
    """The worn ground in front of one front wall, as one ring in local ENU: the
    strip along the wall with a path bulging out at every door. `doors` are
    `(centre_u, half_width, depth)`; paths that would overlap are merged into one
    bulge as deep as the deeper of them. `to_enu(s, t)` maps along-wall `s` and
    outward `t` to local ENU."""
    a, b = fu0 - STRIP_PAST_CORNER_M, fu1 + STRIP_PAST_CORNER_M
    bulges = []
    for c, hw, dep in sorted(doors):
        lo, hi = c - hw - PATH_SIDE_AT_STRIP_M, c + hw + PATH_SIDE_AT_STRIP_M
        lo2, hi2 = c - hw - PATH_SIDE_OUT_M, c + hw + PATH_SIDE_OUT_M
        if bulges and lo <= bulges[-1][1]:
            p = bulges[-1]
            bulges[-1] = (p[0], max(p[1], hi), p[2], max(p[3], hi2), max(p[4], dep))
        else:
            bulges.append((lo, hi, lo2, hi2, dep))
    k = PATH_ROUND_M
    far = []                      # the outer edge, walked from b back to a
    far.append((b, STRIP_DEPTH_M))
    for lo, hi, lo2, hi2, d in reversed(bulges):
        hi, lo = min(hi, b), max(lo, a)
        far += [(hi, STRIP_DEPTH_M), (hi2, d - k), (hi2 - k * 0.3, d - k * 0.3),
                (hi2 - k, d), (lo2 + k, d),
                (lo2 + k * 0.3, d - k * 0.3), (lo2, d - k),
                (lo, STRIP_DEPTH_M)]
    far.append((a, STRIP_DEPTH_M))
    local = [(a, 0.0), (b, 0.0)] + far
    out = []
    for s_, t in local:
        e, n = to_enu(s_, t)
        pt = [_r(e), _r(n)]
        if not out or out[-1] != pt:
            out.append(pt)
    return out


# THE DOORWAY ITSELF (T-1984): what no fence, good or fitting may stand in — the door's
# width and a hand either side, out to two paces. Smaller than the apron, which is
# what the WEAR covers; this is what a person walking out of the door needs.
DOORWAY_SIDE_M = 0.30
DOORWAY_OUT_M = 1.80


def doorway_zones() -> list[tuple[str, list]]:
    """`(entrance id, ring)` for every door's clear doorway, in local ENU."""
    out = []
    for x in build()["entrances"]:
        b = math.radians(x["bearing_deg"])
        o = (math.sin(b), math.cos(b))
        a = (math.cos(b), -math.sin(b))
        e, n = x["at_local_enu_m"]
        hw = x["width_m"] / 2.0 + DOORWAY_SIDE_M
        ring = [(e + a[0] * s + o[0] * t, n + a[1] * s + o[1] * t)
                for s, t in ((-hw, 0.0), (hw, 0.0), (hw, DOORWAY_OUT_M), (-hw, DOORWAY_OUT_M))]
        out.append((x["id"], ring))
    return out


def build() -> dict:
    entrances, rings, unread = [], [], {}
    streets = _streets()
    for sc in _sidecars():
        doors, reader = front_doors(sc)
        if reader is None:
            unread[sc["archetype"]] = unread.get(sc["archetype"], 0) + 1
            continue
        place = sc.get("placement") or {}
        poly = (sc.get("footprint") or {}).get("polygon") or []
        if len(poly) < 3:
            continue
        fu0, fu1, vmax = gbs._front_edge(poly)
        b = math.radians(place.get("rotation_deg") or 0.0)
        out = (math.sin(b), math.cos(b))

        def to_enu(s_, t, vmax=vmax, place=place, out=out):
            e, n = gbs._to_enu(s_, vmax, place)
            return e + out[0] * t, n + out[1] * t
        if doors:
            spec = []
            for d in doors:
                cu = (d["u0"] + d["u1"]) / 2.0
                spec.append((cu, (d["u1"] - d["u0"]) / 2.0,
                             path_depth(to_enu(cu, 0.0), out, streets)))
            rings.append(_front_ring(fu0, fu1, spec, to_enu))
        for k, d in enumerate(sorted(doors, key=lambda o: o["u0"])):
            cu = (d["u0"] + d["u1"]) / 2.0
            e, n = gbs._to_enu(cu, vmax, place)
            w = d["u1"] - d["u0"]
            eid = f"{sc['id']}__{d['kind']}_{k + 1}"
            entrances.append({
                "id": eid, "structure_id": sc["id"], "archetype": sc["archetype"],
                "kind": d["kind"], "read_by": reader,
                "at_local_enu_m": [_r(e), _r(n)],
                "bearing_deg": _r((math.degrees(b)) % 360.0),
                "width_m": _r(w),
            })
    return {
        "id": "town_entrance_aprons",
        "name": "The trodden ground at the town's doors",
        "aka": ["the door yards", "the worn ground at the thresholds"],
        "kind": "yard",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_entrances.py",
        "generated_from": ["data/sidecars/1835/", "generators/archetypes/facade_openings.py"],
        "belongs_to": sorted({x["structure_id"] for x in entrances}),
        "documented_range": {
            "from": "1835-07-01", "to": "1835-07-01", "confidence": "reconstructed",
            "sources": [],
            "note": "Dated to the scene: every door it serves is standing on it."},
        "existence": {
            "value": True, "confidence": "reconstructed", "sources": [],
            "note": ("RECONSTRUCTED (T-1984, docs/LIBERTIES.md L357). No source describes "
                     "the ground at any 1835 Chicago door. The owner's ruling of "
                     "2026-10-02 is that the ground in front of an entrance 'would be worn "
                     "down and not be wild prairie', and a door every household and "
                     "customer used several times a day is a path whatever the source "
                     "says. No fence is claimed.")},
        "runs": [],
        "openings": [],
        "form": {},
        "ground": {
            "treatment": "trodden_earth",
            "confidence": "reconstructed",
            "interior_local_enu_m": rings,
            "note": ("One ring per front with a door in `entrances`: a strip "
                     f"{STRIP_DEPTH_M} m deep along the whole front wall and "
                     f"{STRIP_PAST_CORNER_M} m past its corners, and from each door a path "
                     f"out to {PATH_DEPTH_M} m, {PATH_SIDE_AT_STRIP_M} m either side of the "
                     f"door where it leaves the strip narrowing to {PATH_SIDE_OUT_M} m — "
                     f"or, where a street's track lies within {PATH_TO_STREET_M} m in front, "
                     f"all the way to it and {PATH_INTO_TRACK_M} m onto it. "
                     "Reconstructed — bounded by the building it fronts and the doors in "
                     "it and nothing else (docs/LIBERTIES.md L357).")},
        "entrances": entrances,
        "unread": [{"archetype": a, "count": c,
                    "why": "no reader states this archetype's front door"}
                   for a, c in sorted(unread.items())],
        "research_note": ("Generated. A door is read off the same front elevation its "
                          "builder draws (facade_openings, T-0520), so the apron, the "
                          "frontage stoop and the doorway sweep cannot disagree with the "
                          "mesh about where the door is."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = [m for sc in _sidecars() for m in merged_openings(sc)]
    rec = build()
    # Pairs on one line: 510 aprons of eight vertices each are most of the file.
    text = re.sub(r"\[\s+(-?[\d.]+),\s+(-?[\d.]+)\s+\]", r"[\1, \2]",
                  json.dumps(rec, indent=1)) + "\n"
    listed = {e.get("id") for e in json.loads(INDEX.read_text()).get("enclosures", [])}
    fail = False
    if bad:
        fail = True
        print("MERGED OPENINGS (T-1984)")
        for m in bad:
            print("  - " + m)
    if rec["id"] not in listed:
        fail = True
        print(f"ENTRANCES: {INDEX.relative_to(ROOT)} does not list {rec['id']}")
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"ENTRANCE DRIFT\n  - {OUT.relative_to(ROOT)} does not re-derive; run "
                  "python3 tools/generate_entrances.py")
            return 1
        if fail:
            return 1
        print(f"entrances: {len(rec['entrances'])} doors on "
              f"{len(rec['belongs_to'])} buildings, each with its apron; no two holes "
              "on a read front run together")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rec['entrances'])} doors, "
          f"unread {rec['unread']}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
