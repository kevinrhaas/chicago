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

  **Each `lodge_camp` ground's worn patch is a rounded blob inscribed in its footprint, inset
  `INSET_M` from the rectangle's sides, its edge feathering `FEATHER_M` into the grass; the
  horse ground's patch is smaller (`HORSE_SHARE`), since a picket line grazes more than it
  wears.**

Not one coordinate is authored. Each blob is the record's own `footprint.polygon` and
`placement` (from its sidecar) taken to local ENU in the frame `docs/GLB-CONTRACT.md` fixes,
its corners rounded by a superellipse of exponent `ROUND_P`; `tools/check.sh` re-derives the
file byte for byte.

WHAT IS INVENTED, and docs/LIBERTIES.md L-1812-potawatomi-camp-2515 owns it: that the camp's
ground was worn bare, its extent, its rounded outline and its feather.

THE 1812 MANIFEST. `data/enclosures/1812/index.json` is written by
tools/generate_fort_parade_ground.py's `index_1812()`, which appends the entries this module's
`manifest_entries()` returns (agreed with T-3339, whose worn ground does the same).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "enclosures" / "1812" / "potawatomi_camp_1812_ground.json"
RECORD_ID = "potawatomi_camp_1812_ground"
ARCHETYPE = "lodge_camp"

# THE INVENTED NUMBERS.
INSET_M = 1.5       # the blob's edge stands this far inside the footprint's sides
FEATHER_M = 5.0     # and fades into the grass over this
ROUND_P = 3.0       # the superellipse that rounds its corners (2 an ellipse, large a box)
HORSE_SHARE = 0.85  # the horse ground's blob, as a share of its footprint's half-axes
SIDES = 28          # points round each blob


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


def blob(sc: dict) -> list[list[float]]:
    place = sc.get("placement") or {}
    poly = (sc.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3 or place.get("local_e") is None:
        raise SystemExit(f"CAMP GROUND: {sc.get('id')} carries no placed footprint")
    us, vs = [p[0] for p in poly], [p[1] for p in poly]
    cu, cv = (min(us) + max(us)) / 2.0, (min(vs) + max(vs)) / 2.0
    au, av = (max(us) - min(us)) / 2.0 - INSET_M, (max(vs) - min(vs)) / 2.0 - INSET_M
    if sc["id"].endswith("_horse_ground"):
        au, av = au * HORSE_SHARE, av * HORSE_SHARE
    ring = []
    for k in range(SIDES):
        t = 2.0 * math.pi * k / SIDES
        c, s = math.cos(t), math.sin(t)
        u = cu + au * math.copysign(abs(c) ** (2.0 / ROUND_P), c)
        v = cv + av * math.copysign(abs(s) ** (2.0 / ROUND_P), s)
        e, n = _to_enu(u, v, place)
        ring.append([_round(e), _round(n)])
    return ring


def derive() -> dict:
    groups = camps()
    rings = [blob(sc) for sc in groups]
    return {
        "_doc": (
            "THE WORN GROUND OF THE 1812 POTAWATOMI CAMP (T-3342). One rounded patch inside "
            "each lodge_camp ground's footprint, laid by renderers/web/js/yards.js as "
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
            "inset_m": INSET_M,
            "feather_m": FEATHER_M,
            "round_p": ROUND_P,
            "horse_share": HORSE_SHARE,
            "note": (
                "Each ground's footprint and placement are its record's; this layer adds only a "
                "reconstructed surface, its rounded outline and its feather."
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
            "sources": ["currey_1912_old_fort_dearborn", "kinzie_waubun_1856"],
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
            "feather_m": FEATHER_M,
            "fringe_note": (
                f"Each patch stands {INSET_M:.1f} m inside its footprint and feathers "
                f"{FEATHER_M:.1f} m into the grass, a wandering fade rather than a line."
            ),
        },
        "assertions": [
            {
                "id": "a_patch_for_every_camp_ground",
                "claim": "every lodge_camp record drawn in 1812 has its worn patch",
                "holds": len(rings) == len(groups) and len(groups) > 0,
            },
        ],
        "research_note": (
            "WHAT WOULD MOVE THIS OFF RECONSTRUCTION: a description or picture of the camp's "
            "ground, or a plan of where its lodges stood."
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
          f"{len(rec['structure_ids'])} camp ground(s) worn bare, feathered {FEATHER_M:.1f} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
