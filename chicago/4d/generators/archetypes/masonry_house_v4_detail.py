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

GRANITE, BRICK, TRIM, ROOF, COPPER, GLASS, WOOD, LAWN, DRIVE = range(9)
MORTAR, IRON, DARK_GLASS = 9, 10, 11
PAINTED_WOOD = 23


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
    """Clip a polygon to the left of an oriented line, or its right half-plane."""
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
            out.append((p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])))
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
                        o['face']=='east' and o['z0']>5], key=lambda o:o['u0'])
        for a,c in zip(upper,upper[1:]):
            if .12<c['u0']-a['u1']<.3 and abs(a['z0']-c['z0'])<.05 and abs(a['at']-c['at'])<.05:
                self.openings.append({**a,'u0':a['u1']-.001,'u1':c['u0']+.001,
                                      'z0':a['z0']+.05,'z1':a['z1']-.035})
        self.course_schedule = params.detail.get('ashlar_courses_m') or [0.4572,0.4572,0.3937,0.2413,0.3429,0.3683,0.1905,0.3683,0.1905,0.2921]
        self.masonry_blocks = self.roof_tiles = 0

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
            if o['kind'] in ('fan','band'):
                continue
            on = legacy._plane_dir(o)
            if dot(n,on)<.999 or abs(dot(legacy._plane_point(o,0,0),n)-d)>.055:
                continue
            holes.append([(dot(legacy._plane_point(o,s,z),u),z) for s,z in aperture(o)])
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
                    for fragment in subtract(tile,holes):
                        self.block(fragment,point,n,confidence,mat,rng)
                a = c

    def block(self, polygon, point, normal, confidence, mat, rng):
        if len(polygon)<3:
            return
        x0,y0,x1,y1 = bounds(polygon)
        if min(x1-x0,y1-y0)<.002:
            return
        self.masonry_blocks += 1
        cx,cy = sum(p[0] for p in polygon)/len(polygon),sum(p[1] for p in polygon)/len(polygon)
        bevel = .005 if mat==BRICK else .012
        depth = rng.uniform(.001,.006) if mat==BRICK else rng.uniform(.018,.035)
        variant = (16+rng.randrange(3)) if mat==BRICK else (12+rng.randrange(4))
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
            self.raw([point(q,depth) for q in polygon],confidence,variant,normal)
            return
        back=[point(q,-.009) for q in polygon]
        front=[point(q,depth+rng.uniform(-.001,.001)) for q in inner]
        for i in range(len(polygon)):
            j=(i+1)%len(polygon)
            self.raw([back[i],back[j],front[j],front[i]],confidence,variant)
        if mat==BRICK or len(polygon)>6:
            self.raw(front,confidence,variant,normal)
        else:
            # Broken stone has an uneven face without rounded cobblestone silhouettes.
            center=point((cx,cy),depth+rng.uniform(.001,.009))
            for i in range(len(front)):
                self.raw([front[i],front[(i+1)%len(front)],center],confidence,variant,normal)

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


def cylinder(b,cx,cy,z0,z1,r,conf,mat,segments=16):
    for i in range(segments):
        a,c=2*math.pi*i/segments,2*math.pi*(i+1)/segments
        p,q=(cx+r*math.cos(a),cy+r*math.sin(a)),(cx+r*math.cos(c),cy+r*math.sin(c))
        b.raw([(p[0],p[1],z0),(q[0],q[1],z0),(q[0],q[1],z1),(p[0],p[1],z1)],conf,mat,(math.cos((a+c)/2),math.sin((a+c)/2),0))


def opening(b,o,courtyard=False):
    """An opening with 280 mm deep jambs, inset glazing, sash and separate sill."""
    kind=o['kind']; a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1']; conf=o['conf']
    if kind=='band':
        slab(b,o,a,c,z0,z1,0,.095,conf,TRIM)
        return
    if kind=='fan':
        fan(b,o)
        return
    poly=aperture(o)
    front=[legacy._plane_point(o,u,z,.016) for u,z in poly]
    back=[legacy._plane_point(o,u,z,-.29) for u,z in poly]
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        b.raw([front[i],back[i],back[j],front[j]],conf,TRIM if courtyard else GRANITE)
    if kind=='arch':
        b.raw(back,conf,DARK_GLASS,legacy._plane_dir(o))
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
        # Restrained off-white blinds on a deterministic minority of upper lights.
        if int((a+c)*100)%5==0 and z0>2:
            slab(b,o,a+.10,c-.10,z1-(z1-z0)*.30,z1-.08,-.315,-.312,conf,22)
        slab(b,o,a-.09,c+.09,z0-.085,z0+.025,-.055,.11,conf,TRIM if courtyard else GRANITE)
    if courtyard and not small:
        # Courtyard photographs show brick jambs with rock-faced limestone
        # heads and sills. Full stone jambs belong to the dining bay only.
        slab(b,o,a-.24,c+.24,z1+.006,z1+.21,-.01,.09,conf,TRIM)


def detailed_door(b,o,style):
    a,c,z0,z1=o['u0'],o['u1'],o['z0'],o['z1'];conf=o['conf']
    slab(b,o,a+.025,c-.025,z0+.02,z1-.02,-.305,-.28,conf,WOOD)
    if style=='porte_cochere':
        for leaf in range(2):
            la=a+(c-a)*leaf/2;lc=a+(c-a)*(leaf+1)/2
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


def fan(b,o):
    uc=(o['u0']+o['u1'])/2;zs=o['spring_z'];r=o['r_in'];conf=o['conf']
    poly=[(uc+r*math.cos(math.pi*i/32),zs+r*math.sin(math.pi*i/32)) for i in range(33)]
    solid_polygon(b,o,poly,.022,.050,conf,TRIM)
    ring(b,o,uc,zs,r+.04,o['r_out'],o.get('voussoirs') or 11,conf)
    # Low, repeating radial carving: declared reconstruction of the photographed
    # foliate tympanum, not a fictitious inscription or copied relief image.
    for rad,petals in [(r*.35,8),(r*.65,14),(r*.9,20)]:
        for i in range(petals):
            theta=math.pi*(i+.5)/petals
            cu,cz=uc+rad*math.cos(theta),zs+rad*math.sin(theta)
            rr=min(.052,r*.09)
            leaf=[(cu+rr*math.cos(t),cz+rr*.72*math.sin(t)) for t in [0,math.pi/2,math.pi,math.pi*1.5]]
            solid_polygon(b,o,leaf,.05,.064,conf,TRIM)


def columns(b,params):
    ops=sorted([o for o in params.openings if o['kind']=='window' and o['face']=='east' and o['z0']>5],key=lambda o:o['u0'])
    for a,c in zip(ops,ops[1:]):
        gap=c['u0']-a['u1']
        if not .12<gap<.3 or abs(a['z0']-c['z0'])>.05 or abs(a['at']-c['at'])>.05:
            continue
        u=(c['u0']+a['u1'])/2;z0,z1=a['z0'],a['z1'];conf=max(a['conf'],c['conf'])
        pt=legacy._plane_point(a,u,0,.07)
        cylinder(b,pt[0],pt[1],z0+.05,z1-.24,gap*.62,conf,TRIM,20)
        slab(b,a,u-gap*.78,u+gap*.78,z0,z0+.09,-.08,.16,conf,TRIM)
        slab(b,a,u-gap*.88,u+gap*.88,z1-.19,z1-.035,-.07,.18,conf,TRIM)
        for j in range(5):
            dx=(j-2)*gap*.29
            # Small carved facets cast shadows on the capital, not a smooth cube.
            poly=[(u+dx-.022,z1-.13),(u+dx,z1-.195),(u+dx+.022,z1-.13),(u+dx,z1-.055)]
            solid_polygon(b,a,poly,.17,.185,conf,TRIM)


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
    legacy._chimney(b,c)
    conf=c['conf'];z=c['z1'];x0,x1,y0,y1=c['x0'],c['x1'],c['y0'],c['y1']
    # A coping joint and dark recessed flues are visible from the inspection camera.
    old=b.decorate;b.decorate=False
    inset=.17
    for i in range(max(1,round((x1-x0)/.55))):
        n=max(1,round((x1-x0)/.55));a=x0+(x1-x0)*i/n+inset;c1=x0+(x1-x0)*(i+1)/n-inset
        if c1>a:
            legacy._box(b,a,y0+inset,z+.003,c1,y1-inset,z+.006,conf,IRON)
    # Narrow copper flashing returns at the roof penetration.
    legacy._box(b,x0-.075,y0-.075,c['z0'],x1+.075,y1+.075,c['z0']+.13,conf,COPPER)
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
    # Split curved wall at opening boundaries; all glass is behind its masonry.
    breaks=sorted({a0,a1,*[a0+(a1-a0)*i/72 for i in range(73)],*[a for pair in window_angles for a in pair]})
    for a,c in zip(breaks,breaks[1:]):
        mid=(a+c)/2
        openings=[(z0,z1) for wa,wb in window_angles if wa-1e-8<=mid<=wb+1e-8 for z0,z1 in w['light_rows']]
        zs=sorted({0,w['wall_top_z'],*[z for pair in openings for z in pair]})
        for lo,hi in zip(zs,zs[1:]):
            if any(z0-1e-8<=(lo+hi)/2<=z1+1e-8 for z0,z1 in openings):continue
            p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
            pts=[(*p,lo),(*q,lo),(*q,hi),(*p,hi)]
            if dot(legacy._normal(pts),(math.cos(mid),math.sin(mid),0))<0:pts.reverse()
            b.wall(pts,conf,BRICK)
    for a,c in window_angles:
        mid=(a+c)/2
        # Tangent sash gives each curved bow opening a buildable planar frame.
        p=(cx+r*math.cos(a),cy+r*math.sin(a));q=(cx+r*math.cos(c),cy+r*math.sin(c))
        tangent=norm(sub((*q,0),(*p,0)));normal=(math.cos(mid),math.sin(mid),0)
        width=math.dist(p,q)
        def P(u,z,off):return (p[0]+tangent[0]*u+normal[0]*off,p[1]+tangent[1]*u+normal[1]*off,z)
        for lo,hi in w['light_rows']:
            b.raw([P(0,lo,-.18),P(width,lo,-.18),P(width,hi,-.18),P(0,hi,-.18)],conf,GLASS,normal)
            for ua,ub,za,zb,mat,off in [(0,.065,lo,hi,PAINTED_WOOD,-.08),(width-.065,width,lo,hi,PAINTED_WOOD,-.08),
                  (0,width,lo,lo+.07,PAINTED_WOOD,-.08),(0,width,hi-.07,hi,PAINTED_WOOD,-.08),
                  (0,width,(lo+hi)/2-.028,(lo+hi)/2+.028,PAINTED_WOOD,-.07),
                  (-.15,width+.15,lo-.12,lo,TRIM,.06),(-.15,width+.15,hi,hi+.19,TRIM,.06),
                  (-.15,0,lo,hi,TRIM,.06),(width,width+.15,lo,hi,TRIM,.06)]:
                b.raw([P(ua,za,off),P(ub,za,off),P(ub,zb,off),P(ua,zb,off)],conf,mat,normal)
    z=w['wall_top_z'];zr=z+w['roof_rise_m'];ro=r+.20
    for i in range(48):
        a=a0+(a1-a0)*i/48;c=a0+(a1-a0)*(i+1)/48
        pts=[(cx+ro*math.cos(a),cy+ro*math.sin(a),z),(cx+ro*math.cos(c),cy+ro*math.sin(c),z),(cx,cy,zr)]
        b.raw(pts,w['conf_roof'],COPPER,(0,0,1))
        if i%3==0:
            a2=a+.007
            b.raw([(cx+ro*math.cos(a),cy+ro*math.sin(a),z+.022),(cx+ro*math.cos(a2),cy+ro*math.sin(a2),z+.022),(cx,cy,zr+.022)],w['conf_roof'],COPPER,(0,0,1))



def facet_window(b,p,q,z0,z1,normal,conf,small=False):
    """Recessed sash on an arbitrarily oriented planar bay facet."""
    tangent=norm(sub((*q,0),(*p,0)));width=math.dist(p,q)
    def P(u,z,off):
        return (p[0]+tangent[0]*u+normal[0]*off,p[1]+tangent[1]*u+normal[1]*off,z)
    outline=[(0,z0),(width,z0),(width,z1),(0,z1)]
    for i in range(4):
        a,c=outline[i],outline[(i+1)%4]
        b.raw([P(*a,.02),P(*a,-.29),P(*c,-.29),P(*c,.02)],conf,TRIM)
    b.raw([P(u,z,-.285) for u,z in outline],conf,DARK_GLASS if small else GLASS,normal)
    def box(ua,ub,za,zb,off0,off1,mat):
        front=[P(ua,za,off1),P(ub,za,off1),P(ub,zb,off1),P(ua,zb,off1)]
        back=[P(ua,za,off0),P(ub,za,off0),P(ub,zb,off0),P(ua,zb,off0)]
        b.raw(front,conf,mat,normal)
        for i in range(4):
            j=(i+1)%4;b.raw([front[i],back[i],back[j],front[j]],conf,mat)
    if not small:
        for ua,ub,za,zb in [(0,.06,z0,z1),(width-.06,width,z0,z1),
                    (0,width,z0,z0+.06),(0,width,z1-.06,z1),(0,width,(z0+z1)/2-.028,(z0+z1)/2+.028)]:
            box(ua,ub,za,zb,-.285,-.18,PAINTED_WOOD)
    for ua,ub,za,zb in [(-.17,0,z0,z1),(width,width+.17,z0,z1),
                (-.20,width+.20,z0-.1,z0),(-.20,width+.20,z1,z1+.18)]:
        box(ua,ub,za,zb,-.03,.05,TRIM)


def bay(b,y,params):
    pts=y['pts'];mx=(pts[0][0]+pts[-1][0])/2;my=(pts[0][1]+pts[-1][1])/2
    cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts)
    ix,iy=2*mx-cx,2*my-cy;zt,zb=y['wall_top_z'],y['band_top_z'];conf=y['conf_wall']
    for p,q in zip(pts,pts[1:]):
        want=norm(((p[0]+q[0])/2-ix,(p[1]+q[1])/2-iy,0))
        length=math.dist(p,q);holes=[];windows=[]
        if length>1.2:
            a=(p[0]+(q[0]-p[0])*.2,p[1]+(q[1]-p[1])*.2)
            c=(p[0]+(q[0]-p[0])*.8,p[1]+(q[1]-p[1])*.8)
            rows=([y['light_row']] if y['light_row'] else [])
            if params.detail.get('dining_garden_window_z'):rows+=[params.detail['dining_garden_window_z']]
            for lo,hi in rows:
                holes.append([(*a,lo),(*c,lo),(*c,hi),(*a,hi)]);windows.append((a,c,lo,hi))
        wall=[(*p,0),(*q,0),(*q,zt),(*p,zt)]
        if dot(legacy._normal(wall),want)<0:wall.reverse()
        b.wall(wall,conf,BRICK,holes)
        for a,c,lo,hi in windows:facet_window(b,a,c,lo,hi,want,conf)
        if zb>zt:
            b.raw([(*p,zt),(*q,zt),(*q,zb),(*p,zb)],conf,GLASS,want)
            tangent=norm(sub((*q,0),(*p,0)))
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


def build(params,name):
    from archetypes.masonry_house_v4_materials import build_materials, assign_metric_uvs
    b=DetailBuilder(name,params)
    for r in params.ranges:legacy._range(b,r)
    for t in params.towers:
        legacy._tower(b,{**t,'segments':72})
    for w in params.bows:bow(b,w)
    for y in params.bays:bay(b,y,params)
    for d in params.dormers:legacy._dormer(b,d)
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
    columns(b,params)
    roof_ridges(b,params)
    b.decorate=True
    supplemental(b,params)
    obj=b.to_object(build_materials(params.colours))
    assign_metric_uvs(obj)
    obj['detail_profile']='glessner_v4'
    obj['masonry_blocks']=b.masonry_blocks
    obj['roof_tiles']=b.roof_tiles
    obj['openings_recessed']=len([o for o in params.openings if o['kind'] not in ('fan','band')])
    obj['opening_recess_depth_m']=.29
    return obj
