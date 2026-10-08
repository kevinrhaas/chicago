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
    if params.detail.get('dining_crested_connection'):
        return dining_connection(params)
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


def dining_connection(params):
    """A raised cross ridge, intersected with the unchanged north roof plane.

    The copper hip ends over the bay shoulders. Two planar tile slopes continue
    its ridge back to the main ridge. Their valleys are intersections, not a
    rectangular hole cut down to the clerestory (T-2157).
    """
    bay=params.bays[0];n=north(params);ap=tuple(bay['apex'])
    back=(ap[0],n['ridge_at'],n['ridge_z'])
    eave_y=n['y0']-.20;eave_z=north_height(params,eave_y)
    polygons=[];valleys=[]
    for pt in (bay['pts'][1],bay['pts'][-2]):
        shoulder=(pt[0],ap[1],bay['band_top_z'])
        ring=(shoulder[0]+(ap[0]-shoulder[0])*.18,ap[1],
              shoulder[2]+(ap[2]-shoulder[2])*.11)
        # The connector has a level ridge, matching the host. Its height only
        # varies across x, so this is the exact tile/host intersection at eave.
        fraction=(ap[2]-eave_z)/(ap[2]-ring[2])
        valley=(ap[0]+(ring[0]-ap[0])*fraction,eave_y,eave_z)
        toe=(shoulder[0],eave_y,shoulder[2])
        ring_toe=(ring[0],eave_y,ring[2])
        ridge_eave=(ap[0],eave_y,ap[2])
        # Convex pieces: a fan over the concave five-corner outline would
        # bridge its valley and put submerged tile triangles inside the host.
        polygons.extend([[back,ridge_eave,valley],
                         [ap,ring,ring_toe,ridge_eave],
                         [ring,shoulder,toe,ring_toe]])
        valleys.append(valley)
    # Only the triangular cross-roof intersection replaces the host. The eave
    # on both sides retains precisely its existing line and slope.
    cut=[(valleys[0][0],eave_y-1e-7),(valleys[1][0],eave_y-1e-7),back[:2]]
    return polygons,cut


def add_dining_roof(b,params):
    """Copper hip/apron, standing seams, tiled cross ridge and matching crests."""
    import math
    from archetypes import masonry_house as legacy
    from archetypes.masonry_house_v4_roof_crests import add_ridge_crest
    bay=params.bays[0];ap=tuple(bay['apex']);z=bay['band_top_z']
    copper,roof=4,3;conf=bay['conf_roof']
    outline=[(*p,z) for p in bay['pts'][1:-1]]
    # A shallow flared apron below the steeper cap, as in the owner close-up.
    # Fractions and seam stock are reconstructed, not survey measurements.
    ring=[(p[0]+(ap[0]-p[0])*.18,p[1]+(ap[1]-p[1])*.18,
           z+(ap[2]-z)*.11) for p in outline]

    def mix(a,c,t):return tuple(a[k]+(c[k]-a[k])*t for k in range(3))
    def strip(a,c,width=.018):
        dx,dy=c[0]-a[0],c[1]-a[1];length=math.hypot(dx,dy)
        if length<1e-8:return
        side=(-dy/length*width/2,dx/length*width/2,0)
        def P(p,s):return (p[0]+side[0]*s,p[1]+side[1]*s,p[2]+.014)
        b.raw([P(a,-1),P(a,1),P(c,1),P(c,-1)],conf,copper,(0,0,1))

    for i,(p,q) in enumerate(zip(outline,outline[1:])):
        a,c=ring[i:i+2]
        b.raw([p,q,c,a],conf,copper,(0,0,1))
        b.raw([a,c,ap],conf,copper,(0,0,1))
        strip(a,c,.055)  # folded horizontal apron joint
        count=max(1,round(math.dist(p,q)/.48))
        for j in range(count):
            foot=mix(p,q,j/count);joint=mix(a,c,j/count)
            strip(foot,joint);strip(joint,ap)
        b.raw([(p[0],p[1],z-.055),(q[0],q[1],z-.055),q,p],conf,copper)
    strip(outline[-1],ring[-1]);strip(ring[-1],ap)

    for poly in dining_connection(params)[0]:
        legacy._two_sided_roof(b,poly,conf,roof)
    # Same cap radius, spacing and raised terracotta collars as the main ridge.
    end=north(params)['ridge_at'];start=ap[1]+.30;step=.36
    for i in range(math.ceil((end-start)/step)):
        lo=start+i*step;hi=min(end,lo+step-.012)
        for j in range(12):
            a,c=math.pi*j/12,math.pi*(j+1)/12
            def P(angle,y):return (ap[0]+.14*math.cos(angle),y,ap[2]+.055+.14*math.sin(angle))
            b.raw([P(a,lo),P(c,lo),P(c,hi),P(a,hi)],conf,19+i%3,(0,0,1))
        add_ridge_crest(b,'y',ap[0],ap[2],lo,hi,conf,19+i%3)
    # Folded copper terminal over the hip apex, meeting the first tile cap.
    for j in range(12):
        a,c=math.pi*j/12,math.pi*(j+1)/12
        def P(angle,y):return (ap[0]+.15*math.cos(angle),y,ap[2]+.055+.15*math.sin(angle))
        b.raw([P(a,ap[1]-.025),P(c,ap[1]-.025),P(c,start),P(a,start)],conf,copper,(0,0,1))
    # The visible hip end is folded closed, not an open pipe above the apex.
    b.raw([P(math.pi*j/12,ap[1]-.025) for j in range(13)]+
          [(ap[0]-.15,ap[1]-.025,ap[2]),(ap[0]+.15,ap[1]-.025,ap[2])],
          conf,copper,(0,-1,0))


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
    if params.detail.get('dining_crested_connection'):
        return [(lo,z),(hi,z)]
    bay=params.bays[0];a,c=sorted((bay['pts'][0][0],bay['pts'][-1][0]))
    return [(lo,z),(a-.24,z),(a,bay['band_top_z']),
            (c,bay['band_top_z']),(c+.24,z),(hi,z)]
