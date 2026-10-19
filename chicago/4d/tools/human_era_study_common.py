# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in era-study canonical helpers. No BPy import during source validation.

Contract compliance is necessary for a usable study; it is not photographic,
period-clothing, likeness, deformation or scene-placement acceptance.
"""
from pathlib import Path
import hashlib
import json
import math
import re

ERAS = {"1812": ("1812-08-14", "kinzie_john_elder", "inferred", 49),
        "1904": ("1904-07-01", "glessner_john_j", "attested", 61)}


def need(value, message):
    if not value:
        raise ValueError(message)


def source_file(root, relative, digest=None):
    root = Path(root).resolve()
    rel = Path(relative)
    need(not rel.is_absolute() and ".." not in rel.parts, "Root-relative study input required")
    path = (root/rel).resolve()
    need(path.is_relative_to(root) and path.is_file(), "Study input absent or outside checkout")
    if digest:
        need(hashlib.sha256(path.read_bytes()).hexdigest() == digest,
             "Exact reviewed input differs: " + relative)
    return path


def validate_manifest(root, manifest, liberty):
    need(manifest.get("format") == "chicago4d_era_study_master_v1", "Unknown study manifest")
    era = manifest.get("scene")
    need(era in ERAS, "Only opted-in1812/1904 studies are supported")
    date, person, grade, age = ERAS[era]
    need(manifest.get("scene_date") == date and manifest.get("person_id") == person and
         manifest.get("identity_grade") == grade and manifest.get("body_age_years") == age,
         "Fixed named identity/date/age bounds changed")
    need(manifest.get("asset_id") == person+"_"+era+"_study" and
         manifest.get("appearance_grade") == "reconstructed" and
         manifest.get("production_eligible") is False,
         "Only unaccepted named study assets may be built")
    wanted = ["standing", "walking"] + (["passenger"] if era == "1904" else [])
    need(manifest.get("roles") == wanted, "No driver/rider/event assignment is supplied")
    need(manifest.get("lod_ratios") == [1., .6, .28, .12], "Four fixed study LOD ratios required")
    need(isinstance(liberty, str) and re.fullmatch(r"L[0-9]+", liberty),
         "Integrator must supply a real numeric LIBERTIES heading")
    liberties = source_file(root, "docs/LIBERTIES.md").read_text(errors="surrogateescape")
    need(re.search(r"^### "+re.escape(liberty)+r" ", liberties, re.M),
         "Supplied liberty is not an actual integrated heading")
    scene = json.loads(source_file(root, "data/scenes/"+era+".json").read_text())
    need(scene["target_date"] == date, "Actual scene target date changed")
    for key in ["body", "garment", "household"]:
        source_file(root, manifest[key+"_path"], manifest[key+"_sha256"])
    source_file(root, manifest["body_target_recipe_path"], manifest["body_target_recipe_sha256"])
    body = json.loads(source_file(root, manifest["body_path"], manifest["body_sha256"]).read_text())
    need(body["target_blend"]["recipe_sha256"] == manifest["body_target_recipe_sha256"],
         "Full body must retain its exact reproducible graphical target recipe")
    contract = json.loads(source_file(root, "data/humans/contract.json").read_text())
    skin = manifest["skin_texture"]
    need(skin["license"] == "CC0-1.0" and skin["color_space"] == "sRGB",
         "Only reviewed cleared skin component is allowed")
    source_file(root, skin["path"], skin["sha256"])
    skin_source = json.loads(source_file(root, skin["source_manifest_path"],
                                        skin["source_manifest_sha256"]).read_text())
    need(skin_source["license"] == "CC0-1.0" and
         skin_source["license_evidence"]["record"]["license"] == "CC0",
         "Skin source lacks its actual per-asset CC0 evidence")
    need(skin["sha256"] == "5a53213f061bfa97ee0afd6b40650ffbc089a479c144e63f3c39acceca5853c0",
         "No unreviewed skin substitution")
    need(skin.get("identity_basis") and skin.get("age_limit"),
         "Reusable skin/young-atlas age limitations must remain explicit")
    need(type(skin.get("roughness")) in (int, float) and
         math.isfinite(skin["roughness"]) and 0 <= skin["roughness"] <= 1,
         "Skin roughness must be a finite engineering value within0..1")
    slots = {name.split("__")[0] for name in manifest["material_names"].values()}
    need({"garment_upper", "garment_lower", "footwear"} <= slots,
         "Wardrobe must supply the portable required clothing slots")
    return contract


def mesh_object(name, data, rig, collection, material):
    import bpy
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(p[0], -p[2], p[1]) for p in data["positions_m"]], [], data["triangles"])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        poly.use_smooth = True
        for loop in poly.loop_indices:
            uv.data[loop].uv = data["uvs"][mesh.loops[loop].vertex_index]
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    for bone in rig.data.bones:
        obj.vertex_groups.new(name=bone.name)
    for i, weights in enumerate(data["weights"]):
        for bone, weight in weights.items():
            obj.vertex_groups[bone].add([i], weight, "REPLACE")
    obj.modifiers.new("skin", "ARMATURE").object = rig
    return obj


def skin_and_hair(root, manifest, study):
    import bpy
    from human_hair_short04 import fit
    from human_source_normals import source_shared_normals
    from mathutils import Vector
    skin = manifest["skin_texture"]
    material = bpy.data.materials.new("skin")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1, 1, 1, 1)
    shader.inputs["Roughness"].default_value = skin["roughness"]
    image = bpy.data.images.load(str(source_file(root, skin["path"], skin["sha256"])), check_existing=True)
    image.colorspace_settings.name = "sRGB"
    image.pack()
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    normal_receipts = []
    sources = study.get("body_object_sources", study["body"]["meshes"])
    for obj, source, full in zip(study["body_objects"], sources, study["body"]["meshes"]):
        obj.data.materials.clear()
        obj.data.materials.append(material)
        # Preserve the full original anatomical normal field across the explicit
        # footwear visibility mask; do not regenerate cut-boundary normals.
        full_normals = source_shared_normals(full["positions_m"], full["triangles"], full["source_vertex_indices"])
        by_id = {sid: normal for sid, normal in zip(full["source_vertex_indices"], full_normals)}
        normals = [by_id[sid] for sid in source["source_vertex_indices"]]
        normals = [Vector((n[0], -n[2], n[1])).normalized() for n in normals]
        obj.data.normals_split_custom_set([normals[loop.vertex_index] for loop in obj.data.loops])
        obj.data.update()
        need(obj.data.has_custom_normals and len(obj.data.corner_normals) == len(obj.data.loops),
             "Actual source-body normal readback absent")
        delta = max(math.dist(tuple(obj.data.corner_normals[i].vector), normals[loop.vertex_index])
                    for i, loop in enumerate(obj.data.loops))
        need(delta <= 1e-3, "Unchanged RAW1e-3 source-body normal readback failed")
        normal_receipts.append({"mesh": obj.name, "maximum_raw_vector_delta": delta,
                                "bound": 1e-3, "scope": "Actual BPy body before LOD/export only"})
    hair, hair_path, report = fit(study["body"], manifest["hair_component"], Path(root))
    config = manifest["hair_component"]
    material = bpy.data.materials.new("hair__makehuman_short04")
    material.use_nodes = True
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    material.use_backface_culling = False
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (1, 1, 1, 1)
    shader.inputs["Roughness"].default_value = config["roughness"]
    image = bpy.data.images.load(str(hair_path), check_existing=True)
    need(tuple(image.size) == (2048, 2057), "Reviewed padded hair image dimensions changed")
    image.colorspace_settings.name = "sRGB"
    image.pack()
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "EXTEND"
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    clip = material.node_tree.nodes.new("ShaderNodeMath")
    clip.operation = "LESS_THAN"
    clip.inputs[1].default_value = config["alpha_cutoff"]
    material.node_tree.links.new(texture.outputs["Alpha"], clip.inputs[0])
    inverse = material.node_tree.nodes.new("ShaderNodeMath")
    inverse.operation = "SUBTRACT"
    inverse.inputs[0].default_value = 1
    material.node_tree.links.new(clip.outputs[0], inverse.inputs[1])
    material.node_tree.links.new(inverse.outputs[0], shader.inputs["Alpha"])
    obj = mesh_object(manifest["asset_id"]+"_hair", hair, study["rig"], study["collection"], material)
    study["accessory_objects"] = [obj]
    return report, normal_receipts


def add_eyes(study):
    import bpy
    material = bpy.data.materials.new("eyes")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (.12, .09, .06, 1)
    shader.inputs["Roughness"].default_value = .18
    bones = {b["name"]: b for b in study["body"]["skeleton"]}
    data = {"positions_m": [], "triangles": [], "uvs": [], "weights": []}
    segments, rings, radius = 12, 6, .010
    for side in ("l", "r"):
        center = bones["eye_"+side]["head_m"]
        first = len(data["positions_m"])
        def vertex(point, uv):
            data["positions_m"].append([center[i]+point[i] for i in range(3)])
            data["uvs"].append(uv)
            data["weights"].append({"eye_"+side: 1.})
        vertex([0, radius, 0], [.5, 0])
        for j in range(1, rings):
            theta = math.pi*j/rings
            for k in range(segments):
                phi = 2*math.pi*k/segments
                vertex([radius*math.sin(theta)*math.cos(phi), radius*math.cos(theta),
                        radius*math.sin(theta)*math.sin(phi)], [k/segments, j/rings])
        bottom = len(data["positions_m"])
        vertex([0, -radius, 0], [.5, 1])
        for k in range(segments):
            following = (k+1)%segments
            data["triangles"].append([first, first+1+following, first+1+k])
            for j in range(rings-2):
                a = first+1+j*segments+k
                b = first+1+j*segments+following
                data["triangles"].extend([[a, b, b+segments], [a, b+segments, a+segments]])
            a = first+1+(rings-2)*segments+k
            b = first+1+(rings-2)*segments+following
            data["triangles"].append([a, b, bottom])
    obj = mesh_object("original_reconstructed_eyes", data, study["rig"], study["collection"], material)
    study["accessory_objects"].append(obj)


def add_morphs(obj, body):
    from mathutils import Matrix, Vector
    bones = {b["name"]: b for b in body["skeleton"]}
    frame = lambda p: Vector((p[0], -p[2], p[1]))
    obj.shape_key_add(name="Basis")
    for side, label in (("l", "Left"), ("r", "Right")):
        key = obj.shape_key_add(name="eyeBlink"+label)
        center = frame(bones["eye_"+side]["head_m"])
        for i, vertex in enumerate(obj.data.vertices):
            if abs(vertex.co.x-center.x)<.035 and abs(vertex.co.z-center.z)<.023 and abs(vertex.co.y-center.y)<.045:
                key.data[i].co.z = center.z+(vertex.co.z-center.z)*.08
        need(max((key.data[i].co-v.co).length for i, v in enumerate(obj.data.vertices)) > .001,
             "Blink target must actually move source eyelid vertices >1mm")
    key = obj.shape_key_add(name="jawOpen")
    pivot = frame(bones["jaw"]["head_m"])
    rotation = Matrix.Rotation(math.radians(12), 3, "X")
    for i, vertex in enumerate(obj.data.vertices):
        if pivot.z-.10 < vertex.co.z < pivot.z+.015 and abs(vertex.co.x)<.085 and vertex.co.y<pivot.y+.045:
            key.data[i].co = pivot+rotation@(vertex.co-pivot)
    need(max((key.data[i].co-v.co).length for i, v in enumerate(obj.data.vertices)) > .001,
         "jawOpen target must actually move source jaw vertices >1mm")


def lods_sockets_actions(study, manifest, contract):
    import bpy
    from mathutils import Matrix, Vector, Quaternion
    from human_grounded_gait import (prepare_legs, pose_at_phase, linearize_action,
                                     SPEED_M_S, CYCLE_DURATION_S, CYCLE_FRAMES, STANCE_FRACTION)
    scene, rig = bpy.context.scene, study["rig"]
    originals = [*study["body_objects"], *study["garment_objects"], *study["accessory_objects"]]
    for lod, ratio in enumerate(manifest["lod_ratios"]):
        collection = bpy.data.collections.new("lod"+str(lod))
        scene.collection.children.link(collection)
        for source in originals:
            obj = source.copy()
            obj.data = source.data.copy()
            obj.name = source.name+"_lod"+str(lod)
            collection.objects.link(obj)
            if ratio < 1 and source not in study["accessory_objects"]:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                modifier = obj.modifiers.new("authored_lod_reduction", "DECIMATE")
                modifier.ratio = ratio
                for _ in range(len(obj.modifiers)):
                    if obj.modifiers.find(modifier.name) == 0:
                        break
                    need("FINISHED" in bpy.ops.object.modifier_move_up(modifier=modifier.name),
                         "Decimator could not precede actual skin modifier")
                need(obj.modifiers.find(modifier.name) == 0, "Bounded modifier reorder failed")
                need("FINISHED" in bpy.ops.object.modifier_apply(modifier=modifier.name),
                     "Actual LOD decimation did not finish")
            if source in study["body_objects"] and lod in contract["morphs"]["required_lods"]:
                add_morphs(obj, study["body"])
        need(any(o.type == "MESH" for o in collection.objects), "Every LOD must contain actual meshes")
    # Remove construction meshes from export scene; copies are the canonical LODs.
    for obj in originals:
        bpy.data.objects.remove(obj, do_unlink=True)
    bones = {b["name"]: b for b in study["body"]["skeleton"]}
    for name, bone in contract["sockets"]["required"]:
        obj = bpy.data.objects.new(name, None)
        study["collection"].objects.link(obj)
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = bone
        a, b = (Vector((p[0], -p[2], p[1])) for p in (bones[bone]["head_m"], bones[bone]["tail_m"]))
        bpy.context.view_layer.update()
        obj.matrix_world = Matrix.Translation(b if bone == "head" else (a+b)/2) @ Matrix.Rotation(math.radians(-90 if bone == "head" else 90), 4, "X")
    rig.animation_data_create()
    legs = prepare_legs(bones, 1.)
    for clip, length in (("idle", 60), ("walk", CYCLE_FRAMES)):
        action = bpy.data.actions.new(clip)
        action.use_fake_user = True
        rig.animation_data.action = action
        action["motion_basis"] = "Original mechanical standing/walk study; no biological, cloth-fit or historical-event acceptance"
        action["loop"] = True
        if clip == "walk":
            action["speed_m_s"] = SPEED_M_S
            action["cycle_duration_s"] = CYCLE_DURATION_S
            action["stance_fraction"] = STANCE_FRACTION
        frames = range(1, length+2) if clip == "walk" else range(1, length+2, 5)
        for frame in frames:
            fraction = (frame-1)/length
            gait = pose_at_phase(legs, fraction) if clip == "walk" else None
            for pose in rig.pose.bones:
                name = pose.name
                pose.location = (0, 0, 0)
                rotation = Quaternion((1, 0, 0), 0)
                if name.startswith("upperarm"):
                    rotation = Quaternion((0, 1, 0), math.radians(78 if name.endswith("_l") else -78))
                if gait and name in gait["x_rotations_rad"]:
                    rotation = Quaternion((1, 0, 0), gait["x_rotations_rad"][name])
                if name == "spine_02":
                    rotation = Quaternion((1, 0, 0), math.radians(.6)*math.sin(2*math.pi*fraction))
                basis = rig.data.bones[name].matrix_local.to_quaternion()
                pose.rotation_mode = "QUATERNION"
                pose.rotation_quaternion = basis.inverted()@rotation@basis
                if gait and name == "pelvis":
                    dx, dy, dz = gait["pelvis_delta_m"]
                    pose.location = basis.inverted()@Vector((dx, -dz, dy))
                pose.keyframe_insert("rotation_quaternion", frame=frame)
                pose.keyframe_insert("location", frame=frame)
        linearize_action(action)
    rig.animation_data.action = None
    for pose in rig.pose.bones:
        pose.location = (0, 0, 0)
        pose.rotation_mode = "QUATERNION"
        pose.rotation_quaternion = (1, 0, 0, 0)


def provenance(manifest, contract, liberty, master, identity, hair_report, normals):
    return {"contract_version": contract["version"], "rigid_bone_frame_export": True,
            "kind": "body", "asset_id": manifest["asset_id"], "lod": 0,
            "skeleton": contract["skeleton"]["id"], "grade": "reconstructed",
            "basis": "Original unaccepted era study. Listed historical sources support identity only, not this outfit, appearance or staged action. Named identity retains its own grade; appearance, body shape, outfit, palette and action are reconstruction. Garment sources are absent, cuts conjectural. Cleared young skin atlas and shared hair are reusable engineering components, not age-matched likeness or recorded complexion. No photographic, garment-fit, historical-event or production acceptance.",
            "sources": identity["sources_for_identity_only"], "liberty": liberty, "license": "CC0-1.0",
            "master": str(master), "authored_by": "Chicago4D opt-in era-study authoring",
            "recipe": "data/humans/recipes/era_studies/"+manifest["scene"]+".json",
            "person_reference_id": manifest["person_id"], "person_reference_scene": manifest["scene"],
            "person_reference_grade": manifest["identity_grade"], "production_eligible": False,
            "person_reference_summary_json": json.dumps(identity, sort_keys=True),
            "body_input": manifest["body_path"], "body_input_sha256": manifest["body_sha256"],
            "garment_input": manifest["garment_path"], "garment_input_sha256": manifest["garment_sha256"],
            "garment_sources_json": "[]", "skin_source_json": json.dumps(manifest["skin_texture"], sort_keys=True),
            "hair_source_json": json.dumps(hair_report, sort_keys=True),
            "body_normal_readback_json": json.dumps(normals, sort_keys=True)}
