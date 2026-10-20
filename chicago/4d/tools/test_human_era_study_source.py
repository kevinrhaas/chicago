# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in source/array/CLI semantics, without BPy, master/export or browser."""
from pathlib import Path
import argparse
import ast
import copy
import importlib
import json
import math
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"tools"))
from human_era_study_common import validate_manifest
from human_hair_short04 import fit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--liberty", required=True)
    args = parser.parse_args()
    controls = []
    studies = []
    def reject(label, action):
        try:
            action()
        except (ValueError, FileNotFoundError):
            controls.append(label)
        else:
            raise RuntimeError("Planted source fault accepted: "+label)
    for era in ("1812", "1904"):
        manifest = json.loads((ROOT/"data/humans/recipes/era_studies"/(era+".json")).read_text())
        contract = validate_manifest(ROOT, manifest, args.liberty)
        module = importlib.import_module("human_era_study_"+era)
        body, garment, identity = module.validate_inputs(ROOT, manifest)
        sources, canonical_garment, receipt = module.prepare_canonical_meshes(body, garment)
        hair, _, hair_report = fit(body, manifest["hair_component"], ROOT)
        footwear = ([m for m in canonical_garment if m["name"]=="plain_low_shoes_conjectural"]
                    if era=="1812" else [m for m in canonical_garment["meshes"] if m["name"].startswith("civilian_closed_shoe")])
        if not footwear or any(abs(min(p[1] for p in m["positions_m"]))>1e-10 for m in footwear):
            raise RuntimeError("Canonical source footwear registration failed")
        if any(min(p[1] for p in m["positions_m"])<receipt["body_mask_threshold_y_m"] for m in sources):
            raise RuntimeError("Unreferenced nude sole vertices remain")
        for source, mapping in zip(sources, receipt["body_source_maps"]):
            original = body["meshes"][mapping["body_mesh"]]
            vertex_map = mapping["emitted_vertex_to_original_uv_split_vertex"]
            for key in ("positions_m", "uvs", "weights", "source_vertex_indices"):
                if source[key] != [original[key][i] for i in vertex_map]:
                    raise RuntimeError("Mask changed retained source attributes")
        studies.append({"era":era,"asset_id":manifest["asset_id"],"body_render_vertices":sum(len(m["positions_m"])for m in sources),
                        "body_render_triangles":sum(len(m["triangles"])for m in sources),
                        "garment_triangles":sum(len(m["triangles"])for m in garment["meshes"]),
                        "hair_triangles":len(hair["triangles"]),"identity_grade":identity["identity_grade"],
                        "normal_transfer":"Full original body source normals must be remapped by exact graphical source IDs in BPy",
                        "footwear_body_derivations":receipt,"physical_fit_accepted":False})
        for name, change in [("wrongEra",{"scene":"1835"}),("driverRole",{"roles":["driver"]}),
                             ("production",{"production_eligible":True}),("wrongPerson",{"person_id":"kinzie_john_h"})]:
            modified={**manifest,**change}
            reject(era+"/"+name,lambda m=modified:validate_manifest(ROOT,m,args.liberty))
        modified=copy.deepcopy(manifest);modified["skin_texture"]["roughness"]=math.nan
        reject(era+"/NaNskin",lambda:validate_manifest(ROOT,modified,args.liberty))
        reject(era+"/unassignedLiberty",lambda:validate_manifest(ROOT,manifest,"L999999999"))
        modified=copy.deepcopy(manifest);modified["body_path"]="../outside.json"
        reject(era+"/outsidePath",lambda:validate_manifest(ROOT,modified,args.liberty))
        modified=copy.deepcopy(manifest);modified["body_sha256"]="0"*64
        reject(era+"/changedBodyPin",lambda:module.validate_inputs(ROOT,modified))
        config=copy.deepcopy(manifest["hair_component"]);config["alpha_cutoff"]=math.nan
        reject(era+"/NaNhair",lambda:fit(body,config,ROOT))
    # Execute only the real exporter argument prefix, ending before any Blender
    # pin/cache/download/build step. This cannot simulate a successful export.
    exporter=ROOT/"tools/human_export.sh"
    prefix=exporter.read_text().split("# shellcheck disable=SC1091",1)[0]
    prefix += '\nprintf "SOURCE_ARGMODE=%s\\n" "$MODE"\n'
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp);master=directory/"argument-only.blend";master.write_bytes(b"")
        tests=[("fixture",[],0,"fixture"),("verify",["--verify"],0,"verify"),
               ("masterOverride",["--master",str(master),"--output-dir",str(directory/"fresh")],0,"master"),
               ("overrideWithoutMaster",["--output-dir",str(directory/"fresh")],2,None),
               ("relativeOverride",["--master",str(master),"--output-dir","relative"],2,None),
               ("existingOverride",["--master",str(master),"--output-dir",str(directory)],2,None),
               ("missingMasterValue",["--master"],2,None)]
        for label, argv, code, mode in tests:
            result=subprocess.run(["bash","-c",prefix,str(exporter),*argv],capture_output=True,text=True)
            if result.returncode!=code or (mode and "SOURCE_ARGMODE="+mode not in result.stdout):
                raise RuntimeError("Exporter argument semantics failed: "+label)
            controls.append("export-prefix/"+label)
    if "bpy" in sys.modules:
        raise RuntimeError("Source checks must never import BPy")
    for path in (ROOT/"tools").glob("human_era_study*.py"):
        ast.parse(path.read_text())
    result={"PASS":True,"scope":"Actual relocated source/body/garment/hair arrays and25 refusal/argument-prefix controls; no BPy, canonical master, export, LOD or browser acceptance",
            "studies":studies,"controls":controls,"bpy_executed":False,"master_written":False,"exported":False}
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
