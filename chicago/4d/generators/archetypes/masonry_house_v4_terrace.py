"""HABS 2/4 courtyard terrace, closed curved coping and bounded winder flight.

Dimensions and traced plan boundaries live in the structure record. The lower
turn and its joins to the retained bow/tower are declared reconstructions.
"""
from __future__ import annotations
import math

from archetypes.masonry_house_v4_materials import BRICK, TRIM, DRIVE, IRON

def _point(data,r,a,z):
    return (data['cx']+r*math.cos(a),data['cy']+r*math.sin(a),z)

def _clip(poly,a,c,keep):
    """Clip an XY polygon against a tread line; preserve the floor's Z."""
    def side(p):return ((c[0]-a[0])*(p[1]-a[1])-(c[1]-a[1])*(p[0]-a[0]))*keep
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        sp,sq=side(p),side(q)
        if sp>=-1e-9:out.append(p)
        if (sp>0) != (sq>0):
            t=sp/(sp-sq)
            out.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(3)))
    return out

def _profile(points,x):
    """Monotone cubic interpolation of measured section points, without overshoot."""
    if x<=points[0][0]:return points[0][1]
    if x>=points[-1][0]:return points[-1][1]
    i=next(i for i in range(len(points)-1) if points[i+1][0]>=x)
    def slope(j):
        if j==0 or j==len(points)-1:return 0.
        h0=points[j][0]-points[j-1][0];h1=points[j+1][0]-points[j][0]
        d0=(points[j][1]-points[j-1][1])/h0;d1=(points[j+1][1]-points[j][1])/h1
        if d0*d1<=0:return 0.
        w0=2*h1+h0;w1=h1+2*h0
        return (w0+w1)/(w0/d0+w1/d1)
    a,c=points[i:i+2];h=c[0]-a[0];t=(x-a[0])/h
    return ((2*t**3-3*t*t+1)*a[1]+(t**3-2*t*t+t)*h*slope(i)
            +(-2*t**3+3*t*t)*c[1]+(t**3-t*t)*h*slope(i+1))

def cap_height(data,a,lower=False):
    # Both edges are independently measured in the section. A constant vertical
    # thickness collapses toward zero normal thickness on the steep descent.
    key='lower_S_zft' if lower else 'upper_S_zft'
    return _profile(data['cap_section_profile'][key],-(data['r']+.055)*math.sin(a))

def _solid(b,outline,z0,z1,conf,mat):
    """A closed prism; no stair relies on the view hiding its side or underside.

    T-2906: a tread that runs along the drum is not convex, so its top and
    underside are laid in convex pieces and each side faces out of the outline.
    """
    if len(outline)<3:return
    from archetypes.masonry_house_v4_ground import parts
    turn=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(outline,outline[1:]+outline[:1]))
    for piece in parts(outline):
        b.raw([(*p[:2],z1) for p in piece],conf,mat,(0,0,1))
        b.raw([(*p[:2],z0) for p in piece],conf,mat,(0,0,-1))
    for p,q in zip(outline,outline[1:]+outline[:1]):
        want=((q[1]-p[1])*turn,(p[0]-q[0])*turn,0)
        b.raw([(*p,z0),(*q,z0),(*q,z1),(*p,z1)],conf,mat,want)

def _newel(b,data,conf,reduced):
    x,y=data['newel_xy'];r=data['newel_r']
    z=data['newel_top'];crown=data['newel_crown']
    rings=[(r,-.04),(r,z-crown)]
    rings += [(r*math.cos(math.pi*.5*i/4),z-crown+crown*math.sin(math.pi*.5*i/4)) for i in range(1,5)]
    count=16 if reduced else 48
    for j,((r0,z0),(r1,z1)) in enumerate(zip(rings,rings[1:])):
        for i in range(count):
            a,c=2*math.pi*i/count,2*math.pi*(i+1)/count
            def p(rad,t,h):return (x+rad*math.cos(t),y+rad*math.sin(t),h)
            pts=[p(r0,a,z0),p(r0,c,z0),p(r1,c,z1),p(r1,a,z1)]
            def normal(rad,t,h):
                if j==0:return (math.cos(t),math.sin(t),0)
                v=(rad*math.cos(t)/(r*r),rad*math.sin(t)/(r*r),(h-z+crown)/(crown*crown))
                length=math.sqrt(sum(q*q for q in v))
                return tuple(q/length for q in v)
            ns=[normal(r0,a,z0),normal(r0,c,z0),normal(r1,c,z1),normal(r1,a,z1)]
            if r1<1e-8:pts=pts[:3];ns=ns[:3]
            b.raw_with_normals(pts,ns,conf,TRIM,(math.cos((a+c)/2),math.sin((a+c)/2),.2 if j else 0))
    b.raw([(x+r*math.cos(2*math.pi*i/count),y+r*math.sin(2*math.pi*i/count),-.04) for i in range(count)],conf,TRIM,(0,0,-1))

def tread_tops(data,floor,n):
    """Each tread's top. Even risers from the deck, unless the record carries
    the drawn tops of the lowest treads; the treads above them then share the
    rest of the rise evenly (T-2906: HABS sheet 4 draws the two at the foot)."""
    low=list(data.get('low_tread_tops') or [])
    k=len(low);m=n-k
    if not k:return [floor*(n-i)/n for i in range(n)]
    return [floor-i*(floor-low[0])/m for i in range(m)]+low

def build(b,params):
    from archetypes.masonry_house_v4_detail import facet_window,cylinder
    data=params.detail.get('bow_terrace',{})
    if not data.get('stair_boundaries'):return False
    bow=params.bows[0];conf=params.detail['conf']
    reduced=not getattr(b,'smooth_rock_faces',True)
    count=32 if reduced else 72
    r=data['r'];thick=data['thick_m'];a0,a1=data['arc']
    floor=data['z1']-.18
    boundaries=[[tuple(p) for p in edge] for edge in data['stair_boundaries']]
    lo,hi=data['window_z']
    step_angles=[math.atan2(edge[-1][1]-data['cy'],edge[-1][0]-data['cx']) % (2*math.pi)
                 for edge in boundaries]
    tops=tread_tops(data,floor,len(boundaries)-1)
    def hidden_inner(a):
        # Below the solid landing/treads, close the foundation with one face;
        # individual brick relief there can never be seen from the courtyard.
        index=max([0]+[i for i,t in enumerate(step_angles) if a>=t])
        return max(0.,(tops+[0.])[index]-.13)
    windows=[]
    for near,far in data['window_distance']:
        windows.append((math.pi+math.asin(near/r),math.pi+math.asin(far/r)))
    profiles=list(data['cap_section_profile'].values())
    curve_lo=min(profile[1][0] for profile in profiles)
    curve_hi=max(profile[-1][0] for profile in profiles)
    uniform=[a0+(a1-a0)*i/count for i in range(count+1)]
    # Source knots are denser than Light's uniform ring samples on the descent;
    # replace that subset instead of splitting the same brickwork twice.
    if reduced:uniform=[a for a in uniform if not curve_lo<-(r+.055)*math.sin(a)<curve_hi]
    breaks=sorted({a0,a1,*uniform,
                   *[q for edge in windows for q in edge],
                   *[math.pi+math.asin(distance/(r+.055))
                     for profile in data['cap_section_profile'].values() for distance,z in profile
                     if a0<math.pi+math.asin(distance/(r+.055))<a1]})
    def P(rad,a,z):return _point(data,rad,a,z)
    for a,c in zip(breaks,breaks[1:]):
        mid=(a+c)/2;want=(math.cos(mid),math.sin(mid),0)
        za,zc=cap_height(data,a,True),cap_height(data,c,True)
        ta,tc=cap_height(data,a),cap_height(data,c)
        opening=any(aa-1e-8<mid<cc+1e-8 for aa,cc in windows)
        bands=[(0,lo),(hi,None)] if opening else [(0,None)]
        for bottom,top in bands:
            pa,pc=(za,zc) if top is None else (top,top)
            b.wall([P(r,a,bottom),P(r,c,bottom),P(r,c,pc),P(r,a,pa)],conf,BRICK)
        # Continue the grille aperture through the full wall thickness.
        # Close the hidden foundation cheaply, but never fill an opening.
        for bottom,top in bands:
            pa,pc=(za,zc) if top is None else (top,top)
            ia=max(bottom,min(pa,hidden_inner(a)))
            ic=max(bottom,min(pc,hidden_inner(c)))
            if max(ia,ic)>bottom+1e-8:
                b.raw([P(r-thick,c,bottom),P(r-thick,a,bottom),P(r-thick,a,ia),P(r-thick,c,ic)],
                      conf,BRICK,tuple(-v for v in want))
            if max(pa-ia,pc-ic)>1e-8:
                b.wall([P(r-thick,c,ic),P(r-thick,a,ia),P(r-thick,a,pa),P(r-thick,c,pc)],conf,BRICK)
        # Closed coping: top, soffit, two long faces. Ends close below.
        ri,ro=r-thick-.025,r+.055
        b.raw([P(ri,a,ta),P(ro,a,ta),P(ro,c,tc),P(ri,c,tc)],conf,TRIM,(0,0,1))
        b.raw([P(ri,a,za),P(ro,a,za),P(ro,c,zc),P(ri,c,zc)],conf,TRIM,(0,0,-1))
        b.raw([P(ro,a,za),P(ro,c,zc),P(ro,c,tc),P(ro,a,ta)],conf,TRIM,want)
        b.raw([P(ri,a,za),P(ri,c,zc),P(ri,c,tc),P(ri,a,ta)],conf,TRIM,tuple(-v for v in want))
    for a,sgn in ((a0,-1),(a1,1)):
        z=cap_height(data,a,True);top=cap_height(data,a);want=(-math.sin(a)*sgn,math.cos(a)*sgn,0)
        end=[P(r-thick,a,0),P(r,a,0),P(r,a,z),P(r-thick,a,z)]
        if sgn<0:end.reverse()
        b.wall(end,conf,BRICK)
        b.raw([P(r-thick-.025,a,z),P(r+.055,a,z),P(r+.055,a,top),P(r-thick-.025,a,top)],conf,TRIM,want)
    for aa,cc in windows:
        mid=(aa+cc)/2;p=P(r,aa,0)[:2];q=P(r,cc,0)[:2]
        normal=(math.cos(mid),math.sin(mid),0)
        facet_window(b,p,q,lo,hi,normal,conf,small=True,stone_jambs=False,surrounds=False)
        width=math.dist(p,q);tangent=((q[0]-p[0])/width,(q[1]-p[1])/width,0)
        def local(u,z,off):
            return (p[0]+tangent[0]*u+normal[0]*off,p[1]+tangent[1]*u+normal[1]*off,z)
        def bar_box(ua,ub,za,zb,back,front,mat):
            corners=[(ua,za),(ub,za),(ub,zb),(ua,zb)]
            faces=[[local(u,z,front) for u,z in corners],
                   list(reversed([local(u,z,back) for u,z in corners]))]
            for (u,z),(v,h) in zip(corners,corners[1:]+corners[:1]):
                faces.append([local(u,z,back),local(v,h,back),local(v,h,front),local(u,z,front)])
            for face in faces:b.raw(face,conf,mat)
        stone=data['grille_stone_m'];j=stone['jamb']
        # Surveyed stone reveals are narrow; the generic facade surround is too wide.
        for ua,ub,za,zb in [(-j,0,lo,hi),(width,width+j,lo,hi),
                            (-j,width+j,lo-stone['sill'],lo),(-j,width+j,hi,hi+stone['lintel'])]:
            bar_box(ua,ub,za,zb,-.03,.085,TRIM)
        for i in range(1,data['grille_bars']+1):
            u=width*i/(data['grille_bars']+1)
            pos=local(u,0,-.025)
            cylinder(b,pos[0],pos[1],lo+.02,hi-.02,.009,conf,IRON,4 if reduced else 6)
        for t in data['grille_rails_fraction']:
            z=lo+(hi-lo)*t
            bar_box(0,width,z-.012,z+.012,-.045,-.018,IRON)

    # Land only on the high side of the first riser. A continuous circular slab
    # here would protrude above the descending cheek and through the stair.
    first_inner,first_outer=boundaries[0]
    keep=1 if ((first_outer[0]-first_inner[0])*(data['cy']-first_inner[1])-
               (first_outer[1]-first_inner[1])*(data['cx']-first_inner[0]))>=0 else -1
    ba0,ba1=sorted((bow['a0'],bow['a1']))
    if ba1-ba0>math.pi:ba0,ba1=ba1,ba0+2*math.pi
    floor_edges=[]
    for i in range(count):
        aa=a0+(a1-a0)*i/count;cc=a0+(a1-a0)*(i+1)/count
        # The surveyed bow and terrace meet the north wall on different
        # radial angles; each ring starts on its own wall intersection.
        def inner(t):
            angle=ba0+(ba1-ba0)*(t-a0)/(a1-a0)
            # The central leaf sits 0.23m behind its chord; reach its recessed
            # threshold as well as the visible outer brick face.
            return (bow['cx']+(bow['r']-.40)*math.cos(angle),bow['cy']+(bow['r']-.40)*math.sin(angle),floor)
        poly=[inner(aa),P(r-thick,aa,floor),P(r-thick,cc,floor),inner(cc)]
        poly=_clip(poly,first_inner,first_outer,keep)
        if len(poly)>2:
            b.raw(poly,conf,DRIVE,(0,0,1))
            b.raw([(p[0],p[1],floor-.12) for p in poly],conf,TRIM,(0,0,-1))
            floor_edges.extend(zip(poly,poly[1:]+poly[:1]))
    # Close exposed slab rims once, omitting shared grid edges.
    counts={}
    for p,q in floor_edges:
        key=tuple(sorted((tuple(round(x,7) for x in p),tuple(round(x,7) for x in q))))
        counts.setdefault(key,[]).append((p,q))
    for edges in counts.values():
        if len(edges)!=1:continue
        p,q=edges[0]
        b.raw([(p[0],p[1],floor-.12),(q[0],q[1],floor-.12),q,p],conf,TRIM)

    # The retained door's bottom reveal and sill lie at the deck's exact Z.
    # A single raised threshold covers that overlap, as a real stone threshold
    # does, instead of leaving two visible surfaces fighting for the same depth.
    mid=(ba0+ba1)/2;half=(ba1-ba0)/bow['lights_per_row']*.28
    door=next((s for row in bow.get('light_spans') or [] for s in row if s['door']),None)
    if door:  # T-2925: the door where the drawing puts it
        mid=(door['a0']+door['a1'])/2;half=(door['a1']-door['a0'])/2
    radius=bow['r']*math.cos(half);width=2*bow['r']*math.sin(half)
    normal=(math.cos(mid),math.sin(mid));tangent=(-normal[1],normal[0])
    def threshold_point(u,offset):
        return (bow['cx']+(radius+offset)*normal[0]+u*tangent[0],
                bow['cy']+(radius+offset)*normal[1]+u*tangent[1])
    outline=[threshold_point(u,off) for u,off in
             ((-width/2-.21,-.31),(width/2+.21,-.31),
              (width/2+.21,.065),(-width/2-.21,.065))]
    _solid(b,outline,floor-.10,floor+.006,conf,TRIM)

    # Solid fan treads, including their visible side faces and shallow noses.
    n=len(boundaries)-1
    for i,(edge,next_edge) in enumerate(zip(boundaries,boundaries[1:])):
        # A boundary is [*points along the wall or drum, inner, outer]: its last
        # segment is the riser; any points before it close the tread above it
        # against the wall and the drum, and are no riser (T-2906).
        inner,outer=edge[-2:];ni,no=next_edge[-2:]
        top=tops[i]
        _solid(b,[inner,outer,*reversed(next_edge)],-.04,top,conf,TRIM)
        centre=((inner[0]+outer[0])/2,(inner[1]+outer[1])/2)
        front=((ni[0]+no[0])/2,(ni[1]+no[1])/2)
        length=math.dist(centre,front);v=tuple((front[k]-centre[k])/length for k in range(2))
        nose=[tuple(p[k]+v[k]*offset for k in range(2)) for p,offset in ((ni,-.035),(no,-.035),(no,.022),(ni,.022))]
        _solid(b,nose,top-.035,top+.001,conf,TRIM)
    _newel(b,data,conf,reduced)
    return True
