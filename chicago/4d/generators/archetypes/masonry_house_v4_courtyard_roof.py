"""T-2016 courtyard roof junctions, in the shared engine-neutral metric frame."""
from __future__ import annotations


def north(params):
    return next(r for r in params.ranges if r['name']=='north_range')


def north_height(params,y):
    n=north(params)
    a,za=(n['y0'],n['eave_lo_z']) if y<=n['ridge_at'] else (n['y1'],n['eave_hi_z'])
    return za+(n['ridge_z']-za)*(y-a)/(n['ridge_at']-a)


def dining(params):
    """Two tiled valley returns, each split into exact planar triangles."""
    y=params.bays[0];n=north(params);ap=tuple(y['apex']);z=y['band_top_z']
    left,right=sorted((tuple(y['pts'][0]),tuple(y['pts'][-1])))
    spread=.24
    triangles=[]
    for pt,sign in ((left,-1),(right,1)):
        bottom=(*pt,z);ox=pt[0]+sign*spread
        upper=(ox,ap[1],ap[2]);eave=(ox,n['y0'],n['eave_lo_z'])
        triangles.extend([(ap,upper,bottom),(upper,eave,bottom)])
        # Continue the two returns over the same 20 cm eave as their host;
        # otherwise a remnant of the uncut host forms a bar across the copper.
        low=(ox,n['y0']-.20,north_height(params,n['y0']-.20))
        toe=(pt[0],pt[1]-.20,z)
        triangles.extend([(eave,low,bottom),(low,toe,bottom)])
    cut=[(left[0]-spread,n['y0']-.201),(right[0]+spread,n['y0']-.201),
         (right[0]+spread,ap[1]),(left[0]-spread,ap[1])]
    return triangles,cut


def copper(params):
    """One copper surface from the north return, around the bow, to the east wing."""
    import math
    w=params.bows[0];ret=params.detail['copper_return'];n=north(params)
    a0,a1=sorted((w['a0'],w['a1']))
    if a1-a0>math.pi:a0,a1=a1,a0+2*math.pi
    ro=w['r']+.20;z=w['wall_top_z'];back=ret['y1']
    # This corner is on the north range's plane at the east-wing wall.
    anchor=(n['x1'],back,north_height(params,back))
    arc=[(w['cx']+ro*math.cos(a0+(a1-a0)*i/48),
          w['cy']+ro*math.sin(a0+(a1-a0)*i/48),z) for i in range(49)]
    arc.sort(key=lambda p:p[0])
    # Short continuous return joins the fan's north end. The outside boundary
    # follows the host plane, so subtracting the tile cannot leave a roof gap.
    front=(ret['x0'],n['y0']-.20,north_height(params,n['y0']-.20))
    upper=(ret['x0'],back,north_height(params,back))
    tris=[(upper,front,arc[0]),(upper,arc[0],anchor)]
    tris += [(a,b,anchor) for a,b in zip(arc,arc[1:])]
    cuts=[[(v[0],v[1]) for v in tri] for tri in tris]
    return tris,cuts


def clip_host(pts,params):
    """Remove replaced tiles without changing any neighbouring roof plane."""
    from archetypes.masonry_house_v4_detail import subtract
    from archetypes.masonry_house import _normal
    holes=[]
    if params.detail.get('dining_roof_junction'):holes.append(dining(params)[1])
    if params.detail.get('continuous_copper_corner'):holes.extend(copper(params)[1])
    normal=_normal(pts);a=pts[0]
    def point(p):
        x,y=p
        return (x,y,a[2]-(normal[0]*(x-a[0])+normal[1]*(y-a[1]))/normal[2])
    poly=[(p[0],p[1]) for p in pts]
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))<0:poly.reverse()
    return [[point(p) for p in f] for f in subtract(poly,holes)]


def wall_profile(params,lo,hi,z):
    bay=params.bays[0];a,c=sorted((bay['pts'][0][0],bay['pts'][-1][0]))
    return [(lo,z),(a-.24,z),(a,bay['band_top_z']),
            (c,bay['band_top_z']),(c+.24,z),(hi,z)]
