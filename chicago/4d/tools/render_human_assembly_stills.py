#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read trusted same-job masters and render bounded Blender assembly proofs.

Run only through the existing pinned Blender4.5.3 CI launcher. No source save,
body/rig editing, historical appearance or photographic acceptance is performed.
The fixed3 source recipes/identities remain unchanged; studio objects live only
in a new in-memory scene. PNGs/receipts are the only written artifacts.
"""
from __future__ import annotations
import array
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ('bardwell_otis_1835', 'dufresne_joseph_1835', 'flynn_martin_1835')
OUTPUT = Path('/tmp/teamster-blender-stills')
BLENDER_VERSION = (4, 5, 3)
SIZE = 640
SAMPLES = 24
THREADS = 2


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024*1024):
            digest.update(chunk)
    return digest.hexdigest()


def source_state(objects):
    """Digest actual source geometry/UVs/weights/shapes and armature/pose state.

    Uses original datablocks, not evaluated render meshes. The actual digest
    is recorded before and after rendering in native Blender.
    """
    digest = hashlib.sha256()
    def record(value):
        digest.update(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
        digest.update(b'\0')
    def bulk(data, attribute, width, kind='f'):
        values = array.array(kind, [0])* (len(data)*width)
        if values:
            data.foreach_get(attribute, values)
        record((attribute, len(data), width, kind));digest.update(values.tobytes())
    for obj in sorted(objects, key=lambda item: item.name):
        record((obj.name, obj.type, obj.parent.name if obj.parent else None,
                [list(row) for row in obj.matrix_world], obj.hide_render))
        if obj.type == 'MESH':
            mesh = obj.data
            record((mesh.name, [m.name if m else None for m in mesh.materials]))
            bulk(mesh.vertices, 'co', 3)
            bulk(mesh.loops, 'vertex_index', 1, 'i')
            bulk(mesh.polygons, 'loop_start', 1, 'i')
            bulk(mesh.polygons, 'loop_total', 1, 'i')
            for layer in mesh.uv_layers:
                record(layer.name);bulk(layer.data, 'uv', 2)
            if mesh.shape_keys:
                for key in mesh.shape_keys.key_blocks:
                    record((key.name, key.value));bulk(key.data, 'co', 3)
            record([g.name for g in obj.vertex_groups])
            for vertex in mesh.vertices:
                record([(g.group, g.weight) for g in vertex.groups])
            record([(m.name, m.type, m.show_render, m.show_viewport,
                     getattr(getattr(m, 'object', None), 'name', None)) for m in obj.modifiers])
        if obj.type == 'ARMATURE':
            record([(b.name, b.parent.name if b.parent else None,
                     [list(row) for row in b.matrix_local], list(b.head_local), list(b.tail_local), b.use_deform) for b in obj.data.bones])
            record([(b.name, [list(row) for row in b.matrix_basis]) for b in obj.pose.bones])
            action = obj.animation_data.action if obj.animation_data else None
            record(('active_action', action.name if action else None, obj.data.pose_position))
    return digest.hexdigest()


def png_receipt(path):
    with path.open('rb') as stream:
        header = stream.read(24)
    need(header[:8] == b'\x89PNG\r\n\x1a\n' and header[12:16] == b'IHDR', 'actual PNG output absent')
    width, height = struct.unpack('>II', header[16:24])
    need((width, height) == (SIZE, SIZE), 'unexpected actual PNG dimensions')
    return {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path),
            'width': width, 'height': height}


def render_one(bpy, Vector, asset):
    master = ROOT / 'assets/authored/humans/teamsters' / asset / 'canonical.blend'
    need(master.is_file() and master.resolve().is_relative_to(ROOT), 'trusted canonical master missing/outside checkout')
    before_sha = sha(master)
    bpy.ops.wm.open_mainfile(filepath=str(master.resolve()), load_ui=False, use_scripts=False)
    original_scene = bpy.context.scene
    provenance = original_scene.get('chicago4d_human')
    need(provenance and provenance.get('asset_id') == asset and provenance.get('grade') == 'reconstructed'
         and provenance.get('recipe') == 'data/humans/recipes/worker_1835.json', 'actual master identity/recipe mismatch')
    lod = bpy.data.collections.get('lod0');rig = bpy.data.collections.get('rig')
    need(lod and rig, 'canonical lod0/rig collections missing')
    source_objects = list(bpy.data.objects)
    original_state = source_state(source_objects)
    meshes = [obj for obj in lod.all_objects if obj.type == 'MESH']
    need(meshes and all(obj.name.startswith(asset+'_') for obj in meshes), 'unexpected LOD0 source meshes')
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = [evaluated.matrix_world @ Vector(corner)
              for obj in meshes for evaluated in [obj.evaluated_get(depsgraph)] for corner in evaluated.bound_box]
    minimum = Vector(tuple(min(p[a] for p in points) for a in range(3)))
    maximum = Vector(tuple(max(p[a] for p in points) for a in range(3)))
    need(all(math.isfinite(v) for p in points for v in p), 'nonfinite evaluated source bounds')
    need(.9 <= maximum.z-minimum.z <= 2.3, 'unexpected measured assembly height')
    target = (minimum+maximum)/2
    # New in-memory scene reuses the unchanged source objects/datablocks. No
    # source collection visibility, pose/action, mesh, rig or material is edited.
    scene = bpy.data.scenes.new('_T1789_BLENDER_ASSEMBLY_PROOF')
    for obj in {o.name:o for o in [*lod.all_objects, *rig.all_objects]}.values():
        scene.collection.objects.link(obj)
    scene.render.engine = 'CYCLES';scene.cycles.device = 'CPU'
    scene.cycles.samples = SAMPLES;scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True;scene.cycles.adaptive_threshold = .05
    scene.cycles.max_bounces = 4;scene.cycles.transparent_max_bounces = 4
    scene.render.threads_mode = 'FIXED';scene.render.threads = THREADS
    scene.render.resolution_x = SIZE;scene.render.resolution_y = SIZE;scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG';scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8';scene.render.image_settings.compression = 15
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX';scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0;scene.view_settings.gamma = 1
    world = bpy.data.worlds.new('_T1789_STILL_WORLD');world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.12,.12,.12,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35;scene.world = world
    floor_mesh = bpy.data.meshes.new('_T1789_STILL_FLOOR')
    z = minimum.z-.003
    floor_mesh.from_pydata([(-4,-4,z),(4,-4,z),(4,4,z),(-4,4,z)], [], [(0,1,2,3)])
    floor = bpy.data.objects.new('_T1789_STILL_FLOOR', floor_mesh);scene.collection.objects.link(floor)
    material = bpy.data.materials.new('_T1789_STILL_FLOOR');material.use_nodes = True
    bsdf = material.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (.16,.17,.18,1);bsdf.inputs['Roughness'].default_value = .8
    floor.data.materials.append(material)
    lights = []
    for name, offset, watts, size in [('key',(-2.5,-3,3),700,2.5),('fill',(3,-2,1.5),300,3),('rim',(1,2.5,2.8),500,2)]:
        data = bpy.data.lights.new('_T1789_STILL_'+name, 'AREA');data.energy = watts;data.shape = 'DISK';data.size = size
        obj = bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);obj.location = target+Vector(offset)
        obj.rotation_euler = (target-obj.location).to_track_quat('-Z','Y').to_euler()
        lights.append({'name':name,'location_m':list(obj.location),'watts':watts,'size_m':size,'color':list(data.color)})
    data = bpy.data.cameras.new('_T1789_STILL_CAMERA');data.type = 'ORTHO';data.clip_start = .05;data.clip_end = 50
    camera = bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera)
    camera.location = target+Vector((.45,-1,.16)).normalized()*5
    rotation = (target-camera.location).to_track_quat('-Z','Y');camera.rotation_euler = rotation.to_euler()
    corners = [Vector((x,y,z)) for x in (minimum.x,maximum.x) for y in (minimum.y,maximum.y) for z in (minimum.z,maximum.z)]
    projected = [rotation.inverted() @ (p-target) for p in corners]
    data.ortho_scale = 1.14*max(max(p.x for p in projected)-min(p.x for p in projected),
                                max(p.y for p in projected)-min(p.y for p in projected))
    scene.camera = camera
    need(all(abs(p[a])/data.ortho_scale <= .5/1.14+1e-9 for p in projected for a in (0,1)), 'source bounding box outside intended camera margin')
    image = OUTPUT/(asset+'-assembly-threequarter.png');scene.render.filepath = str(image)
    receipt = {'asset_id':asset,'scope':'Blender still assembly proof only; no photographic acceptance',
               'source_master':str(master.relative_to(ROOT)),'master_sha256_before':before_sha,
               'person_reference_id':provenance.get('person_reference_id'),
               'person_reference_grade':provenance.get('person_reference_grade'),
               'sources':list(provenance.get('sources',[])),'liberty':provenance.get('liberty'),
               'source_body_rig_geometry_state_before':original_state,'frame':'as-saved source rest state; no pose/action changed',
               'lod':0,'source_meshes':[obj.name for obj in meshes],'source_bounds_m':{'min':list(minimum),'max':list(maximum)},
               'camera':{'type':'ORTHO','location_m':list(camera.location),'target_m':list(target),
                         'rotation_quaternion_wxyz':list(rotation),'ortho_scale_m':data.ortho_scale,'bbox_margin_factor':1.14,
                         'clip_start_m':data.clip_start,'clip_end_m':data.clip_end},
               'lighting':lights,'world_strength':.35,'floor_z_m':z,
               'engine':'CYCLES','device':'CPU','samples':SAMPLES,'threads':THREADS,'denoise':True,
               'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,
               'exposure':scene.view_settings.exposure,'photographic_acceptance':False,'production_eligibility_changed':False}
    try:
        bpy.ops.render.render(write_still=True, scene=scene.name)
        receipt['PNG'] = png_receipt(image)
        receipt['status'] = 'actual_native_render_completed'
    finally:
        receipt['master_sha256_after'] = sha(master)
        receipt['source_body_rig_geometry_state_after'] = source_state(source_objects)
        receipt['source_master_bytes_unchanged'] = receipt['master_sha256_after'] == before_sha
        receipt['source_body_rig_geometry_unchanged'] = receipt['source_body_rig_geometry_state_after'] == original_state
        receipt['source_protection_verified'] = receipt['source_master_bytes_unchanged'] and receipt['source_body_rig_geometry_unchanged']
        if 'PNG' not in receipt or not receipt['source_protection_verified']:
            receipt['status'] = 'failed_or_incomplete'
        (OUTPUT/(asset+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    need(receipt['source_master_bytes_unchanged'] and receipt['source_body_rig_geometry_unchanged'], 'source master/body/rig changed')
    return receipt


def main():
    # Imported ONLY by the real native pinned Blender process; no fake bpy path.
    import bpy
    from mathutils import Vector
    need(tuple(bpy.app.version) == BLENDER_VERSION, 'native Blender must match exact4.5.3 pin')
    need(not ('--' in sys.argv and sys.argv[sys.argv.index('--')+1:]), 'no arbitrary source/output/command arguments accepted')
    source = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    need(source == os.environ['GITHUB_SHA'], 'master job checkout is not actual definition source')
    need(not OUTPUT.exists(), 'fresh owned still output directory required')
    OUTPUT.mkdir()
    files = ['generators/blender.pin','tools/render_human_assembly_stills.py','tools/human_teamster_blend.py',
             'tools/human_export.py','data/humans/recipes/worker_1835.json']
    bound = {name:sha(ROOT/name) for name in files}
    manifest = {'scope':'Fixed3existing source assemblies rendered in native Blender; no historical likeness/photo acceptance',
                'source_sha':source,'definition_sha':os.environ['DEFINITION_SHA'],'run_id':os.environ['GITHUB_RUN_ID'],
                'run_attempt':os.environ['GITHUB_RUN_ATTEMPT'],'blender_version':bpy.app.version_string,
                'blender_build_hash':bpy.app.build_hash.decode(),'source_file_SHA256':bound,
                'fixed_assets':list(ASSETS),'photographic_acceptance':False,'production_eligibility_changed':False,'renders':[]}
    try:
        for asset in ASSETS:
            manifest['renders'].append(render_one(bpy,Vector,asset))
        need({name:sha(ROOT/name) for name in files} == bound, 'bound source files changed')
        need(len(manifest['renders']) == 3, 'all3actual stills required')
        manifest['status'] = 'actual_three_native_Blender_stills_completed'
    except Exception as error:
        manifest['status'] = 'failed_or_incomplete';manifest['error_type'] = type(error).__name__
        raise
    finally:
        (OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__':
    main()
