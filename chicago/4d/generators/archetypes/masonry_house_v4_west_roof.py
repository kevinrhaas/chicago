"""T-1830: planar roof union for the Glessner stable; no Blender dependency.

Each roof is the minimum of its slope planes, over a convex footprint. Visible
patches are the upper envelope of these solids. Intersections are clipped at
actual plane equality, never approximated by a warped sampling grid.
"""
from __future__ import annotations

EPS = 1e-8


def z(plane, x, y):
    return plane[0]*x + plane[1]*y + plane[2]


def clip(poly, plane):
    """Keep the half plane a*x+b*y+c >= 0."""
    if not poly: return []
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        za,zb=z(plane,*a),z(plane,*b)
        if za>=-EPS: out.append(a)
        if (za>EPS and zb<-EPS) or (za<-EPS and zb>EPS):
            t=za/(za-zb);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    clean=[]
    for p in out:
        if not clean or sum((p[i]-clean[-1][i])**2 for i in (0,1))>EPS**2:clean.append(p)
    if len(clean)>1 and sum((clean[0][i]-clean[-1][i])**2 for i in (0,1))<EPS**2:clean.pop()
    return clean if len(clean)>2 and abs(area(clean))>EPS else []


def area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2


def rect(x0,x1,y0,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
def bounds_planes(box):
    x0,x1,y0,y1=box
    return [(1,0,-x0),(-1,0,x1),(0,1,-y0),(0,-1,y1)]


def slope(axis,a,za,b,zb):
    m=(zb-za)/(b-a)
    return (m,0,za-m*a) if axis=='x' else (0,m,za-m*a)


def components(r, include_dormer=True):
    g=r['stable_roof'];x0,x1,y0,y1=r['x0'],r['x1'],r['y0'],r['y1'];ov=.15
    box=(x0-ov,x1,y0-ov,y1)
    # Northern full west-facing gable. Its southern foot returns to the lower
    # alley eave; the old crossing range stopped far above that foot.
    cross=[slope('y',y1,g['north_eave'],g['cross_y'],g['cross_z']),
           slope('y',g['south_foot_y'],g['rear_west_eave'],g['cross_y'],g['cross_z'])]
    # The shorter, asymmetric rear range has a hipped south end. The hip stays
    # above the sheet-3 upper windows and does not invent a full-height rear gable.
    rear=[slope('x',x0,g['rear_west_eave'],g['rear_x'],g['rear_z']),
          slope('x',x1,g['rear_east_eave'],g['rear_x'],g['rear_z']),
          slope('y',y0,g['south_eave'],g['hip_y'],g['rear_z'])]
    north=[slope('x',g['front_x0'],g['north_eave'],r['ridge_at'],r['ridge_z']),
           slope('x',g['front_x1'],g['north_eave'],r['ridge_at'],r['ridge_z']),
           slope('y',g['front_hip_y'],r['ridge_z'],g['cross_y'],g['cross_z'])]
    # The north-range courtyard kick meets the higher east-side wall. A narrow
    # inward-sloping connector preserves that surveyed section at its seam.
    n=g['north_range'];nr=n['ridge_at'];nz=n['ridge_z'];yk=n['y0']+n['kick']['run_m']
    import math
    zk=n['eave_lo_z']+n['kick']['run_m']*math.tan(math.radians(n['kick']['pitch_deg']))
    high=slope('y',yk,zk,nr,nz);low=slope('y',n['y0'],n['eave_lo_z'],yk,zk)
    def taper(p):return (p[0]+1.5,p[1],p[2]-1.5*x1)
    comps=[('cross',box,cross),('rear',(x0-ov,x1,y0-ov,g['cross_y']),rear),
           ('north',(x0-ov,x1,g['cross_y'],y1),north),
           ('connector_upper',(x0-ov,x1,yk,nr),[taper(high)]),
           ('connector_kick',(x0-ov,x1,n['y0'],yk),[taper(low)])]
    if include_dormer and g.get('dormer'):
        d=g['dormer'];front=d['hood_front'];back=d['back'];a=d['u0']-.25;c=d['u1']+.25
        peak=d['apex_z'];eave=d['eave_z'];cx=d['crest_x'];mid=(a+c)/2
        # Hipped, flared hood, with a level eave at the front and both sides.
        inner=(front+.42,back-.12,a+.23,c-.23);rise=.13
        planes=[slope('x',inner[0],eave+rise,cx,peak),slope('x',inner[1],eave+rise,cx,peak),
                slope('y',inner[2],eave+rise,mid,peak),slope('y',inner[3],eave+rise,mid,peak)]
        # A shallow skirt meets the steeper cap at the inner rectangle. Their
        # upper envelope makes the small concave flare visible at the eaves.
        skirt=[slope('x',front,eave,inner[0],eave+rise),
               slope('x',back,eave,inner[1],eave+rise),
               slope('y',a,eave,inner[2],eave+rise),
               slope('y',c,eave,inner[3],eave+rise)]
        comps.append(('dormer',(front,back,a,c),planes))
        comps.append(('dormer_skirt',(front,back,a,c),skirt))
    return comps


def height(r,x,y,include_dormer=False):
    vals=[min(z(p,x,y) for p in ps) for _,box,ps in components(r,include_dormer)
          if all(z(b,x,y)>=-EPS for b in bounds_planes(box))]
    return max(vals) if vals else 0.


def patches(r):
    comps=components(r)
    result=[]
    for ci,(name,box,planes) in enumerate(comps):
        for pi,p in enumerate(planes):
            poly=rect(*box)
            for other in planes:
                poly=clip(poly,tuple(other[k]-p[k] for k in range(3)))
            if not poly:continue
            remaining=[poly]
            for cj,(_,other_box,others) in enumerate(comps):
                if ci==cj:continue
                # A competing roof covers this patch only where ALL its slopes
                # are above p and its footprint contains it. Difference of convex
                # regions is emitted as disjoint convex pieces.
                tests=bounds_planes(other_box)+[tuple(o[k]-p[k] for k in range(3)) for o in others]
                if any(max(abs(q) for q in t)<EPS for t in tests[4:]) and cj>ci:continue
                kept=[]
                for piece in remaining:
                    inside=piece
                    for t in tests:
                        outside=clip(inside,tuple(-v for v in t))
                        if outside:kept.append(outside)
                        inside=clip(inside,t)
                        if not inside:break
                remaining=kept
            for poly in remaining:
                result.append((name,[(x,y,z(p,x,y)) for x,y in poly]))
    return result


def profile(r,face):
    fixed=r['x0'] if face=='west' else r['x1'] if face=='east' else r['y0'] if face=='south' else r['y1']
    axis='y' if face in ('west','east') else 'x'
    lo,hi=(r['y0'],r['y1']) if axis=='y' else (r['x0'],r['x1'])
    cuts={lo,hi};planes=[]
    for _,box,ps in components(r,False):
        cuts.update(v for v in (box[2:4] if axis=='y' else box[0:2]) if lo<v<hi)
        planes+=ps
    for p in planes:
        for q in planes:
            m=p[1]-q[1] if axis=='y' else p[0]-q[0]
            b=(p[0]-q[0])*fixed+p[2]-q[2] if axis=='y' else (p[1]-q[1])*fixed+p[2]-q[2]
            if abs(m)>EPS and lo<-b/m<hi:cuts.add(-b/m)
    vals=[(u,height(r,fixed,u) if axis=='y' else height(r,u,fixed)) for u in sorted(cuts)]
    out=[]
    for p in vals:
        while len(out)>=2 and abs((out[-1][1]-out[-2][1])*(p[0]-out[-1][0])-(p[1]-out[-1][1])*(out[-1][0]-out[-2][0]))<1e-7:out.pop()
        out.append(p)
    return out


def ridge_ranges(r):
    """Only crest ridge segments that actually touch the visible roof."""
    if not r.get('stable_roof'):
        a0,a1=(r['y0'],r['y1']) if r['axis']=='y' else (r['x0'],r['x1'])
        for side,v in r['roof_extend'].items():
            if side in ('south','west'):a0=min(a0,v)
            else:a1=max(a1,v)
        a0=max(a0,r.get('roof_min',a0))
        return [(r,a0,a1)]
    g=r['stable_roof'];candidates=[('y',r['ridge_at'],r['ridge_z'],g['front_hip_y'],r['y1']),
      ('x',g['cross_y'],g['cross_z'],r['x0'],r['x1']),
      ('y',g['rear_x'],g['rear_z'],g['hip_y'],g['cross_y'])]
    out=[]
    for axis,at,rz,lo,hi in candidates:
        steps=max(1,round((hi-lo)/.08));start=None
        for i in range(steps+1):
            a=lo+(hi-lo)*i/steps
            ok=abs((height(r,at,a,True) if axis=='y' else height(r,a,at,True))-rz)<.015
            if ok and start is None:start=a
            if (not ok or i==steps) and start is not None:
                if a-start>.05:out.append(({**r,'axis':axis,'ridge_at':at,'ridge_z':rz},start,a))
                start=None
    return out
