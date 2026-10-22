"""Reconstructed courtyard circulation; clip turf against actual occupied ground.

The source record owns path choices and grade bounds. Existing building and stair
parameters own exclusion masks. No photographic pixels or later parking plan are
used here. Full and Light share surfaces and contacts; only Full scatters blades.
"""
from __future__ import annotations
import copy
import math


def triangulate(poly):
    """Ear clip a simple XY outline; retain any extra vertex coordinates."""
    from archetypes.masonry_house_v4_detail import area
    poly=list(poly)
    if area(poly)<0:poly.reverse()
    result=[]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(poly)>3:
        for i,b in enumerate(poly):
            a,c=poly[i-1],poly[(i+1)%len(poly)]
            if cross(a,b,c)<=1e-10:continue
            if any(min(cross(a,b,p),cross(b,c,p),cross(c,a,p))>=-1e-10
                   for j,p in enumerate(poly) if j not in (i,(i-1)%len(poly),(i+1)%len(poly))):continue
            result.append([a,b,c]);poly.pop(i);break
        else:raise ValueError('Court outline cannot be triangulated')
    if len(poly)==3:result.append(poly)
    return result


def parts(poly):
    """Keep convex regions whole; split an orthogonal lawn only at its re-entrant corner."""
    from archetypes.masonry_house_v4_detail import area
    poly=list(poly)
    if area(poly)<0:poly.reverse()
    crosses=[(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
             for a,b,c in zip(poly,poly[1:]+poly[:1],poly[2:]+poly[:2])]
    if len(poly[0])==3 and len(poly)>3:
        from archetypes.masonry_house_v4_detail import sub,cross,dot
        n=cross(sub(poly[1],poly[0]),sub(poly[2],poly[0]))
        if any(abs(dot(n,sub(p,poly[0])))>1e-9 for p in poly[3:]):return triangulate(poly)
    if min(crosses)>=-1e-8:return [poly]
    if all(abs(a[0]-b[0])<1e-8 or abs(a[1]-b[1])<1e-8 for a,b in zip(poly,poly[1:]+poly[:1])):
        result=[];ys=sorted({p[1] for p in poly})
        for y0,y1 in zip(ys,ys[1:]):
            mid=(y0+y1)/2
            xs=sorted(a[0] for a,b in zip(poly,poly[1:]+poly[:1]) if min(a[1],b[1])<mid<max(a[1],b[1]))
            for x0,x1 in zip(xs[::2],xs[1::2]):
                result.append([(*p,*poly[0][2:]) for p in rectangle(x0,y0,x1,y1)])
        return result
    return triangulate(poly)


def rectangle(x0,y0,x1,y1):
    return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]


def occupied(params):
    """Solid court-level footprints, independent of the chosen path layout."""
    result=[list(b['pts']) for b in params.bays]
    for t in [*params.bows,*[t for t in params.towers if t['z0']<.1]]:
        result.append([(t['cx']+t['r']*math.cos(i*math.tau/16),
                        t['cy']+t['r']*math.sin(i*math.tau/16)) for i in range(16)])
    s=params.detail.get('north_court_service_stair')
    if s:
        x0,x1=s['flight_x'];y0,y1=s['flight_y']
        result.append(rectangle(x0-.025,y0-.025,x1+.025,y1))
        # The landing is elevated: exclude only its real support footprints.
        access=params.detail.get('service_access',{}).get('stair',{})
        x0,x1=s['landing_x'];y0,y1=s['landing_y']
        # Same two pier centres and stock used by the service builder.
        half=access['pier_cap_width_m']/2
        for x in (x1-.23,(x0+x1)/2):
            result.append(rectangle(x-half,y0+.19-half,x+half,y0+.19+half))
    t=params.detail.get('bow_terrace')
    if t and t.get('stair_boundaries'):
        a0,a1=t['arc'];r=t['r']
        arc=[(t['cx']+r*math.cos(a0+(a1-a0)*i/16),
              t['cy']+r*math.sin(a0+(a1-a0)*i/16)) for i in range(17)]
        result.append([(t['cx'],t['cy']),*arc])
        nx,ny=t['newel_xy'];nr=t['newel_r']
        result.append([(nx+nr*math.cos(i*math.tau/8),ny+nr*math.sin(i*math.tau/8)) for i in range(8)])
        edges=t['stair_boundaries']
        for a,b in zip(edges,edges[1:]):
            result.extend(parts([*a[-2:],*reversed(b)]))
    return result


def fall_quads(params):
    """T-2978: the court ground's fall to the passage mouth, as sheet 4 draws it.

    Each piece is a convex plan quad and the fall's depth (metres, <= 0) at its four
    corners, read as the triangles (0, 1, 2) and (0, 2, 3) the way passage-ground.js
    reads them. A bank from the lawn down to the mouth's level across S (sheet 4's
    drawn fall), full depth over the drive and the lawn beside it from the face to the
    section plane, then rising back to the court's level westward (reconstructed).
    The strip south of the drive keeps the court's level behind the drive's edge.
    [] when the record draws no fall.
    """
    spec=(params.detail.get('court_ground') or {}).get('mouth_fall')
    drive=next((g for g in params.ground if g['kind']=='drive'),None)
    if not spec or not drive or len(drive['pts'])!=4:return []
    x_face,x_low,x_end=spec['x'];y_top,y_low=spec['y'];d=-spec['depth_m']
    _,_,b1,m1=drive['pts']        # mouth north, far north, far south, mouth south
    def south(x):
        t=(m1[0]-x)/(m1[0]-b1[0]);return m1[1]+(b1[1]-m1[1])*t
    return [
        ([(x_face,y_top),(x_low,y_top),(x_low,y_low),(x_face,y_low)],[0.,0.,d,d]),
        ([(x_face,y_low),(x_low,y_low),(x_low,south(x_low)),(x_face,south(x_face))],[d]*4),
        ([(x_low,y_top),(x_end,y_top),(x_end,y_low),(x_low,y_low)],[0.,0.,0.,d]),
        ([(x_low,y_low),(x_end,y_low),(x_end,south(x_end)),(x_low,south(x_low))],[d,0.,0.,d]),
    ]


def fall_triangles(params):
    """The fall's quads as counter-clockwise (x, y, depth) triangles (no bpy needed:
    compile_scene and the renderer's declared pieces read these too)."""
    def area(t):return sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(t,t[1:]+t[:1]))/2
    result=[]
    for pts,zs in fall_quads(params):
        for i,j,k in ((0,1,2),(0,2,3)):
            tri=[(*pts[n],zs[n]) for n in (i,j,k)]
            if area(tri)<0:tri.reverse()
            result.append(tri)
    return result


def _weights(tri,x,y):
    (x0,y0,_),(x1,y1,_),(x2,y2,_)=tri
    den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    w0=((y1-y2)*(x-x2)+(x2-x1)*(y-y2))/den
    w1=((y2-y0)*(x-x2)+(x0-x2)*(y-y2))/den
    return w0,w1,1-w0-w1


def _plane(tri,x,y):
    w=_weights(tri,x,y);return sum(wi*t[2] for wi,t in zip(w,tri))


def _depth_in(tri,x,y):
    if min(_weights(tri,x,y))<-1e-9:return None
    return _plane(tri,x,y)


def fall_height(params,tris=None):
    """h(x, y): how far the court ground is sunk at a plan point (0 off the fall)."""
    tris=fall_triangles(params) if tris is None else tris
    def h(x,y):
        for tri in tris:
            z=_depth_in(tri,x,y)
            if z is not None:return z
        return 0.
    return h


def _sink(poly,tris):
    """Split a ground polygon by the fall's triangles; lower each piece by the fall."""
    from archetypes.masonry_house_v4_detail import clip,remove_hole
    out=[];rest=[poly]
    for tri in tris:
        nxt=[]
        for p in rest:
            inside=p
            for a,c in zip(tri,tri[1:]+tri[:1]):
                inside=clip(inside,a,c,True)
            if inside:
                out.append([(v[0],v[1],v[2]+_plane(tri,v[0],v[1])) for v in inside])
            nxt.extend(remove_hole(p,[t[:2] for t in tri]))
        rest=nxt
    return out+rest


def layout(params):
    """Return disjoint visible faces and physical masks for grass sampling."""
    from archetypes.masonry_house_v4_detail import subtract
    spec=params.detail.get('court_ground')
    if not spec:return None
    solids=occupied(params)
    hard=[]
    # T-2976: the carriage way's ramp up out of the sunk passage owns its ground first.
    from archetypes.masonry_house_v4_frontage import court_ramp
    ramp=court_ramp(params)
    if ramp:
        hard.append({'kind':'drive','id':'passage-ramp','pts':ramp['pts'],'lift_m':0,
                     'vertices':[(*xy,z) for xy,z in zip(ramp['pts'],ramp['z'])],'conf':spec['conf']})
    for g in params.ground:
        if g['kind']!='lawn':hard.append({**g,'id':'drive','vertices':[(x,y,g['lift_m']) for x,y in g['pts']]})
    for w in spec['walks']:
        # The west wall edge is gently raised; the outside edge stays on the
        # retained drive datum. The entry ramp ties both ends to the drive.
        pts=w['pts'];base=spec['path_lift_m']
        if w['id']=='west-service-approach':
            x0=min(p[0] for p in pts);x1=max(p[0] for p in pts)
            y0=min(p[1] for p in pts);y1=max(p[1] for p in pts)
            start=spec['wall_fall_start_y'];ramp=start+.5
            sets=[[(x0,y0,base),(x1,y0,base),(x1,start,base),(x0,start,base)],
                  [(x0,start,base),(x1,start,base),(x1,ramp,base),(x0,ramp,base+spec['wall_fall_m'])],
                  [(x0,ramp,base+spec['wall_fall_m']),(x1,ramp,base),(x1,y1,base),(x0,y1,base+spec['wall_fall_m'])]]
        else:sets=[[(x,y,base) for x,y in pts]]
        for i,vertices in enumerate(sets):
            hard.append({'kind':'path','id':w['id']+str(i),'pts':[p[:2] for p in vertices],
                         'vertices':vertices,'lift_m':base,'conf':spec['conf']})
    # Clip every hard region by earlier ones, retaining one owner per XY point.
    faces=[];accepted=[]
    for g in hard:
        for tri in parts(g['vertices']):
            for poly in subtract(tri,solids+accepted):
                faces.append({'kind':g['kind'],'id':g['id'],'points':poly,'conf':g['conf']})
        accepted.extend(parts(g['pts']))
    hard_masks=[q['pts'] for q in hard]
    for g in params.ground:
        if g['kind']!='lawn':continue
        for tri in parts([(x,y,spec['turf_lift_m']) for x,y in g['pts']]):
            for poly in subtract(tri,solids+accepted):
                faces.append({'kind':'lawn','id':'lawn','points':poly,'conf':g['conf']})
    # T-2978: the court ground falls to the passage mouth (sheet 4). The ramp out of
    # the passage already carries its own heights; every other surface sinks by it.
    tris=fall_triangles(params)
    if tris:
        sunk=[]
        for f in faces:
            if f['id']=='passage-ramp':sunk.append(f);continue
            sunk.extend({**f,'points':poly} for poly in _sink(f['points'],tris))
        faces=sunk
    # Rough footing relief projects beyond its base cylinder. Keep blades clear
    # without widening the ground cut and exposing a ring of bare terrain.
    # Inscribed floor cuts may extend a little beneath solid masonry. That is
    # invisible and avoids spending Light vertices on buried ground; blade masks
    # retain the true curves so simplification cannot grow grass through a wall.
    grass_only=[[(t['cx']+t['r']*math.cos(i*math.tau/64),
                  t['cy']+t['r']*math.sin(i*math.tau/64)) for i in range(64)] for t in params.bows]
    for t in params.towers:
        if t['name']=='stair':
            grass_only.append([(t['cx']+(t['r']+.05)*math.cos(i*math.tau/32),
                                t['cy']+(t['r']+.05)*math.sin(i*math.tau/32)) for i in range(32)])
    return {'faces':faces,'hard':hard,'solids':solids,'grass_masks':hard_masks+solids+grass_only,
            'fall':tris}


def _edge_parts(a,b,polygons):
    """Split an outline edge wherever another physical surface crosses it."""
    ts={0.,1.};dx,dy=b[0]-a[0],b[1]-a[1]
    for poly in polygons:
        for c,d in zip(poly,poly[1:]+poly[:1]):
            ex,ey=d[0]-c[0],d[1]-c[1];den=dx*ey-dy*ex
            if abs(den)<1e-12:continue
            cx,cy=c[0]-a[0],c[1]-a[1]
            t=(cx*ey-cy*ex)/den;u=(cx*dy-cy*dx)/den
            if 1e-8<t<1-1e-8 and -1e-8<=u<=1+1e-8:ts.add(t)
    ts=sorted(ts)
    for t,u in zip(ts,ts[1:]):
        yield tuple(a[k]+t*(b[k]-a[k]) for k in range(3)),tuple(a[k]+u*(b[k]-a[k]) for k in range(3))


def _footing(b,params,fall):
    """T-2978: where the fall sinks the ground at the east wing's court face, between
    the stair tower and the passage mouth, the wall's rough stone footing runs down to
    it (the tower's own footing does the same, masonry_house_v4_foundation)."""
    from archetypes.masonry_house_v4_foundation import ROUGH_STONE
    spec=params.detail['court_ground']['mouth_fall']
    ys=spec.get('footing_y') or []
    if len(ys)!=2:return
    x=spec['x'][0]-.012;y0,y1=ys;n=6
    conf=params.detail['court_ground']['conf']
    for i in range(n):
        a=y0+(y1-y0)*i/n;c=y0+(y1-y0)*(i+1)/n
        za,zc=fall(x-.05,a)-.03,fall(x-.05,c)-.03
        if za>-.03+1e-6 and zc>-.03+1e-6:continue
        b.raw([(x,c,zc),(x,a,za),(x,a,.02),(x,c,.02)],conf,ROUGH_STONE,(-1,0,0))


def build(b,params):
    """Emit shared ground; return a shallow parameter copy for blade sampling."""
    from archetypes import masonry_house as legacy
    from archetypes.masonry_house_v4_detail import LAWN,DRIVE,TRIM,area
    from archetypes.masonry_house_v4_landscape import _inside
    data=layout(params)
    if data is None:
        for g in params.ground:legacy._ground(b,g)
        return params
    for f in data['faces']:
        b.raw(f['points'],f['conf'],LAWN if f['kind']=='lawn' else DRIVE,(0,0,1))
    # Close the gravel edge down into grade only where it borders lawn. Internal
    # triangulation and path joins never acquire doubled vertical skirt faces.
    lawns=[g['pts'] for g in params.ground if g['kind']=='lawn']
    masks=[g['pts'] for g in data['hard']]+data['solids']
    fall=fall_height(params,data['fall']);fall_on=bool(data['fall'])
    lawn_lift=params.detail['court_ground']['turf_lift_m']
    for g in data['hard']:
        if g['id']=='passage-ramp':
            # Sunk below the court: a stone retaining edge up to the drive along both sides.
            from archetypes.masonry_house_v4_frontage import _edge
            v=g['vertices'];mid=tuple(sum(p[k] for p in v)/4 for k in range(2))
            for a,c in ((v[0],v[1]),(v[3],v[2])):
                # T-2978: each side retains up to the ground beside it, which the fall
                # has sunk on the lawn side but not on the strip behind the drive's edge.
                out=((a[0]+c[0])/2-mid[0],(a[1]+c[1])/2-mid[1]);k=.05/max(math.hypot(*out),1e-9)
                side=fall((a[0]+c[0])/2+out[0]*k,(a[1]+c[1])/2+out[1]*k)
                top=max(v[1][2],side+lawn_lift) if fall_on else v[1][2]
                _edge(b,a[:2],c[:2],a[2],c[2],mid,g['conf'],DRIVE,top=top)
            continue
        pts=g['vertices']
        if area(pts)<0:pts=list(reversed(pts))
        for a,c in zip(pts,pts[1:]+pts[:1]):
            for p,q in _edge_parts(a,c,masks+lawns+[t[:3] for t in data['fall']]):
                length=math.dist(p[:2],q[:2])
                if length<1e-7:continue
                n=((q[1]-p[1])/length,-(q[0]-p[0])/length)
                mid=((p[0]+q[0])/2+n[0]*1e-5,(p[1]+q[1])/2+n[1]*1e-5)
                if not any(_inside(mid,l) for l in lawns) or any(_inside(mid,m) for m in masks):continue
                # T-2978: the surface and the ground beside it both follow the fall; where
                # the drive is sunk below the strip behind its edge the skirt retains it.
                inner=((p[0]+q[0])/2-n[0]*1e-3,(p[1]+q[1])/2-n[1]*1e-3)
                outer=((p[0]+q[0])/2+n[0]*1e-3,(p[1]+q[1])/2+n[1]*1e-3)
                t0,t1=fall(*inner),fall(*outer)
                if abs(t0)<1e-9 and abs(t1)<1e-9:
                    b.raw([(p[0],p[1],0),(q[0],q[1],0),q,p],g['conf'],DRIVE,(*n,0))
                    continue
                def lo(r):return fall(r[0]+n[0]*1e-3,r[1]+n[1]*1e-3)
                def hi(r):return r[2]+fall(r[0]-n[0]*1e-3,r[1]-n[1]*1e-3)
                pb,qb,pt,qt=(p[0],p[1],lo(p)),(q[0],q[1],lo(q)),(p[0],p[1],hi(p)),(q[0],q[1],hi(q))
                if (pb[2]+qb[2])/2<=(pt[2]+qt[2])/2:
                    b.raw([pb,qb,qt,pt],g['conf'],DRIVE,(*n,0))
                else:
                    b.raw([pt,qt,qb,pb],g['conf'],TRIM,(-n[0],-n[1],0))
    if fall_on:
        _footing(b,params,fall)
    sample=copy.copy(params)
    sample.court_fall=fall if fall_on else None
    sample.ground=[g for g in params.ground if g['kind']=='lawn']+[
        {'kind':'occupied','pts':p} for p in data['grass_masks']]
    b.court_ground_faces=len(data['faces'])
    return sample
