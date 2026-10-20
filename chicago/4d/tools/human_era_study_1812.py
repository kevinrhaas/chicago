# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in1812 named mature body/wardrobe composition; never the1835 builder.

Composition mechanics share the original1904 integration helper implementation.
Every identity/body/garment guard below is specific to1812 and source-backed
Kinzie the elder. No BPy has run; no canonical or photographic result exists.
"""
from pathlib import Path
import hashlib,json,math
DATE="1812-08-14"
PERSON="kinzie_john_elder"
ASSET="kinzie_john_elder_1812_study"
ROLES=["standing","walking"]
BODY_SHA="8dfb1a536eac2e505c5192093fb63ec03906d464ff3321380c862543d668570e"
GARMENT_SHA="1396fbb000806bee7384ac4c302cae5929faf7cbd38fc00468e1a080de8d806c"
MATERIAL_NAMES={"plain_linen_conjectural":"garment_upper__plain_shirt_1812",
 "plain_wool_dark_conjectural":"garment_outer__plain_waistcoat_1812",
 "plain_wool_trousers_conjectural":"garment_lower__plain_trousers_1812",
 "plain_leather_conjectural":"footwear__plain_low_shoes_1812"}
REVERSE_WINDING=frozenset()
PART_NAMES=["plain_shirt_conjectural_cut","plain_waistcoat_conjectural_open_front",
 "plain_trousers_conjectural_front_envelope","plain_low_shoes_conjectural"]


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

def compose(root,manifest,authoring_output):
    body,garment,identity=validate_inputs(root,manifest)
    body_sources,garment_sources,derivations=prepare_canonical_meshes(body,garment)
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
    body_objects=[object_mesh(source,ASSET+"_body_"+str(i)) for i,source in enumerate(body_sources)]
    garment_objects=[object_mesh(source,ASSET+"_"+source["name"],materials[source["material"]],source["name"] in REVERSE_WINDING) for source in garment_sources]
    collection["person_reference_id"]=PERSON;collection["scene_date"]=DATE;collection["production_eligible"]=False
    return {"rig":rig,"collection":collection,"body_objects":body_objects,"garment_objects":garment_objects,"body":body,"identity":identity,
        "garment":garment,"contract":contract,"winding_reversed_parts":sorted(REVERSE_WINDING),"material_names":MATERIAL_NAMES,"canonical_derivations":derivations,"body_object_sources":body_sources,"garment_object_sources":garment_sources,
        "remaining":"Shared caller must add cleared engineering skin/hair, eyes, morphs, fourLODs, sockets, clips and real provenance/liberty before saving/export. Fit, normals, material scale, anatomy and photographic quality remain unaccepted."}


def validate_inputs(root,manifest):
    root=Path(root)
    require(manifest.get("format")=="chicago4d_era_study_master_v1" and
            manifest.get("scene")=="1812" and manifest.get("scene_date")==DATE and
            manifest.get("asset_id")==ASSET and manifest.get("person_id")==PERSON,
            "Only explicit named1812 study is qualified")
    require(manifest.get("identity_grade")=="inferred" and
            manifest.get("appearance_grade")=="reconstructed" and
            manifest.get("production_eligible") is False and manifest.get("roles")==ROLES,
            "Do not upgrade identity/appearance or assign a driver/rider")
    require(manifest.get("body_sha256")==BODY_SHA and manifest.get("garment_sha256")==GARMENT_SHA,
            "Only reviewed actual age49 body and original wardrobe arrays")
    require(manifest.get("body_age_years")==49 and manifest.get("body_height_m")==1.75 and
            manifest.get("material_names")==MATERIAL_NAMES,"Original body/material authoring choices changed")
    require(manifest.get("canonical_derivations")=={"policy":"canonical-footwear-visibility-1812-v1"},
            "Explicit paired footwear registration/body visibility policy required")
    body=json.loads(pinned(root,manifest["body_path"],BODY_SHA))
    garment=json.loads(pinned(root,manifest["garment_path"],GARMENT_SHA))
    for value in [body,garment]:
        require(value.get("license")=="CC0-1.0" and value.get("units")=="m" and
                value.get("up_axis")=="+Y" and value.get("forward_axis")=="+Z",
                "Cleared metre/Y-up/+Z inputs required")
    require(body["target_blend"]["phenotype"]["chosen_age_years"]==49 and
            body["target_blend"]["phenotype"]["age_band_years"]==[48,49] and
            abs(body["report"]["chosen_height_m"]-1.75)<1e-9,"Mature body parameters changed")
    contract=json.loads((root/"data/humans/contract.json").read_text())
    parents=dict(contract["skeleton"]["bones"])
    require(len(body["skeleton"])==56 and {b["name"]:b["parent"] for b in body["skeleton"]}==parents and
            garment["skeleton"]==body["skeleton"],"Body/garment contract hierarchy must match exactly")
    for bone in body["skeleton"]:
        require(len(bone["head_m"])==len(bone["tail_m"])==3 and
                all(math.isfinite(v) for v in bone["head_m"]+bone["tail_m"]) and
                math.dist(bone["head_m"],bone["tail_m"])>1e-6,"Invalid source rest bone")
    require(garment.get("scene_date")==DATE and garment.get("person_reference_id")==PERSON and
            garment.get("identity_grade")=="inferred" and garment.get("appearance_grade")=="reconstructed" and
            garment.get("garment_geometry_grade")=="conjectural" and garment.get("garment_sources")==[] and
            garment.get("production_eligible") is False and garment.get("registered") is False and
            garment.get("ready_for_scene") is False and garment.get("allowed_study_roles")==ROLES,
            "Preserve conjectural clothing/date/identity and ineligibility")
    require(garment["body_input_sha256"]==BODY_SHA and
            [m["name"] for m in garment["meshes"]]==PART_NAMES and
            set(garment["materials"])==set(MATERIAL_NAMES),"Exact garment ownership changed")
    for rgba in garment["materials"].values():
        require(len(rgba)==4 and all(math.isfinite(v) and 0<=v<=1 for v in rgba),"Invalid material colour")
    for mesh in body["meshes"]+garment["meshes"]:
        validate_mesh(mesh,set(parents))
    require(json.loads((root/"data/scenes/1812.json").read_text())["target_date"]==DATE,
            "Actual scene target changed")
    require(manifest["household_path"]=="data/residents_1812/households/hh_kinzie_john_elder.json",
            "Never borrow the son's1835 identity")
    household=json.loads(pinned(root,manifest["household_path"],manifest["household_sha256"]))
    require(household["scene"]=="1812" and household["head"]==PERSON and
            household["present_on_scene_date"]["value"]=="present" and
            household["present_on_scene_date"]["confidence"]=="inferred","Date-qualified presence changed")
    people=household["persons"]
    require(len(people)==1 and people[0]["id"]==PERSON and people[0]["grade"]=="inferred" and
            people[0]["born"]["value"]=="1763","Distinct historical identity/birth-year changed")
    index=json.loads((root/"data/sidecars/1812/people.json").read_text())
    compiled=next((p for p in index["people"] if p["id"]==PERSON),None)
    require(compiled is not None and compiled["grade"]=="inferred" and
            compiled["present"]=="present" and compiled["household"]==household["id"],
            "Integrate and compile the actual1812 person before authoring")
    for sid in people[0]["sources"]:
        require((root/"data/sources"/(sid+".json")).is_file(),"Unresolved historical identity source")
    identity={"person_id":PERSON,"name":people[0]["name"],"person_reference_scene":"1812",
              "identity_grade":"inferred","appearance_grade":"reconstructed","presence":"present",
              "roles":ROLES,"historical_age_bound_years":[48,49],"body_age_years":49,
              "body_height_m":1.75,"sources_for_identity_only":people[0]["sources"],
              "source_matched_appearance":False,"production_eligible":False,
              "review_required":bool(people[0].get("review_required") or household.get("review_required") or compiled.get("review_required")),
              "touches_removal":bool(people[0].get("touches_removal") or household.get("touches_removal") or compiled.get("touches_removal"))}
    return body,garment,identity


def register_footwear(garment):
    """Explicit per-foot rigid translation; immutable source arrays stay exact.

    Offset shell construction put sole minima below y0. Register each separate
    footprint to the contract ground plane. This is not a walk/contact proof.
    """
    result=[]
    receipt={}
    for source in garment["meshes"]:
        if source["name"]!="plain_low_shoes_conjectural":
            result.append(source)
            continue
        positions=source["positions_m"]
        sides=["l" if p[0]>0 else "r" for p in positions]
        require(all(len({sides[i] for i in t})==1 for t in source["triangles"]),
                "Footwear triangles must never bridge separate feet")
        minima={side:min(p[1] for p,s in zip(positions,sides) if s==side) for side in ["l","r"]}
        require(all(-.02<y<.02 for y in minima.values()),"Unexpected sole source offset")
        shifted=[[p[0],p[1]-minima[side],p[2]] for p,side in zip(positions,sides)]
        result.append({**source,"positions_m":shifted})
        receipt={"source_component":source["name"],"source_sole_minimum_y_m":minima,
                 "applied_y_translation_m":{side:-y for side,y in minima.items()},
                 "rule":"Rigidly register each separate original footprint to y0; no source file changed",
                 "fit_or_walk_accepted":False}
    require(receipt,"Expected original footwear component")
    return result,receipt


def prepare_canonical_meshes(body,garment):
    registered,receipt=register_footwear(garment)
    shoes=next(m for m in registered if m["name"]=="plain_low_shoes_conjectural")
    threshold=max(p[1] for p in shoes["positions_m"])
    require(.13<threshold<.15,"Reviewed grounded shoe upper bound changed")
    masks=[]
    sources=[]
    for mi,source in enumerate(body["meshes"]):
        keep=[fi for fi,t in enumerate(source["triangles"])
              if min(source["positions_m"][i][1] for i in t)>=threshold]
        removed=sorted(set(range(len(source["triangles"]))) - set(keep))
        used=sorted({i for fi in keep for i in source["triangles"][fi]})
        require(removed and used and keep,"Nonempty source-owned barefoot visibility mask")
        remap={old:new for new,old in enumerate(used)}
        rendered={**source,"positions_m":[source["positions_m"][i] for i in used],
                  "uvs":[source["uvs"][i] for i in used],
                  "weights":[source["weights"][i] for i in used],
                  "source_vertex_indices":[source["source_vertex_indices"][i] for i in used],
                  "triangles":[[remap[i] for i in source["triangles"][fi]] for fi in keep]}
        require(min(p[1] for p in rendered["positions_m"])>=threshold,
                "No unreferenced nude sole vertices may remain in the canonical body")
        sources.append(rendered)
        masks.append({"body_mesh":mi,"kept_source_face_indices":keep,
                      "removed_source_face_indices":removed,
                      "emitted_vertex_to_original_uv_split_vertex":used,
                      "emitted_vertex_to_graphical_source_vertex":rendered["source_vertex_indices"]})
    derivations={**receipt,"policy":"canonical-footwear-visibility-1812-v1",
                 "immutable_body_sha256":BODY_SHA,"immutable_garment_sha256":GARMENT_SHA,
                 "body_face_mask":"Remove source triangles touching below max grounded shoe upperY, compact exact retained positions/UVs/weights; no bare sole geometry remains",
                 "body_mask_threshold_y_m":threshold,"body_source_maps":masks,
                 "body_full_anatomical_normal_field":"Preserved via graphical source IDs by shared caller",
                 "source_inputs_mutated":False,"actual_pose_or_2mm_ground_contact_accepted":False}
    return sources,registered,derivations
