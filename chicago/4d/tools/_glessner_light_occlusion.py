"""Blender side of the Glessner light LOD's own stone-scale occlusion (T-2401).

Run by tools/_glessner_lod.py, never by hand:

    blender -b --factory-startup --python tools/_glessner_light_occlusion.py -- IN.npz OUT.npz

T-2400 baked the granite's stone-scale occlusion onto the full master's own TEXCOORD_1.
The light LOD is a different mesh (the same v4 record through the same construction
functions, sampled more coarsely), so that bake cannot ride it: until now it put
T-2393's faint tiling map back on TEXCOORD_0. This bakes the light mesh itself, with
the full master's baker unchanged — the same slots, reach, samples, seed, weld and
hole fill (generators/archetypes/masonry_house_v4_occlusion.bake_stone_occlusion) —
at the light tier's own atlas size, so mobile pays for a smaller map.

The pure-Python producer stays the GLB's only writer. This script takes the reduced
mesh as arrays, gives back the OcclusionUV corner coordinates (one per GLB vertex, in
the producer's own vertex order) and the quantised 8-bit occlusion atlas, and exports
nothing.

IN.npz:  co (V,3) float64 z-up metres; uv0 (V,2) float32; corners (F,) int32 corner
         counts, faces consecutive over the vertices; slot (F,) int32 v4 material slot;
         slots (S,) material names in slot order; size () int32 atlas edge.
OUT.npz: uv1 (V,2) float32; ao (size,size) uint8, row 0 at the top (PNG order);
         record — the baker's figures as JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


def main(argv):
    import bpy
    import numpy as np

    source, target = (Path(a) for a in argv)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "generators"))
    from archetypes import masonry_house_v4_occlusion as occlusion
    from archetypes.masonry_house_v4_materials import vine_material

    data = np.load(source)
    co, uv0, corners, slot = data["co"], data["uv0"], data["corners"], data["slot"]
    names, size = [str(n) for n in data["slots"]], int(data["size"])
    if int(corners.sum()) != len(co):
        raise SystemExit("light occlusion: face corners do not cover the vertices")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new("glessner_light")
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.astype(np.float32).ravel())
    me.loops.add(len(co))
    me.loops.foreach_set("vertex_index", np.arange(len(co), dtype=np.int32))
    me.polygons.add(len(corners))
    me.polygons.foreach_set("loop_start", (np.cumsum(corners) - corners).astype(np.int32))
    me.polygons.foreach_set("loop_total", corners.astype(np.int32))
    me.polygons.foreach_set("material_index", slot.astype(np.int32))
    me.update(calc_edges=True)
    surface = me.uv_layers.new(name="SurfaceUV")
    # Input UV0 is in glTF's downward-v convention; Blender's shader reads up-v.
    surface_uv=uv0.astype(np.float32).copy()
    surface_uv[:,1]=1-surface_uv[:,1]
    surface.data.foreach_set("uv", surface_uv.ravel())
    me.uv_layers.active = surface
    for name in names:
        if name=='glessner_vines' and 29 in slot:
            # A plain shader would bake solid rectangular shadows behind the
            # reduced foliage panels. Preserve the actual shared alpha mask.
            material=vine_material(bpy)
        else:
            material = bpy.data.materials.new(name)
            material.use_nodes = True
        me.materials.append(material)
    ob = bpy.data.objects.new("glessner_light", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    occlusion.SIZE = size   # the light tier's atlas; every other figure is the master's
    record = occlusion.bake_stone_occlusion(ob)

    uv1 = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[occlusion.OCCLUSION_UV].data.foreach_get("uv", uv1)
    image = bpy.data.images[occlusion.IMAGE_NAME]
    pixels = np.zeros(size * size * 4, np.float32)
    image.pixels.foreach_get(pixels)
    # Blender's rows run bottom-up; a PNG's run top-down. The values were quantised
    # to 1/255 by the baker, so this rounding is exact.
    ao = np.round(pixels.reshape(size, size, 4)[::-1, :, 0] * 255.0).astype(np.uint8)
    np.savez(target, uv1=uv1.reshape(-1, 2), ao=ao, record=json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
