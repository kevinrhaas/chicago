"""Engine-neutral reduced geometry for the explicitly selected Glessner v4.

Imported by structure_versions.py build-light; this file is not a CLI. The full
master remains the material/texture authority. Both levels consume the same v4
record and the same architectural component/opening functions. This profile
reduces surface sampling and carving only; it is never a different house/version.
"""
from __future__ import annotations

from array import array
import builtins
from collections import Counter
import copy
import functools
import hashlib
import importlib
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import zlib
from types import ModuleType

MAX_TRIANGLES=200_000
# T-2401: the light tier's own stone-scale occlusion atlas. Half the master's edge (T-2400,
# 2048, about 2.3 cm a texel), so mobile pays a quarter of its bytes for it.
OCCLUSION_SIZE=1024
# How far a light-tier stone's corner normals lean from its face (tan of about 24
# degrees along each axis): the full tier's bowed crown, carried by shading alone.
PILLOW_LEAN=.45
MATERIAL_NAMES=('granite','brick','limestone_trim','roof_plane','copper','glass','oak',
 'lawn','drive','mortar','iron','glass_dark','granite_1','granite_2','granite_3','granite_4',
 'brick_dark_red','brick_buff','brick_smoky','roof_plane_1','roof_plane_2','roof_plane_3',
 'linen_blind','painted_wood','rough_stone_trim','turf_blade_dark','turf_blade_middle','turf_blade_light',
 'rainwater_metal','glessner_vines','flat_brick')


def _left_to_right_sum(iterable,start=0):
    """sum() as Python 3.11 and earlier compute it: one plain addition per item, in order."""
    total=start
    for value in iterable:total=total+value
    return total


def _blender_arithmetic(build):
    """Run a light-tier build with the summation the full master is built with (T-2311).

    Python 3.12 made sum() over floats compensated (Neumaier), so the same record
    built through the same construction functions gave a different light tier on
    each interpreter: CI's bake (3.11, as is Blender 4.5.3's own 3.11, which builds
    the full master) wrote bd1a614c67b3; a 3.12 runner wrote 8a51eea20569, and that
    was committed, so every full bake redded k01_contract. About twenty sum() sites
    in masonry_house_v4_* and here feed the mesh. Pinning the old arithmetic for
    the duration of the build, rather than editing those generator lines, leaves the
    full master and its inputs hash untouched and makes this tier one set of bytes
    on every interpreter. builtins is swapped, not module globals, so a module
    the construction imports lazily is covered too; the original is always restored.
    """
    @functools.wraps(build)
    def pinned(*args,**kwargs):
        previous=builtins.sum
        builtins.sum=_left_to_right_sum
        try:return build(*args,**kwargs)
        finally:builtins.sum=previous
    return pinned


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


@_blender_arithmetic
def _construct(root, *, roof_details_reduced=True):
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
            self.pillow_normals={}
            self.reduced_roof_details=roof_details_reduced
            # T-2211's two-plane street sash costs more triangles than this tier has left.
            self.reduced_sash=True
            self.reduced_service_access=True
            self.components=Counter()

        def block(self,polygon,point,normal,confidence,mat,rng,holes=None,course=None):
            # A course's own crown (T-3046) deepens a bow this tier does not build.
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
            pillow=None
            if mat!=d.BRICK:
                # The owner's bowed rock faces (2026-10-12) at no triangle cost: the
                # stone's one face keeps its plane, and its corners carry normals
                # leaning out from the stone's centre, so light rounds over it.
                cx,cz=(x0+x1)/2,(y0+y1)/2
                origin=point((0,0),0);along=d.norm(d.sub(point((1,0),0),origin))
                up=d.norm(d.sub(point((0,1),0),origin))
                def pillow(q):
                    tu=max(-1.0,min(1.0,(q[0]-cx)/max(.01,(x1-x0)/2)))
                    tz=max(-1.0,min(1.0,(q[1]-cz)/max(.01,(y1-y0)/2)))
                    return d.norm(tuple(normal[k]+PILLOW_LEAN*(tu*along[k]+tz*up[k]) for k in range(3)))
            for fragment in d.subtract(polygon,holes or []):
                parts=getattr(point,'partition',lambda poly,conf,mat:[(poly,point)])(
                    [(*q,depth) for q in fragment],confidence,variant)
                for piece,mapper in parts:
                    piece_conf=max(confidence,getattr(mapper,'confidence',confidence))
                    pts=[mapper(q[:2],q[2]) for q in piece]
                    if pillow is None:
                        self.raw(pts,piece_conf,variant,normal)
                    else:
                        normals=[pillow(q) for q in piece]
                        if d.dot(d.legacy._normal(pts),normal)<0:
                            pts.reverse();normals.reverse()
                        for index,n in zip(self.raw(pts,piece_conf,variant),normals):
                            self.pillow_normals[index]=n
                    emitted=True
            if emitted:self.masonry_blocks+=1

        def tiles(self,pts,confidence):
            # Every course and joint is mapped at the full model's physical
            # module. T-2219's full service junction took Light to 200,465 tris.
            # With the restored court bars, sample relief every sixth course; the
            # metric texture still shows every course and joint. Silhouettes,
            # apertures and roof planes stay exact, under the unchanged 200k cap.
            normal,poly,point,coords=self.roof_frame(pts)
            self.roof_raw(pts,confidence,d.ROOF,normal,coords)
            spec=self.params.detail['roof_tiles']
            step=6*spec['exposure_in']*.0254
            relief=spec['lap_relief_m']
            a,z0,c,z1=d.bounds(poly)
            for row in range(math.floor(z0/step),math.ceil(z1/step)):
                y=row*step
                lip=d.rect_clip(poly,a,y,c,y+relief)
                if lip:self.roof_raw([point(q,relief*(1-(q[1]-y)/relief)) for q in lip],confidence,19+row%3,normal,coords,detail=True)

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
            if o.get('style')=='rock_faced_lintel':d.rock_lintel(b,o)
            elif o.get('face')=='east' and o['u1']-o['u0']>3 and o['z0']>5:
                # The full wall's carved-sill recess includes both foliate ends.
                # Its reduced stone back must close that whole same aperture.
                # T-2965: granite, as the full tier's carved string.
                d.slab(b,o,o['u0']-.435,o['u1']+.435,o['z0']-.025,o['z1']+.045,-.02,.095,o['conf'],d.GRANITE)
            else:d.slab(b,o,o['u0'],o['u1'],o['z0'],o['z1'],0,.095,o['conf'],d.TRIM)
        else:
            d.opening(b,o,courtyard)
            # The reduced sash path omits Full's axial garden bars. Preserve
            # their count, centres and diameter with four-sided cylinders.
            a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1']
            if courtyard and o['kind']=='window' and z1<1.8 and min(c-a,z1-z0)>=.45:
                count=max(3,round((c-a)/.115))
                for i in range(1,count):
                    x,y,_=legacy._plane_point(o,a+(c-a)*i/count,0,-.10)
                    d.cylinder(b,x,y,z0+.02,z1-.02,.011,o['conf'],d.IRON,4)
    b.decorate=False
    for n in params.bands:
        legacy._band(b,n)
        d.slab(b,n,n['u0'],n['u1'],n['z0']-.055,n['z0']+.025,.07,n['proj_m']+.025,n['conf'],d.TRIM)
    b.decorate=True
    for w in params.walls:
        # T-2201: the courtyard's boundary runs are 30 m of brick; per-course relief on
        # them would spend the reduced tier's triangle cap, so they stay flat here.
        b.decorate='ends' not in w
        d.gate_piece(b,w)
    b.decorate=True
    b.decorate=False
    from archetypes.masonry_house_v4_ground import build as build_ground
    build_ground(b,params)
    from archetypes.masonry_house_v4_frontage import add_frontage
    add_frontage(b,params,reduced=True)
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
    from archetypes.masonry_house_v4_entry import end_returns
    end_returns(b,params)
    add_courtyard_rainwater(b,params)
    b.components.update({'axial_opening_records':len(params.openings),'ground':len(params.ground),
                         'service_stairs':int(bool(params.detail.get('north_court_service_stair'))),
                         'underpass':int(bool(params.detail.get('underpass'))),
                         'supplemental_dormer':int(bool(params.detail.get('west_dormer')))})
    if params.detail.get("roof_edges"):
        from archetypes.masonry_house_v4_roof_edges import add_edges
        add_edges(b,params)
    from archetypes.masonry_house_v4_vines import add_vines
    vines=add_vines(b,params,reduced=True)
    b.components['vine_plants']=len(vines['plants'])
    b.components['vine_panels']=vines['added_faces']
    return b,params,materials


def _low_relief(d):
    """The full fan's carving, drawn at this tier's triangle budget.

    Owner, 2026-10-12, on the phone's Prairie door: "what about on top of the door".
    The reduced fan was a sunburst of seven leaves and three rolls. This keeps the
    full model's layout, band for band and motif for motif (ornament.fan), and
    spends a few triangles on each: rolls and stems as four-sided tubes on a few
    points of their path, beads as low pyramids, and every leaf as a raised
    lozenge with a ridge, its edges skirted so it still casts a shadow line.
    """
    class LowRelief(d.ornament.Relief):
        def tube(self,path,radius,sides=10):
            if len(path)<2:return
            keep=max(5,min(len(path),math.ceil(len(path)/6)))
            picks=sorted({round(i*(len(path)-1)/(keep-1)) for i in range(keep)})
            sub=[path[i] for i in picks]
            span=len(path)-1
            r=(lambda t:radius(picks[min(len(picks)-1,round(t*(len(picks)-1)))]/span)) if callable(radius) else radius
            super().tube(sub,r,4)

        def bead(self,x,z,d0,radius,squash=1):
            ring=[(x+radius*math.cos(a),z+radius*squash*math.sin(a),d0) for a in (math.pi*k/2+math.pi/4 for k in range(4))]
            top=(x,z,d0+radius)
            for p,q in zip(ring,ring[1:]+ring[:1]):self.face([p,q,top])

        def leaf(self,x,z,angle,length,width,depth,lift=.024,curl=.18,holes=True,phase=0,steps=16):
            tx,tz=math.cos(angle),math.sin(angle);nx,nz=-tz,tx
            bend=curl*length*.5
            def at(t,v,up):
                return (x+tx*length*t+nx*(bend*math.sin(math.pi*t)+width*.5*v),
                        z+tz*length*t+nz*(bend*math.sin(math.pi*t)+width*.5*v),depth+up)
            root,tip=at(0,0,0),at(1,0,lift*.2)
            left,right=at(.42,-1,lift*.25),at(.42,1,lift*.25)
            ridge=at(.45,0,lift)
            for p,q in ((root,left),(left,tip),(tip,right),(right,root)):
                self.face([p,q,ridge])
                self.face([p,q,(q[0],q[1],q[2]-.010),(p[0],p[1],p[2]-.010)],normal=None)
    return LowRelief


def _fan(b,o,d):
    orn=d.ornament
    cx=(o['u0']+o['u1'])/2;cz=o['spring_z'];rad=o['r_in']
    from archetypes.masonry_house_v4_entry import settings,relief_profile,recessed_bed
    spec=settings(b);profile=relief_profile(spec,cx,cz,rad+.04) if spec else None
    r=_low_relief(d)(b,o,b.params.detail.get('conf',o['conf']),orn.CARVED_GRANITE,profile=profile)
    d.rock_voussoirs(b,o,cx,cz,rad+.04,o['r_out'],o.get('voussoirs') or 15,b.params.detail.get('conf',o['conf']),90211)
    if spec:recessed_bed(r,cx,cz,rad+.04,o['r_out'],spec,reduced=True)
    else:r.solid([(cx+o['r_out']*math.cos(math.pi*i/20),cz+o['r_out']*math.sin(math.pi*i/20)) for i in range(21)],-.065,-.045)
    R=rad+.04
    # The bands of ornament.fan, outside in, at the same radii and depths.
    r.arc(cx,cz,R-.012,.034,.012)
    orn._annulus(r,cx,cz,R*.885,R-.02,-.045,.004,12)
    for i in range(33):
        th=math.pi*(i+.5)/33;da=math.pi/33*.30
        orn._boss(r,[(cx+rr*math.cos(aa),cz+rr*math.sin(aa))
                     for rr,aa in [(R*.902,th-da*1.08),(R-.032,th-da),(R-.032,th+da),(R*.902,th+da*1.08)]],.004,.040,.16)
    r.arc(cx,cz,R*.878,.030,.010)
    orn._annulus(r,cx,cz,R*.705,R*.868,-.045,-.004,12)
    band=R*.786;size=R*.150
    for i in range(23):
        th=math.pi*(i+.5)/23
        base=(cx+(band-size*.5)*math.cos(th),cz+(band-size*.5)*math.sin(th))
        r.leaf(*base,th,size,size*.62,.004,.022,.06)
        for side in (-1,1):
            r.leaf(*base,th+side*.62,size*.74,size*.42,.000,.018,side*.20)
    for i in range(24):
        th=math.pi*i/23
        r.bead(cx+band*math.cos(th),cz+band*math.sin(th),.012,.0085)
    r.arc(cx,cz,R*.690,.026,.018)
    r.arc(cx,cz,R*.655,.010,.008)
    F=R*.640
    def stem(points,depth=.020,width=.011):
        r.tube(orn._bezier([(cx+x*F,cz+z*F) for x,z in points],depth,20),width)
    def roundel(x,z,radius,depth):
        r.arc(x,z,radius,depth,radius*.075,0,2*math.pi,40)
        for j in range(6):
            th=math.pi/2+2*math.pi*j/6
            r.leaf(x+radius*.10*math.cos(th),z+radius*.10*math.sin(th),th,radius*.86,radius*.62,depth-.006,radius*.16,(.18 if j%2 else -.18))
        r.bead(x,z,depth+.012,radius*.16)
    stem([(0,.0),(0,.25),(0,.55),(0,.80)],.022,.016)
    for mirror in (-1,1):
        stem([(0,.10),(mirror*.18,.12),(mirror*.30,.18),(mirror*.36,.28)])
        stem([(0,.46),(mirror*.08,.50),(mirror*.16,.56),(mirror*.21,.62)])
        roundel(cx+mirror*F*.53,cz+F*.33,F*.235,.024)
        roundel(cx+mirror*F*.27,cz+F*.70,F*.165,.026)
        for x,z,ang,ln in ((.20,.06,.30,.24),(.80,.10,1.75,.20),(.10,.36,.95,.22),(.48,.62,1.25,.22),
                           (.70,.52,2.10,.18),(.42,.86,1.95,.15),(.86,.30,1.45,.15),(.08,.66,1.15,.18)):
            r.leaf(cx+mirror*F*x,cz+F*z,ang if mirror>0 else math.pi-ang,F*ln,F*ln*.55,.016,.016,mirror*.16)
        for x,z,ang,ln in ((.30,.04,.10,.20),(.62,.06,1.00,.16),(.92,.18,1.60,.12),(.30,.52,1.40,.15),
                           (.58,.84,2.40,.12),(.20,.92,1.80,.10),(.06,.20,1.30,.16),(.40,.16,.60,.14),(.76,.68,2.60,.12)):
            r.leaf(cx+mirror*F*x,cz+F*z,ang if mirror>0 else math.pi-ang,F*ln,F*ln*.60,.010,.014,-mirror*.14)
    roundel(cx,cz+F*.83,F*.120,.028)
    r.solid([(cx+F*.14*math.cos(math.pi*i/8),cz+F*.14*math.sin(math.pi*i/8)) for i in range(9)],-.045,.012)
    for j in range(5):
        th=math.pi*(j+.5)/5
        r.leaf(cx+F*.03*math.cos(th),cz+.004+F*.03*math.sin(th),th,F*.13,F*.075,.012,.010,0)


def _columns(b,params,d):
    # T-2965: the full tier's colonnettes (ornament.columns) at fewer facets: splayed
    # base, tapered shaft, cushion block, its carved band as one raised course and
    # the leaf tips; the bodies' fine carving is the master's alone.
    orn=d.ornament;spec=params.detail.get('prairie_colonnette') or {}
    ops=sorted([o for o in params.openings if o['kind']=='window' and o['face']=='east' and o['z0']>5],
               key=lambda o:(round(o['at'],3),round(o['z0'],2),o['u0']))
    for a,c in zip(ops,ops[1:]):
        gap=c['u0']-a['u1']
        if not .12<gap<.3 or abs(a['z0']-c['z0'])>.05 or abs(a['at']-c['at'])>.05:continue
        u=(c['u0']+a['u1'])/2;z0,z1=a['z0'],a['z1'];h=z1-z0
        r=orn.Relief(b,a,params.detail.get('conf',max(a['conf'],c['conf'])),orn.CARVED_GRANITE)
        foot=spec.get('shaft_foot_m',gap*1.24)/2;neck=spec.get('shaft_neck_m',gap*.98)/2
        half=spec.get('abacus_m',gap*2.3)/2
        base=z0+h*spec.get('base_share',.13);low=z1-h*spec.get('capital_share',.33)
        dep=-foot
        r.box(u-gap*.5-.004,u+gap*.5+.004,base,low,-spec.get('mullion_depth_m',.46),dep)
        orn._splayed_base(r,u,z0,base,spec.get('base_foot_m',gap*1.8)/2,foot+.008,dep)
        orn._taper(r,u,base,low,foot,neck,dep,12)
        top=z1-.012;ch=top-low
        orn._block(r,u,low,top,neck,half,dep,16,5)
        r.box(u-half*.92,u+half*.92,low+ch*.82,top-.01,dep+half-.01,dep+half+.012)
        for j in range(3):
            r.leaf(u+(j-1)*half*.45,low+ch*.12,math.pi*.5+(j-1)*.15,ch*.30,half*.28,
                   dep+neck+(half-neck)*.30,.02,0,False,steps=4)


def _ridges(b,params,d):
    if params.detail.get("roof_edges"):
        from archetypes.masonry_house_v4_roof_edges import add_ridges
        return add_ridges(b,params)
    # Same per-tile raised crest envelopes. Four angular intervals include the
    # exact crown and both shoulders while removing invisible sub-centimetre arcs.
    from archetypes.masonry_house_v4_west_roof import ridge_ranges
    for r,a0,a1 in (segment for source in params.ranges for segment in ridge_ranges(source)):
        for i in range(math.ceil((a1-a0)/.36)):
            lo=a0+i*.36+.006;hi=min(a1,lo+.348)
            def P(a,along,radius):
                offset=along-r.get('ridge_origin',0)
                across=r['ridge_at']+r.get('ridge_skew',0)*offset+radius*math.cos(a)
                z=r['ridge_z']+r.get('ridge_slope',0)*offset+.055+radius*math.sin(a)
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


def _blender(root):
    """The pinned Blender bake.sh fetched (generators/blender.pin), or $BLENDER."""
    import os
    if os.environ.get('BLENDER'):return os.environ['BLENDER']
    pin=dict(line.split('=',1) for line in (Path(root)/'generators/blender.pin').read_text().splitlines()
             if '=' in line and not line.lstrip().startswith('#'))
    binary=Path(os.environ.get('BLENDER_CACHE','/opt/blender-dl'))/pin['BLENDER_DIR']/'blender'
    if not binary.is_file():
        raise RuntimeError(f'The light LOD bakes its own occlusion and needs the pinned Blender at {binary}; '
                           'run tools/bake.sh once to fetch it, or set BLENDER')
    return str(binary)


def _png_grey(rows):
    """An 8-bit greyscale PNG of `rows` (top row first), Up-filtered, written the same way every time."""
    height,width=len(rows),len(rows[0]);raw=bytearray();previous=bytes(width)
    for row in rows:
        row=bytes(row);raw.append(2);raw.extend((a-b)&255 for a,b in zip(row,previous));previous=row
    def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,0,0,0,0))+
            chunk(b'IDAT',zlib.compress(bytes(raw),9))+chunk(b'IEND',b''))


def _stone_occlusion(root,groups):
    """T-2401: bake the reduced mesh's own stone-scale occlusion, as T-2400 baked the master's.

    The light tier is a different mesh from the master, so the master's TEXCOORD_1 bake
    cannot ride it. Every face goes to Blender as an occluder; the granite slots are
    unwrapped onto their own OcclusionUV and baked by the master's own baker
    (tools/_glessner_light_occlusion.py), at OCCLUSION_SIZE. Returns each group's
    TEXCOORD_1 values, the atlas as PNG bytes, and the baker's record.
    """
    import numpy as np
    order=sorted(groups)
    co=np.concatenate([np.asarray(groups[m]['p'],np.float64).reshape(-1,3) for m in order])
    co=np.stack([co[:,0],-co[:,2],co[:,1]],1)   # back to the builder's z-up
    uv0=np.concatenate([np.asarray(groups[m]['uv'],np.float32).reshape(-1,2) for m in order])
    corners=np.concatenate([np.asarray(groups[m]['k'],np.int32) for m in order])
    slot=np.concatenate([np.full(len(groups[m]['k']),m,np.int32) for m in order])
    with tempfile.TemporaryDirectory(prefix='glessner-light-ao-') as tmp:
        source,target=Path(tmp)/'in.npz',Path(tmp)/'out.npz'
        np.savez(source,co=co,uv0=uv0,corners=corners,slot=slot,slots=np.array(MATERIAL_NAMES),
                 size=np.int32(OCCLUSION_SIZE))
        run=subprocess.run([_blender(root),'-b','-noaudio','--factory-startup','--python',
                            str(Path(root)/'tools/_glessner_light_occlusion.py'),'--',str(source),str(target)],
                           capture_output=True,text=True)
        if run.returncode or not target.is_file():
            raise RuntimeError('Light LOD occlusion bake failed:\n'+(run.stdout+run.stderr)[-3000:])
        out=np.load(target)
        uv1,ao,record=out['uv1'],out['ao'],json.loads(str(out['record']))
    if len(uv1)!=len(co):raise RuntimeError('Light LOD occlusion bake returned the wrong corner count')
    per={};start=0
    for m in order:
        n=len(groups[m]['p'])//3
        # glTF's v runs down the image, Blender's up.
        per[m]=[float(x) for uv in uv1[start:start+n] for x in (uv[0],1-uv[1])];start+=n
    return per,_png_grey(ao.tolist()),record


def _baked_occlusion(materials,textures,images,append,png):
    """T-2401: each material whose master occlusion is the TEXCOORD_1 stone bake (T-2400)
    takes the light mesh's own bake in that image's slot, on the light's own TEXCOORD_1.
    The material, texture and sampler are the master's; only the image bytes are the
    light's. T-2393's tiling map (`occlusion_tiling_map`) is no longer put back.
    """
    from archetypes.masonry_house_v4_occlusion import GRANITE_SLOTS
    granite={MATERIAL_NAMES[i] for i in GRANITE_SLOTS};sources=set()
    for material in materials:
        occlusion=material.get('occlusionTexture')
        if not occlusion or occlusion.get('texCoord',0)==0:continue
        if material.get('name') not in granite:
            raise ValueError(f"{material.get('name')} reads a TEXCOORD_1 occlusion the light LOD does not bake")
        sources.add(textures[occlusion['index']]['source'])
    for source in sources:
        images[source]={'name':'granite_stone_occlusion_light','mimeType':'image/png','bufferView':append(png)}
    return materials,textures


@_blender_arithmetic
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
    owner=next((n for n in full.get('nodes',[]) if n.get('extras',{}).get('detail_profile')=='glessner_v4'),None)
    if owner is None:raise ValueError('Source master is not the detailed Glessner v4')
    b,params,uv_module=_construct(root)
    required=MATERIAL_NAMES[:29] if params.detail.get('rainwater') else MATERIAL_NAMES[:28]
    if params.detail.get('vines'):required+=MATERIAL_NAMES[29:30]
    if params.detail.get('surface_finish'):required+=MATERIAL_NAMES[30:31]
    if any(n not in names for n in required):raise ValueError('Full master does not contain the expected v4 material library')
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
        group=groups.setdefault(material,{'p':[],'n':[],'uv':[],'c':[],'rd':[],'i':[],'k':[]})
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
            vertex_normal=b.pillow_normals.get(index,normal)
            group['n'].extend((vertex_normal[0],vertex_normal[2],-vertex_normal[1]))
            uv=b.roof_uvs.get(index,(sum(p*v for p,v in zip(point,horizontal)),sum(p*v for p,v in zip(point,uphill))))
            group['uv'].extend((uv[0]/tu,1-uv[1]/tv))
            group['c'].append(b.conf[index])
            group['rd'].append(b.roof_detail.get(index,0))
        group['k'].append(len(face))
        for triangle in triangles:group['i'].extend(start+i for i in triangle)
        triangle_count+=len(triangles)
    if triangle_count>MAX_TRIANGLES:raise ValueError(f'Reduced Glessner has {triangle_count:,} triangles; limit {MAX_TRIANGLES:,}')
    uv1,occlusion_png,occlusion_record=_stone_occlusion(root,groups)
    from archetypes.masonry_house_v4_occlusion import GRANITE_SLOTS
    primitives=[]
    for material,g in sorted(groups.items()):
        attributes={'POSITION':accessor(g['p'],3,bounds=True),'NORMAL':accessor(g['n'],3),
                    'TEXCOORD_0':accessor(g['uv'],2),'_CONFIDENCE':accessor(g['c'],1,bounds=True),
                    '_ROOF_DETAIL':accessor(g['rd'],1,bounds=True)}
        if material in GRANITE_SLOTS:attributes['TEXCOORD_1']=accessor(uv1[material],2)
        primitives.append({'attributes':attributes,'indices':accessor(g['i'],1,'I'),
                           'material':names[MATERIAL_NAMES[material]],'mode':4})
    extras=copy.deepcopy(owner.get('extras',{}))
    extras.update({'lod':'light','grass_blades':0,'roof_tiles':0,'masonry_blocks':b.masonry_blocks,
                   'openings_recessed':sum(counts.values()),'aperture_counts':counts,
                   'stone_occlusion':occlusion_record})
    extras['vine_panels']=b.components['vine_panels']
    bounds=[[min(p[k] for p in b.verts),max(p[k] for p in b.verts)] for k in range(3)]
    receipt={'master_sha256':master_sha,'recipe_sha256':recipe_sha256,'triangles':triangle_count,
             'openings_recessed':sum(counts.values()),'bounds_zup_m':bounds,
             'profile':'same_v4_reduced_surface_sampling'}
    materials,textures=_baked_occlusion(copy.deepcopy(materials),copy.deepcopy(full.get('textures',[])),images,append,occlusion_png)
    doc={'asset':copy.deepcopy(full['asset']),'scene':0,'scenes':[{'nodes':[0]}],
         'nodes':[{'name':b.name+'.light','mesh':0,'extras':extras}],
         'meshes':[{'name':b.name+'.light','primitives':primitives}],
         'materials':materials,'images':images,'textures':textures,
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
