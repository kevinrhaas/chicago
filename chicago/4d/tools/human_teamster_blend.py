# SPDX-License-Identifier: GPL-3.0-or-later
"""Build an existing-resident-referenced reconstructed workwear canonical master; never changes fixture.

blender -b --factory-startup --python tools/human_teamster_blend.py -- \
  --recipe data/humans/recipes/worker_1835.json --variant bardwell_otis_1835 --output OUT.blend
blender -b OUT.blend --python tools/human_export.py -- assets/humans

The body JSON is prepared from cleared CC0 assets by the separate preprocessing tool.
No Blender installation or execution is part of this authoring task. Bone geometry and
UV seam splits come from that input; pattern/color/fit choices are reconstruction.
This builder must be executed and its outputs reviewed before any completion claim.

Unverified until the Blender bake/CI worker executes this code:
- BPy armature, modifier/LOD and action export compatibility with the worker version;
- source A-to-T palm roll, arm/hip correctives, four-influence deformation;
- shirt/waistcoat/trouser/shoe/collar boundary fit and seated/intersection behavior;
- selected blink/jaw regions and meaningful exported morph amplitudes;
- per-material UV overlap/density after decimation (source UV coordinates retained);
- all four human_contract --glb checks, master/web parity and Khronos validation;
- desktop/mobile close renders and grounded idle/walk/contact review.
The synthetic walk is a pose fixture, not measured biomechanical motion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools'))
from human_grounded_gait import (prepare_legs, pose_at_phase, linearize_action,
                                 SPEED_M_S, CYCLE_DURATION_S, CYCLE_FRAMES,
                                 STANCE_FRACTION)
from human_workwear_fit import garment_shell, fitted_shoes, standing_collar_extension
from human_eye_components import build_eye_components, iris_pixels, MATERIALS as EYE_MATERIALS
from human_period_wardrobe import (resolve_wardrobe, finish_edges, waistcoat_buttons,
                                   work_hat, round_jacket)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--body', type=Path)
    p.add_argument('--sit-drive-study', type=Path, help='Explicit reconstructed1835 named-resident/W01 seated study profile')
    p.add_argument('--sit-drive-vehicle', type=Path, help='Actual exported physical driver-bench wagon sidecar')
    p.add_argument('--recipe', type=Path, default=ROOT/'data/humans/recipes/worker_1835.json')
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--liberty', help='Existing project LIBERTIES entry assigned by the integrator')
    p.add_argument('--variant', required=True, help='Required existing-resident recipe variant ID; no generic default')
    p.add_argument('--experimental-normal-probes',action='store_true',help='Explicit isolated-CI experiment only; no default normal method change')
    p.add_argument('--normal-probe-receipts',type=Path,help='Required /tmp directory for experimental normal diagnostics')
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    args=p.parse_args(argv)
    if bool(args.sit_drive_study)!=bool(args.sit_drive_vehicle):
        p.error("--sit-drive-study and --sit-drive-vehicle must be supplied together")
    if args.experimental_normal_probes:
        if args.normal_probe_receipts is None or not args.normal_probe_receipts.resolve().is_relative_to(Path('/tmp')):
            p.error('--experimental-normal-probes requires --normal-probe-receipts under /tmp')
    elif args.normal_probe_receipts is not None:
        p.error('--normal-probe-receipts requires explicit --experimental-normal-probes')
    return args


def validate_input(body, contract):
    """Fail before BPy scene mutations if preparation broke the portable contract."""
    if body.get('license') != 'CC0-1.0' or body.get('units') not in ('m','metres') or body.get('up_axis') != '+Y' or body.get('forward_axis') != '+Z':
        raise ValueError('prepared input must explicitly retain CC0-1.0 and metre/Y-up/+Z-forward frame')
    expected = dict(contract['skeleton']['bones'])
    bones = {b['name']: b for b in body['skeleton']}
    if set(bones) != set(expected):
        raise ValueError('body skeleton must contain exactly the 56 contract joints')
    for name, parent in expected.items():
        b = bones[name]
        if b['parent'] != parent:
            raise ValueError(f'{name}: incompatible parent')
        if sum((a-z)**2 for a,z in zip(b['head_m'], b['tail_m'])) < 1e-10:
            raise ValueError(f'{name}: zero-length bone')
    for mesh in body['meshes']:
        n = len(mesh['positions_m'])
        if len(mesh['weights']) != n or len(mesh['uvs']) != n:
            raise ValueError('UV-seam-split vertices need one UV and weight map each')
        for weights in mesh['weights']:
            if not 1 <= len(weights) <= 4 or set(weights)-set(expected):
                raise ValueError('invalid portable skin influences')
            if any(not math.isfinite(w) or w < 0 for w in weights.values()) or abs(sum(weights.values())-1) > 1e-5:
                raise ValueError('skin influences must be finite, nonnegative and normalized')
        if any(len(f)!=3 or min(f)<0 or max(f)>=n for f in mesh['triangles']):
            raise ValueError('triangles must index existing vertices')
    return bones


def resolve_person_reference(variant, root=ROOT):
    """Resolve existing person and scene; never mint a name or upgrade its grade."""
    scene=str(variant['person_reference_scene'])
    if scene!='1835':raise ValueError('this wardrobe recipe is bounded to the 1835 scene')
    pid=variant['person_reference_id']
    scene_path=root/'data/sidecars'/scene/'people.json'
    if not scene_path.exists():
        raise ValueError('compile the 1835 scene first; its people layer is required for identity validation')
    people={p['id']:p for p in json.loads(scene_path.read_text())['people']}
    if pid not in people:raise ValueError(f'{pid}: absent from the existing 1835 people layer')
    record=root/variant['person_reference_record']
    dress_reference=(variant.get('component_assembly')=='adult_dress_v1' and pid=='rc_flynn_mary'
                     and record==root/'data/residents/households/hh_rc_flynn_mary.json')
    if not (record.is_relative_to(root/'data/residents/reconstructed_trades') or dress_reference):
        raise ValueError('person reference must resolve under reconstructed_trades or the explicit existing Mary Flynn dress study')
    household=json.loads(record.read_text())
    person=next((p for p in household['persons'] if p['id']==pid),None)
    if person is None:raise ValueError(f'{pid}: missing in referenced household')
    grade=variant['person_reference_grade']
    if grade!='reconstructed' or people[pid].get('grade')!=grade or person.get('grade')!=grade:
        raise ValueError('person reference grade differs; never silently upgrade reconstructed identities')
    snapshot={'name':person['name'],'age_band':person['age_band']['value'],'occupation':person['occupation']['value'],'division':household['division'],'presence':household['present_on_scene_date']['value']}
    if snapshot!=variant['reference_summary']:
        raise ValueError('resident reference changed; review recipe rather than retaining stale identity facts')
    if snapshot['presence']!='present':raise ValueError('resident is not present in this scene record')
    return {**snapshot, 'review_required':bool(person.get('review_required') or person.get('reconstruction',{}).get('review_required') or household.get('review_required') or people[pid].get('review_required')), 'touches_removal':bool(person.get('touches_removal') or household.get('touches_removal') or people[pid].get('touches_removal'))}


def verify_skin_texture(recipe, root=ROOT):
    record=recipe['skin_texture']
    if record['license']!='CC0-1.0' or record['color_space']!='sRGB':
        raise ValueError('skin input license/color space differs from reviewed recipe')
    path=root/record['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
        raise ValueError('skin texture checksum mismatch; do not substitute another file')
    return path


def build(args):
    # Deliberately import BPy only at execution, so syntax/import of validation helpers
    # can be checked by normal Python without installing Blender.
    import bpy
    from mathutils import Matrix, Vector, Quaternion
    recipe = json.loads(args.recipe.read_text())
    contract = json.loads((ROOT/'data/humans/contract.json').read_text())
    liberty = args.liberty or recipe.get('liberty')
    if not liberty or not liberty.startswith('L'):
        raise ValueError('a real --liberty or recipe.liberty is required, never fabricate one')
    variants = {v['id']:v for v in recipe.get('proof_variants',[])}
    if args.variant and args.variant not in variants:
        raise ValueError(f'unknown proof variant {args.variant!r}')
    variant = variants[args.variant]
    if 'waistcoat_shoulder_pattern' in variant:
        if args.variant!='bardwell_otis_1835':raise ValueError('connected waistcoat study is Bardwell-only')
        recipe={**recipe,'waistcoat_shoulder_pattern':variant['waistcoat_shoulder_pattern']}
    wardrobe = None
    if 'modular_wardrobe' in recipe:
        recipe, wardrobe = resolve_wardrobe(recipe, variant)
    reference = resolve_person_reference(variant)
    bodypath = ROOT/variant['body_input']
    if args.body and args.body.resolve()!=bodypath.resolve():
        raise ValueError('--body conflicts with the selected resident variant; never silently replace its adult body')
    body = json.loads(bodypath.read_text())
    bones = validate_input(body, contract)
    if body.get('target_blend',{}).get('phenotype',{}).get('chosen_age_years')!=variant['body_parameters']['engineering_age_years']:
        raise ValueError('variant adult macro body does not match its reconstructed authoring-age parameter')
    dress = None
    if variant.get('component_assembly'):
        from human_dress_components import prepare_dress_assembly
        dress = prepare_dress_assembly(ROOT, recipe, variant, body)
        if args.sit_drive_study:
            raise ValueError('dress study has no qualified seated/driver assignment')
    skinpath = verify_skin_texture(recipe)
    from human_hair_short04 import fit as fit_short04
    hair, hairpath, hair_report = fit_short04(body, recipe['hair_component'], ROOT)
    colors = {**recipe['colors_linear_rgba'], **variant.get('color_overrides',{})}
    if wardrobe:
        colors.update(wardrobe['colors'])
    colors.pop('eyes',None)
    colors.update({name:spec['base_color'] for name,spec in EYE_MATERIALS.items() if name!='eyes__cornea'})
    asset = args.variant
    scale = float(recipe.get('height_scale',1))
    if scale <= 0:
        raise ValueError('height_scale must be positive')
    def xyz(p):
        # glTF +Y up/+Z forward -> Blender +Z up/-Y forward; positive determinant.
        return Vector((p[0]*scale,-p[2]*scale,p[1]*scale))
    H = {n:(xyz(b['head_m']),xyz(b['tail_m'])) for n,b in bones.items()}
    height = max(p[1] for m in body['meshes'] for p in m['positions_m'])*scale
    if abs(height-variant['body_parameters']['chosen_height_m'])>.005:
        raise ValueError('prepared height differs from the variant reconstructed height parameter')
    if not .45 <= height <= 2.3:
        raise ValueError(f'body height {height} m violates the contract')
    if wardrobe:
        wardrobe['body_height_m'] = height
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    rigcol = bpy.data.collections.new('rig')
    scene.collection.children.link(rigcol)
    arm = bpy.data.armatures.new(contract['skeleton']['id'])
    rig = bpy.data.objects.new('c4d_armature',arm)
    rigcol.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,parent in contract['skeleton']['bones']:
        b = arm.edit_bones.new(name)
        b.head,b.tail = H[name]
        b.roll = 0
    for name,parent in contract['skeleton']['bones']:
        if parent:
            arm.edit_bones[name].parent = arm.edit_bones[parent]
            arm.edit_bones[name].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    materials = {}
    for name,color in colors.items():
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = .75 if name.startswith('skin') else .88
        if wardrobe and name in recipe['modular_wardrobe']['material_roughness']:
            bsdf.inputs['Roughness'].default_value=recipe['modular_wardrobe']['material_roughness'][name]
        if dress and name in dress['materials']:
            bsdf.inputs['Roughness'].default_value=dress['materials'][name]['roughness']
        if name.startswith('eyes'):
            bsdf.inputs['Roughness'].default_value = .18
        if name in EYE_MATERIALS:bsdf.inputs['Roughness'].default_value=EYE_MATERIALS[name]['roughness']
        materials[name] = material
    # Original opaque sclera/iris/pupil; no transparent shell/new extension.
    # Dimensions and brown color are reconstruction, not resident facts.
    iris=bpy.data.images.new('original_reconstructed_iris',width=512,height=256,alpha=False)
    iris.colorspace_settings.name='sRGB';iris.pixels=iris_pixels();iris.file_format='PNG';iris.pack()
    iris_nodes=materials['eyes__iris'].node_tree.nodes
    iris_tex=iris_nodes.new('ShaderNodeTexImage');iris_tex.image=iris
    materials['eyes__iris'].node_tree.links.new(iris_tex.outputs['Color'],iris_nodes['Principled BSDF'].inputs['Base Color'])
    # Reviewed source atlas: preserve sRGB and do not tint with the old flat skin.
    skin_image=bpy.data.images.load(str(skinpath.resolve()),check_existing=True)
    skin_image.colorspace_settings.name='sRGB'
    skin_image.pack()
    skin_nodes=materials['skin'].node_tree.nodes
    skin_bsdf=skin_nodes['Principled BSDF']
    skin_bsdf.inputs['Base Color'].default_value=(1,1,1,1)
    skin_bsdf.inputs['Roughness'].default_value=recipe['skin_texture']['roughness']
    skin_tex=skin_nodes.new('ShaderNodeTexImage');skin_tex.name='Verified CC0 generic skin atlas';skin_tex.image=skin_image
    materials['skin'].node_tree.links.new(skin_tex.outputs['Color'],skin_bsdf.inputs['Base Color'])
    # Original deterministic 256px interlacing study, not a sampled textile or
    # evidence of a particular historical weave. UV density remains a review gate.
    # Packing is essential: exported masters must decode an actual texture.
    weave=bpy.data.images.new('original_reconstructed_woven_shirt',width=256,height=256,alpha=False)
    weave.colorspace_settings.name='sRGB'
    cloth_material='garment_upper__plain_dress' if dress else 'garment_upper__shirt_linen'
    base=colors[cloth_material];pixels=[]
    for yy in range(256):
        for xx in range(256):
            # The old eight-texel ridges read as giant blocks on body UVs.
            # This original one-texel alternation has only one percent contrast.
            shade=.99+.01*((xx+yy)%2)
            pixels.extend([base[0]*shade,base[1]*shade,base[2]*shade,1.])
    weave.pixels=pixels
    weave.file_format='PNG'
    weave.pack()
    nodes=materials[cloth_material].node_tree.nodes
    links=materials[cloth_material].node_tree.links
    tex=nodes.new('ShaderNodeTexImage');tex.name='Original reconstructed cloth weave';tex.image=weave
    tex.interpolation='Linear'
    links.new(tex.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
    # Cleared CC0 short04 source, fitted to this resident's selected body. The
    # padded derivative preserves source repeat samples at base-level bilinear only;
    # mip/aniso and actual glTF alpha-mode behavior must be reviewed after export.
    hair_config=recipe['hair_component']
    hair_mat=bpy.data.materials.new('hair__makehuman_short04');hair_mat.use_nodes=True
    hair_mat.use_backface_culling=False
    if hasattr(hair_mat,'surface_render_method'):hair_mat.surface_render_method='DITHERED'
    hair_nodes=hair_mat.node_tree.nodes;hair_links=hair_mat.node_tree.links
    hair_bsdf=hair_nodes['Principled BSDF']
    hair_bsdf.inputs['Base Color'].default_value=(1,1,1,1)
    hair_bsdf.inputs['Roughness'].default_value=hair_config['roughness']
    hair_image=bpy.data.images.load(str(hairpath.resolve()),check_existing=True)
    if tuple(hair_image.size)!=(2048,2057):raise ValueError('unexpected padded hair atlas dimensions')
    hair_image.colorspace_settings.name='sRGB';hair_image.pack()
    hair_tex=hair_nodes.new('ShaderNodeTexImage');hair_tex.image=hair_image
    hair_tex.extension='EXTEND';hair_tex.interpolation='Linear'
    hair_links.new(hair_tex.outputs['Color'],hair_bsdf.inputs['Base Color'])
    # Binary alpha threshold is explicit node geometry, not an opaque alpha label.
    # CI must inspect exported material alphaMode/cutoff and actual hair edges.
    clip=hair_nodes.new('ShaderNodeMath');clip.operation='LESS_THAN'
    clip.inputs[1].default_value=hair_config['alpha_cutoff']
    hair_links.new(hair_tex.outputs['Alpha'],clip.inputs[0])
    inverse=hair_nodes.new('ShaderNodeMath');inverse.operation='SUBTRACT'
    inverse.inputs[0].default_value=1
    hair_links.new(clip.outputs[0],inverse.inputs[1])
    hair_links.new(inverse.outputs[0],hair_bsdf.inputs['Alpha'])
    materials['hair__makehuman_short04']=hair_mat
    # Incoming source UVs are retained per loop, including source-seam duplicates.
    def object_mesh(name,points,faces,uvs,weights,material,col,ratio=1,source_vertex_indices=None,corner_uvs=None,flat_face_indices=()):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([xyz(v) for v in points],[],faces)
        mesh.update()
        layer = mesh.uv_layers.new(name='UVMap')
        flat_face_indices = set(flat_face_indices)
        for polygon in mesh.polygons:
            polygon.use_smooth = polygon.index not in flat_face_indices
            for li in polygon.loop_indices:
                layer.data[li].uv = corner_uvs[polygon.index][list(polygon.loop_indices).index(li)] if corner_uvs is not None else uvs[mesh.loops[li].vertex_index]
        if source_vertex_indices is not None:
            # Body UV duplicates share rest normals without welding positions/UVs.
            # Decimation, morph and export behavior still require canonical checks.
            from human_source_normals import source_shared_normals
            source_normals=source_shared_normals(points,faces,source_vertex_indices)
            converted=[tuple(xyz(n).normalized()) for n in source_normals]
            mesh.normals_split_custom_set([converted[loop.vertex_index] for loop in mesh.loops])
            if ratio == 1 and args.experimental_normal_probes:
                # UNEXECUTED prototype until an explicitly opted-in pinned CI run.
                # Existing RAW1e-3 readback audit below remains unchanged.
                from human_normal_probe import experiment
                receipt_path=args.normal_probe_receipts/(asset+'-'+hashlib.sha256(name.encode()).hexdigest()+'-normal-probe.json')
                probe_receipt=experiment(mesh,converted,source_vertex_indices,receipt_path,
                    context={'blender_version':bpy.app.version_string,'asset_id':asset,'explicit_opt_in':True})
                print(json.dumps({'experimental_normal_probe':{'mesh':name,'receipt':str(receipt_path),
                    'maximum_raw_delta':probe_receipt['after']['maximum_raw_vector_delta'],
                    'scope':'experimental LOD0 body packed-normal readback only; not export/appearance acceptance'}}),flush=True)
            if ratio == 1:
                # Blender 4.5 encodes custom corner normals as short2. This 1e-3
                # vector bound is conservative engineering acceptance, not exact
                # float32 equivalence or a proven codec worst-case bound.
                mesh.update()
                actual=mesh.corner_normals
                if not mesh.has_custom_normals or len(actual)!=len(mesh.loops):
                    raise ValueError('LOD0 body custom normals missing or corner count changed')
                deltas=[]
                for index,loop in enumerate(mesh.loops):
                    value=tuple(actual[index].vector)
                    if not all(math.isfinite(x) for x in value):
                        raise ValueError('LOD0 body custom normal readback is nonfinite')
                    deltas.append(math.dist(value,converted[loop.vertex_index]))
                source_groups={}
                for i,loop in enumerate(mesh.loops):
                    sid=source_vertex_indices[loop.vertex_index]
                    group=source_groups.setdefault(sid,{'vertices':set(),'normals':set()})
                    group['vertices'].add(loop.vertex_index)
                    group['normals'].add(tuple(actual[i].vector))
                seam_deltas=[]
                for sid,group in source_groups.items():
                    if len(group['vertices'])<2:continue
                    vectors=list(group['normals'])
                    spread=max((math.dist(a,b) for j,a in enumerate(vectors) for b in vectors[j+1:]),default=0.0)
                    seam_deltas.append({'source_vertex_id':sid,'duplicate_vertices':len(group['vertices']),
                        'actual_normal_variants':len(vectors),'maximum_pair_vector_delta':spread})
                seam_deltas.sort(key=lambda x:(-x['maximum_pair_vector_delta'],x['source_vertex_id']))
                top=sorted(range(len(deltas)),key=lambda i:deltas[i],reverse=True)[:5]
                audit={'asset_id':asset,'mesh':name,'corners':len(deltas),
                    'max_vector_delta':max(deltas) if deltas else None,
                    'mean_vector_delta':math.fsum(deltas)/len(deltas) if deltas else None,
                    'bad_corner_count':sum(delta>1e-3 for delta in deltas),
                    'tolerance':1e-3,'status':'passed' if deltas and max(deltas)<=1e-3 else 'failed',
                    'source_uv_seam_disagreement':{'scope':'actual corner normal pair spread across distinct UV-split vertices sharing source ID; diagnostic only',
                        'duplicate_source_groups':len(seam_deltas),
                        'max_pair_vector_delta':max((x['maximum_pair_vector_delta'] for x in seam_deltas),default=0.0),
                        'groups_over_1e_3':sum(x['maximum_pair_vector_delta']>1e-3 for x in seam_deltas),
                        'top_groups':seam_deltas[:5]},
                    'top_corners':[{'loop_index':i,'vertex_index':mesh.loops[i].vertex_index,
                        'source_vertex_id':source_vertex_indices[mesh.loops[i].vertex_index],
                        'vector_delta':deltas[i],
                        'expected_normal':converted[mesh.loops[i].vertex_index],
                        'actual_normal':tuple(actual[i].vector)} for i in top],
                    'scope':'local LOD0 BPy readback before modifiers/export; bounded diagnostics only, not emitted GLB/morph/decimated normal acceptance'}
                print(json.dumps({'body_normal_preexport_audit':audit}),flush=True)
                if not deltas or max(deltas)>1e-3:
                    raise ValueError('LOD0 body custom normal readback exceeds 1e-3 vector tolerance')
        obj = bpy.data.objects.new(name,mesh)
        col.objects.link(obj)
        mesh.materials.append(materials[material])
        for joint,_ in contract['skeleton']['bones']:
            obj.vertex_groups.new(name=joint)
        for i,mapping in enumerate(weights):
            for joint,w in mapping.items():
                obj.vertex_groups[joint].add([i],w,'REPLACE')
        if ratio < 1 and len(faces)>12:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            decimate = obj.modifiers.new('authored_lod_reduction','DECIMATE')
            decimate.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=decimate.name)
        # Authored identity mesh is a root; skin modifier references the rig.
        mod = obj.modifiers.new('skin','ARMATURE')
        mod.object = rig
        return obj
    shoulder_y = bones['upperarm_l']['head_m'][1]
    wrist_x = abs(bones['hand_l']['head_m'][0])
    neck_y = bones['neck_01']['head_m'][1]
    def shell(m,kind,offset):
        return garment_shell(m,kind,offset,recipe,bones,height,scale)
    def morphs(obj):
        # Actual geometric targets on the source-derived head, not empty name tokens.
        obj.shape_key_add(name='Basis')
        for side,label in (('l','Left'),('r','Right')):
            key=obj.shape_key_add(name='eyeBlink'+label)
            center=H['eye_'+side][0]
            touched=0
            for i,v in enumerate(obj.data.vertices):
                if abs(v.co.x-center.x)<.035*scale and abs(v.co.z-center.z)<.023*scale and abs(v.co.y-center.y)<.045*scale:
                    key.data[i].co.z=center.z+(v.co.z-center.z)*.08
                    touched+=1
            amplitude=max((key.data[i].co-v.co).length for i,v in enumerate(obj.data.vertices))
            if not touched or amplitude<=.001:raise ValueError('blink target must move actual eyelid vertices >1 mm; inspect prepared eye joints/LOD')
        key=obj.shape_key_add(name='jawOpen')
        pivot=H['jaw'][0];rotation=Matrix.Rotation(math.radians(12),3,'X');touched=0
        for i,v in enumerate(obj.data.vertices):
            if v.co.z<pivot.z+.015*scale and v.co.z>pivot.z-.10*scale and abs(v.co.x)<.085*scale and v.co.y<pivot.y+.045*scale:
                key.data[i].co=pivot+rotation@(v.co-pivot);touched+=1
        amplitude=max((key.data[i].co-v.co).length for i,v in enumerate(obj.data.vertices))
        if not touched or amplitude<=.001:raise ValueError('jawOpen target must move actual jaw vertices >1 mm; inspect prepared jaw joint/LOD')
    for lod,ratio in enumerate(recipe['lod_ratios']):
        col=bpy.data.collections.new('lod'+str(lod));scene.collection.children.link(col)
        # Preserve source hair topology pending measured lower-LOD adaptation.
        object_mesh(f'{asset}_short04_hair_lod{lod}',hair['positions_m'],hair['triangles'],hair['uvs'],hair['weights'],'hair__makehuman_short04',col)
        for mi,m in enumerate(body['meshes']):
            obj=object_mesh(f'{asset}_body_{mi}_lod{lod}',m['positions_m'],m['triangles'],m['uvs'],m['weights'],'skin',col,ratio,source_vertex_indices=m['source_vertex_indices'])
            if lod in contract['morphs']['required_lods']:morphs(obj)
            if not dress:
                for kind,mat,offset in [('shirt','garment_upper__shirt_linen',recipe['shirt_offset_m']),('waistcoat','garment_outer__waistcoat_wool',recipe['waistcoat_offset_m']),('trousers','garment_lower__highwaist_pantaloons',recipe['trouser_offset_m'])]:
                    garment=shell(m,kind,offset)
                    if kind=='shirt':garment=standing_collar_extension(garment,m,bones,recipe,scale)
                    if wardrobe:
                        if kind == 'waistcoat':
                            detail = waistcoat_buttons(garment,bones,recipe,wardrobe,lod,scale)
                            object_mesh(f'{asset}_buttons_{mi}_lod{lod}',detail['positions_m'],detail['triangles'],detail['uvs'],detail['weights'],detail['material'],col,corner_uvs=detail['corner_uvs'])
                        garment=finish_edges(garment,recipe['modular_wardrobe']['edge_thickness_m'],scale)
                    object_mesh(f'{asset}_{kind}_{mi}_lod{lod}',garment['positions_m'],garment['triangles'],garment['uvs'],garment['weights'],mat,col,ratio,corner_uvs=garment['corner_uvs'],flat_face_indices=garment.get('flat_face_indices',()))
                    if lod==0:print(json.dumps({'source_workwear_coverage':garment['receipt']}),flush=True)
                if wardrobe:
                    jacket=round_jacket(m,bones,recipe,height,wardrobe,scale)
                    if jacket:
                        jacket=finish_edges(jacket,recipe['modular_wardrobe']['edge_thickness_m'],scale)
                        object_mesh(f'{asset}_jacket_{mi}_lod{lod}',jacket['positions_m'],jacket['triangles'],jacket['uvs'],jacket['weights'],jacket['material'],col,ratio,corner_uvs=jacket['corner_uvs'],flat_face_indices=jacket.get('flat_face_indices',()))
                        if lod==0:print(json.dumps({'source_jacket_construction':jacket['receipt']}),flush=True)
        if wardrobe:
            hat=work_hat(hair,bones,wardrobe,lod,scale)
            if hat:
                object_mesh(f'{asset}_hat_lod{lod}',hat['positions_m'],hat['triangles'],hat['uvs'],hat['weights'],hat['material'],col,corner_uvs=hat['corner_uvs'])
                if lod==0:print(json.dumps({'source_hat_construction':hat['receipt']}),flush=True)
        if dress:
            for component in dress['meshes']:
                if component['name']=='closed_low_shoes':
                    continue # Native per-LOD source-foot shoe below preserves sole support.
                object_mesh(f"{asset}_{component['name']}_lod{lod}",component['positions_m'],component['triangles'],component['uvs'],component['weights'],component['material'],col,ratio,corner_uvs=component['corner_uvs'],flat_face_indices=component.get('flat_face_indices',()))
                if lod==0:print(json.dumps({'source_dress_component':component.get('receipt',{})}),flush=True)
        # Actual source foot sections bound this reconstructed closed shoe.
        # No body skin is hidden. All sole points survive at every LOD; the
        # existing loaded stance/foot/sole contact gates remain unchanged.
        shoes=fitted_shoes(body,bones,lod,scale,recipe['workwear_coverage']['shoe_clearance_m'])
        shoe_material='footwear__plain_low_shoes' if dress else 'footwear__closed_leather_shoes'
        object_mesh(f'{asset}_closed_shoes_lod{lod}',shoes['positions_m'],shoes['triangles'],shoes['uvs'],shoes['weights'],shoe_material,col)
        if lod==0:print(json.dumps({'source_shoe_enclosure':shoes['receipt']}),flush=True)
        # Standing collar is welded into the linen shirt before LOD reduction.
        eye_data=build_eye_components(bones,lod,recipe['eye_components'])
        for component in eye_data['meshes']:
            object_mesh(f"{asset}_{component['name']}_lod{lod}",component['positions_m'],component['triangles'],component['uvs'],component['weights'],component['material'],col)
    for name,bone in contract['sockets']['required']:
        obj=bpy.data.objects.new(name,None);rigcol.objects.link(obj)
        obj.empty_display_size=.035;obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone
        a,b=H[bone];origin=b if bone=='head' else (a+b)/2
        bpy.context.view_layer.update()
        obj.matrix_world=Matrix.Translation(origin)@Matrix.Rotation(math.radians(-90 if bone=='head' else 90),4,'X')
    rig.animation_data_create()
    gait_legs = prepare_legs(bones, scale)
    # Contract-only, in-place clips; this is a mechanical contact study, not mocap.
    for clip,length in [('idle',60),('walk',CYCLE_FRAMES)]:
        act=bpy.data.actions.new(clip);act.use_fake_user=True;rig.animation_data.action=act
        if clip=='walk':
            act['speed_m_s']=SPEED_M_S
            act['cycle_duration_s']=CYCLE_DURATION_S
            act['stance_fraction']=STANCE_FRACTION
            act['contact_basis']='original source-frame flat-foot IK; actual exported skin contact still unverified'
        act['motion_basis']='original reconstructed mechanical pose; no biological or photographic gait acceptance'
        # Walk: 37 inclusive keys at30fps over1.2s. Idle retains its original13 keys.
        frames=range(1,length+2) if clip=='walk' else range(1,length+2,5)
        for frame in frames:
            fraction=(frame-1)/length
            phase=2*math.pi*fraction
            gait=pose_at_phase(gait_legs,fraction) if clip=='walk' else None
            for pose in rig.pose.bones:
                name=pose.name
                # A cross-fade into idle must clear the walking pelvis translation.
                pose.location=(0,0,0)
                world_rotation=Quaternion((1,0,0),0)
                if name.startswith('upperarm'):
                    # Preserve original upper-body lowering and rest-basis handling.
                    world_rotation=Quaternion((0,1,0),math.radians(78 if name.endswith('_l') else -78))
                if gait and name in gait['x_rotations_rad']:
                    world_rotation=Quaternion((1,0,0),gait['x_rotations_rad'][name])
                if name=='spine_02':world_rotation=Quaternion((1,0,0),math.radians(.6)*math.sin(phase))
                basis=rig.data.bones[name].matrix_local.to_quaternion()
                pose.rotation_mode='QUATERNION'
                pose.rotation_quaternion=basis.inverted()@world_rotation@basis
                if gait and name=='pelvis':
                    # Helper is already in scaled metres. Do NOT apply xyz()'s scale again.
                    dx,dy,dz=gait['pelvis_delta_m']
                    world_delta=Vector((dx,-dz,dy))
                    pose.location=basis.inverted()@world_delta
                pose.keyframe_insert('rotation_quaternion',frame=frame)
                pose.keyframe_insert('location',frame=frame)
        linearize_action(act)
        act['loop']=True
    if args.sit_drive_study:
        from human_seated_study import load_study, desired_matrix, local_basis
        if not args.sit_drive_vehicle:raise ValueError('--sit-drive-study requires --sit-drive-vehicle exported sidecar')
        study_pose,study_metadata=load_study(args.sit_drive_study,variant,bodypath,scale,args.sit_drive_vehicle)
        if set(study_pose)!=set(bones):raise ValueError('seated study joint set differs from canonical rig')
        # Read actual Blender rest bases; do not reconstruct roll or treat global
        # deformations as parent-local quaternions.
        rests={n:[list(row) for row in rig.data.bones[n].matrix_local] for n in bones}
        desired={n:desired_matrix(study_pose[n],rests[n]) for n in bones}
        act=bpy.data.actions.new('sit_drive');act.use_fake_user=True
        rig.animation_data.action=act
        act['loop']=True
        act['cycle_duration_s']=1.0
        act['in_place']=True
        act['motion_basis']='Original reconstructed static seated IK study; no driving forces or biological motion claim'
        act['driver_study_json']=json.dumps(study_metadata,sort_keys=True)
        for frame in (0,30):
            for name,parent in contract['skeleton']['bones']:
                pose=rig.pose.bones[name]
                matrix=local_basis(rests[name],desired[name],rests[parent] if parent else None,desired[parent] if parent else None)
                pose.rotation_mode='QUATERNION'
                pose.matrix_basis=Matrix(matrix)
                pose.scale=(1,1,1)
                pose.keyframe_insert('rotation_quaternion',frame=frame)
                pose.keyframe_insert('location',frame=frame)
                # Rigid contract: no scale animation channels or stretched bones.
        linearize_action(act)
        scene['driver_study_json']=json.dumps(study_metadata,sort_keys=True)
    rig.animation_data.action=None
    for pose in rig.pose.bones:
        pose.location=(0,0,0)
        pose.rotation_mode='QUATERNION';pose.rotation_quaternion=(1,0,0,0)
    scene['chicago4d_human']={'contract_version':contract['version'],'rigid_bone_frame_export':True,'kind':'body','asset_id':asset,'lod':0,'skeleton':contract['skeleton']['id'],'grade':'reconstructed','basis':recipe['basis']+' '+recipe['source_scope']+' Existing resident reference '+variant['person_reference_id']+' has reconstructed identity/presence/age/occupation. '+variant.get('body_basis','Age-bounded CC0 male macro body and cleared generic skin atlas are provisional authoring choices; height/complexion are not record facts, and no photographic likeness or individually validated anatomy is claimed.'),'sources':recipe['sources'],'liberty':liberty,'license':recipe['license'],'master':str(args.output),'authored_by':'Chicago4D original workwear authoring (T-1789)','recipe':variant.get('recipe_path','data/humans/recipes/worker_1835.json'),'person_reference_id':variant['person_reference_id'],'person_reference_scene':variant['person_reference_scene'],'person_reference_grade':variant['person_reference_grade'],'review_required':reference['review_required'],'touches_removal':reference['touches_removal'],'person_reference_summary_json':json.dumps(reference,sort_keys=True),'body_input':variant['body_input'],'body_target_blend_json':json.dumps(body.get('target_blend',{}),sort_keys=True),'body_parameters_json':json.dumps(variant['body_parameters'],sort_keys=True),'skin_source_json':json.dumps(recipe['skin_texture'],sort_keys=True),'body_source_json':json.dumps(body.get('source',body.get('provenance',{})),sort_keys=True)}
    scene['chicago4d_human']['hair_source_json']=json.dumps(hair_report,sort_keys=True)
    if wardrobe:
        scene['chicago4d_human']['wardrobe_assembly_json']=json.dumps({
            'assembly':variant['wardrobe_assembly'],'profile':wardrobe,
            'liberty':recipe['modular_wardrobe']['liberty'],
            'master_umbrella_liberty':liberty,
            'body_and_identity_unchanged':True,'grade':'reconstructed',
            'canonical_fit_and_photo_accepted':False},sort_keys=True)
    if dress:
        scene['chicago4d_human']['wardrobe_assembly_json']=json.dumps({'assembly':'adult_dress_v1','liberty':recipe['dress_components']['liberty'],'production_eligible':False,'qualified_roles':[],'standing_source_only':True,'walking_seated_and_photo_accepted':False,'body_and_identity_unchanged':True},sort_keys=True)
    scene['authoring_status']='UNVERIFIED: fitting, anatomy, facial targets, UV density, grounded animation and all export/render gates remain open until Blender/CI runs'
    scene.frame_set(1)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()),compress=True)
    print(f'wrote canonical master {args.output}; export using tools/human_export.py')


if __name__=='__main__':
    build(parse_args())
