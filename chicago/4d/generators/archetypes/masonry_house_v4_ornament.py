"""Carved Prairie entrance stonework for the Glessner v4 alternate (T-1730).

The opening/ring/column bounds come from the resolved structure record. Owner
photograph image(5), checked against the HABS entry views, establishes the carved
organization: branching foliate scrolls inside concentric decorated archivolts,
three unlike capitals, and an egg-and-dart sill above a bead row with leafy ends.
The individual lobes, veins, drilled eyes and undercuts are reconstructed carving,
not a scan or a claim to reproduce the sculptor's exact tool marks. No reference
pixels are used. The scale is architectural (metres), not a renderer effect.

Only ``Builder.raw`` is required. This module deliberately imports no bpy and
does not change dimensions, openings, materials, or the default house builder.
``fan`` replaces the old star-field fan, ``sill`` replaces its flat egg discs,
and ``columns`` retains the shafts but replaces the entry's coarse capitals.
"""
from __future__ import annotations

import math

TRIM = 2
CARVED_GRANITE = 0


class Relief:
    """A sculptor's (horizontal, vertical, outward-depth) work plane."""

    def __init__(self, builder, plane, confidence, mat=TRIM, profile=None):
        self.b = builder
        self.p = plane
        self.conf = confidence
        # The stone the carving is cut in; faces asking for no slot take it.
        self.mat = mat
        self.profile = profile

    def point(self, u, z, d):
        if self.profile: d += self.profile(u,z)
        at = self.p['at'] + self.p['sign'] * d
        return (at, u, z) if self.p['axis'] == 'x' else (u, at, z)

    def vector(self, u, z, d):
        return (self.p['sign'] * d, u, z) if self.p['axis'] == 'x' else (u, self.p['sign'] * d, z)

    def face(self, pts, mat=None, normal=(0, 0, 1)):
        mat = self.mat if mat is None else mat
        if self.profile and normal:
            u=sum(p[0] for p in pts)/len(pts);z=sum(p[1] for p in pts)/len(pts);h=.0001
            du=(self.profile(u+h,z)-self.profile(u-h,z))/(2*h)
            dz=(self.profile(u,z+h)-self.profile(u,z-h))/(2*h)
            normal=(normal[0]-du*normal[2],normal[1]-dz*normal[2],normal[2])
        self.b.raw([self.point(*p) for p in pts], self.conf, mat,
                   self.vector(*normal) if normal else None)

    def solid(self, poly, back, front, mat=None):
        self.face([(*p, front) for p in poly], mat)
        for p, q in zip(poly, poly[1:] + poly[:1]):
            self.face([(*p, back), (*q, back), (*q, front), (*p, front)], mat, None)

    def box(self, x0, x1, z0, z1, back, front, mat=None):
        self.solid([(x0,z0),(x1,z0),(x1,z1),(x0,z1)],back,front,mat)

    def tube(self, path, radius, sides=10):
        """Round carved stem/roll, with real side faces and relief shadows."""
        if len(path) < 2:
            return
        rings = []
        normals = []
        for i, (x, z, d) in enumerate(path):
            a, c = path[max(0,i-1)], path[min(len(path)-1,i+1)]
            length = math.hypot(c[0]-a[0], c[1]-a[1]) or 1
            nx, nz = -(c[1]-a[1])/length, (c[0]-a[0])/length
            r = radius(i/(len(path)-1)) if callable(radius) else radius
            ring, ns = [], []
            for j in range(sides):
                th = 2*math.pi*j/sides
                dx, dz, dd = nx*math.cos(th), nz*math.cos(th), math.sin(th)
                ring.append((x+r*dx,z+r*dz,d+r*dd))
                ns.append((dx,dz,dd))
            rings.append(ring)
            normals.append(ns)
        for i in range(len(rings)-1):
            for j in range(sides):
                k=(j+1)%sides
                want=tuple(normals[i][j][a]+normals[i][k][a] for a in range(3))
                self.face([rings[i][j],rings[i+1][j],rings[i+1][k],rings[i][k]],normal=want)
        self.face(list(reversed(rings[0])),normal=None)
        self.face(rings[-1],normal=None)

    def arc(self, cx, cz, radius, depth, thickness, start=0, end=math.pi, n=64):
        self.tube([(cx+radius*math.cos(start+(end-start)*i/n),
                    cz+radius*math.sin(start+(end-start)*i/n),depth)
                   for i in range(n+1)],thickness)

    def bead(self, x, z, d, radius, squash=1):
        # Small actual hemispherical bosses, not circles painted on a plane.
        for i in range(6):
            aa,cc=math.pi*i/12,math.pi*(i+1)/12
            for j in range(12):
                a,c=2*math.pi*j/12,2*math.pi*(j+1)/12
                def p(th,ph):
                    return (x+radius*math.sin(th)*math.cos(ph),
                            z+radius*squash*math.sin(th)*math.sin(ph),
                            d+radius*math.cos(th))
                self.face([p(aa,a),p(cc,a),p(cc,c)] if i==0 else
                          [p(aa,a),p(cc,a),p(cc,c),p(aa,c)])

    def leaf(self, x, z, angle, length, width, depth, lift=.024, curl=.18,
             holes=True, phase=0, steps=16):
        """Curved lobed acanthus blade, raised midrib and pierced side eye.

        Lobes differ on the two sides; a fluted, cupped cross section and a
        turned tip keep this from being a flat extruded outline. Omitted eye
        cells expose the recessed bed behind the blade as genuine undercuts.
        """
        tx,tz=math.cos(angle),math.sin(angle)
        nx,nz=-tz,tx
        across=10

        def centre(t):
            bend=curl*length*math.sin(math.pi*t)
            return x+tx*length*t+nx*bend,z+tz*length*t+nz*bend

        def vertex(i,j):
            t=i/steps;v=2*j/across-1
            # Root and tip close on the midrib. Their width floor left a row of
            # sub-millimetre slivers there, which the K01 measure reads as
            # coincident faces, and laid one leaf's over another's wherever
            # blades fan from one root (T-2267).
            if i in (0,steps):v=0
            cx,cz=centre(t)
            lobes=.80+.20*math.cos(6*math.pi*t+phase+(0 if v<0 else .5))
            half=width*.5*max(.015,math.sin(math.pi*t))**.68*lobes
            rib=(1-abs(v))**1.5
            raised=lift*math.sin(math.pi*t)**.55*(.24+.76*rib)
            raised+=lift*.20*math.sin(3*math.pi*t+phase)*abs(v)
            # The tip rolls back into its supporting stem.
            raised-=lift*.22*max(0,(t-.80)/.20)**2
            return cx+nx*half*v,cz+nz*half*v,depth+raised

        grid={(i,j):vertex(i,j) for i in range(steps+1) for j in range(across+1)}
        cells=set()
        for i in range(steps):
            for j in range(across):
                t=(i+.5)/steps;v=2*(j+.5)/across-1
                pierced=holes and ((t-.64)/.105)**2+((v-.40)/.29)**2<1
                if not pierced:
                    cells.add((i,j))
        for i,j in sorted(cells):
            corners=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
            pts=[grid[k] for k in corners]
            self.face([p for n,p in enumerate(pts) if p!=pts[n-1]])
            # Close outer edges and the negative eye: no paper-thin leaves.
            for a,c,other in [(corners[0],corners[1],(i,j-1)),
                              (corners[1],corners[2],(i+1,j)),
                              (corners[2],corners[3],(i,j+1)),
                              (corners[3],corners[0],(i-1,j))]:
                if other not in cells and grid[a]!=grid[c]:
                    p,q=grid[a],grid[c]
                    self.face([p,q,(q[0],q[1],q[2]-.010),
                               (p[0],p[1],p[2]-.010)],normal=None)
        path=[]
        for i in range(15):
            t=.06+.88*i/14;cx,cz=centre(t)
            path.append((cx,cz,depth+lift*math.sin(math.pi*t)**.55+.002))
        self.tube(path,lambda t:.0035*(1-.65*t),6)


def _bezier(points, depth, count=28):
    a,b,c,d=points
    return [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*d[0],
             (1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*d[1],
             depth) for t in (i/count for i in range(count+1))]


def _scroll(r, x, z, radius, depth, mirror=1, turn=0, stem=1.0, foliage=1.0):
    """Open curling stem with unequal leaves, rather than a regular rosette.
    ``stem`` and ``foliage`` thicken the stem and enlarge the leaves (T-3564's
    tympanum scrolls, cut fuller than the colonnette capitals')."""
    path=[]
    for i in range(53):
        t=i/52;th=turn+mirror*(.12+1.72*math.pi*t)
        rr=radius*(1-.76*t)
        path.append((x+rr*math.cos(th),z+rr*math.sin(th),depth+.006*math.sin(math.pi*t)))
    r.tube(path,lambda t:radius*(.058-.026*t)*stem,10)
    for j, (t, size) in enumerate(((.13,1),(.31,.90),(.50,.77),(.69,.64),(.84,.47))):
        th=turn+mirror*(.12+1.72*math.pi*t)
        rr=radius*(1-.76*t)
        px,pz=x+rr*math.cos(th),z+rr*math.sin(th)
        r.leaf(px,pz,th+mirror*(math.pi*.44),radius*.93*size*foliage,
               radius*.61*size*foliage,depth+.003*j,lift=radius*.14,
               curl=mirror*.24,phase=j*.6,steps=14)


def _boss(r, poly, back, front, inset):
    """A small square billet: a raised block with a chamfered top, not a tile."""
    cx=sum(p[0] for p in poly)/len(poly);cz=sum(p[1] for p in poly)/len(poly)
    top=[(cx+(p[0]-cx)*(1-inset),cz+(p[1]-cz)*(1-inset)) for p in poly]
    r.face([(*p,front) for p in top])
    for (p,q),(tp,tq) in zip(zip(poly,poly[1:]+poly[:1]),zip(top,top[1:]+top[:1])):
        r.face([(*p,back),(*q,back),(*tq,front),(*tp,front)],normal=None)


def _annulus(r, cx, cz, r0, r1, back, front, n=48, mat=None):
    """A half-annulus moulding floor between two radii, in convex sectors."""
    steps=math.ceil((r1-r0)/.03) if r.profile else 1
    for j in range(steps):
        lo=r0+(r1-r0)*j/steps;hi=r0+(r1-r0)*(j+1)/steps
        for i in range(n):
            a,c=math.pi*i/n,math.pi*(i+1)/n
            r.face([(cx+lo*math.cos(c),cz+lo*math.sin(c),front),(cx+hi*math.cos(c),cz+hi*math.sin(c),front),
                    (cx+hi*math.cos(a),cz+hi*math.sin(a),front),(cx+lo*math.cos(a),cz+lo*math.sin(a),front)][::-1],mat)
    for rr,sign in ((r0,-1),(r1,1)):
        for i in range(n):
            a,c=math.pi*i/n,math.pi*(i+1)/n
            r.face([(cx+rr*math.cos(a),cz+rr*math.sin(a),back),(cx+rr*math.cos(c),cz+rr*math.sin(c),back),
                    (cx+rr*math.cos(c),cz+rr*math.sin(c),front),(cx+rr*math.cos(a),cz+rr*math.sin(a),front)][::sign],
                   mat,None)


def _roundel(r, x, z, radius, depth, seed):
    """A stem bent into a ring round a six-leaf rosette with a drilled boss."""
    # The ring is open by a hair at its foot, where its stem comes in: a closed
    # tube caps back to back on itself, and on a ring a few centimetres across
    # the two caps fall on one millimetre lattice (T-2853; T-2267's measure).
    gap=max(.06,.004/radius)
    r.arc(x,z,radius,depth,radius*.075,-math.pi/2+gap/2,3*math.pi/2-gap/2,40)
    # A small ring's leaves take fewer rows, so none falls under a millimetre.
    steps=max(5,min(10,round(radius/.009)))
    for j in range(6):
        th=math.pi/2+2*math.pi*j/6+seed*.21
        r.leaf(x+radius*.10*math.cos(th),z+radius*.10*math.sin(th),th,radius*.86,radius*.62,
               depth-.006,radius*.16,(.18 if j%2 else -.18),True,seed+j*.7,steps)
    r.bead(x,z,depth+.012,radius*.16)


def _plumb_arc(r, cx, cz, radius, depth, thickness, stilt):
    """A roll round a stilted head: the semicircle, then plumb down by `stilt`."""
    if stilt<=0:
        return r.arc(cx,cz,radius,depth,thickness)
    r.tube([(cx+radius,cz-stilt,depth)]+[(cx+radius*math.cos(math.pi*i/64),cz+radius*math.sin(math.pi*i/64),depth)
                                         for i in range(65)]+[(cx-radius,cz-stilt,depth)],thickness)


def _legs(r, cx, cz, r0, r1, back, front, stilt):
    """A half-annulus floor's two plumb legs under a stilted centre."""
    if stilt<=0:
        return
    steps=math.ceil((r1-r0)/.03) if r.profile else 1
    for sign in (-1,1):
        for j in range(steps):
            x0,x1=sorted((cx+sign*(r0+(r1-r0)*j/steps),cx+sign*(r0+(r1-r0)*(j+1)/steps)))
            r.face([(x0,cz-stilt,front),(x1,cz-stilt,front),(x1,cz,front),(x0,cz,front)])
        for x,n in ((cx+sign*r0,-sign),(cx+sign*r1,sign)):
            quad=[(x,cz-stilt,back),(x,cz,back),(x,cz,front),(x,cz-stilt,front)]
            r.face(quad if n>0 else quad[::-1],None,(n,0,0))


# T-3381: the field is the owner's photographs' tree (2026-11-05): a trunk up the
# middle and scrolls bent into rings either side, mirrored, every ring filled with
# leaves and the ground between them drilled through to shadow. As (across, up,
# radius) in shares of the field's radius F from the stilted centre: the large
# ring low either side of the trunk, a smaller one out at the springing, one
# beside the trunk's head and one between. Read off the photographs to about a
# twentieth of F; HABS sheet 5's eight unmirrored rings (T-2853) are a drawing's
# shorthand that the photographs do not bear out.
FIELD_ROUNDELS = ((-.430, .330, .290), (.430, .330, .290), (-.820, .110, .140), (.820, .110, .140),
                  (-.260, .720, .200), (.260, .720, .200), (-.600, .620, .110), (.600, .620, .110))
# Each branch runs from a parent (-1 the trunk, at the height given) to its ring.
FIELD_STEMS = ((-1, 1, .18), (-1, 0, .18), (1, 3, 0), (0, 2, 0), (-1, 5, .50), (-1, 4, .50), (5, 7, 0), (4, 6, 0))
# The dark slot (glass_dark), used as the deep shadow behind pierced carving and
# in drilled pockets, as window recesses use it: the renderer bakes no occlusion.
DARK = 11


def _cells(cx, cz, a, b, count, stilt):
    """A band between radii a and b cut into `count` cells round the head and on
    down its plumb legs at about the same pitch; each cell maps (radial, along)
    fractions to a point."""
    cells = []
    for i in range(count):
        t0, t1 = math.pi*i/count, math.pi*(i+1)/count
        cells.append(lambda fr, ft, t0=t0, t1=t1: (cx+(a+(b-a)*fr)*math.cos(t0+(t1-t0)*ft),
                                                  cz+(a+(b-a)*fr)*math.sin(t0+(t1-t0)*ft)))
    pitch = (a+b)/2*math.pi/count
    n = int(stilt/pitch+.5) if stilt > 0 else 0
    for k in range(n):
        z0, z1 = cz-stilt*k/n, cz-stilt*(k+1)/n
        for sign in (-1, 1):
            cells.append(lambda fr, ft, z0=z0, z1=z1, sign=sign: (cx+sign*(a+(b-a)*fr), z0+(z1-z0)*ft))
    return cells


def _quad_faces(r, cell, f0, f1, g0, g1, depth, mat=None, steps=1):
    """The cell's front between radial fractions f0..f1 and along g0..g1, at a
    depth that may vary with the radial fraction."""
    for j in range(steps):
        a, c = f0+(f1-f0)*j/steps, f0+(f1-f0)*(j+1)/steps
        da, dc = (depth(a), depth(c)) if callable(depth) else (depth, depth)
        r.face([(*cell(a, g0), da), (*cell(c, g0), dc), (*cell(c, g1), dc), (*cell(a, g1), da)], mat)


def _wall(r, p, q, back, front, inward, mat=None):
    """A side wall between two band points, facing `inward` in the plane."""
    r.face([(*p, back), (*q, back), (*q, front), (*p, front)], mat, (inward[0], inward[1], 0))


def _dentil_band(r, cx, cz, a, b, back, front, count, stilt, low=False):
    """T-3381: the outer rim, a flat band sunk with square pockets ("blockier marks"):
    each cell's face rings its own pocket, whose floor is in shadow."""
    pf0, pf1 = .30, .70
    for cell in _cells(cx, cz, a, b, count, stilt):
        # The pockets stand about their own width apart, as photographed.
        width = math.dist(cell(.5, 0), cell(.5, 1))
        half = min(.27, (pf1-pf0)*(b-a)/max(width, 1e-6)/2)
        g0, g1 = .5-half, .5+half
        if low:
            _quad_faces(r, cell, 0, 1, 0, 1, front)
            # The cell is one flat quad over the curved bed, so the pocket's
            # shadow stands clear of its chord.
            r.face([(*cell(pf0, g0), front+.008), (*cell(pf1, g0), front+.008),
                    (*cell(pf1, g1), front+.008), (*cell(pf0, g1), front+.008)], DARK)
            continue
        _quad_faces(r, cell, 0, pf0, 0, 1, front)
        _quad_faces(r, cell, pf1, 1, 0, 1, front)
        _quad_faces(r, cell, pf0, pf1, 0, g0, front)
        _quad_faces(r, cell, pf0, pf1, g1, 1, front)
        floor = front-.030
        r.face([(*cell(pf0, g0), floor), (*cell(pf1, g0), floor),
                (*cell(pf1, g1), floor), (*cell(pf0, g1), floor)], DARK)
        mid = cell(.5, .5)
        for p, q in ((cell(pf0, g0), cell(pf1, g0)), (cell(pf1, g0), cell(pf1, g1)),
                     (cell(pf1, g1), cell(pf0, g1)), (cell(pf0, g1), cell(pf0, g0))):
            m = ((p[0]+q[0])/2, (p[1]+q[1])/2)
            _wall(r, p, q, floor, front, (mid[0]-m[0], mid[1]-m[1]))
        # The band's own edges, to the bed.
        for fr, way in ((0, -1), (1, 1)):
            p, q = cell(fr, 0), cell(fr, 1)
            m = ((p[0]+q[0])/2, (p[1]+q[1])/2)
            _wall(r, p, q, back, front, ((m[0]-mid[0])*1, (m[1]-mid[1])*1))


def _drill(r, x, z, d, radius, sides=6):
    """A drilled hole: a small dark disc just proud of the stone it pierces."""
    r.face([(x+radius*math.cos(2*math.pi*k/sides), z+radius*math.sin(2*math.pi*k/sides), d) for k in range(sides)], DARK)


def _petal(r, x, z, angle, length, width, depth, lift):
    """The phone tier's leaf: a raised lozenge on its midrib, four triangles."""
    tx, tz = math.cos(angle), math.sin(angle)
    nx, nz = -tz, tx
    at = lambda t, v, up: (x+tx*length*t+nx*width*.5*v, z+tz*length*t+nz*width*.5*v, depth+up)
    root, tip, left, right, ridge = at(0, 0, 0), at(1, 0, lift*.2), at(.42, -1, lift*.25), at(.42, 1, lift*.25), at(.45, 0, lift)
    for p, q in ((root, left), (left, tip), (tip, right), (right, root)):
        r.face([p, q, ridge])


def _leaf(r, low, x, z, angle, length, width, depth, lift, curl, holes, phase, steps):
    if low:
        return _petal(r, x, z, angle, length, width, depth, lift)
    r.leaf(x, z, angle, length, width, depth, lift, curl, holes, phase, steps)


def _carved_roll(r, cx, cz, a, b, base, bulge, count, stilt, low=False):
    """T-3381: the middle rim, a rounded roll cut into blocks at dark radial joints,
    every block filled with a four-leaf cluster and drilled through between them."""
    depth = lambda fr: base+bulge*math.sin(math.pi*fr)
    gap = .022
    for i, cell in enumerate(_cells(cx, cz, a, b, count, stilt)):
        g0, g1 = gap, 1-gap
        steps = 2 if low else 5
        along = 1 if low else 3
        for k in range(along):
            _quad_faces(r, cell, 0, 1, g0+(g1-g0)*k/along, g0+(g1-g0)*(k+1)/along, depth, steps=steps)
        # The joint: the bed seen down the cut between two blocks.
        _quad_faces(r, cell, .04, .96, 1-gap, 1, base-.028, DARK)
        if not low:
            _quad_faces(r, cell, .04, .96, 0, gap, base-.028, DARK)
        if not low:
            mid = cell(.5, .5)
            for g in (g0, g1):
                for j in range(steps):
                    f0, f1 = j/steps, (j+1)/steps
                    p, q = cell(f0, g), cell(f1, g)
                    m = ((p[0]+q[0])/2, (p[1]+q[1])/2)
                    r.face([(*p, base-.03), (*q, base-.03), (*q, depth(f1)), (*p, depth(f0))], None,
                           ((m[0]-mid[0]), (m[1]-mid[1]), 0))
        # The cluster: four broad leaves to the block's corners round a boss,
        # and the stone drilled through in the four gaps between them.
        x, z = cell(.5, .5)
        ux, uz = cell(1, .5)[0]-x, cell(1, .5)[1]-z
        ang = math.atan2(uz, ux)
        size = (b-a)*.47
        top = depth(.5)
        for j in range(4):
            th = ang+math.pi/4+math.pi/2*j
            _leaf(r, low, x+size*.10*math.cos(th), z+size*.10*math.sin(th), th, size, size*.78, top-.006,
                  size*.20, (.20 if j % 2 else -.20), True, i*.41+j, 8)
        r.bead(x, z, top+.010, size*.17)
        for j in range(4):
            th = ang+math.pi/2*j
            for reach, rad in (((.62, .085),) if low else ((.62, .085), (.95, .060))):
                fr = .5+reach*size/(b-a)*math.cos(th-ang)
                _drill(r, x+reach*size*math.cos(th), z+reach*size*math.sin(th), depth(fr)+.0015, size*rad,
                       4 if low else 6)


def _inner_torus(r, cx, cz, a, b, base, bulge, count, stilt, low=False):
    """T-3564: the rim inside the carved roll, a round torus cut at the roll's joints
    and wound with a twist of leaves (the owner's photograph 01, 2026-11-10)."""
    depth = lambda fr: base+bulge*math.sin(math.pi*fr)**.7
    gap = .018
    for i, cell in enumerate(_cells(cx, cz, a, b, count, stilt)):
        steps = 2 if low else 6
        along = 1 if low else 3
        for k in range(along):
            _quad_faces(r, cell, 0, 1, gap+(1-2*gap)*k/along, gap+(1-2*gap)*(k+1)/along, depth, steps=steps)
        _quad_faces(r, cell, .04, .96, 1-gap, 1, base-.02, DARK)
        if low:
            continue
        _quad_faces(r, cell, .04, .96, 0, gap, base-.02, DARK)
        # The twist: three leaves laid slantwise across each block, like a rope.
        for j in range(3):
            g = .2+.3*j
            p, q = cell(.15, g), cell(.85, g+.16)
            ang = math.atan2(q[1]-p[1], q[0]-p[0])
            size = math.dist(p, q)
            _leaf(r, low, p[0], p[1], ang, size*1.05, size*.42, depth(.5)-.010, size*.12,
                  (.2 if j % 2 else -.2), False, i*.53+j, 8)


def _field_fill(F, rings, pitch, keep_off, trunk, low_z=0., jitter=0.):
    """Points of the field's ground the rings and trunk leave bare, mirrored, on
    a staggered lattice of the given pitch (jittered by a share of it), down to
    `low_z` under the centre: (across, up) in metres."""
    found = []
    row = 0
    z = low_z+pitch*.5
    while z < F:
        x0 = pitch*.5 if row % 2 else pitch
        while x0 < F:
            x = x0+jitter*pitch*math.sin(x0*137.1+z*71.9)
            z1 = z+jitter*pitch*math.sin(x0*53.3-z*97.7)
            ok = math.hypot(x, max(z1, 0)) < F*.92 and x > F*trunk and z1 > low_z+F*.02 and x < F*.92
            for rx, rz, rr in rings:
                if ok and math.hypot(x-rx, z1-rz) < rr+F*keep_off:
                    ok = False
            if ok:
                found += [(x, z1), (-x, z1)]
            x0 += pitch
        z += pitch*.87
        row += 1
    return found



def bands_and_field(r, cx, cz, R, stilt, low=False):
    """The fan's carved rims and field, outside in (T-3381, the owner's photographs
    of 2026-11-05): a fillet; a flat rim sunk with square pockets; a rounded roll
    of carved and drilled blocks; a thin plain rim stepped out from the field; and
    the field's tree of ringed scrolls on a drilled-through ground."""
    _plumb_arc(r, cx, cz, R-.012, .034, .012, stilt)
    _dentil_band(r, cx, cz, R*.875, R-.02, -.045, .030, 36, stilt, low)
    _plumb_arc(r, cx, cz, R*.878, .030, .010, stilt)
    if not low:
        _annulus(r, cx, cz, R*.655, R*.872, -.045, -.020, 48)
        _legs(r, cx, cz, R*.655, R*.872, -.045, -.020, stilt)
    # T-3564 (owner, 2026-11-12, his photograph 01 of 2026-11-10): "the mid detail and
    # then another level that you have coming in and it more bulges out". The carved
    # roll stands fuller, and inside it the plain rim is now a fat torus of its own,
    # jointed with the roll's thirteen blocks and twisted with leaves, standing out
    # past both the roll and the field, as the photograph's springing shows it.
    _carved_roll(r, cx, cz, R*.660, R*.866, .000, .062, 13, stilt, low)
    _inner_torus(r, cx, cz, R*.560, R*.652, -.045, .085, 13, stilt, low)
    F = R*.553
    # The field's ground, cut back behind the carving and drilled through it to shadow.
    n = 16 if low else 40
    r.face([(cx+F, cz-stilt, -.020)]+[(cx+F*math.cos(math.pi*i/n), cz+F*math.sin(math.pi*i/n), -.020)
                                      for i in range(n+1)]+[(cx-F, cz-stilt, -.020)], DARK)
    foot = cz-stilt
    # The trunk, broad at its root and tapering up the middle to a small rosette.
    trunk = [(cx, foot+F*.04+(cz+F*.80-foot-F*.04)*i/12, .024) for i in range(13)]
    # T-3564: the photograph's trunk is a slim stem, only a little swollen at its root.
    r.tube(trunk, lambda t: F*(.052-.022*t+.040*max(0, .22-t)/.22), 6 if low else 10)
    rings = [(cx+x*F, cz+z*F, rr*F) for x, z, rr in FIELD_ROUNDELS]
    for j, (parent, child, up) in enumerate(FIELD_STEMS):
        x, z, rr = rings[child]
        p0 = (cx, cz+up*F) if parent < 0 else rings[parent][:2]
        dx, dz = x-p0[0], z-p0[1]; length = math.hypot(dx, dz) or 1.
        p3 = (x-dx/length*rr*.93, z-dz/length*rr*.93)
        out = F*.05 if parent < 0 else rings[parent][2]*.93
        p0 = (p0[0]+dx/length*out, p0[1]+dz/length*out)
        sgn = 1 if x > cx else -1
        bend = (-dz/length*sgn, dx/length*sgn); sway = .14*length
        p1 = (p0[0]+(p3[0]-p0[0])*.33+bend[0]*sway, p0[1]+(p3[1]-p0[1])*.33+bend[1]*sway)
        p2 = (p0[0]+(p3[0]-p0[0])*.66+bend[0]*sway*.5, p0[1]+(p3[1]-p0[1])*.66+bend[1]*sway*.5)
        span = math.hypot(p3[0]-p0[0], p3[1]-p0[1])
        r.tube(_bezier([p0, p1, p2, p3], .022, max(4, min(20, round(span/.012)))),
               F*(.030 if parent < 0 else .024), 6 if low else 8)
        mid = _bezier([p0, p1, p2, p3], 0, 2)[1]
        ang = math.atan2(dz, dx)
        for side in (-1, 1):
            _leaf(r, low, mid[0], mid[1], ang+side*1.05, F*.15, F*.085, .016, .016, side*.16, True, j*.5+side, 10)
    for j, (x, z, rr) in enumerate(rings+[(cx, cz+F*.88, F*.075)]):
        d = .028 if j == len(rings) else .024+.002*(j % 3)
        if low and j < len(rings):
            # T-3564: the phone tier's scroll, as the full tier's: a flat raised
            # stem wound inward on fourteen chords, five petals along it.
            side = 1 if x > cx else -1
            parent, up = next((pa, u) for pa, c, u in FIELD_STEMS if c == j)
            p0 = rings[parent][:2] if parent >= 0 else (cx, cz+up*F)
            start = math.atan2(p0[1]-z, p0[0]-x)
            spiral = []
            for k in range(15):
                t = k/14; th = start-side*(.12+1.72*math.pi*t); rad = rr*1.04*(1-.76*t)
                spiral.append((x+rad*math.cos(th), z+rad*math.sin(th), rr*(.11-.05*t)))
            for (ax, az, aw), (bx, bz, bw) in zip(spiral, spiral[1:]):
                l = math.hypot(bx-ax, bz-az) or 1.; nx, nz = -(bz-az)/l, (bx-ax)/l
                band = [(ax+nx*aw, az+nz*aw), (bx+nx*bw, bz+nz*bw), (bx-nx*bw, bz-nz*bw), (ax-nx*aw, az-nz*aw)]
                r.face([(*q, d+.010) for q in band][::side])
                r.face([(*band[0], d-.01), (*band[1], d-.01), (*band[1], d+.010), (*band[0], d+.010)][::side], None,
                       (nx, nz, 0))
            for k, (t, size) in enumerate(((.13, 1), (.31, .90), (.50, .77), (.69, .64), (.84, .47))):
                th = start-side*(.12+1.72*math.pi*t); rad = rr*1.04*(1-.76*t)
                _petal(r, x+rad*math.cos(th), z+rad*math.sin(th), th-side*math.pi*.44, rr*1.1*size, rr*.7*size,
                       d+.004, rr*.16)
            r.bead(x, z, d+.012, rr*.14)
            continue
        if low:
            # The ring as a flat raised band on sixteen chords.
            w = rr*.075
            for k in range(16):
                a, c = 2*math.pi*k/16, 2*math.pi*(k+1)/16
                ring = [(x+(rr+w)*math.cos(a), z+(rr+w)*math.sin(a)), (x+(rr+w)*math.cos(c), z+(rr+w)*math.sin(c)),
                        (x+(rr-w)*math.cos(c), z+(rr-w)*math.sin(c)), (x+(rr-w)*math.cos(a), z+(rr-w)*math.sin(a))]
                r.face([(*q, d+w) for q in ring])
                r.face([(*ring[1], d-w), (*ring[0], d-w), (*ring[0], d+w), (*ring[1], d+w)], None,
                       (math.cos((a+c)/2), math.sin((a+c)/2), 0))
            for k in range(6):
                th = math.pi/2+2*math.pi*k/6+j*.21
                _petal(r, x+rr*.10*math.cos(th), z+rr*.10*math.sin(th), th, rr*.86, rr*.62, d-.006, rr*.16)
                if j < len(rings):
                    th += math.pi/6
                    _petal(r, x+rr*.30*math.cos(th), z+rr*.30*math.sin(th), th, rr*.62, rr*.46, .014, rr*.12)
            r.bead(x, z, d+.012, rr*.16)
            continue
        if j == len(rings):
            _roundel(r, x, z, rr, d, j)
            continue
        # T-3564: "see how its like a plant?" Each branch ends not in a closed ring
        # but in a leafy scroll curling back over itself, a rosette in its eye.
        side = 1 if x > cx else -1
        parent, up = next((pa, u) for pa, c, u in FIELD_STEMS if c == j)
        p0 = rings[parent][:2] if parent >= 0 else (cx, cz+up*F)
        start = math.atan2(p0[1]-z, p0[0]-x)
        _scroll(r, x, z, rr*1.04, d, -side, start, stem=1.9, foliage=1.18)
        for k in range(4):
            th = math.pi/2+2*math.pi*k/4+j*.37
            r.leaf(x+rr*.08*math.cos(th), z+rr*.08*math.sin(th), th, rr*.42, rr*.32, d+.004, rr*.10,
                   (.2 if k % 2 else -.2), True, j+k*.5, 7)
        r.bead(x, z, d+.012, rr*.12)
        # A second whorl of smaller leaves between the rosette's, so the ring
        # reads full of foliage pierced between, as photographed.
        for k in range(6):
            th = math.pi/2+2*math.pi*(k+.5)/6+j*.21
            r.leaf(x+rr*.30*math.cos(th), z+rr*.30*math.sin(th), th, rr*.62, rr*.46, .014, rr*.12,
                   (.2 if k % 2 else -.2), False, j+k, 7)
    # The ground between the rings, crowded with leaves sprung outward and up
    # from the trunk's root; where they leave it bare it shows the shadow behind.
    near = [(x-cx, z-cz, rr) for x, z, rr in rings]
    # Every ring sprouts leaves off its outside, curling on round it as a scroll.
    for j, (x, z, rr) in enumerate(near):
        side = 1 if x > 0 else -1
        for k, th in enumerate((-.35, .55, 1.45, 2.35, 3.25)):
            th = math.pi/2-side*(math.pi/2-th)
            px, pz = x+rr*1.02*math.cos(th), z+rr*1.02*math.sin(th)
            if math.hypot(px, max(pz, 0)) > F*.90 or abs(px) < F*.10 or pz < -stilt+F*.04:
                continue
            ang = th-side*math.pi*.42
            _leaf(r, low, cx+px, cz+pz, ang, rr*.62, rr*.40, .013, .015, -.18*side, True, j+k*.6, 8)
    for j, (x, z) in enumerate(_field_fill(F, near, F*.10, .025, .11, -stilt, .25)):
        ang = math.atan2(z+F*.35, x)+(.35 if (j//2) % 2 else -.25)*(1 if x > 0 else -1)
        _leaf(r, low, cx+x-math.cos(ang)*F*.07, cz+z-math.sin(ang)*F*.07, ang, F*.16, F*.11, .012, .016,
              .16*(1 if x > 0 else -1), True, j*.37, 8)
    # The small half-boss at the trunk's root.
    k = 6 if low else 16
    r.solid([(cx+F*.12*math.cos(math.pi*i/k), foot+F*.12*math.sin(math.pi*i/k)) for i in range(k+1)], -.020, .012)


def fan(b, o):
    """The Prairie Avenue door's fan: rock-faced voussoirs round a carved tympanum.

    T-2215, rebuilt to the owner's photographs of 2026-10-12 and the HABS
    "Detail of Entrance Doorway" drawing he sent with them. Read off the
    pictures, outside in: fifteen radiating voussoirs, keyed at the crown; a
    fillet; a channel of square billets; a fillet; a broad archivolt of drilled
    foliage; a torus roll; and a semicircular field of pierced foliage, stems
    bent round leafy roundels, the whole standing well in front of a deep dark
    bed so the piercing reads. The arrangement is the pictures'; every leaf,
    lobe and drill hole is reconstructed carving, not traced or projected
    (LIBERTIES).

    T-2853 brought it to HABS sheet 5 measured: the head is stilted (its centre
    `o['stilt']` over the spring line, every ring run plumb down to it), and the
    field's roundels are the sheet's eight, at its places and sizes, on stems
    from the boss at the foot, where the record had five on a mirrored trunk.

    T-3381 rebuilt the rims and field to the owner's photographs of 2026-11-05,
    which govern over the sheet's shorthand: inside out, a tree of ringed scrolls
    either side of a flared trunk, pierced to shadow; a thin plain rim stepped
    out; a rounded roll of carved blocks drilled between the leaves; and a flat
    outer rim sunk with square pockets (bands_and_field).
    """
    conf=b.params.detail.get('conf',o['conf'])
    # The colour photographs show the tympanum cut in the wall's own pink granite,
    # a shade lighter where it is dressed, not in the grey limestone of the trim.
    stilt=o.get('stilt',0.)
    cx=(o['u0']+o['u1'])/2;cz=o['spring_z']+stilt;rad=o['r_in']
    from archetypes.masonry_house_v4_entry import settings,relief_profile
    spec=settings(b)
    profile=relief_profile(spec,cx,cz,rad+.04,stilt) if spec else None
    r=Relief(b,o,conf,CARVED_GRANITE,profile=profile)
    from archetypes.masonry_house_v4_detail import rock_voussoirs
    # The structural arch keeps the opening record's measured outline.
    rock_voussoirs(b,o,cx,cz,rad+.04,o['r_out'],o.get('voussoirs') or 15,conf,90211,stilt)
    # Bed lies behind all carving, letting the drilled pockets remain dark.
    # The wall builder removes the entire arch; overlap the voussoirs' inner
    # radius by 1 mm so their recessed carving bed cannot reveal the sky.
    bed_radius=o['r_out']
    if profile:
        from archetypes.masonry_house_v4_entry import recessed_bed
        recessed_bed(r,cx,cz,rad+.04,bed_radius,spec,stilt=stilt)
    else:
        r.solid([(cx+bed_radius,cz-stilt)]+[(cx+bed_radius*math.cos(math.pi*i/80),cz+bed_radius*math.sin(math.pi*i/80))
                 for i in range(81)]+[(cx-bed_radius,cz-stilt)],-.065,-.045)
    R=rad+.04
    bands_and_field(r,cx,cz,R,stilt)


def sill(b, o):
    """Egg-and-dart, bead-and-reel, and two carved terminal blocks."""
    # T-2965: the carved string is the front's granite, as the colonnettes over it.
    r=Relief(b,o,b.params.detail.get('conf',o['conf']),CARVED_GRANITE)
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];height=z1-z0
    r.box(a,c,z0-.018,z1+.014,-.015,.069)
    # Two continuous rails frame the U-shaped eggs, with a bead row below.
    for zz,dd,rr in ((z1-.004,.109,.012),(z0+.025,.115,.009),(z0-.009,.088,.009)):
        r.tube([(a,zz,dd),(c,zz,dd)],rr)
    n=max(1,round((c-a)/.135));step=(c-a)/n
    for i in range(n):
        x=a+(i+.5)*step;zz=z0+height*.64
        r.bead(x,zz,.093,min(.028,step*.23),squash=1.18)
        # A separate U carves a shadow pocket round every convex egg.
        path=[]
        for j in range(23):
            th=math.pi+math.pi*j/22
            path.append((x+step*.38*math.cos(th),zz+.005+.049*math.sin(th),.108))
        r.tube(path,.009,8)
        xdart=a+i*step
        r.leaf(xdart,z0+.035,math.pi/2,height*.66,step*.15,.104,.012,
               0,False,steps=8)
    for i in range(n*2+1):
        r.bead(a+i*step/2,z0+.004,.096,.017,.82)
    # The photograph shows conspicuous foliate blocks wider than the sill,
    # not an egg row terminating abruptly at the outer jambs.
    # T-2985: each block's width is the record's (sheet 6), 0.44 m where it names none.
    half=o.get('terminal',.44)/2
    for mirror,x in ((-1,a-half+.005),(1,c+half-.005)):
        r.box(x-half,x+half,z0-.025,z1+.045,-.015,.068)
        _scroll(r,x, z0+height*.51,.105,.099,mirror,0 if mirror>0 else math.pi)
        for j in range(3):
            r.leaf(x-mirror*.17,z0+.012+j*.038,
                   (.35+j*.18) if mirror>0 else math.pi-(.35+j*.18),
                   .15,.069,.085,.025,mirror*.22,True,j)


def _shaft(r,u,z0,z1,gap):
    radius=gap*.62
    for j in range(28):
        a,c=2*math.pi*j/28,2*math.pi*(j+1)/28
        r.face([(u+radius*math.cos(a),z0,.07+radius*math.sin(a)),
                (u+radius*math.cos(c),z0,.07+radius*math.sin(c)),
                (u+radius*math.cos(c),z1,.07+radius*math.sin(c)),
                (u+radius*math.cos(a),z1,.07+radius*math.sin(a))],
               normal=(math.cos((a+c)/2),0,math.sin((a+c)/2)))


def _taper(r,u,z0,z1,r0,r1,depth=.07,sides=28):
    """T-2965: a straight-tapered round shaft, radius r0 at z0 narrowing to r1 at z1."""
    rise=(r0-r1)/max(1e-6,z1-z0)
    for j in range(sides):
        a,c=2*math.pi*j/sides,2*math.pi*(j+1)/sides;m=(a+c)/2
        r.face([(u+r0*math.cos(a),z0,depth+r0*math.sin(a)),
                (u+r0*math.cos(c),z0,depth+r0*math.sin(c)),
                (u+r1*math.cos(c),z1,depth+r1*math.sin(c)),
                (u+r1*math.cos(a),z1,depth+r1*math.sin(a))],
               normal=(math.cos(m),rise,math.sin(m)))


def _splayed_base(r,u,z0,z1,w0,w1,depth=.07,fillet=.015):
    """T-2965: sheet 6's angular base, a square block splayed out to the sill.

    A short upright fillet at the sill, then four flat faces leaning in to a square
    top a little wider than the shaft's foot (the joint sheet 6 and the c. 1888 front
    show where shaft and base meet)."""
    rings=((z0,w0),(z0+fillet,w0),(z1,w1))
    corners=((-1,-1),(1,-1),(1,1),(-1,1))
    for (za,wa),(zb,wb) in zip(rings,rings[1:]):
        lean=(wa-wb)/max(1e-6,zb-za)
        for (sa,ta),(sc,tc) in zip(corners,corners[1:]+corners[:1]):
            nu,nd=(sa+sc)/2,(ta+tc)/2
            r.face([(u+sa*wa,za,depth+ta*wa),(u+sc*wa,za,depth+tc*wa),
                    (u+sc*wb,zb,depth+tc*wb),(u+sa*wb,zb,depth+ta*wb)],
                   normal=(nu,lean,nd))
    r.face([(u+s*w1,z1,depth+t*w1) for s,t in corners],normal=(0,1,0))


def cushion(neck,half,t):
    """T-2965: the block capital's section at height t (0 at the neck, 1 at the top).

    The museum's 2013 close-ups show a cubic block, its upper half straight-sided
    under the carved band and its lower half rounded in to the round shaft (a
    cushion). Returns (half-size, superellipse exponent): a circle of the neck's
    radius at the foot, a near-square of the block's half-width from 0.6 up."""
    t=min(1.,max(0.,t));e=math.sin(math.pi/2*min(1.,t/.60))
    # A slight belly under the band, as capital 2's close-up shows.
    return (neck+(half-neck)*e)*(1+.05*math.sin(math.pi*min(1.,t/.85))),2.+8.*e**2


def _section(size,power,th):
    c,s=math.cos(th),math.sin(th)
    return (size*math.copysign(abs(c)**(2/power),c),size*math.copysign(abs(s)**(2/power),s))


def _block(r,u,low,z1,neck,half,depth,sides=32,rows=10):
    """The capital's block, lofted from the neck's circle to its square top."""
    rings=[]
    for k in range(rows+1):
        t=k/rows;size,power=cushion(neck,half,t)
        rings.append([(u+x,low+(z1-low)*t,depth+y) for x,y in
                      (_section(size,power,2*math.pi*(j+.5)/sides) for j in range(sides))])
    for k in range(rows):
        for j in range(sides):
            n=(j+1)%sides;th=2*math.pi*(j+1)/sides
            r.face([rings[k][j],rings[k][n],rings[k+1][n],rings[k+1][j]],
                   normal=(math.cos(th),.2,math.sin(th)))
    r.face(rings[-1],normal=(0,1,0))


def _volute(r,x,z,radius,mirror,depth,turns=1.5,thick=.019,shrink=.82):
    """A flat spiral scroll, coiling inward, as the corners of the 2013 close-ups.

    ``shrink`` is how far in it coils (its eye at radius*(1-shrink)); a smaller block
    (T-3343's north capitals) coils less, so its eye stays wider than the tube is thick
    and K01 does not count the tube's folded rings as coincident faces."""
    path=[]
    for i in range(41):
        t=i/40;th=math.pi*.5+mirror*2*math.pi*turns*t
        rr=radius*(1-shrink*t)
        path.append((x+rr*math.cos(th),z+rr*math.sin(th),depth))
    r.tube(path,lambda t:thick*(1-.4*t),7)


def _band(r,u,z0,z1,half,motif,front):
    """The carved band across the block's top (the 2013 close-ups and sheet 6)."""
    h=z1-z0;zc=(z0+z1)/2;w=half*.92
    if motif=='discs':
        for j in range(5):
            r.bead(u+w*(j-2)/2.4,zc,front,h*.36,1)
        for j in range(4):
            x=u+w*(j-1.5)/2.4
            r.solid([(x-h*.10,zc),(x,zc-h*.26),(x+h*.10,zc),(x,zc+h*.26)],front-.01,front+.012)
    elif motif=='checker':
        n=8;step=2*w/n
        for row in range(2):
            for j in range(n):
                if (j+row)%2:continue
                x0=u-w+j*step;zb=z0+h*(.12+.44*row)
                r.box(x0+step*.08,x0+step*.92,zb,zb+h*.38,front-.012,front+.014)
    elif motif=='diamonds':
        for j in range(5):
            x=u+w*(j-2)/2.4
            r.solid([(x-w*.19,zc),(x,z0+h*.08),(x+w*.19,zc),(x,z1-h*.08)],front-.012,front+.016)
    elif motif=='chevron':
        pts=[(u-w+2*w*i/10,(z0+h*.18) if i%2 else (z1-h*.18),front+.008) for i in range(11)]
        r.tube(pts,.011,7)
        r.tube([(u-w,z0+h*.06,front+.004),(u+w,z0+h*.06,front+.004)],.007,6)
    else:  # 'slots': a dentil row of upright blocks
        n=9;step=2*w/n
        for j in range(n):
            x0=u-w+j*step
            r.box(x0+step*.18,x0+step*.82,z0+h*.10,z1-h*.10,front-.012,front+.014)


def _monogram(r,u,z,radius,d):
    """Richardson's monogram, as the museum records it on the capital over the door:
    two mirrored R's back to back on an H, boxed, inside a large ring."""
    t=.014
    r.arc(u,z,radius,d,t*1.3,0,2*math.pi,48)
    bw,bh=radius*.62,radius*.50
    r.tube([(u-bw,z-bh,d),(u+bw,z-bh,d),(u+bw,z+bh,d),(u-bw,z+bh,d),(u-bw,z-bh,d)],t,6)
    r.tube([(u,z-bh*.85,d+.004),(u,z+bh*.85,d+.004)],t,6)
    r.tube([(u-bw*.8,z+bh*.05,d+.004),(u+bw*.8,z+bh*.05,d+.004)],t*.85,6)
    for m in (-1,1):
        x=u+m*bw*.42
        r.tube([(x,z-bh*.85,d+.004),(x,z+bh*.85,d+.004)],t,6)
        a0,a1=(-math.pi/2,math.pi/2) if m>0 else (math.pi/2,3*math.pi/2)
        r.arc(x+m*bw*.20,z+bh*.45,bw*.22,d+.004,t*.85,a0,a1,12)
        r.tube([(x,z+bh*.05,d+.004),(x+m*bw*.42,z-bh*.85,d+.004)],t*.85,6)


def _lattice(r,u,z,rx,rz,d,pitch):
    """Basket weave inside an oval: two crossing families of straps, over and under."""
    for fam in (-1,1):
        k=-int(2*(rx+rz)/pitch)
        while k*pitch<2*(rx+rz):
            pts=[]
            for i in range(25):
                x=-1.5*rx+3*rx*i/24;zz=fam*(x-k*pitch)*.7
                if (x/rx)**2+(zz/rz)**2<=1:
                    weave=.004*math.sin(math.pi*(i+k)/3)
                    pts.append((u+x,z+zz,d+.006+fam*weave))
            if len(pts)>2:r.tube(pts,.015,6)
            k+=1
    r.tube([(u+rx*math.cos(2*math.pi*i/40),z+rz*math.sin(2*math.pi*i/40),d+.008) for i in range(41)],.016,6)


def _capital(r,u,low,z1,neck,half,spec,depth=.07):
    """T-2965: one Prairie capital, carved to its own picture.

    The block is the 2013 close-ups' cushion; ``spec`` (one of the record's
    prairie_colonnette.capitals, which run south to north) names what each one
    carries, read off HABS sheet 6, which draws all seven, and the museum's three
    2013 close-ups (the monogram capital over the door and its two neighbours): the
    top band (discs, checker, diamonds, chevron or slots), the body (monogram,
    lattice, interlace, roundel, crossing stems or boss), the corner volutes and
    the row of drilled leaf tips. The carving's own cuts are reconstructed."""
    h=z1-.012-low;top=z1-.012
    _block(r,u,low,top,neck,half,depth)
    def face(x,z):
        size,power=cushion(neck,half,(z-low)/h)
        q=min(abs(x-u),size*.999)
        return depth+(size**power-q**power)**(1/power)
    rb=Relief(r.b,r.p,r.conf,r.mat,profile=face)
    F=lambda fx,fz:(u+fx*half,low+fz*h)
    band0=low+h*.80
    front=depth+half
    _band(r,u,band0,top-.006,half,spec.get('band','discs'),front)
    r.tube([(u-half*.96,band0-.004,front+.004),(u+half*.96,band0-.004,front+.004)],.007,6)
    body=spec.get('body','boss')
    if spec.get('volutes',True):
        for m in (-1,1):
            x,z=F(m*.66,.64)
            _volute(rb,x,z,half*.27,-m,.014,shrink=spec.get('volute_shrink',.82))
            # The stem that ends in each volute rises from the block's foot.
            rb.tube([(*F(m*.12,.30),.006),(*F(m*.40,.46),.010),(*F(m*.62,.58),.010),
                     (x+m*half*.02,z+half*.25,.014)],.016,7)
    x,z=F(0,.56)
    if body=='monogram':
        _monogram(rb,x,z,half*.46,.012)
    elif body=='lattice':
        _lattice(rb,x,F(0,.50)[1],half*.60,h*.26,.006,half*.22)
    elif body=='interlace':
        for m in (-1,1):
            rb.tube([(*F(-.55*m,.74),.010),(*F(-.2*m,.56),.016),(*F(.25*m,.40),.010),
                     (*F(.5*m,.30),.006)],.020,7)
        rb.arc(x,z,half*.16,.016,.011,0,2*math.pi,24)
    elif body=='roundel':
        zr=F(0,.52)[1]
        rb.arc(x,zr,half*.46,.014,.018,0,2*math.pi,48)
        for j in range(8):
            th=math.pi*j/4+math.pi/8
            rb.leaf(x+.014*math.cos(th),zr+.014*math.sin(th),th,half*.38,half*.22,.012,.022,
                    .05,False,steps=6)
    elif body=='crossing':
        for m in (-1,1):
            rb.tube([(*F(.45*m,.30),.006),(*F(.05*m,.52),.016),(*F(-.35*m,.70),.014)],.019,7)
        rb.solid([(x-half*.10,z+h*.12),(x,z+h*.02),(x+half*.10,z+h*.12),(x,z+h*.22)],.004,.022)
    else:  # 'boss': a round boss between the stems
        rb.bead(x,z,.010,half*.18,1)
        rb.arc(x,z,half*.26,.012,.014,0,2*math.pi,32)
    if spec.get('leaves',True):
        # Stiff blades rising off the neck, each tip turned over into a curl (the
        # close-ups' lower halves).
        for j in range(4):
            fx=(j-1.5)*.34;m=1 if fx>0 else -1
            x0,z0=F(fx*.55,.10);x1,z1=F(fx,.44)
            rb.leaf(x0,z0,math.atan2(z1-z0,x1-x0),math.hypot(x1-x0,z1-z0),half*.24,.006,.030,
                    -m*.10,False,j*.7,10)
            # The curl stops coiling while its turn is still wider than the tube is
            # thick: tighter, the tube's rings fold into faces K01 counts twice.
            cx,cz,R=x1+m*half*.07,z1-half*.02,half*.08
            rb.tube([(cx+R*(1-.5*t)*math.cos(math.pi*.5+m*2.2*math.pi*t),
                      cz+R*(1-.5*t)*math.sin(math.pi*.5+m*2.2*math.pi*t),.012)
                     for t in (i/16 for i in range(17))],lambda t:.009*(1-.3*t),7)


def colonnette(r,u,z0,z1,gap,spec,cap,reduced=False):
    """T-2965/T-3343: one Glessner colonnette between two lights, z0 sill to z1 head.

    A splayed square base, a straight-tapered round shaft and a carved block capital,
    the round front of a stone mullion flush with the wall's face; ``r`` is a Relief in
    the lights' plane, ``u`` the mullion's centre and ``gap`` the lights' clear spacing.
    ``spec`` is a record stock (prairie_colonnette or north_pair_colonnette): its
    heights are shares of the opening, or ``base_m``/``capital_m`` outright. ``cap`` is
    the capital's own carving. ``reduced`` is the light tier's recipe (fewer facets,
    the band as one raised course and three leaf tips, the body's carving omitted)."""
    h=z1-z0
    foot=spec.get('shaft_foot_m',gap*1.24)/2;neck=spec.get('shaft_neck_m',gap*.98)/2
    half=spec.get('abacus_m',gap*2.3)/2
    base=z0+(spec['base_m'] if 'base_m' in spec else h*spec.get('base_share',.13))
    low=z1-(spec['capital_m'] if 'capital_m' in spec else h*spec.get('capital_share',.33))
    depth=-foot
    r.box(u-gap*.5-.004,u+gap*.5+.004,base,low,-spec.get('mullion_depth_m',.46),depth)
    _splayed_base(r,u,z0,base,spec.get('base_foot_m',gap*1.8)/2,foot+.008,depth)
    if reduced:
        _taper(r,u,base,low,foot,neck,depth,12)
        top=z1-.012;ch=top-low
        _block(r,u,low,top,neck,half,depth,16,5)
        r.box(u-half*.92,u+half*.92,low+ch*.82,top-.01,depth+half-.01,depth+half+.012)
        for j in range(3):
            r.leaf(u+(j-1)*half*.45,low+ch*.12,math.pi*.5+(j-1)*.15,ch*.30,half*.28,
                   depth+neck+(half-neck)*.30,.02,0,False,steps=4)
        return
    _taper(r,u,base,low,foot,neck,depth)
    _capital(r,u,low,z1,neck,half,cap,depth)


def columns(b, params, reduced=False):
    """T-2965: every Prairie colonnette to HABS sheets 3 and 6 and the photographs.

    A splayed square base, a straight-tapered round shaft and a carved block capital,
    the round front of a stone mullion flush with the wall's face (sheet 3), cut in
    the house's granite. Each capital carries its own carving, from the record's
    prairie_colonnette.capitals (south to north)."""
    spec=params.detail.get('prairie_colonnette') or {}
    caps=spec.get('capitals') or []
    ops=sorted([o for o in params.openings if o['kind']=='window' and
                o['face']=='east' and o['z0']>5],
               key=lambda o:(round(o['at'],3),round(o['z0'],2),o['u0']))
    n=0
    for a,c in zip(ops,ops[1:]):
        gap=c['u0']-a['u1']
        if not .12<gap<.3 or abs(a['z0']-c['z0'])>.05 or abs(a['at']-c['at'])>.05:
            continue
        u=(c['u0']+a['u1'])/2
        r=Relief(b,a,params.detail.get('conf',max(a['conf'],c['conf'])),CARVED_GRANITE)
        # The openings run north to south along u (u grows northward); the record
        # lists the capitals south to north, so they are taken in the same order.
        colonnette(r,u,a['z0'],a['z1'],gap,spec,caps[n] if n<len(caps) else {},reduced)
        n+=1


def north_pairs(b, params, conf):
    """T-3343: the two 18th Street pairs' colonnettes, the front's kind (HABS 13/14).

    Each north_gable_pair is two lights either side of a colonnette; the record's
    north_pair_colonnette holds their stock and, east to west, each capital's carving."""
    spec=params.detail.get('north_pair_colonnette') or {}
    caps=spec.get('capitals') or []
    ops=sorted([o for o in params.openings if o.get('style')=='north_gable_pair'],key=lambda o:o['u0'])
    reduced=getattr(b,'reduced_sash',False)
    pairs=[(a,c) for a,c in zip(ops,ops[1:]) if .1<c['u0']-a['u1']<.65]
    # u grows eastward along the north wall; the record lists the capitals east to
    # west (W from Prairie, as HABS 13 reads them right to left), so walk u backwards.
    for n,(a,c) in enumerate(reversed(pairs)):
        r=Relief(b,a,conf,CARVED_GRANITE)
        colonnette(r,(a['u1']+c['u0'])/2,a['z0'],a['z1'],c['u0']-a['u1'],spec,
                   caps[n] if n<len(caps) else {},reduced)


def build_entry_ornament(b, params, part='all'):
    """Optional single entry point; call instead of the corresponding old details."""
    for o in params.openings:
        if o['face']!='east':
            continue
        if part in ('all','fan') and o['kind']=='fan':
            fan(b,o)
        elif part in ('all','sill') and o['kind']=='band' and o['z0']>5 and o['u1']-o['u0']>3:
            sill(b,o)
    if part in ('all','columns'):
        columns(b,params)
