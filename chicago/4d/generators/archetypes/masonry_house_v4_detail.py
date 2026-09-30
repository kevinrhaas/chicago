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


def aperture(o):
    a,b,z0,z1 = o['u0'],o['u1'],o['z0'],o['z1']
    if o['kind'] == 'arch':
        c,r,zs = (a+b)/2,(b-a)/2,o['spring_z']
        return [(a,z0),(b,z0)] + [(c+r*math.cos(math.pi*i/24),zs+r*math.sin(math.pi*i/24)) for i in range(25)]
    return [(a,z0),(b,z0),(b,z1),(a,z1)]


class DetailBuilder(MeshBuilder):
    def __init__(self, name, params):
        super().__init__(name)
        self.params = params
        self.decorate = True
        self.openings = list(params.openings)
        # The Prairie upper colonnades are open between the individual lights.
        # Remove the square masonry piers, then draw the round colonnettes below.
        upper = sorted([o for o in params.openings if o['kind']=='window' and
                        o['face']=='east' and o['z0']>5], key=lambda o:(round(o['at'],3),round(o['z0'],2),o['u0']))
        for a,c in zip(upper,upper[1:]):
            if .12<c['u0']-a['u1']<.3 and abs(a['z0']-c['z0'])<.05 and abs(a['at']-c['at'])<.05:
                self.openings.append({**a,'u0':a['u1']-.001,'u1':c['u0']+.001,
                                      'z0':a['z0']+.05,'z1':a['z1']-.035})
        self.course_schedule = params.detail.get('ashlar_courses_m') or [0.4572,0.4572,0.3937,0.2413,0.3429,0.3683,0.1905,0.3683,0.1905,0.2921]
        self.masonry_blocks = self.roof_tiles = 0

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

    def add_poly(self, points, confidence, mat=0):
        pts = [tuple(p) for p in points]
        n = norm(legacy._normal(pts))
        if self.decorate and mat in (GRANITE,BRICK) and abs(n[2]) < .005:
            self.wall(pts,confidence,mat)
            return []
        if self.decorate and mat == ROOF and n[2] > .12:
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
        holes = []
        for o in self.openings:
            on = legacy._plane_dir(o)
            if dot(n,on)<.999 or abs(dot(legacy._plane_point(o,0,0),n)-d)>.055:
                continue
            if o['kind']=='fan':
                # Carved stone is seated inside the masonry, not overlaid on
                # rock faces. Its recessed bed closes the radial stone joints.
                centre=(o['u0']+o['u1'])/2;radius=o['r_out']
                cut=[(centre+radius*math.cos(math.pi*i/80),
                      o['spring_z']+radius*math.sin(math.pi*i/80)) for i in range(81)]
            elif o['kind']=='band':
                if not (o.get('face')=='east' and o['z0']>5 and o['u1']-o['u0']>3):
                    continue
                cut=[(o['u0']-.435,o['z0']-.025),(o['u1']+.435,o['z0']-.025),
                     (o['u1']+.435,o['z1']+.045),(o['u0']-.435,o['z1']+.045)]
            else:
                cut=aperture(o)
            holes.append([(dot(legacy._plane_point(o,s,z),u),z) for s,z in cut])
        for h in custom_holes or []:
            holes.append([(dot(p,u),p[2]) for p in h])
        for fragment in subtract(polygon,holes):
            self.raw([point(q,-.012) for q in fragment],confidence,MORTAR,n)
        x0,z0,x1,z1 = bounds(polygon)
        courses = []
        z = 0.0
        idx = 0
        while z < z1+1e-6:
            height = .066675 if mat == BRICK else self.course_schedule[idx%len(self.course_schedule)]
            if z+height > z0:
                courses.append((idx,max(z,z0),min(z+height,z1)))
            z += height
            idx += 1
        for row,za,zb in courses:
            if zb-za<.004:
                continue
            rng = random.Random(87013+row*719+int(d*997)+mat*821)
            width = .2159 if mat == BRICK else .85+min(.45,(zb-za)*.4)
            start = math.floor(x0/width)*width-(width/2 if row%2 else 0)
            a = start
            while a < x1-1e-6:
                w = width if mat==BRICK else width*rng.uniform(.65,1.4)
                c = a+w
                gap = .009 if mat==BRICK else .014
                tile = rect_clip(polygon,a+gap/2,za+gap/2,c-gap/2,zb-gap/2)
                if tile:
                    # A clipped fragment is not another physical stone. Build
                    # this stone once, then clip its already-finished surfaces.
                    self.block(tile,point,n,confidence,mat,rng,holes=holes)
                a = c

    def block(self, polygon, point, normal, confidence, mat, rng, holes=None):
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
            for piece in pieces:
                if not emitted:
                    self.masonry_blocks+=1
                    emitted=True
                self.raw([point((q[0],q[1]),q[2]) for q in piece],
                         confidence,variant,facing)

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
        # Large ashlar faces get several angular split planes, rather than a
        # single four-triangle pyramid. The envelope remains the measured course.
        rectangular=len(polygon)==4 and len({round(q[0],6) for q in polygon})==2 and len({round(q[1],6) for q in polygon})==2
        if rectangular and x1-x0>.48 and y1-y0>.16:
            xa,ya,xc,yc=bounds(inner);nx,ny=5,3;grid={}
            for ix in range(nx+1):
                for iy in range(ny+1):
                    xx=xa+(xc-xa)*ix/nx;yy=ya+(yc-ya)*iy/ny
                    boundary=ix in (0,nx) or iy in (0,ny)
                    if 0<ix<nx:xx+=rng.uniform(-.075,.075)*(xc-xa)
                    if 0<iy<ny:yy+=rng.uniform(-.09,.09)*(yc-ya)
                    off=min(.070,max(.004,depth+rng.uniform(-.005,.009) if boundary else depth+rng.uniform(-.015,.025)))
                    grid[ix,iy]=(xx,yy,off)
            for ix in range(nx):
                for iy in range(ny):
                    cell=[grid[ix,iy],grid[ix+1,iy],grid[ix+1,iy+1],grid[ix,iy+1]]
                    surface(cell)
            # Chipped/chamfered perimeter pieces, deliberately irregular along
            # their run while leaving narrow, consistent mortar at the joint.
            ring=[grid[ix,0] for ix in range(nx+1)]+[grid[nx,iy] for iy in range(1,ny+1)]+[grid[ix,ny] for ix in range(nx-1,-1,-1)]+[grid[0,iy] for iy in range(ny-1,0,-1)]
            for qa,qc in zip(ring,ring[1:]+ring[:1]):
                def edge(q):
                    ex=x0 if abs(q[0]-xa)<1e-7 else (x1 if abs(q[0]-xc)<1e-7 else q[0])
                    ey=y0 if abs(q[1]-ya)<1e-7 else (y1 if abs(q[1]-yc)<1e-7 else q[1])
                    return (ex,ey,-.009)
                surface([edge(qa),edge(qc),qc,qa],None)
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

    def tiles(self, pts, confidence):
        normal=norm(legacy._normal(pts))
        uphill=norm((-normal[0]*normal[2],-normal[1]*normal[2],1-normal[2]*normal[2]))
        if abs(uphill[2])<1e-5:
            return self.raw(pts,confidence,ROOF)
        u=norm(cross(uphill,normal))
        d=dot(pts[0],normal)
        poly=[(dot(p,u),dot(p,uphill)) for p in pts]
        if area(poly)<0:
            poly.reverse()
        a,b,c,e=bounds(poly)
        if abs(area(poly))<.08:
            return self.raw(pts,confidence,ROOF)
        self.raw(pts,confidence,ROOF)
        def point(q,off):
            return tuple(u[k]*q[0]+uphill[k]*q[1]+normal[k]*(d+off) for k in range(3))
        w,h=.2032,.12192
        for row in range(math.floor(b/h),math.ceil(e/h)):
            y0,y1=row*h,(row+1)*h
            shift=.5*w if row%2 else 0
            for col in range(math.floor((a-shift)/w),math.ceil((c-shift)/w)):
                x0=col*w+shift
                tile=rect_clip(poly,x0+.002,y0+.002,x0+w-.002,y1+.005)
                if not tile:
                    continue
                rng=random.Random(row*10007+col*813+31)
                mat=19+rng.randrange(3)
                # Raised lower edge and slight lap cast an honest narrow shadow.
                def raised(q):
                    return .006+.006*(1-(q[1]-y0)/h)
                front=[point(q,raised(q)) for q in tile]
                self.raw(front,confidence,mat,normal)
                self.roof_tiles+=1

            lip=rect_clip(poly,a,y0+.002,c,y0+.012)
            if lip:
                self.raw([point(q,.013 if q[1]<y0+.007 else .001) for q in lip],confidence,19+row%3,normal)


def solid_polygon(b, pl, poly, depth0, depth1, confidence, mat):
    n=legacy._plane_dir(pl)
    front=[legacy._plane_point(pl,u,z,depth1) for u,z in poly]
    back=[legacy._plane_point(pl,u,z,depth0) for u,z in poly]
    b.raw(front,confidence,mat,n)
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        b.raw([back[i],back[j],front[j],front[i]],confidence,mat)


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
    if kind=='band':
        if o.get('face')=='east' and c-a>3 and z0>5:
            ornament.sill(b,o)
        else:
            slab(b,o,a,c,z0,z1,0,.095,conf,TRIM)
        return
    if kind=='fan':
        ornament.fan(b,o)
        return
    if kind=='dark' and o.get('face')=='west' and o.get('at',0)>30 and z0<.1 and c-a>2:
        # The porte-cochere is a through passage, not a panel of black glazing.
        return
    poly=aperture(o)
    front=[legacy._plane_point(o,u,z,.016) for u,z in poly]
    back=[legacy._plane_point(o,u,z,-.29) for u,z in poly]
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        b.raw([front[i],back[i],back[j],front[j]],conf,ROUGH_TRIM if courtyard else GRANITE)
    if kind=='arch':
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
    # Small basement grid apertures have stone mullions and only recessed glass.
    small=min(c-a,z1-z0)<.45
    frame=.025 if small else .062
    glazing_mat=DARK_GLASS if small or kind=='dark' else GLASS
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


def detailed_door(b,o,style):
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];conf=o['conf']
    if style!='porte_cochere':
        slab(b,o,a+.025,c-.025,z0+.02,z1-.02,-.305,-.28,conf,WOOD)
    if style=='porte_cochere':
        original=b
        angle=math.radians(b.params.detail.get('porte_cochere_open_deg',82))
        for leaf in range(2):
            la=a+(c-a)*leaf/2;lc=a+(c-a)*(leaf+1)/2
            hinge=legacy._plane_point(o,la if leaf==0 else lc,0,-.23)
            theta=angle if leaf==0 else -angle
            class Leaf:
                def raw(self,pts,confidence,mat,want=None):
                    co,si=math.cos(theta),math.sin(theta)
                    def rotate(p):
                        x,y=p[0]-hinge[0],p[1]-hinge[1]
                        return (hinge[0]+co*x-si*y,hinge[1]+si*x+co*y,p[2])
                    if want:want=(co*want[0]-si*want[1],si*want[0]+co*want[1],want[2])
                    return original.raw([rotate(p) for p in pts],confidence,mat,want)
            b=Leaf()
            slab(b,o,la+.025,lc-.025,z0+.02,z1-.02,-.305,-.28,conf,WOOD)
            slab(b,o,la+.01,la+.06,z0,z1,-.28,-.18,conf,WOOD)
            slab(b,o,lc-.06,lc-.01,z0,z1,-.28,-.18,conf,WOOD)
            for row in range(6):
                lo=z0+.10+(z1-z0-.2)*row/6;hi=z0+.10+(z1-z0-.2)*(row+1)/6
                for col in range(3):
                    left=la+.09+(lc-la-.18)*col/3;right=la+.09+(lc-la-.18)*(col+1)/3
                    slab(b,o,left+.025,right-.025,lo+.025,hi-.025,-.28,-.245,conf,WOOD)
                    for x0,x1,y0,y1 in [(left,left+.027,lo,hi),(right-.027,right,lo,hi),
                                       (left,right,lo,lo+.027),(left,right,hi-.027,hi)]:
                        slab(b,o,x0,x1,y0,y1,-.28,-.19,conf,WOOD)
            slab(b,o,lc-.12,lc-.08,z0+.8,z0+1.03,-.18,-.15,conf,IRON)
    else:
        height=z1-z0
        for left,right,lo,hi in [(a,a+.11,z0,z1),(c-.11,c,z0,z1),(a,c,z0,z0+.12),
                                  (a,c,z1-.12,z1),(a,c,z0+height*.42,z0+height*.49)]:
            slab(b,o,left,right,lo,hi,-.28,-.16,conf,WOOD)
        slab(b,o,a+.19,c-.19,z0+.20,z0+height*.39,-.28,-.225,conf,WOOD)
        lo=z0+height*.51;hi=z1-.16
        slab(b,o,a+.18,c-.18,lo,hi,-.279,-.273,conf,GLASS)
        for i in range(1,5):
            u=a+.18+(c-a-.36)*i/5
            slab(b,o,u-.012,u+.012,lo,hi,-.265,-.24,conf,IRON)
        for j in range(1,4):
            z=lo+(hi-lo)*j/4
            slab(b,o,a+.18,c-.18,z-.012,z+.012,-.265,-.24,conf,IRON)
        slab(b,o,c-.145,c-.105,z0+height*.43,z0+height*.58,-.15,-.10,conf,IRON)


def ring(b,pl,uc,zs,rin,rout,count,conf):
    if rout<=rin:
        return
    for i in range(count):
        a=math.pi*i/count+.005;c=math.pi*(i+1)/count-.005
        poly=[(uc+rin*math.cos(a),zs+rin*math.sin(a)),(uc+rout*math.cos(a),zs+rout*math.sin(a)),
              (uc+rout*math.cos(c),zs+rout*math.sin(c)),(uc+rin*math.cos(c),zs+rin*math.sin(c))]
        solid_polygon(b,pl,poly,-.02,.065,conf,12+i%4)


def roof_ridges(b,params):
    for r in params.ranges:
        a0,a1=(r['y0'],r['y1']) if r['axis']=='y' else (r['x0'],r['x1'])
        for side,v in r['roof_extend'].items():
            if side in ('south','west'):a0=min(a0,v)
            else:a1=max(a1,v)
        step=.36
        for i in range(math.ceil((a1-a0)/step)):
            lo=a0+i*step+.006;hi=min(a1,lo+step-.012)
            for j in range(8):
                p,q=math.pi*j/8,math.pi*(j+1)/8
                def P(a,l):
                    across=r['ridge_at']+.14*math.cos(a);z=r['ridge_z']+.055+.14*math.sin(a)
                    return (across,l,z) if r['axis']=='y' else (l,across,z)
                b.raw([P(p,lo),P(q,lo),P(q,hi),P(p,hi)],r['conf_roof'],19+i%3,(0,0,1))


def chimney(b,c):
    conf=c['conf'];z=c['z1'];x0,x1,y0,y1=c['x0'],c['x1'],c['y0'],c['y1']
    detail=b.params.detail.get('chimney_details',{}).get(c['name'],{})
    slope=float(detail.get('cap_slope_ft',.3))*.3048
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
    old=b.decorate;b.decorate=False
    legacy._box(b,x0-.06,y0-.06,c['z0'],x1+.06,y1+.06,c['z0']+.13,conf,COPPER)
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
    window_angles=[]
    for i in range(n):
        a=a0+(a1-a0)*(i+.5)/n;half=(a1-a0)/n*.28
        window_angles.append((a-half,a+half))
    windows=[]
    for wi,(a,c) in enumerate(window_angles):
        for ri,(lo,hi) in enumerate(w['light_rows']):
            isdoor=ri==0 and wi==n//2 and b.params.detail.get('bow_first_floor_central_door')
            if isdoor and b.params.detail.get('bow_terrace'):
                lo=b.params.detail['bow_terrace']['z1']-.18
            windows.append({'a0':a,'a1':c,'z0':lo,'z1':hi,'door':isdoor})
    curved_masonry(b,cx,cy,r,0,w['wall_top_z'],conf,BRICK,windows,a0,a1)
    for op in windows:
        a,c=op['a0'],op['a1'];mid=(a+c)/2
        p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
        facet_window(b,p,q,op['z0'],op['z1'],(math.cos(mid),math.sin(mid),0),conf,stone_jambs=False,door=op['door'])
    z=w['wall_top_z'];zr=z+w['roof_rise_m'];ro=r+.20
    for i in range(48):
        a=a0+(a1-a0)*i/48;c=a0+(a1-a0)*(i+1)/48
        pts=[(cx+ro*math.cos(a),cy+ro*math.sin(a),z),(cx+ro*math.cos(c),cy+ro*math.sin(c),z),(cx,cy,zr)]
        b.raw(pts,w['conf_roof'],COPPER,(0,0,1))
        if i%3==0:
            a2=a+.007
            b.raw([(cx+ro*math.cos(a),cy+ro*math.sin(a),z+.022),(cx+ro*math.cos(a2),cy+ro*math.sin(a2),z+.022),(cx,cy,zr+.022)],w['conf_roof'],COPPER,(0,0,1))



def facet_window(b,p,q,z0,z1,normal,conf,small=False,stone_jambs=True,door=False,panes=None,surrounds=True):
    """Recessed sash on an arbitrarily oriented planar bay facet."""
    tangent=norm(sub((*q,0),(*p,0)));width=math.dist(p,q)
    def P(u,z,off):
        return (p[0]+tangent[0]*u+normal[0]*off,p[1]+tangent[1]*u+normal[1]*off,z)
    outline=[(0,z0),(width,z0),(width,z1),(0,z1)]
    for i in range(4):
        a,c=outline[i],outline[(i+1)%4]
        b.raw([P(*a,.02),P(*a,-.29),P(*c,-.29),P(*c,.02)],conf,TRIM if stone_jambs else BRICK)
    b.raw([P(u,z,-.60) for u,z in outline],conf,DARK_GLASS,normal)
    if not door:
        b.raw([P(u,z,-.285) for u,z in outline],conf,DARK_GLASS if small else GLASS,normal)
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
        b.raw([P(ga,gz0,-.248),P(gb,gz0,-.248),
               P(gb,gz1,-.248),P(ga,gz1,-.248)],conf,GLASS,normal)
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
    if not small and not door:
        frames=[(0,.06,z0,z1),(width-.06,width,z0,z1),(0,width,z0,z0+.06),(0,width,z1-.06,z1)]
        cols,rows=panes or [1,2]
        for col in range(1,cols):
            u=width*col/cols;frames.append((u-.019,u+.019,z0,z1))
        for row in range(1,rows):
            z=z0+(z1-z0)*row/rows;frames.append((0,width,z-.022,z+.022))
        for ua,ub,za,zb in frames:
            box(ua,ub,za,zb,-.285,-.18,PAINTED_WOOD)
    stones=[(-.20,width+.20,z0-.1,z0),(-.20,width+.20,z1,z1+.18)] if surrounds else []
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
            facet_window(b,a,c,lo,hi,want,conf,small=basal,stone_jambs=not basal)
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
            b.raw([(*p,zt),(*q,zt),(*q,zb),(*p,zb)],conf,GLASS,want)
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
        ap=y['apex'];roof=[(*p,zb),(*q,zb),tuple(ap)]
        b.raw(roof,y['conf_roof'],COPPER,(0,0,1))
        # Standing seams subdivide the hipped cap while its top runs into the main roof.
        count=max(1,round(length/.48))
        for j in range(1,count):
            f=j/count;x=p[0]+(q[0]-p[0])*f;yy=p[1]+(q[1]-p[1])*f
            aa=(x-.01,yy,zb+.016);cc=(x+.01,yy,zb+.016)
            b.raw([aa,cc,(ap[0],ap[1],ap[2]+.016)],y['conf_roof'],COPPER,(0,0,1))



def dormer(b,d):
    f,bk=d['front'],d['back'];a,c=sorted((d['u0'],d['u1']));z0,ze,za=d['z0'],d['eave_z'],d['apex_z']
    sign=-1 if bk>f else 1;pl={'axis':'x','sign':sign,'at':f}
    margin=(c-a)*.22;lo,hi=d['light'];conf=d['conf']
    op={**pl,'face':'west' if sign<0 else 'east','kind':'window','u0':a+margin,'u1':c-margin,'z0':lo,'z1':hi,'conf':conf}
    poly=[(a,z0),(c,z0),(c,ze),(a,ze)]
    for frag in subtract(poly,[aperture(op)]):
        b.raw([legacy._plane_point(pl,u,z) for u,z in frag],conf,PAINTED_WOOD,legacy._plane_dir(pl))
    for u in (a,c):
        pts=[(f,u,z0),(bk,u,z0),(bk,u,ze),(f,u,ze)]
        legacy._poly_facing(b,pts,conf,ROOF,(0,-1 if u==a else 1,0))
    opening(b,op)
    xa,xb=sorted((f,bk));xa,xb=(xa-.12,xb) if sign<0 else (xa,xb+.12)
    ring=[(xa,a-.12,ze),(xb,a-.12,ze),(xb,c+.12,ze),(xa,c+.12,ze)]
    for p,q in zip(ring,ring[1:]+ring[:1]):legacy._up(b,[p,q,((f+bk)/2,(a+c)/2,za)],conf,ROOF)
    legacy._finial(b,(f+bk)/2,(a+c)/2,za,.35,conf,COPPER)

def curved_masonry(b,cx,cy,r,z0,z1,conf,mat,windows,a0=0,a1=2*math.pi):
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
            b.wall(pts,conf,mat)


def tower(b,t,params):
    data=params.detail.get('tower_stair_windows') if t['name']=='stair' else None
    if not data:
        legacy._tower(b,{**t,'segments':48})
        return
    r,cx,cy,conf=t['r'],t['cx'],t['cy'],t['conf_wall'];windows=[]
    for w in data['openings']:
        half=w['width_m']/(2*r)
        windows.append({**w,'a0':w['angle']-half,'a1':w['angle']+half})
    curved_masonry(b,cx,cy,r,t['z0'],t['wall_top_z'],conf,BRICK,windows)
    for w in windows:
        a,c=w['a0'],w['a1'];p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
        lantern=w['z0']>=data['bands'][0][0]
        facet_window(b,p,q,w['z0'],w['z1'],(math.cos(w['angle']),math.sin(w['angle']),0),conf,stone_jambs=False,
                     panes=data['lantern_panes'] if lantern else None,surrounds=not lantern)
    from archetypes.masonry_house_v4_rough_bands import add_rough_band
    for z0,z1 in data['bands']:
        add_rough_band(b,cx,cy,r+.06,z0,z1,conf)
    legacy._cone(b,cx,cy,t['eave_r'],t['wall_top_z'],t['apex_z'],t['conf_roof'],ROOF,72,soffit=r)
    legacy._finial(b,cx,cy,t['apex_z'],t['finial_m'],t['conf_roof'],COPPER)


def terrace(b,params):
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
    s=params.detail.get('north_court_service_stair')
    if not s:return
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
    b.raw([(*p,z0+.006),(*q,z0+.006),(*r,z0+.006),(*s,z0+.006)],params.detail['conf'],DRIVE,(0,0,1))
    for i in range(1,19):
        t=i/19;a=(p[0]+(s[0]-p[0])*t,p[1]+(s[1]-p[1])*t);c=(q[0]+(r[0]-q[0])*t,q[1]+(r[1]-q[1])*t)
        b.raw([(*a,z0+.007),(*c,z0+.007),(c[0]-.012,c[1],z0+.007),(a[0]-.012,a[1],z0+.007)],params.detail['conf'],MORTAR,(0,0,1))



def date_stones(b,params):
    """Evidence-backed north-gable datestones; original generic letter outlines."""
    import bpy
    for stone in params.detail.get('date_stones',[]):
        a,c,z0,z1=stone['u0'],stone['u1'],stone['z0'],stone['z1'];conf=params.detail['conf']
        slab(b,stone,a,c,z0,z1,0,.06,conf,GRANITE)
        curve=bpy.data.curves.new('glessner_datestone_lettering','FONT')
        curve.body=stone['text'];curve.align_x='CENTER';curve.align_y='CENTER'
        curve.size=(z1-z0)*.82;curve.extrude=.0015;curve.bevel_depth=.001
        ob=bpy.data.objects.new('temporary_datestone_letters',curve)
        bpy.context.scene.collection.objects.link(ob)
        mesh=ob.to_mesh()
        for poly in mesh.polygons:
            pts=[]
            for i in poly.vertices:
                v=mesh.vertices[i].co
                pts.append(legacy._plane_point(stone,(a+c)/2+v.x,(z0+z1)/2+v.y,.064+v.z))
            b.raw(pts,conf,TRIM,legacy._plane_dir(stone))
        ob.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True);bpy.data.curves.remove(curve)
    ledge=params.detail.get('pigeon_ledge')
    if ledge:
        slab(b,ledge,ledge['u0'],ledge['u1'],ledge['z0'],ledge['z1'],0,ledge['projection_m'],params.detail['conf'],GRANITE)

def supplemental(b,p):
    g=p.detail.get('west_cross_gable')
    if g:
        lo,hi=g['u0'],g['u1'];base=min(g['eave_lo_z'],g['eave_hi_z'])
        # Existing west wall owns the wall below the crossed roof's eaves.
        poly=[(lo,base),(hi,base),(hi,g['eave_hi_z']),(g['ridge_at'],g['ridge_z']),(lo,g['eave_lo_z'])]
        pts=[legacy._plane_point(g,u,z,.012) for u,z in poly]
        legacy._poly_facing(b,pts,g['conf'],GRANITE,legacy._plane_dir(g))
    d=p.detail.get('west_dormer')
    if d:
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
    if r:
        z=r['wall_top_z'];zt=z+r['rise_m']
        copper_seams(b,[(r['x0'],r['y0'],z),(r['x1'],r['y0'],z),(r['x1'],r['y1'],zt),(r['x0'],r['y1'],zt)],r['conf'])
        # Folded front fascia gives the metal roof its thickness in silhouette.
        b.raw([(r['x0'],r['y0'],z-.055),(r['x1'],r['y0'],z-.055),(r['x1'],r['y0'],z),(r['x0'],r['y0'],z)],r['conf'],COPPER,(0,-1,0))



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


def build(params,name):
    from archetypes.masonry_house_v4_materials import build_materials, assign_metric_uvs
    from archetypes.masonry_house_v4_landscape import add_lawn_blades
    from archetypes.masonry_house_v4_foundation import stair_tower_plinth
    b=DetailBuilder(name,params)
    for r in params.ranges:legacy._range(b,r)
    for t in params.towers:tower(b,t,params)
    for w in params.bows:bow(b,w)
    for y in params.bays:bay(b,y,params)
    for d in params.dormers:dormer(b,d)
    for t in params.turrets:legacy._turret(b,t)
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
    for w in params.walls:legacy._gate_piece(b,w)
    b.decorate=False
    for g in params.ground:legacy._ground(b,g)
    grass_blades=add_lawn_blades(b,params)
    ornament.columns(b,params)
    roof_ridges(b,params)
    b.decorate=True
    supplemental(b,params)
    terrace(b,params)
    service_stair(b,params)
    underpass(b,params)
    date_stones(b,params)
    stair_tower_plinth(b,params)
    obj=b.to_object(build_materials(params.colours))
    assign_metric_uvs(obj)
    _discard_export_scratch_uv(obj)
    obj['detail_profile']='glessner_v4'
    obj['masonry_blocks']=b.masonry_blocks
    obj['roof_tiles']=b.roof_tiles
    obj['grass_blades']=grass_blades
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
