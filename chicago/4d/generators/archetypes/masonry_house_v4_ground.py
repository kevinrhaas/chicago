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
            result.extend(parts([a[0],a[1],b[1],b[0]]))
    return result


def layout(params):
    """Return disjoint visible faces and physical masks for grass sampling."""
    from archetypes.masonry_house_v4_detail import subtract
    spec=params.detail.get('court_ground')
    if not spec:return None
    solids=occupied(params)
    hard=[]
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
    return {'faces':faces,'hard':hard,'solids':solids,'grass_masks':hard_masks+solids+grass_only}


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


def build(b,params):
    """Emit shared ground; return a shallow parameter copy for blade sampling."""
    from archetypes import masonry_house as legacy
    from archetypes.masonry_house_v4_detail import LAWN,DRIVE,area
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
    for g in data['hard']:
        pts=g['vertices']
        if area(pts)<0:pts=list(reversed(pts))
        for a,c in zip(pts,pts[1:]+pts[:1]):
            for p,q in _edge_parts(a,c,masks+lawns):
                length=math.dist(p[:2],q[:2])
                if length<1e-7:continue
                n=((q[1]-p[1])/length,-(q[0]-p[0])/length)
                mid=((p[0]+q[0])/2+n[0]*1e-5,(p[1]+q[1])/2+n[1]*1e-5)
                if not any(_inside(mid,l) for l in lawns) or any(_inside(mid,m) for m in masks):continue
                b.raw([(p[0],p[1],0),(q[0],q[1],0),q,p],g['conf'],DRIVE,(*n,0))
    sample=copy.copy(params)
    sample.ground=[g for g in params.ground if g['kind']=='lawn']+[
        {'kind':'occupied','pts':p} for p in data['grass_masks']]
    b.court_ground_faces=len(data['faces'])
    return sample
