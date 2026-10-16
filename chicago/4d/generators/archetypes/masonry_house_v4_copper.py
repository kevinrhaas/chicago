"""T-2220: low copper hood, intersected with both courtyard roof slopes.

The HABS section controls the relative rise and the ell controls the peak's
plan position. Sheet joints and stock are bounded construction estimates.
All coordinates are metres in the shared engine-neutral building frame.
"""
from __future__ import annotations

import math

from archetypes.masonry_house_v4_west_roof import clip, slope, z

SEGMENTS = 96
COPPER = 4


def controls(params):
    bow = params.bows[0]
    north = next(r for r in params.ranges if r['name'] == 'north_range')
    east = next(r for r in params.ranges if r['name'] == 'east_wing')
    apex = (east['x0'], north['y0'], bow['wall_top_z'] + bow['roof_rise_m'])
    hosts = [slope('y', north['y0'], north['eave_lo_z'], north['ridge_at'], north['ridge_z']),
             slope('x', east['x0'], east['eave_lo_z'], east['ridge_at'], east['ridge_z'])]
    return bow, apex, hosts


def _hull(points):
    """Convex union boundary, so a host is cut once, not once per fan facet."""
    points = sorted(set(points))
    def turn(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def half(seq):
        out = []
        for p in seq:
            while len(out) > 1 and turn(out[-2], out[-1], p) <= 1e-9:
                out.pop()
            out.append(p)
        return out
    return half(points)[:-1] + half(reversed(points))[:-1]


def patches(params):
    """Nonoverlapping angular facets; every cut edge lies on a host plane."""
    bow, apex, hosts = controls(params)
    radius = bow['r'] + .20
    result = []
    for i in range(SEGMENTS):
        def edge(j):
            a = 2*math.pi*j/SEGMENTS
            return (bow['cx']+radius*math.cos(a), bow['cy']+radius*math.sin(a))
        p, q = edge(i), edge(i+1)
        ux, uy = p[0]-apex[0], p[1]-apex[1]
        vx, vy = q[0]-apex[0], q[1]-apex[1]
        dz = bow['wall_top_z']-apex[2]
        determinant = ux*vy-uy*vx
        aa, bb = dz*(vy-uy)/determinant, dz*(ux-vx)/determinant
        plane = (aa, bb, apex[2]-aa*apex[0]-bb*apex[1])
        poly = [apex[:2], p, q]
        for host in hosts:
            poly = clip(poly, tuple(plane[k]-host[k] for k in range(3)))
        if poly:
            result.append({'sector': i, 'plane': plane,
                           'points': [(x, y, z(plane, x, y)) for x, y in poly]})
    return result


def surface(params):
    faces = [p['points'] for p in patches(params)]
    # The hood is a concave height function over a convex eave polygon.
    # Its region above both affine hosts is therefore convex. The independent
    # spatial test checks the hull against all emitted facets and host cuts.
    return faces, [_hull([(p[0], p[1]) for face in faces for p in face])]


def north_cladding(params):
    """Copper replaces tiles on the existing plane, never a raised canopy.

    The owner aerial bounds the chamfered return. Its lower edge follows the
    real overhang. Subtract the radial hood so the two coverings meet once.
    Returning convex fragments also gives the tile cutter exact shared edges.
    """
    spec = params.detail.get('north_copper_cladding')
    if not spec:
        return []
    from archetypes.masonry_house_v4_detail import subtract
    from archetypes.masonry_house_v4_west_roof import area
    north = next(r for r in params.ranges if r['name'] == 'north_range')
    _, _, hosts = controls(params)
    poly = list(spec['outline'])
    if area(poly) < 0:
        poly.reverse()
    # Outline's south end is deliberately beyond the eave: the actual roof,
    # not another guessed datum, owns the visible lower edge.
    low = north['y0'] - north.get('eave_lo_overhang', .20)
    for plane in ((1,0,-north['x0']),(-1,0,north['x1']),
                  (0,1,-low),(0,-1,north['ridge_at'])):
        poly = clip(poly, plane)
    pieces = subtract(poly, surface(params)[1])
    return [[(x,y,z(hosts[0],x,y)) for x,y in part] for part in pieces]


def add_north_cladding(b, params):
    faces = north_cladding(params)
    if not faces:
        return
    _, _, hosts = controls(params)
    normal = _unit((-hosts[0][0],-hosts[0][1],1))
    conf = params.detail['north_copper_cladding']['conf']
    for pts in faces:
        ids = b.raw(pts, conf, COPPER, normal)
        # Metric UVs keep sheet stock at the same scale as the adjoining hood.
        for idx, p in zip(ids, pts):
            b.roof_uvs[idx] = (p[0], p[1]*math.sqrt(1+hosts[0][1]**2))
        b.raw([(x,y,h-.012) for x,y,h in reversed(pts)],conf,COPPER,
              tuple(-v for v in normal))
    # Standing seams follow the fall, clipped independently to each fragment.
    # No folds are placed on internal subtraction/triangulation edges.
    xmin = min(p[0] for face in faces for p in face)
    xmax = max(p[0] for face in faces for p in face)
    x = math.ceil(xmin/.48)*.48
    while x < xmax-1e-6:
        for face in faces:
            ys=[]
            for a,c in zip(face,face[1:]+face[:1]):
                if abs(c[0]-a[0]) < 1e-9:
                    continue
                t=(x-a[0])/(c[0]-a[0])
                if 0 <= t <= 1:
                    ys.append(a[1]+t*(c[1]-a[1]))
            if len(ys)>1 and max(ys)-min(ys)>.05:
                a=(x,min(ys)+.02,z(hosts[0],x,min(ys)+.02))
                c=(x,max(ys)-.02,z(hosts[0],x,max(ys)-.02))
                fold(b,a,c,normal)
        x += .48


def _unit(p):
    length = math.sqrt(sum(x*x for x in p))
    return tuple(x/length for x in p)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def fold(b, a, c, normal, width=.018, height=.012):
    """Closed narrow folded stock, seated within 0.6 mm of the copper sheet."""
    if math.dist(a, c) < .025:
        return
    along = _unit(tuple(c[k]-a[k] for k in range(3)))
    side = _unit(_cross(along, normal))
    reduced = getattr(b, 'reduced_roof_details', False)
    def P(p, u, v):
        return tuple(p[k]+side[k]*u+normal[k]*v for k in range(3))
    if reduced:
        b.raw([P(a,-width/2,.002), P(a,width/2,.002),
               P(c,width/2,.002), P(c,-width/2,.002)], 1.0, COPPER, normal)
        return
    profile = [(-width/2,.0006),(-width/2,height),
               (width/2,height),(width/2,.0006)]
    rings = [[P(p,u,v) for u,v in profile] for p in (a,c)]
    for i in range(4):
        j = (i+1)%4
        pts = [rings[0][i], rings[0][j], rings[1][j], rings[1][i]]
        centre = tuple((a[k]+c[k])/2+normal[k]*(height+.0006)/2 for k in range(3))
        want = tuple(sum(p[k] for p in pts)/4-centre[k] for k in range(3))
        b.raw(pts, 1.0, COPPER, want)
    b.raw(rings[0], 1.0, COPPER, tuple(-x for x in along))
    b.raw(rings[1], 1.0, COPPER, along)


def add_hood(b, params):
    bow, apex, hosts = controls(params)
    radius = bow['r']+.20
    for part in patches(params):
        pts, plane = part['points'], part['plane']
        normal = _unit((-plane[0],-plane[1],1))
        indices = b.raw(pts, bow['conf_roof'], COPPER, normal)
        # Radial drainage coordinates remain continuous across tessellation.
        for index, p in zip(indices, pts):
            theta = math.atan2(p[1]-apex[1],p[0]-apex[0])
            b.roof_uvs[index] = (radius*theta, math.dist(p,apex))
        for a,c in zip(pts,pts[1:]+pts[:1]):
            at_eave = abs(a[2]-bow['wall_top_z'])<1e-7 and abs(c[2]-bow['wall_top_z'])<1e-7
            if at_eave:
                # Closed shallow apron, with its upper lip on the roof itself.
                lower = [(p[0],p[1],p[2]-.045) for p in (a,c)]
                outward = _unit(((a[0]+c[0])/2-bow['cx'],(a[1]+c[1])/2-bow['cy'],0))
                b.raw([lower[0],lower[1],c,a],1.0,COPPER,outward)
                inner = [(bow['cx']+(p[0]-bow['cx'])*bow['r']/radius,
                          bow['cy']+(p[1]-bow['cy'])*bow['r']/radius,
                          bow['wall_top_z']-.045) for p in (a,c)]
                b.raw([inner[0],inner[1],lower[1],lower[0]],1.0,COPPER,(0,0,-1))
            elif any(abs(a[2]-z(h,*a[:2]))<1e-7 and abs(c[2]-z(h,*c[:2]))<1e-7 for h in hosts):
                # A narrow seated flashing at the actual roof intersection.
                fold(b,a,c,normal,.075,.003)
        # Two low transverse laps divide the long radial sheets. They follow
        # the actual planar facet and are clipped at the adjoining roof.
        i = part['sector']
        ends = [(bow['cx']+radius*math.cos(2*math.pi*j/SEGMENTS),
                 bow['cy']+radius*math.sin(2*math.pi*j/SEGMENTS),
                 bow['wall_top_z']) for j in (i,i+1)]
        for fraction in (1/3,2/3):
            line = [tuple(apex[k]+(p[k]-apex[k])*fraction for k in range(3)) for p in ends]
            lo,hi=0.,1.
            for host in hosts:
                d0,d1=[p[2]-z(host,*p[:2]) for p in line]
                if d0<0 and d1<0:
                    hi=-1.;break
                if d0<0:lo=max(lo,d0/(d0-d1))
                if d1<0:hi=min(hi,d0/(d0-d1))
            if hi>lo:
                a,c=[tuple(line[0][k]+(line[1][k]-line[0][k])*t for k in range(3)) for t in (lo,hi)]
                fold(b,a,c,normal,.028,.002)
        # Panel joints follow every second angular ray (~45 cm at the eave),
        # not every triangulation edge. Clip the seam against the same hosts.
        if i%2:
            continue
        angle = 2*math.pi*i/SEGMENTS
        foot = (bow['cx']+radius*math.cos(angle),bow['cy']+radius*math.sin(angle),bow['wall_top_z'])
        end = 1.0
        for host in hosts:
            d0 = apex[2]-z(host,*apex[:2])
            d1 = foot[2]-z(host,*foot[:2])
            if d1<0:
                end = min(end,d0/(d0-d1))
        length = math.dist(apex,foot)
        start = .12/length
        end -= .025/length
        def mix(t):
            return tuple(apex[k]+(foot[k]-apex[k])*t for k in range(3))
        if end>start:
            fold(b,mix(start),mix(end),normal)
