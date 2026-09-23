"""Generate meshes from data/. Run inside Blender:

    blender -b -noaudio --factory-startup --python generators/build.py -- [args]

    --all           build every structure phase resolvable for the scene
    --only <id>     build one structure id
    --scene <id>    scene to resolve phases against (default 1835)
    --no-bake       skip UV + AO baking (fast iteration)
    --ao            bake ambient occlusion (opt-in; nothing in the nightly passes it —
                    see bake_ao() for why, and generators/ao_export.py for the guard
                    that refuses a GLB whose occlusion did not survive the export)
    --out <dir>     output directory (default assets/gltf)

Refuses to run while data/datum.json is unverified — fixing the origin after
geometry exists means regenerating everything, so the build makes that impossible
rather than merely discouraged.
"""

from __future__ import annotations

import argparse
import array
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

import bpy  # noqa: E402

import ao_export  # noqa: E402
import mesh_inputs  # noqa: E402

from common.mesh import reset_scene  # noqa: E402
from common.phases import drawn_by_another_layer  # noqa: E402
from archetypes import (  # noqa: E402
    bridge_timber, fort_structure, frame_dwelling, frame_storefront, frame_tavern,
    log_dwelling, outbuilding, palisade, pier_crib,
)
from archetypes.bridge_timber_params import from_phase as bridge_timber_params  # noqa: E402
from archetypes.fort_structure_params import from_phase as fort_structure_params  # noqa: E402
from archetypes.frame_dwelling_params import from_phase as frame_dwelling_params  # noqa: E402
from archetypes.frame_storefront_params import from_phase as frame_storefront_params  # noqa: E402
from archetypes.frame_tavern_params import from_phase as frame_tavern_params  # noqa: E402
from archetypes.log_dwelling_params import from_phase as log_dwelling_params  # noqa: E402
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
}


def argv_after_ddash() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load(p: Path):
    return json.loads(p.read_text())


def resolve_phase(structure: dict, target: dt.date):
    """The scene rule, identical to tools/validate.py: exactly one phase must
    cover the date, or the structure is not in the scene."""
    hits = []
    for ph in structure.get("phases", []):
        r = ph.get("documented_range", {})
        try:
            frm = dt.date.fromisoformat(r["from"])
            to = dt.date.fromisoformat(r["to"])
        except (KeyError, ValueError):
            continue
        if frm <= target <= to:
            hits.append(ph)
    if len(hits) > 1:
        raise SystemExit(f"{structure['id']}: {len(hits)} phases cover {target}; exactly one must")
    return hits[0] if hits else None


def inputs_hash(structure: dict, phase: dict, archetype: str) -> str:
    """Hash of everything that determines this mesh, written into
    `assets/manifest.json` so `tools/check.sh` can tell a stale committed GLB from
    a fresh one. Determinism is defined on inputs, because Cycles AO is not
    bit-reproducible across hardware.

    The recipe lives in `generators/mesh_inputs.py` rather than here, because the
    gate that compares the hash has to recompute it in a sandbox with no Blender,
    and this module cannot be imported without bpy."""
    return mesh_inputs.structure_inputs_sha(structure, phase, archetype)


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--scene", default="1835")
    ap.add_argument("--no-bake", action="store_true",
                    help="skip UV unwrap as well as AO")
    ap.add_argument("--ao", action="store_true",
                    help="bake ambient occlusion. OFF by default: see bake_ao().")
    ap.add_argument("--out", default=str(ROOT / "assets" / "gltf"))
    args = ap.parse_args(argv_after_ddash())

    datum = load(ROOT / "data" / "datum.json")
    if not datum.get("verified"):
        print("REFUSING TO BUILD: data/datum.json is not verified.\n"
              "Fixing the origin after geometry exists means regenerating everything.\n"
              "See docs/EPOCHS.md and docs/RESEARCH/datum_derivation.md.")
        return 2

    scene = load(ROOT / "data" / "scenes" / f"{args.scene}.json")
    target = dt.date.fromisoformat(scene["target_date"])
    outdir = Path(args.out)

    manifest_path = ROOT / "assets" / "manifest.json"
    manifest = load(manifest_path) if manifest_path.exists() else {}
    manifest.setdefault("assets", {})
    manifest["blender"] = bpy.app.version_string.split()[0]
    # What the hashes below mean. tools/validate.py refuses to compare against a
    # scheme it does not compute, so redefining freshness is a visible event.
    manifest["inputs_scheme"] = mesh_inputs.SCHEME

    built = 0
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = load(path)
        if args.only and st["id"] != args.only:
            continue
        phase = resolve_phase(st, target)
        if phase is None:
            print(f"skip {st['id']}: no phase covers {target}")
            continue
        # T-0161. The phase says its geometry is built at load by another layer,
        # so baking one here puts a mesh in the tree that `tools/validate.py`
        # then refuses — which is what made every full bake need a hand-deletion
        # to pass its own gate. The test is imported rather than restated: see
        # generators/common/phases.py for why a fourth copy was the problem.
        if drawn_by_another_layer(phase):
            layer = (phase.get("drawn_by") or {}).get("layer", "another layer")
            print(f"skip {st['id']}: phase '{phase.get('id', '?')}' is drawn by {layer}")
            continue
        arch = st["archetype"]
        if arch not in ARCHETYPES:
            print(f"skip {st['id']}: archetype '{arch}' has no generator yet")
            continue

        to_params, build_fn = ARCHETYPES[arch]
        # The whole record, not only the phase. The phase carries a building's FORM;
        # the finish the 665-roof programme dealt it lives one level up, in the
        # record's `reconstruction` block — `finish_key` on 222 records and
        # `roof_condition` on 218, read until T-0007 by the placeholder generator
        # alone. `mesh_inputs.resolve_params` passes the same pair, so the staleness
        # hash sees exactly what the builder sees.
        params = to_params(phase, st)
        name = f"{st['id']}__{phase['id']}"

        reset_scene()
        ob = build_fn(params, name)
        baked_mean = None
        if not args.no_bake:
            unwrap(ob)
            if args.ao:
                baked_mean = bake_ao(ob)
        out = export_glb(ob, st["id"], phase["id"], outdir / f"{name}.glb")

        entry = {
            "kind": "generated",
            "structure_id": st["id"],
            "phase_id": phase["id"],
            "archetype": arch,
            "inputs_sha256": inputs_hash(st, phase, arch),
            "bytes": out.stat().st_size,
            "baked_ao": bool(args.ao and not args.no_bake),
        }
        # Read the exported BYTES back and refuse a file whose occlusion texture is
        # not the occlusion that was baked. On the bytes rather than on the in-memory
        # image, because memory is not where this breaks: T-0158 shipped a bake that
        # read min 0.000 / max 1.000 in Blender and min 0 / max 0 in the GLB, with the
        # run exiting 0 and the manifest recording baked_ao: true. The manifest entry
        # is written only if the file passes, so `baked_ao: true` cannot outlive the
        # occlusion again.
        if baked_mean is not None:
            try:
                stats = ao_export.assert_ao_survived_export(out, baked_mean)
            except ao_export.AoExportError as e:
                raise SystemExit(f"REFUSING TO RECORD THIS BAKE: {e}") from e
            entry["ao_occlusion_mean"] = round(stats["mean"], 6)
            print(f"       AO baked mean {baked_mean:.4f} -> exported mean "
                  f"{stats['mean']:.4f} (min {stats['min']:.4f} max {stats['max']:.4f}) over "
                  f"{stats['texels']:,} texels, "
                  f"{abs(stats['mean'] - baked_mean) / max(baked_mean, 1e-9) * 100:.1f} % drift")
        manifest["assets"][out.name] = entry
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        print(f"built {out.name}  {out.stat().st_size:,} bytes  ~{tris} tris")
        built += 1

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"\n{built} asset(s) built; manifest updated")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
