"""How full the AO atlas is, and what one packing change does to it — T-2127.

Run under the pinned Blender (the one `tools/bake.sh` fetches), never plain Python:

    "$BLENDER_CACHE/blender-4.5.3-linux-x64/blender" -b -noaudio --factory-startup \\
        --python tools/measure_ao_atlas.py -- [--per-archetype 3] [--only a,b] \\
        [--margin-div 0.4] [--json docs/measurements/T-2127-ao-atlas-packing.json]

T-0158 measured the AO unwrap on ONE master, `sauganash_hotel`: 31.1 % of a 512²
atlas written. One asset is an anecdote about one unwrap (T-0286's acceptance says
so), so this reads a representative set — the first, middle and last structure of
every archetype the scenes resolve, plus `sauganash_hotel` as the calibration point —
and builds each master through the SAME code the bake runs (`emit.unwrap`,
`emit.bake_ao`, `emit.export_glb`), so the "before" column is the pipeline and not
a re-implementation of it. Three conditions per master:

- **before** — `emit.unwrap` as it ships, `smart_project(angle_limit=1.15,
  island_margin=0.02)`, baked at 512².
- **after** — THE CHANGE, `repack()` below, baked at 512²: the same atlas, so the
  occupancy and density figures are the packing's alone.
- **matched** — the change baked at the smallest atlas side whose wall density is
  still no lower than **before** on the named wall AND over all walls. That is what
  the occupancy is worth in bytes: the same texels per metre of wall, in fewer texels.

## Why the change is a lightmap pack, and not the margin, the angle or a pack pass

Measured while choosing it (docs/measurements/T-2127-ao-atlas-packing.md):

- **Every face is its own island.** These archetypes are boxes, and a box's faces
  meet at 90 degrees, past `smart_project`'s 66-degree limit — so `sauganash_hotel`
  is 626 islands for 626 faces, and the drawbridge 3,991 for 3,991. No angle limit
  joins them (the operator's maximum is 89 degrees), and welding the split vertices
  before the unwrap changed nothing.
- **`island_margin` does nothing here.** 0.02, 0.005 and 0 give the same occupancy, gap and
  density: with single-face islands the packer's gap is not that parameter.
- **So occupancy is island count times gap**, and the gap the shipped unwrap leaves is
  9 px centre to centre. `uv.pack_islands` at that same gap packs no better
  (`exchange_coffee_house` fell 31 -> 17 %) and at 3,991 islands packs to nothing.
- **`uv.lightmap_pack` is the operator built for exactly this** — one quad per face,
  laid edge to edge. `PREF_MARGIN_DIV=0.4` was chosen on a six-master sweep as the
  widest margin at which wall density held on all six; at 0.6 the calibration
  master's walls already fell below what ships.

## What the full set says: the change works, and it should not be adopted

Over 30 masters it takes occupancy from 20.5 % to 56.0 % of a 512² atlas — and the
occlusion PNGs from 3.14 MB to 6.12 MB. **T-0286's premise was that the empty two
thirds is bytes spent on nothing; it is not.** Texels no island owns are one constant
value and PNG stores them for almost nothing, so a pack that fills them spends MORE
bytes, on more texels of baked surface. Baked at the smallest side that holds wall
density, the set needs 45 % fewer texels and still costs 7 % more bytes than ships
(tighter islands are more edge, and edge does not compress). And it does not hold
density everywhere: the lightmap packer does not scale faces strictly by area, so
on 5 of the 30 the walls lose texels per metre even at 512². Its other price is
bleed headroom — the narrowest gap goes from 5 px to 2 — and that is before anyone
asks how it LOOKS, which this tool does not (T-0227's rule; that is
`tools/measure_ao_frame.mjs`). So nothing here is written into `emit.bake_ao`, and
T-2126's per-vertex route, which ships no occlusion PNG at all, stands.

## Why it is measured here and not written into generators/emit.py

`mesh_inputs.py` hashes emit.py's bytes into every asset's freshness record, so one
line there stales all 561 committed masters for a code path (`--ao`) that no
committed master takes. And T-2126 has since named per-vertex AO as the route the
cage parcel takes. So the figures land in ROADMAP R-W3a item 5, and `repack()` stays
here as the measured candidate, not as a pipeline step.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402  (bundled with Blender)

import emit  # noqa: E402
from build import resolve_phase  # noqa: E402  (the scene rule the bake uses)
from common.mesh import reset_scene  # noqa: E402
from common.phases import drawn_by_another_layer  # noqa: E402

SIZE = 512                  # emit.bake_ao's default atlas
BAKE_MARGIN_PX = 4          # emit.bake_ao: render.bake.margin
WALL_NZ = 0.1               # |n_z| under this is a wall
MARGIN_DIV = 0.4            # THE CHANGE's one parameter; see the docstring
# Past this the master is not an atlas question: `glessner_house` is 731,781 faces
# and one pass over it outlasts a run's 600 s foreground call. Skipped by name.
MAX_FACES = 20000
CALIBRATION = "sauganash_hotel"


def repack(ob, margin_div: float = MARGIN_DIV) -> None:
    """THE CHANGE: after `emit.unwrap`, lay every face out again with Blender's
    lightmap packer, edge to edge, in one atlas."""
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES", PREF_PACK_IN_ONE=True,
                             PREF_NEW_UVLAYER=False, PREF_BOX_DIV=12,
                             PREF_MARGIN_DIV=margin_div)
    bpy.ops.object.mode_set(mode="OBJECT")


def argv_after_ddash() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load(p: Path):
    return json.loads(p.read_text())


def candidates() -> dict[str, list[tuple[dict, dict]]]:
    """Every (structure, phase) a scene resolves and the bake would build, by archetype."""
    targets = [dt.date.fromisoformat(load(p)["target_date"])
               for p in sorted((ROOT / "data" / "scenes").glob("*.json"))]
    by_arch: dict[str, list[tuple[dict, dict]]] = {}
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = load(path)
        if st.get("archetype") not in emit.ARCHETYPES:
            continue
        for t in targets:
            ph = resolve_phase(st, t)
            if ph is not None and not drawn_by_another_layer(ph):
                by_arch.setdefault(st["archetype"], []).append((st, ph))
                break
    return by_arch


def pick(by_arch, per_arch: int, only: set[str] | None):
    if only:
        return [(st, ph) for pairs in by_arch.values() for st, ph in pairs if st["id"] in only]
    chosen = []
    for arch in sorted(by_arch):
        pairs = by_arch[arch]
        idx = sorted({round(i * (len(pairs) - 1) / max(per_arch - 1, 1))
                      for i in range(per_arch)}) if len(pairs) > 1 else [0]
        chosen += [pairs[i] for i in idx]
    if not any(st["id"] == CALIBRATION for st, _ in chosen):
        chosen += [p for pairs in by_arch.values() for p in pairs if p[0]["id"] == CALIBRATION]
    return chosen


def triangles(ob):
    """UV and world-space corners of every loop triangle, and its polygon, as arrays."""
    me = ob.data
    me.calc_loop_triangles()
    uv_layer = me.uv_layers.active.data
    mw = ob.matrix_world
    n = len(me.loop_triangles)
    uv = np.empty((n, 3, 2))
    xyz = np.empty((n, 3, 3))
    poly = np.empty(n, dtype=np.int64)
    for i, lt in enumerate(me.loop_triangles):
        poly[i] = lt.polygon_index
        for k in range(3):
            uv[i, k] = uv_layer[lt.loops[k]].uv
            xyz[i, k] = mw @ me.vertices[lt.vertices[k]].co
    return uv, xyz, poly


def raster(uv: np.ndarray, poly: np.ndarray, size: int) -> tuple[np.ndarray, int]:
    """Which polygon owns each texel (-1: none) by texel centre, and how many texels
    two different polygons both claim — an overlap the bake would paint twice."""
    owner = np.full((size, size), -1, dtype=np.int64)
    clashes = 0
    p = uv * size
    for (a, b, c), pid in zip(p, poly):
        x0 = max(int(math.floor(min(a[0], b[0], c[0]) - 0.5)), 0)
        x1 = min(int(math.ceil(max(a[0], b[0], c[0]) - 0.5)), size - 1)
        y0 = max(int(math.floor(min(a[1], b[1], c[1]) - 0.5)), 0)
        y1 = min(int(math.ceil(max(a[1], b[1], c[1]) - 0.5)), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (1 - w0 - w1 >= -1e-9)
        win = owner[y0:y1 + 1, x0:x1 + 1]
        clashes += int((inside & (win >= 0) & (win != pid)).sum())
        win[inside] = pid
    return owner, clashes


def min_gap(owner: np.ndarray, reach: int = 12) -> int | None:
    """The nearest two texels owned by DIFFERENT polygons, centre to centre, in
    texels (Chebyshev). Faces of one island share edges, so on a mesh whose islands
    are single faces this is the island gap; on a connected one it is a floor."""
    size = owner.shape[0]
    best = None
    for dx in range(-reach, reach + 1):
        for dy in range(0, reach + 1):
            dist = max(abs(dx), dy)
            if dist == 0 or (dy == 0 and dx < 0) or (best is not None and dist >= best):
                continue
            a = owner[dy:, max(dx, 0):size + min(dx, 0)]
            b = owner[:size - dy, max(-dx, 0):size + min(-dx, 0)]
            if np.any((a >= 0) & (b >= 0) & (a != b)):
                best = dist
    return best


def island_count(ob) -> int:
    """UV islands: faces joined where an edge they share IN SPACE carries the same UVs
    on both sides. Matched on position, not vertex index, because the archetypes emit
    split vertices — by index no two faces would ever share an edge."""
    me = ob.data
    uvd = me.uv_layers.active.data
    parent = list(range(len(me.polygons)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    edges: dict = {}
    for p in me.polygons:
        ids = list(range(p.loop_start, p.loop_start + p.loop_total))
        for a, b in zip(ids, ids[1:] + ids[:1]):
            ka = (tuple(round(c, 4) for c in me.vertices[me.loops[a].vertex_index].co),
                  tuple(round(c, 6) for c in uvd[a].uv))
            kb = (tuple(round(c, 4) for c in me.vertices[me.loops[b].vertex_index].co),
                  tuple(round(c, 6) for c in uvd[b].uv))
            key = (ka, kb) if ka < kb else (kb, ka)
            if key in edges:
                parent[root(p.index)] = root(edges[key])
            else:
                edges[key] = p.index
    return len({root(i) for i in range(len(me.polygons))})


def dilate(mask: np.ndarray, px: int) -> np.ndarray:
    out = mask.copy()
    for _ in range(px):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def areas(uv: np.ndarray, xyz: np.ndarray):
    """UV area as a fraction of the atlas, world area in m², |n_z|, per triangle."""
    e1, e2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    uv_area = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    cross = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    w_area = 0.5 * np.linalg.norm(cross, axis=1)
    nz = np.where(w_area > 0, np.abs(cross[:, 2]) / np.maximum(2 * w_area, 1e-12), 1.0)
    return uv_area, w_area, nz, cross


def bearing(normal_xy) -> str:
    """Which way a wall faces in the MASTER's own frame. The scene places and turns
    each master at load, so this names the wall within its building, not a compass
    point in the town."""
    deg = (math.degrees(math.atan2(normal_xy[0], normal_xy[1])) + 360) % 360
    return f"{deg:.0f} deg from the master's +y"


def named_wall(ob, poly: np.ndarray, w_area: np.ndarray, nz: np.ndarray):
    """The largest vertical polygon: the wall this master's density is quoted on."""
    walls = {}
    for i in np.nonzero(nz < WALL_NZ)[0]:
        walls[int(poly[i])] = walls.get(int(poly[i]), 0.0) + float(w_area[i])
    if not walls:
        return None
    idx = max(walls, key=lambda k: (walls[k], -k))
    n = ob.matrix_world.to_3x3() @ ob.data.polygons[idx].normal
    return {"polygon": idx, "area_m2": round(walls[idx], 3), "faces": bearing((n.x, n.y))}


def glb_bytes(path: Path) -> tuple[int, int]:
    """(file bytes, bytes of the image buffer views — the occlusion PNG)."""
    data = path.read_bytes()
    jlen = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + jlen])
    views = {im["bufferView"] for im in doc.get("images", []) if "bufferView" in im}
    return len(data), sum(doc["bufferViews"][v]["byteLength"] for v in views)


def build(st: dict, ph: dict, margin_div: float | None):
    to_params, build_fn = emit.ARCHETYPES[st["archetype"]]
    reset_scene()
    ob = build_fn(to_params(ph, st), f"{st['id']}__{ph['id']}")
    emit.unwrap(ob)
    if margin_div is not None:
        repack(ob, margin_div)
    return ob


def layout(ob, size: int, wall_poly: int | None):
    """Everything about the unwrap that does not need the bake."""
    uv, xyz, poly = triangles(ob)
    uv_area, w_area, nz, _ = areas(uv, xyz)
    owner, clashes = raster(uv, poly, size)
    walls = nz < WALL_NZ
    wall = named_wall(ob, poly, w_area, nz) if wall_poly is None else {"polygon": wall_poly}
    on_wall = poly == wall["polygon"] if wall else np.zeros(len(poly), dtype=bool)

    def density(sel):
        return float(uv_area[sel].sum() * size * size / max(w_area[sel].sum(), 1e-9))
    mask = owner >= 0
    return {
        "atlas": size,
        "faces": len(ob.data.polygons),
        "islands": island_count(ob),
        "min_gap_px": min_gap(owner),
        "overlap_texels": clashes,
        "covered_texels": int(mask.sum()),
        "occupancy_pct": round(100 * mask.mean(), 2),
        "with_margin_pct": round(100 * dilate(mask, BAKE_MARGIN_PX).mean(), 2),
        "density_walls_tpm2": round(density(walls), 1),
        "density_named_wall_tpm2": round(density(on_wall), 1) if on_wall.any() else None,
        "density_all_tpm2": round(density(np.ones(len(poly), dtype=bool)), 1),
    }, mask, wall


def measure(st, ph, margin_div, size, tmp: Path, wall_poly=None):
    ob = build(st, ph, margin_div)
    row, mask, wall = layout(ob, size, wall_poly)
    img_name = f"{ob.name}_ao"
    baked_mean = emit.bake_ao(ob, size=size)
    px = np.empty(size * size * 4, dtype=np.float32)
    bpy.data.images[img_name].pixels.foreach_get(px)
    red = px[0::4].reshape(size, size)
    tag = "ship" if margin_div is None else f"lm{size}"
    out = emit.export_glb(ob, st["id"], ph["id"], tmp / f"{st['id']}_{tag}.glb")
    row["glb_bytes"], row["png_bytes"] = glb_bytes(out)
    row["baked_mean_atlas"] = round(float(baked_mean), 4)
    row["baked_mean_covered"] = round(float(red[mask].mean()), 4) if mask.any() else None
    return row, wall


def matched_side(before: dict, after: dict) -> int:
    """The smallest atlas side at which the change holds BOTH wall densities. Density
    scales with the side squared, so the side scales with the square root."""
    ratios = [before[k] / after[k] for k in ("density_walls_tpm2", "density_named_wall_tpm2")
              if before.get(k) and after.get(k)]
    side = SIZE * math.sqrt(max(ratios)) if ratios else SIZE
    return min(SIZE, max(16, 4 * math.ceil(side / 4)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-archetype", type=int, default=3)
    ap.add_argument("--only", default=None, help="comma list of structure ids")
    ap.add_argument("--margin-div", type=float, default=MARGIN_DIV)
    ap.add_argument("--json", default=None, help="write the readings here")
    ap.add_argument("--append", action="store_true",
                    help="keep the masters already in --json and add these: the whole set "
                         "does not fit one 600 s foreground call, so it is read in halves")
    ap.add_argument("--list", action="store_true", help="print the chosen ids and stop")
    args = ap.parse_args(argv_after_ddash())
    only = set(args.only.split(",")) if args.only else None
    if args.list:
        print("CHOSEN " + ",".join(st["id"] for st, _ in pick(candidates(), args.per_archetype, only)))
        return 0
    rows, skipped = [], []
    if args.append and args.json and Path(args.json).exists():
        prior = json.loads(Path(args.json).read_text())
        rows, skipped = prior["masters"], prior["summary"]["skipped"]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for st, ph in pick(candidates(), args.per_archetype, only):
            if any(r["structure"] == st["id"] for r in rows + skipped):
                continue
            to_params, build_fn = emit.ARCHETYPES[st["archetype"]]
            reset_scene()
            faces = len(build_fn(to_params(ph, st), "probe").data.polygons)
            if faces > MAX_FACES:
                skipped.append({"structure": st["id"], "archetype": st["archetype"],
                                "faces": faces, "why": f"over MAX_FACES ({MAX_FACES})"})
                print(f"{st['id']:<44} skipped: {faces} faces", flush=True)
                continue
            before, wall = measure(st, ph, None, SIZE, tmp)
            wp = wall["polygon"] if wall else None
            after, _ = measure(st, ph, args.margin_div, SIZE, tmp, wp)
            side = matched_side(before, after)
            matched, _ = measure(st, ph, args.margin_div, side, tmp, wp)
            rows.append({"structure": st["id"], "phase": ph["id"], "archetype": st["archetype"],
                         "named_wall": wall, "before": before, "after": after,
                         "matched": matched})
            print(f"{st['id'][:40]:<40} {st['archetype']:<16} occ {before['occupancy_pct']:5.1f} -> "
                  f"{after['occupancy_pct']:5.1f}%  gap {before['min_gap_px']}->{after['min_gap_px']}  "
                  f"wall {before['density_named_wall_tpm2']} -> {after['density_named_wall_tpm2']}  "
                  f"png {before['png_bytes']} -> {after['png_bytes']} | {side}² {matched['png_bytes']}",
                  flush=True)

    def total(cond, key):
        return sum(r[cond][key] for r in rows)

    def texels(cond):
        return sum(r[cond]["atlas"] ** 2 for r in rows)
    conds = ("before", "after", "matched")
    summary = {
        "masters": len(rows),
        "skipped": skipped,
        "occupancy_pct": {c: round(100 * total(c, "covered_texels") / texels(c), 2) for c in conds},
        "atlas_texels": {c: texels(c) for c in conds},
        "glb_bytes": {c: total(c, "glb_bytes") for c in conds},
        "png_bytes": {c: total(c, "png_bytes") for c in conds},
        "overlap_texels": {c: total(c, "overlap_texels") for c in conds},
        "min_gap_px": {c: min((r[c]["min_gap_px"] for r in rows if r[c]["min_gap_px"]), default=None)
                       for c in conds},
        "wall_density_fell": {c: [r["structure"] for r in rows
                                  if any((r[c][k] or 0) < (r["before"][k] or 0) for k in
                                         ("density_walls_tpm2", "density_named_wall_tpm2"))]
                              for c in ("after", "matched")},
    }
    print(json.dumps(summary, indent=2))
    if args.json:
        Path(args.json).write_text(json.dumps({
            "ticket": "T-2127", "blender": bpy.app.version_string.split()[0],
            "bake_margin_px": BAKE_MARGIN_PX,
            "before": "emit.unwrap: smart_project(angle_limit=1.15, island_margin=0.02), 512",
            "after": f"emit.unwrap then uv.lightmap_pack(PREF_MARGIN_DIV={args.margin_div}), 512",
            "matched": "the same, at the smallest side holding both wall densities",
            "summary": summary, "masters": rows}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    import os
    os._exit(code)
