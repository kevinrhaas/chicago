"""Glessner v4 granite: stone-scale occlusion baked from the building's own stones (T-2400).

T-2393 gave the split-face granite a tiling occlusion map drawn from its normal map's
height field. It is correct and faint (shade 2-5 % darker, crease contrast +1-6 %),
because that relief is millimetres deep and a tiling map cannot know where one stone
ends. The relief a visitor reads on a face in shade is at the scale of the stones this
builder already models one by one: the recessed joints, the pitched arrises and drafted
margins (fractured_stone), the reveals and the course lines. This bakes that.

What it does, in the order it does it:

1. Unwraps the granite slots (GRANITE_SLOTS) onto their own layer, OcclusionUV. The v4
   mesh is polygon soup — every facet carries its own vertices, 1.61 M of them for
   495 k granite faces — so a smart projection of the mesh as built makes one island per
   facet, and at any atlas size the stones get a handful of texels each (measured: 9 %
   of the atlas covered, nothing baked). So the projection runs on a WELDED COPY
   (vertices merged within 0.1 mm) and its UVs are carried back face by face, corner by
   corner. The building's own geometry is never edited; the copy is deleted.
2. Bakes Cycles ambient occlusion onto that layer at DISTANCE_M, which is the reach of a
   stone's own relief and its reveal, not of the building's masses. A long reach is what
   put the Sauganash out in T-0227: the masses occlude the sky that lights a street face
   at all. Atlas texels no face covers are filled from their neighbours (push-pull), so
   no mip level ever averages a stone with black.
3. Wires the result as the glTF occlusionTexture of the granite slots on OcclusionUV,
   which the exporter writes as TEXCOORD_1 (SurfaceUV is TEXCOORD_0, and BakeUV is
   removed at export). It REPLACES the T-2393 tiling map on those slots: glTF has one
   occlusion slot per material, the two maps ride different UV sets, and at 2.3 cm a
   texel the bake cannot hold millimetre creases. The light LOD, which has no
   TEXCOORD_1, keeps the tiling map (tools/_glessner_lod.py). The sun is untouched:
   three.js applies aoMap to indirect light only.

The figures are written onto the object (`stone_occlusion`), so they travel into the
GLB's node extras; generators/build.py reads them back to record `baked_ao` and to hold
the exported map to the bake with `ao_export.assert_ao_survived_export`.

Cycles AO is not
bit-reproducible across hardware: the same mesh, seed and samples baked in a cloud
container and on an Actions runner differed in 2,471 of 4,194,304 texels (T-2427), so
every off-runner bake of Glessner moved the master's bytes and redded the bake check's
K01 hashes. So the quantised atlas and its written-texel mask are committed beside the
models, in assets/bakes/stone-occlusion/, keyed by a sha256 of everything the bake
reads — the mesh's vertices, faces and slots, its OcclusionUV, the figures below and
the Blender version. T-2494 also found that Blender's welded smart projection / packing
changes OcclusionUV with the host math library: Debian glibc 2.41 and Ubuntu glibc 2.39
produce identical mesh inputs but different UV layouts. The atlas therefore retains
its UV coordinates too, keyed separately by the exact pre-unwrap mesh, mask, Blender
version and unwrap recipe. A changed mesh or recipe cannot reuse that layout. A bake
whose complete atlas key matches takes the committed atlas and runs
no Cycles at all, so it writes the same bytes on any CPU. A bake whose key does not
match bakes fresh, says so, and rewrites the file: geometry that moves carries its new
atlas in the same commit, and the next bake anywhere reproduces it. STONE_OCCLUSION_REBAKE=1
ignores the committed atlas (to measure a fresh bake against it); it still rewrites it.

This module is one of the masonry_house_v4* files generators/mesh_inputs.py hashes for a
v4 building, so it stales the Glessner House and nothing else. The atlas files are not
inputs: they are a cache of this module's output, and a stale one is simply not used.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from archetypes.masonry_house_v4_materials import GRANITE, GRANITE_VARIANTS, ROUGH_TRIM

OCCLUSION_UV = "OcclusionUV"
GRANITE_SLOTS = (GRANITE, *GRANITE_VARIANTS, ROUGH_TRIM)
SIZE = 2048            # ~2.3 cm a texel over 1,528 m2 of granite at 67 % atlas coverage
SAMPLES = 64
DISTANCE_M = 0.30      # a stone's relief and its reveal; not the building's masses
WELD_M = 1e-4
ANGLE_LIMIT = 1.15     # emit.unwrap's, so a stone face and its pitched arris stay one island
PACK_MARGIN = 0.0002   # fraction of the atlas; the bake's own margin covers the seams
BAKE_MARGIN_PX = 4
IMAGE_NAME = "granite_stone_occlusion"
# One committed atlas a size: the master bakes at 2048, the light tier (T-2401) at 1024.
ATLAS_DIR = Path(__file__).resolve().parents[2] / "assets" / "bakes" / "stone-occlusion"
ATLAS_RECIPE = 1       # bump when the bake below changes in a way the key cannot see
UNWRAP_RECIPE = 1      # bump for an unwrap/transfer algorithm change
PACK_OPTIONS = dict(udim_source="CLOSEST_UDIM", rotate=True, shape_method="AABB",
                    scale=True, margin_method="FRACTION")


def _welded_unwrap(bpy, bmesh, np, ob, mask):
    """Write OcclusionUV for the masked faces as if the soup were welded."""
    me = ob.data
    tmp = bpy.data.meshes.new(f"{ob.name}_occlusion_weld")
    bm = bmesh.new()
    bm.from_mesh(me)
    tag = bm.faces.layers.int.new("_occlusion_face")
    for i, f in enumerate(bm.faces):
        f[tag] = i
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not mask[f.index]], context="FACES")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD_M)
    bm.to_mesh(tmp)
    bm.free()
    for layer in list(tmp.uv_layers):
        tmp.uv_layers.remove(layer)
    tmp.uv_layers.new(name=OCCLUSION_UV)
    tob = bpy.data.objects.new(tmp.name, tmp)
    bpy.context.scene.collection.objects.link(tob)
    ob.select_set(False)
    bpy.context.view_layer.objects.active = tob
    tob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=ANGLE_LIMIT, island_margin=0.0)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(**PACK_OPTIONS, margin=PACK_MARGIN)
    bpy.ops.object.mode_set(mode="OBJECT")

    def ints(seq, attr, n):
        a = np.zeros(n, np.int32)
        seq.foreach_get(attr, a)
        return a

    def floats(seq, attr, n, w):
        a = np.zeros(n * w, np.float32)
        seq.foreach_get(attr, a)
        return a.reshape(-1, w)

    m = len(tmp.polygons)
    orig = ints(tmp.attributes["_occlusion_face"].data, "value", m)
    tls, tlt = ints(tmp.polygons, "loop_start", m), ints(tmp.polygons, "loop_total", m)
    tlv = ints(tmp.loops, "vertex_index", len(tmp.loops))
    tuv = floats(tmp.uv_layers[OCCLUSION_UV].data, "uv", len(tmp.loops), 2)
    tco = floats(tmp.vertices, "co", len(tmp.vertices), 3)
    n = len(me.polygons)
    ols, olt = ints(me.polygons, "loop_start", n), ints(me.polygons, "loop_total", n)
    olv = ints(me.loops, "vertex_index", len(me.loops))
    oco = floats(me.vertices, "co", len(me.vertices), 3)
    out = np.zeros((len(me.loops), 2), np.float32)
    # A weld keeps a face's corner order, so a face that kept its corner count maps
    # corner for corner; the check below holds that to the weld distance. A face that
    # lost a corner to the weld takes each corner's nearest.
    same = olt[orig] == tlt
    worst = 0.0
    for k in np.unique(tlt[same]):
        sel = same & (tlt == k)
        ti = tls[sel][:, None] + np.arange(k)
        oi = ols[orig[sel]][:, None] + np.arange(k)
        worst = max(worst, float(np.linalg.norm(tco[tlv[ti]] - oco[olv[oi]], axis=2).max()))
        out[oi.ravel()] = tuv[ti.ravel()]
    for j in np.nonzero(~same)[0]:
        ti = tls[j] + np.arange(tlt[j])
        oi = ols[orig[j]] + np.arange(olt[orig[j]])
        d = np.linalg.norm(oco[olv[oi]][:, None] - tco[tlv[ti]][None], axis=2)
        out[oi] = tuv[ti[d.argmin(1)]]
    if worst > 10 * WELD_M:
        raise RuntimeError(f"stone occlusion: welded corners drifted {worst:.6f} m from "
                           f"their faces; the UV transfer would misplace the bake")
    layer = me.uv_layers.new(name=OCCLUSION_UV)
    layer.data.foreach_set("uv", out.ravel())
    bpy.data.objects.remove(tob)
    bpy.data.meshes.remove(tmp)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return _uv_area(np, me, mask, out)


def _uv_area(np, me, mask, out):
    ols, olt = np.zeros(len(me.polygons), np.int32), np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_start", ols)
    me.polygons.foreach_get("loop_total", olt)
    # Coverage: the share of the atlas the granite faces' UV triangles occupy.
    uv_area = 0.0
    for k in np.unique(olt[mask]):
        sel = mask & (olt == k)
        p = out[ols[sel][:, None] + np.arange(k)]
        x, y = p[..., 0], p[..., 1]
        uv_area += float(np.abs(0.5 * (x * np.roll(y, -1, 1) - np.roll(x, -1, 1) * y).sum(1)).sum())
    return uv_area


def _fill_holes(np, value, covered):
    """Push-pull: every texel no face wrote takes the mean of the nearest written ones."""
    if covered.all():
        return value
    levels = [(value * covered, covered.astype(np.float32))]
    while levels[-1][0].shape[0] > 1:
        v, w = levels[-1]
        h = v.shape[0] // 2
        levels.append((v.reshape(h, 2, h, 2).sum((1, 3)), w.reshape(h, 2, h, 2).sum((1, 3))))
    v, w = levels[-1]
    fill = v / np.maximum(w, 1e-9)
    for v, w in reversed(levels[:-1]):
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)
        fill = np.where(w > 0, v / np.maximum(w, 1e-9), up)
    return np.where(covered, value, fill)


def _mesh_digest(np, me, mask, recipe, include_uv):
    h = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode())
    fingerprints = {}
    inputs = [(me.vertices, "co", len(me.vertices) * 3, np.float32),
              (me.loops, "vertex_index", len(me.loops), np.int32),
              (me.polygons, "loop_start", len(me.polygons), np.int32),
              (me.polygons, "loop_total", len(me.polygons), np.int32)]
    if include_uv:
        inputs.append((me.uv_layers[OCCLUSION_UV].data, "uv", len(me.loops) * 2, np.float32))
    for seq, attr, n, dtype in inputs:
        a = np.zeros(n, dtype)
        seq.foreach_get(attr, a)
        raw = a.tobytes()
        h.update(raw)
        fingerprints[attr] = {"values": n, "sha256": hashlib.sha256(raw).hexdigest()}
    raw_mask = np.packbits(mask).tobytes()
    h.update(raw_mask)
    fingerprints["mask"] = {"faces": len(mask), "sha256": hashlib.sha256(raw_mask).hexdigest()}
    return h.hexdigest(), fingerprints


def _unwrap_key(bpy, np, me, mask):
    """Exact inputs before the host-dependent unwrap; never a rounded geometry key."""
    recipe = {"recipe": UNWRAP_RECIPE, "blender": bpy.app.version_string,
              "weld_m": WELD_M, "angle_limit": ANGLE_LIMIT,
              "pack": {**PACK_OPTIONS, "margin": PACK_MARGIN},
              "slots": list(GRANITE_SLOTS)}
    return _mesh_digest(np, me, mask, recipe, False)[0]


def _atlas_key(bpy, np, me, mask):
    """sha256 of everything the AO and coverage bakes read (see module doc)."""
    recipe = {
        "recipe": ATLAS_RECIPE, "blender": bpy.app.version_string, "size": SIZE,
        "samples": SAMPLES, "distance_m": DISTANCE_M, "margin_px": BAKE_MARGIN_PX,
        "slots": list(GRANITE_SLOTS)}
    key, fingerprints = _mesh_digest(np, me, mask, recipe, True)
    # T-2494: report the actual producer inputs when a runner gets a different
    # key. The digest and all baked/exported values remain unchanged; a key alone
    # cannot distinguish changed geometry from changed unwrap or recipe inputs.
    print("stone occlusion inputs: " + json.dumps({
        "key": key, "recipe": recipe, "components": fingerprints}, sort_keys=True), flush=True)
    return key


def _atlas_path():
    return ATLAS_DIR / f"{IMAGE_NAME}_{SIZE}.npz"


def _load_unwrap(np, key, loops):
    """A validated canonical UV layout for these exact mesh/recipe inputs, or None."""
    path = _atlas_path()
    if not path.is_file():
        return None
    with np.load(path, allow_pickle=False) as atlas:
        if not {"unwrap_key", "uv", "uv_sha256"}.issubset(atlas.files):
            return None  # T-2431 cache: unwrap once, retaining its existing AO if it matches
        if str(atlas["unwrap_key"]) != key:
            return None
        uv, digest = atlas["uv"], str(atlas["uv_sha256"])
    if uv.shape != (loops, 2) or uv.dtype != np.float32 or not np.isfinite(uv).all():
        return None
    if hashlib.sha256(uv.tobytes()).hexdigest() != digest:
        return None
    return uv


def _load_atlas(np, key):
    """The committed (quantised atlas, written-texel mask) for `key`, or None."""
    path = _atlas_path()
    if os.environ.get("STONE_OCCLUSION_REBAKE") == "1" or not path.is_file():
        return None
    with np.load(path) as atlas:
        if str(atlas["key"]) != key:
            return None
        q = atlas["ao"]
        covered = np.unpackbits(atlas["covered"])[:SIZE * SIZE].reshape(SIZE, SIZE) > 0
    if q.shape != (SIZE, SIZE) or q.dtype != np.uint8:
        return None
    return q, covered


def _store_atlas(np, key, q, covered, unwrap_key, uv):
    path = _atlas_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # A failed serialization must not truncate the last usable cache.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as fh:
            temporary = Path(fh.name)
            np.savez_compressed(fh, key=np.str_(key), ao=q, covered=np.packbits(covered.ravel()),
                                unwrap_key=np.str_(unwrap_key), uv=uv,
                                uv_sha256=np.str_(hashlib.sha256(uv.tobytes()).hexdigest()))
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def bake_stone_occlusion(ob):
    """Bake, wire and record the granite's stone-scale occlusion on `ob` (see module doc)."""
    import bmesh
    import bpy
    import numpy as np

    me = ob.data
    slots = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", slots)
    mask = np.isin(slots, GRANITE_SLOTS)
    granite_area = sum(p.area for p in me.polygons if p.material_index in GRANITE_SLOTS)
    keep_active = me.uv_layers.active.name
    unwrap_key = _unwrap_key(bpy, np, me, mask)
    uv_coordinates = _load_unwrap(np, unwrap_key, len(me.loops))
    restored_uv = uv_coordinates is not None
    if restored_uv:
        layer = me.uv_layers.new(name=OCCLUSION_UV)
        layer.data.foreach_set("uv", uv_coordinates.ravel())
        uv_area = _uv_area(np, me, mask, uv_coordinates)
        print(f"stone occlusion: restored canonical UV layout ({unwrap_key[:16]})", flush=True)
    else:
        uv_area = _welded_unwrap(bpy, bmesh, np, ob, mask)
        uv_coordinates = np.zeros(len(me.loops) * 2, np.float32)
        me.uv_layers[OCCLUSION_UV].data.foreach_get("uv", uv_coordinates)
        uv_coordinates = uv_coordinates.reshape(-1, 2)
    me.uv_layers.active = me.uv_layers[keep_active]   # emit.unwrap still edits BakeUV

    # Bake into a float buffer whose alpha says which texels a face wrote.
    raw = bpy.data.images.new(f"{IMAGE_NAME}_raw", SIZE, SIZE, alpha=True, float_buffer=True)
    raw.colorspace_settings.name = "Non-Color"         # BEFORE any pixels (T-0158)
    raw.pixels.foreach_set(np.tile(np.float32([1, 1, 1, 0]), SIZE * SIZE))
    scratch = bpy.data.images.new(f"{IMAGE_NAME}_scratch", 8, 8)
    targets = []
    for i, mat in enumerate(me.materials):
        nt = mat.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = raw if i in GRANITE_SLOTS else scratch
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = OCCLUSION_UV
        nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
        nt.nodes.active = tex
        targets.append((mat, tex, uv))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.seed = 0
    scene.world = scene.world or bpy.data.worlds.new("occlusion")
    scene.world.light_settings.distance = DISTANCE_M
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.margin = BAKE_MARGIN_PX
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    key = _atlas_key(bpy, np, me, mask)
    cached = _load_atlas(np, key)
    if cached is not None:
        q, covered = cached
        print(f"stone occlusion: {_atlas_path().name} matches this mesh ({key[:12]}); "
              f"no Cycles bake (T-2431)")
    else:
        bpy.ops.object.bake(type="AO", uv_layer=OCCLUSION_UV)
        px = np.zeros(SIZE * SIZE * 4, np.float32)
        raw.pixels.foreach_get(px)
        ao = px.reshape(SIZE, SIZE, 4)[..., 0].copy()
        # Which texels a face wrote. Cycles writes the whole buffer, the unwritten texels
        # as 0 with alpha 1, so neither alpha nor a sentinel survives the AO pass. A
        # tangent-space normal bake (no rays, one sample) writes blue near 1 on every
        # face texel and 0 elsewhere, through the same margin.
        scene.cycles.samples = 1
        bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", uv_layer=OCCLUSION_UV)
        raw.pixels.foreach_get(px)
        covered = px.reshape(SIZE, SIZE, 4)[..., 2] > 0.25
        value = np.clip(_fill_holes(np, ao, covered), 0.0, 1.0)
        q = np.round(value * 255.0).astype(np.uint8)
        print(f"stone occlusion: BAKED FRESH on this CPU ({key[:12]}) and wrote "
              f"{_atlas_path().relative_to(ATLAS_DIR.parents[2])}; commit it with the model (T-2431)")
    if cached is None or not restored_uv:
        _store_atlas(np, key, q, covered, unwrap_key, uv_coordinates)
        print("stone occlusion: retained validated UV layout with its atlas (T-2494)")
    # Quantised, so the mean recorded is the mean of the bytes the exporter writes.
    value = q.astype(np.float32) / np.float32(255.0)
    written = value[covered]

    img = bpy.data.images.new(IMAGE_NAME, SIZE, SIZE, alpha=False)
    img.colorspace_settings.name = "Non-Color"         # BEFORE the pixels (T-0158)
    rgba = np.empty((SIZE, SIZE, 4), np.float32)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = value
    rgba[..., 3] = 1.0
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    bpy.data.images.remove(raw)

    group = bpy.data.node_groups.get("glTF Material Output")
    for i, (mat, tex, uv) in enumerate(targets):
        nt = mat.node_tree
        if i not in GRANITE_SLOTS:
            nt.nodes.remove(tex)
            nt.nodes.remove(uv)
            continue
        tex.image = img
        tex.interpolation = "Linear"
        tex.extension = "EXTEND"
        node = nt.nodes.get("glTF Material Output")
        if node is None:
            if group is None:
                group = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
                group.interface.new_socket("Occlusion", in_out="INPUT",
                                           socket_type="NodeSocketFloat")
                group.nodes.new("NodeGroupInput")
            node = nt.nodes.new("ShaderNodeGroup")
            node.node_tree = group
            node.name = "glTF Material Output"
        for link in list(node.inputs["Occlusion"].links):
            nt.links.remove(link)
        split = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tex.outputs["Color"], split.inputs["Color"])
        nt.links.new(split.outputs["Red"], node.inputs["Occlusion"])
        # The light LOD has no TEXCOORD_1 and puts this map back (tools/_glessner_lod.py).
        if mat.get("occlusion_map"):
            mat["occlusion_tiling_map"] = mat["occlusion_map"]
        mat["occlusion_map"] = f"baked:{IMAGE_NAME}"
        mat["occlusion_uv"] = OCCLUSION_UV
    bpy.data.images.remove(scratch)

    record = {
        "image": IMAGE_NAME, "uv": OCCLUSION_UV, "size": SIZE, "samples": SAMPLES,
        "distance_m": DISTANCE_M, "slots": list(GRANITE_SLOTS),
        "mean": round(float(value.mean()), 6),
        "granite_mean": round(float(written.mean()), 6) if written.size else None,
        "granite_p05": round(float(np.percentile(written, 5)), 4) if written.size else None,
        "atlas_written": round(float(covered.mean()), 4),
        "atlas_uv_area": round(uv_area, 4),
        "texel_cm": round(100 * (granite_area / max(uv_area * SIZE * SIZE, 1)) ** 0.5, 2),
        "atlas_key": key[:16],
    }
    ob["stone_occlusion"] = record
    return record
