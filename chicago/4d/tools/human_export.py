"""Export a portable-human Blender master to the contract's four GLBs (T-1787).

    blender -b -noaudio MASTER.blend --python tools/human_export.py -- OUT_DIR

Writes OUT_DIR/<asset_id>.lod0.glb ... lod3.glb, one per `lod<N>` collection in the
master. Every exporter setting the contract depends on is set HERE, explicitly, so an
export is a command and never an interactive dialog with undocumented toggles
(docs/HUMAN-ASSET-CONTRACT.md § 13, T-1787). What each setting buys:

  export_yup                  the contract frame: +Y up, the figure facing +Z
  export_extras               scene custom properties -> scenes[0].extras, which is
                              where `chicago4d_human` (provenance) must live; mesh
                              shape-key names -> mesh.extras.targetNames; a walk
                              action's `speed_m_s` -> its animation's extras
  export_def_bones = False    every contract bone, deform or not, is a joint of the
                              ONE skin (§ 3) — eyes and jaw included
  export_animation_mode       ACTIONS: every action on the armature is one clip,
                              named for the action, so clip names are the master's
  export_rest_position_armature  the bind pose is the rest pose (the T-pose), not
                              whatever frame the file was saved on
  export_draco_mesh_compression_enable = False
                              Draco is refused by the contract (§ 9); Meshopt is
                              applied after, by tools/human_export.sh
  export_image_format AUTO    PNG/JPEG as authored. KTX2 is refused (§ 9)

The master must follow the layout tools/human_fixture_blend.py writes: one armature
object; collections `lod0`..`lod3` of mesh objects parented to it; `socket_*` empties
on their bones beside the armature; one action per clip; and the scene custom
property `chicago4d_human`, whose `lod` this script rewrites per file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy


def main(out_dir: Path) -> int:
    scene = bpy.context.scene
    prov = scene.get("chicago4d_human")
    prov = prov.to_dict() if hasattr(prov, "to_dict") else prov
    if prov is None:
        print("REFUSING: the master has no scene custom property `chicago4d_human` "
              "(the provenance block every human GLB must carry)", file=sys.stderr)
        return 1
    asset_id = prov["asset_id"]
    rigs = [o for o in scene.objects if o.type == "ARMATURE"]
    if len(rigs) != 1:
        print(f"REFUSING: a human master carries exactly one armature, this one has {len(rigs)}",
              file=sys.stderr)
        return 1
    rig = rigs[0]
    sockets = [o for o in scene.objects if o.name.startswith("socket_")]
    lods = sorted(c.name for c in bpy.data.collections if c.name.startswith("lod"))
    if not lods:
        print("REFUSING: no lod<N> collection in the master", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    rig.animation_data_create()
    rig.animation_data.action = None
    for lod_name in lods:
        lod = int(lod_name[3:])
        meshes = [o for o in bpy.data.collections[lod_name].objects if o.type == "MESH"]
        bpy.ops.object.select_all(action="DESELECT")
        for o in [rig, *sockets, *meshes]:
            o.select_set(True)
        bpy.context.view_layer.objects.active = rig
        scene["chicago4d_human"] = {**prov, "lod": lod}
        path = out_dir / f"{asset_id}.lod{lod}.glb"
        bpy.ops.export_scene.gltf(
            filepath=str(path),
            export_format="GLB",
            use_selection=True,
            export_yup=True,
            export_extras=True,
            export_apply=False,
            export_texcoords=True,
            export_normals=True,
            export_tangents=False,
            export_materials="EXPORT",
            export_image_format="AUTO",
            export_skins=True,
            export_def_bones=False,
            export_influence_nb=4,
            export_all_influences=False,
            export_morph=True,
            export_morph_normal=True,
            export_animations=True,
            export_animation_mode="ACTIONS",
            export_rest_position_armature=True,
            export_force_sampling=True,
            export_optimize_animation_size=True,
            export_frame_range=False,
            export_draco_mesh_compression_enable=False,
            export_cameras=False,
            export_lights=False,
        )
        print(f"wrote {path}")
    scene["chicago4d_human"] = {**prov, "lod": 0}
    return 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1:
        print("usage: blender -b MASTER.blend --python tools/human_export.py -- OUT_DIR")
        sys.exit(2)
    sys.exit(main(Path(argv[0])))
