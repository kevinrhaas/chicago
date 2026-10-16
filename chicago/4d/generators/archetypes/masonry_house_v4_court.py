"""Shared courtyard aperture stock and concealed Light wall trimming.

Source dimensions and opt-ins belong to the structure record. The trimming
removes only drum faces inside the closed part of the east-wing envelope.
"""
import math


def half_plane(points, axis, at, sign):
    """Clip a convex 3-D face, retaining sign*(coordinate-at) >= 0."""
    out=[]
    for p,q in zip(points,points[1:]+points[:1]):
        a=sign*(p[axis]-at);c=sign*(q[axis]-at)
        if a>=0:out.append(p)
        if (a>0 and c<0) or (a<0 and c>0):
            t=a/(a-c);out.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(3)))
    clean=[]
    for p in out:
        if not clean or math.dist(p,clean[-1])>1e-9:clean.append(p)
    if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-9:clean.pop()
    if len(clean)<3:return []
    area=[0.,0.,0.]
    for p,q in zip(clean,clean[1:]+clean[:1]):
        for k in range(3):area[k]+=p[(k+1)%3]*q[(k+2)%3]-p[(k+2)%3]*q[(k+1)%3]
    return clean if math.sqrt(sum(v*v for v in area))>1e-10 else []


def outside_box(points, box):
    """Disjoint convex fragments outside an axis-aligned opaque volume."""
    remaining=points;out=[]
    for axis,(lo,hi) in enumerate(box):
        for at,sign in ((lo,1),(hi,-1)):
            if not remaining:return out
            values=[sign*(p[axis]-at) for p in remaining]
            if max(values)<=1e-10:
                out.append(remaining)
                return out
            if min(values)>=0:continue
            part=half_plane(remaining,axis,at,-sign)
            if part:out.append(part)
            remaining=half_plane(remaining,axis,at,sign)
    return out


def concealed_stair_box(params,tower):
    """Conservative inset below both eaves; refuse a pierced adjoining wall."""
    e=next(r for r in params.ranges if r['name']=='east_wing')
    low=tower['cy']-tower['r'];high=tower['cy']+tower['r']
    top=min(e['eave_lo_z'],e['eave_hi_z'])-.04
    if not e['y0']<low<high<e['y1']:return None
    for o in params.openings:
        if o['axis']=='x' and abs(o['at']-e['x0'])<.01 and o['z0']<top and o['z1']>tower['z0']:
            if o['u0']<high and o['u1']>low:
                if o['u0']>tower['cy']:high=min(high,o['u0']-.04)
                elif o['u1']<tower['cy']:low=max(low,o['u1']+.04)
                else:return None
    if low>=high:return None
    return [(e['x0']+.04,e['x1']-.04),(low,high),
            (max(0.,tower['z0'])+.04,top)]


def garden_light(b,o,spec):
    """The broad barred basement light beside the stair tower, HABS sheet 4."""
    from archetypes.masonry_house_v4_detail import slab,cylinder,legacy,TRIM,DARK_GLASS,PAINTED_WOOD,IRON
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];conf=o['conf'];f=spec['frame_m']
    slab(b,o,a+f,c-f,z0+f,z1-f,-.31,-.30,conf,DARK_GLASS)
    for lo,hi,bottom,top in ((a,a+f,z0,z1),(c-f,c,z0,z1),
                             (a,c,z0,z0+f),(a,c,z1-f,z1)):
        slab(b,o,lo,hi,bottom,top,-.29,-.24,conf,PAINTED_WOOD)
    slab(b,o,a-.04,c+.04,z1,z1+spec['head_m'],-.02,.08,conf,TRIM)
    slab(b,o,a-.04,c+.04,z0-spec['sill_m'],z0,-.02,.08,conf,TRIM)
    count=spec['bars'];segments=4 if getattr(b,'reduced_sash',False) else 6
    for i in range(1,count+1):
        x,y,_=legacy._plane_point(o,a+(c-a)*i/(count+1),0,-.08)
        cylinder(b,x,y,z0+f,z1-f,spec['bar_radius_m'],1.,IRON,segments)
    for fraction in spec['rail_fractions']:
        z=z0+(z1-z0)*fraction
        slab(b,o,a+f,c-f,z-.009,z+.009,-.098,-.077,1.,IRON)


def roof_height(params,x):
    e=next(r for r in params.ranges if r['name']=='east_wing')
    return e['eave_lo_z']+(x-e['x0'])*(e['ridge_z']-e['eave_lo_z'])/(e['ridge_at']-e['x0'])


def dormer_roof(d):
    f,bk=d['front'],d['back'];a,c=sorted((d['u0'],d['u1']));ze=d['eave_z']
    xa,xb=sorted((f,bk));xa,xb=(xa-.30,xb+.10) if bk>f else (xa-.10,xb+.30)
    overhang=d.get('side_overhang_m',.26)
    upper_overhang=overhang-d.get('side_apron_inset_m',.18)
    ring=[(xa,a-overhang,ze),(xb,a-overhang,ze),(xb,c+overhang,ze),(xa,c+overhang,ze)]
    kick=[(xa+.18,a-upper_overhang,ze+.13),(xb-.18,a-upper_overhang,ze+.13),
          (xb-.18,c+upper_overhang,ze+.13),(xa+.18,c+upper_overhang,ze+.13)]
    apex=((f+bk)/2,(a+c)/2,d['apex_z'])
    patches=[]
    for i in range(4):
        j=(i+1)%4
        patches.extend([[ring[i],ring[j],kick[j],kick[i]],[kick[i],kick[j],apex]])
    return ring,kick,apex,patches


def above_host(points,params):
    from archetypes.masonry_house_v4_north_tower import _half
    return _half(points,lambda p:p[2]-roof_height(params,p[0]))


def dormer_host(points,params):
    """Cut the union of enclosed dormer volumes, only BELOW each roof patch.

    Keeping the roof under the projecting overhang closes its soffit junction;
    keeping it behind the exact valley prevents rectangular uphill holes.
    """
    from archetypes.masonry_house_v4_detail import subtract,area
    from archetypes.masonry_house import _normal
    from archetypes.masonry_house_v4_north_tower import _half
    n=_normal(points);origin=points[0]
    def height(p):return origin[2]-(n[0]*(p[0]-origin[0])+n[1]*(p[1]-origin[1]))/n[2]
    holes=[]
    for d in params.dormers:
        for poly in dormer_roof(d)[3]:
            for axis,lo,hi in ((0,*sorted((d['front'],d['back']))),(1,d['u0'],d['u1'])):
                poly=half_plane(poly,axis,lo,1)
                if poly:poly=half_plane(poly,axis,hi,-1)
                if not poly:break
            if poly:poly=_half(poly,lambda p:p[2]-height(p))
            if poly and abs(area(poly))>1e-10:holes.append(poly)
    return subtract(points,holes)


def court_finial(b,x,y,kind,material):
    """Closed revolved bell silhouette; only courtyard components opt in."""
    spec=b.params.detail['court_finial'];base=spec[kind+'_base_ft']*.3048
    profile=[(base+z*.3048,r*.3048) for z,r in spec['profile_ft']]
    count=12 if getattr(b,'reduced_sash',False) else 24
    for i in range(count):
        a,c=[2*math.pi*j/count for j in (i,i+1)]
        def P(z,r,angle):return (x+r*math.cos(angle),y+r*math.sin(angle),z)
        for (z,r),(zz,rr) in zip(profile,profile[1:]):
            pts=[P(z,r,a),P(z,r,c),P(zz,rr,c)]
            if rr:pts.append(P(zz,rr,a))
            b.raw(pts,1.,material)
    z,r=profile[0]
    b.raw([P(z,r,2*math.pi*i/count) for i in reversed(range(count))],1.,material,(0,0,-1))
