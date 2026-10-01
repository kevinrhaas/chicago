"""How a record becomes a GLB — the geometry pipeline, and the bytes the staleness hash is taken over.

TICKET T-1654. This module is `build.py`'s other half. `build.py` is a command
line: it parses flags, walks `data/structures/`, decides which phases are in the
scene, keeps `assets/manifest.json` and prints a summary. None of that can move a
vertex. Everything that CAN move one lives here.

## Why the two are separate files rather than two halves of one

`mesh_inputs.py::_code_shas` hashes the bytes of the code that turns parameters
into vertices, and until this split that meant `build.py` WHOLE — all ~420 lines
of it, including its module docstring, its `argparse` block and its result
summary. So a fix to `--only`'s argument handling staled **422 of 422** assets
(T-1652, measured 2026-09-27), and the only remedy the gate offered was a
full-town rebake: ~20 minutes of Blender, ~18 of `web_derivatives.sh`, and 422
GLBs whose bytes all move because Cycles is not bit-reproducible — a diff in
which the reader cannot tell a real content change from a re-roll.

That is precisely the failure `mesh_inputs.py` writes down as its own first
principle, and then committed one directory up:

    A hash that cries stale for reasons that cannot change the geometry gets
    disbelieved, and a disbelieved gate is worse than no gate.

T-0164 made the same argument about `generators/common/` — a comment line in
`common/phases.py` staled 349 of 349 — and fixed it by having the recipe ask
`code_inputs.geometry_modules()` which modules make geometry instead of listing
the ones that share a folder. A whole module is no more a statement about
geometry than a directory listing is. This is that fix, applied to the file
T-0164 left hashed.

## Why a file split and not a declared region of one file

The alternative considered in the ticket was to keep one file and hash a declared
REGION of it. It was rejected for the reason `code_inputs.py` spells out at
length: that shape is an ALLOWLIST, and an allowlist silently drops the next
thing somebody adds. Geometry written outside the declared region would be
outside every asset's input hash, nothing would go stale when it changed, and no
run would ever find out. A file split fails the other way — the safe way. Code
added to THIS module is hashed by default; moving something out of it is a
deliberate edit, in a diff, with a sentence beside it saying why.

The residual is that the split itself can be undone by writing geometry back into
`build.py`, where it would not be hashed. That is not left to good intentions:
`tools/test_build_cli_has_no_geometry.py` reads `build.py` with `ast` on every
`check.sh` run and refuses it if it imports an archetype or a shared builder, or
touches `bpy` beyond `bpy.app` — the three ways geometry gets made. The gate is
the reason the allowlist objection does not simply reappear here.
"""

from __future__ import annotations

import array
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

import bpy  # noqa: E402

from common.mesh import reset_scene  # noqa: E402
from archetypes import (  # noqa: E402
    bridge_timber, camp, fort_structure, frame_dwelling, frame_storefront, frame_tavern,
    log_dwelling, masonry_house, outbuilding, palisade, pier_crib,
)
from archetypes.bridge_timber_params import from_phase as bridge_timber_params  # noqa: E402
from archetypes.camp_params import from_phase as camp_params  # noqa: E402
from archetypes.fort_structure_params import from_phase as fort_structure_params  # noqa: E402
from archetypes.frame_dwelling_params import from_phase as frame_dwelling_params  # noqa: E402
from archetypes.frame_storefront_params import from_phase as frame_storefront_params  # noqa: E402
from archetypes.frame_tavern_params import from_phase as frame_tavern_params  # noqa: E402
from archetypes.log_dwelling_params import from_phase as log_dwelling_params  # noqa: E402
from archetypes.masonry_house_params import from_phase as masonry_house_params  # noqa: E402
from archetypes.outbuilding_params import from_phase as outbuilding_params  # noqa: E402
from archetypes.palisade_params import from_phase as palisade_params  # noqa: E402
from archetypes.pier_crib_params import from_phase as pier_crib_params  # noqa: E402

ARCHETYPES = {
    "frame_tavern": (frame_tavern_params, frame_tavern.build),
    "frame_dwelling": (frame_dwelling_params, frame_dwelling.build),
    "log_dwelling": (log_dwelling_params, log_dwelling.build),
    "bridge_timber": (bridge_timber_params, bridge_timber.build),
    "outbuilding": (outbuilding_params, outbuilding.build),
    "frame_storefront": (frame_storefront_params, frame_storefront.build),
    "pier_crib": (pier_crib_params, pier_crib.build),
    "palisade": (palisade_params, palisade.build),
    "fort_structure": (fort_structure_params, fort_structure.build),
    "masonry_house": (masonry_house_params, masonry_house.build),
    "camp": (camp_params, camp.build),
}


def unwrap(ob) -> None:
    """Smart-UV unwrap. Always run — textures need UVs even when AO does not."""
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_ao(ob, size: int = 512, samples: int = 48) -> float:
    """Bake ambient occlusion, wire it in as the glTF occlusion texture, and
    return the mean occlusion over the atlas so the caller can check that the
    same number survives into the exported file.

    OFF BY DEFAULT, and that is a considered choice rather than an oversight.
    AO is the largest visible quality gain available on plain frame buildings,
    which is why this pipeline uses Blender at all — but it only works on
    geometry built for it. These archetypes model clapboard courses, window
    reveals and shutters as thin surfaces sitting a centimetre off the wall, and
    every one of them occludes its neighbours.

    **The figures this docstring used to quote were wrong twice over — T-0158.**
    "Mean 0.265, 69 % of texels below half" was (a) read off an sRGB-tagged buffer,
    so it was the sRGB-ENCODED occlusion rather than the occlusion, and (b) taken
    over the whole 512x512 atlas, **68.9 % of which is empty UV space** — so most
    of what it counted was blank, not dark, and the 69 % is very nearly the empty
    fraction itself. Re-measured on `sauganash_hotel` from the exported file:
    atlas-wide raw mean 0.1665, and over the 81,458 texels the unwrap actually
    writes, **mean 0.5358 with 58.7 % below half**. The "0.38 at a 0.25 m AO
    distance" figure carries both faults and has NOT been re-measured.

    **ANSWERED FROM THE RENDERED FRAME — T-0227, 2026-08-28. Yes, and by more than
    any atlas statistic said.** `sauganash_hotel` was baked with `--ao`, swapped
    into the source tree, and shot at both Sauganash anchors and both viewports
    through `tools/critic_shots.mjs --metrics`; `tools/measure_ao_frame.mjs` reads
    the building's OWN visible pixels out of those frames (the structures mask
    intersected with what moved between the two conditions). Over the 87,893 pixels
    the hotel paints at `sauganash`, desktop:

    | | mean L* | median L* | L* < 20 | literal black px |
    |---|---|---|---|---|
    | without AO | 33.8 | 44 | 31.1 % | 0 |
    | with AO | **11.1** | **10** | **88.9 %** | **6,532** |

    Mobile agrees (33.4 -> 11.1), and the log wing anchor agrees at both viewports.
    So the lightness of a DOCUMENTED white-painted wall falls by two thirds and
    nearly nine tenths of it lands under L* 20, with thousands of pixels at 0,0,0 —
    a hole in the render, not a shaded wall. An atlas mean of 0.5358 over written
    texels reads as "about half occluded on average" and sounds survivable; the
    frame says the building goes out. **That gap is the lesson: an atlas mean is
    not a statement about the walls.** The mechanism is that glTF occlusion scales
    the INDIRECT term only, and at this scene's 70.5 deg sun the faces a walker sees
    from the street are lit by little else (STATUS §1 items 9-11) — so occlusion
    near 1 on those faces removes essentially all of their light.

    The fix is unchanged and now measured rather than asserted: a low-poly AO cage
    — bake the massing only, and let the decorative surfaces inherit it — not a
    stronger denoiser and not a lower `occlusionTexture.strength`, which would dim
    a correct bake and a wrong one by the same factor. Until then `--ao` exists so
    the path stays exercised, and the manifest records honestly whether any given
    asset actually carries AO.

    **Two costs the cage parcel inherits, both measured on that one asset.** The
    atlas is **31.1 % occupied** (81,458 of 262,144 texels), so two thirds of a
    ~107 KB occlusion PNG is empty space — the master goes 94,420 -> 202,292 bytes,
    +114 %. And `aoMap` is part of `materialKey` in `renderers/web/js/buildings.js`,
    so an asset carrying its own map cannot batch with one that does not: **+2 draw
    calls at every station and viewport, for one building.**

    ## The order of the two lines below is the whole of T-0158

    `colorspace_settings.name` is set BEFORE the bake and must stay there. Setting
    it on a GENERATED image that has no file behind it and is not packed frees the
    image buffer, which regenerates from `generated_color` — black — and clears
    `is_dirty`, which is the flag Blender's own exporter tests in
    `make_temp_image_copy()` before it will carry unsaved pixels across. Doing it
    after the bake therefore destroyed the data AND switched off the exporter's
    only rescue path, and shipped a uniformly black occlusion texture that glTF
    reads as FULLY OCCLUDED while `assets/manifest.json` recorded `baked_ao: true`.
    Measured on `sauganash_hotel`, 512x512, 48 samples: after the bake mean 0.2158
    in memory, in the GLB min 0 max 0 over 262,144 texels. With the tag set first:
    0.1665 in memory, 0.1665 in the GLB, 0.0 % drift.

    Non-Color rather than sRGB, and not merely to dodge the wipe: `Image.pixels`
    on an 8-bit buffer is raw in both directions, so the tag decides what the bake
    WRITES. Under sRGB it stores the sRGB-encoded occlusion; glTF samples an
    occlusion texture as `byte / 255` with no transfer decode, so that file was
    already ~30 % too bright before it went black.
    """
    img = bpy.data.images.new(f"{ob.name}_ao", size, size)
    img.colorspace_settings.name = "Non-Color"      # BEFORE the bake — see above
    for mat in ob.data.materials:
        nt = mat.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.name = "ao_tex"
        nt.nodes.active = tex          # bake target

    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.render.bake.use_selected_to_active = False
    sc.render.bake.margin = 4
    bpy.ops.object.bake(type="AO")

    # What the bake actually put in the buffer, read before anything else touches
    # the image. This is the figure `assert_ao_survived_export` holds the file to.
    buf = array.array("f", bytes(4 * size * size * 4))
    img.pixels.foreach_get(buf)
    red = buf[0::4]
    baked_mean = sum(red) / len(red)

    # Wire the baked image in as the glTF OCCLUSION texture. Without this the
    # exporter drops it and the GLB carries no AO at all — the bake silently
    # produces nothing, which is exactly what happened before this was added.
    # The exporter recognises a node group literally named "glTF Material Output"
    # with an "Occlusion" input; that is the only supported path.
    for mat in ob.data.materials:
        nt = mat.node_tree
        tex = next((n for n in nt.nodes if n.name == "ao_tex"), None)
        if tex is None:
            continue
        grp = bpy.data.node_groups.get("glTF Material Output")
        if grp is None:
            grp = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
            grp.interface.new_socket("Occlusion", in_out="INPUT",
                                     socket_type="NodeSocketFloat")
            grp.nodes.new("NodeGroupInput")
        node = nt.nodes.new("ShaderNodeGroup")
        node.node_tree = grp
        node.name = "glTF Material Output"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Red"], node.inputs["Occlusion"])
    return baked_mean


def export_glb(ob, structure_id: str, phase_id: str, out: Path) -> Path:
    ob["structure_id"] = structure_id
    ob["phase_id"] = phase_id
    ob.name = f"{structure_id}__{phase_id}"
    ob.data.name = ob.name

    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_attributes=True,      # carries _CONFIDENCE — see docs/GLB-CONTRACT.md
        export_extras=True,          # carries structure_id / phase_id into node.extras
        export_cameras=False,
        export_lights=False,
    )
    return out


@dataclass(frozen=True)
class Emitted:
    """What one structure phase's build produced, for the caller's bookkeeping."""
    path: Path
    tris: int
    baked_mean: float | None


def emit_structure(structure: dict, phase: dict, archetype: str, out: Path, *,
                   bake: bool = True, ao: bool = False) -> Emitted:
    """Resolve one structure phase's parameters and turn them into a GLB on disk.

    THE WHOLE OF THE GEOMETRY PIPELINE IS THIS FUNCTION AND WHAT IT CALLS, which is
    the property T-1654 needs: `mesh_inputs.py` hashes this module's bytes, so the
    reach of the staleness gate and the reach of the code that can move a vertex are
    the same set of lines.

    The caller chooses the structures and keeps the manifest; it is handed back
    everything it needs to record this one — the path written, the triangle count it
    prints, and the baked occlusion mean it re-reads out of the exported bytes.
    """
    to_params, build_fn = ARCHETYPES[archetype]
    # The whole record, not only the phase. The phase carries a building's FORM;
    # the finish the 665-roof programme dealt it lives one level up, in the
    # record's `reconstruction` block — `finish_key` on 222 records and
    # `roof_condition` on 218, read until T-0007 by the placeholder generator
    # alone. `mesh_inputs.resolve_params` passes the same pair, so the staleness
    # hash sees exactly what the builder sees.
    params = to_params(phase, structure)
    name = f"{structure['id']}__{phase['id']}"

    reset_scene()
    ob = build_fn(params, name)
    baked_mean = None
    if bake:
        unwrap(ob)
        if ao:
            baked_mean = bake_ao(ob)
    path = export_glb(ob, structure["id"], phase["id"], out)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return Emitted(path=path, tris=tris, baked_mean=baked_mean)
