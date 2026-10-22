"""Prairie entrance section: HABS5 cutback and original doorway23A relief.

The later measured section establishes the relationship, not a 1904 depth
survey. Dimensions are bounded reconstructions in the structure record. This
module has no Blender dependency and does not texture-project reference images.
"""
from __future__ import annotations
import math


def settings(b):
    return b.params.detail.get('prairie_entry')


def batter(z, s):
    """Outward lower-wall slope; the cutback jamb faces stay vertical."""
    return s['batter_m'] * max(0.0, min(1.0, (s['batter_top_z']-z) /
                                           (s['batter_top_z']-s['grade_z'])))


def outline(s):
    c=s['centre_u'];a=s['recess_base_width_m']/2;t=s['recess_top_width_m']/2
    return [(c-a,s['sill_z']),(c+a,s['sill_z']),
            (c+t,s['batter_top_z']),(c-t,s['batter_top_z'])]


def lintel_outline(o, s):
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1']
    if not s:return [(a,z0),(c,z0),(c,z1),(a,z1)]
    shoulder=z1-s['lintel_crown_rise_m'];inset=s['lintel_end_inset_m']
    w=s.get('lintel_crown_width_m')
    if not w:
        return [(a+inset,z0),(c-inset,z0),(c,shoulder),((a+c)/2,z1),(a,shoulder)]
    # T-2972: sheet 5 draws the top flat to the shoulders and raised only under
    # the tympanum, a shallow segment of this chord and rise; the outline stays convex.
    m,h,rise=(a+c)/2,w/2,z1-shoulder
    r=(h*h+rise*rise)/(2*rise);zc=z1-r
    arc=[(m+r*math.sin(t),zc+r*math.cos(t)) for t in
         (math.asin(h/r)*(1-2*i/16) for i in range(17))]
    return [(a+inset,z0),(c-inset,z0),(c,shoulder)]+arc+[(a,shoulder)]


def relief_profile(s, cx, cz, radius, stilt=0.):
    """Continuous recessed section: outer fillet, hollow archivolt, deep field.

    A stilted arch (T-2853) keeps the section square across its plumb legs: in
    the band `stilt` below the centre the distance is the horizontal one.
    """
    knots=s['relief_section']
    def depth(u,z):
        r=(abs(u-cx) if cz-stilt-1e-9<=z<cz else math.hypot(u-cx,z-cz))/radius
        if r<=knots[0][0]:return knots[0][1]
        for (a,da),(c,dc) in zip(knots,knots[1:]):
            if r<=c:
                t=(r-a)/(c-a);t=t*t*(3-2*t)
                return da+(dc-da)*t
        return knots[-1][1]
    return depth


def front_offset(b,o,u,z):
    s=settings(b)
    if not s or o.get('axis')!='x' or o.get('sign')!=1 or abs(o['at']-b.params.width_m)>.001:
        return 0.
    poly=outline(s)
    inside=all((c[0]-a[0])*(z-a[1])-(c[1]-a[1])*(u-a[0])>=-1e-8
               for a,c in zip(poly,poly[1:]+poly[:1]))
    return 0. if inside else batter(z,s)


def wall_mapping(b,plain,n,d,mat):
    """Partition finished stone facets without changing their course or grain.

    The outer lower face slopes out; the doorway cutback keeps the original
    vertical plane. Cutting completed facets preserves bonds across the reveal.
    The returns follow each actual rough face, closing its freshly cut edge.
    """
    s=settings(b)
    if not s or mat!=0 or n[0]<.999 or abs(d-b.params.width_m)>.001:
        return plain
    from archetypes.masonry_house_v4_detail import clip,subtract,bounds,norm,sub
    portal=outline(s);px0,pz0,px1,pz1=bounds(portal)
    def outer(q,off=0):return plain(q,off+batter(q[1],s))
    horizontal=(-n[1],n[0],0)
    def normal(q):
        slope=(-s['batter_m']/(s['batter_top_z']-s['grade_z'])
               if s['grade_z']<q[1]<s['batter_top_z'] else 0.)
        return norm((horizontal[0]*q[3]+n[0]*q[5],
                     horizontal[1]*q[3]+n[1]*q[5],q[4]-slope*q[5]))
    outer.normal=normal
    outer.confidence=s['conf']
    def inset(q,off=0):return plain(q,off)
    inset.confidence=s['conf']
    if not hasattr(b,'entry_return_faces'):b.entry_return_faces=set()
    def bridge(poly,conf,material):
        # Bottom is owned by the single threshold; top converges to zero depth.
        for a,c in zip(poly,poly[1:]+poly[:1]):
            for v,w in ((portal[1],portal[2]),(portal[3],portal[0])):
                cross=lambda q:(w[0]-v[0])*(q[1]-v[1])-(w[1]-v[1])*(q[0]-v[0])
                if abs(cross(a))>1e-7 or abs(cross(c))>1e-7:continue
                if math.dist(a[:3],c[:3])<1e-7:continue
                pts=[plain(a[:2],a[2]),outer(a[:2],a[2]),outer(c[:2],c[2]),plain(c[:2],c[2])]
                clean=[]
                for p in pts:
                    if not clean or math.dist(p,clean[-1])>1e-8:clean.append(p)
                if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-8:clean.pop()
                if len(clean)<3:continue
                key=(material,tuple(sorted(tuple(round(v,8) for v in p)for p in clean)))
                if key in b.entry_return_faces:continue
                b.entry_return_faces.add(key)
                b.raw(clean,conf,material,(0,-(w[1]-v[1]),w[0]-v[0]))
    def partition(poly,conf,material):
        x0,z0,x1,z1=bounds(poly);zt=s['batter_top_z'];parts=[]
        if z0>=zt-1e-9:return [(poly,plain)]
        low=poly
        if z1>zt:
            low=clip(poly,(x1+1,zt),(x0-1,zt))
            high=clip(poly,(x0-1,zt),(x1+1,zt))
            if high:parts.append((high,plain))
        if not low:return parts
        if x1<px0 or x0>px1 or z1<pz0:
            return parts+[(low,outer)]
        inner=low
        for a,c in zip(portal,portal[1:]+portal[:1]):inner=clip(inner,a,c)
        if inner:
            parts.append((inner,inset));bridge(inner,max(conf,s['conf']),material)
        parts.extend((p,outer) for p in subtract(low,[portal]))
        return parts
    outer.partition=partition
    return outer


def end_returns(b,p):
    """Close the measured Prairie-face batter at its north/south corner returns."""
    s=p.detail.get('prairie_entry')
    if not s:return
    x=p.width_m;depth=batter(s['grade_z'],s)
    for y,want in ((0,(0,-1,0)),(p.depth_m,(0,1,0))):
        b.raw([(x,y,s['grade_z']),(x+depth,y,s['grade_z']),(x,y,s['batter_top_z'])],
              s['conf'],0,want)


def recessed_bed(r,cx,cz,inner,outer,s,reduced=False,stilt=0.):
    """One continuous backing following the hollow; no overlapping radial walls."""
    if stilt>0:
        # The plumb band under a stilted centre, strip by strip across the same
        # rings, so the hollow's section carries straight down to the spring.
        edges=sorted(set([-outer,outer]+[sign*v[0]*inner for v in s['relief_section'] for sign in (-1,1)
                                          if 0<v[0]*inner<outer]))
        steps=[e for a,c in zip(edges,edges[1:]) for e in (a+(c-a)*j/2 for j in range(2))]+[edges[-1]]
        for a,c in zip(steps,steps[1:]):
            r.face([(cx+a,cz-stilt,-.045),(cx+c,cz-stilt,-.045),(cx+c,cz,-.045),(cx+a,cz,-.045)])
    rings=[0.]
    knots=sorted(set([v[0]*inner for v in s['relief_section']]+[outer]))
    subdivisions=2 if reduced else 4
    for a,c in zip(knots,knots[1:]):
        count=1 if a==0 or c>inner else subdivisions
        rings.extend(a+(c-a)*j/count for j in range(1,count+1))
    count=24 if reduced else 64
    for j,(low,high) in enumerate(zip(rings,rings[1:])):
        for i in range(count):
            a,c=math.pi*i/count,math.pi*(i+1)/count
            poly=[(cx+low*math.cos(a),cz+low*math.sin(a),-.045),
                  (cx+high*math.cos(a),cz+high*math.sin(a),-.045),
                  (cx+high*math.cos(c),cz+high*math.sin(c),-.045)]
            if j:poly.append((cx+low*math.cos(c),cz+low*math.sin(c),-.045))
            r.face(poly)
