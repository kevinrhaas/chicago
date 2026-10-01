"""Engine-neutral reduced geometry for the explicitly selected Glessner v4.

Imported by structure_versions.py build-light; this file is not a CLI. The full
master remains the material/texture authority. Both levels consume the same v4
record and the same architectural component/opening functions. This profile
reduces surface sampling and carving only; it is never a different house/version.
"""
from __future__ import annotations

from array import array
from collections import Counter
import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
import random
import struct
import sys
from types import ModuleType

MAX_TRIANGLES=200_000
MATERIAL_NAMES=('granite','brick','limestone_trim','roof_plane','copper','glass','oak',
 'lawn','drive','mortar','iron','glass_dark','granite_1','granite_2','granite_3','granite_4',
 'brick_dark_red','brick_buff','brick_smoky','roof_plane_1','roof_plane_2','roof_plane_3',
 'linen_blind','painted_wood','rough_stone_trim','turf_blade_dark','turf_blade_middle','turf_blade_light')


def _geometry_modules(root):
    """Load pure construction methods, with Blender emission deliberately unavailable.

    common.mesh's only import-time Blender dependency is its unused to_object
    boundary. A failing sentinel permits the same numerical geometry classes to
    load in ordinary Python; any accidental Blender operation fails immediately.
    This neither emulates Blender nor substitutes geometry/material outputs.
    """
    class NoBlender(ModuleType):
        def __getattr__(self,name):
            if name.startswith('__'):raise AttributeError(name)
            raise RuntimeError('Reduced Glessner construction cannot call Blender: '+name)
    sys.path.insert(0,str(root/'generators'))
    previous=sys.modules.get('bpy')
    if previous is None:sys.modules['bpy']=NoBlender('bpy')
    try:
        d=importlib.import_module('archetypes.masonry_house_v4_detail')
        params=importlib.import_module('archetypes.masonry_house_params')
        materials=importlib.import_module('archetypes.masonry_house_v4_materials')
    finally:
        if previous is None:sys.modules.pop('bpy',None)
    return d,params,materials


def _construct(root):
    d,param_module,materials=_geometry_modules(root)
    from common.versions import glessner_detail_record
    record=json.loads(glessner_detail_record(root).read_text())
    phase=next((p for p in record['phases'] if p['id']=='as_built_1887'),None)
    if phase is None:raise ValueError('Glessner v4 lacks the requested as_built_1887 phase')
    params=param_module.from_phase(phase,record)
    if params.detail_profile!='glessner_v4':raise ValueError('Reduced geometry requires the actual v4 record')

    class ReducedBuilder(d.DetailBuilder):
        def __init__(self,name,params):
            super().__init__(name,params)
            self.smooth_rock_faces=False
            self.components=Counter()

        def block(self,polygon,point,normal,confidence,mat,rng,holes=None):
            if len(polygon)<3:return
            x0,y0,x1,y1=d.bounds(polygon)
            if min(x1-x0,y1-y0)<.002:return
            depth=rng.uniform(.001,.006) if mat==d.BRICK else rng.uniform(*self.params.detail['ashlar_relief_m'])
            if mat==d.BRICK:
                firing=rng.random()
                variant=d.BRICK if firing<.60 else (16 if firing<.80 else (17 if firing<.94 else 18))
            else:
                variant=mat if mat in (d.TRIM,d.ROUGH_TRIM) else 12+rng.randrange(4)
                rectangular=(len(polygon)==4 and len({round(q[0],6) for q in polygon})==2 and
                             len({round(q[1],6) for q in polygon})==2)
                # Preserve full's RNG consumption and therefore every following
                # course joint, width and material variation exactly.
                large=x1-x0>.48 and y1-y0>.16 and mat!=d.TRIM
                consumed=(52 if rectangular else len(polygon)+(len(polygon)<=6)) if large else len(polygon)+(len(polygon)<=6)
                for _ in range(consumed):rng.random()
                depth=min(.070,depth+.012)
            emitted=False
            for fragment in d.subtract(polygon,holes or []):
                self.raw([point(q,depth) for q in fragment],confidence,variant,normal)
                emitted=True
            if emitted:self.masonry_blocks+=1

        def tiles(self,pts,confidence):
            # Continuous roof plane plus physical course noses every second tile
            # row. Ridge, eaves, valleys, dormers and roof intersections stay exact.
            normal=d.norm(d.legacy._normal(pts))
            self.raw(pts,confidence,d.ROOF)
            uphill=d.norm((-normal[0]*normal[2],-normal[1]*normal[2],1-normal[2]*normal[2]))
            if abs(uphill[2])<1e-5:return
            u=d.norm(d.cross(uphill,normal));distance=d.dot(pts[0],normal)
            poly=[(d.dot(p,u),d.dot(p,uphill)) for p in pts]
            if d.area(poly)<0:poly.reverse()
            a,z0,c,z1=d.bounds(poly)
            def point(q,h):return tuple(u[k]*q[0]+uphill[k]*q[1]+normal[k]*(distance+h) for k in range(3))
            for row in range(math.floor(z0/.24384),math.ceil(z1/.24384)):
                y=row*.24384
                lip=d.rect_clip(poly,a,y+.001,c,y+.017)
                if lip:self.raw([point(q,.012 if q[1]<y+.009 else .001) for q in lip],confidence,19+row%3,normal)

    b=ReducedBuilder('glessner_house__as_built_1887',params)
    legacy=d.legacy
    for r in params.ranges:legacy._range(b,r);b.components['ranges']+=1
    for t in params.towers:d.tower(b,t,params);b.components['towers']+=1
    for w in params.bows:d.bow(b,w);b.components['bows']+=1
    for y in params.bays:d.bay(b,y,params);b.components['bays']+=1
    for dormer in params.dormers:d.dormer(b,dormer);b.components['dormers']+=1
    for t in params.turrets:d.louvred_turret(b,t);b.components['turrets']+=1
    for c in params.chimneys:d.chimney(b,c);b.components['chimneys']+=1
    for o in params.openings:
        courtyard=(o['face']=='south' and o['at']>1) or (o['face']=='west' and o['at']>1) or (o['face']=='east' and o['at']<params.width_m-1)
        if o['kind']=='fan':_fan(b,o,d)
        elif o['kind']=='band':
            if o.get('face')=='east' and o['u1']-o['u0']>3 and o['z0']>5:
                # The full wall's carved-sill recess includes both foliate ends.
                # Its reduced stone back must close that whole same aperture.
                d.slab(b,o,o['u0']-.435,o['u1']+.435,o['z0']-.025,o['z1']+.045,-.02,.095,o['conf'],d.TRIM)
            else:d.slab(b,o,o['u0'],o['u1'],o['z0'],o['z1'],0,.095,o['conf'],d.TRIM)
        else:d.opening(b,o,courtyard)
    b.decorate=False
    for n in params.bands:
        legacy._band(b,n)
        d.slab(b,n,n['u0'],n['u1'],n['z0']-.055,n['z0']+.025,.07,n['proj_m']+.025,n['conf'],d.TRIM)
    b.decorate=True
    for w in params.walls:legacy._gate_piece(b,w)
    b.decorate=False
    for g in params.ground:legacy._ground(b,g)
    _columns(b,params,d)
    _ridges(b,params,d)
    b.decorate=True
    d.supplemental(b,params)
    d.terrace(b,params)
    d.service_stair(b,params)
    d.underpass(b,params)
    # Retain datestone blocks and ledge. Tiny raised letter facets are omitted at
    # this display level; the full master and evidence record remain authoritative.
    for stone in params.detail.get('date_stones',[]):
        d.slab(b,stone,stone['u0'],stone['u1'],stone['z0'],stone['z1'],0,.06,params.detail['conf'],d.GRANITE)
    ledge=params.detail.get('pigeon_ledge')
    if ledge:d.slab(b,ledge,ledge['u0'],ledge['u1'],ledge['z0'],ledge['z1'],0,ledge['projection_m'],params.detail['conf'],d.GRANITE)
    from archetypes.masonry_house_v4_foundation import stair_tower_plinth
    from archetypes.masonry_house_v4_rainwater import add_courtyard_rainwater
    stair_tower_plinth(b,params)
    add_courtyard_rainwater(b,params)
    b.components.update({'axial_opening_records':len(params.openings),'ground':len(params.ground),
                         'service_stairs':int(bool(params.detail.get('north_court_service_stair'))),
                         'underpass':int(bool(params.detail.get('underpass'))),
                         'supplemental_dormer':int(bool(params.detail.get('west_dormer')))})
    return b,params,materials


def _fan(b,o,d):
    r=d.ornament.Relief(b,o,b.params.detail.get('conf',o['conf']))
    cx=(o['u0']+o['u1'])/2;cz=o['spring_z'];rad=o['r_in'];count=o.get('voussoirs') or 11
    for i in range(count):
        a=math.pi*i/count+.004;c=math.pi*(i+1)/count-.004;lo,hi=rad+.04,o['r_out']
        r.solid([(cx+lo*math.cos(a),cz+lo*math.sin(a)),(cx+hi*math.cos(a),cz+hi*math.sin(a)),
                 (cx+hi*math.cos(c),cz+hi*math.sin(c)),(cx+lo*math.cos(c),cz+lo*math.sin(c))],-.02,.065,12+i%4)
    r.solid([(cx+o['r_out']*math.cos(math.pi*i/40),cz+o['r_out']*math.sin(math.pi*i/40)) for i in range(41)],-.065,-.045)
    for rr,dd,t in ((.666,.020,.013),(.745,.030,.012),(.943,.045,.014)):
        r.tube([(cx+rad*rr*math.cos(math.pi*i/32),cz+rad*rr*math.sin(math.pi*i/32),dd) for i in range(33)],t,6)
    for i in range(7):
        th=math.pi*(i+.5)/7
        r.leaf(cx+rad*.32*math.cos(th),cz+rad*.32*math.sin(th),th,rad*.28,rad*.12,.01,.035,0,False,steps=5)


def _columns(b,params,d):
    ops=sorted([o for o in params.openings if o['kind']=='window' and o['face']=='east' and o['z0']>5],
               key=lambda o:(round(o['at'],3),round(o['z0'],2),o['u0']))
    for a,c in zip(ops,ops[1:]):
        gap=c['u0']-a['u1']
        if not .12<gap<.3 or abs(a['z0']-c['z0'])>.05 or abs(a['at']-c['at'])>.05:continue
        u=(c['u0']+a['u1'])/2;z0,z1=a['z0'],a['z1']
        r=d.ornament.Relief(b,a,params.detail.get('conf',max(a['conf'],c['conf'])))
        d.ornament._shaft(r,u,z0+.05,z1-.29,gap)
        r.box(u-gap*.78,u+gap*.78,z0,z0+.075,-.08,.16)
        r.box(u-gap*.88,u+gap*.88,z1-.29,z1-.012,-.075,.198)
        for j in range(3):
            r.leaf(u+(j-1)*gap*.5,z1-.27,math.pi/2,.20,gap*.6,.18,.05,0,False,steps=5)


def _ridges(b,params,d):
    # Same per-tile raised crest envelopes. Four angular intervals include the
    # exact crown and both shoulders while removing invisible sub-centimetre arcs.
    from archetypes.masonry_house_v4_west_roof import ridge_ranges
    for r,a0,a1 in (segment for source in params.ranges for segment in ridge_ranges(source)):
        for i in range(math.ceil((a1-a0)/.36)):
            lo=a0+i*.36+.006;hi=min(a1,lo+.348)
            def P(a,along,radius):
                across=r['ridge_at']+radius*math.cos(a);z=r['ridge_z']+.055+radius*math.sin(a)
                return (across,along,z) if r['axis']=='y' else (along,across,z)
            for j in range(4):
                a,c=math.pi*j/4,math.pi*(j+1)/4
                b.raw([P(a,lo,.14),P(c,lo,.14),P(c,hi,.14),P(a,hi,.14)],r['conf_roof'],19+i%3,(0,0,1))
            front=lo+min(.004,(hi-lo)*.02);back=min(hi,front+min(.035,(hi-lo)*.24))
            axial=(0,1,0) if r['axis']=='y' else (1,0,0)
            for j in range(4):
                a,c=math.pi*j/4,math.pi*(j+1)/4
                ra,rc=.14+.055*math.sin(a)**2,.14+.055*math.sin(c)**2
                # One double-sided raised collar profile retains its exact
                # crown/shoulders. The35 mm connecting rim is microdetail at this
                # level; omitting it avoids changing any ridge silhouette.
                b.raw([P(a,front,.138),P(a,front,ra),P(c,front,rc),P(c,front,.138)],1.0,19+i%3,tuple(-v for v in axial))


def _read_glb(path):
    data=path.read_bytes()
    if len(data)<28 or data[:4]!=b'glTF' or struct.unpack_from('<I',data,4)[0]!=2:
        raise ValueError('Expected a binary glTF2 full master')
    length,tag=struct.unpack_from('<II',data,12)
    if tag!=0x4E4F534A:raise ValueError('Master lacks JSON chunk')
    document=json.loads(data[20:20+length]);offset=20+length
    size,tag=struct.unpack_from('<II',data,offset)
    if tag!=0x004E4942:raise ValueError('Master lacks embedded binary chunk')
    return document,data[offset+8:offset+8+size],hashlib.sha256(data).hexdigest()


def _normal(points):
    # Newell's area-weighted polygon normal matches a planar Blender polygon
    # and remains defined for a polygon whose first three corners are collinear.
    n=[0.,0.,0.]
    for a,b in zip(points,points[1:]+points[:1]):
        n[0]+=(a[1]-b[1])*(a[2]+b[2]);n[1]+=(a[2]-b[2])*(a[0]+b[0]);n[2]+=(a[0]-b[0])*(a[1]+b[1])
    length=math.sqrt(sum(x*x for x in n))
    return tuple(x/length for x in n) if length>1e-14 else (0.,0.,1.)


def _triangles(points,normal):
    """Ear-clip the actual polygon; never fill a concave opening with a fan."""
    if len(points)==3:return [(0,1,2)]
    axis=max(range(3),key=lambda k:abs(normal[k]));axes=[i for i in range(3) if i!=axis]
    p=[(q[axes[0]],q[axes[1]]) for q in points]
    def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]));sign=1 if signed>=0 else -1
    order=list(range(len(p)));result=[]
    while len(order)>3:
        found=False
        for k,b in enumerate(order):
            a,c=order[k-1],order[(k+1)%len(order)]
            if sign*turn(p[a],p[b],p[c])<=1e-12:continue
            inside=False
            for q in order:
                if q in (a,b,c):continue
                if min(sign*turn(p[a],p[b],p[q]),sign*turn(p[b],p[c],p[q]),sign*turn(p[c],p[a],p[q]))>=-1e-10:
                    inside=True;break
            if not inside:
                result.append((a,b,c));order.pop(k);found=True;break
        if not found:
            # Collinear consecutive vertices carry no area and no aperture edge.
            removed=False
            for k,b in enumerate(order):
                if abs(turn(p[order[k-1]],p[b],p[order[(k+1)%len(order)]]))<1e-10:
                    order.pop(k);removed=True;break
            if not removed:raise ValueError('Reduced polygon cannot be triangulated without altering its outline')
        if len(order)<3:break
    if len(order)==3:result.append(tuple(order))
    return result


def _apertures(params):
    axial=len([o for o in params.openings if o['kind'] not in ('fan','band')])
    bowed=sum(w['lights_per_row']*len(w['light_rows']) for w in params.bows)
    tower=len(params.detail.get('tower_stair_windows',{}).get('openings',[]))
    dining=0
    for bay in params.bays:
        facets=sum(math.dist(a,c)>1.2 for a,c in zip(bay['pts'],bay['pts'][1:]))
        dining+=facets*int(bool(bay['light_row']))
        if params.detail.get('dining_garden_window_z'):
            dining+=sum(0<=i<facets for i in params.detail.get('dining_garden_window_facets',[0,2,4]))
    return {'axial':axial,'hall_bow':bowed,'stair_tower':tower,'dining_bay':dining,
            'dormers':len(params.dormers)+int(bool(params.detail.get('west_dormer'))),
            'terrace':params.detail.get('bow_terrace',{}).get('window_count',0)}


def build_light(master:Path,output:Path,*,root:Path,recipe_sha256:str)->dict:
    """Write a temporary, uncompressed same-v4 LOD with exact master fabrics.

    The caller verifies master freshness, optimizes/compresses this source, checks
    its receipt/triangle count and packages the final light alongside master/high.
    No renderer, primary source, manifest or durable fourth asset is written here.
    """
    root=Path(root).resolve();master=Path(master);output=Path(output)
    if output.resolve()==master.resolve():raise ValueError('Reduced output cannot replace its full master')
    if len(recipe_sha256)!=64 or any(c not in '0123456789abcdef' for c in recipe_sha256):
        raise ValueError('Light recipe must be a lowercase SHA256')
    full,master_bin,master_sha=_read_glb(master)
    materials=full.get('materials',[])
    names={m.get('name'):i for i,m in enumerate(materials)}
    if any(n not in names for n in MATERIAL_NAMES):raise ValueError('Full master does not contain the expected v4 material library')
    owner=next((n for n in full.get('nodes',[]) if n.get('extras',{}).get('detail_profile')=='glessner_v4'),None)
    if owner is None:raise ValueError('Source master is not the detailed Glessner v4')
    b,params,uv_module=_construct(root)
    counts=_apertures(params)
    if counts!=owner['extras'].get('aperture_counts'):
        raise ValueError('Reduced source aperture schedule differs from full master')
    payload=bytearray();views=[];accessors=[]
    def append(data,target=None):
        payload.extend(b'\x00'*((-len(payload))%4));offset=len(payload);payload.extend(data)
        view={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
        if target:view['target']=target
        views.append(view);return len(views)-1
    def accessor(values,width,kind='f',bounds=False):
        a=array(kind,values)
        if sys.byteorder!='little':a.byteswap()
        view=append(a.tobytes(),34963 if kind=='I' else 34962)
        item={'bufferView':view,'componentType':5125 if kind=='I' else 5126,
              'count':len(a)//width,'type':{1:'SCALAR',2:'VEC2',3:'VEC3'}[width]}
        if bounds:
            item['min']=[min(a[k::width]) for k in range(width)]
            item['max']=[max(a[k::width]) for k in range(width)]
        accessors.append(item);return len(accessors)-1
    images=[]
    for original in full.get('images',[]):
        if 'bufferView' not in original:raise ValueError('Full master image must be embedded')
        source=full['bufferViews'][original['bufferView']]
        if source.get('buffer',0)!=0:raise ValueError('Unexpected external master image buffer')
        start=source.get('byteOffset',0);image=copy.deepcopy(original)
        image['bufferView']=append(master_bin[start:start+source['byteLength']]);images.append(image)
    groups={};triangle_count=0
    for face,material in zip(b.faces,b.mat_index):
        points=[b.verts[i] for i in face];normal=_normal(points)
        triangles=_triangles(points,normal)
        if not triangles:continue
        group=groups.setdefault(material,{'p':[],'n':[],'uv':[],'c':[],'i':[]})
        start=len(group['p'])//3
        horizontal=(-normal[1],normal[0],0);length=math.hypot(horizontal[0],horizontal[1])
        if length<1e-6:horizontal=(1,0,0);uphill=(0,1,0)
        else:
            horizontal=tuple(v/length for v in horizontal)
            uphill=(normal[1]*horizontal[2]-normal[2]*horizontal[1],normal[2]*horizontal[0]-normal[0]*horizontal[2],normal[0]*horizontal[1]-normal[1]*horizontal[0])
            length=math.sqrt(sum(v*v for v in uphill)) or 1;uphill=tuple(v/length for v in uphill)
            if uphill[2]<0:uphill=tuple(-v for v in uphill);horizontal=tuple(-v for v in horizontal)
        tu,tv=uv_module.TILE_M.get(uv_module.SLOT_FABRIC.get(material),(1,1))
        for index,point in zip(face,points):
            group['p'].extend((point[0],point[2],-point[1]))
            group['n'].extend((normal[0],normal[2],-normal[1]))
            group['uv'].extend((sum(p*v for p,v in zip(point,horizontal))/tu,1-sum(p*v for p,v in zip(point,uphill))/tv))
            group['c'].append(b.conf[index])
        for triangle in triangles:group['i'].extend(start+i for i in triangle)
        triangle_count+=len(triangles)
    if triangle_count>MAX_TRIANGLES:raise ValueError(f'Reduced Glessner has {triangle_count:,} triangles; limit {MAX_TRIANGLES:,}')
    primitives=[]
    for material,g in sorted(groups.items()):
        attributes={'POSITION':accessor(g['p'],3,bounds=True),'NORMAL':accessor(g['n'],3),
                    'TEXCOORD_0':accessor(g['uv'],2),'_CONFIDENCE':accessor(g['c'],1,bounds=True)}
        primitives.append({'attributes':attributes,'indices':accessor(g['i'],1,'I'),
                           'material':names[MATERIAL_NAMES[material]],'mode':4})
    extras=copy.deepcopy(owner.get('extras',{}))
    extras.update({'lod':'light','grass_blades':0,'roof_tiles':0,'masonry_blocks':b.masonry_blocks,
                   'openings_recessed':sum(counts.values()),'aperture_counts':counts})
    bounds=[[min(p[k] for p in b.verts),max(p[k] for p in b.verts)] for k in range(3)]
    receipt={'master_sha256':master_sha,'recipe_sha256':recipe_sha256,'triangles':triangle_count,
             'openings_recessed':sum(counts.values()),'bounds_zup_m':bounds,
             'profile':'same_v4_reduced_surface_sampling'}
    doc={'asset':copy.deepcopy(full['asset']),'scene':0,'scenes':[{'nodes':[0]}],
         'nodes':[{'name':b.name+'.light','mesh':0,'extras':extras}],
         'meshes':[{'name':b.name+'.light','primitives':primitives}],
         'materials':copy.deepcopy(materials),'images':images,'textures':copy.deepcopy(full.get('textures',[])),
         'samplers':copy.deepcopy(full.get('samplers',[])),'accessors':accessors,'bufferViews':views,
         'buffers':[{'byteLength':len(payload)}],'extras':{'glessner_light':receipt}}
    for key in ('extensionsUsed','extensionsRequired'):
        if key in full:doc[key]=copy.deepcopy(full[key])
    encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    payload.extend(b'\x00'*((-len(payload))%4))
    glb=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(payload))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(payload),0x004e4942)+payload
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(glb)
    return {**receipt,'bytes':len(glb),'sha256':hashlib.sha256(glb).hexdigest(),
            'aperture_counts':counts,'components':dict(b.components),'material_images_copied':len(images)}
