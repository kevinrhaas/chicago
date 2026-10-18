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


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--body', type=Path)
    p.add_argument('--recipe', type=Path, default=ROOT/'data/humans/recipes/worker_1835.json')
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--liberty', help='Existing project LIBERTIES entry assigned by the integrator')
    p.add_argument('--variant', required=True, help='Required existing-resident recipe variant ID; no generic default')
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    return p.parse_args(argv)


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
    if not record.is_relative_to(root/'data/residents/reconstructed_trades'):
        raise ValueError('person reference must resolve under reconstructed_trades')
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
    reference = resolve_person_reference(variant)
    bodypath = ROOT/variant['body_input']
    if args.body and args.body.resolve()!=bodypath.resolve():
        raise ValueError('--body conflicts with the selected resident variant; never silently replace its adult body')
    body = json.loads(bodypath.read_text())
    bones = validate_input(body, contract)
    if body.get('target_blend',{}).get('phenotype',{}).get('chosen_age_years')!=variant['body_parameters']['engineering_age_years']:
        raise ValueError('variant adult macro body does not match its reconstructed authoring-age parameter')
    skinpath = verify_skin_texture(recipe)
    colors = {**recipe['colors_linear_rgba'], **variant.get('color_overrides',{})}
    colors['garment_upper__shirt_collar'] = colors['garment_upper__shirt_linen']
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
        if name.startswith('eyes'):
            bsdf.inputs['Roughness'].default_value = .18
        materials[name] = material
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
    base=colors['garment_upper__shirt_linen'];pixels=[]
    for yy in range(256):
        for xx in range(256):
            warp=(xx%8)/7;weft=(yy%8)/7
            over=((xx//8)+(yy//8))%2==0
            ridge=math.sin(math.pi*(warp if over else weft))
            # Bounded microvariation, no baked directional highlight or dirt.
            shade=.88+.12*ridge
            pixels.extend([base[0]*shade,base[1]*shade,base[2]*shade,1.])
    weave.pixels=pixels
    weave.file_format='PNG'
    weave.pack()
    nodes=materials['garment_upper__shirt_linen'].node_tree.nodes
    links=materials['garment_upper__shirt_linen'].node_tree.links
    tex=nodes.new('ShaderNodeTexImage');tex.name='Original reconstructed cloth weave';tex.image=weave
    tex.interpolation='Linear'
    links.new(tex.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
    # Incoming source UVs are retained per loop, including source-seam duplicates.
    def object_mesh(name,points,faces,uvs,weights,material,col,ratio=1):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([xyz(v) for v in points],[],faces)
        mesh.update()
        layer = mesh.uv_layers.new(name='UVMap')
        for polygon in mesh.polygons:
            polygon.use_smooth = True
            for li in polygon.loop_indices:
                layer.data[li].uv = uvs[mesh.loops[li].vertex_index]
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
        obj.parent = rig
        mod = obj.modifiers.new('skin','ARMATURE')
        mod.object = rig
        return obj
    waist = recipe['waist_height_fraction']*height/scale
    hem = recipe['shirt_hem_fraction']*height/scale
    shoulder_y = bones['upperarm_l']['head_m'][1]
    wrist_x = abs(bones['hand_l']['head_m'][0])
    neck_y = bones['neck_01']['head_m'][1]
    def region(m, face, kind):
        p=[sum(m['positions_m'][i][axis] for i in face)/3 for axis in range(3)]
        w={}
        for i in face:
            for b,v in m['weights'][i].items():w[b]=w.get(b,0)+v/3
        armweight=sum(v for b,v in w.items() if b.startswith(('clavicle','upperarm','lowerarm')))
        legweight=sum(v for b,v in w.items() if b.startswith(('thigh','calf','pelvis')))
        footweight=sum(v for b,v in w.items() if b.startswith(('foot','ball')))
        if kind=='shirt':return (hem<=p[1]<=neck_y+.035 and abs(p[0])<.23) or (armweight>.35 and abs(p[0])<wrist_x-.012)
        if kind=='waistcoat':
            torso=waist-.04<=p[1]<=shoulder_y+.025 and armweight<.35 and abs(p[0])<.235
            # Original open V: progressively wider toward the collar. Not a traced cut.
            opening=max(.012,.105*(p[1]-waist)/max(.01,shoulder_y-waist))
            return torso and not(p[2]>0 and abs(p[0])<opening)
        if kind=='trousers':return p[1]<=waist and legweight>.25 and footweight<.35
        if kind=='shoes':return footweight>.30 and p[1]<.17
        return False
    def shell(m,kind,offset):
        faces=[f for f in m['triangles'] if region(m,f,kind)]
        indices=sorted({i for f in faces for i in f})
        remap={v:i for i,v in enumerate(indices)}
        normals={i:Vector((0,0,0)) for i in indices}
        for a,b,c in faces:
            v=[Vector(m['positions_m'][i]) for i in (a,b,c)]
            n=(v[1]-v[0]).cross(v[2]-v[0])
            for i in (a,b,c):normals[i]+=n
        points=[]
        for i in indices:
            v=Vector(m['positions_m'][i]);n=normals[i].normalized() if normals[i].length else Vector((0,0,0))
            v+=n*(offset/scale)
            # Add original garment ease rather than just recoloring skin.
            if kind in ('shirt','waistcoat','trousers'):
                v.x += math.copysign(.007/scale,v.x) if abs(v.x)>.02 else 0
            if kind=='shoes':v.y=max(0,v.y)
            points.append(list(v))
        return points,[[remap[i] for i in f] for f in faces],[m['uvs'][i] for i in indices],[m['weights'][i] for i in indices]
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
        for mi,m in enumerate(body['meshes']):
            obj=object_mesh(f'{asset}_body_{mi}_lod{lod}',m['positions_m'],m['triangles'],m['uvs'],m['weights'],'skin',col,ratio)
            if lod in contract['morphs']['required_lods']:morphs(obj)
            for kind,mat,offset in [('shirt','garment_upper__shirt_linen',recipe['shirt_offset_m']),('waistcoat','garment_outer__waistcoat_wool',recipe['waistcoat_offset_m']),('trousers','garment_lower__highwaist_pantaloons',recipe['trouser_offset_m'])]:
                points,faces,uvs,weights=shell(m,kind,offset)
                if not faces:raise ValueError(f'{kind}: no faces selected from body; input proportions need review')
                object_mesh(f'{asset}_{kind}_{mi}_lod{lod}',points,faces,uvs,weights,mat,col,ratio)
        # Originally authored closed shoes: copying a toe-separated nude foot
        # shell would leave five visible toes and would not model footwear.
        sp=[];sf=[];su=[];sw=[];N=20 if lod<2 else 8
        for side,cell in [('l',0),('r',1)]:
            candidate=[p for m in body['meshes'] for p,w in zip(m['positions_m'],m['weights']) if sum(v for b,v in w.items() if b in ('foot_'+side,'ball_'+side))>.35 and p[1]<.16]
            if not candidate:raise ValueError('missing source foot bounds for closed shoe')
            xmin,xmax=min(p[0] for p in candidate),max(p[0] for p in candidate)
            zmin,zmax=min(p[2] for p in candidate),max(p[2] for p in candidate)
            cx=(xmin+xmax)/2;cz=(zmin+zmax)/2
            rx=(xmax-xmin)/2+recipe['shoe_offset_m']/scale
            rz=(zmax-zmin)/2+recipe['shoe_offset_m']/scale
            base=len(sp)
            # Sole, leather upper and ankle opening: all dimensions reconstructed.
            rings=[(0,1,1,cz),(.016/scale,1,1,cz),(.050/scale,.97,.98,cz),(.090/scale,.83,.68,cz-rz*.22),(.13/scale,.70,.33,cz-rz*.43)]
            for j,(y,fx,fz,zc) in enumerate(rings):
                for k in range(N+1):
                    t=2*math.pi*k/N;z=zc+rz*fz*math.sin(t)
                    sp.append([cx+rx*fx*math.cos(t),y,z]);su.append([(cell+.05+.9*k/N)/2,.05+.9*j/4])
                    blend=max(0,min(1,(z-bones['ball_'+side]['head_m'][2]+.04)/.08))
                    sw.append({'foot_'+side:1-blend,'ball_'+side:blend})
            for j in range(4):
                for k in range(N):
                    a=base+j*(N+1)+k;b=a+1;c=b+N+1;dd=a+N+1
                    sf.extend([(a,c,b),(a,dd,c)])
            # A separate sole UV island occupies the unused bottom atlas margin.
            center=len(sp);sp.append([cx,0,cz]);su.append([cell*.5+.25,.025]);sw.append({'foot_'+side:1.})
            sole=len(sp)
            for k in range(N):
                t=2*math.pi*k/N
                sp.append(sp[base+k]);su.append([cell*.5+.25+.20*math.cos(t),.025+.020*math.sin(t)]);sw.append(sw[base+k])
            for k in range(N):sf.append((center,sole+k,sole+(k+1)%N))
        object_mesh(f'{asset}_closed_shoes_lod{lod}',sp,sf,su,sw,'footwear__closed_leather_shoes',col)
        # Original standing collar, separate material UV island set; a reconstructed
        # construction detail rather than a painted modern shirt neckline.
        cp=[];cf=[];cu=[];cw=[];N=16 if lod<2 else 8
        neck=Vector(bones['neck_01']['head_m']);ch=recipe['collar_height_m']/scale
        rings=[(.052,.048,0),(.050,.046,ch),(.047,.043,ch),(.049,.045,0),(.052,.048,0)]
        for j,(rx,rz,dy) in enumerate(rings):
            for k in range(N+1):
                t=2*math.pi*k/N
                cp.append([neck.x+rx*math.cos(t),neck.y+dy,neck.z+rz*math.sin(t)])
                cu.append([.05+.9*k/N,.05+.9*j/4]);cw.append({'neck_01':1.})
        for j in range(4):
            for k in range(N):
                a=j*(N+1)+k;b=a+1;c=b+N+1;d=a+N+1
                cf.extend([(a,b,c),(a,c,d)])
        object_mesh(f'{asset}_standing_collar_lod{lod}',cp,cf,cu,cw,'garment_upper__shirt_collar',col)
        # Independent originally-authored corneas; no extracted photographic eye map.
        pts=[];faces=[];uv=[];weights=[]
        for side,cell in [('l',0),('r',1)]:
            center=Vector(bones['eye_'+side]['head_m']);base=len(pts);N=12 if lod<2 else 6
            for j in range(7):
                theta=math.pi*j/6
                for k in range(N):
                    phi=2*math.pi*k/N
                    p=center+Vector((.010*math.sin(theta)*math.cos(phi),.010*math.cos(theta),.010*math.sin(theta)*math.sin(phi)))
                    pts.append(list(p));uv.append([(cell+.05+.9*k/N)/2,.05+.9*j/6]);weights.append({'eye_'+side:1.})
            for j in range(6):
                for k in range(N):
                    a=base+j*N+k;b=base+j*N+(k+1)%N;c=b+N;d=a+N;faces.extend([(a,c,b),(a,d,c)])
        object_mesh(f'{asset}_eyes_lod{lod}',pts,faces,uv,weights,'eyes',col)
    for name,bone in contract['sockets']['required']:
        obj=bpy.data.objects.new(name,None);rigcol.objects.link(obj)
        obj.empty_display_size=.035;obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone
        a,b=H[bone];origin=b if bone=='head' else (a+b)/2
        bpy.context.view_layer.update()
        obj.matrix_world=Matrix.Translation(origin)@Matrix.Rotation(math.radians(-90 if bone=='head' else 90),4,'X')
    rig.animation_data_create()
    # Contract-only, in-place clips. Every bone is keyed so cross-fades reset safely.
    for clip,length in [('idle',60),('walk',30)]:
        act=bpy.data.actions.new(clip);act.use_fake_user=True;rig.animation_data.action=act
        if clip=='walk':act['speed_m_s']=1.0
        act['motion_basis']='original synthetic pose fixture; foot contacts not validated'
        for frame in range(1,length+2,5):
            phase=2*math.pi*(frame-1)/length
            for pose in rig.pose.bones:
                name=pose.name
                world_rotation=Quaternion((1,0,0),0)
                if name.startswith('upperarm'):
                    # Conjugate a world-Y rotation into each rest-bone basis. This
                    # lowers horizontal arms even if imported bone roll changes.
                    world_rotation=Quaternion((0,1,0),math.radians(78 if name.endswith('_l') else -78))
                if clip=='walk' and name.startswith('thigh'):
                    world_rotation=Quaternion((1,0,0),math.radians(18)*math.sin(phase+(0 if name.endswith('_l') else math.pi)))
                if clip=='walk' and name.startswith('calf'):
                    world_rotation=Quaternion((1,0,0),-math.radians(25)*max(0,math.sin(phase+(0 if name.endswith('_l') else math.pi))))
                if name=='spine_02':world_rotation=Quaternion((1,0,0),math.radians(.6)*math.sin(phase))
                basis=rig.data.bones[name].matrix_local.to_quaternion()
                pose.rotation_mode='QUATERNION'
                pose.rotation_quaternion=basis.inverted()@world_rotation@basis
                pose.keyframe_insert('rotation_quaternion',frame=frame)
        act['loop']=True
    rig.animation_data.action=None
    for p in rig.pose.bones:
        p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0)
    scene['chicago4d_human']={'contract_version':contract['version'],'kind':'body','asset_id':asset,'lod':0,'skeleton':contract['skeleton']['id'],'grade':'reconstructed','basis':recipe['basis']+' '+recipe['source_scope']+' Existing resident reference '+variant['person_reference_id']+' has reconstructed identity/presence/age/occupation. Age-bounded CC0 male macro body and cleared generic skin atlas are provisional authoring choices; height/complexion are not record facts, and no photographic likeness or individually validated anatomy is claimed.','sources':recipe['sources'],'liberty':liberty,'license':recipe['license'],'master':str(args.output),'authored_by':'Chicago4D original workwear authoring (T-1789)','recipe':'data/humans/recipes/worker_1835.json','person_reference_id':variant['person_reference_id'],'person_reference_scene':variant['person_reference_scene'],'person_reference_grade':variant['person_reference_grade'],'review_required':reference['review_required'],'touches_removal':reference['touches_removal'],'person_reference_summary_json':json.dumps(reference,sort_keys=True),'body_input':variant['body_input'],'body_target_blend_json':json.dumps(body.get('target_blend',{}),sort_keys=True),'body_parameters_json':json.dumps(variant['body_parameters'],sort_keys=True),'skin_source_json':json.dumps(recipe['skin_texture'],sort_keys=True),'body_source_json':json.dumps(body.get('source',body.get('provenance',{})),sort_keys=True)}
    scene['authoring_status']='UNVERIFIED: fitting, anatomy, facial targets, UV density, grounded animation and all export/render gates remain open until Blender/CI runs'
    scene.frame_set(1)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()),compress=True)
    print(f'wrote canonical master {args.output}; export using tools/human_export.py')


if __name__=='__main__':
    build(parse_args())
