#!/usr/bin/env python3
"""Generate the worn ground of the 1812 Potawatomi camp (T-3342).

    python3 tools/generate_camp_ground_1812.py           write the record
    python3 tools/generate_camp_ground_1812.py --check   re-derive and diff, write nothing

WHY THIS EXISTS. The owner, 2026-11-03, of the camp the T-2515 records drew: *"the ground on
the camps should be correct"*. A camp where families had cooked, worked and walked between
lodges for days stood on ground worn bare round its yards and doors, not on the prairie's
standing grass. The yards layer already draws that ground (`worn_earth`, a working yard's
dusty bare dirt with trampled grass surviving at its edges, renderers/web/js/yards.js), so
each camp ground is laid as `worn_earth` and its edge feathers into the sward.

THE RULE, and it is a rule so it follows the records:

  **Each `lodge_camp` ground's worn patch is the ground its own camp stood and worked on: the
  outline, seen from the middle of the group, of a disc round every lodge, hearth, arbor, rack,
  store and stake the archetype lays (generators/archetypes/lodge_camp.py `layout`), each disc
  sized by what it is (`REACH_M`), smoothed and frayed by a slow wobble seeded from the record's
  id, and held inside the footprint grown `HOLD_M`; its edge feathers `FEATHER_M` into the
  grass.**

T-3342 drew each patch as a superellipse inscribed in its 36 x 28 m rectangle, so fourteen
grounds read from the air as fourteen identical rounded squares on a grid (the owner,
2026-11-08: *"the camps look oddly regular ... I would expect more variation, but check me on
that"*). He was right to doubt it. No source describes the camp of 1812 in rows or rounds:
Currey has "groups of Indian wigwams clustered along the creek", and the eyewitnesses of the
next great gathering at Chicago, the treaty of 1833, put the Potawatomi "encamped on all
sides on the wide, level prairie ... beneath the low wood which chequered them, on the sides
of the small river" (Latrobe), "many groups of tents" not far from the river (Latrobe again),
and "in groups in their wigwams scattered about on the prairie" (Andreas 1884 v1, quoting both
him and another visitor of that year). A group of families pitched round its own fire and
yard; so the ground wears where the lodges and the work are, and each group's is its own
shape. The lodges are not moved (T-3500's people stand at their doors).

Not one coordinate is authored. Every disc is an item the archetype lays from the record's own
counts and seed, taken to local ENU through the record's `footprint` frame and `placement` in
the frame `docs/GLB-CONTRACT.md` fixes; `tools/check.sh` re-derives the file byte for byte.

WHAT IS INVENTED, and docs/LIBERTIES.md L-1812-potawatomi-camp-2515 owns it: that the camp's
ground was worn bare, how far round each thing it wore (`REACH_M`), the wobble and the feather.

THE 1812 MANIFEST. `data/enclosures/1812/index.json` is written by
tools/generate_fort_parade_ground.py's `index_1812()`, which appends the entries this module's
`manifest_entries()` returns (agreed with T-3339, whose worn ground does the same).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "enclosures" / "1812" / "potawatomi_camp_1812_ground.json"
RECORD_ID = "potawatomi_camp_1812_ground"
sys.path.insert(0, str(ROOT / "generators"))
from archetypes import lodge_camp, lodge_camp_params  # noqa: E402
ARCHETYPE = "lodge_camp"

# THE INVENTED NUMBERS.
FEATHER_M = 5.0     # the patch fades into the grass over this
HOLD_M = 1.0        # and its edge stays inside the footprint grown by this
SIDES = 72          # rays round each patch
# How far round each thing the archetype lays the ground is worn bare, metres past its own
# half-size: a lodge's doorway and its eaves, a fire's ring of sitters, the work at a rack.
REACH_M = {
    "mat_lodge": 1.9, "bark_roofed": 1.9, "long_lodge": 2.1, "bark_house": 2.3,
    "arbor": 2.9, "hearth": 2.8, "drying_rack": 1.6, "mortar": 1.9, "woodpile": 1.5,
    "scaffold": 1.3, "hide_frame": 1.4, "bundle": 0.9, "canoe": 1.2, "picket": 2.6,
    "pack_saddle": 1.2,
}
# The things a family lives inside: walled to the ground, so no yard earth runs under them.
DWELLINGS = ("mat_lodge", "bark_roofed", "long_lodge", "bark_house")
# Each item's own half-size before its reach (the archetype's dimensions; a dome's is its
# size's half-length, read off the item).
HALF_M = {
    "long_lodge": 4.2, "bark_house": 3.4, "arbor": 1.8, "hearth": 0.6, "drying_rack": 1.5,
    "mortar": 0.3, "woodpile": 0.9, "scaffold": 1.0, "hide_frame": 0.8, "bundle": 0.5,
    "canoe": 2.6, "picket": 0.2, "pack_saddle": 0.6,
}
WOBBLE = 0.13       # the fray: the radius breathes this share in and out round the patch
BAY = 0.74          # a ray that meets nothing stops this share of the way to the patch's mean

def _round(x: float, places: int = 2) -> float:
    return round(x + 0.0, places)


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres (docs/GLB-CONTRACT.md; as the parade)."""
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def camps() -> list[dict]:
    out = []
    for p in sorted((DATA / "sidecars" / "1812").glob("*.json")):
        if p.name == "index.json":
            continue
        sc = json.loads(p.read_text(encoding="utf-8"))
        if sc.get("archetype") == ARCHETYPE:
            out.append(sc)
    return out


def _items(sc: dict) -> list[tuple[str, float, float, float]]:
    """Every item the archetype lays for this record, as (kind, u, v, reach) in the
    footprint's frame (the archetype's x, y ARE the footprint's u, v: lodge_camp.glb writes
    (x, y, z) as glTF (x, z, -y), as every footprint is read)."""
    rec = json.loads((DATA / "structures" / f"{sc['id']}.json").read_text(encoding="utf-8"))
    phase = next(p for p in rec["phases"] if p["id"] == sc.get("phase", rec["phases"][0]["id"]))
    params = lodge_camp_params.from_phase(phase, rec)
    out = []
    for kind, x, y, _rot, extra in lodge_camp.layout(params):
        if kind in ("mat_lodge", "bark_roofed"):
            half = max(extra[0], extra[1]) / 2.0
        else:
            half = HALF_M.get(kind, 0.5)
        out.append((kind, x, y, half + REACH_M.get(kind, 1.2)))
    return out


# T-3526: the plan of every dwelling the archetype stands on a ground, which yards.js leaves
# its earth out from under. Each is (half-width across the door axis, half-length along it,
# superellipse exponent) of what lodge_camp builds: a dome's plan is the _Dome's (a, b, p)
# at its foot, a long lodge's the same with p 2.8, a bark house's its oblong of walls.
def _dwelling_plan(kind: str, extra) -> tuple[float, float, float]:
    if kind == "bark_house":
        return lodge_camp_params.BARK_HOUSE[0] / 2.0, lodge_camp_params.BARK_HOUSE[1] / 2.0, 8.0
    if kind == "long_lodge":
        return lodge_camp_params.LONG_LODGE[0] / 2.0, lodge_camp_params.LONG_LODGE[1] / 2.0, 2.8
    return extra[0] / 2.0, extra[1] / 2.0, 2.0


def dwellings(sc: dict) -> list[list[float]]:
    """Every dwelling on this ground as [e, n, half_x, half_y, axis_deg, p] in local ENU:
    its centre, its plan's half-axes along and across its own x axis, that axis's bearing
    counter-clockwise from east, and its superellipse exponent."""
    rec = json.loads((DATA / "structures" / f"{sc['id']}.json").read_text(encoding="utf-8"))
    phase = next(p for p in rec["phases"] if p["id"] == sc.get("phase", rec["phases"][0]["id"]))
    params = lodge_camp_params.from_phase(phase, rec)
    place = sc.get("placement") or {}
    out = []
    for kind, x, y, rot, extra in lodge_camp.layout(params):
        if kind not in DWELLINGS:
            continue
        hx, hy, p = _dwelling_plan(kind, extra)
        e, n = _to_enu(x, y, place)
        th = math.radians(rot)
        e1, n1 = _to_enu(x + math.cos(th), y + math.sin(th), place)
        axis = math.degrees(math.atan2(n1 - n, e1 - e))
        out.append([_round(e), _round(n), _round(hx), _round(hy), _round(axis, 1), p])
    return out


def window(sc: dict):
    """The days a camp ground is drawn (T-3527): its record's documented_range where that
    range says `drawn_only_within`, else None (drawn every day)."""
    rng = sc.get("documented_range") or {}
    if rng.get("drawn_only_within") is not True:
        return None
    return {"from": rng["from"], "to": rng["to"]}


def _wobble(seed_name: str):
    """A slow, seeded, zero-mean breathing round the patch: three harmonics, phases off the
    record's id (crc32, as the archetype seeds), so no two patches fray alike."""
    h = zlib.crc32(seed_name.encode("utf-8"))
    ph = [((h >> (8 * k)) & 0xFF) / 255.0 * 2.0 * math.pi for k in range(3)]
    ks = (2 + h % 2, 3 + (h >> 3) % 3, 7 + (h >> 7) % 4)
    return lambda t: (0.55 * math.sin(ks[0] * t + ph[0]) + 0.30 * math.sin(ks[1] * t + ph[1])
                      + 0.15 * math.sin(ks[2] * t + ph[2]))


def _ray_rect(cu, cv, c, s, u0, u1, v0, v1) -> float:
    """How far a ray from (cu, cv) runs before it leaves the rectangle."""
    t = 1e9
    if c > 1e-9:
        t = min(t, (u1 - cu) / c)
    elif c < -1e-9:
        t = min(t, (u0 - cu) / c)
    if s > 1e-9:
        t = min(t, (v1 - cv) / s)
    elif s < -1e-9:
        t = min(t, (v0 - cv) / s)
    return max(0.5, t)


def blob(sc: dict) -> list[list[float]]:
    place = sc.get("placement") or {}
    poly = (sc.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3 or place.get("local_e") is None:
        raise SystemExit(f"CAMP GROUND: {sc.get('id')} carries no placed footprint")
    items = _items(sc)
    if not items:
        raise SystemExit(f"CAMP GROUND: {sc['id']}: the archetype lays nothing on this ground")
    us, vs = [p[0] for p in poly], [p[1] for p in poly]
    u0, u1 = min(us) - HOLD_M, max(us) + HOLD_M
    v0, v1 = min(vs) - HOLD_M, max(vs) + HOLD_M
    # the middle of the group: the items weighted by their reach, so the yards pull it
    wsum = math.fsum(r for _k, _x, _y, r in items)
    cu = math.fsum(x * r for _k, x, _y, r in items) / wsum
    cv = math.fsum(y * r for _k, _x, y, r in items) / wsum
    # each ray's far edge on the union of the discs
    raw = []
    for k in range(SIDES):
        t = 2.0 * math.pi * k / SIDES
        c, s = math.cos(t), math.sin(t)
        far = 0.0
        for _kind, x, y, r in items:
            dx, dy = x - cu, y - cv
            along = dx * c + dy * s
            off2 = dx * dx + dy * dy - along * along
            if off2 < r * r:
                far = max(far, along + math.sqrt(r * r - off2))
        raw.append(far)
    hit = [r for r in raw if r > 0]
    mean = math.fsum(hit) / len(hit)
    raw = [r if r > 0 else BAY * mean for r in raw]
    # smoothed round the circle (a trodden edge does not follow every eave), then frayed
    taps = (1, 2, 3, 4, 3, 2, 1)
    sm = [math.fsum(w * raw[(k + j - 3) % SIDES] for j, w in enumerate(taps)) / 16.0
          for k in range(SIDES)]
    wob = _wobble(sc["id"])
    ring = []
    for k in range(SIDES):
        t = 2.0 * math.pi * k / SIDES
        c, s = math.cos(t), math.sin(t)
        r = sm[k] * (1.0 + WOBBLE * wob(t))
        r = min(r, _ray_rect(cu, cv, c, s, u0, u1, v0, v1))
        e, n = _to_enu(cu + r * c, cv + r * s, place)
        ring.append([_round(e), _round(n)])
    # counter-clockwise in ENU, as every interior yards.js lays
    a2 = math.fsum(p[0] * q[1] - q[0] * p[1] for p, q in zip(ring, ring[1:] + ring[:1]))
    return ring if a2 > 0 else ring[::-1]


def _area(ring) -> float:
    return abs(math.fsum(p[0] * q[1] - q[0] * p[1] for p, q in zip(ring, ring[1:] + ring[:1]))) / 2.0


def _all_differ(rings, tol) -> bool:
    """Whether every pair of rings, each taken about its own mean vertex, differs at some
    vertex by more than `tol` (the rings are sampled on the same rays, so vertex k of one
    faces vertex k of the other)."""
    def centred(r):
        me = math.fsum(p[0] for p in r) / len(r)
        mn = math.fsum(p[1] for p in r) / len(r)
        return [(p[0] - me, p[1] - mn) for p in r]
    cs = [centred(r) for r in rings]
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            if len(cs[i]) == len(cs[j]) and max(math.hypot(a[0] - b[0], a[1] - b[1])
                                                for a, b in zip(cs[i], cs[j])) <= tol:
                return False
    return True


def derive() -> dict:
    groups = camps()
    rings = [blob(sc) for sc in groups]
    return {
        "_doc": (
            "THE WORN GROUND OF THE 1812 POTAWATOMI CAMP (T-3342, T-3511). One patch to each "
            "lodge_camp ground, worn round the lodges, fires and yards the archetype lays there, laid by renderers/web/js/yards.js as "
            "`worn_earth` and feathered into the sward. NOT ONE COORDINATE HERE IS AUTHORED - "
            "the rings are derived from the camp's sidecars in data/sidecars/1812/ by "
            "tools/generate_camp_ground_1812.py, and tools/check.sh re-derives this file byte "
            "for byte. IT DRAWS NO FENCE (`runs: []`). Every value is `reconstructed`; "
            "docs/LIBERTIES.md L-1812-potawatomi-camp-2515 states what bounds it."
        ),
        "id": RECORD_ID,
        "name": "The worn ground of the Potawatomi camp of August 1812",
        "kind": "camp_ground",
        "scene": "1812",
        "target_date": "1812-08-14",
        "structure_ids": [sc["id"] for sc in groups],
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin - the frame the "
            "sidecars' placement.local_e / local_n use."
        ),
        "derived_from": {
            "sidecars": [f"data/sidecars/1812/{sc['id']}.json" for sc in groups],
            "layout": "generators/archetypes/lodge_camp.py layout() (T-3511)",
            "reach_m": REACH_M,
            "hold_m": HOLD_M,
            "wobble": WOBBLE,
            "bay": BAY,
            "feather_m": FEATHER_M,
            "note": (
                "Each ground's footprint, placement, counts and seed are its record's, and the "
                "archetype lays its lodges and yards from them; this layer adds only a "
                "reconstructed surface, worn round what the archetype lays, and its feather."
            ),
        },
        "existence": {
            "confidence": "reconstructed",
            "note": (
                "That the camp stood on these grounds is the camp records' argument; that its "
                "ground was worn bare round the lodges and yards, fading raggedly into grass, is "
                "this project's reading of a camp lived in for days. "
                "docs/LIBERTIES.md L-1812-potawatomi-camp-2515."
            ),
            "sources": ["andreas_1884_v1", "currey_1912_old_fort_dearborn", "kinzie_waubun_1856"],
        },
        "runs": [],
        "runs_note": "EMPTY, AND DELIBERATELY. A camp is not fenced; there is no run to draw.",
        "ground": {
            "treatment": "worn_earth",
            "confidence": "reconstructed",
            "note": (
                "A working yard's treatment: bare dusty dirt with trampled grass surviving at "
                "its edges, the right reading for ground walked and worked between lodges."
            ),
            "interior_local_enu_m": rings,
            "interior_drawn_within": [window(sc) for sc in groups],
            "interior_drawn_within_note": (
                "T-3527: one entry to each ring above, in the same order: the days its camp "
                "stands, from that camp's record (documented_range with drawn_only_within), or "
                "null for a ground drawn every day. yards.js draws a ring's earth only on its "
                "days, as buildings.js draws the camp; on any other date the Season or a jaunt "
                "sets, the ground is the prairie's (the owner, 2026-11-08, chose that the camps "
                "come and go with the date)."
            ),
            "dwellings_local_enu_m": [d for sc in groups for d in dwellings(sc)],
            "dwellings_note": (
                "T-3526: the plan of every lodge and bark house standing on these grounds, as "
                "[e, n, half_x, half_y, axis_deg, p] (centre, half-axes along and across the "
                "dwelling's own x axis, that axis counter-clockwise from east, superellipse "
                "exponent), read off the archetype's layout like the rings. yards.js leaves its "
                "earth out from under each, so the bare ground drawn over the terrain cannot "
                "paint over a lodge's foot from a distance (the owner, 2026-11-08: the mat "
                "lodges seemed to float above the ground from far away). Nothing here claims "
                "evidence; the lodges' own records do."
            ),
            "feather_m": FEATHER_M,
            "fringe_note": (
                f"Each patch is worn round its own camp's lodges and yards, so no two are the "
                f"same shape, and feathers {FEATHER_M:.1f} m into the grass, a wandering fade "
                "rather than a line."
            ),
        },
        "assertions": [
            {
                "id": "a_patch_for_every_camp_ground",
                "claim": "every lodge_camp record drawn in 1812 has its worn patch",
                "holds": len(rings) == len(groups) and len(groups) > 0,
            },
            {
                "id": "a_no_two_patches_alike",
                "claim": "no two camp patches are the same shape: laid on each other by their middles, every pair differs somewhere by more than 1.5 m (T-3511: the owner saw fourteen alike)",
                "areas_m2": {sc["id"]: round(_area(r), 1) for sc, r in zip(groups, rings)},
                "holds": _all_differ(rings, 1.5),
            },
        ],
        "research_note": (
            "WHAT WOULD MOVE THIS OFF RECONSTRUCTION: a description or picture of the camp's "
            "ground, or a plan of where its lodges stood. T-3511 (2026-11-08) checked the "
            "regular look the owner questioned: Currey's 'groups of Indian wigwams clustered "
            "along the creek' and the 1833 treaty witnesses in Andreas ('encamped on all sides "
            "... beneath the low wood which chequered them', 'in groups in their wigwams "
            "scattered about on the prairie') describe groups, not rows or rounds, so each "
            "patch now follows its own group's lodges."
        ),
    }


def manifest_entries() -> list[dict]:
    """This module's lines in data/enclosures/1812/index.json (index_1812, T-3339)."""
    return [{"id": RECORD_ID, "file": OUT.name}]


def text(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()
    rec = derive()
    body = text(rec)
    bad = [f"assertion {a['id']} fails — {a['claim']}" for a in rec["assertions"] if not a["holds"]]
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != body:
            bad.append(f"{OUT.relative_to(ROOT)} is not what the rule derives — run "
                       "python3 tools/generate_camp_ground_1812.py")
    else:
        OUT.write_text(body, encoding="utf-8")
    index = DATA / "enclosures" / "1812" / "index.json"
    listed = {e.get("id") for e in json.loads(index.read_text(encoding="utf-8"))["enclosures"]}
    if RECORD_ID not in listed:
        bad.append(f"{index.relative_to(ROOT)} does not list {RECORD_ID} — run "
                   "python3 tools/generate_fort_parade_ground.py")
    if bad:
        print("CAMP GROUND FAIL\n  " + "\n  ".join(bad))
        return 1
    print(f"CAMP GROUND {'PASS' if args.check else 'written'} — "
          f"{len(rec['structure_ids'])} camp ground(s) worn round their own lodges, feathered {FEATHER_M:.1f} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
