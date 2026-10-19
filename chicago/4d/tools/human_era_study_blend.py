# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in1812/1904 canonical authoring CLI; no1835/default builder changes.

blender -b --factory-startup --python-exit-code 1 --python THIS.py -- \
  --era-study 1812 --liberty REAL_HEADING --output FRESH.blend

Arguments use spaces, for example --era-study 1812. Source validation may run in
ordinary Python with --check-source-only; it cannot claim a Blender/export pass.
"""
from pathlib import Path
import argparse
import importlib
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_era_study_common import (need, source_file, validate_manifest, skin_and_hair,
                                    add_eyes, lods_sockets_actions, provenance)


def parse(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--era-study", choices=["1812", "1904"], required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--liberty", required=True,
                        help="Real integrator-assigned docs/LIBERTIES.md heading, after rebase")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-source-only", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    if args.check_source_only:
        parser.error("--check-source-only cannot write a canonical master") if args.output else None
    elif not args.output:
        parser.error("--output is required for explicit canonical authoring")
    if args.output and (args.output.suffix != ".blend" or args.output.exists()):
        parser.error("--output must be a fresh .blend path")
    if args.receipt and args.receipt.exists():
        parser.error("Never overwrite a preceding receipt")
    return args


def checked_inputs(args):
    root = args.root.resolve()
    sys.path.insert(0, str(root/"tools"))
    path = source_file(root, "data/humans/recipes/era_studies/"+args.era_study+".json")
    manifest = json.loads(path.read_text())
    need(manifest["scene"] == args.era_study, "CLI era and exact recipe differ")
    contract = validate_manifest(root, manifest, args.liberty)
    module = importlib.import_module("human_era_study_"+args.era_study)
    body, garment, identity = module.validate_inputs(root, manifest)
    # Existing pure CC0 source fitting checks all actual hair source hashes,
    # declared material settings and full-body source-vertex references before
    # any BPy import or factory-scene mutation. This is not appearance proof.
    from human_hair_short04 import fit
    fit(body, manifest["hair_component"], root)
    # The full source-derived body remains the authority for hair and normals;
    # masks and source-owned shoe translations belong to canonical composition.
    canonical = module.prepare_canonical_meshes(body, garment)
    return root, manifest, contract, module, body, garment, identity, canonical


def main(args):
    root, manifest, contract, module, body, garment, identity, canonical = checked_inputs(args)
    receipt = {"scope": "Named era-study input and canonical authoring; no photographic or scene acceptance",
               "scene": args.era_study, "asset_id": manifest["asset_id"],
               "identity": identity, "source_inputs_validated": True,
               "canonical_derivations": canonical[2], "bpy_executed": False,
               "master_written": False, "exported": False, "production_eligible": False}
    if not args.check_source_only:
        import bpy
        # Validation precedes clearing any factory-startup authoring scene.
        bpy.ops.wm.read_factory_settings(use_empty=True)
        study = module.compose(root, manifest, args.output)
        hair, normals = skin_and_hair(root, manifest, study)
        add_eyes(study)
        lods_sockets_actions(study, manifest, contract)
        scene = bpy.context.scene
        scene.render.fps = 30
        scene["chicago4d_human"] = provenance(manifest, contract, args.liberty,
                                               args.output.resolve(), identity, hair, normals)
        scene["chicago4d_human"]["canonical_derivations_json"] = json.dumps(study["canonical_derivations"], sort_keys=True)
        scene["chicago4d_human"]["winding_reversed_parts_json"] = json.dumps(study["winding_reversed_parts"])
        scene["chicago4d_human"]["body_source_json"] = json.dumps(study["body"]["source"], sort_keys=True)
        scene["chicago4d_human"]["body_target_blend_json"] = json.dumps(study["body"]["target_blend"], sort_keys=True)
        scene["chicago4d_human"]["review_required"] = identity["review_required"]
        scene["chicago4d_human"]["touches_removal"] = identity["touches_removal"]
        scene["authoring_status"] = "UNACCEPTED era-study master; export/LOD/frame, body+garment fit, soles, age-specific skin/hair, anatomy, period wardrobe and actual source+published images remain open"
        scene.frame_set(1)
        need(len([o for o in scene.objects if o.type == "ARMATURE"]) == 1,
             "Canonical source must contain exactly one actual rig")
        need(all("lod"+str(lod) in bpy.data.collections for lod in range(4)),
             "Actual four LOD collections are mandatory")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result = bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()), compress=True)
        need("FINISHED" in result and args.output.is_file(), "Canonical master was not saved")
        receipt.update(bpy_executed=True, master_written=True,
                       master=str(args.output.resolve()), blender=bpy.app.version_string,
                       normal_readback=normals, hair_source=hair)
        print("wrote canonical master "+str(args.output))
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x") as file:
            json.dump(receipt, file, indent=2)
            file.write("\n")
    print(json.dumps({"source_inputs_validated": True, "bpy_executed": receipt["bpy_executed"],
                      "master_written": receipt["master_written"], "exported": False,
                      "production_eligible": False}))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    main(parse(argv))
