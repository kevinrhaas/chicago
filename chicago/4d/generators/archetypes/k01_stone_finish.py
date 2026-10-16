"""T-1883: measured stone-front finish, independent of the building's footprint.

Opt-in dimensions live in form.stone_finish. The pierced panels are actual openings;
turned shafts, spiral volutes and rock-faced diaper units are geometry, never decals.
The small carving sections are reconstructed; see L-k01-keith-finish-1883.
"""
from __future__ import annotations
import math
import random


def box_faces(x0, x1, y0, y1, z0, z1):
    p = [(x,y,z) for x in (x0,x1) for y in (y0,y1) for z in (z0,z1)]
    for ids, n in (((0,1,3,2),(-1,0,0)), ((4,6,7,5),(1,0,0)),
                   ((0,4,5,1),(0,-1,0)), ((2,3,7,6),(0,1,0)),
                   ((0,2,6,4),(0,0,-1)), ((1,5,7,3),(0,0,1))):
        yield [p[i] for i in ids], n


def turned_faces(x, z, profile, segments=20, flutes=0, cap_bottom=True):
    rings = [[(x+r*(1+flutes*math.cos(8*t-9*y))*math.cos(t),y,
               z+r*(1+flutes*math.cos(8*t-9*y))*math.sin(t))
              for t in (2*math.pi*i/segments for i in range(segments))] for r,y in profile]
    for a,b in zip(rings,rings[1:]):
        for i in range(segments):
            j=(i+1)%segments
            t=2*math.pi*(i+.5)/segments
            yield [a[i],b[i],b[j],a[j]], (math.cos(t),0,math.sin(t))
    if cap_bottom:
        yield rings[0],(0,-1,0)
    yield list(reversed(rings[-1])),(0,1,0)


def tube_faces(points, radius, sides=8):
    """A rounded carving following an s/y path, its axis normal in the depth direction."""
    rings=[]
    for i,(x,y,z) in enumerate(points):
        a,b=points[max(0,i-1)],points[min(len(points)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        rings.append([(x+radius*nx*math.cos(t),y+radius*ny*math.cos(t),z+radius*math.sin(t))
                      for t in (2*math.pi*j/sides for j in range(sides))])
    for a,b in zip(rings,rings[1:]):
        for i in range(sides):
            j=(i+1)%sides
            yield [a[i],a[j],b[j],b[i]], None
    yield rings[0],None
    yield list(reversed(rings[-1])),None


def oriented(pts, outward):
    """The face wound so its normal agrees with `outward` (local s/y/d frame)."""
    a,b,c=pts[0],pts[1],pts[2]
    u=(b[0]-a[0],b[1]-a[1],b[2]-a[2]); v=(c[0]-a[0],c[1]-a[1],c[2]-a[2])
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    return (pts if n[0]*outward[0]+n[1]*outward[1]+n[2]*outward[2]>=0 else list(reversed(pts))), outward


def swept_faces(path, profile, bed=0.):
    """A moulding swept along s. `path` is [(s, lift)]; `profile` a convex (d, y) section,
    counter-clockwise, whose points above its bed (y > 0) are raised by the path's lift,
    so the bed (at height `bed`) stays on the wall while the moulding rises into a pinnacle's base."""
    cd=math.fsum(d for d,_ in profile)/len(profile); cy=math.fsum(y for _,y in profile)/len(profile)
    secs=[[(sv,y+(lift if y>bed+1e-9 else 0),d) for d,y in profile] for sv,lift in path]
    m=len(profile)
    for a,b in zip(secs,secs[1:]):
        for i in range(m):
            j=(i+1)%m
            (d0,y0),(d1,y1)=profile[i],profile[j]
            mid=((d0+d1)/2-cd,(y0+y1)/2-cy)
            # the edge's normal in the section, turned away from the section's centre
            nd,ny=(y1-y0),-(d1-d0)
            if nd*mid[0]+ny*mid[1]<0: nd,ny=-nd,-ny
            yield oriented([a[i],b[i],b[j],a[j]],(0,ny,nd))
    yield oriented(secs[0],(-1,0,0))
    yield oriented(secs[-1],(1,0,0))


def ogive(r,base,height,collar=True):
    """A pinnacle cap as the photographs show it: a moulded collar, then a convex
    (ogival) cone closing to a short neck and a ball finial."""
    prof=[(r*1.08,base),(r*1.08,base+.1),(r*.94,base+.13)] if collar else [(r*.94,base)]
    body=height*.8
    for k in range(1,8):
        t=k/8
        prof.append((max(.03,r*.94*math.cos(t*math.pi/2)**.75),base+.13+body*t))
    top=base+.13+body
    prof+=[(.03,top+.02),(.055,top+.05),(.055,top+.09),(.02,top+.12)]
    return prof


def spiral(x,y,z,radius,side=1):
    return [(x+side*radius*(1-.82*i/32)*math.cos(3.5*math.pi*i/32),
             y+radius*(1-.82*i/32)*math.sin(3.5*math.pi*i/32),z) for i in range(33)]


def validate(f, width):
    if not f:
        return f
    expected={'lattice','diaper','colonnettes','pinnacles','deck_drop_m','stone_return_m'}
    if set(f)-{'return_ashlar'}!=expected:
        raise ValueError(f'stone_finish takes {sorted(expected)} and optionally return_ashlar')
    ra=f.get('return_ashlar')
    if ra is not None and (set(ra)!={'course_m','bond_m','rise_m','sweep_m'} or not (
            .25<=ra['course_m']<=.7 and len(ra['bond_m'])==2 and .5<=ra['bond_m'][0]<ra['bond_m'][1]<=2.5
            and 0<=ra['rise_m']<=.4 and .2<=ra['sweep_m']<=1.5)):
        raise ValueError('stone_finish.return_ashlar: bounded courses, bond lengths and coping sweep')
    l=f['lattice']
    if set(l)!={'height_m','pitch_m','bar_m','thickness_m','return_m'} or not (.6<=l['height_m']<=1.6 and
            .25<=l['pitch_m']<=.7 and .08<=l['bar_m']<l['pitch_m']/2 and .15<=l['thickness_m']<=.5 and
            0<=l['return_m']<=8):
        raise ValueError('stone_finish.lattice: two open rows, bounded bars, thickness and return')
    if not .8<=f['deck_drop_m']<=2 or not 0<=f['stone_return_m']<=8:
        raise ValueError('stone_finish: concealed deck and side stone return outside bounds')
    d=f['diaper']
    if set(d)!={'bottom_m','top_m','pitch_m','proud_m','stagger','relief_m'} or not (d['bottom_m']<d['top_m'] and
            .2<=d['pitch_m']<=.6 and .02<=d['proud_m']<=.15 and 0<=d['stagger']<=.5 and
            .008<=d['relief_m'][0]<=d['relief_m'][1]<=.046):
        raise ValueError('stone_finish.diaper: measured band, staggered rows and bounded rock relief')
    c=f['colonnettes']
    if set(c)!={'axes_m','bottom_m','top_m','radius_m'} or not (.06<=c['radius_m']<=.2 and c['bottom_m']<c['top_m'] and
            all(0<s<width for s in c['axes_m'])):
        raise ValueError('stone_finish.colonnettes: shafts inside the front')
    p=f['pinnacles']
    if set(p)!={'height_m','radius_m'} or not (.5<=p['height_m']<=1.5 and .15<=p['radius_m']<=.4):
        raise ValueError('stone_finish.pinnacles: bounded stone caps')
    return f


def dress(a):
    f=a.p.stone_finish
    if not f:
        return
    from .k01_frontage import Y, _cross, _sub
    D,W,E=a.p.depth_m,a.p.width_m,a.p.eave_m
    conf=a.p.conf('stone_finish')
    seed=a.instance('k01.finish.pierced_stone','trim',f,{'seat':(D,E,0)})
    frame=((D,0,0),(0,0,-1),(1,0,0))

    def emit(faces,mat='dress_stone',transform=lambda p:(D+p[2],p[1],-p[0])):
        pr=a.prim(mat)
        for pts,_ in faces:
            pts=[transform(p) for p in pts]
            n=_cross(_sub(pts[1],pts[0]),_sub(pts[2],pts[0]))
            norm=math.sqrt(math.fsum(x*x for x in n))
            if norm<1e-10:
                continue
            n=tuple(x/norm for x in n)
            a._sface(mat,pts,n,pts[0],(0,0,-1),seed,False,conf)

    def box(s0,s1,y0,y1,d0,d1,mat='dress_stone',transform=None):
        kwargs={'mat':mat}
        if transform: kwargs['transform']=transform
        emit(box_faces(s0,s1,y0,y1,d0,d1),**kwargs)

    l=f['lattice']; h,b,t=l['height_m'],l['bar_m'],l['thickness_m']
    base=E+.12; top=base+h
    def lattice(length,transform=None):
        # Three continuous rails; staggered uprights leave two rows of square sky holes.
        for yy in (base,base+h/2-b/2,top-b):
            box(0,length,yy,yy+b,-t,0,transform=transform)
        count=max(2,round(length/l['pitch_m']))
        pitch=length/count
        for row in range(2):
            low=base+b if row==0 else base+h/2+b/2
            high=base+h/2-b/2 if row==0 else top-b
            for j in range(count+1):
                s=j*pitch+(pitch/2 if row else 0)
                if s>=length: continue
                box(max(0,s-b/2),min(length,s+b/2),low,high,-t,0,transform=transform)
        if ra and transform is None:
            # T-2564: the street views show the front coping sweeping up into each corner
            # pinnacle's base, as the return's does
            sw,rs=ra['sweep_m'],ra['rise_m']
            path=([(-.06+sw*k/8,rs*(1-k/8)**2) for k in range(8)]
                  +[(length+.06-sw*(1-k/8),rs*(k/8)**2) for k in range(1,9)])
            emit(swept_faces(path,[(-t-.045,top),(.045,top),(.045,top+.1),(-t-.045,top+.1)],top))
        else:
            box(-.06,length+.06,top,top+.1,-t-.045,.045,transform=transform)
    ra=f.get('return_ashlar')
    lattice(W)
    ret=l['return_m']
    # North return is inside the property; it never projects into Glessner's wall.
    side=lambda p:(D-p[0],p[1],-W-p[2])
    pin=f['pinnacles']; r,ph=pin['radius_m'],pin['height_m']
    if ret and not ra:
        box(0,ret,base,top,-t,0,transform=side)
        box(0,ret,top,top+.1,-t-.03,0,transform=side)
    elif ret:
        # T-2564: the 1887-88 street views show the return as a solid parapet of large
        # dressed courses (laid below with the wall's), under a rounded coping that sweeps
        # up into the corner pinnacle's base. The core stands behind the coursed face.
        box(0,ret,E,top,-t,-.027,transform=side)
        wc=t+.05; sweep,rise=ra['sweep_m'],ra['rise_m']
        section=[(-wc,0.),(0.,0.),(0.,.08)]+[(-wc/2+wc/2*math.cos(math.pi*k/8),.08+.12*math.sin(math.pi*k/8))
                                            for k in range(1,8)]+[(-wc,.08)]
        path=[(sweep*k/8,rise*(1-k/8)**2) for k in range(8)]+[(ret,0.)]
        emit(swept_faces(path,[(dd,top+yy) for dd,yy in section],top),transform=side)
    for s,d in ((r*.6,-t/2),(W-r*.6,-t/2)):
        if ra:
            profile=[(r*.8,base-.45),(r*.8,top-.12)]+ogive(r,top-.1,ph)
        else:
            profile=[(r*.8,base-.45),(r*.8,top-.12),(r*1.08,top-.1),(r*1.08,top+.04),
                     (r*.85,top+.12),(r*.72,top+.16),(r*.58,top+ph*.45),(r*.1,top+ph*.92),(.018,top+ph)]
        emit(turned_faces(s,d,profile,32,.06))
    if ret and ra:
        # The rear pinnacle sits on the coping, smaller than the corner's, with no shaft.
        # Its collar stays inside the lot line, centred on the coping.
        emit(turned_faces(ret-.25,-.22,[(r*.62,top+.12),(r*.62,top+.2)]+ogive(r*.7,top+.2,ph*.85),24,.04),
             transform=side)
    elif ret:
        emit(turned_faces(ret-.16,-t/2,[(r*.8,base-.45),(r*.8,top),(r,top+.08),
                  (r*.7,top+.15),(.018,top+ph)],24,.04),transform=side)
    di=f['diaper']; y0,y1,pitch=di['bottom_m'],di['top_m'],di['pitch_m']
    rows=max(1,round((y1-y0)/pitch)); cols=max(1,round((W-.5)/pitch))
    step=(W-.5)/cols
    rng=random.Random(seed^0xD1A9)
    for row in range(rows):
        # T-2566: the photographs lay the band as rows of rough lumps, each row's joints
        # broken over the row below's (`stagger` of a stone), not one square grid; the
        # proud stones stand out by differing amounts and every face is rock-faced
        shift=di['stagger']*step if row%2 else 0
        edges=sorted({.25,W-.25,*[.25+shift+col*step for col in range(cols+1) if .25<.25+shift+col*step<W-.25]})
        lo=y0+row*(y1-y0)/rows+.01; hi=y0+(row+1)*(y1-y0)/rows-.01
        for col,(e0,e1) in enumerate(zip(edges,edges[1:])):
            if e1-e0<.06:
                continue
            x0,x1=e0+.012,e1-.012
            out=di['proud_m']*(rng.uniform(.55,1.0) if (row+col)%2 else rng.uniform(0,.25))
            # The same rock-face builder as the main K02 courses: metric joints and bevels.
            a.stone(frame,[(x0,lo),(x1,lo),(x1,hi),(x0,hi)],[False]*4,'rough_stone_trim',seed+row*(cols+1)+col,conf,
                    recess=0,bevel=.009,F=.055+out,rock=rng.uniform(*di['relief_m']))
    # T-2566: the head band under the checker and the corbelled bands over it are moulded,
    # stepped out in fillets (bottom up: height, projection), not one plain block each
    for yy,steps in ((y0-.18,((.04,.07),(.05,.10),(.09,.14))),(y1,((.04,.08),(.04,.11),(.04,.14))),
                     (E,((.04,.14),(.08,.22)))):
        for height,proud in steps:
            box(0,W,yy,yy+height,-.03,proud)
            yy+=height
    c=f['colonnettes']; low,high,r=c['bottom_m'],c['top_m'],c['radius_m']
    for s in c['axes_m']:
        # T-2566: the capital is a neck ring under a flaring bell, as the 1888 plate's
        # upper colonnettes spread into the lintel band
        emit(turned_faces(s,.13,[(r*1.5,low),(r*1.5,low+.08),(r,low+.18),(r*.87,high-.32),
                    (r*1.08,high-.31),(r*1.08,high-.26),(r*.9,high-.25),(r*1.2,high-.15),
                    (r*1.55,high-.06),(r*1.7,high)],20))
        box(s-r*1.8,s+r*1.8,high-.04,high+.07,-.02,.34)
    box(min(c['axes_m'])-.65,max(c['axes_m'])+.65,high+.07,high+.23,-.03,.2)
    # The short visible north return above Glessner is stone-faced in the street views.
    # Keep the face inside the footprint and seat the finish on the existing brick wall.
    if f['stone_return_m'] and not ra:
        box(0,f['stone_return_m'],a.p.floors_m[2]+.1,E,-.25,-.015,'rough_stone_trim',side)
    elif f['stone_return_m']:
        # T-2564: one field of large dressed courses from the third floor to the coping,
        # its face 15 mm inside the lot line, bonded with staggered joints. The backing
        # stands behind the joints; nothing projects towards Glessner.
        lo=a.p.floors_m[2]+.1; hi=top if ret else E
        box(0,f['stone_return_m'],lo,E,-.25,-.027,'dress_stone',side)
        length=max(f['stone_return_m'],ret)
        sframe=((D,0,-W+.015),(-1,0,0),(0,0,-1))
        rng=random.Random(seed+2564)
        rows=max(1,round((hi-lo)/ra['course_m']))
        for row in range(rows):
            y0=lo+row*(hi-lo)/rows; y1=lo+(row+1)*(hi-lo)/rows
            cuts=[0.]
            first=ra['bond_m'][0]*(.55 if row%2 else 1.)
            x=first+rng.uniform(0,.2)
            while x<length-ra['bond_m'][0]*.6:
                cuts.append(x); x+=rng.uniform(*ra['bond_m'])
            cuts.append(length)
            for k,(s0,s1) in enumerate(zip(cuts,cuts[1:])):
                joints=[0. if row==0 else .006,0. if s1>=length else .006,0. if row==rows-1 else .006,0. if s0<=0 else .006]
                a.stone(sframe,[(s0,y0),(s1,y0),(s1,y1),(s0,y1)],joints,'dress_stone',seed+5000+row*40+k,conf,
                        recess=.02,bevel=.012,F=0.0,rock=.004)
