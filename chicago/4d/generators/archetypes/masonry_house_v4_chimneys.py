"""T-2222: ridge-seated shafts, masonry cap courses and recessed flue mouths.

The independently sourced stack_finish attribute bounds this optional refinement.
Historic views establish the street stacks; later fabric bounds the service brick
and pale caps, reconstructed for 1904. Flue arrangements/depths are reconstructions.
Legacy versions retain their existing builder. No side vents or pots are invented.
"""
from __future__ import annotations


def outline(c):
    return [(c['x0'],c['y0']),(c['x1'],c['y0']),
            (c['x1'],c['y1']),(c['x0'],c['y1'])]


def shaft_faces(params,c,top):
    """Split the two crossing faces at the ridge; no chord through a gable roof."""
    from archetypes.masonry_house_v4_north_tower import chimney_foot
    seated=c['name'] in ('middle','south')
    e=next(r for r in params.ranges if r['name']=='east_wing')
    foot=lambda x: chimney_foot(params,x) if seated else c['z0']
    corners=outline(c)
    for a,z in zip(corners,corners[1:]+corners[:1]):
        stops=[a]
        if seated and min(a[0],z[0])<e['ridge_at']<max(a[0],z[0]):
            t=(e['ridge_at']-a[0])/(z[0]-a[0])
            stops.append((e['ridge_at'],a[1]+t*(z[1]-a[1])))
        stops.append(z)
        for p,q in zip(stops,stops[1:]):
            yield [(*p,foot(p[0])),(*q,foot(q[0])),(*q,top),(*p,top)]


def flue_holes(c,spec):
    nx,ny=spec['flues'];holes=[]
    for ix in range(nx):
        for iy in range(ny):
            x=c['x0']+(c['x1']-c['x0'])*(ix+.5)/nx
            y=c['y0']+(c['y1']-c['y0'])*(iy+.5)/ny
            hx=min(spec['flue_width_m']/2,(c['x1']-c['x0'])/nx*.28)
            hy=min(spec['flue_width_m']/2,(c['y1']-c['y0'])/ny*.28)
            holes.append([(x-hx,y-hy),(x+hx,y-hy),(x+hx,y+hy),(x-hx,y+hy)])
    return holes


def _band(b,c,lo,hi):
    """One shallow masonry course, with an explicit bed rather than a clipped row."""
    from archetypes import masonry_house_v4_detail as d
    conf=b.params.conf('stack_finish')
    old_schedule=b.course_schedule
    had_origin=hasattr(b,'course_origin');old_origin=getattr(b,'course_origin',None)
    try:
        b.course_schedule=[hi-lo];b.course_origin=lo
        corners=outline(c)
        for a,z in zip(corners,corners[1:]+corners[:1]):
            b.wall([(*a,lo),(*z,lo),(*z,hi),(*a,hi)],conf,d.GRANITE)
    finally:
        b.course_schedule=old_schedule
        if had_origin:b.course_origin=old_origin
        else:del b.course_origin


def _cap(b,c,spec,material):
    """Thick, flush, jointed masonry course; top joints meet its side joints."""
    from archetypes import masonry_house_v4_detail as d
    conf=b.params.conf('stack_finish')
    z=c['z1'];lo=z-spec['cap_height_m'];gap=spec['cap_joint_m']
    rise=lambda y:z-spec['fall_m']*(y-c['y0'])/(c['y1']-c['y0'])
    holes=flue_holes(c,spec)
    nx=max(1,round((c['x1']-c['x0'])/spec['cap_unit_m']))
    ny=max(1,round((c['y1']-c['y0'])/spec['cap_unit_m']))
    xs=[c['x0']+(c['x1']-c['x0'])*i/nx for i in range(nx+1)]
    ys=[c['y0']+(c['y1']-c['y0'])*i/ny for i in range(ny+1)]
    # Continuous recessed mortar closes the narrow joints, but not the flues.
    for frag in d.subtract(outline(c),holes):
        if getattr(b,'reduced_roof_details',False):
            # At Light distance the fine joints within the top bed are below
            # display resolution. Keep its exact outline, fall and open flues.
            b.raw([(x,y,rise(y)) for x,y in frag],conf,material,(0,0,1))
        else:
            b.raw([(x,y,rise(y)-.012) for x,y in frag],conf,d.MORTAR,(0,0,1))
    corners=outline(c)
    for a,q in zip(corners,corners[1:]+corners[:1]):
        n=d.norm((q[1]-a[1],a[0]-q[0],0))
        b.raw([(a[0]-.009*n[0],a[1]-.009*n[1],lo),
               (q[0]-.009*n[0],q[1]-.009*n[1],lo),
               (q[0]-.009*n[0],q[1]-.009*n[1],rise(q[1])),
               (a[0]-.009*n[0],a[1]-.009*n[1],rise(a[1]))],conf,d.MORTAR,n)
    # Each cap stone is dressed at its beds and sides. The existing metric
    # granite/limestone material carries its fine fabric, with no white lid.
    for ix,(xa,xb) in enumerate(zip(xs,xs[1:])):
        for iy,(ya,yb) in enumerate(zip(ys,ys[1:])):
            x0=xa+(gap/2 if ix else 0);x1=xb-(gap/2 if ix<nx-1 else 0)
            y0=ya+(gap/2 if iy else 0);y1=yb-(gap/2 if iy<ny-1 else 0)
            cell=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
            fragments=d.subtract(cell,holes)
            if not getattr(b,'reduced_roof_details',False):
                for frag in fragments:
                    b.raw([(x,y,rise(y)) for x,y in frag],conf,material,(0,0,1))
            # Cell sides close the actual joint; holes are lined independently.
            for a,q in zip(cell,cell[1:]+cell[:1]):
                outer=(abs(a[0]-q[0])<1e-9 and
                       any(abs(a[0]-x)<1e-9 for x in (c['x0'],c['x1']))) or (
                       abs(a[1]-q[1])<1e-9 and
                       any(abs(a[1]-y)<1e-9 for y in (c['y0'],c['y1'])))
                # Light keeps cap silhouette, side joints and all flue reveals.
                # The 8 mm internal joints read against their recessed mortar
                # bed without separately meshing each microscopic joint side.
                if getattr(b,'reduced_roof_details',False) and not outer:continue
                n=(q[1]-a[1],a[0]-q[0],0)
                # A flue can cross a cap cell's side. Split the side at each
                # crossing, retaining only the portions outside the aperture.
                dx,dy=q[0]-a[0],q[1]-a[1];ts={0.,1.}
                for h in holes:
                    for u,v in zip(h,h[1:]+h[:1]):
                        ex,ey=v[0]-u[0],v[1]-u[1];den=dx*ey-dy*ex
                        if abs(den)<1e-12:continue
                        t=((u[0]-a[0])*ey-(u[1]-a[1])*ex)/den
                        s=((u[0]-a[0])*dy-(u[1]-a[1])*dx)/den
                        if 0<t<1 and -1e-9<=s<=1+1e-9:ts.add(t)
                ts=sorted(ts)
                for t0,t1 in zip(ts,ts[1:]):
                    if t1-t0<1e-9:continue
                    mid=(t0+t1)/2;x=a[0]+dx*mid;y=a[1]+dy*mid
                    if any(d._inside(x,y,h) for h in holes):continue
                    p=(a[0]+dx*t0,a[1]+dy*t0);r=(a[0]+dx*t1,a[1]+dy*t1)
                    b.raw([(*p,lo+.004),(*r,lo+.004),(*r,rise(r[1])),(*p,rise(p[1]))],conf,material,n)
    # A deep brick-lined mouth replaces the old shallow iron-coloured patch.
    floor=z-spec['flue_depth_m']
    for h in holes:
        b.raw([(x,y,floor) for x,y in h],conf,18,(0,0,1))
        for a,q in zip(h,h[1:]+h[:1]):
            inward=(a[1]-q[1],q[0]-a[0],0)
            if getattr(b,'reduced_roof_details',False):
                # Same mouth/depth; a continuous soot-darkened masonry lining
                # avoids a subpixel material boundary inside each Light flue.
                b.raw([(*a,floor),(*q,floor),(*q,rise(q[1])),(*a,rise(a[1]))],conf,18,inward)
                continue
            split=max(floor,lo)
            if floor<split:
                b.raw([(*a,floor),(*q,floor),(*q,split),(*a,split)],conf,18,inward)
            b.raw([(*a,split),(*q,split),(*q,rise(q[1])),(*a,rise(a[1]))],conf,material,inward)
    return {'cap_base':lo,'cap_top':z,'holes':holes,'floor':floor,'nx':nx,'ny':ny}


def build_stack(b,c):
    from archetypes import masonry_house_v4_detail as d
    conf=max(c['conf'],b.params.conf('stack_finish'))
    cfg=b.params.detail['stack_finish'];service=c['name'] in cfg['service_stacks']
    spec={**cfg['common'],**cfg['service' if service else 'stone'],
          'flues':cfg['flues'][c['name']]}
    cap_base=c['z1']-spec['cap_height_m'];belt=0 if service else spec['belt_height_m']
    for face in shaft_faces(b.params,c,cap_base-belt):
        if service and getattr(b,'reduced_roof_details',False):
            # Retain the same shaft planes and metric brick albedo/normal map;
            # Light omits only these new stacks' 1–6 mm individual brick relief.
            b.raw(face,conf,d.BRICK)
        else:
            b.wall(face,conf,d.BRICK if service else d.GRANITE)
    if belt:_band(b,c,cap_base-belt,cap_base)
    receipt=_cap(b,c,spec,d.TRIM if service else d.GRANITE)
    if not hasattr(b,'stack_details'):b.stack_details=[]
    b.stack_details.append({'name':c['name'],'body_material':'brick' if service else 'granite',**receipt})
    # roof_edges.add_abutments already supplies the actual roof-following apron
    # on every stack. No second rectangular band is placed at the buried base.
