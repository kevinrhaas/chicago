"""T-2220: low copper hood, intersected with both courtyard roof slopes.

The HABS section controls the relative rise and the ell controls the peak's
plan position. Sheet joints and stock are bounded construction estimates.
All coordinates are metres in the shared engine-neutral building frame.
"""
from __future__ import annotations

import math

from archetypes.masonry_house_v4_west_roof import area, clip, slope, z

SEGMENTS = 96
COPPER = 4


def controls(params):
    bow = params.bows[0]
    north = next(r for r in params.ranges if r['name'] == 'north_range')
    east = next(r for r in params.ranges if r['name'] == 'east_wing')
    apex = (east['x0'], north['y0'], bow['wall_top_z'] + bow['roof_rise_m'])
    hosts = [slope('y', north['y0'], north['eave_lo_z'], north['ridge_at'], north['ridge_z']),
             slope('x', east['x0'], east['eave_lo_z'], east['ridge_at'], east['ridge_z'])]
    L = leanto(params)
    if L:
        # T-3373: the hood now dies into the lean-to's copper, not the tiles.
        hosts.append(L['lean'])
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
    radius = bow['eave_r']
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


def leanto(params):
    """T-3373: the low hipped copper roof between the dining bay and the hall bow.

    HABS sheet 4's section at W 51.3 cuts it: the courtyard wall stands higher
    there (26.5 ft) and the roof's lowest run is flatter (27 degrees) than the
    tiled slope above it. The owner's aerials show that run in copper, its west
    end hipped and a downpipe at its corner. Its eave is level with the hall
    bow's; its plane meets the tiles where the section's flatter run ends
    (`meets_y`), so the roof steps down there instead of running on in one plane.
    Returns None when the record asks for no lean-to.
    """
    spec = params.detail.get('north_copper_leanto')
    if not spec:
        return None
    north = next(r for r in params.ranges if r['name'] == 'north_range')
    east = next(r for r in params.ranges if r['name'] == 'east_wing')
    tile = slope('y', north['y0'], north['eave_lo_z'], north['ridge_at'], north['ridge_z'])
    wing = slope('x', east['x0'], east['eave_lo_z'], east['ridge_at'], east['ridge_z'])
    y0, e, ym = north['y0'], spec['eave_z'], spec['meets_y']
    p = (z(tile, 0, ym) - e) / (ym - y0)
    xw = spec['x_west']
    return dict(tile=tile, wing=wing, lean=(0, p, e - p*y0), hip=(p, 0, e - p*xw),
                pitch=p, xw=xw, x_wing=east['x0'], x_far=east['ridge_at'], y0=y0, ym=ym,
                eave_z=e, ov=spec['overhang_m'], conf=spec['conf'])


def _minus(a, b):
    return tuple(a[k]-b[k] for k in range(3))


def _leanto_regions(params, visible):
    """Plan regions of the lean-to's two sheets. `visible` also trims them where
    they pass under the east wing's slope."""
    L = leanto(params)
    if not L:
        return []
    from archetypes.masonry_house_v4_detail import subtract
    lo = L['y0'] - L['ov']
    box = [(L['xw']-L['ov'], lo), (L['x_far'], lo), (L['x_far'], L['ym']+.5),
           (L['xw']-L['ov'], L['ym']+.5)]
    hood = surface(params)[1]
    out = []
    for name, own, other in (('slope', L['lean'], L['hip']), ('hip', L['hip'], L['lean'])):
        poly = clip(clip(list(box), _minus(own, L['tile'])), _minus(other, own))
        if visible:
            poly = clip(poly, _minus(own, L['wing']))
        if not poly or abs(area(poly)) < 1e-8:
            continue
        if area(poly) < 0:
            poly.reverse()
        for piece in subtract(poly, hood):
            if abs(area(piece)) > 1e-8:
                out.append((name, own, piece, poly))
    return out


def leanto_facets(params):
    """The lean-to's planar sheets, each cut where it meets the tiles, the east
    wing and the bow hood; every cut edge lies on a host plane or the hood's hull."""
    return [dict(name=name, plane=own, points=[(x, y, z(own, x, y)) for x, y in piece])
            for name, own, piece, _ in _leanto_regions(params, True)]


def leanto_tile_holes(params):
    """Tiles the lean-to replaces, including the deep tiled overhang its raised
    wall now stands in front of; the bow hood's own hull is left to the hood."""
    L = leanto(params)
    if not L:
        return []
    from archetypes.masonry_house_v4_detail import subtract
    north = next(r for r in params.ranges if r['name'] == 'north_range')
    low = north['y0'] - north.get('eave_lo_overhang', .20) - .05
    band = [(L['xw']-L['ov'], low), (L['x_far'], low), (L['x_far'], L['y0']-L['ov']),
            (L['xw']-L['ov'], L['y0']-L['ov'])]
    # Whole sheets, not their pieces round the hood: the hood's hull is a hole
    # of its own, and overlapping holes cut the tiles once. Only where a sheet
    # shows (T-3433): every host roof takes the same plan holes, and a sheet's
    # plan runs on under the east wing's slope to its ridge, so cutting that
    # whole plan left the wing's court slope open from eave to ridge beside the
    # middle stack, 2.3 m wide, with no sheet over it.
    holes = list({id(whole): whole for _, _, _, whole in _leanto_regions(params, True)}.values())
    # The overhang band likewise stops where the wing's slope rises over the lean-to.
    band = clip(band, _minus(L['lean'], L['wing']))
    return holes + ([band] if band and abs(area(band)) > 1e-8 else [])


def leanto_front_x(params):
    """Where the lean-to's front eave meets the bow hood's eave circle."""
    L = leanto(params)
    bow = params.bows[0]
    y = L['y0'] - L['ov']
    d = bow['eave_r']**2 - (y-bow['cy'])**2
    return bow['cx'] - math.sqrt(d) if d > 0 else L['x_wing']


def _outside_hull(a, c, hull):
    """Parts of segment a-c (plan) outside a convex CCW hull, as (t0, t1) ranges."""
    lo, hi = 0., 1.
    for p, q in zip(hull, hull[1:]+hull[:1]):
        # inside: (q-p) x (pt-p) >= 0
        def side(pt):
            return (q[0]-p[0])*(pt[1]-p[1])-(q[1]-p[1])*(pt[0]-p[0])
        sa, sc = side(a), side(c)
        if sa < 0 and sc < 0:
            return [(0., 1.)]
        if sa < 0:
            lo = max(lo, sa/(sa-sc))
        elif sc < 0:
            hi = min(hi, sa/(sa-sc))
    if hi <= lo:
        return [(0., 1.)]
    return [r for r in ((0., lo), (hi, 1.)) if r[1]-r[0] > 1e-9]


def add_leanto(b, params):
    L = leanto(params)
    if not L:
        return
    from archetypes import masonry_house as legacy
    conf = L['conf']
    hull = surface(params)[1][0]
    if area(hull) < 0:
        hull = list(reversed(hull))
    sheets = {}
    for name, own, piece, whole in _leanto_regions(params, True):
        pts = [(x, y, z(own, x, y)) for x, y in piece]
        normal = _unit((-own[0], -own[1], 1))
        ids = b.raw(pts, conf, COPPER, normal)
        g = _unit((own[0], own[1], 0))  # the sheet's uphill direction
        t = (-g[1], g[0])
        for idx, q in zip(ids, pts):
            b.roof_uvs[idx] = (q[0]*t[0]+q[1]*t[1],
                               (q[0]*g[0]+q[1]*g[1])*math.sqrt(1+L['pitch']**2))
        b.raw([(x, y, h-.012) for x, y, h in reversed(pts)], conf, COPPER,
              tuple(-v for v in normal))
        sheets[name] = (own, whole)
    for name, (own, whole) in sheets.items():
        normal = _unit((-own[0], -own[1], 1))
        g = _unit((own[0], own[1], 0))
        t = (-g[1], g[0])
        # Standing seams run down the fall of each sheet, 0.48 m apart, over
        # the whole sheet and stopping at the bow hood's edge.
        ss = [q[0]*t[0]+q[1]*t[1] for q in whole]
        s = math.ceil(min(ss)/.48)*.48
        while s < max(ss)-1e-6:
            along = []
            for a, c in zip(whole, whole[1:]+whole[:1]):
                sa, sc = a[0]*t[0]+a[1]*t[1], c[0]*t[0]+c[1]*t[1]
                if abs(sc-sa) < 1e-9 or not (min(sa, sc) <= s <= max(sa, sc)):
                    continue
                k = (s-sa)/(sc-sa)
                along.append((a[0]+k*(c[0]-a[0]), a[1]+k*(c[1]-a[1])))
            if len(along) > 1:
                along.sort(key=lambda q: q[0]*g[0]+q[1]*g[1])
                lo, hi = along[0], along[-1]
                if math.dist(lo, hi) > .06:
                    lo = (lo[0]+g[0]*.02, lo[1]+g[1]*.02)
                    hi = (hi[0]-g[0]*.02, hi[1]-g[1]*.02)
                    for t0, t1 in _outside_hull(lo, hi, hull):
                        p0 = (lo[0]+(hi[0]-lo[0])*t0, lo[1]+(hi[1]-lo[1])*t0)
                        p1 = (lo[0]+(hi[0]-lo[0])*t1, lo[1]+(hi[1]-lo[1])*t1)
                        if math.dist(p0, p1) > .06:
                            fold(b, (*p0, z(own, *p0)), (*p1, z(own, *p1)), normal)
            s += .48
        # Seated flashings where a sheet meets the tiles, the wing or the hip.
        pts = [(x, y, z(own, x, y)) for x, y in whole]
        for a, c in zip(pts, pts[1:]+pts[:1]):
            def on(plane_):
                return all(abs(q[2]-z(plane_, q[0], q[1])) < 1e-6 for q in (a, c))
            if on(L['tile']) or on(L['wing']):
                fold(b, a, c, normal, .075, .003)
            elif name == 'slope' and on(L['hip']):
                fold(b, a, c, normal, .05, .02)
    # Folded front and west fascias give the sheet its thickness at the eaves.
    ez = L['eave_z'] - L['pitch']*L['ov']
    x0, y = L['xw']-L['ov'], L['y0']-L['ov']
    x1 = leanto_front_x(params)
    b.raw([(x0, y, ez-.055), (x1, y, ez-.055), (x1, y, ez), (x0, y, ez)], conf, COPPER, (0, -1, 0))
    tile = L['tile']
    yc = L['y0'] + (ez - z(tile, x0, L['y0'])) / tile[1]
    if yc > y:
        b.raw([(x0, y, ez-.055), (x0, yc, ez-.055), (x0, yc, ez), (x0, y, ez)], conf, COPPER, (-1, 0, 0))
    # The raised wall's west return: brick from the tiles up to the hip's eave.
    yc = L['y0'] + (L['eave_z']-z(tile, L['xw'], L['y0']))/tile[1]
    cheek = [(L['xw'], L['y0'], z(tile, L['xw'], L['y0'])), (L['xw'], yc, L['eave_z']),
             (L['xw'], L['y0'], L['eave_z'])]
    legacy._poly_facing(b, cheek, conf, legacy.BRICK, (-1, 0, 0))


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
    radius = bow['eave_r']
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
