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
def footprint(box):
    return list(box) if isinstance(box[0], (tuple,list)) else rect(*box)
def bounds_planes(box):
    if isinstance(box[0], (tuple,list)):
        return [(-(b[1]-a[1]),b[0]-a[0],(b[1]-a[1])*a[0]-(b[0]-a[0])*a[1])
                for a,b in zip(box,box[1:]+box[:1])]
    x0,x1,y0,y1=box
    return [(1,0,-x0),(-1,0,x1),(0,1,-y0),(0,-1,y1)]


def slope(axis,a,za,b,zb):
    m=(zb-za)/(b-a)
    return (m,0,za-m*a) if axis=='x' else (0,m,za-m*a)


def continuous_gable(r):
    """Level ridge, centered south gable, and the north court's flared eaves.

    The front gable keeps its carriage-door axis. Between the crossing range and
    courtyard corner, the ridge shifts in plan to the rear wing's midpoint while
    staying at one height. Triangulated station strips are continuous planar
    faces; no sampled warped quad and no south hip closes the roof.
    """
    import math
    g=r['stable_roof'];n=g['north_range'];x0,x1=r['x0'],r['x1']
    run=n['kick']['run_m'];rise=run*math.tan(math.radians(n['kick']['pitch_deg']))
    front=[(x0-.15,g['north_eave']), (g['front_x0'],g['north_eave']),
           (r['ridge_at'],r['ridge_z']),
           (x1-run,z(slope('x',r['ridge_at'],r['ridge_z'],x1,g['north_eave']),x1-run,0)),
           (x1,g['north_eave'])]
    rear=[(x0-.20,g['rear_west_eave']-.20*math.tan(math.radians(n['kick']['pitch_deg']))),
          (x0+run,g['rear_west_eave']+rise), (g['rear_x'],g['rear_z']),
          (x1-run,g['rear_east_eave']+rise),(x1+.20,g['rear_east_eave']-.20*math.tan(math.radians(n['kick']['pitch_deg'])))]
    stations=[(r['y0']-.20,rear),(n['y0'],rear),(g['cross_y'],front),(r['y1'],front)]
    result=[]
    for row,((ya,a),(yb,b)) in enumerate(zip(stations,stations[1:])):
        for col in range(len(a)-1):
            quad=[(a[col][0],ya,a[col][1]),(a[col+1][0],ya,a[col+1][1]),
                  (b[col+1][0],yb,b[col+1][1]),(b[col][0],yb,b[col][1])]
            for ti,ids in enumerate(((0,1,2),(0,2,3))):
                pts=[quad[k] for k in ids];p,q,s=pts
                u=[q[k]-p[k] for k in range(3)];v=[s[k]-p[k] for k in range(3)]
                normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                aa,bb=-normal[0]/normal[2],-normal[1]/normal[2]
                plane=(aa,bb,p[2]-aa*p[0]-bb*p[1])
                result.append((f'gable_{row}_{col}_{ti}',[(p[0],p[1]) for p in pts],[plane]))
    return result


def lower_rear_gable(r):
    """T-1999: high alley cross-gable, low rear roof, exact north-range join.

    The alley silhouette is controlled independently from the surveyed north
    range. A level cross crest reaches the stable's north-gable axis, then a
    short set of planar facets meets the north range's ridge and kicked eave.
    Every transition shares its boundary vertices. The rear gable remains level
    from its intersection with the crossing roof through the solid south end.
    """
    import math
    g = r['stable_roof']; n = g['north_range']
    x0, x1, xm = r['x0'], r['x1'], r['ridge_at']
    y0, y1 = r['y0'], r['y1']
    cy, sy = g['cross_y'], g['south_foot_y']
    cross = [slope('y', y1, g.get('north_west_eave', g['north_eave']), cy, g['cross_z']),
             slope('y', sy, g['cross_foot_eave'], cy, g['cross_z'])]
    rear = [slope('x', x0, g['rear_west_eave'], g['rear_x'], g['rear_z']),
            slope('x', x1, g['rear_east_eave'], g['rear_x'], g['rear_z'])]
    north = [slope('x', g['front_x0'], g.get('north_west_eave', g['north_eave']), xm, r['ridge_z']),
             slope('x', g['front_x1'], g['north_eave'], xm, r['ridge_z'])]
    result = [('cross', (x0-.15, xm, y0-.20, y1), cross),
              ('rear_gable', (x0-.15, x1, y0-.20, cy), rear),
              ('north', (x0-.15, x1, cy, y1), north)]
    # Match the north roof at its wall AND its actual courtyard overhang.
    # The extra station below the overhang tapers to the lower rear shoulder;
    # no vertical lip or floating fascia is concealed at the court corner.
    # The north range now has a planar, projecting court eave (T-2183).
    # Preserve its own profile and overhang at the join, including older kicks.
    run = n['kick']['run_m'] if n['kick'] else 0
    pitch = (math.tan(math.radians(n['kick']['pitch_deg'])) if n['kick'] else
             (n['ridge_z']-n['eave_lo_z'])/(n['ridge_at']-n['y0']))
    overhang = n.get('eave_lo_overhang', .20)
    east = [(sy, g['rear_east_eave']),
            (n['y0']-overhang, n['eave_lo_z']-overhang*pitch),
            (n['y0'], n['eave_lo_z']),
            *([(n['y0']+run, n['eave_lo_z']+run*pitch)] if run else []),
            (n['ridge_at'], n['ridge_z']),
            (y1, n['eave_hi_z'])]
    # The intermediate stations remain on one plane at the high gable side.
    # Their fractions correspond to the measured eastern eave/ridge section.
    middle = []
    for ey, _ in east:
        if ey <= n['ridge_at']:
            my = sy+(cy-sy)*(ey-sy)/(n['ridge_at']-sy)
        else:
            my = cy+(y1-cy)*(ey-n['ridge_at'])/(y1-n['ridge_at'])
        middle.append((my, min(z(p, xm, my) for p in cross)))
    for i, ((ma, mb), (ea, eb)) in enumerate(zip(zip(middle, middle[1:]), zip(east, east[1:]))):
        quad = [(xm, ma[0], ma[1]), (x1, ea[0], ea[1]),
                (x1, eb[0], eb[1]), (xm, mb[0], mb[1])]
        for j, ids in enumerate(((0, 1, 2), (0, 2, 3))):
            a, b, c = (quad[k] for k in ids)
            u = [b[k]-a[k] for k in range(3)]
            v = [c[k]-a[k] for k in range(3)]
            normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            aa, bb = -normal[0]/normal[2], -normal[1]/normal[2]
            plane = (aa, bb, a[2]-aa*a[0]-bb*a[1])
            result.append((f'court_join_{i}_{j}', [(q[0], q[1]) for q in (a,b,c)], [plane]))
    return result


def connected_roof(r):
    """T-2016: two straight gables, joined only at their true plane intersections.

    The stable keeps the surveyed north door/loft axis and its existing gable
    section all the way south. The lower E-W ridge retains the measured range
    height; it is locally occluded where the taller stable crosses it. No skewed
    connector, lowered rear ridge, hip, or warped four-corner patch is needed.
    """
    g=r['stable_roof'];n=g['north_range']
    stable=[slope('x',g['front_x0'],g['north_eave'],r['ridge_at'],r['ridge_z']),
            slope('x',g['front_x1'],g['north_eave'],r['ridge_at'],r['ridge_z'])]
    north=[slope('y',n['y0'],n['eave_lo_z'],n['ridge_at'],n['ridge_z']),
           slope('y',n['y1'],n['eave_hi_z'],n['ridge_at'],n['ridge_z'])]
    return [('stable_gable',(r['x0']-.20,r['x1']+.20,r['y0']-.20,r['y1']),stable),
            ('straight_north',(r['x0']-.20,r['x1']+.20,r['y0']-.20,n['y1']),north)]


def level_courtyard_gable(r):
    """T-2235: one full-height stable ridge, with a projecting court eave.

    The west-facing cross-gable is an intersecting roof, not the section of
    the whole wing. Its photographic silhouette therefore does not lower
    the north-south ridge or remove the courtyard slope. All joins are plane
    intersections; there is no falling/skewed ridge or courtyard filler.
    """
    g = r['stable_roof']; n = g['north_range']
    xm, peak = r['ridge_at'], r['ridge_z']
    edge = g['court_edge_x']
    court = slope('x', xm, peak, edge, g['court_edge_z'])
    stable = [slope('x', r['x0'], g['rear_west_eave'], xm, peak), court]
    front = [slope('x', g['front_x0'], g['north_west_eave'], xm, peak)]
    cross = [slope('y', r['y1'], g['north_west_eave'], g['cross_y'], g['cross_z']),
             slope('y', g['south_foot_y'], g['cross_foot_eave'], g['cross_y'], g['cross_z'])]
    north = [slope('y', n['y0'], n['eave_lo_z'], n['ridge_at'], n['ridge_z']),
             slope('y', n['y1'], n['eave_hi_z'], n['ridge_at'], n['ridge_z'])]
    return [('stable_gable', (r['x0']-.15, edge, r['y0']-.20, r['y1']), stable),
            ('north_gable', (r['x0']-.15, xm, g['cross_y'], r['y1']), front),
            ('cross', (r['x0']-.15, xm, r['y0']-.20, r['y1']), cross),
            ('straight_north', (xm, edge, r['y0']-.20, r['y1']), north)]


def components(r, include_dormer=True):
    g=r['stable_roof'];x0,x1,y0,y1=r['x0'],r['x1'],r['y0'],r['y1'];ov=.15
    box=(x0-ov,x1,y0-ov,y1)
    if g.get('level_courtyard_gable'):
        comps=level_courtyard_gable(r)
    elif g.get('connected_roof_plan'):
        comps=connected_roof(r)
    elif g.get('lower_rear_gable'):
        comps=lower_rear_gable(r)
    else:
        # Northern full west-facing gable. Its southern foot returns to the lower
        # alley eave; the old crossing range stopped far above that foot.
        cross=[slope('y',y1,g['north_eave'],g['cross_y'],g['cross_z']),
               slope('y',g['south_foot_y'],g.get('cross_foot_eave',g['rear_west_eave']),g['cross_y'],g['cross_z'])]
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
        if g.get('continuous_south_gable'):
            comps=[comps[0],*continuous_gable(r),*comps[3:]]
    if include_dormer and g.get('dormer'):
        d=g['dormer'];front=d['hood_front'];back=d['back'];overhang=d.get('hood_overhang_m',.25)
        a=d['u0']-overhang;c=d['u1']+overhang
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
        if d.get('connected_ridge'):
            # Remove the rear hip: the hood ridge now reaches the host slope.
            planes.pop(1)
            skirt.pop(1)
        comps.append(('dormer',(front,back,a,c),planes))
        comps.append(('dormer_skirt',(front,back,a,c),skirt))
    return comps


def height(r,x,y,include_dormer=False):
    vals=[min(z(p,x,y) for p in ps) for _,box,ps in components(r,include_dormer)
          if all(z(b,x,y)>=-EPS for b in bounds_planes(box))]
    return max(vals) if vals else 0.


def patches(r, include_dormer=True):
    comps=components(r,include_dormer)
    result=[]
    for ci,(name,box,planes) in enumerate(comps):
        for pi,p in enumerate(planes):
            poly=footprint(box)
            for other in planes:
                poly=clip(poly,tuple(other[k]-p[k] for k in range(3)))
            if not poly:continue
            remaining=[poly]
            for cj,(_,other_box,others) in enumerate(comps):
                if ci==cj:continue
                # A competing roof covers this patch only where ALL its slopes
                # are above p and its footprint contains it. Difference of convex
                # regions is emitted as disjoint convex pieces.
                edge_tests=bounds_planes(other_box)
                tests=edge_tests+[tuple(o[k]-p[k] for k in range(3)) for o in others]
                if any(max(abs(q) for q in t)<EPS for t in tests[len(edge_tests):]) and cj>ci:continue
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
        cuts.update(p[1 if axis=='y' else 0] for p in footprint(box)
                    if lo<p[1 if axis=='y' else 0]<hi)
        # A station triangle can enter the wall at a diagonal footprint edge,
        # between its vertices. Include that boundary before linearizing it.
        for a,b,c in bounds_planes(box):
            m,offset=(b,a*fixed+c) if axis=='y' else (a,b*fixed+c)
            if abs(m)>EPS and lo<-offset/m<hi:cuts.add(-offset/m)
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
    if g.get('level_courtyard_gable'):
        candidates=[('y',r['ridge_at'],r['ridge_z'],r['y0'],r['y1']),
                    ('x',g['cross_y'],g['cross_z'],r['x0'],r['ridge_at']),
                    ('x',g['north_range']['ridge_at'],g['north_range']['ridge_z'],r['ridge_at'],g['court_edge_x'])]
        d=g.get('dormer')
        if d and d.get('connected_ridge'):
            candidates.append(('x',(d['u0']+d['u1'])/2,d['apex_z'],d['crest_x'],d['back']))
    if g.get('connected_roof_plan'):
        candidates=[('y',r['ridge_at'],r['ridge_z'],r['y0'],r['y1']),
                    ('x',g['north_range']['ridge_at'],g['north_range']['ridge_z'],r['x0'],r['x1'])]
        d=g.get('dormer')
        if d and d.get('connected_ridge'):
            candidates.append(('x',(d['u0']+d['u1'])/2,d['apex_z'],d['crest_x'],d['back']))
    if g.get('continuous_south_gable'):
        candidates=[('y',r['ridge_at'],r['ridge_z'],g['cross_y'],r['y1']),
                    ('x',g['cross_y'],g['cross_z'],r['x0'],r['x1']),
                    ('y',g['rear_x'],g['rear_z'],r['y0'],g['north_range']['y0'])]
    if g.get('lower_rear_gable'):
        candidates=[('y',r['ridge_at'],r['ridge_z'],g['cross_y'],r['y1']),
                    ('x',g['cross_y'],g['cross_z'],r['x0'],r['ridge_at']),
                    ('y',g['rear_x'],g['rear_z'],r['y0'],g['cross_y'])]
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
    if g.get('lower_rear_gable'):
        lo,hi=r['ridge_at'],r['x1'];n=g['north_range']
        out.append(({**r,'axis':'x','ridge_at':g['cross_y'],'ridge_z':g['cross_z'],
                     'ridge_origin':lo,'ridge_skew':(n['ridge_at']-g['cross_y'])/(hi-lo),
                     'ridge_slope':(n['ridge_z']-g['cross_z'])/(hi-lo)},lo,hi))
    if g.get('continuous_south_gable') and not g.get('lower_rear_gable'):
        lo,hi=g['north_range']['y0'],g['cross_y']
        out.append(({**r,'axis':'y','ridge_at':g['rear_x'],'ridge_z':g['rear_z'],
                     'ridge_origin':lo,'ridge_skew':(r['ridge_at']-g['rear_x'])/(hi-lo)},lo,hi))
    return out
