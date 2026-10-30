# SPDX-License-Identifier: GPL-3.0-or-later
"""Original reconstructed workwear geometry, evaluated without Blender.

Generated graphical arrays are CC0-1.0, as are their cleared body inputs. The
clothes are not an attested outfit or a photographic human. This helper keeps
the body/rig unchanged, shares offsets across source UV seams, cuts the vest V
on actual triangles, and constructs a shoe around actual source foot sections.
"""
from __future__ import annotations
import math,collections,copy
from human_source_normals import source_shared_normals


def _unit(v):
    d=math.hypot(*v)
    if not math.isfinite(d) or d<=1e-20:raise ValueError('zero or nonfinite normal')
    return [x/d for x in v]


def _mix(a,b,t):return [math.fsum((x*(1-t),y*t)) for x,y in zip(a,b)]


def _clip(poly,field):
    """Retain field>=0 and interpolate source barycentrics, UVs and weights."""
    if not poly:return []
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=field(a),field(b)
        if da>=0:out.append(a)
        if (da<0<db) or (db<0<da):
            # A consistent endpoint order also makes a shared source edge's
            # cut identical when its neighboring face traverses it backwards.
            if tuple(sorted(a['basis'].items()))>tuple(sorted(b['basis'].items())):a,b,da,db=b,a,db,da
            t=da/(da-db)
            basis={i:math.fsum((a['basis'].get(i,0)*(1-t),b['basis'].get(i,0)*t)) for i in sorted(set(a['basis'])|set(b['basis']))}
            out.append({'p':_mix(a['p'],b['p'],t),'uv':_mix(a['uv'],b['uv'],t),
                        'n':_mix(a['n'],b['n'],t),'basis':basis,
                        'w':{i:math.fsum((a['w'].get(i,0)*(1-t),b['w'].get(i,0)*t)) for i in sorted(set(a['w'])|set(b['w']))}})
    clean=[]
    for v in out:
        if not clean or math.dist(v['p'],clean[-1]['p'])>1e-14:clean.append(v)
    if len(clean)>1 and math.dist(clean[0]['p'],clean[-1]['p'])<=1e-14:clean.pop()
    return clean


def garment_shell(m,kind,offset,recipe,bones,height,scale=1.):
    """A source-derived shell with coincident UV seams and clipped vest edges.

    Original source UVs and exact weights survive on original vertices. New vest
    cut vertices interpolate them on their source triangle. At most four skin
    influences are emitted; actual discarded mass must stay below 2.5 percent.
    This is a disclosed garment interpolation choice, not a change to body skin.
    """
    if kind not in ('shirt','waistcoat','trousers') or not 0<scale or not 0<offset<.05:
        raise ValueError('invalid garment kind/scale/ease')
    ps=m['positions_m'];fs=m['triangles'];sids=m['source_vertex_indices']
    ns=source_shared_normals(ps,fs,sids)
    waist=recipe['waist_height_fraction']*height/scale
    hem=recipe['shirt_hem_fraction']*height/scale
    shoulder=bones['upperarm_l']['head_m'][1]
    wrist=abs(bones['hand_l']['head_m'][0]);neck=bones['neck_01']['head_m'][1]
    tailoring=recipe['workwear_tailoring_v5']
    closure_y=waist+tailoring['waistcoat_closed_front_torso_fraction']*(shoulder-waist)
    slope=.105/max(.01,shoulder-closure_y)
    vest_top=shoulder+.025
    shoulder_pattern=recipe.get('waistcoat_shoulder_pattern') if kind=='waistcoat' else None
    armhole_fields=None
    if shoulder_pattern:
        if shoulder_pattern.get('id')!='bardwell_connected_waistcoat_v1':raise ValueError('unsupported waistcoat shoulder pattern')
        # Original reconstructed pattern dimensions, not measurements from Mount.
        # Upper-arm joint height is below the shoulder crest; it is not a top seam.
        vest_top=neck-shoulder_pattern['neckline_drop_m']/scale
        slope=(shoulder_pattern['neck_opening_halfwidth_m']/scale)/max(.01,vest_top-closure_y)
        lo=shoulder-shoulder_pattern['armhole_transition_below_joint_m'][0]/scale
        hi=shoulder-shoulder_pattern['armhole_transition_below_joint_m'][1]/scale
        limit=abs(bones['upperarm_l']['head_m'][0])-shoulder_pattern['shoulder_outer_inset_m']/scale
        field_scale=shoulder_pattern['armhole_field_scale_m']/scale
        if not waist<lo<hi<vest_top<neck or not .10/scale<limit<.20/scale or field_scale<=0:raise ValueError('invalid source shoulder-pattern landmarks')
        armhole_fields={}
        for sid,p,w in zip(sids,ps,m['weights']):
            arm=math.fsum(v for b,v in w.items() if b.startswith(('clavicle','upperarm','lowerarm')))
            t=max(0.,min(1.,(p[1]-lo)/(hi-lo)))
            field=(1-t)*(.35-arm)+t*(limit-abs(p[0]))/field_scale
            if sid in armhole_fields and armhole_fields[sid]!=field:raise ValueError('source UV duplicate armhole fields disagree')
            armhole_fields[sid]=field
        # The scalar is defined on ORIGINAL source corners. Barycentric lookup
        # makes every later clip linear within its original triangle and exactly
        # shared across source edges; no nonlinear field hidden inside _clip.
    hang=trouser_hang_profile(m,bones,tailoring,scale) if kind=='trousers' else None
    shirt_ease=None
    if kind=='shirt':
        # Derive a continuous torso-to-sleeve ease field from the cleared arm
        # frame and actual dominant upperarm surface extent. It reduces the
        # inherited X shift above the arm axis, where actual posed shoulder
        # faces otherwise intersect, and retains it on the lower arm surface.
        arm_axis_y=math.fsum(bones['upperarm_'+side]['head_m'][1] for side in ('l','r'))/2
        radial=max(abs(p[1]-arm_axis_y) for p,w in zip(ps,m['weights']) if max(w.get('upperarm_l',0.),w.get('upperarm_r',0.))>.5)
        fraction=recipe['workwear_tailoring']['shirt_x_ease_arm_radius_fraction']
        if not 0<fraction<=1 or radial<=0:raise ValueError('invalid source-arm shirt ease field')
        shirt_ease={'axis_y_m':arm_axis_y,'actual_arm_radial_extent_m':radial,'transition_width_m':fraction*radial,'radius_fraction':fraction}
    result={'positions_m':[],'triangles':[],'uvs':[],'weights':[],'source_basis':[],'corner_uvs':[],'source_triangle_indices':[]}
    cache={};selected=[];maximum_drop=0.;maximum_neck_transfer=0.;discarded_zero=0
    for fi,face in enumerate(fs):
        p=[math.fsum(ps[i][a] for i in face)/3 for a in range(3)]
        w={}
        for i in face:
            for b,v in m['weights'][i].items():w[b]=w.get(b,0)+v/3
        arm=sum(v for b,v in w.items() if b.startswith(('clavicle','upperarm','lowerarm')))
        leg=sum(v for b,v in w.items() if b.startswith(('thigh','calf','pelvis')))
        foot=sum(v for b,v in w.items() if b.startswith(('foot','ball')))
        keep=((hem<=p[1]<=neck+.035 and abs(p[0])<.23) or (arm>.35 and abs(p[0])<wrist-.012)) if kind=='shirt' else (
             waist-.04<=p[1]<=vest_top and arm<.35 and abs(p[0])<.235) if kind=='waistcoat' else (
             p[1]<=waist and leg>.25 and foot<.35)
        if kind=='waistcoat':
            # Candidate next trim: retain every face crossing the torso slab;
            # continuous source fields, never centroid ownership, cut its edges.
            keep=(max(ps[i][1] for i in face)>=waist-.04 and min(ps[i][1] for i in face)<=vest_top)
        if not keep:continue
        selected.append(fi)
        poly=[{'p':ps[i],'uv':m['uvs'][i],'w':m['weights'][i],'n':ns[i],'basis':{sids[i]:1.}} for i in face]
        # End the shirt on the actual existing collar's base plane. This
        # clips triangles and interpolates UVs/weights, instead of selecting
        # jagged whole faces by head weight. Neck/skin anatomy stays exact.
        polys=[_clip(poly,lambda v:neck-v['p'][1])] if kind=='shirt' else [poly]
        if kind=='waistcoat':
            # Clip source corners/UVs/weights exactly on the declared lower/top
            # planes, side envelope and continuous arm-influence contour.
            poly=_clip(poly,lambda v:v['p'][1]-(waist-.04))
            poly=_clip(poly,lambda v:vest_top-v['p'][1])
            if shoulder_pattern:poly=_clip(poly,lambda v:shoulder_pattern['maximum_head_jaw_source_mass']-math.fsum(v['w'].get(b,0.) for b in ('head','jaw')))
            poly=_clip(poly,lambda v:.235-v['p'][0])
            poly=_clip(poly,lambda v:.235+v['p'][0])
            poly=_clip(poly,lambda v:math.fsum(armhole_fields[i]*w for i,w in v['basis'].items())) if armhole_fields is not None else _clip(poly,lambda v:.35-math.fsum(w for b,w in v['w'].items() if b.startswith(('clavicle','upperarm','lowerarm'))))
            # A union of three disjoint source regions. Their shared z=0
            # boundary is a seam, and the two front boundaries are straight Vs.
            back=_clip(poly,lambda v:-v['p'][2])
            front=_clip(poly,lambda v:v['p'][2])
            left=_clip(_clip(front,lambda v:v['p'][0]),lambda v:v['p'][0]-slope*(v['p'][1]-closure_y))
            right=_clip(_clip(front,lambda v:-v['p'][0]),lambda v:-v['p'][0]-slope*(v['p'][1]-closure_y))
            polys=[back,left,right]
        for polygon in polys:
            ids=[]
            for vertex in polygon:
                n=_unit(vertex['n']);p=[vertex['p'][a]+n[a]*offset/scale for a in range(3)]
                # A global outwardX shift cancels normal ease on the INNER
                # leg. Trousers keep their full positive normal offset only.
                if kind!='trousers' and abs(p[0])>.02:
                    ease=1. if kind!='shirt' else max(0.,min(1.,(shirt_ease['axis_y_m']-vertex['p'][1])/shirt_ease['transition_width_m']))
                    p[0]+=ease*math.copysign(.007/scale,p[0])
                if kind=='shirt':
                    # Cut-edge normals can have a small vertical component.
                    # The garment seam itself stays on its declared collar
                    # plane instead of sagging into a near-planar stair edge.
                    p[1]=neck if abs(vertex['p'][1]-neck)<=1e-12 else min(p[1],neck)
                if kind=='waistcoat':
                    lo,hi=waist-.04,vest_top
                    if 'modular_wardrobe' in recipe:
                        # Keep the declared cut planes while easing vertical
                        # normal displacement continuously toward them. Clamping
                        # displaced interior vertices onto the hem creates folded
                        # coplanar fans on the adult35 source (opposite normals).
                        # This bound leaves every interior point strictly inside
                        # the slab, without dropping faces or altering anatomy.
                        edge_distance=max(0.,min(vertex['p'][1]-lo,hi-vertex['p'][1]))
                        gain=min(1.,edge_distance/(2*offset/scale))
                        p[1]=vertex['p'][1]+n[1]*offset/scale*gain
                    else:
                        p[1]=lo if abs(vertex['p'][1]-lo)<=1e-12 else (hi if abs(vertex['p'][1]-hi)<=1e-12 else max(lo,min(hi,p[1])))
                if kind=='trousers':p=hanging_trouser_point(p,vertex['w'],hang)
                mapping=dict(vertex['w'])
                if kind=='shirt' and abs(vertex['p'][1]-neck)<=1e-12:
                    # The newly cut collar seam belongs to the neck garment,
                    # not the moving jaw/face. Rebind only this new seam, never
                    # the body or existing shirt vertices below the cut.
                    transfer=math.fsum(mapping.pop(k,0.) for k in ('head','jaw'))
                    mapping['neck_01']=mapping.get('neck_01',0.)+transfer
                    maximum_neck_transfer=max(maximum_neck_transfer,transfer)
                weights=sorted(((k,v) for k,v in mapping.items() if v>1e-12),key=lambda kv:(-kv[1],kv[0]))
                dropped=math.fsum(v for k,v in weights[4:]);maximum_drop=max(maximum_drop,dropped)
                if dropped>.025:raise ValueError('garment cut exceeds 2.5 percent discarded skin mass: '+repr((fi,dropped,weights)))
                weights=weights[:4];total=math.fsum(v for k,v in weights)
                if total<=0:raise ValueError('empty garment skin weights')
                weights={k:v/total for k,v in weights}
                basis={k:v for k,v in vertex['basis'].items() if v>1e-12}
                # Geometry is shared across an original body's UV seam. UVs
                # live on corners, so the decimator cannot pull two coincident
                # seam vertices apart and reopen the garment at a lower LOD.
                key=(tuple(p),tuple(sorted(weights.items())))
                if key not in cache:
                    cache[key]=len(result['positions_m']);result['positions_m'].append(p)
                    result['uvs'].append(list(vertex['uv']));result['weights'].append(weights);result['source_basis'].append(basis)
                ids.append(cache[key])
            for k in range(1,len(ids)-1):
                tri=[ids[0],ids[k],ids[k+1]]
                a,b,c=[result['positions_m'][i] for i in tri]
                u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
                cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                if len(set(tri))<3 or math.hypot(*cross)<=1e-18:discarded_zero+=1;continue
                result['triangles'].append(tri)
                result['source_triangle_indices'].append(fi)
                result['corner_uvs'].append([polygon[j]['uv'] for j in (0,k,k+1)])
    if not result['triangles']:raise ValueError('empty garment shell')
    result['receipt']={'kind':kind,'source_selected_faces':selected,'source_uv_seams':'Full-body source-shared normals, not isolated UV chart normals',
        'neckline_clip_y_m':neck if kind=='shirt' else None,
        'maximum_new_collar_seam_head_jaw_mass_rebound_to_neck':maximum_neck_transfer,
        'additional_global_x_ease_m':0. if kind=='trousers' else .007,'shirt_continuous_x_ease_field':shirt_ease,'trouser_hang_profile':hang,
        'waistcoat_front_closure_y_m':closure_y if kind=='waistcoat' else None,
        'body_mutated':False,'maximum_discarded_cut_weight':maximum_drop,'degenerate_cut_fans_discarded':discarded_zero,
        'fit_accepted':False,'scope':'Original source construction; actual deformation and rendered clothing still need review'}
    if shoulder_pattern:result['receipt'].update(waistcoat_shoulder_pattern=shoulder_pattern,waistcoat_top_clip_y_m=vest_top)
    if kind=='trousers':result=level_trouser_hems(result,bones)
    return result


def _slab_points(triangles,lo,hi):
    result=[]
    for tri in triangles:
        poly=[{'p':p,'uv':[],'n':[],'w':{},'basis':{i:1.}} for i,p in enumerate(tri)]
        poly=_clip(_clip(poly,lambda v:v['p'][1]-lo),lambda v:hi-v['p'][1])
        result.extend(v['p'] for v in poly)
    return result


def fitted_shoes(body,bones,lod,scale=1.,clearance_m=.004):
    """Closed soles and support-plane lofts enclosing the actual source feet.

    Each ring's support polygon contains both adjacent complete body slabs.
    The fixed-normal support values interpolate linearly between rings, so every
    clipped source triangle is inside the actual planar loft at rest. An open
    ankle at145mm is deliberate; trousers overlap it. No body is hidden.
    """
    if lod not in range(4) or scale<=0 or not .002<=clearance_m<=.01:raise ValueError('invalid shoe parameters')
    N=[32,24,16,12][lod]
    levels=[v/scale for v in (0,.016,.035,.060,.085,.115,.145)]
    clearance=clearance_m/scale
    planes=[(math.cos(2*math.pi*k/N),math.sin(2*math.pi*k/N)) for k in range(N)]
    out={'positions_m':[],'triangles':[],'uvs':[],'weights':[]};reports=[]
    for side,cell in [('l',0),('r',1)]:
        sign=1 if side=='l' else -1
        triangles=[]
        for mesh in body['meshes']:
            for face in mesh['triangles']:
                ps=[mesh['positions_m'][i] for i in face]
                if min(p[1] for p in ps)>levels[-1] or max(p[1] for p in ps)<0:continue
                if math.fsum(p[0] for p in ps)*sign<=0:continue
                # Preserve exact named-limb ownership instead of assuming the
                # sign of a stray source vertex establishes a foot identity.
                chain={j+'_'+side for j in ('thigh','calf','foot','ball')}
                if min(math.fsum(v for k,v in mesh['weights'][i].items() if k in chain) for i in face)<.9:
                    raise ValueError('body triangle in shoe band has ambiguous leg ownership')
                triangles.append(ps)
        if not triangles:raise ValueError('no source foot triangles')
        supports=[]
        for i,y in enumerate(levels):
            points=_slab_points(triangles,levels[max(0,i-1)],levels[min(len(levels)-1,i+1)])
            if len(points)<3:raise ValueError('empty source foot section')
            supports.append([max(nx*p[0]+nz*p[2] for p in points)+clearance for nx,nz in planes])
        minimum=math.inf;sample_count=0
        for i,(lo,hi) in enumerate(zip(levels,levels[1:])):
            for p in _slab_points(triangles,lo,hi):
                t=(p[1]-lo)/(hi-lo)
                for k,(nx,nz) in enumerate(planes):
                    margin=(1-t)*supports[i][k]+t*supports[i+1][k]-nx*p[0]-nz*p[2]
                    minimum=min(minimum,margin);sample_count+=1
        if minimum<clearance-1e-12:raise ValueError('source foot escapes support-plane loft')
        base=len(out['positions_m']);det=math.sin(2*math.pi/N)
        for j,y in enumerate(levels):
            for k,(nx,nz) in enumerate(planes):
                next_k=(k+1)%N;mx,mz=planes[next_k];h,q=supports[j][k],supports[j][next_k]
                x=(h*mz-nz*q)/det;z=(nx*q-h*mx)/det
                out['positions_m'].append([x,y,z]);out['uvs'].append([(cell+.05+.9*k/N)/2,.05+.9*j/(len(levels)-1)])
                blend=max(0.,min(1.,(z-bones['ball_'+side]['head_m'][2]+.04/scale)/(.08/scale)))
                out['weights'].append({'foot_'+side:1-blend,'ball_'+side:blend})
        for j in range(len(levels)-1):
            for k in range(N):
                a=base+j*N+k;b=base+j*N+(k+1)%N;c=b+N;d=a+N
                out['triangles'].extend([[a,c,b],[a,d,c]])
        center=len(out['positions_m']);p=[math.fsum(out['positions_m'][base+k][a] for k in range(N))/N for a in range(3)]
        out['positions_m'].append(p);out['uvs'].append([(cell+.5)/2,.025]);out['weights'].append({'foot_'+side:1.})
        for k in range(N):out['triangles'].append([center,base+k,base+(k+1)%N])
        reports.append({'side':side,'source_triangles_in_band':len(triangles),'support_inequality_checks':sample_count,
            'minimum_source_support_clearance_m':minimum*scale,'ankle_height_m':levels[-1]*scale,'plane_count':N,
            'body_hidden':False,'proof_scope':'Exact source triangle slab vertices satisfy every linear loft support plane; source Float64 only, actual exported/readback deformation and contact remain untested'})
    out['receipt']={'sides':reports,'clearance_m':clearance_m,'ring_heights_m':[v*scale for v in levels],
        'parameters_status':'Reconstructed footwear last/ease, not an attested shoe or material measurement',
        'export_or_walk_contact_accepted':False}
    return out


def standing_collar_extension(shirt,body_mesh,bones,recipe,scale=1.):
    neck=bones['neck_01']['head_m'];base_y=neck[1]
    edge_faces=collections.defaultdict(list)
    for face in shirt['triangles']:
        for a,b in zip(face,face[1:]+face[:1]):edge_faces[tuple(sorted((a,b)))].append((a,b))
    edges=[e for e,faces in edge_faces.items() if len(faces)==1 and all(abs(shirt['positions_m'][i][1]-base_y)<=1e-12 for i in e)]
    graph=collections.defaultdict(set)
    for a,b in edges:graph[a].add(b);graph[b].add(a)
    if not graph or any(len(v)!=2 for v in graph.values()):raise ValueError('collar requires a closed degree-two shirt boundary')
    start=min(graph);ids=[start];previous=None;current=start
    while True:
        nxt=min(graph[current]-({previous} if previous is not None else set()))
        if nxt==start:break
        if nxt in ids:raise ValueError('collar boundary repeats before closure')
        ids.append(nxt);previous,current=current,nxt
    if len(ids)!=len(graph):raise ValueError('collar boundary has multiple cycles')
    N=len(ids);result=copy.deepcopy(shirt);shirt_vertices=len(shirt['positions_m']);shirt_faces=len(shirt['triangles'])
    # Fixed source angular rays retain the existing welded loop's parameterization.
    angles=[math.atan2(shirt['positions_m'][i][2]-neck[2],shirt['positions_m'][i][0]-neck[0]) for i in ids]
    parameters=recipe['workwear_tailoring']
    max_height=recipe['collar_height_m']/scale;front_height=parameters['collar_front_height_m']/scale;front_dip=max_height-front_height;ease=recipe['shirt_offset_m']/scale
    if not 0<front_height<=max_height<.04/scale:raise ValueError('invalid reconstructed collar heights')
    thickness=parameters['collar_return_thickness_m']/scale;return_depth=parameters['collar_return_depth_m']/scale
    if not 0<thickness<ease or not 0<return_depth<front_height:raise ValueError('invalid reconstructed collar return')
    heights=[max_height-front_dip*max(0.,math.sin(t))**2 for t in angles]
    candidates=[]
    for fi,face in enumerate(body_mesh['triangles']):
        points=[body_mesh['positions_m'][i] for i in face]
        if min(p[1] for p in points)>base_y+max_height or max(p[1] for p in points)<base_y:continue
        if min(p[0] for p in points)>.15/scale or max(p[0] for p in points)<-.15/scale:continue
        candidates.append((fi,face))
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    def support(y,theta):
        d=(math.cos(theta),math.sin(theta));hits=[]
        for fi,face in candidates:
            points=[]
            for ia,ib in zip(face,face[1:]+face[:1]):
                a,b=body_mesh['positions_m'][ia],body_mesh['positions_m'][ib]
                if not ((a[1]<y<b[1]) or (b[1]<y<a[1])):continue
                t=(y-a[1])/(b[1]-a[1]);p=[a[k]+t*(b[k]-a[k]) for k in range(3)]
                points.append((p,{body_mesh['source_vertex_indices'][ia]:1-t,body_mesh['source_vertex_indices'][ib]:t}))
            if len(points)!=2:continue
            (a,wa),(b,wb)=points;A=(a[0]-neck[0],a[2]-neck[2]);E=(b[0]-a[0],b[2]-a[2]);den=cross(d,E)
            if abs(den)<1e-15:continue
            radius=cross(A,E)/den;u=cross(A,d)/den
            if radius<=0 or not -1e-10<=u<=1+1e-10:continue
            u=max(0.,min(1.,u));basis={sid:(1-u)*wa.get(sid,0)+u*wb.get(sid,0) for sid in set(wa)|set(wb)}
            hits.append((radius,fi,basis))
        hits.sort();unique=[]
        for hit in hits:
            if not unique or abs(hit[0]-unique[-1][0])>1e-8:unique.append(hit)
        if len(unique)!=1:raise ValueError('neck source ray must cross one boundary: '+repr((y,theta,len(unique))))
        radius,fi,basis=unique[0]
        return [neck[0]+(radius+ease)*d[0],y,neck[2]+(radius+ease)*d[1]],fi,basis
    distances=[math.dist(shirt['positions_m'][a],shirt['positions_m'][b]) for a,b in zip(ids,ids[1:]+ids[:1])]
    perimeter=math.fsum(distances);us=[math.fsum(distances[:k])/perimeter for k in range(N)]
    rings=[ids];support_records=[]
    for f in (.25,.5,.75,1.):
        ring=[]
        for k,(theta,height) in enumerate(zip(angles,heights)):
            p,fi,basis=support(base_y+f*height,theta)
            weights={j:(1-f)*v for j,v in shirt['weights'][ids[k]].items()};weights['neck_01']=weights.get('neck_01',0)+f
            weights={j:v for j,v in weights.items() if v>1e-12}
            if len(weights)>4 or abs(math.fsum(weights.values())-1)>1e-12:raise ValueError('collar portable weight overflow')
            ring.append(len(result['positions_m']));result['positions_m'].append(p);result['weights'].append(weights);result['uvs'].append([us[k],f]);result['source_basis'].append(basis)
            support_records.append({'vertex':ring[-1],'source_triangle':fi,'source_basis':basis,'ray_radial_ease_m':ease*scale,'height_fraction':f})
        rings.append(ring)
    # Original authored narrow turn-under at upper edge, with no body masking.
    ring=[]
    for k,theta in enumerate(angles):
        q=list(result['positions_m'][rings[-1][k]]);q[0]-=thickness*math.cos(theta);q[2]-=thickness*math.sin(theta);q[1]-=return_depth
        ring.append(len(result['positions_m']));result['positions_m'].append(q);result['weights'].append(dict(result['weights'][rings[-1][k]]));result['uvs'].append([us[k],.94]);result['source_basis'].append(dict(result['source_basis'][rings[-1][k]]))
    rings.append(ring)
    # Base edge direction is opposite the existing shirt face, then remains
    # consistent on all successive bands. The shared IDs cannot unzip under LOD.
    flip=edge_faces[tuple(sorted(ids[:2]))][0]==tuple(ids[:2])
    for row,(lower,upper) in enumerate(zip(rings,rings[1:])):
        for k in range(N):
            n=(k+1)%N;a,b,c,d=lower[k],lower[n],upper[n],upper[k];u0,u1=us[k],(us[n] if n else 1.);v0=row/5;v1=(row+1)/5
            faces=[([a,b,c],[[u0,v0],[u1,v0],[u1,v1]]),([a,c,d],[[u0,v0],[u1,v1],[u0,v1]])]
            for face,uv in faces:
                if flip:face.reverse();uv.reverse()
                result['triangles'].append(face);result['corner_uvs'].append(uv);result['source_triangle_indices'].append(None)
    result['collar_extension']={'original_shirt_vertex_count':shirt_vertices,'original_shirt_face_count':shirt_faces,'shared_base_vertex_ids':ids,'ring_vertex_ids':rings,'source_support':support_records,'same_linen_material':True,'ring0_positions_weights_unchanged':True,'front_height_m':front_height*scale,'side_back_height_m':max_height*scale,'radial_ease_m':ease*scale,'lip_thickness_m':thickness*scale,'lip_return_m':return_depth*scale,'construction':'Reconstructed standing collar with lower front profile to avoid source chin; no new period attestation','uv':'Original shirt corners unchanged; new collar has authored per-corner circumference/height island and explicit U0/1 seam','lod':'Unified shirt/collar topology before existing decimation; same linen material, no extra draw/material','accepted':False}
    return result


def trouser_hang_profile(mesh,bones,parameters,scale=1.):
    """Original knee-to-shoe hanging volume from actual cleared limb sections.

    High waist, seat and upper-thigh source topology remain; this bounded change
    removes calf/knee muscle following with an elliptical hanging silhouette.
    Dimensions are engineering choices, not measurements from an1835 painting.
    """
    result={'sides':{},'cuff_ratio':parameters['trouser_cuff_radius_ratio'],
        'fullness_m':parameters['trouser_added_section_ease_m'],
        'scope':'Static source construction only; no animated cloth/body/LOD/period/photo acceptance'}
    if not .7<=result['cuff_ratio']<=1 or not 0<result['fullness_m']<.04:raise ValueError('invalid reconstructed trouser fullness')
    for side in ('l','r'):
        hip,knee,ankle=[bones[j+'_'+side]['head_m'] for j in ('thigh','calf','foot')]
        fit_top=knee[1]+.1*(hip[1]-knee[1])
        join=knee[1]+parameters['trouser_thigh_transition_fraction']*(hip[1]-knee[1])
        lower=ankle[1]+.073/scale
        chain={j+'_'+side for j in ('thigh','calf','foot','ball')}
        points=[p for p,w in zip(mesh['positions_m'],mesh['weights']) if lower<=p[1]<=fit_top and math.fsum(v for j,v in w.items() if j in chain)>.9]
        if not points or not ankle[1]<knee[1]<join<hip[1]:raise ValueError('invalid source trouser leg bands')
        rx=max(abs(p[0]-hip[0]) for p in points)+result['fullness_m']/scale
        rz=max(abs(p[2]-hip[2]) for p in points)+result['fullness_m']/scale
        support=max(1.,max(math.hypot((p[0]-hip[0])/rx,(p[2]-hip[2])/rz) for p in points))
        rx*=support;rz*=support
        if rx>=abs(hip[0]):raise ValueError('hanging leg envelope reaches opposite leg centre plane')
        result['sides'][side]={'axis_x_m':hip[0],'axis_z_m':hip[2],
            'knee_y_m':knee[1],'transition_end_y_m':join,'hem_profile_y_m':ankle[1]+.03/scale,
            'section_rx_m':rx,'section_rz_m':rz,'body_support_vertices':len(points),
            'fit_band_y_m':[lower,fit_top],'source_bone_basis':'unchanged canonical prepared head_m frame; actual cleared source section supports'}
    return result


def hanging_trouser_point(point,weights,profile):
    """Continuous radial-only expansion; no body/weight/UV/Y or topology edit."""
    owner={side:math.fsum(v for j,v in weights.items() if j in {k+'_'+side for k in ('thigh','calf','foot','ball')}) for side in ('l','r')}
    side=max(owner,key=owner.get);p=list(point);s=profile['sides'][side]
    if p[1]>=s['transition_end_y_m']:return p
    if owner[side]<.9:raise ValueError('hanging trouser vertex lacks source-owned leg identity')
    t=max(0.,min(1.,(s['transition_end_y_m']-p[1])/(s['transition_end_y_m']-s['knee_y_m'])))
    blend=t*t*(3-2*t)
    taper=profile['cuff_ratio']+(1-profile['cuff_ratio'])*max(0.,min(1.,(p[1]-s['hem_profile_y_m'])/(s['knee_y_m']-s['hem_profile_y_m'])))
    dx,dz=p[0]-s['axis_x_m'],p[2]-s['axis_z_m'];r=math.hypot(dx/(taper*s['section_rx_m']),dz/(taper*s['section_rz_m']))
    if r<=1e-12:raise ValueError('trouser surface point lies on source leg axis')
    expand=1+blend*(max(1.,1/r)-1)
    p[0]=s['axis_x_m']+dx*expand;p[2]=s['axis_z_m']+dz*expand
    return p


def level_trouser_hems(shell,bones):
    """Trim only the jagged V5 hem band on its existing source-derived faces.

    Each level is the highest point of the corresponding actual boundary cycle,
    recorded relative to its source ankle. This is an engineering trim, not a
    historical measurement. Cut corners interpolate the existing V5 triangle's
    source barycentrics, UVs and skin; retained V5 positions stay bit-exact.
    The cuffs remain open tubes with closed perimeter cycles, never cap disks.
    """
    ps=shell['positions_m'];edges=collections.Counter(tuple(sorted(e)) for f in shell['triangles'] for e in zip(f,f[1:]+f[:1]))
    if max(edges.values())>2:raise ValueError('hem trim requires manifold input edges')
    adjacency=collections.defaultdict(set)
    for (a,b),count in edges.items():
        if count==1:adjacency[a].add(b);adjacency[b].add(a)
    if any(len(v)!=2 for v in adjacency.values()):raise ValueError('hem trim requires closed boundary cycles')
    seen=set();cycles=[]
    for first in sorted(adjacency):
        if first in seen:continue
        todo=[first];cycle=[]
        while todo:
            i=todo.pop()
            if i in seen:continue
            seen.add(i);cycle.append(i);todo.extend(sorted(adjacency[i]-seen))
        cycles.append(cycle)
    def owner(weights,side):return math.fsum(v for b,v in weights.items() if b in ('thigh_'+side,'calf_'+side,'foot_'+side,'ball_'+side))
    hems={}
    for cycle in cycles:
        if min(ps[i][1] for i in cycle)>=min(bones['calf_'+side]['head_m'][1] for side in ('l','r')):continue
        side=max(('l','r'),key=lambda side:math.fsum(owner(shell['weights'][i],side) for i in cycle))
        if side in hems or any(owner(shell['weights'][i],side)<.9 for i in cycle):raise ValueError('ambiguous source-owned hem cycle')
        ankle=bones['foot_'+side]['head_m'][1];knee=bones['calf_'+side]['head_m'][1]
        lo=min(ps[i][1] for i in cycle);hi=max(ps[i][1] for i in cycle)
        if not ankle<lo<=hi<ankle+.15*(knee-ankle) or hi-lo>.1*(knee-ankle):raise ValueError('hem correction exceeds source ankle band')
        hems[side]={'source_ankle_y_m':ankle,'existing_boundary_y_range_m':[lo,hi],'level_y_m':hi,'above_ankle_m':hi-ankle,'original_boundary_vertices':len(cycle)}
    if set(hems)!={'l','r'} or len(cycles)!=3:raise ValueError('hem trim requires exactly waist and two leg cycles')
    out={k:[] for k in ('positions_m','triangles','uvs','weights','source_basis','corner_uvs','source_triangle_indices')};cache={};maximum_drop=0.;cut_faces=0
    for face,uvs,source_face in zip(shell['triangles'],shell['corner_uvs'],shell['source_triangle_indices']):
        poly=[{'p':ps[i],'uv':uv,'n':[],'w':shell['weights'][i],'basis':shell['source_basis'][i]} for i,uv in zip(face,uvs)]
        if min(ps[i][1] for i in face)<max(v['level_y_m'] for v in hems.values()):
            side=max(('l','r'),key=lambda side:math.fsum(owner(shell['weights'][i],side) for i in face))
            if any(owner(shell['weights'][i],side)<.9 for i in face):raise ValueError('ambiguous source-owned ankle face')
            level=hems[side]['level_y_m'];poly=_clip(poly,lambda v:v['p'][1]-level);cut_faces+=1
            for v in poly:
                if abs(v['p'][1]-level)<=1e-12:v['p']=[v['p'][0],level,v['p'][2]]
        ids=[]
        for v in poly:
            weights=sorted(((k,w) for k,w in v['w'].items() if w>1e-12),key=lambda kv:(-kv[1],kv[0]));drop=math.fsum(w for k,w in weights[4:]);maximum_drop=max(maximum_drop,drop)
            if drop>.025:raise ValueError('hem cut exceeds 2.5 percent discarded skin mass')
            # Keep original lanes exact; only genuinely interpolated cut lanes
            # require truncation/normalization, following the existing guard.
            if len(weights)>4 or len(v['basis'])>1:
                weights=weights[:4];total=math.fsum(w for k,w in weights);mapping={k:w/total for k,w in weights}
            else:mapping=dict(v['w'])
            basis={k:w for k,w in v['basis'].items() if w>1e-12};key=(tuple(v['p']),tuple(sorted(mapping.items())))
            if key not in cache:
                cache[key]=len(out['positions_m']);out['positions_m'].append(list(v['p']));out['uvs'].append(list(v['uv']));out['weights'].append(mapping);out['source_basis'].append(basis)
            ids.append(cache[key])
        for k in range(1,len(ids)-1):
            tri=[ids[0],ids[k],ids[k+1]]
            a,b,c=[out['positions_m'][i] for i in tri];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            if len(set(tri))<3 or math.hypot(*cross)<=1e-18:continue
            out['triangles'].append(tri);out['corner_uvs'].append([poly[j]['uv'] for j in (0,k,k+1)]);out['source_triangle_indices'].append(source_face)
    out['receipt']=copy.deepcopy(shell['receipt']);out['receipt']['trouser_level_hem_v6']={'sides':hems,'touched_original_hem_faces':cut_faces,'maximum_discarded_cut_weight':maximum_drop,'engineering_basis':'Highest existing closed hem-cycle point, relative to actual source ankle; no historical dimension','scope':'Finite ankle-band source trim; separate actual V6 source-preview hem technical PASS. Canonical qualification, full fit,40 inherited idle negative projections and photographic acceptance remain OPEN. Prior whole-shoe disappearance was V2 stale preview-sphere culling, not a shoe-source defect; complete seated enclosure remains unaccepted'}
    return out
