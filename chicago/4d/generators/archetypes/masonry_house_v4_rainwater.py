"""Glessner v4 courtyard gutters and the two clear HABS05 downpipes.

Presence and junctions are inferred for 1904 from the circa1923 courtyard view.
Sections, offsets and dark oxidised-metal finish are reconstructed. Roof geometry
supplies every eave datum; no roof pitch, wall, opening or ridge is moved. This
uses existing dark metal slot10, not a new or globally darkened copper material.
"""
from __future__ import annotations

import math

METAL = 10
CONFIDENCE = 1.0


def _unit(v):
    d=math.sqrt(sum(x*x for x in v)) or 1
    return tuple(x/d for x in v)


def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def _tube(b,path,radius,sides=8):
    """Small closed round metal bead or pipe along an already resolved path."""
    rings=[]
    initial=_unit(tuple(path[1][k]-path[0][k] for k in range(3)))
    seed=(0,0,1) if abs(initial[2])<.9 else (1,0,0)
    for i,p in enumerate(path):
        before,after=path[max(0,i-1)],path[min(len(path)-1,i+1)]
        t=_unit(tuple(after[k]-before[k] for k in range(3)))
        u=_unit(_cross(t,seed));v=_cross(t,u)
        rings.append([tuple(p[k]+radius*(u[k]*math.cos(2*math.pi*j/sides)+v[k]*math.sin(2*math.pi*j/sides)) for k in range(3)) for j in range(sides)])
    for i in range(len(path)-1):
        for j in range(sides):
            q=(j+1)%sides
            pts=[rings[i][j],rings[i][q],rings[i+1][q],rings[i+1][j]]
            centre=tuple((path[i][k]+path[i+1][k])/2 for k in range(3))
            outward=tuple(sum(p[k] for p in pts)/4-centre[k] for k in range(3))
            b.raw(pts,CONFIDENCE,METAL,outward)
    for i,other in ((0,1),(-1,-2)):
        direction=tuple(path[i][k]-path[other][k] for k in range(3))
        b.raw(rings[i],CONFIDENCE,METAL,direction)


def _gutter(b,edge,normals):
    """Open 120mm half-round trough, 3mm metal, with two 6mm rolled lips.

    Its centre projects32mm beyond the roof edge and the outer lip reaches98mm.
    The trough top sits16mm below that edge so the original roof still sheds
    into it. Section is bounded reconstruction, not a measured modern fitting.
    """
    radius,inside,offset=.060,.057,.032
    centres=[(p[0]+n[0]*offset,p[1]+n[1]*offset,p[2]-.016) for p,n in zip(edge,normals)]
    segments=10
    def P(i,theta,r):
        p,n=centres[i],normals[i]
        return (p[0]+n[0]*r*math.cos(theta),p[1]+n[1]*r*math.cos(theta),p[2]+r*math.sin(theta))
    for i in range(len(edge)-1):
        for j in range(segments):
            a,c=math.pi+math.pi*j/segments,math.pi+math.pi*(j+1)/segments
            mid=(a+c)/2
            normal=_unit((normals[i][0]+normals[i+1][0],normals[i][1]+normals[i+1][1],0))
            want=(normal[0]*math.cos(mid),normal[1]*math.cos(mid),math.sin(mid))
            b.raw([P(i,a,radius),P(i,c,radius),P(i+1,c,radius),P(i+1,a,radius)],CONFIDENCE,METAL,want)
            b.raw([P(i,a,inside),P(i+1,a,inside),P(i+1,c,inside),P(i,c,inside)],CONFIDENCE,METAL,tuple(-v for v in want))
    for theta in (math.pi,2*math.pi):
        _tube(b,[P(i,theta,radius) for i in range(len(edge))],.006)
    # Close the small sheet section at each end; leave the drainage trough open.
    for i,other in ((0,1),(-1,-2)):
        want=tuple(edge[i][k]-edge[other][k] for k in range(3))
        for j in range(segments):
            a,c=math.pi+math.pi*j/segments,math.pi+math.pi*(j+1)/segments
            b.raw([P(i,a,inside),P(i,a,radius),P(i,c,radius),P(i,c,inside)],CONFIDENCE,METAL,want)


def _outline_normals(points):
    """Outward horizontal normals for the existing clockwise-facing eave path."""
    normals=[]
    for i,p in enumerate(points):
        before,after=points[max(0,i-1)],points[min(len(points)-1,i+1)]
        normals.append(_unit((after[1]-before[1],before[0]-after[0],0)))
    return normals


def _downpipe(b,x,y,top,inlet=None):
    """Plain88mm pipe, modest collector and three simple retaining collars."""
    bottom=.12
    ix,iy=inlet or (x,y)
    _tube(b,[(x,y,bottom),(x,y,top-.40),(ix,iy,top-.20),(ix,iy,top-.10)],.044,12)
    for f in (.25,.5,.75):
        z=bottom+(top-bottom)*f
        _tube(b,[(x,y,z-.018),(x,y,z+.018)],.049,12)
    # The historical upper collector is visible; exact flared section is not.
    rings=[]
    for z,half in ((top-.19,.048),(top-.025,.073)):
        rings.append([(ix-half,iy-half,z),(ix+half,iy-half,z),(ix+half,iy+half,z),(ix-half,iy+half,z)])
    for j in range(4):
        q=(j+1)%4;pts=[rings[0][j],rings[0][q],rings[1][q],rings[1][j]]
        outward=(sum(p[0] for p in pts)/4-ix,sum(p[1] for p in pts)/4-iy,0)
        b.raw(pts,CONFIDENCE,METAL,outward)


def add_courtyard_rainwater(b,params):
    """Follow the photographed courtyard eaves and their two clear pipe joints."""
    ranges={r['name']:r for r in params.ranges}
    north,east=ranges.get('north_range'),ranges.get('east_wing')
    if not north or not east:return
    overhang=.20  # Same existing eave extension as masonry_house._range.
    bow=next((w for w in params.bows if w['name']=='hall_bow'),None)
    dining=next((w for w in params.bays if w['name']=='dining'),None)
    copper=params.detail.get('copper_return')

    # South eave of the north range. The dining cap and bow occupy interruptions;
    # do not run a gutter through their rooms or through the projecting tower.
    kick=north.get('kick')
    slope=math.tan(math.radians(kick['pitch_deg'])) if kick and kick['side']=='south' else (north['ridge_z']-north['eave_lo_z'])/(north['ridge_at']-north['y0'])
    ny=north['y0']-overhang;nz=north['eave_lo_z']-overhang*slope
    right=copper['x0'] if copper else north['x1']
    runs=[(north['x0'],right)]
    if dining:
        da,dc=min(p[0] for p in dining['pts']),max(p[0] for p in dining['pts'])
        runs=[(a,min(c,da)) for a,c in runs if a<da]+[(max(a,dc),c) for a,c in runs if c>dc]
    for a,c in runs:
        if c>a+.02:_gutter(b,[(a,ny,nz),(c,ny,nz)],[(0,-1,0)]*2)
    if copper:
        _gutter(b,[(copper['x0'],copper['y0'],copper['wall_top_z']),
                   (copper['x1'],copper['y0'],copper['wall_top_z'])],[(0,-1,0)]*2)

    if dining:
        edge=[(*p,dining['band_top_z']) for p in dining['pts']]
        _gutter(b,edge,_outline_normals(edge))
        # HABS05's conspicuous pipe at the photo-left/west bay junction.
        x,y=dining['pts'][0]
        _downpipe(b,x-.085,y-.085,dining['band_top_z'],(x-.032,y-.085))

    if bow:
        a0,a1=sorted((bow['a0'],bow['a1']))
        if a1-a0>math.pi:a0,a1=a1,a0+2*math.pi
        radius=bow['r']+.20
        angles=[a0+(a1-a0)*i/48 for i in range(49)]
        edge=[(bow['cx']+radius*math.cos(a),bow['cy']+radius*math.sin(a),bow['wall_top_z']) for a in angles]
        _gutter(b,edge,[(math.cos(a),math.sin(a),0) for a in angles])
        # HABS05's second slender pipe is immediately west of the bow junction.
        _downpipe(b,bow['cx']+bow['r']*math.cos(a0)-.085,
                  north['y0']-.085,bow['wall_top_z'],
                  (edge[0][0]+.032*math.cos(a0),edge[0][1]+.032*math.sin(a0)))

    # West-facing east-range eave: north end terminates at the bow roof, while
    # the stair drum occupies the middle interval and conceals the rear gutter.
    ex=east['x0']-overhang
    ez=east['eave_lo_z']-overhang*(east['ridge_z']-east['eave_lo_z'])/(east['ridge_at']-east['x0'])
    end=north['y0']
    if bow:
        d=ex-bow['cx'];radius=bow['r']+.20
        if abs(d)<radius:end=min(end,bow['cy']-math.sqrt(radius*radius-d*d))
    runs=[(east['y0'],end)]
    for tower in params.towers:
        if tower['name']!='stair':continue
        d=ex-tower['cx']
        if abs(d)>=tower['r']:continue
        half=math.sqrt(tower['r']**2-d*d)+.025
        lo,hi=tower['cy']-half,tower['cy']+half
        runs=[(a,min(c,lo)) for a,c in runs if a<lo]+[(max(a,hi),c) for a,c in runs if c>hi]
    for a,c in runs:
        if c>a+.02:_gutter(b,[(ex,a,ez),(ex,c,ez)],[(-1,0,0)]*2)
