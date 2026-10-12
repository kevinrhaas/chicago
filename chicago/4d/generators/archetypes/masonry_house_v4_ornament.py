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


class Relief:
    """A sculptor's (horizontal, vertical, outward-depth) work plane."""

    def __init__(self, builder, plane, confidence):
        self.b = builder
        self.p = plane
        self.conf = confidence

    def point(self, u, z, d):
        at = self.p['at'] + self.p['sign'] * d
        return (at, u, z) if self.p['axis'] == 'x' else (u, at, z)

    def vector(self, u, z, d):
        return (self.p['sign'] * d, u, z) if self.p['axis'] == 'x' else (u, self.p['sign'] * d, z)

    def face(self, pts, mat=TRIM, normal=(0, 0, 1)):
        self.b.raw([self.point(*p) for p in pts], self.conf, mat,
                   self.vector(*normal) if normal else None)

    def solid(self, poly, back, front, mat=TRIM):
        self.face([(*p, front) for p in poly], mat)
        for p, q in zip(poly, poly[1:] + poly[:1]):
            self.face([(*p, back), (*q, back), (*q, front), (*p, front)], mat, None)

    def box(self, x0, x1, z0, z1, back, front, mat=TRIM):
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


def _scroll(r, x, z, radius, depth, mirror=1, turn=0):
    """Open curling stem with unequal leaves, rather than a regular rosette."""
    path=[]
    for i in range(53):
        t=i/52;th=turn+mirror*(.12+1.72*math.pi*t)
        rr=radius*(1-.76*t)
        path.append((x+rr*math.cos(th),z+rr*math.sin(th),depth+.006*math.sin(math.pi*t)))
    r.tube(path,lambda t:radius*(.058-.026*t),10)
    for j, (t, size) in enumerate(((.13,1),(.31,.90),(.50,.77),(.69,.64),(.84,.47))):
        th=turn+mirror*(.12+1.72*math.pi*t)
        rr=radius*(1-.76*t)
        px,pz=x+rr*math.cos(th),z+rr*math.sin(th)
        r.leaf(px,pz,th+mirror*(math.pi*.44),radius*.93*size,
               radius*.61*size,depth+.003*j,lift=radius*.14,
               curl=mirror*.24,phase=j*.6,steps=14)


def fan(b, o):
    """The complete entry fan: voussoirs, carved archivolts and foliate field."""
    conf=b.params.detail.get('conf',o['conf'])
    r=Relief(b,o,conf)
    cx=(o['u0']+o['u1'])/2;cz=o['spring_z'];rad=o['r_in']
    # The broad structural arch remains the opening record's measured outline.
    from archetypes.masonry_house_v4_detail import fractured_stone, stone_corner_normals
    import random
    count=o.get('voussoirs') or 11
    for i in range(count):
        a=math.pi*i/count+.004;c=math.pi*(i+1)/count-.004
        lo,hi=rad+.04,o['r_out']
        poly=[(cx+lo*math.cos(a),cz+lo*math.sin(a)),
              (cx+hi*math.cos(a),cz+hi*math.sin(a)),
              (cx+hi*math.cos(c),cz+hi*math.sin(c)),
              (cx+lo*math.cos(c),cz+lo*math.sin(c))]
        for facet,is_front in stone_corner_normals(fractured_stone(poly,.05,random.Random(90211+i*173))):
            if is_front:
                b.raw_with_normals([r.point(*p[:3]) for p in facet],
                                   [r.vector(*p[3:]) for p in facet],
                                   conf,12+i%4,r.vector(0,0,1))
            else:r.face(facet,12+i%4,None)
    # Bed lies behind all carving, letting the drilled pockets remain dark.
    # The wall builder removes the entire arch; overlap the voussoirs' inner
    # radius by 1 mm so their recessed carving bed cannot reveal the sky.
    bed_radius=o['r_out']
    r.solid([(cx+bed_radius*math.cos(math.pi*i/80),cz+bed_radius*math.sin(math.pi*i/80))
             for i in range(81)],-.065,-.045)
    field=rad*.65
    # Several mouldings, with actual convex and recessed cross sections.
    for rr,dd,t in ((.666,.020,.013),(.702,.040,.014),(.745,.030,.012),
                    (.943,.045,.014),(.986,.028,.010)):
        r.arc(cx,cz,rad*rr,dd,t)
    # Inner cove masonry divisions, set well behind the continuous rolls.
    for i in range(21):
        th=math.pi*(i+.5)/21
        r.tube([(cx+rad*.707*math.cos(th),cz+rad*.707*math.sin(th),.025),
                (cx+rad*.739*math.cos(th),cz+rad*.739*math.sin(th),.023)],.006,8)
    # Broad leaf arch: upright palmette stems with opposed lobed leaves.
    for i in range(19):
        th=math.pi*(i+.5)/19
        base=(cx+rad*.774*math.cos(th),cz+rad*.774*math.sin(th))
        r.leaf(*base,th,rad*.146,rad*.118,.051,.020,.04,True,i*.31,12)
        for side in (-1,1):
            # Fine flanking leaflets stay within their individual arch block.
            px=base[0]+side*rad*.028*(-math.sin(th))
            pz=base[1]+side*rad*.028*math.cos(th)
            r.leaf(px,pz,th+side*.35,rad*.108,rad*.050,.045,.014,
                   side*.08,False,steps=10)
    # The small, deep dentils have real recesses between them.
    for i in range(35):
        th=math.pi*(i+.5)/35;da=.018
        poly=[(cx+rr*math.cos(aa),cz+rr*math.sin(aa))
              for rr,aa in [(rad*.951,th-da),(rad*.981,th-da),
                            (rad*.981,th+da),(rad*.951,th+da)]]
        r.solid(poly,.010,.046)
    # Bilateral vine: the macro arrangement follows the photograph; the tiny
    # curls/leaf serrations are intentionally reconstructed rather than traced.
    def B(points,depth=.057,width=.010):
        path=_bezier([(cx+x*field,cz+z*field) for x,z in points],depth)
        r.tube(path,width,10)
    B([(0,.02),(-.04,.22),(.01,.48),(0,.85)],.060,.014)
    for mirror in (-1,1):
        B([(0,.09),(mirror*.13,.25),(mirror*.61,.17),(mirror*.69,.39)],.060,.011)
        B([(0,.34),(mirror*.05,.60),(mirror*.52,.56),(mirror*.41,.74)],.063,.010)
        _scroll(r,cx+mirror*field*.43,cz+field*.34,field*.34,.062,
                mirror,math.pi if mirror<0 else 0)
        _scroll(r,cx+mirror*field*.24,cz+field*.70,field*.205,.063,
                -mirror,math.pi*.55 if mirror<0 else math.pi*.45)
        r.leaf(cx+mirror*field*.06,cz+field*.02,
               math.pi*.5+mirror*.28,field*.36,field*.19,.070,.026,
               -mirror*.20,True,mirror*.4)
        r.leaf(cx+mirror*field*.07,cz+field*.45,
               math.pi*.5+mirror*.40,field*.32,field*.16,.074,.022,
               mirror*.12,False)


def sill(b, o):
    """Egg-and-dart, bead-and-reel, and two carved terminal blocks."""
    r=Relief(b,o,b.params.detail.get('conf',o['conf']))
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
    for mirror,x in ((-1,a-.215),(1,c+.215)):
        r.box(x-.22,x+.22,z0-.025,z1+.045,-.015,.068)
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


def _capital(r,u,z1,gap,variant):
    half=gap*.88;low=z1-.31;high=z1-.035;height=high-low
    # Tapered bell: broad shoulders over a narrower round column neck.
    for j in range(16):
        a,c=2*math.pi*j/16,2*math.pi*(j+1)/16
        for k in range(7):
            p,q=k/7,(k+1)/7
            def P(t,th):
                rad=gap*(.61+.25*math.sin(math.pi*t/2))
                return u+rad*math.cos(th),low+height*t,.055+rad*math.sin(th)
            r.face([P(p,a),P(p,c),P(q,c),P(q,a)],
                   normal=(math.cos((a+c)/2),.15,math.sin((a+c)/2)))
    r.box(u-half,u+half,high-.018,z1-.012,-.075,.198)
    for side in (-1,1):
        _scroll(r,u+side*half*.51,low+height*.71,half*.48,.224,
                -side,math.pi*.15 if side>0 else math.pi*.85)
    # Three hanging acanthus blades define deep eye-shaped undercuts.
    for j in range(3):
        x=u+(j-1)*half*.65
        r.leaf(x,low+.018,math.pi*.5+(j-1)*.14,height*.68,
               half*.77,.178,.050,(j-1)*.15,True,j*.4,16)
    if variant==1:
        # The middle capital has a small woven field above its central leaf.
        for j in range(5):
            x=u+(j-2)*half*.34
            r.tube([(x,high-.045,.235),(x+half*.13,high+.005,.229)],.009,8)
        for j in range(3):
            zz=high-.045+j*.026
            r.tube([(u-half*.79,zz,.232),(u+half*.79,zz,.232)],.008,8)
        r.arc(u,low+height*.65,half*.28,.247,.012,0,2*math.pi,32)
        for j in range(4):
            th=math.pi/4+j*math.pi/2
            r.leaf(u,low+height*.65,th,half*.24,half*.15,.248,.012,
                   .04,False,steps=8)
    else:
        # Unlike top treatments are plainly visible in the supplied closeup.
        for j in range(5):
            x=u+(j-2)*half*.36
            if variant==0:
                r.tube([(x-half*.13,high-.012,.224),(x,high+.019,.230),
                        (x+half*.13,high-.012,.224)],.008,8)
            else:
                r.arc(x,high-.001,half*.13,.222,.008,0,2*math.pi,16)


def columns(b, params):
    """Retain all Prairie shafts; give the entry's three capitals distinct carving."""
    ops=sorted([o for o in params.openings if o['kind']=='window' and
                o['face']=='east' and o['z0']>5],
               key=lambda o:(round(o['at'],3),round(o['z0'],2),o['u0']))
    bands=[o for o in params.openings if o['kind']=='band' and
           o['face']=='east' and o['z0']>5 and o['u1']-o['u0']>3]
    for a,c in zip(ops,ops[1:]):
        gap=c['u0']-a['u1']
        if not .12<gap<.3 or abs(a['z0']-c['z0'])>.05 or abs(a['at']-c['at'])>.05:
            continue
        u=(c['u0']+a['u1'])/2;z0,z1=a['z0'],a['z1']
        r=Relief(b,a,params.detail.get('conf',max(a['conf'],c['conf'])))
        _shaft(r,u,z0+.05,z1-.29,gap)
        r.box(u-gap*.78,u+gap*.78,z0,z0+.075,-.08,.16)
        _shaft(r,u,z0+.075,z0+.094,gap*1.08)
        band=next((o for o in bands if o['u0']<u<o['u1'] and abs(o['at']-a['at'])<.05),None)
        if band:
            variant=min(2,max(0,int(3*(u-band['u0'])/(band['u1']-band['u0']))))
            _capital(r,u,z1,gap,variant)
        else:
            # Preserve the prior alternate's coarse treatment outside the
            # photographed entry instead of borrowing the entry's motifs.
            r.box(u-gap*.88,u+gap*.88,z1-.19,z1-.035,-.07,.18)
            for j in range(5):
                dx=(j-2)*gap*.29
                r.solid([(u+dx-.022,z1-.13),(u+dx,z1-.195),
                         (u+dx+.022,z1-.13),(u+dx,z1-.055)],.17,.185)
            for j in range(8):
                theta=2*math.pi*j/8
                for k in range(4):
                    def P(t,side):
                        rad=gap*(.60+.22*math.sin(math.pi*t))
                        aa=theta+side*.27*math.sin(math.pi*t)
                        return u+rad*math.cos(aa),z1-.29+.25*t,.07+rad*math.sin(aa)
                    r.face([P(k/4,-1),P(k/4,1),P((k+1)/4,1),P((k+1)/4,-1)],
                           normal=(math.cos(theta),0,math.sin(theta)))


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
