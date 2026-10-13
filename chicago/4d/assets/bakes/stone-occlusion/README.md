# Committed stone-occlusion atlases (T-2431)

The Glessner House's granite carries stone-scale ambient occlusion baked by Cycles
(T-2400 on the full master, T-2401 on the light tier). Cycles AO is not bit-reproducible
across CPUs, so a fresh bake on a different machine moved the models' bytes and redded
the bake check's K01 hashes (T-2427).

Each `.npz` here is the baker's own output for one atlas size: `ao` (the quantised 8-bit
atlas), `covered` (the texels a face wrote, bit-packed) and `key` (a sha256 of everything
the bake reads: the mesh, its OcclusionUV, the bake figures and the Blender version).
`generators/archetypes/masonry_house_v4_occlusion.py` uses a file whose key matches the
mesh and runs no Cycles; it bakes fresh and rewrites the file when the key does not
match. So when Glessner's geometry moves, **commit the atlas the bake wrote together
with the model**. `tools/check_stone_occlusion_atlas.py` (a `check.sh` step) refuses a
model whose committed atlas is missing or holds another key.

| file | baked for |
|---|---|
| `granite_stone_occlusion_2048.npz` | the full master and its web derivative |
| `granite_stone_occlusion_1024.npz` | the light tier (`tools/_glessner_lod.py`) |

These are a cache of the baker's output, not inputs to it: `generators/mesh_inputs.py`
does not hash them, and a stale one is simply not used.
