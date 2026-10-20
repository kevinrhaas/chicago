# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in1904 mature civilian composition; no default1835 builder is changed.

validate_inputs() has no BPy dependency. compose() creates only a fresh56-joint
body and civilian wardrobe in an empty authoring scene. The shared caller owns
cleared skin/hair, eyes, morphs, fourLODs, sockets, clips, provenance and saving.
No BPy execution, canonical master, export or photographic acceptance is claimed.
"""
from pathlib import Path
import hashlib
import json
import math
import copy

DATE="1904-07-01"
PERSON="glessner_john_j"
ASSET="glessner_john_j_1904_study"
ROLES=["standing","walking","passenger"]
BODY_SHA="8459b40305b07ad1a481958736160dabe43bf53f4fdc95d8503b6fe103483625"
GARMENT_SHA="5ee0032745a683d81cbd6baceda2394e7580046b42299cf9c099a3fd017c2482"
MATERIAL_NAMES={
    "coat_dark_plain_reconstructed":"garment_outer__civilian_coat_plain_1904",
    "waistcoat_plain_reconstructed":"garment_outer__civilian_waistcoat_plain_1904",
    "shirt_plain_reconstructed":"garment_upper__civilian_shirt_plain_1904",
    "trousers_plain_reconstructed":"garment_lower__civilian_trousers_plain_1904",
    "shoes_plain_reconstructed":"footwear__civilian_low_shoes_plain_1904",
}
# Original prototype construction parameterization has opposite face parity on
# these exact parts. Original serialized arrays remain immutable. Correct parity
# in the canonical composition, rather than hiding backfaces with materials.
REVERSE_WINDING=frozenset(("civilian_coat_sleeve_l","civilian_lapel_r",
    "civilian_shirt_collar","civilian_straight_trouser_l","civilian_straight_trouser_r"))
PART_NAMES=["civilian_open_front_coat_original","civilian_coat_sleeve_l",
    "civilian_lapel_l","civilian_coat_sleeve_r","civilian_lapel_r",
    "civilian_waistcoat_front","civilian_shirt_front","civilian_shirt_collar",
    "civilian_trouser_waist_original","civilian_straight_trouser_l",
    "civilian_closed_shoe_l","civilian_straight_trouser_r","civilian_closed_shoe_r"]
FOOTWEAR_PARTS=frozenset(("civilian_closed_shoe_l","civilian_closed_shoe_r"))
DERIVATION_POLICY={"policy":"canonical-footwear-visibility-1904-v1",
    "shoe_grounding":"translate each reviewed shoe by negative source minY",
    "body_visibility":"mask source body faces crossing below grounded shoe top; prune unused vertices",
    "reverse_source_parts":sorted(REVERSE_WINDING)}


def require(value,message):
    if not value:raise ValueError(message)


def source_path(root,name):
    root=Path(root).resolve();relative=Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts,"Root-relative authoring path required")
    path=(root/relative).resolve()
    require(path.is_relative_to(root),"Authoring input escapes checkout")
    return path


def pinned(root,name,expected):
    path=source_path(root,name);raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected,"Changed authoring input: "+name)
    return raw


def validate_mesh(mesh,names):
    count=len(mesh["positions_m"])
    require(count>0 and count==len(mesh["weights"])==len(mesh["uvs"]),"Incomplete authoring arrays")
    require(all(len(p)==3 and all(math.isfinite(v) for v in p) for p in mesh["positions_m"]),"Invalid position")
    require(all(len(uv)==2 and all(math.isfinite(v) for v in uv) for uv in mesh["uvs"]),"Invalid UV")
    require(bool(mesh["triangles"]),"Empty triangle component")
    for face in mesh["triangles"]:
        require(len(face)==len(set(face))==3 and all(type(i) is int and 0<=i<count for i in face),"Invalid triangle")
    for weights in mesh["weights"]:
        require(1<=len(weights)<=4 and not(set(weights)-names) and
            all(math.isfinite(v) and v>0 for v in weights.values()) and abs(math.fsum(weights.values())-1)<1e-8,"Invalid skin weights")


def validate_inputs(root,manifest):
    root=Path(root)
    require(manifest.get("format")=="chicago4d_era_study_master_v1" and manifest.get("scene")=="1904" and
        manifest.get("scene_date")==DATE and manifest.get("asset_id")==ASSET and manifest.get("person_id")==PERSON,
        "Only explicit named1904 study is qualified")
    require(manifest.get("identity_grade")=="attested" and manifest.get("appearance_grade")=="reconstructed" and
        manifest.get("production_eligible") is False and manifest.get("roles")==ROLES,"Preserve identity/appearance/role limits")
    require(manifest.get("body_sha256")==BODY_SHA and manifest.get("garment_sha256")==GARMENT_SHA,"Only reviewed actual body/garment inputs")
    require(manifest.get("material_names")==MATERIAL_NAMES,"Material remap differs from reviewed contract-slot mapping")
    require(manifest.get("canonical_derivations")==DERIVATION_POLICY,"Explicit canonical derivative policy required")
    require(manifest.get("body_age_years")==61 and manifest.get("body_height_m")==1.75,"Reconstructed body parameters changed")
    body=json.loads(pinned(root,manifest["body_path"],BODY_SHA))
    garment=json.loads(pinned(root,manifest["garment_path"],GARMENT_SHA))
    for value in (body,garment):
        require(value.get("license")=="CC0-1.0" and value.get("units")=="m" and value.get("up_axis")=="+Y" and value.get("forward_axis")=="+Z","Cleared metre/Yup/+Z inputs required")
    require(body["target_blend"]["phenotype"]["chosen_age_years"]==61 and body["target_blend"]["phenotype"]["age_band_years"]==[60,61],"Wrong mature body")
    require(abs(body["report"]["chosen_height_m"]-1.75)<1e-9,"Body height changed")
    contract=json.loads((root/"data/humans/contract.json").read_text());parents=dict(contract["skeleton"]["bones"])
    require(len(body["skeleton"])==56 and {b["name"]:b["parent"] for b in body["skeleton"]}==parents and garment["skeleton"]==body["skeleton"],"Body/garment portable skeleton changed")
    for bone in body["skeleton"]:
        require(len(bone["head_m"])==len(bone["tail_m"])==3 and
            all(math.isfinite(v) for v in bone["head_m"]+bone["tail_m"]) and
            math.dist(bone["head_m"],bone["tail_m"])>1e-6,"Invalid rest bone")
    require(garment.get("person_reference_id")==PERSON and garment.get("scene_date")==DATE and garment.get("identity_grade")=="attested" and
        garment.get("appearance_grade")=="reconstructed" and garment.get("production_eligible") is False and garment.get("roles")==ROLES and garment.get("garment_sources")==[],"Garment provenance/role changed")
    require(garment.get("body_input_sha256")==BODY_SHA and [m["name"] for m in garment["meshes"]]==PART_NAMES,"Body binding/garment component ownership changed")
    require(set(garment["materials"])==set(MATERIAL_NAMES),"Original material palette differs")
    for rgba in garment["materials"].values():require(len(rgba)==4 and all(math.isfinite(v) and 0<=v<=1 for v in rgba),"Invalid original palette")
    for mesh in body["meshes"]+garment["meshes"]:validate_mesh(mesh,set(parents))
    scene=json.loads((root/"data/scenes/1904.json").read_text());require(scene["target_date"]==DATE,"Actual scene date changed")
    require(manifest["household_path"]=="data/residents_1904/households/hh_glessner_john_j.json","Wrong household root")
    household=json.loads(pinned(root,manifest["household_path"],manifest["household_sha256"]))
    require(household["scene"]=="1904" and household["present_on_scene_date"]["value"]=="present","Person presence changed")
    source_person=next((p for p in household["persons"] if p["id"]==PERSON),None)
    require(source_person is not None and source_person["grade"]=="attested" and source_person["born"]["value"]=="1843" and source_person["occupation"]["value"]=="farm machinery executive","Identity facts changed")
    index=json.loads((root/"data/sidecars/1904/people.json").read_text())
    person=next((p for p in index["people"] if p["id"]==PERSON),None)
    require(person is not None and person["grade"]=="attested" and person["present"]=="present" and person["household"]==household["id"],"Actual compiled person differs")
    for sid in source_person["sources"]:require((root/"data/sources"/(sid+".json")).is_file(),"Unresolved identity source")
    identity={"person_id":PERSON,"name":source_person["name"],"person_reference_scene":"1904","identity_grade":"attested",
        "appearance_grade":"reconstructed","presence":"present","roles":ROLES,"historical_age_bound_years":[60,61],
        "body_age_years":61,"body_height_m":1.75,"sources_for_identity_only":source_person["sources"],
        "review_required":bool(source_person.get("review_required") or household.get("review_required") or person.get("review_required")),
        "touches_removal":bool(source_person.get("touches_removal") or household.get("touches_removal") or person.get("touches_removal")),
        "source_matched_appearance":False,"production_eligible":False}
    return body,garment,identity


def prepare_canonical_meshes(body,garment):
    """Explicit original-foot mask and shoe-grounding derivative, no BPy.

    Preserve immutable source inputs; face/vertex maps retain exact ownership.
    Removing anatomy under footwear is an authoring visibility operation, not
    anatomical editing, collision fit or a gait-contact acceptance.
    """
    canonical_garment=copy.deepcopy(garment)
    shifts={};shoe_tops=[]
    for mesh in canonical_garment["meshes"]:
        if mesh["name"] in FOOTWEAR_PARTS:
            old_min=min(p[1] for p in mesh["positions_m"])
            require(abs(old_min-.006)<1e-12,"Reviewed shoe source sole changed")
            shifts[mesh["name"]]=-old_min
            for p in mesh["positions_m"]:p[1]-=old_min
            shoe_tops.append(max(p[1] for p in mesh["positions_m"]))
    require(set(shifts)==FOOTWEAR_PARTS and len(shoe_tops)==2,"Exact two footwear parts")
    threshold=max(shoe_tops)
    require(abs(threshold-.115)<1e-12,"Reviewed derived shoe top changed")
    canonical_body=[];maps=[]
    for mi,source in enumerate(body["meshes"]):
        keep=[fi for fi,face in enumerate(source["triangles"]) if all(source["positions_m"][i][1]>=threshold for i in face)]
        kept=set(keep);removed=[fi for fi in range(len(source["triangles"])) if fi not in kept]
        used=sorted({i for fi in keep for i in source["triangles"][fi]});remap={old:new for new,old in enumerate(used)}
        require(keep and used and removed,"Nonempty source-owned barefoot visibility mask")
        result={**source,"positions_m":[source["positions_m"][i] for i in used],
            "uvs":[source["uvs"][i] for i in used],"weights":[source["weights"][i] for i in used],
            "source_vertex_indices":[source["source_vertex_indices"][i] for i in used],
            "triangles":[[remap[i] for i in source["triangles"][fi]] for fi in keep]}
        require(min(p[1] for p in result["positions_m"])>=threshold,"No unused barefoot source vertices exported")
        canonical_body.append(result)
        maps.append({"body_mesh":mi,"kept_source_face_indices":keep,"removed_source_face_indices":removed,
            "emitted_vertex_to_original_uv_split_vertex":used,"emitted_vertex_to_graphical_source_vertex":result["source_vertex_indices"]})
    receipt={"policy":"canonical-footwear-visibility-1904-v1","immutable_body_sha256":BODY_SHA,"immutable_garment_sha256":GARMENT_SHA,
        "shoe_y_translations_m":shifts,"body_face_mask":"Remove original body triangle if any vertexY is below max grounded shoe-topY; prune unused vertices preserving source maps",
        "body_mask_threshold_y_m":threshold,"body_source_maps":maps,"actual_pose_or_2mm_ground_contact_accepted":False,
        "source_inputs_mutated":False,"scope":"Authoring source derivative only; no collision, fit, animation or photographic acceptance"}
    return canonical_body,canonical_garment,receipt


def compose(root,manifest,authoring_output):
    body,garment,identity=validate_inputs(root,manifest)
    canonical_body,canonical_garment,derivations=prepare_canonical_meshes(body,garment)
    output=Path(authoring_output)
    require(output.suffix==".blend" and not output.exists(),"Fresh explicit canonical master output required")
    import bpy
    require(bpy.context.mode=="OBJECT" and len(bpy.context.scene.objects)==0,"Fresh empty isolated authoring scene required")
    name=ASSET+"_construction"
    require(name not in bpy.data.collections,"Never overwrite an earlier construction collection")
    collection=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(collection)
    arm=bpy.data.armatures.new(ASSET+"_skeleton");rig=bpy.data.objects.new(ASSET+"_rig",arm);collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    def frame(p):return (p[0],-p[2],p[1])
    bones={b["name"]:b for b in body["skeleton"]}
    contract=json.loads((Path(root)/"data/humans/contract.json").read_text())
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        for joint,parent in contract["skeleton"]["bones"]:
            bone=arm.edit_bones.new(joint);bone.head=frame(bones[joint]["head_m"]);bone.tail=frame(bones[joint]["tail_m"]);bone.roll=0
        for joint,parent in contract["skeleton"]["bones"]:
            if parent:arm.edit_bones[joint].parent=arm.edit_bones[parent];arm.edit_bones[joint].use_connect=False
    finally:bpy.ops.object.mode_set(mode="OBJECT")
    rig["person_reference_id"]=PERSON;rig["scene_date"]=DATE;rig["production_eligible"]=False
    # Confirm actual BPy rest state, rather than trusting joint names alone.
    require(set(rig.data.bones.keys())==set(bones),"Actual rig joint set differs")
    for joint,source in bones.items():
        actual=rig.data.bones[joint]
        require((actual.parent.name if actual.parent else None)==source["parent"],"Actual rig parent differs")
        require(math.dist(actual.head_local,frame(source["head_m"]))<=1e-7 and math.dist(actual.tail_local,frame(source["tail_m"]))<=1e-7,"Actual rest endpoints differ")
    materials={}
    for key,rgba in garment["materials"].items():
        material=bpy.data.materials.new(MATERIAL_NAMES[key]);material.use_nodes=True
        shader=material.node_tree.nodes["Principled BSDF"];shader.inputs["Base Color"].default_value=rgba;shader.inputs["Roughness"].default_value=.82
        materials[key]=material
    def object_mesh(source,name,material=None,reverse=False):
        mesh=bpy.data.meshes.new(name);faces=[(t[0],t[2],t[1]) if reverse else tuple(t) for t in source["triangles"]]
        mesh.from_pydata([frame(p) for p in source["positions_m"]],[],faces);mesh.update()
        uv=mesh.uv_layers.new(name="UVMap")
        for polygon in mesh.polygons:
            polygon.use_smooth=True
            for loop in polygon.loop_indices:uv.data[loop].uv=source["uvs"][mesh.loops[loop].vertex_index]
        obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
        if material is not None:mesh.materials.append(material)
        for joint,parent in contract["skeleton"]["bones"]:obj.vertex_groups.new(name=joint)
        for i,weights in enumerate(source["weights"]):
            for joint,value in weights.items():obj.vertex_groups[joint].add([i],value,"REPLACE")
        obj.modifiers.new("skin","ARMATURE").object=rig
        obj["person_reference_id"]=PERSON;obj["scene_date"]=DATE;obj["production_eligible"]=False;obj["appearance_grade"]="reconstructed"
        obj["source_winding_reversed"]=reverse
        return obj
    body_objects=[object_mesh(source,ASSET+"_body_"+str(i)) for i,source in enumerate(canonical_body)]
    garment_objects=[object_mesh(source,ASSET+"_"+source["name"],materials[source["material"]],source["name"] in REVERSE_WINDING) for source in canonical_garment["meshes"]]
    collection["person_reference_id"]=PERSON;collection["scene_date"]=DATE;collection["production_eligible"]=False
    return {"rig":rig,"collection":collection,"body_objects":body_objects,"garment_objects":garment_objects,"body":body,"identity":identity,
        "garment":garment,"contract":contract,"winding_reversed_parts":sorted(REVERSE_WINDING),"material_names":MATERIAL_NAMES,
        "body_object_sources":canonical_body,"garment_object_sources":canonical_garment["meshes"],"canonical_derivations":derivations,
        "remaining":"Shared caller must add cleared engineering skin/hair, eyes, morphs, fourLODs, sockets, clips and real provenance/liberty before saving/export. Fit, normals, material scale, anatomy and photographic quality remain unaccepted."}
