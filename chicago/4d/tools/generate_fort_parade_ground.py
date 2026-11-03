#!/usr/bin/env python3
"""Generate the trodden ground of Fort Dearborn's parade, both forts (T-3320).

WHY THIS EXISTS. The owner, 2026-11-02, standing on the 1835 parade: *"can you improve the
texture of the ground so it is not a solid color but a more realistic texture that looks good
and also blur/gradient all the transitions from that to grass or dirt so there are not sharp
lines dividing ground surfaces"*. Both forts' parades were the fort_structure archetype's
6 cm proud box in one flat wall colour, so they read as a beige slab with a hard edge against
the sward. The apron outside the 1835 walls (T-0097, `generate_fort_apron.py`) already draws
as the yards layer's `trodden_earth` — the grit tile, the darker trodden tone, and a fringe
that feathers into the sward — and looks right. This record puts the parade on the same
treatment, and `renderers/web/js/buildings.js` leaves the slab out (fort-gates.js
`paradeLaidAsGround`).

THE RULE, and it is a rule rather than a drawn polygon so it follows the fort:

  **Each fort's parade footprint, in its own committed placement, is trodden earth; its edge
  feathers into the sward over `FEATHER_M` metres.**

Not one coordinate is authored. The ring is the parade record's `footprint.polygon` and
`placement` taken to local ENU in the frame `docs/GLB-CONTRACT.md` fixes (the same three lines
the apron uses), and `tools/check.sh` re-derives every file here byte for byte.

WHAT IS INVENTED, and docs/LIBERTIES.md L-t3320-parade-ground owns it: that the parade's
ground was bare trodden earth rather than grass (the records say "the open ground" and "worn
bare and packed by a garrison" is the archetype's own reading of it, never a source's); the
treatment's colour and grain; and the feather — how far and how raggedly the trodden earth
gives way to grass beyond the parade's edge. `FEATHER_M` is one number for both forts, sized
so the fade finishes well inside the walls (asserted below).

1812 IS ITS OWN FOLDER. The enclosures layer was 1835's alone; 1812 draws it from
`data/enclosures/1812/` (`enclosures_dir` in data/scenes/1812.json), which holds this record
and nothing else, so no 1835 fence or yard can reach the first fort's scene.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENCLOSURES = DATA / "enclosures"

# THE ONE INVENTED NUMBER. yards.js lays the fade's wandering middle at 0.4 +/- 0.4 of
# this past the ring, so 5 m gives trodden tongues reaching 0.5-4 m into the grass. The
# 1835 parade stands 8-15 m inside its stockade and the 1812 one 5.4-6.2 m inside its inner
# pickets, so the whole skirt stays inside the walls on both (asserted).
FEATHER_M = 5.0

FORTS = [
    {
        "scene": "1835",
        "target_date": "1835-07-01",
        "parade": "fort_dearborn_parade",
        "walls": "fort_dearborn_palisade",
        "out": ENCLOSURES / "fort_dearborn_parade_ground.json",
        "id": "fort_dearborn_parade_ground",
        "name": "The trodden ground of Fort Dearborn's parade",
    },
    {
        "scene": "1812",
        "target_date": "1812-08-14",
        "parade": "first_fort_dearborn_parade",
        "walls": "first_fort_dearborn_pickets_inner",
        "out": ENCLOSURES / "1812" / "first_fort_dearborn_parade_ground.json",
        "id": "first_fort_dearborn_parade_ground",
        "name": "The trodden ground of the first Fort Dearborn's parade",
    },
]
INDEX_1812 = ENCLOSURES / "1812" / "index.json"


def _round(x: float, places: int = 2) -> float:
    return round(x + 0.0, places)


def _to_enu(u: float, v: float, place: dict) -> tuple[float, float]:
    """A footprint coordinate to local ENU metres (docs/GLB-CONTRACT.md; as the apron)."""
    th = math.radians(-(place.get("rotation_deg") or 0.0))
    x, z = u, -v
    xr = x * math.cos(th) + z * math.sin(th)
    zr = -x * math.sin(th) + z * math.cos(th)
    return (place.get("local_e") or 0.0) + xr, (place.get("local_n") or 0.0) - zr


def _point_in_ring(pts: list, e: float, n: float) -> bool:
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > n) != (yj > n) and e < (xj - xi) * (n - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _sidecar(scene: str, sid: str) -> dict:
    return json.loads((DATA / "sidecars" / scene / f"{sid}.json").read_text(encoding="utf-8"))


def _box(poly: list) -> tuple[float, float, float, float]:
    return (min(p[0] for p in poly), max(p[0] for p in poly),
            min(p[1] for p in poly), max(p[1] for p in poly))


def derive(fort: dict) -> dict:
    parade = _sidecar(fort["scene"], fort["parade"])
    walls = _sidecar(fort["scene"], fort["walls"])
    place = parade.get("placement") or {}
    poly = (parade.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3 or place.get("local_e") is None:
        raise SystemExit(f"PARADE GROUND: {fort['parade']} carries no placed footprint")
    ring = [[_round(e), _round(n)] for e, n in (_to_enu(u, v, place) for u, v in poly)]

    # THE FEATHER STAYS INSIDE THE WALLS: the parade ring pushed out FEATHER_M on all sides,
    # in the parade's own frame, must stand inside the stockade's footprint, so the fade
    # never reaches the apron's ground or the pickets.
    u0, u1, v0, v1 = _box(poly)
    f = FEATHER_M
    skirt = [_to_enu(u, v, place) for u, v in
             ((u0 - f, v0 - f), (u1 + f, v0 - f), (u1 + f, v1 + f), (u0 - f, v1 + f))]
    wplace = walls.get("placement") or {}
    wpoly = (walls.get("footprint") or {}).get("polygon") or []
    wring = [_to_enu(u, v, wplace) for u, v in wpoly]
    inside = all(_point_in_ring(wring, e, n) for e, n in skirt)

    # NO OTHER RECORD ALREADY TREATS THIS GROUND (as the apron asserts of itself).
    clashes = []
    folder = fort["out"].parent
    for path in sorted(folder.glob("*.json")):
        if path.name in ("index.json", fort["out"].name):
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        # A door's path (`road_earth`, town_entrance_aprons) is ground that runs from a
        # building's door ONTO the open ground before it, and the officers' quarters'
        # does exactly that on the parade's west edge. That is a path meeting the parade,
        # not a second claim about the parade's surface, so it is not a clash.
        if (rec.get("ground") or {}).get("treatment") == "road_earth":
            continue
        authored = (rec.get("ground") or {}).get("interior_local_enu_m")
        rings = []
        if isinstance(authored, list) and authored and isinstance(authored[0], list):
            rings = authored if isinstance(authored[0][0], list) else [authored]
        for other in rings:
            if any(_point_in_ring(other, e, n) for e, n in ring) \
                    or any(_point_in_ring(ring, e, n) for e, n in other):
                clashes.append(rec.get("id"))

    kind = (parade.get("attributes") or {}).get("kind") or {}
    sources = sorted(set((kind.get("sources") or []) + (place.get("position_sources") or [])))
    return {
        "_doc": (
            "THE TRODDEN GROUND OF THE FORT'S PARADE (T-3320). The parade's own footprint, "
            "laid by renderers/web/js/yards.js as `trodden_earth` and feathered into the "
            "sward, in place of the archetype's flat 6 cm slab (which buildings.js leaves "
            "out). NOT ONE COORDINATE HERE IS AUTHORED - the ring is derived from "
            f"data/sidecars/{fort['scene']}/{fort['parade']}.json by "
            "tools/generate_fort_parade_ground.py and tools/check.sh re-derives this file byte "
            "for byte. IT DRAWS NO FENCE (`runs: []`). Every value is `reconstructed`; "
            "docs/LIBERTIES.md L-t3320-parade-ground states what bounds it."
        ),
        "id": fort["id"],
        "name": fort["name"],
        "kind": "parade_ground",
        "scene": fort["scene"],
        "target_date": fort["target_date"],
        "structure_id": fort["parade"],
        "coordinates": (
            "Local East-North-Up metres from data/datum.json's origin - the frame the "
            "sidecars' placement.local_e / local_n use."
        ),
        "derived_from": {
            "sidecar": f"data/sidecars/{fort['scene']}/{fort['parade']}.json",
            "placement_local_enu_m": [place.get("local_e"), place.get("local_n")],
            "rotation_deg": place.get("rotation_deg"),
            "footprint_frame_m": {"u": [_round(u0), _round(u1)], "v": [_round(v0), _round(v1)]},
            "feather_m": FEATHER_M,
            "note": (
                "The parade's footprint and placement are the record's (inferred); this ground "
                "inherits them and adds only a reconstructed surface and its feather."
            ),
        },
        "existence": {
            "confidence": "reconstructed",
            "note": (
                "That the parade was open ground is the parade record's; that it was bare, "
                "trodden earth fading raggedly into grass at its edges is this project's "
                "reading of a garrison's drill ground. docs/LIBERTIES.md L-t3320-parade-ground."
            ),
            "sources": sources,
        },
        "runs": [],
        "runs_note": (
            "EMPTY, AND DELIBERATELY. The parade is open ground between the fort's own "
            "buildings; there is no fence for this record to draw."
        ),
        "ground": {
            "treatment": "trodden_earth",
            "confidence": "reconstructed",
            "note": (
                "The apron's treatment (fort_dearborn_apron, L174): finer and darker than a "
                "wagon yard, without ruts, so the fort's ground reads as one surface inside "
                "and outside its walls."
            ),
            "interior_local_enu_m": ring,
            "fringe_ring_local_enu_m": ring,
            "feather_m": FEATHER_M,
            "fringe_note": (
                f"The sward feathers in from the parade's own edge over {FEATHER_M:.1f} m, a "
                "wandering ragged fade rather than a line - the owner's ask."
            ),
        },
        "assertions": [
            {
                "id": "the_feather_stays_inside_the_walls",
                "claim": f"the parade ring pushed out {FEATHER_M:.1f} m on every side stands "
                         f"inside {fort['walls']}'s footprint, so the fade never reaches the "
                         "pickets or the ground outside them",
                "holds": inside,
            },
            {
                "id": "no_other_treated_ground_here",
                "claim": "no other enclosure record in this scene already lays an area "
                         "treatment on the parade (a door's road_earth path may run onto it)",
                "clashes": sorted(set(clashes)),
                "holds": not clashes,
            },
        ],
        "research_note": (
            "WHAT WOULD MOVE THIS OFF RECONSTRUCTION: a garrison description, return or "
            "drawing that shows the parade's surface - grass, gravel or bare earth."
        ),
    }


def index_1812() -> dict:
    return {
        "_doc": (
            "Manifest for the 1812 scene's enclosure layer (T-3320), read because "
            "data/scenes/1812.json names `enclosures_dir: enclosures/1812/`. The 1835 "
            "manifest one folder up is the 1835 town's; this one holds the first fort's "
            "parade ground (T-3320) and the worn paths and yards of 1812 (T-3339). Written by "
            "tools/generate_fort_parade_ground.py and tools/generate_worn_ground_1812.py alike."
        ),
        "version": 1,
        "scene": "1812",
        "scene_date": "1812-08-14",
        "coordinates": "Local East-North-Up metres from data/datum.json's origin.",
        "enclosures": [{"id": "first_fort_dearborn_parade_ground",
                        "file": "first_fort_dearborn_parade_ground.json"}] + _worn_ground_entries(),
    }


def _worn_ground_entries() -> list[dict]:
    """T-3339: the worn paths and yards of 1812 share this manifest; their generator says
    which files it writes, so both tools write the same index."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from generate_worn_ground_1812 import manifest_entries
    return manifest_entries()


def text(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()
    outs = [(fort["out"], text(derive(fort))) for fort in FORTS]
    outs.append((INDEX_1812, text(index_1812())))
    bad = []
    for path, body in outs:
        rec = json.loads(body)
        for a in rec.get("assertions", []):
            if not a.get("holds"):
                bad.append(f"{path.relative_to(ROOT)}: assertion {a['id']} fails — {a['claim']}")
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                bad.append(f"{path.relative_to(ROOT)} is not what the rule derives — run "
                           "python3 tools/generate_fort_parade_ground.py")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
    # 1835's manifest is shared with the town; it must list this record.
    listed = {e.get("id") for e in
              json.loads((ENCLOSURES / "index.json").read_text(encoding="utf-8"))["enclosures"]}
    if FORTS[0]["id"] not in listed:
        bad.append(f"data/enclosures/index.json does not list {FORTS[0]['id']}")
    if bad:
        print("PARADE GROUND FAIL\n  " + "\n  ".join(bad))
        return 1
    print(f"PARADE GROUND {'PASS' if args.check else 'written'} — {len(FORTS)} parade(s) as "
          f"trodden earth feathered {FEATHER_M:.1f} m into the sward, inside their walls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
