"""Opt-in Glessner v4 surface construction; legacy records never enter this module.

The record owns all major dimensions and the HABS ashlar course schedule. This
module owns the declared, reconstructed drawing scale: millimetre mortar joints,
rock-face relief, timber sash, metal seams, and overlapping individual roof tiles.
They are actual glTF geometry, batched in one object, rather than renderer tricks.
Apertures are subtracted from both stone/brick and mortar before reveals are built.

The deterministic microgeometry is NOT a claim to reproduce individual historic
stones. It is a reconstruction bounded by the facade photographs; see T-1730 and
LIBERTIES. No photographs are projected onto the model.
"""
from __future__ import annotations

import math
import random

from common.mesh import MeshBuilder
from archetypes import masonry_house as legacy
from archetypes import masonry_house_v4_ornament as ornament

GRANITE, BRICK, TRIM, ROOF, COPPER, GLASS, WOOD, LAWN, DRIVE = range(9)
MORTAR, IRON, DARK_GLASS = 9, 10, 11
PAINTED_WOOD = 23
ROUGH_TRIM = 24


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def norm(a):
    length = math.sqrt(dot(a, a)) or 1
    return tuple(v/length for v in a)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def area(poly):
    return sum(p[0]*q[1]-q[0]*p[1] for p, q in zip(poly, poly[1:]+poly[:1]))/2


def clean(poly):
    result = []
    for p in poly:
        if not result or math.dist(p, result[-1]) > 1e-7:
            result.append(p)
    if len(result) > 1 and math.dist(result[0], result[-1]) < 1e-7:
        result.pop()
    return result if len(result) >= 3 and abs(area(result)) > 1e-8 else []


def clip(poly, a, b, inside=True):
    """Clip in the first two coordinates, interpolating any vertex attributes.

    Relief surfaces carry depth as a third coordinate. Keeping it through a
    cut preserves the original stone's plane across computational fragments.
    """
    if not poly:
        return []
    sign = 1 if inside else -1
    def distance(p):
        return sign*((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
    out = []
    for p, q in zip(poly, poly[1:]+poly[:1]):
        dp, dq = distance(p), distance(q)
        ip, iq = dp >= -1e-9, dq >= -1e-9
        if ip:
            out.append(p)
        if ip != iq:
            t = dp/(dp-dq)
            out.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(len(p))))
    return clean(out)


def rect_clip(poly, x0, y0, x1, y1):
    for a, b in [((x0,y0),(x1,y0)), ((x1,y0),(x1,y1)),
                 ((x1,y1),(x0,y1)), ((x0,y1),(x0,y0))]:
        poly = clip(poly, a, b)
    return poly


def bounds(poly):
    return min(p[0] for p in poly), min(p[1] for p in poly), max(p[0] for p in poly), max(p[1] for p in poly)


def remove_hole(poly, hole):
    """Disjoint convex fragments of poly outside a convex aperture."""
    if not poly:
        return []
    a,b,c,d = bounds(poly)
    e,f,g,h = bounds(hole)
    if c <= e or a >= g or d <= f or b >= h:
        return [poly]
    if area(hole) < 0:
        hole = list(reversed(hole))
    remainder, result = poly, []
    for a,b in zip(hole, hole[1:]+hole[:1]):
        outside = clip(remainder,a,b,False)
        if outside:
            result.append(outside)
        remainder = clip(remainder,a,b,True)
        if not remainder:
            break
    return result


def subtract(poly, holes):
    fragments = [poly]
    for hole in holes:
        fragments = [piece for p in fragments for piece in remove_hole(p,hole)]
    return fragments


def ringed(o):
    """Openings whose voussoir ring() lays radiating stones in the wall."""
    if o.get('r_out',0)<=(o['u1']-o['u0'])/2+.05:
        return False
    return o.get('style')=='north_entry_alcove' or (o['kind']=='arch' and o.get('style')!='pigeon_vent')


def through_passage(o):
    """The porte-cochere's court mouth: a through passage, not a panel of black glazing."""
    return (o['kind']=='dark' and o.get('face')=='west' and o.get('at',0)>30
            and o['z0']<.1 and o['u1']-o['u0']>2)


def aperture(o):
    a,b,z0,z1 = o['u0'],o['u1'],o['z0'],o['z1']
    if o['kind'] == 'arch':
        c,r,zs = (a+b)/2,(b-a)/2,o['spring_z']
        return [(a,z0),(b,z0)] + [(c+r*math.cos(math.pi*i/24),zs+r*math.sin(math.pi*i/24)) for i in range(25)]
    return [(a,z0),(b,z0),(b,z1),(a,z1)]


PITCH_LINE, PITCH_MARGIN = .016, .085
# T-2209 (reconstructed): the 7.5 cm lattice and its random diagonal are a
# computational mesh of one continuous rock face, not fractures. At 35 degrees a
# fifth of the shared facet corners kept a hard crease, so every lattice triangle
# lit as its own flat chip: the "triangulated sparkle" of the GA-09 audit. Only a
# chip steeper than this still keeps a hard ridge; the face's relief is unmoved.
ROCK_SMOOTH_DEGREES = 60
# T-2208 follow-up (owner, 2026-10-12, with six photographs of the Prairie Avenue
# front and its entrance): "they are more like shaped almost with a bow in the
# front, not a ton, but your stone facing I think is too flat". A quarry-faced
# stone is not a plateau with a chamfer: from its pitched arris the face rises
# steeply and then rounds over a crown, so each stone throws its own shadow on
# the joint below it. BOW_* set that crown above the pitch line, scaled to the
# stone's short side (a 7.5 in course bows less than an 18 in one) and capped.
# Reconstructed from the owner's photographs; no projection was measured.
BOW_PER_SHORT_SIDE, BOW_BASE, BOW_MIN, BOW_MAX = .12, .018, .030, .060
# The crown sits a little below the middle of the course, so the lower face is
# the steeper one, as the photographs' dark lower lips show.
BOW_PEAK = .44
# Highest point any rock face reaches in front of its wall plane. Lintels and
# voussoirs laid over the field (masonry_house_v4_north.rough_stone) sit in
# front of it.
ROCK_FACE_MAX = .104
# T-3045: a face piece under this in every direction is dropped as a clipping crumb.
CRUMB_M = .0025


def _segment_distance(x, y, a, b):
    ex,ey=b[0]-a[0],b[1]-a[1]
    length=ex*ex+ey*ey
    t=0.0 if length<1e-18 else max(0.0,min(1.0,((x-a[0])*ex+(y-a[1])*ey)/length))
    return math.hypot(x-a[0]-t*ex,y-a[1]-t*ey)


def _edge_distance(x, y, polygon):
    return min(_segment_distance(x,y,a,b) for a,b in zip(polygon,polygon[1:]+polygon[:1]))


def _rise(t):
    """Steep off the arris, round over the crown: 0 at the edge, 1 at the top."""
    t=min(1.0,max(0.0,t))
    return 1-(1-t)**2.2


def _inside(x, y, poly):
    """Even-odd point in polygon, for whether a course run lies in an aperture."""
    inside=False
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x<ax+(y-ay)*(bx-ax)/(by-ay):
            inside=not inside
    return inside


def fractured_stone(polygon, depth, rng, spacing=.075, crown=None, crown_scale=1.0, lip=None):
    """Reconstructed split-face stone, bounded to the existing block envelope.

    The measured facade owns courses and openings; these 7.5 cm fracture facets
    describe surface finish only. The face is pitched to a straight arris at
    every edge and bowed over a crown between them (BOW_*); correlated relief
    breaks the bow into split planes without independent spikes. The perimeter
    stays inside the original stone. No new joints appear where an aperture
    cuts it. ``crown`` overrides the bow height for a stone of known shape.
    ``crown_scale`` and ``lip`` are a course's own (T-3046): the bow is raised by
    the scale, and a rectangular stone's lower face rises to the crown over at
    most ``lip`` metres, however tall the course.
    """
    x0,y0,x1,y1=bounds(polygon)
    nx=max(2,math.ceil((x1-x0)/spacing));ny=max(2,math.ceil((y1-y0)/spacing))
    dx,dy=(x1-x0)/nx,(y1-y0)/ny
    rectangular=(len(polygon)==4 and len({round(q[0],6) for q in polygon})==2 and
                 len({round(q[1],6) for q in polygon})==2)
    # Random lattice values at two physical scales. Interpolation correlates
    # neighbours; the small independent term gives the exposed split planes.
    fields=[]
    for scale,amplitude in ((.27,.011),(.115,.013)):
        values={(ix,iy):rng.uniform(-1,1)
                for ix in range(-1,math.ceil((x1-x0)/scale)+3)
                for iy in range(-1,math.ceil((y1-y0)/scale)+3)}
        fields.append((scale,amplitude,values))
    # The bow: rectangular stones crown along both axes; a wedge (a voussoir)
    # crowns on its distance from its own sides, out to its inscribed radius.
    if rectangular:
        short=min(x1-x0,y1-y0)
        reach_x=min(.5*(x1-x0),.42)
        reach=None
    else:
        reach=max(_edge_distance(x0+(ix+.5)*(x1-x0)/12,y0+(iy+.5)*(y1-y0)/12,polygon)
                  for ix in range(12) for iy in range(12)
                  if _inside(x0+(ix+.5)*(x1-x0)/12,y0+(iy+.5)*(y1-y0)/12,polygon))
        reach=max(.02,reach)
        short=2*reach
    height=crown if crown is not None else min(BOW_MAX,max(BOW_MIN,BOW_PER_SHORT_SIDE*short+BOW_BASE))
    if crown_scale!=1.0:
        height*=crown_scale
    height*=.86+.28*min(1.0,max(0.0,(depth-.008)/.038))
    def bow(x,y):
        if rectangular:
            low,high=BOW_PEAK*(y1-y0),(1-BOW_PEAK)*(y1-y0)
            if lip is not None and lip<low:
                low,high=lip,(y1-y0)-lip
            across=_rise(min(x-x0,x1-x)/reach_x)
            up=min(_rise((y-y0)/low),_rise((y1-y)/high))
            return (across*up)**.85
        return _rise(_edge_distance(x,y,polygon)/reach)
    def relief(x,y,boundary=False):
        # T-2208 (reconstructed): a rock-faced stone is pitched to a straight
        # arris before it is set, so its face falls to a pitch line at every
        # edge and the joint reads as a line at street distance. The arris sits
        # 16 mm proud, the front of an opening's reveal, so a jamb stone meets
        # its return flush.
        if boundary:
            return PITCH_LINE
        if not rectangular and not _inside(x,y,polygon):
            # A lattice point beyond a wedge's side continues the bow's slope
            # below the arris, so the clipped edge lands on the pitch line.
            return PITCH_LINE-2.2*height*_edge_distance(x,y,polygon)/reach
        rough=0.0
        for scale,amplitude,values in fields:
            u,v=(x-x0)/scale,(y-y0)/scale
            i,j=math.floor(u),math.floor(v);a,b=u-i,v-j
            rough+=amplitude*((1-a)*(1-b)*values[i,j]+a*(1-b)*values[i+1,j]+
                              (1-a)*b*values[i,j+1]+a*b*values[i+1,j+1])
        rough+=rng.uniform(-.006,.006)
        edge=(min(x-x0,x1-x,y-y0,y1-y) if rectangular else _edge_distance(x,y,polygon))
        t=min(1.0,max(0.0,edge/PITCH_MARGIN))
        t=t*t*(3-2*t)
        value=PITCH_LINE+height*bow(x,y)+rough*t
        return min(ROCK_FACE_MAX,max(.006,value))
    grid={};anchors={}
    for ix in range(nx+1):
        for iy in range(ny+1):
            x=x0+ix*dx;y=y0+iy*dy
            # Jitter is a fraction of one cell, so refinement never creates
            # crossed rows/bow-ties or the long sliver wedges of whole-block jitter.
            if 0<ix<nx:x+=rng.uniform(-.22,.22)*dx
            if 0<iy<ny:y+=rng.uniform(-.22,.22)*dy
            anchors[ix,iy]=(x,y,-.009)
            # Small local chips eat into the face, never expand the course or
            # narrow its nominal 14 mm joint. Keep corners within the same bounds.
            edge=ix in (0,nx) or iy in (0,ny)
            if rectangular:
                if ix==0:x+=rng.uniform(.001,.011)
                elif ix==nx:x-=rng.uniform(.001,.011)
                if iy==0:y+=rng.uniform(.001,.009)
                elif iy==ny:y-=rng.uniform(.001,.009)
            grid[ix,iy]=(x,y,relief(x,y,boundary=edge and rectangular))
    for ix in range(nx):
        for iy in range(ny):
            a,b,c,d=grid[ix,iy],grid[ix+1,iy],grid[ix+1,iy+1],grid[ix,iy+1]
            facets=((a,b,d),(b,c,d)) if rng.random()<.5 else ((a,b,c),(a,c,d))
            for facet in facets:
                clipped=list(facet)
                for pa,pb in zip(polygon,polygon[1:]+polygon[:1]):
                    clipped=clip(clipped,pa,pb)
                if not clipped:continue
                yield clipped,True
                # Only physical stone-boundary edges close to the mortar bed.
                # Computational grid edges remain one continuous rock surface.
                for qa,qb in ([] if rectangular else zip(clipped,clipped[1:]+clipped[:1])):
                    for pa,pb in zip(polygon,polygon[1:]+polygon[:1]):
                        ex,ey=pb[0]-pa[0],pb[1]-pa[1]
                        if (abs(ex*(qa[1]-pa[1])-ey*(qa[0]-pa[0]))<1e-8 and
                            abs(ex*(qb[1]-pa[1])-ey*(qb[0]-pa[0]))<1e-8):
                            yield [(qa[0],qa[1],-.009),(qb[0],qb[1],-.009),qb,qa],False
                            break
    if rectangular:
        ring=([(ix,0) for ix in range(nx+1)]+[(nx,iy) for iy in range(1,ny+1)]+
              [(ix,ny) for ix in range(nx-1,-1,-1)]+[(0,iy) for iy in range(ny-1,0,-1)])
        for a,b in zip(ring,ring[1:]+ring[:1]):
            yield [anchors[a],anchors[b],grid[b],grid[a]],False


def stone_corner_normals(facets, angle_degrees=ROCK_SMOOTH_DEGREES):
    """Area-weighted shallow-fracture normals, confined to one physical stone.

    Side faces never participate. The finished facet positions are untouched;
    clipping carries these corner normals with depth, so cutting an opening adds
    neither a shading seam nor a smooth transition into its separate reveal.
    """
    facets=list(facets);at_vertex={};face_normals={}
    for index,(poly,is_front) in enumerate(facets):
        if not is_front:continue
        weighted=tuple(sum(cross(sub(poly[j],poly[0]),sub(poly[j+1],poly[0]))[k]
                           for j in range(1,len(poly)-1)) for k in range(3))
        face_normals[index]=(norm(weighted),weighted)
        for p in poly:
            at_vertex.setdefault(tuple(round(q,9) for q in p),[]).append(index)
    limit=math.cos(math.radians(angle_degrees))
    for index,(poly,is_front) in enumerate(facets):
        if not is_front:
            yield poly,False
            continue
        own,_=face_normals[index];corners=[]
        for p in poly:
            neighbours=at_vertex[tuple(round(q,9) for q in p)]
            eligible=[face_normals[j][1] for j in neighbours
                      if dot(own,face_normals[j][0])>=limit]
            averaged=norm(tuple(sum(v[k] for v in eligible) for k in range(3)))
            corners.append((*p,*averaged))
        yield corners,True


class DetailBuilder(MeshBuilder):
    def __init__(self, name, params):
        super().__init__(name)
        self.params = params
        self.decorate = True
        self.rock_normals = {}
        self.smooth_rock_faces = True
        self.openings = list(params.openings)
        # The Prairie upper colonnades are open between the individual lights.
        # Remove the square masonry piers, then draw the round colonnettes below.
        upper = sorted([o for o in params.openings if o['kind']=='window' and
                        o['face']=='east' and o['z0']>5], key=lambda o:(round(o['at'],3),round(o['z0'],2),o['u0']))
        for a,c in zip(upper,upper[1:]):
            if .12<c['u0']-a['u1']<.3 and abs(a['z0']-c['z0'])<.05 and abs(a['at']-c['at'])<.05:
                self.openings.append({**a,'u0':a['u1']-.001,'u1':c['u0']+.001,
                                      'z0':a['z0']+.05,'z1':a['z1']-.035})
        north_pairs=sorted([o for o in params.openings if o.get('style')=='north_gable_pair'],key=lambda o:o['u0'])
        for a,c in zip(north_pairs,north_pairs[1:]):
            if .1<c['u0']-a['u1']<.65:
                self.openings.append({**a,'u0':a['u1']-.001,'u1':c['u0']+.001,
                                      'z0':a['z0']+.06,'z1':a['z1']-.035})
        self.course_schedule = params.detail.get('ashlar_courses_m') or [0.4572,0.4572,0.3937,0.2413,0.3429,0.3683,0.1905,0.3683,0.1905,0.2921]
        self.masonry_blocks = self.roof_tiles = 0
        self.roof_uvs = {}
        self.roof_detail = {}
        self.roof_surfaces = []

    def add_box(self,x0,y0,z0,x1,y1,z1,confidence,mat=0,skip=()):
        # Correct outward winding locally. The legacy helper's inward box faces
        # would put the v4 relief behind the mortar bed on chimney stacks.
        faces={
            'bottom':[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],
            'top':[(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
            'front':[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],
            'back':[(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],
            'left':[(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)],
            'right':[(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)]}
        centre=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
        for name,pts in faces.items():
            if name in skip:continue
            midpoint=tuple(sum(p[k] for p in pts)/4 for k in range(3))
            if dot(legacy._normal(pts),sub(midpoint,centre))<0:pts.reverse()
            self.add_poly(pts,confidence,mat)

    def raw(self, pts, confidence, mat, want=None):
        if want is not None and dot(legacy._normal(pts),want) < 0:
            pts = list(reversed(pts))
        return super().add_poly(pts,confidence,mat)

    def raw_with_normals(self, pts, normals, confidence, mat, want=None):
        if want is not None and dot(legacy._normal(pts),want)<0:
            pts=list(reversed(pts));normals=list(reversed(normals))
        indices=self.raw(pts,confidence,mat)
        if want is not None:
            # T-2209: a rock facet takes its metric UV in its WALL's plane, not its
            # own. assign_metric_uvs projects each face on its own normal, and a
            # facet tilted 10 degrees, metres from the origin, then shifted its
            # crystal albedo by metres: every lattice triangle showed an unrelated
            # patch with a hard seam. One frame per stone keeps the stone's grain
            # continuous. roof_uvs is the existing per-vertex override (metres).
            horizontal=(-want[1],want[0],0.0)
            length=math.hypot(horizontal[0],horizontal[1])
            if length<1e-6:
                horizontal,uphill=(1.0,0.0,0.0),(0.0,1.0,0.0)
            else:
                horizontal=(horizontal[0]/length,horizontal[1]/length,0.0)
                uphill=norm(cross(norm(want),horizontal))
                if uphill[2]<0:
                    uphill=tuple(-v for v in uphill);horizontal=tuple(-v for v in horizontal)
            for index in indices:
                self.roof_uvs[index]=(dot(self.verts[index],horizontal),dot(self.verts[index],uphill))
        if self.smooth_rock_faces:
            for index,normal in zip(indices,normals):
                self.rock_normals[index]=norm(normal)
        return indices

    def to_object(self, materials=None):
        ob=super().to_object(materials)
        # Exposed course in metres on relief only; zero protects beds and crests.
        attr=ob.data.attributes.new(name="_ROOF_DETAIL",type="FLOAT",domain="POINT")
        for index,value in self.roof_detail.items():attr.data[index].value=value
        if self.rock_normals:
            # Vertices remain separate at material/UV/confidence seams. Explicit
            # corner normals survive glTF without welding geometry or attributes.
            for poly in ob.data.polygons:
                if any(i in self.rock_normals for i in poly.vertices):
                    poly.use_smooth=True
            normals=[self.rock_normals.get(loop.vertex_index,(0,0,0))
                     for loop in ob.data.loops]
            ob.data.normals_split_custom_set(normals)
        return ob

    def add_poly(self, points, confidence, mat=0):
        pts = [tuple(p) for p in points]
        n = norm(legacy._normal(pts))
        if self.decorate and mat in (GRANITE,BRICK) and abs(n[2]) < .005:
            self.wall(pts,confidence,mat)
            return []
        if mat == ROOF and 1e-6 < n[2] < .999999:
            self.tiles(pts,confidence)
            return []
        return self.raw(pts,confidence,mat)

    def wall(self, pts, confidence, mat, custom_holes=None):
        n = norm(legacy._normal(pts))
        u = (-n[1],n[0],0)
        d = dot(pts[0],n)
        polygon = clean([(dot(p,u),p[2]) for p in pts])
        if not polygon:
            return
        if area(polygon)<0:
            polygon.reverse()
        def point(q,off=0):
            return (u[0]*q[0]+n[0]*(d+off),u[1]*q[0]+n[1]*(d+off),q[1])
        from archetypes.masonry_house_v4_entry import wall_mapping
        point=wall_mapping(self,point,n,d,mat)
        holes = []
        for o in self.openings:
            on = legacy._plane_dir(o)
            if dot(n,on)<.999 or abs(dot(legacy._plane_point(o,0,0),n)-d)>.055:
                continue
            if o['kind']=='fan':
                # Carved stone is seated inside the masonry, not overlaid on
                # rock faces. Its recessed bed closes the radial stone joints.
                centre=(o['u0']+o['u1'])/2;radius=o['r_out'];stilt=o.get('stilt',0.)
                cut=[(centre+radius*math.cos(math.pi*i/80),
                      o['spring_z']+stilt+radius*math.sin(math.pi*i/80)) for i in range(81)]
                if stilt>0:
                    # T-2853: the stilted fan's springers run plumb to the spring line.
                    cut=[(centre+radius,o['spring_z'])]+cut+[(centre-radius,o['spring_z'])]
            elif o['kind']=='band':
                if o.get('style')=='rock_faced_lintel':
                    from archetypes.masonry_house_v4_entry import lintel_outline,settings
                    cut=lintel_outline(o,settings(self))
                elif not (o.get('face')=='east' and o['z0']>5 and o['u1']-o['u0']>3):
                    continue
                else:
                    out=o.get('terminal',.44)-.005
                    cut=[(o['u0']-out,o['z0']-.025),(o['u1']+out,o['z0']-.025),
                         (o['u1']+out,o['z1']+.045),(o['u0']-out,o['z1']+.045)]
            elif ringed(o):
                # The voussoir ring is cut from the courses like the fan, so its
                # rock faces stand on their own bed, not on the field's crowns.
                # Two convex holes: the opening itself and the ring's half disc.
                centre=(o['u0']+o['u1'])/2;radius=o['r_out'];zs=o['spring_z']
                holes.append([(dot(legacy._plane_point(o,s,z),u),z) for s,z in aperture(o)])
                cut=[(centre+radius*math.cos(math.pi*i/48),zs+radius*math.sin(math.pi*i/48))
                     for i in range(49)]
            elif through_passage(o) and self.params.detail.get('underpass'):
                # T-3218: the mouth's foot is sheet 4's lawn line on north grade, 0.2 ft
                # over the model's grade where this wall's bottom course starts, and the
                # passage floor is sunk below both (T-2976/T-2978). Cut down to the
                # underpass floor, or that course hangs across the mouth as a brick bar.
                floor=self.params.detail['underpass']['floor_z']
                cut=aperture({**o,'z0':min(o['z0'],floor)})
            else:
                cut=aperture(o)
            holes.append([(dot(legacy._plane_point(o,s,z),u),z) for s,z in cut])
        for h in custom_holes or []:
            holes.append([(dot(p,u),p[2]) for p in h])
        for fragment in subtract(polygon,holes):
            fragments=getattr(point,'partition',lambda poly,conf,mat:[(poly,point)])(
                [(*q,-.012) for q in fragment],confidence,MORTAR)
            for piece,mapper in fragments:
                self.raw([mapper(q[:2],q[2]) for q in piece],max(confidence,getattr(mapper,'confidence',confidence)),MORTAR,n)
        x0,z0,x1,z1 = bounds(polygon)
        courses = []
        # The granite string starts at its own origin (T-2955: north grade); a caller's
        # course_origin (a chimney's single course) and brick keep theirs.
        own = hasattr(self, 'course_origin')
        z = getattr(self, 'course_origin', 0.0 if mat == BRICK else
                    self.params.detail.get('ashlar_origin_m', 0.0))
        # The bottom course runs down to the model's grade, so a raised origin leaves no
        # uncoursed strip at the foot of a wall.
        floor = z if own else min(z, 0.0)
        idx = 0
        while z < z1+1e-6:
            height = .066675 if mat == BRICK else self.course_schedule[idx%len(self.course_schedule)]
            if z+height > z0:
                courses.append((idx,max(floor if idx == 0 else z,z0),min(z+height,z1)))
            z += height
            idx += 1
        for row,za,zb in courses:
            if zb-za<.004:
                continue
            rng = random.Random(87013+row*719+int(d*997)+mat*821)
            if mat != BRICK:
                # T-3046: the house's own string carries each course's crown; a
                # caller's course_origin (a chimney band, the cupola) keeps the bow.
                crowns = None if own else self.params.detail.get('ashlar_course_crowns')
                course = crowns[row%len(crowns)] if crowns else None
                self.ashlar_course(polygon,holes,row,za,zb,point,n,confidence,mat,rng,course=course)
                continue
            width = .2159
            start = math.floor(x0/width)*width-(width/2 if row%2 else 0)
            a = start
            while a < x1-1e-6:
                c = a+width
                gap = .009
                tile = rect_clip(polygon,a+gap/2,za+gap/2,c-gap/2,zb-gap/2)
                if tile:
                    # A clipped fragment is not another physical stone. Build
                    # this stone once, then clip its already-finished surfaces.
                    self.block(tile,point,n,confidence,mat,rng,holes=holes)
                a = c

    def ashlar_course(self, polygon, holes, row, za, zb, point, n, confidence, mat, rng, course=None):
        """One rock-faced course, laid from its ends and its opening jambs inward.

        T-2208 (reconstructed): the course is cut wherever a straight aperture jamb
        crosses it, so a jamb is the end face of a whole stone rather than a sliver
        the aperture happened to leave; the stone runs to the reveal with no joint.
        Every run then alternates a long and a short stone at each end by course
        (a bonded corner/jamb, never joints stacked over each other), and fills its
        middle with whole stones scaled to the run, so no run ends in a sliver.
        """
        x0,_,x1,_ = bounds(polygon)
        strip = rect_clip(polygon,x0-1,za,x1+1,zb)
        if not strip:
            return
        lo,_,hi,_ = bounds(strip)
        mid = (za+zb)/2
        jambs = []
        for hole in holes:
            for (ua,va),(ub,vb) in zip(hole,hole[1:]+hole[:1]):
                if abs(ua-ub)<1e-6 and min(va,vb)-.02<=za and zb<=max(va,vb)+.02:
                    jambs.append(ua)
        cuts = sorted({round(u,6) for u in jambs if lo+.05<u<hi-.05})
        width = .85+min(.45,(zb-za)*.4)
        gap = .014
        for s0,s1 in zip([lo]+cuts,cuts+[hi]):
            if s1-s0<.03:
                continue
            centre = (s0+s1)/2
            # Only a run lying wholly across one aperture is empty. A long run
            # whose middle merely falls in another, shorter opening is still
            # laid; that opening clips its stones as before.
            if any(bounds(h)[0]-1e-6<=s0 and s1<=bounds(h)[2]+1e-6 and
                   _inside(centre,mid,h) for h in holes):
                continue
            s0_jamb = s0 in cuts
            s1_jamb = s1 in cuts
            length = s1-s0
            count = max(1,round(length/width))
            if count == 1:
                sizes = [length]
            else:
                # Long/short at the two ends by course parity, then whole stones.
                head = width*(1.3 if row%2==0 else .62)
                tail = width*(.62 if row%2==0 else 1.3)
                middle = [rng.uniform(.7,1.35)*width for _ in range(max(0,count-2))]
                sizes = [head]+middle+[tail]
                scale = length/sum(sizes)
                sizes = [w*scale for w in sizes]
            a = s0
            for i,w in enumerate(sizes):
                c = a+w
                # A jamb stone runs to the reveal: its end face IS the return.
                left = a+(0 if (i==0 and s0_jamb) else gap/2)
                right = c-(0 if (i==len(sizes)-1 and s1_jamb) else gap/2)
                tile = rect_clip(polygon,left,za+gap/2,right,zb-gap/2)
                if tile:
                    self.block(tile,point,n,confidence,mat,rng,holes=holes,**({'course':course} if course else {}))
                a = c

    def block(self, polygon, point, normal, confidence, mat, rng, holes=None, course=None):
        if len(polygon)<3:
            return
        x0,y0,x1,y1 = bounds(polygon)
        if min(x1-x0,y1-y0)<.002:
            return
        nearby=[]
        for hole in holes or []:
            ha,hb,hc,hd=bounds(hole)
            if x1>ha and x0<hc and y1>hb and y0<hd:
                nearby.append(hole)
        emitted=False

        def surface(poly, facing=normal):
            """Cut finished facets without adding bevels at partition edges."""
            nonlocal emitted
            # Triangulate before clipping: an uneven quad is not one plane.
            # Every resulting fragment then retains its parent's exact plane,
            # colour, depth and metric UV frame, so internal cuts are invisible.
            pieces=([poly] if not nearby else
                    [part for i in range(1,len(poly)-1)
                     for part in subtract([poly[0],poly[i],poly[i+1]],nearby)])
            partitions=[]
            for piece in pieces:
                partitions.extend(getattr(point,'partition',lambda poly,conf,mat:[(poly,point)])(piece,confidence,variant))
            for piece,mapper_point in partitions:
                piece_conf=max(confidence,getattr(mapper_point,'confidence',confidence))
                pts=[mapper_point((q[0],q[1]),q[2]) for q in piece]
                # T-3045: a facet clipped at a partition line can leave a crumb a
                # millimetre or two across; the fan over it comes out as two faces
                # back to back on K01's 1 mm lattice. Nothing that small is seen.
                if max(max(q[k] for q in pts)-min(q[k] for q in pts) for k in range(3))<CRUMB_M:
                    continue
                if not emitted:
                    self.masonry_blocks+=1
                    emitted=True
                if len(piece[0])>3:
                    mapper=getattr(mapper_point,'normal',None)
                    if mapper:
                        normals=[mapper(q) for q in piece]
                    else:
                        origin=mapper_point((0,0),0)
                        basis=(sub(mapper_point((1,0),0),origin),sub(mapper_point((0,1),0),origin),
                               sub(mapper_point((0,0),1),origin))
                        normals=[tuple(sum(q[j+3]*basis[j][k] for j in range(3))
                                       for k in range(3)) for q in piece]
                    self.raw_with_normals(pts,normals,piece_conf,variant,facing)
                else:
                    self.raw(pts,piece_conf,variant,facing)

        cx,cy = sum(p[0] for p in polygon)/len(polygon),sum(p[1] for p in polygon)/len(polygon)
        bevel = .005 if mat==BRICK else .012
        depth = rng.uniform(.001,.006) if mat==BRICK else rng.uniform(*self.params.detail['ashlar_relief_m'])
        if mat==BRICK:
            firing=rng.random()
            variant=BRICK if firing<.60 else (16 if firing<.80 else (17 if firing<.94 else 18))
        else:
            variant=mat if mat in (TRIM,ROUGH_TRIM) else 12+rng.randrange(4)
        inner = []
        for x,y in polygon:
            dx,dy=x-cx,y-cy
            # A bounded chamfer, never a change to the measured wall/opening outline.
            tx=max(0,abs(dx)-min(bevel,abs(dx)*.15))
            ty=max(0,abs(dy)-min(bevel,abs(dy)*.15))
            inner.append((cx+math.copysign(tx,dx),cy+math.copysign(ty,dy)))
        if mat==BRICK:
            # A single relief face per brick; the recessed continuous mortar bed
            # closes the wall. Invisible backs and microscopic internal bevels
            # are intentionally omitted from the shipped inspection model.
            surface([(*q,depth) for q in polygon])
            return
        # Physical fracture scale is metric, not a fixed handful of facets per
        # stone. Work on the complete stone and only then cut finished facets.
        rectangular=len(polygon)==4 and len({round(q[0],6) for q in polygon})==2 and len({round(q[1],6) for q in polygon})==2
        if x1-x0>.48 and y1-y0>.16 and mat != TRIM:
            fracture_rng=random.Random()
            fracture_rng.setstate(rng.getstate())
            # Preserve the existing coursing RNG: wall() uses it to choose the
            # next block width. Refining a face must not move any stone joint.
            consumed=52 if rectangular else len(polygon)+(len(polygon)<=6)
            for _ in range(consumed):rng.random()
            for facet,is_front in stone_corner_normals(fractured_stone(polygon,depth,fracture_rng,**(course or {}))):
                surface(facet,normal if is_front else None)
            return
        back=[(*q,-.009) for q in polygon]
        front=[(*q,depth+rng.uniform(-.001,.001)) for q in inner]
        for i in range(len(polygon)):
            j=(i+1)%len(polygon)
            surface([back[i],back[j],front[j],front[i]],None)
        if mat==BRICK or len(polygon)>6:
            surface(front)
        else:
            # Broken stone has an uneven face without rounded cobblestone silhouettes.
            center=(cx,cy,depth+rng.uniform(.001,.009))
            for i in range(len(front)):
                surface([front[i],front[(i+1)%len(front)],center])

    def roof_frame(self, pts):
        """Metre coordinates on the HOST slope, shared across clipped fragments.

        Global height fixes course phase on equal-pitch cone facets; using each
        raised tile's normal would drift the UVs away from its host courses.
        """
        normal=norm(legacy._normal(pts))
        uphill=norm((-normal[0]*normal[2],-normal[1]*normal[2],1-normal[2]*normal[2]))
        u=norm(cross(uphill,normal));distance=dot(pts[0],normal)
        offset=normal[2]*distance/uphill[2]
        def coords(p):return (dot(p,u),dot(p,uphill)+offset)
        def point(q,off=0):
            return tuple(u[k]*q[0]+uphill[k]*(q[1]-offset)+normal[k]*(distance+off) for k in range(3))
        poly=[coords(p) for p in pts]
        if area(poly)<0:poly.reverse()
        self.roof_surfaces.append({'points':pts,'area_m2':abs(area(poly)),
                                   'normal':normal,'phase_offset':offset})
        return normal,poly,point,coords

    def roof_raw(self, pts, confidence, mat, normal, coords, detail=False):
        indices=self.raw(pts,confidence,mat,normal)
        for index in indices:
            self.roof_uvs[index]=coords(self.verts[index])
            if detail:self.roof_detail[index]=self.params.detail['roof_tiles']['exposure_in']*.0254

    def tiles(self, pts, confidence):
        normal,poly,point,coords=self.roof_frame(pts)
        self.roof_raw(pts,confidence,ROOF,normal,coords)
        spec=self.params.detail['roof_tiles']
        w,h=spec['width_in']*.0254,spec['exposure_in']*.0254
        joint,relief=spec['joint_m'],spec['lap_relief_m']
        a,b,c,e=bounds(poly)
        # Clip every fragment, including narrow returns and cone tips. The
        # continuous mapped bed closes the joints and all computational cuts.
        for row in range(math.floor(b/h),math.ceil(e/h)):
            y0,y1=row*h,(row+1)*h
            shift=.5*w if row%2 else 0
            for col in range(math.floor((a-shift)/w),math.ceil((c-shift)/w)):
                x0=col*w+shift
                tile=rect_clip(poly,x0+joint/2,y0,x0+w-joint/2,y1)
                if not tile:continue
                rng=random.Random(row*10007+col*813+31)
                mat=19+rng.randrange(3)
                def raised(q):return relief+relief*(1-(q[1]-y0)/h)
                front=[point(q,raised(q)) for q in tile]
                self.roof_raw(front,confidence,mat,normal,coords,detail=True)
                # Individual noses close the lap instead of a broad stripe
                # stretching through every tile joint across the whole course.
                for q,r in zip(tile,tile[1:]+tile[:1]):
                    if abs(q[1]-y0)<1e-7 and abs(r[1]-y0)<1e-7:
                        self.roof_raw([point(q,relief),point(r,relief),point(r,raised(r)),point(q,raised(q))],confidence,mat,normal,coords,detail=True)
                self.roof_tiles+=1


def solid_polygon(b, pl, poly, depth0, depth1, confidence, mat):
    n=legacy._plane_dir(pl)
    front=[legacy._plane_point(pl,u,z,depth1) for u,z in poly]
    back=[legacy._plane_point(pl,u,z,depth0) for u,z in poly]
    b.raw(front,confidence,mat,n)
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        b.raw([back[i],back[j],front[j],front[i]],confidence,mat)



def glass_pane(b,front,normal,confidence):
    """Closed 4 mm dielectric pane; stock thickness is reconstructed.

    Keep the existing outward front and its source confidence. The added rear
    and four edge faces are reconstructed (1.0), not additional survey facts.
    Opaque slabs deliberately keep their existing, cheaper surface topology.
    """
    n=norm(normal);front=[tuple(p) for p in front]
    if dot(legacy._normal(front),n)<0:front.reverse()
    back=[tuple(p[k]-.004*n[k] for k in range(3)) for p in front]
    b.raw(front,confidence,GLASS,n)
    b.raw(list(reversed(back)),1.0,GLASS,tuple(-v for v in n))
    for i in range(len(front)):
        j=(i+1)%len(front)
        outward=norm(cross(sub(front[j],front[i]),n))
        b.raw([front[i],back[i],back[j],front[j]],1.0,GLASS,outward)


def slab(b,pl,u0,u1,z0,z1,d0,d1,confidence,mat):
    if min(u1-u0,z1-z0)>1e-5:
        solid_polygon(b,pl,[(u0,z0),(u1,z0),(u1,z1),(u0,z1)],d0,d1,confidence,mat)


def rough_lintel(b,pl,a,c,z0,z1,conf):
    slab(b,pl,a,c,z0,z1,-.035,.035,conf,ROUGH_TRIM)
    def point(q,off):return legacy._plane_point(pl,q[0],q[1],off+.045)
    rng=random.Random(int((a+c+z0)*10003))
    b.block([(a,z0),(c,z0),(c,z1),(a,z1)],point,legacy._plane_dir(pl),conf,ROUGH_TRIM,rng)


def cylinder(b,cx,cy,z0,z1,r,conf,mat,segments=16):
    for i in range(segments):
        a,c=2*math.pi*i/segments,2*math.pi*(i+1)/segments
        p,q=(cx+r*math.cos(a),cy+r*math.sin(a)),(cx+r*math.cos(c),cy+r*math.sin(c))
        b.raw([(p[0],p[1],z0),(q[0],q[1],z0),(q[0],q[1],z1),(p[0],p[1],z1)],conf,mat,(math.cos((a+c)/2),math.sin((a+c)/2),0))


def interior_recess(b,outline,point,normal,front=-.298,back=-.90):
    """Bounded, unfurnished shadow volume behind the exterior glazing.

    Its depth and dark lining are reconstructed rendering closure, not surveyed
    rooms. Closing all four sides stops exterior light reaching behind a lone
    backing card. No glass, sash or aperture dimensions are changed.
    """
    near=[point(u,z,front) for u,z in outline]
    far=[point(u,z,back) for u,z in outline]
    center=tuple(sum(p[k] for p in near+far)/(2*len(outline)) for k in range(3))
    b.raw(far,1.0,DARK_GLASS,normal)
    for i in range(len(outline)):
        j=(i+1)%len(outline)
        face=[near[i],far[i],far[j],near[j]]
        inward=tuple(center[k]-sum(p[k] for p in face)/4 for k in range(3))
        b.raw(face,1.0,DARK_GLASS,inward)


def linen_shade(b,u0,u1,z0,z1,point,normal,conf,seed,prairie_colonnade=False):
    """Reconstructed pale roller shades descend from the head, behind glass."""
    rng=random.Random(seed)
    # HABS court photo05 shows most roller hems near or above the meeting rail,
    # roughly 35–55% of full opening height, with visibly open lower panes.
    # Owner photos 09/10 bound occasional lower shades and gathered side linen.
    # These per-opening positions remain reconstructed, not scene-date facts.
    choices=(.06,.10,.16,.22,.28,.34) if prairie_colonnade else (.18,.32,.36,.40,.43,.46,.49,.52,.55,.64)
    closure=choices[rng.randrange(len(choices))]
    conf=1.0  # Shade positions and cloth folds are reconstructed, unlike the opening dimensions.
    a,c=u0+.075,u1-.075;top=z1-.07
    if c<=a or top<=z0+.07:return
    if closure:
        bottom=top-(z1-z0-.14)*closure
        b.raw([point(a,bottom,-.335),point(c,bottom,-.335),point(c,top,-.335),point(a,top,-.335)],conf,22,normal)
        # Small turned linen hem, not an opaque glazing-height stripe.
        b.raw([point(a,bottom,-.329),point(c,bottom,-.329),point(c,bottom+.018,-.335),point(a,bottom+.018,-.335)],conf,22,normal)
    if not prairie_colonnade and closure<=.55 and rng.random()<.60:
        # Gathered side linen occupies only 14–19% of the opening on each side.
        # Its folds sit behind real glass; a broad central lower pane remains
        # exposed, without painted reflections, furnishings or interior lamps.
        width=(c-a)*rng.uniform(.14,.19)
        for left in (a,c-width):
            for i in range(6):
                ua=left+width*i/6;ub=left+width*(i+1)/6
                oa=-.35+(.014 if i%2 else 0);ob=-.35+(.014 if (i+1)%2 else 0)
                bottom=z0+.08+abs(2*(i+.5)/6-1)*.035
                b.raw([point(ua,bottom,oa),point(ub,bottom,ob),point(ub,top,ob),point(ua,top,oa)],conf,22,normal)


def opening(b,o,courtyard=False):
    """An opening with 280 mm deep jambs, inset glazing, sash and separate sill."""
    kind=o['kind']; a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1']; conf=o['conf']
    if o.get('style') in ('stable_leaded','west_hood_clear'):
        from archetypes.masonry_house_v4_west_fabric import stable_window
        stable_window(b,o)
        return
    if kind=='band':
        if o.get('style')=='rock_faced_lintel':
            rock_lintel(b,o)
        elif o.get('style')=='rough_course':
            # T-2926: a continuous rock-faced lintel or sill course over several lights.
            rough_lintel(b,o,a,c,z0,z1,conf)
        elif o.get('face')=='east' and c-a>3 and z0>5:
            ornament.sill(b,o)
        else:
            slab(b,o,a,c,z0,z1,0,.095,conf,TRIM)
        return
    if kind=='fan':
        ornament.fan(b,o)
        return
    if through_passage(o):
        if o.get('corbels'):
            passage_corbels(b,o)
        return
    if o.get('style')=='north_entry_alcove':
        ring(b,o,(a+c)/2,o['spring_z'],(c-a)/2,o['r_out'],o.get('voussoirs') or 15,conf)
        return
    poly=aperture(o)
    from archetypes.masonry_house_v4_entry import front_offset
    front=[legacy._plane_point(o,u,z,.016+front_offset(b,o,u,z)) for u,z in poly]
    back=[legacy._plane_point(o,u,z,-.29) for u,z in poly]
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        if (o.get('style')=='prairie_front_door' and b.params.detail.get('prairie_entry')
                and abs(poly[i][1]-z0)<1e-8 and abs(poly[j][1]-z0)<1e-8):
            continue  # the single integral threshold owns this horizontal face
        b.raw([front[i],back[i],back[j],front[j]],conf,ROUGH_TRIM if courtyard else GRANITE)
    if o.get('style')=='court_garden_grille':
        from archetypes.masonry_house_v4_court import garden_light
        garden_light(b,o,b.params.detail['court_garden_grille'])
        return
    if kind=='arch':
        if o.get('style')=='gable_slit' and o.get('transom_z'):
            # T-2211: a glazed round head, a stone transom and a sash, not a black slot.
            from archetypes.masonry_house_v4_sash import gable_light
            gable_light(b,o,conf)
            ring(b,o,(a+c)/2,o['spring_z'],(c-a)/2,o['r_out'],o.get('voussoirs') or 11,conf)
            return
        b.raw(back,conf,DARK_GLASS,legacy._plane_dir(o))
        if o.get('style') in ('gable_slit','pigeon_vent'):
            if o.get('style')=='gable_slit':
                ring(b,o,(a+c)/2,o['spring_z'],(c-a)/2,o['r_out'],o.get('voussoirs') or 11,conf)
            return
        # Recessed carriage gate with actual stiles, rails and vertical boards.
        slab(b,o,a+.06,c-.06,z0+.025,o['spring_z'],-.285,-.245,conf,WOOD)
        count=max(2,int((c-a)/.18))
        for i in range(count+1):
            u=a+(c-a)*i/count
            slab(b,o,u-.014,u+.014,z0+.025,o['spring_z'],-.245,-.228,conf,WOOD)
        ring(b,o,(a+c)/2,o['spring_z'],(c-a)/2,o['r_out'],o.get('voussoirs') or 15,conf)
        return
    if kind in ('door','doors'):
        style=o.get('style','')
        if style=='stable_carriage_doors' and b.params.detail.get('north_stable_fabric'):
            from archetypes.masonry_house_v4_north import carriage_doors
            carriage_doors(b,o,b.params.detail['north_stable_fabric'])
            return
        if style in ('prairie_front_door','porte_cochere') or (o.get('face')=='east' and o['at']>45):
            detailed_door(b,o,'porte_cochere' if kind=='doors' else 'prairie_front_door')
            return
        slab(b,o,a+.04,c-.04,z0+.02,z1-.04,-.29,-.24,conf,WOOD)
        leaves=2 if kind=='doors' or c-a>1.3 else 1
        for leaf in range(leaves):
            la=a+.06+leaf*(c-a-.12)/leaves; lc=a+.06+(leaf+1)*(c-a-.12)/leaves
            for low,high in [(z0+.16,z0+(z1-z0)*.4),(z0+(z1-z0)*.46,z1-.16)]:
                slab(b,o,la+.08,lc-.08,low,high,-.25,-.21,conf,WOOD)
            slab(b,o,la,la+.055,z0+.05,z1-.05,-.24,-.18,conf,WOOD)
            slab(b,o,lc-.055,lc,z0+.05,z1-.05,-.24,-.18,conf,WOOD)
            slab(b,o,lc-.16,lc-.12,z0+(z1-z0)*.43,z0+(z1-z0)*.55,-.20,-.15,conf,IRON)
        return
    if o.get('style')=='stable_loft_opening' and b.params.detail.get('north_stable_fabric'):
        from archetypes.masonry_house_v4_north import loft_opening
        loft_opening(b,o,b.params.detail['north_stable_fabric'])
        return
    # Small basement grid apertures have stone mullions and only recessed glass.
    small=min(c-a,z1-z0)<.45
    if kind=='window' and not getattr(b,'reduced_sash',False):
        # T-2211: street and stable sash in their own planes; T-2212 the courtyard's,
        # on rock-faced limestone sills under rough lintels (the light tier keeps
        # the single pane below).
        from archetypes import masonry_house_v4_sash as sash
        sill_mat=ROUGH_TRIM if courtyard else None
        if small and max(c-a,z1-z0)>=.45:
            sash.slit_sash(b,o,a,c,z0,z1,conf,sill_mat=sill_mat,sill=not o.get('courses'),panes=o.get('panes'))
            return
        if not small:
            sash.double_hung(b,o,a,c,z0,z1,conf,divided=o.get('sash')=='two_over_two',sill_mat=sill_mat,
                             sill=not o.get('courses'))
            if courtyard and z1<1.8:
                # HABS photograph 05: the court's garden-level lights are barred.
                sash.garden_bars(b,o,a,c,z0,z1,conf)
            if z0>2:
                linen_shade(b,a,c,z0,z1,lambda u,z,off:legacy._plane_point(o,u,z,off),
                            legacy._plane_dir(o),conf,int((a*17+c*31+o['at']*7+z0)*10003),
                            prairie_colonnade=(not courtyard and o.get('face')=='east' and z0>5))
            if courtyard and not o.get('courses'):
                rough_lintel(b,o,a-.24,c+.24,z1+.006,z1+.21,conf)
            return
    frame=.025 if small else .062
    glazing_mat=DARK_GLASS if small or kind=='dark' else GLASS
    if glazing_mat==GLASS:
        interior_recess(b,[(a+frame,z0+frame),(c-frame,z0+frame),(c-frame,z1-frame),(a+frame,z1-frame)],
                        lambda u,z,off:legacy._plane_point(o,u,z,off),legacy._plane_dir(o))
        glass_pane(b,[legacy._plane_point(o,u,z,-.292) for u,z in
                      [(a+frame,z0+frame),(c-frame,z0+frame),(c-frame,z1-frame),(a+frame,z1-frame)]],
                   legacy._plane_dir(o),conf)
    else:
        slab(b,o,a+frame,c-frame,z0+frame,z1-frame,-.605,-.60,conf,DARK_GLASS)
        slab(b,o,a+frame,c-frame,z0+frame,z1-frame,-.30,-.292,conf,glazing_mat)
    if not small:
        for x0,x1,y0,y1 in [(a,a+frame,z0,z1),(c-frame,c,z0,z1),(a,c,z0,z0+frame),(a,c,z1-frame,z1)]:
            slab(b,o,x0,x1,y0,y1,-.285,-.18,conf,PAINTED_WOOD)
    if not small:
        mid=(z0+z1)/2
        slab(b,o,a+frame,c-frame,mid-.032,mid+.032,-.285,-.17,conf,PAINTED_WOOD)
        if c-a>1.7:
            midu=(a+c)/2
            slab(b,o,midu-.025,midu+.025,z0+frame,z1-frame,-.285,-.17,conf,PAINTED_WOOD)
        if z0>2:
            linen_shade(b,a,c,z0,z1,lambda u,z,off:legacy._plane_point(o,u,z,off),
                        legacy._plane_dir(o),conf,int((a*17+c*31+o['at']*7+z0)*10003),
                        prairie_colonnade=(not courtyard and kind=='window' and o.get('face')=='east' and z0>5))
        slab(b,o,a-.09,c+.09,z0-.085,z0+.025,-.055,.11,conf,ROUGH_TRIM if courtyard else GRANITE)
    if courtyard and not small:
        # Courtyard photographs show brick jambs with rock-faced limestone
        # heads and sills. Full stone jambs belong to the dining bay only.
        rough_lintel(b,o,a-.24,c+.24,z1+.006,z1+.21,conf)


def passage_corbels(b,o):
    """T-2926: the two stone corbels that narrow a passage mouth under its lintel.

    Sheet 4 draws each as a block standing in from its jamb, its lower inner corner
    rounded. How far it runs into the passage is not drawn (`depth`, reconstructed).
    """
    cb=o['corbels'];a,c=o['u0'],o['u1'];z0,z1=cb['z0'],cb['z1']
    w,r=cb['inset'],min(cb['round'],cb['inset'],z1-cb['z0'])
    arc=[(r*math.cos(math.pi*i/16),r*math.sin(math.pi*i/16)) for i in range(9)]
    for jamb,inward in ((a,1),(c,-1)):
        edge=jamb+inward*w
        # The quarter round's centre stands r in from the corbel's face and r above its foot.
        cu,cz=edge-inward*r,z0+r
        poly=[(jamb,z0),(cu,z0)]+[(cu+inward*dx,cz-dz) for dz,dx in arc[1:]]+[(edge,z1),(jamb,z1)]
        if inward<0:poly.reverse()
        solid_polygon(b,o,poly,-cb['depth'],.02,o['conf'],ROUGH_TRIM)


def detailed_door(b,o,style):
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];conf=o['conf']
    if style!='porte_cochere':
        # T-2216: the leaf as sheet No. 95 draws it, grille, strap and panels.
        from archetypes.masonry_house_v4_front_door import build
        build(b,o,subtract,interior_recess,glass_pane)
        return
    from archetypes.masonry_house_v4_porte import build
    build(b,o)

def ring(b,pl,uc,zs,rin,rout,count,conf):
    if rout<=rin:
        return
    rock_voussoirs(b,pl,uc,zs,rin,rout,count,conf,int((uc*31+zs*17+rout*7)*1000))


VOUSSOIR_JOINT = .014


def voussoir_outline(uc,zs,rin,rout,a,c,chord=False):
    """One radiating voussoir between angles a and c, its joints 14 mm wide.

    The extrados and intrados are arcs, so the wall's circular cut and the
    tympanum's outer roll meet a stone and not a chord's open wedge.
    """
    half=VOUSSOIR_JOINT/2
    lo,hi=a+half/max(rin,.05),c-half/max(rin,.05)
    so,eo=a+half/rout,c-half/rout
    # The reduced tier, at its triangle cap, keeps the plain chord of each arc.
    steps=1 if chord else max(2,math.ceil((eo-so)*rout/.06))
    inner_steps=1 if chord else max(1,math.ceil((hi-lo)*max(rin,.05)/.06))
    outline=[(uc+rout*math.cos(so+(eo-so)*k/steps),zs+rout*math.sin(so+(eo-so)*k/steps))
             for k in range(steps+1)]
    if rin<=1e-6:
        return outline+[(uc,zs)]
    return outline+[(uc+rin*math.cos(hi+(lo-hi)*k/inner_steps),zs+rin*math.sin(hi+(lo-hi)*k/inner_steps))
                    for k in range(inner_steps+1)]


def rock_voussoirs(b,pl,uc,zs,rin,rout,count,conf,seed,stilt=0.):
    """Radiating granite voussoirs, each pitched and bowed like the wall's ashlar.

    Owner, 2026-10-12, with photographs of the Prairie Avenue door: "the front
    door arch on the east also has the same stone treatment and should stand out
    more". The voussoirs were flat slabs (the north alcove and gable rings) or
    lower-relief faces than the wall (the door's fan). Each now carries its own
    arris and crown, a little fuller than a wall stone of the same breadth,
    which is how the long radiating stones read in the photographs. The reduced
    tier, which cannot afford the lattice, keeps one flat proud face per stone.

    With a `stilt` (T-2853) zs is the raised centre, and the two springers run
    plumb down to the spring line that far below it, as HABS sheet 5 and the
    office's doorway No. 23A both draw the Prairie fan.
    """
    rel=ornament.Relief(b,pl,conf)
    reduced=not getattr(b,'smooth_rock_faces',True)
    outer,inner=(1,1) if reduced else (4,2)
    for i in range(count):
        a,c=math.pi*i/count,math.pi*(i+1)/count
        # The joints' mortar bed, one sector per stone, where the wall's was cut.
        bed=[(uc+rout*math.cos(a+(c-a)*k/outer),zs+rout*math.sin(a+(c-a)*k/outer)) for k in range(outer+1)]
        bed+=([(uc+rin*math.cos(c-(c-a)*k/inner),zs+rin*math.sin(c-(c-a)*k/inner)) for k in range(inner+1)]
              if rin>1e-6 else [(uc,zs)])
        poly=voussoir_outline(uc,zs,rin,rout,a,c,chord=reduced)
        if stilt>0 and rin>1e-6 and i in (0,count-1):
            bed,poly=_stilted(bed,uc,zs,rin,rout,stilt,i==0,0.),_stilted(poly,uc,zs,rin,rout,stilt,i==0,VOUSSOIR_JOINT/2)
        rel.face([(*q,-.012) for q in bed],MORTAR)
        mat=12+i%4
        if reduced:
            solid_polygon(b,pl,poly,-.02,.065,conf,mat)
            continue
        rng=random.Random(seed+173*i)
        for facet,is_front in stone_corner_normals(fractured_stone(poly,rng.uniform(.030,.046),rng)):
            if is_front:
                b.raw_with_normals([rel.point(*p[:3]) for p in facet],
                                   [rel.vector(*p[3:]) for p in facet],conf,mat,rel.vector(0,0,1))
            else:
                rel.face(facet,mat,None)


def _stilted(poly,uc,zs,rin,rout,stilt,first,joint):
    """A springer: one end stone of a stilted ring, run plumb down by `stilt`.

    Outlines run along the extrados and back along the intrados, so the first
    stone (from angle 0) starts and ends at the centre's level on the right and
    the last stone (to angle pi) turns from extrados to intrados on the left;
    the plumb faces go in at those two places, `joint` clear of the spring line.
    """
    low=zs-stilt+joint
    if first:
        return [(uc+rout,low)]+list(poly)+[(uc+rin,low)]
    # The extrados is the run of points on rout; the intrados starts after it.
    turn=max(j for j,q in enumerate(poly) if abs(math.hypot(q[0]-uc,q[1]-zs)-rout)<1e-6)
    return list(poly[:turn+1])+[(uc-rout,low),(uc-rin,low)]+list(poly[turn+1:])


def rock_lintel(b,o):
    """A granite lintel, rock-faced like the courses either side of it.

    The owner's photographs of the Prairie Avenue door (2026-10-12) show one
    long quarry-faced stone under the fan, about three quarters of the fan's
    width, not a dressed slab the width of the tympanum.
    """
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1']
    half=VOUSSOIR_JOINT/2
    def point(q,off=0):return legacy._plane_point(o,q[0],q[1],off)
    from archetypes.masonry_house_v4_entry import lintel_outline,settings
    poly=lintel_outline(o,settings(b))
    b.raw([point(q,-.012) for q in poly],o['conf'],MORTAR,legacy._plane_dir(o))
    centre=((a+c)/2,(z0+z1)/2)
    face=[(x+math.copysign(half,centre[0]-x) if abs(x-centre[0])>half else x,
           z+math.copysign(half,centre[1]-z)) for x,z in poly]
    b.block(face,point,
            legacy._plane_dir(o),o['conf'],GRANITE,random.Random(int((o['at']*977+a*7919+z0*104729)*1000)))


def roof_ridges(b,params):
    if params.detail.get("roof_edges"):
        from archetypes.masonry_house_v4_roof_edges import add_ridges
        return add_ridges(b,params)
    from archetypes.masonry_house_v4_roof_crests import add_ridge_crest
    from archetypes.masonry_house_v4_west_roof import ridge_ranges
    for r,a0,a1 in (segment for source in params.ranges for segment in ridge_ranges(source)):
        step=.36
        for i in range(math.ceil((a1-a0)/step)):
            lo=a0+i*step+.006;hi=min(a1,lo+step-.012)
            for j in range(8):
                p,q=math.pi*j/8,math.pi*(j+1)/8
                def P(a,l):
                    across=r['ridge_at']+r.get('ridge_skew',0)*(l-r.get('ridge_origin',0))+.14*math.cos(a);z=r['ridge_z']+r.get('ridge_slope',0)*(l-r.get('ridge_origin',0))+.055+.14*math.sin(a)
                    return (across,l,z) if r['axis']=='y' else (l,across,z)
                b.raw([P(p,lo),P(q,lo),P(q,hi),P(p,hi)],r['conf_roof'],19+i%3,(0,0,1))
            add_ridge_crest(b,r['axis'],r['ridge_at'],r['ridge_z'],lo,hi,1.0,19+i%3,r.get('ridge_skew',0),r.get('ridge_origin',0),r.get('ridge_slope',0))


def chimney(b,c):
    if b.params.detail.get('stack_finish'):
        from archetypes.masonry_house_v4_chimneys import build_stack
        return build_stack(b,c)
    conf=c['conf'];z=c['z1'];x0,x1,y0,y1=c['x0'],c['x1'],c['y0'],c['y1']
    detail=b.params.detail.get('chimney_details',{}).get(c['name'],{})
    slope=float(detail.get('cap_slope_ft',.3))*.3048
    if (b.params.detail.get('north_tower_roof') or {}).get('integrated_north_facade') and c['name'] in ('middle','south'):
        # The reconciled ridge changes this pitch. Start each shaft face at its
        # host plane, not at the old horizontal datum (which would float clear
        # on the downhill side and waste hidden stone on the uphill side).
        from archetypes.masonry_house_v4_north_tower import chimney_foot
        outline=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for a,q in zip(outline,outline[1:]+outline[:1]):
            pts=[(*a,chimney_foot(b.params,a[0])),(*q,chimney_foot(b.params,q[0])),
                 (*q,z-slope-.06),(*a,z-slope-.06)]
            legacy._poly_facing(b,pts,conf,GRANITE,(q[1]-a[1],a[0]-q[0],0))
    else:
        legacy._box(b,x0,y0,c['z0'],x1,y1,z-slope-.06,conf,GRANITE)
    # No invented white overhanging lid: HABS stacks finish in granite coping.
    nx,ny=detail.get('flues',[2,1]);holes=[]
    for ix in range(nx):
        for iy in range(ny):
            cx=x0+(x1-x0)*(ix+.5)/nx;cy=y0+(y1-y0)*(iy+.5)/ny
            hx=min(.15,(x1-x0)/nx*.28);hy=min(.15,(y1-y0)/ny*.28)
            holes.append([(cx-hx,cy-hy),(cx+hx,cy-hy),(cx+hx,cy+hy),(cx-hx,cy+hy)])
    def height(y):return z-slope*(y-y0)/(y1-y0)
    outline=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    for frag in subtract(outline,holes):
        b.raw([(x,y,height(y)) for x,y in frag],conf,GRANITE,(0,0,1))
    for a,d in zip(outline,outline[1:]+outline[:1]):
        b.raw([(a[0],a[1],z-slope-.06),(d[0],d[1],z-slope-.06),
               (d[0],d[1],height(d[1])),(a[0],a[1],height(a[1]))],conf,GRANITE)
    for hole in holes:
        b.raw([(x,y,z-slope-.08) for x,y in hole],conf,IRON,(0,0,1))
        for a,d in zip(hole,hole[1:]+hole[:1]):
            b.raw([(a[0],a[1],z-slope-.08),(d[0],d[1],z-slope-.08),
                   (d[0],d[1],height(d[1])),(a[0],a[1],height(a[1]))],conf,GRANITE)
    if (b.params.detail.get('north_tower_roof') or {}).get('integrated_north_facade') and c['name'] in ('middle','south'):
        return # roof_edges.add_abutments supplies the slope-following flashing.
    old=b.decorate;b.decorate=False
    # A stack rising flush out of a gable's face (T-2214) is flashed on the roof
    # side only: no copper band stands proud of the wall it continues.
    north=y1-.10 if detail.get('flush')=='north' else y1+.06
    legacy._box(b,x0-.06,y0-.06,c['z0'],x1+.06,north,c['z0']+.13,conf,COPPER)
    b.decorate=old


def copper_seams(b,pts,conf,step=.48):
    n=norm(legacy._normal(pts));n=tuple(-x for x in n) if n[2]<0 else n
    b.raw(pts,conf,COPPER,n)
    if len(pts)!=4:
        return
    a,c,d,e=pts
    width=math.dist(a,c);count=max(1,round(width/step))
    for i in range(1,count):
        t=i/count
        p=tuple(a[k]+(c[k]-a[k])*t+n[k]*.015 for k in range(3))
        q=tuple(e[k]+(d[k]-e[k])*t+n[k]*.015 for k in range(3))
        side=norm(sub(c,a));r=.012
        b.raw([tuple(p[k]-side[k]*r for k in range(3)),tuple(p[k]+side[k]*r for k in range(3)),
               tuple(q[k]+side[k]*r for k in range(3)),tuple(q[k]-side[k]*r for k in range(3))],conf,COPPER,n)


def bow(b,w):
    a0,a1=sorted((w['a0'],w['a1']))
    if a1-a0>math.pi:a0,a1=a1,a0+2*math.pi
    n=w['lights_per_row'];r=w['r'];cx,cy=w['cx'],w['cy'];conf=w['conf_wall']
    windows=[]
    if w.get('light_spans'):
        # T-2925: each light at the extent the drawing gives it, the door named
        for (lo,hi),row in zip(w['light_rows'],w['light_spans']):
            for s in row:
                z0=b.params.detail['bow_terrace']['z1']-.18 if s['door'] and b.params.detail.get('bow_terrace') else lo
                windows.append({'a0':s['a0'],'a1':s['a1'],'z0':z0,'z1':hi,'door':s['door']})
    else:
        window_angles=[]
        for i in range(n):
            a=a0+(a1-a0)*(i+.5)/n;half=(a1-a0)/n*.28
            window_angles.append((a-half,a+half))
        for wi,(a,c) in enumerate(window_angles):
            for ri,(lo,hi) in enumerate(w['light_rows']):
                isdoor=ri==0 and wi==n//2 and b.params.detail.get('bow_first_floor_central_door')
                if isdoor and b.params.detail.get('bow_terrace'):
                    lo=b.params.detail['bow_terrace']['z1']-.18
                windows.append({'a0':a,'a1':c,'z0':lo,'z1':hi,'door':isdoor})
    curved_masonry(b,cx,cy,r,0,w['wall_top_z'],conf,BRICK,windows,a0,a1)
    courses=w.get('courses') or []
    for op in windows:
        a,c=op['a0'],op['a1'];mid=(a+c)/2
        p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
        facet_window(b,p,q,op['z0'],op['z1'],(math.cos(mid),math.sin(mid),0),conf,stone_jambs=False,door=op['door'],sash=True,
                     surrounds=not courses)
    for course in courses:
        arc_course(b,cx,cy,r,course['a0'],course['a1'],course['z0'],course['z1'],conf)
    if b.params.detail.get('continuous_copper_corner'):
        return  # One joined fan and return are emitted in supplemental().
    z=w['wall_top_z'];zr=z+w['roof_rise_m'];ro=r+.20
    for i in range(48):
        a=a0+(a1-a0)*i/48;c=a0+(a1-a0)*(i+1)/48
        pts=[(cx+ro*math.cos(a),cy+ro*math.sin(a),z),(cx+ro*math.cos(c),cy+ro*math.sin(c),z),(cx,cy,zr)]
        b.raw(pts,w['conf_roof'],COPPER,(0,0,1))
        if i%3==0:
            a2=a+.007
            b.raw([(cx+ro*math.cos(a),cy+ro*math.sin(a),z+.022),(cx+ro*math.cos(a2),cy+ro*math.sin(a2),z+.022),(cx,cy,zr+.022)],w['conf_roof'],COPPER,(0,0,1))



def arc_course(b,cx,cy,r,a0,a1,z0,z1,conf,proud=.05,bed=.03):
    """A stone course laid round part of a curved wall (T-2925: the hall bow's lintel and
    sill courses, which sheet 4 draws running unbroken past its lights)."""
    count=max(2,math.ceil((a1-a0)/math.radians(2)))
    angles=[a0+(a1-a0)*i/count for i in range(count+1)]
    def P(a,rad,z):return (cx+rad*math.cos(a),cy+rad*math.sin(a),z)
    ro,ri=r+proud,r-bed
    for a,c in zip(angles,angles[1:]):
        mid=(a+c)/2;out=(math.cos(mid),math.sin(mid),0)
        b.raw([P(a,ro,z0),P(c,ro,z0),P(c,ro,z1),P(a,ro,z1)],conf,ROUGH_TRIM,out)
        b.raw([P(a,ri,z1),P(c,ri,z1),P(c,ro,z1),P(a,ro,z1)],conf,ROUGH_TRIM,(0,0,1))
        b.raw([P(a,ri,z0),P(c,ri,z0),P(c,ro,z0),P(a,ro,z0)],conf,ROUGH_TRIM,(0,0,-1))
    for a,side in ((a0,-1),(a1,1)):
        tangent=(-math.sin(a)*side,math.cos(a)*side,0)
        b.raw([P(a,ri,z0),P(a,ro,z0),P(a,ro,z1),P(a,ri,z1)],conf,ROUGH_TRIM,tangent)


def facet_window(b,p,q,z0,z1,normal,conf,small=False,stone_jambs=True,door=False,panes=None,surrounds=True,
                 sash=False,stones_m=None):
    """Recessed sash on an arbitrarily oriented planar bay facet.

    `sash` draws T-2212's one-over-one double-hung in two planes in place of the
    single pane and flat frame (the light tier keeps the single pane)."""
    tangent=norm(sub((*q,0),(*p,0)));width=math.dist(p,q)
    sash=sash and not small and not door and not getattr(b,'reduced_sash',False)
    def P(u,z,off):
        return (p[0]+tangent[0]*u+normal[0]*off,p[1]+tangent[1]*u+normal[1]*off,z)
    outline=[(0,z0),(width,z0),(width,z1),(0,z1)]
    for i in range(4):
        a,c=outline[i],outline[(i+1)%4]
        b.raw([P(*a,.02),P(*a,-.29),P(*c,-.29),P(*c,.02)],conf,TRIM if stone_jambs else BRICK)
    if sash:
        from archetypes.masonry_house_v4_sash import on_facet
        on_facet(b,p,tangent,normal,width,z0,z1,conf)
    elif small:
        b.raw([P(u,z,-.60) for u,z in outline],conf,DARK_GLASS,normal)
    else:
        interior_recess(b,outline,P,normal,front=-.291)
    if not door and not sash:
        if small:
            b.raw([P(u,z,-.285) for u,z in outline],conf,DARK_GLASS,normal)
        else:
            glass_pane(b,[P(u,z,-.285) for u,z in outline],normal,conf)
    def box(ua,ub,za,zb,off0,off1,mat):
        front=[P(ua,za,off1),P(ub,za,off1),P(ub,zb,off1),P(ua,zb,off1)]
        back=[P(ua,za,off0),P(ub,za,off0),P(ub,zb,off0),P(ua,zb,off0)]
        b.raw(front,conf,mat,normal)
        for i in range(4):
            j=(i+1)%4;b.raw([front[i],back[i],back[j],front[j]],conf,mat)
    if not small and not door:
        linen_shade(b,0,width,z0,z1,P,normal,conf,int((p[0]*17+q[1]*31+z0)*10003))
    if door:
        # HABS photograph 05 shows four glazed lights above a raised wood
        # panel. The fine iron grid in modern image(10) is not the historical
        # joinery evidence. Stock, moulding and hardware dimensions below are
        # reconstructed within the unchanged doorway and leaf depth.
        height=z1-z0;stile=min(.12,width*.15)
        ga,gb=stile,width-stile
        gz0,gz1=z0+height*.45,z1-.14
        # Only the lower part is solid wood. A full-height backing here made
        # the previous clear glazing render as an opaque grey panel.
        box(0,width,z0,gz0,-.28,-.23,WOOD)
        for ua,ub,za,zb in [(0,ga,z0,z1),(gb,width,z0,z1),
                           (ga,gb,gz1,z1),(ga,gb,gz0-.13,gz0),
                           (ga,gb,z0,z0+.14)]:
            box(ua,ub,za,zb,-.28,-.20,WOOD)
        glass_pane(b,[P(ga,gz0,-.248),P(gb,gz0,-.248),
                      P(gb,gz1,-.248),P(ga,gz1,-.248)],normal,conf)
        um,zm=(ga+gb)/2,(gz0+gz1)/2
        box(um-.012,um+.012,gz0,gz1,-.254,-.208,WOOD)
        box(ga,gb,zm-.015,zm+.015,-.254,-.208,WOOD)

        def moulding(ua,ub,za,zb,depth,radius):
            # A closed rounded rectangle with an actual round bead profile.
            # Unlike a flat outline it catches light along its curved shoulder.
            corner=min(.025,(ub-ua)/6,(zb-za)/6);path=[]
            for cu,cz,start in [(ub-corner,zb-corner,0),(ua+corner,zb-corner,math.pi/2),
                                (ua+corner,za+corner,math.pi),(ub-corner,za+corner,3*math.pi/2)]:
                for k in range(6):
                    th=start+math.pi*k/10
                    path.append((cu+corner*math.cos(th),cz+corner*math.sin(th)))
            rings=[]
            for j,(u,z) in enumerate(path):
                a,c=path[j-1],path[(j+1)%len(path)]
                run=math.hypot(c[0]-a[0],c[1]-a[1]) or 1
                nu,nz=-(c[1]-a[1])/run,(c[0]-a[0])/run
                rings.append([P(u+nu*radius*math.cos(2*math.pi*k/10),
                                z+nz*radius*math.cos(2*math.pi*k/10),
                                depth+radius*math.sin(2*math.pi*k/10)) for k in range(10)])
            for j in range(len(rings)):
                for k in range(10):
                    nxt=(j+1)%len(rings)
                    pts=[rings[j][k],rings[nxt][k],rings[nxt][(k+1)%10],rings[j][(k+1)%10]]
                    centre=P((path[j][0]+path[nxt][0])/2,(path[j][1]+path[nxt][1])/2,depth)
                    outward=tuple(sum(pt[a] for pt in pts)/4-centre[a] for a in range(3))
                    b.raw(pts,conf,WOOD,outward)

        moulding(ga,gb,gz0,gz1,-.218,.008)
        pa,pb=ga+.035,gb-.035;pz0,pz1=z0+.18,gz0-.17
        box(pa,pb,pz0,pz1,-.237,-.215,WOOD)
        moulding(pa,pb,pz0,pz1,-.208,.014)
        # A small round latch is visible in HABS05; its exact metal profile
        # and placement are bounded reconstruction.
        ku=width-stile*.53;kz=gz0-.075
        box(ku-.017,ku+.017,kz-.065,kz+.065,-.201,-.187,IRON)
        for j in range(8):
            a,c=2*math.pi*j/8,2*math.pi*(j+1)/8
            b.raw([P(ku+.009*math.cos(a),kz+.009*math.sin(a),-.191),
                   P(ku+.009*math.cos(c),kz+.009*math.sin(c),-.191),
                   P(ku+.009*math.cos(c),kz+.009*math.sin(c),-.157),
                   P(ku+.009*math.cos(a),kz+.009*math.sin(a),-.157)],conf,IRON,
                  (tangent[0]*math.cos((a+c)/2),tangent[1]*math.cos((a+c)/2),math.sin((a+c)/2)))
        for j in range(12):
            a,c=2*math.pi*j/12,2*math.pi*(j+1)/12
            for k in range(4):
                aa,cc=math.pi*k/8,math.pi*(k+1)/8
                def knob(th,ph):
                    return P(ku+.022*math.sin(th)*math.cos(ph),
                             kz+.022*math.sin(th)*math.sin(ph),-.162+.022*math.cos(th))
                pts=[knob(aa,a),knob(cc,a),knob(cc,c)]
                if k:pts.append(knob(aa,c))
                b.raw(pts,conf,IRON,normal)
    if not small and not door and not sash:
        frames=[(0,.06,z0,z1),(width-.06,width,z0,z1),(0,width,z0,z0+.06),(0,width,z1-.06,z1)]
        cols,rows=panes or [1,2]
        for col in range(1,cols):
            u=width*col/cols;frames.append((u-.019,u+.019,z0,z1))
        for row in range(1,rows):
            z=z0+(z1-z0)*row/rows;frames.append((0,width,z-.022,z+.022))
        for ua,ub,za,zb in frames:
            box(ua,ub,za,zb,-.285,-.18,PAINTED_WOOD)
    # `stones_m` (head, sill, side) sizes a surround the drawing measures (T-2925)
    head,sill,side=stones_m or (.18,.1,.20)
    stones=[(-side,width+side,z0-sill,z0),(-side,width+side,z1,z1+head)] if surrounds else []
    if stone_jambs:stones += [(-.27,0,z0,z1),(width,width+.27,z0,z1)]
    for ua,ub,za,zb in stones:
        box(ua,ub,za,zb,-.03,.05,ROUGH_TRIM)


def bay(b,y,params):
    pts=y['pts'];mx=(pts[0][0]+pts[-1][0])/2;my=(pts[0][1]+pts[-1][1])/2
    cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts)
    ix,iy=2*mx-cx,2*my-cy;zt,zb=y['wall_top_z'],y['band_top_z'];conf=y['conf_wall']
    principal=-1
    for p,q in zip(pts,pts[1:]):
        want=norm(((p[0]+q[0])/2-ix,(p[1]+q[1])/2-iy,0))
        length=math.dist(p,q);holes=[];windows=[]
        if length>1.2:
            principal+=1
            a=(p[0]+(q[0]-p[0])*.2,p[1]+(q[1]-p[1])*.2)
            c=(p[0]+(q[0]-p[0])*.8,p[1]+(q[1]-p[1])*.8)
            rows=([y['light_row']] if y['light_row'] else [])
            if params.detail.get('dining_garden_window_z') and principal in params.detail.get('dining_garden_window_facets',[0,2,4]):
                rows+=[params.detail['dining_garden_window_z']]
            for lo,hi in rows:
                holes.append([(*a,lo),(*c,lo),(*c,hi),(*a,hi)]);windows.append((a,c,lo,hi))
        wall=[(*p,0),(*q,0),(*q,zt),(*p,zt)]
        if dot(legacy._normal(wall),want)<0:wall.reverse()
        b.wall(wall,conf,BRICK,holes)
        if y['light_row']:
            low,high=y['light_row']
            for lo,hi in [(low-.14,low),(high,high+.23)]:
                pa=(p[0]+want[0]*.055,p[1]+want[1]*.055);qa=(q[0]+want[0]*.055,q[1]+want[1]*.055)
                b.raw([(*pa,lo),(*qa,lo),(*qa,hi),(*pa,hi)],conf,ROUGH_TRIM,want)
        for a,c,lo,hi in windows:
            basal=lo<2
            facet_window(b,a,c,lo,hi,want,conf,small=basal,stone_jambs=not basal,sash=True)
            if basal:
                count=max(3,round(math.dist(a,c)/.115))
                for i in range(count+1):
                    x=a[0]+(c[0]-a[0])*i/count;y1=a[1]+(c[1]-a[1])*i/count
                    cylinder(b,x,y1,lo+.025,hi-.025,.012,conf,IRON,6)
        if zb>zt:
            # The shallow bay has its own dark interior behind the glazed band;
            # transmission must never expose the unrelated north-range wall.
            pa=(p[0]-want[0]*.35,p[1]-want[1]*.35);qa=(q[0]-want[0]*.35,q[1]-want[1]*.35)
            b.raw([(*pa,zt),(*qa,zt),(*qa,zb),(*pa,zb)],conf,DARK_GLASS,want)
            glass_pane(b,[(*p,zt),(*q,zt),(*q,zb),(*p,zb)],want,conf)
            # Smooth, projecting limestone roll below the clerestory, visibly
            # continuous around the documented canted outline.
            for j in range(8):
                aa,cc=math.pi*j/8,math.pi*(j+1)/8
                def M(pt,t):return (pt[0]+want[0]*.15*math.sin(t),pt[1]+want[1]*.15*math.sin(t),zt+.04+.15*math.cos(t))
                b.raw([M(p,aa),M(q,aa),M(q,cc),M(p,cc)],conf,TRIM,want)
            tangent=norm(sub((*q,0),(*p,0)))
            # HABS photo05: two glazed rows, each facet divided into three lights.
            for rail,thick in [(zt+.05,.06),((zt+zb)/2,.04),(zb-.04,.06)]:
                a=(p[0]+want[0]*.045,p[1]+want[1]*.045);c=(q[0]+want[0]*.045,q[1]+want[1]*.045)
                b.raw([(*a,rail-thick/2),(*c,rail-thick/2),(*c,rail+thick/2),(*a,rail+thick/2)],conf,PAINTED_WOOD,want)
            for j in range(max(1,round(length/.55))+1):
                f=j/max(1,round(length/.55));x=p[0]+(q[0]-p[0])*f;y1=p[1]+(q[1]-p[1])*f
                aa=(x-tangent[0]*.025+want[0]*.035,y1-tangent[1]*.025+want[1]*.035)
                cc=(x+tangent[0]*.025+want[0]*.035,y1+tangent[1]*.025+want[1]*.035)
                b.raw([(*aa,zt),(*cc,zt),(*cc,zb),(*aa,zb)],conf,PAINTED_WOOD,want)
        if params.detail.get('dining_crested_connection'):
            continue  # The joined hip/apron/cross ridge is emitted together below.
        ap=y['apex'];roof=[(*p,zb),(*q,zb),tuple(ap)]
        b.raw(roof,y['conf_roof'],COPPER,(0,0,1))
        # Standing seams subdivide the hipped cap while its top runs into the main roof.
        count=max(1,round(length/.48))
        for j in range(1,count):
            f=j/count;x=p[0]+(q[0]-p[0])*f;yy=p[1]+(q[1]-p[1])*f
            aa=(x-.01,yy,zb+.016);cc=(x+.01,yy,zb+.016)
            b.raw([aa,cc,(ap[0],ap[1],ap[2]+.016)],y['conf_roof'],COPPER,(0,0,1))




def _arched_hole(l,r,sill,spring,segments):
    """A round-headed opening in face (u, z) coordinates, sill to crown."""
    c,rad=(l+r)/2,(r-l)/2
    return [(l,sill),(r,sill)]+[(c+rad*math.cos(math.pi*i/segments),
                                 spring+rad*math.sin(math.pi*i/segments))
                                for i in range(segments+1)]


def outward_solid(b,pl,poly,depth0,depth1,confidence,mat):
    """solid_polygon with every edge face turned out of the solid (T-3036).

    solid_polygon leaves its edge faces to the polygon's winding, which the
    plane's axis and sign mirror, so on half a box's faces they look inward.
    """
    n=legacy._plane_dir(pl);ccw=area(poly)>0
    b.raw([legacy._plane_point(pl,u,z,depth1) for u,z in poly],confidence,mat,n)
    for (u0,z0),(u1,z1) in zip(poly,poly[1:]+poly[:1]):
        ou,oz=(z1-z0,u0-u1) if ccw else (z0-z1,u1-u0)
        want=(0.0,ou,oz) if pl['axis']=='x' else (ou,0.0,oz)
        b.raw([legacy._plane_point(pl,u0,z0,depth0),legacy._plane_point(pl,u1,z1,depth0),
               legacy._plane_point(pl,u1,z1,depth1),legacy._plane_point(pl,u0,z0,depth1)],
              confidence,mat,want)


def dovecote_band(b,t,x0,x1,y0,y1):
    """The stable cupola's vent band as HABS photograph 1 shows it (T-2207).

    Two tiers of round-headed pigeon holes, each tier standing on its own
    projecting landing board, in place of the slatted louvres the band carried
    before. The form is read from the photograph; counts and stock sizes are
    bounded reconstruction (docs/LIBERTIES.md L-glessner-cupola-2207).

    A `body_material` of granite builds the body, band and ledges in stone, as
    the c. 1887 Cornell view shows them, and `ledge_m` sets the ledge's depth
    (T-2849, L-glessner-cupola-stone-2849); without either it is boarding.

    `ledge_corners: wrapped` runs each tier's ledge unbroken round the corners,
    as both northwest prints show it (T-3030): the east and west faces' ledges
    reach past the corners by their projection, and the north and south faces'
    butt against them, so no two ledge faces lie in one plane.

    The body's walls meet the same way (T-3036): the east and west walls run
    the plan's full depth and the north and south walls stop inside them, so
    no wall's end lies in its neighbour's face, and every edge face looks out.

    `shaft_courses` lays a granite body in rock-faced courses (T-3046,
    coursed_body) where it was dressed plates.
    """
    lo,hi=t['louvre'];conf=t['conf'];v=t['vent'];reconstructed=1.0
    tiers,per_face=v['tiers'],v['per_face'];width=v['opening_width_m']
    perch=v['perch_projection_m'];board=v.get('ledge_m',.025)
    body=GRANITE if t.get('body_material')=='granite' else WOOD
    segments=3 if getattr(b,'reduced_roof_details',False) else 6
    step=(hi-lo)/tiers;wrapped=v.get('ledge_corners')=='wrapped'
    for pl,(a,c) in (({'axis':'x','sign':1,'at':x1},(y0,y1)),
                     ({'axis':'x','sign':-1,'at':x0},(y0,y1)),
                     ({'axis':'y','sign':1,'at':y1},(x0,x1)),
                     ({'axis':'y','sign':-1,'at':y0},(x0,x1))):
        ua,uc=a+.12,c-.12;n=legacy._plane_dir(pl)
        holes=[]
        for tier in range(tiers):
            base=lo+tier*step;sill=base+board+.012
            crown=base+step-.03;spring=crown-width/2
            for k in range(per_face):
                mid=ua+(uc-ua)*(k+.5)/per_face
                holes.append(_arched_hole(mid-width/2,mid+width/2,sill,spring,segments))
            # The landing board the birds alight on, one per tier and face;
            # it stops short of the corner so two faces' boards never meet,
            # unless the record wraps it round them (see the docstring).
            if not wrapped:
                l,r=ua,uc
            elif pl['axis']=='x':
                l,r=a-perch,c+perch
            else:
                l,r=a+.04,c-.04
            outward_solid(b,pl,[(l,base),(r,base),(r,base+board),(l,base+board)],
                          -.04,perch,reconstructed,body)
        # The east and west walls take the corners; the others butt inside.
        l,r=(a,c) if pl['axis']=='x' else (a+.08,c-.08)
        wall=[(l,t['z0']),(r,t['z0']),(r,t['top_z']),(l,t['top_z'])]
        if body==GRANITE and t.get('shaft_courses') and not getattr(b,'reduced_roof_details',False):
            coursed_body(b,t,pl,a,c,l,r,holes,step,board,conf)
        else:
            for fragment in subtract(wall,holes):
                outward_solid(b,pl,fragment,-.08,0,conf,body)
        # The dark cote behind the holes: one closing card per face.
        b.raw([legacy._plane_point(pl,u,z,-.17) for u,z in
               [(ua,lo),(uc,lo),(uc,hi),(ua,hi)]],reconstructed,DARK_GLASS,n)


def coursed_body(b,t,pl,a,c,l,r,holes,step,board,conf):
    """The granite cupola's body in rock-faced courses, as the Cornell print shows it (T-3046).

    The c. 1887 print (T-3044 § 4) shows two or three bed joints in the shaft
    below the lower ledge and each pigeon tier standing as one rock-faced course
    between its ledges. So the shaft is laid in `shaft_courses` equal courses,
    each tier in one course from its ledge to the next, and the band over the top
    tier in one, all through the house's own ashlar_course on a string of their
    own (the chimney bands' way, masonry_house_v4_chimneys._band). The print
    does not resolve the vertical joints: block lengths are the house's own rule.
    Every face's courses run the full plan, so they cover the corner walls' ends.
    The body behind them stands back of the mortar bed, and the holes' reveals
    run out to the pitch line, as the house's own apertures' do. Bounded
    reconstruction: docs/LIBERTIES.md L-glessner-cupola-coursing-3046.
    """
    lo,hi=t['louvre'];z0,top=t['z0'],t['top_z'];n=legacy._plane_dir(pl)
    for fragment in subtract([(l,z0),(r,z0),(r,top),(l,top)],holes):
        outward_solid(b,pl,fragment,-.08,-.02,conf,GRANITE)
    for hole in holes:
        ccw=area(hole)>0
        for (u0,v0),(u1,v1) in zip(hole,hole[1:]+hole[:1]):
            ou,oz=(v0-v1,u1-u0) if ccw else (v1-v0,u0-u1)
            want=(0.0,ou,oz) if pl['axis']=='x' else (ou,0.0,oz)
            b.raw([legacy._plane_point(pl,u0,v0,-.02),legacy._plane_point(pl,u1,v1,-.02),
                   legacy._plane_point(pl,u1,v1,PITCH_LINE),legacy._plane_point(pl,u0,v0,PITCH_LINE)],
                  conf,GRANITE,want)
    cut=[[legacy._plane_point(pl,u,v,0) for u,v in hole] for hole in holes]
    count=t['shaft_courses']
    bands=[(z0,lo,count)]+[(lo+i*step+board,lo+(i+1)*step,1) for i in range(t['vent']['tiers'])]
    if top-hi>.05:
        bands.append((hi,top,1))
    old=b.course_schedule;had=hasattr(b,'course_origin');origin=getattr(b,'course_origin',None)
    try:
        for za,zb,k in bands:
            b.course_schedule=[(zb-za)/k]*k;b.course_origin=za
            pts=[legacy._plane_point(pl,u,v,0) for u,v in ((a,za),(c,za),(c,zb),(a,zb))]
            if dot(legacy._normal(pts),n)<0:pts.reverse()
            b.wall(pts,conf,GRANITE,custom_holes=cut)
    finally:
        b.course_schedule=old
        if had:b.course_origin=origin
        else:del b.course_origin


def flared_turret_roof(b,t,x0,x1,y0,y1):
    """A pyramid that kicks out over a deep eave, as photographs 1 and 17 show.

    The apex and body top are the record's own; only the eave ring moves, out
    by `overhang` and down by `drop`, and the bottom `flare_run` of the slope
    eases to `flare_pitch` (T-2207). The roof-edge pass dresses the eave's
    fascia, as it does every other eave in the house.
    """
    e=t['eave'];conf=t['conf'];cx,cy=(x0+x1)/2,(y0+y1)/2
    ov,ze=e['overhang_m'],t['top_z']-e['drop_m']
    zk=ze+e['flare_run_m']*e['flare_pitch'];kv=ov-e['flare_run_m']
    def ring(o,z):
        return [(x0-o,y0-o,z),(x1+o,y0-o,z),(x1+o,y1+o,z),(x0-o,y1+o,z)]
    eave,kink=ring(ov,ze),ring(kv,zk)
    for i in range(4):
        j=(i+1)%4
        legacy._up(b,[eave[i],eave[j],kink[j],kink[i]],conf,ROOF)
        legacy._up(b,[kink[i],kink[j],(cx,cy,t['apex_z'])],conf,ROOF)
    legacy._poly_facing(b,eave,conf,ROOF,(0,0,-1))
    legacy._finial(b,cx,cy,t['apex_z'],t['finial_m'],conf,COPPER)


def louvred_turret(b,t):
    """Retain the stable turret envelope; its band is timber louvres, not glass."""
    x0,x1=sorted((t['x0'],t['x1']));y0,y1=sorted((t['y0'],t['y1']))
    if t.get('vent') and t.get('eave'):
        dovecote_band(b,t,x0,x1,y0,y1)
        flared_turret_roof(b,t,x0,x1,y0,y1)
        return
    lo,hi=t['louvre'];conf=t['conf'];reconstructed=1.0
    for pl,(a,c) in (({'axis':'x','sign':1,'at':x1},(y0,y1)),
                     ({'axis':'x','sign':-1,'at':x0},(y0,y1)),
                     ({'axis':'y','sign':1,'at':y1},(x0,x1)),
                     ({'axis':'y','sign':-1,'at':y0},(x0,x1))):
        ua,uc=a+.12,c-.12;n=legacy._plane_dir(pl)
        hole=[(ua,lo),(uc,lo),(uc,hi),(ua,hi)]
        wall=[(a,t['z0']),(c,t['z0']),(c,t['top_z']),(a,t['top_z'])]
        for fragment in subtract(wall,[hole]):
            solid_polygon(b,pl,fragment,-.08,0,conf,WOOD)
        b.raw([legacy._plane_point(pl,u,z,-.17) for u,z in hole],reconstructed,DARK_GLASS,n)
        # The louvred form is sourced; roughly145mm spacing,140mm blade depth
        # and16mm stock are bounded reconstructed joinery, not counted slats.
        count=max(2,round((hi-lo)/.145));pitch=(hi-lo)/count
        rise=min(.05,pitch*.34)
        for i in range(count):
            mid=lo+(i+.5)*pitch
            top=[legacy._plane_point(pl,ua,mid-rise,0),
                 legacy._plane_point(pl,uc,mid-rise,0),
                 legacy._plane_point(pl,uc,mid+rise,-.14),
                 legacy._plane_point(pl,ua,mid+rise,-.14)]
            bottom=[(p[0],p[1],p[2]-.016) for p in top]
            b.raw(top,reconstructed,WOOD,(0,0,1))
            b.raw(bottom,reconstructed,WOOD,(0,0,-1))
            centre=tuple(sum(p[k] for p in top+bottom)/8 for k in range(3))
            for j in range(4):
                k=(j+1)%4;face=[top[j],bottom[j],bottom[k],top[k]]
                midpoint=tuple(sum(p[h] for p in face)/4 for h in range(3))
                b.raw(face,reconstructed,WOOD,sub(midpoint,centre))
    b.raw([(x0,y0,t['top_z']),(x1,y0,t['top_z']),
           (x1,y1,t['top_z']),(x0,y1,t['top_z'])],conf,WOOD,(0,0,1))
    # Roof, soffit and finial are exactly the inherited recorded envelope.
    ov=.18;ring=[(x0-ov,y0-ov,t['top_z']),(x1+ov,y0-ov,t['top_z']),
                 (x1+ov,y1+ov,t['top_z']),(x0-ov,y1+ov,t['top_z'])]
    cx,cy=(x0+x1)/2,(y0+y1)/2
    for p,q in zip(ring,ring[1:]+ring[:1]):
        legacy._up(b,[p,q,(cx,cy,t['apex_z'])],conf,ROOF)
    legacy._poly_facing(b,ring,conf,ROOF,(0,0,-1))
    legacy._finial(b,cx,cy,t['apex_z'],t['finial_m'],conf,COPPER)


def dormer(b,d):
    f,bk=d['front'],d['back'];a,c=sorted((d['u0'],d['u1']));z0,ze,za=d['z0'],d['eave_z'],d['apex_z']
    sign=-1 if bk>f else 1;pl={'axis':'x','sign':sign,'at':f}
    margin=(c-a)*d.get('light_margin_fraction',.22);lo,hi=d['light'];conf=d['conf']
    from archetypes.masonry_house_v4_court import dormer_roof,above_host,court_finial
    joined=b.params.detail.get('court_dormer_union')
    def visible(pts):return above_host(pts,b.params) if joined else pts
    reconstructed=1.0  # Exact stock/edge dimensions below are reconstructed.
    op={**pl,'face':'west' if sign<0 else 'east','kind':'window','u0':a+margin,'u1':c-margin,'z0':lo,'z1':hi,'conf':conf}
    poly=[(a,z0),(c,z0),(c,ze),(a,ze)]
    for frag in subtract(poly,[aperture(op)]):
        b.raw([legacy._plane_point(pl,u,z) for u,z in frag],conf,PAINTED_WOOD,legacy._plane_dir(pl))
    for u in (a,c):
        pts=[(f,u,z0),(bk,u,z0),(bk,u,ze),(f,u,ze)]
        pts=visible(pts)
        if pts:legacy._poly_facing(b,pts,conf,ROOF,(0,-1 if u==a else 1,0))
    # HABS photo05 shows one undivided light in timber, not the masonry
    # reveals, granite sill and meeting rail used by a house-wall window.
    la,lc=op['u0'],op['u1'];outline=aperture(op);normal=legacy._plane_dir(pl)
    k=d.get('frame_stock_m',.055)  # T-2859: HABS4 draws the frame stock about 0.22 ft
    for p,q in zip(outline,outline[1:]+outline[:1]):
        b.raw([legacy._plane_point(pl,*p,.016),legacy._plane_point(pl,*p,-.20),
               legacy._plane_point(pl,*q,-.20),legacy._plane_point(pl,*q,.016)],reconstructed,PAINTED_WOOD)
    interior_recess(b,[(la+k,lo+k),(lc-k,lo+k),(lc-k,hi-k),(la+k,hi-k)],
                    lambda u,z,off:legacy._plane_point(pl,u,z,off),normal,front=-.206,back=-.60)
    glass_pane(b,[legacy._plane_point(pl,u,z,-.20) for u,z in
                  [(la+k,lo+k),(lc-k,lo+k),(lc-k,hi-k),(la+k,hi-k)]],
               normal,reconstructed)
    for u0,u1,z0_,z1_ in [(la,la+k,lo,hi),(lc-k,lc,lo,hi),
                          (la,lc,lo,lo+k),(la,lc,hi-k,hi)]:
        slab(b,pl,u0,u1,z0_,z1_,-.195,-.13,reconstructed,PAINTED_WOOD)
    slab(b,pl,la-.065,lc+.065,lo-.055,lo+.012,-.07,.09,reconstructed,PAINTED_WOOD)
    linen_shade(b,la,lc,lo,hi,lambda u,z,off:legacy._plane_point(pl,u,z,off),
                normal,reconstructed,int((a*17+c*31+f*7+lo)*10003))

    # Cleared HABS4 and the licensed modern courtyard views bound the flared
    # foot and narrow side projection. Hidden depth and clay hip stock remain
    # reconstructions; the record keeps their uncertainty separate.
    ring,kick,apex,patches=dormer_roof(d)
    fascia=d.get('fascia_m',.075)  # T-2859: HABS4's apron fascia is about 0.10 ft
    for index,poly in enumerate(patches):
        poly=visible(poly)
        if poly:legacy._up(b,poly,reconstructed if index%2==0 else conf,ROOF)
    for p,q in zip(ring,ring[1:]+ring[:1]):
        lowp=(p[0],p[1],ze-fascia);lowq=(q[0],q[1],ze-fascia)
        facing=norm((p[0]+q[0]-2*apex[0],p[1]+q[1]-2*apex[1],0))
        poly=visible([lowp,lowq,q,p])
        if poly:b.raw(poly,reconstructed,PAINTED_WOOD,facing)
    poly=visible([(p[0],p[1],ze-fascia) for p in ring])
    if poly:b.raw(poly,reconstructed,PAINTED_WOOD,(0,0,-1))

    def hip_cap(p,q):
        if joined:
            from archetypes.masonry_house_v4_court import roof_height
            dp,dq=[v[2]-roof_height(b.params,v[0]) for v in (p,q)]
            if max(dp,dq)<=0:return
            if min(dp,dq)<0:
                intersection=tuple(p[k]+dp/(dp-dq)*(q[k]-p[k]) for k in range(3))
                if dp<0:p=intersection
                else:q=intersection
        if b.params.detail.get('roof_edges'):
            from archetypes.masonry_house_v4_roof_edges import hip_caps
            return hip_caps(b,p,q,d.get('hip_cover_radius_m',.047))
        # Small overlapping half-round clay covers make each actual hip
        # readable against the equally pitched red roof behind the dormer.
        tangent=norm(sub(q,p));across=norm(cross(tangent,(0,0,1)))
        outward=norm(cross(across,tangent));length=math.dist(p,q)
        count=max(1,math.ceil(length/.27));radius=.047
        for k in range(count):
            t0=k/count+.002/length;t1=min(1,(k+1)/count+.014/length)
            for j in range(8):
                angles=(math.pi*j/8,math.pi*(j+1)/8)
                def P(t,angle):
                    return tuple(p[h]+(q[h]-p[h])*t+
                                 radius*(across[h]*math.cos(angle)+outward[h]*math.sin(angle))+
                                 outward[h]*.009 for h in range(3))
                aa,cc=angles
                want=tuple(across[h]*math.cos((aa+cc)/2)+outward[h]*math.sin((aa+cc)/2) for h in range(3))
                b.raw([P(t0,aa),P(t1,aa),P(t1,cc),P(t0,cc)],reconstructed,19+k%3,want)
    # T-2859: HABS sheet 4 draws each hip as one line that dies under the
    # finial's bell, so the cover stops inside the bell's lowest ring instead
    # of running on through it to the apex and burying the bell.
    spec=b.params.detail.get('court_finial');rim=None
    if spec:rim=.85*spec.get('dormer_profile_ft',spec['profile_ft'])[0][1]*.3048
    for p,v in zip(ring,kick):
        hip_cap(p,v);top=apex
        reach=math.hypot(v[0]-apex[0],v[1]-apex[1])
        if rim and reach>rim:top=tuple(v[h]+(apex[h]-v[h])*(1-rim/reach) for h in range(3))
        hip_cap(v,top)
    # HABS05 shows the cap/finial form; owner image(10) confirms their clay
    # material. A green copper vent was not supported by either comparison.
    if b.params.detail.get('court_finial'):court_finial(b,apex[0],apex[1],'dormer',ROOF)
    else:legacy._finial(b,apex[0],apex[1],za,.35,reconstructed,ROOF)

def curved_masonry(b,cx,cy,r,z0,z1,conf,mat,windows,a0=0,a1=2*math.pi,hidden_box=None):
    """Continuous cylindrical face with windows removed in angular coordinates."""
    breaks={a0,a1,*[a0+(a1-a0)*i/48 for i in range(49)]}
    for w in windows:breaks.update((max(a0,w['a0']),min(a1,w['a1'])))
    breaks=sorted(a for a in breaks if a0<=a<=a1)
    for a,c in zip(breaks,breaks[1:]):
        mid=(a+c)/2
        relevant=[w for w in windows if w['a0']-1e-8<mid<w['a1']+1e-8]
        zs=sorted({z0,z1,*[max(z0,min(z1,w[k])) for w in relevant for k in ('z0','z1')]})
        for lo,hi in zip(zs,zs[1:]):
            if any(w['z0']<=(lo+hi)/2<=w['z1'] for w in relevant):continue
            p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
            pts=[(*p,lo),(*q,lo),(*q,hi),(*p,hi)]
            if dot(legacy._normal(pts),(math.cos(mid),math.sin(mid),0))<0:pts.reverse()
            if hidden_box:
                from archetypes.masonry_house_v4_court import outside_box
                for part in outside_box(pts,hidden_box):b.wall(part,conf,mat)
            else:b.wall(pts,conf,mat)


def tower(b,t,params):
    if t['name']=='north' and params.detail.get('north_tower_roof'):
        from archetypes.masonry_house_v4_north_tower import build
        return build(b,t,params)
    data=params.detail.get('tower_stair_windows') if t['name']=='stair' else None
    if not data:
        legacy._tower(b,{**t,'segments':48})
        return
    r,cx,cy,conf=t['r'],t['cx'],t['cy'],t['conf_wall'];windows=[]
    for w in data['openings']:
        half=w['width_m']/(2*r)
        windows.append({**w,'a0':w['angle']-half,'a1':w['angle']+half})
    hidden=None
    if getattr(b,'reduced_sash',False) and params.detail.get('light_hidden_stair_wall'):
        from archetypes.masonry_house_v4_court import concealed_stair_box
        hidden=concealed_stair_box(params,t)
    curved_masonry(b,cx,cy,r,t['z0'],t['wall_top_z'],conf,BRICK,windows,hidden_box=hidden)
    for w in windows:
        a,c=w['a0'],w['a1'];p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
        lantern=w['z0']>=data['bands'][0][0]
        facet_window(b,p,q,w['z0'],w['z1'],(math.cos(w['angle']),math.sin(w['angle']),0),conf,stone_jambs=False,
                     panes=data['lantern_panes'] if lantern else None,surrounds=not lantern,
                     stones_m=None if lantern else data.get('slit_stones_m'))
    from archetypes.masonry_house_v4_rough_bands import add_rough_band
    for z0,z1 in data['bands']:
        add_rough_band(b,cx,cy,r+.06,z0,z1,conf)
    legacy._cone(b,cx,cy,t['eave_r'],t['wall_top_z'],t['apex_z'],t['conf_roof'],ROOF,72,soffit=r)
    if t['name']=='stair' and params.detail.get('court_finial'):
        from archetypes.masonry_house_v4_court import court_finial
        court_finial(b,cx,cy,'stair',COPPER)
    else:legacy._finial(b,cx,cy,t['apex_z'],t['finial_m'],t['conf_roof'],COPPER)


def terrace(b,params):
    from archetypes.masonry_house_v4_terrace import build
    if build(b,params):return
    data=params.detail.get('bow_terrace')
    if not data or not params.bows:return
    w=params.bows[0];a0,a1=sorted((w['a0'],w['a1']))
    if a1-a0>math.pi:a0,a1=a1,a0+2*math.pi
    r,cx,cy,z1=data['r'],data['cx'],data['cy'],data['z1'];conf=params.detail['conf']
    floor=z1-.18;coping=data['coping_m'];parapet=data['parapet_m']
    windows=[];n=data['window_count'];lo,hi=data['window_z']
    for i in range(n):
        mid=a0+(a1-a0)*(i+.5)/n;half=(a1-a0)/n*.22
        windows.append({'a0':mid-half,'a1':mid+half,'z0':lo,'z1':hi})
    curved_masonry(b,cx,cy,r,0,floor,conf,BRICK,windows,a0,a1)
    for op in windows:
        aa,cc=op['a0'],op['a1'];mid=(aa+cc)/2
        p=(cx+r*math.cos(aa),cy+r*math.sin(aa));q=(cx+r*math.cos(cc),cy+r*math.sin(cc))
        facet_window(b,p,q,lo,hi,(math.cos(mid),math.sin(mid),0),conf,small=True,stone_jambs=False)
        length=math.dist(p,q);count=max(3,round(length/.12))
        for i in range(count+1):
            x=p[0]+(q[0]-p[0])*i/count;y=p[1]+(q[1]-p[1])*i/count
            cylinder(b,x,y,lo+.02,hi-.02,.012,conf,IRON,6)
    inner=w['r'];steps=64
    def top(angle):
        t=(angle-a0)/(a1-a0)
        ramp=1 if t<.8 else .5+.5*math.cos(math.pi*(t-.8)/.2)
        return floor+.07+parapet*ramp
    for i in range(steps):
        a=a0+(a1-a0)*i/steps;c=a0+(a1-a0)*(i+1)/steps
        def P(rad,angle,z):return (cx+rad*math.cos(angle),cy+rad*math.sin(angle),z)
        mid=(a+c)/2;want=(math.cos(mid),math.sin(mid),0)
        # Both sides of the parapet are brick, and its floor remains behind it.
        outer=[P(r,a,floor),P(r,c,floor),P(r,c,top(c)),P(r,a,top(a))]
        b.wall(outer,conf,BRICK)
        inside=[P(r-data['thick_m'],c,floor),P(r-data['thick_m'],a,floor),P(r-data['thick_m'],a,top(a)),P(r-data['thick_m'],c,top(c))]
        b.wall(inside,conf,BRICK)
        b.raw([P(inner,a,floor),P(r-data['thick_m'],a,floor),P(r-data['thick_m'],c,floor),P(inner,c,floor)],conf,DRIVE,(0,0,1))
        b.raw([P(r-data['thick_m'],a,top(a)+coping),P(r+.06,a,top(a)+coping),P(r+.06,c,top(c)+coping),P(r-data['thick_m'],c,top(c)+coping)],conf,TRIM,(0,0,1))
        b.raw([P(r+.06,a,top(a)),P(r+.06,c,top(c)),P(r+.06,c,top(c)+coping),P(r+.06,a,top(a)+coping)],conf,TRIM,want)
    old=b.decorate;b.decorate=False
    end=(cx+(r-.65)*math.cos(a1),cy+(r-.65)*math.sin(a1));width=1.25;run=.29;count=data['stair_steps']
    for i in range(count):
        z=floor*(count-i)/count;y=end[1]-run*(i+1)
        legacy._box(b,end[0]-width,y,0,end[0],y+run,z,conf,TRIM)
        # A thin projecting tread nose makes each normal-height riser legible.
        legacy._box(b,end[0]-width-.02,y-.035,z-.045,end[0]+.02,y+run,z,conf,TRIM)
    b.decorate=old


def service_stair(b,params):
    """HABS sheet 2 north service landing and south-descending flight.

    The record owns the measured plan and threshold. Slab, cheek/support and
    simple iron rail construction are bounded reconstructions from courtyard
    photographs, distinct from the excluded later stair south of the stable.
    """
    street = params.detail.get('north_service_junction')
    if street:
        # HABS01 shows two exposed stone treads at the north service door.
        # Solid bases close the grade interface; the top tread reaches the
        # recessed leaf instead of ending at the outer wall plane.
        old = b.decorate
        b.decorate = False
        x0, x1 = street['step_x']; y = street['wall_y']
        for run, top in zip(street['step_runs'], street['step_heights']):
            legacy._box(b, x0, y-.30, 0, x1, y+run, top, 1.0, GRANITE)
        from archetypes.masonry_house_v4_rainwater import _downpipe
        if not params.detail.get('rainwater'):
            _downpipe(b, street['gable_foot_x'], y+.13,
                      street['eave_z']-.20*street['roof_pitch'],
                      inlet=(street['gable_foot_x'], y+.23))
        b.decorate = old
    s=params.detail.get('north_court_service_stair')
    if not s:return
    if params.detail.get('service_access'):
        from archetypes.masonry_house_v4_service import build_stair
        build_stair(b,params)
        return
    x0,x1=s['landing_x'];y0,y1=s['landing_y'];z=s['landing_z']
    fx0,fx1=s['flight_x'];fy0,fy1=s['flight_y']
    conf=params.detail['conf'];old=b.decorate;b.decorate=False
    thickness=.14
    legacy._box(b,x0,y0,z-thickness,x1,y1,z,conf,TRIM)
    # Two slim brick supports leave the documented garden-level wall visible.
    b.decorate=True
    for x in (x1-.23,(x0+x1)/2):
        legacy._box(b,x-.13,y0+.06,0,x+.13,y0+.32,z-thickness,conf,BRICK)
    count=s['steps'];run=(fy1-fy0)/count;rise=z/count
    b.decorate=False
    for i in range(count):
        a=fy0+run*i;c=a+run;top=rise*(i+1)
        legacy._box(b,fx0,a,0,fx1,c,top,conf,TRIM)
        legacy._box(b,fx0-.015,a-.025,top-.04,fx1+.015,c,top,conf,TRIM)
    # A brick cheek under the outside tread ends, never a solid landing plinth.
    b.decorate=True
    for x,want in ((fx1+.045,(1,0,0)),(fx1-.105,(-1,0,0))):
        poly=[(x,fy0,0),(x,fy1,0),(x,fy1,z-.10),(x,fy0,.04)]
        if dot(legacy._normal(poly),want)<0:poly.reverse()
        b.wall(poly,conf,BRICK)
    b.decorate=False

    def rail(a,c):
        height=s['rail_height_m'];length=math.dist(a,c)
        posts=max(1,math.ceil(length/.6))
        for i in range(posts+1):
            t=i/posts;p=tuple(a[k]+(c[k]-a[k])*t for k in range(3))
            cylinder(b,p[0],p[1],p[2],p[2]+height,.013,conf,IRON,6)
        # Square iron handrail plus one light horizontal lower member.
        direction=norm(sub(c,a));side=norm((-direction[1],direction[0],0))
        for level in (.16,height):
            half=.018 if level==height else .010
            points=[]
            for p in (a,c):
                points.append([(p[0]+side[0]*u,p[1]+side[1]*u,p[2]+level+v)
                               for u,v in ((-half,-half),(half,-half),(half,half),(-half,half))])
            for i in range(4):
                j=(i+1)%4
                b.raw([points[0][i],points[1][i],points[1][j],points[0][j]],conf,IRON)
    rail((fx1+.025,y0-.015,z),(x1-.03,y0-.015,z))
    rail((x1-.03,y0,z),(x1-.03,y1,z))
    for x in (fx0-.025,fx1+.025):
        rail((x,fy0,rise),(x,fy1,z))
    b.decorate=old


def underpass(b,params):
    from archetypes.masonry_house_v4_frontage import passage_floor
    u=params.detail.get('underpass')
    if not u:return
    p,q,r,s=u['pts'];zp,zc,z0=u['ceiling_prairie_z'],u['ceiling_court_z'],u['floor_z']
    # Open ends, two masonry reveals, sloping soffit, continuous paving.
    for a,c,za,zc1 in [(p,s,zp,zc),(r,q,zc,zp)]:
        pts=[(*a,z0),(*c,z0),(*c,zc1),(*a,za)]
        mid=tuple((p[k]+q[k]+r[k]+s[k])/4 for k in range(2))
        want=(mid[0]-(a[0]+c[0])/2,mid[1]-(a[1]+c[1])/2,0)
        if dot(legacy._normal(pts),want)<0:pts.reverse()
        b.wall(pts,params.detail['conf'],BRICK)
    b.raw([(*p,zp),(*q,zp),(*r,zc),(*s,zc)],params.detail['conf'],TRIM,(0,0,-1))
    if passage_floor(b,params):return
    b.raw([(*p,z0+.006),(*q,z0+.006),(*r,z0+.006),(*s,z0+.006)],params.detail['conf'],DRIVE,(0,0,1))
    for i in range(1,19):
        t=i/19;a=(p[0]+(s[0]-p[0])*t,p[1]+(s[1]-p[1])*t);c=(q[0]+(r[0]-q[0])*t,q[1]+(r[1]-q[1])*t)
        b.raw([(*a,z0+.007),(*c,z0+.007),(c[0]-.012,c[1],z0+.007),(a[0]-.012,a[1],z0+.007)],params.detail['conf'],MORTAR,(0,0,1))



def date_device(b,stone,a,c,z0,z1,right,off,mat,conf):
    """A monogram drawn as its strokes, not set in a font (T-2869).

    HABS photograph 14 reads the north stack's upper stone as one joined device:
    two bowls facing outward, each closed by a stem, and a bar between the stems at
    mid-height. `device` gives the stems' places as shares of the device's width,
    the bar's height as a share of its height, and the stroke as a share of its
    height; `fill` and `height_fill` its share of the stone.
    """
    d=stone['device'];w=stone['fill']*(c-a);h=stone['height_fill']*(z1-z0)
    t=d['stroke']*h;cu,cz=(a+c)/2,(z0+z1)/2
    s1,s2=(-w/2+u*w for u in d['stems_u']);bar=-h/2+d['bar_z']*h

    def quad(pts):
        b.raw([legacy._plane_point(stone,cu+right*u,cz+v,off) for u,v in pts],conf,mat,legacy._plane_dir(stone))
    for s in (s1,s2):
        quad([(s-t/2,-h/2),(s+t/2,-h/2),(s+t/2,h/2),(s-t/2,h/2)])
    quad([(s1,bar-t/2),(s2,bar-t/2),(s2,bar+t/2),(s1,bar+t/2)])
    # Each bowl a half-ellipse from its stem's centre line out to the device's edge.
    for s,rx,side in ((s1,s1+w/2,-1),(s2,w/2-s2,1)):
        n=12
        for i in range(n):
            ring=[]
            for k,r in ((i,0),(i+1,0),(i+1,t),(i,t)):
                q=math.pi*(k/n-.5)
                ring.append((s+side*(rx-r)*math.cos(q),(h/2-r)*math.sin(q)))
            quad(ring)


def _face_reach(b,plane,u0,u1,v0,v1):
    """How far the faces already built stand in front of ``plane`` over a patch.

    Returns reach(u, v): the front-most offset of any face drawn so far whose
    projection on the plane covers (u, v) and that stands within the rock's
    reach of it, so a mark cut in a rock face can lie on that face. Where
    nothing covers a point (a joint's gap), the patch's median reach serves.
    """
    axis=0 if plane['axis']=='x' else 1
    side=1-axis;at,sign=plane['at'],plane['sign']
    lo,hi=-.02,ROCK_FACE_MAX+.01;pad=.03
    tris=[]
    for face in b.faces:
        pts=[b.verts[i] for i in face]
        offs=[(p[axis]-at)*sign for p in pts]
        if min(offs)<lo or max(offs)>hi:continue
        us=[p[side] for p in pts];vs=[p[2] for p in pts]
        if max(us)<u0-pad or min(us)>u1+pad or max(vs)<v0-pad or min(vs)>v1+pad:continue
        for k in range(1,len(pts)-1):
            tris.append(tuple((us[i],vs[i],offs[i]) for i in (0,k,k+1)))
    def hit(u,v):
        best=None
        for (ax,ay,ao),(bx,by,bo),(cx,cy,co) in tris:
            det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(det)<1e-12:continue
            l1=((by-cy)*(u-cx)+(cx-bx)*(v-cy))/det
            l2=((cy-ay)*(u-cx)+(ax-cx)*(v-cy))/det
            l3=1-l1-l2
            if min(l1,l2,l3)<-1e-9:continue
            o=l1*ao+l2*bo+l3*co
            if best is None or o>best:best=o
        return best
    found=[o for o in (hit(u0+(u1-u0)*i/8,v0+(v1-v0)*j/8) for i in range(9) for j in range(9))
           if o is not None]
    fallback=sorted(found)[len(found)//2] if found else PITCH_LINE
    def reach(u,v):
        o=hit(u,v)
        return fallback if o is None else o
    return reach


def date_stones(b,params):
    """The north-gable chimney's 1886 and AD stones, as HABS photograph 4 reads them.

    The figures and the monogram are cut INTO the dressed stones, so they draw as
    dark strokes on the face rather than raised letters, and two incised crosses
    flank the date. A glyph's advance runs to the viewer's right as seen from
    outside: on this north face that is -x, the handedness T-2214 found reversed.
    Letterforms are Blender's built-in face, a bounded stand-in for the carver's.
    """
    import bpy
    conf=params.detail['conf']
    for stone in params.detail.get('date_stones',[]):
        a,c,z0,z1=stone['u0'],stone['u1'],stone['z0'],stone['z1']
        # Sheet 6 draws both stones about 0.2 ft proud of the stack's line, which
        # is its rock faces' furthest reach, not the plane they bow out from.
        proud=ROCK_FACE_MAX+.06 if stone.get('incised') else .06
        slab(b,stone,a,c,z0,z1,0,proud,conf,GRANITE)
        incised=stone.get('incised')
        right=-stone['sign'] if stone['axis']=='y' else stone['sign']
        if stone.get('device'):
            date_device(b,stone,a,c,z0,z1,right,(proud+.002) if incised else .064,
                        DARK_GLASS if incised else TRIM,conf)
            continue
        curve=bpy.data.curves.new('glessner_datestone_lettering','FONT')
        curve.body=stone['text'];curve.align_x='CENTER';curve.align_y='CENTER'
        curve.size=(z1-z0)*.82
        curve.extrude=0 if incised else .0015;curve.bevel_depth=0 if incised else .001
        ob=bpy.data.objects.new('temporary_datestone_letters',curve)
        bpy.context.scene.collection.objects.link(ob)
        mesh=ob.to_mesh()
        xs=[v.co.x for v in mesh.vertices];ys=[v.co.y for v in mesh.vertices]
        scale,dx,dy=1.0,0.0,0.0
        if stone.get('fill') and xs:
            # The photograph's share of the stone's width the lettering spans,
            # never taller than 0.6 of the stone.
            w,h=max(xs)-min(xs),max(ys)-min(ys)
            scale=min(stone['fill']*(c-a)/w,.6*(z1-z0)/h)
            dx,dy=(max(xs)+min(xs))/2,(max(ys)+min(ys))/2
        # A cut in sunlit granite reads as its shadow: the matte near-black lining.
        mat,off=(DARK_GLASS,proud+.002) if incised else (TRIM,.064)
        for poly in mesh.polygons:
            pts=[]
            for i in poly.vertices:
                v=mesh.vertices[i].co
                pts.append(legacy._plane_point(stone,(a+c)/2+right*(v.x-dx)*scale,
                                               (z0+z1)/2+(v.y-dy)*scale,off+v.z))
            b.raw(pts,conf,mat,legacy._plane_dir(stone))
        ob.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True);bpy.data.curves.remove(curve)
    for cross in params.detail.get('date_crosses',[]):
        u,z,r,t=cross['u'],cross['z'],cross['size']/2,cross['stroke']/2
        # T-3028: a cut line follows the rock it is cut in. At ROCK_FACE_MAX the
        # strokes stood 2-4 cm proud of the stone round them (T-3065 read its
        # reach there at 0.06-0.08 m), so they floated; HABS 14 shows them cut.
        # Each stroke is draped, cell by cell, 2 mm over the stack's own face;
        # the upright is two arms either side of the bar, so no face is drawn twice.
        reach=_face_reach(b,cross,u-r,u+r,z-r,z+r)
        for u0,u1,v0,v1 in ((u-r,u+r,z-t,z+t),(u-t,u+t,z+t,z+r),(u-t,u+t,z-r,z-t)):
            nu,nv=max(1,math.ceil((u1-u0)/.012)),max(1,math.ceil((v1-v0)/.012))
            us=[u0+(u1-u0)*i/nu for i in range(nu+1)];vs=[v0+(v1-v0)*j/nv for j in range(nv+1)]
            off={(i,j):reach(p,q)+.002 for i,p in enumerate(us) for j,q in enumerate(vs)}
            for i in range(nu):
                for j in range(nv):
                    b.raw([legacy._plane_point(cross,us[a],vs[c],off[a,c])
                           for a,c in ((i,j),(i+1,j),(i+1,j+1),(i,j+1))],
                          conf,DARK_GLASS,legacy._plane_dir(cross))
    ledge=params.detail.get('pigeon_ledge')
    if ledge:
        slab(b,ledge,ledge['u0'],ledge['u1'],ledge['z0'],ledge['z1'],0,ledge['projection_m'],params.detail['conf'],GRANITE)
        # The two corbels HABS photograph 15 shows under it (T-2849); their
        # projection is reconstructed (L-glessner-stable-gable-2849).
        for u0,u1 in ledge.get('corbels',[]):
            slab(b,ledge,u0,u1,ledge['z0']-ledge['corbel_drop_m'],ledge['z0'],0,
                 ledge['corbel_projection_m'],1.0,GRANITE)

def north_entry(b,p):
    """Open vaulted porch, west-facing door up the left-turn stair (HABS 2–3)."""
    d=p.detail.get('north_entry_alcove')
    if not d:return
    a,c=d['x'];yf,yb=d['front_y'],d['back_y'];east=d['east_x'];conf=p.detail['conf']
    landing,threshold=d['landing_z'],d['threshold_z']
    arch=next(o for o in p.openings if o.get('style')=='north_entry_alcove')
    poly=aperture(arch)
    # The arch return passes through the outer masonry only. Extruding its
    # low spring line across the room blocks the rising left-turn flight.
    for (u,z),(v,zz) in zip(poly,poly[1:]+poly[:1]):
        if max(z,zz)<.01:continue
        end=yf-.35
        b.raw([(u,yf,z),(v,yf,zz),(v,end,zz),(u,end,z)],conf,GRANITE)
    wp={'axis':'y','sign':1,'at':yb,'face':'north','kind':'window',
        'u0':d['window_x'][0],'u1':d['window_x'][1],'z0':d['window_z'][0],
        'z1':d['window_z'][1],'conf':conf,'style':'courtyard_sash'}
    dp={'axis':'x','sign':-1,'at':east,'face':'west','kind':'door',
        'u0':d['door_y'][0],'u1':d['door_y'][1],'z0':threshold,
        'z1':d['door_top'],'conf':conf,'style':'service_door'}
    b.openings.extend([wp,dp])
    top=d['door_top']+.3
    b.wall([(a,yb,landing),(a,yb,top),(east,yb,top),(east,yb,landing)],conf,GRANITE)
    b.wall([(east,yb,landing),(east,yb,top),(east,yf-.3,top),(east,yf-.3,landing)],conf,GRANITE)
    b.wall([(a,yb,landing),(a,yf-.35,landing),(a,yf-.35,top),(a,yb,top)],conf,GRANITE)
    b.raw([(a,yb,top),(east,yb,top),(east,yf-.35,top),(a,yf-.35,top)],conf,GRANITE,(0,0,-1))
    opening(b,wp);opening(b,dp)
    old=b.decorate;b.decorate=False
    legacy._box(b,a,yb,0,east,yf,landing,conf,TRIM)
    # Front approach uses the right half of the arch; the left half has the
    # low stone cheek, leaving the turn and ascending treads visible behind it.
    ca,cc=d['cheek_x'];n=d['front_steps'];run=d['front_run']/n
    for i in range(n):
        h=landing*(i+1)/n;front=yf+run*(n-i)
        legacy._box(b,a-.12,front-run,0,ca+.05,front,h,conf,TRIM)
        legacy._box(b,a-.15,front-run,h-.045,ca+.08,front+.025,h,conf,TRIM)
    sx0,sx1=d['stair_x'];sy0,sy1=d['stair_y'];n=d['stair_steps'];run=(sx1-sx0)/n
    for i in range(n):
        x=sx0+i*run;h=landing+(threshold-landing)*(i+1)/n
        legacy._box(b,x,sy0,landing,x+run,sy1,h,conf,TRIM)
        legacy._box(b,x-.025,sy0-.025,h-.045,x+run,sy1+.025,h,conf,TRIM)
    from archetypes.masonry_house_v4_north import porch_cheek
    porch_cheek(b,d,landing)
    b.decorate=old


def west_hood(b,p,d):
    """Timber dormer with tile cheeks and the hood generated in the roof union."""
    from archetypes.masonry_house_v4_west_roof import height, patches
    r=next(r for r in p.ranges if r.get('stable_roof'))
    a,c=d['u0'],d['u1'];front,back=d['front'],d['back'];conf=d['conf']
    overhang=d.get('hood_overhang_m',.25)
    pl={'axis':'x','sign':-1,'at':front}
    # The wide opening in sheet 3 belongs up here, above the four lower lights.
    o={**pl,'face':'west','kind':'window','u0':a+.22,'u1':c-.22,
       'z0':d['eave_z']-1.35,'z1':d['eave_z']-.13,'conf':conf,'style':'west_hood_clear'}
    apron_front=r['x0']-.10
    apron_z=height(r,apron_front,(a+c)/2)+.025
    # The upper envelope trims the host at the hood's overhang, while the
    # timber cheeks sit 25 cm inward. Return the host roof under those two
    # overhangs, clipped to its exact planes, so neither cheek has an open seam.
    for _,pts in patches(r,include_dormer=False):
        p0,p1,p2=pts[:3]
        normal=legacy._normal([p0,p1,p2])
        def roof_z(x,y):
            return p0[2]-(normal[0]*(x-p0[0])+normal[1]*(y-p0[1]))/normal[2]
        for lo,hi in ((a-overhang,a),(c,c+overhang)):
            strip=rect_clip([(v[0],v[1]) for v in pts],
                            d['hood_front'],lo,back,hi)
            if strip:
                fragments=[strip]
                if d.get('connected_ridge'):
                    fragments=[]
                    for name,hood in patches(r,True):
                        if not name.startswith('dormer'):continue
                        part=strip
                        poly=[(v[0],v[1]) for v in hood]
                        if area(poly)<0:poly.reverse()
                        for pa,pb in zip(poly,poly[1:]+poly[:1]):part=clip(part,pa,pb)
                        if part:fragments.append(part)
                for fragment in fragments:
                    legacy._two_sided_roof(b,[(x,y,roof_z(x,y)) for x,y in fragment],conf,ROOF)
    old=b.decorate;b.decorate=False
    # Wooden boards around an actual aperture; no opaque panel behind the glass.
    # The sash is set into the roof, above a steep tiled apron. A tall wooden
    # face here falsely turns the small hood into a box rising from the eave.
    b.decorate=old
    legacy._two_sided_roof(b,[(apron_front,a,apron_z),(front,a,o['z0']),
                            (front,c,o['z0']),(apron_front,c,apron_z)],conf,ROOF)
    b.decorate=False
    slab(b,pl,a,c,o['z1'],d['eave_z'],-.03,.03,conf,23)
    slab(b,pl,a,o['u0'],o['z0'],o['z1'],-.03,.03,conf,23)
    slab(b,pl,o['u1'],c,o['z0'],o['z1'],-.03,.03,conf,23)
    for u in (a,c):
        zf=height(r,front,u);zb=height(r,back,u)
        b.raw([(apron_front,u,apron_z),(front,u,zf),(front,u,o['z0'])],conf,ROOF,
              (0,-1 if u==a else 1,0))
        cheek_back=back
        if d.get('connected_ridge') and zb>d['eave_z']:
            cheek_back=front+(back-front)*(d['eave_z']-zf)/(zb-zf)
            zb=d['eave_z']
        cheek=[(front,u,zf),(cheek_back,u,zb),(cheek_back,u,d['eave_z']),(front,u,d['eave_z'])]
        want=(0,-1 if u==a else 1,0)
        if dot(legacy._normal(cheek),want)<0:cheek.reverse()
        b.tiles(cheek,conf)
    opening(b,o)
    # Outward fascia, sill and small hood brackets are visible from below.
    slab(b,pl,a-overhang,c+overhang,d['eave_z']-.10,d['eave_z'],-.02,d['front']-d['hood_front'],conf,23)
    for u in (a+.1,c-.1):
        slab(b,pl,u-.06,u+.06,d['eave_z']-.42,d['eave_z']-.08,0,.22,conf,23)
    legacy._finial(b,d['crest_x'],(a+c)/2,d['apex_z'],d.get('finial_m',.41),conf,COPPER)
    b.decorate=old


def supplemental(b,p):
    north_entry(b,p)
    from archetypes.masonry_house_v4_north import stable_fabric
    stable_fabric(b,p)
    g=p.detail.get('west_cross_gable')
    if g and not any(r.get('north_cross_gable') for r in p.ranges):
        lo,hi=g['u0'],g['u1'];base=min(g['eave_lo_z'],g['eave_hi_z'])
        # Existing west wall owns the wall below the crossed roof's eaves.
        poly=[(lo,base),(hi,base),(hi,g['eave_hi_z']),(g['ridge_at'],g['ridge_z']),(lo,g['eave_lo_z'])]
        pts=[legacy._plane_point(g,u,z,.012) for u,z in poly]
        legacy._poly_facing(b,pts,g['conf'],GRANITE,legacy._plane_dir(g))
    d=p.detail.get('west_dormer')
    if d and d.get('style')=='hipped_flared_hood':
        west_hood(b,p,d)
    elif d:
        a,c=d['u0'],d['u1'];mid=(a+c)/2;pl={'axis':'x','sign':-1,'at':d['front']}
        o={**pl,'face':'west','kind':'window','u0':a+.35,'u1':c-.35,'z0':d['z0']+.15,'z1':d['eave_z']-.10,'conf':d['conf']}
        b.openings.append(o)
        pts=[legacy._plane_point(pl,a,d['z0']),legacy._plane_point(pl,c,d['z0']),legacy._plane_point(pl,c,d['eave_z']),legacy._plane_point(pl,mid,d['apex_z']),legacy._plane_point(pl,a,d['eave_z'])]
        legacy._poly_facing(b,pts,d['conf'],GRANITE,(-1,0,0))
        for u in (a,c):
            pts=[(d['front'],u,d['z0']),(d['back'],u,d['z0']),(d['back'],u,d['eave_z']),(d['front'],u,d['eave_z'])]
            legacy._poly_facing(b,pts,d['conf'],BRICK,(0,-1 if u==a else 1,0))
            legacy._two_sided_roof(b,[(d['front']-.1,u,d['eave_z']),(d['back'],u,d['eave_z']),(d['back'],mid,d['apex_z']),(d['front']-.1,mid,d['apex_z'])],d['conf'],ROOF)
        opening(b,o)
    r=p.detail.get('copper_return')
    if r and not p.detail.get('continuous_copper_corner'):
        z=r['wall_top_z'];zt=z+r['rise_m']
        copper_seams(b,[(r['x0'],r['y0'],z),(r['x1'],r['y0'],z),(r['x1'],r['y1'],zt),(r['x0'],r['y1'],zt)],r['conf'])
        # Folded front fascia gives the metal roof its thickness in silhouette.
        b.raw([(r['x0'],r['y0'],z-.055),(r['x1'],r['y0'],z-.055),(r['x1'],r['y0'],z),(r['x0'],r['y0'],z)],r['conf'],COPPER,(0,-1,0))


    if p.detail.get('dining_crested_connection'):
        from archetypes.masonry_house_v4_courtyard_roof import add_dining_roof
        add_dining_roof(b,p)
    elif p.detail.get('dining_roof_junction'):
        from archetypes.masonry_house_v4_courtyard_roof import dining
        for tri in dining(p)[0]:
            legacy._two_sided_roof(b,list(tri),1.0,ROOF)
    if p.detail.get('continuous_copper_corner'):
        from archetypes.masonry_house_v4_copper import add_hood, add_north_cladding
        add_hood(b,p)
        add_north_cladding(b,p)



def _discard_export_scratch_uv(ob):
    """Remove only the unused unwrap layer from the evaluated v4 mesh.

    emit.unwrap must still see the original, edit-active BakeUV layer so that it
    cannot overwrite metric SurfaceUV. A Geometry Nodes modifier evaluates after
    that edit and removes BakeUV from export_apply=True's result. No geometry,
    material, SurfaceUV value or _CONFIDENCE attribute is changed, and no global
    emitter behavior is replaced. Keeping this opt-in avoids seven megabytes of
    unused texture coordinates in this unusually detailed inspection model.
    """
    import bpy
    graph = bpy.data.node_groups.new(f"{ob.name}_export_uv", "GeometryNodeTree")
    graph.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    graph.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    source = graph.nodes.new("NodeGroupInput")
    remove = graph.nodes.new("GeometryNodeRemoveAttribute")
    remove.inputs["Name"].default_value = "BakeUV"
    target = graph.nodes.new("NodeGroupOutput")
    graph.links.new(source.outputs["Geometry"], remove.inputs["Geometry"])
    graph.links.new(remove.outputs["Geometry"], target.inputs["Geometry"])
    modifier = ob.modifiers.new("Discard unused unwrap coordinates", "NODES")
    modifier.node_group = graph
    modifier.show_in_editmode = False


def gate_piece(b,w):
    """Keep legacy versions intact; both current detail tiers share the gate."""
    if 'ends' in w and not b.decorate and b.params.detail.get('surface_finish'):
        # Only the reduced boundary run is plain. Never remap individual bricks.
        from archetypes.masonry_house_v4_finish import FLAT_BRICK
        first=len(b.mat_index)
        legacy._gate_piece(b,w)
        for i in range(first,len(b.mat_index)):
            if b.mat_index[i]==BRICK:b.mat_index[i]=FLAT_BRICK
        return
    if b.params.detail.get('service_access'):
        from archetypes.masonry_house_v4_service import build_gate,build_jamb_piece
        if w.get('kind')=='gate':return build_gate(b,w)
        if build_jamb_piece(b,w):return
    return legacy._gate_piece(b,w)


def build(params,name):
    from archetypes.masonry_house_v4_materials import build_materials, assign_metric_uvs
    from archetypes.masonry_house_v4_landscape import add_lawn_blades
    from archetypes.masonry_house_v4_frontage import add_frontage
    from archetypes.masonry_house_v4_foundation import stair_tower_plinth
    from archetypes.masonry_house_v4_rainwater import add_courtyard_rainwater
    b=DetailBuilder(name,params)
    for r in params.ranges:legacy._range(b,r)
    for t in params.towers:tower(b,t,params)
    for w in params.bows:bow(b,w)
    for y in params.bays:bay(b,y,params)
    for d in params.dormers:dormer(b,d)
    for t in params.turrets:louvred_turret(b,t)
    for c in params.chimneys:chimney(b,c)
    for o in params.openings:
        courtyard=(o['face']=='south' and o['at']>1) or (o['face']=='west' and o['at']>1) or (o['face']=='east' and o['at']<params.width_m-1)
        opening(b,o,courtyard)
    b.decorate=False
    for n in params.bands:
        legacy._band(b,n)
        # Moulded projecting cornice with a restrained dentil line below the roof.
        slab(b,n,n['u0'],n['u1'],n['z0']-.055,n['z0']+.025,.07,n['proj_m']+.025,n['conf'],TRIM)
        for i in range(max(1,int((n['u1']-n['u0'])/.16))):
            u=n['u0']+i*.16
            slab(b,n,u,u+.075,n['z0']-.125,n['z0']-.05,.015,.07,n['conf'],TRIM)
    b.decorate=True
    for w in params.walls:gate_piece(b,w)
    b.decorate=False
    from archetypes.masonry_house_v4_ground import build as build_ground
    grass_params=build_ground(b,params)
    add_frontage(b,params)
    grass_blades=add_lawn_blades(b,grass_params)
    ornament.columns(b,params)
    roof_ridges(b,params)
    b.decorate=True
    supplemental(b,params)
    terrace(b,params)
    service_stair(b,params)
    underpass(b,params)
    date_stones(b,params)
    stair_tower_plinth(b,params)
    from archetypes.masonry_house_v4_entry import end_returns
    end_returns(b,params)
    add_courtyard_rainwater(b,params)
    if params.detail.get("roof_edges"):
        from archetypes.masonry_house_v4_roof_edges import add_edges
        add_edges(b,params)
    from archetypes.masonry_house_v4_vines import add_vines
    vines=add_vines(b,params)
    obj=b.to_object(build_materials(params.colours,params.detail.get('rainwater'),params.detail.get('vines'),params.detail.get('surface_finish')))
    assign_metric_uvs(obj,b.roof_uvs)
    _discard_export_scratch_uv(obj)
    # T-2400: the granite's stone-scale occlusion, on its own TEXCOORD_1.
    from archetypes.masonry_house_v4_occlusion import bake_stone_occlusion
    bake_stone_occlusion(obj)
    obj['detail_profile']='glessner_v4'
    obj['masonry_blocks']=b.masonry_blocks
    obj['roof_tiles']=b.roof_tiles
    obj['grass_blades']=grass_blades
    obj['vine_plants']=len(vines['plants'])
    obj['vine_leaflets']=sum(p['leaves'] for p in vines['plants'])
    axial=len([o for o in params.openings if o['kind'] not in ('fan','band')])
    bowed=sum(w['lights_per_row']*len(w['light_rows']) for w in params.bows)
    round_tower=len(params.detail.get('tower_stair_windows',{}).get('openings',[]))
    dining=0
    for bay_data in params.bays:
        facets=sum(math.dist(a,c)>1.2 for a,c in zip(bay_data['pts'],bay_data['pts'][1:]))
        dining+=facets*int(bool(bay_data['light_row']))
        if params.detail.get('dining_garden_window_z'):
            dining+=sum(0<=i<facets for i in params.detail.get('dining_garden_window_facets',[0,2,4]))
    dormers=len(params.dormers)+int(bool(params.detail.get('west_dormer')))
    terrace_windows=params.detail.get('bow_terrace',{}).get('window_count',0)
    obj['openings_recessed']=axial+bowed+round_tower+dining+dormers+terrace_windows
    obj['aperture_counts']={'axial':axial,'hall_bow':bowed,'stair_tower':round_tower,
                            'dining_bay':dining,'dormers':dormers,'terrace':terrace_windows}
    obj['opening_recess_depth_m']=.29
    return obj
