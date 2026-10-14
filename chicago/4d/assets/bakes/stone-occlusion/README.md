# Committed stone-occlusion atlases (T-2431)

The Glessner House's granite carries stone-scale ambient occlusion baked by Cycles
(T-2400 on the full master, T-2401 on the light tier). Cycles AO is not bit-reproducible
across CPUs, so a fresh bake on a different machine moved the models' bytes and redded
the bake check's K01 hashes (T-2427).

Each `.npz` here is the baker's own output for one atlas size: `ao` (the quantised 8-bit
atlas), `covered` (the texels a face wrote, bit-packed) and `key` (a sha256 of everything
the bake reads: the mesh, its OcclusionUV, the bake figures and the Blender version).
Since T-2494 it also holds `uv` (float32 loop coordinates), `uv_sha256` and
`unwrap_key`. The latter hashes the exact pre-unwrap geometry, topology, granite mask,
Blender version and unwrap settings/recipe. Blender's smart projection and packing
produce different layouts under Debian glibc 2.41 and Ubuntu glibc 2.39, even with
identical mesh inputs. Retaining only the AO image was therefore insufficient.

The producer restores a layout only when those inputs match and its shape, dtype,
finite values and checksum validate. It still computes the complete atlas key from
the actual mesh and restored UVs before reusing AO. A changed mesh or unwrap recipe
regenerates the layout; a changed AO recipe rebakes AO. `STONE_OCCLUSION_REBAKE=1`
forces the AO bake while retaining a valid layout, so CPU comparisons use the same UVs.
`tools/test_stone_occlusion_uv.py` checks the committed layouts and exercises stale
input and damaged-cache refusals without Blender.
`generators/archetypes/masonry_house_v4_occlusion.py` uses a file whose key matches the
mesh and runs no Cycles; it bakes fresh and rewrites the file when the key does not
match. So when Glessner's geometry moves, **commit the atlas the bake wrote together
with the model**. `tools/check_stone_occlusion_atlas.py` (a `check.sh` step) refuses a
model whose committed atlas is missing or holds another key.

| file | baked for |
|---|---|
| `granite_stone_occlusion_2048.npz` | the full master and its web derivative |
| `granite_stone_occlusion_1024.npz` | the light tier (`tools/_glessner_lod.py`) |

These are validated caches of the baker's output: `generators/mesh_inputs.py`
does not hash them, and a stale one is simply not used.
