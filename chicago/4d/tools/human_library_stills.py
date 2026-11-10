# SPDX-License-Identifier: GPL-3.0-or-later
"""Render reconstructed assembly review stills; never save or export the source master.

blender -b --factory-startup --python tools/human_library_stills.py -- \
  --master canonical.blend --asset-id bardwell_otis_1835 --output-dir /tmp/stills
Requires Blender 4.5.3. These are render-only reconstructions, not historical photos
or acceptance of likeness, garment fit, period accuracy or photographic quality.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SIZE = (512, 768)
VIEWS = (('front', 0), ('threequarter', 45), ('profile', 90))


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_paths(master, output):
    master, output = master.resolve(), output.resolve()
    if master.suffix != '.blend' or not master.is_file():
        raise ValueError('master must be an existing .blend file')
    if output == master or (output.exists() and not output.is_dir()):
        raise ValueError('output-dir must be a directory separate from the master')
    if any((output / name).exists() for name in ['manifest.json', *[v[0]+'.png' for v in VIEWS]]):
        raise ValueError('refusing existing still outputs; choose a fresh output directory')
    return master, output


def validate_identity(metadata, asset_id, root=ROOT):
    if metadata.get('asset_id') != asset_id or metadata.get('skeleton') != 'c4d_humanoid_v1':
        raise ValueError('master asset identity/shared skeleton differs from request')
    recipe_path = (root / metadata.get('recipe', '')).resolve()
    if not recipe_path.is_relative_to((root / 'data/humans/recipes').resolve()) or not recipe_path.is_file():
        raise ValueError('master must name an existing project human recipe')
    recipe = json.loads(recipe_path.read_text())
    variants = [v for v in recipe.get('proof_variants', []) if v['id'] == asset_id]
    if len(variants) != 1:
        raise ValueError('master asset must match exactly one actual recipe variant')
    fields = ('person_reference_id', 'person_reference_scene', 'person_reference_grade')
    if any(not metadata.get(k) or metadata[k] != variants[0].get(k) for k in fields):
        raise ValueError('master person identity differs from actual recipe variant')
    if metadata.get('grade') != 'reconstructed':
        raise ValueError('assembly appearance must remain reconstructed')
    return {'asset_id': asset_id, **{k: metadata[k] for k in fields},
            'recipe': str(recipe_path.relative_to(root)), 'recipe_sha256': sha256(recipe_path)}


def framing(points):
    """One conservative orthographic scale encloses all three camera projections."""
    points = [tuple(p) for p in points]
    if not points or any(len(p) != 3 or not all(math.isfinite(x) for x in p) for p in points):
        raise ValueError('evaluated LOD0 bounds must be finite nonempty 3D points')
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    if any(hi[i] - lo[i] <= 1e-6 for i in range(3)) or not .45 <= hi[2]-lo[2] <= 2.5:
        raise ValueError('evaluated LOD0 bounds are degenerate or outside human metre scale')
    center = [(a+b)/2 for a, b in zip(lo, hi)]
    corners = list(itertools.product(*zip(lo, hi)))
    width = max(2*abs((p[0]-center[0])*math.cos(math.radians(a)) +
                      (p[1]-center[1])*math.sin(math.radians(a))) for p in corners for _, a in VIEWS)
    return {'min_m': lo, 'max_m': hi, 'target_m': center,
            'ortho_scale_m': max(hi[2]-lo[2], width*SIZE[1]/SIZE[0])*1.16}


def verify_outputs(output):
    """Refuse missing, truncated or wrong-size PNG render receipts."""
    records = []
    for name, _ in VIEWS:
        path = output / (name+'.png')
        if not path.is_file():
            raise ValueError(f'missing rendered output: {path.name}')
        with path.open('rb') as stream:
            header = stream.read(24)
            stream.seek(max(0, path.stat().st_size-12))
            trailer = stream.read()
        if len(header) != 24 or header[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' or struct.unpack('>II', header[16:24]) != SIZE:
            raise ValueError(f'invalid PNG header/resolution: {path.name}')
        if path.stat().st_size < 100 or trailer != b'\x00\x00\x00\x00IEND\xaeB`\x82':
            raise ValueError(f'truncated rendered output: {path.name}')
        records.append({'view': name, 'file': path.name, 'sha256': sha256(path), 'bytes': path.stat().st_size})
    return records


def render(master, asset_id, output):
    import bpy
    from mathutils import Vector
    master, output = validate_paths(master, output)
    before = sha256(master)
    try:
        if bpy.app.version != (4, 5, 3):
            raise ValueError('assembly still producer requires Blender 4.5.3')
        bpy.ops.wm.open_mainfile(filepath=str(master), load_ui=False, use_scripts=False)
        source = bpy.context.scene
        metadata = source.get('chicago4d_human', {})
        identity = validate_identity(metadata, asset_id)
        rig = bpy.data.objects.get('c4d_armature')
        lod = bpy.data.collections.get('lod0')
        rigcol = bpy.data.collections.get('rig')
        contract = json.loads((ROOT/'data/humans/contract.json').read_text())
        expected = dict(contract['skeleton']['bones'])
        if rig is None or rig.type != 'ARMATURE' or rigcol is None or rig not in rigcol.all_objects[:]:
            raise ValueError('master must carry its shared c4d_armature in rig')
        if {b.name: b.parent.name if b.parent else None for b in rig.data.bones} != expected:
            raise ValueError('master shared rig bone names/parents differ from contract')
        meshes = sorted((o for o in lod.all_objects if o.type == 'MESH'), key=lambda o: o.name) if lod else []
        if not meshes or any(not any(m.type == 'ARMATURE' and m.object == rig for m in o.modifiers) for o in meshes):
            raise ValueError('master needs LOD0 meshes bound to the same shared rig')
        images = {node.image for o in meshes for mat in o.data.materials if mat and mat.use_nodes
                  for node in mat.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image}
        if any(image.source == 'FILE' and not image.packed_file for image in images):
            raise ValueError('master texture images must remain packed, without external substitutions')
        idle = bpy.data.actions.get('idle')
        if idle is None:
            raise ValueError('master lacks explicit idle action')
        studio = bpy.data.scenes.new('RENDER_ONLY_assembly_studio')
        bpy.context.window.scene = studio
        for obj in [rig, *meshes]:
            studio.collection.objects.link(obj)
            obj.hide_render = False
            obj.hide_viewport = False
            obj.hide_set(False)
        rig.animation_data_create()
        rig.animation_data.use_nla = False
        rig.animation_data.action = idle
        if idle.slots:
            rig.animation_data.action_slot = idle.slots[0]
        studio.frame_set(1)
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        bounds = framing([o.evaluated_get(deps).matrix_world @ Vector(p)
                          for o in meshes for p in o.evaluated_get(deps).bound_box])
        target = Vector(bounds['target_m'])
        studio.render.engine = 'CYCLES'
        studio.cycles.device = 'CPU'
        studio.cycles.samples = 32
        studio.cycles.seed = 1789
        studio.cycles.use_denoising = True
        studio.cycles.denoiser = 'OPENIMAGEDENOISE'
        studio.render.resolution_x, studio.render.resolution_y = SIZE
        studio.render.resolution_percentage = 100
        studio.render.image_settings.file_format = 'PNG'
        studio.render.image_settings.color_mode = 'RGB'
        studio.render.image_settings.color_depth = '8'
        studio.view_settings.view_transform = 'AgX'
        studio.world = bpy.data.worlds.new('RENDER_ONLY_neutral_world')
        studio.world.use_nodes = True
        studio.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18, .18, .18, 1)
        studio.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
        bpy.ops.mesh.primitive_plane_add(size=200, location=(target.x, target.y, bounds['min_m'][2]-.002))
        floor = bpy.context.object
        floor.name = 'RENDER_ONLY_floor'
        mat = bpy.data.materials.new('RENDER_ONLY_floor')
        mat.diffuse_color = (.18, .18, .18, 1)
        floor.data.materials.append(mat)
        lights = []
        for name, offset, energy, size in [('key', (-3, -4, 4), 650, 4), ('fill', (3, -2, 2), 350, 3), ('rim', (1, 3, 3), 500, 3)]:
            data = bpy.data.lights.new('RENDER_ONLY_'+name, 'AREA')
            data.energy, data.shape, data.size = energy, 'DISK', size
            obj = bpy.data.objects.new(data.name, data)
            studio.collection.objects.link(obj)
            obj.location = target + Vector(offset)
            obj.rotation_euler = (target-obj.location).to_track_quat('-Z', 'Y').to_euler()
            lights.append({'name': name, 'location_m': list(obj.location), 'energy_w': energy, 'size_m': size})
        camera = bpy.data.objects.new('RENDER_ONLY_camera', bpy.data.cameras.new('RENDER_ONLY_camera'))
        studio.collection.objects.link(camera)
        studio.camera = camera
        camera.data.type, camera.data.ortho_scale = 'ORTHO', bounds['ortho_scale_m']
        camera.data.sensor_fit = 'VERTICAL'
        output.mkdir(parents=True, exist_ok=True)
        cameras = []
        for name, angle in VIEWS:
            rad = math.radians(angle)
            camera.location = target + Vector((5*math.sin(rad), -5*math.cos(rad), 0))
            camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
            studio.render.filepath = str(output/(name+'.png'))
            bpy.ops.render.render(write_still=True, scene=studio.name)
            cameras.append({'view': name, 'azimuth_deg': angle, 'location_m': list(camera.location), 'rotation_euler_rad': list(camera.rotation_euler)})
        manifest = {'schema': 'chicago4d_human_assembly_stills_v1', 'identity': identity,
                    'source_master': str(master), 'source_sha256': before, 'blender_version': bpy.app.version_string,
                    'pose': {'action': 'idle', 'frame': 1, 'nla_enabled': False, 'basis': str(idle.get('motion_basis', 'reconstructed mechanical pose'))}, 'lod': 0,
                    'bone_count': len(rig.data.bones), 'mesh_count': len(meshes),
                    'parts': [{'name': o.name, 'materials': [m.name if m else None for m in o.data.materials]} for o in meshes],
                    'textures': [{'name': image.name, 'packed': bool(image.packed_file), 'size': list(image.size)} for image in sorted(images, key=lambda image: image.name)],
                    'bounds_and_framing': bounds, 'cameras': cameras, 'lights': lights,
                    'render': {'engine': 'CYCLES', 'device': 'CPU', 'samples': 32, 'seed': 1789, 'denoiser': 'OPENIMAGEDENOISE', 'resolution': SIZE, 'view_transform': 'AgX', 'world_strength': .35, 'world_color_linear_rgba': [.18, .18, .18, 1], 'camera_sensor_fit': 'VERTICAL'},
                    'provenance': {'grade': 'reconstructed', 'render_only': True, 'historical_photo_reference': False,
                                   'likeness_accepted': False, 'fit_accepted': False, 'photo_quality_accepted': False,
                                   'basis': str(metadata.get('basis', '')), 'sources': list(metadata.get('sources', [])), 'liberty': metadata.get('liberty')},
                    'outputs': verify_outputs(output)}
    finally:
        if sha256(master) != before:
            raise RuntimeError('source master changed during render')
    manifest['source_sha256_after'] = before
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master', required=True, type=Path)
    parser.add_argument('--asset-id', required=True)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    render(args.master, args.asset_id, args.output_dir)
