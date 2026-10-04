#!/usr/bin/env python3
"""derive_settled_town_extent.py — the settled town's ground, derived from what is built (T-2084).

WHY THIS EXISTS. `data/flora/zones/z10_settled_town.json` is the one sward in the
dataset that is already the right thing for a town: "a cropped, hoof-poached, dusty
weedy halo", Poa at 0.05-0.20 m, nearly half bare soil. Its extent was a hand-drawn
polygon at the forks, "drawn around the eight structures the 1835 scene actually
places". The scene now places 560, and on 2026-10-04 19 of them stood inside it: every
other house, store and yard stood in a prairie community chosen by the terrain — wet
prairie, cordgrass to 2 m, prairie dock to 3 m. The owner walked through it ("dense
foliage, and a lot of grass and flowers" in the back yards, along the roads, before
the stores) and asked for a town that reads as lived in, not "just dropped on a
prairie".

THE RULE, and every number in it is the record's own:

  * SEEDS — everything the 1835 town has built or laid out: every block of the
    committed plat (`data/traces/vectors/thompson_lots.json`, all five grids, alleys
    inside them), the footprint of every structure standing on the scene date
    (`data/structures/*.json`, first phase, rotated as placed), and the forks
    polygon the record carried until T-2084 (FORKS_SEED below, so no ground that
    was town before stops being town; it lives here and not in the record because
    the record ships to the browser and no renderer would read it).
  * HALO — the seeds grown by the grazed halo at the LOW end of the dossier's
    50-200 m (`docs/research/02-flora.md` § ZONE 10), the end the record already
    used. The street corridors and alleys between blocks are inside it by
    construction: the widest platted street is 30 m and the halo reaches 50 m from
    each block face. The tool still measures every corridor and prints how much of
    each runs through town ground, so a street that does not is named.
  * THE BEACH, held out. Within z08_lakeshore's own band of the lake's edge (its
    `distance_m` far edge plus its `ramp_m`, read off the record, measured from the
    edge validate.py and lakeshore.js both derive from the 1835 heightfield) the
    beach community keeps the sand. Behind the beach the North Division's houses
    stand on sand prairie — big bluestem to 0.9 m — and they get the town's ground
    like every other lot; the ground COLOUR there stays the sand's, because
    terrain.js paints only box and shore zones. Structures inside the band (the
    piers, the fort by the harbour mouth) are named in the report with that reason
    rather than counted silently.
  * THE PUBLIC SQUARE, held out. z03_sedge_meadow names the square as slough by
    name and admits it as an `include_polygons` patch; the town at a higher
    priority would take it, so the patch is carried here as an `exclude_polygons`
    ring and the sedge keeps the ground its dossier names.

The union is rasterised at CELL_M, grown with an exact Euclidean distance transform,
traced back into rings and simplified by SIMPLIFY_M. The largest ring is the
`polygon`, the others are `include_polygons` (the renderer and validate.py read both
the same way), holes are `exclude_polygons`, and `box` is the bounds, so a point
outside the town costs flora.js one comparison.

Nothing about the trees moves. `trees.js` places timber from the heightfield and
asks flora.js's classifier only for the dune (T-2084 § 3 asks that the relict wood
not grow with the extent, and by construction it cannot).

    python3 tools/derive_settled_town_extent.py --write   # rewrite the record and the manifest
    python3 tools/derive_settled_town_extent.py --check   # fail if either drifted (check.sh)
    python3 tools/derive_settled_town_extent.py           # report only
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ZONE = DATA / "flora" / "zones" / "z10_settled_town.json"
SEDGE = DATA / "flora" / "zones" / "z03_sedge_meadow.json"
INDEX = DATA / "flora" / "index.json"
PLAT = DATA / "traces" / "vectors" / "thompson_lots.json"
STREETS = DATA / "streets" / "1835.json"
DATUM = DATA / "datum.json"

SCENE_DATE = "1835-07-01"
HALO_M = 50.0          # § ZONE 10's grazed halo, low end of 50-200 m
SHORE = DATA / "flora" / "zones" / "z08_lakeshore.json"
CELL_M = 4.0
SIMPLIFY_M = 3.0
PAD_M = HALO_M + 3 * CELL_M
# z10_settled_town's hand-drawn extent until T-2084, "drawn around the eight
# structures the 1835 scene actually places" at the forks, sources
# chicagology_prefire278 and chicagology_prefire273. Kept whole as a seed.
FORKS_SEED = [[-160, -14], [-146, -112], [-96, -150], [20, -176], [96, -186],
              [164, -152], [186, -96], [168, -38], [104, 2], [10, 16], [-72, 10]]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def standing(rng: dict | None) -> bool:
    if not rng:
        return True
    lo, hi = rng.get("from"), rng.get("to")
    return (not lo or str(lo) <= SCENE_DATE) and (not hi or str(hi) >= SCENE_DATE)


def footprints():
    """(id, ring in scene-local metres) for every structure standing on the scene date."""
    datum = load(DATUM)
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    out, skipped = [], []
    for f in sorted(glob.glob(str(DATA / "structures" / "*.json"))):
        rec = load(Path(f))
        phase = (rec.get("phases") or [{}])[0]
        pos = phase.get("position") or {}
        if pos.get("utm_e") is None:
            skipped.append((rec.get("id"), "no position"))
            continue
        if not standing(phase.get("documented_range")):
            skipped.append((rec.get("id"), "not standing on " + SCENE_DATE))
            continue
        e0, n0 = pos["utm_e"] - oe, pos["utm_n"] - on
        poly = (phase.get("footprint") or {}).get("polygon") or [[0, 0]]
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        a = math.radians(-(pos.get("rotation_deg") or 0.0))
        ring = []
        for x, y in poly:
            dx, dy = x - cx, y - cy
            ring.append((e0 + dx * math.cos(a) - dy * math.sin(a),
                         n0 + dx * math.sin(a) + dy * math.cos(a)))
        out.append((rec["id"], ring, (e0, n0)))
    return out, skipped


def fill(mask, ring, e0, n0):
    """Set every cell whose centre lies in `ring` (even-odd), plus the cell under each vertex."""
    pts = np.asarray(ring, dtype=float)
    rows, cols = mask.shape
    c0 = max(0, int((pts[:, 0].min() - e0) // CELL_M))
    c1 = min(cols - 1, int((pts[:, 0].max() - e0) // CELL_M) + 1)
    r0 = max(0, int((pts[:, 1].min() - n0) // CELL_M))
    r1 = min(rows - 1, int((pts[:, 1].max() - n0) // CELL_M) + 1)
    ce = e0 + (np.arange(c0, c1 + 1) + 0.5) * CELL_M
    cn = n0 + (np.arange(r0, r1 + 1) + 0.5) * CELL_M
    E, N = np.meshgrid(ce, cn)
    inside = np.zeros(E.shape, dtype=bool)
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if yi != yj:
            cross = ((yi > N) != (yj > N)) & (E < (xj - xi) * (N - yi) / (yj - yi) + xi)
            inside ^= cross
        j = i
    mask[r0:r1 + 1, c0:c1 + 1] |= inside
    for x, y in pts:
        c, r = int((x - e0) // CELL_M), int((y - n0) // CELL_M)
        if 0 <= r < rows and 0 <= c < cols:
            mask[r, c] = True


def trace(mask):
    """Cell-edge rings with the inside on the LEFT: outer rings run counter-clockwise."""
    m = np.pad(mask, 1)
    rows, cols = m.shape
    nxt = {}
    # Directed unit edges on the lattice of cell corners (c, r), inside on the left.
    # Corners are (c, r) on the padded lattice; heading east the left hand is north,
    # heading north it is west.
    ys, xs = np.nonzero(m[1:, :] != m[:-1, :])
    for r, c in zip(ys + 1, xs):            # horizontal edge, row r-1 south of it, row r north
        if m[r, c]:                          # inside to the north: run east
            nxt.setdefault((c, r), []).append((c + 1, r))
        else:                                # inside to the south: run west
            nxt.setdefault((c + 1, r), []).append((c, r))
    ys, xs = np.nonzero(m[:, 1:] != m[:, :-1])
    for r, c in zip(ys, xs + 1):            # vertical edge, col c-1 west of it, col c east
        if m[r, c]:                          # inside to the east: run south
            nxt.setdefault((c, r + 1), []).append((c, r))
        else:                                # inside to the west: run north
            nxt.setdefault((c, r), []).append((c, r + 1))
    rings = []
    while nxt:
        start = next(iter(nxt))
        ring = [start]
        cur, prev_dir = start, None
        while True:
            outs = nxt[cur]
            if len(outs) == 1:
                nb = outs.pop()
            else:  # a pinch: turn left first, so diagonal cells stay separate rings
                def turn(p):
                    d = (p[0] - cur[0], p[1] - cur[1])
                    if prev_dir is None:
                        return 0
                    cross = prev_dir[0] * d[1] - prev_dir[1] * d[0]
                    return -cross
                outs.sort(key=turn)
                nb = outs.pop(0)
            if not outs:
                del nxt[cur]
            prev_dir = (nb[0] - cur[0], nb[1] - cur[1])
            cur = nb
            if cur == start:
                break
            ring.append(cur)
        rings.append(ring)
    return rings


def simplify(pts, tol):
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        L = math.hypot(x2 - x1, y2 - y1) or 1e-9
        best, idx = 0.0, None
        for i in range(a + 1, b):
            x0, y0 = pts[i]
            d = abs((x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1)) / L
            if d > best:
                best, idx = d, i
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def area(ring):
    return 0.5 * sum(ring[i - 1][0] * ring[i][1] - ring[i][0] * ring[i - 1][1]
                     for i in range(len(ring)))


def pip(ring, e, n):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > n) != (yj > n) and e < (xj - xi) * (n - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def lake_line():
    """The 1835 lake edge, E per N, from the same code validate.py checks the sward with."""
    sys.path.insert(0, str(ROOT / "tools"))
    import validate  # noqa: E402 — the one reading of the shore, not a second copy
    epoch = load(DATA / "scenes" / "1835.json")["terrain_epoch"]
    field = validate.Heightfield.load(DATA / "terrain" / "epochs" / epoch)
    line = validate._lake_shore_line(field)
    ext = load(SHORE)["extent"]
    reach = (ext.get("distance_m") or [0, 0])[1] + (ext.get("ramp_m") or 0)
    return (lambda n: validate._shore_e(line, n)), reach


def derive():
    zone = load(ZONE)
    shore_e, beach_m = lake_line()
    seed = FORKS_SEED
    plat = load(PLAT)
    blocks = [(b["id"], b["boundary_local_enu_m"]) for b in plat["blocks"]
              if b.get("boundary_local_enu_m")]
    feet, skipped = footprints()
    sedge = load(SEDGE)["extent"].get("include_polygons") or []

    every = [p for _, r in blocks for p in r] + [p for _, r, _ in feet for p in r] + list(seed)
    e0 = math.floor((min(p[0] for p in every) - PAD_M) / CELL_M) * CELL_M
    n0 = math.floor((min(p[1] for p in every) - PAD_M) / CELL_M) * CELL_M
    e1 = max(p[0] for p in every) + PAD_M
    n1 = max(p[1] for p in every) + PAD_M
    cols = int(math.ceil((e1 - e0) / CELL_M))
    rows = int(math.ceil((n1 - n0) / CELL_M))
    built = np.zeros((rows, cols), dtype=bool)
    for _, ring in blocks:
        fill(built, ring, e0, n0)
    for _, ring, _ in feet:
        fill(built, ring, e0, n0)
    fill(built, seed, e0, n0)
    dist = ndimage.distance_transform_edt(~built) * CELL_M
    town = dist <= HALO_M
    ce = e0 + (np.arange(cols) + 0.5) * CELL_M
    for r in range(rows):
        town[r, ce >= shore_e(n0 + (r + 0.5) * CELL_M) - beach_m] = False

    rings = []
    for ring in trace(town):
        pts = [(round(e0 + (c - 1) * CELL_M, 2), round(n0 + (r - 1) * CELL_M, 2)) for c, r in ring]
        # A closed ring has no chord to measure from: split it at the vertex farthest
        # from its first, and simplify the two open halves.
        far = max(range(len(pts)), key=lambda i: math.dist(pts[0], pts[i]))
        pts = simplify(pts[:far + 1], SIMPLIFY_M)[:-1] + simplify(pts[far:] + [pts[0]], SIMPLIFY_M)[:-1]
        if len(pts) >= 3:
            rings.append(pts)
    outers = sorted((r for r in rings if area(r) > 0), key=area, reverse=True)
    holes = [r for r in rings if area(r) < 0]
    for h in holes:  # an island inside a hole would be cut out again by exclude_polygons
        for o in outers:
            if pip(h, *o[0]) and area(o) < -area(h):
                raise SystemExit(f"an outer ring at {o[0]} sits inside a hole; the extent "
                                 "grammar cannot say that and this tool will not guess")
    allpts = [p for r in outers for p in r]
    extent = dict(zone["extent"])
    extent["kind"] = "polygon"
    extent["polygon"] = [list(p) for p in outers[0]]
    extent["include_polygons"] = [[list(p) for p in r] for r in outers[1:]]
    extent["exclude_polygons"] = [[list(p) for p in r] for r in holes] + sedge
    extent["box"] = {"e": [math.floor(min(p[0] for p in allpts)), math.ceil(max(p[0] for p in allpts))],
                     "n": [math.floor(min(p[1] for p in allpts)), math.ceil(max(p[1] for p in allpts))]}
    extent.pop("seed_polygon", None)
    extent.pop("derived_by", None)
    if not extent["include_polygons"]:
        del extent["include_polygons"]

    def inside(e, n):
        ok = pip(extent["polygon"], e, n) or any(pip(r, e, n) for r in extent.get("include_polygons", []))
        return ok and not any(pip(r, e, n) for r in extent["exclude_polygons"])

    report = {"blocks": len(blocks), "structures": len(feet), "skipped": skipped,
              "rings": len(outers), "holes": len(holes),
              "vertices": sum(len(r) for r in outers + holes),
              "area_ha": round(math.fsum([area(r) for r in outers] + [area(r) for r in holes]) / 1e4, 1),
              "outside": [], "corridors": []}
    for sid, _, (e, n) in feet:
        if not inside(e, n):
            why = (f"within {beach_m:g} m of the lake's edge — the beach community keeps it"
                   if e >= shore_e(n) - beach_m else "in the public square's slough, which z03 keeps"
                   if any(pip(r, e, n) for r in sedge) else "UNEXPLAINED")
            report["outside"].append((sid, round(e), round(n), why))
    for s in load(STREETS)["streets"]:
        path = s["path_local_enu_m"]
        total = inn = 0.0
        for (xa, ya), (xb, yb) in zip(path, path[1:]):
            L = math.hypot(xb - xa, yb - ya)
            k = max(1, int(L // 10))
            for i in range(k):
                t = (i + 0.5) / k
                total += L / k
                if inside(xa + (xb - xa) * t, ya + (yb - ya) * t):
                    inn += L / k
        report["corridors"].append((s["id"], round(inn), round(total)))
    return zone, extent, report


def splice(path: Path, after_id: str | None, extent: dict) -> None:
    """Replace one `"extent"` value in place, leaving every other byte of the file as
    its author wrote it: both files are hand-formatted, and a whole-file re-dump would
    bury a one-key change under thousands of lines of whitespace."""
    text = path.read_text(encoding="utf-8")
    at = text.index(f'"id": "{after_id}"') if after_id else 0
    key = text.index('"extent":', at)
    start = text.index("{", key)
    _, used = json.JSONDecoder().raw_decode(text[start:])
    line_start = text.rfind("\n", 0, key) + 1
    pad = text[line_start:key]
    inner = pad + (" " if len(pad) == 1 else "  ")
    body = ",\n".join(f"{inner}{json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                      for k, v in extent.items())
    text = text[:start] + "{\n" + body + "\n" + pad + "}" + text[start + used:]
    path.write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    zone, extent, rep = derive()
    print(f"settled-town extent: {rep['blocks']} plat blocks, {rep['structures']} structures "
          f"standing on {SCENE_DATE}, the forks seed — grown {HALO_M:g} m, "
          f"{rep['rings']} ring(s), {rep['holes']} hole(s), {rep['vertices']} vertices, "
          f"{rep['area_ha']} ha")
    print(f"  structures inside: {rep['structures'] - len(rep['outside'])} of {rep['structures']}")
    for sid, e, n, why in rep["outside"]:
        print(f"    outside: {sid} at ({e}, {n}) — {why}")
    for sid, why in rep["skipped"]:
        print(f"    not counted: {sid} — {why}")
    part = [(s, i, t) for s, i, t in rep["corridors"] if 0 < i < t]
    full = sum(1 for _, i, t in rep["corridors"] if t and i == t)
    print(f"  street corridors wholly on town ground: {full} of {len(rep['corridors'])}; "
          f"{len(part)} leave it (country roads and the sand), "
          f"{sum(1 for _, i, _ in rep['corridors'] if i == 0)} never reach it")
    unexplained = [o for o in rep["outside"] if o[3] == "UNEXPLAINED"]

    index = load(INDEX)
    entry = next(z for z in index["zones"] if z["id"] == zone["id"])
    drift = zone["extent"] != extent or entry.get("extent") != extent
    if args.write:
        splice(ZONE, None, extent)
        splice(INDEX, zone["id"], extent)
        print(f"  wrote {ZONE.relative_to(ROOT)} and {INDEX.relative_to(ROOT)}")
    elif args.check:
        if drift:
            print("FAIL: z10_settled_town's extent (record or manifest) is not what the plat, the "
                  "structures and the seed derive — never hand-edit it; run "
                  "python3 tools/derive_settled_town_extent.py --write")
            return 1
        print("  the record and the manifest hold the derived extent")
    if unexplained:
        print(f"FAIL: {len(unexplained)} structure(s) outside the town with no stated reason")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
