"""T-2470: the north tower's photographic bellcast eave and roof-seated drum.

All dimensional choices live in the record. HABS 01/14 show the flared skirt
and short pipe; the fitted dimensions remain bounded reconstruction (L295).
The host north-range slope is retained, including beneath the drum.
"""
from __future__ import annotations
import math


def _east(params):
    return next(r for r in params.ranges if r['name']=='east_wing')


def chimney_foot(params,x):
    """Buried foot of a shaft on the reconciled east-facing main roof pitch."""
    e=_east(params)
    return e['eave_hi_z']+(e['x1']-x)*(e['ridge_z']-e['eave_hi_z'])/(e['x1']-e['ridge_at'])-.06


def _join_x(params,z,y=None):
    e=_east(params)
    original=e['x0']+(z-e['eave_lo_z'])*(e['ridge_at']-e['x0'])/(e['ridge_z']-e['eave_lo_z'])
    if y is None or not e.get('north_roof_shoulder'):return original
    g=e['north_roof_shoulder'];west=g['x']
    front=west+(e['y1']-y)*(e['x0']-west)/(e['y1']-g['back_y'])
    front+=(z-e['eave_lo_z'])*(e['ridge_at']-west)/(e['ridge_z']-e['eave_lo_z'])
    join=min(original,front)
    if y>=e['y1']-.08:
        # The north coping is in front of the roof. Its sloping face remains
        # visible; a connector must not project across it as a horizontal shelf.
        lift=e['parapet_m'].get('north',0)
        facade=west+(z-lift-e['eave_lo_z'])*(e['ridge_at']-west)/(e['ridge_z']-e['eave_lo_z'])
        join=min(join,facade-.08)
    return join


def clip_host(points,params,source='north_range'):
    """Remove the host only where the raised facade encloses it below its eave.

    The uphill roof above the eave stays intact. Cutting an entire circular
    footprint here would leave a hole behind the tower.
    """
    from archetypes.masonry_house_v4_detail import clip,subtract
    t=next(t for t in params.towers if t['name']=='north');e=_east(params)
    cx,cy,r=t['cx'],t['cy'],t['r']-.025
    right=e['ridge_at'] if source=='east_wing' else e['x1']
    # Two convex cuts form the footprint's union. Taking their convex hull
    # would overcut the round wall near its tangent and leave a roof gap.
    cut=[(cx+r*math.cos(math.pi/2+math.pi*i/12),
          cy+r*math.sin(math.pi/2+math.pi*i/12)) for i in range(13)]
    rectangle=[(cx,cy-t['r']-.21),(right,cy-t['r']-.21),
               (right,cy+t['r']+.21),(cx,cy+t['r']+.21)]
    def height_half(poly,above):
        result=[]
        for a,c in zip(poly,poly[1:]+poly[:1]):
            da=(a[2]-t['wall_top_z'])*(1 if above else -1)
            dc=(c[2]-t['wall_top_z'])*(1 if above else -1)
            if da>=0:result.append(a)
            if (da>=0)!=(dc>=0):
                f=da/(da-dc);result.append(tuple(a[k]+f*(c[k]-a[k]) for k in range(3)))
        return result if len(result)>=3 else []
    high=height_half(points,True);low=height_half(points,False)
    return ([high] if high else [])+subtract(low,[rectangle,cut])


def facade(b,t,params):
    """The street plane continues to the north tangent of the west half drum."""
    from archetypes import masonry_house as legacy
    e=_east(params);z=t['wall_top_z'];lift=e['parapet_m'].get('north',0)
    pl={'axis':'y','sign':1,'at':e['y1']}
    # The gable coping disappears into the cone connector at the shoulder.
    west=e['north_roof_shoulder']['x']
    join=west+(z-lift-e['eave_lo_z'])*(e['ridge_at']-west)/(e['ridge_z']-e['eave_lo_z'])
    profile=[(t['cx'],z),(join,z),(e['ridge_at'],e['ridge_z']+lift),
             (e['x1'],e['eave_hi_z']+lift)]
    stack=e['stacks']['north'];a,c,base=stack
    low=legacy._crossed(profile,base)
    legacy._profile_wall(b,pl,[(u,min(v,base)) for u,v in low],[(t['cx'],e['x1'])],t['conf_wall'],0)
    for lo,hi in ((t['cx'],a),(c,e['x1'])):
        run=[(lo,legacy._at(profile,lo))]+[q for q in legacy._crossed(profile,base) if lo<q[0]<hi]+[(hi,legacy._at(profile,hi))]
        top=[q for q in legacy._crossed(run,base) if q[1]>=base-1e-9]
        if len(top)>1:
            foot=[(u,base) for u,v in (top[0],top[-1]) if v>base+1e-9]
            legacy._poly_facing(b,[legacy._plane_point(pl,u,v) for u,v in foot+top[::-1]],t['conf_wall'],0,(0,1,0))
    coping=[(join,z-lift),(e['ridge_at'],e['ridge_z']),(e['x1'],e['eave_hi_z'])]
    for piece in legacy._stack_cut(b,pl,coping,lift,stack,t['conf_wall'],0):
        legacy._parapet(b,pl,piece,lift,t['conf_wall'],0)
    from archetypes.masonry_house_v4_ornament import Relief,_shaft
    ops=sorted([o for o in params.openings if o.get('style')=='north_gable_pair'],key=lambda o:o['u0'])
    for a,c in zip(ops,ops[1:]):
        gap=c['u0']-a['u1']
        if not .1<gap<.65:continue
        u=(a['u1']+c['u0'])/2;lo,hi=a['z0'],a['z1'];rr=Relief(b,a,t['conf_wall'])
        # HABS13 shows the round central shaft and a square foliate capital.
        # Stock/profile are bounded reconstructions; no Prairie-entry carving
        # is borrowed as if it were this capital's measured pattern.
        _shaft(rr,u,lo+.06,hi-.23,gap*.60)
        rr.box(u-gap*.47,u+gap*.47,lo,lo+.075,-.10,.12)
        rr.box(u-gap*.49,u+gap*.49,hi-.23,hi-.035,-.10,.16)
        for j in range(3):
            rr.leaf(u+(j-1)*gap*.26,hi-.22,math.pi/2,.17,gap*.25,.16,.025,0,False,steps=5)


def _half(poly, distance):
    """Clip a polygon and all its interpolated attributes in any 3-D plane."""
    out=[]
    for a,c in zip(poly,poly[1:]+poly[:1]):
        da,dc=distance(a),distance(c)
        if da>=-1e-9:out.append(a)
        if (da>=-1e-9)!=(dc>=-1e-9):
            f=da/(da-dc)
            out.append(tuple(a[k]+f*(c[k]-a[k]) for k in range(len(a))))
    return out if len(out)>=3 else []


def wrapped_stone(b,t,params):
    """Lay complete staggered courses once, then bend their finished surfaces.

    Angular tessellation is inside each stone, never a new masonry boundary.
    Both tiers use their normal adjacent-wall block finish and course schedule.
    """
    from archetypes.masonry_house_v4_courtyard_roof import north_height
    from archetypes.masonry_house_v4_detail import norm
    cx,cy,r,z=t['cx'],t['cy'],t['r'],t['wall_top_z']
    length=math.pi*r
    flat=type(b)('north_tower_unwrapped',params)
    flat.openings=[]
    bottom=max(t['z0'],north_height(params,cy+r)-.06)
    flat.wall([(0,0,bottom),(0,0,z),(length,0,z),(length,0,bottom)],t['conf_wall'],0)
    step=length/(12 if getattr(b,'reduced_roof_details',False) else 36)
    for face,mat in zip(flat.faces,flat.mat_index):
        normal_map=(flat.pillow_normals if hasattr(flat,'pillow_normals') else flat.rock_normals)
        smooth=all(i in normal_map for i in face)
        # Preserve continuous metric grain coordinates and the face's original
        # corner normals through both angular and host-roof cuts.
        poly=[(*flat.verts[i],*normal_map.get(i,(0,1,0)),
               *flat.roof_uvs.get(i,(-flat.verts[i][0],flat.verts[i][2]))) for i in face]
        lo,hi=min(q[0] for q in poly),max(q[0] for q in poly)
        for j in range(math.floor(lo/step),max(math.floor(lo/step)+1,math.ceil(hi/step))):
            part=_half(_half(poly,lambda q:q[0]-j*step),lambda q:(j+1)*step-q[0])
            mapped=[]
            for u,depth,height,nx,ny,nz,tu,tv in part:
                a=math.pi/2+u/r;co,si=math.cos(a),math.sin(a)
                mapped.append((cx+(r+depth)*co,cy+(r+depth)*si,height,
                               -nx*si+ny*co,nx*co+ny*si,nz,tu,tv))
            mapped=_half(mapped,lambda q:q[2]-north_height(params,q[1])+.03)
            if len(mapped)<3:continue
            mapped.reverse() # Bending x into angle reverses the planar frame.
            indices=b.raw([q[:3] for q in mapped],t['conf_wall'],mat)
            for i,q in zip(indices,mapped):
                b.roof_uvs[i]=q[6:8]
                if smooth:
                    target=b.pillow_normals if hasattr(b,'pillow_normals') else b.rock_normals
                    target[i]=norm(q[3:6])
    b.masonry_blocks+=flat.masonry_blocks


def build(b,t,params):
    from archetypes import masonry_house as legacy
    from archetypes.masonry_house_v4_courtyard_roof import north_height
    from archetypes.masonry_house_v4_rainwater import _tube
    s=params.detail['north_tower_roof']
    n=32 if getattr(b,'reduced_roof_details',False) else 48
    cx,cy,r,z=t['cx'],t['cy'],t['r'],t['wall_top_z']
    integrated=s.get('integrated_north_facade')
    if integrated:
        facade(b,t,params)
        # Only the west half turns away from the flat north facade. The former
        # complete cylinder exposed a curved north-east quadrant that is absent
        # in HABS 01/13/14.
        wrapped_stone(b,t,params)
    else:
        legacy._drum(b,cx,cy,r,t['z0'],z,t['conf_wall'],legacy.WALL_MAT[t['wall']],n)
        legacy._drum(b,cx,cy,r+.04,z-.12,z,t['conf_wall'],legacy.TRIM,n)
    # Concentric rings share exactly the same angular samples. The upper
    # cone and the gently flattening skirt therefore meet without cracks.
    profile=[(t['eave_r']-dr*.3048,z+dz*.3048) for dr,dz in s['flare_profile_ft']]
    rr,zz=profile[-1]
    if integrated:
        # A half-cone with its eastern slopes continuing into the main roof:
        # the flat wall is enclosed by this roof, not a free-standing screen.
        profile.append((0,t['apex_z']))
    else:
        legacy._cone(b,cx,cy,rr,zz,t['apex_z'],t['conf_roof'],legacy.ROOF,n)
    for (ra,za),(rb,zb) in zip(profile,profile[1:]):
        for i in range(n//2 if integrated else n):
            a,c=(math.pi/2 if integrated else 0)+2*math.pi*i/n,(math.pi/2 if integrated else 0)+2*math.pi*(i+1)/n
            pts=[(cx+ra*math.cos(a),cy+ra*math.sin(a),za),
                          (cx+ra*math.cos(c),cy+ra*math.sin(c),za),
                          (cx+rb*math.cos(c),cy+rb*math.sin(c),zb),
                          (cx+rb*math.cos(a),cy+rb*math.sin(a),zb)]
            legacy._up(b,pts[:3] if rb==0 else pts,t['conf_roof'],legacy.ROOF)
        if integrated:
            for sign in (-1,1):
                legacy._up(b,[(cx,cy+sign*ra,za),(_join_x(params,za,cy+sign*ra),cy+sign*ra,za),
                    (_join_x(params,zb,cy+sign*rb),cy+sign*rb,zb),(cx,cy+sign*rb,zb)],t['conf_roof'],legacy.ROOF)
    # A dark, closed 35 mm eave edge and soffit, tied to the new eave datum.
    er=t['eave_r'];depth=s['edge_depth_m']
    for i in range(n//2 if integrated else n):
        a,c=(math.pi/2 if integrated else 0)+2*math.pi*i/n,(math.pi/2 if integrated else 0)+2*math.pi*(i+1)/n
        p=(cx+er*math.cos(a),cy+er*math.sin(a),z)
        q=(cx+er*math.cos(c),cy+er*math.sin(c),z)
        lowp=(*p[:2],z-depth);lowq=(*q[:2],z-depth)
        mid=(a+c)/2
        b.raw([p,q,lowq,lowp],t['conf_roof'],10,(math.cos(mid),math.sin(mid),0))
        b.raw([lowp,lowq,(cx+r*math.cos(c),cy+r*math.sin(c),z-depth),
               (cx+r*math.cos(a),cy+r*math.sin(a),z-depth)],t['conf_roof'],10,(0,0,-1))
    if integrated:
        for sign in (-1,1):
            a=(cx,cy+sign*er,z);c=(_join_x(params,z,cy+sign*er),cy+sign*er,z)
            b.raw([a,c,(*c[:2],z-depth),(*a[:2],z-depth)],t['conf_roof'],10,(0,sign,0))
            b.raw([(*a[:2],z-depth),(*c[:2],z-depth),(_join_x(params,z,cy+sign*r),cy+sign*r,z-depth),
                (cx,cy+sign*r,z-depth)],t['conf_roof'],10,(0,0,-1))
    legacy._finial(b,cx,cy,t['apex_z'],t['finial_m'],t['conf_roof'],legacy.COPPER)
    # Archived versions retain the earlier roof-discharge interpretation.
    # T-2221's network replaces it with the photographed upper-pipe/bowl/
    # lower-leader connection, and fills this diagnostic with its emitted path.
    a=math.radians(s['pipe_angle_deg']);ux,uy=math.cos(a),math.sin(a)
    px,py=cx+(r+.08)*ux,cy+(r+.08)*uy
    ox,oy=px+.10*ux,py+.10*uy
    end=north_height(params,oy)+.04
    inlet=(cx+er*ux,cy+er*uy,z-depth)
    path=[inlet,(px,py,z-.28),(px,py,end+.12),(ox,oy,end)]
    if end+.24>=z-.28:raise ValueError('North tower pipe no longer clears its host roof')
    if not params.detail.get('rainwater'):
        _tube(b,path,s['pipe_radius_m'],6 if n==32 else 12)
    if not hasattr(b,'north_tower_details'):b.north_tower_details=[]
    b.north_tower_details.append({'eave_z':z,'profile':profile,
                                 'pipe':[] if params.detail.get('rainwater') else path,
                                 'host_roof_z':north_height(params,oy),'segments':n})
