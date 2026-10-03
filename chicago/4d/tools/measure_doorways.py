#!/usr/bin/env python3
"""Nothing stands in a doorway: every placed object in the town, against every door. (T-1984)

The owner, walking dev on 2026-10-02: *"often i will see goods or furntiture in front of
doors"*. The doors are `generate_entrances.doorway_zones()` — a door's width and a hand
either side, two paces out, read off the same front elevation the mesh is built from.
The objects are every layer that puts something down on the ground by coordinate:

* `data/yard/*` — goods, carts, wagons, benches, sheds, outbuildings, building stock;
* `data/frontage/*` — hitching posts, fittings and street fences (a building's OWN stoop
  is its doorway's floor and is not counted against it);
* `data/enclosures/*` — every fence run, as a line;
* `data/signage/` — the posts of the post-mounted boards;
* `data/wells/` and `data/flora/plantings/` — well heads and planted stems.

Before T-1984 it found 11 goods at 5 doors (taverns and boarding houses whose row of
casks was laid from the left end of the wall) and lot-line fences across 9 doors.

    python3 tools/measure_doorways.py          report
    python3 tools/measure_doorways.py --gate   ...and fail on any object in a doorway
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

import generate_entrances  # noqa: E402


def _inside(pt, ring) -> bool:
    x, y = pt
    hit = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def _seg_inside(a, b, ring) -> bool:
    n = max(2, int(math.dist(a, b) / 0.1))
    return any(_inside((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n), ring)
               for i in range(n + 1))


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a file another gate owns
        return None


def objects() -> list[tuple]:
    """`(layer, id, kind, point | None, segment | None, serves)` for every placed thing."""
    out = []
    for f in sorted((DATA / "yard").glob("*.json")):
        d = _load(f)
        if not isinstance(d, dict):
            continue
        for key in ("lots", "frontages"):
            for lot in d.get(key) or []:
                for it in lot.get("items", []):
                    out.append((f.name, lot.get("structure_id") or lot.get("id"),
                                it.get("kind"), it["at_local_enu_m"], None, None))
        for key in ("benches", "wagons", "sheds", "outbuildings"):
            for it in d.get(key) or []:
                if "at_local_enu_m" in it:
                    out.append((f.name, it.get("id"), it.get("kind", key),
                                it["at_local_enu_m"], None, None))
    for f in sorted((DATA / "frontage").glob("*.json")):
        d = _load(f)
        if not isinstance(d, dict):
            continue
        for it in d.get("posts") or []:
            out.append((f.name, it.get("id"), "post", it["at_local_enu_m"], None, None))
        for it in d.get("fittings") or []:
            for pt in it.get("parts", []):
                out.append((f.name, it.get("id"), f"{it['kind']}:{pt.get('part', '')}",
                            pt["at_local_enu_m"], None,
                            it.get("serves") if it["kind"] == "stoop" else None))
        for it in d.get("fences") or []:
            p = it.get("path_local_enu_m", [])
            for i in range(len(p) - 1):
                out.append((f.name, it.get("id"), "fence", None, (p[i], p[i + 1]), None))
    for f in sorted((DATA / "enclosures").glob("*.json")):
        d = _load(f)
        if not isinstance(d, dict) or "runs" not in d:
            continue
        for r in d.get("runs", []):
            p = r.get("path_local_enu_m", [])
            for i in range(len(p) - 1):
                out.append((f.name, r.get("id"), "fence", None, (p[i], p[i + 1]), None))
    signs = _load(DATA / "signage" / "town_business_signboards.json") or {}
    for sg in signs.get("signs", []):
        if sg.get("mounting") == "post_board":
            b = math.radians(sg["facade_bearing_deg"])
            st = (sg.get("geometry") or {}).get("stand_m", 1.9)
            a = sg["anchor_local_enu_m"]
            out.append(("signage", sg["structure_id"], "sign post",
                        [a[0] + math.sin(b) * st, a[1] + math.cos(b) * st], None, None))
    for f in sorted((DATA / "wells").glob("*.json")):
        d = _load(f)
        for w in (d.get("wells") if isinstance(d, dict) else None) or []:
            if "at_local_enu_m" in w:
                out.append(("wells", w.get("id"), "well", w["at_local_enu_m"], None, None))
    for f in sorted((DATA / "flora" / "plantings").glob("*.json")):
        d = _load(f)
        for s in (d.get("stems") if isinstance(d, dict) else None) or []:
            if "at_local_enu_m" in s:
                out.append((f.name, s.get("id"), s.get("species", "stem"),
                            s["at_local_enu_m"], None, None))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    args = ap.parse_args()
    zones = generate_entrances.doorway_zones()
    objs = objects()
    hits = []
    for eid, ring in zones:
        sid = eid.split("__")[0]
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        box = (min(xs) - 0.5, max(xs) + 0.5, min(ys) - 0.5, max(ys) + 0.5)
        for layer, oid, kind, pt, seg, serves in objs:
            if serves == sid:
                continue                      # the door's own stoop is its floor
            if pt is not None:
                if not (box[0] <= pt[0] <= box[1] and box[2] <= pt[1] <= box[3]):
                    continue
                if _inside(pt, ring):
                    hits.append((eid, layer, oid, kind))
            else:
                a, b = seg
                if max(a[0], b[0]) < box[0] or min(a[0], b[0]) > box[1] \
                        or max(a[1], b[1]) < box[2] or min(a[1], b[1]) > box[3]:
                    continue
                if _seg_inside(a, b, ring):
                    hits.append((eid, layer, oid, kind))
    print(f"doorways: {len(zones)} doors against {len(objs)} placed objects — "
          f"{len(hits)} object(s) standing in a doorway")
    for eid, layer, oid, kind in hits:
        print(f"  - {kind} ({layer}: {oid}) stands in the doorway of {eid}")
    return 1 if (args.gate and hits) else 0


if __name__ == "__main__":
    sys.exit(main())
