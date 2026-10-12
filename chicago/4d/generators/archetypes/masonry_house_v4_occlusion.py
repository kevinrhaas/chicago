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

This module is one of the masonry_house_v4* files generators/mesh_inputs.py hashes for a
v4 building, so it stales the Glessner House and nothing else.
"""
from __future__ import annotations

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
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, shape_method="AABB",
                            scale=True, margin_method="FRACTION", margin=PACK_MARGIN)
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
    uv_area = _welded_unwrap(bpy, bmesh, np, ob, mask)
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
    bpy.ops.object.bake(type="AO", uv_layer=OCCLUSION_UV)
    px = np.zeros(SIZE * SIZE * 4, np.float32)
    raw.pixels.foreach_get(px)
    ao = px.reshape(SIZE, SIZE, 4)[..., 0].copy()
    # Which texels a face wrote. Cycles writes the whole buffer, the unwritten texels
    # as 0 with alpha 1, so neither alpha nor a sentinel survives the AO pass. A
    # tangent-space normal bake (no rays, one sample) writes blue near 1 on every face
    # texel and 0 elsewhere, through the same margin.
    scene.cycles.samples = 1
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", uv_layer=OCCLUSION_UV)
    raw.pixels.foreach_get(px)
    covered = px.reshape(SIZE, SIZE, 4)[..., 2] > 0.25
    value = np.clip(_fill_holes(np, ao, covered), 0.0, 1.0)
    # Quantise here, so the mean recorded is the mean of the bytes the exporter writes.
    value = np.round(value * 255.0) / 255.0
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
    }
    ob["stone_occlusion"] = record
    return record
